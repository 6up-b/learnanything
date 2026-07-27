"""Ingest-lane consistency: instrument gates, `any_of`/vacuous recipes,
capability observability, append `items_off`, and the recalibration boundary
stamped at content-apply time.

These cover the fixes that closed the ingest bypass: the synthesis lanes used
to persist practice items with no Stage-5.3/6 instrument judgement, the
canonical lane auto-applied them, `any_of`-shaped recipes could be authored
under semantics certification no longer honours, a parse-time capability
default was unobservable, the append lane ignored `items_off`, and applying
ingested content armed a deferred, misattributed recalibration boundary.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.client import CanonicalIngestContext
from learnloop.codex.schemas import (
    AuthoringProposal,
    SynthCriterion,
    SynthCriterionTarget,
    SynthPracticeItem,
    SynthRecipe,
    SynthRecipeComponent,
)
from learnloop.db.repositories import Repository
from learnloop.services.replay import rebuild_derived_state, record_content_recalibration
from learnloop.services.source_append import append_source
from learnloop.services.source_ingestion import (
    _reachability_summary,
    ingest_canonical_source,
)
from learnloop.services.source_set_synthesis import StudyMapError, create_study_map
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault
from tests.test_source_append import FakeAppendClient, _bootstrap_and_add, _first_new_span
from tests.test_source_ingestion import _FakeCanonicalClient, _proposal_payload, _source_file
from tests.test_source_set_synthesis import (
    _CLOCK,
    FakeSynthesisClient,
    _default_payload,
    _setup,
)

try:  # AppendReconciliation lives beside the other synth wire models.
    from learnloop.codex.schemas import AppendReconciliation
except ImportError:  # pragma: no cover
    from learnloop.codex.client import AppendReconciliation  # type: ignore

from learnloop.codex.schemas import SynthSpanRef


# ---------------------------------------------------------------------------
# 1. The synthesis lane runs the shared instrument-gate chain
# ---------------------------------------------------------------------------


def _payload_with_prompt(context, prompt: str):
    payload = _default_payload(context)
    item = payload.practice_items[0]
    payload.practice_items[0] = item.model_copy(update={"prompt": prompt})
    return payload


def test_synthesis_lane_blocks_selected_response_items(tmp_path):
    """A which-of-the-following item authored AT INGEST is refused, exactly as
    it would be on every practice_generation route."""

    root, repo = _setup(tmp_path)
    client = FakeSynthesisClient(
        builder=lambda context, call: _payload_with_prompt(
            context,
            "Which of the following statements is true about symmetric matrices?",
        )
    )
    result = create_study_map(
        root, "set_la", client=client, brief={"depth": "intro"}, repository=repo, clock=_CLOCK
    )
    rows = repo.proposal_items(result.proposal_id)
    practice_rows = [r for r in rows if r["item_type"] == "practice_item"]
    assert practice_rows, "the batch should still persist the refused row for review"
    row = practice_rows[0]
    assert row["validation_status"] == "invalid"
    assert any("selected_response_surface" in e for e in row["validation_errors"])
    assert any(
        d.get("gate") == "selected_response_surface" and d.get("severity") == "hard_fail"
        for d in result.gate_diagnostics
    )


def test_synthesis_lane_records_persona_gate_outcome(tmp_path):
    """Every ingest-authored practice item carries a persona-gate audit record —
    proof the chain ran on the lane, even when the honest outcome is a pass or
    the UNTESTED abstention."""

    root, repo = _setup(tmp_path)
    result = create_study_map(
        root, "set_la", client=FakeSynthesisClient(), brief={"depth": "intro"},
        repository=repo, clock=_CLOCK,
    )
    rows = repo.proposal_items(result.proposal_id)
    practice_rows = [r for r in rows if r["item_type"] == "practice_item"]
    assert practice_rows
    for row in practice_rows:
        audit = row.get("audit") or {}
        assert "persona_gate" in audit, "instrument chain must judge every ingest-authored item"


# ---------------------------------------------------------------------------
# 2. `any_of` / vacuous recipes at the synthesis gate
# ---------------------------------------------------------------------------


def _payload_with_recipes(context, recipes):
    payload = _default_payload(context)
    blueprint = payload.blueprints[0]
    payload.blueprints[0] = blueprint.model_copy(update={"recipes": recipes})
    return payload


def test_vacuous_recipe_hard_fails_at_the_gate(tmp_path):
    """Zero components in all three slots can never be demonstrated or
    certified (`recipe_gaps` refuses it), so ingest must refuse to mint it."""

    root, repo = _setup(tmp_path)
    client = FakeSynthesisClient(
        builder=lambda context, call: _payload_with_recipes(
            context, [SynthRecipe(id="recipe_vacuous")]
        )
    )
    with pytest.raises(StudyMapError) as excinfo:
        create_study_map(
            root, "set_la", client=client, brief={"depth": "intro"},
            repository=repo, clock=_CLOCK,
        )
    assert excinfo.value.code == "synthesis_gate_failed"
    diags = excinfo.value.diagnostics or []
    assert any(
        d.get("gate") == "recipe_validity" and "no components" in d.get("message", "")
        for d in diags
    )


def test_single_alternative_any_of_gets_review_diagnostic(tmp_path):
    """One-element `any_of` with no `all_of` is a required component in the
    wrong slot: coherent semantics, misleading shape — review, not hard-fail."""

    root, repo = _setup(tmp_path)
    recipe = SynthRecipe(
        id="recipe_single_alt",
        any_of=[SynthRecipeComponent(facet_client_id="f_def", capability="schema_interpretation")],
    )
    client = FakeSynthesisClient(
        builder=lambda context, call: _payload_with_recipes(context, [recipe])
    )
    result = create_study_map(
        root, "set_la", client=client, brief={"depth": "intro"},
        repository=repo, clock=_CLOCK,
    )
    assert not any(d["severity"] == "hard_fail" for d in result.gate_diagnostics)
    assert any(
        d.get("gate") == "recipe_validity"
        and d.get("severity") == "review"
        and "single-alternative" in d.get("message", "")
        for d in result.gate_diagnostics
    )


# ---------------------------------------------------------------------------
# 3. Capability observability (D3 pattern extended)
# ---------------------------------------------------------------------------


def test_omitted_component_capability_defaults_with_diagnostic(tmp_path):
    root, repo = _setup(tmp_path)
    recipe = SynthRecipe(
        id="recipe_defaulted",
        all_of=[
            SynthRecipeComponent(facet_client_id="f_def"),  # capability omitted
            SynthRecipeComponent(facet_client_id="f_spectral", capability="method_selection"),
        ],
    )
    client = FakeSynthesisClient(
        builder=lambda context, call: _payload_with_recipes(context, [recipe])
    )
    result = create_study_map(
        root, "set_la", client=client, brief={"depth": "intro"},
        repository=repo, clock=_CLOCK, apply=True,
    )
    flagged = [
        d for d in result.gate_diagnostics if d.get("gate") == "recipe_component_capability"
    ]
    assert len(flagged) == 1, "exactly the omitted component is flagged, never the explicit one"
    assert flagged[0]["severity"] == "review"
    lo = load_vault(root).learning_objects["lo_diagonalize_symmetric"]
    capabilities = {
        component.facet: component.capability
        for component in lo.blueprints[0].recipes[0].all_of
    }
    assert capabilities["facet_symmetry_definition"] == "retrieval"
    assert capabilities["facet_spectral_applicability"] == "method_selection"


def test_explicit_capabilities_produce_no_capability_diagnostics(tmp_path):
    root, repo = _setup(tmp_path)
    result = create_study_map(
        root, "set_la", client=FakeSynthesisClient(), brief={"depth": "intro"},
        repository=repo, clock=_CLOCK,
    )
    assert not any(
        d.get("gate") in {"recipe_component_capability", "criterion_target_capability"}
        for d in result.gate_diagnostics
    )


def test_omitted_criterion_target_capability_defaults_with_diagnostic(tmp_path):
    root, repo = _setup(tmp_path)

    def builder(context, call):
        payload = _default_payload(context)
        item = payload.practice_items[0]
        criterion = item.criteria[0]
        bare_target = SynthCriterionTarget(
            facet_client_id=criterion.targets[0].facet_client_id  # capability omitted
        )
        payload.practice_items[0] = item.model_copy(
            update={
                "criteria": [
                    criterion.model_copy(update={"targets": [bare_target]}),
                    *item.criteria[1:],
                ]
            }
        )
        return payload

    result = create_study_map(
        root, "set_la", client=FakeSynthesisClient(builder=builder),
        brief={"depth": "intro"}, repository=repo, clock=_CLOCK,
    )
    flagged = [
        d for d in result.gate_diagnostics if d.get("gate") == "criterion_target_capability"
    ]
    assert len(flagged) == 1
    assert flagged[0]["severity"] == "review"


# ---------------------------------------------------------------------------
# 4. Append lane honours items_off
# ---------------------------------------------------------------------------


def _append_with_item(context, call):
    ext, unit, span = _first_new_span(context)
    return AppendReconciliation(
        summary="append with a model-emitted practice item",
        practice_items=[
            SynthPracticeItem(
                client_item_id="pi_appended",
                learning_object_id="lo_diagonalize_symmetric",
                prompt="State the definition of a symmetric matrix.",
                expected_answer="A^T = A.",
                provenance=[
                    SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span, relation="exercise")
                ],
            )
        ],
    )


def test_append_respects_items_off(tmp_path):
    root, repo = _bootstrap_and_add(tmp_path)
    result = append_source(
        root, "set_la", client=FakeAppendClient(builder=_append_with_item),
        new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK,
        brief={"practice_items": "as_you_read"},
    )
    assert result.item_counts.get("practice_item", 0) == 0
    assert any(d.get("gate") == "items_off" for d in result.gate_diagnostics)


def test_append_authors_items_when_upfront(tmp_path):
    """Counter-arm: the drop above is items_off-driven, not incidental."""

    root, repo = _bootstrap_and_add(tmp_path)
    result = append_source(
        root, "set_la", client=FakeAppendClient(builder=_append_with_item),
        new_revision_ids=["rev_alt"], repository=repo, clock=_CLOCK,
        brief={"practice_items": "upfront"},
    )
    assert result.item_counts.get("practice_item", 0) == 1
    assert not any(d.get("gate") == "items_off" for d in result.gate_diagnostics)


# ---------------------------------------------------------------------------
# 5. Canonical lane: gated rows never auto-apply
# ---------------------------------------------------------------------------


class _SelectedResponseCanonicalClient(_FakeCanonicalClient):
    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        self.calls.append(context)
        locator = self.locator or context.chunks[0].locator
        payload = _proposal_payload(context, locator)
        for item in payload["items"]:
            if item["item_type"] == "practice_item":
                item["payload"]["prompt"] = (
                    "Which of the following is the factorization SVD produces? "
                    "A. LU B. QR C. U S V^T"
                )
        return AuthoringProposal.model_validate(payload)


def test_canonical_lane_does_not_auto_apply_gated_items(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    result = ingest_canonical_source(
        vault_root,
        str(_source_file(tmp_path)),
        _SelectedResponseCanonicalClient(),
        subject_id="linear-algebra",
        clock=FrozenClock(NOW),
    )
    assert result.invalid_count == 1
    # The LO still auto-applies; the gated practice item must not.
    assert result.auto_applied_count == 1
    assert "pi_ingested_svd_001" not in load_vault(vault_root).practice_items


# ---------------------------------------------------------------------------
# 6. Recalibration boundary stamped at content-apply time
# ---------------------------------------------------------------------------


def test_apply_stamps_coverage_boundary_and_later_rebuilds_add_nothing(tmp_path):
    root, repo = _setup(tmp_path)
    create_study_map(
        root, "set_la", client=FakeSynthesisClient(), brief={"depth": "intro"},
        repository=repo, clock=_CLOCK, apply=True,
    )
    with repo.connection() as connection:
        stamped = connection.execute(
            "SELECT coverage_denominator_version FROM derived_state_rebuilds"
        ).fetchall()
    assert stamped, "applying LO/blueprint content must record the boundary marker"
    assert any(
        row["coverage_denominator_version"]
        and str(row["coverage_denominator_version"]).startswith("coverage_contract_frontier_v1:")
        for row in stamped
    )
    changes_after_apply = repo.derived_state_rebuild_version_changes()

    # A later full rebuild re-stamps the same content-addressed version: no
    # deferred boundary fires, so the ingest cannot be narrated at rebuild time.
    vault = load_vault(root)
    rebuild_derived_state(vault, repo, clock=FrozenClock(NOW))
    changes_after_rebuild = repo.derived_state_rebuild_version_changes()
    assert len(changes_after_rebuild) == len(changes_after_apply)

    # Idempotence of the apply-time stamp itself.
    record_content_recalibration(
        vault, repo,
        affected_learning_object_ids=["lo_diagonalize_symmetric"],
        clock=FrozenClock(NOW),
    )
    assert len(repo.derived_state_rebuild_version_changes()) == len(changes_after_apply)


def test_record_content_recalibration_ignores_unknown_los(tmp_path):
    root, repo = _setup(tmp_path)
    vault = load_vault(root)
    marker = record_content_recalibration(
        vault, repo, affected_learning_object_ids=["lo_not_in_vault"], clock=FrozenClock(NOW)
    )
    assert marker is None
    with repo.connection() as connection:
        count = connection.execute("SELECT COUNT(*) AS n FROM derived_state_rebuilds").fetchone()
    assert count["n"] == 0


# ---------------------------------------------------------------------------
# 7. Reachability summary at ingest completion
# ---------------------------------------------------------------------------


def test_reachability_summary_reports_minted_cells(tmp_path):
    root, repo = _setup(tmp_path)
    create_study_map(
        root, "set_la", client=FakeSynthesisClient(), brief={"depth": "intro"},
        repository=repo, clock=_CLOCK, apply=True,
    )
    summary = _reachability_summary(load_vault(root), repo, ["lo_diagonalize_symmetric"])
    assert summary["learning_objects"] == ["lo_diagonalize_symmetric"]
    assert summary["contract_cells"] == 2
    assert sum(summary["verdicts"].values()) == 2
