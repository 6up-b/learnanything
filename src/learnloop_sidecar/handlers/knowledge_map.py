from __future__ import annotations

from collections import deque
import hashlib
import heapq
import json
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
            "facet_field": _facet_field(vault, repository),
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


def _facet_field(vault, repository) -> dict[str, Any]:
    """Facet topology + dual evidence/prediction axes for the gravity field.

    Layout topology comes only from authored BlueprintRecipes. Every pair that
    co-occurs in a recipe (all_of, any_of, or integration) receives a direct edge
    weighted by the blueprint recipe weight. The same graph is shipped for
    graph-Laplacian diffusion in the renderer — screen distance alone never
    invents evidence adjacency.
    """

    from learnloop.services.capability_mapping import CAPABILITY_VOCABULARY
    from learnloop.services.certification import is_demonstrated_credit
    from learnloop.services.facet_evidence_timeline import facet_evidence_timeline

    facet_ids = {
        vault.canonical_facet_id(facet_id)
        for facet_id, facet in vault.evidence_facets.items()
        if facet.status != "retired"
    }
    required: dict[str, set[str]] = {}
    lo_ids: dict[str, set[str]] = {}
    edge_weights: dict[tuple[str, str], float] = {}
    graph_nodes: set[str] = set(facet_ids)

    def add_edge(left: str, right: str, weight: float) -> None:
        if not left or not right or left == right:
            return
        key = tuple(sorted((left, right)))
        edge_weights[key] = edge_weights.get(key, 0.0) + max(float(weight), 0.01)
        graph_nodes.update(key)

    for lo_id, learning_object in sorted(vault.learning_objects.items()):
        for blueprint in learning_object.blueprints:
            weight = max(float(blueprint.weight), 0.01)
            for recipe in blueprint.recipes:
                components = [*recipe.all_of, *recipe.any_of]
                if recipe.integration is not None:
                    components.append(recipe.integration)
                component_ids: list[str] = []
                for component in components:
                    facet = vault.canonical_facet_id(component.facet)
                    facet_ids.add(facet)
                    graph_nodes.add(facet)
                    required.setdefault(facet, set()).add(component.capability)
                    lo_ids.setdefault(facet, set()).add(lo_id)
                    component_ids.append(facet)
                unique_ids = sorted(set(component_ids))
                for index, left in enumerate(unique_ids):
                    for right in unique_ids[index + 1 :]:
                        add_edge(left, right, weight)

    # Keep registry-only facets visible as explicitly unblueprinted positions.
    facets = sorted(facet_ids)
    adjacency = _weighted_adjacency(graph_nodes, edge_weights)
    distances = _facet_graph_distances(facets, adjacency)
    if len(facets) > 1 and any(distances[i][j] > 0 for i in range(len(facets)) for j in range(i)):
        coords, stress = _classical_mds(distances)
    elif len(facets) == 1:
        coords, stress = [(0.0, 0.0)], 0.0
    else:
        coords, stress = [], 0.0

    # Ready is capability-agnostic at launch, so fold the capability slices into
    # the same pooled Beta parent used by the capability grid. Canonical rows are
    # keyed by their actual capability (there normally is no literal `shared`
    # row), making a `capability_key == "shared"` lookup silently show 0.5 for
    # every facet.
    recall_by_facet: dict[str, dict[str, float]] = {}
    for row in repository.canonical_facet_recall_states():
        if row.practice_item_id is not None:
            continue
        facet = vault.canonical_facet_id(row.facet_id)
        pooled = recall_by_facet.setdefault(
            facet,
            {"alpha": 1.0, "beta": 1.0, "evidence_mass": 0.0},
        )
        pooled["alpha"] += float(row.recall_alpha) - 1.0
        pooled["beta"] += float(row.recall_beta) - 1.0
        pooled["evidence_mass"] += float(row.independent_evidence_mass)
    evidence_by_facet: dict[str, dict[str, Any]] = {}
    for cell in repository.facet_capability_evidence_all():
        evidence_by_facet.setdefault(cell.facet_id, {})[cell.capability] = cell
    retention_by_facet = _facet_current_retentions(vault, repository)

    ambiguity: dict[str, set[str]] = {}
    ambiguity_target: dict[str, str] = {}
    for factor in repository.open_unresolved_cause_factors():
        candidates = {
            vault.canonical_facet_id(str(cause.get("facet")))
            for cause in factor.get("candidate_causes") or []
            if isinstance(cause, dict) and cause.get("facet")
        }
        for facet in candidates:
            ambiguity.setdefault(facet, set()).update(candidates - {facet})
            ambiguity_target.setdefault(facet, str(factor["attempt_id"]))

    points: list[dict[str, Any]] = []
    for index, facet_id in enumerate(facets):
        requirement = sorted(required.get(facet_id, set()))
        ledger = evidence_by_facet.get(facet_id, {})
        demonstrated_caps = sorted(
            capability
            for capability in requirement
            if capability in ledger
            and is_demonstrated_credit(ledger[capability].certification_credit)
        )
        demonstrated_mass = (
            len(demonstrated_caps) / len(requirement) if requirement else 0.0
        )
        state = recall_by_facet.get(facet_id)
        if state is not None:
            total = state["alpha"] + state["beta"]
            ready_ghost = state["alpha"] / total
            retention = retention_by_facet.get(facet_id, 1.0)
            ready = ready_ghost * retention
            variance = state["alpha"] * state["beta"] / (total**2 * (total + 1.0))
            evidence_mass = state["evidence_mass"]
        else:
            ready = 0.5
            ready_ghost = 0.5
            variance = 1.0 / 12.0
            evidence_mass = 0.0
        registry = vault.evidence_facets.get(facet_id)
        capabilities = []
        for capability in CAPABILITY_VOCABULARY:
            if capability not in requirement:
                status = "absent"
            elif capability in demonstrated_caps:
                status = "demonstrated"
            else:
                status = "required"
            capabilities.append({"capability": capability, "status": status})
        corrections = [
            point for point in facet_evidence_timeline(vault, repository, facet_id)
            if point.is_correction
        ]
        latest_correction = corrections[-1] if corrections else None
        points.append(
            {
                "id": facet_id,
                "title": (registry.title if registry and registry.title else facet_id),
                "x": coords[index][0],
                "y": coords[index][1],
                "ready": ready,
                "ready_ghost": ready_ghost,
                "ready_variance": variance,
                "evidence_mass": evidence_mass,
                "demonstrated_mass": demonstrated_mass,
                "required_capabilities": requirement,
                "demonstrated_capabilities": demonstrated_caps,
                "has_blueprints": bool(requirement),
                "capability_arcs": capabilities,
                "learning_object_ids": sorted(lo_ids.get(facet_id, set())),
                "ambiguity_candidates": sorted(ambiguity.get(facet_id, set())),
                "ambiguity_attempt_id": ambiguity_target.get(facet_id),
                "correction": (
                    {
                        "at": latest_correction.t,
                        "delta": latest_correction.delta,
                        "attempt_id": latest_correction.attempt_id,
                    }
                    if latest_correction is not None
                    else None
                ),
            }
        )

    next_gap = _next_gap(vault, repository, points, adjacency)
    edge_rows = [
        {"source": left, "target": right, "weight": round(weight, 6)}
        for (left, right), weight in sorted(edge_weights.items())
    ]
    layout_payload = {"nodes": sorted(graph_nodes), "edges": edge_rows}
    layout_version = "sha256:" + hashlib.sha256(
        json.dumps(layout_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "points": points,
        "graph_nodes": sorted(graph_nodes),
        "edges": edge_rows,
        "layout_version": layout_version,
        "stress": stress,
        "layout_valid": bool(edge_rows) and stress <= 0.42,
        "layout_warning": (
            None
            if bool(edge_rows) and stress <= 0.42
            else "Recipe topology does not support an honest 3D field yet; showing the flat graph."
        ),
        "next_gap": next_gap,
    }


def _facet_current_retentions(vault, repository) -> dict[str, float]:
    """Evidence-weighted present-day FSRS retention by facet item family.

    Day-granular evaluation keeps the field deterministic within a session while
    still allowing a certified well to visibly relax over time. No supporting
    memory state means no decay information, so retention remains 1 rather than
    inventing forgetting.
    """

    from datetime import UTC, datetime

    from learnloop.clock import parse_utc
    from learnloop.services.fitted_params import resolve_fsrs_weights
    from learnloop.services.fsrs import forgetting_curve

    now = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    states = repository.practice_item_states()
    weights = resolve_fsrs_weights(repository)
    totals: dict[str, list[float]] = {}
    for item in vault.practice_items.values():
        state = states.get(item.id)
        last_attempt = parse_utc(state.last_attempt_at) if state is not None else None
        if state is None or state.stability is None or last_attempt is None:
            continue
        elapsed = max(0.0, (now - last_attempt).total_seconds() / 86400.0)
        retention = forgetting_curve(state.stability, elapsed, weights)
        for raw_facet in item.evidence_facets:
            facet = vault.canonical_facet_id(str(raw_facet))
            weight = max(float(item.evidence_weights.get(str(raw_facet), 1.0)), 0.01)
            acc = totals.setdefault(facet, [0.0, 0.0])
            acc[0] += weight * retention
            acc[1] += weight
    return {
        facet: numerator / denominator
        for facet, (numerator, denominator) in totals.items()
        if denominator > 0
    }


def _weighted_adjacency(nodes, edge_weights) -> dict[str, dict[str, float]]:
    adjacency = {node: {} for node in nodes}
    for (left, right), weight in edge_weights.items():
        # Strong co-requirement means short graph distance.
        cost = 1.0 / max(weight, 0.01)
        adjacency[left][right] = min(adjacency[left].get(right, float("inf")), cost)
        adjacency[right][left] = min(adjacency[right].get(left, float("inf")), cost)
    return adjacency


def _shortest_paths(start: str, adjacency) -> tuple[dict[str, float], dict[str, str]]:
    distance = {start: 0.0}
    previous: dict[str, str] = {}
    queue = [(0.0, start)]
    while queue:
        value, node = heapq.heappop(queue)
        if value != distance.get(node):
            continue
        for neighbor, cost in sorted(adjacency.get(node, {}).items()):
            candidate = value + cost
            if candidate < distance.get(neighbor, float("inf")):
                distance[neighbor] = candidate
                previous[neighbor] = node
                heapq.heappush(queue, (candidate, neighbor))
    return distance, previous


def _facet_graph_distances(facets: list[str], adjacency) -> list[list[float]]:
    paths = [_shortest_paths(facet, adjacency)[0] for facet in facets]
    finite = [
        paths[i][facet]
        for i in range(len(facets))
        for facet in facets
        if facet in paths[i] and paths[i][facet] > 0
    ]
    disconnected = (max(finite) if finite else 1.0) * 1.25
    return [
        [0.0 if left == right else paths[i].get(right, disconnected) for right in facets]
        for i, left in enumerate(facets)
    ]


def _next_gap(vault, repository, points, adjacency) -> dict[str, Any] | None:
    """One model-selected gap pin, routed to its native drill-down."""

    from learnloop.services.capability_grid import lo_blueprint_readiness
    from learnloop.services.goal_certification import lo_certification
    from learnloop.services.goal_projection import resolve_goal_scope

    point_by_id = {point["id"]: point for point in points}
    goals = sorted(
        (goal for goal in vault.goals if goal.status == "active"),
        key=lambda goal: (-goal.priority, goal.due_at or "", goal.id),
    )
    target: dict[str, Any] | None = None
    for goal in goals:
        scope = resolve_goal_scope(vault, goal, repository)
        candidates: list[tuple[float, str, Any]] = []
        for lo_id in sorted(scope):
            learning_object = vault.learning_objects.get(lo_id)
            if learning_object is None:
                continue
            certification = lo_certification(vault, repository, learning_object)
            if not certification.component_gaps and certification.integration_gaps:
                facet = certification.integration_gaps[0]
                target = {
                    "kind": "integration_gap",
                    "facet_id": facet,
                    "goal_id": goal.id,
                    "target_type": "learning_object",
                    "target_id": lo_id,
                    "label": "Connect demonstrated components",
                }
                break
            readiness = lo_blueprint_readiness(vault, repository, lo_id)
            if readiness and readiness.bottleneck:
                candidates.append(
                    (readiness.bottleneck.predicted_recall, lo_id, readiness.bottleneck)
                )
        if target is not None:
            break
        if candidates:
            _score, lo_id, bottleneck = min(candidates, key=lambda row: (row[0], row[1]))
            facet = vault.canonical_facet_id(bottleneck.facet)
            point = point_by_id.get(facet) or {}
            if point.get("ambiguity_attempt_id"):
                kind = "unresolved_diagnostic"
                target_type, target_id = _diagnostic_target(
                    repository, point["ambiguity_attempt_id"]
                )
                label = "Resolve competing causes"
            elif (
                point.get("demonstrated_mass", 0.0) > 0
                and point.get("ready_ghost", 0.0) - point.get("ready", 0.0) >= 0.08
            ):
                kind = "retrievability"
                target_type = "facet"
                target_id = facet
                label = "Restore a relaxing well"
            else:
                kind = "bottleneck_component"
                target_type = "learning_object"
                target_id = lo_id
                label = "Cross the active recipe bottleneck"
            target = {
                "kind": kind,
                "facet_id": facet,
                "goal_id": goal.id,
                "target_type": target_type,
                "target_id": target_id,
                "label": label,
            }
            break
    if target is None or target["facet_id"] not in point_by_id:
        return None

    demonstrated = [point for point in points if point["demonstrated_mass"] > 0]
    if demonstrated:
        source = max(
            demonstrated,
            key=lambda point: (point["demonstrated_mass"], point["evidence_mass"], point["id"]),
        )["id"]
        _distance, previous = _shortest_paths(source, adjacency)
        path = [target["facet_id"]]
        while path[-1] != source and path[-1] in previous:
            path.append(previous[path[-1]])
        path.reverse()
        target["path_facet_ids"] = [node for node in path if node in point_by_id]
    else:
        target["path_facet_ids"] = [target["facet_id"]]
    return target


def _diagnostic_target(repository, attempt_id: str) -> tuple[str, str]:
    """Route ambiguity to its probe episode when one owns the observation."""

    attempt = repository.fetch_practice_attempt(attempt_id)
    presentation_id = attempt.get("probe_presentation_id") if attempt else None
    presentation = (
        repository.probe_presentation(presentation_id) if presentation_id else None
    )
    if presentation is not None:
        return "probe_episode", presentation.probe_episode_id
    return "attempt", attempt_id


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
