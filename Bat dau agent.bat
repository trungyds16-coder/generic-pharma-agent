@echo off
cd /d D:\AI-Data\local-agent
set OLLAMA_MODELS=D:\OllamaModels
set GRADIO_TEMP_DIR=D:\AI-Data\local-agent\data\cache
set HF_HOME=D:\AI-Data\local-agent\data\cache\hf
set PIP_CACHE_DIR=D:\AI-Data\local-agent\data\pip-cache
if not exist "D:\AI-Data\local-agent\data\cache" mkdir "D:\AI-Data\local-agent\data\cache"
if not exist "D:\AI-Data\local-agent\data\pip-cache" mkdir "D:\AI-Data\local-agent\data\pip-cache"
where ollama >nul 2>&1
if errorlevel 1 echo Khong tim thay Ollama trong PATH.
if not errorlevel 1 (
  curl -fsS http://127.0.0.1:11434/api/tags >nul 2>nul
  if errorlevel 1 start "" /min ollama serve
)
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  ".venv\Scripts\python.exe" -m pip install --no-cache-dir -r requirements.txt
)
".venv\Scripts\python.exe" app.py
pause
