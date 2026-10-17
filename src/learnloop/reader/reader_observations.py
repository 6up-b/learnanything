"""Reader workbench RW6a: the session's formative records (spec_reader_workbench_v1
§9.1, ``ReaderObservationV1``; restored rows 58 and 68; gate G50).

One record per tier-2 signal of a reader session (W1), in the shape the
dialogue sketched (round 2 §6), restricted to routing: ``kind``,
``source_event_ids``, ``span_ids``, ``item_id`` and ``step_id`` where they
apply, ``facet_candidates`` (the item's facets, or the Learning Objects of the
spans), ``observed`` (a short typed field, never prose), ``hypotheses`` (gap
ids learner-text gaps named from it), ``assistance`` (level, reveal) and
``authority: "routing_only"``. No second model compiles them: verdicts and
levels are copied from their rows, and the learner's words stay with
learner-text gaps (the compiler, W13), so a record never carries them.

**What exists today.** RW1a's reconnect *still unclear* is the only tier-2
row on ``main``. RW1b's missed next-step, why-step and assumption answers
(``reader_authored_questions`` with a selection scope, those question styles
and a ``partly`` / ``no`` self-check) and RW5a's missed predictions
(``figure_predictions``) have their reads here, and those read nothing until
the phases write rows. RW2b's ``check_questionable``, ``hint_taken``,
``doesnt_connect`` and ``discriminate_answer`` come with ``help_assists``.

**Never evidence.** The numbers stay with the estimator, which never reads
these records (W1): an import-linter contract keeps every package that writes
evidence from importing this module (G50). Pure reads; nothing here writes.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.reader import reader_dialogue as RD
from learnloop.reader.reader_progression import learning_objects_for_span
from learnloop.reader.reader_sessions import ReaderSession

ROUTING_ONLY = "routing_only"
RECORD_VERSION = "reader-observation-v1"

#: Every kind a record may carry (spec §9.1), in the spec's order.
OBSERVATION_KINDS: tuple[str, ...] = (
    "still_unclear", "next_step_missed", "why_step_missed", "assumption_missed", "prediction_missed",
    "check_questionable", "hint_taken", "doesnt_connect", "discriminate_answer",
)
#: RW1b's question styles and the kind a missed answer becomes.
FORMATIVE_STYLE_KINDS: Mapping[str, str] = {
    "next_step": "next_step_missed",
    "why_step": "why_step_missed",
    "assumptions": "assumption_missed",
}
MISSED_SELF_CHECKS: tuple[str, ...] = ("partly", "no")
#: learner-text gaps that named nothing are not hypotheses.
UNNAMED_GAP_KINDS: tuple[str, ...] = ("none", "unread")


@dataclass(frozen=True)
class ReaderObservationV1:
    """One routing-only formative record (spec §9.1). Typed; no prose."""

    kind: str
    source_event_ids: tuple[str, ...]
    span_ids: tuple[str, ...]
    observed: Mapping[str, Any]
    observed_at: str
    item_id: str | None = None
    step_id: str | None = None
    facet_candidates: tuple[str, ...] = ()
    hypotheses: tuple[str, ...] = ()
    assistance: Mapping[str, Any] = field(default_factory=lambda: {"level": None, "reveal": False})
    #: The inquiry the record belongs to, where it has one (the card's "open").
    root_exchange_id: str | None = None
    authority: str = ROUTING_ONLY

    def __post_init__(self) -> None:
        if self.kind not in OBSERVATION_KINDS:
            raise ValueError(f"unknown reader observation kind {self.kind!r}")
        if self.authority != ROUTING_ONLY:
            raise ValueError("a reader observation is routing_only, never evidence")

    def as_dict(self) -> dict[str, Any]:
        return {
            "record_version": RECORD_VERSION,
            "kind": self.kind,
            "source_event_ids": list(self.source_event_ids),
            "span_ids": list(self.span_ids),
            "item_id": self.item_id,
            "step_id": self.step_id,
            "facet_candidates": list(self.facet_candidates),
            "observed": dict(self.observed),
            "hypotheses": list(self.hypotheses),
            "assistance": dict(self.assistance),
            "root_exchange_id": self.root_exchange_id,
            "observed_at": self.observed_at,
            "authority": self.authority,
        }


def _payload(raw: Any) -> dict[str, Any]:
    if isinstance(raw, Mapping):
        return dict(raw)
    try:
        decoded = json.loads(raw or "{}")
    except (TypeError, ValueError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _span_list(raw: Any) -> list[str]:
    try:
        value = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return []
    return [str(span) for span in value] if isinstance(value, list) else []


def _has_table(repository: Any, name: str) -> bool:
    with repository.connection() as connection:
        return connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
        ).fetchone() is not None


def _span_learning_objects(vault: Any, repository: Any, extraction_id: str, span_ids: Sequence[str]) -> tuple[str, ...]:
    found: list[str] = []
    for span_id in span_ids:
        for lo_id in learning_objects_for_span(vault, repository, extraction_id=extraction_id, span_id=span_id):
            if lo_id not in found:
                found.append(lo_id)
    return tuple(sorted(found))


def named_gaps(
    repository: Any, question_event_ids: Sequence[str], *, source_kind: str = "tutor_question",
) -> dict[str, list[dict[str, Any]]]:
    """Gaps learner-text gaps named from these reader questions, by question
    (``source_kind = 'reader_formative'``: from RW1b's missed formative
    answers, by authored question).

    Only rows that named something (``kind`` other than none / unread). Ids,
    kinds and targets; never the learner's text."""

    wanted = sorted({str(q) for q in question_event_ids if q})
    if not wanted or not _has_table(repository, "learner_text_gaps"):
        return {}
    marks = ", ".join("?" for _ in wanted)
    with repository.connection() as connection:
        rows = connection.execute(
            f"SELECT id, source_id, kind, target_kind, target_id, created_at FROM learner_text_gaps "
            f"WHERE source_kind = ? AND source_id IN ({marks}) ORDER BY created_at, id",
            (source_kind, *wanted),
        ).fetchall()
    out: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row["kind"] in UNNAMED_GAP_KINDS:
            continue
        out.setdefault(str(row["source_id"]), []).append({
            "gap_id": str(row["id"]), "kind": row["kind"], "target_kind": row["target_kind"],
            "target_id": row["target_id"], "source_id": str(row["source_id"]),
        })
    return out


# ---------------------------------------------------------------------------
# One read per tier-2 source
# ---------------------------------------------------------------------------

def still_unclear_observations(
    vault: Any, repository: Any, *, extraction_id: str, session: ReaderSession,
    exchanges: Sequence[Mapping[str, Any]] | None = None,
) -> list[ReaderObservationV1]:
    """RW1a: each reconnect *still unclear* answer in the session, one record.

    Its hypotheses are the gaps named from the follow-up the learner asked
    from the root after answering (the "still unclear…" text)."""

    history = list(exchanges) if exchanges is not None else RD.ask_history(
        repository, extraction_id=extraction_id, branches=True
    )
    by_id = {str(e["event_id"]): e for e in history}
    answers = [
        event for event in repository.reader_interaction_events(kind="reader_action_invoked")
        if (event.get("payload") or {}).get("event") == "reconnect_answered"
        and (event.get("payload") or {}).get("extraction_id") == extraction_id
        and (event.get("payload") or {}).get("answer") == "still_unclear"
        and session.contains(event.get("created_at"))
    ]
    follow_ups: dict[str, str] = {}
    for answer in answers:
        root_id = str(answer["payload"].get("root_exchange_id") or "")
        later = sorted(
            (e for e in history if e.get("parent_exchange_id") == root_id
             and str(e.get("created_at") or "") >= str(answer.get("created_at") or "")),
            key=lambda e: (str(e.get("created_at") or ""), str(e["event_id"])),
        )
        if later and later[0].get("question_event_id"):
            follow_ups[str(answer["id"])] = str(later[0]["question_event_id"])
    gaps = named_gaps(repository, list(follow_ups.values()))
    records: list[ReaderObservationV1] = []
    for answer in answers:
        payload = answer["payload"]
        root = by_id.get(str(payload.get("root_exchange_id") or ""))
        spans = tuple((root or {}).get("selection_span_ids") or ([root["span_id"]] if root else []))
        records.append(ReaderObservationV1(
            kind="still_unclear",
            source_event_ids=(str(answer["id"]),),
            span_ids=spans,
            observed={"answer": "still_unclear", "via": payload.get("via")},
            observed_at=str(answer.get("created_at") or ""),
            facet_candidates=_span_learning_objects(vault, repository, extraction_id, spans),
            hypotheses=tuple(g["gap_id"] for g in gaps.get(follow_ups.get(str(answer["id"]), ""), [])),
            root_exchange_id=str(payload.get("root_exchange_id") or "") or None,
        ))
    return records


def formative_answers(repository: Any, *, extraction_id: str, session: ReaderSession) -> list[dict[str, Any]]:
    """RW1b's answered next-step, why-step and assumption questions in the session."""

    styles = tuple(FORMATIVE_STYLE_KINDS)
    marks = ", ".join("?" for _ in styles)
    with repository.connection() as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(reader_authored_questions)")}
        if not {"scope_kind", "question_style", "self_check"} <= columns:
            return []
        rows = connection.execute(
            "SELECT id, question_style, self_check, anchor_span_ids_json, span_ids_json, answered_at "
            "FROM reader_authored_questions WHERE extraction_id = ? AND scope_kind = 'selection' "
            f"AND question_style IN ({marks}) AND answered_at IS NOT NULL ORDER BY answered_at, id",
            (extraction_id, *styles),
        ).fetchall()
    return [dict(row) for row in rows if session.contains(row["answered_at"])]


def formative_answer_observations(
    repository: Any, *, extraction_id: str, session: ReaderSession, vault: Any | None = None,
) -> list[ReaderObservationV1]:
    """RW1b: the missed (``partly`` / ``no``) formative answers, one record
    each, with the gaps learner-text gaps named from them as hypotheses."""

    records = []
    missed = [row for row in formative_answers(repository, extraction_id=extraction_id, session=session)
              if row["self_check"] in MISSED_SELF_CHECKS]
    # The gaps learner-text gaps named from each missed answer (RW1b's
    # reader_formative texts), as the record's hypotheses.
    gaps = named_gaps(repository, [str(row["id"]) for row in missed], source_kind="reader_formative")
    for row in missed:
        spans = tuple(_span_list(row["anchor_span_ids_json"]) or _span_list(row["span_ids_json"]))
        records.append(ReaderObservationV1(
            kind=FORMATIVE_STYLE_KINDS[row["question_style"]],
            source_event_ids=(str(row["id"]),),
            span_ids=spans,
            observed={"self_check": row["self_check"], "style": row["question_style"]},
            observed_at=str(row["answered_at"]),
            facet_candidates=(
                _span_learning_objects(vault, repository, extraction_id, spans) if vault is not None else ()
            ),
            hypotheses=tuple(g["gap_id"] for g in gaps.get(str(row["id"]), [])),
        ))
    return records


def prediction_observations(repository: Any, *, extraction_id: str, session: ReaderSession) -> list[ReaderObservationV1]:
    """RW5a: missed figure predictions. ``figure_predictions`` does not exist
    until RW5a's migration; the read then returns its missed rows."""

    if not _has_table(repository, "figure_predictions"):
        return []
    with repository.connection() as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(figure_predictions)")}
        if not {"id", "extraction_id", "matched", "created_at"} <= columns:
            return []
        rows = connection.execute(
            "SELECT id, created_at FROM figure_predictions WHERE extraction_id = ? AND matched = 0 "
            "ORDER BY created_at, id",
            (extraction_id,),
        ).fetchall()
    return [
        ReaderObservationV1(
            kind="prediction_missed", source_event_ids=(str(row["id"]),), span_ids=(),
            observed={"matched": False}, observed_at=str(row["created_at"]),
        )
        for row in rows if session.contains(row["created_at"])
    ]


def observations_for_session(
    vault: Any, repository: Any, *, extraction_id: str, session: ReaderSession,
    exchanges: Sequence[Mapping[str, Any]] | None = None,
) -> list[ReaderObservationV1]:
    """Every formative record of one session, in time order (deterministic)."""

    records = (
        still_unclear_observations(vault, repository, extraction_id=extraction_id, session=session,
                                   exchanges=exchanges)
        + formative_answer_observations(repository, extraction_id=extraction_id, session=session, vault=vault)
        + prediction_observations(repository, extraction_id=extraction_id, session=session)
    )
    return sorted(records, key=lambda r: (r.observed_at, OBSERVATION_KINDS.index(r.kind), r.source_event_ids))


__all__ = [
    "FORMATIVE_STYLE_KINDS",
    "OBSERVATION_KINDS",
    "ROUTING_ONLY",
    "ReaderObservationV1",
    "formative_answer_observations",
    "formative_answers",
    "named_gaps",
    "observations_for_session",
    "prediction_observations",
    "still_unclear_observations",
]
