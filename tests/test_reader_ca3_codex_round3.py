"""Reader CA3, Codex final verify (codex-job 20261027-190623-5y4LdE): F10 (reopened) and F12.

* F10: a comparison that was not stored (its comparison step skipped or
  unavailable, or fewer than two books) may show more passages than any
  request bound: an anchor of 40 blocks and one passage per book. The server
  records every passage such a comparison showed under its own id
  (``passagesId``), so the tutor about it names that id and reads them all,
  as it does a stored comparison's (``comparisonId``).
* F12: refining a comparison runs a new job under the same ask. A job that
  was cancelled or superseded (a newer comparison of the ask started) never
  rebinds the ask: the comparison shown keeps resolving, for the tutor and
  for Keep, whenever the older job finishes.

Every model is a fake (no network).
"""
from __future__ import annotations

import threading

import pytest
from pydantic import ValidationError

from learnloop_sidecar.errors import SidecarError
from tests.library_ask_fixtures import build_library_vault, call, context, finish_job, set_config, tutor_with_citations
from tests.recap_fixtures import call as call_rpc
from tests.source_service_fakes import seed_textbook
from tests.test_reader_ca3_codex_review import QUESTION, LastWordsLLM, _third

#: The selection's own bound (ANCHOR_SPANS_MAX): the largest anchor a comparison starts from.
BLOCKS = 40


@pytest.fixture
def library(tmp_path, monkeypatch):
    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    rows = [(f"Swapping two rows changes the sign of the determinant, step {n} of the alternating "
             f"argument for rows of a matrix. " + "Each elementary row operation acts on the determinant "
             "in its own way, and a swap reverses its orientation. " * 2, 1 + n // 8) for n in range(BLOCKS)]
    spans = seed_textbook(repository, source_id="src_long", revision_id="rev_long", extraction_id="ext_long",
                          title="Long Book", units={"c1": ("Determinants and row swaps", rows)})
    _third(repository)
    import learnloop.instructional.sources as service
    import learnloop_sidecar.handlers.ai_providers as providers

    real = service.propose_comparison
    llm = LastWordsLLM()
    #: Comparisons naming these books wait here until the test releases them (F12).
    gates: dict[str, threading.Event] = {}

    def propose(*args, **kwargs):
        for source_id in kwargs.get("source_ids") or ():
            if source_id in gates:
                assert gates[source_id].wait(30), "a gated comparison was never released"
        return real(*args, client=llm, verify_client=llm, **kwargs)

    monkeypatch.setattr(service, "propose_comparison", propose)
    tutor = tutor_with_citations([])

    class Ready:
        ready = True

    monkeypatch.setattr(providers, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), tutor))
    return paths, context(paths.root), repository, spans["c1"][1:], gates


def _shown_keys(table: dict) -> list[str]:
    return list(dict.fromkeys(key for row in table["rows"] for key in (row.get("spanKeys") or [row["key"]])))


def _left_out(answer: dict) -> set[str]:
    return {f"{pin['extractionId']}:{pin['spanId']}" for pin in answer["droppedPins"]}


def _skip_the_comparison_step(monkeypatch) -> None:
    """The source_compare route is off: the service lists the passages and compares nothing."""

    import learnloop.source_retrieval.compare as compare_module

    monkeypatch.setattr(compare_module, "route_skip", lambda *a, **k: "skipped: source_compare is off")


# -- F10: an unstored comparison's passages are the server's ------------------------------------------


def test_f10_an_unstored_comparison_of_a_40_block_anchor_reaches_the_tutor_whole(library, monkeypatch):
    _paths, ctx, _repository, blocks, _gates = library
    _skip_the_comparison_step(monkeypatch)
    assert len(blocks) == BLOCKS
    table = call(ctx, "reader.library_compare", {
        "door": "selection", "question": QUESTION, "extractionId": "ext_long", "anchorSpanIds": blocks,
        "sourceIds": ["src_third"]})
    assert table["status"].startswith("skipped") and not table.get("comparisonId"), table
    shown = _shown_keys(table)
    assert len(shown) == BLOCKS + 1  # the reported scenario: 41 passages, more than any request bound
    # The passages are the server's: the comparison names them by one id.
    assert table["passagesId"]
    answer = call(ctx, "reader.library_ask_tutor", {"askId": table["askId"], "passagesId": table["passagesId"]})
    assert set(answer["groundedKeys"]) | _left_out(answer) == set(shown)
    assert answer["groundedKeys"]
    # Its keys never travel in the request: the pins keep their bound of 20.
    with pytest.raises(ValidationError):
        call(ctx, "reader.library_ask_tutor", {"askId": table["askId"], "pinnedSpanKeys": shown[:21]})


def test_f10_a_comparison_of_one_book_is_named_by_its_passages_id(library):
    _paths, ctx, _repository, blocks, _gates = library
    table = call(ctx, "reader.library_compare", {
        "door": "selection", "question": QUESTION, "extractionId": "ext_long", "anchorSpanIds": blocks,
        "sourceIds": ["src_long"]})
    assert table["status"] == "too_few_sources" and not table.get("comparisonId")
    shown = _shown_keys(table)
    assert len(shown) == BLOCKS
    answer = call(ctx, "reader.library_ask_tutor", {"askId": table["askId"], "passagesId": table["passagesId"]})
    assert set(answer["groundedKeys"]) | _left_out(answer) == set(shown)


def test_f10_a_stored_comparison_needs_no_passages_id(library):
    _paths, ctx, _repository, blocks, _gates = library
    table = call(ctx, "reader.library_compare", {
        "door": "selection", "question": QUESTION, "extractionId": "ext_long", "anchorSpanIds": blocks[:3],
        "sourceIds": ["src_third"]})
    assert table["status"] == "ok" and table["comparisonId"]
    assert "passagesId" not in table  # named by its stored id, durable across restarts


def test_f10_a_passages_id_is_its_asks_own_and_unknown_ones_are_refused(library, monkeypatch):
    paths, ctx, _repository, blocks, _gates = library
    _skip_the_comparison_step(monkeypatch)
    first = call(ctx, "reader.library_compare", {
        "door": "selection", "question": QUESTION, "extractionId": "ext_long", "anchorSpanIds": blocks[:2],
        "sourceIds": ["src_third"]})
    second = call(ctx, "reader.library_compare", {
        "door": "selection", "question": QUESTION, "extractionId": "ext_long", "anchorSpanIds": blocks[2:4],
        "sourceIds": ["src_third"]})
    with pytest.raises(SidecarError) as refused:
        call(ctx, "reader.library_ask_tutor", {"askId": second["askId"], "passagesId": first["passagesId"]})
    assert refused.value.code == "validation_error"
    with pytest.raises(SidecarError) as unknown:
        call(ctx, "reader.library_ask_tutor", {"askId": second["askId"], "passagesId": "cmpp_gone"})
    assert unknown.value.code == "validation_error"
    # A replaced sidecar keeps none: said so (compare again), never answered from other passages.
    with pytest.raises(SidecarError) as gone:
        call(context(paths.root), "reader.library_ask_tutor",
             {"askId": second["askId"], "passagesId": second["passagesId"]})
    assert gone.value.code == "not_found"
    with pytest.raises((SidecarError, ValidationError)):
        # Both names at once: one comparison is asked about.
        call(ctx, "reader.library_ask_tutor", {"askId": second["askId"], "passagesId": second["passagesId"],
                                               "comparisonId": "scmp_x"})


def test_f10_while_ca3_is_off_there_is_no_passages_id(library, monkeypatch):
    paths, ctx, _repository, blocks, _gates = library
    _skip_the_comparison_step(monkeypatch)
    table = call(ctx, "reader.library_compare", {
        "door": "selection", "question": QUESTION, "extractionId": "ext_long", "anchorSpanIds": blocks[:2],
        "sourceIds": ["src_third"]})
    set_config(paths, "reader_compare", scope_enabled=False)
    ctx = context(paths.root)
    with pytest.raises((SidecarError, ValidationError)):
        call(ctx, "reader.library_ask_tutor", {"askId": table["askId"], "passagesId": table["passagesId"]})


# -- F12: a superseded comparison job never rebinds the ask ----------------------------------------------


def _first(ctx, blocks) -> dict:
    table = call(ctx, "reader.library_compare", {
        "door": "selection", "question": QUESTION, "extractionId": "ext_long", "anchorSpanIds": blocks[:2]})
    assert table["comparisonId"], table
    return table


def _refine(ctx, ask_id: str, source_ids: list[str]) -> dict:
    return call_rpc(ctx, "reader.library_compare", {"door": "refine", "askId": ask_id, "sourceIds": source_ids})


@pytest.mark.parametrize("cancelled", [True, False], ids=["cancelled", "superseded"])
def test_f12_an_older_refinement_finishing_last_leaves_the_shown_comparison_bound(library, cancelled):
    _paths, ctx, _repository, blocks, gates = library
    ask_id = _first(ctx, blocks)["askId"]
    gates["src_third"] = threading.Event()
    slow = _refine(ctx, ask_id, ["src_third"])  # refinement A: waits
    assert slow["state"] == "pending"
    if cancelled:
        # What the Reader does when the books change again: A is cancelled, B started.
        call_rpc(ctx, "reader.library_job_cancel", {"jobId": slow["jobId"]})
    shown = finish_job(ctx, _refine(ctx, ask_id, ["src_text"]))  # refinement B: shown
    assert shown["comparisonId"], shown
    gates["src_third"].set()
    job = ctx.library_ask_jobs.get(slow["jobId"])
    assert job.done.wait(30)
    # A never answers (cancelled, or superseded by B) ...
    assert call_rpc(ctx, "reader.library_job", {"jobId": slow["jobId"]})["state"] == "cancelled"
    # ... and never rebinds the ask: B's comparison still resolves, for the tutor and for Keep.
    answer = call(ctx, "reader.library_ask_tutor", {"askId": ask_id, "comparisonId": shown["comparisonId"]})
    assert answer["groundedKeys"]
    kept = call_rpc(ctx, "reader.library_compare_keep", {"askId": ask_id, "comparisonId": shown["comparisonId"]})
    assert kept["kept"]["keptAt"], kept  # kept, not refused as a comparison the ask no longer shows


def test_f12_a_refinement_that_finishes_unsuperseded_binds_as_before(library):
    _paths, ctx, _repository, blocks, _gates = library
    first = _first(ctx, blocks)
    refined = finish_job(ctx, _refine(ctx, first["askId"], ["src_text"]))
    assert refined["comparisonId"] and refined["comparisonId"] != first["comparisonId"]
    # The ask shows the newer comparison; the older one is no longer the ask's.
    answer = call(ctx, "reader.library_ask_tutor", {"askId": first["askId"], "comparisonId": refined["comparisonId"]})
    assert answer["groundedKeys"]
    with pytest.raises(SidecarError):
        call(ctx, "reader.library_ask_tutor", {"askId": first["askId"], "comparisonId": first["comparisonId"]})
