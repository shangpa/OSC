# Contributing

Thanks for considering a contribution to Maintainer Report. The project is intentionally small and dependency-free so maintainers can audit and run it quickly.

## Development Setup

```bash
python -m pip install -e .
PYTHONPATH=src python -m unittest discover -s tests
```

## Contribution Guidelines

- Keep runtime dependencies at zero unless there is a clear maintainer benefit.
- Add or update tests for behavior changes.
- Use synthetic fixtures only; do not commit private repository exports.
- Keep CLI output deterministic so reports can be reviewed in pull requests.
- Avoid claims about project adoption or eligibility for external programs unless they are backed by public evidence.

## Pull Request Checklist

- Tests pass with `PYTHONPATH=src python -m unittest discover -s tests`.
- `python -m compileall src tests` passes.
- Documentation examples still match the CLI.
