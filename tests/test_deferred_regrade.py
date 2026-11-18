from __future__ import annotations

from tests.structured_ai import StructuredClientFake
from tests.structured_ai import JointGraderAlsoBlind

import json
import sqlite3
import threading
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

from learnloop.ai.routing import AIProviderSelection, ResolvedClient
from learnloop.ai.runtime import AIRuntimeReport
from learnloop.clock import FrozenClock
from learnloop.attempts.ai_contracts import GradingContext
from learnloop.attempts.ai_contracts import CriterionEvidence, ErrorAttribution, ExercisedFacetObservation, GradingProposal
from learnloop.db.repositories import Repository
from learnloop.goals.exam_seeding import seed_exam_attempts
from learnloop.learner.facet_state_reader import facet_recall_state_for_lo, facet_uncertainty_states_for_lo
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.regrade import regrade_attempt, run_deferred_ai_regrades, run_deferred_regrades
from learnloop.ops.startup import run_startup_maintenance
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.exam_seeding_helpers import _exam_vault, _outcomes
from tests.helpers import NOW, configure_codex_http, create_basic_vault, write_facets
from tests.http_provider_double import serve_structured

import pytest

# The legacy Codex HTTP adapter is refused by the tool lockdown (hardening round 2,
# H3); these tests drive an in-process HTTP server through it as a provider double.
pytestmark = pytest.mark.usefixtures("legacy_codex_http_double")


def test_deferred_regrade_supersedes_self_grade_and_updates_mastery(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="SVD is U Sigma V^T."),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
        clock=clock,
    )
    before_mastery = repository.mastery_state("lo_svd_definition")

    result = run_deferred_regrades(
        vault,
        repository,
        runtime=_ready_runtime(),
        codex_client=_RegradeClient(score=4, points=4),
        clock=clock,
    )

    all_evidence = repository.fetch_grading_evidence(attempt.attempt_id, include_superseded=True)
    current_evidence = repository.fetch_grading_evidence(attempt.attempt_id)
    regraded_attempt = repository.fetch_practice_attempt(attempt.attempt_id)
    after_mastery = repository.mastery_state("lo_svd_definition")

    assert result.as_dict() == {"attempted": 1, "regraded": 1, "failed": 0, "skipped_reason": None}
    assert len(all_evidence) == 2
    assert all_evidence[0].grader_tier == 1
    assert all_evidence[0].superseded_at is not None
    assert all_evidence[1].grader_tier == 3
    assert current_evidence[0].grader_tier == 3
    assert regraded_attempt["rubric_score"] == 4
    assert after_mastery.evidence_count == before_mastery.evidence_count
    assert after_mastery.logit_mean > before_mastery.logit_mean


def test_deferred_regrade_replays_attempt_derived_state(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="I do not know."),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=4, error_type="conceptual_slip"),
        clock=clock,
    )
    before_facet = facet_recall_state_for_lo(vault, repository, "lo_svd_definition", "recall")

    run_deferred_regrades(
        vault,
        repository,
        runtime=_ready_runtime(),
        codex_client=_RegradeClient(score=4, points=4),
        clock=clock,
    )

    regraded_attempt = repository.fetch_practice_attempt(attempt.attempt_id)
    after_facet = facet_recall_state_for_lo(vault, repository, "lo_svd_definition", "recall")
    debug = repository.attempt_debug_payload(attempt.attempt_id)

    assert regraded_attempt["rubric_score"] == 4
    assert regraded_attempt["error_type"] is None
    assert repository.error_events_for_attempt(attempt.attempt_id) == []
    assert after_facet.recall_mean > before_facet.recall_mean
    assert debug["primary_error_type"] is None
    assert debug["max_error_severity"] == 0.0


def test_deferred_regrade_replays_targeted_error_attribution_facets(tmp_path):
    """A regrade's targeted attribution reaches the facet outcome, the error event and the diagnostic layer, never
    the canonical belief (D2a finding 4, ledger D-4: KM2's design, docs/reviews/refactor-dfb.md §0).

    The belief is folded from criterion observations only: an attribution redistributes a FAILED criterion's mass
    among that criterion's own targets (``canonical_projection.attribution_weights``) and never mints evidence on
    a facet no criterion targets (KM spec §18, resolved decision 3). Here the one criterion targets ``concept``
    and scores full marks, so ``numeric`` has no belief; its 0.0 outcome opens its per-LO uncertainty instead
    (the facet-belief successor, mvp-0.59, D-5)."""

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    item = read_yaml(item_path)
    item["evidence_facets"] = ["concept", "numeric"]
    item["evidence_weights"] = {"concept": 0.5, "numeric": 0.5}
    item["criterion_facet_weights"] = {"correctness": {"concept": 1.0}}
    write_yaml(item_path, item)
    write_facets(paths, [
        {"id": "concept", "kind": "definition", "claim": "The SVD concept."},
        {"id": "numeric", "kind": "procedure_contract", "claim": "The arithmetic."},
    ])
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="Correct concept, arithmetic slip."),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=clock,
    )

    run_deferred_regrades(
        vault,
        repository,
        runtime=_ready_runtime(),
        codex_client=_RegradeClient(
            score=4,
            points=4,
            error_attributions=[
                ErrorAttribution(
                    error_type="conceptual_slip",
                    severity=0.6,
                    evidence="Arithmetic slip in otherwise correct concept.",
                    target_evidence_families=["numeric"],
                )
            ],
        ),
        clock=clock,
    )

    debug = repository.attempt_debug_payload(attempt.attempt_id)
    event = repository.error_events_for_attempt(attempt.attempt_id)[0]
    concept = facet_recall_state_for_lo(vault, repository, "lo_svd_definition", "concept", "pi_svd_define_001")
    numeric = facet_recall_state_for_lo(vault, repository, "lo_svd_definition", "numeric", "pi_svd_define_001")

    assert debug["facet_outcomes"] == {"concept": 1.0, "numeric": 0.0}
    assert event["repair_plan"]["target_evidence_families"] == ["numeric"]
    assert concept is not None and concept.recall_mean > 0.5
    assert numeric is None
    uncertainty = {
        state.facet_id: state for state in facet_uncertainty_states_for_lo(vault, repository, "lo_svd_definition")
    }
    assert uncertainty["numeric"].status == "open"
    assert uncertainty["numeric"].opened_reason == "low_facet_outcome"


def test_regrade_projects_new_exercised_supporting_facet(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    item_id = "pi_svd_define_001"
    path = paths.practice_item_path("linear-algebra", item_id)
    item = read_yaml(path)
    item["grading_rubric"] = {"max_points": 4, "criteria": [{
        "id": "correctness", "description": "Correct decomposition.", "points": 4,
        "targets": [
            {"facet": "recall", "capability": "procedure_execution", "role": "primary"},
            {"facet": "algebra", "capability": "procedure_execution", "role": "supporting"},
        ],
    }]}
    write_yaml(path, item)
    write_facets(paths, [
        {"id": "recall", "kind": "definition", "claim": "The decomposition."},
        {"id": "algebra", "kind": "procedure_contract", "claim": "Manipulate the factors."},
    ])
    vault = load_vault(paths.root)
    repo = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repo, clock=clock)
    complete_self_graded_attempt(vault, repo, AttemptDraft(practice_item_id=item_id, learner_answer_md="U Sigma V^T"),
                                 SelfGradeInput(criterion_points={"correctness": 4}, confidence=4), clock=clock)

    class FacetGrader(_RegradeClient):
        def run_grading_proposal(self, context):
            proposal = super().run_grading_proposal(context)
            return proposal.model_copy(update={"exercised_facets": [
                ExercisedFacetObservation(facet="algebra", criterion_id="correctness", evidence="U Sigma V^T"),
            ]})

    result = run_deferred_regrades(vault, repo, runtime=_ready_runtime(),
                                   codex_client=FacetGrader(score=4, points=4), clock=clock)
    assert result.regraded == 1
    live = repo.facet_capability_evidence("algebra", "procedure_execution")
    rebuild_all_derived_state(vault, repo, clock=clock)
    rebuilt = repo.facet_capability_evidence("algebra", "procedure_execution")
    assert rebuilt.embedded_positive_mass > 0
    assert live == rebuilt


def test_deferred_regrade_preserves_blank_answer_manual_review(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=5),
        clock=clock,
    )

    run_deferred_regrades(
        vault,
        repository,
        runtime=_ready_runtime(),
        codex_client=_RegradeClient(score=4, points=4),
        clock=clock,
    )

    regraded_attempt = repository.fetch_practice_attempt(attempt.attempt_id)
    assert regraded_attempt["rubric_score"] == 4
    assert regraded_attempt["manual_review"] is True
    assert regraded_attempt["manual_review_reason"] == "blank_answer"


def test_deferred_regrade_recomputes_downstream_attempts_for_learning_object(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    first = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="wrong"),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=4, error_type="conceptual_slip"),
        clock=clock,
    )
    later = FrozenClock(NOW + timedelta(days=1))
    second = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="still wrong"),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=4, error_type="conceptual_slip"),
        clock=later,
    )
    before_second_prediction = repository.attempt_debug_payload(second.attempt_id)["predicted_correctness"]

    run_deferred_regrades(
        vault,
        repository,
        runtime=_ready_runtime(),
        codex_client=_RegradeClient(score=4, points=4),
        limit=1,
        clock=clock,
    )

    after_second_debug = repository.attempt_debug_payload(second.attempt_id)

    assert repository.fetch_practice_attempt(first.attempt_id)["rubric_score"] == 4
    assert repository.fetch_practice_attempt(second.attempt_id)["rubric_score"] == 0
    assert after_second_debug["predicted_correctness"] > before_second_prediction


def test_deferred_regrade_records_disagreement_event(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="SVD is U Sigma V^T."),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=4),
        clock=clock,
    )

    run_deferred_regrades(
        vault,
        repository,
        runtime=_ready_runtime(),
        codex_client=_RegradeClient(score=4, points=4),
        clock=clock,
    )

    with sqlite3.connect(paths.sqlite_path) as connection:
        event = connection.execute(
            """
            SELECT event_type, entity_type, entity_id, summary
            FROM content_events
            WHERE event_type = 'regrade_disagreement'
            """
        ).fetchone()

    assert event[0] == "regrade_disagreement"
    assert event[1:] == (
        "practice_item",
        "pi_svd_define_001",
        f"Deferred regrade changed rubric_score from 0 to 4; old evidence {repository.fetch_grading_evidence(attempt.attempt_id, include_superseded=True)[0].id}; new evidence {repository.fetch_grading_evidence(attempt.attempt_id)[0].id}.",
    )


def test_deferred_ai_regrade_records_provider_and_ai_origin(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="SVD is U Sigma V^T."),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=4),
        clock=clock,
    )

    result = run_deferred_ai_regrades(
        vault,
        repository,
        runtime=AIRuntimeReport(
            status="ready",
            active_provider="deepseek_flash",
            provider_type="openai_chat",
            model="deepseek-v4-flash",
        ),
        ai_client=_AIRegradeClient(score=4, points=4),
        clock=clock,
    )

    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        run = connection.execute("SELECT * FROM agent_runs WHERE purpose = 'grading_regrade'").fetchone()
        event = connection.execute("SELECT origin FROM content_events WHERE event_type = 'regrade_disagreement'").fetchone()

    assert result.regraded == 1
    assert run["provider"] == "deepseek_flash"
    assert run["provider_type"] == "openai_chat"
    assert run["model"] == "deepseek-v4-flash"
    assert event["origin"] == "ai"


def test_deferred_regrade_skips_when_runtime_not_ready(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="SVD is U Sigma V^T."),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
        clock=clock,
    )

    result = run_deferred_regrades(
        vault,
        repository,
        runtime=AIRuntimeReport(status="provider_missing_config", active_provider="codex"),
        codex_client=_RegradeClient(score=4, points=4),
        clock=clock,
    )

    assert result.as_dict() == {"attempted": 0, "regraded": 0, "failed": 0, "skipped_reason": "provider_missing_config"}


@pytest.mark.parametrize("empty", [False, True], ids=["unknown", "empty"])
def test_deferred_regrade_failure_leaves_self_grade_current_and_agent_failed(tmp_path, empty):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="SVD is U Sigma V^T."),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
        clock=clock,
    )

    before = repository.fetch_grading_evidence(attempt.attempt_id)
    due = repository.practice_item_state("pi_svd_define_001").due_at

    result = run_deferred_regrades(
        vault,
        repository,
        runtime=_ready_runtime(),
        codex_client=_InvalidRegradeClient(empty=empty),
        clock=clock,
    )
    evidence = repository.fetch_grading_evidence(attempt.attempt_id)
    with sqlite3.connect(paths.sqlite_path) as connection:
        agent_status = connection.execute("SELECT status FROM agent_runs WHERE purpose = 'grading_regrade'").fetchone()[0]

    assert result.as_dict() == {"attempted": 1, "regraded": 0, "failed": 1, "skipped_reason": None}
    assert evidence == before
    assert repository.practice_item_state("pi_svd_define_001").due_at == due
    assert evidence[0].grader_tier == 1
    assert agent_status == "failed"


def test_startup_maintenance_regrades_pending_self_grade_when_codex_ready(tmp_path, monkeypatch):
    vault_root = tmp_path / "vault"
    # The head regrades through the learner-blind grader, an isolated turn: the double serves
    # as a structured, isolated transport (tests.http_provider_double.serve_structured).
    serve_structured(monkeypatch)
    paths = create_basic_vault(vault_root)
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    server = _HttpRegradeServer()
    server.start()
    try:
        _configure_codex(vault_root, checkout, server.base_url)
        vault = load_vault(vault_root)
        repository = Repository(paths.sqlite_path)
        clock = FrozenClock(NOW)
        sync_vault_state(vault, repository, clock=clock)
        attempt = complete_self_graded_attempt(
            vault,
            repository,
            AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="SVD is U Sigma V^T."),
            SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
            clock=clock,
        )

        result = run_startup_maintenance(vault, repository, clock=clock)
    finally:
        server.stop()

    assert result.codex_runtime.ready is True
    assert result.deferred_regrades.regraded == 1
    assert repository.fetch_practice_attempt(attempt.attempt_id)["rubric_score"] == 4
    assert repository.fetch_grading_evidence(attempt.attempt_id)[0].grader_tier == 3


@pytest.mark.parametrize("legacy", [False, True], ids=["recorded", "legacy"])
def test_exam_regrade_selection_reads_import_record(tmp_path, legacy):
    _, vault, repo = _exam_vault(tmp_path)
    seeded = seed_exam_attempts(vault, repo, outcomes=_outcomes(outcomes={
        "1": {"score": 1, "answer_md": "[imported exam outcome: score 1.00]"}, "2": 0.5,
    }))
    work, score, _ = seeded.entries
    with repo.connection() as conn:
        # A future placeholder can have any wording. Older imports had NULL notes.
        conn.execute("UPDATE practice_attempts SET learner_answer_md = 'score supplied' WHERE id = ?", (score.attempt_id,))
        if legacy:
            conn.execute("UPDATE grading_evidence SET notes = NULL")
        conn.commit()
    eligible = [row["id"] for row in repo.pending_self_grade_regrade_attempts()]
    assert eligible == ([score.attempt_id] if legacy else [work.attempt_id])


def test_explicit_regrade_keeps_a_score_only_import(tmp_path):
    _, vault, repo = _exam_vault(tmp_path)
    seeded = seed_exam_attempts(vault, repo, outcomes=_outcomes(outcomes={"1": 0.75}))
    attempt_id = seeded.entries[0].attempt_id
    attempt = repo.fetch_practice_attempt(attempt_id)
    evidence = repo.fetch_grading_evidence(attempt_id, include_superseded=True)
    state = repo.practice_item_state(attempt["practice_item_id"])

    class NoCall(_RegradeClient):
        def run_grading_proposal(self, context):
            pytest.fail("The grader received a score-only import")

    with pytest.raises(ValueError, match="score-only exam import"):
        regrade_attempt(vault, repo, attempt, runtime=_ready_runtime(), client=NoCall(score=4, points=4),
                        grading_source="ai", clock=FrozenClock(NOW))
    assert repo.fetch_grading_evidence(attempt_id, include_superseded=True) == evidence
    assert repo.practice_item_state(attempt["practice_item_id"]) == state


def _explicit_regrade_refused(vault, repo, attempt_id):
    class NoCall(_RegradeClient):
        def run_grading_proposal(self, context):
            pytest.fail("The grader received a score-only import")

    attempt = repo.fetch_practice_attempt(attempt_id)
    evidence = repo.fetch_grading_evidence(attempt_id, include_superseded=True)
    with pytest.raises(ValueError, match="score-only exam import"):
        regrade_attempt(vault, repo, attempt, runtime=_ready_runtime(), client=NoCall(score=4, points=4),
                        grading_source="ai", clock=FrozenClock(NOW))
    assert repo.fetch_grading_evidence(attempt_id, include_superseded=True) == evidence


@pytest.mark.parametrize("answer", ["\t\n", "  ", "\r\x0b\x0c　"], ids=["tab_newline", "nbsp_em", "cr_vt_ff"])
def test_a_legacy_import_whose_answer_is_only_whitespace_is_score_only(tmp_path, answer):
    """The importer before the work/score record kept a truthy answer verbatim;
    new imports call it score-only when ``str.strip`` leaves nothing, and so
    does the fallback for rows written before the record."""

    _, vault, repo = _exam_vault(tmp_path)
    attempt_id = seed_exam_attempts(vault, repo, outcomes=_outcomes(outcomes={"1": 0.5})).entries[0].attempt_id
    assert not answer.strip()
    with repo.connection() as conn:
        conn.execute("UPDATE practice_attempts SET learner_answer_md = ? WHERE id = ?", (answer, attempt_id))
        conn.execute("UPDATE grading_evidence SET notes = NULL WHERE attempt_id = ?", (attempt_id,))
        conn.commit()
    assert attempt_id not in [row["id"] for row in repo.pending_self_grade_regrade_attempts()]
    assert repo.is_score_only_exam_import(attempt_id)
    _explicit_regrade_refused(vault, repo, attempt_id)


def test_the_legacy_whitespace_rule_is_pythons():
    from learnloop.db.stores.attempts import PYTHON_WHITESPACE_CODE_POINTS

    assert PYTHON_WHITESPACE_CODE_POINTS == tuple(point for point in range(0x110000) if chr(point).isspace())


def test_a_legacy_import_with_no_import_rows_is_score_only(tmp_path):
    """An import seeded before the importer refused an empty rubric wrote the
    attempt and no criterion row; a rubric supplied later must not make its
    placeholder gradable."""

    _, vault, repo = _exam_vault(tmp_path)
    attempt_id = seed_exam_attempts(vault, repo, outcomes=_outcomes(outcomes={"1": 0.5})).entries[0].attempt_id
    with repo.connection() as conn:
        # What the old producer left: the attempt alone (no criterion to write a row for).
        conn.execute("DELETE FROM grading_evidence WHERE attempt_id = ?", (attempt_id,))
        conn.commit()
    assert repo.is_score_only_exam_import(attempt_id)
    _explicit_regrade_refused(vault, repo, attempt_id)


def test_an_attempt_that_is_not_an_import_is_never_score_only_by_absence(tmp_path):
    _, vault, repo = _exam_vault(tmp_path)
    self_grade = complete_self_graded_attempt(
        vault, repo,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="SVD is U Sigma V^T."),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
        clock=FrozenClock(NOW),
    )
    assert not repo.is_score_only_exam_import(self_grade.attempt_id)


@pytest.mark.parametrize("provider_name", ["codex", "deepseek_flash"])
def test_startup_regrades_real_answers_but_leaves_score_only_exam_import(tmp_path, monkeypatch, provider_name):
    _, vault, repository = _exam_vault(tmp_path)
    clock = FrozenClock(NOW)
    seeded = seed_exam_attempts(
        vault,
        repository,
        outcomes=_outcomes(outcomes={
            "1": {"score": 1.0},
            "3": {"score": 0.25, "answer_md": "SVD factors a matrix into U, Sigma, and V transpose."},
        }),
        clock=clock,
    )
    imported = {entry.question: entry.attempt_id for entry in seeded.entries if entry.status == "seeded"}
    score_only_id = imported["1"]
    with_answer_id = imported["3"]
    self_grade = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="SVD is U Sigma V^T."),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
        clock=clock,
    )

    def imported_snapshot():
        attempt = repository.fetch_practice_attempt(score_only_id)
        return (
            attempt["rubric_score"],
            attempt["correctness"],
            repository.fetch_grading_evidence(score_only_id, include_superseded=True),
            repository.raw_attempt_feedback_metadata(score_only_id),
            repository.observation_by_attempt(score_only_id),
            repository.latest_blind_grade_record(score_only_id),
            repository.practice_item_state("pi_exam_q1").due_at,
        )

    before = imported_snapshot()
    assert before[:2] == (4, 1.0)
    assert len(before[2]) == 1 and before[2][0].local_grader_id == "exam_import"
    assert before[3]["grading_source"] == "self"
    assert before[4:6] == (None, None)
    seen = set()

    class _AnswerOnlyClient(_RegradeClient):
        def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
            assert context.attempt_id in {self_grade.attempt_id, with_answer_id}, context.learner_answer_md
            seen.add(context.attempt_id)
            return super().run_grading_proposal(context)

    runtime = _ready_runtime()
    resolved = ResolvedClient(
        selection=AIProviderSelection(provider_name=provider_name),
        provider_name=provider_name,
        runtime=runtime,
        client=_AnswerOnlyClient(score=4, points=4),
    )
    monkeypatch.setattr("learnloop.ops.startup.runtime_for_provider", lambda *_args: runtime)
    monkeypatch.setattr("learnloop.ops.startup.ready_client_for_task", lambda *_args: resolved)

    result = run_startup_maintenance(vault, repository, clock=clock)

    assert result.deferred_regrades.as_dict() == {
        "attempted": 2, "regraded": 2, "failed": 0, "skipped_reason": None,
    }
    assert seen == {self_grade.attempt_id, with_answer_id}
    for attempt_id in seen:
        assert repository.fetch_practice_attempt(attempt_id)["rubric_score"] == 4
        assert repository.fetch_grading_evidence(attempt_id)[0].grader_tier == 3
    assert imported_snapshot() == before


class _RegradeClient(JointGraderAlsoBlind, StructuredClientFake):
    def __init__(self, *, score: int, points: float, error_attributions: list[ErrorAttribution] | None = None):
        self.score = score
        self.points = points
        self.error_attributions = error_attributions or []

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=self.score,
            criterion_evidence=[
                CriterionEvidence(
                    criterion_id="correctness",
                    points_awarded=self.points,
                    evidence="Codex regrade evidence.",
                )
            ],
            error_attributions=self.error_attributions,
            grader_confidence=0.9,
        )


class _AIRegradeClient(_RegradeClient):
    provider_name = "deepseek_flash"
    provider_type = "openai_chat"
    model = "deepseek-v4-flash"


class _RepairingRegradeClient(_RegradeClient):
    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        proposal = super().run_grading_proposal(context)
        suffix = "\n\nThis completes the requested definition."
        return GradingProposal.model_validate(
            {
                **proposal.model_dump(mode="json"),
                "repair_suggestions": [
                    {
                        "practice_mode": "targeted_repair",
                        "rationale": "Append the missing conclusion.",
                        "operator": "append_conclusion",
                        "repaired_trace": {
                            "learner_work_prefix": context.learner_answer_md,
                            "minimal_edit": "Append the missing conclusion.",
                            "regenerated_work": suffix,
                            "repaired_answer_md": context.learner_answer_md + suffix,
                            "changed_latent_claims": ["The definition is complete."],
                            "changed_checkpoint_ids": [],
                        },
                    }
                ],
            }
        )


class _InvalidRegradeClient(JointGraderAlsoBlind, StructuredClientFake):
    def __init__(self, *, empty):
        self.empty = empty

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=4,
            criterion_evidence=[] if self.empty else [
                CriterionEvidence(
                    criterion_id="missing",
                    points_awarded=4,
                    evidence="Invalid criterion.",
                )
            ],
            grader_confidence=0.9,
        )


def _ready_runtime() -> AIRuntimeReport:
    return AIRuntimeReport(status="ready", active_provider="codex", provider_revision="abc")


def _configure_codex(vault_root, checkout, base_url: str) -> None:
    configure_codex_http(vault_root, checkout, base_url)


class _HttpRegradeServer:
    def __init__(self):
        self._server = HTTPServer(("127.0.0.1", 0), self._handler())
        self.base_url = f"http://127.0.0.1:{self._server.server_port}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._thread.join(timeout=5)
        self._server.server_close()

    def _handler(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                if self.path == "/health":
                    self._json({"status": "ready"})
                    return
                self.send_response(404)
                self.end_headers()

            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                if self.path == "/grading-proposal":
                    self._json(
                        {
                            "proposal": {
                                "attempt_id": body["context"]["attempt_id"],
                                "practice_item_id": body["context"]["practice_item_id"],
                                "rubric_score": 4,
                                "criterion_evidence": [
                                    {"criterion_id": "correctness", "points_awarded": 4, "evidence": "Correct."}
                                ],
                                "grader_confidence": 0.95,
                            }
                        }
                    )
                    return
                self.send_response(404)
                self.end_headers()

            def log_message(self, *_args):
                return

            def _json(self, payload: dict) -> None:
                raw = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        return Handler
