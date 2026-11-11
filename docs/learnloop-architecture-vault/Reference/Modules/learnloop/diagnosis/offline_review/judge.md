---
title: "learnloop.diagnosis.offline_review.judge"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/offline_review/judge.py"
source_paths:
  - "src/learnloop/diagnosis/offline_review/judge.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.offline_review"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.offline_review.judge module"
  - "src/learnloop/diagnosis/offline_review/judge.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-offline-review"
---

# `learnloop.diagnosis.offline_review.judge`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.offline_review.judge` exists within [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] to own the behavior summarized by its module contract: The blind LLM judge for the M1 arms (Slice 1 §12.1 "Who judges").

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/offline_review/judge.py](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py) |
| Source lines | 376 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CandidateVerdict(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 47)
- `class PairPreference(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 53)
- `class DiagnosisJudgment(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 60)
- `class LinkVerdict(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 67)
- `class LinkJudgment(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 73)
- `class CauseMatch(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 77)
- `class PlantedCauseJudgment(WireModel)` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 83)
- `judge_view(proposal: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 87) — What the judge may see of one diagnosis: content only, no ids or labels.
- `assign_labels(arms: Sequence[str], *, seed: int, pass_index: int) -> dict[str, str]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 118) — label -> arm.
- `input_hash(prompt: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 128)
- `diagnosis_judgment_prompt(*, item: Mapping[str, Any], learner_answer_md: str, labelled: Mapping[str, Mapping[str, Any]], pairs: Sequence[tuple[str, str]]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 132)
- `link_judgment_prompt(*, current: Mapping[str, Any], links: Mapping[str, Mapping[str, Any]]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 168)
- `planted_cause_prompt(*, item: Mapping[str, Any], learner_answer_md: str, target_cause: str, other_causes: Sequence[str], labelled_causes: Mapping[str, str]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 191)
- `request_diagnosis_judgment(client: OperationClient, prompt: str) -> DiagnosisJudgment` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 220)
- `request_link_judgment(client: OperationClient, prompt: str) -> LinkJudgment` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 224)
- `request_planted_cause_judgment(client: OperationClient, prompt: str) -> PlantedCauseJudgment` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 228)
- `primary_statement(proposal: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 232)
- `canonical_pair(left_arm: str, right_arm: str, preferred: str) -> tuple[str, str, str]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 244) — Normalize a preference to the PAIRS_OF_INTEREST orientation.
- `stable_json(value: Any) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 256)
- `completed_diagnoses(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 277)
- `judged_arm_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 281) — arm -> the completed diagnosis the listwise judge rates.
- `diagnosis_judgment_revision(by_arm: Mapping[str, Mapping[str, Any]]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 288)
- `cited_links(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, list[str]]]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 296) — cited attempt id -> the arms, relations and claims that proposed the link.
- `link_judgment_revision(cited_ids: Iterable[str]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 313)
- `planted_statements(rows: Sequence[Mapping[str, Any]]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 317) — diagnosis id -> primary cause statement, for the planted-cause matcher.
- `planted_judgment_revision(statements: Mapping[str, str]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 324)
- `content_hash(value: Any) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 328)
- `revision_of(row: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 332)

### Module constants

- `JUDGE_PROMPT_VERSION` ([src/learnloop/diagnosis/offline_review/judge.py](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 28)
- `LINK_JUDGE_PROMPT_VERSION` ([src/learnloop/diagnosis/offline_review/judge.py](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 29)
- `PLANTED_JUDGE_PROMPT_VERSION` ([src/learnloop/diagnosis/offline_review/judge.py](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 30)
- `RATINGS` ([src/learnloop/diagnosis/offline_review/judge.py](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 31)
- `PAIRS_OF_INTEREST` ([src/learnloop/diagnosis/offline_review/judge.py](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 35)
- `JUDGED_ARMS` ([src/learnloop/diagnosis/offline_review/judge.py](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 269)

### Explicit exports

`__all__` declares:

- `JUDGED_ARMS`
- `JUDGE_PROMPT_VERSION`
- `cited_links`
- `completed_diagnoses`
- `content_hash`
- `diagnosis_judgment_revision`
- `judged_arm_rows`
- `link_judgment_revision`
- `planted_judgment_revision`
- `planted_statements`
- `revision_of`
- `LINK_JUDGE_PROMPT_VERSION`
- `PAIRS_OF_INTEREST`
- `PLANTED_JUDGE_PROMPT_VERSION`
- `RATINGS`
- `CandidateVerdict`
- `CauseMatch`
- `DiagnosisJudgment`
- `LinkJudgment`
- `LinkVerdict`
- `PairPreference`
- `PlantedCauseJudgment`
- `assign_labels`
- `canonical_pair`
- `diagnosis_judgment_prompt`
- `input_hash`
- `judge_view`
- `link_judgment_prompt`
- `planted_cause_prompt`
- `primary_statement`
- `request_diagnosis_judgment`
- `request_link_judgment`
- `request_planted_cause_judgment`

## Internal implementation anchors

- `_revision(kind: str, version: str, inputs: Any) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py), line 272)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/offline_review/decider_links|learnloop.diagnosis.offline_review.decider_links]] — imports `LinkJudgment`, `LinkVerdict`; statically calls `LinkJudgment`, `LinkVerdict`
- [[Reference/Modules/learnloop/diagnosis/offline_review/links|learnloop.diagnosis.offline_review.links]] — imports `revision_of`; statically calls `revision_of`
- [[Reference/Modules/learnloop/diagnosis/offline_review/report|learnloop.diagnosis.offline_review.report]] — imports `RATINGS`, `module`; statically calls `cited_links`, `diagnosis_judgment_revision`, `judged_arm_rows`, `link_judgment_revision`, `planted_judgment_revision`, `planted_statements`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `module`; statically calls `assign_labels`, `canonical_pair`, `cited_links`, `diagnosis_judgment_prompt`, `diagnosis_judgment_revision`, `input_hash`, `judge_view`, `judged_arm_rows`, `link_judgment_prompt`, `link_judgment_revision`, `planted_cause_prompt`, `planted_judgment_revision`, `planted_statements`, `request_diagnosis_judgment`, `request_link_judgment`, `request_planted_cause_judgment`, `stable_json`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]] — imports `judge_view`; statically calls `judge_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`, `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/diagnosis/split/validation|learnloop.diagnosis.split.validation]] — imports `primary_cause`; calls `primary_cause`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `random`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/offline_review/decider_links|learnloop.diagnosis.offline_review.decider_links]], [[Reference/Modules/learnloop/diagnosis/offline_review/links|learnloop.diagnosis.offline_review.links]], [[Reference/Modules/learnloop/diagnosis/offline_review/report|learnloop.diagnosis.offline_review.report]], [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnosis_fakes.py](../../../../../../../tests/diagnosis_fakes.py) — direct import
- [tests/test_diagnose_review.py](../../../../../../../tests/test_diagnose_review.py) — direct import
- [tests/test_diagnosis_history_modes.py](../../../../../../../tests/test_diagnosis_history_modes.py) — direct import
  - `test_snapshot_is_unavailable_without_the_capability`
- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_link_judgments`
  - `test_links_the_decider_answered_are_never_paid_for_again_when_the_fallback_failed`

## Modification guidance

- Change judge policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/offline_review/judge.py](../../../../../../../src/learnloop/diagnosis/offline_review/judge.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
