"""Candidate facet harvesting (knowledge-model §3.3).

Gathers facet candidates from existing vault/DB signals — unit inventories (when
present), LO summaries, rubric criteria, existing registry entries, fatal-error
conditions, and misconception statements — and proposes REVIEW pairs for
lexically similar candidates. Similarity is ephemeral and review-only: a
lexical/MinHash Jaccard estimate never merges, and no similarity artifact is
persisted as identity. Output is deterministic JSON.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field

from learnloop.ids import snake_case
from learnloop.vault.models import LoadedVault

_TOKEN = re.compile(r"[a-z0-9]+")
# A candidate pair at or above this Jaccard estimate is proposed for review.
REVIEW_THRESHOLD = 0.6
_MINHASH_PERMUTATIONS = 64


@dataclass(frozen=True)
class FacetCandidate:
    candidate_id: str
    source_kind: str  # unit_inventory | lo_summary | rubric_criterion | registry | fatal_error | misconception
    text: str
    suggested_facet_id: str
    refs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReviewPair:
    left: str
    right: str
    similarity: float
    reason: str = "lexical_similarity_review_only"


def _tokens(text: str) -> set[str]:
    return set(_TOKEN.findall(text.lower()))


def _suggest_id(text: str) -> str:
    slug = snake_case(text)[:60].strip("_")
    return f"facet_{slug}" if slug else "facet_unnamed"


def _minhash_signature(tokens: set[str]) -> tuple[int, ...]:
    """Deterministic MinHash signature of a token set (no external deps)."""

    if not tokens:
        return tuple(0 for _ in range(_MINHASH_PERMUTATIONS))
    # Stable per-token hash (builtin hash() is process-salted; MinHash must be
    # deterministic across runs).
    hashed = [
        int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:4], "big")
        for token in tokens
    ]
    signature: list[int] = []
    for perm in range(_MINHASH_PERMUTATIONS):
        # Universal-hashing style permutation; deterministic per perm index.
        a = 2 * perm + 1
        b = perm * 2654435761 & 0xFFFFFFFF
        signature.append(min(((a * value + b) & 0xFFFFFFFF) for value in hashed))
    return tuple(signature)


def _minhash_similarity(left: tuple[int, ...], right: tuple[int, ...]) -> float:
    if not left or not right:
        return 0.0
    matches = sum(1 for a, b in zip(left, right) if a == b)
    return matches / len(left)


def _harvest(vault: LoadedVault, repository=None) -> list[FacetCandidate]:
    candidates: list[FacetCandidate] = []

    def add(source_kind: str, text: str, refs: list[str]) -> None:
        text = (text or "").strip()
        if not text:
            return
        candidates.append(
            FacetCandidate(
                candidate_id=f"{source_kind}:{len(candidates)}",
                source_kind=source_kind,
                text=text,
                suggested_facet_id=_suggest_id(text),
                refs=refs,
            )
        )

    # Existing registry entries: their claim (v2) or title carries the atom.
    for facet in vault.evidence_facets.values():
        add("registry", facet.claim or facet.title or facet.id, [facet.id])

    # LO summaries.
    for lo in sorted(vault.learning_objects.values(), key=lambda item: item.id):
        add("lo_summary", lo.summary, [lo.id])

    # Rubric criteria (default rubrics + item rubrics).
    for mode, rubric in sorted(vault.default_rubrics.items()):
        for criterion in rubric.criteria:
            add("rubric_criterion", criterion.description, [f"rubric:{mode}", criterion.id])
    for item in sorted(vault.practice_items.values(), key=lambda pi: pi.id):
        if item.grading_rubric is None:
            continue
        for criterion in item.grading_rubric.criteria:
            add("rubric_criterion", criterion.description, [item.id, criterion.id])
        # Fatal-error conditions.
        for fatal in item.grading_rubric.fatal_errors:
            add("fatal_error", fatal.description, [item.id, fatal.id])

    # Misconception statements (from the DB registry, when available).
    if repository is not None:
        seen_misconceptions: set[str] = set()
        for lo in sorted(vault.learning_objects.values(), key=lambda item: item.id):
            for record in repository.misconceptions_for_learning_object(lo.id):
                if record.id in seen_misconceptions:
                    continue
                seen_misconceptions.add(record.id)
                add("misconception", record.statement, [record.id])

    # Unit inventories (source-ingestion): none exist at KM1; harvested when the
    # inventory table lands (ING M4). Guarded so this stays forward-compatible.
    if repository is not None and hasattr(repository, "source_unit_inventory_claims"):
        for claim in repository.source_unit_inventory_claims():  # pragma: no cover - ING M4
            add("unit_inventory", claim.get("text", ""), [str(claim.get("unit_id", ""))])

    return candidates


def _review_pairs(candidates: list[FacetCandidate]) -> list[ReviewPair]:
    signatures = [(candidate, _minhash_signature(_tokens(candidate.text))) for candidate in candidates]
    pairs: list[ReviewPair] = []
    for index, (left, left_sig) in enumerate(signatures):
        for right, right_sig in signatures[index + 1 :]:
            if left.suggested_facet_id == right.suggested_facet_id and left.source_kind == right.source_kind:
                continue
            similarity = _minhash_similarity(left_sig, right_sig)
            if similarity >= REVIEW_THRESHOLD:
                pairs.append(
                    ReviewPair(
                        left=left.candidate_id,
                        right=right.candidate_id,
                        similarity=round(similarity, 4),
                    )
                )
    pairs.sort(key=lambda pair: (-pair.similarity, pair.left, pair.right))
    return pairs


def harvest_facet_candidates(vault: LoadedVault, repository=None) -> dict[str, object]:
    """Harvest candidates and lexical review pairs (§3.3). Deterministic JSON."""

    candidates = _harvest(vault, repository)
    pairs = _review_pairs(candidates)
    return {
        "version": 1,
        "candidates": [asdict(candidate) for candidate in candidates],
        "review_pairs": [asdict(pair) for pair in pairs],
        "notes": (
            "Similarity is review-only and ephemeral; no pair is a merge and no "
            "similarity artifact is persisted as identity (knowledge-model §3.3)."
        ),
    }
