"""Router speed, item 2: the combiner's trace join (the follow-up batch's item 2) read once per decision and made
incremental, with the fit unchanged.

* **Once per decision**: inside ``objective_inputs.decision_reads`` (the prefetch job wraps itself in it), every
  build of the decision reads the combiner's fit once (the card's build for the LLM policy's reference row, then the
  numeric policy's; about 2.4 joins a decision before) while no write has been committed since that read (Codex
  review F2: the database's ``PRAGMA data_version``, through a watcher the scope holds), so a regrade or a hold
  committed between the card's build and the numeric policy's reaches the numeric policy. Nothing outlives the scope,
  so the next decision reads afresh: a regrade, a hold, a late-received outcome or late activity enters it.
* **Incremental on the trace side**: each plan-block trace's untouched topics and sensors are parsed once per trace
  content (``combiner_data._untouched``, keyed by a digest of the drawn option and the whole JSON text), and each
  decision's first served presentation is one read, not one query per trace. The outcome side is read at every call.
* **Linear in the LO's rows**: RO2's resolver indexes the rows by presentation and by LO once (every group scanned
  every attempt, reveal and reading: the join grew with the square of the log).

Every test compares with the code at the follow-up batch's landing (``516db1d862``), copied below verbatim but for
names: the groups, the resolver's rows and the fit (its coefficients' bits, its sources and counts), on a journey's
real traces with cold outcomes answered through the real pipeline, after a regrade, a hold, a late-received
outcome and late activity. Fakes only; no model request.
"""

from __future__ import annotations

from contextlib import closing
from datetime import timedelta
import json
import random
import sqlite3
from typing import Any

import pytest

from learnloop.adaptive_difficulty import history_resolve as HR
from learnloop.clock import parse_utc
from learnloop.daily_plan import objective_inputs as OI
from learnloop.router_objective import combiner_data as CD
from tests.rospeed_join_helpers import _journey

# -- the code at 516db1d862, verbatim but for names --------------------------------------------------------------


def _old_groups(connection: Any, *, now: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    from collections.abc import Mapping

    from learnloop.db.stores import router_objective as store

    if not store.table_present(connection, store.TRACES):
        return [], {}
    skipped: dict[str, int] = {}
    found: list[dict[str, Any]] = []
    for row in connection.execute(
            "SELECT decision_id, chosen_ref, trace_json, created_at FROM router_objective_traces "
            "WHERE decision_kind = 'plan_block' AND created_at <= ? ORDER BY created_at, id", (now,)):
        chosen = str(row["chosen_ref"])
        trace = json.loads(row["trace_json"])
        candidates = trace.get("candidates") or {}
        served = connection.execute(
            "SELECT id FROM plan_presentations WHERE router_decision_id = ? AND served_at <= ? "
            "ORDER BY served_at, id LIMIT 1", (row["decision_id"], now)).fetchone()
        if served is None:
            skipped["no_block_served"] = skipped.get("no_block_served", 0) + 1
            continue
        drawn = set(((candidates.get(chosen) or {}).get("sensors") or {}))
        sensors: dict[str, Mapping[str, Any]] = {}
        for entry in candidates.values():
            for lo, values in ((entry or {}).get("sensors") or {}).items():
                if lo == "llm_forecast" or lo in drawn or not isinstance(values, Mapping):
                    continue
                if values.get("ad_eta") is None:
                    continue
                sensors.setdefault(str(lo), values)
        if not sensors:
            skipped["no_untouched_topic"] = skipped.get("no_untouched_topic", 0) + 1
            continue
        for lo, values in sorted(sensors.items()):
            found.append({"plan_presentation_id": str(served[0]), "learning_object_id": lo,
                          "forecaster": CD.FORECASTER, "curve": dict(CD._FLAT_CURVE),
                          "decision_id": str(row["decision_id"]), "decided_at": str(row["created_at"]),
                          "sensors": {"eta": float(values["ad_eta"]), "stability": float(values.get("fsrs_stability")
                                                                                         or 0.0),
                                      "elapsed": float(values.get("fsrs_elapsed_days") or 0.0),
                                      "practiced": bool(values.get("practiced"))}})
    return found, skipped


def _old_resolve_groups(connection, vault, repository, view, groups, *, now):
    from learnloop.adaptive_difficulty import outcomes as O
    from learnloop.adaptive_difficulty import replay as RP

    if not groups:
        return []
    presentations = view.presentations(connection)
    attempts = view.attempts(connection)
    events = {event.attempt_id: event for event in RP.load_events(connection, vault, repository, view=view).attempts}
    reveals = view.reveals(connection)
    readings = HR._opportunities(connection, vault, repository, view, now=now)
    first_seen: dict[str, str] = {}
    for row in attempts:
        first_seen.setdefault(str(row["practice_item_id"]), str(row["id"]))
    by_block: dict[str, set[str]] = {}
    for pid, row in presentations.items():
        by_block.setdefault(str(row.get("block_id")), set()).add(pid)
    out: list[dict[str, Any]] = []
    for group in groups:
        presentation = presentations.get(group["plan_presentation_id"])
        base = {"resolver_version": HR.RESOLVER_VERSION, **{k: v for k, v in group.items() if k != "curve"},
                "conditional_on_observation": True}
        if presentation is None:
            out += [{**base, "binding": binding, "status": "pending", "reason": "no_presentation"}
                    for binding in HR.BINDINGS]
            continue
        lo = str(group["learning_object_id"] or "")
        block = by_block.get(str(presentation.get("block_id")), {group["plan_presentation_id"]})
        block_attempts = [row for row in attempts if str(row.get("plan_presentation_id") or "") in block]
        block_end = max([str(presentation["served_at"])] + [str(row["created_at"]) for row in block_attempts])
        block_ids = {str(row["id"]) for row in block_attempts}
        on_lo = [row for row in attempts if str(row.get("learning_object_id")) == lo]
        candidate, passed = None, []
        for row in on_lo:
            if str(row["id"]) in block_ids or str(row["created_at"]) <= block_end:
                continue
            if first_seen.get(str(row["practice_item_id"])) != str(row["id"]):
                continue
            event = events.get(str(row["id"]))
            category = event.category if event is not None else None
            if event is None or not event.eligible or category is None:
                passed.append({"attempt_id": str(row["id"]), "why": (event.reason if event is not None else "no_event")
                               or "not_graded"})
                continue
            candidate = (row, category)
            break
        if candidate is None:
            waited = HR._days(now, block_end)
            beyond = waited is not None and waited > HR.MAX_LAG_DAYS
            out += [{**base, "binding": binding, "status": "censored" if beyond else "pending",
                     "reason": "beyond_measured_lag" if beyond else "no_qualifying_outcome",
                     "passed_over": passed} for binding in HR.BINDINGS]
            continue
        row, category = candidate
        at = str(row["created_at"])
        touches = (
            [{"kind": "attempt", "id": str(other["id"]), "at": str(other["created_at"]),
              "in_block": str(other["id"]) in block_ids} for other in on_lo]
            + [{"kind": "reveal", "id": str(reveal["id"]), "at": str(reveal["created_at"]),
                "source_kind": reveal.get("source_kind")} for reveal in reveals
               if str(reveal.get("learning_object_id") or "") == lo]
            + [{"kind": "reading", "id": str(reading["id"]), "at": str(reading["at"]), "subkind": reading.get("subkind")}
               for reading in readings if reading["learning_object_id"] == lo])
        before = [touch for touch in touches if (HR._days(at, touch["at"]) or 0.0) > 0.0]
        exposures = [{k: v for k, v in touch.items() if k != "in_block"} for touch in before
                     if not touch.get("in_block") and (HR._days(touch["at"], block_end) or 0.0) > 0.0]
        lag = HR._days(at, block_end) or 0.0
        latest = max(before, key=lambda touch: parse_utc(touch["at"])) if before else None
        delay = HR._days(at, latest["at"]) if latest is not None else None
        found = {**base, "attempt_id": str(row["id"]), "lag_days": round(lag, 6),
                 "delay_since_exposure_days": None if delay is None else round(delay, 6),
                 "category": category, "outcome_state": HR._outcome_state(row, category),
                 "exposures": sorted(exposures, key=lambda e: (parse_utc(e["at"]), e["id"])),
                 "passed_over": passed}
        for binding in HR.BINDINGS:
            if lag > HR.MAX_LAG_DAYS:
                out.append({**found, "binding": binding, "status": "censored", "reason": "beyond_measured_lag"})
                continue
            if binding == HR.PER_PROTOCOL and exposures:
                out.append({**found, "binding": binding, "status": "censored", "reason": "intervening_exposure"})
                continue
            p = HR.interpolate(group["curve"], max(lag, 1e-9))
            y = O.unassisted_success(category)
            out.append({**found, "binding": binding, "status": "scored", "p": p, "y": y,
                        "log_loss": HR._log_loss(p, y), "brier": None if p is None or y is None else (p - y) ** 2})
    return out


def _landing_code(patch) -> None:
    patch.setattr(CD, "groups", _old_groups)
    patch.setattr(HR, "_resolve_groups", _old_resolve_groups)


# -- the resolver's loop: randomized rows through a fake view ------------------------------------------------------


class _Event:
    def __init__(self, attempt_id: str, eligible: bool, category: int | None, reason: str | None) -> None:
        self.attempt_id, self.eligible, self.category, self.reason = attempt_id, eligible, category, reason


class _View:
    def __init__(self, presentations, attempts, reveals) -> None:
        self._p, self._a, self._r = presentations, attempts, reveals

    def presentations(self, _connection):
        return self._p

    def attempts(self, _connection):
        return self._a

    def reveals(self, _connection):
        return self._r


def _random_log(seed: int):
    rng = random.Random(seed)
    los = [f"lo{i}" for i in range(rng.randint(1, 6))] + [None]
    stamp = lambda minutes: (parse_utc("2026-10-01T08:00:00Z") + timedelta(minutes=minutes)).strftime(  # noqa: E731
        "%Y-%m-%dT%H:%M:%SZ")
    presentations = {}
    for index in range(rng.randint(1, 12)):
        presentations[f"pp{index}"] = {"block_id": f"b{rng.randint(0, 5)}", "served_at": stamp(rng.randint(0, 40000))}
    attempts, events = [], []
    for index in range(rng.randint(0, 60)):
        lo = rng.choice(los)
        attempts.append({"id": f"a{index}", "practice_item_id": f"pi{rng.randint(0, 25)}", "learning_object_id": lo,
                         "plan_presentation_id": rng.choice([*presentations, None, ""]),
                         "created_at": stamp(rng.randint(0, 60000)), "primed": rng.random() < 0.2})
        if rng.random() < 0.85:
            events.append(_Event(f"a{index}", rng.random() < 0.8, rng.choice([0, 1, 2, -1, None]),
                                 rng.choice([None, "help", "not_graded"])))
    attempts.sort(key=lambda row: (row["created_at"], row["id"]))
    reveals = [{"id": f"r{index}", "learning_object_id": rng.choice(los), "created_at": stamp(rng.randint(0, 60000)),
                "source_kind": "tutor_answer"} for index in range(rng.randint(0, 15))]
    readings = [{"id": f"x{index}", "learning_object_id": rng.choice([lo for lo in los if lo]) if los[0] else "lo0",
                 "at": stamp(rng.randint(0, 60000)), "subkind": "section_read"} for index in range(rng.randint(0, 15))]
    groups = [{"plan_presentation_id": rng.choice([*presentations, "missing"]),
               "learning_object_id": rng.choice(los), "forecaster": CD.FORECASTER, "curve": dict(CD._FLAT_CURVE),
               "decision_id": f"d{index}"} for index in range(rng.randint(1, 30))]
    return _View(presentations, attempts, reveals), events, readings, groups


@pytest.mark.parametrize("seed", range(60))
def test_the_indexed_resolver_gives_the_landing_codes_rows(seed, monkeypatch):
    from types import SimpleNamespace

    from learnloop.adaptive_difficulty import replay as RP

    view, events, readings, groups = _random_log(seed)
    monkeypatch.setattr(RP, "load_events", lambda *_a, **_k: SimpleNamespace(attempts=events))
    monkeypatch.setattr(HR, "_opportunities", lambda *_a, **_k: readings)
    now = "2026-11-20T00:00:00Z"
    new = HR._resolve_groups(None, None, None, view, groups, now=now)
    old = _old_resolve_groups(None, None, None, view, groups, now=now)
    assert new == old
    assert json.dumps(new, sort_keys=True, default=str) == json.dumps(old, sort_keys=True, default=str)


# -- the trace side: groups -------------------------------------------------------------------------------------


def _traces_db():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        "CREATE TABLE router_objective_traces (id TEXT, decision_id TEXT, decision_kind TEXT, chosen_ref TEXT, "
        "trace_json TEXT, created_at TEXT);"
        "CREATE TABLE plan_presentations (id TEXT, router_decision_id TEXT, served_at TEXT);")

    def sensors(*los, eta=0.5):
        return {lo: {"ad_eta": eta, "fsrs_stability": 4.0, "fsrs_elapsed_days": 2.0, "practiced": lo != "lo_new"}
                for lo in los}

    def trace(decision, chosen, created, served=(), kind="plan_block", extra=None):
        body = {"candidates": {"b1": {"sensors": sensors("lo_a", "lo_b")},
                               "b2": {"sensors": {**sensors("lo_c", "lo_new"), "llm_forecast": {"p": 0.4},
                                                  "lo_none": {"ad_eta": None}}},
                               "b3": {"sensors": sensors("lo_c", eta=0.9)},
                               "stop_for_today": {"sensors": {}}, **(extra or {})}}
        connection.execute("INSERT INTO router_objective_traces VALUES (?, ?, ?, ?, ?, ?)",
                           (f"t_{decision}", decision, kind, chosen, json.dumps(body), created))
        for index, at in enumerate(served):
            connection.execute("INSERT INTO plan_presentations VALUES (?, ?, ?)", (f"pp_{decision}_{index}", decision, at))

    trace("d1", "b1", "2026-11-01T10:00:00Z", ("2026-11-01T10:00:00Z",))
    # two presentations: the earlier one is the block's; one tie on served_at, broken by id
    trace("d2", "b2", "2026-11-02T10:00:00Z", ("2026-11-02T10:05:00Z", "2026-11-02T10:01:00Z", "2026-11-02T10:01:00Z"))
    trace("d3", "stop_for_today", "2026-11-02T11:00:00Z")
    trace("d4", "b3", "2026-11-03T10:00:00Z", ("2026-11-06T10:00:00Z",))  # served after the moment
    trace("d5", "b1", "2026-11-03T11:00:00Z", ("2026-11-03T11:00:00Z",), kind="plan_interrupt")
    trace("d6", "b1", "2026-11-09T10:00:00Z", ("2026-11-09T10:00:00Z",))  # after the moment
    trace("d7", "b2", "2026-11-04T10:00:00Z", ("2026-11-04T10:00:00Z",),
          extra={"b1": {"sensors": {}}, "b3": {"sensors": {}}})  # every other option's topics are its own
    return connection


@pytest.mark.parametrize("now", ["2026-11-01T09:00:00Z", "2026-11-02T10:03:00Z", "2026-11-05T00:00:00Z",
                                 "2026-11-07T00:00:00Z", "2026-12-01T00:00:00Z"])
def test_the_groups_are_the_landing_codes(now):
    connection = _traces_db()
    assert CD.groups(connection, now=now) == _old_groups(connection, now=now)
    # read again (the parsed traces held): the same
    assert CD.groups(connection, now=now) == _old_groups(connection, now=now)


def test_a_rewritten_trace_is_parsed_again():
    connection = _traces_db()
    now = "2026-11-05T00:00:00Z"
    before, _ = CD.groups(connection, now=now)
    body = json.loads(connection.execute("SELECT trace_json FROM router_objective_traces WHERE id = 't_d1'").fetchone()[0])
    body["candidates"]["b2"]["sensors"]["lo_c"]["ad_eta"] = -1.25
    connection.execute("UPDATE router_objective_traces SET trace_json = ? WHERE id = 't_d1'", (json.dumps(body),))
    after, _ = CD.groups(connection, now=now)
    assert after == _old_groups(connection, now=now)[0] and after != before
    assert [g["sensors"]["eta"] for g in after if g["decision_id"] == "d1" and g["learning_object_id"] == "lo_c"] == [
        -1.25]
    # a group's sensors are its own copy: a caller's edit never reaches the held parse
    after[0]["sensors"]["eta"] = 99.0
    assert CD.groups(connection, now=now)[0] == _old_groups(connection, now=now)[0]


def test_the_parsed_traces_are_bounded(monkeypatch):
    monkeypatch.setattr(CD, "_PARSED", {})
    monkeypatch.setattr(CD, "_PARSED_LIMIT", 3)
    connection = _traces_db()
    now = "2026-12-01T00:00:00Z"
    assert CD.groups(connection, now=now) == _old_groups(connection, now=now)
    assert len(CD._PARSED) <= 3


# -- the fit, on a journey's real traces, with cold outcomes answered through the real pipeline -------------------


def _answer(env, item_id: str, *, correct: bool, at) -> str:
    """A cold outcome graded through the real pipeline (a self-grade), at ``at``."""

    from learnloop.clock import FrozenClock

    from tests.ad23_fakes import answer

    return answer(_paths(env), item_id, correct=correct, session_id=env.session_id, clock=FrozenClock(at))


def _paths(env):
    from learnloop.vault.paths import VaultPaths

    return VaultPaths(env.vault.root, env.vault.config)


def _regrade(env, attempt_id: str, when, *, correct: bool) -> None:
    """A regrade through the repository (every criterion re-graded over the tiers it replaces)."""

    from learnloop.attempts.attempts import unverified_attribution_json
    from learnloop.attempts.grading import resolved_rubric
    from learnloop.clock import FrozenClock

    from tests.held_grade_evidence_helpers import _iso

    attempt = env.repository.fetch_practice_attempt(attempt_id)
    rubric = resolved_rubric(env.vault, env.vault.practice_items[attempt["practice_item_id"]])
    rows = [{"id": f"ge_regrade_{attempt_id}_{criterion.id}", "criterion_id": criterion.id,
             "points_awarded": float(criterion.max_points) if correct else 0.0, "evidence": "regraded", "notes": None,
             "agent_run_id": None, "local_grader_id": None, "grader_tier": 3, "created_at": _iso(when),
             "attribution_json": unverified_attribution_json()} for criterion in rubric.criteria]
    env.repository.insert_regrade_evidence(attempt_id=attempt_id, new_evidence_rows=rows,
                                           superseded_by_evidence_id=rows[0]["id"], supersede_tiers=(1, 3, 4),
                                           clock=FrozenClock(when))


def _cold_items(env) -> list[tuple[str, str, str]]:
    """(decision, untouched LO, an item of the LO never attempted), one per LO, for groups whose LO nothing touched
    after the decision: a first answer on it is then a cold outcome with no exposure in between."""

    with env.repository.connection() as connection:
        found, _skipped = CD.groups(connection, now="2100-01-01T00:00:00Z")
        attempts = [dict(row) for row in connection.execute(
            "SELECT practice_item_id, learning_object_id, created_at FROM practice_attempts")]
    attempted = {row["practice_item_id"] for row in attempts}
    latest: dict[str, dict] = {}
    for group in sorted(found, key=lambda g: (g["decided_at"], g["decision_id"])):
        latest[group["learning_object_id"]] = group
    out = []
    for lo, group in sorted(latest.items()):
        if any(row["learning_object_id"] == lo and row["created_at"] >= group["decided_at"] for row in attempts):
            continue
        unseen = sorted(item.id for item in env.vault.practice_items.values()
                        if item.learning_object_id == lo and item.id not in attempted)
        if unseen:
            out.append((group["decision_id"], lo, unseen[0]))
    return out


def _fit(env, now: str, vault=None):
    """The fit and its record, exactly (the coefficients' bits)."""

    combiner = OI._combiner(env.repository, now, vault or env.vault)
    body = combiner.as_dict()
    return ([float(v).hex() for v in combiner.mean], [float(v).hex() for v in combiner.variance], combiner.n,
            json.dumps(body, sort_keys=True, default=str))


def _both(env, now: str, monkeypatch, vault=None):
    new = _fit(env, now, vault)
    with monkeypatch.context() as patch:
        _landing_code(patch)
        old = _fit(env, now, vault)
    assert new == old
    return new


def test_the_fit_is_the_landing_codes_through_regrades_holds_late_outcomes_and_late_activity(tmp_path, monkeypatch):
    from learnloop.vault.loader import load_vault

    env = _journey(tmp_path)
    cold = _cold_items(env)
    assert len(cold) >= 4, cold
    start = env.clock.now()
    answered = []
    for index, (_decision, _lo, item) in enumerate(cold[:4]):
        answered.append(_answer(env, item, correct=index % 2 == 0, at=start + timedelta(hours=2 + index)))
    now = (start + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    stamp = lambda hours: (start + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    fits = {"answered": _both(env, now, monkeypatch)}
    # a regrade: the first cold outcome (a success) re-graded a failure
    _regrade(env, answered[0], start + timedelta(hours=6), correct=False)
    fits["regraded"] = _both(env, now, monkeypatch)
    # a hold: the second cold outcome regraded into a hold for review (a held blind record)
    from tests.held_grade_evidence_helpers import _hold_by_regrade

    _hold_by_regrade(env.vault, env.repository, answered[1], start + timedelta(hours=7))
    fits["held"] = _both(env, now, monkeypatch)
    # a late-received outcome: the third answer arrived after the moment (at RO1's tag: not known by then)
    with closing(sqlite3.connect(_paths(env).sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET received_at = ? WHERE id = ?", (stamp(72), answered[2]))
        connection.commit()
    fits["late_outcome"] = _both(env, now, monkeypatch)
    # late activity: a reveal on the fourth outcome's LO, stamped between its block and it, recorded afterwards
    with closing(sqlite3.connect(_paths(env).sqlite_path)) as connection:
        connection.execute("INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, "
                           "basis, created_at) VALUES ('rv_late', ?, ?, 'tutor_answer', 0.5, 'overlap', ?)",
                           (cold[3][2], cold[3][1], stamp(1)))
        connection.commit()
    fits["late_activity"] = _both(env, now, monkeypatch, load_vault(env.vault.root))
    counts = {name: (fit[2], json.loads(fit[3])["sources"]["join"]["per_protocol"]) for name, fit in fits.items()}
    print("ROSPEED_JOIN", json.dumps(counts, sort_keys=True))
    # each change moved the fit (no stale read anywhere): the joined rows fall one by one
    assert [fit[2] for fit in fits.values()] == [4, 3, 2, 1, 0]
    assert len({fit[3] for fit in fits.values()}) == 5


def test_one_decisions_builds_read_the_fit_once_and_the_next_decision_afresh(tmp_path, monkeypatch):
    env = _journey(tmp_path)
    cold = _cold_items(env)
    start = env.clock.now()
    attempt = _answer(env, cold[0][2], correct=True, at=start + timedelta(hours=2))
    now = (start + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    calls: list[str] = []
    real = HR.resolve_curves

    def counted(*args, **kwargs):
        calls.append(kwargs.get("now"))
        return real(*args, **kwargs)

    monkeypatch.setattr(HR, "resolve_curves", counted)
    outside = [OI._combiner(env.repository, now, env.vault) for _ in range(2)]
    assert len(calls) == 2
    calls.clear()
    with OI.decision_reads():
        inside = [OI._combiner(env.repository, now, env.vault) for _ in range(3)]
        assert inside[0] is inside[1] is inside[2]
        # another moment, or another vault object, is its own read
        OI._combiner(env.repository, "2100-01-01T00:00:00Z", env.vault)
    assert len(calls) == 2
    assert outside[0] == outside[1] == inside[0]
    # a regrade between two decisions: the next decision's read sees it
    _regrade(env, attempt, start + timedelta(hours=6), correct=False)
    with OI.decision_reads():
        after = OI._combiner(env.repository, now, env.vault)
    assert after == OI._combiner(env.repository, now, env.vault)
    assert after.as_dict() != inside[0].as_dict()


def test_the_prefetch_job_reads_the_fit_again_only_after_a_commit(tmp_path, monkeypatch):
    """The journey's prefetch jobs (the card's build, then the numeric policy's): a decision's fit is read again only
    when a write was committed to the database since its last read (Codex review F2), never twice on one version."""

    from learnloop.daily_plan import objective_chooser as OC

    reads: list[tuple[str, Any]] = []
    real = OI._combiner_read

    def counted(repository, now_iso, vault=None):
        reads.append((now_iso, OI._DECISION_READS.get().version(repository)))
        return real(repository, now_iso, vault)

    monkeypatch.setattr(OI, "_combiner_read", counted)
    builds: list[str] = []
    real_build = OI.build

    def counted_build(*args, **kwargs):
        builds.append(kwargs["now_iso"])
        return real_build(*args, **kwargs)

    monkeypatch.setattr(OC.OI, "build", counted_build)
    _journey(tmp_path)
    assert builds and len(reads) <= len(builds), (builds, reads)
    assert {now for now, _version in reads} == set(builds)
    for now in set(builds):
        versions = [version for at, version in reads if at == now]
        assert len(set(versions)) == len(versions), versions  # each re-read follows a commit
    print("ROSPEED_JOB_READS", json.dumps({"builds": len(builds), "reads": len(reads)}))


# -- Codex review F2: a write committed inside one decision's scope is read --------------------------------------


def _answered_journey(tmp_path):
    """A journey with two cold outcomes answered (a success, then a failure) and the clock a day on, so a decision
    made now joins them and a regrade or a hold of either moves the fit."""

    env = _journey(tmp_path)
    cold = _cold_items(env)
    assert len(cold) >= 2, cold
    start = env.clock.now()
    answered = [_answer(env, item, correct=index == 0, at=start + timedelta(hours=2 + index))
                for index, (_decision, _lo, item) in enumerate(cold[:2])]
    env.clock.advance(24 * 60)
    return env, start, answered


def _change(env, start, answered, change: str) -> None:
    if change == "regrade":  # the success re-graded a failure
        _regrade(env, answered[0], start + timedelta(hours=6), correct=False)
    else:  # the success regraded into a hold for review (a held blind record)
        from tests.held_grade_evidence_helpers import _hold_by_regrade

        _hold_by_regrade(env.vault, env.repository, answered[0], start + timedelta(hours=7))


@pytest.mark.parametrize("change", ["regrade", "hold"])
def test_a_regrade_or_hold_inside_one_decisions_scope_is_read(tmp_path, change):
    """Inside :func:`OI.decision_reads`, a write committed after the first read is read by the next one: the held
    fit is the fresh read's, never the earlier one (``checks.Closure``: grades and holds as they stand now)."""

    env, start, answered = _answered_journey(tmp_path)
    now = env.clock.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    with OI.decision_reads():
        first = OI._combiner(env.repository, now, env.vault)
        assert OI._combiner(env.repository, now, env.vault) is first  # nothing committed: one read
        _change(env, start, answered, change)
        second = OI._combiner(env.repository, now, env.vault)
        assert OI._combiner(env.repository, now, env.vault) is second
    fresh = OI._combiner_read(env.repository, now, env.vault)
    assert second.as_dict() == fresh.as_dict()
    assert second.as_dict() != first.as_dict()


@pytest.mark.parametrize("change", ["regrade", "hold"])
def test_a_regrade_or_hold_between_the_jobs_card_and_numeric_builds_reaches_the_numeric_policy(
        tmp_path, monkeypatch, change):
    """Codex review F2's window: the prefetch job builds the LLM policy's card, then the numeric policy's inputs, in
    one :func:`OI.decision_reads` scope. A regrade or a hold committed between the two reaches the numeric policy's
    fit (a fresh read's), as it did when every build read afresh."""

    from learnloop.daily_plan import objective_card as OCARD

    from tests.daily_plan_fakes import record_attempt
    from tests.router_mixture_helpers import advance

    env, start, answered = _answered_journey(tmp_path)
    # each build's fit, beside a fresh read at the same moment (the job's own trace, written after, adds a group)
    fits: list[tuple[str, dict, dict]] = []
    real = OI._combiner

    def recorded(repository, now_iso, vault=None):
        combiner = real(repository, now_iso, vault)
        fits.append((now_iso, combiner.as_dict(), OI._combiner_read(repository, now_iso, vault).as_dict()))
        return combiner

    monkeypatch.setattr(OI, "_combiner", recorded)
    armed = {"on": True}
    real_card = OCARD.decision_card

    def card(*args, **kwargs):
        if armed["on"]:
            armed["on"] = False
            _change(env, start, answered, change)
        return real_card(*args, **kwargs)

    monkeypatch.setattr(OCARD, "decision_card", card)
    for _ in range(12):  # served on through the block to the next boundary's prefetch job
        fits.clear()
        _record, step = advance(env, serve=True)
        if not armed["on"] or step is None or step["kind"] != "item":
            break
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
    assert not armed["on"], "the job built no card"
    now = fits[0][0]
    mine = [(held, fresh) for at, held, fresh in fits if at == now]
    assert len(mine) >= 2, fits  # the card's build, then the numeric policy's
    assert mine[0][0] == mine[0][1]
    assert mine[1][1]["n"] != mine[0][1]["n"]  # the write moved the fit
    for held, fresh in mine[1:]:
        assert held == fresh
