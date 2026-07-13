"""Long-form/integrative probe families (spec_probe_eig_redesign.md §8.2, §9.5, §7.5)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.probe_coverage import family_coverage_report
from learnloop.services.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    enter_episode,
    episode_hypothesis_set,
    serve_presentation,
)
from learnloop.services.probe_families import (
    DERIVATION_V1,
    EXTENDED_CASE_V1,
    LONGFORM_OBLIGATIONS,
    PROOF_SKELETON_V1,
    PlantedTrial,
    ensure_builtin_families,
    run_family_admission_gate,
)
from learnloop.services.probe_hypotheses import build_episode_hypothesis_set
from learnloop.services.probe_instance_generation import (
    applicable_families,
    ensure_instrument_card,
    generate_instances_for_episode,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import write_yaml
from learnloop.vault.models import LoadedVault

from tests.helpers import NOW, NOW_ISO, create_basic_vault

CLOCK = FrozenClock(NOW)
PROC_LO = "lo_svd_computation"
PROC_ITEM = "pi_svd_derive_001"

DERIVATION_CRITERIA = [
    {"id": "strategy_selection", "points": 1, "description": "Selects a viable strategy."},
    {"id": "setup", "points": 1, "description": "Sets up from the givens."},
    {"id": "execution", "points": 1, "description": "Executes without invalid inferences."},
    {"id": "result", "points": 1, "description": "States the correct result."},
]


def _setup(tmp_path, *, with_item: bool = True):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    write_yaml(
        paths.learning_object_path("linear-algebra", PROC_LO),
        {
            "schema_version": 1,
            "id": PROC_LO,
            "title": "Computing the SVD",
            "subjects": ["linear-algebra"],
            "concept": "singular_value_decomposition",
            "knowledge_type": "procedure",
            "status": "active",
            "contradicts": None,
            "summary": "Compute the SVD by diagonalizing A^T A and assembling the factors.",
            "prerequisites": [],
            "confusables": [],
            "difficulty_prior": 0.6,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    if with_item:
        write_yaml(
            paths.practice_item_path("linear-algebra", PROC_ITEM),
            {
                "schema_version": 1,
                "id": PROC_ITEM,
                "learning_object_id": PROC_LO,
                "subjects": None,
                "practice_mode": "short_answer",
                "attempt_types_allowed": ["independent_attempt", "diagnostic_probe", "dont_know"],
                "evidence_facets": ["recall"],
                "evidence_weights": {"recall": 1.0},
                "prompt": "Derive the SVD of a 2x2 matrix end to end, naming your strategy first.",
                "expected_answer": "Diagonalize A^T A, take singular values, assemble U Sigma V^T.",
                "surface_family": "derivation_manual",
                "grading_rubric": {
                    "max_points": 4,
                    "criteria": DERIVATION_CRITERIA,
                    "fatal_errors": [
                        {
                            "id": "wrong_strategy_selected",
                            "description": "Uses a strategy that cannot reach the SVD.",
                            "max_grade": 1,
                        }
                    ],
                },
                "provenance": {"origin": "human", "source_refs": []},
                "created_at": NOW_ISO,
                "updated_at": NOW_ISO,
            },
        )
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return vault_root, loaded, repository


# --- Registration, applicability, admission (§9.5/§9.6) -----------------------------


def test_longform_templates_registered_as_builtins(tmp_path):
    _, _loaded, repository = _setup(tmp_path)
    ensure_builtin_families(repository, clock=CLOCK)
    for template in (PROOF_SKELETON_V1, DERIVATION_V1, EXTENDED_CASE_V1):
        record = repository.probe_family_template(template.id, template.version)
        assert record is not None
        assert record.status == "provisional"


def test_procedure_knowledge_type_gets_derivation_family(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    learning_object = loaded.learning_objects[PROC_LO]
    families = [template.id for template in applicable_families(loaded, learning_object)]
    assert DERIVATION_V1.id in families


def test_derivation_family_passes_admission_gate(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    ensure_builtin_families(repository, clock=CLOCK)
    resolved = ensure_instrument_card(loaded, repository, PROC_LO, DERIVATION_V1, clock=CLOCK)
    assert resolved is not None
    card, template = resolved
    trials = [
        PlantedTrial(planted_slot="robust_initial_grasp", matched_outcome="correct_strategy_complete"),
        PlantedTrial(planted_slot="procedure_without_selection", matched_outcome="wrong_strategy_selected"),
        PlantedTrial(planted_slot="recall_without_mechanism", matched_outcome="correct_strategy_execution_slip"),
        PlantedTrial(planted_slot="unfamiliar", matched_outcome="unanswered"),
        PlantedTrial(planted_slot="robust_initial_grasp", matched_outcome="correct_strategy_complete"),
    ]
    result = run_family_admission_gate(card, template, trials, repository=repository, clock=CLOCK)
    assert result.accepted, result.reasons
    accuracy = result.reverse_match_accuracy
    if isinstance(accuracy, dict):
        assert all(value >= 0.6 for value in accuracy.values())
    else:
        assert accuracy >= 0.6


def test_derivation_card_declares_ordered_obligations(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    resolved = ensure_instrument_card(loaded, repository, PROC_LO, DERIVATION_V1, clock=CLOCK)
    assert resolved is not None
    card, _template = resolved
    obligations = card.bindings.get("obligations")
    assert obligations == LONGFORM_OBLIGATIONS[DERIVATION_V1.id]
    # Ordered chain: each obligation depends on the previous one.
    ids = [entry["id"] for entry in obligations]
    assert ids == ["ob_strategy", "ob_setup", "ob_execution", "ob_result"]
    assert obligations[0]["kind"] == "selection"


# --- §9.5 coverage: the integrative gap clears -------------------------------------


def _coverage_entry(report, lo_id):
    return next(entry for entry in report["learning_objects"] if entry["learning_object_id"] == lo_id)


def test_integrative_gap_clears_with_derivation_card(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    ensure_builtin_families(repository, clock=CLOCK)

    before = family_coverage_report(loaded, repository)
    assert _coverage_entry(before, PROC_LO)["needs_integrative_family"] is True
    assert before["totals"]["integrative_gaps"] >= 1

    resolved = ensure_instrument_card(loaded, repository, PROC_LO, DERIVATION_V1, clock=CLOCK)
    assert resolved is not None
    after = family_coverage_report(loaded, repository)
    assert _coverage_entry(after, PROC_LO)["needs_integrative_family"] is False
    assert after["totals"]["integrative_gaps"] == before["totals"]["integrative_gaps"] - 1


# --- procedure_without_selection separation (§9.5) ----------------------------------


def test_derivation_separates_procedure_without_selection(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    hypothesis_set = build_episode_hypothesis_set(loaded, repository, PROC_LO, clock=CLOCK)
    labels = [hypothesis.label for hypothesis in hypothesis_set.hypotheses]
    assert "procedure_without_selection" in labels

    from learnloop.services.probe_families import (
        FAMILY_DEFAULT_ROWS,
        InstrumentCard,
        map_episode_labels_to_slots,
        validate_and_compile_card,
    )

    rows = FAMILY_DEFAULT_ROWS[DERIVATION_V1.id]
    card = InstrumentCard(
        id="card_derivation_sep",
        version=1,
        family_template_id=DERIVATION_V1.id,
        family_template_version=1,
        learning_object_id=PROC_LO,
        target_decision="t",
        bindings={},
        hypotheses=tuple(DERIVATION_V1.hypothesis_slots),
        conditional_observations={slot: dict(row) for slot, row in rows.items()},
    )
    instrument = validate_and_compile_card(card, DERIVATION_V1)
    slot_map = map_episode_labels_to_slots(instrument, labels)
    assert slot_map is not None
    assert slot_map["procedure_without_selection"] == "procedure_without_selection"
    robust_slot = slot_map.get("robust_initial_grasp", "robust_initial_grasp")
    assert robust_slot != slot_map["procedure_without_selection"]
    tv = 0.5 * sum(
        abs(
            instrument.rows["procedure_without_selection"][outcome]
            - instrument.rows[robust_slot][outcome]
        )
        for outcome in instrument.outcome_alphabet
    )
    assert tv >= 0.25


# --- §10 generation: pending procedure episode yields a long-form instance -----------


def test_generation_produces_derivation_instance_with_obligation_rubric(tmp_path):
    vault_root, loaded, repository = _setup(tmp_path, with_item=False)
    episode = enter_episode(loaded, repository, PROC_LO, clock=CLOCK)
    assert episode.status == "pending_items"

    summary = generate_instances_for_episode(repository, loaded, episode.id, clock=CLOCK)
    derivation_instances = [
        instance for instance in summary.generated
        if instance.family_template_id == DERIVATION_V1.id
    ]
    assert derivation_instances, "no derivation instance generated for a procedure LO"

    refreshed = load_vault(vault_root)
    item = refreshed.practice_items[derivation_instances[0].practice_item_id]
    criterion_ids = {criterion.id for criterion in item.grading_rubric.criteria}
    assert criterion_ids == {"strategy_selection", "setup", "execution", "result"}
    fatal_ids = {fatal.id for fatal in item.grading_rubric.fatal_errors}
    assert "wrong_strategy_selected" in fatal_ids


# --- §8.2 end to end: structured trace on the observation ---------------------------


def _evidence_rows(points: dict[str, float]) -> list[dict[str, object]]:
    return [
        {
            "id": new_ulid(),
            "criterion_id": criterion_id,
            "points_awarded": awarded,
            "evidence": "graded",
            "notes": None,
            "local_grader_id": "test",
            "grader_tier": 1,
            "learner_confidence": "confident",
            "created_at": NOW_ISO,
        }
        for criterion_id, awarded in points.items()
    ]


def test_longform_observation_records_trace_and_bounded_mass(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    resolved = ensure_instrument_card(loaded, repository, PROC_LO, DERIVATION_V1, clock=CLOCK)
    assert resolved is not None
    card, _template = resolved
    repository.link_probe_item_family(
        practice_item_id=PROC_ITEM,
        instrument_card_id=card.id,
        instrument_card_version=card.version,
        generator_id="manual",
        generator_version="1",
        generation_seed="0",
        instance_metadata={"review_status": "approved"},
        clock=CLOCK,
    )
    episode = enter_episode(loaded, repository, PROC_LO, clock=CLOCK)
    assert episode.status == "in_progress"
    hypothesis_set = episode_hypothesis_set(repository, episode)
    instruments = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
    eligible = next(entry for entry in instruments if entry.item.id == PROC_ITEM)
    presentation = commit_presentation(loaded, repository, episode, eligible, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)

    # Correct strategy and setup; execution diverges; the result depends on
    # execution, so grading it tells us nothing new (§8.2).
    points = {"strategy_selection": 1.0, "setup": 1.0, "execution": 0.0, "result": 1.0}
    attempt_id = new_ulid()
    apply_attempt(
        loaded,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=PROC_ITEM,
                learner_answer_md="derivation attempt",
                attempt_type="diagnostic_probe",
                probe_presentation_id=presentation.id,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=2,
                criterion_points=points,
                evidence_rows=_evidence_rows(points),
                error_attributions=[],
                grader_confidence=1.0,
                confidence=3,
                manual_review_reason=None,
            ),
            grading_source="ai",
        ),
        clock=CLOCK,
    )

    observation = repository.probe_observation_for_attempt(attempt_id)
    assert observation is not None
    trace = (observation.features or {}).get("structured_trace")
    assert trace is not None
    assert trace["first_invalid_id"] == "ob_execution"
    assert trace["correct_prefix_ids"] == ["ob_strategy", "ob_setup"]
    assert trace["unassessable_ids"] == ["ob_result"]
    # Bounded task evidence mass: 3 of 4 obligations assessable.
    assert abs(trace["assessable_mass"] - 0.75) < 1e-9
    assert observation.independent_evidence_discount <= 0.75 + 1e-9
    # The trace-driven classifier chose the execution-slip outcome.
    assert observation.grader_channel["observed_outcome"] == "correct_strategy_execution_slip"
    assert observation.grader_channel["grader_policy"] == "diagnostic_longform_v1"
