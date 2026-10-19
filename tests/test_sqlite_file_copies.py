"""Every byte-level file copy in the repository is an audited SQLite copier.

In WAL mode a committed transaction can live in ``state.sqlite-wal`` until a
checkpoint, so ``shutil.copyfile``/``copy2``/``copytree`` of a live database,
or of a directory holding one, can drop acknowledged commits or pair a main
file with a ``-wal`` from another moment.  Live databases are copied with
:mod:`learnloop.db.copies` (SQLite's backup API).  This test finds every copy
call under ``src/``, ``tests/`` and ``scripts/`` and fails on any site that is
not listed below with the reason it is safe, so a new copier is reviewed
before it lands.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SCANNED_ROOTS = ("src", "tests", "scripts")
COPY_CALL = re.compile(r"\b(?:copyfile|copy2|copytree|shutil\.copy)\s*\(")

# Reasons a byte copy cannot capture a live WAL database.
_TRACKED_FIXTURE = (
    "copies a tracked fixture vault or database; tracked fixtures stay in "
    "rollback mode with no companions (test_tracked_fixture_databases_are_rollback_mode)"
)
_MIGRATION_SQL = "copies migration .sql files, not databases"

AUDITED_COPIERS: dict[str, tuple[int, str]] = {
    "src/learnloop/db/copies.py": (
        1,
        "copy_tree_without_databases: copytree with every database and companion file ignored",
    ),
    "tests/test_activity_backfill.py": (1, _TRACKED_FIXTURE),
    "tests/test_collection_dataset.py": (1, _TRACKED_FIXTURE),
    "tests/test_doctor.py": (1, _TRACKED_FIXTURE),
    "tests/test_exam_seeding.py": (1, _MIGRATION_SQL),
    "tests/test_goal_decay_projection.py": (1, _TRACKED_FIXTURE),
    "tests/test_goal_scope_material.py": (1, _TRACKED_FIXTURE),
    "tests/test_graph_editor_reads.py": (1, _TRACKED_FIXTURE),
    "tests/test_judge_routes.py": (2, _MIGRATION_SQL),
    "tests/test_learner_read_model_pinning.py": (1, _TRACKED_FIXTURE),
    "tests/test_migrate_fresh.py": (1, _TRACKED_FIXTURE),
    "tests/test_migrations.py": (
        15,
        "copies migration .sql files and tracked fixture databases",
    ),
    "tests/test_model_call_receipt_owners.py": (1, _MIGRATION_SQL),
    "tests/test_probe_migration.py": (1, _MIGRATION_SQL),
    "tests/test_question_promotions.py": (1, _MIGRATION_SQL),
    "tests/test_rebuild_orchestrator.py": (1, _TRACKED_FIXTURE),
    "tests/test_reader_rw2b_fix10.py": (
        1,
        "copies a Python helper script (rw2b_fix10_base_sequence.py) into an archived code tree, not a database",
    ),
    "tests/test_reader_rw2b_fix11.py": (
        1,
        "copies a Python helper script (rw2b_fix11_base_sequence.py) into an archived code tree, not a database",
    ),
    "tests/test_receipt_derivation.py": (2, _TRACKED_FIXTURE),
    "tests/test_receipt_exactness.py": (1, _TRACKED_FIXTURE),
    "tests/test_shadow_rebuild.py": (1, _TRACKED_FIXTURE),
    "tests/test_sidecar_contract.py": (5, _TRACKED_FIXTURE),
    "tests/test_sqlite_wal.py": (
        1,
        "plants a -wal from another database to prove fresh creation discards orphans",
    ),
    "tests/test_sqlite_wal_lifecycle.py": (
        1,
        "byte-copies a live WAL database on purpose to show the commit it loses",
    ),
    "tests/test_teach_back.py": (1, _MIGRATION_SQL),
    "tests/test_today_surfaces.py": (3, _TRACKED_FIXTURE),
}


def _copy_calls() -> Counter[str]:
    calls: Counter[str] = Counter()
    for root in SCANNED_ROOTS:
        for path in sorted((REPOSITORY / root).rglob("*.py")):
            relative = path.relative_to(REPOSITORY).as_posix()
            if relative == "tests/test_sqlite_file_copies.py":
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.lstrip().startswith("#"):
                    continue
                calls[relative] += len(COPY_CALL.findall(line))
    return +calls


def test_every_file_copy_site_is_an_audited_sqlite_copier():
    found = _copy_calls()
    unaudited = {
        path: count
        for path, count in found.items()
        if AUDITED_COPIERS.get(path, (0, ""))[0] != count
    }
    stale = sorted(path for path in AUDITED_COPIERS if path not in found)

    assert not unaudited, (
        "New or changed file copies (path: calls found). A database that may "
        "be live must be copied with learnloop.db.copies; then record the "
        f"audited count and reason in AUDITED_COPIERS: {unaudited}"
    )
    assert not stale, f"AUDITED_COPIERS lists files without copy calls: {stale}"
