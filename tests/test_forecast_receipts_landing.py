"""Saved diagnosis forecasts composed with diagnosis input provenance on main.

The forecasts stage (built as migration 230, landed as 206) and the
provenance landing (migration 205) both write inside the diagnosis
transaction (``jobs._persist``), and both read a regrade's re-minted error
events. These tests pin how they compose:

* the diagnosis's write-time record, its row and its forecast receipts are
  one transaction: another connection sees none of them until it commits;
* a forecast receipt that fails rolls back only its own savepoint: the
  diagnosis and its provenance record still commit;
* the forecast resolver reads the outcome attempt's error events as they
  stand now. A regrade re-mints them and records which ids replaced which in
  ``error_event_lineage`` (provenance's Q9, the authority on what a retired
  id stands for); the resolver never counts a retired event as a recurrence,
  and a re-minted event of the same pattern still is one.
"""

from __future__ import annotations

from contextlib import closing

from learnloop.algorithm_versions import METHOD_EXPLICIT_ALGORITHM_VERSION as METHOD_VERSION
from learnloop.attempts.regrade import regrade_attempt
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.migrate import discover_migrations
from learnloop.db.stores import forecast_receipts as receipt_store
from learnloop.db.table_roles import TableRole, role_for_table
from learnloop.diagnosis.split import jobs as jobs_module
from learnloop.scheduling import forecast_receipts as FR

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import ReadyRuntime, at, drain_jobs, split_vault, submit
from tests.test_forecast_receipts import (
    WRONG,
    ITEM,
    _answer,
    _diagnosed,
    _diagnosis_resolution,
    _present,
    _receipts,
)
from tests.test_route_rules_in_grader import FullCreditGrader


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


def test_the_renumbered_migration_and_its_table_role():
    migrations = {migration.version: migration.name for migration in discover_migrations()}
    assert migrations[205] == "write_provenance"
    assert migrations[206] == "forecast_receipts"
    # Reader workbench RW2a's 207 landed after it.
    assert max(migrations) >= 206
    assert role_for_table("forecast_receipts") is TableRole.RECEIPT
    assert role_for_table("text_write_provenance") is TableRole.RAW_LEDGER
    assert role_for_table("error_event_lineage") is TableRole.RAW_LEDGER


def test_the_provenance_record_the_diagnosis_and_its_forecasts_commit_as_one_transaction(tmp_path, monkeypatch):
    paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    diagnosed = submit(vault, repository, client, answer=WRONG, when=at(20))
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

    monkeypatch.setattr(jobs_module, "record_diagnosis_forecasts", spy)
    drain_jobs(vault, repository, client, clock=FrozenClock(at(20.5)))

    # Inside the diagnosis transaction: the record, the row and the receipts;
    # outside it, nothing of the three until it commits.
    assert observed["written"]
    assert observed["inside"] == (1, 1, len(observed["written"]))
    assert observed["outside"] == (0, 0, 0)
    diagnosis = repository.latest_attempt_diagnosis(diagnosed.attempt_id)
    with closing(connect(paths.sqlite_path, read_only=True)) as after:
        assert _counts(after, diagnosis["id"]) == (1, 1, len(observed["written"]))
        (complete,) = after.execute(
            "SELECT complete FROM text_write_provenance WHERE kind = 'diagnosis' AND record_id = ?",
            (diagnosis["id"],),
        ).fetchone()
    assert complete == 1
    [receipt] = _receipts(repository)
    assert receipt["kind"] == FR.DIAGNOSIS_NEXT_OBSERVATION and receipt["decision_ref"] == diagnosis["id"]


def test_a_failed_forecast_receipt_keeps_the_diagnosis_and_its_provenance_record(tmp_path, monkeypatch):
    def broken(*_args, **_kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(receipt_store, "insert_receipt", broken)
    paths, vault, repository, diagnosed = _diagnosed(tmp_path)

    diagnosis = repository.latest_attempt_diagnosis(diagnosed.attempt_id)
    assert diagnosis["status"] == "completed"
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        assert _counts(connection, diagnosis["id"]) == (1, 1, 0)
    assert _receipts(repository) == []


def _events(repository, attempt_id: str) -> list[str]:
    return sorted(str(event["id"]) for event in repository.raw_error_events_for_attempt(attempt_id))


def _lineage(repository, attempt_id: str) -> list[tuple[str | None, str]]:
    with repository.connection() as connection:
        return [
            (row[0], row[1])
            for row in connection.execute(
                "SELECT error_event_id, replaces_error_event_id FROM error_event_lineage WHERE attempt_id = ? "
                "ORDER BY created_at, id",
                (attempt_id,),
            )
        ]


def test_the_resolver_reads_the_regraded_events_the_lineage_names_never_a_retired_one(tmp_path):
    # A method-explicit item, so each regrade cites the contract it read and
    # the forecast resolves on it (any other regrade censors the forecast:
    # test_forecast_receipts' F2 tests).
    _paths, vault, repository, diagnosed = _diagnosed(tmp_path, version=METHOD_VERSION, method=True)
    presentation = _present(repository, ITEM, block="blk_lineage", when=at(29))
    nxt = _answer(vault, repository, ReviewFakeClient(), answer=WRONG + " again", when=at(30),
                  presentation_id=presentation)
    first_events = _events(repository, nxt.attempt_id)
    assert first_events
    assert _diagnosis_resolution(vault, diagnosed.attempt_id)["emission"] == "same_error"

    # 1. The same grade again: the events are re-minted, the lineage names
    # the new ids for the old ones, and the re-minted event of the same
    # pattern is still the recurrence.
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(nxt.attempt_id),
                    runtime=ReadyRuntime(), client=ReviewFakeClient(), grading_source="ai",
                    clock=FrozenClock(at(31)))
    reminted = _events(repository, nxt.attempt_id)
    assert reminted and not set(reminted) & set(first_events)
    assert {replaced for _event, replaced in _lineage(repository, nxt.attempt_id)} == set(first_events)
    assert {event for event, _replaced in _lineage(repository, nxt.attempt_id)} == set(reminted)
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution.get("emission")) == ("resolved", "same_error")

    # 2. Full credit: the regrade retires every event with no replacement
    # (lineage rows with no error_event_id), and the resolver, reading the
    # events as they stand, finds no recurrence: the facet passed.
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(nxt.attempt_id),
                    runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai",
                    clock=FrozenClock(at(32)))
    assert _events(repository, nxt.attempt_id) == []
    retired = [replaced for event, replaced in _lineage(repository, nxt.attempt_id) if event is None]
    assert sorted(retired) == reminted
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution.get("emission")) == ("resolved", "pass")
