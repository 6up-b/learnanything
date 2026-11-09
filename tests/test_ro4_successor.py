"""Router objective RO4's successor mvp-0.47: one constant, its defaults, its switches, and its upgrade.

The upgrade is the chain's next journalled link: from mvp-0.46 (or mvp-0.9 onwards through the chain), one
transaction with the projection's activation under the tag and the config's publication last. Nothing already
recorded changes. Fakes only; no model call.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import tomllib

import pytest

from learnloop.algorithm_versions import (
    INTERVAL_FACTOR_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    ROUTER_OBJECTIVE_ALGORITHM_VERSION,
    ROUTER_OBJECTIVE_VERSIONS,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import LearnLoopConfig, RouterObjectiveConfig
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, default_config_text, defaults_fingerprint_for_version
from learnloop.params.parameter_registry import classify_config_path
from learnloop.router_objective_switches import objective_on, objective_scores_on, sensors_in_value_on
from learnloop.router_objective_upgrade import PREDECESSOR, upgrade_to_router_objective
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = ROUTER_OBJECTIVE_ALGORITHM_VERSION
OLD = INTERVAL_FACTOR_ALGORITHM_VERSION
RO4_KEYS = {
    "enabled": True, "sensors_in_value": True, "rollout_theta_draws": 8, "rollout_theta_draws_max": 64,
    "horizon_days": 90.0, "undated_use_density": 1.0 / 90.0, "dated_use_weight": 1.0, "session_gap_minutes": 60.0,
    "session_guard_minutes": None, "evaluation_window_days": 14, "llm_weight_prior": 0.8, "llm_min_share": 0.1,
    "numeric_min_share": 0.1, "delta_prior_sd": 0.01, "effect_slope_prior_mean": 0.2,
    "effect_slope_prior_variance": 0.04, "stop_accept_prior_a": 1.0, "stop_accept_prior_b": 1.0,
    "llm_card_token_budget": 48_000,
}


def test_the_successor_is_one_constant_after_ro1_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == PREDECESSOR == "mvp-0.46"
    # Router objective RO5 (mvp-0.48), RO6 (mvp-0.49), the follow-up batch (mvp-0.50) and teacher TE2 (mvp-0.51)
    # landed after it and keep it.
    assert TAG == "mvp-0.47" == SUCCESSOR_CHAIN[-9] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.56"
    assert ROUTER_OBJECTIVE_VERSIONS == frozenset({TAG, "mvp-0.48", "mvp-0.49", "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53", "mvp-0.54", "mvp-0.56"})


def test_the_seeds_are_the_specs_and_validated():
    dumped = RouterObjectiveConfig().model_dump()
    for key, value in RO4_KEYS.items():
        assert dumped[key] == pytest.approx(value) if isinstance(value, float) else dumped[key] == value, key
    with pytest.raises(ValueError):
        RouterObjectiveConfig(llm_min_share=0.45, numeric_min_share=0.55)
    with pytest.raises(ValueError):
        RouterObjectiveConfig(llm_weight_prior=0.05)
    with pytest.raises(ValueError):
        RouterObjectiveConfig(rollout_theta_draws=16, rollout_theta_draws_max=8)


def test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys():
    for version, fingerprint in DEFAULTS_SNAPSHOT_BY_ALGORITHM.items():
        assert fingerprint == defaults_fingerprint_for_version(version), version
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[OLD]
    # mvp-0.46's value at this branch's base (cf1019a3cf), frozen here: dropping RO4's keys reproduces it.
    dumped = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD))).model_dump(
        mode="json", exclude_none=False)
    section = dumped["router_objective"]
    # Router objective RO5's keys (mvp-0.48; tests/test_ro5_successor.py) are in every snapshot, inert below it.
    from tests.test_ro5_successor import RO5_KEYS
    from tests.test_ro6_successor import RO6_KEYS
    from tests.test_rofu_successor import FOLLOWUP_KEYS

    for key in (*RO4_KEYS, *RO5_KEYS, *RO6_KEYS, *FOLLOWUP_KEYS):
        section.pop(key)
    assert dumped["teacher"].pop("episode_log") is True  # teacher TE2-log's switch (no successor, every snapshot)
    from tests.test_teacher_te2_successor import drop_te2_keys

    drop_te2_keys(dumped)  # teacher TE2's keys (mvp-0.51; tests/test_teacher_te2_successor.py), inert below it
    from tests.test_te3a_successor import drop_te3a_keys

    drop_te3a_keys(dumped)  # teacher TE3a's key (mvp-0.52; tests/test_te3a_successor.py), inert below it
    from tests.test_te3b_successor import drop_te3b_keys

    drop_te3b_keys(dumped)  # teacher TE3b's key (mvp-0.53; tests/test_te3b_successor.py), inert below it
    from tests.test_placement_unevidenced_return import drop_unevidenced_return_keys

    drop_unevidenced_return_keys(dumped)  # mvp-0.56's switch (tests/test_placement_unevidenced_return.py), inert below it
    digest =hashlib.sha256(json.dumps(dumped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == "5c2ab89bfcb757cbc3038bd6c776bb968ff9688addd7becd4778e489ac461cb4"


@pytest.mark.parametrize("path", [f"router_objective.{key}" for key in RO4_KEYS])
def test_each_new_key_is_classified(path):
    rule = classify_config_path(path)
    assert rule is not None and "mvp-0.47" in rule.rationale, path


def test_the_gates_read_off_and_below_the_tag(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    config = load_vault(paths.root).config
    assert not objective_on(config) and not objective_scores_on(config) and not sensors_in_value_on(config)
    set_algorithm_version(paths, TAG)
    config = load_vault(paths.root).config
    assert objective_on(config) and objective_scores_on(config) and sensors_in_value_on(config)
    append_config_toml(paths.root, "[router_objective]\nreceipts = false\n")
    config = load_vault(paths.root).config
    assert objective_on(config) and not objective_scores_on(config)
    paths2 = create_basic_vault(tmp_path / "vault2")
    set_algorithm_version(paths2, TAG)
    append_config_toml(paths2.root, "[router_objective]\nenabled = false\n")
    config = load_vault(paths2.root).config
    assert not objective_on(config) and not objective_scores_on(config) and not sensors_in_value_on(config)


def test_the_openers_install_this_links_completion():
    from learnloop.cli import runtime
    from learnloop_sidecar import context

    # Teacher TE2's link (mvp-0.51) is the chain's latest; it hands earlier journals to the follow-up batch's,
    # RO6's and RO5's links, which hand this link's journal to this link's completion.
    from learnloop import router_calibration_upgrade

    assert "learnloop.unevidenced_return_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.unevidenced_return_upgrade" in inspect.getsource(context._complete_interrupted_activation)
    assert "learnloop.router_objective_upgrade import complete_interrupted_activation" in inspect.getsource(
        router_calibration_upgrade)


def test_the_upgrade_publishes_the_tag_and_completes_once(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = upgrade_to_router_objective(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (OLD, TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    again = upgrade_to_router_objective(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_refuses_anything_older_than_the_chain(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    result = upgrade_to_router_objective(paths.root)
    assert not result.upgraded and "cannot upgrade from 'mvp-0.8'" in result.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
