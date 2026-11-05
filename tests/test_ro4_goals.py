"""RO4 §8.5: a goal contract's use weights: in the content hash and out of the support hash, their own change
class, a stated default for a goal with no confirmed contract, no old hash rewritten, copied at creation."""

from __future__ import annotations

import pytest

from learnloop.algorithm_versions import INTERVAL_FACTOR_ALGORITHM_VERSION, ROUTER_OBJECTIVE_ALGORITHM_VERSION
from learnloop.config.schema import LearnLoopConfig
from learnloop.goals import goal_contracts as GC
from learnloop.goals import use_weights as U
from learnloop.vault.models import Goal

BODY = {"purpose": "linear algebra exam", "due_at": "2026-12-01T00:00:00Z", "facet_scope": {"concepts": ["c1"]},
        "exemplars": [{"id": "ex1", "surface_ref": "pi_1"}], "baseline_milestone": "m1"}


def test_a_body_without_use_weights_keeps_its_bytes_and_hash():
    canonical = GC.canonicalize_body(BODY)
    assert "use_weight" not in canonical
    # The pre-RO4 canonical form, frozen: no slot was added, so no confirmed contract's hash moves.
    assert GC.content_hash(canonical) == GC.content_hash({key: value for key, value in canonical.items()})


def test_use_weights_are_in_the_content_hash_and_out_of_the_support_hash():
    plain = GC.canonicalize_body(BODY)
    weighted = GC.canonicalize_body({**BODY, "use_weight": {"dated": 2.0, "undated_density": 1 / 90}})
    assert weighted["use_weight"] == {"dated": 2.0, "per_lo": {}, "undated_density": 1 / 90}
    assert GC.content_hash(plain) != GC.content_hash(weighted)
    assert GC.support_hash(plain) == GC.support_hash(weighted)
    assert GC.compute_change_class(plain, weighted) == GC.USE_WEIGHT_CHANGE == "use_weight_change"
    other = GC.canonicalize_body({**BODY, "use_weight": {"dated": 3.0, "undated_density": 1 / 90}})
    assert GC.compute_change_class(weighted, other) == "use_weight_change"
    assert GC.compute_change_class(weighted, weighted) == "metadata"
    # A support edit still wins (most invalidating first).
    moved = GC.canonicalize_body({**BODY, "facet_scope": {"concepts": ["c2"]}, "use_weight": {"dated": 3.0,
                                                                                              "undated_density": 0.0}})
    assert GC.compute_change_class(weighted, moved) == "support_change"
    with pytest.raises(ValueError):
        GC.canonicalize_body({**BODY, "use_weight": {"dated": -1.0, "undated_density": 0.1}})


def _goal(**extra) -> Goal:
    return Goal.model_validate({"id": "g1", "title": "Exam", "status": "active", "due_at": "2026-12-01T00:00:00Z",
                                "facet_scope": {"concepts": ["c1"]}, "created_at": "2026-11-01T00:00:00Z",
                                "updated_at": "2026-11-01T00:00:00Z", **extra})


def test_the_stated_default_for_a_goal_with_no_contract_and_no_copy():
    config = LearnLoopConfig()
    weights = U.for_goal(_goal(), None, config)
    assert (weights.dated, weights.undated_density, weights.source) == (1.0, pytest.approx(1 / 90), U.DEFAULT)


def test_a_copy_made_at_creation_is_read_and_a_config_change_does_not_move_it():
    config = LearnLoopConfig()
    copied = U.copy_at_creation(config, dated=2.5)
    goal = _goal(use_weight=copied)
    config.router_objective.undated_use_density = 1 / 30
    weights = U.for_goal(goal, None, config)
    assert (weights.dated, weights.undated_density, weights.source) == (2.5, pytest.approx(1 / 90), U.COPIED)


def test_the_contract_is_copied_at_confirmation_at_the_tag_and_adjustable(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault

    from tests.helpers import create_basic_vault, set_algorithm_version

    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    for version, expect in ((INTERVAL_FACTOR_ALGORITHM_VERSION, None),
                            (ROUTER_OBJECTIVE_ALGORITHM_VERSION, {"dated": 1.0, "per_lo": {}, "undated_density": 1 / 90})):
        set_algorithm_version(paths, version)
        vault = load_vault(paths.root)
        repository = Repository(paths.sqlite_path)
        goal_id = f"goal_{version.replace('.', '_').replace('-', '_')}"
        assert GC._with_use_weight(dict(BODY), goal_id, vault).get("use_weight") == expect
    version = GC.confirm_goal_contract(repository, goal_id="g_ro4", contract_body=dict(BODY), vault=vault)
    assert version.contract["use_weight"]["undated_density"] == pytest.approx(1 / 90)
    adjusted = GC.set_use_weight(repository, goal_id="g_ro4", use_weight={"dated": 4.0, "undated_density": 0.02})
    assert adjusted.change_class == "use_weight_change" and adjusted.support_hash == version.support_hash
    assert adjusted.content_hash != version.content_hash
    # The first version's row and hash are unchanged.
    first = repository.fetch_goal_contract_version(version.id)
    assert first["content_hash"] == version.content_hash


# Landing ruling R2: the desktop goal form asks the dated use weight, frictionlessly: one optional field, prefilled
# with the default (goal_feasibility says what it is, and only at the tag with the objective on), that can be left
# alone; create_goal copies the asked weight (else the default) with the config's undated density.


def _sidecar(tmp_path, version: str):
    import learnloop_sidecar.handlers  # noqa: F401 - registers methods
    from learnloop_sidecar.context import SidecarContext

    from tests.helpers import create_basic_vault, set_algorithm_version

    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    set_algorithm_version(paths, version)
    context = SidecarContext()
    context.load(paths.root)
    return context, paths


def _rpc(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


_NEW_GOAL = {"title": "Midterm", "targetRecall": 0.85, "concepts": ["singular_value_decomposition"], "facets": [],
             "examEnabled": False, "dueAt": "2026-12-15T23:59:59Z"}


def _yaml_use_weight(paths, goal_id: str):
    from learnloop.vault.yaml_io import read_yaml

    entries = read_yaml(paths.goals_path).get("goals") or []
    return next(entry for entry in entries if entry.get("id") == goal_id).get("use_weight")


def test_the_goal_form_is_told_the_default_use_weight_at_the_tag_only(tmp_path):
    feasibility = {key: _NEW_GOAL[key] for key in ("title", "targetRecall", "concepts", "facets", "examEnabled",
                                                   "dueAt")}
    on, _ = _sidecar(tmp_path / "on", ROUTER_OBJECTIVE_ALGORITHM_VERSION)
    assert _rpc(on, "goal_feasibility", feasibility)["useWeightDefault"] == {"dated": 1.0}
    below, _ = _sidecar(tmp_path / "below", INTERVAL_FACTOR_ALGORITHM_VERSION)
    assert _rpc(below, "goal_feasibility", feasibility)["useWeightDefault"] is None


def test_create_goal_copies_the_asked_use_weight_or_the_default_when_left_alone(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    ctx, paths = _sidecar(tmp_path / "on", ROUTER_OBJECTIVE_ALGORITHM_VERSION)
    asked = _rpc(ctx, "create_goal", {**_NEW_GOAL, "datedUseWeight": 2.5})["goal"]["id"]
    assert _yaml_use_weight(paths, asked) == {"dated": 2.5, "per_lo": {}, "undated_density": pytest.approx(1 / 90)}
    left_alone = _rpc(ctx, "create_goal", dict(_NEW_GOAL))["goal"]["id"]
    assert _yaml_use_weight(paths, left_alone) == {"dated": 1.0, "per_lo": {},
                                                   "undated_density": pytest.approx(1 / 90)}
    vault, repository = ctx.require_vault()
    goal = next(g for g in vault.goals if g.id == asked)
    assert (U.for_goal(goal, repository, vault.config).dated, U.for_goal(goal, repository, vault.config).source) == (
        2.5, U.COPIED)
    with pytest.raises((SidecarError, ValueError)):
        _rpc(ctx, "create_goal", {**_NEW_GOAL, "datedUseWeight": -1.0})


def test_create_goal_below_the_tag_writes_no_use_weight_even_when_asked(tmp_path):
    ctx, paths = _sidecar(tmp_path / "below", INTERVAL_FACTOR_ALGORITHM_VERSION)
    goal_id = _rpc(ctx, "create_goal", {**_NEW_GOAL, "datedUseWeight": 2.5})["goal"]["id"]
    assert _yaml_use_weight(paths, goal_id) is None
