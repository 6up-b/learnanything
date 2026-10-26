"""The query student's pins (spec_local_contextual_retrieval_v1 §7.1, §7.2, §9.3, §9.6; P2).

Owner decision 2026-10-26 (amending Q9): the student is **0.6B**. The primary
base is ``perplexity-ai/pplx-embed-v1-0.6b`` (Perplexity's v1 lineage,
bidirectional, mean pooling, MIT); ``Qwen/Qwen3-Embedding-0.6B`` is the only
second screen arm; ``Qwen3.5-0.8B-Base`` is dropped. ``pplx-embed-v2-late-0.6b``
is not a candidate (its space is the v2-late ColBERT multi-vector space).

What is fixed here is either an **identity** (a base's repository, revision,
files and reviewed code; the student's output width and query method: a
change is a new student, never an edit) or a **guardrail** labelled ``keep``
with its reason (memory floors and scopes, the P2 GPU-hours budget, the money
cap, the leakage guards that protect the evaluation, the data budgets of the
learning curve). No quality margin or ranking weight lives here: adoption,
the screen's choice and whether training continues are expected-utility
decisions (``student_decision``), and the student's weight in the fusion is
learned (``fusion``). Optimizer settings are numerical (how a run descends,
never what it decides), labelled with their basis.

This module imports only the standard library: the trainer and the query
process (which run by path in the separate environment, where ``learnloop`` is
not installed) read the same values from the job file the app writes.
"""
from __future__ import annotations

from pathlib import Path

# -- the student bases (identity: researched and downloaded 2026-10-26) ---------------------
#: ``name -> pins``. Files are ``{relative path: (bytes, sha256)}``; ``remote_code`` are the
#: Python files ``trust_remote_code`` imports (read and pinned); ``inert_python`` are Python
#: files present in the snapshot that nothing imports (pinned so an unreviewed file is refused).
STUDENT_BASES: dict[str, dict] = {
    "pplx-embed-v1-0.6b": {
        "repo": "perplexity-ai/pplx-embed-v1-0.6b",
        "revision": "2c4d510dd4a732063c31a0f70193e35067b51fd8",
        "license": "MIT",
        "role": "primary",
        "parameters": 596_000_000,
        "hidden_size": 1024,
        "pooling": "mean",
        "query_prefix": "",
        "bidirectional": True,
        "trust_remote_code": True,
        "files": {
            "config.json": (1_782, "f7865547ecc1c077c5b1f83913fb9816a6586c676ccf3e0f7f00105a1b0c1c6c"),
            "configuration.py": (152, "e914aa73614c91703364c77917313da0821ea04a14d73a7836b5cb40abab1671"),
            "modeling.py": (3_496, "baf57b645c7ca3f9e2bd57bd0de82c540c7b455665f1b0ef5ee2f29d60cb8ed5"),
            "model.safetensors": (2_384_233_112, "2c8d2f64f8268ccd5383b7f9bea8e660349aa6a151bd68a5a47f4c129f2a4974"),
            "tokenizer.json": (11_422_837, "c6fb5c5bbba5fa5f8332edfb6d8aa67bd7fb3d75365b1765f108201698eaebf5"),
            "tokenizer_config.json": (5_638, "29282daeff3615d49f86c9e6c6fefb3a798a516da39f9297f3fcb2a8b39e0180"),
            "special_tokens_map.json": (902, "3c6243480cd551ae25a1c3430fd1b6fe650cd66a70c407200f114f7151a7aaa3"),
            "added_tokens.json": (707, "c0284b582e14987fbd3d5a2cb2bd139084371ed9acbae488829a1c900833c680"),
            "vocab.json": (2_776_833, "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910"),
            "merges.txt": (1_671_853, "8831e4f1a044471340f7c0a83d7bd71306a5b867e95fd870f74d0c5308a904d5"),
            "modules.json": (361, "26a5eb7ef28ba520882a6be1d24b3c52b69d7267fdde3a31cff8fa5692b4c830"),
            "1_Pooling/config.json": (313, "a30548e8bc4255aafe5e5c638f6b15712eebbc8e84ea5988a5835f976c412907"),
            "st_quantize.py": (3_547, "320c54decc6a150bbfbef5eff4765291e66fb7506503ee65776809d99938faad"),
        },
        "remote_code": ("configuration.py", "modeling.py"),
        "inert_python": ("st_quantize.py",),
        #: Downloaded files (``hf download --exclude onnx/* --exclude assets/*``): the ONNX exports are never needed.
        "allow_patterns": ("*.json", "*.py", "*.txt", "model.safetensors", "1_Pooling/*"),
    },
    "qwen3-embedding-0.6b": {
        "repo": "Qwen/Qwen3-Embedding-0.6B",
        "revision": "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3",
        "license": "Apache-2.0",
        "role": "second_arm",
        "parameters": 596_000_000,
        "hidden_size": 1024,
        "pooling": "last_token",
        "query_prefix": "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery:",
        "bidirectional": False,
        "trust_remote_code": False,
        "files": {
            "config.json": (727, "b5bf1f51fc45be473a54718cef92448d90a1be001bf9b9a44b8c7f10a19feaa9"),
            "model.safetensors": (1_191_586_416, "0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd"),
            "tokenizer.json": (11_423_705, "def76fb086971c7867b829c23a26261e38d9d74e02139253b38aeb9df8b4b50a"),
            "tokenizer_config.json": (9_706, "253153d0738ceb4c668d2eff957714dd2bea0b56de772a9fdccd96cbf517e6a0"),
            "vocab.json": (2_776_833, "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910"),
            "merges.txt": (1_671_853, "8831e4f1a044471340f7c0a83d7bd71306a5b867e95fd870f74d0c5308a904d5"),
            "modules.json": (349, "84e40c8e006c9b1d6c122e02cba9b02458120b5fb0c87b746c41e0207cf642cf"),
            "1_Pooling/config.json": (313, "37bf193fa101f19101bfad9c31d3eb0f786e247b7b1e5cb7f007d730eed1ddbd"),
            "config_sentence_transformers.json": (215, "10667c72ddb772627bf1780cb7f86af8e2ae0032b8c243c731172064105c6961"),
            "generation_config.json": (117, "28396d421a2108acce96383f6a7de78008f7f1b17f807958f3c14c51dbfb65fb"),
        },
        "remote_code": (),
        "inert_python": (),
        "allow_patterns": ("*.json", "*.txt", "model.safetensors", "1_Pooling/*"),
    },
}
PRIMARY_BASE = "pplx-embed-v1-0.6b"
#: Dropped by the owner 2026-10-26 (never screened, never downloaded).
DROPPED_BASES = ("Qwen/Qwen3.5-0.8B-Base",)
#: The screen's arms, in order (the projection-only rung runs on the primary base).
SCREEN_BASES = ("pplx-embed-v1-0.6b", "qwen3-embedding-0.6b")

# -- the student's identity (a change is a new student) -------------------------------------
STUDENT_DIMENSIONS = 2048
STUDENT_PRECISION = "bf16"
STUDENT_QUERY_METHOD = "student: base pooling + Linear(hidden->2048), L2-normalized, FP32 output"
TRAINER_VERSION = "query-student-trainer-v1"
SERVER_VERSION = "query-student-server-v1"
CHECKPOINT_FORMAT = "query-student-checkpoint-v1"
#: The recipes, in the order spec §7.1 sets (the screen runs the first two; the
#: recipe stage adds the next two; the choice among them is expected utility).
RECIPES = ("projection_only", "align", "align_kd", "align_kd_mp")
#: keep (identity of the data the curve reads): the nested learning-curve budgets (spec §7.1).
BUDGETS = (2_000, 10_000, 50_000)
#: keep (spec §7.1): questions asked of the generator per passage.
QUERIES_PER_PASSAGE_MIN = 8
QUERIES_PER_PASSAGE_MAX = 12
#: keep (prompt size, operational): passages per generator call.
PASSAGES_PER_CALL = 4
#: keep (prompt size): estimated tokens of permitted text one passage carries at most.
PASSAGE_TOKENS = 600
#: keep (spec §7.1): the teacher's top-k kept per training query for the ranking losses.
TEACHER_TOP_K = 50
#: keep (spec §7.1, §9.6): the longest training or serving query, in the base's tokens.
MAX_QUERY_TOKENS = 512
#: keep (spec §9.6: protecting the evaluation is a rule, not a trade-off; may only tighten).
LEAKAGE_MAX_TEACHER_COS = 0.90
LEAKAGE_MAX_5GRAM_OVERLAP = 0.5
LEAKAGE_NGRAM = 5
#: keep (spec §7.1): epochs per run.
EPOCHS = 3
#: keep (spec §7.1): the chosen recipe runs on at least this many seeds.
FINAL_SEEDS = 3
#: numerical (optimizer, not a decision): AdamW rates. Basis: published fine-tuning practice for
#: BERT-scale encoders (Devlin et al. 2019: 2e-5 to 5e-5) for the full model; a linear map alone
#: takes the usual 1e-3 Adam rate (Kingma and Ba 2015).
LEARNING_RATE_FULL = 2e-5
LEARNING_RATE_HEAD = 1e-3
WEIGHT_DECAY = 0.01
WARMUP_FRACTION = 0.05
GRAD_CLIP_NORM = 1.0
#: numerical (throughput): queries per optimizer step. Batches are tokenized in-process (no loader
#: worker at all, inside spec §7.1's "at most two").
TRAIN_BATCH_SIZE = 64
#: keep (spec §9.3 diagnostics): the depth of the teacher-agreement measure (top-10 recall).
AGREEMENT_K = 10
#: keep (measurement): queries timed for the latency diagnostic on each device.
LATENCY_PROBES = 64

# -- GPU, memory and money guardrails (keep, spec §7.2, §9.6) --------------------------------
#: P2's whole GPU budget: teacher targets, the screen, recipes, seeds and failed runs.
P2_GPU_HOURS_CAP = 6.0
#: Training runs in the same 12G scope and floors as the 9B worker (spec §7.1 "Host side").
TRAIN_SCOPE_MEMORY_MAX = "12G"
#: The query process: its own 4G scope, swap 0.
SERVE_SCOPE_MEMORY_MAX = "4G"
SERVE_SCOPE_MEMORY_MAX_BYTES = 4 * 1024 ** 3
SERVE_SCOPE_SWAP_MAX = "0"
SERVE_MIN_HOST_AVAILABLE_GIB = 6.0
SERVE_MIN_FREE_VRAM_GIB = 4.0
#: keep (GPU budget, §9.3): logged queries one nightly batch re-encodes with the teacher at most
#: (2,000 at E1's 18 ms per query is about 36 s of an already loaded model).
REPLAY_MAX_QUERIES = 2_000
#: keep (operational, §9.2 "nightly"): a replay-only batch may load the 9B once a day at most.
REPLAY_EVERY_HOURS = 24.0
#: keep (operational): the most recent cold starts the start-time distribution keeps.
START_TIMES_KEPT = 50
#: keep (identity check, as the 9B's canaries): a student canary below this is another computation.
STUDENT_CANARY_MIN_COS = 0.999
STUDENT_CANARY_QUERIES = ("When is a matrix invertible?", "What does the power rule say?",
                          "Explain the law of total probability with an example.")
#: keep (operational): the query process's socket accept and read timeout.
SOCKET_TIMEOUT_S = 30.0

#: The query-process idle exit is ``embedding.local.student_idle_minutes`` and the generator's money cap
#: ``embedding.local.student_generator_max_cost_usd`` (config, keep, §9.6).


def students_root(data_root: Path) -> Path:
    """Everything P2 makes lives under the data root (never in a vault or the repository, §11)."""

    return Path(data_root) / "students"


def space_home(data_root: Path, space_id: str) -> Path:
    """The student's home under the space it was trained for (a teacher change retires it)."""

    if not space_id or "/" in space_id or space_id.startswith("."):
        raise ValueError("a space id names one directory")
    return students_root(data_root) / space_id


def bases_manifest_path(data_root: Path) -> Path:
    return students_root(data_root) / "bases.json"


def base_dir(data_root: Path, name: str) -> Path:
    base = STUDENT_BASES[name]
    return Path(data_root) / "models" / f"{base['repo'].replace('/', '--')}@{base['revision']}"


__all__ = [name for name in dir() if name.isupper()] + ["base_dir", "bases_manifest_path", "space_home",
                                                         "students_root"]
