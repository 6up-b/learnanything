# "Write what you can" replaces "I don't know" (stage `practice-stuck-prompt`)

Branch `practice/stuck-prompt`, worktree `learnanything-stuck`, created by the
workflow from `main` at `22023ab4` (Slice 1 M2 merged, migration head 170).
The prompt's own branch instruction is overridden: the worktree already
exists.

Read first: `CLAUDE.md`; `implementation_handoffs.md` §0 and §4 ("Write what
you can" replaces "I don't know"); architecture `Home.md`; the
algorithm-change playbook; `spec_blind_grading_diagnosis_split_v1.md` (§3-§5,
§6.2, §11); `spec_learner_field_v1.md` §3, §3.1, §5.2; the frictionless
defaults (P7); `docs/reviews/slice-1-m2.md`.

## Plan (written before coding)

### What changes for the learner

- Wherever "I don't know" exists today (practice screen `^d`, diagnostic
  probes on the practice screen and in the dialogue block, the golden-path
  triage option, the TUI `ctrl+d`), the control becomes **"I'm stuck"**. One
  tap puts the answer box into stuck mode with the prompt **"Write what you
  can, or what's confusing you"** and focuses it. No extra screen; the same
  Submit sends it, and an empty box may be sent.
- **Non-empty:** an ordinary attempt of the surface's attempt type, graded by
  the grader (blind in split vaults) at the standard attempt mass, and
  diagnosed by the diagnoser exactly like any other blind-graded attempt.
- **Empty:** an ordinary attempt with an empty answer, scored 0 by a
  deterministic grade (no model call), at the standard attempt mass. The
  learner is routed to feedback, which shows the answer, as `dont_know` does.

### Files

New:

- `src/learnloop/attempts/stuck.py` (leaf module): the prompt text, the
  activity gate `stuck_prompt_active(vault)` (algorithm version + kill
  switch), the grader's `StuckReading` wire model and prompt rules, quote
  verification, and the read-back helper `stuck_answers(connection)` (stuck
  attempts with their text and current grader marker) for the later
  learner-text-gaps stage and the owner report.
- `migrations/172_stuck_prompt.sql` (see Migration).
- Tests: `tests/test_stuck_prompt.py` (domain, sidecar, TUI, CLI,
  signal, replay, kill switch), `tests/test_mvp011_upgrade.py`, vitest cases
  in `PracticeScreen`, `DialogueProbe` and `GoldenPathScreen` tests.

Changed:

- `algorithm_versions.py`: `STUCK_PROMPT_ALGORITHM_VERSION = "mvp-0.11"`,
  in the split and P0-successor sets (the split stays live).
- `attempts/attempts.py`: `AttemptDraft.declared_stuck`; the empty-stuck
  deterministic grade (all criteria 0, the deterministic retrieval/scaffold
  attribution today's `dont_know` writes, `grading_source = "deterministic"`,
  grader tier 2 "heuristic auto-grade", so the deferred self-grade regrade
  never picks it up); every completion door takes it before any provider
  check; `declared_stuck` in the attempt record and in replay; no
  `blank_answer` manual review for a declared-stuck empty answer.
- `attempts/blind_grading.py`, `attempts/grading_support.py`: the blind
  context gains an optional `answer_prompt` (absent for ordinary attempts, so
  their prompt, hash and identity are byte-identical); with it the wire model
  adds `stuck_reading` and the prompt version gains a `+stuck-v1` suffix.
  The validated reading is stored on the blind record as `stuck_reading`.
- `attempts/regrade.py`: a regrade of a stuck attempt re-asks the reading.
- `learner/recall_coverage.py`: response engagement is 1.0 for a declared
  stuck answer (a deliberate empty answer is not an accidental blank, which
  keeps 0.5); `field/outcomes.py` passes the flag.
- `diagnosis/probe_episodes.py`: an empty stuck probe answer classifies as
  `unanswered`, as `dont_know` does (nothing was answered).
- `diagnosis/split/context.py`: the current attempt's blind grade shows the
  diagnoser the stuck reading when there is one (absent otherwise, so other
  contexts hash identically).
- `field/signals.py`: a `stuck_confusion` `SignalRow` per stuck answer whose
  current blind grade marks confusion (the item's LO, mass 0, outcome none),
  read by `load_interaction_signals`; `stuck_confusion` joins
  `FAST_TRACK_BLOCKING_TYPES`, so Phase 6's fast-track check sees it through
  `blocks_fast_track` without depending on Phase 6.
- `db/repositories.py`: insert and decode `declared_stuck`; the clarification
  rate counts model-graded tiers (3+) only.
- `config/schema.py` (`[stuck_prompt] enabled = true`, the kill switch),
  `config/template.py` (defaults snapshots: both existing ones recomputed,
  `mvp-0.11` added), `ops/vault_upgrade.py` + `cli/app.py`
  (`learnloop upgrade --to mvp-0.11`, from `mvp-0.10` only).
- Sidecar: `submit_attempt` takes `declared_stuck`; `submit_dont_know` in an
  active vault records an empty stuck answer instead (no new `dont_know`
  rows); a stuck submission arriving after the switch was turned off is
  recorded exactly as today (empty: `dont_know`; text: an ordinary attempt);
  the config DTO carries `practice.stuck_prompt`.
- TUI practice screen (`ctrl+d` = "I'm stuck"), CLI `learnloop attempt
  --stuck` (and `--attempt-type dont_know` becomes an empty stuck answer in an
  active vault).
- Frontend: `algoConfig` reads the flag; `PracticeScreen`, `DialogueProbe`,
  `GoldenPathScreen` (triage label); `client.ts`/`dto.ts`.
- Head fixture `migration_head_170` -> `migration_head_172`, its README and
  the five references; DB reference regenerated.

### Migration

`172_stuck_prompt.sql`: `practice_attempts.declared_stuck INTEGER NOT NULL
DEFAULT 0 CHECK (declared_stuck IN (0, 1))`. `practice_attempts` is already a
RAW_LEDGER; no new table. 171 is reserved by mobile M1 (prompt note), so this
takes 172; expect a renumber at integration.

### Algorithm successor and kill switch

- `mvp-0.11` (`STUCK_PROMPT_ALGORITHM_VERSION`), immediate successor of
  `mvp-0.10`; projection semantics inherited (P0 successor), the split stays
  live. `learnloop upgrade --to mvp-0.11` refuses jumps, freezes the
  manifest and prepares the projection before the atomic config rename, like
  `mvp-0.10`. Expect a relabel at merge (Phase 6 and Slice 2 T1 also ship
  successors).
- Kill switch `stuck_prompt.enabled` (default true): off, an `mvp-0.11`
  vault shows "I don't know" and records `dont_know` at the configured mass
  exactly as `mvp-0.10` does. Below `mvp-0.11` the switch is dormant.
- Replay never reads the switch: whether an attempt was stuck is the
  persisted `declared_stuck` column, and its grader marker is in its blind
  record. Historical `dont_know` rows are untouched and replay at the
  configured mass.

### Spend caps and model routes

No new paid component and no new route: a stuck answer is graded by
`ai.routing.grading` (the blind grader) and diagnosed by `ai.routing.diagnosis`
under the existing caps (`diagnosis.max_calls_per_day`). The empty path makes
no call. Live verification runs on `fixtures-local/` copies, Codex on the
owner's subscription (`estimated_only`).

### `judgment_ledger` writes

None new. The grader's stuck reading is part of the blind grade (a
measurement record), not a verdict between two records.

### Tests

Partial answer graded and diagnosed; confusion text marked and turned into a
signal (blocks fast-track, mass 0); empty answer scores 0 with no model call
(also with no provider); kill-switch parity (`dont_know` exactly as
`mvp-0.10`); replay of historical `dont_know` rows unchanged and a stuck
vault's rebuild a fixed point; upgrade refusals; frontend control on each
screen.

## As built

Commits on `practice/stuck-prompt` (from `22023ab4`): `f3e0407f` (the
control, the successor, migration 172, the grader reading, the signal, every
surface, tests, head fixture 172), `886abdd5` (DB and config reference
regenerated), plus this review.

### What the learner sees

- **Practice screen (desktop).** In an `mvp-0.11` vault the `^d` key and a
  new visible "I'm stuck" button next to Submit replace "don't know" (the key
  bar says "I'm stuck"). One tap keeps the same answer box, changes its
  placeholder to "Write what you can, or what's confusing you", focuses it and
  shows a one-line banner ("An empty answer is fine: Submit takes you to the
  feedback"; inside a diagnostic check, where feedback is deferred, only "An
  empty answer is fine."). "never mind" leaves stuck mode before sending.
  Submit sends what is there, empty or not, with `declaredStuck: true`; an
  empty stuck answer never asks for a self-grade, even when no grader is
  ready. Teach-back items have no control, as before.
- **Diagnostic probes.** On the practice screen's probe mode the same control
  records a `diagnostic_probe` attempt on the committed presentation. In the
  dialogue block (`DialogueProbe`) "Don't know" becomes "I'm stuck": one tap
  switches the textarea's prompt and lets "Commit answer" send an empty box.
- **Golden path.** Its only "I don't know" is the triage report option "I
  didn't know / left it blank"; in an `mvp-0.11` vault it reads "I was stuck /
  left it blank". Its value stays failure triage's coarse class `dont_know`
  (a report about an attempt, not an answer; triage routing is unchanged).
- **TUI.** `ctrl+d` shows the stuck prompt above the answer box (nothing is
  recorded); submit with an empty box records the empty stuck answer and
  returns to Today, as `ctrl+d` did; with text it opens the feedback screen,
  which grades it.
- **CLI.** `learnloop attempt <item> --stuck [--answer ...]`; in an active
  vault `--attempt-type dont_know` is recorded as an empty stuck answer and
  says so.
- The flag reaches the desktop through the app snapshot
  (`config.practice.stuckPrompt`, read by `algoConfig`); the sidecar decides.

### What is recorded

- **A stuck answer with text** is an ordinary attempt of the surface's
  attempt type (`independent_attempt`/`hinted_attempt`/`open_text`/...,
  `diagnostic_probe` in a check) with `practice_attempts.declared_stuck = 1`.
  In a split vault it is graded by the blind grader through the same door:
  the blind context gains `answer_prompt` (the control and the prompt), the
  task gains the stuck rules (grade it as an answer; confusion text earns no
  points; admitting confusion is not itself an error; do not call it a
  retrieval failure just because the learner is stuck), the wire model adds
  `stuck_reading` LAST (`attempts_answer`, `describes_confusion`,
  `confusion_quote`), and the prompt version gains `+stuck-v1`
  (`mvp-2.1-blind-reference-policy+stuck-v1`). The calibration identity stays
  the base grader's (the scoring rules are the same). The validated reading
  (quote kept only when it is verbatim, whitespace and case aside) is stored
  on the blind record under `stuck_reading`. Standard attempt mass; the
  diagnoser runs as for any non-pass blind grade, and its context shows the
  reading in the current attempt's blind grade (absent for every other
  attempt, so their contexts hash as before). A regrade re-asks the reading.
- **An empty stuck answer** is the same ordinary attempt type with an empty
  answer, scored 0 by `complete_empty_stuck_attempt`: every criterion 0,
  `grading_source = "deterministic"`, grader tier 2 ("heuristic auto-grade",
  so the deferred self-grade regrade never sends it to a model), no manual
  review, and the deterministic attribution `dont_know` writes
  (`retrieval_failure`, `scaffold_failure` after hints). Every completion
  door (required, fallback, self-graded) takes it before any provider check.
  Coverage engagement is 1.0 (a deliberate empty answer, not an accidental
  blank, which keeps 0.5). In a diagnostic check it is the `unanswered`
  observation, as `dont_know` was. It is never diagnosed (nothing to read).
- **No separate weight.** The attempt type's own mass applies (1.0 for
  `independent_attempt` on a first answer versus `dont_know`'s 0.7), with the
  ordinary familiarity and assistance discounts on later answers, exactly as
  for any answer. `dont_know`'s exemptions from those discounts are not
  carried over.
- **The confusion signal.** `field.signals.load_interaction_signals` reads
  `attempts.stuck.stuck_answers(connection)` (stuck attempts with their text
  and the CURRENT blind record's reading) and emits one `SignalRow` per stuck
  answer read as confusion: `signal_type = "stuck_confusion"`, the item's LO
  and subject, `outcome = None`, `effective_mass = 0`, available once the
  reading existed. `stuck_confusion` is in `FAST_TRACK_BLOCKING_TYPES`, so
  `blocks_fast_track` / `confusion_blocks_fast_track` (what Phase 6 uses)
  block fast-track on that LO without this stage depending on Phase 6. It
  carries no mass, so the attempt is not counted twice, and it does not mark
  later attempts "preceded by a question" (report strata unchanged).
- **Easy to read back.** `learnloop.attempts.stuck.stuck_answers(connection)`
  returns, per stuck answer: attempt, item, LO, subject, session, created_at,
  `has_text`, the learner's text, score, blind record id, and the reading
  (`describes_confusion`, verified `confusion_quote`). The learner-text-gaps
  stage can route these to the prerequisite and misconception pipeline as
  they stand.

### Algorithm successor, kill switch, upgrade

- `STUCK_PROMPT_ALGORITHM_VERSION = "mvp-0.11"`, immediate successor of
  `mvp-0.10`, in `P0_SUCCESSOR_VERSIONS` and `DIAGNOSIS_SPLIT_VERSIONS` (the
  split stays live). `learnloop upgrade --to mvp-0.11` (from `mvp-0.10` only)
  freezes the manifest, rebuilds the same projection and rewrites the config
  atomically, like `mvp-0.10`. The template stays at `mvp-0.9`.
- Kill switch `[stuck_prompt] enabled` (default true, left out of the
  decision-only template). Off: the desktop, TUI and CLI show and record "I
  don't know" (`dont_know`, configured mass) exactly as `mvp-0.10`; a stuck
  submission from a surface drawn before the switch flipped is recorded as
  the switch says (empty: `dont_know`; text: an ordinary attempt). On:
  `submit_dont_know` from an old client records an empty stuck answer, so no
  new `dont_know` rows appear.
- Replay never reads the switch or the version for this: `declared_stuck` is
  persisted, the reading is on the blind record, and an `mvp-0.11` vault can
  hold `dont_know`, empty-stuck and graded-stuck attempts side by side.
- Effective-defaults snapshots: `mvp-0.9` and `mvp-0.10` recomputed (the new
  section is in every version's effective defaults, dormant below `mvp-0.11`)
  and `mvp-0.11` added.

### Migration 172

`172_stuck_prompt.sql`: `practice_attempts.declared_stuck INTEGER NOT NULL
DEFAULT 0 CHECK (declared_stuck IN (0, 1))`. No new table
(`practice_attempts` is a RAW_LEDGER). The attempt insert names the column
only when it is set, so a database attached below 172 still records every
ordinary attempt. 171 is left free for mobile M1 (prompt note); the runner
and tests accept the gap. Head fixture `migration_head_170` renamed to
`migration_head_172`, upgraded through 172 only, left in rollback-journal
mode; README and the five references updated; DB reference regenerated and
validated.

## Deviations and decisions

- **The confusion signal type.** It is a new `signal_type`,
  `stuck_confusion`, on the merged `SignalRow` type, read by the merged
  `load_interaction_signals`, and added to the merged fast-track blocking set.
  It is not written to `question_events`: that table is the tutor Q&A ledger,
  read by the outstanding-question queue, question promotion and the
  question-signal mastery likelihood, so a row there would show the learner a
  "question" they never asked and could move mastery. Phase 6 may also edit
  `FAST_TRACK_BLOCKING_TYPES`; a merge conflict there is one line.
- **Joint grading has no reading.** With `diagnosis.split_enabled = false`
  in an `mvp-0.11` vault, a stuck answer is graded by the joint prompt
  unchanged (no `answer_prompt`, no reading), so it writes no confusion
  signal. The empty path and `declared_stuck` work the same either way.
- **The self-grade fallback is unchanged** for a stuck answer with text: if
  the grader is unavailable or times out, the learner self-grades, as for any
  answer, and no reading is recorded.
- **The empty answer keeps `dont_know`'s deterministic attribution**
  (`retrieval_failure` / `scaffold_failure`), so follow-ups, surprise and
  severity keyed on error events behave as for an empty answer today. It does
  not get `dont_know`'s severity bonus or its exemptions.
- **Golden path.** Only the triage wording changes (see above); the cold
  assessment there never had an "I don't know", so it gains no control.
- **Not changed:** Phase 6's "I don't know this" self-report (not in this
  branch), the simulator's `dont_know` modelling, recall-calibration
  scenarios, exam seeding, and the project-understanding `/dk` answer (its own
  store and spec; not listed in the prompt).
- `learnloop field data-check` gained an aggregate `stuck_answers` block (no
  text): total, with text, empty, share with text, graded with a reading,
  describing confusion, and the stuck grading runs' wall times
  (median/p90/max). The `interaction_signals` block counts
  `stuck_confusion_rows`.
- The clarification-rate denominator now counts tiers 3+ (model graded)
  instead of 2+; tier 2 was unused before, so existing counts are unchanged
  and the empty stuck zero is not counted as a grader that could have asked.

## Shadow rebuild (playbook evidence)

Backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of the
worktree's tracked `fixtures/linear_algebra` and `fixtures/probability`
under `fixtures-local/`, each upgraded `mvp-0.8 -> mvp-0.9 -> mvp-0.10`, then
a same-version shadow rebuild and a successor one
(`--set algorithms.algorithm_version=mvp-0.11`):

| Copy | Facet real changes | Mastery real changes | Schedule changes | Successor-only differences |
|---|---|---|---|---|
| `stuck-linear_algebra` (70 attempts) | 2 / 2 | 7 / 7 | 48 / 48 | `algorithm_version` stamps (77 facet and 14 mastery rows changed only by the stamp) and minted surrogate ids |
| `stuck-probability` | 2 / 2 | 1 / 1 | 1 / 1 | `algorithm_version` stamps (17 mastery rows) |

"Real changes" (stamp removed) are identical between the same-version and
the successor rebuilds; they are the first-rebuild calibration settling M2
also reported (same counts on linear algebra). The live database hash was
unchanged by both shadows (`d8cf30d7...` and `33b32473...`). The tracked
fixtures were never written.

## Live runs on a backup copy (paid calls)

`fixtures-local/stuck-linear_algebra` upgraded to `mvp-0.11` (no config
change: the owner's `ai.timeout_seconds = 60`, grading and diagnosis on
`codex_low`, `gpt-5.6-sol`). Three stuck answers through the real sidecar
door (`SidecarContext` + `submit_attempt` with `declaredStuck`), the
post-attempt worker diagnosing in the background, plus one empty stuck answer
from the CLI. The grading call is the ordinary practice door, so there is no
`--dry-run` for it; the diagnoser ran under `diagnosis.max_calls_per_day`.

| Answer | Grading wait (handler wall time) | Score | Reading | Diagnosis |
|---|---|---|---|---|
| Empty (`pi_axiom_associative_recall_03`) | **0.41 s**, no model call | 0, deterministic | none | not needed |
| Partial: coordinate step done, "I'm not sure how to get from coordinates back to the vectors" | **37.1 s** | 2 / 4 | attempts answer, describes confusion, quote verified | done (28 s), read the reading: "explicitly reports being unable to bridge the coordinate result back to the vector equality" |
| Confusion only: "I don't understand what 'transport' means here..." | **28.8 s** | 0 / 4 | describes confusion, no attempt, quote verified | done (34 s) |

Both confusion readings became `stuck_confusion` signals on the right LOs
(`lo_prove_vector_identities_from_scalar_laws`, `lo_what_makes_a_vector_space`),
mass 0, blocking fast-track. `field data-check` on the copy: 4 stuck answers,
2 with text (share 0.5), 2 describing confusion, stuck grading runs 28 s and
36 s by the run clock.

| Calls | Route | Tokens in / out |
|---|---|---|
| 2 blind grading turns (`mvp-2.1-blind-reference-policy+stuck-v1`) | Codex `codex_low` | 33,724 / 3,902 |
| 2 diagnoses (`diagnosis-v1-split`, one turn each, no JSON repair) | Codex `codex_low` | 40,699 / 3,751 |

Cost: Codex on the owner's ChatGPT subscription (`estimated_only`; no
metered spend). No OpenRouter or other metered call was made.

## What the owner should watch

- **The share of stuck answers that contain text**
  (`learnloop field data-check --vault <vault> --json`, `stuck_answers.share_with_text`).
  Low means "I'm stuck" is being used as the old skip; that is allowed, but
  then little reaches the grader and the diagnoser.
- **The grading wait on a stuck answer with text.** It is the ordinary
  synchronous blind grade (P7): 29-37 s on the copy, under the vault's
  `ai.timeout_seconds = 60`; past it the learner is asked to self-grade (M2
  saw 1 timeout in 5). `stuck_answers.grading_wait_seconds` reports the
  median/p90/max of the stuck grading runs. An empty stuck answer is recorded
  at once (0.4 s, no call).
- How often the reading says "describes confusion", and whether those LOs are
  the ones the learner would call confusing (the signal blocks fast-track
  there once Phase 6 lands).

## Test results (gate)

Run on commit `886abdd5` (code identical to this review's commit).

- `uv sync --extra dev`, `uv pip install pypdfium2`: done.
- `uv run lint-imports --no-cache`: **10 kept, 0 broken**.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`: **7300 passed**,
  0 failed (208 s). (A first run before the CLI help snapshot was refreshed
  had 1 failure, `test_recursive_cli_help_matches_snapshot`, for the new
  `--stuck` option and `--to mvp-0.11` text; the snapshot was regenerated.)
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`:
  **79 passed**, 7221 deselected (63 s).
- Frontend (`apps/learnloop-tauri`): `npm install` ok (esbuild's install
  script blocked by npm's allowScripts, as before; builds fine);
  `npm run typecheck` clean; `npm test` **81 passed in 20 files**;
  `npm run frontend:build` ok.
- DB reference: `db_generate_reference.py` then `db_validate_reference.py`:
  `errors: []` (schema head 172, 277 table notes, 584 effective config
  leaves in 34 sections); `validate_vault.py`: passed (1,044 notes).
- Not run: `cargo check` (no Rust change).

## Files touched

- New: `src/learnloop/attempts/stuck.py`, `migrations/172_stuck_prompt.sql`,
  `tests/test_stuck_prompt.py` (20), `tests/test_stuck_prompt_replay.py` (3,
  durability lane), `tests/test_mvp011_upgrade.py` (7),
  `apps/learnloop-tauri/src/components/DialogueProbe.test.tsx` (2),
  `apps/learnloop-tauri/src/screens/GoldenPathScreen.test.tsx` (1).
- Changed, Python: `algorithm_versions.py`; `attempts/attempts.py`,
  `blind_grading.py`, `grading_support.py`, `regrade.py`; `config/schema.py`,
  `config/template.py`; `db/repositories.py`; `diagnosis/probe_episodes.py`,
  `diagnosis/split/context.py`; `field/outcomes.py`, `field/signals.py`;
  `learner/recall_coverage.py`; `ops/vault_upgrade.py`; `cli/app.py`;
  `tui/screens/practice.py` + `practice.tcss`; sidecar `context.py`,
  `handlers/practice.py`.
- Changed, frontend: `api/dto.ts`, `app/algoConfig.ts`,
  `components/DialogueProbe.tsx`, `screens/PracticeScreen.tsx` (+5 vitest
  cases), `screens/GoldenPathScreen.tsx`. No Rust change (the stuck answer
  rides on `submit_attempt`).
- Changed, tests and fixtures: `test_blind_grading_contract.py` (the blind
  context admits `answer_prompt`), `cli_help_snapshot.json` (`attempt`,
  `upgrade`), the head fixture `migration_head_172` and its five references.
- Docs: the DB/config reference (generator gains the `stuck_prompt` section
  and its kill-switch text; Configuration.md and Database.md leaf counts),
  this review.

## Owner-run commands

On a vault (a `fixtures-local/` copy first):

```bash
uv run learnloop rebuild --shadow --set algorithms.algorithm_version=mvp-0.11 --json --vault <vault>  # playbook check (from mvp-0.10)
uv run learnloop upgrade --to mvp-0.11 --vault <vault>        # from mvp-0.10 (mvp-0.9 vaults: --to mvp-0.10 first)
uv run learnloop field data-check --json --vault <vault>      # stuck_answers: share with text, grading wait
uv run learnloop attempt <item> --stuck --answer "..." --vault <vault>   # the CLI door
```

Kill switch: `[stuck_prompt] enabled = false` (restores "I don't know").
The live vaults stay the owner's to upgrade; nothing here touched them.

## Open questions

1. **The empty answer's attribution.** An empty stuck answer still writes
   the deterministic `retrieval_failure` (or `scaffold_failure` after hints)
   error event `dont_know` wrote, which keeps follow-ups and surprise working
   as today. The blind grader is told not to call a stuck answer a retrieval
   failure on its own say-so; should the empty one write no attribution
   instead (score 0, no error event)?
2. **Joint grading.** With `diagnosis.split_enabled = false`, stuck answers
   are graded jointly and get no reading, so no confusion signal. Add the
   reading to the joint prompt too, or accept it for the kill-switched state?
3. **Mixed answers.** A partial answer that also names a confusion is both
   graded and signalled (the first live run). Is that the intended scope of
   "text that describes confusion", or should only text that makes no attempt
   at the answer block fast-track?
4. **Template default.** New vaults still start at `mvp-0.9`; `mvp-0.11` is
   reached by upgrade, like `mvp-0.10`. Move the template when the S1.5 exit
   review moves it to `mvp-0.10`?
5. **Grading wait.** 29-37 s on the copy under the vault's 60 s timeout
   (M2's open question 5 applies here unchanged): raise the vault timeout or
   give blind grading its own deadline?
6. **Errors and misconceptions** (the request that started this run): the
   stuck text and its reading are already readable per attempt
   (`attempts.stuck.stuck_answers`), the diagnoser sees the reading when it
   explains the error, and the learner-text-gaps stage can route the same rows
   to the misconception pipeline. Should that stage also read ordinary
   answers' confusion statements, not only stuck ones?
7. **Renumbering.** Migration 172 leaves 171 to mobile M1; `mvp-0.11` will be
   relabelled if Phase 6 or Slice 2 T1 land a successor first (the label is
   one constant plus the upgrade function, CLI target and snapshot key).
