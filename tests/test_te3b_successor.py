"""Teacher TE3b's router successor (mvp-0.53, after TE3a's mvp-0.52): one constant, its defaults, its gate, and its
upgrade.

The upgrade is the chain's next journalled link: from TE3a's mvp-0.52 (or mvp-0.9 onwards through the chain), one
transaction with the projection's activation under the tag and the config's publication last. Nothing already
recorded changes (no migration). Its kill switch went once every vault was past the tag. Fakes only; no model call.
"""

from __future__ import annotations


from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    LESSON_OFFERS_ALGORITHM_VERSION,
    LESSON_OPPORTUNITY_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.router_objective_switches import lesson_offers_on
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

TAG = LESSON_OFFERS_ALGORITHM_VERSION
OLD = LESSON_OPPORTUNITY_ALGORITHM_VERSION


def test_the_successor_is_one_constant_after_te3a_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == "mvp-0.52"
    # Phone V3's successor (mvp-0.54) follows it and keeps it.
    assert TAG == "mvp-0.53" == SUCCESSOR_CHAIN[-19] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.72"


def test_the_gate_reads_on_and_off_with_the_objective_or_lessons_off(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, TAG)
    assert lesson_offers_on(load_vault(paths.root).config)
    for n, toml in enumerate((
            "[router_objective]\nenabled = false\n",
            "[teacher]\nenabled = false\n")):
        other = create_basic_vault(tmp_path / f"off{n}")
        set_algorithm_version(other, TAG)
        append_config_toml(other.root, toml)
        assert not lesson_offers_on(load_vault(other.root).config), toml
