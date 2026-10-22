"""E0's frozen constants: models, routes, provider contracts, prices, caps, seeds.

Everything a paired comparison depends on is pinned here and hashed into the
run plan (``plan.freeze``), so a changed pin is a new run, never a silent
change inside one.

**Verification status.** This stage ran offline. Every external fact below
(endpoint paths, request and response shapes, limits, query methods, prices)
comes from the spec's §3 list of contracts *to validate* and is flagged
``contract_verified=False``. The paid run's first step (one public canary per
embedding route, document AND query, Qwen included) validates the shape; an
arm whose canary fails or whose shape differs is blocked for contract review
and reported, never substituted (spec §5.4, §6).

**Prices (fix round 4, High 2).** Every metered pin carries
``price_verified = PriceVerification(source_url, checked_on)``, empty by
default; the orchestrator verified each price on the providers' published
price pages on 2026-10-21 and the records below are exactly theirs (Voyage's
free tier is noted and never assumed). Admission refuses any request priced by an
unverified pin. Each reservation is the request's hard maximum charge (the
input token upper bound plus the output bound sent, at the verified price);
a settlement above its reservation halts the whole run at once (the ledger
records the overage and refuses every later request).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from typing import Any

#: The harness version: part of every run id and artifact key.
HARNESS_VERSION = "e0-harness-v2"

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
#: The metered paid-call cap of one authorization (every metered attempt counts).
MAX_PAID_REQUESTS = 6_000
#: The Codex (subscription) request allowance of one authorization: every
#: physical subscription request (retries and JSON repairs included) counts,
#: persisted in the canonical ledger and enforced before each request
#: (orchestrator ruling 2026-10-21, fix round 4: Codex requests stay bounded).
MAX_SUBSCRIPTION_REQUESTS = 600
#: The re-plan (2026-10-22) makes NO Codex call at all: the paid run's ledger
#: is created with a Codex allowance of zero, so any subscription request is
#: refused before it is sent (fail closed).
PAID_RUN_SUBSCRIPTION_ALLOWANCE = 0


@dataclass(frozen=True)
class PriceVerification:
    """Where and when a metered price was checked against the provider's
    published price page. Empty by default: the ORCHESTRATOR fills it from
    the providers' price pages before authorizing a paid run (never from
    memory). An empty or partial record means the price is unverified, and
    admission refuses every request priced by it (fix round 4, High 2)."""

    source_url: str = ""
    checked_on: str = ""
    #: What the price page also says that admission deliberately ignores (a free tier).
    note: str = ""

    @property
    def verified(self) -> bool:
        import re

        return (self.source_url.startswith("https://") and len(self.source_url) > len("https://")
                and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", self.checked_on)))

    def as_dict(self) -> dict[str, str]:
        value = {"source_url": self.source_url, "checked_on": self.checked_on}
        if self.note:
            value["note"] = self.note
        return value


UNVERIFIED = PriceVerification()

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
#: "No Reader latency regression" (S2, S4): an arm's paired p50 and p95 may exceed the
#: incumbent's by at most this share (measurement noise), and its p95 must meet the
#: frozen Reader deadline. Pinned before any result (Codex review F9).
LATENCY_REGRESSION_TOLERANCE = 0.10

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


#: Special tokens a tokenizer may add around one input (BOS/EOS, separators).
TOKEN_BOUND_SPECIAL = 8


def token_estimate(text: str | None) -> int:
    """A token ESTIMATE (UTF-8 bytes / 3, rounded up): typical for English and
    LaTeX under common subword tokenizers, but not a bound (dense notation,
    punctuation or poorly compressible text tokenize above it; Codex review
    F15). Used only where an estimate is labelled as one: the dry-run plan,
    the unit cap and the window packing target. Delivery budgets keep the
    production chars/4 estimate (D1 is the production behaviour)."""

    return math.ceil(len((text or "").encode("utf-8")) / 3)


def token_upper_bound(text: str | None) -> int:
    """A guaranteed token UPPER BOUND: UTF-8 bytes plus the special-token
    allowance. A byte-level BPE (GPT, Qwen) or a byte-fallback SentencePiece
    tokenizer emits at least one byte per token, so no input tokenizes above
    its byte count. Used for every provider limit (per document, per request,
    per query), for whole-segment fits and for paid admission reservations, so
    a request admitted under it can neither pass a provider limit nor cost
    more input than was reserved (Codex review F15)."""

    return len((text or "").encode("utf-8")) + TOKEN_BOUND_SPECIAL


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
    #: The price's published source and check date (empty: unverified, refused).
    price_verified: PriceVerification = UNVERIFIED

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


#: When the orchestrator checked the published prices (fix round 4 follow-up).
PRICES_CHECKED_ON = "2026-10-21"
#: Voyage's free tier is never assumed: admission charges the full price.
VOYAGE_FREE_TIER_NOTE = ("the first 200M tokens are free per account; E0 admits and reconciles at the full "
                         "$0.12 per 1M tokens and never assumes the free tier")


def _verified(source_url: str, *, note: str = "") -> PriceVerification:
    return PriceVerification(source_url, PRICES_CHECKED_ON, note)


#: The required embedding families (spec §5.4: R4 and R5 are in E0).
EMBEDDING_PINS: dict[str, EmbeddingPin] = {
    "qwen3_8b": EmbeddingPin(
        name="qwen3_8b", provider="openrouter", model="qwen/qwen3-embedding-8b", method="independent",
        document_endpoint="https://openrouter.ai/api/v1/embeddings",
        query_endpoint="https://openrouter.ai/api/v1/embeddings",
        query_method="instruct_prefix (learnloop.ai.providers.openai_embedding.prefixed_text)",
        dimensions=4096, output_format="float", decode_transform="l2_normalize",
        max_tokens_per_document=32_768, max_tokens_per_request=300_000, max_chunks_per_request=64,
        max_documents_per_request=64, price_per_million_upper_bound=0.01,
        price_source="OpenRouter: $0.01 per 1M input tokens (orchestrator-verified 2026-10-21)",
        price_verified=_verified("https://openrouter.ai/qwen/qwen3-embedding-8b/pricing"),
        key_env="OPENROUTER_API_KEY",
        contract_source="the production adapter (learnloop.ai.providers.openai_embedding)",
        contract_verified=True,
    ),
    "pplx_context_4b": EmbeddingPin(
        name="pplx_context_4b", provider="perplexity", model="pplx-embed-context-v1-4b", method="grouped",
        document_endpoint="https://api.perplexity.ai/v1/contextualizedembeddings",
        query_endpoint="https://api.perplexity.ai/v1/contextualizedembeddings",
        query_method="single_chunk_document (to validate: the documented query method of the contextual model)",
        dimensions=2560, output_format="int8", decode_transform="int8_to_fp32_l2_normalize",
        max_tokens_per_document=32_000, max_tokens_per_request=120_000, max_chunks_per_request=16_000,
        max_documents_per_request=512, price_per_million_upper_bound=0.05,
        price_source="Perplexity: $0.05 per 1M tokens (orchestrator-verified 2026-10-21)",
        price_verified=_verified("https://docs.perplexity.ai/docs/pricing"),
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
        max_documents_per_request=512, price_per_million_upper_bound=0.03,
        price_source="Perplexity: $0.03 per 1M tokens (orchestrator-verified 2026-10-21)",
        price_verified=_verified("https://docs.perplexity.ai/docs/pricing"),
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
        max_documents_per_request=1_000, price_per_million_upper_bound=0.12,
        price_source="Voyage: $0.12 per 1M tokens, admitted at the full price (orchestrator-verified 2026-10-21)",
        price_verified=_verified("https://docs.voyageai.com/docs/pricing", note=VOYAGE_FREE_TIER_NOTE),
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
        max_documents_per_request=1_000, price_per_million_upper_bound=0.12,
        price_source="Voyage: $0.12 per 1M tokens, admitted at the full price (orchestrator-verified 2026-10-21)",
        price_verified=_verified("https://docs.voyageai.com/docs/pricing", note=VOYAGE_FREE_TIER_NOTE),
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
    #: "metered" for every E0 role (re-plan 2026-10-22: no Codex call at all).
    billing: str
    category: str
    #: The EXPECTED visible output (estimates only; thinking is estimated apart).
    output_tokens: int
    input_price_per_million: float
    output_price_per_million: float
    price_source: str
    prompt_version: str
    #: A metered role's price source and check date (empty: unverified, refused).
    price_verified: PriceVerification = UNVERIFIED
    #: The hard ``max_tokens`` sent with every request (thinking included):
    #: the reservation's output side. None: the profile's output-budget policy.
    max_output_tokens: int | None = None
    #: A long-prompt tier: past ``long_context_threshold`` input tokens the
    #: request is billed at the long prices; a request whose input UPPER BOUND
    #: passes it is admitted at them.
    long_context_threshold: int | None = None
    long_input_price_per_million: float | None = None
    long_output_price_per_million: float | None = None

    def prices_for(self, input_tokens: float) -> tuple[float, float]:
        """``(input, output)`` dollars per million tokens for a request of
        ``input_tokens`` (the long tier past its threshold)."""

        if (self.long_context_threshold is not None and input_tokens > self.long_context_threshold
                and self.long_input_price_per_million is not None and self.long_output_price_per_million is not None):
            return self.long_input_price_per_million, self.long_output_price_per_million
        return self.input_price_per_million, self.output_price_per_million

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# -- the Anthropic Messages API (re-plan 2026-10-22, orchestrator ruling) -------------------
#: E0's LLM roles post directly to the Messages API (one HTTPS POST per admitted
#: request, no ``tools`` key): tool-free by construction, never ``claude -p``.
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
#: The API version header (2026-10-21: sampling parameters are rejected, none is sent).
ANTHROPIC_VERSION = "2026-10-21"
ANTHROPIC_KEY_ENV = "ANTHROPIC_API_KEY"
#: A non-streaming request with a large ``max_tokens`` can take minutes.
ANTHROPIC_TIMEOUT_S = 600.0
#: The exact API model ids, pinned. They come from the Claude API reference's
#: model table (cached 2026-10-06), not from a live call: the paid run's canary
#: (one tiny request per model, before any bulk work) checks each id is served
#: and answered as itself, or the run stops.
ANTHROPIC_MODELS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}
#: Every Anthropic role pin's endpoint (``callers.check_pin``).
ANTHROPIC_PROFILES = {
    f"e0_anthropic_{family}": {"model": model, "base_url": "https://api.anthropic.com/v1"}
    for family, model in ANTHROPIC_MODELS.items()
}
#: The orchestrator verified these on 2026-10-22 from Anthropic's pricing page.
ANTHROPIC_PRICE = PriceVerification("https://platform.claude.com/docs/en/about-claude/pricing", "2026-10-22")
_HAIKU = dict(input_price=0.10, output_price=0.50, long=(100_000, 0.50, 2.50),
              source="Anthropic: $0.10 input / $0.50 output per 1M tokens up to 100k prompt tokens, $0.50 / $2.50 "
                     "above (orchestrator-verified 2026-10-22)")
_SONNET = dict(input_price=2.00, output_price=10.00, long=None,
               source="Anthropic: $2 input / $10 output per 1M tokens (orchestrator-verified 2026-10-22)")
_OPUS = dict(input_price=4.00, output_price=20.00, long=None,
             source="Anthropic: $4 input / $20 output per 1M tokens (orchestrator-verified 2026-10-22)")
_FAMILY_PRICES = {"haiku": _HAIKU, "sonnet": _SONNET, "opus": _OPUS}


def _anthropic(role: str, family: str, category: str, expected_output: int, max_output: int,
               prompt_version: str) -> RolePin:
    price = _FAMILY_PRICES[family]
    long = price["long"]
    return RolePin(role, f"e0_anthropic_{family}", "anthropic_api", ANTHROPIC_MODELS[family], None, "metered",
                   category, expected_output, price["input_price"], price["output_price"], price["source"],
                   prompt_version, price_verified=ANTHROPIC_PRICE, max_output_tokens=max_output,
                   long_context_threshold=long[0] if long else None,
                   long_input_price_per_million=long[1] if long else None,
                   long_output_price_per_million=long[2] if long else None)


ROLE_PINS: dict[str, RolePin] = {
    # Strong writer (spec §5.1: Sonnet 5.5 or GPT-6 Luna): Claude Sonnet 5.5.
    "writer": _anthropic("writer", "sonnet", "drafting_context", 4_000, 16_384, "e0-writer-v1"),
    # R3's 50-100-token chunk context, generated once without benchmark queries.
    "context": _anthropic("context", "haiku", "drafting_context", 4_000, 16_384, "e0-context-v1"),
    # Two independent label passes, two DIFFERENT models, blinded and reordered.
    "label_a": _anthropic("label_a", "haiku", "labels_audits", 2_000, 8_192, "e0-label-v1"),
    "label_b": _anthropic("label_b", "sonnet", "labels_audits", 2_000, 8_192, "e0-label-v1"),
    # The strong adjudicator: a model different from both labellers.
    "adjudicator": _anthropic("adjudicator", "opus", "labels_audits", 2_000, 16_384, "e0-adjudicate-v1"),
    # The same tutor for every delivery and retrieval arm.
    "tutor": _anthropic("tutor", "haiku", "answers_verification", 2_000, 8_192, "e0-tutor-v1"),
    "judge_a": _anthropic("judge_a", "haiku", "answers_verification", 1_000, 8_192, "e0-judge-v1"),
    "judge_b": _anthropic("judge_b", "haiku", "answers_verification", 1_000, 8_192, "e0-judge-v1"),
    # The answer adjudicator: different from the judges.
    "judge_adjudicator": _anthropic("judge_adjudicator", "opus", "answers_verification", 1_000, 16_384,
                                    "e0-judge-adjudicate-v1"),
    # The service copies' production source routes (source_rerank,
    # source_query_rewrite, source_compare) go to OpenRouter's Claude Haiku 5.5
    # (re-plan 2026-10-22). Its slug and price are PENDING orchestrator
    # verification: until filled, admission refuses every such request.
    "system_verifier": RolePin("system_verifier", "e0_openrouter_haiku", "openrouter", "anthropic/claude-haiku-5.5",
                               None, "metered", "answers_verification", 600, 0.10, 0.50,
                               "OpenRouter anthropic/claude-haiku-5.5: assumed equal to Anthropic's own price; "
                               "PENDING orchestrator verification (slug and price not checked offline)",
                               "production-source-routes",
                               price_verified=PriceVerification(note="pending orchestrator verification"),
                               long_context_threshold=100_000, long_input_price_per_million=0.50,
                               long_output_price_per_million=2.50),
}

#: The OpenRouter profile the service copies' production source routes use
#: (written into each service copy's toml only; no vault file or default changes).
EXPERIMENT_PROFILES = {
    "e0_openrouter_haiku": {
        "type": "openrouter", "model": "anthropic/claude-haiku-5.5",
        "base_url": "https://openrouter.ai/api/v1", "api_key_env": "OPENROUTER_API_KEY",
    },
}
#: The production routes the system arms call (re-routed on the service copies).
SYSTEM_ARM_ROUTES = ("source_rerank", "source_query_rewrite", "source_compare")

#: Key environment names (spec D13; configurable with CLI flags).
DEFAULT_KEY_ENVS = {"perplexity": "PERPLEXITY_API_KEY", "voyage": "VOYAGE_API_KEY",
                    "openrouter": "OPENROUTER_API_KEY", "anthropic": ANTHROPIC_KEY_ENV}


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
            "latency_tolerance": LATENCY_REGRESSION_TOLERANCE, "max_wall_s": MAX_WALL_S,
            "max_paid_requests": MAX_PAID_REQUESTS, "max_subscription_requests": MAX_SUBSCRIPTION_REQUESTS,
            "paid_run_subscription_allowance": PAID_RUN_SUBSCRIPTION_ALLOWANCE,
        },
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def price_problem(pin: EmbeddingPin | RolePin) -> str | None:
    """Why a METERED pin's price cannot admit a request (None: it can).

    A subscription role has no marginal bill and needs no price. A metered
    pin needs its ``price_verified`` record (the published price page's URL
    and the date it was checked) before any request is admitted: an
    unverified upper bound cannot hold a hard cap (fix round 4, High 2)."""

    if isinstance(pin, RolePin) and pin.billing == "subscription":
        return None
    if not pin.price_verified.verified:
        name = pin.name if isinstance(pin, EmbeddingPin) else pin.role
        return (f"the price of {name} ({pin.model}) is not verified: its pin needs price_verified "
                "{source_url, checked_on} from the provider's published price page")
    return None


def unverified_prices() -> dict[str, list[str]]:
    """Every metered pin whose price is unverified (the dry run reports them)."""

    return {"embeddings": sorted(name for name, pin in EMBEDDING_PINS.items() if price_problem(pin)),
            "roles": sorted(name for name, pin in ROLE_PINS.items() if price_problem(pin))}


def verified_role_for_model(model: str | None) -> RolePin | None:
    """A metered role pin with a verified price for ``model`` (a production
    route on a service copy is priced only through one)."""

    for pin in ROLE_PINS.values():
        if pin.billing == "metered" and pin.model == model and price_problem(pin) is None:
            return pin
    return None
