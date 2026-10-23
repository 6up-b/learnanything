# Regrade contracts (mvp-0.26): every regrade cites its contract, replay reads the current grading epoch

**Stage:** `regrade-contract-replay`, queued by the orchestrator on 2026-10-16 after two stages found the defect separately (UX Phase 4's Codex review §8.4, and the saved-forecasts stage). The owner was told.
**Branch:** `fix/regrade-contract-replay`, from main `311de408e` (mvp-0.25, migrations to 206).
**Commits:** `8e5292189` (code and tests), `ba8709f00` (playbook, architecture vault, regenerated references), `7940dbd36` (the upgrade replays only learning objects the vault still holds), then this record.
**Successor:** `mvp-0.26` (`REGRADE_CONTRACT_ALGORITHM_VERSION`), the next link after mvp-0.25. No migration (207 stays free), no config key, no RPC, no frontend change.
**Paid calls:** none. Every test uses fakes. The parity runs replay backup-API copies with an empty config directory, so no model could be reached.

## 1. The cause

Reproduced first, with fakes, in a split vault at the latest version: `pi_svd_compute_001` (criteria `setup` 2 + `result` 2), its `result` raised to 6 points (maximum 8) and later lowered. `tests/test_regrade_contract_replay.py` holds the five reproductions. It imports only names that exist on main, so the same file runs against main's code (a `git archive` of `311de408e`), where all five fail (`fixtures-local/regrade-contract/failfirst-main.log`):

| Case | On main | After |
|---|---|---|
| 1. A model grade (2/4, tier 3, citing its contract) regraded above its original maximum (6: 2 + 4) | `IntegrityError: CHECK constraint failed: correctness … <= 1.0`; the regrade transaction rolls back | saved: 6/8 = 0.75, now and after a rebuild |
| 1. The same from the feedback screen's "I think I was right" | `contest.regraded` is false (the grader "couldn't look again") | `regraded` is true; 6, 0.75 |
| 2. The same original regraded within its original maximum (3: 1 + 2) | commits, but replay records 3/4 = 0.75 | 3/8 = 0.375, as the regrade wrote it, now and after a rebuild |
| 3. A self-grade regraded to 6/8, then `result` lowered to 2 (maximum 4) | `rebuild_all_derived_state` fails the CHECK (6/4); so does every later regrade on the learning object | the rebuild succeeds and keeps 6/8; a later regrade of a sibling answer saves |
| 3. The same, `result` lowered to 4 (maximum 6) | the rebuild silently rescores 0.75 to 1.0 | 0.75 stands |

**Why.** Four things combined:

1. **The writer.** An ordinary regrade (`attempts/regrade.py`) read the item as it is now but cited no assessment contract and stamped no grading revision. Only a method-explicit regrade cited its frozen contract.
2. **Partial supersession.** An ordinary regrade superseded only the self-grade tier (1). The original model rows (tier 3) stayed live beside the regrade's, so the ledger held two current grades of one attempt.
3. **Replay.** `replay_existing_attempt` took the contract from the first live row that cited one: the original's. The regrade's points were divided by the original's maximum (case 1: 6/4; case 2: 3/4). With no live row citing a contract (case 3), replay read the item at replay time, so a later rubric edit rescored the regrade or failed the CHECK.
4. **The other folds** had the same choice made separately. The canonical projection resolved a contract only when the live rows cited exactly one, ignoring the uncited ones, so it read the regrade's points against the original's contract and clamped the fraction. The grade dual-write classified every replayed grade out of the item's maximum now. The feedback screen and the facet evidence timeline each ordered epochs their own way.

## 2. Decisions

### 2.1 An ordinary regrade supersedes every live row, the model tier included

At mvp-0.26 a regrade supersedes every live row of the attempt (tiers 0 to 4), whatever the tier of the grade it replaces. So does an adjudication's evidence revision (it already did).

- **Why.** The attempt row has one grade: the regrade writes its `rubric_score` and `correctness`. With the original's model rows left live, the ledger said two grades at once: feedback showed every criterion twice (UX usability round 1, M-b), adjudication mixed contracts, forecasts censored the observation (`graded_contract_unknown`), and replay picked a contract by row order.
- **Nothing is lost.** Supersession never deletes. The original's rows stay in the ledger with `superseded_by_evidence_id` pointing at the regrade. The regrade history, feedback's previous epoch and the facet timeline still read them.
- **Below mvp-0.26** the regrade supersedes as before: tier 1, or (1, 3) for teach-back, a clarification, or a regrade into or out of a hold.

### 2.2 Grading epochs: identity, sequence, the current epoch

`src/learnloop/grading_epochs.py` is now the one definition. It is a leaf of pure functions over evidence rows.

- **Identity.** An epoch is the rows one writer wrote together: `revision:N` when they carry a `grading_revision`, else `legacy:<created_at>`. This is how every reader already grouped them.
- **The sequence.** At mvp-0.26 every new epoch stamps the attempt's next revision (`next_grading_revision`). A first grade takes 0, as before. A regrade or an adjudication takes one more than the greatest revision any row of the attempt carries, superseded rows included, and never less than 1. The number is read and written inside the grading's own `BEGIN IMMEDIATE` transaction, so two epochs of one attempt never share it. For an adjudication, that transaction also covers its reads of the current epoch and its contract (fixed after the Codex review, F2; see [the review record](regrade-contract-replay-codex-review.md)).
- **The current epoch** (`current_epoch`) is chosen among the live rows. Timestamps are never compared to decide it, and no content first-seen stamp is ever used:
  - **One live epoch:** that epoch. Every epoch written at mvp-0.26 is the attempt's only live one, because it supersedes every live row.
  - **Several live epochs** (only rows written before the tag): a revision-less epoch wins over a revisioned one. Every writer that stamped a revision either came first (the first grade, revision 0) or superseded every live row (an adjudication), so a revision-less epoch still live beside one is a later regrade. Among several revision-less epochs, the latest by its last row's `(created_at, id)` wins; ids are unique, so this cannot tie. Among revisioned ones, the greatest revision wins.
- **The written order** of all epochs, superseded ones included (`ordered_epochs`, for display), puts the current epoch last. The earlier ones follow their last row's `(created_at, revision, id)`.
- **An epoch's contract** (`epoch_contract_version_id`) is the one version every row of the epoch cites. An epoch whose rows cite none, several, or not all the same one has no contract on record.

Every reader I changed uses this module: replay, the canonical projection, the facet evidence timeline, the adjudication revision, feedback's epochs and the held-regrade display.

### 2.3 What a regrade cites

In its publication transaction, before its rows are written, a regrade at mvp-0.26 cites one of two contracts:

- **A method-explicit answer** (`regrade_reads_contract`): the frozen contract it read the statement, rubric and method from, as before.
- **Every other answer:** `snapshot_for_presentation` of the item it read, with the rubric it graded under (`attempts.snapshot_graded_contract`). The snapshot is content-addressed, so an unchanged item reuses its version, and a failed publication leaves no version behind (`test_the_regrade_snapshot_is_written_in_the_regrade_transaction`).

Every row of the regrade carries that contract and the revision. The attempt's correctness is `score / rubric.max_points` of exactly that rubric, so replay reproduces it. Every regrade door goes through `regrade_attempt` and so cites: the feedback screen's plain regrade, the contest, the deferred self-grade regrades (run at CLI and app startup), and a clarification's resolution. `learnloop probe-regrade` is non-destructive and writes no evidence.

`attempt_graded_contract` (the presentation's contract: the one a method-explicit regrade reads, and what the answer's question is rendered from) now reads only the first grade's rows (revision 0, or a pre-revision row). A later regrade's contract is never taken for the presentation's.

### 2.4 Replay at mvp-0.26, and an epoch with no contract on record

`replay_existing_attempt` reads the current epoch's rows (`attempts.current_epoch_reading`), never all live rows, and replays them under the contract they cite. The canonical projection, the facet evidence timeline and the grade dual-write read the same thing. The dual-write now classifies a grade out of the maximum it was computed against, never the item's maximum now.

When a current epoch cites no contract, replay never divides it by today's item. Clamping is not used anywhere.

- **The attempt's only grade, made before contracts** (a pre-mvp-0.7 first grade: one write. Its rows, superseded ones included, share one epoch key, none is superseded, and they carry at most one grading run. A regrade written in its original's second shares the original's revision-less key. Its supersession or its own run marks it as a second write, so it is held like any later uncited epoch; Codex review F3, `grading_epochs.only_grade`). It keeps the compatibility reading of the item it always had, while its score fits today's maximum; changing that reading would be a `substrate.compat` decision. If its score exceeds today's maximum, it is held as below, instead of failing the rebuild.
- **Every other epoch with no contract** (an ordinary regrade made before the tag, or an adjudication of one) is **held for review**.
  - **It is no evidence.** No criterion is assessed, so there is no FSRS review, no mastery or facet evidence, no error event, no item-quality move, and no surprise direction. This is exactly what a route-rule hold does.
  - **Its correctness** is its score over the maximum recorded with it, where one exists: a blind grade record of the epoch's own run. Otherwise it is the correctness the attempt row already carries, kept and never recomputed (the table's CHECK keeps it in [0, 1]). NULL was rejected: about 30 readers do `float(row["correctness"])`.
  - **The reason.** Replay records `manual_review_reason = grade_contract_unrecorded` on the attempt (`outcome_contract.GRADE_CONTRACT_UNRECORDED`), and the held-grade predicate (`held_grades.held_for_review_attempts`) reads it. Every reader of a held grade therefore treats it as no outcome. Feedback says "held for review". The projection and the timeline bank nothing from it.
  - **Release.** A regrade releases it by citing a contract; its own review reason replaces this one. An adjudication releases it by citing the contract it scales by and clearing the reason. Replay owns the reason: it records it on an unrecorded epoch and clears it once a recorded epoch replaced that grade.
  - **Below mvp-0.26** nothing writes the reason, so no earlier vault holds anything by it.

### 2.5 Adjudication

At mvp-0.26 `append_adjudication_evidence_revision` revises the current epoch:

- **Its contract.** The revision uses the contract the epoch cites. If the epoch cites none, it uses a snapshot of the item whose rubric scales it, taken in the revision's transaction and cited on its rows.
- **Its revision** is the attempt's next revision.
- **Its correctness** is `round(fraction × total) / maximum`, the value replay computes. Before, it wrote the raw fraction, so a fraction that does not land on a whole score (0.3 × 8) was rewritten by the next rebuild (0.3 became 0.25).
- **The hold.** It clears `grade_contract_unrecorded`.

Without the vault, which names the version, it writes as before. Every caller passes it.

### 2.6 No kill switch, no migration

- **No kill switch.** The behavior a switch would restore is the defect: a regrade that cannot be saved, or one that replays against the wrong maximum. Replay never reads a switch anyway; it reads what each epoch recorded. Rolling the version back is restore-only, like mvp-0.18. This is open question Q1.
  **Owner confirmed 2026-10-20:** no kill switch for the mvp-0.26 regrade; rollback = restore the backup.
- **No migration.** Every column the fix needs already exists: `assessment_contract_version_id`, `grading_revision`, `superseded_*`, and `manual_review_reason`. A unique index on `(attempt_id, grading_revision, criterion_id)` was considered and left out: the sequence is assigned in a serialized transaction, and an index added by migration could fail on historical data.

## 3. The successor note (playbook items)

1. **New tag.** `mvp-0.26` (`REGRADE_CONTRACT_ALGORITHM_VERSION`) is appended to `SUCCESSOR_CHAIN`. `REGRADE_CONTRACT_VERSIONS` follows the chain. `LATEST_ALGORITHM_VERSION`, new vaults and the default upgrade target are mvp-0.26. The note is beside the constant in `algorithm_versions.py`.
2. **Raw ledgers immutable.** No evidence row, contract or blind record is rewritten. The hold is a derived reason replay records on the attempt's summary row; replay already rewrote that row's grade columns.
3. **Upgrade.** `learnloop upgrade --to mvp-0.26` (`regrade_contract_upgrade.upgrade_to_mvp026`) accepts mvp-0.25, or mvp-0.9 to mvp-0.24 through mvp-0.25's own chain; chained notes pass through, a refusal's included. Anything older is refused.
   - **One activation across the database and the config** (Codex review F1). Under the vault mutation lock, one `BEGIN IMMEDIATE` transaction covers the predecessor's manifest, the scan (`attempts.unrecorded_epoch_attempts`), the replay of exactly the learning objects holding an attempt it reinterprets, the re-projection (the activation receipt every successor writes), and the registry refresh. Its last step publishes the config: write and fsync a temporary file, rename it atomically over the config, fsync the directory. The commit follows.
   - **Its notes** name the held attempts.
   - **If this step fails** after the chain succeeded, before or at the publication, the transaction rolls back. The vault stays at the valid mvp-0.25, its database exactly as it was.
   - **If anything fails after the rename** (the directory's fsync, or the commit), the config is restored to mvp-0.25 (Codex re-review F4). A failing fsync of the temporary file precedes the rename: the file is removed and the config never changed.
   - **If the process dies** between the publication and the commit, the vault carries the mvp-0.26 label over the untouched mvp-0.25 database. Every successor leaves that transient state until a rebuild, and doctor reports it (`sql:derived_state_rebuild_stale`). Running `learnloop upgrade --to mvp-0.26` again completes the activation ("completed the interrupted activation"), as does any rebuild. The successor's state is never committed under the predecessor's label.
4. **Fingerprint.** The defaults fingerprint for mvp-0.26 is recorded in `DEFAULTS_SNAPSHOT_BY_ALGORITHM`. Only the version string moves it.
5. **Table roles.** No new table.
6. **Replay and rebuild tests.** Listed in §6.
7. **Shadow rebuild.** The upgrade shadow, on the test vault and on the owner copies, is in §4 and §7.
8. **Upgrade path.** On the migration-head fixture and on the owner copies: the upgrade, the FK check, doctor, and a settled rebuild a further rebuild leaves byte-identical (`test_head_fixture_predecessor_to_successor_path`, `test_after_the_upgrade_a_rebuild_settles_and_stays`).

The playbook gains a recorded rule: a grade is replayed against the contract it was graded under, and there is one definition of the current grading epoch.

## 4. What changes for existing data

- **Below mvp-0.26: nothing.** Replay, the projection, the timeline, the dual-write, regrades and adjudications run exactly as before. The predicate change is inert there, because only mvp-0.26 replay writes the reason. On the owner copies, at their own label (mvp-0.8), `rebuild --shadow` is identical between main's code and this branch's (§7).
- **On upgrade (an earlier label to mvp-0.26)**, an existing attempt changes only if its current grading epoch cites no contract:
  - **An ordinary regrade made before the tag, or an adjudication of one, that is still the attempt's grade.** It is held for review: no FSRS review, no mastery or facet evidence, no error events, no item-quality update. Its correctness is the blind record's fraction when that record kept a maximum, else unchanged. `manual_review` becomes 1 with reason `grade_contract_unrecorded`. Its item's schedule and its learning object's mastery are replayed without it. Facet cells it alone supported lose that support.
  - **A first grade made before contracts** keeps its reading, unless its score exceeds its item's maximum now. Before, that case failed every rebuild; now it is held.
  - **Every other attempt** replays as before. Its current epoch cites the contract its first live row did, under the same rows.
  - **Nothing is rewritten in the ledger.**
- **The owner's vaults** (§7):
  - **`linear_algebra`:** 70 attempts. 7 have an ordinary regrade epoch citing no contract. In 6 of them that epoch is superseded (the self-grade was restored over it on 2026-07-22), so they are unaffected. In 1, `01KYCM9NYBGYDKGR2GGYQYSV23`, it is the current grade. That self-graded answer was regraded on 2026-07-25 by a joint grader, which kept no maximum. After the upgrade it is held, at its stored 4 points and 1.0 correctness.
  - **`probability`:** 2 attempts, none affected.
  - **The upgrade shadow on `linear_algebra`** moves exactly 6 rows beyond mvp-0.25's own replay, all on that attempt's item `pi_exercise_01ky5raxvexp8axggqn8e73vkh` and its learning object:
    - **Facet cells:** 2 item-scoped and 1 aggregate cell of the two complex-number facets lose their only support. The other facet's aggregate cell drops from 0.435 to 0.348 independent mass.
    - **Mastery:** `lo_compute_with_complex_numbers` goes from 5 to 4 evidence, logit mean 1.048 to 0.985.
    - **Schedule:** the item's due date moves from 2026-08-23 to 2026-08-05, stability 26.7 to 12.1.
  - **To release it**, regrade it (one model call) or adjudicate it.

## 5. Compositions: everything that reads the grading epoch

| Reader | At mvp-0.26 | Test |
|---|---|---|
| Feedback `answered_source` | A new regrade cites its contract, so its own response and every later load are `contract`. The key, criteria and maximum come from the regrade's snapshot, even after the item changes again; the regrade history reads 4 → 8. `live` remains only below the tag, and `unrecorded` only for epochs written before it (rare; such a current epoch is held). Feedback orders epochs through `grading_epochs`, so its current epoch is replay's. | `test_feedback_reads_a_reopened_regrade_from_the_contract_it_cites`, `test_a_regrade_from_the_screen_is_read_from_its_contract_then_and_later` |
| Forecasts' graded contract (`forecast_report._Ledgers.current_evidence`, `live_report`) | Unchanged code. With the regrade's epoch the only live one and citing its contract, a regraded observation resolves its contract instead of censoring as `graded_contract_unknown` (still the outcome at mvp-0.25). | `test_a_regraded_observation_resolves_its_graded_contract_in_the_forecast_reader[mvp-0.25, mvp-0.26]` |
| Held grades and their release | A route-rule hold released by a successor regrade, under its contract. The unrecorded hold is read by the one predicate and released by a regrade or an adjudication. Its learner state equals a route-rule hold of the same answer. | `test_a_route_rule_hold_is_released_by_a_successor_regrade_under_its_contract`, `test_a_successor_regrade_releases_an_unrecorded_hold`, `test_an_adjudication_releases_an_unrecorded_hold_under_the_contract_it_cites`, `test_a_held_unrecorded_grade_is_no_evidence` |
| The provenance C4 receipt (`record_grading`, writer `regrade`) | Written in the regrade's transaction after its rows. The answer is now pinned to the regrade's contract; at mvp-0.25 two live epochs pinned none. | `test_the_grading_provenance_record_pins_the_contract_the_regrade_read` |
| The claim ledger's grade contests | The contest's regrade above the original maximum now looks again (`regraded` true, 6/8) and goes to review when not upheld. | `test_case1_a_contest_of_a_model_grade_above_its_original_maximum_looks_again` |
| Adjudication (Ruling A's revision) | Revises the current epoch, under its contract, as the next revision; replay reproduces its correctness. | `test_an_adjudication_of_a_regrade_revises_its_epoch_under_its_contract` |
| The facet evidence timeline | Orders epochs through `grading_epochs`. Each epoch is a whole grading, and a held unrecorded epoch banks nothing, so the receipt-exactness invariant holds at the tag. Without the timeline change the test fails on facet `compute`. | `test_the_timeline_banks_exactly_what_the_projection_banks_at_the_successor` |
| The grade dual-write | Classifies out of the cited contract's maximum (8), not the item's later one (6); below the tag it still reads the item. | `test_the_grade_channel_classifies_…[mvp-0.25, mvp-0.26]` |
| Method-explicit, deferred and clarification regrades | All cite their contract, at revision 1. The method-explicit one cites the frozen contract. | `test_a_method_explicit_regrade_cites_its_frozen_contract_under_a_new_revision`, `test_a_deferred_regrade_of_a_self_grade_cites_its_contract`, `test_a_clarification_regrade_cites_its_contract` |

Out of scope by the brief, and untouched: serving, the reveal ledger, and the queued "one serve/administration eligibility decision" stage.

## 6. Tests

- **`tests/test_regrade_contract_replay.py`** (5, fail-first): the three §8.4 cases plus their variants (§1). All five fail on `311de408e` and pass here.
- **`tests/test_regrade_contract_successor.py`** (38):
  - **Version and fingerprint:** the tag is mvp-0.26, the chain is linear, the fingerprint is recorded.
  - **The epoch rule** as pure functions: same-second legacy regrades, successor supersession, the sequence, mixed citations.
  - **The writer:** cites, revisions, every tier superseded, the snapshot written in the transaction, deferred, clarification and method-explicit regrades, and the old writer below the tag.
  - **Replay of old rows:** byte-identical below the tag; held with the blind maximum (3/8), or the kept correctness (joint) where a lowered rubric never fails a rebuild; no evidence (equal to a route-rule hold); released by a regrade or an adjudication; the compatibility reading of a pre-contract first grade, held only once its score no longer fits.
  - **The readers** (§5).
  - **The property test** (10 seeds). Two answers on one learning object go through a random history of grades, regrades, holds and releases, rubric edits, adjudications and rebuilds. After every step, correctness stays in [0, 1]. After every rebuild, each attempt's grade equals its last live write, whatever the rubric says now, and its current epoch cites a contract. Once settled, a rebuild changes nothing.
  - **`test_rebuild_converges_after_an_adjudication_as_it_did_before[mvp-0.25, mvp-0.26]`:** see Q5.
- **`tests/test_regrade_contract_upgrade.py`** (8):
  - **The upgrade:** holds exactly the unrecorded epochs and rewrites no evidence.
  - **The upgrade shadow predicts the upgrade:** value for value, beyond the version stamp of learning objects the upgrade does not replay. Under the old label the shadow shows 0 changes, and the changes stay on the held attempts' items and learning object.
  - **The rest:** the settled rebuild after the upgrade, nothing replayed when nothing is reinterpreted, the chain from mvp-0.16/0.23/0.24, refusals and idempotence, the CLI, and the head-fixture path (FK check, doctor, settled rebuild).
- **Changed:**
  - **The version pins** in 16 earlier successor tests: the latest is mvp-0.26, negative chain indices shift by one, and version sets gain mvp-0.26, as at every successor merge.
  - **`test_characterization_certification_ledger`:** the evidence rows of the canonical observation ledger now carry their `id` and `created_at`, which the epoch rule orders by.
  - **The CLI help snapshot:** `upgrade` only.
  - **`test_architecture`:** no new function-local cross-domain import; the regrade's snapshot goes through `attempts.attempts`.

## 7. Parity (backup-API copies; no model call)

**The copies.**
- The owner's `fixtures/linear_algebra` and `fixtures/probability` were copied from the main checkout with `learnloop.db.copies.copy_tree_with_databases` into `fixtures-local/regrade-contract/orig/`, including probability's `.learnloop/state.sqlite`.
- Each original was read once. Every per-side copy (`main/`, `branch/`, `shadow25/`, `shadow26/`, `upgrade/`) was made from `orig/` with the same helper, under `fixtures-local/regrade-contract/run1/`.
- `arxiv_v2` was not opened.

**The code and environment.**
- Main's code is `git archive 311de408e`, first on `PYTHONPATH`. `migrations/`, `pyproject.toml` and `uv.lock` are the same on both sides.
- `LEARNLOOP_CONFIG_DIR` was an empty directory and `LEARNLOOP_AI_PROVIDER` was unset.
- `agent_runs` is 105 and 24 before and after every run; `model_call_receipts` is 0.

| Check | linear_algebra | probability |
|---|---|---|
| open (migrate), main's code and the branch's | 165 → 206 on both; schema hash identical (`bd2d227954163df4`) | 165 → 206 on both; schema hash identical (`ef1b4a046f2e0b3e`) |
| `rebuild --shadow --json` at their own label (mvp-0.8), main vs branch | identical (facet 0, mastery 2, schedule 8; live unchanged) | identical (facet 0, mastery 1, schedule 1; live unchanged) |
| `doctor --json`, main vs branch | 0 differences once the copy's path is normalized (57 issues, 1 error) | 0 differences once the copy's path is normalized (101 issues, 48 errors) |
| attempts with an ordinary regrade epoch citing no contract | 7 (6 superseded, 1 current: `01KYCM9N…`) | 0 |
| upgrade shadow: candidate mvp-0.26 vs candidate mvp-0.25 (branch code) | 6 rows differ, all on the held attempt's item and learning object (§4) | 0 rows differ |
| the real upgrade, mvp-0.8 → mvp-0.9 → mvp-0.26 (branch code) | upgraded; its note names `01KYCM9NYBGYDKGR2GGYQYSV23`; that attempt goes from (4, 1.0, no review) to (4, 1.0, held, `grade_contract_unrecorded`) | upgraded; no note |

The shadow and doctor runs left every live copy byte-identical (each shadow's before and after hashes are equal). The scripts and outputs are in `fixtures-local/regrade-contract/` (gitignored): `compare.py`, `count.py`, and `run1/*.json`.

## 8. Gate

Run on the final code (`7940dbd36`) in the worktree, with `TMPDIR=<worktree>/fixtures-local/tmp`, after `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`:

| Check | Result |
|---|---|
| `uv run --no-sync lint-imports --no-cache` | 22 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | 12319 passed, 2 xfailed, 0 failed (12 min 43 s). The 2 xfails are main's strict ones. This includes the 51 new tests. |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | 106 passed, 12215 deselected |
| DB and config references | regenerated at `8e5292189`; `db_validate_reference.py` reports 0 errors; `validate_vault.py` passes |
| CLI help snapshot | regenerated (`upgrade` only) |
| RPC pins, frontend, `cargo check` | not run: no RPC, nothing under `apps/` changed |

The same lanes passed on `ba8709f00` before the one-line upgrade fix in `7940dbd36`: 12319 passed and 2 xfailed, and 106 passed. No run had a timing failure, so nothing needed a rerun alone.

## 9. Open questions (defaults applied)

- **Q1. A kill switch?** None was added. The earlier writer is the defect, and replay reads what each epoch recorded. *Default: no switch; rolling back is restore-only.* **Owner confirmed 2026-10-20:** no switch; rollback = restore the backup.
- **Q2. An unrecorded epoch whose total maximum a blind record kept.** It is held, like one without: its fraction is known but its criteria's maxima are not. The alternative is to schedule it by the recorded fraction with no criterion evidence (PF-c's nothing-assessed path). *Default: held.* No owner vault has such an attempt.
- **Q3. The correctness of a held unrecorded epoch with no recorded maximum.** It is the value the attempt row carries, kept and never used as evidence. NULL would be "unknown", but about 30 readers read the column as a float. *Default: kept.*
- **Q4. Pre-contract first grades** keep the compatibility reading of the item while their score fits, and are held once it no longer does. *Default: as built.* Holding them all would be a `substrate.compat` decision.
- **Q5. Two rebuild passes after a write that does not replay** (an adjudication, a label move). This is pre-existing and identical at mvp-0.25 (`test_rebuild_converges_after_an_adjudication_as_it_did_before`). Replay reads the canonical projection as each attempt's prior, and the projection is the one before the change. An upgrade that holds an attempt leaves the vault one ordinary rebuild from its fixed point. *Default: as is; out of this stage.* A follow-up could give replay an as-of prior.
- **Q6. Adjudication correctness** at mvp-0.26 is `round(fraction × total) / maximum`, what replay computes, not the raw fraction. *Default: as built (one formula).*
- **Q7. The upgrade replays only the learning objects holding a reinterpreted attempt.** The others keep their mvp-0.25 version stamp until their next rebuild, as at every earlier successor. *Default: as built.*
- **Q8. The owner's held answer `01KYCM9NYBGYDKGR2GGYQYSV23`** (linear_algebra) stays held until the owner regrades it (one grading call) or adjudicates it. *Default: leave it held.*

## Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/regrade-contract-onto-main`. The stage's base is `311de408e` and its tip `eb1d146e4`, unchanged. Main's tip was `21187d84d` (mvp-0.25, schema head 206; since the base it changed only `docs/specs/spec_storage_sync_v1.md`, the owner's storage decisions). Main was neither fast-forwarded nor pushed here.

**Commits:**
- `bc073330b`: a real `--no-ff` merge of `fix/regrade-contract-replay` (9 commits) onto `21187d84d`.
- `5616c1bbb`: the references regenerated on the merged tree, and the Pipeline Map entry.
- This record.

### Merge

- **No conflicts.** No file changed on both sides. Main's only change since the base is a spec, which the branch does not touch. Nothing under `apps/` differs from main.
- **No migration** (207 stays free), no config key, no RPC.

### Regenerated

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**. Schema head 206, 325 table notes, 860 effective configuration leaves in 52 sections, the same as the prose counts in `Database.md` and `Configuration.md`. Besides the 379 source-commit labels, two table notes move. Both changes come from the stage's own `7940dbd36`, which postdates the branch's regeneration at `8e5292189`:
  - `derived_state_rebuilds` now names `src/learnloop/regrade_contract_upgrade.py`;
  - `parameter_registry` now names `tests/test_regrade_contract_upgrade.py`.
- **Defaults snapshots.** The template `.pyc` was deleted and `template.py` touched. All 18 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries (`mvp-0.9`..`mvp-0.26`) equal `defaults_fingerprint_for_version`: **0 mismatches**. Main adds no key, so none moved.
- **CLI help snapshot.** Unchanged from the branch's (`upgrade` only). `test_cli_help_snapshot.py` passes on the merged tree.
- **The Pipeline Map.** Its source paths gain `attempts/regrade.py`, `grading_epochs.py` and `regrade_contract_upgrade.py`. The mvp-0.26 entry now names the upgrade's activation: one transaction under the vault mutation lock, replaying only the learning objects that hold a reinterpreted attempt, with the config published by an fsync'd atomic rename before the commit. `validate_vault.py` passes (1,111 notes, 1,109/1,109 reachable).
- **Validators that already fail on main**, run on both trees:
  - **`module_validate.py`:** main reports 765 issues and the merge 769. The full lists, with the 100-line truncation lifted, differ by exactly 4 entries: `grading_epochs.py` and `regrade_contract_upgrade.py`, each with a missing expected note and a "source has no module note". This is the stale catalog's known kind of issue.
  - **`desktop_validate.py`:** identical on both trees, apart from the path. It stops at main's `pdfSelection/testing/syntheticBook.ts`.
  - **No new kind of failure.**

### Gate

Run on `5616c1bbb`, the final code tree; the only later commit adds this section.
- **Environment:** Python 3.12.14, with `TMPDIR` set to merge2's `fixtures-local/tmp`.
- **Commands:** `uv run --no-sync` after the install. Both suite lanes ran under `flock /tmp/learnloop-fullsuite.lock`.
- **Cost:** no paid call. Every test uses fakes.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (178 packages; pypdfium2 5.14.0) |
| `lint-imports --no-cache` | 22 contracts kept, 0 broken |
| `pytest -n auto -q -p no:cacheprovider` (full suite) | **12,333 passed, 2 xfailed**, 0 failed (12 min 58 s; `fixtures-local/regrade-landing-fullsuite.log`) |
| `pytest -m durability` | **106 passed**, 12,229 deselected (2 min 37 s; `fixtures-local/regrade-landing-durability.log`) |
| frontend / `src-tauri` | not run: nothing under `apps/` differs from main |
| tracked fixtures | `git status` clean after both lanes |

The 2 xfails are main's strict marks. Nothing failed, so nothing needed a rerun alone. The count equals the branch's final gate (12,333 passed): main's change since the base added no test.

### Parity (backup-API copies; no model call)

**Setup:**
- **Copies.** The owner's `fixtures/linear_algebra` and `fixtures/probability` (with probability's `.learnloop/state.sqlite`) were copied with `copy_tree_with_databases` into `fixtures-local/landing-regrade/orig/`. Each original was read once. Every per-side copy (`main/`, `merge/`, `shadow/`, `upgrade/`, `upgrade25/` and the rebuild copies) was made from `orig/`, or from another copy, with the same helper. `arxiv_v2` was not opened.
- **Code.** Main's code is `git archive 21187d84d`: the whole tree except the top-level `fixtures/` (`tests/fixtures/` and the app's `src/fixtures/` kept), first on `PYTHONPATH`. Every run printed the `learnloop` package it imported, and main's `upgrade --help` does not list mvp-0.26.
- **Environment.** `LEARNLOOP_CONFIG_DIR` was an empty directory, and it stayed empty. `LEARNLOOP_AI_PROVIDER` was unset. `model_call_receipts` is 0 in every copy afterwards, and `agent_runs` stays at 105 (linear_algebra) and 24 (probability).
- **Starting state.** Both vaults were at schema 165, label `mvp-0.8`.

| Check | linear_algebra | probability |
|---|---|---|
| open (migrate), main's code and the merge's | 165 → 206 (41 migrations) on both; `sqlite_master` hash identical | 165 → 206 (41) on both; identical |
| the two migrated databases, `.dump` compared | identical except the 41 `schema_migrations.applied_at` stamps | the same |
| `rebuild --shadow --json` at the vaults' own label (mvp-0.8), main vs merge | **0 differences** besides the live file's sha256 (`applied_at`). Summary: facet 0, mastery 2, schedule 8; live unchanged | **0 differences** (facet 0, mastery 1, schedule 1; live unchanged) |
| `doctor --json`, main vs merge | **0 differences** once the copy's path is normalized (57 issues, 1 error) | **0 differences** (101 issues, 48 errors) |
| upgrade shadow: main's code migrates a copy, then the merge's code opens it | **0 migrations**; shadow and doctor equal main's | **0 migrations**; equal |

The shadow and doctor runs left every live database byte-identical: the sha256 matched before and after.

**Candidate shadows (merge code, label mvp-0.8):** `--set algorithms.algorithm_version=mvp-0.26` against `=mvp-0.25`.
- **linear_algebra: 6 rows differ**, exactly the stage's §4 rows, all on `pi_exercise_01ky5raxvexp8axggqn8e73vkh` and `lo_compute_with_complex_numbers`:
  - 2 item-scoped facet cells and 1 aggregate cell lose their only support;
  - the other aggregate cell's independent mass goes from 0.435 to 0.348;
  - the learning object's mastery goes from 5 to 4 evidence (logit mean 1.048 → 0.985);
  - the item's due date goes from 2026-08-23 to 2026-08-05 (stability 26.7 → 12.1).
- **probability: 0 rows differ.**

### The upgrade on a copy (`upgrade/`; the owner's vaults untouched)

`learnloop upgrade --to mvp-0.26` refuses both vaults as they stand: "only 'mvp-0.25' (or 'mvp-0.9' to 'mvp-0.24', through it) may activate mvp-0.26". They are at mvp-0.8. The refusal changed nothing: the `.dump` and `learnloop.toml` were identical afterwards. The path is therefore two commands per vault:
1. `--to mvp-0.9` (about 30 s);
2. `--to mvp-0.26` (it chains mvp-0.10..0.25, then activates; about 9 min each on these copies).

Both succeeded. The stage reported the same chain (§7: mvp-0.8 → mvp-0.9 → mvp-0.26).

- **Notes.** Both vaults print the recurrence guard's advisory notes from mvp-0.12. Only linear_algebra prints the hold: `1 attempt(s) whose current grade cites no assessment contract are held for review (grade_contract_unrecorded) …: 01KYCM9NYBGYDKGR2GGYQYSV23`. This is the stage's attempt and count.
- **After it:**
  - doctor shows the same 57 and 101 issues by code and severity as before the upgrade (no `sql:derived_state_rebuild_stale`);
  - `foreign_key_check` is empty;
  - `learnloop.toml` changes only `algorithm_version = "mvp-0.8"` → `"mvp-0.26"`.

**What mvp-0.26 changes on linear_algebra.** A second copy was upgraded to mvp-0.25 by the same path (`upgrade25/`), and both were then fully rebuilt once (`rebuild-derived-state`). This takes out the rows any rebuild rewrites. Compared without ids, timestamps and version stamps, the difference is:
- **The held attempt** `01KYCM9NYBGYDKGR2GGYQYSV23`: `manual_review` goes 0 → 1 with reason `grade_contract_unrecorded`. Its 4 points and 1.0 correctness are kept.
- **The 6 learner-state rows above.** The settled values equal the shadow's, within float noise from the prior: 0.98469 against 0.98471.
- **Downstream rows on the same learning object only:**
  - `practice_item_quality_state` of that item: evidence 4 → 3;
  - 5 `attempt_surprise` rows on the learning object's attempts; the held one has bayesian surprise 0 and FSRS factor 1;
  - the severities of 2 `error_events` on `01KY64FZE7ZVJ79YJFWAYZH53Q` (0.6487 → 0.6493);
  - the 4 `learning_outcome_labels` whose outcome is the held attempt (metadata only);
  - the held attempt's `ability_transition_events` row, whose target facets become empty.
- **Ledger appends, no rewrite.** The activation's replay of that learning object appends the grade dual-write for its 4 other attempts (4 `raw_grade_events`, 4 `grade_interpretations`, 4 `activity_observations`). After the full rebuild the held attempt has no new grade-channel row, which is right: a hold is no evidence. It also appends one `causal_hypotheses` version for `01KY64FZ…`, with its incomplete `text_write_provenance` record (graded before write-time provenance).
- **Other rows the activation writes**, before any rebuild: 82 `facet_outcome_observations` and the FTS segments. They appear because the partial rebuild runs every vault-wide replayer. A full rebuild at mvp-0.25 writes the same 82 rows, so they are not mvp-0.26's.
- **Everything else is identical.**

**Probability:** the same comparison shows **0 differences**. The activation replays no learning object and holds nothing.

**Settling.**
- A further full rebuild of the mvp-0.26 copy leaves every learner-state table unchanged.
- **Pre-existing, not this stage's:** each full rebuild appends about 38 dual-write rows per table (`raw_grade_events`, `grade_interpretations`, `activity_observations`), and moves `hypothesis_recurrence_state.input_fingerprint`. Both happen identically at mvp-0.25, and with main's own code on the same mvp-0.25 copy. Main's and the merge's full rebuilds at mvp-0.25 give identical learner state.

**Releasing the hold**, tried on copies with `learnloop grading adjudicate <interpretation> --resolved-class …` (`human_owner`, no model call):
- `--resolved-class success` upholds the current class. It returns `evidence_revision: skipped_direction_unchanged`, and **the attempt stays held**.
- `--resolved-class partial_success` flips the direction. It writes the revision (`revised`), the attempt becomes 2 points and 0.5, and the hold clears.

So a CLI adjudication releases the hold only when it changes the grade's direction (Ruling A). `test_an_adjudication_releases_an_unrecorded_hold_under_the_contract_it_cites` calls `append_adjudication_evidence_revision` directly, below that gate. The held attempt is also absent from `learnloop grading reviews`, which reads the P0.2 review flags, not `manual_review_reason`.

### The owner's upgrade steps (run by the owner; never run here)

For each vault, with the desktop app, the MCP runtime and the mobile host closed:

1. **Back up** with the backup API, from the repository root:
   `uv run python -c "from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases as c; c(Path('fixtures/linear_algebra'), Path('fixtures-local/backup-linear_algebra-pre-mvp026'))"`.
   Do the same for `probability`; its copy includes `.learnloop/state.sqlite`.
2. **Upgrade.** The first open migrates 165 → 206. mvp-0.26 accepts only mvp-0.9 or later, so each vault needs two commands:
   - `uv run learnloop upgrade --to mvp-0.9 --vault fixtures/linear_algebra`
   - `uv run learnloop upgrade --to mvp-0.26 --vault fixtures/linear_algebra`

   Then the same two for `fixtures/probability`.
3. **Optional:** `uv run learnloop rebuild-derived-state --vault <vault>`, then `uv run learnloop doctor --vault <vault>`. The upgrade leaves a vault one ordinary rebuild from its fixed point (Q5, Q7).

Both vaults are tracked fixtures, so their `state.sqlite` and `learnloop.toml` will show as modified afterwards. That is expected for the owner's working vaults.

**The held answer** `01KYCM9NYBGYDKGR2GGYQYSV23` (linear_algebra, item `pi_exercise_01ky5raxvexp8axggqn8e73vkh`, self-graded, then regraded on 2026-07-25 by a joint grader that kept no maximum) stays held, at 4 points and 1.0 and with no evidence, until one of these:
- **A regrade**: the feedback screen's regrade or contest, one grading model call. It cites the item's contract and replaces the reason. This is the only way to keep a full-credit grade.
- **A direction-changing adjudication**: `uv run learnloop grading adjudicate <its active interpretation id> --resolved-class <class> --vault fixtures/linear_algebra`. The interpretation id is on its newest `activity_observations` row. An adjudication that upholds `success` leaves it held, as shown above.

### Open items

1. **Q1, no kill switch (owner confirmation needed).** Rolling mvp-0.26 back is restore-only: restore the step-1 backup. Setting `algorithm_version` back by hand would leave rows written at the tag (cited regrades, revisions, every tier superseded) under a predecessor's replay. The stage's default is no switch, because the old writer is the defect.
   **Owner confirmed 2026-10-20** ("q1: no switch, q44: end it honestly with no replacement, q45: yes it ends the check. for rw6a yes to defaults"): no kill switch; rollback = restore the step-1 backup.
2. **Releasing a correct held grade without a model call** (new). An upholding adjudication through the CLI does not release `grade_contract_unrecorded`: Ruling A writes an evidence revision only when the direction flips. To keep 4/4, the owner must regrade (one call). Alternatives for a follow-up:
   - let an upholding owner adjudication of a held unrecorded grade write the revision;
   - list such holds in `grading reviews`, which today does not show them.
3. **Two commands per vault.** The owner's vaults are at mvp-0.8, and mvp-0.26 refuses below mvp-0.9. The brief expected one command per vault. Making `--to mvp-0.26` chain from mvp-0.8 is a possible follow-up; it is not needed.
4. **Q2–Q8** stand as the stage recorded them (§9). Q8 (leave the held answer held) is now concrete, as item 2 describes.
5. **Pre-existing:** every full rebuild appends about 38 dual-write rows and moves the recurrence input fingerprint, on main as here (above). It is out of this stage.
