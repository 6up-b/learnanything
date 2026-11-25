---
title: "learnloop.attempts.replay_reading"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/replay_reading.py"
source_paths:
  - "src/learnloop/attempts/replay_reading.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.attempts.replay_reading module"
  - "src/learnloop/attempts/replay_reading.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.replay_reading`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.replay_reading` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: What replay reads of a persisted grade where the evidence reading fixes (mvp-0.61) changed it.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/replay_reading.py](../../../../../../src/learnloop/attempts/replay_reading.py) |
| Source lines | 143 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `replayed_grader_confidence(vault: Any, stored: Any) -> float` ([source](../../../../../../src/learnloop/attempts/replay_reading.py), line 29) — The grader confidence a persisted grade replays with.
- `replayed_grading_source(vault: Any, repository: Any, attempt: Mapping[str, Any], current_rows: Sequence[Any]) -> str` ([source](../../../../../../src/learnloop/attempts/replay_reading.py), line 42) — The grading source a persisted grade replays under.
- `grading_source_for_run(run: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/attempts/replay_reading.py), line 81) — The grading source of a model grading run, from its ``agent_runs`` row: ``codex`` for a provider ``CODEX_PROVIDER_NAMES`` lists, else ``ai``: the split the regrade door makes when it names a provider's source (``learnloop_sidecar.handlers.ai_providers.grading_source_for_provider…
- `replaced_exam_purpose(vault: Any, repository: Any, attempt_id: str, replayed: bool) -> str | None` ([source](../../../../../../src/learnloop/attempts/replay_reading.py), line 91) — The administration purpose an exam answer's grade channel is written under by ``apply_attempt``, or None when it writes none there.
- `withholds_review_as_variant_request(vault: Any, repository: Any, attempt_id: str) -> bool` ([source](../../../../../../src/learnloop/attempts/replay_reading.py), line 108) — Whether this attempt is a request for an easier or harder variant whose source item it leaves unreviewed.

### Module constants

- `MODEL_GRADER_TIER` ([src/learnloop/attempts/replay_reading.py](../../../../../../src/learnloop/attempts/replay_reading.py), line 18)
- `MODEL_GRADING_SOURCES` ([src/learnloop/attempts/replay_reading.py](../../../../../../src/learnloop/attempts/replay_reading.py), line 20)
- `GRADING_RUN_PURPOSES` ([src/learnloop/attempts/replay_reading.py](../../../../../../src/learnloop/attempts/replay_reading.py), line 24)

### Explicit exports

`__all__` declares:

- `GRADING_RUN_PURPOSES`
- `MODEL_GRADER_TIER`
- `MODEL_GRADING_SOURCES`
- `grading_source_for_run`
- `replaced_exam_purpose`
- `replayed_grader_confidence`
- `replayed_grading_source`
- `withholds_review_as_variant_request`

## Internal implementation anchors

- `_graded_more_than_once(repository: Any, attempt_id: str) -> bool` ([source](../../../../../../src/learnloop/attempts/replay_reading.py), line 124) — A second write replaced the attempt's first grade.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `MODEL_GRADING_SOURCES`, `replaced_exam_purpose`, `replayed_grader_confidence`, `replayed_grading_source`, `withholds_review_as_variant_request`; statically calls `replaced_exam_purpose`, `replayed_grader_confidence`, `replayed_grading_source`, `withholds_review_as_variant_request`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `evidence_reading_fixes_on`; calls `evidence_reading_fixes_on`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `EXAM_GRADE_PURPOSE`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `CODEX_PROVIDER_NAMES`
- [[Reference/Modules/learnloop/grading_epochs|learnloop.grading_epochs]] — imports `graded_more_than_once`; calls `graded_more_than_once`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evidence_reading_successor.py](../../../../../../tests/test_evidence_reading_successor.py) — direct import
  - `test_r4_a_replacements_source_is_never_invented`

## Modification guidance

- Change replay reading policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/replay_reading.py](../../../../../../src/learnloop/attempts/replay_reading.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
