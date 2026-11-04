---
title: "learnloop.ai.disclosures"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/disclosures.py"
source_paths:
  - "src/learnloop/ai/disclosures.py"
source_commit: "9c3c613bdf639f94146be3c1f47dcef04060668a"
source_commit_timestamp: "2026-11-04T09:06:52-05:00"
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
  - "learnloop.ai.disclosures module"
  - "src/learnloop/ai/disclosures.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.disclosures`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.disclosures` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Privacy disclosures for the judgment routes (router spec §6.2, D6).

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/disclosures.py](../../../../../../src/learnloop/ai/disclosures.py) |
| Source lines | 360 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `9c3c613bdf639f94146be3c1f47dcef04060668a` |
| Commit timestamp | `2026-11-04T09:06:52-05:00` |

## Public API

- `recipient(config: LearnLoopConfig, provider_name: str) -> str` ([source](../../../../../../src/learnloop/ai/disclosures.py), line 290)
- `judge_route_disclosures(config: LearnLoopConfig) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/ai/disclosures.py), line 315) — One entry per judgment route: who receives learner text, what and when.
- `decider_destination(config: LearnLoopConfig, task: str) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/ai/disclosures.py), line 341) — ``(the key it needs, where it goes)`` for a Decider route, in the connection sheet's plain words.

### Module constants

- `JUDGE_ROUTES` ([src/learnloop/ai/disclosures.py](../../../../../../src/learnloop/ai/disclosures.py), line 18)
- `_WHEN` ([src/learnloop/ai/disclosures.py](../../../../../../src/learnloop/ai/disclosures.py), line 49)

### Explicit exports

`__all__` declares:

- `JUDGE_ROUTES`
- `decider_destination`
- `judge_route_disclosures`
- `recipient`

## Internal implementation anchors

- `_host(url: str | None) -> str` ([source](../../../../../../src/learnloop/ai/disclosures.py), line 285)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `JUDGE_ROUTES`, `judge_route_disclosures`; statically calls `judge_route_disclosures`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `decider_destination`; statically calls `decider_destination`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `judge_route_disclosures`; statically calls `judge_route_disclosures`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`; calls `provider_for_task`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`, `urllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]], [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]], [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_billing_class_is_subscription`
- [tests/test_chatgpt_plan_workspace.py](../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
  - `test_disclosures_name_the_plan_when_it_is_the_active_provider`
- [tests/test_decider_landing.py](../../../../../../tests/test_decider_landing.py) — direct import
  - `test_nothing_in_tier1_reads_the_deleted_route_check`
  - `test_the_one_ok_and_settings_name_perplexity_through_openrouter`
  - `test_the_tier1_disclosure_and_the_one_ok_use_one_recipient_for_a_direct_perplexity_route`
- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
  - `test_the_disclosures_name_the_learner_state`
- [tests/test_method_explicit_landing.py](../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_the_tier1_disclosure_names_the_statement_judgment`
- [tests/test_reader_intent.py](../../../../../../tests/test_reader_intent.py) — direct import
  - `test_the_disclosure_names_speculative_text`
- [tests/test_tier1_decider.py](../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_settings_and_eval_judges_disclose_the_tier1_routes`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/disclosures.py](../../../../../../src/learnloop/ai/disclosures.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
