from __future__ import annotations

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from textual.widgets import Button, Input

from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.tui.app import LearnLoopApp
from learnloop.tui.screens.feedback import FeedbackScreen
from learnloop.vault.loader import load_vault

from tests.helpers import begin_session, configure_codex_http, create_basic_vault, seed_due_item


def _direct_attempt(tmp_path):
    """Run the same attempt through the service directly for parity comparison."""
    vault_root = tmp_path / "direct"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="An answer."),
        SelfGradeInput(criterion_points={"correctness": 3}, confidence=4),
    )


def test_feedback_submit_matches_cli_attempt_and_updates_state(tmp_path):
    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        paths = create_basic_vault(vault_root)
        seed_due_item(paths)

        app = LearnLoopApp(vault_root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
            await today.open_practice()
            await pilot.pause()
            practice = app.screen
            practice.set_answer("An answer.")
            feedback = await practice.open_feedback()
            await pilot.pause()

            assert isinstance(app.screen, FeedbackScreen)
            feedback.set_points("correctness", 3)
            feedback.set_confidence(4)
            result = feedback.submit()

        expected = _direct_attempt(tmp_path)

        assert result.rubric_score == expected.rubric_score
        assert result.correctness == expected.correctness
        assert result.fsrs_rating == expected.fsrs_rating
        assert result.mastery_mean == pytest.approx(expected.mastery_mean, rel=1e-6)

        # State transitions persisted: attempt + grading evidence written.
        repository = Repository(paths.sqlite_path)
        attempt = repository.fetch_practice_attempt(result.attempt_id)
        assert attempt is not None
        assert attempt["rubric_score"] == result.rubric_score
        assert repository.fetch_grading_evidence(result.attempt_id)
        assert repository.fetch_attempt_feedback_metadata(result.attempt_id) is not None

    asyncio.run(scenario())


def test_feedback_screen_reads_visible_self_grade_controls(tmp_path):
    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        create_basic_vault(vault_root)

        app = LearnLoopApp(vault_root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
            await today.open_practice()
            await pilot.pause()
            practice = app.screen
            practice.set_answer("SVD is exactly eigendecomposition.")
            feedback = await practice.open_feedback()
            await pilot.pause()

            feedback.query_one("#criterion-correctness", Input).value = "2"
            feedback.query_one("#confidence-input", Input).value = "4"
            feedback.query_one("#error-type-input", Input).value = "conceptual_slip"
            assert feedback.query_one("#fatal-conceptual_slip", Button)
            feedback.toggle_fatal("conceptual_slip")
            result = feedback.submit()

        assert result.rubric_score == 1
        assert result.error_event_ids

    asyncio.run(scenario())


def test_feedback_submit_uses_codex_grading_when_runtime_ready(tmp_path):
    async def scenario() -> None:
        vault_root = tmp_path / "vault"
        paths = create_basic_vault(vault_root)
        seed_due_item(paths)
        checkout = tmp_path / "codex"
        checkout.mkdir()
        (checkout / "HEAD").write_text("abc123", encoding="utf-8")
        server = _GradingServer()
        server.start()
        try:
            _configure_codex(vault_root, checkout, server.base_url)
            app = LearnLoopApp(vault_root)
            async with app.run_test() as pilot:
                await pilot.pause()
                today = await begin_session(app, pilot)
                await today.open_practice()
                await pilot.pause()
                practice = app.screen
                practice.set_answer("SVD is U Sigma V^T.")
                feedback = await practice.open_feedback()
                for _ in range(10):
                    await pilot.pause()
                    if feedback.result is not None:
                        break
                result = feedback.result
        finally:
            server.stop()

        assert result is not None
        assert result.grading_source == "codex"
        assert result.rubric_score == 4
        assert server.requests[0]["path"] == "/grading-proposal"

    asyncio.run(scenario())


def _configure_codex(vault_root, checkout, base_url: str) -> None:
    configure_codex_http(vault_root, checkout, base_url)


class _GradingServer:
    def __init__(self):
        self.requests: list[dict] = []
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
        owner = self

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
                owner.requests.append({"path": self.path, "body": body})
                if self.path == "/grading-proposal":
                    self._json(
                        {
                            "attempt_id": body["context"]["attempt_id"],
                            "practice_item_id": "pi_svd_define_001",
                            "rubric_score": 4,
                            "criterion_evidence": [
                                {"criterion_id": "correctness", "points_awarded": 4, "evidence": "Correct."}
                            ],
                            "grader_confidence": 0.95,
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


def test_committed_model_grade_is_not_regraded_when_a_later_step_fails(tmp_path, monkeypatch):
    from learnloop.ai.runtime import AIRuntimeReport
    from tests.test_diagnostic_augmentation import (
        _proposal,
        _SequenceDiagnostician,
        fail_after_the_joint_grade_commits,
    )

    client = _SequenceDiagnostician([lambda context: _proposal(context.attempt_id)] * 2)
    runtime = AIRuntimeReport(status="ready", active_provider="diagnostician", provider_type="openai_chat", model="claude-4")
    monkeypatch.setattr(FeedbackScreen, "_grading_provider", lambda self: ("diagnostician", runtime, client))
    fail_after_the_joint_grade_commits(monkeypatch)

    async def scenario():
        vault_root = tmp_path / "vault"
        paths = create_basic_vault(vault_root)
        seed_due_item(paths)
        app = LearnLoopApp(vault_root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
            await today.open_practice()
            await pilot.pause()
            practice = app.screen
            practice.set_answer("A = U Sigma")
            feedback = await practice.open_feedback()
            await pilot.pause()
            graded = await feedback.auto_submit_ai()
            feedback.set_points("correctness", 4)
            feedback.set_confidence(5)
            resubmitted = feedback.submit()
        return paths, graded, resubmitted

    paths, graded, resubmitted = asyncio.run(scenario())
    assert graded is not None and graded.grading_source == "ai"
    assert resubmitted.attempt_id == graded.attempt_id
    assert len(client.contexts) == 1
    assert [row["id"] for row in Repository(paths.sqlite_path).list_attempt_history()] == [graded.attempt_id]



def _commit_grade_behind_the_screen(practice, client, runtime, monkeypatch):
    """Commit a model grade for the practice screen's answer whose later step fails.

    Stands in for an earlier grading call whose screen state was lost.
    """

    from learnloop.attempts.attempts import complete_attempt_with_ai_required
    from tests.test_diagnostic_augmentation import fail_after_the_joint_grade_commits

    with monkeypatch.context() as patch:
        fail_after_the_joint_grade_commits(patch)
        with pytest.raises(ValueError, match="after the grade committed"):
            complete_attempt_with_ai_required(
                practice.state.vault, practice.state.repository, practice._draft(),
                runtime=runtime, ai_client=client,
            )


def _grading_fake(monkeypatch):
    from learnloop.ai.runtime import AIRuntimeReport
    from tests.test_diagnostic_augmentation import _proposal, _SequenceDiagnostician

    client = _SequenceDiagnostician([lambda context: _proposal(context.attempt_id)] * 3)
    runtime = AIRuntimeReport(status="ready", active_provider="diagnostician", provider_type="openai_chat", model="claude-4")
    monkeypatch.setattr(FeedbackScreen, "_grading_provider", lambda self: ("diagnostician", runtime, client))
    return client, runtime


@pytest.mark.parametrize("retry", ["auto_grade", "dont_know"])
def test_tui_retry_resumes_a_committed_grade_instead_of_recording_another(tmp_path, monkeypatch, retry):
    client, runtime = _grading_fake(monkeypatch)
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)

    async def scenario():
        app = LearnLoopApp(vault_root)
        async with app.run_test() as pilot:
            await pilot.pause()
            today = await begin_session(app, pilot)
            await today.open_practice()
            await pilot.pause()
            practice = app.screen
            practice.set_answer("A = U Sigma")
            _commit_grade_behind_the_screen(practice, client, runtime, monkeypatch)
            if retry == "dont_know":
                return practice.dont_know()
            # A fresh feedback screen rebuilds the draft from the practice screen.
            feedback = await practice.open_feedback()
            await pilot.pause()
            return await feedback.auto_submit_ai()

    resumed = asyncio.run(scenario())
    assert resumed is not None and resumed.grading_source == "ai"
    assert len(client.contexts) == 1
    assert [row["id"] for row in Repository(paths.sqlite_path).list_attempt_history()] == [resumed.attempt_id]
