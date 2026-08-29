"""ING M8 — provenance-outcome analytics (spec §11). REPORT-ONLY.

These report provenance-outcome ASSOCIATIONS, never source effectiveness or a
source ranking. Output is additive improvement SUGGESTIONS (maintenance-feed
shaped); this module never writes curriculum, source, or belief state.

Three association families, each gated on minimum sample thresholds with the raw
counts surfaced as visible uncertainty (counts, not point claims):

* ``repeated_failure_despite_coverage`` — a learning object the learner has both
  been EXPOSED to (a ``source_exposure`` event, §11: coverage alone never proves
  the learner saw the source) and repeatedly failed. Suggests more practice/examples.
* ``alternate_exposure_preceded_resolution`` — an alternate-explanation span was
  opened, and a later attempt on the object succeeded. A positive association,
  reported with counts; it is NOT a causal effectiveness claim.
* ``needs_more_example_sources`` — an object with repeated failure and thin
  practice supply. Suggests adding example/practice sources.

The alternate association is report-only; the two actionable families also render
as additive maintenance-feed notices (auto-expiry, never state writes).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault

# Minimum sample thresholds — below these we make no claim (§11).
DEFAULT_MIN_ATTEMPTS = 3
DEFAULT_MIN_FAILURES = 2
DEFAULT_MIN_EXPOSURES = 1
# An object with fewer active practice items than this is "thin supply".
DEFAULT_THIN_PRACTICE = 2
_ATTEMPT_SCAN_LIMIT = 200

_SEMANTIC_RELATIONS = frozenset({"primary", "support", "alternate"})


@dataclass(frozen=True)
class Association:
    kind: str
    entity_type: str
    entity_id: str
    subject_id: str | None
    title: str
    counts: dict[str, int]
    uncertainty_note: str
    suggestion: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "subject_id": self.subject_id,
            "title": self.title,
            "counts": dict(self.counts),
            "uncertainty_note": self.uncertainty_note,
            "suggestion": dict(self.suggestion),
        }


@dataclass
class SourceOutcomeReport:
    subject_id: str | None
    thresholds: dict[str, int]
    associations: list[Association] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "thresholds": dict(self.thresholds),
            "associations": [a.as_dict() for a in self.associations],
        }


def _attempt_failed(attempt: dict[str, Any]) -> bool:
    return (
        attempt.get("attempt_type") == "dont_know"
        or float(attempt.get("correctness") or 0.0) <= 0.40
        or bool(attempt.get("error_type"))
    )


def _lo_facet_ids(vault: LoadedVault, learning_object) -> set[str]:
    facets: set[str] = set()
    for blueprint in learning_object.blueprints or []:
        for recipe in blueprint.recipes or []:
            for comp in [*(recipe.all_of or []), *(recipe.any_of or [])]:
                facets.add(vault.canonical_facet_id(comp.facet))
            if recipe.integration is not None:
                facets.add(vault.canonical_facet_id(recipe.integration.facet))
    for item in vault.practice_items.values():
        if item.learning_object_id == learning_object.id:
            facets.update(vault.canonical_facet_id(f) for f in item.evidence_facets)
    return facets


def analyze_source_outcomes(
    vault: LoadedVault,
    repository: Repository,
    *,
    subject_id: str | None = None,
    min_attempts: int = DEFAULT_MIN_ATTEMPTS,
    min_failures: int = DEFAULT_MIN_FAILURES,
    min_exposures: int = DEFAULT_MIN_EXPOSURES,
    thin_practice: int = DEFAULT_THIN_PRACTICE,
) -> SourceOutcomeReport:
    """Deterministic provenance-outcome associations, report-only (§11)."""

    thresholds = {
        "min_attempts": min_attempts,
        "min_failures": min_failures,
        "min_exposures": min_exposures,
        "thin_practice": thin_practice,
    }
    report = SourceOutcomeReport(subject_id=subject_id, thresholds=thresholds)

    practice_counts: dict[str, int] = {}
    for item in vault.practice_items.values():
        practice_counts[item.learning_object_id] = practice_counts.get(item.learning_object_id, 0) + 1

    for lo_id, lo in sorted(vault.learning_objects.items()):
        if getattr(lo, "status", "active") != "active":
            continue
        if subject_id is not None and subject_id not in (lo.subjects or []):
            continue
        subject = lo.subjects[0] if lo.subjects else None

        attempts = repository.list_recent_attempts_by_learning_object(lo_id, limit=_ATTEMPT_SCAN_LIMIT)
        total = len(attempts)
        failures = [a for a in attempts if _attempt_failed(a)]
        n_fail = len(failures)

        # Coverage: does this object (or its facets) have semantic-authority links?
        semantic_links = [
            link
            for link in repository.entity_source_links("learning_object", lo_id)
            if link.get("relation") in _SEMANTIC_RELATIONS
        ]
        for facet_id in _lo_facet_ids(vault, lo):
            semantic_links.extend(
                link
                for link in repository.entity_source_links("facet", facet_id)
                if link.get("relation") in _SEMANTIC_RELATIONS
            )
        alternate_links = [l for l in semantic_links if l.get("relation") == "alternate"]

        # Exposure: the learner must actually have been shown a source (§11).
        exposures = repository.source_exposure_events(entity_type="learning_object", entity_id=lo_id)
        n_exposure = len(exposures)

        # (1) repeated failure DESPITE coverage the learner has actually seen.
        if (
            semantic_links
            and n_exposure >= min_exposures
            and total >= min_attempts
            and n_fail >= min_failures
        ):
            report.associations.append(
                Association(
                    kind="repeated_failure_despite_coverage",
                    entity_type="learning_object",
                    entity_id=lo_id,
                    subject_id=subject,
                    title=lo.title,
                    counts={
                        "attempts": total,
                        "failures": n_fail,
                        "semantic_sources": len(semantic_links),
                        "exposures": n_exposure,
                    },
                    uncertainty_note=(
                        f"{n_fail}/{total} attempts failed despite {len(semantic_links)} covering "
                        f"source(s) and {n_exposure} exposure(s) — an association, not a cause."
                    ),
                    suggestion={
                        "action": "generate_practice",
                        "label": "Generate more practice / examples",
                        "learning_object_id": lo_id,
                    },
                )
            )

        # (2) alternate-explanation exposure preceding a later success (positive assoc).
        if alternate_links and n_exposure >= min_exposures:
            alt_exposures = sorted(
                (e for e in exposures if e.get("span_id")),
                key=lambda e: e.get("created_at") or "",
            )
            first_alt_at = alt_exposures[0].get("created_at") if alt_exposures else None
            subsequent_success = 0
            if first_alt_at is not None:
                subsequent_success = sum(
                    1
                    for a in attempts
                    if (a.get("created_at") or "") > first_alt_at and not _attempt_failed(a)
                )
            if subsequent_success > 0:
                report.associations.append(
                    Association(
                        kind="alternate_exposure_preceded_resolution",
                        entity_type="learning_object",
                        entity_id=lo_id,
                        subject_id=subject,
                        title=lo.title,
                        counts={
                            "alternate_sources": len(alternate_links),
                            "exposures": n_exposure,
                            "subsequent_successes": subsequent_success,
                        },
                        uncertainty_note=(
                            f"{subsequent_success} success(es) followed an alternate-explanation "
                            "exposure — a temporal association only."
                        ),
                        suggestion={"action": "none", "label": "Report only — no action"},
                    )
                )

        # (3) repeated failure with thin practice supply → needs more example sources.
        if (
            total >= min_attempts
            and n_fail >= min_failures
            and practice_counts.get(lo_id, 0) < thin_practice
        ):
            report.associations.append(
                Association(
                    kind="needs_more_example_sources",
                    entity_type="learning_object",
                    entity_id=lo_id,
                    subject_id=subject,
                    title=lo.title,
                    counts={
                        "attempts": total,
                        "failures": n_fail,
                        "practice_items": practice_counts.get(lo_id, 0),
                    },
                    uncertainty_note=(
                        f"{n_fail}/{total} attempts failed with only "
                        f"{practice_counts.get(lo_id, 0)} practice item(s)."
                    ),
                    suggestion={
                        "action": "align_examples",
                        "label": "Add an example/practice source",
                        "learning_object_id": lo_id,
                    },
                )
            )

    return report


def source_outcome_notices(report: SourceOutcomeReport) -> list[dict[str, Any]]:
    """Additive maintenance-feed notices for the ACTIONABLE associations (§11).

    Never state writes: these are dismissible suggestions (auto-expiry). The
    positive ``alternate_exposure_preceded_resolution`` association is report-only
    and excluded here."""

    notices: list[dict[str, Any]] = []
    for assoc in report.associations:
        if assoc.kind == "alternate_exposure_preceded_resolution":
            continue
        notices.append(
            {
                "notice_type": assoc.kind,
                "dedup_key": assoc.entity_id,
                "subject_id": assoc.subject_id,
                "entity_type": assoc.entity_type,
                "entity_id": assoc.entity_id,
                "title": f"{assoc.title}: {assoc.uncertainty_note}",
                "action": assoc.suggestion,
                "detail": {"counts": assoc.counts},
            }
        )
    return notices
