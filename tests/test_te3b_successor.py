"""Teacher TE3b's router successor (mvp-0.53, after TE3a's mvp-0.52): one constant, its defaults, its gate, and its
upgrade.

The upgrade is the chain's next journalled link: from TE3a's mvp-0.52 (or mvp-0.9 onwards through the chain), one
transaction with the projection's activation under the tag and the config's publication last. Nothing already
recorded changes (no migration). ``router.lesson_suggestions.in_objective = false`` serves mvp-0.52. Fakes only; no
model call.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import tomllib

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    LESSON_OFFERS_ALGORITHM_VERSION,
    LESSON_OFFERS_VERSIONS,
    LESSON_OPPORTUNITY_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import LearnLoopConfig, RouterLessonSuggestionsConfig
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, default_config_text, defaults_fingerprint_for_version
from learnloop.lesson_offers_upgrade import PREDECESSOR, upgrade_to_lesson_offers
from learnloop.params.parameter_registry import classify_config_path
from learnloop.router_objective_switches import lesson_offers_on, lesson_offers_tag
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = LESSON_OFFERS_ALGORITHM_VERSION
OLD = LESSON_OPPORTUNITY_ALGORITHM_VERSION
TE3B_KEYS = {"in_objective": True}


def drop_te3b_keys(dumped: dict) -> dict:
    """An earlier successor's frozen defaults digest: TE3b's key (in every snapshot, inert below mvp-0.53) dropped."""

    for key, value in TE3B_KEYS.items():
        assert dumped["router"]["lesson_suggestions"].pop(key) is value
    return dumped


def test_the_successor_is_one_constant_after_te3a_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == PREDECESSOR == "mvp-0.52"
    # Phone V3's successor (mvp-0.54) follows it and keeps it.
    assert TAG == "mvp-0.53" == SUCCESSOR_CHAIN[-3] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.56"
    assert LESSON_OFFERS_VERSIONS == frozenset({TAG, "mvp-0.54", "mvp-0.56"})


def test_the_switch_defaults_on_and_is_classified():
    section = RouterLessonSuggestionsConfig()
    for key, value in TE3B_KEYS.items():
        assert getattr(section, key) == value
    rule = classify_config_path("router.lesson_suggestions.in_objective")
    assert rule is not None and "kill switch" in rule.rationale and "TE3b" in rule.rationale


def test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_key():
    for version, fingerprint in DEFAULTS_SNAPSHOT_BY_ALGORITHM.items():
        assert fingerprint == defaults_fingerprint_for_version(version), version
    assert TAG in DEFAULTS_SNAPSHOT_BY_ALGORITHM
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[OLD]
    # mvp-0.52's value on main at TE3b's base (8b0738499d), frozen here: dropping TE3b's key reproduces it (and the
    # router speed stage's [router_objective] held_ad_link, in every snapshot, which landed after the base).
    dumped = drop_te3b_keys(LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD))).model_dump(
        mode="json", exclude_none=False))
    assert dumped["router_objective"].pop("held_ad_link") is True
    from tests.test_rofu_successor import drop_rospeed2_keys

    drop_rospeed2_keys(dumped)  # router speed stage 2's switches (its Codex review F2), in every snapshot
    from tests.test_placement_unevidenced_return import drop_unevidenced_return_keys

    drop_unevidenced_return_keys(dumped)  # mvp-0.56's switch (tests/test_placement_unevidenced_return.py), inert below it
    canonical = json.dumps(dumped, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == MVP052_BASE_DIGEST
    # The tag's own defaults differ from the predecessor's by the version label alone (the key is in both).
    at_tag = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(TAG))).model_dump(
        mode="json", exclude_none=False)
    before = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD))).model_dump(
        mode="json", exclude_none=False)
    assert at_tag["algorithms"].pop("algorithm_version") == TAG and before["algorithms"].pop("algorithm_version") == OLD
    assert at_tag == before


#: mvp-0.52's recorded defaults snapshot on main 8b0738499d (the effective config dumped, sorted, compact).
MVP052_BASE_DIGEST = "66eb6308cbf49c476a693a51d1e1819d4883027f83b2552ed507675e10b103a3"


def test_the_gate_reads_off_below_the_tag_switched_off_and_with_suggestions_or_the_objective_off(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    assert not lesson_offers_tag(load_vault(paths.root).config)
    assert not lesson_offers_on(load_vault(paths.root).config)
    set_algorithm_version(paths, TAG)
    assert lesson_offers_on(load_vault(paths.root).config)
    for n, toml in enumerate((
            "[router.lesson_suggestions]\nin_objective = false\n",
            "[router.lesson_suggestions]\nenabled = false\n",
            "[router_objective]\nenabled = false\n",
            "[teacher]\nenabled = false\n")):
        other = create_basic_vault(tmp_path / f"off{n}")
        set_algorithm_version(other, TAG)
        append_config_toml(other.root, toml)
        assert lesson_offers_tag(load_vault(other.root).config)
        assert not lesson_offers_on(load_vault(other.root).config), toml


def test_the_openers_install_this_links_completion():
    from learnloop import lesson_offers_upgrade
    from learnloop.cli import runtime
    from learnloop_sidecar import context

    # The placement hole's link (mvp-0.56) is the chain's latest since; its completion hands this link's journal on to
    # phone V3's (mvp-0.54), which hands it here.
    assert "learnloop.unevidenced_return_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.unevidenced_return_upgrade" in inspect.getsource(context._complete_interrupted_activation)
    from learnloop import phone_probes_upgrade

    assert "learnloop.lesson_offers_upgrade import complete_interrupted_activation" in inspect.getsource(
        phone_probes_upgrade)
    # It hands an earlier link's journal to TE3a's completion, which hands it on in turn.
    assert "learnloop.lesson_opportunity_upgrade import complete_interrupted_activation" in inspect.getsource(
        lesson_offers_upgrade)


def test_the_upgrade_publishes_the_tag_and_completes_once(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = upgrade_to_lesson_offers(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (OLD, TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    again = upgrade_to_lesson_offers(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_chains_from_an_older_link(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.47")
    result = upgrade_to_lesson_offers(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == ("mvp-0.47", TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG


def test_the_upgrade_refuses_anything_older_than_the_chain(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    result = upgrade_to_lesson_offers(paths.root)
    assert not result.upgraded and "cannot upgrade from 'mvp-0.8'" in result.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"


def test_the_cli_upgrade_reaches_the_tag_by_default_and_by_name(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli.app import app

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    # The default target is the chain's latest (phone V3's mvp-0.54 since), through this link.
    assert f"{OLD} -> {LATEST_ALGORITHM_VERSION}" in result.output
    named = create_basic_vault(tmp_path / "named")
    set_algorithm_version(named, OLD)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(named.root), "--to", TAG])
    assert result.exit_code == 0, result.output
    assert load_vault(named.root).config.algorithms.algorithm_version == TAG
