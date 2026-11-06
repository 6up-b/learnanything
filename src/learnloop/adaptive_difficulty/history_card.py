"""Router objective RO2's card, ``ad-forecast-state-v3`` (spec_router_objective_v1 §6.3).

The ``llm_history_v1`` forecaster reads the learner's history as a ladder of rungs, each adding to
the one below:

* **H0**: ``llm_v3``'s card **without its incumbent number** (the LO and its prerequisites, up to 25
  attempts, answer excerpts with ``history_answer_excerpts`` on): the ladder's baseline;
* **H1**: whole answers with the learner's confidence taps; ordered help from ``help_assists`` (kind,
  level, strategy, timing, text); the learner's questions on the LO with the disclosure state at the
  ask; reveals;
* **H2**: the Reader: reading opportunities on the LO, the learner's inquiries and their text (read
  directly, answered or not, each with its root and its learner-owned status at the serve:
  :func:`_inquiries`), self-check verdicts, session digests;
* **H3**: the whole history: other LOs by shared facets and recency, teach-backs, gaps named from the
  learner's text, exam sittings and imports (result only), goals and their dates.

What it reads, and what it never does:

* **Through AD's material view** (A8): every protected table through :meth:`MaterialView.rows`, so a
  row any of whose references resolves to withheld material (an exam or held-out item, a held-out
  reading's events, a help row citing held-out spans) is absent; the served item through its V1 view
  (stem, LO and facet names, capability, practice mode: never the reference solution, key or rubric).
  No stem of an unattempted item beyond the served item's own: an entry quotes an item's stem only for
  an attempt on it, and a Reader question's text only once the learner answered it. A tutor's answer
  text is not quoted (it can carry an item's worked solution); the learner's question and the
  disclosure state at the ask are.
* **Through ``learner_protection``**: an attempt whose question and answer a model context withholds
  (exam work, a diagnostic probe, an item the vault no longer holds:
  :func:`learnloop.learner_protection.attempt_protection`) keeps its result and shows no question and
  no answer, on every rung.
* **Only what was known at the serve**: an event enters only when its availability time is at or
  before ``served_at``: for ``practice_attempts`` RO1's predicate
  (``router_objective_switches.attempt_time_sql``) and, at every version, ``coalesce(received_at,
  created_at)`` (so a backdated import is out until it arrived, whatever the tag); per table
  ``coalesce(received_at, created_at)`` where it has ``received_at``, else ``created_at`` (a help row,
  which has neither, its ``coalesce(shown_at, requested_at)``; a reading receipt its source's write
  time). An inquiry's status is the one in force at the serve (a later logged change is read only for
  its ``previous_resolution``, the state it replaced). Every entry carries an evidence id and its days
  before the serve.
* **Bounded**: every read has a row limit (``keep``: :data:`ROW_LIMITS`) before any trimming, so the
  serve transaction's work is bounded and not only the prompt; then the card is held to
  ``adaptive_difficulty.history_card_token_budget`` (UTF-8 bytes, an upper bound on its tokens) by
  trimming oldest first within each rung, and it states what it left out (``left_out``) and which
  reads reached their row limit (``row_limits_reached``).

Pure reads; nothing is written here. Personal notes are not read at all (no rung lists them; the
spec allows them only if linked and allowlisted, and none is).
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from learnloop.clock import parse_utc
from learnloop.router_objective_switches import attempt_time_sql

from learnloop.adaptive_difficulty.operation import entry
from learnloop.adaptive_difficulty.outside import HISTORY_STEM_LIMIT, answer_excerpts_enabled, history_card, item_view

CARD_VERSION = "ad-forecast-state-v3"
RUNGS = ("H0", "H1", "H2", "H3")
#: Each rung's own sections (a rung's card holds its sections and every lower rung's).
SECTIONS: Mapping[str, tuple[str, ...]] = {
    "H0": ("recent_attempts",),
    "H1": ("whole_answers", "help", "questions", "reveals"),
    "H2": ("reading", "inquiries", "self_checks", "digests"),
    "H3": ("other_topics", "teach_backs", "gaps", "exams", "goals"),
}
#: ``keep``: the row limit of each bounded read (before any trimming): a work bound, never a judgement.
ROW_LIMITS: Mapping[str, int] = {
    "attempts": 400, "other_attempts": 200, "help": 200, "questions": 100, "reveals": 100, "reading": 200,
    "reader_sources": 100, "digests": 20, "gaps": 50, "goals": 20,
    # Codex review F6: H2's inquiries read directly, their exchanges (branch links) and roots, and the
    # logged status changes that place each root's status at the serve.
    "inquiries": 100, "exchanges": 200, "inquiry_roots": 100, "status_changes": 400,
    # Codex re-review F7: the newest inquiries of any LO, for those only the anchor's mapping at the serve
    # places on the scope (the scope's own are selected before the limit, ``inquiries``).
    "recent_inquiries": 100,
}
#: ``keep`` (Codex re-review F8): the most reads up the inquiry branch links in one serve, sharing the
#: ``exchanges`` row budget; past either, the unread ancestry is ``unknown``. A work bound, never a judgement.
ANCESTRY_ROUNDS = 16
#: ``keep``: the text bound of one entry (a whole answer, a help text, a question, a digest; bytes).
ANSWER_TEXT_LIMIT = 4_000
TEXT_LIMIT = 1_500
GAP_TEXT_LIMIT = 600
EXAM_TYPES = frozenset({"exam_attempt", "exam_evidence"})
READER_CONTEXTS = frozenset({"reader", "library"})


def _excerpt(text: Any, limit: int) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _json(value: Any, default: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def _columns(connection: Any, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}


def available_sql(connection: Any, table: str) -> str:
    """A table's availability time in SQL: ``coalesce(received_at, created_at)`` where it has
    ``received_at``, else ``created_at`` (spec §6.3)."""

    columns = _columns(connection, table)
    if "received_at" in columns:
        return "COALESCE(received_at, created_at)"
    return "created_at"


def _marks(values: Sequence[Any]) -> str:
    return ", ".join("?" for _ in values) or "NULL"


class _Days:
    def __init__(self, served_at: str) -> None:
        self.served = parse_utc(served_at)

    def __call__(self, stamp: Any) -> float | None:
        moment = parse_utc(str(stamp)) if stamp else None
        if moment is None or self.served is None or moment > self.served:
            return None
        return round((self.served - moment).total_seconds() / 86400.0, 2)


def _result(correctness: Any) -> str:
    if correctness is None:
        return "ungraded"
    value = float(correctness)
    if value >= 0.8:
        return "correct"
    if value < 0.4:
        return "incorrect"
    return "partial"


def _withheld(vault: Any, view: Any, attempts: Sequence[Mapping[str, Any]]) -> Any:
    """``learner_protection``'s set over what the view lets AD see: the withheld items (the view's) and
    the diagnostic probes (the vault's own modes); unknown items are withheld by ``known_items``."""

    from learnloop.learner_protection import PROBE_MODES, WITHHELD_EXAM, WITHHELD_PROBE, Withheld

    reasons: dict[str, str] = {}
    for attempt in attempts:
        item_id = str(attempt.get("practice_item_id") or "")
        if not item_id:
            continue
        if view.withheld(item_id):
            reasons[item_id] = WITHHELD_EXAM
            continue
        item = view.item(item_id)
        if item is not None and getattr(item, "practice_mode", None) in PROBE_MODES:
            reasons[item_id] = WITHHELD_PROBE
    known = frozenset(str(item_id) for item_id in (getattr(vault, "practice_items", None) or {}))
    return Withheld(reasons=reasons, known_items=known)


def _protection(withheld: Any, attempt: Mapping[str, Any]) -> str | None:
    from learnloop.learner_protection import attempt_protection

    return attempt_protection(withheld, {"item": attempt.get("practice_item_id"), "type": attempt.get("attempt_type"),
                                         "probe": attempt.get("probe_presentation_id")})


class _Reads:
    """Every bounded read the card makes, once per serve (shared by the rungs)."""

    def __init__(self, vault: Any, connection: Any, item: Any, *, served_at: str, view: Any) -> None:
        self.vault, self.connection, self.item, self.view = vault, connection, item, view
        self.served_at = served_at
        self.days = _Days(served_at)
        self.limits_reached: list[str] = []
        lo = vault.learning_objects.get(item.learning_object_id)
        scope = [str(item.learning_object_id), *[str(p) for p in (getattr(lo, "prerequisites", None) or [])]]
        self.scope = list(dict.fromkeys(scope))
        self.scope_items = sorted({str(found.id) for lo_id in self.scope
                                   for found in view.items(learning_object_id=lo_id)} | {str(item.id)})

    def _bounded(self, name: str, table: str, where: str, args: Sequence[Any], order: str, *,
                 limit: int | None = None) -> list[dict[str, Any]]:
        limit = ROW_LIMITS[name] if limit is None else limit
        read = self.view.rows(self.connection, table, where, tuple(args), order=order, limit=limit)
        if len(read) >= limit:
            self.limits_reached.append(name)
        return read

    def attempts(self, *, scope: bool) -> list[dict[str, Any]]:
        config = getattr(self.vault, "config", None)
        # RO1's predicate, and the availability time at every version (a backdated import is out until
        # it arrived): both bound the read, and the work happened before the serve.
        known = attempt_time_sql(config, self.connection)
        available = available_sql(self.connection, "practice_attempts")
        membership = "IN" if scope else "NOT IN"
        return self._bounded(
            "attempts" if scope else "other_attempts", "practice_attempts",
            f"learning_object_id {membership} ({_marks(self.scope)}) AND created_at <= ? AND {known} <= ? "
            f"AND {available} <= ? AND attempt_type != 'self_report'",
            (*self.scope, self.served_at, self.served_at, self.served_at), "created_at DESC, id DESC")

    def help(self, attempt_ids: Sequence[str]) -> list[dict[str, Any]]:
        ids = list(attempt_ids)
        return self._bounded(
            "help", "help_assists",
            f"(attempt_id IN ({_marks(ids)}) OR practice_item_id IN ({_marks(self.scope_items)})) "
            "AND COALESCE(shown_at, requested_at) <= ?",
            (*ids, *self.scope_items, self.served_at), "COALESCE(shown_at, requested_at) DESC, id DESC")

    def questions(self) -> list[dict[str, Any]]:
        available = available_sql(self.connection, "question_events")
        return self._bounded(
            "questions", "question_events",
            f"practice_item_id IN ({_marks(self.scope_items)}) AND {available} <= ?",
            (*self.scope_items, self.served_at), "created_at DESC, id DESC")

    def reveals(self) -> list[dict[str, Any]]:
        return self._bounded(
            "reveals", "reveal_events",
            f"(learning_object_id IN ({_marks(self.scope)}) OR practice_item_id IN ({_marks(self.scope_items)})) "
            "AND created_at <= ?",
            (*self.scope, *self.scope_items, self.served_at), "created_at DESC, id DESC")

    def reading(self) -> list[dict[str, Any]]:
        return self._bounded(
            "reading", "ad_reading_opportunities",
            f"learning_object_id IN ({_marks(self.scope)}) AND source_written_at <= ?",
            (*self.scope, self.served_at), "source_written_at DESC, id DESC")

    def reader_sources(self, table: str, ids: Sequence[str]) -> list[dict[str, Any]]:
        if not ids:
            return []
        available = available_sql(self.connection, table)
        return self._bounded("reader_sources", table, f"id IN ({_marks(ids)}) AND {available} <= ?",
                             (*ids, self.served_at), "created_at DESC, id DESC")

    def digests(self, extractions: Sequence[str]) -> list[dict[str, Any]]:
        if not extractions:
            return []
        available = available_sql(self.connection, "reader_session_digests")
        return self._bounded("digests", "reader_session_digests",
                             f"extraction_id IN ({_marks(extractions)}) AND {available} <= ? "
                             "AND dismissed_at IS NULL",
                             (*extractions, self.served_at), "created_at DESC, id DESC")

    def inquiries(self, *, scoped: bool) -> list[dict[str, Any]]:
        """The learner's Reader and library questions known at the serve, newest first (Codex review F6:
        read directly, answered or not; the caller keeps those on the scope's LOs by the full rule).

        ``scoped`` (Codex re-review F7): the questions that name the scope by what they recorded (a
        candidate LO recorded at the ask, an item of the scope, a note on a scope LO), selected before
        the row limit so questions on other LOs never displace them. Otherwise the newest questions on
        any LO, for the ones only the anchor's mapping at the serve places on the scope."""

        available = available_sql(self.connection, "question_events")
        contexts = sorted(READER_CONTEXTS)
        if not scoped:
            return self._bounded("recent_inquiries", "question_events",
                                 f"context IN ({_marks(contexts)}) AND {available} <= ?",
                                 (*contexts, self.served_at), "created_at DESC, id DESC")
        scope = set(self.scope)
        notes = sorted(str(note_id) for note_id, note in (getattr(self.vault, "notes", None) or {}).items()
                       if {str(lo) for lo in getattr(note, "related_los", None) or []} & scope)
        # An unparseable context names nothing (json_each of NULL is empty), never an error.
        candidates = ("EXISTS (SELECT 1 FROM json_each(CASE WHEN json_valid(source_context_json) THEN "
                      "source_context_json END, '$.candidate_learning_object_ids') WHERE value IN "
                      f"({_marks(self.scope)}))")
        return self._bounded(
            "inquiries", "question_events",
            f"context IN ({_marks(contexts)}) AND {available} <= ? AND ({candidates} OR practice_item_id IN "
            f"({_marks(self.scope_items)}) OR note_id IN ({_marks(notes)}))",
            (*contexts, self.served_at, *self.scope, *self.scope_items, *notes), "created_at DESC, id DESC")

    def exchanges(self, *, question_ids: Sequence[str] = (), event_ids: Sequence[str] = (),
                  limit: int | None = None) -> list[dict[str, Any]]:
        """Completed Reader exchanges (``reader_answer_submitted``) of these questions or with these ids,
        known at the serve: their payload carries the branch link (``parent_exchange_id``). ``limit``:
        what is left of the inquiry ancestry's shared row budget (Codex re-review F8)."""

        if not question_ids and not event_ids:
            return []
        available = available_sql(self.connection, "interaction_events")
        return self._bounded(
            "exchanges", "interaction_events",
            f"kind = 'reader_answer_submitted' AND (json_extract(payload_json, '$.question_event_id') IN "
            f"({_marks(question_ids)}) OR id IN ({_marks(event_ids)})) AND {available} <= ?",
            (*question_ids, *event_ids, self.served_at), "created_at DESC, id DESC", limit=limit)

    def status_changes(self, question_ids: Sequence[str]) -> list[dict[str, Any]]:
        """Every logged inquiry status change of these root questions (``inquiry_status_set``), whenever
        it happened: one after the serve says, by its ``previous_resolution``, what held at the serve."""

        if not question_ids:
            return []
        return self._bounded(
            "status_changes", "interaction_events",
            "kind = 'reader_action_invoked' AND subject_type = 'reader_inquiry' AND "
            "json_extract(payload_json, '$.event') = 'inquiry_status_set' AND "
            f"json_extract(payload_json, '$.question_event_id') IN ({_marks(question_ids)})",
            tuple(question_ids), "created_at, id")

    def questions_by_id(self, ids: Sequence[str]) -> list[dict[str, Any]]:
        if not ids:
            return []
        return self._bounded("inquiry_roots", "question_events", f"id IN ({_marks(ids)})", tuple(ids), "id")

    def gaps(self, los: Sequence[str], attempt_ids: Sequence[str]) -> list[dict[str, Any]]:
        available = available_sql(self.connection, "learner_text_gaps")
        return self._bounded(
            "gaps", "learner_text_gaps",
            f"(anchor_learning_object_id IN ({_marks(los)}) OR attempt_id IN ({_marks(attempt_ids)})) "
            f"AND {available} <= ?", (*los, *attempt_ids, self.served_at), "created_at DESC, id DESC")


def _topic(vault: Any, lo_id: Any) -> str:
    lo = vault.learning_objects.get(str(lo_id))
    return lo.title if lo is not None else str(lo_id)


def _oldest_first(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(entries, key=lambda entry: (-(entry.get("days_before") or 0.0), str(entry.get("evidence_id"))))


def _inquiry_los(reads: _Reads, mapping: Any, row: Mapping[str, Any]) -> set[str]:
    """The LOs a Reader question is on, by the reading sweep's rule (``reading_sources``' tutor events:
    its anchor span's LOs, a note's, its item's) and the candidate LOs it recorded at the ask."""

    from learnloop.ingest.locators import parse_block_span

    los: set[str] = set()
    context = _json(row.get("source_context_json"), {})
    if isinstance(context, Mapping):
        los |= {str(lo) for lo in context.get("candidate_learning_object_ids") or [] if lo}
    note_id = row.get("note_id")
    parsed = parse_block_span(str(note_id)) if note_id else None
    if parsed is not None:
        los |= {str(lo) for lo in mapping.los_for_span(parsed[0], parsed[1])}
    elif note_id:
        los |= {str(lo) for lo in mapping.los_for_note(str(note_id))}
    if row.get("practice_item_id"):
        lo = reads.view.lo_for_item(row.get("practice_item_id"))
        if lo:
            los.add(str(lo))
    return los


def _inquiries(vault: Any, reads: _Reads) -> tuple[list[dict[str, Any]], set[str]]:
    """H2's inquiries (Codex review F6): the learner's Reader and library questions on the scope's LOs,
    known at the serve, answered by the tutor or not, each with its inquiry's status at the serve.

    An inquiry is a root question and its branches (the branch link rides each completed exchange's
    payload, ``parent_exchange_id``); its status is the root's learner-owned ``resolution`` (``open``,
    ``resolved``, ``dismissed``; reopen included), never whether the tutor answered. The status at the
    serve is the last logged change at or before it, else the first later change's
    ``previous_resolution``, else the stored value when it is still the default ``open``; a status a
    path changed without logging is ``unknown`` (its time is not recorded). Every read is bounded and
    through the view (a withheld question, exchange or change is absent): the scope's questions are
    selected before their row limit (Codex re-review F7), and the walk up the branch links shares one
    row budget and :data:`ANCESTRY_ROUNDS` reads, past which an inquiry's root and status are
    ``unknown`` and ``inquiry_ancestry`` is listed among the reads that reached their limit (F8); a
    parent a capped read left unread is unresolved the same way (Codex final verify F9). An older
    question placed on the scope only by its anchor's mapping at the serve can fall behind the
    ``recent_inquiries`` limit; the card then lists that read among the ones that reached their limit
    (F7's remainder, accepted as Low at landing: model input, nothing a learner sees).
    Returns the entries and the readings they were asked on (for the digests)."""

    from learnloop.adaptive_difficulty.reading import VaultReadingMap

    days = reads.days
    mapping = VaultReadingMap(vault, reads.view.repository, reads.view)
    scope = set(reads.scope)
    # Codex re-review F7: the scope's own questions, selected before the limit, and the newest of any LO
    # that the anchor's mapping at the serve places on the scope; newest first, one row limit in all.
    union = {str(row["id"]): row for row in reads.inquiries(scoped=False) + reads.inquiries(scoped=True)}
    kept = sorted((row for row in union.values()
                   if days(row.get("created_at")) is not None and _inquiry_los(reads, mapping, row) & scope),
                  key=lambda row: (str(row.get("created_at") or ""), str(row["id"])), reverse=True)
    if len(kept) > ROW_LIMITS["inquiries"]:
        kept = kept[: ROW_LIMITS["inquiries"]]
        reads.limits_reached.append("inquiries")
    question_of: dict[str, str] = {}
    parent_of: dict[str, str] = {}

    def link(exchanges: list[dict[str, Any]]) -> int:
        for exchange in exchanges:
            payload = _json(exchange.get("payload_json"), {})
            if not isinstance(payload, Mapping) or not payload.get("question_event_id"):
                continue
            question_of[str(exchange["id"])] = str(payload["question_event_id"])
            if payload.get("parent_exchange_id"):
                parent_of.setdefault(str(payload["question_event_id"]), str(payload["parent_exchange_id"]))
        return len(exchanges)

    # Codex re-review F8: one row budget (the exchanges' limit) and at most ANCESTRY_ROUNDS reads up the
    # branch links, shared by every inquiry; past it the unread parents are unresolved ancestry.
    budget = ROW_LIMITS["exchanges"] - link(reads.exchanges(question_ids=[str(row["id"]) for row in kept]))
    # A first read that used the whole budget may have left a question's own exchange unread.
    unread = {str(row["id"]) for row in kept} - set(question_of.values()) if budget <= 0 else set()
    asked: set[str] = set()
    # Codex final verify F9: the parents a capped read left unread (its LIMIT cut the batch), beside the
    # ones never asked; a walk that reaches either has an unknown root, never a false intermediate one.
    # A parent an uncapped read did not return is absent (withheld or never written), as before.
    unresolved: set[str] = set()
    pending = {parent for parent in parent_of.values() if parent not in question_of}
    rounds = 0
    while pending and budget > 0 and rounds < ANCESTRY_ROUNDS:  # each parent asked once (a cycle ends it)
        rounds += 1
        asked |= pending
        returned = link(reads.exchanges(event_ids=sorted(pending), limit=budget))
        if returned >= budget:
            unresolved |= {parent for parent in pending if parent not in question_of}
        budget -= returned
        pending = {parent for parent in parent_of.values() if parent not in question_of and parent not in asked}
    unresolved |= pending
    if unresolved or unread:
        reads.limits_reached.append("inquiry_ancestry")

    def root(question_id: str) -> str | None:
        """The inquiry's root question, ``None`` when the walk stops at a link the budget left unread."""

        if question_id in unread:
            return None
        seen = {question_id}
        while parent_of.get(question_id) in question_of:
            nxt = question_of[parent_of[question_id]]
            if nxt in seen:
                break
            seen.add(nxt)
            question_id = nxt
        return None if parent_of.get(question_id) in unresolved else question_id

    found = {str(row["id"]): root(str(row["id"])) for row in kept}
    roots = {question_id: root_id for question_id, root_id in found.items() if root_id is not None}
    current = {str(row["id"]): str(row.get("resolution") or "open") for row in kept}
    missing = sorted(set(roots.values()) - set(current))
    current.update({str(row["id"]): str(row.get("resolution") or "open") for row in reads.questions_by_id(missing)})
    changes: dict[str, list[Mapping[str, Any]]] = {}
    for change in reads.status_changes(sorted(set(roots.values()))):
        payload = _json(change.get("payload_json"), {})
        if isinstance(payload, Mapping) and payload.get("question_event_id"):
            changes.setdefault(str(payload["question_event_id"]), []).append(
                {**payload, "at": change.get("created_at")})

    def status(root_id: str) -> str:
        logged = changes.get(root_id, [])
        before = [change for change in logged if days(change.get("at")) is not None]
        if before:
            return str(before[-1].get("resolution") or "unknown")
        if logged:
            return str(logged[0].get("previous_resolution") or "unknown")
        stored = current.get(root_id)
        return "open" if stored == "open" else "unknown"

    entries, extractions = [], set()
    for row in kept:
        question_id = str(row["id"])
        root_id = roots.get(question_id)
        # Past the ancestry budget the root and its status are unknown (Codex re-review F8).
        state = status(root_id) if root_id is not None else "unknown"
        answered_at = row.get("answered_at")
        answered = (days(answered_at) is not None) if answered_at else row.get("answer_status") == "answered"
        entries.append({"evidence_id": f"question:{question_id}", "days_before": days(row.get("created_at")),
                        "context": row.get("context"), "question": _excerpt(row.get("question_md"), TEXT_LIMIT),
                        "tutor_answered": bool(answered),
                        "root": "unknown" if root_id is None else None if root_id == question_id
                        else f"question:{root_id}",
                        "status": state, "open": state == "open"})
        context = _json(row.get("source_context_json"), {})
        if isinstance(context, Mapping) and context.get("extraction_id"):
            extractions.add(str(context["extraction_id"]))
    return entries, extractions


def build_sections(vault: Any, connection: Any, item: Any, *, served_at: str, view: Any) -> dict[str, Any]:
    """Every rung's sections, from the bounded reads (oldest entry first in each list), with the
    clocks' input (days since the latest exposure to the LO) and the reads that hit their limit."""

    reads = _Reads(vault, connection, item, served_at=served_at, view=view)
    days = reads.days
    scope_attempts = [row for row in reads.attempts(scope=True) if days(row.get("created_at")) is not None]
    other_attempts = [row for row in reads.attempts(scope=False) if days(row.get("created_at")) is not None]
    withheld = _withheld(vault, view, scope_attempts + other_attempts)
    protected = {str(row["id"]): _protection(withheld, row) for row in scope_attempts + other_attempts}

    # H0: llm_v3's card without its incumbent number, from the bounded read, with evidence ids.
    card = history_card(vault, connection, item, served_at=served_at, view=view, incumbent=None,
                        answers=answer_excerpts_enabled(vault), attempts_read=scope_attempts, evidence_ids=True)
    recent = []
    for entry in card["recent_attempts"]:
        attempt_id = str(entry.get("evidence_id", "")).partition(":")[2]
        reason = protected.get(attempt_id)
        if reason:
            entry = {**{k: v for k, v in entry.items() if k != "answer_excerpt"}, "item": f"(withheld: {reason})"}
        recent.append(entry)
    sections: dict[str, Any] = {"recent_attempts": recent}

    # H1: whole answers with confidence taps, ordered help, questions with disclosure, reveals.
    answers = []
    for row in scope_attempts:
        reason = protected.get(str(row["id"]))
        entry = {"evidence_id": f"attempt:{row['id']}", "days_before": days(row.get("created_at")),
                 "topic": _topic(vault, row.get("learning_object_id")), "same_item": str(row.get("practice_item_id")) ==
                 str(item.id), "attempt_type": row.get("attempt_type"), "result": _result(row.get("correctness")),
                 "hints_used": int(row.get("hints_used") or 0), "answer_was_shown": bool(row.get("primed")),
                 "confidence_tap": row.get("answer_confidence"),
                 "declared_dont_know": bool(row.get("declared_dont_know")),
                 "declared_stuck": bool(row.get("declared_stuck"))}
        if reason:
            entry["withheld"] = reason
        elif str(row.get("learner_answer_md") or "").strip():
            entry["answer"] = _excerpt(row.get("learner_answer_md"), ANSWER_TEXT_LIMIT)
        answers.append(entry)
    attempt_ids = [str(row["id"]) for row in scope_attempts]
    unprotected = {attempt_id for attempt_id in attempt_ids if not protected.get(attempt_id)}
    help_entries = []
    for row in reads.help(attempt_ids):
        stamp = row.get("shown_at") or row.get("requested_at")
        if days(stamp) is None:
            continue
        attempt = str(row.get("attempt_id") or "")
        entry = {"evidence_id": f"help:{row['id']}", "days_before": days(stamp),
                 "attempt": f"attempt:{attempt}" if attempt else None, "surface": row.get("surface"),
                 "kind": row.get("assist_kind") or row.get("hint_kind"), "hint_kind": row.get("hint_kind"),
                 "level": row.get("level"), "strategy": row.get("strategy"), "shown": bool(row.get("shown")),
                 "seconds_to_submit": row.get("submit_latency_seconds")}
        text = row.get("body_md") or row.get("feedback_text")
        if text and (not attempt or attempt in unprotected):
            entry["text"] = _excerpt(text, TEXT_LIMIT)
        help_entries.append(entry)
    questions = []
    for row in reads.questions():
        if str(row.get("context") or "") in READER_CONTEXTS:
            continue
        attempt = str(row.get("attempt_id") or "")
        entry = {"evidence_id": f"question:{row['id']}", "days_before": days(row.get("created_at")),
                 "context": row.get("context"), "attempt": f"attempt:{attempt}" if attempt else None,
                 "question_type": row.get("question_type"), "hint_equivalent": bool(row.get("hint_equivalent")),
                 "hints_used_before": row.get("hints_used_before"), "attempt_progress": row.get("attempt_progress"),
                 "disclosure_at_ask": _json(row.get("reveal_state_json"), None),
                 "answered": row.get("answered_at") is not None or row.get("answer_status") == "answered"}
        if not attempt or attempt in unprotected:
            entry["question"] = _excerpt(row.get("question_md"), TEXT_LIMIT)
        if entry["days_before"] is not None:
            questions.append(entry)
    reveals = [{"evidence_id": f"reveal:{row['id']}", "days_before": days(row.get("created_at")),
                "topic": _topic(vault, row.get("learning_object_id") or item.learning_object_id),
                "source_kind": row.get("source_kind"), "amount": row.get("amount"), "basis": row.get("basis"),
                "attempt": f"attempt:{row['attempt_id']}" if row.get("attempt_id") else None}
               for row in reads.reveals() if days(row.get("created_at")) is not None]
    sections.update(whole_answers=_oldest_first(answers), help=_oldest_first(help_entries),
                    questions=_oldest_first(questions), reveals=_oldest_first(reveals))

    # H2: the Reader, through AD's reading receipts on the LO (their sources resolved again now). Teacher TE3a: a
    # lesson's receipt rows only while lesson opportunities are live (off: the card of before, exactly).
    from learnloop.adaptive_difficulty.successor import lesson_opportunities_on

    lessons = lesson_opportunities_on(getattr(vault, "config", None))
    opportunities = [row for row in reads.reading() if days(row.get("source_written_at")) is not None
                     and (lessons or row.get("kind") != "lesson")]
    reading = [{"evidence_id": f"reading:{row['id']}", "days_before": days(row.get("source_written_at")),
                "topic": _topic(vault, row.get("learning_object_id")), "kind": row.get("kind"),
                "subkind": row.get("subkind")} for row in opportunities]
    by_table: dict[str, list[str]] = {}
    for row in opportunities:
        by_table.setdefault(str(row.get("source_table")), []).append(str(row.get("source_id")))
    inquiries, extractions = _inquiries(vault, reads)
    self_checks: list[dict[str, Any]] = []
    for row in reads.reader_sources("reader_authored_questions", by_table.get("reader_authored_questions", [])):
        if days(row.get("created_at")) is None:
            continue
        extractions.add(str(row.get("extraction_id")))
        answered = row.get("answered_at") is not None and days(row.get("answered_at")) is not None
        entry = {"evidence_id": f"reader_question:{row['id']}", "days_before": days(row.get("created_at")),
                 "style": row.get("question_style"), "status": row.get("status"), "answered": answered}
        if answered:
            # Only an answered question's text (never an unattempted stem), and never its key.
            entry.update(question=_excerpt(row.get("question_md"), TEXT_LIMIT),
                         learner_response=_excerpt(row.get("response_md"), TEXT_LIMIT),
                         self_check=row.get("self_check"), answer_basis=row.get("answer_basis"))
        self_checks.append(entry)
    for row in reads.reader_sources("source_exposure_events", by_table.get("source_exposure_events", [])):
        if row.get("extraction_id"):
            extractions.add(str(row["extraction_id"]))
    digests = []
    for row in reads.digests(sorted(extractions)):
        stamp = row.get("ended_at") or row.get("created_at")
        if days(row.get("created_at")) is None:
            continue
        digests.append({"evidence_id": f"digest:{row['id']}", "days_before": days(stamp) or days(row.get("created_at")),
                        "status": row.get("status"), "narrative": _excerpt(row.get("narrative_md"), TEXT_LIMIT)})
    sections.update(reading=_oldest_first(reading), inquiries=_oldest_first(inquiries),
                    self_checks=_oldest_first(self_checks), digests=_oldest_first(digests))

    # H3: the whole history.
    facet_to_los, lo_to_facets = view.facet_maps()
    related = {str(lo) for scope_lo in reads.scope for facet in lo_to_facets.get(scope_lo, [])
               for lo in facet_to_los.get(facet, []) if str(lo) not in reads.scope}
    others, teach_backs, exams = [], [], []
    for row in other_attempts + scope_attempts:
        reason = protected.get(str(row["id"]))
        base = {"evidence_id": f"attempt:{row['id']}", "days_before": days(row.get("created_at")),
                "topic": _topic(vault, row.get("learning_object_id")), "result": _result(row.get("correctness")),
                "attempt_type": row.get("attempt_type")}
        kind = str(row.get("attempt_type") or "")
        if kind in EXAM_TYPES:
            # Exam sittings and imports: the result only (learner_protection: no question, no answer).
            exams.append(base)
            continue
        if kind == "teach_back":
            entry = dict(base)
            if not reason and str(row.get("learner_answer_md") or "").strip():
                entry["explanation"] = _excerpt(row.get("learner_answer_md"), TEXT_LIMIT)
            teach_backs.append(entry)
            continue
        if str(row.get("learning_object_id")) in reads.scope:
            continue
        entry = {**base, "related_by": "shared_facets" if str(row.get("learning_object_id")) in related else "recency",
                 "hints_used": int(row.get("hints_used") or 0)}
        past = view.item(row.get("practice_item_id"))
        entry["item"] = (f"(withheld: {reason})" if reason else
                         _excerpt(past.prompt, HISTORY_STEM_LIMIT) if past is not None else
                         "(an item no longer in the vault)")
        others.append(entry)
    gaps = []
    for row in reads.gaps(sorted(set(reads.scope) | related), attempt_ids):
        if days(row.get("created_at")) is None:
            continue
        attempt = str(row.get("attempt_id") or "")
        entry = {"evidence_id": f"gap:{row['id']}", "days_before": days(row.get("created_at")),
                 "kind": row.get("kind"), "action": row.get("action"), "target_kind": row.get("target_kind"),
                 "topic": _topic(vault, row.get("anchor_learning_object_id")) if row.get("anchor_learning_object_id")
                 else None}
        if not attempt or not protected.get(attempt):
            entry["learner_text"] = _excerpt(row.get("learner_text"), GAP_TEXT_LIMIT)
        gaps.append(entry)
    goals = []
    for goal in list(getattr(vault, "goals", None) or [])[: ROW_LIMITS["goals"]]:
        created = days(getattr(goal, "created_at", None))
        if created is None:
            continue
        due = parse_utc(str(goal.due_at)) if getattr(goal, "due_at", None) else None
        served = parse_utc(served_at)
        goals.append({"evidence_id": f"goal:{goal.id}", "days_before": created, "title": _excerpt(goal.title, 200),
                      "status": goal.status,
                      "due_in_days": (round((due - served).total_seconds() / 86400.0, 2)
                                      if due is not None and served is not None else None)})
    sections.update(other_topics=_oldest_first(others), teach_backs=_oldest_first(teach_backs),
                    gaps=_oldest_first(gaps), exams=_oldest_first(exams), goals=_oldest_first(goals))

    exposures = [entry.get("days_before") for name in ("whole_answers", "help", "questions", "reveals", "reading")
                 for entry in sections[name] if entry.get("days_before") is not None]
    return {"sections": sections, "scope": reads.scope, "row_limits_reached": sorted(set(reads.limits_reached)),
            "latest_exposure_days_before": min(exposures) if exposures else None}


def _size(state: Mapping[str, Any]) -> int:
    return len(json.dumps(state, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8"))


def rung_card(vault: Any, item: Any, built: Mapping[str, Any], rung: str, *, budget: int) -> tuple[dict[str, Any], dict]:
    """The state sent for ``rung``: the served item, the rung's sections and every lower rung's, held to
    ``budget`` bytes by trimming oldest first within each rung (one entry per rung per round), with what
    it left out. Returns ``(state, left_out)``."""

    if rung not in RUNGS:
        raise ValueError(f"unknown rung {rung!r}")
    included = RUNGS[: RUNGS.index(rung) + 1]
    history = {name: list(built["sections"][name]) for level in included for name in SECTIONS[level]}
    state: dict[str, Any] = {
        "card": CARD_VERSION, "rung": rung, "item": item_view(vault, item),
        "topics": [_topic(vault, lo_id) for lo_id in built["scope"]],
        "history": history,
        "row_limits_reached": list(built["row_limits_reached"]),
        "not_recorded": ("Hedges (the grader's reading of an answer's tone) are not on this card; "
                         "a tutor's answers are summarized by the learner's questions only."),
    }
    left_out: dict[str, dict[str, Any]] = {}
    # Each removal subtracts its entry's own bytes (and its separator), so the card is serialized once
    # per pass, not once per removal; the pass ends on the exact size, the left-out record included.
    estimate = _size({**state, "left_out": left_out})
    while estimate > int(budget):
        trimmed = False
        for level in reversed(included):
            lists = [(name, history[name]) for name in SECTIONS[level] if history[name]]
            if not lists:
                continue
            name, entries = max(lists, key=lambda pair: (pair[1][0].get("days_before") or 0.0, pair[0]))
            dropped = entries.pop(0)
            estimate -= _size(dropped) + 2
            record = left_out.setdefault(level, {}).setdefault(
                name, {"entries": 0, "oldest_days_before": None, "newest_days_before": None})
            record["entries"] += 1
            when = dropped.get("days_before")
            if when is not None:
                record["oldest_days_before"] = max(when, record["oldest_days_before"] or when)
                record["newest_days_before"] = min(when, record["newest_days_before"]
                                                   if record["newest_days_before"] is not None else when)
            trimmed = True
        if not trimmed:
            break
        if estimate <= int(budget):
            estimate = _size({**state, "left_out": left_out})
    state["left_out"] = left_out
    return state, left_out


def decision_sections(vault: Any, repository: Any, connection: Any, candidates: Sequence[tuple[Sequence[str], Sequence[str]]],
                      *, served_at: str, view: Any = None) -> list[dict[str, Any]]:
    """Router objective RO4 (spec §8.3): every rung's sections for one representative item per candidate topic
    (the candidate's own first item on it, else the LO's first item the view shows), for the LLM policy's
    decision-level H3 card. ``candidates``: ``(item ids, LO ids)`` per candidate. Read-only, through AD's material
    view in an AD operation (:func:`decision_sections_entry`)."""

    from learnloop.adaptive_difficulty.material_view import material_view

    view = material_view(vault, repository, view)
    picked: dict[str, Any] = {}
    for item_ids, lo_ids in candidates:
        for item_id in item_ids:
            item = view.item(item_id)
            lo = getattr(item, "learning_object_id", None) if item is not None else None
            if lo and lo not in picked:
                picked[str(lo)] = item
        for lo in lo_ids:
            if lo not in picked:
                visible = list(view.items(learning_object_id=lo))
                if visible:
                    picked[str(lo)] = visible[0]
    out = []
    for lo, item in sorted(picked.items()):
        built = build_sections(vault, connection, item, served_at=served_at, view=view)
        out.append({**built, "item": str(getattr(item, "id", "")), "lo": lo})
    return out


@entry(read_only=True)
def decision_sections_entry(vault: Any, repository: Any, connection: Any,
                            candidates: Sequence[tuple[Sequence[str], Sequence[str]]], *, served_at: str,
                            view: Any = None) -> list[dict[str, Any]]:
    """:func:`decision_sections` inside a read-only AD operation (the material view needs one)."""

    return decision_sections(vault, repository, connection, candidates, served_at=served_at, view=view)


def evidence_ids(state: Mapping[str, Any]) -> set[str]:
    """Every evidence id a card carries (the rationale's citations are checked against it, unvalidated)."""

    found: set[str] = set()
    for entries in (state.get("history") or {}).values():
        for entry in entries:
            if entry.get("evidence_id"):
                found.add(str(entry["evidence_id"]))
    return found


__all__ = ["ANCESTRY_ROUNDS", "CARD_VERSION", "ROW_LIMITS", "RUNGS", "SECTIONS", "available_sql", "build_sections",
           "decision_sections", "decision_sections_entry", "evidence_ids",
           "rung_card"]
