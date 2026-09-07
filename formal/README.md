# RPR Formal Assurance Layer

This Lean 4 package models selected RPR runtime state-transition invariants. It is independent from the Python runtime and is not required to deploy the Python package, but it is part of the public verification surface.

## Pinned environment

- Lean: `v4.30.0`
- build tool: Lake distributed with the pinned Lean toolchain
- external Lean packages: none

## Build

From this directory:

```sh
lake build
```

A successful build checks the declarations and proofs in `rprFormal/` with the pinned Lean kernel.

## Proved scope

- `humanGate` cannot transition directly to `completed`;
- `writeStatusUnknown` can enter only `repairRequired` or `completed` after an independently reconciled result;
- `completed`, `denied`, and `aborted` have no successors;
- every terminal state has no successor;
- only `running` or a reconciled `writeStatusUnknown` state can enter `completed`;
- repair and resume do not bypass their separated transition stages.

## Cross-model checks

The repository test suite compares this Lean transition relation with:

- the Python runtime transition table;
- `specs/pathway-state-machine.json`.

These checks establish parity for the explicit state and transition model. They do not prove all runtime behavior.

## Responsibility Routing boundary

Responsibility Routing metadata and receiver-selection semantics are currently verified by the Python model, persistence/inspection tests, MCP read-only visibility tests, and product-level negative tests. They are **not** represented as Lean proofs in this package.

In particular, this formal layer does not prove:

- receiver eligibility;
- delegation scope correctness;
- Authority non-propagation through evidence or route transfer;
- Residual Owner preservation across arbitrary organizational redesign;
- absence of False Autonomy, Proxy Return, False Escalation, or Nominal Human Return outside the explicitly tested runtime paths.

A successful Lean build therefore must not be described as formal proof of Responsibility Routing as a whole.

## Non-claims

This package does not prove:

- authentication or authorization correctness outside the abstract model;
- executor behavior, external readback, or network effects;
- temporal or distributed-system properties;
- full Python runtime correctness;
- production safety, legal compliance, or regulatory certification.

Formal verification evidence remains separate from release authorization.
