# Security Policy

## Supported release

Security reports are accepted for the current public alpha candidate `0.1.0a2`, Freeze ID `RPR-CF-2026-08-01-02`.

## Reporting

Do not open a public Issue for a suspected vulnerability that could expose credentials, personal data, private infrastructure, or a practical bypass. Use GitHub Private Vulnerability Reporting when enabled for the public repository. Until that channel is available, contact the repository owner privately through the account contact method and provide only the minimum information needed to establish a secure reporting route.

Include:

- affected version and Freeze ID;
- affected component and deployment assumptions;
- impact and required privileges;
- minimal reproduction with secrets removed;
- whether an external effect may already have occurred;
- suggested mitigation, when known.

## Security model boundary

RPR is a control and evidence component inside a host application. The host remains responsible for authentication, authorization, credential isolation, network controls, storage access, bypass prevention, domain-specific readback, and deployment monitoring.

RPR does not claim to provide a production identity provider, secret manager, network sandbox, centralized gateway, strict tenant isolation, signed immutable evidence, or exactly-once guarantees across arbitrary remote systems.

## Ambiguous external effects

When transport failure occurs after dispatch, treat the result as potentially applied. Preserve evidence, stop automatic continuation, perform independent readback or reconciliation, and route unresolved cases to an authorized Human Gate. Do not retry merely to demonstrate the issue.

## Disclosure

The maintainer will validate the report, classify the affected boundary, and coordinate remediation and disclosure when practical. No response-time guarantee is provided for this open-source alpha.