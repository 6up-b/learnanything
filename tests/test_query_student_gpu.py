"""Local retrieval P2: a GPU smoke test of the query-student trainer with a TINY random-initialised
model (no download, no real base, no book text). Skipped unless LEARNLOOP_GPU_SMOKE=1, and even then
only when the exclusive GPU lock is free and the student's memory floors hold (spec §7.2): the
lock is taken non-blocking and held for the run, never broken."""
from __future__ import annotations

import json
import os

import numpy as np
import pytest

from learnloop.local_embeddings import student_pins as SP
from learnloop.local_embeddings import worker
from learnloop.local_embeddings.launcher import LocksBusy, gpu_lock_path, gpu_locks

pytestmark = pytest.mark.gpu_smoke


def test_a_tiny_student_trains_on_the_gpu_under_the_lock_and_the_floors(tmp_path):
    if os.environ.get("LEARNLOOP_GPU_SMOKE") != "1":
        pytest.skip("set LEARNLOOP_GPU_SMOKE=1 to run the GPU smoke test")
    torch = pytest.importorskip("torch", reason="torch is absent (the pdf extra)")
    if not torch.cuda.is_available():
        pytest.skip("no CUDA device")
    available = worker.read_meminfo().get("MemAvailable", 0)
    state = worker.gpu_state()
    if available < SP.SERVE_MIN_HOST_AVAILABLE_GIB * worker.GIB or state["free_mib"] < SP.SERVE_MIN_FREE_VRAM_GIB * 1024:
        pytest.skip("below the student's memory floors (MemAvailable >= 6 GiB, free VRAM >= 4 GiB)")
    from learnloop.local_embeddings import student_trainer
    from tests.query_student_fakes import tiny_factory

    rng = np.random.default_rng(0)
    data = tmp_path / "data"
    data.mkdir()
    documents = rng.standard_normal((64, SP.STUDENT_DIMENSIONS)).astype(np.float16)
    np.save(data / "documents.npy", documents)
    for split, n in (("train", 128), ("dev", 32)):
        targets = documents[rng.integers(0, 64, n)].astype(np.float32) + 0.1 * rng.standard_normal(
            (n, SP.STUDENT_DIMENSIONS)).astype(np.float32)
        np.save(data / f"{split}_targets.npy", targets.astype(np.float16))
        scores = targets @ documents.astype(np.float32).T
        np.save(data / f"{split}_topk.npy", np.argsort(-scores, axis=1)[:, :16].astype(np.int32))
        (data / f"{split}_positives.json").write_text(json.dumps([[int(np.argmax(row))] for row in scores]))
        (data / f"{split}_texts.json").write_text(json.dumps([f"synthetic query {split} {i}" for i in range(n)]))
    job = {"seed": 0, "base": {**SP.STUDENT_BASES[SP.PRIMARY_BASE]}, "base_name": SP.PRIMARY_BASE,
           "base_dir": str(tmp_path), "data_dir": str(data), "out_dir": str(tmp_path / "out"),
           "recipe": "align_kd_mp", "budget": 128, "dimensions": SP.STUDENT_DIMENSIONS,
           "precision": SP.STUDENT_PRECISION, "max_query_tokens": SP.MAX_QUERY_TOKENS, "epochs": 2,
           "batch_size": 32, "learning_rate_full": 1e-3, "learning_rate_head": 1e-3, "weight_decay": 0.0,
           "warmup_fraction": 0.1, "grad_clip_norm": 1.0, "temperature": 0.05, "agreement_k": 10,
           "latency_probes": 8, "canary_queries": list(SP.STUDENT_CANARY_QUERIES),
           "checkpoint_format": SP.CHECKPOINT_FORMAT, "space_id": "ls_smoke"}
    try:
        with gpu_locks((gpu_lock_path(),)):
            torch.zeros(1, device="cuda:0")
            torch.cuda.reset_peak_memory_stats(0)
            output = student_trainer.run_training(job, model_factory=tiny_factory, device="cuda:0",
                                                  base_check=lambda _job: [])
            peak = torch.cuda.max_memory_reserved(0)
    except LocksBusy:
        pytest.skip("another GPU job holds the exclusive lock")
    assert output["status"] == "complete", output
    assert set(output["latency"]) == {"device", "cpu"}
    manifest = json.loads((tmp_path / "out" / "checkpoint" / "student.json").read_text())
    assert set(manifest["canaries"]) == {"gpu", "cpu"}
    assert peak < SP.SERVE_MIN_FREE_VRAM_GIB * worker.GIB
    print(json.dumps({"train_s": output["train_s"], "steps": output["steps"], "peak_reserved_mib": peak // 2**20,
                      "latency_gpu_p50_s": output["latency"]["device"]["p50_s"],
                      "latency_cpu_p50_s": output["latency"]["cpu"]["p50_s"]}))
