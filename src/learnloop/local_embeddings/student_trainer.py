"""The query-student trainer: one run, one recipe, one seed, then exit (spec_local_contextual_retrieval_v1 §7.1, §7.2; P2).

Run ONLY by ``source_retrieval.query_student`` through the local launcher, inside its own
``systemd-run --user --scope -p MemoryMax=12G -p MemorySwapMax=0`` (the 9B worker's scope and
floors, spec §7.1 "Host side"), holding the exclusive GPU lock and the full-suite lock, under
the capped P2 GPU meter, with the SEPARATE environment's interpreter::

    <env>/bin/python -I student_trainer.py --job JOB.json --out OUT.json --heartbeat HB.json

What one run does:

* **Start checks** (the worker's own ``start_problems``: the scope, MemAvailable, free VRAM,
  the workload rule, utilization, the allowance) and the base's pinned files (sizes always;
  SHA-256 of the remote code and of every small file always, of the weights when asked). The
  network is blocked for the whole process.
* **The student**: the base (its own pooling: mean for pplx-embed-v1, last token for
  Qwen3-Embedding; its own query prefix) and a ``Linear(hidden -> 2048)`` head in FP32. Output
  FP32, compared after L2 normalization; never rounded to int8 (spec §7.1).
* **The recipe** (spec §7.1, in its order): ``projection_only`` (base frozen, the head only),
  ``align`` (``1 - cos(student(q), teacher(q))``), ``align_kd`` (plus the KL between the
  teacher's and the student's softmax over the teacher's top-50 documents), ``align_kd_mp``
  (plus a multi-positive contrastive term: every required support of the query's intended set
  is a positive; the hard negatives are the teacher's top-50 from training families only). The
  terms are summed unweighted: any other weight would be a made-up constant, and the recipe is
  itself chosen by expected utility. The temperature comes with the job (the app sets it from
  development data: the spread of the teacher's own top-50 scores).
* **Diagnostics** (never gates, spec §9.3): per development query the cosine to its teacher
  target and the teacher top-10 agreement over the whole document index; latency on the
  training device and on the CPU; the canary vectors per device class.
* **The checkpoint**: ``student.safetensors`` (the head, plus the base's weights unless the
  base stayed frozen) and ``student.json`` in ``out_dir/checkpoint``; the app pins it by
  SHA-256 under the space and moves it into place.

This module imports only the standard library and numpy at load time; torch, transformers and
safetensors are imported inside the functions that need them. The tests drive :func:`run_training`
on the CPU with a tiny random-initialised model and a fake tokenizer (no download).
"""
from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import sys
import threading
import time
import traceback
from typing import Any

import numpy as np

TRAINER_VERSION = "query-student-trainer-v1"


def _worker() -> Any:
    """The 9B worker's probes, sampler and network guard: imported as a package module when
    ``learnloop`` is importable (the tests), else loaded from the sibling file by path (the
    separate environment, where only this directory's two scripts exist)."""

    try:
        from learnloop.local_embeddings import worker  # noqa: PLC0415 - optional package import
        return worker
    except ImportError:
        if "learnloop_local_worker" in sys.modules:
            return sys.modules["learnloop_local_worker"]
        path = Path(__file__).resolve().with_name("worker.py")
        spec = importlib.util.spec_from_file_location("learnloop_local_worker", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


W = _worker()


def sha256_file(path: Path) -> str:
    return W.sha256_file(Path(path))


def base_problems(base_dir: Path, base: Mapping[str, Any], *, verify_weights: bool = False) -> list[str]:
    """Missing or wrong base files: sizes always, digests of the code and small files always,
    of every file when ``verify_weights``; an unpinned Python file is refused."""

    problems = []
    for name, (size, digest) in sorted(base["files"].items()):
        path = Path(base_dir) / name
        if not path.is_file():
            problems.append(f"{name}: missing")
            continue
        if path.stat().st_size != int(size):
            problems.append(f"{name}: size {path.stat().st_size} is not the pinned {size}")
            continue
        if (verify_weights or name.endswith(".py") or path.stat().st_size < 64 * W.MIB) and sha256_file(path) != digest:
            problems.append(f"{name}: SHA-256 differs from the pinned digest")
    allowed = set(base.get("remote_code") or ()) | set(base.get("inert_python") or ())
    unexpected = sorted(str(path.relative_to(base_dir)) for path in Path(base_dir).rglob("*.py")
                        if str(path.relative_to(base_dir)) not in allowed)
    if unexpected:
        problems.append("unreviewed Python files in the base directory: " + ", ".join(unexpected))
    return problems


# -- the student module ---------------------------------------------------------------------------
def build_student(base_model: Any, *, hidden: int, dims: int, pooling: str, frozen_base: bool) -> Any:
    import torch

    class Student(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.base = base_model
            self.head = torch.nn.Linear(hidden, dims).float()
            self.pooling = pooling
            if frozen_base:
                for parameter in self.base.parameters():
                    parameter.requires_grad_(False)

        def forward(self, input_ids: Any, attention_mask: Any) -> Any:
            output = self.base(input_ids=input_ids, attention_mask=attention_mask)
            states = output.last_hidden_state if hasattr(output, "last_hidden_state") else output[0]
            mask = attention_mask.to(states.dtype)
            if self.pooling == "mean":
                pooled = (states * mask.unsqueeze(-1)).sum(1) / mask.sum(1, keepdim=True).clamp(min=1.0)
            elif self.pooling == "last_token":
                last = attention_mask.sum(1).long() - 1
                pooled = states[torch.arange(states.shape[0], device=states.device), last.clamp(min=0)]
            else:
                raise ValueError(f"unknown pooling {self.pooling!r}")
            # The head runs in its own dtype (FP32 in training, BF16 when served); the output is FP32.
            return torch.nn.functional.normalize(self.head(pooled.to(self.head.weight.dtype)).float(), dim=-1)

    return Student()


def hidden_size(model: Any, base: Mapping[str, Any]) -> int:
    """The loaded model's own width (the pinned base's is 1024; a test's tiny model is smaller)."""

    return int(getattr(getattr(model, "config", None), "hidden_size", None) or base["hidden_size"])


def load_base(base_dir: Path, base: Mapping[str, Any], *, device: str) -> tuple[Any, Any]:
    """The pinned base and its tokenizer, offline, FP32 master weights on ``device``."""

    import torch
    from transformers import AutoModel, AutoTokenizer

    model = AutoModel.from_pretrained(str(base_dir), trust_remote_code=bool(base.get("trust_remote_code")),
                                      local_files_only=True, dtype=torch.float32)
    tokenizer = AutoTokenizer.from_pretrained(str(base_dir), local_files_only=True, padding_side="right",
                                              trust_remote_code=bool(base.get("trust_remote_code")))
    return model.to(device), tokenizer


def tokenize(tokenizer: Any, texts: Sequence[str], *, prefix: str, max_tokens: int, device: str) -> tuple[Any, Any]:
    batch = tokenizer([f"{prefix}{text}" if prefix else text for text in texts], padding=True, truncation=True,
                      max_length=max_tokens, return_tensors="pt")
    return batch["input_ids"].to(device), batch["attention_mask"].to(device)


def recipe_loss(student_vectors: Any, teacher_vectors: Any, *, recipe: str, documents: Any | None = None,
                topk: Any | None = None, positives: Sequence[Sequence[int]] | None = None,
                temperature: float = 0.05,
                negatives: Sequence[Sequence[int]] | None = None) -> tuple[Any, dict[str, float]]:
    """Spec §7.1's losses (all terms per-query means, summed unweighted).

    The multi-positive term's hard negatives are ``negatives[row]`` when given: the app's
    permitted manifest (Codex review F3), the teacher's top-k restricted to the query's own
    source, every candidate already from a training family; otherwise the teacher's top-k."""

    import torch

    terms: dict[str, Any] = {"align": (1.0 - (student_vectors * teacher_vectors).sum(-1)).mean()}
    if recipe in ("align_kd", "align_kd_mp"):
        if documents is None or topk is None:
            raise ValueError(f"{recipe} needs the teacher's top-k documents")
        candidates = documents[topk]  # [batch, K, dims], unit rows
        teacher_scores = torch.einsum("bd,bkd->bk", teacher_vectors, candidates) / temperature
        student_scores = torch.einsum("bd,bkd->bk", student_vectors, candidates) / temperature
        terms["kd"] = torch.nn.functional.kl_div(torch.log_softmax(student_scores, -1),
                                                 torch.log_softmax(teacher_scores, -1), log_target=True,
                                                 reduction="batchmean")
        if recipe == "align_kd_mp":
            if positives is None:
                raise ValueError("align_kd_mp needs each query's required supports")
            losses = []
            for row, wanted in enumerate(positives):
                if not wanted:
                    continue
                mined = negatives[row] if negatives is not None else topk[row].tolist()
                pool = sorted({int(index) for index in mined} | {int(index) for index in wanted})
                pool_tensor = torch.tensor(pool, device=student_vectors.device)
                scores = documents[pool_tensor] @ student_vectors[row] / temperature
                is_positive = torch.tensor([index in set(int(w) for w in wanted) for index in pool],
                                           device=student_vectors.device)
                losses.append(torch.logsumexp(scores, 0) - torch.logsumexp(scores[is_positive], 0))
            terms["multi_positive"] = torch.stack(losses).mean() if losses else student_vectors.sum() * 0.0
    total = sum(terms.values())
    return total, {key: float(value.detach()) for key, value in terms.items()}


def encode(student: Any, tokenizer: Any, texts: Sequence[str], *, prefix: str, max_tokens: int, device: str,
           batch_size: int = 64, dtype: Any = None) -> np.ndarray:
    import torch

    rows = []
    student.eval()
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            ids, mask = tokenize(tokenizer, texts[start:start + batch_size], prefix=prefix, max_tokens=max_tokens,
                                 device=device)
            if dtype is not None and device.startswith("cuda"):
                with torch.autocast("cuda", dtype=dtype):
                    rows.append(student(ids, mask).float().cpu().numpy())
            else:
                rows.append(student(ids, mask).float().cpu().numpy())
    return np.concatenate(rows) if rows else np.zeros((0, 0), dtype=np.float32)


def agreement(student: np.ndarray, teacher: np.ndarray, documents: np.ndarray, k: int) -> np.ndarray:
    """Per query: the share of the teacher's top-k over the whole index the student's top-k holds."""

    if not len(student):
        return np.zeros(0)
    teacher_top = np.argsort(-(teacher @ documents.T), axis=1)[:, :k]
    student_top = np.argsort(-(student @ documents.T), axis=1)[:, :k]
    return np.array([len(set(a.tolist()) & set(b.tolist())) / k for a, b in zip(teacher_top, student_top)])


def _load_split(directory: Path, split: str) -> dict[str, Any]:
    texts = json.loads((directory / f"{split}_texts.json").read_text(encoding="utf-8"))
    targets = np.load(directory / f"{split}_targets.npy").astype(np.float32)
    targets /= np.clip(np.linalg.norm(targets, axis=1, keepdims=True), 1e-12, None)
    topk_path = directory / f"{split}_topk.npy"
    positives_path = directory / f"{split}_positives.json"
    negatives_path = directory / f"{split}_negatives.json"
    return {"texts": list(texts), "targets": targets,
            "topk": np.load(topk_path).astype(np.int64) if topk_path.exists() else None,
            "positives": json.loads(positives_path.read_text(encoding="utf-8")) if positives_path.exists() else None,
            "negatives": json.loads(negatives_path.read_text(encoding="utf-8")) if negatives_path.exists() else None}


def run_training(job: Mapping[str, Any], *, model_factory: Callable[..., tuple[Any, Any]] = load_base,
                 device: str | None = None, sampler: Any = None,
                 base_check: Callable[[Mapping[str, Any]], list[str]] | None = None) -> dict[str, Any]:
    """One run: train, measure, save the checkpoint files; returns the output record."""

    import torch

    torch.manual_seed(int(job["seed"]))
    np.random.seed(int(job["seed"]) & 0xFFFFFFFF)
    if device is None:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
    base = job["base"]
    problems = (base_check(job) if base_check is not None
                else base_problems(Path(job["base_dir"]), base, verify_weights=bool(job.get("verify_weights"))))
    if problems:
        return {"status": "refused", "reason": "; ".join(problems[:5])}
    data_dir = Path(job["data_dir"])
    train, dev = _load_split(data_dir, "train"), _load_split(data_dir, "dev")
    documents_np = np.load(data_dir / "documents.npy").astype(np.float32)
    documents_np /= np.clip(np.linalg.norm(documents_np, axis=1, keepdims=True), 1e-12, None)
    recipe = str(job["recipe"])
    started = time.monotonic()
    # Codex review F1: ``load_base``'s device is keyword-only (a positional call raised TypeError).
    base_model, tokenizer = model_factory(Path(job["base_dir"]), base, device=device)
    load_s = time.monotonic() - started
    frozen = recipe == "projection_only"
    student = build_student(base_model, hidden=hidden_size(base_model, base), dims=int(job["dimensions"]),
                            pooling=str(base["pooling"]), frozen_base=frozen).to(device)
    if bool(job.get("gradient_checkpointing")) and not frozen and hasattr(base_model, "gradient_checkpointing_enable"):
        base_model.gradient_checkpointing_enable()
    trainable = [parameter for parameter in student.parameters() if parameter.requires_grad]
    rate = float(job["learning_rate_head"] if frozen else job["learning_rate_full"])
    optimizer = torch.optim.AdamW(trainable, lr=rate, weight_decay=float(job["weight_decay"]))
    batch = int(job["batch_size"])
    epochs = int(job["epochs"])
    steps_total = max(1, epochs * math.ceil(len(train["texts"]) / batch))
    warmup = max(1, int(float(job["warmup_fraction"]) * steps_total))
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer, lambda step: min(1.0, (step + 1) / warmup) * max(0.0, (steps_total - step) / steps_total))
    documents = torch.tensor(documents_np, device=device)
    teacher = torch.tensor(train["targets"], device=device)
    prefix, max_tokens = str(base.get("query_prefix") or ""), int(job["max_query_tokens"])
    temperature = float(job["temperature"])
    autocast = torch.bfloat16 if device.startswith("cuda") else None
    order_rng = np.random.default_rng(int(job["seed"]))
    history = []
    step = 0
    for epoch in range(epochs):
        student.train()
        if frozen:
            student.base.eval()
        order = order_rng.permutation(len(train["texts"]))
        epoch_terms: dict[str, float] = {}
        for start in range(0, len(order), batch):
            if sampler is not None and sampler.abort_reason:
                raise W.Aborted(sampler.abort_reason)
            rows = order[start:start + batch]
            ids, mask = tokenize(tokenizer, [train["texts"][i] for i in rows], prefix=prefix, max_tokens=max_tokens,
                                 device=device)
            if autocast is not None:
                with torch.autocast("cuda", dtype=autocast):
                    vectors = student(ids, mask)
            else:
                vectors = student(ids, mask)
            topk = torch.tensor(train["topk"][rows], device=device) if train["topk"] is not None else None
            positives = [train["positives"][i] for i in rows] if train["positives"] is not None else None
            negatives = [train["negatives"][i] for i in rows] if train["negatives"] is not None else None
            loss, terms = recipe_loss(vectors.float(), teacher[rows], recipe=recipe, documents=documents, topk=topk,
                                      positives=positives, temperature=temperature, negatives=negatives)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(trainable, float(job["grad_clip_norm"]))
            optimizer.step()
            scheduler.step()
            step += 1
            for key, value in terms.items():
                epoch_terms[key] = epoch_terms.get(key, 0.0) + value * len(rows)
        history.append({"epoch": epoch, "steps": step,
                        "loss": {key: round(value / max(len(order), 1), 6) for key, value in epoch_terms.items()}})
    train_s = time.monotonic() - started - load_s
    dev_vectors = encode(student, tokenizer, dev["texts"], prefix=prefix, max_tokens=max_tokens, device=device,
                         dtype=autocast)
    cosines = (dev_vectors * dev["targets"]).sum(1) if len(dev_vectors) else np.zeros(0)
    agreements = agreement(dev_vectors, dev["targets"], documents_np, int(job["agreement_k"]))
    latency = {"device": _latency(student, tokenizer, dev["texts"], prefix, max_tokens, device, autocast,
                                  int(job["latency_probes"]))}
    canaries = {_device_class(device): encode(student, tokenizer, list(job["canary_queries"]), prefix=prefix,
                                              max_tokens=max_tokens, device=device, dtype=autocast).tolist()}
    if device != "cpu":
        student = student.to("cpu").to(torch.bfloat16)
        latency["cpu"] = _latency(student, tokenizer, dev["texts"], prefix, max_tokens, "cpu", None,
                                  max(1, int(job["latency_probes"]) // 4))
        canaries["cpu"] = encode(student, tokenizer, list(job["canary_queries"]), prefix=prefix,
                                 max_tokens=max_tokens, device="cpu").tolist()
    checkpoint = Path(job["out_dir"]) / "checkpoint"
    checkpoint.mkdir(parents=True, exist_ok=True)
    files = save_checkpoint(student, checkpoint, frozen_base=frozen)
    manifest = {"format": job["checkpoint_format"], "trainer": TRAINER_VERSION, "space_id": job["space_id"],
                "base_name": job["base_name"], "base": {key: base[key] for key in ("repo", "revision", "pooling",
                                                                                 "query_prefix", "hidden_size")},
                "recipe": recipe, "seed": int(job["seed"]), "budget": int(job["budget"]), "dims": int(job["dimensions"]),
                "precision": job["precision"], "frozen_base": frozen, "max_query_tokens": max_tokens,
                "files": files, "canaries": canaries, "temperature": temperature,
                # Codex review F9: the checkpoint names the dataset (vault, bank, splits, candidates) it learned.
                "dataset_fingerprint": str(job.get("dataset_fingerprint") or "")}
    (checkpoint / "student.json").write_text(json.dumps(manifest, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    return {"status": "complete", "version": TRAINER_VERSION, "recipe": recipe, "seed": int(job["seed"]),
            "budget": int(job["budget"]), "base_name": job["base_name"], "load_s": round(load_s, 3),
            "train_s": round(train_s, 3), "steps": step, "history": history,
            "dev": {"queries": int(len(dev_vectors)),
                    "median_cos": round(float(np.median(cosines)), 6) if len(cosines) else None,
                    "agreement_mean": round(float(np.mean(agreements)), 6) if len(agreements) else None,
                    "agreements": [round(float(value), 4) for value in agreements]},
            "latency": latency, "checkpoint_dir": str(checkpoint)}


def _device_class(device: str) -> str:
    return "cpu" if device == "cpu" else "gpu"


def _latency(student: Any, tokenizer: Any, texts: Sequence[str], prefix: str, max_tokens: int, device: str,
             dtype: Any, probes: int) -> dict[str, Any]:
    sample = list(texts[:probes]) or ["What is a basis?"]
    timings = []
    for text in sample:
        started = time.monotonic()
        encode(student, tokenizer, [text], prefix=prefix, max_tokens=max_tokens, device=device, batch_size=1,
               dtype=dtype)
        timings.append(time.monotonic() - started)
    timings.sort()
    return {"probes": len(timings), "p50_s": round(timings[len(timings) // 2], 5),
            "p95_s": round(timings[min(len(timings) - 1, int(0.95 * len(timings)))], 5),
            "seconds": [round(value, 5) for value in timings]}


def save_checkpoint(student: Any, directory: Path, *, frozen_base: bool) -> dict[str, str]:
    """The head (and the base unless it stayed frozen) as safetensors; ``{file: sha256}``."""

    from safetensors.torch import save_file

    state = {f"head.{key}": value.detach().float().cpu().contiguous() for key, value in student.head.state_dict().items()}
    if not frozen_base:
        state.update({f"base.{key}": value.detach().cpu().contiguous() for key, value in student.base.state_dict().items()})
    path = Path(directory) / "student.safetensors"
    save_file(state, str(path))
    return {path.name: sha256_file(path)}


def checkpoint_digest(manifest: Mapping[str, Any]) -> str:
    """The checkpoint's pin: SHA-256 over its manifest's identity fields and file digests."""

    core = {key: manifest[key] for key in ("format", "space_id", "base_name", "base", "recipe", "seed", "budget",
                                           "dims", "precision", "frozen_base", "max_query_tokens", "files")}
    core["dataset_fingerprint"] = str(manifest.get("dataset_fingerprint") or "")
    return hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LearnLoop query-student trainer (one run, then exit)")
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--heartbeat", type=Path, required=True)
    args = parser.parse_args(argv)
    job = json.loads(args.job.read_text(encoding="utf-8"))
    private = args.job.parent
    os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
                       "HF_HOME": str(private / "hf_home"), "HF_MODULES_CACHE": str(private / "hf_modules"),
                       "TOKENIZERS_PARALLELISM": "false", "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
    W._guard_network()
    output: dict[str, Any] = {"version": TRAINER_VERSION, "plan_id": job["plan_id"], "status": "started",
                              "environment": {"python": platform.python_version(), "pid": os.getpid()}}
    limits = job["limits"]
    try:
        gpu_now = W.gpu_state()
    except Exception:  # noqa: BLE001 - a refusal below
        gpu_now = None
    problems = W.start_problems(limits, meminfo=W.read_meminfo(), scope=W.scope_limits(), gpu=gpu_now,
                                own_pids=(os.getpid(),))
    if problems:
        output.update(status="refused", reason="; ".join(problems))
        W._atomic_json(args.out, output)
        return 3
    lock = threading.Lock()

    def hard_abort(reason: str) -> None:
        with lock:
            output.update(status="aborted", reason=reason)
            W._atomic_json(args.out, output)
        os._exit(4)

    sampler = W.Sampler(limits, heartbeat=args.heartbeat, meminfo=W.read_meminfo, scope=W.scope_limits,
                        gpu=W.gpu_state, interval=float(limits.get("sample_interval_s", 1.0)), on_hard_abort=hard_abort)
    sampler.sample()
    sampler.start()
    try:
        output.update(run_training(job, sampler=sampler))
    except W.Aborted as exc:
        output.update(status="aborted", reason=str(exc))
    except Exception as exc:  # noqa: BLE001 - recorded whole: the trainer holds no key or provider text
        output.update(status="failed", reason=f"failed: {type(exc).__name__}: {str(exc)[:500]}",
                      traceback=traceback.format_exc())
        print(traceback.format_exc(), file=sys.stderr, flush=True)
    finally:
        sampler.sample()
        sampler.stop()
        output["peaks"] = dict(sampler.peaks)
    W._atomic_json(args.out, output)
    return 0 if output["status"] == "complete" else 3


if __name__ == "__main__":
    sys.exit(main())
