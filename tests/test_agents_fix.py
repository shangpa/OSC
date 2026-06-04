import io
from pathlib import Path
import tempfile
import unittest

from codex_kit.cli import main


class AgentsAndFixTests(unittest.TestCase):
    def test_agents_graph_shows_instruction_scope_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / "AGENTS.md").write_text("Root instructions\nRun tests with `python -m unittest`.\n", encoding="utf-8")
            nested = repo / "packages" / "api"
            nested.mkdir(parents=True)
            (nested / "AGENTS.md").write_text("API instructions\nBuild with `python -m compileall src tests`.\n", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            code = main(["agents", "graph", str(repo)], stdout=stdout, stderr=stderr)

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        output = stdout.getvalue()
        self.assertIn("AGENTS Graph", output)
        self.assertIn("AGENTS.md -> applies to .", output)
        self.assertIn("packages/api/AGENTS.md -> applies to packages/api", output)
        self.assertIn("Effective chain", output)

    def test_agents_lint_reuses_agents_readiness_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / "AGENTS.md").write_text(
                "Use `missing/path.py`.\nRun `git reset --hard` if needed.\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            code = main(["agents", "lint", str(repo)], stdout=stdout, stderr=stderr)

        self.assertEqual(code, 1)
        self.assertEqual(stderr.getvalue(), "")
        output = stdout.getvalue()
        self.assertIn("AGENTS Lint", output)
        self.assertIn("FAIL", output)
        self.assertIn("unsafe destructive instruction", output)
        self.assertIn("stale path", output)

    def test_fix_dry_run_prints_safe_suggestions_without_mutating_files(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            agents = repo / "AGENTS.md"
            original = "Use `missing/path.py`.\nRun `git reset --hard`.\n"
            agents.write_text(original, encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            code = main(["fix", str(repo), "--dry-run"], stdout=stdout, stderr=stderr)
            after = agents.read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(after, original)
        output = stdout.getvalue()
        self.assertIn("Codex Kit Fix Dry Run", output)
        self.assertIn("Would review stale path", output)
        self.assertIn("Would remove or rewrite unsafe instruction", output)

    def test_fix_requires_dry_run(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            stdout = io.StringIO()
            stderr = io.StringIO()

            code = main(["fix", str(repo)], stdout=stdout, stderr=stderr)

        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("--dry-run is required", stderr.getvalue())

    def test_agents_graph_for_target_shows_target_effective_chain_only(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / "AGENTS.md").write_text("Root instructions\nRun tests with `python -m unittest`.\n", encoding="utf-8")
            nested = repo / "packages" / "api"
            nested.mkdir(parents=True)
            (nested / "AGENTS.md").write_text("API instructions\nBuild with `python -m compileall src tests`.\n", encoding="utf-8")
            target = nested / "src" / "app.py"
            target.parent.mkdir()
            target.write_text("print('ok')\n", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            code = main(["agents", "graph", str(repo), "--for", "packages/api/src/app.py"], stdout=stdout, stderr=stderr)

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        output = stdout.getvalue()
        self.assertIn("Target: packages/api/src/app.py", output)
        self.assertIn("Effective chain for target", output)
        self.assertIn("AGENTS.md > packages/api/AGENTS.md", output)
        self.assertNotIn("- .: AGENTS.md", output)


if __name__ == "__main__":
    unittest.main()
