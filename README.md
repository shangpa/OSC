# Maintainer Report

Maintainer Report is a dependency-free Python CLI that turns issue and pull request export JSON into a markdown triage report. It is designed for open-source maintainers who want a quick local view of stale work, unlabeled work, and label distribution before reviewing queues or planning a release.

This project is an early-stage open-source scaffold. It does not claim ecosystem importance, adoption, sponsorship, or eligibility for any external support program.

## What It Does

- Reads a JSON export containing issues and pull requests.
- Counts open issues, open pull requests, closed items, stale open items, and unlabeled open items.
- Produces a deterministic markdown report for maintainers.
- Runs locally without GitHub tokens, API keys, network access, or runtime dependencies.

## Install From Source

```bash
python -m pip install -e .
```

## Usage

Print a report to stdout:

```bash
maintainer-report samples/github-export.json --as-of 2026-06-04
```

Write a report to a file:

```bash
maintainer-report samples/github-export.json --as-of 2026-06-04 --output report.md
```

Run without installing the console script:

```bash
PYTHONPATH=src python -m maintainer_report samples/github-export.json --as-of 2026-06-04
```

## Input Format

The CLI accepts either a list of item objects or an object with these buckets:

```json
{
  "issues": [],
  "pull_requests": []
}
```

Each item can include:

```json
{
  "number": 1,
  "title": "Crash on startup",
  "state": "open",
  "labels": [{ "name": "bug" }],
  "updated_at": "2026-05-01T09:30:00Z",
  "html_url": "https://example.test/issues/1"
}
```

Labels may be strings or GitHub-style objects with a `name` field. Pull requests can be supplied in the `pull_requests` bucket, marked with `kind: "pull_request"`, or inferred from URLs containing `/pull/`.

## Example Output

```markdown
# Maintainer Report

## Summary
- Total items: 4
- Open issues: 2
- Open pull requests: 1
- Closed items: 1
- Stale open items: 2
- Unlabeled open items: 1
```

## Development

Run the test suite:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

Compile-check the package and tests:

```bash
python -m compileall src tests
```

## Maintainer Workflow Fit

This repository focuses on practical open-source maintenance work: triage, release preparation, and queue review. A maintainer can use the report before reviewing issues, preparing release notes, or deciding where automation would reduce repetitive work.

Potential future use of API credits should be optional and maintainer-controlled, such as summarizing local reports, drafting release-note candidates from already exported metadata, or generating test fixtures. The current tool intentionally works without external APIs.

## License

MIT. See [LICENSE](LICENSE).
