---
title: "learnloop.attempts.hint_fold"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/hint_fold.py"
source_paths:
  - "src/learnloop/attempts/hint_fold.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.attempts.hint_fold module"
  - "src/learnloop/attempts/hint_fold.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.hint_fold`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.hint_fold` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Adaptive hints H2a: the submit's fold of shown server hints, taken again at commit (spec §5, G-H2, G-H3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/hint_fold.py](../../../../../../src/learnloop/attempts/hint_fold.py) |
| Source lines | 401 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `held_components(parts: Any) -> tuple[tuple[str, ...], bool, int]` ([source](../../../../../../src/learnloop/attempts/hint_fold.py), line 60) — The open problems' help as components: the UNION of their server assist ids, whether any counted the book, and the largest carried count.
- `combine_held(client_hints: int, parts: Any, *, authored_hints: int | None=None, union: Any=None, book: bool | None=None, carried: int | None=None, client_book: bool=False) -> int` ([source](../../../../../../src/learnloop/attempts/hint_fold.py), line 69) — The submit's count from the client's and the open problems' help (RW2b fix round 10, one rule).
- `class ServerHintFold` ([source](../../../../../../src/learnloop/attempts/hint_fold.py), line 110) — One submit's fold of its shown server hints, and the rule it applied.
  - `base(self) -> int` (line 200; public)
  - `hints_used(self, folded: int | None=None) -> int` (line 211; public)
  - `primed(self, folded_primed: bool | None=None) -> bool` (line 218; public)
  - `attempt_type(self, current: str, folded: int | None=None) -> str` (line 222; public)
- `fold_follows_attach(vault: Any) -> bool` ([source](../../../../../../src/learnloop/attempts/hint_fold.py), line 230) — Whether a keyed fold counts the key's rows in any practice session and its attempt takes them in its own transaction (follow-ups Nov 2; Codex review F1: it changes ``hints_used`` and ``primed`` of new attempts, so it is the successor ``HELP_FOLD_ATTACH_ALGORITHM_VERSION`` with t…
- `read_fold(connection: Any, *, practice_item_id: str, session_id: str, submission_id: str | None, any_session: bool=False) -> tuple[int, bool, str | None]` ([source](../../../../../../src/learnloop/attempts/hint_fold.py), line 246) — The fold over the rows shown now, and a keyless submit's window start (a vault without ``help_assists`` folds nothing).
- `refolded_draft(connection: Any, draft: Any) -> tuple[Any, ServerHintFold | None]` ([source](../../../../../../src/learnloop/attempts/hint_fold.py), line 267) — ``draft`` as its submit would have built it from the fold read on ``connection`` (the attempt's write transaction), and the new fold when it differs from the one read before grading; ``(draft, None)`` when nothing changed or the draft carries no fold.
- `attach_held(connection: Any, draft: Any, attempt_id: str) -> int` ([source](../../../../../../src/learnloop/attempts/hint_fold.py), line 341) — RW2b fix round 13: the attempt takes the workbench server assists it counted (its fold's union, as the refold left it), in its own write transaction, so no later attempt counts them again.
- `attach_keyless(connection: Any, draft: Any, attempt_id: str) -> int` ([source](../../../../../../src/learnloop/attempts/hint_fold.py), line 359) — A keyless submit's attempt takes the rows its fold counted (round 3b), in its own write transaction after the attempt row exists: the window :func:`refolded_draft` read under the same lock.
- `attach_keyed(connection: Any, draft: Any, attempt_id: str) -> int` ([source](../../../../../../src/learnloop/attempts/hint_fold.py), line 377) — A keyed submit's attempt takes the rows its fold counted (follow-ups Nov 2), in its own write transaction, as :func:`attach_keyless` does for a keyless one: the submission's rows of the item in any practice session (a hint shown before the session rolled over included), through…

### Explicit exports

`__all__` declares:

- `HeldPart`
- `ServerHintFold`
- `attach_held`
- `attach_keyed`
- `attach_keyless`
- `combine_held`
- `fold_follows_attach`
- `held_components`
- `read_fold`
- `refolded_draft`

## Internal implementation anchors

- `_part(part: Any) -> HeldPart` ([source](../../../../../../src/learnloop/attempts/hint_fold.py), line 49) — A part as ``(book, carried, ids)`` (a two-number part from before round 5 reads as ``(0, carried, n anonymous ids)``).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `ServerHintFold`, `attach_held`, `attach_keyed`, `attach_keyless`, `refolded_draft`; statically calls `attach_held`, `attach_keyed`, `attach_keyless`, `refolded_draft`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `ServerHintFold`, `combine_held`, `fold_follows_attach`, `held_components`, `read_fold`; statically calls `ServerHintFold`, `combine_held`, `fold_follows_attach`, `held_components`, `read_fold`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `HELP_FOLD_ATTACH_VERSIONS`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `stuck_attempt_type`; calls `stuck_attempt_type`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `attach_keyed_fold`, `attach_keyless_fold`, `attach_workbench_rows`, `keyless_window_start`, `server_fold`, `unattached_ids`; calls `attach_keyed_fold`, `attach_keyless_fold`, `attach_workbench_rows`, `keyless_window_start`, `server_fold`, `unattached_ids`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followups_nov2_help_fold.py](../../../../../../tests/test_followups_nov2_help_fold.py) — direct import
  - `test_the_keyless_window_still_reads_its_own_session_only`
- [tests/test_help_fold_attach_successor.py](../../../../../../tests/test_help_fold_attach_successor.py) — direct import
  - `test_the_fold_is_gated_by_the_tag_and_the_switch`
- [tests/test_hint_h2a_review_round2.py](../../../../../../tests/test_hint_h2a_review_round2.py) — direct import
  - `test_v1_the_fold_rule_is_the_submits_own`
- [tests/test_hint_h2a_review_round3.py](../../../../../../tests/test_hint_h2a_review_round3.py) — direct import
  - `test_w1_the_fence_and_the_keyless_fold_share_one_window`
- [tests/test_reader_rw2b_fix12.py](../../../../../../tests/test_reader_rw2b_fix12.py) — direct import
  - `test_item1_the_refold_keeps_one_when_the_last_problem_closed_during_grading`

## Modification guidance

- Change hint fold policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/hint_fold.py](../../../../../../src/learnloop/attempts/hint_fold.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
