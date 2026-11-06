"""Teacher TE3a's AD successor (mvp-0.50 on its branch): one constant, its defaults, its gate, and its upgrade.

The upgrade is the chain's next journalled link: from RO6's mvp-0.49 (or mvp-0.9 onwards through the chain), one
transaction with the projection's activation under the tag and the config's publication last. Nothing already
recorded changes (migration 248 is the vault's; the lesson receipts already exist). ``lesson_opportunities = false``
serves mvp-0.49. Fakes only; no model call.
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
    ROUTER_LEARNED_TAIL_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import AdaptiveDifficultyConfig, LearnLoopConfig
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, default_config_text, defaults_fingerprint_for_version
from learnloop.lesson_opportunity_upgrade import PREDECESSOR, upgrade_to_lesson_opportunity
from learnloop.params.parameter_registry import classify_config_path
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = LESSON_OPPORTUNITY_ALGORITHM_VERSION
OLD = ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
TE3A_KEYS = {"lesson_opportunities": True}


def test_the_successor_is_one_constant_after_ro6_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == PREDECESSOR == "mvp-0.49"
    assert TAG == "mvp-0.50" == SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION
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
    # mvp-0.49's value at this branch's base (5565bede25), frozen here: dropping TE3a's key reproduces it.
    dumped = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD))).model_dump(
        mode="json", exclude_none=False)
    for key in TE3A_KEYS:
        dumped["adaptive_difficulty"].pop(key)
    digest = hashlib.sha256(json.dumps(dumped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == "cb3a4f907f667d77deb1b53eb92c2e7b57f836443f7058de2a5a6e2b431e2e48"
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
    # It hands an earlier link's journal to RO6's completion, which hands it on in turn.
    assert "learnloop.router_learned_tail_upgrade import complete_interrupted_activation" in inspect.getsource(
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
