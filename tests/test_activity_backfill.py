"""P0.1 activity-substrate backfill (spec_p0_measurement_correctness §7.1, §9.6)."""

from __future__ import annotations

import shutil
from pathlib import Path


from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.substrate.compat.activity_backfill import backfill_activity_substrate
from learnloop.vault.loader import load_vault
from learnloop.vault.repository import open_vault_repository

from tests.helpers import NOW
from tests.owner_vaults import owner_vault, owner_vaults

# A backup-API copy in the owner_vaults lane since S0 (tests/owner_vaults.py).
FIXTURE_VAULT = owner_vault("linear_algebra")
CLOCK = FrozenClock(NOW)


def _copy_fixture(tmp_path) -> Path:
    """Copy the fixture vault so the backfill never mutates it in place (§9.6)."""

    dest = tmp_path / "la"
    shutil.copytree(FIXTURE_VAULT, dest)
    return dest


def _table_counts(repo: Repository) -> dict[str, int]:
    tables = (
        "activity_families",
        "activity_family_versions",
        "activity_cards",
        "activity_card_versions",
        "activity_surfaces",
        "activity_administrations",
        "activity_exposure_events",
        "activity_observations",
    )
    with connect(repo.sqlite_path) as connection:
        return {t: connection.execute(f"SELECT COUNT(*) n FROM {t}").fetchone()["n"] for t in tables}


def _hashes(repo: Repository) -> tuple[list, list]:
    with connect(repo.sqlite_path) as connection:
        cards = [
            r["card_contract_hash"]
            for r in connection.execute(
                "SELECT card_contract_hash FROM activity_card_versions ORDER BY card_contract_hash"
            )
        ]
        surfaces = [
            r["surface_hash"]
            for r in connection.execute(
                "SELECT surface_hash FROM activity_surfaces ORDER BY surface_hash"
            )
        ]
    return cards, surfaces


@owner_vaults
def test_backfill_populates_substrate_from_fixture(tmp_path):
    vault_root = _copy_fixture(tmp_path)
    vault = load_vault(vault_root)
    repo = open_vault_repository(vault_root, vault_root / "state.sqlite")

    report = backfill_activity_substrate(vault, repo, clock=CLOCK)

    assert report.practice_items == len(vault.practice_items)
    # The fixture is intentionally a partially upgraded vault: projection
    # rollout has already materialized some observations while the remainder
    # still need the compatibility backfill. Completeness is the sum of rows
    # replayed now and rows found from an earlier replay, not just new writes.
    assert report.attempts_replayed + report.attempts_skipped_existing == len(
        repo.list_all_attempts()
    )
    counts = _table_counts(repo)
    # The substrate also contains probe-presentation administrations and
    # non-attempt observations. Assert attempt coverage directly rather than
    # equating whole-table row counts with the legacy-attempt count.
    with connect(repo.sqlite_path) as connection:
        missing = connection.execute(
            """
            SELECT a.id
              FROM practice_attempts a
              LEFT JOIN activity_observations o ON o.attempt_id = a.id
             WHERE o.id IS NULL
            """
        ).fetchall()
    assert missing == []
    assert counts["activity_administrations"] >= len(repo.list_all_attempts())
    assert counts["activity_observations"] >= len(repo.list_all_attempts())
    # Every attempt gets a synthetic administration + observation.
    assert counts["activity_families"] >= report.practice_items


@owner_vaults
def test_backfill_is_idempotent_on_fixture_copy(tmp_path):
    vault_root = _copy_fixture(tmp_path)
    vault = load_vault(vault_root)
    repo = open_vault_repository(vault_root, vault_root / "state.sqlite")

    backfill_activity_substrate(vault, repo, clock=CLOCK)
    counts_1 = _table_counts(repo)
    card_hashes_1, surface_hashes_1 = _hashes(repo)

    second = backfill_activity_substrate(vault, repo, clock=CLOCK)
    counts_2 = _table_counts(repo)
    card_hashes_2, surface_hashes_2 = _hashes(repo)

    assert counts_1 == counts_2  # no new rows on re-run
    assert card_hashes_1 == card_hashes_2  # identical content-addressed hashes
    assert surface_hashes_1 == surface_hashes_2
    assert second.attempts_replayed == 0
    assert second.attempts_skipped_existing == len(repo.list_all_attempts())


@owner_vaults
def test_backfill_render_once_per_shared_surface(tmp_path):
    """Multiple attempts on one item share a surface; only one 'rendered' exposure."""

    vault_root = _copy_fixture(tmp_path)
    vault = load_vault(vault_root)
    repo = open_vault_repository(vault_root, vault_root / "state.sqlite")
    backfill_activity_substrate(vault, repo, clock=CLOCK)

    with connect(repo.sqlite_path) as connection:
        over_rendered = connection.execute(
            """
            SELECT surface_id, COUNT(*) n FROM activity_exposure_events
             WHERE kind = 'rendered' GROUP BY surface_id HAVING n > 1
            """
        ).fetchall()
    assert over_rendered == []  # the render-once index holds across shared surfaces


@owner_vaults
def test_diagnostic_probe_attempts_reuse_shared_surface_hash(tmp_path):
    """A diagnostic-probe attempt's adapter shares the practice surface_hash, so
    the shared ledger cannot manufacture novelty (§7.1 step 1)."""

    vault_root = _copy_fixture(tmp_path)
    vault = load_vault(vault_root)
    repo = open_vault_repository(vault_root, vault_root / "state.sqlite")
    backfill_activity_substrate(vault, repo, clock=CLOCK)

    with connect(repo.sqlite_path) as connection:
        # A surface_hash carried by >1 distinct card version (across purposes)
        # proves the diagnostic adapter shares the EXACT hash with its default
        # practice surface -- the shared ledger cannot manufacture novelty.
        shared = connection.execute(
            """
            SELECT surface_hash, COUNT(DISTINCT card_version_id) versions
              FROM activity_surfaces
             GROUP BY surface_hash HAVING versions > 1
            """
        ).fetchall()
    assert shared, "expected at least one surface_hash reused across card versions/purposes"


@owner_vaults
def test_backfill_marks_unverifiable_for_missing_item(tmp_path):
    """An attempt whose item is gone yields a placeholder surface marked
    legacy_surface_unverifiable (§7.1 step 4)."""

    vault_root = _copy_fixture(tmp_path)
    vault = load_vault(vault_root)
    repo = open_vault_repository(vault_root, vault_root / "state.sqlite")

    # Seed a historical attempt referencing a practice item that is not in the vault.
    with connect(repo.sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts(
              id, practice_item_id, learning_object_id, practice_mode,
              attempt_type, hints_used, created_at
            )
            VALUES ('att_ghost', 'pi_deleted_item', 'lo_svd_definition', 'short_answer',
                    'independent_attempt', 0, '2026-05-10T09:00:00Z')
            """
        )
        connection.commit()

    backfill_activity_substrate(vault, repo, clock=CLOCK)

    with connect(repo.sqlite_path) as connection:
        surface = connection.execute(
            """
            SELECT s.legacy_surface_unverifiable
              FROM activity_surfaces s
             WHERE s.legacy_practice_item_id = 'pi_deleted_item'
            """
        ).fetchone()
        observation = connection.execute(
            "SELECT COUNT(*) n FROM activity_observations WHERE attempt_id = 'att_ghost'"
        ).fetchone()
    assert surface is not None
    assert surface["legacy_surface_unverifiable"] == 1
    assert observation["n"] == 1  # replay preserved


@owner_vaults
def test_backfill_logs_attempt_duration_interaction_events(tmp_path):
    """Where a legacy attempt carries a latency, an attempt_duration interaction
    event is logged (§3.8, 'log now, model later')."""

    vault_root = _copy_fixture(tmp_path)
    _assert_backfill_logs_the_duration(load_vault(vault_root),
                                       open_vault_repository(vault_root, vault_root / "state.sqlite"))


def test_backfill_logs_attempt_duration_for_a_pre_substrate_attempt_of_a_live_vault(tmp_path):
    """The owner-vault test's shape on a synthetic vault (FR3-6's boundary): every attempt here was written live, so
    one is made history from before the substrate by the stored facts the boundary reads. Deleting its observation
    alone (the earlier setup) left its live administration, so it was after the substrate began and the backfill,
    rightly, logged nothing for it."""

    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.substrate.state_sync import sync_vault_state
    from datetime import timedelta

    from tests.helpers import create_placement_vault

    paths = create_placement_vault(tmp_path / "vault")
    vault, repo = load_vault(paths.root), Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=CLOCK)
    for minutes, item in zip((0, 10), sorted(vault.practice_items)[:2], strict=True):
        complete_self_graded_attempt(vault, repo, AttemptDraft(item, "An answer."),
                                     SelfGradeInput({"correctness": 3}, 3),
                                     clock=FrozenClock(NOW + timedelta(minutes=minutes)))
    _assert_backfill_logs_the_duration(vault, repo)


def _assert_backfill_logs_the_duration(vault, repo) -> None:
    # Give one attempt a recorded latency so the duration path is exercised. It must be history from before the
    # substrate, and these vaults hold none (every answer since the substrate writes its administration and
    # observation live), so the earliest one is made so by the stored facts the backfill's boundary reads
    # (``activity_backfill.substrate_began_at``: the first administration written live, ``legacy_backfilled = 0``):
    # its observation and its own duration event go, and every administration written live at or before it (its
    # own included, which later answers to the same open item can share, so none is deleted) is marked as the
    # backfill marks what it reconstructs. Before (FR3-6), deleting its observation alone left its live
    # administration, so it was after the substrate began and the backfill rightly logged nothing for it.
    from learnloop.substrate.compat.activity_backfill import predates_substrate, substrate_began_at

    with connect(repo.sqlite_path) as connection:
        target, created_at = connection.execute(
            "SELECT id, created_at FROM practice_attempts ORDER BY created_at, id LIMIT 1").fetchone()
        connection.execute("PRAGMA foreign_keys = OFF")  # this copy only: later rows name the observation
        connection.execute("DELETE FROM activity_observations WHERE attempt_id = ?", (target,))
        connection.execute("DELETE FROM interaction_events WHERE attempt_id = ?", (target,))
        connection.execute("UPDATE activity_administrations SET legacy_backfilled = 1 "
                           "WHERE legacy_backfilled = 0 AND created_at <= ?", (created_at,))
        connection.execute("UPDATE practice_attempts SET latency_seconds = 37 WHERE id = ?", (target,))
        connection.commit()
    assert predates_substrate(created_at, substrate_began_at(repo))

    backfill_activity_substrate(vault, repo, clock=CLOCK)

    events = repo.interaction_events_for_attempt(target)
    assert len(events) == 1
    assert events[0]["kind"] == "attempt_duration"
    assert events[0]["attempt_duration_ms"] == 37000


def _history_with_diagnostics_first(tmp_path):
    """Three practice answers to three items (t0, t10, t20), all written live, then reshaped by the stored facts into
    an older vault's: the first two answers lost their observation and duration event (the practice writer had not
    begun recording them; their administrations are marked as the backfill marks its own), and a diagnostic
    administration was written live at t5, before the practice writer's first live observation (the t20 answer's).
    The t10 answer carries a recorded latency."""

    from datetime import timedelta

    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.substrate.state_sync import sync_vault_state
    from tests.helpers import create_placement_vault

    paths = create_placement_vault(tmp_path / "vault")
    vault, repo = load_vault(paths.root), Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=CLOCK)
    for minutes, item in zip((0, 10, 20), sorted(vault.practice_items)[:3], strict=True):
        complete_self_graded_attempt(vault, repo, AttemptDraft(item, "An answer."),
                                     SelfGradeInput({"correctness": 3}, 3),
                                     clock=FrozenClock(NOW + timedelta(minutes=minutes)))
    with connect(repo.sqlite_path) as connection:
        attempts = connection.execute("SELECT id, created_at FROM practice_attempts ORDER BY created_at, id").fetchall()
        legacy = [row[0] for row in attempts[:2]]
        marks = ", ".join("?" for _ in legacy)
        administrations = [row[0] for row in connection.execute(
            f"SELECT administration_id FROM activity_observations WHERE attempt_id IN ({marks})", legacy)]
        connection.execute("PRAGMA foreign_keys = OFF")  # this copy only: later rows name the observations
        connection.execute(f"DELETE FROM activity_observations WHERE attempt_id IN ({marks})", legacy)
        connection.execute(f"DELETE FROM interaction_events WHERE attempt_id IN ({marks})", legacy)
        connection.execute(f"UPDATE activity_administrations SET legacy_backfilled = 1 WHERE id IN "
                           f"({', '.join('?' for _ in administrations)})", administrations)
        connection.execute("UPDATE practice_attempts SET latency_seconds = 37 WHERE id = ?", (legacy[1],))
        # The diagnostic writer's live administration at t5 (a copy of the first answer's, renamed and re-dated).
        columns = [row[1] for row in connection.execute("PRAGMA table_info(activity_administrations)")]
        chosen = ", ".join("'adm_live_diagnostic'" if c == "id" else "'diagnostic'" if c == "purpose"
                           else "0" if c == "legacy_backfilled"
                           else f"'{(NOW + timedelta(minutes=5)).isoformat()}'" if c == "created_at" else c
                           for c in columns)
        connection.execute(f"INSERT INTO activity_administrations ({', '.join(columns)}) "
                           f"SELECT {chosen} FROM activity_administrations WHERE id = ?", (administrations[0],))
        connection.commit()
    return paths, vault, repo, legacy


def test_a_practice_answer_between_a_live_diagnostic_and_the_practice_writers_first_record_is_history(tmp_path):
    """Review round 4, R4-S2: the backfill's boundary is the answer's own writer's first live record, not the vault's
    first live administration of any purpose. Before, the t10 practice answer fell after the diagnostic administration
    (t5): it was read as a failed live grade, its legacy observation, exposures and duration event were skipped and
    doctor reported it."""

    from learnloop.substrate.compat.activity_backfill import answers_without_grade_record

    paths, vault, repo, legacy = _history_with_diagnostics_first(tmp_path)
    assert answers_without_grade_record(vault, repo) == []  # failed before: the t10 answer was reported missing

    report = backfill_activity_substrate(vault, repo, clock=CLOCK)

    assert report.attempts_after_substrate_without_observation == 0
    assert report.attempts_replayed == 2 and report.attempts_before_their_writer_recorded == 1
    for attempt_id in legacy:
        assert repo.observation_by_attempt(attempt_id) is not None
    events = repo.interaction_events_for_attempt(legacy[1])
    assert [(e["kind"], e["attempt_duration_ms"]) for e in events] == [("attempt_duration", 37000)]
    assert answers_without_grade_record(vault, repo) == []


def test_an_answer_whose_writer_never_recorded_live_is_reported_with_unknown_provenance(tmp_path):
    """R4-S2's ambiguous side: when no practice answer was ever recorded live but a diagnostic administration was, a
    later practice answer without an observation is either history the practice writer never reached or a failed live
    write. No stored fact tells which: the backfill leaves it and counts it, and doctor's issue names it as unknown."""

    from learnloop.ops.doctor import run_doctor
    from learnloop.substrate.compat.activity_backfill import answers_without_grade_record

    paths, vault, repo, legacy = _history_with_diagnostics_first(tmp_path)
    with connect(repo.sqlite_path) as connection:
        last = connection.execute("SELECT id FROM practice_attempts ORDER BY created_at DESC, id DESC").fetchone()[0]
        administration = connection.execute("SELECT administration_id FROM activity_observations WHERE attempt_id = ?",
                                            (last,)).fetchone()[0]
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("DELETE FROM activity_observations WHERE attempt_id = ?", (last,))
        connection.execute("UPDATE activity_administrations SET legacy_backfilled = 1 WHERE id = ?", (administration,))
        connection.commit()
    unknown = [entry for entry in answers_without_grade_record(vault, repo) if entry.get("provenance") == "unknown"]
    assert {entry["attempt_id"] for entry in unknown} == {legacy[1], last}
    issue = next(issue for issue in run_doctor(paths.root).issues if issue.code == "answers:grade_record_missing")
    assert "can't tell" in issue.message

    report = backfill_activity_substrate(vault, repo, clock=CLOCK)
    assert report.attempts_writer_never_recorded == 2 and report.attempts_replayed == 1
