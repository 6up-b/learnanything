"""E1's frozen constants (spec §8, §9, D2): the local model, its files, the
separate environment, the GPU and memory bounds, the $5 plan and the smoke.

Everything here is hashed into the E1 plan id (``e1_pins_fingerprint``), so a
changed bound or model file is a new plan, never a silent change inside one.

**The model (researched 2026-10-23 from the public Hugging Face pages, no
download).** ``perplexity-ai/pplx-embed-v2-context-9b-preview`` at revision
``e2c06a77``: MIT, not gated, a PREVIEW ("embeddings produced with this
preview should not be mixed with embeddings from a future release"). 8.40B
parameters stored in FLOAT32 (33,604,334,528 bytes in 7 shards plus a 33.5 MB
``contextual_head``), Qwen3.5 (3 Gated-DeltaNet linear-attention layers per
full-attention layer, 32 layers, hidden 4096) with an unused vision tower.
Custom code (``trust_remote_code``): ``PplxContextualModel(Qwen3_5Model)``.
``encode(list[list[str]])`` joins a document's chunks as ``"[D] " + c0 +
"<|chunk_sep|>" + c1 ...`` in ONE forward pass and mean-pools each chunk's own
token span; ``encode_queries([[q]])`` prepends the ``[Q] `` token and
mean-pools all tokens. Both project 4096 -> 2048 (an fp32 linear kept in fp32)
and return ``round(tanh(x) * 127)``: int8-valued float32, unnormalized
(Matryoshka 1024 = the first 1024 values, then normalize). No truncation (an
over-limit input raises). The reviewed code's SHA-256 is pinned below; the
worker refuses any other code.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any

E1_HARNESS_VERSION = "e1-harness-v1"

# -- the model -------------------------------------------------------------------------
MODEL_REPO = "perplexity-ai/pplx-embed-v2-context-9b-preview"
MODEL_REVISION = "e2c06a779d45e8db53066735be1b98ffe3412ca3"
MODEL_LICENSE = "mit (model card metadata; no LICENSE file; not gated)"
MODEL_DIMENSIONS = 2048
#: Trained Matryoshka widths ("other truncation sizes were not trained").
MODEL_MATRYOSHKA = (1024, 2048)
MODEL_PARAMETERS = 8_401_083_632
#: Every file the worker reads, with its size and SHA-256 (the LFS digests
#: from the Hugging Face API at ``MODEL_REVISION``; the small text files were
#: fetched and hashed). The preflight checks sizes always and the digests
#: with ``--verify-weights`` (about 34 GB read).
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
#: The reviewed remote code: the worker hashes these before importing anything.
REMOTE_CODE_FILES = ("configuration_pplx_contextual.py", "modeling_pplx_contextual.py")
MODEL_DISK_BYTES = sum(size for size, _digest in MODEL_FILES.values())
#: Free space the download needs (the files plus Hugging Face's partial copies).
DOWNLOAD_FREE_DISK_GIB = 45.0

# -- the separate environment (spec §6: never upgrade the app environment) ---------------
#: The app pins transformers 4.57.6; the model card needs >= 5.4.0. The worker
#: runs in its own virtual environment with these exact pins (both releases
#: are over two weeks old; 5.18.0 is contemporaneous with the model's code).
LOCAL_PYTHON = "3.12"
LOCAL_REQUIREMENTS = ("torch==2.14.0", "transformers==5.18.0", "safetensors", "numpy", "tqdm")
LOCAL_MIN_TRANSFORMERS = (5, 4, 0)

# -- precision (spec §8: BF16 first; FP8 only if measured pressure warrants; LLM.int8 deferred)
PRECISION = "bf16"
DEFERRED_PRECISIONS = {"fp8": "only if measured BF16 memory/latency pressure warrants it (new plan)",
                       "llm_int8": "deferred behind an FP8 failure (spec §9)"}
ATTENTION_IMPLEMENTATION = "sdpa"
#: Modules that must stay fp32 under BF16 loading (the card's ``_keep_in_fp32_modules``).
FP32_MODULES = ("contextual_projection",)

# -- GPU and memory bounds (spec §8, D2) -------------------------------------------------
#: Total GPU-hours for ALL of E1 (failed loads, profiling, indexing included):
#: every worker process's wall time from spawn to exit counts.
GPU_HOURS_CAP = 4.0
#: The process peak target on the device (GiB): exceeded = recorded and the run stops.
DEVICE_PEAK_TARGET_GIB = 20.0
#: The worker's own systemd scope (the owner's terminal was OOM-killed three
#: times this week: a runaway load dies inside this scope, never outside it).
SCOPE_MEMORY_MAX = "12G"
SCOPE_SWAP_MAX = "0"
SCOPE_MEMORY_MAX_BYTES = 12 * 1024 ** 3
#: The worker refuses to start below these measured values.
MIN_HOST_AVAILABLE_GIB = 14.0
MIN_FREE_VRAM_GIB = 22.0
#: No other substantial GPU workload (GLM-OCR, a game, a stream): any other
#: compute process above this, or utilization above that, refuses the start.
MAX_OTHER_GPU_PROCESS_MIB = 1024
MAX_GPU_UTILIZATION_PCT = 15
#: During the run: host MemAvailable below this aborts at once (protects the
#: owner's session even inside the scope's limit).
HOST_FLOOR_GIB = 3.0
SAMPLE_INTERVAL_S = 1.0
#: A worker that has not written a heartbeat for this long is charged up to
#: its last heartbeat plus this (a crash of the orchestrator still counts).
HEARTBEAT_GRACE_S = 60.0
#: SIGTERM grace before SIGKILL when the GPU-hours cap is reached (own child only).
KILL_GRACE_S = 30.0

# -- what one worker process does (spec §8 smoke and profiling) ----------------------------
#: Serialized indexing sizes, smallest first; a failure (OOM included) at one
#: size stops the larger ones. Longer windows are a later plan.
PROFILE_TOKENS = (2048, 4096, 8192)
PROFILE_REPEATS = 3
#: The longest document E1 encodes (tokens, measured by the model's own tokenizer).
MAX_DOCUMENT_TOKENS = 8192
#: Serialized: one document per forward pass (padding never enters the index).
INDEX_BATCH_SIZE = 1
QUERY_BATCH_SIZE = 1
#: Smoke tolerances (cosine of the decoded vectors).
BATCH_INVARIANCE_MIN_COS = 0.995
#: A central chunk in two different contexts must not encode to (nearly) the same vector.
CONTEXT_SENSITIVITY_MAX_COS = 0.9999
#: Public smoke text only (no vault text).
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

# -- money (spec §8: <= $5 additional under a NEW frozen plan with its own hard-cap ledger)
E1_CAP_USD = 5.0
#: Labels for the v2 arms' new candidates and their audits; any voyage-context-4
#: vector the E0 store lacks. Cumulative across every E1 authorization.
E1_ALLOCATION_USD = {"labels_audits": 4.80, "embeddings": 0.20}
E1_MAX_PAID_REQUESTS = 1_000
#: The ledger directory, beside (never inside) E0's ``ledger`` directory: an
#: E1 authorization never carries, seals or reads an E0 ledger.
E1_LEDGER_DIR = ("contextual-embeddings", "e1-ledger")
E1_PLAN_PREFIX = "e1_"
#: Only the v2 arms' top 10 are labelled: every E1 endpoint is @10 (E0 pooled
#: each arm's top 20 because its pool also fed the answers' D1 evidence).
SUPPLEMENT_DEPTH = 10
SUPPLEMENT_PROMPT_VERSION = "e1-supplement-v1"
SUPPLEMENT_ADJUDICATE_VERSION = "e1-supplement-adjudicate-v1"
#: Arms whose missing hosted vectors E1 may buy (the brief: voyage-context-4).
FILLABLE_ARMS = ("R5_grouped", "R5_singleton")

# -- arms and decisions --------------------------------------------------------------------
V2_ARMS = {
    "V2_grouped": {"encoding": "grouped", "recipe": "plain",
                   "description": "pplx-embed-v2-context-9b-preview BF16, E0's 4,096-token grouped windows"},
    "V2_singleton": {"encoding": "singleton", "recipe": "plain",
                     "description": "the same model, one chunk per document (the same-model context control)"},
}
#: E0's representation arms E1 replays from E0's stores (common units, exact cosine).
E0_REPRESENTATION_ARMS = ("R1", "R2", "R3", "R4_grouped", "R4_singleton", "R4_independent",
                          "R5_grouped", "R5_singleton", "R5_independent")
#: Prespecified (before any v2 result): retain local work only for measured
#: additional evidence (spec §8) at the S4 size, else a non-inferior result
#: is kept only for a cost/latency benefit the owner names; otherwise stop.
RETAIN_GAIN_MIN = 0.05
NONINFERIORITY_MARGIN = 0.02
#: Supplementary labels: the same κ gate as E0's S1.
SUPPLEMENT_KAPPA_MIN = 0.60
V2_COMPLETION_MIN = 0.95

# -- estimate assumptions (stated in the plan; the paid stage re-plans from real counts) ---
@dataclass(frozen=True)
class Assumptions:
    #: Expected share of the v2 arms' top-10 slots outside E0's labelled pool.
    new_candidate_share: float = 0.30
    #: Supporting passages shown with the new candidates (E0's required/helpful).
    judged_context_units: int = 5
    label_output_tokens_per_candidate: int = 12
    set_output_tokens: int = 200
    #: Expected share of questions with new candidates that reach the adjudicator.
    adjudicated_share: float = 0.6
    thinking_tokens: dict[str, int] = field(default_factory=lambda: {"claude-sonnet-5-5": 1500,
                                                                     "claude-opus-5-5": 2000})
    #: GPU-time model (upper estimates for a pure-torch linear-attention fallback).
    load_s: float = 600.0
    smoke_s: float = 180.0
    seconds_per_1k_tokens: float = 1.0
    query_s: float = 2.0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


ASSUMPTIONS = Assumptions()


def e1_pins_fingerprint() -> str:
    """One hash of every E1 pin (part of the E1 plan id)."""

    payload = {
        "harness": E1_HARNESS_VERSION, "model": [MODEL_REPO, MODEL_REVISION, MODEL_DIMENSIONS, MODEL_FILES],
        "env": [LOCAL_PYTHON, LOCAL_REQUIREMENTS], "precision": PRECISION, "attention": ATTENTION_IMPLEMENTATION,
        "bounds": [GPU_HOURS_CAP, DEVICE_PEAK_TARGET_GIB, SCOPE_MEMORY_MAX, SCOPE_SWAP_MAX, MIN_HOST_AVAILABLE_GIB,
                   MIN_FREE_VRAM_GIB, MAX_OTHER_GPU_PROCESS_MIB, MAX_GPU_UTILIZATION_PCT, HOST_FLOOR_GIB],
        "work": [PROFILE_TOKENS, PROFILE_REPEATS, MAX_DOCUMENT_TOKENS, INDEX_BATCH_SIZE, QUERY_BATCH_SIZE,
                 BATCH_INVARIANCE_MIN_COS, CONTEXT_SENSITIVITY_MAX_COS, SMOKE_CONTEXT, SMOKE_QUERY],
        "money": [E1_CAP_USD, E1_ALLOCATION_USD, E1_MAX_PAID_REQUESTS, SUPPLEMENT_DEPTH, SUPPLEMENT_PROMPT_VERSION,
                  SUPPLEMENT_ADJUDICATE_VERSION, FILLABLE_ARMS],
        "arms": V2_ARMS, "decisions": [RETAIN_GAIN_MIN, NONINFERIORITY_MARGIN, SUPPLEMENT_KAPPA_MIN,
                                       V2_COMPLETION_MIN],
        "assumptions": ASSUMPTIONS.as_dict(),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def model_identity() -> str:
    """The v2 model's identity in every E1 space id: repo, revision, weight precision."""

    return f"{MODEL_REPO}@{MODEL_REVISION}:{PRECISION}"


def v2_pin():
    """The v2 model as an E0 ``EmbeddingPin`` (its identity fields feed the E0
    space-id formula; it is never sent over HTTP and bills nothing)."""

    from learnloop.experiments.contextual_embeddings.pins import EmbeddingPin

    return EmbeddingPin(
        name="pplx_v2_context_9b", provider="local", model=model_identity(), method="grouped",
        document_endpoint=f"local://{MODEL_REPO}/encode", query_endpoint=f"local://{MODEL_REPO}/encode_queries",
        query_method="encode_queries ([Q] prefix token, mean over all tokens)", dimensions=MODEL_DIMENSIONS,
        output_format="int8", decode_transform="int8_to_fp32_l2_normalize",
        max_tokens_per_document=MAX_DOCUMENT_TOKENS, max_tokens_per_request=MAX_DOCUMENT_TOKENS,
        max_chunks_per_request=16_000, max_documents_per_request=1, price_per_million_upper_bound=0.0,
        price_source="local: no provider billing (GPU-hours are metered instead)", key_env=None,
        contract_source=f"huggingface.co/{MODEL_REPO} @ {MODEL_REVISION} (custom code reviewed 2026-10-23)",
        contract_verified=False,
    )
