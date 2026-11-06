---
title: "learnloop.source_retrieval.deliverables"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/deliverables.py"
source_paths:
  - "src/learnloop/source_retrieval/deliverables.py"
source_commit: "workspace/uncommitted @ HEAD 271a042fd6e7c418c6abdb96d8eb08fd1d8e595a"
source_commit_timestamp: "2026-11-06T11:32:04-05:00"
source_worktree_state: "modified"
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
  - "learnloop.source_retrieval.deliverables module"
  - "src/learnloop/source_retrieval/deliverables.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.deliverables`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.deliverables` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Deliverable curriculum C0b: the deliverable and its scope, in the learner's own words (spec_deliverable_curriculum_v1 §5, §6.5, §9.1, §12).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py) |
| Source lines | 1653 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 271a042fd6e7c418c6abdb96d8eb08fd1d8e595a` |
| Commit timestamp | `2026-11-06T11:32:04-05:00` |

## Public API

- `class DeliverableError(ValueError)` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 140) — A request the deliverable cannot answer (``code`` names it for the sidecar).
  - `__init__(self, code: str, message: str) -> None` (line 143; internal)
- `enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 148)
- `models_off() -> bool` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 152)
- `class RouteUnavailable(Exception)` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 165) — A route cannot run (``reason``: models_off | unrouted | unpriced | capped | unavailable | failed); ``message`` is the learner's line.
  - `__init__(self, reason: str, message: str) -> None` (line 169; internal)
- `daily_envelope(vault: Any, repository: Repository, *, clock: Clock | None=None) -> SharedDailyEnvelope` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 179) — The curriculum's one daily cap (``curriculum.max_daily_cost_usd``) over its routes (C0a's coverage judge, C0b's two and, since C2b, the note link judge).
- `capped_message(vault: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 189)
- `class ChatRoute` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 210) — One C0b route's pinned plan for one call (RW7a's ``JudgeRoute`` shape).
  - `__init__(self, vault: Any, repository: Repository, task: str, *, client: Any | None, envelope: Any | None, label: str, plan_only: bool=False, subscription_only: bool=False) -> None` (line 223; internal)
  - `_subscription_only_refusal(self) -> RouteUnavailable` (line 238; internal)
  - `plan_only_problem(self) -> RouteUnavailable | None` (line 242; public) — With ``plan_only``, why the planned route may not be asked (None: it may).
  - `subscription(self) -> bool` (line 252; public)
  - `problem(self) -> RouteUnavailable | None` (line 255; public)
  - `ask(self, prompt: str, result_model: type[WireModel], *, owner_id: str, prompt_version: str, guard: SC.CoverageGuard | None=None, validate: Callable[[Any], Any] | None=None) -> Any` (line 271; public) — One call.
  - `model(self) -> str` (line 322; public)
- `admission_problem(vault: Any, repository: Repository, task: str, *, client: Any | None=None, clock: Clock | None=None) -> RouteUnavailable | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 328) — Whether a call on ``task`` would be refused now, before any call.
- `recover_publications(vault_root: Path | str, repository: Repository) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 418) — Finish or drop every unfinished publication (see the journal above).
- `goal_of(vault: Any, goal_id: str) -> Any` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 516)
- `kind_of(goal: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 525) — How the deliverable is shown (§5.1; shown, never stored): an exam, a quest or a project.
- `create_deliverable(vault: Any, repository: Repository, sentence: str, *, due_at: str | None=None, exam: bool=False, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 534) — A new learner goal from the learner's sentence, and the sentence as its first scope input.
- `scope_for(vault: Any, repository: Repository, learning_object_ids: Sequence[str]) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 574) — The goal's ``facet_scope`` for the resolved LOs (§5.3).
- `write_facet_scope(vault: Any, repository: Repository, goal_id: str, learning_object_ids: Sequence[str], *, clock: Clock | None=None) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 599) — The goal's ``facet_scope`` from the resolved LOs, under the vault mutation lock (no receipt; :func:`resolve` and :func:`decide_unmatched` publish with theirs).
- `scope_library(vault: Any, repository: Repository) -> SC.Library` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 647) — The library a scope input reads (C3, §9.1): C0a's teaching library plus the readings of ``syllabus`` sources (``SCOPE_READABLE_ROLES``), with exam and held-out material, readings held back and every other non-teaching role left out exactly as C0a leaves them.
- `syllabus_extractions(vault: Any, repository: Repository) -> frozenset[str]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 658) — The readings a ``syllabus`` member holds whole (whole-document scope inputs).
- `syllabus_documents(vault: Any, repository: Repository) -> list[dict[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 664) — The syllabi the learner may attach whole as a scope input (C3, §5.2; Codex review F5): every reading a ``syllabus`` member holds whole that the scope library reads now (exam material, a reading held back or an unreadable predicate: none).
- `whole_document_spans(vault: Any, repository: Repository, extraction_id: str) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 685) — Every readable span of a syllabus, in reading order (§5.2: "a whole short document").
- `passage_texts(vault: Any, repository: Repository, extraction_id: str, span_ids: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 706) — A passage's text, read through the exam predicate now (§9.1, G-C2).
- `add_input(vault: Any, repository: Repository, goal_id: str, kind: str, *, text: str | None=None, extraction_id: str | None=None, span_ids: Sequence[str]=(), context: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 735) — One scope input (append-only).
- `depth_of(repository: Repository, goal_id: str) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 763) — The deliverable's depth: its newest ``depth`` input (None: ask once, §5.4).
- `class NeededTopic(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 777)
- `class UnmatchedPhrase(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 783)
- `class ScopeResolutionV1(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 789)
- `topic_records(vault: Any, *, statement_chars: int=STATEMENT_CHARS) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 827) — The vault's active LOs as compact records (§5.3): never their items.
- `class ScopePrompt` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 849)
- `exam_units_in_scope(vault: Any) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 876) — C3's kill switch (``curriculum.exam_units_in_scope``): off, the resolver reads C0b's prompt.
- `deliverable_subjects(vault: Any, repository: Repository, goal_id: str, inputs: Sequence[Mapping[str, Any]]) -> frozenset[str]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 922) — The subjects a deliverable is about, from its own explicit context (§5.3: the past-papers mapping is "of this subject"; Codex review F1), first that names one: 1.
- `past_paper_groups(vault: Any, repository: Repository, among: Iterable[str] | None=None) -> list[tuple[str, list[str]]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 964) — C2b (past papers option A, §5.3 as built): with the deliverable's subject ambiguous, each active subject's past-papers ids (:func:`past_paper_learning_objects` for that subject alone, so a unit counts only for its own subject), empty groups left out, in subject-id order.
- `past_paper_learning_objects(vault: Any, repository: Repository, subjects: Iterable[str]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1000) — §9.2: the active LOs of ``subjects`` that practice-available exam and problem-set units of those subjects map to, by id.
- `build_scope_prompt(vault: Any, repository: Repository, goal: Any, inputs: Sequence[Mapping[str, Any]]) -> ScopePrompt` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1056)
- `validate_resolution(vault: Any, output: ScopeResolutionV1) -> tuple[list[dict[str, str]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1108) — ``(needs, unmatched)``: every id an active LO, each once (first phrase kept); every unmatched phrase with a title and a statement, each once.
- `class ScopeResult` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1141)
- `latest_resolution(repository: Repository, goal_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1154)
- `needed_learning_objects(vault: Any, repository: Repository, goal_id: str) -> list[dict[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1161) — The deliverable's needed LOs with their phrases (the newest resolution), active ones only.
- `passage_guard(vault: Any, repository: Repository, inputs: Sequence[Mapping[str, Any]], *, live_vault: Callable[[], Any] | None=None, prompt: ScopePrompt | None=None) -> SC.CoverageGuard | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1172) — C0a's :class:`SC.CoverageGuard` over the sections the passage inputs read (Codex review F1): protection is read again, from the vault as it is now (``live_vault``, the sidecar's generation-bound provider; else its files), before every physical request and before the receipt.
- `resolve(vault: Any, repository: Repository, goal_id: str, *, client: Any | None=None, clock: Clock | None=None, live_vault: Callable[[], Any] | None=None) -> ScopeResult` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1230) — One resolver call over the inputs in order (none when this state was resolved), the resolution row and its ledger verdict, then the goal's facet scope.
- `decide_unmatched(vault: Any, repository: Repository, goal_id: str, phrase: str, decision: str, *, subject_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1311) — The learner's *add it* / *no* on an unmatched phrase (§5.3).
- `also_about(vault: Any, repository: Repository, extraction_id: str, section_id: str, text: str, *, client: Any | None=None, clock: Clock | None=None, live_vault: Callable[[], Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1395) — Resolve the learner's words to one LO and write C0a's ``is_about`` correction.
- `scope_view(vault: Any, repository: Repository, goal_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1460) — What the learner sees of the scope (§5.3): one line per topic with the phrase it answers, the phrases not in the library yet with their state, and the receipt on demand.
- `deliverable_goals(vault: Any, repository: Repository) -> list[Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1504) — Active learner goals with a resolution (the deliverables), highest ``(priority, id)`` first.
- `learning_objects_of(entries: Iterable[Mapping[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1516)
- `typed_goal_key(text: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1529)
- `resolve_typed_goal(vault: Any, repository: Repository, text: str, *, client: Any | None=None, clock: Clock | None=None) -> ScopeResult` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1533) — C0b's resolver on a lesson's typed goal alone (§11.5): one call returns the needed LOs, each with the phrase it answers, and the phrases it could not match with a proposed title and statement; ids are validated.
- `create_lesson_topic(vault: Any, repository: Repository, *, lesson_id: str, phrase: str, title: str, statement: str, subject_id: str, anchors: Sequence[Mapping[str, Any]]=(), clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1582) — A typed lesson goal's phrase the learner said *yes* to: ``create_goal_lo`` with ``mechanism = teacher_goal_v1`` (``origin = codex_proposal``, the anchors in ``source_refs``, none: unsourced), the lesson's id as its goal id; undoable; the daily cap shared with text-gap creations,…
- `typed_goal_subject(vault: Any, needs: Sequence[Mapping[str, Any]]) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1600) — The subject a typed goal's new topic joins (:func:`_subject_for`'s rule).

### Module constants

- `SCOPE_ROUTE` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 91)
- `PATH_ROUTE` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 92)
- `OWNER_KINDS` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 94)
- `SCOPE_PROMPT_VERSION` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 95)
- `SCOPE_PAST_PAPERS_PROMPT_VERSION` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 98)
- `SCOPE_PAST_PAPERS_GROUPED_PROMPT_VERSION` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 103)
- `SCOPE_READABLE_ROLES` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 105)
- `PAST_PAPER_ROLES` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 109)
- `DECISION_VERSION` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 110)
- `SCOPE_LEDGER_TASK` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 111)
- `MODELS_ENV` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 114)
- `INPUT_KINDS` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 116)
- `SCOPE_KINDS` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 118)
- `DEPTHS` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 119)
- `EXAM_REFUSAL` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 120)
- `INPUT_CHARS` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 126)
- `PHRASE_CHARS` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 128)
- `STATEMENT_CHARS` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 130)
- `PROPOSAL_CHARS` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 132)
- `_CHARS_PER_TOKEN` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 134)
- `_OVERHEAD_CHARS` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 135)
- `_CAPS` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 137)
- `ADMISSION_REASONS` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 176)
- `PLAN_ONLY_REASON` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 196)
- `SUBSCRIPTION_ONLY_REASON` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 207)
- `_INSTRUCTIONS` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 795)
- `_PAST_PAPERS` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 805)
- `_PAST_PAPERS_GROUPED` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 811)
- `_ALSO_ABOUT` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 819)
- `SUPERSEDED_MESSAGE` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1150)
- `TYPED_GOAL_PREFIX` ([src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1526)

### Explicit exports

`__all__` declares:

- `ADMISSION_REASONS`
- `ChatRoute`
- `DEPTHS`
- `DeliverableError`
- `EXAM_REFUSAL`
- `INPUT_KINDS`
- `MODELS_ENV`
- `OWNER_KINDS`
- `PAST_PAPER_ROLES`
- `PATH_ROUTE`
- `RouteUnavailable`
- `SCOPE_PAST_PAPERS_GROUPED_PROMPT_VERSION`
- `SCOPE_PAST_PAPERS_PROMPT_VERSION`
- `SCOPE_READABLE_ROLES`
- `SCOPE_ROUTE`
- `ScopeResolutionV1`
- `ScopeResult`
- `add_input`
- `admission_problem`
- `also_about`
- `build_scope_prompt`
- `create_deliverable`
- `decide_unmatched`
- `deliverable_goals`
- `deliverable_subjects`
- `depth_of`
- `exam_units_in_scope`
- `goal_of`
- `kind_of`
- `latest_resolution`
- `needed_learning_objects`
- `passage_guard`
- `passage_texts`
- `past_paper_groups`
- `past_paper_learning_objects`
- `recover_publications`
- `resolve`
- `scope_for`
- `scope_library`
- `scope_view`
- `syllabus_documents`
- `syllabus_extractions`
- `topic_records`
- `validate_resolution`
- `whole_document_spans`
- `write_facet_scope`

## Internal implementation anchors

- `_one_line(text: Any, limit: int=PHRASE_CHARS) -> str` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 156)
- `_is_plan_type(profile_type: Any) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 199)
- `_goals_path(vault: Any) -> Path` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 341)
- `_write_goals(path: Path, data: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 347) — Publish ``goals.yaml`` whole (a temporary file, then an atomic replace).
- `_journal_dir(root: Path | str) -> Path` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 374)
- `_journal_write(root: Path | str, entry: Mapping[str, Any]) -> Path` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 378)
- `_goal_entry_update(vault_root: Path | str, goal_id: str, *, scope: Mapping[str, Any] | None=None, append: Mapping[str, Any] | None=None, now: str) -> None` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 391) — goals.yaml: one goal's facet scope replaced, or a new goal appended (validated).
- `_goal_revision(vault_root: Path | str, goal_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 459) — The goal's facet scope and ``updated_at`` as goals.yaml has them now (None: no such goal).
- `_scope_key(scope: Any) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 473) — A facet scope compared by content (key order and list order are not edits).
- `_finish_scope(vault_root: Path | str, entry: Mapping[str, Any], receipt: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 482) — Finish one stopped scope publication without overwriting a later learner edit (F15).
- `_normalize_due(due_at: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 505)
- `_publish(vault: Any, repository: Repository, goal_id: str, row: dict[str, Any], ledger: Mapping[str, Any], *, now: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 613) — One resolution receipt and the goal's scope, journalled (Codex review F8).
- `_input_row(goal_id: str, kind: str, text: str | None, *, now: str, extraction_id: str | None=None, span_ids: Sequence[str]=(), context: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 640)
- `_bounded_topics(vault: Any, budget_chars: int) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 864) — Every active LO's record within the prompt bound: statements are clipped, then dropped, before an LO is ever left out (an LO left out could not be chosen).
- `_source_of_extractions(repository: Repository, extraction_ids: Iterable[str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 882) — ``{extraction id: source id}`` for the readings named (unknown ones are absent).
- `_set_subjects_by_source(vault: Any) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 903) — ``{source id: the subjects of the source sets holding it}``.
- `_active_subjects(vault: Any, learning_object_ids: Iterable[str]) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 913)
- `_subject_name(vault: Any, subject_id: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 958)
- `_learning_object_refs(vault: Any, learning_object: Any) -> list[Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 985) — The LO's own source refs and its canonical facets' (Reader's mapping, ``reader_progression.learning_objects_for_section``; Codex review F2).
- `_superseded_ledger(goal_id: str, prompt: ScopePrompt, needs: Any, unmatched: Any, model: str, now: str, head: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1221)
- `_subject_for(vault: Any, needs: Sequence[Mapping[str, Any]]) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/deliverables.py), line 1377) — The subject a new topic joins: the one most of the needed LOs share (ties by id); None when they name none (the learner then chooses).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; statically calls `ChatRoute`, `DeliverableError`, `_is_plan_type`, `daily_envelope`, `deliverable_goals`, `depth_of`, `goal_of`, `kind_of`, `latest_resolution`, `needed_learning_objects`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `module`; statically calls `ChatRoute`, `daily_envelope`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `module`; statically calls `enabled`, `latest_resolution`
- [[Reference/Modules/learnloop/teacher/topics|learnloop.teacher.topics]] — imports `module`; statically calls `create_lesson_topic`, `resolve_typed_goal`, `typed_goal_key`, `typed_goal_subject`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `module`; statically calls `add_input`, `admission_problem`, `also_about`, `create_deliverable`, `decide_unmatched`, `deliverable_goals`, `depth_of`, `enabled`, `recover_publications`, `resolve`, `scope_view`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `module`; statically calls `enabled`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `call_labels`, `content_key`, `gate_model_requests`; calls `call_labels`, `content_key`, `gate_model_requests`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `is_subscription_transport`, `spend_envelopes`; calls `SpendBudget`, `SpendCaps`, `is_subscription_transport`, `spend_envelopes`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `CHATGPT_PLAN_PROFILE_TYPE`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`; calls `exam_material`, `role_material`, `scope_only_material`, `source_ref_keys`
- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `SCOPE_ONLY_ROLES`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/deliverables|learnloop.db.stores.deliverables]] — imports `module`; calls `inputs`, `insert_input`, `insert_resolution`, `latest_resolution`, `resolution`, `resolved_goals`, `resolver_state`, `tables_present`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/goals/goal_lo|learnloop.goals.goal_lo]] — imports `module`; calls `GoalLoRequest`, `create_goal_lo`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `scope_facets`; calls `scope_facets`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `PaidRoute`, `plan_route`, `resolve_client`; calls `PaidCalls`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; calls `CoverageGuard`, `Library`, `correct`, `enabled`, `read_protection`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SharedDailyEnvelope`, `midnight`; calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Goal`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `yaml_to_string`; calls `read_yaml`, `yaml_to_string`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `json`, `os`, `pathlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]], [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]], [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]], [[Reference/Modules/learnloop/teacher/topics|learnloop.teacher.topics]], [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — direct import
- [tests/test_curriculum_c0b_landing.py](../../../../../../tests/test_curriculum_c0b_landing.py) — direct import
  - `test_i_a_dismissal_and_an_also_about_on_one_section_coexist_through_path_rejudgments`
  - `test_ii_compare_scope_and_the_scope_resolver_are_separate_routes`
  - `test_ii_compare_scopes_cap_does_not_stop_the_resolver`
  - `test_ii_the_curriculum_cap_does_not_stop_compare_scope`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_a_stale_path_is_not_followed_and_the_receipt_says_stale`
  - `test_the_nearest_deliverable_with_a_fresh_path_is_followed`
- [tests/test_curriculum_c1_round5_followups.py](../../../../../../tests/test_curriculum_c1_round5_followups.py) — direct import
  - `test_c1_r5_followup_a_a_metered_client_behind_a_plan_route_sends_nothing`
  - `test_c1_r5_followup_a_the_refresh_resolves_its_route_once_and_judge_sends_on_it`
- [tests/test_curriculum_c2b_past_papers.py](../../../../../../tests/test_curriculum_c2b_past_papers.py) — direct import
  - `test_a_group_held_out_meanwhile_refuses_the_request`
  - `test_a_known_subject_sends_only_its_own_ids_as_one_flat_list`
  - `test_ambiguous_subject_sends_the_ids_grouped_by_subject_name_and_the_resolver_picks_its_group`
  - `test_switched_off_the_prompt_is_c0bs_v1`
- [tests/test_curriculum_c3_codex_review.py](../../../../../../tests/test_curriculum_c3_codex_review.py) — direct import
  - `test_a_change_that_leaves_the_sent_ids_practice_available_publishes`
  - `test_a_held_out_unit_cited_by_a_facet_contributes_nothing`
  - `test_a_mapping_carried_by_a_canonical_facet_counts`
  - `test_a_mapping_held_out_before_the_request_is_never_sent`
  - `test_a_mapping_held_out_during_the_call_publishes_nothing`
  - `test_a_paused_second_subject_keeps_the_only_active_subject_s_past_papers`
  - `test_a_resolution_s_topics_name_the_subject_for_the_next_one`
  - `test_a_second_active_subject_without_topics_sends_linear_algebras_papers_as_its_own_group`
  - `test_a_syllabus_names_the_subject_and_another_subject_s_papers_stay_out`
  - `test_a_vault_without_a_syllabus_keeps_c0b_s_view`
  - `test_an_ambiguous_deliverable_reads_the_past_papers_grouped_by_subject`
  - `test_past_papers_are_read_per_subject_never_vault_wide`
  - `test_the_scope_view_offers_readable_syllabi_only`
- [tests/test_curriculum_c3_exam_scoping.py](../../../../../../tests/test_curriculum_c3_exam_scoping.py) — direct import
  - `test_a_syllabus_made_exam_during_the_call_keeps_nothing`
  - `test_a_syllabus_passage_is_a_scope_input_read_only_by_the_resolver`
  - `test_a_whole_short_syllabus_is_one_input_with_its_spans_recorded`
  - `test_an_unreadable_predicate_contributes_nothing`
  - `test_gc1_no_request_correspondent_path_row_or_slice_names_exam_material`
  - `test_gc1_note_link_judge_requests_carry_no_exam_material_from_sources`
  - `test_gc2_a_syllabus_made_exam_after_it_was_added_is_never_sent`
  - `test_gc2_a_syllabus_with_the_exam_role_is_refused_and_nothing_is_written`
  - `test_gc2_the_same_syllabus_given_the_exam_role_is_refused`
  - `test_gc3_readiness_checks_never_pick_exam_reserved_or_held_out_items`
  - `test_off_is_c0b_byte_for_byte`
  - `test_past_papers_contribute_their_lo_ids_only_and_held_out_units_nothing`
  - `test_the_scope_view_says_which_topics_your_past_papers_test`
- [tests/test_deliverable_codex_review.py](../../../../../../tests/test_deliverable_codex_review.py) — direct import
  - `test_f10_use_instead_refuses_a_section_that_only_mentions_the_topic`
  - `test_f14_the_time_row_counts_each_section_once_and_minutes_read_are_recorded`
  - `test_f15_a_publication_already_on_disk_is_recognized_and_not_written_again`
  - `test_f15_a_stop_before_goals_yaml_then_a_learner_edit_keeps_the_edit`
  - `test_f15_recovery_keeps_a_learner_scope_edit_made_after_the_publication`
  - `test_f1_reopened_a_superseded_answer_keeps_nothing_when_its_passage_was_protected_meanwhile`
  - `test_f1_the_resolver_keeps_nothing_when_its_passage_is_held_out_during_the_call`
  - `test_f2_a_resolution_overtaken_by_a_newer_input_is_kept_but_never_activated`
  - `test_f8_a_goal_whose_first_input_committed_is_recovered_by_the_next_rpc`
  - `test_f8_a_stop_after_the_receipt_is_finished_forward`
  - `test_f8_a_stop_before_the_receipt_publishes_nothing`
  - `test_f9_a_topic_added_since_the_judgment_has_a_line_until_the_next`
- [tests/test_deliverable_path.py](../../../../../../tests/test_deliverable_path.py) — direct import
  - `test_am_i_ready_creates_one_check_per_untested_lo_never_an_exam_reserved_item`
  - `test_ask_depth_and_no_scope_states`
  - `test_overrides_use_instead_skip_and_check_later`
- [tests/test_deliverable_rpcs.py](../../../../../../tests/test_deliverable_rpcs.py) — direct import
  - `test_no_deliverable_slice_is_none_and_also_about_corrects`
  - `test_the_reader_selection_action_scopes_from_the_selected_passage_only`
- [tests/test_deliverable_scope.py](../../../../../../tests/test_deliverable_scope.py) — direct import
  - `test_a_book_passage_is_read_through_the_predicate_when_resolved`
  - `test_a_correction_is_a_new_input_and_reresolves`
  - `test_a_deliverable_is_a_learner_goal_with_its_sentence_and_first_input`
  - `test_a_model_failure_is_unavailable_and_writes_nothing`
  - `test_add_it_creates_the_lo_through_create_goal_lo_and_joins_the_scope`
  - `test_also_about_is_resolved_by_the_same_resolver_and_kept_as_a_learner_row`
  - `test_gc1_no_exam_or_held_out_text_reaches_the_resolver`
  - `test_gc2_an_exam_passage_is_refused_as_a_scope_input_and_nothing_is_written`
  - `test_only_a_learner_goal_is_a_deliverable`
  - `test_resolution_writes_the_scope_through_the_lock_and_a_repeat_pays_nothing`
  - `test_scope_view_lists_topics_unmatched_and_the_receipt`
  - `test_the_depth_is_an_input_the_newest_standing`
  - `test_unmatched_phrases_never_create_an_lo_without_the_learners_yes`
  - `test_without_a_fake_the_models_are_off`
- [tests/test_notes_as_learner_text.py](../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_gc1_exam_sentinels_never_reach_the_gap_model_via_a_notes_context`
- [tests/test_notes_vault_search.py](../../../../../../tests/test_notes_vault_search.py) — direct import
  - `test_c2b_r3_f4_several_named_subjects_send_the_grouped_form_for_those`
- [tests/test_teacher_te2_sidecar.py](../../../../../../tests/test_teacher_te2_sidecar.py) — direct import
  - `test_lesson_goal_and_open_lessons_through_the_handlers`

## Modification guidance

- Make changes here when the responsibility remains deliverables within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/deliverables.py](../../../../../../src/learnloop/source_retrieval/deliverables.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
