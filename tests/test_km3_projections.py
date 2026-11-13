"""KM3 projections + goal certification (knowledge-model §9.2/§9.5/§16).

Builds an mvp-0.7 vault whose composite LO carries an authored AND-recipe
blueprint (two capability-matched components plus an integration factor) and
drives real attempts through the write path, so the blueprint readiness
projection and the Ready/Demonstrated dual-axis run end to end.
"""

from __future__ import annotations

from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.learner.blueprint_projection import project_lo_readiness
from learnloop.goals.goal_certification import facet_demonstration, lo_certification
from learnloop.goals.goal_projection import goal_report
from learnloop.vault.loader import load_vault

from tests.helpers import (
    NOW,
)
from tests.km3_projections_helpers import COMP_A, COMP_B, INTEG, LO_ID, _attempt, build_blueprint_vault
from tests.km3_projections_helpers import blueprint_vault, blueprint_vault_old_tag  # noqa: F401 - fixtures, used by parameter name

# -- Blueprint readiness (§9.2) ------------------------------------------------


def test_blueprint_readiness_wired_into_goal_report(blueprint_vault_old_tag):
    vault, repository = blueprint_vault_old_tag
    _attempt(vault, repository, "pi_comp_a", 4)
    _attempt(vault, repository, "pi_comp_b", 4)

    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    assert LO_ID in report.blueprint_readiness_by_lo
    readiness = report.blueprint_readiness_by_lo[LO_ID]
    assert readiness.has_blueprints is True
    # Components are strong, but the untested integration facet (predicted at the
    # 0.5 prior) is the bottleneck that keeps readiness below the component level.
    assert readiness.bottleneck is not None
    assert readiness.bottleneck.facet == INTEG
    assert readiness.readiness is not None and readiness.readiness < 0.55


def test_readiness_rises_when_components_improve():
    # Pure check: strengthening a component recall raises blueprint readiness.
    lo = _load_lo()
    weak = project_lo_readiness(lo, lambda f, c: 0.3, slip=0.05).readiness
    strong = project_lo_readiness(lo, lambda f, c: 0.9, slip=0.05).readiness
    assert strong > weak


def _load_lo():
    import tempfile

    paths = build_blueprint_vault(Path(tempfile.mkdtemp()) / "vault")
    vault = load_vault(paths.root)
    return vault.learning_objects[LO_ID]


# -- Goal certification / Demonstrated axis (§9.5, §16) ------------------------


def test_retrieval_style_component_demonstrates_only_its_capability(blueprint_vault_old_tag):
    vault, repository = blueprint_vault_old_tag
    _attempt(vault, repository, "pi_comp_a", 4)

    lo = vault.learning_objects[LO_ID]
    comp_a = facet_demonstration(vault, repository, lo, COMP_A)
    assert comp_a.required_capabilities == ("procedure_execution",)
    assert comp_a.demonstrated is True
    # Component B was never attempted -> not demonstrated at its capability.
    comp_b = facet_demonstration(vault, repository, lo, COMP_B)
    assert comp_b.demonstrated is False


def test_planted_integration_gap_not_shown_demonstrated(blueprint_vault_old_tag):
    """§16 projection row: strong components + missing integration -> not demonstrated."""

    vault, repository = blueprint_vault_old_tag
    # Demonstrate BOTH components unassisted, repeatedly, but never the integrated
    # whole-task item.
    for _ in range(3):
        _attempt(vault, repository, "pi_comp_a", 4)
        _attempt(vault, repository, "pi_comp_b", 4)

    lo = vault.learning_objects[LO_ID]
    assert facet_demonstration(vault, repository, lo, COMP_A).demonstrated is True
    assert facet_demonstration(vault, repository, lo, COMP_B).demonstrated is True

    cert = lo_certification(vault, repository, lo)
    assert cert.demonstrated is False
    assert INTEG in cert.integration_gaps

    # Once the integrated task is also demonstrated directly, the LO certifies.
    _attempt(vault, repository, "pi_integrated", 4)
    cert_after = lo_certification(vault, repository, lo)
    assert cert_after.demonstrated is True
    assert cert_after.integration_gaps == ()


def test_goal_report_exposes_dual_axis_fields(blueprint_vault_old_tag):
    vault, repository = blueprint_vault_old_tag
    _attempt(vault, repository, "pi_comp_a", 4)

    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    comp_a = next(f for f in report.facets if f.facet_id == COMP_A)
    # Ready (prediction) and Demonstrated (capability-matched credit) are both
    # exposed and are distinct axes.
    assert comp_a.required_capabilities == ("procedure_execution",)
    assert comp_a.demonstrated is True
    assert comp_a.ready == comp_a.predicted_at_horizon
    integ = next(f for f in report.facets if f.facet_id == INTEG)
    assert integ.demonstrated is False


def test_hinted_component_not_demonstrated(blueprint_vault):
    vault, repository = blueprint_vault
    _attempt(vault, repository, "pi_comp_a", 4, hints_used=1)
    lo = vault.learning_objects[LO_ID]
    # Assisted evidence earns no certification credit -> not demonstrated (§5.4).
    assert facet_demonstration(vault, repository, lo, COMP_A).demonstrated is False
