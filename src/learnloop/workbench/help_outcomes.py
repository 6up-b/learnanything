"""Reader workbench RW2c: what helps this learner, a replayable read (spec_reader_workbench_v1 §5.10, G39).

``help_outcomes(repository, facet_ids, as_of, item_facets=...)`` is a pure
function over rows that already exist. It opens the database read-only, reads
only what was stamped at or before ``as_of``, calls no model, reads no clock
and returns its lists in a fixed order, so the same ledgers and the same
``as_of`` give the same result (computed twice in the tests). It needs no
table, so no replayer (§11: "RW2c's help outcomes are pure reads").

**What it reads.**

* The workbench's ``help_assists`` rows (``surface = 'workbench'``, shown):
  hints (kind, strategy slug, level), bridges and worked examples (the
  passage's role), comparisons. A ``learner_pick`` row (RW2c's "another
  passage") is the learner choosing among a draw's options, not another help.
* **For hints, the hint service's own per-hint records**: the replies
  ("doesn't connect", ``judgment_ledger`` task ``hint_fit``) and, for the
  immediate continuation, the workbench's placement of the work, which the
  service hands to the Reader for this surface (adaptive hints H2b §9: "the
  step verdicts already place that work"; its outcome placement never runs on
  a workbench row). The grade-based "unaided next progress" of ``learnloop
  hints report`` is the practice screen's, and is not re-derived here.
* **For retrieval-supported help, the sources spec's S5 records**
  (``retrieval_interventions`` with ``retrieval_intervention_outcomes``:
  ``R_next``, ``R_cold`` and its censoring) instead of a second derivation;
  an outcome whose attempt is after ``as_of`` reads as pending, and a vault
  without those tables reads them as absent.
* Attempts (``practice_attempts``), the workbench's submitted problems and the
  diagnoser's typed causes (``attempt_diagnoses``, completed and live).

**What it returns**, per help kind on each requested facet:

* ``continuation``: whether the next shown check of the same problem, with no
  other hint shown in between, found a valid step the check before the help
  did not (``continued`` / ``not_continued``), or why it cannot say
  (``more_help`` / ``no_later_check``);
* ``attempt``: the grade of the attempt the help belonged to, when submitted;
* ``later_independent``: the next attempt on the same facet with no hint and
  not primed, after the help's attempt (or the help, when unsubmitted):
  ``pass`` / ``fail`` / ``ungraded`` / ``held``, and how many have no later
  observation yet (``pending``);
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


def _valid_chains(check: Mapping[str, Any] | None) -> set[str]:
    """The steps a check found valid, read through the one accessor of stored
    verdicts (only the verdict is read; its method's reading is not used, so
    the symbolic switch is irrelevant here and read as off)."""

    if check is None:
        return set()
    from learnloop.symbolic_view import verdict_records

    return {str(entry.get("chain_id")) for entry in verdict_records(check, enabled=False)
            if entry.get("verdict") == "valid"}


def _continuation(row: Mapping[str, Any], at: datetime, session_rows: Sequence[Mapping[str, Any]]) -> str:
    """The next shown check after the help, with no other hint between (module docstring)."""

    parent = _loads(row.get("placement_json"), {}).get("hint_assist_id")
    checks = [(other["_at"], other) for other in session_rows if other["assist_kind"] == "check"]
    before = [entry for entry in checks if entry[0] <= at and entry[1]["id"] != row["id"]]
    after = [entry for entry in checks if entry[0] > at]
    if not after:
        return "no_later_check"
    following_at, following = after[0]
    if any(other["assist_kind"] == "hint" and other["id"] not in (row["id"], parent)
           and at < other["_at"] < following_at for other in session_rows):
        return "more_help"
    prior = before[-1][1] if before else None
    gained = _valid_chains(following) - _valid_chains(prior)
    return "continued" if gained else "not_continued"


def help_outcomes(
    repository: Any,
    facet_ids: Iterable[str],
    as_of: str,
    *,
    item_facets: Mapping[str, Iterable[str]],
) -> HelpOutcomesV1:
    """The read (module docstring). ``repository``: a repository or a database
    path; ``item_facets``: each item's evidence facets (the vault's)."""

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
        held: set[str] = set()
        if attempts:
            from learnloop.held_grades import held_for_review_attempts

            held = {str(value) for value in held_for_review_attempts(connection, tuple(sorted(attempts)))}

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
                             "placement_json, step_verdicts_json, first_questionable_step_id, error_kind_guess "
                             "FROM help_assists WHERE surface = 'workbench' AND shown = 1"):
                at = _when(row["shown_at"] or row["requested_at"])
                if at is not None and at <= cutoff:
                    rows.append({**row, "_at": at})
            rows.sort(key=lambda row: (row["_at"], row["id"]))
            by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in rows:
                by_session[str(row["workbench_session_id"])].append(row)
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
                if row["assist_kind"] not in _HELP_KINDS or row.get("chooser") == "learner_pick":
                    continue
                key = _help_key(row)
                session_id = str(row["workbench_session_id"])
                attempt_id = row.get("attempt_id") or session_attempt.get(session_id)
                attempt = attempts.get(str(attempt_id)) if attempt_id else None
                continuation = (_continuation(row, row["_at"], by_session[session_id])
                                if row["assist_kind"] != "compare_methods" else None)
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
                    anchor = attempt["_at"] if attempt is not None else row["_at"]
                    target.later_independent[later(facet, anchor, str(attempt_id) if attempt_id else None)] += 1
                    for shortcut in replies.get(str(row["id"]), []):
                        target.doesnt_connect[shortcut] += 1
        else:
            sources["help_assists"] = "absent"

        # -- the sources spec's S5 records (retrieval-supported help) -----------------------
        if _table(connection, "retrieval_interventions") and _table(connection, "retrieval_intervention_outcomes"):
            sources["retrieval_intervention_outcomes"] = "read"
            outcomes = {str(row["intervention_id"]): row for row in _rows(
                connection, "SELECT intervention_id, next_attempt_id, next_correctness, next_assisted, "
                "cold_attempt_id, cold_outcome_state FROM retrieval_intervention_outcomes")}
            for row in _rows(connection, "SELECT id, created_at, kind, assets_json, targets_json "
                             "FROM retrieval_interventions ORDER BY created_at, id"):
                at = _when(row["created_at"])
                if at is None or at > cutoff:
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


def _s5_next(outcome: Mapping[str, Any] | None, attempts: Mapping[str, Any]) -> str:
    if outcome is None or not outcome.get("next_attempt_id") or str(outcome["next_attempt_id"]) not in attempts:
        return "no_later_attempt"
    if outcome.get("next_correctness") is None:
        return "ungraded"
    if outcome.get("next_assisted"):
        return "more_help"
    return "continued" if float(outcome["next_correctness"]) >= S5_SUCCESS else "not_continued"


def _s5_cold(outcome: Mapping[str, Any] | None, attempts: Mapping[str, Any]) -> str:
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
    return lines_for(help_outcomes(repository, facets, as_of, item_facets=every))


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
