# Support and Field Use

Responsibility Pathway Runtime is actively developed and may be used within documented boundaries. The project welcomes reproducible reports from real integrations because field use is part of the product-quality and evidence loop.

`Public Alpha` describes release maturity and change expectations; it does not mean `do not use`.

## Open a public Issue for

- installation or packaging failures;
- unexpected pathway, attempt, retry, restart, repair, resume, or reconciliation behavior;
- HTTP, MCP, proxy, TLS, identity, or service-integration findings that do not expose secrets;
- platform reports for Windows, macOS, Linux distributions, containers, and supported Python versions;
- documentation, example, API, or operational usability problems;
- feature and integration requests with a concrete use case;
- cases where the runtime is too heavy, too restrictive, or too permissive for the intended pathway;
- adversarial cases that do not require confidential disclosure.

Include the RPR version and Freeze ID where available, operating system, Python version, installation method, minimal reproduction, expected result, observed result, logs with secrets removed, and whether an external effect may have occurred.

## Stop before repeating an ambiguous action

When a request may have reached an external system but the result is unknown, do not repeatedly retry merely to reproduce the issue. Preserve the pathway, attempt, idempotency identifier, timestamps, logs, and independent readback evidence. Report the state as unresolved.

## Current use posture

RPR's documented runtime, persistence, Human Gate, restart/reconciliation, repair/resume, evidence, readback, and bounded MCP surfaces are intended to be tried in real bounded integrations.

Deployment-specific authentication, authorization, credential isolation, network/TLS policy, tenant isolation, bypass prevention, and external-system correctness remain integrator-owned unless a future RPR surface explicitly provides them.

That boundary means `not provided by RPR`, not `all real use is forbidden`.

## Environment reports

Reports from real environments extend field evidence for those environments. They do not automatically create a universal production-readiness claim. Production deployment should still have a named owner, deployment-specific authorization and bypass controls, credential and network review, independent readback where required, recovery procedures, and an explicit acceptance decision.

## Security-sensitive reports

Do not post credentials, access tokens, personal data, private endpoints, exploit details, or confidential evidence in a public Issue. Follow [SECURITY.md](SECURITY.md).

## Compatibility and support line

The current `0.x` line may evolve and may contain breaking changes. `0.x` means evolving contract surface, not evaluation-only software. Breaking changes should be versioned and accompanied by migration guidance where practical.

The project is best-effort OSS without guaranteed response or resolution time. Maintainers may ask for a smaller reproduction, additional evidence, or an environment-specific test before classifying a report.
