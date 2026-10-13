"""Deterministic fakes and a small vault for Slice 2 T6 source-retrieval tests.

``build_retrieval_vault`` extends the practice-index vault (three LOs, six
facets, subject ``linear-algebra``) with a textbook whose blocks discuss the
facets, an exam whose questions must never reach a teaching context, and a
source set naming both. ``FakeSourceLLM`` answers every T6 structured role from
the prompt's own JSON, using lexical overlap where a real model would judge:
results are plumbing checks, not evidence about retrieval quality.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from learnloop.ai.execution import report_call_usage
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.practice_index.text import tokenize
from learnloop.source_retrieval.contracts import (
    QueryRewrite,
    SpanJudgment,
    SpanLabels,
    SpanVerification,
    WrittenQuestion,
    WrittenQuestions,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_source_set
from tests.practice_index_fakes import EMBED_DIMS, HashingEmbedder, build_practice_vault, enable_practice_index
from tests.pf_fakes import prompt_context
from tests.test_source_inventory import _persist

BOOK = {
    "ch_eigen": ("Chapter 5 Eigenvalues", [
        ("Eigenvalues are the roots of the characteristic polynomial det(A - tI) of a square matrix.", 3),
        ("An eigenvector v satisfies Av = tv for its eigenvalue t; eigenvectors span eigenspaces.", 3),
        ("Real symmetric matrices have real eigenvalues and orthogonal eigenvectors.", 4),
    ]),
    "ch_det": ("Chapter 3 Determinants", [
        ("The determinant changes sign when two rows of a matrix are swapped.", 1),
        ("Cofactor expansion computes a determinant along any row or column.", 1),
        ("A matrix is invertible exactly when its determinant is nonzero.", 2),
    ]),
    "ch_orth": ("Chapter 6 Orthogonality", [
        ("Two vectors are orthogonal when their dot product is zero.", 5),
        ("Orthogonal nonzero vectors are linearly independent, so they form a basis of their span.", 5),
        ("Projection onto a unit vector u is (v . u) u.", 6),
    ]),
}
EXAM_QUESTION = "Exam question 1: compute the eigenvalues of the matrix [[4,1],[2,3]] and justify them."


def _blocks(unit_id: str, header: str, rows: list[tuple[str, int]], start: int) -> tuple[list[DocumentBlock], list[str]]:
    header_ref = f"/page/{rows[0][1]}/SectionHeader/{start}"
    blocks = [DocumentBlock.build(span_id=f"s{start}", block_type="SectionHeader", text=header,
                                  ordinal=start, page=rows[0][1], section_path=[header_ref],
                                  extractor_block_id=header_ref)]
    for offset, (text, page) in enumerate(rows, start=1):
        blocks.append(DocumentBlock.build(span_id=f"s{start + offset}", block_type="Text", text=text,
                                          ordinal=start + offset, page=page, section_path=[header_ref]))
    return blocks, [block.span_id for block in blocks]


def seed_source(repository: Repository, *, source_id: str, revision_id: str, extraction_id: str,
                title: str, units: dict[str, tuple[str, list[tuple[str, int]]]],
                furniture: bool = True, reader_enabled: bool = True, asset_hash: str | None = None,
                original_uri: str | None = None) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, current_revision_id, "
            "reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (source_id, "pdf", f"file:///{source_id}.pdf", title, revision_id, int(reader_enabled),
             "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            (revision_id, source_id, asset_hash or f"sha256:{source_id}", original_uri, "2026-01-01T00:00:00Z"),
        )
        connection.commit()
    blocks: list[DocumentBlock] = []
    document_units: list[DocumentUnit] = []
    start = 1
    for ordinal, (unit_id, (header, rows)) in enumerate(units.items()):
        unit_blocks, span_ids = _blocks(unit_id, header, rows, start)
        start += len(unit_blocks) + 1
        blocks.extend(unit_blocks)
        document_units.append(DocumentUnit(unit_id=unit_id, label=header, ordinal=ordinal,
                                           semantic_hash=f"sha256:{unit_id}", page_start=rows[0][1],
                                           page_end=rows[-1][1], span_ids=span_ids))
    if furniture:
        blocks.append(DocumentBlock.build(span_id="s999", block_type="PageHeader",
                                          text=f"{title} running header eigenvalues", ordinal=999, page=1))
    ir = DocumentIR(extractor="marker", extractor_version="1", units=document_units, blocks=blocks,
                    assets=[], health=ExtractionHealth())
    _persist(repository, ir, revision_id=revision_id, extraction_id=extraction_id)


def build_retrieval_vault(root: Path, *, embeddings: bool = True) -> tuple[VaultPaths, Repository]:
    paths = build_practice_vault(root)
    enable_practice_index(paths, embeddings=embeddings)
    repository = Repository(paths.sqlite_path)
    seed_source(repository, source_id="src_book", revision_id="rev_book", extraction_id="ext_book",
                title="Linear Algebra Notes", units=BOOK)
    seed_source(repository, source_id="src_exam", revision_id="rev_exam", extraction_id="ext_exam",
                title="Midterm", units={"exam_q": ("Midterm problems", [(EXAM_QUESTION, 1)])}, furniture=False)
    upsert_source_set(paths.root, {
        "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
        "members": [
            {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
            {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
        ],
    })
    return paths, repository


def loaded(paths: VaultPaths):
    return load_vault(paths.root)


def _grade(question: str, text: str) -> str:
    hits = len(set(tokenize(question)) & set(tokenize(text)))
    return "answers" if hits >= 2 else "related" if hits == 1 else "unrelated"


class FakeSourceLLM:
    """A structured client for T6's live and benchmark roles (no network)."""

    provider_name = "fake_source_llm"

    def __init__(self, *, provider_type: str = "codex_sdk", model: str = "fake-source-model",
                 fail: bool = False, drop_label_refs: int = 0) -> None:
        self.provider_type = provider_type
        self.model = model
        self.fail = fail
        self.drop_label_refs = drop_label_refs
        self.calls: list[tuple[str, dict[str, Any]]] = []
        #: (purpose, requested reasoning effort) per request.
        self.efforts: list[tuple[str, str | None]] = []

    def supports(self, capability: str) -> bool:
        return capability in {"structured_completion", "bounded_structured_completion", "isolated_turn"}

    def complete(self, request):
        context = prompt_context(request.prompt)
        self.calls.append((request.purpose, context))
        self.efforts.append((request.purpose, request.reasoning_effort))
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 40,
                           "resolved_model": self.model})
        if self.fail:
            from learnloop.ai.errors import AIProviderUnavailable

            raise AIProviderUnavailable("fake failure")
        model = request.result_model
        if model is QueryRewrite:
            question = context["question"]
            terms = tokenize(question)
            return QueryRewrite(passage=f"A passage explaining {question} with eigenvalues and determinants.",
                                keywords=[*terms[:4], "characteristic polynomial"])
        if model is SpanVerification:
            question = " ".join([context["question"], context.get("practice_question") or ""])
            judged = [(c["ref"], _grade(question, c["passage"])) for c in context["candidates"]]
            order = {"answers": 0, "related": 1}
            picks = [ref for ref, verdict in sorted(judged, key=lambda pair: (order.get(pair[1], 9), pair[0]))
                     if verdict != "unrelated"][: context["pick_at_most"]]
            return SpanVerification(
                judgments=[SpanJudgment(ref=ref, verdict=verdict, rationale="overlap") for ref, verdict in judged],
                picks=picks)
        if model is SpanLabels:
            candidates = context["candidates"][self.drop_label_refs:]
            return SpanLabels(labels=[
                SpanJudgment(ref=c["ref"], verdict=_grade(context["question"],
                                                          c.get("passage") or c.get("text") or ""),
                             rationale="overlap")
                for c in candidates])
        if model is WrittenQuestions:
            if "pairs" in context:  # compositional: one question needing both passages
                return WrittenQuestions(questions=[
                    WrittenQuestion(seed_ref=p["seed_ref"],
                                    question="How does " + " ".join(tokenize(p["passage_a"])[:4]) + " relate to "
                                    + " ".join(tokenize(p["passage_b"])[:4]) + "?")
                    for p in context["pairs"]])
            return WrittenQuestions(questions=[
                WrittenQuestion(seed_ref=p["seed_ref"],
                                question="Why " + " ".join(tokenize(p["passage"])[:6]) + "?")
                for p in context["passages"]])
        raise AssertionError(f"unexpected result model {model}")


__all__ = [
    "BOOK", "EMBED_DIMS", "EXAM_QUESTION", "FakeSourceLLM", "HashingEmbedder", "build_retrieval_vault",
    "loaded", "seed_source",
]
