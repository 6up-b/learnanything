"""Blueprint likelihood projections (knowledge-model §9.2).

Pure, derived, versioned read-side projection: given an LO's authored
performance blueprints (§7.2) and the learner's predicted per-facet recall, it
computes the probability of success on each recipe, blueprint, and the LO as a
whole. **It writes no evidence** — like every other projection it is a fold over
already-derived state, recomputed by ``rebuild_derived_state`` and versioned
with ``algorithm_version``.

Launch likelihood defaults (normative, §9.2):

* A conjunctive recipe is noisy-AND with a slip and an optional guess floor:
  ``P = guess + (1 - guess - slip) · Π_i p_i`` over its required
  facet-capability components ``p_i`` (capability-damped predicted recall).
  ``guess = 0`` (constructed response) collapses this to the plain noisy-AND
  ``(1 - slip) · Π p_i``; a selected-response format raises the floor
  (``guess`` from ``[evidence.blueprints].guess_by_format`` / ``1/n_options``).
* Alternative recipes combine as the **maximum** over applicable recipes — the
  learner is credited with whichever valid method they can execute.
* A reviewed partially-compensatory (explanatory) recipe uses a weighted
  geometric mean instead of the strict product.
* An authored integration facet enters as one more conjunct.
* ``readiness(lo) = Σ blueprint.weight × P(success)`` (weight-normalized).

Item difficulty, familiarity, scaffold, and testlet effects are deliberately
**not** terms here — they live in the observation-level modifiers and the
prediction-only calibration residual (§9.2). Upgrading the likelihood family
later is a projection recompute, never an evidence migration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from learnloop.numeric import clamp
from learnloop.vault.models import (
    Blueprint,
    BlueprintRecipe,
    LearningObject,
    LoadedVault,
    PracticeItem,
    RecipeComponent,
)

# Component recall lookup: (facet, capability) -> predicted recall in [0, 1].
ComponentRecall = Callable[[str, str], float]

# Requirement modalities that materially gate task likelihood (§8.2). A
# ``facilitating`` / ``instructional_order`` component improves performance but
# can be bypassed, so it never drags a recipe's predicted success down.
GATING_MODALITIES: frozenset[str] = frozenset({"hard", "path_specific"})

# Compositions that combine their conjuncts by weighted geometric mean rather
# than the strict noisy-AND product (reviewed partially-compensatory tasks).
# Authored as ``composition`` on a recipe; unknown/absent -> conjunctive.
COMPENSATORY_COMPOSITIONS: frozenset[str] = frozenset(
    {"partially_compensatory", "explanatory"}
)

_NEUTRAL_PRIOR = 0.5


@dataclass(frozen=True)
class ComponentReadiness:
    facet: str
    capability: str
    modality: str
    predicted_recall: float
    gating: bool  # whether it enters the recipe likelihood (hard/path_specific)

    def as_dict(self) -> dict[str, object]:
        return {
            "facet": self.facet,
            "capability": self.capability,
            "modality": self.modality,
            "predicted_recall": self.predicted_recall,
            "gating": self.gating,
        }


@dataclass(frozen=True)
class RecipeProjection:
    recipe_id: str
    composition: str
    success_probability: float
    components: list[ComponentReadiness]
    bottleneck: ComponentReadiness | None  # weakest gating conjunct

    def as_dict(self) -> dict[str, object]:
        return {
            "recipe_id": self.recipe_id,
            "composition": self.composition,
            "success_probability": self.success_probability,
            "components": [c.as_dict() for c in self.components],
            "bottleneck": self.bottleneck.as_dict() if self.bottleneck else None,
        }


@dataclass(frozen=True)
class BlueprintProjection:
    blueprint_id: str
    weight: float
    success_probability: float  # max over applicable recipes
    best_recipe_id: str | None
    recipes: list[RecipeProjection]

    def as_dict(self) -> dict[str, object]:
        return {
            "blueprint_id": self.blueprint_id,
            "weight": self.weight,
            "success_probability": self.success_probability,
            "best_recipe_id": self.best_recipe_id,
            "recipes": [r.as_dict() for r in self.recipes],
        }


@dataclass(frozen=True)
class LoReadiness:
    learning_object_id: str
    has_blueprints: bool
    readiness: float | None  # weight-normalized Σ weight×P(success); None when no blueprint
    blueprints: list[BlueprintProjection]
    bottleneck: ComponentReadiness | None  # weakest gating conjunct on the LO's best paths

    def as_dict(self) -> dict[str, object]:
        return {
            "learning_object_id": self.learning_object_id,
            "has_blueprints": self.has_blueprints,
            "readiness": self.readiness,
            "blueprints": [b.as_dict() for b in self.blueprints],
            "bottleneck": self.bottleneck.as_dict() if self.bottleneck else None,
        }


def _product(values: list[float]) -> float:
    result = 1.0
    for value in values:
        result *= max(0.0, min(1.0, value))
    return result


def _weighted_geometric_mean(pairs: list[tuple[float, float]]) -> float:
    """``Π p_i^(w_i / Σ w)`` over (recall, weight) pairs; 1.0 when empty."""

    total_weight = sum(max(weight, 0.0) for _p, weight in pairs)
    if total_weight <= 0.0:
        return 1.0
    log_sum = 0.0
    from math import log

    for recall, weight in pairs:
        w = max(weight, 0.0)
        if w <= 0.0:
            continue
        # log(0) guard: a zero-recall conjunct still collapses the mean toward 0.
        p = max(min(recall, 1.0), 1e-9)
        log_sum += (w / total_weight) * log(p)
    from math import exp

    return exp(log_sum)


def guess_floor_for_item(item: PracticeItem, config) -> float:
    """The selected-response guess floor for an item (§9.2).

    ``1/n_options`` for multiple choice when the option count is known, else the
    configured ``guess_by_format`` default; ``0`` for constructed response.
    """

    guess_by_format = dict(config.evidence.blueprints.guess_by_format)
    if item.practice_mode in ("multiple_choice", "recognition", "true_false"):
        n_options = _n_options(item)
        if n_options and n_options > 1:
            return 1.0 / float(n_options)
        return float(guess_by_format.get("multiple_choice", 0.25))
    return float(guess_by_format.get(item.practice_mode, guess_by_format.get("constructed_response", 0.0)))


def _n_options(item: PracticeItem) -> int | None:
    """Best-effort option count from a structured expected answer; None if unknown."""

    answer = item.expected_answer
    if isinstance(answer, dict):
        for key in ("options", "choices"):
            value = answer.get(key)
            if isinstance(value, (list, tuple)):
                return len(value)
    return None


def _gating_conjuncts(recipe: BlueprintRecipe) -> list[RecipeComponent]:
    """The components that materially gate this recipe's likelihood (§8.2).

    ``all_of`` hard/path_specific components plus the integration factor. The
    ``any_of`` alternatives are handled separately (max, not product).
    """

    conjuncts = [c for c in recipe.all_of if c.modality in GATING_MODALITIES]
    if recipe.integration is not None and recipe.integration.modality in GATING_MODALITIES:
        conjuncts.append(recipe.integration)
    return conjuncts


def project_recipe(
    recipe: BlueprintRecipe,
    component_recall: ComponentRecall,
    *,
    slip: float,
    guess: float,
) -> RecipeProjection:
    """Success probability for one recipe (§9.2 recipe core)."""

    def readiness(component: RecipeComponent, *, gating: bool) -> ComponentReadiness:
        return ComponentReadiness(
            facet=component.facet,
            capability=component.capability,
            modality=component.modality,
            predicted_recall=clamp(component_recall(component.facet, component.capability)),
            gating=gating,
        )

    conjuncts = _gating_conjuncts(recipe)
    conjunct_readiness = [readiness(c, gating=True) for c in conjuncts]

    # ``any_of`` alternatives: the learner uses their strongest available method,
    # so the best alternative contributes as a single factor (max, not product).
    any_of_readiness = [readiness(c, gating=False) for c in recipe.any_of]
    any_of_factor: float | None = None
    if any_of_readiness:
        any_of_factor = max(c.predicted_recall for c in any_of_readiness)

    composition = getattr(recipe, "composition", "conjunctive") or "conjunctive"
    if composition in COMPENSATORY_COMPOSITIONS:
        pairs = [(c.predicted_recall, 1.0) for c in conjunct_readiness]
        if any_of_factor is not None:
            pairs.append((any_of_factor, 1.0))
        base = _weighted_geometric_mean(pairs)
        # Reviewed explanatory tasks are constructed-response: no guess floor,
        # slip only.
        success = (1.0 - slip) * base
    else:
        factors = [c.predicted_recall for c in conjunct_readiness]
        if any_of_factor is not None:
            factors.append(any_of_factor)
        product = _product(factors)
        # guess + (1 - guess - slip) · Π p_i ; guess=0 -> plain noisy-AND.
        success = guess + max(0.0, 1.0 - guess - slip) * product

    bottleneck = (
        min(conjunct_readiness, key=lambda c: c.predicted_recall)
        if conjunct_readiness
        else None
    )
    return RecipeProjection(
        recipe_id=recipe.id,
        composition=composition,
        success_probability=clamp(success),
        components=conjunct_readiness + any_of_readiness,
        bottleneck=bottleneck,
    )


def project_blueprint(
    blueprint: Blueprint,
    component_recall: ComponentRecall,
    *,
    slip: float,
    guess: float,
) -> BlueprintProjection:
    """Success probability for one blueprint = max over its applicable recipes."""

    recipes = [
        project_recipe(recipe, component_recall, slip=slip, guess=guess)
        for recipe in blueprint.recipes
    ]
    best: RecipeProjection | None = None
    for recipe in recipes:
        if best is None or recipe.success_probability > best.success_probability:
            best = recipe
    return BlueprintProjection(
        blueprint_id=blueprint.id,
        weight=blueprint.weight,
        success_probability=best.success_probability if best is not None else 0.0,
        best_recipe_id=best.recipe_id if best is not None else None,
        recipes=recipes,
    )


def project_lo_readiness(
    learning_object: LearningObject,
    component_recall: ComponentRecall,
    *,
    slip: float,
    guess: float = 0.0,
) -> LoReadiness:
    """``readiness(lo) = Σ blueprint.weight × P(success)`` (§9.2), weight-normalized.

    ``guess`` defaults to 0 (the representative task for LO readiness is treated
    as constructed response); item-level projections pass the item's format
    guess floor. LOs with no authored blueprints return ``has_blueprints=False``
    and ``readiness=None`` — the caller keeps the legacy compatibility path.
    """

    if not learning_object.blueprints:
        return LoReadiness(
            learning_object_id=learning_object.id,
            has_blueprints=False,
            readiness=None,
            blueprints=[],
            bottleneck=None,
        )
    blueprints = [
        project_blueprint(blueprint, component_recall, slip=slip, guess=guess)
        for blueprint in learning_object.blueprints
    ]
    total_weight = sum(max(bp.weight, 0.0) for bp in blueprints)
    if total_weight <= 0.0:
        readiness = None
    else:
        readiness = clamp(
            sum(max(bp.weight, 0.0) * bp.success_probability for bp in blueprints)
            / total_weight
        )

    # Overall bottleneck: the weakest gating conjunct on each blueprint's best
    # recipe, across blueprints — the single component most limiting readiness.
    candidate_bottlenecks: list[ComponentReadiness] = []
    for bp in blueprints:
        best = next((r for r in bp.recipes if r.recipe_id == bp.best_recipe_id), None)
        if best is not None and best.bottleneck is not None:
            candidate_bottlenecks.append(best.bottleneck)
    bottleneck = (
        min(candidate_bottlenecks, key=lambda c: c.predicted_recall)
        if candidate_bottlenecks
        else None
    )
    return LoReadiness(
        learning_object_id=learning_object.id,
        has_blueprints=True,
        readiness=readiness,
        blueprints=blueprints,
        bottleneck=bottleneck,
    )


def item_exercised_recipes(
    vault: LoadedVault, item: PracticeItem, learning_object: LearningObject
) -> list[BlueprintRecipe]:
    """Recipes an item exercises, via its criteria ``recipe_ids`` (§5.1/§7.2).

    Falls back to every recipe of the LO's blueprints when no criterion names a
    recipe — the item is treated as exercising any valid method.
    """

    rubric = vault.rubric_for_item(item)
    named: set[str] = set()
    if rubric is not None:
        for criterion in rubric.criteria:
            named.update(criterion.recipe_ids)
    all_recipes = [
        recipe for blueprint in learning_object.blueprints for recipe in blueprint.recipes
    ]
    if not named:
        return all_recipes
    exercised = [recipe for recipe in all_recipes if recipe.id in named]
    return exercised or all_recipes


def predict_item_success(
    vault: LoadedVault,
    item: PracticeItem,
    learning_object: LearningObject,
    component_recall: ComponentRecall,
) -> float | None:
    """P(success) on a specific item via the blueprint recipes it exercises (§9.2).

    Applies the item's selected-response guess floor. Returns None when the LO
    has no blueprints (caller keeps the legacy prediction path).
    """

    if not learning_object.blueprints:
        return None
    recipes = item_exercised_recipes(vault, item, learning_object)
    if not recipes:
        return None
    slip = float(vault.config.evidence.blueprints.slip)
    guess = guess_floor_for_item(item, vault.config)
    projections = [
        project_recipe(recipe, component_recall, slip=slip, guess=guess) for recipe in recipes
    ]
    return clamp(max(p.success_probability for p in projections))
