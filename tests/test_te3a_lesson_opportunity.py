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

import functools
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
from learnloop.algorithm_versions import LESSON_OPPORTUNITY_ALGORITHM_VERSION, TEACHER_PROBES_ALGORITHM_VERSION
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
OLD = TEACHER_PROBES_ALGORITHM_VERSION
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
            goal: dict[str, Any] | None = None, exposure: dict[str, Any] | None = None) -> None:
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
        if exposure is not None:
            receipt["exposure"] = exposure
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


def _exposure(*, shown: tuple[str, ...] = (), revealed: tuple[str, ...] = (),
              readings: list[dict[str, Any]] | None = None, passages: tuple[str, ...] = (),
              identities: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """A receipt's exposure; ``identities`` defaults to each exposed item's frozen identity with no sources (the fake
    items cite none), as the teacher's close records them since the re-review."""

    out: dict[str, Any] = {"reveals": [{"item_id": item, "kind": "tutor_answer", "amount": 1.0} for item in revealed],
                           "passages": list(passages), "shown_items": list(shown)}
    if readings is not None:
        out["readings"] = readings
    out["identities"] = identities if identities is not None else [
        {"practice_item_id": item, "keys": [], "whole": []} for item in sorted({*shown, *revealed})]
    return out


def test_codex_f1_a_lesson_whose_shown_items_or_passages_are_withheld_now_is_absent(tmp_path, monkeypatch):
    """Codex review F1: a closed lesson's receipt is judged against today's protection by what it showed (its shown and
    revealed items) and by the readings of the passages it delivered (``exposure.readings``); a receipt that names
    passages without their readings cannot be judged (withheld). An opportunity recorded before an item became
    protected is withheld from the replay afterwards (the receipt is resolved again by its rule)."""

    from learnloop.adaptive_difficulty import material_view as MV

    paths = _vault(tmp_path)
    landed = [{"id": "n1", "status": "landed"}]
    _lesson(paths, "les_shown", landed, exposure=_exposure(shown=("pi_exam",)))
    _lesson(paths, "les_revealed", landed, exposure=_exposure(revealed=("pi_exam_2",)))
    _lesson(paths, "les_legacy", landed, exposure=_exposure(passages=("S1",)))
    _lesson(paths, "les_reading", landed, exposure=_exposure(
        passages=("S1",), readings=[{"alias": "S1", "extraction_id": "ext_exam", "span_id": "b7"}]))
    _lesson(paths, "les_open", landed, exposure=_exposure(
        shown=(ITEMS[0],), passages=("S1",), readings=[{"alias": "S1", "extraction_id": "ext_open", "span_id": "b1"}]))
    withheld_items: set[str] = set()
    original_item, original_reading = MV.MaterialView.withheld, MV.MaterialView.reading_withheld
    monkeypatch.setattr(MV.MaterialView, "withheld",
                        lambda self, item: str(item) in withheld_items or original_item(self, item))
    monkeypatch.setattr(MV.MaterialView, "reading_withheld",
                        lambda self, extraction_id: str(extraction_id) == "ext_exam"
                        or original_reading(self, extraction_id))
    _sweep(paths)
    # Nothing protected yet but the exam reading: the shown and revealed lessons are recorded; the alias-only
    # receipt and the one whose passage reads the exam's extraction are not.
    assert [row["source_id"] for row in _opportunities(paths)] == ["les_open/n1", "les_revealed/n1", "les_shown/n1"]
    # The items become protected after the close: the recorded opportunities stop contributing.
    source = {row["id"]: row["source_id"] for row in _opportunities(paths)}
    assert sorted(source[e.opportunity_id] for e in _snapshot(paths).events.opportunities
                  if e.kind == "lesson") == ["les_open/n1", "les_revealed/n1", "les_shown/n1"]
    withheld_items.update({"pi_exam", "pi_exam_2"})
    assert sorted(source[e.opportunity_id] for e in _snapshot(paths).events.opportunities
                  if e.kind == "lesson") == ["les_open/n1"]


def test_codex_rereview_f1_a_lesson_is_judged_by_the_revision_it_showed_not_the_items_current_one(tmp_path,
                                                                                                    monkeypatch):
    """Codex re-review F1: a lesson showed an item's revision made from ``ext_old`` block b1; the item has since a
    public replacement (its current revision cites nothing protected) and b1 became protected. The receipt's frozen
    identity of the shown revision (``exposure.identities``, the AD serve's ``source_identity`` shape) is judged
    against today's protection, so the lesson is withheld though the item's current id is not; a receipt naming an
    exposed item without its identity cannot be judged (withheld, fail closed). The replay re-resolves it too."""

    from learnloop.adaptive_difficulty.protection import protection
    from learnloop.content.sources import exam_material

    paths = _vault(tmp_path)
    landed = [{"id": "n1", "status": "landed"}]
    old_revision = {"practice_item_id": ITEMS[0], "keys": [["ext_old", "b1"]], "whole": []}
    _lesson(paths, "les_old_revision", landed, exposure=_exposure(shown=(ITEMS[0],), identities=[old_revision]))
    _lesson(paths, "les_old_reveal", landed, exposure=_exposure(
        revealed=(ITEMS[0],), identities=[{**old_revision, "keys": [], "whole": ["ext_old_whole"]}]))
    _lesson(paths, "les_unidentified", landed, exposure=_exposure(shown=(ITEMS[1],), identities=[]))
    _lesson(paths, "les_open", landed, exposure=_exposure(shown=(ITEMS[2],), revealed=(ITEMS[0],)))
    held: dict[str, Any] = {"material": exam_material.Material()}
    monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: held["material"])
    _sweep(paths)
    assert [row["source_id"] for row in _opportunities(paths)] == ["les_old_reveal/n1", "les_old_revision/n1",
                                                                   "les_open/n1"]
    held["material"] = exam_material.Material(extractions=frozenset({"ext_old_whole"}),
                                              spans=frozenset({("ext_old", "b1")}))
    vault = load_vault(paths.root)
    now = protection(vault, Repository(paths.sqlite_path))
    assert ITEMS[0] not in now.ids  # the item's current revision is public: its id alone reads as visible
    assert now.covers_identity(old_revision)
    # The protection epoch moved, so the rows stamped before are stale; the sweep at the new epoch re-resolves each
    # receipt by its rule, and the replay reads only what that sweep recorded.
    _sweep(paths)
    source = {row["id"]: row["source_id"] for row in _opportunities(paths)}
    assert sorted(source[e.opportunity_id] for e in _snapshot(paths).events.opportunities
                  if e.kind == "lesson") == ["les_open/n1"]


def test_landing_r1_an_item_replaced_before_the_close_is_judged_by_the_revision_the_lesson_revealed(tmp_path,
                                                                                                   monkeypatch):
    """Landing ruling R1 (Codex final verify, F1 reopened): the lesson reveals ``pi_eig_1`` while its revision cites
    ``ext_old`` block b1; the item is replaced by a public revision BEFORE the lesson closes; the lesson closes; then
    b1 becomes protected. The identity is frozen when the lesson reveals the item (on the turn's record), so the
    receipt's ``exposure.identities`` holds the revealed revision's, and AD's guarded reader withholds the lesson
    (its current id reads as visible). On the close-time identity alone the receipt would be admitted."""

    from learnloop.adaptive_difficulty import material_view as MV
    from learnloop.adaptive_difficulty.protection import protection
    from learnloop.content.sources import exam_material
    from learnloop.teacher import service as S
    from learnloop.vault.yaml_io import read_yaml, write_yaml
    from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients, close_turn, plan_turn

    # No exam reservation: b1 is then the only protected material, so the control below isolates the frozen identity.
    paths, repository = build_teacher_vault(tmp_path / "vault", reserved=False)
    item_path = paths.practice_item_path("linear-algebra", "pi_eig_1")
    shown_revision = read_yaml(item_path)
    shown_revision["provenance"] = {"origin": "human", "source_refs": [{
        "ref_type": "canonical_source", "ref_id": "ext_old", "extraction_id": "ext_old", "span_ids": ["b1"]}]}
    write_yaml(item_path, shown_revision)
    # A teaching turn that partly reveals pi_eig_1's key (one word of five: below the key guard, above zero).
    fake = TeacherFake([plan_turn, {"message": "Picture a quokka scaling its own shadow: that is an eigenvalue."}])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
                payload={"text": "Go ahead."}, clients=clients(fake))
    with repository.connection() as connection:
        revealed = {row[0] for row in connection.execute(
            "SELECT practice_item_id FROM reveal_events WHERE basis = ? AND amount > 0",
            (f"lesson:{view['lesson_id']}",)).fetchall()}
    assert "pi_eig_1" in revealed
    # The public replacement, before the close.
    write_yaml(item_path, {**shown_revision, "provenance": {"origin": "human", "source_refs": []}})
    fake.turns = [close_turn()]
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
                payload={"text": "Thanks."}, clients=clients(fake))
    with repository.connection() as connection:
        receipt_json = connection.execute("SELECT receipt_json FROM lesson_receipts").fetchone()[0]
    identities = json.loads(receipt_json)["exposure"]["identities"]
    frozen = {"practice_item_id": "pi_eig_1", "keys": [["ext_old", "b1"]], "whole": []}
    assert frozen in identities, "the revealed revision's identity, frozen at the reveal"
    # b1 becomes protected after the close.
    monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: exam_material.Material(
        spans=frozenset({("ext_old", "b1")})))
    vault = load_vault(paths.root)
    now = protection(vault, repository)
    assert "pi_eig_1" not in now.ids  # the current revision is public: the id alone reads as visible
    material = MV.MaterialView(vault, repository, now)
    assert material._lesson_record_withheld({"receipt_json": receipt_json}, "receipt_json")
    with repository.connection() as connection:
        assert material.rows(connection, "lesson_receipts") == []
    # Control: the close-time identity alone (the reopened defect) would have admitted it.
    close_time = [entry for entry in identities if entry != frozen]
    receipt = json.loads(receipt_json)
    receipt["exposure"]["identities"] = close_time + [{"practice_item_id": "pi_eig_1", "keys": [], "whole": []}]
    assert not material._lesson_record_withheld({"receipt_json": json.dumps(receipt)}, "receipt_json")


def test_landing_r1_a_probe_lesson_freezes_every_display_and_its_receipt_is_judged_not_failed_closed(tmp_path):
    """Landing ruling R1 with TE2 (merged at TE3a's landing): every displayed record of a lesson with a probe carries
    its frozen identities, the served probe's ``probe_served`` included (its question is shown), so the receipt has
    ``identities`` (it does not fail closed on every probe lesson) and holds the served question's identity; AD's guard
    admits the lesson while nothing it exposed is protected and withholds it once the probe's item is."""

    from learnloop.adaptive_difficulty import material_view as MV
    from learnloop.adaptive_difficulty.protection import Protection
    from learnloop.content.sources import exam_material
    from learnloop.db.stores import lessons as store
    from learnloop.teacher import probes as PR
    from learnloop.teacher import service as S
    from tests.teacher_fakes import close_turn
    from tests.test_teacher_te2_probes import _Lesson, _probe, probe_turn

    lesson = _Lesson(tmp_path, [probe_turn])
    lesson.generate()
    probe = _probe(lesson)
    assert probe.status == "ready" and probe.item_id
    assert lesson.look()["probe"]["status"] == "open"  # served: its question is shown now
    lesson.act("answer_probe", {"answer": "(1, 0), stretched by three", "tap": 4}, turns=[close_turn()])
    assert lesson.view["closed"]
    with lesson.repository.connection() as connection:
        turns = store.turns(connection, lesson.lesson_id)
        receipt = json.loads(connection.execute("SELECT receipt_json FROM lesson_receipts").fetchone()[0])
    vault = lesson.vault()
    served = [entry for entry in turns if entry["action"] == PR.SERVED]
    assert len(served) == 1
    probe_identity = S._exposed_identities(vault, [probe.item_id])[0]
    assert served[0]["payload"][S.EXPOSURE_KEY] == [probe_identity]
    displayed = [entry for entry in turns if (entry["action"] == "teacher_turn" and entry["validation"] == "ok")
                 or (entry["action"] == "visual" and (entry["payload"] or {}).get("shown_text"))
                 or entry["action"] == PR.SERVED]
    assert len(displayed) >= 3 and all(isinstance(entry["payload"].get(S.EXPOSURE_KEY), list) for entry in displayed)
    identities = receipt["exposure"]["identities"]
    assert probe_identity in identities
    nothing = Protection(ids=frozenset(), material=exam_material.Material())
    assert not MV.MaterialView(vault, lesson.repository, nothing)._lesson_record_withheld(
        {"receipt_json": json.dumps(receipt)}, "receipt_json")
    held = Protection(ids=frozenset({probe.item_id}), material=exam_material.Material())
    assert MV.MaterialView(vault, lesson.repository, held)._lesson_record_withheld(
        {"receipt_json": json.dumps(receipt)}, "receipt_json")


def test_landing_r1_the_receipt_unions_frozen_identities_and_a_display_without_them_fails_closed():
    """Landing ruling R1: the receipt's identities are the union of each displayed record's frozen ones and the
    close's, deduplicated, in id order; a displayed record without frozen identities (shown before the rule) leaves
    the receipt without ``identities``, so AD reads every exposed item as unidentified (withheld)."""

    from types import SimpleNamespace

    from learnloop.teacher import service as S

    old = {"practice_item_id": "pi_a", "keys": [["ext_old", "b1"]], "whole": []}
    new = {"practice_item_id": "pi_a", "keys": [], "whole": []}
    other = {"practice_item_id": "pi_0", "keys": [], "whole": ["ext_w"]}
    turns = [{"action": "teacher_turn", "validation": "ok", "payload": {S.EXPOSURE_KEY: [old]}},
             {"action": "teacher_turn", "validation": "withheld", "payload": {}},  # never displayed
             {"action": "visual", "validation": "ok", "payload": {"shown_text": "a figure", S.EXPOSURE_KEY: [other, old]}},
             {"action": "visual", "validation": "ok", "payload": {"status": "failed"}},  # nothing shown
             {"action": "teacher_turn", "validation": "ok", "payload": {S.EXPOSURE_KEY: [new]}}]
    vault = SimpleNamespace(practice_items={})
    assert S._receipt_identities(vault, SimpleNamespace(turns=turns), ["pi_a"]) == {"identities": [other, old, new]}
    legacy = [*turns, {"action": "teacher_turn", "validation": "ok", "payload": {"turn": {}}}]
    assert S._receipt_identities(vault, SimpleNamespace(turns=legacy), ["pi_a"]) == {}
    # TE2's served probe is a displayed record too: frozen, it joins the union; without, the receipt fails closed.
    probe = {"action": "probe_served", "validation": "ok", "payload": {"probe_ref": "p1", S.EXPOSURE_KEY: [other]}}
    assert S._receipt_identities(vault, SimpleNamespace(turns=[*turns, probe]), ["pi_a"]) == {
        "identities": [other, old, new]}
    unfrozen = {"action": "probe_served", "validation": "ok", "payload": {"probe_ref": "p1"}}
    assert S._receipt_identities(vault, SimpleNamespace(turns=[*turns, unfrozen]), ["pi_a"]) == {}
    from learnloop.adaptive_difficulty.material_view import _lesson_exposure

    items, unresolved, identities = _lesson_exposure({"exposure": {"reveals": [{"item_id": "pi_a"}], "passages": []}})
    assert items == {"pi_a"} and unresolved and identities == []


def test_codex_f1_the_teachers_close_records_each_delivered_passages_reading(tmp_path):
    """Codex review F1: ``exposure.readings`` names each delivered passage's extraction and block (ids, no text), one
    per alias in ``exposure.passages``."""

    from learnloop.teacher import service as S
    from tests.teacher_fakes import TeacherFake, build_teacher_vault, check_turn, clients, landed_and_close_turn, \
        plan_turn

    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([plan_turn, check_turn()])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="reply",
                payload={"text": "Go ahead."}, clients=clients(fake))
    fake.turns = [landed_and_close_turn()]
    S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="answer_check",
                payload={"answer": "det(A - tI) = 0", "tap": 4}, clients=clients(fake))
    with repository.connection() as connection:
        receipt = json.loads(connection.execute("SELECT receipt_json FROM lesson_receipts").fetchone()[0])
    exposure = receipt["exposure"]
    assert exposure["passages"], "the fake library delivers passages"
    assert [entry["alias"] for entry in exposure["readings"]] == exposure["passages"]
    assert all(entry["extraction_id"] and entry["span_id"] and set(entry) == {"alias", "extraction_id", "span_id"}
               for entry in exposure["readings"])
    # Codex re-review F1: each exposed item's frozen revision identity, as AD's serve records one.
    from learnloop.adaptive_difficulty.outside import source_identity

    vault = load_vault(paths.root)
    exposed = sorted({entry["item_id"] for entry in exposure["reveals"]} | set(exposure["shown_items"]))
    assert exposed, "the fake lesson reveals its LO's items"
    assert exposure["identities"] == [source_identity(vault.practice_items[item]) for item in exposed]


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


#: The router follow-up batch's switches as the objective's inputs see them (landing at TE3a's merge): R9's AD link
#: with R10's latent posterior, R6's monotone combiner prior, and the merged sessions and consistent review draw.
FOLLOWUPS: dict[str, bool] = {"off": False, "on": True}


def _inputs(learning: V.Learning, *, followups: bool = False) -> V.Inputs:
    from learnloop.adaptive_difficulty import model as ADM

    link = V.AdLink(lapse=P.LAPSE, spread=P.A * P.TAU0, nodes=tuple(ADM.X32), weights=tuple(ADM.W32))
    return V.Inputs(
        topics=(V.Topic(lo="lo_a", eta_mean=0.3, eta_var=0.5, undated_density=0.02,
                        eta_latent=(0.35, 0.45) if followups else None),
                V.Topic(lo="lo_b", eta_mean=-0.4, eta_var=1.0, undated_density=0.02)),
        dated=(V.DatedUse(goal_id="exam", lo="lo_a", at_days=6.0, weight=1.0),), session_minutes=10.0,
        price=V.Price(kappa0=0.01, remembered=20.0, remembered_source="test"),
        tail_block_minutes=10.0, tail_block_items=2, horizon_days=7.0,
        fsrs_weights=tuple(FSRS6_DEFAULT_WEIGHTS),
        return_gaps_days=(1.0, 2.0), combiner=MEM.monotone_prior() if followups else MEM.Combiner(),
        learning=learning, ad_link=link if followups else None)


def _prior_curve(positions: dict[str, float] | None = None, *, mean: tuple[float, float] | None = None,
                 cov: Any = None) -> V.LessonCurve:
    """The seeded prior as AD's entry reads it (``mean``/``cov``: a posterior in its place, the prior kept)."""

    prior = lesson_curve_moments(type("S", (), {"bank": M.Bank((P.LO_VIEW_POINT,))})())
    prior_mean, prior_cov = tuple(prior["prior_mean"]), tuple(tuple(row) for row in prior["prior_cov"])
    assert prior_mean == tuple(prior["mean"]) and prior_cov == tuple(tuple(row) for row in prior["cov"])
    return V.LessonCurve(mean=mean or prior_mean, cov=cov or prior_cov, positions=positions or {},
                         version=prior["version"], prior_mean=prior_mean, prior_cov=prior_cov)


def _lesson_q(learning: V.Learning) -> tuple[float, tuple[float, ...]]:
    return _lesson_q_at(learning)


def _lesson_q_at(learning: V.Learning, *, followups: bool = False,
                 held: bool = False) -> tuple[float, tuple[float, ...]]:
    lesson = V.Action(ref="lesson", kind=V.LESSON, item_los=("lo_a", "lo_b"), minutes=15.0,
                      mass=P.LESSON_CHECK_MASS_PRIOR)
    block = V.Action(ref="practice", kind=V.NEW_PRACTICE, item_los=("lo_a",), minutes=10.0)
    out = V.evaluate(_inputs(learning, followups=followups), [lesson, block], draws=64, seed="te3a",
                     merged_sessions=followups, consistent_review_draw=followups, held_ad_link=held).by_ref()
    return out["lesson"].q, out["lesson"].q_draws


#: Router speed's ``held_ad_link`` (R9's link values held per role; landing at router speed's merge of TE3a): off,
#: the follow-up batch's landing code (a quadrature per read); on, the held values. It acts only with the link.
HELD: dict[str, bool] = {"held_off": False, "held_on": True}


@pytest.mark.parametrize("held", HELD.values(), ids=HELD.keys())
@pytest.mark.parametrize("followups", FOLLOWUPS.values(), ids=FOLLOWUPS.keys())
def test_at_the_seeded_prior_the_lesson_q_bar_equals_ro4s_placeholder(followups, held):
    """With every router follow-up switch off (TE3a's own read on ``logit p̄``) and on (the lesson curve read
    through AD's link on AD's latent ``η``, the monotone combiner, merged sessions, the consistent review draw), with
    router speed's held link off and on (at a fixed number of draws the same values, bit for bit)."""

    _lesson_q = functools.partial(_lesson_q_at, followups=followups, held=held)
    if held:
        for learning in (V.Learning(gamma=(P.GAMMA_PRIOR[1], P.GAMMA_PRIOR[2])),
                         V.Learning(gamma=(P.GAMMA_PRIOR[1], P.GAMMA_PRIOR[2]), lesson=_prior_curve(
                             {"lo_a": 1.0}, mean=(0.6, 0.6), cov=((0.0, 0.0), (0.0, 0.0))))):
            on, off = _lesson_q(learning), _lesson_q_at(learning, followups=followups, held=False)
            assert on[0] == off[0] and np.array_equal(on[1], off[1])
    placeholder = V.Learning(gamma=(P.GAMMA_PRIOR[1], P.GAMMA_PRIOR[2]))
    curved = V.Learning(gamma=(P.GAMMA_PRIOR[1], P.GAMMA_PRIOR[2]), lesson=_prior_curve())
    q_placeholder, draws_placeholder = _lesson_q(placeholder)
    q_curve, draws_curve = _lesson_q(curved)
    assert q_curve == pytest.approx(q_placeholder, abs=1e-12)
    assert np.allclose(draws_curve, draws_placeholder, atol=1e-12, rtol=0.0)  # draw for draw
    # Off the prior the curve's learned shift decides: a larger learned lesson effect raises the lesson's Q-bar.
    larger = V.Learning(gamma=(P.GAMMA_PRIOR[1], P.GAMMA_PRIOR[2]),
                        lesson=_prior_curve(mean=(0.6, 0.6), cov=((0.0, 0.0), (0.0, 0.0))))
    q_larger = _lesson_q(larger)[0]
    assert q_larger > q_placeholder
    # At the prior a topic's place on its lesson window moves nothing (Codex review F2); off it, a topic further
    # along takes a smaller learned shift (AD's window).
    far = V.Learning(gamma=(P.GAMMA_PRIOR[1], P.GAMMA_PRIOR[2]), lesson=_prior_curve({"lo_a": 3.0, "lo_b": 3.0}))
    assert np.array_equal(_lesson_q(far)[1], draws_placeholder)
    far_larger = V.Learning(gamma=(P.GAMMA_PRIOR[1], P.GAMMA_PRIOR[2]), lesson=_prior_curve(
        {"lo_a": 3.0, "lo_b": 3.0}, mean=(0.6, 0.6), cov=((0.0, 0.0), (0.0, 0.0))))
    assert q_placeholder < _lesson_q(far_larger)[0] < q_larger


def test_a_probe_closes_the_lesson_window_on_the_held_link_too():
    """Router speed's landing merge of TE3a: with the follow-up batch's AD link on, a probe's observation closes the
    topic's lesson window (TE3a, Codex review F3) on the held link's path as on the landing code's, so a lesson, a
    probe and a lesson on one topic value the same, bit for bit, with ``held_ad_link`` on and off. Off the prior, so
    the window's place moves the second lesson's learned shift."""

    learning = V.Learning(gamma=(P.GAMMA_PRIOR[1], P.GAMMA_PRIOR[2]), lesson=_prior_curve(
        {"lo_a": 0.0}, mean=(0.6, 0.6), cov=((0.0, 0.0), (0.0, 0.0))))
    lesson = V.Action(ref="lesson", kind=V.LESSON, item_los=("lo_a",), minutes=5.0, mass=P.LESSON_CHECK_MASS_PRIOR)
    probe = V.Action(ref="probe", kind=V.PROBE, item_los=("lo_a",), minutes=3.0)
    sequence = V.Action(ref="seq", kind=V.SEQUENCE, steps=(replace(lesson, ref="s1"), replace(probe, ref="s2"),
                                                          replace(lesson, ref="s3")))
    block = V.Action(ref="practice", kind=V.NEW_PRACTICE, item_los=("lo_a",), minutes=10.0)
    values = {}
    for held in (False, True):
        out = V.evaluate(_inputs(learning, followups=True), [sequence, block], draws=64, seed="te3a-window",
                         merged_sessions=True, consistent_review_draw=True, held_ad_link=held).by_ref()
        values[held] = (out["seq"].q, out["seq"].q_draws)
    assert values[True][0] == values[False][0]
    assert np.array_equal(values[True][1], values[False][1])


def _f2_choice(learning: V.Learning, *, mass: float) -> tuple[dict[str, V.Valued], str]:
    """Codex review F2's case: practised topics, equal one-minute lesson and practice actions on ``lo_a``."""

    inputs = _inputs(learning)
    inputs = replace(inputs, topics=tuple(replace(topic, practiced=True, stability=3.0, elapsed_days=1.0)
                                          for topic in inputs.topics))
    lesson = V.Action(ref="lesson", kind=V.LESSON, item_los=("lo_a",), minutes=1.0, mass=mass)
    practice = V.Action(ref="practice", kind=V.REVIEW, item_los=("lo_a",), minutes=1.0)
    out = V.evaluate(inputs, [lesson, practice], draws=64, seed="te3a-f2").by_ref()
    return out, max(("lesson", "practice"), key=lambda ref: out[ref].q)


@pytest.mark.parametrize("mass", [P.LESSON_CHECK_MASS_PRIOR, 0.8])
@pytest.mark.parametrize("positions", [{}, {"lo_a": 1.0}])
def test_codex_f2_with_fitted_practice_parameters_the_untouched_lesson_curve_moves_no_decision(mass, positions):
    """Codex review F2: ordinary practice has fitted ``γ`` (moments (0.05, 0.01)) and no lesson has informed the
    lesson curve (its coefficients at their seeded prior). The lesson's value is then RO4's placeholder at the fitted
    ``γ`` and the lesson's learned mass, draw for draw, whatever the topic's place on its lesson window: no decision
    moves. (Before the fix the curve stood in for the placeholder centred on ``γ``'s *prior*, and the lesson won.)"""

    fitted = (0.05, 0.01)
    placeholder, chose_placeholder = _f2_choice(V.Learning(gamma=fitted), mass=mass)
    curved, chose_curve = _f2_choice(V.Learning(gamma=fitted, lesson=_prior_curve(positions)), mass=mass)
    assert chose_curve == chose_placeholder
    for ref in ("lesson", "practice"):
        assert curved[ref].q == placeholder[ref].q
        assert np.array_equal(curved[ref].q_draws, placeholder[ref].q_draws)


def _ad_lesson_steps(sequence: str, coefficients: tuple[float, float]) -> list[float]:
    """The oracle: AD's own transition (``View.reading`` on the lesson window, ``close_windows`` for a graded
    attempt) with the ``landed`` coefficients' means set to ``coefficients``: each lesson's step on the facet."""

    view = _view(lessons=True)
    spec = _spec()
    view.ensure(spec, 0.0)
    view.bank.ensure_lessons()
    for m in (1, 2):
        view.bank.mu[:, view.bank.index[P.lesson_coordinate("landed", m)]] = coefficients[m - 1]
    steps = []
    for step in sequence:
        if step == "L":
            before = float(view.prediction(spec)[0][0])
            view.reading("s", "lesson", {"f0": 1.0}, 0.0, subkind="landed")
            steps.append(float(view.prediction(spec)[0][0]) - before)
        else:
            view.close_windows(("f0",))
    return steps


def _objective_lesson_steps(sequence: str, learning: V.Learning) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """The objective's rollout state through ``sequence`` on ``lo_a`` (``L`` a lesson, ``P`` a graded practice
    attempt, ``B`` a probe): each lesson's step on the belief and on the true ability, per draw."""

    model = V._Model(_inputs(learning), 32, "te3a-f3")
    state = model.initial()
    everyone, at = np.ones(model.k, dtype=bool), np.zeros(model.k)
    lesson = V.Action(ref="lesson", kind=V.LESSON, item_los=("lo_a",), minutes=15.0, mass=P.LESSON_CHECK_MASS_PRIOR)
    practice = V.Action(ref="practice", kind=V.REVIEW, item_los=("lo_a",), minutes=10.0)
    believed, true = [], []
    for step in sequence:
        if step == "L":
            bel, eta = state.bel[:, 0].copy(), state.eta[:, 0].copy()
            model.apply(state, lesson, at, everyone)
            believed.append(state.bel[:, 0] - bel)
            true.append(state.eta[:, 0] - eta)
        elif step == "P":
            model.apply(state, practice, at, everyone)
        else:
            model._observe(state, 0, model.streams.action_u[:, 0, 0], everyone)
    return believed, true


@pytest.mark.parametrize("sequence", ["LL", "LPL", "LBL", "LLPL"])
def test_codex_f3_rollouts_carry_the_lesson_window_as_ads_transition_does(sequence):
    """Codex review F3: a rollout's lessons advance the topic's lesson window and a graded attempt (practice or probe)
    resets it, as AD's transition does. The learned part of each lesson step (the curve's shift from its seeded prior,
    added to RO4's placeholder) equals AD's step with the learned coefficients minus AD's step with the prior ones,
    lesson by lesson; at the seeded prior every step is the placeholder's (the spec's neutrality, §14.2)."""

    gm = P.GAMMA_PRIOR[1]
    placeholder = gm * P.LESSON_CHECK_MASS_PRIOR
    prior = _prior_curve()
    posterior = (prior.prior_mean[0] + 0.3, prior.prior_mean[1] - 0.05)
    learned = V.Learning(gamma=(gm, P.GAMMA_PRIOR[2]), lesson=_prior_curve(mean=posterior, cov=prior.prior_cov))
    believed, _true = _objective_lesson_steps(sequence, learned)
    oracle = [post - pri for post, pri in zip(_ad_lesson_steps(sequence, posterior),
                                              _ad_lesson_steps(sequence, prior.prior_mean), strict=True)]
    assert len(believed) == len(oracle) == sequence.count("L")
    for step, expected in zip(believed, oracle, strict=True):
        assert np.allclose(step, placeholder + expected, atol=1e-12, rtol=0.0)
    # The window moved: a second consecutive lesson's learned shift is AD's second-dose one, not a first dose again;
    # after a graded attempt the window is closed and the next lesson is a first dose.
    if sequence.startswith("LL"):
        assert oracle[1] < oracle[0]
    else:
        assert oracle[1] == pytest.approx(oracle[0], abs=1e-15)
    if sequence == "LLPL":
        assert oracle[2] == pytest.approx(oracle[0], abs=1e-15)
    # At the seeded prior (positions anywhere) every lesson step is the placeholder's, on the belief and draw for draw.
    at_prior = V.Learning(gamma=(gm, P.GAMMA_PRIOR[2]), lesson=_prior_curve({"lo_a": 2.0}))
    believed_prior, true_prior = _objective_lesson_steps(sequence, at_prior)
    believed_off, true_off = _objective_lesson_steps(sequence, V.Learning(gamma=(gm, P.GAMMA_PRIOR[2])))
    for a, b in zip(believed_prior + true_prior, believed_off + true_off, strict=True):
        assert np.array_equal(a, b)


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
