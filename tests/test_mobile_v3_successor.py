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


from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    LESSON_OFFERS_ALGORITHM_VERSION,
    PHONE_PROBES_ALGORITHM_VERSION,
    PHONE_PROBES_VERSIONS,
    SUCCESSOR_CHAIN,
)
from learnloop.vault.loader import load_vault
from learnloop_mobile.config import MobileConfig
from learnloop_sidecar.request_origin import RequestOrigin, phone_probes_on

from tests.helpers import create_basic_vault, set_algorithm_version

TAG = PHONE_PROBES_ALGORITHM_VERSION
OLD = LESSON_OFFERS_ALGORITHM_VERSION


def test_the_successor_is_one_constant_after_te3b_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == "mvp-0.53"
    # IH5's successor (mvp-0.55) follows it and keeps it, then the placement hole's (mvp-0.56) and slip or gap's (mvp-0.57).
    assert TAG == "mvp-0.54" == SUCCESSOR_CHAIN[-6] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.59"
    assert PHONE_PROBES_VERSIONS == frozenset({TAG, "mvp-0.55", "mvp-0.56", "mvp-0.57", "mvp-0.58", "mvp-0.59"})


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
