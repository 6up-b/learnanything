"""Read-only interaction derivation. No model, evidence, or repository writes.

``interaction-signals-v1`` chooses a conservative 0.3 mass per subject/LO/UTC
day (D12 does not specify a number). Missing timing is NOT evidence of help
before work: only an explicitly logged zero, or the practice screen's explicit
"no work yet" marker (``attempt_progress = "no_draft"``), qualifies.

A stuck answer (``mvp-0.13``) whose CURRENT grader reading (its
``stuck_reading`` judgment, blind or joint) describes confusion is one more
signal of the same kind: a ``stuck_confusion`` row on
the item's LO. It is already graded as an attempt, so it carries no outcome
and no mass (no double counting); it only blocks fast-track, like a confused
question.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import logging
import math
from typing import Any

from learnloop.attempts.stuck import stuck_answers
from learnloop.field.types import AttemptRow, SignalRow

SIGNAL_VERSION = "interaction-signals-v1"
DAILY_SIGNAL_MASS_CAP = 0.3
QUESTION_TYPES = frozenset({
    "prerequisite", "mechanism", "clarification", "strategy", "verification", "other",
})
# question_events.attempt_progress as the practice screen logs it: the learner
# had typed nothing when they asked ("no_draft") or had started a draft
# ("draft_started"). The screen logs elapsed time in fractional seconds, so an
# exact zero almost never holds; this marker is the explicit "no work yet".
ATTEMPT_PROGRESS_NO_WORK = "no_draft"
#: A stuck answer the grader read as describing confusion (mvp-0.13).
STUCK_CONFUSION_SIGNAL = "stuck_confusion"
logger = logging.getLogger(__name__)


def instant(value: str) -> datetime:
    """Normalize ISO timestamps, including legacy naive UTC values."""
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)


def _list(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return []
    return list(dict.fromkeys(x for x in (value or []) if isinstance(x, str) and x)) if isinstance(value, (list, tuple)) else []


def normalize_question(event: Mapping[str, Any], *, reader: bool = False) -> dict[str, Any]:
    """Flatten logged reader payloads without inventing a type or LO mapping."""
    row = dict(event)
    payload = row.get("payload", row.get("payload_json")) or {}
    if isinstance(payload, str):
        payload = json.loads(payload)
    row = {**payload, **row}
    source = row.get("source_context") or row.get("source_context_json") or {}
    if isinstance(source, str):
        source = json.loads(source)
    if not (row.get("lo_ids") or row.get("lo_ids_json") or row.get("lo_id")):
        row["lo_ids"] = _list(source.get("candidate_learning_object_ids"))
    # Question-time facet -> LO mapping, persisted with the tutor's answer
    # (review F4) and grounded in the question's own item, note or declared
    # prerequisites (review F11). Immutable once logged; never today's facet
    # membership. Each mapped target carries its subject as of the question.
    mapping = source.get("facet_learning_object_ids")
    row["_question_time_facet_los"] = (
        {str(f): _list(los) for f, los in mapping.items()} if isinstance(mapping, Mapping) else {}
    )
    subjects = source.get("learning_object_subject_ids")
    row["_question_time_lo_subjects"] = (
        {str(lo): str(subject) for lo, subject in subjects.items() if isinstance(subject, str) and subject}
        if isinstance(subjects, Mapping) else {}
    )
    row["event_kind"] = "interaction_event" if reader or row.get("kind") == "learner_question_asked" else "question_event"
    row["context"] = row.get("context") or ("library" if row["event_kind"] == "interaction_event" else "")
    return row


def _question_time_targets(row: Mapping[str, Any], facets: Iterable[str]) -> list[str]:
    """LOs a logged facet mapped to when the question was asked (sorted)."""
    mapping = row.get("_question_time_facet_los") or {}
    return sorted({lo for facet in facets for lo in mapping.get(facet, ())})


def classification_input(event: Mapping[str, Any]) -> dict[str, Any]:
    """Whitelist question-time inputs; never include tutor answers/later grades.

    ``lo_ids`` are the logged targets: explicit LO ids, else the LOs the logged
    facets mapped to at question time. Empty means the LO mapping is missing.
    """
    row = normalize_question(event)
    facets = _list(row.get("facets_json", row.get("facets")))
    return {
        "id": row["id"], "event_kind": row["event_kind"],
        "question_md": row.get("question_md", ""),
        "context": row["context"],
        "question_type": row.get("question_type"),
        "facets": facets,
        "lo_ids": (
            _list(row.get("lo_ids_json", row.get("lo_ids")))
            or ([row["lo_id"]] if row.get("lo_id") else [])
            or _question_time_targets(row, facets)
        ),
        "source_id": row.get("source_id"),
        "extraction_id": row.get("extraction_id"),
        "span_id": row.get("span_id"),
    }


def input_hash(event: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(classification_input(event), sort_keys=True).encode()).hexdigest()


def _facet_los(mapping: Mapping[str, Any], facet: str) -> tuple[str, ...]:
    value = mapping.get(facet, ())
    return (value,) if isinstance(value, str) else tuple(value)


def derive_interaction_signals(
    question_events: Iterable[Mapping[str, Any]],
    interaction_events: Iterable[Mapping[str, Any]],
    attempts: Iterable[AttemptRow],
    *,
    facet_to_lo: Mapping[str, str | tuple[str, ...]],
    cached_classifications: Iterable[Mapping[str, Any]] = (),
    daily_mass_cap: float = DAILY_SIGNAL_MASS_CAP,
    lo_to_subject: Mapping[str, str] | None = None,
    diagnostics: dict[str, Any] | None = None,
    stuck_confusions: Iterable[Mapping[str, Any]] = (),
) -> tuple[SignalRow, ...]:
    """Derive immutable rows using logged data and already-paid classifications.

    Classifications supply ONLY missing fields. Their availability is their
    creation time, not the historical question time. Feedback dependent on a
    correct grade is available no earlier than that grade. Prerequisite targets
    come from mapped question facets, never from the item's own LO by fallback.
    Multi-target questions split one question's mass across their target LOs.
    ``facet_to_lo`` may contain only immutable historical mapping evidence,
    never current vault membership. Explicit targets override facet mappings.
    ``lo_to_subject`` is retained for compatibility but cannot retarget history.
    ``stuck_confusions`` are :func:`learnloop.attempts.stuck.stuck_answers`
    rows; each one whose current reading describes confusion becomes a
    ``stuck_confusion`` row on the attempt's own LO, available once the
    reading existed, with no outcome and no mass.
    """
    if not math.isfinite(daily_mass_cap) or daily_mass_cap < 0:
        raise ValueError("daily_mass_cap must be finite and nonnegative")
    attempts = tuple(attempts)
    by_attempt = {a.attempt_id: a for a in attempts}
    cache: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for raw in sorted(cached_classifications, key=lambda c: (instant(c["created_at"]), c["id"])):
        c = dict(raw)
        kind = "question_event" if c.get("question_event_id") else "interaction_event"
        event_id = c.get("question_event_id") or c.get("interaction_event_id")
        # First paid proposal is the historical input. A later rerun/model
        # must not retroactively replace what was available to an earlier arm.
        cache.setdefault((kind, event_id, c["input_hash"]), c)
    events = [normalize_question(e) for e in question_events]
    events += [normalize_question(e, reader=True) for e in interaction_events if e["kind"] == "learner_question_asked"]
    signals: list[SignalRow] = []
    unmapped = 0
    for event in events:
        event_id = event["id"]
        kind = event["event_kind"]
        observed = event.get("received_at") or event["created_at"]
        logged_at = observed
        qtype = event.get("question_type")
        no_work_yet = _logged_no_work_yet(event)
        logged_before = no_work_yet and (
            bool(event.get("hint_equivalent")) or qtype in {"prerequisite", "mechanism", "clarification", "strategy"}
        )
        facets = _list(event.get("facets_json", event.get("facets")))
        los = _list(event.get("lo_ids_json", event.get("lo_ids")))
        if event.get("lo_id"):
            los.append(event["lo_id"])
        if not los:
            # Logged facets resolve through the mapping persisted at question
            # time; only an unresolved mapping is left to a paid classification.
            los = _question_time_targets(event, facets)
        lookup = {**facet_to_lo, **event["_question_time_facet_los"]}
        classification = cache.get((kind, event_id, event.get("_classification_input_hash") or input_hash(event)))
        if classification and (not qtype or not los):
            qtype = qtype or classification["question_type"]
            if not los:
                facets = facets or _list(classification["facets_json"])
                los = _list(classification["lo_ids_json"])
            observed = max((observed, classification["created_at"]), key=instant)
        los = sorted(set(los) if los else {lo for f in facets for lo in _facet_los(lookup, f)})
        if not los:
            unmapped += 1
        attempt = by_attempt.get(event.get("attempt_id"))
        help_requested = bool(event.get("hint_equivalent")) or qtype in {
            "prerequisite", "mechanism", "clarification", "strategy",
        }
        before = help_requested and no_work_yet
        leak = bool(event.get("leak_suspected") or event.get("answer_revealed"))
        if attempt is not None and event.get("context") == "practice" and (
            leak or logged_before or event.get("hint_equivalent")
        ):
            # Explicit pre-result provenance survives coarse timestamp ties.
            # Only logged facts belong here, never a later paid classification.
            signals.append(SignalRow(
                signal_id=f"{kind}:{event_id}:assistance", lo_id=attempt.lo_id,
                observed_at=logged_at, signal_type="practice_assistance",
                subject_id=attempt.features.subject_id, attempt_id=attempt.attempt_id,
                help_before_work=logged_before,
                leak_suspected=leak,
            ))
        outcome, mass = None, 0.0
        signal_type = qtype or "unclassified"
        if qtype == "prerequisite":
            outcome, mass = 0.0, 0.15
        elif qtype in {"mechanism", "clarification"}:
            if event.get("context") == "feedback" and attempt is not None and attempt.outcome == 1:
                outcome, mass = 0.5, 0.1
                observed = max((observed, attempt.observed_at), key=instant)
            elif event.get("context") in {"library", "reader"}:
                signal_type = "reader_confusion"
        elif qtype == "strategy" and before:
            signal_type = "hint"
        # Preserve assistance/leak telemetry even when there is no target
        # classification. This is not a prerequisite mapping fallback.
        if not los and attempt is not None and (before or leak or event.get("hint_equivalent")):
            los = [attempt.lo_id]
            outcome, mass = None, 0.0
        for lo in los:
            signals.append(SignalRow(
                signal_id=f"{kind}:{event_id}:{lo}", lo_id=lo,
                observed_at=observed, signal_type=signal_type, outcome=outcome,
                effective_mass=mass / len(los),
                subject_id=_target_subject(event, lo, attempt),
                facet_id=next((f for f in facets if lo in _facet_los(lookup, f)), None),
                attempt_id=event.get("attempt_id"), help_before_work=before,
                leak_suspected=leak,
            ))
    for attempt in attempts:
        if attempt.hints_used > 0:
            before = attempt.help_before_work or any(
                s.attempt_id == attempt.attempt_id and s.help_before_work
                and _available_for_attempt(s, attempt) for s in signals
            )
            outcome = min(attempt.outcome, max(0.2, 1.0 - 0.2 * attempt.hints_used))
            if before:
                outcome = min(outcome, 0.3)
            signals.append(SignalRow(
                signal_id=f"hint:{attempt.attempt_id}", lo_id=attempt.lo_id,
                observed_at=attempt.observed_at, signal_type="hint", outcome=outcome,
                subject_id=attempt.features.subject_id, attempt_id=attempt.attempt_id,
                help_before_work=before,
            ))
    stuck_rows = 0
    for stuck in stuck_confusions:
        if not stuck.get("describes_confusion"):
            continue
        stuck_rows += 1
        observed = max(
            (str(stuck["created_at"]), str(stuck.get("graded_at") or stuck["created_at"])),
            key=instant,
        )
        signals.append(SignalRow(
            signal_id=f"stuck:{stuck['attempt_id']}", lo_id=str(stuck["learning_object_id"]),
            observed_at=observed, signal_type=STUCK_CONFUSION_SIGNAL,
            subject_id=str(stuck.get("subject_id") or "default"),
            attempt_id=str(stuck["attempt_id"]),
        ))
    used: dict[tuple[str, str, str], float] = defaultdict(float)
    result = []
    for signal in sorted(signals, key=lambda s: (instant(s.observed_at), s.signal_id)):
        key = signal.subject_id, signal.lo_id, instant(signal.observed_at).date().isoformat()
        mass = min(signal.effective_mass, max(0.0, daily_mass_cap - used[key]))
        used[key] += mass
        result.append(replace(signal, effective_mass=mass))
    logger.info(
        "Interaction mapping: %d questions, %d unmapped", len(events), unmapped,
        extra={"interaction_questions": len(events), "interaction_unmapped": unmapped},
    )
    if diagnostics is not None:
        diagnostics.update(
            version=SIGNAL_VERSION, questions=len(events), unmapped_questions=unmapped,
            signal_rows=len(result), weak_observations=sum(s.effective_mass > 0 for s in result),
            cache_entries_considered=len(cache), daily_mass_cap=daily_mass_cap,
            stuck_confusion_rows=stuck_rows,
        )
    return tuple(result)


def _logged_no_work_yet(event: Mapping[str, Any]) -> bool:
    """A practice question logged as asked before any work (spec §3.1).

    Only explicit logging counts: an exact zero ``seconds_into_attempt`` or the
    practice screen's ``no_draft`` marker. Missing or late timing does not."""
    return event.get("context") == "practice" and (
        event.get("seconds_into_attempt") == 0
        or event.get("attempt_progress") == ATTEMPT_PROGRESS_NO_WORK
    )


def _target_subject(event: Mapping[str, Any], lo: str, attempt: AttemptRow | None) -> str:
    """A mapped target keeps its own subject, not the asking item's (review F11).

    The linked attempt's own LO keeps the attempt's subject, so its rows meet the
    attempt rows. Another target uses the subject recorded with the question's
    mapping. Without one (an explicit or classifier-supplied LO), the logged
    fallback is unchanged: the linked attempt's subject, else the event's own.
    """
    if attempt is not None and lo == attempt.lo_id:
        return attempt.features.subject_id
    recorded = event["_question_time_lo_subjects"].get(lo)
    if recorded:
        return recorded
    return attempt.features.subject_id if attempt else (
        event.get("learner_subject_id") or event.get("subject_id") or "default"
    )


def load_interaction_signals(
    connection: Any, vault: Any, attempts: Iterable[AttemptRow],
    *, diagnostics: dict[str, Any] | None = None,
) -> tuple[SignalRow, ...]:
    """Read logged mappings and paid outputs, never today's authored model.

    Current facets, aliases, subjects and source provenance are mutable, even
    when an object's updated_at predates an event. Without an immutable mapping
    snapshot they cannot resolve historical questions. Unmapped questions are
    counted in the derivation log, not guessed from present-day content.
    """
    def rows(table: str) -> list[dict[str, Any]]:
        cursor = connection.execute(f"SELECT * FROM {table}")
        names = [c[0] for c in cursor.description]
        return [dict(zip(names, row, strict=True)) for row in cursor]

    questions = _link_practice_questions(connection, rows("question_events"))
    readers = [r for r in rows("interaction_events") if r["kind"] == "learner_question_asked"]
    # Read-only reports also open pre-classifier vaults; never migrate them just
    # to discover that no paid classifications are available.
    has_cache = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='question_classifications'"
    ).fetchone()
    cached = rows("question_classifications") if has_cache else ()
    return derive_interaction_signals(
        questions, readers, attempts,
        facet_to_lo={}, cached_classifications=cached, diagnostics=diagnostics,
        # mvp-0.13: graded stuck answers the grader read as confusion. Read
        # from the persisted flag and the reading's judgment, never config.
        stuck_confusions=stuck_answers(connection),
    )


def _link_practice_questions(connection: Any, questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Link a practice-screen question to the attempt it preceded (review F5).

    The practice screen asks before the attempt exists, so its row carries the
    item and session but no ``attempt_id``. Submission counts such a question
    as a hint equivalent of the NEXT attempt on the item when that attempt is
    in the question's session (``tutor_qa.hint_equivalents_for_submission``:
    after the previous attempt on the item, at or before this one). The same
    window over the two immutable ledgers supplies the link here. Explicit
    links and other contexts are left as logged.
    """
    pending = [
        q for q in questions
        if not q.get("attempt_id") and q.get("context") == "practice" and q.get("practice_item_id")
    ]
    if not pending or connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='practice_attempts'"
    ).fetchone() is None:
        return questions
    by_item: dict[str, list[tuple[datetime, str, str | None]]] = defaultdict(list)
    for attempt_id, item_id, session_id, created_at in connection.execute(
        "SELECT id, practice_item_id, session_id, created_at FROM practice_attempts"
    ):
        by_item[item_id].append((instant(created_at), attempt_id, session_id))
    for attempts in by_item.values():
        attempts.sort()
    pending_ids = {id(q) for q in pending}
    linked = []
    for question in questions:
        if id(question) in pending_ids:
            asked = instant(question["created_at"])
            following = next((a for a in by_item.get(question["practice_item_id"], ()) if a[0] >= asked), None)
            if following is not None and following[2] in (None, question.get("session_id")):
                question = {**question, "attempt_id": following[1]}
        linked.append(question)
    return linked


def _available_for_attempt(signal: SignalRow, attempt: AttemptRow) -> bool:
    """At tied timestamps only linked, logged practice assistance precedes the result."""
    observed, completed = instant(signal.observed_at), instant(attempt.observed_at)
    return observed < completed or (
        observed == completed and signal.attempt_id == attempt.attempt_id
        and signal.signal_type == "practice_assistance"
    )


def enrich_attempts(attempts: Iterable[AttemptRow], signals: Iterable[SignalRow]) -> tuple[AttemptRow, ...]:
    """Add predictor-only covariates without future-question leakage.

    Grade-time hint counts are an outcome covariate, not a prediction feature.
    Only linked, already-available signals change this attempt's assistance and
    cold flags. Questions on the same LO can mark the chronological split.
    """
    signals = tuple(signals)
    result = []
    for attempt in attempts:
        available = [s for s in signals if _available_for_attempt(s, attempt)]
        prior = [s for s in available if s.lo_id == attempt.lo_id and s.subject_id == attempt.features.subject_id]
        linked = [s for s in available if s.attempt_id == attempt.attempt_id]
        leaked = any(s.leak_suspected for s in linked)
        result.append(replace(
            attempt,
            features=replace(attempt.features, cold=False) if leaked else attempt.features,
            # A suspected answer leak also voids the strict memory coldness.
            retrieval_cold=attempt.retrieval_cold and not leaked,
            help_before_work=attempt.help_before_work or any(s.help_before_work for s in linked),
            # A stuck answer is an attempt, not a question: it never marks a
            # later attempt as preceded by one (report strata stay as before).
            preceded_by_question=attempt.preceded_by_question or any(
                not s.signal_id.startswith(("hint:", "stuck:")) for s in prior
            ),
        ))
    return tuple(result)


# Help or confusion on an LO: it is taught first and never fast-tracked on early
# answers alone (spec §3.1). Curiosity (`other`, `verification`) never blocks.
# A stuck answer that says what is confusing (mvp-0.13) is confusion too.
FAST_TRACK_BLOCKING_TYPES = frozenset({
    "prerequisite", "mechanism", "clarification", "strategy", "reader_confusion", "hint",
    STUCK_CONFUSION_SIGNAL,
})


def blocks_fast_track(signal: SignalRow) -> bool:
    """The one report-2 blocking rule, shared by the harness and the helper below."""
    return bool(
        signal.help_before_work or signal.leak_suspected
        or signal.signal_type in FAST_TRACK_BLOCKING_TYPES
    )


def confusion_blocks_fast_track(
    signals: Iterable[SignalRow], *, lo_id: str, as_of: str,
    subject_id: str = "default", self_report_known: bool = False,
) -> bool:
    """Pure report-2 eligibility only; does not implement or mutate F2 routing."""
    if self_report_known:
        return False
    return any(
        s.lo_id == lo_id and s.subject_id == subject_id
        and instant(s.observed_at) <= instant(as_of)
        and blocks_fast_track(s)
        for s in signals
    )
