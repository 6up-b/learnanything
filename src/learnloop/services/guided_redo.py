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

Everything served here is a pure read of stored grading artifacts
(``attempt_debug_payloads`` → ``causal_attribution.diagnosis_receipt`` →
``repair_selection``); the only writes are the episode (re)binding, which
commits an open, not-yet-primed episode to the original item as its primed
surface.
"""

from __future__ import annotations

from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.repair_splice import is_end_append
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
                None if cold is not None else "no_independent_surface"
            ),
        }
    return {
        "episode_id": None,
        "episode": None,
        "cold_item_id": None,
        "cold_unmeasurable_reason": None,
    }


def start_guided_redo(
    vault: LoadedVault,
    repository: Repository,
    attempt_id: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """The redo context for one failed attempt, binding an open episode if any.

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
    prefix = str(trace.get("learner_work_prefix") or "")
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
    insertion_kind = "end_append" if is_end_append(trace) else "mid_splice"
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
        "insertion_kind": insertion_kind,
        "repair_class_id": str(repair_class.get("id") or "") or None,
        **binding,
    }
