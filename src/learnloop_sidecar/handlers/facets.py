from __future__ import annotations

from typing import Any

from learnloop.learner.facet_diagnostics import mastery_diagnostic_view
from learnloop.learner.facet_state_reader import is_canonical_state_vault
from learnloop.scheduling.scheduler import build_due_queue
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import versioned
from learnloop_sidecar.registry import method

_STATES = ("solid", "uncertain", "known_gap", "unexamined")
_TITLE_MAX = 80


@method("get_facet_mastery")
def get_facet_mastery(ctx: SidecarContext, _params) -> dict[str, Any]:
    """Evidence-facet mastery rollup powering the radar chart.

    For every Learning Object we take ``mastery_diagnostic_view`` (which already
    merges required facets with any open facet-uncertainty states) and fold each
    per-LO facet row into a vault-wide axis keyed by facet id.

    Per-LO facet mastery is the diagnostic posterior's probability that the
    facet is solid: ``hypothesis_marginal["facet_solid:<facet>"]`` (missing
    label -> 0.0). When no hypothesis marginal exists (facet never opened a
    diagnostic), we fall back to the coarse state: ``solid`` (independent
    evidence mass above the configured floor) -> 1.0, anything else
    (``unexamined``) -> 0.0.

    The aggregate ``mastery`` per facet is the unweighted mean of those per-LO
    values across every LO requiring the facet. A plain mean (rather than an
    evidence-weighted one) keeps the axis interpretable as "fraction of LOs on
    this facet believed solid", and unexamined LOs correctly drag the axis
    toward 0 instead of being silently skipped.

    Facets are sorted alphabetically by facet id; facets with no evidence still
    appear (state ``unexamined``, mastery from the fallback above).

    ``uncertainty`` per facet is the unweighted mean of the per-LO diagnostic
    posterior entropies (``mastery_diagnostic_view``'s ``uncertainty`` field,
    in nats; ``None``/never-opened rows count as 0.0) across every LO requiring
    the facet. It is the radius of the variance band the radar draws around the
    mastery polygon: a fat band means the diagnostic posterior still hesitates
    between "solid" and gap/misconception hypotheses on this axis.

    Per practice item, ``is_probe``/``queued`` come from one read-only
    ``build_due_queue`` pass (``persist_explanations=False`` so a chart refresh
    never writes scheduler explanations): ``queued`` means the item is in
    today's due queue; ``is_probe`` mirrors the queue serializer's probe test
    (``components["probe_eig"] > 0``, i.e. the scheduler selected it for
    diagnostic information gain rather than plain review).
    """

    vault, repository = ctx.require_vault()

    # Interpretive note for the radar overlay: item dots sit at their authored
    # difficulty radius, so dots just *outside* the mastery polygon mark the
    # desirable-difficulty band the selector should be sampling from, and probe
    # markers should cluster on axes with fat uncertainty bands. This view
    # exists to make selection-policy behavior visible at a glance.
    queue = build_due_queue(vault, repository, persist_explanations=False)
    queued_ids = {scheduled.practice_item_id for scheduled in queue}
    probe_ids = {
        scheduled.practice_item_id
        for scheduled in queue
        if scheduled.components.get("probe_eig", 0.0) > 0.0
    }

    # KM3 §9.6 re-key: mvp-0.7 folds per-LO facet rows onto their canonical
    # (post-alias) facet id so a shared parent surfaces under every LO that
    # touches it ("also counted toward X and Y"); mvp-0.6 keeps the legacy raw
    # key byte-identical. The DTO carries ``modelVersion`` so the UI can branch.
    canonical_keys = is_canonical_state_vault(vault)

    def _key(raw: str) -> str:
        return vault.canonical_facet_id(raw) if canonical_keys else raw

    facets: dict[str, dict[str, Any]] = {}
    los_seen: set[str] = set()

    for lo_id, learning_object in sorted(vault.learning_objects.items()):
        diagnostic = mastery_diagnostic_view(vault, repository, lo_id)
        for row in diagnostic["facets"]:
            raw_facet_id = str(row["facet_id"])
            facet_id = _key(raw_facet_id)
            entry = facets.setdefault(
                facet_id,
                {
                    "facet_id": facet_id,
                    "_masteries": [],
                    "_uncertainties": [],
                    "state_counts": {state: 0 for state in _STATES},
                    "learning_objects": [],
                    "practice_items": [],
                },
            )
            state = row["state"] if row["state"] in _STATES else "unexamined"
            mastery = _facet_mastery(raw_facet_id, row)
            entry["_masteries"].append(mastery)
            entry["_uncertainties"].append(max(0.0, float(row.get("uncertainty") or 0.0)))
            entry["state_counts"][state] += 1
            entry["learning_objects"].append(
                {
                    "id": lo_id,
                    "title": learning_object.title,
                    "state": state,
                    "facet_mastery": mastery,
                }
            )
            los_seen.add(lo_id)

    items_seen: set[str] = set()
    for item_id, item in sorted(vault.practice_items.items()):
        for facet in item.evidence_facets:
            raw_facet_id = str(facet)
            facet_id = _key(raw_facet_id)
            entry = facets.get(facet_id)
            if entry is None:
                continue
            entry["practice_items"].append(
                {
                    "id": item_id,
                    "title": _item_title(item.prompt),
                    "learning_object_id": item.learning_object_id,
                    "weight": item.evidence_weights.get(raw_facet_id),
                    "difficulty": item.difficulty,
                    "is_probe": item_id in probe_ids,
                    "queued": item_id in queued_ids,
                }
            )
            items_seen.add(item_id)

    question_counts = repository.question_counts_by_facet()
    payload = []
    for facet_id in sorted(facets):
        entry = facets[facet_id]
        masteries = entry.pop("_masteries")
        uncertainties = entry.pop("_uncertainties")
        entry["mastery"] = sum(masteries) / len(masteries) if masteries else 0.0
        entry["uncertainty"] = sum(uncertainties) / len(uncertainties) if uncertainties else 0.0
        entry["question_count"] = question_counts.get(facet_id, 0)
        payload.append(entry)

    return versioned(
        {
            "model_version": vault.config.algorithms.algorithm_version,
            "canonical_keys": canonical_keys,
            "facets": payload,
            "counts": {
                "facets": len(payload),
                "learning_objects": len(los_seen),
                "practice_items": len(items_seen),
            },
        }
    )


def _facet_mastery(facet_id: str, row: dict[str, Any]) -> float:
    marginal = row.get("hypothesis_marginal")
    if marginal:
        return max(0.0, min(1.0, float(marginal.get(f"facet_solid:{facet_id}", 0.0))))
    return 1.0 if row.get("state") == "solid" else 0.0


def _item_title(prompt: str) -> str:
    text = " ".join(prompt.split())
    if len(text) <= _TITLE_MAX:
        return text
    return text[: _TITLE_MAX - 1].rstrip() + "…"
