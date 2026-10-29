# GenericPharma-Agent 💊🤖

> **A Lightweight Local AI Agent for Generic Drug Research, Patent Mining & Autonomous Software Engineering on Resource-Constrained PCs (Windows 11 / CPU-Only / 16GB RAM)**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform Windows 11](https://img.shields.io/badge/platform-Windows%2011-0078D6.svg)](https://microsoft.com)
[![Engine Ollama](https://img.shields.io/badge/engine-Ollama-black.svg)](https://ollama.ai)
[![License MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests 100% Passing](https://img.shields.io/badge/tests-166%20passed-brightgreen.svg)](run_tests.py)

---

## 🌐 English Overview

**GenericPharma-Agent** is an open-source, privacy-preserving autonomous AI agent operating **100% locally** on Windows 11. Built specifically for pharmaceutical scientists, generic drug formulators, and automation engineers working on standard office workstations without high-end GPUs.

### 🌟 Key Highlights

1. **Optimized for Low-Spec Hardware & CPU-Only Systems**:
   - **Zero GPU Required:** Runs inference directly on system CPU and RAM via Ollama.
   - **Intelligent Model Routing (`model_router.py`):** Automatically dispatches tasks to the most efficient local model:
     - 💻 **Complex coding, unit tests, and debugging:** Powered by **Qwen 2.5 Coder 7B (Q4_K_M)** – the state-of-the-art open-weights 7B coding model.
     - ⚡ **Precision tool calling, web search, and data extraction:** Powered by **Llama 3.2 3B** / **Qwen 3.5 4B** for near-instant responses with low memory footprint (~2 GB RAM).
   - **Configurable Context Window (4K / 8K):** Fine-tune memory cache (`num_ctx`) in `config.yaml` to ensure zero memory exhaustion on 16 GB machines.

2. **Generic Drug Research & Patent Intelligence**:
   - **Keyless Web & Patent Mining:** Scrapes and summarizes drug monographs and patents across authoritative priority portals: Google Patents, WIPO Patentscope, PubChem, ChEMBL, DailyMed, US FDA Orange Book, and EMA.
   - **Dual-Engine Molecular Structure Resolver:** Automatically fetches 2D chemical structure PNGs via PubChem CID API, with seamless automatic failover to the **U.S. National Cancer Institute (Cactus NCI) Resolver** if PubChem encounters IP rate-limits.
   - **Pharmaceutical Document Processing:** Parses Word (`.docx`), text-layer PDFs, and HTML. Auto-populates standard generic drug formulation review templates (`TEMPLATE_TONG_QUAN.docx`) and produces standalone scientific HTML dossiers with full source citations.

3. **Autonomous Coding & Self-Correcting Execution**:
   - **Parent-Child Workspace Architecture:** Every created subproject automatically provisions:
     - `run_project.bat`: Self-configuring single-click launcher.
     - `create_desktop_shortcut.bat`: Instant Desktop shortcut deployment with custom icon.
     - `assets/icons/project.ico`: Tailored application branding.
     - `plan.md`: Verified roadmap and acceptance criteria.
   - **Autonomous Loop:** Generates dynamic task checklists, compiles syntax checks (`py_compile`), executes unit tests, detects tracebacks, and self-repairs code autonomously.

4. **100% On-Premise Privacy**:
   - Confidential patent research, formulation data, and proprietary code never leave your local environment (`D:\AI-Data\local-agent`).

---

## 🇻🇳 Giới thiệu tiếng Việt

**GenericPharma-Agent** là hệ thống AI Agent cá nhân chạy **100% cục bộ (Local & Offline)** trên Windows 11, được thiết kế chuyên biệt để:
1. **Nghiên cứu & phát triển thuốc Generic**: Tra cứu tài liệu dược học, bằng sáng chế (patents), tổng hợp dữ liệu hoạt chất, tải công thức cấu tạo phân tử 2D và tự động lập báo cáo tổng quan kỹ thuật.
2. **Tự động hóa lập trình (Autonomous Coding Agent)**: Tự tạo dự án con, sinh mã nguồn, kiểm tra cú pháp, chạy unit test, tự sửa lỗi và tạo lối tắt Desktop 1-click.
3. **Tối ưu hóa đặc biệt cho máy tính cấu hình văn phòng/máy yếu**: Chạy mượt mà hoàn toàn bằng CPU với 16 GB RAM (hoặc tối thiểu 8 GB RAM), không đòi hỏi card đồ họa rời (GPU).

---

## 📂 Project Architecture / Cấu trúc thư mục

```text
generic-pharma-agent/
│
├── app/                  # Web application & Gradio UI module
│   ├── __init__.py
│   └── ui.py
│
├── core/                 # Core logging & foundation utilities
│   ├── __init__.py
│   └── logging_config.py
│
├── agents/               # LocalAgent coordination & reasoning loops
│   ├── __init__.py
│   └── local_agent.py
│
├── memory/               # Persistent chat history, checkpoints & usage tracking
│   ├── __init__.py
│   └── manager.py
│
├── tools/                # Workspace file tools, Python validator & research tools
│   ├── __init__.py
│   └── workspace_tools.py
│
├── tests/                # 166 automated unit test cases (100% Pass)
│   ├── __init__.py
│   ├── test_agent.py
│   ├── test_agents_module.py
│   ├── test_config.py
│   ├── test_documents.py
│   ├── test_memory.py
│   ├── test_model_router.py
│   ├── test_monitor.py
│   ├── test_project_launcher.py
│   ├── test_research.py
│   └── test_tools.py
│
├── data/
│   └── references/       # Sample generic drug Word & HTML templates
│
├── assets/icons/         # Windows project icon
├── logs/                 # app.log & error.log storage
│
├── launcher.bat          # 1-click Windows 11 launcher
├── main.py               # Production startup entry point
├── config.py             # Unified settings (.env + config.yaml)
├── config.yaml           # YAML configuration defaults
├── models.yaml           # Intelligent model routing matrix
├── requirements.txt      # Clean, locked dependencies
├── run_tests.py          # Test discoverer & runner
├── create_shortcut.py    # Desktop shortcut creator (Python)
├── create_shortcut.ps1   # Desktop shortcut creator (PowerShell)
└── push_to_github.bat    # GitHub synchronization utility
```

---

## ⚡ Quick Start / Hướng dẫn cài đặt

### 1. Prerequisites / Yêu cầu
- **OS**: Windows 11 or Windows 10 x64
- **Python**: 3.11+
- **Ollama**: Installed and running ([ollama.ai](https://ollama.ai))
- Pull recommended local models:
  ```shell
  ollama pull qwen2.5-coder:7b
  ollama pull llama3.2:3b
  ollama pull qwen3.5:4b
  ```

### 2. Installation / Cài đặt thư viện
```shell
git clone https://github.com/trungyds16-coder/generic-pharma-agent.git
cd generic-pharma-agent
pip install -r requirements.txt
```

### 3. Launch the Application / Khởi chạy
- **Option 1 (Fastest):** Double-click `launcher.bat` or the `Local Agent` Desktop shortcut.
- **Option 2 (Terminal):**
  ```shell
  python main.py
  ```
The Web UI opens automatically in your browser at: `http://127.0.0.1:7860`.

---

## 🧪 Verification & Unit Tests

Run the full automated test suite (166 test cases covering all modules):
```shell
python run_tests.py
```
Expected output:
```text
Ran 166 tests in 0.5s
OK
```

---

## 📦 Build Windows Executable (.exe)

Compile into a standalone executable using PyInstaller:
```shell
pip install pyinstaller
pyinstaller --onefile --name "GenericPharmaAgent" --icon "assets/icons/project.ico" main.py
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
