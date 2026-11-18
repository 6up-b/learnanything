"""Figure source identifiers and input manifests.

These pure readers keep text_gaps.sources out of text_gaps.provenance.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any

#: Reader RW5a: a figure prediction's id (``figure_predictions``). It shares
#: the ``reader_formative`` source kind with RW1b's answers, told apart by
#: this prefix (the figure service writes it).
FIGURE_PREDICTION_PREFIX = "fpr_"


#: A missed prediction's "what changed?" written after the prediction's own
#: reading started: its own text, ``<prediction id>`` + this suffix, read
#: with the answer; the earlier reading is kept (Codex review F5).
FIGURE_EXPLANATION_SUFFIX = ":explained"


def figure_prediction_id(source_id: str) -> tuple[str, bool]:
    """``(prediction id, whether the source is its later explanation)``."""

    source_id = str(source_id or "")
    if source_id.endswith(FIGURE_EXPLANATION_SUFFIX):
        return source_id[: -len(FIGURE_EXPLANATION_SUFFIX)], True
    return source_id, False


def figure_input_manifest(row: Mapping[str, Any]) -> list[str] | None:
    """Every span a figure was built from and its author was sent, or None
    when the stored lists are unreadable (a caller fails closed): the
    selection, the region's block, the crop's block and ``input_span_ids``
    (the paragraphs around it). The figure service rechecks the same list
    (``figures.service._figure_spans``; Codex review F1)."""

    try:
        spans = [str(span) for span in json.loads(row.get("span_ids_json") or "[]")]
        region = json.loads(row.get("region_json") or "null") or {}
        manifest = json.loads(row.get("input_span_ids_json") or "[]")
        if not isinstance(region, dict) or not isinstance(manifest, list):
            return None
        if region.get("span_id"):
            spans.append(str(region["span_id"]))
        if row.get("asset_id"):
            spans.append(str(row["asset_id"]))
        spans += [str(span) for span in manifest]
    except (TypeError, ValueError):
        return None
    return list(dict.fromkeys(spans))


def figure_input_keys(row: Mapping[str, Any]) -> dict[str, list[str]] | None:
    """Reader RW5d: the retrieved passages a figure was built from, in any
    source (``input_span_keys_json``), by extraction; None when unreadable
    (a caller fails closed)."""

    try:
        keys = json.loads(row.get("input_span_keys_json") or "[]")
        if not isinstance(keys, list):
            return None
        grouped: dict[str, list[str]] = {}
        for key in keys:
            if not isinstance(key, list) or len(key) != 2:
                return None
            grouped.setdefault(str(key[0]), []).append(str(key[1]))
    except (TypeError, ValueError):
        return None
    return grouped
