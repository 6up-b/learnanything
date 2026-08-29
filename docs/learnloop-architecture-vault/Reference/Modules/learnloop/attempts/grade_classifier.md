---
title: "learnloop.attempts.grade_classifier"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/grade_classifier.py"
source_paths:
  - "src/learnloop/attempts/grade_classifier.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.grade_classifier module"
  - "src/learnloop/attempts/grade_classifier.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.grade_classifier`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.grade_classifier` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Deterministic, versioned rich-grade -> observed class G classifier (§3.1, §4.1 step 4), plus the confidence/length bucketing (§3.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/grade_classifier.py](../../../../../../src/learnloop/attempts/grade_classifier.py) |
| Source lines | 173 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `bucket_confidence(value: float | None) -> str` ([source](../../../../../../src/learnloop/attempts/grade_classifier.py), line 36) — Map a raw numeric grader confidence to its bucket (§3.2).
- `exact_word_count(text: str | None) -> int` ([source](../../../../../../src/learnloop/attempts/grade_classifier.py), line 49) — Exact Unicode word count = whitespace-split length over NFC-normalized text (§3.2).
- `length_bucket(word_count: int) -> str` ([source](../../../../../../src/learnloop/attempts/grade_classifier.py), line 59)
- `length_bucket_for_text(text: str | None) -> tuple[int, str]` ([source](../../../../../../src/learnloop/attempts/grade_classifier.py), line 69)
- `class ResponseClassification` ([source](../../../../../../src/learnloop/attempts/grade_classifier.py), line 75)
- `class SchemaShape` ([source](../../../../../../src/learnloop/attempts/grade_classifier.py), line 82) — The subset of an outcome schema the classifier needs.
- `schema_shape_from_row(row: Mapping[str, object]) -> SchemaShape` ([source](../../../../../../src/learnloop/attempts/grade_classifier.py), line 90)
- `classify_response(*, rubric_score: int | None, max_points: int, schema: SchemaShape, has_fatal: bool=False, response_empty: bool=False, signature_matched: bool=False, malformed: bool=False) -> ResponseClassification` ([source](../../../../../../src/learnloop/attempts/grade_classifier.py), line 101) — Map a rich rubric grade to the coarse observed class G (§3.1, §4.1 step 4).
- `classify_criteria(*, criterion_points: Mapping[str, float], criterion_max: Mapping[str, float]) -> dict[str, str]` ([source](../../../../../../src/learnloop/attempts/grade_classifier.py), line 152) — Map each criterion's ``points_awarded / criterion.points`` onto full/partial/none, and unassessable when max is missing/zero (§3.1).

### Module constants

- `RESPONSE_CLASSIFIER_VERSION` ([src/learnloop/attempts/grade_classifier.py](../../../../../../src/learnloop/attempts/grade_classifier.py), line 20)
- `CRITERION_CLASSIFIER_VERSION` ([src/learnloop/attempts/grade_classifier.py](../../../../../../src/learnloop/attempts/grade_classifier.py), line 21)
- `CONFIDENCE_LOW_MAX` ([src/learnloop/attempts/grade_classifier.py](../../../../../../src/learnloop/attempts/grade_classifier.py), line 25)
- `CONFIDENCE_MEDIUM_MAX` ([src/learnloop/attempts/grade_classifier.py](../../../../../../src/learnloop/attempts/grade_classifier.py), line 26)
- `CONFIDENCE_BUCKETS` ([src/learnloop/attempts/grade_classifier.py](../../../../../../src/learnloop/attempts/grade_classifier.py), line 27)
- `LENGTH_BUCKET_SMALL_MAX` ([src/learnloop/attempts/grade_classifier.py](../../../../../../src/learnloop/attempts/grade_classifier.py), line 31)
- `LENGTH_BUCKET_MEDIUM_MAX` ([src/learnloop/attempts/grade_classifier.py](../../../../../../src/learnloop/attempts/grade_classifier.py), line 32)
- `LENGTH_BUCKETS` ([src/learnloop/attempts/grade_classifier.py](../../../../../../src/learnloop/attempts/grade_classifier.py), line 33)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/calibration_streams|learnloop.attempts.calibration_streams]] — imports `bucket_confidence`, `length_bucket_for_text`; statically calls `bucket_confidence`, `length_bucket_for_text`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `CRITERION_CLASSIFIER_VERSION`, `RESPONSE_CLASSIFIER_VERSION`, `bucket_confidence`, `classify_criteria`, `classify_response`, `length_bucket_for_text`, `schema_shape_from_row`; statically calls `bucket_confidence`, `classify_criteria`, `classify_response`, `length_bucket_for_text`, `schema_shape_from_row`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `bucket_confidence`; statically calls `bucket_confidence`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`, `unicodedata`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/calibration_streams|learnloop.attempts.calibration_streams]], [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]], [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_bootstrap_frame_logs_inclusion_probabilities_and_is_deterministic`
  - `test_classifier_maps_score_boundaries`
  - `test_classifier_unanswered_only_when_schema_has_class`
  - `test_classifier_unclassifiable_maps_to_other_plus_flag`
  - `test_confidence_buckets_at_040_and_080`
  - `test_length_buckets`
  - `test_raw_confidence_only_affects_interpretation_through_bucket`

## Modification guidance

- Change grade classifier policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/grade_classifier.py](../../../../../../src/learnloop/attempts/grade_classifier.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
