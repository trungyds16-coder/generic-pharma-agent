"""Generate dependency-free SVG graphs for calculator expressions."""

from __future__ import annotations

import html
import math
from pathlib import Path

from .calculator import evaluate


def plot_svg(expression: str, start: float = -10, end: float = 10, width: int = 800, height: int = 480) -> str:
    if start >= end:
        raise ValueError("Giá trị bắt đầu phải nhỏ hơn giá trị kết thúc.")
    points = []
    values = []
    for index in range(801):
        x = start + (end - start) * index / 800
        try:
            y = evaluate(expression, x)
            if math.isfinite(y):
                points.append((x, y))
                values.append(y)
            else:
                points.append((x, None))
        except (ValueError, OverflowError, ZeroDivisionError):
            points.append((x, None))
    if not values:
        raise ValueError("Không có điểm hợp lệ để vẽ đồ thị.")
    ymin, ymax = min(values), max(values)
    if ymin == ymax:
        ymin, ymax = ymin - 1, ymax + 1
    pad = (ymax - ymin) * 0.08
    ymin, ymax = ymin - pad, ymax + pad
    margin = 48
    sx = lambda x: margin + (x - start) * (width - 2 * margin) / (end - start)
    sy = lambda y: height - margin - (y - ymin) * (height - 2 * margin) / (ymax - ymin)
    path_parts, pen_down = [], False
    for x, y in points:
        if y is None or y < ymin or y > ymax:
            pen_down = False
            continue
        path_parts.append(("L" if pen_down else "M") + f"{sx(x):.2f},{sy(y):.2f}")
        pen_down = True
    zero_y = sy(0) if ymin <= 0 <= ymax else None
    zero_x = sx(0) if start <= 0 <= end else None
    axes = ""
    if zero_y is not None:
        axes += f'<line x1="{margin}" y1="{zero_y:.2f}" x2="{width-margin}" y2="{zero_y:.2f}" stroke="#94a3b8"/>'
    if zero_x is not None:
        axes += f'<line x1="{zero_x:.2f}" y1="{margin}" x2="{zero_x:.2f}" y2="{height-margin}" stroke="#94a3b8"/>'
    title = html.escape(f"y = {expression}")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">'
        f'<rect width="100%" height="100%" fill="#fff"/><text x="{width/2}" y="26" text-anchor="middle" font-size="18">{title}</text>'
        f'<rect x="{margin}" y="{margin}" width="{width-2*margin}" height="{height-2*margin}" fill="none" stroke="#cbd5e1"/>'
        f'{axes}<path d="{" ".join(path_parts)}" fill="none" stroke="#2563eb" stroke-width="2.5"/>'
        f'<text x="{margin}" y="{height-12}" font-size="12">x: {start:g} đến {end:g}</text></svg>'
    )


def save_plot(expression: str, start: float = -10, end: float = 10, output: str | Path = "docs/graph.svg") -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plot_svg(expression, start, end), encoding="utf-8")
    return path.resolve()
