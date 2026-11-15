"""The robust completion gate fixes in mvp-0.59 (refactor bug ledger D-39; docs/reviews/refactor-k9.0b.md).

Two faults made every unstable planted episode end ``couldnt_reliably_distinguish`` after two answers: the gate
ended the episode on a fragile *pick* although the robust stop rule said the next probe pays, and the robust
selector took a card's second item (an identical ensemble) as its winner's runner-up, so the winner's advantage
was exactly zero. Both are behind ``probe.episode.robust_gate_fixes`` at mvp-0.59; off, or at mvp-0.58, the gate
and the selector are the predecessor's exactly. Fakes and plain values only; no model call.
"""

from __future__ import annotations

from learnloop.algorithm_versions import (
    FACET_BELIEF_FIX_ALGORITHM_VERSION,
    FIGURE_WAIT_ALGORITHM_VERSION,
    ROBUST_GATE_FIX_VERSIONS,
)
from learnloop.config.kill_switches import TAGGED_SWITCHES
from learnloop.config.schema import LearnLoopConfig, ProbeEpisodeConfig
from learnloop.diagnosis.probe_robust import robust_gate_fixes_on
from learnloop.params.parameter_registry import classify_config_path

TAG = FACET_BELIEF_FIX_ALGORITHM_VERSION
OLD = FIGURE_WAIT_ALGORITHM_VERSION
SWITCH = "probe.episode.robust_gate_fixes"


def _config(version: str, *, switch: bool = True) -> LearnLoopConfig:
    config = LearnLoopConfig()
    config.algorithms.algorithm_version = version
    config.probe.episode.robust_gate_fixes = switch
    return config


def test_the_fixes_ride_on_mvp_0_59_behind_their_own_switch():
    assert TAG == "mvp-0.59" and OLD == "mvp-0.58"
    assert TAG in ROBUST_GATE_FIX_VERSIONS and OLD not in ROBUST_GATE_FIX_VERSIONS
    assert ProbeEpisodeConfig().robust_gate_fixes is True
    assert robust_gate_fixes_on(_config(TAG)) is True
    assert robust_gate_fixes_on(_config(TAG, switch=False)) is False
    assert robust_gate_fixes_on(_config(OLD)) is False
    assert any(row.path == SWITCH and row.tag == TAG and row.default is True for row in TAGGED_SWITCHES)
    rule = classify_config_path(SWITCH)
    assert rule is not None and rule.kind == "structural" and "robust completion gate" in rule.rationale
