"""Slip or gap's successor (mvp-0.57, after the placement hole's mvp-0.56): one constant, its defaults, its gates, its
prefetch key, its generator payload and its upgrade (docs/specs/spec_slip_vs_gap_v1.md §7).

The upgrade is the chain's next journalled link (a projection activation; nothing recorded changes, no migration).
``[router_objective] miss_cause_sensor = false`` serves mvp-0.56 exactly; ``miss_cause_in_value = false`` keeps the
sensor and mvp-0.56's values. Built on instruct/handoff as mvp-0.57: the placement fix's mvp-0.56 landed before it and
became its predecessor at the landing. Fakes only; no model call.
"""

from __future__ import annotations


from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    SLIP_GAP_ALGORITHM_VERSION,
    SLIP_GAP_VERSIONS,
    SUCCESSOR_CHAIN,
    UNEVIDENCED_RETURN_ALGORITHM_VERSION,
)
from learnloop.config.schema import RouterObjectiveConfig
from learnloop.daily_plan.objective_chooser import objective_settings
from learnloop.params.parameter_registry import classify_config_path
from learnloop.router_objective_switches import (
    COMMON_DRAW_OBJECTIVE_KEYS,
    SEED_NEUTRAL_SWITCHES,
    followup_generator_switches,
    slip_gap_tag,
)
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = SLIP_GAP_ALGORITHM_VERSION
OLD = UNEVIDENCED_RETURN_ALGORITHM_VERSION
#: Slip or gap's keys and their defaults, inert below the tag.
SG_KEYS = {"miss_cause_sensor": True, "miss_cause_in_value": True}


def test_the_successor_is_one_constant_after_the_placement_hole_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == "mvp-0.56"
    # The figure wait estimate's successor (mvp-0.58) follows it and keeps it.
    assert TAG == "mvp-0.57" == SUCCESSOR_CHAIN[-3] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.59"
    assert SLIP_GAP_VERSIONS == frozenset({TAG, "mvp-0.58", "mvp-0.59"})


def test_the_switches_default_on_and_are_classified():
    section = RouterObjectiveConfig()
    assert section.miss_cause_sensor is True and section.miss_cause_in_value is True
    for key, stage in (("miss_cause_sensor", "SG1"), ("miss_cause_in_value", "SG2")):
        rule = classify_config_path(f"router_objective.{key}")
        assert rule is not None and "kill switch" in rule.rationale and stage in rule.rationale


def test_the_gates_read_off_below_the_tag(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    assert not slip_gap_tag(load_vault(paths.root).config)
    set_algorithm_version(paths, TAG)
    assert slip_gap_tag(load_vault(paths.root).config)


def test_the_prefetch_key_names_both_switches_at_the_tag_and_keeps_its_bytes_below(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    below = objective_settings(load_vault(paths.root).config)
    assert not set(SG_KEYS) & set(below)
    set_algorithm_version(paths, TAG)
    on = objective_settings(load_vault(paths.root).config)
    assert {key: on[key] for key in SG_KEYS} == SG_KEYS
    assert {k: v for k, v in on.items() if k not in SG_KEYS} == below
    off = create_basic_vault(tmp_path / "off")
    set_algorithm_version(off, TAG)
    append_config_toml(off.root, "[router_objective]\nmiss_cause_in_value = false\n")
    flipped = objective_settings(load_vault(off.root).config)
    assert flipped["miss_cause_in_value"] is False and flipped != on
    # Never in the seed (common random numbers across the switches), never a speed switch.
    assert set(COMMON_DRAW_OBJECTIVE_KEYS) == set(SG_KEYS) and not set(SG_KEYS) & set(SEED_NEUTRAL_SWITCHES)


def test_sg2_is_in_ro6s_generator_payload_at_the_tag_and_sg1_is_not(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    below = followup_generator_switches(load_vault(paths.root).config)
    assert below is not None and "miss_cause_in_value" not in below and "miss_cause_sensor" not in below
    set_algorithm_version(paths, TAG)
    on = followup_generator_switches(load_vault(paths.root).config)
    assert on == {**below, "miss_cause_in_value": True}
    append_config_toml(paths.root, "[router_objective]\nmiss_cause_in_value = false\n")
    assert followup_generator_switches(load_vault(paths.root).config)["miss_cause_in_value"] is False
