"""Router R1: ``router_outcomes`` (DERIVED, one replayer) per logged decision.

The Pipeline plan's outcome (``docs/brainstorming/Pipeline Augmentation
Plan.md``, "Outcome and cost contract"):

    S = alpha R_cold + (1 - alpha) R_next,   alpha = 0.75

* ``R_next``: success on the first fresh, unassisted, independently attempted
  item on the decision's learning object after the action. Fresh = a different
  item from the action's; unassisted = no hints, not primed; independent = an
  independent attempt type, human origin, a scorable resolved grade (PF-c
  nothing-assessed answers and grades the proofs route check holds for review
  excluded), the outcome contract's own rules
  (``outcome_contract.retention_exclusions``) minus its delay rules.
* ``R_cold``: success on the next eligible delayed cold retrieval on that
  learning object under the reveal ledger: an attempt at least one day after
  the last exposure to the learning object, where an exposure is any attempt on
  it or any reveal on the item or the learning object (``reveal_events``), in
  a different session from that last attempt, and unassisted as above.

The action is what the decision served and the learner answered, bound by the
most exact receipt that exists (router R2a, ``router_outcomes_v2``; plan §5.4):

1. **presentation** (``action_binding = presentation``): a ``plan_block``
   decision's block -> its ``plan_presentations`` in serving order -> the first
   one an attempt answered (``practice_attempts.plan_presentation_id``). The
   action is the item the learner was actually served and answered, not the
   block's first planned item;
2. **candidate** (``candidate``): a Today offer's head is taken when an attempt
   is bound to its scheduler candidate; a learner pick's when an attempt is
   bound to the picked candidate (R1);
3. **session rule** (``session_rule``, the labelled fallback): the first
   attempt on the decision's chosen item at or after the decision in its
   session (R1's rule), kept only for rows and clients with no receipt (a
   ``plan_block`` row from before R2a, a ``staged_p2`` row, an attempt sent
   with no presentation id: an older client or the TUI). It never takes an
   attempt bound to a presentation: that attempt answered the step that
   presentation names, which is not this decision's. R3 reports the mix and
   may exclude it.

An attempt on an unverified answer key is an outcome like any other (owner
Q13); its ``reference_status`` is recorded beside R_next and R_cold. An
untaken head is
``overridden`` (a learner pick from the same offer), ``superseded`` (a later
decision in its session), ``not_taken`` (its session ended) or ``open``. An
outcome with no eligible attempt yet is ``pending``: right-censored at
``observed_through`` (the newest attempt in the ledger), never a failure.
Values are the attempt's ``correctness`` in [0, 1].

``S`` follows the plan's rule that R_next makes it provisional and only R_cold
finalizes it. An observed R_cold makes ``S`` final: with the R_next observed at
or before the cold attempt, ``S = 0.75 R_cold + 0.25 R_next``; with none, the
R_next window is closed (``not_applicable``, ``closed_by_r_cold``: a "next"
attempt after the cold retrieval is not immediate uptake) and ``S = R_cold``.
So a final ``S`` never moves. R_next is also ``not_applicable`` when the
learning object has no other servable item (``no_other_servable_item``): it
could never be observed, so it is not reported as pending forever.

**Coldness is learned, not hard-coded** (owner decision D12, spec §15.2). The
one-day R_cold rule above stays as a provisional label. Each outcome also
records, for its R_next and R_cold attempts, the covariates a learned coldness
is fitted from (R3): the time since the last exposure to the attempt's item,
its facets and its learning object (an attempt, a reveal, a tutor question or a
reading of the source), the attempts in between (since the last exposure to
the learning object), the FSRS-predicted retrievability at the attempt (the
caller's ``retrievability_by_attempt``) and the reveal-ledger amount since the
last attempt on the learning object. ``coldness_candidates_json`` lists the
same covariates, the answer and the rule's verdict for every later attempt the
rule considered (at most ``COLDNESS_CANDIDATE_CAP``), so a learned coldness is
not limited to the rule's own pick.

Deterministic from ledgers (``router_decisions``, ``practice_attempts``,
grading evidence through the caller's PF-c states, ``reveal_events``,
``question_events``, ``source_exposure_events``, ``sessions.ended_at``) and the
caller's maps (servable items per learning object from vault content; the FSRS
prediction per attempt): no clock, no model call. It imports no scheduler or
substrate code.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import defaultdict
from collections.abc import Mapping
import json
import sqlite3
from typing import Any

from learnloop.clock import parse_utc
from learnloop.db.stores.plan_presentations import presentations_for_blocks
from learnloop.db.stores.router import replace_router_outcomes
from learnloop.outcome_contract import RETENTION_MIN_DELAY_SECONDS, retention_exclusions

OUTCOME_VERSION = "router_outcomes_v2"

#: How an action attempt was bound (plan §5.4), most exact first.
BINDING_PRESENTATION = "presentation"
BINDING_CANDIDATE = "candidate"
BINDING_SESSION_RULE = "session_rule"

#: The Pipeline plan's declared policy weight on durable retrieval.
S_ALPHA = 0.75

#: Attempt types that count as an independent attempt for R_next and R_cold.
INDEPENDENT_ATTEMPT_TYPES: frozenset[str] = frozenset(
    {"independent_attempt", "dont_know", "diagnostic_probe", "open_text", "exam_attempt"}
)

#: The outcome contract's delay rules, which R_next does not apply.
_DELAY_REASONS = frozenset({"insufficient_delay", "same_session", "intervening_practice"})

_ATTEMPT_COLUMNS = (
    "id, practice_item_id, learning_object_id, session_id, created_at, "
    "scheduler_candidate_id, attempt_type, hints_used, primed, correctness, "
    "manual_review, manual_review_reason, evidence_origin, evidence_facets_json"
)
#: Columns later migrations added, read when present (202: the presentation
#: an attempt answers; 188: its answer-key status).
_OPTIONAL_ATTEMPT_COLUMNS = ("plan_presentation_id", "reference_status")

#: The provisional R_cold rule's name (D12: a label until R3 fits coldness).
R_COLD_RULE = "provisional_one_day"
#: Later attempts listed per outcome in ``coldness_candidates_json``.
COLDNESS_CANDIDATE_CAP = 20
#: The covariates recorded per outcome attempt (column suffixes).
COVARIATE_NAMES: tuple[str, ...] = (
    "since_item_seconds",
    "since_facet_seconds",
    "since_lo_seconds",
    "intervening_attempts",
    "predicted_retrievability",
    "reveal_amount",
)

#: An exposure: (created_at, tie-break, kind, linked attempt id). Attempts sort
#: by (created_at, id); other events sort before an attempt at the same instant.
_Exposure = tuple[str, str, str, "str | None"]


def _facet_ids(raw: Any) -> tuple[str, ...]:
    """Facet ids from an ``evidence_facets_json`` / ``facets_json`` value."""

    if not raw:
        return ()
    try:
        value = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return ()
    if isinstance(value, Mapping):
        value = list(value)
    ids: list[str] = []
    for entry in value if isinstance(value, list) else ():
        if isinstance(entry, str):
            ids.append(entry)
        elif isinstance(entry, Mapping) and isinstance(entry.get("id") or entry.get("facet_id"), str):
            ids.append(entry.get("id") or entry.get("facet_id"))
    return tuple(dict.fromkeys(ids))


def _table_present(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _seconds(later: str, earlier: str) -> int | None:
    late, early = parse_utc(later), parse_utc(earlier)
    if late is None or early is None:
        return None
    return int((late - early).total_seconds())


def _exclusions(
    attempt: Mapping[str, Any],
    *,
    elapsed_seconds: int | None,
    source_session_id: str | None,
    pfc_states: Mapping[str, str],
) -> list[str]:
    reasons = retention_exclusions(
        {
            "label_value": attempt["correctness"],
            "elapsed_seconds": elapsed_seconds,
            "outcome_hints_used": attempt["hints_used"],
            "outcome_primed": attempt["primed"],
            "outcome_manual_review": attempt["manual_review"],
            "outcome_manual_review_reason": attempt["manual_review_reason"],
            "outcome_pfc_assessment": pfc_states.get(attempt["id"]),
            "outcome_grade_held_for_review": attempt.get("grade_held_for_review", False),
            "source_session_id": source_session_id,
            "outcome_session_id": attempt["session_id"],
            "intervening_attempt_count": 0,
        }
    )
    if attempt["attempt_type"] not in INDEPENDENT_ATTEMPT_TYPES:
        reasons.append("not_independent_type")
    if attempt["evidence_origin"] != "human":
        reasons.append("non_human_outcome")
    return reasons


class _Ledger:
    """The attempt, reveal and exposure ledgers, indexed once for every decision."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        item_learning_objects: Mapping[str, str] | None = None,
        retrievability_by_attempt: Mapping[str, float] | None = None,
        held_attempt_ids: frozenset[str] = frozenset(),
    ) -> None:
        present = {row[1] for row in connection.execute("PRAGMA table_info(practice_attempts)")}
        optional = "".join(
            f", {column}" if column in present else f", NULL AS {column}" for column in _OPTIONAL_ATTEMPT_COLUMNS
        )
        attempts = [
            dict(row)
            for row in connection.execute(
                f"SELECT {_ATTEMPT_COLUMNS}{optional} FROM practice_attempts ORDER BY created_at, id"
            )
        ]
        for row in attempts:
            # mvp-0.17: a grade held for review is no scored outcome (still an
            # exposure: the learner saw the item and answered it).
            row["grade_held_for_review"] = row["id"] in held_attempt_ids
        self.by_id = {row["id"]: row for row in attempts}
        self.by_lo: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.position: dict[str, int] = {}
        self.by_candidate: dict[str, dict[str, Any]] = {}
        self.by_presentation: dict[str, dict[str, Any]] = {}
        self.by_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in attempts:
            lo_rows = self.by_lo[row["learning_object_id"]]
            self.position[row["id"]] = len(lo_rows)
            lo_rows.append(row)
            self.by_item[row["practice_item_id"]].append(row)
            candidate = row.get("scheduler_candidate_id")
            if candidate and candidate not in self.by_candidate:
                self.by_candidate[candidate] = row
            presentation = row.get("plan_presentation_id")
            if presentation and presentation not in self.by_presentation:
                self.by_presentation[presentation] = row
        self.observed_through = attempts[-1]["created_at"] if attempts else None
        reveals: dict[tuple[str, str], list[str]] = defaultdict(list)
        has_reveals = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='reveal_events'"
        ).fetchone()
        if has_reveals:
            for row in connection.execute(
                "SELECT practice_item_id, learning_object_id, created_at FROM reveal_events ORDER BY created_at, id"
            ):
                if row["practice_item_id"]:
                    reveals[("item", row["practice_item_id"])].append(row["created_at"])
                if row["learning_object_id"]:
                    reveals[("lo", row["learning_object_id"])].append(row["created_at"])
        self.reveals = reveals
        self._index_exposures(
            connection, attempts, has_reveals=bool(has_reveals), item_learning_objects=item_learning_objects or {}
        )
        self.retrievability = dict(retrievability_by_attempt or {})

    def _index_exposures(
        self,
        connection: sqlite3.Connection,
        attempts: list[dict[str, Any]],
        *,
        has_reveals: bool,
        item_learning_objects: Mapping[str, str],
    ) -> None:
        """Every exposure to an item, a facet or a learning object (D12)."""

        item_lo: dict[str, str] = dict(item_learning_objects)
        for row in attempts:
            item_lo.setdefault(row["practice_item_id"], row["learning_object_id"])
        items: dict[str, list[_Exposure]] = defaultdict(list)
        los: dict[str, list[_Exposure]] = defaultdict(list)
        facets: dict[str, list[_Exposure]] = defaultdict(list)
        lo_reveals: dict[str, list[tuple[str, float, str | None]]] = defaultdict(list)
        self.attempt_facets: dict[str, tuple[str, ...]] = {}
        self.attempt_keys = [(row["created_at"], row["id"]) for row in attempts]
        for row in attempts:
            exposure: _Exposure = (row["created_at"], row["id"], "attempt", row["id"])
            items[row["practice_item_id"]].append(exposure)
            los[row["learning_object_id"]].append(exposure)
            row_facets = _facet_ids(row.get("evidence_facets_json"))
            self.attempt_facets[row["id"]] = row_facets
            for facet in row_facets:
                facets[facet].append(exposure)
        if has_reveals:
            for row in connection.execute(
                "SELECT practice_item_id, learning_object_id, amount, attempt_id, created_at "
                "FROM reveal_events ORDER BY created_at, id"
            ):
                lo = row["learning_object_id"] or item_lo.get(row["practice_item_id"])
                exposure = (row["created_at"], "", "reveal", row["attempt_id"])
                items[row["practice_item_id"]].append(exposure)
                if lo:
                    los[lo].append(exposure)
                    lo_reveals[lo].append((row["created_at"], float(row["amount"] or 0.0), row["attempt_id"]))
        if _table_present(connection, "question_events"):
            for row in connection.execute(
                "SELECT practice_item_id, attempt_id, facets_json, created_at FROM question_events "
                "WHERE practice_item_id IS NOT NULL ORDER BY created_at, id"
            ):
                exposure = (row["created_at"], "", "tutor", row["attempt_id"])
                items[row["practice_item_id"]].append(exposure)
                lo = item_lo.get(row["practice_item_id"])
                if lo:
                    los[lo].append(exposure)
                for facet in _facet_ids(row["facets_json"]):
                    facets[facet].append(exposure)
        if _table_present(connection, "source_exposure_events"):
            for row in connection.execute(
                "SELECT entity_type, entity_id, created_at FROM source_exposure_events "
                "WHERE entity_type IN ('learning_object', 'practice_item') AND entity_id IS NOT NULL "
                "ORDER BY created_at, id"
            ):
                exposure = (row["created_at"], "", "reading", None)
                if row["entity_type"] == "learning_object":
                    los[row["entity_id"]].append(exposure)
                else:
                    items[row["entity_id"]].append(exposure)
                    lo = item_lo.get(row["entity_id"])
                    if lo:
                        los[lo].append(exposure)
        for table in (items, los, facets):
            for entries in table.values():
                entries.sort(key=lambda entry: (entry[0], entry[1]))
        for entries in lo_reveals.values():
            entries.sort(key=lambda entry: entry[0])
        self.item_exposures, self.lo_exposures, self.facet_exposures = items, los, facets
        self.lo_reveals = lo_reveals

    @staticmethod
    def _last_before(entries: list[_Exposure], attempt: Mapping[str, Any]) -> _Exposure | None:
        """The newest exposure before ``attempt``, never one the attempt caused."""

        index = bisect_left(entries, (attempt["created_at"], attempt["id"]))
        while index > 0:
            index -= 1
            entry = entries[index]
            if entry[3] != attempt["id"]:
                return entry
        return None

    def covariates(self, attempt: Mapping[str, Any]) -> dict[str, Any]:
        """The D12 coldness covariates of one attempt (its learning object's view)."""

        def since(entry: _Exposure | None) -> int | None:
            return None if entry is None else _seconds(attempt["created_at"], entry[0])

        item_last = self._last_before(self.item_exposures.get(attempt["practice_item_id"], []), attempt)
        facet_last: _Exposure | None = None
        for facet in self.attempt_facets.get(attempt["id"], ()):
            entry = self._last_before(self.facet_exposures.get(facet, []), attempt)
            if entry is not None and (facet_last is None or (entry[0], entry[1]) > (facet_last[0], facet_last[1])):
                facet_last = entry
        lo_last = self._last_before(self.lo_exposures.get(attempt["learning_object_id"], []), attempt)
        intervening = None
        if lo_last is not None:
            end = bisect_left(self.attempt_keys, (attempt["created_at"], attempt["id"]))
            start = bisect_right(self.attempt_keys, (lo_last[0], lo_last[1]))
            intervening = max(end - start, 0)
        rows = self.by_lo[attempt["learning_object_id"]]
        position = self.position.get(attempt["id"])
        previous = rows[position - 1]["created_at"] if position else None
        reveal_amount = 0.0
        for created_at, amount, linked in self.lo_reveals.get(attempt["learning_object_id"], []):
            if created_at > attempt["created_at"]:
                break
            if linked == attempt["id"] or (previous is not None and created_at <= previous):
                continue
            reveal_amount += amount
        return {
            "since_item_seconds": since(item_last),
            "since_facet_seconds": since(facet_last),
            "since_lo_seconds": since(lo_last),
            "intervening_attempts": intervening,
            "predicted_retrievability": self.retrievability.get(attempt["id"]),
            "reveal_amount": round(reveal_amount, 12),
            "last_item_exposure_kind": item_last[2] if item_last else None,
            "last_facet_exposure_kind": facet_last[2] if facet_last else None,
            "last_lo_exposure_kind": lo_last[2] if lo_last else None,
        }

    def last_reveal(self, item_id: str, learning_object_id: str, until: str) -> str | None:
        """The newest reveal on the item or its learning object at or before ``until``."""

        latest = None
        for key in (("item", item_id), ("lo", learning_object_id)):
            times = self.reveals.get(key) or []
            index = bisect_right(times, until)
            if index:
                candidate = times[index - 1]
                if latest is None or candidate > latest:
                    latest = candidate
        return latest


def _decision_block(decision: Mapping[str, Any]) -> str | None:
    """A ``plan_block`` decision's block (its receipt key names it)."""

    key = str(decision.get("receipt_key") or "")
    if decision.get("decision_kind") == "plan_block" and key.startswith("plan_block:"):
        return key.split(":", 1)[1] or None
    return None


def _action_attempt(
    decision: Mapping[str, Any],
    ledger: _Ledger,
    presentations: Mapping[str, list[dict[str, Any]]] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """The action attempt and how it was bound (module docstring, rules 1-3)."""

    block_id = _decision_block(decision)
    for presentation in (presentations or {}).get(block_id or "", ()):
        row = ledger.by_presentation.get(str(presentation["id"]))
        if row is not None and row["created_at"] >= decision["created_at"]:
            return row, BINDING_PRESENTATION
    candidate = decision.get("chosen_scheduler_candidate_id")
    if candidate:
        row = ledger.by_candidate.get(candidate)
        return (row, BINDING_CANDIDATE) if row is not None else (None, None)
    item_id = decision.get("chosen_practice_item_id")
    if not item_id:
        return None, None
    for row in ledger.by_item.get(item_id, []):
        if row["created_at"] < decision["created_at"]:
            continue
        if decision.get("session_id") and row["session_id"] != decision["session_id"]:
            continue
        if row.get("plan_presentation_id"):
            # An attempt with an exact receipt answered that presentation (a
            # step this decision's block did not serve: rule 1 already read
            # every presentation of its own). The fallback takes only an
            # attempt sent with no presentation id (R2a review F3).
            continue
        return row, BINDING_SESSION_RULE
    return None, None


def servable_items_by_learning_object(vault: Any) -> dict[str, set[str]]:
    """Each learning object's active, servable practice items (vault content).

    R_next needs a different item on the action's learning object; where there
    is none it is ``not_applicable``. Retired items and ephemeral dialogue-turn
    microprobes are never served.
    """

    by_lo: dict[str, set[str]] = defaultdict(set)
    for item in getattr(vault, "practice_items", {}).values():
        if getattr(item, "status", "active") != "active":
            continue
        if getattr(item, "practice_mode", None) == "diagnostic_microprobe":
            continue
        learning_object_id = getattr(item, "learning_object_id", None)
        if learning_object_id:
            by_lo[learning_object_id].add(item.id)
    return dict(by_lo)


def _r_next(
    action: Mapping[str, Any],
    ledger: _Ledger,
    pfc_states: Mapping[str, str],
    *,
    until_position: int | None = None,
) -> dict[str, Any]:
    """The first fresh, unassisted, independent attempt after the action, at or
    before ``until_position`` (the R_cold attempt) when one is given."""

    rows = ledger.by_lo[action["learning_object_id"]]
    end = len(rows) if until_position is None else until_position + 1
    skipped: dict[str, int] = defaultdict(int)
    for row in rows[ledger.position[action["id"]] + 1:end]:
        if row["practice_item_id"] == action["practice_item_id"]:
            skipped["not_fresh_same_item"] += 1
            continue
        reasons = [
            reason
            for reason in _exclusions(row, elapsed_seconds=None, source_session_id=None, pfc_states=pfc_states)
            if reason not in _DELAY_REASONS
        ]
        if reasons:
            for reason in reasons:
                skipped[reason] += 1
            continue
        return {
            "status": "observed",
            "value": float(row["correctness"]),
            "attempt_id": row["id"],
            "row": row,
            "elapsed_seconds": _seconds(row["created_at"], action["created_at"]),
            "skipped": skipped,
        }
    return {
        "status": "pending", "value": None, "attempt_id": None, "row": None, "elapsed_seconds": None,
        "skipped": skipped,
    }


def _r_cold(action: Mapping[str, Any], ledger: _Ledger, pfc_states: Mapping[str, str]) -> dict[str, Any]:
    learning_object_id = action["learning_object_id"]
    rows = ledger.by_lo[learning_object_id]
    start = ledger.position[action["id"]]
    skipped: dict[str, int] = defaultdict(int)
    considered: list[tuple[dict[str, Any], list[str]]] = []
    for index in range(start + 1, len(rows)):
        row = rows[index]
        previous = rows[index - 1]
        last_exposure = previous["created_at"]
        reveal = ledger.last_reveal(row["practice_item_id"], learning_object_id, row["created_at"])
        if reveal is not None and reveal > last_exposure:
            last_exposure = reveal
        gap = _seconds(row["created_at"], last_exposure)
        reasons = _exclusions(
            row,
            elapsed_seconds=gap,
            source_session_id=previous["session_id"],
            pfc_states=pfc_states,
        )
        considered.append((row, list(reasons)))
        if reasons:
            for reason in reasons:
                skipped[reason] += 1
            continue
        return {
            "status": "observed",
            "value": float(row["correctness"]),
            "attempt_id": row["id"],
            "row": row,
            "gap_seconds": gap,
            "position": index,
            "skipped": skipped,
            "considered": considered,
        }
    return {
        "status": "pending", "value": None, "attempt_id": None, "row": None, "gap_seconds": None, "position": None,
        "skipped": skipped, "considered": considered,
    }


def _not_applicable(decision: Mapping[str, Any], status: str, observed_through: str | None, *, pending: bool) -> dict[str, Any]:
    outcome = "pending" if pending else "not_applicable"
    return {
        "decision_id": decision["id"],
        "outcome_version": OUTCOME_VERSION,
        "target_practice_item_id": decision.get("chosen_practice_item_id"),
        "target_learning_object_id": decision.get("chosen_learning_object_id"),
        "action_status": status,
        "action_attempt_id": None,
        "r_next_status": outcome,
        "r_next_value": None,
        "r_next_attempt_id": None,
        "r_next_elapsed_seconds": None,
        "r_next_skipped": 0,
        "r_cold_status": outcome,
        "r_cold_value": None,
        "r_cold_attempt_id": None,
        "r_cold_gap_seconds": None,
        "r_cold_skipped": 0,
        "s_status": outcome,
        "s_value": None,
        "s_alpha": S_ALPHA,
        "observed_through": observed_through,
        **_covariate_columns("r_next", None),
        **_covariate_columns("r_cold", None),
        "coldness_candidates_json": "[]",
        "action_binding": None,
        "r_next_reference_status": None,
        "r_cold_reference_status": None,
        "detail_json": json.dumps({"basis": OUTCOME_VERSION, "r_cold_rule": R_COLD_RULE}, sort_keys=True),
    }


def _covariate_columns(prefix: str, covariates: Mapping[str, Any] | None) -> dict[str, Any]:
    return {f"{prefix}_{name}": (covariates or {}).get(name) for name in COVARIATE_NAMES}


def _coldness_candidates(
    action: Mapping[str, Any],
    considered: list[tuple[dict[str, Any], list[str]]],
    ledger: _Ledger,
    *,
    r_next_id: str | None,
    r_cold_id: str | None,
) -> tuple[list[dict[str, Any]], int]:
    """Every later attempt the R_cold rule considered, with its covariates."""

    entries: list[dict[str, Any]] = []
    for row, reasons in considered[:COLDNESS_CANDIDATE_CAP]:
        role = "r_cold" if row["id"] == r_cold_id else "r_next" if row["id"] == r_next_id else None
        entries.append(
            {
                "attempt_id": row["id"],
                "practice_item_id": row["practice_item_id"],
                "created_at": row["created_at"],
                # A held grade is no answer yet: its score is never the label.
                "correctness": (
                    None if row["correctness"] is None or row.get("grade_held_for_review")
                    else float(row["correctness"])
                ),
                "since_action_seconds": _seconds(row["created_at"], action["created_at"]),
                "role": role,
                "exclusions": sorted(reasons),
                **ledger.covariates(row),
            }
        )
    return entries, max(len(considered) - COLDNESS_CANDIDATE_CAP, 0)


def _ended_sessions(connection: sqlite3.Connection, session_ids: set[str]) -> set[str]:
    if not session_ids:
        return set()
    ended: set[str] = set()
    ids = sorted(session_ids)
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        ended.update(
            row[0]
            for row in connection.execute(
                f"SELECT id FROM sessions WHERE ended_at IS NOT NULL AND id IN ({','.join('?' for _ in chunk)})",
                chunk,
            )
        )
    return ended


def derive_router_outcomes(
    connection: sqlite3.Connection,
    *,
    pfc_states: Mapping[str, str] | None = None,
    servable_items_by_lo: Mapping[str, set[str]] | None = None,
    retrievability_by_attempt: Mapping[str, float] | None = None,
    held_attempt_ids: frozenset[str] | set[str] = frozenset(),
) -> list[dict[str, Any]]:
    """One outcome row per logged decision, from the ledgers alone (read-only).

    ``pfc_states`` maps attempt id to its PF-c assessment
    (``substrate.canonical_projection.pfc_assessments``); a nothing-assessed
    answer is never an outcome. ``held_attempt_ids``
    (``substrate.canonical_projection.held_for_review_attempts``) names the
    grades the proofs route check holds for review (mvp-0.17): never an
    outcome, and listed in ``coldness_candidates_json`` with no score. ``servable_items_by_lo``
    (:func:`servable_items_by_learning_object`) lets R_next be
    ``not_applicable`` where the learning object has no other item; without it
    an unobserved R_next stays ``pending``. ``retrievability_by_attempt`` maps
    attempt id to its FSRS-predicted retrievability (D12; the replayer's fold,
    ``scheduling.review_log.predicted_retrievability_by_attempt``); without it
    that covariate is NULL.
    """

    pfc_states = pfc_states or {}
    item_learning_objects = {
        item: learning_object
        for learning_object, items in (servable_items_by_lo or {}).items()
        for item in items
    }
    ledger = _Ledger(
        connection,
        item_learning_objects=item_learning_objects,
        retrievability_by_attempt=retrievability_by_attempt,
        held_attempt_ids=frozenset(held_attempt_ids),
    )
    decisions = [
        dict(row)
        for row in connection.execute(
            "SELECT id, receipt_key, decision_kind, session_id, created_at, chosen_ref, chosen_practice_item_id, "
            "chosen_learning_object_id, chosen_scheduler_candidate_id, parent_decision_id "
            "FROM router_decisions ORDER BY created_at, id"
        )
    ]
    presentations = presentations_for_blocks(
        connection, [block for row in decisions if (block := _decision_block(row)) is not None]
    )
    overridden = {row["parent_decision_id"] for row in decisions if row["decision_kind"] == "learner_pick"}
    # Decisions are ordered by (created_at, id): a later one in the same
    # session supersedes an offer whose head was never taken.
    last_in_session: dict[str, int] = {}
    for index, row in enumerate(decisions):
        if row["session_id"]:
            last_in_session[row["session_id"]] = index
    ended = _ended_sessions(connection, set(last_in_session))

    outcomes: list[dict[str, Any]] = []
    for index, decision in enumerate(decisions):
        if not decision.get("chosen_practice_item_id"):
            # Stop for today, a vetoed run, a block with no item: no action to follow.
            outcomes.append(_not_applicable(decision, "not_applicable", ledger.observed_through, pending=False))
            continue
        action, binding = _action_attempt(decision, ledger, presentations)
        if action is None:
            if decision["decision_kind"] == "today_offer" and decision["id"] in overridden:
                status, pending = "overridden", False
            elif decision["session_id"] and last_in_session.get(decision["session_id"], -1) > index:
                status, pending = "superseded", False
            elif decision["session_id"] in ended:
                status, pending = "not_taken", False
            else:
                status, pending = "open", True
            outcomes.append(_not_applicable(decision, status, ledger.observed_through, pending=pending))
            continue
        r_cold = _r_cold(action, ledger, pfc_states)
        # Only R_cold finalizes S: once it is observed, R_next counts only if
        # it came at or before the cold attempt.
        r_next = _r_next(action, ledger, pfc_states, until_position=r_cold["position"])
        r_next_not_applicable = None
        if r_next["status"] != "observed":
            others = (
                set(servable_items_by_lo.get(action["learning_object_id"], set())) - {action["practice_item_id"]}
                if servable_items_by_lo is not None
                else None
            )
            if others is not None and not others:
                r_next_not_applicable = "no_other_servable_item"
            elif r_cold["status"] == "observed":
                r_next_not_applicable = "closed_by_r_cold"
            if r_next_not_applicable is not None:
                r_next = {**r_next, "status": "not_applicable"}
        candidates, truncated = _coldness_candidates(
            action, r_cold["considered"], ledger,
            r_next_id=r_next["attempt_id"] if r_next["status"] == "observed" else None,
            r_cold_id=r_cold["attempt_id"],
        )
        if r_cold["status"] == "observed":
            s_status = "final"
            s_value = (
                S_ALPHA * r_cold["value"] + (1.0 - S_ALPHA) * r_next["value"]
                if r_next["status"] == "observed"
                else r_cold["value"]
            )
        elif r_next["status"] == "observed":
            # Provisional: R_next while R_cold is pending.
            s_status, s_value = "provisional", r_next["value"]
        else:
            s_status, s_value = "pending", None
        outcomes.append(
            {
                "decision_id": decision["id"],
                "outcome_version": OUTCOME_VERSION,
                "target_practice_item_id": action["practice_item_id"],
                "target_learning_object_id": action["learning_object_id"],
                "action_status": "taken",
                "action_attempt_id": action["id"],
                "r_next_status": r_next["status"],
                "r_next_value": r_next["value"],
                "r_next_attempt_id": r_next["attempt_id"],
                "r_next_elapsed_seconds": r_next["elapsed_seconds"],
                "r_next_skipped": sum(r_next["skipped"].values()),
                "r_cold_status": r_cold["status"],
                "r_cold_value": r_cold["value"],
                "r_cold_attempt_id": r_cold["attempt_id"],
                "r_cold_gap_seconds": r_cold["gap_seconds"],
                "r_cold_skipped": sum(r_cold["skipped"].values()),
                "s_status": s_status,
                "s_value": s_value,
                "s_alpha": S_ALPHA,
                "observed_through": ledger.observed_through,
                **_covariate_columns(
                    "r_next", ledger.covariates(r_next["row"]) if r_next["status"] == "observed" else None
                ),
                **_covariate_columns(
                    "r_cold", ledger.covariates(r_cold["row"]) if r_cold["status"] == "observed" else None
                ),
                "coldness_candidates_json": json.dumps(candidates, sort_keys=True),
                "action_binding": binding,
                "r_next_reference_status": (
                    r_next["row"].get("reference_status") if r_next["status"] == "observed" else None
                ),
                "r_cold_reference_status": (
                    r_cold["row"].get("reference_status") if r_cold["status"] == "observed" else None
                ),
                "detail_json": json.dumps(
                    {
                        "basis": OUTCOME_VERSION,
                        "r_cold_rule": R_COLD_RULE,
                        "coldness_candidates_truncated": truncated,
                        "cold_min_gap_seconds": RETENTION_MIN_DELAY_SECONDS,
                        "r_next_skip_reasons": dict(sorted(r_next["skipped"].items())),
                        "r_cold_skip_reasons": dict(sorted(r_cold["skipped"].items())),
                        "r_next_not_applicable": r_next_not_applicable,
                        "s_provisional_from": "r_next" if s_status == "provisional" else None,
                        "s_from": (
                            None
                            if s_value is None
                            else "r_cold_and_r_next"
                            if s_status == "final" and r_next["status"] == "observed"
                            else "r_cold" if s_status == "final" else "r_next"
                        ),
                    },
                    sort_keys=True,
                ),
            }
        )
    return outcomes


def rebuild_router_outcomes(
    connection: sqlite3.Connection,
    *,
    pfc_states: Mapping[str, str] | None = None,
    servable_items_by_lo: Mapping[str, set[str]] | None = None,
    retrievability_by_attempt: Mapping[str, float] | None = None,
    held_attempt_ids: frozenset[str] | set[str] = frozenset(),
) -> int:
    """Replace the derived cache; the caller owns the transaction."""

    return replace_router_outcomes(
        connection,
        derive_router_outcomes(
            connection,
            pfc_states=pfc_states,
            servable_items_by_lo=servable_items_by_lo,
            retrievability_by_attempt=retrievability_by_attempt,
            held_attempt_ids=held_attempt_ids,
        ),
    )


__all__ = [
    "COLDNESS_CANDIDATE_CAP",
    "COVARIATE_NAMES",
    "INDEPENDENT_ATTEMPT_TYPES",
    "R_COLD_RULE",
    "OUTCOME_VERSION",
    "S_ALPHA",
    "derive_router_outcomes",
    "rebuild_router_outcomes",
    "servable_items_by_learning_object",
]
