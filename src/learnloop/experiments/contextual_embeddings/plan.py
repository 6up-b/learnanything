"""E0's frozen run plan and its cost estimate (spec §6).

Built from the copies' actual inventory, with no network and no write:

* every arm's documents, chunks, requests and conservative tokens, computed
  by the same batching the adapters use, priced at the pins' upper bounds,
  expected and worst case (every request retried twice);
* every paid LLM role's calls and tokens: the writer's and R3's prompts are
  built exactly (the seeds are deterministic); the label, adjudication,
  answer and judge sizes come from the real unit, section and source sizes
  under the stated assumptions;
* the category totals against §6's allocation, the total against the $25 cap,
  and which keys are present (names only).

Assumptions are recorded in the plan itself. A plan that does not fit is
reported as such with the categories that overflow; it is never executed by
silently cutting cases (spec §6: fewer cases need a revised plan).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from typing import Any

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.adapters import Chunk, Document
from learnloop.experiments.contextual_embeddings.bank import BankQuestion, Seed, writer_prompt
from learnloop.experiments.contextual_embeddings.callers import SCHEMA_ALLOWANCE_TOKENS, role_cost
from learnloop.experiments.contextual_embeddings.corpus import CorpusSnapshot
from learnloop.experiments.contextual_embeddings.pins import token_estimate
from learnloop.experiments.contextual_embeddings.retrieval import context_prompt, recipe_text

#: Stated assumptions of the estimate (each one is in the plan).
ASSUMPTIONS = {
    "r3_header_tokens_per_unit": 200,
    "development_query_tokens": 60,
    "pool_overlap_factor": 0.5,
    "label_batch": 40,
    "label_tokens_per_candidate_overhead": 30,
    "label_output_tokens_per_candidate": 12,
    "adjudicated_share_of_labelled_questions": 1.0,
    "adjudicator_output_tokens_per_candidate": 12,
    "answer_output_tokens": 600,
    "judge_output_tokens": 300,
    "judge_disagreement_share": 0.35,
    "retrieval_finalists": 3,
    "writer_batch": 6,
    "writer_output_tokens_per_question": 160,
    "qwen_query_prefix_tokens": 30,
    #: A pool over one label batch gets a joint sufficiency review per pass
    #: (Codex review F13) over this share of it (the required/helpful ones).
    "joint_review_support_share": 0.25,
    #: One fresh online query per question and finalist (Codex review F9).
    "online_latency_queries_per_question": 3,
}

EMBEDDING_ARMS = ("R1", "R2", "R3", "R4_grouped", "R4_singleton", "R4_independent", "R5_grouped",
                  "R5_singleton", "R5_independent")


def _sha(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


def _chunk_tokens(text: str) -> int:
    return token_estimate(text) + pins.CHUNK_MARKER_TOKENS


def _batches(documents: Sequence[Sequence[int]], pin: pins.EmbeddingPin) -> int:
    """Requests the adapter batching makes for documents of these chunk token sizes."""

    requests = 0
    tokens = chunks = count = 0
    for sizes in documents:
        size = sum(sizes)
        if count and (tokens + size > pin.max_tokens_per_request or chunks + len(sizes) > pin.max_chunks_per_request
                      or count + 1 > pin.max_documents_per_request):
            requests += 1
            tokens = chunks = count = 0
        tokens += size
        chunks += len(sizes)
        count += 1
    return requests + (1 if count else 0)


def embedding_arm_estimate(arm: str, snapshots: Sequence[CorpusSnapshot], query_tokens: Sequence[int]) -> dict[str, Any]:
    spec = pins.RETRIEVAL_ARMS[arm]
    pin = pins.EMBEDDING_PINS[spec.embedding]
    documents: list[list[int]] = []
    oversize = 0
    for snapshot in snapshots:
        if spec.encoding == "grouped":
            for window in snapshot.windows:
                documents.append([_chunk_tokens(recipe_text(snapshot, snapshot.unit(unit_id), "plain"))
                                  for unit_id in window.unit_ids])
        else:
            for unit in snapshot.units:
                if spec.recipe == "llm_context":
                    tokens = _chunk_tokens(unit.text) + ASSUMPTIONS["r3_header_tokens_per_unit"]
                else:
                    tokens = _chunk_tokens(recipe_text(snapshot, unit, spec.recipe))
                documents.append([tokens])
    for sizes in documents:
        if sum(sizes) > pin.max_tokens_per_document:
            oversize += 1
    document_tokens = sum(map(sum, documents))
    prefix = ASSUMPTIONS["qwen_query_prefix_tokens"] if pin.provider == "openrouter" else 0
    q_tokens = sum(tokens + prefix + pins.CHUNK_MARKER_TOKENS for tokens in query_tokens)
    query_requests = math.ceil(len(query_tokens) / max(1, min(pin.max_documents_per_request, 128))) if query_tokens else 0
    canary = 0 if pin.provider == "openrouter" else 1
    canary_tokens = 80 * canary
    # Upper estimate: any arm may be a finalist, measured online with one fresh
    # query request per question (Codex review F9).
    online_requests = len(query_tokens)
    requests = _batches(documents, pin) + query_requests + canary + online_requests
    tokens = document_tokens + 2 * q_tokens + canary_tokens
    usd = tokens * pin.price_per_million_upper_bound / 1_000_000
    blocked = []
    if not pin.contract_verified:
        blocked.append("contract_unverified: the canary must pass before paid calls")
    if not pin.price_verified:
        blocked.append("price_unverified: admission reserves at the conservative upper bound")
    if oversize:
        blocked.append(f"{oversize} documents over the per-document limit")
    return {
        "arm": arm, "kind": spec.kind, "model": pin.model, "provider": pin.provider, "encoding": spec.encoding,
        "recipe": spec.recipe, "documents": len(documents), "chunks": sum(len(sizes) for sizes in documents),
        "document_tokens": document_tokens, "query_tokens": q_tokens, "queries": len(query_tokens),
        "requests": requests, "tokens": tokens, "price_per_million_upper_bound": pin.price_per_million_upper_bound,
        "estimated_usd": round(usd, 6), "worst_case_usd": round(usd * (1 + pins.TRANSIENT_RETRIES), 6),
        "category": "embeddings", "notes": blocked,
    }


def _role(role: str, calls: int, input_tokens: int, output_tokens: int, *, arm: str | None = None,
          detail: str = "") -> dict[str, Any]:
    pin = pins.ROLE_PINS[role]
    usd = role_cost(pin, input_tokens, output_tokens)
    list_price = (input_tokens * 2.0 + output_tokens * 10.0) / 1_000_000 if pin.billing == "subscription" else None
    return {"role": role, "model": pin.model, "transport": pin.transport, "billing": pin.billing,
            "category": pin.category, "arm": arm, "calls": calls, "input_tokens": input_tokens,
            "output_tokens": output_tokens, "estimated_usd": round(usd, 6),
            "worst_case_usd": round(usd * (1 + pins.TRANSIENT_RETRIES), 6),
            "estimated_only_reference_usd": None if list_price is None else round(list_price, 6),
            "detail": detail}


def llm_estimates(snapshots: Sequence[CorpusSnapshot], seeds: Mapping[str, Sequence[Seed]],
                  questions: Mapping[str, Mapping[str, int]]) -> list[dict[str, Any]]:
    """The paid LLM roles. ``questions``: per vault, scored question counts
    (``development`` target, ``logged``, ``known_location``)."""

    rows: list[dict[str, Any]] = []
    writer_calls = writer_in = writer_out = 0
    context_calls = context_in = context_out = 0
    label_calls = label_in = label_out = 0
    adj_calls = adj_in = adj_out = 0
    answer_calls = answer_in = 0
    judge_calls = judge_in = 0
    judge_adj_calls = judge_adj_in = 0
    arms = len(EMBEDDING_ARMS) + 3  # + R0, R1_service, R3_bm25
    for snapshot in snapshots:
        vault_seeds = list(seeds.get(snapshot.vault_label, []))
        batch = ASSUMPTIONS["writer_batch"]
        for start in range(0, len(vault_seeds), batch):
            prompt, _refs, _units = writer_prompt(snapshot, vault_seeds[start:start + batch])
            writer_calls += 1
            writer_in += token_estimate(prompt) + SCHEMA_ALLOWANCE_TOKENS
            writer_out += ASSUMPTIONS["writer_output_tokens_per_question"] * len(vault_seeds[start:start + batch])
        for window in snapshot.windows:
            prompt, refs = context_prompt(snapshot, window)
            context_calls += 1
            context_in += token_estimate(prompt) + SCHEMA_ALLOWANCE_TOKENS
            context_out += ASSUMPTIONS["r3_header_tokens_per_unit"] * len(refs)
        counts = questions.get(snapshot.vault_label, {})
        scored = int(counts.get("development", 0)) + int(counts.get("logged", 0))
        units = len(snapshot.units)
        average_unit = (sum(unit.tokens for unit in snapshot.units) / units) if units else 0.0
        pool = min(units, math.ceil((arms * pins.POOL_DEPTH) * ASSUMPTIONS["pool_overlap_factor"]) + 7)
        per_candidate = average_unit + ASSUMPTIONS["label_tokens_per_candidate_overhead"]
        passes = 2
        calls_per_pass = math.ceil(pool / ASSUMPTIONS["label_batch"]) if pool else 0
        label_calls += scored * passes * calls_per_pass
        label_in += int(scored * passes * (pool * per_candidate + calls_per_pass * (400 + SCHEMA_ALLOWANCE_TOKENS)))
        label_out += int(scored * passes * pool * ASSUMPTIONS["label_output_tokens_per_candidate"])
        if calls_per_pass > 1:
            support = math.ceil(pool * ASSUMPTIONS["joint_review_support_share"])
            label_calls += scored * passes
            label_in += int(scored * passes * (support * per_candidate + 400 + SCHEMA_ALLOWANCE_TOKENS))
            label_out += int(scored * passes * 200)
        audited = math.ceil(scored * ASSUMPTIONS["adjudicated_share_of_labelled_questions"])
        adj_calls += audited
        adj_in += int(audited * (pool * (per_candidate + 10) + 600 + SCHEMA_ALLOWANCE_TOKENS))
        adj_out += int(audited * pool * ASSUMPTIONS["adjudicator_output_tokens_per_candidate"])
        known = int(counts.get("known_location", 0))
        section_tokens = _average_section_tokens(snapshot)
        source_tokens = _average_source_tokens(snapshot)
        d_inputs = [min(pins.D1_EVIDENCE_TOKENS, 2_400), pins.D1_EVIDENCE_TOKENS, section_tokens,
                    min(source_tokens, pins.GENERATOR_CONTEXT_TOKENS)]
        reserves = sum(pins.GENERATOR_RESERVES.values())
        answer_calls += known * 4 + scored * ASSUMPTIONS["retrieval_finalists"]
        answer_in += int(known * sum(value + reserves for value in d_inputs)
                         + scored * ASSUMPTIONS["retrieval_finalists"] * (pins.D1_EVIDENCE_TOKENS + reserves))
        answers = known * 4 + scored * ASSUMPTIONS["retrieval_finalists"]
        evidence = (known * sum(d_inputs) + scored * ASSUMPTIONS["retrieval_finalists"] * pins.D1_EVIDENCE_TOKENS)
        per_answer = (evidence / answers if answers else 0) + ASSUMPTIONS["answer_output_tokens"] + 800
        judge_calls += answers * 2
        judge_in += int(answers * 2 * per_answer)
        disagreements = math.ceil(answers * ASSUMPTIONS["judge_disagreement_share"])
        judge_adj_calls += disagreements
        judge_adj_in += int(disagreements * (per_answer + 600))
    rows.append(_role("writer", writer_calls, writer_in, writer_out, detail="exact prompts from the frozen seeds"))
    rows.append(_role("context", context_calls, context_in, context_out, arm="R3",
                      detail="exact prompts, one per window"))
    rows.append(_role("label_a", math.ceil(label_calls / 2), label_in // 2, label_out // 2))
    rows.append(_role("label_b", math.ceil(label_calls / 2), label_in // 2, label_out // 2))
    rows.append(_role("adjudicator", adj_calls, adj_in, adj_out,
                      detail="every question with a disagreement or an accepted set (assumed all)"))
    rows.append(_role("tutor", answer_calls, answer_in, answer_calls * ASSUMPTIONS["answer_output_tokens"],
                      detail="D0-D3 on known-location questions; D1 for the retrieval finalists"))
    rows.append(_role("judge_a", judge_calls // 2, judge_in // 2, (judge_calls // 2) * ASSUMPTIONS["judge_output_tokens"]))
    rows.append(_role("judge_b", judge_calls // 2, judge_in // 2, (judge_calls // 2) * ASSUMPTIONS["judge_output_tokens"]))
    rows.append(_role("judge_adjudicator", judge_adj_calls, judge_adj_in,
                      judge_adj_calls * ASSUMPTIONS["judge_output_tokens"]))
    return rows


def _average_section_tokens(snapshot: CorpusSnapshot) -> int:
    sizes = []
    for extraction_id, outline in snapshot.outline_units.items():
        for unit in outline:
            wanted = set(unit.span_ids)
            sizes.append(sum(math.ceil(len(block.text) / 4) for block in snapshot.blocks.get(extraction_id, [])
                             if block.span_id in wanted and snapshot.policy.permitted(extraction_id, block.span_id)))
    return int(sum(sizes) / len(sizes)) if sizes else pins.D1_EVIDENCE_TOKENS


def _average_source_tokens(snapshot: CorpusSnapshot) -> int:
    sizes = [sum(math.ceil(len(block.text) / 4) for block in blocks
                 if snapshot.policy.permitted(extraction_id, block.span_id))
             for extraction_id, blocks in snapshot.blocks.items()]
    return int(sum(sizes) / len(sizes)) if sizes else 0


def system_arm_estimates(snapshots: Sequence[CorpusSnapshot], config_allowlists: Mapping[str, Mapping[str, Any]],
                         query_counts: Mapping[str, int]) -> list[dict[str, Any]]:
    """R0 (today's effective path) and R1_service (find_sources on a copy
    with Qwen enabled and backfilled): what they would spend."""

    rows = []
    qwen = pins.EMBEDDING_PINS["qwen3_8b"]
    for snapshot in snapshots:
        allowlist = config_allowlists.get(snapshot.vault_label, {})
        queries = int(query_counts.get(snapshot.vault_label, 0))
        dense_on = bool(allowlist.get("embedding.enabled")) and bool(allowlist.get("source_retrieval.dense"))
        rewrite_on = bool(allowlist.get("source_retrieval.query_rewrite"))
        rows.append({"arm": "R0", "vault": snapshot.vault_label, "kind": "system", "dense_effective": dense_on,
                     "rewrite": rewrite_on, "queries": queries,
                     "paid_steps": (["query_embedding"] if dense_on else []) + (["rewrite"] if rewrite_on else []),
                     "estimated_usd": 0.0 if not dense_on else round(queries * 60 * qwen.price_per_million_upper_bound
                                                                     / 1_000_000, 6),
                     "rewrite_route": allowlist.get("routes", {}).get("source_query_rewrite"),
                     "category": "embeddings",
                     "notes": ["rewrite calls follow the copy's route; a metered rewrite route without "
                               "source_retrieval.llm_price_per_million is refused before sending"] if rewrite_on else []})
        # The service copy is redacted first: only permitted blocks are embedded (Codex review F1).
        block_tokens = sum(_chunk_tokens(" ".join(block.text.split()))
                           for extraction_id, blocks in snapshot.blocks.items()
                           for block in blocks if block.text.strip()
                           and snapshot.policy.permitted(extraction_id, block.span_id))
        backfill_usd = block_tokens * qwen.price_per_million_upper_bound / 1_000_000
        query_usd = queries * 2 * 90 * qwen.price_per_million_upper_bound / 1_000_000
        rows.append({"arm": "R1_service", "vault": snapshot.vault_label, "kind": "system", "queries": queries,
                     "variants": ["find_sources (RRF, intent lists, mandatory verification, compare delegation)",
                                  "first-page dense_plus_bm25", "pool_verify (tutor_pool + verify_spans)"],
                     "backfill_tokens": block_tokens, "estimated_usd": round(backfill_usd + query_usd, 6),
                     "verification_route": allowlist.get("routes", {}).get("source_rerank"),
                     "category": "embeddings",
                     "notes": ["runs on a separate, redacted service copy with embeddings enabled (its toml only)",
                               "verification runs on the copy's source_rerank route: subscription at $0, a "
                               "metered route needs source_retrieval.llm_price_per_million or is refused"]})
    return rows


def summarize(arms: Sequence[Mapping[str, Any]], systems: Sequence[Mapping[str, Any]],
              roles: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    categories = {name: {"estimated_usd": 0.0, "worst_case_usd": 0.0, "allocation_usd": value}
                  for name, value in pins.ALLOCATION_USD.items()}
    for row in [*arms, *systems, *roles]:
        category = categories[row["category"]]
        category["estimated_usd"] += float(row.get("estimated_usd") or 0.0)
        category["worst_case_usd"] += float(row.get("worst_case_usd") or row.get("estimated_usd") or 0.0)
    for category in categories.values():
        category["estimated_usd"] = round(category["estimated_usd"], 4)
        category["worst_case_usd"] = round(category["worst_case_usd"], 4)
        category["fits"] = category["estimated_usd"] <= category["allocation_usd"]
    total = round(sum(category["estimated_usd"] for category in categories.values()), 4)
    worst = round(sum(category["worst_case_usd"] for category in categories.values()), 4)
    overflow = sorted(name for name, category in categories.items() if not category["fits"])
    subscription_tokens = sum(int(row["input_tokens"]) + int(row["output_tokens"]) for row in roles
                              if row["billing"] == "subscription")
    return {"categories": categories, "estimated_usd": total, "worst_case_usd": worst, "cap_usd": pins.E0_CAP_USD,
            "fits_cap": total <= pins.E0_CAP_USD, "fits_allocations": not overflow, "overflowing_categories": overflow,
            "subscription_estimated_only_tokens": subscription_tokens,
            "basis": "conservative upper-bound prices; admission reserves the same bounds before each request"}


def run_id(snapshots: Sequence[CorpusSnapshot], bank_ids: Sequence[str]) -> str:
    return "e0_" + _sha(pins.pins_fingerprint(), [snapshot.policy.fingerprint for snapshot in snapshots],
                        [[unit.unit_id for unit in snapshot.units] for snapshot in snapshots], sorted(bank_ids),
                        pins.SEED)[:16]


def query_token_sizes(bank: Sequence[BankQuestion], development_target: int) -> list[int]:
    sizes = [token_estimate(question.effective_query) for question in bank]
    sizes.extend([ASSUMPTIONS["development_query_tokens"]] * development_target)
    return sizes


def embedding_documents(snapshot: CorpusSnapshot, arm: str) -> list[Document]:
    """The plain documents of an arm (for tests and the paid run's first step)."""

    spec = pins.RETRIEVAL_ARMS[arm]
    if spec.encoding == "grouped":
        return [Document(window.window_id, tuple(Chunk(unit_id, snapshot.unit(unit_id).text)
                                                 for unit_id in window.unit_ids)) for window in snapshot.windows]
    return [Document(unit.unit_id, (Chunk(unit.unit_id, recipe_text(snapshot, unit, spec.recipe or "plain")),))
            for unit in snapshot.units]
