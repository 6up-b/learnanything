"""Authored scalar/IRT parameters and FSRS D have separate readers."""

import ast
import re
from collections import Counter
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from learnloop.algorithm_versions import LABEL_RETIRED_ALGORITHM_VERSION, PROBE_ROUTER_ALGORITHM_VERSION
from learnloop.config import EvidenceConfig, MasteryConfig, ProbeConfig
from learnloop.daily_plan.lesson_suggestion import _predicted
from learnloop.delayed_checks import predicted_item_success
from learnloop.diagnosis.probes import resolve_item_irt
from learnloop.learner import lesson_weight as LW
from learnloop.learner.mastery import resolve_item_irt_params
from learnloop.scheduling.selection_rewards import item_demand_vector
from learnloop.teacher import checks, delayed
from learnloop.teacher.brief import lo_prediction


#: The tag before the label's retirement: the literal values below are the predecessor's.
BEFORE_RETIREMENT = PROBE_ROUTER_ALGORITHM_VERSION


def _literal_inputs(scalar_difficulty, lo_scalar_difficulty, algorithm_version=BEFORE_RETIREMENT):
    mastery = MasteryConfig()
    assert mastery.irt.eb_difficulty_enabled is False
    item = NS(id="pi", learning_object_id="lo", difficulty=scalar_difficulty,
              evidence_weights={"f": 1.0}, evidence_facets=["f"], retrieval_demand=0.7,
              transfer_distance=0.0, scaffold_level=0.0, surface_family=None, repair_targets=[])
    lo = NS(id="lo", difficulty_prior=lo_scalar_difficulty)
    vault = NS(config=NS(mastery=mastery, probe=ProbeConfig(), evidence=EvidenceConfig(),
                         adaptive_difficulty=NS(practice_band=(0.7, 0.8)),
                         algorithms=NS(algorithm_version=algorithm_version)),
               practice_items={"pi": item}, learning_objects={"lo": lo},
               learning_object_for_item=lambda _: lo, rubric_for_item=lambda _: None)
    state = NS(logit_mean=0.4, logit_variance=0.3, last_evidence_at="2026-11-01T00:00:00Z")
    repository = NS(mastery_state=lambda _: state,
                    item_parameter_state=lambda _: NS(b_mean=-3.0),
                    practice_item_states=lambda: {"pi": NS(difficulty=9.0)})
    return vault, repository, item, lo


# Captured from the unchanged callers at bcccfa2174 before routing edits.
EXPECTED = [{'probe': (1.0, 1.5000000000000002),
  'suggestion': 0.8577942484315435,
  'demand': (1.0, 1.5000000000000002),
  'brief': {'source': 'mastery_ekf',
            'p': 0.8578,
            'interval': [0.6956, 0.9514],
            'words': "about 86% on a fresh question on your own (between 70% and 95%; LearnLoop's mastery "
                     'model)',
            'mu': 0.4,
            'variance': 0.3,
            'item_a': 1.0,
            'item_b': -1.5,
            'last_evidence_at': '2026-11-01T00:00:00Z'},
  'cold_reference': {'item_id': 'pi', 'a': 1.0, 'b': 1.5000000000000002, 'days': 3.0, 'dated_by': 'legacy'},
  'check': {'a': 1.0,
            'b': 1.5000000000000002,
            'learned': 0.5,
            'applied': 0.9999938558253978,
            'pool': {'family': 'family',
                     'lambda': 0.18065079365079373,
                     'p_b': 0.65,
                     'p_a': 0.2822500859661234,
                     'target': 0.34868439980135435,
                     'reference': {}}},
  'delayed': 0.26106893902450123,
  'seam': (1.0, 1.5000000000000002)},
 {'probe': (1.0, -1.5),
  'suggestion': 0.8577942484315435,
  'demand': (1.0, -1.5),
  'brief': {'source': 'mastery_ekf',
            'p': 0.8578,
            'interval': [0.6956, 0.9514],
            'words': "about 86% on a fresh question on your own (between 70% and 95%; LearnLoop's mastery "
                     'model)',
            'mu': 0.4,
            'variance': 0.3,
            'item_a': 1.0,
            'item_b': -1.5,
            'last_evidence_at': '2026-11-01T00:00:00Z'},
  'cold_reference': {'item_id': 'pi', 'a': 1.0, 'b': -1.5, 'days': 3.0, 'dated_by': 'legacy'},
  'check': {'a': 1.0,
            'b': -1.5,
            'learned': 0.5,
            'applied': 6.144174602214718e-06,
            'pool': {'family': 'family',
                     'lambda': 0.18065079365079373,
                     'p_b': 0.65,
                     'p_a': 0.8598870147006229,
                     'target': 0.8219707589179596,
                     'reference': {}}},
  'delayed': 0.8577942484315435,
  'seam': (1.0, -1.5)},
 {'probe': (1.0, 0.0),
  'suggestion': 0.5934713636269644,
  'demand': (1.0, 0.0),
  'brief': {'source': 'mastery_ekf',
            'p': 0.5935,
            'interval': [0.3377, 0.8136],
            'words': "about 59% on a fresh question on your own (between 34% and 81%; LearnLoop's mastery "
                     'model)',
            'mu': 0.4,
            'variance': 0.3,
            'item_a': 1.0,
            'item_b': 0.0,
            'last_evidence_at': '2026-11-01T00:00:00Z'},
  'cold_reference': {'item_id': 'pi', 'a': 1.0, 'b': 0.0, 'days': 3.0, 'dated_by': 'legacy'},
  'check': {'a': 1.0,
            'b': 0.0,
            'learned': 0.5,
            'applied': 0.7996425075277717,
            'pool': {'family': 'family',
                     'lambda': 0.18065079365079373,
                     'p_b': 0.65,
                     'p_a': 0.6071010703748768,
                     'target': 0.6148507960584249,
                     'reference': {}}},
  'delayed': 0.5934713636269644,
  'seam': (1.0, 0.0)}]


def _caller_values(monkeypatch, vault, repository, item, lo) -> dict:
    monkeypatch.setattr(LW, "replay_state", lambda *args, **kwargs: LW.WeightState())
    import learnloop.learner_protection as protection

    monkeypatch.setattr(protection, "withheld_items", lambda *args: None)
    monkeypatch.setattr(delayed, "candidates", lambda *args, **kwargs: [item])
    monkeypatch.setattr(delayed, "pick", lambda *args, **kwargs: item)
    monkeypatch.setattr(delayed, "_attempted", lambda *args: set())
    monkeypatch.setattr(delayed, "_revealed", lambda *args: set())
    monkeypatch.setattr(delayed, "due_days", lambda *args, **kwargs: (3.0, "legacy"))
    mass = checks.check_mass(vault, repository, learning_object_id="lo", tap=3, hedge=None,
                             correctness=1.0, item=item, as_of="2026-11-02T00:00:00Z",
                             p_teacher_retained=0.65, family="family")
    reference = checks.cold_reference(vault, repository, "lo", lesson_id="lesson", exclude=[], lesson_item_ids=[])
    demand = item_demand_vector(vault, item, lo, None)
    return {
        "probe": resolve_item_irt(vault, item)[:2],
        "suggestion": _predicted(vault, repository, "lo", "2026-11-02T00:00:00Z"),
        "demand": (demand.discrimination_a, demand.difficulty_b),
        "brief": lo_prediction(vault, repository, "lo"),
        "cold_reference": reference,
        "check": {"a": mass["sensitivity"]["item_a"], "b": mass["sensitivity"]["item_b"],
                  "learned": mass["mass_learned"], "applied": mass["mass_applied"], "pool": mass["pool"]},
        "delayed": predicted_item_success(vault, repository, item),
        "seam": resolve_item_irt_params(item, lo, vault.config.mastery, repository.item_parameter_state("pi"),
                                        algorithm_version=vault.config.algorithms.algorithm_version),
    }


@pytest.mark.parametrize("case", range(3), ids=["item_scalar", "lo_scalar", "default"])
@pytest.mark.parametrize("caller", tuple(EXPECTED[0]))
def test_switch_off_literal_caller_values(monkeypatch, case, caller):
    scalar_difficulty, lo_scalar_difficulty = [(0.8, 0.2), (None, 0.2), (None, None)][case]
    vault, repository, item, lo = _literal_inputs(scalar_difficulty, lo_scalar_difficulty)
    assert _caller_values(monkeypatch, vault, repository, item, lo)[caller] == EXPECTED[case][caller]


@pytest.mark.parametrize("case", range(3), ids=["item_scalar", "lo_scalar", "default"])
@pytest.mark.parametrize("caller", tuple(EXPECTED[0]))
def test_from_the_label_retirement_every_caller_reads_no_label(monkeypatch, case, caller):
    """At the retirement's tag the label (and the empirical-Bayes posterior the repository offers, b = -3) is read
    by no caller: every case gives the predecessor's no-label values exactly."""

    scalar_difficulty, lo_scalar_difficulty = [(0.8, 0.2), (None, 0.2), (None, None)][case]
    vault, repository, item, lo = _literal_inputs(scalar_difficulty, lo_scalar_difficulty,
                                                  algorithm_version=LABEL_RETIRED_ALGORITHM_VERSION)
    assert _caller_values(monkeypatch, vault, repository, item, lo)[caller] == EXPECTED[2][caller]


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="H1-1: the scalar display falls back to FSRS D on a different scale")
def test_scalar_display_uses_lo_prior_when_item_scalar_is_absent():
    from learnloop.tui.screens.practice import PracticeScreen

    vault, repository, item, lo = _literal_inputs(None, 0.2)
    screen = NS(practice_item=item, learning_object=lo, state=NS(vault=vault, repository=repository))
    assert PracticeScreen._difficulty(screen) == 0.2


REPOSITORY = Path(__file__).resolve().parents[1]

# Pin each expression as well as its count: replacing item.difficulty with
# state.difficulty must fail even when the number of reads stays the same.
# Each entry is audited, not a claim that a source scan can infer Python types.
AUDITED_READERS = {
    'src/learnloop/adaptive_difficulty/data_check.py': (
        'scalar: label/correctness correlation report',
        {
            'data_check: item.difficulty': 2,
        },
    ),
    'src/learnloop/adaptive_difficulty/forecasters.py': (
        'scalar/IRT: incumbent features, omitting LLM-estimated labels',
        {
            '_features: resolve_item_irt_params(None if llm_estimate else item, None, vault.config.mastery, algorithm_version=vault.config.algorithms.algorithm_version)': 1,
        },
    ),
    'src/learnloop/adaptive_difficulty/replay.py': (
        'scalar: reconstruct z_llm for historical AD events',
        {
            "_historical_signals: 'difficulty'": 1,
            "_historical_signals: getattr(item, 'difficulty', None)": 1,
            '_historical_signals: item.difficulty': 1,
        },
    ),
    'src/learnloop/adaptive_difficulty/serve_inputs.py': (
        'scalar: z_llm input receipt, no FSRS state',
        {
            "_z_llm: 'difficulty'": 1,
            "_z_llm: getattr(item, 'difficulty', None)": 1,
            '_z_llm: item.difficulty': 1,
        },
    ),
    'src/learnloop/attempts/attempts.py': (
        'separate: scalar/IRT mastery (the EB prior starts at its b); FSRS review, summary and state conversion',
        {
            '_belief_update: item_irt_params(item, learning_object, config.mastery, algorithm_version=config.algorithms.algorithm_version)': 1,
            "_fsrs_review_summary: 'difficulty'": 3,
            "_fsrs_review_summary: getattr(next_memory, 'difficulty', None)": 1,
            "_fsrs_review_summary: getattr(previous_state, 'difficulty', None)": 1,
            '_grade_evidence: resolve_item_irt_params(item, learning_object, config.mastery, prior_state.item_parameter_state, algorithm_version=config.algorithms.algorithm_version)': 1,
            '_memory_state: state.difficulty': 2,
            'grade_application: next_memory.difficulty': 1,
        },
    ),
    'src/learnloop/cli/success_head.py': (
        'metadata: difficulty-feature coverage flag, neither numerical difficulty',
        {
            "success_head_eval: 'difficulty'": 1,
            "success_head_eval: coverage['difficulty']": 1,
        },
    ),
    'src/learnloop/content/authoring/exercise_authoring.py': (
        'scalar: copy the authored contract value to item payload',
        {
            "author_exercises: 'difficulty'": 2,
            'author_exercises: entry.difficulty': 1,
        },
    ),
    'src/learnloop/content/authoring/practice_generation.py': (
        'scalar: check an authored label against its requested band',
        {
            "_check_difficulty_band: 'difficulty'": 1,
            "_check_difficulty_band: payload.get('difficulty')": 1,
        },
    ),
    'src/learnloop/content/authoring/rung_variants.py': (
        'scalar: variant direction audit and generation instructions',
        {
            "_variant_instructions: 'difficulty'": 1,
            '_variant_instructions: source_item.difficulty': 1,
            "_variant_kind: 'difficulty'": 1,
            '_variant_kind: source_item.difficulty': 1,
            "audit_variant_direction: 'difficulty'": 6,
            "audit_variant_direction: declarations.get('difficulty')": 1,
            "audit_variant_direction: payload.get('difficulty')": 1,
            'audit_variant_direction: source_item.difficulty': 1,
        },
    ),
    'src/learnloop/content/proposals/patches.py': (
        'FSRS: preserve memory state while deactivating a rejected item',
        {
            '_apply_reject_side_effect: state.difficulty': 1,
        },
    ),
    'src/learnloop/curriculum/golden_path_fixture.py': (
        'scalar: synthetic authoring payloads, no numerical reading',
        {
            "_practice_item: 'difficulty'": 1,
            "_seed_vault: 'difficulty_prior'": 1,
        },
    ),
    'src/learnloop/daily_plan/lesson_suggestion.py': (
        'scalar/IRT: LO prediction, no item posterior',
        {
            '_predicted: resolve_item_irt_params(None, learning_object, vault.config.mastery, algorithm_version=vault.config.algorithms.algorithm_version)': 1,
        },
    ),
    'src/learnloop/daily_plan/objective_inputs.py': (
        'FSRS: read practiced items for the topic memory summary',
        {
            "_practiced: 'SELECT practice_item_id, stability, difficulty, last_attempt_at FROM practice_item_state WHERE stability IS NOT NULL AND last_attempt_at IS NOT NULL'": 1,
        },
    ),
    'src/learnloop/db/stores/pf.py': (
        'scalar: column list used by generic candidate persistence and row transport',
        {
            "<module>: 'difficulty'": 1,
        },
    ),
    'src/learnloop/db/stores/practice_state.py': (
        'FSRS: decode persisted state and write memory state records',
        {
            "_practice_item_state: 'difficulty'": 1,
            "_practice_item_state: row['difficulty']": 1,
            '_record_attempt_practice_item_state: state.difficulty': 1,
            '_upsert_practice_item_state_record: state.difficulty': 1,
        },
    ),
    'src/learnloop/delayed_checks.py': (
        'scalar/IRT: item prediction with the EB item-parameter posterior',
        {
            'predicted_item_success: resolve_item_irt_params(item, learning_object, vault.config.mastery, repository.item_parameter_state(item.id), algorithm_version=vault.config.algorithms.algorithm_version)': 1,
        },
    ),
    'src/learnloop/diagnosis/causal_probe_coherence.py': (
        'scalar: compare source and candidate instrument fields',
        {
            "_item_diff: 'difficulty'": 3,
            "_item_diff: candidate.get('difficulty')": 1,
            "_item_diff: source.get('difficulty')": 1,
        },
    ),
    'src/learnloop/diagnosis/contrast_pairs.py': (
        'scalar: band audit, judge receipt and item payload',
        {
            "_payload_of: 'difficulty'": 1,
            '_payload_of: item.difficulty': 1,
            "judge_pair: 'difficulty'": 3,
            "judge_pair: first.get('difficulty')": 1,
            "judge_pair: payload.get('difficulty')": 1,
            "judge_pair: second.get('difficulty')": 1,
        },
    ),
    'src/learnloop/diagnosis/probe_remint.py': (
        'scalar: copy label to reminted item',
        {
            "_remint_payload: 'difficulty'": 1,
            '_remint_payload: source.difficulty': 1,
        },
    ),
    'src/learnloop/diagnosis/probes.py': (
        'scalar/IRT: probe response curve, no item posterior',
        {
            'resolve_item_irt: resolve_item_irt_params(item, learning_object, vault.config.mastery, algorithm_version=vault.config.algorithms.algorithm_version)': 1,
        },
    ),
    'src/learnloop/field/item_content.py': (
        'metadata: solver-panel feature coverage report',
        {
            "load_content_index: 'difficulty'": 1,
        },
    ),
    'src/learnloop/field/outcomes.py': (
        'scalar/IRT: historical features and uncertainty flag, omitting LLM-estimated labels',
        {
            '_load: item.difficulty': 1,
            '_load: resolve_item_irt_params(None if llm_estimate else item, None, vault.config.mastery, algorithm_version=vault.config.algorithms.algorithm_version)': 1,
        },
    ),
    'src/learnloop/field/probability_states.py': (
        'scalar: explain the authored or measured prior in item view',
        {
            "item_view: 'difficulty_prior'": 1,
            'item_view: item.difficulty': 2,
        },
    ),
    'src/learnloop/field/success_head.py': (
        'metadata: self.difficulty enables the solver-panel b feature; no FSRS value',
        {
            "<module>: 'difficulty'": 1,
            "__init__: 'difficulty'": 1,
            "_explicit: 'difficulty'": 1,
            '_explicit: self.difficulty': 1,
            "_prior: 'difficulty'": 1,
            'covers: self.difficulty': 1,
        },
    ),
    'src/learnloop/followup_run/admission.py': (
        'scalar: system-owned instrument axis list, no numerical reading',
        {
            "<module>: 'difficulty'": 1,
        },
    ),
    'src/learnloop/goals/exam_pool.py': (
        'scalar: stratify the held-out pool',
        {
            '_difficulty_stratum: item.difficulty': 1,
        },
    ),
    'src/learnloop/instructional/tools.py': (
        'scalar: serialize practice view',
        {
            "_practice_view: 'difficulty'": 1,
            '_practice_view: item.difficulty': 1,
        },
    ),
    'src/learnloop/learner/lesson_weight.py': (
        'scalar/IRT: current-content reconstruction; retain L4-2 until recorded inputs exist',
        {
            '_outcome_item_params: item_irt_params(item, learning_object, mastery_config, algorithm_version=vault.config.algorithms.algorithm_version)': 1,
            'recorded_trajectory: item_irt_params(item, vault.learning_objects.get(lo), mastery_config, algorithm_version=vault.config.algorithms.algorithm_version)': 1,
        },
    ),
    'src/learnloop/learner/mastery.py': (
        'scalar/IRT: static label-to-b map and EB seam; never FSRS D',
        {
            "item_irt_params: 'difficulty'": 1,
            "item_irt_params: 'difficulty_prior'": 1,
            "item_irt_params: getattr(item, 'difficulty', None)": 1,
            "item_irt_params: getattr(learning_object, 'difficulty_prior', None)": 1,
            'resolve_item_irt_params: item_irt_params(item, learning_object, config, algorithm_version=algorithm_version)': 1,
        },
    ),
    'src/learnloop/learner/recall_calibration.py': (
        'scalar: synthetic calibration item payload',
        {
            "_fresh_calibration_vault: 'difficulty'": 1,
        },
    ),
    'src/learnloop/ops/pf_generation.py': (
        'scalar: candidate row decoding, panel offsets, publication, selection and resume',
        {
            "_candidate_from_row: 'difficulty'": 1,
            "_candidate_from_row: row['difficulty']": 1,
            '_finalize_difficulty: self.parent.difficulty': 3,
            "_plan_resume: 'difficulty'": 2,
            "_plan_resume: entry.get('difficulty')": 1,
            "_resumable_job: 'difficulty'": 2,
            "_resumable_job: row['difficulty']": 1,
            "_select: 'difficulty'": 1,
            '_select: by_id[cid].difficulty': 1,
            '_write: candidate.difficulty': 2,
        },
    ),
    'src/learnloop/ops/pf_publish.py': (
        'scalar: candidate-to-item payload',
        {
            "build_item_payload: 'difficulty'": 3,
            "build_item_payload: row['difficulty']": 2,
        },
    ),
    'src/learnloop/placement/predictor.py': (
        'scalar/IRT: resolve placement item parameters, including EB state',
        {
            '_item: resolve_item_irt_params(practice_item, learning_object, self._vault.config.mastery, self._item_params.get(item), algorithm_version=self._vault.config.algorithms.algorithm_version)': 1,
        },
    ),
    'src/learnloop/practice_index/retrieval.py': (
        'scalar: min/max index filters',
        {
            '_base_matches: item.difficulty': 4,
        },
    ),
    'src/learnloop/router_objective/decision_state.py': (
        'FSRS: item memory projection in the decision receipt',
        {
            "_item_rows: 'SELECT practice_item_id, difficulty, stability, due_at, last_attempt_at FROM practice_item_state WHERE practice_item_id IN ('": 1,
            "_item_rows: 'difficulty'": 1,
            "_item_rows: row['difficulty']": 1,
        },
    ),
    'src/learnloop/router_objective/rollouts.py': (
        'FSRS: initialize rollout D from topic memory summaries',
        {
            'initial: t.difficulty': 1,
        },
    ),
    'src/learnloop/scheduling/family_memory_model.py': (
        'FSRS: preserve D across credit and freeze replay history bytes',
        {
            'observe: state.difficulty': 1,
            'snapshot_bytes: h.state.difficulty': 1,
        },
    ),
    'src/learnloop/scheduling/fsrs.py': (
        'FSRS: review update uses previous D',
        {
            'apply_review: previous.difficulty': 1,
        },
    ),
    'src/learnloop/scheduling/scheduler.py': (
        'scalar/IRT: information prediction with authored fallback',
        {
            '_practice_information: resolve_item_irt_params(item, learning_object, config.mastery, algorithm_version=config.algorithms.algorithm_version)': 1,
        },
    ),
    'src/learnloop/scheduling/selection_rewards.py': (
        'scalar/IRT: demand vector, no item posterior',
        {
            'item_demand_vector: resolve_item_irt_params(item, learning_object, vault.config.mastery, algorithm_version=vault.config.algorithms.algorithm_version)': 1,
        },
    ),
    'src/learnloop/substrate/card_lineage.py': (
        'separate: scalar contract edit axis; FSRS card projection from review memory',
        {
            "<module>: 'difficulty'": 1,
            'rebuild_card_state: memory.difficulty': 1,
        },
    ),
    'src/learnloop/substrate/family_memory.py': (
        'FSRS: persist replayed family memory projection',
        {
            'rebuild_family_memory: history.state.difficulty': 1,
        },
    ),
    'src/learnloop/substrate/shadow_rebuild.py': (
        'FSRS: named projection fields compared by the generic shadow reader',
        {
            "<module>: 'difficulty'": 2,
        },
    ),
    'src/learnloop/substrate/surface_mint.py': (
        'scalar: authored candidate and declared bounds gate',
        {
            "_within_difficulty_bounds: 'difficulty'": 1,
            "_within_difficulty_bounds: bounds.get('difficulty')": 1,
            "run_all_gates: 'difficulty'": 1,
            "run_all_gates: candidate.get('difficulty')": 1,
        },
    ),
    'src/learnloop/teacher/actions.py': (
        'scalar: copy tool-result difficulty via a literal-key comprehension',
        {
            "find: 'difficulty'": 1,
        },
    ),
    'src/learnloop/teacher/brief.py': (
        'scalar/IRT: LO success prediction and interval, no item posterior',
        {
            'lo_prediction: resolve_item_irt_params(None, learning_object, vault.config.mastery, algorithm_version=vault.config.algorithms.algorithm_version)': 1,
        },
    ),
    'src/learnloop/teacher/checks.py': (
        'scalar/IRT: retention reference and check sensitivity, no item posterior',
        {
            'check_mass: resolve_item_irt_params(item, learning_object, vault.config.mastery, algorithm_version=vault.config.algorithms.algorithm_version)': 1,
            'cold_reference: resolve_item_irt_params(found, vault.learning_objects.get(learning_object_id), vault.config.mastery, algorithm_version=vault.config.algorithms.algorithm_version)': 1,
        },
    ),
    'src/learnloop/tui/screens/practice.py': (
        'known crossing H1-1: scalar display falls back to FSRS D; strict xfail, fix due at arc H close',
        {
            '_difficulty: self.learning_object.difficulty_prior': 2,
            '_difficulty: self.practice_item.difficulty': 2,
            '_difficulty: state.difficulty': 2,
        },
    ),
    'src/learnloop/tutor/teach_back.py': (
        'scalar: copy source item label with existing default',
        {
            "_ensure_lo_wide_teach_back_item: 'difficulty'": 1,
            "ensure_teach_back_item: 'difficulty'": 1,
            'ensure_teach_back_item: source_item.difficulty': 2,
        },
    ),
    'src/learnloop/vault/hashes.py': (
        'scalar: frozen hash input; persisted key must keep its bytes',
        {
            "practice_item_hash: 'difficulty'": 1,
            'practice_item_hash: practice_item.difficulty': 1,
        },
    ),
    'src/learnloop/vault/writer.py': (
        'scalar: YAML serialization order for persisted item and LO fields',
        {
            "<module>: 'difficulty'": 1,
            "<module>: 'difficulty_prior'": 1,
        },
    ),
    'src/learnloop_sidecar/handlers/facets.py': (
        'scalar: facet map DTO',
        {
            "get_facet_mastery: 'difficulty'": 1,
            'get_facet_mastery: item.difficulty': 1,
        },
    ),
    'src/learnloop_sidecar/handlers/knowledge_map.py': (
        'scalar: knowledge map DTO',
        {
            "get_knowledge_map: 'difficulty'": 1,
            'get_knowledge_map: item.difficulty': 1,
        },
    ),
    'src/learnloop_sidecar/handlers/serializers.py': (
        'separate DTOs: item/LO scalar fields and FSRS practice-item state field',
        {
            "learning_object_detail: 'difficulty_prior'": 1,
            'learning_object_detail: learning_object.difficulty_prior': 1,
            "practice_item_detail: 'difficulty'": 1,
            'practice_item_detail: item.difficulty': 1,
            "practice_item_state_dto: 'difficulty'": 1,
            'practice_item_state_dto: state.difficulty': 1,
        },
    ),
}


def _reads(source: str) -> Counter[str]:
    tree = ast.parse(source)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    found = []
    for node in ast.walk(tree):
        read = False
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load) and node.attr in {'difficulty', 'difficulty_prior'}:
            read = True
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load) and isinstance(node.slice, ast.Constant) and node.slice.value in {'difficulty', 'difficulty_prior'}:
            read = True
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'getattr' and len(node.args) > 1:
                read = isinstance(node.args[1], ast.Constant) and node.args[1].value in {'difficulty', 'difficulty_prior'}
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'get' and node.args:
                read = isinstance(node.args[0], ast.Constant) and node.args[0].value in {'difficulty', 'difficulty_prior'}
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            read = node.value in {'difficulty', 'difficulty_prior'} or bool(re.search(r"^\s*SELECT\b[\s\S]*\b(?:difficulty|difficulty_prior)\b", node.value, re.I))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {'item_irt_params', 'resolve_item_irt_params'}:
                read = True
        if read:
            parent = parents.get(node)
            while parent is not None and not isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                parent = parents.get(parent)
            found.append((parent.name if parent else '<module>', ast.unparse(node), node.lineno))
    return Counter(f"{function}: {expression}" for function, expression, _line in found)


def _assert_audited(repository: Path) -> None:
    current = {}
    for path in sorted((repository / "src").rglob("*.py")):
        sites = _reads(path.read_text(encoding="utf-8"))
        if sites:
            current[path.relative_to(repository).as_posix()] = sites
    expected = {path: Counter(sites) for path, (reason, sites) in AUDITED_READERS.items()}
    assert all(reason.strip() for reason, _sites in AUDITED_READERS.values())
    differences = {
        path: {"new": dict(current.get(path, Counter()) - expected.get(path, Counter())),
               "removed": dict(expected.get(path, Counter()) - current.get(path, Counter()))}
        for path in sorted(current.keys() | expected.keys())
        if current.get(path) != expected.get(path)
    }
    assert not differences, f"Unaudited scalar/FSRS readers (audit kind and reason): {differences}"


def test_difficulty_readers_keep_scalar_and_fsrs_apart() -> None:
    _assert_audited(REPOSITORY)
