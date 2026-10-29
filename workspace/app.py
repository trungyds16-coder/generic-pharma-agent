"""Simple desktop scientific calculator with graph and integration tools."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from src.calculator import CalculatorError, evaluate, integrate
from src.plotter import plot_svg, save_plot


class CalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculator · Máy tính khoa học")
        self.geometry("900x700")
        self.minsize(720, 560)
        self.configure(bg="#f4f7fb")
        self._build_ui()

    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f7fb")
        style.configure("TLabel", background="#f4f7fb", font=("Segoe UI", 11))
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), foreground="#172554")
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="Máy tính khoa học", style="Title.TLabel").pack(anchor="w")
        ttk.Label(container, text="Phép tính · lượng giác · tích phân · đồ thị hàm số").pack(anchor="w", pady=(2, 16))

        row = ttk.Frame(container); row.pack(fill="x")
        self.expression = tk.StringVar(value="sin(x) + x^2")
        ttk.Label(row, text="Biểu thức").pack(side="left")
        entry = ttk.Entry(row, textvariable=self.expression, font=("Consolas", 14))
        entry.pack(side="left", fill="x", expand=True, padx=10); entry.bind("<Return>", lambda _e: self.calculate())
        ttk.Button(row, text="Tính", command=self.calculate).pack(side="right")

        self.result = tk.StringVar(value="Nhập biểu thức rồi nhấn Tính. Dùng x cho đồ thị/tích phân.")
        ttk.Label(container, textvariable=self.result, font=("Segoe UI", 13, "bold"), foreground="#0f766e", wraplength=820).pack(anchor="w", pady=14)

        bounds = ttk.Frame(container); bounds.pack(fill="x", pady=(2, 10))
        self.start = tk.StringVar(value="-10"); self.end = tk.StringVar(value="10")
        ttk.Label(bounds, text="Từ x").pack(side="left"); ttk.Entry(bounds, textvariable=self.start, width=10).pack(side="left", padx=(6, 18))
        ttk.Label(bounds, text="Đến x").pack(side="left"); ttk.Entry(bounds, textvariable=self.end, width=10).pack(side="left", padx=6)
        ttk.Button(bounds, text="Tính tích phân", command=self.calculate_integral).pack(side="left", padx=8)
        ttk.Button(bounds, text="Vẽ đồ thị", command=self.draw_graph).pack(side="left", padx=8)
        ttk.Button(bounds, text="Lưu SVG", command=self.export_svg).pack(side="left", padx=8)

        self.canvas = tk.Canvas(container, height=380, bg="white", highlightthickness=1, highlightbackground="#cbd5e1")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self.draw_graph(silent=True))
        self.draw_graph(silent=True)

    def _bounds(self):
        return float(self.start.get()), float(self.end.get())

    def calculate(self):
        try: self.result.set(f"Kết quả: {evaluate(self.expression.get()):,.10g}")
        except (CalculatorError, ValueError) as exc: self._error(exc)

    def calculate_integral(self):
        try:
            a, b = self._bounds(); value = integrate(self.expression.get(), a, b)
            self.result.set(f"Tích phân từ {a:g} đến {b:g}: {value:,.10g}")
        except (CalculatorError, ValueError) as exc: self._error(exc)

    def draw_graph(self, silent=False):
        try:
            a, b = self._bounds(); svg = plot_svg(self.expression.get(), a, b)
            self._draw_svg_path(svg)
        except (CalculatorError, ValueError) as exc:
            if not silent: self._error(exc)

    def _draw_svg_path(self, svg):
        import re
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 100); height = max(self.canvas.winfo_height(), 100)
        view = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
        vw, vh = map(int, view.groups()) if view else (800, 480)
        sx, sy = width / vw, height / vh
        for x1, y1, x2, y2, color in re.findall(r'<line x1="([\d.-]+)" y1="([\d.-]+)" x2="([\d.-]+)" y2="([\d.-]+)" stroke="([^"]+)"', svg):
            self.canvas.create_line(float(x1)*sx, float(y1)*sy, float(x2)*sx, float(y2)*sy, fill=color)
        match = re.search(r'<path d="([^"]+)"', svg)
        if match:
            coords = []
            for pair in re.findall(r'[ML]([\d.-]+),([\d.-]+)', match.group(1)):
                coords.extend((float(pair[0])*sx, float(pair[1])*sy))
            if len(coords) >= 4: self.canvas.create_line(*coords, fill="#2563eb", width=2, smooth=False)
        self.canvas.create_text(12, 12, anchor="nw", text=f"y = {self.expression.get()}", fill="#172554", font=("Segoe UI", 11, "bold"))

    def export_svg(self):
        try:
            a, b = self._bounds(); path = save_plot(self.expression.get(), a, b)
            self.result.set(f"Đã lưu đồ thị: {path}")
        except (CalculatorError, ValueError, OSError) as exc: self._error(exc)

    def _error(self, exc):
        self.result.set(f"Lỗi: {exc}")


if __name__ == "__main__":
    CalculatorApp().mainloop()
