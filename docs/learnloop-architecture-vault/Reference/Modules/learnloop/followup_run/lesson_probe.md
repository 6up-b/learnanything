---
title: "learnloop.followup_run.lesson_probe"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_run/lesson_probe.py"
source_paths:
  - "src/learnloop/followup_run/lesson_probe.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.followup_run"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.followup_run.lesson_probe module"
  - "src/learnloop/followup_run/lesson_probe.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-run"
---

# `learnloop.followup_run.lesson_probe`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_run.lesson_probe` exists within [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] to own the behavior summarized by its module contract: Teacher TE2: a lesson's probe, written by FG1's generation path (spec_teacher_v1 rev 5 §11.3 "What code does").

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_run/lesson_probe.py](../../../../../../src/learnloop/followup_run/lesson_probe.py) |
| Source lines | 196 |
| Owning package | [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `parse_key(dedupe_key: str) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/followup_run/lesson_probe.py), line 43) — ``(lesson id, node id)`` from a lesson job's key.
- `enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/followup_run/lesson_probe.py), line 52)
- `refuse(vault: Any, repository: Repository, job: Mapping[str, Any], reason: str, *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/lesson_probe.py), line 58)
- `failure_reason(error: str) -> str` ([source](../../../../../../src/learnloop/followup_run/lesson_probe.py), line 64) — A job's last error as the probe's refusal reason (its runs exhausted).
- `run(vault: Any, repository: Repository, job: Mapping[str, Any], *, clients: Any, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/followup_run/lesson_probe.py), line 107) — One lesson job: a typed refusal recorded in the lesson, or the admitted question.

### Module constants

- `ADMISSION_VERSION` ([src/learnloop/followup_run/lesson_probe.py](../../../../../../src/learnloop/followup_run/lesson_probe.py), line 37)
- `LESSON_DECISION` ([src/learnloop/followup_run/lesson_probe.py](../../../../../../src/learnloop/followup_run/lesson_probe.py), line 39)

### Explicit exports

`__all__` declares:

- `ADMISSION_VERSION`
- `LESSON_DECISION`
- `enabled`
- `failure_reason`
- `parse_key`
- `refuse`
- `run`

## Internal implementation anchors

- `_context(vault: Any, repository: Repository, *, learning_object_id: str, readings: list[str], card: Any, template: Any) -> tuple[Any, dict[str, str]]` ([source](../../../../../../src/learnloop/followup_run/lesson_probe.py), line 70) — FG1's context with the readings as the rival readings (no causal hypothesis row exists for them).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `module`; statically calls `enabled`, `failure_reason`, `refuse`, `run`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `is_subscription_transport`; calls `is_subscription_transport`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `reserved_findings`; calls `reserved_findings`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] — imports `FollowupProbeContext`; calls `FollowupProbeContext`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `family_measurement_intent`; calls `family_measurement_intent`
- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `module`; calls `_template_and_card`, `persist_item`
- [[Reference/Modules/learnloop/followup_run/authoring|learnloop.followup_run.authoring]] — imports `admissible_item`, `module`, `protection_view`, `reserved_view`; calls `admissible_item`, `check_output`, `protection_view`, `request_authored_probe`, `reserved_view`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `GenerationDeferred`, `_author_client`; calls `GenerationDeferred`, `_author_client`
- [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]] — imports `module`; calls `pending_request`, `record_ready`, `record_refused`
- [[Reference/Modules/learnloop/teacher/te2|learnloop.teacher.te2]] — imports `on`; calls `on`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/followup_rival_factor_helpers.py](../../../../../../tests/followup_rival_factor_helpers.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]
- [tests/followup_serve_helpers.py](../../../../../../tests/followup_serve_helpers.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]
- [tests/ih2_lessons_compete_helpers.py](../../../../../../tests/ih2_lessons_compete_helpers.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]
- [tests/teacher_te2_probes_helpers.py](../../../../../../tests/teacher_te2_probes_helpers.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]
- [tests/test_followup_next_matrix.py](../../../../../../tests/test_followup_next_matrix.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]
- [tests/test_followup_reserved_only.py](../../../../../../tests/test_followup_reserved_only.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]

## Modification guidance

- Make changes here when the responsibility remains lesson probe within learnloop.followup_run; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_run/lesson_probe.py](../../../../../../src/learnloop/followup_run/lesson_probe.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
