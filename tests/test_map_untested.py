"""Slice A F1: the map exposes evidence, never a default prior as Ready."""

from types import SimpleNamespace

import pytest

from learnloop_sidecar.handlers.knowledge_map import _facet_current_retentions, _facet_field
from tests.test_graph_editor_reads import _blueprint_ctx, _call
from tests.test_km3_projections import COMP_A, INTEG


def test_map_untested_rpc_and_demonstrated_readiness(tmp_path):
    ctx = _blueprint_ctx(tmp_path / "vault")
    result = _call(ctx, "get_knowledge_map", {})
    points = {point["id"]: point for point in result["facetField"]["points"]}
    unknown = points[INTEG]
    assert unknown["untested"] is True
    assert not {"ready", "readyGhost", "readyVariance"} & unknown.keys()
    assert unknown["demonstratedMass"] == 0
    assert unknown["demonstratedCapabilities"] == []
    assert all(arc["status"] != "demonstrated" for arc in unknown["capabilityArcs"])
    known = points[COMP_A]
    assert known["untested"] is False
    assert known["demonstratedMass"] > 0
    assert known["evidenceMass"] > 0
    assert 0 <= known["ready"] <= known["readyGhost"] <= 1
    assert known["readyVariance"] > 0
    rows = [
        row for row in ctx.repository.canonical_facet_recall_states()
        if row.facet_id == COMP_A and row.practice_item_id is None
    ]
    alpha = 1.0 + sum(row.recall_alpha - 1.0 for row in rows)
    beta = 1.0 + sum(row.recall_beta - 1.0 for row in rows)
    retention = _facet_current_retentions(ctx.vault, ctx.repository).get(COMP_A, 1.0)
    assert known["readyGhost"] == alpha / (alpha + beta)
    assert known["ready"] == pytest.approx(known["readyGhost"] * retention)
    assert known["readyVariance"] == alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1))


@pytest.mark.parametrize("alpha,beta,raw_mass", [(1.0, 1.0, 0.0), (3.0, 1.0, 2.0)])
def test_zero_independent_mass_is_not_tested_even_with_prior_or_warm_rows(
    tmp_path, monkeypatch, alpha, beta, raw_mass
):
    ctx = _blueprint_ctx(tmp_path / "vault")
    baseline = _facet_field(ctx.vault, ctx.repository)
    original = ctx.repository.canonical_facet_recall_states
    monkeypatch.setattr(
        ctx.repository,
        "canonical_facet_recall_states",
        lambda: [
            *original(),
            SimpleNamespace(
                facet_id=INTEG,
                practice_item_id=None,
                recall_alpha=alpha,
                recall_beta=beta,
                independent_evidence_mass=0.0,
                raw_coverage_mass=raw_mass,
            ),
        ],
    )
    # Neither a row's existence nor an unsupported estimate changes the map.
    assert _facet_field(ctx.vault, ctx.repository) == baseline
