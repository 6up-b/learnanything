# Review fixes, September 23

On September 23, ten reviews covered branch `fix/review-recovery-and-telemetry` at `210621a`, compared against `origin/main` at `472128f`. Each area's fixes were made on its own branch from `210621a` and merged back. Three of those branches merged the PR head part-way through their work. This record lists what each review found, what the merged fixes changed, what was measured, and what is still open. The behaviour itself is documented in the architecture vault; the links go there.

## Commits

| Area | Merge commit | Fix commits (`merge^1..merge^2`) | Non-merge commits |
|---|---|---|---:|
| Desktop | `0aad175` | `210621a..29221dd` | 8 |
| Collection, dataset and CLI | `95689d7` | `0aad175..334f6cc` | 5 |
| Test infrastructure | `0410121` | `95689d7..54624c1` | 6 |
| AI provider layer and synthesis | `4fd2b2e` | `0410121..c838069` | 12 |
| Database, substrate and scheduling | `3c7439e` | `4fd2b2e..a31467d` | 9 |
| Attempts, sidecar recovery and TUI | `a75d8d5` | `3c7439e..4b93c66` | 10 |
| Ingestion pipeline | `ce60670` | `a75d8d5..1f8987c` | 17 |
| Sidecar loop pinning | none (on the branch) | `c1619d0` | 1 |
| Core performance and readability | `5856dd5` | `c1619d0..df70ec9` | 13 |
| PyYAML dependency | none (on the branch) | `0622ea1` | 1 |
| Documentation | on `fix/pr5-docs` | commits after `0622ea1` | — |

Migrations 159–163 are unchanged from `210621a`. Migration 164 is new, and the schema-head fixture is now `fixtures/migration_head_164`.

## Attempts, sidecar recovery and TUI

Reviews 01 and 10 found these problems:

- **Normalization before feedback metadata (P1).** Normalization ran before the feedback metadata was written, so on mvp-0.7/0.8 vaults every model-graded misconception got a second causal-hypothesis version with no run or model.
- **Recovered grades lost their source (P1).** The saved completion result held the result from before the grading source was attached, so recovery reported and replayed a model grade as a self-grade.
- **Learners stuck on a reopened item (P1).** Reopening an item from a refreshed Today queue sent a new scheduler candidate under an already-bound submission id, so every later save and submit of that item failed.
- **Completion rows never finished (P2).** Several doors (exam seeding, the simulators, rung variants, observations, recall calibration) left completion rows pending forever. Recovery normalized without the configured grading provider, and concurrent recoveries could normalize twice.
- **Lock errors were not retryable (P2).** `database is locked` reached the desktop as a non-retryable `internal` error.

Fixed:

- **Pipeline order.** Cold probes and feedback metadata are written first, then normalization, then follow-ups and the completion mark in one transaction. Every new grade writes its complete `attempt_feedback_metadata` row before materialization.
- **Grade provenance.** `apply_attempt` records the real grading source, run and fallback reason. A committed grade finishes its agent run `completed`, and a grading run that loses a submission race is closed as `failed`.
- **Routing by episode.** The completion row records the probe episode that was open at apply time, and a resumed completion routes and defers follow-ups by that episode. A pending row without the episode fails closed with `submission_committed`.
- **Completion lock.** An advisory lock, `attempt-completion.lock` next to the database, serializes the pipeline for an attempt. Its key is the resolved path; it waits up to 120 s and then raises the retryable `completion_busy`.
- **First offer wins.** `bind_submission_offer` keeps the first offer bound to a submission id. A refreshed candidate for the same item and session is accepted and mapped to the original. Existing intents are read without taking the write lock.
- **Commit races.** A submission that loses a commit race answers with the winner's attempt.
- **Doors without a pipeline.** Doors with no post-attempt pipeline set `awaits_completion=False` and complete at apply. Every door that records attempts sets `entry_surface` and `evidence_origin`.
- **Recovery provider.** Recovery normalizes with the configured grading provider.
- **Retryable lock errors.** `database is locked` and `database is busy` map to the retryable `database_busy`.
- **TUI retries.** The TUI keeps one submission id per practice screen and resumes a committed grade instead of recording a second attempt.
- **Pinned connections.** `get_today_queue`, `feedback_bundle`, `practice_item_detail`, the knowledge-map loop and the facet-mastery loop each reuse one connection.

See [Continue a Learning Cycle](../learnloop-architecture-vault/Workflows/Continue%20a%20Learning%20Cycle.md), [Process Model Output](../learnloop-architecture-vault/Workflows/Process%20Model%20Output.md) and [Attempt Processing](../learnloop-architecture-vault/Concepts/Attempt%20Processing.md) in the architecture vault.

## Ingestion pipeline

Review 02 found these problems:

- **Goal creation crashed (P1).** Exam-prep goal creation called `vault_mutation_lock` without a purpose and crashed after applying the map. The fix is in the AI branch.
- **A live job could be failed (P1).** One transient database error killed the heartbeat thread, and in-process recovery then failed the live owner's job.
- **v2-lite dropped fetch metadata (P2).** A v2-lite ingest skipped the fetch on its first attempt, which lost YouTube caption timestamps, arXiv locators, authors and license.
- **Ctrl-C deadlock (P2).** Ctrl-C during parallel inventory deadlocked executor shutdown.
- **Unfenced writes (P2).** Source-note and goal-linkage writes were not fenced.
- **Lock contention failed lease work (P2).** Vault-lock contention made lease recovery fail instead of wait.

Fixed:

- **Heartbeat.** It retries after 1 s on errors and stops only when ownership is lost.
- **Live-attempt registry.** A process-wide registry keeps lease expiry from failing an attempt whose handler is still running in the process.
- **v2-lite resume.** It resumes from retained bytes only on a retry (attempt count above 1).
- **Runner mailbox.** The inventory runner uses a mailbox that closes and releases every waiting worker on interrupt. The runner is woken by completions rather than polling every 50 ms, and it checks cancellation at most every 0.25 s.
- **Late checkpoints.** A late model checkpoint is saved like a late receipt. A cached window or pass that no longer validates is discarded and remade, at the legacy-window, inventory-window and synthesis-pass sites.
- **Job-path window keys.** Ingest-job inventory windows are keyed with the warm client's settings, the same as direct inventory runs.
- **Lock contention.** Startup recovery, claims and `resume_batch` defer on vault-lock contention. Drain-tick expiry waits at most 0.5 s.
- **Startup-only sweep.** The abandoned synthesis-run sweep runs only at startup.
- **Transport interrupts.** Interrupts are keyed by job and attempt, so a replaced attempt interrupts only its own transport.
- **Originals.** Each original is written to a unique temporary file, fsynced, then renamed.
- **Locked writes.** Source registration and goal linkage run under `vault_mutation_lock`.
- **CTE writes.** `WITH … INSERT/UPDATE/DELETE` is classified as a write, and CTE reads are not.
- **Store API.**
  - `JobOwner(worker_id, attempt_count)` is passed through the ownership checks.
  - `finish_ingest_job` is split into `finish_owned_ingest_job`, `expire_ingest_lease` and `transition_unleased_ingest_job`.
  - `allow_late_model_observation` is renamed `allow_late_model_records`.

See [Import Canonical Sources](../learnloop-architecture-vault/Workflows/Import%20Canonical%20Sources.md) and [Content Pipeline](../learnloop-architecture-vault/Architecture/Content%20Pipeline.md).

## AI provider layer and synthesis

Review 03 found these problems:

- **Goal-lock crash (P1).** The same goal-lock crash as in the ingestion review.
- **Receipts discarded paid responses (P2).** A failed receipt-finish write discarded a paid response, and ownership and cancellation signals were re-wrapped as `CodexUnavailable`.
- **Weak retry policy (P2).** With `max_retries=0` the adapter retried only 429/5xx on fixed delays, with no `Retry-After` handling and no overall deadline.
- **Non-ASCII output overcharged (P2).** Non-ASCII output was charged by its JSON escapes.
- **Over-budget passes not checkpointed (P2).** A paid pass that went over budget was not checkpointed.
- **Incomplete checkpoint keys (P2).** Checkpoint keys omitted endpoint and reasoning settings.
- **Budget preflight (P2, plausible).** The complete-request budget preflight could reject single-shard syntheses.

Fixed:

- **Goal lock.** Goal creation passes `purpose="study_map_goal"`. Apply-and-create-goal is one helper.
- **Receipt finish.** The finish write is best-effort: it logs and leaves the receipt `started`. The start write stays fail-closed. Adapter request failures are classified inside the receipt, and observer exceptions propagate unchanged.
- **Retry policy.**
  - Connection errors, timeouts and HTTP 408/409/429/5xx are retried, at most 3 attempts.
  - `retry-after-ms` and `Retry-After` are honoured, up to 60 s.
  - The jittered backoff ceiling is 1 s, then 2 s (capped at 8 s).
  - One deadline covers the whole loop.
- **Token charging.** Output tokens are charged on `ensure_ascii=False` text.
- **Checkpoints before budget checks.** Inventory windows and synthesis passes are checkpointed before the budget check.
- **Checkpoint keys.** They include `ai.execution.model_settings` (provider, model, endpoint, reasoning effort, thinking, response format) and the rendered prompt.
- **Explicit metering.** Receipt metering has its own functions (`receipt_fields_from_chat_response`, `receipt_fields_from_codex_turn`). Budget snapshots use `UsageMeter` and `_SynthesisBudget`.
- **Provider-resolution tests.** The provider-resolution matrix tests again cover codex-only, named-profile, openrouter, fallback and manual.

**Budget ceiling (F5), confirmed and not changed.** With the default budgets (40k shard input, 48k total ceiling), a near-full single shard fails the complete-request preflight once the registry holds about 230 ids. The fixed overhead is about 6,126 tokens and each id adds about 9.8. Packing shards to leave room for the overhead made the total larger (51,952 tokens with 0 ids). The refusal now states the estimate and the ceiling. Changing the default budgets is an owner decision.

See [AI Architecture](../learnloop-architecture-vault/Architecture/AI%20Architecture.md).

## Database, substrate and scheduling

Review 04 found these problems:

- **Decision features grew without bound (P1).** Immutable `decision_features` rows held a full item dump plus facet states, about 475 KB per queue refresh on a 99-item vault, and can never be pruned.
- **Adjudication foreign key broke replays (P2).** The adjudication foreign key aborted goal-series and scoreboard replays. This is also collection finding B1.
- **Nested transactions could commit late (P2).** `atomic()` nested in `pinned()` could raise at COMMIT and still commit later through the pin.
- **Degenerate propensity report (P2).** The propensity report called composed-offer data degenerate instead of unavailable.
- **Recalibration replay could lose its lease (P2).** Content recalibration replay could lose its ingest lease halfway through.
- **Reader blackout undocumented.** The atomic live rebuild blocks readers under DELETE journaling, and this was not documented.

Fixed:

- **Compact selection features.** Selection features use `selection_features_v1`: the ability vector, the demand vector, and a `content_hash` reference to the scored item.
- **Item snapshots.** Migration 164 adds `practice_item_snapshots`, one immutable row per scored item revision.
- **Adjudication table without foreign key.** Migration 164 rebuilds `false_remediation_adjudications` without its foreign key. The store checks that the attempt exists.
- **Transaction scopes.** `atomic()` and `pinned()` roll back on failure. A failed rollback keeps the original error, attaches a note, and invalidates the pinned connection so nothing is published.
- **Propensity readiness.** `learnloop eval` counts `unavailable_composed_offer` candidates separately and reports readiness `UNAVAILABLE` when no chosen candidate recorded a propensity.
- **Atomic recalibration replay.** `record_content_recalibration` replays inside `repository.atomic()`.

**Measured.** Over 5 persisted builds on a copy of `fixtures/linear_algebra` (99 items, 41 candidates):

- DB growth fell from 4.64 MB to 2.79 MB, about 100 KB per build over main instead of about 475 KB.
- Snapshots add a one-time 151,159 bytes of item JSON (41 rows) on the first build.
- Live-rebuild reader blackout was 0.40, 0.16 and 0.14 s over three runs.

See [Collection and Dataset Contract](../learnloop-architecture-vault/Concepts/Collection%20and%20Dataset%20Contract.md), [Rebuild Ownership](../learnloop-architecture-vault/Reference/Database/Rebuild%20Ownership.md) and [ADR-014 SQLite stays in DELETE journal mode](../learnloop-architecture-vault/Decisions/ADR-014%20SQLite%20stays%20in%20DELETE%20journal%20mode.md).

## Collection, dataset and CLI

Review 05 found these problems:

- **Adjudication foreign key (B1, P1).** The adjudication foreign key broke scratch replays.
- **Split grouping on a format label (B2, P1).** Splits grouped on the shared `surface_family` format label. On the fixture copy that left 2 groups, 63 of 70 attempts quarantined and no train, validation or test rows.
- **Non-atomic manifest (B3, P2).** The export manifest was not written atomically or durably.
- **Non-human rows quarantined human families (B5, P2).** Non-human attempts set cutoffs and quarantined human families.
- **Unchecked evidence and unlocked opener (B6–B9, P2).** Adjudication evidence was not type-checked, the adjudication CLI bypassed the vault lock, and data CLI errors printed tracebacks.
- **Collection version literals.** Writers stamped the collection version from literals.

Fixed:

- **Split families.** Families join through item, learning object, contract blueprint, evidence-fingerprint source family and shared stimulus, and cited source spans. `surface_family` never joins them.
- **Split eligibility.** Only human attempts with content provenance set cutoffs and occupy buckets. The export field is `content_provenance`.
- **Split policy.** The learning object stratifies the default split and does not group it. `dataset-export --split-policy` chooses between `temporal` (default) and `content`, and the manifest records `split_policy`, `split_parameters` and the claim each policy supports. `temporal` splits each learning object's own history 70/15/15 by time and labels a held-out attempt less than `--embargo` (a duration, default `7d`) after that learning object's last training attempt `quarantined_embargo`; it supports forecasting a known learner on practised content, and items sharing a stimulus or blueprint can cross its cutoffs. `content` is the family policy above, for generalization to unseen content. The export's data-quality report names the policy next to its split counts. `dataset_version` is 2, and a manifest without `split_policy` used the content policy. Temporal cutoffs use integer percentiles and read offsetless timestamps as UTC, and an embargo too large to represent exits 1 with a message.
- **Atomic export.** Artifacts are hashed while written and fsynced, and the manifest is published by atomic rename. A failed export removes its directory.
- **Evidence references.** They resolve through the table's single-column primary key, so `submission_intents` and `scheduler_offer_receipts` can be cited.
- **CLI.** `adjudicate-remediation` opens the vault through the locked opener. Bad input exits 1 with a one-line message.
- **Collection version.** Slates, attempts and offer receipts use `COLLECTION_VERSION`.
- **Cold-receipt status.** A receipt with no recorded outcome falls back to its qualification.
- **SQLite benchmark.** It keeps a connection attached so the WAL checkpoint is real, and it records the busy timeout.

**Measured on a copy of `fixtures/linear_algebra`**, with all 70 attempts forced to human origin:

| | Groups | Train | Quarantined | No provenance |
|---|---:|---:|---:|---:|
| Before | 2 | 0 | 63 | 7 |
| After | 6 | 23 | 47 | 0 |

Those are `content` counts. On the same copy, `temporal` gives 45 train, 10 validation and 15 test with `--embargo 0`, and 45 train, 1 validation, 3 test and 21 embargoed with `--embargo 1d`. The fixture spans 5.6 days, so the default `7d` embargo quarantines all 25 held-out rows.

The SQLite benchmark was re-run on 2026-09-23 on btrfs:

| Mode | Elapsed | Writer p95 | Reader busy failures |
|---|---:|---:|---|
| DELETE | 7.94 s | 39.28 ms | 2 (each a 5 s stall) |
| WAL | 1.96 s | 10.01 ms | 0; 599 of 599 frames checkpointed |

Production stays in DELETE mode; ADR-014 records why and what must be checked before switching. See [Collection and Dataset Contract](../learnloop-architecture-vault/Concepts/Collection%20and%20Dataset%20Contract.md).

## Desktop

Review 06 found these problems:

- **Stuck reopened item (R1, P1).** Reopening a started item from a rebuilt queue sent a new candidate for a bound retry key, and every save and submit then failed.
- **Invalid grading override (R4, P1).** An invalid grading override replayed on reconnect made every command fail.
- **Frozen Practice screen (R2, P2).** A failed vault switch could leave the Practice screen on "Loading…".
- **Close during flush (R5, P3).** Double-clicking close destroyed the window during a draft flush.
- **Commands for the old vault (R7, P2, plausible).** A command queued before a vault switch could run against the new vault.

Fixed:

- **Offer on serve.** `schedulerCandidateForServe` sends no candidate for a resumed, bound submission.
- **Override refusal.** A refused override on reconnect clears it and returns one retryable `grading_provider_reset` error.
- **Resume after a failed switch.** A frozen recovery reloads on resume.
- **Close flush.** `useCloseWithFlush` prevents every close while a flush is pending.
- **Vault changes.** Commands issued before a vault switch fail with `vault_changed`.
- **Shell reset.** All shell resets run before `loadVault()`.
- **Error boundary.** `ScreenErrorBoundary` wraps the lazy screens.
- **Media ranges.** `llmedia` serves at most 4 MiB per range response.
- **.gitignore.** It ignores a `node_modules` symlink.

**Main JS bundle.** Measured main JS chunk sizes:

| Build | Main JS | gzip |
|---|---:|---:|
| Base `472128f` | 2,150.96 kB | 630.24 kB |
| `210621a` | 1,251.12 kB | 370.82 kB |
| Head of this record | 1,252.29 kB | 371.26 kB |

The frontend has 6 vitest files with 22 tests.

See [Desktop Architecture](../learnloop-architecture-vault/Architecture/Desktop%20Architecture.md).

## Test infrastructure

Review 07 found these problems:

- **Durability lane missed shared fixtures (T1, P2).** The `durability` mark and `--durable-sqlite` did not reach module- or session-scoped fixtures.
- **Order-dependent test (T2, P2).** `common_repair_cover.matrix` order was nondeterministic, which masked a flaky assertion.
- **Allowlist too broad (T3, P2).** The SQL-owner allowlist admitted read-only modules.
- **Unused marker.** The `fresh_vault` marker was declared but unused.

Fixed:

- **SQLite mode per test.** The mode is set in runtest hooks, so it applies to fixtures of every scope.
- **Monotonic ULIDs.** `new_ulid()` is monotonic within a process.
- **SQL-owner allowlist.** Read-only modules are removed from it, with a reverse guard test.
- **Markers.** `--strict-markers` is on and `fresh_vault` is deleted.
- **Template equivalence.** A test checks that the per-session vault template equals a fresh build.
- **AST cache rename.** `tests/source_inventory.py` is now `tests/ast_cache.py`.

At the head of this record: 445 `test_*.py` files, 5,827 collected tests, and import contracts 6 kept, 0 broken.

## Core performance and readability

Review 09 found these problems:

- **Completion rows (P2).** The same pending-completion problem as review 01; it is fixed in the attempts branch.
- **Slow YAML reads.** Read-only YAML loads used the ruamel round-trip loader.
- **Unneeded vault loads.** Seven `vault/writer` functions parsed the whole vault.
- **Repeated parsing in doctor.** The doctor parsed files more than once.
- **Unpinned read models.** Learner read models opened 50–350 connections per request.
- **Uncalled functions.** 13 functions have no caller.

Fixed:

- **Fast YAML reads.** `read_yaml_data` and `read_markdown_frontmatter_data` read with libyaml under ruamel's YAML 1.2 resolver and fall back to the round-trip loader for forms that need it. `load_vault` and `load_practice_item_file` take `read_yaml_file=`.
- **Writer paths.** The seven writer functions build `VaultPaths` directly.
- **Doctor parse cache.** A per-run cache feeds doctor's checks and `load_vault`.
- **Pinned read models.** Six learner read models are pinned, and `predicted_correctness` shares one facet-state reader.
- **Depth envelopes.** A new `curriculum/depth_envelopes` module holds the shared envelope-edge and depth-policy helpers.
- **Long functions split.** `build_learner_review_feed`, `_entailment_conversions`, `build_guide_plan` and `run_doctor` are split into named steps with byte-identical output.
- **PyYAML.** `PyYAML` is a declared dependency.

**Measured** on a scratch copy of the linear-algebra vault, base `210621a` against the fix branch:

| Path | Before | After |
|---|---:|---:|
| `load_vault` | 729 ms | 65 ms |
| `run_doctor` | 2,508 ms | 455 ms |
| `upsert`/`delete_concept_edge`, per call | 772 ms | 49 ms |
| `capability_grid`, all 21 learning objects | 210 ms | 53 ms |
| `build_learner_review_feed` | 104 ms | 9 ms |

**Uncalled functions.** The 13 uncalled functions are removable: `resume_arc`, `record_depth_transition_committed`, `attach_family`, `detach_family`, `load_commitment`, `append_template_version`, `next_feasible_action`, `discover_exemplar_candidates`, `retry_outbox`, `fitted_fsrs_provenance`, `concept_hash`, `concept_edge_hash` and `rubric_hash`. They have no caller in `src/`, `tests/`, `scripts/` or the desktop app. The module reference leaves them out (`UNCALLED_DEFINITIONS` in `_scripts/module_generate.py`), so nothing in the repository refers to them.

## Sidecar timings

Measured on fresh copies of `fixtures/linear_algebra`, with identical serialized results before and after. The first three rows (attempts branch) are medians of 5 with a frozen clock; the last two are from commit `c1619d0`.

| Sidecar call | Before | After |
|---|---:|---:|
| `get_today_queue` | 191.6 ms, 86 connections | 38.6 ms, 7 connections |
| `get_practice_item` | 26.2 ms, 12 connections | 5.8 ms, 1 connection |
| `get_feedback` | 70.5 ms, 36 connections | 10.5 ms, 4 connections |
| knowledge map | 1,171 ms | 521 ms |
| facet mastery | 211 ms | 17 ms |

## Documentation

Review 08 found these problems:

- **No hand-written docs for the new behaviour (P2).** The new durable model existed only in the PR report.
- **Wrong propensity claims (P2).** Two concept notes claimed that persisted propensities support policy evaluation.
- **Understated export (P2).** The export was described as "selected" records.
- **Wrong bundle baseline (P2).** The bundle baseline was wrong.
- **Generated references.** They had a hard-coded config leaf count and had lost the `ingest.*` descriptions. The desktop validator crashed on `.test.tsx` files, and 9 new modules had no reference notes.
- **Stale guidance.** CLAUDE.md and README counts and commands were stale, and the September 6 reviews used absolute `/home/...` links.

Fixed on `fix/pr5-docs`:

- **CLAUDE.md and README.** Updated for the suite, markers, template and vitest. README links point at `docs/specs/` and the vault.
- **Database and configuration reference.** Regenerated at schema head 164, with generator-owned descriptions for four `ingest.*` leaves and a computed leaf count. The validator checks the prose counts.
- **Module and desktop reference.** Regenerated; there are 469 module notes. Vitest files are listed as tests.
- **New notes.** The Collection and Dataset Contract concept note and ADR-014.
- **Updated pages.** Pages for recovery, model output, import, desktop, rebuild, privacy, AI and scheduling, plus stale counts.
- **Implementation notes.** `2026-09-07-implementation.md` is corrected against the code and a re-run SQLite benchmark.
- **Links.** The September 6 reviews use repository-relative links.

All four vault validators pass at the head of the documentation branch.

## Still open

**Attempts and sidecar**

- Teach-back attempts are not linked to a scheduler slate; the teach-back RPC carries no candidate.
- `finish_teach_back` applies AI-graded transcripts with the default `grading_source="self"`.
- The TUI installs no model-call observer.
- On non-POSIX hosts the completion lock gives no cross-process exclusion.

**Ingestion**

- A v2-lite retry lacks fetch-only metadata (captions, labels, authors, license).
- `add_subject` writes the subjects file without the vault lock.
- A claim lost to lock contention counts as an idle tick, and after 3 idle ticks the drain thread exits.
- After bind no drain runs, so an expired lease from an earlier process stays `running` until a drain starts (D-5).

**AI**

- The manifest hash and completed agent-run reuse identify the provider by name and model only.
- OpenAI leaf receipts all use purpose `chat_request` (F8).
- An over-ceiling evidence expansion fails the whole synthesis (F9).
- Graph-structuring output is not added to `output_tokens_charged`.
- `prompt_safe` set ordering (R6) and a shared `USAGE_COUNTER_FIELDS` constant (R7).
- The default synthesis budgets need an owner decision (see F5 above).
- `_normalize` is not split.

**Database and scheduling**

- The ability vector is repeated on every candidate of a learning object in a slate (about 865 B each).
- `record_scheduler_slate` re-reads its candidates.
- `goals/exam_seeding.py` calls `rebuild_derived_state` outside a transaction.
- DELETE journaling blocks readers during a live rebuild, and reads fail once the blackout passes 5 s (ADR-014).

**Collection**

- `doctor --data-quality` ignores `--fix-state` and `--ai` (A6).
- `submission_intents.scheduler_candidate_id` has no partial unique index (A3).
- Adjudication evidence need not relate to the adjudicated attempt (A4).
- `B.total_burden_seconds` is always null.

**Desktop**

- A Practice screen that mounts during a vault-switch freeze is not in the owners snapshot (R3, partial).
- `observedRequests` is not seeded from `refresh`.
- After `grading_provider_reset`, Settings can show the old provider until health refreshes.

**Tests**

- ULIDs are monotonic only within one process.
- `tests/ast_cache.py` keeps every parsed AST for the session.
- Tests import private helpers across modules; a shared `tests/ingest_helpers.py` is proposed.

**Core**

- The 13 uncalled functions listed above can be deleted.
- `_check_instrument_contracts` and the other long functions from review 09 are not split.
- History-narrating comments remain in `learner/mastery.py`, `ops/settings_store.py`, `params/sensitivity_certificates.py`, `reader/reader_progression.py`, `curriculum/commitments.py`, `learner/familiarity.py` and `scheduling/scheduler.py`.

**Documentation and tooling**

- `tests/conftest.py` still says tmpfs and a 10-minute suite.
- The migration-head fixture path is hard-coded in 5 places.
- No queue benchmark script is committed, and `artifacts/queue-connections.json` names a `migration_head_162` fixture that never existed in a commit.
