"""Calibration sessions (spec §5.9): batching, budget, cap lift, stop control."""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.calibration_sessions import (
    CalibrationSessionError,
    calibration_cap_lifted,
    calibration_session_progress,
    start_calibration_session,
    stop_calibration_session,
)
from learnloop.services.probe_families import builtin_family_templates
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, admit_probe_instrument_card, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
CLOCK = FrozenClock(NOW)


def _setup(tmp_path, *, trust_families: bool = True):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, items=(ITEM_ID,))
    if trust_families:
        for template in builtin_family_templates():
            repository.upsert_probe_family_template(
                family_id=template.id,
                version=template.version,
                status="trusted",
                template=template.as_dict(),
                schema_hash=template.schema_hash(),
                clock=CLOCK,
            )
    return vault_root, loaded, repository


def test_calibration_session_plans_episodes_and_reports_progress(tmp_path):
    _vault_root, loaded, repository = _setup(tmp_path)
    progress = start_calibration_session(
        loaded,
        repository,
        session_id="s1",
        learning_object_ids=[LO_ID],
        time_budget_minutes=15,
        clock=CLOCK,
    )
    assert progress["status"] == "active"
    assert progress["blocks_planned"] == 1
    assert progress["time_budget_minutes"] == 15
    assert progress["next_target"] is not None
    assert progress["next_target"]["learning_object_id"] == LO_ID

    # §5.9: the calibration session lifts only the per-session cap.
    assert calibration_cap_lifted(repository, "s1", clock=CLOCK)
    assert not calibration_cap_lifted(repository, "other-session", clock=CLOCK)

    # Only one active calibration session per client session.
    with pytest.raises(CalibrationSessionError):
        start_calibration_session(
            loaded, repository, session_id="s1", learning_object_ids=[LO_ID], clock=CLOCK
        )


def test_calibration_session_stop_and_budget_expiry(tmp_path):
    _vault_root, loaded, repository = _setup(tmp_path)
    progress = start_calibration_session(
        loaded,
        repository,
        session_id="s1",
        learning_object_ids=[LO_ID],
        time_budget_minutes=10,
        clock=CLOCK,
    )
    calibration_id = progress["calibration_session_id"]

    stop_calibration_session(repository, calibration_id, clock=CLOCK)
    stopped = calibration_session_progress(loaded, repository, calibration_id, clock=CLOCK)
    assert stopped["status"] == "stopped"
    assert not calibration_cap_lifted(repository, "s1", clock=CLOCK)

    # A second session on a new session id expires once past its budget.
    progress = start_calibration_session(
        loaded,
        repository,
        session_id="s2",
        learning_object_ids=[LO_ID],
        time_budget_minutes=10,
        clock=CLOCK,
    )
    later = FrozenClock(NOW + timedelta(minutes=11))
    assert not calibration_cap_lifted(repository, "s2", clock=later)
    expired = calibration_session_progress(
        loaded, repository, progress["calibration_session_id"], clock=later
    )
    assert expired["status"] == "expired"


def test_calibration_session_requires_scope(tmp_path):
    _vault_root, loaded, repository = _setup(tmp_path)
    with pytest.raises(CalibrationSessionError):
        start_calibration_session(
            loaded, repository, session_id="s1", learning_object_ids=["lo_missing"], clock=CLOCK
        )
