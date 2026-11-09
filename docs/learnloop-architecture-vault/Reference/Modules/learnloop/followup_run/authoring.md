---
title: "learnloop.followup_run.authoring"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_run/authoring.py"
source_paths:
  - "src/learnloop/followup_run/authoring.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_run.authoring` exists within [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] to own the behavior summarized by its module contract: The one new authoring operation (spec §4.1), on a frontier LLM.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py) |
| Source lines | 290 |
| Owning package | [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class AuthoringRejected(ValueError)` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 40) — An authored question failed an output check: nothing was written, nothing is served.
- `class AuthoredProbe` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 45)
- `protection_view(vault: Any, repository: Repository) -> Any` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 53) — The withheld items; raises when they can't be read, so no prompt is built.
- `admissible_item(withheld: Any, item: Any) -> bool` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 64)
- `reserved_view(vault: Any, repository: Repository) -> Any` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 68) — The questions still reserved or withheld, as ``protection_view`` says; raises when they can't be read, so nothing is compared against half a list and no prompt is built.
- `causes_match_reserved(vault: Any, repository: Repository, hypothesis_ids: Sequence[str]) -> bool` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 89) — The owner's ruling of Nov 4, 2026: a cause stops its probe only by reproducing a question still reserved, read by its words.
- `causes_coverage(vault: Any, repository: Repository, hypothesis_ids: Sequence[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 105) — For the admission receipt: what each cause's write-time record covers.
- `build_context(vault: Any, repository: Repository, *, learning_object_id: str, hypotheses: Sequence[Mapping[str, Any]], router_decision: Mapping[str, Any], target_facets: Sequence[str], source_item_id: str | None, measurement_pattern: str | None=None, avoid_phrases: Sequence[str]=()) -> tuple[FollowupProbeContext, dict[str, str]]` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 134) — The prompt's context, and the reference -> hypothesis id map.
- `request_authored_probe(client: Any, context: FollowupProbeContext) -> FollowupProbeAuthored` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 201)
- `check_output(vault: Any, repository: Repository, authored: FollowupProbeAuthored, *, refs: Mapping[str, str], learning_object_id: str) -> AuthoredProbe` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 214) — The output checks that run before anything is written (§4.1).
- `resolve_author_client(vault: Any) -> Any | None` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 277) — The route's client, or None when it is not ready (nothing is spent).

### Module constants

- `AUTHORING_PURPOSE` ([src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py), line 28)
- `AUTHOR_ROUTE` ([src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py), line 30)
- `AUTHOR_AXES` ([src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py), line 32)
- `CAUSE_MATCHES_RESERVED` ([src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py), line 35)
- `QUESTION_MATCHES_RESERVED` ([src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py), line 36)
- `RESERVED_MATCHES` ([src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py), line 37)

### Explicit exports

`__all__` declares:

- `AUTHORING_PURPOSE`
- `AUTHOR_AXES`
- `AUTHOR_ROUTE`
- `AuthoredProbe`
- `AuthoringRejected`
- `CAUSE_MATCHES_RESERVED`
- `QUESTION_MATCHES_RESERVED`
- `RESERVED_MATCHES`
- `admissible_item`
- `build_context`
- `causes_coverage`
- `causes_match_reserved`
- `check_output`
- `reserved_view`
- `protection_view`
- `request_authored_probe`
- `resolve_author_client`

## Internal implementation anchors

- `_cause_words(hypothesis: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 81) — What the router's card and the author's prompt would show of a cause.
- `_normalized(text: str) -> str` ([source](../../../../../../src/learnloop/followup_run/authoring.py), line 210)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `AuthoredProbe`, `AuthoringRejected`, `QUESTION_MATCHES_RESERVED`, `build_context`, `causes_coverage`, `check_output`, `request_authored_probe`, `reserved_view`; statically calls `build_context`, `causes_coverage`, `check_output`, `request_authored_probe`, `reserved_view`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `QUESTION_MATCHES_RESERVED`, `RESERVED_MATCHES`, `module`, `resolve_author_client`; statically calls `causes_match_reserved`, `resolve_author_client`
- [[Reference/Modules/learnloop/followup_run/lesson_probe|learnloop.followup_run.lesson_probe]] — imports `admissible_item`, `module`, `protection_view`, `reserved_view`; statically calls `admissible_item`, `check_output`, `protection_view`, `request_authored_probe`, `reserved_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `reserved_findings`, `reserved_questions`; calls `reserved_findings`, `reserved_questions`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `Inputs`, `stored_record`, `text_sha256`; calls `Inputs`, `stored_record`, `text_sha256`
- [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] — imports `FollowupProbeAuthored`, `FollowupProbeContext`, `followup_probe_prompt`; calls `FollowupProbeContext`, `followup_probe_prompt`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `EXAM_ATTEMPT_TYPES`, `PastWork`, `WITHHELD_EXAM`, `WITHHELD_RESERVED`, `hypothesis_answers`, `withheld_items`; calls `PastWork`, `hypothesis_answers`, `withheld_items`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]], [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]], [[Reference/Modules/learnloop/followup_run/lesson_probe|learnloop.followup_run.lesson_probe]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f7_verify_the_settled_exit_adds_no_question_of_its_own`
- [tests/test_followup_live_shape.py](../../../../../../tests/test_followup_live_shape.py) — direct import
  - `test_audit_task_features_are_declared_as_the_systems_and_nothing_undeclared_slips_through`
- [tests/test_followup_reserved_only.py](../../../../../../tests/test_followup_reserved_only.py) — direct import
  - `test_a_cause_quoting_a_reserved_question_takes_the_practice_lane`
  - `test_a_short_reserved_stem_is_still_a_match_within_longer_words`
  - `test_an_authored_question_echoing_a_reserved_one_is_refused_with_nothing_served`
  - `test_r10_a_second_match_takes_the_practice_lane`
  - `test_r10_the_retry_is_the_workflows_one_so_no_third_call`
  - `test_the_retired_codes_are_gone`
- [tests/test_followup_rival_factor.py](../../../../../../tests/test_followup_rival_factor.py) — direct import
  - `test_a_cause_matching_a_reserved_question_closes_the_factor_this_lane_opened`

## Modification guidance

- Make changes here when the responsibility remains authoring within learnloop.followup_run; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_run/authoring.py](../../../../../../src/learnloop/followup_run/authoring.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
