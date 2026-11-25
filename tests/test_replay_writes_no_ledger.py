"""A replay derives; it never writes history. A vault's first rebuild adds only the catalog backfill of rows the vault
never recorded (:data:`FIRST_REBUILD_BACKFILL`: cards, surfaces and families for items nobody answered, the outcome
schemas, the mastery seeds), plus, for history recorded before the activity substrate existed and only for it, the
backfill's administrations, exposures and observations and the grade chain on them (:data:`PRE_SUBSTRATE_BACKFILL`;
review round 3, FR3-6). Every further whole-vault rebuild and every per-LO replay adds no row to a table whose role is
``RAW_LEDGER`` or ``RECEIPT`` (``db.table_roles``), over every synthetic diagnosis journey and the broad graded history
of the grade-application golden.

Two named exceptions, each the code's own rule: a whole-vault rebuild appends its one receipt
(``derived_state_rebuilds``); and a vault below the grade channel fixes (mvp-0.60; the tests' older journeys run at
older tags) re-mints each answer's grade chain at every rebuild, as that predecessor does
(``tests/test_rebuild_history_appends.py`` pins it). A later answer with no grade record is never given one by a
rebuild (``tests/test_rebuild_writes_no_grade_record.py``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.attempts.grade_resolution import grade_channel_fixes_on
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from learnloop.substrate.compat.activity_backfill import substrate_cutovers
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.replay import replay_learning_object
from learnloop.vault.loader import load_vault

from tests import pinned_draws
from tests.diagnosis_journey_helpers import CASES, freeze_ids, freeze_wall, pin_journey_draws, run_case

REBUILD_RECEIPT = "derived_state_rebuilds"
#: What the predecessor of the grade channel fixes re-mints per graded answer at every rebuild.
GRADE_CHAIN = frozenset({"activity_observations", "raw_grade_events", "grade_interpretations", "measurement_events",
                         "activity_administrations"})
#: What a vault's first rebuild may add, once: the activity substrate's catalog backfill of cards, surfaces and families
#: for items nobody answered, and the outcome schemas and mastery seeds a vault never recorded. A second adds none.
FIRST_REBUILD_BACKFILL = frozenset({
    "activity_cards", "activity_card_versions", "activity_families", "activity_family_versions", "activity_surfaces",
    "outcome_schemas", "outcome_schema_versions", "mastery_seed_inputs", REBUILD_RECEIPT,
})
#: What the first rebuild adds, once, for history recorded before the activity substrate existed (and only for it):
#: the presentations' and answers' administrations, exposures and observations, and the grade chain on them.
PRE_SUBSTRATE_BACKFILL = frozenset({"activity_exposure_events"}) | GRADE_CHAIN
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


def _holds_pre_substrate_history(repository) -> bool:
    cutovers = substrate_cutovers(repository)
    return any(cutovers.answer_predates(str(attempt["attempt_type"]), attempt.get("created_at"))
               for attempt in repository.list_all_attempts()) or any(
        cutovers.presentation_predates(presentation.get("served_at") or presentation.get("created_at"))
        for presentation in repository.list_all_probe_presentations())


def _assert_replays_add_no_ledger_row(vault, repository, *, pre_substrate: bool = False,
                                      first_rebuild_lag: frozenset[str] = frozenset()) -> None:
    allowed_chain = set() if grade_channel_fixes_on(vault.config) else set(GRADE_CHAIN)
    assert _holds_pre_substrate_history(repository) is pre_substrate
    # The first may backfill the catalog the vault never recorded, and evidence for history from before the
    # substrate only.
    first = FIRST_REBUILD_BACKFILL | allowed_chain | (PRE_SUBSTRATE_BACKFILL if pre_substrate else set())
    before = _counts(repository)
    rebuild_all_derived_state(vault, repository)
    added = _added(before, _counts(repository))
    assert set(added) <= first | first_rebuild_lag, added
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


#: The grade chain's interpretation and its measurement events for one answer whose grade the channel lags.
_ONE_LAGGING_GRADE = frozenset({"raw_grade_events", "grade_interpretations", "measurement_events"})


def test_the_broad_graded_history_at_the_head_adds_no_ledger_row(tmp_path):
    from tests.grade_application_golden_helpers import build_graded_vault, play_history

    _paths, vault, repository = build_graded_vault(tmp_path)
    play_history(vault, repository)
    assert grade_channel_fixes_on(vault.config)
    graded = _graded_answers(repository)
    # `play_history` writes its adjudication's evidence revision directly (`append_adjudication_evidence_revision`),
    # without the ruling the adjudication door writes first, so the channel lags that one grade and the first rebuild
    # reconciles it: one raw grade, for that answer alone. The door itself leaves no lag (its ruling is the head).
    _assert_replays_add_no_ledger_row(vault, repository, first_rebuild_lag=_ONE_LAGGING_GRADE)
    reconciled = _graded_answers(repository) - graded
    assert {attempt_id for attempt_id, _event in reconciled} == {"att_i1_self"}, reconciled
    assert len(reconciled) == 1


def _graded_answers(repository) -> set[tuple[str, str]]:
    with repository.connection() as connection:
        return {tuple(row) for row in connection.execute(
            "SELECT o.attempt_id, r.id FROM raw_grade_events r JOIN activity_observations o ON o.id = r.observation_id")}


def test_history_from_before_the_substrate_is_backfilled_once(tmp_path):
    """An answer recorded before the vault's first live administration (an older vault's first answer, from before
    the substrate wrote anything) has its administration, exposures, observation and grade chain backfilled by the
    first rebuild, and by no later one."""

    from tests.grade_application_golden_helpers import build_graded_vault, play_history

    _paths, vault, repository = build_graded_vault(tmp_path)
    play_history(vault, repository)
    rebuild_all_derived_state(vault, repository)  # the history's own lag reconciled (see above)
    earliest = min(repository.list_all_attempts(), key=lambda attempt: (str(attempt["created_at"]), attempt["id"]))
    with repository.connection() as connection:
        # The substrate's rows for the earliest answer are removed, as if it had been recorded before the substrate.
        connection.execute("PRAGMA foreign_keys = OFF")
        administrations = [row[0] for row in connection.execute(
            "SELECT administration_id FROM activity_observations WHERE attempt_id = ?", (earliest["id"],))]
        marks = ", ".join("?" for _ in administrations)
        for table in ("measurement_events", "grade_interpretations", "raw_grade_events", "activity_observations",
                      "activity_exposure_events"):
            connection.execute(f"DELETE FROM {table} WHERE administration_id IN ({marks})", administrations)
        connection.execute(f"DELETE FROM activity_administrations WHERE id IN ({marks})", administrations)
        connection.commit()
    assert administrations and repository.observation_by_attempt(earliest["id"]) is None
    assert substrate_cutovers(repository).answer_predates(str(earliest["attempt_type"]), earliest["created_at"])
    _assert_replays_add_no_ledger_row(vault, repository, pre_substrate=True)
    assert repository.observation_by_attempt(earliest["id"]) is not None
