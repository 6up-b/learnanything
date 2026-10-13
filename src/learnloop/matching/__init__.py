"""Embeddings shortlist, judges decide: the one "same or different?" step.

Slice 2 R4 and §4: every track that asks "is this the same thing?" registers
a :class:`~learnloop.matching.kinds.MatchKind`, shortlists with stored
vectors (top-k plus a benchmark-set cutoff), lets an LLM judge decide every
shortlisted pair, and appends each verdict to ``judgment_ledger``.
:mod:`~learnloop.matching.union` turns verdicts into groups with the
no-chaining refusal. Below the domains: it imports only ``ai`` and ``db``.
"""

from learnloop.matching.judge import JudgedPair, SameOrDifferent, judge_pairs, pair_input_hash, pair_prompt
from learnloop.matching.kinds import EmbeddingIdentity, MatchKind, Subject, VERDICTS
from learnloop.matching.shortlist import CandidatePair, Shortlist, shortlist_pairs
from learnloop.matching.union import Refusal, UnionEdge, UnionResult, union_with_refusals

__all__ = [
    "CandidatePair",
    "EmbeddingIdentity",
    "JudgedPair",
    "MatchKind",
    "Refusal",
    "SameOrDifferent",
    "Shortlist",
    "Subject",
    "UnionEdge",
    "UnionResult",
    "VERDICTS",
    "judge_pairs",
    "pair_input_hash",
    "pair_prompt",
    "shortlist_pairs",
    "union_with_refusals",
]
