import io
import json
from pathlib import Path
import tempfile
import unittest

from codex_kit.cli import main
from codex_kit.scan import scan_repository


class ScanTests(unittest.TestCase):
    def test_scan_repository_reports_codex_readiness_risks(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / "AGENTS.md").write_text(
                """# Agent Instructions

Use `src/app.py` for the app.
Run `git reset --hard` if work gets messy.
MCP server: filesystem
""" + "Extra instruction line.\n" * 260,
                encoding="utf-8",
            )
            (repo / ".codex").mkdir()
            (repo / ".codex" / "config.toml").write_text(
                "[mcp_servers.filesystem]\ncommand = \"mcp-filesystem\"\n",
                encoding="utf-8",
            )
            (repo / "package.json").write_text("{}", encoding="utf-8")
            (repo / "node_modules").mkdir()

            report = scan_repository(repo)

        messages = "\n".join(finding.message for finding in report.findings)
        self.assertEqual(report.agents_files, ["AGENTS.md"])
        self.assertTrue(report.codex_config_present)
        self.assertIn("MCP references found", messages)
        self.assertIn("stale path", messages)
        self.assertIn("missing test/build command hints", messages)
        self.assertIn("unsafe destructive instruction", messages)
        self.assertIn("node_modules", messages)
        self.assertIn("overly large", messages)
        self.assertEqual(report.status_counts["FAIL"], 1)
        self.assertGreaterEqual(report.status_counts["WARN"], 4)

    def test_scan_cli_prints_pass_warn_fail_sections(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / "AGENTS.md").write_text(
                """# Agent Instructions

Run tests with `python -m unittest`.
Build check: `python -m compileall src tests`.
""",
                encoding="utf-8",
            )
            (repo / "src").mkdir()
            stdout = io.StringIO()
            stderr = io.StringIO()

            code = main(["scan", str(repo)], stdout=stdout, stderr=stderr)

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        output = stdout.getvalue()
        self.assertIn("Codex Kit Scan", output)
        self.assertIn("PASS", output)
        self.assertIn("WARN", output)
        self.assertIn("FAIL", output)
        self.assertIn("AGENTS.md files: 1", output)

    def test_scan_cli_rejects_missing_repository(self):
        stdout = io.StringIO()
        stderr = io.StringIO()

        code = main(["scan", "/no/such/repo"], stdout=stdout, stderr=stderr)

        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("error:", stderr.getvalue())

    def test_scan_cli_can_emit_machine_readable_json(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / "AGENTS.md").write_text(
                "Run tests with `python -m unittest`.\nMCP server: filesystem\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            code = main(["scan", "--json", str(repo)], stdout=stdout, stderr=stderr)

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["agents_files"], ["AGENTS.md"])
        self.assertIn("status_counts", payload)
        self.assertIn("findings", payload)
        self.assertNotIn("# Codex Kit Scan", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
