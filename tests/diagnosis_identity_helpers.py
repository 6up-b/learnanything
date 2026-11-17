"""Fixed diagnosis identity inputs; repository doubles stop at the durable write boundary."""
from __future__ import annotations

from contextlib import nullcontext
from dataclasses import asdict
from types import SimpleNamespace


class CapturedWrite(BaseException):
    """Stop after production has built the identity, before unrelated follow-up work."""

    def __init__(self, values):
        self.values = values


def capture_write(**values):
    raise CapturedWrite(values)


def captured(call, field):
    try:
        call()
    except CapturedWrite as write:
        return write.values[field]
    raise AssertionError("production did not reach the identity's write")


def echo(**values):
    return values


def hypothesis(label="hyp_a"):
    return {"id": label, "version": 2, "statement": "Reverses the product in a transpose.",
            "statement_normalized": "reverses the product in a transpose.", "cause_scope": "learner_state",
            "target_ref": {"kind": "criterion", "criterion_id": "result"}, "episode_key": "att_pin:event:err_pin",
            "repair_class_id": "rc_pin", "operation": "reverse_product", "status": "active"}


def bundle_rows():
    from learnloop.diagnosis.causal_probe_coherence import BLIND_INPUT_CONTRACT_VERSION

    return [{"id": f"bundle_{letter}", "hypothesis_id": f"hyp_{letter}", "hypothesis_version": 2,
             "practice_item_id": "pi_pin", "predictions": {"predicted_features": {"sign": sign}},
             "model_revision": "model_pin", "outcome_schema_version": "outcome_pin",
             "generated_without_observation": True, "blind_input_contract_version": BLIND_INPUT_CONTRACT_VERSION}
            for letter, sign in (("a", "+"), ("b", "-"))]


def probe_repository():
    from learnloop.diagnosis.causal_probe_coherence import BLIND_INPUT_CONTRACT_VERSION

    bundles = bundle_rows()
    locked = {"hypotheses": [{"label": label, "causal_hypothesis_version": 2}
                              for label in ("hyp_a", "hyp_b", "other_or_unknown")]}
    return SimpleNamespace(
        causal_hypothesis=lambda label: hypothesis(label),
        causal_blind_prediction_bundles=lambda **kw: [b for b in bundles if b["hypothesis_id"] in kw["hypothesis_ids"]],
        causal_blind_prediction_bundle=lambda key: next(b for b in bundles if b["id"] == key),
        fetch_hypothesis_set=lambda key: locked,
        probe_manipulation_audit=lambda key: {"id": key, "status": "passed"},
        causal_probe_candidate=lambda key: {"id": key, "blind_input_contract_version": BLIND_INPUT_CONTRACT_VERSION},
        probe_presentation=lambda key: SimpleNamespace(practice_item_id="pi_pin", selection_components={
            "causal_probe": {"causal_probe_candidate_id": "candidate_pin", "causal_factor_id": "factor_pin",
                             "hypothesis_set_id": "set_pin", "blind_bundle_ids": ["bundle_b", "bundle_a"]}}),
        unresolved_cause_factor=lambda key: {"attempt_id": "att_pin"},
        resolve_unresolved_cause_factor=lambda *a, **kw: True,
        insert_causal_discriminating_observation=lambda **kw: {"id": kw["observation_id"]},
    )


def embedded_prediction():
    from learnloop.diagnosis.causal_orchestrator import record_learner_embedded_prediction

    return record_learner_embedded_prediction(
        probe_repository(), factor_id="factor_pin", prediction="  I expect the order to reverse.  ",
        question_event_id="question_pin", attempt_id="att_pin")["id"]


def probe_classification():
    from learnloop.diagnosis.causal_orchestrator import record_probe_classification

    return record_probe_classification(probe_repository(), presentation_id="presentation_pin",
                                       observed_features={"sign": "+"}, feature_source="deterministic").observation_id


def blind_bundle(field):
    from learnloop.diagnosis.causal_probe_coherence import generate_blind_prediction_bundle
    from tests.identity_pins_helpers import item

    repository = probe_repository()
    repository.insert_causal_blind_prediction_bundle = echo
    fixed_item = item()
    result = generate_blind_prediction_bundle(
        repository, hypothesis_id="hyp_a", item=fixed_item, rubric={"criteria": [{"id": "result", "max_points": 2}]},
        trace_contract=fixed_item.trace_contract, generator=lambda value: {"predicted_features": {"sign": "+"}},
        model_revision="model_pin", outcome_schema_version="outcome_pin")
    return result[field]


def manipulation_audit():
    from learnloop.diagnosis.causal_probe_coherence import audit_manipulation_contract

    return audit_manipulation_contract(
        SimpleNamespace(insert_probe_manipulation_audit=echo),
        source_item={"id": "pi_source", "prompt": "Transpose AB.", "surface_family": "source"},
        candidate_item={"id": "pi_probe", "prompt": "Transpose CD.", "surface_family": "probe",
                        "variant_contract": {"intended_manipulations": [{"axis": "prompt"}],
                                             "incidental_changes": ["surface_family"]}},
        source_kind="probe", adversarial_review={"contract_consistent": True, "measurement_target_independence": True},
        generation_agent_run_id="author_pin", reviewer_agent_run_id="reviewer_pin")["audit_id"]


def probe_candidate():
    from learnloop.diagnosis.causal_probe_coherence import create_probe_candidate

    repository = probe_repository()
    repository.insert_causal_probe_candidate = echo
    return create_probe_candidate(repository, factor_id="factor_pin", practice_item_id="pi_pin",
                                  hypothesis_set_id="set_pin", manipulation_audit_id="audit_pin",
                                  measurement_contract={"independently_compiled": True,
                                                        "measurement_status": "item_local"})["candidate_id"]


def cold_outcome():
    from learnloop.diagnosis.causal_probe_coherence import record_causal_cold_outcome

    return record_causal_cold_outcome(SimpleNamespace(insert_causal_cold_outcome=echo), outcome="learner_declined",
                                     followup_task_id="task_pin", remediation_episode_id="episode_pin",
                                     source_attempt_id="source_pin", servable_opportunity=False)["outcome_id"]


def cold_verification():
    from learnloop.diagnosis.causal_probe_coherence import record_delayed_cold_verification
    from tests.identity_pins_helpers import item, vault

    fixed_vault = vault()
    source = item()
    cold = source.model_copy(update={"id": "pi_cold", "surface_family": "cold_surface", "evidence_fingerprint": source.evidence_fingerprint.model_copy(update={"shared_stimulus_id": None, "source_family": None, "solution_recipe_family": None})})
    fixed_vault.practice_items[cold.id] = cold
    repository = SimpleNamespace(
        fetch_practice_attempt=lambda key: {"practice_item_id": source.id if key == "source_pin" else cold.id,
                                           "correctness": 1.0, "primed": False, "hints_used": 0,
                                           "created_at": "2026-01-01T00:00:00Z" if key == "source_pin" else "2026-01-03T00:00:00Z"},
        fetch_grading_evidence=lambda key: [],
        insert_causal_cold_verification=capture_write, active_fitted_parameters=lambda scope: None,
    )
    return captured(lambda: record_delayed_cold_verification(
        fixed_vault, repository, source_attempt_id="source_pin", cold_attempt_id="cold_pin", repair_class_id="rc_pin",
        hypothesis_ids=["hyp_b", "hyp_a"], avoided_affordances=["same_numbers", "same_order"]), "verification_id")


def repair_validation():
    from learnloop.diagnosis.causal_attribution import RepairValidationResult, VerificationResult

    return RepairValidationResult("valid", (), {"preserves_target": True},
                                  VerificationResult("verified", parsed_form="x=2")).as_dict()["id"]


def taxonomy(field):
    from learnloop.diagnosis.causal_attribution import mint_causal_mechanism_taxonomy

    repository = SimpleNamespace(
        causal_hypotheses_with_operations=lambda **kw: [hypothesis("hyp_a"), hypothesis("hyp_b")],
        causal_repair_class_definitions=lambda ids: {"rc_pin": {"repair_equivalence_id": "re_pin"}},
        insert_causal_mechanism_taxonomy_version=echo,
    )
    result = mint_causal_mechanism_taxonomy(repository)
    return result["taxonomy"]["clusters"][0]["id"] if field == "mechanism" else result[field]


def missing_vocabulary():
    from learnloop.diagnosis.missing_vocabulary import record_missing_vocabulary_notes

    rows = []
    repository = SimpleNamespace(insert_missing_vocabulary_notes=lambda notes, **kw: rows.extend(notes))
    record_missing_vocabulary_notes(repository, [{"source": "diagnostic_abstention", "abstention_reason": "unmapped",
        "learning_object_id": "lo_pin", "practice_item_id": "pi_pin", "attempt_id": "att_pin",
        "error_event_id": "err_pin", "criterion_id": "result", "grading_prompt_version": "grading_pin",
        "decision_policy_version": "policy_pin", "repair_policy_version": "repair_pin", "grader_model": "model_pin",
        "grader_provider_revision": "revision_pin"}])
    return rows[0]["id"]


def prior_draw():
    from learnloop.diagnosis.split.prior_analysis import assign

    return asdict(assign("randomized", "att_pin"))


def text_kind():
    from learnloop.diagnosis.text_gaps.judges import kind_input_hash
    from learnloop.diagnosis.text_gaps.contract import LearnerText

    return kind_input_hash(LearnerText(source_kind="tutor_question", source_id="question_pin",
                                      text="Why does the order reverse?", context_judge="tutor", created_at="2026-01-01T00:00:00Z", context={"item": "pi_pin"}))


def recurrence_reuse():
    from learnloop.diagnosis.recurrence.guard import GUARD_KIND, PlantedPair, guard_pairs
    from learnloop.matching.judge import pair_input_hash

    pair = guard_pairs([PlantedPair("case_pin", "different", "Transpose", "Transpose AB", "A^T B^T",
                                    "Keeps order.", "Believes matrices commute.")])[0]
    return pair_input_hash(GUARD_KIND, pair.left, pair.right)


def robust_context():
    from learnloop.diagnosis.robust_composition import decision_context_hash

    return decision_context_hash(episode_id="episode_pin", candidate_card_version="card_pin",
                                 resolved_slot_map={"a": "hyp_a", "b": "hyp_b"},
                                 posterior_at_selection={"hyp_a": 0.3, "hyp_b": 0.7},
                                 projection_algorithm_version="algorithm_pin")


def robust_seed():
    from learnloop.diagnosis.robust_composition import build_ensemble

    return build_ensemble(joint_alpha={"z": {"right": 3.0, "wrong": 1.0}},
                          instrument_rows={"a": {"z": 1.0}}, calibration_model_hash="calibration_pin",
                          decision_context_hash="context_pin", draw_count=1).seed


def retrieval_hash():
    from learnloop.diagnosis.split.retrieval import content_hash

    return content_hash("Transpose AB: the learner kept the order.")


def correct_sample():
    from learnloop.diagnosis.split.live import sampled_correct_answer

    return [sampled_correct_answer(f"att_pin_{i}", 0.5) for i in range(32)]


def repair_class():
    from learnloop.diagnosis.causal_attribution import select_minimal_repair

    result = select_minimal_repair([{"operator": "replace_step", "target_criterion_ids": ["result"],
        "preserve_refs": [{"kind": "criterion", "criterion_id": "setup"}], "expected_minutes": 3,
        "answer_reveal_budget": 0.25}], episode_id="episode_pin")
    return result["ranking"][0]


def repair_equivalence():
    from learnloop.diagnosis.causal_attribution import repair_equivalence_id

    return repair_equivalence_id({"operator": "replace_step", "target_refs": [
        {"kind": "criterion", "criterion_id": "result"}],
        "preserve_refs": [{"kind": "facet_capability", "facet_id": "facet_pin"}]})


def dialogue_candidate():
    from learnloop.diagnosis.causal_attribution import append_dialogue_candidate
    from tests.identity_pins_helpers import vault, item

    repository = SimpleNamespace(fetch_practice_attempt=lambda key: {
        "practice_item_id": item().id, "learning_object_id": "lo_pin"}, append_causal_hypothesis=echo)
    return append_dialogue_candidate(vault(), repository, attempt_id="att_pin", question_event_id="question_pin",
                                     candidate=hypothesis())["episode_key"]


def diagnosis_receipt():
    from learnloop.clock import FrozenClock
    from learnloop.diagnosis.causal_attribution import materialize_causal_episode
    from tests.identity_pins_helpers import vault, item
    from tests.helpers import NOW

    repository = SimpleNamespace(
        fetch_practice_attempt=lambda key: {"id": key, "practice_item_id": item().id,
                                           "learning_object_id": "lo_pin", "created_at": "2026-01-01T00:00:00Z"},
        fetch_grading_evidence=lambda key: [], record_causal_repair_class_definitions=lambda *a, **kw: None,
        error_events_for_attempt=lambda key: [], attempt_debug_payload=lambda key: None,
        fetch_attempt_feedback_metadata=lambda key: None,
        insert_missing_vocabulary_notes=lambda *a, **kw: None,
        unresolved_cause_factors_for_attempt=lambda *a, **kw: [],
        causal_hypotheses_for_attempt=lambda key: [], latest_active_causal_mechanism_taxonomy=lambda: None,
        causal_activity_classification=lambda key: None,
    )
    return materialize_causal_episode(vault(), repository, attempt_id="att_pin", clock=FrozenClock(NOW))["id"]


def prompt_version(workbench, figures, prior):
    from pytest import MonkeyPatch
    from learnloop.clock import FrozenClock
    from learnloop.diagnosis.split import jobs
    from tests.helpers import NOW
    from tests.identity_pins_helpers import vault, item
    from tests.structured_ai import StructuredClientFake

    fixed_vault = vault()
    fixed_vault.config.diagnosis.history_includes_prior_analysis = "on" if prior else "off"
    fixed_vault.config.embedding.enabled = False
    repository = SimpleNamespace(
        fetch_practice_attempt=lambda key: {"id": key, "practice_item_id": item().id},
        attempt_diagnoses_for_attempt=lambda key: [], diagnosis_calls_since=lambda when: 0,
        latest_attempt_diagnosis=lambda *a, **kw: None,
        insert_agent_run=lambda row: capture_write(prompt_version=row["prompt_version"]),
    )
    with MonkeyPatch.context() as patch:
        # These are input readers; the job still assembles the stored version itself.
        patch.setattr(jobs, "live_history_store", lambda *a: SimpleNamespace(blind_grade=lambda key: {}))
        patch.setattr(jobs, "current_attempt_for", lambda *a: SimpleNamespace(workbench_trace=workbench,
                                                                            figure_trace=figures))
        return captured(lambda: jobs.run_diagnose_job(
            fixed_vault, repository, {"id": "job_pin", "attempt_id": "att_pin", "payload": {"mode": "shadow"}},
            client_factory=StructuredClientFake, spend=SimpleNamespace(register=lambda *a: None,
                                                                       collector=SimpleNamespace()),
            clock=FrozenClock(NOW)), "prompt_version")


def text_needed():
    from pytest import MonkeyPatch
    from learnloop.diagnosis.text_gaps import judges
    from tests.structured_ai import StructuredClientFake

    class NeededFake(StructuredClientFake):
        def complete(self, request):
            return judges.NeededVerdict(verdict="yes", rationale="The operation uses this prerequisite.")

    repository = SimpleNamespace(atomic=nullcontext, connection=lambda: None)
    budget = SimpleNamespace(register_llm=lambda *a: None, request=lambda *a, **kw: nullcontext())
    with MonkeyPatch.context() as patch:
        patch.setattr(judges, "append_judgment", lambda *a, **kw: capture_write(**kw))
        return captured(lambda: judges.ask_needed(
            repository, budget, context={"item": {"prompt": "Transpose AB."},
                                         "prerequisite": {"title": "Matrix products", "statement": "Order matters."}},
            learning_object_id="lo_pin", practice_item_id="pi_pin", judge_client=NeededFake(), decider_client=None),
            "input_hash")


def machine_check():
    from learnloop.diagnosis.machine_checks import enqueue_backfill_obligation

    return enqueue_backfill_obligation(SimpleNamespace(enqueue_causal_machine_check=echo),
        {"kind": "repair_class_mapping_backfill", "factor_id": "factor_pin", "attempt_id": "att_pin",
         "hypothesis_ids": ["hyp_b", "hyp_a"]}, learning_object_id="lo_pin")["check_id"]


def embedding_hash():
    from learnloop.diagnosis.split.embeddings import misconception_record

    return misconception_record("durable:belief_pin", "Matrix multiplication commutes.").content_hash


def gap_query_hash():
    from learnloop.diagnosis.text_gaps.kinds import query_hash

    return query_hash("prerequisite", "Matrix multiplication\nThe order matters.")


def criteria_hash():
    from learnloop.diagnosis.voi_forecasting import facet_contract_criteria_hash

    return facet_contract_criteria_hash([{"id": "result", "points": 2, "targets": [{"facet": "facet_pin"}]}])


def contrast_draw():
    from learnloop.diagnosis.contrast_pairs import randomization_draw

    return randomization_draw("session_pin:pair_pin:2026-01-01")


def pack_hash():
    from learnloop.diagnosis.diagnostic_pack import pack_content_hash

    return pack_content_hash(pack_slug="pack_pin", blueprint_version_id="blueprint_pin",
                             cards=[{"card_slug": "card_pin", "coverage": ["b", "a"], "instrument_ref": "instrument_pin"}])


def family_schema():
    from learnloop.diagnosis.probe_families import ProbeFamilyTemplate

    return ProbeFamilyTemplate.from_dict({"id": "family_pin", "version": 2, "instrument_kind": "contrast",
        "observation_alphabet": ["right", "wrong"], "hypothesis_slots": ["a", "b"]}).schema_hash()


def compiled_likelihood():
    from learnloop.diagnosis.probe_families import CompiledInstrument

    return CompiledInstrument(outcome_alphabet=("right", "wrong"), rows={"a": {"right": 0.8, "wrong": 0.2},
        "b": {"right": 0.3, "wrong": 0.7}}, pseudo_count=12, grader_policy="policy_pin",
        provenance="instrument_card").compiled_likelihood_hash()


def emission_keys():
    from learnloop.diagnosis.causal_diagnostic_selector import likelihood_regime_for_candidate

    bundles = bundle_rows()
    for row in bundles:
        row["predictions"]["open_set_disposition"] = "excluded"
    regime, detail, _ = likelihood_regime_for_candidate(
        SimpleNamespace(causal_blind_prediction_bundles=lambda **kw: bundles), {"practice_item_id": "pi_pin"},
        concrete_hypothesis_ids=["hyp_a", "hyp_b"])
    assert regime == "arm_b_noiseless_partition"
    return detail["emission_keys"]


def gap_creation():
    from learnloop.diagnosis.text_gaps.actions import creation_ids
    from learnloop.diagnosis.text_gaps.contract import LearnerText

    text = LearnerText("tutor_question", "question_pin", "Why?", "tutor", "2026-01-01T00:00:00Z")
    return creation_ids(text, SimpleNamespace(learning_object_title="Matrix products", concept_title="Product order"),
                        dependent_lo="lo_pin")


def guard_suite_identity():
    from learnloop.diagnosis.recurrence.guard import guard_suite, suite_hash

    suite = guard_suite()
    return {"cases": [pair.case_id for pair in suite], "suite_hash": suite_hash(suite)}


def parametric_ids():
    from learnloop.clock import FrozenClock
    from learnloop.diagnosis.probe_families import InstrumentCard, MINIMAL_RECALL_V1
    from learnloop.diagnosis.probe_instance_generation import parametric_instance_payloads
    from tests.helpers import NOW
    from tests.identity_pins_helpers import vault

    card = InstrumentCard("card_pin", 2, MINIMAL_RECALL_V1.id, 1, "lo_pin_svd", "repair", {}, ("a", "b"), {})
    rows = parametric_instance_payloads(vault(), card, MINIMAL_RECALL_V1, count=2, seed=7, clock=FrozenClock(NOW))
    assert len(rows) == 2
    return [row["id"] for row in rows]


def needed_tier1():
    from pytest import MonkeyPatch
    from learnloop.diagnosis.text_gaps import tier1
    from tests.identity_pins_helpers import vault

    with MonkeyPatch.context() as patch:
        patch.setattr(tier1, "decide", capture_write)
        return captured(lambda: tier1.ask_needed(
            vault(), SimpleNamespace(), SimpleNamespace(spend=None),
            context={"item": {"prompt": "Transpose AB."}}, learning_object_id="lo_pin", practice_item_id="pi_pin",
            clients=SimpleNamespace()), "input_hash")


def pattern_verdict():
    from learnloop.diagnosis.split.jobs import record_pattern_verdicts

    connection = SimpleNamespace(execute=lambda sql, args: capture_write(input_hash=args[0]))
    repository = SimpleNamespace(atomic=nullcontext, connection=lambda: connection,
        diagnosis_context_receipt=lambda key: {"validated_citations": [{"claim_index": 2, "attempt_id": "att_prior"}]})
    return captured(lambda: record_pattern_verdicts(repository, diagnosis={"id": "diagnosis_pin"},
                                                    attempt_id="att_pin"), "input_hash")


def guard_link():
    from learnloop.diagnosis.recurrence.guard import DiagnoserLink, record_diagnoser_links

    connection = SimpleNamespace(execute=lambda sql, args: capture_write(input_hash=args[1]))
    repository = SimpleNamespace(atomic=nullcontext, connection=lambda: connection)
    link = DiagnoserLink("case_pin", "run_pin", "diagnosis_pin", "arm_pin", "exact", "model_pin", "prompt_pin", (), ())
    return captured(lambda: record_diagnoser_links(repository, [link]), "input_hash")


def card_verdict():
    from pytest import MonkeyPatch
    from learnloop.db.stores import judgments
    from learnloop.diagnosis.split.card import record_card_tap
    from tests.identity_pins_helpers import vault

    repository = SimpleNamespace(atomic=nullcontext, connection=lambda: None,
        attempt_diagnosis=lambda key: {"attempt_id": "att_pin", "status": "completed"},
        diagnosis_context_receipt=lambda key: {"validated_citations": [{"attempt_id": "att_prior"}]},
        fetch_practice_attempt=lambda key: {}, insert_diagnosis_feedback=lambda **kw: "feedback_pin")
    with MonkeyPatch.context() as patch:
        patch.setattr(judgments, "append_judgment", lambda *a, **kw: capture_write(**kw))
        return captured(lambda: record_card_tap(vault(), repository, attempt_id="att_pin", diagnosis_id="diagnosis_pin",
            response="not_same_mistake", cited_attempt_id="att_prior"), "input_hash")


def belief_reversal():
    from pytest import MonkeyPatch
    from learnloop.diagnosis.text_gaps import actions

    repository = SimpleNamespace(atomic=nullcontext, connection=lambda: None)
    with MonkeyPatch.context() as patch:
        patch.setattr(actions, "append_judgment", lambda *a, **kw: capture_write(**kw))
        return captured(lambda: actions.not_this_belief(repository, {"id": "gap_pin", "source_kind": "tutor_question",
            "source_id": "question_pin", "target_kind": "durable", "target_id": "belief_pin"}), "input_hash")


def prerequisite_reversal():
    from learnloop.diagnosis.text_gaps.actions import reversal_verdict

    return reversal_verdict({"id": "gap_pin", "created_learning_object_id": "lo_pin", "practice_item_id": "pi_pin"},
        "undo_creation", actor="learner", created_at="2026-01-01T00:00:00Z")["input_hash"]


def pack_card():
    from learnloop.diagnosis.diagnostic_pack import assemble_pack

    repository = SimpleNamespace(ensure_diagnostic_pack=lambda **kw: {"pack": {"id": "pack_pin"}},
                                 register_diagnostic_pack_card=capture_write)
    return captured(lambda: assemble_pack(repository, pack_slug="pack_pin", blueprint_version_id="blueprint_pin",
        cards=[{"card_slug": "a", "coverage": ["result", "setup"], "instrument_ref": "instrument_pin"},
               {"card_slug": "b", "coverage": ["setup"]}]), "content_hash")
