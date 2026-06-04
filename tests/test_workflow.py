from pathlib import Path
import unittest


class WorkflowTests(unittest.TestCase):
    def test_github_actions_runs_cli_smoke_checks(self):
        workflow = Path(".github/workflows/test.yml").read_text(encoding="utf-8")

        self.assertIn("codex-kit --help", workflow)
        self.assertIn("codex-kit scan --json .", workflow)
        self.assertIn("codex-kit agents graph . --for README.md", workflow)
        self.assertIn("codex-kit mcp doctor --repo .", workflow)


if __name__ == "__main__":
    unittest.main()
