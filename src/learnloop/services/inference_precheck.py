"""Static cells-converted precheck for measurement inference rules.

Implementation plan item 8.1 applies the measurement spec's §5.8.2 method to
Wave 4 *before* either inference rule is built:

* B1 capability dominance can fill a contract cell when the same facet already
  has an instrument at a strictly higher capability.  Those are exactly the
  reachability report's ``MISMATCH_ABOVE`` rows.
* B3 prerequisite entailment can fill an upstream learning object's contract
  cells only when a downstream learning object has a directly reachable cell
  and the prerequisite relationship is explicitly typed ``hard``.  A
  ``path_specific`` relationship is reported separately because a static pass
  cannot establish that its path was exercised.

This module is deliberately a counterfactual over vault content.  It reads no
attempts, learner state, or provider, writes nothing, and applies no inferred
credit.  Its only job is to answer the go/no-go question: *how many currently
unreachable contract cells could this rule move?*

The B3 fail-closed rule is load-bearing.  Existing concept prerequisite edges
were authored for instructional ordering and predate edge modalities.  Missing
modality is therefore ``untyped``, never an implicit logical entailment.
``instructional_order`` and ``facilitating`` relationships convert zero cells by
construction.  This is the static guard against silently turning a pedagogical
graph into a logical one.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable

from learnloop.services.contract_reachability import (
    CAPABILITY_RANK,
    CONTRACT_MODALITIES,
    CellReachability,
    ContractCell,
    ContractReachabilityReport,
    ReachabilityVerdict,
    analyze_contract_reachability,
    build_instrument_pool,
)
from learnloop.vault.models import ConceptEdge, LoadedVault


class PrerequisiteDisposition(StrEnum):
    """Why one declared prerequisite can or cannot convert upstream cells."""

    CONVERTS = "CONVERTS"
    CONDITIONAL_ON_PATH = "CONDITIONAL_ON_PATH"
    NO_DOWNSTREAM_DIRECT_ANCHOR = "NO_DOWNSTREAM_DIRECT_ANCHOR"
    NO_UPSTREAM_CONTRACT = "NO_UPSTREAM_CONTRACT"
    NO_UPSTREAM_GAP = "NO_UPSTREAM_GAP"
    MISSING_GRAPH_EDGE = "MISSING_GRAPH_EDGE"
    UNTYPED = "UNTYPED"
    INSTRUCTIONAL_ORDER = "INSTRUCTIONAL_ORDER"
    FACILITATING = "FACILITATING"
    INVALID_MODALITY = "INVALID_MODALITY"


@dataclass(frozen=True)
class DominanceConversion:
    """One baseline-unreachable cell B1 could fill downward."""

    cell: ContractCell
    source_capabilities: tuple[str, ...]
    source_instrument_ids: tuple[str, ...]

    @property
    def substitutable_for_certification(self) -> bool:
        # Measurement §5.3: integration is the assembly claim and always needs a
        # direct observation.  Inference may still improve its prediction, so it
        # remains in ``cells_converted`` and is split out in the summary.
        return not self.cell.integration

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.cell.as_dict(),
            "baseline_verdict": str(ReachabilityVerdict.MISMATCH_ABOVE),
            "rule": "capability_dominance",
            "source_capabilities": list(self.source_capabilities),
            "source_instrument_ids": list(self.source_instrument_ids),
            "substitutable_for_certification": self.substitutable_for_certification,
        }


@dataclass(frozen=True)
class EntailmentSource:
    """A typed prerequisite edge plus the direct downstream observation."""

    edge_id: str
    modality: str
    source_concept_id: str
    target_concept_id: str
    upstream_learning_object_id: str
    downstream_learning_object_id: str
    downstream_anchor_cells: tuple[tuple[str, str, str], ...]
    downstream_instrument_ids: tuple[str, ...]

    @property
    def conditional_on_path(self) -> bool:
        return self.modality == "path_specific"

    def as_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "modality": self.modality,
            "source_concept_id": self.source_concept_id,
            "target_concept_id": self.target_concept_id,
            "upstream_learning_object_id": self.upstream_learning_object_id,
            "downstream_learning_object_id": self.downstream_learning_object_id,
            "downstream_anchor_cells": [list(key) for key in self.downstream_anchor_cells],
            "downstream_instrument_ids": list(self.downstream_instrument_ids),
            "conditional_on_path": self.conditional_on_path,
        }


@dataclass(frozen=True)
class EntailmentConversion:
    """One upstream cell B3 could fill from direct downstream evidence."""

    cell: ContractCell
    baseline_verdict: ReachabilityVerdict
    sources: tuple[EntailmentSource, ...]
    conditional_only: bool

    @property
    def substitutable_for_certification(self) -> bool:
        return not self.cell.integration

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.cell.as_dict(),
            "baseline_verdict": str(self.baseline_verdict),
            "rule": "prerequisite_entailment",
            "conditional_only": self.conditional_only,
            "substitutable_for_certification": self.substitutable_for_certification,
            "sources": [source.as_dict() for source in self.sources],
        }


@dataclass(frozen=True)
class PrerequisiteAudit:
    """One LO prerequisite declaration and its static eligibility verdict."""

    downstream_learning_object_id: str
    source_concept_id: str
    target_concept_id: str
    edge_id: str | None
    modality: str
    disposition: PrerequisiteDisposition
    upstream_learning_object_ids: tuple[str, ...]
    downstream_anchor_cell_count: int
    target_gap_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "downstream_learning_object_id": self.downstream_learning_object_id,
            "source_concept_id": self.source_concept_id,
            "target_concept_id": self.target_concept_id,
            "edge_id": self.edge_id,
            "modality": self.modality,
            "disposition": str(self.disposition),
            "upstream_learning_object_ids": list(self.upstream_learning_object_ids),
            "downstream_anchor_cell_count": self.downstream_anchor_cell_count,
            "target_gap_count": self.target_gap_count,
        }


@dataclass(frozen=True)
class InferencePrecheckReport:
    """B1/B3 counterfactual conversion counts over one reachability baseline."""

    baseline: ContractReachabilityReport
    dominance: tuple[DominanceConversion, ...]
    entailment: tuple[EntailmentConversion, ...]
    prerequisite_audit: tuple[PrerequisiteAudit, ...]
    prerequisite_graph_edge_count: int
    prerequisite_graph_edges_unreferenced: int

    @property
    def hard_entailment(self) -> tuple[EntailmentConversion, ...]:
        return tuple(row for row in self.entailment if not row.conditional_only)

    @property
    def conditional_entailment(self) -> tuple[EntailmentConversion, ...]:
        return tuple(row for row in self.entailment if row.conditional_only)

    @staticmethod
    def _keys(rows: Iterable[DominanceConversion | EntailmentConversion]) -> set[tuple[str, str, str]]:
        return {row.cell.key for row in rows}

    @property
    def combined_cells_converted(self) -> int:
        """Guaranteed static union: B1 plus hard-edge B3, without double count."""

        return len(self._keys(self.dominance) | self._keys(self.hard_entailment))

    @property
    def combined_maximum_cells_converted(self) -> int:
        """Union including path-specific candidates if their paths are exercised."""

        return len(self._keys(self.dominance) | self._keys(self.entailment))

    @staticmethod
    def _share(numerator: int, denominator: int) -> float | None:
        return numerator / denominator if denominator else None

    def _rule_summary(
        self,
        rows: tuple[DominanceConversion | EntailmentConversion, ...],
    ) -> dict[str, Any]:
        count = len(rows)
        substitutable = sum(row.substitutable_for_certification for row in rows)
        return {
            "cells_converted": count,
            "moves_count": count > 0,
            "share_of_unreachable": self._share(count, self.baseline.unreachable_count),
            "share_of_all_cells": self._share(count, self.baseline.cell_count),
            "substitutable_cells": substitutable,
            "integration_prediction_only_cells": count - substitutable,
        }

    def summary(self) -> dict[str, Any]:
        disposition_counts = Counter(str(row.disposition) for row in self.prerequisite_audit)
        modality_counts = Counter(row.modality for row in self.prerequisite_audit)
        dominance = self._rule_summary(self.dominance)
        hard_entailment = self._rule_summary(self.hard_entailment)
        conditional = self._rule_summary(self.conditional_entailment)
        maximum_entailment_keys = self._keys(self.entailment)
        hard_keys = self._keys(self.hard_entailment)
        b3_summary = {
            **hard_entailment,
            "conditional_cells": len(maximum_entailment_keys - hard_keys),
            "maximum_cells_converted": len(maximum_entailment_keys),
            "maximum_share_of_unreachable": self._share(
                len(maximum_entailment_keys), self.baseline.unreachable_count
            ),
            "conditional": conditional,
            "prerequisite_declaration_count": len(self.prerequisite_audit),
            "prerequisite_graph_edge_count": self.prerequisite_graph_edge_count,
            "prerequisite_graph_edges_unreferenced": self.prerequisite_graph_edges_unreferenced,
            "modality_counts": dict(sorted(modality_counts.items())),
            "disposition_counts": dict(sorted(disposition_counts.items())),
        }
        return {
            "baseline": self.baseline.summary(),
            "capability_dominance": dominance,
            "prerequisite_entailment": b3_summary,
            "combined": {
                "cells_converted": self.combined_cells_converted,
                "maximum_cells_converted": self.combined_maximum_cells_converted,
                "moves_count": self.combined_cells_converted > 0,
                "share_of_unreachable": self._share(
                    self.combined_cells_converted, self.baseline.unreachable_count
                ),
                "maximum_share_of_unreachable": self._share(
                    self.combined_maximum_cells_converted,
                    self.baseline.unreachable_count,
                ),
            },
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "summary": self.summary(),
            "dominance_cells": [row.as_dict() for row in self.dominance],
            "entailment_cells": [row.as_dict() for row in self.entailment],
            "prerequisite_audit": [row.as_dict() for row in self.prerequisite_audit],
        }


def _edge_modality(edge: ConceptEdge) -> str:
    """Return the explicit edge modality, failing closed when it is absent."""

    raw = getattr(edge, "modality", None)
    if raw is None or not str(raw).strip():
        return "untyped"
    return str(raw)


def _ineligible_disposition(modality: str) -> PrerequisiteDisposition | None:
    if modality == "untyped":
        return PrerequisiteDisposition.UNTYPED
    if modality == "instructional_order":
        return PrerequisiteDisposition.INSTRUCTIONAL_ORDER
    if modality == "facilitating":
        return PrerequisiteDisposition.FACILITATING
    if modality not in CONTRACT_MODALITIES:
        return PrerequisiteDisposition.INVALID_MODALITY
    return None


def _dominance_conversions(
    vault: LoadedVault,
    baseline: ContractReachabilityReport,
) -> tuple[DominanceConversion, ...]:
    pool = build_instrument_pool(vault)
    rows: list[DominanceConversion] = []
    for row in baseline.by_verdict(ReachabilityVerdict.MISMATCH_ABOVE):
        # nearest_above is sufficient to classify the cell, but every higher
        # capability and its instrument travels with the report so the eventual
        # B1 implementation can be priced without reconstructing the pool.
        source_capabilities = tuple(
            capability
            for capability in row.observed_capabilities
            if CAPABILITY_RANK.get(capability, -1)
            > CAPABILITY_RANK.get(row.cell.capability, len(CAPABILITY_RANK))
        )
        rows.append(
            DominanceConversion(
                cell=row.cell,
                source_capabilities=source_capabilities,
                source_instrument_ids=tuple(
                    sorted(
                        {
                            item_id
                            for capability in source_capabilities
                            for item_id in pool.item_ids(row.cell.facet_id, capability)
                        }
                    )
                ),
            )
        )
    return tuple(rows)


def _reachable_by_learning_object(
    baseline: ContractReachabilityReport,
) -> dict[str, tuple[CellReachability, ...]]:
    grouped: dict[str, list[CellReachability]] = defaultdict(list)
    for row in baseline.cells:
        if row.verdict is ReachabilityVerdict.REACHABLE:
            grouped[row.cell.learning_object_id].append(row)
    return {
        learning_object_id: tuple(rows)
        for learning_object_id, rows in sorted(grouped.items())
    }


def _contract_by_learning_object(
    baseline: ContractReachabilityReport,
) -> dict[str, tuple[CellReachability, ...]]:
    grouped: dict[str, list[CellReachability]] = defaultdict(list)
    for row in baseline.cells:
        grouped[row.cell.learning_object_id].append(row)
    return {
        learning_object_id: tuple(rows)
        for learning_object_id, rows in sorted(grouped.items())
    }


def _entailment_conversions(
    vault: LoadedVault,
    baseline: ContractReachabilityReport,
) -> tuple[
    tuple[EntailmentConversion, ...],
    tuple[PrerequisiteAudit, ...],
    int,
    int,
]:
    prerequisite_edges = tuple(
        edge for edge in vault.edges if edge.relation_type == "prerequisite"
    )
    edges_by_pair: dict[tuple[str, str], list[ConceptEdge]] = defaultdict(list)
    for edge in prerequisite_edges:
        edges_by_pair[(edge.source, edge.target)].append(edge)

    learning_objects_by_concept: dict[str, list[str]] = defaultdict(list)
    for learning_object in vault.learning_objects.values():
        learning_objects_by_concept[learning_object.concept].append(learning_object.id)
    for ids in learning_objects_by_concept.values():
        ids.sort()

    reachable_by_lo = _reachable_by_learning_object(baseline)
    contract_by_lo = _contract_by_learning_object(baseline)
    audit: list[PrerequisiteAudit] = []
    hard_sources: dict[tuple[str, str, str], list[EntailmentSource]] = defaultdict(list)
    conditional_sources: dict[tuple[str, str, str], list[EntailmentSource]] = defaultdict(list)
    rows_by_key = {row.cell.key: row for row in baseline.cells}
    referenced_edge_ids: set[str] = set()

    for downstream in sorted(vault.learning_objects.values(), key=lambda lo: lo.id):
        for source_concept_id in sorted(set(downstream.prerequisites)):
            target_concept_id = downstream.concept
            matching_edges = tuple(
                sorted(
                    edges_by_pair.get((source_concept_id, target_concept_id), ()),
                    key=lambda edge: edge.id,
                )
            )
            upstream_ids = tuple(learning_objects_by_concept.get(source_concept_id, ()))
            anchors = reachable_by_lo.get(downstream.id, ())
            anchor_keys = tuple(row.cell.key for row in anchors)
            anchor_instruments = tuple(
                sorted({item_id for row in anchors for item_id in row.matching_instrument_ids})
            )
            target_rows = tuple(
                row
                for upstream_id in upstream_ids
                for row in contract_by_lo.get(upstream_id, ())
            )
            gaps = tuple(
                row for row in target_rows if row.verdict is not ReachabilityVerdict.REACHABLE
            )

            if not matching_edges:
                audit.append(
                    PrerequisiteAudit(
                        downstream_learning_object_id=downstream.id,
                        source_concept_id=source_concept_id,
                        target_concept_id=target_concept_id,
                        edge_id=None,
                        modality="untyped",
                        disposition=PrerequisiteDisposition.MISSING_GRAPH_EDGE,
                        upstream_learning_object_ids=upstream_ids,
                        downstream_anchor_cell_count=len(anchors),
                        target_gap_count=len(gaps),
                    )
                )
                continue

            for edge in matching_edges:
                referenced_edge_ids.add(edge.id)
                modality = _edge_modality(edge)
                disposition = _ineligible_disposition(modality)
                if disposition is None:
                    if not upstream_ids or not target_rows:
                        disposition = PrerequisiteDisposition.NO_UPSTREAM_CONTRACT
                    elif not anchors:
                        disposition = PrerequisiteDisposition.NO_DOWNSTREAM_DIRECT_ANCHOR
                    elif not gaps:
                        disposition = PrerequisiteDisposition.NO_UPSTREAM_GAP
                    elif modality == "path_specific":
                        disposition = PrerequisiteDisposition.CONDITIONAL_ON_PATH
                    else:
                        disposition = PrerequisiteDisposition.CONVERTS
                audit.append(
                    PrerequisiteAudit(
                        downstream_learning_object_id=downstream.id,
                        source_concept_id=source_concept_id,
                        target_concept_id=target_concept_id,
                        edge_id=edge.id,
                        modality=modality,
                        disposition=disposition,
                        upstream_learning_object_ids=upstream_ids,
                        downstream_anchor_cell_count=len(anchors),
                        target_gap_count=len(gaps),
                    )
                )
                if disposition not in {
                    PrerequisiteDisposition.CONVERTS,
                    PrerequisiteDisposition.CONDITIONAL_ON_PATH,
                }:
                    continue
                destination = (
                    conditional_sources
                    if disposition is PrerequisiteDisposition.CONDITIONAL_ON_PATH
                    else hard_sources
                )
                for target in gaps:
                    source = EntailmentSource(
                        edge_id=edge.id,
                        modality=modality,
                        source_concept_id=source_concept_id,
                        target_concept_id=target_concept_id,
                        upstream_learning_object_id=target.cell.learning_object_id,
                        downstream_learning_object_id=downstream.id,
                        downstream_anchor_cells=anchor_keys,
                        downstream_instrument_ids=anchor_instruments,
                    )
                    destination[target.cell.key].append(source)

    conversions: list[EntailmentConversion] = []
    for key in sorted(
        set(hard_sources) | set(conditional_sources),
        key=lambda cell_key: (cell_key[0], cell_key[2], cell_key[1]),
    ):
        hard = hard_sources.get(key, [])
        conditional = conditional_sources.get(key, [])
        sources = tuple(
            sorted(
                [*hard, *conditional],
                key=lambda source: (
                    source.modality,
                    source.edge_id,
                    source.downstream_learning_object_id,
                ),
            )
        )
        baseline_row = rows_by_key[key]
        conversions.append(
            EntailmentConversion(
                cell=baseline_row.cell,
                baseline_verdict=baseline_row.verdict,
                sources=sources,
                conditional_only=not hard,
            )
        )

    return (
        tuple(conversions),
        tuple(
            sorted(
                audit,
                key=lambda row: (
                    row.downstream_learning_object_id,
                    row.source_concept_id,
                    row.edge_id or "",
                ),
            )
        ),
        len(prerequisite_edges),
        len(prerequisite_edges) - len(referenced_edge_ids),
    )


def analyze_inference_precheck(
    vault: LoadedVault,
    *,
    reachability: ContractReachabilityReport | None = None,
) -> InferencePrecheckReport:
    """Price B1 and B3 against the current static contract-cell baseline.

    ``reachability`` is injectable so callers already rendering §5.8.2 can reuse
    the exact same snapshot.  Supplying it changes no semantics.
    """

    baseline = reachability or analyze_contract_reachability(vault)
    entailment, audit, graph_edges, unreferenced = _entailment_conversions(
        vault, baseline
    )
    return InferencePrecheckReport(
        baseline=baseline,
        dominance=_dominance_conversions(vault, baseline),
        entailment=entailment,
        prerequisite_audit=audit,
        prerequisite_graph_edge_count=graph_edges,
        prerequisite_graph_edges_unreferenced=unreferenced,
    )
