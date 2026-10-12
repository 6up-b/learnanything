"""The shared `learnloop embeddings compare` harness: B2 and the valid-alternative suite."""
from __future__ import annotations

import hashlib
import json
import math

import pytest
from typer.testing import CliRunner

from learnloop.ai.execution import report_call_usage
from learnloop.ai.spend import SpendCaps
from learnloop.attempts.blind_grading import BlindGradingProposal
from learnloop.cli import app
from learnloop.content.authoring.pf_sandbox import sandbox_available
from learnloop.ops.embedding_compare import (
    SUITES, CompareRequest, blocking_cutoff, binary_metrics, roc_auc, run_compare,
)
from learnloop.vault.loader import load_vault
from tests.pf_fakes import PFFake, prompt_context, seed_pf_vault

CAPS = SpendCaps(max_candidates=100, max_pairs=2000, max_calls=2000, max_total_tokens=10**9, max_estimated_usd=10**4)
needs_bwrap = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")


class FakeEmbedder:
    model_id = "fake/embed"
    dims = 64
    modalities = frozenset({"text"})
    max_input_tokens = 10_000

    def __init__(self):
        self.calls = []

    def embed(self, inputs, task_prefix):
        self.calls.append(list(inputs))
        report_call_usage({"input_tokens": sum(len(text) for text in inputs)})
        vectors = []
        for text in inputs:
            words = [word for word in text.casefold().split() if word.isalpha()]
            vector = [0.0] * self.dims
            for word in words:
                vector[int(hashlib.sha256(word.encode()).hexdigest(), 16) % self.dims] += 1.0
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            vectors.append([value / norm for value in vector])
        return vectors


def benchmark(tmp_path, *, licence="CC-BY-4.0"):
    directory = tmp_path / "b2"
    directory.mkdir(parents=True)
    (directory / "manifest.json").write_text(json.dumps({
        "name": "b2-test", "sources": [{"name": "synthetic", "version": "1", "licence": licence}]}))
    rows = []
    for index in range(6):
        rows.append({"id": f"p{index}", "label": "positive", "category": "gsm_symbolic", "domain": "arithmetic",
                     "left": {"stem": f"Ana has {index + 2} apples and buys {index + 3} more apples. How many apples?",
                              "answer": str(2 * index + 5)},
                     "right": {"stem": f"Ana has {index + 7} apples and buys {index + 1} more apples. How many apples?",
                               "answer": str(2 * index + 8)}})
        rows.append({"id": f"n{index}", "label": "negative", "category": "math_perturb_hard", "domain": "arithmetic",
                     "left": {"stem": f"A train travels {index + 40} km in {index + 2} hours. What is its speed?",
                              "answer": "x"},
                     "right": {"stem": f"Ana has {index + 2} apples and buys {index + 3} more apples. How many apples?",
                               "answer": str(2 * index + 5)}})
    (directory / "pairs.jsonl").write_text("\n".join(json.dumps(row) for row in rows))
    return directory


def fakes():
    judge = PFFake("fake-judge")
    return {"skeleton": judge, "freshness": judge}


def test_metric_helpers():
    assert roc_auc([0.9, 0.8, 0.1], [True, True, False]) == 1.0
    assert roc_auc([0.1], [True]) is None
    cutoff = blocking_cutoff([0.9, 0.7, 0.5, 0.6, 0.2], [True, True, True, False, False], 0.95)
    assert cutoff["cutoff"] == 0.5 and cutoff["recall"] == 1.0 and cutoff["judge_load"] == 0.5
    assert binary_metrics([True, False], [True, True])["recall"] == 0.5
    assert set(SUITES) == {"b2", "valid_alternative"}


def test_b2_reports_views_and_recall_oriented_cutoffs_and_caches_vectors(tmp_path):
    vault, repository, paths = seed_pf_vault(tmp_path / "vault")
    embedder = FakeEmbedder()
    request = CompareRequest(suite="b2", output_dir=tmp_path / "out", benchmark_dir=benchmark(tmp_path),
                             models=("fake/embed",), dims=(16, 64))
    report = run_compare(vault, request=request, caps=CAPS, price_per_million=1.0,
                         embedding_price_per_million=0.02, clients=fakes(),
                         embedding_clients={"fake/embed": embedder})
    assert report["status"] == "complete", report
    results = report["results"]
    assert results["positives"] == 6 and results["negatives"] == 6
    for view in ("stem", "skeleton"):
        for dims in (16, 64):
            assert results["views"][f"{view}|fake/embed|{dims}"]["auc"] is not None
    cutoffs = {(c["view"], c["dims"]) for c in results["blocking_cutoffs"]}
    assert cutoffs == {("stem", 16), ("stem", 64), ("skeleton", 16), ("skeleton", 64)}
    assert all(c["record_kind"] == "item" and c["model_id"] == "fake/embed" and c["recall"] >= 0.95
               for c in results["blocking_cutoffs"])
    assert "fingerprint" in results["views"] and "judge" in results["views"]
    assert results["views"]["judge"]["by_model"]
    for name in report["report_files"]:
        assert (tmp_path / "out" / name).exists()
    with repository.connection() as connection:
        verdicts = connection.execute(
            "SELECT COUNT(*) FROM judgment_ledger WHERE task='isomorph' AND left_kind='b2_case'").fetchone()[0]
    assert verdicts == 12
    calls = len(embedder.calls)
    again = run_compare(load_vault(paths.root), request=request, caps=CAPS, price_per_million=1.0,
                        embedding_price_per_million=0.02, clients=fakes(),
                        embedding_clients={"fake/embed": embedder})
    assert again["status"] == "complete" and len(embedder.calls) == calls  # cached vectors
    assert again["results"]["blocking_cutoffs"] == results["blocking_cutoffs"]


def test_b2_requires_licensed_manifest_and_known_prices(tmp_path):
    vault, _, _ = seed_pf_vault(tmp_path / "vault")
    with pytest.raises(ValueError, match="licence"):
        run_compare(vault, request=CompareRequest(suite="b2", output_dir=tmp_path / "out",
                                                  benchmark_dir=benchmark(tmp_path, licence="")), caps=CAPS)
    unknown = run_compare(vault, request=CompareRequest(
        suite="b2", output_dir=tmp_path / "out2", benchmark_dir=benchmark(tmp_path / "x"),
        models=("someone/unknown-embedder",), views=("stem",)), caps=CAPS, clients=fakes())
    assert unknown["status"] == "over_budget" and "embedding price" in unknown["reason"]


def test_b2_dry_run_sends_nothing_and_writes_nothing(tmp_path):
    vault, _, paths = seed_pf_vault(tmp_path / "vault")
    embedder = FakeEmbedder()
    judge = fakes()
    before = paths.sqlite_path.read_bytes()
    report = run_compare(vault, request=CompareRequest(
        suite="b2", output_dir=tmp_path / "out", benchmark_dir=benchmark(tmp_path), dry_run=True,
        models=("fake/embed",)), caps=CAPS, embedding_price_per_million=0.02, clients=judge,
        embedding_clients={"fake/embed": embedder})
    assert report["status"] == "dry_run"
    assert report["estimate"]["llm_calls"] > 0 and report["estimate"]["embedding_calls"] > 0
    assert not embedder.calls and not judge["skeleton"].calls
    assert not (tmp_path / "out").exists()
    assert paths.sqlite_path.read_bytes() == before


class Grader:
    provider_name = "fake"
    model = "fake-grader"

    def __init__(self):
        self.requests = []

    def supports(self, capability):
        return capability in {"structured_completion", "bounded_structured_completion", "isolated_turn"}

    def complete(self, request):
        self.requests.append(request)
        report_call_usage({"input_tokens": 10, "output_tokens": 10, "resolved_model": "fake-grader"})
        context = prompt_context(request.prompt)
        alternative = "Divide every term" in context["learner_answer_md"]
        return BlindGradingProposal(
            local_analysis_md="ok", attempt_id=context["attempt_id"], practice_item_id=context["practice_item_id"],
            rubric_score=1 if alternative else 2, grader_confidence=0.9,
        )


@needs_bwrap
def test_valid_alternative_suite_is_cas_checked_and_graded_learner_blind(tmp_path):
    vault, repository, paths = seed_pf_vault(tmp_path / "vault")
    grader = Grader()
    judge = PFFake("fake-judge")
    report = run_compare(vault, request=CompareRequest(suite="valid_alternative", output_dir=tmp_path / "out"),
                         caps=CAPS, price_per_million=1.0,
                         clients={"valid_alternative": judge, "equivalence": judge, "grading": grader})
    assert report["status"] == "complete", report
    results = report["results"]
    assert results["suite_traces"] == 2 and results["excluded_unverified_traces"] == 1
    by_model = results["by_grader_model"]
    assert by_model["fake-grader|canonical"]["not_full_credit"] == 0.0
    assert by_model["fake-grader|alternative"]["not_full_credit"] == 1.0
    suite = json.loads((tmp_path / "out" / "valid_alternative_suite.json").read_text())
    assert {case["kind"] for case in suite["cases"]} == {"canonical", "alternative"}
    # Learner-blind: isolated turns whose only answer text is a synthetic trace.
    traces = {case["trace"] for case in suite["cases"]}
    assert grader.requests and all(request.isolated for request in grader.requests)
    for request in grader.requests:
        context = prompt_context(request.prompt)
        assert context["learner_answer_md"] in traces
        assert context["attempt_id"].startswith("va_")
        assert "diagnostic_history" not in context
    with repository.connection() as connection:
        attempts = connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()[0]
        grades = connection.execute(
            "SELECT COUNT(*) FROM judgment_ledger WHERE task='valid_alternative_grade'").fetchone()[0]
    assert attempts == 0 and grades == 2


def test_cli_compare_dry_run(tmp_path):
    _, _, paths = seed_pf_vault(tmp_path / "vault")
    result = CliRunner().invoke(app, [
        "embeddings", "compare", "--vault", str(paths.root), "--suite", "b2", "--benchmark",
        str(benchmark(tmp_path)), "--dry-run", "--json", "--output", str(tmp_path / "out"),
        "--view", "fingerprint",
    ])
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert report["status"] == "dry_run" and report["suite"] == "b2"
    unknown = CliRunner().invoke(app, ["embeddings", "compare", "--vault", str(paths.root), "--suite", "nope"])
    assert unknown.exit_code == 1 and "Unknown suite" in unknown.stdout


@needs_bwrap
def test_valid_alternative_suite_rejects_a_degenerate_equivalence_check(tmp_path):
    """Codex review F10: an always-true check confirms nothing, so no trace is verified."""
    from tests.pf_fakes import ALWAYS_TRUE_CHECK

    vault, repository, _ = seed_pf_vault(tmp_path / "vault")
    grader = Grader()
    writer = PFFake("fake-judge")
    sycophant = PFFake("fake-verifier", always_agree=True, sympy_check=ALWAYS_TRUE_CHECK)
    report = run_compare(vault, request=CompareRequest(suite="valid_alternative", output_dir=tmp_path / "out"),
                         caps=CAPS, price_per_million=1.0,
                         clients={"valid_alternative": writer, "equivalence": sycophant, "grading": grader})
    assert report["status"] == "complete", report
    results = report["results"]
    # The wrong alternative ("999") must not enter the regression suite.
    assert results["suite_traces"] == 0 and results["excluded_unverified_traces"] == 3
    assert results["degenerate_checks"] == 1
    assert not grader.requests
    suite = json.loads((tmp_path / "out" / "valid_alternative_suite.json").read_text())
    assert suite["cases"] == []
    with repository.connection() as connection:
        verdicts = {row[0] for row in connection.execute(
            "SELECT verdict FROM judgment_ledger WHERE task='answer_equivalence' AND left_kind='va_trace'")}
    assert verdicts == {"degenerate_check"}
