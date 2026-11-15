"""Jointly graded attempts and joint regrades, written as stored history.

Before the diagnosis split (``mvp-0.10``), and while its kill switch was off, the
practice door graded an answer and diagnosed it in one call (the joint grader):
no blind record, a C2/C4-augmented context, a Phase-C receipt with no grader
mode, a ``joint_grader`` grading record. Owner vaults still hold such attempts,
and replay, regrade, the feedback bundle, placement and every report read them.
No door writes one now, so a test that needs one as history builds it here: the
same rows the joint door wrote, from a given grading proposal, without a model
call. ``tests/test_joint_grading_builder.py`` pins the rows this module writes.

Three builders, one per joint writer that is gone:

- :func:`write_joint_graded_attempt`, the practice door's joint arm;
- :func:`write_joint_regrade`, a regrade of a practice attempt with no blind
  record, which graded jointly with the split off;
- :func:`joint_vault_door`, the door every grader outside the practice door
  shares (teach-back, exams, teacher checks and probes), which graded with the
  joint prompt and recorded the joint (``None``) calibration identity.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import replace
from typing import Any

from learnloop.ai.runs import finish_agent_run
from learnloop.ai.usage import TokenUsage
from learnloop.attempts.ai_contracts import GradingProposal, StuckGradingProposal, grading_prompt_version
from learnloop.attempts.attempts import AttemptDraft, AttemptResult, complete_codex_graded_attempt, validate_attempt_draft
from learnloop.attempts.grading import build_grading_context, grading_context_hash, resolved_rubric
from learnloop.attempts.stuck import record_stuck_reading_judgment, stuck_answer_prompt, verified_stuck_reading
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores.write_provenance import grading_in_progress, record_grading
from learnloop.diagnosis.diagnostic_augmentation import (
    PHASE_C_HYPOTHESES,
    PHASE_C_REVERT_CRITERIA,
    diagnostic_verifier_observations,
)
from learnloop.ids import new_ulid
from learnloop.vault.models import LoadedVault

#: What the joint grader was shown of earlier answers (C4): up to this many raw
#: traces on the same facet and surface family (``[diagnostic_augmentation]
#: history_limit``'s default).
JOINT_HISTORY_LIMIT = 4

#: A proposal, or a function of the joint grading context that returns one (a
#: fake grader answering from the context it is sent, as the joint door's
#: clients did). A :class:`StuckGradingProposal` carries the stuck reading.
Proposal = GradingProposal | Callable[[Any], GradingProposal]


def _proposal_for(proposal: Proposal, context: Any) -> GradingProposal:
    return proposal(context) if callable(proposal) else proposal


def joint_history(vault: LoadedVault, repository: Repository, item: Any, *, limit: int = JOINT_HISTORY_LIMIT) -> list[dict[str, Any]]:
    """The C4 history the joint grader was shown: the latest raw traces of the
    item's learning object on a shared facet and the same surface family,
    oldest first (no prior diagnosis: the grader saw recurrence, not the
    system's old answer)."""

    wanted_facets = {vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets}
    wanted_surface = item.surface_family or item.id
    history: list[dict[str, Any]] = []
    for attempt in repository.list_recent_attempts_by_learning_object(item.learning_object_id, limit=max(limit * 5, limit)):
        previous = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
        if previous is None:
            continue
        previous_facets = {vault.canonical_facet_id(str(facet)) for facet in previous.evidence_facets}
        previous_surface = previous.surface_family or previous.id
        if not (wanted_facets & previous_facets) or previous_surface != wanted_surface:
            continue
        trace = str(attempt.get("learner_answer_md") or "").strip()
        if not trace:
            continue
        history.append(
            {
                "attempt_id": str(attempt["id"]),
                "learner_trace_md": trace,
                "created_at": attempt.get("created_at"),
                "surface_family": previous_surface,
                "shared_facets": sorted(wanted_facets & previous_facets),
            }
        )
        if len(history) >= limit:
            break
    history.reverse()
    return history


def joint_grading_context(vault: LoadedVault, repository: Repository, draft: AttemptDraft, *, attempt_id: str) -> Any:
    """The context the joint door graded ``draft`` under: the item (or its
    frozen assessment contract), the stuck prompt for a stuck answer, the C2
    verifier observations and the C4 history."""

    item = vault.practice_items[draft.practice_item_id]
    contract = None
    if draft.assessment_contract_version_id is not None:
        stored = repository.fetch_assessment_contract_version(draft.assessment_contract_version_id)
        contract = (stored or {}).get("contract") or {}
    if contract is not None:
        from learnloop.learner.assessment_contracts import rubric_from_contract

        rubric = rubric_from_contract(contract)
    else:
        rubric = resolved_rubric(vault, item)
    context = build_grading_context(
        vault, item, attempt_id=attempt_id, learner_answer_md=draft.learner_answer_md, rubric=rubric,
        assessment_contract=contract,
    )
    if draft.declared_stuck:
        context = replace(context, answer_prompt=stuck_answer_prompt())
    return replace(
        context,
        verifier_observations=diagnostic_verifier_observations(context.learner_answer_md, context.expected_answer),
        diagnostic_history=joint_history(vault, repository, item),
    )


def _provider_fields(provider: str, provider_type: str | None, model: str | None) -> dict[str, Any]:
    fields: dict[str, Any] = {"provider": provider, "provider_type": provider_type, "model": model, "provider_revision": None}
    if provider == "codex" or provider_type == "codex_sdk":
        fields["codex_revision"] = None
    return fields


def write_joint_graded_attempt(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    proposal: Proposal,
    *,
    grading_source: str = "ai",
    provider: str = "fake",
    provider_type: str | None = "codex_sdk",
    model: str | None = "fake-model",
    usage: TokenUsage | None = None,
    clock: Clock | None = None,
) -> AttemptResult:
    """One practice answer graded jointly, as the joint door recorded it.

    The grading run (the joint prompt's version and context hash,
    ``GradingProposal``), the attempt and its application, a stuck answer's
    reading in ``judgment_ledger``, the Phase-C receipt (k = 1, the C4 history
    ids, no grader mode) and the ``joint_grader`` grading record, in the one
    transaction the door used; then the run completes with ``usage`` (the
    door's client reported none for the fakes this replaces: zero tokens).
    The answer must need a model grade (not an empty stuck answer, not an
    option letter the deterministic grader reads). The post-attempt pipeline
    is the caller's, as it was after the door.
    """

    draft = validate_attempt_draft(vault, repository, draft, clock=clock)
    attempt_id = new_ulid()
    context = joint_grading_context(vault, repository, draft, attempt_id=attempt_id)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "grading",
            **_provider_fields(provider, provider_type, model),
            "prompt_template": "grading",
            "prompt_version": grading_prompt_version(context),
            "input_context_hash": grading_context_hash(context),
            "output_schema": "GradingProposal",
            "started_at": utc_now_iso(clock),
            "status": "running",
        }
    )
    graded = _proposal_for(proposal, context)
    marker = None
    if isinstance(graded, StuckGradingProposal):
        marker = verified_stuck_reading(graded.stuck_reading, draft.learner_answer_md)
        graded = graded.as_grading_proposal()
    shown = [row.get("attempt_id") for row in context.diagnostic_history or ()]
    with repository.atomic(), grading_in_progress(attempt_id, shown_history=shown):
        result = complete_codex_graded_attempt(
            vault, repository, draft, graded, attempt_id=attempt_id, agent_run_id=agent_run_id,
            grading_source=grading_source, diagnostic_sample_support=None, clock=clock,
        )
        if marker is not None:
            record_stuck_reading_judgment(
                repository.connection(), attempt_id=attempt_id, marker=marker, judge_model=model,
                prompt_version=grading_prompt_version(context), input_hash=grading_context_hash(context),
                created_at=utc_now_iso(clock),
            )
        repository.insert_diagnostic_augmentation_receipt(
            {
                "attempt_id": attempt_id,
                "grading_prompt_version": grading_prompt_version(context),
                "grader_provider": provider,
                "grader_model": model,
                "c1_repair_before_structure": True,
                "c2_verifier_observations": context.verifier_observations,
                "c3_sample_count": 1,
                "c3_agreement_support": 1.0,
                "c3_disagreement_causes": [],
                "c4_history_attempt_ids": [row["attempt_id"] for row in context.diagnostic_history if row.get("attempt_id")],
                "hypotheses": PHASE_C_HYPOTHESES,
                "revert_criteria": PHASE_C_REVERT_CRITERIA,
            },
            clock=clock,
        )
        record_grading(
            repository.connection(), attempt_id=result.attempt_id, writer="joint_grader", shown_history=shown, clock=clock,
        )
    finish_agent_run(repository, agent_run_id, usage=usage or TokenUsage(), clock=clock)
    return result


def write_joint_regrade(
    vault: LoadedVault,
    repository: Repository,
    attempt_id: str,
    proposal: Proposal,
    *,
    grading_source: str = "ai",
    purpose: str = "grading_regrade",
    provider: str = "fake",
    provider_type: str | None = "codex_sdk",
    model: str | None = "fake-model",
    usage: TokenUsage | None = None,
    clock: Clock | None = None,
) -> Any:
    """A joint regrade of a practice attempt with no blind record, as
    ``regrade_attempt`` recorded it with the split off: the item as it is now
    (or the contract a method-explicit answer froze), the stuck prompt for a
    stuck answer, no C4 history, the joint run identity; one publication with
    no blind record (so replay keeps the joint identity, ``None``), the route
    rule's verdict ``not_checked`` and a stuck answer's new reading. Returns
    the validated grade, as the regrade did."""

    from learnloop.attempts import regrade as regrade_module
    from learnloop.attempts.attempts import attempt_graded_contract, regrade_reads_contract
    from learnloop.attempts.grading import validate_codex_grading_proposal
    from learnloop.attempts.grading_support import record_route_rule_judgment

    attempt = repository.fetch_practice_attempt(attempt_id)
    assert attempt is not None, attempt_id
    assert repository.latest_blind_grade_record(attempt_id) is None, "a blind-graded attempt always regraded blind"
    assert attempt.get("attempt_type") != "teach_back", "teach-back regrades through the vault door"
    item = vault.practice_items[attempt["practice_item_id"]]
    learning_object = vault.learning_objects[attempt["learning_object_id"]]
    graded_contract = attempt_graded_contract(repository, attempt_id)
    reads_contract = regrade_reads_contract(vault, item, graded_contract)
    rubric = graded_contract.rubric() if reads_contract else resolved_rubric(vault, item)
    old_evidence = repository.fetch_grading_evidence(attempt_id)
    answer = attempt.get("learner_answer_md") or ""
    context = build_grading_context(
        vault, item, attempt_id=attempt_id, learner_answer_md=answer, rubric=rubric,
        assessment_contract=graded_contract.contract if reads_contract else None,
    )
    if attempt.get("declared_stuck"):
        context = replace(context, answer_prompt=stuck_answer_prompt())
    identity = {
        "prompt_version": grading_prompt_version(context),
        "input_context_hash": grading_context_hash(context),
        "output_schema": "GradingProposal",
    }
    now = utc_now_iso(clock)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(), "purpose": purpose, **_provider_fields(provider, provider_type, model),
            "prompt_template": "grading", **identity, "started_at": now, "status": "running",
        }
    )
    graded = _proposal_for(proposal, context)
    stuck_judgment = None
    if isinstance(graded, StuckGradingProposal):
        stuck_judgment = {
            "marker": verified_stuck_reading(graded.stuck_reading, answer),
            "prompt_version": identity["prompt_version"],
            "input_hash": identity["input_context_hash"],
        }
        graded = graded.as_grading_proposal()
    validated = validate_codex_grading_proposal(
        graded, attempt_id=attempt_id, item=item, vault=vault, learner_answer_md=answer, rubric=rubric,
    )
    old_score = int(attempt["rubric_score"] or 0)
    new_score = validated.rubric_score
    first_new_evidence_id = new_ulid()
    new_evidence_rows = []
    for index, evidence in enumerate(validated.criterion_evidence):
        new_evidence_rows.append(
            {
                "id": first_new_evidence_id if index == 0 else new_ulid(),
                "criterion_id": evidence.criterion_id,
                "points_awarded": evidence.points_awarded,
                "evidence": evidence.evidence,
                "notes": evidence.notes,
                "agent_run_id": agent_run_id,
                "local_grader_id": None,
                "grader_tier": 3,
                "created_at": now,
                **(
                    {"assessment_contract_version_id": graded_contract.version_id}
                    if reads_contract and graded_contract is not None
                    else {}
                ),
            }
        )
    primary_error_type = (
        max(validated.error_attributions, key=lambda attribution: attribution.severity).error_type
        if validated.error_attributions
        else None
    )
    content_events = []
    if abs(new_score - old_score) >= 2:
        content_events.append(
            {
                "id": new_ulid(),
                "event_type": "regrade_disagreement",
                "subject": attempt.get("subject"),
                "entity_type": "practice_item",
                "entity_id": item.id,
                "origin": grading_source,
                "review_status": "accepted",
                "summary": regrade_module._disagreement_summary(old_evidence, new_evidence_rows, old_score, new_score),
                "created_at": now,
            }
        )
    with repository.atomic(), grading_in_progress(attempt_id):
        regrade_module._publish_regrade(
            vault, repository, attempt, item=item, learning_object=learning_object, validated=validated,
            agent_run_id=agent_run_id, new_evidence_rows=new_evidence_rows, first_new_evidence_id=first_new_evidence_id,
            new_score=new_score, rubric=rubric,
            bind_frozen=graded_contract if reads_contract and graded_contract is not None else None,
            primary_error_type=primary_error_type, content_events=content_events, blind_record=None, prior_blind=None,
            blind_context_hash=None, grader_identity_overrides={attempt_id: None}, clock=clock,
            grading_source=grading_source,
        )
        record_route_rule_judgment(
            repository.connection(), attempt_id=attempt_id, grading_support={}, judge_model=model,
            prompt_version=identity["prompt_version"], input_hash=identity["input_context_hash"], created_at=now,
        )
        if stuck_judgment is not None:
            record_stuck_reading_judgment(
                repository.connection(), attempt_id=attempt_id, judge_model=model, created_at=now, **stuck_judgment,
            )
    finish_agent_run(repository, agent_run_id, usage=usage or TokenUsage(), clock=clock)
    return validated


@contextmanager
def joint_vault_door(patch) -> Iterator[None]:
    """Inside, the graders outside the practice door grade jointly, as they did
    with the split off: the joint prompt and its run identity, the joint
    proposal applied as the grader wrote it, and the joint calibration identity
    (``None``) on the raw grade. ``patch`` is a ``pytest.MonkeyPatch``; every
    module that took the door's three functions by name is patched with them."""

    from learnloop.attempts import grading, regrade
    from learnloop.attempts.grading import request_grading_proposal
    from learnloop.tutor import teach_back

    def joint_proposal(_vault, client, context):
        return request_grading_proposal(client, context)

    def joint_run_identity(*args):
        context = args[-1]
        return {
            "prompt_version": grading_prompt_version(context),
            "input_context_hash": grading_context_hash(context),
            "output_schema": "GradingProposal",
        }

    def joint_calibration_identity(*_args):
        return None

    replacements = {
        "request_vault_grading_proposal": joint_proposal,
        "vault_grading_run_identity": joint_run_identity,
        "vault_grading_calibration_identity": joint_calibration_identity,
    }
    with patch.context() as scoped:
        for module in (grading, regrade, teach_back):
            for name, replacement in replacements.items():
                if hasattr(module, name):
                    scoped.setattr(module, name, replacement)
        yield
