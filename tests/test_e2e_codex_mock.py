from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.codex.client import AuthoringContext, GradingContext
from learnloop.codex.runtime import CodexRuntimeReport
from learnloop.codex.schemas import AuthoringProposal, CriterionEvidence, GradingProposal
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_attempt_with_codex_fallback
from learnloop.services.proposals import accept_items, generate_authoring_proposal
from learnloop.services.scheduler import build_due_queue
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import add_note, load_vault

from tests.helpers import NOW, create_basic_vault


class _FakeAuthoringClient:
    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        return AuthoringProposal.model_validate(_authoring_payload())

    def run_grading_proposal(self, context):  # pragma: no cover
        raise NotImplementedError


class _FakeGradingClient:
    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=4,
            criterion_evidence=[
                CriterionEvidence(criterion_id="correctness", points_awarded=4, evidence="Correct.")
            ],
            grader_confidence=0.95,
        )


def _ready_runtime() -> CodexRuntimeReport:
    return CodexRuntimeReport(
        status="ready", checkout_path="codex", configured_revision="abc", actual_revision="abc"
    )


def test_codex_mocked_end_to_end(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    add_note(vault_root, "linear-algebra", "note_svd", "SVD", "SVD compresses matrices.", clock=FrozenClock(NOW))
    clock = FrozenClock(NOW)

    # Authoring proposal via fake Codex client -> persisted with agent-run lineage.
    patch_id = generate_authoring_proposal(vault_root, _FakeAuthoringClient(), clock=clock)
    repository = Repository(paths.sqlite_path)
    batch = next(b for b in repository.proposal_batches() if b["id"] == patch_id)
    assert batch["agent_run_id"]
    assert repository.find_record(batch["agent_run_id"])[1]["status"] == "completed"

    # Accept -> YAML written through LearnLoop storage, with change batches + content events.
    apply_result = accept_items(vault_root, patch_id)
    assert apply_result.applied_count == 2
    for change_batch_id in apply_result.change_batch_ids:
        assert repository.find_record(change_batch_id)[0] == "change_batch"
    with repository.connection() as connection:
        content_event_count = connection.execute("SELECT COUNT(*) AS c FROM content_events").fetchone()["c"]
    assert content_event_count >= 2

    reloaded = load_vault(vault_root)
    assert "lo_svd_imported" in reloaded.learning_objects
    assert "pi_svd_imported_001" in reloaded.practice_items
    assert reloaded.issues == []  # reloaded YAML still validates and references resolve

    sync_vault_state(reloaded, repository, clock=clock)

    # Grade the generated item with a fake Codex grader (ready runtime).
    result = complete_attempt_with_codex_fallback(
        reloaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_imported_001", learner_answer_md="Low-rank approximation."),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=3),
        runtime=_ready_runtime(),
        codex_client=_FakeGradingClient(),
        clock=clock,
    )

    assert result.grading_source == "codex"
    assert result.rubric_score == 4
    evidence = repository.fetch_grading_evidence(result.attempt_id)
    assert evidence and evidence[0].grader_tier == 3
    assert evidence[0].agent_run_id == result.agent_run_id
    assert repository.find_record(result.agent_run_id)[1]["status"] == "completed"
    assert repository.practice_item_state("pi_svd_imported_001").due_at is not None
    assert repository.mastery_state("lo_svd_imported").evidence_count == 1
    assert repository.latest_attempt_surprise(result.attempt_id) is not None

    # The graded item participates in scheduling.
    queue = build_due_queue(load_vault(vault_root), repository, clock=clock, persist_explanations=False)
    assert "pi_svd_imported_001" in [item.practice_item_id for item in queue]


def _authoring_payload() -> dict:
    return {
        "summary": "SVD application content",
        "source_refs": [{"ref_type": "note", "ref_id": "note_svd"}],
        "items": [
            {
                "client_item_id": "lo_1",
                "item_type": "learning_object",
                "operation": "create",
                "proposed_entity_id": "lo_svd_imported",
                "source_ref_ids": ["note_svd"],
                "rationale": "Add an application LO.",
                "review_route": "review_required",
                "payload": {
                    "title": "Imported SVD use",
                    "subjects": ["linear-algebra"],
                    "concept_id": "singular_value_decomposition",
                    "knowledge_type": "application",
                    "summary": "SVD compresses matrices via low-rank approximation.",
                },
            },
            {
                "client_item_id": "pi_1",
                "item_type": "practice_item",
                "operation": "create",
                "proposed_entity_id": "pi_svd_imported_001",
                "source_ref_ids": ["note_svd"],
                "rationale": "Practice the new application LO.",
                "review_route": "review_required",
                "payload": {
                    "learning_object_id": "lo_svd_imported",
                    "subjects": None,
                    "practice_mode": "short_answer",
                    "attempt_types_allowed": ["independent_attempt"],
                    "prompt": "What is one use of SVD?",
                    "expected_answer": "Low-rank approximation.",
                    "evidence_facets": ["application"],
                    "evidence_weights": {"application": 1.0},
                    "grading_rubric": {
                        "max_points": 4,
                        "criteria": [{"id": "correctness", "points": 4, "description": "Names a real use."}],
                        "fatal_errors": [],
                    },
                },
            },
        ],
    }
