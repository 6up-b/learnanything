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

import pytest

from tests.facet_identity_fakes import supporting_span_decider  # noqa: F401

from learnloop.content.facet_identity import actions as facet_actions
from learnloop.content.facet_identity.actions import FacetIdentityActionError, list_actions
from learnloop.content.proposals.patches import PatchApplicationError, apply_accepted_items
from learnloop.content.synthesis.ai_contracts import (
    AppendReconciliation,
    SourceSetSynthesis,
    SynthFacet,
    SynthSpanRef,
)
from learnloop.content.synthesis.source_append import append_source
from learnloop.content.synthesis.source_set_synthesis import (
    StudyMapError,
    _collect_inputs,
    _normalize,
    _span_refs,
)
from learnloop.content.synthesis.synthesis_gates import (
    GateContext,
    GateItem,
    GateProposal,
    ProvenanceRef,
    run_synthesis_gates,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, yaml_to_string

from tests.facet_identity_actions_helpers import SHARED, _vault_with_duplicate
from tests.facet_reword_paths_helpers import NEW_SPAN, SYMMETRY, TEXT_SPAN, _facet_restructure
from tests.facet_rewords_helpers import OLD_CLAIM
from tests.source_append_helpers import FakeAppendClient, _bootstrap_and_add
from tests.source_set_synthesis_helpers import _setup
from tests.facet_authority_helpers import (
    EXAM_CLAIM,
    EXAM_CONDITION,
    EXAM_SPAN,
    NEW_CLAIM,
    NOW,
    SUBJECT,
    _CLOCK,
    _GUARDED_CALLS,
    _REGISTRY_FILE_MODULES,
    _SRC,
    _add_member,
    _add_two_units,
    _called,
    _consolidation,
    _exam_alias_consolidation,
    _exam_vault,
    _facet_proposal,
    _meaning,
    _owner_judgments,
    _python_sources,
    _source_set,
    _support,
)

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


def _accept_pending(root, repo, proposal_id) -> None:
    pending = [row["id"] for row in repo.proposal_items(proposal_id or "") or [] if row["decision"] == "pending"]
    if pending:
        try:
            apply_accepted_items(root, proposal_id, item_ids=pending, clock=_CLOCK)
        except PatchApplicationError:
            pass  # refused at the writer: equally safe, checked by the caller's assertions


def _registry_entry(root, facet_id):
    vault = load_vault(root)
    data = read_yaml(VaultPaths(vault.root, vault.config).facets_path)
    return next(entry for entry in data["facets"] if entry["id"] == facet_id)


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


#: Calls that write a file.
_FILE_WRITES = {"write_yaml", "write_text", "write_bytes", "materialize_targets", "replace", "rename",
                "unlink", "open"}


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
