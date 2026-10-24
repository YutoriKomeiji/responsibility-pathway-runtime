# First working result: uncertain external writes

**Problem:** An AI agent dispatches a write, then loses the response. Retrying blindly may duplicate a real external effect. RPR preserves the unresolved outcome and the responsibility path needed to reconcile it.

## Start from the published package

Requirements: Python 3.11+.

```bash
python -m pip install responsibility-pathway-runtime==0.1.0a6
rpr --help
rpr-mcp --help
```

These commands confirm the published distribution and its CLI/MCP entry points. They do **not** execute a real remote mutation or demonstrate a completed incident recovery.

Next, follow the repository's [Quick Start](en/quick-start.md) for a runnable example. For API and integration boundaries, use [Security, integration and API](en/security-integration-api.md) and [MCP integration](en/mcp-integration.md).

## What to look for

- A post-dispatch unknown outcome remains unresolved (`write_status_unknown`), not an automatic failure or success.
- Independent readback and reconciliation are separate from the dispatch receipt.
- Replaying an unresolved write requires explicit permission and the appropriate recovery route.
- Human Return is a bounded route, not the default for every error.

The published `0.1.0a6` package and the repository `main` may differ; for released behavior use the pinned package and its tag.

## Build on this foundation

Use, adapt, and fork RPR under its [MIT license](../LICENSE). You do not have to submit improvements upstream. Reproducible installation reports, integration findings, counterexamples and focused PRs are welcome: see [CONTRIBUTING](../CONTRIBUTING.md) and [Issues](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/issues).

In particular, proxy/TLS, framework, remote MCP, restart and real-system edge cases that cannot be exercised in the maintainer's personal CI environment are useful opportunities for independent verification. Include exact versions, conditions, expected versus observed behavior and redacted logs. Report security-sensitive issues via [SECURITY](../SECURITY.md), not a public exploit issue.

The documented tests establish only the behavior they execute. Real deployments must provide their own credentials, operational authorization, verification sources and recovery ownership.
