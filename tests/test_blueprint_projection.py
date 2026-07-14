"""Blueprint likelihood projections (knowledge-model §9.2, §16 recipes/projection).

Covers the normative launch defaults (noisy-AND, guess floor, max-over-recipes,
integration conjunct, compensatory geometric mean) and the §16 acceptance rows
deferred from KM2: a conjunctive bottleneck is not averaged away, alternative
method success does not credit a bypassed requirement, and a path-specific
failure affects only the exercised path.
"""

from __future__ import annotations

import pytest

from learnloop.config import LearnLoopConfig
from learnloop.services.blueprint_projection import (
    project_blueprint,
    project_lo_readiness,
    project_recipe,
)
from learnloop.vault.models import (
    Blueprint,
    BlueprintRecipe,
    LearningObject,
    RecipeComponent,
)

CONFIG = LearnLoopConfig()
SLIP = CONFIG.evidence.blueprints.slip  # 0.05


def _component(facet, capability="retrieval", modality="hard"):
    return RecipeComponent(facet=facet, capability=capability, modality=modality)


def _recall(mapping, default=0.5):
    return lambda facet, capability: mapping.get((facet, capability), mapping.get(facet, default))


def test_conjunctive_recipe_is_noisy_and_with_slip():
    recipe = BlueprintRecipe(
        id="r",
        all_of=[_component("a"), _component("b")],
    )
    recall = _recall({"a": 0.9, "b": 0.8})
    projection = project_recipe(recipe, recall, slip=SLIP, guess=0.0)
    # (1 - slip) * 0.9 * 0.8
    assert projection.success_probability == pytest.approx((1 - SLIP) * 0.9 * 0.8)


def test_selected_response_adds_guess_floor():
    recipe = BlueprintRecipe(id="r", all_of=[_component("a"), _component("b")])
    recall = _recall({"a": 0.0, "b": 0.0})
    guess = 0.25
    projection = project_recipe(recipe, recall, slip=SLIP, guess=guess)
    # With zero component recall, success falls to the guess floor exactly.
    assert projection.success_probability == pytest.approx(guess)


def test_conjunctive_bottleneck_not_averaged_away():
    """§16: a weak conjunct keeps readiness low no matter how strong the rest."""

    recipe = BlueprintRecipe(
        id="r",
        all_of=[_component("strong1"), _component("strong2"), _component("weak")],
    )
    recall = _recall({"strong1": 0.99, "strong2": 0.99, "weak": 0.10})
    projection = project_recipe(recipe, recall, slip=SLIP, guess=0.0)
    # A simple average would be ~0.69; the noisy-AND is dragged down by the weak
    # conjunct to ~0.09.
    assert projection.success_probability < 0.12
    assert projection.bottleneck is not None
    assert projection.bottleneck.facet == "weak"


def test_alternative_recipe_success_does_not_credit_bypassed_requirement():
    """§16: an easy alternative recipe lifts the blueprint, but the hard recipe's
    bottleneck is untouched — success via one method never credits the other's
    bypassed requirement."""

    hard_recipe = BlueprintRecipe(id="hard", all_of=[_component("difficult")])
    easy_recipe = BlueprintRecipe(id="easy", all_of=[_component("shortcut")])
    blueprint = Blueprint(id="bp", weight=1.0, recipes=[hard_recipe, easy_recipe])
    recall = _recall({"difficult": 0.10, "shortcut": 0.95})
    projection = project_blueprint(blueprint, recall, slip=SLIP, guess=0.0)
    # Blueprint success is the max over recipes -> the easy path.
    assert projection.best_recipe_id == "easy"
    assert projection.success_probability == pytest.approx((1 - SLIP) * 0.95)
    # The hard recipe's own projection still reflects its bottleneck (not lifted).
    hard = next(r for r in projection.recipes if r.recipe_id == "hard")
    assert hard.success_probability < 0.12


def test_path_specific_failure_affects_only_the_exercised_path():
    """§16: a path_specific requirement gates only its own recipe."""

    recipe_a = BlueprintRecipe(
        id="path_a",
        all_of=[_component("shared"), _component("only_a", modality="path_specific")],
    )
    recipe_b = BlueprintRecipe(id="path_b", all_of=[_component("shared")])
    blueprint = Blueprint(id="bp", weight=1.0, recipes=[recipe_a, recipe_b])
    recall = _recall({"shared": 0.9, "only_a": 0.05})
    projection = project_blueprint(blueprint, recall, slip=SLIP, guess=0.0)
    path_a = next(r for r in projection.recipes if r.recipe_id == "path_a")
    path_b = next(r for r in projection.recipes if r.recipe_id == "path_b")
    # path_a is crippled by only_a; path_b, which never exercises it, is fine.
    assert path_a.success_probability < 0.12
    assert path_b.success_probability == pytest.approx((1 - SLIP) * 0.9)
    assert projection.best_recipe_id == "path_b"


def test_facilitating_component_does_not_drag_readiness():
    recipe = BlueprintRecipe(
        id="r",
        all_of=[_component("core"), _component("nice_to_have", modality="facilitating")],
    )
    recall = _recall({"core": 0.9, "nice_to_have": 0.05})
    projection = project_recipe(recipe, recall, slip=SLIP, guess=0.0)
    # facilitating is bypassable, so it does not enter the product.
    assert projection.success_probability == pytest.approx((1 - SLIP) * 0.9)


def test_integration_facet_enters_as_conjunct():
    with_integration = BlueprintRecipe(
        id="r",
        all_of=[_component("a"), _component("b")],
        integration=_component("coordinate", capability="coordination"),
    )
    recall = _recall({"a": 0.9, "b": 0.9, "coordinate": 0.3})
    projection = project_recipe(with_integration, recall, slip=SLIP, guess=0.0)
    assert projection.success_probability == pytest.approx((1 - SLIP) * 0.9 * 0.9 * 0.3)
    assert projection.bottleneck.facet == "coordinate"


def test_any_of_uses_strongest_alternative():
    recipe = BlueprintRecipe(
        id="r",
        all_of=[_component("core")],
        any_of=[_component("method_x"), _component("method_y")],
    )
    recall = _recall({"core": 0.9, "method_x": 0.2, "method_y": 0.8})
    projection = project_recipe(recipe, recall, slip=SLIP, guess=0.0)
    # The best alternative (method_y=0.8) contributes as one factor.
    assert projection.success_probability == pytest.approx((1 - SLIP) * 0.9 * 0.8)


def test_compensatory_composition_is_geometric_mean():
    recipe = BlueprintRecipe(
        id="r",
        composition="conjunctive",  # model literal; override treated below
        all_of=[_component("a"), _component("b")],
    )
    # Force the compensatory path by constructing a recipe-like object.
    object.__setattr__(recipe, "composition", "partially_compensatory")
    recall = _recall({"a": 0.4, "b": 0.9})
    projection = project_recipe(recipe, recall, slip=SLIP, guess=0.0)
    # Geometric mean sqrt(0.4*0.9) ~= 0.6, times (1-slip) — softer than noisy-AND
    # (0.36) because a strong conjunct partially compensates a weak one.
    assert projection.success_probability == pytest.approx((1 - SLIP) * (0.4 * 0.9) ** 0.5)
    assert projection.success_probability > (1 - SLIP) * 0.4 * 0.9


def test_lo_readiness_is_weight_normalized_sum():
    bp1 = Blueprint(id="bp1", weight=0.7, recipes=[BlueprintRecipe(id="r1", all_of=[_component("a")])])
    bp2 = Blueprint(id="bp2", weight=0.3, recipes=[BlueprintRecipe(id="r2", all_of=[_component("b")])])
    lo = LearningObject(
        id="lo",
        title="t",
        subjects=["s"],
        concept="c",
        knowledge_type="definition",
        summary="s",
        blueprints=[bp1, bp2],
        created_at="2020-01-01T00:00:00Z",
        updated_at="2020-01-01T00:00:00Z",
    )
    recall = _recall({"a": 0.8, "b": 0.4})
    readiness = project_lo_readiness(lo, recall, slip=SLIP)
    expected = (0.7 * (1 - SLIP) * 0.8 + 0.3 * (1 - SLIP) * 0.4) / 1.0
    assert readiness.has_blueprints is True
    assert readiness.readiness == pytest.approx(expected)
    # The overall bottleneck is the weakest gating conjunct across best paths.
    assert readiness.bottleneck.facet == "b"


def test_lo_without_blueprints_returns_none():
    lo = LearningObject(
        id="lo",
        title="t",
        subjects=["s"],
        concept="c",
        knowledge_type="definition",
        summary="s",
        blueprints=[],
        created_at="2020-01-01T00:00:00Z",
        updated_at="2020-01-01T00:00:00Z",
    )
    readiness = project_lo_readiness(lo, _recall({}), slip=SLIP)
    assert readiness.has_blueprints is False
    assert readiness.readiness is None
