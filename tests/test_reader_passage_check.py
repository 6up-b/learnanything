"""RW1a Codex review: the reconnect line's passage check as a paid, untrusted-input call.

* **F1, isolation.** The passage is untrusted source text, so the request is an
  isolated turn (no files, tools, connectors or vault); a transport that cannot
  isolate it is refused before any request.
* **F2, spend.** Every check is admitted through the Phase 1 framework
  (``learnloop.ai.spend``) before it is sent: a daily count of checks, a
  per-check dollar cap on a metered route at the owner's price (an unknown
  price is refused), one admitted request per physical request on a metered
  route; Codex on the subscription is ``estimated_only``. Receipts are written
  before the request, so failed calls count.
* **F3, one check per reuse key.** A durable claim on (root exchange, prompt
  version) is taken before the model call; a second worker makes no call; a
  late completion never replaces the row the learner already saw; the queue
  never holds two live jobs for one key; the database refuses a second row.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import timedelta
from types import SimpleNamespace

import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.transport import ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.clock import FrozenClock
from learnloop.reader import reader_dialogue as RD
from learnloop.reader import reader_quick_check as RQC
from learnloop.reader.ai_contracts import ReadingQuickCheck
from tests.helpers import NOW
from tests.structured_ai import StructuredClientFake
from tests.test_reader_guidance import _setup as _guide_setup

_CLOCK = FrozenClock(NOW)


class RecordingClient(StructuredClientFake):
    """A transport that records every request it is sent (no tools, files or network)."""

    provider_name = "fake"
    provider_type = "codex_sdk"  # billed to the subscription unless a test says otherwise
    model = "fake-model"

    def __init__(self, *, provider_type: str | None = None, isolates: bool = True, fail: bool = False,
                 span_ids=("s1",), gate: threading.Event | None = None, entered: threading.Event | None = None,
                 usage: dict | None = None) -> None:
        if provider_type is not None:
            self.provider_type = provider_type
        self.isolates = isolates
        self.fail = fail
        self.span_ids = list(span_ids)
        self.gate = gate
        self.entered = entered
        self.usage = usage
        self.requests: list = []

    def supports(self, capability: str) -> bool:
        if capability == ISOLATED_TURN:
            return self.isolates
        return capability == STRUCTURED_COMPLETION

    def complete(self, request):
        self.requests.append(request)
        if self.entered is not None:
            self.entered.set()
        if self.gate is not None:
            assert self.gate.wait(10)
        if self.usage:
            from learnloop.ai.execution import report_call_usage

            report_call_usage(self.usage)
        if self.fail:
            raise RuntimeError("the provider dropped the connection")
        return ReadingQuickCheck(
            question_md="Why is A's eigenbasis orthonormal?",
            expected_answer_md="Because A is symmetric.",
            span_ids=self.span_ids,
        )


def _spend(**over) -> RQC.PassageCheckSpend:
    values = {"max_checks_per_day": 100, "max_usd_per_check": 0.25, "price_per_million": None, "output_tokens": 4_000}
    values.update(over)
    return RQC.PassageCheckSpend(**values)


def _root(vault, repo, question="Why orthonormal?"):
    return RD.ask(vault, repo, RD.StubReaderClient(), extraction_id="ext1", span_id="s1",
                  question_md=question, clock=_CLOCK)["reader_answer_event_id"]


def _author(repo, client, root, *, spend=None, owner="job_a", clock=_CLOCK):
    return RQC.author_inquiry_quick_check(
        repo, client, extraction_id="ext1", inquiry_root_event_id=root, anchor_span_ids=["s1"],
        clock=clock, spend=spend or _spend(), owner=owner,
    )


def _receipts(repo):
    with repo.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM model_call_receipts WHERE owner_kind = ? ORDER BY started_at", (RQC.PASSAGE_CHECK_RECEIPT_OWNER,)
        )]


def _inquiry_rows(repo):
    with repo.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM reader_authored_questions WHERE scope_kind = 'inquiry'"
        )]


def _job_ctx(repo, vault, client, root, *, job_id="ijob_1"):
    return SimpleNamespace(
        payload={"extraction_id": "ext1", "scope_kind": "inquiry", "inquiry_root_event_id": root,
                 "anchor_span_ids": ["s1"]},
        repo=repo, clock=_CLOCK, report=lambda *a, **k: None, vault_root=vault.root,
        job={"id": job_id, "batch_id": "batch_1", "attempt_count": 1},
        cancelled=lambda: False, bind_interruptible=lambda client: None,
        services=SimpleNamespace(quick_check_client=lambda ctx: client),
    )


# -- F1: an isolated turn, failing closed ---------------------------------------------

def test_the_passage_check_request_is_an_isolated_turn(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    client = RecordingClient()
    _author(repo, client, _root(vault, repo))
    (request,) = client.requests
    assert request.isolated is True
    assert request.workspace is None


def test_a_transport_that_cannot_isolate_the_passage_is_refused_before_any_request(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    client = RecordingClient(isolates=False)
    root = _root(vault, repo)
    with pytest.raises(AIProviderUnavailable):
        _author(repo, client, root)
    assert client.requests == [] and _inquiry_rows(repo) == [] and _receipts(repo) == []


def test_the_job_fails_closed_with_a_named_reason_when_isolation_is_unavailable(tmp_path):
    from learnloop.content.pipeline.jobs import handle_reader_quick_check
    from learnloop.content.pipeline.runner import IngestRunnerError

    vault, repo = _guide_setup(tmp_path)
    client = RecordingClient(isolates=False)
    with pytest.raises(IngestRunnerError) as raised:
        handle_reader_quick_check(_job_ctx(repo, vault, client, _root(vault, repo)))
    assert raised.value.code == "provider_unavailable"
    assert client.requests == []


# -- F2: spend admission before generation --------------------------------------------

def test_a_metered_route_without_an_owner_price_makes_no_request(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    client = RecordingClient(provider_type="openai_compatible")
    root = _root(vault, repo)
    with pytest.raises(RQC.PassageCheckRefused) as refused:
        _author(repo, client, root, spend=_spend(price_per_million=None))
    assert refused.value.reason == "spend_refused"
    assert client.requests == [] and _receipts(repo) == [] and _inquiry_rows(repo) == []
    # The claim was given back: a priced retry authors it.
    row = _author(repo, client, root, spend=_spend(price_per_million=1.0))
    assert row["scope_kind"] == "inquiry" and len(client.requests) == 1


def test_a_metered_check_over_its_dollar_cap_makes_no_request(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    client = RecordingClient(provider_type="openai_compatible")
    with pytest.raises(RQC.PassageCheckRefused) as refused:
        # ~4,000 output tokens plus the prompt at $100 per million is about $0.4.
        _author(repo, client, _root(vault, repo), spend=_spend(price_per_million=100.0, max_usd_per_check=0.05))
    assert refused.value.reason == "spend_refused"
    assert client.requests == [] and _receipts(repo) == []


def test_an_exhausted_daily_budget_makes_no_request(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    client = RecordingClient(provider_type="openai_compatible")
    spend = _spend(price_per_million=1.0, max_checks_per_day=1)
    _author(repo, client, _root(vault, repo, "First"), spend=spend, clock=None)
    assert len(client.requests) == 1
    with pytest.raises(RQC.PassageCheckRefused) as refused:
        _author(repo, client, _root(vault, repo, "Second"), spend=spend, clock=None, owner="job_b")
    assert refused.value.reason == "capped"
    assert len(client.requests) == 1  # nothing more was sent
    assert len([r for r in _receipts(repo) if r["parent_call_id"] is None]) == 1


def test_a_failed_call_is_receipted_and_counts_toward_the_daily_cap(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    failing = RecordingClient(provider_type="openai_compatible", fail=True)
    spend = _spend(price_per_million=1.0, max_checks_per_day=1)
    root = _root(vault, repo)
    with pytest.raises(RuntimeError):
        _author(repo, failing, root, spend=spend, clock=None)
    (receipt,) = [r for r in _receipts(repo) if r["parent_call_id"] is None]
    assert receipt["status"] == "failed"
    budget = json.loads(receipt["budget_json"])
    assert budget["max_calls"] == 1 and budget["max_estimated_usd"] == spend.max_usd_per_check
    healthy = RecordingClient(provider_type="openai_compatible")
    with pytest.raises(RQC.PassageCheckRefused):
        _author(repo, healthy, root, spend=spend, clock=None, owner="job_b")
    assert healthy.requests == []


def test_a_metered_check_is_one_admitted_physical_request_held_to_its_output_allowance(tmp_path):
    from learnloop.ai.execution import output_limit, single_request_active

    seen: dict = {}

    class Probe(RecordingClient):
        def complete(self, request):
            seen["single"] = single_request_active()
            seen["limit"] = output_limit()
            return super().complete(request)

    vault, repo = _guide_setup(tmp_path)
    _author(repo, Probe(provider_type="openai_compatible"), _root(vault, repo), spend=_spend(price_per_million=1.0))
    assert seen == {"single": True, "limit": 4_000}


def test_codex_on_the_subscription_runs_without_a_price_and_is_estimated_only(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    client = RecordingClient(provider_type="codex_sdk", usage={"input_tokens": 900, "output_tokens": 120})
    row = _author(repo, client, _root(vault, repo), spend=_spend(price_per_million=None))
    assert row["scope_kind"] == "inquiry" and len(client.requests) == 1
    (receipt,) = [r for r in _receipts(repo) if r["parent_call_id"] is None]
    budget = json.loads(receipt["budget_json"])
    assert budget["billing"] == "subscription" and budget["cost_basis"] == "estimated_only"
    assert budget["physical_request_bound"] is False
    usage = json.loads(receipt["usage_json"])
    assert usage["cost_basis"] == "estimated_only" and usage["estimated_total_tokens"] == 1020


@pytest.mark.parametrize("over,reason", [
    ({"price_per_million": None}, "spend_refused"),
    ({"price_per_million": 1.0, "max_checks_per_day": 0}, "capped"),
])
def test_the_job_reports_a_refusal_as_its_error_code_and_sends_nothing(tmp_path, monkeypatch, over, reason):
    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import IngestRunnerError

    vault, repo = _guide_setup(tmp_path)
    client = RecordingClient(provider_type="openai_compatible")
    monkeypatch.setattr(jobs, "_passage_check_spend", lambda ctx: _spend(**over))
    with pytest.raises(IngestRunnerError) as raised:
        jobs.handle_reader_quick_check(_job_ctx(repo, vault, client, _root(vault, repo)))
    assert raised.value.code == reason
    assert client.requests == []


def test_the_vaults_spend_settings_reach_the_check(tmp_path):
    from learnloop.content.pipeline import jobs
    from tests.helpers import append_config_toml

    vault, repo = _guide_setup(tmp_path)
    append_config_toml(vault.root, """
    [reader_inquiry]
    max_checks_per_day = 7
    max_usd_per_check = 0.03
    metered_price_per_million = 2.5
    """)
    spend = jobs._passage_check_spend(SimpleNamespace(vault_root=vault.root, cancelled=lambda: False))
    assert (spend.max_checks_per_day, spend.max_usd_per_check, spend.price_per_million) == (7, 0.03, 2.5)
    assert spend.output_tokens > 0


# -- F3: one check per (root exchange, prompt version) --------------------------------

def test_the_database_refuses_a_second_row_for_one_reuse_key(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    row = _author(repo, RecordingClient(), _root(vault, repo))
    with repo.connection() as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO reader_authored_questions (id, extraction_id, section_id, question_md, expected_answer_md, "
            "prompt_version, scope_kind, inquiry_root_event_id, created_at, updated_at) "
            "VALUES ('raq_dup', 'ext1', 'u1', 'Q', 'A', ?, 'inquiry', ?, 'x', 'x')",
            (row["prompt_version"], row["inquiry_root_event_id"]),
        )


def test_overlapping_workers_make_one_model_call_and_one_row(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    root = _root(vault, repo)
    gate, entered = threading.Event(), threading.Event()
    first = RecordingClient(gate=gate, entered=entered)
    outcome: dict = {}

    def worker_a():
        outcome["a"] = _author(repo, first, root, owner="job_a")

    thread = threading.Thread(target=worker_a)
    thread.start()
    assert entered.wait(10)  # worker A is inside its model call
    second = RecordingClient()
    with pytest.raises(RQC.InquiryCheckHeld):
        _author(repo, second, root, owner="job_b")
    assert second.requests == []
    gate.set()
    thread.join(10)
    assert len(_inquiry_rows(repo)) == 1 and outcome["a"]["id"] == _inquiry_rows(repo)[0]["id"]
    # Once it landed, every later request reuses it without a call.
    again = RecordingClient()
    assert _author(repo, again, root, owner="job_c")["id"] == outcome["a"]["id"] and again.requests == []


def test_a_late_completion_never_replaces_the_check_the_learner_saw(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    root = _root(vault, repo)
    gate, entered = threading.Event(), threading.Event()
    slow = RecordingClient(gate=gate, entered=entered)
    outcome: dict = {}

    def worker_a():
        try:
            outcome["a"] = _author(repo, slow, root, owner="job_a", clock=_CLOCK)
        except Exception as exc:  # noqa: BLE001 - asserted below
            outcome["error"] = exc

    thread = threading.Thread(target=worker_a)
    thread.start()
    assert entered.wait(10)
    # A's lease expires (a hung call); B takes the key over and lands a check,
    # which the learner answers.
    later = FrozenClock(NOW + timedelta(seconds=RQC.INQUIRY_CLAIM_LEASE_SECONDS + 60))
    landed = _author(repo, RecordingClient(), root, owner="job_b", clock=later)
    RQC.record_inquiry_action(repo, question_id=landed["id"], action="answered", response_md="Mine.", clock=later)
    gate.set()
    thread.join(10)
    rows = _inquiry_rows(repo)
    assert [r["id"] for r in rows] == [landed["id"]]
    assert rows[0]["response_md"] == "Mine."
    assert isinstance(outcome.get("error"), RQC.InquiryCheckHeld) or outcome["a"]["id"] == landed["id"]


def test_a_crashed_claim_is_recovered_by_its_own_job_at_once_and_by_others_after_its_lease(tmp_path):
    from learnloop.db.stores.judgment_claims import claim_work

    vault, repo = _guide_setup(tmp_path)
    root = _root(vault, repo)
    with repo.atomic():  # job_a claimed, then its process died mid-call
        claim_work(repo.connection(), claim_key=RQC.inquiry_claim_key(root), task=RQC.INQUIRY_CLAIM_TASK,
                   producer=RQC.INQUIRY_CLAIM_PRODUCER, prompt_version=RQC.INQUIRY_PROMPT_VERSION,
                   input_hash="x", owner="job_a", now="2026-05-19T12:00:00Z", lease_seconds=RQC.INQUIRY_CLAIM_LEASE_SECONDS)
    other = RecordingClient()
    with pytest.raises(RQC.InquiryCheckHeld):
        _author(repo, other, root, owner="job_b")
    assert other.requests == []
    # The runner re-runs job_a (same owner): it re-claims and authors.
    rerun = RecordingClient()
    assert _author(repo, rerun, root, owner="job_a")["scope_kind"] == "inquiry" and len(rerun.requests) == 1


def test_a_crashed_claim_from_another_job_is_taken_over_after_its_lease(tmp_path):
    from learnloop.db.stores.judgment_claims import claim_work

    vault, repo = _guide_setup(tmp_path)
    root = _root(vault, repo)
    with repo.atomic():
        claim_work(repo.connection(), claim_key=RQC.inquiry_claim_key(root), task=RQC.INQUIRY_CLAIM_TASK,
                   producer=RQC.INQUIRY_CLAIM_PRODUCER, prompt_version=RQC.INQUIRY_PROMPT_VERSION,
                   input_hash="x", owner="job_a", now="2026-05-19T12:00:00Z", lease_seconds=RQC.INQUIRY_CLAIM_LEASE_SECONDS)
    later = FrozenClock(NOW + timedelta(seconds=RQC.INQUIRY_CLAIM_LEASE_SECONDS + 1))
    client = RecordingClient()
    assert _author(repo, client, root, owner="job_b", clock=later)["scope_kind"] == "inquiry"
    assert len(client.requests) == 1


def test_a_second_request_while_one_is_live_joins_its_job(tmp_path):
    from learnloop.content.pipeline.jobs import DurableIngestJobs

    vault, repo = _guide_setup(tmp_path)
    jobs = DurableIngestJobs()
    jobs.bind(repo, vault.root, background=False)
    jobs._ensure_worker = lambda: None  # the quick-check workers have not reached it yet
    first = jobs.enqueue_reader_inquiry_check(extraction_id="ext1", inquiry_root_event_id="root_a", anchor_span_ids=["s1"])
    again = jobs.enqueue_reader_inquiry_check(extraction_id="ext1", inquiry_root_event_id="root_a", anchor_span_ids=["s1"])
    other = jobs.enqueue_reader_inquiry_check(extraction_id="ext1", inquiry_root_event_id="root_b", anchor_span_ids=["s1"])
    assert again == first and other != first
    # A finished (here: cancelled) job no longer holds the key: a new request queues anew.
    jobs.cancel_batch(first)
    assert jobs.enqueue_reader_inquiry_check(extraction_id="ext1", inquiry_root_event_id="root_a", anchor_span_ids=["s1"]) != first
