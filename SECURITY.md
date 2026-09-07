# Security Policy

## Supported release

Security reports are accepted for the current published public alpha `0.1.0a6`, released from commit `9f71a34f5d7eb0e25359ccf31d0c6d85570203d8`.

## Reporting

Do not open a public Issue for a suspected vulnerability that could expose credentials, personal data, private infrastructure, or a practical bypass. Use GitHub Private Vulnerability Reporting when enabled for the public repository. Until that channel is available, contact the repository owner privately through the account contact method and provide only the minimum information needed to establish a secure reporting route.

Include:

- affected version and release/tag identity;
- affected component and deployment assumptions;
- impact and required privileges;
- minimal reproduction with secrets removed;
- whether an external effect may already have occurred;
- suggested mitigation, when known.

## Security model boundary

RPR is a control and evidence component inside a host application. The host remains responsible for authentication, authorization, credential isolation, network controls, storage access, bypass prevention, domain-specific readback, and deployment monitoring.

RPR does not claim to provide a production identity provider, secret manager, network sandbox, centralized gateway, strict tenant isolation, signed immutable evidence, or exactly-once guarantees across arbitrary remote systems.

## Ambiguous external effects

When transport failure occurs after dispatch, treat the result as potentially applied. Preserve evidence, stop automatic continuation, and perform independent readback or reconciliation.

If the effect remains unresolved, preserve it under an explicit Responsibility Route. The correct next state may be a reconciliation hold, bounded Human Return, another explicitly delegated eligible receiver, or stop-and-preserve-residue. Do not manufacture a Human Gate merely because the outcome is uncertain, and do not retry merely to demonstrate the issue.

Evidence transfer, receiver capability, transport success, or recovered state do not create Authority. Any next receiver must be eligible for the bounded action and must operate within declared delegation.

## Disclosure

The maintainer will validate the report, classify the affected boundary, and coordinate remediation and disclosure when practical. No response-time guarantee is provided for this open-source alpha.
