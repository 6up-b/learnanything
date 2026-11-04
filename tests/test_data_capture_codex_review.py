"""Data capture A1-A6: the Codex review's findings F1-F8, each reproduced first.

F1 ordinary Reader activity still got a cold label; F2 a measurement consumed before its window; F3 rejected
probes' likelihood inputs; F4 goal expansion enrolling retroactively; F5 reading time counted twice; F6 the report
comparing different endpoints across arms; F7 a lost measurement reported as due; F8 receipts committed apart from
their decisions. Fakes only; no network.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import sqlite3
from types import SimpleNamespace

import pytest

from learnloop import delayed_completion as DC
from learnloop.adaptive_difficulty.report import _offer_outcomes
from learnloop.clock import parse_utc
from learnloop.daily_plan import measurement as M
from learnloop.data_capture import prefilter as PF
from learnloop.db.repositories import Repository
from learnloop.data_capture import reading_exposures as RE
from learnloop.db.stores import ad_receipts
from learnloop.db.stores import data_capture as store
from learnloop.diagnosis import voi_stopping as voi
from learnloop.ops import capture_report as CR
from learnloop.router import outcomes as RO
from learnloop.router.first_delayed_success import trajectories
from learnloop.scheduling.intent.serving import check_date
from learnloop.scheduling.scheduler import OfferTrace
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault
from tests.test_data_capture_a2_measurement import _answer, _arranged_wait, _due_measurement, _events, _objectives
from tests.test_data_capture_a3_time_metric import _attempt as _timed_attempt
from tests.test_data_capture_a3_time_metric import _reader_visit
from tests.test_router_outcomes import A, B, LO, _attempt, _decision

T0 = datetime(2026, 5, 18, 12, 0, tzinfo=UTC)  # a Monday
AS_OF = "2026-08-01T00:00:00Z"


def _at(**delta):
    return (T0 + timedelta(**delta)).strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture
def world(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    vault.goals = []
    return vault, Repository(paths.sqlite_path)


def _section_read(repository, *, at, lo=LO, key="sec"):
    """What the sweep freezes for a completed Reader section (``adaptive_difficulty.reading``)."""

    with repository.atomic(), repository.connection() as connection:
        ad_receipts.insert_reading_opportunity(connection, {
            "protection_epoch": "e", "opportunity_key": f"reading:{key}:{lo}", "kind": "reading", "subkind": "section_read",
            "source_table": "reader_section_progress", "source_id": f"x/{key}",
            "source_written_at": parse_utc(at).isoformat(timespec="microseconds").replace("+00:00", "Z"),
            "learning_object_id": lo, "facet_doses": {"f": 1.0}, "mapping_version": "m", "sweep": "serve", "sweep_ref": "s",
            "swept_at": at,
        })


def _metric(world, lo=LO):
    vault, repository = world
    with repository.connection() as connection:
        found, facts = trajectories(connection, vault, success_correctness=0.8, as_of=AS_OF,
                                    reader_exposures=RE.read(connection, vault, repository))
    return next(row for row in found if row.learning_object_id == lo)


def _derive(repository, version=RO.OUTCOME_VERSION_V3):
    with repository.connection() as connection:
        return {row["decision_id"]: row for row in RO.derive_router_outcomes(
            connection, outcome_version=version,
            reader_exposures=store.reading_receipts(connection) if version == RO.OUTCOME_VERSION_V3 else None)}


# -- F1: ordinary Reader activity is an exposure for every reader of the definition ----------------------------


class _View:
    """The material view's reads, over plain rows."""

    def __init__(self, *, draws, attempts, opportunities=(), source_exposures=()):
        self._draws, self._attempts, self._opportunities, self._exposures = draws, attempts, opportunities, source_exposures

    def dose_rows(self, _connection):
        return list(self._draws)

    def reveals(self, _connection):
        return []

    def attempts(self, _connection):
        return list(self._attempts)

    def reading_opportunities(self, _connection):
        return list(self._opportunities)

    def rows(self, _connection, table, *_args, **_kwargs):
        return list(self._exposures) if table == "source_exposure_events" else []


def _ad_outcome(*, opportunities=(), source_exposures=()):
    answered = _at(days=2, minutes=30)
    event = SimpleNamespace(attempt_id="a1", created_at=answered, served_at=answered, eligible=True, category=2,
                            learning_object_id=LO, practice_item_id=B)
    draw = {"id": "dr", "row_kind": "draw", "created_at": _at(minutes=0), "learning_object_ids": [LO], "forecast_p": 0.7,
            "chosen_variant": "extra", "propensities": {"none": 0.5, "extra": 0.5}, "detail": {}}
    view = _View(draws=[draw], attempts=[{"learning_object_id": LO, "created_at": _at(minutes=1), "practice_item_id": A},
                                         {"learning_object_id": LO, "created_at": answered, "practice_item_id": B}],
                 opportunities=opportunities, source_exposures=source_exposures)
    snapshot = SimpleNamespace(events=SimpleNamespace(attempts=[event], opportunities=[]))
    return _offer_outcomes(None, snapshot, view=view, delayed_definition=True)["extra"][0].outcome


def test_f1_a_completed_section_makes_the_next_answer_warm_for_router_ad_and_the_time_metric(world):
    """Reproduced first: the router's index had no section-completion record: ``completed``, 1.0, 172800."""

    _vault, repository = world
    _decision(repository, "d1", created_at=_at(minutes=0))
    _attempt(repository, "a0", item=A, created_at=_at(minutes=1), correctness=0.4, candidate="c1")   # Monday
    _section_read(repository, at=_at(days=2))                                                        # Wednesday
    _attempt(repository, "a1", item=B, created_at=_at(days=2, minutes=30), correctness=1.0, session="s2")

    outcome = _derive(repository)["d1"]
    assert (outcome["r_cold_status"], outcome["r_cold_value"]) == ("pending", None)
    assert json.loads(outcome["detail_json"])["r_cold_skip_reasons"] == {"insufficient_delay": 1}

    opportunity = {"learning_object_id": LO, "source_written_at": _at(days=2)}
    assert _ad_outcome(opportunities=[opportunity]) is None, "the same history: AD calls it warm too"
    assert _ad_outcome() == 1.0, "and without the reading both call it delayed"

    metric = _metric(world)
    assert not metric.reached and metric.attempts == 2, "the warm answer is no first delayed success"


def test_f1_a_section_read_does_not_change_the_predecessors_outcome(world):
    _vault, repository = world
    _decision(repository, "d1", created_at=_at(minutes=0))
    _attempt(repository, "a0", item=A, created_at=_at(minutes=1), correctness=0.4, candidate="c1")
    _attempt(repository, "a1", item=B, created_at=_at(days=2, minutes=30), correctness=1.0, session="s2")
    before = _derive(repository, RO.OUTCOME_VERSION)["d1"]
    _section_read(repository, at=_at(days=2))
    assert _derive(repository, RO.OUTCOME_VERSION)["d1"] == before


def test_f1_a_reading_long_before_the_presentation_leaves_it_delayed(world):
    _vault, repository = world
    _decision(repository, "d1", created_at=_at(minutes=0))
    _attempt(repository, "a0", item=A, created_at=_at(minutes=1), correctness=0.4, candidate="c1")
    _section_read(repository, at=_at(days=2))
    _attempt(repository, "a1", item=B, created_at=_at(days=4), correctness=1.0, session="s2")
    outcome = _derive(repository)["d1"]
    assert (outcome["r_cold_status"], outcome["r_cold_value"]) == ("observed", 1.0)
    assert json.loads(outcome["coldness_candidates_json"])[0]["last_lo_exposure_kind"] == "reading"
    assert _metric(world).reached


def test_f1_ad_reads_a_span_exposure_on_the_lo_as_the_router_does(world):
    """A second passage view the same day writes no receipt (one per LO per day); the router read it, AD did not."""

    exposure = {"entity_type": "learning_object", "entity_id": LO, "created_at": _at(days=2)}
    assert _ad_outcome(source_exposures=[exposure]) is None
    _vault, repository = world
    _decision(repository, "d1", created_at=_at(minutes=0))
    _attempt(repository, "a0", item=A, created_at=_at(minutes=1), correctness=0.4, candidate="c1")
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_exposure_events(id, context, extraction_id, span_id, entity_type, entity_id, created_at)"
            " VALUES ('e1', 'reader', 'x', 's', 'learning_object', ?, ?)", (LO, _at(days=2)))
        connection.commit()
    _attempt(repository, "a1", item=B, created_at=_at(days=2, minutes=30), correctness=1.0, session="s2")
    assert _derive(repository)["d1"]["r_cold_status"] == "pending"


# -- F2: a measurement can satisfy the decision it measures ------------------------------------------------------


def _second_decision(env, source_id):
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO router_decisions SELECT 'd2', 'k2', decision_kind, surface, mode, policy, algorithm_version, log_version,"
            " session_id, parent_decision_id, scheduler_slate_id, controller_decision_id, snapshot_hash, design, seed,"
            " candidates_json, exclusions_json, candidate_count, chosen_ref, chosen_practice_item_id, chosen_learning_object_id,"
            " chosen_scheduler_candidate_id, propensity, propensity_kind, learner_pick, fallback, mixture_weights_json,"
            " model_distributions_json, sensor_answers_json, question_set_version, model_ids_json, card_hash,"
            " similar_decision_ids_json, latency_ms, cost_usd, detail_json, ? FROM router_decisions WHERE id = ?",
            (env.now_iso(), source_id))
        M.record(env.vault, env.repository, connection, decision_id="d2", decision_kind="plan_interrupt",
                 frozen=M.freeze_followup("lo_diag", support=["insert_now", "continue_current"]), arm=M.ARM_WAIT,
                 clock=env.clock)
    return _objectives(env)["d2"]


def _due_hint(env, commitment_id):
    with env.repository.connection() as connection:
        return connection.execute(
            "SELECT due_hint FROM commitment_versions WHERE commitment_id = ?", (commitment_id,)).fetchone()[0]


def _hint_instant(hint):
    return check_date(SimpleNamespace(due_hint=hint, created_at=""), default_days=1)[0]


def test_f2_a_check_already_due_is_not_shared_with_a_decision_it_cannot_measure(tmp_path):
    """Reproduced first: shared, then answered an hour later: satisfied, but the decision's ITT rejects it."""

    env, _decision_id, objective = _due_measurement(tmp_path)
    second = _second_decision(env, objective["decision_id"])
    assert second["measurement"] == M.ARRANGED and second["commitment_id"] != objective["commitment_id"]
    assert second["practice_item_id"] != objective["practice_item_id"], "the earlier decision keeps its check"
    assert _hint_instant(_due_hint(env, second["commitment_id"])) >= env.clock.now() + timedelta(seconds=DC.MIN_DELAY_SECONDS)


def test_f2_a_check_due_after_the_window_opens_is_still_shared(tmp_path):
    env, _decision_id, objective = _arranged_wait(tmp_path)
    second = _second_decision(env, objective["decision_id"])
    assert second["measurement"] == M.SHARED and second["commitment_id"] == objective["commitment_id"]


@pytest.mark.parametrize("hour", [0, 6, 23])
@pytest.mark.parametrize("days", [0.0, 0.2, 1.0, 3.5])
def test_f2_the_date_is_never_before_the_delay_whatever_truncation_does(hour, days):
    """Reproduced first: 0.2 days from an evening truncated to tomorrow's date: an hour away."""

    now = datetime(2026, 5, 19, hour, 30, tzinfo=UTC)
    due = _hint_instant(M._due_iso(now, days))
    assert due >= now + timedelta(seconds=DC.MIN_DELAY_SECONDS)
    assert due - timedelta(days=1) < max(now + timedelta(days=days), now + timedelta(seconds=DC.MIN_DELAY_SECONDS)), (
        "and the first such day: no later than the interval asks")


def test_f2_a_new_check_with_a_short_interval_is_dated_past_the_window(tmp_path, monkeypatch):
    monkeypatch.setattr("learnloop.delayed_checks.due_days", lambda *_a, **_k: (0.05, "retrievability"))
    env, _decision_id, objective = _arranged_wait(tmp_path)
    assert _hint_instant(_due_hint(env, objective["commitment_id"])) >= env.clock.now() + timedelta(seconds=DC.MIN_DELAY_SECONDS)


def _warm_answer(env, objective, *, warm_item="pi_diag_easy"):
    """The learner practises the LO, then answers the due check minutes later: on their own, and warm."""

    lo = objective["learning_object_id"]
    _answer(env, warm_item, lo)
    env.clock.advance(5)
    _answer(env, objective["practice_item_id"], lo)
    env.clock.advance(1)


def test_f2_a_warm_answer_consumes_the_check_but_keeps_the_measurement_duty(tmp_path):
    """Reproduced first: ``answered`` written, no qualifying outcome and no later question."""

    env, decision_id, objective = _due_measurement(tmp_path)
    warm = next(i.id for i in env.vault.practice_items.values()
                if i.learning_object_id == objective["learning_object_id"] and i.id != objective["practice_item_id"])
    _warm_answer(env, objective, warm_item=warm)
    M.settle(env.vault, env.repository, clock=env.clock)
    events = _events(env)[decision_id]
    assert "answered" not in {event["state"] for event in events}
    early = next(event for event in events if event["reason"] == M.ANSWER_NOT_DELAYED)
    assert early["state"] == "unavailable" and early["attempt_id"]
    replacement = json.loads(early["detail_json"])["replacement_commitment_id"]
    assert replacement and replacement != objective["commitment_id"]
    assert _hint_instant(_due_hint(env, replacement)) >= env.clock.now() + timedelta(seconds=DC.MIN_DELAY_SECONDS)
    with env.repository.connection() as connection:
        state = RO.fold_measurement(objective, store.measurement_events(connection)[decision_id])
    assert state["state"] == "scheduled" and state["replacement_commitment_id"] == replacement
    # Idempotent: the duty is not arranged twice.
    assert M.settle(env.vault, env.repository, clock=env.clock) == 0
    with env.repository.connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM commitments WHERE created_action = 'test_me_later'").fetchone()[0] == 2


def test_f2_the_replacement_answered_cold_completes_the_measurement(tmp_path):
    env, decision_id, objective = _due_measurement(tmp_path)
    lo = objective["learning_object_id"]
    warm = next(i.id for i in env.vault.practice_items.values()
                if i.learning_object_id == lo and i.id != objective["practice_item_id"])
    _warm_answer(env, objective, warm_item=warm)
    M.settle(env.vault, env.repository, clock=env.clock)
    early = next(event for event in _events(env)[decision_id] if event["reason"] == M.ANSWER_NOT_DELAYED)
    item = json.loads(early["detail_json"])["practice_item_id"]
    env.clock.advance(60 * 24 * 30)
    M.settle(env.vault, env.repository, clock=env.clock)
    assert "due" in {event["state"] for event in _events(env)[decision_id] if event["reason"].startswith(M.REPLACEMENT)}
    _answer(env, item, lo)
    env.clock.advance(1)
    M.settle(env.vault, env.repository, clock=env.clock)
    events = _events(env)[decision_id]
    assert [event["state"] for event in events if event["state"] == "answered"] == ["answered"]
    assert RO.fold_measurement(objective, events)["state"] == "answered"
    assert json.loads(_outcome(env, decision_id)["detail_json"])["measurement"]["state"] == "answered"
    assert _outcome(env, decision_id)["r_cold_status"] == "observed"


def _outcome(env, decision_id):
    return _derive(env.repository)[decision_id]


def test_f2_a_cold_answer_is_answered_as_before(tmp_path):
    env, decision_id, objective = _due_measurement(tmp_path)
    _answer(env, objective["practice_item_id"], objective["learning_object_id"])
    env.clock.advance(1)
    M.settle(env.vault, env.repository, clock=env.clock)
    events = _events(env)[decision_id]
    assert "answered" in {event["state"] for event in events}
    assert not [event for event in events if event["reason"] == M.ANSWER_NOT_DELAYED]


# -- F3: a rejected probe keeps its likelihood inputs --------------------------------------------------------------


def test_f3_every_evaluated_probe_keeps_its_forecast_in_the_receipt_only(tmp_path, monkeypatch):
    """Reproduced first: rejected candidates reached the receipt as summaries, no likelihood rows."""

    from tests.test_voi_stopping import _build, _minutes, _probe_vault

    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 10_000.0)  # nothing pays: every candidate is rejected
    trace = OfferTrace()
    queue = _build(vault, repository, trace=trace)
    (decision,) = [d for d in trace.voi_decisions if d["site"] == voi.SITE_PROBE_EPISODE]
    assert decision["decision"] == voi.STOP and decision["candidate_count"] >= 2
    upstream = json.loads(PF.today_offer_material(trace, offered=[item.practice_item_id for item in queue],
                                                  versions={}).parts["upstream"])
    (kept,) = [row for row in upstream["candidate_forecasts"] if row["site"] == voi.SITE_PROBE_EPISODE]
    assert len(kept["candidates"]) == decision["candidate_count"]
    for candidate in kept["candidates"]:
        assert candidate["decision"] == voi.STOP
        assert candidate["forecast"]["likelihood"] and candidate["forecast"]["prior"]
        assert candidate["minutes"]["minutes"] > 0
    # The decision's inline receipt keeps its shape: the forecasts live in the content-addressed part.
    assert "forecast" not in decision["candidates"][-1]
    material = PF.today_offer_material(trace, offered=[item.practice_item_id for item in queue], versions={})
    assert material.versions["likelihood_rows_hash"]


def test_f3_a_build_with_no_valued_probe_keeps_no_forecasts():
    assert voi.candidate_forecasts([]) == []


# -- F4: membership is read from the contract, not from today's scope ----------------------------------------------


def _goal(vault, *, concept):
    return SimpleNamespace(id="g1", due_at="2026-12-01T00:00:00Z", created_at=_at(days=-30),
                           facet_scope=SimpleNamespace(concepts=[concept], facets=[]))


def _contract(repository, version, at, *, concepts):
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO goal_contract_versions(id, goal_id, version, contract_json, content_hash, support_hash,"
            " contract_schema_version, change_class, author, created_at) VALUES (?,?,?,?,?,?,1,?,'learner',?)",
            (f"gc{version}", "g1", version, json.dumps({"due_at": f"due-{version}", "facet_scope": {"concepts": concepts, "facets": []}}),
             f"c{version}", "s", "confirm" if version == 1 else "support_change", at))
        connection.commit()


def test_f4_an_objective_a_later_contract_added_enrolls_when_it_was_added(world):
    """Reproduced first: v2 added the LO on June 1, it was enrolled on May 1, and a May 22 success cited v1."""

    vault, repository = world
    concept = vault.learning_objects[LO].concept
    vault.goals = [_goal(vault, concept=concept)]
    _contract(repository, 1, "2026-05-01T00:00:00Z", concepts=["elsewhere"])
    _contract(repository, 2, "2026-06-01T00:00:00Z", concepts=["elsewhere", concept])
    _timed_attempt(repository, "a1", at="2026-05-10T12:00:00Z", correctness=0.4)
    _timed_attempt(repository, "a2", at="2026-05-22T12:00:00Z", session="s2")
    row = _metric(world)
    assert (row.enrollment_source, row.enrolled_at) == ("goal", "2026-06-01T00:00:00Z")
    assert not row.reached and row.attempts_before_enrollment == 2, "those attempts came before the goal held it"
    assert row.goal["contract_version_id"] == "gc2"
    _timed_attempt(repository, "a3", at="2026-06-20T12:00:00Z", session="s3")
    row = _metric(world)
    assert row.reached and row.success_at == "2026-06-20T12:00:00Z" and row.goal["contract_version_id"] == "gc2"


def test_f4_a_success_before_the_contract_covered_it_never_cites_that_contract(world):
    vault, repository = world
    concept = vault.learning_objects[LO].concept
    vault.goals = [_goal(vault, concept=concept)]
    _contract(repository, 1, "2026-05-01T00:00:00Z", concepts=["elsewhere"])
    _contract(repository, 2, "2026-06-01T00:00:00Z", concepts=["elsewhere", concept])
    from learnloop.clock import FrozenClock
    from learnloop.curriculum import commitments as C

    C.create_commitment(repository, action="help_me_remember", intent_text="mine",
                        targets=[{"target_kind": "learning_object", "target_ref": LO, "role": "required"}],
                        depth_preset="keep_in_touch", client_idempotency_key="l", reason="r",
                        clock=FrozenClock(parse_utc("2026-05-05T00:00:00Z")))
    _timed_attempt(repository, "a1", at="2026-05-10T12:00:00Z", correctness=0.4)
    _timed_attempt(repository, "a2", at="2026-05-22T12:00:00Z", session="s2")
    row = _metric(world)
    assert row.enrollment_source == "commitment" and row.reached
    assert row.goal is None, "v1, in force at the success, never covered it"


def test_f4_a_contract_that_dropped_the_objective_is_not_pinned(world):
    vault, repository = world
    concept = vault.learning_objects[LO].concept
    vault.goals = [_goal(vault, concept=concept)]
    _contract(repository, 1, "2026-05-01T00:00:00Z", concepts=[concept])
    _contract(repository, 2, "2026-06-01T00:00:00Z", concepts=["elsewhere"])
    _timed_attempt(repository, "a1", at="2026-05-10T12:00:00Z", correctness=0.4)
    row = _metric(world)
    assert (row.enrollment_source, row.enrolled_at) == ("goal", "2026-05-01T00:00:00Z"), "an enrollment is a historical fact"
    assert row.goal is None, "unfinished at the report: v2, in force now, does not hold it"


def test_f4_a_goal_whose_contract_never_covered_the_lo_does_not_enroll_it(world):
    vault, repository = world
    vault.goals = [_goal(vault, concept=vault.learning_objects[LO].concept)]
    _contract(repository, 1, "2026-05-01T00:00:00Z", concepts=["elsewhere"])
    _timed_attempt(repository, "a1", at="2026-05-10T12:00:00Z", correctness=0.4)
    row = _metric(world)
    assert (row.enrollment_source, row.enrolled_at) == ("first_exposure", "2026-05-10T12:00:00Z")
    assert row.goal is None


# -- F5: an interval is counted once ---------------------------------------------------------------------------------


def _reading_block(repository, block, *, start, end, lo=LO):
    with repository.connection() as connection:
        connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, short_circuit_reason, content_hash, created_at)"
                           " VALUES (?, 'reading', 30, '', 'h', ?)", (block, start))
        connection.executemany(
            "INSERT INTO attention_block_events(id, block_id, event_ordinal, kind, created_at) VALUES (?,?,?,?,?)",
            [(f"{block}_s", block, 1, "block_started", start), (f"{block}_e", block, 2, "block_ended", end)])
        connection.commit()
    _decision(repository, block, created_at=start, kind="plan_block", item=None, candidate=None)  # its key names the block
    with repository.atomic(), repository.connection() as connection:
        store.insert_objective(connection, {
            "decision_id": block, "decision_kind": "plan_block", "objective_version": "v", "learning_object_id": lo,
            "source": "reading_section", "scope_json": "[]", "arm": "reading", "support_json": "[]", "measurement": "natural", "pick_json": "{}",
            "created_at": start,
        })


def _exposed_in_visit(repository, at, lo=LO, key="e1"):
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_exposure_events(id, context, extraction_id, span_id, entity_type, entity_id, created_at)"
            " VALUES (?, 'reader', 'x', 's', 'learning_object', ?, ?)", (key, lo, at))
        connection.commit()


def test_f5_a_reading_block_inside_a_reader_visit_counts_its_minutes_once(world):
    """Reproduced first: a single 30-minute reading produced 60 elapsed minutes."""

    _vault, repository = world
    _timed_attempt(repository, "a1", at=_at(days=-5), correctness=0.4, latency=None)
    _reader_visit(repository, "v1", opened=_at(days=1), closed=_at(days=1, minutes=30), active=600)
    _exposed_in_visit(repository, _at(days=1, minutes=10))
    _reading_block(repository, "b1", start=_at(days=1), end=_at(days=1, minutes=30))
    row = _metric(world)
    assert row.elapsed_minutes == pytest.approx(30.0)
    assert row.active_minutes == pytest.approx(10.0), "active time is untouched"
    assert row.plan_reading_elapsed_seconds == 0.0


def test_f5_a_block_running_past_the_visit_counts_the_union(world):
    _vault, repository = world
    _timed_attempt(repository, "a1", at=_at(days=-5), correctness=0.4, latency=None)
    _reader_visit(repository, "v1", opened=_at(days=1, minutes=10), closed=_at(days=1, minutes=30), active=600)
    _exposed_in_visit(repository, _at(days=1, minutes=20))
    _reading_block(repository, "b1", start=_at(days=1), end=_at(days=1, minutes=40))
    assert _metric(world).elapsed_minutes == pytest.approx(40.0)


def test_f5_a_block_with_no_reader_timing_still_counts(world):
    _vault, repository = world
    _timed_attempt(repository, "a1", at=_at(days=-5), correctness=0.4, latency=None)
    _reading_block(repository, "b1", start=_at(days=1), end=_at(days=1, minutes=25))
    assert _metric(world).elapsed_minutes == pytest.approx(25.0)


def test_f5_two_overlapping_blocks_count_their_union(world):
    _vault, repository = world
    _timed_attempt(repository, "a1", at=_at(days=-5), correctness=0.4, latency=None)
    _reading_block(repository, "b1", start=_at(days=1), end=_at(days=1, minutes=20))
    _reading_block(repository, "b2", start=_at(days=1, minutes=10), end=_at(days=1, minutes=30))
    assert _metric(world).elapsed_minutes == pytest.approx(30.0)


# -- F6: the report compares one endpoint across arms ----------------------------------------------------------------


def _row(decision_id, *, status, detail):
    return {"decision_id": decision_id, "r_cold_status": status, "detail_json": json.dumps(detail)}


def test_f6_every_arm_is_reported_on_its_frozen_objective_and_action_outcomes_apart(world, monkeypatch):
    """Reproduced first: common ITT ``observed`` under the practice arm, the report said ``pending``."""

    vault, repository = world
    itt = {"arm": "practice", "r_cold_status": "observed", "r_cold_value": 1.0}
    derived = [
        _row("practice_with_objective", status="pending", detail={"objective_itt": itt}),
        _row("reading", status="observed", detail={"arm": "reading"}),
        _row("waiting", status="pending", detail={"arm": "wait"}),
        _row("insert_with_objective", status="observed", detail={"objective_itt": {"arm": "insert", "r_cold_status": "pending"}}),
        _row("plain_offer", status="observed", detail={}),
        _row("no_objective", status="not_applicable", detail={"no_outcome": "no_frozen_objective"}),
    ]
    monkeypatch.setattr(RO, "derive_router_outcomes", lambda *_a, **_k: derived)
    with repository.connection() as connection:
        section = CR.outcome_section(connection, vault, repository)
    assert section["r_cold_by_arm"] == {"practice": {"observed": 1}, "reading": {"observed": 1}, "wait": {"pending": 1},
                                        "insert": {"pending": 1}}
    assert section["action_bound_r_cold"] == {"pending": 1, "observed": 2}
    assert section["no_frozen_objective"] == 1


def test_f6_the_text_report_names_both(world, monkeypatch):
    vault, repository = world
    monkeypatch.setattr(RO, "derive_router_outcomes", lambda *_a, **_k: [
        _row("x", status="pending", detail={"objective_itt": {"arm": "practice", "r_cold_status": "observed"}})])
    with repository.connection() as connection:
        report = CR.build_report(connection, vault, repository, as_of=AS_OF, success_correctness=0.8)
    text = "\n".join(CR.lines(report))
    assert "objective, by arm" in text and "action-bound" in text and "practice: {'observed': 1}" in text


# -- F7: a lost measurement stays visible; a later offer restores it -------------------------------------------------


def _state_event(state, at, reason=""):
    return {"state": state, "reason": reason, "created_at": at, "detail_json": "{}"}


def test_f7_a_replaced_check_reads_unavailable_not_due():
    """Reproduced first: due followed by replacement still returned ``state: due``."""

    objective = {"measurement": "arranged"}
    state = RO.fold_measurement(objective, [_state_event("due", "2026-05-20T00:00:00Z"),
                                             _state_event("unavailable", "2026-05-21T00:00:00Z", "check_replaced")])
    assert state["state"] == "unavailable" and state["reasons"] == ["check_replaced"]


def test_f7_a_later_offer_restores_it_and_an_answer_is_terminal():
    objective = {"measurement": "arranged"}
    lost = [_state_event("due", "2026-05-20T00:00:00Z"),
            _state_event("unavailable", "2026-05-21T00:00:00Z", "plan_minutes_exhausted")]
    offered = [*lost, _state_event("offered", "2026-05-22T00:00:00Z")]
    assert RO.fold_measurement(objective, offered)["state"] == "offered"
    # A reason is still on the record: the day it could not be held happened.
    assert RO.fold_measurement(objective, offered)["reasons"] == ["plan_minutes_exhausted"]
    answered = [*offered, _state_event("answered", "2026-05-22T00:05:00Z"),
                _state_event("unavailable", "2026-05-23T00:00:00Z", "check_replaced")]
    assert RO.fold_measurement(objective, answered)["state"] == "answered"


def test_f7_times_of_different_precision_fold_in_time_order():
    objective = {"measurement": "arranged"}
    state = RO.fold_measurement(objective, [
        _state_event("unavailable", "2026-05-20T00:00:00.500000Z", "later_in_the_second"),
        _state_event("due", "2026-05-20T00:00:00Z")])
    assert state["state"] == "unavailable"


def test_f7_the_report_counts_a_replaced_check_as_unavailable(tmp_path):
    from learnloop.curriculum import commitments as C

    env, decision_id, objective = _due_measurement(tmp_path)
    M.settle(env.vault, env.repository, clock=env.clock)
    env.clock.advance(60)
    C.create_commitment(env.repository, action="help_me_remember", intent_text="keep it",
                        targets=[{"target_kind": "legacy_practice_item", "target_ref": objective["practice_item_id"],
                                  "role": "required"}],
                        depth_preset="keep_in_touch", client_idempotency_key="own", reason="r", clock=env.clock)
    M.settle(env.vault, env.repository, clock=env.clock)
    assert [event["state"] for event in _events(env)[decision_id]] == ["due", "unavailable"]
    with env.repository.connection() as connection:
        section = CR.measurement_section(connection)
    assert section["states_by_arm"][M.ARM_WAIT] == {"unavailable": 1}
    assert section["unavailable_reasons"] == {M.CHECK_REPLACED: 1}


# -- F8: a receipt commits with its decision ---------------------------------------------------------------------------


def _spy_on_commit(monkeypatch, path, seen):
    """At the receipt's write, whether a second connection can already read its decision (it committed apart)."""

    real = PF.record

    def spy(connection, *, decision_id, **kwargs):
        other = sqlite3.connect(path)
        try:
            seen.append(other.execute("SELECT COUNT(*) FROM router_decisions WHERE id = ?", (decision_id,)).fetchone()[0])
        finally:
            other.close()
        return real(connection, decision_id=decision_id, **kwargs)

    monkeypatch.setattr(PF, "record", spy)


def test_f8_an_offers_receipt_commits_in_its_decisions_transaction(tmp_path, monkeypatch):
    """Reproduced first: the decision was already committed when its receipt began its own transaction."""

    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    from tests.helpers import seed_due_item

    paths = create_basic_vault(tmp_path / "vault")
    seed_due_item(paths)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    session = METHOD_REGISTRY["start_session"].handler(
        ctx, METHOD_REGISTRY["start_session"].params_model.model_validate({"availableMinutes": 25}))
    seen: list[int] = []
    _spy_on_commit(monkeypatch, paths.sqlite_path, seen)
    spec = METHOD_REGISTRY["get_today_queue"]
    spec.handler(ctx, spec.params_model.model_validate({"sessionId": session["sessionId"]}))
    _vault, repository = ctx.require_vault()
    assert seen == [0], "no other connection sees the decision before its receipt is written"
    with repository.connection() as connection:
        offer = connection.execute(
            "SELECT id FROM router_decisions WHERE decision_kind = 'today_offer' ORDER BY created_at DESC").fetchone()
        assert PF.read(connection, offer[0]) is not None


def test_f8_a_crash_before_the_transaction_ends_loses_both_or_neither(tmp_path):
    from learnloop.router import decisions as RD

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    row = _staged_row()

    class Stop(BaseException):
        pass

    def crash(_connection):
        raise Stop

    with pytest.raises(Stop):
        RD.record_decision(repository, row, alongside=crash)
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM router_decisions WHERE id = ?", (row["id"],)).fetchone()[0] == 0

    def link(connection):
        PF.record(connection, decision_id=row["id"], decision_kind="staged_p2",
                  material=PF.decision_row_material(row, versions={}), config=vault.config, at=row["created_at"])

    assert RD.record_decision(repository, row, alongside=link) is True
    assert RD.record_decision(repository, row, alongside=crash) is False, "a repeated key writes nothing and runs nothing"
    with repository.connection() as connection:
        assert PF.read(connection, row["id"]) is not None


def _staged_row():
    from learnloop.db.stores.router import ROUTER_LOG_VERSION

    return {
        "id": "staged1", "receipt_key": "staged_p2:staged1", "decision_kind": "staged_p2", "surface": "live", "mode": "staged",
        "policy": "staged", "algorithm_version": "mvp-0.44", "log_version": ROUTER_LOG_VERSION, "session_id": None,
        "snapshot_hash": "h", "candidates_json": "[]", "exclusions_json": "{}", "candidate_count": 0, "chosen_ref": "x",
        "propensity": 1.0, "propensity_kind": "deterministic", "learner_pick": 0, "detail_json": "{}", "created_at": _at(minutes=0),
    }


def test_f8_the_staged_decisions_receipt_commits_with_it(tmp_path, monkeypatch):
    """Reproduced first: ``staged_p2`` used the same two transactions."""

    from learnloop.scheduling import controller_cutover as CC

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    row = _staged_row()
    monkeypatch.setattr("learnloop.router.decisions.build_staged_p2_decision", lambda *_a, **_k: row)
    monkeypatch.setattr(CC.sp, "ladder_eligibility", lambda *_a, **_k: {})
    seen: list[int] = []
    _spy_on_commit(monkeypatch, paths.sqlite_path, seen)
    CC._log_staged_decision(
        vault, repository, SimpleNamespace(chosen_candidate_ref=None, trace={}, decision_id="staged1"),
        snapshot=SimpleNamespace(session_id=None), signals=None,
        canonical=SimpleNamespace(to_state="x", reason="r", terminal=False),
        action=SimpleNamespace(authority="a", veto_reason=None), run_id="r", commitment_id=None, clock=None)
    assert seen == [0]
    with repository.connection() as connection:
        assert PF.read(connection, "staged1") is not None
