from pathlib import Path
import unittest


class FrontendReactTest(unittest.TestCase):
    def test_react_ui_contains_full_workflow_controls(self):
        app = Path("frontend/src/App.jsx").read_text()
        package = Path("frontend/package.json").read_text()
        vite = Path("frontend/vite.config.js").read_text()

        self.assertIn("Campaign → Plan → Generate → Review", app)
        self.assertIn("Create campaign", app)
        self.assertIn("Generate plan", app)
        self.assertIn("Regenerate", app)
        self.assertIn("/content-entries/${entryId}/approve", app)
        self.assertIn('"react"', package)
        self.assertIn("proxy", vite)


if __name__ == "__main__":
    unittest.main()
