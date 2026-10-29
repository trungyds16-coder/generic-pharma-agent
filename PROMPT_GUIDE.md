# Sổ tay Hướng dẫn Prompt & Mẫu Đặc tả Kỹ thuật (Prompt Engineering Guide)

> **Dành cho Local AI Agent trên Windows 11 (Tối ưu cho CPU & 16GB RAM)**  
> *Hỗ trợ song ngữ Tiếng Việt & English*

---

## 📋 1. Cấu trúc Prompt Chuẩn — Bạn Cần Điền Gì?

Để Agent hiểu chính xác và lập trình tự động từ A đến Z mà bạn không cần phải giải thích lại nhiều lần, hãy dùng cấu trúc **6 Khối Chuẩn** sau:

```text
[DỰ ÁN]: <Tên thư mục dự án viết liền hoặc có dấu gạch ngang, ví dụ: natural-math-calc>
[MỤC TIÊU]: <Ứng dụng làm gì, giải quyết bài toán gì cho người dùng>
[GIAO DIỆN & TRẢI NGHIỆM]: 
  - Khung giao diện: Tkinter Canvas (máy tính để bàn) hoặc Web HTML5 (trình duyệt)
  - Trải nghiệm: Nhập liệu trực quan, không bắt người dùng phải gõ code hay cú pháp phức tạp
[BIỂU TƯỢNG (ICON)]: 
  - Tự động sinh file assets/icons/project.ico chuẩn Windows (ví dụ: máy tính xanh navy, phi thuyền neon, viên thuốc cyan)
[THUẬT NGỮ KỸ THUẬT]: <Xem bảng thuật ngữ mục 2 bên dưới để điền>
[KIỂM THỬ & BÀN GIAO]:
  - Kiểm tra cú pháp py_compile, viết bộ unit test tự động (100% pass)
  - Tự tạo file launcher.bat và shortcut ngoài Desktop (.lnk) kèm icon
```

---

## 📚 2. Bảng Tra Cứu Thuật Ngữ Chuyên Ngành (Glossary)

Nếu bạn không biết diễn đạt cho máy hiểu các tính năng phức tạp, chỉ cần sao chép các từ khóa sau vào câu lệnh:

### A. Toán học & Nhập liệu Trực quan (Math & WYSIWYG)
| Tính năng mong muốn | Thuật ngữ tiếng Anh cần đưa vào Prompt | Ý nghĩa chuyên ngành |
| :--- | :--- | :--- |
| **Nhập phân số xếp chồng tự nhiên** | `Stacked fraction with horizontal fraction bar`, `WYSIWYG 2D math layout` | Tử số nằm trên, mẫu số nằm dưới với vạch kẻ ngang; không bắt gõ dấu `/` |
| **Căn thức có thanh ngang trùm lên** | `Square root with vinculum over expression`, `Radical symbol` | Dấu căn $\sqrt{...}$ có thanh ngang bên trên tự động kéo dài bao trọn biểu thức |
| **Phân tích biểu thức toán học** | `Abstract Syntax Tree (AST)`, `Recursive descent expression parser` | Máy tự hiểu thứ tự ưu tiên nhân chia trước, cộng trừ sau, trong ngoặc trước |
| **Vẽ đồ thị & Tô màu tích phân** | `Canvas coordinate mapping`, `Definite integral area fill (under curve)` | Vẽ hàm $f(x)$ và tô màu vùng diện tích giới hạn giữa đồ thị và trục $Ox$ |
| **Tích phân số học** | `Numerical integration (Simpson's 1/3 rule, Trapezoidal rule)` | Thuật toán tính xấp xỉ diện tích tích phân chính xác cao |

### B. Đồ họa 2D & Game Development
| Tính năng mong muốn | Thuật ngữ tiếng Anh cần đưa vào Prompt | Ý nghĩa chuyên ngành |
| :--- | :--- | :--- |
| **Không nhấp nháy màn hình** | `Double buffering`, `Off-screen canvas buffer` | Vẽ sẵn khung hình trong bộ nhớ đệm rồi mới đẩy lên màn hình để chuyển động mượt mà |
| **Chuyển động mượt 60 khung hình/giây** | `60 FPS Game Loop`, `Delta time (dt) update tick` | Tốc độ khung hình ổn định, không bị giật lag trên máy cấu hình yếu |
| **Phát hiện va chạm vật thể** | `AABB (Axis-Aligned Bounding Box) collision detection` | Kiểm tra hộp va chạm giữa đạn, nhân vật và chướng ngại vật |
| **Hiệu ứng tia lửa, nổ** | `Particle explosion system`, `Sprite rendering` | Sinh các hạt pixel bung ra và mờ dần khi vật thể bị phá hủy |
| **Âm thanh phản hồi nhẹ** | `Windows native winsound.Beep`, `Low-latency sound effects` | Phát âm thanh phản xạ mà không cần cài thêm thư viện âm thanh nặng |

### C. Đồ họa 3D Tối ưu cho Máy CPU (CPU-Friendly 3D)
| Tính năng mong muốn | Thuật ngữ tiếng Anh cần đưa vào Prompt | Ý nghĩa chuyên ngành |
| :--- | :--- | :--- |
| **Chạy 3D nhẹ không cần card rời** | `Three.js WebGL canvas (HTML5)` hoặc `Ursina Engine / Panda3D` | Đồ họa 3D tối ưu cho CPU và đồ họa tích hợp (Intel Iris / AMD Radeon) |
| **Góc nhìn thứ nhất** | `First-Person Shooter (FPS) camera controller`, `Mouse look (pointer lock)` | Dùng chuột xoay góc nhìn 360 độ và phím W-A-S-D di chuyển |
| **Ánh sáng & Không gian** | `Directional light`, `Ambient occlusion`, `Skybox` | Tạo bóng đổ nhẹ và phông nền bầu trời xung quanh |

### D. Dược phẩm & Hóa học (Generic Pharma Informatics)
| Tính năng mong muốn | Thuật ngữ tiếng Anh cần đưa vào Prompt | Ý nghĩa chuyên ngành |
| :--- | :--- | :--- |
| **Tra cứu hoạt chất** | `PubChem CID`, `CAS Registry Number`, `IUPAC Nomenclature` | Mã định danh quốc tế chuẩn của hóa chất và dược chất |
| **Tải ảnh cấu trúc 2D** | `PubChem 2D Structure API`, `Cactus NCI Chemical Resolver` | Tải sơ đồ cấu tạo phân tử 2D dạng file ảnh PNG rõ nét |
| **Tính chất lý hóa & Bào chế** | `BCS (Biopharmaceutics Classification)`, `Solubility profile`, `pKa`, `LogP` | Phân loại độ tan, tính thấm sinh học phục vụ thiết kế công thức thuốc generic |
| **Tự động điền báo cáo Word** | `python-docx paragraph & table replacement`, `add_picture to section` | Tự động điền các mục kỹ thuật và chèn ảnh cấu trúc vào đúng tiêu đề Word |

---

## 🤖 3. Mẹo Dùng Gemini / ChatGPT Tạo Prompt Siêu Chuẩn

Nếu bạn có một ý tưởng nhưng không biết cách mô tả kỹ thuật, hãy sao chép mẫu câu hỏi sau để hỏi **Gemini** hoặc **Copilot**, sau đó lấy kết quả dán vào Agent:

### Mẫu câu lệnh gửi Gemini (Copy & Paste):
```text
Bạn là một Kỹ sư Kiến trúc Phần mềm cao cấp (Senior Software Architect & Prompt Engineer).
Tôi muốn xây dựng ứng dụng sau đây bằng AI Agent lập trình cục bộ (Local AI Agent) trên Windows 11 (máy CPU, 16GB RAM):

Ý TƯỞNG CỦA TÔI: "[GHI Ý TƯỞNG NGẮN GỌN CỦA BẠN VÀO ĐÂY, VÍ DỤ: Làm app máy tính để bàn có thể nhập phân số và căn thức trực quan không cần gõ code, vẽ đồ thị hàm số và tô màu tích phân]"

Hãy viết cho tôi một BẢN CÂU LỆNH ĐẶC TẢ KỸ THUẬT (Technical Specification Prompt) hoàn chỉnh, chi tiết nhất để tôi SAO CHÉP VÀ DÁN TRỰC TIẾP vào Local Agent. Yêu cầu câu lệnh phải hướng dẫn Agent:
1. Đặt tên dự án (Project Name) và phân chia cấu trúc file chuẩn.
2. Công nghệ giao diện (Tkinter Canvas hoặc Web HTML5) đảm bảo người dùng cuối thao tác tự nhiên, không phải gõ code.
3. Đầy đủ các thuật ngữ chuyên môn cần thiết (AST parser, stacked fraction, vinculum radical, 60 FPS double buffering, collision detection...).
4. Mô tả chi tiết giao diện, màu sắc, và tự tạo file icon .ico riêng (assets/icons/project.ico).
5. Yêu cầu viết Unit Test đầy đủ, tự chạy py_compile và tự sửa lỗi nếu gặp traceback.
6. Tự động sinh file launcher.bat và tạo lối tắt Desktop .lnk 1-click.

Hãy chỉ xuất ra nội dung câu lệnh hoàn chỉnh để tôi dán ngay vào Agent.
```

---

## 💡 4. Thư viện Prompt Mẫu Sẵn Có (Có Thể Dùng Ngay)

### Mẫu 1: Ứng dụng Toán học nhập Phân số & Căn thức tự nhiên (WYSIWYG Math)
```text
DỰ ÁN: Máy tính Desktop thông minh với bộ nhập liệu Toán học tự nhiên (Natural Math Input)
TÊN PROJECT: natural-math-calc
GIAO DIỆN & ICON: Tkinter GUI hiện đại, icon hình máy tính khoa học tông xanh navy (32x32 .ico)

YÊU CẦU CHỨC NĂNG CỐT LÕI:
1. Nhập liệu trực quan tự nhiên (Natural WYSIWYG Math):
   - Cho phép người dùng nhập phân số trực quan (tử số nằm trên mẫu số với vạch ngang phân cách rõ ràng).
   - Cho phép chèn dấu căn bậc hai (√) với thanh ngang (vinculum) tự động kéo dài bao trùm toàn bộ biểu thức bên trong.
   - Hỗ trợ số mũ, lũy thừa, các hằng số π, e, và hàm lượng giác sin, cos, tan (hiển thị rõ chế độ Radian / Degree).
   - Người dùng KHÔNG CẦN phải gõ code hay cú pháp phức tạp; có bàn phím ảo toán học trên màn hình và phím tắt tiện lợi.
2. Vẽ đồ thị hàm số & Tính tích phân xác định:
   - Nhập hàm số f(x), chọn khoảng [a, b] để vẽ đồ thị tự động trên Canvas.
   - Tính diện tích tích phân và TÔ MÀU trực quan vùng giới hạn giữa đồ thị và trục hoành (f(x) ≥ 0 tô xanh lục, f(x) < 0 tô cam nhạt).
3. Ràng buộc kỹ thuật:
   - Viết hoàn toàn bằng Python chuẩn và Tkinter Canvas; không phụ thuộc các thư viện nặng ngoài (zero-bloat).
4. Kiểm thử & Bàn giao:
   - Viết bộ Unit Test kiểm tra tính toán phân số, căn thức và parser biểu thức.
   - Tự động tạo launcher.bat và shortcut ngoài Desktop kèm icon máy tính.
```

### Mẫu 2: Mini Game 2D Arcade Canvas 60 FPS
```text
DỰ ÁN: Mini Game 2D Arcade trên Windows (Chạy mượt trên CPU)
TÊN PROJECT: retro-space-defender
GIAO DIỆN & ICON: Đồ họa Canvas 2D phong cách Retro Arcade, icon hình tàu vũ trụ màu neon (assets/icons/project.ico)

YÊU CẦU CHỨC NĂNG CỐT LÕI:
1. Game Loop & Điều khiển:
   - Vòng lặp cập nhật 60 FPS mượt mà sử dụng Canvas Tkinter.
   - Điều khiển phi thuyền bằng phím mũi tên hoặc A/D để di chuyển, Spacebar để bắn đạn laze.
2. Đồ họa & Cơ chế Vật lý:
   - Phát hiện va chạm (AABB Collision Detection) giữa đạn, phi thuyền và các thiên thạch rơi tự do.
   - Hệ thống tính điểm (Score), mạng sống (Lives: 3), và các đợt quái tăng dần độ khó.
   - Hiệu ứng nổ hạt đơn giản (Particle Explosion) khi thiên thạch bị bắn trúng.
3. Âm thanh & Trạng thái:
   - Âm thanh beep phản hồi qua winsound tích hợp sẵn của Windows.
   - Các màn hình: Menu chính, Đang chơi, Tạm dừng, và Game Over kèm nút Chơi lại.
4. Đóng gói:
   - Sinh file launcher.bat và tạo shortcut Desktop 1-click để mở chơi ngay.
```

### Mẫu 3: Nghiên cứu Dược học & Hồ sơ Thuốc Generic
```text
DỰ ÁN: Báo cáo Tổng quan Kỹ thuật & Hồ sơ Hoạt chất Dược phẩm Generic
TÊN PROJECT: pharma-atorvastatin-dossier
HOẠT CHẤT MỤC TIÊU: Atorvastatin (hoặc thay thế bằng hoạt chất bạn muốn)

YÊU CẦU CHỨC NĂNG CỐT LÕI:
1. Tra cứu Dữ liệu Khoa học & Bằng sáng chế:
   - Tìm kiếm thông tin hoạt chất trên PubChem, DailyMed và cơ sở dữ liệu sáng chế (Google Patents / WIPO).
   - Trích xuất: Tên IUPAC, Công thức phân tử, Khối lượng mol, CAS Registry, Phân loại BCS, Độ tan, và Chỉ định điều trị.
2. Tải & Xử lý Hình ảnh Cấu trúc:
   - Tự động tải hình ảnh cấu trúc phân tử 2D từ PubChem API (hoặc Cactus NCI Resolver).
   - Lưu file ảnh chuẩn PNG vào thư mục data/ của dự án.
3. Điền Tài liệu Báo cáo:
   - Điền tự động vào template Word (TEMPLATE_TONG_QUAN.docx) và chèn ảnh cấu trúc vào đúng mục 'Cấu trúc hoạt chất sử dụng'.
   - Đồng thời xuất ra file báo cáo HTML độc lập có đầy đủ danh mục tài liệu tham khảo và trích dẫn URL.
4. Kiểm tra:
   - Đảm bảo file Word và HTML mở ra hiển thị đúng bảng dữ liệu và hình ảnh cấu trúc rõ nét.
```
