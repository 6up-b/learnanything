"""Router objective RO5's successor mvp-0.48: one constant, its defaults, its gates, and its upgrade.

The upgrade is the chain's next journalled link: from mvp-0.47 (or mvp-0.9 onwards through the chain), one
transaction with the projection's activation under the tag and the config's publication last. Nothing already
recorded changes. Each arm is a declared price for information, off at zero. Fakes only; no model call.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import tomllib

import pytest

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    ROUTER_CALIBRATION_ALGORITHM_VERSION,
    ROUTER_CALIBRATION_VERSIONS,
    ROUTER_OBJECTIVE_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import LearnLoopConfig, RouterObjectiveConfig
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, default_config_text, defaults_fingerprint_for_version
from learnloop.params.parameter_registry import classify_config_path
from learnloop import router_objective_switches as SW
from learnloop.router_calibration_upgrade import PREDECESSOR, upgrade_to_router_calibration
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = ROUTER_CALIBRATION_ALGORITHM_VERSION
OLD = ROUTER_OBJECTIVE_ALGORITHM_VERSION
RO5_KEYS = {
    "stop_coin": 0.05, "check_rate": "embedded", "embedded_checks_per_day": 1, "pick_open_share": 0.1,
    "kappa_prior_log_sd": 0.7, "return_slope_prior_sd": 0.5, "goal_transfer_prior_sd": 1.0, "fitted_models": True,
}


def test_the_successor_is_one_constant_after_ro4_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == PREDECESSOR == "mvp-0.47"
    # Router objective RO6 (mvp-0.49) landed after it and keeps it.
    assert TAG == "mvp-0.48" == SUCCESSOR_CHAIN[-3] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.50"
    assert ROUTER_CALIBRATION_VERSIONS == frozenset({TAG, "mvp-0.49", "mvp-0.50"})


def test_the_seeds_are_the_specs_and_validated():
    dumped = RouterObjectiveConfig().model_dump()
    for key, value in RO5_KEYS.items():
        assert dumped[key] == pytest.approx(value) if isinstance(value, float) else dumped[key] == value, key
    assert RouterObjectiveConfig(check_rate=0.25).check_rate == 0.25
    assert RouterObjectiveConfig(check_rate="off").check_rate == "off"
    with pytest.raises(ValueError):
        RouterObjectiveConfig(check_rate=1.5)
    with pytest.raises(ValueError):
        RouterObjectiveConfig(check_rate="sometimes")
    with pytest.raises(ValueError):
        RouterObjectiveConfig(stop_coin=0.6)


def test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys():
    for version, fingerprint in DEFAULTS_SNAPSHOT_BY_ALGORITHM.items():
        assert fingerprint == defaults_fingerprint_for_version(version), version
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[OLD]
    # mvp-0.47's value at this branch's base (59a0de9832), frozen here: dropping RO5's keys reproduces it.
    dumped = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD))).model_dump(
        mode="json", exclude_none=False)
    # Router objective RO6's keys (mvp-0.49; tests/test_ro6_successor.py) are in every snapshot, inert below it.
    from tests.test_ro6_successor import RO6_KEYS

    for key in (*RO5_KEYS, *RO6_KEYS):
        dumped["router_objective"].pop(key)
    assert dumped["teacher"].pop("episode_log") is True  # teacher TE2-log's switch (no successor, every snapshot)
    assert dumped["adaptive_difficulty"].pop("lesson_opportunities") is True  # teacher TE3a's switch, inert below mvp-0.50
    digest =hashlib.sha256(json.dumps(dumped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == "fa0065c811aa4288783fb0f01567c35eab688a18d941122918499efb8305bfa2"


@pytest.mark.parametrize("path", [f"router_objective.{key}" for key in RO5_KEYS])
def test_each_new_key_is_classified(path):
    rule = classify_config_path(path)
    assert rule is not None and "mvp-0.48" in rule.rationale, path


def test_the_gates_read_off_below_the_tag_and_at_zero(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    config = load_vault(paths.root).config
    assert SW.stop_coin_rate(config) == 0.0 and SW.check_mode(config) == (SW.CHECKS_OFF, 0.0)
    assert SW.pick_open_share(config) == 0.0 and not SW.fitted_models_on(config)
    set_algorithm_version(paths, TAG)
    config = load_vault(paths.root).config
    assert SW.stop_coin_rate(config) == pytest.approx(0.05)
    assert SW.check_mode(config) == (SW.CHECKS_EMBEDDED, 1.0)
    assert SW.pick_open_share(config) == pytest.approx(0.1) and SW.fitted_models_on(config)
    append_config_toml(paths.root, "[router_objective]\nstop_coin = 0.0\ncheck_rate = 0.2\npick_open_share = 0.0\n"
                                   "fitted_models = false\n")
    config = load_vault(paths.root).config
    assert SW.stop_coin_rate(config) == 0.0 and SW.check_mode(config) == (SW.CHECKS_RATE, 0.2)
    assert SW.pick_open_share(config) == 0.0 and not SW.fitted_models_on(config)
    paths2 = create_basic_vault(tmp_path / "vault2")
    set_algorithm_version(paths2, TAG)
    append_config_toml(paths2.root, "[router_objective]\nenabled = false\n")
    config = load_vault(paths2.root).config
    # The coin and the checks live in the objective's frame; the open picks only need the tag.
    assert SW.stop_coin_rate(config) == 0.0 and SW.check_mode(config) == (SW.CHECKS_OFF, 0.0)
    assert SW.pick_open_share(config) == pytest.approx(0.1)


def test_the_openers_install_this_links_completion():
    from learnloop.cli import runtime
    from learnloop_sidecar import context

    # RO6's link (mvp-0.49) is the chain's latest: it hands this link's journal to this link's completion.
    from learnloop import router_learned_tail_upgrade

    assert "learnloop.lesson_opportunity_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.lesson_opportunity_upgrade" in inspect.getsource(context._complete_interrupted_activation)
    assert "learnloop.router_calibration_upgrade import complete_interrupted_activation" in inspect.getsource(
        router_learned_tail_upgrade)


def test_the_upgrade_publishes_the_tag_and_completes_once(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = upgrade_to_router_calibration(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (OLD, TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    again = upgrade_to_router_calibration(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_chains_from_an_older_link(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.46")
    result = upgrade_to_router_calibration(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == ("mvp-0.46", TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG


def test_the_upgrade_refuses_anything_older_than_the_chain(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    result = upgrade_to_router_calibration(paths.root)
    assert not result.upgraded and "cannot upgrade from 'mvp-0.8'" in result.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
