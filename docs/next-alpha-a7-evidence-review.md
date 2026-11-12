# RPR 0.1.0a7 — candidate evidence review (not a release)

Status: REVIEW / UNRELEASED / evidence pending. Current public distribution remains `0.1.0a6`.

## Product value under review
The published RPR runtime preserves responsibility state for ambiguous writes, restart and reconciliation. Current main adds a bounded framework-neutral compatibility probe using actual LangGraph StateGraph, OpenAI Agents SDK FunctionTool, Temporal Python SDK ActivityEnvironment, and plain Python. It checks that a response lost after dispatch remains `write_status_unknown` and that repeating the same call identity does not blindly redispatch. The Temporal coverage is an activity-test boundary, not a full server/worker production deployment. These source-level observations do not imply a released a7 wheel or third-party deployment success.

## Exact evidence owners
- Source: `src/rpr/agent_adapters.py`, `tests/integration/test_cross_runtime_responsibility_boundary.py`
- Workflow: `.github/workflows/cross-runtime-e2e.yml` (installs real framework libraries without fixed version pins; resolved versions printed by CI)
- Legacy/standalone baseline and distribution: `.github/workflows/public-export-quality.yml`, `product-status.json`, `CHANGELOG.md`
- Open security change: PR #56 is separate; check merge/coverage before final candidate freeze.

## Two-sided claim review
**Do claim after exact-head tests:** The specified activity/node/function-tool integrations preserve the same declared ambiguous-write boundary under the tested versions and fixture.
**Do not underclaim:** Calling the repository only a demo or calling the framework integrations nonexistent is false given the exercised code path.
**Do not overclaim:** No universal framework compatibility, complete Temporal deployment semantics, independent customer validation, full exactly-once guarantee or enterprise production certification is established.

## Evidence not yet established
1. Exact-head successful cross-runtime CI and source unit/integration coverage for this candidate branch.
2. Complete standalone/package wheel+sdist, clean install, CLI/MCP, browser demo, reproducibility and failure-injection suite at same head.
3. PR #56 security fix ownership and compatibility with the candidate.
4. EN/JA README/site/manifest and PyPI long-description version identity for any future version bump.
5. Release owner authorization and separate Human Gate for tag/GitHub prerelease/PyPI.

## Candidate sequence
1. Finish bounded regression review without changing published version metadata.
2. Reconcile unmerged security PR and exact-head evidence; if tests fail, repair source and re-run.
3. On a dedicated candidate commit, update all version-bearing surfaces together; never claim PyPI publication before readback.
4. Obtain explicit Human Gate **after** exact-head package validation. Publication is intentionally out of scope here.
