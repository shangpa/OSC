import io
import json
from pathlib import Path
import tempfile
import unittest

from maintainer_report.cli import main


SAMPLE_EXPORT = {
    "issues": [
        {
            "number": 10,
            "title": "Needs release note",
            "state": "open",
            "labels": [],
            "updated_at": "2026-05-01T00:00:00Z",
            "html_url": "https://example.test/issues/10",
        }
    ],
    "pull_requests": [
        {
            "number": 11,
            "title": "Fix parser edge case",
            "state": "open",
            "labels": ["bug"],
            "updated_at": "2026-06-01T00:00:00Z",
            "html_url": "https://example.test/pull/11",
        }
    ],
}


class CliTests(unittest.TestCase):
    def test_main_prints_markdown_report_to_stdout(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = _write_export(Path(directory) / "export.json")
            stdout = io.StringIO()
            stderr = io.StringIO()

            code = main(
                [str(input_path), "--as-of", "2026-06-04", "--stale-days", "30"],
                stdout=stdout,
                stderr=stderr,
            )

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("# Maintainer Report", stdout.getvalue())
        self.assertIn("- Open issues: 1", stdout.getvalue())
        self.assertIn("- Unlabeled open items: 1", stdout.getvalue())

    def test_main_writes_markdown_report_to_output_file(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = _write_export(Path(directory) / "export.json")
            output_path = Path(directory) / "report.md"
            stdout = io.StringIO()
            stderr = io.StringIO()

            code = main(
                [
                    str(input_path),
                    "--as-of",
                    "2026-06-04",
                    "--output",
                    str(output_path),
                ],
                stdout=stdout,
                stderr=stderr,
            )

            output = output_path.read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("# Maintainer Report", output)

    def test_stale_days_option_changes_stale_classification(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = _write_export(Path(directory) / "export.json")
            stdout = io.StringIO()
            stderr = io.StringIO()

            code = main(
                [str(input_path), "--as-of", "2026-06-04", "--stale-days", "60"],
                stdout=stdout,
                stderr=stderr,
            )

        self.assertEqual(code, 0)
        self.assertIn("- Stale open items: 0", stdout.getvalue())

    def test_invalid_input_path_returns_readable_error(self):
        stdout = io.StringIO()
        stderr = io.StringIO()

        code = main(["/no/such/export.json"], stdout=stdout, stderr=stderr)

        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("error:", stderr.getvalue())
        self.assertIn("/no/such/export.json", stderr.getvalue())


def _write_export(path: Path) -> Path:
    path.write_text(json.dumps(SAMPLE_EXPORT), encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
