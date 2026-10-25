"""Local contextual retrieval P0/P1a: the moved worker, the true-token profile,
the launcher's scope and locks, the meter, setup and the index job (fakes only:
no process, no GPU, no download)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from learnloop.db.connection import connect
from learnloop.db.stores.retrieval_spaces import spaces
from learnloop.local_embeddings import launcher, pins, setup, worker
from learnloop.local_embeddings.cache import VectorCache, cache_path
from learnloop.local_embeddings.gpu_meter import GpuBudgetExceeded, GpuMeter
from learnloop.source_retrieval import local_index
from tests.helpers import append_config_toml
from tests.local_embeddings_fakes import (
    FakeLocalModel,
    InProcessLauncher,
    no_locks,
    run_fake_job,
    set_up_data_root,
)
from tests.source_retrieval_fakes import build_retrieval_vault, loaded


@pytest.fixture
def data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    root = pins.data_root()
    root.mkdir(parents=True)
    return root


def _local_vault(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    append_config_toml(paths.root, "[embedding.local]\nenabled = true\n")
    return paths, repository


def test_the_moved_pins_equal_e1s():
    from learnloop.experiments.contextual_embeddings.e1 import pins as e1

    for name in ("MODEL_REPO", "MODEL_REVISION", "MODEL_DIMENSIONS", "MODEL_FILES", "REMOTE_CODE_FILES",
                 "LOCAL_PYTHON", "LOCAL_REQUIREMENTS", "PRECISION", "ATTENTION_IMPLEMENTATION", "FP32_MODULES",
                 "SCOPE_MEMORY_MAX", "SCOPE_SWAP_MAX", "SCOPE_MEMORY_MAX_BYTES", "MIN_HOST_AVAILABLE_GIB",
                 "MIN_FREE_VRAM_GIB", "MAX_OTHER_GPU_PROCESS_MIB", "MAX_OTHER_GPU_TOTAL_MIB",
                 "FORBIDDEN_GPU_WORKLOADS", "MAX_GPU_UTILIZATION_PCT", "HOST_FLOOR_GIB", "DEVICE_PEAK_TARGET_GIB",
                 "MAX_DOCUMENT_TOKENS", "BATCH_INVARIANCE_MIN_COS", "CONTEXT_SENSITIVITY_MAX_COS",
                 "SMOKE_CONTEXT", "SMOKE_QUERY", "PROFILE_TOKENS", "PROFILE_REPEATS", "DOWNLOAD_FREE_DISK_GIB"):
        assert getattr(pins, name) == getattr(e1, name), name
    from learnloop.source_retrieval import windows

    assert windows.MAX_DOCUMENT_TOKENS == pins.MAX_DOCUMENT_TOKENS


def test_the_production_worker_imports_only_the_standard_library_and_numpy():
    import ast

    tree = ast.parse(Path(worker.__file__).read_text(encoding="utf-8"))
    top = {alias.name.split(".")[0] for node in tree.body if isinstance(node, ast.Import) for alias in node.names}
    top |= {node.module.split(".")[0] for node in tree.body if isinstance(node, ast.ImportFrom) and node.module}
    assert top <= {"__future__", "argparse", "collections", "gc", "hashlib", "json", "os", "pathlib", "platform",
                   "socket", "subprocess", "sys", "threading", "time", "traceback", "typing", "numpy"}


def test_the_profile_is_fitted_to_the_true_token_count():
    model = FakeLocalModel()
    pool = [f"sentence number {index} has seven words" for index in range(100)]
    chunks, tokens = worker.fit_window(model, pool, 200)
    assert tokens == model.count_tokens(chunks) and 195 <= tokens <= 200  # within one word of the target
    job = {"profile": {"200": {"pool": pool, "target": 200}, "100": pool[:3]}, "profile_repeats": 1,
           "max_document_tokens": 8192}
    result = worker.profile(model, job)
    assert result["200"]["fitted"] and result["200"]["target"] == 200 and 195 <= result["200"]["tokens"] <= 200
    assert "fitted" not in result["100"]  # a list is profiled as given (E1's form)


def test_the_profile_pools_hold_teaching_text_only(tmp_path):
    paths, repository = _local_vault(tmp_path)
    pools = local_index.profile_pools(loaded(paths), repository, "ext_book", (50,))
    assert pools["50"]["target"] == 50 and pools["50"]["pool"]
    assert local_index.profile_pools(loaded(paths), repository, "ext_exam", (50,))["50"]["pool"] == []


def test_the_worker_encodes_the_canaries_with_every_batch():
    job, _targets = local_index.build_job([], manifest={"model_dir": "/x"}, plan_id="local_0")
    output = run_fake_job(job, FakeLocalModel())
    assert output["status"] == "complete", output.get("reason")
    canaries = output["canaries"]
    assert len(canaries["documents"]) == len(pins.CANARY_DOCUMENTS) and len(canaries["queries"]) == len(pins.CANARY_QUERIES)
    assert local_index.canary_check(canaries, canaries)["ok"]
    drifted = run_fake_job(job, FakeLocalModel(salt="other"))["canaries"]
    assert not local_index.canary_check(drifted, canaries)["ok"]


def test_the_worker_runs_in_its_own_capped_scope_and_the_locks_are_never_broken(tmp_path):
    command = launcher.scope_command(Path("/env/bin/python"), Path("j"), Path("o"), Path("h"), unit="u")
    assert command[:4] == ["systemd-run", "--user", "--scope", "--quiet"]
    assert "MemoryMax=12G" in command and "MemorySwapMax=0" in command
    assert command[command.index("--") + 1:command.index("--") + 3] == ["/env/bin/python", "-I"]
    assert Path(command[command.index("--") + 3]) == Path(worker.__file__).resolve()
    locks = (tmp_path / "gpu.lock", tmp_path / "suite.lock")
    with launcher.gpu_locks(locks):
        with pytest.raises(launcher.LocksBusy):
            with launcher.gpu_locks(locks):
                pass
    with launcher.gpu_locks(locks):  # released after the block
        pass


def test_the_meter_meters_production_uncapped_and_refuses_a_second_live_worker(tmp_path):
    meter = GpuMeter(tmp_path / "meter")
    entry, deadline = meter.open(plan_id="p", label="a", min_slot_s=0)
    assert deadline is None
    with pytest.raises(GpuBudgetExceeded):
        meter.open(plan_id="p", label="b", min_slot_s=0)
    meter.close(entry, status="exited", returncode=0)
    assert meter.report()["cap_hours"] is None and meter.report()["processes"] == 1
    capped = GpuMeter(tmp_path / "capped", cap_hours=0.1)
    with pytest.raises(GpuBudgetExceeded):
        capped.open(plan_id="p", label="c")  # below the 15-minute minimum slot


def _fake_setup_runner(files, *, fail_install=False, partial_download=False):
    """A fake ``subprocess.run`` for setup: ``uv venv`` makes the interpreter,
    ``uv pip install`` installs the pins (or fails), the package probe
    reports what is installed, the download writes the files (only the
    first one when ``partial_download``), the epoch probe reports E1's epoch."""

    calls: list[list[str]] = []
    state = {"installed": False, "fail_install": fail_install, "partial": partial_download}

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        joined = " ".join(command)
        stdout = json.dumps({"torch": "2.14.0+cu130", "transformers": "5.18.0", "cuda": "13.0"})
        if command[:2] == ["uv", "venv"]:
            python = Path(command[-1]) / "bin" / "python"
            python.parent.mkdir(parents=True, exist_ok=True)
            python.write_text("", encoding="utf-8")
        elif command[:3] == ["uv", "pip", "install"]:
            if state["fail_install"]:
                return SimpleNamespace(returncode=1, stdout="")
            state["installed"] = True
        elif "metadata" in joined:
            names = command[4:]
            versions = dict(requirement.split("==", 1) for requirement in pins.LOCAL_REQUIREMENTS)
            stdout = json.dumps({name: (versions[name] + ("+cu130" if name == "torch" else ""))
                                 if state["installed"] else None for name in names})
        elif "snapshot_download" in joined:
            target = Path(command[-1])
            target.mkdir(parents=True, exist_ok=True)
            for index, (name, body) in enumerate(files.items()):
                if state["partial"] and index > 0:
                    break
                (target / name).write_bytes(body)
        return SimpleNamespace(returncode=0, stdout=stdout)

    return calls, fake_run, state


def test_an_interrupted_setup_resumes_the_install_and_the_download(tmp_path, monkeypatch):
    """Codex review F16: a path that exists is not a finished step."""

    files = {"config.json": b"{}", "configuration_pplx_contextual.py": b"# reviewed\n",
             "modeling_pplx_contextual.py": b"# reviewed too\n"}
    monkeypatch.setattr(pins, "MODEL_FILES", {name: (len(body), hashlib.sha256(body).hexdigest())
                                              for name, body in files.items()})
    root = tmp_path / "data"
    calls, fake_run, state = _fake_setup_runner(files, fail_install=True, partial_download=True)
    with pytest.raises(RuntimeError, match="failed"):
        setup.run_setup(root=root, run=fake_run, disk_free=lambda _p: 100 * 1024 ** 3)
    assert Path(setup.setup_plan(root)["env_python"]).exists()  # the interpreter was left behind
    state["fail_install"] = False
    with pytest.raises(RuntimeError, match="does not match the pins"):
        setup.run_setup(root=root, run=fake_run, disk_free=lambda _p: 100 * 1024 ** 3)  # the download stops short
    assert state["installed"]  # the rerun installed into the existing interpreter
    assert [command[:3] for command in calls].count(["uv", "pip", "install"]) == 2
    state["partial"] = False
    calls.clear()
    report = setup.run_setup(root=root, run=fake_run, disk_free=lambda _p: 100 * 1024 ** 3)
    assert report["status"] == "ready" and "model downloaded" in report["steps"]
    assert ["uv", "venv"] not in [command[:2] for command in calls]  # nothing redone that was done
    assert ["uv", "pip", "install"] not in [command[:3] for command in calls]
    # Done: a rerun downloads nothing and installs nothing.
    calls.clear()
    again = setup.run_setup(root=root, run=fake_run, disk_free=lambda _p: 1)
    assert again["steps"] == ["already present"] and not any("snapshot_download" in " ".join(c) for c in calls)


def test_setup_verifies_the_files_records_the_epoch_and_adopts_without_moving(tmp_path, monkeypatch):
    files = {"config.json": b"{}", "configuration_pplx_contextual.py": b"# reviewed\n",
             "modeling_pplx_contextual.py": b"# reviewed too\n"}
    monkeypatch.setattr(pins, "MODEL_FILES", {name: (len(body), hashlib.sha256(body).hexdigest())
                                              for name, body in files.items()})
    root = tmp_path / "data"
    calls, fake_run, _state = _fake_setup_runner(files)

    report = setup.run_setup(root=root, run=fake_run, disk_free=lambda _p: 100 * 1024 ** 3)
    assert report["status"] == "ready" and report["software_epoch"]["torch"] == "2.14.0+cu130"
    assert [command[:2] for command in calls if command[0] == "uv"] == [["uv", "venv"], ["uv", "pip"]]
    manifest, reason = setup.load_manifest(root)
    assert reason is None and manifest["revision"] == pins.MODEL_REVISION
    # A wrong file is refused before anything is recorded.
    (Path(manifest["model_dir"]) / "modeling_pplx_contextual.py").write_bytes(b"# changed\n")
    with pytest.raises(RuntimeError, match="does not match the pins"):
        setup.run_setup(root=tmp_path / "other", run=fake_run, adopt_model_dir=Path(manifest["model_dir"]),
                        adopt_env_python=Path(manifest["env_python"]))
    # Not enough disk: refused before any process.
    calls.clear()
    with pytest.raises(RuntimeError, match="GiB free"):
        setup.run_setup(root=tmp_path / "small", run=fake_run, disk_free=lambda _p: 1)
    assert calls == []


def test_the_index_job_caches_both_variants_and_registers_the_spaces(tmp_path, data_root):
    paths, repository = _local_vault(tmp_path)
    set_up_data_root(data_root)
    vault = loaded(paths)
    model = FakeLocalModel()
    report = local_index.run_local_index(vault, repository, launcher=InProcessLauncher(model), preflight=lambda: [],
                                         locks=no_locks, force=True)
    assert report["status"] == "complete", report
    assert report["windows_stored"] > 0 and report["canaries"]["first"]
    with connect(repository.sqlite_path, read_only=True) as connection:
        known = spaces(connection)
    assert {row["name"] for row in known.values()} == {"local:grouped", "local:singleton"}
    assert all(row["status"] == "active" and row["canaries"] for row in known.values())
    for space in report["spaces"].values():
        assert VectorCache(cache_path(paths.root, space)).report()["rows"] > 0
    # Exam windows are their own class: never joined to teaching text.
    exam_texts = [chunks for chunks in model.documents if any("Exam question" in chunk for chunk in chunks)]
    assert exam_texts and all(len(chunks) == 1 for chunks in exam_texts)
    again = local_index.run_local_index(vault, repository, launcher=InProcessLauncher(FakeLocalModel()),
                                        preflight=lambda: [], locks=no_locks, force=True)
    assert again["status"] == "complete" and again["windows_stored"] == 0 and again["owed_windows"] == 0


def test_a_moved_canary_stores_nothing_and_marks_epoch_drift(tmp_path, data_root):
    paths, repository = _local_vault(tmp_path)
    set_up_data_root(data_root)
    vault = loaded(paths)
    first = local_index.run_local_index(vault, repository, launcher=InProcessLauncher(FakeLocalModel()),
                                        preflight=lambda: [], locks=no_locks, force=True)
    cache_path(paths.root, first["spaces"]["local:grouped"]).unlink()
    drifted = local_index.run_local_index(vault, repository, launcher=InProcessLauncher(FakeLocalModel(salt="x")),
                                          preflight=lambda: [], locks=no_locks, force=True)
    assert drifted["status"] == "epoch_drift" and "canary" in drifted["reason"]
    assert not cache_path(paths.root, first["spaces"]["local:grouped"]).exists()
    with connect(repository.sqlite_path, read_only=True) as connection:
        assert {row["status"] for row in spaces(connection).values()} == {"epoch_drift"}
    blocked = local_index.run_local_index(vault, repository, launcher=InProcessLauncher(FakeLocalModel()),
                                          preflight=lambda: [], locks=no_locks, force=True)
    assert blocked["status"] == "epoch_drift"


def test_a_job_that_cannot_start_is_waiting_never_failed(tmp_path, data_root):
    paths, repository = _local_vault(tmp_path)
    set_up_data_root(data_root)
    vault = loaded(paths)
    run = InProcessLauncher(FakeLocalModel())
    gpu = local_index.run_local_index(vault, repository, launcher=run, locks=no_locks, force=True,
                                      preflight=lambda: ["free VRAM 3.0 GiB is below 22.0 GiB"])
    assert gpu["status"] == "waiting_for_gpu" and "VRAM" in gpu["reason"] and run.jobs == []

    def busy():
        raise launcher.LocksBusy("the GPU lock is held")

    held = local_index.run_local_index(vault, repository, launcher=run, preflight=lambda: [], force=True,
                                       locks=busy)
    assert held["status"] == "waiting_for_gpu" and run.jobs == []
    completed = local_index._completed_at(repository, "ext_book") or datetime.now(timezone.utc)
    young = local_index.run_local_index(vault, repository, launcher=run, preflight=lambda: [], locks=no_locks,
                                        now=completed + timedelta(minutes=1))
    assert young["status"] == "waiting_for_batch" and run.jobs == []
    old = local_index.run_local_index(vault, repository, launcher=run, preflight=lambda: [], locks=no_locks,
                                      now=completed + timedelta(minutes=16))
    assert old["status"] == "complete" and len(run.jobs) == 1


def test_the_local_space_is_off_until_enabled_and_set_up(tmp_path, data_root):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    off = local_index.run_local_index(loaded(paths), repository, launcher=InProcessLauncher(FakeLocalModel()))
    assert off == {"job": "local_source_index", "status": "disabled", "reason": "embedding.local.enabled is false"}
    append_config_toml(paths.root, "[embedding.local]\nenabled = true\n")
    unset = local_index.run_local_index(loaded(paths), repository, launcher=InProcessLauncher(FakeLocalModel()))
    assert unset["status"] == "disabled" and "not set up" in unset["reason"]


def test_extraction_queues_the_index_jobs_only_while_their_switches_are_on(tmp_path):
    from learnloop.config.loader import load_config
    from learnloop.content.pipeline.jobs import queue_contextual_indexes

    paths, repository = build_retrieval_vault(tmp_path / "vault")
    queued: list[tuple[str, list]] = []
    ctx = SimpleNamespace(repo=repository, enqueue_batch=lambda kind, jobs: queued.append((kind, jobs)) or f"b{len(queued)}")
    config = load_config(paths.root / "learnloop.toml", load_environment=False)
    assert queue_contextual_indexes(ctx, config, "ext_book") == [] and queued == []
    append_config_toml(paths.root, "[embedding.local]\nenabled = true\n\n" + """
[ai.providers.voyage_context]
type = "voyage_contextual_embedding"

[embedding.fallback]
enabled = true
""")
    config = load_config(paths.root / "learnloop.toml", load_environment=False)
    assert len(queue_contextual_indexes(ctx, config, "ext_book")) == 2
    assert [kind for kind, _jobs in queued] == ["local_source_index", "source_fallback_backfill"]


def test_the_commands_dry_run_without_starting_anything(tmp_path, data_root, monkeypatch):
    from typer.testing import CliRunner

    from learnloop.cli import app

    def refuse(*_args, **_kwargs):
        raise AssertionError("a process was started")

    monkeypatch.setattr("subprocess.run", refuse)
    monkeypatch.setattr("subprocess.Popen", refuse)
    runner = CliRunner()
    plan = runner.invoke(app, ["embeddings", "local", "setup", "--dry-run", "--json"])
    assert plan.exit_code == 0, plan.output
    planned = json.loads(plan.output)
    assert planned["status"] == "dry_run" and planned["model"]["revision"] == pins.MODEL_REVISION
    assert not pins.manifest_path().exists()
    refused = runner.invoke(app, ["embeddings", "local", "setup", "--json"])
    assert refused.exit_code == 1 and "33-gb" in json.loads(refused.output)["reason"]
    paths, _repository = _local_vault(tmp_path)
    set_up_data_root(data_root)
    owed = runner.invoke(app, ["embeddings", "local", "index", "--vault", str(paths.root), "--dry-run", "--json"])
    assert owed.exit_code == 0, owed.output
    assert json.loads(owed.output)["status"] == "dry_run" and json.loads(owed.output)["owed_windows"] > 0


def test_a_worker_on_another_software_epoch_stores_nothing(tmp_path, data_root):
    """Codex review F13: the measured (torch, transformers, CUDA) must equal the
    epoch in the space id; canaries within tolerance do not excuse a change."""

    paths, repository = _local_vault(tmp_path)
    set_up_data_root(data_root)
    vault = loaded(paths)
    model = FakeLocalModel()
    model.info = {**model.info, "transformers": "5.19.0"}
    report = local_index.run_local_index(vault, repository, launcher=InProcessLauncher(model), preflight=lambda: [],
                                         locks=no_locks, force=True)
    assert report["status"] == "epoch_changed" and report["measured_epoch"]["transformers"] == "5.19.0"
    for space in report["spaces"].values():
        assert not cache_path(paths.root, space).exists() or VectorCache(cache_path(paths.root, space)).report()["rows"] == 0
    with connect(repository.sqlite_path, read_only=True) as connection:
        assert spaces(connection) == {}  # no space registered under the old identity


class _OneBadVector(FakeLocalModel):
    def encode_documents(self, documents, *, batch_size=1):
        rows = super().encode_documents(documents, batch_size=batch_size)
        return [row * float("nan") if any("Cofactor" in chunk for chunk in chunks) else row
                for row, chunks in zip(rows, documents, strict=True)]


def test_a_rejected_window_leaves_the_run_partial_and_the_window_owed(tmp_path, data_root):
    """Codex review F15: completion counts invalid and over-limit windows."""

    paths, repository = _local_vault(tmp_path)
    set_up_data_root(data_root)
    vault = loaded(paths)
    report = local_index.run_local_index(vault, repository, launcher=InProcessLauncher(_OneBadVector()),
                                         preflight=lambda: [], locks=no_locks, force=True)
    assert report["windows_invalid"] >= 1 and report["status"] == "partial", report
    again = local_index.run_local_index(vault, repository, launcher=InProcessLauncher(FakeLocalModel()),
                                        preflight=lambda: [], locks=no_locks, force=True, dry_run=True)
    assert again["owed_windows"] >= 1


def test_a_deferred_index_job_is_woken_at_its_retry_time(tmp_path, data_root):
    """Codex review F4: a job that waits for the batch (or the GPU) completes
    with a ``retry_at``; the host's sweep queues the next batch once it has
    passed, so the new book is indexed without another import or a command."""

    import threading

    from learnloop.content.pipeline.jobs import DurableIngestJobs
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec
    from learnloop.db.repositories import Repository

    paths, repository = _local_vault(tmp_path)
    set_up_data_root(data_root)
    vault = loaded(paths)
    completed = local_index._completed_at(repository, "ext_book") or datetime.now(timezone.utc)
    deferred = local_index.run_local_index(vault, repository, launcher=InProcessLauncher(FakeLocalModel()),
                                           preflight=lambda: [], locks=no_locks, now=completed + timedelta(minutes=1))
    assert deferred["status"] == "waiting_for_batch"
    due = datetime.fromisoformat(deferred["retry_at"])
    assert due == completed + timedelta(minutes=15)
    runner = IngestRunner(Repository(repository.sqlite_path), vault_root=paths.root, worker_id="test")
    first = runner.enqueue_batch(local_index.INDEX_JOB, [JobSpec(local_index.INDEX_JOB, {"extraction_id": "ext_book"})])
    [job] = repository.ingest_jobs_for_batch(first)
    assert repository.transition_unleased_ingest_job(job["id"], status="completed", result=deferred)
    started: list[int] = []
    host = SimpleNamespace(_runner=runner, _stop=threading.Event(), reading_now=lambda: due - timedelta(seconds=1),
                           _ensure_worker=lambda: started.append(1))
    assert DurableIngestJobs.resume_contextual_index(host) is None and started == []  # not due yet
    host.reading_now = lambda: due + timedelta(seconds=1)
    batch = DurableIngestJobs.resume_contextual_index(host)
    assert batch is not None and started == [1]
    [queued] = repository.ingest_jobs_for_batch(batch)
    assert queued["status"] == "queued" and queued["job_type"] == local_index.INDEX_JOB
    assert DurableIngestJobs.resume_contextual_index(host) is None  # the newest job is live: nothing twice
    # A finished index (or one switched off) wakes nothing.
    assert repository.transition_unleased_ingest_job(queued["id"], status="completed", result={"status": "complete"})
    assert DurableIngestJobs.resume_contextual_index(host) is None


def test_an_index_obligation_that_cannot_be_queued_fails_the_extraction_retryably(tmp_path):
    """Codex review F4: never swallowed (the source_vectors survival rule)."""

    from learnloop.config.loader import load_config
    from learnloop.content.pipeline.jobs import queue_contextual_indexes
    from learnloop.content.pipeline.runner import IngestRunnerError

    paths, repository = _local_vault(tmp_path)

    def broken(_kind, _jobs):
        raise OSError("disk full")

    ctx = SimpleNamespace(repo=repository, enqueue_batch=broken)
    config = load_config(paths.root / "learnloop.toml", load_environment=False)
    with pytest.raises(IngestRunnerError) as caught:
        queue_contextual_indexes(ctx, config, "ext_book")
    assert caught.value.code == "contextual_index_not_queued" and caught.value.retryable
