"""Owner-run batch work over textbook exercises (spec_source_practice_and_probes_v1 §7.2).

* ``harvest``: for facets ``coverage_report`` lists as thin (and, from S2a on,
  facets with open rival hypotheses), the exercise arm's judged candidates are
  imported with the verifier ladder run BEFORE writing. Bounded by money
  (``--max-cost-usd``) and by the judge's picks; there is no count of
  exercises. DL1's new-material admission bounds what reaches the learner.
* ``verify``: the ladder over exercise imports whose CURRENT content is not
  verified (historical Reader imports and items edited since their last check
  included), each result a ``reference_key_checks`` row bound to the content
  it checked.

Both have ``--dry-run`` (no client is built, nothing is sent or written; the
plan carries numerical estimates of calls, tokens and dollars) and a money cap
that is ENFORCED, not just checked between targets: one envelope for
``--max-cost-usd`` is shared by every paid request the command makes (the
rerank, each import's solution match, authoring, ladder and family judge),
and each request reserves its estimate before it is sent (Codex review F2).
The service's daily cap applies inside it. Codex routes are
``estimated_only``: never refused by money, their estimated tokens and
dollars reported.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import closing
from typing import Any

from learnloop.ai.spend import spend_envelopes
from learnloop.clock import Clock, utc_now_iso
from learnloop.content.authoring.source_exercise_import import (
    import_source_exercise,
    plan_import_cost,
    verify_item_key,
)
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_service import (
    VERIFIED_STATUSES,
    effective_key_status,
    imports_for_item,
    is_exercise_import,
    reference_content_hash,
    spend_since,
)
from learnloop.instructional.validation import draft_validator
from learnloop.instructional.wiring import disabled_reason, find_practice_injections
from learnloop.practice_index.catalog import facet_label, registered_facets
from learnloop.practice_index.coverage import coverage_targets
from learnloop.practice_index.paid import FRAMING_TOKENS
from learnloop.practice_index.retrieval import (
    MIXED_RERANK_OUTPUT_TOKENS,
    PracticeConstraints,
    find_practice,
)
from learnloop.source_retrieval.service_spend import batch_envelope, service_spend, subscription_providers
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault


def harvest_targets(vault: LoadedVault, repository: Repository, *, learning_object_ids: tuple[str, ...] = (),
                    facet_ids: tuple[str, ...] = (), extra_facets: tuple[str, ...] = (),
                    clock: Clock | None = None) -> list[dict[str, Any]]:
    """Thin facets (fewest admissible items first), narrowed by --lo/--facet."""

    targets = [target.as_dict() for target in coverage_targets(vault, repository, clock=clock)]
    facets = registered_facets(vault)
    known = {target["facet_id"] for target in targets}
    for facet_id in extra_facets:
        canonical = vault.canonical_facet_id(facet_id)
        if canonical in facets and canonical not in known:
            targets.append({"facet_id": canonical, "label": facet_label(facets[canonical]),
                            "learning_object_ids": [], "reason": "open rival hypotheses"})
            known.add(canonical)
    if facet_ids:
        # Facets the owner names are targets whether or not they are thin.
        wanted = [vault.canonical_facet_id(facet) for facet in facet_ids]
        by_id = {target["facet_id"]: target for target in targets}
        targets = []
        for facet_id in dict.fromkeys(wanted):
            if facet_id in by_id:
                targets.append(by_id[facet_id])
            elif facet_id in facets:
                lo_ids = sorted({item.learning_object_id for item in vault.practice_items.values()
                                 if facet_id in {vault.canonical_facet_id(f) for f in item.evidence_facets}})
                targets.append({"facet_id": facet_id, "label": facet_label(facets[facet_id]),
                                "learning_object_ids": lo_ids, "reason": "named by the owner"})
    if learning_object_ids:
        targets = [target for target in targets
                   if not target["learning_object_ids"] or set(target["learning_object_ids"]) & set(learning_object_ids)]
    return targets


def _query(vault: LoadedVault, facet_id: str) -> str:
    facet = vault.evidence_facets.get(facet_id)
    parts = [facet_label(facet) if facet is not None else facet_id]
    claim = getattr(facet, "claim", None) if facet is not None else None
    if claim:
        parts.append(str(claim))
    return " ".join(parts)[:1500]


def _spend(vault: LoadedVault, repository: Repository, started: str) -> dict[str, Any]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return spend_since(connection, started, owner_kinds=None,
                           price_per_million=vault.config.source_service.llm_price_per_million,
                           subscription_providers=subscription_providers(vault))


#: What each exact-filter verdict on a raw exercise means (``exercise_filter``).
_FILTER_MEANINGS = {
    "failed_unknown": "the judge quoted none of the requested facets in it",
    "facets": "the facets it quoted are not the requested ones",
    "facet_match_all": "it does not exercise every requested facet",
    "too_long": "it would take longer than allowed",
}


def _skip(facet_id: str, result: Mapping[str, Any]) -> dict[str, Any]:
    """Why a target imported nothing, in the report's own words (honest labels)."""

    if result.get("source_exercises_status"):
        return {"facet_id": facet_id, "reason": result["source_exercises_status"]}
    failed = dict(((result.get("signals") or {}).get("exercises") or {}).get("failed_filters") or {})
    if not failed:
        return {"facet_id": facet_id, "reason": "no exercise picked"}
    parts = "; ".join(f"{count} {reason}: {_FILTER_MEANINGS.get(reason, reason)}"
                      for reason, count in sorted(failed.items()))
    return {"facet_id": facet_id, "failed_filters": failed,
            "reason": f"no exercise passed the exact filters ({parts})"}


def _sum_plans(plans: list[dict[str, Any]]) -> dict[str, Any]:
    usd = [plan.get("usd") for plan in plans]
    return {"calls": sum(plan["calls"] for plan in plans), "tokens": sum(plan["tokens"] for plan in plans),
            "usd": None if any(value is None for value in usd) else round(sum(usd), 6)}


def harvest(vault: LoadedVault, repository: Repository, *, dry_run: bool, max_cost_usd: float | None,
            learning_object_ids: tuple[str, ...] = (), facet_ids: tuple[str, ...] = (),
            clients: Mapping[str, Any] | None = None, rerank_client: Any | None = None,
            embedder: Any | None = None, clock: Clock | None = None,
            on_progress: Callable[[str], None] | None = None) -> dict[str, Any]:
    switched_off = disabled_reason(vault, "exercise_arm")
    if switched_off is not None:
        return {"dry_run": dry_run, "targets": [], "imports": [], "skipped": [], "status": "disabled",
                "reason": switched_off}
    exercise_arm = find_practice_injections(vault)["exercise_arm"]
    targets = harvest_targets(vault, repository, learning_object_ids=learning_object_ids,
                              facet_ids=facet_ids, clock=clock)
    report: dict[str, Any] = {"dry_run": dry_run, "targets": targets, "imports": [], "skipped": []}
    if dry_run:
        price = vault.config.source_service.llm_price_per_million
        plans = []
        for target in targets:
            constraints = PracticeConstraints(facet_ids=(target["facet_id"],),
                                              learning_object_ids=tuple(target["learning_object_ids"]))
            pool = exercise_arm(vault, repository, _query(vault, target["facet_id"]), constraints,
                                pool_size=vault.config.practice_index.candidate_pool, embedder=None)
            target["exercise_candidates"] = len(pool.candidates)
            statements = [len(str(candidate.get("statement") or "")) for candidate in pool.candidates]
            rerank_tokens = sum(statements) + len(_query(vault, target["facet_id"])) + FRAMING_TOKENS \
                + MIXED_RERANK_OUTPUT_TOKENS
            rerank = {"calls": 1, "tokens": rerank_tokens,
                      "usd": None if price is None else round(rerank_tokens * float(price) / 1_000_000, 6)}
            imports = plan_import_cost(vault, statement_chars=max(statements, default=0),
                                       imports=len(pool.candidates))
            target["estimate"] = {"rerank": rerank, "imports": imports, "total": _sum_plans([rerank, imports])}
            plans.append(target["estimate"]["total"])
        report["estimate"] = {**_sum_plans(plans), "price_per_million": price,
                              "basis": "upper bound: every candidate the arm finds is picked and imported; "
                                       "metered dollars at source_service.llm_price_per_million (None: unpriced, "
                                       "metered routes are skipped); subscription routes are estimated_only"}
        report["status"] = "dry_run"
        report["note"] = ("Dry run: no client constructed, nothing sent or written. Each target costs one "
                          "rerank call, and each picked exercise one authoring call, one solution match and "
                          "the verifier ladder (panel solves, one equivalence judge, a span-support check when "
                          "the book's solution is found) plus the family judge's passes.")
        return report
    if max_cost_usd is None:
        raise ValueError("A live harvest needs --max-cost-usd (or --dry-run)")
    started = utc_now_iso(clock)
    envelope = batch_envelope("--max-cost-usd", max_cost_usd)
    # The batch cap and the service's shared daily cap bound every request,
    # the reranks included (Codex re-review F2).
    with spend_envelopes(envelope), service_spend(vault, repository, clock=clock):
        for target in targets:
            if envelope.remaining() <= 0 or envelope.report()["refused_requests"]:
                report["status"] = "over_budget"
                break
            constraints = PracticeConstraints(facet_ids=(target["facet_id"],),
                                              learning_object_ids=tuple(target["learning_object_ids"]),
                                              kinds="source_exercises")
            result = find_practice(load_vault(vault.root), repository, _query(vault, target["facet_id"]),
                                   constraints, origin="cli", caller={"kind": "harvest", "ref": target["facet_id"]},
                                   exercise_arm=exercise_arm, rerank_client=rerank_client,
                                   embedder=embedder, clock=clock)
            for entry in result.get("source_exercises") or []:
                if envelope.remaining() <= 0 or envelope.report()["refused_requests"]:
                    report["status"] = "over_budget"
                    break
                if on_progress is not None:
                    on_progress(f"importing {entry.get('label')} for {target['facet_id']}")
                validate = draft_validator(load_vault(vault.root), constraints, intent="practice", independent=True)
                outcome = import_source_exercise(
                    vault.root, repository, extraction_id=entry["extraction_id"], span_ids=entry["span_ids"],
                    caller="harvest", proposal_id=result["proposal_id"], clients=clients, validate=validate,
                    label=entry.get("label"), learning_object_hint=(target["learning_object_ids"] or [None])[0],
                    clock=clock,
                )
                report["imports"].append({key: outcome.get(key) for key in (
                    "import_id", "status", "practice_item_id", "key_status", "reason", "label")})
            if report.get("status") == "over_budget":
                break
            if not result.get("source_exercises"):
                report["skipped"].append(_skip(target["facet_id"], result))
    report["budget"] = envelope.report()
    if report.get("status") == "over_budget" or envelope.report()["refused_requests"]:
        report["status"] = "over_budget"
        report["reason"] = (f"the --max-cost-usd envelope (${max_cost_usd:.4f}) refused the next request: "
                            f"${report['budget']['metered_usd']:.4f} reserved or spent")
    report["spend"] = _spend(vault, repository, started)
    report.setdefault("status", "complete")
    return report


def verification_targets(vault: LoadedVault, repository: Repository,
                         item_ids: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    """Exercise imports whose current content is not verified."""

    rows = []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        for item in sorted(vault.practice_items.values(), key=lambda value: value.id):
            if item_ids and item.id not in item_ids:
                continue
            if item.status == "retired" or not is_exercise_import(connection, item):
                continue
            status = effective_key_status(connection, item)
            if status not in VERIFIED_STATUSES:
                row: dict[str, Any] = {"practice_item_id": item.id, "key_status": status}
                # A check an import left pending on this same content: this
                # check completes it (its marker cleared with the check row).
                pending = [entry for entry in imports_for_item(connection, item.id)
                           if (entry.get("verification") or {}).get("pending_check")
                           and entry.get("content_hash") == reference_content_hash(item)]
                if pending:
                    row["pending_import_id"] = pending[-1]["id"]
                rows.append(row)
    return rows


def verify(vault: LoadedVault, repository: Repository, *, dry_run: bool, max_cost_usd: float | None,
           item_ids: tuple[str, ...] = (), clients: Mapping[str, Any] | None = None,
           clock: Clock | None = None) -> dict[str, Any]:
    switched_off = disabled_reason(vault, "exercise_verification")
    if switched_off is not None:
        return {"dry_run": dry_run, "targets": [], "checks": [], "status": "disabled", "reason": switched_off}
    targets = verification_targets(vault, repository, item_ids)
    report: dict[str, Any] = {"dry_run": dry_run, "targets": targets, "checks": []}
    if dry_run:
        plans = []
        for target in targets:
            item = vault.practice_items[target["practice_item_id"]]
            plan = plan_import_cost(vault, statement_chars=len(item.prompt))
            # A check has no authoring request.
            authoring = next(row for row in plan["by_role"] if row["role"] == "exercise_authoring")
            plan["by_role"] = [row for row in plan["by_role"] if row["role"] != "exercise_authoring"]
            plan["calls"] -= authoring["calls"]
            plan["tokens"] -= authoring["tokens"]
            if plan["usd"] is not None:
                plan["usd"] = round(plan["tokens"] * float(plan["price_per_million"]) / 1_000_000, 6)
            target["estimate"] = plan
            plans.append(plan)
        report["estimate"] = {**_sum_plans(plans),
                              "price_per_million": vault.config.source_service.llm_price_per_million,
                              "basis": "upper bound per check: the solution match, the panel, the equivalence "
                                       "judge and a span-support check; subscription routes are estimated_only"}
        report["status"] = "dry_run"
        report["note"] = ("Dry run: no client constructed, nothing sent or written. Each target costs a "
                          "solution match, the panel solves and one equivalence judge (plus a span-support "
                          "check when the book's solution is found).")
        return report
    if max_cost_usd is None:
        raise ValueError("A live verify needs --max-cost-usd (or --dry-run)")
    started = utc_now_iso(clock)
    envelope = batch_envelope("--max-cost-usd", max_cost_usd)
    with spend_envelopes(envelope), service_spend(vault, repository, clock=clock):
        for target in targets:
            if envelope.remaining() <= 0 or envelope.report()["refused_requests"]:
                report["status"] = "over_budget"
                break
            report["checks"].append(verify_item_key(vault.root, repository, target["practice_item_id"],
                                                    trigger="verify", clients=clients, clock=clock,
                                                    import_id=target.get("pending_import_id")))
    report["budget"] = envelope.report()
    if report.get("status") == "over_budget" or envelope.report()["refused_requests"]:
        report["status"] = "over_budget"
        report["reason"] = (f"the --max-cost-usd envelope (${max_cost_usd:.4f}) refused the next request: "
                            f"${report['budget']['metered_usd']:.4f} reserved or spent")
    report["spend"] = _spend(vault, repository, started)
    report.setdefault("status", "complete")
    return report


__all__ = ["harvest", "harvest_targets", "verification_targets", "verify"]
