"""Slice 2 T1 §3.3: B1 (Eedi 2024) and B3 (vault replay) on the harness contract."""

from __future__ import annotations

import csv
import json

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.clock import FrozenClock
from learnloop.diagnosis.recurrence.backlog import run_backlog
from learnloop.diagnosis.recurrence.benchmarks import (
    BM25,
    B1Suite,
    B3Suite,
    BenchRequest,
    MisconceptionHypothesis,
    SUITES,
    blocking_cutoff,
    load_eedi,
    rank_metrics,
    register_suites,
    roc_auc,
    run_bench,
)
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import FakeEmbeddingClient
from tests.recurrence_fakes import JudgeFake, StatementFake, shares_word
from tests.split_live_helpers import at, drain_jobs, enable_embeddings, split_vault, submit

CAPS = SpendCaps(max_candidates=200, max_pairs=0, max_retries=10, max_calls=200, max_total_tokens=2_000_000, max_estimated_usd=1.0)


def _eedi(directory, *, manifest=True):
    directory.mkdir(parents=True, exist_ok=True)
    if manifest:
        (directory / "manifest.json").write_text(json.dumps({
            "sources": [{"name": "Eedi Mining Misconceptions in Mathematics", "version": "2024", "licence": "competition rules"}]
        }), encoding="utf-8")
    with (directory / "misconception_mapping.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["MisconceptionId", "MisconceptionName"])
        writer.writerow([0, "Adds the numerators and adds the denominators when adding fractions"])
        writer.writerow([1, "Uses the diameter instead of the radius in the area of a circle"])
        writer.writerow([2, "Believes multiplying two negatives gives a negative"])
    with (directory / "train.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "QuestionId", "ConstructId", "ConstructName", "SubjectId", "SubjectName", "CorrectAnswer", "QuestionText",
            "AnswerAText", "AnswerBText", "AnswerCText", "AnswerDText",
            "MisconceptionAId", "MisconceptionBId", "MisconceptionCId", "MisconceptionDId",
        ])
        writer.writerow([1, 10, "Add fractions", 100, "Fractions", "A", "1/2 + 1/3 = ?", "5/6", "2/5", "1/5", "2/6", "", "0.0", "", ""])
        writer.writerow([2, 11, "Area of a circle", 101, "Circles", "B", "Area with diameter 6?", "36π", "9π", "6π", "12π", "1", "", "", ""])
        writer.writerow([3, 12, "Negative numbers", 102, "Integers", "C", "-2 × -3 = ?", "-6", "-5", "6", "5", "2", "", "", "2"])


def test_the_eedi_loader_reads_the_kaggle_files_and_needs_a_manifest(tmp_path):
    _eedi(tmp_path / "eedi")
    manifest, misconceptions, cases = load_eedi(tmp_path / "eedi")
    assert manifest["sources"][0]["version"] == "2024"
    assert len(misconceptions) == 3
    assert sorted(case["gold"] for case in cases) == ["0", "1", "2", "2"]
    assert {case["id"] for case in cases} == {"1B", "2A", "3A", "3D"}
    _eedi(tmp_path / "bare", manifest=False)
    with pytest.raises(ValueError, match="manifest"):
        load_eedi(tmp_path / "bare")
    with pytest.raises(ValueError, match="Kaggle"):
        (tmp_path / "eedi" / "train.csv").unlink()
        load_eedi(tmp_path / "eedi")


def test_metrics():
    assert rank_metrics([1, 2, None, 30], 25) == {"n": 4, "recall@25": 0.5, "map@25": 0.375}
    assert roc_auc([0.9, 0.8, 0.1], [True, True, False]) == 1.0
    cutoff = blocking_cutoff([0.9, 0.5, 0.4, 0.2], [True, True, False, False], 1.0)
    assert cutoff["cutoff"] == 0.5 and cutoff["recall"] == 1.0 and cutoff["negatives_above"] == 0
    scores = BM25(["adds the numerators", "uses the diameter"]).scores("numerators of fractions")
    assert scores[0] > scores[1] == 0.0


class _Writer:
    provider_type = "codex_sdk"
    provider_name = "fake"
    model = "fake-writer"

    def __init__(self):
        self.calls = 0

    def supports(self, capability):
        return True

    def complete(self, request):
        self.calls += 1
        return MisconceptionHypothesis(misconception="adds the numerators and the denominators")


def _bench_vault(tmp_path):
    paths, _vault, repository = split_vault(tmp_path, version="mvp-0.10", seed=False)
    enable_embeddings(paths.root)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace("dimensions = 4096", "dimensions = 16"), encoding="utf-8")
    return paths, load_vault(paths.root), repository


def test_b1_dry_run_then_run_with_fakes(tmp_path):
    _paths, vault, _repository = _bench_vault(tmp_path)
    _eedi(tmp_path / "eedi")
    request = BenchRequest(suite="b1", output_dir=tmp_path / "out", benchmark_dir=tmp_path / "eedi",
                           models=("qwen/qwen3-embedding-8b",), dims=16)
    writer = _Writer()
    embedder = FakeEmbeddingClient(dims=16)
    plan = run_bench(vault, request=BenchRequest(**{**request.__dict__, "dry_run": True}), caps=CAPS,
                     embedding_clients={"qwen/qwen3-embedding-8b": embedder}, writer_client=writer)
    assert plan["status"] == "dry_run" and plan["plan"]["roles"]["diagnosis"]["calls"] == 4
    assert writer.calls == 0 and embedder.calls == 0
    report = run_bench(vault, request=request, caps=CAPS,
                       embedding_clients={"qwen/qwen3-embedding-8b": embedder}, writer_client=writer)
    assert report["status"] == "complete", report
    results = report["results"]
    assert set(results["bm25"]) == {"raw", "hypothesis"}
    assert results["embedding"]["qwen/qwen3-embedding-8b"]["raw"]["centred"]["n"] == 4
    assert "qwen/qwen3-embedding-8b" in results["hybrid"]
    assert writer.calls == 4
    # Hypotheses and vectors are cached in the output directory: a rerun sends nothing.
    calls = embedder.calls
    run_bench(vault, request=request, caps=CAPS, embedding_clients={"qwen/qwen3-embedding-8b": embedder}, writer_client=writer)
    assert writer.calls == 4 and embedder.calls == calls
    assert (tmp_path / "out" / report["report_files"][1]).read_text(encoding="utf-8").startswith("# Recurrence benchmark b1")


def test_b1_fails_closed_on_an_unknown_embedding_price(tmp_path):
    _paths, vault, _repository = _bench_vault(tmp_path)
    _eedi(tmp_path / "eedi")
    request = BenchRequest(suite="b1", output_dir=tmp_path / "out", benchmark_dir=tmp_path / "eedi",
                           models=("google/gemini-embedding-2",), dims=16, views=("raw",), dry_run=True)
    report = run_bench(vault, request=request, caps=CAPS)
    assert report["status"] == "over_budget" and "price" in report["reason"]


def test_b3_replays_the_vaults_labelled_pairs(tmp_path):
    paths, _vault, repository = split_vault(tmp_path, version="mvp-0.11", seed=False,
                                            config="[recurrence]\njudge_enabled = false")
    enable_embeddings(paths.root)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace("dimensions = 4096", "dimensions = 16"), encoding="utf-8")
    vault = load_vault(paths.root)
    client = StatementFake({
        "first": "Believes V and V transpose are the same matrix.",
        "second": "Thinks the last SVD factor never needs transposing.",
        "third": "Forgets that singular values are non-negative.",
    })
    embedder = FakeEmbeddingClient(dims=16)
    for offset, (item_id, answer) in enumerate((
        ("pi_svd_compute_001", "A = U Sigma V first"),
        ("pi_svd_compute_002", "B = U Sigma V second"),
        ("pi_svd_compute_001", "A = U Sigma V third"),
    )):
        submit(vault, repository, client, item_id=item_id, answer=answer, when=at(10 + 2 * offset))
        drain_jobs(vault, repository, client, embedding=embedder, clock=FrozenClock(at(11 + 2 * offset)))
    backlog_caps = SpendCaps(max_candidates=50, max_pairs=50, max_retries=10, max_calls=50, max_total_tokens=500_000, max_estimated_usd=1.0)
    run_backlog(vault, repository, caps=backlog_caps, judge_client=JudgeFake(shares_word("transpos")), embedding_client=embedder)
    request = BenchRequest(suite="b3", output_dir=tmp_path / "b3", models=("qwen/qwen3-embedding-8b",), dims=16, target_recall=1.0)
    report = run_bench(vault, request=request, caps=CAPS, embedding_clients={"qwen/qwen3-embedding-8b": embedder})
    assert report["status"] == "complete", report
    model = report["results"]["models"]["qwen/qwen3-embedding-8b"]
    assert model["positives"] >= 1 and model["recall@10"] == 1.0
    assert model["recommended_top_k"] is not None and model["config"][0] == "[recurrence]"
    assert report["results"]["merge_replay"]["label_judge"] == "llm"
    assert report["results"]["merge_replay"]["exact_only"]["merged_label_pairs"] == 0


def test_suites_register_on_a_harness_registry():
    registry = {"b2": object()}
    register_suites(registry)
    assert isinstance(registry["b1"], B1Suite) and isinstance(registry["b3"], B3Suite)
    assert set(SUITES) == {"b1", "b3"}
    for suite in SUITES.values():
        assert suite.name and suite.description
        assert all(callable(getattr(suite, name)) for name in ("load", "plan", "run"))
