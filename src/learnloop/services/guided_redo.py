"""Guided partial redo of a failed attempt (owner Fix 3).

After a wrong attempt whose grading produced a repair selection, the learner can
redo ONLY the part where the mistake was made: the server-recomposed
``learner_work_prefix`` (their preserved work) is shown read-only, and the
learner rewrites just the repaired portion. The composed answer is submitted as
a PRIMED attempt on the SAME item — priming semantics already exist
(``contamination_class='repair_activity'``, asymmetric mastery updates) — and,
when an open remediation episode exists for the diagnosed case, the redo binds
as that episode's primed attempt so the §6.2 cold retry on a *different*
surface is scheduled exactly as in the sibling-item treatment flow.

When NO open episode exists for the diagnosed case, one is established through
the sanctioned entry (``remediation.start_remediation_episode`` →
``causal_orchestrator.causal_repair_status``) before binding, so a redo taken
straight from the feedback screen — without ever visiting the Repair overlay —
still closes the primed → cold funnel. A held or blocked repair (probe first,
budget, no adjudicated case) degrades gracefully: the redo still serves as a
plain primed attempt, and ``remediation.record_remediation_attempt`` leaves a
typed ``causal_cold_outcomes`` disposition instead of dropping the evidence.

The composed answer is always ``learner_work_prefix + rewrite``: the repaired
trace schema can only express a *prefix* (see
``repair_splice.preserved_prefix_from_refs``), so there is never preserved
trailing text to splice the rewrite into — a "mid-splice" redo would have to
fabricate work the learner did not keep.

Everything else served here is a pure read of stored grading artifacts
(``attempt_debug_payloads`` → ``causal_attribution.diagnosis_receipt`` →
``repair_selection``); the writes are the episode establishment and
(re)binding, which commit an open, not-yet-primed episode to the original item
as its primed surface.
"""

from __future__ import annotations

from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault


class GuidedRedoUnavailable(ValueError):
    """No guided redo can be offered for this attempt, with a stable reason."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def _diagnosis_receipt(repository: Repository, attempt_id: str) -> dict[str, Any] | None:
    debug = repository.attempt_debug_payload(attempt_id) or {}
    attribution = debug.get("causal_attribution")
    if not isinstance(attribution, dict):
        return None
    receipt = attribution.get("diagnosis_receipt")
    return receipt if isinstance(receipt, dict) else None


def _selected_repair(receipt: dict[str, Any] | None) -> dict[str, Any] | None:
    """``repair_selection.selected`` — {repair_class, suggestion, minimality}."""

    if not isinstance(receipt, dict):
        return None
    selection = receipt.get("repair_selection")
    if not isinstance(selection, dict):
        return None
    selected = selection.get("selected")
    return selected if isinstance(selected, dict) else None


def _preserved_prefix(selected: dict[str, Any] | None) -> str:
    """The SELECTED repair's ``learner_work_prefix``, or ``""``."""

    suggestion = (selected or {}).get("suggestion")
    suggestion = suggestion if isinstance(suggestion, dict) else {}
    trace = suggestion.get("repaired_trace")
    trace = trace if isinstance(trace, dict) else {}
    return str(trace.get("learner_work_prefix") or "")


def guided_redo_available(repository: Repository, attempt_id: str) -> bool:
    """Whether :func:`start_guided_redo` would serve this attempt.

    The exact server-side availability rule — a stored repair *selection* whose
    selected repair preserves a non-empty prefix — exposed so the feedback
    surface can gate its button on the truth instead of on "any suggestion has
    a prefix", which is visible-but-unavailable whenever the selected class
    differs (or nothing was selected at all).
    """

    selected = _selected_repair(_diagnosis_receipt(repository, attempt_id))
    if selected is None:
        return False
    return bool(_preserved_prefix(selected).strip())


def _item_step_checkpoint_ids(repair_class: dict[str, Any] | None) -> list[str]:
    checkpoint_ids: list[str] = []
    for ref in (repair_class or {}).get("target_refs") or []:
        if isinstance(ref, dict) and ref.get("kind") == "item_step" and ref.get("checkpoint_id"):
            checkpoint_ids.append(str(ref["checkpoint_id"]))
    return list(dict.fromkeys(checkpoint_ids))


def _case_candidates(
    repository: Repository, attempt_id: str
) -> list[tuple[str, str]]:
    """(case_kind, case_ref) pairs this attempt's diagnosis could bind to.

    Misconception cases come from the attempt's error events; diagnosis-kind
    cases from its causal hypotheses. Ordered deterministically: durable
    misconceptions first (they own the authored correction), then hypotheses.
    """

    pairs: list[tuple[str, str]] = []
    for event in repository.error_events_for_attempt(attempt_id):
        misconception_id = event.get("misconception_id")
        if misconception_id:
            pairs.append(("misconception", str(misconception_id)))
    for hypothesis in repository.causal_hypotheses_for_attempt(attempt_id):
        if hypothesis.get("id"):
            pairs.append(("diagnosis", str(hypothesis["id"])))
    return list(dict.fromkeys(pairs))


def _bind_episode_to_redo(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt: dict[str, Any],
    item: Any,
    target_checkpoint_ids: tuple[str, ...],
    clock: Clock | None,
) -> dict[str, Any]:
    """Commit an open, unbound episode to the redo item as its primed surface.

    Only an episode whose ``primed_item_id`` is NULL or already the redo item is
    (re)bound — a treatment episode committed to a SIBLING item keeps its pair,
    so the existing sibling flow is untouched. The cold item is re-picked from
    the case ranking and must sit in a different surface group from the
    ORIGINAL item (which is what the redo primes), mirroring
    ``start_remediation_treatment``'s §6.2 rule.
    """

    from learnloop.services.canonical_projection import surface_group_id
    from learnloop.services.remediation import _episode_case, _rank_items

    for case_kind, case_ref in _case_candidates(repository, str(attempt["id"])):
        episode = repository.open_remediation_episode_for_case(
            case_kind=case_kind, case_ref=case_ref
        )
        if episode is None:
            continue
        primed_item_id = str(episode.get("primed_item_id") or "")
        if primed_item_id and primed_item_id != item.id:
            # Committed to a sibling pair already; leave the sibling flow alone.
            continue
        case = _episode_case(repository, episode)
        cold = None
        # Distinct honest reasons: a case that no longer resolves is not the
        # same fact as "the case is fine but every sibling shares the redo's
        # surface", and reporting the latter for the former sends a reader
        # authoring surfaces that would change nothing.
        cold_unmeasurable_reason = "case_unresolvable"
        if case is not None:
            ranked, _skips = _rank_items(
                vault,
                repository,
                case,
                target_checkpoint_ids=target_checkpoint_ids,
                clock=clock,
            )
            redo_surface = surface_group_id(item)
            cold = next(
                (
                    candidate
                    for candidate in ranked
                    if candidate.id != item.id
                    and surface_group_id(candidate) != redo_surface
                ),
                None,
            )
            cold_unmeasurable_reason = "no_independent_surface"
        updated = repository.update_remediation_episode(
            episode["id"],
            state="treatment",
            primed_item_id=item.id,
            cold_item_id=cold.id if cold is not None else None,
            clock=clock,
        )
        return {
            "episode_id": str(episode["id"]),
            "episode": updated,
            "cold_item_id": cold.id if cold is not None else None,
            "cold_unmeasurable_reason": (
                None if cold is not None else cold_unmeasurable_reason
            ),
        }
    return {
        "episode_id": None,
        "episode": None,
        "cold_item_id": None,
        "cold_unmeasurable_reason": None,
    }


def _establish_episode(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt: dict[str, Any],
    clock: Clock | None,
) -> bool:
    """Mint an open episode for the attempt's diagnosed case, where permitted.

    Episodes used to be minted only by the Repair overlay, so a redo taken
    directly from the feedback screen bound nothing and its primed submit was a
    silent dead end. This goes through the sanctioned entry —
    ``start_remediation_episode`` → ``causal_repair_status(start_repair=True)``
    — with the case resolved exactly as :func:`_case_candidates` orders them:
    the matched durable misconception for misconception-kind diagnoses, the
    hypothesis (candidate belief) id for diagnosis-kind ones.

    Returns whether any episode is now open. The holding/blocked arms (probe
    first, session budget, no adjudicatable case) raise typed errors that are
    deliberately swallowed here: they mean "no episode may exist yet", and the
    redo must still serve as a plain primed attempt in that world.

    If ANY candidate case already has an open episode, establishment stands
    down entirely: binding just declined it, which can only mean it is
    committed to a sibling pair — and the sanctioned entry only reuses
    *uncommitted* episodes, so starting the repair again would mint a parallel
    episode measuring the same diagnosis twice (the orphan-twin failure
    ``get_or_create_open_remediation_episode`` exists to prevent). The sibling
    flow keeps its measurement; the redo stays unbound.
    """

    from learnloop.services.remediation import (
        RemediationError,
        start_remediation_episode,
    )

    candidates = _case_candidates(repository, str(attempt["id"]))
    for case_kind, case_ref in candidates:
        if (
            repository.open_remediation_episode_for_case(
                case_kind=case_kind, case_ref=case_ref
            )
            is not None
        ):
            return False
    for _case_kind, case_ref in candidates:
        try:
            episode = start_remediation_episode(
                repository,
                case_ref,
                vault=vault,
                session_id=str(attempt.get("session_id") or "") or None,
                clock=clock,
            )
        except RemediationError:
            # Includes RemediationBlocked (held: probe/budget) and the
            # unadjudicated-case refusal — both are honest "not yet" arms.
            continue
        if episode is not None:
            return True
    return False


def start_guided_redo(
    vault: LoadedVault,
    repository: Repository,
    attempt_id: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """The redo context for one failed attempt, binding an episode when possible.

    When no open episode exists for the diagnosed case, one is established via
    the sanctioned repair entry first; a held/blocked repair leaves the binding
    null and the redo serves as a plain primed attempt.

    Raises :class:`GuidedRedoUnavailable` (stable ``reason``) when the attempt
    has no usable repair selection: ``attempt_not_found``, ``item_not_found``,
    ``no_repair_selection``, ``no_preserved_prefix``.
    """

    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        raise GuidedRedoUnavailable("attempt_not_found", f"Attempt {attempt_id} not found.")
    item = vault.practice_items.get(str(attempt["practice_item_id"]))
    if item is None:
        raise GuidedRedoUnavailable(
            "item_not_found",
            f"{attempt['practice_item_id']} is no longer in the vault.",
        )
    receipt = _diagnosis_receipt(repository, attempt_id)
    selected = _selected_repair(receipt)
    if selected is None:
        raise GuidedRedoUnavailable(
            "no_repair_selection",
            "This attempt has no repair selection to redo from.",
        )
    suggestion = selected.get("suggestion")
    suggestion = suggestion if isinstance(suggestion, dict) else {}
    trace = suggestion.get("repaired_trace")
    trace = trace if isinstance(trace, dict) else {}
    prefix = _preserved_prefix(selected)
    if not prefix.strip():
        # Nothing was preserved: a "partial" redo would be a full retry, and the
        # existing primed-retry path already covers that honestly.
        raise GuidedRedoUnavailable(
            "no_preserved_prefix",
            "The repair preserves none of this answer — use a full retry instead.",
        )
    repair_class = selected.get("repair_class")
    repair_class = repair_class if isinstance(repair_class, dict) else {}
    failed_checkpoint_ids = [
        str(value) for value in trace.get("changed_checkpoint_ids") or [] if value
    ] or _item_step_checkpoint_ids(repair_class)
    binding = _bind_episode_to_redo(
        vault,
        repository,
        attempt=attempt,
        item=item,
        target_checkpoint_ids=tuple(failed_checkpoint_ids),
        clock=clock,
    )
    if binding["episode_id"] is None and _establish_episode(
        vault, repository, attempt=attempt, clock=clock
    ):
        binding = _bind_episode_to_redo(
            vault,
            repository,
            attempt=attempt,
            item=item,
            target_checkpoint_ids=tuple(failed_checkpoint_ids),
            clock=clock,
        )
    return {
        "attempt_id": str(attempt["id"]),
        "practice_item_id": item.id,
        "prompt": item.prompt,
        "learner_work_prefix": prefix,
        # What to redo, in the grader's own words: the repair op rationale plus
        # the checkpoint-precise targets when the item has a decomposition.
        "redo_instruction": str(suggestion.get("rationale") or "") or None,
        "failed_checkpoint_ids": failed_checkpoint_ids,
        "repair_class_id": str(repair_class.get("id") or "") or None,
        **binding,
    }
