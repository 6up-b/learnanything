from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.codex.client import GradingContext
from learnloop.codex.schemas import GradingProposal
from learnloop.db.repositories import Repository
from learnloop.services.causal_attribution import APPROVED_SUPPORT_AUTHORITIES
from learnloop.services.diagnostic_augmentation import (
    PlantedDiagnosticCase,
    REGRESSION_SHAPES,
    commission_planted_diagnostic_evaluation,
    model_family,
    planted_cases_from_manifest,
    run_diagnosis_samples,
    run_planted_diagnostic_evaluation,
)
from learnloop.services.persona_realism import match_persona_realism
from learnloop.services.scoreboard import planted_ground_truth
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault


def _proposal(
    attempt_id: str,
    *,
    cause: str = "confuses SVD with an eigendecomposition",
    anchor_kind: str = "whole_answer",
) -> GradingProposal:
    return GradingProposal.model_validate(
        {
            "diagnosis_md": f"The trace {cause}.",
            "repair_suggestions": [
                {
                    "repaired_trace": {
                        "learner_work_prefix": "",
                        "minimal_edit": "restore V transpose",
                        "repaired_answer_md": "A = U Sigma V transpose",
                        "changed_latent_claims": ["right factor omitted"],
                        "changed_checkpoint_ids": [],
                    },
                    "practice_mode": "short_answer",
                    "rationale": "Restore the omitted factor.",
                    "operator": "restore_factor",
                    "target_refs": [
                        {"kind": "criterion", "criterion_id": "correctness"}
                    ],
                    "preserve_refs": [],
                }
            ],
            "attempt_id": attempt_id,
            "practice_item_id": "pi_svd_define_001",
            "rubric_score": 0,
            "criterion_evidence": [
                {
                    "criterion_id": "correctness",
                    "points_awarded": 0,
                    "evidence": "The right factor is absent.",
                }
            ],
            "fatal_errors": [],
            "error_attributions": [
                {
                    "error_type": "conceptual_slip",
                    "severity": 0.7,
                    "evidence": cause,
                    "is_misconception": True,
                    "misconception_statement": cause,
                    "target_criterion_ids": ["correctness"],
                    "resolution_status": "resolved",
                    "cause_scope": "learner_state",
                    "target_ref": {
                        "kind": "criterion",
                        "criterion_id": "correctness",
                    },
                    "operation": "restore_factor",
                    "first_divergence": {
                        "anchor_kind": anchor_kind,
                        "criterion_id": "correctness",
                    },
                }
            ],
            "grader_confidence": 0.8,
            "manual_review_recommended": False,
        }
    )


class _SequenceDiagnostician:
    provider_name = "diagnostician"
    model = "claude-4"

    def __init__(self, proposals):
        self.proposals = list(proposals)
        self.contexts = []

    def run_grading_proposal(self, context):
        self.contexts.append(context)
        proposal = self.proposals.pop(0)
        return proposal(context) if callable(proposal) else proposal


class _Generator:
    provider_name = "generator"
    model = "gpt-5"

    def run_diagnostic_trials(self, _context):
        return SimpleNamespace(
            planted=[
                SimpleNamespace(
                    answer="SVD is just U Sigma; the right factor is unnecessary."
                )
            ]
        )


def test_blind_realism_matcher_abstains_on_small_corpus_and_rejects_separable(
    tmp_path,
):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)

    small = match_persona_realism(
        repository,
        ["one", "two"],
        real_traces=["one", "two"],
    )
    assert small.verdict == "insufficient_data"
    assert not small.licensed

    persona = [
        f"## Therefore\nWe compute x = 2 by the theorem. {'detail ' * index}"
        for index in range(4, 8)
    ]
    real = ["idk", "U sigma Vt", "maybe factorization", "I forgot"]
    separated = match_persona_realism(
        repository,
        persona,
        real_traces=real,
        separation_threshold=0.7,
    )
    assert separated.verdict == "separable"
    assert separated.balanced_accuracy == pytest.approx(1.0)


def test_stage7_cli_reports_explicitly_empty_producers(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")

    result = CliRunner().invoke(
        app,
        ["diagnostic-augmentation", "--vault", str(paths.root), "--json"],
    )

    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["persona_realism"]["runs"] == 0
    assert report["planted_evaluation"]["runs"] == 0
    assert report["phase_c"]["live_receipts"] == 0


def test_persona_realism_cli_runs_the_blind_matcher(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    personas = tmp_path / "personas.json"
    personas.write_text(
        json.dumps({"traces": ["idk", "maybe", "I forgot", "U Sigma"]}),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        [
            "persona-realism",
            "--vault",
            str(paths.root),
            "--personas",
            str(personas),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["verdict"] == "insufficient_data"
    stored = Repository(paths.sqlite_path).persona_realism_run_rows()
    assert len(stored) == 1
    assert stored[0]["persona_source"] == "authored_signature"


def test_planted_case_manifest_is_strict_and_carries_history():
    cases = planted_cases_from_manifest(
        {
            "cases": [
                {
                    "case_key": "cause_changed",
                    "regression_shape": "cause_change_mid_history",
                    "practice_item_id": "pi_svd_define_001",
                    "learner_trace_md": "A = U Sigma",
                    "should_abstain": False,
                    "history": [
                        {"attempt_id": "a1", "learner_trace_md": "old cause"},
                        {"attempt_id": "a2", "learner_trace_md": "new cause"},
                    ],
                }
            ]
        }
    )
    assert len(cases[0].history) == 2
    with pytest.raises(ValueError, match="unknown field"):
        planted_cases_from_manifest(
            [
                {
                    "case_key": "bad",
                    "regression_shape": "exhibit",
                    "practice_item_id": "pi_svd_define_001",
                    "learner_trace_md": "trace",
                    "should_abstain": False,
                    "oracle_note": "this oracle field must not disappear silently",
                }
            ]
        )


def test_identical_text_distributions_license_personas(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    traces = ["idk", "U sigma Vt", "maybe factorization", "I forgot"]

    report = match_persona_realism(
        repository,
        traces,
        real_traces=traces,
        generator_family="generator:gpt",
    )

    assert report.verdict == "indistinguishable"
    assert report.licensed
    assert report.balanced_accuracy == pytest.approx(0.5)


def test_c3_disagreement_becomes_unresolved_cause_set_and_real_support():
    context = GradingContext(
        attempt_id="attempt_1",
        practice_item_id="pi_svd_define_001",
        prompt="Define SVD.",
        expected_answer="A = U Sigma V transpose",
        learner_answer_md="A = U Sigma",
        rubric={"max_points": 4, "criteria": []},
    )
    client = _SequenceDiagnostician(
        [
            _proposal("attempt_1"),
            _proposal("attempt_1"),
            _proposal(
                "attempt_1",
                cause="makes only a transient notation omission",
                anchor_kind="between_spans",
            ),
        ]
    )

    consensus = run_diagnosis_samples(client, context, sample_count=3)

    assert consensus.agreement_support == pytest.approx(2 / 3)
    assert consensus.disagreed
    primary = consensus.proposal.error_attributions[0]
    assert primary.resolution_status == "unresolved"
    assert len(primary.candidate_causes) == 2
    assert primary.causal_confidence == pytest.approx(2 / 3)
    assert "sample_agreement" not in APPROVED_SUPPORT_AUTHORITIES


def test_same_model_family_invalidates_b1_without_running_diagnostician(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    generator = _Generator()
    diagnostician = _SequenceDiagnostician([])
    diagnostician.provider_name = generator.provider_name
    diagnostician.model = "gpt-4o"

    report = run_planted_diagnostic_evaluation(
        vault,
        repository,
        generator_client=generator,
        diagnostician_client=diagnostician,
        cases=[],
    )

    assert model_family("generator", "gpt-5") == model_family(
        "generator", "gpt-4o"
    )
    assert report.status == "invalid_same_model_family"
    assert not diagnostician.contexts


def test_model_family_cannot_be_hidden_behind_a_provider_alias():
    assert model_family("openai", "gpt-5") == model_family(
        "openrouter", "openai/gpt-4o"
    )
    assert model_family("anthropic", "claude-4") != model_family(
        "openai", "gpt-5"
    )


def test_commissioning_rejects_same_family_before_persona_generation(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    generator = _Generator()
    diagnostician = _SequenceDiagnostician([])
    diagnostician.provider_name = "another-gateway"
    diagnostician.model = "gpt-4o"

    result = commission_planted_diagnostic_evaluation(
        vault,
        repository,
        generator_client=generator,
        diagnostician_client=diagnostician,
        cases=[],
    )

    assert result["persona_realism"] is None
    assert result["evaluation"]["status"] == "invalid_same_model_family"
    assert repository.persona_realism_run_rows() == []


def test_b2_license_cannot_be_reused_for_a_different_b1_corpus(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    generator = _Generator()
    match_persona_realism(
        repository,
        ["corpus A"] * 4,
        real_traces=["corpus A"] * 4,
        persona_source="generated_regression_matrix",
        generator_family=model_family(generator.provider_name, generator.model),
    )
    diagnostician = _SequenceDiagnostician([_proposal("placeholder")])
    case = PlantedDiagnosticCase(
        case_key="different",
        regression_shape="exhibit",
        practice_item_id="pi_svd_define_001",
        learner_trace_md="corpus B",
        should_abstain=False,
    )

    report = run_planted_diagnostic_evaluation(
        vault,
        repository,
        generator_client=generator,
        diagnostician_client=diagnostician,
        cases=[case],
        sample_count=1,
        personas_pre_generated=True,
    )

    assert report.status == "unlicensed_realism"
    assert report.persona_realism_run_id is None
    assert report.metrics["counts_for_decisions"] is False


def test_licensed_b1_runs_blind_and_never_writes_a_learner_attempt(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    generator = _Generator()
    generator_family = model_family(generator.provider_name, generator.model)
    diagnostician = _SequenceDiagnostician(
        [lambda context: _proposal(context.attempt_id)]
        * len(REGRESSION_SHAPES)
    )
    cases = [
        PlantedDiagnosticCase(
            case_key=f"svd_{shape}",
            regression_shape=shape,
            practice_item_id="pi_svd_define_001",
            learner_trace_md="SVD is only U Sigma",
            should_abstain=shape == "open_vocabulary_abstention",
            planted_anchor={
                "anchor_kind": "whole_answer",
                "criterion_id": "correctness",
            },
            planted_cause_key="confuses SVD with an eigendecomposition",
            source="authored_fixture",
            history=(
                (
                    {"attempt_id": "prior_1", "learner_trace_md": "old cause"},
                    {"attempt_id": "prior_2", "learner_trace_md": "new cause"},
                )
                if shape == "cause_change_mid_history"
                else ()
            ),
            attempt_id=(
                "adjudicatable_overlap"
                if index == 0
                else None
            ),
        )
        for index, shape in enumerate(REGRESSION_SHAPES)
    ]
    traces = [case.learner_trace_md for case in cases]
    match_persona_realism(
        repository,
        traces,
        real_traces=traces,
        persona_source="generated_regression_matrix",
        generator_family=generator_family,
    )

    report = run_planted_diagnostic_evaluation(
        vault,
        repository,
        generator_client=generator,
        diagnostician_client=diagnostician,
        cases=cases,
        sample_count=1,
        personas_pre_generated=True,
    )

    assert report.licensed
    assert report.metrics["counts_for_decisions"] is True
    assert set(report.metrics["by_regression_shape"]) == set(REGRESSION_SHAPES)
    assert (
        diagnostician.contexts[0].discrimination_profiles == []
    )  # planted oracle withheld
    assert repository.list_recent_attempts_by_learning_object(
        "lo_svd_definition"
    ) == []
    labels = planted_ground_truth(repository)
    assert labels is not None
    assert labels["adjudicatable_overlap"]["anchor_key"].startswith(
        "whole_answer:correctness"
    )
