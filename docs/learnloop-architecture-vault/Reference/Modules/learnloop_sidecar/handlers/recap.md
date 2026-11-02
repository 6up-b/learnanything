---
title: "learnloop_sidecar.handlers.recap"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/recap.py"
source_paths:
  - "src/learnloop_sidecar/handlers/recap.py"
source_commit: "5ba84e102d5fe35da6fba74894ee503f47e206b9"
source_commit_timestamp: "2026-11-01T01:10:34-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
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
  - "learnloop_sidecar.handlers.recap module"
  - "src/learnloop_sidecar/handlers/recap.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.recap`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.recap` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench RW6a: "Last time here" and Wrap up (spec_reader_workbench_v1 §9.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/recap.py](../../../../../../src/learnloop_sidecar/handlers/recap.py) |
| Source lines | 168 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5ba84e102d5fe35da6fba74894ee503f47e206b9` |
| Commit timestamp | `2026-11-01T01:10:34-05:00` |

## Public API

- `class ReaderRecapInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/recap.py), line 64)
- `reader_recap(ctx: SidecarContext, params: ReaderRecapInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/recap.py), line 72) — The "Last time here" card for a source, or ``recap: null`` (first visit, within the first session, or dismissed this session).
- `class ReaderRecapEventInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/recap.py), line 109)
- `reader_recap_event(ctx: SidecarContext, params: ReaderRecapEventInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/recap.py), line 116) — Record that the card was shown or dismissed, or that Wrap up was opened.
- `class ReaderWrapUpInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/recap.py), line 132)
- `reader_wrap_up(ctx: SidecarContext, params: ReaderWrapUpInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/recap.py), line 140) — The session's resolved, still open and worth reinforcing lists, each line with the action the same chip takes elsewhere.
- `class ReaderWrapUpOfferInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/recap.py), line 158)
- `reader_wrap_up_offer(ctx: SidecarContext, params: ReaderWrapUpOfferInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/recap.py), line 163) — Whether the place the learner lands offers Wrap up: the most recent reader session had activity and was not wrapped up.

## Internal implementation anchors

- `_now() -> datetime` ([source](../../../../../../src/learnloop_sidecar/handlers/recap.py), line 37)
- `_require(ctx: SidecarContext, *, wrap_up: bool)` ([source](../../../../../../src/learnloop_sidecar/handlers/recap.py), line 41)
- `_extraction(repository, extraction_id: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/recap.py), line 57)
- `_narrative(ctx: SidecarContext, vault, repository, extraction_id: str, session: Any, now: datetime)` ([source](../../../../../../src/learnloop_sidecar/handlers/recap.py), line 88) — RW6b part 2's narrative for the session the card or Wrap up is about (spec §9.2; W14's states), or None: absent with ``digest.narrative_enabled`` off (part 1's payload exactly), and for a session still running.
- `_coming_up(vault, repository, extraction_id: str, now: datetime) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/recap.py), line 100) — RW6b's "Coming up" (spec §9.1, §9.3; UX S15, D36): the source's scheduled checks as a dated timeline.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `module`; calls `narrative_enabled`, `narrative_view`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `module`; calls `coming_up`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `inquiry_enabled`, `reader_enabled`
- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `module`; calls `build_recap`, `build_wrap_up`, `recap_enabled`, `record_recap_event`, `wrap_up_enabled`, `wrap_up_offer`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/reading_path_fixtures.py](../../../../../../tests/reading_path_fixtures.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/recap_fixtures.py](../../../../../../tests/recap_fixtures.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2b_fix10_base_sequence.py](../../../../../../tests/rw2b_fix10_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2b_fix11_base_sequence.py](../../../../../../tests/rw2b_fix11_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2c_base_sequence.py](../../../../../../tests/rw2c_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2c_state_parity.py](../../../../../../tests/rw2c_state_parity.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad1_attempt_columns.py](../../../../../../tests/test_ad1_attempt_columns.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_intent_compose.py](../../../../../../tests/test_ad23_intent_compose.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_successor.py](../../../../../../tests/test_ad23_successor.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/recap.py](../../../../../../src/learnloop_sidecar/handlers/recap.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
