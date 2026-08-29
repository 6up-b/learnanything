"""Deterministic exam profile aggregation (spec_source_ingestion_v2 §7, §4.2).

A pure function over exam-unit inventories → aggregate task-family / capability /
representation / format counts + point/time emphasis (the 1k–3k-token profile M6
synthesis consumes). The load-bearing correlation discipline (§4.2): near-duplicate
papers from the **same syllabus family** collapse into ONE assessment-alignment
vote rather than counting as independent evidence of emphasis — the same rule the
knowledge model applies to correlated surfaces. The family key is derived
deterministically from paper metadata (administration syllabus/version), so two
years of the same syllabus vote once per shared task family.

No LLM here, no learner state, no semantic authority — assessment alignment only.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

_WS = re.compile(r"\s+")

# Sentinel family for a paper carrying no syllabus/family/paper_id/year metadata;
# aggregate_exam_profile disambiguates these per unit so unrelated unkeyed papers
# never accidentally collapse (§4.2).
_UNKEYED_FAMILY = "paper:__unkeyed__"


def _norm(text: Any) -> str:
    return _WS.sub(" ", str(text or "").strip().lower())


def exam_family_key(metadata: Mapping[str, Any] | None) -> str:
    """Deterministic same-syllabus-family key (§4.2 near-duplicate collapse).

    Papers sharing a syllabus/version belong to one family regardless of
    administration year, so successive years vote once. Falls back to an explicit
    ``family``/``paper_id`` field, else a per-paper singleton so unrelated papers
    never accidentally collapse."""

    metadata = metadata or {}
    for key in ("family", "syllabus_family"):
        value = _norm(metadata.get(key))
        if value:
            return f"fam:{value}"
    syllabus = _norm(metadata.get("syllabus"))
    version = _norm(metadata.get("syllabus_version") or metadata.get("version"))
    if syllabus:
        return f"syl:{syllabus}|{version}" if version else f"syl:{syllabus}"
    # No family metadata: each paper is its own family (no accidental collapse).
    singleton = _norm(metadata.get("paper_id")) or _norm(metadata.get("year"))
    return f"paper:{singleton}" if singleton else _UNKEYED_FAMILY


@dataclass
class ExamProfile:
    task_families: dict[str, int] = field(default_factory=dict)
    capabilities: dict[str, int] = field(default_factory=dict)
    representations: dict[str, int] = field(default_factory=dict)
    response_formats: dict[str, int] = field(default_factory=dict)
    point_time_emphasis: dict[str, int] = field(default_factory=dict)
    held_out_task_families: dict[str, int] = field(default_factory=dict)
    family_count: int = 0
    families: list[dict[str, Any]] = field(default_factory=list)
    item_count: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_families": self.task_families,
            "capabilities": self.capabilities,
            "representations": self.representations,
            "response_formats": self.response_formats,
            "point_time_emphasis": self.point_time_emphasis,
            "held_out_task_families": self.held_out_task_families,
            "family_count": self.family_count,
            "families": self.families,
            "item_count": self.item_count,
        }


@dataclass(frozen=True)
class ExamUnitEntry:
    """One selected exam unit: its inventory plus its paper metadata."""

    unit_id: str
    inventory: Mapping[str, Any]
    paper_metadata: Mapping[str, Any] = field(default_factory=dict)


def aggregate_exam_profile(entries: Sequence[ExamUnitEntry]) -> ExamProfile:
    """Aggregate exam-unit inventories into a deterministic profile (§7).

    Each syllabus family contributes ONE vote for each distinct
    (task_family / capability / representation / format) it exhibits — near-
    duplicate papers cannot inflate emphasis. Counts are votes over families,
    NOT raw item counts."""

    families: dict[str, dict[str, set[str]]] = {}
    family_meta: dict[str, dict[str, Any]] = {}
    item_count = 0

    for entry in sorted(entries, key=lambda item: item.unit_id):
        family = exam_family_key(entry.paper_metadata)
        if family == _UNKEYED_FAMILY:
            # Deterministically keep unkeyed papers separate by unit id.
            family = f"paper:unit:{entry.unit_id}"
        buckets = families.setdefault(
            family,
            {
                "task_families": set(),
                "capabilities": set(),
                "representations": set(),
                "response_formats": set(),
                "point_time_emphasis": set(),
                "held_out_task_families": set(),
            },
        )
        meta = family_meta.setdefault(family, {"family": family, "papers": set(), "unit_ids": []})
        year = _norm(entry.paper_metadata.get("year"))
        if year:
            meta["papers"].add(year)
        meta["unit_ids"].append(entry.unit_id)
        for signal in entry.inventory.get("assessment_signals", []):
            item_count += 1
            task_family = _norm(signal.get("task_family"))
            if task_family:
                buckets["task_families"].add(task_family)
                if signal.get("held_out"):
                    buckets["held_out_task_families"].add(task_family)
            for capability in signal.get("capability_demands", []):
                capability = _norm(capability)
                if capability:
                    buckets["capabilities"].add(capability)
            representation = _norm(signal.get("representation"))
            if representation:
                buckets["representations"].add(representation)
            response_format = _norm(signal.get("response_format"))
            if response_format:
                buckets["response_formats"].add(response_format)
            emphasis = _norm(signal.get("point_or_time_emphasis"))
            if emphasis:
                buckets["point_time_emphasis"].add(emphasis)

    profile = ExamProfile(item_count=item_count, family_count=len(families))
    task_counter: Counter[str] = Counter()
    capability_counter: Counter[str] = Counter()
    representation_counter: Counter[str] = Counter()
    format_counter: Counter[str] = Counter()
    emphasis_counter: Counter[str] = Counter()
    held_out_counter: Counter[str] = Counter()

    for family in sorted(families):
        buckets = families[family]
        task_counter.update(buckets["task_families"])
        capability_counter.update(buckets["capabilities"])
        representation_counter.update(buckets["representations"])
        format_counter.update(buckets["response_formats"])
        emphasis_counter.update(buckets["point_time_emphasis"])
        held_out_counter.update(buckets["held_out_task_families"])
        meta = family_meta[family]
        profile.families.append(
            {
                "family": family,
                "papers": sorted(meta["papers"]),
                "unit_ids": sorted(meta["unit_ids"]),
                "task_families": sorted(buckets["task_families"]),
            }
        )

    profile.task_families = dict(sorted(task_counter.items()))
    profile.capabilities = dict(sorted(capability_counter.items()))
    profile.representations = dict(sorted(representation_counter.items()))
    profile.response_formats = dict(sorted(format_counter.items()))
    profile.point_time_emphasis = dict(sorted(emphasis_counter.items()))
    profile.held_out_task_families = dict(sorted(held_out_counter.items()))
    return profile


def profile_hash(profile: ExamProfile) -> str:
    """Deterministic hash of the profile content for cache identity."""

    import json

    payload = json.dumps(profile.as_dict(), sort_keys=True, ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
