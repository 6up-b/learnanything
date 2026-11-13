"""Teacher TE3a's AD successor (mvp-0.52; built as mvp-0.50, renumbered at landing after the router follow-up batch's
mvp-0.50 and TE2's mvp-0.51): one constant, its defaults, its gate, and its upgrade.

The upgrade is the chain's next journalled link: from TE2's mvp-0.51 (or mvp-0.9 onwards through the chain), one
transaction with the projection's activation under the tag and the config's publication last. Nothing already
recorded changes (migration 249 is the vault's; the lesson receipts already exist). ``lesson_opportunities = false``
serves mvp-0.51. Fakes only; no model call.
"""

from __future__ import annotations


from learnloop.adaptive_difficulty.successor import LESSON_SWITCH, lesson_opportunities_on, settings
from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    LESSON_OPPORTUNITY_ALGORITHM_VERSION,
    LESSON_OPPORTUNITY_VERSIONS,
    SUCCESSOR_CHAIN,
    TEACHER_PROBES_ALGORITHM_VERSION,
)
from learnloop.config.schema import AdaptiveDifficultyConfig
from learnloop.params.parameter_registry import classify_config_path
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = LESSON_OPPORTUNITY_ALGORITHM_VERSION
OLD = TEACHER_PROBES_ALGORITHM_VERSION
TE3A_KEYS = {"lesson_opportunities": True}


def test_the_successor_is_one_constant_after_te2_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == "mvp-0.51"
    # Teacher TE3b's router successor (mvp-0.53) landed after it and keeps it.
    assert TAG == "mvp-0.52" == SUCCESSOR_CHAIN[-8] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.59"
    assert LESSON_OPPORTUNITY_VERSIONS == frozenset({TAG, "mvp-0.53", "mvp-0.54", "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58", "mvp-0.59"})


def test_the_switch_defaults_on_and_is_classified():
    section = AdaptiveDifficultyConfig()
    for key, value in TE3A_KEYS.items():
        assert getattr(section, key) == value
    rule = classify_config_path(f"adaptive_difficulty.{LESSON_SWITCH}")
    assert rule is not None and "kill switch" in rule.rationale and "TE3a" in rule.rationale


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
