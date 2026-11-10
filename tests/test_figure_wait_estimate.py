"""The figure wait estimate (mvp-0.58, ``prefetch_decision_v2``; docs/reviews/figure-wait-estimate.md).

Found in refactor B4 (docs/reviews/refactor-b4.md, step 0): the figure pre-builder meant to leave its own background
calls out of W (the minutes a press would wait for the quick tiers) and out of the blocked minutes, with
``owner_kind NOT LIKE 'prefetch%'`` and ``startswith("prefetch")``; no figure receipt's owner kind starts with
``prefetch``, so neither filter removed anything. Owner decision: "W from pressed builds with a prior; cost from
foreground minutes only".

* **Which call is whose**: a figure author receipt's owner (``figure:<content_key(input, generation)>``) names the
  stored figure of its build, whose building request carries the build mode (``call_build_modes``); the judge's
  calls are always the pre-builder's.
* **W**: the pressed calls' log-normal mean, shrunk toward the other calls' by a prior worth one measurement
  (``wait_estimate``): however many background calls there are, they move W only through that prior.
* **The blocked minutes**: foreground failures inside a pause window times the foreground calls' latency.
* **The switch** ``figures.prefetch.pressed_waits`` (and any vault below the tag): ``prefetch_decision_v1``,
  today's numbers exactly. With no measured pause the cost is 0 and the decision, its propensity and the draw
  order are the same either way.
* **The records**: a ``figure_prebuild`` record carries W's basis (pressed n, prior, posterior) and what the
  blocked minutes counted, numbers only.

Fakes only (the figure author); no model is reached.
"""

from __future__ import annotations

import hashlib
import json
import math
from contextlib import closing
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
import pytest

from learnloop import provenance
from learnloop.algorithm_versions import FIGURE_WAIT_ALGORITHM_VERSION, SLIP_GAP_ALGORITHM_VERSION
from learnloop.db.connection import connect
from learnloop.figures import power as P
from learnloop.figures import prefetch as PF
from learnloop.figures import prefetch_ledger as PL
from learnloop.figures import prefetch_model as PM
from learnloop.figures import records as FR
from learnloop.figures import service as FS
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import EXTRACTION, AuthorFake, build_figure_vault, set_config
from tests.helpers import set_algorithm_version

NOW = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
PROVIDER = AuthorFake.provider_name
PAUSE_AT = datetime(2026, 11, 1, 9, 0, tzinfo=UTC)
#: The prefetch judge's receipts' purpose (``PL.JUDGE_PURPOSE``), spelled out so the fail-first run reads it on v1.
JUDGE = "figure_prefetch_judge"


@pytest.fixture(autouse=True)
def mains():
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    yield
    P.set_power_reader(None)


def _iso(when: datetime) -> str:
    return when.isoformat()


def ledger(tmp_path: Any, **figures: Any) -> tuple[Any, Any, Any, str, str]:
    """A vault with one pressed build and one pre-build (real builds, fake author): the pressed and the background
    author calls' owners."""

    paths, repository = build_figure_vault(tmp_path / "vault")
    set_config(paths, "figures", prefetch_enabled=True)
    if figures:
        set_config(paths, "figures.prefetch", **figures)
    vault = load_vault(paths.root)
    FS.build_figure(vault, repository, FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]),
                    author_client=AuthorFake())
    with repository.connection() as connection:
        pressed = {row[0] for row in connection.execute(
            "SELECT owner_id FROM model_call_receipts WHERE purpose = 'figure_author'")}
    FS.build_prefetch_figure(vault, repository, FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p2"],
                                                                 origin="prefetch"), author_client=AuthorFake())
    with repository.connection() as connection:
        owners = {row[0] for row in connection.execute(
            "SELECT owner_id FROM model_call_receipts WHERE purpose = 'figure_author'")}
        modes = {row[0] for row in connection.execute("SELECT build_mode FROM figure_requests")}
    (press,), (background,) = pressed, owners - pressed
    assert modes == {"pressed", "prefetch"}
    return paths, repository, vault, press, background


def time_calls(repository: Any, owner: str, seconds: float) -> None:
    """Every completed author call of ``owner`` took ``seconds``."""

    start = datetime(2026, 10, 1, 10, 0, tzinfo=UTC)
    with repository.connection() as connection:
        connection.execute("UPDATE model_call_receipts SET started_at = ?, finished_at = ? WHERE owner_id = ? "
                           "AND purpose = 'figure_author'",
                           (_iso(start), _iso(start + timedelta(seconds=seconds)), owner))
        connection.commit()


def add_calls(repository: Any, owner: str, count: int, *, seconds: float = 6.0, status: str = "completed",
              purpose: str = "figure_author", at: datetime | None = None) -> None:
    """``count`` more receipts of ``owner`` (a build's further attempts, or the judge's calls)."""

    start = at or datetime(2026, 10, 1, 11, 0, tzinfo=UTC)
    with repository.connection() as connection:
        for index in range(count):
            begun = start + timedelta(minutes=index)
            connection.execute(
                "INSERT INTO model_call_receipts (id, owner_kind, owner_id, purpose, provider, status, started_at, "
                "finished_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (f"mcr_{purpose}_{owner[-6:]}_{status}_{index}_{start.minute}_{start.hour}", purpose, owner, purpose,
                 PROVIDER, status, _iso(begun), _iso(begun + timedelta(seconds=seconds))))
        connection.commit()


def add_pause(repository: Any) -> None:
    with repository.connection() as connection:
        connection.execute("INSERT INTO plan_usage_pauses (id, hit_at, reset_at, observed_at) VALUES (?, ?, ?, ?)",
                           ("pause_1", _iso(PAUSE_AT), _iso(PAUSE_AT + timedelta(hours=5)), _iso(PAUSE_AT)))
        connection.commit()


def model(repository: Any, **kwargs: Any) -> PM.Model:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return PL.load_model(connection, {PROVIDER}, now=NOW, **kwargs)


def durations(repository: Any, *, status: str = "completed", purpose: str | None = "figure_author") -> list[float]:
    sql = "SELECT started_at, finished_at FROM model_call_receipts WHERE status = ? AND provider = ?"
    params: tuple[Any, ...] = (status, PROVIDER)
    if purpose:
        sql += " AND purpose = ?"
        params += (purpose,)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return [PL._minutes(start, end) for start, end in connection.execute(sql, params)]


# ---------------------------------------------------------------------------
# Which call is whose
# ---------------------------------------------------------------------------

def test_each_author_call_is_named_by_its_builds_mode_from_the_ledger(tmp_path):
    _paths, repository, _vault, press, background = ledger(tmp_path)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        modes = PL.call_build_modes(connection)
    assert modes[press] == "pressed" and modes[background] == "prefetch"
    # No receipt says it: the owner kinds are the route's task for a press and a pre-build alike.
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        kinds = {row[0] for row in connection.execute(
            "SELECT owner_kind FROM model_call_receipts WHERE purpose = 'figure_author'")}
    assert kinds == {"figure_author"}
    assert PL.JUDGE_PURPOSE == JUDGE
    judge = {"purpose": JUDGE, "owner_id": "prefetch_judge:x"}
    assert PL.background_call(judge, modes)
    assert PL.background_call({"purpose": "figure_author", "owner_id": background}, modes)
    assert not PL.background_call({"purpose": "figure_author", "owner_id": press}, modes)
    # A figure call no stored build names (a refused build alone) is read as foreground.
    assert not PL.background_call({"purpose": "figure_author", "owner_id": "figure:unowned"}, modes)
    assert not PL.background_call({"purpose": "grading", "owner_id": background}, modes)


def test_a_rich_figures_calls_are_named_by_the_rich_jobs_own_key_and_a_reuse_never_relabels_a_build(tmp_path):
    from learnloop.db.stores.figures import FIGURE_COLUMNS
    from learnloop.figures import rich as RICH

    _paths, repository, _vault, press, background = ledger(tmp_path)
    with repository.connection() as connection:
        quick = {row[1]: (row[0], row[2]) for row in connection.execute(
            "SELECT f.id, r.build_mode, f.input_hash FROM interactive_figures f JOIN figure_requests r "
            "ON r.id = f.request_id")}
        figure_id, input_hash = quick["prefetch"]
        # The pre-build's fuller version (a rich figure following its quick one, stored by its rich job) ...
        columns = [name for name in FIGURE_COLUMNS if name not in ("id", "tier", "spec_version", "fuller_of_id")]
        connection.execute(
            f"INSERT INTO interactive_figures (id, tier, spec_version, fuller_of_id, {', '.join(columns)}) "
            f"SELECT 'fig_rich', 'manim', 'manim-fig-v1', id, {', '.join(columns)} FROM interactive_figures WHERE id = ?",
            (figure_id,))
        # ... and a later press that reused the pre-built figure (its request names the figure, made no call).
        connection.execute(
            "INSERT INTO figure_requests (id, origin, anchor_json, policy, caller_kind, grounding, build_mode, figure_id, "
            "created_at) SELECT 'freq_reuse', 'selection', anchor_json, policy, caller_kind, grounding, 'pressed', ?, "
            "created_at FROM figure_requests WHERE build_mode = 'prefetch'", (figure_id,))
        connection.commit()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        modes = PL.call_build_modes(connection)
    rich_owner = f"figure_rich:{RICH.content_key_for({'input_hash': input_hash, 'fast_figure_id': figure_id, 'generation': 0})}"
    assert modes[rich_owner] == "prefetch" and modes[background] == "prefetch" and modes[press] == "pressed"


# ---------------------------------------------------------------------------
# W: background calls move it only through the prior (fail-first on prefetch_decision_v1)
# ---------------------------------------------------------------------------

def test_background_calls_do_not_outweigh_the_presses_in_w(tmp_path):
    _paths, repository, _vault, press, background = ledger(tmp_path)
    time_calls(repository, press, 60.0)
    time_calls(repository, background, 6.0)
    before = model(repository).waits.expected("offer")
    add_calls(repository, background, 30, seconds=6.0)
    after = model(repository).waits.expected("offer")
    # v1 read all 32 calls alike: 30 more 6 s background calls dragged W to the background builds' time (0.61 to 0.12
    # minutes on v1); here they move nothing but the last bit of a mean of equal logs.
    assert before == pytest.approx(after, rel=1e-12)
    presses = [value for value in durations(repository) if value == 1.0]
    assert before == pytest.approx(PM.wait_estimate(presses, [0.1]).minutes, rel=1e-12)
    assert before == pytest.approx(math.sqrt(0.1), rel=1e-12)
    estimate = model(repository).waits.estimates["grammar"]
    assert (estimate.pressed_n, estimate.pressed_minutes, estimate.prior_n) == (len(presses), 1.0, 31)


def test_background_durations_never_move_the_pressed_measurement(tmp_path):
    _paths, repository, _vault, press, background = ledger(tmp_path)
    time_calls(repository, press, 60.0)
    found = []
    for seconds in (3.0, 600.0):
        time_calls(repository, background, seconds)
        estimate = model(repository).waits.estimates["sketch"]
        found.append((estimate.pressed_n, estimate.pressed_minutes))
    assert found[0] == found[1] and found[0][1] == 1.0


# ---------------------------------------------------------------------------
# The blocked minutes: foreground only (fail-first on prefetch_decision_v1)
# ---------------------------------------------------------------------------

def test_background_calls_never_move_the_blocked_minutes(tmp_path):
    _paths, repository, _vault, press, background = ledger(tmp_path)
    time_calls(repository, press, 60.0)
    time_calls(repository, background, 6.0)
    add_pause(repository)
    inside = PAUSE_AT + timedelta(minutes=30)
    add_calls(repository, press, 1, status="failed", at=inside)
    add_calls(repository, background, 2, status="failed", at=inside + timedelta(minutes=5))
    add_calls(repository, "prefetch_judge:abc", 2, status="failed", purpose=JUDGE,
              at=inside + timedelta(minutes=10))
    before = model(repository)
    add_calls(repository, background, 5, status="failed", at=inside + timedelta(minutes=20))
    add_calls(repository, background, 4, seconds=600.0, at=inside - timedelta(hours=3))
    add_calls(repository, "prefetch_judge:abc", 3, seconds=300.0, purpose=JUDGE,
              at=inside - timedelta(hours=4))
    after = model(repository)
    # One foreground failure in one pause, times the foreground calls' latency (the press's 1 minute).
    assert before.blocked_minutes == after.blocked_minutes == 1.0
    assert before.blocked_basis == {"refused": 1, "background_left_out": 4, "latency_calls": 1, "pauses": 1}
    assert after.blocked_basis == {"refused": 1, "background_left_out": 9, "latency_calls": 1, "pauses": 1}


# ---------------------------------------------------------------------------
# The prior and the posterior (pure)
# ---------------------------------------------------------------------------

def test_the_wait_estimate_is_the_presses_shrunk_toward_the_other_calls_by_one_measurement():
    pressed, others = [1.0, 2.0], [0.25, 0.5, 0.25]
    found = PM.wait_estimate(pressed, others)
    logs_p, logs_o = np.log(pressed), np.log(others)
    centre = (1.0 * logs_o.mean() + 2 * logs_p.mean()) / 3.0
    variance = (3 * logs_o.var() + 2 * logs_p.var()) / 5.0
    assert found.minutes == pytest.approx(math.exp(centre + variance / 2.0), rel=1e-12)
    assert (found.pressed_n, found.prior_n, found.prior_strength) == (2, 3, 1.0)
    assert found.pressed_minutes == PM.lognormal_mean(pressed) and found.prior_minutes == PM.lognormal_mean(others)
    assert PM.WAIT_PRIOR_STRENGTH == 1.0


def test_the_limits_are_v1s_w_with_no_press_and_the_presses_own_with_no_other_call():
    others, pressed = [0.4, 0.5, 0.61], [0.7, 0.66]
    assert PM.wait_estimate([], others).minutes == PM.lognormal_mean(others)  # bit for bit
    assert PM.wait_estimate(pressed, []).minutes == PM.lognormal_mean(pressed)
    assert PM.wait_estimate([1.0], []).minutes == 1.0
    nothing = PM.wait_estimate([], [0.0, 0.0])
    assert nothing.minutes is None and (nothing.pressed_n, nothing.prior_n) == (0, 0)


def test_the_presses_weight_is_learned_as_n_over_n_plus_one_and_a_shift_never_widens_the_spread():
    # Constant groups: the spread is 0 and the log-centre moves n/(n+1) of the way to the presses'.
    for n in (1, 2, 9, 99):
        found = PM.wait_estimate([1.0] * n, [0.1] * 7)
        assert math.log(found.minutes) == pytest.approx((math.log(0.1) + n * math.log(1.0)) / (n + 1), abs=1e-12)
    # However far the two groups sit apart, the spread is each group's about its own mean.
    near, far = PM.wait_estimate([1.0, 2.0], [1.0, 2.0]), PM.wait_estimate([1.0, 2.0], [100.0, 200.0])
    assert math.log(far.minutes) - math.log(near.minutes) == pytest.approx(math.log(100.0) / 3.0, abs=1e-12)
    # The number of other calls never changes the prior's weight.
    assert PM.wait_estimate([1.0], [0.1]).minutes == PM.wait_estimate([1.0], [0.1] * 50).minutes


# ---------------------------------------------------------------------------
# The switch: prefetch_decision_v1 exactly
# ---------------------------------------------------------------------------

def _v1_digest(found: PM.Model) -> str:
    """prefetch_decision_v1's digest as the predecessor built it (its payload, key for key)."""

    payload = {
        "version": "prefetch_decision_v1",
        "opening": {"sources": list(found.opening.sources),
                    "weights": [round(float(w), 10) for w in found.opening.weights],
                    "means": [[round(float(v), 10) for v in mean] for mean in found.opening.means],
                    "observations": found.opening.observations},
        "pause": {"mean": [round(float(v), 10) for v in found.pause.mean], "days": found.pause.days,
                  "load": [found.pause.load_mean, found.pause.load_sd]},
        "waits": {"minutes_by_tier": {tier: round(value, 3) for tier, value in sorted(found.waits.minutes.items())},
                  "measured_builds_by_tier": dict(sorted(found.waits.counts.items())),
                  "pressed_tier_mix": {tier: round(value, 4) for tier, value in sorted(found.waits.pressed_mix.items())},
                  "tier_mix_by_trigger": {kind: {tier: round(value, 4) for tier, value in sorted(mix.items())}
                                          for kind, mix in sorted(found.waits.mix_by_kind.items())}},
        "blocked_minutes": found.blocked_minutes, "load_today": found.load_today,
        "incremental": [found.incremental.author_calls, found.incremental.rich_calls],
        "per_request": found.pause.per_request,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def test_switched_off_w_the_blocked_minutes_and_the_digest_are_v1s_exactly(tmp_path):
    _paths, repository, _vault, press, background = ledger(tmp_path)
    time_calls(repository, press, 60.0)
    time_calls(repository, background, 6.0)
    add_calls(repository, background, 3, seconds=20.0)
    add_pause(repository)
    inside = PAUSE_AT + timedelta(minutes=30)
    add_calls(repository, press, 1, status="failed", at=inside)
    add_calls(repository, background, 2, status="failed", at=inside)
    add_calls(repository, "prefetch_judge:abc", 1, status="failed", purpose=JUDGE, at=inside)
    off = model(repository, pressed_waits=False)
    # v1's W: every completed author call alike; v1's blocked minutes: every failure in the window times every
    # completed plan call's mean latency.
    every = durations(repository)
    assert off.waits.minutes == {"grammar": PM.lognormal_mean(every), "sketch": PM.lognormal_mean(every)}
    assert off.waits.counts == {"grammar": len(every), "sketch": len(every)}
    completed = durations(repository, purpose=None)
    failed = len(durations(repository, status="failed", purpose=None))
    assert off.blocked_minutes == failed * (sum(completed) / len(completed)) / 1
    assert off.version == PM.MODEL_VERSION_V1 == "prefetch_decision_v1" and off.blocked_basis is None
    assert off.waits.estimates == {} and "estimate_by_tier" not in off.waits.summary()
    assert off.digest() == _v1_digest(off)
    on = model(repository)
    assert on.version == PM.MODEL_VERSION == "prefetch_decision_v2" and on.digest() != off.digest()


def test_with_no_measured_pause_the_decision_its_propensity_and_the_order_are_the_same(tmp_path):
    _paths, repository, _vault, press, background = ledger(tmp_path)
    time_calls(repository, press, 60.0)
    time_calls(repository, background, 6.0)
    add_calls(repository, background, 9, seconds=8.0)
    off, on = model(repository, pressed_waits=False), model(repository)
    assert off.blocked_minutes is None and on.blocked_minutes is None  # cost 0 either way
    assert on.waits.expected("offer") != off.waits.expected("offer")
    candidates = [PM.Candidate(kind, None, p, 1.0) for kind in PM.TRIGGER_KINDS for p in (None, 0.05, 0.5, 0.95)]
    for seed in range(5):
        first, second = np.random.default_rng(seed), np.random.default_rng(seed)
        a = [off.decide(item, first) for item in candidates]
        b = [on.decide(item, second) for item in candidates]
        assert [(d.build, d.propensity, d.p_open, d.rule) for d in a] == [(d.build, d.propensity, d.p_open, d.rule)
                                                                         for d in b]
        order = sorted(range(len(a)), key=lambda index: -(a[index].sampled_eu or float("-inf")))
        assert order == sorted(range(len(b)), key=lambda index: -(b[index].sampled_eu or float("-inf")))


# ---------------------------------------------------------------------------
# The pass: its rows' model version and its records' basis
# ---------------------------------------------------------------------------

def _decide(vault: Any, repository: Any) -> list[dict[str, Any]]:
    env = PF.PrefetchEnv(vault=vault, repository=repository, author_client=AuthorFake(),
                         rng=np.random.default_rng(0), pause_reader=lambda: None, foreground_wait_seconds=0.0)
    result = PF.PassResult("ok", "offer")
    PF.decide_and_log(env, [PF.Candidate("offer", "tutor:q", EXTRACTION, ["p5"], p_open_content=0.5)], on_mains=True,
                      plan_wait=None, result=result)
    return result.decisions


def _prebuild_records(repository: Any) -> list[provenance.DecisionRecord]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return provenance.read_kind(connection, FR.KIND_PREBUILD)


def test_at_the_tag_the_rows_say_v2_and_the_records_carry_ws_basis(tmp_path):
    paths, repository, _vault, press, background = ledger(tmp_path)
    set_algorithm_version(paths, FIGURE_WAIT_ALGORITHM_VERSION)  # the test vaults are older by default
    vault = load_vault(paths.root)
    time_calls(repository, press, 60.0)
    time_calls(repository, background, 6.0)
    assert PL.pressed_waits_on(vault)
    (row,) = _decide(vault, repository)
    assert row["model_version"] == PM.MODEL_VERSION and row["w_minutes"] is not None
    (record,) = _prebuild_records(repository)
    basis = record.facts["wait_estimate_by_tier"]
    assert set(basis) == {"grammar", "sketch"}
    assert basis["grammar"] == {"pressed_n": 1, "pressed_min": 1.0, "prior_n": 1, "prior_min": 0.1,
                                "prior_strength": 1.0, "posterior_min": round(math.sqrt(0.1), 4)}
    assert record.facts["blocked_basis"] == {"background_left_out": 0, "latency_calls": 0, "pauses": 0, "refused": 0}
    assert record.facts["wait_min"] == pytest.approx(math.sqrt(0.1))
    assert record.versions["model_version"] == PM.MODEL_VERSION and provenance.check_no_prose(record) == []


@pytest.mark.parametrize("how", ["switch_off", "below_the_tag"])
def test_switched_off_or_below_the_tag_the_rows_say_v1_and_the_records_are_as_before(tmp_path, how):
    if how == "switch_off":
        paths, repository, _vault, press, background = ledger(tmp_path, pressed_waits=False)
        set_algorithm_version(paths, FIGURE_WAIT_ALGORITHM_VERSION)
    else:
        paths, repository, _vault, press, background = ledger(tmp_path)
        set_algorithm_version(paths, SLIP_GAP_ALGORITHM_VERSION)
    vault = load_vault(paths.root)
    time_calls(repository, press, 60.0)
    time_calls(repository, background, 6.0)
    assert not PL.pressed_waits_on(vault)
    (row,) = _decide(vault, repository)
    assert row["model_version"] == PM.MODEL_VERSION_V1
    (record,) = _prebuild_records(repository)
    assert "wait_estimate_by_tier" not in record.facts and "blocked_basis" not in record.facts
    assert record.facts["wait_min"] == PM.lognormal_mean([1.0, 0.1])


def test_the_reader_report_reads_the_ledger_as_the_decisions_do(tmp_path):
    _paths, repository, _vault, press, background = ledger(tmp_path)
    time_calls(repository, press, 60.0)
    time_calls(repository, background, 6.0)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        on = PL.report_block(connection, plan_providers={PROVIDER}, now=NOW)
        off = PL.report_block(connection, plan_providers={PROVIDER}, now=NOW, pressed_waits=False)
    assert on["posterior"]["model_version"] == PM.MODEL_VERSION and "estimate_by_tier" in on["measured_wait"]
    assert on["blocked_basis"]["pauses"] == 0
    assert off["posterior"]["model_version"] == PM.MODEL_VERSION_V1 and "blocked_basis" not in off
    assert "estimate_by_tier" not in off["measured_wait"]
