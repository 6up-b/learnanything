"""UX Phase 4 (practice and feedback) composed with provenance and saved forecasts on main.

The stage's "I think I was right" (``trigger_regrade`` with a reason) regrades
in place through the ordinary learner-blind regrade, which on main also writes
diagnosis input provenance's records (migration 205) and which saved diagnosis
forecasts (migration 206) read at resolution time. These tests pin how they
compose, through the sidecar RPC itself:

* a contest's regrade records its grading provenance and the error-event
  lineage like any regrade, and the reason never reaches the grader;
* the regrade re-resolves a saved forecast the contested attempt resolves;
* a contest the regrade does not uphold is queued for review with a
  ``review_flag`` head of the same authority: not a hold, so the forecast
  still resolves on the grade as it stands;
* a held grade shows "held for review" in the feedback bundle and resolves no
  forecast, by the one held predicate; a contest whose regrade releases it
  clears both;
* what feedback says a grade stands on (round 3 F9: ``answered_source``,
  contract | live | unrecorded) agrees with what the forecast resolver reads:
  a regrade that cites its contract shows that contract and resolves the
  forecast; one that cites none shows the content it read in its own
  response only (``live``), ``unrecorded`` on any later read, and censors the
  forecast (``graded_contract_unknown``);
* round 4's one reveal coverage (``reveal_coverage``) governs the readers that
  judge or serve by reveals; provenance's question record asks whether the
  solution was ever shown before the question, so a routine display (a
  feedback display, or round 5's versioned self-grade disclosure) counts
  there after its coverage has ended;
* the serve-time revalidation (rounds 5 and 6) defers a cold check on the
  direct opens (``open_queue_item``, ``get_practice_item`` with a session)
  only while a routine display covers it; any other reveal keeps main's
  serving behaviour (round 6 withdrew round 5's typed refusal);
* round 7's waiting plan composes with the router's receipts: a waiting
  boundary writes nothing (no block, no plan presentation, no router
  decision, no stop), and the item served once the hold lifts binds to its
  plan presentation as any served plan item does;
* under router R2b's mixture (round 8), a stop the mixture draws while other
  work is feasible stays a logged stop (its ``router_decisions`` row, chosen
  ref and exact propensity on the plan's stop receipt) even when a held cold
  check lifts later today, and a plan waiting for coverage asks no model and
  writes no ``router_decisions`` row until the hold lifts.

Fakes only; no network, no paid call.
"""

from __future__ import annotations

import pytest

from learnloop.algorithm_versions import METHOD_EXPLICIT_ALGORITHM_VERSION as METHOD_VERSION
from learnloop.held_grades import held_attempt_ids
from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import ReadyRuntime, at
from tests.test_diagnosis_input_provenance import _question, world  # noqa: F401 - world is a fixture
from tests.test_ux_phase4_feedback import ctx  # noqa: F401 - ctx is a fixture
from tests.test_forecast_receipts import ITEM, WRONG, _answer, _diagnosed, _diagnosis_resolution, _present
from tests.test_route_rules_in_grader import ALTERNATIVE, DivergentUnlocatedGrader, FullCreditGrader
from tests.test_route_rules_in_grader import VERSION as ROUTE_RULES_VERSION

REASON = "I did transpose V; the last line says so"


def _context(paths, monkeypatch, client):
    """The sidecar on the vault, its grading provider the fake ``client``."""

    import learnloop_sidecar.handlers  # noqa: F401 - populates the registry
    import learnloop_sidecar.handlers.ai_providers as providers
    from learnloop_sidecar.context import SidecarContext

    monkeypatch.setattr(providers, "ready_grading_provider",
                        lambda vault, override=None: ("fake", ReadyRuntime(), client))
    monkeypatch.setattr(providers, "grading_source_for_provider", lambda name: "ai")
    context = SidecarContext()
    context.load(paths.root)
    return context


def _contest(context, attempt_id: str, contest_id: str) -> dict:
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY["trigger_regrade"]
    return spec.handler(context, spec.params_model.model_validate(
        {"attemptId": attempt_id, "learnerReason": REASON, "contestId": contest_id}
    ))


def _regrade_provenance(repository, attempt_id: str) -> list[dict]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT writer, complete FROM text_write_provenance WHERE kind = 'grading' AND record_id = ? "
            "ORDER BY created_at, id",
            (attempt_id,),
        ).fetchall()
    return [dict(row) for row in rows if row["writer"] == "regrade"]


def _lineage(repository, attempt_id: str) -> list[tuple]:
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT error_event_id, replaces_error_event_id FROM error_event_lineage WHERE attempt_id = ?",
            (attempt_id,),
        ).fetchall()]


def _events(repository, attempt_id: str) -> list[str]:
    return sorted(str(event["id"]) for event in repository.raw_error_events_for_attempt(attempt_id))


def _pending_reviews(repository) -> list[str]:
    return [row["attempt_id"] for row in repository.pending_grade_reviews()]


def test_a_contest_regrade_records_provenance_and_re_resolves_the_forecast(tmp_path, monkeypatch):
    # A method-explicit item, so the regrade cites the contract it read and
    # the forecast resolves on it (test_forecast_receipts' F2 tests).
    paths, vault, repository, diagnosed = _diagnosed(tmp_path, version=METHOD_VERSION, method=True)
    presentation = _present(repository, ITEM, block="blk_contest", when=at(29))
    contested = _answer(vault, repository, ReviewFakeClient(), answer=WRONG + " again", when=at(30),
                        presentation_id=presentation)
    old_events = _events(repository, contested.attempt_id)
    assert old_events
    assert _diagnosis_resolution(vault, diagnosed.attempt_id)["emission"] == "same_error"
    assert _regrade_provenance(repository, contested.attempt_id) == []

    grader = FullCreditGrader()
    context = _context(paths, monkeypatch, grader)
    bundle = _contest(context, contested.attempt_id, "contest_upheld")

    assert bundle["contest"] == {"recorded": True, "regraded": True, "reviewRequested": False}
    assert grader.prompts and not any(REASON in prompt for prompt in grader.prompts)
    # Provenance's records: the regrade's grading record (Q14) and, for the
    # events full credit retired, lineage rows with no replacement (Q9).
    assert len(_regrade_provenance(repository, contested.attempt_id)) == 1
    assert _events(repository, contested.attempt_id) == []
    assert sorted(old for new, old in _lineage(repository, contested.attempt_id) if new is None) == old_events
    # The saved forecast reads the regraded attempt as it stands now, on the
    # contract the regrade cites; feedback shows that same contract.
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution.get("emission")) == ("resolved", "pass")
    assert bundle["answeredSource"] == "contract"
    assert _pending_reviews(repository) == []


def test_a_contest_the_regrade_does_not_uphold_is_flagged_never_held(tmp_path, monkeypatch):
    paths, vault, repository, diagnosed = _diagnosed(tmp_path, version=METHOD_VERSION, method=True)
    presentation = _present(repository, ITEM, block="blk_flag", when=at(29))
    contested = _answer(vault, repository, ReviewFakeClient(), answer=WRONG + " again", when=at(30),
                        presentation_id=presentation)
    old_events = _events(repository, contested.attempt_id)

    grader = ReviewFakeClient()
    context = _context(paths, monkeypatch, grader)
    bundle = _contest(context, contested.attempt_id, "contest_flagged")

    assert bundle["contest"] == {"recorded": True, "regraded": True, "reviewRequested": True}
    assert not any(REASON in prompt for prompt in grader.prompts)
    assert _pending_reviews(repository) == [contested.attempt_id]
    # The regrade still wrote provenance's records: its grading record, and
    # lineage naming the re-minted events for the replaced ones.
    assert len(_regrade_provenance(repository, contested.attempt_id)) == 1
    reminted = _events(repository, contested.attempt_id)
    assert reminted and not set(reminted) & set(old_events)
    assert {old for _new, old in _lineage(repository, contested.attempt_id)} == set(old_events)
    # A review flag keeps the grade's authority: it is not a hold.
    assert bundle["heldForReview"] is False
    assert held_attempt_ids(repository, [contested.attempt_id]) == frozenset()
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution.get("emission")) == ("resolved", "same_error")


def test_a_held_grade_resolves_nothing_until_a_contest_regrade_releases_it(tmp_path, monkeypatch):
    paths, vault, repository, diagnosed = _diagnosed(tmp_path, version=ROUTE_RULES_VERSION)
    presentation = _present(repository, ITEM, block="blk_held_contest", when=at(29))
    held = _answer(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE, when=at(30),
                   presentation_id=presentation)

    from learnloop_sidecar.handlers.serializers import feedback_bundle

    # One predicate: the feedback says "held for review" and the forecast is held.
    assert feedback_bundle(vault, repository, held.attempt_id)["heldForReview"] is True
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution["reason"]) == ("held", "grade_held_for_review")

    context = _context(paths, monkeypatch, FullCreditGrader())
    bundle = _contest(context, held.attempt_id, "contest_release")

    # The regrade validated the route: released, upheld, nothing to review.
    assert bundle["heldForReview"] is False
    assert bundle["contest"] == {"recorded": True, "regraded": True, "reviewRequested": False}
    assert len(_regrade_provenance(repository, held.attempt_id)) == 1
    # No longer held. This item has no frozen method, so the regrade cites no
    # contract and the forecast is censored, exactly as a plain regrade's
    # (test_forecast_receipts::test_a_held_grade_resolves_nothing_until_a_regrade_releases_it).
    resolution = _diagnosis_resolution(vault, diagnosed.attempt_id)
    assert (resolution["state"], resolution["reason"]) == ("censored", "graded_contract_unknown")
    # Feedback agrees (round 3 F9): the content the regrade read, in its own
    # response only, and unrecorded on any later read; never inferred.
    assert bundle["answeredSource"] == "live"
    assert feedback_bundle(vault, repository, held.attempt_id)["answeredSource"] == "unrecorded"


def test_a_routine_display_marks_a_later_question_solution_seen_beyond_its_coverage(world):
    """Diagnosis input provenance's one reveal reader
    (``text_gaps.provenance._revealed_before``) asks whether the learner could
    have seen an item's solution before asking about it: ever, not within a
    window. A routine full-answer display (round 4's one coverage,
    ``reveal_coverage``) is such a reveal, and it keeps counting there after
    its coverage has ended for admissibility, auto-prime and serving."""

    from datetime import UTC, datetime

    from learnloop.attempts.reveal_ledger import record_feedback_answer_display_reveal
    from learnloop.clock import FrozenClock
    from learnloop.diagnosis.text_gaps.provenance import question_record
    from learnloop.reveal_coverage import routine_row_covers

    _question(world, "q_after_display", context="practice", item="pi_own", contract="acv_own", record=False)
    with world.repository.connection() as connection:
        assert question_record(connection, "q_after_display").inputs.solution_items == frozenset()

    receipt = record_feedback_answer_display_reveal(
        world.repository, attempt_id="att_own", practice_item_id="pi_own", display_id="display_landing",
        clock=FrozenClock(datetime(2026, 9, 21, 9, 0, tzinfo=UTC)),
    )
    asked_at = "2026-09-25T09:00:00Z"  # the question's stamp (tests.test_diagnosis_input_provenance._question)
    assert not routine_row_covers(receipt.recorded_at, asked_at)  # its coverage ended days before

    with world.repository.connection() as connection:
        assert question_record(connection, "q_after_display").inputs.solution_items == frozenset({"pi_own"})

    # Round 5's self-grade disclosure: a versioned JSON identity in the same
    # basis column. The reader filters by item and stamp only, so a v2 row
    # marks the question exactly as the feedback display did.
    from learnloop.attempts.reveal_ledger import (
        disclosure_identity,
        frozen_trace_hash,
        record_self_grade_disclosure_display,
    )

    _question(world, "q_after_disclosure", context="practice", item="pi_key", record=False)
    with world.repository.connection() as connection:
        assert question_record(connection, "q_after_disclosure").inputs.solution_items == frozenset()
    disclosed = record_self_grade_disclosure_display(
        world.repository, practice_item_id="pi_key", submission_id="sub_landing",
        frozen_hash=frozen_trace_hash("a rotation preserves lengths", None), display_id="display_v2",
        clock=FrozenClock(datetime(2026, 9, 21, 9, 0, tzinfo=UTC)),
    )
    assert not routine_row_covers(disclosed.recorded_at, asked_at)
    with world.repository.connection() as connection:
        row = connection.execute(
            "SELECT source_kind, basis FROM reveal_events WHERE practice_item_id = 'pi_key'"
        ).fetchone()
        assert disclosure_identity(dict(row))["display"] == "display_v2"
        assert question_record(connection, "q_after_disclosure").inputs.solution_items == frozenset({"pi_key"})


def test_a_cold_check_on_a_direct_open_is_served_as_on_main_unless_a_routine_display_covers_it(ctx):
    """Round 6 (ruling 2) withdrew round 5's typed refusal: nothing raises
    ``cold_check_unavailable`` any more. On the direct opens, a due cold retry
    after a NON-routine reveal (a tutor answer after the item's last attempt,
    before the task was created) is served exactly as on main: no error, the
    task is not deferred, the session serve opens the cold administration, and
    submit then primes the answer (main's own handling of a primed cold retry).
    Only routine-display coverage defers it (``revalidate_cold_check``):
    ``open_queue_item`` then opens no administration and the task stops being
    due until the coverage ends."""

    from learnloop.attempts.attempts import AUTO_PRIME_REVEAL_THRESHOLD, reveal_total_for_submission
    from learnloop.attempts.reveal_ledger import record_reveal
    from learnloop_sidecar.registry import METHOD_REGISTRY
    from tests.test_ux_phase4_feedback import (
        ITEM,
        _administration_receipts,
        _due_cold_task,
        _exposure,
        _feedback_answer,
        _later,
    )

    def call(method: str, params: dict):
        spec = METHOD_REGISTRY[method]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    _vault, repository = ctx.require_vault()
    answered = _feedback_answer(ctx, then=_later(days=-2))
    record_reveal(repository, practice_item_id=ITEM, source_kind="tutor_answer", amount=1.0,
                  clock=_later(days=-1, hours=-12))
    task = _due_cold_task(ctx, case_ref="ep_landing")
    session_id = call("start_session", {"availableMinutes": 20})["sessionId"]

    # A non-routine reveal: served as on main, on both direct opens.
    assert call("get_practice_item", {"practiceItemId": ITEM, "sessionId": session_id})["id"] == ITEM
    assert call("open_queue_item", {"practiceItemId": ITEM})["id"] == ITEM
    assert repository.followup_task(task["id"])["not_before"] == task["not_before"]
    assert repository.active_followup_task_for_item(ITEM, kind="cold_retry") is not None
    assert _administration_receipts(repository) >= 1
    assert reveal_total_for_submission(repository, ITEM) >= AUTO_PRIME_REVEAL_THRESHOLD

    # A routine display now covers the item: the next open defers the task
    # (persisted) and opens no further administration.
    before = _administration_receipts(repository)
    _exposure(ctx, answered, "display_landing_open", clock=_later(minutes=-1))
    assert call("open_queue_item", {"practiceItemId": ITEM})["id"] == ITEM
    assert _administration_receipts(repository) == before
    assert repository.active_followup_task_for_item(ITEM, kind="cold_retry") is None
    assert repository.followup_task(task["id"])["not_before"] > task["not_before"]


def test_a_waiting_plan_writes_nothing_and_the_served_item_binds_its_presentation(tmp_path):
    """Round 7's PlanWaiting against the plan's receipts (router R2a's
    ``plan_presentations``, the ``router_decisions`` ledger, the block events):
    the waiting step is decided again on every call and writes none of them,
    so no decision or presentation stands for a block that was never chosen.
    When the hold lifts, the same plan serves the item, and the serve writes
    its plan presentation, which an answer binds to."""

    from datetime import timedelta

    from learnloop.daily_plan.engine import advance, get_or_create_today
    from tests.test_ux_phase4_feedback import _one_item_plan, _served_items

    def counts(env) -> dict[str, int]:
        with env.repository.connection() as connection:
            return {
                table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in ("attention_blocks", "plan_presentations", "router_decisions")
            }

    env, clock = _one_item_plan(tmp_path, timedelta(hours=25) - timedelta(seconds=30))
    record = get_or_create_today(env)
    before = counts(env)
    for _call in range(2):
        record, step = advance(env, serve=True)
        assert step["kind"] == "waiting" and record.status == "open"
    assert counts(env) == before
    assert _served_items(env) == []

    clock.instant = clock.instant + timedelta(seconds=31)
    record, step = advance(env, serve=True)
    assert step["kind"] == "item" and step["practice_item_id"] == "pi_cold"
    with env.repository.connection() as connection:
        bound = connection.execute(
            "SELECT practice_item_id FROM plan_presentations WHERE practice_item_id = 'pi_cold'"
        ).fetchall()
    assert len(bound) == 1


def _r2b_env_with_a_lifting_hold(tmp_path, decider, *, items=None):
    """Router R2b's mixture with only the (fake) Decider weighted, a seed whose
    draw follows it, and a cold check on ``pi_m1a`` held by a routine display
    that lifts in 30 seconds."""

    from datetime import timedelta

    from learnloop.clock import FrozenClock
    from tests.router_mixture_helpers import mixture_env
    from tests.router_model_fakes import fake_runtime, seed_with_first_uniform
    from tests.test_ux_phase4_feedback import _iso

    env = mixture_env(
        tmp_path, fake_runtime(decider=decider, seed=seed_with_first_uniform(at_least=0.5)), items=items,
        toml="[router.weights]\nstaged = 0.0\ndecider = 1.0\nllm = 0.0\n",
    )
    now = env.clock.now()
    env.repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_r8",
        not_before=_iso(FrozenClock(now - timedelta(hours=1))), expires_at=_iso(FrozenClock(now + timedelta(days=30))),
        selected_item_id="pi_m1a", clock=FrozenClock(now - timedelta(days=1)),
    )
    env.repository.insert_reveal_event(
        {"practice_item_id": "pi_m1a", "learning_object_id": "lo_m1", "source_kind": "answer_display",
         "amount": 1.0, "basis": "feedback_full_answer:desktop:display_r8"},
        clock=FrozenClock(now - (timedelta(hours=25) - timedelta(seconds=30))),
    )
    return env


def test_under_the_router_mixture_a_drawn_stop_stays_a_logged_stop_beside_a_lifting_hold(tmp_path):
    from learnloop.daily_plan.engine import advance, build_plan
    from learnloop.daily_plan.types import STOP_FOR_TODAY
    from tests.router_mixture_helpers import rows
    from tests.router_model_fakes import FakeDecider

    def stop_mass(refs):
        return {ref: (1.0 if ref == STOP_FOR_TODAY else 0.0) for ref in refs}

    decider = FakeDecider(choice=stop_mass)
    env = _r2b_env_with_a_lifting_hold(tmp_path, decider)
    # Four minutes: the stop is offered while one-minute reviews still fit.
    record = build_plan(env, kind="normal", budget=4.0, remembered=4, minutes_source="chip")
    record, step = advance(env, serve=False)

    assert decider.calls, "the mixture asked its model"
    assert record.status == "complete" and step["kind"] == "done"
    (stop,) = record.stops()
    assert stop.chosen["feasible_ids"], "other work was feasible: this was a chosen stop"
    (decision,) = [row for row in rows(env) if row["chosen_ref"] == STOP_FOR_TODAY]
    assert stop.decision_ref == decision["id"]
    assert 0.0 < decision["propensity"] < 1.0
    assert stop.chosen["propensity"] == pytest.approx(decision["propensity"])


def test_under_the_router_mixture_a_waiting_plan_asks_no_model_and_logs_no_decision(tmp_path):
    from datetime import timedelta

    from learnloop.daily_plan.engine import advance, get_or_create_today
    from tests.daily_plan_fakes import scheduled
    from tests.router_mixture_helpers import rows
    from tests.router_model_fakes import FakeDecider, first_option

    decider = FakeDecider(choice=first_option)
    env = _r2b_env_with_a_lifting_hold(
        tmp_path, decider, items=[scheduled("pi_m1a", "lo_m1", forgetting_risk=0.6)],
    )
    record = get_or_create_today(env)
    for _call in range(2):
        record, step = advance(env, serve=True)
        assert step["kind"] == "waiting" and record.status == "open"
    assert rows(env) == [] and decider.calls == []

    env.clock.instant = env.clock.instant + timedelta(seconds=31)
    record, step = advance(env, serve=True)
    assert step["kind"] == "item" and step["practice_item_id"] == "pi_m1a"
    assert len(rows(env)) == 1
