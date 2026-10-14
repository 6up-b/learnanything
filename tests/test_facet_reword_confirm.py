"""A reword without explanatory support waits for the owner's one-tap confirm (owner, 2026-10-13).

The facet-authority chokepoint used to refuse a model-proposed change to a
registered facet's meaning unless every source of it cited an explanatory span
(textbook, lecture, paper, reference, alternate explanation). The owner decided
that "a confirm this reword is better" than a refusal:

1. A change with no explanatory support (uncited, or supported only by notes,
   problem-set or unknown-role citations) is no longer refused. Accepting its
   proposal holds it as a pending "confirm this reword" item (a ``proposed``
   ``reword`` action), shown with its before and after wording and its sources
   in registry review and in the proposals inbox. Confirming it is the owner's
   manual authority: an owner verdict (``judge = 'owner'``), a write through the
   chokepoint as an owner edit, and an undo. Keeping the current wording closes
   it. A pending proposal the old code would have refused becomes one too.
2. Exam material stays a hard block. Exam-only support (exam citations with no
   explanatory one beside them, held-out evaluation units included) cannot
   change a facet's meaning on any write path, a confirm included; only the
   owner's own Library edit can.
3. A facet's title and worked examples are not meaning: changing them needs no
   explanatory citation, and the change is recorded on the facet's history
   with its sources. Claim, definition, conditions and non-goals stay meaning.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.content.facet_identity import actions as facet_actions
from learnloop.content.facet_identity import authority
from learnloop.content.facet_identity.actions import (
    FacetIdentityActionError,
    describe,
    facet_history,
    list_actions,
    undo_action,
)
from learnloop.content.proposals.patches import PatchApplicationError, apply_accepted_items
from learnloop.content.synthesis.ai_contracts import SourceSetSynthesis, SynthFacet, SynthSpanRef
from learnloop.content.synthesis.source_append import append_source
from learnloop.content.synthesis.source_set_synthesis import StudyMapError, _collect_inputs, _normalize
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_source_set
from learnloop.vault.yaml_io import read_yaml, yaml_to_string

from tests.helpers import seed_explanatory_source
from tests.test_facet_identity_actions import SHARED, _vault_with_duplicate
from tests.test_facet_reword_paths import (
    NEW_SPAN,
    SYMMETRY,
    SYMMETRY_CLAIM,
    _call,
    _facet_restructure,
    _sidecar,
)
from tests.test_facet_rewords import NEW_CLAIM, OLD_CLAIM, _entry, _facet_update_proposal
from tests.test_source_append import FakeAppendClient, _bootstrap_and_add

_CLOCK = FrozenClock(datetime(2026, 10, 13, 14, 0, 0, tzinfo=UTC))
NOW = "2026-10-13T14:00:00Z"
SUBJECT = "linear-algebra"
THIRD_CLAIM = "A = U Sigma V^T, with the singular values on Sigma's diagonal in decreasing order."
EXAM_TEXT = "Final exam, question 3: show that every matrix has a singular value decomposition."


# --- setup ---------------------------------------------------------------------------------


def _seed(paths, repository, role: str, name: str, *, text: str | None = None) -> dict[str, str]:
    """A source-set member of ``role`` with one span; returns a citation of it."""

    citation = seed_explanatory_source(
        paths.root, repository, source_id=f"src_{name}", revision_id=f"rev_{name}",
        extraction_id=f"ext_{name}", unit_id=f"unit_{name}", role=role,
    )
    if text is not None:
        from learnloop.ingest.ir import DocumentBlock

        ir = repository.load_document_ir(citation["extraction_id"])
        ir.blocks = [DocumentBlock.build(span_id="s1", block_type="Text", ordinal=1, section_path=["root"],
                                         text=text)]
        repository.persist_document_ir(citation["extraction_id"], ir)
    return citation


def _support(*citations, label: str = "reword") -> list[dict]:
    return [{"from": label, "citations": [dict(citation) for citation in citations]}]


def _proposal(repository, payload: dict, *, operation: str = "update") -> str:
    """A facet proposal exactly as given (no citation added)."""

    now = utc_now_iso(_CLOCK)
    agent_run_id = repository.insert_agent_run({
        "purpose": "test_confirm", "provider": "learner", "provider_type": "learner",
        "started_at": now, "completed_at": now, "status": "completed",
    })
    item = {
        "client_item_id": f"facet_{operation}_1", "item_type": "facet", "operation": operation,
        "target_entity_type": "facet" if operation == "update" else None,
        "target_entity_id": payload["id"] if operation == "update" else None, "payload": payload,
        "source_ref_ids": [], "audit": {"origin": "test"}, "decision": "pending",
        "validation_status": "valid", "validation_errors": [], "depends_on_client_item_ids": [],
        "dependency_status": "pending", "created_at": now, "updated_at": now,
    }
    return repository.persist_proposal_batch({
        "agent_run_id": agent_run_id, "purpose": "test_reword_confirm", "summary": "reword",
        "source_refs": [], "status_cache": "pending", "created_at": now, "updated_at": now,
    }, [item])


def _pending(repository, root) -> list[dict]:
    return facet_actions.pending_reword_confirms(repository, load_vault(root))


def _ledger(repository, task: str) -> list[dict]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = ? ORDER BY created_at, id", (task,),
        ).fetchall()
    return [dict(row) for row in rows]


def _held(paths, repository, payload: dict | None = None) -> dict:
    """An uncited reword of SHARED, accepted: it waits for the owner's confirm."""

    patch_id = _proposal(repository, payload or {"id": SHARED, "claim": NEW_CLAIM})
    apply_accepted_items(paths.root, patch_id, clock=_CLOCK)
    (confirm,) = _pending(repository, paths.root)
    return confirm


# --- 1. a reword without explanatory support waits for the owner's confirm -------------------


def test_an_uncited_reword_of_a_registered_facet_waits_for_the_owners_confirm(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    patch_id = _proposal(repository, {"id": SHARED, "claim": NEW_CLAIM})

    apply_accepted_items(paths.root, patch_id, clock=_CLOCK)  # refused before the owner's decision

    # Nothing about the facet changed yet.
    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM and _entry(paths, SHARED).get("version", 1) == 1
    assert repository.entity_source_links("facet", SHARED) == []
    (item,) = repository.proposal_items(patch_id)
    assert item["decision"] == "accepted"
    (confirm,) = _pending(repository, paths.root)
    assert confirm["facet_id"] == SHARED and confirm["status"] == "pending"
    assert confirm["changes"] == [{"field": "claim", "before": OLD_CLAIM, "after": NEW_CLAIM}]
    assert confirm["sources"] == [] and confirm["proposal_id"] == patch_id
    assert SHARED in confirm["message"] and "no source" in confirm["message"]
    record = facet_actions.action_by_id(repository, confirm["action_id"])
    assert (record["action"], record["status"], record["scope"]) == ("reword", "proposed", "vault")
    shown = describe(record, load_vault(paths.root))
    assert shown["status"] == "proposed" and shown["undoable"] is False and shown["confirm"]["status"] == "pending"


@pytest.mark.parametrize("role", ["notes", "problem_set", "worksheet"])
def test_a_reword_supported_only_by_a_non_explanatory_role_waits_for_confirm(tmp_path, role):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    citation = _seed(paths, repository, role, role, text=f"From the {role}: every real matrix has an SVD.")
    patch_id = _proposal(repository, {"id": SHARED, "claim": NEW_CLAIM, "meaning_support": _support(citation)})

    apply_accepted_items(paths.root, patch_id, clock=_CLOCK)

    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM
    (confirm,) = _pending(repository, paths.root)
    (source,) = confirm["sources"]
    assert (source["role"], source["extraction_id"], source["span_id"]) == (role, f"ext_{role}", "s1")
    assert source["excerpt"] == f"From the {role}: every real matrix has an SVD."
    assert confirm["changes"] == [{"field": "claim", "before": OLD_CLAIM, "after": NEW_CLAIM}]


def test_confirming_a_reword_applies_it_as_the_owners_authority_with_an_undo(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    confirm = _held(paths, repository)

    result = facet_actions.confirm_reword(paths.root, repository, confirm["action_id"], clock=_CLOCK)

    assert result["status"] == "applied" and result["facet_id"] == SHARED
    entry = _entry(paths, SHARED)
    assert entry["claim"] == NEW_CLAIM and entry["version"] == 2
    record = facet_actions.action_by_id(repository, confirm["action_id"])
    assert record["status"] == "applied" and record["judge"] == "owner"
    assert record["after"]["facets"][SHARED]["claim"] == NEW_CLAIM
    (grant,) = _ledger(repository, facet_actions.MANUAL_AUTHORITY_TASK)
    assert (grant["judge"], grant["verdict"], grant["left_id"]) == ("owner", "granted", SHARED)
    rationale = json.loads(grant["rationale"])
    assert rationale["origin"] == "confirm" and rationale["action_id"] == confirm["action_id"]
    assert result["owner_judgment_id"] == grant["id"]
    with repository.connection() as connection:
        (save,) = [dict(row) for row in connection.execute("SELECT * FROM facet_registry_saves").fetchall()]
    assert save["status"] == "applied" and confirm["action_id"] in save["action_ids_json"]
    assert _pending(repository, paths.root) == []
    shown = describe(record, load_vault(paths.root))
    assert shown["undoable"] is True and shown["confirm"]["status"] == "confirmed"
    assert [row["id"] for row in facet_history(repository, SHARED, load_vault(paths.root))] == [record["id"]]

    undo_action(paths.root, repository, confirm["action_id"], clock=_CLOCK)

    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM and _entry(paths, SHARED).get("version", 1) == 1


def test_confirming_keeps_what_changed_on_the_facet_since_beside_the_new_wording(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    confirm = _held(paths, repository)
    # An alias added since the reword was held is not meaning: the confirm keeps it.
    apply_accepted_items(paths.root, _facet_update_proposal(repository, {"id": SHARED, "aliases": ["svd"]}),
                         clock=_CLOCK)

    facet_actions.confirm_reword(paths.root, repository, confirm["action_id"], clock=_CLOCK)

    entry = _entry(paths, SHARED)
    assert entry["claim"] == NEW_CLAIM and "svd" in entry["aliases"]


def test_keeping_the_current_wording_closes_the_confirm_and_changes_nothing(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    confirm = _held(paths, repository)
    before = paths.facets_path.read_text(encoding="utf-8")

    result = facet_actions.keep_current_wording(paths.root, repository, confirm["action_id"], clock=_CLOCK)

    assert result["status"] == "kept"
    assert paths.facets_path.read_text(encoding="utf-8") == before
    assert _pending(repository, paths.root) == []
    (verdict,) = _ledger(repository, facet_actions.REWORD_TASK)
    assert (verdict["judge"], verdict["verdict"], verdict["left_id"]) == ("owner", "rejected", SHARED)
    record = facet_actions.action_by_id(repository, confirm["action_id"])
    assert describe(record, load_vault(paths.root))["confirm"]["status"] == "kept"
    with pytest.raises(FacetIdentityActionError) as raised:
        facet_actions.confirm_reword(paths.root, repository, confirm["action_id"], clock=_CLOCK)
    assert raised.value.code == "not_pending"


def test_a_pending_proposal_the_old_code_refused_becomes_a_confirm_naming_the_facet(tmp_path):
    """A create carrying a registered id, uncited, persisted before the owner's decision."""

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    patch_id = _proposal(repository, {
        "id": SHARED, "kind": "definition", "claim": NEW_CLAIM,
        "provenance": {"origin": "sourceset_synthesis", "source_refs": []},
    }, operation="create")

    apply_accepted_items(paths.root, patch_id, clock=_CLOCK)

    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM
    (confirm,) = _pending(repository, paths.root)
    assert confirm["facet_id"] == SHARED and SHARED in confirm["message"]
    assert "confirm" in confirm["message"]


def test_a_confirm_refuses_when_the_facets_wording_changed_since(tmp_path, monkeypatch):
    from learnloop import decider_judgments as tier1
    from tests.test_tier1_decider import FixedDecider
    monkeypatch.setattr(tier1, 'client_for', lambda *args: FixedDecider({'facet_span_support': 'supports'}))
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    confirm = _held(paths, repository)
    apply_accepted_items(paths.root, _facet_update_proposal(repository, {"id": SHARED, "claim": THIRD_CLAIM}),
                         clock=_CLOCK)

    with pytest.raises(FacetIdentityActionError) as raised:
        facet_actions.confirm_reword(paths.root, repository, confirm["action_id"], clock=_CLOCK)

    assert raised.value.code == "changed_since" and SHARED in str(raised.value)
    assert _entry(paths, SHARED)["claim"] == THIRD_CLAIM
    assert _ledger(repository, facet_actions.MANUAL_AUTHORITY_TASK) == []
    # The owner can still close it.
    assert facet_actions.keep_current_wording(paths.root, repository, confirm["action_id"],
                                              clock=_CLOCK)["status"] == "kept"


class _Killed(BaseException):
    """The process stopping mid-confirm (not an ``Exception``: nothing in process catches it)."""


def test_an_interrupted_confirm_returns_to_pending_and_withdraws_its_verdict(tmp_path, monkeypatch):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    confirm = _held(paths, repository)

    def killed(*_args, **_kwargs):
        raise _Killed()

    monkeypatch.setattr(facet_actions, "_write_registry", killed)
    with pytest.raises(_Killed):
        facet_actions.confirm_reword(paths.root, repository, confirm["action_id"], clock=_CLOCK)
    monkeypatch.undo()
    assert facet_actions.action_by_id(repository, confirm["action_id"])["status"] == "applying"

    facet_actions.recover_interrupted_actions(paths.root, repository, clock=_CLOCK)

    assert facet_actions.action_by_id(repository, confirm["action_id"])["status"] == "proposed"
    assert sorted(row["verdict"] for row in _ledger(repository, facet_actions.MANUAL_AUTHORITY_TASK)) == [
        "granted", "withdrawn"]
    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM
    (again,) = _pending(repository, paths.root)
    assert again["action_id"] == confirm["action_id"]
    facet_actions.confirm_reword(paths.root, repository, confirm["action_id"], clock=_CLOCK)
    assert _entry(paths, SHARED)["claim"] == NEW_CLAIM


def test_a_confirm_that_fails_in_process_stays_pending(tmp_path, monkeypatch):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    confirm = _held(paths, repository)

    def crash(*_args, **_kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(facet_actions, "_write_registry", crash)
    with pytest.raises(RuntimeError):
        facet_actions.confirm_reword(paths.root, repository, confirm["action_id"], clock=_CLOCK)
    monkeypatch.undo()

    assert facet_actions.action_by_id(repository, confirm["action_id"])["status"] == "proposed"
    assert sorted(row["verdict"] for row in _ledger(repository, facet_actions.MANUAL_AUTHORITY_TASK)) == [
        "granted", "withdrawn"]
    assert facet_actions.recover_interrupted_actions(paths.root, repository, clock=_CLOCK) == []


def test_an_uncited_append_reword_reaches_the_owner_as_a_confirm(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    old = load_vault(root).evidence_facets[SYMMETRY]

    result = append_source(root, "set_la", client=FakeAppendClient(builder=_facet_restructure(citations=())),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)

    (item,) = [row for row in repo.proposal_items(result.proposal_id or "") or []
               if row["item_type"] == "facet" and row["operation"] == "update"]
    assert any(diag["gate"] == "facet_reword_confirm" and SYMMETRY in diag["entity_refs"]
               for diag in result.gate_diagnostics)
    apply_accepted_items(root, result.proposal_id, item_ids=[item["id"]], clock=_CLOCK)
    assert load_vault(root).evidence_facets[SYMMETRY].claim == old.claim
    (confirm,) = _pending(repo, root)
    assert confirm["facet_id"] == SYMMETRY and confirm["changes"][0]["after"] == SYMMETRY_CLAIM

    facet_actions.confirm_reword(root, repo, confirm["action_id"], clock=_CLOCK)
    assert load_vault(root).evidence_facets[SYMMETRY].claim == SYMMETRY_CLAIM


def test_a_notes_cited_append_reword_reaches_the_owner_as_a_confirm(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path, add_role="notes")

    result = append_source(root, "set_la", client=FakeAppendClient(builder=_facet_restructure()),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)
    (item,) = [row for row in repo.proposal_items(result.proposal_id) if row["item_type"] == "facet"
               and row["operation"] == "update"]

    apply_accepted_items(root, result.proposal_id, item_ids=[item["id"]], clock=_CLOCK)

    (confirm,) = _pending(repo, root)
    assert [(source["role"], source["extraction_id"]) for source in confirm["sources"]] == [
        ("notes", NEW_SPAN["extraction_id"])]


def test_a_bootstrap_candidate_carrying_a_registered_id_uncited_is_kept_for_confirm(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    vault = load_vault(root)
    source_set = next(source_set for source_set in vault.source_sets if source_set.id == "set_la")
    inputs = _collect_inputs(repo, vault, source_set)
    synth = SourceSetSynthesis(facets=[SynthFacet(
        client_item_id="f_again", id=SYMMETRY, kind="definition", claim=NEW_CLAIM, provenance=[],
    )])

    normalized = _normalize(synth, inputs, vault, NOW, subject_id=SUBJECT)

    (row,) = [row for row in normalized.rows if row["item_type"] == "facet"]
    assert row["operation"] == "update" and row["payload"]["expected_target_hash"]
    assert "meaning_support" in row["payload"]
    assert any(diag["gate"] == "facet_reword_confirm" and SYMMETRY in diag["entity_refs"]
               for diag in normalized.edge_diagnostics)


def test_a_confirm_never_shows_exam_text(tmp_path):
    """An exam span may corroborate one source of a reword; its text never reaches the owner's screen."""

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    text = _seed(paths, repository, "primary_textbook", "text", text="Every real matrix has an SVD.")
    exam = _seed(paths, repository, "exam", "exam", text=EXAM_TEXT)
    patch_id = _proposal(repository, {"id": SHARED, "claim": NEW_CLAIM, "meaning_support": [
        *_support(text, exam, label="corroborated"), *_support(label="uncited"),
    ]})

    apply_accepted_items(paths.root, patch_id, clock=_CLOCK)

    (confirm,) = _pending(repository, paths.root)
    by_role = {source["role"]: source for source in confirm["sources"]}
    assert by_role["primary_textbook"]["excerpt"] == "Every real matrix has an SVD."
    assert by_role["exam"]["excerpt"] is None and by_role["exam"]["relation"] == "assessment_alignment"
    assert EXAM_TEXT not in json.dumps(confirm) and EXAM_TEXT not in json.dumps(
        facet_actions.action_by_id(repository, confirm["action_id"]))


# --- surfaces: registry review, the proposals inbox, the sidecar, the CLI ----------------------


def test_registry_review_lists_a_pending_confirm_with_its_wording_and_sources(tmp_path):
    from learnloop.curriculum.subject_registry import build_subject_registry

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    notes = _seed(paths, repository, "notes", "notes", text="My notes on the SVD.")
    patch_id = _proposal(repository, {"id": SHARED, "claim": NEW_CLAIM, "meaning_support": _support(notes)})
    apply_accepted_items(paths.root, patch_id, clock=_CLOCK)

    registry = build_subject_registry(load_vault(paths.root), repository, SUBJECT)

    (confirm,) = registry["reword_confirms"]
    assert confirm["facet_id"] == SHARED
    assert confirm["changes"] == [{"field": "claim", "before": OLD_CLAIM, "after": NEW_CLAIM}]
    assert confirm["sources"][0]["excerpt"] == "My notes on the SVD."


def test_the_sidecar_lists_and_decides_reword_confirms(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    confirm = _held(paths, repository)
    ctx = _sidecar(paths)

    inbox = _call(ctx, "get_proposals", {})  # the desktop's camelCase DTOs
    (listed,) = inbox["rewordConfirms"]
    assert listed["actionId"] == confirm["action_id"] and listed["facetId"] == SHARED
    assert listed["changes"] == [{"field": "claim", "before": OLD_CLAIM, "after": NEW_CLAIM}]
    (item,) = [item for batch in inbox["batches"] for item in batch["items"]]
    assert (item["decision"], item["rewordConfirm"]) == ("accepted", "pending")

    decided = _call(ctx, "decide_facet_reword", {"actionId": confirm["action_id"], "decision": "confirm"})

    assert decided["status"] == "applied" and decided["action"]["confirm"]["status"] == "confirmed"
    assert _entry(paths, SHARED)["claim"] == NEW_CLAIM
    after = _call(ctx, "get_proposals", {})
    assert after["rewordConfirms"] == []
    assert [item["rewordConfirm"] for batch in after["batches"] for item in batch["items"]] == ["confirmed"]


def test_the_sidecar_keeps_the_current_wording_on_request(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    confirm = _held(paths, repository)
    ctx = _sidecar(paths)

    decided = _call(ctx, "decide_facet_reword", {"actionId": confirm["action_id"], "decision": "keep"})

    assert decided["status"] == "kept" and _entry(paths, SHARED)["claim"] == OLD_CLAIM
    with pytest.raises(SidecarError) as raised:
        _call(ctx, "decide_facet_reword", {"actionId": confirm["action_id"], "decision": "confirm"})
    assert raised.value.code == "not_pending"


def test_the_cli_confirms_a_reword(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli import app

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    confirm = _held(paths, repository)

    result = CliRunner().invoke(app, ["facets", "confirm", confirm["action_id"], "--vault", str(paths.root),
                                      "--json"])

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["status"] == "applied"
    assert _entry(paths, SHARED)["claim"] == NEW_CLAIM


# --- 2. exam material stays a hard block on every write path ----------------------------------


def _exam(paths, repository) -> dict[str, str]:
    return _seed(paths, repository, "exam", "exam", text=EXAM_TEXT)


@pytest.mark.parametrize("change", [
    {"claim": NEW_CLAIM},
    {"preconditions": ["the matrix is real"]},
    {"title": "SVD (exam wording)"},
    {"positive_examples": ["A = U Sigma V^T for the matrix of exam question 3"]},
], ids=["claim", "precondition", "title", "worked_example"])
def test_an_exam_only_change_through_a_proposal_is_refused_never_held(tmp_path, change):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    exam = _exam(paths, repository)
    notes = _seed(paths, repository, "notes", "notes")
    before = paths.facets_path.read_text(encoding="utf-8")
    patch_id = _proposal(repository, {"id": SHARED, **change, "meaning_support": _support(exam, notes)})

    with pytest.raises(PatchApplicationError, match="exam"):
        apply_accepted_items(paths.root, patch_id, clock=_CLOCK)

    assert paths.facets_path.read_text(encoding="utf-8") == before
    assert _pending(repository, paths.root) == [] and list_actions(repository) == []


def test_an_exam_only_create_carrying_a_registered_id_is_refused(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    exam = _exam(paths, repository)
    patch_id = _proposal(repository, {
        "id": SHARED, "kind": "definition", "claim": NEW_CLAIM,
        "provenance": {"origin": "sourceset_synthesis", "source_refs": [{
            "ref_type": "canonical_source", "ref_id": "src_exam", "source_id": "src_exam",
            "revision_id": "rev_exam", "extraction_id": exam["extraction_id"],
            "locator": f"span:{exam['extraction_id']}/s1", "locator_scheme": "block_span_v1",
            "relation": "primary", "role": "primary_textbook",
        }]},
    }, operation="create")

    with pytest.raises(PatchApplicationError, match="exam"):
        apply_accepted_items(paths.root, patch_id, clock=_CLOCK)

    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM and _pending(repository, paths.root) == []


def test_an_exam_only_bootstrap_candidate_carrying_a_registered_id_is_dropped_not_held(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path, add_role="exam")
    vault = load_vault(root)
    source_set = next(source_set for source_set in vault.source_sets if source_set.id == "set_la")
    inputs = _collect_inputs(repo, vault, source_set)
    synth = SourceSetSynthesis(facets=[SynthFacet(
        client_item_id="f_exam", id=SYMMETRY, kind="definition", claim=NEW_CLAIM,
        provenance=[SynthSpanRef(**NEW_SPAN, relation="primary")],
    )])

    normalized = _normalize(synth, inputs, vault, NOW, subject_id=SUBJECT)

    assert not [row for row in normalized.rows if row["item_type"] == "facet"]
    assert any(diag["gate"] == "exam_authority" and SYMMETRY in diag["entity_refs"]
               for diag in normalized.edge_diagnostics)


def test_an_exam_only_append_reword_still_hard_fails(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path, add_role="exam")

    with pytest.raises(StudyMapError) as raised:
        append_source(root, "set_la", client=FakeAppendClient(builder=_facet_restructure()),
                      new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)

    assert [diag["severity"] for diag in raised.value.diagnostics if diag["gate"] == "exam_authority"] == [
        "hard_fail"]
    assert _pending(repo, root) == []


def test_the_registry_writer_refuses_exam_only_meaning_and_an_unconfirmed_reword(tmp_path):
    paths, vault, repository = _vault_with_duplicate(tmp_path)
    exam = _exam(paths, repository)
    vault = load_vault(paths.root)
    document = read_yaml(paths.facets_path)
    for entry in document["facets"]:
        if entry["id"] == SHARED:
            entry["claim"] = NEW_CLAIM
    text = yaml_to_string(document)
    resolver = authority.CitationResolver.for_vault(repository, vault)

    for basis, code in (
        ({SHARED: authority.Cited(authority.contributions([exam]))}, "exam_authority"),
        # Unsupported is not exam: but only the owner's confirm (an owner edit) may write it.
        ({SHARED: authority.Cited(())}, "unsupported_reword"),
    ):
        with pytest.raises(authority.FacetAuthorityError) as raised:
            authority.write_registry_text(paths, text, basis=basis, resolver=resolver)
        assert raised.value.code == code
    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM


def test_a_confirm_whose_support_became_exam_material_is_refused(tmp_path):
    """The roles are judged again at confirm: a source re-marked as an exam since cannot reword a facet."""

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    notes = _seed(paths, repository, "notes", "notes")
    apply_accepted_items(paths.root, _proposal(repository, {"id": SHARED, "claim": NEW_CLAIM,
                                                            "meaning_support": _support(notes)}), clock=_CLOCK)
    (confirm,) = _pending(repository, paths.root)
    vault = load_vault(paths.root)
    source_set = next(source_set for source_set in vault.source_sets if source_set.id == "set_src_notes")
    members = [{**member.model_dump(mode="json", exclude_none=True), "default_role": "exam"}
               for member in source_set.members]
    upsert_source_set(paths.root, {"id": source_set.id, "subject_id": source_set.subject_id,
                                   "title": source_set.title, "members": members}, clock=_CLOCK)

    with pytest.raises(FacetIdentityActionError) as raised:
        facet_actions.confirm_reword(paths.root, repository, confirm["action_id"], clock=_CLOCK)

    assert raised.value.code == "exam_authority"
    assert _entry(paths, SHARED)["claim"] == OLD_CLAIM
    assert _ledger(repository, facet_actions.MANUAL_AUTHORITY_TASK) == []


@pytest.mark.parametrize("named_unit", ["chapter#Theory", "chapter#Nowhere"])
def test_an_exam_span_cited_under_the_wrong_unit_is_refused_not_held(tmp_path, named_unit):
    """A misdeclared citation supports nothing, but never turns exam material into "uncited"."""

    from tests.test_facet_authority_review import _add_split_chapter

    root, repo = _bootstrap_and_add(tmp_path)
    _add_split_chapter(repo, root, [{"unit_id": "chapter#Theory"},
                                    {"unit_id": "chapter#Exam", "role_override": "exam"}])
    patch_id = _proposal(repo, {"id": SYMMETRY, "claim": NEW_CLAIM, "meaning_support": _support(
        {"extraction_id": "ext_split", "unit_id": named_unit, "span_id": "s2"})})

    with pytest.raises(PatchApplicationError, match="exam"):
        apply_accepted_items(root, patch_id, clock=_CLOCK)

    assert load_vault(root).evidence_facets[SYMMETRY].claim != NEW_CLAIM and _pending(repo, root) == []


def test_an_append_reword_citing_exam_material_under_the_wrong_unit_is_dropped_not_held(tmp_path):
    """The producer drops a citation that does not resolve; it must not turn exam material into "uncited"."""

    root, repo = _bootstrap_and_add(tmp_path, add_role="exam")
    misplaced = {**NEW_SPAN, "unit_id": "chapter_symmetry"}  # the textbook's unit, not the exam's

    result = append_source(root, "set_la", client=FakeAppendClient(builder=_facet_restructure(citations=(misplaced,))),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)

    assert not [row for row in repo.proposal_items(result.proposal_id or "") or []
                if row["item_type"] == "facet" and row["operation"] == "update"]
    assert any(diag["gate"] == "exam_authority" and SYMMETRY in diag["entity_refs"]
               for diag in result.gate_diagnostics)
    assert not any(diag["gate"] == "facet_reword_confirm" for diag in result.gate_diagnostics)


def test_a_bootstrap_reword_citing_exam_material_under_the_wrong_unit_is_dropped_not_held(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path, add_role="exam")
    vault = load_vault(root)
    source_set = next(source_set for source_set in vault.source_sets if source_set.id == "set_la")
    inputs = _collect_inputs(repo, vault, source_set)
    synth = SourceSetSynthesis(facets=[SynthFacet(
        client_item_id="f_exam", id=SYMMETRY, kind="definition", claim=NEW_CLAIM,
        provenance=[SynthSpanRef(**{**NEW_SPAN, "unit_id": "chapter_symmetry"}, relation="primary")],
    )])

    normalized = _normalize(synth, inputs, vault, NOW, subject_id=SUBJECT)

    assert not [row for row in normalized.rows if row["item_type"] == "facet"]
    assert any(diag["gate"] == "exam_authority" and SYMMETRY in diag["entity_refs"]
               for diag in normalized.edge_diagnostics)


def test_a_held_out_evaluation_unit_is_exam_material_whatever_its_members_role(tmp_path):
    from learnloop.content.synthesis.source_unit_selection import save_unit_selection

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    # A member the owner gave an explanatory role, one of whose units is held out for evaluation.
    held = _seed(paths, repository, "primary_textbook", "held", text=EXAM_TEXT)
    save_unit_selection(repository, held["extraction_id"], [held["unit_id"]],
                        exam_use_modes={held["unit_id"]: "held_out_evaluation"})
    resolver = authority.CitationResolver.for_vault(repository, load_vault(paths.root))

    resolved = resolver.resolve(held)

    assert isinstance(resolved, authority.ResolvedCitation)
    assert (resolved.role, resolved.relation) == ("exam", "assessment_alignment")
    patch_id = _proposal(repository, {"id": SHARED, "claim": NEW_CLAIM, "meaning_support": _support(held)})
    with pytest.raises(PatchApplicationError, match="exam"):
        apply_accepted_items(paths.root, patch_id, clock=_CLOCK)
    assert _pending(repository, paths.root) == []


def test_the_library_stays_the_owners_override_for_exam_wording(tmp_path):
    """The one route by which exam-derived wording reaches a facet: the owner typing it."""

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    document = read_yaml(paths.facets_path)
    for entry in document["facets"]:
        if entry["id"] == SHARED:
            entry["claim"] = NEW_CLAIM

    facet_actions.save_registry_text(paths.root, repository, yaml_to_string(document), clock=_CLOCK)

    assert _entry(paths, SHARED)["claim"] == NEW_CLAIM


# --- 3. titles and worked examples need no explanatory citation --------------------------------


def test_a_title_change_needs_no_explanatory_citation_and_is_on_the_facets_history(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    patch_id = _proposal(repository, {"id": SHARED, "title": "Singular value decomposition"})

    apply_accepted_items(paths.root, patch_id, clock=_CLOCK)

    entry = _entry(paths, SHARED)
    assert entry["title"] == "Singular value decomposition" and entry.get("version", 1) == 1
    assert _pending(repository, paths.root) == []
    (record,) = facet_history(repository, SHARED, load_vault(paths.root))
    assert record["action"] == "reword" and record["presentation"] is True
    assert record["reworded"]["fields"] == ["title"] and record["sources"] == []
    assert record["proposal_id"] == patch_id and record["undoable"] is True


def test_a_worked_example_change_applies_with_its_source_on_the_facets_history(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    notes = _seed(paths, repository, "notes", "notes", text="Example: a 3x2 matrix and its SVD.")
    examples = list(_entry(paths, SHARED).get("positive_examples") or [])
    patch_id = _proposal(repository, {"id": SHARED, "positive_examples": [*examples, "a 3x2 example"],
                                      "meaning_support": _support(notes)})

    apply_accepted_items(paths.root, patch_id, clock=_CLOCK)

    entry = _entry(paths, SHARED)
    assert "a 3x2 example" in entry["positive_examples"] and entry.get("version", 1) == 1
    (record,) = facet_history(repository, SHARED, load_vault(paths.root))
    assert record["presentation"] is True and record["reworded"]["fields"] == ["positive_examples"]
    (source,) = record["sources"]
    assert (source["role"], source["extraction_id"]) == ("notes", "ext_notes")

    undo_action(paths.root, repository, record["id"], clock=_CLOCK)
    assert "a 3x2 example" not in (_entry(paths, SHARED).get("positive_examples") or [])


@pytest.mark.parametrize("change", [
    {"claim": NEW_CLAIM},
    {"description": "The factorization every real matrix has."},
    {"preconditions": ["the matrix is real"]},
    {"non_goals": ["eigendecomposition"]},
], ids=["claim", "definition", "preconditions", "non_goals"])
def test_claim_definition_preconditions_and_non_goals_stay_meaning(tmp_path, change):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    before = paths.facets_path.read_text(encoding="utf-8")

    apply_accepted_items(paths.root, _proposal(repository, {"id": SHARED, **change}), clock=_CLOCK)

    assert paths.facets_path.read_text(encoding="utf-8") == before
    (confirm,) = _pending(repository, paths.root)
    assert [change["field"] for change in confirm["changes"]] == list(change)


def test_a_cited_reword_records_its_sources_on_the_facets_history(tmp_path, monkeypatch):
    from learnloop import decider_judgments as tier1
    from tests.test_tier1_decider import FixedDecider
    monkeypatch.setattr(tier1, 'client_for', lambda *args: FixedDecider({'facet_span_support': 'supports'}))
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    text = _seed(paths, repository, "primary_textbook", "text")
    patch_id = _proposal(repository, {"id": SHARED, "claim": NEW_CLAIM, "meaning_support": _support(text)})

    apply_accepted_items(paths.root, patch_id, clock=_CLOCK)

    assert _entry(paths, SHARED)["claim"] == NEW_CLAIM and _pending(repository, paths.root) == []
    (record,) = facet_history(repository, SHARED, load_vault(paths.root))
    assert record["presentation"] is False
    assert [(source["role"], source["extraction_id"]) for source in record["sources"]] == [
        ("primary_textbook", "ext_text")]


def test_the_chokepoint_judges_titles_and_examples_without_an_explanatory_citation(tmp_path):
    paths, vault, _repository = _vault_with_duplicate(tmp_path)
    before = vault.evidence_facets[SHARED].model_dump(mode="json")

    for change, code, allowed in (
        ({"title": "SVD"}, "presentation", True),
        ({"positive_examples": ["another example"]}, "presentation", True),
        ({"negative_examples": ["a non-example"]}, "presentation", True),
        ({"claim": NEW_CLAIM}, "unsupported_reword", False),
        ({"claim": NEW_CLAIM, "title": "SVD"}, "unsupported_reword", False),
    ):
        verdict = authority.check_meaning_write(
            SHARED, before=before, after={**before, **change}, registered=True, contributions=(), resolver=None,
        )
        assert (verdict.code, verdict.allowed) == (code, allowed), change
        assert verdict.confirmable is (code == "unsupported_reword")

