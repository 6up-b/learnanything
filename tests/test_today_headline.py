"""Daily-loop DL1 §6.7 (D7): the Today headline's classes.

Each active LO is in exactly one class, in order: assumed, demonstrated (the
whole LO, never part of it), learning (direct evidence), untested. One of two
required capabilities demonstrated on a facet is learning; one of two facets
fully demonstrated is learning; every facet fully demonstrated is
demonstrated; a blueprint LO with all components but an integration gap is
learning.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from learnloop.clock import FrozenClock
from learnloop.daily_plan import headline as headline_module
from learnloop.daily_plan.headline import classify_learning_objects, today_headline
from learnloop.db.repositories import Repository
from learnloop.goals.certification import DEMONSTRATED_CREDIT
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from tests.test_km3_projections import COMP_A, COMP_B, INTEG, LO_ID, NOW, _attempt, build_blueprint_vault


def _cell(facet, capability, *, credit=0.0, direct=0.0):
    return SimpleNamespace(
        facet_id=facet, capability=capability, certification_credit=credit,
        direct_positive_mass=direct, direct_negative_mass=0.0,
    )


class _Repo:
    def __init__(self, cells):
        self._cells = cells

    def facet_capability_evidence_all(self):
        return list(self._cells)

    def mastery_states(self):
        return {}


def _vault(los):
    return SimpleNamespace(
        learning_objects={lo.id: lo for lo in los},
        canonical_facet_id=lambda facet: facet,
        config=SimpleNamespace(algorithms=SimpleNamespace(algorithm_version="mvp-0.14"), placement=SimpleNamespace(enabled=False)),
    )


def _lo(lo_id):
    return SimpleNamespace(id=lo_id, status="active", blueprints=[])


@pytest.fixture
def capability_world(monkeypatch):
    facets = {"lo_one_cap": ["f1"], "lo_two_facets": ["f2", "f3"], "lo_full": ["f4", "f5"], "lo_none": ["f6"]}
    required = {"f1": ("retrieval", "procedure_execution"), "f2": ("retrieval",), "f3": ("retrieval",), "f4": ("retrieval",), "f5": ("procedure_execution",), "f6": ("retrieval",)}
    monkeypatch.setattr(headline_module, "scope_facets", lambda _v, lo_id, _r: set(facets[lo_id]))
    monkeypatch.setattr(headline_module, "required_capabilities_for_facet", lambda _v, _lo, facet: (required[facet], False))
    monkeypatch.setattr(headline_module, "is_canonical_state_vault", lambda _v: True)
    monkeypatch.setattr(headline_module, "placement_active", lambda _v: False)
    cells = [
        _cell("f1", "retrieval", credit=DEMONSTRATED_CREDIT, direct=2.0),  # one of two capabilities
        _cell("f2", "retrieval", credit=DEMONSTRATED_CREDIT, direct=2.0),  # one of two facets
        _cell("f4", "retrieval", credit=DEMONSTRATED_CREDIT, direct=2.0),
        _cell("f5", "procedure_execution", credit=DEMONSTRATED_CREDIT, direct=2.0),
    ]
    vault = _vault([_lo(lo) for lo in facets])
    return vault, _Repo(cells)


def test_partial_demonstration_is_learning_and_whole_is_demonstrated(capability_world):
    vault, repository = capability_world
    classes = classify_learning_objects(vault, repository)
    assert classes == {
        "lo_full": "demonstrated",
        "lo_none": "untested",
        "lo_one_cap": "learning",
        "lo_two_facets": "learning",
    }


def test_each_lo_is_in_exactly_one_class(capability_world):
    vault, repository = capability_world
    classes = classify_learning_objects(vault, repository)
    assert set(classes) == set(vault.learning_objects)
    assert set(classes.values()) <= {"assumed", "demonstrated", "learning", "untested"}


def test_a_blueprint_lo_with_an_integration_gap_is_learning(tmp_path):
    # The KM3 composite-LO vault (mvp-0.7), whose certification the headline
    # reuses unchanged through lo_certification.
    paths = build_blueprint_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    assert classify_learning_objects(vault, repository)[LO_ID] == "untested"
    for _ in range(3):
        _attempt(vault, repository, "pi_comp_a", 4)
        _attempt(vault, repository, "pi_comp_b", 4)
    # All components, but the integration facet is a gap: learning, not demonstrated.
    assert classify_learning_objects(vault, repository)[LO_ID] == "learning"
    _attempt(vault, repository, "pi_integrated", 4)
    assert classify_learning_objects(vault, repository)[LO_ID] == "demonstrated"


def test_assumed_comes_first_and_is_omitted_before_placement(tmp_path):
    from learnloop.placement.decisions import record_self_report
    from tests.helpers import create_daily_plan_vault

    paths = create_daily_plan_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    record_self_report(vault, repository, report="know_this", learning_object_ids=["lo_diag"])
    now = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
    line = today_headline(vault, repository, now=now)
    assert line["counts"]["assumed"] == 1 and line["show_assumed"] is True
    assert " assumed · " in line["line"]
    # Before Phase 6 (placement off) the class is omitted rather than shown as 0.
    off = create_daily_plan_vault(tmp_path / "off", plan_toml="[placement]\nenabled = false\n")
    off_vault = load_vault(off.root)
    no_assumed = today_headline(off_vault, Repository(off.sqlite_path), now=now)
    assert "assumed" not in no_assumed["counts"] and "assumed" not in no_assumed["line"]


def test_expected_recall_is_a_labelled_model_estimate(tmp_path):
    from tests.daily_plan_fakes import seed_due
    from tests.helpers import create_daily_plan_vault

    paths = create_daily_plan_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    now = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
    assert today_headline(vault, repository, now=now)["expected_recall"] is None
    seed_due(repository, "pi_svd_define_001", due=now, last=now, stability=10.0)
    line = today_headline(vault, repository, now=now)
    assert line["expected_recall"] == pytest.approx(1.0)
    assert line["expected_recall_tooltip"] == "a model estimate, not a test"
    assert line["line"].endswith("expected recall today 100%")
