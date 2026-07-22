"""Deterministic, versioned rich-grade -> observed class G classifier (§3.1, §4.1
step 4), plus the confidence/length bucketing (§3.2).

Pure + deterministic + snapshotted: the classifier version is pinned on the raw
grade event and echoed on the administration so selection and update never resolve
different classes. Unclassifiable output maps to ``other`` PLUS a review flag; it
never silently maps to success/failure (§3.1). Changing a threshold mints a ``_v2``
version and forces a card successor rather than a retroactive re-classification.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Mapping

# Versioned classifier contracts (§3, §10 param 9). Structural version pins, not
# tunable knobs, but registered so a bump is auditable and triggers the
# card-successor rule.
RESPONSE_CLASSIFIER_VERSION = "grade_classifier_response_v1"
CRITERION_CLASSIFIER_VERSION = "grade_classifier_criterion_v1"

# Confidence-bucket boundaries (§3.2). Registered heuristic decision parameters;
# boundaries at 0.40 and 0.80.
CONFIDENCE_LOW_MAX = 0.40  # decision parameter: heuristic
CONFIDENCE_MEDIUM_MAX = 0.80  # decision parameter: heuristic
CONFIDENCE_BUCKETS = ("unknown", "low", "medium", "high")

# Response-length bucket boundaries in Unicode words (§3.2). Registered heuristic
# decision parameters. Buckets: 0, 1-50, 51-200, 201+.
LENGTH_BUCKET_SMALL_MAX = 50  # decision parameter: heuristic
LENGTH_BUCKET_MEDIUM_MAX = 200  # decision parameter: heuristic
LENGTH_BUCKETS = ("0", "1-50", "51-200", "201+")


def bucket_confidence(value: float | None) -> str:
    """Map a raw numeric grader confidence to its bucket (§3.2). The raw number is
    stored but only this bucket may affect interpretation (§9.1)."""

    if value is None:
        return "unknown"
    if value < CONFIDENCE_LOW_MAX:
        return "low"
    if value < CONFIDENCE_MEDIUM_MAX:
        return "medium"
    return "high"


def exact_word_count(text: str | None) -> int:
    """Exact Unicode word count = whitespace-split length over NFC-normalized text
    (§3.2). Stable definition so calibration residuals are reproducible."""

    if not text:
        return 0
    normalized = unicodedata.normalize("NFC", text)
    return len(normalized.split())


def length_bucket(word_count: int) -> str:
    if word_count <= 0:
        return "0"
    if word_count <= LENGTH_BUCKET_SMALL_MAX:
        return "1-50"
    if word_count <= LENGTH_BUCKET_MEDIUM_MAX:
        return "51-200"
    return "201+"


def length_bucket_for_text(text: str | None) -> tuple[int, str]:
    count = exact_word_count(text)
    return count, length_bucket(count)


@dataclass(frozen=True)
class ResponseClassification:
    observed_class: str  # G
    unclassifiable: bool
    version: str = RESPONSE_CLASSIFIER_VERSION


@dataclass(frozen=True)
class SchemaShape:
    """The subset of an outcome schema the classifier needs."""

    observed_classes: tuple[str, ...]
    has_signature_error: bool = False
    has_unanswered: bool = False


def schema_shape_from_row(row: Mapping[str, object]) -> SchemaShape:
    import json

    observed = tuple(json.loads(row["observed_classes_json"]))
    return SchemaShape(
        observed_classes=observed,
        has_signature_error=bool(row.get("has_signature_error")),
        has_unanswered=bool(row.get("has_unanswered")),
    )


def classify_response(
    *,
    rubric_score: int | None,
    max_points: int,
    schema: SchemaShape,
    has_fatal: bool = False,
    response_empty: bool = False,
    signature_matched: bool = False,
    malformed: bool = False,
) -> ResponseClassification:
    """Map a rich rubric grade to the coarse observed class G (§3.1, §4.1 step 4).

    - ``success`` when ``rubric_score == max_points`` and no fatal error;
    - ``partial_success`` (or the schema's ``signature_error`` slot when it has
      one and a card-declared misconception matched) when
      ``0 < rubric_score < max_points``;
    - ``other`` when ``rubric_score == 0`` OR the output is malformed/unmappable;
    - ``unanswered`` when the response is empty AND the schema has that class;
    - unclassifiable output -> ``other`` PLUS a review flag (never silent
      success/failure).
    """

    if malformed or rubric_score is None:
        return ResponseClassification("other", unclassifiable=True)

    if response_empty and schema.has_unanswered and rubric_score == 0:
        return ResponseClassification("unanswered", unclassifiable=False)

    capped_max = max(int(max_points), 1)
    score = int(rubric_score)

    if score >= capped_max and not has_fatal:
        klass = "success"
    elif score <= 0:
        klass = "other"
    else:
        if schema.has_signature_error and signature_matched:
            klass = "signature_error"
        elif schema.has_signature_error:
            # A partial that is not the declared misconception has no partial slot
            # in a signature-error schema; it is not the recognized error class.
            klass = "other"
        else:
            klass = "partial_success"

    if klass not in schema.observed_classes:
        # The mapped class is not representable in this schema: unclassifiable.
        return ResponseClassification("other", unclassifiable=True)
    return ResponseClassification(klass, unclassifiable=False)


def classify_criteria(
    *,
    criterion_points: Mapping[str, float],
    criterion_max: Mapping[str, float],
) -> dict[str, str]:
    """Map each criterion's ``points_awarded / criterion.points`` onto
    full/partial/none, and unassessable when max is missing/zero (§3.1)."""

    result: dict[str, str] = {}
    for cid, max_pts in criterion_max.items():
        awarded = criterion_points.get(cid)
        if max_pts is None or float(max_pts) <= 0 or awarded is None:
            result[cid] = "unassessable"
            continue
        fraction = float(awarded) / float(max_pts)
        if fraction >= 1.0:
            result[cid] = "full"
        elif fraction <= 0.0:
            result[cid] = "none"
        else:
            result[cid] = "partial"
    return result
