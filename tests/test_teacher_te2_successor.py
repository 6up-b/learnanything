"""Teacher TE2's successor (spec_teacher_v1 rev 5 §18.3, §24 row TE2): one constant, its defaults, its gate, its upgrade.

The upgrade is the chain's next journalled link: from mvp-0.50 (or mvp-0.9 onwards through the chain), one
transaction with the projection's activation under the tag and the config's publication last. Nothing already
recorded changes. ``teacher.probes = false`` (or below the tag) serves mvp-0.50's lessons. Fakes only; no model call.
Built as mvp-0.50 on mvp-0.49 and renumbered at landing to mvp-0.51 on the router follow-up batch's mvp-0.50.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import tomllib

import pytest

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    ROUTER_FOLLOWUPS_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    TEACHER_PROBES_ALGORITHM_VERSION,
    TEACHER_PROBES_VERSIONS,
)
from learnloop.config.schema import LearnLoopConfig, TeacherConfig, TeacherPlacementConfig
from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, default_config_text, defaults_fingerprint_for_version
from learnloop.params.parameter_registry import classify_config_path
from learnloop.teacher import te2 as T2
from learnloop.teacher_probes_upgrade import PREDECESSOR, upgrade_to_teacher_probes
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = TEACHER_PROBES_ALGORITHM_VERSION
OLD = ROUTER_FOLLOWUPS_ALGORITHM_VERSION
#: TE2's keys under [teacher] (modelled defaults, in every snapshot, inert below the tag).
TE2_KEYS = ("probes", "placement")


def drop_te2_keys(dumped: dict) -> dict:
    """An earlier successor's frozen defaults digest: TE2's keys (in every snapshot, inert below mvp-0.51) dropped."""

    assert dumped["teacher"].pop("probes") is True
    assert dumped["teacher"].pop("placement") == {"max_probes": 8}
    return dumped


def test_the_successor_is_one_constant_after_the_router_followups_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == PREDECESSOR == "mvp-0.50"
    assert TAG == "mvp-0.51" == SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION
    assert TEACHER_PROBES_VERSIONS == frozenset({TAG})


def test_the_switch_and_the_keep_bound_and_their_validation():
    config = TeacherConfig()
    assert config.probes is True and config.placement.max_probes == 8
    for bad in (-1, 9):
        with pytest.raises(ValueError):
            TeacherPlacementConfig(max_probes=bad)


def test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys():
    for version, fingerprint in DEFAULTS_SNAPSHOT_BY_ALGORITHM.items():
        assert fingerprint == defaults_fingerprint_for_version(version), version
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[OLD]
    # mvp-0.50's value on main at the landing (516db1d862, the router follow-up batch's own mvp-0.50 snapshot),
    # frozen here: dropping TE2's keys reproduces it.
    dumped = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD))).model_dump(
        mode="json", exclude_none=False)
    assert dumped["teacher"].pop("probes") is True
    assert dumped["teacher"].pop("placement") == {"max_probes": 8}
    digest = hashlib.sha256(json.dumps(dumped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == "780d5afa78fc92eae0911c381a364428f126dabd594125f7d63f423a4638ae59"


@pytest.mark.parametrize("path", ["teacher.probes", "teacher.placement.max_probes"])
def test_each_new_key_is_classified(path):
    rule = classify_config_path(path)
    assert rule is not None and "TE2" in rule.rationale, path


def test_the_gate_reads_off_below_the_tag_switched_off_and_with_lessons_off(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    assert not T2.on(load_vault(paths.root))
    set_algorithm_version(paths, TAG)
    assert T2.on(load_vault(paths.root))
    append_config_toml(paths.root, "[teacher]\nprobes = false\n")
    assert not T2.on(load_vault(paths.root))
    paths2 = create_basic_vault(tmp_path / "vault2")
    set_algorithm_version(paths2, TAG)
    append_config_toml(paths2.root, "[teacher]\nenabled = false\n")
    assert not T2.on(load_vault(paths2.root))


def test_the_openers_install_this_links_completion():
    from learnloop import teacher_probes_upgrade
    from learnloop.cli import runtime
    from learnloop_sidecar import context

    assert "learnloop.teacher_probes_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.teacher_probes_upgrade" in inspect.getsource(context._complete_interrupted_activation)
    # It hands an earlier link's journal to the follow-up batch's completion, which hands it on in turn.
    assert "learnloop.router_followups_upgrade import complete_interrupted_activation" in inspect.getsource(
        teacher_probes_upgrade)


def test_the_upgrade_publishes_the_tag_and_completes_once(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = upgrade_to_teacher_probes(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (OLD, TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    again = upgrade_to_teacher_probes(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_chains_from_an_older_link(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.48")
    result = upgrade_to_teacher_probes(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == ("mvp-0.48", TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG


def test_the_upgrade_refuses_anything_older_than_the_chain(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    result = upgrade_to_teacher_probes(paths.root)
    assert not result.upgraded and "cannot upgrade from 'mvp-0.8'" in result.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"


def test_the_cli_upgrade_reaches_the_tag_by_default(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli.app import app

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
