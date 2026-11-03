"""Builders for Reader RW5c's tests: a book whose blocks hold LaTeX, and small figure specs (no network, no model)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.vault.writer import upsert_source_set
from tests.figure_fixtures import seed_probability_book
from tests.source_service_fakes import build_textbook_vault, set_config
from tests.test_source_inventory import _persist

EXTRACTION = "ext_math"
FLAGSHIP_TEX = (r"f(x) = \begin{cases} p \lambda e^{\lambda x} & x < 0 \\ (1-p)\lambda e^{-\lambda x} & x \ge 0 \end{cases}")
FLAGSHIP_EXPR = "piecewise((x < 0, p*lambda*exp(lambda*x)), (1 - p)*lambda*exp(-lambda*x))"
HALF_EXPR = "piecewise((x < 0, 0.5*p*lambda*exp(lambda*x)), (1 - p)*lambda*exp(-lambda*x))"
PARAMETERS = [{"name": "p", "label": "mixing weight", "min": 0.125, "max": 0.875, "step": 0.125, "default": 0.5},
              {"name": "lambda", "label": "rate", "min": 0.5, "max": 2.0, "step": 0.25, "default": 1.0}]


def set_switch(paths: Any, enabled: bool) -> None:
    """``figures.checked_labels_enabled`` set again and again (``set_config`` appends once per key)."""

    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    value = "true" if enabled else "false"
    if "checked_labels_enabled" in text:
        config.write_text(re.sub(r"checked_labels_enabled = \w+", f"checked_labels_enabled = {value}", text), encoding="utf-8")
    else:
        set_config(paths, "figures", checked_labels_enabled=enabled)


def seed_math_book(repository: Any, blocks: list[tuple[str, str, str]], *, extraction: str = EXTRACTION,
                   source: str = "src_math", revision: str = "rev_math", geometry: bool = True) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, current_revision_id, "
            "reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (source, "pdf", f"file:///{source}.pdf", "A book with equations", revision, 1,
             "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            (revision, source, f"sha256:{source}", None, "2026-01-01T00:00:00Z"))
        connection.commit()
    built = []
    for ordinal, (span, block_type, text) in enumerate(blocks, start=1):
        built.append(DocumentBlock.build(
            span_id=span, block_type=block_type, text=text, ordinal=ordinal, page=87 if geometry else None,
            bbox=[72.0, 40.0 * ordinal, 540.0, 40.0 * ordinal + 30] if geometry else None,
            section_path=["/page/87/SectionHeader/1"], extractor_block_id=f"/page/87/{block_type}/{ordinal}"))
    unit = DocumentUnit(unit_id=f"u_{source}", label="5.4 Equations", ordinal=0, semantic_hash=f"sha256:{source}",
                        page_start=87, page_end=87, span_ids=[span for span, *_ in blocks])
    ir = DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=built, assets=[],
                    health=ExtractionHealth())
    _persist(repository, ir, revision_id=revision, extraction_id=extraction)


def build_check_vault(root: Path, blocks: list[tuple[str, str, str]], *, extra_members: tuple[dict[str, str], ...] = (),
                      **seed: Any) -> tuple[Any, Any]:
    paths, repository, _spans = build_textbook_vault(root)
    set_config(paths, "figures", sketch_enabled=False, rich_tiers_enabled=False)
    seed_probability_book(repository)
    seed_math_book(repository, blocks, **seed)
    upsert_source_set(paths.root, {
        "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
        "members": [
            {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
            {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
            {"source_id": "src_text", "revision_id": "rev_text", "default_role": "primary_textbook"},
            {"source_id": "src_prob", "revision_id": "rev_prob", "default_role": "primary_textbook"},
            {"source_id": seed.get("source", "src_math"), "revision_id": seed.get("revision", "rev_math"),
             "default_role": "primary_textbook"},
            *extra_members,
        ],
    })
    return paths, repository


def plot(expr: str, *, name: str = "f", parameters: list[dict[str, Any]] | None = None, low: float = 0.0,
         high: float = 1.0, variable: str = "x", kind: str = "reconstructed", label: str = "the book's curve",
         stated: str | None = None, span: str = "s1", definitions: list[dict[str, str]] | None = None,
         shades: list[dict[str, str]] | None = None, invariants: list[dict[str, Any]] | None = None,
         **changes: Any) -> dict[str, Any]:
    """A one-panel figure drawing ``name`` by bare reference. ``stated``: its quote and ``equals_source``."""

    spec: dict[str, Any] = {
        "spec_version": "ifs-v1", "kind": kind, "demonstrates": "how the curve moves",
        "parameters": parameters or [], "definitions": definitions or [{"name": name, "expr": expr}],
        "panels": [{"kind": "function_plot", "x": {"var": variable, "min": low, "max": high},
                    "series": [{"expr": name, "label": label}], **({"shade": shades} if shades else {})}],
        "invariants": list(invariants or []),
    }
    if stated is not None:
        spec["source_claims"] = [{"span_id": span, "quote": stated}]
        spec["invariants"] = [*spec["invariants"], {"kind": "equals_source", "name": name}]
    spec.update(changes)
    return spec


__all__ = ["EXTRACTION", "FLAGSHIP_EXPR", "FLAGSHIP_TEX", "HALF_EXPR", "PARAMETERS", "build_check_vault", "plot",
           "seed_math_book", "set_switch"]
