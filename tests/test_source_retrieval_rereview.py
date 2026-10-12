"""Slice 2 T6 Codex re-review: what the tutor's teaching scope may never read.

F1 (reopened): in practice and feedback, every span linked to the bound item is
excluded whatever its relation (with the same text in the source's other runs,
and the body after a linked example, exercise or solution lead), and a link
that names no block excludes its extraction. F17: a source in no source set and
cited by no teaching link never grounds the tutor. F19: heading substrings do
not drop teaching sections from practice grounding.
"""
from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.ingest.block_roles import classify_block_role
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.source_retrieval.corpus import teaching_scope
from learnloop.source_retrieval.dense import clear_cache
from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES
from learnloop.source_retrieval.tutor import TutorSpanProvider
from learnloop.tutor.ai_contracts import TutorAnswer, TutorCitation
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.writer import upsert_source_set
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.source_retrieval_fakes import (
    FakeSourceLLM,
    HashingEmbedder,
    build_retrieval_vault,
    loaded,
    seed_source,
)
from tests.structured_ai import StructuredClientFake
from tests.test_source_inventory import _block, _ir, _persist

CLOCK = FrozenClock(datetime(2026, 10, 12, 12, 0, 0, tzinfo=UTC))
CAPS = SpendCaps(max_candidates=10_000, max_pairs=0, max_calls=100, max_total_tokens=10**8,
                 max_estimated_usd=10.0)
WORKED = ("Example 5.2. Compute the eigenvalues of the matrix [[2,0],[0,3]]. The matrix is diagonal, so its "
          "eigenvalues are the diagonal entries: lambda_1 = 2, lambda_2 = 3.")
QUESTION = "What does it mean to compute eigenvalues of a diagonal matrix?"


@pytest.fixture(autouse=True)
def _fresh_dense_cache():
    clear_cache()
    yield
    clear_cache()


class CitingTutor(StructuredClientFake):
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-tutor"

    def __init__(self):
        self.contexts = []

    def run_tutor_qa(self, context):
        self.contexts.append(context)
        return TutorAnswer(
            answer_md="Think about what an eigenvalue is.", question_type="clarification",
            facets=list(context.candidate_facets),
            citations=[TutorCitation(extraction_id=span["extraction_id"], span_id=span["span_id"])
                       for span in context.source_spans],
        )


def _members(*extra):
    return [
        {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
        {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
        *extra,
    ]


def _set_members(paths, *extra) -> None:
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra",
                                   "title": "Linear algebra sources", "members": _members(*extra)})


def _set_expected(paths, answer: str) -> None:
    item = paths.practice_item_path("linear-algebra", "pi_eigen_1")
    item.write_text(item.read_text(encoding="utf-8").replace(
        "expected_answer: ANSWER-pi_eigen_1", f"expected_answer: {answer}"), encoding="utf-8")


def _backfill(paths, embedder=None) -> None:
    embedder = embedder or HashingEmbedder()
    report = backfill_embeddings(loaded(paths), caps=CAPS, recipes=("source_block",),
                                 registry=SOURCE_RETRIEVAL_RECIPES, client_factory=lambda: embedder)
    assert report["status"] == "complete", report


def _provider(llm=None, embedder=None):
    llm = llm or FakeSourceLLM()
    return TutorSpanProvider(embedder=embedder or HashingEmbedder(), rewrite_client=llm, rerank_client=llm,
                             clock=CLOCK), llm


def _ask(paths, repository, tutor, provider, *, context="practice", question=QUESTION, session="s1"):
    return ask_question(loaded(paths), repository, tutor, context=context, question_md=question,
                        practice_item_id="pi_eigen_1", session_id=session, source_span_provider=provider,
                        clock=CLOCK)


def _with_workbook(tmp_path, *, relation="primary", locator="span:ext_wb/s2", link=True):
    """The re-review's reproduction: a primary textbook whose worked example is the item."""

    paths, repository = build_retrieval_vault(tmp_path / "vault")
    seed_source(repository, source_id="src_wb", revision_id="rev_wb", extraction_id="ext_wb", title="Workbook",
                units={"wb": ("Chapter 5 eigenvalues", [(WORKED, 1)])}, furniture=False)
    _set_members(paths, {"source_id": "src_wb", "revision_id": "rev_wb", "default_role": "primary_textbook"})
    if link:
        repository.insert_entity_source_link(
            entity_type="practice_item", entity_id="pi_eigen_1", locator=locator, relation=relation,
            source_id="src_wb", revision_id="rev_wb", extraction_id="ext_wb")
    _set_expected(paths, "2 and 3")
    _backfill(paths)
    return paths, repository


def _reveals(repository, event_id):
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return connection.execute(
            "SELECT source_kind FROM reveal_events WHERE question_event_id = ?", (event_id,)).fetchall()


# --- F1 (reopened) --------------------------------------------------------------------------


@pytest.mark.parametrize("relation", ["primary", "support", "alternate"])
def test_a_passage_linked_to_the_item_never_reaches_the_practice_tutor(tmp_path, relation):
    paths, repository = _with_workbook(tmp_path, relation=relation)
    tutor = CitingTutor()
    provider, llm = _provider()
    result = _ask(paths, repository, tutor, provider)
    spans = tutor.contexts[0].source_spans
    assert spans and all((span["extraction_id"], span["span_id"]) != ("ext_wb", "s2") for span in spans)
    assert all("lambda_2 = 3" not in span["text"] for span in spans)
    verified = [ctx for purpose, ctx in llm.calls if purpose == "source_rerank"]
    assert verified and all("lambda_2 = 3" not in candidate["passage"]
                            for ctx in verified for candidate in ctx["candidates"])
    manifest = repository.question_event(result["event_id"])["source_context"]["source_retrieval"]
    assert manifest["basis"] == "retrieved_verified"
    assert "ext_wb/s2" not in manifest["candidate_keys"]
    vault = loaded(paths)
    # Feedback is bound to the same item.
    feedback_spans, feedback = _provider()[0](
        vault, repository, context="feedback", question_md=QUESTION, learning_object_ids=["lo_matrices"],
        item=vault.practice_items["pi_eigen_1"])
    assert feedback["basis"] == "retrieved_verified" and "ext_wb/s2" not in feedback["candidate_keys"]
    assert feedback_spans and all("lambda_2 = 3" not in span["text"] for span in feedback_spans)
    # Outside an item-bound context the same passage is ordinary teaching text.
    free = teaching_scope(vault, repository, ["lo_matrices"])
    assert ("ext_wb", "s2") not in free.excluded and "ext_wb" in free.extractions
    bound = teaching_scope(vault, repository, ["lo_matrices"], item_bound=True,
                           item=vault.practice_items["pi_eigen_1"])
    assert ("ext_wb", "s2") in bound.excluded
    assert any("linked to the practice item" in note for note in bound.notes)


def test_the_reviewers_repro_is_no_longer_cited_or_uncounted(tmp_path):
    paths, repository = _with_workbook(tmp_path)
    tutor = CitingTutor()
    result = _ask(paths, repository, tutor, _provider()[0])
    assert ("ext_wb", "s2") not in {(c["extraction_id"], c["span_id"]) for c in result["citations"]}
    assert ("source_review",) not in _reveals(repository, result["event_id"])  # nothing exposed, nothing debited


@pytest.mark.parametrize("locator", ["root/chapter-5/p1", "t=12.0-30.5", "thm:5.2", "opaque"])
def test_an_item_link_that_names_no_block_excludes_its_whole_extraction(tmp_path, locator):
    paths, repository = _with_workbook(tmp_path, locator=locator)
    vault = loaded(paths)
    bound = teaching_scope(vault, repository, ["lo_matrices"], item_bound=True,
                           item=vault.practice_items["pi_eigen_1"])
    assert "ext_wb" not in bound.extractions and "ext_book" in bound.extractions
    assert "ext_wb" in teaching_scope(vault, repository, ["lo_matrices"]).extractions


def test_an_items_yaml_source_ref_is_excluded_without_a_link_row(tmp_path):
    paths, repository = _with_workbook(tmp_path, link=False)
    item_path = paths.practice_item_path("linear-algebra", "pi_eigen_1")
    data = read_yaml(item_path)
    data["provenance"] = {"origin": "canonical_extract", "source_refs": [
        {"ref_type": "canonical_source", "ref_id": "src_wb", "source_id": "src_wb", "revision_id": "rev_wb",
         "extraction_id": "ext_wb", "locator": "span:ext_wb/s2", "relation": "primary"},
        {"ref_type": "existing_entity", "ref_id": "lo_matrices", "locator": "target learning object"},
    ]}
    write_yaml(item_path, data)
    vault = loaded(paths)
    bound = teaching_scope(vault, repository, ["lo_matrices"], item_bound=True,
                           item=vault.practice_items["pi_eigen_1"])
    assert ("ext_wb", "s2") in bound.excluded
    assert "ext_book" in bound.extractions  # a ref to another entity names no source
    tutor = CitingTutor()
    _ask(paths, repository, tutor, _provider()[0])
    assert all((span["extraction_id"], span["span_id"]) != ("ext_wb", "s2")
               for span in tutor.contexts[0].source_spans)


def test_an_item_link_into_an_older_run_is_matched_in_the_re_extraction(tmp_path):
    paths, repository = _with_workbook(tmp_path)  # the item links ext_wb/s2
    # The same revision re-extracted: the latest run renumbers the example to s4.
    _persist(repository, _ir([("wb", "Chapter 5 eigenvalues", [
        _block("s1", "Chapter 5 eigenvalues", block_type="SectionHeader"),
        _block("s2", "Eigenvalues of a diagonal matrix sit on its diagonal."),
        _block("s3", "We now work an example."),
        _block("s4", WORKED),
    ], "sha256:wb2", 1)], extractor="marker"), revision_id="rev_wb", extraction_id="ext_wb_v2",
             config={"rerun": 2})
    vault = loaded(paths)
    bound = teaching_scope(vault, repository, ["lo_matrices"], item_bound=True,
                           item=vault.practice_items["pi_eigen_1"])
    assert "ext_wb_v2" in bound.extractions  # the revision's latest run
    assert ("ext_wb_v2", "s4") in bound.excluded and ("ext_wb_v2", "s2") not in bound.excluded


def test_the_body_after_an_item_linked_example_lead_is_excluded(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, current_revision_id, "
            "reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            ("src_text", "pdf", "file:///src_text.pdf", "Textbook", "rev_text", 1,
             "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_text", "src_text", "sha256:src_text", None, "2026-01-01T00:00:00Z"))
        connection.commit()
    _persist(repository, _ir([("u1", "Eigenvalues", [
        _block("s1", "Eigenvalues of a diagonal matrix are its diagonal entries.", role_hint="definition"),
        _block("s2", "Example 5.2 Compute the eigenvalues of [[2,0],[0,3]].", role_hint="worked_example"),
        _block("s3", "The matrix is diagonal, so the eigenvalues are read off the diagonal."),
        _block("s4", "$$\\lambda_1 = 2, \\lambda_2 = 3$$", block_type="Equation", role_hint="equation"),
        _block("s5", "Theorem 5.3 A triangular matrix has its eigenvalues on the diagonal.", role_hint="theorem"),
        _block("s6", "Example 5.4 Compute the eigenvalues of [[1,1],[0,4]].", role_hint="worked_example"),
        _block("s7", "Its eigenvalues are 1 and 4, read off the diagonal."),
    ], "sha256:u1", 1)]), revision_id="rev_text", extraction_id="ext_text")
    _set_members(paths, {"source_id": "src_text", "revision_id": "rev_text", "default_role": "primary_textbook"})
    repository.insert_entity_source_link(
        entity_type="practice_item", entity_id="pi_eigen_1", locator="span:ext_text/s2", relation="primary",
        source_id="src_text", revision_id="rev_text", extraction_id="ext_text")
    vault = loaded(paths)
    bound = teaching_scope(vault, repository, ["lo_matrices"], item_bound=True,
                           item=vault.practice_items["pi_eigen_1"])
    # The linked lead and its worked body up to the theorem; another example is teaching text.
    assert {key for key in bound.excluded if key[0] == "ext_text"} == {
        ("ext_text", "s2"), ("ext_text", "s3"), ("ext_text", "s4")}


# --- F17 ------------------------------------------------------------------------------------


def test_a_source_in_no_set_never_grounds_the_tutor(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    seed_source(repository, source_id="src_loose", revision_id="rev_loose", extraction_id="ext_loose",
                title="Solutions manual", units={"sol": ("Chapter 5", [
                    ("Solution 5.2: the eigenvalues of the diagonal matrix are 2 and 3.", 1)])},
                furniture=False)
    vault = loaded(paths)
    fallback = teaching_scope(vault, repository, [])  # no LO: the fallback scope
    assert "ext_loose" not in fallback.extractions and "ext_book" in fallback.extractions
    assert any("1 source(s) in no source set and cited by no teaching link" in note for note in fallback.notes)
    # A teaching link from any learning object gives a set-less source standing.
    repository.insert_entity_source_link(
        entity_type="learning_object", entity_id="lo_vectors", locator="span:ext_loose/s2", relation="support",
        source_id="src_loose", revision_id="rev_loose", extraction_id="ext_loose")
    assert "ext_loose" in teaching_scope(loaded(paths), repository, []).extractions


# --- F19 ------------------------------------------------------------------------------------


def test_heading_cues_do_not_drop_teaching_sections_from_practice(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, current_revision_id, "
            "reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            ("src_md", "markdown", "file:///notes.md", "Lecture notes", "rev_md", 1,
             "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_md", "src_md", "sha256:src_md", None, "2026-01-01T00:00:00Z"))
        connection.commit()

    def block(span_id, text, heading):
        section = ("root", heading)
        return _block(span_id, text, role_hint=classify_block_role("Text", list(section), text), section=section)

    blocks = [
        block("s1", "A linear system has a solution exactly when b lies in the column space.",
              "Solutions of linear systems"),
        block("s2", "Gaussian elimination reduces the augmented matrix to echelon form.",
              "Solutions of linear systems"),
        block("s3", "The eigenvalue problem asks for every t with Av = tv for some nonzero v.",
              "The eigenvalue problem"),
        block("s4", "Least squares minimizes the residual norm over the column space.", "Least-squares problems"),
        block("s5", "1. Find the eigenvalues of [[1,1],[0,2]].", "Exercises"),
        block("s6", "Solution: the eigenvalues are 1 and 2.", "Solutions of linear systems"),
        block("s7", "Problem 4. Show that a symmetric matrix has real eigenvalues.", "The eigenvalue problem"),
        block("s8", "2. Compute det(A) for A = [[2,1],[1,2]].", "Exercises for Section 5.3"),
    ]
    hints = {b.span_id: b.role_hint for b in blocks}
    assert hints["s1"] == hints["s2"] == "solution" and hints["s3"] == hints["s4"] == "exercise"  # heading cues
    _persist(repository, _ir([("u1", "Notes", blocks, "sha256:md", 1)], extractor="markdown"),
             revision_id="rev_md", extraction_id="ext_md")
    _set_members(paths, {"source_id": "src_md", "revision_id": "rev_md", "default_role": "lecture"})
    vault = loaded(paths)
    bound = teaching_scope(vault, repository, ["lo_matrices"], item_bound=True)
    dropped = {key[1] for key in bound.excluded if key[0] == "ext_md"}
    # Lead cues (s6, s7) and dedicated exercise headings (s5, s8) only.
    assert dropped == {"s5", "s6", "s7", "s8"}
    assert any("4 exercise or solution block(s) excluded" in note for note in bound.notes)
