# Security Policy

## Supported Versions

The main branch is the only supported development line until the project publishes tagged releases.

## Reporting a Vulnerability

Please open a private security advisory on GitHub if the repository is hosted there. If private advisories are unavailable, open a minimal public issue that states a security report exists without including exploit details.

Do not include real private issue exports, access tokens, credentials, or customer data in reports. Synthetic reproduction data is preferred.

## Security Scope

Maintainer Report is a local CLI. It does not make network calls, require credentials, or execute content from the input JSON. Security reviews should focus on parser behavior, generated report content, packaging, and accidental disclosure through committed fixtures.
