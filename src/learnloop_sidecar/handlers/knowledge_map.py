from __future__ import annotations

from collections import deque
from math import sqrt
from typing import Any

from learnloop.services.mastery import display_mastery, sigmoid
from learnloop.services.probes import resolve_item_irt
from learnloop.services.recall_coverage import predicted_correctness
from learnloop.services.scheduler import build_due_queue
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import versioned
from learnloop_sidecar.registry import method

# Distance blend for the 2D knowledge map. Facet similarity dominates (items
# that exercise the same evidence facets should sit together) while the concept
# graph pulls structurally-related material into neighborhoods even when facet
# vocabularies barely overlap. Deliberately constants, not config: the map is a
# visualization, and a stable geometry across sessions matters more than
# tunability.
_FACET_BLEND = 0.6
_GRAPH_BLEND = 0.4

# Concept-graph relations that carry "these live near each other" semantics.
# confusable_with is excluded: confusables are adversarial neighbors, and
# pulling them together would flatter exactly the distinction the learner
# struggles with.
_GRAPH_RELATIONS = {"prerequisite", "related", "part_of"}

_TOP_FACETS = 3
_TITLE_MAX = 80
# Nearest neighbors shipped per point, ranked by the *blended* distance matrix
# (not the lossy 2D embedding) — the chronicle draws these as labeled spokes so
# unattempted probes show what they are actually similar to.
_NEIGHBOR_COUNT = 4


@method("get_knowledge_map")
def get_knowledge_map(ctx: SidecarContext, _params) -> dict[str, Any]:
    """Deterministic 2D embedding of every practice item (the knowledge map).

    Pipeline: one L2-normalized vector per item over the facet vocabulary
    (weights default to 1.0 for declared facets, matching
    ``predicted_correctness``), a blended distance matrix
    (0.6 x cosine facet distance + 0.4 x normalized concept-graph geodesic,
    same-LO pairs forced to 0 in the graph term), then classical MDS
    (Torgerson double-centering + top-2 eigenvectors via cyclic Jacobi —
    pure python, numpy is not a project dependency and the matrices are tiny).

    Determinism: items are processed in sorted-id order, Jacobi sweeps are
    cyclic (fixed pivot order), eigenpairs are stably sorted by descending
    eigenvalue, and each eigenvector's sign is fixed by forcing its
    largest-|component| entry (first index on ties) positive. Two calls on the
    same vault state therefore return byte-identical coordinates.

    ``stress`` is Kruskal stress-1 between the blended input distances and the
    embedded 2D distances — an honesty number: the plane is an approximation,
    and this is how approximate.
    """

    vault, repository = ctx.require_vault()

    item_ids = sorted(vault.practice_items)
    items = [vault.practice_items[item_id] for item_id in item_ids]
    n = len(items)

    # Probe/queued flags from one read-only scheduler pass (no persisted
    # explanations), same convention as get_facet_mastery.
    queue = build_due_queue(vault, repository, persist_explanations=False)
    queued_ids = {scheduled.practice_item_id for scheduled in queue}
    probe_ids = {
        scheduled.practice_item_id
        for scheduled in queue
        if scheduled.components.get("probe_eig", 0.0) > 0.0
    }

    vectors = [_facet_vector(item) for item in items]
    concept_of = {
        item.id: (lo.concept if (lo := vault.learning_object_for_item(item)) is not None else None)
        for item in items
    }
    hops = _concept_geodesics(vault, {c for c in concept_of.values() if c is not None})

    distances = _blended_distances(items, vectors, concept_of, hops)
    coords, stress = _classical_mds(distances)

    # Top-K neighbors per item from the true blended distances (ties broken by
    # id so repeat calls stay byte-identical).
    neighbor_lists: list[list[dict[str, Any]]] = []
    for i in range(n):
        order = sorted(
            (j for j in range(n) if j != i),
            key=lambda j: (distances[i][j], items[j].id),
        )
        neighbor_lists.append(
            [{"id": items[j].id, "distance": distances[i][j]} for j in order[:_NEIGHBOR_COUNT]]
        )

    facet_count = len({facet for item in items for facet in item.evidence_facets})
    points: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        mastery_state = repository.mastery_state(item.learning_object_id)
        display = display_mastery(mastery_state) if mastery_state is not None else None
        predicted = None
        if mastery_state is not None:
            item_a, item_b, _irt_config = resolve_item_irt(vault, item)
            predicted, _trace = predicted_correctness(
                repository,
                item,
                learning_object_id=item.learning_object_id,
                prior_mastery=mastery_state,
                item_a=item_a,
                item_b=item_b,
                config=vault.config,
                vault=vault,
            )
        top_facets = sorted(
            item.evidence_facets,
            key=lambda facet: (-item.evidence_weights.get(facet, 1.0), facet),
        )[:_TOP_FACETS]
        points.append(
            {
                "id": item.id,
                "title": _item_title(item.prompt),
                "learning_object_id": item.learning_object_id,
                "concept_id": concept_of[item.id],
                "x": coords[index][0],
                "y": coords[index][1],
                "mastery": display.mastery_mean if display is not None else None,
                "variance": display.mastery_variance if display is not None else None,
                "predicted_correct": predicted,
                "is_probe": item.id in probe_ids,
                "queued": item.id in queued_ids,
                "difficulty": item.difficulty,
                "facets": top_facets,
                "neighbors": neighbor_lists[index],
            }
        )

    return versioned(
        {
            "points": points,
            "counts": {
                "items": n,
                "learning_objects": len({item.learning_object_id for item in items}),
                "concepts": len({c for c in concept_of.values() if c is not None}),
                "facets": facet_count,
            },
            "stress": stress,
        }
    )


@method("get_knowledge_map_history")
def get_knowledge_map_history(ctx: SidecarContext, _params) -> dict[str, Any]:
    """Attempt events + reconstructed mastery trajectories for the chronicle.

    Two parallel feeds, both time-ordered:

    - ``attempts``: every recorded attempt as a discrete event (timestamp,
      item, correctness, type) — the chronicle plots these as dots in the
      space-time cube.
    - ``learning_objects[].series``: per-LO mastery step series reconstructed
      from ``attempt_surprise.posterior_delta`` (``sigmoid(mu_after)`` is the
      same display-mean mapping the feedback panel's before/after bars use).
      Only the *current* mastery state is stored; the surprise log is the
      canonical record of how it got there, so attempts without a surprise row
      (legacy imports, non-updating types) contribute an event but no series
      point.

    The frontend joins attempts to map points by ``practice_item_id`` and
    series to points by ``learning_object_id``; attempts referencing items
    since removed from the vault are simply never matched.
    """

    _vault, repository = ctx.require_vault()

    rows = repository.list_attempt_history()
    series_by_lo: dict[str, list[dict[str, Any]]] = {}
    attempts: list[dict[str, Any]] = []
    for row in rows:
        attempts.append(
            {
                "id": row["id"],
                "t": row["created_at"],
                "practice_item_id": row["practice_item_id"],
                "learning_object_id": row["learning_object_id"],
                "attempt_type": row["attempt_type"],
                "correctness": row["correctness"],
                "rubric_score": row["rubric_score"],
                "hints_used": row["hints_used"],
            }
        )
        delta = row["posterior_delta"] or {}
        mu_after = delta.get("mu_after")
        if mu_after is not None:
            series_by_lo.setdefault(row["learning_object_id"], []).append(
                {"t": row["created_at"], "mastery": sigmoid(mu_after)}
            )

    return versioned(
        {
            "attempts": attempts,
            "learning_objects": [
                {"id": lo_id, "series": series}
                for lo_id, series in sorted(series_by_lo.items())
            ],
            "range": (
                {"start": attempts[0]["t"], "end": attempts[-1]["t"]} if attempts else None
            ),
        }
    )


def _item_title(prompt: str) -> str:
    text = " ".join(prompt.split())
    if len(text) <= _TITLE_MAX:
        return text
    return text[: _TITLE_MAX - 1].rstrip() + "…"


def _facet_vector(item) -> dict[str, float]:
    """L2-normalized facet weights (missing declared weights default to 1.0).

    L2 (rather than sum) normalization because ``evidence_weights`` are
    free-scale relative importances — some authors write them summing to 1,
    others leave them all at the implicit 1.0 — and L2 makes the cosine
    distance below scale-invariant either way.
    """

    raw = {facet: max(0.0, float(item.evidence_weights.get(facet, 1.0))) for facet in item.evidence_facets}
    norm = sqrt(sum(value * value for value in raw.values()))
    if norm <= 0.0:
        return {}
    return {facet: value / norm for facet, value in raw.items()}


def _cosine_distance(u: dict[str, float], v: dict[str, float]) -> float:
    if not u or not v:
        return 1.0
    dot = sum(weight * v.get(facet, 0.0) for facet, weight in u.items())
    return max(0.0, min(1.0, 1.0 - dot))


def _concept_geodesics(vault, concepts: set[str]) -> dict[tuple[str, str], int | None]:
    """BFS hop counts between concepts over undirected structural edges.

    ``None`` marks unreachable pairs (different components); the blend treats
    those as maximally distant.
    """

    adjacency: dict[str, set[str]] = {}
    for edge in vault.edges:
        if edge.relation_type not in _GRAPH_RELATIONS:
            continue
        adjacency.setdefault(edge.source, set()).add(edge.target)
        adjacency.setdefault(edge.target, set()).add(edge.source)

    hops: dict[tuple[str, str], int | None] = {}
    for start in concepts:
        seen = {start: 0}
        frontier = deque([start])
        while frontier:
            node = frontier.popleft()
            for neighbor in adjacency.get(node, ()):
                if neighbor not in seen:
                    seen[neighbor] = seen[node] + 1
                    frontier.append(neighbor)
        for other in concepts:
            hops[(start, other)] = seen.get(other)
    return hops


def _blended_distances(
    items: list,
    vectors: list[dict[str, float]],
    concept_of: dict[str, str | None],
    hops: dict[tuple[str, str], int | None],
) -> list[list[float]]:
    n = len(items)
    # Normalize geodesics by the largest finite hop count so the graph term is
    # in [0, 1]; unreachable/unknown pairs sit at the top of that range.
    max_hops = max((h for h in hops.values() if h), default=0)

    def graph_distance(i: int, j: int) -> float:
        if items[i].learning_object_id == items[j].learning_object_id:
            return 0.0  # same LO: structurally identical for this term
        ci, cj = concept_of[items[i].id], concept_of[items[j].id]
        if ci is None or cj is None:
            return 1.0
        hop = hops.get((ci, cj))
        if hop is None:
            return 1.0
        if max_hops == 0:
            return 0.0 if hop == 0 else 1.0
        return min(1.0, hop / max_hops)

    distances = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            value = _FACET_BLEND * _cosine_distance(vectors[i], vectors[j]) + _GRAPH_BLEND * graph_distance(i, j)
            distances[i][j] = value
            distances[j][i] = value
    return distances


def _classical_mds(distances: list[list[float]]) -> tuple[list[tuple[float, float]], float]:
    """Torgerson classical MDS to 2D, plus Kruskal stress-1.

    Coordinates are rescaled uniformly (one shared factor, preserving the
    embedding's aspect ratio) so the largest |coordinate| is 1.
    """

    n = len(distances)
    if n == 0:
        return [], 0.0
    if n == 1:
        return [(0.0, 0.0)], 0.0

    # B = -1/2 * J D^2 J (double centering).
    sq = [[distances[i][j] ** 2 for j in range(n)] for i in range(n)]
    row_mean = [sum(row) / n for row in sq]
    grand = sum(row_mean) / n
    b = [
        [-0.5 * (sq[i][j] - row_mean[i] - row_mean[j] + grand) for j in range(n)]
        for i in range(n)
    ]

    eigenvalues, eigenvectors = _jacobi_eigh(b)
    # Stable sort by descending eigenvalue (ties keep Jacobi's output order).
    order = sorted(range(n), key=lambda k: -eigenvalues[k])
    axes: list[list[float]] = []
    for rank in range(2):
        if rank < len(order) and eigenvalues[order[rank]] > 1e-12:
            k = order[rank]
            vector = [eigenvectors[i][k] for i in range(n)]
            # Sign convention: the largest-|component| entry (first index on
            # ties) is forced positive so repeat calls never mirror the map.
            pivot = max(range(n), key=lambda i: abs(vector[i]))
            if vector[pivot] < 0:
                vector = [-value for value in vector]
            scale = sqrt(eigenvalues[k])
            axes.append([value * scale for value in vector])
        else:
            axes.append([0.0] * n)

    coords = [(axes[0][i], axes[1][i]) for i in range(n)]

    # Stress-1 on the raw (pre-rescale) embedding vs the blended input.
    num = 0.0
    den = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            embedded = sqrt((coords[i][0] - coords[j][0]) ** 2 + (coords[i][1] - coords[j][1]) ** 2)
            num += (distances[i][j] - embedded) ** 2
            den += distances[i][j] ** 2
    stress = sqrt(num / den) if den > 0 else 0.0

    extent = max((max(abs(x), abs(y)) for x, y in coords), default=0.0)
    if extent > 0:
        coords = [(x / extent, y / extent) for x, y in coords]
    return coords, stress


def _jacobi_eigh(matrix: list[list[float]]) -> tuple[list[float], list[list[float]]]:
    """Cyclic Jacobi eigendecomposition for a small symmetric matrix.

    Pure python on purpose: numpy is not a project dependency and n here is
    the practice-item count (tens). Fixed sweep order keeps it deterministic.
    Returns (eigenvalues, eigenvectors) with eigenvector k in column k.
    """

    n = len(matrix)
    a = [row[:] for row in matrix]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    for _sweep in range(100):
        off = sqrt(sum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j))
        if off < 1e-12:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(a[p][q]) < 1e-15:
                    continue
                theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
                t = (1.0 if theta >= 0 else -1.0) / (abs(theta) + sqrt(theta * theta + 1.0))
                c = 1.0 / sqrt(t * t + 1.0)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p] = c * akp - s * akq
                    a[k][q] = s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k] = c * apk - s * aqk
                    a[q][k] = s * apk + c * aqk
                for k in range(n):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p] = c * vkp - s * vkq
                    v[k][q] = s * vkp + c * vkq

    return [a[i][i] for i in range(n)], v
