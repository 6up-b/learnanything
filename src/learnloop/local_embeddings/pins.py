"""The local space's pins (spec_local_contextual_retrieval_v1 §4.1, §4.2, §7.2, §9.6).

Moved from E1 (``experiments/contextual_embeddings/e1/pins.py``) for the
production package, which never imports ``learnloop.experiments``
(import-linter ``experiments-stay-outside-production``).
``tests/test_local_embeddings_pins.py`` pins every moved value equal to E1's,
so the two cannot drift apart while E1's record stays frozen.

What stays fixed here is either an **identity** (the model, its files and
reviewed code, the environment: a change is a new space, never an edit) or a
**guardrail** labelled ``keep`` with its reason (memory floors and scopes, the
canary tolerance, the batching default). No ranking weight or quality margin
lives here (§9: those are learned).
"""
from __future__ import annotations

import os
from pathlib import Path

# -- the model (identity: E1 pins, researched 2026-10-23) ------------------------------
MODEL_REPO = "perplexity-ai/pplx-embed-v2-context-9b-preview"
MODEL_REVISION = "e2c06a779d45e8db53066735be1b98ffe3412ca3"
MODEL_DIMENSIONS = 2048
MODEL_FILES: dict[str, tuple[int, str]] = {
    "config.json": (3_180, "8f0ee5fd8901b88b779ec0f094c60db04ca59fcf9b831c420bab325aa5a51236"),
    "configuration_pplx_contextual.py": (852, "fc05839ea7274b6d0c2c02aea7157a247df081bd31f647c8d612e7552ceba99a"),
    "modeling_pplx_contextual.py": (9_318, "090f68c9907f2b055b3f41bd0dfc94ef8250e8a98e390e6d308b8fa34702bd45"),
    "model.safetensors.index.json": (64_671, "cf9bb663fe0cc4333d7b70b206d3e1f50074b4031120d80588e58f2e77b4171d"),
    "tokenizer_config.json": (1_195, "85d5045a11205796e6ec9615f104437813b9d1810debb2669219fe32901eb922"),
    "processor_config.json": (1_300, "14932921ca485d458a04dafd8069fbb0a4505622a48208d19ed247115801385b"),
    "tokenizer.json": (19_989_896, "d76b678db762df7761041239ca8950fb190135c94bb66ce8aeff5a0ff2933cf5"),
    "contextual_head.safetensors": (33_554_536, "073d617eb35536b74598c8aaa3036ba7408c178b525ef27949e8074ffce6a51e"),
    "model-00001-of-00007.safetensors": (4_943_302_192,
                                         "e4dbe24849b8310e1ebad77ac2af380c5a707af35ba1dfd5d40a1883c1d5afb8"),
    "model-00002-of-00007.safetensors": (4_803_180_760,
                                         "786daf6875c2d1cf3aabd0ebbc8ab45383449a5efed8874a88c24af9c13b39bd"),
    "model-00003-of-00007.safetensors": (4_970_987_816,
                                         "60b5429f715daae9cf4f9643934a6ec53a6943f2f190881159e17eec304579f8"),
    "model-00004-of-00007.safetensors": (4_938_611_312,
                                         "e30304189f45dad98b423aa228d3e8a0acca2bdde9b1a6a6e5ac98b78336118e"),
    "model-00005-of-00007.safetensors": (4_953_012_272,
                                         "1b7012b55a946c2859a2f74514899e0cfb644b4c67bd6a7b1a43b4942d7b6057"),
    "model-00006-of-00007.safetensors": (4_821_156_456,
                                         "7594d53d27c4b230a1a68ae06bd82c293bced745f2a0e667a5c345b6efd34f4b"),
    "model-00007-of-00007.safetensors": (4_140_617_632,
                                         "feffec312d10e3d3b25b39c2b62378ae28351a47a58fc3b50bd32e25c33ae208"),
}
REMOTE_CODE_FILES = ("configuration_pplx_contextual.py", "modeling_pplx_contextual.py")
MODEL_DISK_BYTES = sum(size for size, _digest in MODEL_FILES.values())
#: keep (disk guardrail): free space the download needs (the files plus partial copies).
DOWNLOAD_FREE_DISK_GIB = 45.0

# -- the separate environment (identity: never the app environment) --------------------
LOCAL_PYTHON = "3.12"
LOCAL_REQUIREMENTS = ("torch==2.14.0", "transformers==5.18.0", "accelerate==1.15.0", "safetensors==0.8.0",
                      "numpy==2.5.3", "tqdm==4.70.1")
PRECISION = "bf16"
ATTENTION_IMPLEMENTATION = "sdpa"
FP32_MODULES = ("contextual_projection",)
OUTPUT_FORMAT = "int8_valued"
#: E1 measured ordinary cosine; the Qwen space's mean-centring is not applied (§4.2).
SCORE_TRANSFORM = "l2_normalize_cosine"
QUERY_METHOD = "[Q] prefix, mean pool"

# -- memory and GPU guardrails (keep: safety, §9.6; E1 measured these limits) ----------
SCOPE_MEMORY_MAX = "12G"
SCOPE_SWAP_MAX = "0"
SCOPE_MEMORY_MAX_BYTES = 12 * 1024 ** 3
MIN_HOST_AVAILABLE_GIB = 14.0
MIN_FREE_VRAM_GIB = 22.0
MAX_OTHER_GPU_PROCESS_MIB = 1024
MAX_OTHER_GPU_TOTAL_MIB = 3072
FORBIDDEN_GPU_WORKLOADS = ("python", "torch", "glmocr", "glm-ocr", "glm_ocr", "marker")
MAX_GPU_UTILIZATION_PCT = 15
HOST_FLOOR_GIB = 3.0
DEVICE_PEAK_TARGET_GIB = 20.0
SAMPLE_INTERVAL_S = 1.0
HEARTBEAT_GRACE_S = 60.0
KILL_GRACE_S = 30.0
#: keep (operational): a worker is not started with less than this left of a capped meter.
MIN_SLOT_S = 15 * 60.0

# -- what one worker does ----------------------------------------------------------------
#: The window rule itself lives with the windows (``source_retrieval.windows``):
#: it is shared by the local space and the Voyage fallback.
#: The longest document the worker encodes, by the model's OWN tokenizer
#: (never a truncation: an over-limit document is refused and counted).
MAX_DOCUMENT_TOKENS = 8192
INDEX_BATCH_SIZE = 1
QUERY_BATCH_SIZE = 1
BATCH_INVARIANCE_MIN_COS = 0.995
CONTEXT_SENSITIVITY_MAX_COS = 0.9999
#: keep (identity check, §9.6): E1 measured padding/batch invariance at 0.99991,
#: so a canary below this is a different computation, not a quality change.
CANARY_MIN_COS = 0.999
#: P0: the true 8,192-token profile (sizes by the model's own token count).
PROFILE_TOKENS = (2048, 4096, 8192)
PROFILE_REPEATS = 3
#: keep (operational, §9.6): an index batch waits until its oldest owed
#: extraction is this old, so a burst of re-extractions loads the 9B once.
INDEX_BATCH_MINUTES = 15.0

#: Public text only (no vault text): the smoke checks and the fixed canary set.
SMOKE_CONTEXT = {
    "central": "Theorem. Every linearly independent list in a finite-dimensional vector space can be "
               "extended to a basis.",
    "contexts": [
        ["Chapter 2 studies finite-dimensional vector spaces and the length of spanning lists.",
         "Proof. Add vectors from a spanning list one at a time, keeping the list independent."],
        ["A recipe for bread starts with flour, water and salt, kneaded for ten minutes.",
         "The dough then rests overnight in a cool place before baking."],
    ],
}
SMOKE_QUERY = "Can an independent list always be extended to a basis?"
SMOKE_PADDING_DOCUMENT = ["A much longer passage pads the batch. " * 40, "and a second chunk follows. " * 20]
CANARY_DOCUMENTS: tuple[tuple[str, ...], ...] = (
    ("Definition. A matrix is invertible when some matrix multiplies it to the identity.",
     "Theorem. A square matrix is invertible exactly when its determinant is not zero."),
    ("The law of total probability splits an event across a partition of the sample space.",),
    ("Example. Differentiate x squared to get two x, by the power rule.",
     "Exercise. Differentiate x cubed."),
)
CANARY_QUERIES: tuple[str, ...] = ("When is a matrix invertible?", "What does the power rule say?")

WORKER_VERSION = "local-index-worker-v1"


def data_root() -> Path:
    """``$XDG_DATA_HOME/learnloop`` (default ``~/.local/share/learnloop``; Q11)."""

    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "learnloop"


def model_dir(root: Path | None = None) -> Path:
    return (root or data_root()) / "models" / f"{MODEL_REPO.replace('/', '--')}@{MODEL_REVISION}"


def env_dir(root: Path | None = None) -> Path:
    import hashlib

    lock = hashlib.sha256("\n".join((LOCAL_PYTHON, *LOCAL_REQUIREMENTS)).encode()).hexdigest()[:12]
    return (root or data_root()) / "envs" / f"local-embed-{lock}"


def manifest_path(root: Path | None = None) -> Path:
    """The setup record (written only by ``learnloop embeddings local setup``)."""

    return (root or data_root()) / "local-embed.json"


def limits(*, deadline_unix: float | None = None) -> dict:
    """The worker's limits (every one a ``keep`` guardrail above)."""

    return {"memory_max_bytes": SCOPE_MEMORY_MAX_BYTES, "swap_max_bytes": int(SCOPE_SWAP_MAX),
            "min_host_available_gib": MIN_HOST_AVAILABLE_GIB, "min_free_vram_gib": MIN_FREE_VRAM_GIB,
            "max_other_gpu_process_mib": MAX_OTHER_GPU_PROCESS_MIB,
            "max_other_gpu_total_mib": MAX_OTHER_GPU_TOTAL_MIB,
            "forbidden_gpu_workloads": list(FORBIDDEN_GPU_WORKLOADS),
            "max_gpu_utilization_pct": MAX_GPU_UTILIZATION_PCT, "host_floor_gib": HOST_FLOOR_GIB,
            "device_peak_target_gib": DEVICE_PEAK_TARGET_GIB, "sample_interval_s": SAMPLE_INTERVAL_S,
            "hard_abort_grace_s": KILL_GRACE_S, "deadline_unix": deadline_unix}
