"""The follow-up batch, items 1 and 2: the memory model the objective's rollouts read. Fakes only.

* **Item 1 (RO4's landing ruling R3)**: the rollouts draw ``γ`` and the reading curve from AD's posterior (RO5 §9 item
  7 built the read through AD's read-only ``decision_state_fields(learning_moments=True)``; its reading map is RO4's R6
  path), the trace at the tag holds the numbers beside their source, and the objective report says what the rollouts
  read instead of the landing record's "priors".
* **Item 2 (RO4's item 6)**: the Bayesian sensor combiner is also fitted on the traces' frozen sensors joined to
  resolved cold outcomes (RO2's resolver), as of each decision through the availability predicate, with its labelled
  prior; the trace names the combiner's version and fit size.
"""

from __future__ import annotations

import json

import pytest

from learnloop.algorithm_versions import ROUTER_FOLLOWUPS_ALGORITHM_VERSION, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
from learnloop.db.stores import router_objective as store
from learnloop.router_objective import objective_report

from tests.router_mixture_helpers import mixture_env, run, served_horizon  # noqa: F401 - a fixture
from tests.router_model_fakes import block_drawing_seed, fake_runtime

TAG = ROUTER_FOLLOWUPS_ALGORITHM_VERSION
OLD = ROUTER_LEARNED_TAIL_ALGORITHM_VERSION


def _traces(env) -> list[dict]:
    with env.repository.connection() as connection:
        return [store.trace(connection, row["decision_id"]) for row in store.traces(connection)]


def _report(env) -> dict:
    with env.repository.connection() as connection:
        return objective_report.build(connection, now="2099-01-01T00:00:00Z")


# -- item 1 ----------------------------------------------------------------------------------------------


def test_the_rollouts_read_ads_posterior_and_the_trace_holds_the_numbers_at_the_tag(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=TAG)
    run(env)
    traces = [entry for entry in _traces(env) if entry["decision_kind"] == "plan_block"]
    assert traces
    for entry in traces:
        trace = entry["trace"]
        assert "fitted posterior" in trace["versions"]["learning"]
        learning = trace["inputs_sources"]["learning"]
        assert learning["source"] == trace["versions"]["learning"]
        assert "gamma" in learning["ad_parameters_read"]
        assert len(learning["gamma"]) == 2 and learning["gamma"][1] >= 0.0
        assert [len(part) for part in learning["gbar"]] == [2, 2]


def test_below_the_tag_the_trace_has_no_learning_numbers(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=OLD)
    run(env)
    traces = [entry for entry in _traces(env) if entry["decision_kind"] == "plan_block"]
    assert traces and all("learning" not in entry["trace"]["inputs_sources"] for entry in traces)


def test_the_report_says_what_the_rollouts_read(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=TAG)
    run(env)
    report = _report(env)
    memory = report["memory_model"]
    decisions = report["serving"]["decisions"]
    assert memory["decisions"] == decisions and memory["learning"] == {"posterior": decisions}
    assert memory["combiner_latest"]["version"] and memory["combiner_latest"]["n"] is not None
    text = "\n".join(objective_report.lines(report))
    assert f"posterior learning parameters on {decisions} of {decisions} decisions" in text
    assert "use priors" not in text


def test_a_trace_without_versions_counts_as_unknown():
    assert objective_report._memory_model([{"trace_json": json.dumps({})}])["learning"] == {"unknown": 1}


# -- item 2 ----------------------------------------------------------------------------------------------


def _join_db():
    import sqlite3

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        "CREATE TABLE router_objective_traces (id TEXT, decision_id TEXT, decision_kind TEXT, chosen_ref TEXT, "
        "trace_json TEXT, created_at TEXT);"
        "CREATE TABLE plan_presentations (id TEXT, router_decision_id TEXT, served_at TEXT);"
        "CREATE TABLE practice_attempts (id TEXT, created_at TEXT, received_at TEXT);")

    def sensors(*los):
        return {lo: {"ad_eta": 0.5, "fsrs_stability": 4.0, "fsrs_elapsed_days": 2.0, "practiced": lo != "lo_new"}
                for lo in los}

    def trace(decision, chosen, created, served):
        body = {"candidates": {"b1": {"sensors": sensors("lo_a", "lo_b")}, "b2": {"sensors": sensors("lo_c", "lo_new")},
                               "stop_for_today": {"sensors": {}}}}
        connection.execute("INSERT INTO router_objective_traces VALUES (?, ?, 'plan_block', ?, ?, ?)",
                           (f"t_{decision}", decision, chosen, json.dumps(body), created))
        if served:
            connection.execute("INSERT INTO plan_presentations VALUES (?, ?, ?)", (f"pp_{decision}", decision, created))

    trace("d1", "b1", "2026-11-01T10:00:00Z", True)
    trace("d2", "b1", "2026-11-02T10:00:00Z", True)
    trace("d3", "stop_for_today", "2026-11-02T11:00:00Z", False)
    trace("d4", "b2", "2026-11-09T10:00:00Z", True)  # after the read's moment: not admitted
    return connection


def test_the_join_takes_the_drawn_blocks_untouched_topics_as_of_the_moment():
    from learnloop.router_objective import combiner_data as CD

    connection = _join_db()
    found, skipped = CD.groups(connection, now="2026-11-05T00:00:00Z")
    assert skipped == {"no_block_served": 1}
    # The drawn option's own topics (lo_a, lo_b) are left out: the block acted on them.
    assert sorted((g["decision_id"], g["learning_object_id"]) for g in found) == [
        ("d1", "lo_c"), ("d1", "lo_new"), ("d2", "lo_c"), ("d2", "lo_new")]
    assert all(g["plan_presentation_id"] == f"pp_{g['decision_id']}" for g in found)


def test_the_join_rows_count_one_outcome_once_per_protocol_and_only_when_known():
    from learnloop.router_objective import combiner_data as CD
    from learnloop.router_objective_switches import available_at

    connection = _join_db()
    connection.executemany("INSERT INTO practice_attempts VALUES (?, ?, ?)", [
        ("att_c", "2026-11-03T10:00:00Z", None),
        ("att_new", "2026-11-03T12:00:00Z", None),
        ("att_late", "2026-11-03T12:00:00Z", "2026-11-06T00:00:00Z"),  # imported after the moment
        ("att_check", "2026-11-04T09:00:00Z", None),
    ])
    found, _skipped = CD.groups(connection, now="2026-11-05T00:00:00Z")
    by = {(g["decision_id"], g["learning_object_id"]): g for g in found}

    def scored(group, attempt, y, binding="per_protocol"):
        return {**{k: v for k, v in group.items() if k != "curve"}, "binding": binding, "status": "scored",
                "attempt_id": attempt, "y": y, "lag_days": 1.0}

    resolved = [
        scored(by[("d1", "lo_c")], "att_c", 1.0), scored(by[("d2", "lo_c")], "att_c", 1.0),  # one answer, two decisions
        scored(by[("d1", "lo_c")], "att_c", 1.0, binding="intention_to_treat"),
        scored(by[("d2", "lo_new")], "att_new", 0.0),
        scored(by[("d1", "lo_new")], "att_late", 1.0),
        scored(by[("d2", "lo_c")], "att_check", 1.0),
        {**by[("d1", "lo_new")], "binding": "per_protocol", "status": "censored", "reason": "intervening_exposure"},
    ]
    lags: list = []

    def retrievability(stability, elapsed):
        lags.append((stability, elapsed))
        return 0.8

    out, counts = CD.rows(connection, resolved, now="2026-11-05T00:00:00Z", known_at=available_at,
                          retrievability=retrievability, exclude={"att_check"})
    assert sorted(out, key=lambda row: row[2]) == [(0.5, None, 0), (0.5, 0.8, 1)]
    assert counts["not_known_by_now"] == 1 and counts["check_answers"] == 1 and counts["duplicates"] == 1
    # att_c joins the latest decision before it (d2, a day before the answer): its R is at elapsed 2 + 1 day.
    assert lags == [(4.0, 3.0)]


@pytest.mark.usefixtures("served_horizon")
def test_the_combiner_is_fitted_on_trace_outcomes_at_the_tag_and_the_trace_names_it(tmp_path, monkeypatch):
    from learnloop.adaptive_difficulty import history_resolve as HR
    from learnloop.daily_plan import objective_inputs as OI
    from learnloop.router_objective import memory as M

    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=TAG)
    run(env)
    calls: list = []

    def resolve_curves(_connection, _vault, _repository, groups, *, now):
        calls.append(now)
        out = []
        for index, group in enumerate(groups):
            attempt = f"planted_{index}"
            out.append({**{k: v for k, v in group.items() if k != "curve"}, "binding": "per_protocol",
                        "status": "scored", "attempt_id": attempt, "y": float(index % 3 != 0), "lag_days": 1.0})
        return out

    monkeypatch.setattr(HR, "resolve_curves", resolve_curves)
    from learnloop.router_objective import combiner_data as CD

    real_rows = CD.rows

    def planted_rows(connection, resolved, **kwargs):
        # The planted answers are not attempts in this vault; every one is known by the moment.
        return real_rows(connection, resolved, **{**kwargs, "known_at": lambda _row: "2000-01-01T00:00:00Z"})

    monkeypatch.setattr(CD, "rows", planted_rows)
    now = env.now_iso()
    item = next(iter(env.vault.practice_items.values()))
    with env.repository.connection() as connection:
        for index in range(200):
            connection.execute("INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, "
                               "attempt_type, created_at) VALUES (?, ?, ?, 'short_answer', 'independent_attempt', ?)",
                               (f"planted_{index}", item.id, item.learning_object_id, now))
        connection.commit()
    fitted = OI._combiner(env.repository, now, env.vault)
    assert calls == [now]
    assert fitted.n > 0 and fitted.sources["trace_outcomes"] == fitted.n and fitted.mean != M.COMBINER_PRIOR_MEAN
    body = fitted.as_dict()
    assert body["fit_version"] == M.COMBINER_FIT_VERSION and body["n"] == fitted.n
    assert body["sources"]["join"]["version"] == CD.JOIN_VERSION
    # Switched off at the tag: RO5's checks-only fit, the predecessor's record exactly.
    from tests.helpers import append_config_toml
    from learnloop.vault.loader import load_vault

    append_config_toml(env.vault.root, "[router_objective]\ncombiner_trace_outcomes = false\n")
    off = OI._combiner(env.repository, now, load_vault(env.vault.root))
    assert off.sources is None and "sources" not in off.as_dict() and off.n == 0


def test_below_the_tag_the_combiner_reads_no_trace(tmp_path, monkeypatch):
    from learnloop.adaptive_difficulty import history_resolve as HR
    from learnloop.daily_plan import objective_inputs as OI

    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=OLD)
    run(env)
    monkeypatch.setattr(HR, "resolve_curves", lambda *a, **k: (_ for _ in ()).throw(AssertionError("read")))
    combiner = OI._combiner(env.repository, env.now_iso(), env.vault)
    assert combiner.sources is None and combiner.n == 0
