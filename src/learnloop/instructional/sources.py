"""Passages and comparisons for real callers (spec_source_practice_and_probes_v1 §9.5).

* :func:`tutor_intent_for`: the tutor's grounding asks for ``remediate`` when
  the item's learning object has an active misconception (practice and
  feedback contexts), ``explain`` otherwise. Kill switch
  ``source_service.tutor_intents``.
* :func:`remediation_passage_provider`: the repair overlay's passages, ranked
  and verified by ``find_sources(intent="remediate")`` instead of the first
  linked span per facet; at most one per role. When verification cannot run,
  ``prescribe_remediation`` keeps today's choice. Kill switch
  ``source_service.remediation_passages``.
* :func:`propose_sources` and :func:`propose_comparison`: ``find_sources`` and
  ``compare_sources`` under a server-derived caller (the RPCs, the tutor's
  tools, the Reader's UI).

Retrieval is context: nothing here serves, grades or schedules.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.source_retrieval.compare import Comparison, compare_sources
from learnloop.source_retrieval.find_sources import SourceHits, find_sources_for_caller
from learnloop.source_retrieval.policy import CallerContext, PolicyRefused
from learnloop.source_retrieval.service_spend import service_spend
from learnloop.vault.models import LoadedVault, PracticeItem


class ServiceDisabled(PolicyRefused):
    def __init__(self, switch: str) -> None:
        super().__init__("source_service_disabled", f"source_service.{switch} is off")


def _require(vault: LoadedVault, switch: str | None = None) -> None:
    config = vault.config.source_service
    if not config.enabled:
        raise ServiceDisabled("enabled")
    if switch is not None and not getattr(config, switch):
        raise ServiceDisabled(switch)


def active_misconceptions(repository: Repository, learning_object_id: str) -> list[Any]:
    """The LO's active misconceptions (the diagnoser's overlay as recorded)."""

    return list(repository.misconceptions_for_learning_object(learning_object_id, statuses=("active",)))


def resolve_misconceptions(repository: Repository, target_hypotheses: Sequence[Mapping[str, Any]], *,
                           item: PracticeItem | None) -> list[Any]:
    """Remediation targets: named misconception refs (a named gap counts as the
    belief it names), else the item's LO's active ones."""

    from learnloop.instructional.valuation import named_gap_target

    found: list[Any] = []
    for ref in target_hypotheses or ():
        kind, ident = str(ref.get("kind") or ""), str(ref.get("id") or "")
        if kind == "named_gap" and ident:
            target, _reason = named_gap_target(repository, ident)
            kind, ident = (target.kind, target.id) if target is not None else ("", "")
        if kind == "misconception" and ident:
            record = repository.misconception(ident)
            if record is not None and all(getattr(other, "id", None) != record.id for other in found):
                found.append(record)
    if not found and item is not None:
        found = active_misconceptions(repository, item.learning_object_id)
    return found


def tutor_intent_for(vault: LoadedVault, repository: Repository, *, context: str,
                     item: PracticeItem | None) -> dict[str, Any] | None:
    config = vault.config.source_service
    if not (config.enabled and config.tutor_intents) or item is None or context not in ("practice", "feedback"):
        return None
    misconceptions = active_misconceptions(repository, item.learning_object_id)
    if not misconceptions:
        return None
    return {"intent": "remediate", "misconceptions": misconceptions}


def remediation_passage_provider(vault: LoadedVault, repository: Repository, *, misconception: Any,
                                 episode: Mapping[str, Any]) -> list[dict[str, Any]] | None:
    """At most one ranked, verified passage per role the overlay shows."""

    config = vault.config.source_service
    if not (config.enabled and config.remediation_passages):
        return None
    roles = [("target", getattr(misconception, "target_facet", None) if not isinstance(misconception, Mapping)
              else misconception.get("target_facet")),
             ("confused_with", getattr(misconception, "confused_with_facet", None)
              if not isinstance(misconception, Mapping) else misconception.get("confused_with_facet"))]
    roles = [(role, facet) for role, facet in roles if facet]
    if not roles:
        return None
    item_id = episode.get("primed_item_id")
    item = vault.practice_items.get(item_id) if item_id else None
    lo_id = getattr(misconception, "learning_object_id", None) if not isinstance(misconception, Mapping) \
        else misconception.get("learning_object_id")
    from learnloop.source_retrieval.find_sources import find_sources

    with service_spend(vault, repository):  # the shared daily cap (Codex re-review F2)
        hits = find_sources(
            vault, repository, "", policy="assisted_practice" if item is not None else "reading",
            intent="remediate", scope="teaching", learning_object_ids=[lo_id] if lo_id else [], item=item,
            misconceptions=[misconception], limit=len(roles), owner_id=f"rem_{episode.get('id')}",
        )
    if not hits.hits or not str(hits.manifest.get("verification", {}).get("status")) in ("verified", "cached"):
        return None
    return [{"role": role, "facet_id": facet, "extraction_id": hit["extraction_id"], "span_id": hit["span_id"],
             "basis": "ranked_verified"} for (role, facet), hit in zip(roles, hits.hits)]


def propose_sources(vault: LoadedVault, repository: Repository, query: str, *, caller: CallerContext,
                    intent: str = "explain", **kwargs: Any) -> SourceHits:
    _require(vault)
    item = vault.practice_items.get(caller.item_id) if caller.item_id else None
    misconceptions = kwargs.pop("misconceptions", None)
    if intent == "remediate" and misconceptions is None:
        misconceptions = resolve_misconceptions(repository, kwargs.get("target_hypotheses") or (), item=item)
    # Retrieval, its embeddings and rewrite, and verification all run under the
    # service's shared daily cap (Codex re-review F2).
    with service_spend(vault, repository, clock=kwargs.get("clock")):
        return find_sources_for_caller(vault, repository, query, caller=caller, intent=intent, item=item,
                                       misconceptions=misconceptions or (), **kwargs)


def propose_comparison(vault: LoadedVault, repository: Repository, query: str, *, caller: CallerContext,
                       **kwargs: Any) -> Comparison:
    _require(vault, "compare")
    # The whole comparison (its retrieval, verification and the comparison
    # call), not only its last call, is under the daily cap (re-review F2).
    with service_spend(vault, repository, clock=kwargs.get("clock")):
        return compare_sources(vault, repository, query, caller=caller, **kwargs)


__all__ = [
    "ServiceDisabled",
    "active_misconceptions",
    "propose_comparison",
    "propose_sources",
    "remediation_passage_provider",
    "resolve_misconceptions",
    "tutor_intent_for",
]
