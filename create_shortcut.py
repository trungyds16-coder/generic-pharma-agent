"""Create a Windows desktop shortcut pointing to launcher.bat.

Tries win32com first; falls back to PowerShell if pywin32 is not installed.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
LAUNCHER = PROJECT_DIR / "launcher.bat"
SHORTCUT_NAME = "Local Agent.lnk"
DESKTOP = Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop"
SHORTCUT_PATH = DESKTOP / SHORTCUT_NAME
ICON_PATH = PROJECT_DIR / "assets" / "icons" / "project.ico"


def _create_with_win32com() -> bool:
    """Create shortcut using the pywin32 COM wrapper. Returns True on success."""
    try:
        import win32com.client  # type: ignore[import-untyped]
    except ImportError:
        return False

    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(SHORTCUT_PATH))
        shortcut.TargetPath = str(LAUNCHER)
        shortcut.WorkingDirectory = str(PROJECT_DIR)
        shortcut.Description = "Local AI Agent"
        if ICON_PATH.is_file():
            shortcut.IconLocation = str(ICON_PATH)
        shortcut.save()
        return True
    except Exception as exc:
        print(f"win32com failed: {exc}", file=sys.stderr)
        return False


def _create_with_powershell() -> bool:
    """Create shortcut via PowerShell (no external packages needed)."""
    icon_line = ""
    if ICON_PATH.is_file():
        icon_line = f'$s.IconLocation = "{ICON_PATH}"'

    ps_script = f"""
$ws  = New-Object -ComObject WScript.Shell
$s   = $ws.CreateShortcut("{SHORTCUT_PATH}")
$s.TargetPath       = "{LAUNCHER}"
$s.WorkingDirectory  = "{PROJECT_DIR}"
$s.Description       = "Local AI Agent"
{icon_line}
$s.Save()
"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except Exception as exc:
        print(f"PowerShell fallback failed: {exc}", file=sys.stderr)
        return False


def main() -> None:
    print(f"Creating desktop shortcut -> {SHORTCUT_PATH}")
    if _create_with_win32com() or _create_with_powershell():
        print(f"[OK] Shortcut created: {SHORTCUT_PATH}")
    else:
        print("[ERROR] Failed to create desktop shortcut.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
