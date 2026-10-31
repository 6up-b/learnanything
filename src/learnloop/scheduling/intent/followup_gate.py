"""The serve-time gate of Reader RW6b's automatic follow-ups (Codex review F1, F11).

A follow-up (a ``test_me_later`` commitment whose provenance says
``via: reader_followup``) was valued as an independent check when it was
planned. Before DL2 serves it cold, two facts are re-checked here, with no
model call:

* **exposure since valuation** (F1): the sources spec's exposure rule at
  serve (``db.stores.source_service.serve_time_exposure``: an attempt on the
  item, a reveal on it or its family, source text shown from its span, an
  impression from any proposal, and a studied worked example the judge called
  ``equivalent``/``related`` or never judged), counted from the later of the
  valuation and the cold delay's start. A ``related`` worked example is a
  label for a ``discriminate`` check (the valuation's own rule), never an
  exclusion there;
* **repair ownership** (F11): a retention follow-up yields to a repair
  ``cold_retry`` still pending (or served) that assesses one of its facets
  (:func:`owning_retry`, the one rule RW6b's creation and re-valuation use too).

A gated candidate is held (never administered cold; DL2 serves nothing for it
today) and the next daily re-valuation retires the check with its reason and
re-asks the question. Pure reads; nothing is persisted here.
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


def independent_reasons(reasons: Iterable[str], *, intent: str) -> list[str]:
    """The exposure reasons that exclude an independent check of ``intent``."""

    kept = [str(reason) for reason in reasons]
    if intent == "discriminate":
        kept = [reason for reason in kept if reason not in _LABEL_ONLY_FOR_DISCRIMINATE]
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


def followup_gate(vault: Any, repository: Any, *, item_id: str, provenance: Mapping[str, Any], valued_at: str,
                  now: datetime) -> dict[str, Any] | None:
    """Why a reader follow-up may not be served cold now, or None (it may).

    ``None`` too for any other commitment: only RW6b's automatic checks pass
    through here."""

    if provenance.get("via") != VIA:
        return None
    from learnloop.db.connection import connect
    from learnloop.db.stores.source_service import serve_time_exposure
    from learnloop.serve_eligibility import COLD_RETRIEVAL_DELAY

    question = provenance.get("question") or {}
    intent = str(question.get("intent") or "retention")
    item = vault.practice_items.get(item_id)
    valued = parse_utc(valued_at)
    window = now - COLD_RETRIEVAL_DELAY
    since = _iso(max(valued, window) if valued is not None else window)
    family = ({other.id for other in vault.practice_items.values() if other.family_id == item.family_id}
              if item is not None and item.family_id else set())
    canonical = getattr(item, "canonical_exercise", None) if item is not None else None
    scope = provenance.get("exposure_scope_extraction_ids")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        verdict = serve_time_exposure(
            connection, practice_item_id=item_id, family_item_ids=family,
            extraction_id=canonical.extraction_id if canonical is not None else None,
            span_ids=list(canonical.span_ids) if canonical is not None else (),
            studied_extraction_ids=None if scope is None else [str(value) for value in scope],
            since=since)
        retries = open_cold_retries(connection, now=now) if provenance.get("purpose") == "retention" else []
    reasons = independent_reasons(verdict.get("reasons") or (), intent=intent)
    owner = None
    for facet in question.get("facet_ids") or ():
        owner = owning_retry(vault, retries, facet_id=str(facet), attempt_ids=provenance.get("attempt_ids") or (),
                             learning_object_ids=question.get("learning_object_ids") or ())
        if owner is not None:
            break
    if owner is not None:
        reasons.append(REPAIR_RETRY_OWNS)
    if not reasons:
        return None
    return {"reasons": reasons, "since": since, "exposure": verdict,
            "followup_task_id": None if owner is None else owner.get("id")}


__all__ = ["REPAIR_RETRY_OWNS", "VIA", "followup_gate", "independent_reasons", "open_cold_retries", "owning_retry"]
