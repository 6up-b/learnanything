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
    student_vault,
    thread_spawn,
    write_bank,
)
from tests.source_retrieval_fakes import HashingEmbedder, loaded


@pytest.fixture(autouse=True)
def _fresh(monkeypatch, tmp_path):
    clear_cache()
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    # A Unix socket path is at most 107 bytes: the runtime directory is a short temporary one.
    short = Path(tempfile.mkdtemp(prefix="llq"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(short))
    E._ENCODERS.clear()
    yield short
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
    ids, _matrix = Q.documents(loaded(paths), repository, space, exclude={("ext_book", gold)})
    assert stats["documents"] == len(ids) and not any(gold in record for record in ids)
    job = Q.trainer_job({"base": SP.PRIMARY_BASE, "recipe": recipe, "budget": 50_000, "seed": 0}, space=space,
                        base_dir=tmp_path, data_dir=data, out_dir=tmp_path / "out", temperature=stats["temperature"],
                        plan_id="t")
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
    paths, repository, root, model, space, bank = _targets(tmp_path)
    vault = loaded(paths)
    trainer = InProcessTrainer()
    for _ in range(12):
        out = Q.run_next(vault, repository, bank_path=bank, launcher=trainer, preflight=lambda: [], locks=no_locks)
        if out["status"] != "trained":
            break
    assert out["status"] == "evaluate", out
    return paths, repository, root, model, space, bank, out


def _bank_targets(paths, repository, model, bank):
    out = Q.run_targets(loaded(paths), repository, bank_path=bank, launcher=InProcessLauncher(model),
                        preflight=lambda: [], locks=no_locks)
    assert out["status"] == "complete", out


def test_a_student_that_matches_its_teacher_is_adopted_and_one_that_misses_is_not(torch_present, tmp_path):
    paths, repository, root, model, space, _bank, _out = _trained(tmp_path)
    vault = loaded(paths)
    good = _bank_for(paths, repository, model, space, good=True, tmp_path=tmp_path)
    _bank_targets(paths, repository, model, good)

    class Encoder:
        def encode(self, texts, *, deadline=None):
            return TeacherService(model).encode(texts)

    adopted = Q.evaluate(vault, repository, bank_path=good, encoder_factory=lambda _sha: Encoder())
    assert adopted["status"] == "adopted", adopted
    assert adopted["decision"]["chosen"] == "student" and set(adopted["decision"]["p_best"]) >= {"student", "qwen"}
    assert adopted["strata"]["all"]["p_student_ge_teacher"] > 0.3
    record = E.read_adoption(root, space)
    assert record["checkpoint_sha256"] == _out["step"]["checkpoint_sha256"]
    assert Q.revoke(vault)["status"] == "revoked" and E.read_adoption(root, space) is None
    bad = _bank_for(paths, repository, model, space, good=False, tmp_path=tmp_path)
    _bank_targets(paths, repository, model, bad)
    refused = Q.evaluate(vault, repository, bank_path=bad, encoder_factory=lambda _sha: Encoder())
    assert refused["status"] == "not_adopted" and E.read_adoption(root, space) is None


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
