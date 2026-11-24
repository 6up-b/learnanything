"""Deterministic build plan (spec_source_ingestion_v2 §8.6.2).

Given imported extractions plus the learner's unit selection, project the cost of
turning them into a study map *before* any pedagogical LLM call: exact revision /
asset / extraction hashes, the selected units and their cached-inventory markers
(M4 seam), per-stage input / cached / max-output token estimates and call counts
derived from ``[ingest.budgets]`` and ``[ingest.providers.<name>]``, cache savings,
the configured ceilings / provider, extraction warnings, Create-vs-Update routing,
and a what-will-be-created summary.

Zero LLM calls. Token sizing uses the single :func:`approx_token_count` estimator
so it never disagrees with the outline. When a batch is started from a plan, the
per-stage estimate is snapshotted into the batch/job payload (§6.2/§8.6.2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from learnloop.config import LearnLoopConfig
from learnloop.content.synthesis.ai_contracts import AppendReconciliationContext
from learnloop.content.synthesis.append_budget import append_groups, append_input_tokens
from learnloop.db.repositories import Repository
from learnloop.content.sources.source_outline import OutlineUnit, build_source_outline


@dataclass
class StageEstimate:
    stage: str
    calls: int
    input_tokens: int
    cached_tokens: int
    max_output_tokens: int
    ceiling: int
    exceeds_ceiling: bool
    peak_input_tokens: int | None = None

    def as_dict(self) -> dict:
        return {
            "stage": self.stage,
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "cached_tokens": self.cached_tokens,
            "max_output_tokens": self.max_output_tokens,
            "ceiling": self.ceiling,
            "exceeds_ceiling": self.exceeds_ceiling,
        }


@dataclass
class PlannedSource:
    extraction_id: str
    revision_id: str | None
    source_id: str | None
    title: str
    asset_hash: str | None
    extraction_result_hash: str | None
    selected_unit_ids: list[str] = field(default_factory=list)
    selected_unit_count: int = 0
    cached_inventory_count: int = 0
    approx_tokens: int = 0
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "extraction_id": self.extraction_id,
            "revision_id": self.revision_id,
            "source_id": self.source_id,
            "title": self.title,
            "asset_hash": self.asset_hash,
            "extraction_result_hash": self.extraction_result_hash,
            "selected_unit_ids": list(self.selected_unit_ids),
            "selected_unit_count": self.selected_unit_count,
            "cached_inventory_count": self.cached_inventory_count,
            "approx_tokens": self.approx_tokens,
            "warnings": list(self.warnings),
        }


@dataclass
class BuildPlan:
    routing: str
    subject_id: str | None
    provider: str
    provider_context_tokens: int | None
    provider_max_output_tokens: int | None
    sources: list[PlannedSource] = field(default_factory=list)
    stages: list[StageEstimate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def selected_unit_count(self) -> int:
        return sum(source.selected_unit_count for source in self.sources)

    @property
    def total_input_tokens(self) -> int:
        return sum(stage.input_tokens for stage in self.stages)

    @property
    def total_max_output_tokens(self) -> int:
        return sum(stage.max_output_tokens for stage in self.stages)

    @property
    def total_calls(self) -> int:
        return sum(stage.calls for stage in self.stages)

    @property
    def cache_savings_tokens(self) -> int:
        return sum(stage.cached_tokens for stage in self.stages)

    def as_dict(self) -> dict:
        return {
            "routing": self.routing,
            "subject_id": self.subject_id,
            "provider": self.provider,
            "provider_context_tokens": self.provider_context_tokens,
            "provider_max_output_tokens": self.provider_max_output_tokens,
            "sources": [source.as_dict() for source in self.sources],
            "stages": [stage.as_dict() for stage in self.stages],
            "warnings": list(self.warnings),
            "totals": {
                "selected_unit_count": self.selected_unit_count,
                "input_tokens": self.total_input_tokens,
                "max_output_tokens": self.total_max_output_tokens,
                "calls": self.total_calls,
                "cache_savings_tokens": self.cache_savings_tokens,
            },
            "what_will_be_created": {
                "sources": len(self.sources),
                "selected_units": self.selected_unit_count,
                "routing": self.routing,
                "subject_id": self.subject_id,
            },
        }

    def snapshot_payload(self) -> dict:
        """The estimate snapshot stored in a batch/job payload when it starts."""

        return {"stages": [stage.as_dict() for stage in self.stages], "totals": self.as_dict()["totals"]}


def subject_has_study_map(vault, subject_id: str | None) -> bool:
    """True when the subject already has an applied study map (any learning object).

    The Create-vs-Update seam (§8.6.2): a subject with no applied map routes to
    *create*; one with a map routes to *update*. This is the single routing rule."""

    if subject_id is None:
        return False
    for lo in getattr(vault, "learning_objects", {}).values():
        if subject_id in getattr(lo, "subjects", []) or []:
            return True
    return False


def route_create_or_update(vault, subject_id: str | None) -> str:
    return "update" if subject_has_study_map(vault, subject_id) else "create"


def build_build_plan(
    repo: Repository,
    config: LearnLoopConfig,
    vault,
    *,
    subject_id: str | None,
    selections: list[Mapping[str, object]],
    budget_overrides: Mapping[str, int] | None = None,
) -> BuildPlan:
    """Assemble the deterministic build plan for a set of selected extractions.

    ``selections`` is a list of ``{"extraction_id", "selected_unit_ids"}`` (an empty
    or missing ``selected_unit_ids`` means "all units of that extraction").

    ``budget_overrides`` layers per-run ceilings over ``[ingest.budgets]`` so the
    plan charts the ceilings the batch will actually run under — the same
    ``model_copy(update=...)`` seam synthesis uses for its own overrides."""

    routing = route_create_or_update(vault, subject_id)
    provider = config.ai.routing.canonical_ingest or config.ai.active_provider
    limits = config.ingest.providers.get(provider)
    provider_context = limits.context_tokens if limits else None
    provider_max_output = limits.max_output_tokens if limits else None
    budgets = config.ingest.budgets.model_copy(update=dict(budget_overrides or {}))

    planned: list[PlannedSource] = []
    unit_tokens: list[int] = []
    append_units = []
    cached_token_pool = 0
    global_warnings: list[str] = []
    for selection in selections:
        extraction_id = str(selection.get("extraction_id"))
        outline = build_source_outline(repo, extraction_id)
        run = repo.get_extraction_run(extraction_id)
        revision = repo.get_source_revision(outline.revision_id) if outline.revision_id else None

        requested = list(selection.get("selected_unit_ids") or [])
        units = _selected_units(outline.units, requested)
        cached = sum(1 for unit in units if bool(unit.inventory.get("inventoried")))
        warnings = _source_warnings(outline, units)
        source_tokens = sum(unit.approx_tokens for unit in units)
        planned.append(
            PlannedSource(
                extraction_id=extraction_id,
                revision_id=outline.revision_id,
                source_id=outline.source_id,
                title=outline.title,
                asset_hash=revision.get("asset_hash") if revision else None,
                extraction_result_hash=run.get("extraction_result_hash") if run else None,
                selected_unit_ids=[unit.unit_id for unit in units],
                selected_unit_count=len(units),
                cached_inventory_count=cached,
                approx_tokens=source_tokens,
                warnings=warnings,
            )
        )
        for unit in units:
            append_units.append(unit.approx_tokens)
            # Cached inventories don't re-consume input tokens (M4 seam: all False).
            if bool(unit.inventory.get("inventoried")):
                cached_token_pool += unit.approx_tokens
            else:
                unit_tokens.append(unit.approx_tokens)
        global_warnings.extend(warnings)

    stages = _stage_estimates(
        unit_tokens=unit_tokens,
        cached_token_pool=cached_token_pool, append_units=append_units,
        one_facet_per_skill=config.facet_identity.enabled,
        budgets=budgets,
        routing=routing,
        provider_context=provider_context,
    )
    warnings = _dedupe(global_warnings + _provider_warnings(stages, provider, provider_context))

    return BuildPlan(
        routing=routing,
        subject_id=subject_id,
        provider=provider,
        provider_context_tokens=provider_context,
        provider_max_output_tokens=provider_max_output,
        sources=planned,
        stages=stages,
        warnings=warnings,
    )


def _selected_units(units: list[OutlineUnit], requested: list[str]) -> list[OutlineUnit]:
    if not requested:
        return list(units)
    wanted = set(requested)
    return [unit for unit in units if unit.unit_id in wanted]


def _source_warnings(outline, units: list[OutlineUnit]) -> list[str]:
    warnings: list[str] = []
    if outline.difficult_page_count:
        warnings.append(f"{outline.difficult_page_count} difficult page(s) flagged for repair")
    reasons = {reason for unit in units for reason in unit.health_flags}
    for reason in sorted(reasons):
        warnings.append(f"extraction warning: {reason}")
    return warnings


def _stage_estimates(
    *,
    unit_tokens: list[int],
    cached_token_pool: int,
    budgets,
    routing: str,
    provider_context: int | None,
    append_units: list[int] | None = None,
    one_facet_per_skill: bool = False,
) -> list[StageEstimate]:
    active_units = [tokens for tokens in unit_tokens if tokens > 0]
    stages: list[StageEstimate] = []

    # Inventory: one call per not-yet-cached unit.
    inventory_ceiling = budgets.inventory_input_tokens
    inventory_input = sum(min(tokens, inventory_ceiling) for tokens in active_units)
    stages.append(
        StageEstimate(
            stage="inventory",
            calls=len(active_units),
            input_tokens=inventory_input,
            cached_tokens=cached_token_pool,
            # The most a window may write is its ceiling, not the size it is
            # asked for: an answer up to the ceiling is kept and paid.
            max_output_tokens=len(active_units) * max(budgets.inventory_output_tokens,
                                                      budgets.inventory_output_ceiling_tokens),
            ceiling=inventory_ceiling,
            exceeds_ceiling=_exceeds(active_units, inventory_ceiling, provider_context),
        )
    )

    # Synthesis: shard the selected units so no shard exceeds the shard ceiling.
    shards = _shard(active_units, budgets.synthesis_shard_input_tokens)
    shard_inputs = [min(sum(shard), budgets.synthesis_shard_input_tokens) for shard in shards]
    total_input = min(sum(shard_inputs), budgets.synthesis_total_input_ceiling) if shard_inputs else 0
    stages.append(
        StageEstimate(
            stage="synthesis",
            calls=len(shards),
            input_tokens=total_input,
            cached_tokens=0,
            # Every call of a synthesis run (its passes, a span round, the
            # structuring call) is held to what the run's total leaves.
            max_output_tokens=budgets.synthesis_output_tokens if shards else 0,
            ceiling=budgets.synthesis_shard_input_tokens,
            exceeds_ceiling=any(value > budgets.synthesis_shard_input_tokens for value in shard_inputs)
            or _over_context(shard_inputs, provider_context),
        )
    )

    if routing == "update":
        # Before inventory the source sizes are estimates. Cached inventories still participate in reconciliation.
        units = unit_tokens if append_units is None else append_units
        append_ceiling = budgets.append_input_ceiling
        neighborhood = budgets.append_neighborhood_input_tokens
        span_room = budgets.synthesis_span_request_max_count * budgets.synthesis_span_char_cap // 4
        fixed = append_input_tokens(AppendReconciliationContext("", "", "source_added",
                                                                one_facet_per_skill=one_facet_per_skill))
        def base_size(group):
            return fixed + neighborhood + sum(group)

        groups = append_groups(units, budgets, base_size) if units else []
        base = [min(append_ceiling, base_size(group)) for group in groups]
        expanded = [min(append_ceiling, tokens + span_room) for tokens in base] if budgets.synthesis_span_request_max_count else []
        peak = max((*base, *expanded), default=0)
        stages.append(
            StageEstimate(
                stage="append",
                calls=len(base) + len(expanded),
                input_tokens=sum(base) + sum(expanded),
                cached_tokens=0,
                max_output_tokens=(len(base) + len(expanded)) * budgets.append_output_tokens,
                ceiling=append_ceiling,
                exceeds_ceiling=any(base_size([unit]) > append_ceiling for unit in units) or _over_context([peak], provider_context),
                peak_input_tokens=peak,
            )
        )
    return stages


def _shard(unit_tokens: list[int], ceiling: int) -> list[list[int]]:
    shards: list[list[int]] = []
    current: list[int] = []
    running = 0
    for tokens in unit_tokens:
        if current and running + tokens > ceiling:
            shards.append(current)
            current = []
            running = 0
        current.append(tokens)
        running += tokens
    if current:
        shards.append(current)
    return shards


def _exceeds(unit_tokens: list[int], ceiling: int, provider_context: int | None) -> bool:
    for tokens in unit_tokens:
        if tokens > ceiling:
            return True
        if provider_context is not None and min(tokens, ceiling) > provider_context:
            return True
    return False


def _over_context(inputs: list[int], provider_context: int | None) -> bool:
    if provider_context is None:
        return False
    return any(value > provider_context for value in inputs)


def _provider_warnings(stages: list[StageEstimate], provider: str, provider_context: int | None) -> list[str]:
    if provider_context is None:
        # `[ingest.providers.<name>]` is commented out in the default config, so a
        # vault routed at (say) openrouter silently loses every context check
        # below. Say so instead of rendering a plan that looks unconditionally
        # safe — Settings > Token budgets writes this limit.
        return [
            f"no context limit configured for {provider} — context checks are off; "
            "set it under Settings → Token budgets"
        ]
    warnings: list[str] = []
    for stage in stages:
        request_input = stage.input_tokens if stage.peak_input_tokens is None else stage.peak_input_tokens
        if request_input > provider_context:
            warnings.append(
                f"{stage.stage} input {request_input} exceeds {provider} context limit {provider_context}"
            )
    return warnings


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out
