"""Saved diagnosis forecasts (owner go-ahead 2026-10-15): forecast receipts.

A completed diagnosis and a scheduled repair cold check each write what they
expect as a ``forecast_receipts`` row (migration 230, a placeholder number) in
the deciding transaction, before the outcome exists. ``learnloop diagnosis
calibration`` resolves each at read time through its exact binding only:

* a diagnosis forecast on the first attempt on its facet that the receipt was
  not written after and that tests the facet unaided, and only when that
  attempt answered a plan presentation (or a probe presentation, or a
  scheduler offer); an unbound one censors it, never a later bound one;
* a repair forecast on its cold task's consumed attempt and the cold
  verification's disposition for it.

A held grade resolves nothing until it is released; a regrade re-resolves;
replay neither reads nor writes receipts. Fakes only: no network, no paid call.
"""

from __future__ import annotations

import json
from contextlib import closing
from datetime import timedelta

import pytest
from typer.testing import CliRunner

from learnloop.attempts.attempts import AttemptDraft, complete_attempt_with_ai_required
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.attempts.regrade import regrade_attempt
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.copies import backup_database
from learnloop.db.repositories import Repository
from learnloop.db.stores import forecast_receipts as receipt_store
from learnloop.db.table_roles import TableRole, role_for_table, tables_for_role
from learnloop.diagnosis.causal_orchestrator import record_cold_verification_from_task
from learnloop.diagnosis import forecast_receipts as repair_forecasts
from learnloop.diagnosis import remediation
from learnloop.diagnosis.split import jobs as jobs_module
from learnloop.evsi_calibration.forecast_report import forecast_calibration_report, resolved_receipts
from learnloop.scheduling import forecast_receipts as FR
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.shadow_rebuild import _learner_state_snapshot
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import ReviewFakeClient
from tests.helpers import NOW
from tests.split_live_helpers import ReadyRuntime, append_config, at, drain_jobs, split_vault, submit
from tests.test_causal_cold_outcomes import _attempt, _setup, _to_treatment
from tests.test_route_rules_in_grader import (
    ALTERNATIVE,
    VERSION as ROUTE_RULES_VERSION,
    DivergentUnlocatedGrader,
    FullCreditGrader,
)

ITEM = "pi_svd_compute_001"
WRONG = "A = U Sigma V wrong"
RIGHT = "A = U Sigma V^T"


# -- helpers ----------------------------------------------------------------------------------


def _present(repository: Repository, item: str, *, block: str, when) -> str:
    """One served plan item (router R2a's receipt), the presentation an answer binds to."""

    served = when.strftime("%Y-%m-%dT%H:%M:%SZ")
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
            "VALUES (?, 'practice', 10, 'hash', ?)",
            (block, served),
        )
        connection.execute(
            "INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
            "VALUES (?, ?, ?, 'chooser', ?)",
            (f"pp_{block}", block, item, served),
        )
        connection.commit()
    return f"pp_{block}"


def _answer(vault, repository, client, *, answer: str, when, presentation_id: str | None = None):
    """A graded attempt through the live door, bound to a plan presentation when given."""

    draft = AttemptDraft(
        practice_item_id=ITEM,
        learner_answer_md=answer,
        attempt_type="independent_attempt",
        plan_presentation_id=presentation_id,
    )
    clock = FrozenClock(when)
    result = complete_attempt_with_ai_required(
        vault, repository, draft, runtime=ReadyRuntime(), ai_client=client, clock=clock
    )
    run_post_attempt_pipeline(vault, repository, result=result, session_id=None, clock=clock)
    return result


def _receipts(repository: Repository, kind: str | None = None) -> list[dict]:
    with repository.connection() as connection:
        return receipt_store.list_receipts(connection, kind=kind)


def _only(rows, kind):
    matching = [(receipt, resolution) for receipt, resolution in rows if receipt["kind"] == kind]
    assert len(matching) == 1, matching
    return matching[0]


def _diagnosed(tmp_path, *, version: str = "mvp-0.10", config: str = ""):
    """A split vault with one wrong answer diagnosed (its forecast written)."""

    paths, vault, repository = split_vault(tmp_path, version=version, config=config)
    client = ReviewFakeClient()
    diagnosed = submit(vault, repository, client, answer=WRONG, when=at(20))
    drain_jobs(vault, repository, client, clock=FrozenClock(at(20.5)))
    return paths, vault, repository, diagnosed


def _diagnosis_resolution(vault, attempt_id: str) -> dict:
    rows = [
        (receipt, resolution)
        for receipt, resolution in resolved_receipts(vault)
        if receipt["kind"] == FR.DIAGNOSIS_NEXT_OBSERVATION and receipt["source_attempt_id"] == attempt_id
    ]
    assert len(rows) == 1, rows
    return rows[0][1]


# -- written in the decision's transaction, before any outcome ---------------------------------


def test_a_completed_diagnosis_writes_its_forecast_in_its_own_transaction(tmp_path, monkeypatch):
    paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    diagnosed = submit(vault, repository, client, answer=WRONG, when=at(20))
    observed: dict = {}
    real = jobs_module.record_diagnosis_forecasts

    def counts(connection, diagnosis_id):
        return (
            connection.execute("SELECT COUNT(*) FROM attempt_diagnoses WHERE id = ?", (diagnosis_id,)).fetchone()[0],
            connection.execute(
                "SELECT COUNT(*) FROM forecast_receipts WHERE decision_ref = ?", (diagnosis_id,)
            ).fetchone()[0],
        )

    def spy(spy_vault, spy_repository, **kwargs):
        written = real(spy_vault, spy_repository, **kwargs)
        with spy_repository.connection() as inside:
            observed["inside"] = counts(inside, kwargs["diagnosis_id"])
        with closing(connect(paths.sqlite_path, read_only=True)) as outside:
            observed["outside"] = counts(outside, kwargs["diagnosis_id"])
        observed["written"] = written
        return written

    monkeypatch.setattr(jobs_module, "record_diagnosis_forecasts", spy)
    drain_jobs(vault, repository, client, clock=FrozenClock(at(20.5)))

    # The receipt and the diagnosis row are one uncommitted transaction.
    assert observed["written"] and observed["inside"] == (1, len(observed["written"]))
    assert observed["outside"] == (0, 0)
    diagnosis = repository.latest_attempt_diagnosis(diagnosed.attempt_id)
    [receipt] = _receipts(repository)
    assert receipt["kind"] == FR.DIAGNOSIS_NEXT_OBSERVATION
    assert receipt["forecaster"] == "diagnoser_causal_class"
    assert receipt["decision_kind"] == "diagnosis" and receipt["decision_ref"] == diagnosis["id"]
    assert receipt["source_attempt_id"] == diagnosed.attempt_id and receipt["facet_id"] == "recall"
    assert receipt["binding_kind"] == FR.PRESENTED_ATTEMPT_ON_FACET and receipt["censor_reason"] is None
    assert receipt["created_at"] == diagnosis["created_at"]
    assert receipt["inputs_as_of"] <= receipt["created_at"]
    assert receipt["versions"]["receipt_shape_version"] == FR.RECEIPT_SHAPE_VERSION
    body = receipt["forecast"]
    # The fake diagnoser names learner_state without a confidence: the default prior.
    assert body["prior"] == {"learner_state": 0.7, "transient_execution": 0.3}
    assert abs(sum(body["predicted_outcomes"].values()) - 1.0) < 1e-6
    assert receipt["p"] == pytest.approx(body["predicted_outcomes"]["pass"])
    assert body["likelihood"]["transient_execution"]["pass"] > body["likelihood"]["learner_state"]["pass"]
    # Nothing after the diagnosed attempt existed when it was written: no outcome.
    assert body["target"]["seen_attempt_ids"] == []
    assert body["target"]["after_attempt_id"] == diagnosed.attempt_id
    assert _diagnosis_resolution(vault, diagnosed.attempt_id) == {
        "state": "pending", "reason": "awaiting_observation", "intervening": 0,
    }


def test_a_failed_receipt_never_breaks_its_diagnosis(tmp_path, monkeypatch):
    def broken(*_args, **_kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(receipt_store, "insert_receipt", broken)
    _paths, vault, repository, diagnosed = _diagnosed(tmp_path)

    assert repository.latest_attempt_diagnosis(diagnosed.attempt_id)["status"] == "completed"
    assert repository.causal_hypotheses_for_attempt(diagnosed.attempt_id)
    assert _receipts(repository) == []


def test_an_unclassed_cause_states_no_expectation(tmp_path):
    class Unknowing(ReviewFakeClient):
        def _diagnosis(self, request, context):
            result = super()._diagnosis(request, context)
            events = [event.model_copy(update={"causal_class": "unknown"}) for event in result.event_diagnoses]
            return result.model_copy(update={"event_diagnoses": events})

    _paths, vault, repository = split_vault(tmp_path)
    client = Unknowing()
    diagnosed = submit(vault, repository, client, answer=WRONG, when=at(20))
    drain_jobs(vault, repository, client, clock=FrozenClock(at(20.5)))

    assert repository.latest_attempt_diagnosis(diagnosed.attempt_id)["status"] == "completed"
    assert _receipts(repository) == []


def test_the_kill_switch_writes_no_receipt(tmp_path):
    off = "[diagnosis]\nforecast_receipts = false"
    _paths, vault, repository, diagnosed = _diagnosed(tmp_path / "diagnosis", config=off)

    assert repository.latest_attempt_diagnosis(diagnosed.attempt_id)["status"] == "completed"
    assert _receipts(repository) == []
    assert forecast_calibration_report(vault)["forecast_receipts"] is False

    root, _vault, repository, misconception_id = _setup(tmp_path / "repair")
    append_config(root, off)
    vault = load_vault(root)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True)
    assert _cold_task(repository)["kind"] == "cold_retry"
    assert _receipts(repository) == []


# -- exact binding through presentations ------------------------------------------------------


def test_the_forecast_resolves_on_the_next_attempt_bound_to_a_presentation(tmp_path):
    _paths, vault, repository, diagnosed = _diagnosed(tmp_path)
    presentation = _present(repository, ITEM, block="blk_next", when=at(29))
    nxt = _answer(vault, repository, ReviewFakeClient(), answer=WRONG + " again", when=at(30),
                  presentation_id=presentation)

    assert repository.fetch_practice_attempt(nxt.attempt_id)["plan_presentation_id"] == presentation
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert resolution == {
        "state": "resolved", "reason": "realized", "emission": "same_error", "attempt_id": nxt.attempt_id,
        "intervening": 0, "facets_from": "recorded", "binding": "plan_presentation",
    }


def test_an_unbound_next_attempt_censors_the_forecast_never_a_later_bound_one(tmp_path):
    _paths, vault, repository, diagnosed = _diagnosed(tmp_path)
    unbound = _answer(vault, repository, ReviewFakeClient(), answer=RIGHT, when=at(30))
    presentation = _present(repository, ITEM, block="blk_later", when=at(39))
    _answer(vault, repository, ReviewFakeClient(), answer=RIGHT + " later", when=at(40),
            presentation_id=presentation)

    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert resolution["state"] == "censored" and resolution["reason"] == "unbound_attempt"
    assert resolution["attempt_id"] == unbound.attempt_id


def test_attempts_visible_when_the_receipt_was_written_are_never_its_observation(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    diagnosed = submit(vault, repository, client, answer=WRONG, when=at(20))
    # Answered (and graded) before the diagnosis ran: visible to its transaction.
    early = _answer(vault, repository, client, answer=RIGHT, when=at(21),
                    presentation_id=_present(repository, ITEM, block="blk_early", when=at(21)))
    drain_jobs(vault, repository, client, clock=FrozenClock(at(22)))

    [receipt] = _receipts(repository, FR.DIAGNOSIS_NEXT_OBSERVATION)
    assert receipt["forecast"]["target"]["seen_attempt_ids"] == [early.attempt_id]
    assert _diagnosis_resolution(vault, diagnosed.attempt_id)["state"] == "pending"

    later = _answer(vault, repository, client, answer=RIGHT + " again", when=at(30),
                    presentation_id=_present(repository, ITEM, block="blk_later", when=at(30)))
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution.get("emission"), resolution["attempt_id"]) == (
        "resolved", "pass", later.attempt_id,
    )


# -- held grades and regrades -----------------------------------------------------------------


def test_a_held_grade_resolves_nothing_until_a_regrade_releases_it(tmp_path):
    _paths, vault, repository, diagnosed = _diagnosed(tmp_path, version=ROUTE_RULES_VERSION)
    presentation = _present(repository, ITEM, block="blk_held", when=at(29))
    held = _answer(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE, when=at(30),
                   presentation_id=presentation)
    record = repository.latest_blind_grade_record(held.attempt_id)["record"]
    assert record["grading_support"]["proof_route_check"]["held_for_review"] is True

    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution["reason"], resolution["attempt_id"]) == (
        "held", "grade_held_for_review", held.attempt_id,
    )
    report = forecast_calibration_report(vault, include_checks=False)
    n = report["kinds"][FR.DIAGNOSIS_NEXT_OBSERVATION]["forecasters"]["diagnoser_causal_class"]["n"]
    assert n["resolved"] == 0 and n["held_for_review"] == {"grade_held_for_review": 1}

    # A regrade that validates the route releases it: now it is an outcome.
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(held.attempt_id),
                    runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai",
                    clock=FrozenClock(at(31)))
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution.get("emission"), resolution["attempt_id"]) == (
        "resolved", "pass", held.attempt_id,
    )


def test_a_regrade_re_resolves_the_forecast(tmp_path):
    _paths, vault, repository, diagnosed = _diagnosed(tmp_path, version=ROUTE_RULES_VERSION)
    presentation = _present(repository, ITEM, block="blk_regrade", when=at(29))
    nxt = _answer(vault, repository, ReviewFakeClient(), answer=WRONG + " again", when=at(30),
                  presentation_id=presentation)
    assert _diagnosis_resolution(vault, diagnosed.attempt_id)["emission"] == "same_error"

    regrade_attempt(vault, repository, repository.fetch_practice_attempt(nxt.attempt_id),
                    runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai",
                    clock=FrozenClock(at(31)))
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution.get("emission")) == ("resolved", "pass")
    # The receipt itself never changed: resolutions are derived at read time.
    [receipt] = [r for r in _receipts(repository) if r["source_attempt_id"] == diagnosed.attempt_id]
    assert receipt["forecast"]["target"]["seen_attempt_ids"] == []


# -- repair expectations --------------------------------------------------------------------


def _cold_task(repository):
    with repository.connection() as connection:
        row = connection.execute("SELECT id FROM followup_tasks WHERE kind = 'cold_retry'").fetchone()
    return dict(repository.followup_task(row["id"]))


def test_a_scheduled_cold_check_records_its_repair_forecast_and_resolves_on_its_task(tmp_path, monkeypatch):
    root, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    observed: dict = {}
    real = repair_forecasts.record_repair_expectation

    def spy(spy_vault, spy_repository, **kwargs):
        written = real(spy_vault, spy_repository, **kwargs)
        query = "SELECT (SELECT COUNT(*) FROM followup_tasks), (SELECT COUNT(*) FROM forecast_receipts)"
        with spy_repository.connection() as inside:
            observed["inside"] = tuple(inside.execute(query).fetchone())
        with closing(connect(root / "state.sqlite", read_only=True)) as outside:
            observed["outside"] = tuple(outside.execute(query).fetchone())
        return written

    monkeypatch.setattr(repair_forecasts, "record_repair_expectation", spy)
    primed = _attempt(vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True)
    task = _cold_task(repository)

    # The task and its forecast are one uncommitted transaction: the primed attempt's.
    assert observed == {"inside": (1, 1), "outside": (0, 0)}

    [receipt] = _receipts(repository, FR.REPAIR_COLD_OUTCOME)
    assert receipt["binding_kind"] == FR.FOLLOWUP_TASK and receipt["followup_task_id"] == task["id"]
    assert receipt["source_attempt_id"] == primed.attempt_id
    assert receipt["decision_kind"] == "cold_retry_schedule" and receipt["censor_reason"] is None
    # Written with the task, in the primed attempt's transaction.
    assert receipt["created_at"] == task["created_at"]
    assert receipt["forecast"]["target"]["success_threshold"] == 0.8
    # No cold outcome measured yet: the pooled Laplace prior.
    assert receipt["p"] == pytest.approx(0.5)
    assert _only(resolved_receipts(vault), FR.REPAIR_COLD_OUTCOME)[1]["reason"] == "awaiting_cold_attempt"

    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=FrozenClock(NOW + timedelta(days=2)))
    assert _only(resolved_receipts(vault), FR.REPAIR_COLD_OUTCOME)[1] == {
        "state": "pending", "reason": "awaiting_cold_verification", "attempt_id": cold.attempt_id,
        "binding": "followup_task",
    }
    task = dict(task)
    task["context"] = dict(task["context"]) | {"repair_class_id": "rc_stub"}
    record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=FrozenClock(NOW + timedelta(days=2)),
    )
    _receipt, resolution = _only(resolved_receipts(vault), FR.REPAIR_COLD_OUTCOME)
    assert resolution == {
        "state": "resolved", "reason": "realized", "emission": "cold_success", "attempt_id": cold.attempt_id,
        "binding": "followup_task", "regraded_since_verification": False,
    }


def test_a_repair_without_an_independent_surface_is_censored_at_birth(tmp_path):
    _root, vault, repository, misconception_id = _setup(tmp_path, extra_items=False)
    treatment = _to_treatment(vault, repository, misconception_id)
    assert treatment["cold_item_id"] is None
    _attempt(vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True)

    [receipt] = _receipts(repository, FR.REPAIR_COLD_OUTCOME)
    assert receipt["binding_kind"] == FR.NO_BINDING
    assert receipt["censor_reason"] == "no_independent_surface"
    assert receipt["followup_task_id"] is None
    assert _only(resolved_receipts(vault), FR.REPAIR_COLD_OUTCOME)[1] == {
        "state": "censored", "reason": "no_independent_surface",
    }


# -- replay ---------------------------------------------------------------------------------


def test_replay_neither_reads_nor_writes_forecast_receipts(tmp_path, monkeypatch):
    root, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True)
    _attempt(vault, repository, treatment["cold_item_id"], clock=FrozenClock(NOW + timedelta(days=2)))
    before = _receipts(repository)
    assert [r["kind"] for r in before] == [FR.REPAIR_COLD_OUTCOME]
    assert role_for_table("forecast_receipts") is TableRole.RECEIPT
    database = root / "state.sqlite"
    without = tmp_path / "without_receipts.sqlite"
    backup_database(database, without)
    with closing(connect(without)) as connection:
        connection.execute("DROP TABLE forecast_receipts")
        connection.commit()

    writers: list[str] = []
    replayed: list[tuple[bool, object]] = []
    real_remediation = remediation.record_remediation_attempt

    def remediation_spy(spy_repository, attempt, **kwargs):
        replayed.append((bool(attempt.get("primed")), kwargs.get("vault")))
        return real_remediation(spy_repository, attempt, **kwargs)

    monkeypatch.setattr(remediation, "record_remediation_attempt", remediation_spy)
    monkeypatch.setattr(repair_forecasts, "record_repair_expectation", lambda *a, **k: writers.append("repair"))
    monkeypatch.setattr(jobs_module, "record_diagnosis_forecasts", lambda *a, **k: writers.append("diagnosis"))
    clock = FrozenClock(NOW + timedelta(days=3))
    rebuild_all_derived_state(vault, repository, clock=clock)
    stripped = Repository.attach(without)
    rebuild_all_derived_state(vault, stripped, clock=clock)

    # Replay re-applies the primed attempt without a vault, so no forecast
    # writer can run; nothing else reaches one.
    assert (True, None) in replayed and all(vault_seen is None for _primed, vault_seen in replayed)
    assert writers == []

    # Replay wrote none (a replayed primed attempt passes no vault) and cleared none.
    assert _receipts(repository) == before
    # And derived state is the same with the receipts gone.
    assert _learner_state_snapshot(repository) == _learner_state_snapshot(stripped)
    with closing(connect(database, read_only=True)) as left, closing(connect(without, read_only=True)) as right:
        for table in sorted(tables_for_role(TableRole.DERIVED)):
            count = f'SELECT COUNT(*) FROM "{table}"'
            assert left.execute(count).fetchone()[0] == right.execute(count).fetchone()[0], table


def test_receipts_are_append_only(tmp_path):
    _paths, _vault, repository, _diagnosed_attempt = _diagnosed(tmp_path)
    with closing(connect(repository.sqlite_path)) as connection:
        for statement in ("UPDATE forecast_receipts SET p = 0.5", "DELETE FROM forecast_receipts"):
            with pytest.raises(Exception, match="append-only"):
                connection.execute(statement)


# -- the report -------------------------------------------------------------------------------


def test_the_calibration_report_on_a_seeded_vault(tmp_path):
    paths, vault, repository, diagnosed = _diagnosed(tmp_path)
    client = ReviewFakeClient()
    nxt = _answer(vault, repository, client, answer=WRONG + " again", when=at(30),
                  presentation_id=_present(repository, ITEM, block="blk_a", when=at(30)))
    drain_jobs(vault, repository, client, clock=FrozenClock(at(30.5)))
    final = _answer(vault, repository, client, answer=RIGHT, when=at(40),
                    presentation_id=_present(repository, ITEM, block="blk_b", when=at(40)))

    result = CliRunner().invoke(app, ["diagnosis", "calibration", "--vault", str(paths.root), "--json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["status"] == "ok" and report["receipts_table"] is True
    block = report["kinds"][FR.DIAGNOSIS_NEXT_OBSERVATION]["forecasters"]["diagnoser_causal_class"]
    # Two diagnoses, two forecasts, resolved on two different attempts.
    assert block["n"]["receipts"] == 2 and block["n"]["decisions"] == 2
    assert block["n"]["resolved"] == 2 and block["n"]["distinct_outcome_attempts"] == 2
    assert block["small_n"] is True
    binary = block["binary"]
    assert binary["event"] == "pass" and binary["pairs"] == 2
    assert binary["observed_rate"] == 0.5
    assert sum(row["n"] for row in binary["bins"]) == 2
    assert block["categorical"]["scored"] == 2 and block["categorical"]["log_loss"] is not None
    assert block["by_causal_class"]["learner_state"]["resolved"] == 2
    outcomes = sorted(
        (resolution["attempt_id"], resolution["emission"]) for receipt, resolution in resolved_receipts(vault)
        if receipt["kind"] == FR.DIAGNOSIS_NEXT_OBSERVATION
    )
    assert outcomes == sorted([(nxt.attempt_id, "same_error"), (final.attempt_id, "pass")])
    with repository.connection() as connection:
        checks = connection.execute("SELECT COUNT(*) FROM voi_forecasts").fetchone()[0]
    assert report["kinds"].get(FR.CHECK_OUTCOME, {"receipts": 0})["receipts"] == checks

    text = CliRunner().invoke(app, ["diagnosis", "calibration", "--vault", str(paths.root)])
    assert text.exit_code == 0, text.output
    assert "diagnoser_causal_class: 2 receipts, 2 resolved on 2 attempts (the honest n)" in text.output
    assert "P(pass)" in text.output


def test_the_report_reads_a_vault_without_receipts_as_empty(tmp_path):
    paths, vault, repository = split_vault(tmp_path)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("DROP TABLE forecast_receipts")
        connection.commit()

    report = forecast_calibration_report(load_vault(paths.root), include_checks=False)
    assert report["receipts_table"] is False and report["kinds"] == {}
