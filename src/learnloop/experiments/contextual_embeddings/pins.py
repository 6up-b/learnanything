"""E0's frozen constants: models, routes, provider contracts, prices, caps, seeds.

Everything a paired comparison depends on is pinned here and hashed into the
run plan (``plan.freeze``), so a changed pin is a new run, never a silent
change inside one.

**Verification status.** This stage ran offline. Every external fact below
(endpoint paths, request and response shapes, limits, query methods, prices)
comes from the spec's §3 list of contracts *to validate* and is flagged
``contract_verified=False`` / ``price_verified=False``. The paid run's first
step (``learnloop experiments e0 contracts``, one tiny canary request per
adapter) validates the shape; an arm whose canary fails or whose shape
differs is blocked for contract review and reported, never substituted
(spec §5.4, §6). Prices are conservative **upper bounds** used for
admission: the ledger reserves at the bound and reconciles to the provider's
reported cost when one is returned, so an over-estimate can only stop work
early, never overspend.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from typing import Any

#: The harness version: part of every run id and artifact key.
HARNESS_VERSION = "e0-harness-v1"

# -- the D1 baseline (spec §1, §11 row 1) --------------------------------------------
#: The tutor delivery fixes stage, consumed as D1 (merged onto main).
DELIVERY_FIXES = {
    "merge_commit": "275fd5f7e",
    "implementation_commits": ["43060df29", "0fa0ec1b4"],
    "review": "docs/reviews/tutor-delivery-fixes.md",
    "policy": {
        "neighbours": "nearest content blocks both sides, i-1, i+1, widening to 3 a side",
        "blocks": "complete canonical blocks; one explicit token budget, trims recorded",
        "references": "numbered references followed within the same extraction (max 4)",
        "d0_kill_switch": "tutor_qa.expanded_delivery = false, tutor_qa.resolve_references = false",
    },
}
#: D1's frozen retrieval-evidence ceiling (tutor tokens, chars/4), spec §5.3.
D1_EVIDENCE_TOKENS = 8192
#: The tutor generator's context limit a D2/D3 delivery must fit (tokens,
#: conservative): past it the arm records ``does_not_fit`` and the named
#: bounded fallback runs instead (never a silent truncation).
GENERATOR_CONTEXT_TOKENS = 128_000
#: Generator reserves counted apart from evidence (system, history, output).
GENERATOR_RESERVES = {"system": 2_000, "history": 2_000, "output": 2_000}

# -- money (spec §6) -----------------------------------------------------------------
#: The hard E0 ceiling across ALL paid calls, providers, copies and stages.
E0_CAP_USD = 25.0
#: §6's proposed allocation; enforced as category sub-caps inside the cap.
ALLOCATION_USD = {
    "embeddings": 2.0,
    "drafting_context": 5.0,
    "labels_audits": 10.0,
    "answers_verification": 8.0,
}
#: Retries per request: transient failures only; auth and contract errors none.
TRANSIENT_RETRIES = 2
REQUEST_TIMEOUT_S = 120.0
#: Total wall time one paid run may take before it stops cleanly.
MAX_WALL_S = 6 * 3600.0
#: The paid-call cap of one run (every attempt counts).
MAX_PAID_REQUESTS = 6_000

# -- determinism ---------------------------------------------------------------------
SEED = 20261021
BOOTSTRAP_RESAMPLES = 10_000
#: Agreement samples the adjudicator audits (spec §5.2): 20%.
AUDIT_SAMPLE_SHARE = 0.20

# -- representation (spec §4.1) ------------------------------------------------------
#: Grouped windows: tokens per window, chunk markers included.
WINDOW_TOKENS = 4096
#: Tokens counted per chunk for its boundary marker inside a window.
CHUNK_MARKER_TOKENS = 8
#: A block larger than this is split deterministically (offsets kept).
UNIT_MAX_TOKENS = 1024
#: Transcript captions merge toward this range (within one section).
CAPTION_TARGET_TOKENS = (300, 600)
TOP_K = 10
#: Candidates pooled from every arm for labelling (spec §5.2: top-20).
POOL_DEPTH = 20

# -- labels and stop rules (spec §5.2, §7) -------------------------------------------
KAPPA_MIN = 0.60
#: An arm scored on fewer than this share of its questions is "materially incomplete" (S1).
ARM_COMPLETION_MIN = 0.95
#: Independent source families below which intervals are exploratory only.
MIN_INDEPENDENT_FAMILIES = 5
S2_NONINFERIORITY_MARGIN = 0.02
S3_CONTEXT_GAIN_MIN = 0.03
S3_QWEN_WITHIN = 0.02
S4_GAIN_MIN = 0.05

# -- bank (spec §5.1) ----------------------------------------------------------------
SMOKE_CASES = 16
DEV_QUESTIONS = (60, 80)
DEV_QUESTION_TARGET = 72
#: Strata of the development bank (spec §5.1.3), with target counts.
DEV_STRATA = {
    "reader_deictic": 20,
    "distant_same_source": 20,
    "intent_explain": 4,
    "intent_remediate": 4,
    "intent_alternative": 4,
    "intent_worked_example": 4,
    "intent_compare": 4,
    "direct_lookup": 6,
    "no_support": 6,
}


def conservative_tokens(text: str | None) -> int:
    """The frozen token bound for provider limits, windows and cost estimates:
    UTF-8 bytes / 3, rounded up. Every common subword tokenizer emits at most
    about one token per 3 bytes of English or LaTeX, so a window packed under
    this bound never passes a provider's token limit and an estimate is never
    low. (Delivery budgets keep the production chars/4 estimate: D1 is the
    production behaviour.)"""

    return math.ceil(len((text or "").encode("utf-8")) / 3)


@dataclass(frozen=True)
class EmbeddingPin:
    """One embedding model's frozen contract (unverified until its canary)."""

    name: str
    provider: str
    model: str
    #: grouped: a document is a list of chunks encoded in one context;
    #: independent: one text per vector.
    method: str
    document_endpoint: str
    query_endpoint: str
    #: How queries are encoded (validated by the canary before any paid run).
    query_method: str
    dimensions: int
    output_format: str
    #: How a raw output becomes the scoring copy.
    decode_transform: str
    max_tokens_per_document: int
    max_tokens_per_request: int
    max_chunks_per_request: int
    max_documents_per_request: int
    price_per_million_upper_bound: float
    price_source: str
    key_env: str | None
    contract_source: str
    contract_verified: bool = False
    price_verified: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


#: The required embedding families (spec §5.4: R4 and R5 are in E0).
EMBEDDING_PINS: dict[str, EmbeddingPin] = {
    "qwen3_8b": EmbeddingPin(
        name="qwen3_8b", provider="openrouter", model="qwen/qwen3-embedding-8b", method="independent",
        document_endpoint="https://openrouter.ai/api/v1/embeddings",
        query_endpoint="https://openrouter.ai/api/v1/embeddings",
        query_method="instruct_prefix (learnloop.ai.providers.openai_embedding.prefixed_text)",
        dimensions=4096, output_format="float", decode_transform="l2_normalize",
        max_tokens_per_document=32_768, max_tokens_per_request=300_000, max_chunks_per_request=64,
        max_documents_per_request=64, price_per_million_upper_bound=0.03,
        price_source="embedding.price_per_million_tokens default (0.03); published 0.01 (ai.embedding)",
        key_env="OPENROUTER_API_KEY",
        contract_source="the production adapter (learnloop.ai.providers.openai_embedding)",
        contract_verified=True, price_verified=True,
    ),
    "pplx_context_4b": EmbeddingPin(
        name="pplx_context_4b", provider="perplexity", model="pplx-embed-context-v1-4b", method="grouped",
        document_endpoint="https://api.perplexity.ai/v1/contextualizedembeddings",
        query_endpoint="https://api.perplexity.ai/v1/contextualizedembeddings",
        query_method="single_chunk_document (to validate: the documented query method of the contextual model)",
        dimensions=2560, output_format="int8", decode_transform="int8_to_fp32_l2_normalize",
        max_tokens_per_document=32_000, max_tokens_per_request=120_000, max_chunks_per_request=16_000,
        max_documents_per_request=512, price_per_million_upper_bound=0.20,
        price_source="conservative upper bound, unverified offline (spec §3)",
        key_env="PERPLEXITY_API_KEY",
        contract_source="spec §3: /v1/contextualizedembeddings, nested document/chunk inputs, 32K/doc, "
                        "120K/request, 16,000 chunks, int8 outputs (reported, unverified)",
    ),
    "pplx_4b": EmbeddingPin(
        name="pplx_4b", provider="perplexity", model="pplx-embed-v1-4b", method="independent",
        document_endpoint="https://api.perplexity.ai/v1/embeddings",
        query_endpoint="https://api.perplexity.ai/v1/embeddings",
        query_method="documented query encoder of pplx-embed-v1-4b (to validate before calls, spec §5.4)",
        dimensions=2560, output_format="int8", decode_transform="int8_to_fp32_l2_normalize",
        max_tokens_per_document=32_000, max_tokens_per_request=120_000, max_chunks_per_request=512,
        max_documents_per_request=512, price_per_million_upper_bound=0.20,
        price_source="conservative upper bound, unverified offline (spec §3)",
        key_env="PERPLEXITY_API_KEY",
        contract_source="spec §5.4 independent sibling (reported, unverified)",
    ),
    "voyage_context_4": EmbeddingPin(
        name="voyage_context_4", provider="voyage", model="voyage-context-4", method="grouped",
        document_endpoint="https://api.voyageai.com/v1/contextualizedembeddings",
        query_endpoint="https://api.voyageai.com/v1/contextualizedembeddings",
        query_method="input_type=query, one single-chunk input",
        dimensions=1024, output_format="float", decode_transform="l2_normalize",
        max_tokens_per_document=32_000, max_tokens_per_request=120_000, max_chunks_per_request=16_000,
        max_documents_per_request=1_000, price_per_million_upper_bound=0.30,
        price_source="conservative upper bound, unverified offline (docs.voyageai.com/docs/pricing)",
        key_env="VOYAGE_API_KEY",
        contract_source="docs.voyageai.com contextualized chunk embeddings (reported, unverified)",
    ),
    "voyage_4_large": EmbeddingPin(
        name="voyage_4_large", provider="voyage", model="voyage-4-large", method="independent",
        document_endpoint="https://api.voyageai.com/v1/embeddings",
        query_endpoint="https://api.voyageai.com/v1/embeddings",
        query_method="input_type=query",
        dimensions=1024, output_format="float", decode_transform="l2_normalize",
        max_tokens_per_document=32_000, max_tokens_per_request=120_000, max_chunks_per_request=1_000,
        max_documents_per_request=1_000, price_per_million_upper_bound=0.30,
        price_source="conservative upper bound, unverified offline (docs.voyageai.com/docs/pricing)",
        key_env="VOYAGE_API_KEY",
        contract_source="docs.voyageai.com embeddings (reported, unverified)",
    ),
}


@dataclass(frozen=True)
class RolePin:
    """One paid LLM role: its exact route, model, transport and price bound."""

    role: str
    provider_profile: str
    transport: str
    model: str
    reasoning_effort: str | None
    #: "subscription" (Codex: no marginal bill, tallied estimated_only) or "metered".
    billing: str
    category: str
    output_tokens: int
    input_price_per_million: float
    output_price_per_million: float
    price_source: str
    prompt_version: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


#: OpenRouter list prices plus a 10% margin (fees, rounding): upper bounds.
_SONNET = (2.00 * 1.1, 10.00 * 1.1, "Anthropic list $2/$10 per MTok (claude-sonnet-5-5, cached 2026-10-06) +10%")
_LUNA = (0.0, 0.0, "Codex subscription (owner decision 2026-10-12): no marginal bill, estimated_only")
_SOL = (0.0, 0.0, "Codex subscription (owner decision 2026-10-12): no marginal bill, estimated_only")

ROLE_PINS: dict[str, RolePin] = {
    # Strong writer (spec §5.1, D10): GPT-6 Luna through Codex.
    "writer": RolePin("writer", "codex_luna", "codex_sdk", "gpt-6-luna", "low", "subscription",
                      "drafting_context", 4_000, _LUNA[0], _LUNA[1], _LUNA[2], "e0-writer-v1"),
    # R3's 50-100-token chunk context, generated once without benchmark queries.
    "context": RolePin("context", "codex_luna", "codex_sdk", "gpt-6-luna", "low", "subscription",
                       "drafting_context", 4_000, _LUNA[0], _LUNA[1], _LUNA[2], "e0-context-v1"),
    # Two independent label passes, different models, blinded and reordered.
    "label_a": RolePin("label_a", "codex_luna", "codex_sdk", "gpt-6-luna", "low", "subscription",
                       "labels_audits", 2_000, _LUNA[0], _LUNA[1], _LUNA[2], "e0-label-v1"),
    "label_b": RolePin("label_b", "codex_low", "codex_sdk", "gpt-5.6-sol", "low", "subscription",
                       "labels_audits", 2_000, _SOL[0], _SOL[1], _SOL[2], "e0-label-v1"),
    # The named strong adjudicator: a different family from the writer and both passes.
    "adjudicator": RolePin("adjudicator", "e0_openrouter_sonnet", "openrouter", "anthropic/claude-sonnet-5.5",
                           None, "metered", "labels_audits", 2_000, _SONNET[0], _SONNET[1], _SONNET[2],
                           "e0-adjudicate-v1"),
    # The same tutor for every delivery and retrieval arm (the production tutor route).
    "tutor": RolePin("tutor", "codex_low", "codex_sdk", "gpt-5.6-sol", "low", "subscription",
                     "answers_verification", 2_000, _SOL[0], _SOL[1], _SOL[2], "e0-tutor-v1"),
    "judge_a": RolePin("judge_a", "codex_luna", "codex_sdk", "gpt-6-luna", "low", "subscription",
                       "answers_verification", 1_000, _LUNA[0], _LUNA[1], _LUNA[2], "e0-judge-v1"),
    "judge_b": RolePin("judge_b", "codex_low", "codex_sdk", "gpt-5.6-sol", "low", "subscription",
                       "answers_verification", 1_000, _SOL[0], _SOL[1], _SOL[2], "e0-judge-v1"),
    "judge_adjudicator": RolePin("judge_adjudicator", "e0_openrouter_sonnet", "openrouter",
                                 "anthropic/claude-sonnet-5.5", None, "metered", "answers_verification",
                                 1_000, _SONNET[0], _SONNET[1], _SONNET[2], "e0-judge-adjudicate-v1"),
}

#: The OpenRouter profile the metered roles use (added to an in-memory config
#: of the copy only; no vault file or default changes).
EXPERIMENT_PROFILES = {
    "e0_openrouter_sonnet": {
        "type": "openrouter", "model": "anthropic/claude-sonnet-5.5",
        "base_url": "https://openrouter.ai/api/v1", "api_key_env": "OPENROUTER_API_KEY",
    },
}

#: Key environment names (spec D13; configurable with CLI flags).
DEFAULT_KEY_ENVS = {"perplexity": "PERPLEXITY_API_KEY", "voyage": "VOYAGE_API_KEY",
                    "openrouter": "OPENROUTER_API_KEY"}


@dataclass(frozen=True)
class ArmPin:
    """A named arm: what it encodes, with which model, how it searches."""

    arm: str
    kind: str  # "delivery" | "representation" | "system"
    description: str
    embedding: str | None = None
    encoding: str | None = None  # "singleton" | "grouped" | "independent" | None
    recipe: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)


DELIVERY_ARMS = {
    "D0": ArmPin("D0", "delivery", "today's context: the neighbour defect and the 240/600 cuts (kill switch off)"),
    "D1": ArmPin("D1", "delivery", "fixed delivery: complete blocks, nearest neighbours, references, 8,192 tokens"),
    "D2": ArmPin("D2", "delivery", "the whole permitted section containing the selection"),
    "D3": ArmPin("D3", "delivery", "the whole permitted source (does_not_fit -> named fallback D3_section)"),
}

RETRIEVAL_ARMS = {
    "R0": ArmPin("R0", "system", "today's effective path on the copy (keyword-only when dense is off)",
                 recipe="production"),
    "R1": ArmPin("R1", "representation", "Qwen, production recipe text on common units, exact cosine",
                 embedding="qwen3_8b", encoding="independent", recipe="production_recipe"),
    "R1_service": ArmPin("R1_service", "system", "find_sources RRF/intent path vs first-page dense-plus-BM25",
                         embedding="qwen3_8b", recipe="find_sources"),
    "R2": ArmPin("R2", "representation", "Qwen + deterministic title, section path, environment label, "
                 "bounded preceding text", embedding="qwen3_8b", encoding="independent", recipe="deterministic_header"),
    "R3": ArmPin("R3", "representation", "Qwen + 50-100-token LLM chunk context from permitted text",
                 embedding="qwen3_8b", encoding="independent", recipe="llm_context"),
    "R3_bm25": ArmPin("R3_bm25", "representation", "contextual BM25 over R3's headers (separately reported add-on)",
                      recipe="contextual_bm25"),
    "R4_grouped": ArmPin("R4_grouped", "representation", "pplx-embed-context-v1-4b grouped windows",
                         embedding="pplx_context_4b", encoding="grouped", recipe="plain"),
    "R4_singleton": ArmPin("R4_singleton", "representation", "pplx-embed-context-v1-4b, one chunk per document",
                           embedding="pplx_context_4b", encoding="singleton", recipe="plain"),
    "R4_independent": ArmPin("R4_independent", "representation", "pplx-embed-v1-4b sibling",
                             embedding="pplx_4b", encoding="independent", recipe="plain"),
    "R5_grouped": ArmPin("R5_grouped", "representation", "voyage-context-4 grouped windows",
                         embedding="voyage_context_4", encoding="grouped", recipe="plain"),
    "R5_singleton": ArmPin("R5_singleton", "representation", "voyage-context-4, one chunk per document",
                           embedding="voyage_context_4", encoding="singleton", recipe="plain"),
    "R5_independent": ArmPin("R5_independent", "representation", "voyage-4-large via the Voyage API",
                             embedding="voyage_4_large", encoding="independent", recipe="plain"),
}


def pins_fingerprint() -> str:
    """One hash of every pin above (part of the run id)."""

    payload = {
        "harness": HARNESS_VERSION,
        "delivery_fixes": DELIVERY_FIXES,
        "embeddings": {key: pin.as_dict() for key, pin in sorted(EMBEDDING_PINS.items())},
        "roles": {key: pin.as_dict() for key, pin in sorted(ROLE_PINS.items())},
        "arms": {key: asdict(pin) for key, pin in sorted({**DELIVERY_ARMS, **RETRIEVAL_ARMS}.items())},
        "numbers": {
            "cap": E0_CAP_USD, "allocation": ALLOCATION_USD, "window": WINDOW_TOKENS,
            "marker": CHUNK_MARKER_TOKENS, "unit_max": UNIT_MAX_TOKENS, "caption": CAPTION_TARGET_TOKENS,
            "d1": D1_EVIDENCE_TOKENS, "top_k": TOP_K, "pool": POOL_DEPTH, "seed": SEED,
            "bootstrap": BOOTSTRAP_RESAMPLES, "kappa": KAPPA_MIN, "retries": TRANSIENT_RETRIES,
        },
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
