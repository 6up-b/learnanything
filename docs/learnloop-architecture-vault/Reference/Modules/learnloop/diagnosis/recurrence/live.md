---
title: "learnloop.diagnosis.recurrence.live"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/recurrence/live.py"
source_paths:
  - "src/learnloop/diagnosis/recurrence/live.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.recurrence"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.recurrence.live module"
  - "src/learnloop/diagnosis/recurrence/live.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-recurrence"
---

# `learnloop.diagnosis.recurrence.live`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.recurrence.live` exists within [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] to own the behavior summarized by its module contract: The live T1 step of a diagnose job, and the escalated repair (Slice 2 §3.2, §3.7).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/recurrence/live.py](../../../../../../../src/learnloop/diagnosis/recurrence/live.py) |
| Source lines | 530 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `live_judge_caps(max_pairs: int) -> SpendCaps` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 86) — One diagnose job's own budget: its judge calls (Codex: calls bound them) plus the few metered embedding requests for its own hypotheses.
- `recurrence_step(vault: LoadedVault, repository: Repository, *, attempt_id: str, judge_factory: ClientFactory | None=None, embedding_factory: ClientFactory | None=None, spend: ReviewSpend | None=None, reserve: Reserve | None=None, cancelled: Cancelled | None=None, clock: Clock | None=None, heartbeat: Heartbeat | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 113) — ``spend``/``reserve``: the enclosing command's budget and what it keeps for its remaining diagnoses; None outside a budgeted command.
- `default_live_judge_factory(vault: LoadedVault) -> ClientFactory` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 233)
- `escalation_card_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 268)
- `record_escalation(vault: LoadedVault, repository: Repository, *, attempt_id: str, diagnosis: Mapping[str, Any], writer_factory: ClientFactory | None=None, spend: ReviewSpend | None=None, reserve: Reserve | None=None, cancelled: Cancelled | None=None, clock: Clock | None=None, heartbeat: Heartbeat | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 297) — Write the escalation receipt when this attempt's cause recurs K times.

### Module constants

- `LOG` ([src/learnloop/diagnosis/recurrence/live.py](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 71)
- `MODEL_CALL_OWNER_KIND` ([src/learnloop/diagnosis/recurrence/live.py](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 74)
- `LIVE_EMBED_CALLS` ([src/learnloop/diagnosis/recurrence/live.py](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 76)
- `PLANNED_JUDGE_PROMPT_TOKENS` ([src/learnloop/diagnosis/recurrence/live.py](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 79)
- `PLANNED_EMBED_TOKENS_PER_JOB` ([src/learnloop/diagnosis/recurrence/live.py](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 80)
- `_SUGGESTION_FIELDS` ([src/learnloop/diagnosis/recurrence/live.py](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 417)

### Explicit exports

`__all__` declares:

- `PLANNED_EMBED_TOKENS_PER_JOB`
- `escalation_card_enabled`
- `PLANNED_JUDGE_PROMPT_TOKENS`
- `default_live_judge_factory`
- `live_judge_caps`
- `record_escalation`
- `recurrence_step`

## Internal implementation anchors

- `_receipts_for(spend: ReviewSpend, repository: Repository, attempt_id: str) -> Iterator[None]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 102) — Receipt the step's calls under THIS attempt, even on a shared command budget.
- `_judge_attempt(vault: LoadedVault, repository: Repository, *, attempt_id: str, judge_factory: ClientFactory, embedding_factory: ClientFactory, spend: ReviewSpend, reserve: Reserve | None, heartbeat: Heartbeat | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 166)
- `_attempt_classes(repository: Repository, attempt_id: str) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 240)
- `_escalated_class(proposal: Mapping[str, Any], classes: Mapping[str, list[dict[str, Any]]]) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 249) — The diagnosis's highest-weight cause that is a learner-state hypothesis here.
- `_diagnosis_in_force(repository: Repository, attempt_id: str) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 272) — A blind-graded answer counts only while a completed live diagnosis is in force for its current grade (a regrade that left nothing to explain, or a failed rediagnosis, takes it out); a pre-split answer counts as is.
- `_shown_repairs(repository: Repository, attempt_ids: list[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 282) — Every repair shown for these answers: their feedback's suggestions and any repair an earlier escalation wrote for them.
- `_as_repair_suggestion(vault: LoadedVault, repository: Repository, repair: Mapping[str, Any], *, attempt_id: str, diagnosis_id: str, rows: list[dict[str, Any]], current_repairs: list[dict[str, Any]]=()) -> tuple[dict[str, Any], dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 423) — The generated repair as a repair suggestion, and its validation.
- `_request_repair(vault: LoadedVault, *, statement: str, classes: Mapping[str, list[dict[str, Any]]], count: int, earlier_repairs: list[dict[str, Any]], current_repairs: list[dict[str, Any]], writer_factory: ClientFactory | None, spend: ReviewSpend | None, reserve: Reserve | None, cancelled: Cancelled | None, repository: Repository, attempt_id: str, heartbeat: Heartbeat | None=None) -> tuple[dict[str, Any] | None, dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/live.py), line 474) — Ask the diagnosis route for a repair with a new operator (§3.7), once.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `PLANNED_EMBED_TOKENS_PER_JOB`, `PLANNED_JUDGE_PROMPT_TOKENS`, `default_live_judge_factory`, `record_escalation`, `recurrence_step`; statically calls `default_live_judge_factory`, `record_escalation`, `recurrence_step`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`, `SpendLimitExceeded`; calls `SpendCaps`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `RECURRENCE_GROUP_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/recurrence|learnloop.db.stores.recurrence]] — imports `insert_escalation`; calls `insert_escalation`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `validate_repair_candidate`; calls `validate_repair_candidate`
- [[Reference/Modules/learnloop/diagnosis/causal_factor_deferral|learnloop.diagnosis.causal_factor_deferral]] — imports `ESCALATION_RECURRENCE_K`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `materialize_attempt_episode`; calls `materialize_attempt_episode`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `ReviewSpend`; calls `ReviewSpend`
- [[Reference/Modules/learnloop/diagnosis/recurrence/display|learnloop.diagnosis.recurrence.display]] — imports `escalation_suggestion_id`; calls `escalation_suggestion_id`
- [[Reference/Modules/learnloop/diagnosis/recurrence/escalation|learnloop.diagnosis.recurrence.escalation]] — imports `per_job_spend`, `repair_key`, `request_different_repair`; calls `per_job_spend`, `repair_key`, `request_different_repair`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `Heartbeat`, `LeaseLost`, `Reserve`, `default_judge_client`, `embed_on_spend`, `judge_executor`, `learner_state`, `plan_shortlist`, `receipt_sink`; calls `default_judge_client`, `embed_on_spend`, `judge_executor`, `learner_state`, `plan_shortlist`, `receipt_sink`
- [[Reference/Modules/learnloop/diagnosis/recurrence/kind|learnloop.diagnosis.recurrence.kind]] — imports `SAME_CAUSE`, `hypothesis_subjects`; calls `hypothesis_subjects`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `hypothesis_records`, `pending_records`; calls `hypothesis_records`, `pending_records`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `judge_pairs`; calls `judge_pairs`
- [[Reference/Modules/learnloop/recurrence|learnloop.recurrence]] — imports `key_for_statement`, `normalize_statement`; calls `key_for_statement`, `normalize_statement`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `active_group_map`, `recurrence_active`, `refresh_recurrence_groups`; calls `active_group_map`, `recurrence_active`, `refresh_recurrence_groups`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_recurrence_live.py](../../../../../../../tests/test_recurrence_live.py) — direct import
  - `test_the_generated_repair_aims_at_the_recurring_causes_target`

## Modification guidance

- Change live policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/recurrence/live.py](../../../../../../../src/learnloop/diagnosis/recurrence/live.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
