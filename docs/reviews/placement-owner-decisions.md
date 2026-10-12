# Placement owner decisions (2026-10-12): Slice A Phase 6 and Slice 1 M2 OQ1

**Branch:** `fix/placement-owner-decisions`, worktree
`learnanything-placement-decisions`, from `main` at `0583648d` (Phase 6 merged
as `mvp-0.11`). Not merged, not pushed.

**What it applies.** The owner's answers (2026-10-12) to Slice A Phase 6's open
questions 1-3 (`slice-a-phase-6.md`) and Slice 1 M2's open question 1
(`slice-1-m2.md`):

| # | Owner's answer | Built as |
|---|---|---|
| M2 OQ1 | Start at the latest version | New vaults are written at `LATEST_ALGORITHM_VERSION` (`mvp-0.11` today) |
| P6 OQ2 | `q` stays 0.8 for now; a learned variable eventually | No code change; deferred with a trigger in `spec_learner_field_v1.md` §11 |
| P6 OQ3 | Let the diagnosis decide (the question may not make clear what a full answer must state) | The first-review check and lapses in maintenance return an LO to learning only on a knowledge gap |
| P6 OQ1 | Ignore unanswered opening probes | Under placement, unanswered `initial` episodes are ignored for serving and instrument generation, never rewritten |

Owner decisions in force: the spec defaults are accepted; frictionless
defaults (honest labels, generous defaults, live changes behind kill
switches, no shadow stages). Codex is exhausted until 2026-10-18: no Codex
review ran for this stage (see "Review" below).

## Amending `mvp-0.11` in place

No owner vault has been upgraded to `mvp-0.11` (the tracked working vaults are
at `mvp-0.8`), so its semantics are amended in place, as the PF-c fix amended
`mvp-0.10`. The amendment is recorded beside `PLACEMENT_ALGORITHM_VERSION` in
`src/learnloop/algorithm_versions.py`, in this file, in the Phase 6 review's
header and in `docs/algorithm-change-playbook.md` (a new paragraph: a
successor no vault has reached may be amended in place by an owner decision,
recorded beside the version and in the review; items 4 and 6-8 still apply).

Playbook check:

| Item | For this amendment |
|---|---|
| 1. New tag? | No: amended in place by owner decision (above). `RULES_VERSION` moves to `placement-rules-v3` and report 3 to `placement-report-3-v3`, so receipts and reports say which rule produced them |
| 2. Raw ledgers immutable | Yes: nothing is written by the new rules. Opening episodes are not rewritten or closed; outcomes are derived on read |
| 3. Upgrade function | Unchanged (`upgrade_to_mvp011`); the real upgrade path was run on copies (below) |
| 4. Defaults fingerprint | No default changed. Every snapshot (`mvp-0.9`, `mvp-0.10`, `mvp-0.11`) recomputes unchanged from the template rendered at its own version |
| 5. Table roles | No migration, no new table |
| 6. Replay / rebuild equivalence | The projection is untouched (placement is serving-only). Full suite and durability lane pass (gate) |
| 7. Shadow rebuild on copies | Same-version shadow at `mvp-0.11` on all three upgraded copies: 0 facet / 0 mastery / 0 schedule changes after the usual two settling rebuilds, live database hash unchanged |
| 8. Head fixture path | `test_mvp011_upgrade.py::test_head_fixture_predecessor_to_successor_path` passes unchanged |

## 1. New vaults start at the latest version

- `config/template.py`: the decision-only template is `_DEFAULT_CONFIG_TEMPLATE`
  with an `@ALGORITHM_VERSION@` placeholder; `default_config_text(version)`
  renders it and `DEFAULT_CONFIG_TEXT = default_config_text()` renders it at
  `LATEST_ALGORITHM_VERSION`. A successor merge (Slice 2 T1 `mvp-0.12`,
  practice/stuck-prompt `mvp-0.13`) moves only that constant, plus its own
  snapshot entry. The template stays at 80 lines.
- `DEFAULTS_SNAPSHOT_BY_ALGORITHM` is now defined as
  `defaults_fingerprint_for_version(version)`: the template rendered at each
  version. All three recorded snapshots recompute unchanged
  (`a9a1916d…a6f`, `ab768a5d…7af9`, `36b5b6c3…c4c9`). The tests no longer
  string-replace a hard-coded `algorithm_version = "mvp-0.9"`
  (`test_mvp010_upgrade.py`, `test_mvp011_upgrade.py`, `test_config_refactor.py`
  use the helper; the legacy-equivalence test compares the legacy text with the
  template rendered at the legacy's own version).
- Existing vaults keep their version: `init_vault` never overwrites an existing
  `learnloop.toml`, and loading, syncing or re-initialising a vault never moves
  its version; only `learnloop upgrade` does (pinned by a test).
- A new vault therefore starts with the split and placement live. Docs updated:
  the architecture vault's version note, version registry and "Initialize a
  Vault" invariant, and `docs/specs/documentation.md`'s default table.

## 2. The first review and lapses in maintenance are decided by the diagnosis

`placement/rules.py` (pure) and `placement/state.py` (reads):

- **Which misses the diagnosis decides.** A *graded miss*: no help on the
  learner's side, but short of clean full marks (or flagged for review). Its
  verdict comes from the Slice 1 M2 ledgers, read the way every other reader
  reads them (`load_miss_verdicts`): the attempt's latest blind grade, its
  latest live diagnosis (in force only when it completed for that grade), and
  the live diagnose jobs.
- **Knowledge gap → learning.** `causal_class = learner_state` on a
  `valid_measurement` attribution (any event): the LO goes back to learning
  (`failed` at the check, `missed_in_maintenance` after it). Reason
  `knowledge_gap`.
- **Kept, with the reason on the receipt.** Otherwise the topic is kept:
  - `item_contract`: an attribution with validity `item_contract` or
    `grader_interpretation` (the owner's case: the question did not make clear
    what a full answer had to state);
  - `slip`: `transient_execution` on a valid measurement;
  - `unassessed`: the answer's only shortfall is a PF-c unverified criterion
    (decided without a diagnosis; PF-c shortfalls queue none);
  - `no_gap_attributed`: the diagnoser abstained (`unknown`) or wrote no event.

  Before `first_review_due` a kept miss leaves the LO assumed
  (`Assumption.kept_answers`); from the due date on it resolves the check into
  maintenance (`status = passed`, `resolution_reason` = the reason), provided
  the existing independence rule admits the answer (otherwise it is
  ineligible and the check waits, as for a clean answer). In maintenance a
  kept miss is recorded on the intent (`LearningObjectIntent.kept_misses`) and
  the LO stays.
- **Pending: the decision waits.** While the miss's live diagnosis job is
  queued or leased (and a diagnosis can arrive), the topic stays as it was:
  the assumption stays open with `awaiting_diagnosis_attempt_id`, or the
  maintained LO stays in maintenance. No second check item is served
  meanwhile (`PlacementState.awaiting_diagnosis_learning_object_ids`, which
  the scheduler subtracts from the due set). A later "I don't know this" does
  not wait: it returns the LO. A regrade or `diagnose retry` re-queues the
  diagnosis, so the decision waits again until the new one lands.
- **No diagnosis can arrive: today's rule, said so.** Reason `no_diagnosis`
  with `MissVerdict.fallback` naming why: `split_disabled`
  (`diagnosis.split_enabled = false`, read from today's config, so a held job
  never blocks), `not_blind_graded` (a joint grade), `diagnosis_failed`,
  `diagnosis_budget_skipped`, `diagnosis_rejected`, `diagnosis_not_needed`, or
  `not_diagnosed` (none was ever queued, e.g. a full-marks answer flagged for
  review).
- **Receipts.** Outcomes stay derived on read, as Phase 6 designed (no
  migration). The receipt is the resolution: `Assumption.resolution_reason`
  and `resolution` (a `MissVerdict`: attempt, outcome, reason, fallback,
  diagnosis id, blind-grade record id, job state, and each attribution's
  `(index, validity_scope, causal_class)`), and the same on
  `LearningObjectIntent` (`outcome_reason`, `resolution`, `kept_misses`,
  `awaiting_diagnosis_attempt_id`). `learnloop placement status` prints them
  (plus `resolved_by_reason` and `awaiting_diagnosis_learning_object_ids`);
  the `get_placement_state` RPC adds `outcomeReason` and `awaitingDiagnosis`;
  the LO inspector says why a topic stayed in maintenance ("slipped, not a
  knowledge gap", "missed what the question expected", "took a route the
  grader could not check") or is waiting for the diagnosis.
- **Report 3** (`placement-report-3-v3`) counts outcomes by reason per source
  (`outcomes_by_reason`, e.g. `passed:slip`, `failed:knowledge_gap`), plus
  `passed_clean`, `kept_by_diagnosis`, `awaiting_diagnosis`,
  `fallbacks_by_reason` and `kept_early_misses_by_reason`, and a `maintenance`
  block (`kept_misses_by_reason`, `lapses_by_reason`,
  `lapse_fallbacks_by_reason`, `awaiting_diagnosis`). `first_review_miss_rate`
  is now the rate of returns to learning; a new confound names diagnoser error.

Fast-track and the quick check are unchanged: they still count only clean
answers.

## 3. Unanswered opening probes are ignored under placement

`placement/state.py`: `opening_probes_ignored(vault)` (placement active and
`placement.initial_probes = false`), `unanswered_opening_episode_ids` (an open
`initial` episode with no probe observation and no submitted presentation, the
same "answered" test as `episode_has_observations`), `servable_open_episodes`
and `episode_ignored`. The doors that read them:

- serving: the queue build (`build_due_queue`: the LO enters as new material
  instead of behind the episode, and no probe EIG is scored), the desktop probe
  contract (`get_probe_contract`) and the TUI practice screen (an ignored
  in-progress episode is neither served nor parked), and the post-attempt
  intervention policy's `probe_phase_active`;
- instrument generation: the empty-pool sweep (no generation need, no
  "probe pool empty" notice), `learnloop probe-instances`, and an unscoped
  calibration session's default scope (naming the LO still uses its episode).

Nothing rewrites or closes an episode, so `placement.enabled = false` restores
today's behaviour exactly, and `placement.initial_probes = true` serves the
opening probes again.

**Proof on backup-API copies** (`fixtures-local/placement-decisions/`, made with
`copy_tree_with_databases` from the worktree's tracked `linear_algebra`,
`probability` and `arxiv_v2`; each taken through the real owner path: `doctor
--fix-state`, `upgrade --to mvp-0.9`, then `upgrade` (to `mvp-0.11`), or
`upgrade --to mvp-0.10` for the predecessor; queue built at 2026-10-12T09:30Z):

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Open opening episodes, all unanswered (ignored with placement on) | 9 | 18 | 31 |
| `placement.enabled = false` vs `mvp-0.10`: episodes, queue items, priorities, components, order | identical | identical | identical |
| `placement.initial_probes = true` vs `mvp-0.10` | identical | identical | identical |
| Placement on: episodes (id, status) unchanged | yes | yes | yes |
| Placement on: same queue items as `mvp-0.10` | 41 = 41 | 67 = 67 | 32 = 32 |
| Never-practised LOs the predecessor served behind an opening episode | 1 | 17 | 28 |
| ... of which now start as learning (`new_material`) | 1 | 17 | 28 |
| New-material items | 1 | 64 | 28 |
| Queue fingerprint (sha256/12) `mvp-0.10` / off / on | `26b4b0c81220` / `26b4b0c81220` / `c2573b22d39c` | `e93a08d0505e` / `e93a08d0505e` / `d3e12644bfcf` | `4c8a2f89cb34` / `4c8a2f89cb34` / `94798064ab55` |

The other never-practised LOs have no practice item yet (12 in
`linear_algebra`, 3 in `arxiv_v2`); 8 of `linear_algebra`'s 9 ignored episodes
sit on LOs that were already practised (their items are served as before).
The same result holds when the versions are set directly in the config
(`test_placement_fixture_copies.py`, which runs it on every suite run).

Also on the upgraded copies: `placement status` is active with nothing
assumed; report 3 v3 runs (0 decisions; new LOs 13 / 17 / 31); a
same-version shadow rebuild after two settling rebuilds is 0/0/0 with the
live database hash unchanged (the first shadow straight after the upgrade
shows the pre-existing first-rebuild drift Phase 6 and M2 recorded:
version-stamped mastery rows and schedule rows, identical at `mvp-0.10`).
`doctor` reports the vaults' existing content errors
(`criterion:unknown_dependency`) before and after the upgrade.

## 4. `q` stays 0.8; a learned parameter later

`placement.fast_track_q` stays 0.8 (no default change). `spec_learner_field_v1.md`
§11 now defers a learned `q` (per source, fitted to a target first-review miss
rate from the active predictor's `P(θ_L > θ_known)`), triggered when report 3
has at least 30 resolved first reviews for the source being tuned whose
decisions recorded `p` (a 95% Wilson interval of about ±0.15 or narrower). A
fitted `q` is a default change and takes a version or fingerprint decision.
D6 and D11 in §10 and §5.2 carry the decisions.

## 5. Records

- `docs/reviews/slice-a-phase-6.md`: header note on the amendment; open
  questions 1-3 marked decided (4 stays open; 5 is the DL1 note); the
  "new vaults stay at `mvp-0.9`" integration bullet marked superseded.
- `docs/reviews/slice-1-m2.md`: open question 1 marked decided; the
  "template stays at `mvp-0.9`" line marked superseded.

## Interpretations (flagged for the owner)

1. **Learner-side help keeps today's rule.** Hints, priming, "don't know",
   assistance, a walkthrough reconstruction or a teach-back on an assumed or
   maintained LO still return it to learning (reason `learner_side`), whatever
   a diagnosis of the written errors says. The owner's question was about
   partial credit; the diagnosis explains graded errors, not a request for
   help. One line to change if the diagnosis should decide these too.
2. **An unassessed answer at the check now resolves it into maintenance**
   (Phase 6's merge had made it ineligible, the check waiting). Before the due
   date it leaves the LO assumed.
3. **`no_gap_attributed` keeps the topic.** A diagnosis that abstains, or a
   blind grade with a shortfall but no attribution, is not a knowledge gap.
   Report 3 counts these separately so they can be watched.
4. **A kept miss must still pass the independence rule** to resolve the check
   (a post-reveal answer is ineligible and the check waits), as a clean answer
   must.
5. **`due_learning_object_ids` is unchanged** (an assumption whose check
   answer awaits its diagnosis is still open and due); the scheduler subtracts
   the new `awaiting_diagnosis_learning_object_ids`. DL1 can do the same to
   count checks still to serve.
6. **What "ignored" does not touch.** An ignored opening episode still
   occupies its LO's one open-episode slot, so an error-driven re-probe on that
   LO stays blocked exactly as before (where the opening episode stood in for
   it); closing it would break the kill switch's exactness. The staged
   controller's robust-value signal, the routine planner's shadow log and the
   completion route's applied-episode record still see it (none serves or
   generates). On the three fixtures every opening episode is `pending_items`,
   so none of these is reached.

## Tests

Fail-first: every new or changed test file below was run against the base
source (`git checkout 0583648d -- src/`, keeping only the new pure
`placement/rules.py` so the new test modules import), then the source was
restored: **30 failed, 2 collection errors, 119 passed** (the passes are the
files' unchanged tests and the two pure-rule tests).

| File | Covers | Against the base source |
|---|---|---|
| `test_config_refactor.py` (+5: latest-version template, every recorded snapshot via the helper ×3, chain coverage; legacy-equivalence test reworked) | Item 1 | collection error (no `default_config_text` / `defaults_fingerprint_for_version`) |
| `test_mvp011_upgrade.py` (new-vault test rewritten, +1 existing vaults keep their version, snapshot via the helper), `test_mvp010_upgrade.py`, `test_ai_config.py` (2 changed), `test_assumed_known.py` (new vaults start with placement on) | Item 1 | 6 failed (new vaults at `mvp-0.9`; no helper) |
| `test_placement_opening_probes.py` (6) | Ignored for serving (queue, probe contract, no parking), for generation (sweep, notices, `probe-instances`, unscoped calibration); an answered episode is not ignored; both switches restore the predecessor exactly | collection error; with only the new helpers present, 4 behavioural failures (no new material, the starved episode still a condition) |
| `test_placement_fixture_copies.py` (+3; the kill-switch test also pins `initial_probes = true`) | Item 3 on copies of the three working fixtures | 3 failed (no LO started as learning) |
| `test_placement_diagnosis_decides.py` (17) | Knowledge gap → learning; slip, item contract, grader interpretation, no gap → maintenance with the reason; an early kept miss stays assumed, an early gap returns it; pending waits (no second check) but a return does not; split disabled, diagnoser failed, budget-skipped, joint grade → today's rule with the fallback named; learner-side help; the M2 vocabulary; lapses in maintenance (kept, pending, gap); kill switch; report 3 by reason | 15 failed (`failed`/`learning` where `passed`/`maintenance` or `open` expected; no receipts; report v2); the 2 pure-rule tests pass |
| `test_placement_split_grades.py` (4 rewritten, 1 extended) | Unassessed at the check keeps maintenance (reason `unassessed`); a located error waits for, then follows, its diagnosis; a regrade re-queues it; a regrade to unverified keeps maintenance; a kept miss in maintenance is recorded | 5 failed |
| `test_placement_sidecar.py` (1 extended) | `outcomeReason`, `awaitingDiagnosis` on the RPC | 1 failed |
| `test_teach_back.py` (1 adapted) | A new vault's teach-back is now graded blind, so the double serves both contracts | (passes either way) |
| Vitest `PlacementControls.test.tsx` (+1) | Honest maintenance and waiting labels | (labels absent) |

## Paid calls and spend

None. No model route, no Codex call (exhausted), no OpenRouter call: $0.00.
The stage has no paid command; the manual runs above are read-only or
serving-only on backup copies. No tracked working vault was read directly or
written (`git status` clean for `fixtures/linear_algebra`, `probability`,
`arxiv_v2`). The Eedi dataset the owner downloaded is for another stage and was
not opened here.

## Review

No Codex review ran (Codex exhausted until 2026-10-18). The stage's own
review found one defect before the gate, fixed with a test: a learner's "I
don't know this" after a check answer whose diagnosis was still pending left
the assumption open (its items withheld) instead of returning the LO
(`0abe2da3`).

## Gate

GATE_PLACEHOLDER

## Open questions

1. Interpretation 1: should the diagnosis also decide misses with learner-side
   help (hints, priming, "don't know")?
2. Interpretation 3: should `no_gap_attributed` (the diagnoser abstained, or a
   shortfall with no attribution) keep the topic, or fall back to today's rule?
3. A pending diagnosis that never lands while the split is on (provider never
   ready) keeps the decision waiting indefinitely. Add a time-out (say 7 days)
   after which today's rule applies?
4. Phase 6 open question 4 (the quick check on the import result) is still
   open.
