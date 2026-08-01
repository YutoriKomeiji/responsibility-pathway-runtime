# Support and Field Testing

Responsibility Pathway Runtime is currently a public alpha. The project welcomes reproducible reports that improve product quality, documentation, and environment coverage.

## Open a public Issue for

- installation or packaging failures;
- unexpected pathway, attempt, retry, restart, repair, resume, or reconciliation behavior;
- HTTP, MCP, proxy, TLS, identity, or service-integration findings that do not expose secrets;
- platform reports for Windows, macOS, Linux distributions, containers, and supported Python versions;
- documentation, example, API, or operational usability problems;
- feature and integration requests with a concrete use case.

Include the RPR version and Freeze ID, operating system, Python version, installation method, minimal reproduction, expected result, observed result, logs with secrets removed, and whether an external effect may have occurred.

## Stop before repeating an ambiguous action

When a request may have reached an external system but the result is unknown, do not repeatedly retry merely to reproduce the issue. Preserve the pathway, attempt, idempotency identifier, timestamps, logs, and independent readback evidence. Report the state as unresolved.

## Environment reports

Reports from real environments extend field evidence for those environments. They do not create a universal production-readiness claim. Production deployment requires a named owner, deployment-specific authorization and bypass controls, credential and network review, independent readback, recovery procedures, and an explicit acceptance decision.

## Security-sensitive reports

Do not post credentials, access tokens, personal data, private endpoints, exploit details, or confidential evidence in a public Issue. Follow [SECURITY.md](SECURITY.md).

## Service level

This open-source alpha is provided without a guaranteed response or resolution time. Maintainers may ask for a smaller reproduction, additional evidence, or an environment-specific test before classifying a report.