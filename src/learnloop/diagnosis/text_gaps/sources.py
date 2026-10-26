"""The learner-text sources, each read into one :class:`LearnerText`.

* **Tutor question** (``question_events``): the question, read by the tutor in
  the call that answered it (``source_context.learner_gap``).
* **Diagnosis** (``attempt_diagnoses``): the wrong answer, read by the
  diagnoser. Its causes are read deterministically (no diagnoser prompt
  change): validated ``prerequisite_gap_hypotheses`` -> prerequisite; a
  learner-state event with a ``misconception_statement`` -> misconception;
  ``transient_execution`` -> slip; otherwise none.
* **Reader formative answer** (RW1b, ``reader_authored_questions``): a
  next-step, why-step or assumption answer the learner wrote while reading
  and marked *partly* or *no* against the expected answer; read by the
  stuck-text reader with its own task (:data:`~.contract.READER_FORMATIVE_TASK`).
* **Workbench text** (RW2b, ``workbench_text``): text the learner wrote while
  working a problem in steps: a stuck step (its newest version, a
  ``workbench_steps`` row), a "this doesn't connect" reply with text and an
  answer to a discriminating question (the workbench's ``help_assists``
  rows); read by the gap reader with the item, the step, the anchors and the
  role (``stuck`` | ``hint_feedback`` | ``discriminate_answer``). Read by SQL
  here, never through the workbench's modules (the import contract
  ``evidence-never-reads-the-workbench``); the kind is non-serving.
* **Stuck answer**: a non-empty answer written under "I'm stuck" (the
  stuck prompt, mvp-0.13). ``learnloop.attempts.stuck`` owns the marker
  (``practice_attempts.declared_stuck``) and the read-only views: one stuck
  answer by its id (``stuck_answer``) and every stuck answer
  (``stuck_answers``, the backlog). This module reads them through
  :class:`StuckTextSource`, whose default adapter is that module. An empty
  "I'm stuck" (a deterministic zero, no model call) carries no learner text.
  Its reading is one call to the stuck-text reader.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
import json
from typing import Any, Protocol

from learnloop.attempts import stuck as stuck_module
from learnloop.content.sources.exam_material import spans_withheld
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.figure_admission import figure_home_keys
from learnloop.figure_admission import figures_enabled as _figures_switch
from learnloop.diagnosis.text_gaps.contract import GapReading, LearnerText
from learnloop.reader.reader_progression import learning_objects_for_span
from learnloop.substrate.canonical_projection import held_for_review_attempts
from learnloop.vault.models import LoadedVault, learning_object_facet_union
from learnloop.vault.required_method import presented_prompt

#: Diagnoses whose causes this pipeline reads (live, applied).
_READABLE_DIAGNOSIS = ("completed",)


# -- tutor questions ---------------------------------------------------------------------


def _item_subject(vault: LoadedVault, item: Any) -> str | None:
    subjects = vault.subjects_for_item(item) if item is not None else []
    return subjects[0] if subjects else None


def tutor_question_text(vault: LoadedVault, repository: Repository, event_id: str) -> LearnerText | None:
    """An answered tutor question; None when there is nothing to read."""

    event = repository.question_event(event_id)
    if event is None or event.get("answer_status") != "answered":
        return None
    source_context = event.get("source_context") or {}
    if isinstance(source_context, str):
        try:
            source_context = json.loads(source_context)
        except ValueError:
            source_context = {}
    item = vault.practice_items.get(str(event.get("practice_item_id") or "")) if event.get("practice_item_id") else None
    anchors: list[str] = []
    subject: str | None = None
    context: dict[str, Any] = {"surface": event.get("context")}
    if item is not None:
        anchors = [item.learning_object_id]
        subject = _item_subject(vault, item)
        context["item_prompt"] = presented_prompt(item.prompt, item.required_method)
    elif event.get("context") == "library":
        note = vault.notes.get(str(event.get("note_id") or ""))
        if note is not None:
            anchors = sorted(lo for lo in note.related_los if lo in vault.learning_objects)
            subject = note.subjects[0] if note.subjects else None
            context["note"] = getattr(note, "title", None) or note.id
    elif event.get("context") == "reader":
        anchors = sorted(
            str(lo) for lo in (source_context.get("candidate_learning_object_ids") or [])
            if str(lo) in vault.learning_objects
        )
    if subject is None and anchors:
        subjects = {s for lo in anchors for s in vault.learning_objects[lo].subjects[:1]}
        subject = next(iter(subjects)) if len(subjects) == 1 else None
    titles = [vault.learning_objects[lo].title for lo in anchors if lo in vault.learning_objects]
    if titles:
        context["learning_objects"] = titles
    raw = source_context.get("learner_gap")
    reading = None
    if isinstance(raw, Mapping):
        reading = GapReading.from_gap(
            raw, judge="llm", judge_model=str(raw.get("model") or event.get("provider") or "unknown"),
            prompt_version=str(raw.get("prompt_version") or ""),
        )
    return LearnerText(
        source_kind="tutor_question",
        source_id=str(event["id"]),
        text=str(event.get("question_md") or ""),
        context_judge="tutor",
        created_at=str(event.get("created_at") or ""),
        subject_id=subject,
        anchor_learning_object_ids=tuple(anchors),
        practice_item_id=item.id if item is not None else None,
        attempt_id=event.get("attempt_id"),
        question_event_id=str(event["id"]),
        reading=reading,
        context=context,
    )


# -- diagnoses -------------------------------------------------------------------------------


def _diagnosis_row(repository: Repository, diagnosis_id: str) -> dict[str, Any] | None:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        cursor = connection.execute("SELECT * FROM attempt_diagnoses WHERE id = ?", (diagnosis_id,))
        names = [column[0] for column in cursor.description]
        row = cursor.fetchone()
    return dict(zip(names, row, strict=True)) if row is not None else None


def resolve_prerequisite_ref(vault: LoadedVault, ref: str, anchor: str | None) -> str | None:
    """A diagnoser's validated prerequisite ref as one LO id (a facet resolves
    only when exactly one of the anchor's declared prerequisite LOs owns it)."""

    if ref in vault.learning_objects:
        return ref
    if anchor is None:
        return None
    from learnloop.placement.state import prerequisite_learning_objects

    facet = vault.canonical_facet_id(ref)
    owners = []
    for lo_id in sorted(prerequisite_learning_objects(vault, anchor)):
        learning_object = vault.learning_objects.get(lo_id)
        if learning_object is None:
            continue
        facets = {vault.canonical_facet_id(f) for f in learning_object_facet_union(learning_object)}
        facets |= {
            vault.canonical_facet_id(str(f))
            for item in vault.practice_items.values() if item.learning_object_id == lo_id
            for f in item.evidence_facets
        }
        if facet in facets:
            owners.append(lo_id)
    return owners[0] if len(owners) == 1 else None


def reading_from_diagnosis(
    vault: LoadedVault, proposal: Mapping[str, Any], *, anchor: str | None, model: str | None,
    prompt_version: str | None,
) -> GapReading:
    """The diagnoser's causes as a gap reading (deterministic; no call)."""

    refs = [
        resolved
        for gap in proposal.get("prerequisite_gap_hypotheses") or []
        if (resolved := resolve_prerequisite_ref(vault, str(gap.get("prerequisite_ref") or ""), anchor))
    ]
    events = [event for event in proposal.get("event_diagnoses") or [] if isinstance(event, Mapping)]
    beliefs = [
        event for event in events
        if event.get("causal_class") == "learner_state" and str(event.get("misconception_statement") or "").strip()
    ]
    slips = [event for event in events if event.get("causal_class") == "transient_execution"]
    if refs:
        kind = "prerequisite"
    elif beliefs:
        kind = "misconception"
    elif slips:
        kind = "slip"
    else:
        kind = "none"
    first_ref = refs[0] if refs else None
    learning_object = vault.learning_objects.get(first_ref) if first_ref else None
    belief = beliefs[0] if beliefs else None
    return GapReading(
        kind=kind,
        prerequisite_name=learning_object.title if learning_object is not None else None,
        prerequisite_line=learning_object.summary if learning_object is not None else None,
        belief_statement=" ".join(str(belief.get("misconception_statement")).split()) if belief else None,
        judge="diagnoser",
        judge_model=str(model or "unknown"),
        prompt_version=str(prompt_version or ""),
        prerequisite_refs=tuple(dict.fromkeys(refs)),
        registry_match=dict(belief.get("registry_match") or {}) if belief else None,
    )


def attempt_grade_held(repository: Repository, attempt_id: str) -> bool:
    """Is the attempt's current grade held for review (mvp-0.17)?

    Read through the one ledger helper every reader shares
    (``substrate.canonical_projection.held_for_review_attempts``).
    """

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return bool(held_for_review_attempts(connection, (attempt_id,)))


def diagnosis_text(vault: LoadedVault, repository: Repository, diagnosis_id: str) -> LearnerText | None:
    """A completed live diagnosis of a wrong answer; None otherwise.

    A grade the proofs route check holds for review (mvp-0.17) is no wrong
    answer: nothing validated it, so its diagnosis is not read (whenever the
    hold began).
    """

    row = _diagnosis_row(repository, diagnosis_id)
    if row is None or row.get("mode") != "live" or row.get("status") not in _READABLE_DIAGNOSIS:
        return None
    attempt = repository.fetch_practice_attempt(str(row["attempt_id"]))
    if attempt is None:
        return None
    if attempt_grade_held(repository, str(attempt["id"])):
        return None
    try:
        proposal = json.loads(row.get("proposal_json") or "{}")
    except ValueError:
        return None
    item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
    anchor = str(attempt.get("learning_object_id") or "") or None
    subject = str(attempt.get("subject") or "") or _item_subject(vault, item)
    reading = reading_from_diagnosis(
        vault, proposal, anchor=anchor, model=row.get("model"), prompt_version=row.get("diagnosis_prompt_version"),
    )
    divergences = [
        str(event.get("first_divergence_quote")) for event in proposal.get("event_diagnoses") or []
        if isinstance(event, Mapping) and event.get("first_divergence_quote")
    ]
    context: dict[str, Any] = {"surface": "wrong_answer"}
    if item is not None:
        context["item_prompt"] = presented_prompt(item.prompt, item.required_method)
    if anchor and anchor in vault.learning_objects:
        context["learning_objects"] = [vault.learning_objects[anchor].title]
    if divergences:
        context["first_divergence"] = divergences[:3]
    return LearnerText(
        source_kind="diagnosis",
        source_id=str(row["id"]),
        text=str(attempt.get("learner_answer_md") or ""),
        context_judge="diagnoser",
        created_at=str(row.get("created_at") or ""),
        subject_id=subject,
        anchor_learning_object_ids=(anchor,) if anchor else (),
        practice_item_id=item.id if item is not None else None,
        attempt_id=str(attempt["id"]),
        reading=reading,
        context=context,
    )


# -- stuck answers --------------------------------------------------------------------------


@dataclass(frozen=True)
class StuckText:
    """One non-empty stuck answer (the stuck-prompt stage's view)."""

    attempt_id: str
    practice_item_id: str
    learning_object_id: str
    subject_id: str
    text: str
    created_at: str
    confusion_quote: str = ""


class StuckTextSource(Protocol):
    """Where stuck answers come from (the stuck-prompt stage's read-only view).

    A source may also offer ``stuck_text(connection, attempt_id)``: one
    attempt's stuck text or None, without scanning every stuck answer (what
    queueing at attempt recording asks, F8). :func:`stuck_text_for` falls
    back to filtering :meth:`stuck_texts`.
    """

    def stuck_texts(self, connection: Any) -> Sequence[StuckText]: ...


class StuckAnswersAdapter:
    """The stuck prompt's own views (``learnloop.attempts.stuck``).

    :meth:`stuck_text` reads one attempt by its id through the module's
    ``stuck_answer(connection, attempt_id)`` (the attempt, its current
    ``stuck_reading`` verdict and its latest blind record: the reading
    ``stuck_answers`` would give it), never a scan of every stuck answer, so
    queueing at attempt recording stays O(1) per answer (Codex review F8,
    re-review F4). :meth:`stuck_texts` reads every stuck answer
    (``stuck_answers``), for the backlog. Rows without text (an empty
    "I'm stuck") are dropped: there is no learner text to read.
    """

    def stuck_text(self, connection: Any, attempt_id: str) -> StuckText | None:
        row = stuck_module.stuck_answer(connection, attempt_id)
        rows = self._rows([row] if row else [])
        return rows[0] if rows else None

    def stuck_texts(self, connection: Any) -> Sequence[StuckText]:
        return self._rows(stuck_module.stuck_answers(connection))

    @staticmethod
    def _rows(rows: Any) -> list[StuckText]:
        out = []
        for row in rows:
            if not row.get("has_text") or not str(row.get("learner_answer_md") or "").strip():
                continue
            reading = row.get("reading") or {}
            out.append(StuckText(
                attempt_id=str(row["attempt_id"]),
                practice_item_id=str(row.get("practice_item_id") or ""),
                learning_object_id=str(row.get("learning_object_id") or ""),
                subject_id=str(row.get("subject_id") or "default"),
                text=str(row["learner_answer_md"]),
                created_at=str(row.get("created_at") or ""),
                confusion_quote=str(reading.get("confusion_quote") or "") if isinstance(reading, Mapping) else "",
            ))
        return out


DEFAULT_STUCK_SOURCE: StuckTextSource = StuckAnswersAdapter()


def stuck_texts(repository: Repository, source: StuckTextSource | None = None) -> list[StuckText]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return list((source or DEFAULT_STUCK_SOURCE).stuck_texts(connection))


def stuck_text_for(
    repository: Repository, attempt_id: str, source: StuckTextSource | None = None,
) -> StuckText | None:
    """One attempt's non-empty stuck text, or None."""

    source = source or DEFAULT_STUCK_SOURCE
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        lookup = getattr(source, "stuck_text", None)
        if lookup is not None:
            return lookup(connection, attempt_id)
        return next((row for row in source.stuck_texts(connection) if row.attempt_id == attempt_id), None)


def stuck_answer_text(
    vault: LoadedVault, repository: Repository, attempt_id: str, source: StuckTextSource | None = None,
) -> LearnerText | None:
    found = stuck_text_for(repository, attempt_id, source)
    if found is None:
        return None
    item = vault.practice_items.get(found.practice_item_id)
    context: dict[str, Any] = {"surface": "stuck_answer"}
    if item is not None:
        context["item_prompt"] = presented_prompt(item.prompt, item.required_method)
    if found.learning_object_id in vault.learning_objects:
        context["learning_objects"] = [vault.learning_objects[found.learning_object_id].title]
    if found.confusion_quote:
        context["confusion_quote"] = found.confusion_quote
    return LearnerText(
        source_kind="stuck_answer",
        source_id=found.attempt_id,
        text=found.text,
        context_judge="gap_reader",
        created_at=found.created_at,
        subject_id=found.subject_id or _item_subject(vault, item),
        anchor_learning_object_ids=(found.learning_object_id,) if found.learning_object_id else (),
        practice_item_id=found.practice_item_id or None,
        attempt_id=found.attempt_id,
        reading=None,
        context=context,
    )


# -- reader formative answers (RW1b) ---------------------------------------------------------

#: The active-reading styles whose missed answer is read (spec_reader_workbench_v1 §4.2).
FORMATIVE_STYLES = ("next_step", "why_step", "assumptions")
MISSED_SELF_CHECKS = ("partly", "no")
#: Bounds on what the reader is shown besides the answer (prompt size only).
FORMATIVE_PASSAGE_CHARS = 2_000
FORMATIVE_EXPECTED_CHARS = 2_000


#: Reader RW5a: a figure prediction's id (``figure_predictions``). It shares
#: the ``reader_formative`` source kind with RW1b's answers, told apart by
#: this prefix (the figure service writes it).
FIGURE_PREDICTION_PREFIX = "fpr_"
#: A missed prediction's "what changed?" written after the prediction's own
#: reading started: its own text, ``<prediction id>`` + this suffix, read
#: with the answer; the earlier reading is kept (Codex review F5).
FIGURE_EXPLANATION_SUFFIX = ":explained"
#: The words of a direction prediction's answers (the figure service's).
_DIRECTION_WORDS = {"rises": "it rises", "falls": "it falls", "same": "it stays the same"}


def is_figure_prediction(source_id: str) -> bool:
    return str(source_id or "").startswith(FIGURE_PREDICTION_PREFIX)


def figure_prediction_id(source_id: str) -> tuple[str, bool]:
    """``(prediction id, whether the source is its later explanation)``."""

    source_id = str(source_id or "")
    if source_id.endswith(FIGURE_EXPLANATION_SUFFIX):
        return source_id[: -len(FIGURE_EXPLANATION_SUFFIX)], True
    return source_id, False


def figure_prediction_row(repository: Repository, source_id: str) -> dict[str, Any] | None:
    """A missed figure prediction with an answer, with its figure, or None
    (for an explanation source, also None until the explanation is written)."""

    prediction_id, explained = figure_prediction_id(source_id)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN ('figure_predictions', 'interactive_figures')")}
        if tables != {"figure_predictions", "interactive_figures"}:
            return None
        row = connection.execute(
            "SELECT p.id, p.figure_id, p.extraction_id, p.prediction_index, p.learner_answer, p.observed_json, "
            "p.matched, p.explanation_text, p.created_at, f.spec_json, f.span_ids_json, f.region_json, "
            "f.input_span_ids_json, f.asset_id, f.input_span_keys_json "
            "FROM figure_predictions AS p JOIN interactive_figures AS f ON f.id = p.figure_id WHERE p.id = ?",
            (prediction_id,)).fetchone()
    if row is None or int(row[6]) != 0 or not str(row[4] or "").strip():
        return None
    if explained and not str(row[7] or "").strip():
        return None
    keys = ("id", "figure_id", "extraction_id", "prediction_index", "learner_answer", "observed_json", "matched",
            "explanation_text", "created_at", "spec_json", "span_ids_json", "region_json", "input_span_ids_json",
            "asset_id", "input_span_keys_json")
    return {**dict(zip(keys, row)), "source_id": str(source_id)}


def figure_input_manifest(row: Mapping[str, Any]) -> list[str] | None:
    """Every span a figure was built from and its author was sent, or None
    when the stored lists are unreadable (a caller fails closed): the
    selection, the region's block, the crop's block and ``input_span_ids``
    (the paragraphs around it). The figure service rechecks the same list
    (``figures.service._figure_spans``; Codex review F1)."""

    try:
        spans = [str(span) for span in json.loads(row.get("span_ids_json") or "[]")]
        region = json.loads(row.get("region_json") or "null") or {}
        manifest = json.loads(row.get("input_span_ids_json") or "[]")
        if not isinstance(region, dict) or not isinstance(manifest, list):
            return None
        if region.get("span_id"):
            spans.append(str(region["span_id"]))
        if row.get("asset_id"):
            spans.append(str(row["asset_id"]))
        spans += [str(span) for span in manifest]
    except (TypeError, ValueError):
        return None
    return list(dict.fromkeys(spans))


def figure_input_keys(row: Mapping[str, Any]) -> dict[str, list[str]] | None:
    """Reader RW5d: the retrieved passages a figure was built from, in any
    source (``input_span_keys_json``), by extraction; None when unreadable
    (a caller fails closed)."""

    try:
        keys = json.loads(row.get("input_span_keys_json") or "[]")
        if not isinstance(keys, list):
            return None
        grouped: dict[str, list[str]] = {}
        for key in keys:
            if not isinstance(key, list) or len(key) != 2:
                return None
            grouped.setdefault(str(key[0]), []).append(str(key[1]))
    except (TypeError, ValueError):
        return None
    return grouped


class SourceWithheld(Exception):
    """A learner text whose context is held-out material now: nothing of it
    is built or sent, and its job is skipped (not retried) with this reason."""


def figure_prediction_withheld(vault: LoadedVault, repository: Repository, row: Mapping[str, Any]) -> str | None:
    """Why a missed prediction's text may not be read now, or None: any span
    of its figure's complete input manifest is held out (the figure service's
    one predicate, ``exam_material.spans_withheld``), or the manifest is
    unreadable (fails closed). Fix round 2, F1."""

    manifest = figure_input_manifest(row)
    keys = figure_input_keys(row)
    if manifest is None or keys is None:
        return "the figure's input spans are unreadable"
    message = spans_withheld(vault, repository, str(row["extraction_id"]), manifest) if row.get("extraction_id") else None
    for extraction_id, spans in keys.items():
        message = message or spans_withheld(vault, repository, extraction_id, spans)
    if message is None and row.get("figure_id"):
        # Reader RW5d (Codex review F4): a figure with no passage is also
        # checked at every place it lands (the figure service's same rule).
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            homes = figure_home_keys(connection, str(row["figure_id"]))
        if homes is None:
            return "the figure's place in the book is unreadable"
        for extraction_id, span_id in homes:
            message = message or spans_withheld(vault, repository, extraction_id, [span_id])
    return message


def figure_grounding_keys(repository: Repository, row: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Reader RW5d (Codex review F5): the passages a figure with no passage of
    its own was grounded in, ``(extraction_id, span_id)`` across sources: the
    kept ones its request recorded (the verified retrieval's picks, or a tutor
    answer's cited spans), else every retrieved key it was sent. Empty for an
    anchored figure (its selection is its passage)."""

    if figure_prediction_spans(row):
        return []
    kept: list[tuple[str, str]] = []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'figure_requests'"
                              ).fetchone():
            found = connection.execute(
                "SELECT r.grounding_manifest_json FROM interactive_figures AS f JOIN figure_requests AS r "
                "ON r.id = f.request_id WHERE f.id = ?", (str(row.get("figure_id") or ""),)).fetchone()
            try:
                manifest = json.loads(found[0] or "{}") if found else {}
                kept = [(str(key[0]), str(key[1])) for key in (manifest.get("kept") or ())
                        if isinstance(key, list) and len(key) == 2 and key[0] and key[1]]
            except (TypeError, ValueError, AttributeError):
                kept = []
    if not kept:
        grouped = figure_input_keys(row) or {}
        kept = [(extraction_id, span) for extraction_id, spans in grouped.items() for span in spans]
    return list(dict.fromkeys(kept))


def missed_prediction_ids(repository: Repository) -> list[str]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'figure_predictions'"
                                  ).fetchone():
            return []
        return [str(row[0]) for row in connection.execute(
            "SELECT id FROM figure_predictions WHERE matched = 0 AND TRIM(learner_answer) != '' ORDER BY created_at, id")]


def explained_predictions(repository: Repository) -> list[tuple[str, str]]:
    """``(prediction id, its "what changed?" text)`` for every missed
    prediction with an answer and an explanation, oldest first: what the
    backlog sweep reconciles (fix round 2, F5)."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'figure_predictions'"
                                  ).fetchone():
            return []
        return [(str(row[0]), str(row[1]).strip()) for row in connection.execute(
            "SELECT id, explanation_text FROM figure_predictions WHERE matched = 0 AND TRIM(learner_answer) != '' "
            "AND TRIM(COALESCE(explanation_text, '')) != '' ORDER BY created_at, id")]


def figure_prediction_spans(row: Mapping[str, Any]) -> list[str]:
    try:
        spans = [str(span) for span in json.loads(row.get("span_ids_json") or "[]")]
    except (TypeError, ValueError):
        spans = []
    try:
        region = json.loads(row.get("region_json") or "null") or {}
    except (TypeError, ValueError):
        region = {}
    if isinstance(region, dict) and region.get("span_id"):
        spans.append(str(region["span_id"]))
    return list(dict.fromkeys(spans))


def figure_prediction_text(vault: LoadedVault, repository: Repository, prediction_id: str) -> LearnerText | None:
    """RW5a: a missed figure prediction, read by the gap reader.

    The text is the learner's answer and, when they wrote one, their "what
    changed?" line; the context is the prediction's question, the passage the
    figure was built from, and what the figure showed (computed by code, not
    the book's words). The LOs are the passage's provenance-linked ones.

    Before anything is built, the figure's complete input manifest is
    checked against held-out material now: a figure any of whose spans is
    held out raises :class:`SourceWithheld`, so neither the passage, the
    question nor the readout reaches the gap reader (fix round 2, F1)."""

    row = figure_prediction_row(repository, prediction_id)
    if row is None:
        return None
    withheld = figure_prediction_withheld(vault, repository, row)
    if withheld is not None:
        raise SourceWithheld(withheld)
    try:
        spec = json.loads(row.get("spec_json") or "{}")
        prediction = (spec.get("predictions") or [])[int(row["prediction_index"])]
        observed = json.loads(row.get("observed_json") or "{}")
    except (TypeError, ValueError, IndexError, KeyError):
        return None
    answer = str(row["learner_answer"])
    words = _DIRECTION_WORDS.get(answer, answer)
    explanation = str(row.get("explanation_text") or "").strip()
    text = words if not explanation else f"{words}. What changed, in my words: {explanation}"
    extraction_id = str(row["extraction_id"])
    spans = figure_prediction_spans(row)
    # The passages the figure was built from: its selection, else (Reader RW5d,
    # Codex review F5) the passages its goal was grounded in, in any source.
    keys = [(extraction_id, span) for span in spans] or figure_grounding_keys(repository, row)
    los: list[str] = []
    for key_extraction, span_id in keys:
        for lo_id in learning_objects_for_span(vault, repository, extraction_id=key_extraction, span_id=span_id):
            if lo_id in vault.learning_objects and lo_id not in los:
                los.append(lo_id)
    los.sort()
    subjects = {s for lo in los for s in vault.learning_objects[lo].subjects[:1]}
    correct = observed.get("answer")
    shown = _DIRECTION_WORDS.get(str(correct), str(correct))
    context: dict[str, Any] = {
        "surface": "reader_formative",
        "style": "figure_prediction",
        "question": str(prediction.get("prompt") or ""),
        "passage": _key_texts(repository, keys),
        "expected_answer": (f"{shown} (the figure's readout went from {observed.get('before')} to "
                            f"{observed.get('after')})")[:FORMATIVE_EXPECTED_CHARS],
        "expected_answer_from": "LearnLoop's figure (computed, not the book's words)",
        "self_check": "missed",
    }
    titles = [vault.learning_objects[lo].title for lo in los]
    if titles:
        context["learning_objects"] = titles
    return LearnerText(
        source_kind="reader_formative",
        source_id=str(row["source_id"]),
        text=text,
        context_judge="gap_reader",
        created_at=str(row.get("created_at") or ""),
        subject_id=next(iter(subjects)) if len(subjects) == 1 else None,
        anchor_learning_object_ids=tuple(los),
        reading=None,
        context=context,
        # Whether this reading reads the "what changed?" (fix round 3): the
        # backlog reconciles a later explanation by this marker, recorded on
        # the job, never by searching the text.
        markers={"explanation_read": bool(explanation)},
    )


def formative_row(repository: Repository, question_id: str) -> dict[str, Any] | None:
    """A missed formative answer (``reader_authored_questions``), or None.
    A figure prediction id (RW5a) reads :func:`figure_prediction_row`.

    Selection-scoped, in a next-step, why-step or assumption style, marked
    partly or no by the learner, with an answer they wrote, and not added to
    practice since (an escalated question's expected answer is an item's key
    now, which no learner text carries)."""

    if is_figure_prediction(question_id):
        return figure_prediction_row(repository, question_id)
    row = repository.get_reader_authored_question(question_id)
    if row is None or row.get("scope_kind") != "selection" or row.get("question_style") not in FORMATIVE_STYLES:
        return None
    if row.get("self_check") not in MISSED_SELF_CHECKS or row.get("status") != "answered":
        return None
    if not str(row.get("response_md") or "").strip():
        return None
    return row


def figures_enabled(vault: LoadedVault) -> bool:
    """RW5a's kill switch, ``figures.enabled``: off, no figure prediction or
    explanation is discovered, reconciled, queued or read. The one predicate
    (:func:`learnloop.figure_admission.figures_enabled`), one default."""

    return _figures_switch(vault)


def missed_formative_ids(repository: Repository, *, figures: bool = True) -> list[str]:
    """Every missed formative answer (:func:`formative_row`'s rule), oldest
    first, then, with ``figures`` (:func:`figures_enabled`), every missed
    figure prediction (RW5a): what the backlog sweep may queue."""

    return _missed_answer_ids(repository) + (missed_prediction_ids(repository) if figures else [])


def _missed_answer_ids(repository: Repository) -> list[str]:
    with repository.connection() as connection:
        if "scope_kind" not in {row[1] for row in connection.execute("PRAGMA table_info(reader_authored_questions)")}:
            return []
        styles, checks = tuple(FORMATIVE_STYLES), tuple(MISSED_SELF_CHECKS)
        rows = connection.execute(
            f"SELECT id FROM reader_authored_questions WHERE scope_kind = 'selection' "
            f"AND question_style IN ({','.join('?' for _ in styles)}) "
            f"AND self_check IN ({','.join('?' for _ in checks)}) AND status = 'answered' "
            "AND TRIM(COALESCE(response_md, '')) != '' ORDER BY created_at, id",
            (*styles, *checks),
        ).fetchall()
    return [str(row[0]) for row in rows]


def _key_texts(repository: Repository, keys: Sequence[tuple[str, str]]) -> str:
    """The passages' texts in order, across sources (one source: :func:`_span_texts`)."""

    by_extraction: dict[str, list[str]] = {}
    for extraction_id, span_id in keys:
        by_extraction.setdefault(extraction_id, []).append(span_id)
    parts = [_span_texts(repository, extraction_id, spans) for extraction_id, spans in by_extraction.items()]
    return " ".join(part for part in parts if part)[:FORMATIVE_PASSAGE_CHARS]


def _span_texts(repository: Repository, extraction_id: str, span_ids: Sequence[str]) -> str:
    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        return ""
    by_span = {block.span_id: block for block in ir.blocks}
    parts = [" ".join((by_span[span].text or "").split()) for span in span_ids if span in by_span]
    return " ".join(part for part in parts if part)[:FORMATIVE_PASSAGE_CHARS]


def reader_formative_text(vault: LoadedVault, repository: Repository, question_id: str) -> LearnerText | None:
    """A missed next-step, why-step or assumption answer, read by the gap reader.

    The text is the learner's own answer; the context is the question, the
    selected passage and the expected answer with whose words it is (the
    book's or LearnLoop's model's). The LOs are the passage's provenance-linked
    ones, and the subject theirs when they share one."""

    if is_figure_prediction(question_id):
        # Figures off: no figure-derived text is built (fix round 4; the job
        # runner defers such a job before it gets here).
        return figure_prediction_text(vault, repository, question_id) if figures_enabled(vault) else None
    row = formative_row(repository, question_id)
    if row is None:
        return None
    try:
        anchors = [str(span) for span in json.loads(row.get("anchor_span_ids_json") or "[]")]
    except (TypeError, ValueError):
        anchors = []
    extraction_id = str(row["extraction_id"])
    los: list[str] = []
    for span_id in anchors:
        for lo_id in learning_objects_for_span(vault, repository, extraction_id=extraction_id, span_id=span_id):
            if lo_id in vault.learning_objects and lo_id not in los:
                los.append(lo_id)
    los.sort()
    subjects = {s for lo in los for s in vault.learning_objects[lo].subjects[:1]}
    subject = next(iter(subjects)) if len(subjects) == 1 else None
    context: dict[str, Any] = {
        "surface": "reader_formative",
        "style": str(row["question_style"]),
        "question": str(row.get("question_md") or ""),
        "passage": _span_texts(repository, extraction_id, anchors),
        "expected_answer": str(row.get("expected_answer_md") or "")[:FORMATIVE_EXPECTED_CHARS],
        "expected_answer_from": "the book" if row.get("answer_basis") == "source" else "LearnLoop's model",
        "self_check": str(row["self_check"]),
    }
    titles = [vault.learning_objects[lo].title for lo in los]
    if titles:
        context["learning_objects"] = titles
    return LearnerText(
        source_kind="reader_formative",
        source_id=str(row["id"]),
        text=str(row["response_md"]),
        context_judge="gap_reader",
        created_at=str(row.get("updated_at") or row.get("answered_at") or ""),
        subject_id=subject,
        anchor_learning_object_ids=tuple(los),
        reading=None,
        context=context,
    )


#: Adaptive hints H2b: the two roles of a ``hint_feedback`` text (spec §9).
HINT_FEEDBACK_ROLES = ("hint_feedback", "discriminate_answer")
#: Bounds on what the reader is shown besides the text (prompt size only).
HINT_TEXT_CHARS = 2_000


def hint_feedback_row(repository: Repository, assist_id: str) -> dict[str, Any] | None:
    """A practice-screen ``help_assists`` row whose learner text is a
    ``hint_feedback`` source (spec §9), with its role, or None: a "doesn't
    connect" reply with text (``request = 'feedback'``, role
    ``hint_feedback``) or an answer to a discriminating question
    (``assist_kind = 'discriminate_answer'``, role ``discriminate_answer``).
    Outside the workbench only: the workbench's texts are ``workbench_text``."""

    with repository.connection() as connection:
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'help_assists'"
                              ).fetchone() is None:
            return None
        cursor = connection.execute("SELECT * FROM help_assists WHERE id = ?", (assist_id,))
        raw = cursor.fetchone()
        if raw is None:
            return None
        row = dict(zip([column[0] for column in cursor.description], raw))
    if row.get("surface") == "workbench" or not str(row.get("feedback_text") or "").strip():
        return None
    if row.get("assist_kind") == "discriminate_answer":
        row["role"] = "discriminate_answer"
    elif row.get("assist_kind") == "hint" and row.get("request") == "feedback":
        row["role"] = "hint_feedback"
    else:
        return None
    return row


def hint_feedback_ids(repository: Repository) -> list[str]:
    """Every ``help_assists`` row whose text is a ``hint_feedback`` source
    (:func:`hint_feedback_row`'s rule), oldest first: what the backlog sweep
    and the sidecar's start-up reconciliation may queue (H2b review F4: a row
    that committed while its job did not)."""

    with repository.connection() as connection:
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'help_assists'"
                              ).fetchone() is None:
            return []
        rows = connection.execute(
            "SELECT id FROM help_assists WHERE surface != 'workbench' "
            "AND TRIM(COALESCE(feedback_text, '')) != '' "
            "AND (assist_kind = 'discriminate_answer' OR (assist_kind = 'hint' AND request = 'feedback')) "
            "ORDER BY requested_at, id"
        ).fetchall()
    return [str(row[0]) for row in rows]


def _json_field(value: Any) -> dict[str, Any]:
    try:
        parsed = json.loads(value or "{}")
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _assist_text(repository: Repository, item: Any, assist_id: str | None) -> tuple[str, int | None]:
    """The text a learner replied to (a hint, or a discriminating question)
    and its level. Worked help (levels 4-5) is not shown to the reader: it
    can carry the item's solution, and a reader is never shown an answer key."""

    if not assist_id:
        return "", None
    with repository.connection() as connection:
        found = connection.execute("SELECT body_md, authored_index, level FROM help_assists WHERE id = ?",
                                   (assist_id,)).fetchone()
    if found is None:
        return "", None
    body, index, level = found[0], found[1], found[2]
    if level is not None and int(level) >= 4:
        return "", int(level)
    if body:
        return str(body)[:HINT_TEXT_CHARS], level
    if index is not None and item is not None and 0 <= int(index) < len(item.hints):
        return str(item.hints[int(index)])[:HINT_TEXT_CHARS], level
    return "", level


def hint_feedback_text(vault: LoadedVault, repository: Repository, assist_id: str) -> LearnerText | None:
    """Adaptive hints H2b: a "doesn't connect" reply's text or a
    discriminating answer, read by the gap reader (``hint_feedback``).

    The text is the learner's own; the context is the item's question, its
    LO, the role, and what the learner was answering (the hint replied to,
    with the shortcut, or the question asked), never the item's answer key or
    worked help. The item's LO anchors it and its subject grounds it; the
    gap row carries the item, so a gap named mid-attempt joins the next
    hint's rivals (``learnloop.hints.discriminating``)."""

    row = hint_feedback_row(repository, assist_id)
    if row is None:
        return None
    item = vault.practice_items.get(str(row.get("practice_item_id") or ""))
    if item is None:
        return None
    lo = vault.learning_objects.get(item.learning_object_id)
    context: dict[str, Any] = {"surface": "hint_feedback", "role": row["role"], "question": item.prompt}
    if lo is not None:
        context["learning_objects"] = [lo.title]
    if row["role"] == "hint_feedback":
        answered = _json_field(row.get("options_json")).get("answered_assist_id")
        hint, level = _assist_text(repository, item, answered)
        context["hint_replied_to"] = hint or ("worked help (not shown)" if level and level >= 4 else "")
        if row.get("feedback_shortcut"):
            context["shortcut"] = str(row["feedback_shortcut"])
    else:
        question_id = _json_field(row.get("placement_json")).get("question_assist_id")
        question, _level = _assist_text(repository, item, question_id)
        context["question_asked"] = question
    subject = item.subjects[0] if getattr(item, "subjects", None) else (
        lo.subjects[0] if lo is not None and lo.subjects else None)
    return LearnerText(
        source_kind="hint_feedback",
        source_id=str(row["id"]),
        text=str(row["feedback_text"]),
        context_judge="gap_reader",
        created_at=str(row.get("requested_at") or ""),
        subject_id=subject,
        anchor_learning_object_ids=(item.learning_object_id,) if item.learning_object_id else (),
        practice_item_id=item.id,
        attempt_id=row.get("attempt_id"),
        reading=None,
        context=context,
    )


#: Reader workbench RW2b: the three roles of a ``workbench_text`` (spec §5.6).
WORKBENCH_TEXT_ROLES = ("stuck", "hint_feedback", "discriminate_answer")


def _table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
                              ).fetchone() is not None


def workbench_text_row(repository: Repository, source_id: str) -> dict[str, Any] | None:
    """A workbench learner text with its role, or None: a stuck step's
    version (``workbench_steps``, role ``stuck``, not deleted, non-empty), or
    a workbench ``help_assists`` row with text (a reply, role
    ``hint_feedback``; an answer to a discriminating question, role
    ``discriminate_answer``)."""

    with repository.connection() as connection:
        if _table(connection, "help_assists"):
            cursor = connection.execute("SELECT * FROM help_assists WHERE id = ? AND surface = 'workbench'",
                                        (source_id,))
            raw = cursor.fetchone()
            if raw is not None:
                row = dict(zip([column[0] for column in cursor.description], raw))
                if not str(row.get("feedback_text") or "").strip():
                    return None
                if row.get("assist_kind") == "discriminate_answer":
                    row["role"] = "discriminate_answer"
                elif row.get("assist_kind") == "hint" and row.get("request") == "feedback":
                    row["role"] = "hint_feedback"
                else:
                    return None
                row["text"] = str(row["feedback_text"])
                row["created"] = str(row.get("requested_at") or "")
                return row
        if not _table(connection, "workbench_steps"):
            return None
        cursor = connection.execute(
            "SELECT steps.id, steps.session_id, steps.kind, steps.body_md, steps.deleted, steps.created_at, "
            "sessions.practice_item_id, sessions.attempt_id, sessions.extraction_id, sessions.span_ids_json "
            "FROM workbench_steps AS steps JOIN workbench_sessions AS sessions ON sessions.id = steps.session_id "
            "WHERE steps.id = ?", (source_id,))
        raw = cursor.fetchone()
        if raw is None:
            return None
        row = dict(zip([column[0] for column in cursor.description], raw))
    if row["kind"] != "stuck" or row["deleted"] or not str(row["body_md"] or "").strip():
        return None
    return {**row, "role": "stuck", "text": str(row["body_md"]), "created": str(row["created_at"] or ""),
            "workbench_session_id": row["session_id"]}


def workbench_text(vault: LoadedVault, repository: Repository, source_id: str) -> LearnerText | None:
    """Reader workbench RW2b: a workbench text read by the gap reader
    (``workbench_text``). The text is the learner's own; the context is the
    item's question, its LO, the role and, for a reply or an answer, what the
    learner was answering (never the answer key or worked help). The item's
    LO anchors it; the gap row carries the item, so a gap named mid-problem
    joins the next hint's rivals."""

    row = workbench_text_row(repository, source_id)
    if row is None:
        return None
    item = vault.practice_items.get(str(row.get("practice_item_id") or ""))
    if item is None:
        return None
    lo = vault.learning_objects.get(item.learning_object_id)
    context: dict[str, Any] = {"surface": "workbench", "role": row["role"], "question": item.prompt}
    if lo is not None:
        context["learning_objects"] = [lo.title]
    if row["role"] == "hint_feedback":
        answered = _json_field(row.get("options_json")).get("answered_assist_id")
        hint, level = _assist_text(repository, item, answered)
        context["hint_replied_to"] = hint or ("worked help (not shown)" if level and level >= 4 else "")
        if row.get("feedback_shortcut"):
            context["shortcut"] = str(row["feedback_shortcut"])
    elif row["role"] == "discriminate_answer":
        question_id = _json_field(row.get("placement_json")).get("question_assist_id")
        question, _level = _assist_text(repository, item, question_id)
        context["question_asked"] = question
    subject = item.subjects[0] if getattr(item, "subjects", None) else (
        lo.subjects[0] if lo is not None and lo.subjects else None)
    return LearnerText(
        source_kind="workbench_text",
        source_id=source_id,
        text=row["text"],
        context_judge="gap_reader",
        created_at=row["created"],
        subject_id=subject,
        anchor_learning_object_ids=(item.learning_object_id,) if item.learning_object_id else (),
        practice_item_id=item.id,
        attempt_id=row.get("attempt_id"),
        reading=None,
        context=context,
    )


def workbench_text_ids(repository: Repository) -> list[str]:
    """Every workbench reply or discriminating answer with text, oldest first
    (the backlog sweep; stuck steps are queued when they are sent, by
    version, never swept)."""

    with repository.connection() as connection:
        if not _table(connection, "help_assists"):
            return []
        rows = connection.execute(
            "SELECT id FROM help_assists WHERE surface = 'workbench' "
            "AND TRIM(COALESCE(feedback_text, '')) != '' "
            "AND (assist_kind = 'discriminate_answer' OR (assist_kind = 'hint' AND request = 'feedback')) "
            "ORDER BY requested_at, id"
        ).fetchall()
    return [str(row[0]) for row in rows]


def learner_text(
    vault: LoadedVault, repository: Repository, source_kind: str, source_id: str,
    *, stuck_source: StuckTextSource | None = None,
) -> LearnerText | None:
    if source_kind == "tutor_question":
        return tutor_question_text(vault, repository, source_id)
    if source_kind == "diagnosis":
        return diagnosis_text(vault, repository, source_id)
    if source_kind == "stuck_answer":
        return stuck_answer_text(vault, repository, source_id, stuck_source)
    if source_kind == "reader_formative":
        return reader_formative_text(vault, repository, source_id)
    if source_kind == "hint_feedback":
        return hint_feedback_text(vault, repository, source_id)
    if source_kind == "workbench_text":
        return workbench_text(vault, repository, source_id)
    raise ValueError(f"unknown learner-text source {source_kind!r}")


__all__ = [
    "DEFAULT_STUCK_SOURCE",
    "StuckAnswersAdapter",
    "StuckText",
    "SourceWithheld",
    "StuckTextSource",
    "diagnosis_text",
    "FIGURE_EXPLANATION_SUFFIX",
    "FIGURE_PREDICTION_PREFIX",
    "explained_predictions",
    "figure_input_manifest",
    "figures_enabled",
    "figure_prediction_id",
    "figure_prediction_row",
    "figure_prediction_text",
    "figure_prediction_withheld",
    "formative_row",
    "is_figure_prediction",
    "hint_feedback_ids",
    "hint_feedback_row",
    "hint_feedback_text",
    "learner_text",
    "missed_formative_ids",
    "reader_formative_text",
    "reading_from_diagnosis",
    "resolve_prerequisite_ref",
    "stuck_answer_text",
    "stuck_text_for",
    "stuck_texts",
    "tutor_question_text",
    "WORKBENCH_TEXT_ROLES",
    "workbench_text",
    "workbench_text_ids",
    "workbench_text_row",
]
