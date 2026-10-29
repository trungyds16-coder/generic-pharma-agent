import unittest
from prompts import (
    GLOSSARY,
    PROMPT_PRESETS,
    build_custom_prompt,
    build_gemini_prompt_request,
)


class TestPrompts(unittest.TestCase):
    def test_glossary_contains_essential_categories(self):
        self.assertIn("math_natural_input", GLOSSARY)
        self.assertIn("graphics_2d_canvas", GLOSSARY)
        self.assertIn("graphics_3d_engine", GLOSSARY)
        self.assertIn("pharma_chemistry", GLOSSARY)
        self.assertIn("windows_desktop_deployment", GLOSSARY)

        math_glossary = GLOSSARY["math_natural_input"]
        self.assertIn("phân số", math_glossary["vi"])
        self.assertIn("vinculum", math_glossary["keywords"])

    def test_presets_exist_and_non_empty(self):
        self.assertGreaterEqual(len(PROMPT_PRESETS), 5)
        for key, data in PROMPT_PRESETS.items():
            self.assertIn("title", data)
            self.assertIn("prompt", data)
            self.assertTrue(len(data["title"]) > 5)
            self.assertTrue(len(data["prompt"]) > 50)

    def test_math_preset_contains_natural_input_and_icon(self):
        math_preset = PROMPT_PRESETS["math_calculator"]["prompt"]
        self.assertIn("phân số", math_preset)
        self.assertIn("căn bậc hai", math_preset)
        self.assertIn("vinculum", math_preset)
        self.assertIn("launcher.bat", math_preset)
        self.assertIn(".ico", math_preset)

    def test_build_custom_prompt_vietnamese(self):
        prompt = build_custom_prompt(
            project_name="calc-pro",
            goal="Ứng dụng máy tính vẽ đồ thị",
            ui_type="Tkinter Canvas",
            icon_theme="Biểu tượng máy tính xanh",
            special_requirements="Nhập phân số tự nhiên không gõ code",
            test_requirements="100% unit tests pass",
            language="vi",
        )
        self.assertIn("DỰ ÁN: calc-pro", prompt)
        self.assertIn("MỤC TIÊU CỐT LÕI: Ứng dụng máy tính vẽ đồ thị", prompt)
        self.assertIn("Tkinter Canvas", prompt)
        self.assertIn("launcher.bat", prompt)
        self.assertIn("assets/icons/project.ico", prompt)

    def test_build_custom_prompt_english(self):
        prompt = build_custom_prompt(
            project_name="pharma-app",
            goal="Generic drug monograph research",
            ui_type="Web GUI",
            icon_theme="Capsule icon",
            special_requirements="PubChem 2D structure resolver",
            test_requirements="py_compile and unit tests",
            language="en",
        )
        self.assertIn("PROJECT SPECIFICATION: pharma-app", prompt)
        self.assertIn("PRIMARY GOAL: Generic drug monograph research", prompt)
        self.assertIn("EXECUTION WORKFLOW", prompt)

    def test_build_gemini_prompt_request(self):
        req_vi = build_gemini_prompt_request("Làm app máy tính nhập phân số căn thức", language="vi")
        self.assertIn("Bạn là một Kỹ sư Kiến trúc Phần mềm cao cấp", req_vi)
        self.assertIn("Làm app máy tính nhập phân số căn thức", req_vi)
        self.assertIn("launcher.bat", req_vi)

        req_en = build_gemini_prompt_request("Build a 2D space shooter game", language="en")
        self.assertIn("Senior Software Architect", req_en)
        self.assertIn("Build a 2D space shooter game", req_en)


if __name__ == "__main__":
    unittest.main()
