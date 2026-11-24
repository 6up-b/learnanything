---
title: "learnloop_sidecar.handlers.inline_checks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/inline_checks.py"
source_paths:
  - "src/learnloop_sidecar/handlers/inline_checks.py"
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
  - "learnloop_sidecar.handlers.inline_checks module"
  - "src/learnloop_sidecar/handlers/inline_checks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.inline_checks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.inline_checks` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench v2 RPCs for checks where the learner reads (spec §3.4, §12.6; mvp-0.69).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/inline_checks.py](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py) |
| Source lines | 282 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class ChecksDueForInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 34)
- `checks_due_for_handler(ctx: SidecarContext, params: ChecksDueForInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 42) — ``{checks: [{commitment_id, lo_id, due, host?, provenance, being_answered}]}``.
- `class VisibleFigure(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 51)
- `class VisibleWindow(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 56)
- `class VisibleSearchRow(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 68)
- `class Visible(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 76) — What is on screen, on every desk: the windows (with what each shows), the companion, overview previews and search results.
- `class BeginInlineInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 87)
- `class TokenInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 95)
- `class ProtectMoreInput(TokenInput)` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 99)
- `class ExposeInput(TokenInput)` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 103)
- `class SubmitInlineInput(TokenInput)` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 109)
- `check_begin_inline(ctx: SidecarContext, params: BeginInlineInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 166) — Open an inline administration; the prompt is in the reply only once the veils are recorded.
- `check_protect_more(ctx: SidecarContext, params: ProtectMoreInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 181) — Veil what came into view during the administration: ``{veil_additions}``.
- `check_expose(ctx: SidecarContext, params: ExposeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 194) — Record an exposure at once: ``{protection_status: {exposure, cold_now}}``.
- `check_submit_inline(ctx: SidecarContext, params: SubmitInlineInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 208) — The attempt through the one attempt service for the frozen item and contract, then settlement: the attempt's own reply plus ``{cold, reason}``.
- `check_abandon_inline(ctx: SidecarContext, params: TokenInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 243) — "Not now": closed with no attempt; the duty stays pending.
- `class OpenInlineInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 254)
- `check_open_inline(ctx: SidecarContext, params: OpenInlineInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 259) — The restart read: the open administration with its veils and prompt, or ``administration: null``.

### Module constants

- `INLINE_CHECK_RPCS` ([src/learnloop_sidecar/handlers/inline_checks.py](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 30)

### Explicit exports

`__all__` declares:

- `INLINE_CHECK_RPCS`

## Internal implementation anchors

- `_covered(vault: Any, repository: Any) -> IA.Covered` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 116) — The sections that treat the check's LOs (judged coverage about them, as the goal lens reads it), or None when coverage cannot be read (every visible source passage is then veiled).
- `_error(exc: IA.InlineCheckError) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 137)
- `_card(admin: dict[str, Any], served: dict[str, Any] | None, veils: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 141)
- `_serve(ctx: SidecarContext, session_id: str)` ([source](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py), line 153)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `stuck_attempt_type`; calls `stuck_attempt_type`
- [[Reference/Modules/learnloop/intent/inline_administration|learnloop.intent.inline_administration]] — imports `module`; calls `abandon`, `attempt_submission_key`, `begin`, `expose`, `finish_submit`, `outcome`, `prepare_submit`, `protect_more`, `reopen`, `veils`
- [[Reference/Modules/learnloop/intent/inline_checks|learnloop.intent.inline_checks]] — imports `due_checks`; calls `due_checks`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; calls `Library`, `standing`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `Verbatim`, `versioned`; calls `Verbatim`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `ServePracticeItemInput`, `SubmitAttemptInput`, `get_practice_item`, `submit_attempt_on`; calls `ServePracticeItemInput`, `SubmitAttemptInput`, `get_practice_item`, `submit_attempt_on`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `practice_item_detail`; calls `practice_item_detail`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`
- [[Reference/Modules/learnloop_sidecar/request_origin|learnloop_sidecar.request_origin]] — imports `host_mutation`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

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

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rd0_rpcs_are_all_of_them`
  - `test_the_pinned_rd7_rpcs_are_all_of_them`
- [tests/test_reader_rd0_rpcs.py](../../../../../../tests/test_reader_rd0_rpcs.py) — direct import
  - `test_the_rpcs_are_registered_and_desktop_only`
- [tests/test_reader_rd7a_inline_checks.py](../../../../../../tests/test_reader_rd7a_inline_checks.py) — direct import
  - `test_the_rpcs_are_registered_desktop_only_and_refuse_extra_fields`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/inline_checks.py](../../../../../../src/learnloop_sidecar/handlers/inline_checks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
