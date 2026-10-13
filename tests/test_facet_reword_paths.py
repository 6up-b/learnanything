"""Every supported path that rewords a facet keeps the old wording (Codex review of facet locks).

The stage made a proposal apply that changes an existing facet's meaning write
a facet version (a ``reword`` action with an undo). The review found three
gaps around it, each pinned here:

* F1: the desktop Library writes ``facets.yaml`` as plain text, so an owner
  edit of an evidenced facet's claim bypassed the version entirely. It now
  goes through the same locked, write-ahead reword record.
* F4: undoing a reword is the owner's verdict on that wording, so it appends
  to ``judgment_ledger`` (handoffs §0 rule 6), once, even across a crash.
* F5: ``version`` is server-managed for an existing facet. A payload's own
  ``version`` (stale or oversized) never overwrites it, so a later write can
  not break an earlier reword's undo.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from learnloop.clock import FrozenClock
from learnloop.content.facet_identity import actions as facet_actions
from learnloop.content.facet_identity.actions import (
    FacetIdentityActionError,
    facet_history,
    list_actions,
    recover_interrupted_actions,
    undo_action,
)
from learnloop.content.proposals.patches import apply_accepted_items
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, yaml_to_string

from tests.test_facet_identity_actions import SHARED, _belief, _lock_shared, _vault_with_duplicate
from tests.test_facet_rewords import NEW_CLAIM, OLD_CLAIM, _entry, _facet_update_proposal

_CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, 0, tzinfo=UTC))
THIRD_CLAIM = "A = U Sigma V^T, with the singular values on Sigma's diagonal in decreasing order."


def _ledger(repository, task: str = "facet_reword") -> list[dict]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = ? ORDER BY created_at, id", (task,),
        ).fetchall()
    return [dict(row) for row in rows]


# --- F5: version is server-managed --------------------------------------------------------


def test_a_stale_version_on_an_unchanged_meaning_keeps_the_current_version_and_the_undo(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    apply_accepted_items(paths.root, _facet_update_proposal(repository, {"id": SHARED, "claim": NEW_CLAIM}),
                         clock=_CLOCK)
    (reword,) = list_actions(repository)
    assert _entry(paths, SHARED)["version"] == 2

    # The same meaning, carrying the version the payload was drafted against.
    apply_accepted_items(
        paths.root, _facet_update_proposal(repository, {"id": SHARED, "claim": NEW_CLAIM, "version": 1}),
        clock=_CLOCK,
    )

    assert _entry(paths, SHARED)["version"] == 2  # not lowered
    assert [row["id"] for row in list_actions(repository)] == [reword["id"]]  # and not a version
    undone = undo_action(paths.root, repository, reword["id"], clock=_CLOCK)
    assert undone["status"] == "undone"
    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM and _entry(paths, SHARED).get("version", 1) == 1


def test_an_oversized_incoming_version_is_ignored_and_every_undo_still_applies(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    apply_accepted_items(
        paths.root, _facet_update_proposal(repository, {"id": SHARED, "claim": NEW_CLAIM, "version": 99}),
        clock=_CLOCK,
    )
    assert _entry(paths, SHARED)["version"] == 2  # one more than the facet's, whatever the payload says
    apply_accepted_items(
        paths.root, _facet_update_proposal(repository, {"id": SHARED, "claim": THIRD_CLAIM, "version": 1}),
        clock=_CLOCK,
    )
    assert _entry(paths, SHARED)["version"] == 3
    # Growth only, with a version of its own: not a version, and nothing moves.
    apply_accepted_items(
        paths.root, _facet_update_proposal(repository, {"id": SHARED, "aliases": ["svd"], "version": 50}),
        clock=_CLOCK,
    )
    assert _entry(paths, SHARED)["version"] == 3 and "svd" in _entry(paths, SHARED)["aliases"]

    first, second = sorted(list_actions(repository), key=lambda row: row["after"]["facets"][SHARED]["version"])
    assert (first["after"]["facets"][SHARED]["version"], second["after"]["facets"][SHARED]["version"]) == (2, 3)
    # The alias write changed the entry after the second reword, so its undo
    # refuses rather than overwrite it (the version stayed 3 either way).
    with pytest.raises(FacetIdentityActionError) as exc:
        undo_action(paths.root, repository, second["id"], clock=_CLOCK)
    assert exc.value.code == "changed_since"


def test_a_reword_after_a_reword_undoes_in_order_with_server_versions(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    for claim, version in ((NEW_CLAIM, 7), (THIRD_CLAIM, 2)):
        apply_accepted_items(
            paths.root, _facet_update_proposal(repository, {"id": SHARED, "claim": claim, "version": version}),
            clock=_CLOCK,
        )
    first, second = sorted(list_actions(repository), key=lambda row: row["after"]["facets"][SHARED]["version"])
    assert _entry(paths, SHARED)["version"] == 3
    undo_action(paths.root, repository, second["id"], clock=_CLOCK)
    assert _entry(paths, SHARED)["claim"] == NEW_CLAIM and _entry(paths, SHARED)["version"] == 2
    undo_action(paths.root, repository, first["id"], clock=_CLOCK)
    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM and _entry(paths, SHARED).get("version", 1) == 1


# --- F4: a reword undo is the owner's verdict ----------------------------------------------


def test_undoing_a_reword_appends_the_owners_verdict_to_the_judgment_ledger(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    apply_accepted_items(paths.root, _facet_update_proposal(repository, {"id": SHARED, "claim": NEW_CLAIM}),
                         clock=_CLOCK)
    (reword,) = list_actions(repository)
    assert _ledger(repository) == []

    undone = undo_action(paths.root, repository, reword["id"], clock=_CLOCK)

    (verdict,) = _ledger(repository)
    assert verdict["judge"] == "owner" and verdict["verdict"] == "rejected"
    assert (verdict["left_kind"], verdict["left_id"]) == ("facet", SHARED)
    assert verdict["right_kind"] == "facet_wording" and verdict["right_id"]
    assert undone["owner_judgment_ids"] == [verdict["id"]]
    assert reword["id"] in verdict["rationale"] and NEW_CLAIM not in verdict["right_id"]
    # Keyed to the wording rejected: a later, different wording is a different question.
    apply_accepted_items(paths.root, _facet_update_proposal(repository, {"id": SHARED, "claim": THIRD_CLAIM}),
                         clock=_CLOCK)
    later = next(row for row in list_actions(repository) if row["id"] != reword["id"])
    undo_action(paths.root, repository, later["id"], clock=_CLOCK)
    first, second = _ledger(repository)
    assert first["right_id"] != second["right_id"] and second["left_id"] == SHARED


def test_an_interrupted_reword_undo_records_the_verdict_once(tmp_path, monkeypatch):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    apply_accepted_items(paths.root, _facet_update_proposal(repository, {"id": SHARED, "claim": NEW_CLAIM}),
                         clock=_CLOCK)
    (reword,) = list_actions(repository)

    real_write = facet_actions._write_facets

    def crash(*_args, **_kwargs):
        raise RuntimeError("power cut before facets.yaml was restored")

    monkeypatch.setattr(facet_actions, "_write_facets", crash)
    with pytest.raises(RuntimeError):
        undo_action(paths.root, repository, reword["id"], clock=_CLOCK)
    assert facet_actions.action_by_id(repository, reword["id"])["status"] == "undoing"
    assert len(_ledger(repository)) == 1  # committed with the intent
    assert _entry(paths, SHARED)["claim"] == NEW_CLAIM

    monkeypatch.setattr(facet_actions, "_write_facets", real_write)
    retried = undo_action(paths.root, repository, reword["id"], clock=_CLOCK)

    assert retried["status"] == "undone" and retried.get("recovered") is True
    assert len(_ledger(repository)) == 1
    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM


# --- F1: the Library editor writes facets.yaml through the reword record --------------------


def _sidecar(paths):
    import learnloop_sidecar.handlers  # noqa: F401 - registers methods
    from learnloop_sidecar.context import SidecarContext

    ctx = SidecarContext()
    ctx.load(paths.root)
    return ctx


def _call(ctx, name, params):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _edited_registry(paths, **changes) -> str:
    """The owner's edit in the Library: facets.yaml's text with one facet changed."""

    document = read_yaml(paths.facets_path)
    for entry in document["facets"]:
        if entry["id"] == SHARED:
            entry.update(changes)
    return yaml_to_string(document)


def test_a_library_edit_that_rewords_an_evidenced_facet_records_a_version_with_undo(tmp_path):
    paths, vault, repository = _vault_with_duplicate(tmp_path)
    _lock_shared(vault, repository)
    belief = _belief(repository)
    ctx = _sidecar(paths)
    rel_path = str(paths.facets_path.relative_to(paths.root))
    assert _entry(paths, SHARED).get("version", 1) == 1

    saved = _call(ctx, "write_vault_file", {"path": rel_path, "body": _edited_registry(paths, claim=NEW_CLAIM)})

    # The saved text is what the editor shows next: the version the server wrote.
    shown = next(entry for entry in read_yaml(paths.facets_path)["facets"] if entry["id"] == SHARED)
    assert shown["claim"] == NEW_CLAIM and shown["version"] == 2
    assert saved["body"] == paths.facets_path.read_text(encoding="utf-8")
    (record,) = list_actions(repository)
    assert record["action"] == "reword" and record["status"] == "applied"
    assert record["origin"] == "registry" and record["judge"] == "owner"
    assert record["detail"]["via"] == "library" and record["detail"]["fields"] == ["claim"]
    assert record["before"]["facets"][SHARED]["claim"] == OLD_CLAIM  # the replaced text is kept
    assert SHARED in record["detail"]["evidence"]
    history = _call(ctx, "get_facet_detail", {"facetId": SHARED})["history"]
    assert [(entry["id"], entry["undoable"]) for entry in history] == [(record["id"], True)]
    assert _belief(repository) == belief

    undone = _call(ctx, "undo_facet_identity_action", {"actionId": record["id"]})

    assert undone["action"]["status"] == "undone"
    restored = _entry(paths, SHARED)
    assert restored["claim"] == OLD_CLAIM and restored.get("version", 1) == 1
    assert len(_ledger(repository)) == 1  # the undo is the owner's verdict (F4)
    assert _belief(repository) == belief


def test_a_library_edit_that_only_grows_a_facet_is_written_as_typed_and_is_not_a_version(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    ctx = _sidecar(paths)
    rel_path = str(paths.facets_path.relative_to(paths.root))
    body = _edited_registry(paths, aliases=["svd"]) + "# the owner's note\n"

    saved = _call(ctx, "write_vault_file", {"path": rel_path, "body": body})

    assert saved["body"] == body and paths.facets_path.read_text(encoding="utf-8") == body
    assert list_actions(repository) == []
    assert "svd" in load_vault(paths.root).evidence_facets[SHARED].aliases


def test_a_library_edit_cannot_set_a_facets_version_by_hand(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    ctx = _sidecar(paths)
    rel_path = str(paths.facets_path.relative_to(paths.root))
    _call(ctx, "write_vault_file", {"path": rel_path, "body": _edited_registry(paths, claim=NEW_CLAIM)})
    (reword,) = list_actions(repository)

    # A stale version typed back with the same meaning: corrected, not a version.
    _call(ctx, "write_vault_file", {"path": rel_path, "body": _edited_registry(paths, version=1)})

    assert _entry(paths, SHARED)["version"] == 2 and _entry(paths, SHARED)["claim"] == NEW_CLAIM
    assert [row["id"] for row in list_actions(repository)] == [reword["id"]]
    undo_action(paths.root, repository, reword["id"], clock=_CLOCK)
    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM


def test_a_library_registry_edit_that_does_not_parse_is_refused_and_writes_nothing(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    ctx = _sidecar(paths)
    rel_path = str(paths.facets_path.relative_to(paths.root))
    before = paths.facets_path.read_bytes()

    for body in ("facets: [\n  - id: x\n", "facets:\n  - id: x\n    version: not-a-number\n"):
        with pytest.raises(SidecarError) as exc:
            _call(ctx, "write_vault_file", {"path": rel_path, "body": body})
        assert exc.value.code == "invalid_registry"
    assert paths.facets_path.read_bytes() == before
    assert list_actions(repository) == []


def test_a_library_reword_interrupted_before_the_write_is_withdrawn(tmp_path, monkeypatch):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    before = paths.facets_path.read_bytes()

    def crash(*_args, **_kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(facet_actions, "_write_registry_text", crash)
    with pytest.raises(RuntimeError):
        facet_actions.save_registry_text(paths.root, repository, _edited_registry(paths, claim=NEW_CLAIM),
                                         clock=_CLOCK)

    (record,) = list_actions(repository)
    assert record["status"] == "abandoned"
    assert paths.facets_path.read_bytes() == before


def test_a_library_reword_interrupted_after_the_write_is_finished_by_recovery(tmp_path, monkeypatch):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)

    def crash(*_args, **_kwargs):
        raise RuntimeError("killed after the rename")

    monkeypatch.setattr(facet_actions, "refresh_derived_state", crash)
    with pytest.raises(RuntimeError):
        facet_actions.save_registry_text(paths.root, repository, _edited_registry(paths, claim=NEW_CLAIM),
                                         clock=_CLOCK)
    (record,) = list_actions(repository)
    assert record["status"] == "applying" and _entry(paths, SHARED)["claim"] == NEW_CLAIM
    monkeypatch.undo()

    (outcome,) = recover_interrupted_actions(paths.root, repository, clock=_CLOCK)

    assert outcome["to"] == "applied"
    undo_action(paths.root, repository, record["id"], clock=_CLOCK)
    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM


def test_a_library_reword_whose_write_never_landed_is_withdrawn_by_recovery(tmp_path):
    """An ``applying`` reword whose file still shows the old entry: the owner's
    save never happened, so recovery withdraws it rather than writing one entry
    of a save the owner never saw land."""

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    entry = _entry(paths, SHARED)
    with repository.atomic():
        facet_actions.insert_action(repository.connection(), {
            "origin": "registry", "scope": "vault", "run_id": "library", "action": "reword",
            "survivor_facet_id": SHARED, "retired_facet_ids": [],
            "before": {"facets": {SHARED: dict(entry)}, "order": {}},
            "after": {"facets": {SHARED: {**dict(entry), "claim": NEW_CLAIM, "version": 2}}},
            "merge_rows": [], "judgment_ids": [], "judge": "owner", "judge_model": None,
            "prompt_version": None, "detail": {"via": "library"}, "status": "applying",
            "created_at": "2026-10-13T12:00:00Z",
        })

    (outcome,) = recover_interrupted_actions(paths.root, repository, clock=_CLOCK)

    assert outcome["to"] == "abandoned"
    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM
    assert facet_history(repository, SHARED)[0]["status"] == "abandoned"


# --- F2: an append restructure can reword a facet ------------------------------------------

SYMMETRY = "facet_symmetry_definition"
SYMMETRY_CLAIM = "A real square matrix A is symmetric exactly when it equals its transpose: A^T = A."


def _facet_restructure(operation: str = "update", target: str = SYMMETRY):
    """The response a provider returns under the strict schema (validated, not constructed)."""

    from learnloop.content.synthesis.ai_contracts import AppendReconciliation

    def builder(_context, _n):
        return AppendReconciliation.model_validate({
            "summary": "the new source states the definition precisely",
            "restructures": [{
                "client_item_id": "reword_symmetry", "target_entity_type": "facet",
                "target_entity_id": target, "operation": operation,
                "expected_target_hash": "", "payload": {},
                "facet_wording": {
                    "kind": None, "claim": SYMMETRY_CLAIM, "description": "",
                    "preconditions": [], "postconditions": [], "applicability": [], "non_goals": [],
                },
            }],
        })

    return builder


def test_the_append_schema_lets_a_provider_reword_a_facet():
    from learnloop.ai.strict_schema import strict_output_schema
    from learnloop.content.synthesis.ai_contracts import AppendReconciliation

    schema = strict_output_schema(AppendReconciliation)
    restructure = schema["$defs"]["AppendRestructure"]["properties"]
    assert "facet" in restructure["target_entity_type"]["enum"]
    # The bare ``payload`` dict is unfillable under strict output (an empty
    # object), so the facet's new wording travels in a declared shape.
    wording = schema["$defs"]["AppendFacetWording"]["properties"]
    assert {"kind", "claim", "preconditions", "non_goals"} <= set(wording)
    assert "facet_wording" in restructure


def test_an_append_facet_restructure_applies_as_a_facet_version_with_undo(tmp_path):
    from learnloop.content.synthesis.source_append import append_source

    from tests.test_source_append import FakeAppendClient, _bootstrap_and_add

    root, repo = _bootstrap_and_add(tmp_path)
    old = load_vault(root).evidence_facets[SYMMETRY]

    result = append_source(root, "set_la", client=FakeAppendClient(builder=_facet_restructure()),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)

    assert not any(diag["severity"] == "hard_fail" for diag in result.gate_diagnostics)
    (item,) = [row for row in repo.proposal_items(result.proposal_id)
               if row["item_type"] == "facet" and row["operation"] == "update"]
    assert item["payload"]["claim"] == SYMMETRY_CLAIM and "preconditions" not in item["payload"]
    assert item["payload"]["expected_target_hash"]  # stamped from the vault, not the model's ""
    assert result.auto_applied_item_ids == []  # a restructure is always reviewed

    apply_accepted_items(root, result.proposal_id, item_ids=[item["id"]], clock=_CLOCK)

    facet = load_vault(root).evidence_facets[SYMMETRY]
    assert facet.claim == SYMMETRY_CLAIM and facet.version == old.version + 1
    assert facet.preconditions == old.preconditions  # a blank field keeps the facet's own
    vault = load_vault(root)
    stored = next(entry for entry in read_yaml(VaultPaths(vault.root, vault.config).facets_path)["facets"]
                  if entry["id"] == SYMMETRY)
    assert "expected_target_hash" not in stored  # proposal bookkeeping stays out of the registry
    (record,) = [row for row in list_actions(repo) if row["action"] == "reword"]
    assert record["proposal_id"] == result.proposal_id and record["detail"]["fields"] == ["claim"]

    undo_action(root, repo, record["id"], clock=_CLOCK)
    assert load_vault(root).evidence_facets[SYMMETRY].claim == old.claim


def test_an_append_facet_restructure_refuses_when_the_facet_changed_since(tmp_path):
    from learnloop.content.proposals.patches import PatchApplicationError
    from learnloop.content.synthesis.source_append import append_source

    from tests.test_source_append import FakeAppendClient, _bootstrap_and_add

    root, repo = _bootstrap_and_add(tmp_path)
    result = append_source(root, "set_la", client=FakeAppendClient(builder=_facet_restructure()),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)
    (item,) = [row for row in repo.proposal_items(result.proposal_id) if row["item_type"] == "facet"]
    apply_accepted_items(root, _facet_update_proposal(repo, {"id": SYMMETRY, "aliases": ["symmetric"]}),
                         clock=_CLOCK)

    with pytest.raises(PatchApplicationError, match="target changed after synthesis"):
        apply_accepted_items(root, result.proposal_id, item_ids=[item["id"]], clock=_CLOCK)
    assert load_vault(root).evidence_facets[SYMMETRY].claim != SYMMETRY_CLAIM


@pytest.mark.parametrize(("operation", "target"), [("deactivate", SYMMETRY), ("update", "facet_not_registered")])
def test_an_append_facet_restructure_that_cannot_apply_is_dropped_with_a_diagnostic(tmp_path, operation, target):
    from learnloop.content.synthesis.source_append import append_source

    from tests.test_source_append import FakeAppendClient, _bootstrap_and_add

    root, repo = _bootstrap_and_add(tmp_path)
    result = append_source(root, "set_la", client=FakeAppendClient(builder=_facet_restructure(operation, target)),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)

    assert not any(row["item_type"] == "facet" and row["operation"] != "create"
                   for row in repo.proposal_items(result.proposal_id or "") or [])
    (diag,) = [diag for diag in result.gate_diagnostics if diag["gate"] == "facet_restructure"]
    assert diag["severity"] == "review" and target in diag["entity_refs"]
