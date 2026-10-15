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

A held grade resolves nothing until it is released; a regrade re-resolves
(when it cites the contract it was read under); replay neither reads nor
writes receipts. The Codex review's four findings (2026-10-15) each have a
fail-first test: an error on another facet, or an unassessed target facet,
is never a recurrence (F1); a grade that cites no contract is censored, never
read against today's rubric (F2); the repair forecaster measures cold outcomes
as their grades stand (F3); a reference that establishes no administration
binds nothing (F4). Fakes only: no network, no paid call.
"""

from __future__ import annotations

import json
from contextlib import closing
from datetime import timedelta

import pytest
from typer.testing import CliRunner

from learnloop.algorithm_versions import METHOD_EXPLICIT_ALGORITHM_VERSION as METHOD_VERSION
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


def _answer(vault, repository, client, *, answer: str, when, presentation_id: str | None = None, **draft):
    """A graded attempt through the live door, bound to a plan presentation when given."""

    draft = AttemptDraft(
        practice_item_id=ITEM,
        learner_answer_md=answer,
        attempt_type="independent_attempt",
        plan_presentation_id=presentation_id,
        **draft,
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


def _diagnosed(tmp_path, *, version: str = "mvp-0.10", config: str = "", method: bool = False):
    """A split vault with one wrong answer diagnosed (its forecast written).

    ``method``: the item is method-explicit (at the method-explicit
    successor), so a regrade reads and cites its assessment contract."""

    paths, vault, repository = split_vault(tmp_path, version=version, config=config)
    if method:
        from tests.test_required_method_grading import _require_method

        _require_method(paths)
        vault = load_vault(paths.root)
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


def test_the_forecast_reads_the_diagnosis_class_and_confidence_once_per_facet_and_pattern(tmp_path):
    from learnloop.diagnosis.forecast_receipts import diagnosis_receipts

    _paths, vault, _repository = split_vault(tmp_path, seed=False)
    attempt = {"id": "att_x", "practice_item_id": ITEM, "learning_object_id": "lo_svd_compute",
               "created_at": "2026-05-02T09:00:00Z"}
    record = {"error_attributions": [
        {"index": 0, "error_type": "slip", "target_evidence_families": ["recall"], "validity_scope": "valid_measurement"},
        {"index": 1, "error_type": "slip", "target_evidence_families": ["recall"], "validity_scope": "valid_measurement"},
        {"index": 2, "error_type": "gap", "target_evidence_families": ["recall"], "validity_scope": "item_contract"},
    ]}
    event = {"registry_match": {"kind": "abstain"}, "history_changed_cause": {"changed": False}}
    values = {"status": "completed", "mode": "live", "proposal": {"event_diagnoses": [
        {**event, "event_index": 0, "causal_class": "transient_execution", "causal_confidence": 0.9},
        {**event, "event_index": 1, "causal_class": "learner_state", "causal_confidence": 0.8},
        {**event, "event_index": 2, "causal_class": "learner_state"},
    ]}}

    receipts = diagnosis_receipts(vault, diagnosis_id="dg_x", attempt=attempt, values=values, record=record)

    # One pattern on one facet is one forecast (the first event's); an error
    # the grader scoped to the item contract is not the learner's.
    [receipt] = receipts
    assert receipt.inputs["event_index"] == 0 and receipt.columns["hypothesis_ref"] == "error_type:slip"
    assert receipt.forecast["prior"] == {"learner_state": pytest.approx(0.1), "transient_execution": pytest.approx(0.9)}
    assert receipt.p == pytest.approx(receipt.forecast["predicted_outcomes"]["pass"]) and receipt.p > 0.5


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
        "intervening": 0, "facets_from": "recorded", "binding": "plan_presentation", "facet_outcome": 0.0,
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


def _cited_by_the_current_grade(repository, attempt_id: str) -> set:
    """The contract versions the winning row of each criterion cites."""

    latest: dict = {}
    with repository.connection() as connection:
        for criterion, cited in connection.execute(
            "SELECT criterion_id, assessment_contract_version_id FROM grading_evidence "
            "WHERE attempt_id = ? AND superseded_at IS NULL ORDER BY created_at, criterion_id, id", (attempt_id,)
        ):
            latest[criterion] = cited
    return set(latest.values())


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

    # A regrade that validates the route releases it: no longer held. This
    # item has no frozen method, so its regrade read the item as it was then
    # and cites no contract: what the grade was read under is not on record,
    # and the forecast is censored (Codex review F2; a method-explicit
    # item's regrade cites its contract and resolves:
    # test_a_regrade_re_resolves_the_forecast).
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(held.attempt_id),
                    runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai",
                    clock=FrozenClock(at(31)))
    assert _cited_by_the_current_grade(repository, held.attempt_id) == {None}
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution["reason"], resolution["attempt_id"]) == (
        "censored", "graded_contract_unknown", held.attempt_id,
    )


def test_a_regrade_re_resolves_the_forecast(tmp_path):
    # A method-explicit item: its regrade cites the contract it read; any
    # other regrade cites none and censors (test_f2_...).
    _paths, vault, repository, diagnosed = _diagnosed(tmp_path, version=METHOD_VERSION, method=True)
    presentation = _present(repository, ITEM, block="blk_regrade", when=at(29))
    nxt = _answer(vault, repository, ReviewFakeClient(), answer=WRONG + " again", when=at(30),
                  presentation_id=presentation)
    assert _diagnosis_resolution(vault, diagnosed.attempt_id)["emission"] == "same_error"

    regrade_attempt(vault, repository, repository.fetch_practice_attempt(nxt.attempt_id),
                    runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai",
                    clock=FrozenClock(at(31)))
    assert None not in _cited_by_the_current_grade(repository, nxt.attempt_id)
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


# -- Codex review (2026-10-15): F1-F4 ------------------------------------------------------------


class _CrossFacetSlipGrader(ReviewFakeClient):
    """Full credit on ``result`` (recall); ``setup`` (compute) marked down
    with the forecast's error type, attributed to compute only."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [
            row.model_copy(update={"points_awarded": 2.0 if row.criterion_id == "result" else 0.0})
            for row in result.criterion_evidence
        ]
        attributions = [
            row.model_copy(update={
                "target_evidence_families": ["compute"], "target_criterion_ids": ["setup"],
                "first_divergence": row.first_divergence.model_copy(update={"criterion_id": "setup"}),
                "resolution_status": "resolved",
            })
            for row in result.error_attributions
        ]
        assert [row.error_type for row in attributions] == ["conceptual_slip"]
        return result.model_copy(update={
            "criterion_evidence": evidence, "rubric_score": 2, "error_attributions": attributions,
        })


#: The reference's final answer by another route: PF-c's final-answer check verifies it.
VERIFYING_ANSWER = "A different route.\nFinal answer: U Sigma V^T"


class _UnassessedRecallSlipOnCompute(ReviewFakeClient):
    """On a verifying answer: ``result`` (recall) half-marked with nothing
    located (PF-c records it unverified: unassessed), ``setup`` (compute)
    marked down with the forecast's error type located on compute."""

    def _blind_grading(self, request, context):
        from learnloop.attempts.blind_grading import BlindErrorAttribution

        result = super()._blind_grading(request, context)
        evidence = [
            row.model_copy(update={"points_awarded": 1.0 if row.criterion_id == "result" else 0.0})
            for row in result.criterion_evidence
        ]
        slip = BlindErrorAttribution.model_validate({
            "error_type": "conceptual_slip",
            "evidence": "The setup diverges here.",
            "first_divergence": {"anchor_kind": "span", "criterion_id": "setup", "quote": "A different route."},
            "target_evidence_families": ["compute"],
            "target_criterion_ids": ["setup"],
            "validity_scope": "valid_measurement",
            "resolution_status": "resolved",
        })
        return result.model_copy(update={
            "criterion_evidence": evidence, "rubric_score": 1, "error_attributions": [slip],
        })


def test_f1_an_error_on_another_facet_is_not_the_forecast_facets_recurrence(tmp_path):
    _paths, vault, repository, diagnosed = _diagnosed(tmp_path)
    [receipt] = _receipts(repository, FR.DIAGNOSIS_NEXT_OBSERVATION)
    pattern = receipt["forecast"]["pattern"]["error_type"]
    assert receipt["facet_id"] == "recall"
    nxt = _answer(vault, repository, _CrossFacetSlipGrader(), answer=WRONG + " again", when=at(30),
                  presentation_id=_present(repository, ITEM, block="blk_cross", when=at(29)))
    with repository.connection() as connection:
        events = [tuple(row) for row in connection.execute(
            "SELECT error_type, repair_plan_json FROM error_events WHERE attempt_id = ?", (nxt.attempt_id,)
        )]
    # The forecast's own pattern shows on the answer, attributed to compute.
    assert [error_type for error_type, _plan in events] == [pattern]
    assert json.loads(events[0][1])["target_evidence_families"] == ["compute"]

    # recall earned full credit; the slip is compute's: recall passed.
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution.get("emission"), resolution.get("facet_outcome")) == (
        "resolved", "pass", 1.0,
    )


def test_f1_an_unassessed_target_facet_censors_whatever_errors_another_facet_shows(tmp_path):
    _paths, vault, repository, diagnosed = _diagnosed(tmp_path)
    [receipt] = _receipts(repository, FR.DIAGNOSIS_NEXT_OBSERVATION)
    nxt = _answer(vault, repository, _UnassessedRecallSlipOnCompute(), answer=VERIFYING_ANSWER, when=at(30),
                  presentation_id=_present(repository, ITEM, block="blk_unassessed", when=at(29)))
    support = repository.latest_blind_grade_record(nxt.attempt_id)["record"]["grading_support"]
    assert support["unverified_criterion_ids"] == ["result"]
    with repository.connection() as connection:
        assert [row[0] for row in connection.execute(
            "SELECT error_type FROM error_events WHERE attempt_id = ?", (nxt.attempt_id,)
        )] == [receipt["forecast"]["pattern"]["error_type"]]

    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution["reason"], resolution["attempt_id"]) == (
        "censored", "facet_unassessed", nxt.attempt_id,
    )


def _edit_result_points(paths, points: int) -> None:
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    path = paths.practice_item_path("linear-algebra", ITEM)
    data = read_yaml(path)
    for criterion in data["grading_rubric"]["criteria"]:
        if criterion["id"] == "result":
            criterion["points"] = points
    data["grading_rubric"]["max_points"] = sum(c["points"] for c in data["grading_rubric"]["criteria"])
    write_yaml(path, data)


def test_f2_a_grade_that_cites_no_contract_is_never_read_against_todays_rubric(tmp_path):
    paths, vault, repository, diagnosed = _diagnosed(tmp_path)
    nxt = _answer(vault, repository, ReviewFakeClient(), answer=RIGHT, when=at(30),
                  presentation_id=_present(repository, ITEM, block="blk_contract", when=at(29)))
    assert _diagnosis_resolution(vault, diagnosed.attempt_id)["emission"] == "pass"

    # The live grade cites the contract it was presented under: a later edit
    # of the rubric changes nothing.
    _edit_result_points(paths, 4)
    vault = load_vault(paths.root)
    assert _diagnosis_resolution(vault, diagnosed.attempt_id)["emission"] == "pass"
    _edit_result_points(paths, 2)
    vault = load_vault(paths.root)

    # A regrade of an item without a frozen method reads the item as it is
    # then and cites no contract: what it was read under is not on record.
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(nxt.attempt_id),
                    runtime=ReadyRuntime(), client=ReviewFakeClient(), grading_source="ai",
                    clock=FrozenClock(at(31)))
    assert _cited_by_the_current_grade(repository, nxt.attempt_id) == {None}
    first = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (first["state"], first["reason"]) == ("censored", "graded_contract_unknown")

    # Editing today's content never rewrites it.
    _edit_result_points(paths, 4)
    vault = load_vault(paths.root)
    assert _diagnosis_resolution(vault, diagnosed.attempt_id) == first


def test_f2_editing_todays_rubric_never_rewrites_a_regraded_self_grade(tmp_path):
    """The review's scenario: a self-grade (it cites its presentation's
    contract) is superseded by an AI regrade of an item without a frozen
    method, so no surviving row cites any contract. The forecast is censored,
    and an edit of the item's rubric afterwards changes nothing (it used to
    compile today's item: pass, then other_error after the edit)."""

    from learnloop.attempts.attempts import SelfGradeInput, complete_self_graded_attempt

    paths, vault, repository, diagnosed = _diagnosed(tmp_path)
    nxt = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=ITEM, learner_answer_md=RIGHT, attempt_type="independent_attempt",
                     plan_presentation_id=_present(repository, ITEM, block="blk_self", when=at(29))),
        SelfGradeInput(criterion_points={"setup": 2, "result": 2}, confidence=4, fatal_errors=[]),
        clock=FrozenClock(at(30)),
    )
    assert _cited_by_the_current_grade(repository, nxt.attempt_id) - {None}
    assert _diagnosis_resolution(vault, diagnosed.attempt_id)["emission"] == "pass"

    regrade_attempt(vault, repository, repository.fetch_practice_attempt(nxt.attempt_id),
                    runtime=ReadyRuntime(), client=ReviewFakeClient(), grading_source="ai",
                    clock=FrozenClock(at(31)))
    with repository.connection() as connection:
        surviving = {row[0] for row in connection.execute(
            "SELECT assessment_contract_version_id FROM grading_evidence "
            "WHERE attempt_id = ? AND superseded_at IS NULL", (nxt.attempt_id,)
        )}
    assert surviving == {None}
    regraded = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (regraded["state"], regraded["reason"]) == ("censored", "graded_contract_unknown")

    _edit_result_points(paths, 4)
    vault = load_vault(paths.root)
    assert _diagnosis_resolution(vault, diagnosed.attempt_id) == regraded


def _measured_prediction(repository, attempt_id: str) -> tuple[float, dict]:
    with repository.connection() as connection:
        receipt = repair_forecasts.repair_receipt(
            connection, attempt={"id": attempt_id}, repair_class_id="rc_stub", hypothesis_ids=(),
            episode=None, task=None, censor_reason="test", success_threshold=0.8,
        )
    return receipt.p, receipt.forecast["measured"]


def _measured_cold_success(tmp_path):
    """One repair cycle whose cold attempt was verified a cold success (class rc_stub)."""

    root, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    primed = _attempt(vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True)
    task = _cold_task(repository)
    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=FrozenClock(NOW + timedelta(days=2)))
    task["context"] = dict(task["context"]) | {"repair_class_id": "rc_stub"}
    record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=FrozenClock(NOW + timedelta(days=2)),
    )
    with repository.connection() as connection:
        assert [tuple(row) for row in connection.execute(
            "SELECT outcome, repair_class_id, cold_attempt_id FROM causal_cold_outcomes "
            "WHERE outcome IN ('cold_success', 'cold_failure')"
        )] == [("cold_success", "rc_stub", cold.attempt_id)]
    p, measured = _measured_prediction(repository, primed.attempt_id)
    assert p == pytest.approx(7 / 9) and measured["class"] == {"successes": 1, "n": 1}
    return root, vault, repository, primed, cold


def test_f3_a_cold_success_regraded_to_failure_is_measured_as_a_failure(tmp_path):
    _root, vault, repository, primed, cold = _measured_cold_success(tmp_path)
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(cold.attempt_id),
                    runtime=ReadyRuntime(), client=ReviewFakeClient(), grading_source="ai",
                    clock=FrozenClock(NOW + timedelta(days=3)))
    assert repository.fetch_practice_attempt(cold.attempt_id)["correctness"] < 0.8

    p, measured = _measured_prediction(repository, primed.attempt_id)
    # One measured failure: the class 0/1, the pooled mean (0 + 1) / (1 + 2).
    assert measured["class"] == {"successes": 0, "n": 1} and measured["pooled"] == {"successes": 0, "n": 1}
    assert p == pytest.approx((0 + 2 * (1 / 3)) / (1 + 2))


def test_f3_a_cold_success_whose_grade_is_now_held_is_not_measured(tmp_path):
    from learnloop.held_grades import held_for_review_attempts
    from tests.helpers import set_algorithm_version
    from learnloop.vault.paths import VaultPaths

    root, vault, repository, primed, cold = _measured_cold_success(tmp_path)
    # The vault moves to the own-route rules; a regrade holds the cold grade.
    set_algorithm_version(VaultPaths(vault.root, vault.config), ROUTE_RULES_VERSION)
    vault = load_vault(root)
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(cold.attempt_id),
                    runtime=ReadyRuntime(), client=DivergentUnlocatedGrader(), grading_source="ai",
                    clock=FrozenClock(NOW + timedelta(days=3)))
    with repository.connection() as connection:
        assert cold.attempt_id in held_for_review_attempts(connection, (cold.attempt_id,))

    p, measured = _measured_prediction(repository, primed.attempt_id)
    # Nothing measured stands: the no-measurement prior.
    assert measured["class"] == {"successes": 0, "n": 0} and measured["pooled"] == {"successes": 0, "n": 0}
    assert p == pytest.approx(0.5)


def _offer(repository, *, item: str, session: str, candidate: str, when) -> str:
    """One returned scheduler offer of ``item`` in ``session`` (a one-candidate slate)."""

    stamp = when.strftime("%Y-%m-%dT%H:%M:%SZ")
    with repository.connection() as connection:
        connection.execute("INSERT OR IGNORE INTO sessions(id, started_at) VALUES (?, ?)", (session, stamp))
        lo = connection.execute(
            "SELECT learning_object_id FROM practice_attempts WHERE practice_item_id = ? LIMIT 1", (ITEM,)
        ).fetchone()[0]
        connection.execute(
            "INSERT INTO scheduler_slates(id, session_id, generated_at, selection_policy, session_context_json, "
            "config_snapshot_json, algorithm_version, created_at, updated_at) "
            "VALUES (?, ?, ?, 'test', '{}', '{}', 'test', ?, ?)",
            (f"slate_{candidate}", session, stamp, stamp, stamp),
        )
        connection.execute(
            "INSERT INTO scheduler_slate_candidates(id, slate_id, practice_item_id, learning_object_id, rank, "
            "returned_rank, was_returned, selected_mode, priority, components_json, algorithm_version, created_at) "
            "VALUES (?, ?, ?, ?, 1, 1, 1, 'test', 1.0, '{}', 'test', ?)",
            (candidate, f"slate_{candidate}", item, lo, stamp),
        )
        connection.commit()
    return candidate


def test_f4_an_answer_to_a_scheduler_offer_resolves_through_it(tmp_path):
    _paths, vault, repository, diagnosed = _diagnosed(tmp_path)
    candidate = _offer(repository, item=ITEM, session="ses_offer", candidate="cand_ok", when=at(29))
    nxt = _answer(vault, repository, ReviewFakeClient(), answer=RIGHT, when=at(30),
                  session_id="ses_offer", scheduler_candidate_id=candidate)
    assert repository.fetch_practice_attempt(nxt.attempt_id)["scheduler_candidate_id"] == candidate

    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution.get("emission"), resolution["binding"]) == (
        "resolved", "pass", "scheduler_candidate",
    )


@pytest.mark.parametrize("reference", ["dangling_candidate", "another_items_candidate", "dangling_probe"])
def test_f4_a_reference_that_establishes_no_administration_censors_the_forecast(tmp_path, reference):
    _paths, vault, repository, diagnosed = _diagnosed(tmp_path)
    nxt = _answer(vault, repository, ReviewFakeClient(), answer=RIGHT, when=at(30))
    # Rows the schema admits (neither column has a foreign key) and an older
    # or out-of-band writer could leave.
    with repository.connection() as connection:
        if reference == "dangling_candidate":
            connection.execute("UPDATE practice_attempts SET scheduler_candidate_id = 'NONEXISTENT_CANDIDATE' "
                               "WHERE id = ?", (nxt.attempt_id,))
        elif reference == "another_items_candidate":
            connection.commit()
            other = _offer(repository, item="pi_svd_compute_002", session="ses_other", candidate="cand_other",
                           when=at(29))
            connection.execute("UPDATE practice_attempts SET scheduler_candidate_id = ?, "
                               "scheduler_slate_id = ?, session_id = 'ses_other' WHERE id = ?",
                               (other, f"slate_{other}", nxt.attempt_id))
        else:
            connection.execute("UPDATE practice_attempts SET probe_presentation_id = 'NONEXISTENT_PRESENTATION' "
                               "WHERE id = ?", (nxt.attempt_id,))
        connection.commit()

    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution["reason"], resolution["attempt_id"]) == (
        "censored", "unbound_attempt", nxt.attempt_id,
    )
    assert resolution["rejected_bindings"]
