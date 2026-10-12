"""Review F2: a reader question's practice card belongs to its own commitment.

Crash-safe adoption used to reuse ANY active human card with the same words
under the LO. A second identical reader question, or a card the learner wrote
independently, was then shared, and retiring one question retired practice
another commitment still requested.
"""

from __future__ import annotations

import pytest

from learnloop.content.authoring.item_authoring import author_item
from learnloop.curriculum import commitments as C
from learnloop.db.repositories import Repository
from learnloop.reader import reader_authoring as AUTH
from learnloop.vault.loader import load_vault

from tests.test_daily_loop_reader_authored_practice import (
    ANSWER,
    CLOCK,
    LO_ID,
    QUESTION,
    _author,
    _reader_vault,
)


def _status(paths, item_id):
    return load_vault(paths.root).practice_items[item_id].status


def _retire(paths, commitment_id):
    return AUTH.maintain(
        Repository(paths.sqlite_path), action="retire", commitment_id=commitment_id,
        root=paths.root, clock=CLOCK,
    )


def test_identical_questions_get_their_own_cards_and_retire_independently(tmp_path):
    paths = _reader_vault(tmp_path)
    first = _author(paths, key="qa1")
    second = _author(paths, key="qa2")
    assert first["practice_status"] == second["practice_status"] == "scheduled"
    assert first["practice_item_id"] != second["practice_item_id"]

    assert _retire(paths, first["commitment_id"])["retired_practice_item_ids"] == [
        first["practice_item_id"]]
    assert _status(paths, first["practice_item_id"]) == "retired"
    assert _status(paths, second["practice_item_id"]) == "active"


def test_an_independently_written_matching_card_is_not_captured(tmp_path):
    paths = _reader_vault(tmp_path)
    repository = Repository(paths.sqlite_path)
    own = author_item(paths.root, repository, learning_object_id=LO_ID,
                      prompt=QUESTION, expected_answer=ANSWER, clock=CLOCK)
    saved = _author(paths)
    assert saved["practice_item_id"] != own["id"]
    _retire(paths, saved["commitment_id"])
    assert _status(paths, own["id"]) == "active"


def test_crash_before_the_link_reuses_the_commitments_own_card(tmp_path, monkeypatch):
    paths = _reader_vault(tmp_path)
    original = C.add_target

    def crash(*args, **kwargs):
        raise OSError("crashed before the commitment link landed")

    monkeypatch.setattr(AUTH.C, "add_target", crash)
    with pytest.raises(OSError):
        _author(paths)
    monkeypatch.setattr(AUTH.C, "add_target", original)
    retried = _author(paths)  # the same idempotency key, as the reader retries
    cards = [item for item in load_vault(paths.root).practice_items.values() if item.prompt == QUESTION]
    assert [card.id for card in cards] == [retried["practice_item_id"]]
    targets = C.resolve_head(Repository(paths.sqlite_path), retried["commitment_id"]).targets
    assert ("legacy_practice_item", retried["practice_item_id"]) in {
        (t.target_kind, t.target_ref) for t in targets}


def test_retiring_a_question_keeps_a_card_another_commitment_still_requests(tmp_path):
    """Defence in depth for cards shared before this fix (or by any other path)."""
    paths = _reader_vault(tmp_path)
    first = _author(paths, key="qa1")
    second = _author(paths, key="qa2")
    repository = Repository(paths.sqlite_path)
    C.add_target(
        repository, commitment_id=second["commitment_id"],
        target={"target_kind": "legacy_practice_item", "target_ref": first["practice_item_id"],
                "role": "required"},
        change_reason="adopted_into_practice", clock=CLOCK,
    )
    assert _retire(paths, first["commitment_id"])["retired_practice_item_ids"] == []
    assert _status(paths, first["practice_item_id"]) == "active"
    # Once no active commitment requests it, retiring the last one retires it.
    retired = _retire(paths, second["commitment_id"])["retired_practice_item_ids"]
    assert sorted(retired) == sorted([first["practice_item_id"], second["practice_item_id"]])
