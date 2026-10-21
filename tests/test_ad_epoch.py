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
    from learnloop.adaptive_difficulty.operation import epoch_of
    from learnloop.adaptive_difficulty.protection import protection

    return epoch_of(protection(vault, repository))


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
