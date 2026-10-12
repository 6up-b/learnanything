"""Daily-loop follow-up: retiring a reader question left its practice card served.

The reader's "retire" (``reader.maintain`` action ``retire``) appended a
``retired`` event to the question's commitment and nothing else, so the practice
item the question had been adopted into stayed in the queue as ordinary practice.
Retiring the question now retires its linked item through the existing learner
retire path (``item_authoring.retire_item``): the item leaves the queue, its
derived serving doors close, and its substrate surface work is made obsolete.
The reader has no un-retire verb, so there is nothing to restore.
"""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.reader import reader_authoring as AUTH
from learnloop.vault.loader import load_vault

from tests.test_daily_loop_reader_authored_practice import (
    ANSWER,
    CLOCK,
    QUESTION,
    _author,
    _queue_ids,
    _reader_vault,
)


def test_retiring_a_reader_question_retires_its_practice_item(tmp_path):
    paths = _reader_vault(tmp_path)
    saved = _author(paths)
    item_id = saved["practice_item_id"]
    assert item_id in _queue_ids(paths), "sanity: the adopted card is served"
    repository = Repository(paths.sqlite_path)

    result = AUTH.maintain(
        repository, action="retire", commitment_id=saved["commitment_id"], root=paths.root, clock=CLOCK
    )

    assert result["retired_practice_item_ids"] == [item_id]
    item = load_vault(paths.root).practice_items[item_id]
    assert item.status == "retired"  # history kept, never served again
    assert not repository.practice_item_state(item_id).active
    assert repository.requested_practice_item_ids() == []
    assert item_id not in _queue_ids(paths)
    # Recorded through the learner retire path, with its typed reason.
    assert item.status_reason.startswith("no_longer_relevant")
    assert repository.reader_interaction_events(kind="learner_item_retired", subject_id=item_id)


def test_retiring_a_reference_only_question_retires_nothing_else(tmp_path):
    paths = _reader_vault(tmp_path, cite_span=False)
    saved = _author(paths)
    result = AUTH.maintain(
        Repository(paths.sqlite_path), action="retire", commitment_id=saved["commitment_id"],
        root=paths.root, clock=CLOCK,
    )
    assert result["retired_practice_item_ids"] == []


def test_sidecar_retire_takes_the_card_out_of_today(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    def call(ctx, name, params):
        spec = METHOD_REGISTRY[name]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    def served(ctx):
        queue = call(ctx, "get_today_queue", {})
        return [item["practiceItemId"] for section in queue["sections"] for item in section["items"]]

    paths = _reader_vault(tmp_path)
    toml = paths.root / "learnloop.toml"
    text = toml.read_text(encoding="utf-8")
    toml.write_text(
        text.replace("reader_enabled = false", "reader_enabled = true")
        if "reader_enabled" in text
        else text + "\n[tutor_qa]\nreader_enabled = true\n",
        encoding="utf-8",
    )
    ctx = SidecarContext()
    ctx.load(paths.root)
    saved = call(ctx, "reader.author_qa", {
        "question": QUESTION, "answer": ANSWER, "sourceId": "src1", "revisionId": "rev1",
        "subjectId": "span:ext1/s2", "clientIdempotencyKey": "retire-1",
    })
    assert saved["practiceItemId"] in served(ctx)

    call(ctx, "reader.maintain", {"action": "retire", "commitmentId": saved["commitmentId"]})

    assert saved["practiceItemId"] not in served(ctx)
