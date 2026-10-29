# Kế hoạch: Calculator tích phân và đồ thị

## Mục tiêu

Tạo ứng dụng máy tính desktop bằng Python, chạy trên Windows, gồm:

- Phép tính cơ bản: cộng, trừ, nhân, chia, lũy thừa.
- Hàm lượng giác: sin, cos, tan; sử dụng radian và ghi rõ trong giao diện.
- Nhập hàm số theo biến x, tính tích phân xác định và vẽ đồ thị.
- TÔ MÀU vùng giữa đồ thị và trục x trong khoảng tích phân. Phần f(x) ≥ 0 tô xanh; phần f(x) < 0 tô cam. Chỉ tô trong hai cận đã nhập.
- Nhận ký hiệu Unicode thông dụng: ½, ⅓, ¼, ¾, ⅔, √2, √x và √(biểu thức).
- Dùng Python chuẩn và Tkinter Canvas; không phụ thuộc scipy, numpy hoặc matplotlib.

## Cấu trúc file

Tạo hoặc cập nhật trong project hiện tại:

- `main.py`: điểm khởi chạy giao diện.
- `src/calculator.py`: phép tính, parser biểu thức và tích phân.
- `tests/test_calculator.py`: kiểm thử tự động.
- `docs/README.md` hoặc `README.md`: cách cài và sử dụng.
- `requirements.txt`: không khai báo gói ngoài nếu không cần.
- `run_project.bat`: chạy đúng `main.py`.

Không sửa `app.py` của Local Agent và không tạo project khác.

## Giao diện

- Ô nhập phép tính thông thường và nút tính kết quả.
- Ô nhập hàm f(x), hai ô nhập cận a và b.
- Nút **Tính tích phân** và nút **Vẽ đồ thị**.
- Khu vực đồ thị có trục x/y, lưới, nhãn cận và đường biểu diễn.
- Tô màu vùng tích phân giữa đồ thị và trục x trong [a,b]; tách vùng dương và âm khi đồ thị cắt trục x.
- Hiển thị giá trị tích phân có dấu. Báo lỗi dễ hiểu khi biểu thức hoặc cận không hợp lệ.

## Quy tắc tính toán và an toàn

- Dùng Simpson với số khoảng chẵn; nếu đầu vào là số lẻ thì điều chỉnh lên số chẵn.
- Parser phải hỗ trợ phép toán `+ - * / ^`, ngoặc, biến `x`, hằng số `pi`/`π`, `e`, các hàm `sin`, `cos`, `tan`, `sqrt`, `log`, `log10`, `exp`, `abs`.
- Chuyển `½`, `⅓`, `¼`, `¾`, `⅔` thành giá trị tương ứng; chuyển `√2`, `√x`, `√(x+1)` thành biểu thức căn hợp lệ.
- Từ chối tên hàm hoặc cú pháp không hỗ trợ; xử lý chia cho 0 và căn bậc hai của số âm bằng thông báo lỗi.
- Không dùng `eval()` hoặc `exec()` để tính biểu thức người dùng.

## Kiểm thử và tiêu chí đạt

Viết **ít nhất 10 test tự động**, bao gồm:

1. Cộng, trừ, nhân và chia.
2. Lũy thừa và ngoặc.
3. Các hàm sin, cos, tan.
4. Hằng số pi và e.
5. Tính `∫ x^2 dx` từ 0 đến 1, kết quả xấp xỉ 1/3.
6. Tính `∫ sin(x) dx` từ 0 đến pi, kết quả xấp xỉ 2.
7. Tính `½ + ⅓`, kết quả xấp xỉ 5/6.
8. Tính `√2` và biểu thức `√x`.
9. Tích phân của `x` từ -1 đến 1 có giá trị có dấu xấp xỉ 0.
10. Hàm vẽ/tạo vùng tô xác nhận có cả vùng dương màu xanh và vùng âm màu cam khi đồ thị cắt trục x.
11. Vùng tô chỉ nằm giữa hai cận đã nhập.
12. Parser từ chối cú pháp nguy hiểm hoặc tên hàm không được hỗ trợ.

Kết quả tích phân dùng sai số phù hợp, ví dụ sai lệch không quá `1e-6` với các test nêu trên.

## Quy trình bắt buộc

1. Đọc `plan.md` và các file hiện có trong project.
2. Tạo checklist riêng cho từng yêu cầu.
3. Tạo/sửa file bằng công cụ ghi file; không chỉ gửi code trong chat.
4. Xác nhận file tồn tại trước khi kiểm tra hoặc chạy file đó. Không gọi `run_python` cho file chưa được tạo.
5. Chạy kiểm tra cú pháp và test tự động; nếu lỗi, đọc lỗi thật, sửa và chạy lại tối đa 3 lần.
6. Đọc lại file và đối chiếu từng tiêu chí với code và kết quả test.
7. Cập nhật `run_project.bat` để gọi `main.py`.
8. Không mở giao diện trong lúc chat. Dừng sau khi kiểm tra đạt để tôi tự bấm **Play**.

Chỉ báo hoàn tất khi các file tồn tại, launcher trỏ đúng `main.py`, toàn bộ test pass và phần tô vùng được kiểm tra. Nếu có mục chưa đạt, ghi rõ mục đó và không tuyên bố project đã hoàn thành.
