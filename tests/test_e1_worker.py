"""The E1 worker with a fake model: start guards, smoke, profiling, encoding,
aborts, unload. No torch, no GPU, no download, no network."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import socket
import subprocess
import sys

import pytest

from learnloop.experiments.contextual_embeddings.e1 import pins as e1_pins
from learnloop.experiments.contextual_embeddings.e1 import worker
from learnloop.experiments.contextual_embeddings.e1.local import limits
from tests.e1_fakes import GIB, HEALTHY_GPU, HEALTHY_MEMINFO, HEALTHY_SCOPE, FakeV2Model, run_fake_job

WORKER = Path(worker.__file__)


def _job(**changes):
    job = {
        "version": worker.WORKER_VERSION, "plan_id": "e1_0000000000000000", "model_dir": "/nonexistent",
        "model_files": {}, "remote_code": [], "precision": "bf16", "attention": "sdpa",
        "fp32_modules": ["contextual_projection"], "dimensions": 2048,
        "max_document_tokens": e1_pins.MAX_DOCUMENT_TOKENS, "index_batch_size": 1, "query_batch_size": 1,
        "batch_invariance_min_cos": e1_pins.BATCH_INVARIANCE_MIN_COS,
        "context_max_cos": e1_pins.CONTEXT_SENSITIVITY_MAX_COS,
        "smoke": {"context": e1_pins.SMOKE_CONTEXT, "query": e1_pins.SMOKE_QUERY,
                  "padding_document": e1_pins.SMOKE_PADDING_DOCUMENT},
        "profile": {"2048": ["word " * 1600], "4096": ["word " * 3300], "8192": ["word " * 6600]},
        "profile_repeats": 2,
        "documents": [{"id": "d1", "chunks": [{"id": "c1", "text": "A vector space."},
                                              {"id": "c2", "text": "A basis spans it."}]},
                      {"id": "big", "chunks": [{"id": "c3", "text": "word " * 40_000}]}],
        "queries": [{"id": "q1", "text": "What is a basis?"}],
        "limits": limits(deadline_unix=None) | {"sample_interval_s": 60.0},
    }
    job.update(changes)
    return job


def test_the_worker_module_is_standalone_and_runs_with_an_isolated_interpreter():
    tree = ast.parse(WORKER.read_text(encoding="utf-8"))
    top = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    names = {alias.name.split(".")[0] for node in top for alias in node.names} | {
        (node.module or "").split(".")[0] for node in top if isinstance(node, ast.ImportFrom)}
    assert not names & {"torch", "transformers", "learnloop", "safetensors"}
    result = subprocess.run([sys.executable, "-I", str(WORKER), "--help"], capture_output=True, text=True,
                            timeout=60, cwd="/")
    assert result.returncode == 0 and "--heartbeat" in result.stdout


def test_a_complete_job_runs_every_smoke_check_and_stores_int8_rows_without_truncation():
    model = FakeV2Model()
    output = run_fake_job(_job(), model)
    assert output["status"] == "complete", output["reason"]
    smoke = output["smoke"]
    assert smoke["all_ok"] and {"dims_and_order", "context_sensitive", "methods_separate", "decoding",
                                "finite_nonzero", "padding_batch_invariance", "deterministic",
                                "no_truncation"} <= set(smoke)
    rows = output["documents"]["d1"]["vectors"]
    assert len(rows) == 2 and len(rows[0]) == 2048 and all(isinstance(value, int) for value in rows[0])
    # An over-limit document is refused, never truncated.
    assert output["documents"]["big"] == {"error": "over_limit", "tokens": model.count_tokens(["word " * 40_000])}
    assert len(output["queries"]["q1"]["vector"]) == 2048 and output["queries"]["q1"]["latency_s"] >= 0
    assert [output["profile"][size]["oom"] for size in ("2048", "4096", "8192")] == [False, False, False]
    assert output["unload"]["complete"] and model.unloaded
    assert output["peaks"]["samples"] >= 2 and output["peaks"]["host_available_min"] == HEALTHY_MEMINFO["MemAvailable"]


@pytest.mark.parametrize("changes, expected", [
    ({"meminfo": lambda: {"MemAvailable": 8 * GIB}}, "MemAvailable"),
    ({"gpu": lambda: HEALTHY_GPU | {"free_mib": 12_000}}, "free VRAM"),
    ({"gpu": lambda: HEALTHY_GPU | {"processes": [{"pid": 999_999, "used_mib": 9_000}]}}, "other GPU compute"),
    ({"gpu": lambda: HEALTHY_GPU | {"utilization_pct": 80}}, "utilization"),
    ({"scope": lambda: HEALTHY_SCOPE | {"scope": False}}, "systemd scope"),
    ({"scope": lambda: HEALTHY_SCOPE | {"memory_max": None}}, "memory.max"),
    ({"scope": lambda: HEALTHY_SCOPE | {"memory_max": 40 * GIB}}, "exceeds the plan"),
    ({"scope": lambda: HEALTHY_SCOPE | {"swap_max": None}}, "swap"),
    ({"model_check": lambda _job: ["modeling_pplx_contextual.py: SHA-256 differs from the pinned digest"]},
     "SHA-256"),
])
def test_the_worker_refuses_to_load_unless_every_start_condition_holds(changes, expected):
    model = FakeV2Model()
    loads = []
    output = run_fake_job(_job(), model, model_factory=lambda *_a: loads.append(1) or model, **changes)
    assert output["status"] == "refused" and expected in output["reason"]
    assert loads == [] and output["documents"] == {}


def test_a_spent_gpu_allowance_refuses_the_start():
    output = run_fake_job(_job(limits=limits(deadline_unix=1.0)), FakeV2Model())
    assert output["status"] == "refused" and "GPU-hours" in output["reason"]


def test_a_failed_smoke_check_indexes_nothing():
    for model, check in ((FakeV2Model(contextual=False), "context_sensitive"),
                         (FakeV2Model(query_like_document=True), "methods_separate")):
        output = run_fake_job(_job(), model)
        assert output["status"] == "aborted" and not output["smoke"][check]["ok"]
        assert output["documents"] == {} and output["queries"] == {} and output["unload"]["complete"]


def test_an_oom_while_profiling_stops_the_larger_sizes_and_counts():
    output = run_fake_job(_job(), FakeV2Model(oom_at=3000))
    profile = output["profile"]
    assert profile["2048"]["oom"] is False and profile["4096"]["oom"] is True
    assert profile["8192"] == {"skipped": "oom at 4096"}
    assert output["status"] == "complete"


class SlowModel(FakeV2Model):
    def encode_documents(self, documents, *, batch_size=1):
        import time

        time.sleep(0.02)
        return super().encode_documents(documents, batch_size=batch_size)


def test_the_sampler_aborts_below_the_host_floor_and_keeps_partial_results():
    readings = iter([HEALTHY_MEMINFO] * 3 + [{"MemAvailable": 1 * GIB}] * 100_000)
    documents = [{"id": f"d{index}", "chunks": [{"id": "c", "text": f"passage {index}"}]} for index in range(200)]
    job = _job(documents=documents, limits=limits(deadline_unix=None) | {"sample_interval_s": 0.005})
    output = run_fake_job(job, SlowModel(), meminfo=lambda: next(readings))
    assert output["status"] == "aborted" and "host MemAvailable" in output["reason"]
    assert output["peaks"]["host_available_min"] == 1 * GIB
    assert len(output["documents"]) < 200 and output["unload"]["complete"]


def test_scope_and_meminfo_probes_read_cgroup_v2(tmp_path):
    scope = tmp_path / "user.slice" / "run-x.scope"
    scope.mkdir(parents=True)
    (scope / "memory.max").write_text("12884901888\n")
    (scope / "memory.swap.max").write_text("0\n")
    (scope / "memory.peak").write_text("1000\n")
    found = worker.scope_limits(cgroup_text="0::/user.slice/run-x.scope\n", root=tmp_path)
    assert found["scope"] and found["memory_max"] == 12 * GIB and found["swap_max"] == 0 and found["memory_peak"] == 1000
    (scope / "memory.max").write_text("max\n")
    assert worker.scope_limits(cgroup_text="0::/user.slice/run-x.scope\n", root=tmp_path)["memory_max"] is None
    assert worker.read_meminfo("MemTotal: 2048 kB\nMemAvailable: 1024 kB\n") == {"MemTotal": 2097152,
                                                                                  "MemAvailable": 1048576}


def test_gpu_state_parses_nvidia_smi():
    def run(arguments):
        if any("query-gpu" in item for item in arguments):
            return "NVIDIA GeForce RTX 5090, 615.78.08, 32607, 2200, 30407, 3\n"
        return "4242, 1800\n"

    state = worker.gpu_state(run)
    assert state["free_mib"] == 30407 and state["utilization_pct"] == 3
    assert state["processes"] == [{"pid": 4242, "used_mib": 1800}]


def test_model_files_are_checked_by_size_and_the_remote_code_by_digest(tmp_path):
    code = b"class PplxContextualModel: pass\n"
    (tmp_path / "modeling_pplx_contextual.py").write_bytes(code)
    (tmp_path / "model-00001.safetensors").write_bytes(b"x" * 10)
    import hashlib

    files = {"modeling_pplx_contextual.py": (len(code), hashlib.sha256(code).hexdigest()),
             "model-00001.safetensors": (10, hashlib.sha256(b"x" * 10).hexdigest())}
    assert worker.model_dir_problems(tmp_path, files, ["modeling_pplx_contextual.py"]) == []
    (tmp_path / "modeling_pplx_contextual.py").write_bytes(code.replace(b"pass", b"None"))
    assert "SHA-256 differs" in worker.model_dir_problems(tmp_path, files, ["modeling_pplx_contextual.py"])[0]
    (tmp_path / "modeling_pplx_contextual.py").write_bytes(code)
    (tmp_path / "evil.py").write_text("import os")
    assert any("unreviewed" in item for item in worker.model_dir_problems(tmp_path, files,
                                                                          ["modeling_pplx_contextual.py"]))
    (tmp_path / "evil.py").unlink()
    (tmp_path / "model-00001.safetensors").write_bytes(b"x" * 9)
    assert "size 9" in worker.model_dir_problems(tmp_path, files, ["modeling_pplx_contextual.py"])[0]


def test_the_pinned_remote_code_digests_are_the_reviewed_files():
    assert set(e1_pins.REMOTE_CODE_FILES) <= set(e1_pins.MODEL_FILES)
    assert e1_pins.MODEL_DISK_BYTES > 33_600_000_000
    shards = [name for name in e1_pins.MODEL_FILES if name.startswith("model-")]
    assert len(shards) == 7 and all(len(e1_pins.MODEL_FILES[name][1]) == 64 for name in e1_pins.MODEL_FILES)


def test_the_network_guard_refuses_inet_connections(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", socket.socket.connect)
    monkeypatch.setattr(socket, "create_connection", socket.create_connection)
    worker._guard_network()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock, pytest.raises(ConnectionRefusedError):
        sock.connect(("127.0.0.1", 9))
    with pytest.raises(ConnectionRefusedError):
        socket.create_connection(("127.0.0.1", 9))


def test_main_writes_its_output_and_a_heartbeat(tmp_path, monkeypatch):
    job_path = tmp_path / "job.json"
    job_path.write_text(json.dumps(_job()))
    monkeypatch.setattr(socket.socket, "connect", socket.socket.connect)
    monkeypatch.setattr(socket, "create_connection", socket.create_connection)
    for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "HF_HOME", "HF_MODULES_CACHE",
                 "TOKENIZERS_PARALLELISM", "PYTORCH_CUDA_ALLOC_CONF"):
        monkeypatch.delenv(name, raising=False)
    model = FakeV2Model()
    real = worker.run_job
    monkeypatch.setattr(worker, "run_job", lambda job, **kwargs: real(
        job, **kwargs, model_factory=lambda *_a: model, meminfo=lambda: HEALTHY_MEMINFO, scope=lambda: HEALTHY_SCOPE,
        gpu=lambda: HEALTHY_GPU, model_check=lambda _job: []))
    code = worker.main(["--job", str(job_path), "--out", str(tmp_path / "out.json"),
                        "--heartbeat", str(tmp_path / "hb.json")])
    assert code == 0 and json.loads((tmp_path / "out.json").read_text())["status"] == "complete"
    assert json.loads((tmp_path / "hb.json").read_text())["step"] in ("unload", "encode", "profile", "smoke")
    import os

    assert os.environ["HF_HUB_OFFLINE"] == "1" and os.environ["HF_MODULES_CACHE"].startswith(str(tmp_path))
