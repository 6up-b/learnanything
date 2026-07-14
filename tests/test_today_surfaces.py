"""Focused read-model tests for the F5/F7 Today surfaces (spec §4.3-§4.5).

These cover the deterministic selection/ranking/threshold logic in isolation:
the underlying FSRS projection (``facet_projections_at``) and ``goal_report`` are
monkeypatched so the tests are hermetic and do not depend on fixture drift. One
test exercises ``blueprint_weight_by_facet`` against real blueprint dataclasses.
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from learnloop.db.repositories import Repository
from learnloop.services.probe_episodes import enter_episode
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from learnloop.clock import FrozenClock
from learnloop.services import decay_pressure as dp_mod
from learnloop.services import overconfidence as oc_mod
from learnloop.services import reentry_summary as re_mod
from learnloop.services.blueprint_projection import (
    BlueprintProjection,
    ComponentReadiness,
    LoReadiness,
    RecipeProjection,
)
from learnloop.services.decay_pressure import decay_pressure
from learnloop.services.goal_projection import FacetProjection, GoalReport
from learnloop.services.overconfidence import blueprint_weight_by_facet, overconfidence_facets
from learnloop.services.reentry_summary import reentry_summary


# --- lightweight fakes -------------------------------------------------------


class _FakeHyp:
    overconfidence_min_evidence_mass = 1.0
    reentry_gap_days = 7
    decay_pressure_target_recall = 0.8
    decay_pressure_horizon_days = 60


class _FakeConfig:
    hypothesis = _FakeHyp()


@dataclass
class _FakeLO:
    title: str
    concept: str = "concept_x"
    status: str = "active"


class _FakeVault:
    def __init__(self, los: dict[str, _FakeLO]):
        self.config = _FakeConfig()
        self.learning_objects = los

    def canonical_facet_id(self, facet: str) -> str:
        return facet


class _FakeGoal:
    def __init__(self, target_recall: float = 0.8):
        self.id = "goal_test"
        self.target_recall = target_recall


class _FakeRepo:
    def __init__(self, ended_at: str | None):
        self._ended_at = ended_at

    def most_recent_ended_at(self) -> str | None:
        return self._ended_at


def _facet(
    facet_id: str,
    *,
    lo: str = "lo1",
    ready: float,
    demonstrated: bool = False,
    evidence_mass: float = 5.0,
    decay_estimated: bool = True,
) -> FacetProjection:
    return FacetProjection(
        learning_object_id=lo,
        facet_id=facet_id,
        label="uncertain",
        current_recall=ready,
        projected_recall=ready,
        on_track=ready >= 0.8,
        predicted_current=ready,
        predicted_at_horizon=ready,
        evidence_mass=evidence_mass,
        certified=demonstrated,
        attempts_to_certify=None,
        demonstrated=demonstrated,
        decay_estimated=decay_estimated,
    )


def _report(facets: list[FacetProjection]) -> GoalReport:
    return GoalReport(
        goal_id="goal_test",
        target_recall=0.8,
        due_at=None,
        horizon=datetime(2026, 1, 1, tzinfo=UTC),
        facets=facets,
        blueprint_readiness_by_lo={},
    )


# --- F5 overconfidence -------------------------------------------------------


def test_overconfidence_excludes_demonstrated_and_low_ready(monkeypatch):
    facets = [
        _facet("f_hot", ready=0.92, demonstrated=False),      # qualifies
        _facet("f_done", ready=0.95, demonstrated=True),      # demonstrated -> excluded
        _facet("f_lowready", ready=0.60, demonstrated=False),  # ready < target -> excluded
    ]
    monkeypatch.setattr(oc_mod, "goal_report", lambda *a, **k: _report(facets))
    monkeypatch.setattr(oc_mod, "blueprint_weight_by_facet", lambda *a, **k: {})
    vault = _FakeVault({"lo1": _FakeLO("LO One")})
    out = overconfidence_facets(vault, _FakeRepo(None), _FakeGoal())
    assert [f.facet_id for f in out] == ["f_hot"]
    assert out[0].blueprint_weight == 1.0  # default when no blueprint weight


def test_overconfidence_evidence_mass_gate(monkeypatch):
    facets = [
        _facet("f_thin", ready=0.9, demonstrated=False, evidence_mass=0.4),  # below gate
        _facet("f_solid", ready=0.9, demonstrated=False, evidence_mass=3.0),
    ]
    monkeypatch.setattr(oc_mod, "goal_report", lambda *a, **k: _report(facets))
    monkeypatch.setattr(oc_mod, "blueprint_weight_by_facet", lambda *a, **k: {})
    vault = _FakeVault({"lo1": _FakeLO("LO One")})
    out = overconfidence_facets(vault, _FakeRepo(None), _FakeGoal(), min_evidence_mass=1.0)
    assert [f.facet_id for f in out] == ["f_solid"]


def test_overconfidence_ranks_by_ready_times_weight(monkeypatch):
    facets = [
        _facet("f_a", ready=0.85, demonstrated=False),  # 0.85 * 3 = 2.55
        _facet("f_b", ready=0.95, demonstrated=False),  # 0.95 * 1 = 0.95
    ]
    weights = {("lo1", "f_a"): 3.0, ("lo1", "f_b"): 1.0}
    monkeypatch.setattr(oc_mod, "goal_report", lambda *a, **k: _report(facets))
    monkeypatch.setattr(oc_mod, "blueprint_weight_by_facet", lambda *a, **k: weights)
    vault = _FakeVault({"lo1": _FakeLO("LO One")})
    out = overconfidence_facets(vault, _FakeRepo(None), _FakeGoal())
    assert [f.facet_id for f in out] == ["f_a", "f_b"]  # higher ready×weight first
    assert out[0].score == pytest.approx(2.55)


def test_blueprint_weight_by_facet_sums_referencing_blueprints():
    component = ComponentReadiness(
        facet="f_a", capability="retrieval", modality="hard", predicted_recall=0.5, gating=True
    )
    recipe = RecipeProjection(
        recipe_id="r1", composition="conjunctive", success_probability=0.5,
        components=[component], bottleneck=component,
    )
    bp = BlueprintProjection(
        blueprint_id="bp1", weight=2.5, success_probability=0.5, best_recipe_id="r1",
        recipes=[recipe],
    )
    readiness = LoReadiness(
        learning_object_id="lo1", has_blueprints=True, readiness=0.5,
        blueprints=[bp], bottleneck=component,
    )
    report = GoalReport(
        goal_id="g", target_recall=0.8, due_at=None,
        horizon=datetime(2026, 1, 1, tzinfo=UTC), facets=[],
        blueprint_readiness_by_lo={"lo1": readiness},
    )
    vault = _FakeVault({"lo1": _FakeLO("LO One")})
    weights = blueprint_weight_by_facet(vault, report)
    assert weights[("lo1", "f_a")] == pytest.approx(2.5)


# --- F7 welcome-back ---------------------------------------------------------


def test_reentry_below_threshold_does_not_show(monkeypatch):
    now = datetime(2026, 7, 14, tzinfo=UTC)
    ended = (now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    vault = _FakeVault({"lo1": _FakeLO("LO One")})
    summary = reentry_summary(
        vault, _FakeRepo(ended), _FakeGoal(), clock=FrozenClock(now)
    )
    assert summary.show is False
    assert summary.gap_days == 3


def test_reentry_splits_solid_slipped_and_excludes_held_flat(monkeypatch):
    now = datetime(2026, 7, 14, tzinfo=UTC)
    ended_dt = now - timedelta(days=20)
    ended = ended_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def fake_projections(vault, repo, goal, at, *, clock=None):
        away = abs((at.astimezone(UTC) - ended_dt).total_seconds()) < 3600
        if away:  # projection to the last session end (recall was higher)
            return [
                _facet("f_solid", ready=0.9),
                _facet("f_slip", ready=0.9),          # was above target
                _facet("f_flat", ready=0.9, decay_estimated=False),
            ]
        return [  # projection to now (some decayed below target)
            _facet("f_solid", ready=0.85),
            _facet("f_slip", ready=0.5),               # now below target -> slipped
            _facet("f_flat", ready=0.4, decay_estimated=False),  # held flat -> excluded
        ]

    monkeypatch.setattr(re_mod, "facet_projections_at", fake_projections)
    monkeypatch.setattr(re_mod, "goal_report", lambda *a, **k: _report([]))
    monkeypatch.setattr(re_mod, "blueprint_weight_by_facet", lambda *a, **k: {})
    vault = _FakeVault({"lo1": _FakeLO("LO One")})
    summary = reentry_summary(vault, _FakeRepo(ended), _FakeGoal(), clock=FrozenClock(now))
    assert summary.show is True
    assert summary.gap_days == 20
    assert summary.solid_count == 1                 # f_solid only; f_flat excluded
    assert summary.slipped_count == 1               # f_slip only
    assert [f.facet_id for f in summary.slipped_top] == ["f_slip"]


# --- F7 decay pressure -------------------------------------------------------


def test_decay_pressure_crossing_day_math(monkeypatch):
    now = datetime(2026, 7, 14, tzinfo=UTC)

    # A facet that starts at 0.95 and loses 0.01/day crosses 0.8 after 15 days.
    def fake_projections(vault, repo, goal, at, *, clock=None):
        days = (at.astimezone(UTC) - now).total_seconds() / 86400
        crossing = max(0.0, 0.95 - 0.01 * days)
        stable = 0.99  # never crosses within horizon
        return [
            _facet("f_cross", ready=crossing),
            _facet("f_stable", ready=stable),
            _facet("f_flat", ready=0.3, decay_estimated=False),  # held flat
        ]

    monkeypatch.setattr(dp_mod, "facet_projections_at", fake_projections)
    vault = _FakeVault({"lo1": _FakeLO("LO One")})
    pressure = decay_pressure(vault, _FakeRepo(None), clock=FrozenClock(now))
    assert pressure.has_history is True
    assert pressure.held_flat_count == 1  # f_flat excluded from confident list
    by_id = {f.facet_id: f for f in pressure.facets}
    assert set(by_id) == {"f_cross", "f_stable"}
    assert by_id["f_cross"].crosses_in_days == 15
    assert by_id["f_stable"].crosses_in_days is None
    # Soonest crossing sorts first.
    assert pressure.facets[0].facet_id == "f_cross"


def test_decay_pressure_already_below_target_crosses_at_zero(monkeypatch):
    now = datetime(2026, 7, 14, tzinfo=UTC)

    def fake_projections(vault, repo, goal, at, *, clock=None):
        return [_facet("f_low", ready=0.5)]

    monkeypatch.setattr(dp_mod, "facet_projections_at", fake_projections)
    vault = _FakeVault({"lo1": _FakeLO("LO One")})
    pressure = decay_pressure(vault, _FakeRepo(None), clock=FrozenClock(now))
    assert pressure.facets[0].crosses_in_days == 0


# --- F5 overconfidence probe origin (§4.3) -----------------------------------


def test_overconfidence_probe_records_origin(tmp_path):
    root = Path("fixtures/linear_algebra")
    vault = load_vault(root)
    scratch = tmp_path / "state.sqlite"
    shutil.copyfile(VaultPaths(root, vault.config).sqlite_path, scratch)
    repo = Repository(scratch)
    lo_id = next(iter(vault.learning_objects))
    episode = enter_episode(
        vault, repo, lo_id, trigger="goal_diagnostic", origin="overconfidence_list"
    )
    fetched = repo.probe_episode(episode.id)
    # Origin lives in its own durable column (migration 059), not the free-form
    # target_decision blob which later target selection overwrites.
    assert fetched.origin == "overconfidence_list"
    assert fetched.trigger == "goal_diagnostic"


def test_overconfidence_probe_origin_survives_target_selection(tmp_path):
    """Driving the real target-selection flow overwrites target_decision_json but
    must not erase the origin (spec §4.3)."""

    from learnloop.services.probe_episodes import stop_diagnosing_and_teach

    root = Path("fixtures/linear_algebra")
    vault = load_vault(root)
    scratch = tmp_path / "state.sqlite"
    shutil.copyfile(VaultPaths(root, vault.config).sqlite_path, scratch)
    repo = Repository(scratch)
    lo_id = next(iter(vault.learning_objects))
    episode = enter_episode(
        vault, repo, lo_id, trigger="goal_diagnostic", origin="overconfidence_list"
    )

    # Target selection persists a typed transition decision into
    # target_decision_json (the pre-059 side-channel for origin).
    stop_diagnosing_and_teach(vault, repo, lo_id)

    fetched = repo.probe_episode(episode.id)
    assert fetched.target_decision is not None  # decision was written
    assert "origin" not in fetched.target_decision  # no reliance on the blob
    assert fetched.origin == "overconfidence_list"  # origin still durable


def test_probe_episode_without_origin_is_null(tmp_path):
    """A legacy/ordinary episode entered with no origin keeps NULL origin."""

    root = Path("fixtures/linear_algebra")
    vault = load_vault(root)
    scratch = tmp_path / "state.sqlite"
    shutil.copyfile(VaultPaths(root, vault.config).sqlite_path, scratch)
    repo = Repository(scratch)
    lo_id = next(iter(vault.learning_objects))
    episode = enter_episode(vault, repo, lo_id, trigger="initial")
    fetched = repo.probe_episode(episode.id)
    assert fetched.origin is None
    assert fetched.target_decision is None
