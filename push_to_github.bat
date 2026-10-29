@echo off
setlocal
cd /d %~dp0
echo ============================================================
echo   GenericPharma-Agent - Day ma nguon len GitHub
echo ============================================================
echo.

set "GIT=C:\Users\PC\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe"
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
echo ============================================================
echo Repository GitHub mac dinh:
echo   %DEFAULT_REPO_URL%
echo.
echo Nhan [Enter] de tiep tuc, hoac dan URL khac neu can:
echo ============================================================
set /p USER_INPUT="URL GitHub [%DEFAULT_REPO_URL%]: "

if "%USER_INPUT%"=="" (
    set "REPO_URL=%DEFAULT_REPO_URL%"
) else (
    set "REPO_URL=%USER_INPUT%"
)

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
