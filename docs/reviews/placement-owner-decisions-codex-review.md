# Placement owner decisions: review fixes (2026-10-12)

**Branch:** `fix/placement-owner-decisions` (worktree
`learnanything-placement-decisions`), on top of the stage's first pass
(`c4ebee44`; record: `placement-owner-decisions.md`). Not merged, not pushed.

**Input.** Twelve review findings (F1-F12; 2 High, 3 Medium, 7 Low) and six
claims in the first pass that did not hold. Codex is exhausted until
2026-10-18, so no Codex call was made: every test uses fakes. Every finding
was reproduced first. F1 and F2 were reproduced with the reviewer's scratch
tests: on `c4ebee44`, `submit_attempt` on an ignored `in_progress` episode
returned `feedbackDeferred: True`, and `start_overconfidence_probe` left the
episode ignored. The others were reproduced with the new tests below, run
against the pre-fix source.

**Owner decisions in force.** The spec defaults are accepted. Frictionless
defaults: honest labels, generous defaults, live changes behind kill switches,
no shadow stages. The owner's Phase 6 answers are implemented, not
re-litigated: OQ1 ignore unanswered opening probes, OQ2 `q` stays 0.8, OQ3 let
the diagnosis decide, and M2 OQ1 start at the latest version.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | An ignored opening episode still holds back feedback on ordinary answers | Fixed | `113b2622` | `test_placement_opening_probes.py::test_an_answer_on_an_ignored_episode_is_not_held_back_for_it` (placement: no route, no applied episode recorded, next-probe peek inactive; kill switch: the predecessor's deferral, exactly) |
| F2 | High | An ignored opening episode swallows probes the learner asks for and blocks error-driven re-probes | Fixed (one part rejected, below) | `113b2622` | `test_the_overconfidence_list_adopts_an_ignored_episode`, `test_the_causal_quick_check_stops_the_episode_being_ignored`, `test_an_error_driven_reprobe_adopts_an_ignored_episode`, `test_a_named_calibration_adopts_an_ignored_episode` |
| F3 | Medium | A pending diagnosis can hold the check indefinitely | Fixed (count-based bound rejected, below) | `a3d23bf7` | `test_placement_diagnosis_decides.py::test_a_diagnosis_that_never_lands_stops_holding_the_check` (provider never ready, frozen clocks either side of the deadline, then a late diagnosis) |
| F4 | Medium | Resolved outcomes are not latched: a regrade, `diagnose retry` or the split switch reopens or flips them | Fixed (one residual kept, below) | `a3d23bf7` | `test_a_decided_miss_is_not_reopened_by_a_retry`, `test_a_decided_miss_is_not_reopened_by_a_regrade`, `test_turning_the_split_back_on_does_not_reopen_held_misses` |
| F5 | Medium | "No gap attributed" fails open: a blank or zero-score check passes into maintenance | Fixed | `a3d23bf7` (rules, report), `298cedbf` (§11) | `test_no_gap_attributed_is_not_a_pass[diagnoser-abstains, validity-unknown]`, `test_report3_keeps_the_raw_full_marks_miss_rate`, `test_the_diagnosis_reading_is_the_m2_vocabulary`, vitest `PlacementControls.test.tsx` |
| F6 | Low | Several readers still see the ignored episode | Fixed | `113b2622` | `test_an_ignored_episode_feeds_no_reader_that_scores_it` (intervention trigger wiring, tutor Q&A guard, staged-controller robust value) |
| F7 | Low | The placement sweep resolves existing probe-pool-empty notices, and the kill switch does not undo that | Fixed | `113b2622` | `test_a_notice_raised_before_placement_is_held_not_resolved` (sweep and feed aging; kill switch refreshes the same notice) |
| F8 | Low | A pending miss also holds back later learner-side misses | Fixed | `a3d23bf7` | `test_learner_side_help_does_not_wait_on_an_earlier_pending_miss`, `test_learner_side_help_in_maintenance_does_not_wait_on_a_pending_lapse` |
| F9 | Low | `diagnosis_live` defaults to True | Fixed | `a3d23bf7` | `test_the_state_loader_requires_the_split_reading_and_the_time` |
| F10 | Low | Placement reimplements the "one rule for every reader" for which diagnosis is in force | Fixed | `a3d23bf7` | Refactor. Placement calls `Repository._diagnosis_in_force` and the new `_diagnosis_concerns_grade`, which `_diagnosis_in_force` is now built from. Covered by every diagnosis-decides test |
| F11 | Low | The playbook was widened beyond the owner's decisions, and the "no vault reached mvp-0.11" check is narrow | Fixed | `298cedbf` | Docs. The playbook records the amendment as a one-off exception. Both review records state that the check covered the three tracked vaults only (open question 1) |
| F12 | Low | `probe-instances --lo <LO>` skips an ignored episode, but naming the LO in calibration works | Fixed | `113b2622` | `test_probe_instances_reaches_an_ignored_episode_when_the_lo_is_named` |

Rejected parts (each with its reason; the rest of the finding is fixed):

- **F2, "and no presentation in any status".** Not adopted. An opening
  episode with a committed presentation the learner never submitted is still
  an unanswered opening probe, which the owner said to ignore "for sure". The
  case the reviewer meant (the causal quick check commits a `selected`
  presentation) is caught by the origin stamp: the relock writes `origin =
  causal_factor:<id>`. Every adoption also writes a `target_decision`. Under
  placement no door commits a presentation on a pristine episode without
  stamping it first.
- **F3, "or released `provider_not_ready` more than K times".** Not
  adopted. `post_attempt_jobs` keeps no release count (`attempt_count` is
  refunded on each such release), so adding one would need a migration.
  Neither the stage nor the fix needs one. The time bound alone covers every
  cause: a provider that is never ready, a queue held behind a stuck head, or
  the switch turned off and on.
- **F4, a regrade that changes whether the answer is a miss at all.** Still
  read live. This is Phase 6's merged semantics: the grade is read from the
  attempt row and the check follows the regraded grade, as pinned by
  `test_placement_split_grades.py::test_the_check_follows_a_regrade_that_requeues_the_diagnosis`.
  Latching it would mean rebuilding each answer's grade as of its decision
  time from the blind-grade ledger. That is a redesign, not a fix. A regrade
  that leaves the answer a miss no longer reopens its decision; this was the
  defect introduced by this stage.

## How each fix works

**F1, F2, F6, F7, F12 (OQ1, ignore unanswered opening probes).**
- **Narrower definition.** Placement ignores only a *pristine* opening
  episode: `trigger = 'initial'`, no `origin`, no `target_decision`, and
  nothing answered (`unanswered_opening_episode_ids`).
- **Absent at every door.** The feedback route, the applied-episode record,
  `_attempt_result` and `get_next_probe_item` all read the new
  `servable_open_episode`. So do tutor Q&A's decision guard, the intervention
  trigger's unfamiliar-probability input and the staged controller's robust
  value (`ignored_episode_ids`).
- **Adoption.** `enter_episode` adopts an ignored episode
  (`adopt_ignored_opening_episode`) instead of returning it unchanged. It is
  relocked the way the causal quick check relocks an observation-free episode:
  a fresh hypothesis set, any committed presentation invalidated, `entered_at`
  moved, and the request stamped on `origin` and `target_decision`
  (`kind = adopted_opening_episode`, the requested trigger, origin and goal).
  The episode keeps its id, its `initial` trigger and its observation budget,
  as every relock does.
- **Re-probes.** The misconception and predictive-failure triggers treat an
  ignored episode as absent (`_open_episode_blocks`). A named or goal-scoped
  calibration adopts it too.
- **Notices.** Both the sweep and the maintenance feed's aging hold an
  empty-pool notice on an LO whose episode is ignored
  (`held_probe_pool_notice_keys`). They neither raise nor resolve it.
- **Kill switches.** Nothing changes until the learner or an error acts on
  the LO. `placement.enabled = false` and `placement.initial_probes = true`
  still restore the predecessor exactly for every episode no door touched.
  The kill-switch half of the F1 test and the existing fixture-copy test pin
  this. An adopted episode stays adopted, as any episode a door opened would.

**F3, F4, F5, F8, F9, F10 (OQ3, let the diagnosis decide).**
- **Decided once (F4).** `load_miss_verdicts` decides a graded miss by its
  first live diagnosis that read the blind grade current when it landed. It
  reads append-only rows only (`blind_grade_records`, `attempt_diagnoses`). A
  later `diagnose retry`, a re-queue, or a regrade that leaves the answer a
  miss appends rows but never reopens or changes a decision that has landed.
  A diagnosis of a grade that a regrade had already superseded decides
  nothing.
- **Wait bound (F3).** A miss waits at most
  `placement.rules.DIAGNOSIS_WAIT_DAYS = 7` from its first live diagnose job
  (the earliest `post_attempt_jobs.created_at`; a re-queue does not restart
  the wait, whether it adds a row or resets one). After that, today's rule applies with fallback
  `diagnosis_unavailable`, decided at the deadline. A diagnosis that lands
  later does not change it. This is a hard-coded bound, like `q`, and it is
  versioned under `RULES_VERSION`. Seven days also covers the current Codex
  outage, which ends 2026-10-18.
- **Split switch (F4).** A job the worker released `split_disabled` keeps
  today's rule until its diagnosis lands, read from the job's own
  `last_error`. Switching the split back on therefore does not reopen held
  misses. Today's switch still applies at once when it is off, so the kill
  switch stays immediate.
- **Decision times (F8).** Every verdict now carries `decided_at` and
  `decided_ref`: the deciding diagnosis row, the deadline, or the answer
  itself. Learner-side help (a hint, priming, "don't know", assistance) or
  "I don't know this" recorded before an earlier miss's decision landed
  returns the LO at once. That holds at the check and in maintenance, and it
  stays the decision whatever the diagnosis later reads. A receipt therefore
  does not change after the fact.
- **Fail closed (F5).** Only a positive non-gap reading keeps the topic: a
  slip, an item contract or grader interpretation, `interaction_context`
  (new: the grader's "the presentation, not knowledge", which the first pass
  kept through `no_gap_attributed`), or an unassessed criterion.
  `no_gap_attributed` (the diagnoser abstained, the validity was left
  `unknown`, or there is no attribution) returns the LO to learning, with
  that reason on the receipt.
- **Report 3 (F5).** Report 3 adds `first_review_full_marks_misses`,
  `first_review_full_marks_miss_rate` and its Wilson interval, per source and
  overall. Field spec §11 now names `first_review_miss_rate` (returns to
  learning) as the rate a learned `q` is fitted to.
- **Required arguments (F9).** `load_placement_state_from_connection` now
  requires `diagnosis_live` and `now_iso`. `load_placement_state(vault,
  repository)` keeps its two-argument form, which DL1's `daily_plan/headline.py`
  calls; `now_iso` defaults to the wall clock. Every production caller passes
  its clock.

**The successor chain (claims 5-6, F11).** `algorithm_versions.SUCCESSOR_CHAIN`
lists `mvp-0.9 -> mvp-0.10 -> mvp-0.11`. `DIAGNOSIS_SPLIT_VERSIONS`,
`PLACEMENT_VERSIONS` and `P0_SUCCESSOR_VERSIONS` are derived from it
(`successors_from`), as is `LATEST_ALGORITHM_VERSION = SUCCESSOR_CHAIN[-1]`.
The values are unchanged. Slice 2 T1 (`mvp-0.12`) and practice/stuck-prompt
(`mvp-0.13`) each append one tag, plus their defaults snapshot, and keep the
split and placement. `test_config_refactor.py::test_a_successor_merge_appends_one_tag_and_every_gate_follows`
pins this.

## Claims that did not hold

| Claim (first pass) | Now |
|---|---|
| "Ignored for serving" | True at every door (F1, F6). A door that opens an episode adopts it instead (F2) |
| Interpretation 6: "a re-probe stays blocked exactly as before" | Withdrawn: re-probes, the overconfidence list, the causal quick check and named calibrations adopt the episode (F2) |
| "`placement.enabled = false` restores today's behaviour exactly" | True for every episode and notice no door touched: notices are held, not resolved (F7). Adopted episodes are a learner's or an error's action, not placement's |
| "The receipt is the resolution" | True now: each miss is decided once, with its decision time on the receipt (F4, F8) |
| "A successor merge moves only that constant" | Fixed in code: the merge appends one tag to `SUCCESSOR_CHAIN` and every gate follows |
| "`DEFAULTS_SNAPSHOT_BY_ALGORITHM` is defined as `defaults_fingerprint_for_version`" | Corrected: the entries are literal hashes pinned by a test to that helper (`config/template.py`, both records) |
| §11: "≥ 30 resolved first reviews ⇒ ±0.15 or narrower" | Corrected: at n = 30 the 95% Wilson half-width is 0.168 at a 50% rate, 0.156 at 30%, 0.139 at 20%; ±0.15 or narrower only at or below about 25% |

## Spec conformance after the fixes

| Item | Status |
|---|---|
| M2 OQ1: new vaults at `LATEST_ALGORITHM_VERSION` | Built; existing vaults are not moved; the version gates follow the chain |
| P6 OQ2: `q` stays 0.8, learned later | Built (docs); the §11 trigger arithmetic is correct and the rate `q` is fitted to is named |
| P6 OQ3: the diagnosis decides the check and lapses | Built. It fails closed on `no_gap_attributed`, waits at most 7 days, and decides each miss once. Learner-side help keeps today's rule (interpretation 1, still open) |
| P6 OQ1: ignore unanswered opening probes | Built at every door; a door that opens an episode adopts it |
| Kill switches | `placement.enabled` and `placement.initial_probes` restore every untouched episode exactly. `diagnosis.split_enabled = false` applies today's rule to misses whose diagnosis has not landed. As before, OQ3 has no switch of its own (open question 3) |
| Replay/rebuild, evidence and blindness | Unchanged: no projection, evidence or model change. The adoption relock writes only `probe_episodes` and `hypothesis_sets` rows, as the causal relock already does |
| Migrations, table roles, spend | No migration (head 173); no paid path |
| DL1 interface | Stable: `load_placement_state(vault, repository)`, `PlacementState` and the queue components are unchanged. `MissVerdict` gains two fields (additive) |

## Proof on the backup copies

These are read-only reads of the existing backup-API copies under
`fixtures-local/placement-decisions/` (made with `copy_tree_with_databases`
from the worktree's tracked `linear_algebra`, `probability` and `arxiv_v2`, and
taken through the real upgrade path to `mvp-0.11` in the first pass). The
narrower pristine definition changes nothing on the owner's data: every open
opening episode is unstamped and unanswered, so all of them are still ignored.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Open `initial` episodes | 9 | 18 | 31 |
| ... with an `origin` or a `target_decision` | 0 | 0 | 0 |
| Pristine and unanswered (ignored with placement on) | 9 | 18 | 31 |
| Assumptions (so the OQ3 changes act on nothing yet) | 0 | 0 | 0 |

The fixture-copy test (`test_placement_fixture_copies.py`) reran the kill
switch and the new-material checks on fresh copies in the full suite. The
tracked working vaults were not read directly or written.

## Paid calls and spend

None: no model route, no Codex call (exhausted), no OpenRouter call; $0.00.
The Eedi dataset the owner downloaded is for another stage and was not opened.

## Gate

The gate ran on source and tests as of `a907b46a`. The later commit adds
only these review records.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | OK (pypdfium2 5.14.0 reinstalled after the sync) |
| `uv run lint-imports --no-cache` | **12 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7,817 passed**, 0 failed, 46 warnings (the existing Python 3.12 fork and SQLite datetime-adapter deprecations); 190.6 s. That is 20 more than the first pass's 7,797 |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **84 passed**, 7,733 deselected, 1 warning; 65.6 s |
| `npm install` (apps/learnloop-tauri) | OK (the existing notice that esbuild's postinstall is blocked by allowScripts); lockfile unchanged |
| `npm run typecheck` | **0 errors** |
| `npm test` (vitest) | **103 passed** in 23 files (the `PlacementControls` label test gains two assertions) |
| DB reference (`db_generate_reference.py`, `db_validate_reference.py`) | No schema change; regenerated for the moved source anchors (`a907b46a`): schema head **173**, **288** table notes, **599** config leaves in **35** sections, **0 errors**. `validate_vault.py`: passed (1,056 notes) |
| `cargo check` | Not run: no Rust change |
| Fail-first | Run against the pre-fix source of each group: the 8 new opening-episode tests and the 10 new diagnosis-decides tests all failed there (the F1 kill-switch case passes on both sides, pinning the predecessor). The successor-chain test fails there too (no `SUCCESSOR_CHAIN`) |
| Tracked working vaults | Untouched (`git status` clean for `fixtures/linear_algebra`, `probability`, `arxiv_v2`) |

## Open questions for the owner

1. **The in-place amendment's scope (F11).** Confirm that no vault other than
   the three tracked working vaults was upgraded to `mvp-0.11` after the
   Phase 6 merge (2026-10-12 15:19 -0400). Any such vault would run the
   amended semantics without a new tag.
2. **The wait bound.** Is `DIAGNOSIS_WAIT_DAYS = 7` right? It is a hard-coded
   bound like `q`.
3. **A switch for OQ3.** OQ3 has no switch of its own. `placement.enabled =
   false` turns off all of placement, and `diagnosis.split_enabled = false`
   restores today's rule only for misses whose diagnosis has not landed.
   Should "let the diagnosis decide" get its own switch?
4. **Learner-side help** (first pass, interpretation 1). Hints, priming and
   "don't know" keep today's rule. Should the diagnosis decide these too?
5. **A regrade that turns a miss into a clean answer, or the reverse.** It is
   still read live (Phase 6's merged semantics). Should a resolved assumption
   ignore it?
6. **Phase 6 open question 4** (the quick check on the import result) is
   still open.
