"""Reader quick-check producer: authoring, idempotency, guide-plan fallback,
and escalation into a real PracticeItem (spec_reader_quick_check_producer.md)."""

from __future__ import annotations

import json

from learnloop.codex.schemas import ReadingQuickCheck
from learnloop.services import reader_quick_check as RQC
from learnloop.services.reader_guidance import build_guide_plan
from learnloop.vault.loader import load_vault

import pytest

from tests.test_reader_guidance import _place_question, _setup


class FakeClient:
    def __init__(self, result: ReadingQuickCheck | None = None) -> None:
        self.calls: list = []
        self.result = result or ReadingQuickCheck(
            question_md="Why are the columns of U and V orthonormal?",
            expected_answer_md="Because the SVD factors A into orthogonal U and V; their columns form orthonormal bases.",
            span_ids=["s1", "s2"],
        )

    def run_reading_quick_check(self, context):
        self.calls.append(context)
        return self.result


def test_author_quick_check_persists_span_grounded_row(tmp_path):
    _vault, repository = _setup(tmp_path)
    client = FakeClient()

    row = RQC.author_quick_check(
        repository, client, extraction_id="ext1", section_id="u1"
    )

    assert row["status"] == "proposed"
    assert row["section_id"] == "u1"
    assert row["source_id"] == "src1"
    assert json.loads(row["span_ids_json"]) == ["s1", "s2"]
    # The section view fed the model only readable section blocks with span ids.
    context = client.calls[0]
    provided = {block["span_id"] for block in context.section["blocks"]}
    assert provided == {"s0", "s1", "s2"}


def test_author_quick_check_rejects_invented_spans(tmp_path):
    _vault, repository = _setup(tmp_path)
    client = FakeClient(
        ReadingQuickCheck(question_md="Q?", expected_answer_md="A.", span_ids=["s99"])
    )

    with pytest.raises(RQC.ReaderQuickCheckError, match="no valid section spans"):
        RQC.author_quick_check(repository, client, extraction_id="ext1", section_id="u1")
    assert repository.latest_reader_authored_question(
        extraction_id="ext1", section_id="u1"
    ) is None


def test_author_quick_check_is_idempotent_per_section(tmp_path):
    _vault, repository = _setup(tmp_path)
    client = FakeClient()

    first = RQC.author_quick_check(repository, client, extraction_id="ext1", section_id="u1")
    second = RQC.author_quick_check(repository, client, extraction_id="ext1", section_id="u1")

    assert second["id"] == first["id"]
    assert len(client.calls) == 1


def test_guide_plan_falls_back_to_authored_question(tmp_path):
    vault, repository = _setup(tmp_path)
    RQC.author_quick_check(repository, FakeClient(), extraction_id="ext1", section_id="u1")

    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    question = plan["sections"][0]["question"]

    assert question["placement"] == "auto_authored"
    assert question["practice_item_id"] is None
    assert question["authored_question_id"].startswith("raq_")
    assert question["prompt"].startswith("Why are the columns")
    assert question["span_ids"] == ["s1", "s2"]
    # Escalation defaults to the section's strongest source-grounded passage LO.
    assert question["escalation_learning_object_id"] == "lo_svd_definition"


def test_owner_reviewed_placement_wins_over_authored(tmp_path):
    vault, repository = _setup(tmp_path)
    _place_question(repository)
    RQC.author_quick_check(repository, FakeClient(), extraction_id="ext1", section_id="u1")

    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    question = plan["sections"][0]["question"]

    assert question["placement"] == "owner_reviewed"
    assert question["practice_item_id"] == "pi_svd_define_001"


def test_dismissed_question_suppresses_reauthoring_and_display(tmp_path):
    vault, repository = _setup(tmp_path)
    client = FakeClient()
    row = RQC.author_quick_check(repository, client, extraction_id="ext1", section_id="u1")

    RQC.record_action(repository, question_id=row["id"], action="dismissed")
    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    assert plan["sections"][0]["question"] is None

    reused = RQC.author_quick_check(repository, client, extraction_id="ext1", section_id="u1")
    assert reused["id"] == row["id"]
    assert reused["status"] == "dismissed"
    assert len(client.calls) == 1


def test_record_answer_stamps_response_on_the_row(tmp_path):
    _vault, repository = _setup(tmp_path)
    row = RQC.author_quick_check(repository, FakeClient(), extraction_id="ext1", section_id="u1")

    updated = RQC.record_action(
        repository, question_id=row["id"], action="answered",
        response_md="They come from orthogonal factors.",
    )

    assert updated["status"] == "answered"
    assert updated["response_md"] == "They come from orthogonal factors."
    assert updated["answered_at"] is not None


def test_escalate_mints_practice_item_with_span_provenance(tmp_path):
    vault, repository = _setup(tmp_path)
    row = RQC.author_quick_check(repository, FakeClient(), extraction_id="ext1", section_id="u1")

    result = RQC.escalate(
        vault.root, repository, question_id=row["id"],
        learning_object_id="lo_svd_definition",
    )
    item_id = result["practice_item_id"]
    assert item_id.startswith("pi_reader_")
    assert result["question"]["status"] == "escalated"
    assert result["question"]["practice_item_id"] == item_id

    reloaded = load_vault(vault.root)
    item = reloaded.practice_items[item_id]
    assert item.learning_object_id == "lo_svd_definition"
    assert item.prompt.startswith("Why are the columns")
    assert item.provenance.origin == "codex_proposal"
    locators = [ref.locator for ref in item.provenance.source_refs]
    assert locators == ["span:ext1/s1", "span:ext1/s2"]

    # An escalated question leaves the guide plan (its card is a real PI now).
    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    assert plan["sections"][0]["question"] is None

    # Escalating twice is idempotent; a dismissed row cannot be escalated.
    again = RQC.escalate(
        vault.root, repository, question_id=row["id"],
        learning_object_id="lo_svd_definition",
    )
    assert again["practice_item_id"] == item_id
