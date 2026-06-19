from pathlib import Path
import unittest


class FrontendStaticTest(unittest.TestCase):
    def test_basic_ui_contains_full_workflow_controls(self):
        html = Path("app/static/index.html").read_text()
        self.assertIn("Campaign → Plan → Generate → Review", html)
        self.assertIn("Create campaign", html)
        self.assertIn("Generate plan", html)
        self.assertIn("Regenerate", html)
        self.assertIn("/content-entries/${id}/approve", html)


if __name__ == "__main__":
    unittest.main()
