# Responsibility Pathway Runtime

**Govern external actions without losing evidence, recovery, or the human decision point.**

Responsibility Pathway Runtime (RPR) is an MIT-licensed Python runtime for applications that need to place an explicit responsibility pathway in front of consequential external actions. It helps a host application preserve actor and authority declarations, execution-attempt continuity, readback evidence, fail-closed ambiguity handling, repair routes, and Human Gate decisions.

> **Public alpha — 0.1.0a2**  
> Freeze ID: `RPR-CF-2026-08-01-02`  
> Tested final rehearsal profile: Linux, Python 3.11  
> RPR is not a legal-responsibility engine, identity provider, secret manager, production gateway, or guarantee of exactly-once effects across arbitrary remote systems.

[日本語の入口](docs/ja/README.md) · [Product documentation](docs/en/README.md) · [Report an issue](https://github.com/YutoriKomeiji/responsibility-pathway-runtime/issues)

## Verified in the frozen alpha candidate

- pathway registration and authorized state transitions;
- persistent pathway and execution-attempt stores;
- Human Gate, repair, resume, and reconciliation boundaries;
- local-file, allow-listed HTTP, durable outbound-message, and real MCP subprocess paths;
- fail-closed ambiguous-write handling;
- restart, backup, restore, diagnostics, uninstall, and customer-data retention;
- clean wheel and source-distribution installation;
- reproducible release artifacts;
- English-primary and Japanese-parallel product documentation.

## Field evidence requested

Please report reproducible findings for Windows, macOS, additional Linux/container environments, proxy/TLS/identity/credential routes, remote MCP, framework integrations, installation, operations, recovery, and documentation usability. A report is evidence for that environment; it does not imply universal production readiness.

## Artifact verification

```text
responsibility_pathway_runtime-0.1.0a2-py3-none-any.whl
SHA-256 33f1f9255ee93b4f8be28abf3d547a038eea463e7d0965dada843d8724af3790
size 107214 bytes

responsibility_pathway_runtime-0.1.0a2.tar.gz
SHA-256 7a82e586d44954ed3c3ead0b7d89dba27cb3d308f0fe721cbe8b37d55e1541dd
size 129479 bytes
```

## Integration boundary

The host application remains responsible for authentication, credential isolation, network controls, bypass prevention, domain-specific authorization, and independent readback. RPE integration is optional; absent, malformed, or unsupported RPE output must not become implicit permission.

## License

Released under the [MIT License](LICENSE). Copyright © 2026 Akihisa Ono.
