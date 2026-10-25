"""The local document index job (spec_local_contextual_retrieval_v1 §4.1, §4.3, §7.2).

It lives in source_retrieval (windows, the policy predicates, the corpus) and
drives learnloop.local_embeddings (the worker, the meter, the cache), which
never imports source_retrieval back.

Batch, deferred, no residency. ``run_local_index`` takes every owed window of
the vault (both variants, grouped and singleton), and when the batch rule,
the start checks and the locks allow it launches ONE worker in its own capped
scope under the GPU meter: load, smoke, canaries, encode, unload, exit. It
then checks the canaries against the space's stored ones (cos >= 0.999, an
identity check: below it nothing is stored and the space is ``epoch_drift``)
and writes the vectors into the vault's vector cache.

A job that cannot start is ``waiting_for_gpu`` (with its reason) or
``waiting_for_batch``, never ``failed``: coverage stays partial and the
resolver uses another space meanwhile. The obligation is the cache's own
coverage, so a later run (``learnloop embeddings local index``, or the next
extraction's job) picks up whatever is still owed.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.retrieval_spaces import register_space, set_space_canaries, set_space_status, spaces
from learnloop.local_embeddings import pins
from learnloop.local_embeddings import worker as worker_module
from learnloop.local_embeddings.cache import CacheUnreadable, VectorCache, cache_path
from learnloop.local_embeddings.gpu_meter import GpuBudgetExceeded, GpuMeter
from learnloop.local_embeddings.identity import local_space_pins, space_id as make_space_id
from learnloop.local_embeddings.launcher import LocksBusy, ScopedLauncher, gpu_locks
from learnloop.local_embeddings.setup import load_manifest
from learnloop.source_retrieval.corpus import current_extractions
from learnloop.source_retrieval.windows import (
    WINDOW_RULE,
    Window,
    expected_keys,
    extraction_windows,
    window_key,
    windows_by_extraction,
)
from learnloop.vault.models import LoadedVault

INDEX_JOB = "local_source_index"
#: Statuses that leave windows owed and name a ``retry_at``: the sweep queues the next batch then.
DEFERRED_STATUSES = frozenset({"waiting_for_batch", "waiting_for_gpu", "partial"})
VARIANTS = ("grouped", "singleton")
LIST_NAMES = {"grouped": "local:grouped", "singleton": "local:singleton"}


def local_reason(vault: LoadedVault, root: Path | None = None) -> tuple[dict[str, Any] | None, str | None]:
    """``(setup manifest, None)`` when the local space may be used, else ``(None, why)``."""

    if not vault.config.embedding.local.enabled:
        return None, "embedding.local.enabled is false"
    if not vault.config.source_retrieval.dense:
        return None, "source_retrieval.dense is false"
    return load_manifest(root)


EPOCH_KEYS = ("torch", "transformers", "cuda")


def _epoch_value(value: Any) -> str:
    return str(value) if value not in (None, "") else "none"


def epoch_of(manifest: Mapping[str, Any]) -> dict[str, str]:
    """The software epoch setup recorded (part of the space id)."""

    recorded = manifest.get("software_epoch") or {}
    return {key: _epoch_value(recorded.get(key)) for key in EPOCH_KEYS}


def measured_epoch(load: Mapping[str, Any] | None) -> dict[str, str]:
    """The epoch the worker measured after loading (``torch.__version__``,
    ``transformers.__version__``, ``torch.version.cuda``)."""

    return {key: _epoch_value((load or {}).get(key)) for key in EPOCH_KEYS}


def local_spaces(manifest: Mapping[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]:
    """``{variant: (space_id, pins)}`` for the set-up environment's epoch."""

    out = {}
    for variant in VARIANTS:
        space_pins = local_space_pins(variant=variant, software_epoch=manifest["software_epoch"],
                                      window_rule=WINDOW_RULE)
        out[variant] = (make_space_id(space_pins), space_pins)
    return out


def owed(vault: LoadedVault, repository: Repository, local: Mapping[str, tuple[str, dict[str, Any]]],
         extraction_ids: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """Every (extraction, variant) whose windows the cache does not fully hold."""

    targets = sorted(extraction_ids if extraction_ids is not None else current_extractions(repository))
    windows = windows_by_extraction(vault, repository, targets, VARIANTS)
    items = []
    for (extraction_id, variant), rows in sorted(windows.items()):
        space, _pins = local[variant]
        cache = VectorCache(cache_path(vault.root, space))
        try:
            have = cache.present(key for keys in expected_keys(space, rows).values() for key, _w in keys)
        except CacheUnreadable:
            have = set()
        missing = [window for window in rows
                   if any(key not in have for _span, keys in expected_keys(space, [window]).items()
                          for key, _w in keys)]
        if missing:
            items.append({"extraction_id": extraction_id, "variant": variant, "space_id": space,
                          "windows": len(rows), "missing": missing})
    return items


def _document_id(chunks: Sequence[str]) -> str:
    return "d_" + hashlib.sha256(json.dumps(list(chunks)).encode("utf-8")).hexdigest()[:24]


def build_job(items: Sequence[Mapping[str, Any]], *, manifest: Mapping[str, Any], plan_id: str,
              profile: Mapping[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """The private job (carries book text) and ``{document id: [targets]}``.

    Identical window texts (a one-block grouped window and its singleton) are
    encoded once and stored in each space."""

    documents: dict[str, list[str]] = {}
    targets: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        for window in item["missing"]:
            document = _document_id(window.chunks)
            documents.setdefault(document, window.chunks)
            targets.setdefault(document, []).append({"space_id": item["space_id"], "window": window})
    job = {
        "version": worker_module.WORKER_VERSION, "plan_id": plan_id, "model_dir": str(manifest["model_dir"]),
        "model_files": {name: list(value) for name, value in pins.MODEL_FILES.items()},
        "remote_code": list(pins.REMOTE_CODE_FILES), "precision": pins.PRECISION,
        "attention": pins.ATTENTION_IMPLEMENTATION, "fp32_modules": list(pins.FP32_MODULES),
        "dimensions": pins.MODEL_DIMENSIONS, "max_document_tokens": pins.MAX_DOCUMENT_TOKENS,
        "index_batch_size": pins.INDEX_BATCH_SIZE, "query_batch_size": pins.QUERY_BATCH_SIZE,
        "batch_invariance_min_cos": pins.BATCH_INVARIANCE_MIN_COS,
        "context_max_cos": pins.CONTEXT_SENSITIVITY_MAX_COS,
        "smoke": {"context": pins.SMOKE_CONTEXT, "query": pins.SMOKE_QUERY,
                  "padding_document": pins.SMOKE_PADDING_DOCUMENT},
        "canaries": {"documents": [list(document) for document in pins.CANARY_DOCUMENTS],
                     "queries": list(pins.CANARY_QUERIES)},
        "profile": dict(profile or {}), "profile_repeats": pins.PROFILE_REPEATS,
        "documents": [{"id": key, "chunks": [{"id": str(position), "text": text}
                                             for position, text in enumerate(chunks)]}
                      for key, chunks in sorted(documents.items())],
        "queries": [], "limits": pins.limits(),
    }
    return job, targets


def _cos(a: Sequence[float], b: Sequence[float]) -> float:
    x, y = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    denominator = float(np.linalg.norm(x) * np.linalg.norm(y))
    return float(x @ y / denominator) if denominator else 0.0


def canary_check(new: Mapping[str, Any] | None, stored: Mapping[str, Any] | None) -> dict[str, Any]:
    """Compare this batch's canaries with the space's stored ones (cos >= ``CANARY_MIN_COS``)."""

    if not new or new.get("problems"):
        return {"ok": False, "reason": "the worker returned no valid canaries", "min_cos": None}
    if not stored:
        return {"ok": True, "first": True, "min_cos": None}
    pairs = [(a, b) for row_a, row_b in zip(new["documents"], stored["documents"], strict=False)
             for a, b in zip(row_a, row_b, strict=False)]
    pairs += list(zip(new["queries"], stored["queries"], strict=False))
    if len(pairs) != sum(len(row) for row in stored["documents"]) + len(stored["queries"]):
        return {"ok": False, "reason": "the canary set changed shape", "min_cos": None}
    lowest = min(_cos(a, b) for a, b in pairs)
    return {"ok": lowest >= pins.CANARY_MIN_COS, "min_cos": round(lowest, 6), "tolerance": pins.CANARY_MIN_COS,
            "reason": None if lowest >= pins.CANARY_MIN_COS else
            f"a canary moved (cos {lowest:.6f} < {pins.CANARY_MIN_COS}): epoch drift"}


def store_output(vault: LoadedVault, output: Mapping[str, Any], targets: Mapping[str, Sequence[Mapping[str, Any]]],
                 *, job_id: str) -> dict[str, int]:
    """Validate and cache the worker's vectors; a wrong count or value stores nothing for that window."""

    rows_by_space: dict[str, list[dict[str, Any]]] = {}
    counts = {"windows_stored": 0, "windows_missing": 0, "windows_invalid": 0, "windows_over_limit": 0}
    for document, entries in targets.items():
        result = (output.get("documents") or {}).get(document)
        if result is None:
            counts["windows_missing"] += len(entries)
            continue
        if result.get("error") == "over_limit":
            counts["windows_over_limit"] += len(entries)
            continue
        vectors = result.get("vectors") or []
        for entry in entries:
            window: Window = entry["window"]
            if result.get("error") or len(vectors) != len(window.members) or any(
                    worker_module.check_vector(np.asarray(vector), pins.MODEL_DIMENSIONS) for vector in vectors):
                counts["windows_invalid"] += 1
                continue
            space = entry["space_id"]
            for member, vector in zip(window.members, vectors, strict=True):
                rows_by_space.setdefault(space, []).append({
                    "key": window_key(space, window, member.span_id), "extraction_id": window.extraction_id,
                    "span_id": member.span_id, "vector": vector, "split_mean": member.split is not None})
            counts["windows_stored"] += 1
    for space, rows in rows_by_space.items():
        VectorCache(cache_path(vault.root, space)).write(rows, job_id=job_id, meta={"space_id": space})
    return counts


def preflight_problems(*, meminfo: Callable[[], Mapping[str, int]] = worker_module.read_meminfo,
                       gpu: Callable[[], Mapping[str, Any] | None] = worker_module.gpu_state) -> list[str]:
    """The worker's own start checks, measured now (no scope needed: this is the caller)."""

    try:
        state = gpu()
    except Exception:  # noqa: BLE001 - recorded as a refusal
        state = None
    return worker_module.start_problems(pins.limits(), meminfo=meminfo(), scope={}, gpu=state, require_scope=False)


def _completed_at(repository: Repository, extraction_id: str) -> datetime | None:
    run = repository.get_extraction_run(extraction_id) or {}
    value = run.get("completed_at") or run.get("created_at")
    try:
        stamp = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def run_local_index(vault: LoadedVault, repository: Repository, *, root: Path | None = None,
                    launcher: Callable[..., dict[str, Any]] | None = None, meter: GpuMeter | None = None,
                    preflight: Callable[[], list[str]] | None = None, locks: Callable[[], Any] = gpu_locks,
                    now: datetime | None = None, force: bool = False,
                    extraction_ids: Sequence[str] | None = None, dry_run: bool = False) -> dict[str, Any]:
    """Index every owed window of the vault in one worker batch (aggregate report only)."""

    report: dict[str, Any] = {"job": INDEX_JOB}
    manifest, reason = local_reason(vault, root)
    if manifest is None:
        return {**report, "status": "disabled", "reason": reason}
    local = local_spaces(manifest)
    report["spaces"] = {LIST_NAMES[variant]: space for variant, (space, _p) in local.items()}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        known = spaces(connection)
    drift = [space for space, _p in local.values() if (known.get(space) or {}).get("status") == "epoch_drift"]
    if drift:
        return {**report, "status": "epoch_drift",
                "reason": "the canaries moved under this environment: re-index under a new epoch or pin the old "
                          "environment back (the owner's choice)"}
    items = owed(vault, repository, local, extraction_ids)
    report.update(owed_extractions=len({item["extraction_id"] for item in items}),
                  owed_windows=sum(len(item["missing"]) for item in items))
    if not items:
        return {**report, "status": "complete", "windows_stored": 0}
    if dry_run:
        return {**report, "status": "dry_run"}
    moment = now or datetime.now(timezone.utc)
    stamps = [stamp for item in items if (stamp := _completed_at(repository, item["extraction_id"])) is not None]
    minutes = float(vault.config.embedding.local.index_batch_minutes)
    # Codex review F4: every deferral names when to try again, and the ingest
    # host's sweep (``DurableIngestJobs.resume_contextual_index``) queues the
    # next batch then; a GPU that is busy is checked again at the batch pace.
    recheck = (moment + timedelta(minutes=minutes)).isoformat()
    report["retry_at"] = recheck
    if not force and stamps and (moment - min(stamps)).total_seconds() < minutes * 60:
        return {**report, "status": "waiting_for_batch", "retry_at": (min(stamps) + timedelta(minutes=minutes)).isoformat(),
                "reason": f"the batch waits until its oldest owed extraction is {minutes:g} minutes old "
                          "(embedding.local.index_batch_minutes; `--now` forces it)"}
    problems = (preflight or preflight_problems)()
    if problems:
        return {**report, "status": "waiting_for_gpu", "reason": "; ".join(problems)}
    data = root or pins.data_root()
    job_id = uuid4().hex
    job, targets = build_job(items, manifest=manifest, plan_id=f"local_{job_id[:16]}")
    meter = meter or GpuMeter(data / "gpu-meter")
    run = launcher or ScopedLauncher(Path(manifest["env_python"]))
    try:
        with locks():
            output = run(job, data / "runs" / job_id, meter=meter, plan_id=job["plan_id"])
    except LocksBusy as exc:
        return {**report, "status": "waiting_for_gpu", "reason": str(exc)}
    except GpuBudgetExceeded as exc:
        return {**report, "status": "waiting_for_gpu", "reason": str(exc)}
    report["worker"] = {key: output.get(key) for key in ("status", "reason", "peaks", "unload", "supervised")}
    if output.get("status") not in ("complete", "aborted") or output.get("canaries") is None:
        # Refused, failed, or stopped before the canaries: nothing is stored and
        # no drift is inferred (a run that never measured cannot have drifted).
        return {**report, "status": "worker_" + str(output.get("status")), "reason": output.get("reason")}
    measured = measured_epoch(output.get("load"))
    if measured != epoch_of(manifest):
        # Codex review F13: the epoch is part of the space id, so vectors made
        # under another (torch, transformers, CUDA) belong to ANOTHER space,
        # whatever the canaries say. Nothing is stored; the owner reruns
        # setup, which records the new epoch (a new space, indexed afresh).
        return {**report, "status": "epoch_changed", "measured_epoch": measured,
                "recorded_epoch": epoch_of(manifest),
                "reason": "the worker's software epoch differs from the one setup recorded (a new space): rerun "
                          "`learnloop embeddings local setup` to record it, then index again"}
    stamp = datetime.now(timezone.utc).isoformat()
    with repository.connection() as connection:
        for variant, (space, space_pins) in local.items():
            register_space(connection, space_id=space, name=LIST_NAMES[variant], kind="local", pins=space_pins,
                           status="active", now=stamp)
        stored = (spaces(connection).get(local["grouped"][0]) or {}).get("canaries")
        check = canary_check(output.get("canaries"), stored)
        report["canaries"] = check
        if not check["ok"]:
            for space, _p in local.values():
                set_space_status(connection, space, "epoch_drift", reason=check["reason"], now=stamp)
            return {**report, "status": "epoch_drift", "reason": check["reason"]}
        if check.get("first"):
            for space, _p in local.values():
                set_space_canaries(connection, space, output["canaries"], now=stamp)
    counts = store_output(vault, output, targets, job_id=job_id)
    # Codex review F15: a window the worker rejected (over its limit, or an
    # invalid vector) is not stored, so it stays owed; the run is partial.
    rejected = counts["windows_missing"] + counts["windows_invalid"] + counts["windows_over_limit"]
    status = "complete" if output.get("status") == "complete" and not rejected else "partial"
    return {**report, "status": status, **counts}


#: The profile pool's ESTIMATED size per target: E1 measured 0.68 model tokens
#: per estimated token (5,603 for a nominal 8,192), so twice the target is
#: always enough text for the worker to fit the true target by its own count.
PROFILE_POOL_FACTOR = 2


def profile_pools(vault: LoadedVault, repository: Repository, extraction_id: str,
                  sizes: Sequence[int] = pins.PROFILE_TOKENS) -> dict[str, dict[str, Any]]:
    """P0: per size, a pool of consecutive TEACHING blocks the worker fits to the
    true token count (``worker.fit_window``). Teaching text only: no exam,
    held-out, solution or assessment-lane block is ever sent."""

    from learnloop.source_retrieval.windows import token_estimate

    windows = extraction_windows(vault, repository, extraction_id, "singleton")
    texts = [window.chunks[0] for window in windows if window.policy_class == "teaching"]
    pools: dict[str, dict[str, Any]] = {}
    for size in sizes:
        pool, total = [], 0
        for text in texts:
            pool.append(text)
            total += token_estimate(text)
            if total >= PROFILE_POOL_FACTOR * size:
                break
        pools[str(size)] = {"pool": pool, "target": int(size)}
    return pools


def run_profile(vault: LoadedVault, repository: Repository, extraction_id: str, *, root: Path | None = None,
                launcher: Callable[..., dict[str, Any]] | None = None, meter: GpuMeter | None = None,
                preflight: Callable[[], list[str]] | None = None, locks: Callable[[], Any] = gpu_locks,
                sizes: Sequence[int] = pins.PROFILE_TOKENS) -> dict[str, Any]:
    """P0's true 8,192-token profile: one metered worker (load, smoke, canaries,
    profile at each size by the model's own count, unload); nothing is indexed."""

    manifest, reason = load_manifest(root)
    if manifest is None:
        return {"status": "not_set_up", "reason": reason}
    problems = (preflight or preflight_problems)()
    if problems:
        return {"status": "waiting_for_gpu", "reason": "; ".join(problems)}
    pools = profile_pools(vault, repository, extraction_id, sizes)
    data = root or pins.data_root()
    job_id = uuid4().hex
    job, _targets = build_job([], manifest=manifest, plan_id=f"profile_{job_id[:16]}", profile=pools)
    meter = meter or GpuMeter(data / "gpu-meter")
    run = launcher or ScopedLauncher(Path(manifest["env_python"]))
    try:
        with locks():
            output = run(job, data / "runs" / job_id, meter=meter, plan_id=job["plan_id"])
    except (LocksBusy, GpuBudgetExceeded) as exc:
        return {"status": "waiting_for_gpu", "reason": str(exc)}
    return {"status": output.get("status"), "reason": output.get("reason"), "profile": output.get("profile"),
            "load": {key: (output.get("load") or {}).get(key) for key in ("load_s", "torch", "transformers", "cuda")},
            "smoke_ok": (output.get("smoke") or {}).get("all_ok"), "peaks": output.get("peaks"),
            "unload": output.get("unload"), "supervised": output.get("supervised")}


def coverage_report(vault: LoadedVault, repository: Repository, root: Path | None = None) -> dict[str, Any]:
    """Doctor's view: per local space, rows, covered extractions, epoch and canary status."""

    manifest, reason = local_reason(vault, root)
    if manifest is None:
        return {"enabled": False, "reason": reason}
    local = local_spaces(manifest)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        known = spaces(connection)
    extractions = sorted(current_extractions(repository))
    items = owed(vault, repository, local, extractions)
    owed_by_variant = {variant: {item["extraction_id"] for item in items if item["variant"] == variant}
                       for variant in VARIANTS}
    rows = {}
    for variant, (space, _p) in local.items():
        row = known.get(space) or {}
        rows[LIST_NAMES[variant]] = {
            "space_id": space, "status": row.get("status") or "not_indexed", "reason": row.get("status_reason"),
            "canaries": "stored" if row.get("canaries") else "none",
            "cache": VectorCache(cache_path(vault.root, space)).report(),
            "covered_sources": len(extractions) - len(owed_by_variant[variant]), "sources": len(extractions),
        }
    return {"enabled": True, "software_epoch": manifest["software_epoch"], "spaces": rows}


__all__ = ["DEFERRED_STATUSES", "EPOCH_KEYS", "INDEX_JOB", "LIST_NAMES", "VARIANTS", "build_job", "canary_check", "coverage_report",
           "epoch_of", "local_reason", "local_spaces", "measured_epoch", "owed", "preflight_problems", "profile_pools", "run_local_index", "run_profile", "store_output"]
