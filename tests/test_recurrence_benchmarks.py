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
    B1_WRITER_ROLE,
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
from tests.recurrence_fakes import JudgeFake, StatementFake, record_verdict, shares_word
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
                           models=("qwen/qwen3-embedding-8b",), dims=(16,))
    writer = _Writer()
    embedder = FakeEmbeddingClient(dims=16)
    plan = run_bench(vault, request=BenchRequest(**{**request.__dict__, "dry_run": True}), caps=CAPS,
                     embedding_clients={"qwen/qwen3-embedding-8b": embedder}, writer_client=writer)
    assert plan["status"] == "dry_run" and plan["plan"]["roles"][B1_WRITER_ROLE]["calls"] == 4
    # The subscription writer counts its calls; its cost is estimated only.
    assert plan["estimate"]["billing"][B1_WRITER_ROLE] == "subscription"
    assert plan["estimate"]["subscription"]["calls"] == 4 and plan["estimate"]["subscription"]["cost_basis"] == "estimated_only"
    assert writer.calls == 0 and embedder.calls == 0
    report = run_bench(vault, request=request, caps=CAPS,
                       embedding_clients={"qwen/qwen3-embedding-8b": embedder}, writer_client=writer)
    assert report["status"] == "complete", report
    results = report["results"]
    assert set(results["bm25"]) == {"raw", "hypothesis"}
    assert results["embedding"]["qwen/qwen3-embedding-8b"]["raw"]["centred"]["n"] == 4
    assert "qwen/qwen3-embedding-8b" in results["hybrid"]
    assert writer.calls == 4
    with _repository.connection() as connection:
        purposes = {row[0] for row in connection.execute(
            "SELECT purpose FROM model_call_receipts WHERE owner_kind = 'recurrence_benchmark'"
        )}
    assert "embedding" in purposes, "benchmark calls are receipted"
    # Hypotheses and vectors are cached in the output directory: a rerun sends nothing.
    calls = embedder.calls
    run_bench(vault, request=request, caps=CAPS, embedding_clients={"qwen/qwen3-embedding-8b": embedder}, writer_client=writer)
    assert writer.calls == 4 and embedder.calls == calls
    assert (tmp_path / "out" / report["report_files"][1]).read_text(encoding="utf-8").startswith("# Recurrence benchmark b1")


def test_b1_fails_closed_on_an_unknown_embedding_price(tmp_path):
    _paths, vault, _repository = _bench_vault(tmp_path)
    _eedi(tmp_path / "eedi")
    request = BenchRequest(suite="b1", output_dir=tmp_path / "out", benchmark_dir=tmp_path / "eedi",
                           models=("google/gemini-embedding-2",), dims=(16,), views=("raw",), dry_run=True)
    report = run_bench(vault, request=request, caps=CAPS)
    assert report["status"] == "over_budget" and "price" in report["reason"]


def test_b3_replays_the_vaults_labelled_pairs(tmp_path):
    paths, _vault, repository = split_vault(tmp_path, version="mvp-0.12", seed=False,
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
    # The owner's verdicts (independent of the shortlist) are what B3 measures.
    _owner_labels(repository, ("same", "different"))
    request = BenchRequest(suite="b3", output_dir=tmp_path / "b3", models=("qwen/qwen3-embedding-8b",), target_recall=1.0)
    report = run_bench(vault, request=request, caps=CAPS, embedding_clients={"qwen/qwen3-embedding-8b": embedder})
    assert report["status"] == "complete", report
    model = report["results"]["models"]["qwen/qwen3-embedding-8b"]
    assert model["positives"] >= 1 and model["recall@10"] == 1.0
    assert model["recommended_top_k"] is not None
    # A handful of confirmed matches reports a cutoff but recommends none.
    assert model["recommendation_backed"] is False and model["config"][0].startswith("# ")
    # Review F7: by default B3 measures the serving width (embedding.dimensions),
    # the production recipe and prefix, and says so.
    assert report["results"]["dims"] == [vault.config.embedding.dimensions] == [16]
    assert model["serving_width"] is True
    assert model["blocking_cutoff"]["dims"] == 16 and model["blocking_cutoff"]["recipe"] == "hypothesis/statement@v1"
    assert model["blocking_cutoff"]["task_prefix"] == "retrieval-document"
    assert report["results"]["merge_replay"]["label_judge"] == "owner"
    assert report["results"]["merge_replay"]["exact_only"]["merged_label_pairs"] == 0
    # Owner labels from M1's link review are on diagnoser-linked pairs: P6 says so.
    assert report["results"]["merge_replay"]["label_nominations"] == {"m1_link": 2}


def _b3_history(tmp_path):
    paths, _vault, repository = split_vault(tmp_path, version="mvp-0.12", seed=False,
                                            config="[recurrence]\njudge_enabled = false")
    enable_embeddings(paths.root)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace("dimensions = 4096", "dimensions = 16"), encoding="utf-8")
    vault = load_vault(paths.root)
    client = StatementFake({
        "first": "Believes V and V transpose are the same matrix.",
        "second": "Thinks the last SVD factor never needs transposing.",
        "third": "Writes V where the transpose of V belongs.",
    })
    embedder = FakeEmbeddingClient(dims=16)
    for offset, (item_id, answer) in enumerate((
        ("pi_svd_compute_001", "A = U Sigma V first"),
        ("pi_svd_compute_002", "B = U Sigma V second"),
        ("pi_svd_compute_001", "A = U Sigma V third"),
    )):
        submit(vault, repository, client, item_id=item_id, answer=answer, when=at(10 + 2 * offset))
        drain_jobs(vault, repository, client, embedding=embedder, clock=FrozenClock(at(11 + 2 * offset)))
    caps = SpendCaps(max_candidates=50, max_pairs=50, max_retries=10, max_calls=50, max_total_tokens=500_000, max_estimated_usd=1.0)
    run_backlog(vault, repository, caps=caps, judge_client=JudgeFake(shares_word("transpos")), embedding_client=embedder)
    return paths, vault, repository, embedder


def _owner_labels(repository, verdicts=("same",)):
    """Owner verdicts (independent of the shortlist) on consecutive answers:
    the second vs the first, then the third vs the first, ..."""

    with repository.connection() as connection:
        attempts = [str(row[0]) for row in connection.execute(
            "SELECT attempt_id FROM causal_hypotheses GROUP BY attempt_id ORDER BY MIN(created_at)"
        )]
    for later, verdict in zip(attempts[1:], verdicts):
        record_verdict(repository, left=later, right=attempts[0], verdict=verdict, judge="owner", kind="attempt")


def test_b3_measures_the_shortlist_only_on_labels_the_shortlist_did_not_select(tmp_path):
    """Second review F3: the live and backlog judge only ever see pairs the
    shortlist nominated (top-k, above any cutoff), so their verdicts cannot
    measure the shortlist's recall, set its top_k or cutoff, or grade P6.
    They are reported apart; an owner verdict (independent) is measured."""

    _paths, vault, repository, embedder = _b3_history(tmp_path)
    request = BenchRequest(suite="b3", output_dir=tmp_path / "b3", models=("qwen/qwen3-embedding-8b",), target_recall=1.0)
    report = run_bench(vault, request=request, caps=CAPS, embedding_clients={"qwen/qwen3-embedding-8b": embedder})
    assert report["status"] == "complete", report
    assert report["plan"]["labels_by_nomination"].get("shortlist", 0) >= 1
    model = report["results"]["models"]["qwen/qwen3-embedding-8b"]
    assert model["positives"] == 0 and model["recommended_top_k"] is None
    assert model["blocking_cutoff"]["cutoff"] is None and model["blocking_cutoff"]["confirmed_matches"] == 0
    assert model["shortlist_nominated"]["positives"] >= 1, "reported apart, never used to calibrate"
    replay = report["results"]["merge_replay"]
    assert replay["label_judge"] is None and replay["labels"] == 0

    # An owner verdict on two answers is independent of the shortlist.
    with repository.connection() as connection:
        first, second = (str(row[0]) for row in connection.execute(
            "SELECT attempt_id FROM causal_hypotheses GROUP BY attempt_id ORDER BY MIN(created_at) LIMIT 2"
        ))
    record_verdict(repository, left=second, right=first, verdict="same", judge="owner", kind="attempt")
    report = run_bench(vault, request=request, caps=CAPS, embedding_clients={"qwen/qwen3-embedding-8b": embedder})
    model = report["results"]["models"]["qwen/qwen3-embedding-8b"]
    assert model["positives"] == 1 and model["recall@10"] == 1.0
    assert report["results"]["merge_replay"]["label_judge"] == "owner"


def test_b3_recommends_only_at_the_serving_width_with_its_provenance(tmp_path, monkeypatch):
    """Review F7: the recommendation is bound to model, width, recipe and
    prefix; the shortlist applies it to matching vectors and refuses others."""

    import tomllib

    from learnloop.config.schema import RecurrenceConfig
    from learnloop.diagnosis.recurrence.judging import blocking_cutoff as configured_cutoff

    monkeypatch.setattr("learnloop.diagnosis.recurrence.benchmarks.MIN_CONFIRMED_FOR_RECOMMENDATION", 1)
    _paths, vault, repository, embedder = _b3_history(tmp_path)
    _owner_labels(repository, ("same", "same"))
    request = BenchRequest(suite="b3", output_dir=tmp_path / "b3", models=("qwen/qwen3-embedding-8b",),
                           dims=(8, 16), target_recall=1.0)
    report = run_bench(vault, request=request, caps=CAPS, embedding_clients={"qwen/qwen3-embedding-8b": embedder})
    assert report["status"] == "complete", report
    models = report["results"]["models"]
    narrow, serving = models["qwen/qwen3-embedding-8b@8"], models["qwen/qwen3-embedding-8b@16"]
    assert narrow["serving_width"] is False and "rerun B3 at the serving width" in narrow["config"][0]
    lines = serving["config"]
    assert lines[0] == "[recurrence]" and any("blocking_cutoffs" in line for line in lines)
    config = RecurrenceConfig.model_validate(tomllib.loads("\n".join(lines))["recurrence"])
    entry = config.blocking_cutoffs["qwen/qwen3-embedding-8b"]
    assert (entry.dims, entry.recipe, entry.task_prefix) == (16, "hypothesis/statement@v1", "retrieval-document")
    vault.config.recurrence.blocking_cutoffs = config.blocking_cutoffs
    applied = configured_cutoff(vault, "qwen/qwen3-embedding-8b", dims=16)
    assert applied[1] == "benchmark" and applied[0] == entry.cutoff
    refused = configured_cutoff(vault, "qwen/qwen3-embedding-8b", dims=4096)
    assert refused[0] is None and refused[1] == "refused_incompatible"


def test_the_b1_dry_run_prices_a_metered_writer_with_its_tokens(tmp_path):
    """Review F10: the writer's billing comes from its route; a metered writer's
    input and output tokens are admitted with the embeddings, and an unknown
    price fails closed."""

    paths, _vault, _repository = _bench_vault(tmp_path)
    toml = paths.root / "learnloop.toml"
    text = toml.read_text(encoding="utf-8")
    head, marker, tail = text.partition("[ai.routing]\n")
    toml.write_text(head + marker + 'diagnosis = "deepseek_pro"\n' + tail, encoding="utf-8")
    vault = load_vault(paths.root)
    _eedi(tmp_path / "eedi")
    request = BenchRequest(suite="b1", output_dir=tmp_path / "out", benchmark_dir=tmp_path / "eedi",
                           models=("qwen/qwen3-embedding-8b",), dims=(16,), dry_run=True)
    unknown = run_bench(vault, request=request, caps=CAPS)
    assert unknown["status"] == "over_budget" and "price" in unknown["reason"].lower()
    priced = run_bench(vault, request=request, caps=CAPS, price_per_million=2.0)
    assert priced["status"] == "dry_run", priced
    estimate = priced["estimate"]
    writer_tokens = priced["plan"]["roles"][B1_WRITER_ROLE]["tokens"]
    assert estimate["billing"][B1_WRITER_ROLE] == "metered" and writer_tokens > 0
    assert estimate["metered"]["tokens"] == writer_tokens + estimate["embedding_tokens"]
    assert estimate["metered"]["estimated_usd"] > writer_tokens * 2.0 / 1_000_000 * 0.99
    tight = SpendCaps(max_candidates=200, max_pairs=0, max_retries=10, max_calls=200, max_total_tokens=writer_tokens,
                      max_estimated_usd=1.0)
    refused = run_bench(vault, request=request, caps=tight, price_per_million=2.0)
    assert refused["status"] == "over_budget", "the writer's tokens count against the token cap"


def test_suites_register_on_a_harness_registry():
    registry = {"b2": object()}
    roles = {"grading": "grading"}
    register_suites(registry, role_tasks=roles)
    assert isinstance(registry["b1"], B1Suite) and isinstance(registry["b3"], B3Suite)
    assert roles[B1_WRITER_ROLE] == "diagnosis" and roles["grading"] == "grading"
    assert set(SUITES) == {"b1", "b3"}


# -- Phase 5a's harness contract (review F6) -------------------------------------------------
#
# Phase 5a's ``learnloop embeddings compare`` (ops/embedding_compare.py on
# slice-a/phase-5a) is not on this branch. ``_FiveACompareRequest`` copies its
# CompareRequest field for field, and ``_five_a_compare`` follows its
# run_compare: whole-plan billing looks every planned role up in the role
# registry (KeyError when unregistered), the context exposes only ``role``,
# ``caller.call`` and ``vectors``, and nothing has a ``k``. Once 5a merges, the
# real harness test below runs instead of skipping.


from dataclasses import dataclass  # noqa: E402
from pathlib import Path  # noqa: E402

#: slice-a/phase-5a ops/pf_calls.ROLE_TASKS (no diagnosis role of its own).
_FIVE_A_ROLE_TASKS = {
    "skeleton": "pf_generator", "program": "pf_generator", "single_shot": "pf_generator",
    "valid_alternative": "pf_generator", "source": "pf_generator", "closed_book": "pf_closed_book",
    "span_support": "pf_reference_verifier", "proposer": "pf_proposers", "panel": "pf_solver_panel",
    "equivalence": "pf_reference_verifier", "structure": "pf_isomorph_judge", "freshness": "pf_isomorph_judge",
    "selection": "pf_selection_judge", "pairwise": "pf_selection_judge", "grading": "grading",
}


@dataclass(frozen=True)
class _FiveACompareRequest:
    suite: str
    output_dir: Path
    benchmark_dir: Path | None = None
    models: tuple[str, ...] = ()
    dims: tuple[int, ...] = ()
    views: tuple[str, ...] = ()
    family_ids: tuple[str, ...] = ()
    target_recall: float = 0.95
    max_cases: int | None = None
    alternatives: int = 2
    max_items: int = 20
    tier: str | None = None
    dry_run: bool = False


@dataclass
class _RoleClient:
    role: str
    client: object
    model: str
    subscription: bool = True


@dataclass(frozen=True)
class _CallResult:
    result: object
    model: str


class _Caller:
    def __init__(self):
        self.calls_by_role: dict[str, int] = {}

    def call(self, entry, *, prompt, prompt_version, result_model, output_tokens, candidates=0, pairs=0):
        from learnloop.ai.transport import execute_structured_operation

        self.calls_by_role[entry.role] = self.calls_by_role.get(entry.role, 0) + 1
        result = execute_structured_operation(entry.client, purpose=f"pf_{entry.role}", prompt=prompt,
                                              result_model=result_model, isolated=True)
        return _CallResult(result_model.model_validate(result), entry.model)


class _FiveAContext:
    def __init__(self, vault, roles, clients, embedding_clients):
        self.vault, self.roles, self.clients, self.embedding_clients = vault, roles, clients, embedding_clients
        self.caller = _Caller()

    def role(self, name):
        task = self.roles[name]  # 5a: ROLE_TASKS[role] (KeyError when unregistered)
        assert task
        client = self.clients[name]
        return [_RoleClient(name, client, getattr(client, "model", "fake"))]

    def vectors(self, model, texts, *, dims, task_prefix="similarity"):
        import numpy as np

        vectors = self.embedding_clients[model].embed(list(texts), task_prefix)
        if any(len(vector) < dims for vector in vectors):
            raise ValueError("narrower than requested")
        out = {}
        for text, vector in zip(texts, vectors):
            array = np.asarray(vector, dtype=np.float32)
            out[text] = array / (np.linalg.norm(array) or 1.0)
        return out


def _five_a_compare(vault, request, *, suites, roles, clients, embedding_clients):
    suite = suites[request.suite]
    data = suite.load(vault, request)
    plan = suite.plan(vault, data, request)
    billing = {role: roles[role] for role in plan.get("roles", {})}  # 5a: planned_role_clients(vault, role)
    assert all(isinstance(entry, dict) and "calls" in entry and "tokens" in entry
               for entry in plan.get("embedding", {}).values())
    ctx = _FiveAContext(vault, roles, clients, embedding_clients)
    return {"plan": plan, "billing": billing, "results": suite.run(data, request, ctx), "calls": ctx.caller.calls_by_role}


def test_b1_and_b3_run_through_phase_5as_harness_contract(tmp_path):
    _paths, vault, repository, embedder = _b3_history(tmp_path)
    _owner_labels(repository)
    _eedi(tmp_path / "eedi")
    suites, roles = {}, dict(_FIVE_A_ROLE_TASKS)
    # Registration of the suites alone leaves B1's writer role unresolvable.
    register_suites(suites)
    b1 = _FiveACompareRequest(suite="b1", output_dir=tmp_path / "out", benchmark_dir=tmp_path / "eedi",
                              models=("qwen/qwen3-embedding-8b",), dims=(8, 16))
    with pytest.raises(KeyError):
        _five_a_compare(vault, b1, suites=suites, roles=roles, clients={B1_WRITER_ROLE: _Writer()},
                        embedding_clients={"qwen/qwen3-embedding-8b": embedder})
    register_suites(suites, role_tasks=roles)
    writer = _Writer()
    run = _five_a_compare(vault, b1, suites=suites, roles=roles, clients={B1_WRITER_ROLE: writer},
                          embedding_clients={"qwen/qwen3-embedding-8b": embedder})
    assert run["billing"] == {B1_WRITER_ROLE: "diagnosis"} and run["calls"] == {B1_WRITER_ROLE: 4}
    assert set(run["results"]["embedding"]) == {"qwen/qwen3-embedding-8b@8", "qwen/qwen3-embedding-8b@16"}
    assert run["results"]["k"] == 25
    b3 = _FiveACompareRequest(suite="b3", output_dir=tmp_path / "out3", models=("qwen/qwen3-embedding-8b",),
                              target_recall=1.0)
    run3 = _five_a_compare(vault, b3, suites=suites, roles=roles, clients={},
                           embedding_clients={"qwen/qwen3-embedding-8b": embedder})
    assert run3["results"]["dims"] == [16] and run3["results"]["models"]["qwen/qwen3-embedding-8b"]["positives"] >= 1


def test_b1_and_b3_run_through_the_real_phase_5a_harness_once_merged(tmp_path):
    compare = pytest.importorskip("learnloop.ops.embedding_compare")
    pf_calls = pytest.importorskip("learnloop.ops.pf_calls")
    _paths, vault, repository, embedder = _b3_history(tmp_path)
    _owner_labels(repository)
    _eedi(tmp_path / "eedi")
    register_suites(compare.SUITES, role_tasks=pf_calls.ROLE_TASKS)
    caps = SpendCaps(max_candidates=200, max_pairs=10, max_retries=10, max_calls=200, max_total_tokens=2_000_000,
                     max_estimated_usd=1.0)
    for request in (
        compare.CompareRequest(suite="b1", output_dir=tmp_path / "o1", benchmark_dir=tmp_path / "eedi",
                               models=("qwen/qwen3-embedding-8b",), dims=(16,)),
        compare.CompareRequest(suite="b3", output_dir=tmp_path / "o3", models=("qwen/qwen3-embedding-8b",)),
    ):
        report = compare.run_compare(vault, request=request, caps=caps, clients={B1_WRITER_ROLE: _Writer()},
                                     embedding_clients={"qwen/qwen3-embedding-8b": embedder})
        assert report["status"] == "complete", report
