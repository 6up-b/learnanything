"""What other test files use from ``tests/test_contamination_report.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import report_call_usage
from learnloop.ai.spend import SpendCaps
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import put_vector
from learnloop.ops.contamination.judge import ContaminationJudgment
from learnloop.ops.contamination.recipes import CONTAMINATION_RECIPES
from learnloop.ops.contamination.report import contamination_report
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import create_basic_vault


BASIC_ITEM = "pi_svd_define_001"
PARAPHRASE = "It splits any matrix into an orthogonal factor, a diagonal scaling and another orthogonal factor."
LEARNER_QUESTION = "PRIVATE LEARNER QUESTION about my exam"


class Judge:
    provider_name = "fake"
    provider_type = "openai_chat"
    model = "fake-judge"

    def __init__(self, verdict="contaminated", *, fail_at=None):
        self.verdict = verdict
        self.fail_at = fail_at
        self.calls = []

    def supports(self, capability):
        return capability in {"structured_completion", "bounded_structured_completion", "isolated_turn"}

    def complete(self, request):
        self.calls.append(request)
        assert request.isolated and request.output_budget_tokens == 16_384  # the shared policy budget
        report_call_usage({"input_tokens": 10, "output_tokens": 20, "resolved_model": "fake-resolved"})
        if self.fail_at == len(self.calls):
            raise AIProviderUnavailable("PRIVATE provider detail")
        verdict = self.verdict(request) if callable(self.verdict) else self.verdict
        return ContaminationJudgment(
            verdict=verdict, rationale=f"judged {verdict}",
            revealed="orthogonal factor" if verdict == "contaminated" else "",
        )


def _item(loaded, item_id, *, prompt, expected, origin="codex_proposal"):
    base = loaded.practice_items[BASIC_ITEM]
    item = base.model_copy(update={
        "id": item_id, "prompt": prompt, "expected_answer": expected,
        "provenance": base.provenance.model_copy(update={"origin": origin}),
    })
    upsert_practice_item(loaded.root, item)


def _answer(repository, item_id, answer, *, context="practice", leak_suspected=False, overlap=0.0,
            created_at="2026-05-19T12:00:00+00:00", source_context=None):
    event_id = repository.insert_question_event({
        "context": context, "practice_item_id": item_id, "question_md": LEARNER_QUESTION,
        "answer_md": answer, "question_type": "mechanism", "answer_status": "answered",
        "leak_suspected": leak_suspected, "created_at": created_at,
    })
    repository.update_question_event_answer(
        event_id, answer_md=answer, question_type="mechanism", facets=[], hint_equivalent=True,
        leak_suspected=leak_suspected, answer_status="answered", leak_overlap=overlap,
        source_context=source_context,
    )
    return event_id


def _vectors(loaded, repository, recipe, vectors):
    """Place fake vectors for the CURRENT content hash of each named record."""
    records = {record.record_id: record for record in CONTAMINATION_RECIPES[recipe].records(loaded)}
    with repository.connection() as connection:
        for record_id, vector in vectors.items():
            record = records[record_id]
            put_vector(
                connection, record_kind=record.record_kind, record_id=record_id, field=record.field,
                content_hash=record.content_hash, model_id=loaded.config.embedding.model,
                task_prefix="retrieval-document", vector=vector,
            )


def run(loaded, client, **kwargs):
    """No noise-floor repeats unless a test asks: call counts stay per pair."""
    return contamination_report(
        loaded, client=client, caps=kwargs.pop("caps", SpendCaps(max_total_tokens=1_000_000)),
        price_per_million=kwargs.pop("price_per_million", 1.0),
        repeat_sample=kwargs.pop("repeat_sample", 0), **kwargs,
    )


@pytest.fixture
def tutor_vault(tmp_path):
    """Three items; one paraphrased tutor leak the lexical floor misses."""
    paths = create_basic_vault(tmp_path / "vault")
    loaded = load_vault(paths.root)
    _item(loaded, "pi_trace", prompt="Define the trace.", expected="The sum of the diagonal entries.")
    _item(loaded, "pi_rank", prompt="Define rank.", expected="The dimension of the column space.")
    loaded = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    event = _answer(repository, BASIC_ITEM, PARAPHRASE)
    _vectors(loaded, repository, "item/expected_answer", {
        BASIC_ITEM: [1.0, 0.0, 0.0], "pi_trace": [0.0, 1.0, 0.0], "pi_rank": [0.0, 0.0, 1.0],
    })
    _vectors(loaded, repository, "question_event/answer", {event: [0.9, 0.05, 0.05]})
    return paths, loaded, repository, event
