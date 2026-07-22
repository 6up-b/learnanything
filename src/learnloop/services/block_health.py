"""Per-block extraction health (spec_p3_reader_integration §3.4, design B step 2).

The IR carries only per-page ``PageHealth`` today. This module derives per-block
health as an additive, versioned artifact (persisted to ``source_block_health``)
by folding the block's page-health inputs with block geometry/text-density/OCR
heuristics. It deliberately does NOT infer equation/figure safety from a page-wide
flag alone (§2 ledger). Rows begin ``unknown`` until analyzed (§13.1.2) and unknown
is never treated as healthy (§16).

``recommended_view`` drives the reader's four §3.4 behaviors: derived /
crop_adjacent / crop_default / warn_link.
"""

from __future__ import annotations

from typing import Any

from learnloop.ingest.ir import DocumentBlock, PageHealth

ANALYZER_VERSION = "block-health-v1"

# Decision parameters (registered in parameter_registry §E).
EQUATION_LOW_CONFIDENCE_THRESHOLD = 0.55
TEXT_DENSITY_ANOMALY_THRESHOLD = 0.02
OCR_ANOMALY_THRESHOLD = 0.10

# Reason flags (§3.4).
REASON_FLAGS = (
    "equation_low_confidence",
    "figure_missing_or_misaligned",
    "reading_order_suspect",
    "ocr_character_anomaly",
    "table_structure_lost",
    "text_density_anomaly",
    "geometry_missing",
    "manual_flag",
)

# Map page-health flags onto the block-level reason vocabulary.
_PAGE_FLAG_MAP = {
    "reading_order_suspect": "reading_order_suspect",
    "ocr": "ocr_character_anomaly",
    "ocr_low_confidence": "ocr_character_anomaly",
    "table_structure_lost": "table_structure_lost",
    "figures_missing": "figure_missing_or_misaligned",
}


def _ocr_anomaly_fraction(text: str) -> float:
    if not text:
        return 0.0
    bad = sum(1 for ch in text if ch == "�" or (ord(ch) < 32 and ch not in "\n\t\r"))
    return bad / len(text)


def _text_density(block: DocumentBlock) -> float | None:
    if not block.bbox or len(block.bbox) != 4:
        return None
    x0, y0, x1, y1 = block.bbox
    area = abs((x1 - x0) * (y1 - y0))
    if area <= 0:
        return None
    return len(block.text) / area


def analyze_block_health(
    block: DocumentBlock,
    page_health: PageHealth | None,
    *,
    equation_confidence: float | None = None,
    analyzer_version: str = ANALYZER_VERSION,
) -> dict[str, Any]:
    """Compute per-block health from a block + its page health. Returns a dict
    ready for ``repository.upsert_block_health`` (minus extraction_id)."""

    flags: list[str] = []
    provenance: dict[str, Any] = {"analyzer_version": analyzer_version}

    has_geometry = block.page is not None and bool(block.bbox)
    if not has_geometry:
        flags.append("geometry_missing")

    ocr_fraction = _ocr_anomaly_fraction(block.text)
    provenance["ocr_anomaly_fraction"] = round(ocr_fraction, 4)
    if ocr_fraction > OCR_ANOMALY_THRESHOLD:
        flags.append("ocr_character_anomaly")

    density = _text_density(block)
    if density is not None:
        provenance["text_density"] = round(density, 5)
        if 0 < density < TEXT_DENSITY_ANOMALY_THRESHOLD and len(block.text) < 8:
            flags.append("text_density_anomaly")

    block_kind = (block.block_type or "").lower()
    if block_kind in {"equation", "formula", "math"}:
        conf = equation_confidence
        provenance["equation_confidence"] = conf
        if conf is not None and conf < EQUATION_LOW_CONFIDENCE_THRESHOLD:
            flags.append("equation_low_confidence")

    page_flags: list[str] = list(page_health.flags) if page_health is not None else []
    for pflag in page_flags:
        mapped = _PAGE_FLAG_MAP.get(pflag)
        # A page-wide flag is only applied to a block whose type it can plausibly
        # affect -- never blanket-marking every block on a flagged page (§2 ledger).
        if mapped == "table_structure_lost" and block_kind not in {"table"}:
            continue
        if mapped == "figure_missing_or_misaligned" and block_kind not in {"figure", "image", "picture"}:
            continue
        if mapped and mapped not in flags:
            flags.append(mapped)

    # De-dup while preserving order.
    flags = list(dict.fromkeys(flags))

    if any(f in {"ocr_character_anomaly", "table_structure_lost"} for f in flags) and ocr_fraction > OCR_ANOMALY_THRESHOLD:
        status = "failed"
    elif flags:
        status = "suspect"
    else:
        status = "ok"

    confidence = 1.0 - min(1.0, ocr_fraction + 0.2 * len([f for f in flags if f != "geometry_missing"]))

    return {
        "span_id": block.span_id,
        "analyzer_version": analyzer_version,
        "status": status,
        "reason_flags": flags,
        "signal_provenance": provenance,
        "confidence": round(confidence, 4),
        "page_health_flags": page_flags,
        "recommended_view": recommended_view(status, has_geometry, flags),
    }


def recommended_view(status: str, has_geometry: bool, flags: list[str]) -> str:
    """§3.4 four behaviors."""

    if not has_geometry or "geometry_missing" in flags:
        return "warn_link"
    if status == "failed":
        return "crop_default"
    if status == "suspect":
        return "crop_adjacent"
    return "derived"
