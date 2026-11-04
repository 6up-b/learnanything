---
title: "learnloop.followup_serve.marks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_serve/marks.py"
source_paths:
  - "src/learnloop/followup_serve/marks.py"
source_commit: "workspace/uncommitted @ HEAD 450c22470d46f9bd13a2faf2d4fb955ba0dad985"
source_commit_timestamp: "2026-11-04T10:02:56-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.followup_serve"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.followup_serve.marks module"
  - "src/learnloop/followup_serve/marks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-serve"
---

# `learnloop.followup_serve.marks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_serve.marks` exists within [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] to own the behavior summarized by its module contract: The learner's marks on possible causes: the pure parts and the receipts (spec §7).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_serve/marks.py](../../../../../../src/learnloop/followup_serve/marks.py) |
| Source lines | 132 |
| Owning package | [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 450c22470d46f9bd13a2faf2d4fb955ba0dad985` |
| Commit timestamp | `2026-11-04T10:02:56-05:00` |

## Public API

- `display_order(attempt_id: str, keys: Sequence[str]) -> tuple[str, tuple[str, ...]]` ([source](../../../../../../src/learnloop/followup_serve/marks.py), line 39) — (the logged seed, the stable identities in display order).
- `latest_marks(rows: Iterable[Mapping[str, Any]]) -> dict[str | None, Mapping[str, Any]]` ([source](../../../../../../src/learnloop/followup_serve/marks.py), line 52) — A change of mind appends and the latest counts: per hypothesis identity (None is the None of these line), the latest row in ``rows``, oldest first, unless it took the mark back.
- `opinion_entries(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/followup_serve/marks.py), line 62) — What the diagnoser reads of one attempt's marks: the latest counts.
- `opinion_block(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_serve/marks.py), line 78) — The attributed block a context carries for one attempt, or None (it renders as before).
- `marked_causes(rows: Iterable[Mapping[str, Any]]) -> tuple[tuple[str, str], ...]` ([source](../../../../../../src/learnloop/followup_serve/marks.py), line 85) — (hypothesis version, statement) of each cause the opinion shows: model-written text, so what reads the opinion read it, and it folds into that writer's provenance record (Codex review F1).
- `attempt_marks(repository: Any, attempt_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/followup_serve/marks.py), line 96) — One attempt's ledger rows, oldest first; none below migration 242.
- `probe_state(connection: Any, *, factor_id: str | None, workflow: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/followup_serve/marks.py), line 103) — Whether the attempt's probe has been answered, by which attempt, and its outcome if known.

### Module constants

- `ORDER_VERSION` ([src/learnloop/followup_serve/marks.py](../../../../../../src/learnloop/followup_serve/marks.py), line 23)
- `MY_GAP` ([src/learnloop/followup_serve/marks.py](../../../../../../src/learnloop/followup_serve/marks.py), line 25)
- `PARTLY` ([src/learnloop/followup_serve/marks.py](../../../../../../src/learnloop/followup_serve/marks.py), line 26)
- `NOT_IT` ([src/learnloop/followup_serve/marks.py](../../../../../../src/learnloop/followup_serve/marks.py), line 27)
- `NONE_OF_THESE` ([src/learnloop/followup_serve/marks.py](../../../../../../src/learnloop/followup_serve/marks.py), line 28)
- `CLEARED` ([src/learnloop/followup_serve/marks.py](../../../../../../src/learnloop/followup_serve/marks.py), line 29)
- `HYPOTHESIS_MARKS` ([src/learnloop/followup_serve/marks.py](../../../../../../src/learnloop/followup_serve/marks.py), line 31)
- `MARKS` ([src/learnloop/followup_serve/marks.py](../../../../../../src/learnloop/followup_serve/marks.py), line 32)
- `MARK_WORDS` ([src/learnloop/followup_serve/marks.py](../../../../../../src/learnloop/followup_serve/marks.py), line 34)
- `ATTRIBUTION` ([src/learnloop/followup_serve/marks.py](../../../../../../src/learnloop/followup_serve/marks.py), line 36)

### Explicit exports

`__all__` declares:

- `ATTRIBUTION`
- `CLEARED`
- `HYPOTHESIS_MARKS`
- `MARKS`
- `MARK_WORDS`
- `MY_GAP`
- `NONE_OF_THESE`
- `NOT_IT`
- `ORDER_VERSION`
- `PARTLY`
- `attempt_marks`
- `display_order`
- `latest_marks`
- `marked_causes`
- `opinion_block`
- `opinion_entries`
- `probe_state`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `module`; statically calls `latest_marks`
- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `opinion_block`; statically calls `opinion_block`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `attempt_marks`, `marked_causes`, `opinion_block`; statically calls `attempt_marks`, `marked_causes`, `opinion_block`
- [[Reference/Modules/learnloop/diagnosis/split/provenance|learnloop.diagnosis.split.provenance]] — imports `marked_causes`; statically calls `marked_causes`
- [[Reference/Modules/learnloop/diagnosis/split/snapshot|learnloop.diagnosis.split.snapshot]] — imports `opinion_block`; statically calls `opinion_block`
- [[Reference/Modules/learnloop/followup_run/marks|learnloop.followup_run.marks]] — imports `module`; statically calls `display_order`, `latest_marks`, `probe_state`
- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `module`; statically calls `latest_marks`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/hypothesis_marks|learnloop.db.stores.hypothesis_marks]] — imports `module`; calls `attempt_of_item`, `latest_observation`, `marks_for_attempt`, `present`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]], [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]], [[Reference/Modules/learnloop/diagnosis/split/provenance|learnloop.diagnosis.split.provenance]], [[Reference/Modules/learnloop/diagnosis/split/snapshot|learnloop.diagnosis.split.snapshot]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_hypothesis_marks.py](../../../../../../tests/test_hypothesis_marks.py) — direct import
  - `test_an_exposure_records_the_order_as_displayed_not_the_servers`
  - `test_the_blind_grader_never_sees_marks_and_the_diagnoser_does`
  - `test_the_list_keeps_its_order_on_every_read_and_a_new_version_keeps_its_place`
  - `test_the_order_is_a_logged_seed_over_stable_identities`
- [tests/test_hypothesis_marks_context.py](../../../../../../tests/test_hypothesis_marks_context.py) — direct import
  - `test_the_opinion_block_says_whose_it_is_and_is_absent_with_none`

## Modification guidance

- Make changes here when the responsibility remains marks within learnloop.followup_serve; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_serve/marks.py](../../../../../../src/learnloop/followup_serve/marks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
