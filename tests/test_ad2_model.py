"""Adaptive difficulty AD2: the model, offline (spec_adaptive_difficulty_v1 §14 AD2, "The model").

G-AD2-1..6, 9..13, 15..17 (the simulation gates G-AD2-7, 8, 14 and 18 are in
``tests/test_ad23_sim.py``). Each failed before AD2 for the reason the spec
names: no feature-based demand, no AD state, no replay of frozen inputs, no
joint factor. Fakes only; no model is called.
"""

from __future__ import annotations

import json
import math
from contextlib import closing
from dataclasses import replace

import numpy as np
import pytest

from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import outcomes as O
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty.state import ItemSpec, View
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import ITEMS, LO, ad23_vault, answer, env_for, rows

SPEC = ItemSpec("i", "lo", "s", "retrieval", {"f": 1.0},
                features={"scaffolding": "worked", "response": "recognize", "tools": ["open_book"]})


def _fixed_state(variance: float, demand: float) -> tuple[M.Bank, View]:
    """One cell with ability mean 1.0 and the given variance; the demand known (β, α, γ, ζ near-fixed)."""

    bank = M.Bank([P.LO_VIEW_POINT])
    view = View(bank, subject_view=False)
    view.ensure(SPEC, 0.0)
    for name in bank.names:
        i = bank.index[name]
        bank.S[:, i, :] = 0.0
        bank.S[:, :, i] = 0.0
        bank.S[:, i, i] = 1e-10
    i = bank.index["G:s"]
    bank.mu[:, i] = 1.0
    bank.S[:, i, i] = variance
    coding = P.feature_coding(SPEC.features)
    for name in coding:
        bank.mu[:, bank.index[name]] = demand / len(coding)
    for name in ("F:f", "E:f:retrieval"):
        bank.mu[:, bank.index[name]] = 0.0
    return bank, view


def _theta(bank: M.Bank) -> float:
    return float(sum(bank.mu[0, bank.index[n]] for n in ("G:s", "F:f", "E:f:retrieval")))


def _move(variance: float, demand: float, category: int) -> float:
    bank, view = _fixed_state(variance, demand)
    before = _theta(bank)
    view.observe(SPEC, category, 0.0, learn=False)
    return _theta(bank) - before


# -- G-AD2-1 ------------------------------------------------------------------------------------


def test_trivial_success_barely_moves_ability():
    """The core question (pre-registered with amendment A1): with the cell's posterior mean at
    1.0, an unassisted success on an item whose features put its demand at -3.0 moves the mean
    by < 0.02, a success at demand ≈ 1.0 moves it by >= 0.2, and a failure on the trivial item
    moves it far more than the trivial success (>= 0.15 and 8x at the usable sd 0.74; >= 0.5 at
    the cold-start variance). Fails before AD2: no feature-based demand exists (the canonical
    path is difficulty-blind, G3)."""

    usable = 0.74 ** 2
    trivial = _move(usable, -3.0, 2)
    assert 0.0 < trivial < 0.02
    assert _move(usable, 1.0, 2) >= 0.2
    failure = _move(usable, -3.0, 0)
    assert failure <= -0.15 and abs(failure) >= 8 * trivial
    assert _move(P.COLD_START_VARIANCE, -3.0, 0) <= -0.5


# -- G-AD2-2 ------------------------------------------------------------------------------------


def _audit(paths, item_id: str, values: dict[str, str], at: str) -> None:
    from learnloop.adaptive_difficulty.feature_audit import LEFT_KIND, RIGHT_KIND, TASK, VERSION, item_revision
    from learnloop.db.stores.judgments import append_judgment

    vault = load_vault(paths.root)
    content_hash, _json = item_revision(vault.practice_items[item_id])
    with closing(connect(paths.sqlite_path)) as connection:
        for dimension, value in values.items():
            append_judgment(connection, task=TASK, left_kind=LEFT_KIND, left_id=content_hash, right_kind=RIGHT_KIND,
                            right_id=dimension, judge="decider", judge_model="fake", prompt_version=VERSION,
                            input_hash="h", verdict=value, score=1.0, created_at=at)
        connection.commit()


def _serve_and_answer(paths, env, clock, *, correct=True, hints=0, first_hint_progress=None):
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    clock.advance(2)
    attempt_id = answer(paths, step["practice_item_id"], correct=correct, presentation_id=step["presentation_id"],
                        hints=hints, clock=clock, first_hint_progress=first_hint_progress)
    clock.advance(1)
    return step, attempt_id


def _events(paths, settings=RP.ReplaySettings(), *, fallback: str | None = None):
    vault = load_vault(paths.root)
    if fallback is not None:
        vault.config.adaptive_difficulty.history_fallback = fallback
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return RP.load_events(connection, vault, Repository(paths.sqlite_path), settings=settings)


def test_overclaimed_features_do_not_lower_demand_estimate(tmp_path):
    """Audited features override stamped ones in the likelihood: an item stamped hard but audited
    easy enters the update at its audited (easier) features. Fails before AD2: no replay reads the
    frozen, audited tuple."""

    hard = {"complexity": 3, "transfer": "far", "scaffolding": "none", "span": "multi_step",
            "response": "long_constructed", "tools": ["closed_book"]}
    items = ("pi_h1",)
    paths = ad23_vault(tmp_path, items=items, features={"pi_h1": hard})
    env, clock = env_for(paths, items=items)
    _audit(paths, "pi_h1", {"complexity": "0", "transfer": "same_context", "scaffolding": "cue", "span": "atomic",
                            "response": "short_constructed"}, "2026-10-01T00:00:00Z")
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    _serve_and_answer(paths, env, clock)
    event = next(e for e in _events(paths).attempts if e.eligible)
    assert event.input_status == "frozen"
    assert event.spec.features["complexity"] == 0 and event.spec.features["transfer"] == "same_context"
    assert P.prior_demand(event.spec.features) < P.prior_demand(hard)


# -- G-AD2-3 ------------------------------------------------------------------------------------


def _flow(tmp_path, n=4, items=("pi_a1", "pi_a2", "pi_a3", "pi_a4", "pi_a5")):
    paths = ad23_vault(tmp_path, items=items)
    env, clock = env_for(paths, items=items)
    build_plan(env, kind="normal", budget=30.0, remembered=30, minutes_source="chip")
    for index in range(n):
        _serve_and_answer(paths, env, clock, correct=index % 2 == 0)
    return paths, env, clock


def test_rebuild_byte_identical(tmp_path):
    """Two rebuilds of AD's DERIVED tables are byte-identical (§11.3). Fails before AD2: no tables."""

    paths, _env, _clock = _flow(tmp_path)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    RP.rebuild(vault, repository)
    first = (rows(paths.sqlite_path, "SELECT * FROM ad_state ORDER BY view, part"),
             rows(paths.sqlite_path, "SELECT * FROM ad_attempt_trace ORDER BY attempt_id, view"))
    RP.clear_cache()
    RP.rebuild(vault, repository)
    second = (rows(paths.sqlite_path, "SELECT * FROM ad_state ORDER BY view, part"),
              rows(paths.sqlite_path, "SELECT * FROM ad_attempt_trace ORDER BY attempt_id, view"))
    assert first == second and first[0] and first[1]


def test_zero_model_calls(tmp_path, monkeypatch):
    """The whole-vault rebuild (AD's replayers included) builds no model client (A1)."""

    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths, _env, _clock = _flow(tmp_path, n=2)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("a model client was constructed during replay")

    import learnloop.ai.routing as routing
    import learnloop.practice_index.paid as paid

    monkeypatch.setattr(routing, "ready_client_for_task", forbidden)
    monkeypatch.setattr(paid, "resolve_client", forbidden)
    result = rebuild_all_derived_state(load_vault(paths.root), Repository(paths.sqlite_path))
    names = {r.name for r in result.replayers}
    assert {"adaptive_difficulty", "item_forecast_scores"} <= names
    assert rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM ad_state")[0]["n"] > 0


# -- G-AD2-4 ------------------------------------------------------------------------------------


EVIDENCE_TABLES = {
    # Attempt ids are fresh ULIDs per vault: the evidence is compared by its content.
    "grading_evidence": "criterion_id, points_awarded, superseded_at",
    "learning_object_mastery": "learning_object_id, logit_mean, logit_variance, evidence_count",
    "facet_recall_state": "*",
    "practice_item_state": "practice_item_id, stability, difficulty, due_at, last_attempt_at",
    "facet_capability_evidence": "*",
}


def _evidence(paths):
    out = {}
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        for table, columns in EVIDENCE_TABLES.items():
            data = connection.execute(f"SELECT {columns} FROM {table}").fetchall()
            out[table] = sorted(tuple(row) for row in data)
    return out


def test_ad_never_writes_evidence(tmp_path):
    """Evidence, mastery, facet recall, FSRS and the capability ledger are byte-identical with AD on
    vs off on the same answers, and AD's own rebuild changes none of them; an import-linter contract
    keeps the AD package away from the evidence writers (A2, §11.3)."""

    import tomllib
    from pathlib import Path

    contracts = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text())["tool"][
        "importlinter"]["contracts"]
    guard = next(c for c in contracts if c["id"] == "adaptive-difficulty-never-writes-evidence")
    assert guard["source_modules"] == ["learnloop.adaptive_difficulty"]
    assert {"learnloop.attempts", "learnloop.substrate", "learnloop.goals"} <= set(guard["forbidden_modules"])

    on, _e, _c = _flow(tmp_path / "on")
    off = ad23_vault(tmp_path / "off", items=("pi_a1", "pi_a2", "pi_a3", "pi_a4", "pi_a5"),
                     config="enabled = false\n")
    env, clock = env_for(off, items=("pi_a1", "pi_a2", "pi_a3", "pi_a4", "pi_a5"))
    build_plan(env, kind="normal", budget=30.0, remembered=30, minutes_source="chip")
    for index in range(4):
        _serve_and_answer(off, env, clock, correct=index % 2 == 0)
    assert rows(on.sqlite_path, "SELECT COUNT(*) AS n FROM ad_selections")[0]["n"] > 0
    assert rows(off.sqlite_path, "SELECT COUNT(*) AS n FROM ad_selections")[0]["n"] == 0
    before = _evidence(on)
    assert before == _evidence(off)
    vault = load_vault(on.root)
    RP.rebuild(vault, Repository(on.sqlite_path))
    from learnloop.adaptive_difficulty.scoring import rebuild as rebuild_scores

    rebuild_scores(vault, Repository(on.sqlite_path))
    assert _evidence(on) == before


# -- G-AD2-5 ------------------------------------------------------------------------------------


def test_self_report_and_held_grades_excluded(tmp_path):
    """A ``self_report`` row never enters (D8) and a grade held for review never updates."""

    paths, _env, _clock = _flow(tmp_path, n=2)
    events = _events(paths)
    target = next(e for e in events.attempts if e.eligible)
    with closing(connect(paths.sqlite_path)) as connection:
        attempt = dict(zip([d[0] for d in connection.execute("SELECT * FROM practice_attempts LIMIT 1").description],
                           connection.execute("SELECT * FROM practice_attempts WHERE id = ?",
                                              (target.attempt_id,)).fetchone()))
        connection.execute("UPDATE practice_attempts SET attempt_type = 'self_report' WHERE id = ?",
                           (target.attempt_id,))
        connection.commit()
    assert all(e.attempt_id != target.attempt_id for e in _events(paths).attempts)
    assert attempt["attempt_type"] != "self_report"


def test_held_grade_excluded(tmp_path, monkeypatch):
    paths, _env, _clock = _flow(tmp_path, n=2)
    target = next(e for e in _events(paths).attempts if e.eligible)
    import learnloop.held_grades as held

    monkeypatch.setattr(held, "held_for_review_attempts", lambda connection, ids=None: frozenset({target.attempt_id}))
    event = next(e for e in _events(paths).attempts if e.attempt_id == target.attempt_id)
    assert not event.eligible and event.reason == "held_for_review"


def test_repeat_surface_attempts_excluded(tmp_path):
    """Only the first graded attempt on a surface group updates the state (D10)."""

    paths, env, clock = _flow(tmp_path, n=1)
    first = next(e for e in _events(paths).attempts if e.eligible)
    clock.advance(60 * 24)
    answer(paths, first.practice_item_id, correct=True, clock=clock)
    repeat = [e for e in _events(paths).attempts if e.practice_item_id == first.practice_item_id]
    assert len(repeat) == 2 and repeat[1].reason == "repeat_surface" and not repeat[1].eligible


# -- G-AD2-6 ------------------------------------------------------------------------------------


def test_rating_subarm_off_is_identical_to_base():
    """With the rating sub-arm off (or no rating tapped) the factor is exactly the base arm's: the
    rating is one factor of one joint likelihood, never a free extra vote."""

    base = M.Bank([P.LO_VIEW_POINT])
    with_arm = M.Bank([P.LO_VIEW_POINT], rating=True)
    for bank in (base, with_arm):
        View(bank, subject_view=False).observe(SPEC, 2, 0.0)
    common = [n for n in base.names]
    assert np.array_equal(base.mu[:, [base.index[n] for n in common]],
                          with_arm.mu[:, [with_arm.index[n] for n in common]])
    tapped = M.Bank([P.LO_VIEW_POINT], rating=True)
    View(tapped, subject_view=False).observe(SPEC, 2, 0.0, rating="easy")
    assert not np.array_equal(tapped.mu[:, tapped.index["G:s"]], with_arm.mu[:, with_arm.index["G:s"]])


# -- G-AD2-9 ------------------------------------------------------------------------------------


@pytest.mark.parametrize("m,v,g", [(0.5, 0.8, 0.0), (1.8, 0.3, 0.0), (-0.4, 2.0, 0.0), (1.0, 0.5, 0.76),
                                   (3.0, 0.2, 0.0)])
def test_band_probability_exact(m, v, g):
    """``P_band`` (§5.7) matches 10⁶-draw Monte Carlo within 1e-3, a band edge outside ``F_x``'s
    range included (a guess floor above 0.70 reaches the band only from its lower edge)."""

    exact = float(M.band_probability(np.array([m]), np.array([v]), g, (0.70, 0.80))[0])
    rng = np.random.default_rng(20261018)
    eta = rng.normal(m, math.sqrt(v), 1_000_000)
    success = M.residual_success(eta, g)
    mc = float(np.mean((success >= 0.70) & (success <= 0.80)))
    assert abs(exact - mc) < 1e-3


# -- G-AD2-10 -----------------------------------------------------------------------------------


def _brute(mu_e: float, v_e: float, link: dict[str, float], *, category: int, rating: str, joint: bool) -> tuple[float, float]:
    """Brute-force moments of η_e: a 4001-point grid on η_e and a 2001-point grid on ε."""

    grid = np.linspace(mu_e - 10 * math.sqrt(v_e), mu_e + 10 * math.sqrt(v_e), 4001)
    eps = np.linspace(-10.0, 10.0, 2001)
    w_eps = np.exp(-0.5 * eps ** 2)
    w_eps /= w_eps.sum()
    prior = np.exp(-0.5 * (grid - mu_e) ** 2 / v_e)
    eta = grid[:, None] - P.A * P.TAU0 * eps[None, :]
    l_y = M.category_likelihood(eta, np.zeros(len(grid)), np.full(len(grid), category))
    rho, c1 = math.exp(link["rating:rho_t"]), link["rating:c1"]
    c2 = c1 + math.exp(link["rating:d_t"])
    l_r = M.rating_likelihood(eta, rho, c1, c2, rating)
    if joint:
        likelihood = (w_eps[None, :] * l_y * l_r).sum(1)
    else:
        likelihood = (w_eps[None, :] * l_y).sum(1) * (w_eps[None, :] * l_r).sum(1)
    post = prior * likelihood
    post /= post.sum()
    mean = float((post * grid).sum())
    return mean, float((post * (grid - mean) ** 2).sum())


def test_joint_attempt_factor_integrates_residual_once():
    """With a rating present, the update matches brute-force joint integration over ``ε_i`` within
    1e-6, and differs from the product of separately marginalized factors (one joint factor,
    §5.6 step 4)."""

    bank = M.Bank([P.LO_VIEW_POINT], rating=True)
    view = View(bank, subject_view=False)
    view.ensure(SPEC, 0.0)
    # A posterior state (the cell's sd 1 after some answers). At the cold-start variance the
    # spec's 32-node rule's error in the posterior variance is ~1e-6 itself (review §2, D-quad).
    for name in ("G:s", "F:f", "E:f:retrieval"):
        i = bank.index[name]
        bank.S[:, i, i] = 1.0 / 3.0
    for name in bank.names:
        i = bank.index[name]
        if name.startswith("rating:"):
            bank.S[:, i, :] = 0.0
            bank.S[:, :, i] = 0.0
            bank.S[:, i, i] = 1e-12
    u, _m, _v = view.projection(SPEC)
    mu_e, v_e = (float(x[0]) for x in bank.moments(u))
    link = {name: float(bank.mu[0, bank.index[name]]) for name in ("rating:rho_t", "rating:c1", "rating:d_t")}
    record = bank.update_joint(u, category=2, rating="easy")
    joint = _brute(mu_e, v_e, link, category=2, rating="easy", joint=True)
    separate = _brute(mu_e, v_e, link, category=2, rating="easy", joint=False)
    assert abs(float(record.post_mean[0]) - joint[0]) < 1e-6
    assert abs(float(record.post_var[0]) - joint[1]) < 1e-6
    assert abs(separate[0] - joint[0]) > 1e-3


# -- G-AD2-11 -----------------------------------------------------------------------------------


def test_link_parameters_always_valid():
    """For any ``(c_1, d̃, ρ̃)`` the rating category probabilities lie in [0, 1] and sum to 1."""

    rng = np.random.default_rng(11)
    for _ in range(2000):
        c1, d_t, rho_t = rng.normal(0, 5), rng.normal(0, 3), rng.normal(0, 3)
        eta = rng.normal(0, 6)
        probs = M.rating_probabilities(eta, rho_t, c1, d_t)
        assert all(-1e-12 <= value <= 1.0 + 1e-12 for value in probs.values())
        assert abs(sum(probs.values()) - 1.0) < 1e-12


# -- G-AD2-12 -----------------------------------------------------------------------------------


def _claim(paths, *, source: str, scope_type: str, scope_id: str | None, level: float, at: str) -> None:
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO learner_claims(id, claim_type, scope_type, scope_id, claimed_level, prior_pseudo_count, "
            "source, created_at) VALUES (?, 'self_rating', ?, ?, ?, 2.0, ?, ?)",
            (f"claim_{source}_{at}", scope_type, scope_id, level, source, at))
        connection.commit()


def test_claims_applied_at_created_at_and_request_claims_excluded(tmp_path):
    """A claim never moves an attempt that precedes it, and ``rung_variant_request`` and
    ``learner_report`` claims never enter the state (D8)."""

    paths, _env, clock = _flow(tmp_path, n=2)
    baseline = RP.run(_events(paths))
    first = [r for r in baseline.trace if r["view"] == RP.VIEW_SUBJECT and "prior_mean" in r]
    _claim(paths, source="init_wizard", scope_type="global", scope_id=None, level=0.9, at="2026-10-12T09:04:00Z")
    _claim(paths, source="rung_variant_request", scope_type="learning_object", scope_id=LO, level=0.95,
           at="2026-10-01T00:00:00Z")
    _claim(paths, source="learner_report", scope_type="learning_object", scope_id=LO, level=0.05,
           at="2026-10-01T00:00:00Z")
    after = RP.run(_events(paths))
    second = [r for r in after.trace if r["view"] == RP.VIEW_SUBJECT and "prior_mean" in r]
    # The first attempt precedes the global claim: identical.
    assert first[0]["prior_mean"] == second[0]["prior_mean"]
    # The two request claims alone (before every attempt) change nothing.
    only_requests = tmp_path / "requests"
    paths2, _e2, _c2 = _flow(only_requests, n=2)
    plain = RP.run(_events(paths2)).subject.bank.state_hash()
    _claim(paths2, source="rung_variant_request", scope_type="learning_object", scope_id=LO, level=0.95,
           at="2026-10-01T00:00:00Z")
    _claim(paths2, source="learner_report", scope_type="learning_object", scope_id=LO, level=0.05,
           at="2026-10-01T00:00:00Z")
    assert RP.run(_events(paths2)).subject.bank.state_hash() == plain
    # A global claim before every attempt moves the subject level's mean, never its variance below the prior.
    _claim(paths2, source="init_wizard", scope_type="global", scope_id=None, level=0.9, at="2026-10-01T00:00:00Z")
    events = _events(paths2)
    claimed = RP.run(events)
    assert claimed.subject.bank.state_hash() != plain


# -- G-AD2-13 -----------------------------------------------------------------------------------


def test_warmth_uses_only_pre_serve_exposures(tmp_path):
    """An exposure after the serve never changes ``w_t`` or the receipt's ``p`` (§5.4)."""

    items = ("pi_w1", "pi_w2")
    paths = ad23_vault(tmp_path, items=items)
    env, clock = env_for(paths, items=items)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    _record, step = advance(env, serve=True)
    receipt_before = rows(paths.sqlite_path, "SELECT p FROM forecast_receipts WHERE forecaster = "
                                             "'ad_threshold@subject'")
    clock.advance(1)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, basis, "
            "created_at) VALUES ('rv_after', 'pi_w2', ?, 'tutor_answer', 0.1, 'overlap', ?)",
            (LO, "2026-10-12T09:01:00Z"))
        connection.commit()
    clock.advance(1)
    answer(paths, step["practice_item_id"], correct=True, presentation_id=step["presentation_id"], clock=clock)
    event = next(e for e in _events(paths).attempts if e.eligible)
    assert event.warmth == 0.0
    assert rows(paths.sqlite_path, "SELECT p FROM forecast_receipts WHERE forecaster = 'ad_threshold@subject'") \
        == receipt_before
    # A control: the same exposure before the serve warms the attempt.
    exposures = {LO: [RP.days("2026-10-12T08:59:00Z")]}
    assert RP._warmth(exposures, LO, RP.days(event.served_at), None) > 0.0


# -- G-AD2-15 -----------------------------------------------------------------------------------


def test_unknown_hint_timing_never_read_as_after_work():
    """A success with ordinary hints and no marker, and one with a help-equivalent question and no
    progress marker, are both censored ``{0, 1}``; with ``draft_started`` they are category 1, with
    ``no_draft`` category 0 (§5.3)."""

    hint_unknown = O.AttemptFacts(correctness=1.0, hints_used=1)
    question_unknown = O.AttemptFacts(correctness=1.0, help_questions=(O.HelpQuestion(None, None),))
    assert O.category(hint_unknown) == M.CENSORED and O.category(question_unknown) == M.CENSORED
    assert O.category(replace(hint_unknown, first_hint_progress=O.DRAFT_STARTED)) == 1
    assert O.category(O.AttemptFacts(correctness=1.0, help_questions=(O.HelpQuestion(O.DRAFT_STARTED),))) == 1
    assert O.category(replace(hint_unknown, first_hint_progress=O.NO_DRAFT)) == 0
    assert O.category(O.AttemptFacts(correctness=1.0, help_questions=(O.HelpQuestion(O.NO_DRAFT),))) == 0
    assert O.category(O.AttemptFacts(correctness=1.0, help_questions=(O.HelpQuestion(None, 0.0),))) == 0
    # The binary event is always observed: any help makes it 0.
    assert O.unassisted_success(O.category(hint_unknown)) == 0.0


def test_unknown_hint_timing_through_the_replay(tmp_path):
    items = ("pi_t1",)
    paths = ad23_vault(tmp_path, items=items)
    env, clock = env_for(paths, items=items)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    _serve_and_answer(paths, env, clock, correct=True, hints=1)
    event = next(e for e in _events(paths).attempts if e.eligible)
    assert event.category == M.CENSORED


# -- G-AD2-16 -----------------------------------------------------------------------------------


def test_replay_uses_frozen_inputs_and_explicit_history(tmp_path):
    """Each attempt's factor is built from its ``item_serve_inputs`` row, never the current item; a
    historical attempt resolves ``exact``, else ``reconstructed_current`` under AD's history
    fallback (``adaptive_difficulty.history_fallback``, ``current_content`` by default, owner
    decision 2026-10-19), or ``excluded`` with it set to ``exclude``; an ``excluded`` attempt never
    updates (§7.5). Field's own ``legacy_fallback`` is untouched."""

    import yaml

    paths, _env, clock = _flow(tmp_path, n=1)
    event = next(e for e in _events(paths).attempts if e.eligible)
    frozen_features = dict(event.spec.features)
    path = paths.practice_item_path("linear-algebra", event.practice_item_id)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["task_features"] = {**payload["task_features"], "complexity": 4}
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    again = next(e for e in _events(paths).attempts if e.attempt_id == event.attempt_id)
    assert again.input_status == "frozen" and dict(again.spec.features) == frozen_features
    # A historical attempt (no bound presentation) on another item: excluded under "exclude".
    answer(paths, "pi_a5", correct=True, presentation_id=None, clock=clock)
    historical = next(e for e in _events(paths, fallback="exclude").attempts if e.practice_item_id == "pi_a5")
    assert historical.input_status == "excluded" and not historical.eligible
    events = _events(paths, fallback="exclude")
    with_excluded = RP.run(events).subject.bank.state_hash()
    events.attempts = [e for e in events.attempts if e.practice_item_id != "pi_a5"]
    assert RP.run(events).subject.bank.state_hash() == with_excluded
    # By default (AD's current-content fallback) the same attempt resolves reconstructed_current.
    resolved = next(e for e in _events(paths).attempts if e.practice_item_id == "pi_a5")
    assert resolved.input_status == "reconstructed_current"


# -- G-AD2-17 -----------------------------------------------------------------------------------


def test_pre_exposed_presentation_excluded_from_update_and_scoring(tmp_path):
    """A reveal sum at the auto-prime threshold before ``served_at`` removes the item from ``P_c``,
    sets ``pre_exposed``, and the attempt neither updates nor is scored (§5.3)."""

    from learnloop.adaptive_difficulty.scoring import score_rows

    items = ("pi_p1",)
    paths = ad23_vault(tmp_path, items=items)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, basis, "
            "created_at) VALUES ('rv_pre', 'pi_p1', ?, 'tutor_answer', 0.5, 'overlap', '2026-10-10T08:00:00Z')",
            (LO,))
        connection.commit()
    env, clock = env_for(paths, items=items)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    _record, step = advance(env, serve=True)
    # The reveal is older than the cold retrieval delay: pre-exposure is the only failed check, so
    # the predecessor serves the item with no draw (mode predecessor, π_AD = 1).
    selection = rows(paths.sqlite_path, "SELECT * FROM ad_selections WHERE kind = 'serve'")
    assert selection and selection[0]["mode"] == "predecessor" and selection[0]["propensity"] == 1.0
    assert json.loads(selection[0]["excluded_json"]) == [{"ref": "pi_p1", "failed": ["pre_exposed"]}]
    assert step["kind"] == "item" and step["practice_item_id"] == "pi_p1"
    assert rows(paths.sqlite_path, "SELECT pre_exposed FROM item_serve_inputs")[0]["pre_exposed"] == 1
    clock.advance(2)
    answer(paths, step["practice_item_id"], correct=True, presentation_id=step["presentation_id"], clock=clock)
    event = next(e for e in _events(paths).attempts if e.practice_item_id == "pi_p1")
    assert not event.eligible and event.reason == "pre_exposed"
    vault = load_vault(paths.root)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        scored = [r for r in score_rows(connection, vault, Repository(paths.sqlite_path))
                  if r["plan_presentation_id"] == step["presentation_id"]]
    assert scored and all(r["status"] == "pre_exposed" for r in scored)


def test_surface_group_mirrors_the_projection():
    """``replay.surface_group`` is ``canonical_projection.surface_group_id`` (pinned)."""

    from learnloop.substrate.canonical_projection import surface_group_id

    for path in sorted((__import__("pathlib").Path(__file__).resolve().parents[1] / "fixtures" / "conic-sections"
                        / "subjects").rglob("practice-items/*.yaml"))[:20]:
        from learnloop.vault.models import PracticeItem
        import yaml

        item = PracticeItem.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        assert RP.surface_group(item) == surface_group_id(item)
