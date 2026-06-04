# Security Policy

## Supported Versions

The main branch is the only supported development line until the project publishes tagged releases.

## Reporting a Vulnerability

Please open a private security advisory on GitHub if the repository is hosted there. If private advisories are unavailable, open a minimal public issue that states a security report exists without including exploit details.

Do not include tokens, private MCP configuration, private AGENTS.md content, customer data, or real repository exports in reports. Synthetic reproduction data is preferred.

## Security Scope

Codex Kit is a local CLI. It should not start MCP servers during validation, execute Codex during dry-run evals, make network calls, or print secret values from configuration files.
