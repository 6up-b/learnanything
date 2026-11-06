---
title: "learnloop.diagnosis.text_gaps.judges"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/text_gaps/judges.py"
source_paths:
  - "src/learnloop/diagnosis/text_gaps/judges.py"
source_commit: "dc5302d98cfcd397c2bb3678cdb2bf12f232164a"
source_commit_timestamp: "2026-11-06T04:43:14-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.text_gaps"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.text_gaps.judges module"
  - "src/learnloop/diagnosis/text_gaps/judges.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-text-gaps"
---

# `learnloop.diagnosis.text_gaps.judges`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.text_gaps.judges` exists within [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] to own the behavior summarized by its module contract: Paid calls of the learner-text gap pipeline, each admitted before it is sent.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/text_gaps/judges.py](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py) |
| Source lines | 532 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `dc5302d98cfcd397c2bb3678cdb2bf12f232164a` |
| Commit timestamp | `2026-11-06T04:43:14-05:00` |

## Public API

- `caps_for(vault: LoadedVault) -> SpendCaps` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 85)
- `class TextBudget` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 94) — Route registration and admission over one :class:`ReviewSpend`.
  - `__init__(self, spend: ReviewSpend, *, owner_kind: str=MODEL_CALL_OWNER_KIND) -> None` (line 102; internal)
  - `for_command(cls, spend: ReviewSpend) -> 'TextBudget'` (line 107; public) — A command's budget shared by every text it reads (``learnloop gaps run``).
  - `for_text(cls, vault: LoadedVault, *, price_per_million: float | None=None, cancelled: Callable[[], bool] | None=None) -> 'TextBudget'` (line 113; public)
  - `register_llm(self, route: str, client: Any) -> None` (line 121; public)
  - `register_decider(self, client: Any) -> None` (line 125; public)
  - `register_embedding(self, client: Any) -> None` (line 136; public)
  - `request(self, route: str, purpose: str, *, input_tokens: int, output_tokens: int | None=None) -> Iterator[Any]` (line 144; public)
  - `receipts(self, repository: Repository, owner_id: str) -> Iterator[None]` (line 150; public)
- `class LLMPairExecutor` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 162) — One isolated structured call per pair on ``learner_gap_judge`` (judge ``llm``).
  - `__init__(self, budget: TextBudget, client: Any) -> None` (line 167; internal)
  - `__call__(self, prompt: str, result_model: type[SameOrDifferent], purpose: str) -> tuple[SameOrDifferent, str]` (line 174; internal)
- `decider_rationale(question_set: str, probabilities: Mapping[str, float]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 186)
- `class DeciderPairExecutor` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 191) — The Decider on the same rendered pair (judge ``decider``).
  - `__init__(self, budget: TextBudget, client: Any) -> None` (line 196; internal)
  - `__call__(self, prompt: str, result_model: type[SameOrDifferent], purpose: str) -> tuple[SameOrDifferent, str]` (line 205; internal)
- `kind_state(text: LearnerText) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 219) — What the Decider reads for the kind: the learner's text and what it was about.
- `kind_input_hash(text: LearnerText) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 240)
- `log_reading(repository: Repository, text: LearnerText, reading: GapReading) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 258) — The context model's reading as a ``learner_gap_kind`` verdict (idempotent).
- `class DeciderKind` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 280)
  - `as_dict(self) -> dict[str, Any]` (line 288; public)
- `decider_kind(repository: Repository, budget: TextBudget, client: Any, text: LearnerText) -> DeciderKind` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 293) — The Decider's typed kind, appended to ``judgment_ledger`` (judge ``decider``).
- `reader_version(text: LearnerText) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 334) — The reader's prompt version for this text (RW1b's formative answers have their own task).
- `reader_prompt(text: LearnerText) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 342)
- `read_text(budget: TextBudget, client: Any, text: LearnerText) -> GapReading` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 353) — One isolated call naming the gap in a stuck answer; ``failed`` on refusal or error.
- `needed_context(vault: LoadedVault, item: Any, prerequisite_lo: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 378)
- `needed_prompt(context: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 388)
- `ask_needed(repository: Repository, budget: TextBudget, *, context: Mapping[str, Any], learning_object_id: str, practice_item_id: str, judge_client: Any | None, decider_client: Any | None) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 394) — Both judges' "needed?" verdicts, each appended to the ledger.
- `draft_prompt(context: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 466)
- `draft_prerequisite(budget: TextBudget, client: Any, context: Mapping[str, Any]) -> PrerequisiteDraft` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 472) — One authoring-route call; raises on refusal or failure (the caller logs it).
- `query_vector(repository: Repository, budget: TextBudget, embedder: Any, subject: Subject, *, field_name: str) -> np.ndarray | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 486) — The named gap's ``retrieval-query`` vector, stored once (a retry reuses it).

### Module constants

- `MODEL_CALL_OWNER_KIND` ([src/learnloop/diagnosis/text_gaps/judges.py](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 80)

### Explicit exports

`__all__` declares:

- `DeciderKind`
- `DeciderPairExecutor`
- `LLMPairExecutor`
- `MODEL_CALL_OWNER_KIND`
- `TextBudget`
- `ask_needed`
- `caps_for`
- `decider_kind`
- `decider_rationale`
- `draft_prerequisite`
- `kind_state`
- `log_reading`
- `needed_context`
- `query_vector`
- `read_text`
- `reader_prompt`

## Internal implementation anchors

- `_probabilities(answer: Any) -> dict[str, float]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 182)
- `_already_logged(connection: Any, *, task: str, left: tuple[str, str], judge: str, judge_model: str, prompt_version: str, input_hash: str, right: tuple[str, str] | None=None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py), line 244)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]] — imports `TextBudget`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `TextBudget`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `DeciderKind`, `DeciderPairExecutor`, `LLMPairExecutor`, `TextBudget`, `ask_needed`, `decider_kind`, `draft_prerequisite`, `log_reading`, `needed_context`, `query_vector`, `read_text`; statically calls `DeciderKind`, `ask_needed`, `decider_kind`, `draft_prerequisite`, `log_reading`, `needed_context`, `query_vector`, `read_text`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/tier1|learnloop.diagnosis.text_gaps.tier1]] — imports `DeciderKind`, `DeciderPairExecutor`, `LLMPairExecutor`, `TextBudget`, `ask_needed`, `decider_rationale`, `kind_input_hash`, `kind_state`, `log_reading`, `needed_prompt`, `read_text`; statically calls `DeciderKind`, `LLMPairExecutor`, `ask_needed`, `decider_rationale`, `kind_input_hash`, `kind_state`, `log_reading`, `needed_prompt`, `read_text`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`; calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`, `SpendLimitExceeded`; calls `SpendCaps`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `get_vector`, `put_vector`; calls `get_vector`, `put_vector`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `COMMAND_RECEIPT_OWNER`, `PIPELINE_RECEIPT_OWNER`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `ReviewSpend`, `RouteInfo`; calls `ReviewSpend`, `RouteInfo`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `estimate_tokens`, `producer_label`, `receipt_sink`; calls `estimate_tokens`, `producer_label`, `receipt_sink`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `register_retrieval_route`; calls `register_retrieval_route`
- [[Reference/Modules/learnloop/diagnosis/split/retrieval|learnloop.diagnosis.split.retrieval]] — imports `QUERY_PREFIX`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]] — imports `DECIDER_KIND_QUESTION_SET`, `DECIDER_NEEDED_QUESTION_SET`, `DECIDER_PAIR_QUESTION_SET`, `DECIDER_ROUTE`, `DRAFT_PROMPT_VERSION`, `DRAFT_PURPOSE`, `DRAFT_ROUTE`, `DRAFT_TASK`, `EMBEDDING_ROUTE`, `GapReading`, `JUDGE_ROUTE`, `KIND_QUESTION`, `KIND_TASK`, `LearnerText`, `NEEDED_PROMPT_VERSION`, `NEEDED_PURPOSE`, `NEEDED_QUESTION`, `NEEDED_TASK`, `NEEDED_TASK_TEXT`, `NeededVerdict`, `PAIR_OPTIONS`, `PAIR_QUESTION_INSTRUCTIONS`, `PrerequisiteDraft`, `READER_FORMATIVE_PROMPT_VERSION`, `READER_FORMATIVE_TASK`, `READER_NOTE_PROMPT_VERSION`, `READER_NOTE_TASK`, `READER_PROMPT_VERSION`, `READER_PURPOSE`, `READER_ROUTE`, `READER_TASK`; calls `GapReading`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `SameOrDifferent`; calls `SameOrDifferent`
- [[Reference/Modules/learnloop/matching/kinds|learnloop.matching.kinds]] — imports `Subject`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `LearnerGap`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `presented_prompt`; calls `presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]], [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]], [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]], [[Reference/Modules/learnloop/diagnosis/text_gaps/tier1|learnloop.diagnosis.text_gaps.tier1]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_learner_text_gaps_rereview.py](../../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
  - `test_rr_f3_a_failed_pair_backs_off_one_text_and_the_run_goes_on`
  - `test_rr_f5_a_commands_calls_do_not_count_toward_the_live_daily_cap`
  - `test_rr_f5_gaps_run_reads_on_a_command_budget`
- [tests/test_learner_text_gaps_review.py](../../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f12_the_seed_unit_is_admitted_on_a_metered_tutor_route`
  - `test_f2_a_refused_draft_is_deferred_not_logged_unmatched`
  - `test_f2_a_spend_stop_leaves_both_texts_queued_and_stops_the_run`
- [tests/test_notes_as_learner_text.py](../../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_c2b_a_note_and_an_ordinary_gap_share_the_gap_readers_route`
- [tests/test_required_method_round3_review.py](../../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f4_model_readers_and_review_exports_render_the_instruction`
- [tests/test_t6_followup_composition.py](../../../../../../../tests/test_t6_followup_composition.py) — direct import
  - `test_text_gap_routes_follow_the_vaults_output_budget_policy`
  - `test_the_seed_unit_is_admitted_at_the_policy_budget`
- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_text_gap_kind_is_reused_never_paid_for_twice`

## Modification guidance

- Change judges policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/text_gaps/judges.py](../../../../../../../src/learnloop/diagnosis/text_gaps/judges.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
