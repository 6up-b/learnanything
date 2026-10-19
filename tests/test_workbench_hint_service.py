"""Reader workbench RW2b + hints H3: one hint service (spec_reader_workbench_v1 §5.2 "the service", G64; adaptive
hints §10 H3, G-H3, G-H13).

Every workbench hint, its kind and the suggested rung come from
``learnloop.hints`` (``request_hint`` and ``hints.workbench.suggest``,
asserted by monkeypatch); the Reader's packages define no writer, chooser or
map builder (an import-linter contract, and no Reader module names the hint
routes); its rows are ``help_assists`` rows with ``surface = 'workbench'``;
its hint calls use ``hint_writer`` and ``hint_chooser`` only and the check
its own ``workbench_check``. The practice screen's requests, prompts and rows
are unchanged by the surface (its H2b tests pin them). Help events are
salience-only. Fakes only.
"""

from __future__ import annotations

from pathlib import Path
import tomllib

import pytest

from learnloop.attempts import salience_firewall as SF
from learnloop.db.repositories import Repository
from learnloop.hints import service as hint_service
from learnloop.hints import workbench as hint_workbench
from learnloop.reader import workbench as WB
from tests.hint_fakes import receipts
from tests.workbench_help_fakes import call, help_rows, open_problem, run_job, sidecar

ROOT = Path(__file__).resolve().parents[1]


def test_every_workbench_hint_comes_from_request_hint_and_the_suggestion_from_the_service(tmp_path, monkeypatch):
    seen = {"request_hint": 0, "suggest": 0}
    real_request, real_suggest = hint_service.request_hint, hint_workbench.suggest

    def request_spy(*args, **kwargs):
        seen["request_hint"] += 1
        assert args[2].surface == "workbench" and args[2].workbench is not None
        return real_request(*args, **kwargs)

    def suggest_spy(*args, **kwargs):
        seen["suggest"] += 1
        return real_suggest(*args, **kwargs)

    monkeypatch.setattr(hint_service, "request_hint", request_spy)
    monkeypatch.setattr(hint_workbench, "suggest", suggest_spy)
    paths, ctx, _session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    run_job(ctx, call(ctx, "workbench.suggest_help", {"sessionId": wb}))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "request": "feedback",
                                                      "answeredAssistId": hint["assistId"]}))
    assert seen == {"request_hint": 2, "suggest": 1}
    rows = help_rows(paths, wb)
    assert rows and {row["surface"] for row in rows} == {"workbench"}
    assert {row["workbench_session_id"] for row in rows} == {wb}
    assert {row["submission_id"] for row in rows} == {WB.submission_id_for(wb)}


def test_hint_calls_use_hint_writer_and_hint_chooser_and_the_check_its_own_route(tmp_path):
    paths, ctx, _session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    run_job(ctx, call(ctx, "workbench.suggest_help", {"sessionId": wb}))
    run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    assert receipts(paths.sqlite_path, "hint_writer") and receipts(paths.sqlite_path, "hint_chooser")
    assert receipts(paths.sqlite_path, "workbench_check")


def test_the_readers_packages_define_no_writer_chooser_or_map_builder():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    contracts = {entry["id"]: entry for entry in config["tool"]["importlinter"]["contracts"]}
    contract = contracts["workbench-calls-the-one-hint-service"]
    assert set(contract["source_modules"]) == {"learnloop.reader", "learnloop.workbench"}
    assert {"learnloop.hints.writer", "learnloop.hints.chooser", "learnloop.hints.map_builder"} <= set(
        contract["forbidden_modules"])
    # No Reader-side module names a hint route or the chooser's ledger task.
    for path in [*sorted((ROOT / "src/learnloop/reader").glob("*.py")),
                 *sorted((ROOT / "src/learnloop/workbench").glob("*.py"))]:
        text = path.read_text(encoding="utf-8")
        for needle in ('"hint_writer"', '"hint_chooser"', '"hint_choice"', "build_map(", "HintWriterOutputV1"):
            assert needle not in text, (path.name, needle)
    assert "evidence-never-reads-the-workbench" in contracts
    assert "learnloop.workbench" in contracts["evidence-never-reads-the-workbench"]["forbidden_modules"]


def test_a_workbench_request_without_its_steps_is_refused_and_a_practice_one_with_them_too(tmp_path):
    paths, ctx, _session = sidecar(tmp_path)
    vault, repository = ctx.require_vault()
    item = next(iter(vault.practice_items))
    with pytest.raises(hint_service.HintRequestError):
        hint_service.request_hint(vault, repository, hint_service.HintRequestV1(
            practice_item_id=item, session_id="w", submission_id="workbench:w", surface="workbench", taken_level=1))
    context = hint_workbench.WorkbenchHintContext(workbench_session_id="w", steps=())
    with pytest.raises(hint_service.HintRequestError):
        hint_service.request_hint(vault, repository, hint_service.HintRequestV1(
            practice_item_id=item, session_id="s", submission_id="k", workbench=context))
    with pytest.raises(hint_service.HintRequestError):
        hint_service.request_hint(vault, repository, hint_service.HintRequestV1(
            practice_item_id=item, session_id="w", submission_id="workbench:w", surface="workbench",
            workbench=context, taken_level=6))


def test_help_events_are_salience_only(tmp_path):
    paths, ctx, _session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    run_job(ctx, call(ctx, "workbench.suggest_help", {"sessionId": wb}))
    call(ctx, "workbench.set_help_style", {"sessionId": wb, "helpStyle": "guide_me"})
    repository = Repository.attach(paths.sqlite_path)
    events = [event for event in repository.reader_interaction_events(kind="reader_action_invoked")
              if event["payload"].get("event") in WB.HELP_WORKBENCH_EVENTS]
    assert {event["payload"]["event"] for event in events} == set(WB.HELP_WORKBENCH_EVENTS)
    for event in events:
        assert event["payload"]["authority_class"] == SF.SALIENCE_ONLY
        with pytest.raises(SF.SalienceEvidenceRejected):
            SF.reject_salience(event)
