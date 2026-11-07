"""Teacher TE3a's AD successor (mvp-0.52; built as mvp-0.50, renumbered at landing after the router follow-up batch's
mvp-0.50 and TE2's mvp-0.51): one constant, its defaults, its gate, and its upgrade.

The upgrade is the chain's next journalled link: from TE2's mvp-0.51 (or mvp-0.9 onwards through the chain), one
transaction with the projection's activation under the tag and the config's publication last. Nothing already
recorded changes (migration 249 is the vault's; the lesson receipts already exist). ``lesson_opportunities = false``
serves mvp-0.51. Fakes only; no model call.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import tomllib

from learnloop.adaptive_difficulty.successor import LESSON_SWITCH, lesson_opportunities_on, settings
from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    LESSON_OPPORTUNITY_ALGORITHM_VERSION,
    LESSON_OPPORTUNITY_VERSIONS,
    SUCCESSOR_CHAIN,
    TEACHER_PROBES_ALGORITHM_VERSION,
)
from learnloop.config.schema import AdaptiveDifficultyConfig, LearnLoopConfig
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, default_config_text, defaults_fingerprint_for_version
from learnloop.lesson_opportunity_upgrade import PREDECESSOR, upgrade_to_lesson_opportunity
from learnloop.params.parameter_registry import classify_config_path
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = LESSON_OPPORTUNITY_ALGORITHM_VERSION
OLD = TEACHER_PROBES_ALGORITHM_VERSION
TE3A_KEYS = {"lesson_opportunities": True}


def drop_te3a_keys(dumped: dict) -> dict:
    """An earlier successor's frozen defaults digest: TE3a's key (in every snapshot, inert below mvp-0.52) dropped."""

    for key, value in TE3A_KEYS.items():
        assert dumped["adaptive_difficulty"].pop(key) is value
    return dumped


def test_the_successor_is_one_constant_after_te2_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == PREDECESSOR == "mvp-0.51"
    assert TAG == "mvp-0.52" == SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION
    assert LESSON_OPPORTUNITY_VERSIONS == frozenset({TAG})


def test_the_switch_defaults_on_and_is_classified():
    section = AdaptiveDifficultyConfig()
    for key, value in TE3A_KEYS.items():
        assert getattr(section, key) == value
    rule = classify_config_path(f"adaptive_difficulty.{LESSON_SWITCH}")
    assert rule is not None and "kill switch" in rule.rationale and "TE3a" in rule.rationale


def test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_key():
    for version, fingerprint in DEFAULTS_SNAPSHOT_BY_ALGORITHM.items():
        assert fingerprint == defaults_fingerprint_for_version(version), version
    assert TAG in DEFAULTS_SNAPSHOT_BY_ALGORITHM
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[OLD]
    # mvp-0.51's value on main at TE3a's landing merge (23182034c6), frozen here: dropping TE3a's key reproduces it
    # (and router speed's [router_objective] held_ad_link, in every snapshot, which landed after it).
    dumped = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD))).model_dump(
        mode="json", exclude_none=False)
    for key in TE3A_KEYS:
        dumped["adaptive_difficulty"].pop(key)
    assert dumped["router_objective"].pop("held_ad_link") is True
    digest = hashlib.sha256(json.dumps(dumped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == "94291ed4789a10800d9b6174d87ae1ccf82a36e1d103d8c89fc98735e5d1d150"
    # The tag's own defaults differ from the predecessor's by the version label alone (the key is in both).
    at_tag = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(TAG))).model_dump(
        mode="json", exclude_none=False)
    before = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD))).model_dump(
        mode="json", exclude_none=False)
    assert at_tag["algorithms"].pop("algorithm_version") == TAG and before["algorithms"].pop("algorithm_version") == OLD
    assert at_tag == before


def test_the_gate_reads_off_below_the_tag_switched_off_and_with_ad_off(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    assert not lesson_opportunities_on(load_vault(paths.root).config)
    assert LESSON_SWITCH not in settings(load_vault(paths.root).config)
    set_algorithm_version(paths, TAG)
    assert lesson_opportunities_on(load_vault(paths.root).config)
    assert settings(load_vault(paths.root).config)[LESSON_SWITCH] is True
    append_config_toml(paths.root, "[adaptive_difficulty]\nlesson_opportunities = false\n")
    assert not lesson_opportunities_on(load_vault(paths.root).config)
    paths2 = create_basic_vault(tmp_path / "vault2")
    set_algorithm_version(paths2, TAG)
    append_config_toml(paths2.root, "[adaptive_difficulty]\nenabled = false\n")
    assert not lesson_opportunities_on(load_vault(paths2.root).config)


def test_the_openers_install_this_links_completion():
    from learnloop import lesson_opportunity_upgrade
    from learnloop.cli import runtime
    from learnloop_sidecar import context

    assert "learnloop.lesson_opportunity_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.lesson_opportunity_upgrade" in inspect.getsource(context._complete_interrupted_activation)
    # It hands an earlier link's journal to TE2's completion, which hands it on in turn.
    assert "learnloop.teacher_probes_upgrade import complete_interrupted_activation" in inspect.getsource(
        lesson_opportunity_upgrade)


def test_the_upgrade_publishes_the_tag_and_completes_once(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = upgrade_to_lesson_opportunity(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (OLD, TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    again = upgrade_to_lesson_opportunity(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_chains_from_an_older_link(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.47")
    result = upgrade_to_lesson_opportunity(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == ("mvp-0.47", TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG


def test_the_upgrade_refuses_anything_older_than_the_chain(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    result = upgrade_to_lesson_opportunity(paths.root)
    assert not result.upgraded and "cannot upgrade from 'mvp-0.8'" in result.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"


def test_the_cli_upgrade_reaches_the_tag_by_default_and_by_name(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli.app import app

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{OLD} -> {TAG}" in result.output
    named = create_basic_vault(tmp_path / "named")
    set_algorithm_version(named, OLD)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(named.root), "--to", TAG])
    assert result.exit_code == 0, result.output
    assert load_vault(named.root).config.algorithms.algorithm_version == TAG
