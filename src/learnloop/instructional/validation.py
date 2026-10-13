"""Post-import validation of an authored exercise against its request (spec §8.1).

A raw textbook exercise matched a request on provisional, quote-verified
metadata. Before it fulfils a need (S2b), serves as an independent check or
is harvested for a thin facet, its authored draft is checked against the same
constraints:

* its ``evidence_facets`` must be ones the author asserted, not the LO-union
  fallback the import applies when the author names none (``facet_basis``);
* it must test the requested facets (any, or all for an integrative request);
* the estimator's minutes for the authored practice mode must fit
  ``max_estimated_minutes`` (refused without an estimator, never ignored).

A draft that fails does not fulfil the need or the check; a learner's own
pick is still imported (learner authority) and the claim corrected on screen.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from learnloop.vault.models import LoadedVault


def draft_validator(vault: LoadedVault, constraints: Any, *, intent: str = "practice",
                    estimator: Callable[..., Any] | None = None,
                    independent: bool = False) -> Callable[[Any], Mapping[str, Any]]:
    wanted = [vault.canonical_facet_id(str(facet)) for facet in getattr(constraints, "facet_ids", ()) or ()]
    match = getattr(constraints, "facet_match", "any") or "any"
    max_minutes = getattr(constraints, "max_estimated_minutes", None)
    strict = independent or intent in ("discriminate", "retention")

    def validate(draft: Any) -> Mapping[str, Any]:
        reasons: list[str] = []
        facets = {vault.canonical_facet_id(str(facet)) for facet in draft.payload.get("evidence_facets") or ()}
        result: dict[str, Any] = {"checked": True, "facets": sorted(facets), "facet_basis": draft.facet_basis}
        if strict and draft.facet_basis != "authored":
            reasons.append("its facets came from the learning object's fallback, not from the author")
        if wanted:
            hits = facets & set(wanted)
            if match == "all" and hits != set(wanted):
                reasons.append(f"it does not practise every requested facet ({', '.join(sorted(set(wanted) - hits))})")
            elif match != "all" and not hits:
                reasons.append(f"it practises {', '.join(sorted(facets)) or 'nothing registered'}, "
                               f"not {', '.join(wanted)}")
        if max_minutes is not None:
            if estimator is None:
                reasons.append("max_estimated_minutes needs a minutes estimator")
            else:
                estimate = estimator(str(draft.payload.get("id") or ""), draft.payload.get("practice_mode"),
                                     draft.payload.get("expected_minutes"))
                minutes = float(getattr(estimate, "minutes", estimate))
                result["minutes"] = round(minutes, 4)
                if minutes > float(max_minutes):
                    reasons.append(f"it would take about {minutes:.1f} minutes (more than {max_minutes})")
        result["ok"] = not reasons
        if reasons:
            result["reason"] = "; ".join(reasons)
            result["correction"] = ("this exercise turned out to practise "
                                    + (", ".join(sorted(facets)) or "something else")
                                    + (f", not {', '.join(wanted)}" if wanted else ""))
        return result

    return validate


__all__ = ["draft_validator"]
