@echo off
setlocal
cd /d %~dp0
echo ============================================================
echo   GenericPharma-Agent - Day ma nguon len GitHub
echo ============================================================
echo.

set "GIT_DIR=C:\Users\PC\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd"
set "GIT=%GIT_DIR%\git.exe"
if exist "%GIT_DIR%" set "PATH=%GIT_DIR%;%PATH%"
if not exist "%GIT%" (
    where git >nul 2>&1
    if not errorlevel 1 (
        set "GIT=git"
    ) else (
        echo [ERROR] Khong tim thay git.exe tren may.
        pause
        exit /b 1
    )
)

if not exist ".git" (
    echo [1/4] Khoi tao Git repository...
    "%GIT%" init
    "%GIT%" branch -M main
)

echo [2/4] Kiem tra va gom file...
"%GIT%" add .
"%GIT%" commit -m "feat: GenericPharma-Agent - Local AI Agent for Generic Drug Research and Coding Automation"

echo.
set "DEFAULT_REPO_URL=https://github.com/trungyds16-coder/generic-pharma-agent.git"
set "REPO_URL=%DEFAULT_REPO_URL%"
if not "%~1"=="" set "REPO_URL=%~1"
echo ============================================================
echo Dang ket noi repository GitHub:
echo   %REPO_URL%
echo ============================================================

echo.
echo [3/4] Ket noi remote origin...
"%GIT%" remote remove origin >nul 2>&1
"%GIT%" remote add origin %REPO_URL%

echo [4/4] Dang day ma nguon len GitHub (nhanh main)...
"%GIT%" push -u origin main

if errorlevel 1 (
    echo.
    echo [!] Neu GitHub yeu cau dang nhap, hay dang nhap tren trinh duyet hoac nhap Personal Access Token.
) else (
    echo.
    echo [OK] Da tai toan bo ma nguon len GitHub thanh cong!
)

pause
