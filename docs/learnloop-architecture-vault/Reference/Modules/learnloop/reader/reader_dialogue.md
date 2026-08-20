---
title: "learnloop.reader.reader_dialogue"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_dialogue.py"
source_paths:
  - "src/learnloop/reader/reader_dialogue.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_dialogue module"
  - "src/learnloop/reader/reader_dialogue.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_dialogue`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_dialogue` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: P2 step B.11 -- minimal bidirectional reader dialogue (U-033, spec §7.6).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py) |
| Source lines | 1039 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ReaderDialogueError(ValueError)` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 129)
- `reader_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 133) — Launch default OFF (§12.3.2): the golden path completes without the reader.
- `reader_prompt_contract() -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 146) — The owner-reviewable ``reader`` prompt/manifest contract (design A.2).
- `build_reader_manifest(repository: Repository, *, extraction_id: str, span_id: str, question_md: str, answer_mode: str, goal_invariants: Mapping[str, Any] | None=None, selection_span_ids: Sequence[str]=(), selection_quote_md: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 187) — The exact bounded context handed to the reader tutor (design A.2).
- `set_answer_mode(repository: Repository, *, extraction_id: str, span_id: str, answer_mode: str, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 244) — Log the per-ask answer-mode toggle (``reader_answer_mode_set``).
- `set_mode(repository: Repository, *, mode: str, extraction_id: str | None=None, session_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 267) — Set the reading mode (skim/anchor/incremental, §5.1).
- `question_control(repository: Repository, *, control: str, administration_id: str | None=None, subject_id: str | None=None, subject_type: str='reader_span', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 296) — Record a per-question control (§5.1).
- `ask(vault: LoadedVault, repository: Repository, client: Any, *, extraction_id: str, span_id: str, question_md: str, answer_mode: str=READER_ANSWER_MODE_DEFAULT, target_key: str | None=None, goal_invariants: Mapping[str, Any] | None=None, revealed_surface_ids: Sequence[str]=(), selection_span_ids: Sequence[str]=(), selection_quote_md: str | None=None, cold_active: bool=False, cold_attempt_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 391) — Answer a span-grounded reader question (§7.6).
- `ask_history(repository: Repository, *, extraction_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 580) — Return every completed Reader Ask for one extraction, newest first.
- `administer_reading_question(vault: LoadedVault, repository: Repository, item: Any, *, reading_phase: str, goal_id: str | None=None, target_contract_version_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 653) — Render an owner-placed reading question as an instructional administration (§7.6): ``source_visible=true`` + a ``reading_phase``, no new activity kind.
- `skip_reading_question(repository: Repository, *, administration_id: str, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 723) — A skip is an interaction-policy signal, NEVER low-ability evidence (§7.6).
- `submit_reading_question(repository: Repository, *, administration_id: str, response_md: str | None=None, target_key: str | None=None, outcome_class: str='unknown', clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 743) — Record an answer to an owner-placed reading question (source_visible instructional; primes/scaffolds, never cold evidence).
- `choose_disposition(vault: LoadedVault, repository: Repository, *, disposition: str, subject_id: str, subject_type: str='reader_span', commitment_target: Mapping[str, Any] | None=None, goal_id: str | None=None, client_idempotency_key: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 777) — Apply one of the four reading dispositions -- and nothing else (§7.6).
- `restore_source(repository: Repository, *, extraction_id: str, span_id: str, cold_surface_id: str | None=None, cold_administration_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 846) — Restore a source span during reading.
- `routing_prior_projection_v1(repository: Repository, *, target_key: str, as_of: str | None=None, cold_observation_at: str | None=None, halflife_days: float | None=None, max_weight: float | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 903) — Fold ``reader_answer_submitted`` events for ``target_key`` into a bounded, replay-derived routing prior (design A.1 / spec §7.6 evidence semantics).
- `class StubReaderClient` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 1005) — A deterministic ``reader`` tutor client (U-034 stub).
  - `__init__(self, *, answer_md: str='Grounded in the span in view.') -> None` (line 1013; internal)
  - `supports(self, capability: str) -> bool` (line 1017; public)
  - `complete(self, request: StructuredRequest[Any]) -> TutorAnswer` (line 1020; public)

### Module constants

- `READER_MODES` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 64)
- `READER_QUESTION_CONTROLS` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 69)
- `ROUTING_PRIOR_HALFLIFE_DAYS` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 77)
- `ROUTING_PRIOR_MAX_WEIGHT` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 78)
- `READER_QUESTION_DENSITY_TARGET` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 81)
- `READER_REVEAL_OVERLAP_THRESHOLD` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 86)
- `READER_ANSWER_MODES` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 88)
- `READER_ANSWER_MODE_DEFAULT` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 89)
- `READER_DISPOSITIONS` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 93)
- `READER_EVENT_KINDS` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 101)
- `READING_PHASES` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 112)
- `READER_PROMPT_CONTRACT_VERSION` ([src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py), line 114)

## Internal implementation anchors

- `_normalize_tokens(text: str) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 325)
- `_bigrams(tokens: Sequence[str]) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 329)
- `_verbatim_overlap(answer_md: str, statement: str) -> float` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 333) — Cheap word-bigram overlap: the share of a reserved statement's bigrams that appear in the answer (no LLM, L3).
- `_surface_statement_text(surface_row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 344)
- `_detect_revealed_reserves(repository: Repository, *, answer_md: str, citations: Sequence[Mapping[str, Any]], caller_supplied: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 354) — Server-side reveal detection (L3): map the answer's text + validated citations against every LIVE assessment reserve by surface_hash / fingerprint / verbatim overlap (>= ``READER_REVEAL_OVERLAP_THRESHOLD``).
- `_record_cold_hint_equivalent(repository: Repository, *, cold_attempt_id: str, question_md: str, answer_md: str | None, span_key: str, clock: Clock | None) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 615) — Record the cold reader Ask as a hint-equivalent PRACTICE question_event tied to the cold attempt's (item, session), so the practice evidence path counts it (L6).
- `_days_between(start_iso: str, end_iso: str) -> float` ([source](../../../../../../src/learnloop/reader/reader_dialogue.py), line 995)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]] — imports `module`; statically calls `restore_source`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `administer_reading_question`, `ask`, `ask_history`, `choose_disposition`, `question_control`, `reader_enabled`, `reader_prompt_contract`, `restore_source`, `routing_prior_projection_v1`, `set_answer_mode`, `set_mode`, `skip_reading_question`, `submit_reading_question`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `create_commitment`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/familiarity|learnloop.learner.familiarity]] — imports `module`; calls `propagate_tutor_exposure`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `SpanViewError`, `build_span_view`; calls `build_span_view`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `append_exposure`, `log_interaction_event`, `open_administration`, `reserve_surface`, `resolve_legacy_item`; calls `append_exposure`, `log_interaction_event`, `open_administration`, `reserve_surface`, `resolve_legacy_item`
- [[Reference/Modules/learnloop/substrate/administration_adapters|learnloop.substrate.administration_adapters]] — imports `module`; calls `resolve_adapter`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `TutorAnswer`, `TutorCitation`, `TutorQAContext`; calls `TutorAnswer`, `TutorCitation`, `TutorQAContext`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `module`; calls `_reader_source_spans`, `ask_question`, `reader_span_key`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_p3_journeys.py](../../../../../../tests/test_p3_journeys.py) — direct import
  - `test_journey1_reading_first_session`
  - `test_journey7_tutor_exchange_to_durable`
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_answer_not_quoting_reserve_leaves_it_eligible`
  - `test_answer_quoting_reserved_surface_burns_it_without_caller_id`
  - `test_ask_answers_logs_new_kinds_and_persists_the_exchange`
  - `test_ask_is_never_ability_evidence`
  - `test_ask_warms_and_invalidates_a_revealed_reserve`
  - `test_cold_active_ask_links_a_hint_equivalent_into_attempt_accounting`
  - `test_each_disposition_produces_its_mechanism_and_nothing_else`
  - `test_golden_path_completes_with_reader_never_invoked`
  - `test_manifest_carries_full_multiblock_selection`
  - `test_manifest_carries_span_and_mode_but_never_ability_or_reserved`
  - `test_owner_placed_question_is_instructional_source_visible_reading_phase`
  - `test_prompt_contract_is_deterministic_and_walls_off_ability`
  - `test_reader_answer_writes_no_posterior_or_fsrs`
  - `test_real_reader_writes_carry_the_salience_firewall_stamp`
  - `test_restore_source_during_cold_burns_eligibility`
  - `test_routing_prior_decays_with_elapsed_time`
  - `test_routing_prior_is_heuristic_decision_aid`
  - `test_routing_prior_superseded_by_cold_observation_before_the_reading_answer`
  - `test_routing_prior_superseded_by_first_cold_observation`
  - `test_skip_is_interaction_policy_not_low_ability`
- [tests/test_reader_guidance.py](../../../../../../tests/test_reader_guidance.py) — direct import
  - `test_dont_bring_this_back_suppresses_the_exact_reviewed_placement`
- [tests/test_sidecar_serializer_snapshot.py](../../../../../../tests/test_sidecar_serializer_snapshot.py) — direct import
  - `test_queue_practice_and_reader_wire_snapshots`

## Modification guidance

- Change reader dialogue policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_dialogue.py](../../../../../../src/learnloop/reader/reader_dialogue.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
