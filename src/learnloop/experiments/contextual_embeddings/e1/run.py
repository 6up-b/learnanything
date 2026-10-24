"""E1's stages: dry run, preflight, local (GPU), labels (paid), score.

Order (spec §8): a frozen plan from a verified import -> ``preflight``
(import digests, replay verification, model files, the separate
environment, measured resources, the GPU meter, the ledger) -> ``local``
(ONE scoped worker: smoke, profiling at 2k/4k/8k, every v2 document and
query, unload, exit) -> ``labels`` (the v2 arms' new candidates and any
voyage-context-4 vector E0 lacks, under E1's $5 ledger; ``--dry-run`` prices
the real counts first) -> ``score`` (every arm on the merged labels, paired
comparisons, the prespecified E1 decision) -> ``report``.

The app process never imports torch. Every stage refuses a provisional plan
(E0 not finished, or the replay unverified). Private state stays under
``fixtures-local/contextual-embeddings/e1/``; results are aggregates only.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from learnloop.experiments.contextual_embeddings import credentials, pins
from learnloop.experiments.contextual_embeddings.adapters import VectorStore
from learnloop.experiments.contextual_embeddings.corpus import _inside_local_root
from learnloop.experiments.contextual_embeddings.e1 import pins as e1_pins
from learnloop.experiments.contextual_embeddings.e1 import worker as worker_module
from learnloop.experiments.contextual_embeddings.e1.gpu_meter import MIN_SLOT_S, GpuMeter
from learnloop.experiments.contextual_embeddings.e1.ledger import ledger_dir, prior_spend
from learnloop.experiments.contextual_embeddings.e1.plan import build_plan, import_inputs, manifest_inputs
from learnloop.experiments.contextual_embeddings.e1.replay import ImportLayout, Replayed

KEY_ENVS = {"anthropic": pins.ANTHROPIC_KEY_ENV, "voyage": "VOYAGE_API_KEY"}
VERSION_PROBE = (
    "import json, importlib.metadata as m\n"
    "out = {}\n"
    "for name in ('torch', 'transformers', 'accelerate', 'safetensors', 'numpy', 'tqdm', 'huggingface-hub'):\n"
    "    try:\n        out[name] = m.version(name)\n    except Exception:\n        out[name] = None\n"
    "try:\n    from transformers import Qwen3_5Model\n    out['qwen3_5_model'] = True\n"
    "except Exception:\n    out['qwen3_5_model'] = False\n"
    "print(json.dumps(out))\n"
)


class PlanRefused(ValueError):
    """The plan cannot run this stage (nothing was started or spent)."""


class LayeredVectorStore(VectorStore):
    """E0's imported vectors read-only beneath E1's own (fills go on top)."""

    def __init__(self, base: Path, overlay: Path) -> None:
        super().__init__(overlay)
        self.base = VectorStore(base)

    def get(self, space: str, key: str) -> list[list[float]] | None:
        return super().get(space, key) or self.base.get(space, key)

    def get_raw(self, space: str, key: str) -> Any:
        return super().get_raw(space, key) or self.base.get_raw(space, key)

    def put(self, space: str, key: str, vectors: Sequence[Sequence[float]], *, raw: Any = None) -> None:
        if self.base.get(space, key) is None:
            super().put(space, key, vectors, raw=raw)


def run_root(layout: ImportLayout, plan_id: str) -> Path:
    return layout.root.parent.parent / "runs" / plan_id


def _scratch(layout: ImportLayout) -> Path:
    path = layout.root / "work" / "scratch"
    path.mkdir(parents=True, exist_ok=True)
    return path


def hosted_store(layout: ImportLayout, label: str, root: Path) -> LayeredVectorStore:
    return LayeredVectorStore(layout.store(label) / "vectors", root / label / "hosted-vectors")


def replay_all(layout: ImportLayout, *, root: Path | None = None) -> list[Replayed]:
    from learnloop.experiments.contextual_embeddings.e1.replay import replay_copy, verify_replay

    replays = []
    for label in layout.labels:
        store = hosted_store(layout, label, root) if root is not None else None
        replayed = replay_copy(layout, label, scratch=_scratch(layout), store=store)
        verify_replay(replayed)
        replays.append(replayed)
    return replays


# -- dry run -----------------------------------------------------------------------------------
def dry_run(*, e0_run_dir: Path | None = None, import_dir: Path | None = None,
            env_file: Sequence[Path] = (), environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    """The E1 plan with no network and no write to any input (digests
    checked before and after). From E0's manifests: provisional; from a
    verified import of a finished E0 run: frozen."""

    from learnloop.experiments.contextual_embeddings.e1.replay import run_identity, verify_import
    from learnloop.experiments.contextual_embeddings.runner import network_guard, tree_digest

    if (e0_run_dir is None) == (import_dir is None):
        raise ValueError("give exactly one of an E0 run directory or an E1 import")
    watched = Path(e0_run_dir) / "frozen" if e0_run_dir is not None else Path(import_dir)
    before = tree_digest(watched) if e0_run_dir is not None else None
    with network_guard() as guard:
        keys = (credentials.load_env_files(list(env_file), KEY_ENVS.values()) if env_file
                else credentials.availability(KEY_ENVS.values(), environ=environ))
        if e0_run_dir is not None:
            inputs = manifest_inputs(Path(e0_run_dir))
            anchor = Path(e0_run_dir)
            extra: dict[str, Any] = {}
        else:
            layout = ImportLayout(Path(import_dir))
            problems = verify_import(layout)
            identity_ok = run_identity(layout) == layout.plan().get("run_id")
            replays = replay_all(layout)
            inputs = import_inputs(layout, replays)
            if problems or not identity_ok:
                for label in inputs["verification"]:
                    inputs["verification"][label] = {**inputs["verification"][label], "ok": False}
            extra = {"import_problems": problems, "e0_run_id_rebuilt": identity_ok}
            anchor = Path(import_dir)
            if verify_import(layout) != problems:
                raise RuntimeError("the dry run changed the import")
        plan = build_plan(inputs, keys=keys, prior=_prior(anchor))
        plan.update(extra)
        attempts = guard.attempts
    if before is not None and tree_digest(watched) != before:
        raise RuntimeError("the dry run changed E0's frozen manifests")
    plan["checks"] = {"network_calls": attempts, "inputs_changed": 0, "settings_file_read": False,
                      "torch_imported": "torch" in __import__("sys").modules}
    return plan


def _prior(anchor: Path) -> dict[str, Any]:
    try:
        return prior_spend(anchor)
    except ValueError:
        return {"plans": {}, "total_usd": 0.0, "by_category": {}}


def require_frozen(plan: Mapping[str, Any], layout: ImportLayout) -> None:
    """A stage runs only the frozen plan the import rebuilds to."""

    if plan.get("status") != "frozen":
        raise PlanRefused("the plan is provisional (E0 unfinished or the replay unverified): run "
                          "`e1 import` after E0 finishes, then `e1 plan --import`")
    again = dry_run(import_dir=layout.root)
    if again["plan_id"] != plan["plan_id"] or again["status"] != "frozen":
        raise PlanRefused("the import no longer rebuilds to this plan; nothing was started")


# -- preflight ---------------------------------------------------------------------------------
def environment_versions(env_python: Path, *, run: Callable[..., Any] = subprocess.run) -> dict[str, Any]:
    """The separate environment's package versions (never the app's)."""

    result = run([str(env_python), "-I", "-c", VERSION_PROBE], capture_output=True, text=True, timeout=180,
                 env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": "/nonexistent"})
    if result.returncode != 0:
        return {"ok": False, "error": "the environment's interpreter failed to report its versions"}
    versions = json.loads(result.stdout.strip().splitlines()[-1])
    wanted = dict(item.split("==") for item in e1_pins.LOCAL_REQUIREMENTS if "==" in item)
    mismatched = sorted(name for name, version in wanted.items() if versions.get(name) != version)
    return {"ok": not mismatched and bool(versions.get("qwen3_5_model")), "versions": versions,
            "pinned": wanted, "mismatched": mismatched}


def resources_now(*, meminfo: Callable[[], Mapping[str, int]] = worker_module.read_meminfo,
                  gpu: Callable[[], Mapping[str, Any] | None] = worker_module.gpu_state) -> dict[str, Any]:
    from learnloop.experiments.contextual_embeddings.e1.local import limits

    info = meminfo()
    try:
        state = gpu()
    except Exception:  # noqa: BLE001 - no nvidia-smi: refused below
        state = None
    problems = worker_module.start_problems(limits(), meminfo=info, scope={}, gpu=state, require_scope=False)
    return {"ok": not problems, "problems": problems,
            "host_available_gib": round(info.get("MemAvailable", 0) / worker_module.GIB, 2),
            "swap_used_gib": round((info.get("SwapTotal", 0) - info.get("SwapFree", 0)) / worker_module.GIB, 2),
            "gpu": None if state is None else {key: state[key] for key in ("name", "driver", "total_mib",
                                                                           "free_mib", "used_mib",
                                                                           "utilization_pct")},
            "other_gpu_processes": None if state is None else len(state.get("processes") or [])}


def preflight(plan: Mapping[str, Any], layout: ImportLayout, *, model_dir: Path, env_python: Path,
              verify_weights: bool = False, resources: Callable[[], dict[str, Any]] = resources_now,
              versions: Callable[[Path], dict[str, Any]] = environment_versions) -> dict[str, Any]:
    """Every check the GPU stage needs, without loading anything (no network)."""

    from learnloop.experiments.contextual_embeddings.e1.replay import verify_import

    checks: dict[str, Any] = {}
    try:
        require_frozen(plan, layout)
        checks["plan"] = {"ok": True, "plan_id": plan["plan_id"]}
    except PlanRefused as exc:
        checks["plan"] = {"ok": False, "reason": str(exc)}
    problems = verify_import(layout)
    checks["import"] = {"ok": not problems, "problems": problems}
    checks["replay"] = {"ok": all((item or {}).get("ok") for item in (plan.get("replay") or {})
                                  .get("verification", {}).values()) and bool(plan.get("replay")),
                        "verification": (plan.get("replay") or {}).get("verification")}
    model_problems = worker_module.model_dir_problems(Path(model_dir), e1_pins.MODEL_FILES,
                                                      e1_pins.REMOTE_CODE_FILES, verify_digests=verify_weights)
    checks["model_files"] = {"ok": not model_problems, "problems": model_problems, "digests_verified": verify_weights}
    checks["environment"] = versions(Path(env_python)) if Path(env_python).is_file() else {
        "ok": False, "error": "no interpreter at --env-python"}
    checks["systemd_run"] = {"ok": shutil.which("systemd-run") is not None}
    checks["resources"] = resources()
    meter = GpuMeter(ledger_dir(layout.root))
    left = meter.remaining_s()
    checks["gpu_meter"] = {"ok": left >= MIN_SLOT_S, **meter.report()}
    checks["e0_s1"] = {"ok": all(value == "labels_ok" for value in (plan.get("e0") or {}).get("S1", {}).values()),
                       "decisions": (plan.get("e0") or {}).get("S1"),
                       "note": "advisory: E0's S1 blocking its verdicts blocks E1's verdict too, not its run"}
    required = ("plan", "import", "replay", "model_files", "environment", "systemd_run", "resources", "gpu_meter")
    return {"ready": all(checks[name]["ok"] for name in required), "checks": checks,
            "plan_id": plan.get("plan_id")}


# -- local (GPU) -------------------------------------------------------------------------------
def run_local(plan: Mapping[str, Any], layout: ImportLayout, *, model_dir: Path, launcher: Any,
              check_plan: bool = True) -> dict[str, Any]:
    """ONE scoped worker for every missing v2 document and query (resumable)."""

    from learnloop.experiments.contextual_embeddings.e1.local import build_job, measurements, store_outputs
    from learnloop.experiments.contextual_embeddings.e1.replay import question_texts

    if check_plan:
        require_frozen(plan, layout)
    root = run_root(layout, plan["plan_id"])
    if not _inside_local_root(root):
        raise PlanRefused("the run directory must be under fixtures-local")
    replays = replay_all(layout, root=root)
    store = VectorStore(root / "vectors")
    job, index = build_job(plan["plan_id"], [(item.label, item.snapshot, question_texts(item)) for item in replays],
                           store, model_dir=Path(model_dir))
    if not job["documents"] and not job["queries"]:
        return {"status": "nothing_to_encode", "stored": {}}
    attempts = sorted(path for path in (root / "local").glob("*") if path.is_dir()) if (root / "local").exists() else []
    workdir = root / "local" / f"{len(attempts) + 1:02d}"
    meter = GpuMeter(ledger_dir(layout.root))
    output = launcher(job, workdir, meter=meter, plan_id=plan["plan_id"])
    stored = store_outputs(output, index, store)
    summary = measurements(output)
    summary.update(stored=stored, supervised=output.get("supervised"),
                   planned={"documents": len(job["documents"]), "queries": len(job["queries"])})
    (workdir).mkdir(parents=True, exist_ok=True)
    (workdir / "measurements.json").write_text(json.dumps(summary, sort_keys=True, indent=1, default=str),
                                               encoding="utf-8")
    # The job held private text: it is not kept once the worker is done.
    (workdir / "job.json").unlink(missing_ok=True)
    return summary


# -- labels (paid) -----------------------------------------------------------------------------
def v2_rankings(replayed: Replayed, store: VectorStore) -> tuple[dict[str, dict[str, list[str]]], dict[str, Any]]:
    from learnloop.experiments.contextual_embeddings.e1.local import rank_v2
    from learnloop.experiments.contextual_embeddings.e1.replay import question_texts
    from learnloop.experiments.contextual_embeddings.paid import allowed_units

    texts = question_texts(replayed)
    rankings, missing = {}, {}
    for arm in e1_pins.V2_ARMS:
        ranked, gaps = rank_v2(replayed.snapshot, replayed.all_questions, texts, store, arm,
                               allowed=lambda question: allowed_units(question, replayed.snapshot))
        if ranked:
            rankings[arm] = ranked
        missing[arm] = gaps
    return rankings, missing


def _priority(question: Any) -> tuple[int, str]:
    from learnloop.experiments.contextual_embeddings.paid import NON_PRIMARY_STRATA

    if question.split == "development" and question.stratum not in NON_PRIMARY_STRATA:
        return 0, question.query_id
    return (1 if question.split == "logged" else 2), question.query_id


def run_labels(plan: Mapping[str, Any], layout: ImportLayout, *, authorized: bool = False, dry_run_only: bool = False,
               env_file: Sequence[Path] = (), key_envs: Mapping[str, str] | None = None,
               new_authorization: str | None = None, transport: Any = None, client_factory: Any = None,
               environ: Mapping[str, str] | None = None, check_plan: bool = True) -> dict[str, Any]:
    """The v2 arms' new candidates labelled (and any voyage-context-4 fill)
    under E1's ledger. ``dry_run_only``: the exact counts and estimate, no network."""

    from learnloop.experiments.contextual_embeddings.callers import Checkpoints, LiveRoleCaller, canary_models
    from learnloop.experiments.contextual_embeddings.e1.ledger import authorized_ledger
    from learnloop.experiments.contextual_embeddings.e1.supplement import E1_ROLE_PINS, new_candidates, supplement_all
    from learnloop.experiments.contextual_embeddings.records import ExperimentRecords

    if check_plan:
        require_frozen(plan, layout)
    if any(pin.transport != "anthropic_api" or pin.billing != "metered" for pin in E1_ROLE_PINS.values()):
        raise PlanRefused("every E1 role must be a metered Messages API route (no Codex turn)")
    root = run_root(layout, plan["plan_id"])
    store = VectorStore(root / "vectors")
    key_envs = dict(KEY_ENVS | dict(key_envs or {}))
    replays = replay_all(layout, root=root)
    counts: dict[str, Any] = {}
    work = []
    for replayed in replays:
        rankings, missing = v2_rankings(replayed, store)
        if set(rankings) != set(e1_pins.V2_ARMS):
            raise PlanRefused(f"{replayed.label}: the v2 arms are not fully encoded ({missing}); run the local stage")
        pending = sum(len(new_candidates(question, replayed.labels.get(question.query_id), rankings))
                      for question in replayed.questions)
        fill = sorted(set((replayed.gaps.get("arms_missing") or {})) & set(e1_pins.FILLABLE_ARMS))
        counts[replayed.label] = {"new_candidates": pending, "hosted_fill_arms": fill}
        work.append((replayed, rankings, fill))
    if dry_run_only:
        return {"status": "dry_run", "counts": counts}
    if not authorized:
        raise PlanRefused("the labels stage spends money: it needs --i-am-authorized-to-spend")
    if env_file:
        credentials.load_env_files(list(env_file), key_envs.values())
    ledger = authorized_ledger(layout.root, plan["plan_id"], new_authorization=new_authorization)
    results: dict[str, Any] = {"status": "complete", "copies": {}}
    for replayed, rankings, fill in work:
        label_dir = root / replayed.label
        if fill:
            results["copies"].setdefault(replayed.label, {})["hosted_fill"] = _fill_hosted(
                replayed, fill, ledger=ledger, store=hosted_store(layout, replayed.label, root),
                receipts_path=label_dir / "receipts.jsonl", transport=transport, key_envs=key_envs, environ=environ)
        records = ExperimentRecords(label_dir / "records")
        with records.receipts(f"e1:{plan['plan_id']}:{replayed.label}"):
            caller = LiveRoleCaller(replayed.handle.root, replayed.handle.vault.config, ledger,
                                    checkpoints=Checkpoints(label_dir / "llm"), role_pins=E1_ROLE_PINS,
                                    client_factory=client_factory, records=records,
                                    key_envs={"anthropic": key_envs["anthropic"]}, environ=environ)
            canaries = canary_models(caller)
            questions = sorted(replayed.questions, key=_priority)
            outcome = supplement_all(replayed.snapshot, questions, replayed.labels, rankings, caller)
        save_supplement(label_dir / "supplement.json", outcome)
        results["copies"].setdefault(replayed.label, {}).update(
            counts=outcome["counts"], audits=outcome["audits"], agreement=outcome["agreement"],
            model_canaries=canaries)
        if outcome["counts"]["stopped"] or outcome["audits"]["mandatory_missing"]:
            results["status"] = "incomplete"
    results["ledger"] = ledger.report()
    return results


def _fill_hosted(replayed: Replayed, arms: Sequence[str], *, ledger: Any, store: VectorStore, receipts_path: Path,
                 transport: Any, key_envs: Mapping[str, str], environ: Mapping[str, str] | None) -> dict[str, Any]:
    """The voyage-context-4 vectors E0 never stored, bought under E1's ledger
    (the route's canary first, checked against E0's first canary)."""

    from learnloop.experiments.contextual_embeddings.adapters import AdapterError, Receipts, UrllibTransport
    from learnloop.experiments.contextual_embeddings.budget import E0Stop
    from learnloop.experiments.contextual_embeddings.paid import make_adapter, rank_arm

    done: dict[str, Any] = {}
    for arm in arms:
        try:
            adapter = make_adapter(arm, replayed.snapshot, ledger=ledger, transport=transport or UrllibTransport(),
                                   receipts=Receipts(receipts_path), store=store, qwen_client_factory=None,
                                   key_envs={"voyage": key_envs["voyage"]}, environ=environ)
            done[arm] = {"canary": adapter.canary()}
            rank_arm(arm, replayed.snapshot, replayed.all_questions, adapter)
            done[arm]["status"] = "filled"
        except (E0Stop, AdapterError) as exc:
            done[arm] = {"status": "blocked", "kind": getattr(exc, "kind", type(exc).__name__)}
    return done


def save_supplement(path: Path, outcome: Mapping[str, Any]) -> None:
    def item(value: Any) -> dict[str, Any]:
        return {"query_id": value.query_id, "candidates": value.candidates, "passes": value.passes,
                "pass_sets": [[sorted(chosen) for chosen in sets] for sets in value.pass_sets],
                "malformed": value.malformed, "final": value.final,
                "final_sets": [sorted(chosen) for chosen in value.final_sets], "adjudicated": value.adjudicated,
                "unresolved": value.unresolved, "audit_reason": value.audit_reason, "problems": value.problems}

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"items": [item(value) for value in outcome["items"].values()],
                                "counts": outcome["counts"], "audits": outcome["audits"],
                                "agreement": outcome["agreement"]}, sort_keys=True, indent=1), encoding="utf-8")


def load_supplement(path: Path) -> dict[str, Any]:
    from learnloop.experiments.contextual_embeddings.e1.supplement import Supplement

    if not path.is_file():
        return {"items": {}, "counts": None, "audits": None, "agreement": None}
    data = json.loads(path.read_text(encoding="utf-8"))
    items = {}
    for raw in data["items"]:
        items[raw["query_id"]] = Supplement(
            raw["query_id"], list(raw["candidates"]), [dict(value) for value in raw["passes"]],
            [[frozenset(chosen) for chosen in sets] for sets in raw["pass_sets"]], list(raw["malformed"]),
            dict(raw["final"]), [frozenset(chosen) for chosen in raw["final_sets"]], bool(raw["adjudicated"]),
            bool(raw["unresolved"]), raw.get("audit_reason"), list(raw.get("problems") or []))
    return {"items": items, "counts": data.get("counts"), "audits": data.get("audits"),
            "agreement": data.get("agreement")}


# -- score -------------------------------------------------------------------------------------
def score(plan: Mapping[str, Any], layout: ImportLayout, *, check_plan: bool = True) -> dict[str, Any]:
    from learnloop.experiments.contextual_embeddings.e1.decide import decide_e1
    from learnloop.experiments.contextual_embeddings.e1.supplement import merge
    from learnloop.experiments.contextual_embeddings.evaluate import question_rows

    if check_plan:
        require_frozen(plan, layout)
    root = run_root(layout, plan["plan_id"])
    store = VectorStore(root / "vectors")
    replays = replay_all(layout, root=root)
    copies: dict[str, Any] = {}
    pooled: list[dict[str, Any]] = []
    for replayed in replays:
        rankings, missing = v2_rankings(replayed, store)
        supplement = load_supplement(root / replayed.label / "supplement.json")
        merged = merge(replayed.snapshot, replayed.questions, replayed.labels, supplement["items"])
        all_rankings = {**replayed.rankings, **rankings}
        rows = question_rows(replayed.snapshot, replayed.questions, all_rankings, replayed.labels)
        finalists = dict(replayed.e0_results.get("finalists") or {})
        for row in rows:
            row["vault"] = replayed.label
        copies[replayed.label] = {"rows": rows, "finalists": finalists, "missing": missing, "merged": merged,
                                  "supplement": {key: supplement[key] for key in ("counts", "audits", "agreement")},
                                  "replay": replayed.verification, "e0_s1": ((replayed.e0_results.get("decisions")
                                                                               or {}).get("S1") or {}).get("decision")}
        pooled.extend(rows)
    local = sorted((root / "local").glob("*/measurements.json")) if (root / "local").exists() else []
    measured = [json.loads(path.read_text(encoding="utf-8")) for path in local]
    meter = GpuMeter(ledger_dir(layout.root)).report()
    ledger_file = ledger_dir(layout.root) / f"{plan['plan_id']}.ledger"
    from learnloop.experiments.contextual_embeddings.budget import ledger_spend

    spend = ledger_spend(ledger_file) if ledger_file.exists() else {"committed_usd": "0", "by_category": {}}
    results = decide_e1(plan, copies, pooled, measured=measured, gpu_meter=meter, spend=spend)
    from learnloop.experiments.contextual_embeddings.report import assert_aggregate

    assert_aggregate(results)
    root.mkdir(parents=True, exist_ok=True)
    (root / "results.json").write_text(json.dumps(results, sort_keys=True, indent=1, default=str), encoding="utf-8")
    return results
