"""Adaptive difficulty AD3: reading raises the prediction, never evidence (spec §5.11; G-AD3-8, G-AD3-15 (1)-(5)).

Each failed before AD3: no reading transition and no verdict term existed (AD1
froze the receipts and nothing read them). The synthetic-learner parts of
G-AD3-8 and G-AD3-15 are in ``tests/test_ad23_sim.py``. Fakes only.
"""

from __future__ import annotations

import json
from contextlib import closing
from typing import Any

import numpy as np
import pytest

from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty import relatedness as R
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty.state import ItemSpec, View
from learnloop.attempts.salience_firewall import (
    SALIENCE_ONLY,
    SalienceEvidenceRejected,
    learning_opportunity_events,
    reject_salience,
)
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import ad_receipts
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import LO, SEEDED, ad23_vault, answer, env_for, restamp, rows

KIND = "worked_example"


def _view(*, structure: Any = None, points=(P.LO_VIEW_POINT,), verdicts: bool = True) -> View:
    bank = M.Bank(points, structure=structure or M.Structure(), reading=True, verdict=True)
    return View(bank, subject_view=True, reading=True, verdicts=verdicts)


def _spec(facet: str = "f0", lo: str = "L0", loadings: dict[str, float] | None = None) -> ItemSpec:
    return ItemSpec(f"i_{facet}", lo, "s", "retrieval", {facet: 1.0}, signals={"z_origin": 1.0},
                    loadings=dict(loadings or {}))


def _m(view: View, spec: ItemSpec) -> np.ndarray:
    return view.prediction(spec)[0]


def _coefficient_means(view: View, kind: str) -> tuple[float, float]:
    bank = view.bank
    return tuple(float(bank.mu[0, bank.index[f"gbar:{m}"]] + bank.mu[0, bank.index[f"delta:{kind}:{m}"]])
                 for m in (1, 2))  # type: ignore[return-value]


# -- G-AD3-8 ------------------------------------------------------------------------------------


@pytest.mark.parametrize("kind", P.READING_KINDS)
def test_each_kind_raises_the_next_draw_by_its_next_increment(kind):
    """An opportunity of each kind raises the LO's predicted ``η`` mean by exactly its kind's next
    dose-curve increment; a second event of the kind in the window adds less (positive
    coefficients); a graded attempt on the facet resets the window."""

    view = _view()
    spec = _spec()
    view.ensure(spec, 0.0)
    c1, c2 = _coefficient_means(view, kind)
    before = _m(view, spec)
    view.reading("s", kind, {"f0": 1.0}, 0.0)
    first = _m(view, spec) - before
    b = M.dose_increment(0.0, 1.0)
    assert first == pytest.approx(c1 * b[0] + c2 * b[1], abs=1e-12)
    view.reading("s", kind, {"f0": 1.0}, 0.0)
    second = _m(view, spec) - before - first
    assert 0.0 < second[0] < first[0]
    view.close_windows(("f0",))
    third_before = _m(view, spec)
    view.reading("s", kind, {"f0": 1.0}, 0.0)
    assert _m(view, spec) - third_before == pytest.approx(first, abs=1e-12)


def test_reading_reaches_loading_items_and_coupled_topics():
    """Items elsewhere that load onto the facet gain through their loadings, and coupled topics by
    ``corr₀`` times the increment (§5.11)."""

    structure = R.VaultStructure.fixed(facet_los={"f0": ["L0"], "f1": ["L1"]}, lo_facets={"L0": ["f0"], "L1": ["f1"]},
                                       couplings={"L0": {"L1": 1.0}, "L1": {"L0": 1.0}})
    point = P.HyperPoint(1.5, 0.5, 0.5)
    view = _view(structure=structure, points=(point,))
    own, coupled = _spec("f0", "L0"), _spec("f1", "L1")
    loader = _spec("f1", "L1", loadings={"f0": 1.0})
    for spec in (own, coupled):
        view.ensure(spec, 0.0)
    before = {name: _m(view, spec) for name, spec in (("own", own), ("coupled", coupled), ("loader", loader))}
    view.reading("s", KIND, {"f0": 1.0}, 0.0)
    delta = {name: _m(view, spec) - before[name] for name, spec in (("own", own), ("coupled", coupled), ("loader", loader))}
    corr = float(view.bank.corr0("F:f0", "F:f1")[0])
    assert corr == pytest.approx(0.5)
    assert delta["coupled"] == pytest.approx(corr * delta["own"], abs=1e-12)
    # The loader's own facet moved by corr₀ x Δ, and its loaded facet by Δ, at weight χ_Q·Q = 0.5.
    assert delta["loader"] == pytest.approx(0.5 * delta["coupled"] + 0.5 * delta["own"], abs=1e-12)


def test_an_in_passage_answer_graded_as_an_attempt_takes_its_increment_not_gamma():
    view = _view()
    spec = _spec()
    plain = _view()
    for v in (view, plain):
        v.ensure(spec, 0.0)
    view.observe(spec, 2, 0.0, in_passage_kind="in_passage_question")
    plain.observe(spec, 2, 0.0, learn=False)
    gamma = view.bank.index["gamma"]
    cell = view.bank.index["E:f0:retrieval"]
    facet = view.bank.index["F:f0"]
    # No γ transition: the cell gained nothing γ-shaped, the facet its kind's increment.
    assert view.bank.S[0, cell, gamma] == pytest.approx(plain.bank.S[0, cell, gamma], abs=1e-12)
    assert view.bank.mu[0, facet] != pytest.approx(plain.bank.mu[0, facet])
    assert view.windows[("in_passage_question", "f0")][0] == pytest.approx(1.0)


def _opportunity(connection: Any, *, key: str, kind: str, subkind: str, source_table: str, at: str,
                 lo: str = LO, doses: dict[str, float] | None = None) -> None:
    ad_receipts.insert_reading_opportunity(connection, {
        "protection_epoch": SEEDED, "opportunity_key": key, "kind": kind, "subkind": subkind, "source_table": source_table,
        "source_id": key, "source_written_at": at, "learning_object_id": lo,
        "facet_doses": doses or {"recall": 1.0}, "dose_offer_id": None, "mapping_version": "ad_reading_map_v1",
        "sweep": "backfill", "sweep_ref": None, "swept_at": at})


def _reading_vault(tmp_path, *, ad: str = ""):
    items = ("pi_r1", "pi_r2", "pi_r3")
    paths = ad23_vault(tmp_path, items=items, ad=ad, config="[router]\nenabled = false\n")
    env, clock = env_for(paths, items=items)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    with closing(connect(paths.sqlite_path)) as connection:
        _opportunity(connection, key="o1", kind="reading", subkind="section_read",
                     source_table="reader_section_progress", at="2026-10-12T08:00:00Z")
        _opportunity(connection, key="o2", kind="worked_example", subkind="shown", source_table="source_exposure_events",
                     at="2026-10-12T08:10:00Z")
        _opportunity(connection, key="o3", kind="in_passage_question", subkind="self_check:missed",
                     source_table="judgment_ledger", at="2026-10-12T08:20:00Z")
        connection.commit()
    restamp(paths)  # recorded under the vault's protection as it stands
    for k in range(3):
        _record, step = advance(env, serve=True)
        if step["kind"] != "item":
            break
        clock.advance(2)
        answer(paths, step["practice_item_id"], correct=k != 1, presentation_id=step["presentation_id"], clock=clock)
        clock.advance(1)
    return paths


EVIDENCE = ("grading_evidence", "learning_object_mastery", "facet_recall_state", "practice_item_state",
            "facet_capability_evidence")


def _evidence(paths) -> dict[str, Any]:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        out = {}
        for table in EVIDENCE:
            cursor = connection.execute(f"SELECT * FROM {table}")
            names = [d[0] for d in cursor.description]
            keep = [i for i, n in enumerate(names) if not (n == "id" or n.endswith("_id") and n not in (
                "practice_item_id", "learning_object_id", "facet_id", "criterion_id") or n.endswith("_at"))]
            out[table] = sorted((tuple(row[i] for i in keep) for row in cursor.fetchall()), key=repr)
    return out


def test_reading_raises_prediction_never_evidence(tmp_path):
    """Every evidence, mastery, facet-recall, FSRS and capability-ledger table is byte-identical
    with reading on vs off; no reading opportunity passes ``apply_attempt``'s first step
    (``reject_salience``); ``reading_opportunities = false`` makes the subject view byte-identical
    to one with no reading transitions."""

    # The same answers in both (selection off: the same items served), reading on vs off.
    on = _reading_vault(tmp_path / "on", ad="selection = false\n")
    off = _reading_vault(tmp_path / "off", ad="selection = false\nreading_opportunities = false\n")
    assert _evidence(on) == _evidence(off)
    vault = load_vault(on.root)
    repository = Repository(on.sqlite_path)
    with closing(connect(on.sqlite_path, read_only=True)) as connection:
        receipt = [dict(row) for row in connection.execute("SELECT * FROM ad_reading_opportunities")]
        events = RP.load_events(connection, vault, repository)
    assert len(events.opportunities) == 3
    for record in learning_opportunity_events(receipt):
        assert record["authority_class"] == SALIENCE_ONLY
        with pytest.raises(SalienceEvidenceRejected):
            reject_salience(record)
    with_reading = RP.run(events, RP.ReplaySettings())
    switched_off = RP.run(events, RP.ReplaySettings(reading=False, verdicts=False))
    stripped = RP.Events(events.attempts, events.claims, [], events.structure, events.lo_subject, events.lo_facets)
    no_events = RP.run(stripped, RP.ReplaySettings(reading=False, verdicts=False))
    assert switched_off.subject.bank.state_hash() == no_events.subject.bank.state_hash()
    assert with_reading.subject.bank.state_hash() != switched_off.subject.bank.state_hash()
    assert RP.ReplaySettings.from_config(load_vault(off.root).config).reading is False


# -- G-AD3-15 (1)-(5) -----------------------------------------------------------------------------


def _verdict_view(*, lam_var: float | None = None, structure: Any = None, points=(P.LO_VIEW_POINT,)) -> View:
    view = _view(structure=structure, points=points)
    if lam_var is not None:
        bank = view.bank
        for name in ("lam:matched", "lam:missed"):
            i = bank.index[name]
            bank.S[:, i, :] = 0.0
            bank.S[:, :, i] = 0.0
            bank.S[:, i, i] = lam_var
    return view


def test_self_check_verdict_shifts_prediction_never_evidence():
    """(1) With ``λ`` at its prior mean (and no spread) the predictions equal D20's exactly.
    (2) A ``missed`` verdict with a learned negative ``λ_missed`` lowers the facet's next draw, a
    coupled facet's by ``corr₀`` times it and a loading item's; a ``matched`` verdict with a
    positive ``λ_matched`` raises it. Fails before AD3: no verdict term existed."""

    spec = _spec()
    with_term = _verdict_view(lam_var=0.0)
    d20 = _view(verdicts=False)
    for view in (with_term, d20):
        view.ensure(spec, 0.0)
        view.reading("s", "in_passage_question", {"f0": 1.0}, 0.0)
    with_term.verdict("s", "self_check:missed", {"f0": 1.0}, 0.0)
    d20.verdict("s", "self_check:missed", {"f0": 1.0}, 0.0)
    assert np.array_equal(with_term.prediction(spec)[0], d20.prediction(spec)[0])
    assert np.allclose(with_term.prediction(spec)[1], d20.prediction(spec)[1], atol=1e-15)

    structure = R.VaultStructure.fixed(facet_los={"f0": ["L0"], "f1": ["L1"]}, lo_facets={"L0": ["f0"], "L1": ["f1"]},
                                       couplings={"L0": {"L1": 1.0}, "L1": {"L0": 1.0}})
    point = P.HyperPoint(1.5, 0.5, 0.5)
    learned = _verdict_view(structure=structure, points=(point,))
    bank = learned.bank
    bank.mu[:, bank.index["lam:missed"]] = -0.4
    bank.mu[:, bank.index["lam:matched"]] = 0.3
    own, coupled, loader = _spec("f0", "L0"), _spec("f1", "L1"), _spec("f1", "L1", loadings={"f0": 1.0})
    for s in (own, coupled):
        learned.ensure(s, 0.0)
    before = {n: _m(learned, s) for n, s in (("own", own), ("coupled", coupled), ("loader", loader))}
    learned.verdict("s", "self_check:missed", {"f0": 1.0}, 0.0)
    delta = {n: _m(learned, s) - before[n] for n, s in (("own", own), ("coupled", coupled), ("loader", loader))}
    assert delta["own"][0] == pytest.approx(-0.4) and delta["coupled"][0] == pytest.approx(0.5 * -0.4)
    assert delta["loader"][0] < 0
    raised = _m(learned, own)
    learned.verdict("s", "self_check:matched", {"f0": 1.0}, 0.0)
    assert _m(learned, own)[0] - raised[0] == pytest.approx(0.3)


def test_a_question_counts_once_and_no_verdict_reaches_evidence(tmp_path):
    """(3) A changed verdict appends a ledger row and moves nothing (AD1's sweep records only the
    first). (4) ``reject_salience`` still refuses the verdict's receipt record."""

    from tests.test_ad1_reading_opportunities import FakeMap, _question, _setup, _sweep, at
    from learnloop.reader import reader_quick_check as RQC

    paths, vault, repo = _setup(tmp_path)
    question = _question(repo, "recall", 1)
    RQC.record_inquiry_action(repo, question_id=question, action="self_checked", self_check="no", clock=at(2))
    _sweep(vault, repo, 3)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        first = RP.run(RP.load_events(connection, vault, repo)).subject.bank.state_hash()
    RQC.record_inquiry_action(repo, question_id=question, action="self_checked", self_check="matches", clock=at(4))
    _sweep(vault, repo, 5)
    ledger = rows(paths.sqlite_path, "SELECT * FROM judgment_ledger WHERE task = 'reader_quick_check_self_check'")
    assert len(ledger) == 2
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        assert RP.run(RP.load_events(connection, vault, repo)).subject.bank.state_hash() == first
        receipt = [dict(r) for r in connection.execute(
            "SELECT * FROM ad_reading_opportunities WHERE subkind LIKE 'self_check:%'")]
    (record,) = learning_opportunity_events(receipt)
    assert record["subkind"] == "self_check:missed"
    with pytest.raises(SalienceEvidenceRejected):
        reject_salience(record)


def test_reading_self_check_switch_restores_d20_and_is_moot_without_reading(tmp_path):
    """(5) ``reading_self_check = false`` gives predictions and draws byte-identical to D20's (the
    receipt rows still written), and the switch is moot under ``reading_opportunities = false``."""

    paths = _reading_vault(tmp_path / "v")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        events = RP.load_events(connection, vault, repository)
    assert any(o.subkind == "self_check:missed" for o in events.opportunities)
    no_verdict = RP.run(events, RP.ReplaySettings(verdicts=False))
    stripped = RP.Events(events.attempts, events.claims,
                         [o for o in events.opportunities if o.subkind not in P.VERDICT_CLASSES],
                         events.structure, events.lo_subject, events.lo_facets)
    d20 = RP.run(stripped, RP.ReplaySettings(verdicts=False))
    assert no_verdict.subject.bank.state_hash() == d20.subject.bank.state_hash()
    assert RP.run(events, RP.ReplaySettings()).subject.bank.state_hash() != d20.subject.bank.state_hash()
    off = RP.run(events, RP.ReplaySettings(reading=False, verdicts=True))
    off_both = RP.run(events, RP.ReplaySettings(reading=False, verdicts=False))
    assert off.subject.bank.state_hash() == off_both.subject.bank.state_hash()
    vault.config.adaptive_difficulty.reading_self_check = False
    assert RP.ReplaySettings.from_config(vault.config).verdicts is False
    assert rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM ad_reading_opportunities WHERE subkind = "
                                   "'self_check:missed'")[0]["n"] == 1
