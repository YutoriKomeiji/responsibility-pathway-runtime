# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from __future__ import annotations

from rpr.delivery_acceptance import DeliveryAcceptanceMatrix, build_matrix


_EVIDENCE = {
    "traceability": (
        "specs/pathway-state-machine.json",
        "specs/claim-traceability.json",
        "src/rpr/claim_traceability.py",
        "tests/test_claim_traceability.py",
    ),
    "runtime_paths": (
        "tests/test_product_e2e.py",
        "tests/test_product_e2e_rpe_reconciliation.py",
        "tests/test_product_e2e_rpe_unavailable_substitution.py",
        "tests/test_product_e2e_human_gate_return.py",
        "tests/test_product_e2e_repair_resume_retry.py",
        "tests/test_product_e2e_explicit_compensation.py",
        "tests/test_resume_authorization_restart.py",
    ),
    "authority_and_escalation": (
        "tests/test_product_e2e_human_gate_return.py",
        "tests/test_abort_residual_binding.py",
        "tests/test_inspection.py",
        "src/rpr/diagnostics.py",
    ),
    "lifecycle_operations": (
        "pyproject.toml",
        "src/rpr/backup.py",
        "tests/test_backup_export.py",
        "src/rpr/lifecycle_acceptance.py",
        "tests/test_lifecycle_acceptance.py",
        "fixtures/lifecycle/previous-candidate-v1.json",
        ".github/workflows/public-export-quality.yml",
    ),
    "supported_scope": (
        "docs/en/product-scope-architecture.md",
        "docs/en/security-integration-api.md",
        "formal/README.md",
    ),
    "release_artifacts": (
        "src/rpr/release_audit.py",
        "src/rpr/rc_execution.py",
        "tests/test_release_audit.py",
        "tests/test_release_prep_bundle.py",
        ".github/workflows/public-export-quality.yml",
    ),
    "customer_handover": (
        "docs/en/install-operations-recovery.md",
        "src/rpr/diagnostics.py",
        "src/rpr/customer_handover.py",
        "tests/test_customer_handover.py",
        ".github/workflows/public-export-quality.yml",
    ),
}


def build_delivery_acceptance_baseline(*, source_commit: str, residual_owner: str) -> DeliveryAcceptanceMatrix:
    """Return the conservative standalone product acceptance baseline."""
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
