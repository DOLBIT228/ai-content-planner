from pathlib import Path
import unittest


class FrontendReactTest(unittest.TestCase):
    def test_react_ui_contains_full_workflow_controls(self):
        app = Path("frontend/src/App.jsx").read_text()
        package = Path("frontend/package.json").read_text()
        vite = Path("frontend/vite.config.js").read_text()

        self.assertIn("AI Content Planner", app)
        self.assertIn("Створити кампанію", app)
        self.assertIn("База знань", app)
        self.assertIn("openai/gpt-4.1-mini", app)
        self.assertIn("/knowledge-documents", app)
        self.assertIn("validationMessage", app)
        self.assertIn("response.text()", app)
        self.assertIn('"react"', package)
        self.assertIn("proxy", vite)
        self.assertIn("/knowledge-documents", vite)


if __name__ == "__main__":
    unittest.main()
