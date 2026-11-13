"""FG1's successor mvp-0.45: one constant, its upgrade, its defaults, and its kill switch."""

from __future__ import annotations

import tomllib

from learnloop.algorithm_versions import (
    DATA_CAPTURE_ALGORITHM_VERSION,
    FOLLOWUP_SERVE_ALGORITHM_VERSION,
    FOLLOWUP_SERVE_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import LearnLoopConfig
from learnloop.config.template import default_config_text
from learnloop.followup_serve.gates import effective_auto_generate_on_entry, generate_and_serve_on
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = FOLLOWUP_SERVE_ALGORITHM_VERSION
OLD = DATA_CAPTURE_ALGORITHM_VERSION


def test_the_successor_is_one_constant_after_data_capture():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == "mvp-0.44"
    assert TAG == "mvp-0.45" and TAG in FOLLOWUP_SERVE_VERSIONS and OLD not in FOLLOWUP_SERVE_VERSIONS
    assert LATEST_ALGORITHM_VERSION in FOLLOWUP_SERVE_VERSIONS


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


def test_the_kill_switch_reads_off_a_vault_at_the_tag(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, TAG)
    append_config_toml(paths.root, "[followup]\ngenerate_and_serve = false\n")
    config = load_vault(paths.root).config
    assert not generate_and_serve_on(config)
    assert effective_auto_generate_on_entry(config) is config.probe.generation.auto_generate_on_entry
