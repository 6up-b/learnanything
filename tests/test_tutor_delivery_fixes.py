"""Tutor delivery fixes (owner-approved 2026-10-13; docs/reviews/tutor-delivery-fixes.md).

What the tutor and the retrieval benchmark actually see of the sources:

1. a Reader Ask about one block gets its nearest neighbours on both sides
   (i-1 and i+1 first, then widening), never i-3 and i-2 alone;
2. complete blocks, not 240/600/900-character cuts, within one explicit
   token budget whose trims are recorded;
3. "by Theorem 3.2" in a delivered passage is followed to the numbered block
   of the same extraction (``referenced``), within the budget and the exam
   rule, and an unresolved reference is recorded;
4. (re-)extraction queues the source-block embedding backfill when embeddings
   are on (``test_source_vector_backfill.py``).
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from learnloop.clock import FrozenClock
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.repositories import Repository
from learnloop.reader import reader_dialogue as RD
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.loader import load_vault
from tests.helpers import append_config_toml, create_basic_vault
from tests.source_retrieval_fakes import seed_source

CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, 0, tzinfo=UTC))

LONG = (
    "A real symmetric matrix has an orthonormal basis of eigenvectors, and the change of basis to that "
    "eigenbasis is an orthogonal matrix whose transpose is its inverse. "
) * 12  # about 2,000 characters: past every preview cut (240, 600, 900)

#: One chapter: a header (s1) then nine paragraphs s2..s10. The Ask is about s6.
CHAPTER = [
    ("Paragraph two sets up the notation for the chapter.", 1),
    ("Paragraph three defines the transpose of a matrix.", 1),
    ("Paragraph four says a matrix is symmetric when it equals its transpose.", 1),
    ("Paragraph five, right before the step: assume A^T = A and Av = tv.", 1),
    ("Paragraph six, the step: hence t is real, by Theorem 3.2 and Lemma 9.9.", 2),
    ("Paragraph seven, right after the step: so the eigenvalues are real numbers.", 2),
    ("Paragraph eight extends the result to Hermitian matrices.", 2),
    ("Paragraph nine gives an example with a 2 by 2 matrix.", 2),
    ("Paragraph ten summarises the section.", 2),
]
THEOREM = ("Theorem 3.2 (Spectral theorem). Every real symmetric matrix A has real eigenvalues "
           "and an orthonormal basis of eigenvectors.")


def _vault(tmp_path, *, chapter=CHAPTER, extra_units=None, config: str | None = None):
    paths = create_basic_vault(tmp_path / "vault")
    if config:
        append_config_toml(paths.root, config)
    repository = Repository(paths.sqlite_path)
    units = dict(extra_units or {})
    units["ch_sym"] = ("Chapter 4 Symmetric matrices", list(chapter))
    seed_source(repository, source_id="src_text", revision_id="rev_text", extraction_id="ext_text",
                title="Linear Algebra Text", units=units)
    return paths, repository


def _span_of(repository, text_start: str, extraction_id: str = "ext_text") -> str:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = ? AND text LIKE ?",
            (extraction_id, text_start + "%"),
        ).fetchone()
    assert row is not None, text_start
    return str(row["span_id"])


def _ask(paths, repository, span_id, **kwargs):
    tutor = RD.StubReaderClient()
    result = ask_question(load_vault(paths.root), repository, tutor, context="reader",
                          question_md="Why does this step follow?", extraction_id="ext_text",
                          span_id=span_id, clock=CLOCK, **kwargs)
    return tutor.contexts[-1].source_spans, result


# -- 1. nearest neighbours on both sides ------------------------------------------


def test_a_single_block_ask_gets_the_nearest_neighbours_on_both_sides_first(tmp_path):
    paths, repository = _vault(tmp_path)
    step = _span_of(repository, "Paragraph six")
    spans, _ = _ask(paths, repository, step)
    around = [span for span in spans if span["relation"] == "surrounding"]
    texts = [span["text"].split(",")[0].split(" the")[0] for span in around]
    # i-1 and i+1 first, then widening symmetrically: i-2, i+2, i-3, i+3.
    assert [span["span_id"] for span in around] == [
        _span_of(repository, "Paragraph five"), _span_of(repository, "Paragraph seven"),
        _span_of(repository, "Paragraph four"), _span_of(repository, "Paragraph eight"),
        _span_of(repository, "Paragraph three"), _span_of(repository, "Paragraph nine"),
    ], texts
    assert [span["offset"] for span in around] == [-1, 1, -2, 2, -3, 3]


def test_a_multi_block_selection_widens_from_its_own_ends(tmp_path):
    paths, repository = _vault(tmp_path)
    five, six = _span_of(repository, "Paragraph five"), _span_of(repository, "Paragraph six")
    spans, _ = _ask(paths, repository, five, selection_span_ids=[five, six],
                    selection_quote_md="assume A^T = A and Av = tv. hence t is real")
    around = [span["span_id"] for span in spans if span["relation"] == "surrounding"]
    assert around[:2] == [_span_of(repository, "Paragraph four"), _span_of(repository, "Paragraph seven")]
    assert five not in around and six not in around


def test_a_held_out_neighbour_is_skipped_and_the_other_side_still_arrives(tmp_path):
    held = {"ch_held": ("Held-out problems", [("Held-out problem: show the eigenvalues are real.", 1)])}
    paths, repository = _vault(tmp_path, extra_units=held)
    save_unit_selection(repository, "ext_text", ["ch_held", "ch_sym"],
                        exam_use_modes={"ch_held": "held_out_evaluation"})
    header = _span_of(repository, "Chapter 4")
    first = _span_of(repository, "Paragraph two")
    spans, _ = _ask(paths, repository, first)
    delivered = {span["span_id"] for span in spans}
    assert header in delivered  # i-1, the chapter header
    assert _span_of(repository, "Paragraph three") in delivered  # i+1
    assert not delivered & {_span_of(repository, "Held-out problem"), _span_of(repository, "Held-out problems")}


# -- 2. complete blocks within one explicit budget ---------------------------------


def test_reader_neighbours_and_the_block_in_view_arrive_whole(tmp_path):
    chapter = list(CHAPTER)
    chapter[3] = ("Paragraph five, right before the step. " + LONG, 1)
    paths, repository = _vault(tmp_path, chapter=chapter)
    spans, result = _ask(paths, repository, _span_of(repository, "Paragraph six"))
    before = next(span for span in spans if span.get("offset") == -1)
    assert before["text"] == chapter[3][0]  # the whole canonical block, not 240 characters
    assert "trimmed" not in before
    event = repository.question_event(result["event_id"])
    assert "delivery" not in (event["source_context"] or {}) or not event["source_context"]["delivery"]["trimmed"]


def test_the_budget_trims_once_at_the_budget_and_records_it(tmp_path):
    chapter = list(CHAPTER)
    chapter[3] = ("Paragraph five, right before the step. " + LONG * 3, 1)  # about 1,500 tokens
    paths, repository = _vault(tmp_path, chapter=chapter, config="[tutor_qa]\ncontext_token_budget = 1000")
    spans, result = _ask(paths, repository, _span_of(repository, "Paragraph six"))
    total = sum(len(span["text"]) for span in spans)
    assert total <= 1000 * 4
    trimmed = [span for span in spans if span.get("trimmed")]
    assert len(trimmed) == 1 and trimmed[0]["offset"] == -1
    assert chapter[3][0].startswith(trimmed[0]["text"])  # a prefix of the canonical text
    delivery = repository.question_event(result["event_id"])["source_context"]["delivery"]
    assert delivery["budget_tokens"] == 1000
    assert [entry["span_id"] for entry in delivery["trimmed"]] == [trimmed[0]["span_id"]]
    assert delivery["dropped"]  # everything after the trim is left out, and said so


# -- 3. references followed to their numbered block --------------------------------


def test_a_theorem_the_step_cites_is_delivered_and_an_unknown_one_recorded(tmp_path):
    early = {"ch_spec": ("Chapter 3 The spectral theorem", [
        ("Chapter three opens with motivation.", 1),
        (THEOREM, 1),
        ("Proof. Take a unit eigenvector and induct on the dimension.", 1),
        ("Remark: the theorem fails for real matrices that are not symmetric.", 1),
        ("Chapter three continues with orthogonal projections.", 1),
    ])}
    paths, repository = _vault(tmp_path, extra_units=early)
    spans, result = _ask(paths, repository, _span_of(repository, "Paragraph six"))
    referenced = [span for span in spans if span["relation"] == "referenced"]
    assert [span["span_id"] for span in referenced] == [_span_of(repository, "Theorem 3.2")]
    assert referenced[0]["text"] == THEOREM and referenced[0]["reference"] == "Theorem 3.2"
    references = repository.question_event(result["event_id"])["source_context"]["delivery"]["references"]
    assert [entry["reference"] for entry in references["resolved"]] == ["Theorem 3.2"]
    assert [(entry["reference"], entry["reason"]) for entry in references["unresolved"]] == [
        ("Lemma 9.9", "no numbered block with this label")]


def test_a_referenced_theorem_is_citable(tmp_path):
    early = {"ch_spec": ("Chapter 3 The spectral theorem", [(THEOREM, 1)])}
    paths, repository = _vault(tmp_path, extra_units=early)
    _spans, result = _ask(paths, repository, _span_of(repository, "Paragraph six"))
    # The stub cites the first span; the referenced one is in the allowlist too.
    from learnloop.tutor.tutor_qa import _validated_citations
    from learnloop.tutor.ai_contracts import TutorCitation

    class _Answer:
        citations = [TutorCitation(extraction_id="ext_text", span_id=_span_of(repository, "Theorem 3.2"))]

    event = repository.question_event(result["event_id"])
    assert _validated_citations(_Answer(), event["source_context"]["source_spans"])


def test_references_never_cross_sources_or_reach_held_out_material(tmp_path):
    early = {"ch_spec": ("Chapter 3 The spectral theorem", [(THEOREM, 1)])}
    paths, repository = _vault(tmp_path, extra_units=early)
    seed_source(repository, source_id="src_other", revision_id="rev_other", extraction_id="ext_other",
                title="Another book", units={"u": ("Chapter 1", [("Lemma 9.9 (Other book). A lemma elsewhere.", 1)])})
    save_unit_selection(repository, "ext_text", ["ch_spec", "ch_sym"],
                        exam_use_modes={"ch_spec": "held_out_evaluation"})
    spans, result = _ask(paths, repository, _span_of(repository, "Paragraph six"))
    assert not [span for span in spans if span["relation"] == "referenced"]
    assert all(span["extraction_id"] == "ext_text" for span in spans)
    unresolved = repository.question_event(result["event_id"])["source_context"]["delivery"]["references"]["unresolved"]
    assert {entry["reference"] for entry in unresolved} == {"Theorem 3.2", "Lemma 9.9"}
    assert next(entry for entry in unresolved if entry["reference"] == "Theorem 3.2")["reason"] == "held-out material"


def test_reference_resolution_has_a_kill_switch(tmp_path):
    early = {"ch_spec": ("Chapter 3 The spectral theorem", [(THEOREM, 1)])}
    paths, repository = _vault(tmp_path, extra_units=early, config="[tutor_qa]\nresolve_references = false")
    spans, _ = _ask(paths, repository, _span_of(repository, "Paragraph six"))
    assert not [span for span in spans if span["relation"] == "referenced"]


def test_the_reader_manifest_records_what_the_tutor_was_given(tmp_path):
    early = {"ch_spec": ("Chapter 3 The spectral theorem", [(THEOREM, 1)])}
    paths, repository = _vault(tmp_path, extra_units=early)
    tutor = RD.StubReaderClient()
    result = RD.ask(load_vault(paths.root), repository, tutor, extraction_id="ext_text",
                    span_id=_span_of(repository, "Paragraph six"), question_md="Why does this step follow?",
                    clock=CLOCK)
    assert result["manifest"]["source_spans"] == tutor.contexts[-1].source_spans


@pytest.mark.parametrize("text,expected", [
    ("Theorem 1.4.1 (Multiplication rule). Consider a compound experiment", ("theorem", "1.4.1")),
    ("**Theorem 3.2.** Let A be symmetric.", ("theorem", "3.2")),
    ("1.20 definition: vector space", ("definition", "1.20")),
    ("Theorem 1.4.8 tells us how many ordered samples there are.", None),
    ("Theorem 3.2 .......... 45", None),
    ("Proof. Let A be a set.", None),
])
def test_numbered_labels(text, expected):
    from learnloop.ingest.block_roles import numbered_label

    label = numbered_label(text)
    assert (None if label is None else (label.kind, label.number)) == expected


def test_numbered_references():
    from learnloop.ingest.block_roles import numbered_references

    found = numbered_references(
        "Theorems 1.4.7 and 1.4.8 count samples; see Example 1.4.13, equation (3.4) and Lemma 2.1. "
        "By 1.32 the vector is in U, for example 2 apples.")
    assert [(ref.kind, ref.number) for ref in found] == [
        ("theorem", "1.4.7"), ("theorem", "1.4.8"), ("example", "1.4.13"), ("equation", "3.4"),
        ("lemma", "2.1"), (None, "1.32")]


# -- 2 and 3 on the retrieval path: retrieved spans, the verifier, the labeller ---

EIGEN_LONG = (
    "Why the eigenvalues of a real symmetric matrix are real: by Theorem 7.1 every eigenvalue is real, "
    "because the eigenvalues of a symmetric matrix satisfy t = conj(t) for the eigenvector's quadratic form. "
) + (
    "The characteristic polynomial of a real symmetric matrix factors over the reals into linear terms, "
    "and each eigenvalue of the symmetric matrix is a real root with a real eigenvector. "
) * 10
# Worded apart from the question, so the verifier does not pick it on its own.
SPECTRAL = ("Theorem 7.1 (Spectral theorem). Every self-adjoint operator on a finite-dimensional inner "
            "product space is diagonalizable by an orthonormal basis.")


def _retrieval_vault(tmp_path, *, hold_out_theorem: bool = False):
    from learnloop.ai.spend import SpendCaps
    from learnloop.ops.embedding_backfill import backfill_embeddings
    from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES
    from learnloop.vault.writer import upsert_source_set
    from tests.source_retrieval_fakes import HashingEmbedder, build_retrieval_vault, loaded

    paths, repository = build_retrieval_vault(tmp_path / "vault")
    seed_source(repository, source_id="src_spec", revision_id="rev_spec", extraction_id="ext_spec",
                title="Spectral notes", units={
                    "ch_thm": ("Chapter 7 Spectral theory", [(SPECTRAL, 7), ("Proof. Induct on the dimension.", 7)]),
                    "ch_why": ("Chapter 8 Why symmetric matrices have real eigenvalues", [(EIGEN_LONG, 8)]),
                })
    upsert_source_set(paths.root, {
        "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
        "members": [
            {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
            {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
            {"source_id": "src_spec", "revision_id": "rev_spec", "default_role": "primary_textbook"},
        ],
    })
    if hold_out_theorem:
        save_unit_selection(repository, "ext_spec", ["ch_thm", "ch_why"],
                            exam_use_modes={"ch_thm": "held_out_evaluation"})
    caps = SpendCaps(max_candidates=10_000, max_pairs=0, max_calls=100, max_total_tokens=10**8,
                     max_estimated_usd=10.0)
    report = backfill_embeddings(loaded(paths), caps=caps, recipes=("source_block",),
                                 registry=SOURCE_RETRIEVAL_RECIPES, client_factory=HashingEmbedder)
    assert report["status"] == "complete", report
    return paths, repository


def _ask_practice(paths, repository):
    from learnloop.source_retrieval.tutor import TutorSpanProvider
    from tests.source_retrieval_fakes import FakeSourceLLM, HashingEmbedder, loaded
    from tests.test_source_retrieval_tutor import CitingTutor

    llm = FakeSourceLLM()
    provider = TutorSpanProvider(embedder=HashingEmbedder(), rewrite_client=llm, rerank_client=llm, clock=CLOCK)
    tutor = CitingTutor()
    result = ask_question(loaded(paths), repository, tutor, context="practice",
                          question_md="Why are the eigenvalues of a real symmetric matrix real?",
                          practice_item_id="pi_eigen_1", session_id="s1", source_span_provider=provider,
                          clock=CLOCK)
    return tutor.contexts[0].source_spans, result, llm


def test_a_retrieved_span_reaches_the_tutor_and_the_verifier_whole_with_the_theorem_it_cites(tmp_path):
    paths, repository = _retrieval_vault(tmp_path)
    spans, result, llm = _ask_practice(paths, repository)
    long_span = next(span for span in spans if span["text"].startswith("Why the eigenvalues"))
    assert long_span["relation"] == "retrieved" and long_span["text"] == EIGEN_LONG  # not 600 characters
    referenced = [span for span in spans if span["relation"] == "referenced"]
    assert [span["text"] for span in referenced] == [SPECTRAL]
    assert referenced[0]["referenced_from"] == [long_span["extraction_id"], long_span["span_id"]]
    # The verifier judged the complete block too (it read 900 characters).
    passages = [candidate["passage"] for purpose, context in llm.calls if purpose == "source_rerank"
                for candidate in context["candidates"]]
    assert " ".join(EIGEN_LONG.split()) in passages
    manifest = repository.question_event(result["event_id"])["source_context"]["source_retrieval"]
    assert [entry["reference"] for entry in manifest["references"]["resolved"]] == ["Theorem 7.1"]


def test_a_cited_theorem_outside_the_tutors_sources_is_recorded_not_delivered(tmp_path):
    paths, repository = _retrieval_vault(tmp_path, hold_out_theorem=True)
    spans, result, _llm = _ask_practice(paths, repository)
    assert any(span["text"] == EIGEN_LONG for span in spans)
    assert not [span for span in spans if span["relation"] == "referenced"]
    unresolved = repository.question_event(result["event_id"])["source_context"]["source_retrieval"][
        "references"]["unresolved"]
    assert [entry["reference"] for entry in unresolved] == ["Theorem 7.1"]


def test_judge_passages_are_complete_blocks_trimmed_only_past_the_budget():
    from learnloop.source_retrieval.verify import judge_passage

    short = "A short block.\n  With spacing."
    assert judge_passage(short, 900) == ("A short block. With spacing.", False)  # as before: no cut, collapsed
    long = "word " * 1000
    passage, trimmed = judge_passage(long, 16_000)  # the default budget: 4,000 tokens
    assert passage == " ".join(long.split()) and not trimmed  # 4,999 characters: past 900, under the budget
    passage, trimmed = judge_passage(long, 1_000)
    assert trimmed and passage.endswith("…") and len(passage) <= 1_000


def test_the_t6_labeller_reads_complete_blocks(tmp_path):
    from learnloop.ai.spend import SpendCaps
    from learnloop.ops.embedding_compare import SUITES, CompareRequest, run_compare
    from learnloop.ops.pf_calls import ROLE_TASKS
    from learnloop.source_retrieval.contracts import SpanLabels
    from learnloop.source_retrieval.suites import register_suites
    from tests.source_retrieval_fakes import FakeSourceLLM, HashingEmbedder, loaded

    register_suites(SUITES, role_tasks=ROLE_TASKS)
    paths, repository = _retrieval_vault(tmp_path)
    llm = FakeSourceLLM()
    labelled: list[str] = []
    original = llm.complete

    def complete(request):
        if request.result_model is SpanLabels:
            from tests.pf_fakes import prompt_context

            labelled.extend(candidate["passage"] for candidate in prompt_context(request.prompt)["candidates"])
        return original(request)

    llm.complete = complete
    caps = SpendCaps(max_candidates=10_000, max_pairs=10_000, max_calls=5_000, max_total_tokens=10**9,
                     max_estimated_usd=10**4)
    request = CompareRequest(suite="source_retrieval", output_dir=tmp_path / "out", max_cases=6,
                             views=("substring", "keyword"))
    report = run_compare(loaded(paths), request=request, caps=caps, price_per_million=1.0,
                         clients={"source_question_writer": llm, "source_relevance": llm, "source_rewrite": llm,
                                  "source_verify": llm},
                         embedding_clients={"qwen/qwen3-embedding-8b": HashingEmbedder()})
    assert report["status"] == "complete", report.get("reason")
    # The labeller reads the embedded recipe text ("Section: ..." then the
    # block): the whole block, 2,000+ characters, not 900.
    assert any(passage.endswith(" ".join(EIGEN_LONG.split())) for passage in labelled)
    assert report["results"]["passages"]["label_trimmed"] == 0


def test_a_pinned_passage_arrives_whole_with_the_theorem_it_cites(tmp_path):
    from learnloop.source_retrieval.tutor import PinnedSpanProvider
    from tests.source_retrieval_fakes import loaded
    from tests.test_source_retrieval_tutor import CitingTutor

    paths, repository = _retrieval_vault(tmp_path)
    long_span = _span_of(repository, "Why the eigenvalues", "ext_spec")
    tutor = CitingTutor()
    result = ask_question(loaded(paths), repository, tutor, context="practice",
                          question_md="Explain this with my work", practice_item_id="pi_eigen_1",
                          session_id="s1", source_span_provider=PinnedSpanProvider([f"ext_spec:{long_span}"]),
                          clock=CLOCK)
    spans = tutor.contexts[0].source_spans
    assert [(span["relation"], span["text"]) for span in spans] == [("retrieved", EIGEN_LONG),
                                                                      ("referenced", SPECTRAL)]
    manifest = repository.question_event(result["event_id"])["source_context"]["source_retrieval"]
    assert manifest["basis"] == "pinned" and manifest["spans"] == 1
    assert manifest["span_keys"] == [f"ext_spec:{long_span}"]
