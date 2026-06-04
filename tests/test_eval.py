from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest

from codex_kit.cli import main
from codex_kit.evals import _save_config, add_case, init_config, load_config


class EvalHarnessTests(unittest.TestCase):
    def test_eval_init_creates_versioned_config(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / ".codex-kit" / "evals.json"

            config = init_config(config_path)

            saved = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual(config["version"], 1)
        self.assertEqual(saved, {"version": 1, "cases": []})

    def test_eval_add_registers_task_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / ".codex-kit" / "evals.json"
            init_config(config_path)

            add_case(
                config_path,
                name="fix-readme",
                prompt="Fix the README typo",
                expected_command="python -m unittest",
                allowed_changes="README.md",
            )
            config = load_config(config_path)

        self.assertEqual(len(config["cases"]), 1)
        self.assertEqual(config["cases"][0]["name"], "fix-readme")
        self.assertEqual(config["cases"][0]["expected_command"], "python -m unittest")
        self.assertEqual(config["cases"][0]["allowed_changes"], "README.md")

    def test_eval_add_rejects_duplicate_names(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / ".codex-kit" / "evals.json"
            init_config(config_path)
            add_case(config_path, name="smoke", prompt="Prompt", expected_command="python -m unittest", allowed_changes="src/**")

            with self.assertRaisesRegex(ValueError, "already exists"):
                add_case(config_path, name="smoke", prompt="Prompt", expected_command="python -m unittest", allowed_changes="src/**")

    def test_eval_cli_init_add_run_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            config_path = repo / ".codex-kit" / "evals.json"
            stdout = io.StringIO()
            stderr = io.StringIO()

            init_code = main(["eval", "init", "--config", str(config_path)], stdout=stdout, stderr=stderr)
            add_code = main(
                [
                    "eval",
                    "add",
                    "smoke",
                    "--prompt",
                    "List files",
                    "--verify",
                    "python -m unittest",
                    "--allowed-changes",
                    "src/**",
                    "--config",
                    str(config_path),
                ],
                stdout=stdout,
                stderr=stderr,
            )
            run_code = main(["eval", "run", "--dry-run", "--config", str(config_path)], stdout=stdout, stderr=stderr)
            report_code = main(["eval", "report", "--config", str(config_path)], stdout=stdout, stderr=stderr)

            production_files = sorted(path.relative_to(repo).as_posix() for path in repo.rglob("*") if path.is_file())

        self.assertEqual((init_code, add_code, run_code, report_code), (0, 0, 0, 0))
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(production_files, [".codex-kit/evals.json"])
        output = stdout.getvalue()
        self.assertIn("Initialized eval config", output)
        self.assertIn("Added eval case: smoke", output)
        self.assertIn("DRY RUN", output)
        self.assertIn("python -m unittest", output)
        self.assertIn("Eval Report", output)
        self.assertIn("Task count: 1", output)

    def test_eval_run_requires_dry_run(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / ".codex-kit" / "evals.json"
            init_config(config_path)
            stdout = io.StringIO()
            stderr = io.StringIO()

            code = main(["eval", "run", "--config", str(config_path)], stdout=stdout, stderr=stderr)

        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("--dry-run is required", stderr.getvalue())

    def test_eval_run_does_not_accept_abbreviated_dry_run_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / ".codex-kit" / "evals.json"
            init_config(config_path)
            stdout = io.StringIO()
            stderr = io.StringIO()

            with redirect_stderr(io.StringIO()):
                code = main(["eval", "run", "--dry", "--config", str(config_path)], stdout=stdout, stderr=stderr)

        self.assertEqual(code, 2)

    def test_eval_config_serialization_rejects_non_finite_json(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / ".codex-kit" / "evals.json"
            config_path.parent.mkdir(parents=True)

            with self.assertRaises(ValueError):
                _save_config(
                    config_path,
                    {
                        "version": 1,
                        "cases": [
                            {
                                "name": "bad",
                                "prompt": float("nan"),
                                "expected_command": "python -m unittest",
                                "allowed_changes": "src/**",
                            }
                        ],
                    },
                )


if __name__ == "__main__":
    unittest.main()
