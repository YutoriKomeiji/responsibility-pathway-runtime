# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT

import pytest

from rpr.launch_claims import LaunchClaim, build_launch_claim_registry


def test_supported_claim_requires_release_evidence() -> None:
    with pytest.raises(ValueError, match="require evidence"):
        build_launch_claim_registry((LaunchClaim("readback", "External effects are read back.", "supported"),))


def test_proposed_claim_cannot_borrow_evidence() -> None:
    with pytest.raises(ValueError, match="cannot carry"):
        build_launch_claim_registry(
            (LaunchClaim("production", "Production ready.", "proposed", ("a" * 64,)),)
        )


def test_registry_is_order_independent() -> None:
    first = LaunchClaim("a", "Authenticated principal boundary.", "supported", ("1" * 64,))
    second = LaunchClaim("b", "Universal sandbox.", "blocked", limitation_refs=("known-limitations",))
    assert build_launch_claim_registry((first, second))["registry_sha256"] == build_launch_claim_registry(
        (second, first)
    )["registry_sha256"]


def test_duplicate_claim_id_is_rejected() -> None:
    claim = LaunchClaim("same", "A claim.", "retired")
    with pytest.raises(ValueError, match="duplicate"):
        build_launch_claim_registry((claim, claim))
