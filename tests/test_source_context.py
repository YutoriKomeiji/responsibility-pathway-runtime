# Copyright (c) 2026 Akihisa Ono
# SPDX-License-Identifier: MIT
from datetime import UTC, datetime, timedelta

import pytest

from rpr import SourceAuthority, SourceContext, SourceContextError


def context(**overrides):
    values = {
        "source_id": "canonical-runbook",
        "authority": SourceAuthority.CANONICAL,
        "provenance": "git:org/runbook@abc123",
        "observed_at": datetime(2026, 7, 30, 6, 0, tzinfo=UTC),
        "applicable_to": ("replace_text_file",),
        "content_digest": "sha256:abc",
    }
    values.update(overrides)
    return SourceContext(**values)


def test_valid_source_context_for_action():
    value = context()
    value.validate_for(
        "replace_text_file",
        maximum_age=timedelta(hours=2),
        now=datetime(2026, 7, 30, 7, 0, tzinfo=UTC),
    )
    assert value.to_evidence()["authority"] == "canonical"


def test_stale_source_context_is_rejected():
    with pytest.raises(SourceContextError, match="stale"):
        context().validate_for(
            "replace_text_file",
            maximum_age=timedelta(minutes=30),
            now=datetime(2026, 7, 30, 7, 0, tzinfo=UTC),
        )


def test_unverified_source_cannot_drive_authorized_action():
    with pytest.raises(SourceContextError, match="authority"):
        context(authority=SourceAuthority.UNVERIFIED).validate_for(
            "replace_text_file",
            maximum_age=timedelta(hours=2),
            now=datetime(2026, 7, 30, 7, 0, tzinfo=UTC),
        )


def test_non_applicable_source_is_rejected():
    with pytest.raises(SourceContextError, match="applicable"):
        context().validate_for(
            "send_message",
            maximum_age=timedelta(hours=2),
            now=datetime(2026, 7, 30, 7, 0, tzinfo=UTC),
        )


def test_naive_observation_time_is_rejected():
    with pytest.raises(SourceContextError, match="timezone-aware"):
        context(observed_at=datetime(2026, 7, 30, 6, 0))
