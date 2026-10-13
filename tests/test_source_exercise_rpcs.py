"""S1: the pick RPCs for textbook exercises, and the owner-run harvest and verify commands."""
from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.instructional.exercises import exercise_candidates
from learnloop.practice_index.retrieval import find_practice
from learnloop.practice_index.usage import USAGE_TASK
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, call, loaded


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
