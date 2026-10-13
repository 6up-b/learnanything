"""The facet-identity plan of one synthesis or append run.

After the shards (or the append reconciliation) return and before the gates:

1. **Within-run consolidation.** The run's candidate facets are grouped into
   concept neighbourhoods (same or consolidated concept, concept-graph
   adjacency, the lexical near-duplicate pairs, and the T5 embedding
   shortlist over the run's own candidates when embeddings are on) and the
   judge partitions each group. A retired candidate is not minted: its
   references point at the survivor, its id becomes an alias of the survivor,
   and the survivor's payload is the union (``views.union_payload``).
2. **Attach (the D2 mint gate with a decision).** Each surviving candidate
   meets the registered facets T5 nominates for it (top-k), plus registered
   facets of its own registry concept and lexical near-duplicates. The same
   judge decides; a match becomes an alias of the registered facet (merge),
   or an alias whose claim joins its examples or preconditions (absorb),
   instead of a mint; the registered facet's contract otherwise stays as it
   is (an append-legal, growth-only update). This replaces T5's shadow-only
   comparison for the facets it decides; D2's structural test still runs on
   everything the judge kept distinct.

The plan is data: it is stored on the synthesis run (``actual_usage``) and
``_normalize`` applies it, so a revalidation replays it with zero model calls.
With ``facet_identity.enabled = false`` no plan exists and nothing changes.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.content.facet_identity.grouping import FacetNode, neighbourhood_groups
from learnloop.content.facet_identity.judge import (
    GroupOutcome,
    Member,
    build_judge,
    build_request,
    caps_from_config,
    resolve_route,
)
from learnloop.content.facet_identity.views import judge_view, union_payload
from learnloop.content.synthesis.synthesis_gates import facet_tokens, jaccard

PLAN_VERSION = "facet-identity-plan-v1"
CANDIDATE_KIND = "facet_candidate"
FACET_KIND = "facet"


@dataclass
class Retirement:
    """One candidate that is not minted, and where it goes."""

    client_id: str
    scope: str  # in_run | attach
    action: str  # merge | absorb
    absorb_as: str | None
    survivor_client: str | None = None  # in_run
    survivor_facet: str | None = None  # attach: the registered facet id
    group_id: str = ""
    judgment_ids: list[str] = field(default_factory=list)
    rationale: str = ""
    judge: str = "llm"
    judge_model: str | None = None
    prompt_version: str = ""


@dataclass
class FacetIdentityPlan:
    status: str  # judged | partial | no_groups | judge_unavailable | over_budget
    retirements: dict[str, Retirement] = field(default_factory=dict)
    groups: list[dict[str, Any]] = field(default_factory=list)
    route: dict[str, Any] | None = None
    charged: dict[str, Any] | None = None
    grouping: dict[str, Any] | None = None
    notes: list[str] = field(default_factory=list)
    version: str = PLAN_VERSION

    def in_run(self) -> dict[str, Retirement]:
        return {key: value for key, value in self.retirements.items() if value.scope == "in_run"}

    def attach(self) -> dict[str, Retirement]:
        return {key: value for key, value in self.retirements.items() if value.scope == "attach"}

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version, "status": self.status,
            "retirements": {key: asdict(value) for key, value in sorted(self.retirements.items())},
            "groups": self.groups, "route": self.route, "charged": self.charged,
            "grouping": self.grouping, "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> FacetIdentityPlan | None:
        if not data:
            return None
        retirements = {
            str(key): Retirement(**{name: value for name, value in dict(raw).items()
                                    if name in Retirement.__dataclass_fields__})
            for key, raw in dict(data.get("retirements") or {}).items()
        }
        return cls(
            status=str(data.get("status") or "judged"), retirements=retirements,
            groups=list(data.get("groups") or []), route=data.get("route"), charged=data.get("charged"),
            grouping=data.get("grouping"), notes=list(data.get("notes") or []),
            version=str(data.get("version") or PLAN_VERSION),
        )

    def summary(self) -> dict[str, Any]:
        in_run, attach = self.in_run(), self.attach()
        return {
            "status": self.status,
            "groups_judged": sum(1 for group in self.groups if group.get("status") in {"judged", "reused"}),
            "groups": len(self.groups),
            "in_run_retired": len(in_run),
            "attached": len(attach),
            "judge": (self.route or {}).get("model"),
            "notes": list(self.notes),
        }


def _d(obj: Any) -> dict[str, Any]:
    if isinstance(obj, Mapping):
        return dict(obj)
    return obj.model_dump(mode="json")


def candidate_subject_id(payload: Mapping[str, Any]) -> str:
    """A candidate's ledger subject: its content, so reruns ask the same question."""

    return "sha:" + content_key({key: payload.get(key) for key in (
        "kind", "claim", "preconditions", "postconditions", "applicability",
        "positive_examples", "negative_examples", "non_goals",
    )})[:40]


def _concepts(synth: Any, vault: Any) -> tuple[dict[str, str], list[tuple[str, str]]]:
    """Concept titles (client and registry ids) and concept-graph edges."""

    titles: dict[str, str] = {concept_id: concept.title for concept_id, concept in vault.concepts.items()}
    for concept in getattr(synth, "concepts", []) or []:
        data = _d(concept)
        key = str(data.get("client_item_id") or data.get("id") or "")
        if key:
            titles[key] = str(data.get("title") or key)
    edges = [(edge.source, edge.target) for edge in vault.edges]
    for relation in getattr(synth, "concept_relations", []) or []:
        data = _d(relation)
        if data.get("source") and data.get("target"):
            edges.append((str(data["source"]), str(data["target"])))
    return titles, edges


def _candidate_nodes(synth: Any) -> list[tuple[str, dict[str, Any], str | None]]:
    out: list[tuple[str, dict[str, Any], str | None]] = []
    seen: set[str] = set()
    for facet in getattr(synth, "facets", []) or []:
        data = _d(facet)
        client = str(data.get("client_item_id") or "")
        if not client or client in seen:
            continue
        seen.add(client)
        concept = str(data.get("concept_client_id") or data.get("concept_id") or "") or None
        out.append((client, data, concept))
    return out


def build_plan(
    synth: Any,
    *,
    vault: Any,
    repository: Any,
    run_id: str,
    nominator: Any = None,
    judge_client: Any = None,
    cancelled: Callable[[], bool] | None = None,
    attach_enabled: bool = True,
) -> FacetIdentityPlan | None:
    """Decide the run's facet identities. ``None`` when facet identity is off."""

    settings = vault.config.facet_identity
    if not settings.enabled:
        return None
    candidates = _candidate_nodes(synth)
    titles, concept_edges = _concepts(synth, vault)
    payload_by_client = {client: payload for client, payload, _concept in candidates}
    subject_ids: dict[str, str] = {}
    used: dict[str, int] = {}
    for client, payload, _concept in candidates:
        base = candidate_subject_id(payload)
        used[base] = used.get(base, 0) + 1
        subject_ids[client] = base if used[base] == 1 else f"{base}#{used[base]}"

    plan = FacetIdentityPlan(status="no_groups")
    vectors: dict[str, Any] = {}
    queries: dict[str, Any] = {}
    if nominator is not None and candidates:
        from learnloop.content.synthesis.graph_nomination import facet_query

        try:
            queries = {client: facet_query(payload, record_id=client) for client, payload, _c in candidates}
            by_hash = nominator.vectors([query for query in queries.values() if query is not None])
            vectors = {client: by_hash[query.content_hash] for client, query in queries.items()
                       if query is not None and query.content_hash in by_hash}
        except Exception as exc:  # noqa: BLE001 - the shortlist never fails ingest
            plan.notes.append(f"shortlist_unavailable:{type(exc).__name__}")
            vectors = {}

    nodes = [FacetNode(key=client, payload=payload, concept=concept, existing=False)
             for client, payload, concept in candidates]
    grouping = neighbourhood_groups(
        nodes, concept_edges=concept_edges, vectors=vectors, top_k=settings.shortlist_top_k,
        max_group_size=settings.max_group_size,
    )
    plan.grouping = grouping.summary()

    # A candidate whose content is a registered facet's is that facet for the
    # owner's verdicts (an undone merge stays undone on a resynthesis).
    registered_by_content: dict[str, list[str]] = {}
    for facet_id, facet in vault.evidence_facets.items():
        registered_by_content.setdefault(candidate_subject_id(facet.model_dump(mode="json")), []).append(facet_id)

    def member(client: str, payload: Mapping[str, Any], concept: str | None) -> Member:
        content = candidate_subject_id(payload_by_client.get(client, payload))
        return Member(label="", key=client, subject_kind=CANDIDATE_KIND, subject_id=subject_ids[client],
                      existing=False, view=judge_view(payload, concept_title=titles.get(concept or "")),
                      payload=payload,
                      also=tuple((FACET_KIND, facet_id) for facet_id in sorted(registered_by_content.get(content, []))))

    concept_of = {client: concept for client, _payload, concept in candidates}
    in_run_requests = [
        build_request([member(client, payload_by_client[client], concept_of[client]) for client in group],
                      mode="consolidate", shortlisted=grouping.shortlisted)
        for group in grouping.groups
    ]
    registered = {
        facet_id: facet for facet_id, facet in vault.evidence_facets.items()
        if facet.status != "retired" and vault.canonical_facet_id(facet_id) == facet_id
    }
    if not in_run_requests and not (attach_enabled and registered and candidates):
        return plan

    judge, route = build_judge(vault, repository, owner_id=run_id, caps=caps_from_config(settings),
                               client=judge_client, cancelled=cancelled)
    plan.route = route.as_dict()
    if judge is None:
        plan.status = "judge_unavailable"
        plan.notes.append(route.problem or "judge unavailable")
        return plan

    outcomes: list[GroupOutcome] = judge.run(in_run_requests) if in_run_requests else []
    for outcome in outcomes:
        plan.groups.append(outcome.summary())
        for decided in outcome.sets:
            for retired in decided.retired:
                plan.retirements[retired] = Retirement(
                    client_id=retired, scope="in_run", action=decided.action, absorb_as=decided.absorb_as,
                    survivor_client=decided.survivor, group_id=outcome.request.group_id,
                    judgment_ids=outcome.judgments_for([retired, decided.survivor]),
                    rationale=decided.rationale, judge=outcome.judge, judge_model=outcome.judge_model,
                    prompt_version=outcome.prompt_version,
                )

    if attach_enabled and registered:
        registry_concept_of = {}
        for concept in getattr(synth, "concepts", []) or []:
            data = _d(concept)
            if data.get("client_item_id") and data.get("id") in vault.concepts:
                registry_concept_of[str(data["client_item_id"])] = str(data["id"])
        attach_requests = _attach_requests(
            plan, candidates, registered, titles=titles, nominator=nominator, queries=queries,
            settings=settings, member=member, payload_by_client=payload_by_client,
            registry_concept_of=registry_concept_of,
        )
        attach_outcomes = judge.run(attach_requests) if attach_requests else []
        for outcome in attach_outcomes:
            plan.groups.append(outcome.summary())
            for decided in outcome.sets:
                survivor_member = outcome.request.by_key(decided.survivor)
                for retired in decided.retired:
                    retired_member = outcome.request.by_key(retired)
                    if retired_member is None or retired_member.existing:
                        continue
                    if survivor_member is not None and survivor_member.existing:
                        plan.retirements[retired] = Retirement(
                            client_id=retired, scope="attach", action=decided.action, absorb_as=decided.absorb_as,
                            survivor_facet=survivor_member.subject_id, group_id=outcome.request.group_id,
                            judgment_ids=outcome.judgments_for([retired, decided.survivor]),
                            rationale=decided.rationale, judge=outcome.judge, judge_model=outcome.judge_model,
                            prompt_version=outcome.prompt_version,
                        )
                    else:
                        plan.retirements[retired] = Retirement(
                            client_id=retired, scope="in_run", action=decided.action, absorb_as=decided.absorb_as,
                            survivor_client=decided.survivor, group_id=outcome.request.group_id,
                            judgment_ids=outcome.judgments_for([retired, decided.survivor]),
                            rationale=decided.rationale, judge=outcome.judge, judge_model=outcome.judge_model,
                            prompt_version=outcome.prompt_version,
                        )
        outcomes = [*outcomes, *attach_outcomes]

    _resolve_chains(plan)
    plan.charged = judge.charged()
    statuses = {outcome.status for outcome in outcomes}
    if not outcomes:
        plan.status = "no_groups"
    elif statuses <= {"judged", "reused"}:
        plan.status = "judged"
    elif statuses & {"judged", "reused"}:
        plan.status = "partial"
    else:
        plan.status = "over_budget" if any(o.error == "SpendLimitExceeded" for o in outcomes) else "judge_failed"
    return plan


def _attach_requests(
    plan: FacetIdentityPlan,
    candidates: Sequence[tuple[str, dict[str, Any], str | None]],
    registered: Mapping[str, Any],
    *,
    titles: Mapping[str, str],
    nominator: Any,
    queries: Mapping[str, Any],
    settings: Any,
    member: Callable[..., Member],
    payload_by_client: Mapping[str, Mapping[str, Any]],
    registry_concept_of: Mapping[str, str] | None = None,
) -> list[Any]:
    """Groups of surviving candidates with the registered facets nominated for them."""

    registry_concept_of = dict(registry_concept_of or {})
    survivors = [(client, payload, concept) for client, payload, concept in candidates if client not in plan.retirements]
    if not survivors:
        return []
    # Survivors are judged with their consolidated payload.
    absorbed: dict[str, list[tuple[Mapping[str, Any], str, str | None]]] = {}
    for retirement in plan.in_run().values():
        absorbed.setdefault(str(retirement.survivor_client), []).append(
            (payload_by_client[retirement.client_id], retirement.action, retirement.absorb_as))
    views: dict[str, Mapping[str, Any]] = {}
    for client, payload, _concept in survivors:
        merged = dict(payload)
        for retired_payload, action, absorb_as in absorbed.get(client, []):
            merged = union_payload(merged, [retired_payload], action=action, absorb_as=absorb_as)
        views[client] = merged

    pairs: set[tuple[str, str]] = set()
    if nominator is not None and queries:
        from learnloop.content.synthesis.graph_nomination import FACET_RECIPE

        try:
            nominations = nominator.nominate(
                FACET_RECIPE, [queries[client] for client, _p, _c in survivors if queries.get(client) is not None],
                k=settings.attach_top_k,
            )
        except Exception as exc:  # noqa: BLE001 - nominations never fail ingest
            plan.notes.append(f"attach_nominations_unavailable:{type(exc).__name__}")
            nominations = {}
        for client, found in nominations.items():
            for nomination in found:
                if nomination.record_id in registered:
                    pairs.add((client, nomination.record_id))
    registered_tokens = {facet_id: facet_tokens(facet.model_dump(mode="json")) for facet_id, facet in registered.items()}
    by_concept: dict[str, list[str]] = {}
    for facet_id, facet in registered.items():
        if facet.concept_id:
            by_concept.setdefault(facet.concept_id, []).append(facet_id)
    for client, _payload, concept in survivors:
        tokens = facet_tokens(dict(views[client]))
        registry_concept = registry_concept_of.get(concept or "", concept)
        for facet_id in sorted(by_concept.get(registry_concept or "", []))[: settings.max_group_size]:
            pairs.add((client, facet_id))
        for facet_id, other in registered_tokens.items():
            if jaccard(tokens, other) >= 0.85:
                pairs.add((client, facet_id))
    if not pairs:
        return []
    nodes = [FacetNode(key=client, payload=views[client], existing=False) for client, _p, _c in survivors
             if any(pair[0] == client for pair in pairs)]
    nodes += [FacetNode(key=f"registered::{facet_id}", payload=registered[facet_id].model_dump(mode="json"))
              for facet_id in sorted({pair[1] for pair in pairs})]
    grouping = neighbourhood_groups(
        nodes, extra_pairs=[(client, f"registered::{facet_id}") for client, facet_id in sorted(pairs)],
        max_group_size=settings.max_group_size, lexical_threshold=2.0,
    )
    concept_of = {client: concept for client, _p, concept in candidates}
    requests = []
    for group in grouping.groups:
        members: list[Member] = []
        for key in group:
            if key.startswith("registered::"):
                facet_id = key.split("::", 1)[1]
                facet = registered[facet_id]
                members.append(Member(
                    label="", key=key, subject_kind=FACET_KIND, subject_id=facet_id, existing=True,
                    view=judge_view(facet.model_dump(mode="json"), concept_title=titles.get(facet.concept_id or "")),
                    payload=facet.model_dump(mode="json"),
                ))
            else:
                members.append(member(key, views[key], concept_of.get(key)))
        if any(not m.existing for m in members) and any(m.existing for m in members):
            # Every candidate-registered pair the attach step put forward (T5's
            # nominations, the registry concept, lexical near-duplicates) is
            # shortlisted for the ledger.
            requests.append(build_request(members, mode="attach", shortlisted=grouping.shortlisted))
    return requests


def _resolve_chains(plan: FacetIdentityPlan) -> None:
    """A survivor that is itself retired forwards its retirees (never a cycle)."""

    for retirement in plan.retirements.values():
        seen = {retirement.client_id}
        while retirement.scope == "in_run" and retirement.survivor_client in plan.retirements:
            nxt = plan.retirements[str(retirement.survivor_client)]
            if nxt.client_id in seen:
                break
            seen.add(nxt.client_id)
            if nxt.scope == "attach":
                retirement.scope = "attach"
                retirement.survivor_facet = nxt.survivor_facet
                retirement.survivor_client = None
                retirement.judgment_ids = sorted({*retirement.judgment_ids, *nxt.judgment_ids})
                break
            retirement.survivor_client = nxt.survivor_client


def ingest_dry_run(vault: Any) -> dict[str, Any]:
    """The facet-identity judge's part of a synthesis/append dry run (review F5).

    The run writes its candidates, so the calls are bounded by the per-run
    caps, not counted: one call per concept neighbourhood of the run's new
    facets, plus one per attach group against registered facets, retries
    included, never more than ``max_calls``. No client, no call, no change.
    """

    settings = vault.config.facet_identity
    if not settings.enabled:
        return {"enabled": False, "status": "off", "max_calls": 0, "max_estimated_usd": 0.0}
    route = resolve_route(vault.config)
    caps = caps_from_config(settings)
    return {
        "enabled": True,
        "status": "unavailable" if route.problem else "may_judge",
        "route": route.as_dict(),
        "caps": caps.as_dict(),
        "max_calls": caps.max_calls,
        "max_total_tokens": caps.max_total_tokens,
        # Codex on the subscription: dollars are estimated only, never a cap.
        "max_estimated_usd": None if route.subscription else caps.max_estimated_usd,
        "billing": "subscription" if route.subscription else "metered",
        "cost_basis": route.as_dict()["cost_basis"],
        "covers": ("one judge call per concept neighbourhood of the run's new facets and one per attach "
                   "group against registered facets, retries included, bounded by the per-run caps"),
    }


__all__ = [
    "CANDIDATE_KIND",
    "FACET_KIND",
    "FacetIdentityPlan",
    "PLAN_VERSION",
    "Retirement",
    "build_plan",
    "candidate_subject_id",
    "ingest_dry_run",
]
