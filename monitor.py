"""Giám sát nhẹ cho Local Agent: tài nguyên máy, tiến trình sinh code, file vừa thay đổi.

Không phụ thuộc cấu trúc cũ: agent.py chỉ gọi LIVE.*, app.py chỉ gọi render_markdown().
Chi phí: vài lệnh đọc số liệu mỗi 3 giây, nhỏ hơn nhiều so với model đang chạy.
"""
from __future__ import annotations

import threading
import time
import re
from pathlib import Path

try:
    import psutil
except ImportError:  # app vẫn chạy, chỉ thiếu phần đo máy
    psutil = None

_CODE_SUFFIXES = {".py", ".html", ".js", ".css", ".json", ".md", ".bat", ".yaml", ".yml"}
_SKIP_DIRS = {".agent", ".git", "__pycache__", "venv", ".venv", "node_modules"}


class _Live:
    """Trạng thái của lượt chạy hiện tại, agent ghi, giao diện đọc."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.writes: list[dict] = []  # code agent đã ghi, giữ qua các lượt
        self.reset()

    def record_write(self, path: str, content: str) -> None:
        with self._lock:
            item = {"path": path, "content": content, "at": time.strftime("%H:%M:%S")}
            self.writes.append(item)
            self.writes = self.writes[-8:]
            self.code_path = path
            self.code_preview = content
            self.code_language = Path(path).suffix.lower()

    def stream_code(self, path: str, content: str) -> None:
        with self._lock:
            self.code_path = path or self.code_path
            self.code_preview = content
            self.code_language = Path(self.code_path).suffix.lower() if self.code_path else ".py"

    def reset(self) -> None:
        with self._lock:
            self.running = False
            self.model = ""
            self.round = 0
            self.max_rounds = 0
            self.phase = "Rảnh"
            self.started = 0.0
            self.finished = 0.0
            self.chars = 0
            self.tokens = 0
            self.tok_per_s = 0.0
            self.preview = ""
            self.code_path = ""
            self.code_preview = ""
            self.code_language = ".py"
            self.round_started = 0.0
            self.last_usage: dict = {}

    def start(self, model: str, max_rounds: int) -> None:
        self.reset()
        with self._lock:
            self.running = True
            self.model = model
            self.max_rounds = max_rounds
            self.started = time.monotonic()
            self.phase = "Bắt đầu"

    def begin_round(self, index: int) -> None:
        with self._lock:
            self.round = index
            self.phase = "Model đang suy nghĩ / viết"
            self.chars = 0
            self.tokens = 0
            self.tok_per_s = 0.0
            self.preview = ""
            self.round_started = time.monotonic()

    def stream_update(self, text: str, tokens: int) -> None:
        with self._lock:
            self.chars = len(text)
            self.tokens = tokens
            elapsed = max(time.monotonic() - self.round_started, 0.001)
            self.tok_per_s = tokens / elapsed
            self.preview = text[-1200:]

    def set_phase(self, phase: str) -> None:
        with self._lock:
            self.phase = phase

    def finish(self, usage: dict | None = None) -> None:
        with self._lock:
            self.running = False
            self.finished = time.monotonic()
            self.phase = "Xong"
            if usage:
                self.last_usage = dict(usage)

    def view(self) -> dict:
        with self._lock:
            return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def latest_write(self) -> dict | None:
        with self._lock:
            return dict(self.writes[-1]) if self.writes else None


LIVE = _Live()

_proc_cache: dict[str, list] = {}


def _ollama_processes() -> list:
    """Cache tiến trình ollama để không phải quét toàn bộ tiến trình mỗi lần."""
    if psutil is None:
        return []
    procs = [p for p in _proc_cache.get("ollama", []) if p.is_running()]
    if not procs and time.monotonic() - _proc_cache.get("_scan", [0])[0] > 10:
        _proc_cache["_scan"] = [time.monotonic()]
        procs = []
        for p in psutil.process_iter(["name"]):
            if "ollama" in (p.info.get("name") or "").lower():
                try:
                    p.cpu_percent(None)  # mồi lần đo đầu
                except psutil.Error:
                    continue
                procs.append(p)
        _proc_cache["ollama"] = procs
    return procs


def machine_stats(client=None, disk: str = "D:\\") -> dict:
    out: dict = {"psutil": psutil is not None}
    if psutil is not None:
        mem = psutil.virtual_memory()
        out["cpu"] = psutil.cpu_percent(None)
        out["ram_used"] = mem.used / 2**30
        out["ram_total"] = mem.total / 2**30
        out["ram_pct"] = mem.percent
        try:
            out["disk_free"] = psutil.disk_usage(disk).free / 2**30
        except Exception:
            out["disk_free"] = None
        cpu = rss = 0.0
        for p in _ollama_processes():
            try:
                cpu += p.cpu_percent(None)
                rss += p.memory_info().rss
            except psutil.Error:
                pass
        out["ollama_cpu"] = cpu
        out["ollama_rss"] = rss / 2**30
    out["loaded"] = []
    if client is not None:
        try:
            for m in client.ps().models:
                out["loaded"].append({
                    "name": getattr(m, "model", None) or getattr(m, "name", "?"),
                    "size": (getattr(m, "size", 0) or 0) / 2**30,
                    "vram": (getattr(m, "size_vram", 0) or 0) / 2**30,
                    "expires": str(getattr(m, "expires_at", "") or "")[:19],
                })
        except Exception:
            pass
    return out


def _recent_files(project: Path, since: float, limit: int = 4) -> list[Path]:
    found: list[tuple[float, Path]] = []
    try:
        for p in project.rglob("*"):
            if any(part in _SKIP_DIRS for part in p.parts):
                continue
            if p.is_file() and p.suffix.lower() in _CODE_SUFFIXES:
                try:
                    mt = p.stat().st_mtime
                except OSError:
                    continue
                if mt >= since:
                    found.append((mt, p))
            if len(found) > 400:
                break
    except OSError:
        pass
    found.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in found[:limit]]


def _bar(pct: float, width: int = 12) -> str:
    filled = int(round(max(0.0, min(100.0, pct)) / 100 * width))
    return "█" * filled + "░" * (width - filled)


def render_markdown(client=None, project: Path | None = None, code_lines: int = 40) -> str:
    live = LIVE.view()
    st = machine_stats(client)
    lines = ["### Giám sát máy và tiến trình code"]

    # --- Máy ---
    if st["psutil"]:
        lines.append(
            f"**Máy:** CPU {st['cpu']:.0f}% `{_bar(st['cpu'])}` · "
            f"RAM {st['ram_used']:.1f}/{st['ram_total']:.1f} GB ({st['ram_pct']:.0f}%) `{_bar(st['ram_pct'])}`"
            + (f" · ổ D còn {st['disk_free']:.0f} GB" if st.get("disk_free") is not None else "")
        )
        lines.append(f"**Ollama:** CPU {st['ollama_cpu']:.0f}% · RAM {st['ollama_rss']:.1f} GB")
        if st["ram_pct"] >= 90:
            lines.append("⚠️ RAM trên 90%: máy có thể chậm hoặc đứng, nên đóng bớt ứng dụng hoặc chọn model nhỏ hơn.")
    else:
        lines.append("Chưa cài `psutil` nên chưa đo được CPU/RAM. Chạy: `pip install psutil`")
    if st["loaded"]:
        for m in st["loaded"]:
            where = "GPU" if m["vram"] > 0.1 else "CPU/RAM"
            lines.append(f"**Model đang nạp:** `{m['name']}` · {m['size']:.1f} GB ({where}) · giữ đến {m['expires'] or '?'}")
    else:
        lines.append("**Model đang nạp:** chưa có (sẽ nạp ở lần chat tiếp theo, mất vài chục giây)")

    # --- Tiến trình lượt chạy ---
    if live["running"]:
        total = max(live["max_rounds"], 1)
        elapsed = int(time.monotonic() - live["started"])
        lines.append(
            f"**Lượt chạy:** vòng {live['round']}/{total} `{_bar(live['round'] / total * 100)}` · {elapsed} giây · {live['phase']}"
        )
        if live["tokens"]:
            lines.append(f"**Đang sinh:** {live['tokens']} token · {live['chars']} ký tự · ~{live['tok_per_s']:.1f} token/giây")
        elif live["round"]:
            lines.append("**Đang sinh:** model đang đọc prompt (lần đầu hoặc sau khi nạp model có thể chờ khá lâu)")
    else:
        u = live["last_usage"]
        if u:
            eval_s = (u.get("eval_duration_ns", 0) or 0) / 1e9
            tps = (u.get("output_tokens", 0) / eval_s) if eval_s else 0
            lines.append(
                f"**Lượt gần nhất:** {u.get('rounds', 0)} vòng · {u.get('prompt_tokens', 0)} token vào · "
                f"{u.get('output_tokens', 0)} token ra · ~{tps:.1f} token/giây"
            )
        else:
            lines.append("**Lượt chạy:** đang rảnh")

    # --- Văn bản model đang viết ---
    if live["running"] and live["preview"]:
        lines.append("**Đang viết (đoạn mới nhất):**\n```\n" + live["preview"][-600:].replace("```", "'''") + "\n```")

    # --- Code agent đã ghi (ghi nhận trực tiếp từ công cụ write_file) ---
    with LIVE._lock:
        writes = list(LIVE.writes)
    if writes:
        lines.append("**Agent đã ghi file (mới nhất ở cuối):**")
        for w in writes[-5:]:
            lines.append(f"- {w['at']} · `{w['path']}` · {len(w['content'].splitlines())} dòng")
        lines.append("Nội dung code xem ở khung **Code agent vừa ghi** bên dưới.")
    else:
        lines.append("**Agent chưa ghi file nào.** Nếu bạn đã yêu cầu viết code mà vẫn trống, "
                     "model có thể chỉ in code ra chat thay vì gọi `write_file`.")

    # --- File vừa thay đổi ---
    recent = live["running"] or (live["finished"] and time.monotonic() - live["finished"] < 120)
    if project is not None and recent:
        since = time.time() - (time.monotonic() - (live["started"] or time.monotonic())) - 5
        files = _recent_files(project, since)
        if files:
            lines.append("**File vừa tạo/sửa trong lượt này:**")
            for p in files:
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                n = text.count("\n") + 1
                try:
                    rel = p.relative_to(project)
                except ValueError:
                    rel = p
                lines.append(f"- `{rel}` · {n} dòng · {p.stat().st_size / 1024:.1f} KB")
            newest = files[0]
            try:
                body = newest.read_text(encoding="utf-8", errors="replace").splitlines()
                tail = "\n".join(body[-code_lines:]).replace("```", "'''")
                lines.append(f"**{newest.name} · {code_lines} dòng cuối:**\n```\n{tail}\n```")
            except OSError:
                pass
    return "\n\n".join(lines)


_LANG = {".py": "python", ".html": "html", ".js": "javascript", ".css": "css", ".json": "json",
         ".md": "markdown", ".yaml": "yaml", ".yml": "yaml", ".bat": "shell", ".ps1": "shell"}


def latest_code(max_lines: int = 400) -> tuple[str, str, str]:
    """Trả về code đang sinh; nếu model đã ghi file thì trả về file vừa ghi."""
    live = LIVE.view()
    if live["running"] and live.get("code_preview"):
        code = live["code_preview"]
        lines = code.splitlines()
        shown = "\n".join(lines[-max_lines:])
        if len(lines) > max_lines:
            shown = f"# ... {len(lines) - max_lines} dòng đầu đã lược trong khung xem\n" + shown
        label = f"Đang sinh {live.get('code_path') or 'file'} · {len(lines)} dòng hiện có"
        return label, shown, _LANG.get(live.get("code_language", ".py"), "python")
    if live["running"] and live.get("preview"):
        # Some models stream code as assistant text before/without a write_file call.
        blocks = re.findall(r"```([\w.+-]*)\s*\n(.*?)```", live["preview"], re.S)
        if blocks:
            language, code = max(blocks, key=lambda block: len(block[1]))
            lines = code.strip("\n").splitlines()
            shown = "\n".join(lines[-max_lines:])
            if len(lines) > max_lines:
                shown = f"# ... {len(lines) - max_lines} dòng đầu đã lược trong khung xem\n" + shown
            lang = language.casefold()
            lang = {"py": "python", "js": "javascript", "ts": "typescript", "sh": "shell"}.get(lang, lang or "python")
            return f"Model đang stream code · {len(lines)} dòng", shown, lang
        candidate = live["preview"].strip()
        if re.search(r"(?m)^\s*(?:def |class |async def |from \w+ import |import \w+|function |const |let |var )", candidate):
            lines = candidate.splitlines()
            shown = "\n".join(lines[-max_lines:])
            return f"Model đang stream code · {len(lines)} dòng", shown, "python"
    w = LIVE.latest_write()
    if not w:
        return "Chưa có code nào được agent ghi trong phiên này", "", "python"
    lines = w["content"].splitlines()
    shown = "\n".join(lines[:max_lines])
    if len(lines) > max_lines:
        shown += f"\n# ... còn {len(lines) - max_lines} dòng nữa, mở file để xem đủ"
    label = f"{w['path']} · {len(lines)} dòng · ghi lúc {w['at']}"
    return label, shown, _LANG.get(Path(w["path"]).suffix.lower(), "python")
