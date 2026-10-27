# AD guard: scheduler offer receipts and the reachable-reads audit (2026-10-27)

Branch `fix/ad-guard-offer-receipts` from `5c6a0834f`, worktree `learnanything-dl2`. This is an
orchestrator-queued blocker stage; the owner said to proceed with the queue.

**The blocker.** The orchestrator dry-ran `learnloop upgrade --to mvp-0.35` on a backup-API copy of
the owner's `probability` vault (at mvp-0.31), and it failed. The chain was `one_ask_upgrade` →
`replay_ledger_upgrade` → `claim_fixes_upgrade._activate_as_writer` → `rebuild_all_derived_state` →
`rebuild_ad_state` → `replay.load_events` → `MaterialView.field_rows` →
`field.outcomes._serving`. The last step reads `scheduler_offer_receipts`, which the AD guard's
registry had not classified. The guard refused the read, AD's operation was poisoned, and the
failure surfaced as `ViewDenied: ('denied', 'DatabaseError')`.

**Verdict:**

- It was a registry gap, not a design question. `scheduler_offer_receipts` is the incumbent
  scheduler's serving receipt. It is now classified `DENIED`, next to its slate's
  `scheduler_slate_candidates` and `submission_intents`. The rules (the material view's readers) may
  read it; nothing else inside an operation may.
- The guard is not broadened. An unclassified table is still refused in every scope.
- The audit (§4) found two more latent denials of the same class and fixed both.
- **No successor.** The fix is a bug fix: it restores the behaviour specified since mvp-0.30. On every
  vault without such an attempt the result is row-identical (§5).
- All three owner copies now upgrade to mvp-0.35, rebuild, report and pass doctor (§6).

## 1. Reproduction

**Owner copy.** I made a fresh `copy_tree_with_databases` copy of
`fixtures-local/owner-copies-20261027/probability` and ran `upgrade --to mvp-0.35` on base code. It
failed exactly as the orchestrator logged:

- the warning `AD guard denied read of scheduler_offer_receipts (an unclassified table) by
  learnloop.field.outcomes: AD is unavailable for the rest of
  learnloop.adaptive_difficulty.replay.load_events`;
- `field revision resolution failed`;
- `ViewDenied`, exit code 1.

The upgrade chain is step-atomic, so the failed copy was left at **mvp-0.32**: the chain activated
mvp-0.32 and stopped at the next step. The owner's live vault is untouched and still at mvp-0.31.

**Fail-first tests.** `tests/test_ad_guard_offer_receipts.py` builds the shape with the
`ad23_vault` and `answer` builders: a graded attempt bound to a slate candidate that is not a forced
follow-up, plus its published offer receipt and its submission intent. On base code all four tests
failed:

- `rebuild_all_derived_state` raised `ViewDenied`;
- the view's attempt rows raised;
- the serve's `replay.snapshot` and `ad report`'s `build` raised;
- the registry assertion failed with `KeyError`.

**What the owner's vault actually holds** (counts only):

| Vault | Attempts | Offer receipts | Attempts reaching the offer read | Serving labels |
|---|---|---|---|---|
| probability | 3 | 0 | 1 | `daily_plan` 1, `unknown` 2 |
| linear_algebra | 70 | 0 | 0 | `unknown` 70 |
| arxiv_v2 | 3 | 0 | 0 | `unknown` 3 |

On probability, one attempt is bound to a non-forced slate candidate. The read finds no offer row,
so the attempt falls through to its plan receipt and is labelled `daily_plan`. The denial still
happens, because SQLite's authorizer judges a statement when it is **prepared**, before any row is
read. So the receipt read does not change a single label on the owner's vault. Only the refusal
mattered.

## 2. Blast radius: what the owner has been getting

**Evidence from the owner's vault.** The probability copy carries the live vault's
`ad_guard_denials.jsonl`. It has 6 lines: 3 operations, each with one `scheduler_offer_receipts`
denial plus one "made unavailable by an earlier denial" line. The file was last written
2026-10-26 14:08 local. The log does not record each operation's entry point. The linear_algebra
and arxiv_v2 copies have no denial log.

**The same commands on a fresh copy, with live code (base `5c6a0834f`, at mvp-0.31):**

| Path | Result on the probability vault |
|---|---|
| `learnloop ad report --json` | Exit 1, `ViewDenied`. The report crashed; it did not just count the denial. |
| `learnloop rebuild-derived-state` | Exit 1, `ViewDenied`. The whole rebuild transaction rolls back, so no derived table is refreshed. |
| AD readiness (`lo_readiness`, the desktop's `adaptive_difficulty.readiness` RPC) | Denied for 18 of 18 LOs. The sidecar handler turns a denial into "not predicted", so the desktop showed no readiness line for any probability LO. |
| The serve's replay snapshot (`replay.snapshot`) | Denied. |
| `learnloop doctor` | Unaffected: no AD operation reads field's rows. |
| Desktop open | Not hit at open itself: a first open schedules no AD work, and the revision preparation reads no field rows. |

The snapshot denial reaches every path that calls `snapshot`:

- the plan's AD slot (`serving`);
- the Reader's dose offer (`dose.decide`);
- commissioning (`generation`);
- readiness.

AD1's in-process forecast receipts at a plan serve (`forecasters._challenger`) also read
`view.field_rows`. Each of these paths fails closed: AD is unavailable for that operation, and the
incumbent serves or nothing is offered. Nothing is shown in the UI.

**What the owner got:** on the probability vault, AD has been **silently unavailable since its
attempt bound to a slate candidate existed**, from mvp-0.30 on:

- no AD draws;
- no readiness lines;
- no dose offers;
- no AD1 forecast receipts at serve;
- a crashing `ad report` and `rebuild-derived-state`.

The incumbent served every plan slot, as it does with the kill switch off. A poisoned operation
writes nothing, so no AD row was persisted under the denial and no history needs reinterpreting.
The vault's stored `ad_state` and `ad_attempt_trace` are stale: 3 trace rows, against the 4 a rebuild
now writes. linear_algebra and arxiv_v2 were never affected.

## 3. The fix

`src/learnloop/adaptive_difficulty/protected_tables.py`, `ROLES` now has
`("scheduler_offer_receipts", DENIED)`, with a comment saying why:

- It is the scheduler's published offer: which of a slate's candidates the learner was shown.
- Field's serving attribution reads it, inside the rules, only to label an attempt picked from that
  offer `learner_pick`.
- Like its slate's candidates, it is the incumbent's serving state, derived from incumbent state
  that includes protected answers.

`DENIED` is the only role consistent with its neighbours:

- **Why not `NEUTRAL`:** that would allow raw reads of its metadata anywhere inside an operation,
  which broadens the guard.
- **Why not `PROTECTED`:** that needs a reference kind the material view can resolve, and a
  candidate-id list has none.

The rules use the row for one thing only: whether the visible attempt's own candidate is in the
offer list. That is a boolean about a visible attempt, so nothing protected is handed out.

`column_classes.py` classifies the columns:

- **metadata:** `slate_id`, `returned_candidate_ids_json` (a JSON list of ids), `collection_version`,
  `created_at`;
- **content:** `entry_surface`, classified as `submission_intents.entry_surface` is.

**Alternative considered and rejected: don't read the receipt inside AD's scope.** Field's
`_serving` would then label a learner pick differently inside AD than outside (`daily_plan` or
`unknown` instead of `learner_pick`). AD's comparators and its report would read a different history
from field's, and that divergence is exactly what the view is meant to avoid.
`test_the_view_labels_the_pick_as_field_does_outside_ad` pins that the labels are the same inside
and outside.

## 4. Audit: every table reachable code can read inside an operation

**`tests/ad_reachable_reads.py`.** A profiler (`sys.setprofile` and `threading.setprofile`) records
every `learnloop` function that is called while an AD operation is open, and whether it ever ran
outside the rules' scopes. A static scan of each recorded function then names every table it can
read **on any branch**, including branches the run never took. A table counts as named when:

- it follows `FROM` or `JOIN` in one of the function's string constants (nested lambdas and closures
  included);
- a constant is exactly a table name (a composed statement);
- the function names a module-level string that is a table name.

Module and class bodies are skipped: importing a module inside an operation defines all its
functions, whether or not they are ever called.

**`tests/test_ad_guard_reachable_reads.py`:**

- **Static check, over two runs:** AD's whole contract pipeline (the `test_ad23_contract` harness,
  every entry point) and a vault that takes **every branch of field's serving attribution**. The
  branches are: pick from a published offer, candidate with no published offer, forced follow-up,
  system probe, plan serve, legacy unversioned.
  - Every table named by reached code must be classified.
  - Outside the rules, a named non-neutral table that AD does not own must be in a reviewed list
    (`UNRULED_REVIEWED`), each entry with its reason:
    - two carve-outs, AD1's `mastery_ekf` comparator: `Repository.mastery_states` and
      `Repository.item_parameter_states`;
    - two incumbent branches that AD bypasses by passing the view's rows:
      `daily_plan.estimates.load_duration_evidence` and `_feedback_dwell`.
  - A reviewed function that no longer runs there fails the test too, so the list cannot go stale
    silently.
- **Negative controls:**
  - On the contract pipeline alone, whose vault never takes the learner-pick branch, the scan
    still names `scheduler_offer_receipts` through `field.outcomes:_serving`. The scan would have
    caught this table in CI before the owner's vault did.
  - With the table taken out of `ROLES`, the scan reports it.
  - The scan's own rules have a fixture test.
- **Dynamic check:** over the every-branch vault, the replayer (through `rebuild_all_derived_state`),
  the serve's snapshot, the prequential arms and the report all run with zero denials. The view's
  labels equal field's, and all five labels occur.

**The audit found two more latent denials of the same class.** Neither is present in an owner copy
today: all 353 interpretations across the three copies have a persisted LCB.

1. **`grader_calibration_alphas` (unclassified).** Field's effective observations read a grader
   model's pooled alphas for an interpretation recorded before its shared certainty LCB was
   persisted (`shared_certainty_lcb` NULL). That read is
   `Repository.calibration_alphas_by_model_ids`, reached inside the rules through `field_rows`. A
   fail-first test (`test_a_legacy_grade_interpretation_reads_its_pooled_alphas_with_zero_denials`)
   gave the same `ViewDenied` on base code.
   - **Fix:** classified `NEUTRAL`, with every column metadata. These are the model's own immutable
     numbers, and the model row is already `NEUTRAL` with its reliability bins and counts as
     metadata.
2. **The replay's measurement masses, resolved outside the rules.** `replay.load_events` called
   `field.outcomes.measurement_masses` directly, outside the view. For the same legacy
   interpretation that call reads `raw_grade_events` (by id) and `fitted_parameters` (the grader
   channel prior). Both are `DENIED`, so the read was refused (`access to fitted_parameters.id is
   prohibited`).
   - **Fix:** the masses now resolve through a new view reader, `MaterialView.measurement_masses`,
     inside the rules. It applies the same function to the same visible ledger entries, the same way
     `field_rows` already resolves these references.
   - **Negative control:** with the old call restored, both the dynamic test and the static scan
     fail (`raw_grade_events` via `Repository.raw_grade_events_by_ids`).

After the fixes, the scan over 988 reached functions (747 that ran outside the rules) finds no
unclassified table and no unreviewed raw read.

## 5. Successor decision: none

The playbook asks whether persisted meaning changes. It does not:

- **The specified behaviour.** Since mvp-0.30 (AD23), AD reads field's rows through the view, and
  an operation that does so runs with zero denials. That is AD23's contract test. A refusal caused
  by an incomplete registry is a defect, and the incumbent-serves fallback is the failure mode, not
  a specified state.
  - Labels, masses, the replay and AD state mean what they meant.
  - No default, fingerprint, schema or migration changes.
  - The upgrade chain is untouched and stays linear.
- **Row-identical where nothing was denied.** The change only authorizes statements that were
  refused before. The moved masses are the same function over the same entries. So any operation
  that ran with zero denials runs identically. On copies of the two unaffected owner vaults I ran
  upgrade to mvp-0.35 and `rebuild-derived-state`, once on base code and once on this branch, and
  digested every `DERIVED` table (counts and row hashes, timestamps excluded):
  - linear_algebra: 23 tables, 1,773 rows, identical. `ad_state` 9 rows and `ad_attempt_trace` 90
    rows, same hashes.
  - arxiv_v2: 23 tables, 4,662 rows, identical.
  - `subject_identifiability_watermarks` differs only in its `checked_at` timestamp.
- **No golden projection moves.** `fixtures/migration_head_224` is at mvp-0.6, below AD, and the
  AD contract and rebuild-orchestrator tests pass unchanged.
- **The affected vault gains the specified behaviour.** On probability, serving changes because AD
  becomes available. No AD row was ever written under the denial, so there is no recorded history
  for the new behaviour to contradict. `adaptive_difficulty.enabled` remains the kill switch.

## 6. Proof on fresh copies of all three owner copies

Each run started from a new `copy_tree_with_databases` copy, under `env -i` with existing empty
`HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` and AI routes off. The sequence was:

1. `upgrade --to mvp-0.35`
2. `rebuild-derived-state --json`
3. `ad report --json --no-sensitivity`
4. `doctor --json`

No model call and no spend.

| | linear_algebra | arxiv_v2 | probability |
|---|---|---|---|
| upgrade (mvp-0.31 → mvp-0.35) | exit 0 | exit 0 | exit 0 (base: exit 1, left at mvp-0.32) |
| rebuild | exit 0: 70 attempts replayed, 8 LOs | exit 0: 3 attempts, 3 LOs | exit 0: 3 attempts, 1 LO |
| `ad report` | exit 0: `guard.denials` 0. Inputs: 70 attempts, 28 eligible, 62 `reconstructed_current`. Field coverage `mastery_ekf` 28, `lo_general` 28 | exit 0: denials 0. 3 attempts, 0 eligible | exit 0. 3 attempts, 1 eligible. Inputs 1 `exact` + 2 `reconstructed_current`, 182 opportunities. Field coverage 1 and 1 |
| new guard denials (log lines before → after) | 0 → 0 | 0 → 0 | **6 → 6 (no new denial)** |
| doctor errors | 1: `layout:missing_directory` | 47: `criterion:unknown_dependency` 46, `layout:missing_directory` 1 | 48: `criterion:unknown_dependency` 46, `yaml:invalid` 2 |
| WAL after | `-wal` 0 bytes | `-wal` 0 bytes | `-wal` 0 bytes |
| `ad_state` / `ad_attempt_trace` rows | 9 / 90 | 1 / 0 | 2 / 4 |

The probability report's `guard.denials` reads **6**. These are the copy's 6 historical lines from
the live vault, not new denials: the count is cumulative over the log file, and no line was added.
Doctor's error codes are only the known content ones.

## 7. Gate (this stage; the full suite runs once at landing)

- `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`.
- `uv run lint-imports --no-cache`: 36 contracts kept, 0 broken.
- Targeted pytest in a 5G memory-capped scope, `-n 6`. The run and its file list are in §8.
- No migration, schema, frontend or Tauri change, so no durability lane, DB reference regeneration,
  vitest or cargo run.

## 8. Targeted test files

New:

- `tests/test_ad_guard_offer_receipts.py`
- `tests/test_ad_guard_reachable_reads.py`
- `tests/ad_reachable_reads.py` (helper)

Existing, covering the changed modules (`protected_tables`, `column_classes`, `material_view`,
`replay`, `field.outcomes`) and the contract tests:

- every `tests/test_ad*.py`;
- `tests/test_answer_signal_arms.py`, `tests/test_daily_plan_composition.py`,
  `tests/test_daily_plan_owner_decisions.py`;
- `tests/test_facet_outcome_view.py`, `tests/test_family_memory_projection.py`,
  `tests/test_field_split_outcomes.py`, `tests/test_field_workbench_signals.py`;
- `tests/test_held_grade_composition.py`, `tests/test_held_grade_evidence.py`,
  `tests/test_integration_daily_loop_field.py`;
- `tests/test_pfc_unassessed_readers.py`, `tests/test_pfc_unverified_unassessed.py`;
- `tests/test_reading_hardening_landing.py`, `tests/test_rebuild_orchestrator.py`,
  `tests/test_salience_firewall.py`, `tests/test_section_coverage_migration.py`;
- `tests/test_stuck_prompt.py`, `tests/test_stuck_prompt_replay.py`;
- `tests/test_architecture.py`, `tests/test_table_roles.py`;
- `tests/test_observation_ledger_bulk.py`, `tests/test_effective_observation.py`.

## 9. Open items for the owner

- **The probability vault's denial log.** It keeps its historical lines, and `ad report` counts the
  log cumulatively, so after the upgrade the report says 6 or more denials that predate the fix.
  Should the log be archived at upgrade? This stage leaves it alone: it is the owner's file.
- **The log has no entry point.** It does not record which operation was denied, so the 3 owner-side
  operations cannot be attributed. Recording `op.guard.entry` in each line is a small follow-up, not
  done here.
