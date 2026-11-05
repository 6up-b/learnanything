"""Router objective RO4 §8.5: a goal's use weights, the objective's preferences about what knowledge is for.

* **Dated goal**: ``ω_{g,L}`` per topic in the goal's scope, at its ``due_at``; one default for the goal
  (``dated``) and optional per-topic weights (``per_lo``). Asked once at goal creation and adjustable later.
* **Undated use**: ``c_L`` per day per topic, from enrollment, with no end (``undated_density``). A config default,
  ``[router_objective] undated_use_density`` (1/90), **copied into the goal at creation**, so a later config change
  never rewrites a goal's history or a replay.

Where a goal's weights come from, in order: its confirmed contract's ``use_weight`` (a field in the content hash and
out of the support hash; an edit to it alone is the change class ``use_weight_change``); the ``use_weight`` copied
into its ``goals.yaml`` entry when it was created at the tag; else the **stated default** for a goal with no
confirmed contract and no copy (a goal created before RO4, or below the tag): the config's ``dated_use_weight`` and
``undated_use_density``, labelled ``default``. No old contract or hash is rewritten. ``Goal.priority`` stays a
tie-break. Pass thresholds are not used.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import json
from typing import Any

CONTRACT = "contract"
COPIED = "copied_at_creation"
DEFAULT = "default"


@dataclass(frozen=True)
class UseWeights:
    dated: float
    undated_density: float
    per_lo: Mapping[str, float] = field(default_factory=dict)
    source: str = DEFAULT
    contract_version_id: str | None = None

    def for_lo(self, lo: str) -> float:
        return float(self.per_lo.get(lo, self.dated))

    def as_dict(self) -> dict[str, Any]:
        return {"dated": self.dated, "undated_density": self.undated_density, "per_lo": dict(self.per_lo),
                "source": self.source, "contract_version_id": self.contract_version_id}


def config_defaults(config: Any) -> dict[str, float]:
    section = getattr(config, "router_objective", None)
    return {"dated": float(getattr(section, "dated_use_weight", 1.0)),
            "undated_density": float(getattr(section, "undated_use_density", 1.0 / 90.0))}


def _parsed(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    from learnloop.goals.goal_contracts import canonical_use_weight

    try:
        return canonical_use_weight(value)
    except ValueError:
        return None


def for_goal(goal: Any, repository: Any, config: Any) -> UseWeights:
    """The weights in force for ``goal`` (module docstring's order)."""

    defaults = config_defaults(config)
    head_id = getattr(goal, "confirmed_contract_head_id", None)
    if head_id and repository is not None:
        try:
            row = repository.fetch_goal_contract_version(str(head_id))
        except Exception:  # noqa: BLE001 - an unreadable contract reads as unconfirmed
            row = None
        if row is not None:
            try:
                body = json.loads(row.get("contract_json") or "{}")
            except ValueError:
                body = {}
            parsed = _parsed(body.get("use_weight"))
            if parsed is not None:
                return UseWeights(dated=parsed["dated"], undated_density=parsed["undated_density"],
                                  per_lo=parsed["per_lo"], source=CONTRACT, contract_version_id=str(head_id))
    extra = getattr(goal, "model_extra", None) or {}
    parsed = _parsed(extra.get("use_weight"))
    if parsed is not None:
        return UseWeights(dated=parsed["dated"], undated_density=parsed["undated_density"], per_lo=parsed["per_lo"],
                          source=COPIED)
    return UseWeights(dated=defaults["dated"], undated_density=defaults["undated_density"], source=DEFAULT)


def copy_at_creation(config: Any, *, dated: float | None = None) -> dict[str, Any]:
    """The ``use_weight`` a goal is created with at the tag: the asked weight (or the config's default) and the
    config's undated density, copied now."""

    defaults = config_defaults(config)
    return {"dated": float(defaults["dated"] if dated is None else dated), "per_lo": {},
            "undated_density": defaults["undated_density"]}


__all__ = ["CONTRACT", "COPIED", "DEFAULT", "UseWeights", "config_defaults", "copy_at_creation", "for_goal"]
