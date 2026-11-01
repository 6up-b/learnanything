"""The canonical facet writers write only what changed (followups-oct31, fix 1).

``project_canonical_facet_state`` runs on every ``SidecarContext.load`` and
``reload``. It used to DELETE both facet tables and re-INSERT every row, so a
reload with nothing new rewrote ``updated_at`` everywhere (and ``created_at`` on
capability rows) and every session left a "changed" database behind. The
writers now compare value columns per key and write nothing when the
projection matches what is stored; a changed row gets ``updated_at = now`` and
keeps its ``created_at``.
"""

from __future__ import annotations

from datetime import timedelta
import sqlite3

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.substrate.canonical_projection import project_canonical_facet_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, add_followup_item, create_placement_vault

FACET_TABLES = ("facet_recall_state", "facet_capability_evidence")
RECALL_KEY = ("facet_id", "capability_key", "practice_item_id")
CAPABILITY_KEY = ("facet_id", "capability")
TIMESTAMPS = ("created_at", "updated_at")
OLD = "2000-01-01T00:00:00Z"


def _at(minutes: float) -> FrozenClock:
    return FrozenClock(NOW + timedelta(minutes=minutes))


def _vault(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version=LATEST_ALGORITHM_VERSION)
    add_followup_item(paths.root)
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(0))
    return paths, vault, repository


def _answer(vault, repository, item_id, *, minutes, points=4.0):
    draft = AttemptDraft(
        practice_item_id=item_id, learner_answer_md="An answer.", attempt_type="independent_attempt"
    )
    grade = SelfGradeInput(criterion_points={"correctness": points}, confidence=4)
    return complete_self_graded_attempt(vault, repository, draft, grade, clock=_at(minutes))


def _rows(sqlite_path, table):
    with sqlite3.connect(sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(f"SELECT rowid AS _rowid, * FROM {table} ORDER BY rowid")]


def _snapshot(sqlite_path, tables=FACET_TABLES):
    return {table: _rows(sqlite_path, table) for table in tables}


def _keyed(rows, key):
    return {tuple(row[column] for column in key): row for row in rows}


def _values(row):
    return {name: value for name, value in row.items() if name not in TIMESTAMPS + ("_rowid",)}


class _DataVersion:
    """``PRAGMA data_version`` seen from a connection of its own: it moves
    exactly when another connection commits a change to the database file."""

    def __init__(self, sqlite_path):
        self._connection = sqlite3.connect(sqlite_path)

    def __call__(self) -> int:
        return int(self._connection.execute("PRAGMA data_version").fetchone()[0])

    def close(self) -> None:
        self._connection.close()


def _history(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, "pi_svd_define_001", minutes=1)
    _answer(vault, repository, "pi_diag_easy", minutes=2, points=1.0)
    _answer(vault, repository, "pi_svd_define_002", minutes=3)
    return paths, vault, repository


def _journal_mode(sqlite_path) -> str:
    with sqlite3.connect(sqlite_path) as connection:
        return str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower()


def _assert_second_projection_writes_nothing(tmp_path, *, expect_wal: bool):
    paths, vault, repository = _history(tmp_path)
    project_canonical_facet_state(vault, repository, clock=_at(10))
    assert (_journal_mode(paths.sqlite_path) == "wal") is expect_wal
    before = _snapshot(paths.sqlite_path)
    assert before["facet_recall_state"] and before["facet_capability_evidence"]
    data_version = _DataVersion(paths.sqlite_path)
    try:
        version = data_version()
        # A later clock: a rewrite would move every updated_at to it.
        project_canonical_facet_state(vault, repository, clock=_at(60))
        assert data_version() == version
    finally:
        data_version.close()
    assert _snapshot(paths.sqlite_path) == before


def test_a_second_projection_over_an_unchanged_ledger_writes_nothing(tmp_path):
    _assert_second_projection_writes_nothing(tmp_path, expect_wal=False)


@pytest.mark.durability
def test_a_second_projection_writes_nothing_with_production_durability_and_wal(tmp_path):
    _assert_second_projection_writes_nothing(tmp_path, expect_wal=True)


def test_a_new_attempt_moves_updated_at_only_on_the_cells_it_changed(tmp_path):
    paths, vault, repository = _history(tmp_path)
    project_canonical_facet_state(vault, repository, clock=_at(10))
    before = _snapshot(paths.sqlite_path)

    _answer(vault, repository, "pi_diag_easy", minutes=20, points=4.0)
    after = _snapshot(paths.sqlite_path)
    stamp = utc_now_iso(_at(20))

    changed = unchanged = 0
    for table, key in (("facet_recall_state", RECALL_KEY), ("facet_capability_evidence", CAPABILITY_KEY)):
        old_rows = _keyed(before[table], key)
        new_rows = _keyed(after[table], key)
        assert set(old_rows) <= set(new_rows)  # an attempt adds evidence; no cell vanishes
        for cell, new in new_rows.items():
            old = old_rows.get(cell)
            if old is None:
                assert new["updated_at"] == stamp
                continue
            assert new["created_at"] == old["created_at"], (table, cell)
            if _values(new) == _values(old):
                unchanged += 1
                assert new["updated_at"] == old["updated_at"], (table, cell)
                assert new["_rowid"] == old["_rowid"], (table, cell)
            else:
                changed += 1
                assert new["updated_at"] == stamp, (table, cell)
    # The history touches cells the new attempt does not: both kinds occur.
    assert changed and unchanged


def test_capability_rows_keep_their_created_at_across_projections(tmp_path):
    paths, vault, repository = _history(tmp_path)
    created = {
        cell: row["created_at"]
        for cell, row in _keyed(_rows(paths.sqlite_path, "facet_capability_evidence"), CAPABILITY_KEY).items()
    }
    _answer(vault, repository, "pi_diag_easy", minutes=20, points=4.0)
    project_canonical_facet_state(vault, repository, clock=_at(30))
    for cell, row in _keyed(_rows(paths.sqlite_path, "facet_capability_evidence"), CAPABILITY_KEY).items():
        if cell in created:
            assert row["created_at"] == created[cell]


def test_a_sidecar_reload_after_nothing_happened_writes_nothing_to_the_facet_tables(tmp_path, monkeypatch):
    from learnloop_sidecar.context import SidecarContext

    paths, vault, repository = _history(tmp_path)
    # Reloading must not queue model work (and never does in this test).
    monkeypatch.setattr(SidecarContext, "prepare_new_revisions", lambda self, previous: None)
    ctx = SidecarContext()
    try:
        ctx.load(paths.root, maintenance=False)
        # Mark the stored timestamps, so a rewrite cannot hide inside the
        # same wall-clock second as the first load. (A recall row's
        # created_at is projected, its first observation's time, so only a
        # capability row's is the writer's to keep.)
        with sqlite3.connect(paths.sqlite_path) as connection:
            connection.execute("UPDATE facet_recall_state SET updated_at = ?", (OLD,))
            connection.execute("UPDATE facet_capability_evidence SET created_at = ?, updated_at = ?", (OLD, OLD))
        before = _snapshot(paths.sqlite_path)
        data_version = _DataVersion(paths.sqlite_path)
        try:
            version = data_version()
            ctx.reload(maintenance=False)
            # Nothing else on this reload path writes either: the whole
            # database is unchanged, not only the facet tables.
            assert data_version() == version
        finally:
            data_version.close()
        assert _snapshot(paths.sqlite_path) == before
    finally:
        ctx.close()


# ── the repository writers on their own ─────────────────────────────────────


def _recall(facet, *, item=None, alpha=2.0, created_at="2026-01-01T00:00:00Z"):
    return {
        "facet_id": facet, "capability_key": "shared", "practice_item_id": item,
        "recall_alpha": alpha, "recall_beta": 1.0, "recall_mean": alpha / (alpha + 1.0),
        "recall_variance": 0.05, "created_at": created_at,
    }


def _capability(facet, *, mass=1.0, groups=("g1",)):
    return {
        "facet_id": facet, "capability": "recall", "direct_positive_mass": mass,
        "certification_credit": 0.5, "independent_surface_groups": list(groups),
    }


def _residual(facet, *, mean=0.4):
    return {
        "facet_id": facet, "capability": "apply", "active": True,
        "activation_reason": "closed_diagnostic_episode", "residual_alpha": 2.0,
        "residual_beta": 3.0, "residual_mean": mean, "parent_alpha": 3.0,
        "parent_beta": 2.0, "parent_mean": 0.6, "divergence": 0.2,
        "independent_groups": 2, "independent_mass": 1.5,
    }


def test_the_writer_deletes_vanished_cells_inserts_new_ones_and_updates_only_changed_ones(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    repo.replace_canonical_facet_state(
        recall_rows=[_recall("f_a"), _recall("f_a", item="pi_1"), _recall("f_b")],
        capability_rows=[_capability("f_a"), _capability("f_b")],
        algorithm_version="mvp-0.8",
        clock=_at(0),
    )
    first = _snapshot(repo.sqlite_path)
    repo.replace_canonical_facet_state(
        recall_rows=[_recall("f_a"), _recall("f_a", item="pi_1", alpha=3.0), _recall("f_c")],
        capability_rows=[_capability("f_a"), _capability("f_b", groups=("g1", "g2"))],
        algorithm_version="mvp-0.8",
        clock=_at(5),
    )
    second = _snapshot(repo.sqlite_path)
    recall_before = _keyed(first["facet_recall_state"], RECALL_KEY)
    recall_after = _keyed(second["facet_recall_state"], RECALL_KEY)
    assert set(recall_after) == {("f_a", "shared", None), ("f_a", "shared", "pi_1"), ("f_c", "shared", None)}
    assert recall_after[("f_a", "shared", None)] == recall_before[("f_a", "shared", None)]
    moved = recall_after[("f_a", "shared", "pi_1")]
    assert moved["recall_alpha"] == 3.0
    assert moved["updated_at"] == utc_now_iso(_at(5))
    assert moved["created_at"] == recall_before[("f_a", "shared", "pi_1")]["created_at"]
    assert recall_after[("f_c", "shared", None)]["updated_at"] == utc_now_iso(_at(5))

    cap_before = _keyed(first["facet_capability_evidence"], CAPABILITY_KEY)
    cap_after = _keyed(second["facet_capability_evidence"], CAPABILITY_KEY)
    assert cap_after[("f_a", "recall")] == cap_before[("f_a", "recall")]
    assert cap_after[("f_b", "recall")]["independent_surface_groups_json"] == '["g1","g2"]'
    assert cap_after[("f_b", "recall")]["updated_at"] == utc_now_iso(_at(5))
    # A capability row carries no created_at of its own: the stored one stays.
    assert cap_after[("f_b", "recall")]["created_at"] == utc_now_iso(_at(0))


def test_a_projected_recall_created_at_is_still_written_when_it_moves(tmp_path):
    """Recall rows carry the first observation's time; a fresh rebuild writes
    that value, so the incremental writer must not keep a stale one."""

    repo = Repository(tmp_path / "state.sqlite")
    repo.replace_canonical_facet_state(
        recall_rows=[_recall("f_a", created_at="2026-01-01T00:00:00Z")], capability_rows=[],
        algorithm_version="mvp-0.8", clock=_at(0),
    )
    repo.replace_canonical_facet_state(
        recall_rows=[_recall("f_a", created_at="2026-01-02T00:00:00Z")], capability_rows=[],
        algorithm_version="mvp-0.8", clock=_at(5),
    )
    (row,) = _rows(repo.sqlite_path, "facet_recall_state")
    assert row["created_at"] == "2026-01-02T00:00:00Z"
    assert row["updated_at"] == utc_now_iso(_at(5))


def test_an_algorithm_version_change_rewrites_the_rows_it_stamps(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    for version, minutes in (("mvp-0.7", 0), ("mvp-0.8", 5)):
        repo.replace_canonical_facet_state(
            recall_rows=[_recall("f_a")], capability_rows=[_capability("f_a")],
            algorithm_version=version, clock=_at(minutes),
        )
    snapshot = _snapshot(repo.sqlite_path)
    for table in FACET_TABLES:
        (row,) = snapshot[table]
        assert row["algorithm_version"] == "mvp-0.8"
        assert row["updated_at"] == utc_now_iso(_at(5))


def test_two_projected_rows_for_one_cell_are_refused(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    with pytest.raises(sqlite3.IntegrityError):
        repo.replace_canonical_facet_state(
            recall_rows=[_recall("f_a"), _recall("f_a", alpha=3.0)], capability_rows=[],
            algorithm_version="mvp-0.8",
        )


def test_the_residual_writer_writes_nothing_when_nothing_changed(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    repo.replace_capability_residual_state(
        rows=[_residual("f_a"), _residual("f_b")], algorithm_version="mvp-0.8", clock=_at(0)
    )
    first = _rows(repo.sqlite_path, "capability_residual_state")
    data_version = _DataVersion(repo.sqlite_path)
    try:
        version = data_version()
        repo.replace_capability_residual_state(
            rows=[_residual("f_a"), _residual("f_b")], algorithm_version="mvp-0.8", clock=_at(5)
        )
        assert data_version() == version
    finally:
        data_version.close()
    assert _rows(repo.sqlite_path, "capability_residual_state") == first

    repo.replace_capability_residual_state(
        rows=[_residual("f_a", mean=0.45)], algorithm_version="mvp-0.8", clock=_at(9)
    )
    (row,) = _rows(repo.sqlite_path, "capability_residual_state")
    assert row["facet_id"] == "f_a" and row["residual_mean"] == 0.45
    assert row["updated_at"] == utc_now_iso(_at(9))
    assert row["created_at"] == utc_now_iso(_at(0))
