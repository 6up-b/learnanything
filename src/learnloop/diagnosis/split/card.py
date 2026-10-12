"""The M2 diagnosis card (Slice 1 §12.2).

Shown in the feedback view when the asynchronous diagnosis arrives:

* the diagnosis summary in plain language;
* its repair suggestion(s);
* "You've made this mistake before": ONLY validated citations (S4), each with
  its date and blind grade, omitted when none validated;
* the prerequisite-gap hypothesis, if any, labelled "possible cause - not yet
  checked".

At most one optional tap, in a fixed neutral order, using the existing
self-report vocabulary plus two card-only values. Every tap is an eval-only
``diagnosis_feedback`` row (no support authority, invariant 12). With an open
unresolved-cause factor, ``believed_candidate`` / ``slipped`` /
``diagnosis_wrong`` are also forwarded to that factor's existing self-report
channel (O14; ``diagnosis.forward_card_taps``). A per-citation "not the same
mistake" tap is also a learner ``same_cause`` verdict in ``judgment_ledger``.

Slice 2 T1 (``mvp-0.11``): when the diagnosis's cause has recurred K times,
the card also shows the escalated repair with the earlier answers as its
evidence ("Third time with this one"), read from the escalation receipt
written when the diagnosis was applied, plus its own one-tap usefulness
rating (``helped`` / ``didn't help`` / ``not sure``), recorded in
``diagnosis_feedback`` with ``response`` prefixed ``escalation:``. The
headline says "trying a different approach" only when the repair's operator
really differs from every repair shown for the group before.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Mapping

from learnloop.attempts.reveal_ledger import record_repair_display_reveals
from learnloop.clock import Clock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.diagnosis.split.validation import primary_cause
from learnloop.substrate.recurrence_groups import refresh_recurrence_groups
from learnloop.vault.models import LoadedVault

LOG = logging.getLogger(__name__)

#: Fixed neutral order (§12.2); the diagnosis is not visually privileged.
CARD_RESPONSES: tuple[str, ...] = ("believed_candidate", "partly", "slipped", "diagnosis_wrong", "unsure")
CARD_LABELS = {
    "believed_candidate": "That's it",
    "partly": "Partly",
    "slipped": "I just slipped",
    "diagnosis_wrong": "That's wrong",
    "unsure": "Not sure",
}
NOT_SAME_MISTAKE = "not_same_mistake"
#: The escalated repair's usefulness tap (Slice 2 §3.7), fixed neutral order.
ESCALATION_RESPONSES: tuple[str, ...] = ("escalation:helped", "escalation:didnt_help", "escalation:not_sure")
ESCALATION_LABELS = {
    "escalation:helped": "Helped",
    "escalation:didnt_help": "Didn't help",
    "escalation:not_sure": "Not sure",
}
_ORDINALS = {3: "Third", 4: "Fourth", 5: "Fifth", 6: "Sixth"}
#: Card taps that the existing unresolved-cause channel understands.
_FORWARDABLE = {"believed_candidate", "slipped", "diagnosis_wrong"}
PREREQUISITE_LABEL = "possible cause - not yet checked"


class CardError(ValueError):
    """A tap that names no diagnosis, an unknown response or an unvalidated citation."""


def _normalized(text: str) -> str:
    from learnloop.diagnosis.misconceptions import normalize_text

    return normalize_text(text or "")


def _citations(repository: Repository, diagnosis_id: str) -> list[dict[str, Any]]:
    receipt = repository.diagnosis_context_receipt(diagnosis_id) or {}
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for citation in receipt.get("validated_citations") or []:
        attempt_id = str(citation.get("attempt_id") or "")
        if not attempt_id or attempt_id in seen:
            continue
        seen.add(attempt_id)
        attempt = repository.fetch_practice_attempt(attempt_id) or {}
        out.append(
            {
                "attempt_id": attempt_id,
                "practice_item_id": attempt.get("practice_item_id"),
                "date": attempt.get("created_at"),
                "quote": citation.get("quote"),
                "rubric_score": attempt.get("rubric_score"),
                "correctness": attempt.get("correctness"),
            }
        )
    return out


def _prerequisite_gap(vault: LoadedVault, proposal: Mapping[str, Any]) -> dict[str, Any] | None:
    for gap in proposal.get("prerequisite_gap_hypotheses") or []:
        ref = str(gap.get("prerequisite_ref") or "")
        if not ref:
            continue
        learning_object = vault.learning_objects.get(ref)
        facet = vault.evidence_facets.get(vault.canonical_facet_id(ref)) if learning_object is None else None
        title = (
            learning_object.title
            if learning_object is not None
            else (getattr(facet, "title", None) or ref)
        )
        return {
            "prerequisite_ref": ref,
            "title": title,
            "suggested_check_md": gap.get("suggested_discriminator_md"),
            "label": PREREQUISITE_LABEL,
        }
    return None


_ULID = re.compile(r"\b[0-9A-HJKMNP-TV-Z]{26}\b")


def plain_summary(repository: Repository, text: str) -> str:
    """The diagnoser's ``analysis_md`` with record ids put in learner terms.

    The diagnoser cites earlier attempts by id (that is how its citations are
    validated); the card speaks of "your answer on <date>" instead. Any other
    record id becomes "an earlier record". The wording is otherwise the
    diagnoser's own.
    """

    def label(match: re.Match[str]) -> str:
        attempt = repository.fetch_practice_attempt(match.group(0))
        if attempt is None:
            return "an earlier record"
        created = str(attempt.get("created_at") or "")[:10]
        return f"your answer on {created}" if created else "an earlier answer"

    return _ULID.sub(label, text)


def escalation_block(
    vault: LoadedVault, repository: Repository, diagnosis_id: str, repair_suggestions: list[Mapping[str, Any]]
) -> dict[str, Any] | None:
    """The escalated repair and its evidence, from the escalation receipt."""

    config = getattr(vault.config, "recurrence", None)
    if config is not None and not bool(getattr(config, "escalation_card_enabled", True)):
        return None
    escalation = repository.recurrence_escalation(diagnosis_id)
    if escalation is None:
        return None
    count = int(escalation["recurrence_count"])
    ordinal = _ORDINALS.get(count, f"{count}th")
    headline = f"{ordinal} time with this one"
    if escalation["different_approach"]:
        headline += " - trying a different approach"
    repair = next(
        (
            dict(row)
            for row in repair_suggestions
            if escalation.get("repair_suggestion_id") and str(row.get("id")) == escalation["repair_suggestion_id"]
        ),
        None,
    )
    earlier = []
    for attempt_id in escalation["earlier_attempt_ids"]:
        attempt = repository.fetch_practice_attempt(attempt_id) or {}
        earlier.append(
            {
                "attempt_id": attempt_id,
                "practice_item_id": attempt.get("practice_item_id"),
                "date": attempt.get("created_at"),
                "rubric_score": attempt.get("rubric_score"),
                "correctness": attempt.get("correctness"),
            }
        )
    taps = [
        row["response"]
        for row in repository.diagnosis_feedback_rows(diagnosis_id)
        if str(row["response"]).startswith("escalation:")
    ]
    return {
        "escalation_id": escalation["id"],
        "headline": headline,
        "recurrence_count": count,
        "different_approach": escalation["different_approach"],
        # Honest label: the repair is the same kind as before when no
        # different operator was available (the headline then makes no claim).
        "approach_note": None
        if escalation["different_approach"]
        else "This is the same kind of repair you were shown before; no different one was available.",
        "repair": repair,
        "earlier_answers": earlier,
        "responses": [{"response": value, "label": ESCALATION_LABELS[value]} for value in ESCALATION_RESPONSES],
        "recorded_response": taps[-1] if taps else None,
    }


def diagnosis_card(vault: LoadedVault, repository: Repository, attempt_id: str) -> dict[str, Any]:
    """The card for one attempt (status first; content only when done)."""

    from learnloop.diagnosis.split.jobs import DONE, diagnosis_status

    config = getattr(vault.config, "diagnosis", None)
    status = diagnosis_status(repository, attempt_id)
    card: dict[str, Any] = {
        "attempt_id": attempt_id,
        "status": status["status"],
        "card_enabled": bool(getattr(config, "card_enabled", True)),
        "responses": [
            {"response": value, "label": CARD_LABELS[value]} for value in CARD_RESPONSES
        ],
    }
    if status["status"] != DONE:
        return card
    diagnosis = repository.attempt_diagnosis(str(status["diagnosis_id"])) or {}
    proposal = diagnosis.get("proposal") or {}
    metadata = repository.fetch_attempt_feedback_metadata(attempt_id) or {}
    taps = repository.diagnosis_feedback_rows(str(diagnosis.get("id")))
    repair_suggestions = list(metadata.get("repair_suggestions") or [])
    card.update(
        diagnosis_id=diagnosis.get("id"),
        created_at=diagnosis.get("created_at"),
        history_mode=diagnosis.get("history_mode"),
        summary_md=plain_summary(repository, str(proposal.get("analysis_md") or "")),
        repair_suggestions=repair_suggestions,
        made_before=_citations(repository, str(diagnosis.get("id"))),
        prerequisite_gap=_prerequisite_gap(vault, proposal),
        escalation=escalation_block(vault, repository, str(diagnosis.get("id")), repair_suggestions),
        recorded_response=next(
            (
                row["response"]
                for row in reversed(taps)
                if row["response"] != NOT_SAME_MISTAKE and not str(row["response"]).startswith("escalation:")
            ),
            None,
        ),
        not_same_mistake_attempt_ids=sorted(
            {str(row["cited_attempt_id"]) for row in taps if row["response"] == NOT_SAME_MISTAKE}
        ),
    )
    return card


def _forward(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    response: str,
    proposal: Mapping[str, Any],
    clock: Clock | None,
) -> tuple[str | None, str]:
    """Forward to an open factor's self-report channel; (factor id, note)."""

    from learnloop.diagnosis.causal_attribution import record_unresolved_cause_self_report

    factors = repository.unresolved_cause_factors_for_attempt(attempt_id, status="open")
    if not factors:
        return None, "no_open_factor"
    factor = factors[0]
    candidate_index: int | None = None
    if response == "believed_candidate":
        _event, cause = primary_cause(proposal)
        wanted = _normalized(str((cause or {}).get("statement") or ""))
        for index, candidate in enumerate(factor.get("candidate_causes") or []):
            if not isinstance(candidate, Mapping) or candidate.get("open_set"):
                continue
            if wanted and _normalized(str(candidate.get("statement") or "")) == wanted:
                candidate_index = index
                break
        if candidate_index is None:
            return None, "primary_cause_not_in_factor"
    try:
        record_unresolved_cause_self_report(
            vault,
            repository,
            factor_id=str(factor["id"]),
            response=response,
            candidate_index=candidate_index,
            clock=clock,
        )
    except ValueError as exc:
        return None, f"not_forwarded:{exc}"
    return str(factor["id"]), "forwarded"


def record_card_tap(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    diagnosis_id: str,
    response: str,
    cited_attempt_id: str | None = None,
    shown_at: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    diagnosis = repository.attempt_diagnosis(diagnosis_id)
    if diagnosis is None or diagnosis.get("attempt_id") != attempt_id or diagnosis.get("status") != "completed":
        raise CardError("diagnosis_id does not name this attempt's completed diagnosis")
    if response == NOT_SAME_MISTAKE:
        cited = {row["attempt_id"] for row in _citations(repository, diagnosis_id)}
        if not cited_attempt_id or cited_attempt_id not in cited:
            raise CardError("not_same_mistake must name a validated citation of this diagnosis")
    elif response in ESCALATION_RESPONSES:
        if repository.recurrence_escalation(diagnosis_id) is None:
            raise CardError("an escalation rating needs an escalated repair on this diagnosis")
        if cited_attempt_id is not None:
            raise CardError("only not_same_mistake names a cited attempt")
    elif response not in CARD_RESPONSES:
        raise CardError(f"unknown card response {response!r}")
    elif cited_attempt_id is not None:
        raise CardError("only not_same_mistake names a cited attempt")
    if shown_at is not None and parse_utc(shown_at) is None:  # pragma: no cover - parse raises
        shown_at = None
    forwarded_factor_id: str | None = None
    note = "card_only"
    config = getattr(vault.config, "diagnosis", None)
    if response in ESCALATION_RESPONSES:
        note = "escalation_rating"
    elif response in _FORWARDABLE and bool(getattr(config, "forward_card_taps", True)):
        forwarded_factor_id, note = _forward(
            vault,
            repository,
            attempt_id=attempt_id,
            response=response,
            proposal=diagnosis.get("proposal") or {},
            clock=clock,
        )
    feedback_id = repository.insert_diagnosis_feedback(
        diagnosis_id=diagnosis_id,
        attempt_id=attempt_id,
        response=response,
        cited_attempt_id=cited_attempt_id,
        forwarded_factor_id=forwarded_factor_id,
        shown_at=shown_at,
        clock=clock,
    )
    if response == NOT_SAME_MISTAKE:
        from learnloop.ai.execution import content_key
        from learnloop.db.stores.judgments import append_judgment

        with repository.atomic():
            append_judgment(
                repository.connection(),
                task="same_cause",
                left_kind="attempt",
                left_id=attempt_id,
                right_kind="attempt",
                right_id=str(cited_attempt_id),
                judge="learner_card",
                input_hash=content_key({"diagnosis_feedback_id": feedback_id}),
                verdict="different",
                rationale="diagnosis card: not the same mistake",
            )
        # Slice 2 T1: the tap is a learner_card "different" for the groups.
        refresh_recurrence_groups(vault, repository)
    return {"feedback_id": feedback_id, "forwarded_factor_id": forwarded_factor_id, "forwarding": note}


def diagnosis_repairs_debited(repository: Repository, attempt_id: str, diagnosis_id: str) -> bool:
    """Were this diagnosis's displayed repairs already charged to the ledger?"""

    with repository.connection() as connection:
        return connection.execute(
            "SELECT 1 FROM reveal_events WHERE attempt_id = ? AND basis LIKE ? LIMIT 1",
            (attempt_id, f"repair_display:diagnosis:{diagnosis_id}:%"),
        ).fetchone() is not None


def debit_displayed_repairs(
    repository: Repository,
    *,
    attempt: Mapping[str, Any],
    diagnosis: Mapping[str, Any],
    repair_suggestions: list[Mapping[str, Any]],
    learning_object_id: str | None,
) -> int:
    """Reveal accounting when the diagnosis's repairs are displayed (§8).

    Charged when the repair is displayed, not when the attempt is submitted,
    and once per diagnosis: whichever surface shows them first (the card, or a
    feedback screen first opened after the diagnosis landed) debits them, and
    the other finds the rows (their basis names the diagnosis) and charges
    nothing.
    """

    if diagnosis_repairs_debited(repository, str(attempt["id"]), str(diagnosis["id"])):
        return 0
    try:
        return record_repair_display_reveals(
            repository,
            attempt_id=str(attempt["id"]),
            practice_item_id=str(attempt.get("practice_item_id") or "") or None,
            learning_object_id=learning_object_id,
            repair_suggestions=repair_suggestions,
        )
    except Exception:  # pragma: no cover - bookkeeping never costs the card
        LOG.warning("failed to debit diagnosis repair reveals for %s", attempt.get("id"), exc_info=True)
        return 0


__all__ = [
    "CARD_LABELS",
    "CARD_RESPONSES",
    "ESCALATION_LABELS",
    "ESCALATION_RESPONSES",
    "CardError",
    "NOT_SAME_MISTAKE",
    "PREREQUISITE_LABEL",
    "debit_displayed_repairs",
    "diagnosis_card",
    "diagnosis_repairs_debited",
    "escalation_block",
    "record_card_tap",
]
