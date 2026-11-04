"""RO0 row 11 (spec_router_objective_v1 §4): a goal's lifecycle, detected at load from the vault's YAML."""

from __future__ import annotations

import sqlite3

from learnloop.db.repositories import Repository
from learnloop.router_objective import goal_lifecycle as GL
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml
from learnloop_sidecar.context import SidecarContext
from tests.helpers import NOW_ISO, append_config_toml, create_basic_vault

GOAL = {"id": "g1", "title": "A goal", "status": "active", "priority": 0.5, "due_at": "2026-12-01T00:00:00Z",
        "created_at": "2026-01-01T00:00:00Z", "updated_at": NOW_ISO,
        "facet_scope": {"concepts": ["singular_value_decomposition"]}, "target_recall": 0.8}


def _write(paths, *goals):
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": list(goals)})


def _setup(tmp_path, off=False):
    paths = create_basic_vault(tmp_path / "vault")
    if off:
        append_config_toml(paths.root, "[router_objective]\nreceipts = false\n")
    _write(paths, GOAL)
    return paths, Repository(paths.sqlite_path)


def _rows(repository):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM goal_lifecycle_events ORDER BY created_at, id")]


def _sweep(paths, repository):
    return GL.sweep(load_vault(paths.root), repository)


def test_a_goal_is_seen_once_with_its_own_start(tmp_path):
    paths, repository = _setup(tmp_path)
    assert _sweep(paths, repository) == 1
    assert _sweep(paths, repository) == 0, "unchanged: nothing"
    [row] = _rows(repository)
    assert (row["goal_id"], row["event"], row["status"], row["due_at"], row["occurred_at"]) == (
        "g1", GL.CREATED, "active", GOAL["due_at"], GOAL["created_at"])


def test_a_pause_a_new_date_a_resumption_and_a_completion(tmp_path):
    paths, repository = _setup(tmp_path)
    _sweep(paths, repository)
    _write(paths, {**GOAL, "status": "paused"})
    _sweep(paths, repository)
    _write(paths, {**GOAL, "status": "paused", "due_at": "2027-01-01T00:00:00Z"})
    _sweep(paths, repository)
    _write(paths, {**GOAL, "status": "active", "due_at": "2027-01-01T00:00:00Z"})
    _sweep(paths, repository)
    _write(paths, {**GOAL, "status": "completed", "due_at": "2027-01-01T00:00:00Z"})
    _sweep(paths, repository)
    rows = _rows(repository)
    assert [row["event"] for row in rows] == [GL.CREATED, "paused", GL.DATE_CHANGED, GL.RESUMED, "completed"]
    assert (rows[2]["previous_due_at"], rows[2]["due_at"]) == (GOAL["due_at"], "2027-01-01T00:00:00Z")
    assert (rows[1]["previous_status"], rows[1]["status"]) == ("active", "paused")
    assert all(row["reason"] == GL.SEEN_AT_LOAD for row in rows), "the YAML gives no reason: says what was seen"


def test_status_and_date_changed_together_are_two_events(tmp_path):
    paths, repository = _setup(tmp_path)
    _sweep(paths, repository)
    _write(paths, {**GOAL, "status": "expired", "due_at": None})
    assert _sweep(paths, repository) == 2
    assert [row["event"] for row in _rows(repository)][1:] == ["expired", GL.DATE_CHANGED]


def test_a_removal_says_whether_the_goal_was_active_and_a_return_is_a_new_goal(tmp_path):
    paths, repository = _setup(tmp_path)
    _sweep(paths, repository)
    _write(paths)
    _sweep(paths, repository)
    assert _sweep(paths, repository) == 0, "removed once"
    _write(paths, GOAL)
    _sweep(paths, repository)
    rows = _rows(repository)
    assert [row["event"] for row in rows] == [GL.CREATED, GL.REMOVED, GL.CREATED]
    assert rows[1]["reason"] == "removed_while_active"


def test_the_sidecar_sweeps_at_load(tmp_path):
    paths, repository = _setup(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root, maintenance=False)
    assert [row["event"] for row in _rows(repository)] == [GL.CREATED]
    _write(paths, {**GOAL, "status": "paused"})
    ctx.reload(maintenance=False)
    assert [row["event"] for row in _rows(repository)] == [GL.CREATED, "paused"]


def test_off_nothing_is_written(tmp_path):
    paths, repository = _setup(tmp_path, off=True)
    assert _sweep(paths, repository) == 0
    assert _rows(repository) == []


def test_a_refused_row_rolls_back_alone(tmp_path, monkeypatch):
    paths, repository = _setup(tmp_path)
    vault = load_vault(paths.root)

    def broken(*_args, **_kwargs):
        raise sqlite3.OperationalError("no")

    monkeypatch.setattr(GL.store, "latest_goal_events", broken)
    assert GL.sweep(vault, repository) == 0


