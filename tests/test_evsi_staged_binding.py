"""Router R2a: a staged forecast joins its bound attempt through the exact receipt.

EVSI calibration's staged adapter (``live_report.LedgerOutcomeAdapter.
_staged_attempt``) reported every committed live staged diagnostic forecast as
``no_attempt_binding``: nothing linked a staged decision to the attempt that
answered it. R2a's chain does (plan §5.3, owner Q10, exact receipts only): the
forecast's ``decision_ref`` (a ``controller_decisions`` id) -> the
``plan_block`` router decision carrying that ``controller_decision_id`` -> its
block -> the ``plan_presentations`` row for the forecast's chosen item -> the
attempt bound to it. The session rule is never used for a forecast.

No production caller passes a ``DiagnosticSelector`` (owner Q2: VOI v2 stays the
only authority on diagnostic checks), so the chain is proven with a fake one and
a chooser that names the staged decision, as a staged frame that persists one
would. Fail-first: plan §9 R2a, item 1.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from learnloop.daily_plan.engine import advance, build_plan
from learnloop.evsi_calibration import live_report as LR
from learnloop.scheduling import controller_snapshot as cs
from learnloop.scheduling import staged_policy as sp
from learnloop.scheduling.scheduler import SchedulerSession

from tests.daily_plan_fakes import MovableClock, iso, make_env, scheduled, seed_due
from tests.helpers import create_daily_plan_vault
from tests.test_voi_forecasts import _STAGED_PRIOR, _forecasts, _separating, _staged_loss

PAST = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
LAST = datetime(2026, 9, 20, 9, 0, tzinfo=UTC)
ITEM = "pi_pa"


def _world(tmp_path):
    from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION

    paths = create_daily_plan_vault(
        tmp_path / "vault", learning_objects={"lo_probe": [(ITEM, 2.0), ("pi_pb", 2.0)]},
        version=ROUTER_STAGED_FRAME_ALGORITHM_VERSION,
    )
    clock = MovableClock()
    env = make_env(
        paths.root,
        [scheduled(ITEM, "lo_probe", forgetting_risk=0.6), scheduled("pi_pb", "lo_probe", forgetting_risk=0.6)],
        clock=clock, session_id="s1",
    )
    for item in (ITEM, "pi_pb"):
        seed_due(env.repository, item, due=PAST, last=LAST)
    with env.repository.connection() as connection:
        connection.execute("INSERT INTO sessions(id, started_at) VALUES ('s1', ?)", (iso(clock.now()),))
        connection.commit()
    return env, clock


def _live_staged_decision(env) -> sp.DecisionResult:
    diagnostic = sp.DiagnosticSelector(
        loss_table=_staged_loss(),
        candidates={ITEM: {"members": [_separating(f"{ITEM}_e")], "prior": _STAGED_PRIOR, "expected_minutes": 0.5}},
    )
    candidates = [cs.Candidate(candidate_ref=ITEM, learning_object_id="lo_probe", active=True, purpose="diagnostic",
                               surface_hash=f"S_{ITEM}")]
    result = sp.decide(
        env.vault, env.repository, SchedulerSession(session_id="s1", available_minutes=15),
        signals=sp.StateSignals(decision_relevant_robust_value=0.9), candidates=candidates,
        diagnostic=diagnostic, mode="live", clock=env.clock,
    )
    assert result.chosen_candidate_ref == ITEM
    return result


def _forecast(env, decision_id: str) -> dict:
    [row] = [
        row for row in _forecasts(env.repository)
        if row["site"] == "staged_diagnostic_selection" and row["decision_ref"] == decision_id
    ]
    assert row["chosen_practice_item_id"] == ITEM
    return row


def _naming(policy, controller_decision_id: str):
    """The staged chooser, naming the persisted staged decision on its record."""

    inner = policy.chooser

    class Naming:
        name = inner.name

        def choose(self, state, feasible):
            choice = inner.choose(state, feasible)
            return replace(choice, router_record={**dict(choice.router_record or {}),
                                                  "controller_decision_id": controller_decision_id})

    return replace(policy, chooser=Naming())


def _binding(env, forecast) -> tuple[str | None, str]:
    with env.repository.connection() as connection:
        return LR.LedgerOutcomeAdapter(connection).attempt_for(forecast)


def _answer(env, at, presentation_id) -> str:
    attempt_id = f"att_{ITEM}_{int(at.timestamp())}"
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "created_at, session_id, correctness, evidence_origin, plan_presentation_id) "
            "VALUES (?, ?, 'lo_probe', 'short_answer', 'independent_attempt', ?, 's1', 1.0, 'human', ?)",
            (attempt_id, ITEM, iso(at), presentation_id),
        )
        connection.commit()
    return attempt_id


def test_a_committed_staged_forecast_joins_the_attempt_bound_to_its_presentation(tmp_path):
    from learnloop.daily_plan.policy import policy_for

    env, clock = _world(tmp_path)
    result = _live_staged_decision(env)
    forecast = _forecast(env, result.decision_id)
    # Nothing composes it yet: no router decision names it.
    assert _binding(env, forecast) == (None, "no_attempt_binding")

    env.policy = _naming(policy_for(env.vault, env.repository, session_id="s1", clock=clock), result.decision_id)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    with env.repository.connection() as connection:
        row = connection.execute(
            "SELECT controller_decision_id FROM router_decisions WHERE decision_kind = 'plan_block'"
        ).fetchone()
    assert row["controller_decision_id"] == result.decision_id
    assert _binding(env, forecast) == (None, "not_presented")

    clock.advance(1)
    _record, step = advance(env, serve=True)
    assert step["practice_item_id"] == ITEM
    assert _binding(env, forecast) == (None, "presented_unanswered")

    clock.advance(2)
    attempt_id = _answer(env, clock.now(), step["presentation_id"])
    assert _binding(env, forecast) == (attempt_id, "taken")


def test_an_unbound_attempt_on_the_chosen_item_is_never_the_forecasts_outcome(tmp_path):
    """No session rule for forecasts (Q10, option a): an attempt on the item
    that answered no presentation leaves the forecast right-censored."""

    from learnloop.daily_plan.policy import policy_for

    env, clock = _world(tmp_path)
    result = _live_staged_decision(env)
    forecast = _forecast(env, result.decision_id)
    env.policy = _naming(policy_for(env.vault, env.repository, session_id="s1", clock=clock), result.decision_id)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    clock.advance(1)
    advance(env, serve=True)
    clock.advance(2)
    _answer(env, clock.now(), None)
    assert _binding(env, forecast) == (None, "presented_unanswered")


def test_the_report_version_moved_with_the_presentation_join():
    assert LR.REPORT_VERSION == "voi_calibration_report_v6"
