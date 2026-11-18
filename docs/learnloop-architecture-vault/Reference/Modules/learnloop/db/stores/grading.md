---
title: "learnloop.db.stores.grading"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/grading.py"
source_paths:
  - "src/learnloop/db/stores/grading.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.db.stores.grading module"
  - "src/learnloop/db/stores/grading.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.grading`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.grading` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Grading contracts, observations and adjudication ledgers.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/grading.py](../../../../../../../src/learnloop/db/stores/grading.py) |
| Source lines | 663 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class GradingStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/grading.py), line 34)
  - `insert_observation_template(self, template: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 36; public)
  - `observation_templates(self, *, active_only: bool=False) -> list[dict[str, Any]]` (line 63; public)
  - `fetch_observation_template(self, template_id: str) -> dict[str, Any] | None` (line 72; public)
  - `insert_observation_event(self, event: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 80; public)
  - `observation_events(self) -> list[dict[str, Any]]` (line 110; public)
  - `ensure_outcome_schema_version(self, *, schema_id: str, version: int, observed_classes_json: str, true_classes_json: str, has_signature_error: bool, has_unanswered: bool, score_fraction_json: str, content_hash: str, clock: Clock | None=None) -> str` (line 117; public)
  - `fetch_outcome_schema_version(self, *, slug: str, version: int | None=None) -> dict[str, Any] | None` (line 163; public)
  - `fetch_outcome_schema_version_by_id(self, schema_id: str, version: int) -> dict[str, Any] | None` (line 188; public)
  - `find_calibration_model_by_hash(self, content_hash: str) -> dict[str, Any] | None` (line 196; public)
  - `calibration_models_by_hashes(self, content_hashes: Iterable[str]) -> dict[str, dict[str, Any]]` (line 204; public) — Bulk calibration-model lookup for a whole projection replay.
  - `fetch_calibration_alphas(self, model_id: str) -> dict[str, dict[str, float]]` (line 223; public)
  - `calibration_alphas_by_model_ids(self, model_ids: Iterable[str]) -> dict[str, dict[str, dict[str, float]]]` (line 231; public) — Bulk Dirichlet rows keyed by model id, preserving empty models.
  - `find_calibration_models(self, *, scope_level: str | None=None, grader_identity_hash: Any=_UNSET, outcome_schema_id: Any=_UNSET, outcome_schema_version: Any=_UNSET, domain: Any=_UNSET, length_bucket: Any=_UNSET, status: str | None=None) -> list[dict[str, Any]]` (line 259; public)
  - `insert_raw_grade_event(self, *, values: Mapping[str, Any], clock: Clock | None=None) -> str` (line 301; public)
  - `raw_grade_events_for_observation(self, observation_id: str) -> list[dict[str, Any]]` (line 349; public)
  - `latest_raw_grade_identity(self, attempt_id: str) -> tuple[str | None, str | None] | None` (line 357; public) — (prompt, output schema) calibration identity of the attempt's newest primary raw grade.
  - `raw_grade_event(self, event_id: str) -> dict[str, Any] | None` (line 368; public)
  - `raw_grade_events_by_ids(self, event_ids: Iterable[str]) -> dict[str, dict[str, Any]]` (line 375; public) — Bulk raw-grade lookup for legacy certainty-LCB reconstruction.
  - `insert_grade_interpretation(self, *, values: Mapping[str, Any], clock: Clock | None=None) -> str` (line 391; public)
  - `grade_interpretation(self, interpretation_id: str) -> dict[str, Any] | None` (line 437; public)
  - `grade_interpretations_for_observation(self, observation_id: str) -> list[dict[str, Any]]` (line 444; public)
  - `insert_grade_adjudication(self, *, values: Mapping[str, Any], clock: Clock | None=None) -> str` (line 452; public)
  - `insert_calibration_stream_sample(self, *, values: Mapping[str, Any], clock: Clock | None=None) -> str` (line 484; public)
  - `calibration_stream_samples(self, *, stream: str | None=None, sampling_frame_id: str | None=None) -> list[dict[str, Any]]` (line 513; public)
  - `insert_discrimination_profile_match(self, *, attempt_id: str, practice_item_id: str, outcome: str, attempt_failed: bool, profile_id: str | None=None, misconception_id: str | None=None, evidence: str | None=None, grading_prompt_version: str | None=None, agent_run_id: str | None=None, id: str | None=None, clock: Clock | None=None) -> str | None` (line 541; public) — Record A5's per-attempt profile judgement; ``None`` when one exists.
  - `discrimination_profile_match(self, attempt_id: str) -> dict[str, Any] | None` (line 591; public)
  - `insert_diagnostic_augmentation_receipt(self, values: Mapping[str, Any], *, clock: Clock | None=None) -> str | None` (line 599; public) — Append Phase-C provenance; idempotent for one live attempt.
  - `diagnostic_augmentation_receipt_for_attempt(self, attempt_id: str) -> dict[str, Any] | None` (line 642; public) — The Phase-C receipt for one graded attempt, or None.

## Internal implementation anchors

- `_decode_diagnostic_augmentation_receipt(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/grading.py), line 16)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `GradingStoreMixin`
- [[Reference/Modules/learnloop/db/stores/learner_model|learnloop.db.stores.learner_model]] — imports `_decode_diagnostic_augmentation_receipt`; statically calls `_decode_diagnostic_augmentation_receipt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/records|learnloop.db.records]] — imports `_UNSET`, `_decode_observation_event`, `_decode_observation_template`; calls `_decode_observation_event`, `_decode_observation_template`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/db/stores/learner_model|learnloop.db.stores.learner_model]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad1_codex_rereview_fixes_helpers.py](../../../../../../../tests/ad1_codex_rereview_fixes_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad1_reading_opportunities_helpers.py](../../../../../../../tests/ad1_reading_opportunities_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_fakes.py](../../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_fix_r8_helpers.py](../../../../../../../tests/ad23_fix_r8_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad2_serving_helpers.py](../../../../../../../tests/ad2_serving_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad_ingest_fakes.py](../../../../../../../tests/ad_ingest_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad_projection_helpers.py](../../../../../../../tests/ad_projection_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/apply_write_ahead_helpers.py](../../../../../../../tests/apply_write_ahead_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/approach_map_fakes.py](../../../../../../../tests/approach_map_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/assumed_known_helpers.py](../../../../../../../tests/assumed_known_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/canonical_facet_helpers.py](../../../../../../../tests/canonical_facet_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/grading.py](../../../../../../../src/learnloop/db/stores/grading.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
