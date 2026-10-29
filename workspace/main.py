import tkinter as tk
from tkinter import messagebox
from src.calculator import calculate_integral, plot_function

def on_calculate_integral():
    try:
        a = float(entry_a.get())
        b = float(entry_b.get())
        result = calculate_integral(entry_function.get(), a, b)
        messagebox.showinfo("Kết quả", f"Tích phân từ {a} đến {b} là {result}")
    except Exception as e:
        messagebox.showerror("Lỗi", str(e))

def on_plot_function():
    try:
        a = float(entry_a.get())
        b = float(entry_b.get())
        plot_function(entry_function.get(), a, b)
    except Exception as e:
        messagebox.showerror("Lỗi", str(e))

root = tk.Tk()
root.title("Calculator")

tk.Label(root, text="Hàm f(x):").grid(row=0, column=0, padx=10, pady=10)
entry_function = tk.Entry(root, width=50)
entry_function.grid(row=0, column=1, padx=10, pady=10)

tk.Label(root, text="a:").grid(row=1, column=0, padx=10, pady=10)
entry_a = tk.Entry(root, width=20)
entry_a.grid(row=1, column=1, padx=10, pady=10)

tk.Label(root, text="b:").grid(row=2, column=0, padx=10, pady=10)
entry_b = tk.Entry(root, width=20)
entry_b.grid(row=2, column=1, padx=10, pady=10)

tk.Button(root, text="Tính tích phân", command=on_calculate_integral).grid(row=3, column=0, columnspan=2, pady=10)
tk.Button(root, text="Vẽ đồ thị", command=on_plot_function).grid(row=4, column=0, columnspan=2, pady=10)

root.mainloop()
