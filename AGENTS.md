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

## GitHub Actions preflight

Before making a change that may trigger GitHub Actions:

1. Identify the workflows triggered by the target paths and event.
2. Inspect the relevant workflow definitions before changing files. If the workflow has not run recently, especially after several days, also inspect its latest runs and recent failure history before triggering it again.
3. Check referenced action/runtime versions, dependency-install behavior, runner assumptions, and obvious deprecation or staleness risks.
4. Check freeze, release, candidate, publication, branch, path-filter, and other repository-specific gates before changing a governed path.
5. Keep mutually dependent source, test, schema, generated, or fixture changes atomic where practical so an intermediate commit does not create avoidable red runs.
6. After the change, read back every workflow triggered by that change to a terminal state. Do not report the change as green while relevant runs are queued or in progress.
7. Treat historical failed runs as retained evidence. Do not rerun, erase, or cosmetically replace them only to make the Actions UI green.

A passing workflow proves only the scope asserted by that workflow. It does not replace repository-specific Authority, release, publication, or evidence gates.
