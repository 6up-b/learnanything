"""The owner's change to an item's required method, through the proposal/confirm path.

Redesign 2026-10-14: the item's ``required_method`` field is the one
authority grading reads. A source-authored statement's requirement is decided
once at import (a ledgered judgment); this is how the owner changes that
decision, or any item's field: ``learnloop grading required-method`` persists
ONE pending ``update`` proposal (purpose ``required_method_override``, never
auto-applied) that ``learnloop accept`` applies.

The statement is never read and never edited (round 3): the instruction
("Use {name} in your answer.") is rendered from the field wherever the item
is shown or sent, so setting, renaming or clearing the field changes what is
rendered and nothing else (no text surgery that could cut a quotation:
review F18, F21). A SOURCE statement (a textbook stem) records ``statement =
source, decided_by = owner``.

The proposal carries the item's content hash: an item changed before
acceptance is refused (run the command again). An accepted change moves the
item's content and so its assessment contract: attempts already graded keep
the contract (and required method) they were graded under.

**The owner's verdict is ledgered** (implementation handoffs §0 rule 6;
review F16). Accepting the proposal appends one ``judge = owner`` row to
``judgment_ledger`` (task ``required_method_statement``, the same question
as the import's judgment: the item and the method), write-ahead in the
acceptance plan (:func:`owner_verdict_side_effect`, performed by
:func:`record_owner_verdict`) and idempotently: ``requires`` when the owner
sets the method, ``not_required`` when they clear it. It supersedes the
latest verdict on the same question (the import's judgment, or an earlier
owner verdict) and names the decision it replaced.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.vault.models import LoadedVault
from learnloop.vault.required_method import (
    best_target,
    is_source_statement,
    method_targets,
    names_match,
)

PROPOSAL_PURPOSE = "required_method_override"
OVERRIDE_VERSION = "required-method-override-v1"
#: The acceptance plan's side-effect kind (``apply_protocol``).
OWNER_VERDICT_EFFECT = "required_method_owner_verdict"
#: The owner's verdicts: the method is required, or it is not.
OWNER_REQUIRES = "requires"
OWNER_NOT_REQUIRED = "not_required"


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
    # The field alone changes; the statement is left exactly as it is.
    payload["required_method"] = new_field
    current = compute_target_hash(vault, "practice_item", item.id)
    if current is not None:
        payload["expected_target_hash"] = current
    return {
        "item_id": item.id,
        "statement": "source" if source else "instruction",
        "from": existing.model_dump(mode="json") if existing is not None else None,
        "to": new_field,
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
            "from": change["from"], "to": change["to"],
        }},
        "decision": "pending", "validation_status": "valid", "validation_errors": [],
        "created_at": now, "updated_at": now,
    }
    action = "clears" if change["to"] is None else "sets"
    summary = (
        f"The owner {action} the required method of {change['item_id']} "
        f"({'source statement, never rewritten' if change['statement'] == 'source' else 'its instruction is rendered from the field'}). "
        "Nothing is applied until it is accepted; an item changed before then is refused."
    )
    patch_id = repository.persist_proposal_batch({
        "id": new_ulid(), "agent_run_id": agent_run_id, "purpose": PROPOSAL_PURPOSE, "source_refs": [],
        "summary": summary, "created_at": now, "updated_at": now,
    }, [row])
    return {"status": "proposed", "proposal_id": patch_id, **{key: change[key] for key in
                                                             ("item_id", "statement", "from", "to")}}


def is_override_item(item: Mapping[str, Any]) -> bool:
    """Is this proposal item the owner's override (its audit, which only
    :func:`propose_required_method_override` writes)?"""

    audit = item.get("audit")
    return isinstance(audit, Mapping) and isinstance(audit.get(PROPOSAL_PURPOSE), Mapping)


def owner_verdict_side_effect(
    proposal_item_id: str, existing: Any, data: Mapping[str, Any],
) -> dict[str, Any]:
    """The acceptance plan's write of the owner's verdict for one override.

    ``existing`` is the item before the override, ``data`` the item after
    it. The row's id is fixed by the proposal item, so a recovery that
    re-runs the plan appends nothing twice.
    """

    before = getattr(existing, "required_method", None)
    after = data.get("required_method") or None
    if after is None and before is None:
        raise ValueError("an override that neither sets nor clears a required method")
    name = str(after["name"]) if after is not None else before.name
    statement = (str(after.get("statement") or "instruction") if after is not None
                 else getattr(before, "statement", "instruction"))
    return {
        "kind": OWNER_VERDICT_EFFECT,
        "row": {
            "id": f"rmowner_{proposal_item_id}",
            "practice_item_id": str(data.get("id") or existing.id),
            "method": " ".join(name.split()),
            "criterion_ids": [str(value) for value in (after or {}).get("criterion_ids") or ()],
            "statement": statement,
            "prompt": str(data.get("prompt") or ""),
            "cleared": after is None,
            "prior": before.model_dump(mode="json") if before is not None else None,
            "proposal_item_id": proposal_item_id,
        },
    }


def owner_input_hash(row: Mapping[str, Any]) -> str:
    """What the owner decided on: a source statement's verdict answers the
    import judgment's own question (its statement and method), so a lookup
    of that question finds it; a generated item's verdict is the field."""

    from learnloop.content.proposals.method_statement_judge import TASK, statement_input_hash

    if row["statement"] == "source":
        return statement_input_hash("source", str(row["prompt"]), str(row["method"]))
    identity = {"task": TASK, "question": OVERRIDE_VERSION, "statement": row["statement"],
                "prompt": str(row["prompt"]), "method": row["method"],
                "criterion_ids": list(row.get("criterion_ids") or ())}
    return "sha256:" + hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()


def record_owner_verdict(repository: Repository, row: Mapping[str, Any], created_at: str) -> str:
    """Append the owner's verdict (idempotent on the row's fixed id); returns its id."""

    from learnloop.content.proposals.method_statement_judge import TASK
    from learnloop.db.stores.judgments import append_judgment

    judgment_id = str(row["id"])
    with repository.atomic():
        connection = repository.connection()
        if connection.execute("SELECT 1 FROM judgment_ledger WHERE id = ?", (judgment_id,)).fetchone() is not None:
            return judgment_id
        latest = connection.execute(
            "SELECT id FROM judgment_ledger WHERE task = ? AND left_kind = 'practice_item' AND left_id = ? "
            "AND right_kind = 'required_method' AND right_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1",
            (TASK, str(row["practice_item_id"]), str(row["method"])),
        ).fetchone()
        prior = row.get("prior") or None
        rationale = {
            "decided_by": "owner", "statement": row["statement"], "method": row["method"],
            "criterion_ids": list(row.get("criterion_ids") or ()), "cleared": bool(row.get("cleared")),
            "prior": prior, "prior_judgment_id": (prior or {}).get("judgment_id"),
            "proposal_id": row.get("patch_id"), "proposal_item_id": row.get("proposal_item_id"),
            "version": OVERRIDE_VERSION,
        }
        append_judgment(
            connection, id=judgment_id, task=TASK, left_kind="practice_item", left_id=str(row["practice_item_id"]),
            right_kind="required_method", right_id=str(row["method"]), judge="owner",
            prompt_version=OVERRIDE_VERSION, input_hash=owner_input_hash(row),
            verdict=OWNER_NOT_REQUIRED if row.get("cleared") else OWNER_REQUIRES,
            supersedes_id=str(latest[0]) if latest is not None else None,
            rationale=json.dumps(rationale, sort_keys=True), created_at=created_at,
        )
    return judgment_id


__all__ = [
    "OVERRIDE_VERSION",
    "OWNER_NOT_REQUIRED",
    "OWNER_REQUIRES",
    "OWNER_VERDICT_EFFECT",
    "PROPOSAL_PURPOSE",
    "is_override_item",
    "override_payload",
    "owner_input_hash",
    "owner_verdict_side_effect",
    "propose_required_method_override",
    "record_owner_verdict",
]
