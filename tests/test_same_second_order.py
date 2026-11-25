"""Same-second grades replay in the order they were applied (mvp-0.65; ``learnloop.db.attempt_order``).

An attempt's id is minted when its grading starts and its ``created_at`` (whole seconds) when its grade is applied, so
two grades of one learning object applied in one second can carry ids in the opposite order from their application.
Below the tag every prefix reader orders the ledger by ``(created_at, id)`` and replay folds such a pair in id order;
at the tag ``apply_attempt`` reserves a sequence in its own write transaction and every prefix reader breaks a tie by
it. The boundaries are tested, not only the final state: each attempt must see, on replay, the recent attempts and the
canonical belief cache its live write saw.
"""

from __future__ import annotations

import contextvars
from datetime import UTC, datetime, timedelta

import pytest

import learnloop.attempts.attempts as attempts_module
from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    APPLICATION_ORDER_ALGORITHM_VERSION,
    APPLICATION_ORDER_VERSIONS,
    SUCCESSOR_CHAIN,
    UNTAKEN_EPISODE_END_ALGORITHM_VERSION,
    application_order_on,
)
from learnloop.db.attempt_order import (
    APPLICATION_ORDER,
    BASIS_APPLIED,
    BASIS_LEGACY_ORDER_UNKNOWN,
    LEGACY_ORDER,
    attempt_order_for,
)
from learnloop.db.stores.attempts import reserve_application_sequence
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ops.upgrades import upgrade
from learnloop.substrate import replay as replay_module
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.rebuild_equivalence_helpers import ZERO, _mastery, _shadow_summary
from tests.regrade_contract_replay_helpers import SIBLING_ITEM, _regrade, _self_graded_apply
from tests.route_rules_in_grader_helpers import ITEM
from tests.split_live_helpers import split_vault

AT, BEFORE = APPLICATION_ORDER_ALGORITHM_VERSION, UNTAKEN_EPISODE_END_ALGORITHM_VERSION
#: One second: every attempt below is applied at it unless it says otherwise.
T = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)

#: Ids minted in this order (A before B) and applied in the other (B, then A).
A_ID, B_ID = "01ZZZZZZZZZZZZZZZZZZZZZZZA", "01ZZZZZZZZZZZZZZZZZZZZZZZB"
FULL, NONE = {"setup": 2.0, "result": 2.0}, {"setup": 0.0, "result": 0.0}


def _vault(tmp_path, version):
    """The diagnosis vault at ``version`` with no history, its state synced (every learning object materialized, as a
    rebuild materializes them)."""

    paths, vault, repository = split_vault(tmp_path, version=version, seed=False)
    sync_vault_state(vault, repository, clock=FrozenClock(T - timedelta(days=1)))
    return paths, vault, repository


def _lo(vault) -> str:
    return vault.practice_items[ITEM].learning_object_id


def _sequences(repository) -> list[tuple[str, int, str, str]]:
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT attempt_id, sequence, basis, algorithm_version FROM attempt_application_order ORDER BY sequence"
        )]


def _reversed_pair(vault, repository, *, second_repository=None, when=T):
    """B (the later id) applied first, A (the earlier id) in the same second: a pass, then a total miss."""

    _self_graded_apply(vault, second_repository or repository, ITEM, FULL, attempt_id=B_ID, when=when)
    _self_graded_apply(vault, repository, ITEM, NONE, attempt_id=A_ID, when=when)


# -- the tag ---------------------------------------------------------------------------------------------------


def test_the_tag():
    assert AT == "mvp-0.65" == SUCCESSOR_CHAIN[-10] and SUCCESSOR_CHAIN[-11] == BEFORE == "mvp-0.64"
    assert APPLICATION_ORDER_VERSIONS == frozenset({AT, "mvp-0.66", "mvp-0.67", "mvp-0.68", "mvp-0.69", "mvp-0.70", "mvp-0.71", "mvp-0.72", "mvp-0.73", "mvp-0.74"})
    for version, order in ((BEFORE, LEGACY_ORDER), (AT, APPLICATION_ORDER)):
        config = type("C", (), {"algorithms": type("A", (), {"algorithm_version": version})()})()
        assert application_order_on(config) is (version == AT)
        assert attempt_order_for(config) == order
    assert application_order_on(object()) is False


# -- below the tag: nothing is reserved and replay folds in id order --------------------------------------------


def test_below_the_tag_no_sequence_is_reserved_and_a_reversed_pair_rebuilds_in_id_order(tmp_path):
    paths, vault, repository = _vault(tmp_path, BEFORE)
    _reversed_pair(vault, repository)
    live = _mastery(repository)

    assert _sequences(repository) == []
    assert [row["id"] for row in repository.list_attempts_by_learning_object(_lo(vault))] == [A_ID, B_ID]
    rebuild_all_derived_state(vault, repository)
    # The predecessor's defect, kept below the tag: the rebuild folded the miss first.
    assert _mastery(repository) != live


# -- at the tag: the reservation --------------------------------------------------------------------------------


def test_at_the_tag_each_live_attempt_reserves_the_next_sequence_in_application_order(tmp_path):
    paths, vault, repository = _vault(tmp_path, AT)
    _reversed_pair(vault, repository)
    assert _sequences(repository) == [(B_ID, 1, BASIS_APPLIED, AT), (A_ID, 2, BASIS_APPLIED, AT)]
    assert [row["id"] for row in repository.list_attempts_by_learning_object(_lo(vault), order=APPLICATION_ORDER)] == [
        B_ID, A_ID]


def test_two_connections_with_reversed_allocation_and_completion_rebuild_to_live(tmp_path):
    # Each grade through its own connection to the one database, as two sidecars would: the sequence comes from the
    # database under the write lock, not from any process's state.
    paths, vault, repository = _vault(tmp_path, LATEST_ALGORITHM_VERSION)
    other = Repository(paths.sqlite_path)
    _reversed_pair(vault, repository, second_repository=other)
    assert [row[0] for row in _sequences(repository)] == [B_ID, A_ID]
    live = _mastery(repository)

    rebuild_all_derived_state(vault, repository)

    assert _mastery(repository) == live
    assert _shadow_summary(paths)["summary"] == ZERO


def test_a_rolled_back_application_leaves_no_reservation_and_its_retry_takes_the_next(tmp_path, monkeypatch):
    paths, vault, repository = _vault(tmp_path, AT)
    _self_graded_apply(vault, repository, ITEM, FULL, attempt_id=B_ID, when=T)

    def refused(*args, **kwargs):
        raise RuntimeError("injected failure after the reservation")

    # The attempt's own write fails inside the transaction, after the reservation.
    monkeypatch.setattr(repository, "record_attempt_outcome", refused)
    with pytest.raises(RuntimeError, match="injected"):
        _self_graded_apply(vault, repository, ITEM, NONE, attempt_id=A_ID, when=T)
    assert _sequences(repository) == [(B_ID, 1, BASIS_APPLIED, AT)]
    assert repository.fetch_practice_attempt(A_ID) is None

    monkeypatch.undo()
    _self_graded_apply(vault, repository, ITEM, NONE, attempt_id=A_ID, when=T)
    assert _sequences(repository) == [(B_ID, 1, BASIS_APPLIED, AT), (A_ID, 2, BASIS_APPLIED, AT)]
    # A second reservation of an attempt that has one finds it (no second row, no new number).
    with repository.connection() as connection:
        assert reserve_application_sequence(connection, A_ID, algorithm_version=AT, recorded_at="x") == 2
    assert len(_sequences(repository)) == 2


def test_a_replay_and_a_regrade_keep_the_attempts_sequence(tmp_path):
    # A regrade is not a new observation: it supersedes the grade and replays the learning object, and the
    # attempt keeps the place it was applied at.
    paths, vault, repository = _vault(tmp_path, LATEST_ALGORITHM_VERSION)
    _reversed_pair(vault, repository)
    before = _sequences(repository)

    rebuild_all_derived_state(vault, repository)
    assert _sequences(repository) == before
    _regrade(vault, repository, B_ID, {"setup": 1.0, "result": 0.0}, when=T + timedelta(hours=1))
    assert _sequences(repository) == before
    live = _mastery(repository)
    rebuild_all_derived_state(vault, repository)
    assert _mastery(repository) == live


# -- the boundaries ---------------------------------------------------------------------------------------------


class _Seen:
    """What each attempt computation read: the recent LO and item windows (ids, newest first) and the canonical belief
    cache's values, keyed by attempt id; the last reading of an attempt wins (live, then replay)."""

    def __init__(self, monkeypatch):
        self.windows: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
        self.cache: dict[str, tuple] = {}
        current: contextvars.ContextVar[str | None] = contextvars.ContextVar("attempt", default=None)
        real_compute = attempts_module.compute_attempt_application
        real_prior = attempts_module.load_attempt_prior_state

        def compute(vault, repository, attempt, **kwargs):
            token = current.set(attempt.attempt_id)
            try:
                with repository.connection() as connection:
                    self.cache[attempt.attempt_id] = tuple(tuple(row) for row in connection.execute(
                        "SELECT facet_id, capability_key, practice_item_id, recall_alpha, recall_beta, "
                        "independent_evidence_mass, raw_coverage_mass, last_observed_at, consecutive_failures "
                        "FROM facet_recall_state ORDER BY facet_id, capability_key, practice_item_id"
                    ))
                return real_compute(vault, repository, attempt, **kwargs)
            finally:
                current.reset(token)

        def prior(*args, **kwargs):
            state = real_prior(*args, **kwargs)
            attempt_id = current.get()
            if attempt_id is not None:
                self.windows[attempt_id] = (
                    tuple(row["id"] for row in state.recent_learning_object_attempts),
                    tuple(row["id"] for row in state.recent_practice_item_attempts),
                )
            return state

        monkeypatch.setattr(attempts_module, "compute_attempt_application", compute)
        monkeypatch.setattr(attempts_module, "load_attempt_prior_state", prior)

    def snapshot(self):
        return dict(self.windows), dict(self.cache)


def _three_in_one_second(vault, repository):
    """B then A on the item, then the sibling item's C (id below both) in the same second, then D a minute later."""

    _reversed_pair(vault, repository)
    _self_graded_apply(vault, repository, SIBLING_ITEM, FULL, attempt_id="01ZZZZZZZZZZZZZZZZZZZZZZZ0", when=T)
    _self_graded_apply(vault, repository, ITEM, FULL, attempt_id="01ZZZZZZZZZZZZZZZZZZZZZZZD",
                       when=T + timedelta(minutes=1))


def test_at_the_tag_each_replayed_attempt_sees_the_windows_and_cache_its_live_write_saw(tmp_path, monkeypatch):
    paths, vault, repository = _vault(tmp_path, AT)
    seen = _Seen(monkeypatch)
    _three_in_one_second(vault, repository)
    live_windows, live_cache = seen.snapshot()
    # Live, each write saw every attempt applied before it, newest applied first.
    assert live_windows[B_ID] == ((), ())
    assert live_windows[A_ID] == ((B_ID,), (B_ID,))
    assert live_windows["01ZZZZZZZZZZZZZZZZZZZZZZZ0"][0] == (A_ID, B_ID)
    assert live_windows["01ZZZZZZZZZZZZZZZZZZZZZZZD"] == (("01ZZZZZZZZZZZZZZZZZZZZZZZ0", A_ID, B_ID), (A_ID, B_ID))

    replay_module.replay_learning_object(vault, repository, _lo(vault))
    replay_windows, replay_cache = seen.snapshot()

    assert replay_windows == live_windows
    assert replay_cache == live_cache


def test_below_the_tag_the_replayed_windows_follow_the_ids(tmp_path, monkeypatch):
    # The predecessor's boundary, kept below the tag: replay hands B the miss A as its history, which live never did.
    paths, vault, repository = _vault(tmp_path, BEFORE)
    seen = _Seen(monkeypatch)
    _reversed_pair(vault, repository)
    live_windows, _ = seen.snapshot()
    replay_module.replay_learning_object(vault, repository, _lo(vault))
    replay_windows, _ = seen.snapshot()
    assert live_windows[B_ID] == ((), ()) and replay_windows[B_ID] == ((A_ID,), (A_ID,))
    assert live_windows[A_ID] == ((B_ID,), (B_ID,)) and replay_windows[A_ID] == ((), ())


@pytest.mark.parametrize("version", [BEFORE, AT])
def test_distinct_seconds_replay_alike_at_both_tags(tmp_path, monkeypatch, version):
    # The control: one second apart, the ids reversed as above. Occurrence time orders them at both tags, so the
    # windows, the cache and the rebuilt mastery are the live ones either way.
    paths, vault, repository = _vault(tmp_path, version)
    seen = _Seen(monkeypatch)
    _self_graded_apply(vault, repository, ITEM, FULL, attempt_id=B_ID, when=T)
    _self_graded_apply(vault, repository, ITEM, NONE, attempt_id=A_ID, when=T + timedelta(seconds=1))
    live = (_mastery(repository), *seen.snapshot())
    replay_module.replay_learning_object(vault, repository, _lo(vault))
    assert (_mastery(repository), *seen.snapshot()) == live
    order = attempt_order_for(vault.config)
    assert [row["id"] for row in repository.list_attempts_by_learning_object(_lo(vault), order=order)] == [B_ID, A_ID]


# -- the upgrade: legacy rows keep the predecessor's order, labelled unknown --------------------------------------


def test_the_upgrade_ranks_legacy_attempts_in_id_order_then_new_ones_follow_in_application_order(tmp_path):
    paths, vault, repository = _vault(tmp_path, BEFORE)
    _reversed_pair(vault, repository)
    predecessor_live = _mastery(repository)

    result = upgrade(paths.root, to=AT)
    assert result.upgraded, result.problems
    vault = load_vault(paths.root)
    # The real order (B then A) was never recorded: the legacy rank is the predecessor's (A, B), labelled unknown,
    # and the rebuild under the tag reads it, so the live row the predecessor left is normalized to it.
    assert _sequences(repository) == [
        (A_ID, 1, BASIS_LEGACY_ORDER_UNKNOWN, AT), (B_ID, 2, BASIS_LEGACY_ORDER_UNKNOWN, AT)]
    upgraded = _mastery(repository)
    assert upgraded != predecessor_live
    assert _shadow_summary(paths)["summary"] == ZERO

    # A new attempt in the same second, with an id below both: applied last, so it folds last.
    new_id = "01ZZZZZZZZZZZZZZZZZZZZZZZ0"
    _self_graded_apply(vault, repository, ITEM, FULL, attempt_id=new_id, when=T)
    assert _sequences(repository)[-1] == (new_id, 3, BASIS_APPLIED, AT)
    assert [row["id"] for row in repository.list_attempts_by_learning_object(_lo(vault), order=APPLICATION_ORDER)] == [
        A_ID, B_ID, new_id]
    live = _mastery(repository)
    rebuild_all_derived_state(vault, repository)
    assert _mastery(repository) == live
    assert _shadow_summary(paths)["summary"] == ZERO

    # A second upgrade does nothing: the rebuild's receipt is the activation's.
    again = upgrade(paths.root, to=AT)
    assert not again.upgraded and again.problems == [f"vault is already {AT}"]
    assert len(_sequences(repository)) == 3


# -- the other prefix readers ------------------------------------------------------------------------------------


@pytest.mark.parametrize("version, first", [(BEFORE, A_ID), (AT, B_ID)])
def test_the_field_fsrs_history_chains_a_tie_in_the_ledgers_order(tmp_path, version, first):
    # Each item's reviews chain through FSRS in order: the first has no memory yet, so no prediction. Below the tag the
    # lower id is first; at the tag the grade applied first is, as the live schedule chained them.
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.field.outcomes import fsrs_predicted_retrievability

    paths, vault, repository = _vault(tmp_path, version)
    _reversed_pair(vault, repository)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        predicted = fsrs_predicted_retrievability(connection, vault, repository)
    assert first not in predicted and ({A_ID, B_ID} - {first}) <= set(predicted)


@pytest.mark.parametrize("version, order", [(BEFORE, [A_ID, B_ID]), (AT, [B_ID, A_ID])])
def test_adaptive_difficultys_replay_gives_the_first_surface_to_the_first_in_the_ledgers_order(tmp_path, version, order):
    from contextlib import closing

    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.db.connection import connect

    paths, vault, repository = _vault(tmp_path, version)
    _reversed_pair(vault, repository)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        events = RP.load_events(connection, vault, repository, settings=RP.ReplaySettings.from_config(vault.config))
    assert [event.attempt_id for event in events.attempts] == order
    assert [event.first_surface for event in events.attempts] == [True, False]
    assert [event.attempt_id for kind, event in events.ordered() if kind == "attempt"] == order
    assert (events.attempt_sequences is None) is (version == BEFORE)


def test_adaptive_difficultys_stream_keeps_attempts_before_claims_and_opportunities_at_one_time():
    from types import SimpleNamespace

    from learnloop.adaptive_difficulty.replay import Events

    def attempt(attempt_id):
        return SimpleNamespace(attempt_id=attempt_id, at=1.0)

    claim = SimpleNamespace(claim_id="0claim", at=1.0)
    opportunity = SimpleNamespace(opportunity_id="0opportunity", at=1.0)
    for sequences, expected in ((None, ["A", "B"]), ({"A": 2, "B": 1}, ["B", "A"])):
        events = Events([attempt("A"), attempt("B")], [claim], [opportunity], None, {}, {},
                        attempt_sequences=sequences)
        stream = events.ordered()
        assert [kind for kind, _ in stream] == ["attempt", "attempt", "claim", "opportunity"]
        assert [event.attempt_id for kind, event in stream if kind == "attempt"] == expected


def test_the_family_memory_fold_breaks_a_tie_by_the_ledgers_order():
    from types import SimpleNamespace

    from learnloop.substrate.family_memory import in_fold_order

    def row(attempt_id, observed_at):
        return SimpleNamespace(attempt_id=attempt_id, features=SimpleNamespace(observed_at=observed_at))

    rows = [row("C", T + timedelta(seconds=1)), row("B", T), row("A", T)]
    assert [r.attempt_id for r in in_fold_order(rows, LEGACY_ORDER, {})] == ["A", "B", "C"]
    assert [r.attempt_id for r in in_fold_order(rows, APPLICATION_ORDER, {"B": 1, "A": 2, "C": 3})] == ["B", "A", "C"]


@pytest.mark.parametrize("version, order", [(BEFORE, [A_ID, B_ID]), (AT, [B_ID, A_ID])])
def test_the_facet_timeline_walks_the_attempts_in_the_projections_order(tmp_path, version, order):
    from learnloop.learner.facet_evidence_timeline import load_facet_timeline_snapshot

    paths, vault, repository = _vault(tmp_path, version)
    _reversed_pair(vault, repository)
    snapshot = load_facet_timeline_snapshot(repository, projection_version=version)
    assert [attempt["id"] for attempt in snapshot.attempts] == order
    assert snapshot.order == attempt_order_for(vault.config)
    assert snapshot.application_sequences == ({} if version == BEFORE else {B_ID: 1, A_ID: 2})
