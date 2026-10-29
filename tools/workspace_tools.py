from __future__ import annotations

import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import documents
import research
import project_launcher

_BLOCKED = re.compile(
    r"(remove-item|\brm\b|\bdel\b|\berase\b|rmdir|format-volume|\bformat\b|\breg\b|"
    r"set-executionpolicy|invoke-expression|\biex\b|invoke-webrequest|\bcurl\b|\bwget\b|"
    r"shutdown|stop-computer|restart-computer|taskkill|stop-process|start-process)", re.I,
)


def _schema(name, description, properties, required=None):
    return {"type": "function", "function": {"name": name, "description": description,
        "parameters": {"type": "object", "properties": properties, **({"required": required} if required else {})}}}

SCHEMAS = [
    _schema("set_task_checklist", "Create a concise ordered checklist from the user's request and approved plan before changing files. Use 3-12 concrete steps.", {"items_json": {"type": "string", "description": "JSON array of step strings, ordered from inspection through implementation and verification"}}, ["items_json"]),
    _schema("update_task_step", "Update one checklist step as in_progress, done, or blocked. Index is zero-based.", {"index": {"type": "integer"}, "status": {"type": "string", "enum": ["todo", "in_progress", "done", "blocked"]}, "note": {"type": "string"}}, ["index", "status"]),
    _schema("write_project_launcher", "Update this project's run_project.bat with the actual one-line command that starts the finished project. Keep it inside the project and do not start it now.", {"run_command": {"type": "string", "description": "One project-relative launch command, for example python main.py or npm run dev"}}, ["run_command"]),
    _schema("list_dir", "List files in the selected project.", {"path": {"type": "string"}}),
    _schema("read_file", "Read a text file from the selected project or the exact selected input file.", {"path": {"type": "string"}}, ["path"]),
    _schema("read_document", "Extract text from Word, PDF, HTML, or text documents, including a selected input file.", {"path": {"type": "string"}}, ["path"]),
    _schema("write_file", "Create or overwrite the requested project file. For implementation tasks, use this before any run/check call; success means the file was actually written. Python source is normalized and syntax-parsed.", {"path": {"type": "string"}, "content": {"type": "string"}}, ["path", "content"]),
    _schema("check_python", "Check Python syntax without starting the application. Use for automatic validation before Play.", {"path": {"type": "string"}}, ["path"]),
    _schema("run_python", "Run an existing Python test or non-GUI script only; the path must already exist. Never call this to create a file or start a GUI/app/server. Use write_file first for missing files. Output streams live.", {"path": {"type": "string"}}, ["path"]),
    _schema("launch_python", "Request to start an interactive app. During chat this waits for the user's Play approval.", {"path": {"type": "string"}}, ["path"]),
    _schema("run_powershell", "Run a non-destructive PowerShell command in the project and stream output to the terminal panel.", {"command": {"type": "string"}}, ["command"]),
    _schema("open_file", "Open a project file in its Windows application.", {"path": {"type": "string"}}, ["path"]),
    _schema("search_web", "Search the public web. Search project priority domains first, then general results; return source URLs.", {"query": {"type": "string"}}, ["query"]),
    _schema("fetch_url", "Fetch and extract readable text from a public HTTP/HTTPS page or PDF, preserving its URL as a source.", {"url": {"type": "string"}}, ["url"]),
    _schema("download_image", "Download an image from a public URL into project assets; validate type and size and record the source URL.", {"url": {"type": "string"}, "filename": {"type": "string"}}, ["url", "filename"]),
    _schema("download_compound_structure", "Find and download a 2D molecular structure PNG from PubChem using a compound name/CAS; save it in project assets and return the CID/source for verification.", {"compound": {"type": "string"}, "filename": {"type": "string"}}, ["compound", "filename"]),
    _schema("fill_docx_template", "Fill a user-provided Word template using JSON field values, optionally inserting the downloaded molecular structure image at the structure placeholder. Save output in the project.", {"template_path": {"type": "string"}, "output_path": {"type": "string"}, "fields_json": {"type": "string"}, "structure_image_path": {"type": "string"}}, ["template_path", "output_path", "fields_json"]),
    _schema("fill_html_template", "Fill a user-provided HTML report template with JSON fields and save the result in the project.", {"template_path": {"type": "string"}, "output_path": {"type": "string"}, "fields_json": {"type": "string"}}, ["template_path", "output_path", "fields_json"]),
    _schema("create_html_report", "Create an accessible standalone HTML report with sections, sources, and a local molecular image.", {"output_path": {"type": "string"}, "title": {"type": "string"}, "sections_json": {"type": "string"}, "sources_json": {"type": "string"}, "image_path": {"type": "string"}}, ["output_path", "title", "sections_json"]),
    _schema("convert_pdf_to_html", "Convert a local PDF into a searchable, lightweight HTML document. Save HTML in the project.", {"pdf_path": {"type": "string"}, "output_path": {"type": "string"}, "title": {"type": "string"}}, ["pdf_path", "output_path"]),
]


def _normalize_python_source(path: Path, content: str) -> tuple[str, list[str]]:
    notes = []
    if path.suffix.lower() != ".py":
        return content, notes
    wrapped = re.fullmatch(r"\s*```(?:python|py)?\s*\n(.*?)\n```\s*", content, re.I | re.S)
    if wrapped:
        content = wrapped.group(1) + "\n"
        notes.append("Removed Markdown code fences from Python source.")
    # Repair the common corruption where escaped newlines were written as literal backslash-n text.
    if "\n" not in content and content.count(r"\n") >= 2 and re.search(r"\b(import|from|def|class|if)\b", content):
        content = content.replace(r"\r\n", "\n").replace(r"\n", "\n").replace(r"\t", "    ")
        notes.append("Converted escaped newline/tab text into real Python line breaks.")
    guard = re.compile(r"(?m)^\s*if\s+\*\*name\*\*\s*==\s*['\"]\*\*main\*\*['\"]\s*:")
    if guard.search(content):
        content = guard.sub('if __name__ == "__main__":', content)
        notes.append("Repaired Markdown-formatted __name__/__main__ guard.")
    return content, notes


class WorkspaceTools:
    def __init__(self, root: Path, python_timeout: int = 30, editable_file: Path | None = None,
                 on_activity=None, reference_paths: list[str] | None = None, allow_launch: bool = False,
                 chat_id: str = ""):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.python_timeout = python_timeout
        self.editable_file = editable_file.expanduser().resolve() if editable_file else None
        self.on_activity = on_activity or (lambda _text: None)
        self.reference_paths = {Path(p).expanduser().resolve() for p in (reference_paths or []) if p}
        self.allow_launch = allow_launch
        self.chat_id = re.sub(r"[^a-zA-Z0-9_-]", "", chat_id)[:80] or "current"
        self._active_log: Path | None = None

    def _task_state_path(self) -> Path:
        return self.root / ".agent" / "task-state" / f"{self.chat_id}.json"

    def set_task_checklist(self, items_json: str) -> str:
        try:
            parsed = json.loads(items_json)
            if isinstance(parsed, dict): parsed = parsed.get("items", [])
        except json.JSONDecodeError as exc:
            return f"Error: checklist JSON không hợp lệ: {exc}"
        if not isinstance(parsed, list):
            return "Error: checklist phải là một danh sách các bước."
        items = []
        for value in parsed[:12]:
            label = str(value.get("text", "") if isinstance(value, dict) else value).strip()
            if label:
                items.append({"text": label[:240], "status": "todo", "note": ""})
        if not items:
            return "Error: checklist cần ít nhất một bước cụ thể."
        state = {"chat_id": self.chat_id, "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"), "items": items}
        path = self._task_state_path(); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        self.on_activity("CHECKLIST|" + json.dumps(state, ensure_ascii=False))
        return f"Đã lưu checklist {len(items)} bước cho chat {self.chat_id}. Hãy đánh dấu từng bước trong khi làm."

    def update_task_step(self, index: int, status: str, note: str = "") -> str:
        path = self._task_state_path()
        try: state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError): return "Error: chưa có checklist; hãy gọi set_task_checklist trước."
        items = state.get("items", [])
        if not isinstance(index, int) or index < 0 or index >= len(items):
            return f"Error: index phải từ 0 đến {len(items)-1}."
        if status not in {"todo", "in_progress", "done", "blocked"}:
            return "Error: status phải là todo, in_progress, done hoặc blocked."
        items[index]["status"] = status
        items[index]["note"] = str(note or "")[:500]
        state["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        self.on_activity("CHECKLIST|" + json.dumps(state, ensure_ascii=False))
        return f"Đã cập nhật bước {index+1}/{len(items)}: {status}."

    def finish_task_checklist(self, note: str = "Đã hoàn tất sau khi agent rà soát.") -> None:
        path = self._task_state_path()
        try: state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError): return
        for item in state.get("items", []):
            if isinstance(item, dict):
                item["status"] = "done"
                item["note"] = str(note)[:500]
        state["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        self.on_activity("CHECKLIST|" + json.dumps(state, ensure_ascii=False))

    def write_project_launcher(self, run_command: str) -> str:
        if _BLOCKED.search(run_command or ""):
            raise ValueError("Lệnh launcher chứa thao tác phá/xóa dữ liệu bị chặn.")
        runner = project_launcher.write_project_launcher(self.root, run_command)
        return f"Đã cấu hình launcher của project: {runner}. Shortcut dùng icon tại {self.root / 'assets' / 'icons' / 'project.ico'}."

    def note_command(self, name: str, args: dict) -> str:
        if name == "set_task_checklist":
            try: display = "Lập checklist: " + " · ".join(str(x) for x in json.loads(args.get("items_json", "[]"))[:8])
            except Exception: display = "Lập checklist theo yêu cầu"
        elif name == "update_task_step":
            display = f"Checklist bước {int(args.get('index', 0))+1}: {args.get('status', '')} {args.get('note', '')}".strip()
        elif name == "write_project_launcher":
            display = f"Cấu hình run_project.bat: {args.get('run_command', '')}"
        elif name == "run_powershell":
            display = "powershell> " + str(args.get("command", ""))
        elif name == "run_python":
            display = f'python -u "{args.get("path", "")}"'
        elif name == "check_python":
            display = f'python -m py_compile "{args.get("path", "")}"'
        elif name == "write_file":
            display = f'Ghi file "{args.get("path", "")}" ({len(str(args.get("content", "")))} ký tự nội dung)'
        else:
            target = args.get("path") or args.get("url") or args.get("query") or args.get("filename") or ""
            display = f"{name} {target}".strip()
        record = {"time": datetime.now().astimezone().isoformat(timespec="seconds"), "tool": name, "display": display}
        path = self.root / ".agent" / "command-logs" / f"{self.chat_id}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.on_activity("COMMAND|" + display)
        return display

    def _safe(self, rel: str, *, allow_editable_file: bool = False, allow_reference: bool = False) -> Path:
        raw = Path(rel or ".").expanduser()
        p = (raw if raw.is_absolute() else self.root / raw).resolve()
        if p == self.root or self.root in p.parents:
            return p
        if allow_editable_file and self.editable_file is not None and p == self.editable_file:
            return p
        if allow_reference and p in self.reference_paths:
            return p
        raise ValueError("Đường dẫn nằm ngoài project và chưa được chọn làm file đầu vào/mục tiêu.")

    def _say_terminal(self, line: str) -> None:
        self.on_activity("TERMINAL|" + line.rstrip("\r\n"))
        if self._active_log:
            with self._active_log.open("a", encoding="utf-8") as log:
                log.write(line.rstrip("\r\n") + "\n")

    def _run_streamed(self, args: list[str], *, cwd: Path, label: str, timeout: int, env_overrides: dict | None = None) -> str:
        log_dir = self.root / ".agent" / "terminal-logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        self._active_log = log_dir / (datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".log")
        self._say_terminal("$ " + label)
        chunks=[]
        proc = subprocess.Popen(args, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace", bufsize=1,
            env={**os.environ, **(env_overrides or {}), "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"})
        lines=queue.Queue()
        def reader():
            try:
                for line in proc.stdout or []: lines.put(line)
            finally: lines.put(None)
        threading.Thread(target=reader,daemon=True).start()
        deadline=time.monotonic()+max(1,timeout)
        timed_out=False
        try:
            while True:
                try: line=lines.get(timeout=0.5)
                except queue.Empty:
                    if time.monotonic()>=deadline:
                        timed_out=True; proc.kill(); break
                    continue
                if line is None: break
                chunks.append(line); self._say_terminal(line)
                if sum(map(len,chunks))>24000: chunks=["".join(chunks)[-18000:]]
            if timed_out:
                proc.wait(timeout=3)
                self._say_terminal(f"Stopped after {timeout}s timeout.")
                return "Exit code: -1\nTimed out; process stopped.\n"+"".join(chunks)[-12000:]
            code=proc.wait(timeout=3)
        except Exception:
            proc.kill(); proc.wait(); raise
        finally:
            if proc.stdout: proc.stdout.close()
            self._active_log=None
        self._say_terminal(f"[exit code {code}]")
        output="".join(chunks).strip()
        return f"Exit code: {code}\n{output[-12000:]}" if output else f"Exit code: {code}"

    def list_dir(self, path: str = ".") -> str:
        p=self._safe(path)
        if not p.exists(): return f"Not found: {path}"
        if p.is_file(): return p.name
        names=sorted(x.name+("/" if x.is_dir() else "") for x in p.iterdir())
        return "\n".join(names) or "(empty)"

    def read_file(self, path: str) -> str:
        p=self._safe(path,allow_editable_file=True,allow_reference=True)
        if not p.is_file(): return f"Not a file: {path}"
        return p.read_text(encoding="utf-8",errors="replace")[:80000]

    def read_document(self,path: str) -> str:
        p=self._safe(path,allow_editable_file=True,allow_reference=True)
        return documents.read_document(str(p))

    def write_file(self, path: str, content: str) -> str:
        p=self._safe(path,allow_editable_file=True)
        p.parent.mkdir(parents=True,exist_ok=True)
        content,notes=_normalize_python_source(p,str(content))
        p.write_text(content,encoding="utf-8")
        summary=f"Wrote {p}"
        if notes: summary += "\n" + "\n".join(notes)
        if p.suffix.lower()==".py":
            try:
                import ast
                ast.parse(content,filename=str(p))
                summary += "\nKiểm tra cú pháp Python: hợp lệ."
            except SyntaxError as exc:
                summary += f"\nKiểm tra cú pháp Python còn lỗi tại dòng {exc.lineno}: {exc.msg}; agent cần tự sửa trước khi báo hoàn tất."
        return summary

    def check_python(self, path: str) -> str:
        p=self._safe(path)
        if not p.is_file() or p.suffix.lower()!=".py": return f"Not a Python file: {p}"
        return self._run_streamed([sys.executable,"-m","py_compile",str(p)],cwd=self.root,
            label=f'python -m py_compile "{p.relative_to(self.root).as_posix()}"',timeout=30)

    def run_python(self, path: str) -> str:
        path=path.strip().strip('"')
        if path.lower().startswith(("python ","python.exe ","py ")):
            path=path.split(None,1)[1].strip().strip('"')
        p=self._safe(path)
        if not p.is_file(): return f"Not a file: {path}"
        is_test = bool(re.search(r"(^|[\\/])tests?([\\/])|(^|[\\/])test_[^\\/]+\.py$|run_tests\.py$",str(p),re.I))
        if not is_test:
            try: source=p.read_text(encoding="utf-8",errors="replace")
            except OSError: source=""
            if p.name.casefold() in {"app.py","main.py","server.py"} or re.search(r"(?:\.launch|\.mainloop|uvicorn\.run|flask\.run|\.serve)\s*\(",source,re.I):
                return "APP_START_APPROVAL_REQUIRED: Application/server is not launched; use the Play button to approve and start it."
        env={**os.environ,"PYTHONIOENCODING":"utf-8","MPLBACKEND":"Agg",
             "PYTHONPATH":str(self.root)+(os.pathsep+os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")}
        try: display_path=p.relative_to(self.root).as_posix()
        except ValueError: display_path=str(p)
        # Keep the selected project's import path while executing the explicitly selected external file.
        return self._run_streamed([sys.executable,"-u",str(p)],cwd=self.root,label=f'python "{display_path}"',timeout=self.python_timeout,env_overrides=env)

    def run_powershell(self, command: str) -> str:
        if not command or not command.strip(): return "Error: command is empty"
        if _BLOCKED.search(command): return "Error: lệnh có khả năng phá/xóa dữ liệu hoặc tải mã bị chặn. Dùng tool phù hợp khác."
        if re.search(r"(?:^|[;&|]\s*)(?:start|start-process)\s|(?:^|\s)(?:python|python.exe|py)\s+.*(?:app|main|server)\.py\b|\b(?:uvicorn|flask)\s+run\b",command,re.I):
            return "APP_START_APPROVAL_REQUIRED: Use the Play button to approve starting an app/server."
        return self._run_streamed(["powershell.exe","-NoLogo","-NoProfile","-NonInteractive","-Command",command],cwd=self.root,label="powershell " + command[:200],timeout=self.python_timeout)

    def launch_python(self, path: str) -> str:
        if not self.allow_launch:
            return "Chưa khởi chạy ứng dụng. Người dùng cần nhấn nút Play để duyệt việc mở chương trình."
        p=self._safe(path)
        if not p.is_file() or p.suffix.lower()!=".py": return f"Not a Python file: {p}"
        flags=getattr(subprocess,"DETACHED_PROCESS",0)|getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0)
        proc=subprocess.Popen([sys.executable,str(p)],cwd=str(self.root),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
        return f"Started GUI process {proc.pid}: {p}"

    def open_file(self, path: str) -> str:
        p=self._safe(path,allow_editable_file=True)
        if not p.is_file(): return f"Not a file: {p}"
        os.startfile(str(p))
        return f"Opened {p}"

    def _priority_domains(self) -> list[str]:
        path=self.root/".agent"/"priority_sources.json"
        try: data=json.loads(path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError): return []
        if not isinstance(data,list): return []
        return [str(item.get("url","") if isinstance(item,dict) else item) for item in data if (item.get("url") if isinstance(item,dict) else item)]

    def _record_source(self,url: str,kind: str):
        path=self.root/".agent"/"research_sources.json"; path.parent.mkdir(parents=True,exist_ok=True)
        try: data=json.loads(path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError): data=[]
        if not isinstance(data,list): data=[]
        entry={"url":url,"type":kind,"recorded_at":datetime.now().astimezone().isoformat(timespec="seconds")}
        if not any(isinstance(item,dict) and item.get("url")==url for item in data): data.append(entry)
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

    def search_web(self, query: str) -> str:
        result=research.search_web(query,self._priority_domains())
        for url in re.findall(r"https?://[^\s)]+",result): self._record_source(url,"search")
        return result

    def fetch_url(self, url: str) -> str:
        result=research.fetch_url(url); self._record_source(url,"page")
        return result

    def download_image(self,url: str,filename: str) -> str:
        target=self._safe(filename)
        if target.suffix.lower() not in {".png",".jpg",".jpeg",".webp",".gif"}: target=target.with_suffix(".png")
        result=research.download_image(url,str(target)); self._record_source(url,"image")
        return result

    def download_compound_structure(self,compound: str,filename: str) -> str:
        target=self._safe(filename)
        if target.suffix.lower()!=".png": target=target.with_suffix(".png")
        result=research.download_compound_structure(compound,str(target))
        urls=re.findall(r"https?://[^\s]+",result)
        for url in urls: self._record_source(url,"molecular-structure")
        return result

    def fill_docx_template(self,template_path: str,output_path: str,fields_json: str,structure_image_path: str="") -> str:
        template=self._safe(template_path,allow_reference=True,allow_editable_file=True)
        output=self._safe(output_path)
        image=self._safe(structure_image_path) if structure_image_path else ""
        return documents.fill_docx_template(str(template),str(output),fields_json,str(image) if image else "")

    def fill_html_template(self,template_path: str,output_path: str,fields_json: str) -> str:
        template=self._safe(template_path,allow_reference=True,allow_editable_file=True)
        output=self._safe(output_path,allow_editable_file=True)
        return documents.fill_html_template(str(template),str(output),fields_json)

    def create_html_report(self,output_path: str,title: str,sections_json: str,sources_json: str="[]",image_path: str="") -> str:
        output=self._safe(output_path)
        image=self._safe(image_path) if image_path else ""
        return documents.create_html_report(str(output),title,sections_json,sources_json,str(image) if image else "")

    def convert_pdf_to_html(self,pdf_path: str,output_path: str,title: str="") -> str:
        source=self._safe(pdf_path,allow_editable_file=True,allow_reference=True)
        output=self._safe(output_path)
        return documents.convert_pdf_to_html(str(source),str(output),title or source.stem)

    def dispatch(self,name: str,args: dict) -> str:
        fn=getattr(self,name,None)
        if not fn: return f"Unknown tool: {name}"
        try: return str(fn(**args))
        except Exception as e: return f"Error: {type(e).__name__}: {e}"
