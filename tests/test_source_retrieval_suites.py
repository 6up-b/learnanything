"""Slice 2 T6 on the shared compare harness: the source_retrieval report and benchmark B4."""
from __future__ import annotations

from contextlib import closing
import hashlib
import io
import json

import pytest
from typer.testing import CliRunner

from learnloop.ai.spend import SpendCaps
from learnloop.cli import app
from learnloop.db.connection import connect
from learnloop.ingest.originals import store_original_bytes
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.ops.embedding_compare import SUITES, CompareRequest, run_compare
from learnloop.ops.pf_calls import ROLE_TASKS
from learnloop.source_retrieval.dense import clear_cache
from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES
from learnloop.source_retrieval.suites import register_suites
from tests.source_retrieval_fakes import (
    FakeSourceLLM,
    HashingEmbedder,
    build_retrieval_vault,
    loaded,
    seed_source,
)

CAPS = SpendCaps(max_candidates=10_000, max_pairs=10_000, max_calls=5_000, max_total_tokens=10**9,
                 max_estimated_usd=10**4)
QWEN = "qwen/qwen3-embedding-8b"
GEMINI = "google/gemini-embedding-2"


@pytest.fixture(autouse=True)
def _registered():
    clear_cache()
    register_suites(SUITES, role_tasks=ROLE_TASKS)
    yield
    clear_cache()


class FakeMultimodalEmbedder(HashingEmbedder):
    model_id = model = GEMINI
    modalities = frozenset({"text", "image"})

    def __init__(self):
        super().__init__()
        self.images = 0

    def embed(self, inputs, task_prefix):
        texts = []
        for value in inputs:
            if isinstance(value, str):
                texts.append(value)
            else:
                self.images += 1
                texts.append("image " + hashlib.sha256(value[1]).hexdigest()[:12])
        return super().embed(texts, task_prefix)


def _ledger(repository, task="source_relevance") -> int:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE task = ?", (task,)).fetchone()[0]


def _receipts(repository) -> int:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return connection.execute("SELECT COUNT(*) FROM model_call_receipts").fetchone()[0]


def test_register_suites_is_idempotent_and_refuses_a_conflict():
    register_suites(SUITES, role_tasks=ROLE_TASKS)
    assert {"source_retrieval", "b4", "b2", "valid_alternative"} <= set(SUITES)
    assert ROLE_TASKS["source_relevance"] == "source_relevance_judge"
    with pytest.raises(ValueError, match="already mapped"):
        register_suites({}, role_tasks={"source_relevance": "grading"})


def test_source_retrieval_dry_run_plans_every_paid_step_and_writes_nothing(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    receipts = _receipts(repository)
    llm = FakeSourceLLM()
    request = CompareRequest(suite="source_retrieval", output_dir=tmp_path / "out", max_cases=6, dry_run=True)
    report = run_compare(loaded(paths), request=request, caps=CAPS,
                         clients={"source_question_writer": llm, "source_relevance": llm, "source_rewrite": llm},
                         embedding_clients={QWEN: HashingEmbedder()})
    assert report["status"] == "dry_run"
    plan = report["plan"]
    assert plan["questions"] == 6 and plan["dense_index"]["status"] == "incomplete"
    assert set(plan["roles"]) == {"source_question_writer", "source_rewrite", "source_relevance"}
    assert report["estimate"]["llm_calls"] > 0 and report["estimate"]["embedding_calls"] >= 1
    assert llm.calls == [] and _receipts(repository) == receipts and not (tmp_path / "out").exists()


def test_source_retrieval_report_compares_against_todays_substring_search(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    backfill = backfill_embeddings(loaded(paths), caps=CAPS, recipes=("source_block",),
                                   registry=SOURCE_RETRIEVAL_RECIPES, client_factory=HashingEmbedder)
    assert backfill["status"] == "complete"
    llm = FakeSourceLLM()
    request = CompareRequest(suite="source_retrieval", output_dir=tmp_path / "out", max_cases=8)
    report = run_compare(loaded(paths), request=request, caps=CAPS, price_per_million=1.0,
                         clients={"source_question_writer": llm, "source_relevance": llm, "source_rewrite": llm},
                         embedding_clients={QWEN: HashingEmbedder()})
    assert report["status"] == "complete", report.get("reason")
    results = report["results"]
    assert results["systems"] == ["substring", "keyword", "meaning", "hybrid", "hybrid_rewrite"]
    assert results["scored_questions"] == results["questions"] == 8
    assert set(results["summary"]["differences"]) >= {"hybrid - substring", "keyword - substring"}
    assert results["label_agreement"]["pairs"] > 0
    assert results["seed_hit@10"]["hybrid"] >= results["seed_hit@10"]["substring"]
    assert _ledger(repository) == 2 * results["label_agreement"]["pairs"]
    markdown = (tmp_path / "out" / report["report_files"][1]).read_text(encoding="utf-8")
    assert "| hybrid |" in markdown and "Label agreement" in markdown
    # A rerun pays for nothing: questions, rewrites and labels come from checkpoints.
    calls = len(llm.calls)
    again = run_compare(loaded(paths), request=request, caps=CAPS, price_per_million=1.0,
                        clients={"source_question_writer": llm, "source_relevance": llm, "source_rewrite": llm},
                        embedding_clients={QWEN: HashingEmbedder()})
    assert again["status"] == "complete" and len(llm.calls) == calls
    assert again["results"]["summary"] == results["summary"]


def test_without_a_backfill_the_dense_system_is_reported_unavailable(tmp_path):
    paths, _repository = build_retrieval_vault(tmp_path / "vault")
    llm = FakeSourceLLM()
    request = CompareRequest(suite="source_retrieval", output_dir=tmp_path / "out", max_cases=4,
                             views=("substring", "keyword", "meaning", "hybrid"))
    report = run_compare(loaded(paths), request=request, caps=CAPS,
                         clients={"source_question_writer": llm, "source_relevance": llm},
                         embedding_clients={QWEN: HashingEmbedder()})
    results = report["results"]
    assert results["systems"] == ["substring", "keyword", "hybrid"]
    assert "--record-kind source_block" in results["unavailable_systems"]["meaning"]


def test_missing_labels_are_asked_again_then_left_as_abstentions(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    llm = FakeSourceLLM(drop_label_refs=1)  # every label answer skips its first candidate
    request = CompareRequest(suite="source_retrieval", output_dir=tmp_path / "out", max_cases=3,
                             views=("substring", "keyword"))
    report = run_compare(loaded(paths), request=request, caps=CAPS,
                         clients={"source_question_writer": llm, "source_relevance": llm})
    results = report["results"]
    assert results["incomplete_questions"] + results["scored_questions"] == results["questions"]


def _pdf(pages: int) -> bytes:
    from pypdf import PdfWriter

    writer = PdfWriter()
    for index in range(pages):
        writer.add_blank_page(width=300 + 20 * index, height=400)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def _pdf_vault(tmp_path):
    pytest.importorskip("pypdfium2")
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    raw = _pdf(7)
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    store_original_bytes(paths.root, digest, raw)
    pages = {
        "p_eigen": ("Eigen chapter", [
            ("Eigenvalues are roots of the characteristic polynomial; long explanation of eigenvalue theory "
             "for square matrices and their determinants det(A - tI) = 0 in every case we study.", 0),
            ("Symmetric matrices have real eigenvalues and an orthonormal basis of eigenvectors, which is "
             "the spectral theorem for real symmetric matrices used throughout the chapter.", 1)]),
        "p_orth": ("Orthogonality chapter", [
            ("Orthogonal vectors have zero dot product; orthogonal nonzero vectors are linearly independent "
             "and projection onto a unit vector uses the dot product in every inner product space.", 2),
            ("Gram-Schmidt turns any basis into an orthonormal basis by subtracting projections one vector at "
             "a time, keeping the span of the first k vectors unchanged at each step.", 3)]),
    }
    pages = {unit: (header, [(text + " " + text, page) for text, page in rows])
             for unit, (header, rows) in pages.items()}  # every page well above the short-page floor
    seed_source(repository, source_id="src_pdf", revision_id="rev_pdf", extraction_id="ext_pdf",
                title="Scanned Notes", units=pages, asset_hash=digest, furniture=False)
    return paths, repository


def test_b4_compares_page_images_with_text_chunks_and_decides_conservatively(tmp_path):
    paths, repository = _pdf_vault(tmp_path)
    llm = FakeSourceLLM()
    image = FakeMultimodalEmbedder()
    request = CompareRequest(suite="b4", output_dir=tmp_path / "out", max_cases=4, max_items=20)
    clients = {"source_question_writer": llm, "source_relevance": llm}
    embedders = {QWEN: HashingEmbedder(), GEMINI: image}
    dry = run_compare(loaded(paths), request=CompareRequest(**{**request.__dict__, "dry_run": True}),
                      caps=CAPS, price_per_million=1.0, embedding_price_per_million=0.45,
                      clients=clients, embedding_clients=embedders)
    assert dry["status"] == "dry_run" and dry["plan"]["embedding"][GEMINI]["images"] == 4
    assert llm.calls == [] and image.images == 0
    report = run_compare(loaded(paths), request=request, caps=CAPS, price_per_million=1.0,
                         embedding_price_per_million=0.45, clients=clients, embedding_clients=embedders)
    assert report["status"] == "complete", report.get("reason")
    results = report["results"]
    assert results["pages"] == 4 and image.images == 4
    assert {f"text:{QWEN}", f"text:{GEMINI}", f"image:{GEMINI}", "keyword", "hybrid_text",
            "hybrid_image"} == set(results["systems"])
    assert results["decision"]["page_image_default"] is False  # four questions can never clear the bar
    # Review F5: text-seeded, text-labelled questions favour text by construction,
    # so the decision is provisional until an image-labelled pass agrees.
    assert results["decision"]["status"] == "provisional"
    assert "Marker" in results["decision"]["bias"] and "page image" in results["decision"]["close_condition"]
    assert "hybrid_image - hybrid_text" in results["summary"]["differences"]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        kinds = {row[0] for row in connection.execute(
            "SELECT right_kind FROM judgment_ledger WHERE task = 'source_relevance'")}
    assert kinds == {"pdf_page"}
    # Page-image vectors are cached in the output directory, never in the vault.
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        stored = connection.execute("SELECT COUNT(*) FROM embedding_vectors WHERE model_id = ?", (GEMINI,)).fetchone()[0]
    assert stored == 0
    images_before = image.images
    run_compare(loaded(paths), request=request, caps=CAPS, price_per_million=1.0,
                embedding_price_per_million=0.45, clients=clients, embedding_clients=embedders)
    assert image.images == images_before


def test_cli_compare_registers_the_t6_suites(tmp_path):
    paths, _repository = build_retrieval_vault(tmp_path / "vault")
    result = CliRunner().invoke(app, [
        "embeddings", "compare", "--vault", str(paths.root), "--suite", "source_retrieval", "--dry-run",
        "--json", "--output", str(tmp_path / "out"), "--max-cases", "5", "--view", "substring",
        "--view", "keyword",
    ])
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert report["status"] == "dry_run" and report["plan"]["questions"] == 5


def test_the_bar_needs_an_interval_above_zero_recall_not_worse_and_ten_questions():
    from learnloop.source_retrieval.bench import beats, score_question, summarize

    def question(left_gain: float, right_gain: float) -> dict:
        labels = {"a": ["answers", "answers"], "b": ["unrelated", "related"]}
        rankings = {"left": ["a", "b"] if left_gain else ["b", "a"], "right": ["a", "b"] if right_gain else ["b", "a"]}
        return score_question(rankings, labels)

    better = [question(1, 0) for _ in range(10)]
    summary = summarize(better, ["left", "right"], [("left", "right")])
    assert beats(summary["differences"]["left - right"])
    assert not beats(summarize(better[:9], ["left", "right"], [("left", "right")])["differences"]["left - right"])
    tied = [question(1, 1) for _ in range(12)]
    assert not beats(summarize(tied, ["left", "right"], [("left", "right")])["differences"]["left - right"])
    assert score_question({"left": ["a"]}, {"a": ["answers", None]}) is None
