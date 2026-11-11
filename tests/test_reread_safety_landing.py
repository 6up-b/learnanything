"""Re-read safety landed onto main: the compositions (docs/reviews/reread-safety.md,
"Landing onto main").

* **Protection reaches every model-visible path.** ``learner_protection`` (the
  one protection authority for model-visible learner work, main's chat
  frontend C1a) routes exam decisions through ``exam_material``, so rule 4
  reaches the chat's ``find_sources`` and ``learning_context`` and router
  R2a's learner-state card: an unmarked reading of a protected book is held
  back whole from each of them, and an item made from it is withheld.
* **Prompt rendering.** A passage an item cited on the old reading resolves
  on the re-read through the one alias authority (``span_aliases``), and the
  margin cue's question renders with the method its contract froze
  (method-explicit items' ``answered_question``).
* **The readers get the stored original's bytes.** A re-read hands Marker's
  worker process (main's Marker pdfium worker) and GLM-OCR's transport the
  bytes of the book's own revision from the originals store, never the
  git-LFS pointer at its ``canonical_uri``.

Fakes only; no network, no model.
"""

from __future__ import annotations

import base64
import io
import json

import anyio
from mcp import Client

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop import learner_protection as protection
from learnloop.content.sources import exam_material as EM
from learnloop.ingest.hashing import asset_hash
from learnloop.ingest.ir import DocumentIR, ExtractionHealth
from learnloop.remote.runtime import RemoteRuntime
from learnloop.vault.loader import load_vault
from learnloop_mcp.server import build_server

from tests.mcp_world import LO, payload_text
from tests.reread_safety_helpers import card_book, call  # noqa: F401 -- card_book is a fixture
from tests.source_inventory_helpers import _persist
from tests.reread_safety_landing_helpers import REREAD_ANSWER, REREAD_STEM, _protect_the_first_reading
from tests.reread_safety_landing_helpers import reread_world  # noqa: F401 - fixtures, used by parameter name

REREAD_QUERY = "determinant of a triangular matrix is the product of its diagonal entries"


def _call_all(server, calls: list[tuple[str, dict]]) -> list:
    async def main():
        results = []
        async with Client(server) as client:
            for name, arguments in calls:
                results.append(await client.call_tool(name, arguments))
        return results

    return anyio.run(main)


def _card_recent_work(world) -> dict[str, dict]:
    from learnloop.daily_plan.router_card import CardGatherer
    from learnloop.daily_plan.types import BlockCandidate, PlanState

    state = PlanState(plan_id="p", kind="normal", minutes_budget=25.0, minutes_left=25.0,
                      lane_minutes_left={"maintain": 10.0}, days_since_last_activity=0, streak_days=1,
                      current_block_id=None)
    feasible = [BlockCandidate(
        candidate_id="maintain:x", lane="maintain", action="maintain", subtype=None,
        learning_object_ids=(LO,), item_ids=("pi_reread",), reading=None, est_minutes=4.0,
        planner_value=1.0, reason="review", annotations={"reason_code": "review", "reversible": True},
    )]
    inputs = CardGatherer(load_vault(world.root), world.repository, session_id="s1").inputs(
        state, feasible, now_iso="2026-10-15T09:00:00Z")
    return {entry["attempt_id"]: entry for entry in inputs.recent_work}


def _chat(server) -> tuple[dict, dict]:
    sources, context = _call_all(server, [("find_sources", {"query": REREAD_QUERY, "limit": 12}),
                                          ("learning_context", {"learning_object_ids": [LO], "max_traces": 30})])
    return sources.structured_content, context.structured_content


def test_an_unmarked_reading_of_a_protected_book_is_withheld_from_every_model_visible_path(reread_world):
    world, span = reread_world
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))

    # Before any mark the book is not protected: the re-read's passage is
    # found, and the answer made from it shows with its pinned question.
    sources, context = _chat(server)
    shown = {(p["citation"]["extraction_id"], p["citation"]["span_id"]) for p in sources["passages"]}
    assert ("ext_book_r2", span) in shown, "the control: the chat finds the re-read's passage"
    trace = {t["attempt_id"]: t for t in context["recent_answer_traces"]}["att_reread"]
    assert trace["withheld"] is None and trace["stem"] == REREAD_STEM and trace["answer"] == REREAD_ANSWER
    card = _card_recent_work(world)["att_reread"]
    assert card["withheld"] is None and card["answer"] == REREAD_ANSWER

    _protect_the_first_reading(world)
    vault = load_vault(world.root)
    # Rule 4: the book is protected and the re-read carries no exact mark, so
    # it is withheld whole; exam_material is the one predicate behind it.
    assert EM.reading_held_back(vault, world.repository, "ext_book_r2")
    verdict = EM.exam_material(vault, world.repository).verdict("ext_book_r2", span)
    assert verdict.exam and verdict.held_out and EM.UNMARKED_READING in verdict.reasons
    assert protection.withheld_items(vault, world.repository).reason("pi_reread") == protection.WITHHELD_EXAM

    # The chat's find_sources: nothing of the re-read, counted as exam material.
    sources, context = _chat(server)
    assert not [p for p in sources["passages"] if p["citation"]["extraction_id"] == "ext_book_r2"]
    assert sources["withheld"]["exam_material"] >= 1
    assert "REREAD_ONLY_7719" not in payload_text(sources)
    # The chat's learning_context: the answer keeps its result, never its words.
    trace = {t["attempt_id"]: t for t in context["recent_answer_traces"]}["att_reread"]
    assert trace["withheld"] == protection.WITHHELD_EXAM and trace["stem"] is None and trace["answer"] is None
    assert trace["result"] == "correct"
    for planted in (REREAD_STEM, REREAD_ANSWER):
        assert planted not in payload_text(context)
    # Router R2a's learner-state card: the same withholding, for the same reason.
    card = _card_recent_work(world)["att_reread"]
    assert card["withheld"] == protection.WITHHELD_EXAM and card["stem"] is None and card["answer"] is None
    assert REREAD_ANSWER not in payload_text(card)


# -- prompt rendering: aliases and the method's instruction compose -------------------------------


def test_a_cue_on_a_reread_resolves_the_cited_passage_and_shows_the_question_with_its_method(tmp_path):
    """An item cited ``s1``-``s3`` and ``s5`` on ``ext1``; the book is read
    again (``ext2``: the same text under other span ids). The Guide of the
    re-read places each cited passage through the alias authority (exact:
    ``current``, never the old span id), and the margin cue's "Open" shows the
    answered question with the frozen method's sentence whole."""

    from learnloop.content.sources.span_aliases import SpanTranslator
    from learnloop.content.pipeline.reread import carry_over
    from learnloop.reader import reader_cues as RCU
    from learnloop.reader.reader_guidance import build_guide_plan

    from tests.method_explicit_landing_helpers import LONG, METHOD, SENTENCE, _graded_attempt_under
    from tests.reader_cues_helpers import _active_error, _cue_vault, _ir

    _root, vault, repository = _cue_vault(tmp_path, error=False)
    _graded_attempt_under(repository, vault, attempt_id="att-method", prompt=LONG, method=METHOD)
    _active_error(repository, attempt_id="att-method")

    first = _ir()
    renamed = {block.span_id: f"n{block.span_id}" for block in first.blocks}
    second = DocumentIR(
        extractor="glm_ocr", extractor_version="1", assets=[], health=ExtractionHealth(),
        blocks=[block.model_copy(update={"span_id": renamed[block.span_id]}) for block in first.blocks],
        units=[unit.model_copy(update={"unit_id": f"h{unit.unit_id}",
                                       "span_ids": [renamed[s] for s in unit.span_ids]}) for unit in first.units],
    )
    _persist(repository, second, revision_id="rev1", extraction_id="ext2")
    carry_over(repository, "ext2")  # the re-read's carry: aliases recorded, progress moved

    cited = ("s1", "s2", "s3", "s5")
    translator = SpanTranslator(repository, "ext2")
    for span in cited:
        resolution = translator.resolve("ext1", span)
        assert resolution.span_id == renamed[span] and resolution.exact

    plan = build_guide_plan(vault, repository, extraction_id="ext2")
    passages = {p["span_id"]: p for section in plan["sections"] for p in section["suggested_passages"]}
    assert {renamed[span] for span in cited} == set(passages)
    assert all(passage["anchor"] == "current" for passage in passages.values())
    cues = RCU.guide_cues(vault, repository, extraction_id="ext2", plan=plan)
    assert cues["marks"], cues
    for mark in cues["marks"]:
        assert mark["span_id"] in {renamed[span] for span in cited}
        prompt = mark["earlier"]["prompt"]
        assert prompt.endswith(" " + SENTENCE) and len(prompt) <= RCU.MAX_PROMPT_CHARS
        assert prompt.startswith("Let A be the 2 by 2 matrix")


# -- the readers get the stored original's bytes on a re-read ------------------------------------


def _damage_the_path(card_book) -> dict:
    from tests.reread_safety_helpers import LFS_POINTER

    ctx, source_id = card_book["ctx"], card_book["source_id"]
    (revision,) = ctx.repository.source_revisions_for(source_id)
    card_book["book"].write_bytes(LFS_POINTER)  # what the owner's checkout holds at canonical_uri
    return revision


def test_a_marker_reread_hands_the_worker_the_stored_originals_bytes(card_book, monkeypatch):
    """Main's Marker pdfium worker reads in its own process from the bytes it
    is handed: on a re-read, the revision's own bytes, hash-checked."""

    from learnloop.ingest import extractors
    from learnloop.ingest.extractors import marker as marker_module
    from learnloop.ingest.extractors import marker_worker
    from tests.reread_safety_helpers import reading_b
    from tests.ux_phase1_support import fake_services

    revision = _damage_the_path(card_book)
    handed: list[bytes] = []

    def worker(task, raw, options, **_kwargs):
        assert task == "chunks"
        handed.append(raw)
        return reading_b().model_dump(mode="json")

    monkeypatch.setattr(extractors, "marker_available", lambda: True)
    if hasattr(marker_module, "marker_available"):
        monkeypatch.setattr(marker_module, "marker_available", lambda: True)
    monkeypatch.setattr(marker_worker, "run_marker", worker)
    ctx, source_id = card_book["ctx"], card_book["source_id"]
    ctx.ingest_jobs.bind(ctx.repository, card_book["root"], background=False, clock=card_book["clock"],
                         services=fake_services(background_key_checks=False))
    out = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})
    if out.get("needsConfirmation"):
        out = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition", "confirmed": True})
    ctx.ingest_jobs.drain_foreground()
    assert ctx.repository.get_ingest_batch(out["batchId"])["status"] == "completed"
    assert handed, "Marker's worker was not asked"
    assert all(asset_hash(raw) == revision["asset_hash"] for raw in handed), "the stored original's bytes"
    assert [rev["id"] for rev in ctx.repository.source_revisions_for(source_id)] == [revision["id"]]


def test_a_glm_reread_uploads_pages_of_the_stored_original_not_the_pointer(card_book, monkeypatch):
    from pypdf import PdfReader

    from learnloop.ingest.extractors import glm_ocr as glm
    from tests.glm_ocr_helpers import hosted
    from tests.ux_phase1_support import fake_services, grant_consent

    revision = _damage_the_path(card_book)
    sent = []

    def transport(request, timeout):
        body = json.loads(request.data)
        sent.append(body)
        pages = body.get("end_page_id", 1) - body.get("start_page_id", 1) + 1
        return io.BytesIO(json.dumps(hosted(pages)).encode())

    monkeypatch.setattr(glm, "_PROBES", {})
    monkeypatch.setattr(glm, "_open", transport)
    ctx, source_id, root = card_book["ctx"], card_book["source_id"], card_book["root"]
    monkeypatch.setenv("ZAI_API_KEY", "fake-zai-key-123456")
    grant_consent(root, "whole_files_zai")
    ctx.reload(maintenance=False)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=card_book["clock"],
                         services=fake_services(background_key_checks=False))
    out = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})
    if out.get("needsConfirmation"):
        out = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition", "confirmed": True})
    ctx.ingest_jobs.drain_foreground()
    assert ctx.repository.get_ingest_batch(out["batchId"])["status"] == "completed"
    assert sent, "GLM-OCR was not asked"
    uploaded = [PdfReader(io.BytesIO(base64.b64decode(body["file"].split(",", 1)[-1]))) for body in sent]
    assert sum(len(reader.pages) for reader in uploaded) == 26  # the reading's own pages, from the store
    assert [rev["id"] for rev in ctx.repository.source_revisions_for(source_id)] == [revision["id"]]
