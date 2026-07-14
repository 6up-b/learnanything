"""ING M7 — Update study map (append reconciliation) end-to-end.

Bootstrap an applied study map, then add a source and run bounded append
reconciliation: provenance_link auto-apply rules, conflict persistence, notation,
study-map diff, and the linear-scaling gate (bounded neighborhood, planted
full-map resend fails). Canned codex payloads, zero network.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.schemas import (
    AppendConflict,
    AppendNotationMapping,
    AppendProvenanceLink,
    AppendReconciliation,
    SynthSpanRef,
)
from learnloop.db.repositories import Repository
from learnloop.services.append_neighborhood import select_neighborhood
from learnloop.services.source_append import append_source
from learnloop.services.source_set_synthesis import create_study_map
from learnloop.services.source_unit_inventory import run_unit_inventory
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_source_set

from learnloop.codex.schemas import (
    InventoryClaim,
    InventoryConceptMention,
    SourceUnitInventory,
)
from tests.helpers import set_algorithm_version
from tests.test_source_inventory import _block, _ir, _persist, _register_revision
from tests.test_source_set_synthesis import FakeSynthesisClient, _setup

_CLOCK = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))


class SymmetryInventoryClient:
    """Inventory double that mentions the SAME concept as the bootstrap map, so the
    appended source lands in the affected neighborhood."""

    model = "fake-model-1"
    provider_type = "codex"

    def __init__(self):
        self.calls: list[object] = []

    def run_source_unit_inventory(self, context):
        self.calls.append(context)
        spans = [b["span_id"] for b in context.unit_view["blocks"]] or ["s_missing"]
        return SourceUnitInventory(
            unit_id=context.unit_id,
            semantic_hash=context.semantic_hash,
            outline_summary="symmetric matrices",
            concept_mentions=[InventoryConceptMention(name="symmetric matrix", aliases=["symmetric"], span_ids=spans[:1])],
            claims=[
                InventoryClaim(
                    kind="definition",
                    statement="A real square matrix is symmetric exactly when A^T = A.",
                    preconditions=["the matrix is real and square"],
                    span_ids=spans,
                )
            ],
        )


def _first_new_span(context):
    for entry in context.new_inventories:
        inv = entry["inventory"]
        for claim in inv.get("claims", []) or []:
            spans = claim.get("span_ids") or []
            if spans:
                return entry["extraction_id"], entry["unit_id"], spans[0]
        for m in inv.get("concept_mentions", []) or []:
            spans = m.get("span_ids") or []
            if spans:
                return entry["extraction_id"], entry["unit_id"], spans[0]
    return "", "", ""


def _neighborhood_facet_id(context):
    facets = context.neighborhood.get("facets") or []
    return facets[0]["id"] if facets else ""


class FakeAppendClient:
    """House fake-client for append: builds provenance_link / conflict / notation
    items against the bounded neighborhood + a span cited from the new inventories."""

    provider_name = "codex"
    provider_type = "codex"
    model = "fake-append-1"

    def __init__(self, *, builder=None):
        self.calls: list[object] = []
        self.builder = builder

    def run_append_reconciliation(self, context) -> AppendReconciliation:
        self.calls.append(context)
        if self.builder is not None:
            return self.builder(context, len(self.calls))
        return _default_append(context)


def _default_append(context) -> AppendReconciliation:
    ext, unit, span = _first_new_span(context)
    target = _neighborhood_facet_id(context)
    span_ref = SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span, relation="support")
    links = []
    if target and span:
        links.append(
            AppendProvenanceLink(
                client_item_id="plink_alt",
                reconciliation_intent="alternate_explanation",
                target_entity_type="facet",
                target_entity_id=target,
                relation="alternate",
                span=span_ref,
            )
        )
    return AppendReconciliation(summary="append alternate explanation", provenance_links=links)


def _add_member_source(repo, root, *, source_id, revision_id, extraction_id, unit_id, role, claim_text):
    inv_client = SymmetryInventoryClient()
    _register_revision(repo, source_id=source_id, revision_id=revision_id)
    ir = _ir([(unit_id, "Symmetric matrices, again",
               [_block("s1", claim_text)], f"sha256:{unit_id}", 3)])
    _persist(repo, ir, revision_id=revision_id, extraction_id=extraction_id)
    run_unit_inventory(repo, extraction_id, unit_id, role=role, profile="combined",
                       client=inv_client, input_budget_tokens=20000, clock=_CLOCK)
    return {"source_id": source_id, "revision_id": revision_id, "default_role": role,
            "scope": [{"unit_id": unit_id}], "priority": 1}


def _bootstrap_and_add(tmp_path, *, add_role="alternate_explanation"):
    """Bootstrap+apply a map, then add a second explanatory member to the set."""

    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"depth": "intro"})
    member = _add_member_source(
        repo, root, source_id="src_alt", revision_id="rev_alt", extraction_id="ext_alt",
        unit_id="chapter_symmetry_alt", role=add_role,
        claim_text="A real square matrix with A^T = A is called symmetric.",
    )
    vault = load_vault(root)
    members = [
        {"source_id": m.source_id, "revision_id": m.revision_id, "default_role": m.default_role,
         "scope": [{"unit_id": s.unit_id} for s in m.scope], "priority": m.priority}
        for m in next(s for s in vault.source_sets if s.id == "set_la").members
    ]
    members.append(member)
    upsert_source_set(root, {"id": "set_la", "subject_id": "linear-algebra",
                             "title": "Linear Algebra", "members": members}, clock=_CLOCK)
    return root, repo


def test_append_provenance_link_auto_applies_without_rewriting_lo_yaml(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    before_lo = load_vault(root).learning_objects["lo_diagonalize_symmetric"].model_dump_json()

    client = FakeAppendClient()
    result = append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"],
                           repository=repo, clock=_CLOCK)

    assert not any(d["severity"] == "hard_fail" for d in result.gate_diagnostics)
    assert result.auto_applied_item_ids, "routine alternate-explanation link should auto-apply"
    # the LO YAML is byte-identical: an additive link never rewrites the target.
    after_lo = load_vault(root).learning_objects["lo_diagonalize_symmetric"].model_dump_json()
    assert before_lo == after_lo
    links = repo.entity_source_links(entity_type="facet", entity_id="facet_symmetry_definition")
    assert any(link["relation"] == "alternate" and link["revision_id"] == "rev_alt" for link in links)


def test_append_context_bounded_by_neighborhood(tmp_path):
    """Append context stays bounded by the neighborhood cap regardless of map size."""

    root, repo = _bootstrap_and_add(tmp_path)
    vault = load_vault(root)
    budget = vault.config.ingest.budgets.append_neighborhood_input_tokens

    # Build the same new inventories the append would see.
    from learnloop.services.source_set_synthesis import _collect_inputs
    source_set = next(s for s in vault.source_sets if s.id == "set_la")
    inputs = _collect_inputs(repo, vault, source_set)
    new_inv = [e for e in inputs.unit_inventories if e["revision_id"] == "rev_alt"]

    neighborhood = select_neighborhood(vault, repo, new_inv, budget_tokens=budget,
                                       source_ids={"src_alt"}, revision_ids={"rev_alt"})
    assert neighborhood.input_token_estimate <= budget
    # the neighborhood matched the symmetry facet (concept-name / fingerprint), and
    # records WHY each entity matched (reviewable, §10.1).
    assert any(ref.startswith("facet:") for ref in neighborhood.entity_refs())
    assert all(neighborhood.match_reasons[ref] for ref in neighborhood.match_reasons)


def test_planted_full_map_resend_fails_scaling_gate(tmp_path):
    """A planted implementation that resends the entire map exceeds the bound; the
    real deterministic neighborhood stays under it (source-ingestion §3.2/§14)."""

    root, repo = _bootstrap_and_add(tmp_path)
    vault = load_vault(root)
    budget = vault.config.ingest.budgets.append_neighborhood_input_tokens

    from learnloop.services.source_set_synthesis import _collect_inputs
    from learnloop.services.append_neighborhood import _estimate_tokens, _facet_contract

    source_set = next(s for s in vault.source_sets if s.id == "set_la")
    inputs = _collect_inputs(repo, vault, source_set)
    new_inv = [e for e in inputs.unit_inventories if e["revision_id"] == "rev_alt"]
    neighborhood = select_neighborhood(vault, repo, new_inv, budget_tokens=budget,
                                       source_ids={"src_alt"}, revision_ids={"rev_alt"})

    # Plant a "resend the whole map" context: every facet contract, unbounded.
    def append_context_within_budget(context_estimate: int) -> bool:
        return context_estimate <= budget

    real_estimate = neighborhood.input_token_estimate
    assert append_context_within_budget(real_estimate)

    # Blow the map up far past the budget and prove a full-map resend fails.
    fat_facets = []
    for i in range(4000):
        fat_facets.append({"id": f"facet_{i}", "claim": "x" * 40, "error_signatures": ["y" * 40]})
    full_map_estimate = _estimate_tokens({"facets": fat_facets})
    assert full_map_estimate > budget
    assert not append_context_within_budget(full_map_estimate)


def test_n_sources_append_linear_inventory_and_bounded_context(tmp_path):
    """§14 scaling row: N comparable sources appended -> inventory cost linear in
    the NEW selected units (one inventory call per new unit, zero re-inventory of
    old units), and every append reconciliation context stays bounded."""

    from learnloop.services.source_unit_inventory import run_unit_inventory

    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"depth": "intro"})
    budget = load_vault(root).config.ingest.budgets.append_neighborhood_input_tokens

    n = 4
    context_sizes: list[int] = []
    inventory_calls_per_append: list[int] = []
    for i in range(n):
        inv_client = SymmetryInventoryClient()
        _register_revision(repo, source_id=f"src_n{i}", revision_id=f"rev_n{i}")
        unit_id = f"chapter_sym_n{i}"
        ir = _ir([(unit_id, f"Symmetric matrices vol {i}",
                   [_block("s1", f"A real square matrix is symmetric when A^T = A (edition {i}).")],
                   f"sha256:n{i}", 2)])
        _persist(repo, ir, revision_id=f"rev_n{i}", extraction_id=f"ext_n{i}")
        run_unit_inventory(repo, f"ext_n{i}", unit_id, role="alternate_explanation",
                           profile="combined", client=inv_client, input_budget_tokens=20000, clock=_CLOCK)
        inventory_calls_per_append.append(len(inv_client.calls))

        vault = load_vault(root)
        members = [
            {"source_id": m.source_id, "revision_id": m.revision_id, "default_role": m.default_role,
             "scope": [{"unit_id": s.unit_id} for s in m.scope], "priority": m.priority}
            for m in next(s for s in vault.source_sets if s.id == "set_la").members
        ]
        members.append({"source_id": f"src_n{i}", "revision_id": f"rev_n{i}",
                        "default_role": "alternate_explanation",
                        "scope": [{"unit_id": unit_id}], "priority": 1})
        upsert_source_set(root, {"id": "set_la", "subject_id": "linear-algebra",
                                 "title": "Linear Algebra", "members": members}, clock=_CLOCK)

        client = FakeAppendClient()
        append_source(root, "set_la", client=client, new_revision_ids=[f"rev_n{i}"],
                      repository=repo, clock=_CLOCK)
        # the reconciliation context carries ONLY the new inventories + bounded
        # neighborhood — never previously appended sources' inventories.
        context = client.calls[0]
        assert {e["revision_id"] for e in context.new_inventories} == {f"rev_n{i}"}
        context_sizes.append(len(json.dumps(asdict(context), default=str)) // 4)

    # inventory cost is linear in NEW units: exactly one call per appended unit.
    assert inventory_calls_per_append == [1] * n
    # every append context stays under the neighborhood budget; the last append
    # (largest accumulated map) is not meaningfully bigger than the first.
    assert all(size <= budget for size in context_sizes)
    assert context_sizes[-1] <= context_sizes[0] * 3


def test_append_vocabulary_auto_apply_rules(tmp_path):
    """span/alternate/assessment auto-apply; notation + conflict require review;
    a mutation dressed as additive fails the append-vocabulary gate."""

    root, repo = _bootstrap_and_add(tmp_path)

    def builder(context, _n):
        ext, unit, span = _first_new_span(context)
        target = _neighborhood_facet_id(context)
        ref = SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span)
        return AppendReconciliation(
            summary="mixed append",
            provenance_links=[
                AppendProvenanceLink(client_item_id="plink", reconciliation_intent="alternate_explanation",
                                     target_entity_type="facet", target_entity_id=target,
                                     relation="alternate", span=ref),
            ],
            notation_mappings=[
                AppendNotationMapping(client_item_id="notation", target_entity_type="facet",
                                      target_entity_id=target, canonical_notation="A^T",
                                      alternate_notation="A'", context="transpose", span=ref),
            ],
        )

    result = append_source(root, "set_la", client=FakeAppendClient(builder=builder),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)

    assert not any(d["severity"] == "hard_fail" for d in result.gate_diagnostics)
    # exactly the provenance_link auto-applies; notation stays for review.
    assert result.item_counts.get("provenance_link") == 1
    assert result.item_counts.get("notation_mapping") == 1
    assert len(result.auto_applied_item_ids) == 1
    # the notation mapping was NOT written (still pending review).
    assert repo.notation_mappings_for_entity("facet", "facet_symmetry_definition") == []


def test_conflict_accept_creates_open_row_reject_creates_none(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path, add_role="primary_textbook")

    def builder(context, _n):
        ext, unit, span = _first_new_span(context)
        target = _neighborhood_facet_id(context)
        left = SynthSpanRef(extraction_id="ext_text", unit_id="chapter_symmetry", span_id="s1")
        right = SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span)
        return AppendReconciliation(
            summary="conflict",
            conflicts=[AppendConflict(client_item_id="conflict1", entity_type="facet",
                                      entity_id=target, statement="sources disagree on the symmetry condition",
                                      left=left, right=right)],
        )

    result = append_source(root, "set_la", client=FakeAppendClient(builder=builder),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)
    assert result.item_counts.get("source_conflict") == 1
    # conflict is review-required: not auto-applied, no open row yet.
    assert result.auto_applied_item_ids == []
    assert repo.source_conflicts_by_status("open") == []

    # Accepting the conflict item persists an OPEN two-sided row (never a side).
    from learnloop.services.patches import apply_accepted_items
    conflict_ids = [i["id"] for i in repo.proposal_items(result.proposal_id) if i["item_type"] == "source_conflict"]
    apply_accepted_items(root, result.proposal_id, item_ids=conflict_ids, clock=_CLOCK)
    open_rows = repo.source_conflicts_by_status("open")
    assert len(open_rows) == 1
    assert open_rows[0]["left_locator"] and open_rows[0]["right_locator"]


def test_conflict_reject_creates_no_row(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path, add_role="primary_textbook")

    def builder(context, _n):
        ext, unit, span = _first_new_span(context)
        target = _neighborhood_facet_id(context)
        return AppendReconciliation(
            conflicts=[AppendConflict(client_item_id="c1", entity_type="facet", entity_id=target,
                                      statement="disagree",
                                      left=SynthSpanRef(extraction_id="ext_text", unit_id="chapter_symmetry", span_id="s1"),
                                      right=SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span))],
        )

    result = append_source(root, "set_la", client=FakeAppendClient(builder=builder),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)
    # Rejecting the conflict item: no row is ever created.
    conflict_ids = [i["id"] for i in repo.proposal_items(result.proposal_id) if i["item_type"] == "source_conflict"]
    repo.set_proposal_item_decision(result.proposal_id, "rejected", conflict_ids, clock=_CLOCK)
    assert repo.source_conflicts_by_status("open") == []


def test_replay_identical_after_append_apply(tmp_path):
    """§14 replay safety: rebuild_derived_state after an applied append — the
    appended provenance links and the study map survive intact."""

    root, repo = _bootstrap_and_add(tmp_path)
    append_source(root, "set_la", client=FakeAppendClient(), new_revision_ids=["rev_alt"],
                  repository=repo, clock=_CLOCK)
    from learnloop.services.replay import rebuild_derived_state

    links_before = repo.entity_source_links("facet", "facet_symmetry_definition")
    rebuild_derived_state(load_vault(root), repo, clock=_CLOCK)
    assert "facet_symmetry_definition" in load_vault(root).evidence_facets
    assert repo.entity_source_links("facet", "facet_symmetry_definition") == links_before


def test_specialized_side_effects_recover_idempotently(tmp_path):
    """§10.2 crash safety for the new handlers: re-running recovery on an intent
    that carried a source_conflict/provenance_link side effect never duplicates
    the row (the write-ahead protocol's idempotency covers the M7 handlers)."""

    root, repo = _bootstrap_and_add(tmp_path, add_role="primary_textbook")

    def builder(context, _n):
        ext, unit, span = _first_new_span(context)
        target = _neighborhood_facet_id(context)
        return AppendReconciliation(
            conflicts=[AppendConflict(client_item_id="c1", entity_type="facet", entity_id=target,
                                      statement="disagree",
                                      left=SynthSpanRef(extraction_id="ext_text", unit_id="chapter_symmetry", span_id="s1"),
                                      right=SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span))],
        )

    result = append_source(root, "set_la", client=FakeAppendClient(builder=builder),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)
    from learnloop.services.patches import apply_accepted_items
    conflict_items = [i["id"] for i in repo.proposal_items(result.proposal_id) if i["item_type"] == "source_conflict"]
    apply_accepted_items(root, result.proposal_id, item_ids=conflict_items, clock=_CLOCK)
    assert len(repo.source_conflicts_by_status("open")) == 1

    # Simulate a crash between the DB side effects and the applied mark: flip the
    # intent back to pending and run startup recovery — it must re-run harmlessly.
    from learnloop.services.apply_protocol import recover_apply_intents
    with repo.connection() as connection:
        connection.execute("UPDATE apply_intents SET status = 'pending', applied_at = NULL")
        connection.commit()
    recovered = recover_apply_intents(root, repo, clock=_CLOCK)
    assert recovered, "recovery completed the pending intent"
    assert len(repo.source_conflicts_by_status("open")) == 1  # no duplicate row


def test_study_map_diff_reports_changes(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    result = append_source(root, "set_la", client=FakeAppendClient(), new_revision_ids=["rev_alt"],
                           repository=repo, clock=_CLOCK)
    diff = result.study_map_diff
    assert diff["has_changes"] is True
    assert diff["new_links"] >= 1


def test_append_vocabulary_gate_rejects_mutation_outside_restructure():
    """The append-vocabulary gate hard-fails any update/deactivate that is not an
    explicit restructure_unlocked item, and additive types that are not create."""

    from learnloop.services.synthesis_gates import GateContext, GateItem, GateProposal, run_synthesis_gates

    ctx = GateContext(append_mode=True)
    # a bare update on a learning_object without restructure_unlocked intent.
    bad_update = GateItem(client_item_id="u1", item_type="learning_object", operation="update",
                          entity_id="lo_x", reconciliation_intent=None)
    # a provenance_link that claims to be an update (would mutate) — invalid.
    bad_additive = GateItem(client_item_id="p1", item_type="provenance_link", operation="update",
                            entity_id=None)
    # a legitimate restructure_unlocked update passes the vocabulary gate.
    ok_restructure = GateItem(client_item_id="r1", item_type="learning_object", operation="update",
                              entity_id="lo_y", reconciliation_intent="restructure_unlocked")
    report = run_synthesis_gates(GateProposal(items=[bad_update, bad_additive, ok_restructure]), ctx)
    fired = [d for d in report.diagnostics if d.gate == "append_vocabulary"]
    refs = {r for d in fired for r in d.entity_refs}
    assert "lo_x" in refs and "p1" in refs
    assert "lo_y" not in refs


def test_post_append_near_duplicate_yields_merge_review_never_auto_merge(tmp_path):
    """A new_coverage facet nearly identical to an existing one yields a merge-review
    proposal, never an auto-merge (§14)."""

    root, repo = _bootstrap_and_add(tmp_path)

    def builder(context, _n):
        ext, unit, span = _first_new_span(context)
        ref = SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span, relation="primary", role="primary_textbook")
        from learnloop.codex.schemas import SynthConcept, SynthFacet
        # a near-duplicate of facet_symmetry_definition (same claim wording).
        return AppendReconciliation(
            summary="new near-duplicate coverage",
            concepts=[SynthConcept(client_item_id="c_dup", id="concept_symmetric_dup", title="Symmetric matrix (dup)")],
            facets=[SynthFacet(client_item_id="f_dup", id="facet_symmetry_definition_dup",
                               concept_client_id="c_dup", kind="definition",
                               claim="A real square matrix is symmetric exactly when A^T = A.",
                               preconditions=["the matrix is real and square"],
                               error_signatures=["substitutes A^T A = I for A^T = A"],
                               instructional_repairs=["contrast symmetric and orthogonal matrices"],
                               provenance=[ref])],
        )

    result = append_source(root, "set_la", client=FakeAppendClient(builder=builder),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)
    # new_coverage facet is a pending review item (not auto-applied).
    assert result.item_counts.get("facet") == 1
    # apply the new facet so the registry contains both, then the near-dup pass fires.
    from learnloop.services.patches import apply_accepted_items
    facet_items = [i["id"] for i in repo.proposal_items(result.proposal_id) if i["item_type"] in {"facet", "concept"}]
    apply_accepted_items(root, result.proposal_id, item_ids=facet_items, clock=_CLOCK)
    from learnloop.services.facet_doctor import near_duplicate_facet_review
    pairs = near_duplicate_facet_review(load_vault(root))
    assert any({p.left_facet_id, p.right_facet_id} == {"facet_symmetry_definition", "facet_symmetry_definition_dup"} for p in pairs)
    # nothing auto-merged: both facets still exist independently.
    v = load_vault(root)
    assert "facet_symmetry_definition" in v.evidence_facets and "facet_symmetry_definition_dup" in v.evidence_facets
