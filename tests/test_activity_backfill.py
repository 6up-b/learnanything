"""P0.1 activity-substrate backfill (spec_p0_measurement_correctness §7.1, §9.6)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.services.activity_backfill import backfill_activity_substrate
from learnloop.vault.loader import load_vault

from tests.helpers import NOW

FIXTURE_VAULT = Path(__file__).resolve().parents[1] / "fixtures" / "linear_algebra"
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


def test_backfill_populates_substrate_from_fixture(tmp_path):
    vault_root = _copy_fixture(tmp_path)
    vault = load_vault(vault_root)
    repo = Repository(vault_root / "state.sqlite")

    report = backfill_activity_substrate(vault, repo, clock=CLOCK)

    assert report.practice_items == len(vault.practice_items)
    assert report.attempts_replayed == len(repo.list_all_attempts())
    counts = _table_counts(repo)
    assert counts["activity_administrations"] == report.attempts_replayed
    assert counts["activity_observations"] == report.attempts_replayed
    # Every attempt gets a synthetic administration + observation.
    assert counts["activity_families"] >= report.practice_items


def test_backfill_is_idempotent_on_fixture_copy(tmp_path):
    vault_root = _copy_fixture(tmp_path)
    vault = load_vault(vault_root)
    repo = Repository(vault_root / "state.sqlite")

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


def test_backfill_render_once_per_shared_surface(tmp_path):
    """Multiple attempts on one item share a surface; only one 'rendered' exposure."""

    vault_root = _copy_fixture(tmp_path)
    vault = load_vault(vault_root)
    repo = Repository(vault_root / "state.sqlite")
    backfill_activity_substrate(vault, repo, clock=CLOCK)

    with connect(repo.sqlite_path) as connection:
        over_rendered = connection.execute(
            """
            SELECT surface_id, COUNT(*) n FROM activity_exposure_events
             WHERE kind = 'rendered' GROUP BY surface_id HAVING n > 1
            """
        ).fetchall()
    assert over_rendered == []  # the render-once index holds across shared surfaces


def test_diagnostic_probe_attempts_reuse_shared_surface_hash(tmp_path):
    """A diagnostic-probe attempt's adapter shares the practice surface_hash, so
    the shared ledger cannot manufacture novelty (§7.1 step 1)."""

    vault_root = _copy_fixture(tmp_path)
    vault = load_vault(vault_root)
    repo = Repository(vault_root / "state.sqlite")
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


def test_backfill_marks_unverifiable_for_missing_item(tmp_path):
    """An attempt whose item is gone yields a placeholder surface marked
    legacy_surface_unverifiable (§7.1 step 4)."""

    vault_root = _copy_fixture(tmp_path)
    vault = load_vault(vault_root)
    repo = Repository(vault_root / "state.sqlite")

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


def test_backfill_logs_attempt_duration_interaction_events(tmp_path):
    """Where a legacy attempt carries a latency, an attempt_duration interaction
    event is logged (§3.8, 'log now, model later')."""

    vault_root = _copy_fixture(tmp_path)
    vault = load_vault(vault_root)
    repo = Repository(vault_root / "state.sqlite")
    # Give one attempt a recorded latency so the duration path is exercised.
    with connect(repo.sqlite_path) as connection:
        target = connection.execute("SELECT id FROM practice_attempts LIMIT 1").fetchone()["id"]
        connection.execute(
            "UPDATE practice_attempts SET latency_seconds = 37 WHERE id = ?", (target,)
        )
        connection.commit()

    backfill_activity_substrate(vault, repo, clock=CLOCK)

    events = repo.interaction_events_for_attempt(target)
    assert len(events) == 1
    assert events[0]["kind"] == "attempt_duration"
    assert events[0]["attempt_duration_ms"] == 37000
