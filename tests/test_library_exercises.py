"""Reader workbench RW4b: exercises from my sources (spec_reader_workbench_v1 §7.4; G19, G34, G53).

* **The view** (``reader.exercise_candidates``): the textbook exercises a
  ``find_practice`` proposal offered the Reader, each with the sources
  service's exposure rule read as the Reader shows it. An exposed candidate
  carries the reason's label and is offered as practice, never as a check on
  your own; a key the proposal did not propose is refused; exam and held-out
  material is never shown, however old the proposal (the held-out sentinel).
* **"Use this one"** (``workbench.open`` with ``sourceExercise``): the
  workbench opens at once on the verbatim statement while the sources
  service's own import runs (S1: the import row, the pick's usage verdict,
  the job); it binds only once the import WROTE the item (running, admitted,
  refused); a refusal is shown with its reason, nothing is bound, and "try
  again" re-queues the same import. Once bound the item is a learner pick
  through the plan's existing pick path (the proposal and import ids).
* **The fallback** (``reader.find_exercises``): ``find_sources`` under the
  Reader's caller (``reading``, derived on the server), exercise regions of
  the teaching scope only (never worked examples, solutions or the exam);
  "use this one" runs the Reader's existing ``import_exercises`` unchanged
  (G34). Off by default: the spec retires it once S1 is live.
* **Switch-off pins**: with ``library_exercises.enabled`` off, the prompt
  contract has no ``library_exercises`` key, every RW4b RPC refuses and
  ``find_practice``'s Reader answer is what it was.
* **G53**: the sources service absent (the view is absent) and faked (the
  fallback's call is the documented one); no RW4b module defines a second
  ``find_sources``, ``find_practice``, exposure rule or import.

Fakes only; no network.
"""
from __future__ import annotations

import ast
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest

from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.instructional.exercises import exercise_candidates
from learnloop.instructional.interventions import record_shown_spans
from learnloop.practice_index.retrieval import find_practice
from learnloop.practice_index.usage import USAGE_TASK
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers import workbench as workbench_handler
from tests.library_ask_fixtures import build_library_vault, context, finish_job, set_config, table_counts
from tests.recap_fixtures import call as call_rpc
from tests.source_service_fakes import LEARNING_STATE_TABLES, FakeServiceLLM

ROOT = Path(__file__).resolve().parents[1]
QUERY = "solve for the eigenvalue x"
#: The solutions' own words (exercise 1's and 2's): never in what the Reader is sent.
SOLUTION_TEXT = ("so the eigenvalue is x = 5", "so the eigenvalue is x = 3", "Subtracting")


#: RW4b's two RPCs answer with a library job (never on the request path).
JOB_RPCS = frozenset({"reader.exercise_candidates", "reader.find_exercises"})


def call(ctx, name: str, params: dict[str, Any]) -> dict[str, Any]:
    """An RPC as the Reader sees it: RW4b's job RPCs are read until done."""

    result = call_rpc(ctx, name, params)
    if name in JOB_RPCS:
        assert set(result) >= {"jobId", "state"}, result  # never answered on the request path
        return finish_job(ctx, result)
    return result


@pytest.fixture
def library(tmp_path):
    paths, repository, spans = build_library_vault(tmp_path / "vault")
    return paths, repository, spans


def _proposal(paths, repository, *, caller_ref: str = "ext_text") -> dict[str, Any]:
    """What the Reader's "practice this question" gets back: find_practice with
    the arm injected and the mixed rerank faked (as the S1 tests do)."""

    return find_practice(load_vault(paths.root), repository, QUERY, {"learning_object_ids": ["lo_matrices"]},
                         exercise_arm=exercise_candidates, rerank_client=FakeServiceLLM(),
                         caller={"kind": "reader", "ref": caller_ref})


def _keys(proposal: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"extractionId": e["extraction_id"], "spanIds": e["span_ids"]} for e in proposal["source_exercises"]]


def _view(ctx, proposal: dict[str, Any]) -> dict[str, Any]:
    return call(ctx, "reader.exercise_candidates", {"proposalId": proposal["proposal_id"], "keys": _keys(proposal)})


def _all_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_all_text(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return " ".join(_all_text(v) for v in value)
    return str(value)


# -- config, contract and the switch-off pins -------------------------------------------------------


def test_the_view_is_on_and_the_fallback_off_by_default_the_specs_rule_once_s1_is_live(library):
    paths, _repository, _spans = library
    vault = load_vault(paths.root)
    assert vault.config.library_exercises.enabled is True
    # §7.4: "the fallback is retired when the sources spec's candidates are live
    # (its switch, library_exercises.fallback_enabled, then defaults off)".
    assert vault.config.source_service.exercise_arm is True
    assert vault.config.library_exercises.fallback_enabled is False
    contract = call(context(paths.root), "reader.prompt_contract", {})
    assert contract["libraryExercises"] == {"fallback": False}
    set_config(paths, "library_exercises", fallback_enabled=True)
    assert call(context(paths.root), "reader.prompt_contract", {})["libraryExercises"] == {"fallback": True}


def test_switched_off_the_contract_rpcs_and_practice_answer_are_as_before(library):
    paths, repository, _spans = library
    on = call(context(paths.root), "reader.prompt_contract", {})
    proposal = _proposal(paths, repository)
    with_view = call(context(paths.root), "find_practice", {"query": QUERY, "learningObjectIds": ["lo_matrices"],
                                                            "caller": {"kind": "reader", "ref": "ext_text"}})
    set_config(paths, "library_exercises", enabled=False, fallback_enabled=True)
    ctx = context(paths.root)
    off = call(ctx, "reader.prompt_contract", {})
    assert "libraryExercises" not in off
    assert {key: value for key, value in on.items() if key != "libraryExercises"} == off
    for name, params in (
        ("reader.exercise_candidates", {"proposalId": proposal["proposal_id"], "keys": _keys(proposal)}),
        ("reader.find_exercises", {"query": QUERY, "learningObjectIds": ["lo_matrices"]}),
    ):
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, params)
        assert caught.value.code == "library_exercises_disabled"
    exercise = proposal["source_exercises"][0]
    with pytest.raises(SidecarError) as caught:
        call(ctx, "workbench.open", {"origin": "reader", "entry": "practice_this", "stemMd": exercise["statement"],
                                     "extractionId": "ext_text", "spanIds": exercise["span_ids"],
                                     "sourceExercise": {"proposalId": proposal["proposal_id"],
                                                        "extractionId": "ext_text",
                                                        "spanIds": exercise["span_ids"]}})
    assert caught.value.code == "library_exercises_disabled"
    # find_practice's Reader answer is RW4b's input, never changed by it.
    again = call(ctx, "find_practice", {"query": QUERY, "learningObjectIds": ["lo_matrices"],
                                        "caller": {"kind": "reader", "ref": "ext_text"}})
    # What the Reader renders from it (the receipt's timings and signals aside).
    shown = lambda result: (result["status"], result["items"], result.get("sourceExercises"))  # noqa: E731
    assert shown(again) == shown(with_view)


def test_the_new_rpcs_take_no_policy_and_the_workbench_view_of_other_problems_is_unchanged(library):
    from learnloop_sidecar.handlers import library_exercises as handler

    for model in (handler.ExerciseCandidatesInput, handler.FindExercisesInput):
        assert "policy" not in model.model_fields
    paths, _repository, _spans = library
    ctx = context(paths.root)
    session = call(ctx, "workbench.open", {"origin": "reader", "entry": "work_through", "stemMd": "Solve it",
                                           "practiceItemId": "pi_eigen_1", "extractionId": "ext_text",
                                           "spanIds": ["t6"]})["session"]
    assert "sourceExercise" not in session


# -- the view: exposure, never as a check on your own, held-out material -----------------------------


def test_fresh_candidates_are_offered_as_a_check_on_your_own_with_their_verbatim_statement_only(library):
    paths, repository, spans = library
    proposal = _proposal(paths, repository)
    assert proposal["source_exercises"], proposal.get("source_exercises_status")
    for exercise in proposal["source_exercises"]:
        assert set(exercise["span_ids"]) <= set(spans["exercises"])  # never a worked example or a solution
        assert not any(text in exercise["statement"] for text in SOLUTION_TEXT)
    before = table_counts(repository, LEARNING_STATE_TABLES)
    view = _view(context(paths.root), proposal)
    assert view["withheld"] == 0 and len(view["candidates"]) == len(proposal["source_exercises"])
    for candidate in view["candidates"]:
        assert candidate["exposure"]["exposed"] is False and candidate["exposure"]["label"] is None
        assert candidate["exposure"]["offeredAs"] == "check_on_your_own"
        assert candidate["exposure"]["exposureRuleVersion"] == "reading_exposure_v1"
    assert not any(text in _all_text(view) for text in SOLUTION_TEXT)
    assert table_counts(repository, LEARNING_STATE_TABLES) == before  # display: nothing learned, nothing served


def test_a_seen_page_or_solution_is_labelled_and_offered_as_practice_never_as_a_check(library):
    paths, repository, spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    record_shown_spans(repository, [f"ext_text:{exercise['span_ids'][0]}"], context="library",
                       entity_type="test", entity_id="read")
    view = _view(context(paths.root), proposal)
    seen = next(c for c in view["candidates"] if c["key"] == exercise["key"])
    assert seen["exposure"]["exposed"] is True and "source_exposed" in seen["exposure"]["reasons"]
    assert seen["exposure"]["label"] == "you've recently seen this page or its solution"
    assert seen["exposure"]["offeredAs"] == "practice"


def test_an_earlier_suggestion_counts_and_this_proposals_own_impression_does_not(library):
    paths, repository, _spans = library
    first = _proposal(paths, repository)
    exercise = first["source_exercises"][0]
    ctx = context(paths.root)
    keys = [{"kind": "source_exercise", "extractionId": exercise["extraction_id"], "spanIds": exercise["span_ids"]}]
    call(ctx, "record_proposal_impressions", {"proposalId": first["proposal_id"], "surface": "reader", "keys": keys})
    own = next(c for c in _view(ctx, first)["candidates"] if c["key"] == exercise["key"])
    assert own["exposure"]["exposed"] is False  # the impression the pick comes from never counts against it
    second = _proposal(paths, repository)
    later = next(c for c in _view(ctx, second)["candidates"] if c["key"] == exercise["key"])
    assert later["exposure"]["reasons"] == ["seen_in_proposal"]
    assert later["exposure"]["offeredAs"] == "practice"


def test_a_key_the_proposal_did_not_propose_is_refused(library):
    paths, repository, spans = library
    proposal = _proposal(paths, repository)
    with pytest.raises(SidecarError) as caught:
        call(context(paths.root), "reader.exercise_candidates", {
            "proposalId": proposal["proposal_id"], "keys": [{"extractionId": "ext_text", "spanIds": spans["solutions"][1:2]}]})
    assert caught.value.code == "validation_error"


def test_the_held_out_sentinel_is_never_offered_by_the_view_the_arm_or_the_fallback(library):
    paths, repository, spans = library
    set_config(paths, "library_exercises", fallback_enabled=True)
    proposal = _proposal(paths, repository)
    assert proposal["source_exercises"]
    # The book's exercises are held out for evaluation AFTER they were proposed.
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    ctx = context(paths.root)
    view = _view(ctx, proposal)
    assert view["candidates"] == [] and view["withheld"] == len(proposal["source_exercises"])
    sentinel = "An eigenvalue t satisfies 3t + 5 = 20"
    # A fresh proposal and the fallback never even find them.
    fresh = _proposal(paths, repository)
    assert all(sentinel not in exercise["statement"] for exercise in fresh["source_exercises"])
    found = call(ctx, "reader.find_exercises", {"query": QUERY, "learningObjectIds": ["lo_matrices"],
                                                "extractionId": "ext_text"})
    assert sentinel not in _all_text(found["candidates"])
    assert not {span for c in found["candidates"] for span in c["spanIds"]} & set(spans["exercises"])


# -- "use this one": the sources service's import, inside the workbench -------------------------------


@pytest.fixture
def imports(monkeypatch):
    """The S1 job behind the workbench: the real enqueue helper and handler
    code, the job queue faked. ``jobs[batch]`` is what the queue reports."""

    state: dict[str, Any] = {"queued": [], "jobs": {}}

    def enqueue(self, **kwargs):
        batch = f"batch_{len(state['queued']) + 1}"
        state["queued"].append(dict(kwargs))
        state["jobs"][batch] = {"id": f"job_{batch}", "status": "running", "payload": dict(kwargs),
                                "result": None, "error": None}
        return batch

    monkeypatch.setattr(DurableIngestJobs, "enqueue_source_exercise_import", enqueue)
    monkeypatch.setattr(DurableIngestJobs, "needs_reload", lambda self, job_id: False)
    monkeypatch.setattr(Repository, "ingest_jobs_for_batch",
                        lambda self, batch_id: [state["jobs"][batch_id]] if batch_id in state["jobs"] else [])
    return state


def _run_job(paths, repository, queued: dict[str, Any], llm: Any) -> dict[str, Any]:
    """Run the S1 import job itself, synchronously, with the fake service LLM."""

    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import IngestRunnerError, JobContext, RunnerServices

    ctx = JobContext(repo=repository, vault_root=paths.root,
                     job={"id": "job_1", "attempt_count": 1, "payload": {**queued, "caller": "learner"}},
                     clock=None, worker_id="w",
                     services=RunnerServices(exercise_import_client_factory=lambda ctx: llm,
                                             background_key_checks=False))
    ctx.report = lambda *args, **kwargs: None  # type: ignore[method-assign]
    try:
        return {"status": "completed", "result": jobs.handle_source_exercise_import(ctx), "error": None}
    except IngestRunnerError as exc:
        return {"status": "failed", "result": None, "error": {"message": str(exc), "code": exc.code}}


def _use_this_one(ctx, proposal: dict[str, Any], exercise: dict[str, Any], *, entry: str = "practice_this"):
    return call(ctx, "workbench.open", {
        "origin": "reader", "entry": entry, "stemMd": exercise["statement"], "extractionId": exercise["extraction_id"],
        "spanIds": exercise["span_ids"], "clientIdempotencyKey": f"use-{exercise['key']}",
        "sourceExercise": {"proposalId": proposal["proposal_id"], "extractionId": exercise["extraction_id"],
                           "spanIds": exercise["span_ids"]}})["session"]


def _item_count(paths) -> int:
    return len(load_vault(paths.root).practice_items)


def test_use_this_one_opens_at_once_on_the_verbatim_stem_while_the_import_runs(library, imports):
    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    items_before = _item_count(paths)
    session = _use_this_one(ctx, proposal, exercise)
    assert session["stemMd"] == exercise["statement"] and session["importStatus"] == "pending"
    assert session["sourceVisible"] is False  # an unexposed exercise: your own attempt, the book hidden
    [queued] = imports["queued"]
    assert (queued["proposal_id"], queued["extraction_id"], queued["span_ids"]) == (
        proposal["proposal_id"], exercise["extraction_id"], exercise["span_ids"])
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = connection.execute("SELECT caller, status, proposal_id FROM source_exercise_imports").fetchone()
        pick = connection.execute("SELECT right_kind, right_id, verdict FROM judgment_ledger WHERE task=?",
                                  (USAGE_TASK,)).fetchone()
    assert tuple(row) == ("learner", "authoring", proposal["proposal_id"])
    assert tuple(pick) == ("source_exercise", exercise["key"], "practised")
    assert session["sourceExercise"]["importId"] == queued["import_id"]
    assert session["sourceExercise"]["importStatus"] == "authoring"
    # Running: the steps are the learner's, nothing is bound, nothing exists to serve.
    call(ctx, "workbench.save_step", {"sessionId": session["sessionId"], "clientIdempotencyKey": "k1",
                                      "op": "add", "bodyMd": "3x = 15"})
    running = call(ctx, "workbench.refresh_import", {"sessionId": session["sessionId"]})["session"]
    assert running["importStatus"] == "pending" and running["practiceItemId"] is None and running["steps"]
    assert _item_count(paths) == items_before
    # The same pick twice resumes the one problem; no second import.
    again = _use_this_one(ctx, proposal, exercise)
    assert again["sessionId"] == session["sessionId"] and len(imports["queued"]) == 1


def test_admitted_the_problem_binds_to_the_written_item_and_becomes_a_learner_pick(library, imports, monkeypatch):
    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    session = _use_this_one(ctx, proposal, exercise)
    batch = next(iter(imports["jobs"]))
    imports["jobs"][batch].update(_run_job(paths, repository, imports["queued"][0], FakeServiceLLM()))
    ctx.reload(maintenance=False)
    bound = call(ctx, "workbench.refresh_import", {"sessionId": session["sessionId"]})["session"]
    assert bound["importStatus"] == "bound" and bound["practiceItemId"]
    item = load_vault(paths.root).practice_items[bound["practiceItemId"]]
    assert item.canonical_exercise is not None and item.canonical_exercise.relation == "verbatim"
    assert list(item.canonical_exercise.span_ids) == exercise["span_ids"]
    # The key's honest status, as the sources service labels it.
    source = bound["sourceExercise"]
    assert source["importStatus"] == "written" and source["keyStatus"] and source["keyLabel"]
    # The pick (fix round 4, R1): the server's one admission, for this problem
    # by its id: the plan's own learner pick with the proposal and the import,
    # served, its serve kept on THIS problem, the book choice kept.
    picks = _spy_picks(monkeypatch)
    admitted = call(ctx, "workbench.admit", {"sessionId": session["sessionId"]})
    assert admitted["session"]["sessionId"] == session["sessionId"]
    assert admitted["session"]["exercisePick"]["admitted"] is True and admitted["session"]["sourceVisible"] is False
    [picked] = picks
    assert (picked.practice_item_id, picked.proposal_id, picked.source_exercise_import_id) == (
        bound["practiceItemId"], proposal["proposal_id"], source["importId"])
    assert admitted["practiceSession"]["sessionId"] == picked.session_id


def test_a_refused_import_is_shown_with_its_reason_binds_nothing_and_tries_the_same_import_again(library, imports):
    paths, repository, _spans = library
    # The owner's switches: only verified keys are written, and nothing verifies here.
    set_config(paths, "source_service", unverified_imports=False, exercise_verification=False)
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    items_before = _item_count(paths)
    session = _use_this_one(ctx, proposal, exercise)
    batch = next(iter(imports["jobs"]))
    imports["jobs"][batch].update(_run_job(paths, repository, imports["queued"][0], FakeServiceLLM()))
    assert imports["jobs"][batch]["status"] == "failed"
    failed = call(ctx, "workbench.refresh_import", {"sessionId": session["sessionId"]})["session"]
    assert failed["importStatus"] == "failed" and failed["practiceItemId"] is None
    assert failed["importError"] == "LearnLoop couldn't check this answer key yet"
    assert failed["sourceExercise"]["importStatus"] == "rejected"
    assert _item_count(paths) == items_before  # nothing half-imported exists to serve
    retried = call(ctx, "workbench.retry_import", {"sessionId": session["sessionId"]})["session"]
    assert retried["importStatus"] == "pending" and len(imports["queued"]) == 2
    first, second = imports["queued"]
    assert (second["proposal_id"], second["span_ids"]) == (first["proposal_id"], first["span_ids"])
    assert second["import_id"] != first["import_id"]


def test_a_problem_imports_one_way_and_an_unproposed_exercise_never_opens(library, imports):
    paths, repository, spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "workbench.open", {
            "origin": "reader", "entry": "practice_this", "stemMd": "x", "extractionId": "ext_text",
            "spanIds": exercise["span_ids"], "importRequest": {"extractionId": "ext_text", "rawSelection": {}},
            "sourceExercise": {"proposalId": proposal["proposal_id"], "extractionId": "ext_text",
                               "spanIds": exercise["span_ids"]}})
    assert caught.value.code == "validation_error"
    opened = call(ctx, "workbench.open", {
        "origin": "reader", "entry": "practice_this", "stemMd": "The book's solution", "extractionId": "ext_text",
        "spanIds": spans["solutions"][1:2],
        "sourceExercise": {"proposalId": proposal["proposal_id"], "extractionId": "ext_text",
                           "spanIds": spans["solutions"][1:2]}})["session"]
    assert opened["importStatus"] == "failed" and imports["queued"] == []
    assert "not proposed" in opened["importError"]


# -- the fallback --------------------------------------------------------------------------------------


def test_the_fallback_finds_exercise_regions_of_the_teaching_scope_only_and_records_what_it_showed(library):
    paths, repository, spans = library
    set_config(paths, "library_exercises", fallback_enabled=True)
    ctx = context(paths.root)
    found = call(ctx, "reader.find_exercises", {"query": QUERY, "learningObjectIds": ["lo_matrices"],
                                                "extractionId": "ext_text"})
    assert found["status"] == "ok" and found["policy"] == "reading"
    assert found["manifest"]["policy"] == "reading"
    shown_spans = [span for candidate in found["candidates"] for span in candidate["spanIds"]]
    assert shown_spans and set(shown_spans) <= set(spans["exercises"])  # never worked examples or solutions
    for candidate in found["candidates"]:
        assert candidate["extractionId"] == "ext_text" and candidate["sourceTitle"] == "Matrix Theory"
        assert candidate["exposure"]["exposed"] is False  # what it was before this list showed it
        request = candidate["importRequest"]
        assert request["extractionId"] == "ext_text" and request["sourceId"] == "src_text"
        assert [node["spanId"] for node in request["rawSelection"]["nodes"]] == candidate["spanIds"]
        assert all(node["start"] == 0 for node in request["rawSelection"]["nodes"])
    assert not any(text in _all_text(found["candidates"]) for text in SOLUTION_TEXT)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        recorded = {row[0] for row in connection.execute(
            "SELECT span_id FROM source_exposure_events WHERE entity_type='library_exercises'")}
    assert recorded == set(shown_spans)
    # Shown once, it is no longer unseen: the next list says so, and offers it as practice.
    again = call(ctx, "reader.find_exercises", {"query": QUERY, "learningObjectIds": ["lo_matrices"],
                                                "extractionId": "ext_text"})
    assert all(c["exposure"]["offeredAs"] == "practice" for c in again["candidates"])


def test_the_fallback_is_learner_initiated_and_switched_off_by_default(library):
    paths, _repository, _spans = library
    with pytest.raises(SidecarError) as caught:
        call(context(paths.root), "reader.find_exercises", {"query": QUERY, "learningObjectIds": ["lo_matrices"]})
    assert caught.value.code == "library_exercises_disabled"


def test_use_this_one_on_a_fallback_exercise_runs_the_readers_import_unchanged(library, monkeypatch):
    """G34: before (or beside) S1's candidates, choosing one runs import_exercises unchanged."""

    import learnloop_sidecar.handlers.ai_providers as providers

    paths, _repository, _spans = library
    set_config(paths, "library_exercises", fallback_enabled=True)
    queued = []
    monkeypatch.setattr(DurableIngestJobs, "enqueue_reader_exercise_import",
                        lambda self, **kwargs: queued.append(kwargs) or "batch_reader")
    monkeypatch.setattr(providers, "ready_canonical_ingest_provider", lambda vault: ("fake", None, object()))
    ctx = context(paths.root)
    candidate = call(ctx, "reader.find_exercises", {"query": QUERY, "learningObjectIds": ["lo_matrices"],
                                                    "extractionId": "ext_text"})["candidates"][0]
    session = call(ctx, "workbench.open", {"origin": "reader", "entry": "practice_this",
                                           "stemMd": candidate["statement"], "extractionId": "ext_text",
                                           "spanIds": candidate["spanIds"],
                                           "importRequest": candidate["importRequest"]})["session"]
    assert session["importStatus"] == "pending" and "sourceExercise" not in session
    [kwargs] = queued
    assert kwargs["extraction_id"] == "ext_text" and kwargs["source_id"] == "src_text"
    # The crosswalk reads a node's span under either spelling (reader/annotations.py).
    assert [node.get("span_id") or node.get("spanId") for node in kwargs["raw_selection"]["nodes"]] == \
        candidate["spanIds"]


# -- G19 / G53 ------------------------------------------------------------------------------------------


def test_with_the_sources_service_faked_the_fallbacks_call_is_the_documented_one(library, monkeypatch):
    import learnloop.instructional.sources as service
    from learnloop.source_retrieval.find_sources import SourceHits

    paths, _repository, _spans = library
    set_config(paths, "library_exercises", fallback_enabled=True)
    calls = []

    def fake_propose_sources(vault, repository, query, *, caller, intent="explain", **kwargs):
        calls.append({"caller": caller, "intent": intent, **kwargs})
        hits = SourceHits(intent=intent, policy="reading")
        hits.manifest = {"policy": "reading", "query_hash": "q"}
        return hits

    monkeypatch.setattr(service, "propose_sources", fake_propose_sources)
    found = call(context(paths.root), "reader.find_exercises", {"query": QUERY, "learningObjectIds": ["lo_matrices"],
                                                                "extractionId": "ext_text"})
    assert found["status"] == "none_found" and found["candidates"] == []
    [made] = calls
    assert made["intent"] == "explain" and made["scope"] == "teaching" and made["roles"] == ["exercise"]
    assert made["learning_object_ids"] == ["lo_matrices"] and made["verify"] is False and "policy" not in made
    assert made["caller"].kind == "reader" and made["caller"].ref == "ext_text"


def test_with_the_sources_service_absent_the_view_is_absent(library):
    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    set_config(paths, "source_service", enabled=False)
    ctx = context(paths.root)
    assert "libraryExercises" not in call(ctx, "reader.prompt_contract", {})
    with pytest.raises(SidecarError) as caught:
        _view(ctx, proposal)
    assert caught.value.code == "library_exercises_disabled"


def _defined_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def test_rw4b_defines_no_second_service_function():
    """Built once (G53): the view composes the sources service; it never re-implements it."""

    owned = {"find_sources", "find_sources_for_caller", "compare_sources", "find_practice", "value_candidates",
             "propose_sources", "propose_comparison", "independent_check_eligibility", "exercise_candidates",
             "exercise_regions", "import_source_exercise", "import_exercises", "selection_for_region"}
    files = [ROOT / "src" / "learnloop_sidecar" / "handlers" / "library_exercises.py",
             ROOT / "src" / "learnloop_sidecar" / "handlers" / "workbench.py"]
    assert {path.name: _defined_names(path) & owned for path in files} == {path.name: set() for path in files}


# -- Codex review round 1: the pick's record, exposure at the pick, the complete stem -------------------


def _bind(paths, repository, ctx, imports, session: dict[str, Any]) -> dict[str, Any]:
    """The S1 job wrote the item; the problem binds to it."""

    batch = next(iter(imports["jobs"]))
    imports["jobs"][batch].update(_run_job(paths, repository, imports["queued"][0], FakeServiceLLM()))
    ctx.reload(maintenance=False)
    bound = call(ctx, "workbench.refresh_import", {"sessionId": session["sessionId"]})["session"]
    assert bound["importStatus"] == "bound" and bound["practiceItemId"]
    return bound


def _admit(ctx, session_id: str, **params: Any) -> dict[str, Any]:
    """The server's one admission of a picked exercise's learner pick (fix round 4, R1)."""

    return call(ctx, "workbench.admit", {"sessionId": session_id, **params})["session"]


def _spy_picks(monkeypatch) -> list[Any]:
    """Every learner pick the admission makes (the plan's own pick path)."""

    from learnloop_sidecar.handlers import daily_plan

    made: list[Any] = []
    real = daily_plan.plan_learner_pick

    def spy(ctx, params):
        made.append(params)
        return real(ctx, params)

    monkeypatch.setattr(daily_plan, "plan_learner_pick", spy)
    return made


def _admitted_events(repository, session_id: str) -> list[dict[str, Any]]:
    return [event for event in repository.reader_interaction_events(kind="reader_action_invoked")
            if event["payload"].get("event") == "workbench_exercise_admitted"
            and event["payload"].get("workbench_session_id") == session_id]


def test_the_learner_pick_is_owed_durably_across_a_restart_and_acknowledged_only_after_delivery(library, imports):
    """Codex review F2: admission lives on the problem, not in the visit that
    opened it. A restart (a fresh sidecar, nothing in memory), a resume or a
    second "use this one" on the bound problem all still owe the pick; a
    failed delivery leaves it owed; once delivered it is acknowledged once."""

    from learnloop.attempts import salience_firewall as SF

    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    session = _use_this_one(ctx, proposal, exercise)
    pick = session["exercisePick"]
    assert pick["proposalId"] == proposal["proposal_id"] and pick["due"] is False and pick["admitted"] is False
    assert pick["exposure"]["exposed"] is False and pick["exposureChecked"] == "selection"
    bound = _bind(paths, repository, ctx, imports, session)
    assert bound["exercisePick"]["due"] is True
    # A restart: nothing in memory, the pick is still owed, on every way back.
    restarted = context(paths.root)
    assert call(restarted, "workbench.get", {"sessionId": session["sessionId"]})["session"]["exercisePick"]["due"] is True
    resumed = call(restarted, "workbench.open", {"origin": "reader", "entry": "resume", "sessionId": session["sessionId"],
                                                 "extractionId": "ext_text"})["session"]
    assert resumed["exercisePick"]["due"] is True
    again = _use_this_one(restarted, proposal, exercise)  # "use this one" on the already-bound problem
    assert again["sessionId"] == session["sessionId"] and again["exercisePick"]["due"] is True
    # A failed admission acknowledges nothing: the pick stays owed, to retry.
    from learnloop_sidecar.handlers import daily_plan

    real_pick = daily_plan.plan_learner_pick

    def refused(ctx, params):
        raise SidecarError("validation_error", "refused")

    daily_plan.plan_learner_pick = refused
    try:
        with pytest.raises(SidecarError):
            _admit(restarted, session["sessionId"])
    finally:
        daily_plan.plan_learner_pick = real_pick
    assert call(restarted, "workbench.get", {"sessionId": session["sessionId"]})["session"]["exercisePick"]["due"] is True
    # Admitted: the server's one operation, for this problem.
    admitted = _admit(restarted, session["sessionId"])
    assert admitted["sessionId"] == session["sessionId"]
    assert admitted["exercisePick"]["admitted"] is True and admitted["exercisePick"]["due"] is False
    assert admitted["exercisePick"]["exposureChecked"] == "admission"
    # Once: a repeated admission and another restart owe nothing more.
    _admit(restarted, session["sessionId"])
    assert call(context(paths.root), "workbench.get", {"sessionId": session["sessionId"]})["session"]["exercisePick"]["due"] is False
    [event] = _admitted_events(repository, session["sessionId"])
    assert event["payload"]["authority_class"] == SF.SALIENCE_ONLY
    with pytest.raises(SF.SalienceEvidenceRejected):
        SF.reject_salience(event)


def test_admitting_needs_the_item_and_never_marks_another_problem(library, imports, monkeypatch):
    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    session = _use_this_one(ctx, proposal, exercise)
    picks = _spy_picks(monkeypatch)
    # Still running: nothing is owed yet, and nothing is picked or marked.
    pending = _admit(ctx, session["sessionId"])
    assert pending["exercisePick"]["admitted"] is False and picks == []
    # The open hand-off of PR rounds 1-3 is gone: an open never admits anything.
    with pytest.raises(Exception):
        call(ctx, "workbench.open", {"origin": "reader", "entry": "practice_this", "practiceItemId": "pi_eigen_1",
                                     "stemMd": "Solve it", "extractionId": "ext_text", "spanIds": ["t6"],
                                     "admittedSessionId": session["sessionId"]})
    bound = _bind(paths, repository, ctx, imports, session)
    # A problem that is no exercise admits nothing.
    plain = call(ctx, "workbench.open", {"origin": "reader", "entry": "work_through", "practiceItemId": "pi_eigen_1",
                                         "stemMd": "Solve it", "extractionId": "ext_text", "spanIds": ["t6"]})["session"]
    assert "exercisePick" not in _admit(ctx, plain["sessionId"]) and picks == []
    assert call(ctx, "workbench.get", {"sessionId": bound["sessionId"]})["session"]["exercisePick"]["due"] is True
    assert _admitted_events(repository, session["sessionId"]) == []


def test_exposure_since_the_card_was_shown_is_read_again_at_the_pick(library, imports):
    """Codex review F3: shown unexposed, then its page seen while the card is
    open: "use this one" opens it as practice beside the book, whatever entry
    the card asked for, and the problem says why."""

    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    shown = next(c for c in _view(ctx, proposal)["candidates"] if c["key"] == exercise["key"])
    assert shown["exposure"]["offeredAs"] == "check_on_your_own"
    record_shown_spans(repository, [f"ext_text:{exercise['span_ids'][0]}"], context="library",
                       entity_type="library_ask", entity_id="later")
    session = _use_this_one(ctx, proposal, exercise, entry="practice_this")
    assert session["entry"] == "work_through" and session["sourceVisible"] is True
    exposure = session["exercisePick"]["exposure"]
    assert exposure["exposed"] is True and exposure["offeredAs"] == "practice"
    assert exposure["label"] == "you've recently seen this page or its solution"


def test_exposure_since_the_pick_is_read_again_at_admission_and_shown(library, imports):
    """Codex review F3: an ordinary practice proposal's pick is re-read too
    (the sources service's own check re-reads only discriminate and retention
    proposals): exposed before admission, the problem says so."""

    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    session = _use_this_one(ctx, proposal, exercise)
    assert session["sourceVisible"] is False and session["exercisePick"]["exposure"]["exposed"] is False
    bound = _bind(paths, repository, ctx, imports, session)
    record_shown_spans(repository, [f"ext_text:{exercise['span_ids'][0]}"], context="library",
                       entity_type="library_ask", entity_id="later")
    admitted = _admit(ctx, bound["sessionId"])
    exposure = admitted["exercisePick"]["exposure"]
    assert admitted["exercisePick"]["exposureChecked"] == "admission"
    assert exposure["exposed"] is True and exposure["offeredAs"] == "practice"


def test_a_long_exercise_opens_on_its_complete_statement_not_the_cards_preview(library, imports, monkeypatch):
    """Codex review F4: the card's statement stops at the arm's display bound;
    the problem opens on the region's whole text, so its last subpart is
    there before the import finishes."""

    import learnloop.instructional.exercises as exercises
    from learnloop.instructional.exercises import exercise_regions

    monkeypatch.setattr(exercises, "STATEMENT_CHARS", 12)
    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    assert exercise["statement"].endswith("…") and len(exercise["statement"]) == 12  # the card's preview
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        [region] = [region for region in exercise_regions(connection, exercise["extraction_id"])
                    if list(region.span_ids) == exercise["span_ids"]]
    ctx = context(paths.root)
    session = _use_this_one(ctx, proposal, exercise)
    assert session["stemMd"] == region.text and len(region.text) > 12
    assert session["stemMd"].endswith(region.text[-12:])  # its final words, beyond the preview
    # The same pick again resumes that problem.
    assert _use_this_one(ctx, proposal, exercise)["sessionId"] == session["sessionId"]
    assert len(imports["queued"]) == 1


def test_a_fallback_pick_is_not_exposed_by_its_own_listing_and_its_request_reaches_the_import_unchanged(
        library, monkeypatch):
    import learnloop_sidecar.handlers.ai_providers as providers
    from learnloop_sidecar.handlers import library_exercises as LX

    paths, repository, _spans = library
    set_config(paths, "library_exercises", fallback_enabled=True)
    queued = []
    monkeypatch.setattr(DurableIngestJobs, "enqueue_reader_exercise_import",
                        lambda self, **kwargs: queued.append(kwargs) or "batch_reader")
    monkeypatch.setattr(providers, "ready_canonical_ingest_provider", lambda vault: ("fake", None, object()))
    ctx = context(paths.root)
    candidate = call(ctx, "reader.find_exercises", {"query": QUERY, "learningObjectIds": ["lo_matrices"],
                                                    "extractionId": "ext_text"})["candidates"][0]
    pick = candidate["pick"]
    assert pick["learningObjectIds"] == ["lo_matrices"] and len(pick["shownEventIds"]) == len(candidate["spanIds"])
    session = call(ctx, "workbench.open", {"origin": "reader", "entry": "practice_this",
                                           "stemMd": candidate["statement"], "extractionId": "ext_text",
                                           "spanIds": candidate["spanIds"], "importRequest": candidate["importRequest"],
                                           "exercisePick": pick})["session"]
    # The list's own showing never counts against the pick (as a proposal's own impression).
    assert session["exercisePick"]["proposalId"] is None
    assert session["exercisePick"]["exposure"]["exposed"] is False and session["sourceVisible"] is False
    [kwargs] = queued
    assert "reader_exercise" not in kwargs and "reader_exercise" not in kwargs["raw_selection"]
    assert [node.get("span_id") or node.get("spanId") for node in kwargs["raw_selection"]["nodes"]] == candidate["spanIds"]
    # Any other showing does, and ids that are not the list's own are ignored.
    other = record_shown_spans(repository, [f"ext_text:{candidate['spanIds'][0]}"], context="library",
                               entity_type="library_ask", entity_id="later")
    forged = {"proposal_id": None, "extraction_id": "ext_text", "span_ids": candidate["spanIds"],
              "learning_object_ids": ["lo_matrices"], "shown_event_ids": [*pick["shownEventIds"], *other]}
    verdict = LX.pick_exposure(load_vault(paths.root), repository, forged)
    assert verdict["exposed"] is True and verdict["reasons"] == ["source_exposed"]


def test_the_rw4b_switches_are_classified_in_the_parameter_registry():
    """Every new config key has a rule (the stage's rule; RW2b fix round 1 F11 for booleans)."""

    from learnloop.params import parameter_registry as registry

    for key in ("library_exercises.enabled", "library_exercises.fallback_enabled"):
        rule = registry.classify_config_path(key)
        assert rule is not None, key
        assert (rule.kind, rule.param_class) == ("structural", "operational"), key


# -- fix round 4 (orchestrator rulings): the server owns the admission ---------------------------------
# R1: one server operation admits a picked exercise's learner pick, keyed by
# the workbench session id. R2: a submit admits an owed pick first, or refuses
# (retryable) and submits nothing. R3: a resume opens the problem it names and
# checks its item and book. R4: one statement reader re-checks the exam and
# held-out predicate on the complete region at read time and fails closed.


@pytest.fixture
def grader(monkeypatch):
    """A blind grader fake behind the sidecar's grading provider (as RW2a's tests)."""

    import learnloop_sidecar.handlers.practice as practice
    from tests.split_live_helpers import ReadyRuntime
    from tests.test_stuck_prompt import StuckFake

    client = StuckFake()
    monkeypatch.setattr(practice, "ready_grading_provider",
                        lambda vault, override=None: ("fake", ReadyRuntime(), client))
    return client


def _end_open_sessions(ctx, repository) -> None:
    while (recent := repository.most_recent_open_session()) is not None:
        call(ctx, "end_session", {"sessionId": recent["id"]})


def test_r2_verify_f2_submit_with_no_practice_session_admits_the_owed_pick_first(library, imports, grader):
    """Codex final verify F2, end to end: the exercise was left while it
    imported, the practice session ended, and the problem is resumed and
    submitted with no practice session in the app. The submit admits the owed
    pick first (the practice session it starts, the learner pick, the serve on
    this problem), so nothing is left owed or lost."""

    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    session = _use_this_one(ctx, proposal, exercise)
    call(ctx, "workbench.save_step", {"sessionId": session["sessionId"], "clientIdempotencyKey": "s1", "op": "add",
                                      "bodyMd": "3x = 15, so x = 5"})
    call(ctx, "workbench.leave", {"sessionId": session["sessionId"]})
    bound = _bind(paths, repository, ctx, imports, session)
    assert bound["exercisePick"]["due"] is True
    _end_open_sessions(ctx, repository)
    resumed = call(ctx, "workbench.open", {"origin": "reader", "entry": "resume", "sessionId": session["sessionId"],
                                           "extractionId": "ext_text"})["session"]
    assert resumed["exercisePick"]["due"] is True
    submitted = call(ctx, "workbench.submit", {"sessionId": session["sessionId"]})
    view = submitted["session"]
    assert view["status"] == "submitted"
    assert view["exercisePick"]["admitted"] is True and view["exercisePick"]["due"] is False
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = connection.execute("SELECT import_request_json, practice_session_id FROM workbench_sessions WHERE id = ?",
                                 (session["sessionId"],)).fetchone()
    import json

    pick = json.loads(row[0])["reader_exercise"]
    assert pick["admitted_at"] and pick["practice_session_id"] == row[1] == submitted["practiceSession"]["sessionId"]
    assert len(_admitted_events(repository, session["sessionId"])) == 1
    # After a restart nothing is owed, and nothing is lost: the submit is answered from its receipt.
    again = call(context(paths.root), "workbench.submit", {"sessionId": session["sessionId"]})
    assert again["attempt"]["attemptId"] == submitted["attempt"]["attemptId"]


def test_r2_a_submit_whose_admission_fails_submits_nothing_and_stays_retryable(library, imports, grader, monkeypatch):
    from learnloop_sidecar.handlers import daily_plan

    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    session = _use_this_one(ctx, proposal, exercise)
    call(ctx, "workbench.save_step", {"sessionId": session["sessionId"], "clientIdempotencyKey": "s1", "op": "add",
                                      "bodyMd": "x = 5"})
    _bind(paths, repository, ctx, imports, session)
    attempts = _rows(repository, "practice_attempts")
    real = daily_plan.plan_learner_pick

    def refused(ctx, params):
        raise SidecarError("validation_error", "the plan refused the pick")

    monkeypatch.setattr(daily_plan, "plan_learner_pick", refused)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "workbench.submit", {"sessionId": session["sessionId"]})
    assert caught.value.code == "admission_pending"
    view = call(ctx, "workbench.get", {"sessionId": session["sessionId"]})["session"]
    assert view["status"] == "open" and view["exercisePick"]["due"] is True and view["steps"]
    assert _rows(repository, "practice_attempts") == attempts
    # Retried: admitted, then submitted.
    monkeypatch.setattr(daily_plan, "plan_learner_pick", real)
    done = call(ctx, "workbench.submit", {"sessionId": session["sessionId"]})["session"]
    assert done["status"] == "submitted" and done["exercisePick"]["admitted"] is True


def test_r1_verify_f10_admission_names_its_problem_never_another_with_the_same_item(library, imports, monkeypatch):
    """Codex final verify F10: two open problems share the item (A abandoned,
    B opened on the item, A reopened, B touched last). Delivering A's pick
    returns A, keeps A's serve on A and marks A admitted; B is untouched."""

    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    a = _use_this_one(ctx, proposal, exercise)
    bound = _bind(paths, repository, ctx, imports, a)
    call(ctx, "workbench.abandon", {"sessionId": a["sessionId"]})
    b = call(ctx, "workbench.open", {"origin": "reader", "entry": "work_through", "practiceItemId": bound["practiceItemId"],
                                     "stemMd": exercise["statement"], "extractionId": "ext_text",
                                     "spanIds": exercise["span_ids"]})["session"]
    assert b["sessionId"] != a["sessionId"]
    call(ctx, "workbench.reopen", {"sessionId": a["sessionId"]})
    call(ctx, "workbench.save_step", {"sessionId": b["sessionId"], "clientIdempotencyKey": "b1", "op": "add",
                                      "bodyMd": "B's step"})
    delivered = _deliver_pick(ctx, a["sessionId"], bound["practiceItemId"], proposal["proposal_id"],
                              bound["sourceExercise"]["importId"])
    assert delivered["sessionId"] == a["sessionId"]
    a_now = call(ctx, "workbench.get", {"sessionId": a["sessionId"]})["session"]
    b_now = call(ctx, "workbench.get", {"sessionId": b["sessionId"]})["session"]
    assert a_now["exercisePick"]["admitted"] is True
    assert (b_now["schedulerCandidateId"], b_now["planPresentationId"]) == (None, None)
    assert "exercisePick" not in b_now


def _deliver_pick(ctx, session_id: str, item_id: str, proposal_id: str, import_id: str) -> dict[str, Any]:
    """Delivering a picked exercise's owed pick: the server's one admission."""

    return _admit(ctx, session_id)


def test_r1_admission_is_idempotent_one_pick_one_admission(library, imports, monkeypatch):
    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    session = _use_this_one(ctx, proposal, exercise)
    _bind(paths, repository, ctx, imports, session)
    picks = _spy_picks(monkeypatch)
    first = call(ctx, "workbench.admit", {"sessionId": session["sessionId"]})
    second = call(context(paths.root), "workbench.admit", {"sessionId": session["sessionId"]})
    assert len(picks) == 1 and len(_admitted_events(repository, session["sessionId"])) == 1
    assert first["practiceSession"]["sessionId"] == second["practiceSession"]["sessionId"]
    assert first["session"]["exercisePick"] == second["session"]["exercisePick"]


def test_r3_a_resume_opens_the_problem_it_names_on_its_own_item_and_book(library, imports):
    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    session = _use_this_one(ctx, proposal, exercise)
    bound = _bind(paths, repository, ctx, imports, session)
    for wrong in ({"practiceItemId": "pi_eigen_1"}, {"extractionId": "ext_other"}):
        with pytest.raises(SidecarError) as caught:
            call(ctx, "workbench.open", {"origin": "reader", "entry": "resume", "sessionId": session["sessionId"],
                                         "extractionId": "ext_text", **wrong})
        assert caught.value.code == "validation_error"
    resumed = call(ctx, "workbench.open", {"origin": "reader", "entry": "resume", "sessionId": session["sessionId"],
                                           "practiceItemId": bound["practiceItemId"], "extractionId": "ext_text"})
    assert resumed["session"]["sessionId"] == session["sessionId"]


def test_r4_verify_f7_an_exercise_held_out_after_its_card_was_shown_is_never_read_or_opened(library, imports):
    """Codex final verify F7: the card was shown (eligible), then its region
    was held out; "use this one" reads nothing of it, opens nothing, imports
    nothing, and no part of its statement (the preview's tail included) is
    returned."""

    from learnloop.instructional.exercises import exercise_regions

    paths, repository, spans = library
    proposal = _proposal(paths, repository)
    sentinel = "An eigenvalue t satisfies 3t + 5 = 20"
    exercise = next(e for e in proposal["source_exercises"] if sentinel[:20] in e["statement"])
    ctx = context(paths.root)
    assert any(c["key"] == exercise["key"] for c in _view(ctx, proposal)["candidates"])  # shown, eligible
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        [region] = [r for r in exercise_regions(connection, exercise["extraction_id"])
                    if list(r.span_ids) == exercise["span_ids"]]
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    with pytest.raises(SidecarError) as caught:
        call(ctx, "workbench.open", {
            "origin": "reader", "entry": "practice_this", "stemMd": exercise["statement"],
            "extractionId": exercise["extraction_id"], "spanIds": exercise["span_ids"], "clientIdempotencyKey": "k",
            "sourceExercise": {"proposalId": proposal["proposal_id"], "extractionId": exercise["extraction_id"],
                               "spanIds": exercise["span_ids"]}})
    assert caught.value.code == "exercise_withheld"
    assert region.text[-15:] not in caught.value.message and sentinel not in caught.value.message
    assert imports["queued"] == []
    assert _rows(repository, "workbench_sessions") == 0


def test_r4_a_problem_opened_before_its_region_was_held_out_is_not_shown_again(library, imports):
    paths, repository, spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    session = _use_this_one(ctx, proposal, exercise)
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    for params in ({"entry": "resume", "sessionId": session["sessionId"], "extractionId": "ext_text"},):
        with pytest.raises(SidecarError) as caught:
            call(ctx, "workbench.open", {"origin": "reader", **params})
        assert caught.value.code == "exercise_withheld"
    with pytest.raises(SidecarError) as caught:
        _use_this_one(ctx, proposal, exercise)
    assert caught.value.code == "exercise_withheld"


def test_r4_the_statement_reader_fails_closed(library, monkeypatch):
    from learnloop.content.sources import exercise_statements as shared
    from learnloop_sidecar.handlers import library_exercises as LX

    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    vault = load_vault(paths.root)
    assert LX.read_exercise_statement(vault, repository, exercise["extraction_id"], exercise["span_ids"]) is not None

    def broken(*args, **kwargs):
        raise RuntimeError("the predicate could not be read")

    monkeypatch.setattr(shared.EM, "exam_withheld", broken)
    assert LX.read_exercise_statement(vault, repository, exercise["extraction_id"], exercise["span_ids"]) is None
    ctx = context(paths.root)
    view = _view(ctx, proposal)
    assert view["candidates"] == [] and view["withheld"] == len(proposal["source_exercises"])


#: What reads an exercise statement (fix rounds 4 and 5): the regions, the
#: blocks' text and the exam predicate that clears them. Only the one shared
#: reader (``learnloop.content.sources.exercise_statements``) touches them.
_STATEMENT_READS = frozenset({"exercise_regions", "blocks_by_key", "extraction_hint_rows", "exam_withheld",
                              "full_statement"})
#: S1's two paths that read a statement (its import worker, its selection):
#: scanned too, and each must read through the shared reader.
_S1_PATHS = {"selection_for_region", "_import_source_exercise"}
#: The modules that build responses carrying a stored statement (a problem's
#: stem, a list's titles), and the gates such a response must pass.
_RESPONSE_MODULES = {"src/learnloop_sidecar/handlers/workbench.py", "src/learnloop_sidecar/handlers/workbench_help.py",
                     "src/learnloop_sidecar/handlers/library_exercises.py", "src/learnloop/reader/recap.py"}
_GATES = frozenset({"statement_cleared", "_refuse_withheld_exercise", "_cleared", "_view"})
#: Builders allowed without a gate, and why.
_UNGATED = {
    "record_line": "returns the record line and save time only, never the statement",
    "_view": "is the gate's own caller (it calls _refuse_withheld_exercise first)",
}
_STORED_READS = frozenset({"session_view", "sessions_for_source", "sessions_for_item"})


def _functions(path: Path) -> dict[str, ast.AST]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name: node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _names(node: ast.AST) -> set[str]:
    found: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            found.add(child.id)
        elif isinstance(child, ast.Attribute):
            found.add(child.attr)
        elif isinstance(child, ast.ImportFrom):
            found.update(alias.name for alias in child.names)
    return found


def _literals(node: ast.AST) -> set[str]:
    return {child.value for child in ast.walk(node) if isinstance(child, ast.Constant) and isinstance(child.value, str)}


def _scanned() -> dict[tuple[str, str], ast.AST]:
    functions: dict[tuple[str, str], ast.AST] = {}
    for root in (ROOT / "src" / "learnloop_sidecar" / "handlers", ROOT / "src" / "learnloop" / "reader"):
        for path in sorted(root.rglob("*.py")):
            for name, node in _functions(path).items():
                functions[(str(path.relative_to(ROOT)), name)] = node
    s1 = ROOT / "src" / "learnloop" / "content" / "authoring" / "source_exercise_import.py"
    for name, node in _functions(s1).items():
        if name in _S1_PATHS:
            functions[(str(s1.relative_to(ROOT)), name)] = node
    return functions


def test_r2_no_handler_reader_module_or_s1_path_reads_an_exercise_statement_another_way():
    """Direct reads, and indirect ones through a helper that reads (transitively)."""

    functions = _scanned()
    direct = {key for key, node in functions.items() if _names(node) & _STATEMENT_READS}
    # A function that calls a scanned function that reads is a reader too.
    by_name: dict[str, set[tuple[str, str]]] = {}
    for key in functions:
        by_name.setdefault(key[1], set()).add(key)
    readers = set(direct)
    changed = True
    while changed:
        changed = False
        for key, node in functions.items():
            if key in readers:
                continue
            called = {n for n in _names(node) if n != key[1]}
            if any(other in readers for name in called for other in by_name.get(name, ())):
                readers.add(key)
                changed = True
    assert sorted(f"{path}:{name}" for path, name in readers) == []
    # S1's worker and its selection read through the shared reader.
    for (path, name), node in functions.items():
        if name in _S1_PATHS:
            assert "read_exercise_statement" in _names(node), name


def test_r2_every_response_carrying_a_stored_statement_passes_the_gate():
    found: list[str] = []
    for (path, name), node in _scanned().items():
        if path not in _RESPONSE_MODULES or name in _UNGATED:
            continue
        stored = bool(_names(node) & _STORED_READS) or "stem_md" in _literals(node)
        if stored and not (_names(node) & _GATES):
            found.append(f"{path}:{name}")
    assert found == []


def test_r2_the_shared_reader_lives_where_s1_and_the_reader_import_it():
    from learnloop.content.sources import exercise_statements as shared
    from learnloop.content.authoring import source_exercise_import as s1
    from learnloop.instructional import exercises as arm
    from learnloop_sidecar.handlers import library_exercises as LX

    assert LX.read_exercise_statement is shared.read_exercise_statement
    assert s1.read_exercise_statement is shared.read_exercise_statement
    assert arm.exercise_regions is shared.exercise_regions


def test_r1_admit_is_a_workbench_rpc_that_refuses_while_switched_off(library):
    paths, _repository, _spans = library
    set_config(paths, "workbench", enabled=False)
    with pytest.raises(SidecarError) as caught:
        call(context(paths.root), "workbench.admit", {"sessionId": "wbs_x"})
    assert caught.value.code == "workbench_disabled"


def _rows(repository, table: str) -> int:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]


# -- fix round 5 (orchestrator rulings): R2 contract, R3 item exposure ------------------------------


def _hold_out(repository, spans) -> None:
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})


def _sentinel_exercise(proposal: dict[str, Any]) -> dict[str, Any]:
    return next(e for e in proposal["source_exercises"] if "An eigenvalue t satisfies" in e["statement"])


def test_r2_verify_f7_get_refresh_and_an_admitted_admit_never_return_a_withheld_statement(library, imports):
    """Codex final verify (round 4) F7, as written: an allowed exercise is
    opened, then its region is held out; ``workbench.get``,
    ``workbench.refresh_import`` and an already-admitted ``workbench.admit``
    refuse, and nothing of the statement is returned."""

    paths, repository, spans = library
    proposal = _proposal(paths, repository)
    exercise = _sentinel_exercise(proposal)
    ctx = context(paths.root)
    session = _use_this_one(ctx, proposal, exercise)
    assert "An eigenvalue t satisfies" in session["stemMd"]
    _bind(paths, repository, ctx, imports, session)
    _admit(ctx, session["sessionId"])
    _hold_out(repository, spans)
    for name in ("workbench.get", "workbench.refresh_import", "workbench.admit"):
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, {"sessionId": session["sessionId"]})
        assert caught.value.code == "exercise_withheld", name
        assert "eigenvalue" not in caught.value.message


#: Every parameter an enumerated RPC may require, and what it is given.
def _params_for(spec, ids: dict[str, Any]) -> dict[str, Any]:
    from pydantic.alias_generators import to_camel as camel

    fill = {
        "session_id": ids["session"], "practice_item_id": ids["item"], "extraction_id": "ext_text",
        "attempt_id": ids["attempt"], "job_id": "job_unknown", "origin": "reader", "entry": "resume",
        "client_idempotency_key": "contract-k", "op": "add", "body_md": "x = 5", "visible": True,
        "proposal_id": ids["proposal"], "query": QUERY, "question_assist_id": "qa_unknown", "answer_md": "x = 5",
        # Reader RW2c's "another passage".
        "assist_id": "ha_unknown",
    }
    params: dict[str, Any] = {}
    for field, info in spec.params_model.model_fields.items():
        if field in fill:
            params[camel(field)] = fill[field]
        elif info.is_required():
            raise AssertionError(f"{spec.name}: the contract test has no value for {field!r}; add one")
    if spec.name == "reader.exercise_candidates":
        params["keys"] = ids["keys"]
    if spec.name == "reader.library_job":
        params["jobId"] = ids["library_job"]
    return params


def _finished_exercise_jobs(ctx, proposal: dict[str, Any], exercise: dict[str, Any]) -> dict[str, str]:
    """A finished ``reader.exercise_candidates`` and ``reader.find_exercises``
    job, both showing ``exercise`` while it may be shown; their job ids."""

    from tests.library_ask_fixtures import finish_job as finish

    started = {
        "exercise_candidates": call_rpc(ctx, "reader.exercise_candidates",
                                        {"proposalId": proposal["proposal_id"], "keys": _keys(proposal)}),
        "find_exercises": call_rpc(ctx, "reader.find_exercises", {"query": QUERY, "learningObjectIds": ["lo_matrices"],
                                                                  "extractionId": "ext_text"}),
    }
    for kind, job in started.items():
        result = finish(ctx, job)
        assert exercise["key"] in [candidate["key"] for candidate in result["candidates"]], kind
    return {kind: job["jobId"] for kind, job in started.items()}


def test_r2_contract_no_workbench_or_reader_exercise_rpc_returns_a_held_out_statement(library, imports, grader):
    """Every registered ``workbench.*`` RPC and every reader exercise RPC
    (from the registry, so a new one is covered as it is added) is called
    once the open exercise's region is held out: whatever each answers or
    refuses, the statement is never in it."""

    import json

    from learnloop_sidecar.registry import METHOD_REGISTRY
    from learnloop_sidecar.handlers.library_exercises import LIBRARY_EXERCISE_RPCS

    paths, repository, spans = library
    set_config(paths, "library_exercises", fallback_enabled=True)
    proposal = _proposal(paths, repository)
    exercise = _sentinel_exercise(proposal)
    ctx = context(paths.root)
    # Fix round 6 (F7): finished exercise jobs, kept from before the hold-out.
    jobs = _finished_exercise_jobs(ctx, proposal, exercise)
    session = _use_this_one(ctx, proposal, exercise)
    call(ctx, "workbench.save_step", {"sessionId": session["sessionId"], "clientIdempotencyKey": "s1", "op": "add",
                                      "bodyMd": "3t = 15"})
    bound = _bind(paths, repository, ctx, imports, session)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        from learnloop.instructional.exercises import exercise_regions

        [region] = [r for r in exercise_regions(connection, exercise["extraction_id"])
                    if list(r.span_ids) == exercise["span_ids"]]
    _hold_out(repository, spans)
    ids = {"session": session["sessionId"], "item": bound["practiceItemId"], "attempt": "att_unknown",
           "proposal": proposal["proposal_id"], "keys": _keys(proposal), "library_job": jobs["find_exercises"]}
    # The reads of kept jobs (fix round 6): every registered ``reader.library_job*``
    # read, beside the workbench and the exercise RPCs.
    names = sorted(name for name in METHOD_REGISTRY if name.startswith("workbench.") or name in LIBRARY_EXERCISE_RPCS
                   or name == "reader.library_job")
    assert {"workbench.get", "workbench.admit", "workbench.submit", "reader.exercise_candidates",
            "reader.library_job"} <= set(names)
    sentinels = ("An eigenvalue t satisfies", region.text[-24:])
    answered: dict[str, str] = {}
    for name in names:
        params = _params_for(METHOD_REGISTRY[name], ids)
        try:
            text = json.dumps(call(ctx, name, params), default=str)
            answered[name] = "answered"
        except SidecarError as exc:
            text = f"{exc.code} {exc.message} {json.dumps(exc.details, default=str)}"
            answered[name] = exc.code
        for sentinel in sentinels:
            assert sentinel not in text, (name, answered[name])
    # Every kept exercise job, read after the hold-out: the candidate is gone
    # (its statement, and its permission to render the proposal's stored one).
    for kind, job_id in jobs.items():
        read = call_rpc(ctx, "reader.library_job", {"jobId": job_id})
        text = json.dumps(read, default=str)
        assert read["state"] == "done" and exercise["key"] not in text, kind
        for sentinel in sentinels:
            assert sentinel not in text, kind
    # The statement-bearing ones refuse with the existing code.
    for name in ("workbench.get", "workbench.open", "workbench.admit", "workbench.submit", "workbench.leave",
                 "workbench.refresh_import"):
        assert answered[name] == "exercise_withheld", (name, answered[name])
    # The lists leave the problem out; its steps are kept.
    assert call(ctx, "workbench.for_source", {"extractionId": "ext_text"})["sessions"] == []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM workbench_steps WHERE session_id = ?",
                                  (session["sessionId"],)).fetchone()[0] >= 1


def test_r3_verify_f11_admission_reads_the_bound_items_own_exposure_and_says_practice_only(library, imports):
    """Codex final verify (round 4) F11: the bound item's answer (or a family
    member's) was revealed after the pick; admission's exposure reading now
    includes the item, so the problem is practice only, kept and shown."""

    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    session = _use_this_one(ctx, proposal, exercise)
    assert session["exercisePick"]["exposure"]["exposed"] is False
    bound = _bind(paths, repository, ctx, imports, session)
    from learnloop.attempts.reveal_ledger import record_reveal_strict

    # The item's answer is shown (a full answer display), after the pick.
    record_reveal_strict(repository, practice_item_id=bound["practiceItemId"], source_kind="answer_display", amount=1.0)
    admitted = _admit(ctx, session["sessionId"])
    exposure = admitted["exercisePick"]["exposure"]
    assert exposure["exposed"] is True and exposure["offeredAs"] == "practice"
    assert set(exposure["reasons"]) & {"revealed", "family_revealed"}
    assert admitted["exercisePick"]["exposureChecked"] == "admission"
    # Kept: a later read shows the same classification.
    again = call(ctx, "workbench.get", {"sessionId": session["sessionId"]})["session"]["exercisePick"]["exposure"]
    assert again == exposure


# -- fix round 6 (orchestrator rulings): F7, kept exercise jobs revalidated at delivery -----------------


def test_r6_verify_f7_a_finished_exercise_job_read_after_its_region_is_held_out_never_delivers_it(library):
    """Codex verify (round 5) F7: ``reader.find_exercises`` (and the
    candidates view) finished while the exercise was allowed; its region is
    then held out. ``reader.library_job`` drops it at delivery, counted as
    withheld; the kept result itself is unchanged, and a region that is
    still allowed is still delivered."""

    paths, repository, spans = library
    set_config(paths, "library_exercises", fallback_enabled=True)
    proposal = _proposal(paths, repository)
    exercise = _sentinel_exercise(proposal)
    ctx = context(paths.root)
    jobs = _finished_exercise_jobs(ctx, proposal, exercise)
    found_before = call_rpc(ctx, "reader.library_job", {"jobId": jobs["find_exercises"]})["result"]
    assert "An eigenvalue t satisfies" in _all_text(found_before["candidates"])
    _hold_out(repository, spans)
    found = call_rpc(ctx, "reader.library_job", {"jobId": jobs["find_exercises"]})["result"]
    assert "An eigenvalue t satisfies" not in _all_text(found)
    assert exercise["key"] not in [candidate["key"] for candidate in found["candidates"]]
    assert found["dropped"]["withheld"] >= 1
    view = call_rpc(ctx, "reader.library_job", {"jobId": jobs["exercise_candidates"]})["result"]
    assert exercise["key"] not in [candidate["key"] for candidate in view["candidates"]]
    assert view["withheld"] >= 1
    # The kept result is not rewritten: the gate runs at every read.
    kept = ctx.library_ask_jobs.get(jobs["find_exercises"]).result
    assert exercise["key"] in [candidate["key"] for candidate in kept["candidates"]]
