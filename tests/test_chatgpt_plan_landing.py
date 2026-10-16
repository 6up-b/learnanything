"""The ChatGPT plan's served workspace composed with main's diagnosis input provenance and saved forecasts.

The plan stage (no migration) serves a snapshot diagnosis's as-of export
itself and reports exactly the files it handed out (``workspace_activity()``).
Main's diagnoser maps that report to export entries through
``provenance.served_entries(manifest.entries, ...)`` and records them with the
diagnosis, in the ``jobs._persist`` transaction that also writes the
diagnosis row and its forecast receipts. This drives the real plan client,
against the fake Responses server, through the async diagnosis job (the same
door a vault with ``active_provider = "chatgpt"`` would use) and pins that:

* the receipt names exactly the files the plan served, as entries;
* the export part of the diagnosis's write-time record is built from the
  plan's own report and names the answer of the one history attempt it
  served and nothing else; the stored record is complete and joins it to
  what the inline context showed (snapshot mode is the ``exact`` context
  plus the export);
* the record, the row and the forecasts are one transaction: another
  connection sees none of them until it commits.
"""

from __future__ import annotations

from contextlib import closing
import json

import pytest

from learnloop.ai.chatgpt_plan.session import PlanSession
from learnloop.ai.providers.chatgpt_plan import ChatGPTPlanProviderClient
from learnloop.clock import FrozenClock
from learnloop.config.schema import ChatGPTPlanProviderConfig
from learnloop.db.connection import connect
from learnloop.diagnosis.split import jobs as jobs_module
from learnloop.diagnosis.split import provenance

from tests.chatgpt_plan_fakes import Reply, fake_chatgpt, sign_in
from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import at, drain_jobs, split_vault, submit
from tests.test_chatgpt_plan_workspace import _diagnosis_answer
from tests.test_forecast_receipts import WRONG


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    monkeypatch.setattr("learnloop.ai.providers.chatgpt_plan._sleep", lambda _seconds: None)


@pytest.fixture
def server():
    with fake_chatgpt() as fake:
        sign_in(PlanSession(), fake)
        yield fake


def _counts(connection, diagnosis_id: str) -> tuple[int, int, int]:
    return (
        connection.execute("SELECT COUNT(*) FROM attempt_diagnoses WHERE id = ?", (diagnosis_id,)).fetchone()[0],
        connection.execute(
            "SELECT COUNT(*) FROM text_write_provenance WHERE kind = 'diagnosis' AND record_id = ?", (diagnosis_id,)
        ).fetchone()[0],
        connection.execute(
            "SELECT COUNT(*) FROM forecast_receipts WHERE decision_ref = ?", (diagnosis_id,)
        ).fetchone()[0],
    )


def _members(values) -> set:
    """A record field's members: a mapping's keys, or a list's items (dicts as JSON)."""

    return {json.dumps(value, sort_keys=True) if isinstance(value, dict) else value for value in values}


def test_a_snapshot_diagnosis_on_the_plan_records_what_it_served_with_its_row_and_forecasts(
    server, tmp_path, monkeypatch
):
    paths, vault, repository = split_vault(tmp_path, config='[diagnosis]\nhistory_mode = "snapshot"')
    wrong = submit(vault, repository, ReviewFakeClient(), answer=WRONG, when=at(20))

    server.default_reply = lambda body: Reply(events=_diagnosis_answer(body))
    plan = ChatGPTPlanProviderClient("chatgpt", ChatGPTPlanProviderConfig(
        model="gpt-test-fast", base_url=server.base_url, timeout_seconds=10))
    observed: dict = {}
    real = jobs_module.record_diagnosis_forecasts

    def spy(spy_vault, spy_repository, **kwargs):
        written = real(spy_vault, spy_repository, **kwargs)
        with spy_repository.connection() as inside:
            observed["inside"] = _counts(inside, kwargs["diagnosis_id"])
        with closing(connect(paths.sqlite_path, read_only=True)) as outside:
            observed["outside"] = _counts(outside, kwargs["diagnosis_id"])
        observed["written"] = written
        return written

    real_snapshot_record = provenance.snapshot_record

    def snapshot_spy(entries, opened):
        record = real_snapshot_record(entries, opened)
        observed["snapshot"] = (list(opened) if opened is not None else None, record)
        return record

    monkeypatch.setattr(jobs_module, "record_diagnosis_forecasts", spy)
    monkeypatch.setattr(provenance, "snapshot_record", snapshot_spy)
    drain_jobs(vault, repository, plan, clock=FrozenClock(at(20.5)))

    diagnosis = repository.latest_attempt_diagnosis(wrong.attempt_id)
    assert diagnosis["status"] == "completed" and diagnosis["history_mode"] == "snapshot"
    assert diagnosis["provider"] == "chatgpt"
    # What the plan served, in order: the index, then one failed attempt.
    served = plan.workspace_activity()
    assert served is not None and served[0] == "INDEX.md" and len(served) == 2
    assert served[1].startswith("attempts/") and "att_02_svd_fail" in served[1]
    assert len(server.requests) == 3  # two rounds of workspace calls, then the answer

    # The receipt: the served files as export entries (served_entries).
    with repository.connection() as connection:
        (retrieval,) = connection.execute(
            "SELECT retrieval_json FROM diagnosis_context_receipts WHERE diagnosis_id = ?", (diagnosis["id"],)
        ).fetchone()
        (complete, inputs_json, reasons_json) = connection.execute(
            "SELECT complete, inputs_json, incomplete_reasons_json FROM text_write_provenance "
            "WHERE kind = 'diagnosis' AND record_id = ?", (diagnosis["id"],)
        ).fetchone()
    snapshot = json.loads(retrieval)["snapshot"]
    assert snapshot["opened"] == served and snapshot["opened_reported"] is True
    assert snapshot["served"] == {"how": "entries", "entry_count": 2, "paths": sorted(served)}
    assert snapshot["file_count"] > 2

    # The export part of the record: built from the plan's own report, it
    # names the one history answer the plan handed out and nothing else.
    opened, exported = observed["snapshot"]
    assert opened == served
    assert exported.complete and set(exported.inputs.as_json()["answers"]) == {"att_02_svd_fail"}
    # The stored record: complete, and it joins the export part to what the
    # inline (exact) context showed.
    assert complete == 1 and json.loads(reasons_json) == []
    stored = json.loads(inputs_json)
    assert "att_02_svd_fail" in stored["answers"] and wrong.attempt_id in stored["answers"]
    for kind, values in exported.inputs.as_json().items():
        assert _members(values) <= _members(stored.get(kind) or ()), kind

    # One transaction: the record, the row and the forecasts, invisible to
    # another connection until it commits.
    assert observed["written"]
    assert observed["inside"] == (1, 1, len(observed["written"]))
    assert observed["outside"] == (0, 0, 0)
    with closing(connect(paths.sqlite_path, read_only=True)) as after:
        assert _counts(after, diagnosis["id"]) == (1, 1, len(observed["written"]))
