"""What other test files use from ``tests/test_source_append.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.content.synthesis.ai_contracts import (
    AppendProvenanceLink,
    AppendReconciliation,
    SynthSpanRef,
    VaultEpigraph,
    VaultEpigraphBatch,
)
from learnloop.content.synthesis.source_set_synthesis import create_study_map
from learnloop.content.synthesis.source_unit_inventory import run_unit_inventory
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_source_set
from learnloop.content.synthesis.ai_contracts import (
    InventoryClaim,
    InventoryConceptMention,
    SourceUnitInventory,
)

from tests.structured_ai import StructuredClientFake
from tests.source_inventory_helpers import _block, _ir, _persist, _register_revision
from tests.source_set_synthesis_helpers import FakeSynthesisClient, _setup


_CLOCK = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))


class SymmetryInventoryClient(StructuredClientFake):
    """Inventory double that mentions the SAME concept as the bootstrap map, so the
    appended source lands in the affected neighborhood."""

    model = "fake-model-1"
    provider_type = "codex"

    def __init__(self):
        self.calls: list[object] = []

    def run_source_unit_inventory(self, context):
        self.calls.append(context)
        spans = [b["span_id"] for b in context.unit_view["blocks"]] or ["s_missing"]
        return SourceUnitInventory(
            unit_id=context.unit_id,
            semantic_hash=context.semantic_hash,
            outline_summary="symmetric matrices",
            concept_mentions=[InventoryConceptMention(name="symmetric matrix", aliases=["symmetric"], span_ids=spans[:1])],
            claims=[
                InventoryClaim(
                    kind="definition",
                    statement="A real square matrix is symmetric exactly when A^T = A.",
                    preconditions=["the matrix is real and square"],
                    span_ids=spans,
                )
            ],
        )


def _first_new_span(context):
    for entry in context.new_inventories:
        inv = entry["inventory"]
        for claim in inv.get("claims", []) or []:
            spans = claim.get("span_ids") or []
            if spans:
                return entry["extraction_id"], entry["unit_id"], spans[0]
        for m in inv.get("concept_mentions", []) or []:
            spans = m.get("span_ids") or []
            if spans:
                return entry["extraction_id"], entry["unit_id"], spans[0]
    return "", "", ""


def _neighborhood_facet_id(context):
    facets = context.neighborhood.get("facets") or []
    return facets[0]["id"] if facets else ""


class FakeAppendClient(StructuredClientFake):
    """House fake-client for append: builds provenance_link / conflict / notation
    items against the bounded neighborhood + a span cited from the new inventories."""

    provider_name = "codex"
    provider_type = "codex"
    model = "fake-append-1"

    def __init__(self, *, builder=None, epigraph_builder=None):
        self.calls: list[object] = []
        self.epigraph_calls: list[object] = []
        self.builder = builder
        self.epigraph_builder = epigraph_builder

    def run_append_reconciliation(self, context) -> AppendReconciliation:
        self.calls.append(context)
        if self.builder is not None:
            return self.builder(context, len(self.calls))
        return _default_append(context)

    def run_vault_epigraphs(self, context):
        self.epigraph_calls.append(context)
        if self.epigraph_builder is not None:
            return self.epigraph_builder(context, len(self.epigraph_calls))
        # Distinct from the bootstrap fake's lines: the service dedupes a
        # batch against the subject's recent rows, so a repeat persists nothing.
        return VaultEpigraphBatch(
            epigraphs=[
                VaultEpigraph(kind="quote", lines=["A second source, the same transpose."]),
                VaultEpigraph(kind="haiku", lines=["again, symmetric", "another voice says A T", "equals A, still true"]),
                VaultEpigraph(kind="quote", lines=["Escape will make me corroborated."]),
            ]
        )


def _default_append(context) -> AppendReconciliation:
    ext, unit, span = _first_new_span(context)
    target = _neighborhood_facet_id(context)
    span_ref = SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span, relation="support")
    links = []
    if target and span:
        links.append(
            AppendProvenanceLink(
                client_item_id="plink_alt",
                reconciliation_intent="alternate_explanation",
                target_entity_type="facet",
                target_entity_id=target,
                relation="alternate",
                span=span_ref,
            )
        )
    return AppendReconciliation(summary="append alternate explanation", provenance_links=links)


def _add_member_source(repo, root, *, source_id, revision_id, extraction_id, unit_id, role, claim_text):
    inv_client = SymmetryInventoryClient()
    _register_revision(repo, source_id=source_id, revision_id=revision_id)
    ir = _ir([(unit_id, "Symmetric matrices, again",
               [_block("s1", claim_text)], f"sha256:{unit_id}", 3)])
    _persist(repo, ir, revision_id=revision_id, extraction_id=extraction_id)
    run_unit_inventory(repo, extraction_id, unit_id, role=role, profile="combined",
                       client=inv_client, input_budget_tokens=20000, clock=_CLOCK)
    return {"source_id": source_id, "revision_id": revision_id, "default_role": role,
            "scope": [{"unit_id": unit_id}], "priority": 1}


def _bootstrap_and_add(tmp_path, *, add_role="alternate_explanation"):
    """Bootstrap+apply a map, then add a second explanatory member to the set."""

    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"depth": "intro"})
    member = _add_member_source(
        repo, root, source_id="src_alt", revision_id="rev_alt", extraction_id="ext_alt",
        unit_id="chapter_symmetry_alt", role=add_role,
        claim_text="A real square matrix with A^T = A is called symmetric.",
    )
    vault = load_vault(root)
    members = [
        {"source_id": m.source_id, "revision_id": m.revision_id, "default_role": m.default_role,
         "scope": [{"unit_id": s.unit_id} for s in m.scope], "priority": m.priority}
        for m in next(s for s in vault.source_sets if s.id == "set_la").members
    ]
    members.append(member)
    upsert_source_set(root, {"id": "set_la", "subject_id": "linear-algebra",
                             "title": "Linear Algebra", "members": members}, clock=_CLOCK)
    return root, repo
