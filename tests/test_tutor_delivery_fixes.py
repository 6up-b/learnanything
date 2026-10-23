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
from learnloop.tutor.context_delivery import BlockSource, follow_references
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.loader import load_vault
from tests.helpers import append_config_toml, create_basic_vault
from tests.source_retrieval_fakes import seed_source

# The legacy Codex HTTP adapter is refused by the tool lockdown (hardening round 2,
# H3); these tests drive an in-process HTTP server through it as a provider double.
pytestmark = pytest.mark.usefixtures("legacy_codex_http_double")

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


def _retrieval_vault(tmp_path, *, hold_out_theorem: bool = False, long_text: str = EIGEN_LONG,
                     config: str | None = None):
    from learnloop.ai.spend import SpendCaps
    from learnloop.ops.embedding_backfill import backfill_embeddings
    from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES
    from learnloop.vault.writer import upsert_source_set
    from tests.source_retrieval_fakes import HashingEmbedder, build_retrieval_vault, loaded

    paths, repository = build_retrieval_vault(tmp_path / "vault")
    if config:
        append_config_toml(paths.root, config)
    seed_source(repository, source_id="src_spec", revision_id="rev_spec", extraction_id="ext_spec",
                title="Spectral notes", units={
                    "ch_thm": ("Chapter 7 Spectral theory", [(SPECTRAL, 7), ("Proof. Induct on the dimension.", 7)]),
                    "ch_why": ("Chapter 8 Why symmetric matrices have real eigenvalues", [(long_text, 8)]),
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


def _labelled_passages(paths) -> tuple[list[str], dict]:
    """Run the T6 report on fakes; the passages the labeller read, and the results."""

    from learnloop.ai.spend import SpendCaps
    from learnloop.ops.embedding_compare import SUITES, CompareRequest, run_compare
    from learnloop.ops.pf_calls import ROLE_TASKS
    from learnloop.source_retrieval.contracts import SpanLabels
    from learnloop.source_retrieval.suites import register_suites
    from tests.source_retrieval_fakes import FakeSourceLLM, HashingEmbedder, loaded

    register_suites(SUITES, role_tasks=ROLE_TASKS)
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
    request = CompareRequest(suite="source_retrieval", output_dir=paths.root.parent / "out", max_cases=6,
                             views=("substring", "keyword"))
    report = run_compare(loaded(paths), request=request, caps=caps, price_per_million=1.0,
                         clients={"source_question_writer": llm, "source_relevance": llm, "source_rewrite": llm,
                                  "source_verify": llm},
                         embedding_clients={"qwen/qwen3-embedding-8b": HashingEmbedder()})
    assert report["status"] == "complete", report.get("reason")
    return labelled, report


def test_the_t6_labeller_reads_complete_blocks(tmp_path):
    paths, _repository = _retrieval_vault(tmp_path)
    labelled, report = _labelled_passages(paths)
    # The labeller reads "Section: ..." then the block: the whole block,
    # 2,000+ characters, not 900.
    assert any(passage.endswith(" ".join(EIGEN_LONG.split())) for passage in labelled)
    assert report["results"]["passages"]["label_trimmed"] == 0
    assert report["manifest"]["benchmark"]["version"] == "t6-eval-v3"


#: Codex review F2: a passage past the embedding recipe's 6,000-character cap
#: whose decisive assumption comes last.
ASSUMPTION = "All of this assumes the matrix is real and symmetric; a complex matrix needs the Hermitian version."
PAST_RECIPE_CAP = (
    "Why the eigenvalues of a real symmetric matrix are real: by Theorem 7.1 every eigenvalue is real. "
    + "The quadratic form argument gives t = conj(t) for each eigenvector of the symmetric matrix. " * 70
)[:6_400] + " " + ASSUMPTION


def test_the_t6_labeller_reads_a_block_past_the_embedding_recipes_cap_whole(tmp_path):
    assert len(PAST_RECIPE_CAP) > 6_000 and PAST_RECIPE_CAP.index(ASSUMPTION) > 6_000
    paths, _repository = _retrieval_vault(tmp_path, long_text=PAST_RECIPE_CAP)
    labelled, report = _labelled_passages(paths)
    long_passages = [passage for passage in labelled if "quadratic form argument" in passage]
    assert long_passages and all(passage.endswith(ASSUMPTION) for passage in long_passages)
    assert report["results"]["passages"]["label_trimmed"] == 0


def test_a_trim_between_the_recipe_cap_and_the_block_length_is_counted(tmp_path):
    # 1,600 tokens = 6,400 characters: past the recipe's 6,000, short of the block.
    paths, _repository = _retrieval_vault(tmp_path, long_text=PAST_RECIPE_CAP,
                                          config="[source_retrieval]\npassage_token_budget = 1600")
    labelled, report = _labelled_passages(paths)
    from learnloop.source_retrieval.evaluation import LABEL_PROMPT_VERSIONS

    long_passages = [passage for passage in labelled if "quadratic form argument" in passage]
    assert long_passages and all(6_000 < len(passage) <= 6_400 for passage in long_passages)
    assert report["results"]["passages"]["label_trimmed"] * len(LABEL_PROMPT_VERSIONS) == len(long_passages)


def test_the_t6_labeller_counts_a_trim_at_the_passage_budget(tmp_path):
    paths, _repository = _retrieval_vault(tmp_path, long_text=PAST_RECIPE_CAP,
                                          config="[source_retrieval]\npassage_token_budget = 1000")
    labelled, report = _labelled_passages(paths)
    long_passages = [passage for passage in labelled if "quadratic form argument" in passage]
    assert long_passages and all(len(passage) <= 4_000 and passage.endswith("…") for passage in long_passages)
    # Counted once per candidate, though both labelling passes read it.
    from learnloop.source_retrieval.evaluation import LABEL_PROMPT_VERSIONS

    assert report["results"]["passages"]["label_trimmed"] * len(LABEL_PROMPT_VERSIONS) == len(long_passages)


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


# -- Codex review F1: a linked span's references keep the item's exclusions -------
#
# When retrieval keeps the learning object's linked spans (no provider, or the
# provider declined), the numbered blocks those spans cite pass the same rules a
# retrieved span's references pass: the tutor's teaching scope for the question
# (``source_retrieval.tutor.linked_reference_filter``, injected by the adapter),
# so the item's database links, the same text in another extraction of its
# source and a solution region's body never arrive. Without the injected rules
# nothing is followed (fail closed).

WORKED = "Example 3.2 (A diagonal matrix). Find the eigenvalues of the diagonal matrix diag(5, 7)."
WORKED_BODY = "The eigenvalues of diag(5, 7) are its diagonal entries, read off the matrix."
TEACHING = "A diagonal matrix has its diagonal entries as eigenvalues, as Example 3.2 shows."
WORKED_EQUATION = "Example 3.3 (Characteristic equation). Find the eigenvalues of the matrix [[2, 1], [1, 2]]."
SOLUTION_LEAD = "Solution."
SOLUTION_EQUATION = "$$ t^2 - 4t + 3 = 0 \\tag{3.4} $$"
EQUATION_TEACHING = "The roots of the characteristic equation (3.4) are the eigenvalues of the matrix."


def _seed_hinted(repository, *, source_id: str, revision_id: str, extraction_id: str,
                 rows: list[tuple[str, str]], register: bool = True) -> None:
    """One chapter (header s1, then ``rows`` as s2, s3, ...) whose blocks carry
    the extractor's role hints, as Marker's normalizer assigns them."""

    from learnloop.ingest.block_roles import classify_block_role
    from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
    from tests.test_source_inventory import _persist

    if register:
        with repository.connection() as connection:
            connection.execute(
                "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, "
                "current_revision_id, reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (source_id, "pdf", f"file:///{source_id}.pdf", "Eigen text", revision_id, 1,
                 "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
            connection.execute(
                "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
                (revision_id, source_id, f"sha256:{source_id}", None, "2026-01-01T00:00:00Z"))
            connection.commit()
    header, ref = "Chapter 3 Eigenvalues", "/page/1/SectionHeader/1"
    blocks = [DocumentBlock.build(span_id="s1", block_type="SectionHeader", text=header, ordinal=1, page=1,
                                  section_path=[ref], extractor_block_id=ref)]
    for index, (text, block_type) in enumerate(rows, start=2):
        blocks.append(DocumentBlock.build(span_id=f"s{index}", block_type=block_type, text=text, ordinal=index,
                                          page=1, section_path=[ref],
                                          role_hint=classify_block_role(block_type, [], text)))
    unit = DocumentUnit(unit_id="ch3", label=header, ordinal=0, semantic_hash=f"sha256:{extraction_id}",
                        page_start=1, page_end=1, span_ids=[block.span_id for block in blocks])
    _persist(repository, DocumentIR(extractor="marker", extractor_version=extraction_id, units=[unit],
                                    blocks=blocks, assets=[], health=ExtractionHealth()),
             revision_id=revision_id, extraction_id=extraction_id)


def _linked_vault(tmp_path, rows: list[tuple[str, str]], *, teaching_span: str):
    """The retrieval vault plus a primary textbook ``src_eigen`` (``ext_eigen``)
    whose ``teaching_span`` is lo_matrices' linked passage."""

    from learnloop.vault.writer import upsert_source_set
    from tests.source_retrieval_fakes import build_retrieval_vault

    paths, repository = build_retrieval_vault(tmp_path / "vault", embeddings=False)
    _seed_hinted(repository, source_id="src_eigen", revision_id="rev_eigen", extraction_id="ext_eigen", rows=rows)
    upsert_source_set(paths.root, {
        "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
        "members": [
            {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
            {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
            {"source_id": "src_eigen", "revision_id": "rev_eigen", "default_role": "primary_textbook"},
        ],
    })
    repository.insert_entity_source_link(
        entity_type="learning_object", entity_id="lo_matrices", locator=f"span:ext_eigen/{teaching_span}",
        relation="primary", source_id="src_eigen", revision_id="rev_eigen", extraction_id="ext_eigen")
    return paths, repository


def _ask_linked(paths, repository, *, item: str = "pi_eigen_1", injected: bool = True):
    from tests.source_retrieval_fakes import loaded
    from tests.test_source_retrieval_tutor import CitingTutor

    tutor = CitingTutor()
    extra: dict = {}
    if injected:
        from learnloop.source_retrieval.tutor import linked_reference_filter

        extra["linked_reference_filter"] = linked_reference_filter
    result = ask_question(loaded(paths), repository, tutor, context="practice",
                          question_md="Why are these the eigenvalues?", practice_item_id=item, session_id="s1",
                          clock=CLOCK, **extra)
    spans = tutor.contexts[0].source_spans
    delivery = (repository.question_event(result["event_id"])["source_context"] or {}).get("delivery") or {}
    return spans, delivery


def test_a_linked_spans_reference_to_the_items_own_example_is_refused_by_its_database_link(tmp_path):
    paths, repository = _linked_vault(
        tmp_path, [(WORKED, "Text"), (WORKED_BODY, "Text"), (TEACHING, "Text")], teaching_span="s4")
    # The item was made from Example 3.2: linked in the database only (no YAML provenance).
    repository.insert_entity_source_link(
        entity_type="practice_item", entity_id="pi_eigen_1", locator="span:ext_eigen/s2", relation="primary",
        source_id="src_eigen", revision_id="rev_eigen", extraction_id="ext_eigen")
    spans, delivery = _ask_linked(paths, repository)
    assert [span["text"] for span in spans] == [TEACHING]
    assert not {WORKED, WORKED_BODY} & {span["text"] for span in spans}
    unresolved = delivery["references"]["unresolved"]
    assert [(entry["reference"], entry["span_id"]) for entry in unresolved] == [("Example 3.2", "s2")]
    # Another item of the same learning object is not made from it: it is the tutor's scaffold there.
    other, _ = _ask_linked(paths, repository, item="pi_eigen_2")
    assert [span["text"] for span in other if span["relation"] == "referenced"] == [WORKED]


def test_a_linked_spans_reference_to_a_re_extracted_copy_of_the_items_example_is_refused(tmp_path):
    rows = [(WORKED, "Text"), (WORKED_BODY, "Text"), (TEACHING, "Text")]
    paths, repository = _linked_vault(tmp_path, rows, teaching_span="s4")
    # The item links the same example in an older extraction of the same source.
    _seed_hinted(repository, source_id="src_eigen", revision_id="rev_eigen", extraction_id="ext_eigen_old",
                 rows=[("Front matter.", "Text"), *rows], register=False)
    repository.insert_entity_source_link(
        entity_type="practice_item", entity_id="pi_eigen_1", locator="span:ext_eigen_old/s3", relation="support",
        source_id="src_eigen", revision_id="rev_eigen", extraction_id="ext_eigen_old")
    spans, delivery = _ask_linked(paths, repository)
    assert WORKED not in {span["text"] for span in spans}
    assert [entry["reference"] for entry in delivery["references"]["unresolved"]] == ["Example 3.2"]


def test_a_linked_spans_reference_into_a_solution_regions_body_is_refused_while_practising(tmp_path):
    paths, repository = _linked_vault(tmp_path, [
        (WORKED_EQUATION, "Text"), (SOLUTION_LEAD, "Text"), (SOLUTION_EQUATION, "Equation"),
        ("Chapter three continues with the spectral theorem.", "Text"), (EQUATION_TEACHING, "Text"),
    ], teaching_span="s6")
    spans, delivery = _ask_linked(paths, repository)
    assert SOLUTION_EQUATION not in {span["text"] for span in spans}
    assert [(entry["reference"], entry["span_id"]) for entry in delivery["references"]["unresolved"]] == [
        ("Equation 3.4", "s4")]


def test_without_the_adapters_rules_a_linked_spans_references_are_not_followed(tmp_path):
    paths, repository = _linked_vault(
        tmp_path, [(WORKED, "Text"), (WORKED_BODY, "Text"), (TEACHING, "Text")], teaching_span="s4")
    spans, _delivery = _ask_linked(paths, repository, item="pi_eigen_2", injected=False)
    assert [span["text"] for span in spans] == [TEACHING]  # fail closed: no exclusions, no references


def test_the_sidecar_injects_the_linked_reference_rules(tmp_path, monkeypatch):
    from learnloop.source_retrieval.tutor import linked_reference_filter
    from learnloop_sidecar.handlers import tutor_qa as handler
    from tests.test_sidecar_tutor_qa import _TutorServer, _init, _rpc, _tutor_vault

    seen: list[dict] = []
    real = handler.ask_question

    def capture(*args, **kwargs):
        seen.append(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(handler, "ask_question", capture)
    server = _TutorServer()
    server.start()
    try:
        vault_root, _paths = _tutor_vault(tmp_path, server)
        session = _rpc([_init(vault_root), {"jsonrpc": "2.0", "id": 2, "method": "start_session",
                                            "params": {"energy": "medium"}}])[1]["result"]["sessionId"]
        response = _rpc([_init(vault_root), {"jsonrpc": "2.0", "id": 2, "method": "ask_tutor_question", "params": {
            "context": "practice", "question": "Why orthogonal?", "practiceItemId": "pi_svd_define_001",
            "sessionId": session, "secondsIntoAttempt": 12.0}}])[1]
    finally:
        server.stop()
    assert "result" in response, response
    assert seen and seen[0]["linked_reference_filter"] is linked_reference_filter


# -- Codex review F6: a numbered statement ending in a number is not a TOC line ----


@pytest.mark.parametrize("text,block_type,expected", [
    ("Theorem 3.2. The derivative of a constant is 0", "Text", ("theorem", "3.2")),
    ("Definition 1.1. A group of order 2", "Text", ("definition", "1.1")),
    ("Lemma 2.4: every subgroup of index 2", "Text", ("lemma", "2.4")),
    # Axler's number-first labels whose OCR ends in a number (the copies' own blocks).
    ("1.31 a number times the vector 0", "Text", (None, "1.31")),
    ("1.15 notation: 0", "SectionHeader", (None, "1.15")),
    ("1.7 example: 2 and 3", "SectionHeader", ("example", "1.7")),
    # Table-of-contents lines: a TOC block, leaders, or a page number in its own column.
    ("Theorem 3.2 Spectral theorem 45", "TableOfContents", None),
    ("Theorem 3.2 .......... 45", "Text", None),
    ("Theorem 3.2\tSpectral theorem\t45", "Text", None),
    ("Theorem 3.2 Spectral theorem    45", "Text", None),
    # A course number glued to letters is not a number-first label.
    ("6.041SC Probabilistic Systems Analysis and Applied Probability Fall 2013", "Text", None),
])
def test_numbered_statements_ending_in_a_number_are_labels_and_toc_lines_are_not(text, block_type, expected):
    from learnloop.ingest.block_roles import numbered_label

    label = numbered_label(text, block_type)
    assert (None if label is None else (label.kind, label.number)) == expected


def test_by_theorem_resolves_to_a_statement_ending_in_a_number(tmp_path):
    chapter = list(CHAPTER)
    chapter[0] = ("Theorem 3.2. The derivative of a constant is 0", 1)
    paths, repository = _vault(tmp_path, chapter=chapter)
    spans, result = _ask(paths, repository, _span_of(repository, "Paragraph six"))
    referenced = [span for span in spans if span["relation"] == "referenced"]
    # The statement block leads (an unpunctuated end may take the next block as its continuation).
    assert referenced[0]["text"] == "Theorem 3.2. The derivative of a constant is 0"
    assert referenced[0]["reference"] == "Theorem 3.2"
    references = repository.question_event(result["event_id"])["source_context"]["delivery"]["references"]
    assert [entry["reference"] for entry in references["resolved"]] == ["Theorem 3.2"]


# -- Codex review F5: the kill switches restore the predecessor's delivery ---------

_ROLLBACK = "[tutor_qa]\nexpanded_delivery = false\nresolve_references = false"


def _predecessor_reader_spans(repository, extraction_id, span_id, *, selection_span_ids=(),
                              selection_quote_md=None, withheld=None):
    """tutor_qa._reader_source_spans as it was at 4cf54a295 (mvp-0.22), verbatim
    but for the module-level names: the reference the kill switch must restore."""

    from learnloop.reader.span_view import SpanViewError, build_span_view

    if not extraction_id or not span_id:
        return []
    try:
        view = build_span_view(repository, extraction_id, span_id, record=False)
    except SpanViewError:
        return []
    spans = []

    def _label(text):
        text = " ".join((text or "").split())
        return text[:59].rstrip() + "…" if len(text) > 60 else text

    if selection_quote_md and selection_quote_md.strip():
        spans.append({"extraction_id": extraction_id, "span_id": span_id, "label": "learner selection",
                      "text": selection_quote_md, "relation": "selected_text"})
    spans.append({"extraction_id": extraction_id, "span_id": span_id, "label": _label(view.get("text")),
                  "text": view.get("text"), "relation": "in_view"})
    for extra_id in list(dict.fromkeys(selection_span_ids))[:8]:
        if extra_id == span_id:
            continue
        try:
            extra = build_span_view(repository, extraction_id, extra_id, record=False)
        except SpanViewError:
            continue
        spans.append({"extraction_id": extraction_id, "span_id": extra_id, "label": _label(extra.get("text")),
                      "text": extra.get("text"), "relation": "in_view"})
    max_spans = max(4, len(spans) + 2)
    for neighbour in (view.get("previous_spans") or []) + (view.get("next_spans") or []):
        nid = neighbour.get("span_id")
        if nid is None or (withheld is not None and withheld.covers(str(extraction_id), str(nid))):
            continue
        spans.append({"extraction_id": extraction_id, "span_id": nid, "label": _label(neighbour.get("text")),
                      "text": neighbour.get("text"), "relation": "surrounding"})
        if len(spans) >= max_spans:
            break
    return spans


@pytest.mark.parametrize("case", ["one_block", "quote", "multi_block", "held_out_neighbour"])
def test_the_expanded_delivery_kill_switch_restores_the_predecessors_reader_window(tmp_path, case):
    from learnloop.content.sources.exam_material import held_out_material

    chapter = list(CHAPTER)
    chapter[3] = ("Paragraph five, right before the step. " + LONG, 1)  # past the 240-character preview
    chapter[5] = ("Paragraph seven, right after the step. " + LONG, 2)
    held = {"ch_held": ("Held-out problems", [("Held-out problem: show the eigenvalues are real.", 1)])}
    paths, repository = _vault(tmp_path, chapter=chapter, config=_ROLLBACK,
                               extra_units=held if case == "held_out_neighbour" else None)
    if case == "held_out_neighbour":
        save_unit_selection(repository, "ext_text", ["ch_held", "ch_sym"],
                            exam_use_modes={"ch_held": "held_out_evaluation"})
    five, six = _span_of(repository, "Paragraph five"), _span_of(repository, "Paragraph six")
    primary, kwargs = six, {}
    if case == "quote":
        kwargs = {"selection_quote_md": "hence t is real"}
    elif case == "multi_block":
        primary, kwargs = five, {"selection_span_ids": [five, six], "selection_quote_md": "assume A^T = A. hence"}
    elif case == "held_out_neighbour":
        primary = _span_of(repository, "Paragraph two")
    spans, _result = _ask(paths, repository, primary, **kwargs)
    expected = _predecessor_reader_spans(
        repository, "ext_text", primary, withheld=held_out_material(load_vault(paths.root), repository), **kwargs)
    assert spans == expected
    if case == "one_block":  # not vacuous: i-3, i-2 and the 240-character preview of i-1, nothing after
        assert [len(span["text"]) for span in spans if span["relation"] == "surrounding"][-1] == 240


def test_with_the_kill_switch_on_the_reader_still_gets_complete_nearest_neighbours(tmp_path):
    chapter = list(CHAPTER)
    chapter[3] = ("Paragraph five, right before the step. " + LONG, 1)
    paths, repository = _vault(tmp_path, chapter=chapter)
    spans, _ = _ask(paths, repository, _span_of(repository, "Paragraph six"))
    assert next(span for span in spans if span.get("offset") == -1)["text"] == chapter[3][0]


def test_the_expanded_delivery_kill_switch_restores_the_600_character_retrieved_span(tmp_path):
    paths, repository = _retrieval_vault(tmp_path, config=_ROLLBACK)
    spans, _result, llm = _ask_practice(paths, repository)
    long_span = next(span for span in spans if span["text"].startswith("Why the eigenvalues"))
    assert long_span["text"] == " ".join(EIGEN_LONG.split())[:600]  # span_context's predecessor cut
    assert not [span for span in spans if span["relation"] == "referenced"]


def test_the_expanded_delivery_kill_switch_keeps_a_linked_span_at_its_600_character_cut(tmp_path):
    teaching = TEACHING + " " + LONG
    paths, repository = _linked_vault(tmp_path, [(WORKED, "Text"), (WORKED_BODY, "Text"), (teaching, "Text")],
                                      teaching_span="s4")
    expanded, _ = _ask_linked(paths, repository, item="pi_eigen_2")
    assert expanded[0]["text"] == teaching  # completed from the block
    append_config_toml(paths.root, _ROLLBACK)
    rolled_back, _ = _ask_linked(paths, repository, item="pi_eigen_2")
    assert [span["text"] for span in rolled_back] == [teaching.strip()[:600]]  # the predecessor, unhydrated


def test_the_complete_passages_kill_switch_restores_the_judges_900_characters(tmp_path):
    from learnloop.source_retrieval.recipes import source_block_text

    paths, repository = _retrieval_vault(tmp_path, config="[source_retrieval]\ncomplete_passages = false")
    _spans, _result, llm = _ask_practice(paths, repository)
    passages = [candidate["passage"] for purpose, context in llm.calls if purpose == "source_rerank"
                for candidate in context["candidates"]]
    collapsed = " ".join(EIGEN_LONG.split())
    assert collapsed[:899] + "…" in passages and collapsed not in passages
    labelled, report = _labelled_passages(paths)
    assert labelled and all(len(passage) <= 900 for passage in labelled)
    from learnloop.db.connection import connect
    from learnloop.db.stores.source_block_fts import blocks_by_key, section_header_titles
    from contextlib import closing

    span = _span_of(repository, "Why the eigenvalues", "ext_spec")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        block = blocks_by_key(connection, [("ext_spec", span)])[("ext_spec", span)]
        embedded = source_block_text(block, section_header_titles(connection, "ext_spec"))
    predecessor = " ".join(embedded.split())[:899] + "…"  # bench.clip(source_block_text(...), 900)
    assert predecessor in labelled
    assert report["results"]["passages"]["complete"] is False
    assert report["manifest"]["benchmark"]["version"] == "t6-eval-v2"


# -- Codex re-review F7: the exercise and solution lead guard survives F1 ------------
#
# The teaching scope drops exercise and solution blocks by their role hints. A
# lecture transcript's captions all carry ``ordinary_prose`` (the caption
# normalizer cannot tell), and a Marker block may carry no hint or a wrong one:
# the block's own lead ("Exercise 3.2", "Problem 3.2.", "Solution:") still keeps
# it from an item-bound tutor, as the predecessor's linked-span filter did.

EXERCISE_CAPTION = "Exercise 3.2: show that every real symmetric matrix has real eigenvalues."
CITING_CAPTION = "As Exercise 3.2 asks, the eigenvalues of a symmetric matrix are real numbers."
LEAD_REFUSED = "an exercise or solution, while the item is being practised"


def _seed_ir(repository, ir, *, source_id: str, revision_id: str, extraction_id: str) -> None:
    from tests.test_source_inventory import _persist

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, "
            "current_revision_id, reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (source_id, "transcript", f"file:///{source_id}.vtt", "Lecture 3", revision_id, 1,
             "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            (revision_id, source_id, f"sha256:{source_id}", None, "2026-01-01T00:00:00Z"))
        connection.commit()
    _persist(repository, ir, revision_id=revision_id, extraction_id=extraction_id)


def _linked_ir_vault(tmp_path, ir, *, teaching_span: str):
    """The retrieval vault plus a teaching source ``src_lecture`` (``ext_lecture``)
    built from ``ir``, whose ``teaching_span`` is lo_matrices' linked passage."""

    from learnloop.vault.writer import upsert_source_set
    from tests.source_retrieval_fakes import build_retrieval_vault

    paths, repository = build_retrieval_vault(tmp_path / "vault", embeddings=False)
    _seed_ir(repository, ir, source_id="src_lecture", revision_id="rev_lecture", extraction_id="ext_lecture")
    upsert_source_set(paths.root, {
        "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
        "members": [
            {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
            {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
            {"source_id": "src_lecture", "revision_id": "rev_lecture", "default_role": "primary_textbook"},
        ],
    })
    repository.insert_entity_source_link(
        entity_type="learning_object", entity_id="lo_matrices", locator=f"span:ext_lecture/{teaching_span}",
        relation="primary", source_id="src_lecture", revision_id="rev_lecture", extraction_id="ext_lecture")
    return paths, repository


def _caption_vault(tmp_path):
    from learnloop.ingest.extractors.normalizers import captions_to_ir

    ir = captions_to_ir([
        {"start": 0.0, "end": 4.0, "text": "Today we look at symmetric matrices."},
        {"start": 4.0, "end": 9.0, "text": EXERCISE_CAPTION},
        {"start": 9.0, "end": 14.0, "text": CITING_CAPTION},
    ], title="Lecture 3")
    assert {block.role_hint for block in ir.blocks} == {"ordinary_prose"}  # the normalizer cannot tell
    return _linked_ir_vault(tmp_path, ir, teaching_span="s3")


def _hinted_ir(rows: list[tuple[str, str, str | None]]):
    """A Marker chapter (header s1, then ``rows`` as s2, s3, ...) whose blocks
    carry exactly the given role hints (None: an extraction without hints)."""

    from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth

    header, ref = "Chapter 3 Eigenvalues", "/page/1/SectionHeader/1"
    blocks = [DocumentBlock.build(span_id="s1", block_type="SectionHeader", text=header, ordinal=1, page=1,
                                  section_path=[ref], extractor_block_id=ref)]
    for index, (text, block_type, hint) in enumerate(rows, start=2):
        blocks.append(DocumentBlock.build(span_id=f"s{index}", block_type=block_type, text=text, ordinal=index,
                                          page=1, section_path=[ref], role_hint=hint))
    unit = DocumentUnit(unit_id="ch3", label=header, ordinal=0, semantic_hash="sha256:ext_lecture",
                        page_start=1, page_end=1, span_ids=[block.span_id for block in blocks])
    return DocumentIR(extractor="marker", extractor_version="ext_lecture", units=[unit], blocks=blocks, assets=[],
                      health=ExtractionHealth())


def _unresolved(delivery) -> list[tuple[str, str, str]]:
    return [(entry["reference"], entry["span_id"], entry["reason"])
            for entry in delivery["references"]["unresolved"]]


def test_a_linked_captions_reference_to_an_exercise_caption_is_refused_while_practising(tmp_path):
    paths, repository = _caption_vault(tmp_path)
    spans, delivery = _ask_linked(paths, repository)
    assert [span["text"] for span in spans] == [CITING_CAPTION]
    assert EXERCISE_CAPTION not in {span["text"] for span in spans}
    assert _unresolved(delivery) == [("Exercise 3.2", "s2", LEAD_REFUSED)]


@pytest.mark.parametrize("hint", [None, "ordinary_prose", "theorem"])
def test_a_linked_spans_reference_to_an_exercise_with_a_missing_or_wrong_hint_is_refused(tmp_path, hint):
    exercise = "Problem 3.2. Show that every real symmetric matrix has real eigenvalues."
    citing = "By Problem 3.2, the eigenvalues of a real symmetric matrix are real numbers."
    paths, repository = _linked_ir_vault(
        tmp_path, _hinted_ir([(exercise, "Text", hint), (citing, "Text", "ordinary_prose")]), teaching_span="s3")
    spans, delivery = _ask_linked(paths, repository)
    assert [span["text"] for span in spans] == [citing]
    assert _unresolved(delivery) == [("Problem 3.2", "s2", LEAD_REFUSED)]


def test_an_exercise_continuing_a_cited_theorem_is_cut_while_practising(tmp_path):
    theorem = "Theorem 3.5. Every real symmetric matrix has real eigenvalues and"
    rest = "an orthonormal basis of eigenvectors, as the page goes on to check in"  # an open sentence
    exercise = "Exercise: verify the theorem for the matrix [[2, 1], [1, 2]] and find its eigenvalues"
    citing = "By Theorem 3.5, a symmetric matrix can be diagonalized by an orthogonal matrix."
    paths, repository = _linked_ir_vault(tmp_path, _hinted_ir([
        (theorem, "Text", "theorem"), (rest, "Text", "ordinary_prose"), (exercise, "Text", "ordinary_prose"),
        ("Section 3.6 turns to Hermitian matrices", "Text", "ordinary_prose"), (citing, "Text", "ordinary_prose"),
    ]), teaching_span="s6")
    spans, delivery = _ask_linked(paths, repository)
    referenced = [span["text"] for span in spans if span["relation"] == "referenced"]
    assert referenced == [theorem, rest]  # the statement, never the exercise that continues the page
    assert [entry["reference"] for entry in delivery["references"]["resolved"]] == ["Theorem 3.5"]
    # Another context than practice or feedback keeps the predecessor's rule: the lead guard is item-bound.
    from learnloop.source_retrieval.tutor import reference_filter, tutor_scope
    from tests.source_retrieval_fakes import loaded

    vault = loaded(paths)
    item = vault.practice_items["pi_eigen_1"]
    block = BlockSource(repository.sqlite_path).block("ext_lecture", "s4")
    bound = reference_filter(vault, repository, tutor_scope(vault, repository, context="practice",
                                                            learning_object_ids=["lo_matrices"], item=item),
                             item=item)
    library = reference_filter(vault, repository, tutor_scope(vault, repository, context="library",
                                                              learning_object_ids=["lo_matrices"], item=None),
                               item=None)
    assert bound("ext_lecture", block) == LEAD_REFUSED
    assert library("ext_lecture", block) is None


def test_a_retrieved_spans_reference_to_an_exercise_caption_is_refused_while_practising(tmp_path):
    # The retrieved and pinned providers share reference_filter with the linked fallback.
    from learnloop.source_retrieval.tutor import reference_filter, tutor_scope
    from tests.source_retrieval_fakes import loaded

    paths, repository = _caption_vault(tmp_path)
    vault = loaded(paths)
    item = vault.practice_items["pi_eigen_1"]
    scope = tutor_scope(vault, repository, context="practice", learning_object_ids=["lo_matrices"], item=item)
    found = follow_references(
        BlockSource(repository.sqlite_path),
        [{"extraction_id": "ext_lecture", "span_id": "s3", "text": CITING_CAPTION}],
        allow=reference_filter(vault, repository, scope, item=item), delivered={("ext_lecture", "s3")})
    assert found.spans == []
    assert [(entry["span_id"], entry["reason"]) for entry in found.unresolved] == [("s2", LEAD_REFUSED)]
