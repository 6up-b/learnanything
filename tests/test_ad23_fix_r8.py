"""Adaptive difficulty AD2+AD3, fix round 8: one protected material view for AD (spec A8; Codex
verify 20261019-215812-pCHeIT, F19-F27; docs/reviews/adaptive-difficulty-ad23-codex-review.md).

One regression per reproduction of the verify, through the public paths where one exists:

* F19: the replay's and the Reader map's facet maps and item lookups name nothing only a withheld
  item names, and an LO claim no longer moves a forecast through a withheld item's facet;
* F20: an attempt on held-out material warms nothing and is invisible to the replay (no window
  closed, no first surface); a reading receipt whose source is held out now is not replayed;
* F21: under the generation contract the targets' counts, facets and surface families exclude a
  withheld item (the predecessor's, with the contract off);
* F22: AD's protection does not depend on ``goals.held_out_selection``, and a predicate that raises
  makes AD unavailable for the slot, never an exception (the incumbent serves);
* F23: the dose arm never offers or returns a held-out Reader question;
* F24: the challenger's history and ``z_v1``'s calibration never read a withheld item;
* F25: report sensitivity never re-forecasts a withheld item, and says how many it left out;
* F26: the dose moderator's window closes only at a visible graded attempt;
* F27: practice minutes come from the visible practice cohort;
* the degradations with the predicate unavailable (selection, generation, report, dose).

Fakes only: no network, no model call, no paid call.
"""

from __future__ import annotations

import json
from contextlib import closing
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty import report as REP
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import ad_receipts
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import LO, SEEDED, ad23_vault, ad_epoch, answer, env_for, restamp, rows, selections, set_item
from tests.daily_plan_fakes import iso

ROUTER_OFF = "[router]\nenabled = false\n"
EXTRACTION = "ext_r8"


def _derived(paths, item_id: str, span: str) -> None:
    """The item is made from a span of ``EXTRACTION`` (its canonical exercise)."""

    set_item(paths, item_id, canonical_exercise={"source_id": "src_r8", "extraction_id": EXTRACTION,
                                                 "span_ids": [span]})


def _hold_out(monkeypatch, *spans: str) -> None:
    """From now on the held-out predicate covers these spans of ``EXTRACTION``."""

    from learnloop.content.sources import exam_material

    material = exam_material.Material(spans=frozenset((EXTRACTION, span) for span in spans))
    monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: material)


def _predicate_raises(monkeypatch) -> None:
    from learnloop.content.sources import exam_material

    def broken(*_args, **_kwargs):
        raise RuntimeError("held-out source sets unreadable")

    monkeypatch.setattr(exam_material, "held_out_material", broken)


def _reserve(monkeypatch, *item_ids: str) -> None:
    monkeypatch.setattr(Repository, "reserved_exam_pool_item_ids", lambda _self: list(item_ids))


def _attempt(paths, item_id: str, *, at: datetime, latency: int | None = None, session: str | None = "s1",
             presentation_id: str | None = None, correct: bool = True) -> str:
    vault = load_vault(paths.root)
    draft = AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer.", latency_seconds=latency,
                         session_id=session, plan_presentation_id=presentation_id)
    grade = SelfGradeInput(criterion_points={"correctness": 4.0 if correct else 0.0}, confidence=4)
    return str(complete_self_graded_attempt(vault, Repository(paths.sqlite_path), draft, grade,
                                            clock=FrozenClock(at)).attempt_id)


def _events(paths) -> Any:
    vault = load_vault(paths.root)
    RP.clear_cache()
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return RP.load_events(connection, vault, Repository(paths.sqlite_path))


# -- F19: facet maps and item lookups ----------------------------------------------------------------


def _secret_vault(tmp_path, *, with_secret: bool = True):
    """LO ``lo_x`` has no authored facets; its one item ``pi_secret`` (facet ``secret``) is held out.
    The open item ``pi_open`` of the main LO measures ``secret`` too."""

    paths = ad23_vault(tmp_path, items=("pi_open",), learning_objects={"lo_x": ("pi_secret",)}, config=ROUTER_OFF)
    set_item(paths, "pi_open", evidence_facets=["secret"], evidence_weights={"secret": 1.0})
    set_item(paths, "pi_secret", evidence_facets=["secret"], evidence_weights={"secret": 1.0})
    if not with_secret:
        paths.practice_item_path("linear-algebra", "pi_secret").unlink()
    else:
        _derived(paths, "pi_secret", "held")
    Repository(paths.sqlite_path).insert_learner_claim({
        "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": "lo_x", "claimed_level": 0.9,
        "prior_pseudo_count": 2.0, "source": "tutor_gap_declaration", "created_at": "2026-10-01T09:00:00Z"})
    return paths


def test_a_withheld_items_facet_never_enters_the_facet_maps_or_the_reading_map(tmp_path, monkeypatch):
    """F19: ``lo_x``'s only facet comes from a held-out item: the replay's LO -> facet map and the
    Reader map give it none, the Reader map maps the item to no LO (an owner-placed or tutor
    question on it is no opportunity), and a reading dose on ``lo_x`` names no facet. Failed before:
    ``['secret']``, ``'lo_x'`` and ``{'secret': 1.0}``."""

    from learnloop.adaptive_difficulty.reading import VaultReadingMap, _doses

    paths = _secret_vault(tmp_path)
    _hold_out(monkeypatch, "held")
    assert _events(paths).lo_facets.get("lo_x") == []
    from learnloop.adaptive_difficulty.operation import ad_operation

    with ad_operation(load_vault(paths.root), Repository(paths.sqlite_path)) as op:
        mapping = VaultReadingMap(op.vault, op.repository)
        assert mapping.facets_for_lo("lo_x") == []
        assert mapping.lo_for_item("pi_secret") is None and mapping.lo_for_item("pi_open") == LO
        assert _doses(mapping, "lo_x", ()) == {}


def test_a_claim_moves_no_forecast_through_a_withheld_items_facet(tmp_path, monkeypatch):
    """F19 (the verify's forecast): a 0.9 claim on ``lo_x``, whose facet only the held-out item
    names, leaves the open item's cell forecast exactly as if the held-out item were not in the vault
    at all: 0.49 (failed before: 0.7807798714, the verify's figure: the claim reached ``secret``
    through the held-out item and raised the forecast)."""

    from learnloop.adaptive_difficulty import predict as PR
    from learnloop.adaptive_difficulty import selection as S

    def forecast(paths) -> float:
        vault = load_vault(paths.root)
        RP.clear_cache()
        snapshot = RP.snapshot(vault, Repository(paths.sqlite_path))
        point = S.entry_point("retrieval") or {}
        spec = PR.point_spec(point, learning_object_id=LO, subject="linear-algebra", facet="secret",
                             capability_name="retrieval")
        return PR.predict(snapshot.subject, spec).p_bar

    held = _secret_vault(tmp_path / "held")
    absent = _secret_vault(tmp_path / "absent", with_secret=False)
    _hold_out(monkeypatch, "held")
    assert forecast(absent) == pytest.approx(0.49, abs=1e-8)
    assert forecast(held) == pytest.approx(forecast(absent), abs=1e-12)


# -- F20: warmth, replay visibility, replayed receipts -------------------------------------------------


def _warm_vault(tmp_path):
    paths = ad23_vault(tmp_path, items=("pi_open", "pi_h"), config=ROUTER_OFF)
    _derived(paths, "pi_h", "held")
    return paths


def test_an_attempt_on_held_out_material_warms_nothing_and_is_invisible_to_the_replay(tmp_path, monkeypatch):
    """F20: an answer on ``pi_h`` one hour before the open item is served, then ``pi_h``'s source is
    held out. The serve's ``ad_threshold@subject`` warmth is 0 (failed before: 0.8465), and the
    replay has no event for that attempt at all (it closes no reading window and takes no first
    surface; before, it was an excluded ``held_out`` event that still closed windows)."""

    paths = _warm_vault(tmp_path)
    env, clock = env_for(paths, items=("pi_open",))
    _attempt(paths, "pi_h", at=clock.now() - timedelta(hours=1))
    _hold_out(monkeypatch, "held")
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item" and step["practice_item_id"] == "pi_open"
    (receipt,) = rows(paths.sqlite_path, "SELECT inputs_json FROM forecast_receipts WHERE forecaster = "
                                         "'ad_threshold@subject' AND plan_presentation_id = ?", (step["presentation_id"],))
    assert json.loads(receipt["inputs_json"])["warmth"] == 0.0
    assert all(event.practice_item_id != "pi_h" for event in _events(paths).attempts)


def test_a_reading_receipt_whose_source_is_held_out_now_is_not_replayed(tmp_path, monkeypatch):
    """F20: receipts are revalidated against the current predicate before the replay reads them. Since
    the AD23 redesign's round 2 a receipt is read only at the protection epoch it was recorded under,
    so holding a span out first takes every earlier receipt out of force (E2: it is swept again);
    a receipt of the current epoch whose source is withheld is still not replayed. Since round 8
    (Option B) the held span's whole reading is absent for reading signals, so its other receipt
    (on a public span) is not replayed either."""

    paths = ad23_vault(tmp_path, items=("pi_open",), config=ROUTER_OFF)

    def record(epoch: str | None, suffix: str = "") -> None:
        with closing(connect(paths.sqlite_path)) as connection:
            for span in ("open_span", "held"):
                ad_receipts.insert_reading_opportunity(connection, {
                    "protection_epoch": epoch,
                    "opportunity_key": f"worked_example:{EXTRACTION}/{span}:{LO}{suffix}", "kind": "worked_example",
                    "subkind": "in_completed_section", "source_table": "reader_section_progress",
                    "source_id": f"{EXTRACTION}/{span}", "source_written_at": "2026-10-01T09:00:00Z",
                    "learning_object_id": LO, "facet_doses": {"recall": 1.0}, "dose_offer_id": None,
                    "mapping_version": "ad_reading_map_v1", "sweep": "backfill", "sweep_ref": None,
                    "swept_at": "2026-10-01T09:00:00Z"})
            connection.commit()

    record(ad_epoch(paths))
    assert len(_events(paths).opportunities) == 2
    _hold_out(monkeypatch, "held")
    assert _events(paths).opportunities == [], "another epoch's receipts are out of force"
    record(ad_epoch(paths))
    assert _events(paths).opportunities == [], "the reading the held span is in is absent (Option B)"
    assert rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM ad_reading_opportunities")[0]["n"] == 4  # frozen


# -- F21: generation target metadata ------------------------------------------------------------------


def _target(paths) -> Any:
    from learnloop.content.authoring.practice_generation import (
        _practice_expansion_instructions,
        build_practice_expansion_plan,
    )

    vault = load_vault(paths.root)
    plan = build_practice_expansion_plan(vault, Repository(paths.sqlite_path), learning_object_ids=[LO],
                                         require_completed_probe=False)
    (target,) = plan.targets
    return target, json.dumps(target.as_dict()) + _practice_expansion_instructions(plan, extra_instructions=None)


def _sentinel_vault(tmp_path, *, ad: str = ""):
    paths = ad23_vault(tmp_path, items=("pi_g1", "pi_s1"), config=ROUTER_OFF, ad=ad)
    set_item(paths, "pi_s1", evidence_facets=["HELD_SENTINEL"], evidence_weights={"HELD_SENTINEL": 1.0},
             surface_family="HELD_FAMILY")
    _derived(paths, "pi_s1", "held")
    return paths


def test_a_withheld_items_metadata_never_reaches_an_ad_generation_target(tmp_path, monkeypatch):
    """F21: under the generation contract the LO's target counts one existing item and names
    neither ``HELD_SENTINEL`` nor ``HELD_FAMILY`` (failed before: 2 items, both named, in the
    ``Targets:`` payload). With the contract off the predecessor's target is unchanged."""

    _hold_out(monkeypatch, "held")
    target, text = _target(_sentinel_vault(tmp_path / "on"))
    assert target.ad_commission_id is not None
    assert target.existing_practice_items == 1
    assert "HELD_SENTINEL" not in target.existing_evidence_facets and "HELD_SENTINEL" not in text
    assert "HELD_FAMILY" not in target.existing_surface_families and "HELD_FAMILY" not in text
    off, _text = _target(_sentinel_vault(tmp_path / "off", ad="generation_contract = false\n"))
    assert off.ad_commission_id is None and off.existing_practice_items == 2
    assert "HELD_SENTINEL" in off.existing_evidence_facets and "HELD_FAMILY" in off.existing_surface_families


# -- F22: selection's protection is unconditional and fails closed ---------------------------------------


def _slot_vault(tmp_path):
    from tests.test_ad2_serving import HARD

    items = ("pi_a", "pi_held")
    paths = ad23_vault(tmp_path, items=items, features={"pi_a": HARD}, config=ROUTER_OFF)
    _derived(paths, "pi_held", "held")
    return paths, items


def test_ad_selection_withholds_held_out_material_with_held_out_selection_off(tmp_path, monkeypatch):
    """F22: with ``goals.held_out_selection = false`` the routine exclusions name no held-out item,
    but AD's draw never has ``pi_held`` in its support and never serves it (failed before: the
    eligibility checks passed it)."""

    paths, items = _slot_vault(tmp_path)
    _hold_out(monkeypatch, "held")
    env, clock = env_for(paths, items=items)
    env.vault.config.goals.held_out_selection = False
    build_plan(env, kind="normal", budget=6.0, remembered=6, minutes_source="chip")
    served = []
    for _ in range(4):
        _record, step = advance(env, serve=True)
        if step["kind"] != "item":
            break
        served.append(step["practice_item_id"])
        clock.advance(2)
        answer(paths, step["practice_item_id"], correct=True, presentation_id=step["presentation_id"], clock=clock)
        clock.advance(1)
    draws = selections(paths, kind="serve")
    assert draws, "AD drew the slot"
    assert all(entry["ref"] != "pi_held" for row in draws for entry in row["support"])
    assert all(row.get("chosen_item_id") != "pi_held" for row in draws) and "pi_held" not in served
    for row in draws:
        failed = {entry["ref"]: entry["failed"] for entry in row["excluded"]}
        # Withheld as a slot (no candidate at all) or as a candidate (``held_out``).
        assert (row["slot_item_id"] == "pi_held" and row["empty_support"]) or "held_out" in failed.get(
            "pi_held", ["held_out"])


def test_an_unreadable_predicate_makes_ad_unavailable_and_the_incumbent_serves(tmp_path, monkeypatch):
    """F22 (and the selection degradation): the held-out predicate raises at the serve. AD writes
    no draw and the planned item is served as the incumbent serves it; no exception reaches the
    caller (failed before: ``RuntimeError`` out of the serve)."""

    paths, items = _slot_vault(tmp_path)
    env, _clock = env_for(paths, items=items)
    record = build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    planned = [item.practice_item_id for item in record.items()]
    _predicate_raises(monkeypatch)
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item" and step["practice_item_id"] == planned[0]
    assert selections(paths) == []


# -- F23: the dose arm never offers a held-out question -------------------------------------------------


def test_the_dose_arm_never_offers_or_returns_a_held_out_question(tmp_path, monkeypatch):
    """F23: a produced, unanswered question anchored on a span that is held out now is not a
    feasible extra (failed before: ``extra_question`` with ``q_held``), and an earlier draw that
    chose it returns no offer (``withheld``)."""

    from learnloop.adaptive_difficulty import dose as D
    from learnloop.content.sources import exam_material
    from learnloop.db.stores import ad_serving

    from tests.test_ad1_reading_opportunities import _question, at
    from tests.test_ad3_dose_arm import _arm, _boundary, _mapping

    paths, vault, repo = _arm(tmp_path)
    question = _question(repo, "recall", 1, answer=False)
    material = exam_material.Material(spans=frozenset({("ext1", "s1")}))
    monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: material)
    with closing(connect(paths.sqlite_path)) as connection:
        feasible, infeasible, content = D.feasible_variants(vault, repo, connection, _boundary(), ["lo_svd_definition"],
                                                            reading_map=_mapping())
    assert D.EXTRA_QUESTION not in feasible and infeasible[D.EXTRA_QUESTION] == "no_producer_result"
    with closing(connect(paths.sqlite_path)) as connection:
        ad_serving.insert_dose_row(connection, {
            "row_kind": "draw", "draw_key": "visit9:ext1:u1", "visit_id": "visit9", "extraction_id": "ext1",
            "section_id": "u1", "learning_object_ids": ["lo_svd_definition"], "feasible": ["none", D.EXTRA_QUESTION],
            "infeasible": {}, "base_version": D.BASE_VERSION, "floor": 0.1,
            "propensities": {"none": 0.9, D.EXTRA_QUESTION: 0.1}, "seed": "s", "u": 0.95,
            "chosen_variant": D.EXTRA_QUESTION, "content": {"question_id": question, "style": "recall"},
            "forecast_p": None, "detail": {}, "created_at": "2026-10-12T09:00:00Z"})
        connection.commit()
    decision = D.decide(vault, repo, _boundary(visit="visit9"), clock=at(5), reading_map=_mapping())
    assert decision.reason == "withheld" and decision.as_dict()["offer"] is None


# -- F24: forecast and calibration history ------------------------------------------------------------


def test_the_challengers_history_never_reads_a_withheld_items_answer(tmp_path, monkeypatch):
    """F24: the serve-time challenger (``lo_general+composite``) rebuilds on the view's rows: an
    earlier answer on ``pi_h``, whose source is held out now, is not among them (failed before: the
    observation spy saw it)."""

    import learnloop.field.predictors as predictors

    paths = _warm_vault(tmp_path)
    env, clock = env_for(paths, items=("pi_open",))
    attempt = _attempt(paths, "pi_h", at=clock.now() - timedelta(hours=3))
    _hold_out(monkeypatch, "held")
    seen: list[str] = []
    real = predictors.create_predictor

    def create(name, **kwargs):
        predictor = real(name, **kwargs)
        rebuild = predictor.rebuild

        def spy(rows_):
            rows_ = list(rows_)
            seen.extend(row.attempt_id for row in rows_)
            return rebuild(rows_)

        predictor.rebuild = spy
        return predictor

    monkeypatch.setattr(predictors, "create_predictor", create)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    _record, step = advance(env, serve=True)
    assert step["practice_item_id"] == "pi_open"
    assert attempt not in seen
    assert rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM forecast_receipts WHERE forecaster = "
                                   "'lo_general+composite'")[0]["n"] == 1


def test_z_v1_calibration_never_reads_a_withheld_items_forecast(tmp_path, monkeypatch):
    """F24 (the verify's fit): an ``llm_v1:item`` forecast for ``pi_x`` and its answered first
    presentation, then ``pi_x`` is reserved for an exam. A later serve's ``z_v1`` recalibration fits
    on nothing (``n = 0``; failed before: ``n = 1``)."""

    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.adaptive_difficulty.outside import _receipt
    from learnloop.adaptive_difficulty.switches import LLM_V1
    from learnloop.scheduling.forecast_receipts import record_receipts

    paths = ad23_vault(tmp_path, items=("pi_x", "pi_y", "pi_z"), config=ROUTER_OFF)
    env, clock = env_for(paths, items=("pi_x",))
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    _record, step = advance(env, serve=True)
    assert step["practice_item_id"] == "pi_x"
    forecast_at = iso(clock.now() - timedelta(minutes=30))
    clock.advance(2)
    answer(paths, "pi_x", correct=True, presentation_id=step["presentation_id"], clock=clock)
    content_hash = item_revision(load_vault(paths.root).practice_items["pi_x"])[0]
    from dataclasses import replace

    receipt = _receipt(
        key=f"llm_v1:{content_hash}", forecaster=LLM_V1, version="v1", scope="item", decision_kind="item_prepare",
        binding_kind="first_presentation", inputs={}, inputs_as_of=forecast_at, p=0.8, status="ok",
        received_at=forecast_at, model="fake", request_hash="h",
        columns={"practice_item_id": "pi_x", "learning_object_id": LO, "item_content_hash": content_hash,
                 "decision_ref": content_hash})
    # Written by AD at the current protection epoch, as AD stamps every forecast (round 2).
    receipt = replace(receipt, versions={**dict(receipt.versions), "protection_epoch": ad_epoch(paths)})
    record_receipts(Repository(paths.sqlite_path), [receipt], created_at=forecast_at)

    def later_n(item_id: str, session: str) -> int:
        clock.advance(60 * 24)
        env2, _ = env_for(paths, items=(item_id,), clock=clock, session=session)
        build_plan(env2, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
        _r, served = advance(env2, serve=True)
        assert served["practice_item_id"] == item_id
        (row,) = rows(paths.sqlite_path, "SELECT signals_json FROM item_serve_inputs WHERE plan_presentation_id = ?",
                      (served["presentation_id"],))
        return int(json.loads(row["signals_json"])["z_v1"]["recalibration"]["n"])

    assert later_n("pi_y", "s2") == 1  # while pi_x is open, its forecast and answer are one observation
    _reserve(monkeypatch, "pi_x")
    assert later_n("pi_z", "s3") == 0


# -- F25: report sensitivity ----------------------------------------------------------------------------


def test_report_sensitivity_never_re_forecasts_a_withheld_item(tmp_path, monkeypatch):
    """F25: a serve draw logged while its support was open; one support member is reserved for an
    exam afterwards. The report's sensitivity never asks for its forecast and says how many support
    members it left out (failed before: the spy saw it)."""

    from learnloop.adaptive_difficulty import predict as PR

    from tests.test_ad2_serving import HARD

    items = ("pi_h1", "pi_e1", "pi_e2")
    paths = ad23_vault(tmp_path, items=items, features={"pi_h1": HARD}, config=ROUTER_OFF)
    env, _clock = env_for(paths, items=items)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    advance(env, serve=True)
    (draw,) = selections(paths, kind="serve")
    refs = [entry["ref"] for entry in draw["support"]]
    assert len(refs) >= 2
    # A support member that is neither the draw's choice nor its slot's item: reserving either of
    # those leaves the whole draw out of the report's cohort (fix round 12, F39).
    refs = [ref for ref in refs if ref not in (draw.get("chosen_item_id"), draw.get("slot_item_id"))] + refs
    _reserve(monkeypatch, refs[0])
    seen: list[str] = []
    real = PR.current_spec

    def spy(vault, connection, item, **kwargs):
        seen.append(str(item.id))
        return real(vault, connection, item, **kwargs)

    monkeypatch.setattr(PR, "current_spec", spy)
    RP.clear_cache()
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        report = REP.build(load_vault(paths.root), Repository(paths.sqlite_path), connection, sensitivity=True)
    # Since the AD23 redesign's round 2 the draw, logged before the reservation (another protection
    # epoch), is out of the cohort altogether (E2), so nothing of its support is asked for.
    assert refs[0] not in seen
    from learnloop.adaptive_difficulty.material_view import detached_view

    view = detached_view(load_vault(paths.root), Repository(paths.sqlite_path))
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        assert draw["id"] not in {row["id"] for row in view.selections(connection)}
    assert report["prior_sensitivity"] is not None


# -- F26: the dose moderator's window -------------------------------------------------------------------


def test_the_dose_moderator_window_closes_only_at_a_visible_graded_attempt(tmp_path, monkeypatch):
    """F26: one worked example studied, then an answer on an item reserved for an exam now: the
    draw's recorded ``dose_taken.worked_example`` stays 1 (failed before: 0, the later attempt
    closed the window whatever it was)."""

    from learnloop.adaptive_difficulty import dose as D

    from tests.test_ad1_reading_opportunities import ITEM, LO_A, at
    from tests.test_ad3_dose_arm import _arm, _boundary, _draws, _mapping

    paths, vault, repo = _arm(tmp_path)
    with closing(connect(paths.sqlite_path)) as connection:
        ad_receipts.insert_reading_opportunity(connection, {
            "protection_epoch": SEEDED,
            "opportunity_key": f"worked_example:ext1/we2:{LO_A}", "kind": "worked_example", "subkind": "shown",
            "source_table": "reader_section_progress", "source_id": "ext1/we2",
            "source_written_at": iso_at(at(1)), "learning_object_id": LO_A, "facet_doses": {"fa1": 1.0},
            "dose_offer_id": None, "mapping_version": "ad_reading_map_v1", "sweep": "backfill", "sweep_ref": None,
            "swept_at": iso_at(at(1))})
        connection.commit()
    _attempt(paths, ITEM, at=at(5).now(), session=None)
    _reserve(monkeypatch, ITEM)
    restamp(paths)  # the studied example's receipt as the current epoch's sweep records it again (E2)
    D.decide(vault, repo, _boundary(), clock=at(10), reading_map=_mapping())
    (draw,) = _draws(paths)
    assert draw["detail"]["dose_taken"]["worked_example"] == 1


def iso_at(clock: Any) -> str:
    return clock.now().astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# -- F27: practice minutes ------------------------------------------------------------------------------


def test_practice_minutes_come_from_the_visible_practice_cohort(tmp_path, monkeypatch):
    """F27: one ordinary answer of one minute, and a 1,000-minute answer on an item reserved for an
    exam now: the report's practice reference reads 1 minute (failed before: the median, 500.5)."""

    paths = ad23_vault(tmp_path, items=("pi_m1", "pi_m2"), config=ROUTER_OFF)
    _env, clock = env_for(paths, items=("pi_m1", "pi_m2"))
    _attempt(paths, "pi_m1", at=clock.now() - timedelta(hours=2), latency=60)
    _attempt(paths, "pi_m2", at=clock.now() - timedelta(hours=1), latency=60000)
    _reserve(monkeypatch, "pi_m2")
    RP.clear_cache()
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        report = REP.build(load_vault(paths.root), Repository(paths.sqlite_path), connection, sensitivity=False)
    assert report["dose_and_burden"]["practice_reference"]["answer_minutes"] == pytest.approx(1.0)


# -- the degradations with the predicate unavailable -------------------------------------------------------


def test_with_the_predicate_unavailable_generation_takes_the_predecessors_target(tmp_path, monkeypatch):
    paths = ad23_vault(tmp_path, items=("pi_g1",), config=ROUTER_OFF)
    _predicate_raises(monkeypatch)
    target, text = _target(paths)
    assert target.ad_commission_id is None and selections(paths) == []
    assert "recommended_difficulty_band" in json.dumps(target.as_dict())


def test_with_the_predicate_unavailable_the_report_discloses_zero_observations(tmp_path, monkeypatch):
    paths = ad23_vault(tmp_path, items=("pi_m1",), config=ROUTER_OFF)
    _env, clock = env_for(paths, items=("pi_m1",))
    _attempt(paths, "pi_m1", at=clock.now() - timedelta(hours=1), latency=60)
    _predicate_raises(monkeypatch)
    RP.clear_cache()
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        report = REP.build(load_vault(paths.root), Repository(paths.sqlite_path), connection, sensitivity=True)
    assert report["protection"] == {"available": False, "reason": "held_out_predicate_unavailable",
                                    "withheld_items": len(load_vault(paths.root).practice_items)}
    assert report["records"] == 0 and report["inputs"]["attempts"] == 0
    assert report["dose_and_burden"]["practice_reference"] is None


def test_with_the_predicate_unavailable_the_dose_arm_draws_nothing(tmp_path, monkeypatch):
    from learnloop.adaptive_difficulty import dose as D

    from tests.test_ad1_reading_opportunities import at
    from tests.test_ad3_dose_arm import _arm, _boundary, _draws, _mapping

    paths, vault, repo = _arm(tmp_path)
    _predicate_raises(monkeypatch)
    decision = D.decide(vault, repo, _boundary(), clock=at(2), reading_map=_mapping())
    assert (decision.eligible, decision.reason) == (False, "protection_unavailable") and _draws(paths) == []
