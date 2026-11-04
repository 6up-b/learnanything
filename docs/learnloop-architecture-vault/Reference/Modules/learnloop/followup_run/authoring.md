---
title: "learnloop.followup_run.authoring"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_run/authoring.py"
source_paths:
  - "src/learnloop/followup_run/authoring.py"
source_commit: "06461f09ccf65c6446b23516124ce9c3b699b9f9"
source_commit_timestamp: "2026-11-04T02:59:38-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.followup_run"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.followup_run.authoring module"
  - "src/learnloop/followup_run/authoring.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-run"
---

# `learnloop.followup_run.authoring`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_run.authoring` exists within [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] to own the behavior summarized by its module contract: The one new authoring operation (spec §4.1), on a frontier LLM.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py) |
| Source lines | 250 |
| Owning package | [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `06461f09ccf65c6446b23516124ce9c3b699b9f9` |
| Commit timestamp | `2026-11-04T02:59:38-05:00` |

## Public API

- `class AuthoringRejected(ValueError)` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 38) — An authored question failed an output check: nothing was written, nothing is served.
- `class AuthoredProbe` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 43)
- `protection_view(vault: Any, repository: Repository) -> Any` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 51) — The withheld items; raises when they can't be read, so no prompt is built.
- `admissible_item(withheld: Any, item: Any) -> bool` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 62)
- `hypotheses_exam_reason(vault: Any, repository: Repository, hypothesis_ids: Sequence[str]) -> str | None` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 66) — Why any of these causes' words may carry exam material, or None.
- `causes_refusal(reason: str) -> str` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 104) — The workflow's word for :func:`hypotheses_exam_reason`'s answer: exam material itself, or causes nothing rules it out for.
- `build_context(vault: Any, repository: Repository, *, learning_object_id: str, hypotheses: Sequence[Mapping[str, Any]], router_decision: Mapping[str, Any], target_facets: Sequence[str], source_item_id: str | None, measurement_pattern: str | None=None) -> tuple[FollowupProbeContext, dict[str, str]]` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 113) — The prompt's context, and the reference -> hypothesis id map.
- `request_authored_probe(client: Any, context: FollowupProbeContext) -> FollowupProbeAuthored` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 169)
- `check_output(vault: Any, repository: Repository, authored: FollowupProbeAuthored, *, refs: Mapping[str, str], learning_object_id: str) -> AuthoredProbe` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 182) — The output checks that run before anything is written (§4.1).
- `resolve_author_client(vault: Any) -> Any | None` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 238) — The route's client, or None when it is not ready (nothing is spent).

### Module constants

- `AUTHORING_PURPOSE` ([src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py), line 28)
- `AUTHOR_ROUTE` ([src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py), line 30)
- `AUTHOR_AXES` ([src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py), line 32)
- `CAUSES_FROM_EXAM` ([src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py), line 34)
- `CAUSES_UNACCOUNTED` ([src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py), line 35)

### Explicit exports

`__all__` declares:

- `AUTHORING_PURPOSE`
- `AUTHOR_AXES`
- `AUTHOR_ROUTE`
- `AuthoredProbe`
- `AuthoringRejected`
- `CAUSES_FROM_EXAM`
- `CAUSES_UNACCOUNTED`
- `admissible_item`
- `build_context`
- `causes_refusal`
- `check_output`
- `hypotheses_exam_reason`
- `protection_view`
- `request_authored_probe`
- `resolve_author_client`

## Internal implementation anchors

- `_normalized(text: str) -> str` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 178)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `AuthoredProbe`, `AuthoringRejected`, `build_context`, `check_output`, `request_authored_probe`; statically calls `build_context`, `check_output`, `request_authored_probe`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `AuthoringRejected`, `causes_refusal`, `hypotheses_exam_reason`, `resolve_author_client`; statically calls `causes_refusal`, `hypotheses_exam_reason`, `resolve_author_client`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `Inputs`, `stored_record`, `text_sha256`; calls `Inputs`, `stored_record`, `text_sha256`
- [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] — imports `FollowupProbeAuthored`, `FollowupProbeContext`, `followup_probe_prompt`; calls `FollowupProbeContext`, `followup_probe_prompt`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `CAUSE_UNRECORDED`, `PastWork`, `WITHHELD_EXAM`, `WITHHELD_RESERVED`, `hypothesis_answers`, `withheld_items`; calls `PastWork`, `hypothesis_answers`, `withheld_items`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]], [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f5_exam_attempt_work_is_exam_material_whatever_its_item`
  - `test_f5_rereview_a_cause_the_record_doesnt_cover_reaches_neither_request`
  - `test_f5_rereview_a_question_no_longer_on_record_counts_as_unaccounted`
  - `test_f5_rereview_a_vault_with_nothing_to_protect_keeps_its_probe_lane`
  - `test_f5_rereview_every_recorded_input_is_checked`
  - `test_f5_rereview_exam_work_anywhere_means_there_is_something_to_protect`
  - `test_f5_rereview_the_author_builder_refuses_a_cause_the_record_doesnt_cover`
  - `test_f5_what_the_writer_recorded_reading_counts`

## Modification guidance

- Make changes here when the responsibility remains authoring within learnloop.followup_run; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
