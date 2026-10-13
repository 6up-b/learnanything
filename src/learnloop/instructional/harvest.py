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

Both have ``--dry-run`` (no client is built, nothing is sent or written) and
stop at the money cap. Codex routes are ``estimated_only``.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import closing
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.content.authoring.source_exercise_import import import_source_exercise, verify_item_key
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_service import (
    VERIFIED_STATUSES,
    effective_key_status,
    is_exercise_import,
    spend_since,
)
from learnloop.instructional.exercises import exercise_candidates
from learnloop.instructional.validation import draft_validator
from learnloop.practice_index.catalog import facet_label, registered_facets
from learnloop.practice_index.coverage import coverage_targets
from learnloop.practice_index.retrieval import PracticeConstraints, find_practice
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


def harvest(vault: LoadedVault, repository: Repository, *, dry_run: bool, max_cost_usd: float | None,
            learning_object_ids: tuple[str, ...] = (), facet_ids: tuple[str, ...] = (),
            clients: Mapping[str, Any] | None = None, rerank_client: Any | None = None,
            embedder: Any | None = None, clock: Clock | None = None,
            on_progress: Callable[[str], None] | None = None) -> dict[str, Any]:
    targets = harvest_targets(vault, repository, learning_object_ids=learning_object_ids,
                              facet_ids=facet_ids, clock=clock)
    report: dict[str, Any] = {"dry_run": dry_run, "targets": targets, "imports": [], "skipped": []}
    if dry_run:
        for target in targets:
            constraints = PracticeConstraints(facet_ids=(target["facet_id"],),
                                              learning_object_ids=tuple(target["learning_object_ids"]))
            pool = exercise_candidates(vault, repository, _query(vault, target["facet_id"]), constraints,
                                       pool_size=vault.config.practice_index.candidate_pool, embedder=None)
            target["exercise_candidates"] = len(pool.candidates)
        report["status"] = "dry_run"
        report["note"] = ("Dry run: no client constructed, nothing sent or written. Each target costs one "
                          "rerank call, and each picked exercise one authoring call, one solution match and "
                          "the verifier ladder (panel solves, one equivalence judge, a span-support check when "
                          "the book's solution is found) plus the family judge's passes.")
        return report
    if max_cost_usd is None:
        raise ValueError("A live harvest needs --max-cost-usd (or --dry-run)")
    started = utc_now_iso(clock)
    for target in targets:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            spent = spend_since(connection, started, owner_kinds=None)
        if spent["usd"] >= max_cost_usd:
            report["status"] = "over_budget"
            report["reason"] = f"spent ${spent['usd']:.4f} of ${max_cost_usd:.4f}"
            break
        constraints = PracticeConstraints(facet_ids=(target["facet_id"],),
                                          learning_object_ids=tuple(target["learning_object_ids"]),
                                          kinds="source_exercises")
        result = find_practice(load_vault(vault.root), repository, _query(vault, target["facet_id"]), constraints,
                               origin="cli", caller={"kind": "harvest", "ref": target["facet_id"]},
                               exercise_arm=exercise_candidates, rerank_client=rerank_client, embedder=embedder,
                               clock=clock)
        for entry in result.get("source_exercises") or []:
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
        if not result.get("source_exercises"):
            report["skipped"].append({"facet_id": target["facet_id"],
                                      "reason": result.get("source_exercises_status") or "no exercise picked"})
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        report["spend"] = spend_since(connection, started, owner_kinds=None)
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
                rows.append({"practice_item_id": item.id, "key_status": status})
    return rows


def verify(vault: LoadedVault, repository: Repository, *, dry_run: bool, max_cost_usd: float | None,
           item_ids: tuple[str, ...] = (), clients: Mapping[str, Any] | None = None,
           clock: Clock | None = None) -> dict[str, Any]:
    targets = verification_targets(vault, repository, item_ids)
    report: dict[str, Any] = {"dry_run": dry_run, "targets": targets, "checks": []}
    if dry_run:
        report["status"] = "dry_run"
        report["note"] = ("Dry run: no client constructed, nothing sent or written. Each target costs a "
                          "solution match, the panel solves and one equivalence judge (plus a span-support "
                          "check when the book's solution is found).")
        return report
    if max_cost_usd is None:
        raise ValueError("A live verify needs --max-cost-usd (or --dry-run)")
    started = utc_now_iso(clock)
    for target in targets:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            spent = spend_since(connection, started, owner_kinds=None)
        if spent["usd"] >= max_cost_usd:
            report["status"] = "over_budget"
            report["reason"] = f"spent ${spent['usd']:.4f} of ${max_cost_usd:.4f}"
            break
        report["checks"].append(verify_item_key(vault.root, repository, target["practice_item_id"],
                                                trigger="verify", clients=clients, clock=clock))
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        report["spend"] = spend_since(connection, started, owner_kinds=None)
    report.setdefault("status", "complete")
    return report


__all__ = ["harvest", "harvest_targets", "verification_targets", "verify"]
