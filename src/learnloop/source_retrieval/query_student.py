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
   kept. The teacher-cosine leakage guard (>= 0.90 to any bank question) runs here. The teacher
   and the student are never resident together: each is its own process, one at a time, by the
   lock.
4. ``train`` (:func:`run_next`): the next run of the schedule (:func:`next_step`): the screen
   (``projection_only`` and ``align`` on the primary base, ``align`` on the second base, at the
   screen budget), then the recipes on the chosen base (``align_kd``, ``align_kd_mp``), then the
   learning curve (the small budget, then the large one only when its expected gain beats its
   GPU-hours: ``student_decision.continue_training``), then the remaining seeds of the chosen
   recipe. Every choice is ``argmax E[U]`` on development (``student_decision.decide``); none is
   a margin. The teacher's top-50 for the ranking losses is computed here from the vault's own
   vector cache, the bank's gold supports left out (never a hard negative).
5. ``evaluate`` (:func:`evaluate`): the candidate checkpoint through the real query process on
   the bank, beside the teacher's bank vectors, per stratum (deictic, logged, unseen family);
   the student is ADOPTED when ``E[U(student)] >= E[U(each alternative)]`` (§9.3), and the
   adoption is recorded under the space with its decision. Its weight in the fusion is then
   learned (§9.2) like every list.

No book text, synthetic question or checkpoint is ever written to a vault's ``state.sqlite`` or
the repository: everything lives under ``<data root>/students/<space id>/`` (§11).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from datetime import datetime, timedelta, timezone
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
from learnloop.local_embeddings import worker as worker_module
from learnloop.local_embeddings.cache import CacheUnreadable, VectorCache, cache_path
from learnloop.local_embeddings.gpu_meter import GpuBudgetExceeded, GpuMeter
from learnloop.local_embeddings.launcher import LocksBusy, ScopedLauncher, gpu_locks
from learnloop.local_embeddings.setup import load_manifest
from learnloop.source_retrieval import student_data as D
from learnloop.source_retrieval.corpus import current_extractions
from learnloop.source_retrieval.local_index import build_job, canary_check, epoch_of, measured_epoch, preflight_problems
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


# -- 3. teacher targets ------------------------------------------------------------------------------------
def targets_index(space_home: Path) -> dict[str, Any]:
    return _read_json(space_home / "targets" / "index.json", {"queries": {}, "bank": {}, "dropped": {}, "shards": {}})


def teacher_vectors(space_home: Path, ids: Sequence[str], *, kind: str = "queries") -> dict[str, np.ndarray]:
    """``{id: unit float32 vector}`` from the int8 shards (rows that never arrived are absent)."""

    index = targets_index(space_home)
    wanted = [(str(identity), index[kind].get(str(identity))) for identity in ids]
    by_shard: dict[str, list[tuple[str, int]]] = {}
    for identity, place in wanted:
        if place:
            by_shard.setdefault(str(place[0]), []).append((identity, int(place[1])))
    out: dict[str, np.ndarray] = {}
    for shard, rows in by_shard.items():
        array = np.load(space_home / "targets" / f"{shard}.npy", mmap_mode="r")
        for identity, row in rows:
            vector = np.asarray(array[row], dtype=np.float32)
            norm = float(np.linalg.norm(vector))
            if norm:
                out[identity] = vector / norm
    return out


def all_rows(root: Path, space: str) -> list[dict[str, Any]]:
    """Every stored question of every vault for this space."""

    rows = []
    for directory in sorted((home(root, space) / "data").glob("*")):
        rows.extend(D.stored_queries(directory))
    return rows


def run_targets(vault: LoadedVault, repository: Repository, *, bank_path: Path | None, root: Path | None = None,
                launcher: Callable[..., dict[str, Any]] | None = None, meter: GpuMeter | None = None,
                preflight: Callable[[], list[str]] | None = None, locks: Callable[[], Any] = gpu_locks,
                dry_run: bool = False) -> dict[str, Any]:
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
    bank = D.load_bank(bank_path)
    index = targets_index(space_home)
    rows = all_rows(root, space)
    owed = [row for row in rows if row["id"] not in index["queries"]]
    bank_owed = [question for question in bank if question["query_id"] not in index["bank"]]
    meter = meter or p2_meter(root, space)
    seconds = (len(owed) + len(bank_owed)) * 0.018 + 25.0
    out.update(space_id=space, questions=len(rows), owed=len(owed), bank_owed=len(bank_owed),
               estimate={"gpu_minutes": round(seconds / 60, 1),
                         "basis": "E1: 18 ms per query (batch one, BF16, resident) plus the 25 s load"},
               meter=meter.report())
    if not owed and not bank_owed:
        return {**out, "status": "complete"}
    if dry_run:
        return {**out, "status": "dry_run"}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        stored = (known_spaces(connection).get(space) or {}).get("canaries")
    if not stored:
        return {**out, "status": "refused", "reason": "index this vault's local space first (`learnloop embeddings "
                                                      "local index`): the targets' canaries are checked against "
                                                      "the space's stored ones"}
    problems = (preflight or preflight_problems)()
    if problems:
        return {**out, "status": "waiting_for_gpu", "reason": "; ".join(problems)}
    run_id = uuid4().hex
    job, _targets = build_job([], manifest=manifest, plan_id=f"p2targets_{run_id[:16]}")
    targets_dir = space_home / "targets"
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
    for kind, items, key in (("queries", owed, "id"), ("bank", bank_owed, "query_id")):
        for start in range(0, len(items), SHARD_SIZE):
            chunk = items[start:start + SHARD_SIZE]
            name = shard_name("q" if kind == "queries" else "b")
            plan[name] = (kind, [str(item[key]) for item in chunk])
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
            kept[kind] += 1
        index["shards"][name] = {"kind": kind, "rows": len(ids), "latency_p50_s": result.get("latency_p50_s")}
    # The teacher-cosine leakage guard (keep, may only tighten).
    bank_vectors = teacher_vectors_from(index, targets_dir, list(index["bank"]), "bank")
    if bank_vectors:
        matrix = np.stack(list(bank_vectors.values()))
        fresh = teacher_vectors_from(index, targets_dir, [row["id"] for row in rows], "queries")
        for identity, vector in fresh.items():
            highest = float(np.max(matrix @ vector))
            if highest >= SP.LEAKAGE_MAX_TEACHER_COS:
                index["dropped"][identity] = round(highest, 4)
    _write_json(targets_dir / "index.json", index)
    complete = output.get("status") == "complete" and not kept["errors"]
    return {**out, "status": "complete" if complete else "partial", "kept": kept,
            "leakage_dropped_by_teacher_cos": len(index["dropped"]), "meter": meter.report()}


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
def documents(vault: LoadedVault, repository: Repository, space: str, *,
              exclude: set[tuple[str, str]] = frozenset()) -> tuple[list[str], np.ndarray]:
    """The grouped space's current covered blocks: ``(record ids, unit float32 matrix)``."""

    extraction_ids = sorted(current_extractions(repository))
    windows = windows_by_extraction(vault, repository, extraction_ids, ("grouped",))
    cache = VectorCache(cache_path(vault.root, space))
    ids, rows = [], []
    for (extraction_id, _variant), found in sorted(windows.items()):
        keys = expected_keys(space, found)
        try:
            vectors = cache.vectors(key for parts in keys.values() for key, _w in parts)
        except CacheUnreadable:
            continue
        for span_id, parts in sorted(keys.items()):
            if (extraction_id, span_id) in exclude or not all(key in vectors for key, _w in parts):
                continue
            vector = (vectors[parts[0][0]] if len(parts) == 1 else
                      np.asarray(mean_vector([vectors[key] for key, _w in parts], [w for _k, w in parts])))
            norm = float(np.linalg.norm(vector))
            if norm:
                ids.append(block_record_id(extraction_id, span_id))
                rows.append(np.asarray(vector, dtype=np.float32) / norm)
    matrix = np.stack(rows) if rows else np.zeros((0, SP.STUDENT_DIMENSIONS), dtype=np.float32)
    return ids, matrix


def complete_evidence(ranked: Sequence[str], sets: Sequence[Sequence[tuple[str, str]]], k: int = 10) -> float | None:
    """1 when some evidence set's every required block is in the top ``k``, 0 when none is, None when unlabelled."""

    if not sets:
        return None
    top = set(ranked[:k])
    return 1.0 if any(all(block_record_id(e, s) in top for e, s in required) for required in sets if required) else 0.0


# -- 4. datasets and the schedule ---------------------------------------------------------------------------
def _ledger_path(space_home: Path) -> Path:
    return space_home / "p2-ledger.json"


def read_ledger(space_home: Path) -> dict[str, Any]:
    return _read_json(_ledger_path(space_home), {"version": 1, "runs": {}, "decisions": []})


def effective_budgets(n_train: int) -> list[int]:
    """The nested budgets the data allows today (a budget above the data is the data)."""

    return sorted({min(budget, n_train) for budget in SP.BUDGETS if min(budget, n_train) > 0})


def _spec_key(spec: Mapping[str, Any]) -> str:
    return f"{spec['base']}|{spec['recipe']}|{spec['budget']}|{spec['seed']}"


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


def choose(runs: Sequence[Mapping[str, Any]], *, teacher_q: np.ndarray, box_s: float, mu: float) -> dict[str, Any]:
    lam = SD.seeded_lambda()
    return SD.decide(run_actions(runs, teacher_q=teacher_q, box_s=box_s), lam=lam.draws(len(teacher_q)), mu=mu)


def next_step(ledger: Mapping[str, Any], *, n_train: int, has_positives: bool, teacher_q: np.ndarray, box_s: float,
              hours_left: float) -> dict[str, Any]:
    """The schedule's next run, or ``{"step": "evaluate", ...}`` when the chosen recipe has its seeds."""

    budgets = effective_budgets(n_train)
    if not budgets:
        return {"step": "blocked", "reason": "no training question has a teacher target yet (generate, then targets)"}
    screen_budget = budgets[1] if len(budgets) > 1 else budgets[0]
    done, tried = _completed(ledger), _tried(ledger)
    mu = float(np.mean(teacher_q))
    lam = SD.seeded_lambda()
    nu = SD.seeded_nu(mu, SP.P2_GPU_HOURS_CAP, lam).mean()

    def pending(specs: Sequence[dict[str, Any]], stage: str) -> dict[str, Any] | None:
        for spec in specs:
            key = _spec_key(spec)
            if key in done:
                continue
            if key in tried:
                return {"step": "blocked", "stage": stage, "spec": spec,
                        "reason": f"run {tried[key]['run_id']} ended {tried[key].get('status')}: "
                                  f"{tried[key].get('reason') or ''}"[:300]}
            return {"step": "train", "stage": stage, "spec": spec}
        return None

    screen = [{"base": SP.PRIMARY_BASE, "recipe": "projection_only", "budget": screen_budget, "seed": 0},
              {"base": SP.PRIMARY_BASE, "recipe": "align", "budget": screen_budget, "seed": 0}] + \
             [{"base": base, "recipe": "align", "budget": screen_budget, "seed": 0}
              for base in SP.SCREEN_BASES if base != SP.PRIMARY_BASE]
    step = pending(screen, "screen")
    if step:
        return step
    screen_runs = [done[_spec_key(spec)] for spec in screen]
    decision = choose(screen_runs, teacher_q=teacher_q, box_s=box_s, mu=mu)
    chosen_base = next(run["spec"]["base"] for run in screen_runs if run["run_id"] == decision["chosen"])
    recipes = [{"base": chosen_base, "recipe": "align_kd", "budget": screen_budget, "seed": 0}]
    if has_positives:
        recipes.append({"base": chosen_base, "recipe": "align_kd_mp", "budget": screen_budget, "seed": 0})
    step = pending(recipes, "recipes")
    if step:
        return {**step, "screen_decision": decision}
    candidates = [run for run in screen_runs if run["spec"]["base"] == chosen_base] + \
                 [done[_spec_key(spec)] for spec in recipes]
    recipe_decision = choose(candidates, teacher_q=teacher_q, box_s=box_s, mu=mu)
    chosen_recipe = next(run["spec"]["recipe"] for run in candidates if run["run_id"] == recipe_decision["chosen"])
    final_budget = screen_budget
    if budgets[0] < screen_budget:
        curve = [{"base": chosen_base, "recipe": chosen_recipe, "budget": budgets[0], "seed": 0}]
        step = pending(curve, "learning_curve")
        if step:
            return {**step, "recipe_decision": recipe_decision}
    if budgets[-1] > screen_budget:
        large = {"base": chosen_base, "recipe": chosen_recipe, "budget": budgets[-1], "seed": 0}
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
                                        teacher_quality=mu, nu=nu)
            if rule["continue"]:
                return {"step": "train", "stage": "learning_curve", "spec": large, "continue_rule": rule}
            final_budget = screen_budget
        else:
            same = [done[_spec_key({**large, "budget": budget})] for budget in (screen_budget, budgets[-1])]
            budget_decision = choose(same, teacher_q=teacher_q, box_s=box_s, mu=mu)
            final_budget = next(run["spec"]["budget"] for run in same if run["run_id"] == budget_decision["chosen"])
    seeds = [{"base": chosen_base, "recipe": chosen_recipe, "budget": final_budget, "seed": seed}
             for seed in range(SP.FINAL_SEEDS)]
    step = pending(seeds, "seeds")
    if step:
        return step
    final = [done[_spec_key(spec)] for spec in seeds]
    seed_decision = choose(final, teacher_q=teacher_q, box_s=box_s, mu=mu)
    candidate = next(run for run in final if run["run_id"] == seed_decision["chosen"])
    spread = [float(np.mean(run["dev"]["agreements"])) for run in final]
    return {"step": "evaluate", "candidate": candidate["run_id"], "checkpoint_sha256": candidate["checkpoint_sha256"],
            "spec": candidate["spec"], "seed_decision": seed_decision,
            "seed_agreements": [round(value, 4) for value in spread]}


def _vault_rows(root: Path, space: str, vault: LoadedVault) -> list[dict[str, Any]]:
    return D.stored_queries(D.data_dir(root, space, vault))


def build_dataset(vault: LoadedVault, repository: Repository, *, root: Path, space: str, budget: int,
                  bank_path: Path, out_dir: Path) -> dict[str, Any]:
    """The run's files: the nested training budget, the development split, the documents and the
    teacher's top-k over them (gold supports never a candidate), the temperature."""

    space_home = home(root, space)
    index = targets_index(space_home)
    excluded = D.bank_supports(D.load_bank(bank_path))
    record_ids, matrix = documents(vault, repository, space, exclude=excluded)
    if not record_ids:
        raise ValueError("the vault's local space has no covered block: index it first")
    position = {record_id: row for row, record_id in enumerate(record_ids)}
    rows = [row for row in _vault_rows(root, space, vault)
            if row["id"] in index["queries"] and row["id"] not in index["dropped"]]
    train = D.nested(rows, budget)
    dev = sorted((row for row in rows if row["split"] == "dev"), key=lambda row: row["rank"])[:DEV_MAX]
    out_dir.mkdir(parents=True, exist_ok=True)
    stats: dict[str, Any] = {"documents": len(record_ids), "train": len(train), "dev": len(dev),
                             "bank_supports_excluded": len(excluded)}
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
        (out_dir / f"{split}_texts.json").write_text(json.dumps([row["text"] for row in items]), encoding="utf-8")
        np.save(out_dir / f"{split}_targets.npy", targets.astype(np.float16))
        np.save(out_dir / f"{split}_topk.npy", topk)
        (out_dir / f"{split}_positives.json").write_text(json.dumps(positives), encoding="utf-8")
        stats[f"{split}_with_positives"] = sum(1 for item in positives if item)
    np.save(out_dir / "documents.npy", matrix.astype(np.float16))
    # Structural: a softmax temperature on the scale of the teacher's own top-k score spread.
    stats["temperature"] = round(max(float(np.median(spreads)) if spreads else 0.05, MIN_TEMPERATURE), 6)
    return stats


def trainer_job(spec: Mapping[str, Any], *, space: str, base_dir: Path, data_dir: Path, out_dir: Path,
                temperature: float, plan_id: str) -> dict[str, Any]:
    base = SP.STUDENT_BASES[spec["base"]]
    return {"version": SP.TRAINER_VERSION, "plan_id": plan_id, "space_id": space, "base_name": spec["base"],
            "base": {key: base[key] for key in ("repo", "revision", "pooling", "query_prefix", "hidden_size",
                                                "trust_remote_code", "files", "remote_code", "inert_python")},
            "base_dir": str(base_dir), "data_dir": str(data_dir), "out_dir": str(out_dir),
            "recipe": spec["recipe"], "seed": int(spec["seed"]), "budget": int(spec["budget"]),
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
             dry_run: bool = False) -> dict[str, Any]:
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
    ledger = read_ledger(space_home)
    index = targets_index(space_home)
    rows = [row for row in _vault_rows(root, space, vault)
            if row["id"] in index["queries"] and row["id"] not in index["dropped"]]
    n_train = sum(1 for row in rows if row["split"] == "train")
    meter = meter or p2_meter(root, space)
    teacher_q, basis = teacher_quality(space_home)
    box = float(vault.config.source_retrieval.retrieval_timeout_seconds)
    step = next_step(ledger, n_train=n_train, has_positives=any(row["supports"] for row in rows), teacher_q=teacher_q,
                     box_s=box, hours_left=(meter.remaining_s() or 0.0) / 3600.0)
    out.update(space_id=space, step=step, teacher_quality_basis=basis, meter=meter.report(),
               budgets=effective_budgets(n_train))
    if step["step"] != "train" or dry_run:
        return {**out, "status": "dry_run" if dry_run else step["step"]}
    spec = step["spec"]
    record = (bases.get("bases") or {}).get(spec["base"])
    if record is None:
        return {**out, "status": "not_set_up", "reason": f"the base {spec['base']} is not recorded (rerun setup)"}
    problems = (preflight or preflight_problems)()
    if problems:
        return {**out, "status": "waiting_for_gpu", "reason": "; ".join(problems)}
    run_id = uuid4().hex
    work = root / "runs" / run_id
    data = space_home / "runs" / run_id / "data"
    stats = build_dataset(vault, repository, root=root, space=space, budget=int(spec["budget"]), bank_path=bank_path,
                          out_dir=data)
    job = trainer_job(spec, space=space, base_dir=Path(record["dir"]), data_dir=data,
                      out_dir=space_home / "runs" / run_id, temperature=stats["temperature"],
                      plan_id=f"p2train_{run_id[:16]}")
    from learnloop.local_embeddings import student_trainer

    run = launcher or ScopedLauncher(Path(manifest["env_python"]), script=Path(student_trainer.__file__),
                                     memory_max=SP.TRAIN_SCOPE_MEMORY_MAX, unit_prefix="learnloop-student-train")
    entry: dict[str, Any] = {"run_id": run_id, "spec": dict(spec), "stage": step["stage"], "dataset": stats,
                             "started_at": datetime.now(timezone.utc).isoformat()}
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


# -- 5. evaluation and adoption -------------------------------------------------------------------------------
def _outcomes(bank: Sequence[Mapping[str, Any]], vectors: Mapping[str, np.ndarray], record_ids: Sequence[str],
              matrix: np.ndarray) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for question in bank:
        vector = vectors.get(question["query_id"])
        if vector is None:
            out[question["query_id"]] = None
            continue
        order = np.argsort(-(matrix @ np.asarray(vector, dtype=np.float32)))[:10]
        out[question["query_id"]] = complete_evidence([record_ids[i] for i in order], question["evidence_sets"])
    return out


def _strata(bank: Sequence[Mapping[str, Any]], trained_families: set[str]) -> dict[str, set[str]]:
    return {"all": {q["query_id"] for q in bank},
            "deictic": {q["query_id"] for q in bank if q["deictic"]},
            "logged": {q["query_id"] for q in bank if q["origin"] == "logged"},
            "unseen_family": {q["query_id"] for q in bank if q["family"] and q["family"] not in trained_families}}


def _monthly_query_usd(repository: Repository) -> float:
    since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        try:
            value = connection.execute("SELECT COALESCE(SUM(cost), 0) FROM model_call_receipts WHERE owner_kind = "
                                       "'source_query_embedding' AND started_at >= ?", (since,)).fetchone()[0]
        except Exception:  # noqa: BLE001 - an older schema has no receipts table
            value = 0.0
    return float(value or 0.0)


def evaluate(vault: LoadedVault, repository: Repository, *, bank_path: Path | None, root: Path | None = None,
             encoder_factory: Callable[[str], Any] | None = None, arms: Mapping[str, Path] | None = None,
             dry_run: bool = False) -> dict[str, Any]:
    """The candidate on the bank beside the teacher, per stratum; adopted by §9.3's expected utility."""

    from learnloop.source_retrieval.student_encoder import StudentEncoder

    root = root or pins.data_root()
    manifest, space, reason = context(vault, root)
    out: dict[str, Any] = {"job": "query_student_evaluate"}
    if manifest is None:
        return {**out, "status": "disabled", "reason": reason}
    if bank_path is None:
        return {**out, "status": "refused", "reason": "the labelled bank is required (--bank)"}
    space_home = home(root, space)
    ledger = read_ledger(space_home)
    index = targets_index(space_home)
    rows = [row for row in _vault_rows(root, space, vault) if row["id"] in index["queries"]]
    teacher_q, _basis = teacher_quality(space_home)
    box = float(vault.config.source_retrieval.retrieval_timeout_seconds)
    meter = p2_meter(root, space)
    step = next_step(ledger, n_train=sum(1 for row in rows if row["split"] == "train"),
                     has_positives=any(row["supports"] for row in rows), teacher_q=teacher_q, box_s=box,
                     hours_left=(meter.remaining_s() or 0.0) / 3600.0)
    if step["step"] != "evaluate":
        return {**out, "status": "not_ready", "step": step}
    sha = step["checkpoint_sha256"]
    out.update(space_id=space, candidate=step["candidate"], checkpoint_sha256=sha, spec=step["spec"])
    bank = D.load_bank(bank_path)
    teacher = teacher_vectors_from(index, space_home / "targets", [q["query_id"] for q in bank], "bank")
    if len(teacher) < len(bank):
        return {**out, "status": "refused", "reason": f"{len(bank) - len(teacher)} bank question(s) have no teacher "
                                                      "vector: run `student targets` with this bank"}
    if dry_run:
        return {**out, "status": "dry_run", "bank_questions": len(bank)}
    bases = bases_manifest(root) or {"bases": {}}
    record = bases["bases"].get(step["spec"]["base"])
    if encoder_factory is None:
        def encoder_factory(digest: str) -> Any:
            return StudentEncoder(vault, space_id=space, checkpoint_sha=digest,
                                  checkpoint=checkpoint_dir(root, space, digest), base_name=step["spec"]["base"],
                                  base_dir=Path(record["dir"]), env_python=Path(manifest["env_python"]),
                                  data_root=root)
    encoder = encoder_factory(sha)
    texts = [question["text"] for question in bank]
    started = datetime.now(timezone.utc)
    encoded = encoder.encode(texts, deadline=None)
    student = {question["query_id"]: np.asarray(vector, dtype=np.float32)
               for question, vector in zip(bank, encoded, strict=True)}
    record_ids, matrix = documents(vault, repository, space)
    families = {q["query_id"]: q["family"] or q["vault"] or "bank" for q in bank}
    outcomes = {"student": _outcomes(bank, student, record_ids, matrix),
                "teacher": _outcomes(bank, teacher, record_ids, matrix)}
    _write_json(space_home / "evaluation" / "teacher_outcomes.json",
                {"outcomes": outcomes["teacher"], "families": families})
    trained = {row["family"] for row in rows if row["split"] == "train"}
    strata = {}
    for name, members in _strata(bank, trained).items():
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
    # The alternatives: what serves without the student (supplied per-question outcomes, else E1's aggregates).
    alternatives: dict[str, SD.ArmOutcomes] = {}
    for name, path in (arms or {}).items():
        values = _read_json(Path(path), {})
        alternatives[name] = SD.ArmOutcomes(name, {str(k): v for k, v in values.items()}, families)
    sources = {name: "supplied" for name in alternatives}
    for name in ("qwen", "voyage"):
        if name not in alternatives:
            alternatives[name] = SD.aggregate_arm(name, E1_AGGREGATES[name])
            sources[name] = "legacy: E1's committed aggregates (unpaired)"
    student_q = SD.bank_quality_draws(SD.ArmOutcomes("student", outcomes["student"], families), seed=11)
    keyword = alternatives.pop("keyword", None)
    sources.pop("keyword", None)
    dense_q = SD.bank_quality_draws(SD.ArmOutcomes("teacher", outcomes["teacher"], families), seed=12)
    mu = (dense_q - SD.bank_quality_draws(keyword, seed=13)) if keyword is not None else dense_q
    mu_basis = "bank: teacher minus keyword" if keyword is not None else "upper bound: the teacher's whole quality"
    run = ledger["runs"][step["candidate"]]
    starts = [float(value) for value in _read_json(checkpoint_dir(root, space, sha) / "start_times.json", [])]
    late, total = _late_counts(run, box)
    late += sum(1 for value in starts if value > box)
    total += len(starts)
    lam = SD.ExchangeRate.from_dict(_read_json(space_home / "lambda.json", SD.seeded_lambda().as_dict()))
    monthly = _monthly_query_usd(repository)
    actions = [SD.Action("student", student_q, monthly_usd=0.0, late=SD.late_draws(late, total, seed=21))]
    for i, (name, arm) in enumerate(sorted(alternatives.items())):
        actions.append(SD.Action(name, SD.bank_quality_draws(arm, seed=31 + i), monthly_usd=monthly))
    decision = SD.decide(actions, lam=lam.draws(seed=41), mu=mu)
    adopted = decision["chosen"] == "student"
    record_out = {"checkpoint_sha256": sha, "space_id": space, "base_name": step["spec"]["base"],
                  "recipe": step["spec"]["recipe"], "budget": step["spec"]["budget"], "seed": step["spec"]["seed"],
                  "decision": decision, "strata": strata, "alternatives": sources, "mu_basis": mu_basis,
                  "decided_at": started.isoformat(), "rule": "spec §9.3: adopted when E[U(student)] >= each alternative"}
    ledger["decisions"].append({**record_out, "adopted": adopted})
    _write_json(_ledger_path(space_home), ledger)
    if adopted:
        _write_json(adoption_path(root, space), record_out)
    return {**out, "status": "adopted" if adopted else "not_adopted", "decision": decision, "strata": strata,
            "alternatives": sources, "mu_basis": mu_basis}


def revoke(vault: LoadedVault, *, root: Path | None = None) -> dict[str, Any]:
    """The owner's per-checkpoint kill switch: the adoption is removed (recorded in the ledger)."""

    root = root or pins.data_root()
    manifest, space, reason = context(vault, root)
    if manifest is None:
        return {"status": "disabled", "reason": reason}
    path = adoption_path(root, space)
    previous = _read_json(path, None)
    if previous is None:
        return {"status": "none"}
    path.unlink()
    ledger = read_ledger(home(root, space))
    ledger["decisions"].append({"revoked": previous.get("checkpoint_sha256"),
                                "at": datetime.now(timezone.utc).isoformat(), "by": "owner"})
    _write_json(_ledger_path(home(root, space)), ledger)
    return {"status": "revoked", "checkpoint_sha256": previous.get("checkpoint_sha256")}


def status(vault: LoadedVault, repository: Repository, *, root: Path | None = None) -> dict[str, Any]:
    """Doctor's view of P2: bases, data, targets, runs, the meter, the adoption and the replay."""

    from learnloop.source_retrieval.student_encoder import read_adoption, replay_report

    root = root or pins.data_root()
    manifest, space, reason = context(vault, root)
    if manifest is None:
        return {"enabled": False, "reason": reason}
    space_home = home(root, space)
    rows = _vault_rows(root, space, vault)
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


__all__ = ["E1_AGGREGATES", "SHARD_SIZE", "all_rows", "build_dataset", "choose", "complete_evidence", "context",
           "documents", "effective_budgets", "evaluate", "install_checkpoint", "next_step", "p2_meter", "plan",
           "read_ledger", "revoke", "run_next", "run_targets", "setup_bases", "status", "targets_index",
           "teacher_quality", "teacher_vectors", "trainer_job"]

# The worker module is the targets job's process; imported for its version pin in build_job.
_ = worker_module
