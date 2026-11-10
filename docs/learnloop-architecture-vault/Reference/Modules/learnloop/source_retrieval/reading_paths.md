---
title: "learnloop.source_retrieval.reading_paths"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/reading_paths.py"
source_paths:
  - "src/learnloop/source_retrieval/reading_paths.py"
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
  - "learnloop.source_retrieval.reading_paths module"
  - "src/learnloop/source_retrieval/reading_paths.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.reading_paths`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.reading_paths` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Reader workbench RW7a: reading paths in the Guide, display only (spec_reader_workbench_v1 §10.1, G47; UX §4.11, Moment 0, W1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py) |
| Source lines | 1375 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ReadingPathError(ValueError)` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 149) — A request the path cannot answer (``code`` names it for the sidecar).
  - `__init__(self, code: str, message: str) -> None` (line 152; internal)
- `enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 157)
- `models_off() -> bool` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 162)
- `class LoStatus` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 171)
- `class PathSection` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 178)
- `class PathInputs` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 190)
  - `section(self, section_id: str) -> PathSection | None` (line 202; public)
  - `section_list_hash(self) -> str` (line 205; public)
  - `state_key(self, depth: str) -> str` (line 208; public) — The cache key (§10.1): the depth, the section list sent and every linked LO's status (and the goal the path names, and the prompt).
- `open_assumption_rows(vault: Any, repository: Repository) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 229) — LOs with an open placement assumption that IS an ``assumption_decisions`` row (Codex review F1).
- `lo_statuses(vault: Any, repository: Repository, learning_object_ids: Iterable[str]) -> dict[str, LoStatus]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 247) — Each LO's status: demonstrated (``lo_certification``), assumed (an open assumption row), learning (any evidence), or new.
- `goal_for_source(vault: Any, learning_object_ids: Iterable[str]) -> Any | None` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 275) — The active goal whose facet scope covers the source's LOs (the Guide's ``goal_for_item`` over each, the highest priority); RW7a creates none.
- `reading_of(repository: Repository, extraction_id: str) -> tuple[str, str | None]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 290)
- `path_inputs(vault: Any, repository: Repository, extraction_id: str) -> PathInputs` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 298) — Everything a path is judged and shown from, read now.
- `honest_label(label: str, learning_object_ids: Sequence[str], statuses: Mapping[str, LoStatus]) -> tuple[str, bool]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 349) — ``(label, changed)``: ``already_shown`` only when every LO the section teaches is demonstrated, ``assumed`` only with an open assumption on every LO not demonstrated (at least one); otherwise ``core``.
- `effective_label(stored: str, override_row: Mapping[str, Any] | None, learning_object_ids: Sequence[str], statuses: Mapping[str, LoStatus]) -> tuple[str, bool, str | None, str]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 369) — ``(label, changed, override, effective)`` for one judged section: the honest label (:func:`honest_label`), the learner's newest choice (``None`` when there is none or it was cleared) and what that makes the section: a "read it anyway" is ``core``, a "skip it" is ``skipped``, oth…
- `shown_reason(label: str, model_label: str, model_reason: str | None, section: PathSection, lo_titles: Mapping[str, str]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 389) — The line under a chip.
- `class SectionVerdict(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 411)
- `class ReadingPathOutputV1(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 419)
- `build_prompt(inputs: PathInputs, depth: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 438)
- `class Verdict` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 460)
- `validate(output: ReadingPathOutputV1, inputs: PathInputs) -> list[Verdict]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 468) — Every sent section once, in book order: the model's label made honest (:func:`honest_label`); a section the model left out or named twice keeps its first answer, or is ``core``; unknown section ids are dropped.
- `exercise_label(text: str, page: int | None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 492) — "Exercise 4.12" when the lead names one, else its number, else the page.
- `pick_exercises(vault: Any, repository: Repository, inputs: PathInputs, section_ids: Iterable[str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 504) — For each named section, the lead span of its first exercise region the one statement reader still reads (exam and held-out material never; fail closed).
- `exercise_view(vault: Any, repository: Repository, inputs: PathInputs, lead_span_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 530) — The stored exercise read again now: None when its region is gone or exam or held-out material now (the statement reader fails closed).
- `depth_choice(vault: Any, repository: Repository, source_id: str, extraction_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 606) — The depth the path is for: the newer of the Guide's choice and DL2's (mapped); ``depth`` None asks the learner.
- `set_depth(repository: Repository, source_id: str, depth: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 623)
- `class JudgeUnavailable(Exception)` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 636) — The judge cannot run (``reason``: models_off | unrouted | unpriced | capped | unavailable); ``message`` is the learner's line.
  - `__init__(self, reason: str, message: str) -> None` (line 640; internal)
- `daily_envelope(vault: Any, repository: Repository, *, clock: Clock | None=None) -> SharedDailyEnvelope` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 646)
- `capped_message(vault: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 653)
- `class JudgeRoute` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 658) — The judge's pinned route for one judgment.
  - `__init__(self, vault: Any, repository: Repository, *, client: Any | None, envelope: Any) -> None` (line 661; internal)
  - `subscription(self) -> bool` (line 671; public)
  - `problem(self) -> JudgeUnavailable | None` (line 674; public) — Checked before any call: the switch's env, the route, the price and the day's cap.
  - `ask(self, prompt: str, *, owner_id: str) -> ReadingPathOutputV1` (line 690; public)
  - `model(self) -> str` (line 710; public)
- `admission_problem(vault: Any, repository: Repository, *, client: Any | None=None, clock: Clock | None=None) -> JudgeUnavailable | None` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 723) — Whether a judgment would be refused now, before any call (today's envelope, the vault's current config).
- `class JudgeResult` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 733)
- `claim_key(extraction_id: str, depth: str, state_key: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 772)
- `judge(vault: Any, repository: Repository, extraction_id: str, depth: str, *, client: Any | None=None, clock: Clock | None=None, inputs: PathInputs | None=None) -> JudgeResult` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 848) — Label the reading's sections at ``depth``: no call when the cached path for the current state exists; otherwise one call, the honest-label rule, the exercises, then the ledger verdicts and the rows in one transaction.
- `override(vault: Any, repository: Repository, extraction_id: str, depth: str, section_id: str, choice: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 966) — "Read it anyway" / "skip it" (or ``none``, clearing it): one ``learner_card`` ledger verdict and one ``reader_path_sections`` row, nothing else.
- `next_activity(sections: Sequence[Mapping[str, Any]], depth: str, progress: Mapping[str, Mapping[str, Any]]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1027) — The suggested next activity, composed without a model (§10.1): the next unfinished core or prerequisite section (a "read it anyway" counts as core, a "skip it" leaves it out) and, at learn to use it and fluency, its exercise.
- `goal_line(goal: Mapping[str, Any] | None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1048)
- `judged_sections(rows: Iterable[Mapping[str, Any]]) -> frozenset[str]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1054) — The sections one judgment was asked about: its judge rows.
- `reasons_held_back(rows: Iterable[Mapping[str, Any]], inputs: PathInputs) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1064) — True when the judgment behind ``rows`` was asked about a section that may not be sent now (withheld since: held out, or exam material).
- `path_view(vault: Any, repository: Repository, extraction_id: str, *, inputs: PathInputs | None=None, judging: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1090) — What the Guide shows.
- `class PlanSectionRef` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1174) — One section's effective label as the plan read it, with the rows it came from (Codex review F3): the judge's row and the learner's newest override row (None when there is none).
  - `receipt(self) -> dict[str, Any]` (line 1185; public)
- `class PlanPath` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1191) — What RW7b's plan reads of one reading's path.
  - `follows(self) -> bool` (line 1213; public)
  - `labels(self) -> Mapping[str, str]` (line 1217; public) — Section id -> effective label, for the sections the judgment names.
  - `label_for(self, section_id: str) -> str | None` (line 1222; public) — The section's effective label, or None for a section the judgment does not name (a fresh judgment names every sendable section, so only a withheld one): never planned through the path.
  - `plannable(self, section_id: str) -> bool` (line 1229; public)
  - `receipt(self) -> dict[str, Any]` (line 1234; public) — The receipt's entry (Codex review F3): the inputs' key and the consumed judgment's key apart, and every judge and override row the labels came from, so neither a later judgment nor a later override changes what the receipt says was read.
- `plan_path(vault: Any, repository: Repository, extraction_id: str) -> PlanPath` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1251) — The reading path RW7b's plan follows for one reading, read now and never judged here (the plan calls no model).
- `skipped_section_learning_objects(vault: Any, repository: Repository) -> dict[str, dict[str, list[str]]]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1303) — RW7b's report adapter (spec §15's reading-path row, Codex review F4): for every reading with a "skip it" row, each skipped section's linked LOs (``reader_progression.learning_objects_by_section``, the map the report's connection-only reader does not have).

### Module constants

- `DEPTHS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 97)
- `DEPTH_LABELS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 98)
- `DEPTH_MEANS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 101)
- `INTENT_DEPTH` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 107)
- `LABELS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 111)
- `CHIPS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 112)
- `OVERRIDES` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 117)
- `STATUSES` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 119)
- `ROUTE_TASK` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 121)
- `OWNER_KIND` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 122)
- `PROMPT_VERSION` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 123)
- `OVERRIDE_VERSION` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 124)
- `LEDGER_TASK` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 125)
- `LEDGER_LEFT` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 126)
- `LEDGER_RIGHT` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 127)
- `ENVELOPE` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 128)
- `MODELS_ENV` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 131)
- `_CAPS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 133)
- `REASON_CHARS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 134)
- `WORDS_PER_MINUTE` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 135)
- `STATEMENT_CHARS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 136)
- `DEFAULT_REASONS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 138)
- `NOT_SHOWN_REASON` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 143)
- `NOT_ASSUMED_REASON` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 144)
- `CODE_REASONS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 146)
- `_INSTRUCTIONS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 423)
- `ADMISSION_REASONS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 720)
- `CLAIM_TASK` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 753)
- `CLAIM_LEASE_SECONDS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 754)
- `CLAIM_HEARTBEAT_SECONDS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 755)
- `CLAIM_WAIT_SECONDS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 758)
- `_CLAIM_POLL_SECONDS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 759)
- `PROCESS_TOKEN` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 760)
- `PLANNED_LABELS` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1160)
- `PLAN_PATH_STATUSES` ([src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1170)

### Explicit exports

`__all__` declares:

- `ADMISSION_REASONS`
- `CHIPS`
- `CLAIM_TASK`
- `CODE_REASONS`
- `DEPTHS`
- `DEPTH_LABELS`
- `INTENT_DEPTH`
- `LABELS`
- `LEDGER_TASK`
- `MODELS_ENV`
- `OVERRIDES`
- `PROMPT_VERSION`
- `ROUTE_TASK`
- `JudgeResult`
- `JudgeUnavailable`
- `LoStatus`
- `PLANNED_LABELS`
- `PLAN_PATH_STATUSES`
- `PathInputs`
- `PathSection`
- `PlanPath`
- `PlanSectionRef`
- `ReadingPathError`
- `ReadingPathOutputV1`
- `SectionVerdict`
- `admission_problem`
- `build_prompt`
- `claim_key`
- `depth_choice`
- `effective_label`
- `enabled`
- `exercise_view`
- `goal_for_source`
- `honest_label`
- `judge`
- `judged_sections`
- `lo_statuses`
- `next_activity`
- `open_assumption_rows`
- `override`
- `path_inputs`
- `path_view`
- `plan_path`
- `skipped_section_learning_objects`
- `pick_exercises`
- `reading_of`
- `reasons_held_back`
- `set_depth`
- `validate`

## Internal implementation anchors

- `_one_line(text: str | None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 384)
- `_intent_choice(vault: Any, repository: Repository, source_id: str, extraction_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 568) — DL2's own choice on this source (its intent-control commitment for the source or one of its readings), newest; read only.
- `_instant(value: str) -> datetime` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 596) — An ISO timestamp as an aware instant (``Z`` and offsets alike); unreadable is the epoch.
- `class _Claim` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 766)
- `_lease_now() -> str` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 776) — Wall-clock time for leases: process liveness, never the vault's clock.
- `_acquire(repository: Repository, extraction_id: str, depth: str, key: str, input_hash: str) -> tuple[str, _Claim | None]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 782) — ``("fresh", None)`` once the state's rows exist, ``("claimed", claim)``, or ``("held", None)`` when another process kept its claim past the wait.
- `_release(repository: Repository, claim: _Claim) -> None` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 810)
- `_heartbeat(repository: Repository, claim: _Claim) -> Iterator[None]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 820) — Renew the claim's lease while the call runs (stops once it is lost).
- `_ledger_question(extraction_id: str, depth: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 844)
- `_judge_claimed(vault: Any, repository: Repository, extraction_id: str, depth: str, *, inputs: PathInputs, key: str, prompt: str, input_hash: str, route: JudgeRoute, claim: _Claim, clock: Clock | None) -> JudgeResult` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 886) — The call and the rows, under ``claim`` (the caller releases it unless this returns ``ready``, which completes it).
- `_latest_ledger(connection: sqlite3.Connection, extraction_id: str, depth: str) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 950) — The newest ledger row per section on this path's question (what a new verdict supersedes).
- `_section_marker(label: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1013)
- `_done(progress: Mapping[str, Mapping[str, Any]], section_id: str) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1017)
- `_reason_by(label: str, reason: str, *, code_wrote: bool) -> str` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1077) — Who wrote the line shown: ``code`` (the evidence lines, a changed label's line, a default, a held-back reason's replacement) or ``model``.
- `_depths() -> list[dict[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/reading_paths.py), line 1086)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]] — imports `skipped_section_learning_objects`; statically calls `skipped_section_learning_objects`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `PlanPath`, `plan_path`
- [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] — imports `lo_statuses`; statically calls `lo_statuses`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `enabled`, `plan_path`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; statically calls `_done`, `exercise_label`, `goal_for_source`, `lo_statuses`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `lo_statuses`; statically calls `lo_statuses`
- [[Reference/Modules/learnloop_sidecar/handlers/reading_paths|learnloop_sidecar.handlers.reading_paths]] — imports `module`; statically calls `admission_problem`, `enabled`, `judge`, `override`, `path_inputs`, `path_view`, `reading_of`, `set_depth`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `call_labels`, `content_key`; calls `call_labels`, `content_key`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`; calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`; calls `exam_material`
- [[Reference/Modules/learnloop/content/sources/exercise_statements|learnloop.content.sources.exercise_statements]] — imports `LABEL_RE`, `NUMBER_RE`, `exercise_region_spans`, `exercise_regions`, `read_exercise_statement`, `selection_nodes`; calls `exercise_region_spans`, `exercise_regions`, `read_exercise_statement`, `selection_nodes`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgment_claims|learnloop.db.stores.judgment_claims]] — imports `CLAIMED`, `claim_work`, `complete_claim`, `holds_claim`, `release_claim`, `renew_claim`; calls `claim_work`, `complete_claim`, `holds_claim`, `release_claim`, `renew_claim`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/reading_paths|learnloop.db.stores.reading_paths]] — imports `module`; calls `insert_depth`, `insert_section`, `judged`, `latest_depth`, `latest_judged`, `overrides`, `tables_present`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `module`; calls `lo_certification`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/intent/control|learnloop.intent.control]] — imports `Scope`, `own_commitments`; calls `Scope`, `own_commitments`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `load_placement_state`; calls `load_placement_state`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `PaidRoute`, `plan_route`, `resolve_client`; calls `PaidCalls`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `extraction_sections`, `goal_for_item`; calls `extraction_sections`, `goal_for_item`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_by_section`; calls `learning_objects_by_section`
- [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]] — imports `module`; calls `best_roles`
- [[Reference/Modules/learnloop/scheduling/intent/model|learnloop.scheduling.intent.model]] — imports `CHOICE_LABEL`, `choice_for`; calls `choice_for`
- [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] — imports `load_snapshots`; calls `load_snapshots`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SharedDailyEnvelope`, `midnight`; calls `SharedDailyEnvelope`, `midnight`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `hashlib`, `json`, `math`, `os`, `sqlite3`, `threading`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]], [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_deliverable_path.py](../../../../../../tests/test_deliverable_path.py) — direct import
  - `test_already_shown_only_while_demonstrated`
- [tests/test_followups_batch6_prefetch_next_section.py](../../../../../../tests/test_followups_batch6_prefetch_next_section.py) — direct import
- [tests/test_plan_follows_path.py](../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_a_path_that_cannot_be_read_leaves_the_reading_to_the_order`
  - `test_a_source_without_a_depth_or_a_judged_path_keeps_the_predecessors_order`
  - `test_a_stored_already_shown_that_no_longer_holds_leaves_the_stale_path_to_the_order`
  - `test_an_exam_reading_plans_nothing_through_its_path`
  - `test_enrichment_already_shown_and_assumed_are_never_planned_and_nothing_left_offers_no_reading`
  - `test_g47_a_rebuild_shows_zero_projection_deltas_and_never_reads_a_path`
  - `test_read_it_anyway_makes_a_section_core_and_skip_it_leaves_one_out`
  - `test_the_path_is_read_only_when_the_plan_is_built_and_ad_slot_facts_read_the_record`
- [tests/test_reader_rw6b_p2_landing.py](../../../../../../tests/test_reader_rw6b_p2_landing.py) — direct import
  - `test_iii_the_narration_claim_and_the_reading_path_claims_are_distinct_and_independent`
- [tests/test_reading_paths.py](../../../../../../tests/test_reading_paths.py) — direct import
  - `test_a_stored_already_shown_is_shown_as_core_once_the_evidence_no_longer_holds`
  - `test_already_shown_stands_only_when_every_lo_the_section_teaches_is_demonstrated`
  - `test_an_override_writes_one_learner_card_and_one_row_and_skip_marks_nothing_known`
  - `test_assumed_stands_only_with_an_open_assumption_row`
  - `test_each_dl2_choice_maps_onto_a_depth_or_asks`
  - `test_f1_a_learner_gap_commitment_is_never_assumed_known`
  - `test_f2_try_it_carries_the_whole_exercise_and_only_the_preview_is_clipped`
  - `test_f4_a_budget_refusal_is_reconsidered_when_the_day_turns_or_the_cap_changes`
  - `test_f6_a_failed_judgment_gives_its_claim_back`
  - `test_f6_two_sidecars_opening_one_uncached_path_pay_for_one_judgment`
  - `test_honest_label_is_pure_and_total`
  - `test_next_activity_counts_read_anyway_as_core_and_is_none_when_nothing_is_left`
  - `test_section_roles_combine_role_hint_and_visible_rw4e_proposals`
  - `test_the_depth_is_asked_first_and_nothing_is_called_until_it_is_known`
  - `test_the_newer_setting_is_compared_as_instants_not_strings`
  - `test_the_state_key_hashes_depth_section_list_and_statuses_only`
- [tests/test_rw7b_codex_review_fixes.py](../../../../../../tests/test_rw7b_codex_review_fixes.py) — direct import
  - `test_f2_a_goal_change_invalidates_an_enrichment_judgment`
  - `test_f2_a_judgment_for_an_older_state_is_stale_and_the_plan_keeps_the_order`

## Modification guidance

- Make changes here when the responsibility remains reading paths within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/reading_paths.py](../../../../../../src/learnloop/source_retrieval/reading_paths.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
