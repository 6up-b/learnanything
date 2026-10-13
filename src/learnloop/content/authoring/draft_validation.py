"""Post-import validation of an authored exercise against its request (spec §8.1).

It lives in the content layer so the interactive import job, which may not
import the service, validates a learner's pick against the proposal it came
from (Codex re-review F7); ``learnloop.instructional.validation`` re-exports it.

A raw textbook exercise matched a request on provisional, quote-verified
metadata. Before it fulfils a need (S2b), serves as an independent check or
is harvested for a thin facet, its authored draft is checked against the same
constraints:

* its ``evidence_facets`` must be ones the author asserted, not the LO-union
  fallback the import applies when the author names none (``facet_basis``);
* it must test the requested facets (any, or all for an integrative request);
* the estimator's minutes for the authored practice mode AND the authored
  duration (``expected_minutes``) must fit ``max_estimated_minutes``
  (refused without an estimator, never ignored). The interactive job
  evaluates the plan estimator's carried response (:func:`duration_estimator`).

A draft that fails does not fulfil the need or the check; a learner's own
pick is still imported (learner authority) and the claim corrected on screen.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from learnloop.vault.models import LoadedVault


def _field(constraints: Any, name: str, default: Any = None) -> Any:
    if isinstance(constraints, Mapping):
        return constraints.get(name, default)
    return getattr(constraints, name, default)


def draft_validator(vault: LoadedVault, constraints: Any, *, intent: str = "practice",
                    estimator: Callable[..., Any] | None = None,
                    independent: bool = False) -> Callable[[Any], Mapping[str, Any]]:
    """``constraints``: ``PracticeConstraints`` or its stored mapping (a proposal's receipt)."""

    wanted = [vault.canonical_facet_id(str(facet)) for facet in _field(constraints, "facet_ids", ()) or ()]
    match = _field(constraints, "facet_match", "any") or "any"
    max_minutes = _field(constraints, "max_estimated_minutes")
    strict = independent or intent in ("discriminate", "retention")

    def validate(draft: Any) -> Mapping[str, Any]:
        reasons: list[str] = []
        corrections: list[str] = []
        facets = {vault.canonical_facet_id(str(facet)) for facet in draft.payload.get("evidence_facets") or ()}
        result: dict[str, Any] = {"checked": True, "facets": sorted(facets), "facet_basis": draft.facet_basis}
        if strict and draft.facet_basis != "authored":
            reasons.append("its facets came from the learning object's fallback, not from the author")
        if wanted:
            hits = facets & set(wanted)
            if (match == "all" and hits != set(wanted)) or (match != "all" and not hits):
                if match == "all" and hits:
                    reasons.append(f"it does not practise every requested facet "
                                   f"({', '.join(sorted(set(wanted) - hits))})")
                else:
                    reasons.append(f"it practises {', '.join(sorted(facets)) or 'nothing registered'}, "
                                   f"not {', '.join(wanted)}")
                corrections.append(f"practise {', '.join(sorted(facets)) or 'something else'}, "
                                   f"not {', '.join(wanted)}")
        if max_minutes is not None:
            estimate = None if estimator is None else estimator(
                str(draft.payload.get("id") or ""), draft.payload.get("practice_mode"),
                draft.payload.get("expected_minutes"))
            if estimator is None:
                reasons.append("max_estimated_minutes needs a minutes estimator")
            elif estimate is None:
                reasons.append("no minutes estimate for its practice mode")
            else:
                minutes = float(getattr(estimate, "minutes", estimate))
                result["minutes"] = round(minutes, 4)
                if minutes > float(max_minutes):
                    reasons.append(f"it would take about {minutes:.1f} minutes (more than {max_minutes})")
                    corrections.append(f"take about {minutes:.0f} minutes, more than {max_minutes:g}")
        result["ok"] = not reasons
        if reasons:
            result["reason"] = "; ".join(reasons)
            result["correction"] = "this exercise turned out to " + (
                " and ".join(corrections) if corrections else "differ from what was suggested")
        return result

    return validate


def duration_estimator(duration_by_mode: Mapping[str, Mapping[str, Any]]) -> Callable[..., float | None]:
    """The plan estimator's carried response per practice mode
    (``instructional.practice.duration_response``), evaluated on the authored
    draft: ``(item_id, practice_mode, expected_minutes) -> minutes``, or None
    for a mode it has no estimate for (Codex third pass F7).

    An authored duration (``expected_minutes`` > 0) is the estimator's prior;
    without one the estimator's fallback holds, as the plan computes it."""

    def estimate(_item_id: str, practice_mode: str | None, expected_minutes: Any) -> float | None:
        response = duration_by_mode.get(str(practice_mode or ""))
        if not response:
            return None
        try:
            authored = None if expected_minutes is None else float(expected_minutes)
        except (TypeError, ValueError):
            authored = None
        if authored is not None and authored > 0:
            return float(response["at_zero"]) + float(response["per_authored_minute"]) * authored
        return float(response["fallback_minutes"])

    return estimate


__all__ = ["draft_validator", "duration_estimator"]
