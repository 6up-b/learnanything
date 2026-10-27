"""Local retrieval P2, the query student: pins (0.6B, owner 2026-10-26), the decision core, the
synthetic questions and their leakage guards, the teacher targets, the trainer on a tiny
random-initialised model, the schedule, evaluation and adoption by expected utility, the query
process and its client, the resolver's cold-start rule, the teacher replay and the kill switches.
Fakes and tiny synthetic models only: no process, no download, no plan call, no GPU."""
from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import time

import numpy as np
import pytest

from learnloop.db.connection import connect
from learnloop.local_embeddings import pins
from learnloop.local_embeddings import student_decision as SD
from learnloop.local_embeddings import student_pins as SP
from learnloop.local_embeddings import worker
from learnloop.local_embeddings.gpu_meter import GpuMeter
from learnloop.source_retrieval import local_index, query_student as Q, spaces, student_data as D
from learnloop.source_retrieval import student_encoder as E
from learnloop.source_retrieval.corpus import library_scope
from learnloop.source_retrieval.dense import clear_cache
from learnloop.source_retrieval.recipes import split_record_id
from learnloop.source_retrieval.search import search_spans
from tests.helpers import append_config_toml
from tests.local_embeddings_fakes import FakeLocalModel, InProcessLauncher, no_locks, run_fake_job
from tests.query_student_fakes import (
    BANK_QUESTION,
    FakeGenerator,
    InProcessTrainer,
    TeacherService,
    default_bank,
    find_gold,
    set_up_bases,
    stop_thread_servers,
    student_vault,
    thread_spawn,
    write_bank,
)
from tests.source_retrieval_fakes import HashingEmbedder, loaded


@pytest.fixture(autouse=True)
def _fresh(monkeypatch, tmp_path):
    clear_cache()
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    # A Unix socket path is at most 107 bytes: the runtime directory is a short temporary one,
    # under /tmp whatever the runner's TMPDIR (a long one pushed the socket past the limit).
    short = Path(tempfile.mkdtemp(prefix="llq", dir="/tmp" if Path("/tmp").is_dir() else None))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(short))
    E._ENCODERS.clear()
    yield short
    stop_thread_servers()  # before the runtime directory (its sockets) goes
    clear_cache()
    E._ENCODERS.clear()
    shutil.rmtree(short, ignore_errors=True)


# -- pins -------------------------------------------------------------------------------------------
def test_the_student_is_0_6b_with_pplx_primary_and_qwen3_5_dropped():
    assert SP.PRIMARY_BASE == "pplx-embed-v1-0.6b" and SP.SCREEN_BASES == ("pplx-embed-v1-0.6b", "qwen3-embedding-0.6b")
    assert SP.STUDENT_BASES["pplx-embed-v1-0.6b"]["repo"] == "perplexity-ai/pplx-embed-v1-0.6b"
    assert SP.STUDENT_BASES["qwen3-embedding-0.6b"]["repo"] == "Qwen/Qwen3-Embedding-0.6B"
    assert all(base["parameters"] < 700_000_000 for base in SP.STUDENT_BASES.values())
    assert not any("3.5" in base["repo"] for base in SP.STUDENT_BASES.values())
    assert "Qwen/Qwen3.5-0.8B-Base" in SP.DROPPED_BASES
    for base in SP.STUDENT_BASES.values():
        assert len(base["revision"]) == 40 and set(base["remote_code"]) <= set(base["files"])
        assert all(len(digest) == 64 for _size, digest in base["files"].values())
        assert not any("onnx" in pattern for pattern in base["allow_patterns"])
    assert SP.STUDENT_BASES["pplx-embed-v1-0.6b"]["pooling"] == "mean"
    assert SP.STUDENT_BASES["qwen3-embedding-0.6b"]["pooling"] == "last_token"


def test_an_unpinned_python_file_or_a_wrong_digest_refuses_the_base(tmp_path):
    from learnloop.local_embeddings.student_trainer import base_problems

    base = {"files": {"config.json": (2, __import__("hashlib").sha256(b"{}").hexdigest())},
            "remote_code": (), "inert_python": ()}
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    assert base_problems(tmp_path, base) == []
    (tmp_path / "evil.py").write_text("import os", encoding="utf-8")
    assert "unreviewed Python files" in base_problems(tmp_path, base)[0]
    (tmp_path / "evil.py").unlink()
    (tmp_path / "config.json").write_text("[]", encoding="utf-8")
    assert "SHA-256 differs" in base_problems(tmp_path, base)[0]


# -- the decision core ----------------------------------------------------------------------------------
def test_the_cold_start_rule_has_no_constant_of_its_own():
    fast = [0.5] * 20
    assert SD.should_wait(fast, 10.0, 1.0)[0] is True  # the only space, likely in time
    assert SD.should_wait(fast, 10.0, 0.0)[0] is False  # no weight: never waited for
    assert SD.should_wait([], 10.0, 1.0) == (False, 0.5)  # unmeasured: P = 1/2 is not > 1/2
    slow = [30.0] * 20
    assert SD.should_wait(slow, 10.0, 1.0)[0] is False
    # The threshold is 1/(1+w): a half share needs P > 2/3.
    nine_of_ten = [0.1] * 9 + [99.0]
    assert SD.should_wait(nine_of_ten, 1.0, 0.5)[0] is True
    assert SD.should_wait([0.1] * 6 + [99.0] * 4, 1.0, 0.5)[0] is False


def test_the_bank_posterior_pools_families_and_unknowns_widen_it():
    families = {f"q{i}": ("a" if i < 20 else "b") for i in range(40)}
    good = SD.ArmOutcomes("good", {q: (1.0 if int(q[1:]) % 10 else 0.0) for q in families}, families)
    bad = SD.ArmOutcomes("bad", {q: (1.0 if int(q[1:]) % 2 else 0.0) for q in families}, families)
    g, b = SD.bank_quality_draws(good, seed=1), SD.bank_quality_draws(bad, seed=2)
    assert 0.8 < g.mean() < 0.95 and 0.4 < b.mean() < 0.6
    known = SD.ArmOutcomes("k", {q: v for q, v in list(good.outcomes.items())[:20]} |
                           {q: v for q, v in list(good.outcomes.items())[20:]}, families)
    unknown = SD.ArmOutcomes("u", {q: (v if int(q[1:]) < 30 else None) for q, v in good.outcomes.items()}, families)
    assert SD.bank_quality_draws(unknown, seed=3).std() > SD.bank_quality_draws(known, seed=3).std()
    decision = SD.decide([SD.Action("good", g), SD.Action("bad", b)], lam=0.001, mu=0.5)
    assert decision["chosen"] == "good" and decision["p_best"]["good"] > 0.99
    soft = SD.ArmOutcomes("soft", {q: 0.5 for q in families}, families)
    assert abs(SD.bank_quality_draws(soft, seed=4).mean() - 0.5) < 0.05


def test_lateness_and_money_enter_the_utility_and_the_rates_learn_from_owner_choices():
    q = np.full(SD.DRAWS, 0.8)
    late = SD.Action("slow", q + 0.01, late=SD.late_draws(90, 100))
    fast = SD.Action("fast", q, late=SD.late_draws(0, 100))
    assert SD.decide([late, fast], lam=0.0, mu=0.5)["chosen"] == "fast"
    costly = SD.Action("paid", q + 0.01, monthly_usd=100.0)
    assert SD.decide([costly, SD.Action("free", q)], lam=0.01, mu=0.0)["chosen"] == "free"
    lam = SD.seeded_lambda()
    before = lam.mean()
    for _ in range(5):
        lam.observe(dq=0.02, cost=50.0, s=0.01, accepted=True)  # the owner pays more for quality than seeded
    assert lam.mean() < before
    restored = SD.ExchangeRate.from_dict(lam.as_dict())
    assert restored.mean() == pytest.approx(lam.mean())
    assert set(SD.PRIOR_BASIS) >= {"lambda", "nu", "mu", "b_local", "late", "in_time", "learning_curve"}


def test_training_continues_only_while_the_expected_gain_beats_the_gpu_hours():
    rising = [(2_000, 0.60, 0.01), (10_000, 0.75, 0.01)]
    flat = [(2_000, 0.75, 0.01), (10_000, 0.751, 0.01)]
    yes = SD.continue_training(rising, 50_000, hours=0.5, hours_left=5.0, teacher_quality=0.83, nu=0.02)
    no = SD.continue_training(flat, 50_000, hours=0.5, hours_left=5.0, teacher_quality=0.83, nu=0.02)
    capped = SD.continue_training(rising, 50_000, hours=6.0, hours_left=5.0, teacher_quality=0.83, nu=0.0)
    assert yes["continue"] and not no["continue"] and not capped["continue"] and not capped["within_cap"]


# -- the worker's query shards ------------------------------------------------------------------------------
def test_the_worker_writes_teacher_targets_as_int8_shards(tmp_path):
    from learnloop.source_retrieval.local_index import build_job

    job, _targets = build_job([], manifest={"model_dir": str(tmp_path)}, plan_id="p2")
    job["query_shards"] = [{"name": "q0000", "path": str(tmp_path / "q0000.npy"),
                            "queries": [{"id": "a", "text": "what is a basis"}, {"id": "b", "text": "eigen " * 9000}]}]
    model = FakeLocalModel()
    output = run_fake_job(job, model)
    assert output["status"] == "complete", output
    shard = output["query_shards"]["q0000"]
    assert shard["rows"] == 2 and shard["errors"] == {"b": "over_limit"}
    array = np.load(tmp_path / "q0000.npy")
    assert array.dtype == np.int8 and array.shape == (2, pins.MODEL_DIMENSIONS)
    expected = model.encode_queries(["what is a basis"])[0][0]
    assert np.array_equal(array[0], expected.astype(np.int8)) and not array[1].any()
    assert not (tmp_path / "q0000.npy.partial").exists() and "vectors" not in json.dumps(output["query_shards"])


# -- synthetic questions -----------------------------------------------------------------------------------
def _space(paths):
    manifest, space, reason = Q.context(loaded(paths))
    assert manifest is not None, reason
    return space


def test_passages_hold_permitted_text_only_and_never_a_bank_support(tmp_path):
    paths, repository, root, _model, _report = student_vault(tmp_path)
    gold = find_gold(repository)
    found = D.passages(loaded(paths), repository, excluded={("ext_book", gold)})
    texts = " ".join(block["text"] for passage in found for block in passage["blocks"])
    assert "Exam question" not in texts and "Real symmetric matrices" not in texts
    assert {passage["source_id"] for passage in found} == {"src_book", "src_prob", "src_calc"}
    assert all(len({tuple(p["section"])}) == 1 for p in found)
    held = D.held_out_family(found)
    assert held in {"src_book", "src_prob", "src_calc"}
    assert {D.split_of(p, held) for p in found if p["source_id"] == held} == {"heldout"}


def test_generation_refuses_without_the_bank_and_dry_runs_without_a_call(tmp_path):
    paths, repository, root, _model, _report = student_vault(tmp_path)
    vault = loaded(paths)
    space = _space(paths)
    assert D.generate(vault, repository, space_id=space, bank_path=None)["status"] == "refused"
    fake = FakeGenerator()
    plan = D.generate(vault, repository, space_id=space, bank_path=default_bank(tmp_path, repository), dry_run=True,
                      client=fake)
    assert plan["status"] == "dry_run" and plan["calls"] >= 1 and fake.prompts == []
    assert plan["route"]["billing"] == "subscription" and plan["spend_plan"]["marginal_usd"] == 0.0
    assert plan["bank_supports_excluded"] == 1


def test_generation_stores_questions_drops_bank_lookalikes_and_resumes(tmp_path):
    paths, repository, root, _model, _report = student_vault(tmp_path)
    vault = loaded(paths)
    space = _space(paths)
    bank = default_bank(tmp_path, repository)
    fake = FakeGenerator(leak=True)
    report = D.generate(vault, repository, space_id=space, bank_path=bank, client=fake)
    assert report["status"] == "complete", report
    assert report["ngram_dropped"] == report["passages_written"] >= 3
    rows = D.stored_queries(D.data_dir(root, space, vault))
    assert rows and all(BANK_QUESTION.lower() not in row["text"].lower() for row in rows)
    assert all("Real symmetric matrices" not in prompt for prompt in fake.prompts)
    assert all("Exam question" not in prompt for prompt in fake.prompts)
    deictic = [row for row in rows if row["shape"] == "deictic"]
    assert deictic and all(D.SELECTION_LABEL in row["text"] and row["selection"] for row in deictic)
    assert {row["split"] for row in rows} >= {"train", "heldout"}
    # Nested budgets: the first n are inside the first m.
    assert [row["id"] for row in D.nested(rows, 3)] == [row["id"] for row in D.nested(rows, 10)][:3]
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        kinds = {row[0] for row in connection.execute("SELECT owner_kind FROM model_call_receipts")}
    assert D.OWNER_KIND in kinds
    again = D.generate(vault, repository, space_id=space, bank_path=bank, client=fake)
    assert again["status"] == "complete" and again["calls"] == 0 and len(fake.prompts) == report["calls_done"]


def test_a_metered_generator_needs_a_price_and_the_plan_route_is_the_luna_default(tmp_path):
    paths, repository, root, _model, _report = student_vault(tmp_path)
    vault = loaded(paths)
    assert vault.config.ai.routing.retrieval_query_generator == "chatgpt_luna"
    out = D.generate(vault, repository, space_id=_space(paths), bank_path=default_bank(tmp_path, repository),
                     client=None)
    # The suite turns generator models off: nothing is reached, and the reason says so.
    assert out["status"] in {"unavailable", "skipped"}


# -- teacher targets ------------------------------------------------------------------------------------------
def _generated(tmp_path, *, leak=False, per=8):
    paths, repository, root, model, report = student_vault(tmp_path)
    vault = loaded(paths)
    space = _space(paths)
    bank = default_bank(tmp_path, repository)
    D.generate(vault, repository, space_id=space, bank_path=bank, client=FakeGenerator(leak=leak, per=per))
    return paths, repository, root, model, space, bank


def test_targets_are_one_metered_query_batch_with_the_canaries_and_the_cosine_guard(tmp_path):
    paths, repository, root, model, space, bank = _generated(tmp_path)
    vault = loaded(paths)
    rows = D.stored_queries(D.data_dir(root, space, vault))
    # A bank question the teacher puts at cosine >= 0.90 to a synthetic one drops it.
    twin = next(row for row in rows if row["shape"] != "deictic")
    write_bank(bank, json.loads(bank.read_text()) + [{"query_id": "bank_twin", "question": twin["text"],
                                                      "family": "src_prob", "evidence_sets": []}])
    meter = GpuMeter(tmp_path / "meter", cap_hours=SP.P2_GPU_HOURS_CAP)
    dry = Q.run_targets(vault, repository, bank_path=bank, dry_run=True, meter=meter)
    assert dry["status"] == "dry_run" and dry["owed"] == len(rows) and dry["bank_owed"] == 2
    launcher = InProcessLauncher(model)
    out = Q.run_targets(vault, repository, bank_path=bank, launcher=launcher, meter=meter, preflight=lambda: [],
                        locks=no_locks)
    assert out["status"] == "complete", out
    assert out["kept"]["queries"] == len(rows) and out["kept"]["bank"] == 2 and out["canaries"]["ok"]
    assert launcher.jobs[0]["documents"] == [] and launcher.jobs[0]["queries"] == []
    index = Q.targets_index(SP.space_home(root, space))
    assert twin["id"] in index["dropped"] and out["leakage_dropped_by_teacher_cos"] >= 1
    assert meter.report()["cap_hours"] == SP.P2_GPU_HOURS_CAP and meter.report()["processes"] == 1
    again = Q.run_targets(vault, repository, bank_path=bank, launcher=launcher, meter=meter, preflight=lambda: [],
                          locks=no_locks)
    assert again["status"] == "complete" and len(launcher.jobs) == 1
    vectors = Q.teacher_vectors(SP.space_home(root, space), [rows[1]["id"]])
    expected = model.encode_queries([rows[1]["text"]])[0][0]
    assert np.allclose(vectors[rows[1]["id"]], expected / np.linalg.norm(expected), atol=1e-6)


def test_targets_refuse_a_drifted_teacher_and_wait_for_a_busy_gpu(tmp_path):
    paths, repository, root, _model, space, bank = _generated(tmp_path)
    vault = loaded(paths)
    busy = Q.run_targets(vault, repository, bank_path=bank, launcher=InProcessLauncher(FakeLocalModel()),
                         preflight=lambda: ["free VRAM 3.0 GiB is below 22.0 GiB"], locks=no_locks)
    assert busy["status"] == "waiting_for_gpu"
    drifted = Q.run_targets(vault, repository, bank_path=bank, launcher=InProcessLauncher(FakeLocalModel(salt="x")),
                            preflight=lambda: [], locks=no_locks)
    assert drifted["status"] == "epoch_drift" and not Q.targets_index(SP.space_home(root, space))["queries"]


# -- the trainer (tiny random-initialised model, CPU) ---------------------------------------------------------
@pytest.fixture
def torch_present():
    """The trainer needs torch (the app environment has it only with the pdf extra; the separate
    environment always has it). Without it these tests skip and say so."""

    return pytest.importorskip("torch", reason="torch is absent (install the pdf extra to run the trainer tests)")


def _targets(tmp_path, **kwargs):
    paths, repository, root, model, space, bank = _generated(tmp_path, **kwargs)
    vault = loaded(paths)
    out = Q.run_targets(vault, repository, bank_path=bank, launcher=InProcessLauncher(model), preflight=lambda: [],
                        locks=no_locks)
    assert out["status"] == "complete", out
    set_up_bases(root)
    return paths, repository, root, model, space, bank


@pytest.mark.parametrize("recipe", SP.RECIPES)
def test_every_recipe_trains_measures_and_writes_a_pinned_checkpoint(torch_present, tmp_path, recipe):
    from learnloop.local_embeddings import student_trainer

    paths, repository, root, _model, space, bank = _targets(tmp_path)
    data = tmp_path / "data"
    stats = Q.build_dataset(loaded(paths), repository, root=root, space=space, budget=50_000, bank_path=bank,
                            out_dir=data)
    assert stats["train"] > 0 and stats["temperature"] > 0 and stats["documents"] > 0
    gold = find_gold(repository)
    camp = Q.campaign(loaded(paths), repository, root=root, space=space, bank=D.load_bank(bank))
    ids = camp["candidates"]["ids"]
    assert stats["documents"] == len(ids) and not any(record.endswith("/" + gold) for record in ids)
    assert stats["dataset_fingerprint"] == camp["fingerprint"]
    job = Q.trainer_job({"base": SP.PRIMARY_BASE, "recipe": recipe, "budget": 50_000, "seed": 0}, space=space,
                        base_dir=tmp_path, data_dir=data, out_dir=tmp_path / "out", temperature=stats["temperature"],
                        plan_id="t", dataset_fingerprint=camp["fingerprint"],
                        training_families=stats["training_families"])
    job["epochs"] = 1
    output = student_trainer.run_training(job, model_factory=__import__("tests.query_student_fakes",
                                                                         fromlist=["x"]).tiny_factory,
                                          device="cpu", base_check=lambda _job: [])
    assert output["status"] == "complete", output
    assert set(output["history"][0]["loss"]) >= ({"align"} | ({"kd"} if "kd" in recipe else set())
                                                 | ({"multi_positive"} if recipe.endswith("mp") else set()))
    assert output["latency"]["device"]["probes"] >= 1 and 0.0 <= output["dev"]["agreement_mean"] <= 1.0
    manifest = json.loads((Path(output["checkpoint_dir"]) / "student.json").read_text())
    assert manifest["frozen_base"] is (recipe == "projection_only") and "cpu" in manifest["canaries"]
    assert manifest["dataset_fingerprint"] == camp["fingerprint"]
    assert manifest["training_families"] == Q.run_training_families(camp, 50_000)  # F19: pinned with the checkpoint
    assert manifest["training_families_provenance"] == Q.TRAINING_FAMILIES_PROVENANCE
    sha = Q.install_checkpoint(output, root=root, space=space)
    assert (E.checkpoint_dir(root, space, sha) / "student.safetensors").is_file()
    assert sha == student_trainer.checkpoint_digest(manifest)


def test_the_trainer_refuses_a_base_that_fails_its_pins(torch_present, tmp_path):
    from learnloop.local_embeddings import student_trainer

    output = student_trainer.run_training({"seed": 0, "base": SP.STUDENT_BASES[SP.PRIMARY_BASE],
                                           "base_dir": str(tmp_path / "missing")}, device="cpu")
    assert output["status"] == "refused" and "missing" in output["reason"]


# -- the schedule, evaluation and adoption --------------------------------------------------------------------
def _bank_for(paths, repository, model, space, *, good: bool, tmp_path):
    """A bank whose evidence is the teacher's own top block (good) or its worst one (bad)."""

    ids, matrix = Q.documents(loaded(paths), repository, space)
    rows = []
    for index, question in enumerate(["How do eigenvectors relate to eigenvalues?", "What is a determinant?",
                                      "When are two vectors orthogonal?", "What does Bayes' rule do?"]):
        vector = model.encode_queries([question])[0][0]
        order = np.argsort(-(matrix @ (vector / np.linalg.norm(vector))))
        target = ids[order[0] if good else order[-1]]
        extraction, span = split_record_id(target)
        rows.append({"query_id": f"bank_{index}", "question": question, "family": "src_book",
                     "evidence_sets": [{"set_id": "e", "required": [[extraction, span, 0, 1]]}]})
    return write_bank(tmp_path / ("good.json" if good else "bad.json"), rows)


def test_the_schedule_screens_both_bases_then_recipes_then_seeds_by_expected_utility(torch_present, tmp_path):
    paths, repository, root, model, space, bank = _targets(tmp_path)
    vault = loaded(paths)
    trainer = InProcessTrainer()
    meter = GpuMeter(tmp_path / "p2meter", cap_hours=SP.P2_GPU_HOURS_CAP)
    plan = Q.run_next(vault, repository, bank_path=bank, dry_run=True, meter=meter)
    assert plan["status"] == "dry_run" and plan["step"]["stage"] == "screen"
    assert plan["step"]["spec"]["recipe"] == "projection_only" and plan["step"]["spec"]["base"] == SP.PRIMARY_BASE
    stages = []
    for _ in range(12):
        out = Q.run_next(vault, repository, bank_path=bank, launcher=trainer, meter=meter, preflight=lambda: [],
                         locks=no_locks)
        if out["status"] != "trained":
            break
        stages.append((out["run"]["stage"], out["run"]["spec"]["base"], out["run"]["spec"]["recipe"],
                       out["run"]["spec"]["seed"]))
    assert out["status"] == "evaluate", out
    assert stages[:3] == [("screen", SP.PRIMARY_BASE, "projection_only", 0), ("screen", SP.PRIMARY_BASE, "align", 0),
                          ("screen", "qwen3-embedding-0.6b", "align", 0)]
    assert [stage for stage, *_ in stages[3:5]] == ["recipes", "recipes"]
    assert [seed for stage, _b, _r, seed in stages if stage == "seeds"] == [1, 2]
    assert out["step"]["checkpoint_sha256"] and len(out["step"]["seed_agreements"]) == SP.FINAL_SEEDS
    ledger = Q.read_ledger(SP.space_home(root, space))
    assert all(run["status"] == "complete" and run["checkpoint_sha256"] for run in ledger["runs"].values())
    # The data files (book text, teacher vectors) do not outlive their run.
    assert not any((SP.space_home(root, space) / "runs").glob("*/data"))


def test_a_failed_run_blocks_the_schedule_with_its_reason(tmp_path):
    paths, repository, root, _model, _space_id, bank = _targets(tmp_path)
    vault = loaded(paths)
    failed = Q.run_next(vault, repository, bank_path=bank, launcher=InProcessTrainer(fail=True), preflight=lambda: [],
                        locks=no_locks)
    assert failed["status"] == "run_failed"
    blocked = Q.run_next(vault, repository, bank_path=bank, launcher=InProcessTrainer(), preflight=lambda: [],
                         locks=no_locks)
    assert blocked["status"] == "blocked" and "fake failure" in blocked["step"]["reason"]


def _trained(tmp_path):
    """Generate (default bank), then targets, the whole schedule and evaluation against ONE bank:
    the teacher's own top blocks as evidence, a twin of a training question (dropped by the
    teacher-cosine guard, so the schedule runs with leakage drops: Codex review F7) and a
    question about another vault's book (out of scope for every arm, F4)."""

    paths, repository, root, model, space, _default = _generated(tmp_path)
    vault = loaded(paths)
    good = _bank_for(paths, repository, model, space, good=True, tmp_path=tmp_path)
    rows = D.stored_queries(D.data_dir(root, space, vault))
    twin = next(row for row in rows if row["split"] == "train" and row["shape"] != "deictic")
    write_bank(good, json.loads(good.read_text()) + [
        {"query_id": "bank_twin", "question": twin["text"], "family": "fam_alias_1", "evidence_sets": []},
        {"query_id": "bank_elsewhere", "question": "What is a Markov chain?", "family": "fam_alias_2",
         "evidence_sets": [{"set_id": "e", "required": [["ext_other_vault", "s1", 0, 1]]}]}])
    _bank_targets(paths, repository, model, good)
    assert twin["id"] in Q.targets_index(SP.space_home(root, space))["dropped"]
    set_up_bases(root)
    trainer = InProcessTrainer()
    for _ in range(12):
        out = Q.run_next(vault, repository, bank_path=good, launcher=trainer, preflight=lambda: [], locks=no_locks)
        if out["status"] != "trained":
            break
    assert out["status"] == "evaluate", out
    return paths, repository, root, model, space, good, out


def _bank_targets(paths, repository, model, bank):
    out = Q.run_targets(loaded(paths), repository, bank_path=bank, launcher=InProcessLauncher(model),
                        preflight=lambda: [], locks=no_locks)
    assert out["status"] == "complete", out


class _TeacherEncoder:
    def __init__(self, model):
        self.model = model

    def encode(self, texts, *, deadline=None):
        return TeacherService(self.model).encode(texts)


def _judgments(paths):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return [(row[0], row[1], row[2]) for row in connection.execute(
            "SELECT judge, verdict, left_id FROM judgment_ledger WHERE task = ? ORDER BY created_at, rowid",
            (Q.JUDGMENT_TASK,))]


def test_the_scheduled_candidate_is_recommended_adopted_and_a_lost_reevaluation_recommends_withdrawal(
        torch_present, tmp_path):
    """Codex review F4, F5, F7, F13, F14, F15 and the re-review's F4/F5: every arm on the same
    in-scope questions (measured alternatives naming the comparison); the rule recommends, never
    changes the serving state; the owner's adopt is a judgment_ledger verdict and a lambda
    observation; re-evaluating the adopted checkpoint against better measured alternatives
    recommends its withdrawal, which the owner's reject applies."""

    paths, repository, root, model, space, bank, trained = _trained(tmp_path)
    vault = loaded(paths)
    sha = trained["step"]["checkpoint_sha256"]
    factory = lambda _sha: _TeacherEncoder(model)  # noqa: E731
    dry = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, dry_run=True)
    assert dry["status"] == "dry_run" and dry["candidate_basis"] == "schedule"  # F7: train's "evaluate" is evaluate's
    comparison = dry["comparison_fingerprint"]
    scoped = [q["query_id"] for q in D.load_bank(bank) if q["query_id"].startswith("bank_") and
              q["query_id"] not in ("bank_twin", "bank_elsewhere")]
    worse = {name: _arm(tmp_path / f"{name}-worse.json", comparison, {qid: 0.0 for qid in scoped})
             for name in ("qwen", "voyage")}
    result = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, arms=worse)
    assert result["status"] == "recommended", result
    assert result["recommendation"] == "adopt" and result["authority"]["automatic"] is False
    assert result["decision"]["chosen"] == "student" and set(result["decision"]["p_best"]) == {"student", "qwen",
                                                                                                "voyage"}
    assert result["authority"]["comparable_alternatives"] is True and result["prior_alternatives"] == {}
    assert result["strata"]["all"]["p_student_ge_teacher"] > 0.3
    assert result["training_families"]["basis"] == "checkpoint_manifest"  # F19: run_next pinned them
    assert E.read_adoption(root, space) is None  # the rule recommends; the owner adopts (F5)
    record = Q.read_ledger(SP.space_home(root, space))["decisions"][-1]
    assert record["scope"]["questions"] == 4 and record["scope"]["outside"] == {"no_evidence_set": 1,
                                                                                "another_corpus": 1}
    assert (SP.space_home(root, space) / "evaluation" / record["draws"]["file"]).is_file()
    assert _judgments(paths) == [("verifier", "recommend_adopt", sha)]
    adopted = Q.owner_choice(vault, repository, accept=True)
    assert adopted["status"] == "adopted" and E.read_adoption(root, space)["checkpoint_sha256"] == sha
    assert E.read_adoption(root, space)["judgment_id"] == adopted["judgment_id"]
    lam, _nu = Q.exchange_rates(SP.space_home(root, space), 0.8)
    assert len(lam.observations) == 1 and lam.observations[0]["accepted"] is True  # F14
    # (No query receipts here, so that choice cost nothing and says nothing about lambda; a costed one moves it.)
    Q.record_owner_choice(SP.space_home(root, space), rate="lambda", dq=0.05, cost=2.0, s=0.02, accepted=False,
                          what="declined a $2 option worth 5 points")
    moved, _nu = Q.exchange_rates(SP.space_home(root, space), 0.8)
    assert moved.mean() > SD.seeded_lambda().mean()  # declining it says a dollar costs more quality
    # Better measured alternatives on the same questions: withdrawal is RECOMMENDED (F13, re-review F5).
    arms = {name: _arm(tmp_path / f"{name}.json", comparison, {qid: 1.0 for qid in scoped})
            for name in ("qwen", "voyage")}
    again = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, arms=arms)
    assert again["status"] == "withdrawal_recommended" and again["recommendation"] == "keep_alternatives", again
    assert again["alternatives"]["qwen"].startswith("measured")
    assert E.read_adoption(root, space)["checkpoint_sha256"] == sha
    assert Q.owner_choice(vault, repository, accept=False)["withdrawn"] and E.read_adoption(root, space) is None
    assert [verdict for _judge, verdict, _left in _judgments(paths)] == [
        "recommend_adopt", "adopt", "recommend_keep_alternatives", "recommend_withdraw", "reject", "withdrawn"]
    # An alternative that does not cover the same questions is refused, never compared (F4).
    arms["qwen"] = _arm(tmp_path / "qwen-partial.json", comparison, {scoped[0]: 1.0})
    partial = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, arms=arms)
    assert partial["status"] == "refused" and "same questions" in partial["reason"]


def test_the_owner_revoke_is_a_judgment_ledger_verdict(tmp_path):
    """Codex review F15."""

    paths, repository, root, _model, _report = student_vault(tmp_path)
    space = _space(paths)
    sha = _adopt(root, space)
    out = Q.revoke(loaded(paths), repository)
    assert out["status"] == "revoked" and out["judgment_id"]
    assert _judgments(paths) == [("owner", "revoked", sha)] and E.read_adoption(root, space) is None


# -- the query process and its client ---------------------------------------------------------------------
def test_the_query_process_answers_over_its_unix_socket_and_exits_idle(_fresh):
    from learnloop.local_embeddings import student_server

    socket_path = _fresh / "s.sock"
    service = TeacherService()
    import threading

    reasons = []
    thread = threading.Thread(target=lambda: reasons.append(student_server.serve_forever(
        service, socket_path, idle_s=2.0, timeout_s=0.1)), daemon=True)
    thread.start()
    for _ in range(100):
        if socket_path.exists():
            break
        time.sleep(0.01)
    assert oct(socket_path.stat().st_mode & 0o777) == "0o600"
    reply = E.request(socket_path, {"op": "encode", "texts": ["what is a basis"]}, timeout_s=2.0)
    assert reply["ok"] and len(reply["vectors"][0]) == pins.MODEL_DIMENSIONS
    assert E.request(socket_path, {"op": "nope"}, timeout_s=2.0)["error"] == "unknown_op"
    thread.join(timeout=15)
    assert reasons == ["idle"] and not socket_path.exists()


def test_the_query_process_refuses_outside_its_4g_scope_and_under_the_host_floor():
    from learnloop.local_embeddings import student_server

    job = {"limits": {"memory_max_bytes": SP.SERVE_SCOPE_MEMORY_MAX_BYTES, "swap_max_bytes": 0,
                      "min_host_available_gib": SP.SERVE_MIN_HOST_AVAILABLE_GIB, "min_free_vram_gib": 4.0}}
    ok_scope = {"scope": True, "memory_max": 4 * worker.GIB, "swap_max": 0}
    assert student_server.start_problems(job, meminfo={"MemAvailable": 8 * worker.GIB}, scope=ok_scope) == []
    big = student_server.start_problems(job, meminfo={"MemAvailable": 8 * worker.GIB},
                                        scope={**ok_scope, "memory_max": 12 * worker.GIB})
    low = student_server.start_problems(job, meminfo={"MemAvailable": 5 * worker.GIB}, scope=ok_scope)
    assert "4 GiB" in big[0] and "below" in low[0]
    gpu = {"free_mib": 8_000}
    job["gpu_lock"] = "/nonexistent/lock"
    assert student_server.choose_device(job, gpu=lambda: gpu, lock_free=lambda _p: True)[0] == "cuda:0"
    assert student_server.choose_device(job, gpu=lambda: gpu, lock_free=lambda _p: False)[0] == "cpu"
    assert student_server.choose_device(job, gpu=lambda: {"free_mib": 3_000}, lock_free=lambda _p: True)[0] == "cpu"


def _adopt(root, space, *, base=SP.PRIMARY_BASE, sha="a" * 64):
    set_up_bases(root)
    directory = E.checkpoint_dir(root, space, sha)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "student.json").write_text(json.dumps({"canaries": {}}), encoding="utf-8")
    E.adoption_path(root, space).write_text(json.dumps({"checkpoint_sha256": sha, "base_name": base}), encoding="utf-8")
    return sha


def test_the_adopted_student_starts_lazily_serves_and_queues_the_teacher_replay(tmp_path, monkeypatch):
    paths, repository, root, model, report = student_vault(tmp_path)
    vault = loaded(paths)
    space = _space(paths)
    assert E.adopted_encoder(vault) is None  # nothing adopted: P1's behaviour
    sha = _adopt(root, space)
    encoder = E.adopted_encoder(vault)
    assert encoder is not None and encoder.sha == sha
    monkeypatch.delenv(D.MODELS_ENV, raising=False)
    spawn, _threads = thread_spawn(TeacherService(model))
    encoder.spawn = spawn
    command = E.server_command(Path("/env/python"), Path("/job.json"), unit="u")
    assert command[:8] == ["systemd-run", "--user", "--scope", "--quiet", "--unit=u", "-p", "MemoryMax=4G", "-p"]
    assert "MemorySwapMax=0" in command and command[command.index("--") + 2] == "-I"
    vectors = encoder.encode(["what is a basis"], deadline=time.monotonic() + 5, receipt_id="rq_1")
    assert len(vectors) == 1 and encoder.ready() and len(encoder.start_times()) == 1
    assert encoder.encoder_id.startswith("qe_") and encoder.device_class() == "cpu"
    pending = E.pending_replay(vault.root)
    assert [row["receipt_id"] for row in pending] == ["rq_1"] and pending[0]["checkpoint"] == sha
    job = json.loads((encoder.home / "job.json").read_text())
    assert job["limits"]["min_host_available_gib"] == SP.SERVE_MIN_HOST_AVAILABLE_GIB
    assert job["idle_minutes"] == vault.config.embedding.local.student_idle_minutes


def test_the_kill_switches_take_the_student_and_the_replay_out(tmp_path, monkeypatch):
    paths, repository, root, model, report = student_vault(tmp_path, extra="student = false\n")
    vault = loaded(paths)
    _adopt(root, _space(paths))
    assert E.adopted_encoder(vault) is None
    paths2, repository2, root2, model2, _r = student_vault(tmp_path / "second", extra="teacher_replay = false\n")
    vault2 = loaded(paths2)
    _adopt(root2, _space(paths2))
    encoder = E.adopted_encoder(vault2)
    monkeypatch.delenv(D.MODELS_ENV, raising=False)
    encoder.spawn = thread_spawn(TeacherService(model2))[0]
    encoder.encode(["a question"], deadline=time.monotonic() + 5, receipt_id="rq_2")
    assert E.pending_replay(vault2.root) == []


def _search(paths, repository):
    clear_cache()
    return search_spans(loaded(paths), repository, "eigenvalues of a symmetric matrix", library_scope(repository),
                        deep=True, rewrite=False, embedder=HashingEmbedder(), pool="hybrid_rrf")


def test_the_resolver_serves_the_adopted_student_and_never_waits_for_a_zero_weight_cold_start(tmp_path, monkeypatch):
    from learnloop.ops.embedding_backfill import backfill_embeddings
    from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES
    from learnloop.ai.spend import SpendCaps

    CAPS = SpendCaps(max_candidates=10_000, max_pairs=0, max_calls=100, max_total_tokens=10**8, max_estimated_usd=10.0)

    paths, repository, root, model, report = student_vault(tmp_path)
    assert backfill_embeddings(loaded(paths), caps=CAPS, recipes=("source_block",), registry=SOURCE_RETRIEVAL_RECIPES,
                               client_factory=HashingEmbedder)["status"] == "complete"
    space = _space(paths)
    _adopt(root, space)
    monkeypatch.delenv(D.MODELS_ENV, raising=False)
    started = []

    def spawn(command, *, env, log):
        started.append(command)
        return type("P", (), {"pid": None})()

    monkeypatch.setattr(E, "_spawn", spawn)
    cold = _search(paths, repository).space_selection
    local = cold["spaces"]["local:grouped"]
    assert local["status"] == "encoder_late" and "not waited for" in local["reason"]
    assert started and cold["contributing"] == ["qwen"]
    # With the default on the local space and starts measured in time, the query waits and is served.
    append_config_toml(paths.root, '\n[embedding.source_space]\ndefault = "local:grouped"\n')
    E._ENCODERS.clear()
    encoder = E.adopted_encoder(loaded(paths))
    for _ in range(10):
        encoder._record_start(0.05)
    spawn_thread, _threads = thread_spawn(TeacherService(model))
    monkeypatch.setattr(E, "_spawn", spawn_thread)
    (encoder.status_path).unlink(missing_ok=True)
    served = _search(paths, repository).space_selection
    assert served["spaces"]["local:grouped"]["status"] == "ok", served["spaces"]["local:grouped"]
    assert "local:grouped" in served["contributing"]
    assert "#qe_" in served["spaces"]["local:grouped"]["list"]


def test_a_student_that_never_becomes_ready_is_late_within_the_time_box_never_a_hang(tmp_path, monkeypatch):
    """Batch landing (2026-10-26): a search with no deadline waited for a starting student
    forever (``_await_ready(None)``; a full-suite run hung there under load). Without a
    deadline the start wait is bounded by the query process's own time box
    (``SOCKET_TIMEOUT_S``, the registered `keep` guardrail), and the resolver reports the
    local space as ``encoder_late`` while the others serve."""

    import threading

    from learnloop.ai.spend import SpendCaps
    from learnloop.ops.embedding_backfill import backfill_embeddings
    from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES

    caps = SpendCaps(max_candidates=10_000, max_pairs=0, max_calls=100, max_total_tokens=10**8, max_estimated_usd=10.0)
    paths, repository, root, _model, _report = student_vault(
        tmp_path, extra='\n[embedding.source_space]\ndefault = "local:grouped"\n')
    assert backfill_embeddings(loaded(paths), caps=caps, recipes=("source_block",), registry=SOURCE_RETRIEVAL_RECIPES,
                               client_factory=HashingEmbedder)["status"] == "complete"
    _adopt(root, _space(paths))
    monkeypatch.delenv(D.MODELS_ENV, raising=False)
    # A started query process that never writes its ready status (stalled, or starved under load).
    monkeypatch.setattr(E, "_spawn", lambda command, *, env, log: type("P", (), {"pid": None})())
    monkeypatch.setattr(SP, "SOCKET_TIMEOUT_S", 0.5)
    E._ENCODERS.clear()
    encoder = E.adopted_encoder(loaded(paths))
    for _ in range(10):
        encoder._record_start(0.05)  # starts measured in time: the resolver waits rather than skips
    out: dict = {}

    def run() -> None:
        try:
            out["selection"] = _search(paths, repository).space_selection
        except BaseException as exc:  # noqa: BLE001 - reported below
            out["error"] = exc

    thread = threading.Thread(target=run, daemon=True)
    started = time.monotonic()
    thread.start()
    thread.join(20)
    assert not thread.is_alive(), "the search waited for the student without a bound"
    assert "error" not in out, out.get("error")
    assert time.monotonic() - started < 20
    local = out["selection"]["spaces"]["local:grouped"]
    assert local["status"] == "encoder_late", local
    assert "qwen" in out["selection"]["contributing"]


def test_the_nightly_index_batch_replays_the_queued_queries_with_the_teacher(tmp_path, monkeypatch):
    paths, repository, root, model, report = student_vault(tmp_path)
    vault = loaded(paths)
    space = _space(paths)
    _adopt(root, space)
    student = TeacherService(model).encode(["how are eigenvectors found"])[0]
    assert E.queue_replay(vault, receipt_id="rq_9", texts=["how are eigenvectors found"], vectors=[student],
                          encoder_id="qe_x", checkpoint_sha="a" * 64) == 1
    launcher = InProcessLauncher(model)
    out = local_index.run_local_index(vault, repository, launcher=launcher, preflight=lambda: [], locks=no_locks,
                                      force=True)
    assert out["replay_queries"] == 1 and out["replay"]["replayed"] == 1, out
    assert out["replay"]["agreement_mean"] == 1.0  # the fake student is its teacher
    assert launcher.jobs[-1]["queries"][0]["text"] == "how are eigenvectors found"
    assert E.pending_replay(vault.root) == []
    summary = E.replay_report(vault, repository)
    assert summary["replayed"] == 1 and summary["pending"] == 0
    idle = local_index.run_local_index(vault, repository, launcher=launcher, preflight=lambda: [], locks=no_locks,
                                       force=True)
    assert idle["status"] == "complete" and idle["replay_queries"] == 0


def test_the_whole_p2_dry_run_starts_nothing_and_estimates_time_gpu_and_plan_calls(tmp_path):
    paths, repository, root, _model, _report = student_vault(tmp_path)
    fake = FakeGenerator()
    out = Q.plan(loaded(paths), repository, bank_path=default_bank(tmp_path, repository), client=fake)
    assert out["status"] == "dry_run" and fake.prompts == []
    assert out["plan_calls"] >= 1 and out["gpu_hours_estimate_total"] < SP.P2_GPU_HOURS_CAP
    assert out["training_runs"][0]["recipe"] == "projection_only" and out["targets"]["gpu_minutes_estimate"] > 0
    assert Q.status(loaded(paths), repository)["adopted"] is None


def test_a_student_that_misses_the_time_box_is_late_and_the_others_serve(tmp_path, monkeypatch):
    from learnloop.ai.spend import SpendCaps
    from learnloop.ops.embedding_backfill import backfill_embeddings
    from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES

    paths, repository, root, model, report = student_vault(
        tmp_path, extra='\n[embedding.source_space]\ndefault = "local:grouped"\n')
    caps = SpendCaps(max_candidates=10_000, max_pairs=0, max_calls=100, max_total_tokens=10**8, max_estimated_usd=10.0)
    assert backfill_embeddings(loaded(paths), caps=caps, recipes=("source_block",), registry=SOURCE_RETRIEVAL_RECIPES,
                               client_factory=HashingEmbedder)["status"] == "complete"

    class Late:
        encoder_id = "qe_late"
        accepts_receipt = True

        def encode(self, texts, *, deadline=None, receipt_id=None):
            raise TimeoutError("the query student did not start within the time box")

    monkeypatch.setattr(spaces, "LOCAL_QUERY_ENCODER", lambda _vault: Late())
    selection = _search(paths, repository).space_selection
    assert selection["spaces"]["local:grouped"]["status"] == "encoder_late"
    assert selection["spaces"]["local:grouped"]["query"]["status"] == "encoder_late"
    assert "qwen" in selection["contributing"]  # the extractions the late student held are reassigned


# -- Codex review fixes (stage retrieval-lr-p2-query-student) -------------------------------------------------
def test_the_default_base_loader_is_called_with_its_keyword_only_device(torch_present, tmp_path, monkeypatch):
    """F1: production training reaches ``load_base`` (device keyword-only); only the Hugging Face
    loaders are replaced, by the tiny model and tokenizer."""

    import transformers

    from learnloop.local_embeddings import student_trainer
    from tests.query_student_fakes import TinyTokenizer, tiny_model

    seen = {}

    def model_from(path, **kwargs):
        seen["model"] = (path, kwargs)
        return tiny_model()

    def tokenizer_from(path, **kwargs):
        seen["tokenizer"] = (path, kwargs)
        return TinyTokenizer()

    monkeypatch.setattr(transformers.AutoModel, "from_pretrained", model_from)
    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained", tokenizer_from)
    paths, repository, root, _model, space, bank = _targets(tmp_path)
    data = tmp_path / "data"
    stats = Q.build_dataset(loaded(paths), repository, root=root, space=space, budget=2_000, bank_path=bank,
                            out_dir=data)
    job = Q.trainer_job({"base": SP.PRIMARY_BASE, "recipe": "align", "budget": 2_000, "seed": 0}, space=space,
                        base_dir=tmp_path, data_dir=data, out_dir=tmp_path / "out", temperature=stats["temperature"],
                        plan_id="t")
    job["epochs"] = 1
    output = student_trainer.run_training(job, device="cpu", base_check=lambda _job: [])
    assert output["status"] == "complete", output
    assert seen["model"][1]["local_files_only"] is True and seen["model"][1]["trust_remote_code"] is True


def test_a_targets_run_interrupted_before_the_bank_shards_admits_no_question(tmp_path):
    """F2: the query shards finished, the bank's did not: nothing is screened, nothing trains, and
    the twin of a bank question is dropped once the complete bank is screened."""

    paths, repository, root, model, space, bank = _generated(tmp_path)
    vault = loaded(paths)
    rows = D.stored_queries(D.data_dir(root, space, vault))
    twin = next(row for row in rows if row["split"] == "train" and row["shape"] != "deictic")
    write_bank(bank, json.loads(bank.read_text()) + [{"query_id": "bank_twin", "question": twin["text"],
                                                      "evidence_sets": []}])

    class AbortsBeforeTheBank(InProcessLauncher):
        def __call__(self, job, workdir, *, meter, plan_id):
            job["query_shards"] = [shard for shard in job["query_shards"] if shard["name"].startswith("q")]
            output = super().__call__(job, workdir, meter=meter, plan_id=plan_id)
            return {**output, "status": "aborted", "reason": "below the host floor"}

    partial = Q.run_targets(vault, repository, bank_path=bank, launcher=AbortsBeforeTheBank(model),
                            preflight=lambda: [], locks=no_locks)
    assert partial["status"] == "partial" and partial["leakage_screen"]["complete"] is False, partial
    index = Q.targets_index(SP.space_home(root, space))
    assert twin["id"] in index["queries"] and Q.eligible_rows(rows, index, D.load_bank(bank)) == []
    set_up_bases(root)
    refused = Q.run_next(vault, repository, bank_path=bank, launcher=InProcessTrainer(), preflight=lambda: [],
                         locks=no_locks)
    assert refused["status"] == "refused" and "teacher target" in refused["reason"]
    done = Q.run_targets(vault, repository, bank_path=bank, launcher=InProcessLauncher(model), preflight=lambda: [],
                         locks=no_locks)
    assert done["status"] == "complete" and done["bank_owed"] == 2, done
    index = Q.targets_index(SP.space_home(root, space))
    eligible = {row["id"] for row in Q.eligible_rows(rows, index, D.load_bank(bank))}
    assert twin["id"] in index["dropped"] and twin["id"] not in eligible and eligible
    # Another bank (a changed question) is another screen: nothing is eligible until it is screened.
    write_bank(bank, json.loads(bank.read_text())[:-1])
    assert Q.eligible_rows(rows, index, D.load_bank(bank)) == []


def test_training_candidates_hold_training_families_only_and_no_bank_tainted_window(tmp_path):
    """F3: the KD top-k and the hard negatives come from an explicit manifest: no held-out family,
    no block whose contextual window holds a bank support, negatives from the query's own source."""

    from learnloop.source_retrieval.windows import windows_by_extraction

    paths, repository, root, _model, space, bank = _targets(tmp_path)
    vault = loaded(paths)
    camp = Q.campaign(vault, repository, root=root, space=space, bank=D.load_bank(bank))
    candidates = camp["candidates"]
    held = set(candidates["held_out"])
    assert held and not held & set(candidates["families"])
    held_extractions = {e for e, family in camp["by_extraction"].items() if family in held}
    assert not any(record.split("/")[0] in held_extractions for record in candidates["ids"])
    gold = find_gold(repository)
    windows = windows_by_extraction(vault, repository, ["ext_book"], ("grouped",))[("ext_book", "grouped")]
    tainted = {member.span_id for window in windows if any(m.span_id == gold for m in window.members)
               for member in window.members}
    if "ext_book" not in held_extractions:
        assert len(tainted) > 1 and candidates["bank_tainted_blocks"] >= len(tainted)
        assert not any(record == f"ext_book/{span}" for span in tainted for record in candidates["ids"])
    data = tmp_path / "data"
    Q.build_dataset(vault, repository, root=root, space=space, budget=2_000, bank_path=bank, out_dir=data, camp=camp)
    negatives = json.loads((data / "train_negatives.json").read_text())
    train = D.nested(camp["rows"], 2_000)
    assert len(negatives) == len(train)
    assert all(candidates["sources"][index] == row["extraction_id"]
               for row, found in zip(train, negatives) for index in found)


def test_unjudged_retrieved_material_is_latent_never_a_miss():
    """F5 (and re-review F5): a top 10 that completes no evidence set but holds a block the
    protocol never judged is unknown (imputed by the posterior, listed for labelling); with every
    retrieved block judged it is a miss. A bank without judged lists judged only its evidence, so
    its other retrieved blocks stay latent, never a failure."""

    question = {"evidence_sets": [[("ext", "s1"), ("ext", "s2")]], "judged": [("ext", "s3")]}
    assert Q.judged_outcome(["ext/s1", "ext/s2"], question) == 1.0
    assert Q.judged_outcome(["ext/s1", "ext/s3"], question) == 0.0
    assert Q.judged_outcome(["ext/s1", "ext/s9"], question) is None
    assert Q.unjudged_blocks(["ext/s1", "ext/s9"], question) == ["ext/s9"]
    assert Q.judged_outcome(["ext/s1", "ext/s9"], {**question, "judged": None}) is None
    assert Q.judged_outcome(["ext/s1", "ext/s3"], {**question, "judged": None}) is None
    assert Q.judged_outcome(["ext/s1", "ext/s2"], {**question, "judged": None}) == 1.0
    # The judged lists are labels: they are part of the bank's identity.
    bank = [{"query_id": "q", "text": "t", "evidence_sets": question["evidence_sets"], "answer_spans": [],
             "judged": question["judged"]}]
    assert Q.bank_fingerprint(bank) != Q.bank_fingerprint([{**bank[0], "judged": None}])


def test_the_query_process_never_runs_a_changed_base(tmp_path, monkeypatch):
    """F6: the base's pinned files are checked before ``load_base`` (trust_remote_code) runs any of
    them: a ``modeling.py`` changed after setup refuses the start, and the loader is never reached."""

    from learnloop.local_embeddings import student_server, student_trainer

    base_dir = tmp_path / "base"
    base_dir.mkdir()
    (base_dir / "modeling.py").write_text("x = 1\n", encoding="utf-8")
    pinned = {"modeling.py": (6, student_trainer.sha256_file(base_dir / "modeling.py"))}
    base = {**SP.STUDENT_BASES[SP.PRIMARY_BASE], "files": pinned, "remote_code": ["modeling.py"], "inert_python": []}
    job = {"base_dir": str(base_dir), "base": base, "status_path": str(tmp_path / "status.json"),
           "checkpoint_sha256": "a" * 64, "limits": {}}
    assert student_server.base_check(job) == []
    (base_dir / "modeling.py").write_text("x = 2\n", encoding="utf-8")  # same size, other code
    (tmp_path / "job.json").write_text(json.dumps(job), encoding="utf-8")
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "HF_HOME", "HF_MODULES_CACHE",
                "TOKENIZERS_PARALLELISM"):
        monkeypatch.setenv(key, "test")
    monkeypatch.setattr(student_server.W, "_guard_network", lambda: None)
    monkeypatch.setattr(student_server, "start_problems", lambda *_a, **_k: [])
    monkeypatch.setattr(student_server, "checkpoint_problems", lambda _job: [])

    def never(*_args, **_kwargs):
        raise AssertionError("the base loader ran")

    monkeypatch.setattr(student_server, "load_service", never)
    monkeypatch.setattr(student_trainer, "load_base", never)
    assert student_server.main(["--job", str(tmp_path / "job.json")]) == 3
    status = json.loads((tmp_path / "status.json").read_text())
    assert status["status"] == "refused" and "modeling.py" in status["reason"]


def test_a_client_that_gives_up_never_stops_the_query_process(_fresh):
    """F12: the first client times out and closes its socket before the reply; the process keeps
    serving and the second client is answered."""

    import socket as socket_module
    import threading

    from learnloop.local_embeddings import student_server

    class Slow(TeacherService):
        def encode(self, texts):
            time.sleep(0.4)
            return super().encode(texts)

    socket_path = _fresh / "slow.sock"
    reasons = []
    thread = threading.Thread(target=lambda: reasons.append(student_server.serve_forever(
        Slow(), socket_path, idle_s=5.0, timeout_s=0.2)), daemon=True)
    thread.start()
    for _ in range(200):
        if socket_path.exists():
            break
        time.sleep(0.01)
    with pytest.raises((TimeoutError, socket_module.timeout)):
        E.request(socket_path, {"op": "encode", "texts": ["slow"]}, timeout_s=0.05)
    time.sleep(0.6)  # the reply to the closed socket has failed by now
    assert thread.is_alive()
    reply = E.request(socket_path, {"op": "encode", "texts": ["what is a basis"]}, timeout_s=5.0)
    assert reply["ok"] and len(reply["vectors"]) == 1
    assert E.request(socket_path, {"op": "shutdown"}, timeout_s=5.0)["ok"]
    thread.join(timeout=5)
    assert reasons == ["shutdown"]


def test_a_resident_gpu_student_yields_before_an_index_batch(tmp_path, _fresh, monkeypatch):
    """F11: a student serving on the GPU is asked to exit before the 9B's start checks; the index
    batch then runs. A CPU student is not a GPU workload and is left alone."""

    import threading

    from learnloop.local_embeddings import student_server

    paths, repository, root, model, _report = student_vault(tmp_path)
    home = _fresh / "learnloop-student" / "abc"
    home.mkdir(parents=True)
    socket_path = home / "student.sock"
    thread = threading.Thread(target=student_server.serve_forever, args=(TeacherService(model), socket_path),
                              kwargs={"idle_s": 30.0, "timeout_s": 0.2}, daemon=True)
    thread.start()
    for _ in range(200):
        if socket_path.exists():
            break
        time.sleep(0.01)
    (home / "status.json").write_text(json.dumps({"status": "ready", "device": "gpu", "pid": 4242}), encoding="utf-8")
    cpu_home = _fresh / "learnloop-student" / "cpu"
    cpu_home.mkdir()
    (cpu_home / "status.json").write_text(json.dumps({"status": "ready", "device": "cpu", "pid": 4343}),
                                          encoding="utf-8")
    monkeypatch.setattr(E, "_pid_alive", lambda pid: thread.is_alive() if pid == 4242 else pid == 4343)
    order = []

    def preflight():
        order.append("preflight")
        return ["a concurrent GPU workload is running (python)"] if thread.is_alive() else []

    def yielder():
        order.append("yield")
        return E.yield_gpu_students(wait_s=5.0)

    from tests.query_student_fakes import CALCULUS
    from tests.source_retrieval_fakes import seed_source

    seed_source(repository, source_id="src_new", revision_id="rev_new", extraction_id="ext_new",
                title="New Notes", units=CALCULUS)  # a new book: the batch has work
    seed = local_index.run_local_index(loaded(paths), repository, launcher=InProcessLauncher(model),
                                       preflight=preflight, locks=no_locks, force=True, yielder=yielder)
    assert order[:2] == ["yield", "preflight"] and not thread.is_alive()
    assert seed["students_yielded"] == {"asked": 1, "exited": 1, "still_running": 0}
    assert seed["status"] != "waiting_for_gpu", seed


def test_a_due_replay_is_scheduled_for_a_fully_indexed_library(tmp_path):
    """F10: indexing is complete and the adopted student's queries wait; the host's sweep queues one
    replay-only index batch (once), and nothing while a batch ran within the cadence."""

    import threading
    from types import SimpleNamespace
    from datetime import datetime, timedelta, timezone

    from learnloop.content.pipeline.jobs import DurableIngestJobs
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec
    from learnloop.db.repositories import Repository

    paths, repository, root, model, _report = student_vault(tmp_path)
    vault = loaded(paths)
    assert vault.config.source_retrieval.dense
    runner = IngestRunner(Repository(repository.sqlite_path), vault_root=paths.root, worker_id="test")
    first = runner.enqueue_batch(local_index.INDEX_JOB, [JobSpec(local_index.INDEX_JOB, {"extraction_id": "ext_book"})])
    [job] = repository.ingest_jobs_for_batch(first)
    assert repository.transition_unleased_ingest_job(job["id"], status="completed", result={"status": "complete"})
    [job] = repository.ingest_jobs_for_batch(first)
    started: list[int] = []
    now = datetime.now(timezone.utc)
    host = SimpleNamespace(_runner=runner, _stop=threading.Event(), reading_now=lambda: now, _background=True,
                           _lock=threading.Lock(), _worker_thread=SimpleNamespace(is_alive=lambda: True),
                           _ensure_worker=lambda: started.append(1))
    assert DurableIngestJobs.resume_contextual_index(host) is None  # no replay queued
    vector = TeacherService(model).encode(["how are eigenvectors found"])[0]
    E.queue_replay(vault, receipt_id="rq_1", texts=["how are eigenvectors found"], vectors=[vector],
                   encoder_id="qe_x", checkpoint_sha="a" * 64)
    assert DurableIngestJobs.resume_contextual_index(host) is None  # the batch above ran within the cadence
    host.reading_now = lambda: now + timedelta(hours=SP.REPLAY_EVERY_HOURS + 1)
    batch = DurableIngestJobs.resume_contextual_index(host)
    assert batch == f"{local_index.INDEX_JOB}_replay_after_{job['id']}" and started == [1]
    [queued] = repository.ingest_jobs_for_batch(batch)
    assert queued["status"] == "queued" and queued["payload"]["replay"] is True
    assert DurableIngestJobs.resume_contextual_index(host) is None  # the replay batch is live: nothing twice
    # The queued batch, run, replays the queue with the teacher (no items owed).
    out = local_index.run_local_index(vault, repository, launcher=InProcessLauncher(model), preflight=lambda: [],
                                      locks=no_locks, now=now + timedelta(hours=SP.REPLAY_EVERY_HOURS + 1))
    assert out["replay"]["replayed"] == 1 and E.pending_replay(vault.root) == []


def test_families_group_editions_and_bank_questions_by_their_evidence(tmp_path):
    """F8: one persisted family mapping: alternate editions share a family (splits by family), and a
    bank question's family is its evidence's, whatever alias the bank's own tool gave it."""

    from tests.query_student_fakes import PROBABILITY
    from tests.source_retrieval_fakes import seed_source

    paths, repository, root, _model, _report = student_vault(tmp_path)
    seed_source(repository, source_id="src_prob_2e", revision_id="rev_prob_2e", extraction_id="ext_prob_2e",
                title="Probability Notes 2nd edition", units=PROBABILITY)
    directory = tmp_path / "families"
    families = D.family_map(directory, repository)
    assert families["src_prob"] == families["src_prob_2e"] != families["src_calc"]
    assert json.loads((directory / "families.json").read_text())["sources"] == families
    by_extraction = D.extraction_families(repository, families)
    question = {"evidence_sets": [[("ext_prob_2e", "s1")]], "answer_spans": [], "family": "fam_3f2a9c"}
    assert D.question_families(question, by_extraction) == {families["src_prob"]}
    found = [{**p, "family": families[p["source_id"]]} for p in D.passages(loaded(paths), repository, excluded=set())]
    held = D.held_out_family(found)
    splits = {D.split_of(p, held) for p in found if p["source_id"] in ("src_prob", "src_prob_2e")}
    assert splits == {"heldout"} or "heldout" not in splits  # both editions on the same side


def test_a_run_is_reused_only_on_the_dataset_it_learned(tmp_path):
    """F9: the schedule's completed runs carry their dataset fingerprint; another vault, bank or
    candidate set starts the schedule again."""

    teacher_q = np.full(64, 0.8)
    run = {"run_id": "r1", "status": "complete", "checkpoint_sha256": "c" * 64, "charged_s": 1.0,
           "dev": {"agreements": [0.9] * 10}, "latency": {}, "load_s": 0.1,
           "spec": {"base": SP.PRIMARY_BASE, "recipe": "projection_only", "budget": 100, "seed": 0, "dataset": "A"}}
    ledger = {"runs": {"r1": run}, "decisions": []}
    same = Q.next_step(ledger, n_train=100, has_positives=True, teacher_q=teacher_q, box_s=2.0, hours_left=5.0,
                       dataset="A")
    other = Q.next_step(ledger, n_train=100, has_positives=True, teacher_q=teacher_q, box_s=2.0, hours_left=5.0,
                        dataset="B")
    assert same["spec"]["recipe"] == "align" and other["spec"]["recipe"] == "projection_only"
    assert other["spec"]["dataset"] == "B"
    paths, repository, root, _model, space, bank = _targets(tmp_path)
    vault = loaded(paths)
    first = Q.campaign(vault, repository, root=root, space=space, bank=D.load_bank(bank))
    write_bank(tmp_path / "bank2.json", json.loads(bank.read_text()) + [
        {"query_id": "bank_extra", "question": "What is a random variable?", "evidence_sets": []}])
    second = Q.campaign(vault, repository, root=root, space=space, bank=D.load_bank(tmp_path / "bank2.json"))
    assert first["fingerprint"] != second["fingerprint"] and second["rows"] == []  # not screened by bank2 yet


# -- Codex re-review (F4, F5, F16, F17, F18): evaluation without the trainer --------------------------------
def _fake_run(root, space, *, sha="b" * 64, dataset="", run_id="run_fake"):
    """One completed run's checkpoint in the ledger (no trainer: these tests run without torch)."""

    directory = E.checkpoint_dir(root, space, sha)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "student.json").write_text(json.dumps({"canaries": {}}), encoding="utf-8")
    home = SP.space_home(root, space)
    ledger = Q.read_ledger(home)
    ledger["runs"][run_id] = {"run_id": run_id, "status": "complete", "checkpoint_sha256": sha, "load_s": 0.1,
                              "dev": {"agreements": [0.9] * 4}, "latency": {},
                              "spec": {"base": SP.PRIMARY_BASE, "recipe": "align", "budget": 100, "seed": 0,
                                       "dataset": dataset}}
    (home / "p2-ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
    return sha


def _evaluable(tmp_path):
    """Targets for a bank whose evidence is the teacher's own top blocks, the bases, and one
    completed checkpoint trained on the current campaign."""

    paths, repository, root, model, space, _default = _generated(tmp_path)
    vault = loaded(paths)
    bank = _bank_for(paths, repository, model, space, good=True, tmp_path=tmp_path)
    _bank_targets(paths, repository, model, bank)
    set_up_bases(root)
    camp = Q.campaign(vault, repository, root=root, space=space, bank=D.load_bank(bank))
    sha = _fake_run(root, space, dataset=camp["fingerprint"])
    return paths, repository, root, model, space, bank, sha


def _arm(path, comparison, outcomes):
    path.write_text(json.dumps({"comparison": comparison, "outcomes": outcomes}), encoding="utf-8")
    return path


def test_priors_never_decide_and_no_evaluation_changes_serving_by_itself(tmp_path):
    """Re-review F4, F5: E1's aggregates are reported as priors, never actions in the decision; a
    supplied arm must carry this comparison's fingerprint (bank labels, candidate units,
    questions); a losing re-evaluation RECOMMENDS withdrawal (a verifier verdict), the owner's
    reject withdraws."""

    paths, repository, root, model, space, bank, sha = _evaluable(tmp_path)
    vault = loaded(paths)
    factory = lambda _sha: _TeacherEncoder(model)  # noqa: E731
    first = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, checkpoint=sha)
    assert first["recommendation"] == "unmeasured" and first["status"] == "unmeasured", first
    assert set(first["decision"]["expected_utility"]) == {"student"}
    assert set(first["prior_alternatives"]) == {"qwen", "voyage"}
    assert all(item["basis"].startswith("prior:") for item in first["prior_alternatives"].values())
    assert first["authority"]["automatic"] is False and first["authority"]["comparable_alternatives"] is False
    adopted = Q.owner_choice(vault, repository, accept=True)
    assert adopted["status"] == "adopted" and adopted["lambda_observation"] is None  # no costed choice was offered
    assert E.read_adoption(root, space)["checkpoint_sha256"] == sha
    comparison = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, checkpoint=sha,
                            dry_run=True)["comparison_fingerprint"]
    scoped = [q["query_id"] for q in D.load_bank(bank)]
    # An arm without this comparison's provenance, or with another one, is refused.
    bare = tmp_path / "bare.json"
    bare.write_text(json.dumps({qid: 1.0 for qid in scoped}), encoding="utf-8")
    refused = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, checkpoint=sha,
                         arms={"qwen": bare})
    assert refused["status"] == "refused" and "comparison" in refused["reason"]
    other = _arm(tmp_path / "other.json", "f" * 64, {qid: 1.0 for qid in scoped})
    assert Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, checkpoint=sha,
                      arms={"qwen": other})["status"] == "refused"
    partial = _arm(tmp_path / "partial.json", comparison, {scoped[0]: 1.0})
    partial_out = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, checkpoint=sha,
                             arms={"qwen": partial})
    assert partial_out["status"] == "refused" and "same questions" in partial_out["reason"]
    # Better measured alternatives: withdrawal is recommended, never applied by the rule.
    arms = {name: _arm(tmp_path / f"{name}.json", comparison, {qid: 1.0 for qid in scoped})
            for name in ("qwen", "voyage")}
    again = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, checkpoint=sha, arms=arms)
    assert again["recommendation"] == "keep_alternatives" and again["status"] == "withdrawal_recommended", again
    assert again["alternatives"]["qwen"].startswith("measured")
    assert again["withdrawal"]["checkpoint_sha256"] == sha and "student reject" in again["withdrawal"]["command"]
    assert E.read_adoption(root, space)["checkpoint_sha256"] == sha  # still serving: the owner decides
    rejected = Q.owner_choice(vault, repository, accept=False)
    assert rejected["status"] == "rejected" and rejected["withdrawn"] and E.read_adoption(root, space) is None
    assert [verdict for _judge, verdict, _left in _judgments(paths)] == [
        "recommend_unmeasured", "adopt", "recommend_keep_alternatives", "recommend_withdraw", "reject", "withdrawn"]


def test_consecutive_owner_decisions_resolve_to_their_evaluation(tmp_path):
    """Re-review F16: adopt then reject (and reject then adopt) the same evaluated checkpoint with
    no evaluation in between, with and without --checkpoint."""

    paths, repository, root, _model, _report = student_vault(tmp_path)
    space = _space(paths)
    vault = loaded(paths)
    set_up_bases(root)
    sha = _fake_run(root, space)
    home = SP.space_home(root, space)
    ledger = Q.read_ledger(home)
    ledger["decisions"].append({"kind": "evaluation", "evaluation_id": "ev_1", "checkpoint_sha256": sha,
                                "space_id": space, "base_name": SP.PRIMARY_BASE, "recommendation": "adopt",
                                "choice": {"against": "qwen", "dq": 0.01, "cost": 0.0, "s": 0.02},
                                "judgment_id": None})
    (home / "p2-ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
    assert Q.owner_choice(vault, repository, accept=True)["status"] == "adopted"
    rejected = Q.owner_choice(vault, repository, accept=False)
    assert rejected["status"] == "rejected" and rejected["withdrawn"] and E.read_adoption(root, space) is None
    again = Q.owner_choice(vault, repository, accept=True, checkpoint=sha)
    assert again["status"] == "adopted" and E.read_adoption(root, space)["evaluation_id"] == "ev_1"
    assert Q.owner_choice(vault, repository, accept=False, checkpoint=sha)["status"] == "rejected"


def test_the_serving_checkpoint_is_reevaluated_on_corrected_labels(tmp_path):
    """Re-review F17: corrected evidence makes a new campaign (training reuse stops), but the
    serving checkpoint (or any completed one, by --checkpoint) is still evaluated on the new bank."""

    paths, repository, root, model, space, bank, sha = _evaluable(tmp_path)
    vault = loaded(paths)
    factory = lambda _sha: _TeacherEncoder(model)  # noqa: E731
    assert Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, checkpoint=sha)["checkpoint_sha256"] == sha
    Q.owner_choice(vault, repository, accept=True)
    rows = json.loads(bank.read_text())
    ids, _matrix = Q.documents(vault, repository, space)
    extraction, span = split_record_id(ids[-1])
    rows[0]["evidence_sets"] = [{"set_id": "e", "required": [[extraction, span, 0, 1]]}]  # a corrected label
    corrected = write_bank(tmp_path / "corrected.json", rows)
    _bank_targets(paths, repository, model, corrected)
    out = Q.evaluate(vault, repository, bank_path=corrected, encoder_factory=factory)
    assert out["status"] != "not_ready" and out["checkpoint_sha256"] == sha, out
    assert out["candidate_basis"] == "serving" and out["trained_on_current_dataset"] is False
    record = Q.read_ledger(SP.space_home(root, space))["decisions"][-1]
    assert record["bank_fingerprint"] == Q.bank_fingerprint(D.load_bank(corrected))
    explicit = Q.evaluate(vault, repository, bank_path=corrected, encoder_factory=factory, checkpoint=sha)
    assert explicit["candidate_basis"] == "explicit" and explicit["checkpoint_sha256"] == sha
    missing = Q.evaluate(vault, repository, bank_path=corrected, encoder_factory=factory, checkpoint="c" * 64)
    assert missing["status"] == "refused"


def test_dry_runs_never_write_the_family_mapping(tmp_path):
    """Re-review F18: `student train --dry-run` and `student evaluate --dry-run` read the persisted
    family mapping and compute additions in memory; neither creates nor rewrites families.json."""

    paths, repository, root, model, space, bank, sha = _evaluable(tmp_path)
    vault = loaded(paths)
    path = D.data_dir(root, space, vault) / "families.json"
    stored = json.loads(path.read_text())
    real = Q.campaign(vault, repository, root=root, space=space, bank=D.load_bank(bank))["fingerprint"]
    path.unlink()
    assert Q.run_next(vault, repository, bank_path=bank, dry_run=True)["status"] == "dry_run"
    assert Q.evaluate(vault, repository, bank_path=bank, dry_run=True, checkpoint=sha)["status"] == "dry_run"
    assert not path.exists()
    outdated = {"sources": {}, "keys": {}}
    path.write_text(json.dumps(outdated), encoding="utf-8")
    Q.run_next(vault, repository, bank_path=bank, dry_run=True)
    assert json.loads(path.read_text()) == outdated
    path.write_text(json.dumps(stored), encoding="utf-8")
    dry = Q.campaign(vault, repository, root=root, space=space, bank=D.load_bank(bank), persist=False)
    assert dry["fingerprint"] == real


# -- Codex final verify (F19): evaluation strata from the checkpoint's own training families ------------------
def _pinned_run(root, space, *, families, dataset, run_id, provenance="current"):
    """A completed run whose checkpoint manifest is pinned (its SHA is the manifest's digest) and,
    unless ``families`` is None, records the families it trained on (no trainer: no torch), under
    the current producer's provenance version unless ``provenance`` names another (None: none)."""

    from learnloop.local_embeddings import student_trainer

    if provenance == "current":
        provenance = getattr(Q, "TRAINING_FAMILIES_PROVENANCE", None)

    manifest = {"format": SP.CHECKPOINT_FORMAT, "space_id": space, "base_name": SP.PRIMARY_BASE, "base": {},
                "recipe": "align", "seed": 0, "budget": 100, "dims": SP.STUDENT_DIMENSIONS,
                "precision": SP.STUDENT_PRECISION, "frozen_base": False, "max_query_tokens": SP.MAX_QUERY_TOKENS,
                "files": {}, "canaries": {}, "dataset_fingerprint": dataset}
    if families is not None:
        manifest["training_families"] = sorted(families)
        if provenance is not None:
            manifest["training_families_provenance"] = provenance
    sha = student_trainer.checkpoint_digest(manifest)
    _fake_run(root, space, sha=sha, dataset=dataset, run_id=run_id)
    (E.checkpoint_dir(root, space, sha) / "student.json").write_text(json.dumps(manifest), encoding="utf-8")
    return sha


def test_reevaluation_strata_come_from_the_checkpoint_training_families(tmp_path, monkeypatch):
    """F19: a checkpoint trained on family A, re-evaluated against a newly screened campaign with
    no eligible A row, never reports A's bank questions as an unseen family: the strata come from
    the families pinned in the checkpoint's manifest. A checkpoint without recoverable provenance
    puts those questions under ``unknown_family``, never seen or unseen."""

    from learnloop.local_embeddings import student_trainer

    paths, repository, root, model, space, bank, current_sha = _evaluable(tmp_path)
    vault = loaded(paths)
    factory = lambda _sha: _TeacherEncoder(model)  # noqa: E731
    real_campaign = Q.campaign

    def rescreened(*args, **kwargs):  # the new campaign holds no eligible row of the old families
        camp = real_campaign(*args, **kwargs)
        return {**camp, "candidates": {**camp["candidates"], "families": []}}

    monkeypatch.setattr(Q, "campaign", rescreened)
    camp = Q.campaign(vault, repository, root=root, space=space, bank=D.load_bank(bank))
    scoped, _outside = Q.bank_scope(D.load_bank(bank), repository)
    question_families = {q["query_id"]: D.question_families(q, camp["by_extraction"]) for q in scoped}
    with_family = {qid for qid, found in question_families.items() if found}
    assert with_family  # the bank's questions are supported by indexed families
    family_a = set().union(*question_families.values())

    trained = _pinned_run(root, space, families=family_a, dataset="old-dataset", run_id="run_a")
    out = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, checkpoint=trained)
    assert out["trained_on_current_dataset"] is False
    assert "unseen_family" not in out["strata"], out["strata"]  # pre-fix: every family-A question was "unseen"
    assert "unknown_family" not in out["strata"]
    assert out["training_families"] == {"basis": "checkpoint_manifest", "families": len(family_a)}
    record = Q.read_ledger(SP.space_home(root, space))["decisions"][-1]
    assert record["training_families"]["basis"] == "checkpoint_manifest"

    # The same checkpoint trained on another family: A's questions ARE unseen.
    other = _pinned_run(root, space, families={"another-family"}, dataset="old-dataset", run_id="run_b")
    unseen = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, checkpoint=other)
    assert unseen["strata"]["unseen_family"]["questions"] == len(with_family)

    # No recoverable provenance (a legacy manifest, another dataset): unknown, never seen or unseen.
    legacy = _pinned_run(root, space, families=None, dataset="older-dataset", run_id="run_c")
    unknown = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, checkpoint=legacy)
    assert "unseen_family" not in unknown["strata"]
    assert unknown["strata"]["unknown_family"]["questions"] == len(with_family)
    assert unknown["training_families"] == {"basis": "unknown", "families": None}

    # A manifest that no longer matches its pin is not provenance either.
    path = E.checkpoint_dir(root, space, trained) / "student.json"
    tampered = {**json.loads(path.read_text()), "training_families": ["another-family"]}
    path.write_text(json.dumps(tampered), encoding="utf-8")
    assert student_trainer.checkpoint_digest(tampered) != trained
    forged = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, checkpoint=trained)
    assert forged["training_families"]["basis"] == "unknown" and "unseen_family" not in forged["strata"]

    # A legacy checkpoint trained on the CURRENT dataset: that dataset names its families.
    current = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, checkpoint=current_sha)
    assert current["trained_on_current_dataset"] is True
    assert current["training_families"]["basis"] == "current_dataset"


def test_the_trainer_job_and_manifest_pin_the_training_families():
    """F19: the job carries the run's training families, and the checkpoint digest covers them when
    recorded (a manifest without them, made before F19, keeps its digest)."""

    from learnloop.local_embeddings import student_trainer

    job = Q.trainer_job({"base": SP.PRIMARY_BASE, "recipe": "align", "budget": 100, "seed": 0}, space="s",
                        base_dir=Path("/b"), data_dir=Path("/d"), out_dir=Path("/o"), temperature=0.1, plan_id="p",
                        dataset_fingerprint="ds", training_families=["b", "a"])
    assert job["training_families"] == ["a", "b"]
    legacy = {"format": SP.CHECKPOINT_FORMAT, "space_id": "s", "base_name": SP.PRIMARY_BASE, "base": {},
              "recipe": "align", "seed": 0, "budget": 100, "dims": 1, "precision": "p", "frozen_base": False,
              "max_query_tokens": 1, "files": {}, "dataset_fingerprint": "ds"}
    core = {key: legacy[key] for key in legacy}
    assert student_trainer.checkpoint_digest(legacy) == __import__("hashlib").sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    pinned = {**legacy, "training_families": ["a", "b"]}
    assert student_trainer.checkpoint_digest(pinned) != student_trainer.checkpoint_digest(legacy)
    assert student_trainer.checkpoint_digest({**legacy, "training_families": ["a"]}) != \
        student_trainer.checkpoint_digest(pinned)


# -- F19 reopened (scoped verify 20261026-151935-zeVlcA): the families a run consumed; the hold-out rule ----------
def _stale_splits(tmp_path):
    """Targets for a vault whose stored rows carry splits from before the current hold-out: the
    held-out family's rows were stored as training rows (generated while it was the only family),
    and one other family's rows as held-out (an earlier hold-out)."""

    paths, repository, root, model, space, bank = _targets(tmp_path)
    vault = loaded(paths)
    directory = D.data_dir(root, space, vault)
    rows = D.stored_queries(directory)
    held = {row["family"] for row in rows if row["split"] == "heldout"}
    assert len(held) == 1
    (family,) = held
    other = sorted({row["family"] for row in rows} - held)[0]
    stale = [{**row, "split": "train"} if row["family"] == family else
             {**row, "split": "heldout"} if row["family"] == other else row for row in rows]
    (directory / "queries.jsonl").write_text("".join(json.dumps(row) + "\n" for row in stale), encoding="utf-8")
    return paths, repository, root, model, space, bank, family, other, rows


def test_a_newly_held_out_familys_older_rows_leave_training(tmp_path):
    """Spec §7 (splits by source family: a held-out family is NEVER trained on): a row's split is
    re-derived from the vault's current hold-out when a dataset is built, so rows stored as
    training rows before their family was held out leave training (and the development split),
    and rows of a family no longer held out take their passage's split."""

    paths, repository, root, _model, space, bank, family, other, original = _stale_splits(tmp_path)
    vault = loaded(paths)
    camp = Q.campaign(vault, repository, root=root, space=space, bank=D.load_bank(bank))
    assert camp["rows"] and all(row["split"] == "heldout" for row in camp["rows"] if row["family"] == family)
    assert family not in camp["candidates"]["families"]
    expected = {row["id"]: row["split"] for row in original}
    assert all(row["split"] == expected[row["id"]] for row in camp["rows"] if row["family"] == other)
    data = tmp_path / "data"
    Q.build_dataset(vault, repository, root=root, space=space, budget=max(SP.BUDGETS), bank_path=bank, out_dir=data,
                    camp=camp)
    held_texts = {row["text"] for row in original if row["family"] == family}
    for split in ("train", "dev"):
        assert held_texts.isdisjoint(json.loads((data / f"{split}_texts.json").read_text()))
    # The doctor's view counts the splits a dataset would use now.
    by_split = Q.status(vault, repository, root=root)["questions"]["by_split"]
    assert by_split == {split: sum(1 for row in original if row["split"] == split)
                        for split in ("train", "dev", "heldout")}


def test_the_pinned_families_are_every_family_the_run_consumed(tmp_path):
    """F19 reopened: the checkpoint pins the families of the queries the trainer consumed (its
    nested training budget and development split) and of the candidate blocks its top-k, positives
    and hard negatives come from; the current-dataset fallback derives the same set."""

    paths, repository, root, _model, space, bank, _family, _other, _original = _stale_splits(tmp_path)
    vault = loaded(paths)
    camp = Q.campaign(vault, repository, root=root, space=space, bank=D.load_bank(bank))
    budget = max(SP.BUDGETS)
    data = tmp_path / "data"
    stats = Q.build_dataset(vault, repository, root=root, space=space, budget=budget, bank_path=bank, out_dir=data,
                            camp=camp)
    texts = set(json.loads((data / "train_texts.json").read_text())) | \
        set(json.loads((data / "dev_texts.json").read_text()))
    consumed = {row["family"] for row in camp["rows"] if row["text"] in texts} | \
        {camp["by_extraction"][source] for source in camp["candidates"]["sources"]}
    assert consumed and consumed <= set(stats["training_families"])
    assert stats["training_families"] == Q.run_training_families(camp, budget)
    trainer = InProcessTrainer(fail=True)  # records the job; no torch, no training
    Q.run_next(vault, repository, bank_path=bank, launcher=trainer, preflight=lambda: [], locks=no_locks)
    (job,) = trainer.jobs
    assert job["training_families"] == Q.run_training_families(camp, int(job["budget"]))
    run = {"checkpoint_sha256": "d" * 64, "spec": {"dataset": camp["fingerprint"], "budget": int(job["budget"])}}
    fallback, basis = Q.checkpoint_training_families(run, camp, root=root, space=space)
    assert basis == "current_dataset" and fallback == set(job["training_families"])


# -- F19 residual and F20 (scoped verify 20261026-153448-dFvUTA) -------------------------------------------------
def test_only_the_current_producers_pinned_families_are_provenance(tmp_path):
    """F19 residual: a pinned list without the current producer's provenance version (the first
    F19 round pinned candidate families only, which could omit consumed ones) is not trusted: the
    evaluation falls back to the current dataset, else to ``unknown_family``."""

    from learnloop.local_embeddings import student_trainer

    paths, repository, root, model, space, bank, _sha = _evaluable(tmp_path)
    vault = loaded(paths)
    factory = lambda _sha: _TeacherEncoder(model)  # noqa: E731
    camp = Q.campaign(vault, repository, root=root, space=space, bank=D.load_bank(bank))
    first_round = _pinned_run(root, space, families={"another-family"}, dataset="old-dataset", run_id="run_r1",
                              provenance=None)
    out = Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory, checkpoint=first_round)
    assert out["training_families"]["basis"] == "unknown" and "unseen_family" not in out["strata"], out["strata"]
    older = _pinned_run(root, space, families={"another-family"}, dataset="old-dataset", run_id="run_r0",
                        provenance="candidate-families-v0")
    assert Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory,
                      checkpoint=older)["training_families"]["basis"] == "unknown"
    here = _pinned_run(root, space, families={"another-family"}, dataset=camp["fingerprint"], run_id="run_here",
                       provenance=None)
    assert Q.evaluate(vault, repository, bank_path=bank, encoder_factory=factory,
                      checkpoint=here)["training_families"]["basis"] == "current_dataset"
    # The version is pinned with the list: changing it breaks the pin.
    job = Q.trainer_job({"base": SP.PRIMARY_BASE, "recipe": "align", "budget": 100, "seed": 0}, space="s",
                        base_dir=Path("/b"), data_dir=Path("/d"), out_dir=Path("/o"), temperature=0.1, plan_id="p",
                        training_families=["a"])
    assert job["training_families_provenance"] == Q.TRAINING_FAMILIES_PROVENANCE
    manifest = json.loads((E.checkpoint_dir(root, space, here) / "student.json").read_text())
    pinned = {**manifest, "training_families_provenance": Q.TRAINING_FAMILIES_PROVENANCE}
    assert student_trainer.checkpoint_digest(pinned) != student_trainer.checkpoint_digest(
        {**pinned, "training_families_provenance": "other"})


def test_generation_counts_its_budget_by_the_current_splits(tmp_path):
    """F20: generation's progress and remaining budget count the rows' CURRENT splits (the same
    hold-out every dataset build uses): a family's stale training rows, held out since, never fill
    the budget, so owed training passages of the other families are still planned."""

    paths, repository, root, _model, space, bank = _generated(tmp_path)
    vault = loaded(paths)
    directory = D.data_dir(root, space, vault)
    rows = D.stored_queries(directory)
    held = {row["family"] for row in rows if row["split"] == "heldout"}
    assert len(held) == 1
    owed = next(row["passage"] for row in rows if row["split"] == "train")
    stale = [{**row, "split": "train"} if row["family"] in held else row for row in rows if row["passage"] != owed]
    (directory / "queries.jsonl").write_text("".join(json.dumps(row) + "\n" for row in stale), encoding="utf-8")
    done = [json.loads(line) for line in (directory / "passages.jsonl").read_text().splitlines() if line.strip()]
    (directory / "passages.jsonl").write_text("".join(json.dumps(row) + "\n" for row in done if row["key"] != owed),
                                              encoding="utf-8")
    current_train = sum(1 for row in stale if row["split"] == "train" and row["family"] not in held)
    budget = sum(1 for row in stale if row["split"] == "train")  # what the stale labels claim
    assert budget > current_train
    out = D.generate(vault, repository, space_id=space, bank_path=bank, budget=budget, dry_run=True)
    assert out["questions"]["train"] == current_train
    assert out["passages"]["owed"] == 1 and out["passages"]["planned"] == 1 and out["calls"] == 1, out
