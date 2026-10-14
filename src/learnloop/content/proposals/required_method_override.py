"""The owner's change to an item's required method, through the proposal/confirm path.

Redesign 2026-10-14: the item's ``required_method`` field is the one
authority grading reads. A source-authored statement's requirement is decided
once at import (a ledgered judgment); this is how the owner changes that
decision, or any item's field: ``learnloop grading required-method`` persists
ONE pending ``update`` proposal (purpose ``required_method_override``, never
auto-applied) that ``learnloop accept`` applies.

The text agrees with the field without being read:

* a GENERATED statement gains the canonical sentence ("Use {name} in your
  answer.") with the field, and loses it when the field is cleared or renamed;
* a SOURCE statement (a textbook stem) is never rewritten: the field records
  ``statement = source, decided_by = owner``.

The proposal carries the item's content hash: an item changed before
acceptance is refused (run the command again). An accepted change moves the
item's content and so its assessment contract: attempts already graded keep
the contract (and required method) they were graded under.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.vault.models import LoadedVault
from learnloop.vault.required_method import (
    best_target,
    ensure_method_instruction,
    is_source_statement,
    method_targets,
    names_match,
    strip_method_instruction,
)

PROPOSAL_PURPOSE = "required_method_override"
OVERRIDE_VERSION = "required-method-override-v1"


def _input_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def override_payload(
    vault: LoadedVault,
    item_id: str,
    *,
    name: str | None = None,
    criterion_ids: Sequence[str] = (),
    clear: bool = False,
) -> dict[str, Any]:
    """The update one override proposes (``payload``), with the field before
    (``from``) and after (``to``). Raises ``ValueError`` on an unknown item or
    criterion, a missing name or criteria, or a clear with nothing to clear."""

    from learnloop.content.proposals.patches import compute_target_hash

    item = vault.practice_items.get(item_id)
    if item is None:
        raise ValueError(f"unknown practice item {item_id!r}")
    existing = item.required_method
    rubric = vault.rubric_for_item(item)
    known = [str(criterion.id) for criterion in (rubric.criteria if rubric is not None else ())]
    source = (getattr(existing, "statement", "instruction") == "source") if existing is not None \
        else is_source_statement(item)
    payload: dict[str, Any] = {"id": item.id, "learning_object_id": item.learning_object_id}
    if clear:
        if existing is None:
            raise ValueError(f"{item.id} has no required method to clear")
        if name is not None or criterion_ids:
            raise ValueError("--clear takes no method or criteria")
        new_field: dict[str, Any] | None = None
        prompt = item.prompt if source else strip_method_instruction(item.prompt, existing.name)
    else:
        method = " ".join(str(name or "").split())
        if not method:
            raise ValueError("name the required method (--method), or --clear it")
        criteria = [str(value) for value in dict.fromkeys(criterion_ids) if str(value).strip()]
        if not criteria and existing is not None and names_match(existing.name, method):
            criteria = list(existing.criterion_ids)
        if not criteria:
            raise ValueError("name the criteria that grade use of the method (--criterion)")
        unknown = [cid for cid in criteria if cid not in known]
        if unknown:
            raise ValueError(f"{item.id} has no criterion {', '.join(map(repr, unknown))} (known: {', '.join(known)})")
        targets = method_targets(vault, learning_object_id=item.learning_object_id, facet_ids=item.evidence_facets,
                                 capability=item.capability)
        target = best_target(method, targets)
        new_field = {"name": method, "criterion_ids": criteria, **(target.link() if target is not None else {})}
        if source:
            new_field.update(statement="source", decided_by="owner")
            prompt = item.prompt
        else:
            prompt = item.prompt
            if existing is not None and existing.name != method:
                prompt = strip_method_instruction(prompt, existing.name)
            prompt = ensure_method_instruction(prompt, method)
    payload["required_method"] = new_field
    if prompt != item.prompt:
        payload["prompt"] = prompt
    current = compute_target_hash(vault, "practice_item", item.id)
    if current is not None:
        payload["expected_target_hash"] = current
    return {
        "item_id": item.id,
        "statement": "source" if source else "instruction",
        "from": existing.model_dump(mode="json") if existing is not None else None,
        "to": new_field,
        "prompt_changed": "prompt" in payload,
        "payload": payload,
    }


def propose_required_method_override(
    vault: LoadedVault,
    repository: Repository,
    item_id: str,
    *,
    name: str | None = None,
    criterion_ids: Sequence[str] = (),
    clear: bool = False,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Persist the owner's override as one pending proposal; returns its id and change."""

    change = override_payload(vault, item_id, name=name, criterion_ids=criterion_ids, clear=clear)
    now = utc_now_iso(clock)
    agent_run_id = repository.insert_agent_run({
        "id": new_ulid(), "purpose": PROPOSAL_PURPOSE, "model": None, "provider": "owner",
        "prompt_template": PROPOSAL_PURPOSE, "prompt_version": OVERRIDE_VERSION,
        "input_context_hash": _input_hash(change["payload"]), "output_schema": "practice_item update",
        "started_at": now, "completed_at": now, "status": "completed",
    })
    row = {
        "id": new_ulid(), "client_item_id": f"required_method_override:{change['item_id']}",
        "item_type": "practice_item", "operation": "update",
        "target_entity_type": "practice_item", "target_entity_id": change["item_id"],
        "payload": change["payload"], "source_ref_ids": [],
        "audit": {"required_method_override": {
            "version": OVERRIDE_VERSION, "decided_by": "owner", "statement": change["statement"],
            "from": change["from"], "to": change["to"], "prompt_changed": change["prompt_changed"],
        }},
        "decision": "pending", "validation_status": "valid", "validation_errors": [],
        "created_at": now, "updated_at": now,
    }
    action = "clears" if change["to"] is None else "sets"
    summary = (
        f"The owner {action} the required method of {change['item_id']} "
        f"({'source statement, never rewritten' if change['statement'] == 'source' else 'the canonical sentence follows the field'}). "
        "Nothing is applied until it is accepted; an item changed before then is refused."
    )
    patch_id = repository.persist_proposal_batch({
        "id": new_ulid(), "agent_run_id": agent_run_id, "purpose": PROPOSAL_PURPOSE, "source_refs": [],
        "summary": summary, "created_at": now, "updated_at": now,
    }, [row])
    return {"status": "proposed", "proposal_id": patch_id, **{key: change[key] for key in
                                                             ("item_id", "statement", "from", "to", "prompt_changed")}}


__all__ = ["OVERRIDE_VERSION", "PROPOSAL_PURPOSE", "override_payload", "propose_required_method_override"]
