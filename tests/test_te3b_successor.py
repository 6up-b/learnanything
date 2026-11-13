"""Teacher TE3b's router successor (mvp-0.53, after TE3a's mvp-0.52): one constant, its defaults, its gate, and its
upgrade.

The upgrade is the chain's next journalled link: from TE3a's mvp-0.52 (or mvp-0.9 onwards through the chain), one
transaction with the projection's activation under the tag and the config's publication last. Nothing already
recorded changes (no migration). ``router.lesson_suggestions.in_objective = false`` serves mvp-0.52. Fakes only; no
model call.
"""

from __future__ import annotations


from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    LESSON_OFFERS_ALGORITHM_VERSION,
    LESSON_OFFERS_VERSIONS,
    LESSON_OPPORTUNITY_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import RouterLessonSuggestionsConfig
from learnloop.params.parameter_registry import classify_config_path
from learnloop.router_objective_switches import lesson_offers_on, lesson_offers_tag
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = LESSON_OFFERS_ALGORITHM_VERSION
OLD = LESSON_OPPORTUNITY_ALGORITHM_VERSION
TE3B_KEYS = {"in_objective": True}


def test_the_successor_is_one_constant_after_te3a_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == "mvp-0.52"
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
