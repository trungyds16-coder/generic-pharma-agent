# GenericPharma-Agent 💊🤖

> **Local AI Agent Tối Ưu Cho Nghiên Cứu Thuốc Generic & Tự Động Hóa Lập Trình Trên Máy Cấu Hình Khiêm Tốn (Windows 11 / CPU / 16GB RAM)**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform Windows 11](https://img.shields.io/badge/platform-Windows%2011-0078D6.svg)](https://microsoft.com)
[![Ollama](https://img.shields.io/badge/engine-Ollama-black.svg)](https://ollama.ai)
[![License MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests 100% Passing](https://img.shields.io/badge/tests-165%20passed-brightgreen.svg)](run_tests.py)

---

## 🌟 Giới thiệu tổng quan

**GenericPharma-Agent** là hệ thống AI Agent cá nhân chạy **100% cục bộ (Local & Offline)** trên Windows 11, được thiết kế chuyên biệt để:
1. **Hỗ trợ nghiên cứu phát triển thuốc Generic**: Tra cứu tài liệu dược học, bằng sáng chế (patents), tổng hợp dữ liệu hoạt chất, tải công thức cấu tạo phân tử và lập báo cáo tổng quan kỹ thuật.
2. **Tự động hóa lập trình (Autonomous Coding Agent)**: Tự tạo dự án con, sinh mã nguồn, tự động kiểm tra cú pháp, chạy unit test, tự sửa lỗi và tạo lối tắt Desktop 1-click.
3. **Tối ưu hóa đặc biệt cho máy tính cấu hình văn phòng/máy yếu**: Chạy mượt mà hoàn toàn bằng CPU với 16 GB RAM (hoặc tối thiểu 8 GB RAM), không đòi hỏi card đồ họa rời (GPU).

---

## 🚀 Các tính năng cốt lõi

### 1. 💻 Tối ưu cho máy yếu & CPU (Resource-Constrained Optimization)
- **Không cần GPU đắt tiền:** Chạy suy luận trực tiếp trên CPU và RAM hệ thống thông qua Ollama.
- **Định tuyến mô hình thông minh (`model_router.py`):**
  - Tác vụ lập trình, gỡ lỗi, kiểm thử: Tự chọn **Qwen 2.5 Coder 7B (bản lượng tử 4-bit Q4_K_M)** – model coding 7B mạnh nhất hiện nay.
  - Tác vụ tra cứu nhanh, đọc tài liệu, tóm tắt: Tự chuyển sang **Qwen 3.5 4B** hoặc **Llama 3.2 3B** để phản hồi tức thì và tiết kiệm RAM.
- **Quản lý ngữ cảnh (Context 4K/8K):** Tùy chỉnh linh hoạt độ dài bộ nhớ làm việc (`num_ctx`) trong `config.yaml` để cân bằng giữa tốc độ xử lý và khả năng ghi nhớ.

### 2. 🔬 Bộ công cụ nghiên cứu dược phẩm & thuốc Generic chuyên sâu
- **Tra cứu web & bằng sáng chế không cần API Key:** Tìm kiếm thông tin thuốc và văn bằng bảo hộ từ danh mục nguồn ưu tiên (Google Patents, WIPO, PubChem, ChEMBL, DailyMed, US FDA Orange Book, EMA).
- **Tải cấu trúc phân tử tự động (Dual-Engine Resolver):**
  - Tự động truy vấn PubChem theo tên hoạt chất/CAS/InChIKey để tải ảnh cấu trúc phân tử 2D độ nét cao.
  - Tích hợp cổng dự phòng **Cactus NCI Chemical Structure Resolver** của Viện Ung thư Quốc gia Hoa Kỳ, đảm bảo quá trình tải ảnh phân tử không bao giờ bị gián đoạn.
- **Xử lý tài liệu dược phẩm đa định dạng:**
  - Đọc và bóc tách nội dung từ tài liệu kỹ thuật Word (`.docx`), PDF quét dạng văn bản và trang HTML.
  - Tự động điền dữ liệu nghiên cứu vào biểu mẫu báo cáo tổng quan (`TEMPLATE_TONG_QUAN.docx`).
  - Xuất báo cáo khoa học dạng HTML độc lập, chuẩn thẩm mỹ, liên kết nguồn tài liệu đầy đủ.

### 3. 🛠️ Tự động hóa dự án & Lập trình tự trị (Autonomous Workflow)
- **Mô hình Quản lý Dự án Mẹ - Con:** Mỗi dự án con được tạo mới đều có thư mục riêng, tự động sinh:
  - `run_project.bat`: Khởi chạy ứng dụng con chỉ với 1 nhấp đúp chuột.
  - `create_desktop_shortcut.bat`: Đưa ứng dụng con ra màn hình Desktop.
  - `assets/icons/project.ico`: File icon nhận diện riêng.
  - `plan.md`: Bản kế hoạch mục tiêu và tiêu chuẩn nghiệm thu.
- **Quy trình tự khép kín (Self-Correction):** Lập checklist -> Viết code -> Biên dịch kiểm tra cú pháp -> Chạy Unit Test -> Tự phát hiện lỗi và sửa chữa cho đến khi hoàn thành.

### 4. 🔒 Bảo mật dữ liệu tuyệt đối (100% Local Privacy)
- Toàn bộ hồ sơ sáng chế, công thức nghiên cứu thuốc và mã nguồn dự án được lưu trữ hoàn toàn trên ổ cứng cục bộ (`D:\AI-Data\local-agent`), không gửi dữ liệu ra máy chủ bên thứ ba.

---

## 📂 Cấu trúc thư mục chuẩn Production

```text
local-agent/
│
├── app/                  # Module Web UI (Gradio Dashboard)
│   ├── __init__.py
│   └── ui.py
│
├── core/                 # Hệ thống Logging và tiện ích nền tảng
│   ├── __init__.py
│   └── logging_config.py
│
├── agents/               # Điều phối Agent và vòng lặp suy luận
│   ├── __init__.py
│   └── local_agent.py
│
├── memory/               # Quản lý bộ nhớ hội thoại, checkpoints & usage
│   ├── __init__.py
│   └── manager.py
│
├── tools/                # Bộ công cụ workspace, tra cứu web & tài liệu
│   ├── __init__.py
│   └── workspace_tools.py
│
├── tests/                # Bộ 165 Unit Tests tự động (100% Pass)
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
│   └── references/       # Biểu mẫu mẫu Word & HTML tổng quan dược
│
├── assets/icons/         # Icon Windows cho lối tắt Desktop
│
├── logs/                 # Nhật ký hoạt động app.log và error.log
│
├── launcher.bat          # File 1-click khởi chạy trên Windows 11
├── main.py               # Điểm khởi động chuẩn Production
├── config.py             # Cấu hình thống nhất (.env + config.yaml)
├── config.yaml           # Cấu hình mặc định hệ thống
├── requirements.txt      # Thư viện phụ thuộc
├── run_tests.py          # Runner kiểm thử tự động
├── create_shortcut.py    # Script tạo Desktop Shortcut (Python)
├── create_shortcut.ps1   # Script tạo Desktop Shortcut (PowerShell)
└── push_to_github.bat    # Script tiện ích đẩy mã nguồn lên GitHub
```

---

## ⚡ Hướng dẫn cài đặt & Triển khai

### 1. Chuẩn bị môi trường
- Hệ điều hành: **Windows 11 / 10 x64**
- Cài đặt **Python 3.11+** và [Ollama](https://ollama.ai).
- Tải model khuyến nghị trên Ollama:
  ```shell
  ollama pull qwen2.5-coder:7b
  ollama pull qwen3.5:4b
  ```

### 2. Cài đặt thư viện
Tại thư mục dự án, chạy:
```shell
pip install -r requirements.txt
```

### 3. Khởi chạy ứng dụng
- **Cách 1 (Nhanh nhất):** Nhấp đúp chuột vào file `launcher.bat` hoặc shortcut `Local Agent` ngoài Desktop.
- **Cách 2:** Chạy lệnh:
  ```shell
  python main.py
  ```
Giao diện sẽ tự động mở trên trình duyệt tại: `http://127.0.0.1:7860`.

---

## 🧪 Kiểm thử hệ thống (Unit Tests)

Dự án đi kèm bộ 165 test cases kiểm thử toàn diện:
```shell
python run_tests.py
```
Kết quả kỳ vọng:
```text
Ran 165 tests
OK
```

---

## 📦 Đóng gói thành file `.exe` độc lập

```shell
pip install pyinstaller
pyinstaller --onefile --name "GenericPharmaAgent" --icon "assets/icons/project.ico" main.py
```

---

## 📄 Bản quyền (License)

Dự án được phát hành theo giấy phép [MIT License](LICENSE).
