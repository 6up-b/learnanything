"""AD23 redesign (E2, owner decision 2026-10-21): one vault-wide protection epoch scopes every cache
and persisted artefact computed from an operation's projection.

* the epoch changes on mark, unmark, reserve and release, and not on unrelated edits;
* each artefact class is in force at its own epoch and out of force at another: a relatedness run,
  a frozen outside-forecast state, the preparation cache (``_PREPARED``), the replay's snapshot cache
  and the span-alias memo;
* the preparation scheduler: 20 protected revisions queued before a public one leave the public one
  prepared in the first run (Codex verify F49), and a revision prepared while protected is prepared
  once it is public again (F50).

The F49 and F50 cases use only the scheduler's production entry points (``schedule_item_preparation``,
``prepare_items``), so they run unchanged on the pre-redesign tree (fail-before).

Fakes only: no network, no model call.
"""

from __future__ import annotations

import threading
from types import SimpleNamespace

import pytest

from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import ForecastLLM, ad_plan_vault

EXTRACTION = "ext_epoch"
HELD = "held_epoch"


def _hold(monkeypatch, *spans: str) -> None:
    from learnloop.content.sources import exam_material

    material = exam_material.Material(spans=frozenset((EXTRACTION, span) for span in spans))
    monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: material)


def _vault(paths, protected: int, public: tuple[str, ...] = ("pi_public",)):
    """A stand-in vault: ``protected`` items made from the held span (queued first), then the public
    ones (made from a public span)."""

    from learnloop.vault.models import CanonicalExercise

    real = load_vault(paths.root)
    base = real.practice_items["pi_m1a"]

    def made(item_id: str, span: str):
        return base.model_copy(update={"id": item_id, "prompt": f"Stem of {item_id}.", "canonical_exercise":
                                       CanonicalExercise(source_id="src_epoch", extraction_id=EXTRACTION,
                                                         span_ids=[span])})

    items = {f"pi_prot_{index:02d}": made(f"pi_prot_{index:02d}", HELD) for index in range(protected)}
    items.update({item_id: made(item_id, "public_epoch") for item_id in public})
    return SimpleNamespace(practice_items=items, config=real.config, root=real.root, source_sets=[])


class _Visits:
    """The audit and the forecast: each records the revision it was asked to prepare."""

    def __init__(self) -> None:
        self.visits: list[str] = []
        self.lock = threading.Lock()

    def audit(self, _vault, _repository, item, **_kwargs):
        with self.lock:
            self.visits.append(str(item.id))
        return SimpleNamespace(as_dict=lambda: {"status": "current"})

    def forecast(self, _vault, _repository, item, **_kwargs):
        return SimpleNamespace(as_dict=lambda: {"status": "current"})


def _patch(monkeypatch) -> _Visits:
    from learnloop.adaptive_difficulty import background, feature_audit

    visits = _Visits()
    monkeypatch.setattr(feature_audit, "audit_revision", visits.audit)
    monkeypatch.setattr(background, "forecast_item", visits.forecast)
    return visits


def _builds(paths):
    from learnloop.hints.map_builder import BackgroundBuilds

    builds = BackgroundBuilds()
    builds.bind(paths.sqlite_path)
    return builds


def _run(trigger):
    thread = trigger()
    if thread is not None:
        thread.join(30)
    return thread


# -- F49, F50: the preparation scheduler ---------------------------------------------------------------


def test_twenty_protected_revisions_queued_first_never_hold_back_the_public_one(tmp_path, monkeypatch):
    """F49: 20 protected revisions are queued before public revision P. The first run prepares P:
    protected keys do not count against the run's limit (failed before: the run took the first 20
    entries, all protected, and P waited for another trigger)."""

    from learnloop.adaptive_difficulty.background import schedule_item_preparation
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path)
    _hold(monkeypatch, HELD)
    vault = _vault(paths, 20)
    visits = _patch(monkeypatch)
    builds = _builds(paths)
    try:
        _run(lambda: schedule_item_preparation(vault, paths.sqlite_path, list(vault.practice_items),
                                               clients=Clients(llm=ForecastLLM()), builds=builds))
        assert visits.visits == ["pi_public"], visits.visits
    finally:
        builds.close()


def test_the_synchronous_preparation_counts_visible_revisions_only(tmp_path, monkeypatch):
    """F49's synchronous half: ``prepare_items`` with 20 protected ids first and a limit of 20 still
    prepares the public one (failed before: it sliced the ids before filtering them)."""

    from learnloop.adaptive_difficulty.background import prepare_items
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path)
    _hold(monkeypatch, HELD)
    vault = _vault(paths, 20)
    visits = _patch(monkeypatch)
    results = prepare_items(vault, Repository(paths.sqlite_path), list(vault.practice_items),
                            clients=Clients(llm=ForecastLLM()), limit=20)
    assert visits.visits == ["pi_public"]
    statuses = {entry["practice_item_id"]: (entry.get("audit") or {}).get("status") for entry in results}
    assert statuses["pi_public"] == "current" and statuses["pi_prot_00"] == "protected"


def test_a_revision_prepared_while_protected_is_prepared_once_it_is_public(tmp_path, monkeypatch):
    """F50: a revision is prepared while its source is protected (settled as protected); the source
    is then released without editing the item, and the next trigger prepares it (failed before: the
    process cache kept it as done for ever)."""

    from learnloop.adaptive_difficulty.background import schedule_item_preparation
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path)
    _hold(monkeypatch, HELD)
    vault = _vault(paths, 1, public=())
    visits = _patch(monkeypatch)
    builds, clients = _builds(paths), Clients(llm=ForecastLLM())
    try:
        _run(lambda: schedule_item_preparation(vault, paths.sqlite_path, ["pi_prot_00"], clients=clients,
                                               builds=builds))
        assert visits.visits == []
        _hold(monkeypatch)  # released
        _run(lambda: schedule_item_preparation(vault, paths.sqlite_path, ["pi_prot_00"], clients=clients,
                                               builds=builds))
        assert visits.visits == ["pi_prot_00"]
        # Done at this epoch: the next trigger at the same epoch schedules nothing.
        assert schedule_item_preparation(vault, paths.sqlite_path, ["pi_prot_00"], clients=clients,
                                         builds=builds) is None
    finally:
        builds.close()


# -- the epoch itself ------------------------------------------------------------------------------


def _epoch(vault, repository) -> str | None:
    from learnloop.adaptive_difficulty.material_view import detached_view

    return detached_view(vault, repository).epoch


def test_the_epoch_changes_on_mark_unmark_reserve_and_release_and_not_on_unrelated_edits(tmp_path, monkeypatch):
    from learnloop.adaptive_difficulty import protection as protection_module

    paths = ad_plan_vault(tmp_path)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    _hold(monkeypatch)
    unmarked = _epoch(vault, repository)
    _hold(monkeypatch, HELD)
    marked = _epoch(vault, repository)
    assert marked != unmarked
    _hold(monkeypatch)
    assert _epoch(vault, repository) == unmarked, "releasing restores the epoch"
    reserved = {"pi_m1a"}
    monkeypatch.setattr(Repository, "reserved_exam_pool_item_ids", lambda _self: sorted(reserved))
    with_reservation = _epoch(vault, repository)
    assert with_reservation != unmarked
    reserved.clear()
    assert _epoch(vault, repository) == unmarked
    # An unrelated edit (an item's text, an answer) leaves it.
    vault.practice_items["pi_m1a"] = vault.practice_items["pi_m1a"].model_copy(update={"prompt": "Edited."})
    with __import__("contextlib").closing(__import__("sqlite3").connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, "
                           "attempt_type, correctness, hints_used, created_at) VALUES ('att_epoch', 'pi_m1a', "
                           "'lo_m1', 'short_answer', 'independent_attempt', 1.0, 0, '2026-10-01T09:00:00Z')")
        connection.commit()
    assert _epoch(vault, repository) == unmarked
    # Unavailable: no epoch (nothing is in force).
    monkeypatch.setattr(protection_module, "protection",
                        lambda *_a, **_k: protection_module.Protection(frozenset(), None))
    assert _epoch(vault, repository) is None


# -- each artefact class, in force at its epoch only -------------------------------------------------


def test_a_relatedness_run_is_in_force_at_its_epoch_only():
    from learnloop.adaptive_difficulty.relatedness import EPOCH_UNIT, run_in_force, touched_units

    run = {"status": "ok", "units": {"lo:lo_a": "h1", EPOCH_UNIT: "e1"}, "judgment_ids": []}
    assert run_in_force(run, "e1") and not run_in_force(run, "e2") and not run_in_force(run, None)
    assert not run_in_force({"status": "ok", "units": {"lo:lo_a": "h1"}}, "e1"), "a run without an epoch"
    inputs = {"unit_hashes": {"lo:lo_a": "h1", EPOCH_UNIT: "e1"}}
    assert touched_units(inputs, [run]) == []
    assert touched_units({"unit_hashes": {"lo:lo_a": "h1", EPOCH_UNIT: "e2"}}, [run]) == ["lo:lo_a"]


def test_a_frozen_outside_state_is_sent_only_at_its_epoch(tmp_path, monkeypatch):
    """E2 (and F33's replacement): the history card is frozen at the serve; any protection change
    since then, even of a span nothing in the card quotes, expires it (owner decision 2026-10-21),
    and nothing reaches either model."""

    from tests.test_ad1_codex_rereview_fixes import _forecast, _served_with_history

    paths, step = _served_with_history(tmp_path)
    from learnloop.content.sources import exam_material

    material = exam_material.Material(spans=frozenset({("ext_rereview", "a_span_nothing_quotes")}))
    monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: material)
    outcomes, llm, decider = _forecast(paths, step)
    assert {outcome.status for outcome in outcomes} == {"protected"}
    assert llm.prompts == [] and decider.calls == []


def test_the_replay_cache_and_the_alias_memo_are_keyed_by_the_epoch(tmp_path, monkeypatch):
    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.adaptive_difficulty.operation import ad_operation

    paths = ad_plan_vault(tmp_path)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    RP.clear_cache()
    _hold(monkeypatch)
    first = RP.snapshot(vault, repository)
    assert RP.snapshot(vault, repository) is first, "the same epoch is served from the cache"
    with ad_operation(vault, repository) as op:
        public_key = op.repository.projection_key
    _hold(monkeypatch, HELD)
    assert RP.snapshot(vault, repository) is not first, "another epoch is never served from the cache"
    with ad_operation(vault, repository) as op:
        assert op.repository.projection_key != public_key, "the alias memo keys a projection by its epoch"
    from learnloop.content.sources.span_aliases import _memo_key

    assert _memo_key(repository, "a", "b") != _memo_key(op.repository, "a", "b")


# -- round 2 (the closed-checklist verify 20261021-081118-y3cr1s), class 3: epoch completeness ---------
#
# Each case below uses only entry points that exist on the round-1 tree (96c23b28a), so each fails there.


def _ad23_epoch():
    try:
        from tests.ad23_fakes import ad_epoch
    except ImportError:  # the round-1 tree: rows carried no epoch
        return lambda _paths: None
    return ad_epoch


def test_a_history_item_newly_protected_by_its_own_provenance_expires_the_frozen_forecast(tmp_path, monkeypatch):
    """Finding 1: the frozen card quotes history item ``pi_hist`` while it is public; its provenance
    then moves to a span that was ALREADY held out (the material is unchanged, only the items it
    protects). The frozen state is never sent (failed before: the epoch digested the material only,
    so it was unchanged and the history went out)."""

    from tests.test_ad1_codex_rereview_fixes import _exercise, _forecast, _served_with_history, _set_fields
    from tests.test_ad1_codex_rereview_fixes import _hold_out as hold

    hold(monkeypatch, "already_held")
    paths, step = _served_with_history(tmp_path)
    _set_fields(paths, "pi_hist", canonical_exercise=_exercise("already_held"))
    outcomes, llm, decider = _forecast(paths, step)
    assert {outcome.status for outcome in outcomes} == {"protected"}
    assert llm.prompts == [] and decider.calls == []


def test_a_commission_drawn_under_other_protection_is_not_open(tmp_path, monkeypatch):
    """Finding 2: a commission is drawn; then another item of its cell is withheld (the cell keeps
    public material). The old commission is out of force: it is not open, so it neither suppresses a
    fresh draw nor supplies the generation target (failed before: it stayed open across epochs)."""

    from contextlib import closing

    from learnloop.adaptive_difficulty.material_view import detached_view
    from learnloop.db.connection import connect

    from tests.ad23_fakes import ad23_vault, selections, set_item
    from tests.test_ad2_serving import _generation_prompt

    paths = ad23_vault(tmp_path, items=("pi_g1", "pi_g2"))
    set_item(paths, "pi_g2", canonical_exercise={"source_id": "src_epoch", "extraction_id": EXTRACTION,
                                                  "span_ids": [HELD]})
    _generation_prompt(paths)
    (commission,) = selections(paths, kind="commission")

    def open_ids() -> list[str]:
        view = detached_view(load_vault(paths.root), Repository(paths.sqlite_path))
        with closing(connect(paths.sqlite_path, read_only=True)) as connection:
            return [str(row["id"]) for row in view.open_commissions(connection, now=commission["created_at"])]

    assert open_ids() == [commission["id"]]
    _hold(monkeypatch, HELD)
    assert open_ids() == []


def test_a_reading_receipt_recorded_under_other_protection_is_mapped_again(tmp_path, monkeypatch):
    """Finding 3: a public passage view is recorded while the LO has public facet ``fp`` and facet
    ``fh`` (doses 0.5 each); ``fh``'s only item is then withheld. The old receipt counts for nothing
    and the sweep maps the view again under the current projection: ``{fp: 1.0}`` (failed before: the
    receipt's surviving weight ``{fp: 0.5}`` was replayed)."""

    from contextlib import closing

    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.adaptive_difficulty.reading import sweep
    from learnloop.db.connection import connect

    from tests.ad23_fakes import set_item
    from tests.test_ad_projection import EXT, LO as PLO, P, _iso, _mixed_section, T0

    # A clean reading (the withheld material lies in another extraction): read as stored (round 8).
    paths = _mixed_section(tmp_path)
    set_item(paths, "pi_m1a", evidence_facets=["fp"], evidence_weights={"fp": 1.0})
    set_item(paths, "pi_f48", learning_object_id=PLO, evidence_facets=["fh"], evidence_weights={"fh": 1.0},
             canonical_exercise={"source_id": "src_f48", "extraction_id": "ext_other", "span_ids": ["h_other"]})

    def doses() -> list[dict[str, float]]:
        RP.clear_cache()
        with closing(connect(paths.sqlite_path, read_only=True)) as connection:
            events = RP.load_events(connection, load_vault(paths.root), Repository(paths.sqlite_path))
        return [dict(event.facet_doses) for event in events.opportunities if event.learning_object_id == PLO]

    sweep(load_vault(paths.root), Repository(paths.sqlite_path), as_of=_iso(T0), sweep_kind="backfill")
    assert doses() == [{"fh": 0.5, "fp": 0.5}]
    from learnloop.content.sources import exam_material

    material = exam_material.Material(spans=frozenset({("ext_other", "h_other")}))
    monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: material)
    assert {"fp": 0.5} not in doses()
    sweep(load_vault(paths.root), Repository(paths.sqlite_path), as_of=_iso(T0), sweep_kind="backfill")
    assert doses() == [{"fp": 1.0}]
    assert EXT and P  # the mapping's own span, public throughout


def test_frozen_serve_signals_trained_on_a_newly_protected_answer_are_not_replayed(tmp_path, monkeypatch):
    """Finding 4: ``pi_y`` is served while ``z_v1`` is calibrated on ``pi_x``'s forecast and answer
    (its frozen signals say so); ``pi_x`` is then reserved for an exam. The replay no longer reads
    ``pi_y``'s frozen inputs (failed before: the frozen signal, trained on ``pi_x``, was replayed)."""

    from contextlib import closing
    from dataclasses import replace
    from datetime import timedelta

    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.adaptive_difficulty.outside import _receipt
    from learnloop.adaptive_difficulty.switches import LLM_V1
    from learnloop.daily_plan.engine import advance, build_plan
    from learnloop.db.connection import connect
    from learnloop.scheduling.forecast_receipts import record_receipts

    from tests.ad23_fakes import LO, ad23_vault, answer, env_for
    from tests.daily_plan_fakes import iso
    from tests.test_ad23_fix_r8 import _reserve

    paths = ad23_vault(tmp_path, items=("pi_x", "pi_y"), config="[router]\nenabled = false\n")
    env, clock = env_for(paths, items=("pi_x",))
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    _record, step = advance(env, serve=True)
    forecast_at = iso(clock.now() - timedelta(minutes=30))
    clock.advance(2)
    answer(paths, "pi_x", correct=True, presentation_id=step["presentation_id"], clock=clock)
    content_hash = item_revision(load_vault(paths.root).practice_items["pi_x"])[0]
    receipt = _receipt(
        key=f"llm_v1:{content_hash}", forecaster=LLM_V1, version="v1", scope="item", decision_kind="item_prepare",
        binding_kind="first_presentation", inputs={}, inputs_as_of=forecast_at, p=0.8, status="ok",
        received_at=forecast_at, model="fake", request_hash="h",
        columns={"practice_item_id": "pi_x", "learning_object_id": LO, "item_content_hash": content_hash,
                 "decision_ref": content_hash})
    epoch = _ad23_epoch()(paths)
    if epoch is not None:
        receipt = replace(receipt, versions={**dict(receipt.versions), "protection_epoch": epoch})
    record_receipts(Repository(paths.sqlite_path), [receipt], created_at=forecast_at)
    clock.advance(60 * 24)
    env2, _ = env_for(paths, items=("pi_y",), clock=clock, session="s2")
    build_plan(env2, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    _r, served = advance(env2, serve=True)
    clock.advance(2)
    answer(paths, "pi_y", correct=True, presentation_id=served["presentation_id"], clock=clock)

    def status() -> str:
        RP.clear_cache()
        with closing(connect(paths.sqlite_path, read_only=True)) as connection:
            events = RP.load_events(connection, load_vault(paths.root), Repository(paths.sqlite_path))
        (event,) = [e for e in events.attempts if e.practice_item_id == "pi_y"]
        return event.input_status

    assert status() == "frozen"
    _reserve(monkeypatch, "pi_x")
    assert status() != "frozen"


def test_a_protected_pending_proposal_never_holds_a_commission_open(tmp_path, monkeypatch):
    """Finding 5: a commission drawn outside any job expires seven days after its draw unless an item
    proposed for its LO is in review. A pending proposal whose item is made from held-out material
    is withheld before the expiry decision, so twenty days on the commission is closed (failed
    before: the raw pending proposal kept it open)."""

    import json
    import sqlite3
    from contextlib import closing
    from datetime import UTC, datetime, timedelta

    from learnloop.adaptive_difficulty.material_view import detached_view
    from learnloop.db.connection import connect

    from tests.ad23_fakes import LO, ad23_vault, selections
    from tests.test_ad2_serving import _generation_prompt

    _hold(monkeypatch, HELD)
    paths = ad23_vault(tmp_path, items=("pi_g1",))
    _generation_prompt(paths)
    (commission,) = selections(paths, kind="commission")
    drawn = datetime.fromisoformat(str(commission["created_at"]).replace("Z", "+00:00"))
    later = (drawn + timedelta(days=1)).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {"id": "pi_proposed", "learning_object_id": LO, "prompt": "A proposed item.",
               "canonical_exercise": {"source_id": "src_epoch", "extraction_id": EXTRACTION, "span_ids": [HELD]}}
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO proposed_patches(id, agent_run_id, purpose, status_cache, created_at, updated_at) "
                           "VALUES ('pp_r2', 'run_r2', 'practice_generation', 'pending', ?, ?)", (later, later))
        connection.execute(
            "INSERT INTO proposed_patch_items(id, proposed_patch_id, client_item_id, item_type, operation, payload_json, "
            "decision, validation_status, created_at, updated_at) VALUES ('ppi_r2', 'pp_r2', 'c1', 'practice_item', "
            "'create', ?, 'pending', 'valid', ?, ?)", (json.dumps(payload), later, later))
        connection.commit()
    now = (drawn + timedelta(days=20)).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    view = detached_view(load_vault(paths.root), Repository(paths.sqlite_path))
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        assert [row["id"] for row in view.open_commissions(connection, now=now)] == []


def test_any_change_to_the_protection_changes_the_epoch(tmp_path, monkeypatch):
    """Class 3a, a property over the protection's fields: every field of ``Protection`` and of its
    held-out ``Material`` that decides what is withheld, and every withheld set the view derives
    (revisions, notes, facets), is in the epoch: changing any one changes it. ``Material``'s
    ``reasons`` and ``pinned_revisions`` explain a verdict and decide nothing (``Material.covers``
    reads extractions and spans only), so they are not."""

    import dataclasses

    from learnloop.adaptive_difficulty.material_view import MaterialView
    from learnloop.adaptive_difficulty.protection import Protection, protection
    from learnloop.content.sources import exam_material

    paths = ad_plan_vault(tmp_path)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    _hold(monkeypatch)
    base = protection(vault, repository)

    def epoch(value: Protection) -> str | None:
        return MaterialView(vault, repository, value).epoch

    explanatory = {"reasons", "pinned_revisions"}
    material_fields = {field.name for field in dataclasses.fields(exam_material.Material)}
    assert explanatory <= material_fields
    changed_material = {
        "extractions": dataclasses.replace(base.material, extractions=frozenset({"ext_new"})),
        "spans": dataclasses.replace(base.material, spans=frozenset({("ext_new", "span_new")})),
    }
    assert set(changed_material) | explanatory == material_fields, "a new Material field must be classified here"
    for name, material in changed_material.items():
        assert epoch(dataclasses.replace(base, material=material)) != epoch(base), name
    protection_fields = {field.name for field in dataclasses.fields(Protection)}
    changed = {"ids": dataclasses.replace(base, ids=base.ids | {"pi_m1a"}),
               "reserved": dataclasses.replace(base, reserved=frozenset({"pi_m1a"}), ids=base.ids | {"pi_m1a"})}
    assert set(changed) | {"material"} == protection_fields, "a new Protection field must be classified here"
    for name, value in changed.items():
        assert epoch(value) != epoch(base), name
    assert epoch(dataclasses.replace(base, reserved=frozenset({"pi_m1b"}))) != epoch(base), "reserved alone"
    assert epoch(dataclasses.replace(base, material=None)) is None
