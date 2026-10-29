from __future__ import annotations

import struct
from pathlib import Path


def _default_icon() -> bytes:
    """Build a small self-contained 32x32 calculator-style Windows icon."""
    width = height = 32
    pixels = []
    for y in range(height - 1, -1, -1):
        for x in range(width):
            # BGRA pixels. Navy tile, white calculator body, blue screen and keys.
            color = (57, 54, 22, 255)
            if 6 <= x <= 25 and 3 <= y <= 28:
                color = (246, 248, 250, 255)
            if 9 <= x <= 22 and 7 <= y <= 12:
                color = (194, 123, 20, 255)
            if (13 <= x <= 15 or 19 <= x <= 21) and (16 <= y <= 18 or 21 <= y <= 23):
                color = (180, 112, 27, 255)
            if 9 <= x <= 12 and 16 <= y <= 18:
                color = (180, 112, 27, 255)
            pixels.extend(color)
    xor_bitmap = bytes(pixels)
    and_mask = bytes(((width + 31) // 32) * 4 * height)
    bitmap = struct.pack("<IiiHHIIiiII", 40, width, height * 2, 1, 32, 0, len(xor_bitmap) + len(and_mask), 0, 0, 0, 0) + xor_bitmap + and_mask
    entry = struct.pack("<BBBBHHII", width, height, 0, 0, 1, 32, len(bitmap), 22)
    return struct.pack("<HHH", 0, 1, 1) + entry + bitmap


DEFAULT_RUNNER = r'''@echo off
setlocal
cd /d "%~dp0"
title Local Agent Project
set "RESULT=0"
set "PYTHON=%~dp0.venv\Scripts\python.exe"
if exist "%PYTHON%" set "PATH=%~dp0.venv\Scripts;%PATH%"
if not exist "%PYTHON%" set "PYTHON=python"

if exist "app.py" set "ENTRYPOINT=app.py"
if not defined ENTRYPOINT if exist "main.py" set "ENTRYPOINT=main.py"
if not defined ENTRYPOINT if exist "run.py" set "ENTRYPOINT=run.py"
if defined ENTRYPOINT goto run_python

if exist "package.json" goto run_node
if exist "index.html" goto run_html
for %%F in (*.csproj) do if exist "%%~fF" (set "DOTNET_PROJECT=%%~fF"& goto run_dotnet)
goto no_entrypoint

:run_python
echo Running Python project: %ENTRYPOINT%
"%PYTHON%" -u "%ENTRYPOINT%"
set "RESULT=%ERRORLEVEL%"
goto finish

:run_node
where npm >nul 2>nul
if errorlevel 1 (echo npm was not found in PATH.& set "RESULT=1"& goto finish)
echo Starting Node project with npm start...
call npm start
set "RESULT=%ERRORLEVEL%"
if not errorlevel 1 goto finish
echo npm start was unavailable; trying npm run dev...
call npm run dev
set "RESULT=%ERRORLEVEL%"
goto finish

:run_html
echo Opening project page in the default browser...
start "" "%~dp0index.html"
goto finish

:run_dotnet
echo Running .NET project: %DOTNET_PROJECT%
dotnet run --project "%DOTNET_PROJECT%"
set "RESULT=%ERRORLEVEL%"
goto finish

:no_entrypoint
echo No known application entry point was found.
echo Ask the Local Agent to update run_project.bat for this project's actual start command.
set "RESULT=2"

:finish
echo.
echo Finished with exit code %RESULT%.
pause
exit /b %RESULT%
'''


DESKTOP_SHORTCUT = r'''@echo off
setlocal
for %%I in ("%~dp0.") do set "PROJECT_NAME=%%~nxI"
set "PROJECT_DIR=%~dp0"
set "SHORTCUT=%USERPROFILE%\Desktop\%PROJECT_NAME%.lnk"
set "TARGET=%~dp0run_project.bat"
set "ICON=%~dp0assets\icons\project.ico"
powershell.exe -NoLogo -NoProfile -NonInteractive -Command "$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut($env:SHORTCUT); $s.TargetPath=$env:TARGET; $s.WorkingDirectory=$env:PROJECT_DIR; $s.IconLocation=$env:ICON; $s.Description='Run project '+$env:PROJECT_NAME; $s.Save()"
if errorlevel 1 (
  echo Could not create the desktop shortcut. Check the Windows PowerShell installation.
  pause
  exit /b 1
)
echo Created desktop shortcut: %SHORTCUT%
pause
'''


def ensure_project_launcher(project: Path) -> tuple[Path, Path, Path]:
    project = project.resolve()
    icon_dir = project / "assets" / "icons"
    icon_dir.mkdir(parents=True, exist_ok=True)
    icon = icon_dir / "project.ico"
    if not icon.exists():
        icon.write_bytes(_default_icon())
    runner = project / "run_project.bat"
    if not runner.exists():
        runner.write_text(DEFAULT_RUNNER, encoding="utf-8")
    shortcut = project / "create_desktop_shortcut.bat"
    if not shortcut.exists():
        shortcut.write_text(DESKTOP_SHORTCUT, encoding="utf-8")
    return runner, shortcut, icon


def write_project_launcher(project: Path, run_command: str) -> Path:
    project = project.resolve()
    command = (run_command or "").strip()
    if not command:
        raise ValueError("Cần cung cấp lệnh khởi chạy thật của project.")
    if "\n" in command or "\r" in command:
        raise ValueError("Chỉ nhận một lệnh khởi chạy trên một dòng.")
    ensure_project_launcher(project)
    runner = project / "run_project.bat"
    lines = [
        "@echo off", "setlocal", 'cd /d "%~dp0"',
        f'title {project.name}',
        'set "PYTHON=%~dp0.venv\Scripts\python.exe"',
        'if exist "%PYTHON%" set "PATH=%~dp0.venv\Scripts;%PATH%"',
        'if not exist "%PYTHON%" set "PYTHON=python"',
        "echo Project: %CD%", f"echo Command: {command}", command,
        'set "RESULT=%ERRORLEVEL%"', "echo.", "echo Finished with exit code %RESULT%.", "pause", "exit /b %RESULT%",
    ]
    runner.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return runner
