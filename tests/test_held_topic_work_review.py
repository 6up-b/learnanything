"""A topic whose first set was held for a look stays ``held`` in its work row only while its questions wait: giving
or refusing the OK moves the row, in the same write as the decision, so what comes next never counts a topic as
held after its questions were looked at (``next_practice.held``).

The book and the learner's part read are ``tests/part_read_helpers.py``'s; the questions' writer marks every
question for review, as the live route did.
"""

from __future__ import annotations

import pytest

from learnloop.daily_plan.next_practice import next_practice
from learnloop.vault.loader import load_vault

from tests.part_read_helpers import SeenWriter, book_ctx, build
from tests.ux_phase1_add_source_helpers import call

STOP = ("P1", "P2", "P3", "P4")


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)


@pytest.fixture
def book(tmp_path):
    built = book_ctx(tmp_path, writer=SeenWriter(held=True))
    build(built)
    built.read(*STOP)
    return built


def _states(book) -> dict[str, str]:
    return {row["learning_object_id"]: row["state"] for row in book.claims()}


def _patch(book, topic) -> str:
    import json

    row = next(row for row in book.claims() if row["learning_object_id"] == topic)
    (patch_id,) = json.loads(row["proposal_ids_json"])
    return patch_id


def _held(book) -> dict:
    return next_practice(load_vault(book.ctx.vault.root), book.repo)["held"]


def test_the_ok_and_the_refusal_each_move_a_held_topic_on(book):
    assert _states(book) == {"lo_diagonalize_symmetric": "held", "lo_early": "held"}
    assert _held(book)["topic_count"] == 2

    call(book.ctx, "accept_proposal_items", {"patchId": _patch(book, "lo_early")})
    assert _states(book) == {"lo_diagonalize_symmetric": "held", "lo_early": "written"}
    assert _held(book) == {"topic_count": 1, "learning_object_ids": ["lo_diagonalize_symmetric"]}

    call(book.ctx, "reject_proposal_items", {"patchId": _patch(book, "lo_diagonalize_symmetric")})
    assert _states(book) == {"lo_diagonalize_symmetric": "written", "lo_early": "written"}
    assert _held(book) == {"topic_count": 0, "learning_object_ids": []}


def test_undoing_a_refusal_holds_the_topic_again(book):
    patch_id = _patch(book, "lo_early")
    call(book.ctx, "reject_proposal_items", {"patchId": patch_id})
    assert _states(book)["lo_early"] == "written"

    call(book.ctx, "reset_proposal_items", {"patchId": patch_id})

    assert _states(book)["lo_early"] == "held"
    assert "lo_early" in _held(book)["learning_object_ids"]


def test_a_topic_with_one_question_still_waiting_stays_held(book):
    patch_id = _patch(book, "lo_early")
    rows = book.repo.proposal_items(patch_id)
    # The writer gives one question per topic; a second, still waiting, is added to the same proposal.
    first = rows[0]
    with book.repo.connection() as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(proposed_patch_items)")]
        copy = dict(connection.execute("SELECT * FROM proposed_patch_items WHERE id = ?", (first["id"],)).fetchone())
        copy.update(id="item_second", client_item_id="second", target_entity_id="pi_second")
        connection.execute(f"INSERT INTO proposed_patch_items({', '.join(columns)}) "
                           f"VALUES ({', '.join('?' for _ in columns)})", [copy[column] for column in columns])
        connection.commit()

    call(book.ctx, "reject_proposal_items", {"patchId": patch_id, "itemIds": [first["id"]]})

    assert _states(book)["lo_early"] == "held"


def test_a_running_or_failed_topic_is_left_as_it_is(book):
    patch_id = _patch(book, "lo_early")
    work_id = next(row["id"] for row in book.claims() if row["learning_object_id"] == "lo_early")
    book.repo.update_topic_question_work(work_id, state="failed")

    call(book.ctx, "reject_proposal_items", {"patchId": patch_id})

    assert _states(book)["lo_early"] == "failed"
