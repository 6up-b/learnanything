"""``LessonBriefV1``: the lesson's opening context, built deterministically from the ledger (spec_teacher_v1 §8.1).

The brief is the only learner context at open; anything more comes through
actions. It holds:

* ``goal``: the text, the LO ids and how they were resolved (curriculum C4, with
  ``teacher.brief.use_deliverable`` on and a deliverable in play: the
  deliverable's sentence and its resolution's phrase per LO);
* ``nodes``: per goal LO and its prerequisite closure (to ``teacher.brief.depth``):
  its statement, its label (demonstrated, assumed, learning or new), the predicted
  unassisted success in words with its interval and the predictor named
  (adaptive difficulty's readiness line beside it when AD serves), retrievability,
  the last cold result, open misconceptions, and eligible vault probe items as
  headers only (C4: the learner's linked notes as headers, ``your_notes``);
* ``history``: one-line headers of attempts and tutor questions on these LOs
  (assisted, primed or cold, the tap and the hedge read); text comes through
  ``read_history``;
* ``last_lessons``: earlier receipts on these LOs with their delayed checks' results;
* ``sources``: the goal's sections whole (C4: the deliverable path's primaries
  whole, alternates as outline), model-safe passages only, each with a short
  alias (``S1``) the teacher cites; over ``teacher.context.sources_tokens``, the
  outline instead;
* ``constraints`` and ``doctrine``.

**Never in the brief:** EVSI values, costs or policy scores; cold-reserve or
protected items; any item's expected answer or rubric; exam or held-out material
(the section library's protection and ``learner_protection.withheld_items``
remove it before anything is rendered).

Owner principle (2026-11-01): the learner's own questions, answers and history
are not private from the teacher and are included where they help; only the
blind grader stays blind.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.adf_numeric import sigmoid
from learnloop.attempts.grading_admission import estimated_prompt_tokens
from learnloop.learner.lesson_weight import predicted_success
from learnloop.teacher.contracts import BRIEF_VERSION
from learnloop.teacher.doctrines import doctrine_identity

#: How a header shows a long prompt (a size bound: the text comes through the actions).
STEM_CHARS = 160
#: The interval shown with a prediction: the conventional 95% interval of the mastery model's logit.
INTERVAL_Z = 1.959964


class LessonRefused(ValueError):
    """A lesson that may not open (protected material, an unknown topic), with one plain line."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class SourceBook:
    """The passages delivered to the teacher, by alias (citation validation and reveals read it)."""

    passages: dict[str, dict[str, Any]] = field(default_factory=dict)
    sections: dict[str, dict[str, Any]] = field(default_factory=dict)

    def alias_for(self, extraction_id: str, span_id: str, text: str, *, section_ref: str | None = None) -> str:
        for alias, passage in self.passages.items():
            if passage["extraction_id"] == extraction_id and passage["span_id"] == span_id:
                return alias
        alias = f"S{len(self.passages) + 1}"
        self.passages[alias] = {"extraction_id": extraction_id, "span_id": span_id, "text": text,
                                "section_ref": section_ref}
        return alias

    def as_dict(self) -> dict[str, Any]:
        return {"passages": self.passages, "sections": self.sections}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any] | None) -> "SourceBook":
        value = value or {}
        return cls(passages=dict(value.get("passages") or {}), sections=dict(value.get("sections") or {}))


# --- the goal ------------------------------------------------------------------


def resolve_goal(vault: Any, repository: Any, *, entry: str, learning_object_ids: Sequence[str] = (),
                 selection: Mapping[str, Any] | None = None) -> tuple[list[str], dict[str, str], dict[str, Any] | None]:
    """The lesson's LOs, how each was resolved, and the Reader selection's section (if any).

    An LO page gives that LO; a Reader selection gives its section's LOs (the section library's
    reading of the LO provenance, as the Reader's active reading resolves them); a selection of
    protected material is refused in one plain line (§7 step 1)."""

    from learnloop.source_retrieval.section_coverage import Library

    if entry in ("learning_object", "new_topic"):
        los = [lo for lo in dict.fromkeys(str(x) for x in learning_object_ids) if lo in vault.learning_objects]
        if not los:
            raise LessonRefused("unknown_topic", "That topic isn't in this vault.")
        how = {lo: ("the topic you opened" if entry == "learning_object" else "the new topic offered") for lo in los}
        return los, how, None
    if entry != "reader_selection" or not selection:
        raise LessonRefused("validation_error", "A lesson needs a topic or a passage.")
    extraction_id = str(selection.get("extraction_id") or "")
    span_ids = [str(span) for span in (selection.get("span_ids") or []) if span]
    library = Library(vault, repository)
    if extraction_id in library.left_out or any(library.protection.span_out(extraction_id, s) for s in span_ids):
        raise LessonRefused("protected", "That passage is kept for your exam, so I won't teach it.")
    reading = library.reading(extraction_id)
    if reading is None:
        raise LessonRefused("validation_error", "That passage isn't in your library's readable sections.")
    section_id = next((library.section_of(extraction_id, span) for span in span_ids
                       if library.section_of(extraction_id, span)), None)
    if section_id is None or section_id in reading.withheld:
        raise LessonRefused("protected", "That passage is kept for your exam, so I won't teach it.")
    los = [lo for lo in library.section_learning_objects(extraction_id, section_id) if lo in vault.learning_objects]
    extra = [lo for lo in learning_object_ids if lo in vault.learning_objects and lo not in los]
    los = [*los, *extra]
    if not los:
        raise LessonRefused("unknown_topic", "No topic in this vault is taught by that passage yet.")
    section = library.section(extraction_id, section_id)
    how = {lo: f"taught in the section you selected ({section.title if section else section_id})" for lo in los}
    return los, how, {"extraction_id": extraction_id, "section_id": section_id, "span_ids": span_ids}


# --- the graph -------------------------------------------------------------------


def _concept_los(vault: Any) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for lo_id in sorted(vault.learning_objects):
        learning_object = vault.learning_objects[lo_id]
        if learning_object.status == "active":
            out.setdefault(learning_object.concept, []).append(lo_id)
    return out


def _prerequisite_concepts(vault: Any) -> dict[str, set[str]]:
    """Concept -> its prerequisite concepts (LO declarations and ``prerequisite`` edges)."""

    out: dict[str, set[str]] = {}
    for learning_object in vault.learning_objects.values():
        out.setdefault(learning_object.concept, set()).update(learning_object.prerequisites)
    for edge in getattr(vault, "edges", ()) or ():
        if getattr(edge, "relation_type", None) == "prerequisite":
            out.setdefault(edge.target, set()).add(edge.source)
    return out


def prerequisite_nodes(vault: Any, goal: Sequence[str], depth: int) -> list[tuple[str, str, int]]:
    """``(lo, "goal" | "prerequisite", depth)`` for the goal LOs and their closure to ``depth``."""

    by_concept = _concept_los(vault)
    prerequisites = _prerequisite_concepts(vault)
    out: list[tuple[str, str, int]] = [(lo, "goal", 0) for lo in goal]
    seen = set(goal)
    frontier = list(goal)
    for level in range(1, max(depth, 0) + 1):
        following: list[str] = []
        for lo_id in frontier:
            learning_object = vault.learning_objects.get(lo_id)
            if learning_object is None:
                continue
            for concept in sorted(prerequisites.get(learning_object.concept, ())):
                for prerequisite in by_concept.get(concept, ()):
                    if prerequisite in seen:
                        continue
                    seen.add(prerequisite)
                    following.append(prerequisite)
                    out.append((prerequisite, "prerequisite", level))
        frontier = following
    return out


def downstream_learning_objects(vault: Any, learning_object_ids: Iterable[str]) -> list[str]:
    """Active LOs whose concept has one of these LOs' concepts as a prerequisite (transfer candidates)."""

    concepts = {vault.learning_objects[lo].concept for lo in learning_object_ids if lo in vault.learning_objects}
    prerequisites = _prerequisite_concepts(vault)
    targets = {concept for concept, needs in prerequisites.items() if needs & concepts}
    return [lo for lo in sorted(vault.learning_objects)
            if vault.learning_objects[lo].status == "active" and vault.learning_objects[lo].concept in targets
            and lo not in set(learning_object_ids)]


# --- predictions -------------------------------------------------------------------


def lo_prediction(vault: Any, repository: Any, learning_object_id: str) -> dict[str, Any]:
    """The active predictor's predicted unassisted success on the LO, with its interval, in words."""

    from learnloop.learner.mastery import item_irt_params

    learning_object = vault.learning_objects.get(learning_object_id)
    a, b = item_irt_params(None, learning_object, vault.config.mastery)
    state = repository.mastery_state(learning_object_id)
    if state is None and learning_object is not None:
        # No evidence yet: the model's own prior for the LO (what its first update would start from).
        from learnloop.clock import utc_now_iso
        from learnloop.learner.mastery import initial_mastery_state_for_learning_object

        state = initial_mastery_state_for_learning_object(vault, repository, learning_object_id, utc_now_iso())
    if state is None:
        return {"source": "mastery_ekf", "p": None, "words": "no prediction yet"}
    mu, var = float(state.logit_mean), float(state.logit_variance)
    p = predicted_success(mu, var, a=a, b=b)
    spread = INTERVAL_Z * math.sqrt(max(var, 0.0))
    low, high = float(sigmoid(a * (mu - spread - b))), float(sigmoid(a * (mu + spread - b)))
    return {"source": "mastery_ekf", "p": round(p, 4), "interval": [round(low, 4), round(high, 4)],
            "words": f"about {round(100 * p)}% on a fresh question on your own (between {round(100 * low)}% and "
                     f"{round(100 * high)}%; LearnLoop's mastery model)",
            "mu": mu, "variance": var, "item_a": a, "item_b": b,
            "last_evidence_at": state.last_evidence_at}


def ad_readiness(vault: Any, repository: Any, learning_object_id: str) -> dict[str, Any] | None:
    """Adaptive difficulty's readiness line for the LO when AD serves (its own read-only entry, its
    own guarded operation); None when AD is off, below its tag or denied (the brief says which)."""

    try:
        from learnloop.adaptive_difficulty.readiness import card_fields, lo_readiness

        line = lo_readiness(vault, repository, learning_object_id)
        if not line.get("predicted"):
            return None
        fields = card_fields(vault, repository, learning_object_id)
    except Exception:  # noqa: BLE001 - AD denied or unavailable: the active predictor stands, and says so
        return None
    return {"source": "adaptive_difficulty", "line": line.get("line"),
            "p_band_next": (fields or {}).get("p_band_next"), "p_bar_at_top": (fields or {}).get("p_bar_at_top"),
            "untested": (fields or {}).get("untested")}


# --- the parts ----------------------------------------------------------------------


def _retrievability(repository: Any, vault: Any, learning_object_id: str) -> float | None:
    item_ids = [item.id for item in vault.practice_items.values() if item.learning_object_id == learning_object_id]
    if not item_ids:
        return None
    marks = ",".join("?" for _ in item_ids)
    with repository.connection() as connection:
        row = connection.execute(
            f"SELECT MAX(retrievability) FROM practice_item_state WHERE practice_item_id IN ({marks})",
            item_ids).fetchone()
    return round(float(row[0]), 4) if row and row[0] is not None else None


def _misconceptions(repository: Any, learning_object_id: str) -> list[str]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT statement FROM misconceptions WHERE learning_object_id = ? AND status != 'resolved' "
            "ORDER BY created_at, id", (learning_object_id,)).fetchall()
    return [str(row[0]) for row in rows]


def _attempt_rows(repository: Any, learning_object_ids: Sequence[str]) -> list[dict[str, Any]]:
    if not learning_object_ids:
        return []
    marks = ",".join("?" for _ in learning_object_ids)
    with repository.connection() as connection:
        cursor = connection.execute(
            f"SELECT id, practice_item_id, learning_object_id, attempt_type, correctness, rubric_score, hints_used, "
            f"primed, answer_confidence, created_at, entry_surface, probe_presentation_id FROM practice_attempts "
            f"WHERE learning_object_id IN ({marks}) ORDER BY created_at, id", list(learning_object_ids))
        names = [d[0] for d in cursor.description]
        return [dict(zip(names, row)) for row in cursor.fetchall()]


_COLD_TYPES = frozenset({"independent_attempt", "open_text", "diagnostic_probe", "exam_attempt"})


def _cold(row: Mapping[str, Any]) -> bool:
    return row["attempt_type"] in _COLD_TYPES and not row["primed"] and not row["hints_used"]


def _result_words(row: Mapping[str, Any]) -> str:
    correctness = row.get("correctness")
    if correctness is None:
        return "not graded"
    if correctness >= 1.0:
        return "right"
    if correctness <= 0.0:
        return "wrong"
    return f"partly right ({round(100 * float(correctness))}%)"


def _history(vault: Any, repository: Any, learning_object_ids: Sequence[str], withheld: Any,
             hedges: Mapping[str, str]) -> list[dict[str, Any]]:
    from learnloop.learner_protection import attempt_protection

    out = []
    for row in _attempt_rows(repository, learning_object_ids):
        protected = attempt_protection(withheld, {"item": row["practice_item_id"], "type": row["attempt_type"],
                                                  "probe": row.get("probe_presentation_id")})
        kind = "cold" if _cold(row) else ("assisted" if row["attempt_type"] in (
            "hinted_attempt", "guided_walkthrough", "reconstruction_after_walkthrough") or row["hints_used"] else (
            "primed" if row["primed"] else row["attempt_type"]))
        tap = row.get("answer_confidence")
        hedge = hedges.get(str(row["id"]))
        header = {
            "id": f"h:{row['id']}", "learning_object_id": row["learning_object_id"], "at": row["created_at"],
            "kind": kind, "type": row["attempt_type"], "result": _result_words(row),
            "tap": f"marked {tap}/5 sure" if tap else None, "hedge": f"read as {hedge}" if hedge else None,
        }
        if protected:
            header["protected"] = "kept for an exam or a check: result only"
        out.append(header)
    item_ids = {item.id: item.learning_object_id for item in vault.practice_items.values()
                if item.learning_object_id in set(learning_object_ids)}
    if item_ids:
        marks = ",".join("?" for _ in item_ids)
        with repository.connection() as connection:
            rows = connection.execute(
                f"SELECT id, practice_item_id, question_md, created_at FROM question_events "
                f"WHERE practice_item_id IN ({marks}) AND answer_status = 'answered' ORDER BY created_at, id",
                list(item_ids)).fetchall()
        for event_id, item_id, question, created in rows:
            if withheld.reason(item_id):
                continue
            out.append({"id": f"q:{event_id}", "learning_object_id": item_ids[item_id], "at": created,
                        "kind": "tutor_question", "line": " ".join(str(question).split())[:STEM_CHARS]})
    out.sort(key=lambda entry: (str(entry["at"]), entry["id"]))
    return out


def _probe_headers(vault: Any, repository: Any, learning_object_id: str, withheld: Any,
                   attempted: set[str], prediction: Mapping[str, Any]) -> list[dict[str, Any]]:
    from learnloop.vault.lifecycle import practice_item_serving_block

    out = []
    for item in sorted(vault.practice_items.values(), key=lambda i: i.id):
        if item.learning_object_id != learning_object_id or item.id in attempted:
            continue
        if withheld.reason(item.id) or practice_item_serving_block(vault, item) is not None:
            continue
        out.append({"id": item.id, "stem": " ".join(str(item.prompt).split())[:STEM_CHARS],
                    "predicted": prediction.get("p")})
    return out


def _last_lessons(repository: Any, learning_object_ids: Sequence[str], exclude: str | None) -> list[dict[str, Any]]:
    from learnloop.db.stores import lessons as store

    out = []
    with repository.connection() as connection:
        for row in store.lessons_on(connection, learning_object_ids, exclude=exclude):
            receipt = store.receipt(connection, row["id"]) or {}
            checks = []
            for entry in receipt.get("delayed_checks") or []:
                result = _delayed_result(connection, entry)
                checks.append({**{k: entry.get(k) for k in ("purpose", "learning_object_id", "due")}, **result})
            out.append({"id": f"l:{row['id']}", "closed_at": row["closed_at"], "close_reason": row["close_reason"],
                        "nodes": receipt.get("nodes_summary") or [], "recap": receipt.get("recap"),
                        "delayed_checks": checks})
    return out


def _delayed_result(connection: Any, entry: Mapping[str, Any]) -> dict[str, Any]:
    item_id = entry.get("item_id")
    if not item_id:
        return {"result": "no question was found for it"}
    row = connection.execute(
        "SELECT correctness, answer_confidence, created_at, attempt_type, hints_used, primed FROM practice_attempts "
        "WHERE practice_item_id = ? ORDER BY created_at, id LIMIT 1", (item_id,)).fetchone()
    if row is None:
        return {"result": "not answered yet"}
    words = _result_words({"correctness": row[0]})
    cold = row[3] in _COLD_TYPES and not row[4] and not row[5]
    tap = f", marked {row[1]}/5 sure" if row[1] else ""
    return {"result": f"answered {'cold' if cold else 'with help'}: {words}{tap}", "answered_at": row[2]}


def _section_refs(vault: Any, library: Any, learning_object_ids: Sequence[str],
                  selection: Mapping[str, Any] | None) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    if selection:
        refs.append((str(selection["extraction_id"]), str(selection["section_id"])))
    for lo in learning_object_ids:
        for ref in library.provenance(lo):
            if ref not in refs:
                refs.append(ref)
    return refs


def _render_sources(library: Any, book: SourceBook, primaries: Sequence[tuple[str, str]],
                    outline_only: Sequence[tuple[str, str]], budget_tokens: int) -> dict[str, Any]:
    """Whole sections (model-safe passages) under the budget, else the outline; ``outline_only``
    sections (a deliverable's alternates) are listed by title."""

    whole: list[dict[str, Any]] = []
    total = 0
    for extraction_id, section_id in primaries:
        reading = library.reading(extraction_id)
        section = library.section(extraction_id, section_id)
        if reading is None or section is None or section_id in reading.withheld:
            continue
        ref = f"{extraction_id}/{section_id}"
        blocks = []
        for span in section.span_ids:
            text = str(reading.texts.get(span) or "").strip()
            if not text:
                continue
            blocks.append({"span": span, "text": text})
        total += estimated_prompt_tokens("\n".join(block["text"] for block in blocks))
        book.sections[ref] = {"extraction_id": extraction_id, "section_id": section_id, "title": section.title,
                              "source_title": section.source_title}
        whole.append({"ref": ref, "title": section.title, "source": section.source_title, "blocks": blocks})
    outline = [{"ref": f"{e}/{s}", "title": (library.section(e, s).title if library.section(e, s) else s),
                "source": (library.section(e, s).source_title if library.section(e, s) else None)}
               for e, s in outline_only if library.section(e, s) is not None]
    for entry in outline:
        e, s = entry["ref"].split("/", 1)
        book.sections[entry["ref"]] = {"extraction_id": e, "section_id": s, "title": entry["title"],
                                       "source_title": entry["source"]}
    if total > budget_tokens:
        return {"mode": "outline", "tokens": total,
                "sections": [{"ref": w["ref"], "title": w["title"], "source": w["source"]} for w in whole],
                "alternates": outline}
    rendered = []
    for section in whole:
        e, s = section["ref"].split("/", 1)
        passages = [{"alias": book.alias_for(e, block["span"], block["text"], section_ref=section["ref"]),
                     "text": block["text"]} for block in section["blocks"]]
        rendered.append({"ref": section["ref"], "title": section["title"], "source": section["source"],
                         "passages": passages})
    return {"mode": "whole", "tokens": total, "sections": rendered, "alternates": outline}


# --- curriculum C4 -------------------------------------------------------------------


def c4_active(vault: Any) -> bool:
    return bool(vault.config.teacher.brief.use_deliverable)


def deliverable_for(vault: Any, repository: Any, learning_object_ids: Sequence[str]) -> dict[str, Any] | None:
    """The nearest active deliverable whose resolution names one of the lesson's LOs, with its
    sentence, the resolution's phrase per LO and the path's primaries and alternates (C4, §8.2)."""

    try:
        from learnloop.source_retrieval import deliverable_path as DP
        from learnloop.source_retrieval import deliverables as DL

        if not DL.enabled(vault):
            return None
        wanted = set(learning_object_ids)
        for goal in DP.nearest_deliverables(vault, repository):
            resolution = DL.latest_resolution(repository, goal.id)
            phrases = _resolution_phrases(resolution)
            if not wanted & set(phrases):
                continue
            view = DP.path_view(vault, repository, goal.id)
            primaries: dict[str, tuple[str, str]] = {}
            alternates: dict[str, list[tuple[str, str]]] = {}
            for line in view.get("lines") or []:
                lo = str(line.get("learning_object_id") or "")
                section = line.get("section") or {}
                if section.get("extraction_id") and section.get("section_id"):
                    primaries[lo] = (str(section["extraction_id"]), str(section["section_id"]))
                for alternate in line.get("alternates") or []:
                    if alternate.get("extraction_id") and alternate.get("section_id"):
                        alternates.setdefault(lo, []).append(
                            (str(alternate["extraction_id"]), str(alternate["section_id"])))
            return {"goal_id": goal.id, "sentence": goal.intent_sentence or goal.title, "phrases": phrases,
                    "status": view.get("status"), "primaries": primaries, "alternates": alternates}
    except Exception:  # noqa: BLE001 - a deliverable that can't be read leaves the brief without it
        return None
    return None


def _resolution_phrases(resolution: Any) -> dict[str, str]:
    """The resolution receipt's phrase per LO (C0b's ``learning_objects`` rows)."""

    out: dict[str, str] = {}
    for row in (resolution or {}).get("learning_objects") or ():
        if isinstance(row, Mapping) and row.get("learning_object_id"):
            out[str(row["learning_object_id"])] = str(row.get("phrase") or "")
    return out


def your_notes(vault: Any, repository: Any, learning_object_ids: Sequence[str]) -> dict[str, list[dict[str, Any]]]:
    """Per LO, headers of the learner's linked notes (title, heading, date, one line): their own voice (C4)."""

    try:
        from learnloop.db.stores import learner_notes as notes_store
        from learnloop.source_retrieval import note_links as NL

        if not NL.enabled(vault) or not NL.available(vault):
            return {}
        with repository.connection() as connection:
            rows = notes_store.links(connection, learning_object_ids=set(learning_object_ids))
        out: dict[str, list[dict[str, Any]]] = {}
        for view in NL.effective(repository, rows):
            lo = str(view.get("learning_object_id") or "")
            if lo not in set(learning_object_ids):
                continue
            note = view["note"]
            first = next((line.strip() for line in str(note.get("text") or "").splitlines() if line.strip()), "")
            out.setdefault(lo, []).append({
                "id": f"n:{view['link_id']}", "title": note.get("title"), "heading": note.get("heading"),
                "date": note.get("date_label"), "line": first[:STEM_CHARS],
                "voice": "the learner's own note (what they think; not a source)"})
        return out
    except Exception:  # noqa: BLE001 - notes that can't be read are left out
        return {}


# --- the brief -------------------------------------------------------------------------


def build_brief(vault: Any, repository: Any, *, learning_object_ids: Sequence[str], how: Mapping[str, str],
                goal_text: str, selection: Mapping[str, Any] | None, driver: str, lesson_id: str | None,
                constraints: Mapping[str, Any]) -> tuple[dict[str, Any], SourceBook]:
    """``(LessonBriefV1, the delivered passages)``."""

    from learnloop.learner.lesson_weight import read_hedges
    from learnloop.learner_protection import withheld_items
    from learnloop.source_retrieval.reading_paths import lo_statuses
    from learnloop.source_retrieval.section_coverage import Library

    config = vault.config.teacher
    withheld = withheld_items(vault, repository)
    nodes_spec = prerequisite_nodes(vault, learning_object_ids, int(config.brief.depth))
    all_los = [lo for lo, _kind, _depth in nodes_spec]
    statuses = lo_statuses(vault, repository, all_los)
    with repository.connection() as connection:
        hedges = read_hedges(connection)
    history = _history(vault, repository, all_los, withheld, hedges)
    attempted = {row["practice_item_id"] for row in _attempt_rows(repository, all_los)}
    deliverable = deliverable_for(vault, repository, learning_object_ids) if c4_active(vault) else None
    notes = your_notes(vault, repository, all_los) if c4_active(vault) else {}
    nodes = []
    for lo, kind, depth in nodes_spec:
        learning_object = vault.learning_objects[lo]
        prediction = lo_prediction(vault, repository, lo)
        cold = [row for row in _attempt_rows(repository, [lo]) if _cold(row)]
        last_cold = ({"result": _result_words(cold[-1]), "at": cold[-1]["created_at"]} if cold else None)
        status = statuses.get(lo)
        node = {
            "id": lo, "kind": kind, "depth": depth, "title": learning_object.title,
            "statement": learning_object.summary,
            "label": status.status if status is not None else "new",
            "prediction": {k: prediction[k] for k in ("source", "p", "interval", "words") if k in prediction},
            "adaptive_difficulty": ad_readiness(vault, repository, lo),
            "retrievability": _retrievability(repository, vault, lo),
            "last_cold": last_cold,
            "misconceptions": _misconceptions(repository, lo),
            "probes": _probe_headers(vault, repository, lo, withheld, attempted, prediction),
        }
        if notes.get(lo):
            node["your_notes"] = notes[lo]
        nodes.append(node)
    library = Library(vault, repository)
    book = SourceBook()
    if deliverable is not None and deliverable.get("primaries"):
        primaries = [deliverable["primaries"][lo] for lo in all_los if lo in deliverable["primaries"]]
        alternates = [ref for lo in all_los for ref in deliverable["alternates"].get(lo, []) if ref not in primaries]
        if selection:
            selected = (str(selection["extraction_id"]), str(selection["section_id"]))
            primaries = [selected, *[ref for ref in primaries if ref != selected]]
    else:
        primaries = _section_refs(vault, library, learning_object_ids, selection)
        alternates = []
    sources = _render_sources(library, book, list(dict.fromkeys(primaries)), list(dict.fromkeys(alternates)),
                              int(config.context.sources_tokens))
    goal: dict[str, Any] = {"text": goal_text, "learning_object_ids": list(learning_object_ids),
                            "resolved_by": dict(how)}
    if deliverable is not None:
        goal["deliverable"] = {"goal_id": deliverable["goal_id"], "sentence": deliverable["sentence"],
                               "phrases": {lo: deliverable["phrases"].get(lo) for lo in learning_object_ids
                                           if lo in deliverable["phrases"]}}
        goal["resolved_by"] = {lo: (f"your deliverable: {deliverable['phrases'][lo]}" if deliverable["phrases"].get(lo)
                                    else how.get(lo)) for lo in learning_object_ids}
    brief = {
        "version": BRIEF_VERSION,
        "goal": goal,
        "nodes": nodes,
        "history": history,
        "last_lessons": _last_lessons(repository, all_los, lesson_id),
        "sources": sources,
        "constraints": {"driver": driver, **dict(constraints)},
        "doctrine": doctrine_identity(),
    }
    return brief, book


__all__ = [
    "LessonRefused",
    "SourceBook",
    "ad_readiness",
    "build_brief",
    "c4_active",
    "deliverable_for",
    "downstream_learning_objects",
    "lo_prediction",
    "prerequisite_nodes",
    "resolve_goal",
    "your_notes",
]
