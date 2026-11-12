"""The figure wait estimate's successor (mvp-0.58, after slip or gap's mvp-0.57): one constant, its switch, its gate,
its openers and its upgrade (docs/reviews/figure-wait-estimate.md; docs/algorithm-change-playbook.md).

The upgrade is the chain's next journalled link (a projection activation; nothing recorded changes, no migration).
``figures.prefetch.pressed_waits = false`` decides as mvp-0.57 exactly (``prefetch_decision_v1``;
tests/test_figure_wait_estimate.py). Fakes only; no model call.
"""

from __future__ import annotations

import inspect

from learnloop.algorithm_versions import (
    FIGURE_WAIT_ALGORITHM_VERSION,
    FIGURE_WAIT_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    SLIP_GAP_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.config.schema import FiguresPrefetchConfig
from learnloop.figure_wait_upgrade import PREDECESSOR, upgrade_to_figure_wait
from learnloop.figures.prefetch_ledger import pressed_waits_on
from learnloop.params.parameter_registry import classify_config_path
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault, set_algorithm_version
from tests.source_service_fakes import set_config

TAG = FIGURE_WAIT_ALGORITHM_VERSION
OLD = SLIP_GAP_ALGORITHM_VERSION


def test_the_successor_is_one_constant_after_slip_or_gap_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == PREDECESSOR == "mvp-0.57"
    # The facet-belief successor (mvp-0.59) follows it and keeps it.
    assert TAG == "mvp-0.58" == SUCCESSOR_CHAIN[-2] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.59"
    assert FIGURE_WAIT_VERSIONS == frozenset({TAG, "mvp-0.59"})


def test_the_switch_defaults_on_and_is_classified():
    assert FiguresPrefetchConfig().pressed_waits is True
    rule = classify_config_path("figures.prefetch.pressed_waits")
    assert rule is not None and "kill switch" in rule.rationale and "mvp-0.58" in rule.rationale


def test_the_gate_reads_off_below_the_tag_and_with_the_switch_off(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    assert not pressed_waits_on(load_vault(paths.root))
    set_algorithm_version(paths, TAG)
    assert pressed_waits_on(load_vault(paths.root))
    set_config(paths, "figures.prefetch", pressed_waits=False)
    assert not pressed_waits_on(load_vault(paths.root))


def test_the_openers_install_this_links_completion():
    from learnloop import figure_wait_upgrade
    from learnloop.cli import runtime
    from learnloop_sidecar import context

    # The facet-belief successor's link is the chain's latest, which hands this link's journal back here.
    assert "learnloop.facet_belief_upgrade" in inspect.getsource(runtime._complete_interrupted_activation)
    assert "learnloop.facet_belief_upgrade" in inspect.getsource(context._complete_interrupted_activation)
    assert "learnloop.slip_gap_upgrade import complete_interrupted_activation" in inspect.getsource(
        figure_wait_upgrade)


def test_the_upgrade_publishes_the_tag_and_completes_once(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = upgrade_to_figure_wait(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (OLD, TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    again = upgrade_to_figure_wait(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_chains_from_an_older_link(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.47")
    result = upgrade_to_figure_wait(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == ("mvp-0.47", TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG


def test_the_upgrade_refuses_anything_older_than_the_chain(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    result = upgrade_to_figure_wait(paths.root)
    assert not result.upgraded and "cannot upgrade from 'mvp-0.8'" in result.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"


def test_the_cli_upgrade_reaches_the_tag_by_default_and_by_name(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli.app import app

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{OLD} -> {LATEST_ALGORITHM_VERSION}" in result.output
    named = create_basic_vault(tmp_path / "named")
    set_algorithm_version(named, OLD)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(named.root), "--to", TAG])
    assert result.exit_code == 0, result.output
    assert load_vault(named.root).config.algorithms.algorithm_version == TAG
