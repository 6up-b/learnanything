"""Teacher TE2's successor (spec_teacher_v1 rev 5 §18.3, §24 row TE2): one constant, its defaults, its gate, its upgrade.

The upgrade is the chain's next journalled link: from mvp-0.50 (or mvp-0.9 onwards through the chain), one
transaction with the projection's activation under the tag and the config's publication last. Nothing already
recorded changes. TE2 serves wherever lessons are on (its switch went once every vault was past the tag). Fakes
only; no model call.
Built as mvp-0.50 on mvp-0.49 and renumbered at landing to mvp-0.51 on the router follow-up batch's mvp-0.50.
"""

from __future__ import annotations


import pytest

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    ROUTER_FOLLOWUPS_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    TEACHER_PROBES_ALGORITHM_VERSION,
)
from learnloop.config.schema import TeacherConfig, TeacherPlacementConfig
from learnloop.params.parameter_registry import classify_config_path
from learnloop.teacher import te2 as T2
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = TEACHER_PROBES_ALGORITHM_VERSION
OLD = ROUTER_FOLLOWUPS_ALGORITHM_VERSION


def test_the_successor_is_one_constant_after_the_router_followups_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == "mvp-0.50"
    # Teacher TE3a's AD successor (mvp-0.52) landed after it and keeps it.
    assert TAG == "mvp-0.51" == SUCCESSOR_CHAIN[-27] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.77"


def test_the_keep_bound_and_its_validation():
    config = TeacherConfig()
    assert config.placement.max_probes == 8
    for bad in (-1, 9):
        with pytest.raises(ValueError):
            TeacherPlacementConfig(max_probes=bad)


@pytest.mark.parametrize("path", ["teacher.placement.max_probes"])
def test_each_new_key_is_classified(path):
    rule = classify_config_path(path)
    assert rule is not None and "TE2" in rule.rationale, path


def test_the_gate_reads_on_with_lessons_on_and_off_with_lessons_off(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, TAG)
    assert T2.on(load_vault(paths.root))
    paths2 = create_basic_vault(tmp_path / "vault2")
    set_algorithm_version(paths2, TAG)
    append_config_toml(paths2.root, "[teacher]\nenabled = false\n")
    assert not T2.on(load_vault(paths2.root))
