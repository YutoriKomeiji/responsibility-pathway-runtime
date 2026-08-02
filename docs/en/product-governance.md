<!--
Document Title: RPR Product Governance
Document Type: Public Product Operations Policy
Status: Active
Header Language: English
Body Language: English
-->

# RPR product governance

## Product source of truth

`YutoriKomeiji/responsibility-pathway-runtime` is the sole source of truth for the RPR product implementation.

The following are maintained here:

- runtime source and tests;
- package metadata and release artifacts;
- public specifications and product documentation;
- English and Japanese product pages;
- CI, Issue Forms, security policy, changelog, and release records;
- user-reported issues and implementation pull requests.

Product fixes must not be applied only to a preparation snapshot in another repository.

## Normal change route

User feedback and defects follow this route:

1. Open or triage an RPR Issue.
2. Create an RPR branch and pull request.
3. Run RPR CI and review the evidence.
4. Merge the approved change into RPR `main`.
5. Close or link the Issue and include the change in an RPR release when appropriate.

Security vulnerabilities use the private reporting route described in `SECURITY.md`, not a public Issue.

## Escalation to the Responsibility Pathway Program

Most fixes and bounded product enhancements remain entirely in RPR.

Escalation to the Responsibility Pathway Program is required when a proposal changes program-level theory or responsibility boundaries, including:

- Human Gate semantics;
- the division of responsibility between RPD, RPE, and RPR;
- canonical pathway states or transition meaning;
- residual ownership semantics;
- assurance or public claim boundaries.

After a program-level decision is adopted, implementation still returns to an RPR pull request. The production code remains canonical in RPR.

## Carryback

RPR may carry release results, evidence summaries, and design-escalation outcomes back to the Responsibility Pathway Program. Carryback records do not turn a program repository snapshot into the product source of truth.
