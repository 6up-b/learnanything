---
title: "learnloop.tutor.tutor_qa"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tutor/tutor_qa.py"
source_paths:
  - "src/learnloop/tutor/tutor_qa.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.tutor"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.tutor.tutor_qa module"
  - "src/learnloop/tutor/tutor_qa.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-tutor"
---

# `learnloop.tutor.tutor_qa`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.tutor.tutor_qa` exists within [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] to own the behavior summarized by its module contract: Tutor Q&A ("ask"): classified learner questions in three contexts.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py) |
| Source lines | 2733 |
| Owning package | [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `ask_panel_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 163) — Reader CA2's presentation switch (``ask.panel_enabled``): off, Ask is exactly as before (the overlay, the Reader's per-source mode, no mode in the practice prompt, the practice thread and budget of B3).
- `help_style_answer_mode(help_style: str | None) -> str` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 171) — The answer mode a help style asks for (unknown: *balanced*'s).
- `request_tutor_answer(client: OperationClient, context: TutorQAContext, *, tools: bool=False) -> TutorAnswer` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 177) — Run the feature-owned tutor-Q&A operation (``tools``: S4's request field; a :class:`ReaderTutorQAContext`: RW1c's three answer modes).
- `tutor_show_me_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 317) — RW5d P1: the Reader tutor may write an optional ``figure_goal`` only while RW5b's tutor offers are on and ``figures.show_me_enabled``; off, its prompt and output are RW5b's (G-SM7).
- `tutor_explorable_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 327) — RW5b: the Reader tutor judges ``explorable`` on cited equation and figure blocks only while figure offers are on and RW1c's offers (the buttons under an answer, where "make this explorable" shows) are on.
- `reader_span_key(extraction_id: str, span_id: str) -> str` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 338) — The persistence/budget key for a reader exchange: one source block span.
- `class TutorQAError(ValueError)` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 368)
- `class HeldOutMaterialRefused(TutorQAError)` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 372) — A Reader question about held-out material (exam protection, 2026-10-13): refused before anything is written or sent, with the learner-facing reason.
- `class QuestionLimitReached(Exception)` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 378)
  - `__str__(self) -> str` (line 383; internal)
- `practice_thread_events(repository: Repository, *, practice_item_id: str | None, session_id: str | None, submission_id: str | None=None, workbench_session_id: str | None=None, aliases: AttemptAliases | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 390) — The practice Ask thread of the attempt being composed: the answered practice questions on (item, session) asked since the item's last attempt (owner capture 2026-10-25, B3).
- `class AttemptAliases` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 438) — The other identities of the one attempt in progress a practice question names (Astra batch review, Medium): the answer box's draft keys handed into Work in Steps and the workbenches they were handed into, as the caller resolved them (``reader.workbench.attempt_identities``; this…
- `attempt_key_matches(event: Mapping[str, Any], *, submission_id: str | None, workbench_session_id: str | None, session_id: str | None=None) -> bool` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 458) — Whether a practice question belongs to the attempt in progress that ``submission_id`` (the answer box's key, or a workbench's ``workbench:<id>``) and ``workbench_session_id`` name (Reader CA2, K5; Codex review F6: the server's identity, the same in every host).
- `attempt_key_of(event: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 472) — The attempt key a practice question was asked under (Reader CA2, ``source_context.attempt_key``), or ``{}`` for one recorded before it.
- `earlier_threads(vault: LoadedVault, repository: Repository, *, practice_item_id: str, limit: int=EARLIER_THREADS_LIMIT) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 486) — Reader CA2 (§7.3, K6): the item's earlier attempts' help, newest first, read-only and never current.
- `question_usage(vault: LoadedVault, repository: Repository, *, context: str, practice_item_id: str | None=None, attempt_id: str | None=None, note_id: str | None=None, session_id: str | None=None, clock: Clock | None=None, submission_id: str | None=None, workbench_session_id: str | None=None, metered: bool=True, aliases: AttemptAliases | None=None) -> tuple[int, int | None]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 585) — (used, limit) for one Q&A budget window.
- `ask_question(vault: LoadedVault, repository: Repository, client: Any, *, context: str, question_md: str, practice_item_id: str | None=None, attempt_id: str | None=None, note_id: str | None=None, session_id: str | None=None, seconds_into_attempt: float | None=None, question_context: Mapping[str, Any] | None=None, extraction_id: str | None=None, span_id: str | None=None, answer_mode: str | None=None, selection_span_ids: Sequence[str]=(), selection_quote_md: str | None=None, question_event_id: str | None=None, source_span_provider: SourceSpanProvider | None=None, learning_object_suggester: LearningObjectSuggester | None=None, reader_thread: Sequence[Mapping[str, Any]] | None=None, tool_request_handler: Callable[..., list[dict[str, Any]]] | None=None, learner_draft_md: str | None=None, linked_reference_filter: LinkedReferenceFilter | None=None, reader_tutor: reader_modes.ReaderTutorRequest | None=None, reader_caller: Mapping[str, Any] | None=None, reader_binding: reader_modes.BoundAsk | None=None, submission_id: str | None=None, workbench_session_id: str | None=None, about_step: int | None=None, count_every_question: bool=False, attempt_aliases: AttemptAliases | None=None, worked_help_check: Callable[[str, Any], Sequence[str]] | None=None, reader_learner_state: Any=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 751) — ``question_context`` carries the §13.4 generating-process fields (preceding_tutor_move, scaffold_level, warning_state, learner_mode, question_opportunity, hints_used_before, direct_explanation_request, attempt_progress).
- `build_tutor_opening(vault: LoadedVault, repository: Repository, client: Any, *, practice_item_id: str, linked_reference_filter: LinkedReferenceFilter | None=None) -> str | None` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1594) — A proactive tutor opening for a just-closed diagnostic block (§12.1).
- `hint_equivalents_for_submission(repository: Repository, practice_item_id: str, session_id: str | None, *, until: str | None=None, item_window_only: bool=False) -> int` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1635) — Hint-equivalent questions since the item was last attempted.
- `hint_equivalents_for_attempt(repository: Repository, attempt: dict[str, Any]) -> int` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1661) — Reconstruct a graded attempt's question-hint count from persisted rows.
- `answer_leak_overlap(answer_md: str, expected_answer: str | dict[str, Any]) -> float` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1685) — How much of the expected answer the tutor's answer exposed (0..1).
- `answer_leaks_expected(answer_md: str, expected_answer: str | dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1715) — Heuristic answer-leak telemetry: did the tutor give the answer away?
- `span_answer_overlap(text: str, expected_answer: str | dict[str, Any]) -> float` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1731) — How much of the expected answer a source span exposes (0..1).
- `span_leaks_expected(text: str, expected_answer: str | dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1763) — A source span that gives the expected answer away (withheld from the tutor).
- `tutor_qa_note_title(question_md: str) -> str` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1787)
- `build_tutor_qa_note(vault: LoadedVault, repository: Repository, event: Mapping[str, Any], *, subject_id: str | None=None, related_lo_ids: list[str] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1794) — Materialize a tutor Q&A turn as a vault note and persist the back-link.
- `withheld_record(answer_md: str | None, leaks: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2045) — What a question row keeps of a withheld worked answer (Codex re-review F12): why it was withheld and a digest of the text (sha256 and length, as ``help_assists`` keeps the learner's work), never the text itself.
- `answer_withheld(event: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2060) — Whether a stored question's answer was withheld as worked help (F2, F12).
- `delivered_answer_md(event: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2066) — The answer the learner was shown for a stored question: a withheld worked answer (Codex review F2) reads as its take step, never the text.

### Module constants

- `QUESTION_CONTEXTS` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 126)
- `READER_ANSWER_MODES` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 142)
- `READER_ANSWER_MODE_DEFAULT` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 143)
- `HELP_STYLE_ANSWER_MODES` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 147)
- `ANSWER_MODE_LABELS` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 153)
- `HELP_STYLE_MODE_CONTEXTS` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 160)
- `HINT_EQUIVALENT_TYPES` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 352)
- `_LEAK_MIN_TOKENS` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 354)
- `_LEAK_OVERLAP_THRESHOLD` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 355)
- `_MAX_CITATION_SPANS` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 359)
- `_MAX_SELECTION_SPANS` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 363)
- `DEFAULT_CONTEXT_TOKEN_BUDGET` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 365)
- `EARLIER_THREADS_LIMIT` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 483)
- `CITATION_EXCERPT_CHARS` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1576)
- `_SHORT_ANSWER_MAX_TOKENS` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1728)
- `WORKED_HELP_TAKE_LEVELS` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2021)
- `WITHHELD_ANSWER_MD` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2023)
- `WITHHELD_NOT_SAVED` ([src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2030)

## Internal implementation anchors

- `_answer_model(context: TutorQAContext, *, tools: bool) -> type[TutorAnswer]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 196)
- `_prompt_version(context: TutorQAContext, *, tools: bool) -> str` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 210)
- `_base_prompt_version(context: TutorQAContext, *, tools: bool) -> str` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 218)
- `_record_explorable_verdicts(repository: Repository, event_id: str, answer: Any, *, model: str | None, prompt_version: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 235) — RW5b (Codex review F3): the tutor's ``explorable`` verdicts, one ``judgment_ledger`` row per judged block (task ``figure_explorable``), as every LLM verdict is.
- `_record_figure_goal(repository: Repository, event_id: str, goal: Mapping[str, Any], *, model: str | None, prompt_version: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 277) — RW5d P1 (Codex review F6): the tutor's figure goal is an LLM judgment (a figure would help this question), so it gets its ``judgment_ledger`` row as RW5b's ``explorable`` verdicts do: task ``figure_goal_offer``, the model and prompt version, the input's identity (prompt version…
- `_key_in(event: Mapping[str, Any], submission_ids: frozenset[str] | set[str], workbench_ids: frozenset[str] | set[str], *, session_id: str | None) -> bool` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 450)
- `_attempt_outcome(attempt: Mapping[str, Any], max_points: int | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 540) — How an attempt ended, in the evidence vocabulary: left unfinished, with help, or on your own (no correctness cut: the score is shown as it is).
- `_attempt_hints(repository: Repository, item: Any, attempt_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 558) — The hints an attempt took (``help_assists`` rows shown and attached to it), in order; an authored reveal's text is the item's own hint.
- `_record_dialogue_causal_signals(vault: LoadedVault, repository: Repository, *, answer: Any, attempt_id: str | None, practice_item_id: str | None, question_event_id: str, remediation_episode_id: str | None, leak_overlap: float, model: str | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 655) — Fold what the learner's question revealed back into the causal record.
- `_question_contract(vault: LoadedVault, repository: Repository, item: Any, attempt_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1480) — The contract (revision) of the item a question is asked about (Q10): for a question about a graded attempt the repository records the attempt's pinned contract; mid-attempt it is the item as presented (``assessment_contracts.snapshot_for_presentation``, content-addressed).
- `_learner_gap_reading(answer: Any, *, model: Any=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1497) — The tutor's named gap, trimmed, with the prompt it was read under.
- `_record_retrieval_citations(vault: LoadedVault, repository: Repository, source_context: Mapping[str, Any] | None, citations: list[dict[str, Any]]) -> None` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1517) — Local contextual retrieval P1 (spec §9.2): a validated citation is a relevance signal on the span the tutor's search delivered.
- `_validated_citations(answer: Any, source_spans: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1544) — Keep only citations naming a span actually provided in context (§9.2).
- `_with_excerpts(citations: list[dict[str, Any]], source_spans: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1579) — Codex review F9 (K11): each citation with its passage's text as the tutor was given it (cut to :data:`CITATION_EXCERPT_CHARS`).
- `_cited_span_overlap(citations: Sequence[Mapping[str, Any]], source_spans: Sequence[Mapping[str, Any]], expected_answer: str | dict[str, Any]) -> float` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1769) — The largest expected-answer overlap among the cited source spans.
- `_normalize(text: str) -> str` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1868)
- `_prerequisite_learning_objects(vault: LoadedVault, anchors: Sequence[str]) -> set[str]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1872) — LOs on the concepts the anchor LOs declare as prerequisites.
- `_grounded_facet_targets(vault: LoadedVault, repository: Repository, facets: Sequence[str], *, question_type: str, item: PracticeItem | None, note: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1895) — The question-time facet -> LO mapping, grounded in the question's context.
- `_candidate_facets(vault: LoadedVault, repository: Repository, context: str, *, item: PracticeItem | None, note) -> list[str]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1956)
- `_thread(repository: Repository, *, context: str, practice_item_id: str | None, attempt_id: str | None, note_id: str | None, session_id: str | None, submission_id: str | None=None, workbench_session_id: str | None=None, aliases: AttemptAliases | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 1974)
- `_worked_help_leaks(check: Callable[[str, Any], Sequence[str]], answer_md: str | None, item: Any) -> list[str]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2033) — The hint service's leak control for an Ask answer at levels 1-3 (hints spec §4.6, through the adapter's ``check``): why the text would give the item's answer away, empty when it does not.
- `_with_step_focus(learner_draft_md: str | None, about_step: int | None) -> str | None` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2075) — Reader CA2 (§7.6): a question asked under one step says so to the tutor (the steps stay the learner's work, as B1 sends them).
- `_tutor_context_hash(context: TutorQAContext) -> str` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2084)
- `_build_context(vault: LoadedVault, repository: Repository, *, context: str, question_md: str, candidates: list[str], thread: list[dict[str, Any]], item: PracticeItem | None, attempt: dict[str, Any] | None, note, note_id: str | None, extraction_id: str | None=None, span_id: str | None=None, answer_mode: str | None=None, selection_span_ids: Sequence[str]=(), selection_quote_md: str | None=None, provided_source_spans: list[dict[str, Any]] | None=None, learner_draft_md: str | None=None, reader_withheld: Any=None, delivery_receipt: dict[str, Any] | None=None, linked_reference_filter: LinkedReferenceFilter | None=None, reader_lookup: tuple[Any, Mapping[str, Any], Any] | None=None, reader_binding: reader_modes.BoundAsk | None=None, now_iso: str | None=None) -> TutorQAContext` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2089) — The tutor's context.
- `_reader_lookup_context(repository: Repository, reader_spans: list[dict[str, Any]], reader_lookup: tuple[Any, Mapping[str, Any], Any], *, question_md: str, thread: list[dict[str, Any]], answer_mode: str | None, withheld: Any, delivery_receipt: dict[str, Any] | None, budget_tokens: int, expanded: bool, guard: Any=None, guarded: Mapping[str, int] | None=None, explorable: bool=False, show_me: bool=False) -> ReaderTutorQAContext` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2277) — RW1c's Reader context: the selection and its neighbours first, then the retrieved passages (each its complete canonical block unless ``tutor_qa.expanded_delivery`` is off; a held-out one never), all within ``tutor_qa.context_token_budget``; and what the three modes need (``books…
- `_delivered_source_spans(vault: LoadedVault, repository: Repository, *, context: str, item: PracticeItem | None, lo_ids: list[str], provided_source_spans: list[dict[str, Any]] | None, delivery_receipt: dict[str, Any] | None, linked_reference_filter: LinkedReferenceFilter | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2370) — A practice, feedback or library turn's source spans, as delivered.
- `_context_learning_objects(item: PracticeItem | None, note: Any) -> list[str]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2429) — The LOs a non-reader question is about: its item's, or its note's related LOs.
- `_provided_source_spans(vault: LoadedVault, repository: Repository, provider: SourceSpanProvider, *, context: str, question_md: str, learning_object_ids: list[str], item: PracticeItem | None) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2439) — The injected span provider's choice; any failure keeps the linked spans.
- `_suggested_learning_objects(vault: LoadedVault, repository: Repository, suggester: LearningObjectSuggester, *, extraction_id: str, span_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2474)
- `_source_spans(vault: LoadedVault, repository: Repository, lo_ids: list[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2490) — Bounded semantic-authority source spans for the LO(s) in tutor context (§9.2).
- `_reader_source_spans(repository: Repository, extraction_id: str | None, span_id: str | None, *, selection_span_ids: Sequence[str]=(), selection_quote_md: str | None=None, withheld: Any=None, budget_tokens: int=DEFAULT_CONTEXT_TOKEN_BUDGET, resolve_references: bool=True, expanded: bool=True) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2517) — The reader manifest's citable spans (:func:`_reader_delivery`).
- `_reader_delivery(repository: Repository, extraction_id: str | None, span_id: str | None, *, selection_span_ids: Sequence[str]=(), selection_quote_md: str | None=None, withheld: Any=None, budget_tokens: int=DEFAULT_CONTEXT_TOKEN_BUDGET, resolve_references: bool=True, expanded: bool=True) -> tuple[list[dict[str, Any]], dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2538) — Block-level spans for the reader manifest (§7.6) and their delivery receipt.
- `_predecessor_reader_delivery(text: Any, primary: int, spans: list[dict[str, Any]], cited: References, refused: BlockFilter, budget_tokens: int) -> tuple[list[dict[str, Any]], dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2641) — The predecessor's Reader window (``tutor_qa.expanded_delivery = false``).
- `_diagnostic_decision_for(vault: LoadedVault, repository: Repository, item: PracticeItem | None, context: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2681) — The §12.1 typed transition decision steering post-diagnosis tutoring.
- `_grading_evidence_rows(repository: Repository, attempt_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/tutor_qa.py), line 2719)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `span_leaks_expected`; statically calls `span_leaks_expected`
- [[Reference/Modules/learnloop/hints/contracts|learnloop.hints.contracts]] — imports `answer_leaks_expected`; statically calls `answer_leaks_expected`
- [[Reference/Modules/learnloop/hints/maps|learnloop.hints.maps]] — imports `span_leaks_expected`; statically calls `span_leaks_expected`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `span_answer_overlap`; statically calls `span_answer_overlap`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `answer_leaks_expected`, `span_leaks_expected`; statically calls `answer_leaks_expected`, `span_leaks_expected`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `span_leaks_expected`; statically calls `span_leaks_expected`
- [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]] — imports `answer_leak_overlap`; statically calls `answer_leak_overlap`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; statically calls `HeldOutMaterialRefused`, `_reader_source_spans`, `ask_question`, `delivered_answer_md`, `reader_span_key`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `span_leaks_expected`; statically calls `span_leaks_expected`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `span_leaks_expected`; statically calls `span_leaks_expected`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `span_answer_overlap`, `span_leaks_expected`; statically calls `span_answer_overlap`, `span_leaks_expected`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `span_leaks_expected`; statically calls `span_leaks_expected`
- [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] — imports `span_leaks_expected`; statically calls `span_leaks_expected`
- [[Reference/Modules/learnloop/teacher/guards|learnloop.teacher.guards]] — imports `span_answer_overlap`, `span_leaks_expected`; statically calls `span_answer_overlap`, `span_leaks_expected`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `answer_leak_overlap`, `span_answer_overlap`; statically calls `answer_leak_overlap`, `span_answer_overlap`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `_thread`, `build_tutor_qa_note`, `delivered_answer_md`; statically calls `_thread`, `build_tutor_qa_note`, `delivered_answer_md`
- [[Reference/Modules/learnloop/tutor/question_queue|learnloop.tutor.question_queue]] — imports `_source_spans`, `delivered_answer_md`; statically calls `_source_spans`, `delivered_answer_md`
- [[Reference/Modules/learnloop/tutor/reader_modes|learnloop.tutor.reader_modes]] — imports `span_leaks_expected`; statically calls `span_leaks_expected`
- [[Reference/Modules/learnloop/workbench/passage_draw|learnloop.workbench.passage_draw]] — imports `span_leaks_expected`; statically calls `span_leaks_expected`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `span_leaks_expected`; statically calls `span_leaks_expected`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `HeldOutMaterialRefused`, `QuestionLimitReached`, `TutorQAError`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `hint_equivalents_for_submission`; statically calls `hint_equivalents_for_submission`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `QuestionLimitReached`, `TutorQAError`, `ask_panel_enabled`, `help_style_answer_mode`; statically calls `ask_panel_enabled`, `help_style_answer_mode`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `hint_equivalents_for_attempt`; statically calls `hint_equivalents_for_attempt`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `AttemptAliases`, `QuestionLimitReached`, `READER_ANSWER_MODES`, `TutorQAError`, `WITHHELD_NOT_SAVED`, `answer_withheld`, `ask_panel_enabled`, `ask_question`, `build_tutor_opening`, `build_tutor_qa_note`, `delivered_answer_md`, `earlier_threads`, `help_style_answer_mode`, `hint_equivalents_for_submission`, `practice_thread_events`, `question_usage`; statically calls `AttemptAliases`, `answer_withheld`, `ask_panel_enabled`, `ask_question`, `build_tutor_opening`, `build_tutor_qa_note`, `delivered_answer_md`, `earlier_threads`, `help_style_answer_mode`, `hint_equivalents_for_submission`, `practice_thread_events`, `question_usage`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `hint_equivalents_for_submission`; statically calls `hint_equivalents_for_submission`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `finish_agent_run`; calls `finish_agent_run`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `is_subscription_transport`; calls `is_subscription_transport`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `record_reveal`, `reveal_episode_id`; calls `record_reveal`, `reveal_episode_id`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]] — imports `module`; calls `safe_learner_events`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `TutorQAConfig`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `build_cross_source_spans`; calls `build_cross_source_spans`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `held_out_among`, `held_out_material`, `held_out_refusal`; calls `held_out_among`, `held_out_material`, `held_out_refusal`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `objective_receipts_on`; calls `objective_receipts_on`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `judgments_by_ids`; calls `judgments_by_ids`
- [[Reference/Modules/learnloop/db/stores/retrieval_spaces|learnloop.db.stores.retrieval_spaces]] — imports `has_tables`, `record_citation_signals`; calls `has_tables`, `record_citation_signals`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `append_dialogue_candidate`; calls `append_dialogue_candidate`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `record_learner_embedded_prediction`; calls `record_learner_embedded_prediction`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `FIGURE_GOAL_OFFERED`, `TUTOR_EXPLORABLE_TASK`, `TUTOR_FIGURE_GOAL_TASK`, `explorable_yes`, `figure_goal_digest`, `offerable_blocks`, `offers_enabled`, `show_me_enabled`, `tutor_explorable_judgment_id`, `tutor_figure_goal_judgment_id`; calls `explorable_yes`, `figure_goal_digest`, `offerable_blocks`, `offers_enabled`, `show_me_enabled`, `tutor_explorable_judgment_id`, `tutor_figure_goal_judgment_id`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `snapshot_for_presentation`; calls `snapshot_for_presentation`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `required_facets`, `scope_facets`; calls `required_facets`, `scope_facets`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `servable_open_episode`; calls `servable_open_episode`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`; calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/router_objective/question_state|learnloop.router_objective.question_state]] — imports `module`; calls `fields_at_ask`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `READER_LEARNER_STATE_SUFFIX`, `READER_TUTOR_EXPLORABLE_PROMPT_VERSION`, `READER_TUTOR_EXPLORABLE_SHOW_ME_PROMPT_VERSION`, `READER_TUTOR_EXPLORABLE_SHOW_ME_TOOLS_PROMPT_VERSION`, `READER_TUTOR_EXPLORABLE_TOOLS_PROMPT_VERSION`, `READER_TUTOR_PROMPT_VERSION`, `READER_TUTOR_SHOW_ME_PROMPT_VERSION`, `READER_TUTOR_SHOW_ME_TOOLS_PROMPT_VERSION`, `READER_TUTOR_TOOLS_PROMPT_VERSION`, `ReaderTutorAnswer`, `ReaderTutorAnswerWithTools`, `ReaderTutorExplorableAnswer`, `ReaderTutorExplorableAnswerWithTools`, `ReaderTutorExplorableQAContext`, `ReaderTutorExplorableShowMeAnswer`, `ReaderTutorExplorableShowMeAnswerWithTools`, `ReaderTutorExplorableShowMeQAContext`, `ReaderTutorQAContext`, `ReaderTutorShowMeAnswer`, `ReaderTutorShowMeAnswerWithTools`, `ReaderTutorShowMeQAContext`, `TUTOR_QA_ANSWER_MODE_SUFFIX`, `TUTOR_QA_PROMPT_VERSION`, `TUTOR_QA_TOOLS_PROMPT_VERSION`, `TutorAnswer`, `TutorAnswerWithTools`, `TutorQAContext`, `reader_learner_state_on`, `tutor_context_payload`, `tutor_qa_prompt`; calls `TutorQAContext`, `reader_learner_state_on`, `tutor_context_payload`, `tutor_qa_prompt`
- [[Reference/Modules/learnloop/tutor/context_delivery|learnloop.tutor.context_delivery]] — imports `BlockFilter`, `BlockSource`, `MAX_REFERENCES`, `NEIGHBOUR_RADIUS`, `PREDECESSOR_RADIUS`, `PREVIEW_CHARS`, `References`, `SPAN_CHARS`, `apply_budget`, `follow_references`, `hydrate`, `neighbour_order`, `notable`, `passage_label`, `predecessor_cut`, `predecessor_window`; calls `BlockSource`, `References`, `apply_budget`, `follow_references`, `hydrate`, `neighbour_order`, `notable`, `passage_label`, `predecessor_cut`, `predecessor_window`
- [[Reference/Modules/learnloop/tutor/reader_modes|learnloop.tutor.reader_modes]] — imports `module`; calls `deliver`, `displayed_text`, `finalize`, `plan_bound_delivery`, `run_retrieval`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `add_note`; calls `add_note`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `presented_prompt`; calls `presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `logging`, `re`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]], [[Reference/Modules/learnloop/hints/contracts|learnloop.hints.contracts]], [[Reference/Modules/learnloop/hints/maps|learnloop.hints.maps]], [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]], [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] and 21 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad1_fix_round4.py](../../../../../../tests/test_ad1_fix_round4.py) — direct import
  - `test_a_reader_tutor_exchange_is_recorded_under_its_answer_mode`
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_i_a_figure_goal_from_the_ask_rail_or_the_tutor_never_spends_an_ask_question`
  - `test_iii_a_figure_grant_never_meters_an_ask_and_an_ask_grant_meters_it_under_the_cap`
- [tests/test_capture_route_recovery.py](../../../../../../tests/test_capture_route_recovery.py) — direct import
  - `test_purge_during_tutor_answer_does_not_restore_capture`
  - `test_tutor_ai_does_not_hold_a_sqlite_writer`
- [tests/test_diagnosis_input_provenance.py](../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_the_tutor_records_the_contract_a_mid_attempt_question_is_about`
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_a_method_explicit_question_records_the_contract_it_was_presented_with`
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
- [tests/test_e0_delivery.py](../../../../../../tests/test_e0_delivery.py) — direct import
  - `test_d0_and_d1_reproduce_the_production_reader_delivery`
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_reader_question_about_held_out_material_is_refused_before_anything_is_sent`
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_a_held_out_assessment_signal_is_held_out_for_the_reader_and_the_gate_alike`
  - `test_the_switch_never_reaches_what_a_model_is_shown`
- [tests/test_field_signal_production_paths.py](../../../../../../tests/test_field_signal_production_paths.py) — direct import
  - `test_library_question_targets_only_its_notes_learning_objects`
- [tests/test_figure_offers.py](../../../../../../tests/test_figure_offers.py) — direct import
  - `test_the_tutor_context_asks_for_explorable_only_with_a_block_to_judge`
  - `test_the_tutor_prompt_adds_explorable_only_in_its_own_version`
- [tests/test_figures_rw5b_fix_round2.py](../../../../../../tests/test_figures_rw5b_fix_round2.py) — direct import
  - `test_the_tutors_explorable_rows_hash_the_input_not_the_verdict`
- [tests/test_figures_rw5b_review.py](../../../../../../tests/test_figures_rw5b_review.py) — direct import
  - `test_the_tutor_context_marks_each_equation_and_figure_block`
- [tests/test_learner_text_gaps.py](../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_a_library_question_is_anchored_by_its_notes_single_learning_object`
- [tests/test_learner_text_gaps_composition.py](../../../../../../tests/test_learner_text_gaps_composition.py) — direct import
  - `test_t6_verified_spans_and_the_tutors_named_gap_both_hold`
  - `test_the_gap_signal_changes_serving_only_at_mvp016_with_its_switch`
- [tests/test_learner_text_gaps_flow.py](../../../../../../tests/test_learner_text_gaps_flow.py) — direct import
  - `test_a_job_that_keeps_failing_is_logged_as_failed_without_a_target`
  - `test_the_queue_runs_a_text_once_retries_failures_and_respects_the_switch`
- [tests/test_learner_text_gaps_review.py](../../../../../../tests/test_learner_text_gaps_review.py) — direct import
- [tests/test_owner_capture_1025.py](../../../../../../tests/test_owner_capture_1025.py) — direct import
  - `test_b3_a_reattempt_starts_a_fresh_ask_thread`
- [tests/test_pinned_span_bridge.py](../../../../../../tests/test_pinned_span_bridge.py) — direct import
  - `test_the_bridge_is_a_normal_tutor_question_with_the_draft`
- [tests/test_placement_opening_probes.py](../../../../../../tests/test_placement_opening_probes.py) — direct import
  - `test_an_adopted_episode_that_completes_without_a_gap_opens_no_tutor`
  - `test_an_ignored_episode_feeds_no_reader_that_scores_it`
- [tests/test_placement_signals.py](../../../../../../tests/test_placement_signals.py) — direct import
  - `test_help_before_starting_blocks_fast_track`
- [tests/test_question_context.py](../../../../../../tests/test_question_context.py) — direct import
  - `test_classifier_channel_is_persisted`
  - `test_direct_explanation_request_forces_preference_channel`
  - `test_question_context_fields_persist`
- [tests/test_question_promotions.py](../../../../../../tests/test_question_promotions.py) — direct import
  - `test_build_tutor_qa_note_raises_without_subject`
  - `test_build_tutor_qa_note_writes_back_link_and_is_idempotent`
- [tests/test_question_signal.py](../../../../../../tests/test_question_signal.py) — direct import
  - `test_failed_provider_keeps_question_row_without_charging_budget`
  - `test_successful_ask_records_answered_event_and_agent_run`
- [tests/test_reader_ca1_astra_codex_review.py](../../../../../../tests/test_reader_ca1_astra_codex_review.py) — direct import
  - `test_words_after_the_statement_in_its_block_give_no_free_crop`
- [tests/test_reader_ca1_astra_rereview.py](../../../../../../tests/test_reader_ca1_astra_rereview.py) — direct import
  - `test_an_answer_before_the_statement_in_its_block_gives_no_free_crop`
- [tests/test_reader_ca2_astra_handoff.py](../../../../../../tests/test_reader_ca2_astra_handoff.py) — direct import
  - `test_a_new_attempt_still_gets_a_fresh_allowance`
  - `test_the_production_counting_functions_read_one_attempt_across_the_handoff`
- [tests/test_reader_ca2_codex_rereview.py](../../../../../../tests/test_reader_ca2_codex_rereview.py) — direct import
  - `test_f12_a_withheld_answer_is_never_stored_saved_promoted_or_queued`
  - `test_f13_a_sessionless_reader_question_counts_after_its_session_ends_and_the_problem_resumes`
  - `test_f13_an_unbound_practice_question_keeps_its_own_session_rule`
- [tests/test_reader_ca2_codex_review.py](../../../../../../tests/test_reader_ca2_codex_review.py) — direct import
  - `test_a_cited_passage_carries_its_excerpt_as_provided_and_stores_it`
  - `test_a_reader_question_with_no_practice_session_still_counts_at_the_submit`
  - `test_a_subscription_route_has_no_request_bound_and_a_metered_route_keeps_the_per_attempt_cap`
  - `test_an_answer_that_gives_the_answer_away_is_withheld_with_the_take_step`
  - `test_panel_off_the_answer_is_delivered_as_before`
  - `test_the_help_record_lists_what_submit_folds_including_an_earlier_serves_question`
- [tests/test_reader_ca2_fix_orchestrator.py](../../../../../../tests/test_reader_ca2_fix_orchestrator.py) — direct import
  - `test_f12_a_stored_withheld_answer_reaches_the_queue_only_as_its_take_step`
- [tests/test_reader_ca2_one_ask.py](../../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_a_practice_answer_mode_reaches_the_prompt_and_the_row`
  - `test_earlier_threads_list_each_attempts_help_newest_first`
  - `test_nothing_earlier_enters_the_tutors_context`
  - `test_panel_off_the_thread_and_budget_are_b3s`
  - `test_the_practice_thread_and_its_budget_are_keyed_by_the_attempt`
  - `test_the_three_styles_map_to_the_three_modes`
  - `test_without_a_mode_the_practice_prompt_is_todays`
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_ask_is_never_ability_evidence`
  - `test_each_disposition_produces_its_mechanism_and_nothing_else`
  - `test_reader_is_the_fourth_tutor_context`
  - `test_real_reader_writes_carry_the_salience_firewall_stamp`
- [tests/test_reader_rw1b_review.py](../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f1_a_formative_gap_brings_no_check_forward`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_a_bound_hint_asked_before_any_practice_session_counts_once`
  - `test_a_bound_hint_asked_in_an_ended_session_counts_in_the_next`
  - `test_a_bound_question_precedes_the_next_attempt_in_the_field`
  - `test_a_bound_reader_question_counts_on_its_items_submission`
  - `test_a_cold_bound_hint_survives_a_session_change_once`
  - `test_a_cold_bound_question_keeps_its_reveals_and_counts_one_hint`
  - `test_a_displayed_excerpt_is_debited_once`
  - `test_a_gap_and_a_misconceptions_correction_are_withheld_as_one`
  - `test_a_hint_shown_in_the_bound_session_counts_there_once`
  - `test_a_length_limit_never_cuts_a_statement_into_the_key`
  - `test_a_mapped_lo_does_not_suppress_the_attribution`
  - `test_a_misconception_beside_a_fitted_gap_never_reaches_the_verification`
  - `test_a_same_session_cold_hint_still_counts_once`
  - `test_a_three_slot_split_is_withheld_as_one`
  - `test_a_whitespace_variant_of_the_key_never_reaches_the_rewrite`
  - `test_an_answer_split_across_earlier_turns_is_not_delivered_whole`
  - `test_an_earlier_answer_and_a_gap_are_withheld_as_one`
  - `test_an_unbound_reader_question_still_counts_nowhere`
  - `test_every_sent_model_written_fragment_was_checked`
  - `test_item_bound_the_neighbours_and_references_are_guarded_too`
  - `test_the_practice_question_is_a_planned_member_of_the_verification`
  - `test_the_verifys_cold_thread_case_delivers_what_was_scored`
- [tests/test_reveal_ledger.py](../../../../../../tests/test_reveal_ledger.py) — direct import
  - `test_a_reveal_inside_a_live_repair_is_attributed_to_its_episode`
  - `test_a_tutor_answer_that_gives_the_solution_primes_the_next_attempt`
  - `test_answer_leak_overlap_accepts_a_structured_expected_answer`
  - `test_answer_leak_overlap_is_a_fraction_not_a_flag`
  - `test_answer_leak_overlap_is_zero_when_it_cannot_be_computed`
  - `test_answer_leak_overlap_scores_a_verbatim_restatement_as_a_full_reveal`
  - `test_feedback_question_is_hint_equivalent_and_writes_a_reveal_event`
  - `test_feedback_questions_count_as_hints_for_the_next_attempt`
  - `test_hint_window_still_starts_at_the_previous_attempt`
  - `test_reader_questions_bind_no_item_so_they_debit_nothing`
- [tests/test_ro0_codex_review.py](../../../../../../tests/test_ro0_codex_review.py) — direct import
  - `test_f1_a_refused_disclosure_write_leaves_the_question_and_warns`
- [tests/test_ro0_codex_verify.py](../../../../../../tests/test_ro0_codex_verify.py) — direct import
  - `test_r1_an_answer_stands_whatever_its_questions_receipt_meets`
- [tests/test_ro0_question_state.py](../../../../../../tests/test_ro0_question_state.py) — direct import
- [tests/test_ro0_report.py](../../../../../../tests/test_ro0_report.py) — direct import
  - `test_each_row_reports_what_was_written_and_measured_bytes`
- [tests/test_sidecar_close_cancels_jobs.py](../../../../../../tests/test_sidecar_close_cancels_jobs.py) — direct import
- [tests/test_source_retrieval_followup.py](../../../../../../tests/test_source_retrieval_followup.py) — direct import
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
  - `test_a_cited_span_overlapping_the_expected_answer_is_debited_as_a_reveal`
  - `test_short_answers_are_measured_in_source_spans`
- [tests/test_source_retrieval_rereview.py](../../../../../../tests/test_source_retrieval_rereview.py) — direct import
- [tests/test_source_retrieval_rereview_cost.py](../../../../../../tests/test_source_retrieval_rereview_cost.py) — direct import
- [tests/test_source_retrieval_search.py](../../../../../../tests/test_source_retrieval_search.py) — direct import
  - `test_with_retrieval_off_reader_answers_carry_no_suggestion_field`
- [tests/test_source_retrieval_tutor.py](../../../../../../tests/test_source_retrieval_tutor.py) — direct import
  - `test_a_reader_question_records_the_suggestion_and_promotion_names_it`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_the_tutor_citation_hook_does_nothing_with_the_switches_off_and_joins_its_delivery_when_on`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_teacher_te0_confidence_events.py](../../../../../../tests/test_teacher_te0_confidence_events.py) — direct import
  - `test_with_no_confidence_data_the_tutor_context_renders_and_hashes_as_before`
- [tests/test_tutor_citations.py](../../../../../../tests/test_tutor_citations.py) — direct import
  - `test_citations_validated_against_provided_spans`
  - `test_no_links_degrades_to_no_citations`
  - `test_tutor_context_carries_semantic_authority_spans`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
  - `test_a_pinned_passage_arrives_whole_with_the_theorem_it_cites`
  - `test_a_referenced_theorem_is_citable`
- [tests/test_tutor_qa.py](../../../../../../tests/test_tutor_qa.py) — direct import
  - `test_answer_leaks_expected_heuristics`
  - `test_ask_question_classifies_and_marks_hint_equivalents`
  - `test_ask_question_drops_facets_outside_candidates`
  - `test_ask_question_enforces_practice_limit`
  - `test_ask_question_feedback_limit_and_intervention_wiring`
  - `test_ask_question_leak_check_flags_expected_answer`
  - `test_ask_question_library_context_and_daily_limit`
  - `test_ask_question_validation_errors`
  - `test_diagnostic_decision_attaches_after_probe_transition`
  - `test_hint_equivalents_for_submission_window_starts_at_last_attempt`
  - `test_practice_prompt_context_carries_guardrail_grounding`
  - `test_question_raises_diagnostic_uncertainty_read_side`
- [tests/test_tutor_tool_requests.py](../../../../../../tests/test_tutor_tool_requests.py) — direct import

## Modification guidance

- Change tutor qa policy here when tutor owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tutor/tutor_qa.py](../../../../../../src/learnloop/tutor/tutor_qa.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
