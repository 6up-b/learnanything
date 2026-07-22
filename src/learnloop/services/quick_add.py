"""Quick add (spec_source_ingestion_v2 §1).

Paste one source -> auto-selected units, a suggested role, a default brief, and
ONE confirmation on the happy path (token estimate + any external-AI consent),
then a priority build batch that reaches a study map ahead of bulk work.

The flow's state machine has exactly ONE consent/confirmation checkpoint:

    plan_quick_add(...)  ->  [ the single confirmation ]  ->  enqueue_quick_add(...)

``plan_quick_add`` is pure (no writes, no enqueue, no external AI): it reads the
already-extracted outline, runs a deterministic ToC-guided selection, suggests a
role, fills a default brief, and estimates tokens via the build plan. Everything
it returns is the confirmation payload. ``enqueue_quick_add`` is the
post-confirmation step: it creates the source set and enqueues the priority
[inventory(selected) -> bootstrap_synthesis] batch.

Acquisition (fetch + local extraction) is NOT a consent checkpoint — it is
deterministic, local, and token-free — so the CLI/sidecar run it before planning
when the source has no extraction yet (via the existing import machinery). Late
units beyond the selected relevant scope route through append in M7; the seam is
the source-set scope, which append can widen without re-synthesising.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from learnloop.services.acquisition_preview import build_acquisition_preview
from learnloop.services.build_plan import build_build_plan
from learnloop.services.source_outline import OutlineNotFound, build_source_outline

# Acquisition category (learnloop.ingest.resolution.SourceCategory) -> a suggested
# source-set role (source_set_synthesis role vocabulary).
_ROLE_BY_CATEGORY: dict[str, str] = {
    "pdf": "primary_textbook",
    "youtube": "lecture",
    "arxiv": "paper",
    "web": "reference",
    "textfile": "reference",
}
# Categories whose role is a confident guess; the rest proceed flagged (§1: role
# ambiguity proceeds flagged, not blocked).
_CONFIDENT_ROLE_CATEGORIES = frozenset({"pdf", "youtube", "arxiv"})
_STOPWORDS = frozenset(
    {"the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "with", "into", "intro"}
)


class QuickAddError(ValueError):
    """Typed failure for the Quick-add plan/enqueue flow."""

    def __init__(self, code: str, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


@dataclass
class QuickAddPlan:
    source: str
    normalized_uri: str
    category: str | None
    subject_id: str | None
    source_id: str
    revision_id: str
    extraction_id: str
    title: str
    suggested_role: str
    role_ambiguous: bool
    selected_unit_ids: list[str]
    selected_unit_labels: list[str]
    selected_tokens: int
    outline_tokens: int
    whole_source: bool
    brief: dict[str, Any]
    token_estimate: dict[str, Any]
    external_ai_consent: list[dict[str, Any]] = field(default_factory=list)

    @property
    def source_set_id(self) -> str:
        return f"sset_quickadd_{self.source_id}"

    def confirmation(self) -> dict[str, Any]:
        """THE single confirmation checkpoint (§1): what will be imported, the
        selected-unit summary, the suggested role, the token estimate, and any
        external-AI consent. There is no other consent gate in the flow."""

        totals = self.token_estimate.get("totals", {}) if isinstance(self.token_estimate, dict) else {}
        return {
            "id": "quick_add_confirm",
            "title": self.title,
            "source": self.source,
            "normalized_uri": self.normalized_uri,
            "suggested_role": self.suggested_role,
            "role_ambiguous": self.role_ambiguous,
            "selected_unit_ids": list(self.selected_unit_ids),
            "selected_unit_labels": list(self.selected_unit_labels),
            "selected_unit_count": len(self.selected_unit_ids),
            "selected_tokens": self.selected_tokens,
            "whole_source": self.whole_source,
            "estimated_input_tokens": totals.get("input_tokens", self.selected_tokens),
            "estimated_calls": totals.get("calls"),
            "external_ai_consent": list(self.external_ai_consent),
            "requires_external_ai": bool(self.external_ai_consent),
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "normalized_uri": self.normalized_uri,
            "category": self.category,
            "subject_id": self.subject_id,
            "source_id": self.source_id,
            "revision_id": self.revision_id,
            "extraction_id": self.extraction_id,
            "source_set_id": self.source_set_id,
            "title": self.title,
            "suggested_role": self.suggested_role,
            "role_ambiguous": self.role_ambiguous,
            "selected_unit_ids": list(self.selected_unit_ids),
            "selected_unit_labels": list(self.selected_unit_labels),
            "selected_tokens": self.selected_tokens,
            "outline_tokens": self.outline_tokens,
            "whole_source": self.whole_source,
            "brief": dict(self.brief),
            "token_estimate": self.token_estimate,
            "external_ai_consent": list(self.external_ai_consent),
            # The state machine exposes exactly one confirmation checkpoint.
            "confirmation": self.confirmation(),
        }


def _keywords(brief: dict[str, Any], vault, subject_id: str | None) -> set[str]:
    tokens: set[str] = set()

    def _add(text: Any) -> None:
        for word in re.findall(r"[a-z0-9]+", str(text or "").lower()):
            if len(word) >= 3 and word not in _STOPWORDS:
                tokens.add(word)

    for key in ("subject", "topic", "goal_title"):
        _add(brief.get(key))
    for topic in brief.get("include_topics") or []:
        _add(topic)
    if subject_id and vault is not None:
        subject = getattr(vault, "subjects", {}).get(subject_id)
        metadata = getattr(subject, "metadata", None)
        _add(getattr(metadata, "title", None) or subject_id)
    return tokens


def select_relevant_units(outline, *, keywords: set[str], cap_tokens: int) -> tuple[list[str], list[str], int, bool]:
    """Deterministic ToC-guided relevant-scope selection (§1).

    Whole source when it fits under ``cap_tokens``; otherwise the brief/subject
    keyword-matching chapters in outline order up to the cap (falling back to the
    leading chapters when nothing matches). Returns
    ``(unit_ids, labels, tokens, whole_source)``. Always non-empty when the
    outline has units."""

    units = list(outline.units)
    if not units:
        return [], [], 0, False
    total = sum(unit.approx_tokens for unit in units)
    if total <= cap_tokens:
        return (
            [unit.unit_id for unit in units],
            [unit.label for unit in units],
            total,
            True,
        )

    def _matches(unit) -> bool:
        label = unit.label.lower()
        return any(keyword in label for keyword in keywords)

    matched = [unit for unit in units if _matches(unit)]
    ordered = matched or units  # fall back to leading chapters when nothing matches
    picked_ids: list[str] = []
    picked_labels: list[str] = []
    accumulated = 0
    for unit in ordered:
        if picked_ids and accumulated + unit.approx_tokens > cap_tokens:
            continue
        picked_ids.append(unit.unit_id)
        picked_labels.append(unit.label)
        accumulated += unit.approx_tokens
    return picked_ids, picked_labels, accumulated, False


def _resolve_extraction(repo, source_id: str) -> tuple[str, str] | None:
    """Return ``(revision_id, extraction_id)`` for the latest completed extraction
    of ``source_id`` (its current revision preferred), or None."""

    revisions = repo.source_revisions_for(source_id)
    if not revisions:
        return None
    artifact = repo.get_source_artifact(source_id)
    current_id = artifact.get("current_revision_id") if artifact else None
    ordered = sorted(revisions, key=lambda rev: rev["id"] == current_id, reverse=True)
    for revision in ordered:
        runs = repo.extraction_runs_for_revision(revision["id"])
        completed = [run for run in runs if run.get("status") == "completed"]
        if completed:
            return revision["id"], completed[-1]["id"]
    return None


def _default_brief(
    brief_overrides: dict[str, Any] | None,
    title: str,
    subject_id: str | None,
    vault=None,
) -> dict[str, Any]:
    from learnloop.services.brief import validate_brief
    from learnloop.services.learner_profile import read_learner_profile
    from learnloop.vault.paths import VaultPaths

    brief: dict[str, Any] = {
        "outcome": "general_learning",
        "scope": "relevant",
    }
    if subject_id:
        brief["subject"] = subject_id
    if title:
        brief["source_title"] = title
    for key, value in validate_brief(brief_overrides, strict=False).items():
        if value is not None:
            brief[key] = value
    # Surface the vault's declared learner level in the plan preview; the
    # synthesis choke point (_create_study_map) merges it again regardless.
    if vault is not None and not brief.get("starting_level"):
        profile = read_learner_profile(VaultPaths(vault.root, vault.config))
        if profile is not None:
            brief["starting_level"] = profile["starting_level"]
    return brief


def plan_quick_add(
    repo,
    config,
    vault,
    source: str,
    *,
    subject_id: str | None = None,
    brief_overrides: dict[str, Any] | None = None,
) -> QuickAddPlan:
    """Build the single-confirmation Quick-add plan for an already-extracted
    source. Raises ``quick_add_requires_import`` when no completed extraction
    exists yet (the caller runs import first, then re-plans)."""

    preview = build_acquisition_preview(repo, config, [source])
    item = preview.items[0] if preview.items else None
    if item is None or not item.recognized:
        detail = item.error if item is not None else "unrecognized source"
        raise QuickAddError("unsupported_source", f"Quick add cannot use this source: {detail}")

    source_id = item.existing_source_id
    if not source_id:
        raise QuickAddError(
            "quick_add_requires_import",
            "This source has not been imported yet; run import, then quick-add.",
            details={"normalized_uri": item.normalized_uri, "category": item.category},
        )
    resolved = _resolve_extraction(repo, source_id)
    if resolved is None:
        raise QuickAddError(
            "quick_add_requires_import",
            "This source has no completed extraction yet; import must finish first.",
            details={"source_id": source_id},
        )
    revision_id, extraction_id = resolved

    try:
        outline = build_source_outline(repo, extraction_id)
    except OutlineNotFound as exc:
        raise QuickAddError("extraction_not_found", str(exc)) from exc

    brief = _default_brief(brief_overrides, outline.title, subject_id, vault=vault)
    keywords = _keywords(brief, vault, subject_id)
    cap = config.ingest.budgets.quick_add_scope_input_tokens
    unit_ids, labels, tokens, whole = select_relevant_units(outline, keywords=keywords, cap_tokens=cap)

    category = item.category
    suggested_role = _ROLE_BY_CATEGORY.get(category or "", "reference")
    role_ambiguous = category not in _CONFIDENT_ROLE_CATEGORIES

    plan_estimate = build_build_plan(
        repo,
        config,
        vault,
        subject_id=subject_id,
        selections=[{"extraction_id": extraction_id, "selected_unit_ids": unit_ids}],
    ).as_dict()

    consent: list[dict[str, Any]] = []
    for entry in item.potential_external or []:
        consent.append({**entry, "stage": "extraction"})
    # Inventory + synthesis call the configured external AI provider (codex) — the
    # single consent that actually spends tokens on the build batch.
    consent.append(
        {
            "kind": "external_ai_synthesis",
            "stage": "synthesis",
            "reason": "unit inventory and study-map synthesis call the configured AI provider",
            "provider": "codex",
        }
    )

    return QuickAddPlan(
        source=source,
        normalized_uri=item.normalized_uri or source,
        category=category,
        subject_id=subject_id,
        source_id=source_id,
        revision_id=revision_id,
        extraction_id=extraction_id,
        title=outline.title,
        suggested_role=suggested_role,
        role_ambiguous=role_ambiguous,
        selected_unit_ids=unit_ids,
        selected_unit_labels=labels,
        selected_tokens=tokens,
        outline_tokens=outline.approx_tokens,
        whole_source=whole,
        brief=brief,
        token_estimate=plan_estimate,
        external_ai_consent=consent,
    )


def enqueue_quick_add(
    vault,
    ingest_jobs,
    plan: QuickAddPlan,
    *,
    role_override: str | None = None,
    output_budget_tokens: int | None = None,
    unlimited_token_budget: bool = False,
) -> dict[str, Any]:
    """Post-confirmation step: create the source set from the plan and enqueue the
    priority [inventory(selected) -> bootstrap_synthesis] build batch (§1)."""

    from learnloop.vault.writer import upsert_source_set

    if plan.subject_id is None:
        raise QuickAddError("subject_required", "Quick add needs a target subject to build a study map.")

    role = role_override or plan.suggested_role
    scope = [{"unit_id": unit_id} for unit_id in plan.selected_unit_ids]
    upsert_source_set(
        vault.root,
        {
            "id": plan.source_set_id,
            "subject_id": plan.subject_id,
            "title": plan.title or plan.source_set_id,
            "members": [
                {
                    "source_id": plan.source_id,
                    "revision_id": plan.revision_id,
                    "default_role": role,
                    "scope": scope,
                    "priority": 1,
                }
            ],
        },
    )

    units = [{"unit_id": unit_id, "role": role} for unit_id in plan.selected_unit_ids]
    batch_id = ingest_jobs.enqueue_quick_add_build(
        extraction_id=plan.extraction_id,
        units=units,
        source_set_id=plan.source_set_id,
        subject_id=plan.subject_id,
        brief=plan.brief,
        mode="auto",
        output_budget_tokens=output_budget_tokens,
        unlimited_token_budget=unlimited_token_budget,
    )
    return {
        "batch_id": batch_id,
        "source_set_id": plan.source_set_id,
        "subject_id": plan.subject_id,
        "role": role,
        "selected_unit_ids": list(plan.selected_unit_ids),
    }
