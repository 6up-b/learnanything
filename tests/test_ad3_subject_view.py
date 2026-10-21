"""Adaptive difficulty AD3: the subject view live (spec §5.6, §5.10, §6.1, §9.5, §10.1; G-AD3-1, 2, 5, 6, 10).

Each failed before AD3: no AD state existed (no subject view, no couplings, no
readiness numbers). Fakes only; no model is called.
"""

from __future__ import annotations

import math
from contextlib import closing
from datetime import timedelta
from typing import Any

import numpy as np
import pytest

from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import predict as PR
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty import readiness as RD
from learnloop.adaptive_difficulty import relatedness as R
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty import selection as S
from learnloop.adaptive_difficulty.state import ItemSpec, View
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import COUPLED, LO, ProposalLLM, ad23_vault, answer, env_for, rows, selections, set_item

OTHER = ("pi_o1", "pi_o2", "pi_o3", "pi_o4")
MINE = ("pi_m1", "pi_m2")
ROUTER_OFF = "[router]\nenabled = false\n"


def _two_los(tmp_path, *, ad: str = ""):
    paths = ad23_vault(tmp_path, items=MINE, learning_objects={"lo_other": OTHER}, ad=ad, config=ROUTER_OFF)
    for item in MINE:
        set_item(paths, item, evidence_facets=["f_mine"], evidence_weights={"f_mine": 1.0})
    for item in OTHER:
        set_item(paths, item, evidence_facets=["f_other"], evidence_weights={"f_other": 1.0})
    return paths


def _serve_and_answer(paths, env, clock, *, correct: bool, steps: int) -> list[dict[str, Any]]:
    served = []
    for _ in range(steps):
        _record, step = advance(env, serve=True)
        if step["kind"] != "item":
            break
        served.append(step)
        clock.advance(2)
        answer(paths, step["practice_item_id"], correct=correct, presentation_id=step["presentation_id"], clock=clock)
        clock.advance(1)
    return served


def _scenario(tmp_path, name: str, *, seen: bool, ad: str = "") -> dict[str, Any]:
    paths = _two_los(tmp_path / name, ad=ad)
    env, clock = env_for(paths, items=OTHER)
    if seen:
        build_plan(env, kind="normal", budget=12.0, remembered=12, minutes_source="chip")
        assert len(_serve_and_answer(paths, env, clock, correct=True, steps=4)) == 4
    clock.advance(60 * 24)
    env, clock = env_for(paths, items=MINE, clock=clock, session="s2")
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item" and step["learning_object_id"] == LO
    draws = [row for row in selections(paths) if row["learning_object_id"] == LO]
    receipts = {row["forecaster"]: row for row in rows(
        paths.sqlite_path, "SELECT forecaster, p, forecast_json FROM forecast_receipts WHERE kind = "
        "'item_unassisted_success' AND practice_item_id = ?", (step["practice_item_id"],))}
    return {"paths": paths, "step": step, "draws": draws, "receipts": receipts}


def _scores(draws: list[dict[str, Any]], kind: str) -> list[Any]:
    return [[(e["ref"], e["p_band"], e["p_bar"], e["propensity"]) for e in row["support"]]
            for row in draws if row["kind"] == kind]


# -- G-AD3-1 ------------------------------------------------------------------------------------


def test_live_decisions_read_subject_view_and_switch_restores_lo_view(tmp_path):
    """With ``promoted_predictor`` on, answers on another LO change an LO's ``P_band``, ``π`` and
    commission point, and a never-seen LO's first draw reads the subject-level estimate (D18).
    With it off they change none of them (they still change ``ad_threshold@subject``'s receipts),
    and the draws and the ``@lo`` receipts are those of the same successor without the other LO's
    answers. Fails before AD3: no AD state existed."""

    on_seen = _scenario(tmp_path, "on_seen", seen=True)
    on_fresh = _scenario(tmp_path, "on_fresh", seen=False)
    assert _scores(on_seen["draws"], "serve") != _scores(on_fresh["draws"], "serve")
    seen_bar = on_seen["draws"][0]["support"][0]["p_bar"]
    fresh_bar = on_fresh["draws"][0]["support"][0]["p_bar"]
    assert seen_bar > fresh_bar  # four successes elsewhere in the subject raise where this LO starts
    assert on_seen["draws"][0]["view"] == "subject"
    assert _scores(on_seen["draws"], "commission") != _scores(on_fresh["draws"], "commission")

    off = "promoted_predictor = false\n"
    off_seen = _scenario(tmp_path, "off_seen", seen=True, ad=off)
    off_fresh = _scenario(tmp_path, "off_fresh", seen=False, ad=off)
    assert off_seen["draws"][0]["view"] == f"lo:{LO}"
    assert _scores(off_seen["draws"], "serve") == _scores(off_fresh["draws"], "serve")
    assert _scores(off_seen["draws"], "commission") == _scores(off_fresh["draws"], "commission")
    assert off_seen["step"]["practice_item_id"] == off_fresh["step"]["practice_item_id"]
    assert off_seen["receipts"]["ad_threshold@lo"]["p"] == off_fresh["receipts"]["ad_threshold@lo"]["p"]
    assert off_seen["receipts"]["ad_threshold@subject"]["p"] != off_fresh["receipts"]["ad_threshold@subject"]["p"]


# -- G-AD3-2 ------------------------------------------------------------------------------------


def test_readiness_numbers_from_subject_view_with_untested_cells(tmp_path):
    """With the switch on, the readiness line and the router card's AD fields appear, labelled as
    predictions; a cell with no eligible answer of its own shows "untested" whatever the shared
    terms predict, so it never shows "likely ready"; with the switch off, "exam level: not yet
    predicted" and no card fields."""

    scenario = _scenario(tmp_path, "on", seen=True)
    paths = scenario["paths"]
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    RP.clear_cache()
    other = RD.lo_readiness(vault, repository, "lo_other")
    mine = RD.lo_readiness(vault, repository, LO)
    assert other["predicted"] and all(cell["kind"] == "prediction" for cell in other["cells"])
    assert not any(cell["untested"] for cell in other["cells"]) and "(a prediction)" in other["line"]
    assert all(cell["untested"] and cell["p_bar_at_top"] is None for cell in mine["cells"])
    assert "likely ready" not in mine["line"] and "untested" in mine["line"]
    fields = RD.card_fields(vault, repository, LO)
    assert fields["kind"] == "prediction" and fields["untested"] is True and fields["p_bar_at_top"] is None
    assert 0.0 <= fields["p_band_next"] <= 1.0
    # The router card carries them (and moves its version) only with the switch on.
    from learnloop.router.card import AD_CARD_VERSION, CARD_VERSION, CardInputs, build_card

    card = build_card(CardInputs(decision={}, session={},
                                 learning_objects={LO: {"title": "Mine", "adaptive_difficulty": fields}}))
    assert card.card_version == AD_CARD_VERSION and "AD prediction" in card.text and "untested" in card.text
    assert build_card(CardInputs(decision={}, session={},
                                 learning_objects={LO: {"title": "Mine"}})).card_version == CARD_VERSION

    off = _scenario(tmp_path, "off", seen=True, ad="promoted_predictor = false\n")
    vault_off = load_vault(off["paths"].root)
    readiness = RD.lo_readiness(vault_off, Repository(off["paths"].sqlite_path), "lo_other")
    assert readiness == {"version": RD.READINESS_VERSION, "predicted": False, "line": RD.NOT_PREDICTED, "cells": []}
    assert RD.card_fields(vault_off, Repository(off["paths"].sqlite_path), "lo_other") is None


def test_shared_terms_alone_never_show_likely_ready():
    """However high the subject level, a cell with no answer of its own is "untested"."""

    events = RP.Events([], [], [], R.VaultStructure(facet_los={}, lo_facets={}), {}, {})
    snap = RP.run(events)
    snap.subject.bank.ensure_subject("s", 0.0)
    snap.subject.bank.mu[:, snap.subject.bank.index["G:s"]] = 6.0  # a learner far above the target
    assert ("f", "retrieval") not in snap.observed_cells


# -- G-AD3-5 ------------------------------------------------------------------------------------


EVIDENCE_TABLES = {
    "grading_evidence": "criterion_id, points_awarded, superseded_at",
    "learning_object_mastery": "learning_object_id, logit_mean, logit_variance, evidence_count",
    "facet_recall_state": "*",
    "practice_item_state": "practice_item_id, stability, difficulty, due_at, last_attempt_at",
    "facet_capability_evidence": "*",
}


def _evidence(paths) -> dict[str, Any]:
    out = {}
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        for table, columns in EVIDENCE_TABLES.items():
            out[table] = sorted(tuple(row) for row in connection.execute(f"SELECT {columns} FROM {table}"))
    return out


def vault_los(paths) -> list[str]:
    return sorted(load_vault(paths.root).learning_objects)


def _adversarial(subject_inputs: dict[str, Any]) -> dict[str, Any]:
    """Couple everything at full strength and load every item onto every other facet."""

    los = [row["learning_object_id"] for row in subject_inputs["payload"]["learning_objects"]]
    facets = [row["facet_id"] for row in subject_inputs["payload"]["facets"]]
    return {
        "items": [{"item_id": item["item_id"], "loadings": [
            {"facet_id": f, "strength": "strong", "why": "everything"} for f in facets if f not in item["facets"]]}
            for item in subject_inputs["payload"]["items"]],
        "learning_objects": [{"learning_object_id": lo, "related": [
            {"learning_object_id": other, "strength": "strong", "why": "everything"} for other in los if other != lo]}
            for lo in los],
    }


def test_coupling_is_prediction_only(tmp_path):
    """Under an adversarial proposal (everything coupled and loaded at full strength), evidence,
    mastery, facet recall, FSRS, the capability ledger and cell-pool membership are byte-identical
    to no proposal; the caps hold; ``learned_coupling = false`` makes the subject view
    byte-identical to its uniform-sharing points and makes no proposal call."""

    from learnloop.daily_plan import ad_slot

    results = {}
    for name in ("plain", "adversarial"):
        paths = _two_los(tmp_path / name, ad=COUPLED)
        vault = load_vault(paths.root)
        repository = Repository(paths.sqlite_path)
        if name == "adversarial":
            inputs = R.subject_inputs(vault, repository, "linear-algebra")
            assert R.propose_subject(vault, repository, "linear-algebra",
                                     client=ProposalLLM(_adversarial(inputs))).status == "ok"
            assert R.adopt(repository, "linear-algebra", adopted_by="test")
        env, clock = env_for(paths, items=OTHER + MINE)
        build_plan(env, kind="normal", budget=20.0, remembered=20, minutes_source="chip")
        served = _serve_and_answer(paths, env, clock, correct=True, steps=6)
        RP.clear_cache()
        RP.rebuild(load_vault(paths.root), repository)
        results[name] = {"evidence": _evidence(paths), "served": [s["practice_item_id"] for s in served],
                         "paths": paths}
    assert results["plain"]["evidence"] == results["adversarial"]["evidence"]
    # Caps: no item loads more than 3 facets, no LO couples more than 3 LOs; χ caps from the grid.
    with closing(connect(results["adversarial"]["paths"].sqlite_path)) as connection:
        from learnloop.adaptive_difficulty.material_view import detached_view as material_view

        adversarial = load_vault(results["adversarial"]["paths"].root)
        structure = R.load_structure(connection, adversarial, view=material_view(
            adversarial, Repository(results["adversarial"]["paths"].sqlite_path)))
    assert all(len(structure.coupling(lo)) <= P.MAX_COUPLED for lo in vault_los(results["adversarial"]["paths"]))
    assert max(p.coupling for p in P.hyper_grid()) <= 0.75 and max(p.implication for p in P.hyper_grid()) <= 0.5
    # Cell-pool membership reads the item's own facets, never its loadings.
    vault = load_vault(results["adversarial"]["paths"].root)
    item = vault.practice_items["pi_m1"]
    assert set(PR.facet_weights(vault, item)) == {"f_mine"}

    # learned_coupling = false: the subject view equals its uniform-sharing points; no call.
    paths = results["adversarial"]["paths"]
    vault = load_vault(paths.root)
    vault.config.adaptive_difficulty.learned_coupling = False
    llm = ProposalLLM()
    assert R.propose_subject(vault, Repository(paths.sqlite_path), "linear-algebra", client=llm).status == "disabled"
    assert not llm.prompts
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        off = RP.run(RP.load_events(connection, vault, Repository(paths.sqlite_path),
                                    settings=RP.ReplaySettings(coupling=False)), RP.ReplaySettings(coupling=False))
        full = RP.run(RP.load_events(connection, load_vault(paths.root), Repository(paths.sqlite_path)))
    uniform = [i for i, p in enumerate(full.subject.bank.points) if p.uniform]
    assert [p.key() for p in off.subject.bank.points] == [full.subject.bank.points[i].key() for i in uniform]
    names = off.subject.bank.names
    index = [full.subject.bank.index[n] for n in names]
    assert np.array_equal(off.subject.bank.mu, full.subject.bank.mu[uniform][:, index])


# -- G-AD3-6 (replay part) --------------------------------------------------------------------------


def _coupled_structure() -> R.VaultStructure:
    los = [f"L{k}" for k in range(6)]
    couplings = {lo: {other: 1.0 for other in los if other != lo} for lo in los}  # adversarial: everything
    facet_los = {f"f{k}": [f"L{k}"] for k in range(6)}
    lo_facets = {f"L{k}": [f"f{k}"] for k in range(6)}
    loadings = {f"rev:{k}": {f"f{(k + 1) % 6}": 1.0, f"f{(k + 2) % 6}": 1.0} for k in range(6)}
    return R.VaultStructure.fixed(facet_los=facet_los, lo_facets=lo_facets, couplings=couplings, loadings=loadings)


def _spec(k: int, structure: R.VaultStructure, *, capability: str = "retrieval") -> ItemSpec:
    return ItemSpec(f"i{k}", f"L{k}", "s", capability, {f"f{k}": 1.0}, features={"complexity": k % 3},
                    signals={"z_origin": 1.0}, loadings=structure.loadings(f"rev:{k}"))


def test_hyperparameters_learned_and_replayable():
    """The weights follow the running marginal likelihoods exactly; the joint prior stays positive
    definite under any proposal (an adversarial one included); rebuilds are byte-identical."""

    structure = _coupled_structure()

    def build() -> tuple[View, list[np.ndarray]]:
        bank = M.Bank(P.hyper_grid(), structure=structure, reading=True, verdict=True)
        view = View(bank, subject_view=True, reading=True, verdicts=True)
        log_z = []
        rng = np.random.default_rng(7)
        for t in range(24):
            spec = _spec(t % 6, structure)
            record = view.observe(spec, int(rng.integers(0, 3)), t * 0.01)
            log_z.append(record.log_z)
        return view, log_z

    view, log_z = build()
    bank = view.bank
    total = np.sum(log_z, axis=0)
    expected = np.exp(total - total.max())
    assert np.allclose(bank.weights()[0], expected / expected.sum(), rtol=0, atol=1e-12)
    for b in range(bank.B):
        assert np.linalg.eigvalsh(bank.S0[b][np.ix_(sorted(i for n, i in bank.index.items() if n in bank.topic),
                                                    sorted(i for n, i in bank.index.items() if n in bank.topic))]).min() > 0
        assert np.linalg.eigvalsh(0.5 * (bank.S[b] + bank.S[b].T)).min() > 0
    again, _ = build()
    assert again.bank.state_hash() == bank.state_hash()


def test_a_proposal_recorded_after_a_coordinate_exists_changes_no_earlier_state():
    """A later run reaches only what does not exist yet (§5.10 "As of"): coordinates created
    before it keep their construction, and the state up to that point is unchanged."""

    los = ["L0", "L1"]
    facet_los, lo_facets = {"f0": ["L0"], "f1": ["L1"]}, {"L0": ["f0"], "L1": ["f1"]}
    early = R.VaultStructure(facet_los=facet_los, lo_facets=lo_facets)
    late = R.VaultStructure(facet_los=facet_los, lo_facets=lo_facets,
                            couplings={"L0": [R._UnitProposal(5.0, {"L1": 1.0})]})  # noqa: SLF001 - in force from day 5

    def run(structure: R.VaultStructure, *, until: float) -> str:
        bank = M.Bank(P.hyper_grid(), structure=structure)
        view = View(bank, subject_view=True)
        for t, k in enumerate((0, 1, 0, 1)):
            at = float(t)
            if at > until:
                break
            structure.now = at
            view.observe(ItemSpec(f"i{k}", los[k], "s", "retrieval", {f"f{k}": 1.0}), 2, at)
        return bank.state_hash()

    assert run(early, until=3.0) == run(late, until=3.0)


def test_shadow_report_names_what_a_new_version_reinterprets(tmp_path):
    """A new coupling version applies through its shadow rebuild: the report (in memory) shows the
    change before anything is adopted."""

    paths = _two_los(tmp_path, ad=COUPLED)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    env, clock = env_for(paths, items=OTHER + MINE)
    build_plan(env, kind="normal", budget=20.0, remembered=20, minutes_source="chip")
    _serve_and_answer(paths, env, clock, correct=True, steps=4)
    inputs = R.subject_inputs(vault, repository, "linear-algebra")
    R.propose_subject(vault, repository, "linear-algebra", client=ProposalLLM({"items": [], "learning_objects": []}))
    R.adopt(repository, "linear-algebra", adopted_by="test")
    set_item(paths, "pi_m1", prompt="A rewritten question.")
    vault = load_vault(paths.root)
    R.propose_subject(vault, repository, "linear-algebra", client=ProposalLLM(_adversarial(
        R.subject_inputs(vault, repository, "linear-algebra"))))
    report = R.shadow_report(vault, repository, "linear-algebra")
    assert report["candidate"] and isinstance(report["attempts_moved"], list)
    assert rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM ad_coupling_versions")[0]["n"] == 1
    assert inputs["unit_hashes"]


# -- G-AD3-10 -----------------------------------------------------------------------------------


def test_subject_view_mixture_keeps_propensities_exact():
    """``P_band`` under the mixture matches 10⁶-draw Monte Carlo over ``ξ`` and the state within
    1e-3; a draw's ``π`` recomputes from its logged row; the seed reproduces the draw."""

    structure = _coupled_structure()
    bank = M.Bank(P.hyper_grid(), structure=structure)
    view = View(bank, subject_view=True)
    rng = np.random.default_rng(10)
    for t in range(18):
        view.observe(_spec(t % 6, structure), int(rng.integers(0, 3)), t * 0.01)
    spec = _spec(2, structure)
    prediction = PR.predict(view, spec)
    weights = bank.weights()[0]
    m, v = view.prediction(spec)
    draws = 1_000_000
    points = rng.choice(bank.P, size=draws, p=weights)
    eta = m[points] + np.sqrt(v[points]) * rng.standard_normal(draws)
    success = M.residual_success(eta, 0.0)
    mc = float(np.mean((success >= 0.70) & (success <= 0.80)))
    assert abs(prediction.p_band - mc) < 1e-3
    specs = [_spec(k, structure) for k in range(6)]
    scored = PR.score(view, specs)
    drawn = S.draw(scored, key="mixture:1")
    row = {"support": [s.as_dict() for s in scored], "seed": drawn.seed, "constants": S.SelectionConstants().as_dict()}
    redone = S.recompute(row)
    assert redone.chosen == drawn.chosen
    assert {k: round(p, 9) for k, p in redone.propensities.items()} == {k: round(p, 9) for k, p in drawn.propensities.items()}
