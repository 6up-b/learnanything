"""Slice 2 T6 review fixes: what the tutor's retrieval may never read, and what it costs.

F1: an item's own exercise and solution never reach the tutor, short numeric
answers included, and a cited span's overlap with the expected answer is a
reveal. F6/F7: assessment material is excluded in every extraction and for
every locator shape. F8: nothing is paid for when verification cannot run.
F10: at most four spans. F11: one listwise judge. F13: the manifest names the
spans the tutor saw.
"""
from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.clock import FrozenClock
from learnloop.config.schema import SourceRetrievalConfig
from learnloop.db.connection import connect
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.practice_index import listwise
from learnloop.source_retrieval.corpus import teaching_scope
from learnloop.source_retrieval.dense import clear_cache
from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES
from learnloop.source_retrieval.search import search_spans
from learnloop.source_retrieval.tutor import TutorSpanProvider
from learnloop.source_retrieval.verify import VERIFY_TASK
from learnloop.tutor.ai_contracts import TutorAnswer, TutorCitation
from learnloop.tutor.tutor_qa import ask_question, span_answer_overlap, span_leaks_expected
from learnloop.vault.writer import upsert_source_set
from tests.helpers import append_config_toml
from tests.source_retrieval_fakes import (
    EXAM_QUESTION,
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
PROBLEM = "Problem 3. Compute the eigenvalues of the matrix [[2,0],[0,3]]."
SOLUTION = "Solution to Problem 3: the matrix is diagonal, so its eigenvalues are the diagonal entries 2 and 3."
QUESTION = "What does it mean to compute eigenvalues here?"


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


def _register(repository, *, source_id: str, revision_id: str, title: str) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, current_revision_id, "
            "reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (source_id, "pdf", f"file:///{source_id}.pdf", title, revision_id, 1,
             "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            (revision_id, source_id, f"sha256:{source_id}:{revision_id}", None, "2026-01-01T00:00:00Z"))
        connection.commit()


def _set_expected(paths, answer: str) -> None:
    item = paths.practice_item_path("linear-algebra", "pi_eigen_1")
    item.write_text(item.read_text(encoding="utf-8").replace(
        "expected_answer: ANSWER-pi_eigen_1", f"expected_answer: {answer}"), encoding="utf-8")


def _backfill(paths) -> None:
    report = backfill_embeddings(loaded(paths), caps=CAPS, recipes=("source_block",),
                                 registry=SOURCE_RETRIEVAL_RECIPES, client_factory=HashingEmbedder)
    assert report["status"] == "complete", report


def _members(*extra):
    return [
        {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
        {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
        *extra,
    ]


def _with_problem_set(tmp_path):
    """The review's F1 reproduction: a problem set whose exercise is linked to the item."""

    paths, repository = build_retrieval_vault(tmp_path / "vault")
    seed_source(repository, source_id="src_ps", revision_id="rev_ps", extraction_id="ext_ps",
                title="Problem Set 4", units={"ps_q": ("Problem Set 4", [(PROBLEM, 1), (SOLUTION, 1)])},
                furniture=False)
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra",
                                   "title": "Linear algebra sources", "members": _members(
                                       {"source_id": "src_ps", "revision_id": "rev_ps",
                                        "default_role": "problem_set"})})
    repository.insert_entity_source_link(
        entity_type="practice_item", entity_id="pi_eigen_1", locator="span:ext_ps/s2", relation="exercise",
        source_id="src_ps", revision_id="rev_ps", extraction_id="ext_ps")
    _set_expected(paths, "2 and 3")
    _backfill(paths)
    return paths, repository


def _ask(paths, repository, tutor, provider, *, context="practice", question=QUESTION, session="s1"):
    return ask_question(loaded(paths), repository, tutor, context=context, question_md=question,
                        practice_item_id="pi_eigen_1", session_id=session, source_span_provider=provider,
                        clock=CLOCK)


def _provider(llm=None, **kwargs):
    llm = llm or FakeSourceLLM()
    return TutorSpanProvider(embedder=HashingEmbedder(), rewrite_client=llm, rerank_client=llm,
                             clock=CLOCK, **kwargs), llm


# --- F1 -------------------------------------------------------------------------------------


def test_short_answers_are_measured_in_source_spans():
    # answer_leak_overlap cannot measure these (fewer than three content tokens).
    for answer, text in (("2 and 3", SOLUTION), ("2/13", "so the probability is 2/13."),
                         ("0.154", "which gives 0.154 to three places")):
        assert span_answer_overlap(text, answer) == 1.0 and span_leaks_expected(text, answer)
    assert not span_leaks_expected("Chapter 2 and section 4", "2 and 3")
    assert not span_leaks_expected("there are 3 cases", "3")  # a lone digit is too common to match
    assert span_answer_overlap("unrelated text", "2/13") == 0.0


def test_the_items_own_solution_never_reaches_the_tutor(tmp_path):
    paths, repository = _with_problem_set(tmp_path)
    tutor = CitingTutor()
    provider, llm = _provider()
    result = _ask(paths, repository, tutor, provider)
    spans = tutor.contexts[0].source_spans
    texts = " ".join(span["text"] for span in spans)
    assert spans and "2 and 3" not in texts and PROBLEM not in texts
    assert all(span["extraction_id"] != "ext_ps" for span in spans)  # a problem set does not teach
    assert all(citation["extraction_id"] != "ext_ps" for citation in result["citations"])
    verified = [context for purpose, context in llm.calls if purpose == "source_rerank"]
    assert verified and all("2 and 3" not in candidate["passage"]
                            for context in verified for candidate in context["candidates"])
    manifest = repository.question_event(result["event_id"])["source_context"]["source_retrieval"]
    assert manifest["basis"] == "retrieved_verified"
    assert not any(key.startswith("ext_ps/") for key in manifest["candidate_keys"])


def test_a_teaching_span_stating_a_short_answer_is_withheld(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    seed_source(repository, source_id="src_ref", revision_id="rev_ref", extraction_id="ext_ref",
                title="Reference notes", units={"ref": ("Diagonal matrices", [
                    ("A diagonal matrix has its eigenvalues on the diagonal: diag(2,3) has eigenvalues 2 and 3.", 1),
                    ("The eigenvalues of a diagonal matrix are read off its diagonal entries.", 1)])},
                furniture=False)
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra",
                                   "title": "Linear algebra sources", "members": _members(
                                       {"source_id": "src_ref", "revision_id": "rev_ref",
                                        "default_role": "reference"})})
    _set_expected(paths, "2 and 3")
    _backfill(paths)
    tutor = CitingTutor()
    provider, _llm = _provider()
    result = _ask(paths, repository, tutor, provider, question="What are the eigenvalues of a diagonal matrix?")
    assert all("2 and 3" not in span["text"] for span in tutor.contexts[0].source_spans)
    manifest = repository.question_event(result["event_id"])["source_context"]["source_retrieval"]
    assert manifest["withheld_answer_overlap"] >= 1 and "ext_ref/s2" in manifest["withheld_keys"]


def test_the_practice_question_is_never_the_retrieval_query(tmp_path):
    paths, repository = _with_problem_set(tmp_path)
    append_config_toml(paths.root, "[source_retrieval]\ntutor_query_rewrite = true\n")
    seen = []
    original = search_spans

    def spy(*args, **kwargs):
        seen.append((args[2], kwargs.get("context_text")))
        return original(*args, **kwargs)

    import learnloop.source_retrieval.tutor as tutor_module

    provider, llm = _provider()
    try:
        tutor_module.search_spans = spy
        _ask(paths, repository, CitingTutor(), provider,
             question="Why are the eigenvalues of a diagonal matrix its diagonal entries?")
    finally:
        tutor_module.search_spans = original
    assert seen == [("Why are the eigenvalues of a diagonal matrix its diagonal entries?", None)]
    rewrites = [context for purpose, context in llm.calls if purpose == "source_query_rewrite"]
    assert rewrites and all("context" not in context for context in rewrites)


def _book_with_worked_solution(repository):
    _register(repository, source_id="src_text", revision_id="rev_text", title="Textbook")
    _persist(repository, _ir([
        ("u1", "Eigenvalues", [
            _block("s1", "Eigenvalues of a diagonal matrix are its diagonal entries.", role_hint="definition"),
            _block("s2", "Example 5.1 Compute the eigenvalues of a diagonal matrix.", role_hint="worked_example"),
            _block("s3", "Solution:", role_hint="solution"),
            _block("s4", "Reading off the diagonal of the matrix gives each eigenvalue in turn."),
            _block("s5", "Exercise 5.2 Find the eigenvalues of a triangular matrix.", role_hint="exercise"),
            _block("s6", "Theorem 5.3 A triangular matrix has its eigenvalues on the diagonal.",
                   role_hint="theorem"),
        ], "sha256:u1", 1),
    ]), revision_id="rev_text", extraction_id="ext_text")


def test_practice_and_feedback_drop_exercise_and_solution_blocks(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    _book_with_worked_solution(repository)
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra", "title": "LA",
                                   "members": _members({"source_id": "src_text", "revision_id": "rev_text",
                                                        "default_role": "primary_textbook"})})
    vault = loaded(paths)
    bound = teaching_scope(vault, repository, ["lo_matrices"], item_bound=True)
    # The solution's lead and the body after it, and the exercise; not the
    # definition, the example statement or the theorem that ends the region.
    assert {key for key in bound.excluded if key[0] == "ext_text"} == {
        ("ext_text", "s3"), ("ext_text", "s4"), ("ext_text", "s5")}
    free = teaching_scope(vault, repository, ["lo_matrices"])
    assert not {key for key in free.excluded if key[0] == "ext_text"}


def test_a_cited_span_overlapping_the_expected_answer_is_debited_as_a_reveal(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    _set_expected(paths, "the roots of the characteristic polynomial found by solving det(A - tI) = 0 "
                         "and checking each multiplicity")
    _backfill(paths)
    tutor = CitingTutor()
    provider, _llm = _provider()
    result = _ask(paths, repository, tutor, provider,
                  question="Why are eigenvalues the roots of the characteristic polynomial?")
    spans = {(span["extraction_id"], span["span_id"]): span["text"] for span in tutor.contexts[0].source_spans}
    expected = max(span_answer_overlap(text, loaded(paths).practice_items["pi_eigen_1"].expected_answer)
                   for text in spans.values())
    assert 0 < expected < 0.8  # partial: not withheld, but exposed when opened
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            "SELECT source_kind, amount, basis FROM reveal_events WHERE question_event_id = ? "
            "AND source_kind = 'source_review'", (result["event_id"],)).fetchall()
    assert [(row[0], round(row[1], 6), row[2]) for row in rows] == [
        ("source_review", round(expected, 6), "tutor_qa:practice:cited_source_span")]


def test_linked_spans_without_retrieval_are_not_debited(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault", embeddings=False)
    repository.insert_entity_source_link(
        entity_type="learning_object", entity_id="lo_matrices", locator="span:ext_book/s2",
        relation="primary", source_id="src_book", revision_id="rev_book", extraction_id="ext_book")
    _set_expected(paths, "the roots of the characteristic polynomial found by solving det(A - tI) = 0")
    result = _ask(paths, repository, CitingTutor(), None)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        kinds = [row[0] for row in connection.execute(
            "SELECT source_kind FROM reveal_events WHERE question_event_id = ?", (result["event_id"],))]
    assert "source_review" not in kinds  # the kill-switch path is unchanged


# --- F6, F7 ---------------------------------------------------------------------------------


def test_an_exam_reimport_is_excluded_whatever_revision_the_set_pins(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_exam2", "src_exam", "sha256:exam-v2", None, "2026-02-01T00:00:00Z"))
        connection.execute("UPDATE source_artifacts SET current_revision_id = 'rev_exam2' WHERE id = 'src_exam'")
        connection.commit()
    _persist(repository, _ir([("exam_q", "Midterm v2", [_block("s1", EXAM_QUESTION)], "sha256:exam3", 1)]),
             revision_id="rev_exam2", extraction_id="ext_exam2")
    vault = loaded(paths)
    # No LO: the fallback searches every current extraction, ext_exam2 included.
    scope = teaching_scope(vault, repository, [])
    assert "ext_exam2" not in scope.extractions and "ext_exam" not in scope.extractions
    found = search_spans(vault, repository, "compute the eigenvalues of the matrix", scope, deep=False)
    assert found.hits and all(EXAM_QUESTION not in hit.text for hit in found.hits)


@pytest.mark.parametrize("locator", ["root/chapter-5/p1", "t=12.0-30.5", "thm:4.2", "opaque"])
def test_an_assessment_link_that_names_no_block_excludes_its_whole_extraction(tmp_path, locator):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    repository.insert_entity_source_link(
        entity_type="practice_item", entity_id="pi_eigen_1", locator=locator, relation="exercise",
        source_id="src_book", revision_id="rev_book", extraction_id="ext_book")
    scope = teaching_scope(loaded(paths), repository, ["lo_matrices"])
    assert "ext_book" not in scope.extractions  # fail closed
    assert any("without teaching authority" in note for note in scope.notes)


def test_an_assessment_link_without_an_extraction_excludes_its_sources_extractions(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    repository.insert_entity_source_link(
        entity_type="practice_item", entity_id="pi_eigen_1", locator="root/ch5", relation="assessment_alignment",
        source_id="src_book", revision_id=None, extraction_id=None)
    assert "ext_book" not in teaching_scope(loaded(paths), repository, ["lo_matrices"]).extractions


def test_a_unit_override_is_resolved_on_its_reading_and_an_unmarked_reimport_is_held_back_whole(tmp_path):
    """An exam unit override is resolved on the reading its scope names. The
    book's re-import (a new revision, units renumbered) never inherits it by
    label (protection redesign, re-read safety 2026-10-15): with no exam
    material marked on it, the whole re-import stays out of teaching until the
    owner marks it."""

    paths, repository = build_retrieval_vault(tmp_path / "vault")
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra", "title": "LA", "members": [
        {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook",
         "scope": [{"unit_id": "ch_det", "role_override": "exam"}],
         "scope_extraction_id": "ext_book", "scope_revision_id": "rev_book"},
        {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
    ]})
    from tests.source_retrieval_fakes import BOOK

    # The book re-imported (a new current revision the set does not pin), its
    # units renumbered.
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_book2", "src_book", "sha256:book-v2", None, "2026-02-01T00:00:00Z"))
        connection.execute("UPDATE source_artifacts SET current_revision_id = 'rev_book2' WHERE id = 'src_book'")
        connection.commit()
    renamed = {f"x_{unit_id}": value for unit_id, value in BOOK.items()}
    seed_source_extraction(repository, "rev_book2", "ext_book_v2", renamed)
    scope = teaching_scope(loaded(paths), repository, ["lo_matrices"])
    assert ("ext_book", "s6") in scope.excluded  # "Chapter 3 Determinants" header ...
    assert ("ext_book", "s7") in scope.excluded  # ... and its blocks
    assert ("ext_book", "s2") not in scope.excluded
    # The re-import is held back whole until it is marked: no block of it teaches.
    from learnloop.source_retrieval.corpus import teaching_exclusions

    assert "ext_book_v2" in teaching_exclusions(loaded(paths), repository).extractions
    assert "ext_book" not in teaching_exclusions(loaded(paths), repository).extractions


def seed_source_extraction(repository, revision_id, extraction_id, units):
    from tests.source_retrieval_fakes import _blocks
    from learnloop.ingest.ir import DocumentIR, DocumentUnit, ExtractionHealth

    blocks, document_units, start = [], [], 1
    for ordinal, (unit_id, (header, rows)) in enumerate(units.items()):
        unit_blocks, span_ids = _blocks(unit_id, header, rows, start)
        start += len(unit_blocks) + 1
        blocks.extend(unit_blocks)
        document_units.append(DocumentUnit(unit_id=unit_id, label=header, ordinal=ordinal,
                                           semantic_hash=f"sha256:{unit_id}", page_start=rows[0][1],
                                           page_end=rows[-1][1], span_ids=span_ids))
    ir = DocumentIR(extractor="marker", extractor_version="1", units=document_units, blocks=blocks,
                    assets=[], health=ExtractionHealth())
    _persist(repository, ir, revision_id=revision_id, extraction_id=extraction_id)


# --- F8 -------------------------------------------------------------------------------------


def test_nothing_is_paid_for_when_verification_cannot_run(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    _backfill(paths)
    append_config_toml(paths.root, "[source_retrieval]\ntutor_query_rewrite = true\n")
    rewrite = FakeSourceLLM()
    embedder = HashingEmbedder()
    provider = TutorSpanProvider(embedder=embedder, rewrite_client=rewrite,
                                 rerank_client=FakeSourceLLM(provider_type="openrouter"), clock=CLOCK)
    result = _ask(paths, repository, CitingTutor(), provider,
                  question="Why are eigenvalues the roots of the characteristic polynomial?")
    assert rewrite.calls == [] and embedder.calls == []
    manifest = repository.question_event(result["event_id"])["source_context"]["source_retrieval"]
    assert manifest["basis"] == "lo_provenance"
    assert manifest["reason"].startswith("verification skipped: metered route")


# --- F10, F11, F13 --------------------------------------------------------------------------


def test_at_most_four_spans_reach_the_tutor(tmp_path):
    with pytest.raises(ValueError):
        SourceRetrievalConfig(tutor_spans=5)
    paths, repository = build_retrieval_vault(tmp_path / "vault", embeddings=False)
    spans = [{"extraction_id": "ext_book", "span_id": f"s{n}", "label": "x", "text": "x",
              "relation": "retrieved"} for n in (2, 3, 4, 7, 8, 9)]
    tutor = CitingTutor()
    _ask(paths, repository, tutor, lambda *args, **kwargs: (spans, {"basis": "retrieved_verified"}))
    assert [span["span_id"] for span in tutor.contexts[0].source_spans] == ["s2", "s3", "s4", "s7"]


def test_tutor_verification_and_the_practice_rerank_share_one_listwise_judge(tmp_path, monkeypatch):
    from learnloop.practice_index.retrieval import RERANK_TASK

    assert isinstance(VERIFY_TASK, listwise.ListwiseTask) and isinstance(RERANK_TASK, listwise.ListwiseTask)
    calls = []
    original = listwise.judge_listwise

    def spy(*args, **kwargs):
        calls.append(args[2].route_task)
        return original(*args, **kwargs)

    monkeypatch.setattr("learnloop.source_retrieval.verify.judge_listwise", spy)
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    _backfill(paths)
    _ask(paths, repository, CitingTutor(), _provider()[0],
         question="Why are eigenvalues the roots of the characteristic polynomial?")
    assert calls == ["source_rerank"]


def test_the_manifest_records_the_span_keys_the_tutor_saw(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    _backfill(paths)
    tutor = CitingTutor()
    result = _ask(paths, repository, tutor, _provider()[0],
                  question="Why are eigenvalues the roots of the characteristic polynomial?")
    manifest = repository.question_event(result["event_id"])["source_context"]["source_retrieval"]
    assert manifest["span_keys"] == [f"{span['extraction_id']}/{span['span_id']}"
                                     for span in tutor.contexts[0].source_spans]
    assert set(manifest["span_keys"]) <= set(manifest["candidate_keys"])
    assert all(isinstance(key, str) and "/" in key for key in manifest["candidate_keys"])
    assert "text" not in repr(manifest["span_keys"])  # keys only, never span text
