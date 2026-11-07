---
title: "learnloop.followup_serve.gates"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_serve/gates.py"
source_paths:
  - "src/learnloop/followup_serve/gates.py"
source_commit: "98ecc0dca01b7a869e5544bec341618560243ba1"
source_commit_timestamp: "2026-11-06T19:52:14-05:00"
source_worktree_state: "clean"
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
  - "learnloop.followup_serve.gates module"
  - "src/learnloop/followup_serve/gates.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-serve"
---

# `learnloop.followup_serve.gates`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_serve.gates` exists within [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] to own the behavior summarized by its module contract: The switches of follow-up generate and serve (FG1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_serve/gates.py](../../../../../../src/learnloop/followup_serve/gates.py) |
| Source lines | 54 |
| Owning package | [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `98ecc0dca01b7a869e5544bec341618560243ba1` |
| Commit timestamp | `2026-11-06T19:52:14-05:00` |

## Public API

- `generate_and_serve_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/followup_serve/gates.py), line 29)
- `hypothesis_marks_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/followup_serve/gates.py), line 38) — FG1c's kill switch (``followup.hypothesis_marks``), at every algorithm version: a mark and an exposure are receipts, and an attributed opinion moves nothing.
- `effective_auto_generate_on_entry(config: Any) -> bool` ([source](../../../../../../src/learnloop/followup_serve/gates.py), line 46) — §4.3: true while FG1 is on, whatever the file says.

### Module constants

- `SERVING_SURFACE` ([src/learnloop/followup_serve/gates.py](../../../../../../src/learnloop/followup_serve/gates.py), line 16)
- `PHONE_SURFACE` ([src/learnloop/followup_serve/gates.py](../../../../../../src/learnloop/followup_serve/gates.py), line 18)
- `WORKFLOW_SURFACES` ([src/learnloop/followup_serve/gates.py](../../../../../../src/learnloop/followup_serve/gates.py), line 23)
- `RIVAL_CAUSES_FACTOR_VERSION` ([src/learnloop/followup_serve/gates.py](../../../../../../src/learnloop/followup_serve/gates.py), line 26)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `WORKFLOW_SURFACES`, `generate_and_serve_on`, `hypothesis_marks_on`; statically calls `generate_and_serve_on`, `hypothesis_marks_on`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `generate_and_serve_on`; statically calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `hypothesis_marks_on`; statically calls `hypothesis_marks_on`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `RIVAL_CAUSES_FACTOR_VERSION`, `generate_and_serve_on`; statically calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `RIVAL_CAUSES_FACTOR_VERSION`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `generate_and_serve_on`; statically calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `generate_and_serve_on`; statically calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `generate_and_serve_on`; statically calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `hypothesis_marks_on`; statically calls `hypothesis_marks_on`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `hypothesis_marks_on`; statically calls `hypothesis_marks_on`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `generate_and_serve_on`; statically calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/followup_run/lanes|learnloop.followup_run.lanes]] — imports `generate_and_serve_on`; statically calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/followup_run/marks|learnloop.followup_run.marks]] — imports `hypothesis_marks_on`; statically calls `hypothesis_marks_on`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `RIVAL_CAUSES_FACTOR_VERSION`, `WORKFLOW_SURFACES`, `generate_and_serve_on`; statically calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `hypothesis_marks_on`; statically calls `hypothesis_marks_on`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `generate_and_serve_on`; statically calls `generate_and_serve_on`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `SERVING_SURFACE`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `generate_and_serve_on`, `hypothesis_marks_on`; statically calls `generate_and_serve_on`, `hypothesis_marks_on`
- [[Reference/Modules/learnloop_sidecar/handlers/followup|learnloop_sidecar.handlers.followup]] — imports `generate_and_serve_on`; statically calls `generate_and_serve_on`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `PHONE_SURFACE`, `SERVING_SURFACE`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `generate_and_serve_on`; statically calls `generate_and_serve_on`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `SERVING_SURFACE`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `FOLLOWUP_SERVE_VERSIONS`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]], [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] and 17 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/followup_serve_helpers.py](../../../../../../tests/followup_serve_helpers.py) — direct import
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f7_a_prepared_probe_closes_with_the_switch`
- [tests/test_followup_journey.py](../../../../../../tests/test_followup_journey.py) — direct import
- [tests/test_followup_successor.py](../../../../../../tests/test_followup_successor.py) — direct import
  - `test_new_vaults_get_true_effectively_and_older_templates_stay_as_they_were`
  - `test_the_kill_switch_reads_off_a_vault_at_the_tag`
  - `test_the_switch_governs_the_effective_setting`
- [tests/test_followup_workflow.py](../../../../../../tests/test_followup_workflow.py) — direct import
  - `test_a_miss_at_the_tag_opens_one_workflow_and_withholds_the_predecessors_insertion`
  - `test_auto_generate_on_entry_is_effectively_true_only_while_fg1_is_on`
  - `test_below_the_tag_or_with_the_switch_off_no_workflow_opens`
- [tests/test_mobile_v2_followup.py](../../../../../../tests/test_mobile_v2_followup.py) — direct import
  - `test_f3_a_phone_miss_opens_its_workflow_held_under_the_phones_surface`
- [tests/test_te3b_codex_review.py](../../../../../../tests/test_te3b_codex_review.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains gates within learnloop.followup_serve; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_serve/gates.py](../../../../../../src/learnloop/followup_serve/gates.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
