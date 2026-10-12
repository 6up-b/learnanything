# Slice 1 M2: the live split and the diagnosis card (with PF-c)

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
