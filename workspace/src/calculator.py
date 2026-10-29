"""Safe expression evaluation and numerical integration for the calculator app."""

from __future__ import annotations

import ast
import math
import operator

_BIN_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_FUNCTIONS = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "asin": math.asin, "acos": math.acos, "atan": math.atan, "sqrt": math.sqrt, "log": math.log, "log10": math.log10, "exp": math.exp, "abs": abs, "floor": math.floor, "ceil": math.ceil}
_CONSTANTS = {"pi": math.pi, "e": math.e, "tau": math.tau}


class CalculatorError(ValueError):
    """Raised when an expression is invalid or unsafe."""


def evaluate(expression: str, x: float | None = None) -> float:
    """Evaluate arithmetic and common math functions without executing code."""
    if not isinstance(expression, str) or not expression.strip():
        raise CalculatorError("Hãy nhập biểu thức cần tính.")
    try:
        tree = ast.parse(expression.replace("^", "**"), mode="eval")
        result = float(_evaluate_node(tree.body, x))
        if not math.isfinite(result):
            raise CalculatorError("Kết quả không phải số hữu hạn.")
        return result
    except CalculatorError:
        raise
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
        raise CalculatorError(f"Biểu thức không hợp lệ: {exc}") from exc


def _evaluate_node(node: ast.AST, x: float | None) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id == "x" and x is not None:
            return float(x)
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise CalculatorError(f"Tên không được hỗ trợ: {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left, right = _evaluate_node(node.left, x), _evaluate_node(node.right, x)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise CalculatorError("Số mũ quá lớn.")
        return _BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_evaluate_node(node.operand, x))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS:
        if node.keywords or not 1 <= len(node.args) <= 2:
            raise CalculatorError("Hàm chỉ nhận một hoặc hai đối số.")
        return _FUNCTIONS[node.func.id](*[_evaluate_node(arg, x) for arg in node.args])
    raise CalculatorError("Biểu thức chứa cú pháp không được hỗ trợ.")


def integrate(expression: str, start: float, end: float, intervals: int = 1000) -> float:
    """Integrate a function using composite Simpson's rule."""
    start, end, intervals = float(start), float(end), int(intervals)
    if intervals < 2:
        raise CalculatorError("Số khoảng phải từ 2 trở lên.")
    if intervals % 2:
        intervals += 1
    if start == end:
        return 0.0
    step = (end - start) / intervals
    total = evaluate(expression, start) + evaluate(expression, end)
    for index in range(1, intervals):
        total += (4 if index % 2 else 2) * evaluate(expression, start + index * step)
    return total * step / 3
