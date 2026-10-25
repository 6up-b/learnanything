"""Adaptive difficulty AD2+AD3: the ``mvp-0.30`` successor (spec §11.1; docs/algorithm-change-playbook.md).

One successor, six switches, each restoring its part of ``mvp-0.29`` exactly and
composing as §11.1 states; the dose arm outside it. With every switch false, or
below the tag, what is served is the predecessor's (pinned on fixture copies).
Fails before AD2+AD3: there was no ``mvp-0.30``. Fakes only; no model is called.
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

from tests.owner_vaults import owner_vault, working_vault_params
from tests.ad23_fakes import COUPLED, ad23_vault, commit, selections
from tests.helpers import append_config_toml, create_placement_vault, set_algorithm_version

T0 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
# The owner's working vaults: backup-API copies in the owner_vaults lane (S0).
WORKING_FIXTURES = working_vault_params()
ALL_OFF = "\n".join(f"{name} = false" for name in SC.SWITCHES) + "\n"


def test_the_successor_is_the_next_link_with_its_defaults_snapshot():
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version

    # Reader workbench RW2d's mvp-0.31 landed after it and keeps it, and
    # rebuild equivalence's mvp-0.34 follows as the latest.
    assert ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION == "mvp-0.30" == SUCCESSOR_CHAIN[20]
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.34"
    # DL2 landed first: mvp-0.29 is the predecessor and mvp-0.28 is never used (the compose round).
    assert SUCCESSOR_CHAIN[19] == "mvp-0.29" and "mvp-0.28" not in SUCCESSOR_CHAIN
    assert ADAPTIVE_DIFFICULTY_VERSIONS == frozenset({"mvp-0.30", "mvp-0.31", "mvp-0.34"})
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.30"] == defaults_fingerprint_for_version("mvp-0.30")


def test_below_the_tag_every_switch_reads_off_whatever_the_config_says(tmp_path):
    paths = ad23_vault(tmp_path, version="mvp-0.29", ad=COUPLED)
    vault = load_vault(paths.root)
    assert all(getattr(vault.config.adaptive_difficulty, name) for name in SC.SWITCHES)
    assert not SC.successor_active(vault.config)
    assert not any(SC.switch_on(vault.config, name) for name in SC.SWITCHES)
    # The dose arm is outside the successor: it acts at every version.
    assert SC.dose_offers_on(vault.config)
    set_algorithm_version(paths, "mvp-0.30")
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
    config.algorithms.algorithm_version = "mvp-0.30"
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
    from learnloop.ad_successor_upgrade import upgrade_to_mvp030
    from learnloop.cli.app import app
    from learnloop.db.repositories import Repository
    from learnloop.db.stores import ad_serving

    clock = FrozenClock(T0)
    direct = create_placement_vault(tmp_path / "direct", version="mvp-0.29")
    result = upgrade_to_mvp030(direct.root, clock=clock)
    assert result.upgraded and (result.from_version, result.to_version) == ("mvp-0.29", "mvp-0.30")
    assert load_vault(direct.root).config.algorithms.algorithm_version == "mvp-0.30"
    with Repository(direct.sqlite_path).connection() as connection:
        assert ad_serving.read_state(connection), "AD's DERIVED state is prepared before the rename"
    again = upgrade_to_mvp030(direct.root, clock=clock)
    assert not again.upgraded and again.problems == ["vault is already mvp-0.30"]

    chained = create_placement_vault(tmp_path / "chained", version="mvp-0.25")
    assert upgrade_to_mvp030(chained.root, clock=clock).upgraded
    assert load_vault(chained.root).config.algorithms.algorithm_version == "mvp-0.30"

    old = create_placement_vault(tmp_path / "old", version="mvp-0.8")
    refused = upgrade_to_mvp030(old.root, clock=clock)
    assert not refused.upgraded and "only 'mvp-0.29'" in refused.problems[0]
    assert load_vault(old.root).config.algorithms.algorithm_version == "mvp-0.8"

    cli = create_placement_vault(tmp_path / "cli", version="mvp-0.29")
    invoked = CliRunner().invoke(app, ["upgrade", "--vault", str(cli.root), "--to", "mvp-0.30"])
    assert invoked.exit_code == 0, invoked.output
    assert "mvp-0.29 -> mvp-0.30" in invoked.output

    # The owner's chain: --to mvp-0.9, --to mvp-0.27, --to mvp-0.29, then --to mvp-0.30.
    owner = create_placement_vault(tmp_path / "owner", version="mvp-0.8")
    for step in ("mvp-0.9", "mvp-0.27", "mvp-0.29", "mvp-0.30"):
        ran = CliRunner().invoke(app, ["upgrade", "--vault", str(owner.root), "--to", step])
        assert ran.exit_code == 0, (step, ran.output)
    assert load_vault(owner.root).config.algorithms.algorithm_version == "mvp-0.30"


def test_new_vaults_start_at_the_successor_with_every_switch_on(tmp_path):
    """Every switch but ``learned_coupling``, which is off until the owner has spot-checked the
    relatedness proposal and adopted a coupling version (owner decision 2026-10-19)."""

    from learnloop.bootstrap import init_vault

    init_vault(tmp_path / "fresh", clock=FrozenClock(T0))
    fresh = load_vault(tmp_path / "fresh")
    # The latest successor (RW2d's mvp-0.31 since its landing) keeps AD's switches.
    assert fresh.config.algorithms.algorithm_version == "mvp-0.34"
    assert all(SC.switch_on(fresh.config, name) for name in SC.SWITCHES if name != "learned_coupling")
    assert not SC.switch_on(fresh.config, "learned_coupling") and SC.dose_offers_on(fresh.config)


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
    copy_tree_with_databases(owner_vault(fixture), root)
    set_algorithm_version(type("Paths", (), {"root": root})(), version)
    append_config_toml(root, toml)
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    return ctx, root


QUIET_ROUTES = ("[adaptive_difficulty]\noutside_forecasters = []\nfeature_audit = false\n")


@pytest.mark.parametrize("fixture", WORKING_FIXTURES)
def test_every_switch_false_serves_the_predecessor_on_fixture_copies(tmp_path, monkeypatch, fixture):
    """At ``mvp-0.30`` with the six switches false, Today, the plan and every served step are
    ``mvp-0.29``'s exactly (DL2's intent, with an active commitment on both copies so intent is not
    inert: the compose fix round, L4), and no AD2+AD3 row is written (the pin of orchestrator note 4)."""

    if not (owner_vault(fixture) / "state.sqlite").exists():
        pytest.skip(f"{fixture} fixture absent")
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: T0)
    monkeypatch.setenv("LEARNLOOP_AD_MODELS", "off")
    before, root_b = _copy(tmp_path, fixture, "pred", version="mvp-0.29", toml=QUIET_ROUTES)
    after, root_a = _copy(tmp_path, fixture, "succ", version="mvp-0.30", toml=QUIET_ROUTES + ALL_OFF)
    lo = sorted(load_vault(root_b).learning_objects)[0]
    for root in (root_b, root_a):
        commit(type("Paths", (), {"root": root, "sqlite_path": root / "state.sqlite"})(),
               [("learning_object", lo, "master")])
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


def test_below_the_tag_a_rebuild_writes_no_ad_state(tmp_path):
    """Below the tag nothing reads AD's DERIVED state, so a whole-vault rebuild leaves its tables
    empty (the predecessor's rebuild exactly), and a rolled-back vault's rows are cleared."""

    from learnloop.db.repositories import Repository
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths = ad23_vault(tmp_path, version="mvp-0.29")
    repository = Repository(paths.sqlite_path)
    rebuild_all_derived_state(load_vault(paths.root), repository)
    with repository.connection() as connection:
        for table in ("ad_state", "ad_attempt_trace", "item_forecast_scores"):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0, table
    set_algorithm_version(paths, "mvp-0.30")
    rebuild_all_derived_state(load_vault(paths.root), repository)
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM ad_state").fetchone()[0] > 0
    set_algorithm_version(paths, "mvp-0.29")
    rebuild_all_derived_state(load_vault(paths.root), repository)
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM ad_state").fetchone()[0] == 0
