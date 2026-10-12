"""The T6 report: source retrieval vs today's substring search (suite ``source_retrieval``).

Runs on the shared ``learnloop embeddings compare`` harness (Slice 2 §4,
§13: "retrieval recall on LLM-labelled question → span pairs, two passes, with
agreement reported").

* **Corpus.** The library scope: every reader-enabled source's current blocks.
* **Questions.** LLM-written questions seeded from sampled substantive blocks
  (the seed is a known-relevant span: its hit rate is a label-free check), plus
  logged tutor questions: a reader question's anchored span is its seed.
* **Systems.** ``substring`` is today's library search (``instr`` of the whole
  query, document order); ``keyword`` FTS5 BM25; ``meaning`` the dense index
  over stored ``source_block/text`` vectors; ``hybrid`` the production deep
  search without a rewrite; ``hybrid_rewrite`` with the production LLM rewrite
  for conceptual questions. Dense systems need a complete
  ``source_block/text`` backfill for ``embedding.model``; without it they are
  reported as unavailable, never approximated.
* **Labels and metrics** as in ``bench``: two LLM passes, agreement, nDCG@10,
  Recall@10, MRR, paired bootstrap intervals against ``substring`` and between
  adjacent systems.

Reports are aggregate only; every verdict is in ``judgment_ledger``.
"""
from __future__ import annotations

from collections.abc import Iterable
from contextlib import closing
from dataclasses import dataclass, field
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import (
    blocks_by_key,
    extraction_blocks,
    search_blocks,
    section_header_titles,
)
from learnloop.ops.pf_calls import estimate_tokens
from learnloop.source_retrieval import bench
from learnloop.source_retrieval.contracts import QueryRewrite
from learnloop.source_retrieval.corpus import Scope, library_scope
from learnloop.source_retrieval.dense import load_dense_index
from learnloop.source_retrieval.queries import (
    REWRITE_OUTPUT_TOKENS,
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
from learnloop.source_retrieval.search import search_spans
from learnloop.vault.models import LoadedVault

SYSTEMS = ("substring", "keyword", "meaning", "hybrid", "hybrid_rewrite")
DENSE_SYSTEMS = frozenset({"meaning", "hybrid", "hybrid_rewrite"})
DEFAULT_QUESTIONS = 40
QUESTION_PROMPT_VERSION = "source_eval_question.v1"
LABEL_PROMPT_VERSIONS = ("source_relevance_label.v1.pass1", "source_relevance_label.v1.pass2")
QUESTION_BATCH = 8
LABEL_BATCH = 20
SEED_MIN_CHARS = 60
SEED_CHARS = 1200
LABEL_PASSAGE_CHARS = 900
EMBED_BATCH = 32
COMPARISONS = (("keyword", "substring"), ("meaning", "substring"), ("hybrid", "substring"),
               ("hybrid_rewrite", "substring"), ("hybrid", "keyword"), ("hybrid_rewrite", "hybrid"))


@dataclass
class Seed:
    key: tuple[str, str]
    text: str


@dataclass
class LoggedQuestion:
    text: str
    seed: tuple[str, str] | None
    context: str


@dataclass
class EvalData:
    manifest: dict[str, Any]
    scope: Scope
    seeds: list[Seed]
    logged: list[LoggedQuestion]
    systems: tuple[str, ...]
    revision: str
    dense: dict[str, Any] = field(default_factory=dict)


def _seeds(repository: Repository, scope: Scope, count: int) -> list[Seed]:
    candidates: list[Seed] = []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        for extraction_id in sorted(scope.extractions):
            for block in extraction_blocks(connection, extraction_id):
                text = " ".join(block.text.split())
                if embeddable(block) and len(text) >= SEED_MIN_CHARS and scope.allows(*(
                        block.extraction_id, block.span_id)):
                    candidates.append(Seed((block.extraction_id, block.span_id), text[:SEED_CHARS]))
    candidates.sort(key=lambda seed: bench.stable_key("t6-seed-v1", *seed.key))
    return candidates[: max(0, count)]


def _logged(repository: Repository, scope: Scope, count: int) -> list[LoggedQuestion]:
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
        found.append(LoggedQuestion(text[:400], seed, str(event.get("context") or "")))
    found.sort(key=lambda entry: bench.stable_key("t6-logged-v1", entry.text))
    unique: dict[str, LoggedQuestion] = {}
    for entry in found:
        unique.setdefault(entry.text.lower(), entry)
    return list(unique.values())[: max(0, count)]


class SourceRetrievalSuite:
    name = "source_retrieval"
    description = ("Slice 2 T6 report: hybrid source retrieval vs today's substring search on "
                   "LLM-labelled question -> span pairs (two passes, agreement reported).")

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
        logged = _logged(repository, scope, total // 4)
        seeds = _seeds(repository, scope, total - len(logged))
        dense = load_dense_index(vault, repository, scope).describe() if set(systems) & DENSE_SYSTEMS else {}
        revision = content_key({"seeds": [seed.key for seed in seeds],
                                "logged": [entry.text for entry in logged], "scope": sorted(scope.extractions)})
        manifest = {"name": "source_retrieval", "version": "t6-eval-v1",
                    "sources": [{"name": "vault library scope", "version": revision[:16],
                                 "licence": "owner's own sources"}],
                    "scope": scope.describe()}
        return EvalData(manifest, scope, seeds, logged, systems, revision, dense)

    def plan(self, vault: LoadedVault, data: EvalData, request: Any) -> dict[str, Any]:
        questions = len(data.seeds) + len(data.logged)
        plan: dict[str, Any] = {"questions": questions, "seeded": len(data.seeds),
                                "logged": len(data.logged), "systems": list(data.systems),
                                "dense_index": data.dense, "roles": {}, "embedding": {}}
        plan["roles"][bench.QUESTION_ROLE] = bench.plan_question_calls(
            [seed.text for seed in data.seeds], QUESTION_PROMPT_VERSION, QUESTION_BATCH)
        if "hybrid_rewrite" in data.systems:
            sample = rewrite_prompt("x" * 400, None)
            plan["roles"][bench.REWRITE_ROLE] = {
                "calls": questions, "tokens": questions * estimate_tokens(sample, QueryRewrite, REWRITE_OUTPUT_TOKENS)}
        plan["roles"][bench.LABEL_ROLE] = bench.plan_label_calls(
            questions, bench.TOP_K * len(data.systems), LABEL_BATCH, LABEL_PROMPT_VERSIONS,
            {"source": "x" * 120, "section": "x" * 200, "passage": "x" * LABEL_PASSAGE_CHARS})
        if set(data.systems) & DENSE_SYSTEMS:
            texts = questions * (2 if "hybrid_rewrite" in data.systems else 1)
            plan["embedding"][vault.config.embedding.model] = {
                "texts": texts, "calls": -(-texts // EMBED_BATCH) if texts else 0,
                "tokens": questions * (400 + 128) + (questions * (2000 + 128) if "hybrid_rewrite" in data.systems else 0),
            }
        return plan

    def run(self, data: EvalData, request: Any, ctx: Any) -> dict[str, Any]:
        vault = ctx.vault
        repository = bench.read_only_repository(vault)
        written = bench.write_questions(ctx, [(block_record_id(*seed.key), seed.text) for seed in data.seeds],
                                        version=QUESTION_PROMPT_VERSION, batch=QUESTION_BATCH)
        questions: list[dict[str, Any]] = []
        for seed in data.seeds:
            entry = written.get(block_record_id(*seed.key))
            if entry is not None:
                questions.append({"text": entry["question"], "seed": seed.key, "origin": "generated",
                                  "writer": entry["model"]})
        for entry in data.logged:
            questions.append({"text": entry.text, "seed": entry.seed, "origin": f"logged_{entry.context}",
                              "writer": "learner"})
        rewrites: dict[str, Rewrite] = {}
        if "hybrid_rewrite" in data.systems:
            role = ctx.role(bench.REWRITE_ROLE)[0]
            for question in questions:
                if not is_conceptual(question["text"]):
                    continue
                call = ctx.caller.call(role, prompt=rewrite_prompt(question["text"], None),
                                       prompt_version=REWRITE_PROMPT_VERSION, result_model=QueryRewrite,
                                       output_tokens=REWRITE_OUTPUT_TOKENS, candidates=1)
                keywords = [" ".join(term.split()) for term in call.result.keywords if term.strip()][:12]
                rewrites[question["text"]] = Rewrite("rewritten", " ".join(call.result.passage.split()),
                                                     keywords, call.model)
        index = load_dense_index(vault, repository, data.scope)
        dense_ready = index.ready
        vectors: dict[str, Any] = {}
        if dense_ready and set(data.systems) & DENSE_SYSTEMS:
            texts = [question["text"] for question in questions]
            texts += [rewritten_text(rewrite) for rewrite in rewrites.values()]
            vectors = ctx.vectors(vault.config.embedding.model, texts,
                                  dims=vault.config.embedding.dimensions, task_prefix="retrieval-query")
        # Without a complete index only the pure dense system is unavailable;
        # the hybrids then fuse their keyword (and rewrite) lists, as production would.
        systems = [system for system in data.systems if system != "meaning" or dense_ready]
        per_question: list[dict[str, Any]] = []
        all_labels: list[dict[str, list[str | None]]] = []
        incomplete = 0
        label_models: dict[str, int] = {}
        seed_hits: dict[str, list[bool]] = {system: [] for system in systems}
        for question in questions:
            rankings = self._rankings(vault, repository, data.scope, question["text"], systems,
                                      index, vectors, rewrites.get(question["text"]))
            pool = sorted({key for ranked in rankings.values() for key in ranked[: bench.TOP_K]})
            blocks = self._blocks(repository, pool)
            candidates = {
                key: {"source": bench.clip(data.scope.extractions[split_record_id(key)[0]].title, 120),
                      "passage": bench.clip(blocks.get(key, ""), LABEL_PASSAGE_CHARS)}
                for key in pool
            }
            labels, models = bench.label_pool(
                ctx, question=question["text"], candidates=candidates, versions=LABEL_PROMPT_VERSIONS,
                batch=LABEL_BATCH, left_kind="source_query", right_kind="source_span",
                right_id=lambda key: key, rationale={"suite": self.name, "revision": data.revision})
            for model, count in models.items():
                label_models[model] = label_models.get(model, 0) + count
            all_labels.append(labels)
            if question["seed"] is not None:
                seed_key = block_record_id(*question["seed"])
                for system in systems:
                    seed_hits[system].append(seed_key in rankings[system][: bench.TOP_K])
            scored = bench.score_question(rankings, labels)
            if scored is None:
                incomplete += 1
                continue
            scored.update(origin=question["origin"], conceptual=is_conceptual(question["text"]))
            per_question.append(scored)
        comparisons = [(left, right) for left, right in COMPARISONS if left in systems and right in systems]
        summary = bench.summarize(per_question, systems, comparisons)
        return {
            "questions": len(questions),
            "question_origins": _count(question["origin"] for question in questions),
            "scored_questions": len(per_question),
            "incomplete_questions": incomplete,
            "systems": systems,
            "unavailable_systems": {system: index.reason for system in data.systems if system not in systems},
            "dense_index": index.describe(),
            "rewritten_questions": len(rewrites),
            "seed_hit@10": {system: (sum(hits) / len(hits) if hits else None) for system, hits in seed_hits.items()},
            "summary": summary,
            "by_origin": _split(per_question, systems, "origin"),
            "by_conceptual": _split(per_question, systems, "conceptual"),
            "label_agreement": bench.label_agreement(all_labels),
            "label_models": label_models,
            "mean_pool": (sum(q["pool"] for q in per_question) / len(per_question)) if per_question else None,
            "mean_relevant": (sum(q["relevant"] for q in per_question) / len(per_question)) if per_question else None,
            "method": {
                "labels": "two LLM passes, different framings and opposite orders; relevant = both at least related",
                "pooling": f"union of each system's top {bench.TOP_K}",
                "baseline": "substring = today's library search: instr(lower(text), query), document order",
                "bar": (f"a system beats another when the nDCG@10 difference's 95% bootstrap interval is "
                        f"above 0, mean Recall@10 is not worse and at least {bench.MIN_SCORED_QUESTIONS} "
                        "questions are scored"),
            },
            "verdicts": {f"{left} - {right}": bench.beats(summary["differences"][f"{left} - {right}"])
                         for left, right in comparisons},
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
            else:
                # The production deep search on vectors and rewrites already paid
                # for: search_spans makes no call when both are supplied.
                rewritten = rewrite if system == "hybrid_rewrite" else None
                query_vectors = {"query": vectors[text]} if text in vectors else {}
                if rewritten is not None and rewritten_text(rewritten) in vectors:
                    query_vectors["rewrite"] = vectors[rewritten_text(rewritten)]
                search = search_spans(
                    vault, repository, text, scope, limit=bench.TOP_K, deep=True,
                    rewrite=rewritten is not None, include_substring=True,
                    query_vectors=query_vectors, rewritten=rewritten,
                )
                rankings[system] = [hit.record_id for hit in search.hits]
        return rankings

    def _blocks(self, repository: Repository, keys: list[str]) -> dict[str, str]:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            rows = blocks_by_key(connection, [split_record_id(key) for key in keys])
            titles = {extraction_id: section_header_titles(connection, extraction_id)
                      for extraction_id in sorted({key[0] for key in rows})}
        return {block_record_id(*key): source_block_text(block, titles[key[0]]) for key, block in rows.items()}

    def markdown_lines(self, results: dict[str, Any]) -> list[str]:
        lines = [f"Questions: {results.get('questions')} (scored {results.get('scored_questions')}, "
                 f"incomplete {results.get('incomplete_questions')}); dense index: "
                 f"{(results.get('dense_index') or {}).get('status')}.", "",
                 "| System | nDCG@10 | Recall@10 | MRR@10 | seed hit@10 |", "|---|---|---|---|---|"]
        means = (results.get("summary") or {}).get("means", {})
        for system in results.get("systems", []):
            row = means.get(system, {})
            lines.append(f"| {system} | {_fmt(row.get('ndcg@10'))} | {_fmt(row.get('recall@10'))} | "
                         f"{_fmt(row.get('mrr@10'))} | {_fmt((results.get('seed_hit@10') or {}).get(system))} |")
        lines += ["", "| Comparison | Δ nDCG@10 [95% CI] | Δ Recall@10 | beats |", "|---|---|---|---|"]
        for name, entry in ((results.get("summary") or {}).get("differences") or {}).items():
            ndcg = entry.get("ndcg@10", {})
            ci = ndcg.get("ci95") or [None, None]
            lines.append(f"| {name} | {_fmt(ndcg.get('mean'))} [{_fmt(ci[0])}, {_fmt(ci[1])}] | "
                         f"{_fmt((entry.get('recall@10') or {}).get('mean'))} | "
                         f"{(results.get('verdicts') or {}).get(name)} |")
        agreement = results.get("label_agreement") or {}
        lines += ["", f"Label agreement: {agreement.get('pairs')} pairs, exact {_fmt(agreement.get('exact'))}, "
                  f"kappa {_fmt(agreement.get('cohen_kappa'))}, binary kappa {_fmt(agreement.get('binary_cohen_kappa'))}."]
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


__all__ = ["COMPARISONS", "LABEL_PROMPT_VERSIONS", "QUESTION_PROMPT_VERSION", "SYSTEMS", "SourceRetrievalSuite"]
