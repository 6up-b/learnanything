"""Shadow contamination candidates: the lexical floor, the symbolic check and stored vectors.

Nothing here calls a model, writes data, or changes what is served. Each
detector starts from the live lexical floor, unchanged, and widens the set of
(subject, target) pairs a judge will see:

* **exam_leakage** — every generated practice item against every held-out exam
  span: the floor's shingle/numeric findings, plus the top-k spans nearest the
  item's stored ``item/stem`` and ``item/expected_answer`` vectors;
* **tutor_answer_leak** — every answered tutor turn bound to an item against
  that item's expected answer: the floor (its persisted leak flag, or a live
  reveal debit that alone primes the next attempt), the symbolic check, plus a
  shortlist when the item's own expected answer ranks in the top k for the
  stored answer vector among all expected answers;
* **reader_reveal** — every reader answer against every live assessment
  reserve: the floor's hash/fingerprint/bigram rule, the symbolic check on the
  reserve's answer, plus the top-k reserves nearest the stored answer vector.

Shortlisting is by rank only (R4): no cosine cutoff is set here, and no score
decides anything. An index without the complete current set of vectors, or a
subject without its vector, degrades to the lexical floor and the symbolic
check, and the scan says so.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
import sqlite3
from typing import Any

import numpy as np

from learnloop.attempts.attempts import AUTO_PRIME_REVEAL_THRESHOLD
from learnloop.content.authoring.practice_leakage import (
    held_out_spans, inventory_for_texts, screen_practice_payload,
)
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import EmbeddingMatch, get_vector, retrieve
from learnloop.ops.contamination.recipes import (
    CONTAMINATION_RECIPES, answered_question_events, expected_answer_text,
)
from learnloop.ops.contamination.symbolic import SymbolicResult, symbolic_check
from learnloop.reader.reader_dialogue import lexical_reserve_reveal, surface_statement_text
from learnloop.tutor.tutor_qa import answer_leak_overlap
from learnloop.vault.models import LoadedVault, PracticeItem


DETECTORS = ("exam_leakage", "tutor_answer_leak", "reader_reveal")
TASK_FOR_DETECTOR = {"exam_leakage": "leak", "tutor_answer_leak": "reveal", "reader_reveal": "reveal"}
POSITIVE_VERDICT = {"leak": "leak", "reveal": "reveal"}
#: Practice a model produced: AI authoring proposals and canonical extraction.
GENERATED_ORIGINS = frozenset({"codex_proposal", "canonical_extract"})
TASK_PREFIX = "retrieval-document"


@dataclass
class Candidate:
    detector: str
    left_kind: str
    left_id: str
    right_kind: str
    right_id: str
    context: dict[str, Any]
    subject_text: str
    target_text: str
    reasons: set[str] = field(default_factory=set)
    floor: bool = False
    floor_score: float | None = None
    symbolic: SymbolicResult | None = None
    embedding_score: float | None = None
    embedding_rank: int | None = None
    embedding_query: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def task(self) -> str:
        return TASK_FOR_DETECTOR[self.detector]

    @property
    def question(self) -> tuple[str, str, str, str, str]:
        return (self.task, self.left_kind, self.left_id, self.right_kind, self.right_id)

    def note_embedding(self, *, query: str, score: float, rank: int) -> None:
        if self.embedding_rank is None or rank < self.embedding_rank:
            self.embedding_score, self.embedding_rank, self.embedding_query = score, rank, query

    def signals(self) -> dict[str, Any]:
        return {
            "reasons": sorted(self.reasons),
            "floor": self.floor,
            "floor_score": self.floor_score,
            "symbolic": self.symbolic.as_dict() if self.symbolic else None,
            "embedding": None if self.embedding_rank is None else {
                "score": round(self.embedding_score or 0.0, 6),
                "rank": self.embedding_rank, "query": self.embedding_query,
            },
            **self.extra,
        }


@dataclass
class DetectorScan:
    detector: str
    status: str
    subjects: int
    targets: int
    floor_subjects: int
    embedding: dict[str, Any]
    candidates: list[Candidate]
    symbolic: dict[str, int] | None = None


class StoredVectors:
    """Read-only vectors of one model and prefix. It never calls a provider."""

    def __init__(self, loaded: LoadedVault, sqlite_path: Path):
        self.loaded = loaded
        self.model_id = loaded.config.embedding.model
        self._connection: sqlite3.Connection | None = None
        self.reason: str | None = None
        if not sqlite_path.exists():
            self.reason = "no_database"
            return
        connection = connect(sqlite_path, read_only=True)
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='embedding_vectors'"
        ).fetchone() is None:
            connection.close()
            self.reason = "no_vector_table"
            return
        self._connection = connection

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def manifest(self, recipe: str) -> dict[str, str]:
        return {record.record_id: record.content_hash
                for record in CONTAMINATION_RECIPES[recipe].records(self.loaded)}

    def stored(self, recipe: str, manifest: Mapping[str, str]) -> set[str]:
        """Record ids whose CURRENT content hash has a vector for this model."""

        if self._connection is None or not manifest:
            return set()
        definition = CONTAMINATION_RECIPES[recipe]
        rows = self._connection.execute(
            "SELECT record_id, content_hash FROM embedding_vectors "
            "WHERE record_kind=? AND field=? AND model_id=? AND task_prefix=?",
            (definition.record_kind, definition.field, self.model_id, TASK_PREFIX),
        ).fetchall()
        return {str(row[0]) for row in rows if manifest.get(str(row[0])) == row[1]}

    def vector(self, recipe: str, record_id: str, content_hash: str | None) -> np.ndarray | None:
        if self._connection is None or content_hash is None:
            return None
        definition = CONTAMINATION_RECIPES[recipe]
        return get_vector(
            self._connection, record_kind=definition.record_kind, record_id=record_id,
            field=definition.field, content_hash=content_hash, model_id=self.model_id,
            task_prefix=TASK_PREFIX,
        )

    def index(self, recipe: str) -> VectorIndex:
        manifest = self.manifest(recipe)
        stored = self.stored(recipe, manifest)
        missing = len(set(manifest) - stored)
        if self._connection is None:
            status = self.reason or "unavailable"
        elif not manifest:
            status = "empty"
        elif missing:
            status = "incomplete"
        else:
            status = "complete"
        return VectorIndex(self, recipe, manifest, status, missing)


@dataclass
class VectorIndex:
    vectors: StoredVectors
    recipe: str
    manifest: dict[str, str]
    status: str
    missing: int

    @property
    def usable(self) -> bool:
        return self.status == "complete"

    def ranked(self, query: np.ndarray, *, limit: int) -> list[EmbeddingMatch]:
        """Mean-centred cosine over the complete current index, best first."""

        definition = CONTAMINATION_RECIPES[self.recipe]
        assert self.vectors._connection is not None and self.usable
        return retrieve(
            self.vectors._connection, record_kind=definition.record_kind, field=definition.field,
            model_id=self.vectors.model_id, task_prefix=TASK_PREFIX, query=query,
            expected_records=self.manifest, limit=limit,
        )

    def describe(self) -> dict[str, Any]:
        return {"recipe": self.recipe, "status": self.status,
                "records": len(self.manifest), "missing": self.missing}


def _embedding_block(index: VectorIndex, queries: Iterable[str], with_vectors: int, without: int) -> dict[str, Any]:
    used = index.usable and with_vectors > 0
    return {
        "status": "used" if used else "unavailable",
        "reason": None if used else (
            f"index {index.recipe} is {index.status}" if not index.usable
            else "no subject has a stored query vector"
        ),
        "model_id": index.vectors.model_id,
        "index": index.describe(),
        "query_recipes": list(queries),
        "subjects_with_vectors": with_vectors,
        "subjects_without_vectors": without,
    }


def _excerpt_rubric(item: PracticeItem) -> list[str]:
    rubric = item.grading_rubric
    return [criterion.description for criterion in rubric.criteria] if rubric is not None else []


def scan_exam_leakage(loaded: LoadedVault, repository: Repository, vectors: StoredVectors, *, top_k: int) -> DetectorScan:
    items = sorted(
        (item for item in loaded.practice_items.values()
         if item.status != "retired" and item.provenance.origin in GENERATED_ORIGINS),
        key=lambda item: item.id,
    )
    spans = held_out_spans(loaded, repository)
    span_by_key = {span.key: span for span in spans}
    index = vectors.index("exam_span/text")
    queries = ("item/stem", "item/expected_answer")
    if not spans or not items:
        return DetectorScan(
            "exam_leakage", "no_targets" if not spans else "no_subjects", len(items), len(spans), 0,
            _embedding_block(index, queries, 0, len(items)), [],
        )
    candidates: dict[tuple[str, str], Candidate] = {}

    def candidate(item: PracticeItem, span_key: str) -> Candidate:
        key = (item.id, span_key)
        if key not in candidates:
            span = span_by_key[span_key]
            candidates[key] = Candidate(
                "exam_leakage", "practice_item", item.id, "source_span", span_key,
                context={
                    "practice_item": {
                        "prompt": item.prompt,
                        "expected_answer": expected_answer_text(item),
                        "rubric_criteria": _excerpt_rubric(item),
                    },
                    "held_out_exam_span": span.text,
                },
                subject_text=item.prompt, target_text=span.text,
                extra={"origin": item.provenance.origin},
            )
        return candidates[key]

    union = inventory_for_texts([span.text for span in spans])
    per_span = {}
    floor_subjects = 0
    for item in items:
        payload = item.model_dump(mode="json")
        if not screen_practice_payload(payload, union):
            continue
        floor_subjects += 1
        for span in spans:
            inventory = per_span.setdefault(span.key, inventory_for_texts([span.text]))
            findings = screen_practice_payload(payload, inventory)
            if findings:
                hit = candidate(item, span.key)
                hit.reasons.add("lexical")
                hit.floor, hit.floor_score = True, float(len(findings))

    with_vectors = 0
    if index.usable:
        manifests = {recipe: vectors.manifest(recipe) for recipe in queries}
        for item in items:
            found = False
            for recipe in queries:
                query = vectors.vector(recipe, item.id, manifests[recipe].get(item.id))
                if query is None:
                    continue
                found = True
                for rank, match in enumerate(index.ranked(query, limit=top_k), start=1):
                    if match.record_id not in span_by_key:
                        continue  # changed between the index manifest and this scan
                    hit = candidate(item, match.record_id)
                    hit.reasons.add("embedding")
                    hit.note_embedding(query=recipe, score=match.score, rank=rank)
            with_vectors += found
    return DetectorScan(
        "exam_leakage", "scanned", len(items), len(spans), floor_subjects,
        _embedding_block(index, queries, with_vectors, len(items) - with_vectors),
        [candidates[key] for key in sorted(candidates)],
    )


def _next_attempt(repository: Repository, item_id: str, after: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT id, created_at, primed FROM practice_attempts "
            "WHERE practice_item_id=? AND created_at > ? ORDER BY created_at, id LIMIT 1",
            (item_id, after),
        ).fetchone()
    return None if row is None else {"id": row[0], "created_at": row[1], "primed": bool(row[2])}


def scan_tutor_answer_leak(loaded: LoadedVault, repository: Repository, vectors: StoredVectors, *, top_k: int) -> DetectorScan:
    events = [
        event for event in answered_question_events(repository)
        if event.get("practice_item_id") in loaded.practice_items
    ]
    index = vectors.index("item/expected_answer")
    queries = ("question_event/answer",)
    answer_manifest = vectors.manifest("question_event/answer") if index.usable else {}
    candidates: list[Candidate] = []
    floor_subjects = with_vectors = 0
    symbolic_counts = {"math_pairs": 0, "matches": 0, "verifier_decisions": 0}
    for event in events:
        item = loaded.practice_items[event["practice_item_id"]]
        answer = str(event["answer_md"])
        # A turn from before the reveal ledger (migration 154) has no persisted
        # overlap and was never debited: its live floor was the 0.8 flag alone.
        debited = event.get("leak_overlap")
        overlap = debited if debited is not None else answer_leak_overlap(answer, item.expected_answer)
        debited = float(debited or 0.0)
        hit = Candidate(
            "tutor_answer_leak", "question_event", str(event["id"]), "practice_item", item.id,
            context={
                "practice_item": {"prompt": item.prompt, "expected_answer": expected_answer_text(item)},
                "tutor_answer": answer,
            },
            subject_text=answer, target_text=expected_answer_text(item),
            # The live floor protects cold evidence two ways: the 0.8 leak flag,
            # and the reveal-ledger debit, which alone primes the next attempt
            # at AUTO_PRIME_REVEAL_THRESHOLD. Either counts as caught.
            floor=bool(event.get("leak_suspected")) or debited >= AUTO_PRIME_REVEAL_THRESHOLD,
            floor_score=float(overlap),
            extra={"context": event.get("context"), "asked_at": event.get("created_at"),
                   "leak_suspected": bool(event.get("leak_suspected")),
                   "live_reveal_amount": debited},
        )
        floor_subjects += hit.floor
        # Today's lexical rule shortlists even a pre-ledger turn it would flag;
        # ``floor`` alone says whether the live path actually protected it.
        if hit.floor or overlap >= AUTO_PRIME_REVEAL_THRESHOLD:
            hit.reasons.add("lexical")
        hit.symbolic = symbolic_check(answer, item.expected_answer)
        if hit.symbolic.status != "not_math":
            symbolic_counts["math_pairs"] += 1
        if hit.symbolic.status == "match":
            symbolic_counts["matches"] += 1
            symbolic_counts["verifier_decisions"] += hit.symbolic.decides
            hit.reasons.add("symbolic")
        if index.usable:
            query = vectors.vector("question_event/answer", hit.left_id, answer_manifest.get(hit.left_id))
            if query is not None:
                with_vectors += 1
                ranked = index.ranked(query, limit=len(index.manifest))
                for rank, match in enumerate(ranked, start=1):
                    if match.record_id == item.id:
                        hit.note_embedding(query="question_event/answer", score=match.score, rank=rank)
                        if rank <= top_k:
                            hit.reasons.add("embedding")
                        break
        if hit.reasons:
            hit.extra["next_attempt"] = _next_attempt(repository, item.id, str(event.get("created_at") or ""))
            candidates.append(hit)
    return DetectorScan(
        "tutor_answer_leak", "scanned" if events else "no_subjects", len(events), len(events), floor_subjects,
        _embedding_block(index, queries, with_vectors, len(events) - with_vectors),
        candidates, symbolic_counts,
    )


def _reserved_at(repository: Repository) -> dict[str, str]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT surface_id, reserved_at FROM activity_surface_reservations "
            "WHERE status='reserved' AND purpose='assessment'"
        ).fetchall()
    return {str(row[0]): str(row[1]) for row in rows}


def scan_reader_reveal(loaded: LoadedVault, repository: Repository, vectors: StoredVectors, *, top_k: int) -> DetectorScan:
    events = [event for event in answered_question_events(repository) if event.get("context") == "reader"]
    reserves = sorted(repository.reserved_assessment_surfaces(), key=lambda row: str(row["id"]))
    index = vectors.index("surface/statement")
    queries = ("question_event/answer",)
    if not reserves or not events:
        return DetectorScan(
            "reader_reveal", "no_targets" if not reserves else "no_subjects", len(events), len(reserves), 0,
            _embedding_block(index, queries, 0, len(events)), [], None,
        )
    reserved_at = _reserved_at(repository)
    by_id = {str(surface["id"]): surface for surface in reserves}
    candidates: dict[tuple[str, str], Candidate] = {}
    symbolic_counts = {"math_pairs": 0, "matches": 0, "verifier_decisions": 0}

    def candidate(event: Mapping[str, Any], surface_id: str) -> Candidate:
        key = (str(event["id"]), surface_id)
        if key not in candidates:
            surface = by_id[surface_id]
            statement = surface_statement_text(surface)
            candidates[key] = Candidate(
                "reader_reveal", "question_event", str(event["id"]), "activity_surface", surface_id,
                context={"reserved_assessment_question": statement, "reader_answer": str(event["answer_md"])},
                subject_text=str(event["answer_md"]), target_text=statement,
                extra={"asked_at": event.get("created_at"), "reserved_at": reserved_at.get(surface_id)},
            )
        return candidates[key]

    floor_subjects = with_vectors = 0
    answer_manifest = vectors.manifest("question_event/answer") if index.usable else {}
    for event in events:
        answer = str(event["answer_md"])
        citations = list((event.get("source_context") or {}).get("citations") or [])
        flagged = False
        for surface_id, surface in by_id.items():
            hit_floor, overlap = lexical_reserve_reveal(answer, surface, citations=citations)
            expected = (surface.get("surface") or {}).get("expected_answer")
            result = symbolic_check(answer, expected) if expected is not None else None
            if result is not None and result.status != "not_math":
                symbolic_counts["math_pairs"] += 1
            if hit_floor or (result is not None and result.status == "match"):
                hit = candidate(event, surface_id)
                hit.floor, hit.floor_score = hit_floor, overlap
                if hit_floor:
                    hit.reasons.add("lexical")
                    flagged = True
                if result is not None and result.status == "match":
                    hit.symbolic = result
                    hit.reasons.add("symbolic")
                    symbolic_counts["matches"] += 1
                    symbolic_counts["verifier_decisions"] += result.decides
        floor_subjects += flagged
        if index.usable:
            query = vectors.vector("question_event/answer", str(event["id"]), answer_manifest.get(str(event["id"])))
            if query is None:
                continue
            with_vectors += 1
            for rank, match in enumerate(index.ranked(query, limit=top_k), start=1):
                if match.record_id not in by_id:
                    continue  # a reserve released between the index manifest and this scan
                hit = candidate(event, match.record_id)
                hit.reasons.add("embedding")
                hit.note_embedding(query="question_event/answer", score=match.score, rank=rank)
                if hit.floor_score is None:
                    hit.floor_score = lexical_reserve_reveal(answer, by_id[match.record_id], citations=citations)[1]
    return DetectorScan(
        "reader_reveal", "scanned", len(events), len(reserves), floor_subjects,
        _embedding_block(index, queries, with_vectors, len(events) - with_vectors),
        [candidates[key] for key in sorted(candidates)], symbolic_counts,
    )


SCANNERS = {
    "exam_leakage": scan_exam_leakage,
    "tutor_answer_leak": scan_tutor_answer_leak,
    "reader_reveal": scan_reader_reveal,
}
