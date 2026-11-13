"""Router objective RO6's successor mvp-0.49: one constant, its defaults, its gates, and its upgrade.

The upgrade is the chain's next journalled link: from mvp-0.48 (or mvp-0.9 onwards through the chain), one
transaction with the projection's activation under the tag and the config's publication last. Nothing already
recorded changes (RO6 adds no table and no column). ``learned_tail = false`` serves mvp-0.48. Fakes only; no model
call.
"""

from __future__ import annotations


import pytest

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    ROUTER_CALIBRATION_ALGORITHM_VERSION,
    ROUTER_LEARNED_TAIL_ALGORITHM_VERSION,
    ROUTER_LEARNED_TAIL_VERSIONS,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import RouterObjectiveConfig
from learnloop.params.parameter_registry import classify_config_path
from learnloop import router_objective_switches as SW
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
OLD = ROUTER_CALIBRATION_ALGORITHM_VERSION
RO6_KEYS = {"learned_tail": True, "residual_prior_sd": 0.01, "residual_weight_prior_sd": 1.0}


def test_the_successor_is_one_constant_after_ro5_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == "mvp-0.48"
    # The follow-up batch (mvp-0.50) and teacher TE2 (mvp-0.51) landed after it and keep it.
    assert TAG == "mvp-0.49" == SUCCESSOR_CHAIN[-11] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.59"
    assert ROUTER_LEARNED_TAIL_VERSIONS == frozenset({TAG, "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53", "mvp-0.54", "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58", "mvp-0.59"})


def test_the_seeds_are_labelled_and_validated():
    dumped = RouterObjectiveConfig().model_dump()
    for key, value in RO6_KEYS.items():
        assert dumped[key] == (pytest.approx(value) if isinstance(value, float) else value), key
    for bad in ({"residual_prior_sd": 0.0}, {"residual_weight_prior_sd": -1.0}):
        with pytest.raises(ValueError):
            RouterObjectiveConfig(**bad)


@pytest.mark.parametrize("path", [f"router_objective.{key}" for key in RO6_KEYS])
def test_each_new_key_is_classified(path):
    rule = classify_config_path(path)
    assert rule is not None and "mvp-0.49" in rule.rationale, path


def test_the_gate_reads_off_below_the_tag_switched_off_and_with_the_objective_off(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    assert not SW.learned_tail_on(load_vault(paths.root).config)
    set_algorithm_version(paths, TAG)
    assert SW.learned_tail_on(load_vault(paths.root).config)
    append_config_toml(paths.root, "[router_objective]\nlearned_tail = false\n")
    assert not SW.learned_tail_on(load_vault(paths.root).config)
    paths2 = create_basic_vault(tmp_path / "vault2")
    set_algorithm_version(paths2, TAG)
    append_config_toml(paths2.root, "[router_objective]\nenabled = false\n")
    assert not SW.learned_tail_on(load_vault(paths2.root).config)
