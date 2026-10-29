import math
import unittest

from src.calculator import CalculatorError, evaluate, integrate
from src.plotter import plot_svg


class TestCalculator(unittest.TestCase):
    def test_addition(self): self.assertEqual(evaluate("2 + 3"), 5)
    def test_subtraction(self): self.assertEqual(evaluate("9 - 4"), 5)
    def test_multiplication(self): self.assertEqual(evaluate("6 * 7"), 42)
    def test_division(self): self.assertEqual(evaluate("8 / 2"), 4)
    def test_power_python_syntax(self): self.assertEqual(evaluate("2 ** 5"), 32)
    def test_power_calculator_syntax(self): self.assertEqual(evaluate("2 ^ 5"), 32)
    def test_modulo(self): self.assertEqual(evaluate("17 % 5"), 2)
    def test_parentheses(self): self.assertEqual(evaluate("(2 + 3) * 4"), 20)
    def test_unary_minus(self): self.assertEqual(evaluate("-8"), -8)
    def test_unary_plus(self): self.assertEqual(evaluate("+8"), 8)
    def test_nested_operations(self): self.assertEqual(evaluate("2 + 3 * 4"), 14)
    def test_decimal(self): self.assertAlmostEqual(evaluate("0.1 + 0.2"), 0.3)
    def test_pi_constant(self): self.assertAlmostEqual(evaluate("pi"), math.pi)
    def test_e_constant(self): self.assertAlmostEqual(evaluate("e"), math.e)
    def test_tau_constant(self): self.assertAlmostEqual(evaluate("tau"), math.tau)
    def test_sine(self): self.assertAlmostEqual(evaluate("sin(pi / 2)"), 1)
    def test_cosine(self): self.assertAlmostEqual(evaluate("cos(0)"), 1)
    def test_tangent(self): self.assertAlmostEqual(evaluate("tan(0)"), 0)
    def test_square_root(self): self.assertEqual(evaluate("sqrt(81)"), 9)
    def test_natural_log(self): self.assertAlmostEqual(evaluate("log(e)"), 1)
    def test_log10(self): self.assertAlmostEqual(evaluate("log10(1000)"), 3)
    def test_exponential(self): self.assertAlmostEqual(evaluate("exp(1)"), math.e)
    def test_absolute(self): self.assertEqual(evaluate("abs(-12)"), 12)
    def test_floor(self): self.assertEqual(evaluate("floor(2.9)"), 2)
    def test_ceil(self): self.assertEqual(evaluate("ceil(2.1)"), 3)
    def test_variable_x(self): self.assertEqual(evaluate("x ** 2", 4), 16)
    def test_empty_expression_rejected(self):
        with self.assertRaises(CalculatorError): evaluate("")
    def test_division_by_zero_rejected(self):
        with self.assertRaises(CalculatorError): evaluate("1 / 0")
    def test_unknown_name_rejected(self):
        with self.assertRaises(CalculatorError): evaluate("secret(1)")
    def test_python_execution_rejected(self):
        with self.assertRaises(CalculatorError): evaluate("__import__('os').system('whoami')")
    def test_sine_integral(self): self.assertAlmostEqual(integrate("sin(x)", 0, math.pi), 2, places=6)
    def test_polynomial_integral(self): self.assertAlmostEqual(integrate("x ** 2", 0, 3), 9, places=7)
    def test_reversed_integral(self): self.assertAlmostEqual(integrate("x", 2, 0), -2, places=7)
    def test_zero_width_integral(self): self.assertEqual(integrate("x", 2, 2), 0)
    def test_odd_intervals_are_adjusted(self): self.assertAlmostEqual(integrate("x", 0, 2, 9), 2, places=7)
    def test_too_few_intervals_rejected(self):
        with self.assertRaises(CalculatorError): integrate("x", 0, 1, 1)
    def test_plot_svg_contains_curve(self): self.assertIn("<path", plot_svg("x ** 2", -2, 2))
    def test_plot_svg_has_accessible_role(self): self.assertIn('role="img"', plot_svg("x + 1", -1, 1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
