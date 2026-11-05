"""Router objective RO5, landing rulings (docs/reviews/router-ro5.md, "Landing onto main"): each reproduced by a test
that fails on the pre-fix source (``5f02be6eb2``). Fakes, in-memory SQLite and synthetic vaults only; no model is
asked.

* R2 (Codex final verify F11): the return slope's integration adapts to the posterior: its grid covers the prior's
  and the likelihood's peaks and the region between, its bounds widen until the tail mass beyond them is negligible,
  and it converges only when both the spacing and the tail mass pass; a planted slope is recovered at a narrow prior
  and at a wide one.
* R4: the stop coin skips the session's opening boundary (no active minute yet).
* R1 (Codex final verify F10, reopened): every read forming a check's completion, a completion rate or a comparison
  score reads as of one closure through one function (``checks.Closure``), applied to every event it counts
  (answers on occurrence and received time, skips, displacements, administrations, the days drawn and the sessions):
  Codex's two reproductions (a later skip moving a past rate; a later answer moving a closed score).
* R6: the calibration's lag join end to end (one trace with a known ``m⁰`` vector, one graded check two days later;
  a coverage test, passing on the pre-fix source too).
"""

from __future__ import annotations

import random

import pytest

from learnloop.algorithm_versions import ROUTER_CALIBRATION_ALGORITHM_VERSION
from learnloop.router_objective import assignments as A
from learnloop.router_objective import mix
from learnloop.router_objective import stop_coin as SC

from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import fake_runtime

TAG = ROUTER_CALIBRATION_ALGORITHM_VERSION
SUPPORT = ("a", "b", SC.STOP)


# -- R2 (F11) ------------------------------------------------------------------------------------------------


def _planted(slope: float, *, n: int, p: float, seed: int, noise: float = 0.002) -> list[SC.ReturnRow]:
    """Sessions whose randomized coin moves the minutes (``z``) and whose return gap follows them at ``slope``."""

    rng = random.Random(seed)
    rows = []
    for i in range(n):
        u = rng.random()
        weight = 1 / p if u < p else (-1 / p if u < 2 * p else 0.0)
        z = -0.1 * weight + rng.gauss(0, 0.01)
        arm = SC.OFFER_STOP if weight > 0 else SC.PRESENT_NEXT if weight < 0 else SC.POLICY
        rows.append(SC.ReturnRow(str(i), str(i), arm, weight, (0.0, 1.0), z, slope * z + rng.gauss(0, noise)))
    return rows


def test_r2_f11_the_dominant_posterior_peak_outside_the_priors_reach_is_integrated():
    # Codex's reproduction (verify 20261105-104749-57ysh9): prior sd 0.01, coin probability 0.45, the likelihood's
    # peak at 0.4197, 42 prior sds out. Pre-fix: mean 0.000275, variance 1.0e-4, labelled posterior_randomized_coin
    # (the integration stopped at 40 prior sds and declared convergence on the prior's side alone).
    fitted = SC.fit_return_slope(_planted(0.42, n=3000, p=0.45, seed=8), 0.01)
    assert fitted.source == "posterior_randomized_coin"
    assert fitted.mean == pytest.approx(0.4196, abs=2e-3) and 0 < fitted.variance < 1e-6


@pytest.mark.parametrize("prior_sd", [0.01, 1.0], ids=["narrow", "wide"])
def test_r2_a_planted_slope_is_recovered_at_a_narrow_and_at_a_wide_prior(prior_sd):
    fitted = SC.fit_return_slope(_planted(0.3, n=4000, p=0.3, seed=21), prior_sd)
    assert fitted.source == "posterior_randomized_coin"
    assert fitted.mean == pytest.approx(0.3, abs=5e-3) and 0 < fitted.variance < 1e-5


def test_r2_a_weak_instrument_keeps_the_priors_resolution_and_bounds():
    # The other side (a guard, passing before and after): little information, the posterior near the prior, still
    # integrated with its tails (the bounded statistic can leave the posterior a little wider than the prior).
    rng = random.Random(5)
    rows = []
    for i in range(40):
        u = rng.random()
        weight = 1 / 0.3 if u < 0.3 else (-1 / 0.3 if u < 0.6 else 0.0)
        arm = SC.OFFER_STOP if weight > 0 else SC.PRESENT_NEXT if weight < 0 else SC.POLICY
        z = rng.gauss(0, 1) - 0.05 * weight
        rows.append(SC.ReturnRow(str(i), str(i), arm, weight, (0.0, 1.0), z, rng.gauss(0, 1)))
    fitted = SC.fit_return_slope(rows, 0.5)
    assert fitted.source == "posterior_randomized_coin"
    assert abs(fitted.mean) < 0.5 and 0.01 < fitted.variance < 0.5


def test_r2_an_integration_that_cannot_converge_leaves_the_labelled_prior(monkeypatch):
    monkeypatch.setattr(SC, "_WIDENINGS", 0)
    fitted = SC.fit_return_slope(_planted(0.42, n=3000, p=0.45, seed=8), 0.01)
    assert fitted.source == "prior_integration_unconverged" and fitted.mean == 0.0
    assert fitted.variance == pytest.approx(0.01 ** 2)


# -- R4: the stop coin skips the session's opening boundary ---------------------------------------------------


def _offer_seed(rate: float):
    """A seed whose stop-coin uniform lands on ``offer_stop`` (every decision would offer stop)."""

    from learnloop.router.mixture import uniform

    seed = next(f"offer-{i}" for i in range(10_000) if uniform(f"offer-{i}", "stop_coin") < rate)
    return lambda _key, _decision_id: seed


def test_r4_the_coin_is_not_drawn_before_any_active_minute_of_the_session(tmp_path):
    # The synthetic week's case: an offer at minute 0 that ended the day before any question. Pre-fix the day's first
    # decision drew offer_stop and the plan closed with nothing served.
    env = mixture_env(tmp_path, fake_runtime(seed=_offer_seed(0.45)), version=TAG,
                      toml="[router_objective]\nstop_coin = 0.45\ncheck_rate = \"off\"\npick_open_share = 0.0\n")
    run(env)
    decided = [row for row in rows(env) if row["policy"] == mix.POLICY]
    with env.repository.connection() as connection:
        coins = {row["unit_id"]: row for row in A.rows(connection, A.STOP_COIN)}
        attempts = connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()[0]
    assert decided, "the day had policy decisions"
    first = decided[0]
    assert first["id"] not in coins and "stop_coin" not in first["detail_json"]["mixture"]
    assert attempts >= 1, "the opening boundary served a question"
    # Every coin drawn was at a boundary with active minutes in the session (structural: the eligibility asks it).
    assert coins and all(row["detail"]["availability"]["session_minutes"] > 0 for row in coins.values())
    assert not SC.eligible([*SUPPORT], session_minutes=0.0) and SC.eligible([*SUPPORT], session_minutes=0.5)
    assert not SC.eligible([*SUPPORT], session_minutes=None)


# -- R1 (F10): one closure for every event a check, a rate or a score counts ----------------------------------


def _ledger_db():
    """The tables a check's resolution and a score read, in memory (Codex's reproductions' shape)."""

    import sqlite3

    from learnloop.db.stores import router_objective as store

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(f"CREATE TABLE policy_experiment_assignments ({', '.join(store.ASSIGNMENT_COLUMNS)})")
    connection.execute("CREATE TABLE attention_block_events (id INTEGER PRIMARY KEY, block_id TEXT, event_ordinal "
                       "INTEGER, kind TEXT, detail_json TEXT, created_at TEXT)")
    connection.execute("CREATE TABLE sessions (id TEXT, started_at TEXT, ended_at TEXT)")
    connection.execute("CREATE TABLE plan_presentations (id TEXT, block_id TEXT)")
    connection.execute("CREATE TABLE practice_attempts (id TEXT, practice_item_id TEXT, learning_object_id TEXT, "
                       "attempt_type TEXT, correctness REAL, hints_used INTEGER, primed INTEGER, latency_seconds REAL, "
                       "plan_presentation_id TEXT, created_at TEXT, received_at TEXT, manual_review_reason TEXT)")
    connection.execute("CREATE TABLE interaction_events (kind TEXT, occurred_at TEXT, created_at TEXT, payload_json TEXT)")
    connection.execute("CREATE TABLE router_objective_traces (id TEXT, decision_id TEXT, decision_kind TEXT, "
                       "local_date TEXT, created_at TEXT, window_closes_at TEXT, llm_status TEXT, numeric_status TEXT, "
                       "kappa0 REAL, remembered_minutes REAL, trace_json TEXT)")
    return connection


def _check_day(connection, day: str, *, item: str, topic: str = "L", r: float = 0.5) -> str:
    """One drawn day with one slot, its session and its administration (block ``b-<day>``); the slot's id."""

    import json

    from learnloop.router_objective import checks as C

    at = f"{day}T12:00:00Z"
    A.insert(connection, experiment_id=A.CHECK, unit_id=C.day_unit(day), variant="day", propensity=1.0, seed="s",
             draw=None, candidate_refs=[topic], detail={"r": {topic: r}}, at=at)
    slot = A.insert(connection, experiment_id=A.CHECK, unit_id=C.slot_unit(day, 0), variant=topic, propensity=r,
                    seed="s", draw=0.1, candidate_refs=[topic], detail={"slot": 0, "item_id": item}, at=at)
    connection.execute("INSERT INTO sessions VALUES (?, ?, NULL)", (f"s-{day}", f"{day}T12:30:00Z"))
    connection.execute("INSERT INTO attention_block_events (block_id, event_ordinal, kind, detail_json, created_at) "
                       "VALUES (?, 0, 'item_planned', ?, ?)",
                       (f"b-{day}", json.dumps({"practice_item_id": item, "ro5_check": {"assignment_id": slot}}),
                        f"{day}T12:31:00Z"))
    return str(slot)


def _answer(connection, item: str, at: str, *, correctness: float = 1.0, received: str | None = None) -> None:
    connection.execute("INSERT INTO practice_attempts VALUES (?, ?, 'L', 'independent_attempt', ?, 0, 0, 60, NULL, ?, ?, "
                       "NULL)",
                       (f"a-{item}-{at}", item, correctness, at, received))


def _skip(connection, day: str, item: str, at: str, kind: str = "item_skipped") -> None:
    import json

    connection.execute("INSERT INTO attention_block_events (block_id, event_ordinal, kind, detail_json, created_at) "
                       "VALUES (?, 1, ?, ?, ?)", (f"b-{day}", kind, json.dumps({"practice_item_id": item}), at))


def test_r1_f10_a_later_skip_never_moves_a_past_completion_rate():
    from learnloop.router_objective import checks as C

    connection = _ledger_db()
    _check_day(connection, "2026-01-01", item="i1")
    _answer(connection, "i1", "2026-01-01T13:00:00Z")
    _check_day(connection, "2026-01-02", item="i2")  # administered, not answered
    before = C.completion(connection, through="2026-01-02")
    assert before["rate"] == pytest.approx(1.0) and before["assigned"] == 1  # January 2's check is still open
    # Codex's reproduction: an item_skipped dated January 3 for January 2's block. Pre-fix: rate 0.5, assigned 2
    # (the skip had no cutoff and turned the open check into a skipped one).
    _skip(connection, "2026-01-02", "i2", "2026-01-03T09:00:00Z")
    assert C.completion(connection, through="2026-01-02") == before
    # A displacement after the cutoff is not seen either; both are seen from their own date on.
    _skip(connection, "2026-01-02", "i2", "2026-01-03T09:05:00Z", kind="item_displaced")
    assert C.completion(connection, through="2026-01-02") == before
    later = {e.assignment_id: e.status for e in C.resolve(connection, through="2026-01-03")}
    assert sorted(later.values()) == [C.COMPLETED, C.DISPLACED]


def _score_trace(connection):
    import json

    from tests.test_ro5_checks import _row, _trace

    row = _row()
    connection.execute("INSERT INTO router_objective_traces VALUES ('t1', ?, 'plan_block', ?, ?, ?, 'answered', "
                       "'answered', 0.0, 10.0, ?)", (row["decision_id"], row["local_date"], row["created_at"],
                                                     row["window_closes_at"], json.dumps(_trace())))


class _Config:
    class router_objective:  # noqa: N801 - the config's section, as the scores read it
        session_gap_minutes = 60


def test_r1_f10_a_closed_score_never_moves_with_an_answer_after_its_closure():
    from learnloop.router_objective import checks as C
    from learnloop.router_objective import scores as S

    connection = _ledger_db()
    _score_trace(connection)  # decided January 1 at 10:00, its window closing January 3 at 10:00
    _check_day(connection, "2026-01-01", item="i1")
    _answer(connection, "i1", "2026-01-01T13:00:00Z")
    _check_day(connection, "2026-01-02", item="i2")  # unanswered when the window closes
    at_closure = S.scores(connection, _Config, at="2026-01-03T11:00:00Z")
    assert len(at_closure) == 1 and at_closure[0].observed == 0
    # Codex's reproduction: the January 2 check answered correctly on January 5. Pre-fix, reading the scores on
    # January 6 moved the same closed decision to an observed check (value 4, observed 1).
    _answer(connection, "i2", "2026-01-05T09:00:00Z")
    after = S.scores(connection, _Config, at="2026-01-06T00:00:00Z")
    assert [(d.scored.value, d.observed, d.uses_with_r) for d in after] == \
        [(d.scored.value, d.observed, d.uses_with_r) for d in at_closure]
    # The check itself completes from January 5 on: the closure is the read's, never the check's history rewritten.
    assert {e.local_date: e.status for e in C.resolve(connection, through="2026-01-05")}["2026-01-02"] == C.COMPLETED


def test_r1_an_answer_received_after_the_closure_is_not_seen_at_it():
    # RO1's availability predicate: an answer counts at a cutoff only once it happened AND was known.
    from learnloop.router_objective import checks as C

    connection = _ledger_db()
    _check_day(connection, "2026-01-02", item="i2")
    _answer(connection, "i2", "2026-01-02T14:00:00Z", received="2026-01-04T08:00:00Z")
    closure = C.Closure.through("2026-01-03")
    assert [e.status for e in C.resolve(connection, closure=closure)] == [C.NOT_ANSWERED]
    assert [e.status for e in C.resolve(connection, closure=C.Closure.through("2026-01-04"))] == [C.COMPLETED]


def test_r1_one_function_reads_every_counted_event_as_of_its_closure():
    """The structure: ``checks.Closure.admits`` is the one cutoff; resolve, completion, r_for and the scores take a
    closure and never read an event's time through another path."""

    import inspect

    from learnloop.router_objective import checks as C
    from learnloop.router_objective import scores as S

    assert "closure" in inspect.signature(C.resolve).parameters
    assert "closure" in inspect.signature(C.completion).parameters
    assert "closure" in inspect.signature(C.r_for).parameters
    doc = inspect.getdoc(C.Closure) or ""
    assert "hold" in doc and "regrade" in doc  # the intended current-grade behaviour, named
    source = inspect.getsource(S.scores)
    assert "Closure" in source


# -- R6: the calibration's lag join, end to end ----------------------------------------------------------------


def test_r6_the_lag_join_reads_the_newest_trace_before_the_check_at_its_lag():
    """One trace row with a known ``m⁰`` vector and one graded check two days later: the calibration row is that
    trace's forecast at lag 2, on the logit scale, against the check's label (``goal_read.calibration_rows``)."""

    import json
    import math

    from learnloop.router_objective import goal_read as G

    connection = _ledger_db()
    trace = {"evaluation": {"window_days": 3, "uses": {"topics": [{"lo": "L", "c": 0.5, "m0": [0.3, 0.6, 0.9]}],
                                                        "dated": []}}}
    connection.execute("INSERT INTO router_objective_traces VALUES ('t1', 'd1', 'plan_block', '2026-01-01', "
                       "'2026-01-01T10:00:00Z', '2026-01-04T10:00:00Z', 'answered', 'answered', 0.0, 10.0, ?)",
                       (json.dumps(trace),))
    _check_day(connection, "2026-01-03", item="i3")
    _answer(connection, "i3", "2026-01-03T13:00:00Z", correctness=1.0)
    rows = G.calibration_rows(connection, through="2026-01-04")
    assert rows == [(pytest.approx(math.log(0.6 / 0.4)), None, 1.0, 2)]
    # A check the next day reads the same trace at lag 1, and a miss is a 0 at its own lag.
    _check_day(connection, "2026-01-02", item="i2")
    _answer(connection, "i2", "2026-01-02T13:00:00Z", correctness=0.0)
    by_lag = {row[3]: row for row in G.calibration_rows(connection, through="2026-01-04")}
    assert by_lag[1] == (pytest.approx(math.log(0.3 / 0.7)), None, 0.0, 1) and set(by_lag) == {1, 2}


_STAGE_OR_SYMBOL = __import__("re").compile(r"\b(RO|TE|FG|AD|RW|LP|UX|PF|S)\d\w*\b|\bw\b|[μπκΔθσεωαβγ]|\bmvp\b")


@pytest.mark.parametrize("version", ["ro4", "ro5"])
def test_r5_3_how_was_this_chosen_is_plain_words_with_no_stage_names_or_symbols(tmp_path, version):
    """RO4's open item 3: the why surface printed the trace's weight note verbatim ("no randomized checks exist
    before RO5, so no score forms and w stays at its prior"). Pre-fix this fails on both versions' traces."""

    from learnloop.algorithm_versions import ROUTER_OBJECTIVE_ALGORITHM_VERSION
    from learnloop.db.stores import router_objective as store
    from learnloop.router import why
    from learnloop.router_objective.trace import explain

    env = mixture_env(tmp_path, fake_runtime(), version=TAG if version == "ro5" else ROUTER_OBJECTIVE_ALGORITHM_VERSION)
    run(env)
    with env.repository.connection() as connection:
        traces = [store.trace(connection, row["decision_id"]) for row in store.traces(connection)]
    assert traces
    for trace in traces:
        lines = explain(trace)
        text = " ".join(lines)
        assert lines and why.jargon_in(text) == [], text
        assert not _STAGE_OR_SYMBOL.search(text), (_STAGE_OR_SYMBOL.search(text), text)
        assert any("split" in line for line in lines)
    # The moved case reads in plain words too.
    moved = {**traces[0], "trace": {**traces[0]["trace"], "mixing": {
        **traces[0]["trace"]["mixing"], "w": 0.6, "weight_note": "w moved on closed scores",
        "posterior": {"source": "posterior", "n": 12}}}}
    text = " ".join(explain(moved))
    assert why.jargon_in(text) == [] and not _STAGE_OR_SYMBOL.search(text) and "moved" in text


@pytest.mark.parametrize("version", ["ro4", "ro5"])
def test_r5_2_the_objective_report_prints_w_and_its_posterior(tmp_path, version):
    """RO4's open item 2: the CLI never passed the weight, so the report printed ``w None`` and an empty posterior
    while every trace recorded 0.8."""

    import json

    from typer.testing import CliRunner

    from learnloop.algorithm_versions import ROUTER_OBJECTIVE_ALGORITHM_VERSION
    from learnloop.cli import app

    env = mixture_env(tmp_path, fake_runtime(), version=TAG if version == "ro5" else ROUTER_OBJECTIVE_ALGORITHM_VERSION)
    run(env)
    runner = CliRunner()
    shown = runner.invoke(app, ["router", "objective-report", "--vault", str(env.vault.root), "--json"])
    assert shown.exit_code == 0, shown.output
    value = json.loads(shown.output)["router_objective"]["recommendation_value"]
    assert value["w"] == pytest.approx(0.8)
    assert value["posterior"].get("source") and "mean" in value["posterior"]
    words = runner.invoke(app, ["router", "objective-report", "--vault", str(env.vault.root)])
    assert words.exit_code == 0 and "w 0.8" in words.output and "w None" not in words.output


def test_r6_the_return_models_assumption_is_labelled_in_the_trace_and_the_report():
    # The return model's record (the trace's ``inputs.return_model`` and the report's ``return_model``) is
    # ReturnSlope.as_dict: the assumption travels with it, fitted or at its prior.
    for fitted in (SC.ReturnSlope(), SC.fit_return_slope(_planted(0.3, n=400, p=0.3, seed=2), 1.0)):
        assert fitted.as_dict()["assumption"] == SC.RETURN_ASSUMPTION
    assert "only through the session's minutes" in SC.RETURN_ASSUMPTION
