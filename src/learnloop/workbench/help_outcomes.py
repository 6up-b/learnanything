"""Reader workbench RW2c: what helps this learner, a replayable read (spec_reader_workbench_v1 §5.10, G39).

``help_outcomes(repository, facet_ids, as_of, item_facets=...)`` is a pure
function over rows that already exist. It opens the database read-only, reads
only what was stamped at or before ``as_of``, calls no model, reads no clock
and returns its lists in a fixed order, so the same ledgers and the same
``as_of`` give the same result (computed twice in the tests). It needs no
table, so no replayer (§11: "RW2c's help outcomes are pure reads").

**What it reads.**

* The workbench's ``help_assists`` rows (``surface = 'workbench'``, shown):
  hints (kind, strategy slug, level; a hint the learner picked, "a smaller
  step" or "the book's way", is a hint like any other), bridges and worked
  examples (the passage's role), comparisons. A passage ``learner_pick`` row
  (RW2c's "another passage") is the learner choosing among a draw's options,
  not a help kind of its own; it still counts as further help after another
  help (review F3).
* **For hints, the hint service's own per-hint outcome**: the replies
  ("doesn't connect", ``judgment_ledger`` task ``hint_fit``) and unaided
  next progress as the service defines it for this surface
  (:func:`learnloop.hints.report_workbench.workbench_unaided_progress`:
  measured to the next valid step against the work at delivery, further help
  of any kind in between, unknown kept unknown; review F4). The same
  definition gives a passage's continuation.
* **For retrieval-supported help, the sources spec's S5 outcomes**
  (``R_next``, ``R_cold`` and its censoring) instead of a second derivation,
  read AS THEY STOOD at ``as_of`` through S5's own historical read
  (:func:`learnloop.substrate.intervention_outcomes.outcomes_as_of`: inputs
  written by then, the grades as they stood then, expiry judged at
  ``as_of``; fix round 2, 5), never today's persisted rows:
  a workbench passage an S5 record names by its assist id takes its later
  outcome from that record, and the record is not counted again on its own
  (review F10); every other S5 record is its own help. An outcome whose
  attempt is after ``as_of`` reads as pending, and a vault without those
  tables reads them as absent.
* Attempts (``practice_attempts``) **as graded at ``as_of``** (review F6): an
  attempt whose grading changed after ``as_of`` is read from the grading
  epoch standing then (``grading_epochs``, and RW6a's as-of hold), never from
  its current correctness; the workbench's submitted problems and the
  diagnoser's typed causes (``attempt_diagnoses``, completed and live).

**What it returns**, per help kind on each requested facet:

* ``continuation``: the hint service's unaided next progress (above):
  whether the next shown check of the same problem, with no further help in
  between, found a valid step new or changed since the help was delivered
  (``continued`` / ``not_continued``), or why it cannot say (``more_help`` /
  ``no_later_check`` / ``unknown``, no work recorded at delivery);
* ``attempt``: the grade of the attempt the help belonged to, when submitted;
* ``later_independent``: the next attempt on the same facet with no hint and
  not primed, after both the help's attempt and the help itself (help shown
  after its attempt, a comparison, gets no credit for what came before it;
  review F5): ``pass`` / ``fail`` / ``ungraded`` / ``held``, and how many
  have no later observation yet (``pending``);
* ``doesnt_connect``: the replies by shortcut.

And, per facet, **where the work tends to go off**: the check's error-kind
guesses on first questionable steps (labelled guesses) and the diagnoser's
causes at Submit (``causal_class``, the ``operation`` slug and the registry
match's id; the diagnoser is the authority), with counts and dates.

**Associations only** (§5.10): labelled "what preceded recovery for you",
never "what works". :func:`lines_for` gives the hint writer and the chooser
typed lines (kinds, levels, counts, outcomes and step ids, never text), so no
line can carry the item's answer or its reference solution.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import sqlite3
from typing import Any

from learnloop.db.connection import connect

VERSION = "help_outcomes.v1"
LABEL = "what preceded recovery for you (associations, not what works)"
GUESSES_LABEL = "the check's guesses, not a diagnosis"
CAUSES_LABEL = "the diagnoser's causes at Submit"
#: A correctness at or above this is a correct (or passing) attempt: the
#: attempt window's own "correct" (``instructional.policy.WINDOW_CLOSING_CORRECTNESS``).
CORRECT = 0.999
#: S5's report threshold for its next-attempt success (``intervention_outcomes.SUCCESS_CORRECTNESS``).
S5_SUCCESS = 0.5
#: How many help lines the writer and chooser are given per request, and how
#: many per facet (a prompt-size bound; the most observed come first).
MAX_LINES = 4
MAX_LINES_PER_FACET = 3
#: A strategy is a writer's slug; anything else is not carried (leak control).
_SLUG = re.compile(r"^[a-z][a-z0-9_]{0,47}$")
_HELP_KINDS = ("hint", "bridge", "example", "compare_methods")
_S5_COLD_PASS = ("cold_success",)
_S5_COLD_FAIL = ("cold_failure", "cold_dont_know")
_S5_COLD_PENDING = ("right_censored_pending",)


def _when(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _loads(value: Any, default: Any) -> Any:
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def _table(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (name,)).fetchone() is not None


def _grade(correctness: Any) -> str:
    if correctness is None:
        return "ungraded"
    value = float(correctness)
    return "correct" if value >= CORRECT else "partial" if value > 0 else "incorrect"


def _day(value: datetime | None) -> str | None:
    return value.date().isoformat() if value is not None else None


def safe_slug(value: Any) -> str | None:
    """A strategy slug the lines may carry, or None (free text never is)."""

    text = str(value or "").strip()
    return text if _SLUG.match(text) else None


@dataclass
class HelpKindOutcome:
    """One help kind on one facet (module docstring)."""

    facet_id: str
    help: str
    kind: str | None
    strategy: str | None
    shown: int = 0
    levels: Counter = field(default_factory=Counter)
    continuation: Counter = field(default_factory=Counter)
    attempt: Counter = field(default_factory=Counter)
    later_independent: Counter = field(default_factory=Counter)
    doesnt_connect: Counter = field(default_factory=Counter)
    source: str = "help_assists"
    first_at: str | None = None
    last_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "facet_id": self.facet_id, "help": self.help, "kind": self.kind, "strategy": self.strategy,
            "source": self.source, "shown": self.shown,
            "levels": {str(key): self.levels[key] for key in sorted(self.levels, key=str)},
            "continuation": {key: self.continuation[key] for key in sorted(self.continuation)},
            "attempt": {key: self.attempt[key] for key in sorted(self.attempt)},
            "later_independent": {key: self.later_independent[key] for key in sorted(self.later_independent)},
            "doesnt_connect": {key: self.doesnt_connect[key] for key in sorted(self.doesnt_connect)},
            "first_at": self.first_at, "last_at": self.last_at,
        }


@dataclass
class GoesOff:
    """Where the work tends to go off on one facet (module docstring)."""

    facet_id: str
    guesses: Counter = field(default_factory=Counter)
    guess_last: dict[str, str] = field(default_factory=dict)
    causes: Counter = field(default_factory=Counter)
    cause_last: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "facet_id": self.facet_id,
            "first_questionable_guesses": [{"kind": key, "count": self.guesses[key], "last": self.guess_last.get(key)}
                                           for key in sorted(self.guesses)],
            "guesses_are": GUESSES_LABEL,
            "diagnosed_causes": [{"cause": key, "count": self.causes[key], "last": self.cause_last.get(key)}
                                 for key in sorted(self.causes)],
            "causes_are": CAUSES_LABEL,
        }

    @property
    def empty(self) -> bool:
        return not self.guesses and not self.causes


@dataclass
class HelpOutcomesV1:
    version: str
    as_of: str
    facet_ids: tuple[str, ...]
    helps: list[HelpKindOutcome]
    goes_off: list[GoesOff]
    sources: dict[str, str]
    label: str = LABEL

    def as_dict(self) -> dict[str, Any]:
        return {"version": self.version, "label": self.label, "as_of": self.as_of,
                "facet_ids": list(self.facet_ids), "sources": dict(sorted(self.sources.items())),
                "helps": [entry.as_dict() for entry in self.helps],
                "goes_off": [entry.as_dict() for entry in self.goes_off]}


# ---------------------------------------------------------------------------
# The read
# ---------------------------------------------------------------------------

def _rows(connection: sqlite3.Connection, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
    connection.row_factory = sqlite3.Row
    return [dict(row) for row in connection.execute(sql, tuple(params)).fetchall()]


def _help_key(row: Mapping[str, Any]) -> tuple[str, str | None, str | None]:
    kind = str(row["assist_kind"])
    if kind == "hint":
        return "hint", str(row.get("hint_kind") or "") or None, safe_slug(row.get("strategy"))
    if kind in ("bridge", "example"):
        placement = _loads(row.get("placement_json"), {})
        role = safe_slug(placement.get("role")) or ("worked_example" if kind == "example" else None)
        return kind, role, None
    return kind, None, None


#: Passage kinds whose ``learner_pick`` rows are a choice among a draw's
#: options ("another passage"), not a help kind of their own (review F3).
_PASSAGE_KINDS = ("bridge", "example")


def _passage_pick(row: Mapping[str, Any]) -> bool:
    return row.get("assist_kind") in _PASSAGE_KINDS and row.get("chooser") == "learner_pick"


def _after(value: Any, cutoff: datetime) -> bool:
    """Was this stamp written after the cutoff? (An unreadable stamp is not.)"""

    when = _when(value)
    return when is not None and when > cutoff


def _grades_at(connection: sqlite3.Connection, attempts: Mapping[str, Mapping[str, Any]], cutoff: datetime,
               vault: Any | None) -> dict[str, tuple[Any, bool]]:
    """``(correctness, held)`` of each attempt as the grading ledger stood at
    the cutoff (review F6), with the shared grading-history machinery.

    An attempt with no grading row and no blind grade record written (or
    superseded) after the cutoff has the same current epoch then as now: its
    stored correctness and today's held predicate
    (:func:`learnloop.held_grades.held_for_review_attempts`). Otherwise the
    rows standing at the cutoff are read (a row superseded later still stood
    then; a row written later had not happened), exactly as RW6a's
    ``facet_evidence_timeline.snapshot_as_of`` reads them: the current epoch
    among them (:func:`learnloop.grading_epochs.current_epoch`) gives the
    score (its points summed, as the score is summed) over the item's rubric
    maximum (the regrade's own ``score / max(max_points, 1)``); no epoch then,
    or no rubric to divide by, is ungraded. The hold at the cutoff is the
    route rule over the blind records written by then and that epoch's
    assessed criteria (``outcome_contract.grade_is_held``), or replay's
    unrecorded-contract hold decided from that epoch as RW6a decides it."""

    from types import SimpleNamespace

    from learnloop.held_grades import held_for_review_attempts

    ids = sorted(attempts)
    if not ids:
        return {}
    held_now = held_for_review_attempts(connection, ids)
    evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    blind: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        marks = ", ".join("?" for _ in chunk)
        if _table(connection, "grading_evidence"):
            for row in _rows(connection, "SELECT id, attempt_id, criterion_id, points_awarded, created_at, "
                             "superseded_at, grading_revision, assessment_contract_version_id, attribution_json "
                             f"FROM grading_evidence WHERE attempt_id IN ({marks})", chunk):
                evidence[str(row["attempt_id"])].append(row)
        if _table(connection, "blind_grade_records"):
            for row in _rows(connection, "SELECT id, attempt_id, record_json, created_at FROM blind_grade_records "
                             f"WHERE attempt_id IN ({marks})", chunk):
                blind[str(row["attempt_id"])].append(row)
    out: dict[str, tuple[Any, bool]] = {}
    for attempt_id in ids:
        attempt = attempts[attempt_id]
        rows = evidence.get(attempt_id, [])
        records = blind.get(attempt_id, [])
        changed = any(_after(row["created_at"], cutoff) or _after(row["superseded_at"], cutoff) for row in rows) \
            or any(_after(record["created_at"], cutoff) for record in records)
        if not changed:
            out[attempt_id] = (attempt["correctness"], attempt_id in held_now)
            continue
        out[attempt_id] = _grade_from_ledger(attempt, rows, records, cutoff, vault, SimpleNamespace)
    return out


def _grade_from_ledger(attempt: Mapping[str, Any], rows: Sequence[Mapping[str, Any]],
                       records: Sequence[Mapping[str, Any]], cutoff: datetime, vault: Any | None,
                       namespace: Any) -> tuple[Any, bool]:
    from learnloop.grading_epochs import current_epoch
    from learnloop.learner.facet_evidence_timeline import epoch_held_as_of
    from learnloop.outcome_contract import grade_held_for_review, grade_is_held, unassessed_evidence_row

    standing = [namespace(**{**row, "superseded_at": None if _after(row["superseded_at"], cutoff)
                             else row["superseded_at"]})
                for row in rows if not _after(row["created_at"], cutoff)]
    epoch = current_epoch(standing)
    if epoch is None:
        return None, False  # not graded yet at the cutoff
    item_id = str(attempt["practice_item_id"])
    item = vault.practice_items.get(item_id) if vault is not None else None
    rubric = vault.rubric_for_item(item) if item is not None else None
    score = int(round(sum(float(row.points_awarded or 0.0) for row in epoch.rows)))
    correctness = (score / max(int(rubric.max_points), 1)) if rubric is not None else None
    live = [row for row in standing if row.superseded_at is None]
    criteria = {str(row.criterion_id) for row in live}
    unassessed = {str(row.criterion_id) for row in live if unassessed_evidence_row(row.attribution_json)}
    record_held = False
    written = [record for record in records if not _after(record["created_at"], cutoff)]
    if written:
        latest = max(written, key=lambda record: (str(record["created_at"]), str(record["id"])))
        decoded = _loads(latest["record_json"], {})
        record_held = isinstance(decoded, Mapping) and grade_held_for_review(decoded.get("grading_support"))
    held = bool(record_held) and grade_is_held(record_held=True, anything_assessed=bool(criteria - unassessed))
    held = held or epoch_held_as_of(tuple(standing), vault, item_id)
    return correctness, held


def help_outcomes(
    repository: Any,
    facet_ids: Iterable[str],
    as_of: str,
    *,
    item_facets: Mapping[str, Iterable[str]],
    vault: Any | None = None,
) -> HelpOutcomesV1:
    """The read (module docstring). ``repository``: a repository or a database
    path; ``item_facets``: each item's evidence facets (the vault's);
    ``vault``: for an attempt regraded after ``as_of``, the item's rubric
    maximum its grade at ``as_of`` is read against (without it such an
    attempt reads as ungraded at ``as_of``, never as its later grade)."""

    wanted = tuple(dict.fromkeys(str(facet) for facet in facet_ids if facet))
    cutoff = _when(as_of)
    if cutoff is None:
        raise ValueError(f"as_of {as_of!r} is not an ISO time")
    facets_of = {str(item): {str(facet) for facet in values} for item, values in item_facets.items()}
    path = Path(getattr(repository, "sqlite_path", repository))
    sources: dict[str, str] = {}
    helps: dict[tuple[str, str, str | None, str | None], HelpKindOutcome] = {}
    goes: dict[str, GoesOff] = {facet: GoesOff(facet) for facet in wanted}
    if not wanted:
        return HelpOutcomesV1(VERSION, cutoff.isoformat(), wanted, [], [], {"facets": "none_requested"})

    def entry(facet: str, key: tuple[str, str | None, str | None], source: str) -> HelpKindOutcome:
        found = helps.get((facet, *key))
        if found is None:
            found = helps[(facet, *key)] = HelpKindOutcome(facet, key[0], key[1], key[2], source=source)
        return found

    def stamp(target: HelpKindOutcome, at: datetime) -> None:
        iso = at.isoformat()
        target.first_at = min(filter(None, (target.first_at, iso)))
        target.last_at = max(filter(None, (target.last_at, iso)))

    session_attempt: dict[str, str] = {}
    with closing(connect(path, read_only=True)) as connection:
        attempts = {row["id"]: {**row, "_at": _when(row["created_at"])} for row in _rows(
            connection, "SELECT id, practice_item_id, correctness, hints_used, primed, created_at, "
            "evidence_facets_json FROM practice_attempts")}
        attempts = {key: value for key, value in attempts.items()
                    if value["_at"] is not None and value["_at"] <= cutoff}
        # Each attempt's grade and hold AS OF the cutoff (review F6): a later
        # regrade or adjudication never changes what this read says of T.
        graded = _grades_at(connection, attempts, cutoff, vault)
        for attempt_id, (correctness, _held) in graded.items():
            attempts[attempt_id] = {**attempts[attempt_id], "correctness": correctness}
        held = {attempt_id for attempt_id, (_correctness, is_held) in graded.items() if is_held}
        # Fix round 2 (5): S5's outcomes AS THEY STOOD at the cutoff, from
        # S5's own historical read (inputs written by then, the grades above,
        # expiry judged at the cutoff), never today's persisted rows.
        s5_outcomes = _s5_outcomes_at(connection, vault, cutoff, graded)

        def attempt_facets(attempt: Mapping[str, Any]) -> set[str]:
            # The facets recorded with the attempt, and the item's (canonical) now.
            recorded = _loads(attempt.get("evidence_facets_json"), None)
            found = {str(value) for value in recorded} if isinstance(recorded, list) else set()
            return found | facets_of.get(str(attempt["practice_item_id"]), set())

        independent = sorted(
            (value for value in attempts.values()
             if not int(value["hints_used"] or 0) and not int(value["primed"] or 0)),
            key=lambda value: (value["_at"], value["id"]))

        def later(facet: str, after: datetime, exclude: str | None) -> str:
            for candidate in independent:
                if candidate["_at"] > after and candidate["id"] != exclude and facet in attempt_facets(candidate):
                    if candidate["id"] in held:
                        return "held"
                    grade = _grade(candidate["correctness"])
                    return "ungraded" if grade == "ungraded" else ("pass" if grade == "correct" else "fail")
            return "pending"

        def attempt_grade(attempt_id: str | None) -> str:
            attempt = attempts.get(str(attempt_id)) if attempt_id else None
            if attempt is None:
                return "not_submitted"
            return "held" if attempt["id"] in held else _grade(attempt["correctness"])

        # -- the workbench's help rows ------------------------------------------------------
        if _table(connection, "help_assists"):
            sources["help_assists"] = "read"
            rows = []
            for row in _rows(connection, "SELECT id, assist_kind, hint_kind, level, strategy, practice_item_id, "
                             "workbench_session_id, attempt_id, shown, shown_at, requested_at, chooser, "
                             "placement_json, step_snapshot_json, step_verdicts_json, first_questionable_step_id, "
                             "error_kind_guess, map_id, route_id, from_node_id, target_node_id "
                             "FROM help_assists WHERE surface = 'workbench' AND shown = 1"):
                at = _when(row["shown_at"] or row["requested_at"])
                if at is not None and at <= cutoff:
                    rows.append({**row, "_at": at})
            rows.sort(key=lambda row: (row["_at"], row["id"]))
            by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in rows:
                by_session[str(row["workbench_session_id"])].append(row)
            # The hint service's per-help outcome (review F4): one definition,
            # read here, never derived again (C13). Map structure only (node
            # ids), for the next hint's placement; nothing of it is returned.
            from learnloop.hints import report_adaptive
            from learnloop.hints.report_workbench import workbench_unaided_progress

            maps = report_adaptive.map_paths(connection, (row.get("map_id") for row in rows))
            # S5 records that name a workbench passage by its assist id (review
            # F10): that record's later outcome is the passage's.
            linked, counted = _s5_links(connection, {str(row["id"]) for row in rows
                                                     if row["assist_kind"] in _PASSAGE_KINDS}, cutoff,
                                        s5_outcomes if s5_outcomes is not None else {})
            if _table(connection, "workbench_sessions"):
                for row in _rows(connection, "SELECT id, attempt_id FROM workbench_sessions "
                                 "WHERE attempt_id IS NOT NULL"):
                    session_attempt[str(row["id"])] = str(row["attempt_id"])
            replies: dict[str, list[str]] = defaultdict(list)
            for fit in _rows(connection, "SELECT left_id, rationale, created_at FROM judgment_ledger "
                             "WHERE task = 'hint_fit' ORDER BY created_at, id"):
                at = _when(fit["created_at"])
                if at is not None and at <= cutoff:
                    replies[str(fit["left_id"])].append(
                        str(_loads(fit["rationale"], {}).get("shortcut") or "none"))
            for row in rows:
                item_facets_now = facets_of.get(str(row["practice_item_id"] or ""), set())
                if row["assist_kind"] == "check":
                    first = row.get("first_questionable_step_id")
                    guess = safe_slug(row.get("error_kind_guess"))
                    for facet in wanted:
                        if first and guess and facet in item_facets_now:
                            goes[facet].guesses[guess] += 1
                            goes[facet].guess_last[guess] = max(
                                filter(None, (goes[facet].guess_last.get(guess), _day(row["_at"]))))
                    continue
                # Review F3: only a passage pick ("another passage") is not a
                # help kind of its own; a hint the learner picked is a hint.
                if row["assist_kind"] not in _HELP_KINDS or _passage_pick(row):
                    continue
                key = _help_key(row)
                session_id = str(row["workbench_session_id"])
                attempt_id = row.get("attempt_id") or session_attempt.get(session_id)
                attempt = attempts.get(str(attempt_id)) if attempt_id else None
                continuation = (workbench_unaided_progress(row, by_session[session_id], maps=maps)
                                if row["assist_kind"] != "compare_methods" else None)
                s5_linked = str(row["id"]) in linked
                s5 = linked.get(str(row["id"]))
                for facet in wanted:
                    if facet not in item_facets_now:
                        continue
                    target = entry(facet, key, "help_assists")
                    target.shown += 1
                    stamp(target, row["_at"])
                    if row.get("level"):
                        target.levels[int(row["level"])] += 1
                    if continuation is not None:
                        target.continuation[continuation] += 1
                    target.attempt[attempt_grade(attempt_id)] += 1
                    if s5_linked:
                        # S5 is the authority on what followed (its R_cold
                        # with censoring), not a second derivation (F10).
                        target.later_independent[_s5_cold(s5, attempts)] += 1
                    else:
                        # Review F5: never before the help itself was shown
                        # (help after its attempt, a comparison opened later,
                        # gets no credit for what came between).
                        anchor = max(attempt["_at"], row["_at"]) if attempt is not None else row["_at"]
                        target.later_independent[later(facet, anchor, str(attempt_id) if attempt_id else None)] += 1
                    for shortcut in replies.get(str(row["id"]), []):
                        target.doesnt_connect[shortcut] += 1
        else:
            sources["help_assists"] = "absent"
            linked, counted = {}, set()

        # -- the sources spec's S5 records (retrieval-supported help) -----------------------
        if s5_outcomes is not None:
            # Without the vault S5 cannot judge its targets or exposures:
            # its outcomes are unknown, never guessed (fix round 2, 5).
            sources["retrieval_intervention_outcomes"] = "read" if vault is not None else "read_without_vault"
            outcomes = s5_outcomes
            for row in _rows(connection, "SELECT id, created_at, kind, assets_json, targets_json "
                             "FROM retrieval_interventions ORDER BY created_at, id"):
                at = _when(row["created_at"])
                if at is None or at > cutoff or str(row["id"]) in counted:
                    # A record that names a workbench passage is that passage's
                    # outcome, counted once, with it (review F10).
                    continue
                targets = _loads(row["targets_json"], {})
                facets = {str(value) for value in targets.get("facets") or ()}
                if not facets:
                    for item_id in _loads(row["assets_json"], {}).get("practice_item_ids") or ():
                        facets |= facets_of.get(str(item_id), set())
                outcome = outcomes.get(str(row["id"]))
                for facet in wanted:
                    if facet not in facets:
                        continue
                    target = entry(facet, ("retrieval", safe_slug(row["kind"]), None),
                                   "retrieval_intervention_outcomes")
                    target.shown += 1
                    stamp(target, at)
                    target.continuation[_s5_next(outcome, attempts)] += 1
                    target.later_independent[_s5_cold(outcome, attempts)] += 1
        else:
            sources["retrieval_intervention_outcomes"] = "absent"

        # -- the diagnoser's causes at Submit, on the workbench's submitted problems ---------
        submitted = set(session_attempt.values())
        if submitted and _table(connection, "attempt_diagnoses"):
            latest: dict[str, dict[str, Any]] = {}
            for row in _rows(connection, "SELECT id, attempt_id, proposal_json, created_at FROM attempt_diagnoses "
                             "WHERE status = 'completed' AND mode = 'live' ORDER BY created_at, id"):
                at = _when(row["created_at"])
                if at is not None and at <= cutoff and str(row["attempt_id"]) in submitted:
                    latest[str(row["attempt_id"])] = {**row, "_at": at}
            for attempt_id, row in sorted(latest.items()):
                attempt = attempts.get(attempt_id)
                if attempt is None:
                    continue
                facets = attempt_facets(attempt)
                for cause in _causes(row.get("proposal_json")):
                    for facet in wanted:
                        if facet in facets:
                            goes[facet].causes[cause] += 1
                            goes[facet].cause_last[cause] = max(
                                filter(None, (goes[facet].cause_last.get(cause), _day(row["_at"]))))
    ordered = sorted(helps.values(), key=lambda value: (value.facet_id, value.help, value.kind or "",
                                                        value.strategy or ""))
    return HelpOutcomesV1(VERSION, cutoff.isoformat(), wanted, ordered,
                          [goes[facet] for facet in wanted if not goes[facet].empty], sources)


def _s5_outcomes_at(connection: sqlite3.Connection, vault: Any | None, cutoff: datetime,
                    graded: Mapping[str, tuple[Any, bool]]) -> Mapping[str, Any] | None:
    """S5's outcomes at ``cutoff`` by intervention id (fix round 2, 5), from
    the sources spec's own historical read
    (:func:`learnloop.substrate.intervention_outcomes.outcomes_as_of`) over the
    grades as they stood then; None when S5's tables are absent. Without a
    vault every record reads :data:`UNJUDGED` (unknown, never a guess)."""

    if not (_table(connection, "retrieval_interventions") and _table(connection, "retrieval_intervention_outcomes")):
        return None
    if vault is None:
        return _Unjudged()
    from learnloop.substrate.intervention_outcomes import outcomes_as_of

    return outcomes_as_of(vault, connection, cutoff, grades=graded)


#: An S5 outcome that could not be judged (no vault given).
UNJUDGED: Mapping[str, Any] = {"unjudged": True}


class _Unjudged(Mapping[str, Any]):
    """Every intervention's outcome is :data:`UNJUDGED` (no vault given)."""

    def __getitem__(self, key: str) -> Any:
        return UNJUDGED

    def __iter__(self) -> Any:
        return iter(())

    def __len__(self) -> int:
        return 0


def _s5_links(connection: sqlite3.Connection, assist_ids: set[str], cutoff: datetime,
              outcomes: Mapping[str, Any]) -> tuple[dict[str, Mapping[str, Any] | None], set[str]]:
    """The S5 records that name a workbench passage BY ITS ASSIST ID (the
    record's ``caller_ref``, or ``assets.help_assist_id``; never a match on
    time, item or spans), written by ``cutoff``: ``({assist id: its outcome
    row or None}, {those records' ids})``. Neither the bridge nor the worked
    example writes such a record today; when the sources spec's S5 records a
    workbench passage (Reader §18 item 5 copies the draw's propensity and seed
    into it), this is where its outcome becomes the passage's (review F10)."""

    if not assist_ids or not (_table(connection, "retrieval_interventions")
                              and _table(connection, "retrieval_intervention_outcomes")):
        return {}, set()
    linked: dict[str, Mapping[str, Any] | None] = {}
    counted: set[str] = set()
    for row in _rows(connection, "SELECT id, created_at, caller_ref, assets_json FROM retrieval_interventions "
                     "ORDER BY created_at, id"):
        at = _when(row["created_at"])
        if at is None or at > cutoff:
            continue
        assets = _loads(row["assets_json"], {})
        named = {str(row["caller_ref"] or "")} | (
            {str(assets.get("help_assist_id"))} if isinstance(assets, Mapping) and assets.get("help_assist_id")
            else set())
        for assist_id in sorted(named & assist_ids):
            if assist_id not in linked:  # the first record that names it
                linked[assist_id] = outcomes.get(str(row["id"]))
            counted.add(str(row["id"]))
    return linked, counted


def _s5_next(outcome: Mapping[str, Any] | None, attempts: Mapping[str, Any]) -> str:
    if outcome is UNJUDGED:
        return "unknown"
    if outcome is None or not outcome.get("next_attempt_id") or str(outcome["next_attempt_id"]) not in attempts:
        return "no_later_attempt"
    if outcome.get("next_correctness") is None:
        return "ungraded"
    if outcome.get("next_assisted"):
        return "more_help"
    return "continued" if float(outcome["next_correctness"]) >= S5_SUCCESS else "not_continued"


def _s5_cold(outcome: Mapping[str, Any] | None, attempts: Mapping[str, Any]) -> str:
    if outcome is UNJUDGED:
        return "unmeasured"
    if outcome is None:
        return "pending"
    state = str(outcome.get("cold_outcome_state") or "")
    cold = outcome.get("cold_attempt_id")
    if cold and str(cold) not in attempts:
        return "pending"  # observed after as_of: not yet, at as_of
    if state in _S5_COLD_PASS:
        return "pass"
    if state in _S5_COLD_FAIL:
        return "fail"
    if state in _S5_COLD_PENDING:
        return "pending"
    return safe_slug(state) or "unmeasured"


def _causes(proposal_json: Any) -> list[str]:
    """The diagnoser's typed causes: never a statement or a quote."""

    proposal = _loads(proposal_json, {})
    found: list[str] = []
    for event in proposal.get("event_diagnoses") or ():
        if not isinstance(event, Mapping):
            continue
        operation = safe_slug(event.get("operation"))
        causal = safe_slug(event.get("causal_class"))
        match = event.get("registry_match") or {}
        ident = match.get("id") if isinstance(match, Mapping) and match.get("kind") in ("durable", "candidate") \
            else None
        cause = operation or causal
        if cause:
            found.append(cause)
        if ident and re.match(r"^[A-Za-z0-9_.:-]{1,80}$", str(ident)):
            found.append(f"misconception:{ident}")
    return found


# ---------------------------------------------------------------------------
# The lines given to the hint writer and the chooser
# ---------------------------------------------------------------------------

def lines_for(outcomes: HelpOutcomesV1, *, limit: int = MAX_LINES,
              per_facet: int = MAX_LINES_PER_FACET) -> tuple[dict[str, Any], ...]:
    """Typed lines (kinds, levels, counts, outcomes; never text): per facet,
    the help kinds shown most, then those with the most observed outcomes
    (a continuation or a later independent attempt), then the most recent;
    then where the work goes off. Empty when there is no history (so the
    caller's request is unchanged)."""

    def outcomes_observed(value: HelpKindOutcome) -> int:
        return (value.continuation.get("continued", 0) + value.continuation.get("not_continued", 0)
                + value.later_independent.get("pass", 0) + value.later_independent.get("fail", 0))

    lines: list[dict[str, Any]] = []
    by_facet: dict[str, list[HelpKindOutcome]] = defaultdict(list)
    for entry in outcomes.helps:
        by_facet[entry.facet_id].append(entry)
    for facet in outcomes.facet_ids:
        ranked = sorted(by_facet.get(facet, []), key=lambda value: (value.help, value.kind or "",
                                                                    value.strategy or ""))
        ranked.sort(key=lambda value: value.last_at or "", reverse=True)
        ranked.sort(key=lambda value: (-value.shown, -outcomes_observed(value)))
        for entry in ranked[:per_facet]:
            continuation = entry.continuation
            # A separate name from the ranking key above (fix: rebinding it
            # here made the second facet's sort call an int).
            observed = continuation.get("continued", 0) + continuation.get("not_continued", 0)
            later = entry.later_independent
            lines.append({
                "line": "help_outcome", "facet": facet, "help": entry.help, "kind": entry.kind,
                "strategy": entry.strategy, "levels": {str(key): entry.levels[key] for key in sorted(entry.levels)},
                "shown": entry.shown,
                "continued_unaided": continuation.get("continued", 0), "continuation_observed": observed,
                "more_help_followed": continuation.get("more_help", 0),
                "attempt_grades": {key: entry.attempt[key] for key in sorted(entry.attempt)},
                "later_independent": {key: later.get(key, 0) for key in ("pass", "fail", "pending")},
                "doesnt_connect": sum(entry.doesnt_connect.values()),
            })
    for goes in outcomes.goes_off:
        lines.append({
            "line": "goes_off", "facet": goes.facet_id,
            "first_questionable_guesses": {key: goes.guesses[key] for key in sorted(goes.guesses)},
            "guesses_are": GUESSES_LABEL,
            "diagnosed_causes": {key: goes.causes[key] for key in sorted(goes.causes)},
            "causes_are": CAUSES_LABEL,
        })
    help_lines = [line for line in lines if line["line"] == "help_outcome"][:limit]
    goes_lines = [line for line in lines if line["line"] == "goes_off"][:limit]
    if not help_lines and not goes_lines:
        return ()
    return tuple([{"line": "label", "label": LABEL}] + help_lines + goes_lines)


def item_facets_of(vault: Any) -> dict[str, list[str]]:
    """Each item's evidence facets, canonical (the vault's)."""

    canonical = getattr(vault, "canonical_facet_id", None)
    found: dict[str, list[str]] = {}
    for item_id, item in sorted(vault.practice_items.items()):
        facets = [str(canonical(str(facet)) if canonical else facet) for facet in item.evidence_facets]
        found[str(item_id)] = sorted(set(facets))
    return found


def lines_for_item(vault: Any, repository: Any, item: Any, *, as_of: str) -> tuple[dict[str, Any], ...]:
    """The lines for one item's facets at ``as_of`` (the workbench's hint context)."""

    every = item_facets_of(vault)
    facets = every.get(str(item.id), [])
    if not facets:
        return ()
    return lines_for(help_outcomes(repository, facets, as_of, item_facets=every, vault=vault))


__all__ = [
    "CAUSES_LABEL",
    "GUESSES_LABEL",
    "GoesOff",
    "HelpKindOutcome",
    "HelpOutcomesV1",
    "LABEL",
    "VERSION",
    "help_outcomes",
    "item_facets_of",
    "lines_for",
    "lines_for_item",
    "safe_slug",
]
