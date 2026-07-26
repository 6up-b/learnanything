"""Diagnosis adjudication: the ground-truth store for diagnostic quality.

`spec_diagnostic_augmentation_v1.md` §2 A4. `spec_causal_attribution_v1.md`
§12 lists *first-divergence accuracy vs adjudication* and *abstention
precision* among its primary metrics with nothing producing either. Grade-
**points** adjudication exists (`services/grade_resolution.append_adjudication`,
§4.4); diagnosis adjudication did not. This module is the producer.

One append-only table (migration 126), one write path, and two read paths:
a queue that decides *which* attempt is worth a verdict, and a scoreboard that
turns verdicts into the §3 B5 metrics.

Why this is a separate record from the §5.6 learner contest
-----------------------------------------------------------
The typed `doesnt_fit` contest (`causal_attribution.record_causal_diagnosis_contest`
→ `causal_attribution_reports`) is already wired to the feedback screen and is
the cheapest signal the system has. It is *not* the same record as an
adjudication, and this store does not launder one into the other:

* §2's producer/confirmer matrix lists "learner confirmation" and
  "adjudication" as **separate** confirmation channels, and
  `causal_attribution.SUPPORT_AUTHORITIES` separates `learner_confirmed` from
  `adjudicated`. §5.6 calls the contest "bounded negative evidence ... an
  evidence channel, not an override", while durable promotion condition (d) is
  "human adjudication". Collapsing them would grant a bounded-trust report the
  authority reserved for a considered verdict.
* A contest carries a typed *reason* and nothing else. A4 requires an
  adjudicated **anchor** and an adjudicated **minimal repair**; both would be
  NULL on every laundered record, and `first_divergence_anchor_accuracy` — the
  metric this store exists to produce — would be uncomputable.
* Learners contest when they disagree. An eval set made of contests is ~100%
  negative verdicts: `correct` and `correctly_abstained` would never be
  observed, so precision would be undefined and §3 B4's planted-vs-adjudicated
  agreement would compare against a censored sample.

What they *do* share is a substrate: the contest is the highest-yield **queue
producer**. `adjudication_queue` ranks a contested attempt first, carries the
contest's typed reason forward as displayed context, and stores its id in
`learner_report_id` as provenance. Every record also stores `queue_reason`, so
the eval set's selection bias is auditable instead of invisible — which is what
makes B4 mean anything.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault


ADJUDICATION_STORE_VERSION = "diagnosis_adjudication_v1"

#: The A4 verdict vocabulary. `should_not_have_abstained` is a deliberate
#: sixth value; see :data:`ABSTENTION_VERDICTS` and migration 126's comment.
VERDICTS: tuple[str, ...] = (
    "correct",
    "wrong_anchor",
    "wrong_repair",
    "should_have_abstained",
    "correctly_abstained",
    "should_not_have_abstained",
)

#: Verdicts that may only be recorded when the system *did* abstain.
ABSTENTION_VERDICTS = frozenset({"correctly_abstained", "should_not_have_abstained"})
#: Verdicts that may only be recorded when the system *named* a cause.
FILLED_VERDICTS = frozenset(
    {"correct", "wrong_anchor", "wrong_repair", "should_have_abstained"}
)
#: Verdicts that assert something about the system's anchor, and therefore
#: require the adjudicated anchor to be recorded.
ANCHOR_REQUIRED_VERDICTS = frozenset(
    {"correct", "wrong_anchor", "wrong_repair", "should_not_have_abstained"}
)
#: Verdicts where the system produced an anchor and the adjudicator ruled on
#: it: the denominator of `first_divergence_anchor_accuracy`.
ANCHOR_SCORED_VERDICTS = frozenset({"correct", "wrong_anchor", "wrong_repair"})
#: ...and the numerator. `wrong_repair` means "right place, wrong fix".
ANCHOR_CORRECT_VERDICTS = frozenset({"correct", "wrong_repair"})

QUEUE_REASONS: tuple[str, ...] = (
    "learner_contest",
    "system_abstention",
    "anchor_disagreement",
    "incomplete_repair_mapping",
    "sampled",
    "manual",
)

#: Priority order for the queue. Contests first (the learner already paid the
#: attention cost, §5.6), abstentions second (B1: an eval set without
#: abstention cases "selects toward over-filling, which is the disease v1
#: exists to cure"), then the cases the system itself flagged as unresolved,
#: then an unflagged stratum so the set is not purely adversarially selected.
_QUEUE_PRIORITY: dict[str, int] = {
    "learner_contest": 0,
    "system_abstention": 1,
    "anchor_disagreement": 2,
    "incomplete_repair_mapping": 3,
    "sampled": 4,
    "manual": 5,
}

#: Full-authority sources only. `learner_clarification` (which grade
#: adjudication admits under a bounded trust weight < 1) is deliberately
#: absent: a bounded-trust label is not eval ground truth.
ADJUDICATOR_SOURCES: tuple[str, ...] = (
    "human_owner",
    "independent_expert",
    "deterministic_verifier",
)

ANCHOR_KINDS: tuple[str, ...] = (
    "span",
    "between_spans",
    "missing_required_step",
    "whole_answer",
    "none",
)

#: A learner report that CONFIRMS a presented candidate is not a contest.
_CONFIRMING_REPORT = "believed_candidate"

_WHITESPACE = re.compile(r"\s+")


# ---------------------------------------------------------------------------
# System-side snapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiagnosisSnapshot:
    """What the system produced, frozen at adjudication time.

    The receipt lives in `attempt_debug_payloads`, which replay may rebuild
    (`services/replay.py`). An eval record that had to re-read it would silently
    change meaning after a rebuild, so every field a metric needs is copied
    here and persisted with the verdict.
    """

    attempt_id: str
    receipt_id: str
    receipt_schema_version: int | None
    decision_policy_version: str | None
    repair_policy_version: str | None
    grading_prompt_version: str | None
    grader_model: str | None
    grader_provider: str | None
    grader_provider_revision: str | None
    grading_agent_run_id: str | None
    mechanism_taxonomy_version_id: str | None
    mechanism_taxonomy_hash: str | None
    support_authority: str | None
    contamination_class: str | None
    selection_basis: str | None
    system_abstained: bool
    abstention_basis: str
    system_anchor: dict[str, Any] | None
    anchor_disagreement: bool
    system_repair_class_id: str | None
    known_repair_class_ids: tuple[str, ...]
    incomplete_repair_mapping: bool
    plausible_hypothesis_ids: tuple[str, ...]
    resolution_counts: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "store_version": ADJUDICATION_STORE_VERSION,
            "receipt_id": self.receipt_id,
            "receipt_schema_version": self.receipt_schema_version,
            "decision_policy_version": self.decision_policy_version,
            "repair_policy_version": self.repair_policy_version,
            "grading_prompt_version": self.grading_prompt_version,
            "grader_model": self.grader_model,
            "grader_provider": self.grader_provider,
            "grader_provider_revision": self.grader_provider_revision,
            "grading_agent_run_id": self.grading_agent_run_id,
            "mechanism_taxonomy_version_id": self.mechanism_taxonomy_version_id,
            "mechanism_taxonomy_hash": self.mechanism_taxonomy_hash,
            "support_authority": self.support_authority,
            "contamination_class": self.contamination_class,
            "selection_basis": self.selection_basis,
            "system_abstained": self.system_abstained,
            "abstention_basis": self.abstention_basis,
            "system_anchor": self.system_anchor,
            "system_anchor_key": anchor_key(self.system_anchor),
            "anchor_disagreement": self.anchor_disagreement,
            "system_repair_class_id": self.system_repair_class_id,
            "known_repair_class_ids": list(self.known_repair_class_ids),
            "incomplete_repair_mapping": self.incomplete_repair_mapping,
            "plausible_hypothesis_ids": list(self.plausible_hypothesis_ids),
            "resolution_counts": dict(self.resolution_counts),
        }


def anchor_key(anchor: Mapping[str, Any] | None) -> str:
    """A comparable key for a first-divergence anchor.

    Used to compare an adjudicated anchor against the system's, and — the
    reason it is public — against a *planted* anchor for §3 B4's
    planted-vs-adjudicated agreement. Offsets win over quotes because the
    quote is model-transcribed prose and the offsets are computed against the
    stored answer.
    """

    if not isinstance(anchor, Mapping):
        return "none"
    kind = str(anchor.get("anchor_kind") or "unknown")
    if kind == "none":
        return "none"
    criterion = str(anchor.get("criterion_id") or "")
    if kind == "missing_required_step":
        return f"{kind}:{criterion}:{anchor.get('checkpoint_id') or ''}"
    start = anchor.get("char_start")
    end = anchor.get("char_end")
    if isinstance(start, int) and isinstance(end, int):
        return f"{kind}:{criterion}:{start}-{end}"
    quote = anchor.get("normalized_quote") or anchor.get("quote")
    if quote:
        return f"{kind}:{criterion}:q:{_WHITESPACE.sub(' ', str(quote)).strip().casefold()}"
    return f"{kind}:{criterion}"


def _abstention_state(
    receipt: Mapping[str, Any], telemetry: Mapping[str, Any]
) -> tuple[bool, str]:
    """Did the diagnosis decline to name a cause, and on what basis?

    This is a record of what the system DID, never a judgement — the
    adjudicator cannot override it, because it is the term the abstention
    confusion matrix is conditioned on.
    """

    axes = [
        value
        for value in receipt.get("attribution_axes") or []
        if isinstance(value, Mapping)
    ]
    statuses = [
        str(value.get("resolution_status"))
        for value in axes
        if value.get("resolution_status")
    ]
    if statuses:
        if all(status == "abstained" for status in statuses):
            return True, "all_attribution_axes_abstained"
        return False, "named_cause_present"
    # An abstained attribution materializes no hypothesis, so the receipt's
    # axes are empty and the grading telemetry is the only place the explicit
    # `resolution_status='abstained'` survives.
    counts = telemetry.get("resolution_counts") or {}
    abstained = int(counts.get("abstained") or 0)
    named = int(counts.get("resolved") or 0) + int(counts.get("unresolved") or 0)
    if abstained and not named:
        return True, "all_attributions_abstained"
    if not (receipt.get("plausible_set") or []):
        # Silence is not the same as a declared abstention, but it is equally
        # "no cause was named", and the confusion matrix conditions on what the
        # system produced rather than on how loudly it said so.
        return True, "no_concrete_hypothesis_named"
    return False, "named_cause_present"


def diagnosis_snapshot(
    repository: Repository, attempt_id: str
) -> DiagnosisSnapshot | None:
    """Freeze the system's diagnosis for one attempt, or None if it has none."""

    from learnloop.services.causal_attribution import causal_episode_for_attempt

    episode = causal_episode_for_attempt(repository, attempt_id)
    if episode is None or not isinstance(episode.get("receipt"), Mapping):
        return None
    receipt: Mapping[str, Any] = episode["receipt"]
    receipt_id = str(receipt.get("id") or "")
    if not receipt_id:
        return None

    debug = repository.attempt_debug_payload(attempt_id) or {}
    telemetry = debug.get("causal_attribution")
    telemetry = telemetry if isinstance(telemetry, Mapping) else {}

    metadata = repository.fetch_attempt_feedback_metadata(attempt_id) or {}
    run_id = metadata.get("agent_run_id")
    run = repository.agent_run(str(run_id)) if run_id else None
    run = run or {}

    anchors = receipt.get("divergence_anchors")
    anchors = anchors if isinstance(anchors, Mapping) else {}
    system_anchor = anchors.get("first_observable_divergence")
    system_anchor = dict(system_anchor) if isinstance(system_anchor, Mapping) else None

    selection = receipt.get("repair_selection")
    selection = selection if isinstance(selection, Mapping) else {}
    selected = selection.get("selected")
    selected = selected if isinstance(selected, Mapping) else {}
    selected_class = selected.get("repair_class")
    selected_class = selected_class if isinstance(selected_class, Mapping) else {}

    repair_classes = [
        value
        for value in receipt.get("repair_classes") or []
        if isinstance(value, Mapping) and value.get("id")
    ]
    repair_policy_version = next(
        (
            str(value["repair_policy_version"])
            for value in repair_classes
            if value.get("repair_policy_version")
        ),
        None,
    )
    probe_need = receipt.get("probe_need")
    probe_need = probe_need if isinstance(probe_need, Mapping) else {}

    abstained, basis = _abstention_state(receipt, telemetry)
    schema_version = receipt.get("schema_version")
    return DiagnosisSnapshot(
        attempt_id=attempt_id,
        receipt_id=receipt_id,
        receipt_schema_version=(
            int(schema_version) if isinstance(schema_version, int) else None
        ),
        decision_policy_version=(
            str(receipt["decision_policy_version"])
            if receipt.get("decision_policy_version")
            else None
        ),
        repair_policy_version=repair_policy_version,
        grading_prompt_version=(
            str(telemetry["prompt_version"])
            if telemetry.get("prompt_version")
            else None
        ),
        grader_model=str(run["model"]) if run.get("model") else None,
        grader_provider=str(run["provider"]) if run.get("provider") else None,
        grader_provider_revision=(
            str(run["provider_revision"]) if run.get("provider_revision") else None
        ),
        grading_agent_run_id=str(run_id) if run_id else None,
        mechanism_taxonomy_version_id=(
            str(receipt["mechanism_taxonomy_version_id"])
            if receipt.get("mechanism_taxonomy_version_id")
            else None
        ),
        mechanism_taxonomy_hash=(
            str(receipt["mechanism_taxonomy_hash"])
            if receipt.get("mechanism_taxonomy_hash")
            else None
        ),
        support_authority=(
            str(receipt["support_authority"])
            if receipt.get("support_authority")
            else None
        ),
        contamination_class=(
            str(receipt["contamination_class"])
            if receipt.get("contamination_class")
            else None
        ),
        selection_basis=(
            str(selection["selection_basis"])
            if selection.get("selection_basis")
            else None
        ),
        system_abstained=abstained,
        abstention_basis=basis,
        system_anchor=system_anchor,
        anchor_disagreement=bool(anchors.get("anchor_disagreement")),
        system_repair_class_id=(
            str(selected_class["id"]) if selected_class.get("id") else None
        ),
        known_repair_class_ids=tuple(
            str(value["id"]) for value in repair_classes
        ),
        incomplete_repair_mapping=bool(
            probe_need.get("incomplete_repair_mapping")
        ),
        plausible_hypothesis_ids=tuple(
            str(value) for value in receipt.get("plausible_set") or []
        ),
        resolution_counts={
            str(key): int(value or 0)
            for key, value in (telemetry.get("resolution_counts") or {}).items()
        },
    )


# ---------------------------------------------------------------------------
# Queue
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdjudicationQueueEntry:
    attempt_id: str
    queue_reason: str
    priority: int
    detail: str
    created_at: str
    learning_object_id: str | None
    practice_item_id: str | None
    snapshot: DiagnosisSnapshot
    learner_report: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "queue_reason": self.queue_reason,
            "priority": self.priority,
            "detail": self.detail,
            "created_at": self.created_at,
            "learning_object_id": self.learning_object_id,
            "practice_item_id": self.practice_item_id,
            "learner_report": self.learner_report,
            "system": self.snapshot.as_dict(),
        }


def latest_learner_report(
    repository: Repository, attempt_id: str
) -> dict[str, Any] | None:
    """The most recent §5.6 typed self-report for an attempt, any factor status.

    `record_causal_diagnosis_contest` refuses a second report per attempt, so
    there is at most one; scanning all three statuses matches the check it
    already performs.
    """

    reports: list[dict[str, Any]] = []
    for status in ("open", "resolved", "retired"):
        for factor in repository.unresolved_cause_factors_for_attempt(
            attempt_id, status=status
        ):
            report = factor.get("self_report")
            if isinstance(report, Mapping) and report.get("id"):
                reports.append({**dict(report), "factor_id": factor.get("id")})
    if not reports:
        return None
    reports.sort(key=lambda value: (str(value.get("created_at") or ""), str(value["id"])))
    return reports[-1]


def _queue_reason(
    snapshot: DiagnosisSnapshot, report: Mapping[str, Any] | None
) -> tuple[str, str]:
    if report is not None and report.get("response") != _CONFIRMING_REPORT:
        return (
            "learner_contest",
            f"learner reported {report.get('response')!r} on this diagnosis",
        )
    if snapshot.system_abstained:
        return ("system_abstention", f"system abstained ({snapshot.abstention_basis})")
    if snapshot.anchor_disagreement:
        return (
            "anchor_disagreement",
            "candidate hypotheses disagreed on the first-divergence anchor",
        )
    if snapshot.incomplete_repair_mapping:
        return (
            "incomplete_repair_mapping",
            "a concrete hypothesis carries no repair class",
        )
    if report is not None:
        return (
            "sampled",
            f"learner confirmed a candidate ({report.get('response')})",
        )
    return ("sampled", "unflagged stratum")


def adjudication_queue(
    repository: Repository,
    *,
    learning_object_id: str | None = None,
    reasons: Sequence[str] | None = None,
    limit: int | None = 20,
) -> list[AdjudicationQueueEntry]:
    """Attempts worth a verdict, highest information first.

    The `sampled` stratum is deliberately kept: an eval set drawn only from
    contests and abstentions is adversarially selected, and §3 B4's
    planted-vs-adjudicated agreement over such a set would not license using
    the synthetic numbers for anything. `queue_reason` is persisted so the
    stratification is recoverable after the fact.
    """

    if reasons is not None:
        unknown = set(reasons) - set(QUEUE_REASONS)
        if unknown:
            raise ValueError(f"unknown queue reasons: {sorted(unknown)}")
    already = repository.adjudicated_attempt_ids()
    entries: list[AdjudicationQueueEntry] = []
    for attempt in repository.list_all_attempts():
        attempt_id = str(attempt["id"])
        if attempt_id in already:
            continue
        if (
            learning_object_id is not None
            and str(attempt.get("learning_object_id") or "") != learning_object_id
        ):
            continue
        snapshot = diagnosis_snapshot(repository, attempt_id)
        if snapshot is None:
            continue
        report = latest_learner_report(repository, attempt_id)
        reason, detail = _queue_reason(snapshot, report)
        if reasons is not None and reason not in reasons:
            continue
        entries.append(
            AdjudicationQueueEntry(
                attempt_id=attempt_id,
                queue_reason=reason,
                priority=_QUEUE_PRIORITY[reason],
                detail=detail,
                created_at=str(attempt.get("created_at") or ""),
                learning_object_id=(
                    str(attempt["learning_object_id"])
                    if attempt.get("learning_object_id")
                    else None
                ),
                practice_item_id=(
                    str(attempt["practice_item_id"])
                    if attempt.get("practice_item_id")
                    else None
                ),
                snapshot=snapshot,
                learner_report=dict(report) if report is not None else None,
            )
        )
    entries.sort(key=lambda value: (value.priority, value.created_at, value.attempt_id))
    return entries[:limit] if limit is not None else entries


# ---------------------------------------------------------------------------
# Write path
# ---------------------------------------------------------------------------


def append_diagnosis_adjudication(
    repository: Repository,
    *,
    attempt_id: str,
    verdict: str,
    adjudicated_anchor: Mapping[str, Any] | None = None,
    adjudicated_repair_md: str | None = None,
    adjudicated_repair_class_id: str | None = None,
    queue_reason: str | None = None,
    adjudicator_source: str = "human_owner",
    rationale: str | None = None,
    learner_report_id: str | None = None,
    supersedes_id: str | None = None,
    vault: LoadedVault | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Append one verdict on one diagnosis. Never overwrites a prior verdict.

    Ergonomics matter here: in a single-learner vault the adjudicator is the
    learner, and annotation competes with learning time. So the common case —
    "the diagnosis was right" — needs no arguments beyond the verdict: the
    adjudicated anchor and repair are taken from the system's own choice,
    because that is exactly what `correct` asserts. `wrong_repair` likewise
    inherits the anchor, because it asserts the anchor was right.

    ``vault`` is optional and changes nothing about what is recorded — this store
    stays the ground truth of what was judged, not a belief mutator. Supplying it
    additionally applies §5.6 arm (d) immediately
    (``services/durable_promotion``): an affirming verdict promotes the asserted
    cause to a durable belief, and an overturning verdict retracts it and owes
    the learner an A6 correction. Without a vault the verdict is still recorded
    and the effect is picked up by the next normalization sweep on that learning
    object, so no verdict is ever silently inert.
    """

    if verdict not in VERDICTS:
        raise ValueError(f"unknown diagnosis verdict {verdict!r}")
    if adjudicator_source not in ADJUDICATOR_SOURCES:
        raise ValueError(
            f"unknown adjudicator source {adjudicator_source!r}; a bounded-trust "
            "learner clarification is not eval ground truth"
        )
    if queue_reason is not None and queue_reason not in QUEUE_REASONS:
        raise ValueError(f"unknown queue reason {queue_reason!r}")

    snapshot = diagnosis_snapshot(repository, attempt_id)
    if snapshot is None:
        raise ValueError("attempt has no diagnosis receipt to adjudicate")
    report = latest_learner_report(repository, attempt_id)
    if queue_reason is None:
        # Record the stratum this case actually came from. Defaulting to
        # `manual` would erase the selection structure §3 B4 needs.
        queue_reason, _ = _queue_reason(snapshot, report)

    if snapshot.system_abstained and verdict not in ABSTENTION_VERDICTS:
        raise ValueError(
            f"the system abstained on {attempt_id}; use "
            "'correctly_abstained' or 'should_not_have_abstained'"
        )
    if not snapshot.system_abstained and verdict not in FILLED_VERDICTS:
        raise ValueError(
            f"the system named a cause on {attempt_id}; "
            f"{verdict!r} is only recordable against an abstention"
        )

    anchor = dict(adjudicated_anchor) if adjudicated_anchor is not None else None
    if anchor is None and verdict in {"correct", "wrong_repair"}:
        # `correct` and `wrong_repair` both assert the system's anchor was
        # right, so it IS the adjudicated anchor.
        anchor = dict(snapshot.system_anchor) if snapshot.system_anchor else None
        if anchor is None:
            raise ValueError(
                "the system produced no first-divergence anchor, so it cannot be "
                "inherited; supply one, or record anchor_kind 'none' to adjudicate "
                "that no anchor exists"
            )
    if anchor is not None:
        kind = str(anchor.get("anchor_kind") or "")
        if kind not in ANCHOR_KINDS:
            raise ValueError(f"unknown adjudicated anchor kind {kind!r}")
    if verdict in ANCHOR_REQUIRED_VERDICTS and anchor is None:
        raise ValueError(
            f"{verdict!r} rules on the first-divergence anchor and therefore "
            "requires an adjudicated anchor"
        )

    repair_class_id = adjudicated_repair_class_id
    repair_md = adjudicated_repair_md
    if verdict == "correct" and repair_class_id is None and not repair_md:
        repair_class_id = snapshot.system_repair_class_id
    if repair_class_id is not None and repair_class_id not in snapshot.known_repair_class_ids:
        raise ValueError(
            f"repair class {repair_class_id!r} is not one this episode offered; "
            "record the adjudicated repair in prose instead — a repair outside "
            "the offered set is the finding, not a class id"
        )
    if verdict == "wrong_repair" and repair_class_id is None and not repair_md:
        raise ValueError(
            "'wrong_repair' requires the repair that should have been chosen"
        )

    if learner_report_id is None and report is not None:
        learner_report_id = str(report["id"])

    # Re-adjudication appends a successor; it never rewrites the verdict that
    # was actually recorded. The chain stays linear and single-headed, which is
    # what lets a rate count each attempt exactly once.
    active = repository.active_diagnosis_adjudication(attempt_id)
    head_id = str(active["id"]) if active is not None else None
    if supersedes_id is None:
        supersedes_id = head_id
    elif supersedes_id != head_id:
        raise ValueError(
            "a second opinion must supersede the current head "
            f"({head_id!r}), not {supersedes_id!r}"
        )

    adjudication_id = repository.insert_diagnosis_adjudication(
        values={
            "attempt_id": attempt_id,
            "diagnosis_receipt_id": snapshot.receipt_id,
            "verdict": verdict,
            "system_abstained": snapshot.system_abstained,
            "adjudicated_anchor": anchor,
            "adjudicated_anchor_kind": (
                str(anchor.get("anchor_kind")) if anchor is not None else None
            ),
            "adjudicated_repair_md": repair_md,
            "adjudicated_repair_class_id": repair_class_id,
            "queue_reason": queue_reason,
            "learner_report_id": learner_report_id,
            "adjudicator_source": adjudicator_source,
            "rationale": rationale,
            "decision_policy_version": snapshot.decision_policy_version,
            "repair_policy_version": snapshot.repair_policy_version,
            "grading_prompt_version": snapshot.grading_prompt_version,
            "grader_model": snapshot.grader_model,
            "receipt_schema_version": snapshot.receipt_schema_version,
            "system_snapshot": snapshot.as_dict(),
            "supersedes_id": supersedes_id,
        },
        clock=clock,
    )
    if vault is not None:
        # §5.6 arm (d). Runs AFTER the verdict is durable, so a failure to move
        # belief state can never lose the eval record — the verdict is the
        # ground truth this store exists for, the belief effect is downstream.
        from learnloop.services.durable_promotion import (
            apply_adjudicated_belief_effects,
        )

        apply_adjudicated_belief_effects(
            vault, repository, attempt_id=attempt_id, clock=clock
        )
    return repository.diagnosis_adjudication(adjudication_id) or {}


# ---------------------------------------------------------------------------
# Read paths: the scoreboard, and the B4 join key
# ---------------------------------------------------------------------------


def _empty_group(**identity: Any) -> dict[str, Any]:
    return {
        **identity,
        "records": 0,
        "by_verdict": {verdict: 0 for verdict in VERDICTS},
        "by_queue_reason": {reason: 0 for reason in QUEUE_REASONS},
        "anchor_scored": 0,
        "anchor_correct": 0,
        "repair_id_scored": 0,
        "repair_id_match": 0,
        "abstention_confusion": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
    }


def _finalize(group: dict[str, Any]) -> dict[str, Any]:
    confusion = group["abstention_confusion"]
    predicted = confusion["tp"] + confusion["fp"]
    actual = confusion["tp"] + confusion["fn"]
    verdicts = group["by_verdict"]
    group["first_divergence_anchor_accuracy"] = (
        group["anchor_correct"] / group["anchor_scored"]
        if group["anchor_scored"]
        else None
    )
    # `correct` is the only verdict asserting the system's repair was the right
    # one. The denominator is the same set of verdicts that scored the anchor:
    # `should_have_abstained` is excluded from both because it says the
    # diagnosis should not have proposed anything, and scoring its repair would
    # reward filling.
    group["repair_class_match_rate"] = (
        verdicts["correct"] / group["anchor_scored"]
        if group["anchor_scored"]
        else None
    )
    group["repair_class_id_match_rate"] = (
        group["repair_id_match"] / group["repair_id_scored"]
        if group["repair_id_scored"]
        else None
    )
    # `None`, never 1.0, when the denominator is empty. An abstention
    # precision of 1.0 computed over zero abstentions is the exact false
    # comfort standing constraint 2's two-tailed watch exists to prevent.
    group["abstention_precision"] = (
        confusion["tp"] / predicted if predicted else None
    )
    group["abstention_recall"] = confusion["tp"] / actual if actual else None
    group["abstention_cases_present"] = bool(predicted or actual)
    return group


def diagnosis_adjudication_scoreboard(
    repository: Repository,
    *,
    group_by: str | None = "version",
    attempt_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    """The §3 B5 metrics this store owns, over the active verdicts.

    ``group_by``: ``"version"`` (grading prompt version x grader model, the
    slice §3 B5 requires), ``"queue_reason"`` (the selection-bias audit), or
    ``None`` for the pooled numbers only.
    """

    if group_by not in {None, "version", "queue_reason"}:
        raise ValueError(f"unknown scoreboard grouping {group_by!r}")
    rows = repository.list_diagnosis_adjudications(
        active_only=True, attempt_ids=attempt_ids
    )
    overall = _empty_group(scope="overall")
    groups: dict[Any, dict[str, Any]] = {}
    for row in rows:
        verdict = str(row["verdict"])
        snapshot = row.get("system_snapshot") or {}
        targets = [overall]
        if group_by == "version":
            key = (
                str(row.get("grading_prompt_version") or "unknown"),
                str(row.get("grader_model") or "unknown"),
            )
            targets.append(
                groups.setdefault(
                    key,
                    _empty_group(grading_prompt_version=key[0], grader_model=key[1]),
                )
            )
        elif group_by == "queue_reason":
            key = str(row.get("queue_reason") or "manual")
            targets.append(
                groups.setdefault(key, _empty_group(queue_reason=key))
            )
        for group in targets:
            group["records"] += 1
            group["by_verdict"][verdict] = group["by_verdict"].get(verdict, 0) + 1
            reason = str(row.get("queue_reason") or "manual")
            group["by_queue_reason"][reason] = (
                group["by_queue_reason"].get(reason, 0) + 1
            )
            if verdict in ANCHOR_SCORED_VERDICTS:
                group["anchor_scored"] += 1
                if verdict in ANCHOR_CORRECT_VERDICTS:
                    group["anchor_correct"] += 1
            system_repair = snapshot.get("system_repair_class_id")
            adjudicated_repair = row.get("adjudicated_repair_class_id")
            if system_repair and adjudicated_repair:
                group["repair_id_scored"] += 1
                if str(system_repair) == str(adjudicated_repair):
                    group["repair_id_match"] += 1
            confusion = group["abstention_confusion"]
            if row.get("system_abstained"):
                confusion["tp" if verdict == "correctly_abstained" else "fp"] += 1
            elif verdict == "should_have_abstained":
                confusion["fn"] += 1
            else:
                confusion["tn"] += 1
    return {
        "store_version": ADJUDICATION_STORE_VERSION,
        "group_by": group_by,
        "overall": _finalize(overall),
        "groups": [_finalize(groups[key]) for key in sorted(groups)],
    }


def adjudicated_ground_truth(
    repository: Repository, *, attempt_ids: Sequence[str] | None = None
) -> dict[str, dict[str, Any]]:
    """Adjudicated labels keyed by attempt — the join key for §3 B4.

    B4 asks for *agreement between planted and adjudicated ground truth on the
    overlap*. That comparison needs the adjudicated label in the same shape as
    a planted one: should the diagnosis have abstained, where is the true
    anchor, and which repair. Returning it here means the planted harness never
    has to re-derive verdict semantics.
    """

    labels: dict[str, dict[str, Any]] = {}
    for row in repository.list_diagnosis_adjudications(
        active_only=True, attempt_ids=attempt_ids
    ):
        verdict = str(row["verdict"])
        labels[str(row["attempt_id"])] = {
            "adjudication_id": row["id"],
            "verdict": verdict,
            "should_abstain": verdict
            in {"should_have_abstained", "correctly_abstained"},
            "system_abstained": bool(row["system_abstained"]),
            "anchor": row.get("adjudicated_anchor"),
            "anchor_key": anchor_key(row.get("adjudicated_anchor")),
            "repair_class_id": row.get("adjudicated_repair_class_id"),
            "repair_md": row.get("adjudicated_repair_md"),
            "queue_reason": row.get("queue_reason"),
            "grading_prompt_version": row.get("grading_prompt_version"),
            "grader_model": row.get("grader_model"),
            "decision_policy_version": row.get("decision_policy_version"),
            "repair_policy_version": row.get("repair_policy_version"),
        }
    return labels
