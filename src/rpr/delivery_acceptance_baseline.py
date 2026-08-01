# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from rpr.delivery_acceptance import DeliveryAcceptanceMatrix, build_matrix


_EVIDENCE = {
    "traceability": (
        "incubator/rpr/specs/pathway-state-machine.json",
        "incubator/rpr/src/rpr/claim_traceability.py",
        "incubator/rpr/tests/test_claim_traceability.py",
    ),
    "runtime_paths": (
        "incubator/rpr/tests/test_product_e2e.py",
        "incubator/rpr/tests/test_product_e2e_rpe_reconciliation.py",
        "incubator/rpr/tests/test_product_e2e_rpe_unavailable_substitution.py",
        "incubator/rpr/tests/test_product_e2e_human_gate_return.py",
        "incubator/rpr/tests/test_product_e2e_repair_resume_retry.py",
        "incubator/rpr/tests/test_product_e2e_explicit_compensation.py",
        "incubator/rpr/tests/test_resume_authorization_restart.py",
    ),
    "authority_and_escalation": (
        "incubator/rpr/tests/test_product_e2e_human_gate_return.py",
        "incubator/rpr/tests/test_abort_residual_binding.py",
        "incubator/rpr/tests/test_inspection.py",
        "incubator/rpr/src/rpr/diagnostics.py",
    ),
    "lifecycle_operations": (
        "incubator/rpr/pyproject.toml",
        "incubator/rpr/src/rpr/backup.py",
        "incubator/rpr/tests/test_backup_export.py",
        "incubator/rpr/src/rpr/lifecycle_acceptance.py",
        "incubator/rpr/tests/test_lifecycle_acceptance.py",
        "incubator/rpr/fixtures/lifecycle/previous-candidate-v1.json",
        ".github/workflows/rpr-lifecycle-acceptance.yml",
    ),
    "supported_scope": (
        "incubator/rpr/docs/known-limitations.md",
        "incubator/rpr/docs/product-positioning.md",
        "incubator/rpr/docs/formal-methods-integrity.md",
    ),
    "release_artifacts": (
        "incubator/rpr/src/rpr/release_audit.py",
        "incubator/rpr/src/rpr/rc_execution.py",
        "incubator/rpr/tests/test_release_audit.py",
        "incubator/rpr/tests/test_release_prep_bundle.py",
        ".github/workflows/rpr-test.yml",
    ),
    "customer_handover": (
        "incubator/rpr/docs/using-rpr.md",
        "incubator/rpr/src/rpr/diagnostics.py",
        "incubator/rpr/src/rpr/customer_handover.py",
        "incubator/rpr/tests/test_customer_handover.py",
        ".github/workflows/rpr-customer-handover.yml",
    ),
}


def build_delivery_acceptance_baseline(
    *,
    source_commit: str,
    residual_owner: str,
) -> DeliveryAcceptanceMatrix:
    """Return the conservative post-hardening B2B acceptance baseline.

    Verified dimensions point to retained implementation and test evidence.
    Pending dimensions remain explicit so documentation gaps cannot be
    mistaken for completed customer acceptance or release approval.
    """

    statuses = {
        "traceability": "verified",
        "runtime_paths": "verified",
        "authority_and_escalation": "verified",
        "lifecycle_operations": "verified",
        "supported_scope": "verified",
        "release_artifacts": "verified",
        "customer_handover": "verified",
        "bilingual_documents": "pending",
    }
    return build_matrix(
        source_commit=source_commit,
        statuses=statuses,
        evidence=_EVIDENCE,
        blockers={},
        residual_owner=residual_owner,
    )
