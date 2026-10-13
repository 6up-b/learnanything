"""Facet locks removed: what they protected becomes history (handoff §4, owner 2026-10-12).

Locks used to refuse rewording an evidenced facet in place, because that would
reinterpret its past evidence. Now a proposal apply that changes an existing
facet's meaning writes a facet version: ``version`` goes up, a ``reword``
action keeps the old entry, and the one-tap undo restores it. Growth-only
writes (aliases, examples) are not versions. The synthesis gate and the
bootstrap no longer refuse because a facet carries evidence; the
learning-object arm (an LO with attempts) still refuses a destructive op.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.content.facet_identity.actions import (
    FacetIdentityActionError,
    describe,
    facet_history,
    list_actions,
    undo_action,
)
from learnloop.content.proposals.patches import apply_accepted_items
from learnloop.content.synthesis.synthesis_gates import GateContext, GateItem, GateProposal, run_synthesis_gates
from learnloop.curriculum.curriculum_locks import Operation, can_apply
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml

from tests.helpers import seed_explanatory_source
from tests.test_facet_identity_actions import SHARED, _belief, _lock_shared, _vault_with_duplicate

_CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, 0, tzinfo=UTC))
OLD_CLAIM = "SVD factorizes into U, Sigma, V^T."
NEW_CLAIM = "Every real matrix factorizes as U Sigma V^T with orthogonal U, V and non-negative diagonal Sigma."


#: The facet's meaning (``facet_identity.authority.AUTHORITY_FIELDS``).
_MEANING_KEYS = {"kind", "title", "claim", "description", "preconditions", "postconditions", "applicability",
                 "non_goals", "positive_examples", "negative_examples"}


def _facet_update_proposal(repository, payload: dict, *, cited: bool = True) -> str:
    """A facet update proposal. One that changes the facet's meaning cites an
    explanatory span (``seed_explanatory_source``), as the facet-meaning
    chokepoint requires; ``cited=False`` leaves it uncited."""

    if cited and "meaning_support" not in payload and set(payload) & _MEANING_KEYS:
        citation = seed_explanatory_source(Path(repository.sqlite_path).parent, repository)
        payload = {**payload, "meaning_support": [{"from": "test", "citations": [citation]}]}
    now = utc_now_iso(_CLOCK)
    agent_run_id = repository.insert_agent_run({
        "purpose": "test_append", "provider": "learner", "provider_type": "learner",
        "started_at": now, "completed_at": now, "status": "completed",
    })
    item = {
        "client_item_id": "facet_update_1", "item_type": "facet", "operation": "update",
        "target_entity_type": "facet", "target_entity_id": payload["id"], "payload": payload,
        "source_ref_ids": [], "audit": {"origin": "test"}, "decision": "pending",
        "validation_status": "valid", "validation_errors": [], "depends_on_client_item_ids": [],
        "dependency_status": "pending", "created_at": now, "updated_at": now,
    }
    return repository.persist_proposal_batch({
        "agent_run_id": agent_run_id, "purpose": "test_facet_update", "summary": "reword",
        "source_refs": [], "status_cache": "pending", "created_at": now, "updated_at": now,
    }, [item])


def _entry(paths, facet_id: str) -> dict:
    return next(entry for entry in read_yaml(paths.facets_path)["facets"] if entry["id"] == facet_id)


def test_rewording_an_evidenced_facet_records_a_version_and_its_undo_restores_the_old_wording(tmp_path):
    paths, vault, repository = _vault_with_duplicate(tmp_path)
    _lock_shared(vault, repository)  # evidence in two surface groups: what used to lock it
    belief = _belief(repository)
    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM and _entry(paths, SHARED).get("version", 1) == 1

    patch_id = _facet_update_proposal(repository, {"id": SHARED, "claim": NEW_CLAIM})
    apply_accepted_items(paths.root, patch_id, clock=_CLOCK)

    assert _entry(paths, SHARED)["claim"] == NEW_CLAIM and _entry(paths, SHARED)["version"] == 2
    (record,) = list_actions(repository)
    assert record["action"] == "reword" and record["origin"] == "proposal" and record["status"] == "applied"
    assert record["survivor_facet_id"] == SHARED and record["retired_facet_ids"] == []
    assert record["proposal_id"] == patch_id
    assert record["before"]["facets"][SHARED]["claim"] == OLD_CLAIM  # the old text is kept
    assert record["detail"]["fields"] == ["claim"]
    assert SHARED in record["detail"]["evidence"]
    shown = describe(record, load_vault(paths.root))
    assert shown["reworded"] == {"from": OLD_CLAIM, "to": NEW_CLAIM, "from_version": 1, "to_version": 2,
                                 "fields": ["claim"]}
    assert shown["undoable"] is True
    assert [entry["id"] for entry in facet_history(repository, SHARED, load_vault(paths.root))] == [record["id"]]
    # A reword moves no evidence: the facet keeps its id and its beliefs.
    assert _belief(repository) == belief

    undone = undo_action(paths.root, repository, record["id"], clock=_CLOCK)
    assert undone["status"] == "undone" and undone["affected_learning_objects"] == []
    restored = _entry(paths, SHARED)
    assert restored["claim"] == OLD_CLAIM and restored.get("version", 1) == 1
    assert _belief(repository) == belief
    with pytest.raises(FacetIdentityActionError):
        undo_action(paths.root, repository, record["id"])


def test_a_growth_only_update_is_not_a_version(tmp_path):
    paths, vault, repository = _vault_with_duplicate(tmp_path)
    _lock_shared(vault, repository)
    examples = list(_entry(paths, SHARED).get("positive_examples") or [])
    patch_id = _facet_update_proposal(
        repository, {"id": SHARED, "positive_examples": [*examples, "a 3x2 example"], "aliases": ["svd"]},
    )
    apply_accepted_items(paths.root, patch_id, clock=_CLOCK)
    assert "a 3x2 example" in _entry(paths, SHARED)["positive_examples"]
    assert _entry(paths, SHARED).get("version", 1) == 1
    assert list_actions(repository) == []


def test_a_reword_undo_refuses_after_a_later_edit(tmp_path):
    paths, vault, repository = _vault_with_duplicate(tmp_path)
    apply_accepted_items(paths.root, _facet_update_proposal(repository, {"id": SHARED, "claim": NEW_CLAIM}),
                         clock=_CLOCK)
    apply_accepted_items(paths.root, _facet_update_proposal(repository, {"id": SHARED, "claim": "Third wording."}),
                         clock=_CLOCK)
    first, second = sorted(list_actions(repository), key=lambda row: row["before"]["facets"][SHARED]["version"])
    assert first["after"]["facets"][SHARED]["version"] == 2 and second["after"]["facets"][SHARED]["version"] == 3
    with pytest.raises(FacetIdentityActionError) as exc:
        undo_action(paths.root, repository, first["id"])
    assert exc.value.code == "changed_since"
    undo_action(paths.root, repository, second["id"], clock=_CLOCK)
    undo_action(paths.root, repository, first["id"], clock=_CLOCK)
    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM


def test_no_facet_arm_refuses_and_the_learning_object_arm_still_does(tmp_path):
    paths, vault, repository = _vault_with_duplicate(tmp_path)
    _lock_shared(vault, repository)
    vault = load_vault(paths.root)
    for op_type in ("facet_merge", "facet_split", "blueprint_identity_change", "deactivate"):
        result = can_apply(vault, repository, Operation(op_type=op_type, entity_type="facet", entity_id=SHARED))
        assert result.legal and result.lock_reasons == [] and result.requires_review
    item = vault.practice_items["pi_svd_define_001"]
    blocked = can_apply(vault, repository, Operation(
        op_type="blueprint_identity_change", entity_type="practice_item", entity_id=item.id))
    assert not blocked.legal
    assert [(reason.source, reason.entity_id) for reason in blocked.lock_reasons] == [
        ("attempts", item.learning_object_id)]


def test_the_gate_lets_a_facet_update_through_and_still_guards_a_practised_learning_object(tmp_path):
    paths, vault, repository = _vault_with_duplicate(tmp_path)
    _lock_shared(vault, repository)
    vault = load_vault(paths.root)
    lo_id = vault.practice_items["pi_svd_define_001"].learning_object_id
    proposal = GateProposal(items=[
        GateItem(client_item_id="f", item_type="facet", operation="update", entity_id=SHARED,
                 payload={"id": SHARED, "claim": NEW_CLAIM}, establishes_semantic=False),
        GateItem(client_item_id="lo", item_type="learning_object", operation="update", entity_id=lo_id,
                 payload={"id": lo_id}, establishes_semantic=False),
    ])
    report = run_synthesis_gates(proposal, GateContext(vault=vault, repository=repository))
    guarded = [diag for diag in report.diagnostics if diag.gate == "lock_guard"]
    assert [diag.entity_refs for diag in guarded] == [(lo_id,)]


def test_the_facet_inspector_shows_the_version_history_and_undoes_a_reword(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401 - registers methods
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    def call(ctx, name, params):
        spec = METHOD_REGISTRY[name]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    apply_accepted_items(paths.root, _facet_update_proposal(repository, {"id": SHARED, "claim": NEW_CLAIM}),
                         clock=_CLOCK)
    ctx = SidecarContext()
    ctx.load(paths.root)

    detail = call(ctx, "get_facet_detail", {"facetId": SHARED})
    assert "lock" not in detail and detail["facet"]["version"] == 2
    (entry,) = detail["history"]
    assert entry["action"] == "reword" and entry["undoable"] is True
    assert entry["reworded"]["from"] == OLD_CLAIM and entry["reworded"]["to"] == NEW_CLAIM

    undone = call(ctx, "undo_facet_identity_action", {"actionId": entry["id"]})
    assert undone["action"]["status"] == "undone"
    detail = call(ctx, "get_facet_detail", {"facetId": SHARED})
    assert detail["facet"]["claim"] == OLD_CLAIM and detail["facet"]["version"] == 1
    assert detail["history"][0]["status"] == "undone"
