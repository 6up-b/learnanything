"""Evidence packets EPp, second part: the predecessor's prediction on a repeat presentation (spec §7.7.3 item 1,
§7.7.5, §10).

At an ordinary plan presentation of an item the learner attempted before, AD's serve hook writes two
evaluation-only receipts, ``ad_threshold_repeat@subject`` and ``@lo``, with the three category probabilities and
the inputs the predecessor read (signals with availability, warmth and its exposure, the surface group as served,
the earlier attempts on the item and its group, the delay, the predecessor's memory assumptions). Nothing reads them
to decide anything, ``item_serve_inputs`` gets no repeat row, and the receipts' ids come from a stream of their own:
no selection, served item, existing receipt, score row, state, id or seed moves. Fakes only: no network, no model
call.
"""

from __future__ import annotations

import json
import math
from contextlib import closing
from types import SimpleNamespace

import pytest

from learnloop.adaptive_difficulty import predict as PR
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty import repeat_receipts as RR
from learnloop.adaptive_difficulty import serve as serve_module
from learnloop.adaptive_difficulty.material_view import MaterialView
from learnloop.adaptive_difficulty.material_view import detached_view
from learnloop.adaptive_difficulty.operation import GuardDenied
from learnloop.daily_plan.engine import advance
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import forecast_receipts as store
from learnloop.scheduling import forecast_receipts as FR
from learnloop.vault.loader import load_vault

from tests.epp_repeat_helpers import (
    EARLIER_DAYS,
    REPEATED,
    FakeView,
    comparable,
    receipts,
    repeat_journey,
    repeat_presentation,
    table_rows,
)

THRESHOLDS = ("ad_threshold@subject", "ad_threshold@subject_uniform", "ad_threshold@lo")
IN_PROCESS = ("mastery_ekf", "lo_general+composite")


def _by_presentation(path, presentation_id):
    return {row["forecaster"]: row for row in receipts(path) if row["plan_presentation_id"] == presentation_id}


def _member(row, kind):
    [member] = [m for m in row["versions"]["snapshot"]["target"]["target"]["members"] if m["kind"] == kind]
    return member


def _scores(path):
    return {(row["plan_presentation_id"], row["forecaster"]): row for row in table_rows(path, "item_forecast_scores")}


# -- which presentation gets them ---------------------------------------------------------------------------------


def test_a_repeat_gets_the_two_receipts_and_a_fresh_item_keeps_its_own(tmp_path, monkeypatch):
    """The ordinary plan's serve hook: the repeated item's presentation gets the in-process receipts and the two
    repeat receipts (no ``ad_threshold@*``, no ``item_serve_inputs`` row); each fresh item's gets the five it got
    before and no repeat receipt."""

    run = repeat_journey(tmp_path / "run", monkeypatch)
    path = run["paths"].sqlite_path
    repeat = repeat_presentation(run)
    assert set(_by_presentation(path, repeat)) == {*IN_PROCESS, *RR.REPEAT_FORECASTERS}
    fresh = [str(step["presentation_id"]) for step in run["served"] if step["practice_item_id"] != REPEATED]
    assert len(fresh) == 2
    for presentation in fresh:
        assert set(_by_presentation(path, presentation)) == {*IN_PROCESS, *THRESHOLDS}
    frozen = {row["plan_presentation_id"] for row in table_rows(path, "item_serve_inputs")}
    assert frozen == set(fresh)


def test_a_reopened_presentation_records_nothing_again(tmp_path, monkeypatch):
    """Serving the open step again inserts no presentation, so the hook does not run; called again directly on
    the repeat's presentation, it finds the presentation recorded and writes nothing."""

    run = repeat_journey(tmp_path / "run", monkeypatch, rounds=1, answer_repeat=False)
    paths, env = run["paths"], run["env"]
    before = table_rows(paths.sqlite_path, "forecast_receipts")
    _record, step = advance(env, serve=True)
    assert step["practice_item_id"] == REPEATED and step["presentation_id"] == repeat_presentation(run)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    with repository.atomic():
        record = serve_module.record_plan_serve(vault, repository, presentation_id=repeat_presentation(run),
                                                practice_item_id=REPEATED, served_at="2026-10-12T09:00:00Z")
    assert record.skipped == "recorded" and record.repeat_receipt_ids == []
    assert table_rows(paths.sqlite_path, "forecast_receipts") == before


# -- what they say ------------------------------------------------------------------------------------------------


def test_the_categories_sum_to_one_and_category_two_is_the_binary_value(tmp_path, monkeypatch):
    """Each repeat receipt's ``p`` column is ``p̄`` and its categories' category 2 equals it to the bit; the
    snapshot's distribution states the same three categories over AD's category unit."""

    run = repeat_journey(tmp_path / "run", monkeypatch)
    rows = receipts(run["paths"].sqlite_path, forecasters=RR.REPEAT_FORECASTERS)
    assert len(rows) == 2
    for row in rows:
        categories = row["forecast"]["p_categories"]
        assert set(categories) == {"0", "1", "2"}
        assert abs(sum(categories.values()) - 1.0) <= 1e-12
        assert categories["2"] == row["p"]
        assert row["forecast"]["p"] == round(row["p"], 8)
        distribution = row["forecast"]["distribution"]
        assert distribution["unit"] == "ad_category3" and distribution["outcomes"] == categories
        assert distribution["event_outcomes"] == ["2"] and row["status"] == "ok"


def test_the_subject_receipt_is_the_predecessors_own_prediction_at_the_serve(tmp_path, monkeypatch):
    """Recomputed from the state the serve read (its hash recorded) with the predecessor's own functions, the
    subject view's ``p̄`` equals the receipt's: the receipt states the model as it stood, not a variant."""

    from learnloop.adaptive_difficulty.material_view import material_view
    from learnloop.adaptive_difficulty.operation import ad_operation

    calls: list = []
    computed = PR.category_mixture

    def recording(view, spec, *, warmth=0.0, weights=None):
        result = computed(view, spec, warmth=warmth, weights=weights)
        calls.append((view, spec, warmth, weights, result))
        return result

    monkeypatch.setattr(PR, "category_mixture", recording)
    # The grade's own forecast of each answer (one more prediction per answer) is not this test's subject.
    monkeypatch.setattr("learnloop.adaptive_difficulty.surprise_forecast.safe_grade_receipt", lambda *_a, **_k: None)
    run = repeat_journey(tmp_path / "run", monkeypatch, rounds=1, answer_repeat=False)
    paths = run["paths"]
    stored = {row["forecaster"]: row for row in receipts(paths.sqlite_path, forecasters=RR.REPEAT_FORECASTERS)}
    assert len(calls) == 2
    for name, (view, spec, warmth, weights, categories) in zip(RR.REPEAT_FORECASTERS, calls, strict=True):
        prediction = PR.predict(view, spec, warmth=warmth, weights=weights)
        assert weights is None and categories[2] == prediction.p_bar == stored[name]["p"]
        assert warmth == stored[name]["inputs"]["warmth"]["value"]
        assert dict(spec.signals) == stored[name]["inputs"]["signals_read"]
    # The state and the item as the predecessor reads them at that instant, recomputed: the same state hash, the
    # same item spec, so the subject receipt is the predecessor's own p̄ (the LO view is the item's LO's).
    subject = stored[RR.REPEAT_SUBJECT]
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    RP.clear_cache()
    with closing(connect(paths.sqlite_path)) as connection, ad_operation(
            vault, repository, read_only=True, connections=(connection,)):
        view = material_view(vault, repository)
        snapshot = RP.snapshot(vault, repository, connection=connection, view=view)
        spec = PR.current_spec(vault, connection, vault.practice_items[REPEATED], at=subject["created_at"],
                               view=view)
    assert snapshot.state_hash() == subject["inputs"]["state_hash"]
    assert spec == calls[0][1]
    assert PR.predict(snapshot.subject, spec, warmth=calls[0][2]).p_bar == subject["p"]
    assert calls[1][0] is not calls[0][0] and not calls[1][0].subject_view


def test_the_inputs_state_signals_with_availability_and_the_memory_context(tmp_path, monkeypatch):
    """Every signal is recorded with its availability: an unavailable one has no value and says why; an
    available one says whether the prediction read it (``z_v1`` enters only the outside arm). The memory context
    names the earlier attempt with its id and time, the surface group as served and its source, the case, the
    last exposure warmth came from (warmth is its formula's value), pre-exposure and the delay."""

    run = repeat_journey(tmp_path / "run", monkeypatch, rounds=1, answer_repeat=False)
    subject, lo = receipts(run["paths"].sqlite_path, forecasters=RR.REPEAT_FORECASTERS)
    inputs = subject["inputs"]
    assert inputs["schema"] == RR.INPUTS_SCHEMA and inputs["inputs_kind"] == "frozen_at_serve"
    signals = inputs["signals"]
    assert set(signals) == {"z_llm", "z_panel", "z_v1", "z_origin"}
    for name, entry in signals.items():
        if not entry["available"]:
            assert entry["value"] is None and entry["why"], name
            assert entry["read_by_prediction"] is False
    assert signals["z_panel"]["why"] == "not_solver_panel"
    assert signals["z_v1"]["available"] and signals["z_v1"]["read_by_prediction"] is False
    assert signals["z_v1"]["not_read_because"] == "outside_arm_only"
    assert signals["z_llm"]["read_by_prediction"] and set(inputs["signals_read"]) == {"z_llm", "z_origin"}
    memory = inputs["memory"]
    assert memory["item"]["attempts"] == 1
    assert memory["item"]["last"]["attempt_id"] == run["earlier_attempt"]
    assert memory["item"]["last"]["hours_before_serve"] == pytest.approx(EARLIER_DAYS * 24.0, abs=1.0)
    assert memory["surface_group"]["key"] == f"item:{REPEATED}" and memory["surface_group"]["source"] == "item"
    assert memory["case"] == {"item": "practised", "group": "singleton"}
    assert inputs["surface"] == {"key": f"item:{REPEATED}", "source": "item", "singleton": True}
    exposure = inputs["warmth"]["last_exposure"]
    assert exposure["available"] and exposure["kind"] == "attempt" and exposure["id"] == run["earlier_attempt"]
    assert inputs["warmth"]["value"] == pytest.approx(math.exp(-exposure["hours_before_serve"] / P.WARMTH_HOURS),
                                                      rel=1e-9)
    assert inputs["pre_exposed"] is False
    assert inputs["delay"]["kind"] == "natural" and inputs["delay"]["router_decision_id"]
    assert inputs["delay"]["assignment_propensity"]["available"] is False
    assert inputs["predecessor_memory"]["version"] == RR.PREDECESSOR_MEMORY["version"]
    assert inputs["item_revision"] == _member(subject, "item")["revision"]
    # The views differ only in their own fields: the LO view reads no loadings.
    differing = {key for key in inputs if inputs[key] != lo["inputs"].get(key)}
    assert differing <= {"view", "mixture", "loadings", "signals", "signals_read"}
    assert lo["inputs"]["view"] == "lo:lo_m1" and lo["inputs"]["loadings"] == {}


def test_the_snapshot_names_the_repeat_target_and_no_frozen_serve_inputs(tmp_path, monkeypatch):
    """The snapshot targets the item at its served revision with its surface group and source, conditional on this
    presentation, resolved by AD's scorer; its source names the inputs in the receipt, not an
    ``item_serve_inputs`` row (a repeat has none); provenance names the memory assumptions."""

    run = repeat_journey(tmp_path / "run", monkeypatch, rounds=1, answer_repeat=False)
    for row in receipts(run["paths"].sqlite_path, forecasters=RR.REPEAT_FORECASTERS):
        snapshot = row["versions"]["snapshot"]
        target = snapshot["target"]["target"]
        assert snapshot["target"]["stated_by"] == "producer"
        assert target["anchor"] == {"kind": "plan_presentation", "id": repeat_presentation(run)}
        assert target["horizon"]["kind"] == "presentation" and target["action"] == {"kind": "serve", "id": REPEATED}
        assert target["resolver_version"] == "ad_forecast_scores_v1" and target["unit"] == "ad_category3"
        assert _member(row, "surface_group") == {"kind": "surface_group", "id": f"item:{REPEATED}", "revision": None,
                                                 "source": "item"}
        assert _member(row, "item")["revision"] == row["inputs"]["item_revision"]
        source = snapshot["cutoff"]["source"]
        assert "item_serve_inputs" not in source and source["repeat_inputs"] == "inputs_json"
        assert snapshot["provenance"]["memory_assumptions"] == RR.PREDECESSOR_MEMORY["version"]
        assert row["versions"]["protection_epoch"] and row["algorithm_version"]


def test_the_surface_group_is_recorded_as_served_after_a_later_edit(tmp_path, monkeypatch):
    """The repeated item is in surface family ``fam_a`` with a sibling practised before; after the serve the
    family is edited to ``fam_b``: the receipt keeps ``fam_a``, its source and the sibling's attempt."""

    def family(paths):
        from tests.ad23_fakes import set_item

        set_item(paths, REPEATED, surface_family="fam_a")
        set_item(paths, "pi_m1c", surface_family="fam_a")

    def setup(paths):
        family(paths)
        from datetime import timedelta

        from tests.ad23_fakes import answer
        from tests.daily_plan_fakes import NOW, MovableClock

        answer(paths, "pi_m1c", correct=True, clock=MovableClock(NOW - timedelta(days=5)))

    run = repeat_journey(tmp_path / "run", monkeypatch, rounds=1, answer_repeat=False, setup=setup,
                         edit_after={"surface_family": "fam_b"})
    [subject] = receipts(run["paths"].sqlite_path, forecasters=(RR.REPEAT_SUBJECT,))
    memory = subject["inputs"]["memory"]
    assert subject["inputs"]["surface"] == {"key": "fam_a", "source": "surface_family", "singleton": False}
    assert memory["surface_group"]["sibling_attempts"] == 1 and memory["surface_group"]["items_attempted"] == 2
    assert memory["surface_group"]["last_sibling"]["practice_item_id"] == "pi_m1c"
    assert memory["case"] == {"item": "practised", "group": "family_siblings_practised"}
    assert _member(subject, "surface_group") == {"kind": "surface_group", "id": "fam_a", "revision": None,
                                                 "source": "surface_family"}
    assert load_vault(run["paths"].root).practice_items[REPEATED].surface_family == "fam_b"


# -- the pure parts -----------------------------------------------------------------------------------------------


def _item(item_id, family=None):
    return SimpleNamespace(id=item_id, evidence_fingerprint=None, surface_family=family, learning_object_id="lo")


def _attempt(attempt_id, item_id, at, **extra):
    return {"id": attempt_id, "practice_item_id": item_id, "learning_object_id": "lo", "created_at": at,
            "attempt_type": "independent_attempt", "plan_presentation_id": None, "correctness": 1.0,
            "hints_used": 0, "primed": 0, **extra}


SERVED_AT = "2026-10-12T09:00:00Z"


@pytest.mark.parametrize(("family", "sibling", "case"), [
    (None, None, "singleton"),
    ("fam", "pi_b", "family_siblings_practised"),
    ("fam", None, "family_item_only"),
])
def test_the_memory_context_tells_the_cases_apart(family, sibling, case):
    """A singleton group, a family whose other items were practised, and a family met only through this item:
    each named, with the last attempt of the item and of the group, at or before the serve (the freshness test's
    boundary: an attempt at the serve's own instant counts, a later one does not)."""

    from learnloop.adaptive_difficulty.snapshot_parts import ServedItem

    key = family or "item:pi_a"
    served = ServedItem("pi_a", "h", "lo", (), key, "surface_family" if family else "item")
    items = {"pi_a": _item("pi_a", family), "pi_b": _item("pi_b", family if sibling else "other"),
             "pi_c": _item("pi_c", "other")}
    attempts = [_attempt("a1", "pi_a", "2026-10-09T09:00:00Z"), _attempt("b1", "pi_b", "2026-10-10T09:00:00Z"),
                _attempt("c1", "pi_c", "2026-10-11T09:00:00Z"), _attempt("a2", "pi_a", SERVED_AT),
                _attempt("a3", "pi_a", "2026-10-12T09:00:01Z")]
    found = RR.memory_context(None, FakeView(attempts=attempts, items=items), items["pi_a"], served, SERVED_AT)
    assert found["case"] == {"item": "practised", "group": case}
    assert found["item"]["attempts"] == 2 and found["item"]["last"]["attempt_id"] == "a2"
    assert found["item"]["last"]["hours_before_serve"] == 0.0
    group = found["surface_group"]
    assert group["singleton"] is (family is None)
    assert group["sibling_attempts"] == (1 if sibling else 0)
    assert (group["last_sibling"] or {}).get("attempt_id") == ("b1" if sibling else None)


def test_the_last_exposure_is_the_one_warmth_reads():
    """The latest of the learning object's attempts, reveals and reading opportunities strictly before the serve,
    with its id, time and kind; none before the serve is unavailable with its reason, never a zero."""

    view = FakeView(attempts=[_attempt("a1", "pi_a", "2026-10-12T03:00:00Z"), _attempt("a2", "pi_a", SERVED_AT)],
                    reveals=[{"id": "r1", "learning_object_id": "lo", "created_at": "2026-10-12T05:00:00Z"}],
                    readings=[{"id": "o1", "learning_object_id": "lo", "kind": "section",
                               "source_written_at": "2026-10-12T04:00:00Z"}])
    found = RR.last_exposure(None, view, "lo", SERVED_AT)
    assert found == {"available": True, "id": "r1", "at": "2026-10-12T05:00:00Z", "kind": "reveal",
                     "hours_before_serve": 4.0}
    assert RR.last_exposure(None, FakeView(), "lo", SERVED_AT) == {"available": False,
                                                                  "why": "no_exposure_before_serve"}


def test_the_delay_names_its_kind_and_what_is_unknown_of_its_assignment():
    """A plan's own repeat is natural; a randomized check's origin (the router's constant, restated) is named so;
    the propensities, outside what AD's operation may read, are unavailable with their reason."""

    from learnloop.router_objective.checks import ORIGIN

    assert RR.RANDOMIZED_CHECK_ORIGIN == ORIGIN
    memory = {"item": {"last": {"hours_before_serve": 72.0}}, "surface_group": {"last": {"hours_before_serve": 5.0}}}
    natural = RR.delay_context(None, FakeView(presentations={"pp": {"origin": "chooser", "router_decision_id": "rd",
                                                                    "block_id": "b"}}), "pp", memory, SERVED_AT)
    assert natural["kind"] == "natural" and natural["hours_since_item_attempt"] == 72.0
    assert natural["assignment_propensity"]["why"].startswith("not_readable_in_ad_operation")
    assert natural["redraw_probability"]["why"].startswith("not_applicable")
    check = RR.delay_context(None, FakeView(presentations={"pp": {"origin": ORIGIN}}), "pp", memory, SERVED_AT)
    assert check["kind"] == "randomized_check"
    assert check["assignment_propensity"]["why"].startswith("no_router_decision")


# -- lifecycle: failed, refused, unwritten, answered, censored ----------------------------------------------------


def test_a_computation_that_fails_is_recorded_as_failed_with_its_reason(tmp_path, monkeypatch):
    """Both receipts are written as failed forecasts (no ``p``, the reason named, the snapshot's distribution not
    issued); the scorer reads them as invalid. Every other receipt of the serve stands."""

    def broken(*_args, **_kwargs):
        raise RuntimeError("memory read")

    monkeypatch.setattr(RR, "memory_context", broken)
    run = repeat_journey(tmp_path / "run", monkeypatch, rounds=1, answer_repeat=False)
    path = run["paths"].sqlite_path
    rows = _by_presentation(path, repeat_presentation(run))
    assert set(rows) == {*IN_PROCESS, *RR.REPEAT_FORECASTERS}
    for name in RR.REPEAT_FORECASTERS:
        row = rows[name]
        assert row["status"] == "failed" and row["p"] is None
        assert row["forecast"]["reason"] == "compute_failed:RuntimeError"
        assert row["forecast"]["distribution"]["outcomes"] is None
        assert row["forecast"]["distribution"]["reason"] == "failed"
    scores = _scores(path)
    assert {scores[(repeat_presentation(run), name)]["status"] for name in RR.REPEAT_FORECASTERS} == {"invalid"}


def test_a_write_that_fails_rolls_back_alone(tmp_path, monkeypatch):
    """A repeat receipt whose insert fails is not written (nothing forced), and the serve's other receipts stand:
    the repeat receipts have their own savepoint."""

    real = store.insert_receipt

    def failing(connection, **kwargs):
        if kwargs.get("forecaster") in RR.REPEAT_FORECASTERS:
            raise RuntimeError("disk")
        return real(connection, **kwargs)

    monkeypatch.setattr(store, "insert_receipt", failing)
    run = repeat_journey(tmp_path / "run", monkeypatch, rounds=1, answer_repeat=False)
    assert set(_by_presentation(run["paths"].sqlite_path, repeat_presentation(run))) == set(IN_PROCESS)


def test_a_guard_refusal_is_never_bypassed(tmp_path, monkeypatch):
    """A refusal of AD's guard while building them rolls the serve's whole AD record back, as any refusal in it
    does: no receipt is forced past the guard, and the plan still serves the item."""

    def refused(*_args, **_kwargs):
        raise GuardDenied("refused")

    monkeypatch.setattr(serve_module, "repeat_receipts", refused)
    run = repeat_journey(tmp_path / "run", monkeypatch, rounds=1, answer_repeat=False)
    assert run["served"][0]["practice_item_id"] == REPEATED
    assert _by_presentation(run["paths"].sqlite_path, repeat_presentation(run)) == {}


def test_a_protected_item_gets_no_repeat_receipt(tmp_path, monkeypatch):
    """An item the serve's material view withholds gets no receipt of any kind, as before; a receipt written
    earlier is withheld by the view once its revision is."""

    real_withheld = MaterialView.withheld
    real_serve = serve_module.record_plan_serve

    def withholding(*args, **kwargs):
        with monkeypatch.context() as patch:
            patch.setattr(MaterialView, "withheld",
                          lambda self, item_id: str(item_id) == REPEATED or real_withheld(self, item_id))
            return real_serve(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(serve_module, "record_plan_serve", withholding)
        protected = repeat_journey(tmp_path / "protected", monkeypatch, rounds=1, answer_repeat=False)
    assert _by_presentation(protected["paths"].sqlite_path, repeat_presentation(protected)) == {}

    run = repeat_journey(tmp_path / "run", monkeypatch, rounds=1, answer_repeat=False)
    paths = run["paths"]
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    with closing(connect(paths.sqlite_path)) as connection:
        rows = [row for row in store.list_receipts(connection, kind=FR.ITEM_UNASSISTED_SUCCESS)
                if row["forecaster"] in RR.REPEAT_FORECASTERS]
        assert len(rows) == 2
        view = detached_view(vault, repository)
        assert len(view.filter(connection, "forecast_receipts", rows)) == 2
        [revision] = {m["revision"] for m in rows[0]["versions"]["snapshot"]["target"]["target"]["members"]
                      if m["kind"] == "item"}
        bare = [{**row, "practice_item_id": None, "plan_presentation_id": None} for row in rows]
        monkeypatch.setattr(view, "revision_hash_withheld", lambda _connection, value: value == revision)
        assert view.filter(connection, "forecast_receipts", bare) == []


def test_answered_unanswered_and_scored_like_the_in_process_receipts(tmp_path, monkeypatch):
    """The scorer gives a repeat receipt the row it gives the in-process receipts of the same presentation:
    ``excluded`` (a repeat surface) once answered, ``pending`` (censored: no attempt) while unanswered. No new
    eligibility: the same attempt, the same reason."""

    answered = repeat_journey(tmp_path / "answered", monkeypatch)
    scores = _scores(answered["paths"].sqlite_path)
    presentation = repeat_presentation(answered)
    statuses = {name: scores[(presentation, name)]["status"] for name in (*IN_PROCESS, *RR.REPEAT_FORECASTERS)}
    assert set(statuses.values()) == {"excluded"}
    assert {json.loads(scores[(presentation, name)]["detail_json"])["why"] for name in statuses} == {"repeat_surface"}

    open_run = repeat_journey(tmp_path / "open", monkeypatch, rounds=1, answer_repeat=False)
    scores = _scores(open_run["paths"].sqlite_path)
    presentation = repeat_presentation(open_run)
    statuses = {name: (scores[(presentation, name)]["status"], json.loads(scores[(presentation, name)]["detail_json"]))
                for name in (*IN_PROCESS, *RR.REPEAT_FORECASTERS)}
    assert all(status == ("pending", {"why": "no_attempt"}) for status in statuses.values()), statuses


def test_the_repeat_path_writes_no_frozen_inputs_and_no_revision_snapshot(tmp_path, monkeypatch):
    """The serve inputs' writer (``build_row``, which also inserts the revision's snapshot) is never called for a
    repeat, and the repeat serve adds no ``practice_item_snapshots`` row."""

    from learnloop.db.stores import ad_receipts

    calls = []
    real_build = serve_module.build_row
    real_snapshot = ad_receipts.insert_item_snapshot

    def build(*args, **kwargs):
        calls.append(("build_row", str(args[2].id)))
        return real_build(*args, **kwargs)

    def snap(connection, **kwargs):
        calls.append(("snapshot", kwargs["practice_item_id"]))
        return real_snapshot(connection, **kwargs)

    monkeypatch.setattr(serve_module, "build_row", build)
    monkeypatch.setattr(ad_receipts, "insert_item_snapshot", snap)
    repeat_journey(tmp_path / "run", monkeypatch)
    assert REPEATED not in {item for _kind, item in calls}
    assert {item for _kind, item in calls} == {"pi_m1b", "pi_m1c"}


# -- writes: idempotent, rolled back with their transaction, ids from their own stream ----------------------------


def test_repeat_receipts_roll_back_with_the_serve_transaction(tmp_path, monkeypatch):
    """Written in the serve's transaction: a serve that fails after the hook leaves none."""

    real = serve_module.record_plan_serve
    vaults = []

    def then_fail(*args, **kwargs):
        record = real(*args, **kwargs)
        if kwargs["practice_item_id"] == REPEATED:
            assert len(record.repeat_receipt_ids) == 2
            raise RuntimeError("the serve failed after the hook")
        return record

    monkeypatch.setattr(serve_module, "record_plan_serve", then_fail)
    with pytest.raises(RuntimeError, match="after the hook"):
        repeat_journey(tmp_path / "run", monkeypatch, rounds=1, answer_repeat=False, setup=vaults.append)
    assert receipts(vaults[0].sqlite_path, forecasters=RR.REPEAT_FORECASTERS) == []
    assert table_rows(vaults[0].sqlite_path, "plan_presentations") == []


def test_repeat_receipt_ids_come_from_their_own_stream(tmp_path, monkeypatch):
    """Under the frozen clock the global stream counts from one instant; the repeat receipts' ids are not drawn
    from it, and the serve draws them from ``new_receipt_id``, which never calls ``ids.new_ulid``."""

    from learnloop import ids

    run = repeat_journey(tmp_path / "run", monkeypatch, rounds=1, answer_repeat=False)
    rows = receipts(run["paths"].sqlite_path)
    own = {row["id"][:10] for row in rows if row["forecaster"] in RR.REPEAT_FORECASTERS}
    global_ = {row["id"][:10] for row in rows if row["forecaster"] not in RR.REPEAT_FORECASTERS}
    assert len(own) == 1 and own.isdisjoint(global_)
    assert serve_module.new_receipt_id is RR.new_receipt_id

    def forbidden() -> str:
        raise AssertionError("a repeat receipt id was drawn from the global stream")

    monkeypatch.setattr(ids, "new_ulid", forbidden)
    first, second = RR.new_receipt_id(), RR.new_receipt_id()
    assert first < second and len(first) == 26


# -- non-interference --------------------------------------------------------------------------------------------


def _surprise_forecasters(sqlite_path) -> set[str]:
    with closing(connect(sqlite_path, read_only=True)) as connection:
        return {json.loads(row[0]).get("forecaster") for row in connection.execute(
            "SELECT predicted_score_dist_json FROM attempt_surprise")} - {None}


def test_repeat_receipts_move_no_id_seed_receipt_score_or_state_under_a_frozen_clock(tmp_path, monkeypatch):
    """Two copies of one journey with a repeat in it, the second without repeat capture: every row of every table
    is identical once the repeat receipts and their score rows are left out (router decisions and their seeds, AD
    selections, served items, plan presentations, the fresh items' receipts with their keys, ``p`` and input
    hashes, ``item_serve_inputs`` with ``z_v1``, AD state and trace, every other score row). A mutation that takes
    one global id per repeat receipt breaks it."""

    # The first journey of a process mints one id more than later ones (a one-time process setup): a discarded
    # warm-up makes the compared copies start alike.
    repeat_journey(tmp_path / "warm", monkeypatch)
    with_repeat = repeat_journey(tmp_path / "with", monkeypatch)
    without = repeat_journey(tmp_path / "without", monkeypatch, capture=False)
    new, old = comparable(with_repeat["paths"].sqlite_path), comparable(without["paths"].sqlite_path)
    assert new.keys() == old.keys()
    # From the difficulty label's retirement the repeat answer's surprise is scored against its repeat receipt
    # (without capture, against the grade's own forecast): that surprise row and the result that carries it are the
    # only rows that differ, and the forecaster each read is the one named.
    assert {table for table in new if new[table] != old[table]} <= {"attempt_surprise", "attempt_completion_work"}
    assert _surprise_forecasters(with_repeat["paths"].sqlite_path) - _surprise_forecasters(
        without["paths"].sqlite_path) == {RR.REPEAT_SUBJECT}
    for table in ("forecast_receipts", "item_serve_inputs", "ad_state", "ad_attempt_trace", "item_forecast_scores",
                  "plan_presentations", "router_decisions", "ad_selections"):
        assert new[table], table
    assert len(receipts(with_repeat["paths"].sqlite_path, forecasters=RR.REPEAT_FORECASTERS)) == 2
    assert receipts(without["paths"].sqlite_path, forecasters=RR.REPEAT_FORECASTERS) == []
    signals = [json.loads(json.loads(row)["signals_json"])["z_v1"] for row in new["item_serve_inputs"]]
    assert len(signals) == 2 and all(signal["available"] for signal in signals)
    assert [step["presentation_id"] for step in with_repeat["served"]] == [
        step["presentation_id"] for step in without["served"]]

    mutated = repeat_journey(tmp_path / "mutated", monkeypatch, mutate=True)
    changed = comparable(mutated["paths"].sqlite_path)
    assert {table for table in changed if changed[table] != old[table]} >= {"plan_presentations", "forecast_receipts"}
