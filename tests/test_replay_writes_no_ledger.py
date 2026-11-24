"""A replay derives; it never writes history. A vault's first rebuild adds only the backfill of rows the vault never
recorded (:data:`FIRST_REBUILD_BACKFILL`), and every further whole-vault rebuild and every per-LO replay adds no row to
a table whose role is ``RAW_LEDGER`` or ``RECEIPT`` (``db.table_roles``), over every synthetic diagnosis journey and
the broad graded history of the grade-application golden.

Two named exceptions, each the code's own rule: a whole-vault rebuild appends its one receipt
(``derived_state_rebuilds``); and a vault below the grade channel fixes (mvp-0.60; the tests' older journeys run at
older tags) re-mints each answer's grade chain at every rebuild, as that predecessor does
(``tests/test_rebuild_history_appends.py`` pins it).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.attempts.grade_resolution import grade_channel_fixes_on
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.replay import replay_learning_object
from learnloop.vault.loader import load_vault

from tests import pinned_draws
from tests.diagnosis_journey_helpers import CASES, freeze_ids, freeze_wall, pin_journey_draws, run_case

REBUILD_RECEIPT = "derived_state_rebuilds"
#: What the predecessor of the grade channel fixes re-mints per graded answer at every rebuild.
GRADE_CHAIN = frozenset({"activity_observations", "raw_grade_events", "grade_interpretations", "measurement_events",
                         "activity_administrations"})
#: What a vault's first rebuild may add, once: the activity substrate's backfill of cards, surfaces and families for
#: items nobody answered, of administrations, exposures and observations for answers recorded without them, the
#: outcome schemas and the mastery seeds a vault never recorded, and the grade channel's one reconciliation of a grade
#: the ledger lags (a regrade, an adjudication). A second rebuild adds none of them.
FIRST_REBUILD_BACKFILL = frozenset({
    "activity_cards", "activity_card_versions", "activity_families", "activity_family_versions", "activity_surfaces",
    "outcome_schemas", "outcome_schema_versions", "mastery_seed_inputs", "activity_exposure_events", REBUILD_RECEIPT,
}) | GRADE_CHAIN
LEDGERS = sorted(name for name, role in TABLE_ROLES.items() if role in (TableRole.RAW_LEDGER, TableRole.RECEIPT))


def _counts(repository) -> dict[str, int]:
    with repository.connection() as connection:
        present = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        return {name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                for name in LEDGERS if name in present}


def _added(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    return {name: after[name] - before.get(name, 0) for name in after if after[name] != before.get(name, 0)}


def _journey(case: str, root: Path):
    with pytest.MonkeyPatch.context() as patch:
        freeze_wall(patch)
        freeze_ids(patch, 104)
        pin_journey_draws(patch, case)
        pushed = pinned_draws.push(f"diagnosis-journey:{case}")
        try:
            journey = run_case(case, root, patch)
        finally:
            if pushed:
                pinned_draws.pop()
    repository = journey.repository
    vault_root = next(p for p in Path(repository.sqlite_path).resolve().parents if (p / "learnloop.toml").exists())
    return load_vault(vault_root), repository


def _assert_replays_add_no_ledger_row(vault, repository) -> None:
    allowed_chain = set() if grade_channel_fixes_on(vault.config) else set(GRADE_CHAIN)
    # The first may backfill what the vault never recorded, and nothing else.
    before = _counts(repository)
    rebuild_all_derived_state(vault, repository)
    assert set(_added(before, _counts(repository))) <= FIRST_REBUILD_BACKFILL, _added(before, _counts(repository))
    for _ in range(2):
        before = _counts(repository)
        rebuild_all_derived_state(vault, repository)
        added = _added(before, _counts(repository))
        assert added.pop(REBUILD_RECEIPT, None) == 1
        assert set(added) <= allowed_chain, added
    for _ in range(2):
        before = _counts(repository)
        for learning_object_id in repository.learning_object_ids_with_attempts():
            replay_learning_object(vault, repository, learning_object_id)
        added = _added(before, _counts(repository))
        assert set(added) <= allowed_chain, added


@pytest.mark.parametrize("case", CASES)
def test_rebuilds_and_replays_add_no_ledger_row(case, tmp_path):
    vault, repository = _journey(case, tmp_path)
    _assert_replays_add_no_ledger_row(vault, repository)


def test_the_broad_graded_history_at_the_head_adds_no_ledger_row(tmp_path):
    from tests.grade_application_golden_helpers import build_graded_vault, play_history

    _paths, vault, repository = build_graded_vault(tmp_path)
    play_history(vault, repository)
    assert grade_channel_fixes_on(vault.config)
    _assert_replays_add_no_ledger_row(vault, repository)
