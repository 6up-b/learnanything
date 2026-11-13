"""What other test files use from ``tests/test_teacher_te1b_suggestions.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import socket
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.router import lesson_suggestions as LS
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import set_algorithm_version
from tests.teacher_fakes import build_teacher_vault


TAG = LATEST_ALGORITHM_VERSION
T0 = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)


def _clock(days: float = 0.0, hours: float = 0.0) -> FrozenClock:
    return FrozenClock(T0 + timedelta(days=days, hours=hours))


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(sql, params).fetchall()]


#: The synthetic vault's six LOs (``lo_det`` on determinants, the other five on the SVD concept).
LOS = ("lo_det", "lo_eigen", "lo_inner", "lo_matrices", "lo_svd_definition", "lo_vectors")


def _vault(tmp_path, *, version: str = TAG, goal: bool = True, name: str = "vault"):
    """TE1's teacher vault at TE1b's tag, with one active goal over both concepts (so all six LOs are new
    goal LOs), or no goal at all (no candidate)."""

    paths, repository = build_teacher_vault(tmp_path / name, reserved=False)
    set_algorithm_version(paths, version)
    goals = [{
        "id": "goal_la", "title": "Linear algebra", "status": "active", "priority": 0.5, "due_at": None,
        "created_at": "2026-10-01T00:00:00Z", "updated_at": "2026-10-01T00:00:00Z",
        "facet_scope": {"concepts": ["determinants_c", "singular_value_decomposition"]}, "target_recall": 0.8}]
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": goals if goal else []})
    return paths, repository


@pytest.fixture
def shown(monkeypatch):
    """The draw's uniforms: the mixture's staged component (above the floor), its pick (the highest-valued
    candidate), and the show coin at 0 (a card to act on)."""

    monkeypatch.setattr(LS, "_uniforms", lambda seed: (0.5, 0.0, 0.0))


@pytest.fixture
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("TE1b made a network call")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def _suggestion(paths, repository, clock):
    return SG.today_suggestion(load_vault(paths.root), repository, clock=clock)


def _decisions(repository):
    return _rows(repository, "SELECT * FROM router_decisions WHERE decision_kind = 'lesson_suggestion' "
                             "ORDER BY created_at, id")
