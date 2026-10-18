"""`learnloop hints report`: which hints are used and what follows (spec_adaptive_hints_v1 §6).

H0's rows are the **descriptive** ones (§6.3), with authored hints as the
baseline kind (§10 H0, "Data it starts"): per surface, kind and level, how many
were shown, on how many items, sessions and attempts, which hint in the item's
list, when (reveal to submit, and how far into the attempt), and what followed
(§6.1, as far as H0's rows can say it): more help in the same attempt, the
attempt's recorded outcome, unaided next progress where the grade settles it,
and later independent success on the item and on its learning object.

**Rows and attempts.** A row belongs to the attempt it was attached to or,
when the attach never happened (it failed, or the process stopped after the
attempt committed), to the attempt committed under the row's submission key
(``practice_attempts.submission_id``): the same binding the attach makes, so
a failed attach loses nothing and no row is ever given to another
submission's attempt.

**Timing.** "Reveal to submit" ends at ``submitted_at``, the sidecar's clock
when the submission reached it, before grading (``practice_attempts.
created_at`` is stamped when the grade is applied, after the grader's
latency). A row without a submit time (an attach repaired by a recovery that
never saw the submit) is counted in ``timing_unknown`` and never timed from
the grade's time. "Seconds into the attempt" is the open-to-submit latency
that same submission sent (``submit_latency_seconds``, stamped with
``submitted_at`` and kept with it) minus that gap, never the attempt's
``latency_seconds``: a grading fallback's retry records a later latency, and
the two would not be on one basis. A row without either is counted in
``seconds_into_attempt_unknown`` by reason (``no_submit_time``,
``no_submit_latency``).

**Outcomes are never imputed.** The next independent attempt (``hints_used =
0``, not primed) on the item, and on its learning object, is the outcome:
``pass`` when it is fully correct, ``fail`` when graded and not, ``ungraded``
when it has no grade (it stays that attempt's outcome: a later attempt is not
searched for instead), ``pending`` while none has happened.

**Unaided next progress** (§6.1). For an authored hint (no map, so its target
is the next node) the grade settles one case: a fully correct submission with
no further help after the hint reached the goal. "No further help" is
established only from records no cap applies to: the submission's own rows
and, for the attempt (after the item's previous attempt, up to this one),
the tutor's questions, reveal events (except the attempt's own post-attempt
displays and this submission's own self-grade disclosure). A workbench
problem's help cannot be reconstructed from its current state (the book can
be hidden, or first shown, after the submit; RW2b/H3 write it to
``help_assists``), so a workbench problem on the item that could have been
open during the window makes the case ``workbench_state_unknown``. An event attributed to an attempt was written after
that attempt existed, so attribution orders it: one attributed to the
previous attempt is after the window opened (but still must precede this
attempt), one attributed to this attempt came after it. Otherwise the
whole-second times decide, and an event in the same second as a boundary
cannot be ordered (``help_order_ambiguous``). ``hints_used`` is the client's
count plus the tutor's, capped at the item's ``max_useful_hints``, so it can
only confirm what those records say. Every other case is reported as unknown
with its reason, never as a failure: more help followed (H2's next hint
placement says whether the learner progressed first), primed (worked help or
a disclosed answer), help the rows cannot order (``help_not_ordered``: other
assistance recorded in the attempt, or a count above its recorded reveals),
help that cannot be placed in or out of the attempt (``help_order_ambiguous``),
a workbench problem that may have helped (``workbench_state_unknown``),
a count that reached the item's cap (``help_count_capped``: the client's
count may have been larger), a cap that cannot be known (``help_cap_unknown``:
the report was given no items, or the item changed since the hint), no grade,
or an answer not fully correct (H2's outcome placement, ``hint_outcome``).

**Uncertainty.** Every number carries its sample size. A share carries a 95%
Wilson score interval (``None`` when its denominator is 0; at n = 1 it spans
most of [0, 1], as it should). A timing or count summary's p50 and p95 carry a
distribution-free 95% interval from the order statistics (the binomial
coverage of [X(j), X(k)] for the quantile, its terms computed in log space so
any n works); when no pair of observations reaches 95% coverage (the median
needs n >= 6, p95 needs n >= 59) the interval is ``None`` with ``reason:
"too_few"``. Every number is a report, never a threshold (§6).

Pure read: the database is opened read-only and never migrated, no model is
called, and no learner text is read (the rows carry a hash and a length of the
draft, never the draft). "Doesn't connect", the off-policy estimates and the
expertise-reversal split need H2-H5's rows and are not computed here.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from collections.abc import Mapping
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from learnloop.clock import parse_utc
from learnloop.db.connection import connect
from learnloop.vault.hashes import practice_item_hash

REPORT_VERSION = "hints-report-v1"
#: How many items the per-item list shows (a display cap).
TOP_ITEMS = 20
#: The intervals' nominal coverage, and the normal quantile Wilson uses for it.
INTERVAL_LEVEL = 0.95
_Z = 1.959963984540054
#: The unknown cases of unaided next progress, in the order they are checked.
UNAIDED_UNKNOWN_REASONS = (
    "more_help_followed", "primed", "help_not_ordered", "help_order_ambiguous", "workbench_state_unknown",
    "help_count_capped",
    "help_cap_unknown", "ungraded", "not_fully_correct",
)
#: Why "seconds into the attempt" is unknown for a row.
INTO_ATTEMPT_UNKNOWN_REASONS = ("no_submit_time", "no_submit_latency")
#: The basis prefix of a plain self-grade's disclosure row
#: (``attempts.reveal_ledger.SELF_GRADE_DISCLOSURE_BASIS``; that package is
#: closed to this one, G-H13): its JSON identity names the submission.
_SELF_GRADE_DISCLOSURE = "self_grade_disclosure:"


def item_caps(practice_items: Iterable[Any]) -> dict[str, tuple[str, int]]:
    """Each item's content hash and ``max_useful_hints`` (0: no cap), for the
    report's completeness check: a row's cap is known only when the item is
    unchanged since the hint (the row's ``practice_item_hash``)."""

    return {
        item.id: (practice_item_hash(item), int(item.hint_policy.max_useful_hints or 0)) for item in practice_items
    }


def _own_disclosure(reveal: Mapping[str, Any], submission_id: str | None) -> bool:
    """The submission's own plain self-grade disclosure (shown after its trace
    was frozen; a trace changed after it makes the attempt primed)."""

    basis = reveal["basis"]
    if not submission_id or reveal["source_kind"] != "answer_display" or not isinstance(basis, str):
        return False
    if not basis.startswith(_SELF_GRADE_DISCLOSURE) or "{" not in basis:
        return False
    try:
        identity = json.loads(basis[basis.index("{"):])
    except ValueError:
        return False
    return isinstance(identity, dict) and identity.get("submission") == submission_id


def _wilson(count: int, of: int) -> dict[str, Any] | None:
    if of <= 0:
        return None
    share = count / of
    denominator = 1.0 + _Z * _Z / of
    centre = (share + _Z * _Z / (2 * of)) / denominator
    half = _Z * math.sqrt(share * (1.0 - share) / of + _Z * _Z / (4 * of * of)) / denominator
    return {
        "method": "wilson", "level": INTERVAL_LEVEL,
        "low": round(max(0.0, centre - half), 4), "high": round(min(1.0, centre + half), 4),
    }


def _binomial_pmf(n: int, q: float) -> list[float]:
    """P(B = i) for i = 0..n, B ~ Binomial(n, q), 0 < q < 1, in log space: the
    exact coefficient times ``q**i`` overflows a float from n = 1030 (review
    round 2, V1). The two log-factorials are added before they are subtracted
    and the two powers are added together, so P(i) and P(n - i) are the same
    float at q = 0.5 and the interval breaks a tie exactly as before."""

    log_n, log_q, log_r = math.lgamma(n + 1), math.log(q), math.log(1.0 - q)
    return [
        math.exp(log_n - (math.lgamma(i + 1) + math.lgamma(n - i + 1)) + (i * log_q + (n - i) * log_r))
        for i in range(n + 1)
    ]


def _quantile_interval(ordered: list[float], q: float) -> dict[str, Any]:
    """A distribution-free interval for the q-quantile: the order statistics
    [X(j), X(k)] (1-based) cover it with probability P(j <= B <= k - 1),
    B ~ Binomial(n, q). Grown outward from the point estimate's rank, the
    likelier side first, until the coverage reaches the level."""

    n = len(ordered)
    if n == 0:
        return {"method": "order_statistic", "level": INTERVAL_LEVEL, "low": None, "high": None,
                "coverage": None, "reason": "empty"}
    pmf = _binomial_pmf(n, q)
    rank = max(1, math.ceil(q * n))
    low, high, coverage = rank, rank, 0.0
    while coverage < INTERVAL_LEVEL:
        below = pmf[low - 1] if low > 1 else -1.0
        above = pmf[high] if high < n else -1.0
        if below < 0 and above < 0:
            return {"method": "order_statistic", "level": INTERVAL_LEVEL, "low": None, "high": None,
                    "coverage": round(coverage, 4), "reason": "too_few"}
        if above >= below:
            coverage += above
            high += 1
        else:
            coverage += below
            low -= 1
    return {"method": "order_statistic", "level": INTERVAL_LEVEL, "low": ordered[low - 1],
            "high": ordered[high - 1], "coverage": round(coverage, 4)}


def _percentiles(values: Iterable[float | None]) -> dict[str, Any]:
    ordered = sorted(v for v in values if v is not None)
    if not ordered:
        return {"n": 0, "p50": None, "p95": None,
                "p50_interval": _quantile_interval([], 0.50), "p95_interval": _quantile_interval([], 0.95)}

    def rank(q: float) -> float:
        return ordered[max(0, math.ceil(q * len(ordered)) - 1)]

    return {
        "n": len(ordered), "p50": rank(0.50), "p95": rank(0.95),
        "p50_interval": _quantile_interval(ordered, 0.50), "p95_interval": _quantile_interval(ordered, 0.95),
    }


def _share(count: int, of: int) -> dict[str, Any]:
    return {"count": count, "of": of, "share": (round(count / of, 4) if of else None), "interval": _wilson(count, of)}


def _when(value: str | None) -> datetime | None:
    try:
        return parse_utc(value) if value else None
    except ValueError:
        return None


def _outcome(correctness: float | None) -> str:
    if correctness is None:
        return "ungraded"
    if correctness >= 1.0 - 1e-9:
        return "correct"
    if correctness <= 1e-9:
        return "incorrect"
    return "partial"


def _table_exists(connection: Any, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone() is not None


def build_hints_report(
    sqlite_path: Path | str,
    *,
    since: str | None = None,
    surface: str | None = None,
    now: datetime | None = None,
    item_caps: Mapping[str, tuple[str, int]] | None = None,
) -> dict[str, Any]:
    """Compute the descriptive rows from ``help_assists`` and the attempts (pure read).

    ``item_caps`` (:func:`item_caps` of the vault's items) gives each item's
    hint cap; without it no row's help count can be shown complete, so
    unaided next progress is ``help_cap_unknown`` throughout."""

    caps = dict(item_caps or {})

    now = (now or datetime.now(UTC)).astimezone(UTC)
    since_at = _when(since) if since else None
    if since is not None and since_at is None:
        raise ValueError(f"--since {since!r} is not an ISO time")
    with closing(connect(Path(sqlite_path), read_only=True)) as connection:
        if not _table_exists(connection, "help_assists"):
            raise ValueError("this vault's database has no help_assists table (migration 210)")
        clauses = ["shown = 1"]
        parameters: list[Any] = []
        if surface is not None:
            clauses.append("surface = ?")
            parameters.append(surface)
        rows = [
            dict(row)
            for row in connection.execute(
                "SELECT id, surface, assist_kind, hint_kind, level, practice_item_id, practice_item_hash, "
                "practice_session_id, attempt_id, submission_id, authored_index, work_chars, counted_by, "
                "requested_at, shown_at, submitted_at, submit_latency_seconds "
                f"FROM help_assists WHERE {' AND '.join(clauses)} ORDER BY requested_at, id",
                parameters,
            ).fetchall()
        ]
        rows = [
            row for row in rows
            if since_at is None or ((_when(row["shown_at"] or row["requested_at"]) or now) >= since_at)
        ]
        columns = (
            "id, practice_item_id, learning_object_id, attempt_type, correctness, latency_seconds, "
            "hints_used, primed, submission_id, created_at"
        )
        attempts: dict[str, dict[str, Any]] = {}

        def fetch(column: str, keys: list[str]) -> None:
            for start in range(0, len(keys), 500):
                chunk = keys[start:start + 500]
                for found in connection.execute(
                    f"SELECT {columns} FROM practice_attempts WHERE {column} IN ({', '.join('?' for _ in chunk)})",
                    chunk,
                ).fetchall():
                    attempts[found["id"]] = dict(found)

        fetch("id", sorted({row["attempt_id"] for row in rows if row["attempt_id"]}))
        fetch("submission_id", sorted({
            row["submission_id"] for row in rows if not row["attempt_id"] and row["submission_id"]
        }))
        by_submission = {
            (attempt["submission_id"], attempt["practice_item_id"]): attempt_id
            for attempt_id, attempt in attempts.items() if attempt["submission_id"]
        }
        resolved_by_submission = 0
        for row in rows:
            if row["attempt_id"] in attempts:
                row["resolved_attempt"] = row["attempt_id"]
            else:
                row["resolved_attempt"] = by_submission.get((row["submission_id"], row["practice_item_id"]))
                if row["resolved_attempt"] is not None and not row["attempt_id"]:
                    resolved_by_submission += 1
        # Later independent attempts (hints_used = 0, not primed) on each
        # touched item and learning object, in time order.
        items = sorted({a["practice_item_id"] for a in attempts.values()})
        los = sorted({a["learning_object_id"] for a in attempts.values() if a["learning_object_id"]})
        independent_by_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
        independent_by_lo: dict[str, list[dict[str, Any]]] = defaultdict(list)
        if items or los:
            for row in connection.execute(
                "SELECT id, practice_item_id, learning_object_id, correctness, created_at FROM practice_attempts "
                "WHERE COALESCE(hints_used, 0) = 0 AND COALESCE(primed, 0) = 0 ORDER BY created_at, id"
            ).fetchall():
                if row["practice_item_id"] in items:
                    independent_by_item[row["practice_item_id"]].append(dict(row))
                if row["learning_object_id"] in los:
                    independent_by_lo[row["learning_object_id"]].append(dict(row))
        # The assistance each hinted attempt recorded outside its own rows,
        # uncapped (review round 2, V2).
        other_help = {
            attempt_id: _other_assistance(connection, attempts[attempt_id])
            for attempt_id in sorted({row["resolved_attempt"] for row in rows if row["resolved_attempt"]})
        }

    def later(attempt: dict[str, Any], pool: list[dict[str, Any]]) -> str:
        """The next independent attempt's outcome, never a later one's."""

        for candidate in pool:
            if candidate["id"] != attempt["id"] and (candidate["created_at"], candidate["id"]) > (
                attempt["created_at"], attempt["id"]
            ):
                outcome = _outcome(candidate["correctness"])
                if outcome == "ungraded":
                    return "ungraded"
                return "pass" if outcome == "correct" else "fail"
        return "pending"

    def later_block(counts: Counter) -> dict[str, Any]:
        block: dict[str, Any] = {key: counts.get(key, 0) for key in ("pass", "fail", "ungraded", "pending")}
        block["pass_rate"] = _share(block["pass"], block["pass"] + block["fail"])
        return block

    groups: dict[tuple[str, str, str | None, int | None], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["surface"], row["assist_kind"], row["hint_kind"], row["level"])].append(row)
    by_attempt: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["resolved_attempt"]:
            by_attempt[row["resolved_attempt"]].append(row)

    def unaided(row: dict[str, Any]) -> str:
        """``reached`` when the grade settles it (§6.1), else why it is unknown."""

        attempt = attempts[row["resolved_attempt"]]
        if any((other["requested_at"], other["id"]) > (row["requested_at"], row["id"])
               for other in by_attempt[row["resolved_attempt"]]):
            return "more_help_followed"
        if attempt["primed"]:
            return "primed"
        recorded = sum(1 for other in by_attempt[row["resolved_attempt"]] if other["counted_by"] == "client")
        hints_used = int(attempt["hints_used"] or 0)
        if other_help[row["resolved_attempt"]] == "help" or hints_used > recorded:
            return "help_not_ordered"
        if other_help[row["resolved_attempt"]] == "ambiguous":
            return "help_order_ambiguous"
        if other_help[row["resolved_attempt"]] == "workbench":
            return "workbench_state_unknown"
        cap = caps.get(attempt["practice_item_id"])
        if cap is None or cap[0] != row["practice_item_hash"]:
            return "help_cap_unknown"
        if cap[1] > 0 and hints_used >= cap[1]:
            return "help_count_capped"
        outcome = _outcome(attempt["correctness"])
        if outcome == "ungraded":
            return "ungraded"
        return "reached" if outcome == "correct" else "not_fully_correct"

    kinds: list[dict[str, Any]] = []
    for (row_surface, assist_kind, hint_kind, level), members in sorted(
        groups.items(), key=lambda entry: tuple("" if part is None else str(part) for part in entry[0])
    ):
        attached = [row for row in members if row["resolved_attempt"]]
        per_item = Counter(row["practice_item_id"] for row in members)
        per_session = Counter(row["practice_session_id"] for row in members if row["practice_session_id"])
        to_submit: list[float] = []
        into_attempt: list[float] = []
        timing_unknown = 0
        into_unknown: Counter = Counter()
        more_help = 0
        progress = Counter(unaided(row) for row in attached)
        for row in attached:
            attempt = attempts[row["resolved_attempt"]]
            shown = _when(row["shown_at"] or row["requested_at"])
            submitted = _when(row["submitted_at"])
            if shown is not None and submitted is not None:
                gap = max(0.0, (submitted - shown).total_seconds())
                to_submit.append(round(gap, 3))
                # The latency the same submission sent, never the attempt's
                # (a fallback's retry records a later one; review round 2, V3).
                if row["submit_latency_seconds"] is not None:
                    into_attempt.append(round(max(0.0, float(row["submit_latency_seconds"]) - gap), 3))
                else:
                    into_unknown["no_submit_latency"] += 1
            else:
                timing_unknown += 1
                into_unknown["no_submit_time"] += 1
            if any(
                (other["requested_at"], other["id"]) > (row["requested_at"], row["id"])
                for other in by_attempt[row["resolved_attempt"]]
            ):
                more_help += 1
        counted_attempts = {row["resolved_attempt"] for row in attached}
        outcomes = Counter(_outcome(attempts[a]["correctness"]) for a in counted_attempts)
        graded = sum(outcomes.get(key, 0) for key in ("correct", "partial", "incorrect"))
        later_item = Counter(
            later(attempts[a], independent_by_item.get(attempts[a]["practice_item_id"], [])) for a in counted_attempts
        )
        later_lo = Counter(
            later(attempts[a], independent_by_lo.get(attempts[a]["learning_object_id"] or "", []))
            for a in counted_attempts
        )
        kinds.append({
            "surface": row_surface,
            "assist_kind": assist_kind,
            "hint_kind": hint_kind,
            "level": level,
            "baseline": hint_kind == "authored",
            "shown": len(members),
            "items": len(per_item),
            "sessions": len(per_session),
            "attempts": len(counted_attempts),
            "unattached": len(members) - len(attached),
            "per_item": _percentiles(per_item.values()),
            "per_session": _percentiles(per_session.values()),
            "by_authored_index": {
                str(index): count
                for index, count in sorted(Counter(
                    row["authored_index"] for row in members if row["authored_index"] is not None
                ).items())
            },
            "work_empty_at_request": _share(sum(1 for row in members if not row["work_chars"]), len(members)),
            "seconds_reveal_to_submit": _percentiles(to_submit),
            "seconds_into_attempt": _percentiles(into_attempt),
            "seconds_into_attempt_unknown": {
                reason: into_unknown.get(reason, 0) for reason in INTO_ATTEMPT_UNKNOWN_REASONS
            },
            "timing_unknown": timing_unknown,
            "more_help_in_attempt": _share(more_help, len(attached)),
            "unaided_next_progress": {
                "reached": _share(progress.get("reached", 0), len(attached)),
                "unknown": {reason: progress.get(reason, 0) for reason in UNAIDED_UNKNOWN_REASONS},
            },
            "attempt_outcome": {key: outcomes.get(key, 0) for key in ("correct", "partial", "incorrect", "ungraded")},
            "attempt_correct": _share(outcomes.get("correct", 0), graded),
            "attempt_types": dict(sorted(Counter(attempts[a]["attempt_type"] for a in counted_attempts).items())),
            "later_independent_success": {
                "item": later_block(later_item),
                "learning_object": later_block(later_lo),
            },
        })

    per_item_all = Counter(row["practice_item_id"] for row in rows)
    top_items = [
        {
            "practice_item_id": item_id,
            "shown": count,
            "sessions": len({row["practice_session_id"] for row in rows if row["practice_item_id"] == item_id}),
            "attempts": len({
                row["resolved_attempt"] for row in rows if row["practice_item_id"] == item_id and row["resolved_attempt"]
            }),
        }
        for item_id, count in sorted(per_item_all.items(), key=lambda entry: (-entry[1], entry[0] or ""))[:TOP_ITEMS]
    ]
    return {
        "report_version": REPORT_VERSION,
        "generated_at": now.isoformat(),
        "since": since_at.isoformat() if since_at else None,
        "surface": surface,
        "totals": {
            "shown": len(rows),
            "items": len(per_item_all),
            "sessions": len({row["practice_session_id"] for row in rows if row["practice_session_id"]}),
            "attempts": len(by_attempt),
            "unattached": sum(1 for row in rows if not row["resolved_attempt"]),
            "resolved_by_submission": resolved_by_submission,
            "per_attempt": _percentiles(Counter(
                row["resolved_attempt"] for row in rows if row["resolved_attempt"]
            ).values()),
        },
        "kinds": kinds,
        "top_items": top_items,
        "not_yet_measured": [
            # The unaided-progress cases the grade cannot settle (H2's hint and
            # outcome placements); the grade-settled ones are in each kind's row.
            "unaided_next_progress_unknown_cases", "doesnt_connect", "off_policy_estimates",
            "expertise_reversal_split",
        ],
    }


def _second(value: Any) -> datetime | None:
    """A stored instant at whole-second resolution: attempts and tutor events
    are stamped to the second, so two stamps in the same second cannot be
    ordered by time."""

    parsed = _when(value) if isinstance(value, str) else None
    return parsed.replace(microsecond=0) if parsed is not None else None


def _window_position(
    event: Mapping[str, Any], *, attempt_id: str, previous_id: str | None,
    since: datetime | None, until: datetime | None,
) -> str:
    """Where an event falls against the attempt's window (after the item's
    previous attempt, up to this one): ``inside``, ``outside`` or
    ``ambiguous``. Attribution settles a side where it can: an event
    attributed to this attempt came after it (its own post-attempt feedback,
    round 3 W1); one attributed to the previous attempt came after that one,
    which relaxes only the lower bound, never the upper (W2). Both hold
    because a row can name only an attempt that already exists. Otherwise the
    whole-second time decides, and a tie with a boundary cannot be ordered
    (W3)."""

    if event["attempt_id"] is not None and event["attempt_id"] == attempt_id:
        return "outside"
    at = _second(event["created_at"])
    if at is None:
        return "ambiguous"
    positions = []
    if previous_id is not None and event["attempt_id"] == previous_id:
        positions.append("inside")
    elif since is None or at > since:
        positions.append("inside")
    elif at < since:
        return "outside"
    else:
        positions.append("ambiguous")
    if until is None:
        positions.append("ambiguous")
    elif at < until:
        positions.append("inside")
    elif at > until:
        return "outside"
    else:
        positions.append("ambiguous")
    return "ambiguous" if "ambiguous" in positions else "inside"


def _other_assistance(connection: Any, attempt: Mapping[str, Any]) -> str | None:
    """Assistance the attempt recorded outside its help rows, read uncapped
    from the records themselves: ``"help"``, ``"ambiguous"`` (an event whose
    order against the window cannot be established), ``"workbench"`` (a
    workbench problem that could have been open in the window) or None. Over
    the attempt's window (after the item's previous attempt, up to this one;
    ``tutor_qa.hint_equivalents_for_attempt``'s): a tutor question that was
    answered or counted as a hint, or a reveal event (a post-attempt display
    of the previous attempt included; the attempt's own post-attempt displays
    and this submission's own self-grade disclosure excluded)."""

    item_id = attempt["practice_item_id"]
    previous = connection.execute(
        "SELECT id, created_at FROM practice_attempts WHERE practice_item_id = ? "
        "AND (created_at < ? OR (created_at = ? AND id < ?)) ORDER BY created_at DESC, id DESC LIMIT 1",
        (item_id, attempt["created_at"], attempt["created_at"], attempt["id"]),
    ).fetchone()
    window = {
        "attempt_id": attempt["id"],
        "previous_id": previous["id"] if previous is not None else None,
        "since": _second(previous["created_at"]) if previous is not None else None,
        "until": _second(attempt["created_at"]),
    }
    positions: set[str] = set()
    for question in connection.execute(
        "SELECT attempt_id, created_at FROM question_events WHERE practice_item_id = ? "
        "AND (hint_equivalent = 1 OR answer_status = 'answered')",
        (item_id,),
    ).fetchall():
        positions.add(_window_position(question, **window))
    for reveal in connection.execute(
        "SELECT source_kind, basis, attempt_id, created_at FROM reveal_events WHERE practice_item_id = ? AND amount > 0",
        (item_id,),
    ).fetchall():
        if not _own_disclosure(reveal, attempt["submission_id"]):
            positions.add(_window_position(reveal, **window))
    if "inside" in positions:
        return "help"
    if "ambiguous" in positions:
        return "ambiguous"
    problems = connection.execute(
        "SELECT created_at, closed_at FROM workbench_sessions WHERE practice_item_id = ?", (item_id,)
    ).fetchall()
    if any(_could_overlap(problem, since=window["since"], until=window["until"]) for problem in problems):
        return "workbench"
    return None


def _could_overlap(problem: Mapping[str, Any], *, since: datetime | None, until: datetime | None) -> bool:
    """Whether a workbench problem could have been open during the window,
    from its timestamps alone (round 4): opened at or before the evaluated
    attempt and not closed before the window opened. Its book and hint state
    are never read: they are current, not as of the attempt. A tie, or a
    missing or unreadable time, could have been open."""

    opened = _second(problem["created_at"])
    if opened is not None and until is not None and opened > until:
        return False
    if problem["closed_at"] is None or since is None:
        return True
    closed = _second(problem["closed_at"])
    return closed is None or closed >= since


__all__ = [
    "INTO_ATTEMPT_UNKNOWN_REASONS", "REPORT_VERSION", "UNAIDED_UNKNOWN_REASONS", "build_hints_report", "item_caps",
]
