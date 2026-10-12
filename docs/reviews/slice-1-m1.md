# Slice 1 M1: offline review of blind grading and history-aware diagnosis

Branch `slice-1/m1`, worktree created from `main` at `aa9320f8` by the
workflow (the prompt's own branch instruction is overridden). All five arms
(a)–(e) are built in one go (owner, 2026-10-12: "finish everything"), and the
contracts are shaped for reuse by M2 and Slice 2 T1. M1 changes nothing live
and adds no vault migration.

## Plan (written before coding)

Read: `CLAUDE.md`; architecture `Home.md`; the algorithm-change playbook;
`spec_blind_grading_diagnosis_split_v1.md` in full (build targets §4, §5
including §5.6, §9.4, §12 M1 row and §12.1, §13 E1–E6, the M1 tests in §14);
`spec_slice_a_practice_and_field_v1.md` §4–§5.

- **Files.** AI layer: `READ_ONLY_WORKSPACE` in `ai/transport.py`, the Codex
  SDK client honouring it, three new routes. Blind grader:
  `attempts/blind_grading.py`. Diagnoser: package `diagnosis/split/`. M1
  harness: package `diagnosis/offline_review/`. Scratch-only store:
  `db/stores/diagnosis_review.py`. CLI: `cli/diagnose.py`.
- **Migrations, successors, kill switches.** None. Nothing is served
  differently; every model output lands in a backup-API scratch copy.
- **Spend caps and routes.** One route per paid component (`grading`,
  `diagnosis`, `diagnosis_judge`, `diagnosis_generator`, `embedding`);
  `--dry-run` prints calls, tokens and cost per route without copying the
  database or building a client; Codex routes are billed to the subscription
  (`estimated_only`), metered routes keep every cap.
- **`judgment_ledger` writes.** Every judge verdict into the scratch copy's
  ledger; `same_cause` rows into the vault's ledger only on `import-links`.
- **Tests.** The five §14 M1 files, plus routing/config/CLI snapshot updates
  and a durability-lane round trip.

## What was built

### Blind grader (§4) — `src/learnloop/attempts/blind_grading.py`

- `BlindGradingContext`: today's grading context **without**
  `diagnostic_history`, as a new type, so S1 cannot be undone by
  configuration. Item-side material only (C2 verifier observations are passed
  in by the caller; they read nothing but the answer and the reference).
- `BlindGradingProposal` in §4.3 generation order: `local_analysis_md` →
  `repaired_traces[]` (each with an id) → localization fields →
  `exercised_facets` last. Attributions carry `validity_scope`
  (`valid_measurement | item_contract | grader_interpretation |
  interaction_context | unknown`) and an optional `repaired_trace_id`; there is
  no causal field (no candidate causes, misconception statement, operation,
  causal confidence, postdictive claims or instructional repair).
- Prompt `mvp-2.0-blind-local-grader`: every causal instruction and the "test
  recurrence" sentence are gone. Calibration identities
  `grading_prompt_v2_blind` / `blind_grading_proposal_v1` are defined for M2 to
  stamp into `raw_grade_events`.
- Validation maps the proposal onto the joint `GradingProposal` (§4.2 in
  forward direction: `local_analysis_md` → `diagnosis_md`, each repaired trace
  → a structural-only repair suggestion, `validity_scope` → the joint
  `cause_scope` gate value, `is_misconception` = the taxonomy prior, O2) and
  reuses `validate_codex_grading_proposal`, so scoring, anchoring, splice,
  passed-facet firewall and clarification rules are identical. Duplicate trace
  ids are rejected; dangling `repaired_trace_id`s are dropped.

### Diagnoser (§5) — `src/learnloop/diagnosis/split/`

- `history.py`: typed **blind-grade-equivalent** history records (date,
  surface group, score, failed/passed criteria, failed criteria's facets,
  first-divergence quotes, error types, targets, validity, assisted/primed,
  answer text for full/snapshot), typed hypotheses (causal hypotheses,
  unresolved factors, durable misconceptions) with an S3 lifecycle status and
  evidence count, registry rows (durable + holding pen), repair records with
  cold-verification counts. `VaultHistoryStore` reads a database with an
  optional blind-grade overlay and strips legacy joint attempts **by
  construction** (there is no field for causal prose). `StaticHistoryStore`
  holds a constructed past (planted learners). Both apply the as-of cutoff
  (attempts strictly before; hypotheses/registry only when their source
  attempt precedes) and report `lagged_attempts`. The one-hop neighbourhood
  covers prerequisite and confusable edges both ways, plus same-concept LOs.
- `context.py`: deterministic assembly for `exact | full | snapshot |
  hybrid`; oldest-first truncation with disclosed dropped counts (hypotheses
  never before attempts); `context_hash`; the closed-world `KnownIds`; and the
  §5.2 cache layout — neighbourhood, registry and history first, the volatile
  hypotheses/repairs/disclosures after, the current attempt last — so a later
  diagnosis on the same LO shares the whole prefix before its newest history
  row (`cacheable_prefix`, tested).
- `contract.py`: `DiagnosisProposal` (§5.3) and its recite-first twin for
  full/snapshot/hybrid (evidence ids generated before the analysis), the
  diagnoser prompt with the anti-anchoring instruction (§5.5) and the
  snapshot rules.
- `validation.py`: every §5.4 rule, recorded in `validation_report` —
  closed-world ids with `unknown_id_count` (M1's invented-history metric),
  evidence ids, verbatim-quote re-anchoring through the grader's
  `resolve_quote_anchor`, S4 citation validity (blind non-pass on an
  overlapping failed target, valid measurement) grouped by surface group,
  passed-facet and scope firewalls, `validate_repair_candidate` plus the
  trace-id check, registry-match rules, and §5.5 `anchoring_suspect`.
- `snapshot.py`: the §5.6 whole-vault as-of export (attempts, hypotheses,
  registry, graph, repairs, INDEX), manifest hash, and a workspace that is
  deleted on success and on failure.
- `retrieval.py`: §9.3–9.4 hybrid kNN over grader-written divergence text
  through the Phase 1 client and store (content-hash idempotent, centred
  over every prepared record), reciprocal-rank fusion with per-item
  provenance, and `exact_fallback` on any failure (S6).
- `legacy_view.py`: the stored joint diagnosis in the new shape (§6.3 reverse
  mapping, `mode='legacy_view'`) — M1's arm (a) and the seed of M2's
  `diagnosis_for_attempt`.
- `diagnoser.py`: one diagnosis (assemble → call → validate → receipt), the
  unit M2's async worker will run.

### Codex read-only workspace (§5.6) — `ai/transport.py`, `ai/providers/codex.py`

`StructuredRequest.workspace`; `execute_structured_operation(workspace=)`
refuses before any request when the transport lacks `READ_ONLY_WORKSPACE`.
The Codex SDK client starts the app server, the thread and the turn with
`cwd=<snapshot>` (replacing, never joining, the vault root), with
`sandbox="read-only"` and `approval_policy="never"`, and fails closed when
the installed SDK's `thread_start` cannot take a sandbox. Tool items the turn
reports are kept as best-effort "files opened".

### M1 harness (§12.1) — `src/learnloop/diagnosis/offline_review/`

- **Sample**: model-graded practice attempts with an error and an answer,
  stratified across LOs × time quartiles, seeded.
- **Planted learners (S1.0)**: `changed_cause` (with a prior hypothesis A —
  C4's revert control), `paraphrased_recurrence` (two cross-surface A
  failures, a C distractor and a pass) and `same_answer_different_cause`;
  written by the `diagnosis_generator` route (or an authored
  `--planted-manifest`), validated structurally (quotes verbatim, shapes
  complete), given real-looking ids, isolated from the real history, and
  interleaved unlabelled among the real targets.
- **Arms**: (a) the stored joint diagnosis (no call; for planted learners the
  joint grader is re-run with today's C4 filter), (b) exact, (c) hybrid,
  (d) full, (e) snapshot — same diagnoser client, prompt and effort — plus
  (b′) a repeat of (b) on a subset (noise floor), (b0) a history-free control
  on planted learners (E2), and the (d) context-length sweep on planted
  learners at 25K/50K/100K and the configured budget.
- **Blind grading** of every target, the joint grader's **repeat** on real
  targets (E1's joint-vs-joint-repeat noise floor), and the E1 **probes**:
  valid-alternative false rejection (deterministically verified by exact
  match or SymPy), real-vs-synthetic gap (planted single-criterion errors vs
  owner-adjudicated real grades), and grade flips under paraphrase.
- **Judge**: per item, one call rates every arm (right / partly / wrong /
  not sure), picks the best and states a preference for each decision-rule
  pair, under shuffled neutral labels; two passes with the order reversed,
  agreement reported. Pattern links are judged separately with both answers
  side by side (two passes); planted causes are matched against the known
  truth. Every verdict goes to the scratch copy's `judgment_ledger`.
- **Report** (`report.py`): aggregates only (asserted in tests) — per-arm
  status, invented ids, anchoring, citations, tokens (cached and uncached),
  cost basis and latency p50/p95; judge ratings, best picks and pairwise wins
  with the (b)/(b′) noise floor; planted recovery, presence/citation/
  validation of expected links, kept-apart rate and the sweep; link
  trustworthiness per arm and links unique to an arm; kNN-only citations; E1
  agreement (κ, exact score, fatal), anchor accuracy vs adjudications, the
  three probes; E4 registry match vs the legacy misconception ids; the
  spot-check and judge–owner agreement.
- **Spot-check** (`spot_check.py`): ≤ 10 stratified items, three screens
  (diagnoses, pattern links, grade disagreements), hidden shuffled labels,
  skip on every screen, resume across sessions. Arm (a) taps on real attempts
  become genuine `diagnosis_adjudications` rows (`human_owner`, `sampled`);
  everything else stays in the scratch `review_judgments`.
- **Import** (`links.py`): pattern-link verdicts between two real attempts
  (never planted ids) append to the vault's `judgment_ledger` as `same_cause`
  rows (judge `llm` with model/prompt/input hash, or `owner`), idempotently.
- **Spend** (`spend.py`): per-route admission before every physical request,
  usage metering through `model_call` observation, receipts in the scratch
  copy's `model_call_receipts`, per-call rows in `review_calls`.
- **Runner** (`runner.py`): plan → estimate → copy → stages, each unit of
  paid work checkpointed by its row; failed units are retried on resume; the
  planted stage runs once per run (a resume never re-drafts rejected cases or
  reshuffles targets); SIGINT/SIGTERM stops before the next request. A fresh
  run that exceeds its caps, or has no ready grading or diagnosis route, is
  refused before anything is copied.

### Scratch store and CLI

- `db/stores/diagnosis_review.py`: the `review_*` tables, created only in a
  copy carrying a scratch marker; every writer asserts the marker.
- `learnloop diagnose data-check | run | report | review | import-links`.

## Deviations from the spec and prompt (and why)

1. **`--dry-run` means the Slice A estimate.** It copies nothing, builds no
   client and calls nothing. The spec's "dry-run into a scratch DB" is what
   every real `diagnose run` does: the vault database is only read.
2. **`learnloop field data-check` is not on this base** (it is on the
   unmerged Phase 2 branch). `learnloop diagnose data-check` reports the same
   count with the same ~40 threshold; either works once the integration lands.
3. **No `[diagnosis]` config section in M1.** M1 settings are a
   `DiagnosisSettings` dataclass with the §12 defaults, exposed as command
   options; M2's config section should map onto it. The three new routes are
   config (`ai.routing.diagnosis` → the resolved grading route when unset;
   `diagnosis_judge` and `diagnosis_generator` → the active provider). The
   mvp-0.9 effective-defaults snapshot was updated for the dormant routes (no
   serving change). The Settings UI does not list them yet (M2, when the
   diagnoser goes live).
4. **Subscription spend rule implemented locally**
   (`offline_review/spend.py`), mirroring the `ai/spend.py` change on
   `integrate/slice-a-2-3`, which is not on this base. M2 should switch to the
   shared `SpendBudget(subscription=...)` once both are merged.
5. **As-of prerequisite status and success history** are derived from as-of
   attempts (demonstrated / attempted / untested) rather than
   `capability_grid` and `facet_evidence_timelines`, which read today's state
   and would leak later evidence into an asynchronous or offline diagnosis.
6. **Listwise-pairwise judge.** One call per item per pass rates all arms and
   states the decision-rule pair preferences (2 calls per item instead of ~16
   pairwise calls); the order is reversed between passes and their agreement
   is reported. Planted-cause matching runs one pass.
7. **(b0) uses an empty history store** (no hypotheses either), a stricter
   "no history" than `history_error_limit=0` alone, as E2 asks.
8. **The context-length sweep** pads the planted needles with real
   distractor attempts from the same neighbourhood. On a vault with little
   history the budget is not reached; the report shows the actual context
   tokens at each point.
9. **Arm (a) spot-check mapping.** right → `correct` (`correctly_abstained`
   when the system abstained); wrong with an optional repair → `wrong_repair`
   (`should_not_have_abstained`). "Partly", "not sure" and a bare "wrong"
   stay in the scratch copy, because the adjudication vocabulary needs an
   anchor or a repair for them.
10. **E3 repair-class agreement is not computed** (planted cases carry no
    repair-class truth); E3 reports cause recovery for the diagnoser vs the
    joint grader vs the repeat.
11. **§5.5 "not supported by the local reading"** is a deterministic
    content-word overlap with the blind local analysis, threshold 0.2, recorded
    with its score.
12. **Exact/hybrid token budget** is 12,000 (the spec gives no number).
13. **Vault validation issues warn instead of refusing**: the review only
    reads, and an item that fails to load is simply not sampled.
14. **M1 writes no `grader_mode` receipt column** (that is M2's migration).

## Test results

Recorded on the final commit (see "Gates" below).

New test files: `test_blind_grading_contract.py` (10),
`test_diagnosis_contract.py` (12), `test_diagnosis_context.py` (8),
`test_diagnosis_history_modes.py` (14), `test_diagnose_review.py` (17, one
in the durability lane). Shared fakes: `tests/diagnosis_fakes.py`,
`tests/diagnosis_split_helpers.py`; `tests/structured_ai.py` gains the
`blind_grading` and `diagnosis` purposes and `tests/openai_fakes.py` a
`blind_grading_json()`.

### Manual run on a fixtures-local copy (fakes only)

`fixtures/linear_algebra` (this worktree's tracked copy) was copied with
`learnloop.db.copies.copy_tree_with_databases` to
`fixtures-local/m1-linear_algebra`.

- `diagnose data-check`: 6 graded wrong answers over 4 LOs (below the ~40
  threshold; the owner's live vault decides).
- `diagnose run --dry-run`: 12 targets (6 real + 6 planted), 196 planned
  calls, admissible, with arm (c) honestly listed as skipped (embeddings are
  off in that vault).
- A full run with the test fakes on every route (fake embeddings included, so
  arm (c) ran): all arms, (b′), (b0), the sweep, the judge and the probes,
  194 fake calls, status `complete`. The copy's `state.sqlite` SHA-256 was
  identical before and after
  (`092b795a…8d126`).
- `diagnose report` wrote the markdown and JSON; none of the 87 learner
  answers in the copy or the planted cases appears in either.
- `diagnose import-links --dry-run`: 16 importable links, 28 planted links
  excluded (the copy predates migration 166, so a real import would migrate
  it first through the vault factory).

## Files touched

- AI and config: `src/learnloop/ai/transport.py`,
  `src/learnloop/ai/providers/codex.py`, `src/learnloop/ai/routing.py`,
  `src/learnloop/config/schema.py`, `src/learnloop/config/template.py`.
- New: `src/learnloop/attempts/blind_grading.py`,
  `src/learnloop/diagnosis/split/` (9 modules),
  `src/learnloop/diagnosis/offline_review/` (9 modules),
  `src/learnloop/db/stores/diagnosis_review.py`, `src/learnloop/cli/diagnose.py`.
- CLI registration: `src/learnloop/cli/__init__.py`.
- Tests: the five new files above, `tests/diagnosis_fakes.py`,
  `tests/diagnosis_split_helpers.py`, `tests/structured_ai.py`,
  `tests/openai_fakes.py`, `tests/test_architecture.py` (registered SQL
  owner), `tests/cli_help_snapshot.json`.

## Migrations

None. The scratch copy is migrated to head only when the source predates
`judgment_ledger`; the vault itself is opened through the migration-aware
factory only by the two commands that write to it (`review`, `import-links`).

## Commands for the owner

All commands read your vault; only `review` (arm (a) verdicts) and
`import-links` write to it. Use the same `--run` directory throughout.

1. **Data check.** The run needs about 40 graded wrong answers across topics.

   ```bash
   uv run learnloop diagnose data-check --vault <vault>
   ```

2. **Dry-run cost estimate** (no copy, no client, no calls):

   ```bash
   uv run learnloop diagnose run --vault <vault> --dry-run
   ```

   Arm (c) needs `embedding.enabled = true` and `OPENROUTER_API_KEY`
   (qwen/qwen3-embedding-8b, about a cent); without them it is skipped and
   the report says so. Arm (e) needs the `diagnosis` route on the Codex SDK
   (the default). For a stronger judge, set `[ai.routing] diagnosis_judge`
   to a higher-effort profile.

3. **The real run** (resumable; Ctrl-C stops before the next request):

   ```bash
   uv run learnloop diagnose run --vault <vault> --run-dir <vault>/.learnloop/diagnose-runs/m1
   ```

4. **The report** (aggregates only):

   ```bash
   uv run learnloop diagnose report --run <vault>/.learnloop/diagnose-runs/m1 --vault <vault> \
     --out docs/reviews/slice-1-m1-report.md
   ```

5. **Optional spot-check** (~10 items, under 15 minutes; Enter skips, q
   saves and quits, rerun to resume), then rerun step 4 to include it:

   ```bash
   uv run learnloop diagnose review --run <vault>/.learnloop/diagnose-runs/m1 --vault <vault>
   ```

6. **Import the pattern-link verdicts** into `judgment_ledger` (the first
   `same_cause` rows for Slice 2 T1):

   ```bash
   uv run learnloop diagnose import-links --run <vault>/.learnloop/diagnose-runs/m1 --vault <vault> --dry-run
   uv run learnloop diagnose import-links --run <vault>/.learnloop/diagnose-runs/m1 --vault <vault>
   ```

## History mode decision (owner, after the report)

Default **`full`** (O16). Record the chosen mode here after reviewing the
report; M2's prompt reads it from this section.

## Open questions

1. **Codex SDK sandbox parameters.** The read-only workspace passes
   `sandbox="read-only"` and `approval_policy="never"` to `thread_start`
   (app-server protocol v2 names). The SDK is not installed in this
   environment, so this was tested against a fake SDK only. If the installed
   SDK names them differently, arm (e) fails closed (`CodexUnavailable`) and
   the report shows it; a one-line fix in `_read_only_sandbox_options`.
2. **Judge strength.** The judge defaults to the active provider. Should M1
   pin `diagnosis_judge` to a higher-effort profile than the diagnoser, so
   the judge is not the same model judging itself?
3. **Arm (a) adjudications.** Is writing spot-check taps on arm (a) into
   `diagnosis_adjudications` (as the spec says) still wanted, given that an
   affirming verdict can later promote a durable belief through the
   normalization sweep, exactly as `learnloop diagnosis adjudicate` can?
4. **Subscription spend.** Reconcile `offline_review/spend.py` with the
   shared `ai/spend.py` subscription rule when `integrate/slice-a-2-3`
   merges.
