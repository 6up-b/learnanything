"""Missing-vocabulary notes: the system's record of what it could not name.

Augmentation A5 (``spec_diagnostic_augmentation_v1`` §2 A5) plus causal §5.8
rule 4.  An abstention is the only signal that says "the vocabulary cannot name
what happened here", it cannot be reconstructed after the fact (standing
constraint 6), and before this module the signal died on the attribution row
that recorded it.

**Capture only.**  Clustering by repair equivalence, facet proposals, and the
review surface are Phase D.  What lands here is the raw material: the trace, the
criterion, the reason, the selected repair, the item context, and the version set
under which the refusal was made.

Two producers, deliberately sharing one store:

* ``diagnostic_abstention`` — the grader declined to name a cause
  (``resolution_status='abstained'`` with a typed ``abstention_reason``).
* ``authoring_facet_abstention`` — an authored/variant item declined to inherit
  canonical facets because the registry has no word for what a criterion
  measures (``measurement_status`` of ``no_canonical_facet`` / ``item_local``,
  causal §5.8 rule 4: "an abstention here becomes a missing-vocabulary note").

Both are the same inadequacy seen from opposite ends of the loop; ``source``
keeps them separable so a Phase D cluster drawn from only one end is visible as
such.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from learnloop.attempts.ai_contracts import GRADING_PROMPT_VERSION
from learnloop.clock import Clock
from learnloop.content.proposals.ai_contracts import AUTHORING_PROMPT_VERSION
from learnloop.db.repositories import Repository

#: Bumped when the captured payload's shape changes, so a Phase D cluster can
#: tell a vocabulary gap from an artifact of how the note was recorded.
MISSING_VOCABULARY_NOTE_VERSION = "missing_vocabulary_v1"

NOTE_SOURCES = ("diagnostic_abstention", "authoring_facet_abstention")

#: The authoring-side statuses that ARE abstentions.  ``item_local`` says "this
#: criterion is genuinely item-specific" and ``no_canonical_facet`` says "the
#: registry lacks the word"; both decline to name canonical vocabulary, and only
#: the second is a request for new vocabulary.  Both are captured, separated by
#: ``abstention_reason``, because deciding which is which is Phase D's job and
#: throwing one away now would prejudge it.
FACET_ABSTAINING_STATUSES = ("item_local", "no_canonical_facet")


def _content_id(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return f"mvn_{hashlib.sha256(encoded).hexdigest()[:26]}"


def _version_stamps(
    repository: Repository, attempt_id: str | None
) -> dict[str, Any]:
    """The A4 version set, read from durable rows plus in-force constants.

    ``prompt_version`` is preferred from the attempt's own telemetry when it is
    there, so a note written while re-materializing an old attempt records the
    prompt that actually abstained rather than today's.
    """

    from learnloop.diagnosis.causal_attribution import (
        CAUSAL_DECISION_POLICY_VERSION,
        REPAIR_POLICY_VERSION,
    )

    prompt_version: str | None = None
    run: Mapping[str, Any] = {}
    run_id: str | None = None
    if attempt_id:
        debug = repository.attempt_debug_payload(attempt_id) or {}
        telemetry = debug.get("causal_attribution")
        if isinstance(telemetry, Mapping) and telemetry.get("prompt_version"):
            prompt_version = str(telemetry["prompt_version"])
        metadata = repository.fetch_attempt_feedback_metadata(attempt_id) or {}
        raw_run_id = metadata.get("agent_run_id")
        if raw_run_id:
            run_id = str(raw_run_id)
            run = repository.agent_run(run_id) or {}
    return {
        "grading_prompt_version": prompt_version or GRADING_PROMPT_VERSION,
        "decision_policy_version": CAUSAL_DECISION_POLICY_VERSION,
        "repair_policy_version": REPAIR_POLICY_VERSION,
        "grader_model": str(run["model"]) if run.get("model") else None,
        "grader_provider": str(run["provider"]) if run.get("provider") else None,
        "grader_provider_revision": (
            str(run["provider_revision"]) if run.get("provider_revision") else None
        ),
        "agent_run_id": run_id,
    }


def _note_id(note: Mapping[str, Any]) -> str:
    """Content-address a note over what makes it the same refusal.

    ``created_at`` is excluded: re-materializing an episode must not mint a
    second note for one abstention.  The version stamps ARE included — the same
    abstention under a new prompt version is a new data point, and collapsing
    them would hide exactly the artifact the stamps exist to expose.
    """

    return _content_id(
        {
            key: note.get(key)
            for key in (
                "source",
                "abstention_reason",
                "learning_object_id",
                "practice_item_id",
                "attempt_id",
                "error_event_id",
                "criterion_id",
                "grading_prompt_version",
                "decision_policy_version",
                "repair_policy_version",
                "grader_model",
                "grader_provider_revision",
                "note_version",
            )
        }
    )


def record_missing_vocabulary_notes(
    repository: Repository,
    notes: Sequence[Mapping[str, Any]],
    *,
    clock: Clock | None = None,
) -> int:
    """Append notes, skipping ones already recorded. Returns the count written."""

    prepared: list[dict[str, Any]] = []
    for note in notes:
        source = str(note.get("source") or "")
        if source not in NOTE_SOURCES:
            raise ValueError(f"unknown missing-vocabulary note source {source!r}")
        if not str(note.get("abstention_reason") or "").strip():
            raise ValueError("a missing-vocabulary note requires an abstention reason")
        payload = {
            "note_version": MISSING_VOCABULARY_NOTE_VERSION,
            **{key: value for key, value in note.items()},
        }
        payload["id"] = _note_id(payload)
        prepared.append(payload)
    return repository.insert_missing_vocabulary_notes(prepared, clock=clock)


# ---------------------------------------------------------------------------
# Producer 1: the diagnostician abstained (§2 A5)
# ---------------------------------------------------------------------------


def diagnostic_abstention_notes(
    repository: Repository,
    *,
    attempt_id: str,
    selected_repair_class_id: str | None = None,
    repair_equivalence_id: str | None = None,
) -> list[dict[str, Any]]:
    """Build one note per abstaining attribution on an attempt.

    Reads the error events rather than the grading proposal, because that is the
    durable record and it is what a regrade re-derives.
    """

    attempt = repository.fetch_practice_attempt(attempt_id) or {}
    notes: list[dict[str, Any]] = []
    stamps = _version_stamps(repository, attempt_id)
    for event in repository.error_events_for_attempt(attempt_id):
        plan = event.get("repair_plan")
        plan = plan if isinstance(plan, Mapping) else {}
        if str(plan.get("resolution_status") or "") != "abstained":
            continue
        reason = str(plan.get("abstention_reason") or "").strip()
        if not reason:
            # The schema requires a reason with an abstention
            # (``learnloop.content.proposals.ai_contracts`` validates it), so an
            # untyped abstention is a
            # defect upstream. Record it as such rather than dropping the note:
            # a silent drop here would understate the abstention rate, which is
            # the one number this store exists to make readable.
            reason = "unspecified_abstention_reason"
        criterion_ids = [
            str(value) for value in plan.get("target_criterion_ids") or []
        ]
        first_divergence = plan.get("first_divergence")
        trace = {
            "learner_answer_md": str(attempt.get("learner_answer_md") or ""),
            "first_divergence": (
                dict(first_divergence)
                if isinstance(first_divergence, Mapping)
                else None
            ),
            "evidence": plan.get("evidence"),
            "error_type": event.get("error_type"),
            "misconception_statement": event.get("misconception_statement"),
        }
        item_context = {
            "practice_item_id": str(attempt.get("practice_item_id") or ""),
            "attempt_type": attempt.get("attempt_type"),
            "target_evidence_families": [
                str(value) for value in plan.get("target_evidence_families") or []
            ],
            "cause_scope": plan.get("cause_scope"),
            "operation": plan.get("operation"),
        }
        # One note per named criterion, and one criterion-less note when the
        # abstention did not localize: "which criterion" is part of what the
        # vocabulary failed to say, so a null there is data.
        for criterion_id in criterion_ids or [None]:
            notes.append(
                {
                    "source": "diagnostic_abstention",
                    "abstention_reason": reason,
                    "learning_object_id": str(
                        attempt.get("learning_object_id") or ""
                    )
                    or None,
                    "practice_item_id": str(attempt.get("practice_item_id") or "")
                    or None,
                    "attempt_id": attempt_id,
                    "error_event_id": str(event["id"]),
                    "criterion_id": criterion_id,
                    "trace": trace,
                    "item_context": item_context,
                    "selected_repair_class_id": selected_repair_class_id,
                    "repair_equivalence_id": repair_equivalence_id,
                    **stamps,
                }
            )
    return notes


def record_diagnostic_abstention_notes(
    repository: Repository,
    *,
    attempt_id: str,
    selected_repair_class_id: str | None = None,
    repair_equivalence_id: str | None = None,
    clock: Clock | None = None,
) -> int:
    return record_missing_vocabulary_notes(
        repository,
        diagnostic_abstention_notes(
            repository,
            attempt_id=attempt_id,
            selected_repair_class_id=selected_repair_class_id,
            repair_equivalence_id=repair_equivalence_id,
        ),
        clock=clock,
    )


# ---------------------------------------------------------------------------
# Producer 2: an authored item abstained from canonical facets (§5.8 rule 4)
# ---------------------------------------------------------------------------


def authoring_facet_abstention_notes(
    payload: Mapping[str, Any],
    *,
    practice_item_id: str | None = None,
    detail: Mapping[str, Any] | None = None,
    version_stamps: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Notes for the criteria of one authored item that named no canonical facet."""

    from learnloop.diagnosis.causal_attribution import (
        CAUSAL_DECISION_POLICY_VERSION,
        REPAIR_POLICY_VERSION,
    )

    rubric = payload.get("grading_rubric")
    criteria = rubric.get("criteria") if isinstance(rubric, Mapping) else None
    item_id = practice_item_id or str(payload.get("id") or "") or None
    stamps = {
        # The database column predates authoring-side notes and retains the
        # generic name. Its value must be the prompt that actually made this
        # authoring refusal, never the unrelated grading prompt.
        "grading_prompt_version": AUTHORING_PROMPT_VERSION,
        "decision_policy_version": CAUSAL_DECISION_POLICY_VERSION,
        "repair_policy_version": REPAIR_POLICY_VERSION,
        "grader_model": None,
        "grader_provider": None,
        "grader_provider_revision": None,
        "agent_run_id": None,
        **dict(version_stamps or {}),
    }
    notes: list[dict[str, Any]] = []
    for criterion in criteria or []:
        if not isinstance(criterion, Mapping):
            continue
        status = str(criterion.get("measurement_status") or "")
        if status not in FACET_ABSTAINING_STATUSES:
            continue
        notes.append(
            {
                "source": "authoring_facet_abstention",
                "abstention_reason": status,
                "learning_object_id": str(payload.get("learning_object_id") or "")
                or None,
                "practice_item_id": item_id,
                "attempt_id": None,
                "error_event_id": None,
                "criterion_id": str(criterion.get("id") or "") or None,
                # The "trace" of an authoring abstention is the criterion itself:
                # the thing the registry could not name.
                "trace": {
                    "criterion_title": criterion.get("title"),
                    "criterion_description": criterion.get("description"),
                    "measurement_status": status,
                },
                "item_context": {
                    "practice_item_id": item_id,
                    "capability": payload.get("capability"),
                    "surface_family": payload.get("surface_family"),
                    "evidence_facets": [
                        str(value) for value in payload.get("evidence_facets") or []
                    ],
                    "variant_contract": payload.get("variant_contract"),
                },
                **stamps,
                "detail": dict(detail or {}),
            }
        )
    return notes


def record_authoring_facet_abstention_notes(
    repository: Repository,
    items: Sequence[Mapping[str, Any]],
    *,
    patch_id: str | None = None,
    clock: Clock | None = None,
) -> int:
    """Capture facet abstentions from accepted proposal items (§5.8 rule 4).

    ``items`` are proposal rows; the edited payload wins over the generated one,
    because a reviewer who filled the facets in has withdrawn the abstention.
    """

    notes: list[dict[str, Any]] = []
    batch = repository.proposal_batch(patch_id) if patch_id else None
    run_id = (
        str(batch["agent_run_id"])
        if batch is not None and batch.get("agent_run_id")
        else None
    )
    run = repository.agent_run(run_id) if run_id else None
    authoring_stamps = {
        "grading_prompt_version": (
            str(run["prompt_version"])
            if run is not None and run.get("prompt_version")
            else None
        ),
        "grader_model": (
            str(run["model"]) if run is not None and run.get("model") else None
        ),
        "grader_provider": (
            str(run["provider"])
            if run is not None and run.get("provider")
            else None
        ),
        "grader_provider_revision": (
            str(run["provider_revision"])
            if run is not None and run.get("provider_revision")
            else None
        ),
        "agent_run_id": run_id,
    }
    # Do not overwrite the in-force authoring prompt fallback with a null from
    # a legacy proposal batch that had no run row.
    authoring_stamps = {
        key: value for key, value in authoring_stamps.items() if value is not None
    }
    for item in items:
        payload = (
            item.get("edited_payload")
            if item.get("edited_payload") is not None
            else item.get("payload")
        )
        if not isinstance(payload, Mapping):
            continue
        if str(item.get("item_type") or "practice_item") != "practice_item":
            continue
        notes.extend(
            authoring_facet_abstention_notes(
                payload,
                version_stamps=authoring_stamps,
                detail={
                    "patch_id": patch_id,
                    "proposal_item_id": item.get("id"),
                    "purpose": item.get("purpose"),
                },
            )
        )
    return record_missing_vocabulary_notes(repository, notes, clock=clock)


# ---------------------------------------------------------------------------
# The rate nobody was reading (§2 A5, standing constraint 2)
# ---------------------------------------------------------------------------


def missing_vocabulary_report(repository: Repository) -> dict[str, Any]:
    """Note counts by source and reason, plus the diagnostic abstention RATE.

    The rate's denominator is attributions, not notes: an attempt with three
    abstaining attributions is three signals, and a store that only reported its
    own row count could never say whether abstention is rising or the vault is
    simply busier.
    """

    notes = repository.missing_vocabulary_notes()
    by_source: dict[str, int] = {}
    by_reason: dict[str, dict[str, int]] = {}
    by_learning_object: dict[str, int] = {}
    for note in notes:
        source = str(note.get("source") or "unknown")
        reason = str(note.get("abstention_reason") or "unknown")
        by_source[source] = by_source.get(source, 0) + 1
        by_reason.setdefault(source, {})
        by_reason[source][reason] = by_reason[source].get(reason, 0) + 1
        learning_object_id = str(note.get("learning_object_id") or "")
        if learning_object_id:
            by_learning_object[learning_object_id] = (
                by_learning_object.get(learning_object_id, 0) + 1
            )
    attributions = 0
    abstentions = 0
    for attempt in repository.list_all_attempts():
        debug = repository.attempt_debug_payload(str(attempt["id"])) or {}
        telemetry = debug.get("causal_attribution")
        if not isinstance(telemetry, Mapping):
            continue
        attributions += int(telemetry.get("attribution_count") or 0)
        counts = telemetry.get("resolution_counts")
        counts = counts if isinstance(counts, Mapping) else {}
        abstentions += int(counts.get("abstained") or 0)
    return {
        "note_version": MISSING_VOCABULARY_NOTE_VERSION,
        "notes": len(notes),
        "by_source": by_source,
        "by_reason": by_reason,
        "by_learning_object": dict(sorted(by_learning_object.items())),
        "attributions": attributions,
        "abstentions": abstentions,
        "abstention_rate": (
            round(abstentions / attributions, 6) if attributions else 0.0
        ),
        # A diagnostic abstention that produced no note is a capture hole, and it
        # is the one failure this module cannot detect after the fact.
        "uncaptured_diagnostic_abstentions": max(
            0, abstentions - by_source.get("diagnostic_abstention", 0)
        ),
    }
