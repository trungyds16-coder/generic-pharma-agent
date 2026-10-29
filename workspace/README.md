# Máy tính khoa học

Ứng dụng desktop Python gồm phép tính an toàn, hàm lượng giác, đồ thị SVG và tích phân Simpson. Chỉ cần Python 3.10 trở lên; không cần cài thư viện ngoài.

## Chạy ứng dụng

Mở Terminal tại thư mục này và chạy:

```powershell
python app.py
```

Hoặc chọn `app.py` trong Local Agent rồi nhấn **Play / Chạy thử**. Giao diện calculator sẽ mở riêng để bạn tương tác.

## Dùng biểu thức

Hỗ trợ `+ - * / ^ ** %`, ngoặc, hằng số `pi`, `e`, `tau` và các hàm `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sqrt`, `log`, `log10`, `exp`, `abs`, `floor`, `ceil`. Hàm số dùng biến `x`, ví dụ `sin(x) + x^2`.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
```

## Cấu trúc

- `app.py`: giao diện Tkinter.
- `src/calculator.py`: bộ phân tích biểu thức an toàn và tích phân Simpson.
- `src/plotter.py`: tạo đồ thị SVG không cần thư viện ngoài.
- `tests/test_calculator.py`: bộ kiểm thử chức năng.
