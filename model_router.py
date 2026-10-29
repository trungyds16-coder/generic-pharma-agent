"""Chọn model Ollama theo loại việc và RAM, đọc cấu hình từ models.yaml."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

AUTO_MODEL_OPTION = "Tự chọn theo việc"
_CONFIG = Path(__file__).resolve().parent / "models.yaml"
_DEFAULT = {
    "auto": {"enabled": True, "ram_headroom_gb": 4, "gb_per_billion": 0.6},
    "profiles": {
        "light": {"prefer": ["qwen3.5:4b", "qwen2.5-coder:7b"]},
        "code": {"prefer": ["qwen3.5:9b", "qwen3.5:4b", "qwen2.5-coder:7b"]},
    },
    "code_keywords": ["code", "lỗi", "test", "python", "html", "app"],
    "escalate_keywords": ["tiếp tục sửa lỗi", "vẫn lỗi"],
}


def load_config() -> dict:
    try:
        data = yaml.safe_load(_CONFIG.read_text(encoding="utf-8-sig")) or {}
    except (OSError, yaml.YAMLError):
        data = {}
    merged = {**_DEFAULT, **data}
    merged["auto"] = {**_DEFAULT["auto"], **(data.get("auto") or {})}
    return merged


def auto_enabled() -> bool:
    return bool(load_config()["auto"].get("enabled", True))


def _size_gb(name: str, per_b: float) -> float:
    m = re.search(r"[:\-_](\d+(?:\.\d+)?)b\b", name.lower())
    return (float(m.group(1)) if m else 7.0) * per_b


def _match(pref: str, installed: list[str]) -> str | None:
    for name in installed:
        if name == pref or name.startswith(pref + "-"):
            return name
    return None


def _ram_total_gb() -> float | None:
    try:
        import psutil
        return psutil.virtual_memory().total / 2**30
    except Exception:
        return None


def classify(message: str, history: list | None = None, cfg: dict | None = None) -> tuple[str, str]:
    cfg = cfg or load_config()
    text = (message or "").lower()
    last_assistant = next((t.get("content", "") for t in reversed(history or []) if t.get("role") == "assistant"), "")
    if any(k in text for k in cfg.get("escalate_keywords", [])) or "Chưa hoàn thành" in str(last_assistant)[:300]:
        return "code", "việc trước chưa đạt nên dùng model mạnh hơn"
    if any(k in text for k in cfg.get("code_keywords", [])):
        return "code", "yêu cầu liên quan đến code"
    return "light", "việc nhẹ (hỏi đáp, tra cứu, báo cáo)"


def choose_model(message: str, installed: list[str], history: list | None = None, default: str = "") -> tuple[str, str]:
    cfg = load_config()
    profile, why = classify(message, history, cfg)
    per_b = float(cfg["auto"].get("gb_per_billion", 0.6))
    headroom = float(cfg["auto"].get("ram_headroom_gb", 4))
    ram = _ram_total_gb()
    skipped = []
    for pref in cfg["profiles"].get(profile, {}).get("prefer", []):
        name = _match(pref, installed)
        if not name:
            continue
        need = _size_gb(name, per_b) + headroom
        if ram is not None and need > ram:
            skipped.append(name)
            continue
        note = f" (bỏ qua {', '.join(skipped)} vì quá nặng cho RAM)" if skipped else ""
        return name, f"{why}{note}"
    fallback = default if default in installed else (installed[0] if installed else default)
    if skipped:
        return fallback, f"{why}; {', '.join(skipped)} quá nặng cho RAM nên dùng model mặc định"
    return fallback, f"{why}; không có model ưu tiên nào đã cài nên dùng model mặc định"
