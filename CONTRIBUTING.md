# Contributing

Thanks for considering a contribution to Codex Kit. Keep the project dependency-free and focused on repository-local agent maintenance workflows.

## Development Setup

```bash
python -m pip install -e .
PYTHONPATH=src python -m unittest discover -s tests
```

## Guidelines

- Add or update tests for behavior changes.
- Use synthetic fixtures only; do not commit private repo exports, secrets, or customer data.
- Do not start MCP servers or execute Codex from tests.
- Keep CLI output deterministic enough for pull request review.
- Avoid claims about project adoption or eligibility for external programs unless backed by public evidence.
