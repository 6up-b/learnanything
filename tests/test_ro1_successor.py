"""Router objective RO1's successor mvp-0.46: one constant, its defaults, its switches, and its upgrade.

The upgrade is the chain's next journalled link: from mvp-0.45 (or mvp-0.9 onwards through the chain), one
transaction with a whole-vault rebuild under the tag, so existing due dates move to
``interval_for_retention(S)`` when it activates. Fakes only; no model call.
"""

from __future__ import annotations


import pytest

from learnloop.algorithm_versions import (
    FOLLOWUP_SERVE_ALGORITHM_VERSION,
    INTERVAL_FACTOR_ALGORITHM_VERSION,
    INTERVAL_FACTOR_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import LearnLoopConfig
from learnloop.config.template import default_config_text
from learnloop.params.parameter_registry import classify_config_path
from learnloop.router_objective_switches import (
    available_at_reads_on,
    interval_factor_removed,
    self_report_not_validated_on,
)
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = INTERVAL_FACTOR_ALGORITHM_VERSION
OLD = FOLLOWUP_SERVE_ALGORITHM_VERSION
SWITCHES = ("scheduler.surprise.remove_interval_factor", "router_objective.available_at_reads",
            "router_objective.self_report_not_validated")


def test_the_successor_is_one_constant_after_fg1_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == "mvp-0.45"
    # Router objective RO4 (mvp-0.47), RO5 (mvp-0.48), RO6 (mvp-0.49), the follow-up batch (mvp-0.50) and teacher TE2
    # (mvp-0.51) landed after it and keep it.
    assert TAG == "mvp-0.46" == SUCCESSOR_CHAIN[-14] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.59"
    assert INTERVAL_FACTOR_VERSIONS == frozenset({TAG, "mvp-0.47", "mvp-0.48", "mvp-0.49", "mvp-0.50", "mvp-0.51", "mvp-0.52", "mvp-0.53", "mvp-0.54", "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58", "mvp-0.59"})


def test_the_factors_constants_stay_in_config():
    surprise = LearnLoopConfig().scheduler.surprise
    assert (surprise.alpha_interval, surprise.f_min, surprise.f_max) == (0.3, 0.5, 1.5)
    # The decision-only template stores none of them.
    assert "alpha_interval" not in default_config_text(TAG)


@pytest.mark.parametrize("path", SWITCHES)
def test_each_switch_is_classified_and_reads_off_or_below_the_tag(tmp_path, path):
    rule = classify_config_path(path)
    assert rule is not None and rule.kind == "structural" and "mvp-0.46" in rule.rationale
    gates = {"scheduler.surprise.remove_interval_factor": interval_factor_removed,
             "router_objective.available_at_reads": available_at_reads_on,
             "router_objective.self_report_not_validated": self_report_not_validated_on}
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    assert not any(gate(load_vault(paths.root).config) for gate in gates.values())
    set_algorithm_version(paths, TAG)
    assert all(gate(load_vault(paths.root).config) for gate in gates.values())
    section, _, key = path.rpartition(".")
    append_config_toml(paths.root, f"[{section}]\n{key} = false\n")
    config = load_vault(paths.root).config
    assert {name: gate(config) for name, gate in gates.items()} == {name: name != path for name in gates}
