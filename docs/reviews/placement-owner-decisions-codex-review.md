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

## Re-review (2026-10-12)

**Input.** The re-review confirmed the first round's F1, F2, F6, F7, F9, F10
and F12, and reopened the stage with four findings (2 Medium, 2 Low). Its
F1 and F2 are new defects in the adoption path. Its F3 says the earlier F4
fix does not hold for the split switch. Its F4 says the earlier F5 fix still
keeps a topic when attributions are mixed. The reviewer's scratch tests
(`rev2/*.py`) were not in the worktree, so each finding was reproduced with a
new test in the suite. All of them failed on the pre-fix source
(`3718eb91`): 11 failures across the two test files. The
positive controls passed on both sides: the overconfidence list keeps the
placement minimum, and a slip plus a grader-interpretation reading is still
kept. Codex is exhausted until 2026-10-18, so no Codex call was made and
every test uses fakes.

**Owner decisions in force.** As above. The owner's Phase 6 answers are
implemented, not re-litigated: OQ1 ignore unanswered opening probes, OQ2 `q`
stays 0.8, OQ3 let the diagnosis decide, and M2 OQ1 start at the latest
version.

### Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| R1 (re-review F1) | Medium | An adopted episode keeps the opening episode's one-observation minimum, so error-driven re-probes conclude on one observation | Fixed | `01719230` | `test_placement_opening_probes.py::test_an_adopted_reprobe_is_held_to_the_reprobe_contract` (minimum 2, algorithm `mvp-0.11`, a freshly persisted channel pin replacing a stale one, and the whole open-time contract equal to a fresh misconception re-probe's). Also new assertions in `test_a_named_calibration_adopts_an_ignored_episode` (manual: 2) and `test_the_overconfidence_list_adopts_an_ignored_episode` (goal_diagnostic: the placement minimum, a positive control) |
| R2 (re-review F2) | Low | An adopted episode that completes with no gap leaks `{"kind": "adopted_opening_episode"}` to the tutor as a typed transition decision | Fixed | `01719230` | `test_an_adopted_episode_that_completes_without_a_gap_opens_no_tutor` (`_diagnostic_decision_for` is None, and `build_tutor_opening` returns None without touching the client; a typed decision written afterwards is returned) |
| R3 (re-review F3) | Medium | The split switch: a provider-not-ready release reopens a held miss, and the diagnosis that lands later flips it | Fixed (one part rejected, below) | `18d1d1cb` | `test_placement_diagnosis_decides.py::test_turning_the_split_back_on_does_not_reopen_held_misses` (now drains after re-enabling: off and released `split_disabled`, then on, then a `provider_not_ready` release, then a slip landing; failed `split_disabled` at the hold throughout). `test_the_first_serving_build_with_the_split_off_records_the_hold` (the toggle with no worker run in between: two misses, head of the line and behind it). `test_a_miss_decided_before_the_hold_keeps_its_diagnosis` |
| R4 (re-review F4) | Low | One non-gap reading outweighs an abstention or a fatal error | Fixed | `18d1d1cb` | `test_the_diagnosis_reading_is_the_m2_vocabulary` (new cases). `test_a_mixed_reading_keeps_the_topic_only_when_every_part_reads_non_gap[abstain-plus-grader-interpretation, slip-plus-abstain, slip-plus-grader-interpretation]`. `test_a_fatal_error_the_diagnosis_never_read_returns_the_topic[unread-fatal-error, fatal-error-named-by-an-attribution]` (real grading door, rubric fatal error) |

Rejected part (the rest of R3 is fixed):

- **R3, "`test_the_check_follows_a_regrade_that_requeues_the_diagnosis`
  still pins a reopen".** Kept, for the reason recorded in the first round
  (F4 residual). That test is a regrade that turns a clean answer into a
  miss, which changes whether the answer is a miss at all. The grade is read
  from the attempt row, which a regrade rewrites in place (Phase 6's merged
  semantics). Latching it would mean rebuilding every answer's grade as of
  its decision time from the blind-grade ledger, and joint grades have no
  such ledger. That is a redesign, not a fix. It stays open question 5. A
  regrade that leaves the answer a miss does not reopen its decision, and the
  re-review confirmed that part.

### How each fix works

**R1, the adopted episode's contract.** `enter_episode`'s open-time fields
are now one function, `episode_open_contract(vault, repository, lo, trigger,
goal_id)`: the observation budget by trigger, the maximum, required facets,
the terminal-contract pin, the calibration channel pin and the algorithm
version. `enter_episode` stamps it on insert, with unchanged behaviour.
`adopt_ignored_opening_episode` re-stamps it for the *requested* trigger in
the same `UPDATE` that relocks the row (`_relock_episode_row(contract=...)`).
So a misconception, predictive-failure or named-calibration adoption keeps
the two-observation breadth contract. The overconfidence list
(`goal_diagnostic`) keeps the placement minimum, as a fresh episode would.
Every adoption resolves and pins the calibration channel and the version of
now. The causal relock still keeps the episode's budget, as before, and the
`trigger` column stays `initial` (the requested trigger rides on
`target_decision`). The ignored-episode definition is unchanged, so on the
owner's data nothing moves until a door acts.

**R2, typed decisions only.** `_diagnostic_decision_for` returns a closed
episode's `target_decision` only when it carries no `kind`. Typed
transitions (`build_typed_transition_decision`) have none. Provenance
stamps have one: an adopted opening episode, and the causal relock's
`causal_repair_class_divergence`. That second one is the same defect,
present before this stage, and the one rule covers both. The adoption stamp
stays on the row, so the episode stays un-ignored and keeps its provenance.
A stamp is skipped like an episode with no decision. The F6 test's fake
decision now has a typed shape.

**R3, the hold is recorded once.**
- **The hold stamp.** `Repository.hold_queued_live_diagnoses` stamps
  `payload.split_held_at = now` on every queued live diagnose job that has
  none. It is write-once and never cleared or moved. Releases, leases,
  settles and owner requeues all keep `payload_json`, and job rows are never
  deleted. Leased rows are skipped, because a settle rewrites the payload it
  leased. The method reads first, so an idle poll with nothing to stamp
  takes no write lock.
- **Who calls it.** It runs only while the switch is off. Callers are the
  worker's `process_next_job` (every pass, so the jobs behind a head of line
  that will not be leased are stamped too), its `split_disabled` release, and
  the scheduler's persisting (serving) build. The persisting build is the
  first serving read, and it runs before fast-track reconciliation.
  Read-only builds (`persist_explanations=False`), the knowledge map and the
  reports record nothing.
- **Deciding.** `load_miss_verdicts` decides a miss by whichever of three
  events came first: its deciding diagnosis landing, the first hold on any of
  its live jobs, or the wait deadline once it has passed. A held miss is
  today's rule (`split_disabled`), with `decided_at` and `decided_ref` set to
  the hold time and job id. It no longer reads `last_error`, so a
  `provider_not_ready` release, the switch coming back on, or the diagnosis
  landing later changes nothing. A miss whose diagnosis landed before the hold
  keeps its reading.
- **Before the hold is recorded.** With the switch off and a queued job not
  yet stamped, today's rule applies at once as of the read, so the kill
  switch stays immediate. A leased job is in flight, so it is pending: it
  lands, or the worker releases it and stamps it.
- **No live job.** A blind-graded miss with no live job is `not_diagnosed`,
  decided with the answer. It no longer reads the switch, because a blind
  grade means the split was on at grading.
- **The docstring.** The "decided once from append-only rows" wording now
  names exactly which job facts are read: the first job's `created_at`, and
  the write-once stamp.

**R4, every part reads non-gap.** `diagnosis_reason(scopes, classes,
unread_fatal_errors=...)` still returns `knowledge_gap` on any gap. Otherwise
it keeps the topic only when every attribution has a positive non-gap
reading (item contract or grader interpretation, a slip on a valid
measurement, the interaction context). The kept topic is labelled by its
strongest reading: item contract, then slip, then interaction context. An
abstention on any valid measurement, a validity left unknown, no attribution
at all, or a fatal error no attribution names gives `no_gap_attributed`, and
the LO returns to learning. The diagnoser's events key on the attributions,
so an unnamed fatal error was never read.

A fatal error that an attribution names in its `error_type` (the grader
prompt allows rubric fatal-error ids there) is read through that
attribution. This narrows the reviewer's "any fatal error". The reason is
the owner's OQ3 example, a miss that only shows the learner did not know
what had to be stated explicitly. That can be a rubric fatal error which
the grader attributes to the item contract. "Let the diagnosis decide" keeps
it. `MissVerdict.unread_fatal_errors` puts the unread ones on the receipt.
`RULES_VERSION` stays `placement-rules-v3`, which this unmerged stage
introduced. Report 3's miss definition, field spec §5.2 and the DTO comment
say the same.

### Spec conformance after the re-review fixes

| Item | Status |
|---|---|
| P6 OQ1: ignore unanswered opening probes | Unchanged definition. An adopted episode is now held to its request's contract and never reaches tutoring as a decision |
| P6 OQ3: the diagnosis decides | Decided once by the first of diagnosis, hold or deadline. A topic is kept only on an all-non-gap reading |
| Kill switches | `diagnosis.split_enabled = false` still applies at once. The first serving build or worker pass records it, and switching back on no longer reopens anything recorded. `placement.enabled` and `placement.initial_probes` are unchanged (the fixture-copy test reran in the full suite) |
| DL1 interface | Stable: `load_placement_state(vault, repository)`, `PlacementState` and the queue components are unchanged. `MissVerdict` gains `unread_fatal_errors` (additive) |
| Successor merges | Unchanged: one line in `SUCCESSOR_CHAIN` |
| Migrations, spend | No migration (head 173). The stamp lives in the existing `post_attempt_jobs.payload_json`. No paid path, no Codex or OpenRouter call: $0.00 |

### Residual found while fixing R3 (open question 7)

A probe-block attempt's diagnose job is queued at the block's end
(`probe_blocks.end_diagnostic_block`), not at the answer. A miss inside a
block of two or more observations, on an assumed or maintained LO,
therefore has no live job until the block ends. In that window it is
`not_diagnosed` (back to learning). When the block ends and the job is
queued, it waits on the diagnosis again. This was true before this stage's
fixes and was not reported. Fixing it needs placement to know that a block
is still open, or a shared "needs diagnosis" rule. Placement cannot import
`diagnosis` (frozen-cycle contract), and F10 asked not to copy that rule. It
also needs a wait base other than the first job. It arises only when a
multi-observation episode (a named calibration, an error-driven re-probe)
runs on an LO that is still assumed or in maintenance. It is left for the
owner or the next review.

### Re-review gate

The gate ran on source and tests as of `3ca612d5`. The commit after it adds
only this section.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | OK (pypdfium2 5.14.0 reinstalled after the sync) |
| `uv run lint-imports --no-cache` | **12 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7,826 passed**, 0 failed, 46 warnings (the existing Python 3.12 fork and SQLite datetime-adapter deprecations); 161.5 s. That is 9 more than round one's 7,817, one per new test case (R1 1, R2 1, R3 2, R4 5). Run with `-q -p no:cacheprovider` added (output and cache only) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **84 passed**, 7,742 deselected, 1 warning; 61.8 s |
| `npm install` (apps/learnloop-tauri) | OK (the existing notice that esbuild's postinstall is blocked by allowScripts); lockfile unchanged |
| `npm run typecheck` | **0 errors** (exit 0) |
| `npm test` (vitest) | **103 passed** in 23 files (only a `dto.ts` comment changed) |
| DB reference (`db_generate_reference.py`, `db_validate_reference.py`) | No schema change. Regenerated for the moved source anchors (`3ca612d5`): schema head **173**, **288** table notes, **599** config leaves in **35** sections, **0 errors**. `validate_vault.py`: passed (1,056 notes) |
| `cargo check` | Not run: no Rust change |
| Fail-first | On the pre-fix source (`3718eb91`) the new and extended tests failed: **11 failed**, 40 passed across `test_placement_opening_probes.py` and `test_placement_diagnosis_decides.py`. The positive controls passed on both sides |
| Tracked working vaults | Untouched (`git status` clean for `fixtures/linear_algebra`, `probability`, `arxiv_v2`). No manual run was needed: nothing here changes what the owner's data reads until a door acts or the split switch is turned off |
| Paid calls | None; $0.00 |

### Open questions added by the re-review

7. **Probe-block misses on an assumed LO** (the residual above). Should a
   miss inside a multi-observation probe block wait for the block's end
   before it is decided?
8. **Fatal errors an attribution names** (R4). They are read through that
   attribution, so an item-contract reading of a rubric fatal error keeps the
   topic. The alternative is that any fatal error returns it. Which does the
   owner want?
