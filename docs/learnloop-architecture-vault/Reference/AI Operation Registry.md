---
title: AI Operation Registry
aliases:
  - Structured Operation Ledger
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/ai/routing.py
  - tests/test_structured_transport_parity.py
  - src/learnloop/ai/providers/codex_http.py
tags:
  - learnloop/reference
  - learnloop/ai
  - learnloop/providers
---

# AI Operation Registry

This is the current structured-operation ledger. Operation meaning lives in the owner listed below; provider behavior lives in [[AI Architecture]].

## Structured operations

| Operation | Owning implementation | Semantic route |
|---|---|---|
| `authoring_proposal` | `content.proposals.proposals` | authoring |
| `canonical_ingest` | `content.pipeline.source_ingestion` | canonical_ingest |
| `grading_proposal` | `attempts.grading` | grading |
| `tutor_qa` | `tutor.tutor_qa` | tutor_qa |
| `teach_back_question` | `tutor.teach_back` | teach_back |
| `teach_back_authoring` | `tutor.teach_back` | teach_back |
| `misconception_match` | `diagnosis.misconceptions` | grading |
| `promotion_analysis` | `tutor.promotions` | tutor_qa |
| `diagnostic_trials` | `diagnosis.diagnostic_gate` | authoring |
| `grade_diagnostic_fire` | `diagnosis.diagnostic_gate` | grading |
| `probe_instance_surfaces` | `diagnosis.probe_instance_generation` | authoring |
| `probe_dialogue_turn` | `diagnosis.probe_dialogue` | authoring |
| `probe_family_trials` | `diagnosis.probe_instance_generation` | authoring |
| `reader_preset_synthesis` | `reader.reader_requests` | tutor_qa |
| `reading_quick_check` | `reader.reader_quick_check` | tutor_qa |
| `rung_backfill` | `curriculum.rung_backfill` | authoring |
| `exercise_authoring` | `content.authoring.exercise_authoring` | authoring |
| `depth_edge_instances` | `curriculum.depth_edge_authoring` | authoring |
| `source_unit_inventory` | `content.synthesis.source_unit_inventory` | canonical_ingest |
| `source_set_synthesis` | `content.synthesis.source_set_synthesis` | canonical_ingest |
| `concept_graph_structuring` | `content.synthesis.source_set_synthesis` | canonical_ingest |
| `concept_animation` | `content.authoring.concept_animation` | animation |
| `append_reconciliation` | `content.synthesis.source_append` | canonical_ingest |

The parity oracle intentionally has 23 rows. `media_transcription` and `media_markdown` are optional transport capabilities rather than structured feature operations; their routes are transcription and canonical ingest respectively.

## Legacy HTTP subset

The retained endpoint adapter supports exactly these eight capability labels and no others:

`authoring`, `canonical_ingest`, `grading`, `tutor_qa`, `teach_back`, `teach_back_authoring`, `misconception_match`, and `promotion_analysis`.

Unsupported operations raise locally before any HTTP request.

## How to locate a contract

Open the owning implementation in [[Module Catalog]], then follow its feature `ai_contracts` dependency. Context, prompt/version, and result model are colocated in that domain. `tests/test_structured_transport_parity.py` is the executable complete ledger.

## Change checklist

1. Define the operation in the owning feature.
2. Map it to a semantic task route.
3. Add one parity ledger row with representative valid output.
4. Verify SDK and chat transport parity.
5. Decide explicitly whether legacy HTTP supports it; default is unsupported/no egress.
6. Add semantic validation and persistence tests in the owner.

