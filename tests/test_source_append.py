"""ING M7 — Update study map (append reconciliation) end-to-end.

Bootstrap an applied study map, then add a source and run bounded append
reconciliation: provenance_link auto-apply rules, conflict persistence, notation,
study-map diff, and the linear-scaling gate (bounded neighborhood, planted
full-map resend fails). Canned codex payloads, zero network.
"""

from __future__ import annotations

import json
from dataclasses import asdict

import pytest

from learnloop.ai.execution import output_limit
from learnloop.content.synthesis.ai_contracts import (
    AppendConflict,
    AppendNotationMapping,
    AppendProvenanceLink,
    AppendReconciliation,
    AppendRestructure,
    SynthSpanRef,
)
from learnloop.content.synthesis.append_neighborhood import select_neighborhood
from learnloop.content.synthesis.source_append import append_source
from learnloop.content.synthesis.source_set_synthesis import StudyMapError, create_study_map
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_source_set

from tests.facet_reword_paths_helpers import _facet_restructure
from tests.source_inventory_helpers import _block, _ir, _persist, _register_revision
from tests.source_set_synthesis_helpers import FakeSynthesisClient, _setup
from tests.source_append_helpers import (
    FakeAppendClient,
    SymmetryInventoryClient,
    _CLOCK,
    _bootstrap_and_add,
    _default_append,
    _first_new_span,
    _neighborhood_facet_id,
)

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


def test_narrow_adjunct_deterministically_drops_model_restructures(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)

    def builder(context, _n):
        additive = _default_append(context)
        return additive.model_copy(
            update={
                "restructures": [
                    AppendRestructure(
                        client_item_id="forbidden_restructure",
                        target_entity_type="learning_object",
                        target_entity_id="lo_diagonalize_symmetric",
                        operation="deactivate",
                    )
                ]
            }
        )

    result = append_source(
        root,
        "set_la",
        client=FakeAppendClient(builder=builder),
        new_revision_ids=["rev_alt"],
        brief={"authoring_preset": "narrow_adjunct"},
        repository=repo,
        clock=_CLOCK,
    )

    assert result.auto_applied_item_ids  # the additive provenance link survives
    assert not any(
        item["client_item_id"] == "forbidden_restructure"
        for item in repo.proposal_items(result.proposal_id)
    )
    assert any(
        diagnostic["gate"] == "narrow_adjunct"
        and "dropped 1 model-emitted restructure" in diagnostic["message"]
        for diagnostic in result.gate_diagnostics
    )


def test_append_context_bounded_by_neighborhood(tmp_path):
    """Append context stays bounded by the neighborhood cap regardless of map size."""

    root, repo = _bootstrap_and_add(tmp_path)
    vault = load_vault(root)
    budget = vault.config.ingest.budgets.append_neighborhood_input_tokens

    # Build the same new inventories the append would see.
    from learnloop.content.synthesis.source_set_synthesis import _collect_inputs
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

    from learnloop.content.synthesis.source_set_synthesis import _collect_inputs
    from learnloop.content.synthesis.append_neighborhood import _estimate_tokens

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

    from learnloop.content.synthesis.source_unit_inventory import run_unit_inventory

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
    from learnloop.content.proposals.patches import apply_accepted_items
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
    from learnloop.substrate.replay import rebuild_derived_state

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
    from learnloop.content.proposals.patches import apply_accepted_items
    conflict_items = [i["id"] for i in repo.proposal_items(result.proposal_id) if i["item_type"] == "source_conflict"]
    apply_accepted_items(root, result.proposal_id, item_ids=conflict_items, clock=_CLOCK)
    assert len(repo.source_conflicts_by_status("open")) == 1

    # Simulate a crash between the DB side effects and the applied mark: flip the
    # intent back to pending and run startup recovery — it must re-run harmlessly.
    from learnloop.content.proposals.apply_protocol import recover_apply_intents
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

    from learnloop.content.synthesis.synthesis_gates import GateContext, GateItem, GateProposal, run_synthesis_gates

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


def test_post_append_near_duplicate_is_aliased_at_mint_and_never_auto_merged(tmp_path):
    """Two rules, at two different times, and they do not conflict.

    Plan item 5.4 / Meas D2 moved the *mint* gate upstream onto the append path
    too, so a near-duplicate `new_coverage` facet no longer earns an id: it is
    registered as an alias of the facet it collapses into ("alias-not-mint"). D2
    also says Phase D's review loop is "otherwise unchanged", and it is — §14's
    near-duplicate doctor still only ever *proposes* a merge for facets that are
    already registered, which the second half of this test pins.

    The two are consistent: D2 governs admission (the second entry never exists),
    §14 governs two entries that already do (never merged without a human).
    """

    root, repo = _bootstrap_and_add(tmp_path)

    def builder(context, _n):
        ext, unit, span = _first_new_span(context)
        ref = SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span, relation="primary", role="primary_textbook")
        from learnloop.content.synthesis.ai_contracts import SynthConcept, SynthFacet
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
    # D2: identical error signature AND identical repair -> one obligation, two ids.
    # The single facet row is the alias registration, not a new facet, and it is a
    # pending review item (never auto-applied).
    assert result.item_counts.get("facet") == 1
    mint = [d for d in result.gate_diagnostics if d["gate"] == "facet_mint"]
    assert len(mint) == 1 and "same_repair_class" in mint[0]["message"]
    from learnloop.content.proposals.patches import apply_accepted_items
    facet_items = [i["id"] for i in repo.proposal_items(result.proposal_id) if i["item_type"] in {"facet", "concept"}]
    apply_accepted_items(root, result.proposal_id, item_ids=facet_items, clock=_CLOCK)

    v = load_vault(root)
    assert "facet_symmetry_definition_dup" not in v.evidence_facets
    assert "facet_symmetry_definition_dup" in v.evidence_facets["facet_symmetry_definition"].aliases
    # The id still resolves, so nothing filed against it is lost.
    assert v.canonical_facet_id("facet_symmetry_definition_dup") == "facet_symmetry_definition"

    # §14, unchanged: two facets that ARE both registered (legacy content, minted
    # before D2 existed) still only ever yield a merge-review proposal.
    from learnloop.vault.writer import upsert_facet

    upsert_facet(root, {
        "id": "facet_spectral_legacy_dup",
        "kind": "applicability_condition",
        "claim": "The spectral theorem applies to real symmetric matrices.",
        "error_signatures": ["applies spectral theorem to non-symmetric matrices"],
        "instructional_repairs": ["check symmetry before invoking the spectral theorem"],
        "status": "reviewed",
    }, clock=_CLOCK)
    from learnloop.content.synthesis.facet_doctor import near_duplicate_facet_review
    pairs = near_duplicate_facet_review(load_vault(root))
    assert any(
        {p.left_facet_id, p.right_facet_id}
        == {"facet_spectral_applicability", "facet_spectral_legacy_dup"}
        for p in pairs
    )
    # Nothing auto-merged: both registered facets still exist independently.
    v = load_vault(root)
    assert "facet_spectral_applicability" in v.evidence_facets
    assert "facet_spectral_legacy_dup" in v.evidence_facets


def test_append_budget_overrides_reach_the_manifest(tmp_path):
    """A per-run ceiling set on the build-plan screen must bind on the UPDATE
    path too. `mode="auto"` routes to append whenever the subject already has a
    map, so without this seam the override silently did nothing there."""

    root, repo = _bootstrap_and_add(tmp_path)
    default_budget = load_vault(root).config.ingest.budgets.append_neighborhood_input_tokens

    result = append_source(
        root, "set_la", client=FakeAppendClient(), new_revision_ids=["rev_alt"],
        repository=repo, clock=_CLOCK,
        budget_overrides={"append_neighborhood_input_tokens": default_budget // 2},
    )

    manifest = repo.synthesis_manifest_by_hash(result.manifest_hash)
    assert manifest["token_budget"]["append_neighborhood_input_tokens"] == default_budget // 2
    # The vault default is untouched — the override is per run, not a mutation.
    assert (
        load_vault(root).config.ingest.budgets.append_neighborhood_input_tokens == default_budget
    )


def test_provenance_links_without_a_resolvable_span_are_dropped_not_hard_failed(tmp_path):
    """A chat provider that never saw the schema leaves ``span`` blank (or
    invents one). Either way the link has nothing to attach: it is dropped
    with a typed review record, and the paid run still lands its other items
    instead of hard-failing on a citation to span "" of extraction ""."""

    root, repo = _bootstrap_and_add(tmp_path)

    def builder(context, _n):
        good = _default_append(context)
        target = _neighborhood_facet_id(context)
        ext, unit, _span = _first_new_span(context)
        return good.model_copy(
            update={
                "provenance_links": [
                    *good.provenance_links,
                    AppendProvenanceLink(
                        client_item_id="plink_blank",
                        target_entity_type="facet",
                        target_entity_id=target,
                        span=SynthSpanRef(),
                    ),
                    AppendProvenanceLink(
                        client_item_id="plink_invented",
                        target_entity_type="facet",
                        target_entity_id=target,
                        span=SynthSpanRef(extraction_id=ext, unit_id=unit, span_id="s_invented"),
                    ),
                ]
            }
        )

    result = append_source(root, "set_la", client=FakeAppendClient(builder=builder),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)

    assert not any(d["severity"] == "hard_fail" for d in result.gate_diagnostics)
    dropped = [d for d in result.gate_diagnostics if d["gate"] == "provenance_link_span"]
    assert {d["entity_refs"][0] for d in dropped} == {"plink_blank", "plink_invented"}
    assert all(d["severity"] == "review" for d in dropped)
    assert any("no span cited" in d["message"] for d in dropped)
    assert any("s_invented" in d["message"] for d in dropped)
    # The well-cited link still lands and auto-applies.
    assert result.item_counts.get("provenance_link") == 1
    assert result.auto_applied_item_ids


def test_provenance_link_span_without_a_unit_id_still_resolves(tmp_path):
    """``unit_id`` is optional on a citation (the gate skips None); a blank one
    must not be read as "unit '' is invalid"."""

    root, repo = _bootstrap_and_add(tmp_path)

    def builder(context, _n):
        good = _default_append(context)
        link = good.provenance_links[0]
        return good.model_copy(
            update={"provenance_links": [link.model_copy(update={"span": link.span.model_copy(update={"unit_id": ""})})]}
        )

    result = append_source(root, "set_la", client=FakeAppendClient(builder=builder),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)

    assert not any(d["severity"] == "hard_fail" for d in result.gate_diagnostics)
    assert result.item_counts.get("provenance_link") == 1
    assert result.auto_applied_item_ids


def test_append_persists_vault_epigraphs(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    client = FakeAppendClient()

    result = append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"],
                           repository=repo, clock=_CLOCK)

    rows = [row for row in repo.recent_vault_epigraphs(subject_id="linear-algebra", limit=50)
            if row["mode"] == "append"]
    assert len(rows) == 3
    assert {row["synthesis_run_id"] for row in rows} == {result.synthesis_run_id}
    context = client.epigraph_calls[0]
    assert context.mode == "append"
    assert context.source_set_id == "set_la"
    # A provenance-link-only append still has material: the new inventory's
    # claim and the neighborhood's facets feed the digest.
    assert any("symmetric" in claim.lower() for claim in context.claims)
    # The bootstrap's epigraphs are handed back as "don't repeat these".
    assert len(context.recent_epigraphs) == 3
    # Newest first: the append batch precedes the bootstrap batch.
    assert repo.recent_vault_epigraphs(subject_id="linear-algebra")[0]["mode"] == "append"


def test_append_epigraph_failure_leaves_the_append_unchanged(tmp_path):
    def exploding(_context, _n):
        raise RuntimeError("epigraph provider down")

    root, repo = _bootstrap_and_add(tmp_path)
    result = append_source(root, "set_la", client=FakeAppendClient(epigraph_builder=exploding),
                           new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK)

    assert not any(d["severity"] == "hard_fail" for d in result.gate_diagnostics)
    assert result.auto_applied_item_ids
    assert repo.synthesis_run(result.synthesis_run_id)["status"] == "completed"
    assert all(row["mode"] == "bootstrap"
               for row in repo.recent_vault_epigraphs(subject_id="linear-algebra", limit=50))


# --- K3.4: the append call is bounded and checkpointed ----------------------
#
# The append call had no per-call checkpoint, no request-level output limit and
# no input ceiling: a retry re-paid it, and a budget failure left both run rows
# `running` (refactor K3.4; map KX2, KM4, KB5).


def _append_run_statuses(repo) -> tuple[list[str], list[str]]:
    with repo.connection() as connection:
        agent = [row[0] for row in connection.execute(
            "SELECT status FROM agent_runs WHERE purpose = 'append_reconciliation' ORDER BY rowid")]
        synthesis = [row[0] for row in connection.execute(
            "SELECT status FROM synthesis_runs WHERE mode = 'append' ORDER BY rowid")]
    return agent, synthesis


def _long_summary_append(context, _n):
    return _default_append(context).model_copy(update={"summary": "symmetric " * 400})


def test_a_retry_after_an_append_gate_failure_makes_no_model_call(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path, add_role="exam")
    client = FakeAppendClient(builder=_facet_restructure())

    for _attempt in range(2):
        with pytest.raises(StudyMapError) as raised:
            append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"],
                          repository=repo, clock=_CLOCK)
        assert raised.value.code == "append_gate_failed"

    # The paid answer was checkpointed: the retry read it instead of paying again.
    assert len(client.calls) == 1
    assert _append_run_statuses(repo) == (["failed", "failed"], ["failed", "failed"])


def test_an_over_budget_append_answer_is_checkpointed_and_the_retry_does_not_repay(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    client = FakeAppendClient(builder=_long_summary_append)
    tight = {"append_output_tokens": 200}

    for _attempt in range(2):
        with pytest.raises(StudyMapError) as raised:
            append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"],
                          repository=repo, clock=_CLOCK, budget_overrides=tight)
        assert raised.value.code == "budget_exceeded"
    assert len(client.calls) == 1

    # A raised budget reuses the paid answer: the checkpoint key holds no budget.
    result = append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"],
                           repository=repo, clock=_CLOCK, budget_overrides={"append_output_tokens": 4000})
    assert len(client.calls) == 1
    assert repo.synthesis_run(result.synthesis_run_id)["status"] == "completed"


def test_an_append_budget_failure_leaves_both_run_rows_failed(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    with pytest.raises(StudyMapError) as raised:
        append_source(root, "set_la", client=FakeAppendClient(builder=_long_summary_append),
                      new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK,
                      budget_overrides={"append_output_tokens": 200})

    assert raised.value.code == "budget_exceeded"
    assert _append_run_statuses(repo) == (["failed"], ["failed"])


def test_the_append_call_runs_under_its_output_limit(tmp_path):
    seen: list[int | None] = []

    def builder(context, _n):
        seen.append(output_limit())
        return _default_append(context)

    root, repo = _bootstrap_and_add(tmp_path)
    append_source(root, "set_la", client=FakeAppendClient(builder=builder), new_revision_ids=["rev_alt"],
                  repository=repo, clock=_CLOCK, budget_overrides={"append_output_tokens": 3000})

    assert seen == [3000]


def test_an_append_over_its_input_ceiling_is_refused_before_any_call(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    client = FakeAppendClient()
    with pytest.raises(StudyMapError) as raised:
        append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"],
                      repository=repo, clock=_CLOCK, budget_overrides={"append_input_ceiling": 1000})

    assert raised.value.code == "append_input_over_ceiling"
    assert client.calls == []
    (diagnostic,) = raised.value.diagnostics
    assert diagnostic["gate"] == "append_input_ceiling" and "1,000" in diagnostic["message"]
    assert _append_run_statuses(repo) == (["failed"], ["failed"])

    # Under the default ceiling the same append goes through.
    result = append_source(root, "set_la", client=client, new_revision_ids=["rev_alt"],
                           repository=repo, clock=_CLOCK)
    assert len(client.calls) == 1
    assert repo.synthesis_run(result.synthesis_run_id)["status"] == "completed"


def test_append_output_is_counted_without_escaping_non_ascii(tmp_path):
    """Bootstrap's estimator: a ``\\uXXXX`` escape is six characters for what
    the model wrote as one, so the escaping estimate refused answers that fit."""

    def builder(context, _n):
        return _default_append(context).model_copy(update={"summary": "対称行列" * 150})

    root, repo = _bootstrap_and_add(tmp_path)
    # The summary alone: 3,600 escaped characters (900 tokens), 600 unescaped (150).
    result = append_source(root, "set_la", client=FakeAppendClient(builder=builder), new_revision_ids=["rev_alt"],
                           repository=repo, clock=_CLOCK, budget_overrides={"append_output_tokens": 600})

    assert repo.synthesis_run(result.synthesis_run_id)["status"] == "completed"
