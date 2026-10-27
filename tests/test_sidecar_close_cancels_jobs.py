"""Closing a sidecar context cancels the jobs it started (test-thread-leak
Codex review, docs/reviews/test-thread-leak-codex-review.md).

F1: a Reader job started from a request (cue discovery here, and every job
spawned through ``ctx.background_jobs``) is cancelled by ``ctx.close()`` and
by the sidecar's EOF: the request in flight finishes, no further request is
sent, and close joins the job's thread. F2: the post-attempt worker's gaps
slot, shut down inside a learner-text gap job's first model request, sends no
second request and releases the job (attempt refunded, checkpoint kept).

Every model is a fake; each test gates the first request on an event so the
close lands while that request is in flight.
"""
from __future__ import annotations

from contextlib import closing
import io
import json
import threading
from datetime import timedelta

from learnloop.ai.execution import model_call
from learnloop.ai.spend import SpendCancelled
from learnloop_sidecar.background_jobs import BackgroundJobs
from tests.passage_cue_fakes import CueJudgeFake, build_cue_vault, snake
from tests.recap_fixtures import call, context


def _more_targets(repository, count: int) -> None:
    for index in range(count):
        repository.insert_misconception(id=f"mis_more_{index}", learning_object_id="lo_matrices", status="active",
                                        statement=f"Swapping rows of a matrix keeps its determinant, variant {index}")


class _GatedJudge(CueJudgeFake):
    """Holds its first request until ``release`` is set."""

    def __init__(self) -> None:
        super().__init__()
        self.entered = threading.Event()
        self.release = threading.Event()

    def complete(self, request):
        if not self.entered.is_set():
            self.entered.set()
            assert self.release.wait(10)
        return super().complete(request)


class _ReleasingJobs(BackgroundJobs):
    """Releases the gated request only once the close has cancelled the jobs,
    so the request's return is ordered after the close (no sleep, no race)."""

    def __init__(self, judge: _GatedJudge) -> None:
        super().__init__()
        self.judge = judge
        self.closes = 0

    def cancel(self):
        threads = super().cancel()
        self.closes += 1
        self.judge.release.set()
        return threads


# -- F1 -----------------------------------------------------------------------------------------


def test_closing_the_context_stops_a_running_discovery_before_its_next_request(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    _more_targets(repository, 3)
    ctx = context(paths.root)
    judge = _GatedJudge()
    ctx.cue_judge_client = judge
    ctx.background_jobs = _ReleasingJobs(judge)
    job = snake(call(ctx, "reader.cue_discovery", {"extraction_id": "ext_text", "source_open_id": "open_1"}))
    assert judge.entered.wait(10), "the first judge request was sent"

    ctx.close()

    stored = ctx.cue_discovery_jobs.get(job["job_id"])
    assert stored.done.is_set(), "close joined the job's thread"
    assert ctx.background_jobs.running == []
    assert not ctx.shutdown_requested  # a close, not the shutdown RPC
    assert len(judge.prompts) == 1, "no request after the context closed"
    assert stored.result["status"] == "cancelled"


def test_the_sidecars_eof_cancels_a_running_discovery(tmp_path, monkeypatch):
    from learnloop_sidecar import server

    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    _more_targets(repository, 3)
    judge = _GatedJudge()
    made = []

    class Loaded(server.SidecarContext):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.load(paths.root)
            self.cue_judge_client = judge
            self.background_jobs = _ReleasingJobs(judge)
            made.append(self)

    request = {"jsonrpc": "2.0", "id": 1, "method": "reader.cue_discovery",
               "params": {"extractionId": "ext_text", "sourceOpenId": "open_1"}}

    def stdin():
        yield json.dumps(request) + "\n"
        # EOF only once the job's first request is in flight.
        assert judge.entered.wait(10), "the first judge request was sent"

    monkeypatch.setattr(server, "SidecarContext", Loaded)
    out = io.StringIO()
    server.serve(stdin(), out)

    (ctx,) = made
    response = json.loads(out.getvalue().splitlines()[0])
    stored = ctx.cue_discovery_jobs.get(response["result"]["jobId"])
    assert ctx.background_jobs.closes >= 1  # EOF closed the context
    assert stored.done.is_set() and ctx.background_jobs.running == []
    assert len(judge.prompts) == 1, "no request after EOF"
    assert stored.result["status"] == "cancelled"


class _PhysicalClient:
    provider_name = "fake_physical"
    model = "fake/physical"


def test_a_closed_contexts_job_has_its_next_physical_request_refused():
    """The gate behind every spawned job: a job with no cancellation check of
    its own (a library ask, a reading-path judgment, an intent routing) has
    each physical request it would make after the close refused."""

    jobs = BackgroundJobs()
    entered, release = threading.Event(), threading.Event()
    sent: list[str] = []
    outcome: dict[str, BaseException] = {}

    def job() -> None:
        try:
            with model_call(_PhysicalClient(), purpose="first"):
                sent.append("first")
                entered.set()
                assert release.wait(10)
            with model_call(_PhysicalClient(), purpose="second"):
                sent.append("second")
        except BaseException as exc:  # noqa: BLE001 - recorded for the assertion
            outcome["error"] = exc

    thread = jobs.spawn(job, name="test-gated-job")
    assert entered.wait(10)
    jobs.cancel()
    release.set()
    thread.join(10)
    assert sent == ["first"]
    assert isinstance(outcome.get("error"), SpendCancelled)

    # A job started after the close belongs to the new epoch and runs.
    later: list[str] = []

    def after() -> None:
        with model_call(_PhysicalClient(), purpose="after"):
            later.append("after")

    jobs.spawn(after, name="test-later-job").join(10)
    assert later == ["after"]


def test_close_is_bounded_when_a_job_does_not_return():
    import time

    jobs = BackgroundJobs()
    hold = threading.Event()
    jobs.spawn(lambda: hold.wait(10), name="test-stuck-job")
    started = time.monotonic()
    jobs.close(timeout=0.2)
    assert time.monotonic() - started < 2.0
    hold.set()


# -- F2 -----------------------------------------------------------------------------------------


def _queued_gap_job(tmp_path):
    from learnloop.clock import FrozenClock
    from learnloop.db.repositories import Repository
    from learnloop.diagnosis.text_gaps.jobs import enqueue
    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.tutor.ai_contracts import LearnerGap
    from learnloop.tutor.tutor_qa import ask_question
    from learnloop.vault.loader import load_vault
    from tests.helpers import NOW, create_placement_vault
    from tests.text_gap_fakes import GapTutor

    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.16")
    repository = Repository(paths.sqlite_path)
    sync_vault_state(load_vault(paths.root), repository, clock=FrozenClock(NOW))
    gap = LearnerGap(prerequisite_name="Eigenvalues", prerequisite_line="Scalars a matrix scales its eigenvectors by.",
                     kind="prerequisite")
    event_id = ask_question(load_vault(paths.root), repository, GapTutor(gap), context="practice",
                            question_md="What's an eigenvalue?", practice_item_id="pi_spec_easy", session_id="s",
                            clock=FrozenClock(NOW + timedelta(minutes=1)))["event_id"]
    job_id = enqueue(repository, source_kind="tutor_question", source_id=event_id)
    assert job_id
    return paths, repository, event_id, job_id


def _job_row(paths, job_id):
    from learnloop.db.connection import connect
    from learnloop.db.stores import learner_gaps as store

    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        (job,) = [row for row in store.jobs(connection) if row["id"] == job_id]
        return job


def test_shutting_down_the_gaps_slot_inside_a_request_sends_no_further_request(tmp_path):
    from learnloop.db.connection import connect
    from learnloop.db.stores import learner_gaps as store
    from learnloop.diagnosis.text_gaps.pipeline import PipelineClients
    from learnloop.vault.loader import load_vault
    from learnloop_sidecar.post_attempt_worker import PostAttemptWorker
    from tests.text_gap_fakes import GapLLMFake, word_match

    paths, _repository, event_id, job_id = _queued_gap_job(tmp_path)
    worker = PostAttemptWorker()
    entered = threading.Event()

    class GatedLLM(GapLLMFake):
        def complete(self, request):
            if not entered.is_set():
                entered.set()
                # The first request returns only once shutdown has begun.
                assert worker._stop.wait(10)
            return super().complete(request)

    llm = GatedLLM(decide=word_match("eigenvalues"))
    worker.gap_clients = lambda _vault: PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=None,
                                                         drafter=lambda: llm, tutor=None, embedder=None)
    vault = load_vault(paths.root)
    worker.bind(lambda: (vault, paths.sqlite_path))
    worker.notify()
    assert entered.wait(20), "the gap job's first request was sent"

    worker.shutdown(timeout=10)

    assert not worker.running
    assert len(llm.calls) == 1, f"no request after shutdown, got {[purpose for purpose, _ in llm.calls]}"
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        assert store.gap_for_source(connection, "tutor_question", event_id) is None
    job = _job_row(paths, job_id)
    # Released for the next start: queued, no backoff, its attempt refunded.
    assert job["state"] == "queued" and job["not_before"] is None
    assert job["attempt_count"] == 0
    assert "cancelled" in (job["last_error"] or "")


def test_a_stopped_worker_leases_no_gap_job(tmp_path):
    from learnloop.diagnosis.text_gaps.jobs import process_next_gap_job

    paths, repository, _event_id, job_id = _queued_gap_job(tmp_path)
    assert process_next_gap_job(paths.root, repository, owner="t", cancelled=lambda: True) is None
    job = _job_row(paths, job_id)
    assert job["state"] == "queued" and job["attempt_count"] == 0
