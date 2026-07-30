# Security Policy

RPR is currently a private alpha and productization candidate. It is not a production authorization, certification, compliance determination, or guarantee of safety.

## Reporting a vulnerability

Please report suspected vulnerabilities privately to the repository owner before public disclosure. Include:

- affected version or commit;
- reproduction steps;
- expected and observed behavior;
- impact on authority, Human Gate, evidence, execution, retry, reconciliation, or residual ownership;
- suggested mitigation when available.

Do not include live credentials, personal data, or third-party secrets in reports.

## Security boundaries

RPR is designed to fail closed at its own runtime boundary. Host applications remain responsible for authentication, authorization, network isolation, secret management, deployment controls, data protection, and infrastructure tenancy.

Formal checks cover only explicitly modeled properties and assumptions. They do not prove the security of the complete Python runtime, dependencies, external services, deployment environment, or operational process.
