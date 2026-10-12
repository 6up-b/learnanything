# Slice 1 M2: the live split and the diagnosis card (with PF-c)

> **Integration note (`merge/slice-1-m2`).** `main` already held 167
> (`learner_field_outcomes`), 168 (`activity_family_membership`) and 169
> (`practice_index`), so this milestone's migration is
> `170_blind_grading_diagnosis_split.sql` and the head fixture is
> `fixtures/migration_head_170` (main's 169 head upgraded through 170 only;
> this branch's own 167 head is dropped). The label `mvp-0.10` is unchanged.
> The template comment lines this branch added are left out of the
> decision-only template (all of `[diagnosis]` is modelled defaults), which
> keeps it within its 80-line cap; both defaults snapshots are recomputed.
> The learner field now treats a PF-c unverified criterion as unassessed, so
> it writes no failure outcome there either (`tests/test_field_split_outcomes.py`),
> and the joint-grading guard also pins direct builders of the joint prompt.
> References below to migration 167 and `migration_head_167` describe the
> branch as built.

Branch `slice-1/m2`, worktree created by the workflow from `main` at
`06b01a22` (which already carries Slice 1 M1). Overrides in force (owner,
2026-10-12, `implementation_goal.md` §1a): M2 is built without waiting for the
M1 run, with `history_mode = "full"` (O16); the split cutover is an algorithm
successor with a kill switch and an owner-run upgrade; S1.4b (hybrid kNN) is
built behind `history_mode = "hybrid"`; PF-c joins the blind prompt and its
before/after report is a command; the `recurrence_key` seam is left ready for
Slice 2 T1.

## Plan (written before coding)

Read: `CLAUDE.md`; architecture `Home.md`; the algorithm-change playbook;
`spec_blind_grading_diagnosis_split_v1.md` in full;
`spec_embedding_consumers_v1.md` §5.5 and §5.7; `docs/reviews/slice-1-m1.md`;
`implementation_goal.md` §1a.

### Files

- **Reused from M1, unchanged contracts:** `attempts/blind_grading.py`
  (`BlindGradingContext`, `BlindGradingProposal`, validation, the §4.2 mapping),
  `diagnosis/split/` (context assembler, `DiagnosisProposal`, validators,
  history stores, snapshot, hybrid retrieval, legacy view, `run_diagnosis`).
- **New, domain:**
  - `diagnosis/split/live.py`: split-mode gate, settings from config, the live
    history store (blind records as the overlay), the causal view
    (§4.2 reverse mapping computed once at diagnosis time), `diagnosis_for_attempt`.
  - `diagnosis/split/jobs.py`: the diagnose/embed job handlers (as-of context,
    run, persist, post-diagnosis steps), drain/retry helpers used by the worker,
    CLI and TUI.
  - `diagnosis/split/embeddings.py`: `hypothesis/statement` and
    `misconception/statement` recipes, embed-on-write, the would-merge log,
    the live hybrid retriever wiring (S1.4b).
  - `diagnosis/split/grading_support.py`: PF-c (reference policy, final-answer
    check, valid-alternative gate, blind k-sampling fingerprint and the
    asymmetric-rule shadow log, the grade-uncertainty shadow signal).
  - `diagnosis/split/reports.py`: the end-of-M2 report (E5, E7, card signals)
    and the PF-c before/after report.
- **New, persistence:** `db/stores/diagnoses.py` (registered SQL owner):
  blind records, diagnoses, receipts, card feedback, job queue, would-merge
  and wait receipts, plus the pure overlay merge used by the repository's
  error-event and feedback-metadata reads.
- **Changed:** `algorithm_versions.py`, `ops/vault_upgrade.py`, `cli/app.py`
  (`upgrade --to mvp-0.10`), `config/schema.py` + `config/template.py`
  (`[diagnosis]`), `attempts/attempts.py` (blind live grading, `grader_mode`
  through apply and replay), `attempts/grade_resolution.py` (blind calibration
  identity), `attempts/post_attempt.py` (sync/worker split, job enqueue),
  `attempts/regrade.py` (blind regrade in split vaults + re-diagnosis),
  `attempts/coldness_receipt.py` (§10), `diagnosis/followups.py` (hook split),
  `diagnosis/misconceptions.py` (`registry_match` instead of
  `misconception_match`), `substrate/canonical_projection.py` (open-factor
  refresh after diagnosis), `substrate/replay.py` (raw events),
  the `recurrence_key` sites (§7.6), `db/repositories.py` (overlay reads),
  `ops/embedding_backfill.py` (DB recipes), `cli/diagnose.py` (drain, retry,
  status, report, pfc-report), `cli/app.py` + TUI (inline diagnosis),
  doctor (failed/stale jobs).
- **Sidecar:** `learnloop_sidecar/post_attempt_worker.py` (daemon worker, two
  slots, completion events), `context.py` (owns it), `handlers/practice.py`
  (`diagnosisStatus` on submit), `handlers/diagnosis.py` (`diagnosis_status`,
  `record_diagnosis_feedback`), `handlers/queue.py` (bounded next-item wait,
  `served_without_diagnosis` receipt).
- **Frontend:** a `DiagnosisCard` in the feedback view (pending placeholder,
  2.5 s polling, one optional tap in fixed neutral order, per-citation "not the
  same mistake"), DTOs and client methods, vitest tests.

### Migration

`167_blind_grading_diagnosis_split.sql` (next free; other unmerged branches
claim 167-169, so expect renumbering at integration):

| Table | Role |
|---|---|
| `blind_grade_records` | RAW_LEDGER (append-only; the validated blind grade a diagnosis reads; supersedes on regrade) |
| `attempt_diagnoses` | RAW_LEDGER (append-only; `supersedes_id` for re-diagnosis) |
| `diagnosis_context_receipts` | RECEIPT |
| `diagnosis_feedback` | RAW_LEDGER (card taps; eval only) |
| `diagnosis_would_merge_log` | RECEIPT (§9.5) |
| `diagnosis_wait_receipts` | RECEIPT (E7 `served_without_diagnosis`) |
| `post_attempt_jobs` | WORKFLOW (lease-fenced queue) |
| `diagnostic_augmentation_receipts.grader_mode` | new nullable column (null = joint) |

Head fixture `migration_head_166` → `migration_head_167`, five references,
DB reference regenerated.

### Algorithm successor and kill switches

- `DIAGNOSIS_SPLIT_ALGORITHM_VERSION = "mvp-0.10"`, immediate successor of
  `mvp-0.9`, in `P0_SUCCESSOR_VERSIONS` (projection semantics inherited).
  `learnloop upgrade --to mvp-0.10` (owner-run; refuses jumps; prepares the
  projection before the atomic config rename).
- Kill switch `diagnosis.split_enabled` (default true): off restores joint
  grading exactly for new attempts in an mvp-0.10 vault; already-blind attempts
  keep their records and replay from them (grader mode is per attempt, never
  read from today's config).
- `diagnosis.card_enabled` (UI), `diagnosis.history_mode`,
  `diagnosis.grading_support` (PF-c prompt), `embedding.enabled` (S1.4a/b).
- The template stays at `mvp-0.9`; new vaults upgrade by command until S1.5.

### Spend caps and model routes

- `ai.routing.grading` (blind grader), `ai.routing.diagnosis` (defaults to the
  resolved grading route), `ai.routing.embedding` (never falls back). Codex is
  the default and runs isolated turns (M1 profile) for grading and diagnosis.
- Live diagnosis: one call per erroring attempt, `diagnosis.max_calls_per_day`
  cap (budget skip, never the grade); Codex cost recorded `estimated_only`.
- Live embeddings: per-job `SpendBudget` (one call, bounded tokens and dollars).
- `pfc-report` and the M2 report: `--dry-run` estimate first; caps on items,
  calls, tokens, dollars.

### `judgment_ledger` writes

- Validated pattern claims: `same_cause` rows, judge `diagnoser`.
- Card "not the same mistake" taps: `same_cause` = `different`, judge
  `learner_card`.
- PF-c report: valid-alternative verdicts (`reference_verified` by the
  deterministic checker, judge `exact_key`) and grade verdicts per prompt.

### Tests

The §14 M2 files: `test_diagnosis_pipeline.py`, `test_diagnosis_replay.py`,
`test_post_attempt_worker.py`, `test_diagnosis_async_router.py`,
`test_diagnosis_card.py`, `test_embedding_store.py` additions, the upgrade and
kill-switch tests, the recurrence-key seam, cold-verification blinding, PF-c
grading support, the reports, plus vitest for the card. Durability lane runs the
pipeline and replay files.

## As built

Commits on `slice-1/m2` (from `06b01a22`): `b7101778` (the split, the
diagnoser, the card, PF-c), `b54cea9b` (tests, head fixture 167, docs,
cycle-free imports), `bb4a324a` (fixes found by the live runs below), plus
this review.

### What M2 does

- **Blind grading is live in `mvp-0.10`.** Practice attempts in an `mvp-0.10`
  vault with `diagnosis.split_enabled = true` are graded by M1's learner-blind
  contract (`BlindGradingContext`, no history), through the M1 isolated-turn
  Codex profile. The validated blind grade is appended to `blind_grade_records`
  in the same transaction that applies the attempt. Error events and feedback
  metadata carry only grader-owned fields (no repairs, no misconception
  match, no causal candidates).
- **The diagnosis is a durable job.** The completion transaction also enqueues
  a `diagnose` row in `post_attempt_jobs` (lease-fenced, `lease_epoch`
  fencing, attempt-ordered, backoff, `max_attempts`, daily call cap with a
  `budget` skip, provider-not-ready release with no attempt spent). Correct
  answers need no diagnosis (§5.1); a shadow sample is configurable
  (`correct_answer_sample_rate`, default 0).
- **Where the job runs.** The sidecar's `PostAttemptWorker` (two daemon slots:
  `diagnose` in strict attempt order, `embed` unordered) starts lazily on the
  first queued job, so a joint vault never starts a thread. The CLI `attempt`
  command drains the attempt's diagnosis inline (`--no-diagnose` only queues
  it); the TUI feedback screen does the same; `learnloop diagnose drain` /
  `retry` / `status` work the queue by hand. Next-item selection waits at most
  `diagnosis.next_item_wait_seconds` (10 s) for this session's pending
  diagnoses, then serves anyway and records a `diagnosis_wait_receipts` row
  (E7 `served_without_diagnosis`).
- **Causal fields come from the diagnosis on read.** A completed live
  diagnosis stores `causal_view_json` (the §4.2 mapping in reverse, computed
  once). `Repository.error_events_for_attempt`, `all_error_events_by_attempt`
  and `fetch_attempt_feedback_metadata` lay the view over the raw rows; replay
  and the legacy view use the `raw_*` accessors. A view applies only while the
  diagnosis read the attempt's current blind grade: a regrade appends a
  superseding blind record, which re-queues the diagnosis in the same
  transaction and hides the stale explanation until the new one lands (or
  records `not_needed` if the regrade leaves nothing to explain).
- **After a diagnosis lands**, the job refreshes the canonical projection for
  the attempt (an open unresolved-cause factor takes the diagnosis's candidate
  set), runs misconception normalization with `registry_match` instead of an
  AI `misconception_match` call, runs the post-diagnosis follow-up hooks that
  the sync path deferred, and writes validated pattern claims to
  `judgment_ledger` as `same_cause` verdicts (judge `diagnoser`).
- **The diagnosis card** (`diagnosis_status` / `record_diagnosis_feedback`
  RPCs, `DiagnosisCard.tsx`): the feedback view polls every 2.5 s while
  pending; when done it shows the summary, the repairs, "You've made this
  mistake before" (validated citations only, with dates), and the
  prerequisite-gap hypothesis marked "possible cause - not yet checked". One
  optional tap in a fixed neutral order; card-only values `partly`/`unsure`;
  per-citation "not the same mistake" (also a learner `same_cause =
  different` verdict). With an open unresolved-cause factor,
  `believed_candidate` / `slipped` / `diagnosis_wrong` are forwarded to that
  factor's existing self-report channel (O14, `forward_card_taps`). Repairs
  first shown by the card are debited to the reveal ledger once per diagnosis.
- **S1.4a / S1.4b.** With embeddings enabled, a completed diagnosis queues an
  `embed` job: the hypotheses it minted and the misconception registry are
  embedded (`hypothesis/statement`, `misconception/statement`, per-job spend
  budget), then the would-merge log (§9.5) records each new hypothesis's
  nearest EARLIER hypotheses next to its exact-key group. Read by nothing that
  routes. `learnloop embeddings backfill --record-kind hypothesis|misconception|attempt`
  embeds history. `history_mode = "hybrid"` (S1.4b) runs M1's hybrid
  retriever live (exact filter + kNN over `attempt/divergence`, RRF) and falls
  back to exact silently without embeddings.
- **PF-c.** The blind prompt becomes `mvp-2.1-blind-reference-policy`: the
  item-side reference policy (computed deterministically) joins the blind
  context; a deterministic valid-alternative gate turns unlocated failures on
  an answer whose final answer verifies against the reference into
  `grader_interpretation` validity plus manual review
  (`valid_alternative_unverified`, points kept); k-sampling (when configured)
  records a fingerprint and the asymmetric-rule shadow log; a
  grade-uncertainty shadow signal is computed within the item family. Blind
  grades carry their own calibration identity in `raw_grade_events`
  (`grading_prompt_v2_blind` / `grading_prompt_v2_1_blind_reference_policy`,
  schema `blind_grading_proposal_v1`), so calibration never pools them with
  joint grades. `diagnosis.grading_support = false` restores the M1 `mvp-2.0`
  blind prompt. `learnloop diagnose pfc-report` is the before/after command.
- **Cold verification (§10).** A blind cold grade passes context blinding
  with reason `blind_grader`; run separation also checks the diagnosis runs.
  Joint receipts keep their shape.
- **`recurrence_key` seam** (`learnloop/recurrence.py`): every site that
  grouped causal candidates by normalized statement goes through
  `recurrence_key()`, which in Slice 1 is exactly that key. Slice 2 T1 swaps
  the function body.

### Algorithm successor, kill switches, owner-run upgrade

- `mvp-0.10` (`DIAGNOSIS_SPLIT_ALGORITHM_VERSION`) is the immediate successor
  of `mvp-0.9` and a P0 successor. `learnloop upgrade --to mvp-0.10` (from
  `mvp-0.9` only) freezes the manifest, activates the P0 projection, refreshes
  the registry and rewrites the config atomically. The template stays at
  `mvp-0.9` until the S1.5 exit review.
- Grader mode is per attempt (the blind ledger), never read from today's
  config: a vault can hold both shapes and rebuild both.
- Kill switches: `diagnosis.split_enabled` (off: new attempts grade jointly;
  queued live diagnoses are held, not run), `diagnosis.card_enabled`,
  `diagnosis.grading_support`, `embedding.enabled`.
- Playbook evidence: a shadow rebuild of a backup copy of the owner's
  `linear_algebra` vault (70 attempts, all joint) under `mvp-0.10` produced
  exactly the same learner-state changes as a same-version `mvp-0.9` shadow
  rebuild (facet 2, mastery 7, schedule 48 real changes in both; the only
  extra difference is the `algorithm_version` stamp). The successor changes
  nothing for joint history.
- The grading-epoch contract the learner field reads is unchanged: blind
  grades write `grading_evidence` through the same apply path; a blind regrade
  appends a new epoch exactly as a joint regrade does (checked side by side);
  a diagnosis or re-diagnosis writes no evidence and creates no epoch.

### Migration 167

As planned (seven tables plus `diagnostic_augmentation_receipts.grader_mode`),
all classified in `table_roles.py`; append-only triggers on the ledgers. Head
fixture `fixtures/migration_head_166` renamed to `migration_head_167`,
upgraded, left in rollback-journal mode, README and the five path references
updated; DB reference regenerated and validated (schema head 167). Other
unmerged branches also claim 167-169: expect a renumber at integration
(migration file, fixture directory, five references, DB reference).

## Deviations from the plan

- `grading_support.py` lives in `attempts/`, not `diagnosis/split/`: the
  blind grader uses it, and `attempts` must not import `diagnosis` (the frozen
  cycle contract). For the same reason M1's deterministic answer checks moved
  from `diagnosis/offline_review/probes.py` to `attempts/answer_check.py`
  (probes re-exports them), the post-attempt enqueue goes through
  `diagnosis.followups.enqueue_post_attempt_diagnosis`, the regrade's
  re-diagnosis is queued by the store when a superseding blind record is
  written, and the DB-backed backfill recipes are built in the diagnosis
  domain and passed to `ops.embedding_backfill` as extra records. No
  import-linter ignore entries were added.
- The sidecar handler module is `handlers/diagnosis_card.py`; the embedding
  tests are `tests/test_diagnosis_embeddings.py`; the M2 report command is
  `learnloop diagnose m2-report` (`diagnose report` is M1's).
- PF-c verdicts in `judgment_ledger` use judge `verifier` (deterministic
  check) and `llm` (the graded alternative), not `exact_key`.
- Graders other than ordinary practice (teach-back, exams, probe audit,
  taxonomy regrade) keep the joint prompt: they are already history-free.
- PF-c keeps the points on criteria the gate marks unverified (validity
  `grader_interpretation` plus manual review), rather than zeroing them.
  The family key for the uncertainty signal is `surface_group_id` until PF-a.
- `diagnosis.sample_count` is accepted only at 1: diagnoser k-sampling (§4.4
  cause disagreement) is not built in M2.
- New after the live runs: `diagnosis.timeout_seconds` (300 s) gives the async
  diagnoser its own Codex turn deadline instead of the vault's interactive
  `ai.timeout_seconds`; the card summary replaces record ids with "your answer
  on <date>"; PF-c compares against a worked-solution reference's numeric
  conclusion (conservative extraction) and samples checkable references first.
- Embed-on-write covers what a diagnosis mints; older hypotheses need the
  backfill command.

## Live runs on backup copies (paid calls)

All on backup-API copies (`learnloop.db.copies.copy_tree_with_databases`)
under the worktree's gitignored `fixtures-local/`: `m2-linear_algebra` and
`m2-probability` (from `fixtures/linear_algebra` and `fixtures/probability`;
the tracked vaults were never written). Each copy was upgraded
`mvp-0.8 -> mvp-0.9 -> mvp-0.10`; the linear-algebra copy got the embedding
route, profile and `[embedding]` switches, and later
`[diagnosis] history_mode = "hybrid"`. Every paid command ran `--dry-run`
first, inside explicit caps.

| What | Route | Calls | Tokens in / out (cached) |
|---|---|---|---|
| 5 real attempts: blind grading | Codex `codex_low` (gpt-5.6-sol) | 5 requests: 4 completed, 1 timed out at the vault's 60 s | 64,177 / 5,642 |
| Their diagnoses (1 full, 3 hybrid; 1 timeout then retried) | Codex `codex_low` | 5 logical calls, 8 turns (4 first turns, 3 JSON repairs, 1 timeout) | 117,536 / 13,392 (22,016) |
| `pfc-report`, 4 runs (2 + 4 + 6 + 6 items) | Codex (generator) and `codex_low` (grading) | 18 generator turns, 2 grading turns | 220,201 / 10,307 (53,760) |
| Embeddings: 2 backfills (9 hypothesis/misconception + 17 attempt-divergence records), 4 hybrid queries, 3 embed-on-write jobs, 1 manual 2-text check | OpenRouter `qwen/qwen3-embedding-8b` | 10 | about 3,600 / 0 |

Cost: Codex runs on the owner's ChatGPT subscription (`estimated_only`; no
metered spend). OpenRouter recorded $0.000035 for the 9 receipted embedding
calls (the manual check was not receipted; it embedded two short texts).

What the runs showed, and what was fixed (commit `bb4a324a`):

1. **End to end works.** Blind grade (21-24 s), diagnosis (28 s in one
   turn; 55-107 s when a JSON-repair turn was needed),
   causal view on read, card content. The hybrid diagnosis of the second
   wrong answer cited the first one as "made this mistake before" (validated
   citation); the would-merge log and embed-on-write ran; the first
   diagnosis, in `full` mode, declined a durable-misconception claim because
   the learner had passed the same item before.
2. **Every diagnosis paid a JSON-repair turn.** Debug capture showed the
   model writing a phrase into `event_diagnoses[].operation` (pattern
   `^[a-z][a-z0-9_]*$`, no description). The field now carries a description;
   the next live diagnosis completed in one turn (n = 1).
3. **The diagnoser timed out at 60 s.** The owner's vaults set
   `ai.timeout_seconds = 60`, sized for interactive calls. Added
   `diagnosis.timeout_seconds = 300` (below the 1,200 s lease); the job had
   backed off and the retry succeeded. Blind grading still uses the vault's
   60 s: one of five blind grades timed out and fell back to the self-grade
   (existing fallback).
4. **Embed jobs failed under `diagnose drain`** (`FileNotFoundError`): the
   diagnose CLI commands never bound their vault for command receipts, so the
   receipt writer looked for a vault in the cwd. Fixed; embed calls are now
   receipted under their attempt, like the diagnosis.
5. **The M2 report miscounted calls**: embedding rows counted as diagnosis
   calls, and usage read from Codex root rows (which carry none). It now
   counts logical calls, their turns' usage, and JSON-repair turns, and
   stamps UTC.
6. **PF-c verified nothing** on the owner's content: M1's verifier compared
   the generated answer with the whole reference text, and real references
   are worked solutions. A numeric conclusion is now extracted
   conservatively ("... P(E)=6/20=3/10." gives "3/10"; anything ambiguous
   gives none), and the plan samples checkable references first. The last
   run verified 1 of 6 alternatives and graded it under both prompts
   (accepted under both). The other 5 failed M1's rule that every relation
   in the derivation must be checkable (probability notation like
   `P(A ∩ B)` is not). PF-c's E1 numbers on these vaults will be small until
   that is decided (open question below).
7. **The card showed raw attempt ids** in the summary; it now names them
   "your answer on <date>". The summary is still the diagnoser's own analysis
   text (open question below).

Doctor on the upgraded copy: no post-attempt job issues; the one error
(`layout:missing_directory: rubrics`) is the same on a plain copy.

## Test results (gate)

- `uv sync --extra dev`, `uv pip install pypdfium2`: done.
- `uv run lint-imports --no-cache`: **8 kept, 0 broken**.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`: **6529 passed**,
  0 failed, 197 s.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`:
  **71 passed**, 6458 deselected.
- Frontend (`apps/learnloop-tauri`): `npm install` ok; `npm run typecheck`
  clean; `npm test` **63 passed in 15 files**.
- DB reference: `db_generate_reference.py` then `db_validate_reference.py`:
  `errors: []` (schema head 167, 268 table notes, 554 effective config
  leaves in 30 sections); `validate_vault.py`: passed (1,031 notes).
- Not in the gate: `cargo check` could not run on this machine (the system
  `rustc` fails to load `librustc_driver`, an environment problem); the Rust
  change is two passthrough commands and an optional `record_open` flag.
  `module_validate.py` and `desktop_validate.py` fail on the base commit too.

New tests: `test_diagnosis_pipeline.py` (15), `test_diagnosis_replay.py` (4,
durability lane: split rebuild is a fixed point, zero model and embedding
calls in replay, joint reads untouched, joint fixture identical at the
previous version), `test_post_attempt_worker.py` (6),
`test_diagnosis_async_router.py` (5), `test_diagnosis_card.py` (8),
`test_diagnosis_embeddings.py` (4), `test_diagnosis_reports.py` (5),
`test_mvp010_upgrade.py` (7), `test_grading_support.py` (9),
`test_recurrence_key.py` (3), `test_coldness_receipt.py` (+3), vitest
`DiagnosisCard.test.tsx` (5) and a `FeedbackScreen` case.

Pre-existing behaviour noted while testing: the first rebuild after a P0
flip settles calibration priors, so the first and second rebuilds differ at
`mvp-0.9` as well; the replay tests compare from the second rebuild.

## Owner-run commands

On a vault (a `fixtures-local/` copy first):

```bash
uv run learnloop upgrade --to mvp-0.10 --vault <vault>        # from mvp-0.9 (mvp-0.8 vaults: --to mvp-0.9 first)
uv run learnloop rebuild --shadow --set algorithms.algorithm_version=mvp-0.10 --json --vault <vault>  # playbook check before upgrading
uv run learnloop diagnose status --attempt <id> --vault <vault>
uv run learnloop diagnose drain --vault <vault>               # CLI/TUI have no daemon; the desktop worker drains itself
uv run learnloop diagnose retry --attempt <id> --vault <vault>
uv run learnloop embeddings backfill --record-kind hypothesis --record-kind misconception --dry-run --vault <vault>
uv run learnloop embeddings backfill --record-kind attempt --dry-run --vault <vault>   # only for history_mode = "hybrid"
uv run learnloop diagnose m2-report --vault <vault> --out m2-report.md   # end of M2 (S1.5)
uv run learnloop diagnose pfc-report --dry-run --vault <vault>           # then without --dry-run, inside caps
```

Kill switch: `[diagnosis] split_enabled = false`.

## Open questions

1. Template default: new vaults start at `mvp-0.9` and need the upgrade
   command until the S1.5 exit review. Move the template to `mvp-0.10` now?
2. PF-c verifier: M1 requires every relation in a generated derivation to be
   checkable, so on the owner's vaults 1 of 18 generated alternatives
   verified. Relax E1 to "final answer verified", or have the generator write
   arithmetic-only derivations?
3. ~~PF-c gate: criteria marked unverified keep their points (manual review
   flag). Keep, or zero them until reviewed?~~ **Decided (owner,
   2026-10-12): unassessed everywhere, inside `mvp-0.10`.** An unverified
   criterion is neither credit nor failure: it leaves the score and so the
   FSRS rating, writes no facet evidence, and the review flag is a
   non-blocking log. Built on `fix/pfc-unverified-unassessed`
   (`docs/reviews/pfc-unverified-unassessed.md`).
4. The card summary is the diagnoser's `analysis_md`, written for the
   diagnosis (it says things like "withdrawn prior hypothesis"). Add a
   learner-facing summary field to `DiagnosisProposal` (prompt version bump)?
5. Blind grading is synchronous and uses the vault's `ai.timeout_seconds`
   (60 s on the owner's vaults); 1 of 5 live blind grades timed out and fell
   back to the self-grade. Raise the vault timeout, or give blind grading its
   own deadline?
6. O14: card taps are forwarded to an open factor's self-report channel by
   default (`forward_card_taps = true`). Confirm.
7. M1's report is still to come: M2 runs `history_mode = "full"` (O16);
   `hybrid` is built and was exercised live, but stays off unless M1 shows it
   beats `full`.
8. Migration 167 will need renumbering when the other branches that claim
   167-169 merge.
