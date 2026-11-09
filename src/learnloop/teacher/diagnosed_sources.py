"""Instruct hand-off IH7 (spec_instruct_handoff_v1 §7c): the sections a lesson opened after a miss also reads.

A lesson opened from an offer or a suggestion (``origin = 'router'``) with a recent miss on its topics behind it
also loads the source sections that match the diagnosed confusion, beside the topic's linked sections. On Nov 8 the
offer was for rendering decision regions (linked: a short code listing) and the confusion was softmax against
``argmax``, which chapter 3 discusses. This module only chooses sections; the brief renders them
(:func:`learnloop.teacher.brief.build_brief`), and nothing here changes what the router decides.

**The miss behind a lesson** is read from what the lesson's origin already records, with no new time constant: the
lesson's ``origin_ref`` is the decision (an offer drawn at a plan block, an IH2 ``plan_interrupt`` offer, or a TE1b
suggestion; all are ``router_decisions`` rows) and its goal topics are the response's. The miss is the latest attempt
on those topics made at or before the decision. It counts only if a live diagnosis is in force for it: a pending,
failed, superseded or absent diagnosis leaves the lesson as it was and the record says which. No score or stuck flag
is read, so an attempt that was correct simply has no diagnosis. A lesson the learner starts from a Reader selection,
on a typed topic, or from IH3's "Something else would help" is ``learner_pick`` with no ``origin_ref``: nothing links
it to a miss, so it is unchanged.

**What searches** (in this order): the miss's hypotheses (``causal_hypotheses``, the latest version of each, the
learner's ``my_gap`` marks first, then the rest in the order they were written; a ``retired`` or ``demoted`` one is
left out unless the learner marked it ``my_gap``), then the attempt's learner-text gaps (``learner_text_gaps.named_json``'s
belief statement, not undone). One search per statement, so each section names what found it.

**How** it searches: ``section_coverage.search_sections(read_only=True)``: keyword (BM25) retrieval only, per source,
over the section library's scope (``Library.search_scope``), grouped to sendable sections at most
``SECTIONS_PER_SOURCE`` per source and statement. ``read_only`` means no query embedding, no rewrite, no model call and
no delivery log, so the brief stays built deterministically from the ledger and nothing here calls out. The Library
already drops withheld sections, exam and held-out material, and exercises and solutions before anything is returned.

**Secrecy.** The lesson is not blind (only the grader is), so the concern is protected and held-out material. A
statement is used only when the shared protection (``learner_protection.PastWork``) passes it: the miss itself may not
be an exam or held-out answer, a reserved, cold-in-flight or diagnostic-probe item (``evidence_reason``), nor may any
answer a hypothesis rests on, nor an input its write-time record names (an answer, item, question or book passage); an
incomplete record is left out (fail closed). No item's expected answer, rubric or the diagnosis's free analysis
(``analysis_md``, which may quote them) is read here. A statement on an unprotected item may still restate what the
diagnoser saw; that is the rule the router card and the figure author's learner state already apply to such text.

Read-only: nothing is written and no model is called.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

_LOG = logging.getLogger(__name__)

VERSION = "lesson_sources_follow_v1"

#: Hypothesis statuses that are no longer a live cause of the miss (a probe or a later reading set them aside).
_SET_ASIDE = ("retired", "demoted")
#: The learner-text gap kinds that name a belief or a missing prerequisite (the figure author's and the cues' rule).
_NAMING_KINDS = ("prerequisite", "misconception")
#: A statement shown in the record at most this long (``section_coverage.STATEMENT_CHARS``, a display bound).
STATEMENT_CHARS = 600

NO_ORIGIN = "the lesson's offer is not on record"
NO_MISS = "no attempt on these topics before the offer"
PENDING = "the diagnosis of that attempt is still being written"
FAILED = "the diagnosis of that attempt did not complete"
SUPERSEDED = "the diagnosis of that attempt no longer applies (the answer was regraded)"
ABSENT = "that attempt has no diagnosis"
NO_CONFUSION = "the diagnosis names no confusion that can be searched"
NOTHING_MATCHED = "no section matched the diagnosed confusion that the lesson was not already given"
PROTECTED = "the attempt behind the lesson is protected material"
UNREADABLE = "the retrieval could not be read"
OVER_BUDGET = "over the sources budget: listed in the outline, the teacher can read it with read_source"
TOPIC_FILLS_BUDGET = "the topic's own sections already fill the sources budget: listed in the outline"


@dataclass
class Confusion:
    """One statement the sections were searched with."""

    index: int
    kind: str
    id: str
    text: str
    mark: str | None = None
    #: Why it was not searched (protected, an unreadable record); None: it was.
    withheld: str | None = None
    matched: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"kind": self.kind, "id": self.id}
        if self.withheld is None:
            out["text"] = self.text
        else:
            out["withheld"] = self.withheld
        if self.mark:
            out["mark"] = self.mark
        if self.withheld is None:
            out["matched"] = list(self.matched)
        return out


@dataclass
class Follow:
    """What :func:`follow` found: the sections to add (in the order they are tried against the budget), the
    statement indexes that found each, and the record (``status`` and ``why`` always; the rest when searched)."""

    record: dict[str, Any]
    extras: list[tuple[str, str]] = field(default_factory=list)
    found_by: dict[tuple[str, str], list[int]] = field(default_factory=dict)
    confusions: list[Confusion] = field(default_factory=list)
    attempt_id: str | None = None

    def none(self, why: str) -> "Follow":
        self.record.update({"status": "none", "why": why})
        return self

    def settle(self, library: Any, rendered: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """The record once the brief rendered the sections: what was added whole, what the outline holds and why."""

        by_ref = {str(entry["ref"]): entry for entry in rendered}
        added: list[dict[str, Any]] = []
        for key in self.extras:
            ref = f"{key[0]}/{key[1]}"
            section = library.section(*key)
            entry = {"ref": ref, "title": section.title if section else key[1],
                     "source": section.source_title if section else None,
                     "found_by": [self.confusions[i].text for i in self.found_by.get(key, ())]}
            outcome = by_ref.get(ref, {})
            entry["shown"] = outcome.get("shown", "left_out")
            if outcome.get("why"):
                entry["why"] = outcome["why"]
            added.append(entry)
        self.record["added"] = added
        whole = [entry for entry in added if entry["shown"] == "whole"]
        self.record.update({"status": "added" if whole else "listed" if added else "none",
                            "why": "" if added else NOTHING_MATCHED})
        return self.record

    def brief_entry(self) -> dict[str, Any] | None:
        """What the teacher is told: each section, the statement that found it, and where it is listed instead."""

        added = self.record.get("added") or []
        if not added:
            return None
        return {"added": [{"ref": e["ref"], "title": e["title"], "found_by": e["found_by"]}
                          for e in added if e["shown"] == "whole"],
                "listed_in_outline": [{"ref": e["ref"], "title": e["title"], "found_by": e["found_by"],
                                       "why": e.get("why")} for e in added if e["shown"] == "outline"]}


def _clip(text: Any) -> str:
    flat = " ".join(str(text or "").split())
    return flat if len(flat) <= STATEMENT_CHARS else flat[: STATEMENT_CHARS - 1].rstrip() + "…"


def _table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (name,)).fetchone() is not None


def _record_reason(past: Any, connection: Any, kind: str, record_id: str) -> str | None:
    """Why a text's write-time record names something protected, or None: no record is no more than the attempt
    itself (the router card reads a cause the same way); an incomplete one cannot be established (fail closed). Only
    what the writer read is checked: an answer, item, question or passage. Not its rubric or solution reading
    (``solution_items``): the lesson is not blind and those are covered by the item's own protection."""

    from learnloop.db.stores.write_provenance import stored_record

    stored = stored_record(connection, kind, record_id)
    if stored is None:
        return None
    if not stored.record.complete:
        return "what the text was written from could not be established"
    inputs = stored.record.inputs
    reason = past.evidence_reason(sorted(inputs.answers), sorted(inputs.items))
    if reason:
        return reason
    for event in sorted(inputs.questions):
        reason = past.question_reason(event, inputs.questions[event])
        if reason:
            return reason
    return past.source_reason(inputs.sources)


def _named(row: Mapping[str, Any]) -> str:
    named: Any = row.get("named") or row.get("named_json") or {}
    if isinstance(named, str):
        try:
            named = json.loads(named)
        except ValueError:
            named = {}
    if not isinstance(named, Mapping):
        return ""
    return str(named.get("belief_statement") or named.get("prerequisite_line")
               or named.get("prerequisite_name") or "").strip()


def _decision_time(connection: Any, decision_id: str) -> str | None:
    row = connection.execute("SELECT created_at FROM router_decisions WHERE id = ?", (decision_id,)).fetchone()
    return None if row is None else str(row[0])


def _miss(connection: Any, learning_object_ids: Sequence[str], decided_at: str) -> dict[str, Any] | None:
    """The latest attempt on the lesson's topics made at or before the offer's decision."""

    ids = sorted(set(learning_object_ids))
    if not ids:
        return None
    row = connection.execute(
        f"SELECT id, learning_object_id, practice_item_id, created_at FROM practice_attempts "
        f"WHERE learning_object_id IN ({','.join('?' for _ in ids)}) AND created_at <= ? "
        "ORDER BY created_at DESC, id DESC LIMIT 1", (*ids, decided_at)).fetchone()
    return None if row is None else {"attempt_id": str(row[0]), "learning_object_id": str(row[1]),
                                     "practice_item_id": row[2], "at": str(row[3])}


def _why_no_diagnosis(connection: Any, attempt_id: str) -> str:
    """Pending, failed, superseded or absent: the one plain reason the attempt has no diagnosis in force."""

    if _table(connection, "post_attempt_jobs"):
        for state, payload in connection.execute(
                "SELECT state, payload_json FROM post_attempt_jobs WHERE attempt_id = ? AND kind = 'diagnose' "
                "AND state IN ('queued', 'leased')", (attempt_id,)):
            try:
                mode = (json.loads(payload or "{}") or {}).get("mode", "live")
            except ValueError:
                mode = "live"
            if mode == "live":
                return PENDING
    if _table(connection, "attempt_diagnoses"):
        row = connection.execute(
            "SELECT status FROM attempt_diagnoses WHERE attempt_id = ? AND mode = 'live' "
            "ORDER BY created_at DESC, id DESC LIMIT 1", (attempt_id,)).fetchone()
        if row is not None:
            return SUPERSEDED if row[0] == "completed" else FAILED
    return ABSENT


def _statements(vault: Any, repository: Any, connection: Any, past: Any, attempt: Mapping[str, Any]) -> list[Confusion]:
    """The miss's hypotheses, then its learner-text gaps, each passed through the shared protection."""

    from learnloop.db.stores import hypothesis_marks as marks_store
    from learnloop.followup_serve import marks as opinion
    from learnloop.learner_protection import hypothesis_answers

    attempt_id = str(attempt["attempt_id"])
    out: list[Confusion] = []

    def passes(kind: str, record_id: str, answers: Iterable[str]) -> str | None:
        reason = past.evidence_reason(sorted({*answers, attempt_id}), [attempt.get("practice_item_id")])
        return reason or _record_reason(past, connection, kind, record_id)

    marked: set[str] = set()
    marks: dict[str, str] = {}
    if marks_store.present(connection):
        for key, row in opinion.latest_marks(marks_store.marks_for_attempt(connection, attempt_id)).items():
            if key is not None and row.get("mark") == opinion.MY_GAP:
                marked.add(str(key))
                marks[str(key)] = str(row["mark"])
    rows = repository.causal_hypotheses_for_attempt(attempt_id)
    rows = [row for row in rows if row.get("status") not in _SET_ASIDE or str(row.get("episode_key")) in marked]
    rows.sort(key=lambda row: str(row.get("episode_key")) not in marked)  # stable: my_gap first, then written order
    behind = hypothesis_answers(connection, [str(row["id"]) for row in rows])
    for row in rows:
        text = _clip(row.get("statement"))
        if not text:
            continue
        reason = passes("hypothesis", str(row["id"]), behind.get(str(row["id"]), ()))
        out.append(Confusion(len(out), "hypothesis", str(row["id"]), text, mark=marks.get(str(row.get("episode_key"))),
                             withheld=reason))
    if _table(connection, "learner_text_gaps"):
        from learnloop.db.stores import learner_gaps as gap_store

        gaps = [row for row in gap_store.gaps_for_attempt(connection, attempt_id)
                if row.get("kind") in _NAMING_KINDS]
        undone = {row["gap_id"] for row in gap_store.reversals(connection, [row["id"] for row in gaps])}
        for row in gaps:
            text = _clip(_named(row))
            if row["id"] in undone or not text:
                continue
            reason = passes("learner_text_gap", str(row["id"]), ()) or past.reading_reason(
                row.get("source_kind"), row.get("source_id"))
            out.append(Confusion(len(out), "learner_text_gap", str(row["id"]), text, withheld=reason))
    return out


def follow(vault: Any, repository: Any, library: Any, *, origin: str, origin_ref: str | None,
           learning_object_ids: Sequence[str], in_hand: Collection[tuple[str, str]]) -> Follow | None:
    """The sections a lesson opened from this origin also reads, or None when the lesson is not one that applies
    (a learner's own start: nothing to say, so no record). ``in_hand``: the sections the lesson already gets (the
    topic's linked ones, a Reader selection first among them), which are never added twice."""

    if origin != "router" or not origin_ref:
        return None
    from learnloop.learner_protection import PastWork
    from learnloop.source_retrieval import section_coverage as SC

    result = Follow(record={"version": VERSION})
    try:
        with repository.connection() as connection:
            decided_at = _decision_time(connection, origin_ref)
            if decided_at is None:
                return result.none(NO_ORIGIN)
            attempt = _miss(connection, learning_object_ids, decided_at)
            if attempt is None:
                return result.none(NO_MISS)
            result.attempt_id = attempt["attempt_id"]
            result.record["miss"] = {"attempt_id": attempt["attempt_id"], "learning_object_id": attempt["learning_object_id"],
                                     "decision_id": origin_ref, "decision_at": decided_at, "attempt_at": attempt["at"]}
            live = repository.current_live_diagnosis(attempt["attempt_id"])
            if live is None:
                return result.none(_why_no_diagnosis(connection, attempt["attempt_id"]))
            result.record["diagnosis_id"] = str(live["id"])
            past = PastWork(connection, vault, repository)
            if not past.withheld.available or past.attempt_reason(attempt["attempt_id"]):
                return result.none(PROTECTED)
            confusions = _statements(vault, repository, connection, past, attempt)
    except Exception:  # noqa: BLE001 - a lesson opens without the added sections rather than not at all
        _LOG.warning("lesson sources: the diagnosed confusion could not be read", exc_info=True)
        return result.none(UNREADABLE)
    result.confusions = confusions
    searchable = [c for c in confusions if c.withheld is None]
    if not searchable:
        result.record["confusions"] = [c.as_dict() for c in confusions]
        return result.none(NO_CONFUSION)
    held = set(in_hand)
    try:
        for confusion in searchable:
            per_source = SC.search_sections(vault, repository, library, confusion.text, read_only=True)
            # Rank 1 of every source first, then rank 2: the retrieval gives no score across books.
            ranked = [hit for rank in range(SC.SECTIONS_PER_SOURCE)
                      for source_id in sorted(per_source) if rank < len(per_source[source_id])
                      for hit in [per_source[source_id][rank]]]
            for extraction_id, section_id, _spans in ranked:
                key = (extraction_id, section_id)
                if key in held or library.section(*key) is None:
                    continue
                confusion.matched.append(f"{extraction_id}/{section_id}")
                if key not in result.found_by:
                    result.extras.append(key)
                result.found_by.setdefault(key, []).append(confusion.index)
    except Exception:  # noqa: BLE001 - e.g. no keyword index: the lesson opens as it did
        _LOG.warning("lesson sources: the keyword search failed", exc_info=True)
        result.extras, result.found_by = [], {}
        result.record["confusions"] = [c.as_dict() for c in confusions]
        return result.none(UNREADABLE)
    result.record["confusions"] = [c.as_dict() for c in confusions]
    if not result.extras:
        return result.none(NOTHING_MATCHED)
    result.record.update({"status": "added", "why": ""})
    return result


__all__ = ["Follow", "VERSION", "follow"]
