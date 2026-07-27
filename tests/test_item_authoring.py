"""Learner-owned item authoring (services.item_authoring): create, edit,
retire (typed reasons), split -- and the serving-path consequences (state_sync
deactivation, scheduler/exam/probe exclusion)."""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.item_authoring import (
    ItemAuthoringError,
    author_item,
    edit_item,
    retire_item,
    split_item,
)
from learnloop.services.scheduler import build_due_queue
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault, seed_due_item

CLOCK = FrozenClock(NOW)
ITEM = "pi_svd_define_001"


@pytest.fixture
def env(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    vault = load_vault(root)
    repo = seed_due_item(paths)
    sync_vault_state(vault, repo, clock=CLOCK)
    return root, repo


def test_author_item_creates_learner_card(env) -> None:
    root, repo = env
    vault = load_vault(root)
    lo_id = next(iter(vault.learning_objects))
    row = author_item(
        root,
        repo,
        learning_object_id=lo_id,
        prompt="In your own words, why do symmetric matrices have real eigenvalues?",
        expected_answer="The spectral theorem: self-adjointness forces real spectrum.",
        clock=CLOCK,
    )
    reloaded = load_vault(root)
    item = reloaded.practice_items[row["id"]]
    assert item.provenance.origin == "human"
    assert item.status == "active"
    # The learner-authored card enters the serving path after a sync.
    sync_vault_state(reloaded, repo, clock=CLOCK)
    states = repo.practice_item_states()
    assert states[row["id"]].active


def test_author_item_validates(env) -> None:
    root, repo = env
    with pytest.raises(ItemAuthoringError):
        author_item(root, repo, learning_object_id="lo_missing", prompt="p", expected_answer="a")
    vault = load_vault(root)
    lo_id = next(iter(vault.learning_objects))
    with pytest.raises(ItemAuthoringError):
        author_item(root, repo, learning_object_id=lo_id, prompt="  ", expected_answer="a")


def test_edit_item_rewords_in_place(env) -> None:
    root, repo = env
    result = edit_item(
        root, repo, practice_item_id=ITEM, prompt="A sharper prompt?", reason="off-target wording"
    )
    assert result["changed"] == ["prompt"]
    assert load_vault(root).practice_items[ITEM].prompt == "A sharper prompt?"
    with pytest.raises(ItemAuthoringError):
        edit_item(root, repo, practice_item_id=ITEM, prompt="A sharper prompt?")  # no-op


def test_retire_item_stops_all_serving(env) -> None:
    root, repo = env
    vault = load_vault(root)
    assert any(e.practice_item_id == ITEM for e in build_due_queue(vault, repo, clock=CLOCK))

    retire_item(
        root, repo, practice_item_id=ITEM, reason="knew_prompt_not_concept", note="just parroting"
    )
    reloaded = load_vault(root)
    item = reloaded.practice_items[ITEM]
    assert item.status == "retired"
    assert item.status_reason == "knew_prompt_not_concept: just parroting"
    # Immediately excluded from the queue (independent of sync ordering) ...
    assert not any(e.practice_item_id == ITEM for e in build_due_queue(reloaded, repo, clock=CLOCK))
    # ... and the narrow write deactivates scheduler state immediately without
    # waiting for a global replay.
    assert not repo.practice_item_states()[ITEM].active
    sync_vault_state(reloaded, repo, clock=CLOCK)
    assert not repo.practice_item_states()[ITEM].active

    with pytest.raises(ItemAuthoringError):
        retire_item(root, repo, practice_item_id=ITEM, reason="because")


def test_retire_item_reuses_loaded_vault_and_clears_serving_backdoors(
    env, monkeypatch
) -> None:
    root, repo = env
    vault = load_vault(root)
    session_id = repo.create_session(energy="medium", available_minutes=25, clock=CLOCK)
    repo.update_session_checkpoint(
        session_id,
        current_practice_item_id=ITEM,
        current_answer="unfinished answer",
        clock=CLOCK,
    )
    task = repo.create_followup_task(
        kind="cold_retry",
        case_kind="diagnosis",
        case_ref="diagnosis_1",
        not_before=NOW_ISO,
        selected_item_id=ITEM,
        clock=CLOCK,
    )
    assert repo.surfaces_for_legacy_practice_item(ITEM) == []

    # The latency seam is contractual: an interactive caller that already owns
    # a validated snapshot must not reparse the vault in either service layer.
    import learnloop.services.item_authoring as authoring_module
    import learnloop.vault.writer as writer_module

    monkeypatch.setattr(
        authoring_module,
        "load_vault",
        lambda _root: pytest.fail("retirement reparsed the vault"),
    )
    monkeypatch.setattr(
        writer_module,
        "load_vault",
        lambda _root: pytest.fail("writer reparsed the vault"),
    )

    result = retire_item(
        root,
        repo,
        practice_item_id=ITEM,
        reason="no_longer_relevant",
        loaded_vault=vault,
        clock=CLOCK,
    )

    assert result["item"].status == "retired"
    assert repo.practice_item_state(ITEM).active is False
    assert repo.fetch_session_checkpoint(session_id) is None
    assert repo.followup_task(task["id"])["status"] == "expired"
    # Retirement mirrors existing substrate state; it must never mint a surface
    # just so there is something to retire.
    assert repo.surfaces_for_legacy_practice_item(ITEM) == []


def test_split_item_retires_original_and_links_parts(env) -> None:
    root, repo = env
    result = split_item(
        root,
        repo,
        practice_item_id=ITEM,
        parts=[
            {"prompt": "What does SVD factor a matrix into?", "expected_answer": "U S V^T"},
            {"prompt": "What is special about S?", "expected_answer": "Nonnegative diagonal singular values"},
        ],
    )
    assert len(result["created"]) == 2
    reloaded = load_vault(root)
    original = reloaded.practice_items[ITEM]
    assert original.status == "retired"
    assert original.status_reason.startswith("wrong_granularity")
    for new_id in result["created"]:
        child = reloaded.practice_items[new_id]
        assert child.status == "active"
        assert child.learning_object_id == original.learning_object_id
        assert child.evidence_facets == original.evidence_facets

    with pytest.raises(ItemAuthoringError):
        split_item(root, repo, practice_item_id=ITEM, parts=[{"prompt": "p", "expected_answer": "a"}])
