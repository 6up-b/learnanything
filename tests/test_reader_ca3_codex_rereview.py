"""Reader CA3, Codex re-review (codex-job 20261027-184553-TESPOx): F10.

A comparison can hold more passages than a pin set: an anchor of up to 40
blocks (the selection's own bound) and one passage per compared book. The
tutor about that comparison names it (``comparisonId``): the server reads
every passage it compared from the stored comparison, so its size never meets
the pins' bound, and the tutor's context budget says what it left out. A
comparison id that is not the ask's own is refused; while CA3 is off the
tutor's request is today's exactly.

Every model is a fake (no network).
"""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from learnloop_sidecar.errors import SidecarError
from tests.library_ask_fixtures import build_library_vault, call, context, set_config, tutor_with_citations
from tests.source_service_fakes import seed_textbook
from tests.test_reader_ca3_codex_review import QUESTION, LastWordsLLM

BLOCKS = 22


@pytest.fixture
def library(tmp_path, monkeypatch):
    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    # An open book whose passage on the question runs over many blocks.
    rows = [(f"Swapping two rows changes the sign of the determinant, step {n} of the alternating "
             f"argument for rows of a matrix. " + "Each elementary row operation acts on the determinant "
             "in its own way, and a swap reverses its orientation. " * 4, 1 + n // 8) for n in range(BLOCKS)]
    spans = seed_textbook(repository, source_id="src_long", revision_id="rev_long", extraction_id="ext_long",
                          title="Long Book", units={"c1": ("Determinants and row swaps", rows)})
    import learnloop.instructional.sources as service
    import learnloop_sidecar.handlers.ai_providers as providers

    real = service.propose_comparison
    llm = LastWordsLLM()
    monkeypatch.setattr(service, "propose_comparison",
                        lambda *a, **k: real(*a, client=llm, verify_client=llm, **k))
    tutor = tutor_with_citations([])

    class Ready:
        ready = True

    monkeypatch.setattr(providers, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), tutor))
    return paths, context(paths.root), repository, spans["c1"][1:], tutor


def _compare(ctx, anchor: list[str]) -> dict:
    table = call(ctx, "reader.library_compare", {
        "door": "selection", "question": QUESTION, "extractionId": "ext_long", "anchorSpanIds": anchor})
    assert table["status"] == "ok", table
    assert table["comparisonId"]
    return table


def _left_out(answer: dict) -> set[str]:
    return {f"{pin['extractionId']}:{pin['spanId']}" for pin in answer["droppedPins"]}


def _shown_keys(table: dict) -> list[str]:
    return list(dict.fromkeys(key for row in table["rows"] for key in (row.get("spanKeys") or [row["key"]])))


def test_f10_the_tutor_reads_every_passage_of_a_comparison_larger_than_a_pin_set(library):
    _paths, ctx, repository, blocks, tutor = library
    table = _compare(ctx, blocks)
    shown = _shown_keys(table)
    assert len(shown) > 20  # the reported scenario: more passages than a pin set may hold
    answer = call(ctx, "reader.library_ask_tutor", {"askId": table["askId"], "comparisonId": table["comparisonId"]})
    # Every passage the comparison read reached the tutor, or is said to be left out.
    given = set(answer["groundedKeys"])
    left_out = _left_out(answer)
    assert given | left_out == set(shown)
    assert given, answer
    prompt = tutor.prompts[0]
    spans = json.loads(prompt[prompt.index("{"):])["context"]["source_spans"]
    assert {f"{s['extraction_id']}:{s['span_id']}" for s in spans} == given
    # The pins' bound is unchanged: a pin set is still at most twenty.
    with pytest.raises(ValidationError):
        call(ctx, "reader.library_ask_tutor", {"askId": table["askId"], "pinnedSpanKeys": shown[:21]})


def test_f10_the_tutors_context_budget_says_what_it_left_out(library):
    paths, _ctx, _repository, blocks, _tutor = library
    set_config(paths, "tutor_qa", context_token_budget=1_000)  # the schema's floor
    ctx = context(paths.root)
    table = _compare(ctx, blocks)
    answer = call(ctx, "reader.library_ask_tutor", {"askId": table["askId"], "comparisonId": table["comparisonId"]})
    over = [pin for pin in answer["droppedPins"] if pin["reason"] == "over the tutor's context budget"]
    assert over, answer["droppedPins"]
    # Nothing is lost unsaid: each passage was given (whole or trimmed) or is named as left out.
    left_out = _left_out(answer)
    assert set(answer["groundedKeys"]) | left_out == set(_shown_keys(table))
    assert set(answer["trimmedKeys"]) <= set(answer["groundedKeys"])


def test_f10_a_comparison_that_is_not_the_asks_own_is_refused(library):
    _paths, ctx, _repository, blocks, _tutor = library
    first = _compare(ctx, blocks[:2])
    second = _compare(ctx, blocks[2:4])
    with pytest.raises(SidecarError) as refused:
        call(ctx, "reader.library_ask_tutor", {"askId": second["askId"], "comparisonId": first["comparisonId"]})
    assert refused.value.code == "validation_error"
    with pytest.raises((SidecarError, ValidationError)):
        # Neither a pin nor a comparison: nothing to answer from.
        call(ctx, "reader.library_ask_tutor", {"askId": second["askId"]})


def test_f10_while_ca3_is_off_the_tutor_request_is_todays(library):
    paths, ctx, _repository, blocks, _tutor = library
    table = _compare(ctx, blocks[:2])
    set_config(paths, "reader_compare", scope_enabled=False)
    ctx = context(paths.root)
    with pytest.raises((SidecarError, ValidationError)):
        call(ctx, "reader.library_ask_tutor", {"askId": table["askId"], "comparisonId": table["comparisonId"]})
    answer = call(ctx, "reader.library_ask_tutor", {"askId": table["askId"], "pinnedSpanKeys": [table["rows"][0]["key"]]})
    assert answer["groundedKeys"]
