"""``learnloop facets dedupe``: one-off cleanup of an existing vault's facets.

The judge gets each concept neighbourhood's facets at once (same concept,
concept-graph adjacency, the lexical near-duplicate pairs) and partitions it
exactly as at ingest. Embeddings are not needed: vaults are small. Stored
``facet/definition`` vectors, when complete, only bound a neighbourhood that
exceeds ``max_group_size``. Every ``merge`` and ``absorb`` is applied live
through the vault-level merge (``facet_merges`` plus aliases) with its own
undo; the dry run plans the calls and cost with no client and no change.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.spend import ESTIMATED_ONLY, SpendBudget, SpendLimitExceeded
from learnloop.clock import Clock
from learnloop.content.facet_identity.actions import (
    action_by_id,
    describe,
    lock_reasons,
    merge_registered_facets,
    recover_interrupted_actions,
)
from learnloop.content.facet_identity.grouping import FacetNode, neighbourhood_groups
from learnloop.content.facet_identity.judge import (
    Member,
    build_judge,
    build_request,
    caps_from_config,
    plan_estimate,
    resolve_route,
)
from learnloop.content.facet_identity.views import judge_view
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault, learning_object_facet_union
from learnloop.vault.paths import VaultPaths


def facets_in_scope(vault: LoadedVault, subject_id: str | None = None) -> list[str]:
    """Registered, non-retired canonical facets (of one subject, if given)."""

    registered = sorted(
        facet_id for facet_id, facet in vault.evidence_facets.items()
        if facet.status != "retired" and vault.canonical_facet_id(facet_id) == facet_id
    )
    if subject_id is None:
        return registered
    if subject_id not in vault.subjects:
        raise ValueError(f"Unknown subject {subject_id!r}")
    referenced: set[str] = set()
    for lo in vault.learning_objects.values():
        if subject_id in lo.subjects:
            referenced.update(vault.canonical_facet_id(facet) for facet in learning_object_facet_union(lo))
    for item in vault.practice_items.values():
        if subject_id in vault.subjects_for_item(item):
            referenced.update(vault.canonical_facet_id(facet) for facet in item.evidence_facets)
    return [facet_id for facet_id in registered if facet_id in referenced]


def _stored_vectors(vault: LoadedVault) -> dict[str, Any]:
    """Complete stored facet/definition vectors, or nothing (never a paid call)."""

    from learnloop.content.synthesis.graph_nomination import FACET_RECIPE, GraphNominator

    nominator = GraphNominator.for_review(vault)
    if nominator is None:
        return {}
    index = nominator.index(FACET_RECIPE)
    if index is None:
        return {}
    return {facet_id: index.vector(facet_id) for facet_id in index.ids}


def plan_dedupe(vault: LoadedVault, *, subject_id: str | None = None) -> tuple[list[Any], dict[str, Any]]:
    """The judge requests (one per bounded neighbourhood) and the grouping summary."""

    settings = vault.config.facet_identity
    facet_ids = facets_in_scope(vault, subject_id)
    nodes = [
        FacetNode(key=facet_id, payload=vault.evidence_facets[facet_id].model_dump(mode="json"),
                  concept=vault.evidence_facets[facet_id].concept_id, existing=True)
        for facet_id in facet_ids
    ]
    vectors = _stored_vectors(vault)
    grouping = neighbourhood_groups(
        nodes,
        concept_edges=[(edge.source, edge.target) for edge in vault.edges],
        vectors=vectors or None,
        top_k=settings.shortlist_top_k,
        max_group_size=settings.max_group_size,
        shortlist_edges=False,
    )
    titles = {concept_id: concept.title for concept_id, concept in vault.concepts.items()}
    requests = []
    for group in grouping.groups:
        members = []
        for facet_id in group:
            facet = vault.evidence_facets[facet_id]
            members.append(Member(
                label="", key=facet_id, subject_kind="facet", subject_id=facet_id, existing=True,
                view=judge_view(facet.model_dump(mode="json"), concept_title=titles.get(facet.concept_id or "")),
            ))
        requests.append(build_request(members, mode="consolidate"))
    summary = {"facets": len(facet_ids), **grouping.summary(), "stored_vectors": bool(vectors)}
    return requests, summary


def run_dedupe(
    root: Path,
    *,
    subject_id: str | None = None,
    dry_run: bool = False,
    caps_overrides: dict[str, Any] | None = None,
    price_per_million_input: float | None = None,
    price_per_million_output: float | None = None,
    client: Any = None,
    cancelled: Callable[[], bool] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Plan, judge and apply. Returns a JSON-safe report."""

    vault = load_vault(root)
    settings = vault.config.facet_identity
    if not settings.enabled:
        return {"status": "disabled", "reason": "facet_identity.enabled is false"}
    if vault.issues:
        return {"status": "invalid", "reason": f"vault has {len(vault.issues)} validation issues; run doctor first"}
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    recovered: list[dict[str, Any]] = []
    if dry_run:
        # No change at all: read the database as it is (no migration).
        repository = Repository.attach(sqlite_path, read_only=True)
    else:
        repository = Repository(sqlite_path)
        # Finish any merge or undo an earlier run left mid-flight first.
        recovered = recover_interrupted_actions(vault.root, repository, clock=clock)
        if recovered:
            vault = load_vault(root)
    requests, grouping = plan_dedupe(vault, subject_id=subject_id)
    caps = caps_from_config(settings, **(caps_overrides or {}))
    route = resolve_route(vault.config, client=client, input_price=price_per_million_input,
                          output_price=price_per_million_output)
    estimate = plan_estimate(requests, route.pricing, decider=route.decider)
    run_id = new_ulid()
    locked = lock_reasons(vault, repository, (member.key for request in requests for member in request.members))
    report: dict[str, Any] = {
        "status": "dry_run" if dry_run else "pending",
        "dry_run": dry_run,
        "run_id": run_id,
        "subject_id": subject_id,
        "grouping": grouping,
        "groups": [
            {"group_id": request.group_id, "facets": [member.key for member in request.members],
             "pairs": len(request.pairs())}
            for request in requests
        ],
        "route": route.as_dict(),
        "caps": caps.as_dict(),
        "estimate": asdict(estimate),
        "billing": "subscription" if route.subscription else "metered",
        "cost_basis": ESTIMATED_ONLY if route.subscription else "metered_caps",
        "locked_facets": sorted(locked),
        "lock_policy": "merge_locked_facets" if settings.merge_locked_facets else "refuse_locked",
        "actions": [],
        # Sets the judge decided that touch a locked facet, under the strict
        # lock policy (knowledge model §3.4): proposed to the owner, never
        # applied. A rerun with merge_locked_facets = true applies them from the
        # reused verdicts (no new call).
        "locked_proposals": [],
        "refused": [],
        "recovered": recovered,
    }
    budget = SpendBudget(caps, cancelled=cancelled, subscription=route.subscription)
    try:
        budget.check(estimate)
    except SpendLimitExceeded as exc:
        report.update(status="over_budget", reason=str(exc))
        return report
    except AIInterrupted:
        report["status"] = "cancelled"
        return report
    if route.problem is not None:
        report.update(status="unavailable", reason=route.problem)
        return report
    if dry_run or not requests:
        if not requests and not dry_run:
            report["status"] = "complete"
        return report

    judge, route = build_judge(vault, repository, owner_id=run_id, caps=caps, client=client, cancelled=cancelled,
                               input_price=price_per_million_input, output_price=price_per_million_output)
    report["route"] = route.as_dict()
    if judge is None:
        report.update(status="unavailable", reason=route.problem)
        return report
    outcomes = judge.run(requests)
    report["judged_groups"] = [outcome.summary() for outcome in outcomes]
    for outcome in outcomes:
        for decided in outcome.sets:
            keys = [decided.survivor, *decided.retired]
            result = merge_registered_facets(
                vault.root, repository,
                survivor=decided.survivor, retired=decided.retired, action=decided.action,
                absorb_as=decided.absorb_as, origin="dedupe", run_id=run_id,
                judge=outcome.judge, judge_model=outcome.judge_model, prompt_version=outcome.prompt_version,
                judgment_ids=outcome.judgments_for(keys),
                detail={"group_id": outcome.request.group_id, "rationale": decided.rationale},
                clock=clock,
            )
            if result["status"] == "applied":
                record = action_by_id(repository, result["action_id"])
                report["actions"].append({
                    **describe(record, load_vault(vault.root)),  # type: ignore[arg-type]
                    "lock_reasons": result.get("lock_reasons") or {},
                    "undo": f"learnloop facets undo {result['action_id']}",
                })
            elif result.get("reason") == "identity_locked":
                report["locked_proposals"].append(_locked_proposal(vault, decided, outcome, result))
            else:
                report["refused"].append({"survivor": decided.survivor, "retired": decided.retired, **result})
    report["charged"] = judge.charged()
    statuses = {outcome.status for outcome in outcomes}
    if statuses <= {"judged", "reused"}:
        report["status"] = "complete"
    elif any(outcome.error in {"AIInterrupted", "SpendCancelled"} for outcome in outcomes):
        report["status"] = "cancelled"
    elif any(outcome.error == "SpendLimitExceeded" for outcome in outcomes):
        report.update(status="over_budget", reason="a cap stopped the run; rerun to resume (judged groups are reused)")
    else:
        report["status"] = "partial"
    return report


def _locked_proposal(vault: LoadedVault, decided: Any, outcome: Any, result: dict[str, Any]) -> dict[str, Any]:
    def facet(facet_id: str) -> dict[str, str]:
        entry = vault.evidence_facets.get(facet_id)
        return {"id": facet_id, "claim": str(getattr(entry, "claim", "") or facet_id)}

    return {
        "status": "proposed_locked",
        "action": decided.action,
        "absorb_as": decided.absorb_as,
        "survivor": facet(decided.survivor),
        "retired": [facet(facet_id) for facet_id in decided.retired],
        "rationale": decided.rationale,
        "lock_reasons": result.get("lock_reasons") or {},
        "judge": outcome.judge,
        "judge_model": outcome.judge_model,
        "judgment_ids": outcome.judgments_for([decided.survivor, *decided.retired]),
        "apply": (
            "not applied: a locked facet's identity changes only with the owner's override "
            "([facet_identity] merge_locked_facets = true, then rerun dedupe; judged groups are reused)"
        ),
    }


__all__ = ["facets_in_scope", "plan_dedupe", "run_dedupe"]
