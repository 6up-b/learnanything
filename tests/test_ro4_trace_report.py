"""RO4 §8.4 (card v3), §8.8 (the trace and its plain words), §8.9 (the report), §8.10 (protection on both cards,
the first-day report on a synthetic vault against the predecessor, latency deadlines). Fakes only."""

from __future__ import annotations

import json
import time

from typer.testing import CliRunner

from learnloop.algorithm_versions import INTERVAL_FACTOR_ALGORITHM_VERSION, ROUTER_OBJECTIVE_ALGORITHM_VERSION
from learnloop.db.stores import router_objective as store
from learnloop.router import card as C
from learnloop.router_objective import objective_report
from learnloop.router_objective.trace import explain

from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import fake_runtime

TAG = ROUTER_OBJECTIVE_ALGORITHM_VERSION
OLD = INTERVAL_FACTOR_ALGORITHM_VERSION


def _first_trace(env):
    with env.repository.connection() as connection:
        listed = store.traces(connection)
        return store.trace(connection, listed[0]["decision_id"]) if listed else None


def test_the_cli_prints_a_decisions_trace_and_the_report(tmp_path):
    from learnloop.cli import app

    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    run(env)
    trace = _first_trace(env)
    assert trace is not None
    runner = CliRunner()
    shown = runner.invoke(app, ["router", "trace", trace["decision_id"], "--vault", str(env.vault.root), "--json"])
    assert shown.exit_code == 0, shown.output
    body = json.loads(shown.output)
    assert body["trace"]["mixing"]["chosen"] == trace["chosen_ref"]
    words = runner.invoke(app, ["router", "trace", trace["decision_id"], "--vault", str(env.vault.root)])
    assert words.exit_code == 0 and "This was chosen by" in words.output
    report = runner.invoke(app, ["router", "objective-report", "--vault", str(env.vault.root), "--json"])
    assert report.exit_code == 0, report.output
    serving = json.loads(report.output)["router_objective"]["serving"]
    assert serving["decisions"] >= 1 and serving["days"]
    missing = runner.invoke(app, ["router", "trace", "no-such-decision", "--vault", str(env.vault.root)])
    assert missing.exit_code == 1


def test_the_why_surface_offers_the_trace_in_plain_words(tmp_path):
    from tests.router_model_fakes import block_drawing_seed

    # RO6's landing ruling R14: a seed pinned to serve a block first (unpinned, a first draw of stop left no decided
    # block: the known flake).
    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=TAG)
    run(env)
    trace = _first_trace(env)
    lines = explain(trace)
    assert lines and all(isinstance(line, str) for line in lines)
    text = " ".join(lines).lower()
    for internal in ("propensity", "kappa", "lane", "posterior", "π", "μ"):
        assert internal not in text, internal
    from learnloop.daily_plan.engine import advance

    record, _step = advance(env, serve=False)
    from learnloop.daily_plan.view import _block_row

    decided = [block for block in record.blocks if block.chosen.get("decision_ref")]
    assert decided and _block_row(env, record, decided[0], None)["objective_decision_id"]


def test_card_v3_renders_goal_dates_and_is_the_predecessors_card_below_the_tag():
    inputs = C.CardInputs(
        decision={"decided_at": "2026-11-05T09:00:00Z"}, session={"plan_kind": "normal"},
        intent={"lo_a": {"deadline": "2026-11-15T09:00:00Z"}},
        candidates=[{"ref": "b1", "kind": "maintain", "est_minutes": 5, "item_count": 2, "topics": ["A"],
                     "learning_object_ids": ["lo_a"], "reversible": True, "reason_code": "maintain"}])
    v2 = C.build_card(inputs)
    v3 = C.build_card(C.CardInputs(**{**inputs.__dict__, "goal_dates": True}))
    assert v2.card_version == C.CARD_VERSION and "goal date" not in v2.text and "goal_dates" not in v2.json
    assert v3.card_version.startswith(C.CARD_V3) and "goal date 2026-11-15 in 10.0 days" in v3.text


def test_protection_holds_on_the_llm_policys_card(tmp_path):
    """The decision-level H3 card reads the history through AD's material view and learner_protection: no
    held-out stem, answer, hint or gap; exam work keeps its result only; no reference solution."""

    from learnloop.daily_plan.objective_card import decision_card
    from learnloop.daily_plan.types import BlockCandidate

    from tests.ro2_history_protection_helpers import SENTINEL, SERVED, _textbook

    paths, repository, _spans, vault = _textbook(tmp_path)
    lo = vault.practice_items["pi_eigen_2"].learning_object_id
    candidate = BlockCandidate(candidate_id="b1", lane="maintain", action="maintain", subtype=None,
                               learning_object_ids=(lo,), item_ids=("pi_eigen_2",), reading=None, est_minutes=4.0,
                               planner_value=1.0, reason="r")
    card = decision_card(vault, repository, [candidate], served_at=SERVED, goals={}, session={}, budget=10 ** 7)
    text = json.dumps(card["state"])
    assert SENTINEL not in text and "CITED-HINT" not in text and "EXAM-ANSWER-TEXT" not in text
    assert vault.practice_items["pi_eigen_2"].expected_answer not in text
    assert "PUBLIC-ANSWER" in text
    exams = card["state"]["history"].get("exams") or []
    assert [set(entry) & {"answer", "item", "explanation"} for entry in exams] == [set()] * len(exams)


def test_the_first_day_report_against_the_predecessor_on_a_synthetic_vault(tmp_path):
    """§8.10's first day: on a copy-shaped synthetic vault with no outcomes, stop's share at each boundary, session
    length and each policy's share, against the predecessor. Reported, never holding the upgrade."""

    old = mixture_env(tmp_path / "old", fake_runtime(), version=OLD)
    new = mixture_env(tmp_path / "new", fake_runtime(), version=TAG)
    old_record, new_record = run(old, steps=60), run(new, steps=60)
    old_minutes = sum(block.est_minutes() for block in old_record.blocks)
    new_minutes = sum(block.est_minutes() for block in new_record.blocks)
    with new.repository.connection() as connection:
        report = objective_report.build(connection, now="2099-01-01T00:00:00Z")
    serving = report["serving"]
    first_day = {
        "predecessor": {"blocks": len(old_record.blocks), "planned_minutes": round(old_minutes, 2),
                        "policies": sorted({row["policy"] for row in rows(old)})},
        "objective": {"blocks": len(new_record.blocks), "planned_minutes": round(new_minutes, 2),
                      "stop_share": serving["stop_share"], "policy_share": serving["policy_share"],
                      "days": serving["days"], "budget": new_record.budget},
    }
    print("FIRST_DAY_REPORT", json.dumps(first_day, sort_keys=True))
    assert serving["decisions"] >= 1
    assert all(day["stop_in_support_share"] == 1.0 for day in serving["days"])
    assert report["recommendation_value"]["closed_scores"] == 0


def test_the_numeric_policy_honours_its_deadline():
    clock = iter([0.0, 0.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0] + [10.0] * 1000)

    # A deadline already passed: the evaluation is incomplete and the policy reports a timeout, never a choice.
    from learnloop.router_objective import value as V
    from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS

    inputs = V.Inputs(topics=(V.Topic("lo", 0.0, 0.1, undated_density=1 / 90),), dated=(), session_minutes=0.0,
                      price=V.Price(kappa0=0.001, remembered=20.0), tail_block_minutes=5.0, tail_block_items=2,
                      horizon_days=90.0, fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS))
    actions = [V.Action(ref="a", kind=V.REVIEW, item_los=("lo",), minutes=5.0), V.Action(ref="stop_for_today",
                                                                                          kind=V.STOP)]
    late = V.evaluate(inputs, actions, draws=8, seed="d", deadline=5.0, clock=lambda: next(clock))
    assert not late.complete
    started = time.monotonic()
    timed = V.evaluate(inputs, actions, draws=8, seed="d", deadline=time.monotonic() + 30.0)
    assert timed.complete and (time.monotonic() - started) < 8.0  # well inside router.timeout_seconds


def test_the_report_counts_how_often_the_days_seed_fell_back():
    """Landing ruling R5: κ0's fallback to the tail's average marginal gain stands until RO5, and the report counts
    the days whose seed fell back (and to what), so the owner can see it."""

    import sqlite3

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE router_objective_traces (id TEXT, decision_id TEXT, decision_kind TEXT, local_date TEXT, "
        "session_minutes REAL, remembered_minutes REAL, kappa0 REAL, kappa_how TEXT, chosen_ref TEXT, "
        "drawn_component TEXT, propensity REAL, w REAL, numeric_ref TEXT, llm_status TEXT, numeric_status TEXT, "
        "stop_in_support INTEGER, guard_crossed INTEGER, window_closes_at TEXT, trace_json TEXT, created_at TEXT)")
    days = [("2026-11-01", ["day_seed", "carried_today", "carried_today"]),
            ("2026-11-02", ["tail_average", "carried_today"]),
            ("2026-11-03", ["floored_at_last_positive"]),
            ("2026-11-04", ["tail_average"])]
    n = 0
    for day, hows in days:
        for how in hows:
            n += 1
            connection.execute(
                "INSERT INTO router_objective_traces VALUES (?, ?, 'plan_block', ?, 5, 25, 0.001, ?, 'b1', 'staged', "
                "1.0, 0.8, 'b1', 'not_ready', 'answered', 1, 0, NULL, '{}', ?)",
                (f"t{n}", f"d{n}", day, how, f"{day}T10:{n:02d}:00Z"))
    report = objective_report.build(connection, now="2099-01-01T00:00:00Z")
    seed = report["serving"]["kappa_seed"]
    assert seed == {"days": 4, "by_how": {"day_seed": 1, "floored_at_last_positive": 1, "tail_average": 2},
                    "fell_back": 3, "fell_back_to_tail_average": 2,
                    # RO5 (its landing, merging this count): days priced by κ0's posterior are counted apart.
                    "posterior_days": 0, "note": seed["note"]}
    assert any("fell back" in line and "2 of 4 days" in line for line in objective_report.lines(report))
