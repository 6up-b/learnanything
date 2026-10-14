"""Exam authority holds wherever a facet's meaning is written (Codex verification of F6).

The facet-locks branch fixed F6 for the append reword lane only. An
independent Codex verification (job ``20261013-055453-vZTyoZ``) found seven
other routes by which exam material could still change a facet's meaning,
with locks gone:

1. an uncited ``create`` carrying a registered facet's id overwrote it
   (append and bootstrap normalization, and the proposal writer itself);
2. a notes (or any non-explanatory) citation beside an exam one defeated the
   ``exam_authority`` hard fail;
3. a unit whose ``role_override`` is ``exam`` inside a textbook extraction
   counted as textbook support;
4. identity consolidation merged an exam-only candidate into a textbook one and
   kept its meaning (merge, absorb as precondition, absorb as example), and the
   merged provenance recorded the exam span as support;
5. a persisted locator could name a different span from the ids validated;
6. citations were not limited to the selected units, nor a span to the unit it
   was cited with;
7. duplicate facet ids in a Library save broke history and undo.

The fix enforces exam authority once, in ``content.facet_identity.authority``:
every facet meaning write (proposal apply, merges and absorbs, consolidation,
undo, recovery, Library saves) goes through it, with citations resolved there
from the source sets (unit override over extraction role, selected units only,
span inside its unit, locator derived from the ids). The last tests pin that a
new write path cannot bypass it.
"""

from __future__ import annotations

import ast
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tests.facet_identity_fakes import supporting_span_decider  # noqa: F401

import learnloop
from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.content.facet_identity import actions as facet_actions
from learnloop.content.facet_identity.actions import FacetIdentityActionError, list_actions
from learnloop.content.facet_identity.plan import FacetIdentityPlan, Retirement
from learnloop.content.proposals.patches import PatchApplicationError, apply_accepted_items
from learnloop.content.synthesis.ai_contracts import (
    AppendReconciliation,
    SourceSetSynthesis,
    SynthConcept,
    SynthFacet,
    SynthSpanRef,
)
from learnloop.content.synthesis.source_append import append_source
from learnloop.content.synthesis.source_set_synthesis import (
    StudyMapError,
    _collect_inputs,
    _gate_context,
    _normalize,
    _span_refs,
)
from learnloop.content.synthesis.source_unit_inventory import run_unit_inventory
from learnloop.content.synthesis.synthesis_gates import (
    GateContext,
    GateItem,
    GateProposal,
    ProvenanceRef,
    run_synthesis_gates,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_source_set
from learnloop.vault.yaml_io import read_yaml, yaml_to_string

from tests.test_facet_identity_actions import SHARED, _vault_with_duplicate
from tests.test_facet_reword_paths import NEW_SPAN, SYMMETRY, TEXT_SPAN, _facet_restructure
from tests.test_facet_rewords import OLD_CLAIM
from tests.test_source_append import FakeAppendClient, SymmetryInventoryClient, _bootstrap_and_add
from tests.test_source_inventory import _block, _ir, _persist, _register_revision
from tests.test_source_set_synthesis import _setup

_CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, 0, tzinfo=UTC))
NOW = "2026-10-13T12:00:00Z"
SUBJECT = "linear-algebra"

EXAM_CLAIM = "On the final, a matrix counts as symmetric only when every diagonal entry is positive."
EXAM_CONDITION = "EXAM-ONLY condition: every diagonal entry is positive"
NEW_CLAIM = "A real square matrix A is symmetric exactly when it equals its transpose: A^T = A."

#: The held-out exam paper of ``_setup(with_exam=True)``.
EXAM_SPAN = {"extraction_id": "ext_exam", "unit_id": "paper_2024", "span_id": "s1"}
#: Members a test adds (``_add_member``): a notes source, a textbook extraction
#: one of whose units is overridden to ``exam``, and an explanatory source with
#: one selected and one unselected unit.
NOTES_SPAN = {"extraction_id": "ext_notes", "unit_id": "notes_symmetry", "span_id": "s1"}
OVERRIDDEN_EXAM_SPAN = {"extraction_id": "ext_mixed", "unit_id": "mixed_exam_part", "span_id": "s2"}
MIXED_TEXT_SPAN = {"extraction_id": "ext_mixed", "unit_id": "mixed_text", "span_id": "s1"}
#: ``s2`` belongs to ``two_outside`` only; the member selects ``two_selected``.
MISMATCHED_SPAN = {"extraction_id": "ext_two", "unit_id": "two_selected", "span_id": "s2"}
UNSELECTED_SPAN = {"extraction_id": "ext_two", "unit_id": "two_outside", "span_id": "s2"}


# --- setup ---------------------------------------------------------------------------------


def _add_member(repo, root, *, source_id, revision_id, extraction_id, units, role, scope):
    """Register a source revision with ``units`` = [(unit_id, [(span_id, text)])] and add it to set_la."""

    _register_revision(repo, source_id=source_id, revision_id=revision_id)
    ir = _ir([
        (unit_id, unit_id.replace("_", " "), [_block(span_id, text) for span_id, text in blocks],
         f"sha256:{unit_id}", index + 3)
        for index, (unit_id, blocks) in enumerate(units)
    ])
    _persist(repo, ir, revision_id=revision_id, extraction_id=extraction_id)
    for entry in scope:
        run_unit_inventory(repo, extraction_id, entry["unit_id"], role=entry.get("role_override") or role,
                           profile="combined", client=SymmetryInventoryClient(), input_budget_tokens=20000,
                           clock=_CLOCK)
    vault = load_vault(root)
    current = next(source_set for source_set in vault.source_sets if source_set.id == "set_la")
    members = [member.model_dump(mode="json", exclude_none=True) for member in current.members]
    members.append({"source_id": source_id, "revision_id": revision_id, "default_role": role,
                    "scope": scope, "priority": 1})
    upsert_source_set(root, {"id": "set_la", "subject_id": SUBJECT, "title": "Linear Algebra",
                             "members": members}, clock=_CLOCK)


def _add_notes(repo, root):
    _add_member(repo, root, source_id="src_notes", revision_id="rev_notes", extraction_id="ext_notes",
                units=[("notes_symmetry", [("s1", "My notes: symmetric means positive diagonal.")])],
                role="notes", scope=[{"unit_id": "notes_symmetry"}])


def _add_mixed_textbook(repo, root):
    """A textbook extraction whose exercise-test unit the owner marked ``exam``."""

    _add_member(repo, root, source_id="src_mixed", revision_id="rev_mixed", extraction_id="ext_mixed",
                units=[("mixed_text", [("s1", "A symmetric matrix equals its transpose.")]),
                       ("mixed_exam_part", [("s2", "Test: show the diagonal of a symmetric matrix is positive.")])],
                role="primary_textbook",
                scope=[{"unit_id": "mixed_text"}, {"unit_id": "mixed_exam_part", "role_override": "exam"}])


def _add_two_units(repo, root):
    """An explanatory source with one selected unit and one the owner left out."""

    _add_member(repo, root, source_id="src_two", revision_id="rev_two", extraction_id="ext_two",
                units=[("two_selected", [("s1", "Symmetric matrices have real eigenvalues.")]),
                       ("two_outside", [("s2", "A matrix is symmetric when its diagonal is positive.")])],
                role="alternate_explanation", scope=[{"unit_id": "two_selected"}])


def _source_set(root):
    return next(source_set for source_set in load_vault(root).source_sets if source_set.id == "set_la")


def _facet_proposal(repository, payload: dict, *, operation: str) -> str:
    now = utc_now_iso(_CLOCK)
    agent_run_id = repository.insert_agent_run({
        "purpose": "test_authority", "provider": "learner", "provider_type": "learner",
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
        "agent_run_id": agent_run_id, "purpose": "test_facet_authority", "summary": "authority",
        "source_refs": [], "status_cache": "pending", "created_at": now, "updated_at": now,
    }, [item])


def _support(*citations, label: str = "test") -> list[dict]:
    return [{"from": label, "citations": [dict(citation) for citation in citations]}]


def _accept_pending(root, repo, proposal_id) -> None:
    pending = [row["id"] for row in repo.proposal_items(proposal_id or "") or [] if row["decision"] == "pending"]
    if pending:
        try:
            apply_accepted_items(root, proposal_id, item_ids=pending, clock=_CLOCK)
        except PatchApplicationError:
            pass  # refused at the writer: equally safe, checked by the caller's assertions


def _meaning(payload: dict) -> str:
    fields = ("kind", "claim", "description", "preconditions", "postconditions", "applicability", "non_goals",
              "positive_examples", "negative_examples")
    return json.dumps({name: payload.get(name) for name in fields}, sort_keys=True)


def _registry_entry(root, facet_id):
    vault = load_vault(root)
    data = read_yaml(VaultPaths(vault.root, vault.config).facets_path)
    return next(entry for entry in data["facets"] if entry["id"] == facet_id)


def _exam_vault(tmp_path):
    """The bootstrap textbook map with the held-out exam paper in the set (``_setup(with_exam=True)``)."""

    from learnloop.content.synthesis.source_set_synthesis import create_study_map

    from tests.test_source_set_synthesis import FakeSynthesisClient

    root, repo = _setup(tmp_path, with_exam=True)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo, clock=_CLOCK, apply=True,
                     brief={"depth": "intro"})
    return root, repo


# --- 1. an uncited create carrying a registered id never overwrites it ---------------------


def test_an_uncited_append_facet_carrying_a_registered_id_never_rewrites_it(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path, add_role="exam")
    old = load_vault(root).evidence_facets[SYMMETRY]

    def builder(_context, _n):
        return AppendReconciliation.model_validate({"summary": "exam material", "facets": [{
            "client_item_id": "f_exam", "id": SYMMETRY, "concept_id": old.concept_id or "",
            "kind": "definition", "claim": EXAM_CLAIM, "preconditions": [EXAM_CONDITION], "provenance": [],
        }]})

    result = append_source(root, "set_la", client=FakeAppendClient(builder=builder), new_revision_ids=["rev_alt"],
                           repository=repo, clock=_CLOCK)

    # Uncited, it is never written as it stands: it is kept as a checked
    # update that waits for the owner's confirm (owner, 2026-10-13), which
    # shows that it cites no source.
    rows = [row for row in repo.proposal_items(result.proposal_id or "") or []
            if row["item_type"] == "facet" and (row["payload"] or {}).get("claim") == EXAM_CLAIM]
    assert [row["operation"] for row in rows] == ["update"]
    assert any(SYMMETRY in diag["entity_refs"] and diag["severity"] == "review"
               and diag["gate"] == "facet_reword_confirm" for diag in result.gate_diagnostics)
    _accept_pending(root, repo, result.proposal_id)
    facet = load_vault(root).evidence_facets[SYMMETRY]
    assert facet.claim == old.claim and EXAM_CONDITION not in facet.preconditions
    (confirm,) = facet_actions.pending_reword_confirms(repo, load_vault(root))
    assert confirm["facet_id"] == SYMMETRY and confirm["sources"] == []


def test_a_bootstrap_candidate_carrying_a_registered_id_rewords_it_uncited_only_with_the_owners_confirm(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path, add_role="exam")
    vault = load_vault(root)
    inputs = _collect_inputs(repo, vault, _source_set(root))
    synth = SourceSetSynthesis(facets=[SynthFacet(
        client_item_id="f_again", id=SYMMETRY, kind="definition", claim=EXAM_CLAIM, provenance=[],
    )])

    normalized = _normalize(synth, inputs, vault, NOW, subject_id=SUBJECT)

    # Kept as a checked update (never a create over the facet), which the
    # apply holds for the owner's confirm (owner, 2026-10-13).
    (row,) = [row for row in normalized.rows
              if row["item_type"] == "facet" and row["payload"].get("claim") == EXAM_CLAIM]
    assert row["operation"] == "update" and row["payload"]["expected_target_hash"]
    assert any(SYMMETRY in diag["entity_refs"] and diag["gate"] == "facet_reword_confirm"
               for diag in normalized.edge_diagnostics)


def test_a_cited_bootstrap_candidate_carrying_a_registered_id_rewords_it_as_a_checked_update(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    vault = load_vault(root)
    inputs = _collect_inputs(repo, vault, _source_set(root))
    synth = SourceSetSynthesis(facets=[SynthFacet(
        client_item_id="f_again", id=SYMMETRY, kind="definition", claim=NEW_CLAIM,
        provenance=[SynthSpanRef(**TEXT_SPAN, relation="primary")],
    )])

    normalized = _normalize(synth, inputs, vault, NOW, subject_id=SUBJECT)

    (row,) = [row for row in normalized.rows if row["item_type"] == "facet"]
    # A create of a registered id is an update: the target hash guards it and it is reviewed.
    assert row["operation"] == "update" and row["payload"]["expected_target_hash"]
    assert row["payload"]["meaning_support"][0]["citations"][0]["extraction_id"] == "ext_text"


def test_a_proposal_create_over_a_registered_facet_needs_explanatory_support_or_the_owners_confirm(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    patch_id = _facet_proposal(repository, {
        "id": SHARED, "kind": "definition", "claim": EXAM_CLAIM,
        "provenance": {"origin": "sourceset_synthesis", "source_refs": []},
    }, operation="create")

    apply_accepted_items(paths.root, patch_id, clock=_CLOCK)

    # Not written: held for the owner's confirm (owner, 2026-10-13).
    assert _registry_entry(paths.root, SHARED)["claim"] == OLD_CLAIM
    (held,) = list_actions(repository)
    assert (held["action"], held["status"]) == ("reword", "proposed") and facet_actions.is_reword_confirm(held)


# --- 2. a non-explanatory citation never corroborates exam material ------------------------


def test_a_notes_citation_never_corroborates_exam_material_at_the_gate():
    item = GateItem(
        client_item_id="f", item_type="facet", entity_id="f", payload={"id": "f", "claim": EXAM_CLAIM},
        provenance=[
            ProvenanceRef(extraction_id="ext_exam", span_id="s1", role="exam", relation="assessment_alignment"),
            ProvenanceRef(extraction_id="ext_notes", span_id="s1", role="notes", relation="support"),
        ],
    )

    report = run_synthesis_gates(GateProposal(items=[item]), GateContext())

    assert [diag.severity for diag in report.diagnostics if diag.gate == "exam_authority"] == ["hard_fail"]


def test_an_exam_and_notes_reword_hard_fails_exam_authority(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path, add_role="exam")
    _add_notes(repo, root)
    old = load_vault(root).evidence_facets[SYMMETRY]

    with pytest.raises(StudyMapError) as raised:
        append_source(root, "set_la", client=FakeAppendClient(builder=_facet_restructure(citations=(NEW_SPAN, NOTES_SPAN))),
                      new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)

    assert [diag["severity"] for diag in raised.value.diagnostics if diag["gate"] == "exam_authority"] == ["hard_fail"]
    assert load_vault(root).evidence_facets[SYMMETRY].claim == old.claim


def test_the_writer_refuses_a_reword_supported_by_exam_and_notes_only(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path, add_role="exam")
    _add_notes(repo, root)
    patch_id = _facet_proposal(repo, {"id": SYMMETRY, "claim": EXAM_CLAIM,
                                      "meaning_support": _support(NEW_SPAN, NOTES_SPAN)}, operation="update")

    with pytest.raises(PatchApplicationError, match="exam"):
        apply_accepted_items(root, patch_id, clock=_CLOCK)

    assert load_vault(root).evidence_facets[SYMMETRY].claim != EXAM_CLAIM


# --- 3. a unit's role override wins over its extraction's role -----------------------------


def test_an_exam_override_inside_a_textbook_extraction_is_exam_material(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    _add_mixed_textbook(repo, root)
    old = load_vault(root).evidence_facets[SYMMETRY]

    with pytest.raises(StudyMapError) as raised:
        append_source(root, "set_la", client=FakeAppendClient(builder=_facet_restructure(citations=(OVERRIDDEN_EXAM_SPAN,))),
                      new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)

    assert [diag["severity"] for diag in raised.value.diagnostics if diag["gate"] == "exam_authority"] == ["hard_fail"]
    assert load_vault(root).evidence_facets[SYMMETRY].claim == old.claim


def test_citations_take_the_units_role_override(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    _add_mixed_textbook(repo, root)
    inputs = _collect_inputs(repo, load_vault(root), _source_set(root))

    gate_refs, yaml_refs, _spans = _span_refs([OVERRIDDEN_EXAM_SPAN, MIXED_TEXT_SPAN], inputs, default_relation="support")

    assert [ref.role for ref in gate_refs] == ["exam", "primary_textbook"]
    assert [(ref["role"], ref["relation"]) for ref in yaml_refs] == [
        ("exam", "assessment_alignment"), ("primary_textbook", "support")]


def test_the_writer_refuses_a_reword_citing_an_exam_override_only(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    _add_mixed_textbook(repo, root)
    patch_id = _facet_proposal(repo, {"id": SYMMETRY, "claim": EXAM_CLAIM,
                                      "meaning_support": _support(OVERRIDDEN_EXAM_SPAN)}, operation="update")

    with pytest.raises(PatchApplicationError, match="exam"):
        apply_accepted_items(root, patch_id, clock=_CLOCK)

    assert load_vault(root).evidence_facets[SYMMETRY].claim != EXAM_CLAIM


# --- 4. consolidation never carries exam-only meaning into a survivor ----------------------


def _consolidation(tmp_path, *, survivor_cites, retired_cites, action, absorb_as):
    root, repo = _setup(tmp_path, with_exam=True)
    vault = load_vault(root)
    inputs = _collect_inputs(repo, vault, _source_set(root))
    synth = SourceSetSynthesis(
        concepts=[SynthConcept(client_item_id="c_sym", id="concept_symmetric_matrix", title="Symmetric matrix")],
        facets=[
            SynthFacet(client_item_id="f_survivor", id="facet_symmetry", concept_client_id="c_sym",
                       kind="definition", claim="A real square matrix is symmetric exactly when A^T = A.",
                       preconditions=["the matrix is real and square"],
                       provenance=[SynthSpanRef(**survivor_cites, relation="primary")]),
            SynthFacet(client_item_id="f_retired", id="facet_symmetry_exam", concept_client_id="c_sym",
                       kind="definition", claim=EXAM_CLAIM, preconditions=[EXAM_CONDITION],
                       provenance=[SynthSpanRef(**retired_cites, relation="primary")]),
        ],
    )
    plan = FacetIdentityPlan(status="judged", retirements={"f_retired": Retirement(
        client_id="f_retired", scope="in_run", action=action, absorb_as=absorb_as, survivor_client="f_survivor",
    )})
    normalized = _normalize(synth, inputs, vault, NOW, subject_id=SUBJECT, facet_identity_plan=plan)
    report = run_synthesis_gates(GateProposal(items=normalized.gate_items), _gate_context(vault, repo, inputs, []))
    survivor = next(row["payload"] for row in normalized.rows if row["client_item_id"] == "f_survivor")
    return normalized, report, survivor


@pytest.mark.parametrize(("action", "absorb_as"), [("merge", None), ("absorb", "precondition"), ("absorb", "example")])
def test_consolidation_never_carries_exam_only_meaning_into_a_survivor(tmp_path, action, absorb_as):
    _normalized, report, survivor = _consolidation(
        tmp_path, survivor_cites=TEXT_SPAN, retired_cites=EXAM_SPAN, action=action, absorb_as=absorb_as,
    )

    meaning = _meaning(survivor)
    assert report.blocked or (EXAM_CLAIM not in meaning and EXAM_CONDITION not in meaning)
    for ref in survivor["provenance"]["source_refs"]:
        if ref.get("extraction_id") == "ext_exam":  # never recorded as semantic support
            assert ref["relation"] == "assessment_alignment"


def test_a_survivor_that_only_exam_material_supports_still_fails_after_consolidation(tmp_path):
    _normalized, report, _survivor = _consolidation(
        tmp_path, survivor_cites=EXAM_SPAN, retired_cites=TEXT_SPAN, action="merge", absorb_as=None,
    )

    assert "exam_authority" in {diag.gate for diag in report.hard_fails}


def test_the_writer_refuses_a_new_facet_one_of_whose_contributions_is_exam_only(tmp_path):
    root, repo = _exam_vault(tmp_path)
    patch_id = _facet_proposal(repo, {
        "id": "facet_symmetry_merged", "kind": "definition", "claim": "A real square matrix is symmetric when A^T = A.",
        "preconditions": [EXAM_CONDITION],
        "meaning_support": [*_support(TEXT_SPAN, label="f_survivor"), *_support(EXAM_SPAN, label="f_retired")],
    }, operation="create")

    with pytest.raises(PatchApplicationError, match="exam"):
        apply_accepted_items(root, patch_id, clock=_CLOCK)

    assert "facet_symmetry_merged" not in load_vault(root).evidence_facets


def _exam_alias_consolidation(tmp_path):
    """An ingest run whose judge merges an exam-only candidate into the textbook one (it joins as an alias)."""

    from learnloop.content.synthesis.source_set_synthesis import create_study_map

    from tests.facet_identity_fakes import FakeFacetJudge
    from tests.test_facet_identity_ingest import DEF_CLAIM
    from tests.test_source_set_synthesis import FakeSynthesisClient, _default_payload

    def with_exam_duplicate(context, _ordinal):
        payload = _default_payload(context)
        payload.facets.append(SynthFacet(
            client_item_id="f_exam_dup", id="facet_symmetry_exam", concept_client_id="c_sym", kind="definition",
            claim=EXAM_CLAIM, preconditions=[EXAM_CONDITION], positive_examples=["an exam-only example"],
            provenance=[SynthSpanRef(**EXAM_SPAN, relation="primary")],
        ))
        return payload

    root, repo = _setup(tmp_path, with_exam=True)
    result = create_study_map(root, "set_la", client=FakeSynthesisClient(builder=with_exam_duplicate),
                              repository=repo, clock=_CLOCK, apply=True,
                              facet_identity_client=FakeFacetJudge(clusters=[[DEF_CLAIM, EXAM_CLAIM]]))
    return root, repo, result


def _owner_judgments(repo) -> list[dict]:
    with repo.connection() as connection:
        rows = connection.execute("SELECT * FROM judgment_ledger WHERE judge = 'owner' ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def test_an_ingest_consolidation_keeps_exam_only_meaning_out_and_its_undo_cannot_mint_it(tmp_path):
    """End to end: the judge merges an exam-only candidate into the textbook one."""

    from learnloop.content.facet_identity.actions import undo_action

    root, repo, result = _exam_alias_consolidation(tmp_path)

    assert result.applied
    survivor = load_vault(root).evidence_facets["facet_symmetry_definition"]
    assert "facet_symmetry_exam" in survivor.aliases  # same skill: an alias of the survivor
    assert EXAM_CONDITION not in survivor.preconditions and "an exam-only example" not in survivor.positive_examples
    assert any(diag["gate"] == "exam_authority" and diag["severity"] == "review"
               for diag in result.gate_diagnostics)
    (action,) = result.facet_identity["actions"]
    assert "alias only" in (action.get("contract_note") or "")
    before = load_vault(root).evidence_facets["facet_symmetry_definition"].model_dump(mode="json")
    status = facet_actions.action_by_id(repo, action["id"])["status"]

    # Undoing the consolidation would mint the exam-only candidate as a facet.
    with pytest.raises(FacetIdentityActionError) as raised:
        undo_action(root, repo, action["id"], clock=_CLOCK)

    assert raised.value.code == "exam_authority"
    vault = load_vault(root)
    assert "facet_symmetry_exam" not in vault.evidence_facets
    assert vault.evidence_facets["facet_symmetry_definition"].model_dump(mode="json") == before
    # Codex re-review F1: the refusal is decided before the undo intent is
    # recorded, so the action stays as it was (never ``undoing``) with no owner
    # verdict, and the next facet operation (each one runs recovery first) is
    # not blocked by it.
    assert facet_actions.action_by_id(repo, action["id"])["status"] == status != "undoing"
    assert facet_actions.describe(facet_actions.action_by_id(repo, action["id"]), vault)["status"] == "applied"
    assert _owner_judgments(repo) == []
    assert facet_actions.recover_interrupted_actions(root, repo, clock=_CLOCK) == []
    paths = VaultPaths(vault.root, vault.config)
    document = read_yaml(paths.facets_path)
    edited = next(entry for entry in document["facets"] if entry["id"] == "facet_symmetry_definition")
    edited["claim"] = NEW_CLAIM
    saved = facet_actions.save_registry_text(root, repo, yaml_to_string(document), clock=_CLOCK)
    assert saved["reword_action_ids"]
    assert load_vault(root).evidence_facets["facet_symmetry_definition"].claim == NEW_CLAIM


# --- 5. the persisted locator is derived from the validated ids ----------------------------


def test_a_citations_locator_is_derived_from_its_validated_ids(tmp_path):
    root, repo = _setup(tmp_path, with_exam=True)
    inputs = _collect_inputs(repo, load_vault(root), _source_set(root))
    spoofed = {**TEXT_SPAN, "locator": "span:ext_exam/s1"}

    _gate_refs, yaml_refs, _spans = _span_refs([spoofed], inputs, default_relation="primary")

    (ref,) = yaml_refs
    assert ref["locator"] == "span:ext_text/s1" and ref["extraction_id"] == "ext_text"


def test_the_writer_judges_a_persisted_citation_by_the_span_its_locator_names(tmp_path):
    root, repo = _exam_vault(tmp_path)
    patch_id = _facet_proposal(repo, {
        "id": "facet_spoofed", "kind": "definition", "claim": EXAM_CLAIM,
        "provenance": {"origin": "sourceset_synthesis", "source_refs": [{
            "ref_type": "canonical_source", "ref_id": "src_text", "source_id": "src_text",
            "revision_id": "rev_text", "extraction_id": "ext_text", "locator": "span:ext_exam/s1",
            "locator_scheme": "block_span_v1", "relation": "primary", "role": "primary_textbook",
        }]},
    }, operation="create")

    with pytest.raises(PatchApplicationError, match="exam"):
        apply_accepted_items(root, patch_id, clock=_CLOCK)

    assert "facet_spoofed" not in load_vault(root).evidence_facets
    assert repo.entity_source_links("facet", "facet_spoofed") == []


# --- 6. citations resolve inside the selected units, a span inside its unit ------------------


def test_a_reword_citing_a_span_outside_its_unit_drops_the_citation(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    _add_two_units(repo, root)

    result = append_source(root, "set_la", client=FakeAppendClient(builder=_facet_restructure(citations=(MISMATCHED_SPAN,))),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)

    # The citation is dropped; left uncited, the reword waits for the owner's
    # confirm (owner, 2026-10-13) and records nothing it cited.
    (row,) = [row for row in repo.proposal_items(result.proposal_id or "") or []
              if row["item_type"] == "facet" and row["operation"] == "update"]
    assert "provenance" not in row["payload"]
    notes = [diag for diag in result.gate_diagnostics if diag["gate"] == "facet_restructure"]
    assert any("two_selected" in diag["message"] for diag in notes)
    assert any(diag["gate"] == "facet_reword_confirm" for diag in result.gate_diagnostics)


def test_an_unselected_span_never_corroborates_exam_material(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path, add_role="exam")
    _add_two_units(repo, root)
    old = load_vault(root).evidence_facets[SYMMETRY]

    with pytest.raises(StudyMapError) as raised:
        append_source(root, "set_la",
                      client=FakeAppendClient(builder=_facet_restructure(citations=(NEW_SPAN, UNSELECTED_SPAN))),
                      new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)

    assert [diag["severity"] for diag in raised.value.diagnostics if diag["gate"] == "exam_authority"] == ["hard_fail"]
    assert load_vault(root).evidence_facets[SYMMETRY].claim == old.claim


def test_a_provenance_link_to_an_unselected_unit_is_dropped(tmp_path):
    from learnloop.content.synthesis.source_append import _span_problem

    root, repo = _bootstrap_and_add(tmp_path)
    _add_two_units(repo, root)
    inputs = _collect_inputs(repo, load_vault(root), _source_set(root))

    assert _span_problem(UNSELECTED_SPAN, inputs) is not None
    assert _span_problem(MISMATCHED_SPAN, inputs) is not None
    assert _span_problem({**MISMATCHED_SPAN, "span_id": "s1"}, inputs) is None


def test_the_writer_never_writes_a_reword_whose_only_support_is_unselected(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    _add_two_units(repo, root)
    patch_id = _facet_proposal(repo, {"id": SYMMETRY, "claim": NEW_CLAIM,
                                      "meaning_support": _support(UNSELECTED_SPAN)}, operation="update")

    apply_accepted_items(root, patch_id, clock=_CLOCK)

    # Unselected support is no support: the reword waits for the owner's
    # confirm (owner, 2026-10-13), which says why its citation does not count.
    assert load_vault(root).evidence_facets[SYMMETRY].claim != NEW_CLAIM
    (confirm,) = facet_actions.pending_reword_confirms(repo, load_vault(root))
    assert confirm["sources"] == [] and any("selected" in problem for problem in confirm["unresolved"])


# --- 7. a Library save that lists a facet twice is refused ---------------------------------


def test_a_library_save_listing_a_facet_twice_is_refused_and_writes_nothing(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    before_text = paths.facets_path.read_text(encoding="utf-8")
    document = read_yaml(paths.facets_path)
    shared = next(entry for entry in document["facets"] if entry["id"] == SHARED)
    document["facets"].append({**shared, "claim": "A second, different wording of the same facet."})
    shared["claim"] = NEW_CLAIM

    with pytest.raises(FacetIdentityActionError) as raised:
        facet_actions.save_registry_text(paths.root, repository, yaml_to_string(document), clock=_CLOCK)

    assert raised.value.code == "invalid_registry" and SHARED in str(raised.value)
    assert paths.facets_path.read_text(encoding="utf-8") == before_text
    assert list_actions(repository) == []


# --- the chokepoint: no writer of facet meaning can bypass it ------------------------------


def test_the_registry_writer_refuses_exam_only_meaning_whatever_the_caller_declares(tmp_path):
    from learnloop.content.facet_identity import authority

    root, repo = _bootstrap_and_add(tmp_path, add_role="exam")
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    before_text = paths.facets_path.read_text(encoding="utf-8")
    document = read_yaml(paths.facets_path)
    entry = next(entry for entry in document["facets"] if entry["id"] == SYMMETRY)
    entry["claim"] = EXAM_CLAIM
    text = yaml_to_string(document)
    resolver = authority.CitationResolver.for_vault(repo, vault)
    # The caller's own role and locator claims are ignored: the span is the exam member's.
    spoofed = {**NEW_SPAN, "role": "primary_textbook", "locator": "span:ext_text/s1"}

    for basis, code in (
        ({SYMMETRY: authority.Cited(authority.contributions([spoofed]))}, "exam_authority"),
        ({SYMMETRY: authority.Cited(())}, "unsupported_reword"),
        ({}, "unauthorized"),
        ({SYMMETRY: authority.RegisteredMerge(SYMMETRY, ("facet_not_registered",), "merge", None)}, "unauthorized"),
        ({SYMMETRY: authority.Restore({SYMMETRY: {**entry, "claim": "some other wording"}})}, "unauthorized"),
    ):
        with pytest.raises(authority.FacetAuthorityError) as raised:
            authority.write_registry_text(paths, text, basis=basis, resolver=resolver)
        assert raised.value.code == code, basis
    assert paths.facets_path.read_text(encoding="utf-8") == before_text


def test_a_facet_write_compiled_without_the_authority_context_is_refused(tmp_path):
    from learnloop.content.proposals.patches import compile_proposal_item

    paths, vault, _repository = _vault_with_duplicate(tmp_path)
    item = {"id": "item_1", "item_type": "facet", "operation": "update",
            "payload": {"id": SHARED, "claim": NEW_CLAIM}}

    with pytest.raises(PatchApplicationError, match="authority"):
        compile_proposal_item(vault, item)


#: The source tree of the ``learnloop`` actually imported (``src/``).
_SRC = Path(learnloop.__file__).resolve().parents[1]
#: Modules allowed to name the facet registry file at all, and why.
_REGISTRY_FILE_MODULES = {
    "learnloop/content/facet_identity/authority.py": "the chokepoint: the one writer",
    "learnloop/content/facet_identity/actions.py": "reads the registry document (merges, undo, Library)",
    "learnloop/vault/paths.py": "defines the path",
    "learnloop/vault/loader.py": "reads it; creates an empty registry for a new vault",
    "learnloop/vault/writer.py": "upsert_facet, called only by the proposal compiler (checked below)",
    "learnloop/ops/doctor.py": "reads and reports",
    "learnloop_sidecar/handlers/library.py": "routes a Library save of the registry to save_registry_text",
}
#: Functions that write facet meaning, and the only modules that may call them.
_GUARDED_CALLS = {
    "upsert_facet": {"learnloop/content/proposals/patches.py"},
    "union_payload": {"learnloop/content/facet_identity/authority.py",
                      # builds the judge's read-only view of a consolidated candidate
                      "learnloop/content/facet_identity/plan.py"},
    "write_registry_text": {"learnloop/content/facet_identity/actions.py",
                            "learnloop/content/facet_identity/authority.py"},
    "OwnerEdit": {"learnloop/content/facet_identity/actions.py"},
    # A proposal's facet writes compile only inside the checked apply.
    "compile_proposal_item": {"learnloop/content/proposals/apply_protocol.py"},
    "stage_target_contents": {"learnloop/content/proposals/patches.py"},
}


#: Calls that write a file.
_FILE_WRITES = {"write_yaml", "write_text", "write_bytes", "materialize_targets", "replace", "rename",
                "unlink", "open"}


def _python_sources():
    for path in sorted(_SRC.rglob("*.py")):
        yield path.relative_to(_SRC).as_posix(), ast.parse(path.read_text(encoding="utf-8"))


def _called(node: ast.Call) -> str:
    func = node.func
    return func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""


def test_every_writer_of_facet_meaning_goes_through_the_authority_chokepoint():
    """A new write path fails here until it goes through ``content.facet_identity.authority``."""

    touching: set[str] = set()
    writers: set[str] = set()
    calls: dict[str, set[str]] = {name: set() for name in _GUARDED_CALLS}
    compile_facet_checks = False
    for module, tree in _python_sources():
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "facets_path":
                touching.add(module)
            if isinstance(node, ast.Constant) and node.value == "facets.yaml":
                touching.add(module)
            if isinstance(node, ast.Call) and _called(node) in calls:
                calls[_called(node)].add(module)
            if isinstance(node, ast.Call) and _called(node) in _FILE_WRITES and any(
                (isinstance(inner, ast.Attribute) and inner.attr == "facets_path")
                or (isinstance(inner, ast.Constant) and inner.value == "facets.yaml")
                for argument in [node.func, *node.args, *(keyword.value for keyword in node.keywords)]
                for inner in ast.walk(argument)
            ):
                writers.add(module)
            if (module == "learnloop/content/proposals/patches.py" and isinstance(node, ast.FunctionDef)
                    and node.name == "_compile_facet"):
                inner = {_called(call) for call in ast.walk(node) if isinstance(call, ast.Call)}
                compile_facet_checks = {"check_meaning_write", "upsert_facet"} <= inner

    assert touching <= set(_REGISTRY_FILE_MODULES), sorted(touching - set(_REGISTRY_FILE_MODULES))
    # Only the chokepoint (and the empty registry of a new vault) writes the file;
    # ``upsert_facet`` writes a staging copy for the proposal compiler.
    assert writers <= {"learnloop/content/facet_identity/authority.py", "learnloop/vault/loader.py",
                       "learnloop/vault/writer.py"}, sorted(writers)
    for name, allowed in _GUARDED_CALLS.items():
        assert calls[name] <= allowed, (name, sorted(calls[name] - allowed))
    assert compile_facet_checks, "_compile_facet must check a write's meaning before upsert_facet writes it"
    # The proposal writer's own file write is checked against what compile authorized.
    patches = (_SRC / "learnloop/content/proposals/patches.py").read_text(encoding="utf-8")
    assert "verify_registry_transition" in patches
