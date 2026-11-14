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
is read, so an attempt that was correct simply has no diagnosis. A lesson the learner starts from a Reader selection
or on a typed topic is ``learner_pick`` with no ``origin_ref``: nothing links it to a miss, so it is unchanged.

**A lesson the learner asked for** (the owner's decision 2, Nov 9: "definitely use the latest miss on that topic"): one
started from IH3's "learn this" is ``learner_pick`` too, and its opening names the preference (``preference_ref``). The
ledger must say it was a request for a lesson on exactly these topics (``router_learner_preferences``, kind ``lesson``),
else nothing is added and the record says so. A request opens one lesson: the first opening that accepts it consumes it
(its open turn names it), and a later opening with the same id reads nothing and its record names the lesson that used
it. Its miss is the attempt the learner was looking at when they asked (the preference's ``attempt_id``, review 3 M1),
else the latest attempt on its topics known before the lesson opens. An attempt with no diagnosis at all (a correct
answer has none) is passed over to the next older one; the first that has one is the miss, and if its diagnosis is
still being written, failed or no longer applies, the lesson opens without diagnosed sections and the record says why.
It never falls back to an older diagnosed miss past a newer one. The record names the attempt it considered and every
attempt it passed over, with why. The rest is as above.

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

from learnloop.clock import utc_now_iso

_LOG = logging.getLogger(__name__)

VERSION = "lesson_sources_follow_v1"

#: Hypothesis statuses that are no longer a live cause of the miss (a probe or a later reading set them aside).
_SET_ASIDE = ("retired", "demoted")
#: The learner-text gap kinds that name a belief or a missing prerequisite (the figure author's and the cues' rule).
_NAMING_KINDS = ("prerequisite", "misconception")
#: A statement shown in the record at most this long (``section_coverage.STATEMENT_CHARS``, a display bound).
STATEMENT_CHARS = 600
#: A lesson option's ref (``daily_plan.types.LESSON_OFFER_PREFIX``; the teacher may not import the plan, so a test pins the
#: two equal).
LESSON_OFFER_PREFIX = "lesson_offer:"

NO_ORIGIN = "the lesson's offer is not on record"
NO_MISS = "no attempt on these topics before the offer"
#: The owner's decision 2 (Nov 9): a lesson the learner asked for ("learn this").
NO_REQUEST = "the learner's request for this lesson is not on record"
NO_DIAGNOSED_MISS = "no attempt on these topics has a diagnosis in force before the lesson opened"
#: Review 3, m3: a request opens one lesson.
REQUEST_USED = "this request already opened a lesson"
#: Review 3, M1: why an attempt was passed over on the way to the miss (``passed_over``).
NOT_A_MISS = "that attempt has no diagnosis (a correct answer has none)"
NOT_ON_TOPIC = "the attempt the learner was looking at is not on this lesson's topics"
NOT_KNOWN = "the attempt the learner was looking at is not on record before the lesson opened"
#: How the miss was chosen (``miss.chosen_as``).
ASKED_FROM = "the_attempt_the_learner_asked_from"
LATEST_ON_TOPIC = "the_latest_attempt_on_the_topic"
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


def _miss(connection: Any, config: Any, learning_object_ids: Sequence[str], decided_at: str) -> dict[str, Any] | None:
    """The latest attempt on the lesson's topics known at the offer's decision (THE availability predicate: a
    backdated import that arrived later was not what the offer was made on)."""

    from learnloop.router_objective_switches import attempt_time_sql

    ids = sorted(set(learning_object_ids))
    if not ids:
        return None
    known = attempt_time_sql(config)
    row = connection.execute(
        f"SELECT id, learning_object_id, practice_item_id, created_at FROM practice_attempts "
        f"WHERE learning_object_id IN ({','.join('?' for _ in ids)}) AND created_at <= ? AND {known} <= ? "
        "ORDER BY created_at DESC, id DESC LIMIT 1", (*ids, decided_at, decided_at)).fetchone()
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


def _asked_lesson(connection: Any, preference_id: str, learning_object_ids: Sequence[str]) -> dict[str, Any] | None:
    """The learner's "learn this" (IH3's ``router_learner_preferences`` row) when it names a lesson on exactly these
    topics, else None: the client names the preference, and the ledger is what says it was a request for this lesson."""

    from learnloop.db.stores import router as router_store

    if not router_store.preferences_present(connection):
        return None
    row = router_store.learner_preference(connection, preference_id)
    if row is None or str(row.get("chosen_kind")) != "lesson":
        return None
    ref = str(row.get("chosen_ref") or "")
    lo = ref[len(LESSON_OFFER_PREFIX):] if ref.startswith(LESSON_OFFER_PREFIX) else ref
    return dict(row) if sorted(set(learning_object_ids)) == [lo] else None


def _lesson_that_used(connection: Any, preference_id: str) -> str | None:
    """The lesson whose opening already consumed this request (its open turn names it in ``refs.preference``), or None."""

    if not _table(connection, "lesson_turns"):
        return None
    row = connection.execute(
        "SELECT lesson_id FROM lesson_turns WHERE action = 'open' AND json_extract(refs_json, '$.preference') = ? "
        "ORDER BY created_at, id LIMIT 1", (preference_id,)).fetchone()
    return None if row is None else str(row[0])


def _not_a_miss(connection: Any, attempt_id: str) -> bool:
    """No live diagnosis was ever queued or written for the attempt (a correct answer has none), or the one that ran found
    none needed. Structure on record, not a score: a pending, failed or superseded diagnosis is a miss's."""

    if _why_no_diagnosis(connection, attempt_id) == ABSENT:
        return True
    if not _table(connection, "attempt_diagnoses"):
        return False
    row = connection.execute(
        "SELECT status, error FROM attempt_diagnoses WHERE attempt_id = ? AND mode = 'live' "
        "ORDER BY created_at DESC, id DESC LIMIT 1", (attempt_id,)).fetchone()
    return row is not None and row[0] == "skipped" and row[1] == "not_needed"


def _attempt(row: Sequence[Any]) -> dict[str, Any]:
    return {"attempt_id": str(row[0]), "learning_object_id": str(row[1]), "practice_item_id": row[2], "at": str(row[3])}


def _asked_miss(connection: Any, repository: Any, config: Any, preference: Mapping[str, Any],
                learning_object_ids: Sequence[str], at: str
                ) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None, list[dict[str, str]]]:
    """The owner's decision 2 (Nov 9): the miss behind a lesson the learner asked for, as ``(attempt, live diagnosis, why
    none, passed over)``. First the attempt the learner was looking at (the preference's ``attempt_id``, review 3 M1),
    then the attempts on the lesson's topics known before the lesson opens (THE availability predicate, as
    :func:`_miss`), latest first. An attempt with no diagnosis at all is passed over (a correct answer has none); the
    first with one is the miss: its live diagnosis in force (``Repository.current_live_diagnosis``), or why it has none
    (pending, failed, superseded), and then no older miss is read. No score, stuck flag or time constant is read."""

    from learnloop.router_objective_switches import attempt_time_sql

    ids = sorted(set(learning_object_ids))
    passed: list[dict[str, str]] = []
    if not ids:
        return None, None, NO_DIAGNOSED_MISS, passed
    known = attempt_time_sql(config)
    columns = "a.id, a.learning_object_id, a.practice_item_id, a.created_at"
    order: list[tuple[dict[str, Any], str]] = []
    asked_from = str(preference.get("attempt_id") or "")
    if asked_from:
        row = connection.execute(
            f"SELECT {columns} FROM practice_attempts a WHERE a.id = ? AND a.created_at <= ? AND {known} <= ?",
            (asked_from, at, at)).fetchone()
        if row is None:
            passed.append({"attempt_id": asked_from, "why": NOT_KNOWN})
        elif str(row[1]) not in ids:
            passed.append({"attempt_id": asked_from, "why": NOT_ON_TOPIC})
        else:
            order.append((_attempt(row), ASKED_FROM))
    rows = connection.execute(
        f"SELECT {columns} FROM practice_attempts a "
        f"WHERE a.learning_object_id IN ({','.join('?' for _ in ids)}) AND a.created_at <= ? AND {known} <= ? "
        "ORDER BY a.created_at DESC, a.id DESC", (*ids, at, at)).fetchall()
    order += [(_attempt(row), LATEST_ON_TOPIC) for row in rows if str(row[0]) != asked_from]
    for attempt, chosen_as in order:
        attempt["chosen_as"] = chosen_as
        live = repository.current_live_diagnosis(attempt["attempt_id"])
        if live is not None:
            return attempt, live, None, passed
        if _not_a_miss(connection, attempt["attempt_id"]):
            passed.append({"attempt_id": attempt["attempt_id"], "why": NOT_A_MISS})
            continue
        return attempt, None, _why_no_diagnosis(connection, attempt["attempt_id"]), passed
    return None, None, NO_DIAGNOSED_MISS, passed


def follow(vault: Any, repository: Any, library: Any, *, origin: str, origin_ref: str | None,
           learning_object_ids: Sequence[str], in_hand: Collection[tuple[str, str]],
           preference_ref: str | None = None, at: str | None = None) -> Follow | None:
    """The sections a lesson opened from this origin also reads, or None when the lesson is not one that applies
    (a learner's own start: nothing to say, so no record). ``in_hand``: the sections the lesson already gets (the
    topic's linked ones, a Reader selection first among them), which are never added twice.

    ``preference_ref`` (the owner's decision 2 of Nov 9): a ``learner_pick`` lesson the learner asked for through IH3's
    "learn this" names its preference, and reads the miss the learner asked from, else the latest miss on its topics
    before the lesson opens (``at``) (:func:`_asked_miss`). The first opening consumes the request: a later one reads
    nothing and says which lesson used it. A Reader selection or a typed topic names none, so it is unchanged."""

    if origin == "router" and origin_ref:
        asked = False
    elif origin == "learner_pick" and preference_ref:
        asked = True
    else:
        return None
    from learnloop.learner_protection import PastWork
    from learnloop.source_retrieval import section_coverage as SC

    result = Follow(record={"version": VERSION})
    try:
        with repository.connection() as connection:
            if asked:
                preference = _asked_lesson(connection, str(preference_ref), learning_object_ids)
                if preference is None:
                    return result.none(NO_REQUEST)
                opens_at = at or utc_now_iso()
                result.record["asked"] = {"preference_id": str(preference["id"]),
                                          "asked_at": str(preference["created_at"]), "lesson_opens_at": opens_at,
                                          "asked_from_attempt": preference.get("attempt_id")}
                used_by = _lesson_that_used(connection, str(preference["id"]))
                if used_by is not None:
                    result.record["asked"]["already_opened_lesson"] = used_by
                    return result.none(REQUEST_USED)
                attempt, live, why, passed = _asked_miss(connection, repository, vault.config, preference,
                                                         learning_object_ids, opens_at)
                result.record["passed_over"] = passed
                if attempt is None:
                    return result.none(why or NO_DIAGNOSED_MISS)
                result.attempt_id = attempt["attempt_id"]
                result.record["miss"] = {"attempt_id": attempt["attempt_id"],
                                         "learning_object_id": attempt["learning_object_id"],
                                         "attempt_at": attempt["at"], "chosen_as": attempt["chosen_as"]}
                if live is None:
                    return result.none(why or ABSENT)
            else:
                decided_at = _decision_time(connection, str(origin_ref))
                if decided_at is None:
                    return result.none(NO_ORIGIN)
                attempt = _miss(connection, vault.config, learning_object_ids, decided_at)
                if attempt is None:
                    return result.none(NO_MISS)
                result.attempt_id = attempt["attempt_id"]
                result.record["miss"] = {"attempt_id": attempt["attempt_id"],
                                         "learning_object_id": attempt["learning_object_id"],
                                         "decision_id": origin_ref, "decision_at": decided_at,
                                         "attempt_at": attempt["at"]}
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


def consumed_preference(record: Mapping[str, Any]) -> str | None:
    """The request a lesson's opening consumes (review 3, m3): one its record accepted and no earlier lesson used."""

    asked = record.get("asked") if isinstance(record, Mapping) else None
    if not isinstance(asked, Mapping) or asked.get("already_opened_lesson"):
        return None
    return str(asked["preference_id"]) if asked.get("preference_id") else None


__all__ = ["Follow", "VERSION", "consumed_preference", "follow"]
