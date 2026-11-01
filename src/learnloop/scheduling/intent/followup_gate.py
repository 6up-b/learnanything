"""The serve-time gate of Reader RW6b's automatic follow-ups (Codex review F1, F11).

A follow-up (a ``test_me_later`` commitment whose provenance says
``via: reader_followup``) was valued as an independent check when it was
planned. Before DL2 serves it cold, two facts are re-checked here, with no
model call:

* **exposure since valuation** (F1): the sources spec's exposure rule at
  serve (``db.stores.source_service.serve_time_exposure``: an attempt on the
  item since the valuation, a reveal on it or its family, source text shown from its span or
  its book solution, an impression from any proposal, and a studied worked example the judge called
  ``equivalent``/``related`` or never judged), counted from the later of the
  valuation and the cold delay's start. A ``related`` worked example is a
  label for a ``discriminate`` check (the valuation's own rule), never an
  exclusion there;
* **repair ownership** (F11): a retention follow-up yields to a repair
  ``cold_retry`` still pending (or served) that assesses one of its facets
  (:func:`owning_retry`, the one rule RW6b's creation and re-valuation use too).

A check several questions license (RW6b round 3) is judged by the STRICTEST
rule across ALL its licensing questions, answered or not (round 6): the
exposure reasons of every licensing intent together (a ``related`` worked
example excludes it when any licensing question is a retention one), and
repair ownership only when a repair owns every one. The gate never reads
answered state: over-holding is re-valued (kept or retired with a reason),
under-holding would serve an exposed check cold. The licensing questions are
the check's own ``chosen`` line's ``licensing`` list, written at publication
and changed in the same transaction as the line; nothing is looked up in the
receipt's question entries. A follow-up whose digest row or chosen line is
missing or inconsistent is held (fail closed).

A gated candidate is held (never administered cold; DL2 serves nothing for it
today) and the next daily re-valuation retires the check with its reason and
re-asks every licensing question. Pure reads; nothing is persisted here.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from datetime import datetime
from typing import Any

from learnloop.clock import parse_utc

VIA = "reader_followup"
#: Reasons that stand as a label, not an exclusion, for a discriminating check
#: (the exposure rule's ``related`` worked example; sources spec §5.4).
_LABEL_ONLY_FOR_DISCRIMINATE = frozenset({"related_worked_example"})
REPAIR_RETRY_OWNS = "repair_retry_owns"


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def independent_reasons(reasons: Iterable[str], *, intent: str,
                        studied: Mapping[str, str | None] | None = None) -> list[str]:
    """The exposure reasons that exclude an independent check of ``intent``.

    ``studied`` is the exposure rule's ``studied_worked_examples`` (each
    studied example's verdict, None when never judged). The rule reports one
    worked-example reason, the strongest; when a ``related`` example (only a
    label for a discriminating check) is dropped, another studied example
    nobody judged still excludes it (``worked_example_unjudged``; Codex
    re-review F1)."""

    kept = [str(reason) for reason in reasons]
    if intent == "discriminate":
        dropped = [reason for reason in kept if reason in _LABEL_ONLY_FOR_DISCRIMINATE]
        kept = [reason for reason in kept if reason not in _LABEL_ONLY_FOR_DISCRIMINATE]
        if dropped and studied and any(verdict is None for verdict in studied.values()):
            kept.append("worked_example_unjudged")
    return kept


def _facets(vault: Any, item: Any) -> set[str]:
    return {vault.canonical_facet_id(str(facet)) for facet in getattr(item, "evidence_facets", ()) or ()}


def owning_retry(vault: Any, rows: Sequence[Mapping[str, Any]], *, facet_id: str, attempt_ids: Iterable[str],
                 learning_object_ids: Iterable[str]) -> Mapping[str, Any] | None:
    """The repair ``cold_retry`` that owns this claim, or None (F11).

    A retry owns a facet when the item it measures assesses that facet: on the
    claim's own attempt (its ``source_attempt_id``), or on an item of the
    claim's learning objects. A retry whose item is not chosen yet owns what
    its source attempt touched (it cannot be told apart)."""

    facet = vault.canonical_facet_id(facet_id)
    attempts = {str(a) for a in attempt_ids}
    los = set(learning_object_ids)
    for row in rows:
        item = vault.practice_items.get(str(row.get("selected_item_id") or ""))
        same_attempt = bool(row.get("source_attempt_id")) and str(row["source_attempt_id"]) in attempts
        if item is None:
            if same_attempt:
                return row
            continue
        if facet not in _facets(vault, item):
            continue
        if same_attempt or item.learning_object_id in los:
            return row
    return None


def open_cold_retries(connection: Any, *, now: datetime) -> list[dict[str, Any]]:
    """Repair cold retries still pending or served (unexpired), oldest first."""

    return [dict(row) for row in connection.execute(
        "SELECT id, source_attempt_id, selected_item_id, not_before, expires_at, created_at FROM followup_tasks "
        "WHERE kind = 'cold_retry' AND status IN ('pending', 'served') "
        "AND (expires_at IS NULL OR expires_at >= ?) ORDER BY not_before, id", (_iso(now),)).fetchall()]


def _primary(provenance: Mapping[str, Any]) -> dict[str, Any]:
    question = provenance.get("question") or {}
    return {"key": str((provenance.get("valuation_ref") or {}).get("question") or ""),
            "intent": str(question.get("intent") or "retention"), "purpose": provenance.get("purpose"),
            "facet_ids": list(question.get("facet_ids") or []),
            "learning_object_ids": list(question.get("learning_object_ids") or []),
            "attempt_ids": list(provenance.get("attempt_ids") or [])}


#: The check's digest row or its ``chosen`` line is missing or inconsistent:
#: the check is held, and re-valuation retires and re-asks it (fail closed).
LICENSING_UNREADABLE = "licensing_unreadable"


def _shape(entry: Mapping[str, Any]) -> dict[str, Any]:
    """A licensing question as the gate reads it (a line's ``licensing`` entry or a caller's)."""

    return {"key": str(entry.get("question") or entry.get("key") or ""),
            "intent": str(entry.get("intent") or "retention"), "purpose": entry.get("purpose"),
            "facet_ids": list(entry.get("facet_ids") or []),
            "learning_object_ids": list(entry.get("learning_object_ids") or []),
            "attempt_ids": list(entry.get("attempt_ids") or [])}


def line_licensing(line: Mapping[str, Any], provenance: Mapping[str, Any]) -> list[dict[str, Any]] | None:
    """The licensing questions a ``chosen`` line carries, or None when the
    line is inconsistent (a malformed ``licensing`` list, or several
    questions named without one). An empty list falls back to the
    provenance's own question."""

    licensing = line.get("licensing")
    if licensing is None:
        # A line written before the list existed names its one question.
        return [_primary(provenance)]
    if not isinstance(licensing, list) or any(
            not isinstance(entry, Mapping) or not entry.get("question") or not entry.get("intent")
            for entry in licensing):
        return None
    return [_shape(entry) for entry in licensing] or [_primary(provenance)]


def licensing_questions(connection: Any, provenance: Mapping[str, Any], commitment_id: str | None,
                        item_id: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
    """ALL the questions that license this check (round 6), read from its own
    ``chosen`` line, and ``LICENSING_UNREADABLE`` when the digest row or the
    line is missing or inconsistent (the caller holds the check). Without a
    commitment id: the provenance's question."""

    primary = _primary(provenance)
    if not commitment_id:
        return [primary], None
    from learnloop.db.stores.reader_digests import digest_for_commitment

    row = digest_for_commitment(connection, str(commitment_id))
    line = next((entry for entry in ((row or {}).get("valuation") or {}).get("chosen") or []
                 if str(entry.get("commitment_id") or "") == str(commitment_id)), None)
    if line is None or (item_id is not None and str(line.get("ref") or "") != str(item_id)):
        return [primary], LICENSING_UNREADABLE
    found = line_licensing(line, provenance)
    if found is None:
        return [primary], LICENSING_UNREADABLE
    return found, None


def followup_gate(vault: Any, repository: Any, *, item_id: str, provenance: Mapping[str, Any], valued_at: str,
                  now: datetime, commitment_id: str | None = None,
                  questions: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any] | None:
    """Why a reader follow-up may not be served cold now, or None (it may).

    ``None`` too for any other commitment: only RW6b's automatic checks pass
    through here. ``questions`` (``licensing`` entries) are ALL the check's
    licensing questions when the caller already read its line (re-valuation);
    otherwise they are read from its ``chosen`` line by ``commitment_id``
    (:func:`licensing_questions`). The strictest rule across them applies,
    answered or not (round 6); with one question, its own rule."""

    if provenance.get("via") != VIA:
        return None
    from learnloop.db.connection import connect
    from learnloop.db.stores.source_service import book_solution_span_ids, exercise_key, serve_time_exposure
    from learnloop.serve_eligibility import COLD_RETRIEVAL_DELAY

    item = vault.practice_items.get(item_id)
    valued = parse_utc(valued_at)
    window = now - COLD_RETRIEVAL_DELAY
    since = _iso(max(valued, window) if valued is not None else window)
    family = ({other.id for other in vault.practice_items.values() if other.family_id == item.family_id}
              if item is not None and item.family_id else set())
    canonical = getattr(item, "canonical_exercise", None) if item is not None else None
    scope = provenance.get("exposure_scope_extraction_ids")
    extraction_id = canonical.extraction_id if canonical is not None else None
    span_ids = [str(span) for span in canonical.span_ids] if canonical is not None else []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        # An imported exercise: its book solution is its source text too, and
        # the judge may have judged it under its pre-import key (rules 3 and
        # 4 as the valuation and the diagnosis follow-up apply them; F1).
        verdict = serve_time_exposure(
            connection, practice_item_id=item_id, family_item_ids=family, extraction_id=extraction_id,
            span_ids=span_ids, solution_span_ids=book_solution_span_ids(connection, item_id),
            candidate_keys=[exercise_key(str(extraction_id), span_ids)] if extraction_id else (),
            studied_extraction_ids=None if scope is None else [str(value) for value in scope],
            since=since)
        unreadable = None
        if questions is not None:
            licensing = [_shape(q) for q in questions]
        else:
            licensing, unreadable = licensing_questions(connection, provenance, commitment_id, item_id)
        licensing = licensing or [_primary(provenance)]
        retries = (open_cold_retries(connection, now=now)
                   if all(q.get("purpose") == "retention" for q in licensing) else [])
        attempted_since = connection.execute(
            "SELECT 1 FROM practice_attempts WHERE practice_item_id = ? AND created_at >= ? LIMIT 1",
            (item_id, valued_at or "")).fetchone() is not None
    # The strictest rule across ALL licensing questions (round 6), the
    # reasons of every intent together (one question: its own rule).
    studied = (verdict.get("inputs") or {}).get("studied_worked_examples")
    reasons: list[str] = []
    for intent in dict.fromkeys(str(q.get("intent") or "retention") for q in licensing):
        for reason in independent_reasons(verdict.get("reasons") or (), intent=intent, studied=studied):
            if reason not in reasons:
                reasons.append(reason)
    if "attempted" in reasons and not attempted_since:
        # Rule 1 counts any attempt; one before the valuation was the
        # valuation's to weigh (``unattempted_only``), not an exposure since.
        reasons.remove("attempted")
    # A repair owns the check only when it owns every licensing question
    # (each a retention claim); the first owner found is named.
    owner = None
    for q in licensing if retries else ():
        found = None
        for facet in q.get("facet_ids") or ():
            found = owning_retry(vault, retries, facet_id=str(facet), attempt_ids=q.get("attempt_ids") or (),
                                 learning_object_ids=q.get("learning_object_ids") or ())
            if found is not None:
                break
        if found is None:
            owner = None
            break
        owner = owner or found
    if owner is not None:
        reasons.append(REPAIR_RETRY_OWNS)
    if unreadable is not None:
        reasons.append(unreadable)  # fail closed (F17)
    if not reasons:
        return None
    return {"reasons": reasons, "since": since, "exposure": verdict,
            "followup_task_id": None if owner is None else owner.get("id")}


__all__ = ["LICENSING_UNREADABLE", "REPAIR_RETRY_OWNS", "VIA", "followup_gate", "independent_reasons",
           "licensing_questions", "line_licensing", "open_cold_retries", "owning_retry"]
