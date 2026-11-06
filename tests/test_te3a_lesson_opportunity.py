"""Teacher TE3a: AD's lesson opportunity and the objective's lesson interface (spec_teacher_v1 rev 5 §14.2, §24).

The §24 TE3a row's tests:

* the AD guard refuses unclassified and raw reads of the lesson tables and fails closed (no lesson opportunity
  while the held-out predicate is unavailable; a lesson whose goal names a withheld reading is absent: Option B);
* replay equivalence: the live snapshot, a fresh replay of the recorded receipts and the rebuild agree;
* switch off (or below the tag) is AD's predecessor exactly, and RO4's placeholder exactly;
* at the seeded prior the objective's lesson ``Q̄`` equals RO4's placeholder within float tolerance;
* AD never writes evidence or mastery (the import-linter contract, and the evidence tables byte-identical);
* the report's ``lesson`` row.

Fakes only (synthetic vaults); no model call.
"""

from __future__ import annotations

import json
import math
import sqlite3
from contextlib import closing
from dataclasses import replace
from typing import Any

import numpy as np
import pytest

from learnloop.adaptive_difficulty import dose_report as DR
from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import operation as O
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty import protected_tables as T
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty.readiness import decision_state_fields, lesson_curve_moments
from learnloop.adaptive_difficulty.reading import sweep
from learnloop.adaptive_difficulty.state import ItemSpec, View
from learnloop.algorithm_versions import LESSON_OPPORTUNITY_ALGORITHM_VERSION, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
from learnloop.attempts import salience_firewall as SF
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.router_objective import memory as MEM
from learnloop.router_objective import value as V
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import LO, ad23_vault, answer
from tests.daily_plan_fakes import MovableClock

TAG = LESSON_OPPORTUNITY_ALGORITHM_VERSION
OLD = ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
ITEMS = ("pi_l1", "pi_l2", "pi_l3")
#: The lesson closes the day before the answers (the fakes' clock starts 2026-10-12 09:00).
CLOSED = "2026-10-11T10:00:00.000000Z"
EVIDENCE = ("grading_evidence", "learning_object_mastery", "facet_recall_state", "practice_item_state",
            "facet_capability_evidence")


# -- the prior, the allowlist and the view's gate ------------------------------------------------------------------


def test_the_prior_is_centred_and_spread_on_ro4s_placeholder_with_ads_shape():
    from learnloop.learner.lesson_weight import ETA0_PRIOR_MEAN

    assert P.LESSON_CHECK_MASS_PRIOR == pytest.approx(1.0 / (1.0 + math.exp(-ETA0_PRIOR_MEAN)))
    assert SF.LESSON_SUBKINDS == P.LESSON_SUBKINDS == ("landed", "taught")
    prior = {name: (mean, var) for name, mean, var in P.LESSON_PRIORS}
    first = M.dose_increment(0.0, 1.0)
    for subkind in P.LESSON_SUBKINDS:
        (m1, v1), (m2, v2) = prior[f"lesson:{subkind}:1"], prior[f"lesson:{subkind}:2"]
        assert first[0] * m1 + first[1] * m2 == pytest.approx(P.GAMMA_PRIOR[1] * P.LESSON_CHECK_MASS_PRIOR, abs=1e-15)
        assert first[0] ** 2 * v1 + first[1] ** 2 * v2 == pytest.approx(
            P.GAMMA_PRIOR[2] * P.LESSON_CHECK_MASS_PRIOR ** 2, abs=1e-15)
        # AD's rule for a new kind (the reading kinds' gbar + delta) sets the ratios between the two scales.
        assert m2 / m1 == pytest.approx(0.20 / 0.10) and v2 / v1 == pytest.approx(0.02 / 0.0098)
    assert prior["lesson:landed:1"] == prior["lesson:taught:1"] and prior["lesson:landed:2"] == prior["lesson:taught:2"]


def _record(subkind: str, table: str = "lesson_receipts", kind: str = "lesson") -> dict[str, Any]:
    return {"id": f"o_{subkind}", "kind": kind, "subkind": subkind, "source_table": table, "source_id": "les_1/n1",
            "source_written_at": CLOSED, "learning_object_id": LO, "facet_doses": {"recall": 1.0},
            "authority_class": SF.SALIENCE_ONLY}


def test_the_firewall_admits_exactly_the_lesson_subkinds_and_they_stay_salience_only():
    admitted = SF.learning_opportunity_events([_record("landed"), _record("taught")])
    assert [record["subkind"] for record in admitted] == ["landed", "taught"]
    for record in admitted:
        assert record["authority_class"] == SF.SALIENCE_ONLY
        with pytest.raises(SF.SalienceEvidenceRejected):
            SF.reject_salience(record)
    for refused in (_record("held"), _record("uncertain"), _record("landed", table="lesson_checks"),
                    _record("landed", table="lesson_turns"), _record("landed", kind="lessons")):
        assert SF.learning_opportunity_events([refused]) == []
    assert "lesson" in SF.LEARNING_OPPORTUNITY_KINDS and "lesson" not in SF.READING_OPPORTUNITY_KINDS


def _view(*, lessons: bool, points=(P.LO_VIEW_POINT,)) -> View:
    bank = M.Bank(points, structure=M.Structure(), reading=True, verdict=True)
    return View(bank, subject_view=True, reading=True, verdicts=True, lessons=lessons)


def _spec(facet: str = "f0") -> ItemSpec:
    return ItemSpec(f"i_{facet}", "L0", "s", "retrieval", {facet: 1.0}, signals={"z_origin": 1.0})


def test_the_view_gate_applies_each_subkinds_curve_and_off_is_the_predecessor_exactly():
    spec = _spec()
    on, off, plain = _view(lessons=True), _view(lessons=False), _view(lessons=False)
    for view in (on, off, plain):
        view.ensure(spec, 0.0)
    before = on.prediction(spec)[0].copy()
    assert not any(name.startswith("lesson:") for name in on.bank.names)  # created lazily, at the first lesson
    for view in (on, off):
        view.reading("s", "lesson", {"f0": 1.0}, 0.0, subkind="landed")
    # Off: nothing at all (no coordinate, no window): the predecessor's bank exactly.
    assert off.bank.state_hash() == plain.bank.state_hash() and off.windows == plain.windows
    step = on.prediction(spec)[0] - before
    assert step[0] == pytest.approx(P.GAMMA_PRIOR[1] * P.LESSON_CHECK_MASS_PRIOR, abs=1e-12)
    # A taught node takes the taught curve, on the same (shared) lesson window: the second dose adds less.
    taught_before = on.prediction(spec)[0].copy()
    on.reading("s", "lesson", {"f0": 1.0}, 0.0, subkind="taught")
    second = on.prediction(spec)[0] - taught_before
    assert 0.0 < second[0] < step[0]
    assert on.windows[("lesson", "f0")][0] == pytest.approx(2.0)
    # Held, uncertain or any other status is no opportunity; a reading kind's window is untouched.
    hashed = on.bank.state_hash()
    on.reading("s", "lesson", {"f0": 1.0}, 0.0, subkind="held")
    on.reading("s", "lesson", {"f0": 1.0}, 0.0)
    assert on.bank.state_hash() == hashed and ("reading", "f0") not in on.windows
    # A graded attempt closes the lesson window as it closes reading's.
    on.close_windows(("f0",))
    assert on.windows[("lesson", "f0")][0] == 0.0


# -- a synthetic vault with a closed lesson ------------------------------------------------------------------------


def _vault(tmp_path, *, version: str = TAG, ad: str = "") -> Any:
    return ad23_vault(tmp_path, items=ITEMS, version=version, ad="selection = false\n" + ad,
                      config="[router]\nenabled = false\n")


def _lesson(paths: Any, lesson_id: str, nodes: list[dict[str, Any]], *, closed_at: str = CLOSED,
            goal: dict[str, Any] | None = None) -> None:
    """A closed lesson and its receipt, as TE1's close writes them (ids, statuses and LOs; no text AD reads)."""

    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO lessons(id, driver, origin, entry, goal_text, goal_json, learning_object_ids_json, "
            "doctrine_version, brief_version, algorithm_version, opened_at, closed_at, close_reason) "
            "VALUES (?, 'desktop', 'learner_pick', 'learning_object', 'teach me', ?, ?, 'd', 'b', ?, ?, ?, "
            "'goal_reached')",
            (lesson_id, json.dumps(goal or {"learning_object_ids": [LO]}), json.dumps([LO]), TAG,
             "2026-10-11T09:40:00.000000Z", closed_at))
        receipt = {"version": "lesson_receipt_v1", "lesson_id": lesson_id, "goal": goal or {}, "nodes": [
            {"id": node["id"], "lo_id": node.get("lo_id", LO), "status": node["status"], "anchors": [], "checks": []}
            for node in nodes], "recap": "retrieve the definition"}
        connection.execute("INSERT INTO lesson_receipts(lesson_id, receipt_version, close_reason, receipt_json, "
                           "created_at) VALUES (?, 'lesson_receipt_v1', 'goal_reached', ?, ?)",
                           (lesson_id, json.dumps(receipt), closed_at))
        connection.commit()


NODES = [{"id": "n1", "status": "landed"}, {"id": "n2", "status": "taught"}, {"id": "n3", "status": "held"},
         {"id": "n4", "status": "uncertain"}, {"id": "n5", "status": "landed", "lo_id": "lo_not_in_vault"}]


def _opportunities(paths: Any) -> list[dict[str, Any]]:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM ad_reading_opportunities WHERE kind = 'lesson' ORDER BY source_id")]


def _sweep(paths: Any) -> Any:
    vault = load_vault(paths.root)
    return sweep(vault, Repository(paths.sqlite_path), as_of="2026-11-06T12:00:00Z", sweep_kind="backfill")


def test_the_sweep_records_one_opportunity_per_landed_or_taught_node_once(tmp_path):
    paths = _vault(tmp_path)
    _lesson(paths, "les_a", NODES)
    first = _sweep(paths)
    rows = _opportunities(paths)
    assert [(row["subkind"], row["source_id"]) for row in rows] == [("landed", "les_a/n1"), ("taught", "les_a/n2")]
    vault = load_vault(paths.root)
    facets = sorted({facet for item in ITEMS for facet in vault.practice_items[item].evidence_facets or ()})
    for row in rows:
        assert row["source_table"] == "lesson_receipts" and row["learning_object_id"] == LO
        assert row["source_written_at"] == CLOSED  # the receipt's write time: when the outcome became known
        assert row["authority_class"] == "salience_only" and row["mapping_version"] == "ad_reading_map_v1"
        doses = json.loads(row["facet_doses_json"])
        assert doses and set(doses.values()) == {1.0} and sorted(doses) == facets  # one per node, each facet
    assert first.by_kind == {"lesson": 2}
    assert _sweep(paths).written == 0 and len(_opportunities(paths)) == 2  # idempotent


@pytest.mark.parametrize("setting", ["off", "below_tag"])
def test_switch_off_or_below_the_tag_records_nothing(tmp_path, setting):
    paths = (_vault(tmp_path, ad="lesson_opportunities = false\n") if setting == "off"
             else _vault(tmp_path, version=OLD))
    _lesson(paths, "les_a", NODES)
    _sweep(paths)
    assert _opportunities(paths) == []


def test_a_lesson_naming_a_withheld_reading_is_absent_and_an_unavailable_predicate_reads_none(tmp_path, monkeypatch):
    """Option B (§14.3): the receipt of a lesson whose goal names a reading the withheld material touches is withheld
    by the rules, so no opportunity is recorded from it; with the predicate unavailable nothing is (fail closed)."""

    from learnloop.adaptive_difficulty import material_view as MV

    paths = _vault(tmp_path)
    _lesson(paths, "les_held", [{"id": "n1", "status": "landed"}],
            goal={"learning_object_ids": [LO], "selection": {"extraction_id": "ext_exam", "span_ids": ["b1"]}})
    _lesson(paths, "les_open", [{"id": "n1", "status": "landed"}])
    original = MV.MaterialView.reading_withheld
    monkeypatch.setattr(MV.MaterialView, "reading_withheld",
                        lambda self, extraction_id: str(extraction_id) == "ext_exam" or original(self, extraction_id))
    _sweep(paths)
    assert [row["source_id"] for row in _opportunities(paths)] == ["les_open/n1"]

    unavailable = _vault(tmp_path / "unavailable")
    _lesson(unavailable, "les_a", NODES)
    built = MV.MaterialView.__init__

    def predicate_unavailable(self, *args: Any, **kwargs: Any) -> None:
        built(self, *args, **kwargs)
        self.available, self.reason = False, MV.UNAVAILABLE

    monkeypatch.setattr(MV.MaterialView, "__init__", predicate_unavailable)
    _sweep(unavailable)
    assert _opportunities(unavailable) == []


def test_the_guard_refuses_raw_and_unclassified_reads_of_lesson_tables(tmp_path):
    """The lesson tables are READING (PROTECTED): the rules read them; a raw read inside an operation is refused and
    poisons it; a table outside the registry is refused too (fail closed). The checks and turns stay DENIED."""

    paths = _vault(tmp_path)
    _lesson(paths, "les_a", NODES)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    assert {T.ROLES[t] for t in ("lessons", "lesson_receipts", "lesson_plans")} == {T.PROTECTED}
    assert {"lessons", "lesson_receipts", "lesson_plans"} <= T.READING
    assert {T.ROLES[t] for t in ("lesson_checks", "lesson_turns", "lesson_turn_payloads")} == {T.DENIED}
    assert T.read_verdict("no_such_lesson_table", rules="view") == "an unclassified table"
    with repository.atomic():
        connection = repository.connection()
        with pytest.raises(O.OperationPoisoned), O.ad_operation(vault, repository):
            with pytest.raises(sqlite3.DatabaseError, match="not authorized|is prohibited"):
                connection.execute("SELECT receipt_json FROM lesson_receipts").fetchall()
        with pytest.raises(O.OperationPoisoned), O.ad_operation(vault, repository):
            with pytest.raises(sqlite3.DatabaseError, match="not authorized|is prohibited"):
                connection.execute("SELECT * FROM lesson_checks").fetchall()
        with O.ad_operation(vault, repository):
            with O.rules(O.Scope.VIEW):
                rows = connection.execute("/* ad-rules */ SELECT lesson_id, receipt_json FROM lesson_receipts"
                                          ).fetchall()
        assert len(rows) == 1


# -- replay: equivalence, the switch, and never evidence -----------------------------------------------------------


def _with_answers(tmp_path, *, ad: str = "", version: str = TAG, lesson: bool = True) -> Any:
    paths = _vault(tmp_path, ad=ad, version=version)
    if lesson:
        _lesson(paths, "les_a", NODES)
    _sweep(paths)
    clock = MovableClock()  # the same instants in every vault, so the incumbent's numbers compare exactly
    for k, item in enumerate(ITEMS):
        clock.advance(3)
        answer(paths, item, correct=k != 1, clock=clock)
    return paths


def _snapshot(paths: Any, **settings: Any) -> RP.Snapshot:
    vault = load_vault(paths.root)
    RP.clear_cache()
    base = RP.ReplaySettings.from_config(vault.config)
    return RP.snapshot(vault, Repository(paths.sqlite_path), settings=replace(base, **settings))


def test_replay_equivalence_live_fresh_and_rebuilt(tmp_path):
    paths = _with_answers(tmp_path)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    settings = RP.ReplaySettings.from_config(vault.config)
    assert settings.lessons
    live = _snapshot(paths)
    assert sum(1 for e in live.events.opportunities if e.kind == "lesson") == 2
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        events = RP.load_events(connection, vault, repository, settings=settings)
    fresh = RP.run(events, settings)
    again = RP.run(events, settings)
    assert live.state_hash() == fresh.state_hash() == again.state_hash()
    assert RP.events_fingerprint(events) == RP.events_fingerprint(live.events)
    RP.rebuild(vault, repository)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        stored = connection.execute("SELECT state_hash, versions_json FROM ad_state WHERE view = ? AND part = 'summary'",
                                    (RP.VIEW_SUBJECT,)).fetchone()
    assert stored[0] == fresh.subject.bank.state_hash()
    assert json.loads(stored[1])["lesson_priors"] == P.LESSON_PRIORS_VERSION
    assert any(name.startswith("lesson:landed:") for name in fresh.subject.bank.names)


def test_switch_off_is_the_predecessor_exactly(tmp_path):
    """With the lesson rows recorded, the switch off (or the arm without lessons) reads none of them: the replay's
    events and state are those of a vault with no lesson at all, and the ad_state rows carry no lesson version."""

    on = _with_answers(tmp_path / "on")
    off_settings = replace(RP.ReplaySettings.from_config(load_vault(on.root).config), lessons=False)
    without = _snapshot(on, lessons=False)
    assert not any(e.kind == "lesson" for e in without.events.opportunities)
    stripped = RP.Events(without.events.attempts, without.events.claims,
                         [e for e in without.events.opportunities if e.kind != "lesson"], without.events.structure,
                         without.events.lo_subject, without.events.lo_facets)
    assert RP.run(stripped, off_settings).state_hash() == without.state_hash()
    assert not any(name.startswith("lesson:") for name in without.subject.bank.names)
    with_lessons = _snapshot(on)
    assert with_lessons.state_hash() != without.state_hash()
    # A vault that never had a lesson, at the tag and switch on, is exactly the predecessor's (the lazy coordinates).
    never = _with_answers(tmp_path / "never", lesson=False)
    old = _with_answers(tmp_path / "old", version=OLD, lesson=False)
    assert _snapshot(never).subject.bank.state_hash() == _snapshot(never, lessons=False).subject.bank.state_hash()
    assert _snapshot(never).subject.bank.names == _snapshot(old).subject.bank.names
    # The switch read from config: off at the tag reads nothing.
    switched = _with_answers(tmp_path / "switched", ad="lesson_opportunities = false\n")
    assert RP.ReplaySettings.from_config(load_vault(switched.root).config).lessons is False
    assert RP.ReplaySettings.from_config(load_vault(old.root).config).lessons is False


def _evidence(paths: Any) -> dict[str, Any]:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        out = {}
        for table in EVIDENCE:
            cursor = connection.execute(f"SELECT * FROM {table}")
            names = [d[0] for d in cursor.description]
            keep = [i for i, n in enumerate(names) if not (n == "id" or n.endswith("_id") and n not in (
                "practice_item_id", "learning_object_id", "facet_id", "criterion_id") or n.endswith("_at"))]
            out[table] = sorted((tuple(row[i] for i in keep) for row in cursor.fetchall()), key=repr)
    return out


def test_a_lesson_raises_the_prediction_and_never_evidence_or_mastery(tmp_path):
    on = _with_answers(tmp_path / "on")
    off = _with_answers(tmp_path / "off", ad="lesson_opportunities = false\n")
    assert _evidence(on) == _evidence(off)
    vault = load_vault(on.root)
    snap = _snapshot(on)
    item = vault.practice_items[ITEMS[0]]
    facet = sorted(item.evidence_facets or ())[0]
    spec = ItemSpec("x", LO, snap.events.lo_subject.get(LO, "default"), "retrieval", {facet: 1.0})
    with_lesson = snap.subject.prediction(spec)[0]
    without = _snapshot(on, lessons=False).subject.prediction(spec)[0]
    assert float(np.dot(snap.subject.bank.weights()[0], with_lesson - without)) != 0.0


def test_the_import_linter_contract_keeps_ad_off_evidence_writers():
    """§24: AD never writes evidence or mastery: the import-linter contract forbids the AD package (the lesson
    sweep included) importing the evidence writers, and the lesson module imports nothing of the teacher."""

    import ast
    import tomllib
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    contracts = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["importlinter"]["contracts"]
    contract = next(c for c in contracts if c.get("id") == "adaptive-difficulty-never-writes-evidence")
    assert contract["type"] == "forbidden" and contract["source_modules"] == ["learnloop.adaptive_difficulty"]
    assert {"learnloop.attempts", "learnloop.substrate", "learnloop.goals"} <= set(contract["forbidden_modules"])
    # TE3a adds no exception: the firewall's two carve-outs and the depth envelope's, as before.
    assert not any("lesson" in ignored for ignored in contract.get("ignore_imports") or [])
    tree = ast.parse((root / "src/learnloop/adaptive_difficulty/lessons.py").read_text(encoding="utf-8"))
    imported = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert not any(module.startswith(("learnloop.teacher", "learnloop.learner", "learnloop.attempts.attempts"))
                   for module in imported)


# -- the objective's lesson interface --------------------------------------------------------------------------------


def _inputs(learning: V.Learning) -> V.Inputs:
    return V.Inputs(
        topics=(V.Topic(lo="lo_a", eta_mean=0.3, eta_var=0.5, undated_density=0.02),
                V.Topic(lo="lo_b", eta_mean=-0.4, eta_var=1.0, undated_density=0.02)),
        dated=(V.DatedUse(goal_id="exam", lo="lo_a", at_days=6.0, weight=1.0),), session_minutes=10.0,
        price=V.Price(kappa0=0.01, remembered=20.0, remembered_source="test"),
        tail_block_minutes=10.0, tail_block_items=2, horizon_days=7.0,
        fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS),
        return_gaps_days=(1.0, 2.0), combiner=MEM.Combiner(), learning=learning)


def _prior_curve(positions: dict[str, float] | None = None) -> V.LessonCurve:
    prior = lesson_curve_moments(type("S", (), {"bank": M.Bank((P.LO_VIEW_POINT,))})())
    return V.LessonCurve(mean=tuple(prior["mean"]), cov=tuple(tuple(row) for row in prior["cov"]),
                         positions=positions or {}, version=prior["version"])


def _lesson_q(learning: V.Learning) -> tuple[float, tuple[float, ...]]:
    lesson = V.Action(ref="lesson", kind=V.LESSON, item_los=("lo_a", "lo_b"), minutes=15.0,
                      mass=P.LESSON_CHECK_MASS_PRIOR)
    block = V.Action(ref="practice", kind=V.NEW_PRACTICE, item_los=("lo_a",), minutes=10.0)
    out = V.evaluate(_inputs(learning), [lesson, block], draws=64, seed="te3a").by_ref()
    return out["lesson"].q, out["lesson"].q_draws


def test_at_the_seeded_prior_the_lesson_q_bar_equals_ro4s_placeholder():
    placeholder = V.Learning(gamma=(P.GAMMA_PRIOR[1], P.GAMMA_PRIOR[2]))
    curved = V.Learning(gamma=(P.GAMMA_PRIOR[1], P.GAMMA_PRIOR[2]), lesson=_prior_curve())
    q_placeholder, draws_placeholder = _lesson_q(placeholder)
    q_curve, draws_curve = _lesson_q(curved)
    assert q_curve == pytest.approx(q_placeholder, abs=1e-12)
    assert np.allclose(draws_curve, draws_placeholder, atol=1e-12, rtol=0.0)  # draw for draw
    # Off the prior the curve, not the placeholder, decides: a larger learned lesson effect raises the lesson's Q-bar.
    larger = V.Learning(gamma=(P.GAMMA_PRIOR[1], P.GAMMA_PRIOR[2]),
                        lesson=V.LessonCurve(mean=(0.6, 0.6), cov=((0.0, 0.0), (0.0, 0.0))))
    assert _lesson_q(larger)[0] > q_placeholder
    # A topic further along its lesson window takes a smaller step.
    far = V.Learning(gamma=(P.GAMMA_PRIOR[1], P.GAMMA_PRIOR[2]),
                     lesson=_prior_curve({"lo_a": 3.0, "lo_b": 3.0}))
    assert _lesson_q(far)[0] != pytest.approx(q_placeholder, abs=1e-9)


def test_the_objective_reads_the_curve_through_ads_entry_only_at_the_tag_with_the_switch_on(tmp_path):
    from learnloop.adaptive_difficulty.priors import DOSE_SCALES, GAMMA_PRIOR, READING_PRIORS
    from learnloop.daily_plan.objective_inputs import _learning

    for version, ad, expected in ((TAG, "", True), (TAG, "lesson_opportunities = false\n", False), (OLD, "", False)):
        paths = _vault(tmp_path / f"{version}-{bool(ad)}", version=version, ad=ad)
        vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
        fields = decision_state_fields(vault, repository, [LO], reading_doses=True, learning_moments=True)
        assert ("lesson_curve" in fields) is expected
        learning = _learning(fields, True, GAMMA_PRIOR, READING_PRIORS, DOSE_SCALES)
        if not expected:
            assert learning.lesson is None  # RO4's placeholder
            continue
        curve = fields["lesson_curve"]
        assert curve["source"] == "prior" and curve["version"] == P.LESSON_PRIORS_VERSION
        assert curve["positions"] == {LO: 0.0}
        assert learning.lesson is not None and learning.lesson.positions == {LO: 0.0}
        first = M.dose_increment(0.0, 1.0)
        assert first[0] * learning.lesson.mean[0] + first[1] * learning.lesson.mean[1] == pytest.approx(0.1, abs=1e-15)
        # fitted_models off (RO4's priors): the placeholder, whatever the switch says.
        assert _learning(fields, False, GAMMA_PRIOR, READING_PRIORS, DOSE_SCALES).lesson is None


def test_after_a_lesson_the_curve_the_objective_reads_has_the_topics_position(tmp_path):
    paths = _vault(tmp_path)
    _lesson(paths, "les_a", NODES)
    _sweep(paths)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    RP.clear_cache()
    fields = decision_state_fields(vault, repository, [LO], reading_doses=True, learning_moments=True)
    curve = fields["lesson_curve"]
    assert curve["source"] == "posterior" and curve["positions"][LO] == pytest.approx(2.0)


# -- the report's lesson row ---------------------------------------------------------------------------------------


def test_the_reports_lesson_row_at_the_prior_and_after_lessons(tmp_path):
    bank = M.Bank((P.LO_VIEW_POINT,), reading=True, verdict=True)
    row = DR.lesson_row(View(bank, subject_view=True, reading=True, lessons=True),
                        {"opportunities": {"landed": 0, "taught": 0}, "after_lesson": {"n": 0}})
    for subkind in P.LESSON_SUBKINDS:
        entry = row["subkinds"][subkind]
        assert entry["source"] == "prior" and entry["lessons"] == 0
        assert entry["first_dose_logit"]["median"] == pytest.approx(row["placeholder"]["logit"], abs=0.01)
        low, high = entry["first_dose_logit"]["ci90"]
        assert low < row["placeholder"]["logit"] < high
    assert len(row["lines"]) == 2 and all(DR.PRIOR_ONLY in line for line in row["lines"])

    paths = _with_answers(tmp_path)
    from learnloop.adaptive_difficulty import report as REPORT

    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    RP.clear_cache()
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        built = REPORT.build(vault, repository, connection, sensitivity=False, now="2026-11-06T12:00:00Z")
    lesson = built["dose_and_burden"]["lesson"]
    assert lesson["subkinds"]["landed"]["lessons"] == 1 and lesson["subkinds"]["taught"]["lessons"] == 1
    assert lesson["subkinds"]["landed"]["source"] == "posterior"
    assert any(line.startswith(DR.LESSON_NAME) for line in built["dose_and_burden"]["lines"])
    flags = {flag["flag"]: flag for flag in built["auto_flags"]}
    assert flags["lessons_worse_than_no_lessons"]["recommends"] == "lesson_opportunities = false"
    assert built["versions"]["lesson_priors"] == P.LESSON_PRIORS_VERSION

    off = _with_answers(tmp_path / "off", ad="lesson_opportunities = false\n")
    vault, repository = load_vault(off.root), Repository(off.sqlite_path)
    RP.clear_cache()
    with closing(connect(off.sqlite_path, read_only=True)) as connection:
        built = REPORT.build(vault, repository, connection, sensitivity=False, now="2026-11-06T12:00:00Z")
    assert "lesson" not in built["dose_and_burden"] and "lesson_priors" not in built["versions"]
    assert "lessons_worse_than_no_lessons" not in {flag["flag"] for flag in built["auto_flags"]}
