from __future__ import annotations

import json
import sqlite3
import threading
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

from learnloop.ai.runtime import AIRuntimeReport
from learnloop.clock import FrozenClock
from learnloop.codex.client import GradingContext
from learnloop.codex.runtime import CodexRuntimeReport
from learnloop.codex.schemas import CriterionEvidence, ErrorAttribution, GradingProposal
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.regrade import run_deferred_ai_regrades, run_deferred_regrades
from learnloop.services.startup import run_startup_maintenance
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, create_basic_vault


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
    before_facet = repository.facet_recall_state("lo_svd_definition", "recall")

    run_deferred_regrades(
        vault,
        repository,
        runtime=_ready_runtime(),
        codex_client=_RegradeClient(score=4, points=4),
        clock=clock,
    )

    regraded_attempt = repository.fetch_practice_attempt(attempt.attempt_id)
    after_facet = repository.facet_recall_state("lo_svd_definition", "recall")
    debug = repository.attempt_debug_payload(attempt.attempt_id)

    assert regraded_attempt["rubric_score"] == 4
    assert regraded_attempt["error_type"] is None
    assert repository.error_events_for_attempt(attempt.attempt_id) == []
    assert after_facet.recall_mean > before_facet.recall_mean
    assert debug["primary_error_type"] is None
    assert debug["max_error_severity"] == 0.0


def test_deferred_regrade_replays_targeted_error_attribution_facets(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    item = read_yaml(item_path)
    item["evidence_facets"] = ["concept", "numeric"]
    item["evidence_weights"] = {"concept": 0.5, "numeric": 0.5}
    item["criterion_facet_weights"] = {"correctness": {"concept": 1.0}}
    write_yaml(item_path, item)
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
    concept = repository.facet_recall_state("lo_svd_definition", "concept", "pi_svd_define_001")
    numeric = repository.facet_recall_state("lo_svd_definition", "numeric", "pi_svd_define_001")

    assert debug["facet_outcomes"] == {"concept": 1.0, "numeric": 0.0}
    assert event["repair_plan"]["target_evidence_families"] == ["numeric"]
    assert concept.recall_mean > numeric.recall_mean


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
        runtime=CodexRuntimeReport(status="codex_missing", checkout_path="missing", configured_revision="abc"),
        codex_client=_RegradeClient(score=4, points=4),
        clock=clock,
    )

    assert result.as_dict() == {"attempted": 0, "regraded": 0, "failed": 0, "skipped_reason": "codex_missing"}


def test_deferred_regrade_failure_leaves_self_grade_current_and_agent_failed(tmp_path):
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

    result = run_deferred_regrades(
        vault,
        repository,
        runtime=_ready_runtime(),
        codex_client=_InvalidRegradeClient(),
        clock=clock,
    )
    evidence = repository.fetch_grading_evidence(attempt.attempt_id)
    with sqlite3.connect(paths.sqlite_path) as connection:
        agent_status = connection.execute("SELECT status FROM agent_runs WHERE purpose = 'grading_regrade'").fetchone()[0]

    assert result.as_dict() == {"attempted": 1, "regraded": 0, "failed": 1, "skipped_reason": None}
    assert evidence[0].grader_tier == 1
    assert agent_status == "failed"


def test_startup_maintenance_regrades_pending_self_grade_when_codex_ready(tmp_path):
    vault_root = tmp_path / "vault"
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


class _RegradeClient:
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


class _InvalidRegradeClient:
    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=4,
            criterion_evidence=[
                CriterionEvidence(
                    criterion_id="missing",
                    points_awarded=4,
                    evidence="Invalid criterion.",
                )
            ],
            grader_confidence=0.9,
        )


def _ready_runtime() -> CodexRuntimeReport:
    return CodexRuntimeReport(
        status="ready",
        checkout_path="codex",
        configured_revision="abc",
        actual_revision="abc",
    )


def _configure_codex(vault_root, checkout, base_url: str) -> None:
    config_path = vault_root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace('provider = "sdk"', 'provider = "http"')
    text = text.replace('checkout_path = "../codex"', f'checkout_path = "{checkout.as_posix()}"')
    text = text.replace('revision = "<pinned-commit>"', 'revision = "abc123"')
    text = text.replace('base_url = "http://127.0.0.1:8765"', f'base_url = "{base_url}"')
    config_path.write_text(text, encoding="utf-8")


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
