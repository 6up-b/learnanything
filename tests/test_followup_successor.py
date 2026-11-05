"""FG1's successor mvp-0.45: one constant, its upgrade, its defaults, and its kill switch."""

from __future__ import annotations

import inspect
import tomllib

from learnloop.algorithm_versions import (
    DATA_CAPTURE_ALGORITHM_VERSION,
    FOLLOWUP_SERVE_ALGORITHM_VERSION,
    FOLLOWUP_SERVE_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import LearnLoopConfig
from learnloop.config.template import (
    DEFAULTS_SNAPSHOT_BY_ALGORITHM,
    default_config_text,
    defaults_fingerprint_for_version,
)
from learnloop.followup_serve.gates import effective_auto_generate_on_entry, generate_and_serve_on
from learnloop.followup_serve_upgrade import PREDECESSOR, upgrade_to_followup_serve
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = FOLLOWUP_SERVE_ALGORITHM_VERSION
OLD = DATA_CAPTURE_ALGORITHM_VERSION


def test_the_successor_is_one_constant_after_data_capture():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == PREDECESSOR == "mvp-0.44"
    assert TAG == "mvp-0.45" and TAG in FOLLOWUP_SERVE_VERSIONS and OLD not in FOLLOWUP_SERVE_VERSIONS
    assert LATEST_ALGORITHM_VERSION in FOLLOWUP_SERVE_VERSIONS


def test_every_defaults_snapshot_is_recomputed():
    for version, fingerprint in DEFAULTS_SNAPSHOT_BY_ALGORITHM.items():
        assert fingerprint == defaults_fingerprint_for_version(version), version
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[OLD]


def test_new_vaults_get_true_effectively_and_older_templates_stay_as_they_were():
    new = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(TAG)))
    old = LearnLoopConfig.model_validate(tomllib.loads(default_config_text(OLD)))
    assert effective_auto_generate_on_entry(new) is True
    assert effective_auto_generate_on_entry(old) is False
    assert new.followup.generate_and_serve is True and new.ui.show_router_decisions is True


def test_the_switch_governs_the_effective_setting(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    config = load_vault(paths.root).config
    assert not generate_and_serve_on(config) and effective_auto_generate_on_entry(config) is False
    set_algorithm_version(paths, TAG)
    config = load_vault(paths.root).config
    assert generate_and_serve_on(config) and effective_auto_generate_on_entry(config) is True


def test_the_upgrade_moves_a_predecessor_and_leaves_the_stored_setting(tmp_path):
    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    set_algorithm_version(paths, OLD)
    before = load_vault(paths.root).config.probe.generation.auto_generate_on_entry
    result = upgrade_to_followup_serve(paths.root)
    assert result.upgraded and result.from_version == OLD and result.to_version == TAG
    loaded = load_vault(paths.root)
    assert loaded.config.algorithms.algorithm_version == TAG
    assert loaded.config.probe.generation.auto_generate_on_entry is before
    again = upgrade_to_followup_serve(paths.root)
    assert not again.upgraded


def test_the_openers_install_this_links_completion():
    from learnloop.cli import runtime
    from learnloop_sidecar import context

    # The chain's latest completion (router objective RO6's) is installed; it hands an earlier link's journal on.
    assert "learnloop.router_learned_tail_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.router_learned_tail_upgrade" in inspect.getsource(context._complete_interrupted_activation)


def test_the_kill_switch_reads_off_a_vault_at_the_tag(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, TAG)
    append_config_toml(paths.root, "[followup]\ngenerate_and_serve = false\n")
    config = load_vault(paths.root).config
    assert not generate_and_serve_on(config)
    assert effective_auto_generate_on_entry(config) is config.probe.generation.auto_generate_on_entry
