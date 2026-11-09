---
title: "learnloop_sidecar.handlers.practice"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/practice.py"
source_paths:
  - "src/learnloop_sidecar/handlers/practice.py"
source_commit: "30b71186d0e5337f3d4926f8428bc46875d218cd"
source_commit_timestamp: "2026-11-09T01:27:28-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.practice module"
  - "src/learnloop_sidecar/handlers/practice.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.practice`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps practice behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `PracticeDraftCheckpoint`, `SelfGradeDisclosureInput`, `PracticeSubmissionRecoveryInput`, `PracticeSubmissionAcknowledgementInput`, `SelfGradeErrorAttributionDto`, `SelfGradeInputDto`, `SubmitAttemptInput`, `DontKnowInput` and 25 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/practice.py](../../../../../../src/learnloop_sidecar/handlers/practice.py) |
| Source lines | 2282 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `30b71186d0e5337f3d4926f8428bc46875d218cd` |
| Commit timestamp | `2026-11-09T01:27:28-05:00` |

## Public API

- `class PracticeDraftCheckpoint(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 105)
- `class SelfGradeDisclosureInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 143) — UX Phase 4 (Codex review F1): the whole trace a plain self-grade froze before it shows a full answer: the answer exactly as Submit sends it and the volunteered line apart, under the draft's retry key.
- `class PracticeSubmissionRecoveryInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 159)
- `class PracticeSubmissionAcknowledgementInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 165)
- `class SelfGradeErrorAttributionDto(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 171)
- `class SelfGradeInputDto(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 176)
- `class SubmitAttemptInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 185)
- `class DontKnowInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 235)
- `class SkipInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 262)
- `class HintRevealInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 267) — Adaptive hints H0: one authored hint the practice screen revealed.
- `class ServePracticeItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 288)
- `followup_surface(ctx: SidecarContext) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 317) — FG1 §3.1, §10: the doors with the pending and skip UI.
- `get_practice_item(ctx: SidecarContext, params: ServePracticeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 330) — Serve one item, carrying A6's elicitation decision for this serve.
- `class ProbeContractInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 462)
- `get_probe_contract(ctx: SidecarContext, params: ProbeContractInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 504) — The probe measurement contract for opening one item (§12).
- `stop_probe_diagnosing(ctx: SidecarContext, params: PracticeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 663) — `Stop diagnosing and teach me` (§3): end the measurement block, persist the typed transition decision, and open a post-intervention state segment.
- `class NextProbeItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 675)
- `get_next_probe_item(ctx: SidecarContext, params: NextProbeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 680) — The item that would continue this LO's open diagnostic block, if any.
- `class OverconfidenceProbeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 702)
- `start_overconfidence_probe(ctx: SidecarContext, params: OverconfidenceProbeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 708) — Launch a diagnostic episode from the F5 overconfidence list (§4.3).
- `save_practice_draft(ctx: SidecarContext, params: PracticeDraftCheckpoint) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 738)
- `record_hint_reveal(ctx: SidecarContext, params: HintRevealInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 782) — Adaptive hints H0 (spec_adaptive_hints_v1 §9, §10 H0): record one authored hint the practice screen revealed, as a ``help_assists`` row.
- `record_self_grade_disclosure(ctx: SidecarContext, params: SelfGradeDisclosureInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 979) — Freeze the learner's whole trace before the plain self-grade shows a full answer (UX Phase 4, Codex review F1).
- `recover_practice_submission(ctx: SidecarContext, params: PracticeSubmissionRecoveryInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1269) — Recover a completed submit before trying to serve the item again.
- `acknowledge_practice_submission(ctx: SidecarContext, params: PracticeSubmissionAcknowledgementInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1305) — Clear only the checkpoint whose authoritative result was received.
- `submit_attempt(ctx: SidecarContext, params: SubmitAttemptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1348)
- `submit_attempt_on(ctx: SidecarContext, params: SubmitAttemptInput, *, entry_surface: str=DESKTOP_PRACTICE, hint_window_fold: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1366) — ``submit_attempt``, recorded on ``entry_surface``.
- `submit_dont_know(ctx: SidecarContext, params: DontKnowInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1610)
- `submit_dont_know_on(ctx: SidecarContext, params: DontKnowInput, *, entry_surface: str=DESKTOP_PRACTICE, hint_window_fold: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1615)
- `submission_key(params: Any) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1800) — The retry key a request's attempt, receipt and model calls are keyed on.
- `answering_key(repository, submission_id: str | None, session_id: str, practice_item_id: str) -> tuple[str | None, bool]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1809) — The key a submission's attempt, intent and receipt are written under, and whether it is a successor of the client's (owner capture 2026-10-25, B4).
- `skip_practice_item(ctx: SidecarContext, params: SkipInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 2014)
- `mark_released_held(payload: dict[str, Any], repository) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 2119) — UX Phase 4 (display only): each released short-check answer says whether its grade is held for review (THE held predicate), so the result shows "held for review" and never the grader's provisional score.

### Module constants

- `HINT_TELEMETRY_RPCS` ([src/learnloop_sidecar/handlers/practice.py](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 285)
- `_OTHER_SESSION` ([src/learnloop_sidecar/handlers/practice.py](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 468)

## Internal implementation anchors

- `_require_active_item(vault, practice_item_id: str)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 302) — One terminal lifecycle gate for every practice write/serve.
- `_schedule_approach_map(ctx: SidecarContext, vault, repository, practice_item_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 453)
- `_committed_presentation(repository, episode, session_id: str | None)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 471) — The durable presentation this open of the item should consume.
- `_probe_contract(ctx: SidecarContext, vault: Any, repository: Any, item: Any, params: ProbeContractInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 541)
- `_with_intent_check(vault: Any, repository: Any, practice_item_id: str, payload: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 647) — DL2 verify F15 (fix round 4, R3): an active diagnostic presentation of a due "Check once" item is the check, served under the diagnostic's duty; the contract (the server's word that this is a probe) carries the check's measured view, which promises no help.
- `_draft_marker(vault, params: PracticeDraftCheckpoint) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 766) — AD1 (§11.2): the draft's first-hint progress marker, kept with its retry key; untouched by a client that does not send it, and never kept with ``adaptive_difficulty.forecast_receipts`` off.
- `_in_diagnostic_block(repository, item) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 830) — The item is being served as a diagnostic probe (an in-progress episode with a served presentation of this item): the screen refuses hints then (probe redesign §5.5), so no reveal is recorded either.
- `_earlier_opened_hint(repository, session_id: str | None, practice_item_id: str) -> int` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 842) — Reader CA2 (K6, Q2; Codex review F1): one hint-equivalent when the attempt opened an earlier attempt's help before Submit, counted by the server whichever surface submits; 0 otherwise.
- `_server_hint_fold(repository, practice_item_id: str, session_id: str, submission_id: str | None, *, base_hints: int, base_primed: bool=False, max_useful_hints: int=0, clamp_without_fold: bool=True, stuck_types: tuple[str, ...] | None=None, stuck_probe: bool=False, window_fold: bool=False, held: dict[str, Any] | None=None, any_session: bool=False) -> ServerHintFold` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 873) — Adaptive hints H2a (spec §5, G-H2, G-H3): the hints the hint service showed in this submission (its ``help_assists`` rows, shown, counted by the server, still unattached): how many at levels 1-3, and whether any was worked help (levels 4-5, ``primed``), with the rule this submit…
- `_stamp_hint_submission(vault, repository, submission_id: str | None, practice_item_id: str, latency_seconds: float | None=None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 914) — Adaptive hints H0 (review F2, round 2 V3): when this submission reached the sidecar, before any grading, and the latency it sent, on its revealed hints' rows.
- `_stamp_window_hints(repository, fold: ServerHintFold, submitted_at: str | None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 933) — H2b re-review F9 under fix round 3's ruling R1: a workbench submission's submit time on the window's rows it folds (requested under the answer box's key, so the keyed stamp above never reaches them).
- `_attach_hint_reveals(vault, repository, submission_id: str | None, practice_item_id: str, attempt_id: str, *, submitted_at: str | None=None, latency_seconds: float | None=None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 951) — Adaptive hints H0: the attempt the submission's revealed hints were part of, matched on the submission key alone (review F1), so it is idempotent and every path that answers for a committed submission (the submit, a retry from its receipt, a resumed completion, a recovery) repai…
- `_record_disclosure_display(repository, item, params: SelfGradeDisclosureInput, submission_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1031) — One display of the key on a pending plain self-grade (UX Phase 4, round 3 F1): a routine display row written while the draft is pending, so every other production is judged against it at once; the frozen trace's own commit is exempt (``reveal_ledger.own_disclosure_bases``).
- `_changed_after_disclosure(repository, session_id: str, practice_item_id: str, submission_id: str | None, learner_answer_md: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1080) — Did the learner submit a trace other than the one frozen before the plain self-grade showed a full answer (UX Phase 4, Codex review F1)?
- `_plan_presentation(repository, params: Any) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1105) — The plan presentation an answer binds to: the one it sends, else the one its saved draft named under the same retry key (router R2a, review F5: a draft resumed after a restart).
- `_held_assistance(repository, item, hints_used: int, attempt_type: str, *, held: tuple[Any, ...] | None=None, authored_hints: int | None=None, book_counted: bool | None=None) -> tuple[int, str]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1124) — Fold in the assistance the item's open workbench problems hold (Reader workbench RW2a, review F2): the book one counted and the answer-box hints it carried.
- `_held_read(repository, item) -> tuple[tuple[tuple[int, int], ...], bool]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1160) — Reader workbench RW2b (§5.4): the help the item's open problems hold, ``(parts, primed)``: per problem ``(book, carried, assist_ids)`` (fix rounds 4 and 5, items 4-5), and whether any showed worked help (a level 4-5 hint, which primes every submit of the item).
- `_held_parts_with_window(connection, practice_item_id: str)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1179) — The open problems' RW2a parts (book, carried) and, as one more part, the item's WINDOW of workbench server assists (RW2b fix round 13: H2b's R1 rule, whatever their problem's status, ``help_assists.workbench_window_ids``), which the attempt counts once and attaches in its own tr…
- `_held_reader(practice_item_id: str)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1197) — RW2b fix round 1, F1: the same read on the attempt's own write connection, for its transactional refold (the attempt path never reads the workbench; the sidecar hands it this callable).
- `_held_fields(item, held: tuple[tuple[Any, ...], bool], *, client_hints: int, extra_hints: int, attempt_types: bool, authored_hints: int | None=None, client_book: bool | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1214)
- `_origin_bind_surface(ctx: SidecarContext) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1231) — A draft's binding surface: the phone's, or the store's default on the desktop.
- `_bind_offer(repository, params, submission_id, *, entry_surface: str | None=None)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1237)
- `_refuse_phone_probe_answer(ctx: SidecarContext, probe_presentation_id: str | None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1353) — Mobile v2 V3 (D3): a phone answers a probe's presentation only with ``phone_probes`` on and the vault at the successor's tag.
- `_schedule_hint_outcome(ctx: SidecarContext, vault, repository, attempt_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1597)
- `_record_empty_stuck(ctx: SidecarContext, vault, repository, draft: AttemptDraft, session_id: str, before, *, hint_submitted_at: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1746) — Commit an empty "I'm stuck" answer and answer like any submission.
- `_submission_id(client_id: str | None, presentation_id: str | None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1790) — Return the stable retry key; old probe clients inherit one for free.
- `_without_stale_help(repository, params: Any, *, successor: bool) -> tuple[Any, bool]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1837) — The submit's params with the help a stale draft carried taken out, and whether the draft was stale (owner capture 2026-10-25, fix round 2, item 2).
- `_window_authored_reveals(repository, practice_item_id: str, session_id: str) -> int` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1876) — The authored hints the practice screen revealed on the item in this session since its last attempt there (H0 rows; any key): a read.
- `_cached_submission(ctx: SidecarContext, vault, repository, submission_id: str | None, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1895) — The response for a submission that was already committed, if any.
- `_resume_saved_completion(ctx: SidecarContext, vault, repository, work: dict[str, Any], submission_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1938) — Complete a committed attempt from its saved result and store the receipt.
- `_normalization_client(ctx: SidecarContext, vault) -> Any | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1963)
- `_open_session_id(repository, session_id: str | None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1968)
- `_require_same_item(recorded_item_id: str, practice_item_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1977)
- `_submission_committed(attempt: dict[str, Any]) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1982)
- `_store_submission_receipt(repository, submission_id: str | None, attempt_id: str, practice_item_id: str, payload: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 1995)
- `_self_grade(payload: SelfGradeInputDto | None) -> SelfGradeInput | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 2066)
- `_attempt_result(result, repository=None, vault=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 2084)
- `_log_attempt_recorded(repository, session_id: str, answer_md: str, result) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 2135)
- `_latent_snapshot(vault, repository, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 2160) — Capture pre-attempt latent state for a practice item, for debug deltas.
- `_log_state_update(vault, repository, method_name: str, session_id: str, before, result) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 2189)
- `_display_mean(mastery) -> float | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 2260)
- `_display_variance(mastery) -> float | None` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 2268)
- `_require_open_session(repository, session_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice.py), line 2276)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `_in_diagnostic_block`; statically calls `_in_diagnostic_block`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `_log_attempt_recorded`; statically calls `_log_attempt_recorded`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `_earlier_opened_hint`; statically calls `_earlier_opened_hint`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `ServePracticeItemInput`, `SubmitAttemptInput`, `_cached_submission`, `_earlier_opened_hint`, `get_practice_item`, `submit_attempt_on`; statically calls `ServePracticeItemInput`, `SubmitAttemptInput`, `_cached_submission`, `_earlier_opened_hint`, `get_practice_item`, `submit_attempt_on`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `_in_diagnostic_block`; statically calls `_in_diagnostic_block`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `submission_key`; statically calls `submission_key`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `receipts_enabled`; calls `receipts_enabled`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptDraft`, `AttemptResult`, `AttemptValidationError`, `SelfGradeErrorAttribution`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_ai_required`, `complete_attempt_with_codex_fallback`, `complete_attempt_with_codex_required`, `complete_empty_stuck_attempt`, `complete_self_graded_attempt`; calls `AttemptDraft`, `SelfGradeErrorAttribution`, `SelfGradeInput`, `complete_attempt_with_ai_fallback`, `complete_attempt_with_ai_required`, `complete_attempt_with_codex_fallback`, `complete_attempt_with_codex_required`, `complete_empty_stuck_attempt`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/attempts/hint_fold|learnloop.attempts.hint_fold]] — imports `ServerHintFold`, `combine_held`, `fold_follows_attach`, `held_components`, `read_fold`; calls `ServerHintFold`, `combine_held`, `fold_follows_attach`, `held_components`, `read_fold`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `CompletionRouteUnknown`, `probe_route`, `run_post_attempt_pipeline`; calls `probe_route`, `run_post_attempt_pipeline`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `DisplayNotRecorded`, `frozen_trace_hash`, `record_self_grade_disclosure_display`; calls `frozen_trace_hash`, `record_self_grade_disclosure_display`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `stuck_attempt_type`, `stuck_prompt_active`; calls `stuck_attempt_type`, `stuck_prompt_active`
- [[Reference/Modules/learnloop/attempts/trace_evidence|learnloop.attempts.trace_evidence]] — imports `compose_learner_trace`, `decide_elicitation`, `elicited_explanations_in`; calls `compose_learner_trace`, `decide_elicitation`, `elicited_explanations_in`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `SystemClock`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `CODEX_PROVIDER_NAMES`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `PlanEnv`, `open_randomized_check`; calls `PlanEnv`, `open_randomized_check`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `authored_reveals_in_window`, `keyless_window_start`, `workbench_window`; calls `authored_reveals_in_window`, `keyless_window_start`, `workbench_window`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `calibration_cap_lifted`, `routine_planner_shadow`; calls `calibration_cap_lifted`, `routine_planner_shadow`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `PROBE_ITEM_ANSWER_SHOWN`, `RoutineDisplayCovered`, `commit_item_presentation`, `enter_episode`, `episode_contract`, `episode_hypothesis_set`, `next_probe_item`, `probe_serving_block_reason`, `probe_value_block_reason`, `routine_display_covers_item`, `serve_presentation`, `stop_diagnosing_and_teach`, `validate_presentation_for_submission`; calls `commit_item_presentation`, `enter_episode`, `episode_contract`, `episode_hypothesis_set`, `next_probe_item`, `probe_serving_block_reason`, `probe_value_block_reason`, `routine_display_covers_item`, `serve_presentation`, `stop_diagnosing_and_teach`, `validate_presentation_for_submission`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `probe_posterior`; calls `probe_posterior`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `NOT_NEEDED`, `diagnosis_status`; calls `diagnosis_status`
- [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] — imports `abandon`; calls `abandon`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `PHONE_SURFACE`, `SERVING_SURFACE`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `workflow_of_item`; calls `workflow_of_item`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_attempt_ids`; calls `held_attempt_ids`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `schedule_build_on_serve`; calls `schedule_build_on_serve`
- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `schedule_outcome_placement`; calls `schedule_outcome_placement`
- [[Reference/Modules/learnloop/hints/telemetry|learnloop.hints.telemetry]] — imports `attach_reveals_to_attempt`, `record_authored_reveal`, `stamp_submission`, `stamp_window_submission`, `telemetry_enabled`; calls `attach_reveals_to_attempt`, `record_authored_reveal`, `stamp_submission`, `stamp_window_submission`, `telemetry_enabled`
- [[Reference/Modules/learnloop/intent/checks|learnloop.intent.checks]] — imports `DUTY_DIAGNOSTIC`, `cold_followup_view`, `served_check`; calls `cold_followup_view`, `served_check`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `display_mastery`; calls `display_mastery`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `episode_ignored`, `servable_open_episode`; calls `episode_ignored`, `servable_open_episode`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `held_earlier`, `held_parts_on`; calls `held_earlier`, `held_parts_on`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `SchedulerSession`, `build_due_queue`; calls `SchedulerSession`, `build_due_queue`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `hint_equivalents_for_submission`; calls `hint_equivalents_for_submission`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `to_camel`, `versioned`; calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `ready_grading_provider`; calls `ready_grading_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `deliver_on_open`, `select_on_open`; calls `deliver_on_open`, `select_on_open`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `PracticeItemInput`, `_sections`, `eligibility_dto`, `offer_trace_for`, `publish_offer`, `record_diagnosis_serve`, `revalidate_cold_check`; calls `_sections`, `eligibility_dto`, `offer_trace_for`, `publish_offer`, `record_diagnosis_serve`, `revalidate_cold_check`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `practice_item_detail`; calls `practice_item_detail`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `KEEP_EARLIER_OPENED`, `KEEP_HINT_SEEN`, `KEEP_MARKER`, `SessionCheckpointInput`, `checkpoint_plan_presentation`, `clear_checkpoint`, `draft_earlier_opened`, `draft_plan_presentation`, `draft_self_grade_disclosure`, `patch_checkpoint`, `phone_claim_owner`, `require_owned_session`, `settle_self_grade_disclosure`; calls `SessionCheckpointInput`, `checkpoint_plan_presentation`, `clear_checkpoint`, `draft_earlier_opened`, `draft_plan_presentation`, `draft_self_grade_disclosure`, `patch_checkpoint`, `phone_claim_owner`, `require_owned_session`, `settle_self_grade_disclosure`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `debug_enabled`, `log_event`; calls `debug_enabled`, `log_event`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`
- [[Reference/Modules/learnloop_sidecar/request_origin|learnloop_sidecar.request_origin]] — imports `DESKTOP_PRACTICE`, `PHONE_PRACTICE`, `host_mutation`, `phone_probes_on`, `practice_surface`; calls `phone_probes_on`, `practice_surface`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `device_filter`, `refuse_device_ineligible_item`, `refuse_generated_probe_door`, `refuse_held_out_item`, `refuse_inactive_learning_object`, `refuse_unservable_item`; calls `device_filter`, `refuse_device_ineligible_item`, `refuse_generated_probe_door`, `refuse_held_out_item`, `refuse_inactive_learning_object`, `refuse_unservable_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `sqlite3`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]], [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]], [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]], [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/mobile_host_helpers.py](../../../../../../tests/mobile_host_helpers.py) — direct import
- [tests/rw2b_fix10_base_sequence.py](../../../../../../tests/rw2b_fix10_base_sequence.py) — direct import
- [tests/rw2b_fix11_base_sequence.py](../../../../../../tests/rw2b_fix11_base_sequence.py) — direct import
- [tests/test_approach_maps.py](../../../../../../tests/test_approach_maps.py) — direct import
  - `test_a_failing_or_raising_build_never_reaches_the_serve`
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_serving_the_pinned_probe_reuses_its_presentation`
- [tests/test_device_eligibility.py](../../../../../../tests/test_device_eligibility.py) — direct import
- [tests/test_followups_nov2_help_fold.py](../../../../../../tests/test_followups_nov2_help_fold.py) — direct import
  - `test_a_counted_row_is_attached_in_the_attempts_own_transaction`
- [tests/test_help_fold_attach_successor.py](../../../../../../tests/test_help_fold_attach_successor.py) — direct import
  - `test_the_fold_is_gated_by_the_tag_and_the_switch`
- [tests/test_hint_h2a_review_round2.py](../../../../../../tests/test_hint_h2a_review_round2.py) — direct import
  - `test_v1_a_hint_delivered_after_the_fold_and_before_the_commit_is_counted`
- [tests/test_hint_h2a_review_round3.py](../../../../../../tests/test_hint_h2a_review_round3.py) — direct import
  - `test_w1_a_delivery_before_a_keyless_commit_is_counted`
- [tests/test_hint_h2b_fix3.py](../../../../../../tests/test_hint_h2b_fix3.py) — direct import
  - `test_r1_f10_an_interrupted_answer_box_attach_never_lets_a_problem_take_the_hint`
- [tests/test_hint_h2b_fix4.py](../../../../../../tests/test_hint_h2b_fix4.py) — direct import
  - `test_f12_a_hint_delivered_during_a_workbench_grade_is_stamped_when_the_attempt_takes_it`
- [tests/test_hint_h2b_review.py](../../../../../../tests/test_hint_h2b_review.py) — direct import
  - `test_f7_surface_filters_the_chooser_statistics_and_avoidance`
- [tests/test_hint_kill_switch.py](../../../../../../tests/test_hint_kill_switch.py) — direct import
  - `test_no_hint_request_reaches_a_model_during_a_diagnostic_block`
- [tests/test_hint_telemetry.py](../../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_a_failed_attach_is_repaired_by_recovery_and_never_given_to_the_next_attempt`
  - `test_a_failed_write_never_fails_the_reveal_or_the_submit`
  - `test_a_retried_submit_repairs_a_failed_attach`
  - `test_a_row_without_a_submit_time_is_timed_unknown_not_from_the_grade`
  - `test_an_attempt_without_its_receipt_is_attached_when_its_completion_resumes`
  - `test_kill_switch_writes_nothing_and_the_rpc_is_a_no_op`
  - `test_no_row_during_a_diagnostic_block`
  - `test_reveal_to_submit_ends_at_the_submit_not_at_the_graded_attempt`
  - `test_seconds_into_the_attempt_is_unknown_without_the_submits_latency`
  - `test_the_diagnostic_block_is_a_served_probe_of_this_item`
- [tests/test_intent_fix_round4.py](../../../../../../tests/test_intent_fix_round4.py) — direct import
  - `test_f15_the_probe_contract_carries_the_diagnostic_variant`
- [tests/test_library_exercises.py](../../../../../../tests/test_library_exercises.py) — direct import
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_hints_h0_rpcs_are_all_of_them`
- [tests/test_mobile_jobs.py](../../../../../../tests/test_mobile_jobs.py) — direct import
  - `test_a_completion_that_can_never_finish_says_recorded_and_never_failed`
  - `test_a_failure_the_runtime_can_not_check_is_not_reported_failed`
  - `test_a_recovery_that_answers_pending_finishes_nothing`
  - `test_the_attempt_of_a_successor_key_counts_for_its_job`
- [tests/test_mobile_two_process.py](../../../../../../tests/test_mobile_two_process.py) — direct import
- [tests/test_mobile_v2_followup.py](../../../../../../tests/test_mobile_v2_followup.py) — direct import
  - `test_f3_a_phone_miss_opens_its_workflow_held_under_the_phones_surface`
- [tests/test_mobile_v3_probes.py](../../../../../../tests/test_mobile_v3_probes.py) — direct import
  - `test_g10_a_phone_admission_is_one_transaction_with_its_cap_count`
- [tests/test_owner_capture_1025.py](../../../../../../tests/test_owner_capture_1025.py) — direct import
- [tests/test_reader_rw2b_fix10.py](../../../../../../tests/test_reader_rw2b_fix10.py) — direct import
  - `test_item3_the_refold_never_drops_an_assist_it_already_counted`
- [tests/test_reader_rw2b_fix11.py](../../../../../../tests/test_reader_rw2b_fix11.py) — direct import
  - `test_item2_the_refold_applies_the_same_floor`
- [tests/test_reader_rw2b_fix12.py](../../../../../../tests/test_reader_rw2b_fix12.py) — direct import
  - `test_item1_end_to_end_a_problem_submitted_during_grading_is_not_counted_twice`
  - `test_item2_the_refold_keeps_the_client_held_book`
- [tests/test_reader_rw2b_fix4.py](../../../../../../tests/test_reader_rw2b_fix4.py) — direct import
  - `test_item4_the_transactional_refold_adds_a_check_shown_during_grading`
- [tests/test_reader_rw2b_review.py](../../../../../../tests/test_reader_rw2b_review.py) — direct import
- [tests/test_reader_rw4b_fix6.py](../../../../../../tests/test_reader_rw4b_fix6.py) — direct import
  - `test_f13_the_admissions_serve_and_its_served_record_share_one_transaction`
- [tests/test_reader_workbench_rw2a.py](../../../../../../tests/test_reader_workbench_rw2a.py) — direct import
  - `test_an_empty_submit_is_the_existing_empty_stuck_answer_with_no_model_call`
  - `test_f4_a_practice_problem_resumed_in_the_reader_moves_there_book_hidden_and_counts_the_book_if_shown`
- [tests/test_request_origin.py](../../../../../../tests/test_request_origin.py) — direct import
  - `test_a_submit_accepted_before_a_handoff_keeps_the_phones_surface`
- [tests/test_session_ownership.py](../../../../../../tests/test_session_ownership.py) — direct import
  - `test_a_skip_never_clears_the_draft_of_a_device_that_adopted_while_the_queue_was_built`
  - `test_a_skip_refuses_a_session_that_moved_and_came_back_while_the_queue_was_built`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_interrupted_submission_resumes_saved_result_once`
  - `test_recovery_normalizes_with_the_configured_grading_provider`
  - `test_submission_that_loses_a_commit_race_answers_with_the_winner`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_sidecar_text_stuck_answer_is_graded_like_any_answer`
  - `test_the_draft_checkpoint_keeps_the_stuck_marker_across_a_restart`
  - `test_tui_empty_stuck_probe_answer_keeps_feedback_deferred`
  - `test_tui_empty_stuck_submit_shows_the_result_and_the_worked_answer`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1l_the_scheduler_never_commits_or_serves_a_covered_probe`
  - `test_released_short_check_feedback_marks_held_grades`
- [tests/test_workbench_check.py](../../../../../../tests/test_workbench_check.py) — direct import
  - `test_during_a_diagnostic_block_no_check_or_hint_reaches_a_model`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/practice.py](../../../../../../src/learnloop_sidecar/handlers/practice.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
