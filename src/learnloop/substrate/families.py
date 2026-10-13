"""Recoverable authored-family application.

The committed intent and decision precede vault writes. Recovery rolls forward
field-level patches, then appends membership events in the completion transaction.
Undo uses the inverse patches, never a stale whole-file backup. Conflicting
owner edits fail closed; unrelated fields and comments survive.
"""
from __future__ import annotations

from itertools import combinations
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import uuid4

from learnloop.ai.execution import content_key
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores.families import ensure_authored_identity, restore_proposal
from learnloop.db.stores.families import append_membership, create_proposal, record_revision, update_proposal_state, validate_authored_identity
from learnloop.db.stores.judgments import append_judgment
from learnloop.substrate.activities import canonical_hash, canonical_json, resolve_legacy_item
from learnloop.vault.loader import load_vault
from learnloop.vault.hashes import activity_family_hash
from learnloop.vault.models import ActivityFamily, LoadedVault, PracticeItem
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, yaml_to_string
from learnloop.vault_lock import vault_mutation_lock


FAMILY_JUDGE_PROMPTS = ("pf-same-target-direct-v1", "pf-same-target-counterexample-v1")
GROUPING_POLICY_VERSION = "unanimous-components-v1"


def family_operation_lock(root: Path):
    return vault_mutation_lock(root, purpose="activity_family")


def family_item_input(vault: LoadedVault, item: PracticeItem) -> dict[str, Any]:
    """Exact authored item and effective rubric judged, excluding regrouping."""
    payload = item.model_dump(mode="json")
    payload.pop("family_id", None)
    payload.pop("variant_relation", None)
    rubric = vault.rubric_for_item(item)
    return {"item": payload, "rubric": rubric.model_dump(mode="json") if rubric is not None else None}


def family_item_input_hash(vault: LoadedVault, item: PracticeItem) -> str:
    return content_key(family_item_input(vault, item))


def _safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if root.resolve() not in path.parents:
        raise ValueError("Family operation path escapes vault")
    return path


def _write_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(yaml_to_string(data))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        temporary.unlink(missing_ok=True)


def _patch_data(path: Path, patch: dict[str, Any], undo: bool) -> dict[str, Any]:
    if not path.exists() and not patch.get("family_file"):
        raise ValueError(f"Owner removed family member file: {path.name}")
    data = read_yaml(path) if path.exists() else {}
    before, after = patch["before"], patch["after"]
    source, target = (after, before) if undo else (before, after)
    for key in source.keys() | target.keys():
        present = key in data
        value = data.get(key)
        if (present, value) not in ((key in source, source.get(key)), (key in target, target.get(key))):
            raise ValueError(f"Owner edit conflicts with family operation: {path.name}:{key}")
        if key in target:
            data[key] = target[key]
        else:
            data.pop(key, None)
    return data


def _validate_judgments(connection: Any, vault: LoadedVault, family: ActivityFamily, members: Mapping[str, str],
                        judgment_ids: Sequence[str]) -> None:
    rows = []
    for judgment_id in judgment_ids:
        row = connection.execute(
            "SELECT j.* FROM judgment_ledger j WHERE j.id=? "
            "AND NOT EXISTS (SELECT 1 FROM judgment_ledger n WHERE n.supersedes_id=j.id)",
            (judgment_id,),
        ).fetchone()
        if row is not None:
            rows.append(row)
    anchor = min(members)
    if members[anchor] != "same_target":
        raise ValueError("Family anchor relation must be same_target")
    for left, right in combinations(sorted(members), 2):
        expected = {item_id: family_item_input_hash(vault, vault.practice_items[item_id])
                    for item_id in (left, right)}
        bound_rows = {}
        for row in rows:
            try:
                rationale = json.loads(row["rationale"])
            except (TypeError, ValueError):
                continue
            if not isinstance(rationale, dict) or rationale.get("item_hashes") != expected:
                continue
            result = rationale.get("result")
            if (isinstance(result, dict) and result.get("verdict") == "same"
                    and result.get("variant_relation") in {"same_target", "isomorph"}
                    and isinstance(result.get("idea_statement"), str) and result["idea_statement"].strip()
                    and isinstance(result.get("retrieval_target"), str) and result["retrieval_target"].strip()
                    and {row["left_id"], row["right_id"]} == {left, right}
                    and row["left_kind"] == row["right_kind"] == "practice_item"
                    and row["task"] == "same_target" and row["verdict"] == "same"
                    and row["judge"] == "llm" and row["judge_model"] and row["input_hash"]
                    and row["prompt_version"] in FAMILY_JUDGE_PROMPTS):
                if row["prompt_version"] in bound_rows:
                    raise ValueError("Family has duplicate judge passes for a pair")
                bound_rows[row["prompt_version"]] = result
        if set(bound_rows) != set(FAMILY_JUDGE_PROMPTS):
            raise ValueError(f"Family requires two agreeing judge passes for {left}, {right}")
        direct, counter = (bound_rows[version] for version in FAMILY_JUDGE_PROMPTS)
        if direct["variant_relation"] != counter["variant_relation"]:
            raise ValueError("Family judge passes disagree on variant relation")
        if left == anchor and members[right] != direct["variant_relation"]:
            raise ValueError("Family member relation differs from judged anchor relation")
        if (left, right) == tuple(sorted(members)[:2]) and (
                family.idea_statement != direct["idea_statement"]
                or family.retrieval_target != direct["retrieval_target"]):
            raise ValueError("Family wording differs from anchor pair judgment")


def apply_family(vault: LoadedVault, repository: Repository, family: ActivityFamily,
                 members: Mapping[str, str], *, proposal_id: str, judge: str = "owner",
                 rationale: str = "", judgment_ids: Sequence[str] = (),
                 clock: Clock | None = None) -> str:
    """Accept an authored record or a complete-link two-pass judged group.

    ``judge='verifier'`` requires persisted pair judgments; ``owner`` records
    explicit authorship. A repeated proposal id resumes, never accepts twice.
    """
    with family_operation_lock(vault.root):
        with repository.connection() as connection:
            _restore_proposals(connection)
            existing = connection.execute("SELECT * FROM family_proposals WHERE id=?", (proposal_id,)).fetchone()
        if existing:
            previous = json.loads(existing["plan_json"])
            previous_members = {member["item_id"]: member["variant_relation"] for member in previous["members"]}
            if previous["family"] != family.model_dump(mode="json") or previous_members != dict(members):
                raise ValueError("Proposal id already belongs to another family operation")
            _recover(vault, repository, clock)
            return proposal_id
        _recover(vault, repository, clock)
        current = load_vault(vault.root)
        if not members:
            raise ValueError("A family requires members")
        if judge not in {"owner", "verifier"}:
            raise ValueError("Family acceptance judge must be owner or verifier")
        if judge == "verifier" and len(members) < 2:
            raise ValueError("Automatic families require at least two judged members")
        if not family.id or Path(family.id).name != family.id or family.id in {".", ".."}:
            raise ValueError("Family id must be a single safe path component")
        now = utc_now_iso(clock)
        lo = current.learning_objects[family.learning_object_id]
        paths = VaultPaths(current.root, current.config)
        family_path = paths.activity_family_path(lo.subjects[0], family.id)
        _safe_path(current.root, str(family_path.relative_to(current.root)))
        if family_path.exists() or family.id in current.activity_families:
            raise ValueError("Apply creates a new authored family; identity already exists")
        plan: dict[str, Any] = {
            "family": family.model_dump(mode="json"), "family_hash": activity_family_hash(family),
            "members": [], "judgment_ids": list(judgment_ids),
            "patches": [{"path": str(family_path.relative_to(current.root)), "before": {},
                         "after": family.model_dump(mode="json"), "family_file": True}],
        }
        for item_id, relation in sorted(members.items()):
            item = current.practice_items[item_id]
            if item.learning_object_id != family.learning_object_id or item.family_id is not None:
                raise ValueError("Members must be unfamilied items of the family's LO")
            PracticeItem.model_validate({**item.model_dump(), "family_id": family.id, "variant_relation": relation})
            matches = list((current.root / "subjects").glob(f"*/practice-items/{item_id}.yaml"))
            if len(matches) != 1:
                raise ValueError(f"Expected one authored item file: {item_id}")
            path = matches[0]
            data = read_yaml(path)
            plan["patches"].append({
                "path": str(path.relative_to(current.root)),
                "before": {k: data[k] for k in ("family_id", "variant_relation") if k in data},
                "after": {"family_id": family.id, "variant_relation": relation},
            })
            resolved = resolve_legacy_item(current, repository, item, purpose="practice", clock=clock)
            plan["members"].append({"item_id": item_id, "card_id": resolved.card_id,
                                    "variant_relation": relation,
                                    "input_hash": family_item_input_hash(current, item)})
        with repository.connection() as connection:
            validate_authored_identity(connection, family.id)
            if judge == "verifier":
                _validate_judgments(connection, current, family, members, judgment_ids)
            decision = append_judgment(
                connection, task="family_decision", left_kind="family_proposal", left_id=proposal_id,
                judge=judge, input_hash=canonical_hash(plan), verdict="accept",
                rationale=canonical_json({"version": 1, "reason": rationale, "plan": plan}),
                prompt_version=GROUPING_POLICY_VERSION if judge == "verifier" else None,
                created_at=now,
            )
            plan["decision_id"] = decision
            create_proposal(connection, proposal_id=proposal_id, family_id=family.id,
                            plan_json=canonical_json(plan), created_at=now)
        _recover(vault, repository, clock)
    return proposal_id


def _validate_attach_judgments(connection: Any, vault: LoadedVault, family: ActivityFamily, item_id: str,
                               relation: str, judgment_ids: Sequence[str]) -> None:
    """Complete-link: the new item judged ``same`` by both passes with every member.

    The passes must agree on the relation, and the relation with the family's
    ``same_target`` anchor is the one the item joins with (the rule
    :func:`_validate_judgments` enforces for automatic families).
    """
    members = sorted(other.id for other in vault.practice_items.values()
                     if other.family_id == family.id and other.status != "retired")
    if not members:
        raise ValueError("Attach requires a family with current members")
    rows = []
    for judgment_id in judgment_ids:
        row = connection.execute(
            "SELECT j.* FROM judgment_ledger j WHERE j.id=? "
            "AND NOT EXISTS (SELECT 1 FROM judgment_ledger n WHERE n.supersedes_id=j.id)",
            (judgment_id,),
        ).fetchone()
        if row is not None:
            rows.append(row)
    anchors = [member for member in members
               if vault.practice_items[member].variant_relation == "same_target"] or members
    anchor = anchors[0]
    new_hash = family_item_input_hash(vault, vault.practice_items[item_id])
    for member in members:
        expected = {item_id: new_hash, member: family_item_input_hash(vault, vault.practice_items[member])}
        bound: dict[str, dict[str, Any]] = {}
        for row in rows:
            try:
                rationale = json.loads(row["rationale"])
            except (TypeError, ValueError):
                continue
            if not isinstance(rationale, dict) or rationale.get("item_hashes") != expected:
                continue
            result = rationale.get("result")
            if (isinstance(result, dict) and result.get("verdict") == "same"
                    and result.get("variant_relation") in {"same_target", "isomorph"}
                    and {row["left_id"], row["right_id"]} == {item_id, member}
                    and row["left_kind"] == row["right_kind"] == "practice_item"
                    and row["task"] == "same_target" and row["verdict"] == "same"
                    and row["judge"] == "llm" and row["judge_model"] and row["input_hash"]
                    and row["prompt_version"] in FAMILY_JUDGE_PROMPTS):
                if row["prompt_version"] in bound:
                    raise ValueError("Attach has duplicate judge passes for a pair")
                bound[row["prompt_version"]] = result
        if set(bound) != set(FAMILY_JUDGE_PROMPTS):
            raise ValueError(f"Attach requires two agreeing judge passes for {item_id}, {member}")
        direct, counter = (bound[version] for version in FAMILY_JUDGE_PROMPTS)
        if direct["variant_relation"] != counter["variant_relation"]:
            raise ValueError("Attach judge passes disagree on variant relation")
        if member == anchor and direct["variant_relation"] != relation:
            raise ValueError("Attached relation differs from the judged anchor relation")


def attach_to_family(vault: LoadedVault, repository: Repository, family_id: str, item_id: str,
                     relation: str, *, proposal_id: str, judgment_ids: Sequence[str],
                     rationale: str = "", clock: Clock | None = None) -> str:
    """Add one unfamilied item to an EXISTING family (canonical sources S1, §7.4).

    ``apply_family`` only creates families; this is PF publication's pattern
    (``append_membership`` with the decision's ledger id) under
    ``apply_family``'s recover and undo discipline: the plan is recorded in the
    ledger and ``family_proposals`` before the YAML patch to ``family_id`` and
    ``variant_relation``, recovery rolls it forward, and ``undo_family``
    removes the membership. Only ``same_target`` or ``isomorph`` members join
    this way, on a complete-link two-pass judgment with every member.
    """
    if relation not in {"same_target", "isomorph"}:
        raise ValueError("Only same_target or isomorph members attach without generation")
    with family_operation_lock(vault.root):
        with repository.connection() as connection:
            _restore_proposals(connection)
            existing = connection.execute("SELECT * FROM family_proposals WHERE id=?", (proposal_id,)).fetchone()
        if existing:
            _recover(vault, repository, clock)
            return proposal_id
        _recover(vault, repository, clock)
        current = load_vault(vault.root)
        family = current.activity_families.get(family_id)
        if family is None:
            raise ValueError(f"Unknown activity family {family_id}")
        item = current.practice_items.get(item_id)
        if item is None:
            raise ValueError(f"Unknown practice item {item_id}")
        if item.learning_object_id != family.learning_object_id:
            raise ValueError("The item's learning object differs from the family's")
        if item.family_id is not None:
            raise ValueError("The item already belongs to a family")
        PracticeItem.model_validate({**item.model_dump(), "family_id": family.id, "variant_relation": relation})
        matches = list((current.root / "subjects").glob(f"*/practice-items/{item_id}.yaml"))
        if len(matches) != 1:
            raise ValueError(f"Expected one authored item file: {item_id}")
        path = matches[0]
        data = read_yaml(path)
        resolved = resolve_legacy_item(current, repository, item, purpose="practice", clock=clock)
        plan: dict[str, Any] = {
            "mode": "attach",
            "family": family.model_dump(mode="json"), "family_hash": activity_family_hash(family),
            "members": [{"item_id": item_id, "card_id": resolved.card_id, "variant_relation": relation,
                         "input_hash": family_item_input_hash(current, item)}],
            "judgment_ids": list(judgment_ids),
            "patches": [{
                "path": str(path.relative_to(current.root)),
                "before": {k: data[k] for k in ("family_id", "variant_relation") if k in data},
                "after": {"family_id": family.id, "variant_relation": relation},
            }],
        }
        now = utc_now_iso(clock)
        with repository.connection() as connection:
            _validate_attach_judgments(connection, current, family, item_id, relation, judgment_ids)
            decision = append_judgment(
                connection, task="family_decision", left_kind="family_proposal", left_id=proposal_id,
                judge="verifier", input_hash=canonical_hash(plan), verdict="accept",
                rationale=canonical_json({"version": 1, "reason": rationale, "plan": plan}),
                prompt_version=GROUPING_POLICY_VERSION, created_at=now,
            )
            plan["decision_id"] = decision
            create_proposal(connection, proposal_id=proposal_id, family_id=family.id,
                            plan_json=canonical_json(plan), created_at=now)
        _recover(vault, repository, clock)
    return proposal_id


def undo_family(vault: LoadedVault, repository: Repository, proposal_id: str, *,
                clock: Clock | None = None) -> None:
    with family_operation_lock(vault.root):
        with repository.connection() as connection:
            _restore_proposals(connection)
            row = connection.execute("SELECT * FROM family_proposals WHERE id=?", (proposal_id,)).fetchone()
            if row is None:
                raise ValueError("Unknown family proposal")
            if row["state"] == "undone":
                return
            if row["state"] not in {"applying", "applied", "undoing"}:
                raise ValueError("Only accepted family proposals can be undone")
            plan = json.loads(row["plan_json"])
            # Preflight every inverse patch before recording an undo intent.
            for patch in plan["patches"]:
                if not patch.get("family_file"):
                    _patch_data(_safe_path(vault.root, patch["path"]), patch, True)
            if row["state"] != "undoing":
                plan["undo_decision_id"] = append_judgment(
                    connection, task="family_decision", left_kind="family_proposal", left_id=proposal_id,
                    judge="owner", input_hash=canonical_hash(plan), verdict="undo",
                    rationale=canonical_json({"version": 1, "acceptance_id": plan["decision_id"]}),
                    supersedes_id=plan["decision_id"], created_at=utc_now_iso(clock),
                )
            update_proposal_state(connection, proposal_id=proposal_id,
                                  state="undoing", plan_json=canonical_json(plan))
        _recover(vault, repository, clock, proposal_id=proposal_id)


def recover_family_operations(vault: LoadedVault, repository: Repository, *,
                              clock: Clock | None = None) -> None:
    with family_operation_lock(vault.root):
        _recover(vault, repository, clock)


def sync_authored_families(vault: LoadedVault, repository: Repository, *,
                          clock: Clock | None = None) -> None:
    """Snapshot owner-edited revisions without minting another family identity."""
    with family_operation_lock(vault.root):
        _recover(vault, repository, clock)
        with repository.connection() as connection:
            for family in vault.activity_families.values():
                record_revision(connection, family_id=family.id,
                                spec_json=canonical_json(family.model_dump(mode="json")),
                                title=family.idea_statement, created_at=utc_now_iso(clock))


def _restore_proposals(connection: Any) -> None:
    """Rebuild disposable workflow cache from immutable decisions and completions."""
    accepts = connection.execute(
        "SELECT * FROM judgment_ledger WHERE task='family_decision' "
        "AND left_kind='family_proposal' AND verdict='accept' ORDER BY created_at,id"
    ).fetchall()
    seen = set()
    for decision in accepts:
        proposal_id = decision["left_id"]
        if proposal_id in seen:
            raise ValueError("Multiple acceptance decisions for family proposal")
        seen.add(proposal_id)
        try:
            envelope = json.loads(decision["rationale"])
            plan = envelope["plan"]
            if envelope["version"] != 1 or canonical_hash(plan) != decision["input_hash"]:
                raise ValueError("Invalid immutable family plan")
            ActivityFamily.model_validate(plan["family"])
        except (TypeError, KeyError, ValueError) as exc:
            raise ValueError("Family acceptance has no valid immutable ledger plan") from exc
        plan["decision_id"] = decision["id"]
        undos = connection.execute(
            "SELECT * FROM judgment_ledger WHERE supersedes_id=? AND task='family_decision' "
            "AND left_kind='family_proposal' AND left_id=? AND verdict='undo' AND judge='owner'",
            (decision["id"], proposal_id),
        ).fetchall()
        if len(undos) > 1:
            raise ValueError("Multiple undo decisions for family proposal")
        undo = undos[0] if undos else None
        if undo is not None:
            if undo["input_hash"] != canonical_hash(plan):
                raise ValueError("Family undo does not bind immutable acceptance")
            plan["undo_decision_id"] = undo["id"]
        action = "remove" if undo else "add"
        completed = {row["card_id"] for row in connection.execute(
            "SELECT card_id FROM activity_family_membership_events WHERE proposal_id=? AND action=? AND judgment_id=?",
            (proposal_id, action, undo["id"] if undo else decision["id"]),
        )}
        complete = completed == {member["card_id"] for member in plan["members"]}
        state = ("undone" if complete else "undoing") if undo else ("applied" if complete else "applying")
        restore_proposal(connection, proposal_id=proposal_id,
                         family_id=plan["family"]["id"], state=state,
                         plan_json=canonical_json(plan), created_at=decision["created_at"])


def _recover(vault: LoadedVault, repository: Repository, clock: Clock | None,
             *, proposal_id: str | None = None) -> None:
    with repository.connection() as connection:
        _restore_proposals(connection)
        rows = connection.execute(
            "SELECT * FROM family_proposals WHERE state IN ('applying','undoing') ORDER BY created_at,id"
        ).fetchall()
    for row in rows:
        if proposal_id is not None and row["id"] != proposal_id:
            continue
        plan = json.loads(row["plan_json"])
        undo = row["state"] == "undoing"
        with repository.connection() as connection:
            decision = connection.execute(
                "SELECT * FROM judgment_ledger WHERE id=?",
                (plan["undo_decision_id" if undo else "decision_id"],),
            ).fetchone()
            if (decision is None or decision["task"] != "family_decision"
                    or decision["left_kind"] != "family_proposal"
                    or decision["left_id"] != row["id"]
                    or decision["verdict"] != ("undo" if undo else "accept")):
                raise ValueError("Family operation has no authoritative ledger decision")
        if not undo:
            current = load_vault(vault.root)
            for member in plan["members"]:
                item = current.practice_items.get(member["item_id"])
                if item is None or family_item_input_hash(current, item) != member["input_hash"]:
                    raise ValueError(
                        "Owner changed judged item content during family application; "
                        f"run learnloop families undo {row['id']} --vault {vault.root}"
                    )
        updates = []
        for patch in plan["patches"]:
            path = _safe_path(vault.root, patch["path"])
            if undo and patch.get("family_file"):
                # Family records are authored content: retain the record on undo.
                # Membership is removed, not the owner's idea or revision history.
                continue
            updates.append((path, _patch_data(path, patch, undo)))
        for path, data in updates:
            _write_atomic(path, data)
        current = load_vault(vault.root)
        with repository.connection() as connection:
            family = ActivityFamily.model_validate(plan["family"])
            authored = current.activity_families.get(family.id)
            if authored is not None:
                record_revision(connection, family_id=family.id,
                                spec_json=canonical_json(authored.model_dump(mode="json")),
                                title=authored.idea_statement, created_at=utc_now_iso(clock))
            else:
                # Abort may precede even the first file write. Establish identity,
                # not a stale authored revision, for the compensating raw event.
                ensure_authored_identity(connection, family_id=family.id,
                                         title=family.idea_statement, created_at=utc_now_iso(clock))
            for member in plan["members"]:
                append_membership(
                    connection, family_id=family.id, member=member, action="remove" if undo else "add",
                    proposal_id=row["id"], judgment_id=plan["undo_decision_id" if undo else "decision_id"],
                    created_at=utc_now_iso(clock),
                )
            update_proposal_state(connection, proposal_id=row["id"],
                                  state="undone" if undo else "applied")
    refreshed = load_vault(vault.root)
    vault.practice_items = refreshed.practice_items
    vault.activity_families = refreshed.activity_families
