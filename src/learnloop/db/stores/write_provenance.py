"""Write-time provenance of model-written text (spec_mcp_frontend_c1 §4.8).

Owner decision 2026-10-14 ("land narrow, then fix source"): a text a model
wrote (a diagnosis summary, a hypothesis, a candidate or misconception
statement and its correction, a learner-text gap's words, a generated topic's
name, a seeded item's question) leaves LearnLoop for a chat host only when its
writer recorded, in the transaction that wrote it, exactly what it was written
from, and every recorded input is safe (``learner_context.TextGuard``, rule
(c)). Inputs are recorded at the source, never inferred from the output.

One append-only table holds the records (``text_write_provenance``, migration
204). A row names the text (``kind``, ``record_id``), the hash of the text as
written, the writer, and the **closed** record of its inputs
(:class:`WriteRecord`): the writer's own reads, plus the recorded inputs of
every derived text it read (:func:`closure`), so a reader never chases a
chain. A text's provenance is the union of every row written for it
(:func:`stored_record`): each writer of the text recorded what it read. A
writer that read something it cannot account for records ``complete = 0``
and why; a text with no row, an incomplete row, or a row whose hash no longer
matches the text as stored is held back.

**What an input is** (:class:`Inputs`):

* ``answers``: the learner's answers read (their text, or a grader's output
  about them), each with the assessment-contract revision it was read under
  (``None`` when the answer had no single pinned contract on its own item);
* ``items``: practice items whose question the writer read;
* ``solution_items``: items whose rubric or reference solution the writer
  read, directly or through a grader's output (a grader read both, so its
  output carries them);
* ``topics``: topics (learning objects) whose name or id the writer read;
* ``sources``: source refs whose text the writer read (a facet claim's
  source, a Reader passage);
* ``questions``: learner questions read, each with the contract it was asked
  about (Q10).

**Gradings** are origins: a grader's output (error events, a blind record,
the joint grader's causes) is folded into whatever is written from it. A
grading made from this migration on records a ``grading`` row in its own
transaction, with the C4 history it was shown (Q14: the receipt is in the
same transaction, so a missing receipt means "not augmented"). An older
grading has no row: a blind grade is learner-blind by construction (its
grader read the answer and its item only), a joint grade with a C4 receipt
read that history, and a joint model grade without one cannot be accounted
for (:func:`grading_record`).

This module is storage only: it never decides whether an input is safe
(``learnloop.learner_protection`` does, for the chat read model).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.ids import new_ulid

PROVENANCE_VERSION = "write_provenance_v1"

#: The derived texts a record may name (``learner_context.DERIVED_KINDS``).
TEXT_KINDS: tuple[str, ...] = (
    "diagnosis",
    "hypothesis",
    "candidate",
    "misconception",
    "misconception_correction",
    "learner_text_gap",
    "learning_object",
    "practice_item",
)
#: A grading: an origin whose output other texts are written from (keyed by attempt).
GRADING = "grading"
KINDS: tuple[str, ...] = (*TEXT_KINDS, GRADING)

#: Why a record is incomplete, for the reasons this module itself names.
NO_RECORD = "no write-time record"
TEXT_CHANGED = "the text was rewritten by a writer that recorded nothing"
GRADING_UNRECORDED = "a grader's inputs were not recorded (graded before write-time provenance, no C4 receipt)"
#: A generated topic's name as a writer was shown it is not the text its
#: record covers (renamed since by a writer that recorded nothing; codex review F2).
NAME_UNCOVERED = "the name the writer was shown is not the text its record covers"

Ref = tuple[str, str]
_CHUNK = 500


def text_sha256(text: Any) -> str | None:
    """The hash a record keeps of the text it covers (exactly as stored)."""

    if text is None:
        return None
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def _table(connection: Any, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone() is not None


def _marks(values: Sequence[Any]) -> str:
    return ",".join("?" for _ in values)


def _contracts(values: Iterable[Any]) -> tuple[str | None, ...]:
    found = {None if value in (None, "") else str(value) for value in values}
    return tuple(sorted(found, key=lambda value: (value is not None, value or "")))


def _source_key(ref: Mapping[str, Any]) -> str:
    return json.dumps(ref, sort_keys=True, ensure_ascii=False, default=str)


def source_ref(ref: Any) -> dict[str, Any] | None:
    """A source ref as a record keeps it: where its text lies (extraction,
    spans, locator, revision, source), from a mapping or a vault model."""

    def get(name: str) -> Any:
        return ref.get(name) if isinstance(ref, Mapping) else getattr(ref, name, None)

    value: dict[str, Any] = {}
    for name in ("ref_type", "ref_id", "source_id", "revision_id", "extraction_id", "locator"):
        found = get(name)
        if found not in (None, ""):
            value[name] = str(found)
    spans = get("span_ids")
    if spans:
        value["span_ids"] = sorted({str(span) for span in spans if span})
    span = get("span_id")
    if span:
        value["span_ids"] = sorted({*value.get("span_ids", []), str(span)})
    if value.get("ref_type") == "canonical_source" and "source_id" not in value and value.get("ref_id"):
        # A canonical-source ref names its source by ``ref_id``.
        value["source_id"] = value["ref_id"]
    return value or None


@dataclass(frozen=True)
class Inputs:
    """What a writer read (see the module doc). Every field is closed under
    :meth:`union`; ``answers`` and ``questions`` keep every contract any
    writer read them under."""

    answers: Mapping[str, tuple[str | None, ...]] = field(default_factory=dict)
    items: frozenset[str] = frozenset()
    solution_items: frozenset[str] = frozenset()
    topics: frozenset[str] = frozenset()
    sources: tuple[Mapping[str, Any], ...] = ()
    questions: Mapping[str, tuple[str | None, ...]] = field(default_factory=dict)

    @classmethod
    def of(
        cls,
        *,
        answers: Mapping[str, Any] | Iterable[tuple[str, Any]] = (),
        items: Iterable[Any] = (),
        solution_items: Iterable[Any] = (),
        topics: Iterable[Any] = (),
        sources: Iterable[Any] = (),
        questions: Mapping[str, Any] | Iterable[tuple[str, Any]] = (),
    ) -> Inputs:
        def pairs(value: Any) -> dict[str, tuple[str | None, ...]]:
            found: dict[str, set[Any]] = {}
            for key, contract in (value.items() if isinstance(value, Mapping) else value):
                if not key:
                    continue
                contracts = contract if isinstance(contract, (tuple, list, set, frozenset)) else (contract,)
                found.setdefault(str(key), set()).update(contracts)
            return {key: _contracts(contracts) for key, contracts in found.items()}

        refs: dict[str, dict[str, Any]] = {}
        for ref in sources:
            value = source_ref(ref)
            if value:
                refs[_source_key(value)] = value
        return cls(
            answers=pairs(answers),
            items=frozenset(str(value) for value in items if value),
            solution_items=frozenset(str(value) for value in solution_items if value),
            topics=frozenset(str(value) for value in topics if value),
            sources=tuple(refs[key] for key in sorted(refs)),
            questions=pairs(questions),
        )

    def union(self, other: Inputs) -> Inputs:
        answers = {key: set(value) for key, value in self.answers.items()}
        for key, value in other.answers.items():
            answers.setdefault(key, set()).update(value)
        questions = {key: set(value) for key, value in self.questions.items()}
        for key, value in other.questions.items():
            questions.setdefault(key, set()).update(value)
        refs = {_source_key(ref): dict(ref) for ref in (*self.sources, *other.sources)}
        return Inputs(
            answers={key: _contracts(value) for key, value in answers.items()},
            items=self.items | other.items,
            solution_items=self.solution_items | other.solution_items,
            topics=self.topics | other.topics,
            sources=tuple(refs[key] for key in sorted(refs)),
            questions={key: _contracts(value) for key, value in questions.items()},
        )

    @property
    def empty(self) -> bool:
        return not (self.answers or self.items or self.solution_items or self.topics or self.sources
                    or self.questions)

    def as_json(self) -> dict[str, Any]:
        return {
            "answers": {key: list(self.answers[key]) for key in sorted(self.answers)},
            "items": sorted(self.items),
            "solution_items": sorted(self.solution_items),
            "topics": sorted(self.topics),
            "sources": [dict(ref) for ref in self.sources],
            "questions": {key: list(self.questions[key]) for key in sorted(self.questions)},
        }

    @classmethod
    def from_json(cls, value: Any) -> Inputs:
        value = value if isinstance(value, Mapping) else {}
        return cls.of(
            answers={str(key): tuple(contracts or (None,)) for key, contracts in
                     (value.get("answers") or {}).items()},
            items=value.get("items") or (),
            solution_items=value.get("solution_items") or (),
            topics=value.get("topics") or (),
            sources=value.get("sources") or (),
            questions={str(key): tuple(contracts or (None,)) for key, contracts in
                       (value.get("questions") or {}).items()},
        )


@dataclass(frozen=True)
class WriteRecord:
    """A writer's closed record: its inputs, whether it could account for
    everything it read (``complete``; ``missing`` names what it could not),
    and the derived texts whose records were folded in (``derived_from``)."""

    inputs: Inputs = field(default_factory=Inputs)
    complete: bool = True
    missing: tuple[str, ...] = ()
    derived_from: tuple[Ref, ...] = ()

    @classmethod
    def incomplete(cls, reason: str, *, inputs: Inputs | None = None) -> WriteRecord:
        return cls(inputs=inputs or Inputs(), complete=False, missing=(str(reason),))

    def join(self, *others: WriteRecord) -> WriteRecord:
        inputs, complete = self.inputs, self.complete
        missing = list(self.missing)
        derived = list(self.derived_from)
        for other in others:
            inputs = inputs.union(other.inputs)
            complete = complete and other.complete
            missing += [reason for reason in other.missing if reason not in missing]
            derived += [ref for ref in other.derived_from if ref not in derived]
        return WriteRecord(inputs=inputs, complete=complete, missing=tuple(missing), derived_from=tuple(derived))

    def with_inputs(self, inputs: Inputs) -> WriteRecord:
        return WriteRecord(self.inputs.union(inputs), self.complete, self.missing, self.derived_from)

    def as_json(self) -> dict[str, Any]:
        """A JSON form (a job's progress keeps a record across retries)."""

        return {"inputs": self.inputs.as_json(), "complete": bool(self.complete), "missing": list(self.missing),
                "derived_from": [list(ref) for ref in self.derived_from]}

    @classmethod
    def from_json(cls, value: Any) -> WriteRecord:
        if not isinstance(value, Mapping):
            return cls.incomplete("the recorded inputs were lost")
        try:
            return cls(
                inputs=Inputs.from_json(value.get("inputs")),
                complete=bool(value.get("complete")),
                missing=tuple(str(reason) for reason in value.get("missing") or ()),
                derived_from=tuple((str(ref[0]), str(ref[1])) for ref in value.get("derived_from") or ()
                                   if isinstance(ref, (list, tuple)) and len(ref) == 2),
            )
        except (TypeError, ValueError, AttributeError):
            return cls.incomplete("the recorded inputs could not be read")

    def as_row(self) -> dict[str, Any]:
        return {
            "complete": 1 if self.complete else 0,
            "incomplete_reasons_json": json.dumps(list(self.missing), ensure_ascii=False),
            "inputs_json": json.dumps(self.inputs.as_json(), sort_keys=True, ensure_ascii=False),
            "derived_from_json": json.dumps([list(ref) for ref in self.derived_from], ensure_ascii=False),
        }


@dataclass(frozen=True)
class StoredRecord:
    """A text's provenance as stored: the union of every row written for it,
    and the hash of the text the LATEST row covers."""

    record: WriteRecord
    text_sha256: str | None
    rows: int
    writers: tuple[str, ...] = ()


def record_text_write(
    connection: Any,
    *,
    kind: str,
    record_id: str,
    text: Any,
    writer: str,
    record: WriteRecord,
    created_at: str | None = None,
    clock: Clock | None = None,
) -> str | None:
    """Append one record for one text write, on the writer's own connection
    (so it commits, or rolls back, with the text). None on a vault older than
    migration 204 (nothing is recorded; the text stays held back)."""

    if kind not in KINDS:
        raise ValueError(f"unknown write-provenance kind {kind!r}")
    if not record_id:
        raise ValueError("a write-provenance record needs the id of what was written")
    if not _table(connection, "text_write_provenance"):
        return None
    row_id = new_ulid()
    row = record.as_row()
    connection.execute(
        "INSERT INTO text_write_provenance(id, kind, record_id, text_sha256, writer, complete, "
        "incomplete_reasons_json, inputs_json, derived_from_json, provenance_version, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (row_id, kind, str(record_id), text_sha256(text), str(writer), row["complete"],
         row["incomplete_reasons_json"], row["inputs_json"], row["derived_from_json"], PROVENANCE_VERSION,
         created_at or utc_now_iso(clock)),
    )
    return row_id


_COLUMNS = ("text_sha256", "writer", "complete", "incomplete_reasons_json", "inputs_json", "derived_from_json")


def _decode(row: Mapping[str, Any]) -> WriteRecord:
    try:
        inputs = Inputs.from_json(json.loads(row["inputs_json"] or "{}"))
        missing = tuple(str(value) for value in json.loads(row["incomplete_reasons_json"] or "[]"))
        derived = tuple((str(ref[0]), str(ref[1])) for ref in json.loads(row["derived_from_json"] or "[]")
                        if isinstance(ref, (list, tuple)) and len(ref) == 2)
    except (TypeError, ValueError, KeyError, IndexError, AttributeError):
        return WriteRecord.incomplete("the record could not be read")
    return WriteRecord(inputs=inputs, complete=bool(row["complete"]), missing=missing, derived_from=derived)


def stored_record(connection: Any, kind: str, record_id: str) -> StoredRecord | None:
    """The union of every row written for one text, or None when none was."""

    if not record_id or not _table(connection, "text_write_provenance"):
        return None
    rows = [dict(zip(_COLUMNS, row, strict=True)) for row in connection.execute(
        f"SELECT {', '.join(_COLUMNS)} FROM text_write_provenance WHERE kind = ? AND record_id = ? "
        "ORDER BY created_at, id",
        (str(kind), str(record_id)),
    )]
    if not rows:
        return None
    record = _decode(rows[0]).join(*(_decode(row) for row in rows[1:]))
    return StoredRecord(record=record, text_sha256=rows[-1]["text_sha256"], rows=len(rows),
                        writers=tuple(dict.fromkeys(str(row["writer"]) for row in rows)))


# -- what gradings read ----------------------------------------------------------------


def attempt_items(connection: Any, attempt_ids: Iterable[Any]) -> dict[str, tuple[str | None, str | None]]:
    """``{attempt: (practice item, learning object)}`` for the attempts on record."""

    ids = sorted({str(value) for value in attempt_ids if value})
    found: dict[str, tuple[str | None, str | None]] = {}
    for start in range(0, len(ids), _CHUNK):
        chunk = ids[start:start + _CHUNK]
        for row in connection.execute(
            f"SELECT id, practice_item_id, learning_object_id FROM practice_attempts WHERE id IN ({_marks(chunk)})",
            chunk,
        ):
            found[str(row[0])] = (None if row[1] is None else str(row[1]), None if row[2] is None else str(row[2]))
    return found


def pinned_contract_ids(connection: Any, items: Mapping[str, Any]) -> dict[str, str]:
    """``{attempt: contract version}`` for the attempts (``{attempt: item}``)
    graded against exactly one assessment contract of their own item: the
    only affirmative record of the revision an answer was graded against
    (``learner_protection.pinned_contracts`` reads the same rule)."""

    ids = [str(attempt) for attempt in items if attempt]
    if not ids or not _table(connection, "grading_evidence") or not _table(connection, "assessment_contract_versions"):
        return {}
    contracts: dict[str, set[Any]] = {}
    for start in range(0, len(ids), _CHUNK):
        chunk = ids[start:start + _CHUNK]
        for attempt_id, contract_id in connection.execute(
            f"SELECT attempt_id, assessment_contract_version_id FROM grading_evidence "
            f"WHERE superseded_at IS NULL AND attempt_id IN ({_marks(chunk)})", chunk,
        ):
            contracts.setdefault(str(attempt_id), set()).add(contract_id)
    single = {attempt: next(iter(found)) for attempt, found in contracts.items()
              if len(found) == 1 and None not in found}
    versions = sorted({str(value) for value in single.values()})
    owners: dict[str, str] = {}
    for start in range(0, len(versions), _CHUNK):
        chunk = versions[start:start + _CHUNK]
        for version_id, item_id in connection.execute(
            f"SELECT id, practice_item_id FROM assessment_contract_versions WHERE id IN ({_marks(chunk)})", chunk,
        ):
            owners[str(version_id)] = str(item_id)
    return {attempt: str(version) for attempt, version in single.items()
            if owners.get(str(version)) is not None and owners[str(version)] == str(items.get(attempt) or "")}


def answer_inputs(connection: Any, attempt_ids: Iterable[Any], *, solution: bool = False) -> Inputs:
    """The inputs of reading these answers: each answer under its pinned
    contract (``None`` without one), its item (named whether or not its
    question was read, so its keys filter the text), its topic, and with
    ``solution`` the item's rubric and reference solution."""

    ids = sorted({str(value) for value in attempt_ids if value})
    if not ids:
        return Inputs()
    rows = attempt_items(connection, ids)
    pins = pinned_contract_ids(connection, {attempt: item for attempt, (item, _lo) in rows.items()})
    items = {item for item, _lo in rows.values() if item}
    return Inputs.of(
        answers={attempt: pins.get(attempt) for attempt in ids},
        items=items,
        solution_items=items if solution else (),
        topics={lo for _item, lo in rows.values() if lo},
    )


def _has_model_grade(connection: Any, attempt_id: str) -> bool:
    if not _table(connection, "grading_evidence"):
        return True
    row = connection.execute(
        "SELECT COUNT(*), SUM(CASE WHEN agent_run_id IS NOT NULL THEN 1 ELSE 0 END) FROM grading_evidence "
        "WHERE attempt_id = ? AND superseded_at IS NULL", (attempt_id,),
    ).fetchone()
    total, model = int(row[0] or 0), int(row[1] or 0)
    # No current evidence at all: nothing says no model graded it.
    return total == 0 or model > 0


def _c4_history(connection: Any, attempt_id: str) -> list[str] | None:
    if not _table(connection, "diagnostic_augmentation_receipts"):
        return None
    rows = connection.execute(
        "SELECT c4_history_attempt_ids_json FROM diagnostic_augmentation_receipts WHERE attempt_id = ? "
        "ORDER BY created_at, id", (attempt_id,),
    ).fetchall()
    if not rows:
        return None
    shown: list[str] = []
    for (value,) in rows:
        try:
            shown += [str(attempt) for attempt in json.loads(value or "[]") if attempt]
        except (TypeError, ValueError):
            return None
    return shown


def grading_inputs(connection: Any, attempt_id: str, *, shown_history: Iterable[Any] = ()) -> Inputs:
    """What one grading read: the answer under its contract, its item's
    question, rubric and reference solution, its topic, and the prior
    answers it was shown (C4)."""

    own = answer_inputs(connection, [attempt_id], solution=True)
    history = [str(value) for value in shown_history if value and str(value) != str(attempt_id)]
    return own.union(answer_inputs(connection, history)) if history else own


#: Gradings whose transaction is open on this thread: ``{attempt: C4 history
#: shown}``. A text written from the grader's output inside that transaction
#: (an error hunt's candidate, a cause materialized with the grade) folds the
#: grading in before its row is written at the end of the transaction.
_PENDING_GRADINGS: ContextVar[Mapping[str, tuple[str, ...]]] = ContextVar("pending_gradings", default={})


@contextmanager
def grading_in_progress(attempt_id: str, *, shown_history: Iterable[Any] = ()) -> Iterator[None]:
    """Declare the grading of ``attempt_id`` the caller is writing (with the
    C4 history its grader was shown) for the length of its transaction."""

    pending = dict(_PENDING_GRADINGS.get())
    pending[str(attempt_id)] = tuple(str(value) for value in shown_history if value)
    token = _PENDING_GRADINGS.set(pending)
    try:
        yield
    finally:
        _PENDING_GRADINGS.reset(token)


def grading_record(connection: Any, attempt_id: str) -> WriteRecord:
    """What the grader(s) of ``attempt_id`` read, for a text written from
    their output: the grading being written now (:func:`grading_in_progress`)
    and the recorded gradings (every grading since migration 204 records one
    in its own transaction), else what the grading's own ledger establishes
    (see the module doc), else incomplete."""

    attempt_id = str(attempt_id)
    pending = _PENDING_GRADINGS.get().get(attempt_id)
    if pending is not None:
        return WriteRecord(grading_inputs(connection, attempt_id, shown_history=pending),
                           derived_from=((GRADING, attempt_id),))
    stored = stored_record(connection, GRADING, attempt_id)
    if stored is not None:
        return WriteRecord(stored.record.inputs, stored.record.complete, stored.record.missing,
                           ((GRADING, attempt_id), *stored.record.derived_from))
    ref = ((GRADING, attempt_id),)
    if _table(connection, "blind_grade_records") and connection.execute(
        "SELECT 1 FROM blind_grade_records WHERE attempt_id = ? LIMIT 1", (attempt_id,),
    ).fetchone() is not None:
        # Learner-blind by construction (Slice 1 §4.1): the answer and its item only.
        return WriteRecord(grading_inputs(connection, attempt_id), derived_from=ref)
    if not _has_model_grade(connection, attempt_id):
        # Deterministic, self- or manual grading: no grader wrote text.
        return WriteRecord(answer_inputs(connection, [attempt_id]), derived_from=ref)
    shown = _c4_history(connection, attempt_id)
    if shown is not None:
        return WriteRecord(grading_inputs(connection, attempt_id, shown_history=shown), derived_from=ref)
    return WriteRecord(answer_inputs(connection, [attempt_id], solution=True), complete=False,
                       missing=(f"{GRADING_UNRECORDED} ({attempt_id})",), derived_from=ref)


def record_grading(connection: Any, *, attempt_id: str, writer: str, shown_history: Iterable[Any] = (),
                   clock: Clock | None = None) -> str | None:
    """Record one grading of ``attempt_id`` in the grading's own transaction
    (call it on that transaction's connection, after the grade is written so
    its contract is pinned)."""

    return record_text_write(
        connection, kind=GRADING, record_id=str(attempt_id), text=None, writer=writer,
        record=WriteRecord(grading_inputs(connection, str(attempt_id), shown_history=shown_history)),
        clock=clock,
    )


# -- what a grading showed, as it stood (codex review F3) --------------------------------


def grading_mark(evidence_ids: Iterable[Any], error_event_ids: Iterable[Any]) -> str:
    """The identity of one attempt's grading as a reader saw it: its current
    (unsuperseded) evidence rows and its error events. A regrade supersedes
    the one and re-mints the other, so the mark changes with every grading."""

    payload = json.dumps([sorted({str(value) for value in evidence_ids if value}),
                          sorted({str(value) for value in error_event_ids if value})])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def grading_marks(connection: Any, attempt_ids: Iterable[Any]) -> dict[str, str]:
    """``{attempt: grading_mark}`` for ``attempt_ids`` as they stand now."""

    ids = sorted({str(value) for value in attempt_ids if value})
    evidence: dict[str, list[str]] = {}
    events: dict[str, list[str]] = {}
    for start in range(0, len(ids), _CHUNK):
        chunk = ids[start:start + _CHUNK]
        if _table(connection, "grading_evidence"):
            for attempt_id, row_id in connection.execute(
                f"SELECT attempt_id, id FROM grading_evidence WHERE superseded_at IS NULL "
                f"AND attempt_id IN ({_marks(chunk)})", chunk,
            ):
                evidence.setdefault(str(attempt_id), []).append(str(row_id))
        if _table(connection, "error_events"):
            for attempt_id, row_id in connection.execute(
                f"SELECT attempt_id, id FROM error_events WHERE attempt_id IN ({_marks(chunk)})", chunk,
            ):
                events.setdefault(str(attempt_id), []).append(str(row_id))
    return {attempt: grading_mark(evidence.get(attempt, ()), events.get(attempt, ())) for attempt in ids}


# -- the closure -------------------------------------------------------------------------


def attempt_statement_refs(connection: Any, attempt_id: str, *, diagnosis_id: str | None = None,
                           every_diagnosis: bool = False) -> tuple[Ref, ...]:
    """Where an attempt's error-event causes were written: its grading, and
    the diagnosis whose causal view lies over them (``diagnosis_id``), or
    with ``every_diagnosis`` every completed live diagnosis of the attempt
    (an unresolved-cause factor's candidate set was drawn from whichever was
    in force when it was refreshed)."""

    refs: list[Ref] = [(GRADING, str(attempt_id))]
    if diagnosis_id:
        refs.append(("diagnosis", str(diagnosis_id)))
    if every_diagnosis and _table(connection, "attempt_diagnoses"):
        for (found,) in connection.execute(
            "SELECT id FROM attempt_diagnoses WHERE attempt_id = ? AND mode = 'live' AND status = 'completed' "
            "AND proposal_json IS NOT NULL ORDER BY created_at, id", (str(attempt_id),),
        ):
            if ("diagnosis", str(found)) not in refs:
                refs.append(("diagnosis", str(found)))
    return tuple(refs)


def closure(connection: Any, refs: Iterable[Ref], *, texts: Mapping[Ref, Any] | None = None) -> WriteRecord:
    """The joined records of the derived texts in ``refs`` (a writer that
    read them folds this into its own record). A text with no record, or
    whose current text (``texts``, when the writer has it) is not the one its
    record covers, makes the closure incomplete."""

    joined = WriteRecord()
    seen: list[Ref] = []
    for kind, record_id in refs:
        ref = (str(kind), str(record_id))
        if not ref[1] or ref in seen:
            continue
        seen.append(ref)
        if ref[0] == GRADING:
            joined = joined.join(grading_record(connection, ref[1]))
            continue
        stored = stored_record(connection, ref[0], ref[1])
        if stored is None:
            joined = joined.join(WriteRecord.incomplete(f"{ref[0]} {ref[1]}: {NO_RECORD}"))
            continue
        part = stored.record
        if texts is not None and ref in texts and stored.text_sha256 is not None \
                and text_sha256(texts[ref]) != stored.text_sha256:
            part = part.join(WriteRecord.incomplete(f"{ref[0]} {ref[1]}: {TEXT_CHANGED}"))
        joined = joined.join(WriteRecord(part.inputs, part.complete, part.missing, (ref, *part.derived_from)))
    return joined


def fold_topic_records(connection: Any, record: WriteRecord, *,
                       titles: Mapping[str, Iterable[Any]] | None = None) -> WriteRecord:
    """``record`` with the record of every topic it names that has one of its
    own folded in (a generated topic: its name was drafted, so a text that
    read it read what it was drafted from). A generated topic with no record
    is left unfolded, and the chat read model holds back what read it.

    ``titles`` (codex review F2): every name the writer was shown for a topic
    (``{topic: (text, ...)}``, captured when its context was built). A
    record covers one text, the name it was written for (the hash of the
    latest row), so a topic shown under any other name (renamed since by a
    writer that recorded nothing) folds in as incomplete. A topic the writer
    read by id only has no entry and folds as it is: its id was minted from
    the drafted name its record covers."""

    shown = {str(topic): [str(text) for text in texts if text is not None]
             for topic, texts in (titles or {}).items()}
    folded = {ref[1] for ref in record.derived_from if ref[0] == "learning_object"}
    while True:
        pending = sorted(topic for topic in record.inputs.topics if topic not in folded)
        found = False
        for topic in pending:
            folded.add(topic)
            stored = stored_record(connection, "learning_object", topic)
            if stored is None:
                continue
            found = True
            part = stored.record
            if any(text_sha256(text) != stored.text_sha256 for text in shown.get(topic, ())):
                part = part.join(WriteRecord.incomplete(f"learning_object {topic}: {NAME_UNCOVERED}"))
            record = record.join(WriteRecord(part.inputs, part.complete, part.missing,
                                             (("learning_object", topic), *part.derived_from)))
        if not found:
            return record


# -- Q9: error-event lineage -------------------------------------------------------------


def record_error_event_lineage(connection: Any, *, attempt_id: str, replaced: Iterable[Any],
                               reminted: Iterable[Any], clock: Clock | None = None) -> int:
    """Record what a regrade did to ``attempt_id``'s error events (Q9): every
    event it retired (one of the attempt's events before the regrade that is
    gone after it) is replaced by each event it minted, or, when it minted
    none (codex review F4: the regrade found no error), by nothing: one row
    with no ``error_event_id``, the explicit "no current error". Either way
    the retired id keeps its attempt. Idempotent. Returns rows written."""

    if not _table(connection, "error_event_lineage"):
        return 0
    before = {str(value) for value in replaced if value}
    after = {str(value) for value in reminted if value}
    retired = sorted(before - after)
    successors: list[str | None] = sorted(after - before) or [None]
    now = utc_now_iso(clock)
    written = 0
    for replaced_id in retired:
        for event_id in successors:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO error_event_lineage(id, attempt_id, error_event_id, replaces_error_event_id, "
                "reason, created_at) VALUES (?, ?, ?, ?, 'regrade', ?)",
                (new_ulid(), str(attempt_id), event_id, replaced_id, now),
            )
            written += int(cursor.rowcount or 0)
    return written


def replaced_error_event_attempts(connection: Any) -> dict[str, str]:
    """``{retired error-event id: its attempt}`` for every event a regrade
    retired, re-minted or not (Q9): a belief listing one still names its
    answer."""

    if not _table(connection, "error_event_lineage"):
        return {}
    return {str(row[0]): str(row[1]) for row in connection.execute(
        "SELECT replaces_error_event_id, attempt_id FROM error_event_lineage ORDER BY created_at, id")}


def retired_error_event_ids(connection: Any, event_ids: Iterable[Any]) -> frozenset[str]:
    """The listed ids a regrade retired with no replacement: the answer they
    belonged to has no error now (codex review F4)."""

    ids = sorted({str(value) for value in event_ids if value})
    if not ids or not _table(connection, "error_event_lineage"):
        return frozenset()
    found: set[str] = set()
    for start in range(0, len(ids), _CHUNK):
        chunk = ids[start:start + _CHUNK]
        found.update(str(row[0]) for row in connection.execute(
            f"SELECT replaces_error_event_id FROM error_event_lineage WHERE error_event_id IS NULL "
            f"AND replaces_error_event_id IN ({_marks(chunk)})", chunk))
    return frozenset(found)


def current_error_event_ids(connection: Any, event_ids: Iterable[Any]) -> dict[str, tuple[str, ...]]:
    """``{listed id: the error events it stands for now}``: an event still on
    record stands for itself; a replaced one for the events that replaced it,
    followed through every later regrade (Q9). An id retired with no
    replacement (:func:`retired_error_event_ids`: no current error), and an
    id nothing records, map to ``()``."""

    resolved: dict[str, tuple[str, ...]] = {}
    has_lineage = _table(connection, "error_event_lineage")
    for listed in dict.fromkeys(str(value) for value in event_ids if value):
        frontier, seen, found = [listed], set(), []
        while frontier:
            current = frontier.pop()
            if current in seen:
                continue
            seen.add(current)
            if connection.execute("SELECT 1 FROM error_events WHERE id = ?", (current,)).fetchone() is not None:
                found.append(current)
                continue
            if has_lineage:
                frontier.extend(str(row[0]) for row in connection.execute(
                    "SELECT error_event_id FROM error_event_lineage WHERE replaces_error_event_id = ? "
                    "AND error_event_id IS NOT NULL ORDER BY created_at, error_event_id", (current,)))
        resolved[listed] = tuple(sorted(dict.fromkeys(found)))
    return resolved


__all__ = [
    "GRADING",
    "GRADING_UNRECORDED",
    "KINDS",
    "NAME_UNCOVERED",
    "NO_RECORD",
    "PROVENANCE_VERSION",
    "TEXT_CHANGED",
    "TEXT_KINDS",
    "Inputs",
    "Ref",
    "StoredRecord",
    "WriteRecord",
    "answer_inputs",
    "attempt_items",
    "attempt_statement_refs",
    "closure",
    "current_error_event_ids",
    "fold_topic_records",
    "grading_in_progress",
    "grading_inputs",
    "grading_mark",
    "grading_marks",
    "grading_record",
    "pinned_contract_ids",
    "record_error_event_lineage",
    "record_grading",
    "record_text_write",
    "replaced_error_event_attempts",
    "retired_error_event_ids",
    "source_ref",
    "stored_record",
    "text_sha256",
]
