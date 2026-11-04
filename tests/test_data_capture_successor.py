"""Data capture's successor mvp-0.44: one constant, its upgrade, its defaults, and its kill switch.

Below the tag, or with ``data_capture.serving`` off, the desktop's serving is mvp-0.43's byte for byte: the plan's
blocks and the router's rows (receipts stay additive in their own tables).
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
import tomllib

import pytest

from learnloop.algorithm_versions import (
    DATA_CAPTURE_ALGORITHM_VERSION,
    DATA_CAPTURE_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    LESSON_SUGGESTIONS_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import DataCaptureConfig, LearnLoopConfig
from learnloop.config.template import (
    DEFAULTS_SNAPSHOT_BY_ALGORITHM,
    default_config_text,
    defaults_fingerprint_for_version,
)
from learnloop.data_capture.gates import receipts_on, serving_on
from learnloop.data_capture_upgrade import PREDECESSOR, upgrade_to_data_capture
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault, set_algorithm_version
from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import fake_runtime
from tests.teacher_fakes import build_teacher_vault

TAG = DATA_CAPTURE_ALGORITHM_VERSION
OLD = LESSON_SUGGESTIONS_ALGORITHM_VERSION
OFF = "[data_capture]\nserving = false\n"


def test_the_successor_is_one_constant_after_te1b_and_the_latest():
    position = SUCCESSOR_CHAIN.index(TAG)
    assert SUCCESSOR_CHAIN[position - 1:position + 1] == (OLD, TAG) == ("mvp-0.43", "mvp-0.44")
    assert TAG in DATA_CAPTURE_VERSIONS and OLD not in DATA_CAPTURE_VERSIONS
    assert PREDECESSOR == OLD


def test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys():
    for version, fingerprint in DEFAULTS_SNAPSHOT_BY_ALGORITHM.items():
        assert fingerprint == defaults_fingerprint_for_version(version), version
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[OLD]
    # main's value at 6cf7a91ba8, frozen here: dropping the two keys reproduces it.
    dumped = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD))).model_dump(mode="json", exclude_none=False)
    assert dumped.pop("data_capture") == {"receipts": True, "serving": True}
    # FG1's keys, in every snapshot and inert below its tag.
    dumped.pop("followup")
    dumped["ai"]["routing"].pop("followup_probe_author", None)
    dumped["ui"].pop("show_router_decisions")
    # RO1's keys (mvp-0.46; tests/test_ro1_successor.py), in every snapshot and inert below its tag.
    assert dumped.pop("router_objective") == {"available_at_reads": True, "self_report_not_validated": True}
    assert dumped["scheduler"]["surprise"].pop("remove_interval_factor") is True
    digest = hashlib.sha256(json.dumps(dumped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == "08840dbd600321a4a8d52fafb969bfacb6ace0e53d3166f5bdb12f81be6b34f3"


def test_the_switches_are_on_by_default_and_the_gate_reads_the_tag():
    assert DataCaptureConfig().serving is True and DataCaptureConfig().receipts is True

    class Config:
        data_capture = DataCaptureConfig()

        class algorithms:
            algorithm_version = TAG

    assert serving_on(Config) and receipts_on(Config)
    Config.algorithms.algorithm_version = OLD
    assert not serving_on(Config) and receipts_on(Config), "receipts act at every version"
    Config.algorithms.algorithm_version = TAG
    Config.data_capture = DataCaptureConfig(serving=False)
    assert not serving_on(Config)


def test_the_upgrade_from_te1b_and_through_the_chain_and_its_refusals(tmp_path):
    direct, _ = build_teacher_vault(tmp_path / "direct", version=OLD, reserved=False)
    result = upgrade_to_data_capture(direct.root)
    assert result.upgraded and (result.from_version, result.to_version) == (OLD, TAG)
    assert load_vault(direct.root).config.algorithms.algorithm_version == TAG
    # Twice is no second upgrade.
    assert not upgrade_to_data_capture(direct.root).upgraded

    chained, _ = build_teacher_vault(tmp_path / "chained", reserved=False)
    result = upgrade_to_data_capture(chained.root)
    assert result.upgraded and result.from_version == "mvp-0.41" and result.to_version == TAG

    paths = create_basic_vault(tmp_path / "old")
    set_algorithm_version(paths, "mvp-0.8")
    refused = upgrade_to_data_capture(paths.root)
    assert not refused.upgraded and refused.problems


def test_the_outcomes_cache_is_rebuilt_under_the_vaults_version(tmp_path):
    """The one replayer reads the vault's outcome version: v2 below the tag, v3 from it."""

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

    assert versions() == {"router_outcomes_v2"}
    upgrade_to_data_capture(direct.root)
    assert versions() == {"router_outcomes_v3"}


def test_the_openers_install_this_links_completion():
    from learnloop import data_capture_upgrade, lesson_suggestions_upgrade
    from learnloop.cli import runtime
    from learnloop_sidecar import context

    # The chain's latest completion hands an earlier link's journal on.
    assert "learnloop.interval_factor_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.interval_factor_upgrade" in inspect.getsource(context._complete_interrupted_activation)
    assert "learnloop.lesson_suggestions_upgrade import complete_interrupted_activation" in inspect.getsource(data_capture_upgrade)
    assert callable(lesson_suggestions_upgrade.complete_interrupted_activation)


#: What differs by construction between two runs: fresh ids, and the version label and its hashes.
_VOLATILE = {"id", "snapshot_hash", "algorithm_version", "seed", "card_hash", "created_at"}


def _canonical_rows(env):
    def scrub(value):
        if isinstance(value, dict):
            return {key: scrub(item) for key, item in value.items() if key not in _VOLATILE and "hash" not in key}
        if isinstance(value, list):
            return [scrub(item) for item in value]
        if isinstance(value, str):
            return re.sub(r"[0-9A-HJKMNP-TV-Z]{26}", "ULID", value)
        return value

    return [scrub({key: value for key, value in row.items()}) for row in rows(env)]


def _blocks(record):
    return [(block.lane, block.action, tuple(item.practice_item_id for item in block.items)) for block in record.blocks]


@pytest.mark.parametrize("variant", ["no_model", "stop_offered"])
def test_switched_off_at_the_tag_the_plan_and_its_rows_are_the_predecessors(tmp_path, variant):
    budget = 25.0 if variant == "no_model" else 6.0
    below = mixture_env(tmp_path / "below", fake_runtime(), version=OLD)
    off = mixture_env(tmp_path / "off", fake_runtime(), version=TAG, toml=OFF)
    for env in (below, off):
        build_plan(env, kind="normal", budget=budget, remembered=int(budget), minutes_source="chip")
        run(env)
    record_below, record_off = advance(below, serve=False)[0], advance(off, serve=False)[0]
    assert _blocks(record_below) == _blocks(record_off)
    assert _canonical_rows(below) == _canonical_rows(off)
    for env in (below, off):
        with env.repository.connection() as connection:
            assert connection.execute("SELECT COUNT(*) FROM decision_objectives").fetchone()[0] == 0
            assert connection.execute("SELECT COUNT(*) FROM commitments").fetchone()[0] == 0
