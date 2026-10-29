"""Prompt presets, structured prompt builder, and Gemini/Copilot prompt generator.

Provides ready-to-use bilingual templates for:
- Natural mathematical expression applications (fractions, square roots, integrals).
- 2D/3D mini games with physics, collision detection, and canvas rendering.
- Generic pharmaceutical monographs with 2D chemical structure retrieval.
- Custom Windows application icons (.ico) with branding.
- Meta-prompts to query Gemini/ChatGPT for production-grade specifications.
"""
from __future__ import annotations

from typing import Any, Dict, List


GLOSSARY: Dict[str, Dict[str, str]] = {
    "math_natural_input": {
        "vi": "Nhập liệu toán học tự nhiên (phân số xếp chồng tử/mẫu, căn thức có thanh ngang vinculum, số mũ subscript/superscript mà không bắt người dùng gõ mã LaTeX).",
        "en": "Natural mathematical WYSIWYG input (stacked fractions with horizontal bar, square root radical with vinculum over expression, exponents without raw LaTeX).",
        "keywords": "WYSIWYG math, stacked fraction, vinculum, radical sign, AST parser, tokenization, Canvas rendering",
    },
    "graphics_2d_canvas": {
        "vi": "Đồ họa 2D Canvas (vẽ trực tiếp pixel/vector, chống nhấp nháy double-buffering, vòng lặp game 60 FPS, phát hiện va chạm AABB).",
        "en": "2D Canvas Graphics (vector/pixel drawing, double buffering, 60 FPS update loop, axis-aligned bounding box AABB collision detection).",
        "keywords": "Canvas, double buffering, requestAnimationFrame, delta time, collision detection, sprite sheet",
    },
    "graphics_3d_engine": {
        "vi": "Đồ họa 3D nhẹ tối ưu cho CPU (không đòi hỏi card GPU rời, dùng Ursina Engine / Panda3D trên Python hoặc Three.js trên Web).",
        "en": "Lightweight 3D graphics optimized for CPU-only systems (Ursina Engine / Panda3D for Python or WebGL / Three.js for HTML).",
        "keywords": "mesh, vertex, texture mapping, wireframe, camera viewport, perspective projection",
    },
    "pharma_chemistry": {
        "vi": "Dược học & Hóa học cấu trúc (tra cứu hoạt chất, tải công thức phân tử 2D từ PubChem / Cactus NCI, đối chiếu bằng sáng chế và tiêu chuẩn Dược điển).",
        "en": "Pharmaceutical & Chemical Informatics (active pharmaceutical ingredient lookup, 2D molecular structure diagram from PubChem / Cactus NCI, patent expiry, pharmacopeia standards).",
        "keywords": "PubChem CID, CAS registry, SMILES, InChIKey, Cactus NCI resolver, dosage form, patent mining",
    },
    "windows_desktop_deployment": {
        "vi": "Đóng gói ứng dụng Windows 11 (tự tạo launcher.bat, file icon .ico 32x32 pixel chuẩn Windows, và lối tắt Desktop .lnk).",
        "en": "Windows 11 desktop deployment (auto-generating launcher.bat, standalone 32x32 .ico icon, and Desktop .lnk shortcut).",
        "keywords": "launcher.bat, Windows shortcut .lnk, WScript.Shell, 32x32 ico bitmap, PyInstaller single-file",
    },
}


PROMPT_PRESETS: Dict[str, Dict[str, str]] = {
    "math_calculator": {
        "title": "📐 [Toán học] Máy tính nhập Phân số & Căn thức tự nhiên (WYSIWYG)",
        "prompt": (
            "DỰ ÁN: Máy tính Desktop thông minh với bộ nhập liệu Toán học tự nhiên (Natural Math Input)\n"
            "TÊN PROJECT: natural-math-calc\n"
            "GIAO DIỆN & ICON: Tkinter GUI hiện đại, icon hình máy tính khoa học tông xanh navy (32x32 .ico)\n\n"
            "YÊU CẦU CHỨC NĂNG CỐT LÕI:\n"
            "1. Nhập liệu trực quan tự nhiên (Natural WYSIWYG Math):\n"
            "   - Cho phép người dùng nhập phân số trực quan (tử số nằm trên mẫu số với vạch ngang phân cách rõ ràng).\n"
            "   - Cho phép chèn dấu căn bậc hai (√) với thanh ngang (vinculum) tự động kéo dài bao trùm toàn bộ biểu thức bên trong.\n"
            "   - Hỗ trợ số mũ, lũy thừa, các hằng số π, e, và hàm lượng giác sin, cos, tan (hiển thị rõ chế độ Radian / Degree).\n"
            "   - Người dùng KHÔNG CẦN phải gõ code hay cú pháp phức tạp; có bàn phím ảo toán học trên màn hình và phím tắt tiện lợi.\n"
            "2. Vẽ đồ thị hàm số & Tính tích phân xác định:\n"
            "   - Nhập hàm số f(x), chọn khoảng [a, b] để vẽ đồ thị tự động trên Canvas.\n"
            "   - Tính diện tích tích phân và TÔ MÀU trực quan vùng giới hạn giữa đồ thị và trục hoành (f(x) ≥ 0 tô xanh lục, f(x) < 0 tô cam nhạt).\n"
            "3. Ràng buộc kỹ thuật:\n"
            "   - Viết hoàn toàn bằng Python chuẩn và Tkinter Canvas; không phụ thuộc các thư viện nặng ngoài (zero-bloat).\n"
            "4. Kiểm thử & Bàn giao:\n"
            "   - Viết bộ Unit Test kiểm tra tính toán phân số, căn thức và parser biểu thức.\n"
            "   - Tự động tạo launcher.bat và shortcut ngoài Desktop kèm icon máy tính."
        ),
    },
    "game_2d_canvas": {
        "title": "🎮 [Game 2D] Mini Game Canvas 60 FPS, va chạm vật lý & phím bấm",
        "prompt": (
            "DỰ ÁN: Mini Game 2D Arcade trên Windows (Chạy mượt trên CPU)\n"
            "TÊN PROJECT: retro-space-defender\n"
            "GIAO DIỆN & ICON: Đồ họa Canvas 2D phong cách Retro Arcade, icon hình tàu vũ trụ màu neon (assets/icons/project.ico)\n\n"
            "YÊU CẦU CHỨC NĂNG CỐT LÕI:\n"
            "1. Game Loop & Điều khiển:\n"
            "   - Vòng lặp cập nhật 60 FPS mượt mà sử dụng Canvas Tkinter (hoặc Pygame nếu có sẵn).\n"
            "   - Điều khiển phi thuyền bằng phím mũi tên hoặc A/D để di chuyển, Spacebar để bắn đạn laze.\n"
            "2. Đồ họa & Cơ chế Vật lý:\n"
            "   - Phát hiện va chạm (AABB Collision Detection) giữa đạn, phi thuyền và các thiên thạch/quái vật rơi tự do.\n"
            "   - Hệ thống tính điểm (Score), mạng sống (Lives: 3), và các đợt quái tăng dần độ khó (Wave Difficulty scaling).\n"
            "   - Hiệu ứng nổ hạt đơn giản (Particle Explosion) khi thiên thạch bị bắn trúng.\n"
            "3. Âm thanh & Trạng thái:\n"
            "   - Âm thanh beep phản hồi qua winsound tích hợp sẵn của Windows.\n"
            "   - Các màn hình: Menu chính, Đang chơi, Tạm dừng (Pause), và Game Over kèm nút Chơi lại (Restart).\n"
            "4. Đóng gói:\n"
            "   - Sinh file launcher.bat và tạo shortcut Desktop 1-click để mở chơi ngay."
        ),
    },
    "game_3d_mini": {
        "title": "🕹️ [Game 3D] Mini Game Mê cung 3D góc nhìn thứ nhất (CPU-Friendly)",
        "prompt": (
            "DỰ ÁN: 3D Mini Labyrinth Explorer (Góc nhìn thứ nhất, chạy nhẹ trên máy CPU)\n"
            "TÊN PROJECT: mini-3d-maze\n"
            "CÔNG NGHỆ: Sử dụng WebGL Three.js (chạy trực tiếp trong file index.html trên trình duyệt) hoặc Ursina Python\n\n"
            "YÊU CẦU CHỨC NĂNG CỐT LÕI:\n"
            "1. Không gian 3D:\n"
            "   - Tạo mê cung 3D ngẫu nhiên với tường gạch, sàn và bầu trời (Skybox).\n"
            "   - Camera góc nhìn thứ nhất (FPS Camera): chuột để xoay góc nhìn 360 độ, phím W-A-S-D để di chuyển.\n"
            "2. Cơ chế Game:\n"
            "   - Va chạm với tường 3D (không đi xuyên tường).\n"
            "   - Thu thập các viên ngọc phát sáng rải rác trong mê cung và tìm cửa thoát hiểm (Exit Portal).\n"
            "   - Đồng hồ đếm ngược thời gian và bảng tổng kết thành tích.\n"
            "3. Đóng gói:\n"
            "   - Tự động mở trình duyệt Edge/Chrome khi bấm nút Play hoặc nhấp launcher.bat."
        ),
    },
    "pharma_research": {
        "title": "💊 [Dược học] Nghiên cứu thuốc Generic, tải ảnh cấu trúc 2D & xuất Word",
        "prompt": (
            "DỰ ÁN: Báo cáo Tổng quan Kỹ thuật & Hồ sơ Hoạt chất Dược phẩm Generic\n"
            "TÊN PROJECT: pharma-atorvastatin-dossier\n"
            "HOẠT CHẤT MỤC TIÊU: Atorvastatin (hoặc thay thế bằng hoạt chất bạn muốn)\n\n"
            "YÊU CẦU CHỨC NĂNG CỐT LÕI:\n"
            "1. Tra cứu Dữ liệu Khoa học & Bằng sáng chế:\n"
            "   - Tìm kiếm thông tin hoạt chất trên PubChem, DailyMed và cơ sở dữ liệu sáng chế (Google Patents / WIPO).\n"
            "   - Trích xuất: Tên IUPAC, Công thức phân tử, Khối lượng mol, CAS Registry, Phân loại BCS, Độ tan, và Chỉ định điều trị.\n"
            "2. Tải & Xử lý Hình ảnh Cấu trúc:\n"
            "   - Tự động tải hình ảnh cấu trúc phân tử 2D từ PubChem API (hoặc Cactus NCI Resolver).\n"
            "   - Lưu file ảnh chuẩn PNG vào thư mục data/ của dự án.\n"
            "3. Điền Tài liệu Báo cáo:\n"
            "   - Điền tự động vào template Word (TEMPLATE_TONG_QUAN.docx) và chèn ảnh cấu trúc vào đúng mục 'Cấu trúc hoạt chất sử dụng'.\n"
            "   - Đồng thời xuất ra file báo cáo HTML độc lập có đầy đủ danh mục tài liệu tham khảo và trích dẫn URL.\n"
            "4. Kiểm tra:\n"
            "   - Đảm bảo file Word và HTML mở ra hiển thị đúng bảng dữ liệu và hình ảnh cấu trúc rõ nét."
        ),
    },
    "custom_icon": {
        "title": "🎨 [Thiết kế Icon] Tự tạo icon Windows .ico đa kích thước theo chủ đề",
        "prompt": (
            "DỰ ÁN: Bộ tạo Icon Windows (.ico) Tự động bằng Python Pillow\n"
            "TÊN PROJECT: icon-generator-suite\n"
            "CHỦ ĐỀ ICON: Thiết kế biểu tượng viên thuốc y tế màu xanh ngọc (Cyan Capsule) với viền bóng đổ 3D hiện đại\n\n"
            "YÊU CẦU CHỨC NĂNG CỐT LÕI:\n"
            "1. Thuật toán vẽ Vector/Bitmap Canvas:\n"
            "   - Vẽ hình khối sắc nét bằng PIL ImageDraw ở độ phân giải cao (256x256 pixel).\n"
            "   - Đổ màu gradient hoặc khối nổi 3D, khử răng cưa (anti-aliasing).\n"
            "2. Đóng gói chuẩn Windows Multi-Size ICO:\n"
            "   - Xuất ra file .ico chứa đầy đủ các tầng kích thước: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256 pixel.\n"
            "   - Đảm bảo Windows hiển thị sắc nét từ thanh Taskbar đến màn hình Desktop lớn.\n"
            "3. Ứng dụng thực tế:\n"
            "   - Lưu file vào assets/icons/project.ico và tự động gán icon này vào shortcut Desktop của ứng dụng."
        ),
    },
    "code_refactor_test": {
        "title": "🛠️ [Tự động sửa code] Quét lỗi cú pháp, bổ sung Unit Test 100% Pass",
        "prompt": (
            "DỰ ÁN: Kiểm tra toàn diện, Sửa lỗi & Chuẩn hóa Unit Test cho toàn bộ dự án\n"
            "MỤC TIÊU:\n"
            "1. Quét cú pháp toàn bộ các file .py trong thư mục (dùng python -m py_compile).\n"
            "2. Sửa triệt để các lỗi: ImportError, ModuleNotFoundError, AttributeError, Circular Import, Encoding Error.\n"
            "3. Chạy unittest tự động với run_tests.py, phát hiện tất cả các testcase bị Fail hoặc Error.\n"
            "4. Tự suy luận nguyên nhân (Root Cause), sửa trực tiếp mã nguồn để đạt tỷ lệ 100% PASS.\n"
            "5. Đảm bảo mọi tính năng chạy mượt trên Windows 11 với Python 3.11+."
        ),
    },
}


def build_custom_prompt(
    project_name: str,
    goal: str,
    ui_type: str = "Tkinter",
    icon_theme: str = "Tự động thiết kế icon phù hợp chủ đề",
    special_requirements: str = "",
    test_requirements: str = "Viết unit test đầy đủ và đảm bảo 100% pass",
    language: str = "vi",
) -> str:
    """Build a structured, production-ready specification prompt from user inputs."""
    safe_name = (project_name or "my-local-app").strip().lower().replace(" ", "-")
    safe_goal = (goal or "Tạo ứng dụng Windows thông minh, dễ dùng, chạy mượt mà").strip()
    safe_ui = ui_type or "Tkinter Desktop GUI"
    safe_icon = icon_theme or "Icon chuẩn Windows 32x32 pixel theo chủ đề ứng dụng"
    safe_special = special_requirements.strip() or "Giao diện trực quan, không bắt người dùng phải gõ code hay cú pháp phức tạp"
    safe_test = test_requirements.strip() or "Kiểm tra cú pháp py_compile, viết unit test tự động"

    if language == "en":
        return (
            f"PROJECT SPECIFICATION: {safe_name}\n"
            f"PRIMARY GOAL: {safe_goal}\n"
            f"UI FRAMEWORK: {safe_ui}\n"
            f"ICON & BRANDING: {safe_icon} (generate assets/icons/project.ico)\n"
            f"SPECIAL CONSTRAINTS: {safe_special}\n"
            f"TESTING & VALIDATION: {safe_test}\n\n"
            "EXECUTION WORKFLOW:\n"
            "1. Create necessary files with clean, modular Python 3.11+ code.\n"
            "2. Validate all syntax with py_compile.\n"
            "3. Run automated tests and self-heal any failures.\n"
            "4. Generate launcher.bat and create a Windows Desktop shortcut with the custom icon."
        )

    return (
        f"DỰ ÁN: {safe_name}\n"
        f"MỤC TIÊU CỐT LÕI: {safe_goal}\n"
        f"KHUNG GIAO DIỆN (UI): {safe_ui}\n"
        f"BIỂU TƯỢNG (ICON): {safe_icon} (tự tạo assets/icons/project.ico)\n"
        f"ĐẶC TẢ KỸ THUẬT & TRẢI NGHIỆM: {safe_special}\n"
        f"KIỂM THỬ & ĐẢM BẢO CHẤT LƯỢNG: {safe_test}\n\n"
        "QUY TRÌNH THỰC HIỆN TỰ ĐỘNG:\n"
        "1. Tạo mã nguồn hoàn chỉnh, cấu trúc module rõ ràng, tương thích Windows 11 & Python 3.11+.\n"
        "2. Kiểm tra cú pháp (py_compile) và tự khắc phục triệt để mọi lỗi phát sinh.\n"
        "3. Chạy kiểm thử tự động, đảm bảo không có cảnh báo hay ngoại lệ chưa xử lý.\n"
        "4. Tự động sinh launcher.bat và tạo lối tắt Desktop (.lnk) kèm icon riêng để sử dụng ngay."
    )


def build_gemini_prompt_request(short_idea: str, language: str = "vi") -> str:
    """Generate a meta-prompt to send to Gemini/ChatGPT to get back an optimal agent prompt.

    The user can copy this meta-prompt, ask Gemini/ChatGPT, and paste the response directly
    back into the local agent chat.
    """
    idea = (short_idea or "Tạo ứng dụng giải toán nhập phân số và căn thức trực quan").strip()
    if language == "en":
        return (
            "You are a Senior Software Architect and Prompt Engineer. "
            "I want to create the following application using an autonomous Local AI Coding Agent on Windows 11:\n\n"
            f"IDEA: \"{idea}\"\n\n"
            "Please write an exhaustive, crystal-clear TECHNICAL SPECIFICATION PROMPT that I can paste "
            "directly into the Local Agent. Make sure the prompt instructs the agent to:\n"
            "1. Specify the Project Name and directory structure.\n"
            "2. Define the GUI framework (e.g. Tkinter Canvas, CustomTkinter, or HTML5 Web) with zero complex coding required by the end-user.\n"
            "3. Include all necessary technical domain terms (e.g., AST parser, stacked fraction rendering, vinculum square root, 60 FPS double buffering, collision detection, etc.).\n"
            "4. Define exact UI layout, color palette, and custom 32x32 .ico icon theme.\n"
            "5. Specify unit test suites and self-healing error verification.\n"
            "6. Request a 1-click launcher.bat and Windows Desktop shortcut.\n"
            "Please output only the ready-to-paste prompt in Vietnamese or English."
        )

    return (
        "Bạn là một Kỹ sư Kiến trúc Phần mềm cao cấp (Senior Software Architect & Prompt Engineer). "
        "Tôi muốn xây dựng ứng dụng sau đây bằng AI Agent lập trình cục bộ (Local AI Agent) trên Windows 11:\n\n"
        f"Ý TƯỞNG CỦA TÔI: \"{idea}\"\n\n"
        "Hãy viết cho tôi một BẢN CÂU LỆNH ĐẶC TẢ KỸ THUẬT (Technical Specification Prompt) hoàn chỉnh, chi tiết và chuyên nghiệp nhất "
        "để tôi có thể SAO CHÉP VÀ DÁN TRỰC TIẾP vào Agent. Yêu cầu câu lệnh phải hướng dẫn Agent:\n"
        "1. Đặt tên dự án (Project Name) và phân chia cấu trúc file chuẩn.\n"
        "2. Xác định công nghệ giao diện (Tkinter Canvas, CustomTkinter hoặc Web) đảm bảo người dùng cuối thao tác tự nhiên, không phải gõ code.\n"
        "3. Đầy đủ các thuật ngữ chuyên môn cần thiết (ví dụ: bộ phân tích cú pháp AST, hiển thị phân số xếp chồng, dấu căn có thanh vinculum, đồ họa 60 FPS double-buffering, va chạm vật lý AABB...).\n"
        "4. Mô tả chi tiết giao diện, màu sắc, và biểu tượng icon .ico riêng (assets/icons/project.ico).\n"
        "5. Yêu cầu viết Unit Test đầy đủ, tự chạy kiểm tra cú pháp và tự sửa lỗi nếu gặp traceback.\n"
        "6. Tự động sinh file khởi chạy launcher.bat và tạo lối tắt Desktop .lnk 1-click.\n\n"
        "Hãy chỉ xuất ra nội dung câu lệnh đặc tả hoàn chỉnh để tôi copy dán ngay."
    )
