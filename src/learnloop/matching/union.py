"""Deterministic union with the no-chaining refusal (Slice 2 §3.4).

Nodes are opaque ids (T1: normalized-statement classes). Edges are verdicts
between two nodes from a judge with an authority tier. The effective verdict
on a pair is the highest-authority tier's latest non-``unsure`` verdict; every
effective ``same`` is then applied in adjudication order (oldest first), and a
union is REFUSED when it would put two nodes with an effective ``different``
verdict at equal or higher authority into one component. The refused pair is
reported so it can be logged for review. This is what keeps A~B, B~C from
silently merging A with C against a judge.

Pure: no I/O, no model, no score. The caller supplies node order (the oldest
node roots its component) so the result is a function of the inputs alone.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class UnionEdge:
    left: str
    right: str
    verdict: str  # same | different | unsure
    authority: int
    judge: str
    source: str
    ref: str
    occurred_at: str = ""
    #: Optional finer-grained subjects behind the node pair (e.g. episodes).
    left_ref: str | None = None
    right_ref: str | None = None
    detail: Mapping[str, Any] = field(default_factory=dict)

    def pair(self) -> frozenset[str]:
        return frozenset((self.left, self.right))

    def order(self) -> tuple[str, str]:
        return (self.occurred_at, self.ref)


@dataclass(frozen=True)
class Refusal:
    edge: UnionEdge
    blocking: UnionEdge


@dataclass
class UnionResult:
    #: node -> its component's root node.
    root_of: dict[str, str]
    #: non-root node -> the edge that first joined it to a larger component.
    joined_by: dict[str, UnionEdge]
    refused: list[Refusal]
    #: ``different`` verdicts between two edges of one node (same class).
    self_conflicts: list[UnionEdge]
    #: the effective verdict per node pair (``same``/``different`` only).
    effective: dict[frozenset[str], UnionEdge]

    def components(self) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}
        for node, root in self.root_of.items():
            groups.setdefault(root, []).append(node)
        return {root: sorted(nodes) for root, nodes in groups.items()}


def effective_verdicts(edges: Iterable[UnionEdge]) -> tuple[dict[frozenset[str], UnionEdge], list[UnionEdge]]:
    """Highest authority wins; latest within a tier; ``unsure`` never counts."""

    best: dict[frozenset[str], UnionEdge] = {}
    conflicts: list[UnionEdge] = []
    for edge in sorted(edges, key=UnionEdge.order):
        if edge.verdict not in ("same", "different"):
            continue
        if edge.left == edge.right:
            if edge.verdict == "different":
                conflicts.append(edge)
            continue
        key = edge.pair()
        current = best.get(key)
        if current is None or edge.authority > current.authority or (
            edge.authority == current.authority and edge.order() >= current.order()
        ):
            best[key] = edge
    return best, conflicts


def union_with_refusals(
    nodes: Iterable[str],
    edges: Iterable[UnionEdge],
    *,
    order: Mapping[str, Hashable] | None = None,
) -> UnionResult:
    node_list = sorted(set(nodes), key=lambda node: (order.get(node, node) if order else node, node))
    rank = {node: index for index, node in enumerate(node_list)}
    parent = {node: node for node in node_list}
    members: dict[str, set[str]] = {node: {node} for node in node_list}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    effective, conflicts = effective_verdicts(edges)
    different = [edge for edge in effective.values() if edge.verdict == "different"]
    joined_by: dict[str, UnionEdge] = {}
    refused: list[Refusal] = []
    for edge in sorted((edge for edge in effective.values() if edge.verdict == "same"), key=UnionEdge.order):
        if edge.left not in parent or edge.right not in parent:
            continue
        left_root, right_root = find(edge.left), find(edge.right)
        if left_root == right_root:
            continue
        blocking = next(
            (
                other
                for other in sorted(different, key=UnionEdge.order)
                if other.authority >= edge.authority
                and other.left in parent
                and other.right in parent
                and {find(other.left), find(other.right)} == {left_root, right_root}
            ),
            None,
        )
        if blocking is not None:
            refused.append(Refusal(edge=edge, blocking=blocking))
            continue
        keep, absorb = sorted((left_root, right_root), key=lambda node: rank[node])
        # The absorbed component's root is the only node without a join edge
        # yet; every other member keeps the edge that first joined it.
        joined_by[absorb] = edge
        parent[absorb] = keep
        members[keep] |= members.pop(absorb)
    root_of = {node: find(node) for node in node_list}
    return UnionResult(
        root_of=root_of,
        joined_by=joined_by,
        refused=refused,
        self_conflicts=conflicts,
        effective=effective,
    )


__all__ = ["Refusal", "UnionEdge", "UnionResult", "effective_verdicts", "union_with_refusals"]
