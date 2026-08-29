from __future__ import annotations

from tests.structured_ai import StructuredClientFake

from learnloop.content.proposals.ai_contracts import AuthoringProposal
from learnloop.tutor.ai_contracts import PromotionAnalysis
from learnloop.db.repositories import Repository
from learnloop.content.pipeline.runner import IngestRunner, JobSpec, RunnerServices
from learnloop.vault.loader import add_note

from tests.helpers import create_basic_vault
from tests.test_tutor_promotion_service import _attach_proposal


class _AnalysisClient(StructuredClientFake):
    provider_name = "analysis"
    provider_type = "test"
    model = "analysis-model"

    def __init__(self) -> None:
        self.calls = 0

    def run_promotion_analysis(self, _context):
        self.calls += 1
        return PromotionAnalysis(attributed_facets=["recall"])


class _AuthoringClient(StructuredClientFake):
    provider_name = "authoring"
    provider_type = "test"
    model = "authoring-model"

    def __init__(self, proposal: AuthoringProposal) -> None:
        self.proposal = proposal
        self.calls = 0

    def run_authoring_proposal(self, _context):
        self.calls += 1
        return self.proposal


def _setup(tmp_path, proposal: AuthoringProposal):
    paths = create_basic_vault(tmp_path / "vault")
    add_note(
        paths.root,
        "linear-algebra",
        "note_svd_source",
        "SVD source",
        "The columns of U are orthonormal.",
        related_los=["lo_svd_definition"],
    )
    repository = Repository(paths.sqlite_path)
    repository.insert_question_event(
        {
            "id": "ev_job",
            "context": "practice",
            "practice_item_id": "pi_svd_define_001",
            "question_md": "Why must U have orthonormal columns?",
            "answer_md": "Which product certifies orthonormality?",
            "answer_status": "answered",
        }
    )
    repository.insert_question_promotion_request(
        question_event_id="ev_job", intent="practice"
    )
    analysis = _AnalysisClient()
    authoring = _AuthoringClient(proposal)
    runner = IngestRunner(
        repository,
        vault_root=paths.root,
        worker_id="promotion-test",
        services=RunnerServices(
            promotion_analysis_client_factory=lambda _ctx: analysis,
            promotion_authoring_client_factory=lambda _ctx: authoring,
        ),
    )
    batch_id = runner.enqueue_batch(
        "question_promotion",
        [JobSpec("question_promotion", {"event_id": "ev_job"})],
    )
    repository.update_question_promotion_request("ev_job", batch_id=batch_id)
    return repository, runner, batch_id, analysis, authoring


def test_durable_promotion_uses_separate_analysis_and_authoring_routes(tmp_path):
    repository, runner, batch_id, analysis, authoring = _setup(
        tmp_path, _attach_proposal()
    )

    assert runner.drain() == 1

    request = repository.question_promotion_request("ev_job")
    promotion = repository.question_promotion("ev_job")
    job = repository.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "completed"
    assert request["status"] == "completed"
    assert request["stage"] == "ready"
    assert promotion["route"] == "auto_apply"
    assert analysis.calls == 1
    assert authoring.calls == 1
    assert repository.queue_revision()["revision"] >= 1


def test_durable_promotion_persists_no_item_failure_for_retry(tmp_path):
    empty = AuthoringProposal.model_validate(
        {"summary": "No item proposed.", "source_refs": [], "items": []}
    )
    repository, runner, batch_id, _analysis, _authoring = _setup(tmp_path, empty)

    assert runner.drain() == 1

    request = repository.question_promotion_request("ev_job")
    job = repository.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "failed"
    assert request["status"] == "failed"
    assert request["error_code"] == "no_practice_item"
    assert request["retryable"] is True
    assert repository.question_promotion("ev_job") is None


def test_queue_revision_advances_after_promotion_job_is_completed(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    runner = IngestRunner(
        repository,
        vault_root=paths.root,
        worker_id="revision-test",
        handlers={"question_promotion": lambda _ctx: {"ok": True}},
    )
    before = repository.queue_revision()["revision"]
    batch_id = runner.enqueue_batch(
        "question_promotion",
        [JobSpec("question_promotion", {"event_id": "unused-by-test-handler"})],
    )

    assert runner.drain() == 1
    assert repository.ingest_jobs_for_batch(batch_id)[0]["status"] == "completed"
    assert repository.queue_revision()["revision"] == before + 1
