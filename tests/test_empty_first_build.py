"""A book's first build that comes back with no topic is not a finished build (UX-43).

On the live route a first build's synthesis once answered with concepts and a facet but no topic (no learning
object, no blueprint), though its prompt says to author them in every mode. Every check passed it, the build read
"Completed", the section the learner had finished was settled as needing no questions, and Today told the learner
to finish a section the Reader showed as finished.

Now a first build (a bootstrap whose subject has no topic yet, not the narrow adjunct, with a source that may teach)
whose answer holds no topic with a usable blueprint asks once more, fresh, and takes the second answer as it is.
Still empty, the build says so (the card's line, its facts, Today), offers Try again, and a later build that finds
topics writes the questions owed to the sections finished meanwhile. Every model call is a house fake.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256

import pytest

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.ai.errors import AITurnTimeout
from learnloop.content.pipeline import add_source as core
from learnloop.content.proposals.proposals import reject_items
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.content.synthesis.source_set_synthesis import create_study_map
from learnloop_sidecar.context import SidecarContext

from tests.source_set_synthesis_helpers import _CLOCK, FakeSynthesisClient, _default_payload, _setup, _setup_two_chapters
from tests.ux_phase1_add_source_helpers import call
from tests.ux_phase1_support import CLOCK, FakeBookSynthesisClient, fake_services, fresh_library, grant_consent, write_book

#: The house fake's topic cites the first section of the house book when the whole book is built at once.
CITED = "u1"
NO_TOPIC_SUMMARY = "Concepts for the chapter. Practice items are deferred to reading progress."
ASKED_AGAIN = "asked_again_without_a_topic"


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)


def no_topic(context):
    """What the walk's model wrote: the concepts and a facet, no learning object, no blueprint."""

    payload = _default_payload(context)
    return payload.model_copy(update={"learning_objects": [], "blueprints": [], "practice_items": [],
                                      "summary": NO_TOPIC_SUMMARY})


class RecordingSynthesisClient(FakeSynthesisClient):
    def __init__(self, *, builder):
        super().__init__(builder=builder)
        self.synthesis_requests = []

    def complete(self, request):
        if request.purpose == "source_set_synthesis":
            self.synthesis_requests.append(request)
        return super().complete(request)


class Script:
    """The answers the synthesis gives, in order, across every client a test's builds make: ``"none"`` (no topic),
    ``"topics"`` (the house answer) or ``"timeout"`` (a failure a fresh try may cure). After the list: topics."""

    def __init__(self, *answers: str) -> None:
        self.answers = list(answers)
        self.asked = 0

    def answer(self, context, _n):
        self.asked += 1
        kind = self.answers.pop(0) if self.answers else "topics"
        if kind == "timeout":
            raise AITurnTimeout("The model took too long.")
        return no_topic(context) if kind == "none" else _default_payload(context)


def _services(script: Script):
    return fake_services(synthesis_client_factory=lambda ctx=None: FakeBookSynthesisClient(builder=script.answer))


def _ctx(root, services):
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=services)
    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    return ctx


def _drain(ctx, max_jobs=1):
    return ctx.ingest_jobs._require_runner().drain(max_jobs=max_jobs)


def _jobs(ctx):
    return [job for batch in ctx.repository.list_ingest_batches() for job in ctx.repository.ingest_jobs_for_batch(batch["id"])]


def _book(tmp_path, script: Script):
    """The house book added through Add, its whole text in one build (as the walk's one-section chapter was)."""

    root = fresh_library(tmp_path, scope_cap=None)
    grant_consent(root)
    ctx = _ctx(root, _services(script))
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    return ctx, source_id


def _until_synthesis_is_next(ctx):
    for _ in range(10):
        if any(job["job_type"] == "inventory" and job["status"] == "completed" for job in _jobs(ctx)):
            assert [job["status"] for job in _jobs(ctx) if job["job_type"] == "bootstrap_synthesis"] == ["queued"]
            return
        assert _drain(ctx), "the queue ran dry before the build's inventory finished"
    pytest.fail("the build's inventory never finished")


def _finish(ctx, source_id, section_id):
    extraction_id = resolve_extraction_id(ctx.repository, source_id)
    return call(ctx, "reader.mark_section_progress",
                {"extractionId": extraction_id, "sectionId": section_id, "spansSeen": 3, "spanCount": 3,
                 "completed": True})


def _stamp(ctx, source_id, section_id):
    row = ctx.repository.reader_section_progress_row(resolve_extraction_id(ctx.repository, source_id), section_id)
    return (row or {}).get("generation_batch_id")


def _section_batches(ctx, section_id):
    return [
        batch for batch in ctx.repository.list_ingest_batches()
        if batch["workflow_type"] == "practice_expansion"
        and any((job.get("payload") or {}).get("reason") == f"reader_section_completed:{section_id}"
                for job in ctx.repository.ingest_jobs_for_batch(batch["id"]))
    ]


def _card(ctx, source_id):
    return next(card for card in call(ctx, "get_source_library", {})["sources"] if card["sourceId"] == source_id)


def _label(ctx, source_id, section_id):
    with ctx.repository.connection() as connection:
        row = connection.execute(
            "SELECT label FROM source_document_units WHERE extraction_id = ? AND unit_id = ?",
            (resolve_extraction_id(ctx.repository, source_id), section_id),
        ).fetchone()
    return str(row["label"])


def _synthesis_job(ctx, source_id):
    batch_id = core.latest_auto_outcome(ctx.repository, source_id)["build_batch_id"]
    return next(job for job in ctx.repository.ingest_jobs_for_batch(batch_id) if job["job_type"] == "bootstrap_synthesis")


# -- the rule, on the synthesis itself ----------------------------------------------------------------


def test_an_empty_first_answer_is_asked_again_once_fresh_and_the_second_is_taken(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    client = RecordingSynthesisClient(
        builder=lambda context, n: no_topic(context) if n == 1 else _default_payload(context),
    )

    result = create_study_map(root, "set_la", client=client, brief={"practice_items": "as_you_read"},
                              repository=repo, clock=_CLOCK)

    # The same request both times: the answer is sampled, so asking again is what may cure it.
    first, second = client.synthesis_requests
    assert first == second
    fields = {**asdict(first), "result_model": first.result_model.model_json_schema()}
    assert sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest() == (
        "2f9ebc40ad099f46b608d97e5a1ca328212f0f01cb4e26b947ce62408108a8c1"
    )
    assert repo.synthesis_run(result.synthesis_run_id)["actual_usage"]["calls"] == 1
    assert result.item_counts.get("learning_object") == 1 and result.item_counts.get("task_blueprint") == 1
    assert [d["gate"] for d in result.gate_diagnostics if d["gate"] == ASKED_AGAIN] == [ASKED_AGAIN]
    with repo.connection() as connection:
        kept = [row[0] for row in connection.execute(
            "SELECT result_json FROM model_work_checkpoints WHERE purpose = 'synthesis_pass'")]
    # The empty answer was dropped before the second request, so only the answer with topics is kept.
    assert len(kept) == 1 and "lo_diagonalize_symmetric" in kept[0]


def test_two_empty_answers_take_the_second_and_ask_no_third(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    client = RecordingSynthesisClient(
        builder=lambda context, n: no_topic(context).model_copy(update={"summary": f"Empty answer {n}"}),
    )

    result = create_study_map(root, "set_la", client=client, brief={"practice_items": "as_you_read"},
                              repository=repo, clock=_CLOCK)

    first, second = client.synthesis_requests
    assert first == second
    assert repo.synthesis_run(result.synthesis_run_id)["status"] == "completed"
    assert repo.proposal_batch(result.proposal_id)["summary"] == "Empty answer 2"
    assert "learning_object" not in result.item_counts and result.item_counts.get("concept")
    # Asked again later (the subject still has no topic): the kept empty answer is replayed at no cost, judged empty
    # again and dropped, and one fresh request is made.
    again = create_study_map(root, "set_la", client=client, brief={"practice_items": "as_you_read"},
                             repository=repo, clock=_CLOCK)
    assert len(client.calls) == 3
    assert "learning_object" not in again.item_counts


@pytest.mark.parametrize("empty_first", [True, False], ids=["empty_then_rejected_match", "rejected_match_then_empty"])
def test_empty_topic_and_rejected_match_share_the_same_two_passes(tmp_path, empty_first):
    root, repo = _setup(tmp_path, with_exam=False)
    options = {"brief": {"practice_items": "as_you_read"}, "repository": repo, "clock": _CLOCK}
    original = create_study_map(root, "set_la", client=FakeSynthesisClient(), **options)
    reject_items(root, original.proposal_id)

    # In the second case the rejected proposal's paid checkpoint supplies the first answer.
    # In the first case remove that answer to send a wire-empty first pass, then return the rejected rows.
    if empty_first:
        with repo.connection() as connection:
            (key,) = connection.execute(
                "SELECT cache_key FROM model_work_checkpoints WHERE purpose = 'synthesis_pass'"
            ).fetchone()
        repo.discard_synthesis_shard_result(key)
        repo.discard_model_checkpoint(key)
    client = RecordingSynthesisClient(
        builder=lambda context, n: _default_payload(context) if n == 2 else no_topic(context),
    )

    result = create_study_map(root, "set_la", client=client, **options)

    assert result.proposal_id != original.proposal_id and not result.reused
    assert {row["decision"] for row in repo.proposal_items(original.proposal_id)} == {"rejected"}
    assert len(client.synthesis_requests) == (2 if empty_first else 1)
    assert bool(result.item_counts.get("learning_object")) is empty_first
    assert any(d["gate"] == ASKED_AGAIN for d in result.gate_diagnostics) is empty_first


@pytest.mark.parametrize("first_pass_owes_retry", [True, False], ids=["all_shards_empty", "one_shard_has_a_topic"])
def test_empty_topic_check_uses_the_aggregate_and_discards_every_shard_on_retry(tmp_path, first_pass_owes_retry):
    root, repo = _setup_two_chapters(tmp_path)

    def build(context, n):
        return _default_payload(context) if n == (4 if first_pass_owes_retry else 2) else no_topic(context)

    client = RecordingSynthesisClient(builder=build)
    result = create_study_map(root, "set_la", client=client, brief={"practice_items": "as_you_read"},
                              budget_overrides={"synthesis_shard_input_tokens": 1}, repository=repo, clock=_CLOCK)

    assert [context.shard_ordinal for context in client.calls] == [0, 1] * (2 if first_pass_owes_retry else 1)
    if first_pass_owes_retry:
        assert client.synthesis_requests[:2] == client.synthesis_requests[2:]
    assert result.item_counts.get("learning_object") == 1
    assert any(d["gate"] == ASKED_AGAIN for d in result.gate_diagnostics) is first_pass_owes_retry
    usage = repo.synthesis_run(result.synthesis_run_id)["actual_usage"]
    assert (usage["calls"], usage["shard_count"], usage["reused_shards"]) == (2, 2, 0)


def test_a_narrow_adjunct_bootstrap_may_add_no_topic_with_one_request(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient(builder=lambda context, n: no_topic(context))

    result = create_study_map(root, "set_la", client=client, brief={"authoring_preset": "narrow_adjunct"},
                              repository=repo, clock=_CLOCK)

    assert len(client.calls) == 1
    assert "learning_object" not in result.item_counts
    assert not [d for d in result.gate_diagnostics if d["gate"] == ASKED_AGAIN]


def test_a_bootstrap_over_a_subject_that_has_topics_may_add_none_with_one_request(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    first = FakeSynthesisClient()
    create_study_map(root, "set_la", client=first, brief={"practice_items": "as_you_read"}, apply=True,
                     repository=repo, clock=_CLOCK)
    rerun = FakeSynthesisClient(builder=lambda context, n: no_topic(context))

    create_study_map(root, "set_la", client=rerun, mode="bootstrap", brief={"practice_items": "as_you_read"},
                     repository=repo, clock=_CLOCK)

    assert len(rerun.calls) == 1


def test_which_runs_owe_a_topic_and_which_answers_hold_one():
    from types import SimpleNamespace

    from learnloop.content.synthesis.ai_contracts import SourceSetSynthesis
    from learnloop.content.synthesis.source_set_synthesis import bootstrap_owes_a_topic, holds_a_topic

    teaching = [{"semantic_authority": True}]
    vault = SimpleNamespace(learning_objects={})
    assert bootstrap_owes_a_topic(vault, "s", {"practice_items": "as_you_read"}, teaching)
    assert not bootstrap_owes_a_topic(vault, "s", {"authoring_preset": "narrow_adjunct"}, teaching)
    assert not bootstrap_owes_a_topic(vault, "s", {}, [{"semantic_authority": False}])  # problem sets, notes only
    assert not bootstrap_owes_a_topic(vault, "s", {}, [])  # nothing to read: no request is made
    mapped = SimpleNamespace(learning_objects={"lo": SimpleNamespace(subjects=["s"])})
    assert not bootstrap_owes_a_topic(mapped, "s", {}, teaching)  # a rerun over the subject's map
    other = SimpleNamespace(learning_objects={"lo": SimpleNamespace(subjects=["t"])})
    assert bootstrap_owes_a_topic(other, "s", {}, teaching)  # another subject's topics are not this one's

    context = SimpleNamespace(unit_inventories=[], exam_profile=None)
    good = _default_payload(context)
    assert holds_a_topic(good)
    assert not holds_a_topic(SourceSetSynthesis())
    assert not holds_a_topic(good.model_copy(update={"blueprints": []}))  # a topic with no question plan
    assert not holds_a_topic(good.model_copy(update={"learning_objects": []}))  # a plan for no topic of this answer
    by_id = good.model_copy(update={"blueprints": [good.blueprints[0].model_copy(
        update={"learning_object_client_id": "", "learning_object_id": good.learning_objects[0].id})]})
    assert holds_a_topic(by_id)


# -- the book: an empty answer, then one with topics ----------------------------------------------


def test_an_empty_first_build_asked_again_completes_with_topics_and_writes_the_finished_sections_questions(tmp_path):
    script = Script("none")
    ctx, source_id = _book(tmp_path, script)
    _until_synthesis_is_next(ctx)
    _finish(ctx, source_id, CITED)

    _drain(ctx)  # the build's synthesis: asked twice

    assert script.asked == 2
    job = _synthesis_job(ctx, source_id)
    assert job["status"] == "completed"
    assert job["result"]["item_counts"].get("learning_object")
    assert len(_section_batches(ctx, CITED)) == 1
    line = _card(ctx, source_id)["statusLine"]
    assert "noTopics" not in line
    assert line["questions"]["writing"] == [_label(ctx, source_id, CITED)]


# -- still empty: said, not hidden ---------------------------------------------------------------


def test_two_empty_answers_end_the_build_saying_so_and_nothing_is_settled_silently(tmp_path):
    script = Script("none", "none")
    ctx, source_id = _book(tmp_path, script)
    _until_synthesis_is_next(ctx)
    _finish(ctx, source_id, CITED)

    _drain(ctx, max_jobs=None)  # everything: the build, and anything it would queue after

    assert script.asked == 2  # one answer, asked again once; an empty answer is not a failure, so no job retry
    assert _synthesis_job(ctx, source_id)["status"] == "completed"
    line = _card(ctx, source_id)["statusLine"]
    assert line["noTopics"] is True
    assert line["tone"] == "problem"
    assert line["text"] == "LearnLoop found no topics to practise in this book"
    assert line["action"] == {"kind": "retry", "label": "Try again"}
    assert line["details"]
    # The finished section is settled as needing nothing to write, and the fact says so.
    assert _stamp(ctx, source_id, CITED) == "none_needed_after_build"
    assert line["questions"]["noneNeeded"] == [_label(ctx, source_id, CITED)]
    assert line["questions"]["count"] == 0
    assert _section_batches(ctx, CITED) == []
    # "Build questions for the whole book at once" says the same truth.
    pressed = call(ctx, "source_action", {"sourceId": source_id, "action": "build_whole_book"})
    assert pressed["notice"] == (
        "LearnLoop found no topics to practise in this book, so there are no questions to write from it yet. "
        "Try again on its card to look once more."
    )
    assert "written when you finish" not in pressed["notice"]
    assert _drain(ctx, max_jobs=None) == 0
    assert script.asked == 2


def test_the_request_bound_with_the_jobs_own_retry(tmp_path):
    """Empty, then the re-ask fails in a way a fresh try may cure: the job tries once more on its own, and that
    try asks at most twice too. Four requests at most, then the build ends saying no topic was found."""

    script = Script("none", "timeout", "none", "none")
    ctx, source_id = _book(tmp_path, script)

    _drain(ctx, max_jobs=None)

    assert script.asked == 4
    assert _synthesis_job(ctx, source_id)["status"] == "completed"
    assert _card(ctx, source_id)["statusLine"]["noTopics"] is True
    assert _drain(ctx, max_jobs=None) == 0
    assert script.asked == 4


def test_a_section_finished_after_the_empty_build_is_said_too(tmp_path):
    script = Script("none", "none")
    ctx, source_id = _book(tmp_path, script)
    _drain(ctx, max_jobs=None)
    _card(ctx, source_id)

    done = _finish(ctx, source_id, CITED)

    assert done["enqueuedGeneration"] is False
    assert _stamp(ctx, source_id, CITED) == "none_needed_after_build"
    assert _card(ctx, source_id)["statusLine"]["questions"]["noneNeeded"] == [_label(ctx, source_id, CITED)]


# -- a later build pays what is owed ----------------------------------------------------------------


def test_try_again_after_an_empty_build_writes_the_owed_sections_questions(tmp_path):
    script = Script("none", "none")
    ctx, source_id = _book(tmp_path, script)
    _until_synthesis_is_next(ctx)
    _finish(ctx, source_id, CITED)
    _drain(ctx, max_jobs=None)
    _card(ctx, source_id)
    assert _stamp(ctx, source_id, CITED) == "none_needed_after_build"
    empty_build = core.latest_auto_outcome(ctx.repository, source_id)["build_batch_id"]

    pressed = call(ctx, "source_action", {"sourceId": source_id, "action": "retry"})
    _drain(ctx, max_jobs=None)  # the new plan and its build: this time the answer has topics

    assert pressed["batchId"]
    outcome = core.latest_auto_outcome(ctx.repository, source_id)
    assert outcome["build_batch_id"] != empty_build
    assert script.asked == 3  # one request: topics on the first answer
    assert _synthesis_job(ctx, source_id)["result"]["item_counts"].get("learning_object")
    batches = _section_batches(ctx, CITED)
    assert len(batches) == 1
    # The section's work is its topics' claims, each naming that batch.
    assert _stamp(ctx, source_id, CITED) == "topic_managed"
    claims = ctx.repository.topic_question_work_rows(owner="topic")
    assert claims and {(row["batch_id"], row["section_id"]) for row in claims} == {(batches[0]["id"], CITED)}
    line = _card(ctx, source_id)["statusLine"]
    assert "noTopics" not in line
    # Read again, everywhere: never a second writing.
    _card(ctx, source_id)
    call(ctx, "reader.get_progress", {"extractionId": resolve_extraction_id(ctx.repository, source_id)})
    assert len(_section_batches(ctx, CITED)) == 1


# -- what an empty answer is allowed to be ------------------------------------------------------------


def test_a_later_chapters_append_that_adds_no_topic_stays_accepted_with_one_request(tmp_path):
    """The book's second build is an append into the map its first build made: links to the topics already there
    are a legitimate answer, with no topic of its own, and are not asked again."""

    script = Script()
    root = fresh_library(tmp_path)  # the house book in parts: the first build covers chapters 1-2
    grant_consent(root)
    appends: list[FakeBookSynthesisClient] = []

    def synthesis(ctx=None):
        client = FakeBookSynthesisClient(builder=script.answer)
        appends.append(client)
        return client

    ctx = _ctx(root, fake_services(synthesis_client_factory=synthesis))
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    _drain(ctx, max_jobs=None)
    assert script.asked == 1

    call(ctx, "source_action", {"sourceId": source_id, "action": "build_whole_book"})
    _drain(ctx, max_jobs=None)

    append_calls = sum(len(client.append.calls) for client in appends)
    assert append_calls == 1
    assert script.asked == 1
    line = _card(ctx, source_id)["statusLine"]
    assert "noTopics" not in line
    assert line["tone"] == "quiet"
