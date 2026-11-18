"""Data capture's successor mvp-0.44: one constant, its upgrade, the receipts' default, and the outcome version every
vault's rebuild derives (its kill switch went once every vault was past the tag).
"""

from __future__ import annotations


from learnloop.algorithm_versions import (
    DATA_CAPTURE_ALGORITHM_VERSION,
    LESSON_SUGGESTIONS_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import DataCaptureConfig
from learnloop.data_capture.gates import receipts_on
from learnloop.vault.loader import load_vault

from tests.helpers import set_algorithm_version
from tests.teacher_fakes import build_teacher_vault

TAG = DATA_CAPTURE_ALGORITHM_VERSION
OLD = LESSON_SUGGESTIONS_ALGORITHM_VERSION


def test_the_successor_is_one_constant_after_te1b_and_the_latest():
    position = SUCCESSOR_CHAIN.index(TAG)
    assert SUCCESSOR_CHAIN[position - 1:position + 1] == (OLD, TAG) == ("mvp-0.43", "mvp-0.44")


def test_the_receipts_are_on_by_default_and_their_gate_is_their_switch():
    assert DataCaptureConfig().receipts is True

    class Config:
        data_capture = DataCaptureConfig()

    assert receipts_on(Config)
    Config.data_capture = DataCaptureConfig(receipts=False)
    assert not receipts_on(Config)


def test_the_outcomes_cache_is_rebuilt_as_version_3_at_any_tag(tmp_path):
    """The one replayer derives every vault's outcomes as v3, a vault at an older tag's too."""

    from learnloop.db.stores.router import ROUTER_LOG_VERSION, insert_router_decision
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    direct, repository = build_teacher_vault(tmp_path / "vault", version=OLD, reserved=False)
    with repository.atomic(), repository.connection() as connection:
        insert_router_decision(connection, {
            "id": "d1", "receipt_key": "plan_block:b1", "decision_kind": "plan_block", "surface": "daily_plan", "mode": "mixture",
            "policy": "staged_v1", "algorithm_version": OLD, "log_version": ROUTER_LOG_VERSION, "snapshot_hash": "h",
            "candidates_json": "[]", "exclusions_json": "{}", "candidate_count": 0, "chosen_ref": "stop_for_today",
            "propensity": 1.0, "propensity_kind": "deterministic", "learner_pick": 0, "detail_json": "{}",
            "created_at": "2026-11-01T00:00:00Z",
        })

    def versions():
        rebuild_all_derived_state(load_vault(direct.root), repository)
        with repository.connection() as connection:
            return {row[0] for row in connection.execute("SELECT outcome_version FROM router_outcomes")}

    assert versions() == {"router_outcomes_v3"}
    set_algorithm_version(direct, TAG)
    assert versions() == {"router_outcomes_v3"}

