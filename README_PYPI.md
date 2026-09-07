# Responsibility Pathway Runtime

## Public Alpha — 0.1.0a6

Package identity: `responsibility-pathway-runtime==0.1.0a6`.

RPR is an MIT-licensed Python runtime for AI agents and automation that perform consequential external actions. It keeps authorization, execution attempts, uncertain external effects, reconciliation, repair/resume boundaries, and Responsibility Routing connected across failures and restarts.

Responsibility Routing treats Human Return as one bounded route rather than the generic meaning of fail-closed behavior. Neutral hold and reconciliation hold remain available when receiver eligibility, Authority, or external effect status is unresolved. Evidence transfer, route selection, transport success, and receiver capability do not create Authority.

### Included surfaces

- persistent pathway and execution-attempt state;
- explicit `write_status_unknown` handling for ambiguous post-dispatch effects;
- reconciliation, repair, resume, and bounded Human Return;
- Responsibility Routing metadata and read-only route visibility;
- local-file, allow-listed HTTP, durable outbound-message, and MCP subprocess execution paths;
- Published read-only MCP inspection server using stable MCP protocol `2025-11-25`;
- `rpr` and `rpr-mcp` command-line entry points;
- English/Japanese browser demo surfaces backed by the built wheel.

### Verification scope

The 0.1.0a6 candidate passed the complete standalone suite (477 tests), production-grade demo tests, clean wheel installation, CLI checks, Lean 4 / JSON / Python parity checks, reproducible artifact verification, and English/Japanese browser/Pyodide E2E checks before release authorization.

### Boundaries

This Public Alpha does not establish universal production readiness, enterprise readiness, customer-environment verification, legal/compliance certification, universal exactly-once external effects, full formal verification, or transfer of final responsibility to software. Receiver eligibility and organizational/legal Authority remain integration responsibilities.

Project home: https://github.com/YutoriKomeiji/responsibility-pathway-runtime
