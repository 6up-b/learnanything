"""The router objective's follow-up batch's successor mvp-0.50: one constant, its defaults, its gates, its upgrade.

The upgrade is the chain's next journalled link: from mvp-0.49 (or mvp-0.9 onwards through the chain), one
transaction with the projection's activation under the tag and the config's publication last. Nothing already
recorded changes (the batch adds no table and no column). Every part's switch off serves mvp-0.49. Fakes only; no
model call.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import tomllib

import pytest

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    ROUTER_FOLLOWUPS_ALGORITHM_VERSION,
    ROUTER_FOLLOWUPS_VERSIONS,
    ROUTER_LEARNED_TAIL_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import LearnLoopConfig, RouterObjectiveConfig
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, default_config_text, defaults_fingerprint_for_version
from learnloop.params.parameter_registry import classify_config_path
from learnloop import router_objective_switches as SW
from learnloop.router_followups_upgrade import PREDECESSOR, upgrade_to_router_followups
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = ROUTER_FOLLOWUPS_ALGORITHM_VERSION
OLD = ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
#: The batch's [router_objective] keys and their defaults (each part's switch).
FOLLOWUP_KEYS: dict[str, object] = {
    "combiner_trace_outcomes": True,
    "merged_sessions": True,
    "consistent_review_draw": True,
    "monotone_combiner": True,
    "ad_predictive_link": True,
    "carried_in_prefetch": True,
    "scope_extension": True,
    # router speed, item 1 (its Codex review F1): a kill switch at the same tag
    "held_ad_link": True,
}


def test_the_successor_is_one_constant_after_ro6_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == PREDECESSOR == "mvp-0.49"
    # Teacher TE2 (mvp-0.51) landed after it and keeps it.
    assert TAG == "mvp-0.50" == SUCCESSOR_CHAIN[-2] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.51"
    assert ROUTER_FOLLOWUPS_VERSIONS == frozenset({TAG, "mvp-0.51"})


def test_the_switches_default_on():
    dumped = RouterObjectiveConfig().model_dump()
    for key, value in FOLLOWUP_KEYS.items():
        assert dumped[key] == value, key


def test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys():
    for version, fingerprint in DEFAULTS_SNAPSHOT_BY_ALGORITHM.items():
        assert fingerprint == defaults_fingerprint_for_version(version), version
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[OLD]
    # mvp-0.49's value on main (5565bede25, merged at the landing: its own mvp-0.49 snapshot, which TE2-log's
    # teacher.episode_log moved), frozen here: dropping the batch's keys reproduces it.
    dumped = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD))).model_dump(
        mode="json", exclude_none=False)
    for key in FOLLOWUP_KEYS:
        dumped["router_objective"].pop(key)
    from tests.test_teacher_te2_successor import drop_te2_keys

    drop_te2_keys(dumped)  # teacher TE2's keys (mvp-0.51; tests/test_teacher_te2_successor.py), inert below it
    digest = hashlib.sha256(json.dumps(dumped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == "cb3a4f907f667d77deb1b53eb92c2e7b57f836443f7058de2a5a6e2b431e2e48"


@pytest.mark.parametrize("path", [f"router_objective.{key}" for key in FOLLOWUP_KEYS])
def test_each_new_key_is_classified(path):
    rule = classify_config_path(path)
    assert rule is not None and "mvp-0.50" in rule.rationale, path


@pytest.mark.parametrize("key", list(FOLLOWUP_KEYS))
def test_each_part_reads_off_below_the_tag_switched_off_and_with_the_objective_off(tmp_path, key):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    assert not SW.followup_on(load_vault(paths.root).config, key)
    set_algorithm_version(paths, TAG)
    assert SW.followup_on(load_vault(paths.root).config, key)
    append_config_toml(paths.root, f"[router_objective]\n{key} = false\n")
    assert not SW.followup_on(load_vault(paths.root).config, key)
    paths2 = create_basic_vault(tmp_path / "vault2")
    set_algorithm_version(paths2, TAG)
    append_config_toml(paths2.root, "[router_objective]\nenabled = false\n")
    assert not SW.followup_on(load_vault(paths2.root).config, key)


def test_the_openers_install_this_links_completion():
    from learnloop.cli import runtime
    from learnloop_sidecar import context
    from learnloop import router_followups_upgrade, teacher_probes_upgrade

    # Teacher TE2's link (mvp-0.51) is the chain's latest; it hands earlier journals to this link.
    assert "learnloop.teacher_probes_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.teacher_probes_upgrade" in inspect.getsource(context._complete_interrupted_activation)
    assert "learnloop.router_followups_upgrade import complete_interrupted_activation" in inspect.getsource(
        teacher_probes_upgrade)
    # It hands an earlier link's journal to RO6's completion, which hands it on in turn.
    assert "learnloop.router_learned_tail_upgrade import complete_interrupted_activation" in inspect.getsource(
        router_followups_upgrade)


def test_the_upgrade_publishes_the_tag_and_completes_once(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = upgrade_to_router_followups(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (OLD, TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    again = upgrade_to_router_followups(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_chains_from_an_older_link(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.47")
    result = upgrade_to_router_followups(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == ("mvp-0.47", TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG


def test_the_upgrade_refuses_anything_older_than_the_chain(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    result = upgrade_to_router_followups(paths.root)
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
