# RPR Architecture

```text
Agent plan / proposed tool call
        ↓
RPR pathway definition and inspection
        ↓
RPE bounded requirement evaluation
        ↓
allow / hold / human_gate / deny
        ↓
RPR state machine and execution-attempt ledger
        ↓
Authorized executor
        ↓
External effect
        ↓
Readback / reconciliation / repair / human return
```

RPR owns pathway lifecycle, execution correlation, state, evidence continuity, readback, reconciliation, repair routing, resume, and residual ownership.

RPE owns bounded evaluation of approved machine-readable Requirement Packs. RPR must not copy or silently redefine RPE policy semantics.

## Trust boundaries

- The host application authenticates principals.
- RPR binds authenticated principals to declared pathway actors.
- Executors preserve operation ID, attempt ID, idempotency key, and readback evidence.
- External completion is never inferred from a callback alone.
- Unknown writes remain unknown until independently reconciled.
- Human Gates require an authorized transition.

## Formal boundary

The canonical transition model is represented in JSON, Python, and Lean 4. Parity checks and selected Lean invariants provide bounded machine-checkable evidence. They do not prove the complete deployed system, external environment, legal validity, or operational suitability.
