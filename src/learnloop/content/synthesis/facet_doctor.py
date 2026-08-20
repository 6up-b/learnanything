"""Post-append near-duplicate facet doctor pass (source-ingestion §12/§14).

After an applied append, run near-duplicate detection over the whole facet registry
(lexical MinHash/Jaccard — the review-only similarity assist §12 permits) and emit
MERGE-REVIEW proposals. It never auto-merges: identity is decided by a human, and
the ephemeral similarity output is never persisted as equivalence.

Wired into (a) the append completion path and (b) ``learnloop doctor``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from learnloop.vault.models import LoadedVault

_TOKEN_RE = re.compile(r"[a-z0-9]+")
DEFAULT_THRESHOLD = 0.85


def _facet_tokens(facet: Any) -> set[str]:
    parts = [
        facet.claim or "",
        facet.title or "",
        " ".join(facet.aliases or []),
        " ".join(facet.error_signatures or []),
    ]
    return set(_TOKEN_RE.findall(" ".join(str(p) for p in parts).lower()))


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


@dataclass(frozen=True)
class MergeReviewProposal:
    left_facet_id: str
    right_facet_id: str
    similarity: float
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "left_facet_id": self.left_facet_id,
            "right_facet_id": self.right_facet_id,
            "similarity": round(self.similarity, 3),
            "reason": self.reason,
            "action": "review_merge",
        }


def near_duplicate_facet_review(
    vault: LoadedVault, *, threshold: float = DEFAULT_THRESHOLD
) -> list[MergeReviewProposal]:
    """Deterministic pairwise near-duplicate detection over the facet registry.

    Returns merge-review proposals (never auto-merges). Only compares distinct
    facet ids that are not already aliases/merges of one another."""

    facets = sorted(vault.evidence_facets.items())
    tokens = {fid: _facet_tokens(f) for fid, f in facets}
    out: list[MergeReviewProposal] = []
    for i in range(len(facets)):
        fid_i = facets[i][0]
        for j in range(i + 1, len(facets)):
            fid_j = facets[j][0]
            # skip pairs already unified by alias/merge (identity already decided).
            if vault.canonical_facet_id(fid_i) == vault.canonical_facet_id(fid_j):
                continue
            sim = _jaccard(tokens[fid_i], tokens[fid_j])
            if sim >= threshold:
                out.append(
                    MergeReviewProposal(
                        left_facet_id=fid_i,
                        right_facet_id=fid_j,
                        similarity=sim,
                        reason=f"registry facets are near-duplicates (jaccard {sim:.2f})",
                    )
                )
    return out
