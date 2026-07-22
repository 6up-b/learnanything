"""P2 step 1 -- reviewed TaskBlueprint versions (spec_p2 §3.2, §12.1)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services import task_blueprints as TB

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


def _spec(**over):
    spec = {
        "source_rev": "rev-1",
        "unit_id": "unit-a",
        "family_key": "method-selection",
        "exemplars": [
            {"exemplar_ref": "ex1", "unit_id": "unit-a", "family_key": "method-selection", "weight": 1.0},
            {"exemplar_ref": "ex_held", "unit_id": "unit-a", "family_key": "method-selection",
             "held_out": True, "held_out_weight": 1.0, "weight": 0.0},
        ],
        "solution_recipes": [{"all_of": [{"facet": "f1", "capability": "method_selection"}]}],
    }
    spec.update(over)
    return spec


def test_register_review_activate_triad(repo):
    v = TB.register_blueprint_version(repo, blueprint_slug="bp1", spec=_spec(), clock=CLOCK)
    assert v.status == "draft" and v.version == 1 and v.minted is True
    reviewed = TB.review_blueprint_version(repo, blueprint_version_id=v.id, clock=CLOCK)
    assert reviewed.status == "reviewed"
    active = TB.activate_blueprint_version(repo, blueprint_version_id=v.id, clock=CLOCK)
    assert active.status == "active"
    # Review ledger is append-only and records each step.
    kinds = [e["kind"] for e in repo.task_blueprint_review_events_for(v.id)]
    assert kinds == ["registered", "reviewed", "activated"]


def test_register_is_content_addressed_idempotent(repo):
    first = TB.register_blueprint_version(repo, blueprint_slug="bp1", spec=_spec(), clock=CLOCK)
    again = TB.register_blueprint_version(repo, blueprint_slug="bp1", spec=_spec(), clock=CLOCK)
    assert again.id == first.id and again.minted is False
    assert len(repo.task_blueprint_versions_for(first.blueprint_id)) == 1


def test_mixed_unit_blueprint_cannot_validate(repo):
    spec = _spec(exemplars=[
        {"exemplar_ref": "ex1", "unit_id": "unit-a", "family_key": "method-selection"},
        {"exemplar_ref": "ex2", "unit_id": "unit-b", "family_key": "method-selection"},
    ])
    with pytest.raises(TB.InvalidBlueprint):
        TB.register_blueprint_version(repo, blueprint_slug="bp2", spec=spec, clock=CLOCK)


def test_multi_family_blueprint_cannot_validate(repo):
    spec = _spec(exemplars=[
        {"exemplar_ref": "ex1", "unit_id": "unit-a", "family_key": "method-selection"},
        {"exemplar_ref": "ex2", "unit_id": "unit-a", "family_key": "integration"},
    ])
    with pytest.raises(TB.InvalidBlueprint):
        TB.register_blueprint_version(repo, blueprint_slug="bp3", spec=spec, clock=CLOCK)


def test_capability_outside_vocab_rejected(repo):
    spec = _spec(solution_recipes=[{"all_of": [{"facet": "f1", "capability": "telepathy"}]}])
    with pytest.raises(TB.InvalidBlueprint):
        TB.register_blueprint_version(repo, blueprint_slug="bp4", spec=spec, clock=CLOCK)


def test_exemplar_anchor_has_zero_held_out_weight(repo):
    v = TB.register_blueprint_version(repo, blueprint_slug="bp1", spec=_spec(), clock=CLOCK)
    rows = {r["exemplar_ref"]: r for r in repo.target_exemplars_for(v.id)}
    # The selected exemplar is a familiar anchor with zero held-out weight (§12.1).
    assert rows["ex1"]["exposure_status"] == "familiar_anchor"
    assert rows["ex1"]["held_out_weight"] == 0.0
    # The unseen sibling carries held-out weight.
    assert rows["ex_held"]["exposure_status"] == "unseen_sibling"
    assert rows["ex_held"]["held_out_weight"] == 1.0


def test_reading_question_placement_is_a_review_artifact(repo):
    v = TB.register_blueprint_version(repo, blueprint_slug="bp1", spec=_spec(), clock=CLOCK)
    TB.place_reading_question(
        repo, blueprint_version_id=v.id,
        placement={"section": "intro", "phase": "pretest_prime"}, clock=CLOCK,
    )
    kinds = [e["kind"] for e in repo.task_blueprint_review_events_for(v.id)]
    assert "reading_question_placed" in kinds
