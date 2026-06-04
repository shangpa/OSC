from datetime import date
import unittest

from maintainer_report.analyzer import analyze_items, normalize_items, render_markdown


SAMPLE_EXPORT = {
    "issues": [
        {
            "number": 1,
            "title": "Crash on startup",
            "state": "open",
            "labels": [{"name": "bug"}],
            "updated_at": "2026-05-01T09:30:00Z",
            "html_url": "https://example.test/issues/1",
        },
        {
            "number": 2,
            "title": "Document release process",
            "state": "closed",
            "labels": ["docs"],
            "updated_at": "2026-06-01T12:00:00Z",
            "html_url": "https://example.test/issues/2",
        },
        {
            "number": 3,
            "title": "Needs triage",
            "state": "open",
            "labels": [],
            "updated_at": "2026-06-03",
            "html_url": "https://example.test/issues/3",
        },
    ],
    "pull_requests": [
        {
            "number": 4,
            "title": "Add JSON fixture support",
            "state": "open",
            "labels": [{"name": "enhancement"}],
            "updated_at": "2026-04-20T08:00:00Z",
            "html_url": "https://example.test/pull/4",
        }
    ],
}


class AnalyzerTests(unittest.TestCase):
    def test_normalize_items_accepts_issue_and_pull_request_buckets(self):
        items = normalize_items(SAMPLE_EXPORT)

        self.assertEqual([item.kind for item in items], ["issue", "issue", "issue", "pull_request"])
        self.assertEqual(items[0].labels, ("bug",))
        self.assertEqual(items[1].labels, ("docs",))
        self.assertEqual(items[3].labels, ("enhancement",))

    def test_analyze_items_counts_maintainer_attention_work(self):
        report = analyze_items(
            normalize_items(SAMPLE_EXPORT),
            as_of=date(2026, 6, 4),
            stale_days=30,
        )

        self.assertEqual(report.total_items, 4)
        self.assertEqual(report.open_issues, 2)
        self.assertEqual(report.open_pull_requests, 1)
        self.assertEqual(report.closed_items, 1)
        self.assertEqual([item.number for item in report.stale_open_items], [1, 4])
        self.assertEqual([item.number for item in report.unlabeled_open_items], [3])
        self.assertEqual(report.label_counts, {"bug": 1, "docs": 1, "enhancement": 1})

    def test_normalize_items_accepts_list_export(self):
        raw_items = SAMPLE_EXPORT["issues"] + SAMPLE_EXPORT["pull_requests"]

        items = normalize_items(raw_items)

        self.assertEqual(len(items), 4)
        self.assertEqual(items[-1].kind, "pull_request")

    def test_normalize_items_rejects_unsupported_json_shape(self):
        with self.assertRaisesRegex(ValueError, "export must be"):
            normalize_items({"unexpected": "shape"})

    def test_render_markdown_uses_stable_maintainer_sections(self):
        report = analyze_items(
            normalize_items(SAMPLE_EXPORT),
            as_of=date(2026, 6, 4),
            stale_days=30,
        )

        markdown = render_markdown(report)

        self.assertIn("# Maintainer Report", markdown)
        self.assertIn("## Summary", markdown)
        self.assertIn("- Open issues: 2", markdown)
        self.assertIn("- Open pull requests: 1", markdown)
        self.assertIn("## Attention Queue", markdown)
        self.assertIn("- issue #1 Crash on startup [stale]", markdown)
        self.assertIn("- issue #3 Needs triage [unlabeled]", markdown)
        self.assertIn("- pull_request #4 Add JSON fixture support [stale]", markdown)
        self.assertIn("## Label Frequency", markdown)
        self.assertIn("- bug: 1", markdown)


if __name__ == "__main__":
    unittest.main()
