"""Router objective RO6's successor mvp-0.49: one constant, its defaults, its gates, and its upgrade.

The upgrade is the chain's next journalled link: from mvp-0.48 (or mvp-0.9 onwards through the chain), one
transaction with the projection's activation under the tag and the config's publication last. Nothing already
recorded changes (RO6 adds no table and no column). ``learned_tail = false`` serves mvp-0.48. Fakes only; no model
call.
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
    ROUTER_LEARNED_TAIL_ALGORITHM_VERSION,
    ROUTER_LEARNED_TAIL_VERSIONS,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import LearnLoopConfig, RouterObjectiveConfig
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, default_config_text, defaults_fingerprint_for_version
from learnloop.params.parameter_registry import classify_config_path
from learnloop import router_objective_switches as SW
from learnloop.router_learned_tail_upgrade import PREDECESSOR, upgrade_to_router_learned_tail
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
OLD = ROUTER_CALIBRATION_ALGORITHM_VERSION
RO6_KEYS = {"learned_tail": True, "residual_prior_sd": 0.01, "residual_weight_prior_sd": 1.0}


def test_the_successor_is_one_constant_after_ro5_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == PREDECESSOR == "mvp-0.48"
    # The follow-up batch (mvp-0.50) and teacher TE2 (mvp-0.51) landed after it and keep it.
    assert TAG == "mvp-0.49" == SUCCESSOR_CHAIN[-5] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.53"
    assert ROUTER_LEARNED_TAIL_VERSIONS == frozenset({TAG, "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53"})


def test_the_seeds_are_labelled_and_validated():
    dumped = RouterObjectiveConfig().model_dump()
    for key, value in RO6_KEYS.items():
        assert dumped[key] == (pytest.approx(value) if isinstance(value, float) else value), key
    for bad in ({"residual_prior_sd": 0.0}, {"residual_weight_prior_sd": -1.0}):
        with pytest.raises(ValueError):
            RouterObjectiveConfig(**bad)


def test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys():
    for version, fingerprint in DEFAULTS_SNAPSHOT_BY_ALGORITHM.items():
        assert fingerprint == defaults_fingerprint_for_version(version), version
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[OLD]
    # mvp-0.48's value at this branch's base (5f02be6eb2), frozen here: dropping RO6's keys reproduces it.
    dumped = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD))).model_dump(
        mode="json", exclude_none=False)
    # The follow-up batch's keys (mvp-0.50; tests/test_rofu_successor.py) are in every snapshot, inert below it.
    from tests.test_rofu_successor import FOLLOWUP_KEYS

    for key in (*RO6_KEYS, *FOLLOWUP_KEYS):
        dumped["router_objective"].pop(key)
    assert dumped["teacher"].pop("episode_log") is True  # teacher TE2-log's switch (no successor, every snapshot)
    from tests.test_teacher_te2_successor import drop_te2_keys

    drop_te2_keys(dumped)  # teacher TE2's keys (mvp-0.51; tests/test_teacher_te2_successor.py), inert below it
    from tests.test_te3a_successor import drop_te3a_keys

    drop_te3a_keys(dumped)  # teacher TE3a's key (mvp-0.52; tests/test_te3a_successor.py), inert below it
    digest =hashlib.sha256(json.dumps(dumped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == "dc39796ffa66ee54c1877cba358f697f24fe449020fba6b2e3a1f14ec521a2b1"


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


def test_the_openers_install_this_links_completion():
    from learnloop.cli import runtime
    from learnloop_sidecar import context
    from learnloop import router_learned_tail_upgrade

    # Teacher TE2's link (mvp-0.51) is the chain's latest; through the follow-up batch's (mvp-0.50) it hands earlier
    # journals to this link.
    assert "learnloop.phone_probes_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.phone_probes_upgrade" in inspect.getsource(context._complete_interrupted_activation)
    # It hands an earlier link's journal to RO5's completion, which hands it on in turn.
    assert "learnloop.router_calibration_upgrade import complete_interrupted_activation" in inspect.getsource(
        router_learned_tail_upgrade)


def test_the_upgrade_publishes_the_tag_and_completes_once(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = upgrade_to_router_learned_tail(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (OLD, TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    again = upgrade_to_router_learned_tail(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_chains_from_an_older_link(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.46")
    result = upgrade_to_router_learned_tail(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == ("mvp-0.46", TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG


def test_the_upgrade_refuses_anything_older_than_the_chain(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    result = upgrade_to_router_learned_tail(paths.root)
    assert not result.upgraded and "cannot upgrade from 'mvp-0.8'" in result.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"


def test_the_cli_upgrade_reaches_the_tag_by_default(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli.app import app

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = CliRunner().invoke(app, ["upgrade", "--to", TAG, "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{OLD} -> {TAG}" in result.output
