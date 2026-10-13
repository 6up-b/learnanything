"""The T6 report: source retrieval vs today's substring search (suite ``source_retrieval``).

Runs on the shared ``learnloop embeddings compare`` harness (Slice 2 §4,
§13: "retrieval recall on LLM-labelled question → span pairs, two passes, with
agreement reported").

* **Corpus.** The library scope: every reader-enabled source's current blocks.
* **Questions** (T6 follow-up, owner 2026-10-12: the first two runs asked only
  single-concept generated questions). LLM-written questions of four types,
  each from its own sampled seeds: ``conceptual`` (one passage, a why/how
  question about its idea; the first run's prompt and seed order, so its seeds
  are the first run's), ``keyword`` (an exact-term search a learner would type),
  ``compositional`` (two passages of one source, a question that needs both)
  and ``procedural`` (how to compute, derive, apply or check something). Plus
  every logged learner question in the vault (a reader question's anchored span
  is its seed). A seed is a known relevant span: its hit rate is a label-free
  check.
* **Systems.** ``substring`` is today's library search (``instr`` of the whole
  query, document order); ``keyword`` FTS5 BM25; ``meaning`` the dense index;
  ``hybrid`` / ``hybrid_rewrite`` the ``hybrid_rrf`` deep search without / with
  the production rewrite; ``pool_rewrite`` the ``dense_plus_bm25`` deep search
  with the rewrite, as the library shows it (its top 10 is dense first, so
  without a rewrite it equals ``meaning``). Three systems run the PRODUCTION
  tutor-span verification (route ``source_rerank``, ``verify_spans``, at most
  ``tutor_spans`` picks) on the tutor's own pools, built by the tutor's own
  ``tutor_pool`` for the question's context (review F5: the teaching scope,
  the LOs' linked spans, answer overlap withheld, and in a practice or feedback
  context the item's exclusions and its practice question shown to the
  verifier): ``hybrid_verify`` (``hybrid_rrf``, as T6 merged), ``pool_verify``
  (``dense_plus_bm25``: the dense top ``tutor_candidate_pool`` plus the BM25 and
  linked-span tops dense missed) and ``dense_verify`` (the dense top
  ``tutor_candidate_pool`` alone). A verification system's ranking is its picks
  then the rest of its pool, and its picks are scored as the spans the tutor
  would get: relevant share, nDCG@picks, latency. A verification that did not
  run is no ranking (the tutor would fall back to the LO-linked spans): the
  question leaves that system's scores, its coverage is reported, and its
  verdicts are blocked (review F4). Dense systems need a complete
  ``source_block/text`` backfill for ``embedding.model``; without it ``meaning``
  and ``dense_verify`` are unavailable and the pool systems report the
  production fallback (``hybrid_rrf``).
* **Labels and metrics** as in ``bench``: two LLM passes over the union of
  every system's top 10 and every verification pool, agreement, nDCG@10,
  Recall@10, MRR, paired bootstrap intervals, all also per query type.

Reports are aggregate only; every verdict is in ``judgment_ledger``.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
import math
import statistics
import time
from typing import Any

import numpy as np

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.execution import content_key
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import (
    blocks_by_key,
    extraction_blocks,
    search_blocks,
    section_header_titles,
)
from learnloop.ops.pf_calls import estimate_tokens
from learnloop.practice_index.evaluation import paired_bootstrap
from learnloop.reader.source_search import MAX_HITS
from learnloop.source_retrieval import bench
from learnloop.source_retrieval.contracts import VERDICT_SCORE, QueryRewrite, SpanVerification
from learnloop.source_retrieval.corpus import Scope, library_scope
from learnloop.source_retrieval.dense import load_dense_index
from learnloop.source_retrieval.queries import (
    REWRITE_PROMPT_VERSION,
    Rewrite,
    is_conceptual,
    rewrite_prompt,
    rewritten_text,
)
from learnloop.source_retrieval.recipes import (
    block_record_id,
    embeddable,
    source_block_text,
    split_record_id,
)
from learnloop.source_retrieval.search import (
    POOL_DENSE_PLUS_BM25,
    POOL_HYBRID_RRF,
    SpanHit,
    search_spans,
)
from learnloop.source_retrieval.tutor import ITEM_BOUND_CONTEXTS, TutorPool, tutor_pool
from learnloop.source_retrieval.verify import PASSAGE_CHARS, verify_prompt, verify_spans
from learnloop.vault.models import LoadedVault

DISPLAY_SYSTEMS = ("substring", "keyword", "meaning", "hybrid", "hybrid_rewrite", "pool_rewrite")
VERIFY_SYSTEMS = ("hybrid_verify", "pool_verify", "dense_verify")
SYSTEMS = DISPLAY_SYSTEMS + VERIFY_SYSTEMS
DENSE_SYSTEMS = frozenset({"meaning", "hybrid", "hybrid_rewrite", "pool_rewrite", *VERIFY_SYSTEMS})
#: Systems that do not exist without a complete dense index.
DENSE_ONLY_SYSTEMS = frozenset({"meaning", "dense_verify"})
REWRITE_SYSTEMS = frozenset({"hybrid_rewrite", "pool_rewrite"})
QUERY_TYPES = ("conceptual", "keyword", "compositional", "procedural")
LOGGED_TYPE = "logged"
DEFAULT_QUESTIONS = 40
QUESTION_PROMPT_VERSION = "source_eval_question.v1"
TYPE_PROMPT_VERSIONS = {
    "conceptual": QUESTION_PROMPT_VERSION,
    "keyword": "source_eval_question.keyword.v1",
    "compositional": "source_eval_question.compositional.v1",
    "procedural": "source_eval_question.procedural.v1",
}
LABEL_PROMPT_VERSIONS = ("source_relevance_label.v1.pass1", "source_relevance_label.v1.pass2")
QUESTION_BATCH = 8
LABEL_BATCH = 20
SEED_MIN_CHARS = 60
SEED_CHARS = 1200
#: A compositional pair's two blocks are at least this many blocks apart.
PAIR_MIN_DISTANCE = 3
LABEL_PASSAGE_CHARS = 900
EMBED_BATCH = 32
COMPARISONS = (("keyword", "substring"), ("meaning", "substring"), ("hybrid", "substring"),
               ("hybrid_rewrite", "substring"), ("hybrid", "keyword"), ("hybrid", "meaning"),
               ("hybrid_rewrite", "hybrid"), ("hybrid_rewrite", "meaning"),
               ("pool_rewrite", "hybrid_rewrite"), ("pool_rewrite", "meaning"),
               ("hybrid_verify", "hybrid"), ("pool_verify", "hybrid_verify"),
               ("pool_verify", "dense_verify"), ("dense_verify", "hybrid_verify"))
#: The comparisons reported within each query type.
TYPE_COMPARISONS = (("hybrid", "meaning"), ("hybrid_rewrite", "hybrid"), ("pool_rewrite", "hybrid_rewrite"),
                    ("pool_verify", "hybrid_verify"), ("pool_verify", "dense_verify"))
#: Verification comparisons on the picked spans themselves.
VERIFY_COMPARISONS = (("pool_verify", "hybrid_verify"), ("pool_verify", "dense_verify"),
                      ("dense_verify", "hybrid_verify"))
VERIFY_METRICS = ("pick_precision", "ndcg@picks")
#: The production tutor pool each verification system judges: (pool mode,
#: extras per widening list; None is ``source_retrieval.pool_keyword_extras``).
VERIFY_POOLS = {"hybrid_verify": (POOL_HYBRID_RRF, None), "pool_verify": (POOL_DENSE_PLUS_BM25, None),
                "dense_verify": (POOL_DENSE_PLUS_BM25, 0)}
#: The context a benchmark question is asked in when the learner gave none:
#: a library question about the passages it came from (review F5).
GENERATED_CONTEXT = "library"


@dataclass
class Seed:
    key: tuple[str, str]
    text: str
    qtype: str = "conceptual"
    partner: tuple[str, str] | None = None
    partner_text: str | None = None

    @property
    def seed_id(self) -> str:
        own = block_record_id(*self.key)
        return own if self.partner is None else f"{own}+{block_record_id(*self.partner)}"

    @property
    def keys(self) -> list[tuple[str, str]]:
        return [self.key] + ([self.partner] if self.partner is not None else [])

    @property
    def writer_text(self) -> str | tuple[str, str]:
        return self.text if self.partner_text is None else (self.text, self.partner_text)


@dataclass
class LoggedQuestion:
    text: str
    seed: tuple[str, str] | None
    context: str
    item_id: str | None = None
    note_id: str | None = None


@dataclass(frozen=True)
class TutorQuestion:
    """How the tutor would be asked one benchmark question (review F5).

    A logged practice or feedback question keeps its item (its LO, the item's
    exclusions, answer withholding and the practice question shown to the
    verifier); a logged library question its note's related LOs. A generated
    question, and a reader question (which the tutor's retrieval never serves:
    the reader answers from its anchored span), is asked as a library question
    about the learning objects the reader links to its passages.
    """

    context: str
    learning_object_ids: tuple[str, ...] = ()
    item_id: str | None = None

    def describe(self) -> dict[str, Any]:
        return {"context": self.context, "learning_objects": len(self.learning_object_ids),
                "item_bound": self.context in ITEM_BOUND_CONTEXTS and self.item_id is not None}


@dataclass
class EvalData:
    manifest: dict[str, Any]
    scope: Scope
    seeds: list[Seed]
    logged: list[LoggedQuestion]
    systems: tuple[str, ...]
    revision: str
    dense: dict[str, Any] = field(default_factory=dict)

    def seeds_of(self, qtype: str) -> list[Seed]:
        return [seed for seed in self.seeds if seed.qtype == qtype]


@dataclass
class _Block:
    key: tuple[str, str]
    text: str
    ordinal: int
    section: str | None


def _candidate_blocks(repository: Repository, scope: Scope) -> list[_Block]:
    found: list[_Block] = []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        for extraction_id in sorted(scope.extractions):
            for block in extraction_blocks(connection, extraction_id):
                text = " ".join(block.text.split())
                if embeddable(block) and len(text) >= SEED_MIN_CHARS and scope.allows(
                        block.extraction_id, block.span_id):
                    found.append(_Block((block.extraction_id, block.span_id), text[:SEED_CHARS],
                                        block.ordinal, block.section_path_json or None))
    return found


def type_counts(generated: int) -> dict[str, int]:
    """Generated questions per type: an even split, the remainder to the first types."""

    base, extra = divmod(max(0, generated), len(QUERY_TYPES))
    return {qtype: base + int(index < extra) for index, qtype in enumerate(QUERY_TYPES)}


def _seeds(repository: Repository, scope: Scope, counts: Mapping[str, int]) -> list[Seed]:
    """Disjoint seeds per type. Conceptual seeds keep the first run's order
    (salt ``t6-seed-v1``), so they are a prefix of the seeds every earlier run
    used; the other types draw from what is left in their own salted order."""

    candidates = _candidate_blocks(repository, scope)
    used: set[tuple[str, str]] = set()
    seeds: list[Seed] = []

    def ordered(salt: str) -> list[_Block]:
        return sorted(candidates, key=lambda block: bench.stable_key(salt, *block.key))

    for qtype in ("conceptual", "keyword", "procedural"):
        salt = "t6-seed-v1" if qtype == "conceptual" else f"t6-seed-{qtype}-v1"
        taken = 0
        for block in ordered(salt):
            if taken >= counts.get(qtype, 0):
                break
            if block.key in used:
                continue
            used.add(block.key)
            seeds.append(Seed(block.key, block.text, qtype))
            taken += 1
    by_extraction: dict[str, list[_Block]] = {}
    for block in candidates:
        by_extraction.setdefault(block.key[0], []).append(block)
    # A pair's first block is unused; its partner may be another type's seed
    # (a small library has few blocks), never another pair's.
    paired: set[tuple[str, str]] = set()
    taken = 0
    for block in ordered("t6-seed-compositional-v1"):
        if taken >= counts.get("compositional", 0):
            break
        if block.key in used or block.key in paired:
            continue
        partners = [other for other in by_extraction[block.key[0]]
                    if other.key not in paired and other.key != block.key
                    and abs(other.ordinal - block.ordinal) >= PAIR_MIN_DISTANCE
                    and (block.section is None or other.section != block.section)]
        if not partners:
            continue
        partner = min(partners, key=lambda other: bench.stable_key("t6-pair-v1", *block.key, *other.key))
        used.add(block.key)
        paired.update({block.key, partner.key})
        seeds.append(Seed(block.key, block.text, "compositional", partner.key, partner.text))
        taken += 1
    return seeds


def _logged(repository: Repository, scope: Scope, count: int | None = None) -> list[LoggedQuestion]:
    """Every distinct logged learner question (``count`` None: all of them)."""

    found: list[LoggedQuestion] = []
    for event in repository.question_events(answer_status="answered"):
        text = " ".join(str(event.get("question_md") or "").split())
        if len(text) < 8:
            continue
        context = event.get("source_context") if isinstance(event.get("source_context"), dict) else {}
        seed = None
        if event.get("context") == "reader" and context.get("extraction_id") and context.get("span_id"):
            key = (str(context["extraction_id"]), str(context["span_id"]))
            seed = key if scope.allows(*key) else None
        found.append(LoggedQuestion(text[:400], seed, str(event.get("context") or ""),
                                    item_id=str(event["practice_item_id"]) if event.get("practice_item_id") else None,
                                    note_id=str(event["note_id"]) if event.get("note_id") else None))
    found.sort(key=lambda entry: bench.stable_key("t6-logged-v1", entry.text))
    unique: dict[str, LoggedQuestion] = {}
    for entry in found:
        unique.setdefault(entry.text.lower(), entry)
    questions = list(unique.values())
    return questions if count is None else questions[: max(0, count)]


def _dcg(gains: Sequence[float]) -> float:
    return sum((2 ** gain - 1) / math.log2(index + 1) for index, gain in enumerate(gains, start=1))


def _gains(labels: Mapping[str, Sequence[str | None]]) -> tuple[dict[str, float], set[str]] | None:
    gains: dict[str, float] = {}
    relevant: set[str] = set()
    for key, passes in labels.items():
        if any(verdict is None for verdict in passes):
            return None
        gains[key] = sum(VERDICT_SCORE[str(v)] for v in passes) / len(passes)
        if all(v != "unrelated" for v in passes):
            relevant.add(key)
    return gains, relevant


def verification_metrics(pool: Sequence[str], picks: Sequence[str], pick_at_most: int,
                         labels: Mapping[str, Sequence[str | None]]) -> dict[str, Any] | None:
    """How good the picked spans are, against the labels of the whole pool."""

    if any(key not in labels for key in pool):
        return None
    found = _gains({key: labels[key] for key in pool})
    if found is None:
        return None
    gains, relevant = found
    top = list(pool)[:pick_at_most]
    ideal = _dcg(sorted((gains[key] for key in pool), reverse=True)[:pick_at_most])
    in_pool = len(set(pool) & relevant)
    return {
        "pool": len(pool), "relevant_in_pool": in_pool, "picks": len(picks),
        "relevant_picks": len(set(picks) & relevant),
        "pick_precision": (len(set(picks) & relevant) / len(picks)) if picks else None,
        "top_precision": (len(set(top) & relevant) / len(top)) if top else None,
        "ndcg@picks": (_dcg([gains[key] for key in picks]) / ideal) if ideal > 0 else None,
        "ndcg@top": (_dcg([gains[key] for key in top]) / ideal) if ideal > 0 else None,
        "empty_with_relevant": (not picks) and in_pool > 0,
    }


def _stats(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    ordered = sorted(values)
    return {"n": len(ordered), "mean": statistics.fmean(ordered), "p50": statistics.median(ordered),
            "p90": ordered[min(len(ordered) - 1, math.ceil(0.9 * len(ordered)) - 1)],
            "max": ordered[-1]}


def summarize_verification(per_question: Sequence[Mapping[str, Any]], systems: Sequence[str],
                           comparisons: Sequence[tuple[str, str]] = VERIFY_COMPARISONS) -> dict[str, Any]:
    """Per verification system: what the tutor would get, and paired differences."""

    out: dict[str, Any] = {"systems": {}, "differences": {}}
    for system in systems:
        metrics = [q["verification"][system]["metrics"] for q in per_question
                   if ((q.get("verification") or {}).get(system) or {}).get("metrics")]
        picks = sum(m["picks"] for m in metrics)

        def mean(name: str, metrics: list[dict[str, Any]] = metrics) -> float | None:
            values = [m[name] for m in metrics if m.get(name) is not None]
            return statistics.fmean(values) if values else None

        out["systems"][system] = {
            "questions": len(metrics), "picks_total": picks,
            "relevant_share_of_picks": (sum(m["relevant_picks"] for m in metrics) / picks) if picks else None,
            **{f"mean_{name}": mean(name) for name in ("picks", "relevant_in_pool", "pick_precision",
                                                        "top_precision", "ndcg@picks", "ndcg@top")},
            "empty_with_relevant": sum(1 for m in metrics if m["empty_with_relevant"]),
        }
    for left, right in comparisons:
        if left not in systems or right not in systems:
            continue
        entry: dict[str, Any] = {}
        for metric in VERIFY_METRICS:
            paired = []
            for q in per_question:
                rows = q.get("verification") or {}
                a = (rows.get(left) or {}).get("metrics") or {}
                b = (rows.get(right) or {}).get("metrics") or {}
                if a.get(metric) is not None and b.get(metric) is not None:
                    paired.append(a[metric] - b[metric])
            entry[metric] = paired_bootstrap(paired, samples=1000, seed=0)
        out["differences"][f"{left} - {right}"] = entry
    return out


class SourceRetrievalSuite:
    name = "source_retrieval"
    description = ("Slice 2 T6 report: source retrieval vs today's substring search on LLM-labelled "
                   "question -> span pairs (two passes, agreement reported), by query type, with the "
                   "production tutor-span verification on the hybrid_rrf, dense_plus_bm25 and dense pools.")

    def load(self, vault: LoadedVault, request: Any) -> EvalData:
        systems = tuple(request.views) or SYSTEMS
        unknown = set(systems) - set(SYSTEMS)
        if unknown:
            raise ValueError(f"Unknown source_retrieval systems: {', '.join(sorted(unknown))}")
        repository = bench.read_only_repository(vault)
        scope = library_scope(repository)
        if not scope.extractions:
            raise ValueError("The vault has no reader-enabled source with an extraction")
        total = request.max_cases or DEFAULT_QUESTIONS
        logged = _logged(repository, scope)
        seeds = _seeds(repository, scope, type_counts(total - len(logged)))
        dense = load_dense_index(vault, repository, scope).describe() if set(systems) & DENSE_SYSTEMS else {}
        revision = content_key({"seeds": [[seed.qtype, *seed.keys] for seed in seeds],
                                "logged": [entry.text for entry in logged], "scope": sorted(scope.extractions)})
        query_types = {qtype: sum(1 for seed in seeds if seed.qtype == qtype) for qtype in QUERY_TYPES}
        manifest = {"name": "source_retrieval", "version": "t6-eval-v2",
                    "sources": [{"name": "vault library scope", "version": revision[:16],
                                 "licence": "owner's own sources"}],
                    "scope": scope.describe(), "query_types": {**query_types, LOGGED_TYPE: len(logged)}}
        return EvalData(manifest, scope, seeds, logged, systems, revision, dense)

    def plan(self, vault: LoadedVault, data: EvalData, request: Any) -> dict[str, Any]:
        config = vault.config.source_retrieval
        questions = len(data.seeds) + len(data.logged)
        plan: dict[str, Any] = {"questions": questions, "seeded": len(data.seeds),
                                "logged": len(data.logged), "systems": list(data.systems),
                                "query_types": data.manifest.get("query_types"),
                                "dense_index": data.dense, "roles": {}, "embedding": {},
                                "output_tokens": {role: bench.role_budget(vault, role)
                                                  for role in bench.T6_ROLE_TASKS}}
        # Every role plans the candidates and pairs it charges, so a dry run
        # that passes cannot stop part-way on them (review F3).
        writer: dict[str, int] = {"calls": 0, "tokens": 0, "candidates": 0}
        for qtype in QUERY_TYPES:
            part = bench.plan_question_calls(
                [seed.writer_text for seed in data.seeds_of(qtype)], TYPE_PROMPT_VERSIONS[qtype], QUESTION_BATCH,
                bench.role_budget(vault, bench.QUESTION_ROLE), bench.TYPE_INSTRUCTIONS[qtype])
            writer = {name: writer[name] + part[name] for name in writer}
        plan["roles"][bench.QUESTION_ROLE] = writer
        if REWRITE_SYSTEMS & set(data.systems):
            sample = rewrite_prompt("x" * 400, None)
            plan["roles"][bench.REWRITE_ROLE] = {
                "calls": questions, "candidates": questions,  # one candidate per rewrite
                "tokens": questions * estimate_tokens(sample, QueryRewrite,
                                                      bench.role_budget(vault, bench.REWRITE_ROLE))}
        plan["roles"][bench.LABEL_ROLE] = bench.plan_label_calls(
            questions, self.label_pool_bound(data.systems, config), LABEL_BATCH, LABEL_PROMPT_VERSIONS,
            {"source": "x" * 120, "section": "x" * 200, "passage": "x" * LABEL_PASSAGE_CHARS},
            bench.role_budget(vault, bench.LABEL_ROLE))
        verifying = [system for system in data.systems if system in VERIFY_SYSTEMS]
        if verifying:
            # A verification charges one candidate and one pair per pool member.
            bounds = [self.verify_pool_bound(system, config) for system in verifying]
            sample = verify_prompt("x" * 400, "x" * 700, config.tutor_spans, [
                {"ref": f"p{index}", "source": "x" * 120, "section": "x" * 200, "passage": "x" * PASSAGE_CHARS}
                for index in range(1, max(bounds) + 1)])
            calls = questions * len(verifying)
            plan["roles"][bench.VERIFY_ROLE] = {
                "calls": calls, "candidates": questions * sum(bounds), "pairs": questions * sum(bounds),
                "tokens": calls * estimate_tokens(sample, SpanVerification,
                                                  bench.role_budget(vault, bench.VERIFY_ROLE))}
        if set(data.systems) & DENSE_SYSTEMS:
            rewrite = bool(REWRITE_SYSTEMS & set(data.systems))
            texts = questions * (2 if rewrite else 1)
            plan["embedding"][vault.config.embedding.model] = {
                "texts": texts, "calls": -(-texts // EMBED_BATCH) if texts else 0,
                "tokens": questions * (400 + 128) + (questions * (2000 + 128) if rewrite else 0),
            }
        return plan

    @staticmethod
    def verify_pool_bound(system: str, config: Any) -> int:
        """Most candidates a verification system's tutor pool can hold: the dense
        (or fused) top ``tutor_candidate_pool``, and for ``pool_verify`` at most
        ``pool_keyword_extras`` more from each widening list (BM25 and the LOs'
        linked spans; a spare dense hit that stays counts as its list's extra)."""

        k, m = config.tutor_candidate_pool, config.pool_keyword_extras
        return k + 2 * m if system == "pool_verify" else k

    @classmethod
    def label_pool_bound(cls, systems: Sequence[str], config: Any) -> int:
        """Upper bound on one question's labelled candidates: each display
        system's top 10, plus the tutor pools (the teaching scope's, so no overlap
        with the library's lists is assumed; dense_verify's pool is the dense part
        of pool_verify's)."""

        chosen = set(systems)
        bound = bench.TOP_K * sum(1 for system in DISPLAY_SYSTEMS if system in chosen)
        if "pool_verify" in chosen:
            bound += cls.verify_pool_bound("pool_verify", config)
        elif "dense_verify" in chosen:
            bound += cls.verify_pool_bound("dense_verify", config)
        if "hybrid_verify" in chosen:
            bound += cls.verify_pool_bound("hybrid_verify", config)
        return bound

    def run(self, data: EvalData, request: Any, ctx: Any) -> dict[str, Any]:
        vault = ctx.vault
        config = vault.config.source_retrieval
        repository = bench.read_only_repository(vault)
        questions: list[dict[str, Any]] = []
        for qtype in QUERY_TYPES:
            seeds = data.seeds_of(qtype)
            if not seeds:
                continue
            written = bench.write_questions(ctx, [(seed.seed_id, seed.writer_text) for seed in seeds],
                                            version=TYPE_PROMPT_VERSIONS[qtype], batch=QUESTION_BATCH,
                                            instructions=bench.TYPE_INSTRUCTIONS[qtype])
            for seed in seeds:
                entry = written.get(seed.seed_id)
                if entry is not None:
                    questions.append({"text": entry["question"], "seeds": seed.keys, "origin": "generated",
                                      "type": qtype, "writer": entry["model"],
                                      "tutor": self._passage_question(vault, repository, seed.keys)})
        for entry in data.logged:
            questions.append({"text": entry.text, "seeds": [entry.seed] if entry.seed else [],
                              "origin": f"logged_{entry.context}", "type": LOGGED_TYPE, "writer": "learner",
                              "tutor": self._logged_question(vault, repository, entry)})
        rewrites: dict[str, Rewrite] = {}
        if REWRITE_SYSTEMS & set(data.systems):
            role = ctx.role(bench.REWRITE_ROLE)[0]
            for question in questions:
                if not is_conceptual(question["text"]) or question["text"] in rewrites:
                    continue
                call = ctx.caller.call(role, prompt=rewrite_prompt(question["text"], None),
                                       prompt_version=REWRITE_PROMPT_VERSION, result_model=QueryRewrite,
                                       candidates=1)
                keywords = [" ".join(term.split()) for term in call.result.keywords if term.strip()][:12]
                rewrites[question["text"]] = Rewrite("rewritten", " ".join(call.result.passage.split()),
                                                     keywords, call.model)
        index = load_dense_index(vault, repository, data.scope)
        dense_ready = index.ready
        vectors: dict[str, Any] = {}
        if dense_ready and set(data.systems) & DENSE_SYSTEMS:
            texts = [question["text"] for question in questions]
            texts += [rewritten_text(rewrite) for rewrite in rewrites.values()]
            paid = ctx.vectors(vault.config.embedding.model, texts,
                               dims=vault.config.embedding.dimensions, task_prefix="retrieval-query")
            # As production serves a query vector: stored at half precision
            # (practice_index.query_vectors), so the tutor's and the library's
            # dense lists are the ones production would rank (review F5).
            vectors = {text: np.asarray(vector, dtype="<f2").astype(np.float64)
                       for text, vector in paid.items() if vector is not None}
        # Without a complete index only the dense-only systems are unavailable;
        # the others run as production would (hybrid_rrf, keyword lists only).
        systems = [system for system in data.systems if system not in DENSE_ONLY_SYSTEMS or dense_ready]
        display = [system for system in systems if system in DISPLAY_SYSTEMS]
        verifying = [system for system in systems if system in VERIFY_SYSTEMS]
        per_question: list[dict[str, Any]] = []
        all_labels: list[dict[str, list[str | None]]] = []
        incomplete = 0
        label_models: dict[str, int] = {}
        seed_hits: dict[str, list[bool]] = {system: [] for system in systems}
        latency: dict[str, list[float]] = {system: [] for system in verifying}
        statuses: dict[str, dict[str, int]] = {system: {} for system in verifying}
        coverage: dict[str, dict[str, int]] = {system: {"questions": 0, "verified": 0} for system in verifying}
        pool_modes: dict[str, dict[str, int]] = {}
        tutor_contexts: dict[str, int] = {}
        verify_truncations: list[dict[str, Any]] = []
        for question in questions:
            text = question["text"]
            rankings = self._rankings(vault, repository, data.scope, text, display, index, vectors,
                                      rewrites.get(text))
            pools = self._verify_pools(vault, repository, question, verifying, vectors, rewrites, pool_modes)
            if pools:
                described = question["tutor"].describe()
                label = described["context"] + (" (item)" if described["item_bound"] else "")
                tutor_contexts[label] = tutor_contexts.get(label, 0) + 1
            keys = {key for ranked in rankings.values() for key in ranked[: bench.TOP_K]}
            keys |= {hit.record_id for built in pools.values() for hit in built.pool}
            pool = sorted(keys)
            blocks = self._blocks(repository, pool)
            titles = {hit.record_id: hit.source_title for built in pools.values() for hit in built.pool}
            candidates = {
                key: {"source": bench.clip(titles.get(key) or data.scope.extractions[split_record_id(key)[0]].title,
                                           120),
                      "passage": bench.clip(blocks.get(key, ""), LABEL_PASSAGE_CHARS)}
                for key in pool
            }
            labels, models = bench.label_pool(
                ctx, question=text, candidates=candidates, versions=LABEL_PROMPT_VERSIONS,
                batch=LABEL_BATCH, left_kind="source_query", right_kind="source_span",
                right_id=lambda key: key, rationale={"suite": self.name, "revision": data.revision})
            for model, count in models.items():
                label_models[model] = label_models.get(model, 0) + count
            all_labels.append(labels)
            verification: dict[str, Any] = {}
            for system, built in pools.items():
                outcome, seconds = self._verify(ctx, vault, text, built.pool, context=built.verify_context)
                statuses[system][outcome.status] = statuses[system].get(outcome.status, 0) + 1
                coverage[system]["questions"] += 1
                verify_truncations += list(((outcome.usage or {}).get("usage") or {}).get("truncations") or [])
                if outcome.status == "verified":
                    latency[system].append(seconds)
                pool_ids = [hit.record_id for hit in built.pool]
                picks: list[str] = []
                if outcome.ran:
                    coverage[system]["verified"] += 1
                    picks = [hit.record_id for hit in outcome.picks]
                    rankings[system] = picks + [key for key in pool_ids if key not in picks]
                # A verification that did not run is no ranking (review F4):
                # the tutor would fall back to the LO-linked spans, which this
                # report does not score, so the question leaves this system's
                # means and comparisons, and its verdicts are blocked below.
                verification[system] = {
                    "status": outcome.status, "seconds": seconds, "pool": len(pool_ids),
                    "metrics": (verification_metrics(pool_ids, picks, config.tutor_spans, labels)
                                if outcome.ran else None),
                }
            seeds = [block_record_id(*key) for key in question["seeds"]]
            if seeds:
                for system in systems:
                    if system in rankings:
                        seed_hits[system].append(any(key in rankings[system][: bench.TOP_K] for key in seeds))
            scored = bench.score_question(rankings, labels)
            if scored is None:
                incomplete += 1
                continue
            scored.update(origin=question["origin"], type=question["type"],
                          conceptual=is_conceptual(text), verification=verification)
            per_question.append(scored)
        comparisons = [(left, right) for left, right in COMPARISONS if left in systems and right in systems]
        summary = bench.summarize(per_question, systems, comparisons)
        coverage_report = {
            system: {**counts, "failed": counts["questions"] - counts["verified"],
                     "share": (counts["verified"] / counts["questions"]) if counts["questions"] else None}
            for system, counts in coverage.items()
        }
        verdicts = {f"{left} - {right}": bench.beats(summary["differences"][f"{left} - {right}"])
                    for left, right in comparisons}
        blocks = verdict_blocks(comparisons, coverage_report)
        for name in blocks:
            verdicts[name] = False
        return {
            "questions": len(questions),
            "question_origins": _count(question["origin"] for question in questions),
            "question_types": _count(question["type"] for question in questions),
            "scored_questions": len(per_question),
            "incomplete_questions": incomplete,
            "systems": systems,
            "unavailable_systems": {system: index.reason for system in data.systems if system not in systems},
            "dense_index": index.describe(),
            "rewritten_questions": len(rewrites),
            "seed_hit@10": {system: (sum(hits) / len(hits) if hits else None) for system, hits in seed_hits.items()},
            "summary": summary,
            "verification": {
                **summarize_verification(per_question, verifying),
                "pick_at_most": config.tutor_spans,
                "pool_sizes": {"candidate_pool": config.tutor_candidate_pool,
                               "keyword_extras": config.pool_keyword_extras},
                "statuses": statuses,
                "coverage": coverage_report,
                "latency_seconds": {system: _stats(values) for system, values in latency.items()},
                "pool_modes": pool_modes,
                "tutor_contexts": dict(sorted(tutor_contexts.items())),
            },
            "by_type": _by_type(per_question, systems, verifying),
            "by_origin": _split(per_question, systems, "origin"),
            "by_conceptual": _split(per_question, systems, "conceptual"),
            "label_agreement": bench.label_agreement(all_labels),
            "label_models": label_models,
            "truncations": list(ctx.caller.truncations) + verify_truncations,
            "mean_pool": (sum(q["pool"] for q in per_question) / len(per_question)) if per_question else None,
            "mean_relevant": (sum(q["relevant"] for q in per_question) / len(per_question)) if per_question else None,
            "method": {
                "labels": "two LLM passes, different framings and opposite orders; relevant = both at least related",
                "pooling": (f"union of each system's top {bench.TOP_K} and every verification pool "
                            f"(tutor_candidate_pool {config.tutor_candidate_pool}, "
                            f"pool_keyword_extras {config.pool_keyword_extras})"),
                "baseline": "substring = today's library search: instr(lower(text), query), document order",
                "verification": (f"the production verify_spans (route source_rerank) picks at most "
                                 f"{config.tutor_spans} from the tutor's own pool (tutor_pool: the teaching "
                                 "scope, the LOs' linked spans, answer overlap withheld, the practice question "
                                 "shown to the verifier); its ranking is the picks then the rest of its pool. A "
                                 "verification that did not run is not scored (the tutor would fall back to the "
                                 "LO-linked spans) and blocks that system's verdicts"),
                "tutor_context": ("a logged practice or feedback question keeps its item, a logged library "
                                  "question its note's LOs; a generated or reader question is asked as a "
                                  "library question about the LOs the reader links to its passages"),
                "bar": (f"a system beats another when the nDCG@10 difference's 95% bootstrap interval is "
                        f"above 0, mean Recall@10 is not worse and at least {bench.MIN_SCORED_QUESTIONS} "
                        "questions are scored"),
            },
            "verdicts": verdicts,
            "verdict_blocks": blocks,
        }

    def _rankings(self, vault: LoadedVault, repository: Repository, scope: Scope, text: str,
                  systems: Iterable[str], index: Any, vectors: dict[str, Any],
                  rewrite: Rewrite | None) -> dict[str, list[str]]:
        extraction_ids = sorted(scope.extractions)
        rankings: dict[str, list[str]] = {}
        for system in systems:
            if system == "substring":
                rows = repository.search_source_blocks(query=text, extraction_ids=extraction_ids,
                                                       limit=bench.TOP_K)
                rankings[system] = [block_record_id(str(r["extraction_id"]), str(r["span_id"])) for r in rows]
            elif system == "keyword":
                with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                    rankings[system] = [block_record_id(m.extraction_id, m.span_id) for m in search_blocks(
                        connection, text, extraction_ids=extraction_ids, limit=bench.TOP_K)]
            elif system == "meaning":
                vector = vectors.get(text)
                rankings[system] = [] if vector is None else [
                    record_id for record_id, _ in index.rank(vector, limit=bench.TOP_K)]
            elif system in VERIFY_SYSTEMS:
                continue
            else:
                # The production deep search on vectors and rewrites already paid
                # for: search_spans makes no call when both are supplied. The
                # library shows MAX_HITS; its top 10 is what is scored.
                rewritten = rewrite if system in REWRITE_SYSTEMS else None
                query_vectors = {"query": vectors[text]} if text in vectors else {}
                if rewritten is not None and rewritten_text(rewritten) in vectors:
                    query_vectors["rewrite"] = vectors[rewritten_text(rewritten)]
                search = search_spans(
                    vault, repository, text, scope, limit=MAX_HITS, deep=True,
                    rewrite=rewritten is not None, include_substring=True,
                    query_vectors=query_vectors, rewritten=rewritten,
                    pool=POOL_DENSE_PLUS_BM25 if system == "pool_rewrite" else POOL_HYBRID_RRF,
                )
                rankings[system] = [hit.record_id for hit in search.hits][: bench.TOP_K]
        return rankings

    def _passage_question(self, vault: LoadedVault, repository: Repository,
                          keys: Sequence[tuple[str, str]]) -> TutorQuestion:
        """A generated (or reader) question: a library question about its passages' LOs."""

        from learnloop.reader.reader_progression import learning_objects_for_span

        lo_ids: dict[str, None] = {}
        for extraction_id, span_id in keys:
            for lo_id in learning_objects_for_span(vault, repository, extraction_id=extraction_id,
                                                   span_id=span_id):
                lo_ids.setdefault(lo_id, None)
        return TutorQuestion(GENERATED_CONTEXT, tuple(lo_ids))

    def _logged_question(self, vault: LoadedVault, repository: Repository,
                         entry: LoggedQuestion) -> TutorQuestion:
        """A logged question in the context the learner asked it (review F5)."""

        if entry.context in ITEM_BOUND_CONTEXTS and entry.item_id in vault.practice_items:
            item = vault.practice_items[entry.item_id]
            return TutorQuestion(entry.context, (item.learning_object_id,), item.id)
        if entry.context == "library" and entry.note_id in vault.notes:
            return TutorQuestion("library", tuple(vault.notes[entry.note_id].related_los))
        return self._passage_question(vault, repository, [entry.seed] if entry.seed else [])

    def _verify_pools(self, vault: LoadedVault, repository: Repository, question: Mapping[str, Any],
                      systems: Sequence[str], vectors: Mapping[str, Any], rewrites: Mapping[str, Rewrite],
                      pool_modes: dict[str, dict[str, int]]) -> dict[str, TutorPool]:
        """The pools each verification system judges: the tutor's own construction
        (``tutor_pool``) for this question's context, on vectors already paid for."""

        if not systems:
            return {}
        text = question["text"]
        tutor: TutorQuestion = question["tutor"]
        item = vault.practice_items.get(tutor.item_id) if tutor.item_id else None
        query_vectors = {"query": vectors[text]} if text in vectors else {}
        # The tutor rewrites only when tutor_query_rewrite is on (off by default);
        # the bench then reuses the rewrite and its vector it already paid for.
        rewritten = rewrites.get(text) if vault.config.source_retrieval.tutor_query_rewrite else None
        if rewritten is not None and rewritten_text(rewritten) in vectors:
            query_vectors["rewrite"] = vectors[rewritten_text(rewritten)]
        pools: dict[str, TutorPool] = {}
        for system in systems:
            mode, extras = VERIFY_POOLS[system]
            built = tutor_pool(vault, repository, context=tutor.context, question_md=text,
                               learning_object_ids=tutor.learning_object_ids, item=item,
                               query_vectors=query_vectors, rewrite=rewritten is not None,
                               rewritten=rewritten, pool=mode, pool_extras=extras)
            used = str((built.search.pool or {}).get("mode"))
            counts = pool_modes.setdefault(system, {})
            counts[used] = counts.get(used, 0) + 1
            pools[system] = built
        return pools

    def _verify(self, ctx: Any, vault: LoadedVault, text: str, hits: Sequence[SpanHit],
                context: str | None = None) -> tuple[Any, float]:
        """The production verification under the harness's budget, price and receipts."""

        entry = ctx.role(bench.VERIFY_ROLE)[0]
        budget = ctx.caller.subscription if entry.subscription else ctx.caller.metered
        started = time.monotonic()
        # Every attempt (the call, its retries, their candidates and pairs) is
        # admitted under the harness's shared caps across billing classes, and
        # only once the ledger and checkpoints did not answer it (review F2).
        outcome = verify_spans(vault, ctx.caller.repository, question=text, pool=list(hits),
                               pick_at_most=vault.config.source_retrieval.tutor_spans, context=context,
                               client=entry.client, owner_id=ctx.caller.run_id, budget=budget,
                               price_per_million=ctx.caller.price, admit=ctx.caller.check_shared)
        seconds = time.monotonic() - started
        if outcome.status == "cancelled":
            raise AIInterrupted("Verification cancelled")
        if outcome.status == "over_budget":
            raise SpendLimitExceeded(outcome.reason or "Verification exceeds the caps")
        if outcome.status == "verified":
            ctx.caller.calls_by_role[bench.VERIFY_ROLE] += 1
            ctx.caller.calls_by_model[outcome.model or entry.model or "unknown"][bench.VERIFY_ROLE] += 1
        elif outcome.status == "cached":
            ctx.caller.cached_by_role[bench.VERIFY_ROLE] += 1
        return outcome, seconds

    def _blocks(self, repository: Repository, keys: list[str]) -> dict[str, str]:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            rows = blocks_by_key(connection, [split_record_id(key) for key in keys])
            titles = {extraction_id: section_header_titles(connection, extraction_id)
                      for extraction_id in sorted({key[0] for key in rows})}
        return {block_record_id(*key): source_block_text(block, titles[key[0]]) for key, block in rows.items()}

    def markdown_lines(self, results: dict[str, Any]) -> list[str]:
        types = results.get("question_types") or {}
        lines = [f"Questions: {results.get('questions')} (scored {results.get('scored_questions')}, "
                 f"incomplete {results.get('incomplete_questions')}; "
                 + ", ".join(f"{name} {count}" for name, count in types.items())
                 + f"); dense index: {(results.get('dense_index') or {}).get('status')}.", "",
                 "| System | nDCG@10 | Recall@10 | MRR@10 | seed hit@10 |", "|---|---|---|---|---|"]
        means = (results.get("summary") or {}).get("means", {})
        for system in results.get("systems", []):
            row = means.get(system, {})
            lines.append(f"| {system} | {_fmt(row.get('ndcg@10'))} | {_fmt(row.get('recall@10'))} | "
                         f"{_fmt(row.get('mrr@10'))} | {_fmt((results.get('seed_hit@10') or {}).get(system))} |")
        blocked = results.get("verdict_blocks") or {}
        lines += ["", "| Comparison | Δ nDCG@10 [95% CI] | Δ Recall@10 | beats |", "|---|---|---|---|"]
        for name, entry in ((results.get("summary") or {}).get("differences") or {}).items():
            ndcg = entry.get("ndcg@10", {})
            ci = ndcg.get("ci95") or [None, None]
            verdict = "blocked" if name in blocked else (results.get("verdicts") or {}).get(name)
            lines.append(f"| {name} | {_fmt(ndcg.get('mean'))} [{_fmt(ci[0])}, {_fmt(ci[1])}] | "
                         f"{_fmt((entry.get('recall@10') or {}).get('mean'))} | {verdict} |")
        for name, reason in blocked.items():
            lines.append(f"- {name} blocked: {reason}.")
        verification = results.get("verification") or {}
        if verification.get("systems"):
            coverage = verification.get("coverage") or {}
            contexts = ", ".join(f"{name} {count}" for name, count in (verification.get("tutor_contexts") or {}).items())
            lines += ["", f"Verification (production verify_spans on the tutor's own pools, at most "
                      f"{verification.get('pick_at_most')} picks; asked as: {contexts or '—'}):",
                      "", "| System | verified / asked | picks/q | relevant share of picks | top-k share (unverified) | "
                      "nDCG@picks | empty with relevant | latency p50 / p90 s |", "|---|---|---|---|---|---|---|---|"]
            for system, row in verification["systems"].items():
                stats = (verification.get("latency_seconds") or {}).get(system) or {}
                counts = coverage.get(system) or {}
                lines.append(f"| {system} | {counts.get('verified')} / {counts.get('questions')} | "
                             f"{_fmt(row['mean_picks'])} | "
                             f"{_fmt(row['relevant_share_of_picks'])} | {_fmt(row['mean_top_precision'])} | "
                             f"{_fmt(row['mean_ndcg@picks'])} | {row['empty_with_relevant']} | "
                             f"{_fmt(stats.get('p50'))} / {_fmt(stats.get('p90'))} |")
            for name, entry in (verification.get("differences") or {}).items():
                parts = []
                for metric in VERIFY_METRICS:
                    boot = entry.get(metric) or {}
                    ci = boot.get("ci95") or [None, None]
                    parts.append(f"{metric} {_fmt(boot.get('mean'))} [{_fmt(ci[0])}, {_fmt(ci[1])}] "
                                 f"(n {boot.get('n')})")
                lines.append(f"- {name}: " + "; ".join(parts))
        by_type = results.get("by_type") or {}
        if by_type:
            systems = results.get("systems", [])
            lines += ["", "By query type (nDCG@10; verification systems also: relevant share of picks):", "",
                      "| Type | n | " + " | ".join(systems) + " |", "|---|---|" + "---|" * len(systems)]
            for qtype, entry in by_type.items():
                cells = []
                for system in systems:
                    ndcg = _fmt((entry["means"].get(system) or {}).get("ndcg@10"))
                    if system in VERIFY_SYSTEMS:
                        share = ((entry.get("verification") or {}).get(system) or {}).get("relevant_share_of_picks")
                        cells.append(f"{ndcg} ({_fmt(share)})")
                    else:
                        cells.append(ndcg)
                lines.append(f"| {qtype} | {entry['questions']} | " + " | ".join(cells) + " |")
        agreement = results.get("label_agreement") or {}
        lines += ["", f"Label agreement: {agreement.get('pairs')} pairs, exact {_fmt(agreement.get('exact'))}, "
                  f"kappa {_fmt(agreement.get('cohen_kappa'))}, binary kappa {_fmt(agreement.get('binary_cohen_kappa'))}.",
                  f"Truncated LLM answers (each retried once at double the budget): "
                  f"{len(results.get('truncations') or [])}."]
        return lines


def _fmt(value: Any) -> str:
    return "—" if value is None else f"{value:.3f}" if isinstance(value, float) else str(value)


def _count(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _split(per_question: list[dict[str, Any]], systems: list[str], key: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for question in per_question:
        groups.setdefault(str(question[key]), []).append(question)
    return {name: bench.summarize(rows, systems, [])["means"] | {"questions": len(rows)}
            for name, rows in sorted(groups.items())}


def _by_type(per_question: list[dict[str, Any]], systems: list[str], verifying: list[str]) -> dict[str, Any]:
    """Every metric within each query type (generated types, then logged)."""

    groups: dict[str, list[dict[str, Any]]] = {}
    for question in per_question:
        groups.setdefault(str(question["type"]), []).append(question)
    order = [qtype for qtype in (*QUERY_TYPES, LOGGED_TYPE) if qtype in groups]
    comparisons = [(left, right) for left, right in TYPE_COMPARISONS if left in systems and right in systems]
    out: dict[str, Any] = {}
    for qtype in order:
        rows = groups[qtype]
        summary = bench.summarize(rows, systems, comparisons)
        out[qtype] = {"questions": len(rows), "means": summary["means"], "differences": summary["differences"],
                      "verification": summarize_verification(rows, verifying)["systems"]}
    return out


def verdict_blocks(comparisons: Sequence[tuple[str, str]],
                   coverage: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    """Comparisons whose verdict is blocked: a verification system with a
    verification that did not run (review F4). Its scored questions are only
    those it verified, so a win there says nothing about the tutor."""

    blocks: dict[str, str] = {}
    for left, right in comparisons:
        reasons = [f"{counts['failed']} of {counts['questions']} {system} verifications did not run "
                   "(the tutor would fall back to the LO-linked spans; not scored)"
                   for system in (left, right)
                   if (counts := coverage.get(system)) and counts.get("failed")]
        if reasons:
            blocks[f"{left} - {right}"] = "; ".join(reasons)
    return blocks


__all__ = [
    "COMPARISONS",
    "DISPLAY_SYSTEMS",
    "LABEL_PROMPT_VERSIONS",
    "QUERY_TYPES",
    "QUESTION_PROMPT_VERSION",
    "SYSTEMS",
    "SourceRetrievalSuite",
    "TYPE_PROMPT_VERSIONS",
    "VERIFY_SYSTEMS",
    "summarize_verification",
    "type_counts",
    "verdict_blocks",
    "verification_metrics",
]
