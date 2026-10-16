"""How long a routine full-answer display counts as an exposure: one definition
for every reader of the reveal ledger (UX Phase 4, rounds 3 and 4).

The plain surface shows the expected answer on every feedback and every plain
self-grade. Each such display is a reveal-ledger row whose basis starts with
:data:`ROUTINE_DISPLAY_BASES`. The screens show the answer only while a
committed row stamped at most :data:`ROUTINE_DISPLAY_RENEWAL_GRACE` ago exists
(``apps/learnloop-tauri/src/screens/feedback/answerExposure.ts``, numbers in
``exposureContract.json``, pinned equal by a test), so a row stamped s covers
every moment T in [s, s + :data:`ROUTINE_DISPLAY_COVERAGE`]: the horizon (the
cold retrieval delay, one day) after any moment the answer was on screen.

Every reader that judges or serves by reveals reads routine rows this way: the
submit path (auto-prime), production admissibility, the scheduler's serving
and deferral of cold follow-ups, the serving exclusions, the independent-check
and source serve-time eligibility, and the practice index. A reader whose
window for a reveal starts at ``T - delay`` reads routine rows from
``T - delay - grace`` (:func:`routine_window_start`). A routine row stamped
after the reader's own clock (the clock went back after it was written) is
never invisible: it counts as covering now. Other reveal kinds keep their
rules.

Dependency free (stdlib only), so persistence, scheduling and instructional
code can all read the one definition.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

#: The routine displays' bases (``reveal_ledger.FEEDBACK_FULL_ANSWER_BASIS``,
#: ``reveal_ledger.SELF_GRADE_DISCLOSURE_BASIS``, each followed by ":").
ROUTINE_DISPLAY_BASES: tuple[str, ...] = ("feedback_full_answer:", "self_grade_disclosure:")

#: The cold retrieval delay (``diagnosis.remediation.COLD_RETRIEVAL_DELAY``,
#: pinned equal by a test; not imported, so this module stays a leaf).
ROUTINE_DISPLAY_HORIZON = timedelta(days=1)

#: How much longer than the horizon a routine row counts: the grace within
#: which the screens renew a row that keeps the answer on screen.
ROUTINE_DISPLAY_RENEWAL_GRACE = timedelta(hours=1)

#: How long after its stamp a routine display row counts.
ROUTINE_DISPLAY_COVERAGE = ROUTINE_DISPLAY_HORIZON + ROUTINE_DISPLAY_RENEWAL_GRACE


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parsed(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def is_routine_display(source_kind: object, basis: object) -> bool:
    """Is a reveal row (its ``source_kind`` and ``basis``) a routine display?"""

    return source_kind == "answer_display" and isinstance(basis, str) and basis.startswith(ROUTINE_DISPLAY_BASES)


def routine_display_sql(table: str = "") -> tuple[str, list[object]]:
    """A SQL predicate (and its parameters) true for routine display rows; a
    prefix match without LIKE (its "_" is a wildcard)."""

    prefix = f"{table}." if table else ""
    matches = " OR ".join(f"substr(COALESCE({prefix}basis, ''), 1, ?) = ?" for _ in ROUTINE_DISPLAY_BASES)
    parameters: list[object] = []
    for basis in ROUTINE_DISPLAY_BASES:
        parameters.extend([len(basis), basis])
    return f"({prefix}source_kind = 'answer_display' AND ({matches}))", parameters


def routine_covered_from(at: datetime | str) -> str | None:
    """The earliest stamp of a routine row still covering ``at`` (ledger format);
    None when ``at`` cannot be read (nothing lapses: fail closed)."""

    moment = _parsed(at) if isinstance(at, str) else at
    return _iso(moment - ROUTINE_DISPLAY_COVERAGE) if moment is not None else None


def routine_window_start(since: str) -> str:
    """For a reader whose window for a reveal starts at ``since`` (``T`` minus
    the cold retrieval delay): where its window for routine rows starts, the
    renewal grace earlier. Unreadable: ``since`` unchanged."""

    moment = _parsed(since)
    return _iso(moment - ROUTINE_DISPLAY_RENEWAL_GRACE) if moment is not None else since


def routine_counts_until(created_at: str) -> str | None:
    """The last moment a routine row stamped ``created_at`` counts (ledger format)."""

    moment = _parsed(created_at)
    return _iso(moment + ROUTINE_DISPLAY_COVERAGE) if moment is not None else None
