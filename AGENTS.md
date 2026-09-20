# Agent instructions for Responsibility Pathway Runtime

This file is the agent-facing entrypoint for repository work. Detailed product, contribution, release, and authoring rules remain in their existing source files.

## Read first

Before editing RPR, fresh-read:

1. `README.md`
2. `product-status.json`
3. `docs/en/README.md` or `docs/ja/README.md` for the affected language surface
4. `CONTRIBUTING.md`
5. the exact specification/test/document affected by the change
6. `.github/authoring/rpr-japanese-writing-standard.md` for Japanese public-surface writing

For verification/evaluation work also read `docs/en/verification-release-uat.md` or its Japanese counterpart.

Do not infer current release state from historical records under `release-history/`.

## Repository role

RPR is a public installable runtime for preserving responsibility state around consequential external actions, especially ambiguous post-dispatch effects, readback, repair/resume, restart continuity, Responsibility Routing, and bounded Human Return.

## Surface projection

Use the smallest surface that matches the role:

- README / product site: human-first product explanation plus compact factual automated-reader information.
- Product documentation: detailed integration and operating responsibilities.
- Verification / Release / UAT guide: evaluator procedure and evidence-reading discipline.
- `product-status.json`, claim/test registries, manifests: structured machine-readable current facts.
- `.github/authoring/`: repository authoring controls, not user-facing product guidance.
- `release-history/`: historical evidence, not current product state.

Do not place run-local evaluator procedure in the product narrative merely because an AI may read it.

## Currentness and parity

When public behavior or claims change, reconcile all affected surfaces:

- Python/API/persistence behavior
- CLI/MCP
- EN/JA docs
- product site/demo
- claim/test/evidence registries
- version and release-state metadata

Keep published package, current `main`, candidate state, and historical release records distinct.

## Evidence and claim boundaries

Do not infer Authority from evidence transfer, capability, route selection, tool success, transport success, or recovered state.

Do not convert `write_status_unknown` into completion or automatic retry.

Demo and source comments should state the local semantic boundary that a reader needs; avoid repeating repository-wide disclaimer inventories when a narrower scope statement is sufficient.

## Human-gated actions

Do not autonomously publish a package, create a release/tag, change permissions/credentials, promote production-readiness claims, or make Authority/canonical semantic changes without the applicable explicit approval.
