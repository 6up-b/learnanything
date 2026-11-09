---
title: "learnloop_sidecar.phone_reader"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/phone_reader.py"
source_paths:
  - "src/learnloop_sidecar/phone_reader.py"
source_commit: "c61150f982e9b7910573adf87ad5fbce3c77ae6c"
source_commit_timestamp: "2026-11-07T06:50:40-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop_sidecar.phone_reader module"
  - "src/learnloop_sidecar/phone_reader.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.phone_reader`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.phone_reader` exists within [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] to own the behavior summarized by its module contract: Mobile v2 stage V4: the phone Reader's protection (spec_mobile_frontend_v2 §3, §5.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/phone_reader.py](../../../../../src/learnloop_sidecar/phone_reader.py) |
| Source lines | 123 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c61150f982e9b7910573adf87ad5fbce3c77ae6c` |
| Commit timestamp | `2026-11-07T06:50:40-05:00` |

## Public API

- `redact_blocks(blocks: list[dict[str, Any]], withheld: PhoneWithheld) -> list[dict[str, Any]]` ([source](../../../../../src/learnloop_sidecar/phone_reader.py), line 31) — The render payload's blocks with every withheld passage's text, assets and math removed.
- `cold_check_open(ctx: Any, vault: Any, repository: Any) -> bool` ([source](../../../../../src/learnloop_sidecar/phone_reader.py), line 49) — Mobile v2 J8: an Ask during a cold check is refused, and on the phone the server knows it, never the phone's word (§5.2, ``coldActive``).
- `once_per_job(ctx: Any, repository: Any, run: Any) -> Any` ([source](../../../../../src/learnloop_sidecar/phone_reader.py), line 86) — Mobile v2 V4 (Codex review F5): an outbox intent's writes, once, whatever restarts.
- `is_phone(ctx: Any) -> bool` ([source](../../../../../src/learnloop_sidecar/phone_reader.py), line 108)
- `refuse_if_withheld(ctx: Any, vault: Any, repository: Any, extraction_id: str | None, span_ids: Iterable[str | None]=()) -> None` ([source](../../../../../src/learnloop_sidecar/phone_reader.py), line 112) — At a phone origin, refuse a request that names protected material (or a reading that is protected whole).

### Module constants

- `PHONE_READER_SURFACE` ([src/learnloop_sidecar/phone_reader.py](../../../../../src/learnloop_sidecar/phone_reader.py), line 26)
- `HELD_OUT_CODE` ([src/learnloop_sidecar/phone_reader.py](../../../../../src/learnloop_sidecar/phone_reader.py), line 28)
- `COLD_CHECK_CODE` ([src/learnloop_sidecar/phone_reader.py](../../../../../src/learnloop_sidecar/phone_reader.py), line 45)
- `COLD_CHECK_MESSAGE` ([src/learnloop_sidecar/phone_reader.py](../../../../../src/learnloop_sidecar/phone_reader.py), line 46)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]] — imports `once_per_job`; statically calls `once_per_job`
- [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]] — imports `phone_withheld`; statically calls `phone_withheld`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `phone_withheld`; statically calls `phone_withheld`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `phone_withheld`; statically calls `phone_withheld`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `PHONE_READER_SURFACE`, `module`, `once_per_job`, `refuse_if_withheld`; statically calls `cold_check_open`, `once_per_job`, `phone_withheld`, `redact_blocks`, `refuse_if_withheld`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/capture/jobs|learnloop.capture.jobs]] — imports `job_receipt`, `write_job_receipt`; calls `job_receipt`, `write_job_receipt`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `PlanEnv`, `open_randomized_check`; calls `PlanEnv`, `open_randomized_check`
- [[Reference/Modules/learnloop/reader/phone_media|learnloop.reader.phone_media]] — imports `PhoneWithheld`, `phone_withheld`; calls `phone_withheld`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]] — imports `cold_now`; calls `cold_now`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]], [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_ad_guard.py](../../../../../tests/test_ad_guard.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]]
- [tests/test_mobile_allowlist.py](../../../../../tests/test_mobile_allowlist.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]]
- [tests/test_mobile_v4_reader.py](../../../../../tests/test_mobile_v4_reader.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]]
- [tests/test_reader_ca1_as_printed.py](../../../../../tests/test_reader_ca1_as_printed.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]]
- [tests/test_reader_ca1_astra_redesign.py](../../../../../tests/test_reader_ca1_astra_redesign.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]]
- [tests/test_ad23_fix_review.py](../../../../../tests/test_ad23_fix_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]]
- [tests/test_followups_batch6_verify_fixes.py](../../../../../tests/test_followups_batch6_verify_fixes.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]]
- [tests/test_ih3_learner_preferences.py](../../../../../tests/test_ih3_learner_preferences.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]]
- [tests/test_instruct_handoff_ih1.py](../../../../../tests/test_instruct_handoff_ih1.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]]
- [tests/test_learner_pick_proposal.py](../../../../../tests/test_learner_pick_proposal.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]]
- [tests/test_library_exercises.py](../../../../../tests/test_library_exercises.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]]
- [tests/test_mobile_v2_plan.py](../../../../../tests/test_mobile_v2_plan.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/phone_reader.py](../../../../../src/learnloop_sidecar/phone_reader.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
