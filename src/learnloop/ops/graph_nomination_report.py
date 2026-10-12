"""Slice 2 T5 report (spec §13): nomination recall on doctor-found duplicates.

The question: would the definition-embedding top-k have put in front of the
deciding model the duplicates the lexical review passes already find? And what
does it nominate that they miss? It is a report, not a threshold (R6): nothing
here merges, aliases or sets a cutoff that any code path reads.

* **Ground truth** (no vectors needed): the doctor's registry near-duplicate
  facets (Jaccard), the D2 mint gate re-run over the registry (its ALIAS
  verdicts), the doctor's concept merge candidates, and ``same`` verdicts in
  ``judgment_ledger`` for ``same_concept`` / ``duplicate_facet`` between two
  current registry records.
* **Paid step**: the Phase 1 backfill of the three recipes the report reads
  (``facet/definition``, ``concept/definition``, ``facet_repair/text``), under
  its caps. ``dry_run`` plans it with no client, migration or data change.
* **Metrics** (stored vectors only): recall@k of each source, the cosine that
  would keep 90/95/100% of those pairs (a candidate blocking cutoff per R4,
  recorded, never applied), the all-pairs noise floor, embedding-only mutual
  nearest neighbours (what lexical misses; unjudged), the repair-equivalence
  shadow over D2's pairs, and the ingest-time nomination records.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from contextlib import closing
import json
import math
import sqlite3
from typing import Any

import numpy as np

from learnloop.ai.embedding import EmbeddingClient
from learnloop.ai.spend import SpendCaps
from learnloop.content.synthesis.facet_doctor import near_duplicate_facet_review
from learnloop.content.synthesis.facet_mint_gate import MintDisposition, judge_facet_mints
from learnloop.content.synthesis.graph_nomination import (
    CONCEPT_RECIPE,
    FACET_RECIPE,
    GraphNominator,
    NOMINATION_VERSION,
    RegistryIndex,
    annotate_mint_report,
    raw_cosine,
    repair_query,
)
from learnloop.db.connection import connect
from learnloop.ops.doctor import concept_merge_candidate_pairs
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

REPORT_VERSION = "t5-nomination-report-1"
REPORT_RECIPES = (FACET_RECIPE, CONCEPT_RECIPE, "facet_repair/text")
RECALL_KS = (1, 3, 5, 10)
RECALL_TARGETS = (0.9, 0.95, 1.0)
MAX_LISTED = 25
LEDGER_TASKS = {"duplicate_facet": "facet", "same_concept": "concept"}


def _pair(left: str, right: str) -> tuple[str, str]:
    return (left, right) if left <= right else (right, left)


def ground_truth(loaded: LoadedVault) -> dict[str, dict[str, set[tuple[str, str]]]]:
    """``{"facet"|"concept": {source: {(a, b), ...}}}`` from the lexical review passes."""

    facets: dict[str, set[tuple[str, str]]] = defaultdict(set)
    concepts: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for proposal in near_duplicate_facet_review(loaded):
        facets["doctor_near_duplicate"].add(_pair(proposal.left_facet_id, proposal.right_facet_id))
    payloads = [facet.model_dump(mode="json") for _id, facet in sorted(loaded.evidence_facets.items())]
    for verdict in judge_facet_mints(payloads).verdicts:
        if verdict.disposition is MintDisposition.ALIAS and verdict.alias_of:
            facets["d2_alias"].add(_pair(verdict.candidate_id, verdict.alias_of))
    for left, right, _score, strong_alias in concept_merge_candidate_pairs(loaded):
        source = "doctor_strong_alias" if strong_alias else "doctor_similarity"
        concepts[source].add(_pair(left, right))
    return {"facet": dict(facets), "concept": dict(concepts)}


def _ledger(loaded: LoadedVault) -> tuple[dict[str, set[tuple[str, str]]], list[dict[str, Any]]]:
    """Confirmed pairs between current registry records, and verdict counts."""

    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    confirmed: dict[str, set[tuple[str, str]]] = {"facet": set(), "concept": set()}
    counts: Counter[tuple[str, str, str, str]] = Counter()
    if not sqlite_path.exists():
        return confirmed, []
    try:
        with closing(connect(sqlite_path, read_only=True)) as connection:
            rows = connection.execute(
                "SELECT id,supersedes_id,task,left_kind,left_id,right_kind,right_id,judge,"
                "judge_model,verdict FROM judgment_ledger WHERE task IN (?, ?) "
                "ORDER BY created_at, id",
                tuple(LEDGER_TASKS),
            ).fetchall()
    except sqlite3.Error:
        return confirmed, []
    superseded = {row[1] for row in rows if row[1]}
    authority = {"owner": 4, "verifier": 3, "llm": 2, "diagnoser": 2, "exact_key": 2, "learner_card": 1}
    latest: dict[tuple[str, str, str], tuple[int, str]] = {}
    for (row_id, _sup, task, left_kind, left_id, right_kind, right_id, judge, model, verdict) in rows:
        counts[(task, judge, model or "", verdict)] += 1
        kind = LEDGER_TASKS[task]
        if row_id in superseded or left_kind != kind or right_kind != kind or not right_id:
            continue
        key = (kind, *_pair(left_id, right_id))
        rank = authority.get(judge, 0)
        if key not in latest or rank >= latest[key][0]:
            latest[key] = (rank, verdict)
    current = {"facet": set(loaded.evidence_facets), "concept": set(loaded.concepts)}
    for (kind, left, right), (_rank, verdict) in latest.items():
        if verdict == "same" and left in current[kind] and right in current[kind]:
            confirmed[kind].add((left, right))
    listed = [
        {"task": task, "judge": judge, "judge_model": model, "verdict": verdict, "count": count}
        for (task, judge, model, verdict), count in sorted(counts.items())
    ]
    return confirmed, listed


def _quantiles(values: Iterable[float]) -> dict[str, float] | None:
    array = np.asarray(list(values), dtype=np.float64)
    if not array.size:
        return None
    return {
        "n": int(array.size),
        **{f"p{q}": round(float(np.percentile(array, q)), 4) for q in (5, 50, 90, 95, 99)},
        "max": round(float(array.max()), 4),
    }


def recall_block(
    index: RegistryIndex | None, status: str, sources: dict[str, set[tuple[str, str]]],
    *, top_k: int, ks: Iterable[int] = RECALL_KS,
) -> dict[str, Any]:
    """Recall@k of each ground-truth source under the stored index."""

    union = set().union(*sources.values()) if sources else set()
    block: dict[str, Any] = {
        "index_status": status,
        "pairs_by_source": {name: len(pairs) for name, pairs in sorted(sources.items())},
        "pairs": len(union),
    }
    if index is None or not len(index):
        block["note"] = "no complete stored index: run the backfill (this report without --stored-only does)"
        return block
    ks = sorted({*ks, top_k})
    rank_cache: dict[str, dict[str, tuple[int, float]]] = {}

    def ranks(record_id: str) -> dict[str, tuple[int, float]]:
        if record_id not in rank_cache:
            vector = index.vector(record_id)
            rank_cache[record_id] = {} if vector is None else index.ranks(vector, exclude={record_id})
        return rank_cache[record_id]

    measured: dict[tuple[str, str], tuple[int, float]] = {}
    unindexed = 0
    for left, right in sorted(union):
        if left not in index or right not in index:
            unindexed += 1
            continue
        forward = ranks(left).get(right, (math.inf, 0.0))
        backward = ranks(right).get(left, (math.inf, 0.0))
        rank = min(forward[0], backward[0])
        cosine = index.pair(left, right)
        measured[(left, right)] = (int(rank), float(cosine if cosine is not None else 0.0))
    block["unindexed_pairs"] = unindexed

    def recall(pairs: set[tuple[str, str]]) -> dict[str, Any]:
        scored = [measured[pair] for pair in pairs if pair in measured]
        if not scored:
            return {"n": 0}
        return {
            "n": len(scored),
            **{f"recall@{k}": round(sum(1 for rank, _c in scored if rank <= k) / len(scored), 4) for k in ks},
        }

    block["recall"] = {name: recall(pairs) for name, pairs in sorted(sources.items())}
    block["recall"]["all"] = recall(union)
    cosines = sorted((cosine for _rank, cosine in measured.values()), reverse=True)
    block["cosine_at_recall"] = {
        f"{int(target * 100)}%": round(cosines[max(0, math.ceil(target * len(cosines)) - 1)], 4)
        for target in RECALL_TARGETS
    } if cosines else {}
    block["cosine_at_recall_note"] = (
        "Recorded candidate blocking cutoffs (R4), keyed by this model and record kind; "
        "no code path reads them. T5 nominates by rank (top_k) only."
    )
    matrix = index.pairwise()
    upper = matrix[np.triu_indices(len(index), k=1)]
    block["noise_floor"] = _quantiles(upper)
    block["missed_at_top_k"] = [
        {"left": left, "right": right, "rank": rank, "cosine": round(cosine, 4)}
        for (left, right), (rank, cosine) in sorted(measured.items(), key=lambda kv: (-kv[1][0], kv[0]))
        if rank > top_k
    ][:MAX_LISTED]
    # What lexical misses: mutual nearest neighbours that no source lists.
    nearest = {record_id: index.nearest(index.vector(record_id), 1, exclude={record_id})
               for record_id in index.ids}
    mutual = sorted({
        _pair(record_id, top[0].record_id)
        for record_id, top in nearest.items()
        if top and nearest.get(top[0].record_id) and nearest[top[0].record_id][0].record_id == record_id
    })
    embedding_only = [pair for pair in mutual if pair not in union]
    block["mutual_nearest_pairs"] = len(mutual)
    block["embedding_only_mutual_nearest"] = {
        "count": len(embedding_only),
        "pairs": [
            {"left": left, "right": right, "cosine": round(float(index.pair(left, right) or 0.0), 4)}
            for left, right in sorted(embedding_only, key=lambda p: -(index.pair(*p) or 0.0))
        ][:MAX_LISTED],
        "note": "Unjudged nominations: the structuring model or the owner decides; nothing is merged.",
    }
    return block


def repair_shadow_block(loaded: LoadedVault, nominator: GraphNominator) -> dict[str, Any]:
    """The repair-equivalence shadow over the D2 re-run's comparable pairs."""

    payloads = [facet.model_dump(mode="json") for _id, facet in sorted(loaded.evidence_facets.items())]
    report = judge_facet_mints(payloads)
    annotated = annotate_mint_report(nominator, report, payloads, payloads)
    shadows = [shadow for record in annotated["candidates"] for shadow in record["repair_shadows"]]
    texts = sorted({str(t).strip() for p in payloads for t in p.get("instructional_repairs") or [] if str(t).strip()})
    vectors = nominator.vectors([repair_query(text) for text in texts])
    by_text = {text: vectors.get(query.content_hash) for text in texts
               if (query := repair_query(text)) is not None}
    noise = [
        score for i, left in enumerate(texts) for right in texts[i + 1:]
        if (score := raw_cosine(by_text.get(left), by_text.get(right))) is not None
    ]
    noise_floor = _quantiles(noise)
    distinct = [s for s in shadows if s["text_distinct_repair"]]
    measured = [s["min_best_cosine"] for s in distinct if s["min_best_cosine"] is not None]
    p95 = (noise_floor or {}).get("p95")
    return {
        "d2_pairs_with_repairs": len(shadows),
        "text_says_distinct_repair": len(distinct),
        "text_says_same_repair_class": len(shadows) - len(distinct),
        "distinct_with_measured_shadow": len(measured),
        "min_best_cosine_of_text_distinct": _quantiles(measured),
        "repair_noise_floor_raw_cosine": noise_floor,
        "text_distinct_but_above_noise_p95": (
            sum(1 for value in measured if value >= p95) if p95 is not None else None
        ),
        "note": (
            "Shadow only: distinct_repair still decides. A text-distinct pair whose every "
            "exclusive repair has a neighbour repair above the repair noise floor's p95 is "
            "the MINT bias the spec names (§8)."
        ),
    }


def ingest_records(loaded: LoadedVault) -> dict[str, Any]:
    """What ingest-time nominations did, from synthesis-run records."""

    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    statuses: Counter[str] = Counter()
    merges = 0
    nominated = 0
    if not sqlite_path.exists():
        return {"runs": 0}
    try:
        with closing(connect(sqlite_path, read_only=True)) as connection:
            rows = connection.execute(
                "SELECT mode,coverage_decisions_json,actual_usage_json FROM synthesis_runs "
                "WHERE status='completed'"
            ).fetchall()
    except sqlite3.Error:
        return {"runs": 0}
    runs = 0
    for _mode, coverage_json, usage_json in rows:
        coverage = json.loads(coverage_json or "{}") if coverage_json else {}
        nomination = coverage.get("graph_nomination") if isinstance(coverage, dict) else None
        if not isinstance(nomination, dict):
            continue
        runs += 1
        statuses[str((nomination.get("summary") or {}).get("status") or "unknown")] += 1
        usage = json.loads(usage_json or "{}") if usage_json else {}
        if isinstance(usage, dict):
            merges += int(usage.get("registry_merges") or 0)
            nominated += int(usage.get("registry_nominated_candidates") or 0)
    return {
        "runs": runs,
        "by_status": dict(sorted(statuses.items())),
        "structuring_candidates_with_registry_nominations": nominated,
        "structuring_registry_merges_applied": merges,
    }


def nomination_report(
    loaded: LoadedVault,
    *,
    caps: SpendCaps,
    dry_run: bool = False,
    stored_only: bool = False,
    batch_size: int = 32,
    price_per_million: float | None = None,
    cancelled: Callable[[], bool] | None = None,
    client_factory: Callable[[], EmbeddingClient] | None = None,
) -> dict[str, Any]:
    """Plan (``dry_run``), backfill what the report reads, then report.

    ``stored_only`` skips the backfill and reports from whatever vectors exist
    (zero model calls). Rebuild never calls this.
    """

    config = loaded.config
    truth = ground_truth(loaded)
    confirmed, ledger_counts = _ledger(loaded)
    for kind, pairs in confirmed.items():
        if pairs:
            truth[kind]["ledger_same"] = pairs
    report: dict[str, Any] = {
        "version": REPORT_VERSION,
        "nomination_version": NOMINATION_VERSION,
        "status": "dry_run" if dry_run else "pending",
        "dry_run": dry_run,
        "model_id": config.embedding.model,
        "top_k": config.graph_nomination.top_k,
        "graph_nomination_enabled": config.graph_nomination.enabled,
        "embedding_enabled": config.embedding.enabled,
        "ground_truth": {
            kind: {source: len(pairs) for source, pairs in sorted(sources.items())}
            for kind, sources in truth.items()
        },
        "ledger": ledger_counts,
    }
    if stored_only:
        report["backfill"] = {"status": "skipped", "reason": "--stored-only"}
    else:
        report["backfill"] = backfill_embeddings(
            loaded, caps=caps, dry_run=dry_run, recipes=REPORT_RECIPES,
            batch_size=batch_size, price_per_million=price_per_million,
            cancelled=cancelled, client_factory=client_factory,
        )
    if dry_run:
        return report
    backfill_status = report["backfill"]["status"]
    nominator = GraphNominator(
        loaded, VaultPaths(loaded.root, config).sqlite_path, allow_new_text=False,
    )
    top_k = config.graph_nomination.top_k
    report["facets"] = recall_block(
        nominator.index(FACET_RECIPE), nominator.summary()["indexes"].get(FACET_RECIPE, "unknown"),
        truth["facet"], top_k=top_k,
    )
    report["concepts"] = recall_block(
        nominator.index(CONCEPT_RECIPE), nominator.summary()["indexes"].get(CONCEPT_RECIPE, "unknown"),
        truth["concept"], top_k=top_k,
    )
    report["repair_shadow"] = repair_shadow_block(loaded, nominator)
    report["ingest"] = ingest_records(loaded)
    report["nominator"] = nominator.summary()
    report["status"] = "complete" if backfill_status in {"complete", "skipped"} else backfill_status
    return report
