"""Phone V3's successor (mvp-0.54; built as mvp-0.53, renumbered after TE3b's mvp-0.53 landed): the chain, its defaults,
its gate, and its upgrade.

The 2026-10-17 rule (docs/algorithm-change-playbook.md): a change to which items are served as measurements is a
successor with a kill switch even when replay is unchanged. From V3 a phone origin serves and answers the probes it
used to leave for the desktop. The upgrade is the chain's next journalled link: from TE3b's mvp-0.53 (or mvp-0.9 onwards
through the chain), one transaction with the projection's activation under the tag and the config's publication last.
Nothing already recorded changes. The kill switch is the phone host's ``phone_probes`` (mobile.toml), so the vault's
effective defaults gain no key. Fakes only; no model call.
"""

from __future__ import annotations

import inspect

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    LESSON_OFFERS_ALGORITHM_VERSION,
    PHONE_PROBES_ALGORITHM_VERSION,
    PHONE_PROBES_VERSIONS,
    SUCCESSOR_CHAIN,
)
from learnloop.phone_probes_upgrade import PREDECESSOR, upgrade_to_phone_probes
from learnloop.vault.loader import load_vault
from learnloop_mobile.config import MobileConfig
from learnloop_sidecar.request_origin import RequestOrigin, phone_probes_on

from tests.helpers import create_basic_vault, set_algorithm_version

TAG = PHONE_PROBES_ALGORITHM_VERSION
OLD = LESSON_OFFERS_ALGORITHM_VERSION


def test_the_successor_is_one_constant_after_te3b_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == PREDECESSOR == "mvp-0.53"
    # IH5's successor (mvp-0.55) follows it and keeps it, then the placement hole's (mvp-0.56) and slip or gap's (mvp-0.57).
    assert TAG == "mvp-0.54" == SUCCESSOR_CHAIN[-4] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.57"
    assert PHONE_PROBES_VERSIONS == frozenset({TAG, "mvp-0.55", "mvp-0.56", "mvp-0.57"})


def test_the_switch_is_the_hosts_and_defaults_on():
    config = MobileConfig(enabled=True, vault="/abs/vault", hostname="desktop.tail.ts.net", owner_login="o@example.com")
    assert config.phone_probes is True and config.phone_plan is True
    # An origin made without it is V2's phone; the desktop never answers to it.
    assert RequestOrigin(device_id="dev").phone_probes is False


def test_the_gate_is_the_switch_and_the_tag_and_never_the_desktop(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    on, off = RequestOrigin(device_id="dev", phone_probes=True), RequestOrigin(device_id="dev")
    set_algorithm_version(paths, OLD)
    assert not phone_probes_on(on, load_vault(paths.root).config)
    set_algorithm_version(paths, TAG)
    config = load_vault(paths.root).config
    assert phone_probes_on(on, config)
    assert not phone_probes_on(off, config)
    assert not phone_probes_on(None, config)


def test_the_openers_install_this_links_completion():
    from learnloop import phone_probes_upgrade
    from learnloop.cli import runtime
    from learnloop_sidecar import context

    # Slip or gap's link (mvp-0.57) is the chain's latest since; its completion hands this link's journal on to the
    # placement hole's (mvp-0.56), then IH5's (mvp-0.55), which hands it here.
    from learnloop import failure_share_upgrade, slip_gap_upgrade, unevidenced_return_upgrade

    assert "learnloop.slip_gap_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.slip_gap_upgrade" in inspect.getsource(context._complete_interrupted_activation)
    assert "learnloop.unevidenced_return_upgrade import complete_interrupted_activation" in inspect.getsource(
        slip_gap_upgrade)
    assert "learnloop.failure_share_upgrade import complete_interrupted_activation" in inspect.getsource(
        unevidenced_return_upgrade)
    assert "learnloop.phone_probes_upgrade import complete_interrupted_activation" in inspect.getsource(
        failure_share_upgrade)
    # It hands an earlier link's journal to TE3b's completion, which hands it on in turn.
    assert "learnloop.lesson_offers_upgrade import complete_interrupted_activation" in inspect.getsource(
        phone_probes_upgrade)


def test_the_upgrade_publishes_the_tag_and_completes_once(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = upgrade_to_phone_probes(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (OLD, TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    again = upgrade_to_phone_probes(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_chains_from_an_older_link(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.47")
    result = upgrade_to_phone_probes(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == ("mvp-0.47", TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG


def test_the_upgrade_refuses_anything_older_than_the_chain(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    result = upgrade_to_phone_probes(paths.root)
    assert not result.upgraded and "cannot upgrade from 'mvp-0.8'" in result.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"


def test_the_cli_upgrade_reaches_the_tag_by_default_and_by_name(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli.app import app

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    # The default target is the chain's latest (slip or gap's mvp-0.57 since), through this link.
    assert f"{OLD} -> {LATEST_ALGORITHM_VERSION}" in result.output
    named = create_basic_vault(tmp_path / "named")
    set_algorithm_version(named, OLD)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(named.root), "--to", TAG])
    assert result.exit_code == 0, result.output
