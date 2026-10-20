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


def test_admitted_the_problem_binds_to_the_written_item_and_becomes_a_learner_pick(library, imports):
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
    # The shell's pick: the plan's own learner pick, with the proposal and the import.
    picked = call(ctx, "plan_learner_pick", {
        "practiceItemId": bound["practiceItemId"], "proposalId": proposal["proposal_id"],
        "sourceExerciseImportId": source["importId"]})
    if picked.get("enabled"):
        assert picked["proposalPick"]["importId"] == source["importId"]
    else:  # the plan off: the selection is recorded, the open's serve delivers it
        assert picked["proposalPick"]["delivery"] == "on_open"
    # The check-me hand-off reopens the same problem with the pick's serve, its book choice kept.
    reopened = call(ctx, "workbench.open", {"origin": "reader", "entry": "practice_this",
                                            "practiceItemId": bound["practiceItemId"], "stemMd": exercise["statement"],
                                            "extractionId": "ext_text", "spanIds": exercise["span_ids"],
                                            "schedulerCandidateId": "cand_1", "planPresentationId": None})
    assert reopened["resumed"] is True and reopened["session"]["sessionId"] == session["sessionId"]
    assert reopened["session"]["schedulerCandidateId"] == "cand_1"
    assert reopened["session"]["sourceVisible"] is False


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


def _admitting_open(ctx, bound: dict[str, Any], exercise: dict[str, Any]) -> dict[str, Any]:
    """The shell's hand-off after the learner pick and its serve succeeded."""

    return call(ctx, "workbench.open", {"origin": "reader", "entry": "practice_this",
                                        "practiceItemId": bound["practiceItemId"], "stemMd": exercise["statement"],
                                        "extractionId": "ext_text", "spanIds": exercise["span_ids"],
                                        "admittedSessionId": bound["sessionId"]})["session"]


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
    # A failed delivery acknowledges nothing: the pick stays owed, to retry.
    with pytest.raises(SidecarError):
        call(restarted, "plan_learner_pick", {"practiceItemId": bound["practiceItemId"],
                                              "proposalId": proposal["proposal_id"],
                                              "sourceExerciseImportId": "sei_not_this_one"})
    assert call(restarted, "workbench.get", {"sessionId": session["sessionId"]})["session"]["exercisePick"]["due"] is True
    # A hand-off that admits nothing (no admitted session named) acknowledges nothing either.
    call(restarted, "workbench.open", {"origin": "reader", "entry": "practice_this", "practiceItemId": bound["practiceItemId"],
                                       "stemMd": exercise["statement"], "extractionId": "ext_text",
                                       "spanIds": exercise["span_ids"]})
    assert call(restarted, "workbench.get", {"sessionId": session["sessionId"]})["session"]["exercisePick"]["due"] is True
    # Delivered: the plan's pick, then the hand-off that resumes the problem.
    call(restarted, "plan_learner_pick", {"practiceItemId": bound["practiceItemId"], "proposalId": proposal["proposal_id"],
                                          "sourceExerciseImportId": bound["sourceExercise"]["importId"]})
    admitted = _admitting_open(restarted, bound, exercise)
    assert admitted["sessionId"] == session["sessionId"]
    assert admitted["exercisePick"]["admitted"] is True and admitted["exercisePick"]["due"] is False
    assert admitted["exercisePick"]["exposureChecked"] == "admission"
    # Once: a repeated hand-off and another restart owe nothing more.
    _admitting_open(restarted, bound, exercise)
    assert call(context(paths.root), "workbench.get", {"sessionId": session["sessionId"]})["session"]["exercisePick"]["due"] is False
    [event] = _admitted_events(repository, session["sessionId"])
    assert event["payload"]["authority_class"] == SF.SALIENCE_ONLY
    with pytest.raises(SF.SalienceEvidenceRejected):
        SF.reject_salience(event)


def test_admitting_needs_the_item_and_never_marks_another_problem(library, imports):
    paths, repository, _spans = library
    proposal = _proposal(paths, repository)
    exercise = proposal["source_exercises"][0]
    ctx = context(paths.root)
    session = _use_this_one(ctx, proposal, exercise)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "workbench.open", {"origin": "reader", "entry": "practice_this", "stemMd": "x",
                                     "extractionId": "ext_text", "spanIds": ["t1"],
                                     "importRequest": {"extractionId": "ext_text", "rawSelection": {}},
                                     "admittedSessionId": session["sessionId"]})
    assert caught.value.code == "validation_error"
    # Still running: an admission names a problem that owes nothing yet, and is ignored.
    call(ctx, "workbench.open", {"origin": "reader", "entry": "work_through", "practiceItemId": "pi_eigen_1",
                                 "stemMd": "Solve it", "extractionId": "ext_text", "spanIds": ["t6"],
                                 "admittedSessionId": session["sessionId"]})
    pending = call(ctx, "workbench.get", {"sessionId": session["sessionId"]})["session"]
    assert pending["exercisePick"]["admitted"] is False
    bound = _bind(paths, repository, ctx, imports, session)
    # Another item's hand-off never admits this problem.
    call(ctx, "workbench.open", {"origin": "reader", "entry": "work_through", "practiceItemId": "pi_eigen_1",
                                 "stemMd": "Solve it", "extractionId": "ext_text", "spanIds": ["t6"],
                                 "admittedSessionId": session["sessionId"]})
    assert call(ctx, "workbench.get", {"sessionId": bound["sessionId"]})["session"]["exercisePick"]["due"] is True
    # An unknown problem named as admitted: the hand-off still opens, nothing is marked.
    call(ctx, "workbench.open", {"origin": "reader", "entry": "practice_this", "practiceItemId": bound["practiceItemId"],
                                 "stemMd": "Solve it", "extractionId": "ext_text", "spanIds": ["t6"],
                                 "admittedSessionId": "wbs_unknown"})
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
    call(ctx, "plan_learner_pick", {"practiceItemId": bound["practiceItemId"], "proposalId": proposal["proposal_id"],
                                    "sourceExerciseImportId": bound["sourceExercise"]["importId"]})
    admitted = _admitting_open(ctx, bound, exercise)
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
