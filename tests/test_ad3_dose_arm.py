"""Adaptive difficulty AD3: the randomized dose arm and the dose-and-burden lines (spec §5.12, §10.4).

G-AD3-12 (fail-first: no dose arm existed) and G-AD3-14. The Reader's mapping is
AD1's fixed map (``tests.test_ad1_reading_opportunities.FakeMap``); fakes only.
"""

from __future__ import annotations

import json
from collections import Counter
from contextlib import closing
from typing import Any

import numpy as np
import pytest

from learnloop.adaptive_difficulty import dose as D
from learnloop.adaptive_difficulty import dose_report as DR
from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty import selection as S
from learnloop.adaptive_difficulty.state import View
from learnloop.db.connection import connect
from learnloop.db.stores import ad_serving
from learnloop.scheduling import randomization_layer as RL
from learnloop.vault.loader import load_vault

from tests.ad_fakes import rows
from tests.test_ad1_reading_opportunities import FakeMap, _question, _setup, at

QUIET = "[adaptive_difficulty]\noutside_forecasters = []\nfeature_audit = false\n"


def _arm(tmp_path, *, config: str = "") -> tuple[Any, Any, Any]:
    paths, _vault, repo = _setup(tmp_path, config=QUIET + config)
    return paths, load_vault(paths.root), repo


def _boundary(visit: str = "visit1", section: str = "u1", **flags: Any) -> D.Boundary:
    return D.Boundary(visit_id=visit, extraction_id="ext1", section_id=section, **flags)


def _draws(paths) -> list[dict[str, Any]]:
    with closing(connect(paths.sqlite_path)) as connection:
        return [row for row in ad_serving.dose_rows(connection) if row["row_kind"] == "draw"]


def _mapping(**changes: Any) -> FakeMap:
    mapping = FakeMap()
    # A second worked example cited by the LO and not in section u1 (the extra example's source).
    mapping.examples["ext1"] = {"we1", "we2"}
    mapping.spans[("ext1", "we2")] = ["lo_svd_definition"]
    for key, value in changes.items():
        setattr(mapping, key, value)
    return mapping


# -- G-AD3-12 -----------------------------------------------------------------------------------


def test_dose_offer_propensities_exact(tmp_path):
    """Each draw's ``π`` recomputes exactly from its row (base, floor, feasible set); every feasible
    variant has ``π >= dose_floor`` and they sum to 1; the seed reproduces the draw; the row is
    written before the offer is returned; the layer registers ``reading_dose``. Fails before AD3:
    there was no dose arm."""

    paths, vault, repo = _arm(tmp_path)
    _question(repo, "recall", 1, answer=False)
    decision = D.decide(vault, repo, _boundary(), clock=at(2), reading_map=_mapping())
    (row,) = _draws(paths)
    assert decision.draw_id == row["id"] and decision.eligible
    assert row["feasible"] == ["none", "extra_worked_example", "extra_question"] and row["infeasible"] == {}
    pi = RL.reading_dose_propensities(row["feasible"], {"none": 1.0}, row["floor"])
    assert row["propensities"] == {v: round(p, 12) for v, p in sorted(pi.items())}
    assert all(p >= row["floor"] - 1e-12 for p in row["propensities"].values())
    assert sum(row["propensities"].values()) == pytest.approx(1.0, abs=1e-12)
    assert row["propensities"]["none"] == pytest.approx(0.8)
    assert row["seed"] == S.seed_for(D.DOSE_VERSION, "visit1:u1")
    assert RL.draw_from(pi, S.uniform(row["seed"])) == row["chosen_variant"] == decision.variant
    assert RL.READING_DOSE in RL.ADMISSIBLE_DESIGNS
    assert row["detail"]["design"] == RL.READING_DOSE and row["base_version"] == D.BASE_VERSION
    # The same boundary again returns the logged draw; nothing is redrawn.
    again = D.decide(vault, repo, _boundary(), clock=at(3), reading_map=_mapping())
    assert again.draw_id == row["id"] and len(_draws(paths)) == 1


def test_draw_frequencies_match_propensities():
    """Over 10⁵ seeds, each variant's frequency is within 0.005 of its ``π``."""

    pi = RL.reading_dose_propensities(("none", "extra_worked_example", "extra_question"), {"none": 1.0}, 0.10)
    counts = Counter(RL.draw_from(pi, S.uniform(S.seed_for(D.DOSE_VERSION, f"v{k}:s"))) for k in range(100_000))
    for variant, p in pi.items():
        assert abs(counts[variant] / 100_000 - p) < 0.005


def test_infeasible_variant_has_no_mass_and_its_reason_is_logged(tmp_path):
    paths, vault, repo = _arm(tmp_path)
    D.decide(vault, repo, _boundary(), clock=at(2), reading_map=FakeMap())
    (row,) = _draws(paths)
    assert row["feasible"] == ["none"]
    assert row["infeasible"] == {"extra_worked_example": "no_unstudied_example", "extra_question": "no_producer_result"}
    assert row["propensities"] == {"none": 1.0} and row["chosen_variant"] == "none"


def test_uptake_appends_rows_and_never_changes_the_draw(tmp_path):
    paths, vault, repo = _arm(tmp_path, config="dose_floor = 0.3\n")
    _question(repo, "recall", 1, answer=False)
    # Find a visit whose draw offers something (the floor 0.3 over two feasible extras).
    for visit in range(40):
        decision = D.decide(vault, repo, _boundary(visit=f"v{visit}", section="u1"), clock=at(2),
                            reading_map=_mapping())
        if decision.variant not in (None, "none"):
            break
    else:  # pragma: no cover
        pytest.fail("no extra offered")
    before = [r for r in _draws(paths) if r["id"] == decision.draw_id][0]
    for event in ("delivered", "taken"):
        D.record_uptake(vault, repo, decision.draw_id, event, clock=at(3))
    after = [r for r in _draws(paths) if r["id"] == decision.draw_id][0]
    assert after == before
    uptake = rows(paths.sqlite_path, "SELECT row_kind, draw_id FROM ad_dose_offers WHERE row_kind != 'draw'")
    assert uptake == [{"row_kind": "delivered", "draw_id": decision.draw_id},
                      {"row_kind": "taken", "draw_id": decision.draw_id}]
    with closing(connect(paths.sqlite_path)) as connection:
        for sql in ("UPDATE ad_dose_offers SET chosen_variant = 'none'", "DELETE FROM ad_dose_offers"):
            with pytest.raises(Exception, match="append-only"):
                connection.execute(sql)
    with pytest.raises(ValueError):
        D.record_uptake(vault, repo, decision.draw_id, "dwelled", clock=at(4))


def test_the_friction_budget_holds(tmp_path):
    """At most one extra offer per section and ``dose_daily_offers`` a day; no draw with the
    budget spent, the cue density off, in skim mode, or on the restored passage."""

    paths, vault, repo = _arm(tmp_path, config="dose_floor = 0.3\ndose_daily_offers = 2\n")
    mapping = _mapping(sections={("ext1", f"u{k}"): ["lo_svd_definition"] for k in range(1, 30)})
    _question(repo, "recall", 1, answer=False)
    offered_sections = set()
    for visit in range(30):
        section = f"u{1 + visit % 3}"
        decision = D.decide(vault, repo, _boundary(visit=f"v{visit}", section=section), clock=at(2 + visit),
                            reading_map=mapping)
        if decision.variant not in (None, "none"):
            assert section not in offered_sections  # one extra per section
            offered_sections.add(section)
    extras = [r for r in _draws(paths) if r["chosen_variant"] not in (None, "none")]
    assert len(extras) <= 2
    for flags, reason in (({"cue_density_off": True}, "density_off"), ({"skim": True}, "skim"),
                          ({"restored_section": True}, "restored_section"),
                          ({"boundary_checks_available": False}, "no_boundary_checks")):
        before = len(_draws(paths))
        decision = D.decide(vault, repo, _boundary(visit="vx", section="u9", **flags), clock=at(40),
                            reading_map=mapping)
        assert not decision.eligible and decision.reason == reason and len(_draws(paths)) == before
    if len(extras) == 2:
        decision = D.decide(vault, repo, _boundary(visit="vy", section="u20"), clock=at(41), reading_map=mapping)
        assert decision.reason == "daily_budget" and not decision.eligible


def test_switch_off_is_todays_reader_exactly(tmp_path):
    """``reading_dose_offers = false``: no draw, no offer, no row (the RPC answers ineligible)."""

    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    paths, vault, repo = _arm(tmp_path, config="reading_dose_offers = false\n")
    decision = D.decide(vault, repo, _boundary(), clock=at(2), reading_map=_mapping())
    assert not decision.eligible and decision.reason == "switch_off" and not _draws(paths)
    ctx = SidecarContext()
    ctx.load(paths.root)
    spec = METHOD_REGISTRY["reader.dose_offer"]
    result = spec.handler(ctx, spec.params_model.model_validate(
        {"extractionId": "ext1", "sectionId": "u1", "visitId": "visit1"}))
    assert result["eligible"] is False and result["offer"] is None
    assert rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM ad_dose_offers")[0]["n"] == 0


def test_a_taken_extra_becomes_a_reading_opportunity_with_the_offer_id(tmp_path):
    """A taken extra question, once answered, is an ordinary in-passage opportunity whose receipt
    names the offer (§5.12 Uptake); a dismissal is never read as low ability (nothing else moves)."""

    from learnloop.adaptive_difficulty.reading import sweep
    from learnloop.reader import reader_quick_check as RQC

    paths, vault, repo = _arm(tmp_path, config="dose_floor = 0.3\n")
    question = _question(repo, "recall", 1, answer=False)
    mapping = _mapping(examples={"ext1": {"we1"}})  # only the question extra is feasible
    for visit in range(40):
        decision = D.decide(vault, repo, _boundary(visit=f"v{visit}"), clock=at(2), reading_map=mapping)
        if decision.variant == "extra_question":
            break
    else:  # pragma: no cover
        pytest.fail("no extra question offered")
    D.record_uptake(vault, repo, decision.draw_id, "taken", clock=at(3))
    RQC.record_inquiry_action(repo, question_id=question, action="answered", response_md="mine", clock=at(4))
    sweep(vault, repo, as_of="2026-10-12T09:05:00Z", sweep_kind="serve", reading_map=mapping, clock=at(5))
    (opportunity,) = rows(paths.sqlite_path, "SELECT * FROM ad_reading_opportunities WHERE source_id = ?", (question,))
    assert opportunity["dose_offer_id"] == decision.draw_id and opportunity["kind"] == "in_passage_question"


# -- G-AD3-14 -----------------------------------------------------------------------------------


def _fitted_view(curves: dict[str, tuple[float, float]], *, sd: float = 0.01, gamma: float = 0.2) -> View:
    """A synthetic fitted subject view: each kind's coefficients known to ``sd``."""

    bank = M.Bank((P.LO_VIEW_POINT,), reading=True, verdict=True)
    for name in bank.names:
        i = bank.index[name]
        bank.S[:, i, :] = 0.0
        bank.S[:, :, i] = 0.0
        bank.S[:, i, i] = 1e-12
    for kind, (c1, c2) in curves.items():
        for m, value in ((1, c1), (2, c2)):
            bank.mu[:, bank.index[f"delta:{kind}:{m}"]] = value
            bank.S[:, bank.index[f"delta:{kind}:{m}"], bank.index[f"delta:{kind}:{m}"]] = sd ** 2
    for m in (1, 2):
        bank.mu[:, bank.index[f"gbar:{m}"]] = 0.0
    bank.mu[:, bank.index["gamma"]] = gamma
    bank.S[:, bank.index["gamma"], bank.index["gamma"]] = (sd / 10) ** 2
    return View(bank, subject_view=True, reading=True)


def _visits(minutes: dict[str, float], n: int = 300, seed: int = 3) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        counts = {kind: int(rng.integers(0, 4)) for kind in P.READING_KINDS}
        out.append({"active_minutes": 1.0 + sum(minutes[k] * counts[k] for k in counts), "counts": counts})
    return out


def _expected_n_star(curve: tuple[float, float], minutes: float, reference: float) -> int:
    best = 0
    for n in range(1, DR.MAX_DOSE + 1):
        gain = float(DR.points_gain(DR.curve(curve[0], curve[1], n) - DR.curve(curve[0], curve[1], n - 1)))
        if gain / minutes >= reference:
            best = n
    return best


def test_dose_report_recommendation_follows_fitted_curves():
    """On synthetic fitted states with known curves and minutes, the useful dose is where the
    curve's marginal gain per minute (posterior median) crosses the practice reference; moving a
    curve moves its recommendation the same way; the lines are fixed templates."""

    minutes = {"reading": 1.0, "reader_tutor_exchange": 0.5, "worked_example": 1.0, "in_passage_question": 2.0}
    curves = {"reading": (0.6, 0.6), "reader_tutor_exchange": (0.9, 0.0), "worked_example": (0.0, 1.2),
              "in_passage_question": (0.0, 0.0)}
    view = _fitted_view(curves)
    report = DR.analyse(view, visits=_visits(minutes), answer_minutes=3.0, median_doses={k: 1.0 for k in curves})
    reference = float(DR.points_gain(0.2)) / 3.0
    for kind, curve in curves.items():
        n_star = report["kinds"][kind]["useful_dose"]
        assert n_star["n_star"] == _expected_n_star(curve, minutes[kind], reference), kind
        assert report["kinds"][kind]["minutes_per_event"] == pytest.approx(minutes[kind], abs=0.05)
    assert report["kinds"]["worked_example"]["useful_dose"]["n_star"] > 0
    assert report["kinds"]["in_passage_question"]["useful_dose"]["n_star"] == 0
    # A stronger curve moves its useful dose up (and its line with it).
    stronger = DR.analyse(_fitted_view({**curves, "worked_example": (0.0, 2.4)}), visits=_visits(minutes),
                          answer_minutes=3.0, median_doses={k: 1.0 for k in curves})
    assert stronger["kinds"]["worked_example"]["useful_dose"]["n_star"] > \
        report["kinds"]["worked_example"]["useful_dose"]["n_star"]
    assert stronger["lines"][2] != report["lines"][2]
    line = report["lines"][2]
    assert line.startswith("Worked examples: about ") and line.endswith(f"({DR.OBSERVATIONAL}).")


def test_cant_tell_exactly_when_the_interval_is_wide_or_minutes_unknown():
    minutes = {"reading": 1.0, "reader_tutor_exchange": 0.5, "worked_example": 1.0, "in_passage_question": 2.0}
    curves = {kind: (0.3, 0.3) for kind in P.READING_KINDS}
    sure = DR.analyse(_fitted_view(curves, sd=0.001), visits=_visits(minutes), answer_minutes=3.0,
                      median_doses={})
    for kind in P.READING_KINDS:
        entry = sure["kinds"][kind]["useful_dose"]
        assert entry["cant_tell"] == (entry["interval"][1] - entry["interval"][0] > 2)
    wide = DR.analyse(_fitted_view(curves, sd=0.6), visits=_visits(minutes), answer_minutes=3.0, median_doses={})
    assert any(wide["kinds"][k]["useful_dose"]["cant_tell"] for k in P.READING_KINDS)
    for kind in P.READING_KINDS:
        entry = wide["kinds"][kind]["useful_dose"]
        assert entry["cant_tell"] == (entry["interval"][1] - entry["interval"][0] > 2)
        if entry["cant_tell"]:
            assert f"{DR.KIND_NAMES[kind]}: can't tell yet." in wide["lines"]
    # Minutes unknown (no visit counts the kind): "can't tell yet".
    no_minutes = DR.analyse(_fitted_view(curves), visits=[], answer_minutes=3.0, median_doses={})
    assert all(no_minutes["kinds"][k]["useful_dose"]["cant_tell"] for k in P.READING_KINDS)
    assert all(line.endswith("can't tell yet.") for line in no_minutes["lines"][:4])


def test_helps_when_lines_only_when_the_moderated_contrast_excludes_zero():
    rng = np.random.default_rng(5)
    records = []
    for _ in range(600):
        p = float(rng.uniform(0.2, 0.95))
        tutor = float(rng.random() < 0.5)
        lift = 0.35 if (tutor and p < 0.5) else 0.0
        y = float(rng.random() < min(p + lift, 0.99))
        records.append({"y": y, "p": p, "doses": {"reader_tutor_exchange": tutor,
                                                  "reader_tutor_exchange:help_me_reason": tutor}})
    contrasts = DR.moderated_contrasts(records)
    lines = DR.helps_when_lines(contrasts, {})
    assert "Tutor exchanges while reading helped when your predicted chance on the topic was below 50% " \
           f"({DR.OBSERVATIONAL})." in lines
    assert not any("above 80%" in line for line in lines)
    assert all(not line.startswith("Worked examples") for line in lines)  # no contrast, no line
    # With no effect anywhere, no line at all.
    flat = [{**r, "y": float(rng.random() < r["p"])} for r in records]
    assert DR.helps_when_lines(DR.moderated_contrasts(flat), {}) == [] or all(
        "below" not in line for line in DR.helps_when_lines(DR.moderated_contrasts(flat), {}))


def test_tested_label_only_when_the_offers_agree_in_sign_and_exclude_zero():
    assert DR.label(0.1, {"sequence": {"n": 50, "lower": 0.02, "upper": 0.3}}) == DR.TESTED
    assert DR.label(-0.1, {"sequence": {"n": 50, "lower": 0.02, "upper": 0.3}}) == DR.OBSERVATIONAL
    assert DR.label(0.1, {"sequence": {"n": 50, "lower": -0.02, "upper": 0.3}}) == DR.OBSERVATIONAL
    assert DR.label(0.1, None) == DR.OBSERVATIONAL


def test_recommendations_never_act(tmp_path, monkeypatch):
    """No line changes a switch, the dose arm's base policy or any offer; no model is called."""

    import learnloop.ai.routing as routing

    monkeypatch.setattr(routing, "ready_client_for_task", lambda *a, **k: pytest.fail("a model was asked"))
    paths, vault, repo = _arm(tmp_path)
    toml_before = (paths.root / "learnloop.toml").read_text(encoding="utf-8")
    DR.analyse(_fitted_view({k: (0.3, 0.3) for k in P.READING_KINDS}), visits=_visits(
        {k: 1.0 for k in P.READING_KINDS}), answer_minutes=3.0, median_doses={})
    assert (paths.root / "learnloop.toml").read_text(encoding="utf-8") == toml_before
    assert D.BASE_VERSION == "reading_dose_base_none_v1"
    assert not _draws(paths)
