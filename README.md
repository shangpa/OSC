# Codex Kit

Codex Kit is a dependency-free Python CLI for repository-local Codex readiness checks, MCP safety validation, and small agent eval workflows. It is an early-stage open-source maintainer tool and does not claim external program eligibility, adoption, or sponsorship.

## Features

- `codex-kit scan`: inspect AGENTS.md files, Codex config presence, MCP references, stale path hints, missing test/build command guidance, unsafe destructive instructions, and Windows/WSL `node_modules` risk.
- `codex-kit agents graph`: show which AGENTS.md files apply to which repository scopes.
- `codex-kit agents lint`: expose AGENTS.md lint findings as a dedicated command.
- `codex-kit fix --dry-run`: print safe fix suggestions without modifying files.
- `codex-kit mcp doctor`: statically validate MCP configuration without starting MCP servers or printing secret values.
- `codex-kit eval init/add/run --dry-run/report`: manage versioned repo-local eval cases without executing Codex.

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

Inspect AGENTS.md instruction scope and lint findings:

```bash
codex-kit agents graph /path/to/repo
codex-kit agents lint /path/to/repo
codex-kit fix /path/to/repo --dry-run
```

Inspect MCP configuration:

```bash
codex-kit mcp doctor --config .codex/config.toml
```

Create and dry-run eval cases:

```bash
codex-kit eval init
codex-kit eval add smoke --prompt "List files" --verify "python -m unittest" --allowed-changes "src/**"
codex-kit eval run --dry-run
codex-kit eval report
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
