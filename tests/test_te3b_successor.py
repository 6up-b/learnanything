"""Teacher TE3b's router successor (mvp-0.53, after TE3a's mvp-0.52): one constant, its defaults, its gate, and its
upgrade.

The upgrade is the chain's next journalled link: from TE3a's mvp-0.52 (or mvp-0.9 onwards through the chain), one
transaction with the projection's activation under the tag and the config's publication last. Nothing already
recorded changes (no migration). ``router.lesson_suggestions.in_objective = false`` serves mvp-0.52. Fakes only; no
model call.
"""

from __future__ import annotations

import inspect

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    LESSON_OFFERS_ALGORITHM_VERSION,
    LESSON_OFFERS_VERSIONS,
    LESSON_OPPORTUNITY_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import RouterLessonSuggestionsConfig
from learnloop.lesson_offers_upgrade import PREDECESSOR, upgrade_to_lesson_offers
from learnloop.params.parameter_registry import classify_config_path
from learnloop.router_objective_switches import lesson_offers_on, lesson_offers_tag
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = LESSON_OFFERS_ALGORITHM_VERSION
OLD = LESSON_OPPORTUNITY_ALGORITHM_VERSION
TE3B_KEYS = {"in_objective": True}


def test_the_successor_is_one_constant_after_te3a_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == PREDECESSOR == "mvp-0.52"
    # Phone V3's successor (mvp-0.54) follows it and keeps it.
    assert TAG == "mvp-0.53" == SUCCESSOR_CHAIN[-7] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.59"
    assert LESSON_OFFERS_VERSIONS == frozenset({TAG, "mvp-0.54", "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58", "mvp-0.59"})


def test_the_switch_defaults_on_and_is_classified():
    section = RouterLessonSuggestionsConfig()
    for key, value in TE3B_KEYS.items():
        assert getattr(section, key) == value
    rule = classify_config_path("router.lesson_suggestions.in_objective")
    assert rule is not None and "kill switch" in rule.rationale and "TE3b" in rule.rationale


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

    # Slip or gap's link (mvp-0.57) is the chain's latest since; its completion hands this link's journal on to the
    # placement hole's (mvp-0.56), IH5's (mvp-0.55), then phone V3's (mvp-0.54), which hands it here.
    assert "learnloop.facet_belief_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.facet_belief_upgrade" in inspect.getsource(context._complete_interrupted_activation)
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
