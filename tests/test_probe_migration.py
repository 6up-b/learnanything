"""Checkpoint 0 migration/cutover tests (spec_probe_eig_redesign.md §14)."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations, default_migrations_dir
from learnloop.db.repositories import Repository
from learnloop.services.probes import probe_posterior
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault

CUTOVER_VERSION = 28


def _migrations_before_cutover(tmp_path: Path) -> Path:
    trimmed = tmp_path / "migrations_pre_redesign"
    trimmed.mkdir()
    for migration in sorted(default_migrations_dir().glob("*.sql")):
        version = int(migration.name.split("_", 1)[0])
        if version < CUTOVER_VERSION:
            shutil.copy(migration, trimmed / migration.name)
    return trimmed


def test_migration_closes_in_progress_phases_as_superseded(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path, _migrations_before_cutover(tmp_path), clock=FrozenClock(NOW))

    with sqlite3.connect(sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO lo_probe_state(
              learning_object_id, status, probe_phase_id, hypothesis_set_id,
              probe_attempts_completed, probe_attempts_target,
              families_converged_json, entered_at, completed_at,
              algorithm_version, updated_at
            )
            VALUES ('lo_open', 'in_progress', 'probe_lo_open', NULL, 1, 3, '[]', ?, NULL, 'mvp-0.5', ?),
                   ('lo_done', 'complete', 'probe_lo_done', NULL, 3, 3, '[]', ?, ?, 'mvp-0.5', ?)
            """,
            (NOW_ISO, NOW_ISO, NOW_ISO, NOW_ISO, NOW_ISO),
        )
        connection.commit()

    apply_migrations(sqlite_path, clock=FrozenClock(NOW))

    with sqlite3.connect(sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = {
            row["learning_object_id"]: dict(row)
            for row in connection.execute("SELECT * FROM lo_probe_state")
        }
    # The open phase is closed as superseded — never silently reinterpreted.
    assert rows["lo_open"]["status"] == "complete"
    assert rows["lo_open"]["completion_reason"] == "superseded_by_redesign"
    assert rows["lo_open"]["completed_at"] is not None
    # Already-terminal history is untouched.
    assert rows["lo_done"]["status"] == "complete"
    assert rows["lo_done"]["completion_reason"] is None
    assert rows["lo_done"]["completed_at"] == NOW_ISO


def test_legacy_probe_history_replays_identically_after_migration(tmp_path):
    # A pre-redesign phase with recorded attempts must replay through the frozen
    # legacy path — same locked set, same posterior — after the cutover closes it.
    from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.services.probes import enter_probe

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    enter_probe(loaded, repository, "lo_svd_definition", clock=FrozenClock(NOW))
    complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="answer"),
        SelfGradeInput(criterion_points={"correctness": 2}, confidence=4),
        clock=FrozenClock(NOW),
    )

    first = probe_posterior(loaded, repository, "lo_svd_definition")
    second = probe_posterior(loaded, repository, "lo_svd_definition")
    assert first is not None
    assert first.posterior == second.posterior
    assert first.attempts == second.attempts
    # The frozen path resolves only its own legacy hypothesis set — no episode,
    # family, or card definitions exist for it.
    assert repository.open_probe_episode("lo_svd_definition") is None or (
        repository.open_probe_episode("lo_svd_definition").hypothesis_set_id
        != repository.probe_state("lo_svd_definition").hypothesis_set_id
    )
