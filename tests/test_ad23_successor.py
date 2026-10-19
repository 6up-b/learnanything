"""Adaptive difficulty AD2+AD3: the ``mvp-0.28`` successor (spec §11.1; docs/algorithm-change-playbook.md).

One successor, six switches, each restoring its part of ``mvp-0.27`` exactly and
composing as §11.1 states; the dose arm outside it. With every switch false, or
below the tag, what is served is the predecessor's (pinned on fixture copies).
Fails before AD2+AD3: there was no ``mvp-0.28``. Fakes only; no model is called.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from learnloop import clock as clock_module
from learnloop.adaptive_difficulty import successor as SC
from learnloop.algorithm_versions import (
    ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION,
    ADAPTIVE_DIFFICULTY_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.clock import FrozenClock
from learnloop.db.copies import copy_tree_with_databases
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import ad23_vault, selections
from tests.helpers import append_config_toml, create_placement_vault, set_algorithm_version

T0 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
WORKING_FIXTURES = ("linear_algebra", "probability", "arxiv_v2")
ALL_OFF = "\n".join(f"{name} = false" for name in SC.SWITCHES) + "\n"


def test_the_successor_is_the_next_link_with_its_defaults_snapshot():
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version

    assert ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION == "mvp-0.28" == SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION
    assert SUCCESSOR_CHAIN[-2] == "mvp-0.27"
    assert ADAPTIVE_DIFFICULTY_VERSIONS == frozenset({"mvp-0.28"})
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.28"] == defaults_fingerprint_for_version("mvp-0.28")


def test_below_the_tag_every_switch_reads_off_whatever_the_config_says(tmp_path):
    paths = ad23_vault(tmp_path, version="mvp-0.27")
    vault = load_vault(paths.root)
    assert all(getattr(vault.config.adaptive_difficulty, name) for name in SC.SWITCHES)
    assert not SC.successor_active(vault.config)
    assert not any(SC.switch_on(vault.config, name) for name in SC.SWITCHES)
    # The dose arm is outside the successor: it acts at every version.
    assert SC.dose_offers_on(vault.config)
    set_algorithm_version(paths, "mvp-0.28")
    vault = load_vault(paths.root)
    assert all(SC.switch_on(vault.config, name) for name in SC.SWITCHES)
    vault.config.adaptive_difficulty.enabled = False
    assert not SC.successor_active(vault.config) and not SC.dose_offers_on(vault.config)


def test_the_switches_compose():
    """``promoted_predictor = false`` makes the subject view's live parts moot for live decisions;
    ``reading_opportunities = false`` makes ``reading_self_check`` moot."""

    from learnloop.adaptive_difficulty.replay import ReplaySettings
    from learnloop.config import LearnLoopConfig

    config = LearnLoopConfig()
    config.algorithms.algorithm_version = "mvp-0.28"
    config.adaptive_difficulty.reading_opportunities = False
    assert not SC.verdicts_on(config) and not ReplaySettings.from_config(config).verdicts
    config.adaptive_difficulty.reading_opportunities = True
    assert SC.verdicts_on(config)
    config.adaptive_difficulty.promoted_predictor = False
    assert not SC.subject_view_live(config)


def test_promoted_predictor_off_makes_coupling_and_reading_moot_for_draws(tmp_path):
    """With the LO view live, the draws are the same whatever ``learned_coupling``,
    ``reading_opportunities`` and ``reading_self_check`` say."""

    from tests.test_ad3_subject_view import _scenario, _scores

    off = "promoted_predictor = false\n"
    base = _scenario(tmp_path, "a", seen=True, ad=off)
    moot = _scenario(tmp_path, "b", seen=True, ad=off + "learned_coupling = false\nreading_opportunities = false\n"
                                                         "reading_self_check = false\n")
    assert _scores(base["draws"], "serve") == _scores(moot["draws"], "serve")
    assert base["step"]["practice_item_id"] == moot["step"]["practice_item_id"]


def test_the_upgrade_takes_the_predecessor_or_the_chain_and_refuses_the_rest(tmp_path):
    from learnloop.ad_successor_upgrade import upgrade_to_mvp028
    from learnloop.cli.app import app
    from learnloop.db.repositories import Repository
    from learnloop.db.stores import ad_serving

    clock = FrozenClock(T0)
    direct = create_placement_vault(tmp_path / "direct", version="mvp-0.27")
    result = upgrade_to_mvp028(direct.root, clock=clock)
    assert result.upgraded and (result.from_version, result.to_version) == ("mvp-0.27", "mvp-0.28")
    assert load_vault(direct.root).config.algorithms.algorithm_version == "mvp-0.28"
    with Repository(direct.sqlite_path).connection() as connection:
        assert ad_serving.read_state(connection), "AD's DERIVED state is prepared before the rename"
    again = upgrade_to_mvp028(direct.root, clock=clock)
    assert not again.upgraded and again.problems == ["vault is already mvp-0.28"]

    chained = create_placement_vault(tmp_path / "chained", version="mvp-0.25")
    assert upgrade_to_mvp028(chained.root, clock=clock).upgraded
    assert load_vault(chained.root).config.algorithms.algorithm_version == "mvp-0.28"

    old = create_placement_vault(tmp_path / "old", version="mvp-0.8")
    refused = upgrade_to_mvp028(old.root, clock=clock)
    assert not refused.upgraded and "only 'mvp-0.27'" in refused.problems[0]
    assert load_vault(old.root).config.algorithms.algorithm_version == "mvp-0.8"

    cli = create_placement_vault(tmp_path / "cli", version="mvp-0.27")
    invoked = CliRunner().invoke(app, ["upgrade", "--vault", str(cli.root), "--to", "mvp-0.28"])
    assert invoked.exit_code == 0, invoked.output
    assert "mvp-0.27 -> mvp-0.28" in invoked.output


def test_new_vaults_start_at_the_successor_with_every_switch_on(tmp_path):
    from learnloop.bootstrap import init_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(T0))
    fresh = load_vault(tmp_path / "fresh")
    assert fresh.config.algorithms.algorithm_version == "mvp-0.28"
    assert all(SC.switch_on(fresh.config, name) for name in SC.SWITCHES) and SC.dose_offers_on(fresh.config)


def test_every_new_key_is_a_classified_config_leaf():
    from learnloop.config import LearnLoopConfig
    from learnloop.params import parameter_registry as registry

    config = LearnLoopConfig()
    config.adaptive_difficulty.price_per_million = 1.0
    leaves = registry.config_numeric_leaves(config)
    numeric = ("dose_floor", "dose_daily_offers", "practice_band", "overlap_band", "overlap_share", "near_tie_margin",
               "calibrate_below", "ready_threshold")
    for key in numeric:
        path = f"adaptive_difficulty.{key}"
        assert path in leaves, path
        assert registry.classify_config_path(path) is not None, path
    # Every numeric leaf of the section is classified (booleans and versions are switches, not parameters).
    for path in leaves:
        if path.startswith("adaptive_difficulty."):
            assert registry.classify_config_path(path) is not None, path


# -- with every switch false the served output is the predecessor's (fixture copies) ---------------------


def _volatile_free(value: Any) -> Any:
    """Drop fresh ids, timestamps and the version string; the decision id inside a receipt line."""

    import re

    if isinstance(value, dict):
        return {k: _volatile_free(v) for k, v in value.items()
                if k not in ("id", "algorithmVersion") and not k.endswith("Id") and not k.endswith("At")
                and not k.endswith("Ref")}
    if isinstance(value, list):
        return [_volatile_free(v) for v in value]
    if isinstance(value, str):
        return re.sub(r"--decision [0-9A-Z]{26}", "--decision <id>", value)
    return value


def _call(ctx: Any, name: str, params: dict[str, Any]) -> Any:
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _copy(tmp_path: Path, fixture: str, name: str, *, version: str, toml: str) -> Any:
    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop_sidecar.context import SidecarContext

    root = tmp_path / name
    copy_tree_with_databases(FIXTURES / fixture, root)
    set_algorithm_version(type("Paths", (), {"root": root})(), version)
    append_config_toml(root, toml)
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    return ctx, root


QUIET_ROUTES = ("[adaptive_difficulty]\noutside_forecasters = []\nfeature_audit = false\n")


@pytest.mark.parametrize("fixture", WORKING_FIXTURES)
def test_every_switch_false_serves_the_predecessor_on_fixture_copies(tmp_path, monkeypatch, fixture):
    """At ``mvp-0.28`` with the six switches false, Today, the plan and every served step are
    ``mvp-0.27``'s exactly, and no AD2+AD3 row is written (the pin of orchestrator note 4)."""

    if not (FIXTURES / fixture / "state.sqlite").exists():
        pytest.skip(f"{fixture} fixture absent")
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: T0)
    monkeypatch.setenv("LEARNLOOP_AD_MODELS", "off")
    before, _root_b = _copy(tmp_path, fixture, "pred", version="mvp-0.27", toml=QUIET_ROUTES)
    after, root_a = _copy(tmp_path, fixture, "succ", version="mvp-0.28", toml=QUIET_ROUTES + ALL_OFF)
    reads = []
    for ctx in (before, after):
        sequence = [_volatile_free(_call(ctx, "get_today_queue", {})), _volatile_free(_call(ctx, "get_daily_plan", {}))]
        for _ in range(3):
            step = _call(ctx, "next_plan_item", {})
            sequence.append(_volatile_free(step))
        reads.append(sequence)
    assert reads[0] == reads[1]
    paths = type("P", (), {"sqlite_path": root_a / "state.sqlite"})()
    assert selections(paths) == []
