# Support and Maturity by Surface

RPR uses per-surface maturity rather than treating the entire repository as uniformly experimental.

| Surface | Current posture | Notes |
|---|---|---|
| Core Python/SQLite pathway runtime | Supported | Intended for bounded real integrations within documented contracts. |
| Pathway persistence / restart continuity | Supported | Covered by repository tests and public scenarios. |
| Responsibility Routing / bounded Human Gate / repair / resume / reconciliation | Supported source preview | Routing is additive and tested in current source; the published `0.1.0a5` package predates the route-visibility addition. |
| Local-file and bounded outbound paths | Supported reference | Usable with integration-specific authority/network controls. |
| Governed outbound MCP subprocess path | Supported reference | Reference integration; peer identity and deployment controls remain integrator-owned. |
| Read-only `rpr-mcp` inspection server | Supported reference | Local trusted-client inspection surface; current source adds read-only route visibility. |
| Article 50 transparency profile | Preview / bounded profile | Structured profile only; not legal classification or compliance certification. |
| Customer-equivalent proxy/TLS/identity profiles | Field evidence collecting | Real environment reports are welcome; universal readiness is not claimed. |
| Remote production MCP transport | Not included | Future scoped work only. |
| Universal exactly-once across arbitrary systems | Unsupported as a universal claim | Requires target-side contracts and authoritative readback. |
| Legal/organizational authority creation | Unsupported | RPR preserves declared Authority; it does not create it. |

## Responsibility Routing maturity boundary

Responsibility Routing in the current source distinguishes bounded Human Return from neutral hold, reconciliation hold, delegated eligible receivers, and stop/preserve outcomes. The route record preserves receiver eligibility, delegation scope, unresolved payload, allowed next actions, closure/reevaluation conditions, and Residual Owner.

This does not mean every possible organizational route is supported. Receiver eligibility and Authority must be supplied by the integrating boundary; evidence transfer, capability, successful transport, or route selection do not create Authority.

The current Lean layer proves selected state-transition invariants only. It does not formally prove Responsibility Routing receiver eligibility or delegation semantics.

## Vocabulary

- **Supported** — normal use is intended within documented boundaries; defects are accepted and repaired.
- **Supported source preview** — implemented and tested in repository source but not yet promoted as a separately released package contract.
- **Supported reference** — usable reference implementation; deployment hardening may remain integrator-owned.
- **Preview** — suitable for early use and feedback; interface/semantics may evolve.
- **Field evidence collecting** — implemented but broader environment evidence is still being accumulated.
- **Not included** — not supplied by the current project surface.
- **Unsupported** — deliberately not promised or not authority the runtime should create.

`Not guaranteed` does not automatically mean `forbidden`.
