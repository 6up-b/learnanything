# Slice 1 M2: Codex review fixes

Branch `slice-1/m2`, worktree `learnanything-slice1-m2`. Review job
`codex-agent/jobs/20261012-055004-tZldBp`, against the stage as gated at
`5aed28d7`. Each finding was reproduced first with a test that fails on the
unfixed source (checked by stashing the fix and rerunning), then fixed, one
commit per finding. F5 and F7 share a commit because they share the drain
and admission code. Tests use fakes only; the live smoke test below made
real calls on a fixtures-local backup copy.

## Review

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | "Unverified" criteria can still write negative evidence | fixed | `a86119f7` | `tests/test_grading_support.py`: `test_an_unverified_criterion_writes_no_negative_evidence_even_without_an_attribution` (live grade and blind regrade, through the projection), `test_an_unverified_multi_target_criterion_opens_no_unresolved_cause_factor` |
| F2 | High | Split vaults still execute grading turns with access to learner history | fixed | `0f1b28d6` | `tests/test_diagnosis_pipeline.py`: `test_a_joint_attempt_regraded_in_a_split_vault_is_graded_blind_and_isolated`, `test_a_self_graded_fallback_is_regraded_blind_and_queues_its_diagnosis`, `test_non_practice_graders_use_the_blind_contract_in_an_isolated_turn`, `test_only_the_joint_doors_call_the_joint_grading_operation` |
| F3 | High | Background diagnosis can overwrite newer canonical evidence | fixed | `c3040bfb` | `tests/test_post_attempt_worker.py`: `test_a_submission_committed_while_the_worker_projects_is_never_overwritten` (durability lane: WAL, the worker paused after its snapshot while a submission commits) |
| F4 | High | Regrades publish evidence before their matching blind record | fixed | `9671ce01` | `tests/test_diagnosis_pipeline.py`: `test_a_crash_between_regrade_publication_steps_publishes_nothing` (5 cases, one per step), `test_regrade_replay_never_reads_the_superseded_diagnosis` |
| F5 | Medium | Live diagnosis spend controls undercount retries and omit dry-run admission | fixed | `b03b18aa` | `tests/test_diagnosis_pipeline.py`: `test_failed_calls_count_toward_the_daily_cap_at_admission`, `test_live_diagnosis_is_admitted_through_the_shared_spend_framework`; `tests/test_diagnosis_reports.py`: `test_cli_drain_and_retry_plan_and_estimate_before_spending` |
| F6 | Medium | Requeueing an older attempt permits concurrent diagnosis leases | fixed | `56054049` | `tests/test_post_attempt_worker.py`: `test_an_older_job_queued_during_a_live_lease_is_never_leased_concurrently` |
| F7 | Medium | SIGINT and SIGTERM do not stop queue draining | fixed | `b03b18aa` | `tests/test_diagnosis_reports.py`: `test_ctrl_c_stops_the_drain_before_the_next_paid_job` (a real SIGINT mid-call), `test_a_cancelled_job_is_released_unspent` |
| F8 | Medium | S1.4a registry embeddings never reach diagnosis context | fixed | `149fb5da` | `tests/test_diagnosis_embeddings.py`: `test_the_registry_shortlist_reaches_the_diagnosis_context_as_of_the_attempt`, `test_the_diagnoser_may_match_a_shortlisted_belief_from_outside_the_neighborhood` |
| F9 | Medium | The advertised diagnosis accessor returns superseded explanations | fixed | `af853d47` | `tests/test_diagnosis_pipeline.py`: `test_the_accessor_and_the_overlays_agree_on_the_diagnosis_in_force` (stale grade and failed successor) |
| F10 | Medium | E7 reports a conditional timeout rate as the serving lag rate | fixed | `77991b93` | `tests/test_diagnosis_async_router.py`: `test_the_lag_rate_is_over_every_serve_that_followed_a_diagnosed_answer`; `test_a_pick_served_while_the_diagnosis_is_pending_is_receipted` and its two neighbours rewritten to serve-time receipts |

No finding was rejected.

### What changed, by finding

- **F1 (PF-c gate).**
  - **Persisted per criterion.** `ApplyAttemptInput.unverified_criterion_ids` carries the gate's list. Each unverified criterion's `grading_evidence` row is stamped `{"targets": [], "negative_evidence_blocked": "valid_alternative_unverified"}`, whether or not any attribution names it. A blind regrade stamps its new evidence rows the same way and takes the same manual-review reason.
  - **Enforced in the projection.** The projection reads that block reason (`UNVERIFIED_CRITERION_BLOCK`) as neither negative mass nor an observed unresolved failure. A multi-target criterion therefore opens no unresolved-cause factor.
  - **Existing vaults are unaffected.** Only rows written by the gate carry the reason, so they project exactly as before. Replay reuses the stored rows.
- **F2 (isolation).** Every new grading execution in a split vault is learner-blind and runs as an isolated turn.
  - **Practice-attempt regrades.** These go through the practice door's blind contract (PF-c included), also for an attempt first graded jointly or self-graded after a timeout. Its first blind record queues its diagnosis in the publication transaction. From then on, replay reads the attempt as blind from the ledger.
  - **Non-practice graders.** Teach-back, exams (sidecar and CLI), the probe audit and the taxonomy regrade use `request_vault_grading_proposal`. That is the blind mvp-2.0 contract in an isolated turn, with no causal fields and no repair suggestions. Teach-back regrades use it too, and teach-back still gets no blind record and no diagnosis.
  - **Joint vaults and the kill switch.** These keep the joint prompt exactly. An attempt already graded blind keeps its mode, as before.
  - **Guard test.** A test pins the only remaining callers of the joint operation: the joint practice path and M1's scratch-copy baseline.
- **F3.** `apply_diagnosis` runs the projection inside `Repository.atomic()` (`BEGIN IMMEDIATE`). Snapshot, compute and replace now hold the write lock, so they serialize with the attempt transactions that publish their own projections. On the 72-attempt linear-algebra copy the locked projection takes 0.06-0.09 s.
- **F4.** After the model returns, `regrade_attempt` publishes in one transaction:
  - the grading revision, the attempt grade and the content events;
  - the blind record, which queues the re-diagnosis inside the same store call;
  - the LO replay, the error-type proposals and the regrade's exercised facets and clarification.

  The blind record goes in before replay, so replay never sees the superseded diagnosis in force. A failed publication marks the agent run `failed`.
- **F5 (spend).**
  - **Daily cap.** `diagnosis.max_calls_per_day` now counts admitted logical calls: `agent_runs` rows with purpose `diagnosis`, written before the request. A call that fails and backs off counts. A run refused or cancelled before anything was sent is `cancelled` and does not count.
  - **Live admission.** Every live diagnosis request goes through `ReviewSpend` over the shared `SpendBudget`, which also writes the model-call receipts. Subscription routes (Codex) count one logical call, have no physical-request, token or dollar bound, and record cost as `estimated_only`. Metered routes admit every physical request against per-job caps (`LIVE_DIAGNOSIS_CAPS`), and an unknown price fails closed. That is a `budget` skip, never the grade.
  - **Commands.** `diagnose drain` and `diagnose retry` gain `--dry-run`, plus `--max-calls`, `--max-retries`, `--max-tokens`, `--max-cost-usd` and `--price-per-million`.
    - The dry run follows the queue exactly: one lease at a time, attempt order, backoff and the daily cap.
    - It estimates each call from its offline-assembled prompt plus the route's output limit, checks the caps, and writes nothing.
    - A run over its caps is refused before any call. A retry is admitted before anything is requeued.
    - When a command's caps run out mid-drain, the job is released unspent, not skipped.
- **F6.** The diagnose claim returns nothing while any diagnose job holds an unexpired lease, whatever its queue position.
- **F7.** `drain`, `process_next_job` and the diagnosis admission take a `cancelled` callable, and the CLI passes its SIGINT/SIGTERM event. The drain stops before the next job. A job claimed when cancellation is seen is released with its attempt refunded. The sidecar worker passes its shutdown event.
- **F8 (registry shortlist).** With `embedding.enabled`, every history mode ranks every registry record visible as of the diagnosed attempt, vault-wide. The query is the current failure and the index is the `misconception/statement` vectors that embed-on-write and the backfill pay for.
  - **What is offered.** Up to `knn_limit` kNN-only candidates are added after the exact neighbourhood set.
  - **Completeness first.** Missing or stale vectors are embedded first, under the retrieval caps. Only a complete index for the model is ranked.
  - **Fallback.** Any failure, refusal or missing client records `exact_fallback` and keeps the exact set.
  - **Provenance.** The universe size, ranks, scores and exact vs kNN source go to `retrieval_json.registry_retrieval`.
  - **Identity.** `registry_match` stays the diagnoser's call, validated against the closed world.
- **F9.** The store owns one eligibility rule, `Repository.current_live_diagnosis`: the attempt's latest live diagnosis, completed, for its current blind grade. `diagnosis_for_attempt`, the overlays and the card status all use it.
- **F10 (E7).**
  - **The wait.** The bounded next-item wait stays on the queue build and is remembered per session.
  - **The receipt.** It is written when an item is actually served (`get_practice_item` with a session) in a session that has a diagnosis-bearing answer. `served_without_diagnosis` is true when one of those diagnoses is still queued or running.
  - **The rate.** The report's rate is over that population, and queue refreshes write nothing.
  - **No schema change.** Only the migration comment describing the rows changed.

### The review's "claims that don't hold"

- **PF-c gate, non-practice graders, concurrency one, single read path.** These are F1, F2, F6 and F9, all fixed above.
- **C1 coverage: pre-diff vs post-diff equivalence across all tracked fixtures.**
  - **The comparison.** Each of the 8 tracked joint fixtures was copied with the backup API to `fixtures-local/c1-<name>-{base,post,post2}`. Each copy was rebuilt at its own algorithm version with a frozen clock: once with the pre-M2 source (`06b01a22`, its own migrations) and twice with this branch.
  - **What was compared.** Every DERIVED table plus the four tables replay rewrites (`error_events`, `causal_hypotheses`, `attempt_debug_payloads`, `unresolved_cause_factors`): 14 tables.
  - **Six fixtures are byte-identical.** `conic-sections`, `law`, `physical_therapy` and `linear_algebra_legacy` are at mvp-0.6; `arxiv_v2` and `probability` are at mvp-0.8.
  - **Two match modulo fresh ids.** On `arxiv` (365 rows) and `linear_algebra` (721 rows), both at mvp-0.8, base and post are identical once ids are masked. The masked ids are the hypothesis ULIDs every rebuild mints, and the diagnosis-receipt ids hashed from them. Two rebuilds with the same code differ in exactly those ids.
  - **Where it lives.** The scripts are in the session scratchpad and the copies in the gitignored `fixtures-local/`. It is evidence, not a test, because it needs the old source tree.

### Deviations and notes

1. **Cross-LO registry matches are recorded, not merged.** The shortlist lets the diagnoser match a durable belief outside the LO neighbourhood. The match validates and is stored in the diagnosis. Misconception normalization still merges an event only into beliefs in its LO/confusable scope: the promotion rules are unchanged, so it falls through to the holding pen. Merging across LOs is an owner decision (open question 1).
2. **Metered diagnosis routes now need a known price.** Live diagnosis on an unpriced metered route is skipped as `budget` before anything is sent. The default (Codex on the subscription) is unaffected, and `diagnose retry --price-per-million` supplies a price per command (open question 2).
3. **This reverses an M2 deviation.** The M2 review said graders other than ordinary practice "keep the joint prompt: they are already history-free". They now use the blind prompt in split vaults, as spec §4.1 says. In a split vault, a regrade of a joint or self-graded practice attempt converts it to blind-graded. Replay preserves historical semantics by reading the persisted grader mode. New grading calls are never joint.
4. **The grading-epoch contract the learner field reads is unchanged.** Regrades still append superseding `grading_evidence` rows exactly as before. F1 only fills `attribution_json` on unverified rows, and F4 only makes the regrade's writes atomic.
5. **Old E7 receipts are not comparable.** Receipts written before F10 (only in the M2 live-run copies under `fixtures-local/`) were written at queue time.
6. **The live daily counter includes earlier runs.** The live smoke copy's counter showed the 5 calls the M2 live runs made earlier today, so admission accounting reads real history.

### Live smoke test (paid calls, fixtures-local copy)

Run on `fixtures-local/m2-linear_algebra`, the M2 backup-API copy (mvp-0.10, `history_mode = "hybrid"`, embeddings on). The tracked vaults were never written. A `--dry-run` preceded each drain.

| Step | Route | Result |
|---|---|---|
| `learnloop attempt pi_axiom_commutative_recall_02 --no-diagnose` (a wrong answer) | Codex `codex_low` (gpt-5.6-sol), blind isolated | graded in 36 s, score 0, blind record written, diagnosis queued |
| `diagnose drain --dry-run`, then `diagnose drain` | Codex (subscription) + OpenRouter `qwen/qwen3-embedding-8b` | dry run: 1 call, about 3,265 input tokens, admissible; run: diagnosis completed in one turn (28 s); spend charged 1 call, `estimated_only`; registry shortlist `knn` added the vault's one durable belief, which sits outside the LO neighbourhood; hybrid `knn`; embed job done |
| `regrade_attempt` on a historical JOINT attempt (scratch script) | Codex, blind isolated (`mvp-2.1-blind-reference-policy`) | 29 s; first blind record (no supersedes) and its diagnose job written in the publication transaction |
| `diagnose drain --dry-run`, then `diagnose drain` | Codex + OpenRouter | re-diagnosis completed; embed job done |

Calls since 10:38 UTC:

- **Codex:** 2 blind-grading turns (32,729 in / 3,363 out) and 2 diagnosis turns (30,651 in / 2,910 out), with no JSON repairs. This is the owner's subscription, `estimated_only`, with no metered spend.
- **OpenRouter:** 4 receipted embedding calls (940 tokens), $0.0000094.

## Test results (gate)

Run on the fix commits (`56054049`..`77991b93`), before the documentation commit.

- `uv sync --extra dev`, `uv pip install pypdfium2`: done.
- `uv run lint-imports --no-cache`: **8 kept, 0 broken**.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`: **6552 passed**, 0 failed, 162 s. The run added `-q -p no:cacheprovider`, which changes neither selection nor counts. That is 23 more than the M2 gate's 6529: the new review tests (the F4 crash test is parametrized 5 ways).
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`: **72 passed**, 6480 deselected, 45 s. The new F3 concurrency test runs in this lane.
- Frontend: not rerun, because the fixes change nothing under `apps/` (and nothing under `learnloop_mobile`).
- Schema: unchanged. The only migration edit is the comment above `diagnosis_wait_receipts`.
  - The DB reference was regenerated anyway, because its citations follow source line numbers and the validator failed on the stale ones.
  - `db_generate_reference.py`: 268 table notes. `db_validate_reference.py`: `errors: []`. `validate_vault.py`: passed (1,031 notes).
- CLI help snapshot (`tests/cli_help_snapshot.json`): regenerated for the new `diagnose drain` and `diagnose retry` options.

## Open questions

1. Should the diagnoser's validated `registry_match` on a shortlisted belief from another LO merge the event into that belief? Normalization's LO/confusable scope is unchanged for now.
2. Live diagnosis on a metered route needs a known price (fail closed). Add a `diagnosis.price_per_million` config field, or keep the per-command `--price-per-million`?
3. Non-practice graders in split vaults use the mvp-2.0 blind prompt without the PF-c reference policy (teach-back grades transcripts, exams grade under time). Should PF-c extend to them?
4. `diagnose drain` now admits a diagnosis's retrieval embeddings on the command's caps (F12). Embed-on-write jobs (`--kind embed`) still run under their own per-job caps, reported in the plan's `embed` block. Should they move onto the command budget too?

## Re-review

Codex re-review `codex-agent/jobs/20261012-064814-gAd2OZ` of `5aed28d7..slice-1/m2` (at `e83396be`).

- **Confirmed fixed:** F1, F2, F3 and F4 (the four Highs).
- **Confirmed as claimed:** F5 to F10.
- **Reopened:** three new Medium findings, F11 to F13.

Each new finding was first reproduced with a test that failed on the unfixed source, then fixed. Tests use fakes only. The live smoke test below made real calls on a fixtures-local backup copy.

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F11 | Medium | Blind teach-back grades retain the joint calibration identity | fixed | `8ed33443` | `tests/test_teach_back.py`: `test_a_teach_back_grade_is_calibrated_and_replayed_under_its_graders_identity` (split and joint), `test_a_teach_back_regraded_blind_keeps_the_blind_identity_through_rebuilds`; `tests/test_exam_session.py`: `test_an_exam_answer_is_stamped_with_its_graders_calibration_identity` (split and joint) |
| F12 | Medium | Registry retrieval bypasses the new command spend caps | fixed | `af8676ad`, `106be2bf` | `tests/test_diagnosis_reports.py`: `test_retrieval_embeddings_are_admitted_and_charged_on_the_command_budget`, `test_retrieval_never_takes_the_call_a_queued_diagnosis_needs`, `test_an_attempt_scoped_command_reserves_only_its_own_diagnosis` |
| F13 | Medium | Failed diagnoses are recorded as available at serve time | fixed | `6f422031` (DB reference: `962df33e`) | `tests/test_diagnosis_async_router.py`: `test_a_failed_or_budget_skipped_diagnosis_is_unavailable_at_the_serve` |

No finding was rejected.

### What changed, by finding

- **F11 (calibration identity).**
  - **Reproduced.** In a split vault:
    - a blind teach-back grade stamped `grading_prompt_v1` / `grading_proposal_v1` on its raw grade, and every soft-score lookup (live and replay) selected that pair;
    - a teach-back regraded blind replayed under the joint pair;
    - exam answers had the same defect: the same F2 change made them blind, and they took the same fix.
  - **Teach-back.** `_grade_and_apply_transcript` passes `vault_grading_calibration_identity(vault)` into `ApplyAttemptInput.grader_identity`. In a split vault that is the blind mvp-2.0 pair (`grading_prompt_v2_blind`, `blind_grading_proposal_v1`); it has no PF-c, so it is not the 2.1 pair. A joint vault gets None. The raw grade and the calibration lookup both use it.
  - **Exams.** `record_exam_answer` stores the identity with the grade (`calibration_identity`, only when it is not the joint grader's). `finish_exam` stamps it on the raw grade.
  - **Replay.** `replay_grader_identity` reads, in order:
    1. the blind record, as before;
    2. else the attempt's newest primary raw grade, when it carries the blind output schema;
    3. else None (joint).
    `raw_grade_events` is a raw ledger, so no config is read. Teach-back writes no blind record, so this is where its identity lives.
  - **Teach-back regrades.** A teach-back regrade passes its new grade's identity to its own replay through `replay_learning_object(grader_identity_overrides=...)`. That replay stamps it on the raw grade it appends, so later rebuilds read it.
  - **Joint vaults replay exactly as before.** Only a blind-schema raw grade changes the replay identity. None of the joint fixture copies under `fixtures-local/c1-*-base` has one (0 of 307 raw grades across 9 copies).
- **F12 (retrieval on the command budget).**
  - **Reproduced.** A `--max-tokens 0 --max-cost-usd 0` drain on an embeddings-on vault sent 2 embedding requests: a registry batch and its query. Neither was charged.
  - **Admission.** With a command budget, every retrieval embedding request is admitted and charged on it (`register_retrieval_route`):
    - route `embedding`, metered;
    - the published price wins over `--price-per-million`, which is for an unknown price; an unknown price still fails closed;
    - the subscription exception stays with the diagnosis route.
  - **The reserve rule.** Retrieval is optional (S6), so a request is admitted only while every queued diagnosis still fits after it. Each needs a call plus its output limit; an `--attempt` drain or a `retry` reserves only its own. A refusal sends nothing, and that diagnosis uses the exact set (`exact_fallback`, `SpendLimitExceeded`).
  - **Metering.** The hybrid index's centring embeds now run inside the diagnosis's observer, so they are metered and receipted.
  - **Dry run.** `drain` and `retry --dry-run` add a `retrieval` block: requests, input tokens, cost, and whether it fits beside the diagnoses. It is an upper bound mirroring the retriever: missing vectors in batches of 32, plus one query per index, with vectors an earlier planned diagnosis embeds counted once. `admissible` still covers the diagnoses, the command's required work.
  - **Unchanged.** Without a command budget (sidecar worker, inline path), per-job `RETRIEVAL_CAPS` apply as before. The `--max-calls`, `--max-tokens` and `--max-cost-usd` help now names retrieval; the help snapshot is regenerated.
- **F13 (E7 availability).**
  - **Reproduced.** For a required diagnosis that failed or was skipped for budget, the serve receipt said `served_without_diagnosis = false`. An attempt a regrade left `not_needed` still produced a receipt.
  - **The fix.** `session_diagnosis_availability` reads each session attempt's `diagnosis_status`, which follows the diagnosis in force:
    - `done` is available;
    - `pending` (queued, running) and `failed` (failed, budget-skipped, rejected, or written for a superseded grade) are not;
    - `not_needed` is outside the population; a session with no required diagnosis writes no receipt.
  - **The receipt.** `pending_attempt_ids_json` now names every unavailable attempt. There is no schema change: the migration-167 comment and the report's population label were updated, and the DB reference regenerated.

### Deviations and notes

1. **Embed-on-write jobs are not on the command budget.** They keep their per-job caps, as F5 left them; see open question 4. F12 covers the embedding requests a diagnosis makes.
2. **The diagnosis reserve is approximate on a metered diagnoser.** It holds back each queued diagnosis's call and output limit, but not its input tokens. A tight token cap on a metered diagnosis route can still release a later job as `over_budget`, unspent. On the default subscription route the reserve is exact (calls only).
3. **The grading-epoch contract the learner field reads is unchanged.** No `grading_evidence` write changed. F11 changes only the calibration identity stamped on non-practice blind raw grades in split vaults.
4. **Charges are reservations.** A run charges each admitted embedding request at its admission estimate (reservations are never refunded, `ai/spend.py`). Each receipt records the reported usage and cost.

### Live smoke test (paid calls, fixtures-local copy)

Run on `fixtures-local/m2-linear_algebra`, the M2 backup-API copy (mvp-0.10, `history_mode = "hybrid"`, embeddings on). The tracked vaults were never written.

| Step | Result |
|---|---|
| `learnloop attempt pi_axiom_commutative_recall_02 --ai-provider codex_low --no-diagnose` (a wrong answer) | Codex blind grade in 26 s, score 0, diagnosis queued |
| `diagnose drain --kind diagnose --max-tokens 0 --max-cost-usd 0 --dry-run` | 1 diagnosis admissible; retrieval 1 request, 801 tokens, `fits: false` (`total_tokens exceeds max_total_tokens`) |
| the same drain, run | diagnosis completed (52 s); hybrid retrieval `exact_fallback` (`SpendLimitExceeded`); 0 embedding requests, no embedding receipt; charged 1 call, 0 metered tokens, $0 |
| a second wrong answer, then `diagnose drain --kind diagnose --dry-run` | retrieval 2 requests (the first answer's divergence vector, then the query), 1,651 tokens, $0.0000165, fits |
| the same drain, run | diagnosis completed (34 s), hybrid `knn`; 2 embedding requests admitted, charged and receipted under the attempt (312 tokens reported, $0.0000031); charged 3 calls, 1,651 metered tokens, $0.0000165 |

Calls since 15:25 UTC:

- **Codex:** 2 blind-grading turns (31,734 in / 2,240 out) and 2 diagnosis turns (33,084 in / 3,379 out), with no JSON repairs. This is the owner's subscription, `estimated_only`.
- **OpenRouter:** 2 embedding calls (312 tokens), $0.0000031.

### Re-review gate

Run on the fix commits (`6f422031`..`962df33e`), before this documentation commit.

- `uv sync --extra dev`, `uv pip install pypdfium2`: done.
- `uv run lint-imports --no-cache`: **8 kept, 0 broken**.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`: **6561 passed**, 0 failed, 169 s.
  - The run added `-q -p no:cacheprovider`, which changes neither selection nor counts.
  - That is 9 more than the first fix gate's 6552: the new tests listed above (F11 is 5 test cases, F12 is 3, F13 is 1).
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`: **72 passed**, 6489 deselected, 47 s.
- **Frontend:** not rerun. Nothing under `apps/` or `learnloop_mobile` changed.
- **Schema:** unchanged. The only migration edit is the comment above `diagnosis_wait_receipts` (F13).
  - `db_generate_reference.py`: 268 table notes.
  - `db_validate_reference.py`: `errors: []`.
  - `validate_vault.py`: passed (1,031 notes).
  - `module_validate.py`: every wikilink and source link resolved.
- **CLI help snapshot** (`tests/cli_help_snapshot.json`): regenerated for the `diagnose drain` and `diagnose retry` help text (F12).
