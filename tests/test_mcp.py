import io
from pathlib import Path
import tempfile
import unittest

from codex_kit.cli import main
from codex_kit.mcp import doctor_config


class McpDoctorTests(unittest.TestCase):
    def test_doctor_config_reports_static_mcp_safety_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            config = repo / "config.toml"
            config.write_text(
                """[mcp_servers.filesystem]
command = "python"
args = ["-m", "safe_server"]
env = { API_KEY = "SECRET_VALUE" }

[mcp_servers.broadfs]
command = "definitely-missing-codexkit-mcp"
args = ["/"]

[mcp_servers.noargs]
command = "python"
""",
                encoding="utf-8",
            )
            (repo / "AGENTS.md").write_text("Use MCP server: browser\n", encoding="utf-8")

            report = doctor_config(config, repo)

        messages = "\n".join(finding.message for finding in report.findings)
        self.assertEqual(report.server_names, ["broadfs", "filesystem", "noargs"])
        self.assertIn("missing command binary", messages)
        self.assertIn("missing args", messages)
        self.assertIn("broad filesystem access", messages)
        self.assertIn("referenced but not configured", messages)
        self.assertNotIn("SECRET_VALUE", messages)
        self.assertGreaterEqual(report.status_counts["WARN"], 4)

    def test_mcp_doctor_cli_prints_actionable_report_without_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            config = repo / "config.toml"
            config.write_text(
                """[mcp_servers.filesystem]
command = "python"
args = ["-m", "safe_server"]
env = { TOKEN = "DO_NOT_PRINT" }
""",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            code = main(["mcp", "doctor", "--config", str(config), "--repo", str(repo)], stdout=stdout, stderr=stderr)

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        output = stdout.getvalue()
        self.assertIn("MCP Doctor", output)
        self.assertIn("Configured servers: 1", output)
        self.assertIn("filesystem", output)
        self.assertNotIn("DO_NOT_PRINT", output)

    def test_mcp_doctor_cli_rejects_invalid_toml(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.toml"
            config.write_text("[mcp_servers\n", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            code = main(["mcp", "doctor", "--config", str(config)], stdout=stdout, stderr=stderr)

        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("error:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
