# LearnAnything MVP Implementation Plan

This file is the implementation roadmap for `spec_mvp.md`. It starts from the
current repository state and continues through the full MVP: storage, scheduler,
CLI, Textual TUI, Codex authoring and grading, Probe-EIG, observation templates,
and negative-surprise follow-ups.

The plan is intentionally sliced so each step can be implemented, tested, and
reviewed without depending on later AI or TUI work. CLI and Textual must both
call the same service layer. Codex must never write vault files directly.

## Current Baseline

Implemented in the first slice:

- Python package scaffold under `src/learnloop`.
- `pyproject.toml` with Typer, Textual, Pydantic v2, ruamel.yaml, and pytest.
- Clock and ULID helpers.
- Default `learnloop.toml` config.
- Vault init that creates the MVP directory skeleton and applies migrations.
- Vault loaders for subjects, concepts, relations, goals, notes, Learning
  Objects, Practice Items, and error types.
- YAML/frontmatter helpers using ruamel.yaml.
- Content hash helpers for core YAML entities.
- SQLite migration runner using `migrations/001_initial.sql`.
- Repository foundations for item state, mastery, active errors, probe state,
  scheduler explanations, proposal decisions, and generic inspection.
- Repository coverage for deterministic attempts, grading evidence, error
  events, attempt surprise, sessions/checkpoints, agent runs, and proposal
  batches.
- FSRS, scalar mastery helpers, and first deterministic scheduler components.
- State sync for Practice Item state and Learning Object mastery initialization.
- Controlled YAML writer operations for concepts, concept edges, Learning
  Objects, Practice Items, and error types.
- Structured doctor service with layout, schema, migration, reference, derived
  state, proposal validity, JSON, and `--fix-state` checks.
- Deterministic self-grade attempt flow with FSRS, mastery, surprise, and CLI
  JSON output.
- `learnloop show` enriches attempts with grading evidence and surprise, and
  proposal batches with proposal items.
- Scheduler golden tests cover due-date suppression, inactive filtering,
  lexicographic ties, active-goal edge rules, and recent-error decay.
- Proposal patch compiler/applier writes accepted proposal items through the
  vault writer, records `change_batches` and `content_events`, marks
  `applied_change_batch_id`, and runs state sync for affected content.
- `learnloop propose --file` imports validated `AuthoringProposal` JSON/YAML
  into `agent_runs`, `proposed_patches`, and `proposed_patch_items` so proposal
  review can be exercised without a live Codex runtime.
- Codex runtime status checks report `codex_missing`,
  `codex_revision_mismatch`, `codex_unavailable`, `codex_auth_required`, and
  `ready`, and doctor exposes that status without breaking local workflows.
- Codex grading context building, grading proposal validation, and a fake
  Codex-grade attempt path write tier-3 evidence through the same post-grade
  FSRS, mastery, surprise, and error-event updates as self-grade.
- Codex grading orchestration attempts a ready `CodexClient`, persists
  `agent_runs`, and falls back to self-grade on runtime, timeout, or validation
  failure while preserving local learning.
- CLI JSON contract tests cover `doctor`, `review`, `why`, `show`,
  `proposals`, and `attempt`.
- Deferred Codex regrade finds non-superseded tier-1 evidence, calls a
  `CodexClient`, writes tier-3 evidence, supersedes tier-1 rows, delta-updates
  mastery, refreshes attempt grade fields, isolates failed runs, and writes
  `regrade_disagreement` content events for large score deltas.
- CLI shell for the MVP command surface.
- Minimal Textual app scaffold.
- Codex schema and protocol scaffolds.
- Initial tests for vault init and scheduler scoring.

Known placeholders:

- `learnloop propose --file` can import proposal files and Codex runtime status
  is checkable; live Codex-backed authoring generation is not implemented yet.
- Real Codex transport is not implemented; deterministic self-grade, validated
  fake Codex-grade paths, Codex fallback orchestration, and deferred regrade
  service logic exist.
- `learnloop accept` applies accepted proposal items for concepts, concept
  edges, Learning Objects, Practice Items, rubrics, and error types through the
  controlled writer. Codex-backed proposal generation is still pending.
- Textual screens are scaffolds only.
- Probe-EIG, observation templates, surprise follow-up insertion, and Codex
  transport are not implemented yet.

## Engineering Rules

- Keep all durable behavior behind services and repositories.
- Keep CLI and Textual thin: parse input, render output, call services.
- Use SQLite only through repository modules.
- Use YAML writes only through vault helpers and proposal application services.
- Use `clock.py` for time everywhere.
- Keep Codex outputs typed, validated, persisted, and reviewable before any
  content mutation.
- Make deterministic tests pass without Codex, Textual, network, or local app
  server dependencies.
- Prefer small migrations over in-place schema drift.
- Every slice should end with tests and a CLI smoke check where applicable.

## MVP Milestones

1. Finish storage foundation.
2. Implement deterministic attempt, grading fallback, FSRS, mastery, and
   scheduler state.
3. Bring CLI parity for deterministic workflows.
4. Add scheduler fixture and golden tests.
5. Build a one-day Textual today-loop spike.
6. Expand to full Textual today, practice, and feedback screens.
7. Implement Codex runtime adapter and proposal persistence.
8. Implement Codex grading with self-grade fallback and deferred regrade.
9. Implement Codex authoring proposals and YAML patch application.
10. Implement Probe-EIG.
11. Implement observation templates and negative-surprise follow-ups.
12. Harden, document, and prepare the MVP for daily use.

## Slice 1: Storage Foundation Completion

Goal: make the local vault and SQLite state reliable enough for all later
services.

### 1.1 Repository Coverage

Add repository methods for:

- `practice_attempts`
  - insert attempt
  - fetch by id
  - list recent by Practice Item
  - list recent by Learning Object
- `grading_evidence`
  - insert criterion evidence rows
  - fetch current evidence for an attempt
  - supersede self-grade rows during deferred Codex regrade
- `error_events`
  - insert active error event
  - resolve error event
  - fetch active errors by LO
- `attempt_surprise`
  - insert computed surprise row
  - fetch latest by attempt
- `practice_item_state`
  - initialize missing rows from loaded Practice Items
  - update after FSRS review
  - deactivate missing or dormant content
- `learning_object_mastery`
  - initialize missing LO rows
  - update after attempt
  - fetch with display-ready mastery values
- `sessions` and `session_checkpoints`
  - create session
  - update checkpoint
  - clear checkpoint after grade
- `scheduler_explanations`
  - latest by item
  - latest by session
  - prune or mark superseded if needed later
- `agent_runs`, `proposed_patches`, `proposed_patch_items`
  - insert agent run
  - complete/fail agent run
  - persist proposal batch and item rows
  - derive batch status from item decisions

Files:

- `src/learnloop/db/repositories.py`
- `tests/test_repositories.py`

Acceptance:

- Repository tests cover every insert/update path.
- Foreign key behavior is enabled on all connections.
- No service writes SQL directly.

### 1.2 Vault State Sync

Add a service that reconciles loaded YAML with SQLite derived state.

Responsibilities:

- For every loaded Practice Item:
  - compute `practice_item_hash`
  - create missing `practice_item_state`
  - update `content_hash` when semantic content changes
  - preserve existing FSRS state when content hash is unchanged
  - reset or flag state when content hash changes, depending on policy
- For every loaded Learning Object:
  - create missing `learning_object_mastery`
  - create or refresh related probe state later, once Probe-EIG lands
- For missing YAML entities that still have SQL state:
  - mark `practice_item_state.active = 0`
  - leave historical attempts intact
- Stamp `algorithm_version` on derived rows.

Files:

- `src/learnloop/services/state_sync.py`
- `src/learnloop/db/repositories.py`
- `tests/test_state_sync.py`

Acceptance:

- `learnloop doctor` or app startup can call state sync safely multiple times.
- Sync is idempotent.
- Scheduler can assume required derived rows exist.

### 1.3 YAML Write Operations

Implement controlled YAML writes for app-owned content.

Operations:

- Create or update concepts in `concepts/concepts.yaml`.
- Create or update edges in `concepts/relations.yaml`.
- Create or update Learning Object YAML under the primary subject.
- Create or update Practice Item YAML under the primary subject.
- Create or update `errors/error_types.yaml`.
- Preserve unknown keys where practical.
- Use stable field order for app-created files.
- Update `updated_at` and keep `created_at` stable.
- Reject arbitrary paths.

Files:

- `src/learnloop/vault/yaml_io.py`
- `src/learnloop/vault/writer.py`
- `tests/test_vault_writer.py`

Acceptance:

- Round-trip tests preserve unknown keys.
- Writer refuses subject/path mismatches unless the service explicitly moves an
  entity.
- Writer output passes loader validation.

### 1.4 Doctor Expansion

Expand `learnloop doctor` from loader issue reporting into a real health check.

Checks:

- Required directory layout exists.
- `learnloop.toml` exists and validates.
- SQLite exists and has all migrations applied.
- YAML schema versions are supported.
- Duplicate YAML IDs are flagged.
- Missing concept, subject, LO, PI, and error-type references are flagged.
- Primary subject mismatches are warnings.
- Fatal rubric errors not in `error_types.yaml` are warnings.
- Practice Items without resolved rubrics are warnings or errors depending on
  whether a default rubric exists.
- SQL state missing for YAML entities is reported and optionally fixable.
- SQL state for missing YAML entities is reported.
- Pending proposal items that are invalid are reported.

CLI:

- `learnloop doctor`
- `learnloop doctor --json`
- `learnloop doctor --fix-state` for safe derived-state sync only

Files:

- `src/learnloop/services/doctor.py`
- `src/learnloop/cli.py`
- `tests/test_doctor.py`

Acceptance:

- Doctor exits `0` when clean, `1` when issues exist.
- JSON output is stable for golden tests.
- `--fix-state` never mutates YAML content.

## Slice 2: Deterministic Attempt Flow

Goal: implement attempts that work without Codex.

### 2.1 Attempt Lifecycle

Implement an `AttemptService`.

Flow:

1. Load the target Practice Item and its Learning Object.
2. Resolve the rubric.
3. Validate the requested attempt type.
4. Record `practice_attempts`.
5. Collect self-grade input when Codex is unavailable or not requested.
6. Write `grading_evidence`.
7. Write `error_events` for selected error attributions.
8. Update FSRS item state.
9. Update LO mastery.
10. Compute surprise.
11. Return a structured result for CLI and Textual.

Attempt type rules:

- `guided_walkthrough` and `skip` do not write `practice_attempts`.
- `dont_know` forces rubric score to `0`.
- `hinted_attempt` applies hint caps and mastery dampening.
- `diagnostic_probe` counts as full evidence.

Files:

- `src/learnloop/services/attempts.py`
- `src/learnloop/services/grading.py`
- `src/learnloop/services/fsrs.py`
- `src/learnloop/services/mastery.py`
- `tests/test_attempts.py`

Acceptance:

- One call logs an attempt and updates all derived state.
- All writes happen in a transaction or with a clearly recoverable boundary.
- Service returns enough data for CLI/TUI feedback.

### 2.2 Self-Grade Fallback

Implement the MVP self-grade fallback before Codex grading.

Inputs:

- Per-criterion points or checkbox.
- Optional fatal error IDs.
- Optional error type.
- Confidence `1..5`.
- Optional notes.

Behavior:

- Map confidence to grader confidence: `1 -> 0.2`, `2 -> 0.4`, `3 -> 0.6`,
  `4 -> 0.8`, `5 -> 1.0`.
- Write one `grading_evidence` row per criterion.
- Use `grader_tier = 1`, `local_grader_id = "self"`.
- Cap rubric score by fatal errors.
- Set `manual_review_reason = "low_self_confidence"` when confidence is below
  the threshold in the spec.

Files:

- `src/learnloop/services/grading.py`
- `src/learnloop/cli.py`
- `tests/test_self_grade.py`

Acceptance:

- CLI can complete an attempt without Codex.
- Low confidence is recorded but does not block deterministic updates unless
  the service policy explicitly says so.

### 2.3 FSRS State Update

Complete FSRS behavior around attempts.

Behavior:

- Convert rubric score to Again/Hard/Good/Easy.
- Apply hint cap from `hint_policy.fsrs_rating_cap_by_hint`.
- Apply FSRS update from previous state.
- Set next `due_at` from the new stability and desired retention.
- Store `difficulty`, `stability`, `retrievability`, `last_attempt_at`, and
  `updated_at`.
- Include interval factor from surprise once surprise is implemented.

Files:

- `src/learnloop/services/fsrs.py`
- `src/learnloop/services/attempts.py`
- `tests/test_fsrs.py`

Acceptance:

- Golden tests lock deterministic updates for first review and later reviews.
- Hint caps cannot increase rating.

### 2.4 Mastery State Update

Complete the logit-space Kalman update.

Behavior:

- Resolve evidence coverage from rubric criteria and evidence facets.
- Apply hint dampening.
- Apply grader confidence.
- Apply attempt type factor.
- Create missing mastery state using defaults or learner claims later.
- Store `logit_mean`, `logit_variance`, evidence count, and timestamps.

Files:

- `src/learnloop/services/mastery.py`
- `src/learnloop/services/attempts.py`
- `tests/test_mastery.py`

Acceptance:

- Tests cover positive score, zero score, low confidence, hint dampening, and
  drift over time.

### 2.5 Error Attribution

Implement error event creation from grading results.

Behavior:

- Known error type:
  - use taxonomy severity default when severity is absent
  - write `error_events`
- Unknown error type:
  - still accept grading
  - write `error_events` with literal error type
  - create pending error taxonomy proposal later in Codex/proposal slice
- Fatal rubric IDs remain scoped to the rubric but doctor warns if not aligned
  to the taxonomy.

Files:

- `src/learnloop/services/grading.py`
- `src/learnloop/services/attempts.py`
- `tests/test_error_events.py`

Acceptance:

- Recent-error scheduler boost reflects newly written errors.
- Unknown taxonomy entries are visible to doctor.

### 2.6 Surprise Computation

Implement MVP surprise tables and formulas.

Behavior:

- Compute predictive surprise.
- Compute Bayesian surprise.
- Compute FSRS interval factor.
- Compute score bucket and observed error type.
- Emit `surprise_direction` as positive, negative, or none.
- Store JSON columns exactly as specified.

Files:

- `src/learnloop/services/surprise.py`
- `src/learnloop/services/attempts.py`
- `tests/test_surprise.py`

Acceptance:

- Tests cover positive, negative, none, and error-type surprise.
- Surprise does not require Probe-EIG to exist.

## Slice 3: CLI Parity for Deterministic Core

Goal: make the CLI a real first-class workflow for local learning.

### 3.1 Stable JSON Output Contracts

Add `--json` output to:

- `review`
- `why`
- `show`
- `proposals`
- `doctor`
- `attempt`

Contracts:

- Use stable key ordering.
- Use explicit version fields where useful.
- Avoid printing human text to stdout when `--json` is set.
- Send diagnostics to stderr when needed.

Files:

- `src/learnloop/cli.py`
- `src/learnloop/cli_output.py`
- `tests/test_cli_json.py`

Acceptance:

- Golden tests compare full JSON shapes.

### 3.2 `learnloop attempt`

Implement a scriptable attempt path.

Modes:

- Interactive prompt for answer and self-grade.
- Non-interactive flags for tests:
  - `--answer`
  - `--criterion-points correctness=3,clarity=1`
  - `--fatal-errors id1,id2`
  - `--confidence 4`
  - `--attempt-type independent_attempt`
  - `--hints-used 0`
  - `--json`

Files:

- `src/learnloop/cli.py`
- `src/learnloop/services/attempts.py`
- `tests/test_cli_attempt.py`

Acceptance:

- A headless command can initialize state, attempt an item, and update the due
  queue.

### 3.3 `learnloop review` and `learnloop why`

Expand scheduler CLI behavior.

Behavior:

- Call state sync first.
- Show due queue with one-line reasons.
- Support `--available-minutes`.
- Support `--energy`.
- Persist scheduler explanations.
- `why` prints the latest explanation if the item is no longer in the current
  queue.

Files:

- `src/learnloop/services/scheduler.py`
- `src/learnloop/cli.py`
- `tests/test_cli_review.py`

Acceptance:

- Review and why agree on component values.

### 3.4 `learnloop show`

Expand universal inspection.

Entities:

- Learning Object
- Practice Item
- concept
- concept edge
- note
- subject
- attempt
- grading evidence
- error event
- proposal batch
- proposal item
- change batch
- scheduler explanation

Files:

- `src/learnloop/services/inspector.py`
- `src/learnloop/cli.py`
- `tests/test_show.py`

Acceptance:

- `show` can inspect every ID created by deterministic flows.

## Slice 4: Scheduler Golden Tests

Goal: lock the deterministic scheduler before adding Textual and Codex.

### 4.1 Fixture Vaults

Create fixture vaults under `tests/fixtures/vaults`.

Fixtures:

- `basic`
  - one subject, one concept, one LO, one PI
- `scheduler_due_queue`
  - multiple items with due and not-due state
  - active goals
  - recent errors
  - lexicographic tiebreak case
- `scheduler_suppression`
  - inactive item
  - cold LO
  - short session suppressing Probe-EIG
- `doctor_invalid`
  - missing references and invalid taxonomy alignment

Files:

- `tests/fixtures/vaults/...`
- `tests/helpers.py`

Acceptance:

- Fixtures are small and human-readable.
- Tests copy fixtures into temp dirs before mutation.

### 4.2 Scheduler Component Tests

Cover:

- Forgetting risk is zero before due date.
- Forgetting risk uses FSRS retrievability after due date.
- Active goal follows `prerequisite` and `part_of` depth 1 only.
- Active goal does not follow `related` or `confusable_with`.
- Recent error decays by `exp(-days_since / 7)`.
- Inactive items are filtered.
- Cold LOs are filtered unless in probe.
- Ties sort by lowest Practice Item ID.

Files:

- `tests/test_scheduler_golden.py`

Acceptance:

- Scheduler tests are deterministic with frozen clocks.

## Slice 5: One-Day Textual Spike

Goal: validate Textual async/state assumptions using the same services as CLI.

### 5.1 TUI App Shell

Implement:

- App object with vault root injection.
- Startup state sync.
- Error screen for missing or invalid vault.
- Key bindings:
  - quit
  - refresh
  - open selected item
- Lightweight service container:
  - loaded vault
  - repository
  - current scheduler queue

Files:

- `src/learnloop/tui/app.py`
- `src/learnloop/tui/state.py`
- `tests/test_tui_app.py`

Acceptance:

- `learnloop today` launches without crashing in a valid vault.
- Textual pilot tests can mount the app.

### 5.2 Bare Today Loop Screen

Implement a minimal Today screen.

UI:

- Queue list.
- Selected item details:
  - prompt
  - LO title
  - scheduler priority components
- Refresh action.
- Begin practice action.

No grading UI yet.

Files:

- `src/learnloop/tui/screens/today.py`
- `src/learnloop/tui/widgets.py`

Acceptance:

- Screen reads scheduler output from service layer.
- No scheduling logic exists in the screen.

## Slice 6: Full Textual Today, Practice, and Feedback Flow

Goal: make Textual the daily workflow surface for the deterministic core.

### 6.1 Today Screen

Features:

- Due queue with stable ordering.
- Compact one-line why summaries.
- Item detail panel.
- Session inputs:
  - available minutes
  - energy
- Start practice.
- Show full why explanation.
- Empty state when no items are scheduled.
- Doctor warning indicator if vault has issues.

Files:

- `src/learnloop/tui/screens/today.py`
- `src/learnloop/tui/widgets.py`

Acceptance:

- Matches CLI `review` ordering for the same vault and session settings.

### 6.2 Practice Screen

Features:

- Prompt display.
- Answer editor.
- Hint reveal controls.
- Attempt type selector.
- Submit answer.
- `dont_know` action.
- Checkpoint answer while typing.

Files:

- `src/learnloop/tui/screens/practice.py`
- `src/learnloop/services/attempts.py`

Acceptance:

- A user can complete an answer and move into feedback/self-grade.
- Checkpoint restores unfinished answer after restart.

### 6.3 Self-Grade Feedback Screen

Features:

- Expected answer and rubric display.
- Per-criterion scoring controls.
- Fatal error selection.
- Error type selection with "other" text.
- Confidence selector.
- Submit grade.
- Show FSRS, mastery, and next due summary.
- Return to Today queue.

Files:

- `src/learnloop/tui/screens/feedback.py`
- `src/learnloop/services/grading.py`

Acceptance:

- TUI attempt result matches CLI attempt result for equivalent inputs.

### 6.4 TUI Tests

Use Textual pilot tests for:

- App launches.
- Today queue renders.
- Selecting an item opens practice.
- Submitting self-grade writes attempt and updates queue.

Files:

- `tests/test_tui_today.py`
- `tests/test_tui_practice.py`

Acceptance:

- Tests do not require a real terminal session.

## Slice 7: Codex Runtime Adapter and Proposal Persistence

Goal: connect LearnLoop to the local Codex checkout while keeping local vault
useful when Codex is unavailable.

### 7.1 Runtime Health Check

Implement Codex runtime status.

Checks:

- `checkout_path` exists.
- checkout revision matches configured `revision`.
- app-server startup command can be launched or is already running.
- healthcheck succeeds within timeout.
- auth failures are reported as `codex_auth_required`.

Statuses:

- `codex_missing`
- `codex_revision_mismatch`
- `codex_unavailable`
- `codex_auth_required`
- `ready`

Files:

- `src/learnloop/codex/runtime.py`
- `src/learnloop/codex/client.py`
- `tests/test_codex_runtime.py`

Acceptance:

- Runtime failures disable Codex-backed writes but do not break local review,
  attempt, or self-grade workflows.

### 7.2 Transport Contract

Before implementation, verify the local Codex app-server transport.

Default implementation plan unless the checkout proves otherwise:

- Use HTTP JSON over localhost.
- Add a health endpoint client.
- Add authoring proposal request/response client.
- Add grading proposal request/response client.
- Time out every call.
- Persist raw request context hash and schema name, not arbitrary raw prompts
  unless needed for debugging.

If the local app-server exposes an SDK instead:

- Wrap it behind the same `CodexClient` protocol.
- Keep the service-level contract unchanged.

Files:

- `src/learnloop/codex/client.py`
- `src/learnloop/codex/transport.py`
- `src/learnloop/codex/schemas.py`

Acceptance:

- Services depend only on `CodexClient`, not on HTTP or SDK details.

### 7.3 Agent Run Persistence

Implement lifecycle around every Codex call.

Behavior:

- Insert `agent_runs` before call.
- Stamp purpose, provider, model, prompt template/version, SDK version, Codex
  revision, input context hash, output schema, and start time.
- On success, complete the run.
- On failure, record status and error.
- Return failure to caller in a typed way.

Files:

- `src/learnloop/services/agent_runs.py`
- `src/learnloop/db/repositories.py`
- `tests/test_agent_runs.py`

Acceptance:

- Every Codex-backed proposal or grade has an `agent_run_id`.

### 7.4 Proposal Persistence

Persist authoring proposals without applying them.

Behavior:

- Validate `AuthoringProposal`.
- Validate source refs.
- Validate target rules.
- Validate item payload against current vault state.
- Insert `proposed_patches`.
- Insert one `proposed_patch_items` row per item.
- Store original payload JSON.
- Store validation status and errors.
- Derive batch status from item decisions.

Files:

- `src/learnloop/services/proposals.py`
- `src/learnloop/db/repositories.py`
- `tests/test_proposal_persistence.py`

Acceptance:

- `learnloop proposals` lists batches and item decisions.
- Invalid proposals are auditable and not applied.

## Slice 8: Codex Grading with Self-Grade Fallback

Goal: use Codex grading when available, with deterministic self-grade fallback.

### 8.1 Grading Context Builder

Build `GradingContext` from:

- Practice Item prompt.
- Expected answer.
- Resolved rubric.
- Learner answer.
- Attempt metadata.
- Relevant error taxonomy entries.
- Relevant LO and concept context.

Files:

- `src/learnloop/services/grading.py`
- `src/learnloop/codex/client.py`
- `tests/test_grading_context.py`

Acceptance:

- Context is deterministic and hashable.

### 8.2 Codex Grade Validation

Validate `GradingProposal`.

Checks:

- Attempt ID matches.
- Practice Item ID matches.
- Rubric score is `0..4`.
- Criterion IDs exist.
- Points do not exceed criterion max.
- Fatal errors exist in the resolved rubric.
- Fatal errors cap score.
- Grader confidence is in range.
- Unknown error types trigger taxonomy proposal flow.

Files:

- `src/learnloop/services/grading.py`
- `tests/test_codex_grading_validation.py`

Acceptance:

- Bad grading proposals are rejected or sent to manual review without corrupting
  derived state.

### 8.3 Codex Attempt Flow

Extend `AttemptService`:

- Try Codex grading when runtime is ready.
- Fall back to self-grade on missing, mismatch, unavailable, auth required,
  timeout, or validation failure.
- Write `grading_evidence` with `grader_tier = 3` for Codex.
- Use the same FSRS, mastery, surprise, and scheduler update path for Codex and
  self-grade.

Files:

- `src/learnloop/services/attempts.py`
- `src/learnloop/services/grading.py`
- `tests/test_codex_attempt_flow.py`

Acceptance:

- Attempt service has one post-grade update path.
- Codex failures are visible but do not block local learning.

### 8.4 Deferred Codex Regrade

Implement startup regrade flow.

Behavior:

- After Codex health passes, find most recent non-superseded tier-1 evidence.
- Call Codex grading.
- Insert tier-3 evidence rows.
- Supersede tier-1 rows.
- Delta-apply the new observation against current mastery.
- Write `regrade_disagreement` content event when score delta is at least 2.

Files:

- `src/learnloop/services/regrade.py`
- `src/learnloop/services/grading.py`
- `tests/test_deferred_regrade.py`

Acceptance:

- Regrade is idempotent.
- Regrade does not replay full history.

## Slice 9: Codex Authoring and Patch Application

Goal: propose, review, accept, reject, and apply Learning Object, Practice Item,
concept, concept-edge, rubric, and error-type patches.

### 9.1 Authoring Context Builder

Build context from selected sources.

Inputs:

- Notes by id or path.
- Existing concepts and relations.
- Existing LOs and PIs relevant to selected subjects.
- Goals when relevant.
- Optional manual instructions.

Behavior:

- Resolve `SourceRef` IDs.
- Include short source excerpts or line/heading locators.
- Avoid overloading Codex with the whole vault unless explicitly requested.

Files:

- `src/learnloop/services/proposals.py`
- `src/learnloop/codex/prompts.py`
- `tests/test_authoring_context.py`

Acceptance:

- Context builder is deterministic and testable without Codex.

### 9.2 `learnloop propose`

Implement CLI proposal generation.

Flags:

- `--subject`
- `--note`
- `--source`
- `--instructions`
- `--json`

Flow:

1. Load vault.
2. Check Codex runtime.
3. Build authoring context.
4. Create agent run.
5. Call Codex client.
6. Validate proposal.
7. Persist batch and items.
8. Print batch summary.

Files:

- `src/learnloop/cli.py`
- `src/learnloop/services/proposals.py`
- `tests/test_cli_propose.py`

Acceptance:

- A mocked Codex client can produce a persisted proposal batch.

### 9.3 Proposal Review Policy

Implement review routing.

Behavior:

- `review_route = reject` persists as rejected or invalid for audit.
- `review_route = review_required` persists pending.
- `review_route = auto_apply` is allowed only when:
  - schema validation passes
  - source refs resolve
  - no ID collisions
  - payload is direct source-grounded extraction
- In early MVP, default to review-required unless auto-apply is clearly safe.

Files:

- `src/learnloop/services/proposals.py`
- `tests/test_proposal_review_policy.py`

Acceptance:

- Auto-apply cannot mutate content unless every guard passes.

### 9.4 Patch Compiler

Compile accepted proposal items into internal patch operations.

Operations:

- `create_yaml_entity`
- `update_yaml_entity`
- `deactivate_entity`
- `upsert_concept_edge`
- `upsert_rubric`
- `record_grading_evidence`
- `record_error_event`

Rules:

- Use `edited_payload_json` when present.
- Validate all references before writing.
- Derive paths from entity type and IDs.
- One accepted proposal item creates one `change_batches` row.
- One accepted proposal item may create multiple `content_events`.

Files:

- `src/learnloop/services/proposals.py`
- `src/learnloop/services/patches.py`
- `src/learnloop/vault/writer.py`
- `tests/test_patch_compiler.py`

Acceptance:

- Patch compiler is pure enough to unit test before writes.

### 9.5 Patch Applier

Apply compiled operations.

Behavior:

- Validate current vault state before mutation.
- Write `change_batches` and `content_events`.
- Mutate YAML through vault writer only.
- Recompute content hashes.
- Run state sync for affected entities.
- Mark proposal item accepted with `applied_change_batch_id`.
- Reject or roll back cleanly if validation fails before file write.

Files:

- `src/learnloop/services/patches.py`
- `src/learnloop/services/proposals.py`
- `tests/test_patch_applier.py`

Acceptance:

- `learnloop accept` can create a new LO and PI from a proposal.
- `learnloop reject` never mutates content.

### 9.6 Proposal Review UI in CLI and TUI

CLI:

- `learnloop proposals`
- `learnloop show <proposal_id>`
- `learnloop show <proposal_item_id>`
- `learnloop accept <patch_id> --items ...`
- `learnloop reject <patch_id> --items ...`

Textual:

- Proposal list screen.
- Proposal item detail.
- Accept/reject action.
- Basic edited payload can be deferred unless needed for daily use.

Files:

- `src/learnloop/cli.py`
- `src/learnloop/tui/screens/proposals.py`

Acceptance:

- Proposal review is possible without opening YAML files manually.

## Slice 10: Probe-EIG

Goal: add probe-only expected information gain as the final scheduler component.

### 10.1 Probe State Entry

Implement entry into `lo_probe_state.status = "in_progress"`.

Rules:

- Pending active-goal LO enters probe when capacity opens.
- Use learner claims to skip or reduce target attempts.
- Build hypothesis set at entry.
- Lock hypothesis set during probe phase.

Files:

- `src/learnloop/services/probes.py`
- `src/learnloop/db/repositories.py`
- `tests/test_probe_entry.py`

Acceptance:

- Probe state creation is deterministic.

### 10.2 Hypothesis Set Builder

Build hypotheses:

- `mastered`
- `unfamiliar`
- active misconceptions on this LO
- neighbor misconceptions from `confusable_with` edges when neighbor mastery is
  high enough

Prior:

- `mastered` proportional to mastery mean.
- `unfamiliar` proportional to `1 - mastery_mean`.
- misconception proportional to severity times decay.
- cap at configured max size.

Files:

- `src/learnloop/services/probes.py`
- `tests/test_hypothesis_sets.py`

Acceptance:

- Tests cover cap behavior and renormalization.

### 10.3 EIG Scoring

Implement deterministic outcome model.

Outcome:

- score bucket: low, mid, high
- error type or null

Behavior:

- Compute `P(o | h, item)`.
- Compute mixture `P(o | item)`.
- Compute mutual information.
- Normalize by `log(|H|)`.

Files:

- `src/learnloop/services/probes.py`
- `tests/test_probe_eig.py`

Acceptance:

- Golden tests cover items that do and do not probe active misconceptions.

### 10.4 Scheduler Integration

Integrate `probe_eig`.

Rules:

- Only when `lo_probe_state.status = "in_progress"`.
- Set to `0` for short sessions.
- Include in scheduler explanations.
- Write `elicitation_events` when selecting probe items.

Files:

- `src/learnloop/services/scheduler.py`
- `src/learnloop/services/probes.py`
- `tests/test_scheduler_probe_eig.py`

Acceptance:

- Existing deterministic scheduler tests still pass.
- Probe-EIG changes rank only when allowed.

### 10.5 Probe Attempt Updates

After a probe attempt:

- Increment completed count.
- Update learner state beliefs if needed.
- Mark probe complete when target attempts reached or convergence threshold met.
- Keep hypothesis set locked until re-entry.

Files:

- `src/learnloop/services/probes.py`
- `src/learnloop/services/attempts.py`
- `tests/test_probe_attempt_updates.py`

Acceptance:

- Probe state progresses deterministically after attempts.

## Slice 11: Observation Templates and Negative-Surprise Follow-Up

Goal: add observation templates and automatic follow-up insertion after
surprising feedback.

### 11.1 Observation Template Loader

Implement template storage and validation.

Behavior:

- Load from `observation_templates` SQL.
- Validate template YAML.
- Support `emits_attempt`.
- Record `observation_events`.

Files:

- `src/learnloop/services/observations.py`
- `tests/test_observation_templates.py`

Acceptance:

- A template can emit a formal attempt when configured to do so.

### 11.2 Observation CLI and TUI Hooks

CLI:

- Observation-specific commands are deferred by spec, but `attempt` can use
  templates internally when needed.

TUI:

- Show template-driven forms only when a workflow requires them.
- Keep generic text workflows first.

Files:

- `src/learnloop/tui/screens/practice.py`
- `src/learnloop/services/observations.py`

Acceptance:

- Templates do not complicate the normal answer-grade loop.

### 11.3 Negative-Surprise Follow-Up Gate

Implement follow-up insertion after feedback.

Inputs:

- `attempt_surprise`
- `tau_followup_nats`
- `gamma_min`
- active errors
- existing local Practice Item pool

Behavior:

- Trigger follow-up when negative surprise exceeds threshold.
- Prefer existing Practice Items.
- Suppress if no suitable item exists and simulator generation is deferred.
- Record triggered and suppressed actions in `attempt_surprise`.
- Add follow-up item to the current session queue or next queue depending on
  UX policy.

Files:

- `src/learnloop/services/followups.py`
- `src/learnloop/services/attempts.py`
- `src/learnloop/services/scheduler.py`
- `tests/test_followups.py`

Acceptance:

- Negative surprise can insert a follow-up deterministically.
- Suppressed follow-ups are explainable.

## Slice 12: Final MVP Hardening

Goal: make the MVP usable and maintainable.

### 12.1 End-to-End Test Scenarios

Scenarios:

- Init vault.
- Add subject.
- Add note.
- Mock Codex proposal for LO and PI.
- Accept proposal.
- Review queue.
- Attempt item with self-grade.
- See updated FSRS and mastery.
- See item scheduled again.
- Trigger recent-error boost.
- Mock Codex grading.
- Deferred regrade supersedes self-grade.
- Probe-EIG changes queue for in-progress probe.
- Negative surprise inserts follow-up.

Files:

- `tests/test_e2e_local.py`
- `tests/test_e2e_codex_mock.py`

Acceptance:

- E2E tests pass without a real Codex server by using a fake client.

### 12.2 Migration Discipline

Add checks:

- No schema changes without a migration.
- Migrations are idempotent only through `schema_migrations`.
- New migrations have tests.

Files:

- `tests/test_migrations.py`

Acceptance:

- A fresh DB and an existing DB both migrate cleanly.

### 12.3 Documentation

Update:

- `README.md`
  - install
  - init
  - add subject
  - add note
  - propose
  - review
  - attempt
  - today
- `AGENTS.md` template for vault behavior.
- Example fixture vault docs.

Acceptance:

- A new user can run the deterministic workflow from README alone.

### 12.4 Manual QA Checklist

Run manually:

- `python -m pytest -q`
- `python -m compileall -q src tests`
- `learnloop --help`
- `learnloop init <tmp-vault>`
- `learnloop add-subject ...`
- `learnloop add-note ...`
- `learnloop doctor`
- `learnloop review`
- `learnloop attempt ...`
- `learnloop why ...`
- `learnloop today`

Codex QA when local checkout is available:

- bad checkout path reports `codex_missing`
- wrong revision reports `codex_revision_mismatch`
- auth failure reports `codex_auth_required`
- mocked or real authoring proposal persists
- accept writes YAML and content events
- grading proposal writes tier-3 evidence

Acceptance:

- MVP can be used locally without Codex.
- Codex-backed flows are optional and auditable.

## Open Decisions to Resolve Before Specific Slices

These are not blockers for deterministic work, but they should be pinned before
the related implementation slice starts.

1. Codex transport contract
   - Confirm whether the local app-server exposes HTTP JSON, an SDK, or another
     RPC mechanism.
   - Pin healthcheck endpoint and request/response shapes.

2. CLI JSON contracts
   - Finalize exact shapes for `review`, `why`, `show`, `proposals`, `doctor`,
     and `attempt`.

3. Doctor severity policy
   - Decide which issues are errors vs warnings.
   - Decide which safe fixes belong under `--fix-state`.

4. Content hash reset policy
   - Decide whether PI content hash changes reset FSRS state, mark it stale, or
     preserve state with a content event.

5. TUI proposal editing
   - Decide whether editing proposal payloads is required for MVP or whether
     accept/reject is sufficient for the first usable version.

## Suggested Immediate Next Work

The next implementation slice should be:

1. Add fixture vault directories under `tests/fixtures/vaults` and move the
   growing test setup helpers toward copied, human-readable fixtures.
2. Start the Textual today-loop spike once deterministic fixtures are stable.
3. Implement the HTTP/SDK Codex transport once the local app-server contract is
   pinned.

This keeps momentum on the spec build path and avoids starting Textual or Codex
before the deterministic storage and inspection contracts are solid.

## Final MVP Acceptance Contract

The MVP is complete when a fresh user can run one complete local learning loop
from an empty vault, with and without Codex, and every state transition is
inspectable through CLI, SQLite, YAML, and automated tests.

The acceptance contract is not a feature checklist. It is a set of verifiable
gates. The automated gates are the source of truth; the manual checks exist only
for behavior that depends on an actual local Codex checkout or a real terminal.

### Acceptance Gate 1: Clean Install

Automated test command:

```powershell
python -m pip install -e .[dev]
python -m pytest -q
learnloop --help
```

Required result:

- Install succeeds from a clean checkout.
- All tests pass.
- CLI entry point resolves and lists every MVP command.

Automated coverage:

- `tests/test_cli_entrypoint.py`
- `tests/test_migrations.py`

### Acceptance Gate 2: Fresh Vault

Automated scenario:

1. Create a temp directory.
2. Run `learnloop init <vault>`.
3. Run `learnloop doctor --vault <vault> --json`.
4. Inspect SQLite migration state.
5. Load the vault through `load_vault`.

Required result:

- `learnloop.toml` exists and validates.
- Required directories exist.
- Required YAML skeletons exist.
- SQLite exists.
- All migrations are recorded.
- Doctor reports no errors.
- Re-running init or state sync is idempotent.

Automated coverage:

- `tests/test_init.py`
- `tests/test_doctor.py`
- `tests/test_state_sync.py`

### Acceptance Gate 3: Deterministic Local Learning Loop

Automated scenario without Codex:

1. Create a fresh vault.
2. Add a subject.
3. Add or write a concept, Learning Object, and Practice Item.
4. Run state sync.
5. Run `learnloop review --json`.
6. Run `learnloop attempt <practice_item_id>` with non-interactive self-grade
   flags.
7. Run `learnloop show <attempt_id> --json`.
8. Run `learnloop why <practice_item_id> --json`.
9. Run `learnloop review --json` again.

Required result:

- Attempt row is written.
- Self-grade fallback writes `grading_evidence`.
- FSRS state is updated.
- LO mastery state is updated.
- Error events are written when the grade includes an error attribution.
- Surprise row is written.
- Scheduler explanation is written.
- Due queue changes deterministically.
- `show` can inspect every ID created by the flow.
- `why` explains the item with the same component values used for ranking.

Automated coverage:

- `tests/test_cli_attempt.py`
- `tests/test_attempts.py`
- `tests/test_self_grade.py`
- `tests/test_fsrs.py`
- `tests/test_mastery.py`
- `tests/test_surprise.py`
- `tests/test_scheduler_golden.py`
- `tests/test_show.py`

### Acceptance Gate 4: CLI MVP Command Reality

Every command in `spec_mvp.md` must be implemented:

```text
learnloop init
learnloop add-subject
learnloop add-note
learnloop propose
learnloop proposals
learnloop accept
learnloop reject
learnloop attempt
learnloop review
learnloop why
learnloop show
learnloop doctor
learnloop today
```

Required result:

- No MVP command exits with a placeholder or "not implemented" message.
- Commands return nonzero only for real validation, runtime, or user-input
  errors.
- Scriptable commands support stable `--json` output where specified.
- Human output remains concise and useful.

Automated coverage:

- `tests/test_cli_commands.py`
- `tests/test_cli_json.py`

### Acceptance Gate 5: Proposal Workflow

Automated scenario with a fake Codex client:

1. Create a vault with notes/source material.
2. Run proposal generation through the service layer using a fake
   `CodexClient`.
3. Persist an `AuthoringProposal`.
4. List proposals.
5. Show proposal and proposal item details.
6. Reject one item.
7. Accept one item that creates or updates YAML content.
8. Reload the vault.
9. Run doctor.

Required result:

- `agent_runs` row is written.
- `proposed_patches` row is written.
- One `proposed_patch_items` row is written per item.
- Invalid items are persisted but not applied.
- Rejected items do not mutate content.
- Accepted items create `change_batches` and `content_events`.
- Accepted items mutate YAML only through LearnLoop storage code.
- Codex output never chooses arbitrary file paths.
- Reloaded YAML validates.
- State sync updates affected derived state.

Automated coverage:

- `tests/test_agent_runs.py`
- `tests/test_authoring_context.py`
- `tests/test_proposal_persistence.py`
- `tests/test_proposal_review_policy.py`
- `tests/test_patch_compiler.py`
- `tests/test_patch_applier.py`
- `tests/test_cli_propose.py`

### Acceptance Gate 6: Codex Grading and Fallback

Automated scenarios with fake Codex clients:

- Codex ready and returns a valid grade.
- Codex missing.
- Codex revision mismatch.
- Codex unavailable.
- Codex auth required.
- Codex times out.
- Codex returns invalid grading payload.
- Deferred Codex regrade supersedes a prior self-grade.

Required result:

- Valid Codex grading writes tier-3 `grading_evidence`.
- Runtime failures fall back to self-grade and keep local learning usable.
- Invalid grading proposals do not corrupt attempt, FSRS, mastery, or surprise
  state.
- Deferred regrade supersedes tier-1 evidence rows.
- Regrade applies a delta observation against current mastery.
- Large score disagreement writes `regrade_disagreement`.

Automated coverage:

- `tests/test_codex_runtime.py`
- `tests/test_grading_context.py`
- `tests/test_codex_grading_validation.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_deferred_regrade.py`

Manual Codex smoke check:

- Configure a real local Codex checkout in `learnloop.toml`.
- Verify bad path reports `codex_missing`.
- Verify wrong revision reports `codex_revision_mismatch`.
- Verify auth failure reports `codex_auth_required`.
- Verify a real grading call writes tier-3 evidence.
- Verify a real authoring call persists proposal items before any content
  mutation.

### Acceptance Gate 7: Textual TUI Parity

Automated Textual pilot scenarios:

1. Launch `LearnLoopApp` against a fixture vault.
2. Today screen renders the same queue ordering as `learnloop review --json`.
3. Selecting an item opens Practice.
4. Submitting an answer opens Feedback.
5. Submitting self-grade writes the same state transitions as CLI attempt.
6. Returning to Today shows the updated queue.

Required result:

- TUI screens contain no scheduling, grading, mastery, proposal, or patch
  application logic.
- TUI and CLI share service-layer behavior.
- Textual tests run without a real terminal session.
- `learnloop today` launches in a valid vault.

Automated coverage:

- `tests/test_tui_app.py`
- `tests/test_tui_today.py`
- `tests/test_tui_practice.py`
- `tests/test_tui_feedback.py`

Manual TUI smoke check:

- Run `learnloop today --vault <fixture-or-manual-vault>`.
- Navigate queue.
- Complete one self-graded item.
- Confirm queue refreshes.

### Acceptance Gate 8: Probe-EIG

Automated scenarios:

- Active-goal LO enters probe state.
- Hypothesis set is built and locked.
- Prior distribution is normalized.
- EIG is computed for items that do and do not probe active misconceptions.
- Scheduler includes Probe-EIG only for in-progress probe state.
- Short sessions suppress Probe-EIG.
- Probe attempt updates progress and can complete the probe.

Required result:

- Probe-EIG is deterministic.
- Existing scheduler component tests still pass.
- Probe-EIG affects ranking only under the conditions in `spec_mvp.md`.
- `scheduler_explanations` include the Probe-EIG component.
- `elicitation_events` are written when probe policy selects an item.

Automated coverage:

- `tests/test_probe_entry.py`
- `tests/test_hypothesis_sets.py`
- `tests/test_probe_eig.py`
- `tests/test_scheduler_probe_eig.py`
- `tests/test_probe_attempt_updates.py`

### Acceptance Gate 9: Observation Templates and Surprise Follow-Ups

Automated scenarios:

- Valid observation template loads.
- Invalid template is rejected by doctor or validation.
- Template configured with `emits_attempt` creates an attempt through the same
  attempt service path.
- Negative surprise above threshold inserts a suitable follow-up when one
  exists.
- Negative surprise records a suppressed action when no suitable follow-up
  exists.

Required result:

- Observation events are recorded.
- Template-emitted attempts produce normal attempt, grading, FSRS, mastery, and
  scheduler side effects.
- Follow-up insertion is deterministic.
- `attempt_surprise.triggered_actions_json` and
  `attempt_surprise.suppressed_actions_json` are populated.

Automated coverage:

- `tests/test_observation_templates.py`
- `tests/test_followups.py`

### Acceptance Gate 10: End-to-End MVP

Automated end-to-end scenarios:

1. Local-only E2E:
   - init vault
   - add subject
   - add source content
   - create LO/PI via controlled writer or fake proposal
   - review
   - attempt with self-grade
   - inspect attempt, grading, FSRS, mastery, surprise, and scheduler why

2. Codex-mocked E2E:
   - init vault
   - add note
   - fake Codex authoring proposal
   - accept proposal
   - review generated PI
   - fake Codex grade
   - inspect grading, mastery, FSRS, surprise

3. TUI E2E:
   - mount app
   - complete one self-graded practice flow
   - verify persistent state

Required result:

- All state transitions are inspectable.
- All durable content mutations have `change_batches` and `content_events`.
- All generated or graded Codex artifacts have `agent_runs` lineage.
- Doctor passes after each complete scenario.

Automated coverage:

- `tests/test_e2e_local.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_e2e_tui.py`

### Final Done Criteria

The MVP is done only when:

- Every acceptance gate above passes.
- `python -m pytest -q` passes from a clean checkout.
- `python -m compileall -q src tests` passes.
- `learnloop doctor` passes on all valid fixture vaults.
- Every MVP command is implemented and covered.
- Local-only learning remains usable when Codex is unavailable.
- Codex-backed authoring and grading are auditable and never perform direct file
  writes.
- Textual and CLI produce equivalent state transitions for equivalent user
  actions.
