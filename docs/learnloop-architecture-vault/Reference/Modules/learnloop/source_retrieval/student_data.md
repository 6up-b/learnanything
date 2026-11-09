---
title: "learnloop.source_retrieval.student_data"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/student_data.py"
source_paths:
  - "src/learnloop/source_retrieval/student_data.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.student_data module"
  - "src/learnloop/source_retrieval/student_data.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.student_data`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.student_data` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: The query student's training data: synthetic questions from permitted passages (spec_local_contextual_retrieval_v1 §7.1 "Data", "Leakage rules"; Q8; P2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py) |
| Source lines | 621 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `models_off() -> bool` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 91)
- `vault_key(vault: LoadedVault) -> str` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 99)
- `data_dir(data_root: Path, space_id: str, vault: LoadedVault) -> Path` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 104)
- `retrieval_text(question: str, selection: str | None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 109) — The text a query encoder sees: the question, and a selection exactly as the Reader sends it.
- `load_bank(path: Path) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 116) — The frozen E0/E1 bank (its private JSON or JSONL rows, read by key; never imported from ``experiments``): per question its id, retrieval text, family, vault, origin and evidence.
- `bank_supports(bank: Sequence[Mapping[str, Any]]) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 154) — Every gold support of the bank: never in a prompt, never a hard negative.
- `ngrams(text: str, n: int=SP.LEAKAGE_NGRAM) -> set[tuple[str, ...]]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 164) — Word n-grams of the lowercased text; a text shorter than ``n`` is its one n-gram (structural).
- `ngram_overlap(query: str, bank_grams: Sequence[set[tuple[str, ...]]]) -> float` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 174) — The largest share of the query's 5-grams any one bank question holds.
- `passages(vault: LoadedVault, repository: Repository, *, excluded: set[tuple[str, str]], extraction_ids: Iterable[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 184) — Consecutive teaching blocks of one section, at most PASSAGE_TOKENS estimated tokens each, with the bank's gold supports left out (the passage then ends at the gap).
- `family_map(directory: Path | None, repository: Repository, *, persist: bool=True) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 245) — ``{source_id: family}``: sources sharing source bytes or a title stem share a family.
- `extraction_families(repository: Repository, families: Mapping[str, str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 283) — ``{extraction_id: family}`` for the vault's current extractions.
- `question_families(question: Mapping[str, Any], by_extraction: Mapping[str, str]) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 290) — A bank question's families in THIS mapping: those of its evidence's sources (the bank's own family labels are aliases of another tool and never compared, Codex review F8).
- `family_of(passage: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 299)
- `split_of(passage: Mapping[str, Any], held_out: str | None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 303)
- `held_out_family(found: Sequence[Mapping[str, Any]]) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 309) — One family per vault is never trained on (the unseen-source test), when it has two or more.
- `held_out_among(families: Iterable[str]) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 315) — The held-out family among ``families`` (two or more), by a stable hash.
- `vault_held_out(by_extraction: Mapping[str, str]) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 324) — THE vault's held-out family, read by generation and by every dataset build alike (Codex final verify F19, spec §7): the hold-out among the family mapping's current families.
- `current_split(row: Mapping[str, Any], held_out: str | None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 331) — A stored row's split under the CURRENT hold-out (F19, spec §7: a held-out family is never trained on).
- `current_rows(rows: Iterable[Mapping[str, Any]], by_extraction: Mapping[str, str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 344) — Stored rows under the CURRENT family mapping and hold-out (F19, F20): each row's family from its extraction, its split by :func:`current_split`.
- `class GeneratedQuestionV1(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 358)
- `class PassageQuestionsV1(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 366)
- `class GeneratedQuestionsV1(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 371)
- `call_prompt(batch: Sequence[Mapping[str, Any]]) -> tuple[str, dict[str, dict[str, Any]]]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 386) — The call's prompt and ``{passage ref: {"passage": passage, "blocks": {ref: span_id}}}``.
- `validated(answer: GeneratedQuestionsV1, refs: Mapping[str, Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 402) — Each passage's valid questions (unknown refs, empty or overlong text dropped; at most the cap).
- `stored_queries(directory: Path) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 444)
- `done_passages(directory: Path) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 448)
- `query_rows(passage: Mapping[str, Any], questions: Sequence[Mapping[str, Any]], *, split: str, vault: str, bank_grams: Sequence[set[tuple[str, ...]]]) -> tuple[list[dict[str, Any]], int]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 452) — Stored rows for one passage's questions; returns ``(rows, dropped by the 5-gram guard)``.
- `budgets_of(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 473) — How many training questions each nested budget can take today.
- `nested(rows: Sequence[Mapping[str, Any]], budget: int) -> list[Mapping[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 480) — The first ``budget`` training questions by stable rank (nested across budgets by construction).
- `generate(vault: LoadedVault, repository: Repository, *, space_id: str, bank_path: Path | None, data_root: Path | None=None, budget: int=max(SP.BUDGETS), dry_run: bool=False, client: Any | None=None, cancelled: Callable[[], bool]=lambda: False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 495) — Generate (or plan) synthetic questions up to ``budget`` training questions for this vault.

### Module constants

- `TASK` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 71)
- `OWNER_KIND` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 72)
- `PROMPT_VERSION` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 73)
- `MODELS_ENV` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 75)
- `CAP_SETTING` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 76)
- `PRICE_SETTING` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 77)
- `INTENTS` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 78)
- `SHAPES` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 79)
- `SELECTION_LABEL` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 80)
- `DEV_SHARE_DENOMINATOR` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 82)
- `MAX_QUESTION_CHARS` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 84)
- `MAX_RETRIES_PER_CALL` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 86)
- `OUTPUT_TOKENS` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 88)
- `_WORD` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 161)
- `INSTRUCTIONS` ([src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py), line 375)

### Explicit exports

`__all__` declares:

- `CAP_SETTING`
- `GeneratedQuestionsV1`
- `INTENTS`
- `MODELS_ENV`
- `OWNER_KIND`
- `PROMPT_VERSION`
- `SHAPES`
- `TASK`
- `bank_supports`
- `budgets_of`
- `call_prompt`
- `data_dir`
- `extraction_families`
- `family_map`
- `current_rows`
- `current_split`
- `family_of`
- `generate`
- `held_out_among`
- `held_out_family`
- `question_families`
- `vault_held_out`
- `load_bank`
- `nested`
- `ngram_overlap`
- `ngrams`
- `passages`
- `query_rows`
- `retrieval_text`
- `split_of`
- `stored_queries`
- `validated`
- `vault_key`

## Internal implementation anchors

- `_sha(*parts: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 95)
- `_title_stem(title: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 225) — The bank's edition rule (``experiments.contextual_embeddings.corpus``, restated: production never imports experiments): lowercased words, edition and ordinal words dropped, the first six.
- `_family_keys(repository: Repository, extraction_id: str, title: str) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 234)
- `_read_jsonl(path: Path) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 429)
- `_append_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 435)
- `_caps(calls: int, *, subscription: bool, cap: float, passages: int=0) -> SpendCaps` ([source](../../../../../../src/learnloop/source_retrieval/student_data.py), line 489)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `generate`; statically calls `generate`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `module`; statically calls `bank_supports`, `current_rows`, `data_dir`, `extraction_families`, `family_map`, `generate`, `load_bank`, `nested`, `question_families`, `stored_queries`, `vault_held_out`, `vault_key`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `models_off`; statically calls `models_off`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `is_granted`, `quiet`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`; calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/local_embeddings/pins|learnloop.local_embeddings.pins]] — imports `module`; calls `data_root`
- [[Reference/Modules/learnloop/local_embeddings/student_pins|learnloop.local_embeddings.student_pins]] — imports `module`; calls `space_home`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `estimated_call_tokens`, `plan_route`, `resolve_client`, `transport_problem`; calls `PaidCalls`, `estimated_call_tokens`, `plan_route`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `current_extractions`; calls `current_extractions`
- [[Reference/Modules/learnloop/source_retrieval/windows|learnloop.source_retrieval.windows]] — imports `extraction_windows`, `token_estimate`; calls `extraction_windows`, `token_estimate`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `hashlib`, `json`, `os`, `pathlib`, `re`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]], [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]], [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/query_student_fakes.py](../../../../../../tests/query_student_fakes.py) — direct import
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iv_with_the_student_off_rw5ds_grounding_retrieval_is_p1s`
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_a_metered_generator_needs_a_price_and_the_plan_route_is_the_luna_default`
  - `test_a_newly_held_out_familys_older_rows_leave_training`
  - `test_a_run_is_reused_only_on_the_dataset_it_learned`
  - `test_a_student_that_never_becomes_ready_is_late_within_the_time_box_never_a_hang`
  - `test_a_targets_run_interrupted_before_the_bank_shards_admits_no_question`
  - `test_dry_runs_never_write_the_family_mapping`
  - `test_every_recipe_trains_measures_and_writes_a_pinned_checkpoint`
  - `test_families_group_editions_and_bank_questions_by_their_evidence`
  - `test_generation_counts_its_budget_by_the_current_splits`
  - `test_generation_refuses_without_the_bank_and_dry_runs_without_a_call`
  - `test_generation_stores_questions_drops_bank_lookalikes_and_resumes`
  - `test_only_the_current_producers_pinned_families_are_provenance`
  - `test_passages_hold_permitted_text_only_and_never_a_bank_support`
  - `test_priors_never_decide_and_no_evaluation_changes_serving_by_itself`
  - `test_reevaluation_strata_come_from_the_checkpoint_training_families`
  - `test_targets_are_one_metered_query_batch_with_the_canaries_and_the_cosine_guard`
  - `test_the_adopted_student_starts_lazily_serves_and_queues_the_teacher_replay`
  - `test_the_kill_switches_take_the_student_and_the_replay_out`
  - `test_the_pinned_families_are_every_family_the_run_consumed`
  - `test_the_resolver_serves_the_adopted_student_and_never_waits_for_a_zero_weight_cold_start`
  - `test_the_scheduled_candidate_is_recommended_adopted_and_a_lost_reevaluation_recommends_withdrawal`
  - `test_the_serving_checkpoint_is_reevaluated_on_corrected_labels`
  - `test_training_candidates_hold_training_families_only_and_no_bank_tainted_window`

## Modification guidance

- Make changes here when the responsibility remains student data within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/student_data.py](../../../../../../src/learnloop/source_retrieval/student_data.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
