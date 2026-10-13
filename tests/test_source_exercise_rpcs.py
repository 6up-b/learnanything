"""S1: the pick RPCs for textbook exercises, and the owner-run harvest and verify commands."""
from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.instructional.exercises import exercise_candidates
from learnloop.practice_index.retrieval import find_practice
from learnloop.practice_index.usage import USAGE_TASK
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, call, loaded, service_clients


def _proposal(paths, repository):
    return find_practice(loaded(paths), repository, "solve for the eigenvalue x", {},
                         exercise_arm=exercise_candidates, rerank_client=FakeServiceLLM(),
                         caller={"kind": "tutor", "ref": "q"})


def test_picking_an_exercise_proposal_queues_its_import_and_records_the_pick(tmp_path, monkeypatch):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    result = _proposal(paths, repository)
    exercise = result["source_exercises"][0]
    queued = {}
    monkeypatch.setattr(DurableIngestJobs, "enqueue_source_exercise_import",
                        lambda self, **kwargs: queued.update(kwargs) or "batch_1")
    response = call(paths.root, "import_source_exercise", {
        "proposalId": result["proposal_id"], "extractionId": exercise["extraction_id"],
        "spanIds": exercise["span_ids"]})
    assert response["result"]["status"] == "queued"
    import_id = response["result"]["importId"]
    assert queued["import_id"] == import_id and queued["span_ids"] == exercise["span_ids"]
    with repository.connection() as connection:
        pick = connection.execute("SELECT right_kind, right_id, verdict FROM judgment_ledger WHERE task=?",
                                  (USAGE_TASK,)).fetchone()
    assert tuple(pick) == ("source_exercise", exercise["key"], "practised")
    status = call(paths.root, "get_source_exercise_import", {"importId": import_id})["result"]
    assert status["status"] == "authoring" and status["practiceItemId"] is None


def test_an_exercise_the_proposal_did_not_propose_is_refused(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    result = _proposal(paths, repository)
    response = call(paths.root, "import_source_exercise", {
        "proposalId": result["proposal_id"], "extractionId": "ext_text", "spanIds": [spans["solutions"][1]]})
    assert response["error"]["data"]["code"] == "validation_error"


def test_harvest_and_verify_dry_runs_send_and_write_nothing(tmp_path):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    with repository.connection() as connection:
        before = connection.execute("SELECT COUNT(*) FROM model_call_receipts").fetchone()[0]
    runner = CliRunner()
    harvest = runner.invoke(app, ["sources", "exercises", "harvest", "--dry-run", "--json",
                                  "--vault", str(paths.root)])
    assert harvest.exit_code == 0, harvest.output
    report = json.loads(harvest.output)
    assert report["status"] == "dry_run" and report["targets"] is not None
    verify = runner.invoke(app, ["sources", "exercises", "verify", "--dry-run", "--json", "--vault", str(paths.root)])
    assert verify.exit_code == 0, verify.output
    assert json.loads(verify.output)["status"] == "dry_run"
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM model_call_receipts").fetchone()[0] == before
        assert connection.execute("SELECT COUNT(*) FROM source_exercise_imports").fetchone()[0] == 0


def test_a_live_batch_needs_a_money_cap(tmp_path):
    paths, _repository, _spans = build_textbook_vault(tmp_path / "vault")
    result = CliRunner().invoke(app, ["sources", "exercises", "verify", "--json", "--vault", str(paths.root)])
    assert result.exit_code == 1
    assert "max-cost-usd" in json.loads(result.output)["reason"]


def test_harvest_imports_judged_exercises_for_thin_facets(tmp_path):
    from learnloop.instructional.harvest import harvest
    from tests.source_service_fakes import service_clients

    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    llm = FakeServiceLLM()
    report = harvest(loaded(paths), repository, dry_run=False, max_cost_usd=1.0, facet_ids=("facet_eigen",),
                     clients=service_clients(llm), rerank_client=llm)
    assert report["status"] == "complete"
    written = [row for row in report["imports"] if row["status"] == "written"]
    assert written and all(row["key_status"] for row in written)
    vault = loaded(paths)
    assert all(vault.practice_items[row["practice_item_id"]].canonical_exercise is not None for row in written)


def test_a_harvest_says_why_picked_exercises_were_not_imported(tmp_path):
    """Live sanity run: the judge picked two exercises but quoted none of the
    requested facet in them, so the exact facet filter dropped all of them
    (``failed_unknown``), and the report said "no exercise picked"."""
    from learnloop.instructional.harvest import harvest
    from learnloop.practice_index.contracts import ExerciseMetadata
    from tests.source_service_fakes import service_clients

    class NoFacetQuotes(FakeServiceLLM):
        def _MixedPracticeRerank(self, request, context):
            judged = super()._MixedPracticeRerank(request, context)
            return judged.model_copy(update={"exercise_metadata": [
                ExerciseMetadata(ref=row.ref, facets=[], practice_mode=row.practice_mode)
                for row in judged.exercise_metadata]})

    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    llm = NoFacetQuotes()
    report = harvest(loaded(paths), repository, dry_run=False, max_cost_usd=1.0, facet_ids=("facet_eigen",),
                     clients=service_clients(llm), rerank_client=llm)
    assert report["imports"] == []
    [skipped] = report["skipped"]
    assert skipped["facet_id"] == "facet_eigen"
    assert skipped["failed_filters"]["failed_unknown"] >= 1
    assert skipped["reason"].startswith("no exercise passed the exact filters")
    assert "failed_unknown" in skipped["reason"]


def _proposal_row(repository, *, proposal_id, constraints, intent, exercise, caller="tutor"):
    from learnloop.db.stores.practice_index import insert_proposal

    with repository.connection() as connection:
        insert_proposal(connection, id=proposal_id, created_at="2026-10-12T08:59:00Z", origin="rpc",
                        query_id="q", query_text="eigenvalues", constraints=constraints, path="direct",
                        path_reason="test", signals={}, reranked=True, rerank_status="reranked",
                        rerank_model=None, proposed=[{**exercise, "rank": 1}], exclusions={}, manifest={},
                        algorithm_version="mvp-0.16", caller=caller, caller_ref="qe_1", intent=intent)


def _run_import_job(paths, repository, queued, llm):
    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import JobContext, RunnerServices

    ctx = JobContext(repo=repository, vault_root=paths.root,
                     job={"id": "job_1", "attempt_count": 1, "payload": {**queued, "caller": "learner"}},
                     clock=None, worker_id="w",
                     services=RunnerServices(exercise_import_client_factory=lambda ctx: llm,
                                             background_key_checks=False))
    ctx.report = lambda *args, **kwargs: None  # type: ignore[method-assign]
    return jobs.handle_source_exercise_import(ctx)


def test_an_interactive_import_is_validated_against_its_proposal_and_corrected(tmp_path, monkeypatch):
    """Codex re-review F7: the import job had no validator, so a draft that
    turned out to practise another facet (or to take longer) than the proposal
    claimed was written with no correction. The job now rehydrates the
    proposal's constraints; a learner's pick is still written, with the claim
    corrected."""

    from learnloop.db.stores.source_service import import_row
    from learnloop.instructional.exercises import exercise_key

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    span = spans["exercises"][1]  # "1. An eigenvalue t satisfies 3t + 5 = 20 ..."
    exercise = {"kind": "source_exercise", "key": exercise_key("ext_text", [span]), "extraction_id": "ext_text",
                "span_ids": [span], "source_id": "src_text", "revision_id": "rev_text", "label": "Exercise 1",
                "page": 9, "statement": "1. An eigenvalue t satisfies 3t + 5 = 20", "relevance": "relevant",
                "rationale": "fits", "provisional": {"facets": ["facet_determinant"], "practice_mode": "short_answer"}}
    _proposal_row(repository, proposal_id="pp_pick", constraints={"facet_ids": ["facet_determinant"]},
                  intent="practice", exercise=exercise)
    queued = {}
    monkeypatch.setattr(DurableIngestJobs, "enqueue_source_exercise_import",
                        lambda self, **kwargs: queued.update(kwargs) or "batch_1")
    response = call(paths.root, "import_source_exercise", {"proposalId": "pp_pick", "extractionId": "ext_text",
                                                           "spanIds": [span]})
    import_id = response["result"]["importId"]
    assert queued["request"]["constraints"] == {"facet_ids": ["facet_determinant"]}
    result = _run_import_job(paths, repository, queued, FakeServiceLLM())
    assert result["status"] == "written"  # learner authority
    with repository.connection() as connection:
        row = import_row(connection, import_id)
    validation = row["validation"]
    assert validation["checked"] is True and validation["ok"] is False, validation
    assert validation["correction"].startswith("this exercise turned out to practise")
    assert "facet_determinant" in validation["correction"]
    status = call(paths.root, "get_source_exercise_import", {"importId": import_id})["result"]
    assert status["validation"]["correction"] == validation["correction"]


def test_an_interactive_import_bounds_the_authored_drafts_own_duration(tmp_path, monkeypatch):
    """Codex third pass F7: the job validated minutes computed before authoring
    with ``expected_minutes=None``, so a draft authored at 20 minutes passed a
    five-minute bound as ``minutes=3.5`` while the plan's estimator, given the
    draft, says 20.5. The job now evaluates the authored draft's duration."""

    from learnloop.content.authoring import source_exercise_import as SEI
    from learnloop.daily_plan.estimates import Estimator, load_duration_evidence
    from learnloop.db.stores.source_service import import_row
    from learnloop.instructional.exercises import exercise_key

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    span = spans["exercises"][1]
    exercise = {"kind": "source_exercise", "key": exercise_key("ext_text", [span]), "extraction_id": "ext_text",
                "span_ids": [span], "source_id": "src_text", "revision_id": "rev_text", "label": "Exercise 1",
                "page": 9, "statement": "1. An eigenvalue t satisfies 3t + 5 = 20", "relevance": "relevant",
                "rationale": "fits", "provisional": {"facets": [], "practice_mode": "short_answer"}}
    _proposal_row(repository, proposal_id="pp_short", constraints={"max_estimated_minutes": 5},
                  intent="practice", exercise=exercise)
    queued = {}
    monkeypatch.setattr(DurableIngestJobs, "enqueue_source_exercise_import",
                        lambda self, **kwargs: queued.update(kwargs) or "batch_1")
    import_id = call(paths.root, "import_source_exercise", {"proposalId": "pp_short", "extractionId": "ext_text",
                                                            "spanIds": [span]})["result"]["importId"]
    authored = SEI.author_exercises

    def twenty_minutes(*args, **kwargs):
        batch = authored(*args, **kwargs)
        for draft in batch.drafts:
            draft.payload["expected_minutes"] = 20.0
        return batch

    monkeypatch.setattr(SEI, "author_exercises", twenty_minutes)
    result = _run_import_job(paths, repository, queued, FakeServiceLLM())
    assert result["status"] == "written"  # learner authority
    vault = loaded(paths)
    plan = Estimator(load_duration_evidence(repository, latency_cap_minutes=vault.config.plan.latency_cap_minutes),
                     read_words_per_minute=vault.config.plan.read_words_per_minute)
    actual = plan.item_minutes(vault, result["practice_item_id"])
    assert actual == 20.5
    with repository.connection() as connection:
        validation = import_row(connection, import_id)["validation"]
    assert validation["ok"] is False and validation["minutes"] == actual, validation
    assert "more than 5" in validation["reason"]


def test_the_carried_duration_response_is_the_plan_estimate_of_the_authored_draft():
    """The job's rehydrated estimator agrees with the plan's for any authored
    duration, with mode latencies and feedback dwell in the evidence."""

    import pytest

    from learnloop.content.authoring.draft_validation import duration_estimator
    from learnloop.daily_plan.estimates import DurationEvidence, Estimator
    from learnloop.instructional.practice import duration_response

    plan = Estimator(DurationEvidence(latencies_by_mode={"short_answer": (2.0, 4.0, 6.0, 30.0)},
                                      feedback_dwell=(1.5,) * 12))
    carried = {mode: duration_response(plan.estimate, "exercise_key", mode) for mode in ("short_answer", "proof")}
    job = duration_estimator(carried)
    for mode in ("short_answer", "proof"):
        for authored in (None, 0, -1, 0.5, 3.0, 7.25, 20.0, 45.0):
            assert job("item_new", mode, authored) == pytest.approx(plan.estimate("item_new", mode, authored).minutes)
    assert job("item_new", "derivation", 5.0) is None  # no carried estimate: the bound is refused


def test_an_imported_exercise_is_rechecked_for_independence_when_served(tmp_path):
    """Codex re-review F7: serving an imported exercise from a discriminate
    proposal checked only the import's ownership and status, bypassing the
    serve-time independence recheck every existing item gets."""

    from learnloop.content.authoring import source_exercise_import as SEI
    from learnloop.instructional.exercises import exercise_key
    from learnloop.instructional.practice import imported_exercise_selection

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    span = spans["exercises"][1]
    exercise = {"kind": "source_exercise", "key": exercise_key("ext_text", [span]), "extraction_id": "ext_text",
                "span_ids": [span], "source_id": "src_text", "revision_id": "rev_text", "label": "Exercise 1",
                "page": 9, "statement": "1. An eigenvalue t satisfies 3t + 5 = 20", "relevance": "relevant",
                "rationale": "fits", "provisional": {}}
    _proposal_row(repository, proposal_id="pp_disc", constraints={}, intent="discriminate", exercise=exercise)
    written = SEI.import_source_exercise(paths.root, repository, extraction_id="ext_text", span_ids=[span],
                                         caller="learner", proposal_id="pp_disc", clients=service_clients(FakeServiceLLM()))
    assert written["status"] == "written"
    # The learner read the exercise's own source text since it was proposed.
    repository.insert_source_exposure_event({"context": "reader", "extraction_id": "ext_text", "span_id": span,
                                             "source_id": "src_text"})
    selection = imported_exercise_selection(repository, proposal_id="pp_disc", import_id=written["import_id"],
                                            practice_item_id=written["practice_item_id"], vault=loaded(paths))
    assert selection["served_as"] == "practice"
    assert "source_exposed" in selection["independence"]["reasons"]
    assert selection["label"] == "you've seen this question since it was suggested"
