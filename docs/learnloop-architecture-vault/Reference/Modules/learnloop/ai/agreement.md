---
title: "learnloop.ai.agreement"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/agreement.py"
source_paths:
  - "src/learnloop/ai/agreement.py"
source_commit: "fb2c453ac3ab8da9efb1006c29e0e6a91f85d263"
source_commit_timestamp: "2026-10-15T02:47:11-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.agreement module"
  - "src/learnloop/ai/agreement.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.agreement`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.agreement` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: ``learnloop decider agreement``: the Decider against the LLM on real pairs; never a model call.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/agreement.py](../../../../../../src/learnloop/ai/agreement.py) |
| Source lines | 187 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `fb2c453ac3ab8da9efb1006c29e0e6a91f85d263` |
| Commit timestamp | `2026-10-15T02:47:11-04:00` |

## Public API

- `probabilities(row: Mapping[str, Any]) -> dict[str, float]` ([source](../../../../../../src/learnloop/ai/agreement.py), line 68) — A Decider row's option distribution, or ``{}`` when it holds none that sums to about 1.
- `agreement_report(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ai/agreement.py), line 98) — Per-task pairs, agreement, confusion (Decider by LLM), fallbacks and labelled calibration.
- `ledger_rows(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/ai/agreement.py), line 174) — Every ``judgment_ledger`` row of one database (none when it has no ledger).

### Module constants

- `FAILURES` ([src/learnloop/ai/agreement.py](../../../../../../src/learnloop/ai/agreement.py), line 46)
- `LLM_JUDGES` ([src/learnloop/ai/agreement.py](../../../../../../src/learnloop/ai/agreement.py), line 47)
- `LABEL_JUDGES` ([src/learnloop/ai/agreement.py](../../../../../../src/learnloop/ai/agreement.py), line 48)
- `UNNAMED_CONTENT_TASKS` ([src/learnloop/ai/agreement.py](../../../../../../src/learnloop/ai/agreement.py), line 56)
- `_TEXT_PROBABILITIES` ([src/learnloop/ai/agreement.py](../../../../../../src/learnloop/ai/agreement.py), line 57)

### Explicit exports

`__all__` declares:

- `FAILURES`
- `LABEL_JUDGES`
- `LLM_JUDGES`
- `UNNAMED_CONTENT_TASKS`
- `agreement_report`
- `ledger_rows`
- `probabilities`

## Internal implementation anchors

- `_metadata(row: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ai/agreement.py), line 60)
- `_endpoints(row: Mapping[str, Any]) -> tuple[tuple[str, str], ...]` ([source](../../../../../../src/learnloop/ai/agreement.py), line 86)
- `_new_task() -> dict[str, Any]` ([source](../../../../../../src/learnloop/ai/agreement.py), line 93)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/decider|learnloop.cli.decider]] — imports `agreement_report`, `ledger_rows`; statically calls `agreement_report`, `ledger_rows`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `math`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/decider|learnloop.cli.decider]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_decider_agreement.py](../../../../../../tests/test_decider_agreement.py) — direct import
  - `test_agreement_reports_real_pairs_fallbacks_and_labels`
  - `test_agreement_without_labels_or_pairs_is_null_not_zero`
  - `test_span_support_labels_never_leak_to_another_rewords_check`
- [tests/test_method_explicit_landing.py](../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_the_agreement_report_binds_a_statement_label_only_explicitly_or_on_the_same_input`
- [tests/test_router_r2b_agreement.py](../../../../../../tests/test_router_r2b_agreement.py) — direct import
  - `test_a_failed_decider_is_a_fallback_in_the_report`
  - `test_the_router_decisions_feed_the_agreement_report`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/agreement.py](../../../../../../src/learnloop/ai/agreement.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
