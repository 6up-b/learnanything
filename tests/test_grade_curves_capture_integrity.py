"""L4-2's review fix round (``docs/reviews/algorithm-mvp-0.71.md``, "Review fix round"): each test failed before its fix.

A grade records its curve whatever tag the writing process loaded. A process holding the predecessor's config (the
desktop sidecar, the phone host, a CLI grade, a background job) can commit after another process completed the
upgrade's freeze; deciding by its cached tag left that epoch uncaptured for good. No replacing insert can delete a
capture behind the ledger's guards, under its key or under its rowid.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

import pytest

from learnloop.algorithm_versions import LESSON_WEIGHT_CURVES_ALGORITHM_VERSION as TAG, SUCCESSOR_CHAIN
from learnloop.ops import upgrades
from learnloop.vault.loader import load_vault

from tests.teacher_fakes import build_teacher_vault
from tests.teacher_te1_review_fixes_helpers import _cold, _rows

T = datetime(2026, 11, 1, 9, tzinfo=UTC)
BEFORE = SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1]
CURVES = "SELECT attempt_id, epoch_key, provenance, algorithm_version FROM attempt_grade_curves ORDER BY attempt_id"


def test_a_grade_written_with_the_predecessors_config_records_its_curve(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault", version=BEFORE)
    graded = _cold(paths, repository, "pi_eig_1", T)
    (row,) = _rows(repository, CURVES)
    assert (row[0], row[2], row[3]) == (graded.attempt_id, "graded", BEFORE)


def test_a_grade_committed_after_another_process_upgraded_keeps_its_curve(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault", version=BEFORE)
    stale = load_vault(paths.root)  # a process that loaded the predecessor's config before the upgrade
    upgrades.upgrade(paths.root, to=TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    graded = _cold(paths, repository, "pi_eig_1", T, vault=stale)
    assert [(r[0], r[2]) for r in _rows(repository, CURVES)] == [(graded.attempt_id, "graded")]


def test_no_replacing_insert_can_remove_a_capture(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault", version=TAG)
    graded = _cold(paths, repository, "pi_eig_1", T)
    with sqlite3.connect(paths.sqlite_path) as connection:
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute(
                "INSERT OR REPLACE INTO attempt_grade_curves(rowid, attempt_id, epoch_key, grading_revision, item_a, "
                "item_b, algorithm_version, provenance) SELECT rowid, attempt_id, 'no_evidence', NULL, 1.0, 0.0, "
                "algorithm_version, 'graded' FROM attempt_grade_curves")
    assert [r[0] for r in _rows(repository, CURVES)] == [graded.attempt_id]
