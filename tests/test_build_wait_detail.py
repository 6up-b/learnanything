"""An honest wait (the first evening, step 6): while a book is got ready and its questions are written, the facts
a waiting screen shows, each recorded when it happened.

- a streamed request's output, through the real plan stream on a fake clock: none yet, advancing, a long silence,
  a retry, the reply, and a transport that does not stream (it records no output, so none is ever claimed);
- the synthesis's own steps (planning, a further pass with the passages it asked for, a part kept from before,
  checking with the topics a parsed candidate drafted, saving), never a topic count before one exists;
- a book's working line and a section's writing carry them, with a measured time only where this library has one
  and the number of samples it rests on.

Every model call is a fake; the request bytes are the same with the recording on.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from learnloop.ai.execution import model_call, observe_model_output, single_request
from learnloop.ai.providers.chatgpt_plan import ChatGPTPlanProviderClient
from learnloop.ai.schemas import WireModel
from learnloop.config.schema import ChatGPTPlanProviderConfig
from learnloop.content.pipeline.runner import IngestRunner, JobSpec
from learnloop.content.pipeline.wait_detail import build_detail, topic_minutes, writing_detail
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from tests.plan_deadline_fakes import Session, completed, delta, install_stream

BASE = datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC)
#: What a build's detail may hold: facts, never an estimate, a percentage or a time left.
BUILD_KEYS = {"as_of", "started_at", "stage", "retry", "delivery", "measured", "inventory", "synthesis", "drafted_topics"}
WRITING_KEYS = {"as_of", "started_at", "queued", "retry", "topic", "topic_started_at", "delivery", "measured"}
DELIVERY_KEYS = {"request_sent_at", "reply_received_at", "output_pieces", "last_output_at"}


class Answer(WireModel):
    ok: bool


class StreamClock:
    """The runner's wall clock, moving with the fake stream's: a piece of output at stream time t is recorded at
    BASE + t."""

    def __init__(self, stream):
        self.stream = stream

    def now(self):
        return BASE + timedelta(seconds=self.stream.now)


def plan_client():
    return ChatGPTPlanProviderClient("plan", ChatGPTPlanProviderConfig(
        model="fake", base_url="http://127.0.0.1", timeout_seconds=180), session=Session())


def _ask():
    from learnloop.ai.transport import execute_structured_operation

    with single_request():
        return execute_structured_operation(plan_client(), purpose="probe", prompt="unchanged", result_model=Answer,
                                            timeout_seconds=480)


def _build(tmp_path, monkeypatch, events, *, job_type="bootstrap_synthesis", seen_at=()):
    """One build step on the real runner whose model request streams ``events`` (stream seconds, event) on the fake
    clock; at each of ``seen_at`` (stream seconds) the job's detail is read, as a screen would read it then: as the
    stream's next line arrives, before that line's event is handled (an event is seen by the read after it)."""

    clock, requests, _connections = install_stream(monkeypatch, events, interrupt_at=lambda t: look(t))
    repo = Repository(tmp_path / "state.sqlite")
    runner = IngestRunner(repo, vault_root=tmp_path, worker_id="w1", clock=StreamClock(clock),
                          handlers={job_type: lambda ctx: _ask().model_dump()})
    batch_id = runner.enqueue_batch("auto_build", [JobSpec(job_type, payload={"auto_build": {}})])
    seen: dict[float, dict] = {}
    due = sorted(seen_at)

    def look(t):
        while due and t >= due[0]:
            batch = repo.get_ingest_batch(batch_id)
            seen[due.pop(0)] = build_detail(repo, batch, measured=None, now=StreamClock(clock).now())

    runner.drain()
    return repo, batch_id, seen, requests


def test_no_output_yet_names_the_request_and_claims_no_output(tmp_path, monkeypatch):
    # The reply's first piece comes at 120 s; at 60 s the request is in flight and nothing has streamed.
    _repo, _batch, seen, _ = _build(tmp_path, monkeypatch, [(60, {"type": "response.created"}), (120, delta()),
                                                             (130, completed())], seen_at=[60])
    detail = seen[60]
    assert set(detail) <= BUILD_KEYS
    assert detail["stage"] == "planning" and detail["retry"] is False
    delivery = detail["delivery"]
    assert set(delivery) == DELIVERY_KEYS
    assert delivery["request_sent_at"] is not None and delivery["reply_received_at"] is None
    assert delivery["output_pieces"] == 0 and delivery["last_output_at"] is None


def test_advancing_output_is_recorded_as_it_arrives(tmp_path, monkeypatch):
    _repo, _batch, seen, _ = _build(tmp_path, monkeypatch, [(t, delta()) for t in (100, 200, 300)] + [(310, completed())],
                                    seen_at=[200, 300, 310])
    assert [seen[t]["delivery"]["output_pieces"] for t in (200, 300, 310)] == [1, 2, 3]
    assert [seen[t]["delivery"]["last_output_at"] for t in (200, 300, 310)] == [
        (BASE + timedelta(seconds=t)).isoformat().replace("+00:00", "Z") for t in (100, 200, 300)]


def test_a_long_silence_keeps_the_last_output_time_and_counts_no_lifecycle_event(tmp_path, monkeypatch):
    # Output at 100 s, then only lifecycle events (not output) until the reply at 270 s: within the idle window.
    events = [(100, delta()), (170, {"type": "response.in_progress"}), (250, {"type": "response.in_progress"}),
              (270, completed())]
    _repo, _batch, seen, _ = _build(tmp_path, monkeypatch, events, seen_at=[170, 250, 270])
    assert [seen[t]["delivery"]["output_pieces"] for t in (170, 250, 270)] == [1, 1, 1]
    last = (BASE + timedelta(seconds=100)).isoformat().replace("+00:00", "Z")
    assert {seen[t]["delivery"]["last_output_at"] for t in (170, 250, 270)} == {last}


def test_a_retry_starts_its_record_afresh_and_says_it_is_one(tmp_path, monkeypatch):
    # The inventory's first try is cut idle (silent after 100 s); the runner tries once more on its own.
    def events(request):
        return [(100, delta()), (400, completed())] if request == 1 else [(50, {"type": "response.created"}),
                                                                          (60, delta()), (70, completed())]

    repo, batch_id, seen, requests = _build(tmp_path, monkeypatch, events, job_type="inventory", seen_at=[400, 450])
    first, second = seen[400], seen[450]
    # Read as the first try's stream is cut (idle since 100 s): its one piece is still the newest output.
    assert first["retry"] is False and first["stage"] == "reading"
    assert first["delivery"]["output_pieces"] == 1
    # The second try's request is in flight at 450 with nothing streamed on it yet.
    assert second["retry"] is True
    assert second["delivery"]["output_pieces"] == 0 and second["delivery"]["last_output_at"] is None
    assert len(requests) == 2
    job = repo.ingest_jobs_for_batch(batch_id)[0]
    assert repo.ingest_job_progress(job["id"])["try_number"] == 2


def test_the_reply_is_named_once_received_and_no_output_is_then_in_flight(tmp_path, monkeypatch):
    clock, _requests, _ = install_stream(monkeypatch, [(100, delta()), (110, completed())])
    repo = Repository(tmp_path / "state.sqlite")
    after: list[dict] = []

    def handler(ctx):
        answer = _ask()
        batch = repo.get_ingest_batch(ctx.job["batch_id"])
        after.append(build_detail(repo, batch, measured=None, now=StreamClock(clock).now()))
        return answer.model_dump()

    runner = IngestRunner(repo, vault_root=tmp_path, worker_id="w1", clock=StreamClock(clock),
                          handlers={"bootstrap_synthesis": handler})
    runner.enqueue_batch("auto_build", [JobSpec("bootstrap_synthesis", payload={"auto_build": {}})])
    runner.drain()
    delivery = after[0]["delivery"]
    assert delivery["reply_received_at"] is not None
    assert delivery["request_sent_at"] is None
    assert delivery["output_pieces"] == 0 and delivery["last_output_at"] is None


def test_a_transport_that_does_not_stream_reports_no_output(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    inside: list[dict] = []

    def handler(ctx):
        client = SimpleNamespace(provider_name="fake", model="fake", config=None)
        with model_call(client, purpose="whole_reply"):
            batch = repo.get_ingest_batch(ctx.job["batch_id"])
            inside.append(build_detail(repo, batch, measured=None, now=BASE))
        return {}

    runner = IngestRunner(repo, vault_root=tmp_path, worker_id="w1", clock=SimpleNamespace(now=lambda: BASE),
                          handlers={"bootstrap_synthesis": handler})
    runner.enqueue_batch("auto_build", [JobSpec("bootstrap_synthesis", payload={"auto_build": {}})])
    runner.drain()
    delivery = inside[0]["delivery"]
    assert delivery["request_sent_at"] is not None
    assert delivery["output_pieces"] == 0 and delivery["last_output_at"] is None


def test_output_is_written_at_most_about_once_a_second(tmp_path, monkeypatch):
    # Ten pieces in half a second, then one more two seconds later: the first of the ten is written, the rest of
    # that second is not, and the later piece is (with the count it brings).
    events = [(100 + i * 0.05, delta()) for i in range(10)] + [(102, delta()), (103, completed())]
    _repo, _batch, seen, _ = _build(tmp_path, monkeypatch, events, seen_at=[102, 103])
    assert seen[102]["delivery"]["output_pieces"] == 1
    assert seen[103]["delivery"]["output_pieces"] == 11


def test_the_request_bytes_are_the_same_with_the_recording_on(monkeypatch):
    _clock, requests, _ = install_stream(monkeypatch, [(10, delta()), (11, completed())])
    _ask()
    with observe_model_output(lambda call_id, pieces: None):
        _clock.now = 0.0
        _ask()
    assert len(requests) == 2 and requests[0] == requests[1]


# -- The synthesis's own steps ------------------------------------------------------------------------------------


def _steps():
    events: list[tuple] = []

    def progress(stage, message, current, total, *, step=None, drafted_topics=None):
        events.append((step, current, total, drafted_topics))

    progress.takes_step = True
    return events, progress


def test_the_synthesis_names_its_steps_and_counts_topics_only_once_parsed(tmp_path):
    from learnloop.content.synthesis.source_set_synthesis import create_study_map
    from tests.source_set_synthesis_helpers import _CLOCK, FakeSynthesisClient, _setup

    root, repo = _setup(tmp_path, with_exam=False)
    events, progress = _steps()
    result = create_study_map(root, "set_la", client=FakeSynthesisClient(), brief={"depth": "intro"},
                              repository=repo, clock=_CLOCK, apply=True, progress=progress)
    steps = [event[0] for event in events if event[0]]
    assert steps[:1] == ["plan"] and steps[-1] == "apply"
    assert {"validate", "persist"} <= set(steps)
    assert steps.index("validate") > steps.index("plan")
    # A count only once the candidate is complete, parsed and normalized: never on a planning step.
    drafted = [event[3] for event in events if event[3] is not None]
    assert all(event[3] is None for event in events if event[0] != "validate")
    written = sum(1 for row in repo.proposal_items(result.proposal_id) if row["item_type"] == "learning_object")
    assert drafted == [written] and written > 0


def test_an_extra_evidence_pass_is_named_as_one(tmp_path):
    from learnloop.content.synthesis.source_set_synthesis import create_study_map
    from learnloop.content.synthesis.ai_contracts import SourceSetSynthesis
    from tests.source_set_synthesis_helpers import _CLOCK, FakeSynthesisClient, _default_payload, _first_semantic_span, _setup

    root, repo = _setup(tmp_path, with_exam=False)

    def builder(context, ordinal):
        if ordinal == 1:
            extraction, unit, span = _first_semantic_span(context)
            return SourceSetSynthesis(span_requests=[{"extraction_id": extraction, "unit_id": unit, "span_id": span}])
        return _default_payload(context)

    events, progress = _steps()
    create_study_map(root, "set_la", client=FakeSynthesisClient(builder=builder), repository=repo, clock=_CLOCK,
                     progress=progress)
    planning = [(step, current, total) for step, current, total, _ in events if step in {"plan", "evidence"}]
    # One part, two model passes: the part count is not the number of calls.
    assert planning == [("plan", 1, 1), ("evidence", 1, 1)]


def test_a_part_kept_from_an_earlier_run_is_named_as_kept(tmp_path):
    from learnloop.ai.errors import AITurnTimeout
    from learnloop.content.synthesis.source_set_synthesis import create_study_map
    from tests.source_set_synthesis_helpers import _CLOCK, FakeSynthesisClient, _default_payload, _setup_two_chapters

    root, repo = _setup_two_chapters(tmp_path)
    failing = {"on": True}

    def builder(context, ordinal):
        if ordinal == 2 and failing["on"]:
            raise AITurnTimeout("the second part was cut")
        return _default_payload(context)

    client = FakeSynthesisClient(builder=builder)
    budgets = {"synthesis_shard_input_tokens": 1}
    with pytest.raises(AITurnTimeout):
        create_study_map(root, "set_la", client=client, repository=repo, clock=_CLOCK, budget_overrides=budgets)
    failing["on"] = False
    events, progress = _steps()
    create_study_map(root, "set_la", client=client, repository=repo, clock=_CLOCK, budget_overrides=budgets,
                     progress=progress)
    planning = [(step, current, total) for step, current, total, _ in events if step in {"plan", "plan_reused"}]
    assert planning == [("plan_reused", 1, 2), ("plan", 2, 2)]


# -- What a book's line and a section's writing carry -------------------------------------------------------------


def _progress_row(repo, job, **facts):
    repo.start_ingest_job_progress(job["id"], attempt_count=job["attempt_count"], try_number=1)
    repo.record_ingest_job_progress(job["id"], attempt_count=job["attempt_count"], **facts)


def _book_being_built(tmp_path, *, step=None, drafted=None, root=None, name="probability_book.md", text=None):
    from learnloop.content.pipeline.add_source import latest_auto_outcome
    from tests.ux_phase1_review_fixes_helpers import _add, _jobs
    from tests.ux_phase1_support import BOOK_MARKDOWN, fake_services, fresh_library, grant_consent, write_book

    root = root or fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services())
    item = _add(root, jobs, write_book(tmp_path, name, text or BOOK_MARKDOWN))
    batch_id = latest_auto_outcome(repo, item["source_id"])["build_batch_id"]
    with repo.connection() as connection:
        connection.execute("UPDATE ingest_batches SET status = 'running', finished_at = NULL WHERE id = ?", (batch_id,))
        connection.execute("UPDATE ingest_jobs SET status = 'running', finished_at = NULL, current_window = 1, "
                           "total_windows = 1 WHERE batch_id = ? AND job_type IN ('bootstrap_synthesis', 'append_synthesis')",
                           (batch_id,))
        connection.commit()
    synthesis = next(job for job in repo.ingest_jobs_for_batch(batch_id) if job["job_type"].endswith("_synthesis"))
    if step:
        _progress_row(repo, synthesis, step=step, drafted_topics=drafted)
    return root, repo, item


def _line(root, repo, item):
    from learnloop.content.pipeline.add_source import source_status_line

    return source_status_line(repo, load_vault(root), item["source_id"])


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)


def test_a_books_working_line_carries_its_build_detail(tmp_path, isolated_config):
    root, repo, item = _book_being_built(tmp_path, step="validate", drafted=8)
    line = _line(root, repo, item)
    detail = line["build_detail"]
    assert set(detail) <= BUILD_KEYS
    assert detail["stage"] == "checking" and detail["drafted_topics"] == 8
    # The library's first build: nothing measured, so no time is said.
    assert detail["measured"] is None and "minutes" not in line
    # The words and the existing facts are unchanged beside it.
    assert line["text"] == "Getting Ch. 1–2 ready for questions" and line["tone"] == "working"


def test_a_planning_step_says_its_part_and_no_topic_count(tmp_path, isolated_config):
    root, repo, item = _book_being_built(tmp_path, step="plan")
    detail = _line(root, repo, item)["build_detail"]
    assert detail["stage"] == "planning"
    assert detail["synthesis"] == {"part": 1, "parts": 1, "pass": "plan"}
    assert "drafted_topics" not in detail


def test_a_measured_build_time_says_how_many_builds_it_rests_on(tmp_path, isolated_config):
    from tests.ux_phase1_review_fixes_helpers import _jobs
    from tests.ux_phase1_support import BOOK_MARKDOWN, fake_services, fresh_library, grant_consent, write_book
    from tests.ux_phase1_review_fixes_helpers import _add

    root = fresh_library(tmp_path)
    grant_consent(root)
    _repo, jobs = _jobs(root, fake_services())
    _add(root, jobs, write_book(tmp_path, "first_book.md", BOOK_MARKDOWN))
    root, repo, item = _book_being_built(tmp_path, root=root, name="second_book.md",
                                         text=BOOK_MARKDOWN + "\nA second book's own closing line.\n")
    detail = _line(root, repo, item)["build_detail"]
    assert detail["measured"] == {"minutes": 0.0, "samples": 1}


def test_a_section_being_written_names_its_topic_and_this_librarys_time_per_topic(tmp_path):
    from tests.section_question_parts_helpers import TOPICS, Writer, enqueue, jobs_for, section

    paths, repo = section(tmp_path)
    writer = Writer()
    during: list[dict] = []

    def at_second_topic():
        if len(writer.calls) == 2:
            job = repo.ingest_jobs_by_types(["practice_expansion"])[0]
            during.append(writing_detail(repo, load_vault(paths.root), job, measured=topic_minutes(repo), now=BASE))

    writer.before = at_second_topic
    enqueue(jobs_for(paths, repo, writer))
    detail = during[0]
    assert set(detail) == WRITING_KEYS
    assert detail["queued"] is False and detail["retry"] is False
    assert detail["topic"] == {"title": TOPICS[1], "index": 2, "total": len(TOPICS)}
    assert detail["topic_started_at"] is not None
    # One topic written so far: this library's time per topic rests on it alone.
    assert detail["measured"]["samples"] == 1
    # Once the section is written, every topic is timed (the newest five are the sample).
    assert topic_minutes(repo)[1] == 5
    parts = repo.ingest_jobs_by_types(["practice_expansion"])[0]["payload"]["question_parts"]
    assert all(part["started_at"] <= part["written_at"] for part in parts)


def test_before_any_topic_is_timed_nothing_is_measured(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    assert topic_minutes(repo) is None
    repo.insert_ingest_batch(id="batch_old", workflow_type="practice_expansion")
    repo.insert_ingest_job(id="job_old", batch_id="batch_old", ordinal=0, job_type="practice_expansion",
                           payload={"learning_object_ids": ["lo"], "question_parts": [{"topic_id": "lo", "patch_id": "p"}]})
    # Parts written before topics were timed carry no times: still nothing measured.
    assert topic_minutes(repo) is None


def test_a_queued_section_job_says_it_waits_and_nothing_else(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    repo.insert_ingest_batch(id="batch_q", workflow_type="practice_expansion")
    repo.insert_ingest_job(id="job_q", batch_id="batch_q", ordinal=0, job_type="practice_expansion",
                           payload={"learning_object_ids": ["lo"]})
    detail = writing_detail(repo, SimpleNamespace(learning_objects={}), repo.get_ingest_job("job_q"), measured=None,
                            now=BASE)
    assert detail["queued"] is True
    assert detail["topic"] is None and detail["delivery"] is None and detail["measured"] is None
    assert json.dumps(detail).count("%") == 0


def _section_job(repo, item, section_id, *, parts):
    from learnloop.content.sources.source_outline import resolve_extraction_id
    from tests.ux_phase1_support import CLOCK

    extraction_id = resolve_extraction_id(repo, item["source_id"])
    repo.upsert_reader_section_progress(extraction_id=extraction_id, section_id=section_id, spans_seen=3, span_count=3,
                                        completed=True, clock=CLOCK)
    batch_id = f"batch_section_{section_id}"
    repo.insert_ingest_batch(id=batch_id, workflow_type="practice_expansion", clock=CLOCK)
    repo.insert_ingest_job(id=f"ijob_section_{section_id}", batch_id=batch_id, ordinal=0, job_type="practice_expansion",
                           payload={"learning_object_ids": [part["topic_id"] for part in parts], "question_parts": parts},
                           clock=CLOCK)
    repo.mark_section_generation(extraction_id=extraction_id, section_id=section_id, batch_id=batch_id, clock=CLOCK)
    with repo.connection() as connection:
        connection.execute("UPDATE ingest_jobs SET status = 'running', attempt_count = 1, total_windows = ?, current_window = 0 "
                           "WHERE batch_id = ?", (len(parts), batch_id))
        connection.commit()


def test_the_topic_keeps_its_place_only_while_one_job_writes(tmp_path, isolated_config):
    from learnloop.content.sources.source_outline import resolve_extraction_id

    root, repo, item = _book_being_built(tmp_path)
    with repo.connection() as connection:  # the build finished: its sections' questions can be written
        connection.execute("UPDATE ingest_batches SET status = 'completed', finished_at = started_at")
        connection.execute("UPDATE ingest_jobs SET status = 'completed', finished_at = started_at")
        connection.commit()
        extraction_id = resolve_extraction_id(repo, item["source_id"])
        sections = [row[0] for row in connection.execute(
            "SELECT unit_id FROM source_document_units WHERE extraction_id = ? ORDER BY ordinal", (extraction_id,))]
    topic = sorted(load_vault(root).learning_objects)[0]
    _section_job(repo, item, sections[0], parts=[{"topic_id": topic, "started_at": "2026-10-13T09:00:00Z"}, {"topic_id": "lo_b"}])
    detail = _line(root, repo, item)["questions"]["writing_detail"]
    assert detail["topic"]["index"] == 1 and detail["topic"]["total"] == 2
    _section_job(repo, item, sections[1], parts=[{"topic_id": "lo_c"}, {"topic_id": "lo_d"}])
    questions = _line(root, repo, item)["questions"]
    assert questions["progress"] == {"done": 0, "total": 4}
    assert questions["writing_detail"]["topic"]["index"] is None and questions["writing_detail"]["topic"]["total"] is None
    assert questions["writing_detail"]["topic"]["title"]
