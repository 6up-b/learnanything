"""UX Phase 1 Codex review: one test (or more) per finding, written to fail first.

docs/reviews/ux-phase1-codex-review.md lists the findings. Every model call is a
house fake; money is counted from synthetic ``model_call_receipts`` rows; no
provider, network or credential is touched.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.clock import FrozenClock
from learnloop.content.pipeline import add_source as core
from learnloop.content.pipeline.add_source import (
    AddSourceOptions,
    add_source,
    advance_reading_build,
    latest_auto_outcome,
    outline_chapters,
    request_auto_build,
    source_status_line,
    undo_source_questions,
)
from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.content.pipeline.runner import JobSpec
from learnloop.content.sources.source_outline import build_source_outline, resolve_extraction_id
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.ux_phase1_support import (
    CLOCK,
    Calls,
    fake_services,
    fresh_library,
    grant_consent,
    repository,
    route,
    set_config,
    write_book,
    write_pdf,
)


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Each test its own machine defaults: an OK recorded here (and mirrored to
    the machine's AI defaults) must not reach another test's new library."""

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    monkeypatch.delenv("LEARNLOOP_MARKER_PROVIDER", raising=False)


def call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _jobs(root, services, *, hold: bool = False):
    repo = repository(root)
    jobs = DurableIngestJobs()
    jobs.bind(repo, root, background=False, clock=CLOCK, services=services)
    if hold:
        jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    return repo, jobs


def _drain(jobs, max_jobs=None):
    return jobs._require_runner().drain(max_jobs=max_jobs)


def _add(root, jobs, source, **options):
    return add_source(load_vault(root), jobs, str(source), AddSourceOptions(**options), clock=CLOCK)


def _build_batches(repo):
    return [batch for batch in repo.list_ingest_batches() if batch["workflow_type"] == "bootstrap_synthesis"]


def _labels(repo, source_id):
    extraction_id = resolve_extraction_id(repo, source_id)
    return {chapter.label: chapter.unit_id for chapter in outline_chapters(build_source_outline(repo, extraction_id))}


def _active_lo_ids(root):
    return {lo_id for lo_id, lo in load_vault(root).learning_objects.items() if lo.status == "active"}


def _receipt(repo, *, provider, cost=None, input_tokens=0, output_tokens=0, owner_kind="sidecar_request",
             owner_id="req_1", started_at=None):
    """A finished model call receipt, as the runner's observer records one."""

    call_id = f"call_{owner_id}_{provider}_{cost}_{input_tokens}_{started_at}"
    started = started_at or CLOCK.now().isoformat()
    repo.record_model_event("start", {"id": call_id, "purpose": "test", "provider": provider,
                                      "model": "m", "started_at": started},
                            owner_kind=owner_kind, owner_id=owner_id)
    repo.record_model_event("finish", {"id": call_id, "status": "completed", "finished_at": started,
                                       "input_tokens": input_tokens, "output_tokens": output_tokens,
                                       "cost": cost}, owner_kind=owner_kind, owner_id=owner_id)


def _metered(root, price):
    set_config(root, {("ingest", "cost_pause", "prices", "openrouter"): price})
    grant_consent(root, "openrouter")
    return route(provider="openrouter", subscription=False, consent_key="openrouter")


# ---------------------------------------------------------------------------
# F1 [High] "Keep this book on this computer" is the book's, everywhere
# ---------------------------------------------------------------------------


def test_f1_a_later_build_of_a_kept_local_book_writes_no_questions(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    calls = Calls()
    repo, jobs = _jobs(root, fake_services(calls=calls))
    item = _add(root, jobs, write_book(tmp_path), keep_local=True)
    source_id = item["source_id"]
    assert repo.source_kept_local(source_id) is True

    # "Build questions for the whole book" from book details, and a retry.
    request_auto_build(jobs, source_id, chapter_ids=list(_labels(repo, source_id).values()))
    request_auto_build(jobs, source_id, approved=True)
    assert latest_auto_outcome(repo, source_id)["reason"] == "kept_local"
    assert _build_batches(repo) == []
    assert calls.inventory_calls == 0 and calls.synthesis_calls == 0


def test_f1_no_question_build_sends_a_kept_local_book(tmp_path):
    """Any build path (here a deliberate one, as Under the hood starts it)."""

    root = fresh_library(tmp_path)
    grant_consent(root)
    calls = Calls()
    repo, jobs = _jobs(root, fake_services(calls=calls))
    item = _add(root, jobs, write_book(tmp_path), keep_local=True)
    extraction_id = resolve_extraction_id(repo, item["source_id"])
    unit_id = next(iter(_labels(repo, item["source_id"]).values()))
    batch_id = jobs._require_runner().enqueue_batch(
        "bootstrap_synthesis", [JobSpec("inventory", {"extraction_id": extraction_id,
                                                      "units": [{"unit_id": unit_id, "role": "primary_textbook"}]})]
    )
    _drain(jobs)
    job = repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "failed" and job["error"]["code"] == "kept_local"
    assert calls.inventory_calls == 0


def _audio_file(tmp_path):
    path = tmp_path / "lecture_one.mp3"
    path.write_bytes(b"ID3\x03\x00\x00\x00\x00\x00\x00fake audio frames")
    return path


def test_f1_a_kept_local_recording_is_never_sent_to_transcription(tmp_path, monkeypatch):
    from learnloop.content.pipeline import jobs as jobs_module

    sent = []
    monkeypatch.setattr(jobs_module, "_extract_audio", lambda fetched, ctx: sent.append(fetched) or None)
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, _audio_file(tmp_path), keep_local=True)
    assert sent == []
    line = source_status_line(repo, load_vault(root), item["source_id"])
    assert line["text"] == "Kept on this computer — this recording can't be read here"
    assert line["action"] is None


def test_f1_sending_a_whole_recording_out_waits_for_its_own_ok(tmp_path, monkeypatch):
    from learnloop.content.pipeline import jobs as jobs_module
    from learnloop.content.pipeline.runner import IngestRunnerError

    sent = []

    def transcribe(fetched, ctx):
        sent.append(fetched)
        raise IngestRunnerError("transcription endpoint not reachable in tests", code="audio_failed")

    monkeypatch.setattr(jobs_module, "_extract_audio", transcribe)
    root = fresh_library(tmp_path)
    grant_consent(root)  # the connection's OK covers passages and answers only
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=fake_services())
    item = call(ctx, "add_source", {"sources": [str(_audio_file(tmp_path))]})["items"][0]
    assert sent == []
    card = next(c for c in call(ctx, "get_source_library", {})["sources"] if c["sourceId"] == item["sourceId"])
    assert card["statusLine"]["text"] == "Transcribing this recording sends it to an online service"
    assert card["statusLine"]["action"] == {"kind": "allow_upload", "label": "OK"}

    call(ctx, "source_action", {"sourceId": item["sourceId"], "action": "allow_upload"})
    record = load_vault(root).config.ai.consent["whole_files"]
    assert record.data_flow == "whole_files" and record.granted_at
    assert len(sent) == 1  # only now does the recording leave


def test_f1_a_kept_local_book_never_uses_the_whole_pdf_model_or_hosted_marker(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from learnloop.content.pipeline.jobs import _pdf_payload_config

    root = fresh_library(tmp_path)
    set_config(root, {("ingest", "pdf", "engine"): "native"})
    kept = SimpleNamespace(job={"_keep_local": True}, payload={}, vault_root=root)
    assert _pdf_payload_config(kept).get("engine") != "native"
    monkeypatch.setenv("LEARNLOOP_MARKER_PROVIDER", "datalab")
    set_config(root, {("ingest", "pdf", "engine"): "auto"})
    assert _pdf_payload_config(kept)["engine"] == "pypdf"
    shared = SimpleNamespace(job={}, payload={}, vault_root=root)
    assert _pdf_payload_config(shared).get("engine") != "pypdf"


def test_f1_the_reader_sends_nothing_from_a_kept_local_book(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=fake_services())
    item = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))], "keepLocal": True})["items"][0]
    extraction_id = resolve_extraction_id(ctx.repository, item["sourceId"])
    section_id = next(iter(_labels(ctx.repository, item["sourceId"]).values()))
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.author_section_question", {"extractionId": extraction_id, "sectionId": section_id})
    assert caught.value.code == "kept_on_this_computer"
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.ask", {"extractionId": extraction_id, "spanId": "s1", "question": "Why?"})
    assert caught.value.code == "kept_on_this_computer"
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.enqueue_request", {
            "sourceId": item["sourceId"], "revisionId": item["revisionId"], "extractionId": extraction_id,
            "spanId": "s1", "preset": "explain",
        })
    assert caught.value.code == "kept_on_this_computer"


def test_f1_book_details_can_keep_a_book_local_and_let_it_go_again(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=fake_services())
    item = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))], "keepLocal": True})["items"][0]
    card = next(c for c in call(ctx, "get_source_library", {})["sources"] if c["sourceId"] == item["sourceId"])
    assert card["keepLocal"] is True
    call(ctx, "source_action", {"sourceId": item["sourceId"], "action": "share_with_ai"})
    assert ctx.repository.source_kept_local(item["sourceId"]) is False
    assert latest_auto_outcome(ctx.repository, item["sourceId"])["outcome"] == "building"


# ---------------------------------------------------------------------------
# F2 [High] Money: a confirmation threshold, enforceable limits, real spending
# ---------------------------------------------------------------------------


def test_f2_build_them_never_passes_the_daily_cap(tmp_path):
    root = fresh_library(tmp_path)
    authoring = _metered(root, 2_000.0)
    set_config(root, {("ingest", "cost_pause", "daily_cap_usd"): 1.0})
    calls = Calls()
    repo, jobs = _jobs(root, fake_services(authoring, calls=calls))
    _receipt(repo, provider="openrouter", cost=0.99)  # today's spending elsewhere
    item = _add(root, jobs, write_book(tmp_path))
    outcome = latest_auto_outcome(repo, item["source_id"])
    assert (outcome["outcome"], outcome["cost_reason"]) == ("paused", "budget_used")

    request_auto_build(jobs, item["source_id"], approved=True)  # "Build them"
    assert latest_auto_outcome(repo, item["source_id"])["cost_reason"] == "budget_used"
    assert _build_batches(repo) == [] and calls.inventory_calls == 0
    line = source_status_line(repo, load_vault(root), item["source_id"])
    assert line["text"] == "Paused — today's AI budget is used"
    assert line["action"] == {"kind": "open_settings", "label": "Raise it"}


def test_f2_todays_spending_is_what_model_calls_cost_not_planner_estimates(tmp_path):
    root = fresh_library(tmp_path)
    _metered(root, 1.0)
    set_config(root, {("ingest", "cost_pause", "daily_cap_usd"): 5.0})
    repo, _jobs_unused = _jobs(root, fake_services())
    config = load_vault(root).config
    # A receipt with a reported cost, one priced from its tokens, one billed to
    # the subscription (free), and yesterday's spending.
    _receipt(repo, provider="openrouter", cost=0.40, owner_id="a")
    _receipt(repo, provider="openrouter", input_tokens=200_000, output_tokens=100_000, owner_id="b")
    _receipt(repo, provider="codex_medium", input_tokens=900_000, owner_id="c")
    _receipt(repo, provider="openrouter", cost=3.0, owner_id="d",
             started_at=(CLOCK.now() - timedelta(days=1)).isoformat())
    assert core.spent_today_usd(repo, config, CLOCK.now()) == pytest.approx(0.40 + 0.30)


def test_f2_each_paid_job_is_admitted_at_the_route_it_really_uses(tmp_path):
    """A runtime fallback to a pricier route is priced as itself."""

    root = fresh_library(tmp_path)
    cheap = _metered(root, 0.01)
    set_config(root, {("ingest", "cost_pause", "prices", "openrouter_pricey"): 500_000.0})
    holder = [cheap]
    calls = Calls()
    repo, jobs = _jobs(root, fake_services(calls=calls, route_holder=holder), hold=True)
    item = _add(root, jobs, write_book(tmp_path))
    _drain(jobs, max_jobs=2)  # the import and the planner
    assert latest_auto_outcome(repo, item["source_id"])["outcome"] == "building"

    holder[0] = route(provider="openrouter_pricey", subscription=False, consent_key="openrouter")
    _drain(jobs)
    assert calls.inventory_calls == 0
    build = _build_batches(repo)[0]
    inventory = next(job for job in repo.ingest_jobs_for_batch(build["id"]) if job["job_type"] == "inventory")
    assert inventory["error"]["code"] == "spend_paused"
    assert inventory["error"]["details"]["provider"] == "openrouter_pricey"
    line = source_status_line(repo, load_vault(root), item["source_id"])
    assert line["text"] == "Questions for Ch. 1–2 would cost more than expected"
    assert line["action"] == {"kind": "build_now", "label": "Build them"}


def test_f2_a_retry_is_admitted_against_what_the_build_already_spent(tmp_path):
    root = fresh_library(tmp_path)
    authoring = _metered(root, 0.01)
    calls = Calls()
    repo, jobs = _jobs(root, fake_services(authoring, calls=calls), hold=True)
    item = _add(root, jobs, write_book(tmp_path))
    _drain(jobs, max_jobs=2)
    outcome = latest_auto_outcome(repo, item["source_id"])
    inventory = next(job for job in repo.ingest_jobs_for_batch(outcome["build_batch_id"])
                     if job["job_type"] == "inventory")
    # An earlier attempt of this job already spent past the authorization.
    _receipt(repo, provider="openrouter", cost=outcome["authorized_usd"] + 0.5,
             owner_kind="ingest_job", owner_id=inventory["id"])
    _drain(jobs)
    assert calls.inventory_calls == 0
    failed = repo.get_ingest_job(inventory["id"])
    assert failed["error"]["code"] == "spend_paused"
    assert failed["error"]["details"]["reason"] == "authorization"


def test_f2_the_dry_run_makes_no_call_and_writes_nothing(tmp_path):
    root = fresh_library(tmp_path)
    authoring = _metered(root, 400_000.0)
    calls = Calls()
    repo, jobs = _jobs(root, fake_services(authoring, calls=calls))
    set_config(root, {("ingest", "auto_build"): False})
    item = _add(root, jobs, write_book(tmp_path))
    set_config(root, {("ingest", "auto_build"): True})
    before = (len(repo.list_ingest_batches()), list(load_vault(root).source_sets), list(load_vault(root).subjects))

    report = core.preview_auto_build(root, repo, item["source_id"], whole_book=True, route=authoring, now=CLOCK.now())
    assert report["model_calls"] == 0 and report["writes"] == 0
    assert report["status"] == "would_ask_first"
    assert report["chapters"] == ["1 Probability and counting", "2 Conditional probability",
                                  "3 Random variables", "4 Expectation"]
    assert report["cost_basis"] == "metered" and report["estimate_usd"] > 1.0
    after = (len(repo.list_ingest_batches()), list(load_vault(root).source_sets), list(load_vault(root).subjects))
    assert after == before and calls.inventory_calls == 0 and calls.synthesis_calls == 0


def test_f2_the_dry_run_command(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from learnloop.cli import app

    monkeypatch.setattr(core, "authoring_route_for", lambda _root, _config: route())
    root = fresh_library(tmp_path)
    grant_consent(root)
    set_config(root, {("ingest", "auto_build"): False})
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    set_config(root, {("ingest", "auto_build"): True})
    result = CliRunner().invoke(app, ["sources", "build-preview", item["source_id"], "--vault", str(root), "--json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["model_calls"] == 0 and report["chapters"]


# ---------------------------------------------------------------------------
# F3 [High] A planner that dies after queuing its build
# ---------------------------------------------------------------------------


class _Crash(BaseException):
    """The process dying: not an exception the runner turns into a failure."""


def test_f3_a_planner_that_dies_after_queuing_its_build_is_never_orphaned(tmp_path, monkeypatch):
    from learnloop.content.pipeline.runner import JobContext

    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services(), hold=True)
    item = _add(root, jobs, write_book(tmp_path))
    source_id = item["source_id"]
    _drain(jobs, max_jobs=1)  # the import

    real = JobContext.enqueue_batch

    def enqueue_then_die(self, *args, **kwargs):
        real(self, *args, **kwargs)
        raise _Crash()

    monkeypatch.setattr(JobContext, "enqueue_batch", enqueue_then_die)
    with pytest.raises(_Crash):
        _drain(jobs, max_jobs=1)  # the planner: build committed, result never saved
    monkeypatch.setattr(JobContext, "enqueue_batch", real)
    planner = core.auto_jobs(repo, source_id)[0]
    assert planner["status"] == "running" and planner["result"] is None
    assert len(_build_batches(repo)) == 1
    # The book already knows its build is underway.
    assert source_status_line(repo, load_vault(root), source_id)["text"].startswith("Questions for Ch. 1–2 in about")

    # Restart: the dead lease is recovered, then the planner is resumed.
    runner = jobs._require_runner()
    runner.clock = FrozenClock(CLOCK.now() + timedelta(hours=1))
    runner.recover_stale_leases()
    assert repo.get_ingest_job(planner["id"])["status"] == "failed"
    assert source_status_line(repo, load_vault(root), source_id)["text"].startswith("Questions for Ch. 1–2 in about")
    jobs.resume_batch(planner["batch_id"])
    _drain(jobs)
    assert len(_build_batches(repo)) == 1  # never a second build
    assert repo.get_ingest_job(planner["id"])["result"]["build_batch_id"] == core.child_batch_id(planner["id"])
    assert source_status_line(repo, load_vault(root), source_id)["text"] == "Questions for Ch. 1–2 come up as you read"
    assert undo_source_questions(jobs, source_id, clock=CLOCK) > 0


# ---------------------------------------------------------------------------
# F4 [Medium] Kill switches govern work already queued
# ---------------------------------------------------------------------------


def test_f4_turning_auto_build_off_stops_queued_automatic_work(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    calls = Calls()
    repo, jobs = _jobs(root, fake_services(calls=calls), hold=True)
    item = _add(root, jobs, write_book(tmp_path))
    _drain(jobs, max_jobs=2)
    assert latest_auto_outcome(repo, item["source_id"])["outcome"] == "building"

    set_config(root, {("ingest", "auto_build"): False})
    _drain(jobs)
    assert calls.inventory_calls == 0 and calls.synthesis_calls == 0
    assert _build_batches(repo)[0]["status"] == "cancelled"
    assert _active_lo_ids(root) == set()
    assert source_status_line(repo, load_vault(root), item["source_id"]) is None


def test_f4_turning_auto_apply_off_after_planning_keeps_the_build_unapplied(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services(), hold=True)
    item = _add(root, jobs, write_book(tmp_path))
    _drain(jobs, max_jobs=2)
    set_config(root, {("ingest", "auto_apply_passing_builds"): False})
    _drain(jobs)
    build = _build_batches(repo)[0]
    synthesis = next(job for job in repo.ingest_jobs_for_batch(build["id"]) if job["job_type"] == "bootstrap_synthesis")
    assert synthesis["status"] == "completed"
    assert synthesis["result"]["applied"] is False and synthesis["result"]["proposal_id"]
    assert _active_lo_ids(root) == set()
    assert source_status_line(repo, load_vault(root), item["source_id"])["text"] == "Questions for Ch. 1–2 need a look"


# ---------------------------------------------------------------------------
# F5 [Medium] Undo while a chapter is building
# ---------------------------------------------------------------------------


def test_f5_undo_while_a_chapter_builds_keeps_it_from_putting_content_back(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    state: dict = {}

    def undo_mid_build(_context):
        # The learner taps Undo while Ch. 3 is being written.
        state["reverted"] = undo_source_questions(state["jobs"], state["source_id"], clock=CLOCK)

    repo, jobs = _jobs(root, fake_services(on_append=undo_mid_build))
    state["jobs"] = jobs
    item = _add(root, jobs, write_book(tmp_path))
    source_id = state["source_id"] = item["source_id"]
    labels = _labels(repo, source_id)
    extraction_id = resolve_extraction_id(repo, source_id)

    advance_reading_build(jobs, extraction_id, labels["2 Conditional probability"])
    assert state["reverted"] > 0
    assert _active_lo_ids(root) == set()
    ch3 = _build_batches(repo)[0]
    append = next(job for job in repo.ingest_jobs_for_batch(ch3["id"]) if job["job_type"] == "bootstrap_synthesis")
    assert not (append.get("result") or {}).get("auto_applied_item_ids")
    line = source_status_line(repo, load_vault(root), source_id)
    assert line["text"] == "Questions for this book were taken back out"
    # Reading on no longer grows the book's questions until they are built again.
    assert advance_reading_build(jobs, extraction_id, labels["3 Random variables"]) is None


def test_f5_undo_cancels_a_build_still_waiting_to_run(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    calls = Calls()
    repo, jobs = _jobs(root, fake_services(calls=calls))
    item = _add(root, jobs, write_book(tmp_path))
    labels = _labels(repo, item["source_id"])
    jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    advance_reading_build(jobs, resolve_extraction_id(repo, item["source_id"]), labels["2 Conditional probability"])
    _drain(jobs, max_jobs=1)  # the planner queues Ch. 3
    before = calls.inventory_calls
    undo_source_questions(jobs, item["source_id"], clock=CLOCK)
    _drain(jobs)
    assert calls.inventory_calls == before
    assert _build_batches(repo)[0]["status"] == "cancelled"


# ---------------------------------------------------------------------------
# F6 [Medium] A failed chapter is not a built chapter
# ---------------------------------------------------------------------------


def test_f6_failed_chapters_are_built_again_by_build_the_whole_book(tmp_path):
    from learnloop.content.pipeline.runner import IngestRunnerError

    root = fresh_library(tmp_path)
    grant_consent(root)
    failing = {"on": True}

    def fail(_context):
        if failing["on"]:
            raise IngestRunnerError("the model returned nothing usable", code="synthesis_failed")

    repo, jobs = _jobs(root, fake_services(on_append=fail))
    item = _add(root, jobs, write_book(tmp_path))
    source_id = item["source_id"]
    labels = _labels(repo, source_id)
    advance_reading_build(jobs, resolve_extraction_id(repo, source_id), labels["2 Conditional probability"])
    assert _build_batches(repo)[0]["status"] == "failed"
    cover = core.coverage(repo, source_id)
    assert labels["3 Random variables"] in cover.failed
    assert labels["3 Random variables"] not in core.built_unit_ids(repo, source_id)

    failing["on"] = False
    call_ids = list(labels.values())
    request_auto_build(jobs, source_id, chapter_ids=call_ids)  # Build questions for the whole book
    assert latest_auto_outcome(repo, source_id)["chapters"] == ["3 Random variables", "4 Expectation"]
    assert core.coverage(repo, source_id).failed == set()


# ---------------------------------------------------------------------------
# F7 [Medium] Reading progress during a build is kept and acted on
# ---------------------------------------------------------------------------


def test_f7_reading_ahead_while_a_build_runs_is_built_when_it_finishes(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    source_id = item["source_id"]
    labels = _labels(repo, source_id)
    extraction_id = resolve_extraction_id(repo, source_id)
    jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    advance_reading_build(jobs, extraction_id, labels["2 Conditional probability"])  # Ch. 3 queued
    # The learner jumps to Ch. 4 while Ch. 3 is still being built.
    deferred = advance_reading_build(jobs, extraction_id, labels["4 Expectation"])
    assert deferred["deferred"] is True
    assert repo.source_auto_build_state(source_id)["wanted_section_id"] == labels["4 Expectation"]

    _drain(jobs)
    assert labels["4 Expectation"] in core.coverage(repo, source_id).built
    assert repo.source_auto_build_state(source_id)["wanted_section_id"] is None


def test_f7_a_position_that_waited_across_a_restart_is_acted_on_when_the_library_opens(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    labels = _labels(repo, item["source_id"])
    repo.set_source_wanted_reading(item["source_id"], resolve_extraction_id(repo, item["source_id"]),
                                   labels["3 Random variables"])
    started = core.reconcile_reading_builds(jobs)
    assert started == [item["source_id"]]
    assert labels["3 Random variables"] in core.coverage(repo, item["source_id"]).built


# ---------------------------------------------------------------------------
# F9 [Medium] Text recognition is real or says it is not set up
# ---------------------------------------------------------------------------


def test_f9_text_recognition_without_an_extractor_that_can_do_it_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "text_recognition_available", lambda **_: False)
    root = fresh_library(tmp_path)
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=fake_services())
    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    item = call(ctx, "add_source", {"sources": [str(write_pdf(tmp_path))], "textRecognition": True})["items"][0]
    assert item["message"] == core.TEXT_RECOGNITION_UNAVAILABLE_MESSAGE
    import_job = next(job for job in ctx.repository.ingest_jobs_for_batch(item["batchId"]) if job["job_type"] == "import")
    assert "force_ocr" not in (import_job["payload"].get("pdf_config") or {})
    with pytest.raises(SidecarError) as caught:
        call(ctx, "source_action", {"sourceId": item["sourceId"], "action": "text_recognition"})
    assert caught.value.code == "text_recognition_unavailable"


def test_f9_text_recognition_names_an_extractor_that_recognises_text(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "text_recognition_available", lambda **_: True)
    root = fresh_library(tmp_path)
    set_config(root, {("ingest", "pdf", "engine"): "pypdf"})
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=fake_services())
    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    item = call(ctx, "add_source", {"sources": [str(write_pdf(tmp_path))]})["items"][0]
    out = call(ctx, "source_action", {"sourceId": item["sourceId"], "action": "text_recognition"})
    import_job = next(job for job in ctx.repository.ingest_jobs_for_batch(out["batchId"]) if job["job_type"] == "import")
    assert import_job["payload"]["pdf_config"] == {"engine": "marker", "force_ocr": True}


# ---------------------------------------------------------------------------
# F10 [Medium] A book's history is not a window over the whole queue
# ---------------------------------------------------------------------------


def test_f10_a_books_history_survives_lots_of_other_work(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    runner = jobs._require_runner()
    runner.clock = FrozenClock(CLOCK.now() + timedelta(minutes=5))
    jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    runner.enqueue_batch(
        core.AUTO_BUILD_WORKFLOW,
        [JobSpec(core.AUTO_STUDY_MAP_JOB, {"source_id": f"src_other_{index}"}) for index in range(520)],
    )
    assert core.latest_auto_outcome(repo, item["source_id"])["outcome"] == "building"
    assert source_status_line(repo, load_vault(root), item["source_id"])["text"] == "Questions for Ch. 1–2 come up as you read"
    assert undo_source_questions(jobs, item["source_id"], clock=CLOCK) > 0


def test_f10_connecting_releases_a_book_however_old_its_wait(tmp_path):
    root = fresh_library(tmp_path)
    repo, jobs = _jobs(root, fake_services(route(ready=False, message="not set up")))
    item = _add(root, jobs, write_book(tmp_path))
    assert latest_auto_outcome(repo, item["source_id"])["reason"] == "no_ai"
    runner = jobs._require_runner()
    runner.clock = FrozenClock(CLOCK.now() + timedelta(minutes=5))
    jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    runner.enqueue_batch(
        core.AUTO_BUILD_WORKFLOW,
        [JobSpec(core.AUTO_STUDY_MAP_JOB, {"source_id": f"src_other_{index}"}) for index in range(520)],
    )
    assert item["source_id"] in core.release_waiting_builds(jobs)


# ---------------------------------------------------------------------------
# F11 [Medium] Retry repairs a preserved result before paying again
# ---------------------------------------------------------------------------


def test_f11_retry_tries_the_zero_model_repair_first_then_a_fresh_run(tmp_path, monkeypatch):
    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=fake_services())
    repo, jobs = ctx.repository, ctx.ingest_jobs
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    outcome = latest_auto_outcome(repo, source_id)
    synthesis = next(job for job in repo.ingest_jobs_for_batch(outcome["build_batch_id"])
                     if job["job_type"] == "bootstrap_synthesis")
    # The gates failed after the model's result was kept (as the service does).
    repo.transition_unleased_ingest_job(
        synthesis["id"], status="failed", phase="failed", message="gates failed",
        error={"code": "synthesis_gate_failed", "message": "gates failed",
               "details": {"candidate_preserved": True, "synthesis_run_id": "run_kept"}},
        clock=CLOCK,
    )
    seen: list[dict] = []
    monkeypatch.setattr(jobs, "retry_synthesis", lambda batch_id, **kwargs: seen.append(kwargs) or {})
    call(ctx, "source_action", {"sourceId": source_id, "action": "retry"})
    assert seen == [{"reuse_candidate": True, "repair_candidate": True}]

    # The repair ran and failed too: the next Retry is a fresh (paid) run.
    payload = dict(synthesis["payload"], reuse_candidate=True, repair_candidate=True, synthesis_run_id="run_kept")
    repo.update_ingest_job_payload(synthesis["id"], payload)
    call(ctx, "source_action", {"sourceId": source_id, "action": "retry"})
    assert seen[-1] == {}


# ---------------------------------------------------------------------------
# F12 [Medium] Undo is an owner verdict in judgment_ledger
# ---------------------------------------------------------------------------


def test_f12_undo_records_the_owners_verdict_once(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path))
    proposal_id = core._build_state(repo, latest_auto_outcome(repo, item["source_id"]))["proposal_id"]
    undo_source_questions(jobs, item["source_id"], clock=CLOCK)
    undo_source_questions(jobs, item["source_id"], clock=CLOCK)
    with repo.connection() as connection:
        rows = [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = ?", (core.UNDO_JUDGMENT_TASK,)
        ).fetchall()]
    assert len(rows) == 1
    row = rows[0]
    assert (row["judge"], row["verdict"], row["left_kind"], row["left_id"], row["right_kind"], row["right_id"]) == (
        "owner", "rejected", "proposal", proposal_id, "source", item["source_id"],
    )
    rationale = json.loads(row["rationale"])
    assert rationale["action"] == "undo_questions" and rationale["item_ids"]


# ===========================================================================
# Codex re-review (be3ad518..3784487c): F1, F2, F3 reopened; F13 new
# ===========================================================================


def _first_span_id(repo, extraction_id):
    ir = repo.load_document_ir(extraction_id)
    return next(block.span_id for block in sorted(ir.blocks, key=lambda b: b.ordinal) if (block.text or "").strip())


def _reader_ctx(root, client, services=None):
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=services or fake_services(),
                         reader_synth_client_factory=lambda: client)
    return ctx


def _queue_reader_request(ctx, item):
    from learnloop.reader import reader_requests as RR

    extraction_id = resolve_extraction_id(ctx.repository, item["sourceId"])
    return RR.enqueue_request(
        ctx.repository, source_id=item["sourceId"], revision_id=item["revisionId"], extraction_id=extraction_id,
        span_id=_first_span_id(ctx.repository, extraction_id), preset="worked_example",
    )


def test_f1_rereview_keeping_a_book_local_stops_the_reader_requests_it_queued(tmp_path):
    from tests.test_reader_requests import _FakePresetClient

    root = fresh_library(tmp_path)
    grant_consent(root)
    client = _FakePresetClient()
    ctx = _reader_ctx(root, client)
    item = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]
    queued = _queue_reader_request(ctx, item)

    call(ctx, "source_action", {"sourceId": item["sourceId"], "action": "keep_local"})
    ctx.ingest_jobs.kick_reader_drain()  # the production drain, as the worker runs it
    assert client.calls == []
    assert ctx.repository.get_reader_request(queued["request_id"])["status"] == "cancelled"


def test_f1_rereview_the_drain_reads_the_books_privacy_when_it_runs(tmp_path):
    """However the policy was persisted (another window, an Add of the same
    book with the option), a queued request is checked when it is executed."""

    from tests.test_reader_requests import _FakePresetClient

    root = fresh_library(tmp_path)
    grant_consent(root)
    client = _FakePresetClient()
    ctx = _reader_ctx(root, client)
    item = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]
    queued = _queue_reader_request(ctx, item)

    ctx.repository.set_source_keep_local(item["sourceId"], True)
    ctx.ingest_jobs.kick_reader_drain()
    assert client.calls == []
    row = ctx.repository.get_reader_request(queued["request_id"])
    assert row["status"] == "cancelled"
    assert json.loads(row["error_json"])["code"] == "kept_on_this_computer"


def test_f1_rereview_keeping_a_book_local_stops_its_queued_build(tmp_path):
    root = fresh_library(tmp_path)
    grant_consent(root)
    calls = Calls()
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=fake_services(calls=calls))
    repo, jobs = ctx.repository, ctx.ingest_jobs
    jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    _drain(jobs, max_jobs=2)  # the import and the planner: the build is queued
    assert latest_auto_outcome(repo, source_id)["outcome"] == "building"

    call(ctx, "source_action", {"sourceId": source_id, "action": "keep_local"})
    _drain(jobs)
    assert calls.inventory_calls == 0 and calls.synthesis_calls == 0
    assert _build_batches(repo)[0]["status"] == "cancelled"
    card = next(c for c in call(ctx, "get_source_library", {})["sources"] if c["sourceId"] == source_id)
    assert card["statusLine"]["text"] == "Kept on this computer — no questions are written for it"


def _openrouter_client():
    from learnloop.ai.providers.openrouter import OpenRouterProviderClient
    from learnloop.config import AIProviderConfig

    return OpenRouterProviderClient(
        "openrouter", AIProviderConfig(type="openrouter", model="test/model", response_format="json_object")
    )


def test_f2_rereview_a_json_repair_is_admitted_like_any_paid_request(tmp_path, monkeypatch):
    """The provider's own JSON repair is a second paid request: it is admitted
    against what the first one really cost (its reported cost here is more
    than the whole build was allowed)."""

    from tests.openai_fakes import install_fake_openai

    fake = install_fake_openai(monkeypatch, "not json", "still not json",
                               usages=[{"prompt_tokens": 900, "completion_tokens": 50, "cost": 5.0}])
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-a-credential")
    root = fresh_library(tmp_path)
    authoring = _metered(root, 0.01)
    repo, jobs = _jobs(root, fake_services(authoring, inventory_client_factory=lambda ctx: _openrouter_client()))
    item = _add(root, jobs, write_book(tmp_path))

    sent = [len(instance.requests) for instance in fake.instances]
    assert sum(sent) >= 1 and max(sent) == 1  # no repair request went out
    outcome = latest_auto_outcome(repo, item["source_id"])
    inventory = next(job for job in repo.ingest_jobs_for_batch(outcome["build_batch_id"])
                     if job["job_type"] == "inventory")
    assert inventory["error"]["code"] == "spend_paused"
    assert inventory["error"]["details"]["reason"] == "authorization"
    line = source_status_line(repo, load_vault(root), item["source_id"])
    assert line["action"] == {"kind": "build_now", "label": "Build them"}


def test_f2_rereview_every_physical_attempt_is_admitted_retries_and_repairs_included(monkeypatch):
    from pydantic import BaseModel

    from learnloop.ai.execution import gate_model_requests
    from learnloop.ai.providers import openai_chat
    from learnloop.ai.transport import execute_structured_operation
    from tests.openai_fakes import FakeAPIConnectionError, install_fake_openai

    class Answer(BaseModel):
        answer: str

    class Recording:
        def __init__(self):
            self.admitted: list[str] = []
            self.settled: list[dict] = []

        def admit(self, client, *, purpose, prompt, budget):
            self.admitted.append(purpose)
            return len(self.admitted)

        def settle(self, admission, usage):
            self.settled.append(dict(usage))

    monkeypatch.setattr(openai_chat, "_sleep", lambda _seconds: None)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-a-credential")
    install_fake_openai(monkeypatch, FakeAPIConnectionError("reset"), "not json", '{"answer": "42"}')
    gate = Recording()
    with gate_model_requests(gate):
        result = execute_structured_operation(_openrouter_client(), purpose="probe", prompt="Answer.",
                                              result_model=Answer)
    assert result.answer == "42"
    # The transport retry, the first answer and the JSON repair: three physical
    # requests, each admitted and settled; the structured call around them is not one.
    assert gate.admitted == ["chat_request", "chat_request", "chat_request"]
    assert len(gate.settled) == 3


def test_f2_rereview_a_transport_retry_is_refused_when_the_failed_attempt_used_the_room(monkeypatch):
    from pydantic import BaseModel

    from learnloop.ai.execution import gate_model_requests
    from learnloop.ai.providers import openai_chat
    from learnloop.ai.spend import MeteredRequestGate, SpendLimitExceeded
    from learnloop.ai.transport import execute_structured_operation
    from tests.openai_fakes import FakeAPIConnectionError, install_fake_openai

    class Answer(BaseModel):
        answer: str

    monkeypatch.setattr(openai_chat, "_sleep", lambda _seconds: None)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-a-credential")
    fake = install_fake_openai(monkeypatch, FakeAPIConnectionError("reset"), '{"answer": "42"}')
    client = _openrouter_client()
    # One request is its input (a few hundred tokens) plus a 100k output
    # ceiling, at $1 a token: room for one, not for a second.
    gate = MeteredRequestGate(limit_usd=150_000, price_per_token=lambda provider: 1.0,
                              is_subscription=lambda c: False, default_output_tokens=100_000)
    with pytest.raises(SpendLimitExceeded), gate_model_requests(gate):
        execute_structured_operation(client, purpose="probe", prompt="Answer.", result_model=Answer)
    # A failed attempt reports nothing, so its reservation stands: no retry.
    assert sum(len(instance.requests) for instance in fake.instances) == 1
    assert gate.refusal is not None


def test_f2_rereview_append_reconciliation_calls_are_admitted_one_by_one(tmp_path):
    """Append reconciliation may ask for more passages and call the model
    again; each request inside the build is admitted on its own."""

    from learnloop.ai.execution import model_call, report_call_usage

    class Metered:
        provider_name = "openrouter"
        model = "test/model"

    sent: list[str] = []

    def two_paid_requests(_context):
        for label in ("first", "with more passages"):
            with model_call(Metered(), purpose="chat_request", prompt=label, budget=100):
                sent.append(label)
                report_call_usage({"input_tokens": 100, "output_tokens": 100, "cost": 5.0})

    root = fresh_library(tmp_path)
    authoring = _metered(root, 0.01)
    on_append = {"hook": None}
    repo, jobs = _jobs(root, fake_services(authoring, on_append=lambda c: on_append["hook"] and on_append["hook"](c)))
    item = _add(root, jobs, write_book(tmp_path))
    source_id = item["source_id"]
    labels = _labels(repo, source_id)
    on_append["hook"] = two_paid_requests
    advance_reading_build(jobs, resolve_extraction_id(repo, source_id), labels["2 Conditional probability"])
    assert sent == ["first"]
    ch3 = _build_batches(repo)[0]
    synthesis = next(job for job in repo.ingest_jobs_for_batch(ch3["id"]) if job["job_type"] == "bootstrap_synthesis")
    assert synthesis["error"]["code"] == "spend_paused"


def _book_html() -> str:
    sections = [
        ("1 Probability and counting", "A probability is a number between zero and one."),
        ("2 Conditional probability", "Conditioning updates a probability in the light of new evidence."),
        ("3 Random variables", "A random variable assigns a number to every outcome."),
        ("4 Expectation", "The expectation of a random variable is its probability-weighted average."),
    ]
    body = "".join(f"<h1>{title}</h1><p>{text} {text} {text}</p>" for title, text in sections)
    return f"<!doctype html><html><head><title>Probability notes</title></head><body>{body}</body></html>"


def test_f3_rereview_a_link_planner_that_dies_after_queuing_its_build_is_found(tmp_path, monkeypatch):
    """A link's Add knows no book yet: its planner's payload has no source.
    The build it queued carries the book, and that association is enough."""

    from learnloop.content.pipeline.runner import FetchedBytes, JobContext

    def fetch(source, category, ctx):
        return FetchedBytes(raw_bytes=_book_html().encode(), content_type="text/html", original_uri=source,
                            retrieved_at=CLOCK.now().isoformat(), title="Probability notes")

    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services(fetch=fetch), hold=True)
    item = _add(root, jobs, "https://example.org/probability-notes")
    assert item["status"] == "queued" and item["source_id"] is None
    _drain(jobs, max_jobs=1)  # the import registers the book
    batch_jobs = repo.ingest_jobs_for_batch(item["batch_id"])
    source_id = next(job for job in batch_jobs if job["job_type"] == "import")["result"]["source_id"]
    planner = next(job for job in batch_jobs if job["job_type"] == core.AUTO_STUDY_MAP_JOB)
    assert "source_id" not in (planner["payload"] or {})

    real = JobContext.enqueue_batch

    def enqueue_then_die(self, *args, **kwargs):
        real(self, *args, **kwargs)
        raise _Crash()

    monkeypatch.setattr(JobContext, "enqueue_batch", enqueue_then_die)
    with pytest.raises(_Crash):
        _drain(jobs, max_jobs=1)  # the planner: build committed, result never saved
    monkeypatch.setattr(JobContext, "enqueue_batch", real)

    assert [job["id"] for job in core.auto_jobs(repo, source_id)] == [planner["id"]]
    assert core.latest_auto_outcome(repo, source_id)["build_batch_id"] == core.child_batch_id(planner["id"])
    assert source_status_line(repo, load_vault(root), source_id)["text"].startswith("Questions for")


def test_f13_letting_a_kept_local_recording_go_resumes_it_through_the_whole_file_ok(tmp_path, monkeypatch):
    from learnloop.content.pipeline import jobs as jobs_module
    from learnloop.content.pipeline.runner import IngestRunnerError

    sent = []

    def transcribe(fetched, ctx):
        sent.append(fetched)
        raise IngestRunnerError("transcription endpoint not reachable in tests", code="audio_failed")

    monkeypatch.setattr(jobs_module, "_extract_audio", transcribe)
    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=fake_services())
    item = call(ctx, "add_source", {"sources": [str(_audio_file(tmp_path))], "keepLocal": True})["items"][0]
    source_id = item["sourceId"]

    def card():
        return next(c for c in call(ctx, "get_source_library", {})["sources"] if c["sourceId"] == source_id)

    assert card()["statusLine"]["text"] == "Kept on this computer — this recording can't be read here"

    call(ctx, "source_action", {"sourceId": source_id, "action": "share_with_ai"})
    assert ctx.repository.source_kept_local(source_id) is False
    assert sent == []  # sharing passages is not the OK to upload the whole recording
    assert card()["statusLine"]["text"] == "Transcribing this recording sends it to an online service"
    assert card()["statusLine"]["action"] == {"kind": "allow_upload", "label": "OK"}

    # Trying the original import again never brings the old choice back.
    call(ctx, "source_action", {"sourceId": source_id, "action": "retry"})
    assert ctx.repository.source_kept_local(source_id) is False
    assert sent == []

    call(ctx, "source_action", {"sourceId": source_id, "action": "allow_upload"})
    assert len(sent) == 1
    assert ctx.repository.source_kept_local(source_id) is False


def test_f13_a_links_keep_local_is_applied_once_when_its_book_is_registered(tmp_path):
    """A link's book exists only once the import registers it, so the import
    applies the Add's choice then, once. After that the book's persisted
    choice decides: an import tried again never brings the old choice back."""

    from learnloop.content.pipeline import jobs as jobs_module
    from learnloop.content.pipeline.runner import FetchedBytes

    url = "https://example.org/probability-notes"
    crash = {"on": True}

    def fetch(source, category, ctx):
        return FetchedBytes(raw_bytes=_book_html().encode(), content_type="text/html", original_uri=source,
                            retrieved_at=CLOCK.now().isoformat(), title="Probability notes")

    def extract(fetched, category, ctx):
        if crash["on"]:
            raise _Crash()  # the process dies after the book was registered
        return jobs_module.default_extract(fetched, category, ctx)

    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services(fetch=fetch, extract=extract), hold=True)
    item = _add(root, jobs, url, keep_local=True)
    with pytest.raises(_Crash):
        _drain(jobs, max_jobs=1)
    import_job = next(job for job in repo.ingest_jobs_for_batch(item["batch_id"]) if job["job_type"] == "import")
    source_id = repo.source_artifact_by_uri("web", url)["id"]
    assert repo.source_kept_local(source_id) is True
    assert repo.get_ingest_job(import_job["id"])["payload"]["keep_local_applied"] is True

    repo.set_source_keep_local(source_id, False)  # the learner lets it go
    crash["on"] = False
    runner = jobs._require_runner()
    runner.clock = FrozenClock(CLOCK.now() + timedelta(hours=1))
    runner.recover_stale_leases()
    jobs.resume_batch(item["batch_id"])
    _drain(jobs)
    assert repo.get_ingest_job(import_job["id"])["status"] == "completed"
    assert repo.source_kept_local(source_id) is False


def test_f1_rereview_a_running_build_sends_nothing_more_once_the_book_is_kept_local(tmp_path):
    """Keeping a book local while its build is mid-call: the call under way is
    not recalled, but the build starts no further request (on the
    subscription route too: privacy is not about money)."""

    from learnloop.ai.execution import model_call

    class Subscription:
        provider_name = "codex_medium"
        provider_type = "codex_sdk"
        model = "test"

    sent: list[str] = []
    state: dict = {}

    def keep_local_between_requests(_context):
        with model_call(Subscription(), purpose="sdk_turn", prompt="first", budget=100):
            sent.append("first")
        core.keep_on_this_computer(state["jobs"], state["source_id"])
        with model_call(Subscription(), purpose="sdk_turn", prompt="second", budget=100):
            sent.append("second")

    root = fresh_library(tmp_path)
    grant_consent(root)
    hook = {"on": None}
    repo, jobs = _jobs(root, fake_services(on_append=lambda c: hook["on"] and hook["on"](c)))
    state["jobs"] = jobs
    item = _add(root, jobs, write_book(tmp_path))
    source_id = state["source_id"] = item["source_id"]
    labels = _labels(repo, source_id)
    hook["on"] = keep_local_between_requests
    advance_reading_build(jobs, resolve_extraction_id(repo, source_id), labels["2 Conditional probability"])
    assert sent == ["first"]
    ch3 = _build_batches(repo)[0]
    synthesis = next(job for job in repo.ingest_jobs_for_batch(ch3["id"]) if job["job_type"] == "bootstrap_synthesis")
    assert synthesis["status"] == "cancelled"
    line = source_status_line(repo, load_vault(root), source_id)
    assert line["text"] == "Kept on this computer — no questions are written for it"
