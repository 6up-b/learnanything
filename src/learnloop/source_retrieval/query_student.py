"""P2, the query student: teacher targets, the screen, recipes, seeds, evaluation and adoption (spec_local_contextual_retrieval_v1 §7.1, §7.2, §9.3, §10 P2).

It lives in source_retrieval (the windows, the policy predicates, the vector cache readers) and
drives learnloop.local_embeddings (the 9B worker, the trainer, the meter, the locks, the
decision core), which never imports source_retrieval back.

Every step is owner-run (``learnloop embeddings local student ...``), resumable, and has a dry
run that starts nothing:

1. ``setup``: the two pinned 0.6B bases (owner, 2026-10-26: ``pplx-embed-v1-0.6b`` primary,
   ``Qwen3-Embedding-0.6B`` second), downloaded into the data root at their pinned revisions or
   adopted in place (``--adopt-base NAME=DIR``, verified, never moved), every file checked.
2. ``generate`` (``student_data``): synthetic questions from permitted passages (Q8).
3. ``targets`` (:func:`run_targets`): ONE 9B worker batch in query mode encodes every training
   question and every bank question (``encode_queries``, ``[Q]``, mean pool) into int8 shards,
   under the GPU lock and the full-suite lock, in the worker's 12G scope, charged to the capped
   P2 meter (6 GPU-hours, keep). Canaries and the software epoch are checked before anything is
   kept. The teacher-cosine leakage guard (>= 0.90 to any bank question) runs here, only against
   the COMPLETE bank, and records that bank's fingerprint: a question is eligible for training or
   evaluation only when that bank's screen passed it (:func:`eligible_rows`). The teacher and the
   student are never resident together: each is its own process, one at a time, by the lock, and a
   GPU-resident query process is asked to exit before any exclusive GPU job starts.
4. ``train`` (:func:`run_next`): the next run of the schedule (:func:`next_step`): the screen
   (``projection_only`` and ``align`` on the primary base, ``align`` on the second base, at the
   screen budget), then the recipes on the chosen base (``align_kd``, ``align_kd_mp``), then the
   learning curve (the small budget, then the large one only when its expected gain beats its
   GPU-hours: ``student_decision.continue_training``), then the remaining seeds of the chosen
   recipe. Every choice is ``argmax E[U]`` on development (``student_decision.decide``); none is
   a margin. The teacher's top-50 for the ranking losses is computed here over the permitted
   training candidates (:func:`training_candidates`: the training families only, every
   contextual window holding a bank support left out), and the multi-positive term's hard
   negatives are that top-50's same-source blocks. A run is named by its dataset fingerprint
   (vault, bank, splits, candidates, families: :func:`campaign`), so nothing is reused across
   datasets.
5. ``evaluate`` (:func:`evaluate`): a checkpoint (the schedule's candidate, the serving one, or
   any completed one by ``--checkpoint``, on any screened bank) through the real query process on
   the bank questions whose evidence lies in this vault (every arm on the same questions,
   candidate units and labels, a supplied arm proving it by the comparison fingerprint; unjudged
   retrieved material latent and listed for labelling), beside the teacher's bank vectors and any
   adopted incumbent, per stratum (deictic, logged, unseen family: unseen by the families pinned in
   the checkpoint's manifest, or ``unknown_family`` without that provenance); §9.3's expected utility over
   the MEASURED actions RECOMMENDS (E1's aggregates are reported as priors, never decided on),
   with its posterior draws kept. No evaluation changes the serving state by itself: a losing
   re-evaluation recommends withdrawal. Adoption and withdrawal are the owner's (``student
   adopt`` / ``reject`` / ``revoke``: :func:`owner_choice`) until P0's §9.1 label-noise posterior
   holds that authority; every verdict (the rule's, the owner's) is appended to
   ``judgment_ledger``, and the owner's answer to a costed recommendation is an observation of
   lambda. ``adoption.json`` is only the serving pointer. Its weight in the fusion is then learned
   (§9.2) like every list.

Book text, teacher vectors and checkpoints live under ``<data root>/students/<space id>/`` (§11),
never in the repository. A vault's ``state.sqlite`` holds the generator's paid-call receipts and
checkpoints (``PaidCalls``: the prompt and output receipts the paid-output invariant needs) and
the adoption verdicts in ``judgment_ledger``; no training data or vector is written there.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence, Set
from contextlib import closing
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any
from uuid import uuid4

import numpy as np

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.retrieval_spaces import spaces as known_spaces
from learnloop.local_embeddings import pins
from learnloop.local_embeddings import student_decision as SD
from learnloop.local_embeddings import student_pins as SP
from learnloop.local_embeddings.cache import CacheUnreadable, VectorCache, cache_path
from learnloop.local_embeddings.gpu_meter import GpuBudgetExceeded, GpuMeter
from learnloop.local_embeddings.launcher import LocksBusy, ScopedLauncher, gpu_locks
from learnloop.local_embeddings.setup import load_manifest
from learnloop.source_retrieval import student_data as D
from learnloop.source_retrieval.corpus import current_extractions
from learnloop.source_retrieval.local_index import (
    build_job,
    canary_check,
    epoch_of,
    exclusive_gpu_yield,
    measured_epoch,
    preflight_problems,
)
from learnloop.source_retrieval.recipes import block_record_id
from learnloop.source_retrieval.student_encoder import adoption_path, bases_manifest, checkpoint_dir, student_space
from learnloop.source_retrieval.windows import expected_keys, mean_vector, windows_by_extraction
from learnloop.vault.models import LoadedVault

#: keep (operational): teacher target rows per int8 shard (an aborted run keeps every finished shard).
SHARD_SIZE = 5_000
#: keep (measurement): development questions one run is measured on at most.
DEV_MAX = 2_000
#: keep (numerical): the smallest cosine spread a temperature may take (a degenerate dev set).
MIN_TEMPERATURE = 1e-3
#: Committed E1 aggregates (docs/reviews/experiments-e1-report.md, primary slice, 29 scored per copy):
#: the teacher (V2_grouped), Qwen (R1) and Voyage (R5_grouped) CE@10. Legacy priors for arms the
#: owner has not supplied per-question outcomes for (unpaired, so wider).
E1_AGGREGATES: dict[str, dict[str, tuple[float, int]]] = {
    "teacher": {"linear_algebra": (0.862, 29), "probability": (0.793, 29)},
    "qwen": {"linear_algebra": (0.828, 29), "probability": (0.828, 29)},
    "voyage": {"linear_algebra": (0.828, 29), "probability": (0.862, 29)},
}
TRAINER_SCRIPT = "student_trainer.py"


# -- context --------------------------------------------------------------------------------------------
def context(vault: LoadedVault, root: Path | None = None) -> tuple[dict[str, Any] | None, str | None, str | None]:
    """``(setup manifest, student space id, None)`` or ``(None, None, why)``."""

    from learnloop.source_retrieval.local_index import local_reason

    manifest, reason = local_reason(vault, root)
    if manifest is None:
        return None, None, reason
    return manifest, student_space(manifest), None


def home(root: Path, space: str) -> Path:
    return SP.space_home(root, space)


def p2_meter(root: Path, space: str) -> GpuMeter:
    """P2's capped meter (6 GPU-hours, keep): teacher targets, every run, failed runs included."""

    return GpuMeter(home(root, space) / "gpu-meter", cap_hours=SP.P2_GPU_HOURS_CAP)


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _write_json(path: Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    os.replace(temporary, path)


# -- 1. the bases ------------------------------------------------------------------------------------------
_DOWNLOAD = (
    "import json, sys\n"
    "from huggingface_hub import snapshot_download\n"
    "snapshot_download(repo_id=sys.argv[1], revision=sys.argv[2], local_dir=sys.argv[3],"
    " allow_patterns=json.loads(sys.argv[4]))\n"
)


def setup_bases(*, root: Path | None = None, run: Callable[..., Any] = subprocess.run,
                adopt: Mapping[str, Path] | None = None, verify_weights: bool = True,
                dry_run: bool = False) -> dict[str, Any]:
    """Record the two pinned bases: adopted in place (verified, never moved) or downloaded at
    their pinned revisions into the data root, every file checked by size and SHA-256."""

    from learnloop.local_embeddings.student_trainer import base_problems

    root = root or pins.data_root()
    manifest, reason = load_manifest(root)
    plan = {name: {"repo": SP.STUDENT_BASES[name]["repo"], "revision": SP.STUDENT_BASES[name]["revision"],
                   "role": SP.STUDENT_BASES[name]["role"],
                   "bytes": sum(size for size, _d in SP.STUDENT_BASES[name]["files"].values()),
                   "dir": str((adopt or {}).get(name) or SP.base_dir(root, name)),
                   "adopt": name in (adopt or {})} for name in SP.SCREEN_BASES}
    out: dict[str, Any] = {"job": "query_student_setup", "bases": plan, "dropped": list(SP.DROPPED_BASES)}
    if manifest is None:
        return {**out, "status": "not_set_up", "reason": reason}
    if dry_run:
        return {**out, "status": "dry_run"}
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(root / "home"),
           "HF_HUB_DISABLE_TELEMETRY": "1"}
    recorded: dict[str, Any] = {}
    for name in SP.SCREEN_BASES:
        base = SP.STUDENT_BASES[name]
        directory = Path(plan[name]["dir"])
        if not plan[name]["adopt"] and base_problems(directory, base, verify_weights=False):
            directory.mkdir(parents=True, exist_ok=True)
            completed = run([manifest["env_python"], "-I", "-c", _DOWNLOAD, base["repo"], base["revision"],
                             str(directory), json.dumps(list(base["allow_patterns"]))],
                            capture_output=True, text=True, check=False, env=env)
            if completed.returncode != 0:
                return {**out, "status": "failed", "reason": f"the {name} download failed (exit {completed.returncode})"}
        problems = base_problems(directory, base, verify_weights=verify_weights)
        if problems:
            return {**out, "status": "failed", "reason": f"{name}: " + "; ".join(problems[:5])}
        recorded[name] = {"dir": str(directory), "repo": base["repo"], "revision": base["revision"],
                          "adopted": bool(plan[name]["adopt"]), "weights_verified": bool(verify_weights)}
    _write_json(SP.bases_manifest_path(root), {"version": 1, "bases": recorded,
                                               "recorded_at": datetime.now(timezone.utc).isoformat()})
    return {**out, "status": "ready", "recorded": recorded}


# -- 3. teacher targets and the leakage screen ---------------------------------------------------------------
def _sha(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def bank_fingerprint(bank: Sequence[Mapping[str, Any]]) -> str:
    """The bank's identity: every question's id, retrieval text and labels (evidence sets, answer
    spans and the judged blocks, when the bank records them)."""

    return _sha([[str(q["query_id"]), q["text"], [[list(ref) for ref in required] for required in q["evidence_sets"]],
                  [list(ref) for ref in q.get("answer_spans") or []],
                  None if q.get("judged") is None else [list(ref) for ref in q["judged"]]]
                 for q in sorted(bank, key=lambda q: q["query_id"])])


def targets_index(space_home: Path) -> dict[str, Any]:
    value = _read_json(space_home / "targets" / "index.json", {})
    for key in ("queries", "bank", "bank_text", "dropped", "shards", "screen"):
        value.setdefault(key, {})
    return value


def teacher_vectors(space_home: Path, ids: Sequence[str], *, kind: str = "queries") -> dict[str, np.ndarray]:
    """``{id: unit float32 vector}`` from the int8 shards (rows that never arrived are absent)."""

    return teacher_vectors_from(targets_index(space_home), space_home / "targets", [str(i) for i in ids], kind)


def all_rows(root: Path, space: str) -> list[dict[str, Any]]:
    """Every stored question of every vault for this space."""

    rows = []
    for directory in sorted((home(root, space) / "data").glob("*")):
        rows.extend(D.stored_queries(directory))
    return rows


def missing_bank_targets(index: Mapping[str, Any], bank: Sequence[Mapping[str, Any]]) -> list[str]:
    """Bank questions with no teacher vector for their CURRENT text."""

    return [str(q["query_id"]) for q in bank
            if str(q["query_id"]) not in index["bank"] or index["bank_text"].get(str(q["query_id"])) != _sha(q["text"])]


def screen_current(index: Mapping[str, Any], bank: Sequence[Mapping[str, Any]]) -> bool:
    return (index["screen"].get("bank_fingerprint") == bank_fingerprint(bank)
            and not missing_bank_targets(index, bank))


def screen_leakage(index: dict[str, Any], targets_dir: Path, rows: Sequence[Mapping[str, Any]],
                   bank: Sequence[Mapping[str, Any]]) -> bool:
    """The teacher-cosine leakage guard (keep, may only tighten), bound to ONE complete bank
    (Codex review F2): it runs only when every question of this bank has its teacher vector,
    screens every synthetic question that has a target against all of them, and records the
    bank's fingerprint with the screened ids. A question is admitted to training only when this
    bank screened it (:func:`eligible_rows`); a partial run screens nothing."""

    if missing_bank_targets(index, bank):
        return False
    bank_vectors = teacher_vectors_from(index, targets_dir, [str(q["query_id"]) for q in bank], "bank")
    if len(bank_vectors) < len(bank):
        return False
    matrix = np.stack(list(bank_vectors.values()))
    fresh = teacher_vectors_from(index, targets_dir, [str(row["id"]) for row in rows if row["id"] in index["queries"]],
                                 "queries")
    dropped: dict[str, float] = {}
    for identity, vector in fresh.items():
        highest = float(np.max(matrix @ vector))
        if highest >= SP.LEAKAGE_MAX_TEACHER_COS:
            dropped[identity] = round(highest, 4)
    index["dropped"] = dropped
    index["screen"] = {"bank_fingerprint": bank_fingerprint(bank), "bank_questions": len(bank),
                       "screened": sorted(fresh), "at": datetime.now(timezone.utc).isoformat()}
    return True


def eligible_rows(rows: Sequence[Mapping[str, Any]], index: Mapping[str, Any],
                  bank: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """THE admission rule, shared by training and evaluation (Codex review F2, F7): a question
    with a teacher target that this bank's complete leakage screen passed. Nothing is eligible
    while the bank's targets or its screen are incomplete."""

    if not screen_current(index, bank):
        return []
    screened = set(index["screen"].get("screened") or ())
    return [dict(row) for row in rows
            if row["id"] in index["queries"] and row["id"] in screened and row["id"] not in index["dropped"]]


def run_targets(vault: LoadedVault, repository: Repository, *, bank_path: Path | None, root: Path | None = None,
                launcher: Callable[..., dict[str, Any]] | None = None, meter: GpuMeter | None = None,
                preflight: Callable[[], list[str]] | None = None, locks: Callable[[], Any] = gpu_locks,
                dry_run: bool = False, yielder: Callable[[], Any] | None = None) -> dict[str, Any]:
    """One 9B batch in query mode for every question and bank question still owed a target."""

    root = root or pins.data_root()
    manifest, space, reason = context(vault, root)
    out: dict[str, Any] = {"job": "query_student_targets"}
    if manifest is None:
        return {**out, "status": "disabled", "reason": reason}
    if bank_path is None:
        return {**out, "status": "refused", "reason": "the bank is required (--bank): its questions are the "
                                                      "teacher-cosine leakage guard"}
    space_home = home(root, space)
    targets_dir = space_home / "targets"
    bank = D.load_bank(bank_path)
    index = targets_index(space_home)
    rows = all_rows(root, space)
    owed = [row for row in rows if row["id"] not in index["queries"]]
    missing = set(missing_bank_targets(index, bank))
    bank_owed = [question for question in bank if str(question["query_id"]) in missing]
    meter = meter or p2_meter(root, space)
    seconds = (len(owed) + len(bank_owed)) * 0.018 + 25.0
    out.update(space_id=space, questions=len(rows), owed=len(owed), bank_owed=len(bank_owed),
               bank_fingerprint=bank_fingerprint(bank),
               estimate={"gpu_minutes": round(seconds / 60, 1),
                         "basis": "E1: 18 ms per query (batch one, BF16, resident) plus the 25 s load"},
               meter=meter.report())
    if not owed and not bank_owed:
        if dry_run:
            return {**out, "status": "dry_run" if not screen_current(index, bank) else "complete"}
        if not screen_current(index, bank):
            screen_leakage(index, targets_dir, rows, bank)
            _write_json(targets_dir / "index.json", index)
        return {**out, "status": "complete", "leakage_dropped_by_teacher_cos": len(index["dropped"]),
                "screened": len(index["screen"].get("screened") or ())}
    if dry_run:
        return {**out, "status": "dry_run"}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        stored = (known_spaces(connection).get(space) or {}).get("canaries")
    if not stored:
        return {**out, "status": "refused", "reason": "index this vault's local space first (`learnloop embeddings "
                                                      "local index`): the targets' canaries are checked against "
                                                      "the space's stored ones"}
    out["students_yielded"] = exclusive_gpu_yield(yielder, preflight)
    problems = (preflight or preflight_problems)()
    if problems:
        return {**out, "status": "waiting_for_gpu", "reason": "; ".join(problems)}
    run_id = uuid4().hex
    job, _targets = build_job([], manifest=manifest, plan_id=f"p2targets_{run_id[:16]}")
    targets_dir.mkdir(parents=True, exist_ok=True)
    shards = []
    taken = set(index["shards"])

    def shard_name(prefix: str) -> str:
        number = 0
        while f"{prefix}{number:04d}" in taken:
            number += 1
        taken.add(f"{prefix}{number:04d}")
        return f"{prefix}{number:04d}"

    plan: dict[str, tuple[str, list[str]]] = {}
    texts: dict[str, str] = {}
    for kind, items, key in (("queries", owed, "id"), ("bank", bank_owed, "query_id")):
        for start in range(0, len(items), SHARD_SIZE):
            chunk = items[start:start + SHARD_SIZE]
            name = shard_name("q" if kind == "queries" else "b")
            plan[name] = (kind, [str(item[key]) for item in chunk])
            texts.update({str(item[key]): item["text"] for item in chunk})
            shards.append({"name": name, "path": str(targets_dir / f"{name}.npy"),
                           "queries": [{"id": str(item[key]), "text": item["text"]} for item in chunk]})
    job["query_shards"] = shards
    run = launcher or ScopedLauncher(Path(manifest["env_python"]))
    try:
        with locks():
            output = run(job, root / "runs" / run_id, meter=meter, plan_id=job["plan_id"])
    except (LocksBusy, GpuBudgetExceeded) as exc:
        return {**out, "status": "waiting_for_gpu", "reason": str(exc)}
    out["worker"] = {key: output.get(key) for key in ("status", "reason", "peaks", "unload", "supervised")}
    if output.get("canaries") is None:
        return {**out, "status": "worker_" + str(output.get("status")), "reason": output.get("reason")}
    if measured_epoch(output.get("load")) != epoch_of(manifest):
        return {**out, "status": "epoch_changed", "reason": "the worker's software epoch differs from setup's (a new "
                                                            "space): nothing kept"}
    check = canary_check(output.get("canaries"), stored)
    out["canaries"] = check
    if not check["ok"]:
        return {**out, "status": "epoch_drift", "reason": check["reason"]}
    kept = {"queries": 0, "bank": 0, "errors": 0}
    for name, (kind, ids) in plan.items():
        result = (output.get("query_shards") or {}).get(name)
        if result is None or not (targets_dir / f"{name}.npy").is_file():
            continue
        errors = result.get("errors") or {}
        for row, identity in enumerate(ids):
            if identity in errors:
                kept["errors"] += 1
                continue
            index[kind][identity] = [name, row]
            if kind == "bank":
                index["bank_text"][identity] = _sha(texts[identity])
            kept[kind] += 1
        index["shards"][name] = {"kind": kind, "rows": len(ids), "latency_p50_s": result.get("latency_p50_s")}
    screened = screen_leakage(index, targets_dir, rows, bank)
    _write_json(targets_dir / "index.json", index)
    complete = output.get("status") == "complete" and not kept["errors"] and screened
    return {**out, "status": "complete" if complete else "partial", "kept": kept,
            "leakage_screen": {"complete": screened, "bank_fingerprint": bank_fingerprint(bank),
                               "bank_targets_missing": len(missing_bank_targets(index, bank))},
            "leakage_dropped_by_teacher_cos": len(index["dropped"]) if screened else None, "meter": meter.report()}


def teacher_vectors_from(index: Mapping[str, Any], targets_dir: Path, ids: Sequence[str], kind: str) -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    by_shard: dict[str, list[tuple[str, int]]] = {}
    for identity in ids:
        place = index[kind].get(identity)
        if place:
            by_shard.setdefault(str(place[0]), []).append((identity, int(place[1])))
    for shard, rows in by_shard.items():
        array = np.load(targets_dir / f"{shard}.npy", mmap_mode="r")
        for identity, row in rows:
            vector = np.asarray(array[row], dtype=np.float32)
            norm = float(np.linalg.norm(vector))
            if norm:
                out[identity] = vector / norm
    return out


# -- documents (the vault's own local index) ---------------------------------------------------------------
def _documents(vault: LoadedVault, repository: Repository, space: str, *, exclude: Set[tuple[str, str]] = frozenset(),
               extraction_ids: Sequence[str] | None = None) -> tuple[list[str], np.ndarray, list[str], int]:
    """``(record ids, unit float32 matrix, each row's extraction, blocks left out as bank-tainted)``.

    A grouped (contextual) window that holds an ``exclude`` span taints EVERY member's vector: each
    was encoded with that span in its context (Codex review F3), so all of them are left out, not
    only the span's own row."""

    current = sorted(current_extractions(repository))
    wanted = current if extraction_ids is None else [e for e in current if e in set(extraction_ids)]
    windows = windows_by_extraction(vault, repository, wanted, ("grouped",))
    cache = VectorCache(cache_path(vault.root, space))
    ids, rows, sources = [], [], []
    tainted_count = 0
    for (extraction_id, _variant), found in sorted(windows.items()):
        tainted = {member.span_id for window in found
                   if any((extraction_id, other.span_id) in exclude for other in window.members)
                   for member in window.members}
        keys = expected_keys(space, found)
        try:
            vectors = cache.vectors(key for parts in keys.values() for key, _w in parts)
        except CacheUnreadable:
            continue
        for span_id, parts in sorted(keys.items()):
            if span_id in tainted or (extraction_id, span_id) in exclude:
                tainted_count += 1
                continue
            if not all(key in vectors for key, _w in parts):
                continue
            vector = (vectors[parts[0][0]] if len(parts) == 1 else
                      np.asarray(mean_vector([vectors[key] for key, _w in parts], [w for _k, w in parts])))
            norm = float(np.linalg.norm(vector))
            if norm:
                ids.append(block_record_id(extraction_id, span_id))
                rows.append(np.asarray(vector, dtype=np.float32) / norm)
                sources.append(extraction_id)
    matrix = np.stack(rows) if rows else np.zeros((0, SP.STUDENT_DIMENSIONS), dtype=np.float32)
    return ids, matrix, sources, tainted_count


def documents(vault: LoadedVault, repository: Repository, space: str, *,
              exclude: Set[tuple[str, str]] = frozenset(),
              extraction_ids: Sequence[str] | None = None) -> tuple[list[str], np.ndarray]:
    """The grouped space's current covered blocks: ``(record ids, unit float32 matrix)``."""

    ids, matrix, _sources, _tainted = _documents(vault, repository, space, exclude=exclude,
                                                 extraction_ids=extraction_ids)
    return ids, matrix


def training_candidates(vault: LoadedVault, repository: Repository, space: str, *, bank: Sequence[Mapping[str, Any]],
                        rows: Sequence[Mapping[str, Any]], by_extraction: Mapping[str, str]) -> dict[str, Any]:
    """The permitted training candidate manifest (Codex review F3): the covered blocks of the
    TRAINING families only (no held-out family, no source without training questions), with every
    contextual window that holds a bank support left out. The KD top-k and the multi-positive
    term's hard negatives are mined from it alone."""

    held = {str(row["family"]) for row in rows if row["split"] == "heldout"}
    trained = {str(row["family"]) for row in rows if row["split"] in ("train", "dev")} - held
    extraction_ids = sorted(e for e, family in by_extraction.items() if family in trained)
    ids, matrix, sources, tainted = _documents(vault, repository, space, exclude=D.bank_supports(bank),
                                               extraction_ids=extraction_ids)
    return {"ids": ids, "matrix": matrix, "sources": sources, "families": sorted(trained), "held_out": sorted(held),
            "extractions": extraction_ids, "bank_tainted_blocks": tainted, "fingerprint": _sha(ids)}


def complete_evidence(ranked: Sequence[str], sets: Sequence[Sequence[tuple[str, str]]], k: int = 10) -> float | None:
    """1 when some evidence set's every required block is in the top ``k``, 0 when none is, None when unlabelled."""

    if not sets:
        return None
    top = set(ranked[:k])
    return 1.0 if any(all(block_record_id(e, s) in top for e, s in required) for required in sets if required) else 0.0


def unjudged_blocks(ranked: Sequence[str], question: Mapping[str, Any], k: int = 10) -> list[str]:
    """The top ``k``'s blocks the label protocol never judged for this question: neither in an
    evidence set nor in the bank's ``judged`` list (a bank without one judged nothing else)."""

    known = {block_record_id(e, s) for e, s in question.get("judged") or []} | {
        block_record_id(e, s) for required in question["evidence_sets"] for e, s in required}
    return [record for record in ranked[:k] if record not in known]


def judged_outcome(ranked: Sequence[str], question: Mapping[str, Any], k: int = 10) -> float | None:
    """Complete evidence, with unjudged material latent (Codex review F5, re-review F5, spec §9.1):
    when no set completes but the top ``k`` holds a block the label protocol never judged for this
    question, that block may be another complete set: the outcome is unknown (None, imputed by the
    posterior and listed for labelling), never a miss. A bank without ``judged`` lists judged only
    its evidence, so every other retrieved block is unjudged."""

    value = complete_evidence(ranked, question["evidence_sets"], k)
    if value == 0.0 and unjudged_blocks(ranked, question, k):
        return None
    return value


# -- 4. datasets and the schedule ---------------------------------------------------------------------------
def _ledger_path(space_home: Path) -> Path:
    return space_home / "p2-ledger.json"


def read_ledger(space_home: Path) -> dict[str, Any]:
    return _read_json(_ledger_path(space_home), {"version": 1, "runs": {}, "decisions": []})


def effective_budgets(n_train: int) -> list[int]:
    """The nested budgets the data allows today (a budget above the data is the data)."""

    return sorted({min(budget, n_train) for budget in SP.BUDGETS if min(budget, n_train) > 0})


def _spec_key(spec: Mapping[str, Any]) -> str:
    # Codex review F9: a run is reused only on the dataset it learned (vault, bank, splits, candidates).
    return f"{spec['base']}|{spec['recipe']}|{spec['budget']}|{spec['seed']}|{spec.get('dataset') or ''}"


def _completed(ledger: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {_spec_key(run["spec"]): run for run in ledger["runs"].values() if run.get("status") == "complete"}


def _tried(ledger: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {_spec_key(run["spec"]): run for run in ledger["runs"].values()}


def teacher_quality(space_home: Path, *, seed: int = 0) -> tuple[np.ndarray, str]:
    """The teacher's bank quality draws: its evaluated outcomes when evaluation ran, else E1's committed aggregates."""

    stored = _read_json(space_home / "evaluation" / "teacher_outcomes.json", None)
    if stored:
        arm = SD.ArmOutcomes("teacher", stored["outcomes"], stored["families"])
        return SD.bank_quality_draws(arm, seed=seed), "bank (evaluated)"
    return SD.bank_quality_draws(SD.aggregate_arm("teacher", E1_AGGREGATES["teacher"]), seed=seed), \
        "legacy: E1's committed V2_grouped aggregates"


# -- the owner's exchange rates (lambda, nu), learned from every costed owner choice ------------------------
def _rates_path(space_home: Path) -> Path:
    return space_home / "rates.json"


def exchange_rates(space_home: Path, mu: float) -> tuple[SD.ExchangeRate, SD.ExchangeRate]:
    """``(lambda, nu)``: the seeded priors (``student_decision.PRIOR_BASIS``) updated by every
    recorded owner choice (Codex review F14). The SAME posteriors serve the screen, the
    continuation rule and the adoption recommendation."""

    stored = _read_json(_rates_path(space_home), {})
    lam = SD.seeded_lambda()
    lam.observations = [dict(item) for item in stored.get("lambda") or []]
    nu = SD.seeded_nu(mu, SP.P2_GPU_HOURS_CAP, lam)
    nu.observations = [dict(item) for item in stored.get("nu") or []]
    return lam, nu


def record_owner_choice(space_home: Path, *, rate: str, dq: float, cost: float, s: float, accepted: bool,
                        what: str, judgment_id: str | None = None) -> dict[str, Any]:
    """One costed owner choice, an observation of ``rate`` (``lambda``: quality per dollar;
    ``nu``: quality per GPU-hour) in the logistic choice model ``P(accept) = sigma((dq - rate *
    cost) / s)`` (spec §9.1: "every owner decision between costed options is an observation")."""

    if rate not in ("lambda", "nu"):
        raise ValueError("rate is lambda or nu")
    stored = _read_json(_rates_path(space_home), {})
    item = {"dq": float(dq), "cost": float(cost), "s": float(s), "accepted": bool(accepted), "what": what,
            "judgment_id": judgment_id, "at": datetime.now(timezone.utc).isoformat()}
    stored.setdefault(rate, []).append(item)
    _write_json(_rates_path(space_home), stored)
    return item


def _late_counts(run: Mapping[str, Any], box_s: float) -> tuple[int, int]:
    samples = [value for device in (run.get("latency") or {}).values() for value in device.get("seconds") or []]
    samples.append(float(run.get("load_s") or 0.0))  # the cold-start proxy until real starts are measured
    return sum(1 for value in samples if value > box_s), len(samples)


def run_actions(runs: Sequence[Mapping[str, Any]], *, teacher_q: np.ndarray, box_s: float) -> list[SD.Action]:
    actions = []
    for index, run in enumerate(runs):
        late, total = _late_counts(run, box_s)
        actions.append(SD.Action(
            run["run_id"], SD.dev_quality_draws(run["dev"]["agreements"], teacher_q, seed=index + 1),
            late=SD.late_draws(late, total, seed=index + 101)))
    return actions


def choose(runs: Sequence[Mapping[str, Any]], *, teacher_q: np.ndarray, box_s: float, mu: float,
           lam: SD.ExchangeRate | None = None) -> dict[str, Any]:
    lam = lam or SD.seeded_lambda()
    return SD.decide(run_actions(runs, teacher_q=teacher_q, box_s=box_s), lam=lam.draws(len(teacher_q)), mu=mu)


def next_step(ledger: Mapping[str, Any], *, n_train: int, has_positives: bool, teacher_q: np.ndarray, box_s: float,
              hours_left: float, dataset: str = "", lam: SD.ExchangeRate | None = None,
              nu: SD.ExchangeRate | None = None) -> dict[str, Any]:
    """The schedule's next run, or ``{"step": "evaluate", ...}`` when the chosen recipe has its seeds."""

    budgets = effective_budgets(n_train)
    if not budgets:
        return {"step": "blocked", "reason": "no training question has a teacher target yet (generate, then targets)"}
    screen_budget = budgets[1] if len(budgets) > 1 else budgets[0]
    done, tried = _completed(ledger), _tried(ledger)
    mu = float(np.mean(teacher_q))
    lam = lam or SD.seeded_lambda()
    nu_mean = (nu or SD.seeded_nu(mu, SP.P2_GPU_HOURS_CAP, lam)).mean()

    def spec(base: str, recipe: str, budget: int, seed: int) -> dict[str, Any]:
        return {"base": base, "recipe": recipe, "budget": budget, "seed": seed, "dataset": dataset}

    def pending(specs: Sequence[dict[str, Any]], stage: str) -> dict[str, Any] | None:
        for item in specs:
            key = _spec_key(item)
            if key in done:
                continue
            if key in tried:
                return {"step": "blocked", "stage": stage, "spec": item,
                        "reason": f"run {tried[key]['run_id']} ended {tried[key].get('status')}: "
                                  f"{tried[key].get('reason') or ''}"[:300]}
            return {"step": "train", "stage": stage, "spec": item}
        return None

    screen = [spec(SP.PRIMARY_BASE, "projection_only", screen_budget, 0), spec(SP.PRIMARY_BASE, "align", screen_budget, 0)] + \
             [spec(base, "align", screen_budget, 0) for base in SP.SCREEN_BASES if base != SP.PRIMARY_BASE]
    step = pending(screen, "screen")
    if step:
        return step
    screen_runs = [done[_spec_key(item)] for item in screen]
    decision = choose(screen_runs, teacher_q=teacher_q, box_s=box_s, mu=mu, lam=lam)
    chosen_base = next(run["spec"]["base"] for run in screen_runs if run["run_id"] == decision["chosen"])
    recipes = [spec(chosen_base, "align_kd", screen_budget, 0)]
    if has_positives:
        recipes.append(spec(chosen_base, "align_kd_mp", screen_budget, 0))
    step = pending(recipes, "recipes")
    if step:
        return {**step, "screen_decision": decision}
    candidates = [run for run in screen_runs if run["spec"]["base"] == chosen_base] + \
                 [done[_spec_key(item)] for item in recipes]
    recipe_decision = choose(candidates, teacher_q=teacher_q, box_s=box_s, mu=mu, lam=lam)
    chosen_recipe = next(run["spec"]["recipe"] for run in candidates if run["run_id"] == recipe_decision["chosen"])
    final_budget = screen_budget
    if budgets[0] < screen_budget:
        curve = [spec(chosen_base, chosen_recipe, budgets[0], 0)]
        step = pending(curve, "learning_curve")
        if step:
            return {**step, "recipe_decision": recipe_decision}
    if budgets[-1] > screen_budget:
        large = spec(chosen_base, chosen_recipe, budgets[-1], 0)
        if _spec_key(large) not in done:
            points = []
            for budget in budgets:
                run = done.get(_spec_key({**large, "budget": budget}))
                if run is not None:
                    values = np.asarray(run["dev"]["agreements"], dtype=float)
                    se = float(values.std(ddof=1) / math.sqrt(len(values))) if len(values) > 1 else 0.5
                    points.append((budget, float(values.mean()), se))
            measured = done[_spec_key({**large, "budget": screen_budget})]
            hours = (float(measured.get("charged_s") or 0.0) / 3600.0) * budgets[-1] / screen_budget
            rule = SD.continue_training(points, budgets[-1], hours=hours, hours_left=hours_left,
                                        teacher_quality=mu, nu=nu_mean)
            if rule["continue"]:
                return {"step": "train", "stage": "learning_curve", "spec": large, "continue_rule": rule}
            final_budget = screen_budget
        else:
            same = [done[_spec_key({**large, "budget": budget})] for budget in (screen_budget, budgets[-1])]
            budget_decision = choose(same, teacher_q=teacher_q, box_s=box_s, mu=mu, lam=lam)
            final_budget = next(run["spec"]["budget"] for run in same if run["run_id"] == budget_decision["chosen"])
    seeds = [spec(chosen_base, chosen_recipe, final_budget, seed) for seed in range(SP.FINAL_SEEDS)]
    step = pending(seeds, "seeds")
    if step:
        return step
    final = [done[_spec_key(item)] for item in seeds]
    seed_decision = choose(final, teacher_q=teacher_q, box_s=box_s, mu=mu, lam=lam)
    candidate = next(run for run in final if run["run_id"] == seed_decision["chosen"])
    spread = [float(np.mean(run["dev"]["agreements"])) for run in final]
    return {"step": "evaluate", "candidate": candidate["run_id"], "checkpoint_sha256": candidate["checkpoint_sha256"],
            "spec": candidate["spec"], "seed_decision": seed_decision,
            "seed_agreements": [round(value, 4) for value in spread]}


def _vault_rows(root: Path, space: str, vault: LoadedVault) -> list[dict[str, Any]]:
    return D.stored_queries(D.data_dir(root, space, vault))


def campaign(vault: LoadedVault, repository: Repository, *, root: Path, space: str,
             bank: Sequence[Mapping[str, Any]], persist: bool = True) -> dict[str, Any]:
    """One vault's training campaign against one bank (Codex review F7, F8, F9): the eligible
    questions (:func:`eligible_rows`), their families in the vault's persisted family mapping,
    the permitted training candidates, and the dataset fingerprint that names every run and
    checkpoint made from them. A campaign belongs to ONE vault: another vault, another bank,
    other splits or other candidates are another dataset, and no run is reused across them.
    ``persist=False`` (the dry runs, re-review F18) reads the family mapping and writes nothing."""

    space_home = home(root, space)
    index = targets_index(space_home)
    families = D.family_map(D.data_dir(root, space, vault), repository, persist=persist)
    by_extraction = D.extraction_families(repository, families)
    held_out = D.vault_held_out(by_extraction)
    # Spec §7, F19: each row's family and split under the CURRENT mapping and hold-out.
    rows = D.current_rows(eligible_rows(_vault_rows(root, space, vault), index, bank), by_extraction)
    candidates = (training_candidates(vault, repository, space, bank=bank, rows=rows, by_extraction=by_extraction)
                  if rows else {"ids": [], "matrix": np.zeros((0, SP.STUDENT_DIMENSIONS), np.float32), "sources": [],
                                "families": [], "held_out": [], "extractions": [], "bank_tainted_blocks": 0,
                                "fingerprint": _sha([])})
    fingerprint = _sha({"vault": D.vault_key(vault), "space": space, "bank": bank_fingerprint(bank),
                        "rows": sorted([row["id"], row["split"], row["rank"], row["family"]] for row in rows),
                        "candidates": candidates["fingerprint"], "families": sorted(families.items())})
    return {"index": index, "rows": rows, "by_extraction": by_extraction, "candidates": candidates,
            "held_out_family": held_out,
            "fingerprint": fingerprint, "bank_fingerprint": bank_fingerprint(bank),
            "bank_missing": missing_bank_targets(index, bank), "screen_current": screen_current(index, bank),
            "n_train": sum(1 for row in rows if row["split"] == "train"),
            "has_positives": any(row["supports"] for row in rows if row["split"] == "train")}


def _incomplete_bank(camp: Mapping[str, Any]) -> str | None:
    if camp["bank_missing"]:
        return (f"{len(camp['bank_missing'])} bank question(s) have no teacher target: run `student targets` with "
                "this bank first (nothing trains or is evaluated until its leakage screen is complete)")
    if not camp["screen_current"]:
        return "the leakage screen is for another bank: run `student targets` with this bank first"
    return None


def build_dataset(vault: LoadedVault, repository: Repository, *, root: Path, space: str, budget: int,
                  bank_path: Path, out_dir: Path, camp: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """The run's files: the nested training budget, the development split, the permitted training
    candidates and the teacher's top-k over them (no held-out family, no bank-tainted window,
    Codex review F3), each query's same-source hard negatives, the temperature."""

    space_home = home(root, space)
    camp = camp or campaign(vault, repository, root=root, space=space, bank=D.load_bank(bank_path))
    candidates = camp["candidates"]
    record_ids, matrix, sources = candidates["ids"], candidates["matrix"], candidates["sources"]
    if not record_ids:
        raise ValueError("no permitted training candidate: index the vault's training families first")
    position = {record_id: row for row, record_id in enumerate(record_ids)}
    train, dev = _consumed_queries(camp, budget)
    out_dir.mkdir(parents=True, exist_ok=True)
    stats: dict[str, Any] = {"documents": len(record_ids), "train": len(train), "dev": len(dev),
                             "candidate_families": len(candidates["families"]),
                             "held_out_families_excluded": len(candidates["held_out"]),
                             "bank_tainted_blocks_excluded": candidates["bank_tainted_blocks"],
                             "dataset_fingerprint": camp["fingerprint"],
                             "training_families": run_training_families(camp, budget)}
    k = min(SP.TEACHER_TOP_K, len(record_ids))
    spreads = []
    for split, items in (("train", train), ("dev", dev)):
        vectors = teacher_vectors(space_home, [row["id"] for row in items])
        items = [row for row in items if row["id"] in vectors]
        targets = np.stack([vectors[row["id"]] for row in items]) if items else np.zeros((0, matrix.shape[1]), np.float32)
        scores = targets @ matrix.T if len(items) else np.zeros((0, len(record_ids)))
        topk = np.argsort(-scores, axis=1)[:, :k].astype(np.int32) if len(items) else np.zeros((0, k), np.int32)
        if split == "dev" and len(items):
            spreads.extend(np.take_along_axis(scores, topk.astype(np.int64), axis=1).std(axis=1).tolist())
        positives = [[position[block_record_id(row["extraction_id"], span)] for span in row["supports"]
                      if block_record_id(row["extraction_id"], span) in position] for row in items]
        # Spec §7.1: in-sequence SAME-SOURCE hard negatives, from the training candidates only.
        negatives = [[int(index) for index in topk[number] if sources[int(index)] == row["extraction_id"]]
                     for number, row in enumerate(items)]
        (out_dir / f"{split}_texts.json").write_text(json.dumps([row["text"] for row in items]), encoding="utf-8")
        np.save(out_dir / f"{split}_targets.npy", targets.astype(np.float16))
        np.save(out_dir / f"{split}_topk.npy", topk)
        (out_dir / f"{split}_positives.json").write_text(json.dumps(positives), encoding="utf-8")
        (out_dir / f"{split}_negatives.json").write_text(json.dumps(negatives), encoding="utf-8")
        stats[f"{split}_with_positives"] = sum(1 for item in positives if item)
    np.save(out_dir / "documents.npy", matrix.astype(np.float16))
    # Structural: a softmax temperature on the scale of the teacher's own top-k score spread.
    stats["temperature"] = round(max(float(np.median(spreads)) if spreads else 0.05, MIN_TEMPERATURE), 6)
    return stats


def trainer_job(spec: Mapping[str, Any], *, space: str, base_dir: Path, data_dir: Path, out_dir: Path,
                temperature: float, plan_id: str, dataset_fingerprint: str = "",
                training_families: Sequence[str] | None = None) -> dict[str, Any]:
    base = SP.STUDENT_BASES[spec["base"]]
    families = {} if training_families is None else {"training_families": sorted(map(str, training_families)),
                                                     "training_families_provenance": TRAINING_FAMILIES_PROVENANCE}
    return {**families, "version": SP.TRAINER_VERSION, "plan_id": plan_id, "space_id": space, "base_name": spec["base"],
            "base": {key: base[key] for key in ("repo", "revision", "pooling", "query_prefix", "hidden_size",
                                                "trust_remote_code", "files", "remote_code", "inert_python")},
            "base_dir": str(base_dir), "data_dir": str(data_dir), "out_dir": str(out_dir),
            "recipe": spec["recipe"], "seed": int(spec["seed"]), "budget": int(spec["budget"]),
            "dataset_fingerprint": str(dataset_fingerprint or spec.get("dataset") or ""),
            "dimensions": SP.STUDENT_DIMENSIONS, "precision": SP.STUDENT_PRECISION,
            "max_query_tokens": SP.MAX_QUERY_TOKENS, "epochs": SP.EPOCHS, "batch_size": SP.TRAIN_BATCH_SIZE,
            "learning_rate_full": SP.LEARNING_RATE_FULL, "learning_rate_head": SP.LEARNING_RATE_HEAD,
            "weight_decay": SP.WEIGHT_DECAY, "warmup_fraction": SP.WARMUP_FRACTION,
            "grad_clip_norm": SP.GRAD_CLIP_NORM, "temperature": float(temperature),
            "agreement_k": SP.AGREEMENT_K, "latency_probes": SP.LATENCY_PROBES,
            "canary_queries": list(SP.STUDENT_CANARY_QUERIES), "checkpoint_format": SP.CHECKPOINT_FORMAT,
            "verify_weights": False, "limits": pins.limits()}


def install_checkpoint(output: Mapping[str, Any], *, root: Path, space: str) -> str:
    """Pin the trained checkpoint by SHA-256 under the space and move it into place."""

    from learnloop.local_embeddings.student_trainer import checkpoint_digest, sha256_file

    staging = Path(str(output["checkpoint_dir"]))
    manifest = json.loads((staging / "student.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        if sha256_file(staging / name) != digest:
            raise ValueError(f"{name}: the checkpoint file does not match its recorded digest")
    if manifest.get("space_id") != space:
        raise ValueError("the checkpoint was trained for another space")
    sha = checkpoint_digest(manifest)
    target = checkpoint_dir(root, space, sha)
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staging), str(target))
    return sha


def run_next(vault: LoadedVault, repository: Repository, *, bank_path: Path | None, root: Path | None = None,
             launcher: Callable[..., dict[str, Any]] | None = None, meter: GpuMeter | None = None,
             preflight: Callable[[], list[str]] | None = None, locks: Callable[[], Any] = gpu_locks,
             dry_run: bool = False, yielder: Callable[[], Any] | None = None) -> dict[str, Any]:
    """Plan (and unless ``dry_run``, run) the schedule's next training run."""

    root = root or pins.data_root()
    manifest, space, reason = context(vault, root)
    out: dict[str, Any] = {"job": "query_student_train"}
    if manifest is None:
        return {**out, "status": "disabled", "reason": reason}
    if bank_path is None:
        return {**out, "status": "refused", "reason": "the bank is required (--bank): its gold supports are never "
                                                      "a training candidate"}
    bases = bases_manifest(root)
    if bases is None:
        return {**out, "status": "not_set_up", "reason": "run `learnloop embeddings local student setup` first"}
    space_home = home(root, space)
    camp = campaign(vault, repository, root=root, space=space, bank=D.load_bank(bank_path), persist=not dry_run)
    incomplete = _incomplete_bank(camp)
    if incomplete:
        return {**out, "status": "refused", "space_id": space, "reason": incomplete}
    ledger = read_ledger(space_home)
    meter = meter or p2_meter(root, space)
    teacher_q, basis = teacher_quality(space_home)
    lam, nu = exchange_rates(space_home, float(np.mean(teacher_q)))
    box = float(vault.config.source_retrieval.retrieval_timeout_seconds)
    step = next_step(ledger, n_train=camp["n_train"], has_positives=camp["has_positives"], teacher_q=teacher_q,
                     box_s=box, hours_left=(meter.remaining_s() or 0.0) / 3600.0, dataset=camp["fingerprint"],
                     lam=lam, nu=nu)
    out.update(space_id=space, step=step, teacher_quality_basis=basis, meter=meter.report(),
               budgets=effective_budgets(camp["n_train"]), dataset_fingerprint=camp["fingerprint"])
    if step["step"] != "train" or dry_run:
        return {**out, "status": "dry_run" if dry_run else step["step"]}
    spec = step["spec"]
    record = (bases.get("bases") or {}).get(spec["base"])
    if record is None:
        return {**out, "status": "not_set_up", "reason": f"the base {spec['base']} is not recorded (rerun setup)"}
    out["students_yielded"] = exclusive_gpu_yield(yielder, preflight)
    problems = (preflight or preflight_problems)()
    if problems:
        return {**out, "status": "waiting_for_gpu", "reason": "; ".join(problems)}
    run_id = uuid4().hex
    work = root / "runs" / run_id
    data = space_home / "runs" / run_id / "data"
    stats = build_dataset(vault, repository, root=root, space=space, budget=int(spec["budget"]), bank_path=bank_path,
                          out_dir=data, camp=camp)
    job = trainer_job(spec, space=space, base_dir=Path(record["dir"]), data_dir=data,
                      out_dir=space_home / "runs" / run_id, temperature=stats["temperature"],
                      plan_id=f"p2train_{run_id[:16]}", dataset_fingerprint=camp["fingerprint"],
                      training_families=stats["training_families"])
    from learnloop.local_embeddings import student_trainer

    run = launcher or ScopedLauncher(Path(manifest["env_python"]), script=Path(student_trainer.__file__),
                                     memory_max=SP.TRAIN_SCOPE_MEMORY_MAX, unit_prefix="learnloop-student-train")
    entry: dict[str, Any] = {"run_id": run_id, "spec": dict(spec), "stage": step["stage"], "dataset": stats,
                             "vault": D.vault_key(vault), "started_at": datetime.now(timezone.utc).isoformat()}
    try:
        with locks():
            output = run(job, work, meter=meter, plan_id=job["plan_id"])
    except (LocksBusy, GpuBudgetExceeded) as exc:
        return {**out, "status": "waiting_for_gpu", "reason": str(exc)}
    entry.update(status=output.get("status"), reason=output.get("reason"),
                 charged_s=(output.get("supervised") or {}).get("charged_s"))
    if output.get("status") == "complete":
        entry.update(dev=output["dev"], latency=output["latency"], load_s=output.get("load_s"),
                     train_s=output.get("train_s"), history=output.get("history"))
        entry["checkpoint_sha256"] = install_checkpoint(output, root=root, space=space)
    ledger["runs"][run_id] = entry
    _write_json(_ledger_path(space_home), ledger)
    # The data files carry book text and teacher vectors: kept only while the run is the record.
    shutil.rmtree(data, ignore_errors=True)
    return {**out, "status": "trained" if output.get("status") == "complete" else "run_" + str(output.get("status")),
            "run": {key: entry.get(key) for key in ("run_id", "spec", "stage", "status", "reason", "charged_s",
                                                    "checkpoint_sha256")},
            "dev": entry.get("dev", {}) and {key: entry["dev"][key] for key in ("queries", "median_cos",
                                                                                 "agreement_mean")},
            "meter": meter.report()}


# -- 5. evaluation, the recommendation, and the owner's adoption ----------------------------------------------
#: The label model behind the bank outcomes (Codex review F5, re-review F5). P0's §9.1 posterior
#: (Dawid-Skene label noise from the blinded passes and the adjudications) is not built; until a
#: stage supplies it, an evaluation RECOMMENDS and never changes the serving state: the owner
#: adopts, rejects or revokes, so this simplified posterior holds no authority alone.
LABEL_MODEL = ("simplified: per-arm family-pooled Beta posteriors, unknown and unjudged outcomes latent; "
               "no label-noise model (spec §9.1's Dawid-Skene posterior is owed by P0)")
PRIOR_ALTERNATIVE = ("prior: E1's committed aggregates (another corpus, other candidate units, the primary "
                     "development slice's denominator): reported for context, never an action in the decision")
#: Spec §9.1's value-of-information rule needs the next label batch's price, which P2 does not
#: record: the evaluation lists the owed labels and the expected loss, and acts on neither.
LABEL_ACQUISITION = ("owed by P0: spec §9.1 buys labels first when the expected loss of acting now exceeds "
                     "lambda x the next label batch's cost; no label price is recorded in P2, so the unjudged "
                     "retrieved blocks are listed for labelling and nothing acts on this posterior alone")
JUDGMENT_TASK = "query_student_adoption"


def _outcomes(bank: Sequence[Mapping[str, Any]], vectors: Mapping[str, np.ndarray], record_ids: Sequence[str],
              matrix: np.ndarray) -> tuple[dict[str, float | None], dict[str, list[str]]]:
    """``(outcomes, owed)``: each question's judged outcome, and for each latent one the
    retrieved blocks its label protocol never judged (what a label batch would judge)."""

    out: dict[str, float | None] = {}
    owed: dict[str, list[str]] = {}
    for question in bank:
        vector = vectors.get(question["query_id"])
        if vector is None:
            out[question["query_id"]] = None
            continue
        order = np.argsort(-(matrix @ np.asarray(vector, dtype=np.float32)))[:10]
        ranked = [record_ids[i] for i in order]
        out[question["query_id"]] = judged_outcome(ranked, question)
        if out[question["query_id"]] is None:
            owed[question["query_id"]] = unjudged_blocks(ranked, question)
    return out, owed


def comparison_fingerprint(bank_print: str, record_ids: Sequence[str], question_ids: Sequence[str]) -> str:
    """What makes two arms' outcomes comparable (re-review F4): the bank's labels (its
    fingerprint), the candidate units every arm ranks (the space's current block ids) and the
    in-scope questions. A supplied arm names it; ``student evaluate --dry-run`` prints it."""

    return _sha({"bank": bank_print, "units": _sha(list(record_ids)), "questions": sorted(question_ids)})


def _evaluation_candidate(ledger: Mapping[str, Any], step: Mapping[str, Any], adoption: Mapping[str, Any] | None,
                          checkpoint: str | None, *, root: Path, space: str
                          ) -> tuple[Mapping[str, Any] | None, str, str | None]:
    """``(run, basis, refusal)``: the checkpoint to evaluate (re-review F17). An explicit one
    (any completed run's), else the schedule's candidate on the current dataset, else the serving
    checkpoint: corrected labels (a new bank, so a new dataset) stop training reuse, never the
    evaluation of what already exists."""

    complete = {str(run["checkpoint_sha256"]): run for run in ledger["runs"].values()
                if run.get("status") == "complete" and run.get("checkpoint_sha256")}

    def present(sha: str) -> bool:
        return (checkpoint_dir(root, space, sha) / "student.json").is_file()

    if checkpoint:
        run = complete.get(checkpoint)
        if run is None or not present(checkpoint):
            return None, "explicit", (f"no completed run made the checkpoint {checkpoint[:12]}, or it is not present "
                                      "under the space")
        return run, "explicit", None
    if step.get("step") == "evaluate":
        return ledger["runs"][step["candidate"]], "schedule", None
    if adoption is not None:
        run = complete.get(str(adoption["checkpoint_sha256"]))
        if run is not None and present(str(adoption["checkpoint_sha256"])):
            return run, "serving", None
    return None, "", None


#: The producer of a pinned ``training_families`` list (F19 residual): a manifest pinned by any
#: other producer (the first F19 round pinned candidate families only, which could omit consumed
#: ones) is not provenance. Bump it whenever :func:`run_training_families` changes what it lists.
TRAINING_FAMILIES_PROVENANCE = "consumed-queries-and-candidates-v1"


def _consumed_queries(camp: Mapping[str, Any], budget: int) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    """``(train, dev)``: the queries a run at ``budget`` gives the trainer (the nested budget, the
    development split's first ``DEV_MAX`` by rank)."""

    rows = camp["rows"]
    dev = sorted((row for row in rows if row["split"] == "dev"), key=lambda row: row["rank"])[:DEV_MAX]
    return D.nested(rows, budget), dev


def run_training_families(camp: Mapping[str, Any], budget: int) -> list[str]:
    """Every family a run at ``budget`` on this campaign consumes (Codex final verify F19): its
    training and development queries' families and the families of the candidate blocks its KD
    top-k, positives and hard negatives come from (and the candidate manifest's own families).
    The trainer pins them in the checkpoint manifest; the current-dataset fallback derives the
    same set, so a family the run saw is never reported unseen."""

    train, dev = _consumed_queries(camp, budget)
    by_extraction = camp["by_extraction"]
    candidates = camp["candidates"]
    found = {str(row["family"]) for row in [*train, *dev]} | {str(family) for family in candidates["families"]}
    found |= {str(by_extraction[source]) for source in candidates["sources"] if source in by_extraction}
    return sorted(found)


def checkpoint_training_families(run: Mapping[str, Any], camp: Mapping[str, Any], *, root: Path, space: str
                                 ) -> tuple[set[str] | None, str]:
    """``(families, basis)``: the families the checkpoint actually trained on (F19). The pinned
    manifest's record when its digest still matches the pin and the current producer made it
    (``TRAINING_FAMILIES_PROVENANCE``: ``checkpoint_manifest``), else the
    families :func:`run_training_families` derives from the current campaign at the run's budget
    when the run was trained on this very dataset (its fingerprint names the rows' splits and
    families: ``current_dataset``), else ``(None, "unknown")``: no stratum then calls its
    questions seen or unseen."""

    from learnloop.local_embeddings.student_trainer import checkpoint_digest

    sha = str(run["checkpoint_sha256"])
    manifest = _read_json(checkpoint_dir(root, space, sha) / "student.json", None)
    if isinstance(manifest, dict) and isinstance(manifest.get("training_families"), list) and \
            manifest.get("training_families_provenance") == TRAINING_FAMILIES_PROVENANCE:
        try:
            pinned = checkpoint_digest(manifest) == sha
        except (KeyError, TypeError):
            pinned = False
        if pinned:
            return {str(family) for family in manifest["training_families"]}, "checkpoint_manifest"
    spec = run.get("spec") or {}
    if spec.get("dataset") == camp["fingerprint"] and spec.get("budget") is not None:
        return set(run_training_families(camp, int(spec["budget"]))), "current_dataset"
    return None, "unknown"


def _strata(bank: Sequence[Mapping[str, Any]], question_families: Mapping[str, set[str]],
            trained_families: set[str] | None) -> dict[str, set[str]]:
    """The reported strata. ``trained_families`` is the checkpoint's own snapshot (F19); None (no
    recoverable provenance) puts every question with a family under ``unknown_family``."""

    out = {"all": {q["query_id"] for q in bank},
           "deictic": {q["query_id"] for q in bank if q["deictic"]},
           "logged": {q["query_id"] for q in bank if q["origin"] == "logged"}}
    with_family = {q["query_id"] for q in bank if question_families.get(q["query_id"])}
    if trained_families is None:
        out["unknown_family"] = with_family
    else:
        out["unseen_family"] = {qid for qid in with_family if question_families[qid].isdisjoint(trained_families)}
    return out


def bank_scope(bank: Sequence[Mapping[str, Any]], repository: Repository) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """The questions every arm is scored on (Codex review F4): those whose every evidence and
    answer span lies in THIS vault's current corpus. A question about another vault's books is
    out of scope for every arm alike, never a miss for one of them."""

    current = set(current_extractions(repository))
    scoped, outside = [], {"no_evidence_set": 0, "another_corpus": 0}
    for question in bank:
        refs = [ref for required in question["evidence_sets"] for ref in required] + list(question["answer_spans"])
        if not question["evidence_sets"] or not refs:
            outside["no_evidence_set"] += 1
        elif all(str(ref[0]) in current for ref in refs):
            scoped.append(dict(question))
        else:
            outside["another_corpus"] += 1
    return scoped, outside


def _monthly_query_usd(repository: Repository) -> float:
    since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        try:
            value = connection.execute("SELECT COALESCE(SUM(cost), 0) FROM model_call_receipts WHERE owner_kind = "
                                       "'source_query_embedding' AND started_at >= ?", (since,)).fetchone()[0]
        except Exception:  # noqa: BLE001 - an older schema has no receipts table
            value = 0.0
    return float(value or 0.0)


def _judge(repository: Repository, *, checkpoint: str, space: str, judge: str, verdict: str,
           evidence: Mapping[str, Any], score: float | None = None) -> str:
    """An auditable verdict in ``judgment_ledger`` (handoff §0.6: every verifier or owner verdict;
    Codex review F15). The local ``adoption.json`` is only the serving pointer it materializes."""

    from learnloop.db.stores.judgments import append_judgment

    rationale = json.dumps(dict(evidence), sort_keys=True, default=str)
    with closing(connect(repository.sqlite_path)) as connection, connection:
        return append_judgment(connection, task=JUDGMENT_TASK, left_kind="query_student_checkpoint", left_id=checkpoint,
                               right_kind="retrieval_space", right_id=space, judge=judge,
                               input_hash=_sha(rationale), verdict=verdict, score=score,
                               prompt_version=SD.DECISION_VERSION, rationale=rationale)


def _withdraw(repository: Repository, *, root: Path, space: str, adoption: Mapping[str, Any], judge: str,
              why: str, evaluation_id: str | None = None, verdict: str = "withdrawn") -> str:
    """Remove the serving pointer (atomic) and record the verdict."""

    path = adoption_path(root, space)
    sha = str(adoption["checkpoint_sha256"])
    judgment = _judge(repository, checkpoint=sha, space=space, judge=judge, verdict=verdict,
                      evidence={"why": why, "evaluation_id": evaluation_id,
                                "adoption_judgment_id": adoption.get("judgment_id")})
    path.unlink(missing_ok=True)
    return judgment


def evaluate(vault: LoadedVault, repository: Repository, *, bank_path: Path | None, root: Path | None = None,
             encoder_factory: Callable[[str], Any] | None = None, arms: Mapping[str, Path] | None = None,
             dry_run: bool = False, checkpoint: str | None = None) -> dict[str, Any]:
    """A checkpoint on the bank beside the teacher (and any adopted incumbent), every arm on the
    same frozen questions, candidate units and labels; §9.3's expected utility over the MEASURED
    actions RECOMMENDS. The checkpoint is ``checkpoint`` (any completed run's), else the
    schedule's candidate, else the serving one, so a corrected bank re-evaluates what serves
    (re-review F17). E1's aggregates are priors, reported and never decided on, and a supplied arm
    must name this comparison's fingerprint (re-review F4). No evaluation changes the serving
    state: a losing re-evaluation RECOMMENDS withdrawal, and adopting, rejecting and revoking are
    the owner's until P0's label-noise posterior holds that authority (Codex review F5, re-review F5)."""

    from learnloop.source_retrieval.student_encoder import StudentEncoder, read_adoption

    root = root or pins.data_root()
    manifest, space, reason = context(vault, root)
    out: dict[str, Any] = {"job": "query_student_evaluate"}
    if manifest is None:
        return {**out, "status": "disabled", "reason": reason}
    if bank_path is None:
        return {**out, "status": "refused", "reason": "the labelled bank is required (--bank)"}
    space_home = home(root, space)
    ledger = read_ledger(space_home)
    bank = D.load_bank(bank_path)
    camp = campaign(vault, repository, root=root, space=space, bank=bank, persist=not dry_run)
    incomplete = _incomplete_bank(camp)
    if incomplete:
        return {**out, "status": "refused", "reason": incomplete}
    teacher_q, _basis = teacher_quality(space_home)
    lam, nu = exchange_rates(space_home, float(np.mean(teacher_q)))
    box = float(vault.config.source_retrieval.retrieval_timeout_seconds)
    meter = p2_meter(root, space)
    step = next_step(ledger, n_train=camp["n_train"], has_positives=camp["has_positives"], teacher_q=teacher_q,
                     box_s=box, hours_left=(meter.remaining_s() or 0.0) / 3600.0, dataset=camp["fingerprint"],
                     lam=lam, nu=nu)
    adoption = read_adoption(root, space)
    run, candidate_basis, refusal = _evaluation_candidate(ledger, step, adoption, checkpoint, root=root, space=space)
    if refusal:
        return {**out, "status": "refused", "reason": refusal}
    if run is None:
        return {**out, "status": "not_ready", "step": step}
    sha = str(run["checkpoint_sha256"])
    spec = dict(run["spec"])
    trained_here = spec.get("dataset") == camp["fingerprint"]
    out.update(space_id=space, candidate=run["run_id"], checkpoint_sha256=sha, spec=spec,
               candidate_basis=candidate_basis, trained_on_current_dataset=trained_here)
    scoped, outside = bank_scope(bank, repository)
    out["scope"] = {"questions": len(scoped), "outside": outside,
                    "splits": {s: sum(1 for q in scoped if q["split"] == s) for s in sorted({q["split"] for q in scoped})},
                    "strata": {s: sum(1 for q in scoped if q["stratum"] == s)
                               for s in sorted({q["stratum"] for q in scoped})}}
    if not scoped:
        return {**out, "status": "refused", "reason": "no bank question's evidence lies in this vault's corpus"}
    scoped_ids = [q["query_id"] for q in scoped]
    record_ids, matrix = documents(vault, repository, space)
    comparison = comparison_fingerprint(camp["bank_fingerprint"], record_ids, scoped_ids)
    out["comparison_fingerprint"] = comparison
    teacher = teacher_vectors_from(camp["index"], space_home / "targets", scoped_ids, "bank")
    question_families = {q["query_id"]: D.question_families(q, camp["by_extraction"]) for q in scoped}
    families = {qid: "|".join(sorted(found)) or "bank" for qid, found in question_families.items()}
    alternatives: dict[str, SD.ArmOutcomes] = {}
    sources: dict[str, str] = {}
    for name, path in (arms or {}).items():
        values = _read_json(Path(path), None)
        if not isinstance(values, dict) or values.get("comparison") != comparison or \
                not isinstance(values.get("outcomes"), dict):
            return {**out, "status": "refused",
                    "reason": f"--arm {name}: the file does not name this comparison ({comparison}): an alternative "
                              "is compared only when it was measured on the same bank labels, candidate units and "
                              "questions (`student evaluate --dry-run` prints the fingerprint; the file is "
                              "{\"comparison\": ..., \"outcomes\": {question id: 1, 0 or null}})"}
        values = values["outcomes"]
        missing = [qid for qid in scoped_ids if qid not in values]
        if missing:
            return {**out, "status": "refused",
                    "reason": f"--arm {name}: {len(missing)} of the {len(scoped_ids)} in-scope question(s) have no "
                              "outcome (null for unknown): an alternative is compared only on the same questions"}
        alternatives[name] = SD.ArmOutcomes(name, {qid: values[qid] for qid in scoped_ids}, families)
        sources[name] = "measured: supplied per-question outcomes on this comparison"
    priors = {name: {"basis": PRIOR_ALTERNATIVE,
                     "expected_quality": round(float(np.mean(SD.bank_quality_draws(
                         SD.aggregate_arm(name, E1_AGGREGATES[name]), seed=31 + i))), 4)}
              for i, name in enumerate(("qwen", "voyage")) if name not in alternatives}
    incumbent = None
    if adoption is not None and adoption["checkpoint_sha256"] != sha and \
            (checkpoint_dir(root, space, str(adoption["checkpoint_sha256"])) / "student.json").is_file():
        incumbent = str(adoption["checkpoint_sha256"])
    if dry_run:
        return {**out, "status": "dry_run", "bank_questions": len(bank), "alternatives": sources,
                "prior_alternatives": priors, "incumbent": incumbent}
    bases = bases_manifest(root) or {"bases": {}}
    base_of = {sha: spec["base"]}
    if incumbent:
        base_of[incumbent] = str(adoption.get("base_name") or "")
    if encoder_factory is None:
        missing_bases = sorted({name for name in base_of.values() if name not in bases["bases"]})
        if missing_bases:
            return {**out, "status": "not_set_up", "reason": f"the base(s) {', '.join(missing_bases)} are not recorded "
                                                            "(rerun setup)"}

        def encoder_factory(digest: str) -> Any:
            return StudentEncoder(vault, space_id=space, checkpoint_sha=digest,
                                  checkpoint=checkpoint_dir(root, space, digest), base_name=base_of[digest],
                                  base_dir=Path(bases["bases"][base_of[digest]]["dir"]),
                                  env_python=Path(manifest["env_python"]), data_root=root)
    started = datetime.now(timezone.utc)
    texts = [question["text"] for question in scoped]

    def encoded(digest: str) -> dict[str, np.ndarray]:
        vectors = encoder_factory(digest).encode(texts, deadline=None)
        return {question["query_id"]: np.asarray(vector, dtype=np.float32)
                for question, vector in zip(scoped, vectors, strict=True)}

    outcomes: dict[str, dict[str, float | None]] = {}
    owed: dict[str, dict[str, list[str]]] = {}
    outcomes["student"], owed["student"] = _outcomes(scoped, encoded(sha), record_ids, matrix)
    outcomes["teacher"], owed["teacher"] = _outcomes(scoped, teacher, record_ids, matrix)
    if incumbent:
        outcomes["incumbent"], owed["incumbent"] = _outcomes(scoped, encoded(incumbent), record_ids, matrix)
    _write_json(space_home / "evaluation" / "teacher_outcomes.json",
                {"outcomes": outcomes["teacher"], "families": families, "bank_fingerprint": camp["bank_fingerprint"]})
    trained, trained_basis = checkpoint_training_families(run, camp, root=root, space=space)
    training_families = {"basis": trained_basis, "families": None if trained is None else len(trained)}
    strata = {}
    for name, members in _strata(scoped, question_families, trained).items():
        if not members:
            continue
        draws = {arm: SD.bank_quality_draws(SD.ArmOutcomes(arm, {q: v for q, v in values.items() if q in members},
                                                           families), seed=7 + i)
                 for i, (arm, values) in enumerate(outcomes.items())
                 if any(v is not None for q, v in values.items() if q in members)}
        if {"student", "teacher"} <= set(draws):
            difference = draws["student"] - draws["teacher"]
            strata[name] = {"questions": len(members), "p_student_ge_teacher": round(float(np.mean(difference >= 0)), 4),
                            "difference_mean": round(float(difference.mean()), 4),
                            "difference_90": [round(float(np.quantile(difference, 0.05)), 4),
                                              round(float(np.quantile(difference, 0.95)), 4)]}
    student_q = SD.bank_quality_draws(SD.ArmOutcomes("student", outcomes["student"], families), seed=11)
    keyword = alternatives.pop("keyword", None)
    keyword_basis = sources.pop("keyword", None)
    dense_q = SD.bank_quality_draws(SD.ArmOutcomes("teacher", outcomes["teacher"], families), seed=12)
    mu = (dense_q - SD.bank_quality_draws(keyword, seed=13)) if keyword is not None else dense_q
    mu_basis = "bank: teacher minus keyword" if keyword is not None else "upper bound: the teacher's whole quality"
    starts = [float(value) for value in _read_json(checkpoint_dir(root, space, sha) / "start_times.json", [])]
    late, total = _late_counts(run, box)
    late += sum(1 for value in starts if value > box)
    total += len(starts)
    monthly = _monthly_query_usd(repository)
    actions = [SD.Action("student", student_q, monthly_usd=0.0, late=SD.late_draws(late, total, seed=21))]
    if incumbent:
        i_run = next((r for r in ledger["runs"].values() if r.get("checkpoint_sha256") == incumbent), {})
        i_late, i_total = _late_counts(i_run, box) if i_run else (0, 0)
        i_starts = [float(v) for v in _read_json(checkpoint_dir(root, space, incumbent) / "start_times.json", [])]
        actions.append(SD.Action("incumbent", SD.bank_quality_draws(
            SD.ArmOutcomes("incumbent", outcomes["incumbent"], families), seed=14), monthly_usd=0.0,
            late=SD.late_draws(i_late + sum(1 for v in i_starts if v > box), i_total + len(i_starts), seed=22)))
    # Only arms measured on THIS comparison are actions (re-review F4); E1's aggregates stay priors.
    for i, (name, arm) in enumerate(sorted(alternatives.items())):
        actions.append(SD.Action(name, SD.bank_quality_draws(arm, seed=31 + i), monthly_usd=monthly))
    lam_draws = lam.draws(seed=41)
    decision = SD.decide(actions, lam=lam_draws, mu=mu)
    chosen = decision["chosen"]
    rivals = [action for action in actions if action.name != "student"]
    choice = None
    if rivals:
        best = max(rivals, key=lambda action: decision["expected_utility"][action.name])
        choice = {"against": best.name, "dq": round(float(np.mean(student_q) - np.mean(best.quality)), 6),
                  "cost": round(0.0 - float(best.monthly_usd), 6),
                  "s": round(SD.difference_sd(student_q, best.quality), 6)}
        recommendation = "adopt" if chosen == "student" else ("keep_incumbent" if chosen == "incumbent"
                                                              else "keep_alternatives")
    else:
        recommendation = "unmeasured"  # nothing measured to compare against: the owner may still adopt
    latent = {arm: sum(1 for value in values.values() if value is None) for arm, values in outcomes.items()}
    latent.update({name: sum(1 for value in arm.outcomes.values() if value is None)
                   for name, arm in alternatives.items()})
    labels_owed = {qid: sorted({block for arm_owed in owed.values() for block in arm_owed.get(qid, [])})
                   for qid in sorted({qid for arm_owed in owed.values() for qid in arm_owed})}
    label_acquisition = {"latent_outcomes": latent, "questions_owed": len(labels_owed),
                         "expected_loss_now": decision["expected_loss_now"], "lambda_mean": round(lam.mean(), 6),
                         "decision": LABEL_ACQUISITION}
    authority = {"automatic": False, "serving_changes": "never by an evaluation: the owner adopts, rejects or revokes",
                 "comparable_alternatives": not priors, "unmeasured_alternatives": sorted(priors),
                 "label_model": LABEL_MODEL,
                 "rule": "spec §9.3 recommends (argmax E[U] over the measured actions); the owner adopts with "
                         "`student adopt` and withdraws with `student reject` / `student revoke` until P0's §9.1 "
                         "label-noise posterior and alternatives measured on these questions hold the authority"}
    evaluation_id = f"ev_{started.strftime('%Y%m%dT%H%M%S')}_{uuid4().hex[:8]}"
    evaluation_dir = space_home / "evaluation"
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    # The posterior draws, kept for audit (spec §9.1), with the seeds that made them.
    np.savez_compressed(evaluation_dir / f"{evaluation_id}.npz", lam=lam_draws, mu=np.asarray(mu, dtype=float),
                        **{f"quality_{action.name}": np.asarray(action.quality, dtype=float) for action in actions})
    record_out = {"kind": "evaluation", "evaluation_id": evaluation_id, "checkpoint_sha256": sha, "space_id": space,
                  "base_name": spec["base"], "recipe": spec["recipe"], "budget": spec["budget"],
                  "seed": spec["seed"], "dataset_fingerprint": camp["fingerprint"],
                  "trained_dataset": spec.get("dataset"), "trained_on_current_dataset": trained_here,
                  "candidate_basis": candidate_basis, "bank_fingerprint": camp["bank_fingerprint"],
                  "comparison_fingerprint": comparison, "scope": out["scope"], "decision": decision,
                  "strata": strata, "training_families": training_families, "alternatives": sources,
                  "prior_alternatives": priors,
                  "keyword": keyword_basis, "mu_basis": mu_basis, "recommendation": recommendation,
                  "choice": choice, "authority": authority, "label_acquisition": label_acquisition,
                  "labels_owed": labels_owed, "incumbent": incumbent, "vault": D.vault_key(vault),
                  "draws": {"file": f"{evaluation_id}.npz", "seeds": {"student": 11, "teacher": 12, "keyword": 13,
                                                                      "incumbent": 14, "alternatives_from": 31,
                                                                      "lambda": 41}},
                  "lambda_observations": len(lam.observations), "decided_at": started.isoformat(),
                  "rule": "spec §9.3: recommended when E[U(student)] >= each measured alternative"}
    _write_json(evaluation_dir / f"{evaluation_id}.json", record_out)
    record_out["judgment_id"] = _judge(
        repository, checkpoint=sha, space=space, judge="verifier", verdict=f"recommend_{recommendation}",
        evidence={"evaluation_id": evaluation_id, "decision": decision["expected_utility"], "choice": choice,
                  "alternatives": sources, "priors": sorted(priors), "label_model": LABEL_MODEL,
                  "dataset": camp["fingerprint"], "comparison": comparison},
        score=(float(decision["expected_utility"]["student"] - decision["expected_utility"][choice["against"]])
               if choice else None))
    # The serving pointer is reconciled by the owner, never here (re-review F4, F5): a losing
    # re-evaluation is a verifier's withdrawal RECOMMENDATION in judgment_ledger.
    withdrawal = None
    if adoption is not None and recommendation != "unmeasured":
        adopted_sha = str(adoption["checkpoint_sha256"])
        if adopted_sha == sha and recommendation != "adopt":
            withdrawal = {"checkpoint_sha256": sha, "why": "the serving checkpoint lost its re-evaluation",
                          "command": f"learnloop embeddings local student reject --checkpoint {sha}"}
        elif incumbent and chosen not in ("student", "incumbent"):
            withdrawal = {"checkpoint_sha256": incumbent,
                          "why": "the serving incumbent lost to the measured alternatives on the same questions",
                          "command": "learnloop embeddings local student revoke"}
    if withdrawal:
        withdrawal["judgment_id"] = _judge(
            repository, checkpoint=withdrawal["checkpoint_sha256"], space=space, judge="verifier",
            verdict="recommend_withdraw", evidence={"why": withdrawal["why"], "evaluation_id": evaluation_id,
                                                    "adoption_judgment_id": adoption.get("judgment_id")})
    ledger["decisions"].append({**record_out, "withdrawal": withdrawal})
    _write_json(_ledger_path(space_home), ledger)
    status_ = ("withdrawal_recommended" if withdrawal else
               "unmeasured" if recommendation == "unmeasured" else
               "kept" if recommendation == "adopt" and adoption and adoption["checkpoint_sha256"] == sha else
               "recommended" if recommendation == "adopt" else "not_recommended")
    following = {"withdrawal_recommended": withdrawal and withdrawal["command"],
                 "recommended": "`learnloop embeddings local student adopt` (or `student reject`) records the "
                                "owner's choice",
                 "unmeasured": "no alternative was measured on this comparison: supply --arm files naming "
                               f"{comparison}, or adopt (or reject) as the owner"}.get(status_)
    return {**out, "status": status_, "evaluation_id": evaluation_id, "recommendation": recommendation,
            "decision": decision, "strata": strata, "training_families": training_families,
            "alternatives": sources, "prior_alternatives": priors,
            "mu_basis": mu_basis, "choice": choice, "authority": authority, "label_acquisition": label_acquisition,
            "judgment_id": record_out["judgment_id"], "withdrawal": withdrawal, "next": following}


def _is_evaluation(record: Mapping[str, Any]) -> bool:
    # Re-review F16: owner decisions also name their evaluation_id; only evaluation records qualify.
    return record.get("kind") == "evaluation" or ("kind" not in record and "recommendation" in record
                                                  and "owner" not in record)


def _latest_evaluation(space_home: Path, checkpoint: str | None) -> dict[str, Any] | None:
    for record in reversed(read_ledger(space_home)["decisions"]):
        if _is_evaluation(record) and (checkpoint is None or record.get("checkpoint_sha256") == checkpoint):
            return record
    return None


def owner_choice(vault: LoadedVault, repository: Repository, *, accept: bool, root: Path | None = None,
                 checkpoint: str | None = None) -> dict[str, Any]:
    """The owner's answer to an evaluation's recommendation (``student adopt`` / ``student reject``).

    Adopting writes the serving pointer (``adoption.json``) from a ``judgment_ledger`` owner
    verdict; rejecting withdraws the checkpoint if it serves. The answer resolves to the latest
    EVALUATION of the checkpoint (never an earlier owner decision: re-review F16), so adopt and
    reject may follow each other. An answer to a costed recommendation (the student against its
    strongest measured alternative) is an observation of lambda (quality per dollar, spec §9.1;
    Codex review F14); an answer with nothing measured to compare against is not."""

    from learnloop.source_retrieval.student_encoder import read_adoption

    root = root or pins.data_root()
    manifest, space, reason = context(vault, root)
    job = "query_student_adopt" if accept else "query_student_reject"
    if manifest is None:
        return {"job": job, "status": "disabled", "reason": reason}
    space_home = home(root, space)
    record = _latest_evaluation(space_home, checkpoint)
    if record is None:
        return {"job": job, "status": "refused", "reason": "no evaluation of this checkpoint: run `student evaluate` first"}
    sha = str(record["checkpoint_sha256"])
    if accept and not (checkpoint_dir(root, space, sha) / "student.json").is_file():
        return {"job": job, "status": "refused", "reason": "the evaluated checkpoint is not present under the space"}
    choice = record.get("choice")
    judgment = _judge(repository, checkpoint=sha, space=space, judge="owner", verdict="adopt" if accept else "reject",
                      evidence={"evaluation_id": record["evaluation_id"], "recommendation": record.get("recommendation"),
                                "choice": choice, "verifier_judgment_id": record.get("judgment_id")})
    observation = None
    if choice:
        observation = record_owner_choice(space_home, rate="lambda", dq=choice["dq"], cost=choice["cost"],
                                          s=max(float(choice["s"]), 1e-6), accepted=accept,
                                          what=f"{'adopt' if accept else 'reject'} student {sha[:12]} against "
                                               f"{choice['against']}", judgment_id=judgment)
    previous = read_adoption(root, space)
    withdrawn = None
    if accept:
        _write_json(adoption_path(root, space), {
            key: record.get(key) for key in ("checkpoint_sha256", "space_id", "base_name", "recipe", "budget", "seed",
                                             "dataset_fingerprint", "trained_dataset", "evaluation_id",
                                             "recommendation")} | {
            "judgment_id": judgment, "adopted_by": "owner", "decided_at": datetime.now(timezone.utc).isoformat()})
    elif previous is not None and previous["checkpoint_sha256"] == sha:
        withdrawn = _withdraw(repository, root=root, space=space, adoption=previous, judge="owner",
                              why="the owner rejected it", evaluation_id=record["evaluation_id"])
    ledger = read_ledger(space_home)
    ledger["decisions"].append({"kind": "owner", "owner": "adopt" if accept else "reject", "checkpoint_sha256": sha,
                                "evaluation_id": record["evaluation_id"], "judgment_id": judgment,
                                "replaced": previous.get("checkpoint_sha256") if accept and previous else None,
                                "withdrawn": withdrawn, "at": datetime.now(timezone.utc).isoformat(), "by": "owner"})
    _write_json(_ledger_path(space_home), ledger)
    return {"job": job, "status": "adopted" if accept else "rejected", "checkpoint_sha256": sha,
            "judgment_id": judgment, "lambda_observation": observation, "withdrawn": withdrawn}


def revoke(vault: LoadedVault, repository: Repository | None = None, *, root: Path | None = None) -> dict[str, Any]:
    """The owner's per-checkpoint kill switch: the serving pointer is removed, the owner's verdict
    appended to ``judgment_ledger`` (when the vault's repository is given) and the ledger."""

    from learnloop.source_retrieval.student_encoder import read_adoption

    root = root or pins.data_root()
    manifest, space, reason = context(vault, root)
    if manifest is None:
        return {"status": "disabled", "reason": reason}
    previous = read_adoption(root, space)
    if previous is None:
        return {"status": "none"}
    judgment = None
    if repository is not None:
        judgment = _withdraw(repository, root=root, space=space, adoption=previous, judge="owner",
                             why="the owner revoked it", verdict="revoked")
    else:
        adoption_path(root, space).unlink(missing_ok=True)
    ledger = read_ledger(home(root, space))
    ledger["decisions"].append({"revoked": previous.get("checkpoint_sha256"), "judgment_id": judgment,
                                "at": datetime.now(timezone.utc).isoformat(), "by": "owner"})
    _write_json(_ledger_path(home(root, space)), ledger)
    return {"status": "revoked", "checkpoint_sha256": previous.get("checkpoint_sha256"), "judgment_id": judgment}


def status(vault: LoadedVault, repository: Repository, *, root: Path | None = None) -> dict[str, Any]:
    """Doctor's view of P2: bases, data, targets, runs, the meter, the adoption and the replay."""

    from learnloop.source_retrieval.student_encoder import read_adoption, replay_report

    root = root or pins.data_root()
    manifest, space, reason = context(vault, root)
    if manifest is None:
        return {"enabled": False, "reason": reason}
    space_home = home(root, space)
    by_extraction = D.extraction_families(repository, D.family_map(D.data_dir(root, space, vault), repository,
                                                                   persist=False))
    # The splits a dataset would use now (F19, spec §7), not the ones stored with the rows.
    rows = D.current_rows(_vault_rows(root, space, vault), by_extraction)
    index = targets_index(space_home)
    ledger = read_ledger(space_home)
    adoption = read_adoption(root, space)
    return {"enabled": True, "space_id": space, "student_switch": bool(vault.config.embedding.local.student),
            "bases": sorted(((bases_manifest(root) or {}).get("bases") or {})),
            "questions": {"stored": len(rows), "by_split": {s: sum(1 for r in rows if r["split"] == s)
                                                            for s in ("train", "dev", "heldout")},
                          "with_target": sum(1 for r in rows if r["id"] in index["queries"]),
                          "leakage_dropped": sum(1 for r in rows if r["id"] in index["dropped"])},
            "runs": {status_: sum(1 for run in ledger["runs"].values() if run.get("status") == status_)
                     for status_ in sorted({str(run.get("status")) for run in ledger["runs"].values()})},
            "meter": p2_meter(root, space).report(),
            "adopted": None if adoption is None else {key: adoption.get(key) for key in (
                "checkpoint_sha256", "base_name", "recipe", "budget", "seed", "decided_at")},
            "replay": replay_report(vault, repository)}


def plan(vault: LoadedVault, repository: Repository, *, bank_path: Path | None, root: Path | None = None,
         client: Any | None = None) -> dict[str, Any]:
    """The whole P2 dry run: what each owner command would do, with time, GPU and plan-call estimates."""

    root = root or pins.data_root()
    manifest, space, reason = context(vault, root)
    if manifest is None:
        return {"status": "disabled", "reason": reason}
    generate = D.generate(vault, repository, space_id=space, bank_path=bank_path, data_root=root, dry_run=True,
                          client=client)
    reachable = generate.get("reachable_budgets") or {}
    largest = max((int(v) for v in reachable.values()), default=0)
    bank_n = generate.get("bank_questions") or 0
    target_s = (largest * 1.15 + bank_n) * 0.018 + 25.0
    # Training estimate (labelled as such): a 0.6B forward+backward of a batch of 64 short queries
    # at ~0.15 s on the 5090 (to be measured by the first run), three epochs, plus load and measurement.
    def run_hours(budget: int, recipe: str) -> float:
        steps = SP.EPOCHS * math.ceil(budget / SP.TRAIN_BATCH_SIZE)
        per = 0.05 if recipe == "projection_only" else (0.15 if recipe == "align" else 0.2)
        return (steps * per + 90.0) / 3600.0

    budgets = effective_budgets(int(reachable.get(str(max(SP.BUDGETS)), 0)))
    screen = budgets[1] if len(budgets) > 1 else (budgets[0] if budgets else 0)
    schedule = [("screen", SP.PRIMARY_BASE, "projection_only", screen), ("screen", SP.PRIMARY_BASE, "align", screen),
                ("screen", "qwen3-embedding-0.6b", "align", screen), ("recipes", "chosen", "align_kd", screen),
                ("recipes", "chosen", "align_kd_mp", screen)]
    if budgets and budgets[0] < screen:
        schedule.append(("learning_curve", "chosen", "chosen", budgets[0]))
    if budgets and budgets[-1] > screen:
        schedule.append(("learning_curve (if its expected gain beats its GPU-hours)", "chosen", "chosen", budgets[-1]))
    schedule += [("seeds", "chosen", "chosen", budgets[-1] if budgets else 0)] * (SP.FINAL_SEEDS - 1)
    runs = [{"stage": stage, "base": base, "recipe": recipe, "budget": budget,
             "gpu_hours_estimate": round(run_hours(budget, "align_kd" if recipe == "chosen" else recipe), 3)}
            for stage, base, recipe, budget in schedule]
    total = target_s / 3600.0 + sum(run["gpu_hours_estimate"] for run in runs)
    calls = int(generate.get("calls") or 0)
    return {"status": "dry_run", "space_id": space, "generate": generate,
            "targets": {"queries": int(largest * 1.15) + bank_n, "gpu_minutes_estimate": round(target_s / 60, 1)},
            "training_runs": runs, "gpu_hours_estimate_total": round(total, 2), "gpu_hours_cap": SP.P2_GPU_HOURS_CAP,
            "plan_calls": calls,
            "plan_wall_hours_estimate": [round(calls * 10 / 3600, 1), round(calls * 30 / 3600, 1)],
            "estimate_basis": {"targets": "E1: 18 ms per query plus the 25 s load",
                               "training": "~0.05/0.15/0.2 s per 64-query step (projection/align/align+KD) on the "
                                           "5090, unmeasured: the first run's charged time replaces it",
                               "plan_calls": "10-30 s per call on the ChatGPT plan, one call per "
                                             f"{SP.PASSAGES_PER_CALL} passages, run serially"},
            "meter": p2_meter(root, space).report()}


__all__ = ["E1_AGGREGATES", "JUDGMENT_TASK", "LABEL_MODEL", "SHARD_SIZE", "all_rows", "bank_fingerprint", "bank_scope",
           "build_dataset", "campaign", "choose", "comparison_fingerprint", "complete_evidence", "context", "documents", "effective_budgets",
           "eligible_rows", "evaluate", "exchange_rates", "install_checkpoint", "judged_outcome",
           "missing_bank_targets", "next_step", "owner_choice", "p2_meter", "plan", "read_ledger",
           "record_owner_choice", "revoke", "run_next", "run_targets", "screen_current", "screen_leakage",
           "setup_bases", "status", "targets_index", "teacher_quality", "teacher_vectors", "trainer_job",
           "training_candidates", "unjudged_blocks"]
