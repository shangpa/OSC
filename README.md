# Codex Kit

Codex Kit is a dependency-free Python CLI for repository-local Codex readiness checks, MCP safety validation, and small agent eval workflows. It is an early-stage open-source maintainer tool and does not claim external program eligibility, adoption, or sponsorship.

## Features

- `codex-kit scan`: inspect AGENTS.md files, Codex config presence, MCP references, stale path hints, missing test/build command guidance, unsafe destructive instructions, and Windows/WSL `node_modules` risk.
- `codex-kit mcp doctor`: planned static MCP configuration validation.
- `codex-kit eval`: planned repo-local eval case management.

## Install From Source

```bash
python -m pip install -e .
```

## Usage

Scan the current repository:

```bash
codex-kit scan
```

Scan another repository:

```bash
codex-kit scan /path/to/repo
```

Run without installing the console script:

```bash
PYTHONPATH=src python -m codex_kit scan .
```

## Development

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

Compile-check source and tests:

```bash
python -m compileall src tests
```

## Maintainer Workflow Fit

Codex Kit is intended for maintainers who want to understand what instructions, MCP references, and local eval definitions an agent will see before they rely on automation for issue triage, code review, or release work.

## License

MIT. See [LICENSE](LICENSE).
