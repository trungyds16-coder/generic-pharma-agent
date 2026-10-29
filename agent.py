from __future__ import annotations

import json
import re
import time
from pathlib import Path
from types import SimpleNamespace

import ollama

from monitor import LIVE
from tools import SCHEMAS, WorkspaceTools

_ALLOWED = {"set_task_checklist", "update_task_step", "write_project_launcher", "list_dir", "read_file", "read_document", "write_file", "check_python", "run_python", "launch_python", "run_powershell", "open_file", "search_web", "fetch_url", "download_image", "download_compound_structure", "fill_docx_template", "fill_html_template", "create_html_report", "convert_pdf_to_html"}

DEFAULT_OPTIONS = {"temperature": 0.1, "num_ctx": 8192}
MAX_TOOL_RESULT_CHARS = 6000  # kết quả đưa lại cho model; tránh tràn context

SYSTEM = (
    "You are an autonomous coding agent on the user's Windows PC. "
    "Reply in Vietnamese unless the user writes in another language.\n"
    "RULES:\n"
    "1. Do not ask permission for research, project file edits, reports, downloads, or internal checks. "
    "Never start an interactive app/server from tools; the user starts it with Play. If information is missing, make a safe reasonable assumption and state it.\n"
    "2. Act through tool calls, not explanations. Never paste code or JSON in the reply instead of calling a tool.\n"
    "3. For code edits, follow this strict order: inspect files -> write/create the required files -> check syntax/tests -> configure the launcher. Never call run_python/check_python on a file before it exists; if a file is missing, create it with write_file first. Never claim that a file exists based only on your own previous reply. Before completion, audit the request and approved-plan criteria against real files and actual tool results. A success claim requires at least one successful artifact write for an implementation request and passing checks for changed Python files. If checks fail, repair the exact failure up to three times; otherwise report incomplete with the real blocker.\n"
    "Never use eval() or exec() to interpret user input; use a restricted parser/AST instead.\n"
    "4. Internal tests may run automatically. Do not use run_python to start an app, GUI, or server; that requires the user's Play action. Use check_python for application syntax.\n"
    "5. Classify each request: code/project edits, web/URL research, document/report work, or a combination. Use search_web/fetch_url for web requests and preserve source links. For drug reports prefer project priority sources first, verify compound identity before downloading a PubChem structure, and never invent missing facts. Use read_document for Word/PDF/HTML inputs. Use fill_docx_template/fill_html_template/create_html_report for reports and convert_pdf_to_html for PDFs.\n"
    "6. Continue from existing files and recent tool outputs when a prior model failed; do not repeat completed work.\n"
    "7. Keep all output, caches, reports, downloaded images, source manifests, and terminal logs inside the selected D-drive project/data folders.\n"
    "If you provide code, use the file tools rather than pasting code as a final answer.\n"
    "8. Only when everything is finished, reply in Vietnamese: what you did, the full file path, "
    "and the real run output.\n"
    "9. For every actionable task, start by creating/refining a concrete 3-12 step checklist with set_task_checklist. Mark the active step and completed/blocked steps with update_task_step as work proceeds. Include every distinct requested feature, then verify each before saying complete.\n"
    "10. Every project gets run_project.bat, create_desktop_shortcut.bat and assets/icons/project.ico. When you create/change a project's entry point or dependencies, inspect how it actually runs and update run_project.bat with write_project_launcher. Do not edit the Local Agent's app.py to launch a child project. Never run the launcher from chat; the user starts it by clicking its desktop shortcut or Play.\n"
    "Example: 'viết chương trình đếm từ' -> write_file(main.py) -> check_python(main.py) -> run_python only for a non-GUI CLI/test file -> configure run_project.bat -> report the real output. Never test a GUI by launching it during chat; leave that to Play."
)

NUDGE = (
    "Continue autonomously using the appropriate tool. Do not paste code/JSON instead of editing files. "
    "If a prior check failed, fix that failure before doing unrelated work. If the requested file does not exist, create it with write_file before any run/check call."
)

_RUN_INTENT = re.compile(r"\b(chạy|run|test|tests|pytest|thử|kiểm tra)\b", re.I)
_NO_RUN = re.compile(r"(đừng|không|chưa|chỉ|do not|don't|only)\s+(cần\s+)?(chạy|run)|chỉ\s+(viết|tạo|write)", re.I)
_ASK_PHRASES = re.compile(
    r"(bạn (có )?(muốn|cần)|vui lòng (cho biết|xác nhận)|hãy cho (tôi )?biết|xác nhận|"
    r"would you like|do you want|let me know)",
    re.I,
)
_PY_PATH = re.compile(r"(?:python(?:\.exe)?\s+|py\s+)?((?:[\w.-]+[\\/])*[\w.-]+\.py)\b", re.I)
_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.I | re.S)
_FILE_MENTION = re.compile(
    r"(?:file|tệp|tập\s*tin)\s*[`'\"]?((?:[\w.-]+[\\/])*[\w.-]+\.(?:py|html?|css|js|json|md|txt|svg|ya?ml))[`'\"]?",
    re.I,
)


def _classify_request(text: str) -> list[str]:
    value=(text or "").casefold()
    modes=[]
    if re.search(r"\b(code|coding|python|javascript|bug|fix|app|s\u1eeda|l\u1ed7i|t\u1ea1o app|x\u00e2y d\u1ef1ng|\u1ee9ng d\u1ee5ng|ch\u1ee9c n\u0103ng|t\u00ednh n\u0103ng|file m\u1edbi|b\u1ed5 sung|th\u00eam|c\u00f4ng c\u1ee5|t\u00edch ph\u00e2n|h\u00e0m s\u1ed1|m\u00e1y t\u00ednh|\u0111\u1ed3 th\u1ecb|tri\u1ec3n khai)\b",value): modes.append("code/project")
    if re.search(r"\b(url|http|link|web|t\u00ecm ki\u1ebfm|tra c\u1ee9u|ngu\u1ed3n|patent|b\u1eb1ng s\u00e1ng ch\u1ebf|ho\u1ea1t ch\u1ea5t|cas|pubchem)\b",value): modes.append("web research")
    if re.search(r"\b(report|b\u00e1o c\u00e1o|t\u1ed5ng quan|word|docx|html|template|m\u1eabu)\b",value): modes.append("document/report")
    if re.search(r"\b(pdf|chuy\u1ec3n \w+ sang html|convert)\b",value): modes.append("PDF conversion")
    return modes or ["chat/help"]


def _tool_args(tc) -> dict:
    raw = tc.function.arguments
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}


def _parse_text_tools(content: str) -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    if not content:
        return out
    dec = json.JSONDecoder()
    i = 0
    while i < len(content):
        start = content.find("{", i)
        if start < 0:
            break
        try:
            obj, end = dec.raw_decode(content, start)
        except json.JSONDecodeError:
            i = start + 1
            continue
        i = end
        if isinstance(obj, dict) and obj.get("name") in _ALLOWED and isinstance(obj.get("arguments"), dict):
            out.append((obj["name"], obj["arguments"]))
    return out


def _norm_path(p: str) -> str:
    p = (p or "").strip().strip('"')
    if p.lower().startswith(("python ", "python.exe ", "py ")):
        p = p.split(None, 1)[1].strip().strip('"')
    return p.replace("\\", "/")


def _looks_like_asking(text: str) -> bool:
    t = (text or "").strip()
    return bool(t) and (t.endswith(("?", "？")) or bool(_ASK_PHRASES.search(t[-300:])))


def _looks_unexecuted(text: str) -> bool:
    return "```" in (text or "") or bool(re.search(r'"name"\s*:\s*"', text or ""))


def _full_path(tools: WorkspaceTools, p: str) -> str:
    path = Path(p)
    return str(path if path.is_absolute() else tools.root / path)


def _exit_code(result: str) -> str:
    m = re.match(r"Exit code:\s*(-?\d+)", result or "")
    return m.group(1) if m else "?"


def _clip(text: str) -> str:
    text = str(text)
    if len(text) <= MAX_TOOL_RESULT_CHARS:
        return text
    return text[:MAX_TOOL_RESULT_CHARS] + "\n...[đã cắt bớt]"


def _with_footer(text: str, actions: list[str]) -> str:
    text = (text or "").strip()
    if not actions:
        return text
    body = text or "Đã xong các thao tác sau."
    return body + "\n\n---\n**Đã thực hiện**\n" + "\n".join(f"- {a}" for a in actions)


def _chat(client, *, model, messages, tools, options, keep_alive, round_index, on_progress=None):
    """Gọi Ollama dạng stream để báo tiến trình sinh (token, tốc độ, đoạn đang viết).

    Trả về đối tượng giống phản hồi không-stream. Nếu stream lỗi trước khi nhận được gì thì tự chạy lại kiểu cũ.
    """
    LIVE.begin_round(round_index + 1)
    parts: list[str] = []
    calls_by_index: dict[int, object] = {}
    streamed_code: dict[int, tuple[str, str]] = {}
    final = None
    tokens = 0
    last_push = 0.0
    try:
        for chunk in client.chat(model=model, messages=messages, tools=tools, options=options,
                                 keep_alive=keep_alive, stream=True):
            m = chunk.message
            if m.content:
                parts.append(m.content)
                tokens += 1
            if m.tool_calls:
                for call_index, call in enumerate(m.tool_calls):
                    calls_by_index[call_index] = call
                    if getattr(getattr(call, "function", None), "name", "") == "write_file":
                        args = _tool_args(call)
                        path = str(args.get("path", ""))
                        content = args.get("content")
                        if isinstance(content, str):
                            previous_path, previous = streamed_code.get(call_index, (path, ""))
                            # Ollama backends may stream either cumulative arguments or deltas.
                            if content.startswith(previous):
                                merged = content
                            elif previous.startswith(content):
                                merged = previous
                            else:
                                merged = previous + content
                            streamed_code[call_index] = (path or previous_path, merged)
                            LIVE.stream_code(path or previous_path, merged)
            now = time.monotonic()
            if now - last_push >= 0.5:
                calls = [calls_by_index[i] for i in sorted(calls_by_index)]
                preview = "\n".join(content for _, content in streamed_code.values()) or "".join(parts)
                LIVE.stream_update(preview, tokens)
                if on_progress:
                    on_progress("STREAM|")
                last_push = now
            if getattr(chunk, "done", False):
                final = chunk
    except Exception:
        if parts or calls_by_index:
            raise
        resp = client.chat(model=model, messages=messages, tools=tools, options=options, keep_alive=keep_alive)
        LIVE.stream_update(resp.message.content or "", int(getattr(resp, "eval_count", 0) or 0))
        return resp
    text = "".join(parts)
    calls = [calls_by_index[i] for i in sorted(calls_by_index)]
    for path, content in streamed_code.values():
        LIVE.stream_code(path, content)
    preview = "\n".join(content for _, content in streamed_code.values()) or text
    LIVE.stream_update(preview, int(getattr(final, "eval_count", 0) or tokens))
    # Ollama may emit tool-call arguments only on the final chunk. Push one
    # last UI event so the completed code is visible before tool execution.
    if on_progress:
        on_progress("STREAM|")
    return SimpleNamespace(
        message=SimpleNamespace(content=text, tool_calls=calls),
        prompt_eval_count=getattr(final, "prompt_eval_count", 0),
        eval_count=getattr(final, "eval_count", 0),
        total_duration=getattr(final, "total_duration", 0),
        eval_duration=getattr(final, "eval_duration", 0),
    )


def run_turn(messages, model, tools, client, max_rounds, on_progress=None, options=None, auto_run=True, keep_alive="5m"):
    LIVE.start(model, max_rounds)
    usage = None
    try:
        reply, usage = _run_turn_impl(messages, model, tools, client, max_rounds, on_progress, options, auto_run, keep_alive)
        return reply, usage
    finally:
        LIVE.finish(usage)


def _run_turn_impl(
    messages: list,
    model: str,
    tools: WorkspaceTools | None,
    client: ollama.Client,
    max_rounds: int,
    on_progress=None,
    options: dict | None = None,
    auto_run: bool = True,
    keep_alive: str = "5m",
) -> tuple[str, dict]:
    def say(text):
        LIVE.set_phase(str(text)[:90])
        if on_progress:
            on_progress(text)
    usage = {"prompt_tokens": 0, "output_tokens": 0, "total_duration_ns": 0, "eval_duration_ns": 0, "rounds": 0}
    actions: list[str] = []
    failed_paths: set[str] = set()
    failure_results: dict[str, str] = {}
    repair_prompts = 0
    repair_attempts: dict[str, int] = {}
    missing_paths: set[str] = set()
    last = ""

    latest_user = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
    latest_user = latest_user if isinstance(latest_user, str) else ""
    wants_run = auto_run and bool(_RUN_INTENT.search(latest_user)) and not _NO_RUN.search(latest_user)
    modes = _classify_request(latest_user)
    code_intent = "code/project" in modes and bool(re.search(r"(tạo|xây dựng|viết|sửa|thêm|bổ sung|triển khai|làm|implement|build|fix|create|write|add|modify|update|refactor|chức năng|tính năng|feature)", latest_user, re.I))
    mode_labels={"code/project":"Code/project","web research":"Tra cứu URL/web","document/report":"Báo cáo/Word/HTML","PDF conversion":"PDF sang HTML","chat/help":"Trò chuyện"}
    say("Phân loại yêu cầu: " + " + ".join(mode_labels.get(mode,mode) for mode in modes))
    if messages and messages[0].get("role") == "system":
        messages.insert(1, {"role": "system", "content": "Task route detected: " + ", ".join(modes) + ". Combine routes when appropriate; use tools, do not only describe them."})
    if tools and modes != ["chat/help"]:
        checklist = [
            "Đọc prompt, file hiện có và tiêu chí trong plan đã duyệt",
            "Thực hiện yêu cầu: " + re.sub(r"\s+", " ", latest_user).strip()[:220],
            "Chạy kiểm tra phù hợp và tự sửa lỗi phát hiện được",
            "Đối chiếu từng yêu cầu với file/kết quả thật rồi báo phần đạt hoặc còn thiếu",
        ]
        tools.set_task_checklist(json.dumps(checklist, ensure_ascii=False))

    written_py: list[str] = []   # file .py đã ghi trong lượt này
    ran: set[str] = set()        # file .py đã chạy sau lần ghi gần nhất
    validated_files: set[str] = set()  # file đã có kết quả kiểm tra thật đạt trong lượt này
    written_files: set[str] = set()    # file write_file đã tạo/sửa thành công thật
    seen: dict[str, int] = {}    # chặn lặp cùng một lệnh
    nudges = 0
    audit_requests = 0
    audit_pending = False
    artifact_changed = False

    for round_index in range(max_rounds):
        say(f"Đang chờ Ollama xử lý (vòng {round_index + 1}/{max_rounds})...")
        resp = _chat(
            client,
            model=model,
            messages=messages,
            tools=SCHEMAS if tools else [],
            options=options or DEFAULT_OPTIONS,
            keep_alive=keep_alive,
            round_index=round_index,
            on_progress=say,
        )
        usage["rounds"] += 1
        usage["prompt_tokens"] += int(getattr(resp, "prompt_eval_count", 0) or 0)
        usage["output_tokens"] += int(getattr(resp, "eval_count", 0) or 0)
        usage["total_duration_ns"] += int(getattr(resp, "total_duration", 0) or 0)
        usage["eval_duration_ns"] += int(getattr(resp, "eval_duration", 0) or 0)

        msg = resp.message
        last = msg.content or ""
        native = list(msg.tool_calls or [])
        if native:
            calls = [(tc.function.name, _tool_args(tc)) for tc in native]
        else:
            calls = _parse_text_tools(last) if tools else []

        # Lần đầu: người dùng bảo chạy/test một file .py cụ thể mà model không gọi tool -> harness tự chạy.
        if not calls and tools and round_index == 0 and _RUN_INTENT.search(latest_user):
            m = _PY_PATH.search(latest_user + "\n" + last)
            if m:
                calls = [("run_python", {"path": _norm_path(m.group(1))})]

        # Một số model chỉ in code kèm hướng dẫn thay vì gọi write_file.
        # Chuyển đúng trường hợp đó thành thao tác ghi file thật.
        if not calls and tools and _FENCE.search(last) and re.search(r"(tạo|ghi|viết|create|write|save)\s+.{0,80}(file|tệp|tập tin)", last, re.I):
            fm = _FILE_MENTION.search(last)
            code = _FENCE.search(last)
            if fm and code:
                calls = [("write_file", {"path": _norm_path(fm.group(1)), "content": code.group(1).strip() + "\n"})]

        # Lịch sử nhất quán: chỉ gắn tool_calls khi là tool call thật của model.
        if native:
            messages.append({"role": "assistant", "content": last, "tool_calls": native})
        else:
            messages.append({"role": "assistant", "content": last})

        if not calls:
            if tools and failed_paths and repair_prompts < 3:
                repair_prompts += 1
                details = "\n\n".join(f"{path}:\n{failure_results.get(path, 'Kiểm tra vẫn lỗi.')}" for path in sorted(failed_paths))
                say(f"Kiểm tra còn lỗi · yêu cầu model tự sửa lần {repair_prompts}/3")
                if missing_paths:
                    instruction = ("CHƯA HOÀN THÀNH: file được gọi chạy không tồn tại. Hãy xem cấu trúc bằng list_dir/read_file; "
                                   "nếu file cần thiết chưa có, tạo bằng write_file trước. Không gọi run_python/check_python "
                                   "cho tới khi file thực sự tồn tại. Sau đó mới kiểm tra cú pháp/test.")
                else:
                    instruction = "CHƯA HOÀN THÀNH. Hãy đọc file thật, sửa đúng lỗi bên dưới bằng write_file, rồi check_python/chạy lại test. Không lặp lại nguyên văn code lỗi và không kết luận xong khi chưa pass."
                messages.append({"role": "user", "content": instruction + "\n\n" + details})
                continue
            if failed_paths:
                return _with_footer("⚠️ Chưa hoàn thành: kiểm tra vẫn lỗi sau các lượt tự sửa có giới hạn. Đổi model rồi nhắn 'tiếp tục sửa lỗi'; agent sẽ dùng lại file và kết quả hiện có.\n\n" + last, actions), usage
            if tools and code_intent and not artifact_changed and nudges < 2:
                nudges += 1
                say("Yêu cầu có ý định triển khai nhưng chưa sửa file · yêu cầu model thực hiện")
                messages.append({"role": "user", "content": "Bạn chưa tạo/sửa được file nào. Đây là yêu cầu triển khai: kiểm tra đường dẫn và kết quả tool. Nếu file chưa tồn tại, tạo bằng write_file trước; không gọi run_python/check_python để thay cho việc tạo file. Sau đó kiểm tra kết quả thật. Không kết thúc bằng lời hứa hay hướng dẫn."})
                continue
            if tools and code_intent:
                if not audit_pending:
                    if audit_requests >= 3:
                        return _with_footer("⚠️ Chưa xác nhận hoàn tất: sau ba lượt rà soát agent vẫn chưa chứng minh đủ yêu cầu. Xem checklist để biết mục nào còn thiếu; không đánh dấu project là xong.\n\n" + last, actions), usage
                    audit_requests += 1
                    audit_pending = True
                    say(f"Đang đối chiếu prompt/plan với file và kiểm tra · lượt {audit_requests}/3")
                    messages.append({"role": "user", "content": (
                        "RÀ SOÁT HOÀN TẤT BẮT BUỘC (chạy hoàn toàn bằng model local): đối chiếu từng yêu cầu trong tin nhắn mới nhất và từng tiêu chí liên quan trong Approved plan.md (nếu có) với file thật. "
                        "Đọc lại file đã sửa, xác nhận từng chức năng có thật trong giao diện/mã, chạy kiểm tra/test phù hợp. "
                        "Nếu còn thiếu mục nào, cập nhật checklist, sửa bằng công cụ rồi kiểm tra lại; không chỉ nêu đề xuất. "
                        "Chỉ khi tất cả yêu cầu đã có trong file và kiểm tra đạt, kết thúc bằng dòng riêng chính xác LOCAL_AGENT_AUDIT: PASS. Nếu chưa đạt thì nói rõ mục thiếu và không dùng PASS."
                    )})
                    continue
                if "LOCAL_AGENT_AUDIT: PASS" not in last:
                    audit_pending = False
                    if audit_requests < 3:
                        messages.append({"role": "user", "content": "Rà soát chưa chứng minh đủ yêu cầu. Tiếp tục sửa các mục còn thiếu bằng công cụ, chạy lại kiểm tra, rồi tự rà soát lại. Chỉ kết luận khi mọi mục đạt."})
                        continue
                    return _with_footer("⚠️ Chưa hoàn thành: rà soát cuối không xác nhận đủ yêu cầu. Không đánh dấu project là xong.\n\n" + last, actions), usage
                changed_python = {p for p in written_py}
                missing_validation = changed_python - validated_files
                if code_intent and not written_files:
                    audit_pending = False
                    messages.append({"role": "user", "content": (
                        "Không chấp nhận LOCAL_AGENT_AUDIT: PASS vì lượt này chưa có file nào được write_file ghi thành công. "
                        "Hãy thực hiện yêu cầu trên file thật; không chỉ báo đã làm."
                    )})
                    continue
                if missing_validation:
                    audit_pending = False
                    messages.append({"role": "user", "content": (
                        "Không chấp nhận LOCAL_AGENT_AUDIT: PASS vì các file Python vừa sửa chưa có kiểm tra thành công: "
                        + ", ".join(sorted(missing_validation)) + ". Chạy check_python/test phù hợp, sửa lỗi nếu có, rồi rà soát lại."
                    )})
                    continue
                last = re.sub(r"(?m)^\s*LOCAL_AGENT_AUDIT:\s*PASS\s*$", "", last).strip()
                if hasattr(tools, "finish_task_checklist"):
                    tools.finish_task_checklist("Đã rà soát đủ yêu cầu và model local xác nhận kiểm tra đạt.")
            if tools and nudges < 2 and (_looks_like_asking(last) or _looks_unexecuted(last)):
                nudges += 1
                say("Model chưa gọi công cụ · nhắc tự thực hiện")
                messages.append({"role": "user", "content": NUDGE})
                continue
            if tools and modes != ["chat/help"] and actions and not code_intent and hasattr(tools, "finish_task_checklist"):
                tools.finish_task_checklist()
            return _with_footer(last, actions), usage

        results: list[str] = []
        call_keys=[]
        for i, (name, args) in enumerate(calls, start=1):
            target = args.get("path") or args.get("command") or args.get("url") or ""
            p = _norm_path(str(args.get("path", "")))
            target_path = None
            if name in {"run_python", "check_python"} and tools:
                try:
                    target_path=Path(str(args.get("path", "")))
                    target_path=target_path if target_path.is_absolute() else tools.root/target_path
                    target_path=target_path.resolve()
                    signature=target_path.read_bytes()
                    import hashlib
                    key=name+str(target_path)+hashlib.sha256(signature).hexdigest()
                except OSError:
                    key=name+json.dumps(args,sort_keys=True,ensure_ascii=False)
                    if target_path is None:
                        target_path=tools.root/p
            else:
                key=name+json.dumps(args,sort_keys=True,ensure_ascii=False)
            seen[key]=seen.get(key,0)+1
            call_keys.append(key)
            if seen[key]>2:
                result="Cùng một file chưa đổi nội dung đã bị kiểm tra lặp lại. Hãy sửa file trước khi chạy lại."
            else:
                say(f"{name}: {target} · bước {i}/{len(calls)}")
                if tools and hasattr(tools, "note_command"):
                    tools.note_command(name, args)
                if name in {"run_python", "check_python"} and tools and target_path is not None and not target_path.is_file():
                    missing_paths.add(p)
                    result=f"BLOCKED_MISSING_FILE: Không tồn tại {target_path}. Hãy dùng write_file để tạo file trước; không gọi chạy/kiểm tra lại đường dẫn này cho tới khi file tồn tại."
                else:
                    result=tools.dispatch(name,args)
            results.append(result)
            say(f"Đã xong {name} · {str(result)[:200]}")

            if name == "write_file":
                written_path = _full_path(tools, p)
                write_ok = not str(result).startswith(("Error:", "Unknown tool:")) and written_path.is_file()
                if write_ok:
                    artifact_changed = True
                    written_files.add(p)
                    missing_paths.discard(p)
                    LIVE.record_write(str(written_path), str(args.get("content", "")))
                    actions.append(f"✅ Ghi file `{written_path}`")
                    if p.lower().endswith(".py"):
                        if p not in written_py: written_py.append(p)
                        ran.discard(p)
                        repair_attempts[p]=repair_attempts.get(p,0)+(1 if p in failed_paths else 0)
                else:
                    failed_paths.add(p)
                    failure_results[p] = str(result)
                    actions.append(f"❌ Không ghi được file `{written_path}` · {str(result)[:180]}")
            elif name == "write_project_launcher":
                launcher = tools.root / "run_project.bat"
                if not str(result).startswith(("Error:", "Unknown tool:")) and launcher.is_file():
                    artifact_changed = True
                    actions.append(f"🔧 Cập nhật launcher `{launcher}`")
                else:
                    failed_paths.add("run_project.bat")
                    failure_results["run_project.bat"] = str(result)
                    actions.append(f"❌ Không cập nhật được launcher · {str(result)[:180]}")
            elif name in {"run_python", "check_python"}:
                code=_exit_code(result)
                if str(result).startswith("APP_START_APPROVAL_REQUIRED"):
                    actions.append(f"⏸ Chưa mở ứng dụng `{p}` · chờ nút Play")
                    continue
                ran.add(p)
                if code=="0":
                    failed_paths.discard(p); failure_results.pop(p,None)
                    missing_paths.discard(p)
                    validated_files.add(p)
                else:
                    failed_paths.add(p); failure_results[p]=result
                actions.append(f"{'✅' if code=='0' else '❌'} {name} `{p}` → {('exit code '+code) if code!='?' else str(result)[:140]}")
            else:
                actions.append(f"🔧 {name} {target}".strip())

        if any(seen[key]>2 for key in call_keys):
            return _with_footer("Đã dừng vòng lặp công cụ vì cùng thao tác bị yêu cầu lặp lại quá nhiều lần. Đây là lỗi/chưa hoàn thành; không đánh dấu project là xong.", actions), usage

        # Every newly written Python file gets a syntax check. Test scripts may run automatically;
        # launching an application/server is reserved for the explicit Play action.
        extra: list[str] = []
        if tools:
            for p in [x for x in written_py if x not in ran]:
                check=tools.dispatch("check_python", {"path": p})
                extra.append(f"[check_python {p}]\n{check}")
                code=_exit_code(check)
                if code=="0":
                    failed_paths.discard(p); failure_results.pop(p,None)
                    validated_files.add(p)
                    actions.append(f"✅ Cú pháp Python hợp lệ `{p}`")
                else:
                    failed_paths.add(p); failure_results[p]=check
                    actions.append(f"❌ Cú pháp Python còn lỗi `{p}`")
                ran.add(p)
                is_test=bool(re.search(r"(^|/)(tests?/|test_[^/]+\.py$|[^/]*_test\.py$)|run_tests\.py$",p,re.I))
                if is_test and code=="0":
                    say(f"Tự chạy kiểm thử {p}")
                    result=tools.dispatch("run_python", {"path": p})
                    extra.append(f"[run_python {p}]\n{result}")
                    test_code=_exit_code(result)
                    if test_code=="0":
                        failed_paths.discard(p); failure_results.pop(p,None)
                        actions.append(f"✅ Kiểm thử pass `{p}`")
                    else:
                        failed_paths.add(p); failure_results[p]=result
                        actions.append(f"❌ Kiểm thử còn lỗi `{p}`")

        if native:
            for (name, _), res in zip(calls, results):
                messages.append({"role": "tool", "tool_name": name, "content": _clip(res)})
            if extra:
                messages.append({
                    "role": "user",
                    "content": "Kết quả chạy tự động:\n" + _clip("\n\n".join(extra))
                    + "\nNếu exit code khác 0 thì sửa file và chạy lại; nếu đã ổn thì báo kết quả.",
                })
        else:
            joined = "\n\n".join(f"[{n}]\n{r}" for (n, _), r in zip(calls, results))
            if extra:
                joined += "\n\n" + "\n\n".join(extra)
            messages.append({
                "role": "user",
                "content": "Kết quả công cụ (đã chạy tự động):\n" + _clip(joined)
                + "\nNếu còn lỗi thì sửa và chạy lại; nếu đã ổn thì báo kết quả.",
            })
        if missing_paths:
            missing_list = "\n".join(f"- {path}" for path in sorted(missing_paths))
            messages.append({
                "role": "user",
                "content": (
                    "BƯỚC TIẾP THEO BẮT BUỘC: các file dưới đây chưa tồn tại. Không gọi run_python/check_python lặp lại. "
                    "Hãy tạo file cần thiết bằng write_file trước, xác nhận file đã tồn tại, rồi mới kiểm tra.\n" + missing_list
                ),
            })

    final = last or "Đã hết số vòng cho phép."
    if tools and code_intent and not artifact_changed:
        final = "⚠️ Chưa hoàn thành: yêu cầu triển khai nhưng không xác nhận được lần ghi file thành công. Xem nhật ký công cụ; chưa thể coi project là xong.\n\n" + final
    elif tools and code_intent and artifact_changed:
        final = "⚠️ Chưa hoàn thành: đã hết số vòng trước khi hoàn tất bước rà soát yêu cầu/plan. Không đánh dấu project là xong. Tiếp tục lại cùng chat để agent rà soát và xử lý phần còn thiếu.\n\n" + final
    if failed_paths:
        final = "⚠️ Chưa hoàn thành: lần chạy/kiểm thử gần nhất còn lỗi. Xem kết quả thật bên dưới; không được coi project là hoàn tất.\n\n" + final
    return _with_footer(final, actions), usage
