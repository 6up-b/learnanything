---
title: "learnloop_sidecar.dto"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/dto.py"
source_paths:
  - "src/learnloop_sidecar/dto.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.dto module"
  - "src/learnloop_sidecar/dto.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.dto`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps dto behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]]. Its public surface centers on `camel_name`, `ParamsModel`, `EmptyParams`, `to_camel`, `versioned`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/dto.py](../../../../../src/learnloop_sidecar/dto.py) |
| Source lines | 43 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `camel_name(name: str) -> str` ([source](../../../../../src/learnloop_sidecar/dto.py), line 9)
- `class ParamsModel(BaseModel)` ([source](../../../../../src/learnloop_sidecar/dto.py), line 14)
- `class EmptyParams(ParamsModel)` ([source](../../../../../src/learnloop_sidecar/dto.py), line 22)
- `to_camel(value: Any) -> Any` ([source](../../../../../src/learnloop_sidecar/dto.py), line 26)
- `versioned(payload: Mapping[str, Any] | None=None, *, version: int=1) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/dto.py), line 38)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] — imports `EmptyParams`, `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]] — imports `EmptyParams`, `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/claims|learnloop_sidecar.handlers.claims]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/cli|learnloop_sidecar.handlers.cli]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/compare_scope|learnloop_sidecar.handlers.compare_scope]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `ParamsModel`, `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnosis_card|learnloop_sidecar.handlers.diagnosis_card]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `EmptyParams`, `ParamsModel`, `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_identity|learnloop_sidecar.handlers.facet_identity]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/facets|learnloop_sidecar.handlers.facets]] — imports `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `ParamsModel`, `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `EmptyParams`, `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/followup|learnloop_sidecar.handlers.followup]] — imports `ParamsModel`, `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `EmptyParams`, `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/graph|learnloop_sidecar.handlers.graph]] — imports `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/graph_edit|learnloop_sidecar.handlers.graph_edit]] — imports `ParamsModel`, `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `ParamsModel`, `camel_name`, `versioned`; statically calls `camel_name`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]] — imports `ParamsModel`, `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/intent|learnloop_sidecar.handlers.intent]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/learner_gaps|learnloop_sidecar.handlers.learner_gaps]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/library|learnloop_sidecar.handlers.library]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `ParamsModel`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `EmptyParams`, `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/placement|learnloop_sidecar.handlers.placement]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `ParamsModel`, `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/provenance|learnloop_sidecar.handlers.provenance]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/reading_paths|learnloop_sidecar.handlers.reading_paths]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/recap|learnloop_sidecar.handlers.recap]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/registry|learnloop_sidecar.handlers.registry]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/review|learnloop_sidecar.handlers.review]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/router_objective|learnloop_sidecar.handlers.router_objective]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `EmptyParams`, `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `EmptyParams`, `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/side_by_side|learnloop_sidecar.handlers.side_by_side]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/sqlite_admin|learnloop_sidecar.handlers.sqlite_admin]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `EmptyParams`, `ParamsModel`, `versioned`; statically calls `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/why|learnloop_sidecar.handlers.why]] — imports `ParamsModel`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `ParamsModel`, `to_camel`; statically calls `to_camel`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `ParamsModel`, `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `ParamsModel`, `to_camel`, `versioned`; statically calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `EmptyParams`, `ParamsModel`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `to_camel`; statically calls `to_camel`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]], [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]], [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]], [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] and 69 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/plan_first_transport_offer_grants_helpers.py](../../../../../tests/plan_first_transport_offer_grants_helpers.py) — direct import
- [tests/sketch_parity_corpus.py](../../../../../tests/sketch_parity_corpus.py) — direct import
- [tests/test_capture_desktop.py](../../../../../tests/test_capture_desktop.py) — direct import
  - `test_summary_listing_banner_dismiss_purge_and_cli`
- [tests/test_chatgpt_plan_sidecar.py](../../../../../tests/test_chatgpt_plan_sidecar.py) — direct import
  - `test_cancel_and_failure_are_reported`
  - `test_resume_clears_a_pause`
  - `test_settings_payload_lists_plan_profiles_and_their_routes`
  - `test_sign_in_from_the_desktop_without_a_vault`
- [tests/test_followup_fg1d_panel_read.py](../../../../../tests/test_followup_fg1d_panel_read.py) — direct import
- [tests/test_ingest_latency_journey.py](../../../../../tests/test_ingest_latency_journey.py) — direct import
  - `test_synthetic_markdown_import_reaches_ready_library_and_outline`
- [tests/test_mobile_v4_reader.py](../../../../../tests/test_mobile_v4_reader.py) — direct import
  - `test_render_view_without_a_range_is_todays_reply_byte_for_byte`
- [tests/test_plan_first_transport.py](../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_f8_an_error_that_is_not_a_sidecar_error_keeps_the_offer`
  - `test_rr_f3_the_plan_status_lists_the_sessions_grants_for_a_lasting_stop`
  - `test_the_sidecar_attaches_the_typed_hint_and_ai_use_fallback_records_the_choice`
- [tests/test_provenance.py](../../../../../tests/test_provenance.py) — direct import
- [tests/test_reader_ca5_also_in_books.py](../../../../../tests/test_reader_ca5_also_in_books.py) — direct import
- [tests/test_reader_intent.py](../../../../../tests/test_reader_intent.py) — direct import
  - `test_switched_off_the_prompt_contract_is_the_bases`
- [tests/test_reader_intentions.py](../../../../../tests/test_reader_intentions.py) — direct import
  - `test_the_readers_test_fixture_is_the_sidecars_palette`
- [tests/test_sidecar_item_presentation.py](../../../../../tests/test_sidecar_item_presentation.py) — direct import
- [tests/test_sidecar_serializer_snapshot.py](../../../../../tests/test_sidecar_serializer_snapshot.py) — direct import
  - `test_queue_practice_and_reader_wire_snapshots`
- [tests/test_sidecar_transport.py](../../../../../tests/test_sidecar_transport.py) — direct import
  - `test_duplicate_method_registration_fails_loudly`
  - `test_unexpected_handler_failure_marks_the_commit_outcome_unknown`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/dto.py](../../../../../src/learnloop_sidecar/dto.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
