---
title: "learnloop.recurrence"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/recurrence.py"
source_paths:
  - "src/learnloop/recurrence.py"
source_commit: "67bc38f20b64011adbc8cf81f90c0722618a49d0"
source_commit_timestamp: "2026-10-12T13:10:39-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.recurrence module"
  - "src/learnloop/recurrence.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.recurrence`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.recurrence` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: The recurrence-key seam (Slice 1 §7.6), dependency-neutral.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/recurrence.py](../../../../../src/learnloop/recurrence.py) |
| Source lines | 92 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `67bc38f20b64011adbc8cf81f90c0722618a49d0` |
| Commit timestamp | `2026-10-12T13:10:39-04:00` |

## Public API

- `normalize_statement(value: str | None) -> str` ([source](../../../../../src/learnloop/recurrence.py), line 42) — The ``statement_normalized`` of a causal hypothesis.
- `group_key_for(root_statement: str) -> str` ([source](../../../../../src/learnloop/recurrence.py), line 53) — The key of a merged group, from its root class's normalized statement.
- `is_group_key(value: str | None) -> bool` ([source](../../../../../src/learnloop/recurrence.py), line 60)
- `key_for_statement(statement_normalized: str | None, groups: Mapping[str, str] | None=None) -> str` ([source](../../../../../src/learnloop/recurrence.py), line 64) — The recurrence key of one normalized statement (or of a key itself).
- `recurrence_key(hypothesis: Mapping[str, Any], groups: Mapping[str, str] | None=None) -> str` ([source](../../../../../src/learnloop/recurrence.py), line 77) — The group a hypothesis (or projected candidate) recurs under.

### Module constants

- `RECURRENCE_KEY_VERSION` ([src/learnloop/recurrence.py](../../../../../src/learnloop/recurrence.py), line 31)
- `GROUP_RECURRENCE_KEY_VERSION` ([src/learnloop/recurrence.py](../../../../../src/learnloop/recurrence.py), line 34)
- `GROUP_KEY_PREFIX` ([src/learnloop/recurrence.py](../../../../../src/learnloop/recurrence.py), line 37)
- `_NORMALIZE_RE` ([src/learnloop/recurrence.py](../../../../../src/learnloop/recurrence.py), line 39)

### Explicit exports

`__all__` declares:

- `GROUP_KEY_PREFIX`
- `GROUP_RECURRENCE_KEY_VERSION`
- `RECURRENCE_KEY_VERSION`
- `group_key_for`
- `is_group_key`
- `key_for_statement`
- `normalize_statement`
- `recurrence_key`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `key_for_statement`, `recurrence_key`; statically calls `key_for_statement`, `recurrence_key`
- [[Reference/Modules/learnloop/diagnosis/causal_factor_deferral|learnloop.diagnosis.causal_factor_deferral]] — imports `RECURRENCE_KEY_VERSION`, `recurrence_key`; statically calls `recurrence_key`
- [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] — imports `recurrence_key`; statically calls `recurrence_key`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `key_for_statement`; statically calls `key_for_statement`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `key_for_statement`; statically calls `key_for_statement`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `key_for_statement`, `normalize_statement`; statically calls `key_for_statement`, `normalize_statement`
- [[Reference/Modules/learnloop/diagnosis/recurrence/report|learnloop.diagnosis.recurrence.report]] — imports `key_for_statement`; statically calls `key_for_statement`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `recurrence_key`; statically calls `recurrence_key`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `GROUP_RECURRENCE_KEY_VERSION`, `group_key_for`, `normalize_statement`; statically calls `group_key_for`, `normalize_statement`
- [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]] — imports `key_for_statement`, `recurrence_key`; statically calls `key_for_statement`, `recurrence_key`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/diagnosis/causal_factor_deferral|learnloop.diagnosis.causal_factor_deferral]], [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]], [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]], [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mcp_c1a_narrow.py](../../../../../tests/test_mcp_c1a_narrow.py) — direct import
  - `test_a_recurrence_group_key_cannot_confirm_a_guessed_statement`
- [tests/test_recurrence_commands.py](../../../../../tests/test_recurrence_commands.py) — direct import
- [tests/test_recurrence_groups.py](../../../../../tests/test_recurrence_groups.py) — direct import
  - `test_a_different_verdict_inside_one_exact_class_is_a_review_case_not_a_split`
  - `test_a_later_same_at_the_judges_authority_is_refused_and_logged`
  - `test_a_same_verdict_merges_two_classes_into_one_group_key`
  - `test_an_owner_different_refuses_the_judge_merge_and_logs_it`
  - `test_attempt_level_owner_verdicts_resolve_only_to_one_class_per_side`
  - `test_no_merges_leave_every_key_exact_and_the_projection_empty`
  - `test_supersession_is_how_a_judges_different_is_replaced`
- [tests/test_recurrence_key.py](../../../../../tests/test_recurrence_key.py) — direct import
  - `test_merged_classes_share_the_group_key_and_singletons_keep_theirs`
  - `test_the_seam_is_the_exact_statement_key_without_groups`
- [tests/test_recurrence_live.py](../../../../../tests/test_recurrence_live.py) — direct import
  - `test_a_citation_of_an_existing_hypothesis_resolves_through_prior_hypothesis_id`
  - `test_a_not_the_same_mistake_tap_records_and_refreshes_without_blocking_a_citation`
  - `test_a_validated_citation_merges_without_any_judge_call`
  - `test_the_judge_merges_reworded_recurrences_and_the_third_escalates`
- [tests/test_stuck_prompt_composition.py](../../../../../tests/test_stuck_prompt_composition.py) — direct import
  - `test_stuck_answers_hypotheses_join_recurrence_groups_and_count_toward_k`

## Modification guidance

- Make changes here when the responsibility remains recurrence within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/recurrence.py](../../../../../src/learnloop/recurrence.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
