"""Lesson checks (spec_teacher_v1 §12, §12.1, §12.2): minted, held, graded blind, entered at a learned mass.

* **Minted held items.** A check the teacher poses becomes a practice item
  (``origin = codex_proposal``, ``mechanism = teacher_lesson_v1``, the lesson and
  node ids, span ``source_refs`` for its anchors), its committed solution the
  expected answer and its criteria (named by fact) the rubric. It is held from
  every routine selection outside its lesson (``vault.lifecycle``'s lesson hold).
* **Graded blind.** The learner's answer (never their "your thinking" note, never
  the lesson, the teacher's reasoning or their history) goes to the blind grader
  (``attempts.grading.request_vault_grading_proposal``) against the committed
  solution and rubric. The teacher never grades.
* **Recorded** as one ``reconstruction_after_walkthrough`` attempt (assisted: it
  never certifies and never answers a Check once; not primed: no double discount)
  through the shared attempt step, and one ``lesson_checks`` row with the mass it
  enters mastery at and every weight input (§8.3 ``weight_inputs``).
* **The mass** (:func:`check_mass`): §12.1's learned mass as of the check (the
  posterior mean of σ(η)), the pool-implied mass when the teacher already
  forecast this node's retention (§12.2), or the type's configured mass with
  ``teacher.weight.learned`` off.
* **Withdrawn** (:func:`withdraw_check`): help during an open check that gave the
  solution away (overlap at the auto-prime threshold) ends the check with no
  attempt: an answer after the solution was shown is not the learner's effort.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.clock import Clock, utc_now_iso
from learnloop.ids import new_ulid
from learnloop.learner import lesson_weight as LW
from learnloop.teacher.brief import SourceBook, lo_prediction
from learnloop.teacher.contracts import CheckV1

#: The mechanism a minted check item carries (``vault.lifecycle`` holds it to its lesson).
LESSON_MECHANISM = "teacher_lesson_v1"
CHECK_ATTEMPT_TYPE = "reconstruction_after_walkthrough"
ENTRY_SURFACE = "lesson"
EVIDENCE_ORIGIN = "lesson_check"


class CheckError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def check_item_id(lesson_id: str, check_ref: str) -> str:
    return f"pi_lesson_{content_key(['teacher_lesson_check', lesson_id, check_ref])[:24]}"


def render_prompt(check: CheckV1) -> str:
    """The item's prompt: the question, and its options for a choices check."""

    if check.form == "choices" and check.choices:
        options = "\n".join(f"{chr(ord('A') + index)}. {choice}" for index, choice in enumerate(check.choices))
        return f"{check.question}\n\n{options}"
    return check.question


def mint_check_item(root: Path, *, lesson_id: str, check_ref: str, check: CheckV1, learning_object_id: str,
                    book: SourceBook, clock: Clock | None = None) -> str:
    """Write the check's held item (vault YAML) and return its id."""

    from learnloop.ingest.locators import BLOCK_SPAN_V1, format_block_span
    from learnloop.vault.writer import upsert_practice_item

    item_id = check_item_id(lesson_id, check_ref)
    source_refs = []
    for alias in check.anchors:
        passage = book.passages.get(alias)
        if passage is None:
            continue
        source_refs.append({"ref_type": "canonical_source", "ref_id": str(passage["extraction_id"]),
                            "locator": format_block_span(str(passage["extraction_id"]), str(passage["span_id"])),
                            "locator_scheme": BLOCK_SPAN_V1})
    now = utc_now_iso(clock)
    payload: dict[str, Any] = {
        "id": item_id,
        "learning_object_id": learning_object_id,
        "practice_mode": "short_answer",
        "attempt_types_allowed": [CHECK_ATTEMPT_TYPE],
        "evidence_facets": [],
        "prompt": render_prompt(check),
        "expected_answer": check.committed_solution,
        "hints": [],
        "grading_rubric": {
            "max_points": sum(criterion.points for criterion in check.rubric),
            "criteria": [{"id": criterion.id, "points": criterion.points, "description": criterion.fact}
                         for criterion in check.rubric],
        },
        "provenance": {"origin": "codex_proposal", "mechanism": LESSON_MECHANISM, "lesson_id": lesson_id,
                       "node_id": check.node, "check_ref": check_ref, "anchored": bool(source_refs),
                       "source_refs": source_refs},
        "created_at": now,
        "updated_at": now,
    }
    upsert_practice_item(root, payload, clock=clock)
    return item_id


def lesson_item(item: Any) -> bool:
    extra: dict[str, Any] = getattr(getattr(item, "provenance", None), "model_extra", None) or {}
    return extra.get("mechanism") == LESSON_MECHANISM


# --- the mass ---------------------------------------------------------------------


def cold_reference(vault: Any, repository: Any, learning_object_id: str, *, lesson_id: str,
                   exclude: Sequence[str], lesson_item_ids: Sequence[str]) -> dict[str, Any]:
    """The committed cold item a node's retention forecast is about, as of now (§12.2; review F5): the
    item the delayed retention check would commit (``teacher.delayed``'s candidate rule and picker,
    excluding the lesson's own and shown items and their lineage), its IRT parameters (the LO's when no
    item fits), and the horizon the check would be dated at (``delayed.due_days``)."""

    from learnloop.learner.mastery import item_irt_params
    from learnloop.learner_protection import withheld_items
    from learnloop.teacher import delayed as D

    shown = [vault.practice_items[i] for i in exclude if i in vault.practice_items]
    lineage: set[str] = set().union(*(D.lineage(i) for i in shown)) if shown else set()
    found = D.pick(vault, repository, D.candidates(
        vault, repository, learning_object_id, exclude=exclude, withheld=withheld_items(vault, repository),
        attempted=D._attempted(repository), revealed=D._revealed(repository, lesson_id), excluded_lineage=lineage),
        seed_key=D.retention_seed_key(lesson_id, learning_object_id))
    a, b = item_irt_params(found, vault.learning_objects.get(learning_object_id), vault.config.mastery)
    days, basis = D.due_days(vault, repository, purpose="retention", lesson_item_ids=list(lesson_item_ids))
    return {"item_id": found.id if found is not None else None, "a": float(a), "b": float(b),
            "days": float(days), "dated_by": basis}


def check_mass(vault: Any, repository: Any, *, learning_object_id: str, tap: int | None, hedge: str | None,
               correctness: float, item: Any, as_of: str, p_teacher_retained: float | None,
               family: str, reference: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """The mass this check enters mastery at, with every input (``weight_inputs``). ``reference``: the
    committed cold item and horizon of the node's retention forecast (:func:`cold_reference`): the
    pool's ``p_A`` and its inversion are both computed for it, never for the check's own item."""

    from learnloop.attempts.evidence import attempt_evidence_mass
    from learnloop.learner.mastery import item_irt_params

    config = vault.config.teacher.weight
    fixed = float(attempt_evidence_mass(CHECK_ATTEMPT_TYPE, vault.config.evidence))
    state = LW.replay_state(vault, repository, as_of=as_of)
    z_c, z_source = LW.confidence_term(state, tap, hedge)
    prediction = lo_prediction(vault, repository, learning_object_id)
    band = tuple(getattr(vault.config.adaptive_difficulty, "practice_band", (0.70, 0.80)))
    z_p = LW.prediction_term(prediction.get("p"), band)
    learned = state.learned_mass(learning_object_id, z_c, z_p)
    learning_object = vault.learning_objects.get(learning_object_id)
    a, b = item_irt_params(item, learning_object, vault.config.mastery)
    state_row = repository.mastery_state(learning_object_id)
    if state_row is not None:
        mu, var, last = float(state_row.logit_mean), float(state_row.logit_variance), state_row.last_evidence_at
    else:
        from learnloop.learner.mastery import initial_mastery_state_for_learning_object

        cold = initial_mastery_state_for_learning_object(vault, repository, learning_object_id, as_of)
        mu, var, last = float(cold.logit_mean), float(cold.logit_variance), cold.last_evidence_at
    sensitivity = LW.CheckSensitivity(mu=mu, variance=var, last_evidence_at=last, item_a=float(a), item_b=float(b),
                                      correctness=float(correctness), observed_at=as_of)
    pool: dict[str, Any] | None = None
    if not config.learned:
        rule, applied = LW.RULE_FIXED, fixed
    elif config.source == "pool" and p_teacher_retained is not None:
        lam = state.pool_lambda(family)
        ref = dict(reference or {})
        ref_a, ref_b = float(ref.get("a", a)), float(ref.get("b", b))
        days = float(ref.get("days") or 0.0)
        drift = float(getattr(vault.config.mastery, "sigma2_drift", 0.0))
        mu_l, var_l = LW.posterior_after(sensitivity, learned, vault.config.mastery)
        p_a = LW.predicted_success(mu_l, var_l, a=ref_a, b=ref_b, drift=drift, days=days)
        target = lam * float(p_teacher_retained) + (1.0 - lam) * p_a
        applied = learned if lam <= 0.0 else LW.pool_implied_mass(sensitivity, target, vault.config.mastery,
                                                                  a=ref_a, b=ref_b, days=days)
        rule = LW.RULE_POOL
        pool = {"family": family, "lambda": lam, "p_b": float(p_teacher_retained), "p_a": p_a, "target": target,
                "reference": ref}
    else:
        rule, applied = LW.RULE_LEARNED, learned
    return {
        "rule": rule, "mass_learned": learned, "mass_applied": float(applied), "fixed_mass": fixed,
        "z_c": z_c, "z_c_source": z_source, "z_p": z_p, "band": list(band),
        "predicted_success": prediction.get("p"), "predicted_source": prediction.get("source"),
        "adaptive_difficulty": None, "sensitivity": sensitivity.as_dict(), "pool": pool,
        "tau_weights": [float(w) for w in state.tau_weights()], "priors_version": LW.PRIORS_VERSION,
        "tap": tap, "hedge": hedge,
    }


# --- grading ---------------------------------------------------------------------


def grade_answer(vault: Any, repository: Any, client: Any, *, item: Any, attempt_id: str, answer: str,
                 runtime: Any = None, clock: Clock | None = None) -> tuple[Any, str]:
    """The blind grader's validated grade of ``answer`` (the answer only), as a ResolvedGrade, and its run id."""

    from learnloop.ai.runs import finish_agent_run
    from learnloop.attempts.attempts import (
        AttemptValidationError,
        GradeAttribution,
        ResolvedGrade,
        agent_run_provider_fields,
    )
    from learnloop.attempts.grading import (
        GradingValidationError,
        build_grading_context,
        request_vault_grading_proposal,
        validate_codex_grading_proposal,
        vault_grading_run_identity,
    )

    context = build_grading_context(vault, item, attempt_id=attempt_id, learner_answer_md=answer)
    run_id = repository.insert_agent_run({
        "id": new_ulid(), "purpose": "grading", **agent_run_provider_fields(client, runtime),
        "prompt_template": "grading", **vault_grading_run_identity(vault, context),
        "started_at": utc_now_iso(clock), "status": "running",
    })
    try:
        proposal = request_vault_grading_proposal(vault, client, context)
        try:
            validated = validate_codex_grading_proposal(
                proposal, attempt_id=attempt_id, item=item, vault=vault, learner_answer_md=answer)
        except GradingValidationError as exc:
            raise AttemptValidationError(str(exc)) from exc
    except Exception as exc:
        finish_agent_run(repository, run_id, client, status="failed", error_message=str(exc), clock=clock)
        raise
    finish_agent_run(repository, run_id, client, clock=clock)
    now = utc_now_iso(clock)
    criterion_points = {evidence.criterion_id: evidence.points_awarded for evidence in validated.criterion_evidence}
    grade = ResolvedGrade(
        rubric_score=validated.rubric_score,
        criterion_points=criterion_points,
        evidence_rows=[{
            "id": new_ulid(), "criterion_id": evidence.criterion_id, "points_awarded": evidence.points_awarded,
            "evidence": evidence.evidence, "notes": evidence.notes, "agent_run_id": run_id, "local_grader_id": None,
            "grader_tier": 3, "learner_confidence": evidence.learner_confidence, "created_at": now,
        } for evidence in validated.criterion_evidence],
        error_attributions=[GradeAttribution(
            error_type=attribution.error_type, severity=attribution.severity, evidence=attribution.evidence,
            is_misconception=attribution.is_misconception,
            target_evidence_families=list(attribution.target_evidence_families or []),
            target_criterion_ids=list(attribution.target_criterion_ids or []),
        ) for attribution in validated.error_attributions],
        grader_confidence=validated.grader_confidence,
        confidence=None,
        manual_review_reason=validated.manual_review_reason,
        feedback_md=validated.feedback_md,
        repair_suggestions=list(validated.repair_suggestions or []),
        fatal_errors=list(validated.fatal_errors),
    )
    return grade, run_id


def record_answered_check(vault: Any, repository: Any, *, lesson_id: str, node_id: str, check_ref: str,
                          item: Any, attempt_id: str, answer: str, grade: Any, grading_run_id: str,
                          grading_source: str, tap: int | None, mass: Mapping[str, Any], created_at: str,
                          forecast_correct_key: str | None, forecast_retained_key: str | None,
                          clock: Clock | None = None) -> Any:
    """One transaction: the ``lesson_checks`` row (the mass the attempt step reads), then the attempt."""

    from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, apply_attempt
    from learnloop.attempts.grading import vault_grading_calibration_identity
    from learnloop.db.stores import lessons as store

    max_points = max(int(getattr(vault.rubric_for_item(item), "max_points", 1) or 1), 1)
    correctness = max(0.0, min(1.0, float(grade.rubric_score) / max_points))
    with repository.atomic():
        connection = repository.connection()
        store.insert_check(connection, {
            "lesson_id": lesson_id, "node_id": node_id, "check_ref": check_ref,
            "learning_object_id": item.learning_object_id, "minted_item_id": item.id, "status": "answered",
            "attempt_id": attempt_id, "correctness": correctness, "tap": tap, "hedge": mass.get("hedge"),
            "predicted_success": mass.get("predicted_success"), "predicted_source": mass.get("predicted_source"),
            "mass_learned": mass["mass_learned"], "mass_applied": mass["mass_applied"],
            "forecast_correct_key": forecast_correct_key, "forecast_retained_key": forecast_retained_key,
            "weight_inputs": dict(mass), "created_at": created_at,
        })
        result = apply_attempt(vault, repository, ApplyAttemptInput(
            draft=AttemptDraft(practice_item_id=item.id, learner_answer_md=answer, attempt_type=CHECK_ATTEMPT_TYPE,
                               hints_used=0, answer_confidence=tap, entry_surface=ENTRY_SURFACE,
                               evidence_origin=EVIDENCE_ORIGIN, awaits_completion=False),
            attempt_id=attempt_id, grade=grade, grading_source=grading_source,
            grading_agent_run_id=grading_run_id, grader_identity=vault_grading_calibration_identity(vault),
        ), clock=clock)
    return result


def withdraw_check(repository: Any, *, lesson_id: str, node_id: str, check_ref: str, item: Any,
                   overlap: float, created_at: str) -> str:
    from learnloop.db.stores import lessons as store

    with repository.atomic():
        return store.insert_check(repository.connection(), {
            "lesson_id": lesson_id, "node_id": node_id, "check_ref": check_ref,
            "learning_object_id": item.learning_object_id, "minted_item_id": item.id, "status": "withdrawn",
            "weight_inputs": {"withdrawn_overlap": overlap}, "created_at": created_at,
        })


__all__ = [
    "CHECK_ATTEMPT_TYPE",
    "CheckError",
    "LESSON_MECHANISM",
    "check_item_id",
    "check_mass",
    "grade_answer",
    "lesson_item",
    "mint_check_item",
    "record_answered_check",
    "render_prompt",
    "withdraw_check",
]
