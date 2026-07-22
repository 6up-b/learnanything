"""P4 §14.2 step 3 -- commitment-scoped controller ownership (design §A.2 / §C).

Covers: staged owns P2 golden-path commitments; legacy is the default owner; a non-P2
commitment is refused staged ownership; transitions are append-only with receipts; the
legacy scheduler EXCLUDES staged-owned items from its queue; rollback returns owned
commitments to legacy atomically with a receipt and restores the legacy queue exactly.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import commitments as C
from learnloop.services import controller_ownership as own
from learnloop.services.scheduler import SchedulerSession, build_due_queue
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, seed_due_item

CLOCK = FrozenClock(NOW)


@pytest.fixture
def wired(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=CLOCK)
    seed_due_item(paths)
    vault = load_vault(root)
    return vault, repo


def _p2_commitment(repo, vault, *, goal_id="g1"):
    item = next(iter(vault.practice_items.values()))
    commitment = C.create_commitment(
        repo, action="select_exemplar", intent_text="master this",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": item.id, "role": "required"}],
        depth_preset="master_tasks_like_these", goal_id=goal_id, clock=CLOCK,
    )
    return commitment.id, item.id


def test_default_owner_is_legacy(wired):
    vault, repo = wired
    cid, _ = _p2_commitment(repo, vault)
    assert own.resolve_owner(repo, cid) == own.LEGACY
    assert not own.is_staged_owned(repo, cid)


def test_p2_commitment_assigned_to_staged_with_receipt(wired):
    vault, repo = wired
    cid, _ = _p2_commitment(repo, vault)
    receipt = own.assign_p2_run(repo, commitment_id=cid, clock=CLOCK)
    assert receipt["changed"] is True and receipt["owner"] == own.STAGED
    assert own.is_staged_owned(repo, cid)
    events = own.ownership_events(repo, cid)
    assert len(events) == 1
    assert events[0]["to_owner"] == own.STAGED
    assert events[0]["from_owner"] is None
    assert events[0]["receipt_id"] == receipt["receipt_id"]


def test_non_p2_commitment_refused_staged_ownership(wired):
    vault, repo = wired
    # No goal contract -> not a P2 golden-path commitment.
    cid, _ = _p2_commitment(repo, vault, goal_id=None)
    with pytest.raises(own.NotAP2GoldenPathCommitment):
        own.assign_p2_run(repo, commitment_id=cid, clock=CLOCK)
    assert own.resolve_owner(repo, cid) == own.LEGACY


def test_assign_is_idempotent_and_append_only(wired):
    vault, repo = wired
    cid, _ = _p2_commitment(repo, vault)
    own.assign_p2_run(repo, commitment_id=cid, clock=CLOCK)
    again = own.assign(repo, commitment_id=cid, owner=own.STAGED, reason="repeat", clock=CLOCK)
    assert again["changed"] is False
    assert len(own.ownership_events(repo, cid)) == 1  # no churn on a no-op re-assign


def test_legacy_scheduler_excludes_staged_owned_items(wired):
    vault, repo = wired
    cid, item_id = _p2_commitment(repo, vault)
    session = SchedulerSession(session_id="s1", available_minutes=30)

    before = build_due_queue(vault, repo, session=session, clock=CLOCK, persist_explanations=False)
    assert any(i.practice_item_id == item_id for i in before), "item should be in the legacy queue pre-ownership"

    own.assign_p2_run(repo, commitment_id=cid, clock=CLOCK)
    assert item_id in own.staged_owned_practice_item_ids(vault, repo)

    after = build_due_queue(vault, repo, session=session, clock=CLOCK, persist_explanations=False)
    assert not any(i.practice_item_id == item_id for i in after), "staged-owned item must be excluded from the legacy queue"


def test_rollback_returns_to_legacy_and_restores_queue(wired):
    vault, repo = wired
    cid, item_id = _p2_commitment(repo, vault)
    session = SchedulerSession(session_id="s1", available_minutes=30)
    own.assign_p2_run(repo, commitment_id=cid, clock=CLOCK)
    assert own.is_staged_owned(repo, cid)

    receipt = own.rollback_to_legacy(repo, reason="test_rollback", clock=CLOCK)
    assert receipt["count"] == 1
    assert receipt["transitioned"][0]["to_owner"] == own.LEGACY
    assert own.resolve_owner(repo, cid) == own.LEGACY
    # The legacy queue is restored exactly: the item is schedulable again.
    after = build_due_queue(vault, repo, session=session, clock=CLOCK, persist_explanations=False)
    assert any(i.practice_item_id == item_id for i in after)
    # History is preserved (append-only): assign + rollback are both durable.
    assert len(own.ownership_events(repo, cid)) == 2


def test_empty_ownership_is_a_noop_exclusion(wired):
    vault, repo = wired
    assert own.staged_owned_practice_item_ids(vault, repo) == set()


def test_rollback_is_all_or_nothing_on_mid_failure(wired, monkeypatch):
    # Audit L10: rollback_to_legacy transitions every owned commitment under ONE shared
    # receipt inside ONE transaction. A fault partway must roll the WHOLE batch back --
    # no commitment is half-transitioned -- and the legacy queue is byte-identical to the
    # pre-rollback queue (the items stay excluded because ownership never changed).
    vault, repo = wired
    item = next(iter(vault.practice_items.values()))
    # Two DISTINCT commitments (different targets -> not merged): one on the item, one on
    # its learning object, so rollback iterates a two-commitment batch.
    c1 = C.create_commitment(
        repo, action="select_exemplar", intent_text="own item",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": item.id, "role": "required"}],
        depth_preset="master_tasks_like_these", goal_id="g1", clock=CLOCK,
    )
    c2 = C.create_commitment(
        repo, action="select_exemplar", intent_text="own lo",
        targets=[{"target_kind": "learning_object", "target_ref": item.learning_object_id, "role": "required"}],
        depth_preset="master_tasks_like_these", goal_id="g2", clock=CLOCK,
    )
    cid1, cid2, item_id = c1.id, c2.id, item.id
    assert cid1 != cid2
    own.assign_p2_run(repo, commitment_id=cid1, clock=CLOCK)
    own.assign_p2_run(repo, commitment_id=cid2, clock=CLOCK)
    session = SchedulerSession(session_id="s1", available_minutes=30)

    before_queue = [i.practice_item_id for i in build_due_queue(
        vault, repo, session=session, clock=CLOCK, persist_explanations=False)]
    assert item_id not in before_queue  # staged-owned -> excluded pre-rollback.

    # Inject a fault on the SECOND append inside the rollback transaction.
    real_append = own._append_transition
    calls = {"n": 0}

    def flaky_append(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("injected mid-rollback fault")
        return real_append(*args, **kwargs)

    monkeypatch.setattr(own, "_append_transition", flaky_append)
    with pytest.raises(RuntimeError):
        own.rollback_to_legacy(repo, reason="faulty", clock=CLOCK)

    # All-or-nothing: BOTH commitments remain staged; no half-applied transition persisted.
    assert own.resolve_owner(repo, cid1) == own.STAGED
    assert own.resolve_owner(repo, cid2) == own.STAGED
    assert len(own.ownership_events(repo, cid1)) == 1
    assert len(own.ownership_events(repo, cid2)) == 1

    # Queue-equality restore: the failed rollback left the legacy queue exactly as it was.
    after_queue = [i.practice_item_id for i in build_due_queue(
        vault, repo, session=session, clock=CLOCK, persist_explanations=False)]
    assert after_queue == before_queue


def test_rebuild_ownership_head_reconstructs_from_events(wired):
    # Audit L1/D3: the head is a rebuildable projection of the append-only events. After a
    # corrupted / dropped head, rebuild_ownership_head folds the events back to the exact
    # standing owner + version. Pre-fix no such rebuild existed, so the "rebuildable
    # projection head" claim was unbacked.
    vault, repo = wired
    cid, _ = _p2_commitment(repo, vault)
    own.assign_p2_run(repo, commitment_id=cid, clock=CLOCK)          # -> staged (v1)
    own.rollback_to_legacy(repo, reason="rb", clock=CLOCK)           # -> legacy (v2)
    truth = own.ownership_head(repo, cid)
    assert truth["owner"] == own.LEGACY and truth["ownership_version"] == 2

    # Corrupt the head, then rebuild: it must match the folded events exactly.
    with repo.connection() as connection:
        connection.execute(
            "UPDATE controller_ownership SET owner = ?, ownership_version = 99 WHERE commitment_id = ?",
            (own.STAGED, cid),
        )
        connection.commit()
    assert own.resolve_owner(repo, cid) == own.STAGED  # diverged from the events.

    result = own.rebuild_ownership_head(repo)
    assert result["count"] == 1
    rebuilt = own.ownership_head(repo, cid)
    assert rebuilt["owner"] == truth["owner"]
    assert rebuilt["ownership_version"] == truth["ownership_version"]
    assert rebuilt["receipt_id"] == truth["receipt_id"]

    # Dropped head is reconstructed too.
    with repo.connection() as connection:
        connection.execute("DELETE FROM controller_ownership WHERE commitment_id = ?", (cid,))
        connection.commit()
    own.rebuild_ownership_head(repo, commitment_id=cid)
    assert own.resolve_owner(repo, cid) == own.LEGACY
