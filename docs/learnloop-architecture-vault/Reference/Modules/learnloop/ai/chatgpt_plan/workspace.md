---
title: "learnloop.ai.chatgpt_plan.workspace"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/chatgpt_plan/workspace.py"
source_paths:
  - "src/learnloop/ai/chatgpt_plan/workspace.py"
source_commit: "42ab0bc90d513d76d7b0eea692d52330b51a8385"
source_commit_timestamp: "2026-10-23T10:49:09-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai.chatgpt_plan"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.chatgpt_plan.workspace module"
  - "src/learnloop/ai/chatgpt_plan/workspace.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-chatgpt-plan"
---

# `learnloop.ai.chatgpt_plan.workspace`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.chatgpt_plan.workspace` exists within [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] to own the behavior summarized by its module contract: A read-only workspace that LearnLoop serves to a ``chatgpt_plan`` turn.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/chatgpt_plan/workspace.py](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py) |
| Source lines | 397 |
| Owning package | [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `42ab0bc90d513d76d7b0eea692d52330b51a8385` |
| Commit timestamp | `2026-10-23T10:49:09-04:00` |

## Public API

- `class WorkspaceTooLarge(ValueError)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py), line 64) — The workspace does not fit the inline budget (``max_workspace_chars``).
- `class ServedEntry` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py), line 69) — One file (or a line range of it) LearnLoop handed to the model.
  - `as_dict(self) -> dict[str, Any]` (line 81; public)
- `class CallRecord` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py), line 86) — Every workspace call, served or refused, in order (for the receipt).
  - `as_dict(self) -> dict[str, Any]` (line 97; public)
- `normalize_path(value: Any) -> str | None` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py), line 116) — A requested path as an index key, or None when it can name nothing in the workspace.
- `class ServedWorkspace` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py), line 134) — The index of one prepared directory and the record of what was served from it.
  - `__init__(self, root: Path, *, max_entry_chars: int, max_workspace_chars: int) -> None` (line 137; internal)
  - `namespace_tool() -> dict[str, Any]` (line 156; public) — The one tool the request declares: a namespace of two strict functions.
  - `inline_block(self) -> str` (line 215; public) — Every file, for ``workspace_mode = "inline"``; each recorded as served.
  - `call(self, name: str, arguments: str, *, call_id: str | None, round_index: int) -> str` (line 238; public) — Run one function call; returns its output text.
  - `refuse(self, name: str, arguments: str, *, call_id: str | None, round_index: int, reason: str) -> str` (line 258; public) — Answer a call without running it (serves nothing); the refusal is recorded.
  - `refuse_exhausted(self, name: str, arguments: str, *, call_id: str | None, round_index: int) -> str` (line 263; public) — The answer to a call made after the tool-round budget is spent (serves nothing).
  - `_list(self, arguments: Mapping[str, Any], raw: str, *, call_id: str | None, round_index: int) -> str` (line 270; internal)
  - `_read(self, arguments: Mapping[str, Any], raw: str, *, call_id: str | None, round_index: int) -> str` (line 301; internal)
  - `_refuse(self, round_index: int, call_id: str | None, name: str, raw: Any, reason: str) -> str` (line 348; internal)
  - `_text(self, path: str) -> str` (line 353; internal)
  - `_record_served(self, path: str, text: str, first: int, last: int, total: int, chars: int, *, call_id: str | None, round_index: int) -> None` (line 360; internal)
  - `activity(self) -> list[str]` (line 370; public) — Every served file's path, once each, in the order first served.
  - `summary(self) -> dict[str, Any]` (line 375; public)

### Module constants

- `NAMESPACE` ([src/learnloop/ai/chatgpt_plan/workspace.py](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py), line 41)
- `LIST_ENTRIES` ([src/learnloop/ai/chatgpt_plan/workspace.py](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py), line 42)
- `READ_ENTRY` ([src/learnloop/ai/chatgpt_plan/workspace.py](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py), line 43)
- `FUNCTIONS` ([src/learnloop/ai/chatgpt_plan/workspace.py](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py), line 44)
- `LIST_LIMIT` ([src/learnloop/ai/chatgpt_plan/workspace.py](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py), line 46)
- `INSTRUCTIONS_TOOLS` ([src/learnloop/ai/chatgpt_plan/workspace.py](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py), line 48)
- `INSTRUCTIONS_INLINE` ([src/learnloop/ai/chatgpt_plan/workspace.py](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py), line 56)

### Explicit exports

`__all__` declares:

- `CallRecord`
- `FUNCTIONS`
- `INSTRUCTIONS_INLINE`
- `INSTRUCTIONS_TOOLS`
- `LIST_ENTRIES`
- `NAMESPACE`
- `READ_ENTRY`
- `ServedEntry`
- `ServedWorkspace`
- `WorkspaceTooLarge`
- `normalize_path`

## Internal implementation anchors

- `_relative_files(root: Path) -> dict[str, Path]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py), line 101) — Every regular file under ``root`` (no symlink is followed or served), by POSIX path.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `INSTRUCTIONS_INLINE`, `INSTRUCTIONS_TOOLS`, `NAMESPACE`, `ServedWorkspace`, `WorkspaceTooLarge`; statically calls `ServedWorkspace`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `INSTRUCTIONS_INLINE`, `ServedWorkspace`, `WorkspaceTooLarge`; statically calls `ServedWorkspace`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `os`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]], [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_chatgpt_plan_workspace.py](../../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
  - `test_echo_items_keep_only_what_store_false_can_resend`
  - `test_inline_mode_sends_every_file_and_records_every_file`
  - `test_inline_mode_serves_a_workspace_over_its_budget_in_tools_mode`
  - `test_the_workspace_character_budget_and_the_listing_are_bounded`
  - `test_the_workspace_never_reaches_outside_its_root`
  - `test_tool_rounds_serve_files_and_record_each_served_entry`
- [tests/test_codex_lockdown_round3.py](../../../../../../../tests/test_codex_lockdown_round3.py) — direct import
  - `test_a_snapshot_diagnosis_on_codex_is_inlined_and_gives_the_same_structured_output`
- [tests/test_plan_first_transport.py](../../../../../../../tests/test_plan_first_transport.py) — direct import

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/chatgpt_plan/workspace.py](../../../../../../../src/learnloop/ai/chatgpt_plan/workspace.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
