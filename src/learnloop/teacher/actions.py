"""The teacher's read actions (spec_teacher_v1 §9, §9.1, §9.2; curriculum C4's ``read_note``).

Policy comes from the caller, never from arguments (§9.1): the lesson is caller
kind ``teacher``; with no check open its policy is ``reading``; with a lesson
check open, ``assisted_practice`` bound to the check's minted item (its
committed solution is filtered out of every result). Every result passes the
same protection the brief does:

* ``read_source``: whole sections of the section library (current readings with
  teaching authority; exam and held-out material and withheld sections left out
  before anything is returned), model-safe passages only (no exercises or
  solutions), each with a fresh alias the teacher may cite;
* ``find_sources`` / ``find_practice``: the instructional dispatcher under caller
  ``teacher`` (receipts in ``source_tool_calls``; never an expected answer,
  rubric, hint or solution);
* ``read_history``: the learner's own words and results for history ids from
  the brief, through ``learner_protection`` (an exam or protected attempt keeps
  its result and shows no question and no answer; a withheld item's question is
  never shown). Owner principle 2026-11-01: the learner's questions, answers
  and history are not private from the teacher; only the grader stays blind;
* ``read_note`` (C4, ``teacher.brief.use_deliverable`` and ``notes.enabled``):
  one of the learner's linked notes, labelled as their own voice.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from learnloop.teacher.contracts import ActionRequestV1

#: How many passages one search result carries back (the dispatcher's own bound applies first).
_HISTORY_TEXT_CHARS = 4000


class ActionRefused(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def caller_for(state: Any) -> Any:
    from learnloop.source_retrieval.policy import CallerContext

    open_check = state.open_check
    return CallerContext(
        kind="teacher", ref=state.lesson_id,
        context="practice" if open_check is not None else None,
        item_id=open_check["item_id"] if open_check is not None else None,
        learning_object_ids=tuple(state.los))


def run_read(vault: Any, repository: Any, state: Any, request: ActionRequestV1, *, model: str | None) -> dict[str, Any]:
    if request.action == "read_source":
        return read_source(vault, repository, state, request.refs)
    if request.action in ("find_sources", "find_practice"):
        return find(vault, repository, state, request, model=model)
    if request.action == "read_history":
        return read_history(vault, repository, state, request.refs)
    if request.action == "read_note":
        from learnloop.teacher.notes import read_note

        return read_note(vault, repository, state, request.refs)
    raise ActionRefused("unknown_action", f"{request.action} is not a read action")


def _open_solution(state: Any) -> str | None:
    if state.open_check is None:
        return None
    return str(state.open_check["check"]["committed_solution"])


def read_source(vault: Any, repository: Any, state: Any, refs: list[str]) -> dict[str, Any]:
    from learnloop.source_retrieval.section_coverage import Library
    from learnloop.teacher.brief import passage_teachable
    from learnloop.tutor.tutor_qa import span_leaks_expected

    library = Library(vault, repository)
    solution = _open_solution(state)
    sections = []
    added: dict[str, Any] = {}
    for ref in refs:
        if ref in state.book.passages:
            passage = state.book.passages[ref]
            # An alias is read back only while its passage is still teachable (review F4): the
            # library's protection NOW, not when the passage was first delivered.
            if ref in state.book.revoked or not passage_teachable(library, str(passage["extraction_id"]),
                                                                  str(passage["span_id"])):
                state.book.revoked.add(ref)
                sections.append({"ref": ref, "refused": "no longer a readable teaching passage"})
                continue
            if solution and span_leaks_expected(str(passage["text"]), solution):
                sections.append({"ref": ref, "passages": [], "withheld_for_open_check": 1})
                continue
            sections.append({"ref": ref, "passages": [{"alias": ref, "text": passage["text"]}]})
            continue
        if "/" not in ref:
            sections.append({"ref": ref, "refused": "unknown reference"})
            continue
        extraction_id, section_id = ref.split("/", 1)
        reading = library.reading(extraction_id)
        section = library.section(extraction_id, section_id)
        if reading is None or section is None or section_id in reading.withheld:
            sections.append({"ref": ref, "refused": "not a readable teaching section"})
            continue
        passages = []
        withheld = 0
        for span in section.span_ids:
            text = str(reading.texts.get(span) or "").strip()
            if not text:
                continue
            if solution and span_leaks_expected(text, solution):
                withheld += 1
                continue
            before = set(state.book.passages)
            alias = state.book.alias_for(extraction_id, span, text, section_ref=ref)
            if alias not in before:
                added[alias] = state.book.passages[alias]
            passages.append({"alias": alias, "text": text})
        state.book.sections.setdefault(ref, {"extraction_id": extraction_id, "section_id": section_id,
                                             "title": section.title, "source_title": section.source_title})
        entry = {"ref": ref, "title": section.title, "source": section.source_title, "passages": passages}
        if withheld:
            entry["withheld_for_open_check"] = withheld
        sections.append(entry)
    return {"sections": sections, "book_additions": added}


def find(vault: Any, repository: Any, state: Any, request: ActionRequestV1, *, model: str | None) -> dict[str, Any]:
    from learnloop.instructional.tools import ToolArgumentsInvalid, request_tool, run_requested_tool
    from learnloop.source_retrieval.policy import PolicyRefused

    caller = caller_for(state)
    if request.action == "find_sources":
        arguments: dict[str, Any] = {"query": request.query or "", "intent": request.intent or "explain"}
    else:
        arguments = {"query": request.query or "", "intent": request.intent or "practice",
                     "learning_object_ids": [lo for lo in request.learning_object_ids if lo in vault.learning_objects]
                     or list(state.los), "unattempted_only": bool(request.unattempted_only)}
    try:
        entry = request_tool(vault, repository, request.action, arguments, caller=caller, model=model,
                             prompt_version="teacher_turn.v1")
        if entry["status"] != "requested":
            refusal = entry.get("refusal") or {}
            return {"refused": refusal.get("code"), "message": refusal.get("message"),
                    "tool_call_id": entry["tool_call_id"]}
        out = run_requested_tool(vault, repository, entry["tool_call_id"])
    except (PolicyRefused, ToolArgumentsInvalid) as exc:
        return {"refused": getattr(exc, "code", "refused"), "message": str(exc)}
    result = dict(out.get("result") or {})
    added: dict[str, Any] = {}
    if request.action == "find_sources":
        passages = []
        for passage in result.get("passages") or []:
            extraction_id, _, span_id = str(passage.get("span_key") or "").partition(":")
            if not span_id:
                continue
            before = set(state.book.passages)
            alias = state.book.alias_for(extraction_id, span_id, str(passage.get("text") or ""))
            if alias not in before:
                added[alias] = state.book.passages[alias]
            passages.append({"alias": alias, "source": passage.get("source_title"), "section": passage.get("section"),
                             "text": passage.get("text")})
        result = {"intent": result.get("intent"), "status": result.get("status"), "passages": passages}
    else:
        result = {"intent": result.get("intent"), "status": result.get("status"),
                  "items": [{k: entry.get(k) for k in ("practice_item_id", "learning_object_id", "prompt",
                                                       "difficulty", "source_label")}
                            for entry in result.get("items") or []]}
    return {**result, "tool_call_id": out.get("tool_call_id"), "book_additions": added}


def read_history(vault: Any, repository: Any, state: Any, refs: list[str]) -> dict[str, Any]:
    from learnloop.learner_protection import attempt_protection, withheld_items

    withheld = withheld_items(vault, repository)
    allowed = {entry["id"] for entry in state.brief.get("history") or []}
    allowed |= {entry["id"] for entry in state.brief.get("last_lessons") or []}
    out = []
    with repository.connection() as connection:
        for ref in refs:
            if ref not in allowed:
                out.append({"id": ref, "refused": "not in the brief's history"})
                continue
            kind, _, raw = ref.partition(":")
            if kind == "h":
                cursor = connection.execute(
                    "SELECT id, practice_item_id, learning_object_id, attempt_type, learner_answer_md, correctness, "
                    "answer_confidence, created_at, probe_presentation_id FROM practice_attempts WHERE id = ?", (raw,))
                row = cursor.fetchone()
                if row is None:
                    out.append({"id": ref, "refused": "not found"})
                    continue
                data = dict(zip([d[0] for d in cursor.description], row))
                protected = attempt_protection(withheld, {"item": data["practice_item_id"],
                                                          "type": data["attempt_type"],
                                                          "probe": data.get("probe_presentation_id")})
                feedback = connection.execute(
                    "SELECT evidence FROM grading_evidence WHERE attempt_id = ? AND superseded_at IS NULL "
                    "ORDER BY id", (raw,)).fetchall()
                entry = {"id": ref, "type": data["attempt_type"], "at": data["created_at"],
                         "correctness": data["correctness"], "tap": data["answer_confidence"]}
                if protected:
                    entry["protected"] = "kept for an exam or a check: the result only"
                else:
                    item = vault.practice_items.get(str(data["practice_item_id"]))
                    entry["question"] = str(item.prompt)[:_HISTORY_TEXT_CHARS] if item is not None else None
                    entry["learner_answer"] = str(data["learner_answer_md"] or "")[:_HISTORY_TEXT_CHARS]
                    entry["grader_notes"] = [str(r[0])[:600] for r in feedback if r[0]]
                out.append(entry)
            elif kind == "q":
                row = connection.execute(
                    "SELECT practice_item_id, question_md, answer_md, created_at FROM question_events WHERE id = ?",
                    (raw,)).fetchone()
                if row is None or withheld.reason(row[0]):
                    out.append({"id": ref, "refused": "not available"})
                    continue
                out.append({"id": ref, "at": row[3], "learner_question": row[1],
                            "tutor_answer": (row[2] or "")[:_HISTORY_TEXT_CHARS]})
            elif kind == "l":
                from learnloop.db.stores import lessons as store

                receipt = store.receipt(connection, raw) or {}
                out.append({"id": ref, "recap": receipt.get("recap"), "nodes": receipt.get("nodes_summary"),
                            "close_reason": receipt.get("close_reason")})
            else:
                out.append({"id": ref, "refused": "unknown history id"})
    return {"entries": out}


__all__ = ["ActionRefused", "caller_for", "find", "read_history", "read_source", "run_read"]
