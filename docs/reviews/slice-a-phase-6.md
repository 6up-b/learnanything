# Slice A Phase 6: starting new material without ceremony (learner field F2)

> **Integration note (merge into main, 2026-10-12, merge branch
> `merge/phase-6` from `f948926d`).** Main had gained Slice 2 T7, Phase 5b
> (migration 169), Slice 1 M2 (migration 170, which already owns `mvp-0.10`:
> the blind-grading/diagnosis split), mobile M1 (171), Slice 2 T8 and T4.
> Where this record and the review file say otherwise, this note is current.
>
> - **Algorithm version `mvp-0.11`, a linear chain.** Phase 6's successor is
>   relabelled `mvp-0.11` and means `mvp-0.10`'s split **plus** placement:
>   `mvp-0.9 -> mvp-0.10 -> mvp-0.11`. `DIAGNOSIS_SPLIT_VERSIONS` is
>   `{mvp-0.10, mvp-0.11}`, `PLACEMENT_VERSIONS` is `{mvp-0.11}`, and
>   `P0_SUCCESSOR_VERSIONS` holds all three successors. Every other gate was
>   already set membership. `LATEST_ALGORITHM_VERSION = mvp-0.11`.
> - **Upgrade.** `upgrade_to_mvp010` is renamed `upgrade_to_mvp011`. It
>   accepts `mvp-0.10`, or `mvp-0.9` by running M2's `upgrade_to_mvp010` first
>   (if the second link then failed, the vault would be left at the valid
>   `mvp-0.10`). It freezes the `mvp-0.10` manifest, rebuilds the unchanged
>   projection and renames the config atomically. `learnloop upgrade` with no
>   `--to` targets `mvp-0.11`; `--to mvp-0.10` still reaches the split alone.
> - **New vaults stay at `mvp-0.9`.** Phase 6's template change to `mvp-0.10`
>   is undone: moving the template is the owner's Slice 1 M2 open question 1.
>   Placement reaches a vault only through `learnloop upgrade`.
> - **Defaults fingerprints.** `[placement]` (eight modelled defaults, not in
>   the 80-line decision-only template) changes the effective config of every
>   version, so `DEFAULTS_SNAPSHOT_BY_ALGORITHM` was recomputed for `mvp-0.9`
>   (`f4d980dd…f786`), `mvp-0.10` (`d35af8a4…8deb`) and `mvp-0.11`
>   (`736a92f1…77e7b2`); the two successors are `DEFAULT_CONFIG_TEXT` with only
>   `algorithm_version` replaced (`test_mvp011_upgrade.py` pins `mvp-0.11`).
> - **Migrations 172 and 173.** Phase 6's 169 and 170 are renumbered 172
>   (`placement_assumptions`) and 173 (`placement_quick_check_presentations`),
>   content unchanged (only their header comments say `mvp-0.11`).
>   `fixtures/migration_head_173` is a backup-API copy of main's
>   `migration_head_171` with only 172 and 173 applied (rollback journal,
>   integrity ok, FK-clean); Phase 6's own head fixtures are dropped. References
>   regenerated: schema 173, 288 table notes, 592 config leaves in 34 sections.
> - **Grades under the split.** Placement reads the attempt row, where a blind
>   grade lands like a joint one and a regrade (which re-queues the diagnosis)
>   rewrites it in place. PF-c unverified criteria are no failure evidence: an
>   answer whose only shortfall is on criteria the valid-alternative gate
>   recorded unverified is *unassessed* (`AnswerFacts.unassessed`): never a
>   pass, never a miss (ineligible at the check, not a lapse in maintenance),
>   and skipped by fast-track and the quick check. A located error on a
>   verified criterion is still a miss. `test_placement_split_grades.py`.
> - **Shared exclusions.** `scheduling.serving_exclusions` now also carries the
>   two rules Phase 5b's `find_practice` applies outside the scheduler's timing
>   (an open cold follow-up's reserved item, an item revealed within the cold
>   retrieval delay); `find_practice` admission, the quick check and the
>   first-review check-item choice read them from there. `find_practice` also
>   refuses a reference-adopted card while `tutor_qa.adopt_reference_questions`
>   is off, as every serving door already did. M2 withholds no item (its
>   diagnosis only delays the next queue build).
> - **Desktop and mobile.** The practice card, LO inspector, map and
>   calibration screen carry Phase 6's controls beside M2's diagnosis card,
>   mobile's Inbox strip and T7's map neighbours; the "assumed (not tested)"
>   label never reads into depth or beads (vitest unchanged). The three new
>   RPCs are pinned as never phone-allowed (`test_mobile_allowlist.py`, used by
>   `test_mobile_host_auth.py`).
> - **Proof on backup copies** of `linear_algebra`, `probability` and
>   `arxiv_v2` (`fixtures-local/`), main's code (`f948926d`) against the merge:
>   at `mvp-0.9` and `mvp-0.10` the opening episodes, the queue (items,
>   priorities, components, order), the same-version shadow diff and every
>   DERIVED row after two rebuilds are identical; `mvp-0.11` with
>   `placement.enabled = false` is identical to main's `mvp-0.10` except the
>   `algorithm_version` stamp. Through the real upgrades (`--to mvp-0.9`, then
>   the default chained upgrade) every copy reaches `mvp-0.11` with a 0-change
>   same-version shadow, and the candidate shadow `mvp-0.10 -> mvp-0.11` has 0
>   semantic changes (version stamps only).
>
> **Superseded in part by the Codex review fixes** (`slice-a-phase-6-codex-review.md`,
> 2026-10-12): a passed check keeps the LO in maintenance with its remaining
> learning items withheld; nothing routine is served before the check date;
> the check and fast-track use the existing independence rule; quick checks
> honour the shared serving exclusions, bind only their own presentations and
> start atomically (migration 170); learner placement verdicts append to
> `judgment_ledger`; report 3 counts unique learning obligations. Where this
> record disagrees, the review file is current.

**Branch:** `slice-a/phase-6`, worktree `learnanything-phase-6`, from `main` at
`974c5647` (Phase 2, Phase 3, the daily-loop bug fixes and follow-ups, and the
Slice A 2-3 integration and its Codex re-review). Not merged, not pushed.

**Owner checkpoint on reports 1-2:** counted as done for this stage, with the
incumbent `mastery_ekf` kept (report gates are post-hoc,
`implementation_goal.md` §1a).

## Plan (written before coding)

### Files to add or change

- `algorithm_versions.py`: `PLACEMENT_ALGORITHM_VERSION = "mvp-0.10"`, a P0
  successor tag (the projection is unchanged; serving changes), and
  `PLACEMENT_VERSIONS`.
- `config/schema.py`, `config/template.py`: a `[placement]` section
  (`enabled`, `initial_probes`, `assumed_first_interval_days`,
  `fast_track_min_correct`, `fast_track_q`, `known_probability`,
  `quick_check_k`, `quick_check_budget_minutes`). New vaults start at
  `mvp-0.10`. Fingerprint keyed by the new version; parameter registry rule.
- New package `learnloop/placement/` (consumers of the `LearnerPredictor`
  interface only):
  - `state.py`: is placement active; open, resolved and returned assumptions;
    per-LO status (`assumed`, `learning`, `untested`); due first-review checks;
    the new-material order (prerequisite layer, help/confusion first,
    predicted success, id);
  - `predictor.py`: the live incumbent, an adapter that serves the
    `LearnerPredictor` contract from the persisted per-LO EKF state
    (`mastery_ekf`), and `P(θ_L > θ_known)`;
  - `rules.py`: the clean-correct predicate and the fast-track rule, sharing
    `field.signals.blocks_fast_track` with report 2;
  - `decisions.py`: self-report ("I know this", "too easy", "I don't know
    this"), fast-track reconciliation, and receipts;
  - `report.py`: report 3.
- `db/stores/placement.py` (the only SQL writer for the new tables).
- `substrate/state_sync.py`: `_enter_initial_probes` runs only when placement is
  inactive or `placement.initial_probes = true`.
- `scheduling/scheduler.py`: under placement, never-attempted LOs enter as new
  material (instead of through an opening episode), assumed LOs' never-attempted
  items are withheld, a due assumed-known first review is admitted as a check,
  and new-material items are reordered among the slots they already hold.
  Fast-track reconciliation runs before the build on the persisting path.
- `content/authoring/item_authoring.py`: a `too_easy` retirement also marks the
  LO assumed known when placement is active.
- `diagnosis/quick_check.py`: "Check what I already know" over
  `start_calibration_session`, k ≤ 4 answers, 8-minute budget, early stop,
  results at the end, results feeding the split.
- `ops/vault_upgrade.py`, `cli/app.py`: `upgrade_to_mvp010`, `learnloop upgrade
  --to mvp-0.10`.
- `cli/placement.py`: `learnloop eval placement` (report 3) and
  `learnloop placement status`.
- Sidecar: `placement_self_report`, `get_placement_state`, `start_quick_check`;
  quick-check progress through `get_calibration_session`; `assumed` on the map's
  facet points and on the LO inspector.
- Desktop: Tauri passthroughs, client and DTOs; "I know this" on the practice
  screen; the LO inspector's placement section (label, "I know this", "I don't
  know this", "Check what I already know"); the well view's outlined
  "assumed (not tested)" bead; the calibration screen's quick-check results.

### Migrations

One migration at the next free number (169 at the time of writing):
`assumption_decisions` (RECEIPT), `assumption_returns` (RECEIPT, "I don't know
this"), `placement_quick_checks` (WORKFLOW). Head fixture renamed and upgraded,
references regenerated.

### Algorithm successor and kill switch

`mvp-0.10` with kill switch `placement.enabled`. Placement acts only on a vault
at `mvp-0.10` with the switch on. With the switch off, initial probes, serving
and ordering are those of `mvp-0.9` (G9). The upgrade refuses jumps, freezes
the `mvp-0.9` manifest, rebuilds the unchanged projection, then renames the
config atomically. Existing open episodes are not closed, so the kill switch
restores them unchanged.

### Spend caps and model routes

None. Phase 6 makes no model calls. Quick checks pass `generate_missing=False`,
so no paid instrument generation runs from them.

### `judgment_ledger` writes

None: no LLM, verifier or owner verdict is produced. Self-reports, fast-track
and quick-check decisions are receipts in `assumption_decisions`.

### Tests

`test_assumed_known.py`, `test_placement_signals.py` (the §9 interaction-signal
routing items and G13), `test_quick_check.py`, `test_placement_upgrade.py`,
`test_placement_report.py`, sidecar RPC tests and the map test; vitest for the
labels and buttons; durability-lane coverage of the new tables on a fresh vault.

---

## What was built

### The successor and its kill switch

- **`mvp-0.10`** (`algorithm_versions.PLACEMENT_ALGORITHM_VERSION`) is a P0
  successor tag: the projection is unchanged, only serving changes. It joins
  `P0_SUCCESSOR_VERSIONS`, so every "is this the P0 projection?" gate keeps
  working. Placement serves only at a version in `PLACEMENT_VERSIONS` with
  `placement.enabled = true` (`placement.state.placement_active`).
- **Upgrade.** `ops.vault_upgrade.upgrade_to_mvp010` refuses anything but
  `mvp-0.9`, freezes the `mvp-0.9` manifest, rebuilds the unchanged
  projection, refreshes the registry, then renames the config atomically.
  `learnloop upgrade` now defaults to `--to mvp-0.10`. Nothing is rewritten:
  episodes already open stay open, so the kill switch restores them exactly.
- **New vaults** start at `mvp-0.10` (template). `[placement]` is not written
  into the decision-only template (its 80-line budget); all eight leaves are
  modeled defaults (`learnloop config effective` shows them). Fingerprint
  `94d7a3e9…f65b` is keyed under `mvp-0.10`; `mvp-0.9`'s stays.
- **Config `[placement]`:** `enabled = true`, `initial_probes = false`,
  `assumed_first_interval_days = 14`, `fast_track_min_correct = 2`,
  `fast_track_q = 0.8`, `known_probability = 0.75` (θ_known = logit .75),
  `quick_check_k = 4`, `quick_check_budget_minutes = 8`. The four routing
  thresholds are registered as decision thresholds, the two quick-check
  bounds as operational, in the parameter registry.

### Serving (`substrate/state_sync.py`, `scheduling/scheduler.py`)

With placement on:

1. **No opening probe per new LO.** `_enter_initial_probes` runs only when
   placement is off or `placement.initial_probes = true`. Error-driven
   diagnosis (`maybe_reprobe_for_misconception`, stale-uncertainty re-probes,
   causal episodes, learner-started calibration) is untouched.
2. **New material starts as learning.** A never-attempted item on an LO with
   no direct evidence, no open episode and no goal frontier (the population
   the predecessor admitted through an opening episode) is admitted with the
   same 0.05 floor the opening episode gave it, component `new_material`,
   reason "new material: starts as learning, no opening probe".
3. **Order.** After the existing sort, new-material items are reordered
   *among the slots they already hold*: prerequisite layer (declared
   `prerequisites` concepts and `prerequisite` edges, direction respected;
   cycles broken deterministically), then LOs with help or confusion signals
   (taught first, reason "taught first: you asked about this topic or needed
   help on it"), then the active predictor's predicted success, easiest first,
   then item id. Every other item keeps its position, so Today's composition
   (goal quota, requested floor, follow-ups, exploration) is unchanged.
4. **Assumed known (not tested).** An open assumption withholds its LO's
   never-attempted items, except learner-requested ones. Items that already
   have memory state keep their normal reviews (maintenance). When the first
   review falls due, one check item is admitted (component `assumed_check`,
   reason "first review of a topic assumed known (not tested): this is the
   check"): a never-seen ordinary item with the median predicted success,
   ties by id, never a diagnostic probe or a teach-back.
5. **Back to learning.** An LO whose latest assumption failed its check or
   was returned by "I don't know this" has its never-attempted items admitted
   as new material again.
6. **Fast-track runs first** on the persisting queue path (the one that
   always follows an attempt), so an LO it assumes stops being served as new
   material in the same build.

With placement off (or at `mvp-0.9`), none of this runs: `placement_serving`
is `None` and every branch is the predecessor's.

### Decisions (`learnloop/placement/`)

Consumers of the `LearnerPredictor` contract only (G10, import-linter):

- `predictor.py`: `LiveMasteryPredictor` serves the incumbent `mastery_ekf`
  from the persisted per-LO EKF posterior (`predict_item`,
  `region_estimates`, `conditional_gain`); `cross_lo_sharing = False`.
  `active_predictor` refuses any other name until Phase 4 adds one.
- `rules.py`: the pure fast-track predicate. An answer is clean when it is an
  independent, free-text, diagnostic-probe or exam answer with full marks, no
  hints, not primed, not "don't know", not flagged for manual review, and not
  in an assisted contamination class. Fast-track fires when every answer so
  far is clean, there are at least `fast_track_min_correct`, no signal blocks
  the LO (`field.signals.blocks_fast_track`, report 2's own rule), and
  `P(θ_L > θ_known) ≥ q` (report 2's arithmetic).
- `signals.py`: the field's interaction-signal derivation over the live
  ledgers (question time mapping and the `no_draft` help-before-work marker
  as integrated); read only (G13).
- `decisions.py`: `record_self_report` ("I know this", "too easy", "I don't
  know this"), `reconcile_fast_track`, `reconcile_predictor_assumptions`
  (cannot fire under the incumbent), the quick check's split, and finalizing
  a quick check abandoned past its budget.
- `state.py`: assumptions and how each resolved (`open`, `passed`, `failed`,
  `returned`), joined from `practice_attempts`, never written back.
- `report.py`: report 3.

**Receipts (G8).** `assumption_decisions` rows carry the LO, source,
trigger, `p`, the 80% θ interval, `q_used`, θ_known, predictor and version
hash, first-review due date, quick-check session, algorithm version, the
placement config in force and every input the rule read (answers with their
facts, blocking signal ids, the region). A test replays a stored receipt
through the predicate and gets the same decision.

**Nothing assumed writes evidence (G7).** Tests snapshot `practice_attempts`,
`grading_evidence`, `learning_object_mastery`, `facet_recall_state`,
`facet_capability_evidence`, `practice_item_state`, `coldness_receipts`,
`learner_claims`, `certification_cold_probe_outcomes` and `error_events`
around every placement action. A "too easy" retirement keeps its
pre-existing self-rating claim; the assumption adds nothing to it.

### The quick check (`diagnosis/quick_check.py`)

"Check what I already know", never prompted, from the LO inspector:

- `start_calibration_session(learning_object_ids=…, time_budget_minutes=8,
  generate_missing=False, open_episodes=False)`, plus a
  `placement_quick_checks` row. No diagnostic episode is opened and no
  instrument is generated, so no paid call and no opening probe survives it.
- Up to k = 4 ordinary never-seen items, one at a time, chosen by the active
  predictor's `conditional_gain` over the undecided LOs (with the incumbent,
  the plain per-LO information), ties by id.
- Early stop when every LO is decided (a non-clean answer decides
  "learning"; enough clean answers above q decide "assumed"), at k answers,
  at the budget, or on Stop.
- Results are withheld until it ends: progress carries only counts, the
  desktop returns each answer straight to the check, and at the end the
  screen lists each topic's verdict and every answer with its feedback.
- The split writes `quick_check` receipts for assumed LOs, once. A check the
  learner walks away from is finalized by the next queue build after its
  budget.

### Report 3 and commands

- `learnloop eval placement --vault <copy> --output-dir <dir>`: first-review
  miss rate by source with Wilson intervals, resolved on schedule vs early,
  returns to learning (missed checks, "I don't know this"), items not served
  as new material and estimated minutes saved against the minutes of learning
  every new LO (median answer latency, else a flat 3 minutes per item), named
  confounds. Aggregates only, content-addressed files, read-only.
- `learnloop placement status --vault <v> --json`: open assumptions and due
  dates.

### Sidecar and desktop

- RPCs `placement_self_report`, `get_placement_state`, `start_quick_check`;
  `get_calibration_session` and `stop_calibration_session` add a quick
  check's own target, counts and (at the end) results. All four bridge
  layers are wired; `test_desktop_rpc_contract.py` passes.
- Map: facet points gain `assumed` and `assumedLearningObjectIds`, item points
  `assumed`, and the payload a `placement` block. Empty while placement is
  off.
- `KnowledgeWellView`: an assumed, untested facet is a dashed purple outline
  labelled "assumed (not tested)"; a tested facet on an assumed LO gets an
  outer dashed ring. Depth, ghosts and demonstrated beads never read the
  flag (G6 vitest).
- The map side panel labels assumed facets and LOs; the LO inspector has a
  "Starting point" section (label, first-review date, "I know this" or "I
  don't know this", "Check what I already know"); the practice card shows
  "✓ I know this" while placement is on; `CalibrationScreen` has a quick-check
  view.

## Deviations and decisions

1. **The quick check is not on the import result.** No single surface lists
   the LOs an import or study-map apply created (they arrive through ingest
   batches). It is on every LO's inspector instead (open an LO from the map
   or the inspector's search).
2. **Quick-check reveal.** Grading stays synchronous (P7). The check withholds
   results and feedback in the desktop flow until it ends. No `reveal_events`
   rows are written at the end: that ledger records answer exposure *before*
   an attempt on an item, and each quick-check item is answered once.
3. **Existing opening episodes are kept.** The successor stops opening them;
   it does not close the ones earlier versions opened, so the kill switch is
   exact. On the three tracked fixtures every never-practised LO already
   carries one (9/21, 18/18 and 31/34 LOs have open `initial` episodes, all
   `pending_items`, none observed). Their queues are therefore unchanged
   until new material arrives (open question 1).
4. **Fast-track with the incumbent needs more than two answers.** With the
   cold-start prior variance 3.0, `P(θ_L > logit .75) ≥ 0.8` takes about 4
   (harder items) to 6 (medium items) consecutive clean full-marks answers;
   the two-answer floor rarely binds. Constants are a priori (D6) and were not
   tuned. D6's parenthetical says 0.9 "if report 2 lacked data"; the handoff
   prompt states P ≥ 0.8, so 0.8 ships (open question 2).
5. **First-review pass = a clean full-marks answer,** the complement of
   report 2's miss (`outcome < 1`). Partial credit, hints, priming or "don't
   know" return the LO to learning (open question 3).
6. **Live rows, report-2 rule.** Live fast-track reads `practice_attempts`
   rather than the strict replay outcome view, which excludes multi-facet and
   pre-snapshot revisions for facet attribution that fast-track does not need.
   The predicate and the signal blocking rule are report 2's.
7. **Taught first within a prerequisite layer,** never ahead of an unlearned
   prerequisite.
8. **"I don't know this" on an LO that is not assumed** records a return with
   no assumption id: the LO stays learning and is never fast-tracked.
9. **Import-linter:** two edges into the field's pure leaf modules are exempt
   from the frozen-cycle contract (`placement.* -> field.types`,
   `placement.signals -> field.signals`); both modules import only the
   standard library and `field.types`. `field-consumers-use-interface` now
   covers the placement package, the quick check, the scheduler and the
   sidecar placement handler, and also forbids `field.evaluation` and
   `field.memory`.
10. **Version tags after upgrade.** Right after `learnloop upgrade`, a
    same-version shadow rebuild still reports the per-LO mastery rows'
    `algorithm_version` tag (21/18/34 rows, zero semantic change) until the
    next `rebuild-derived-state`. The `mvp-0.9` upgrade does the same
    (checked on a fresh copy); it is pre-existing.
11. **Rust not compiled here.** `cargo check` fails before compiling project
    code (`rustc: symbol lookup error … LLVM_23.1`, the environment issue
    Phase 2 recorded). The three passthroughs use the existing macro; the
    static bridge contract test passes.

## Paid calls and spend

None. No model route, no `judgment_ledger` write, $0.00. Replay and rebuild
make zero model calls (durability test with model constructors forbidden).

## Migrations

`169_placement_assumptions.sql`: `assumption_decisions` (RECEIPT),
`assumption_returns` (RECEIPT), `placement_quick_checks` (WORKFLOW). Classified
in `db/table_roles.py`; no DERIVED table, so no replayer. Head fixture renamed
to `fixtures/migration_head_169` (backup-API copy upgraded through 169,
`journal_mode=DELETE`, integrity ok, FK-clean, no WAL companions); README and
the five hard-coded paths updated. DB/config references regenerated: schema
169, 269 table notes, 553 config leaves in 31 sections, 0 validation errors.
Expect renumbering at merge.

## Manual runs (backup-API copies under `fixtures-local/`)

Copies of `linear_algebra`, `probability` and `arxiv_v2` (`phase6-*`), each
`doctor --fix-state`, `upgrade --to mvp-0.9`, two `rebuild-derived-state`
(the fixed point the integration found), then:

| Check | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Same-version shadow at `mvp-0.9` (facet/mastery/schedule rows) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| Candidate shadow `--set algorithms.algorithm_version=mvp-0.10` | 79 / 21 / 0 rows, **0 semantic** (version tag only) | 2 / 18 / 0, **0 semantic** | 6 / 34 / 0, **0 semantic** |
| Source database SHA-256 across shadows | unchanged | unchanged | unchanged |
| `learnloop upgrade` (default target) | mvp-0.9 → mvp-0.10 | same | same |
| `placement status` after upgrade | active, nothing assumed | same | same |

On `phase6-probability`, "I know this" on a never-practised LO
(`lo_apply_inclusion_exclusion_to_overlapping_events`) removed its 5 new items
from a 67-item queue; the other 62 kept their order. Report 3 on that copy:
1 open self-report, 15 estimated minutes saved of 192 for 17 new LOs.
`test_placement_fixture_copies.py` pins the kill-switch equivalence on all
three copies (episodes, queue, priorities, components and order).

## Tests

| File | Covers |
|---|---|
| `tests/test_assumed_known.py` (21) | No initial episodes by default; new material admitted and ordered; error-driven episodes still open; `initial_probes` switch; **G9** kill switch equals `mvp-0.9` and ignores assumptions made while on; each source marks the LO and schedules the check (self-report, "too easy", fast-track, predictor impossible under the incumbent); fast-track needs the minimum and the threshold, blocked by any unclean first answer; a missed check or "I don't know this" returns the LO to learning, a pass keeps it in maintenance; **G7** evidence tables unchanged; **G8** receipt recomputes its decision; deterministic check item; durability-lane receipts survive two rebuilds with model constructors forbidden |
| `tests/test_placement_signals.py` (5) | Reader confusion blocks fast-track and teaches the LO first; "I know this" still assumes; curiosity carries no negative signal; help before starting (`no_draft`) and suspected leaks block; **G13** with and without the question, evidence is identical and only routing differs |
| `tests/test_quick_check.py` (10) | A calibration session without episodes (8 min, k = 4); conditional-gain selection, deterministic; results withheld until the end, then fed to the split (`quick_check` receipt, once); a wrong answer decides learning and a decided LO is never asked again; k ends it; Stop still feeds the split; fast-track waits for an open check; never prompted; needs placement; an abandoned check is finalized after its budget |
| `tests/test_placement_upgrade.py` (4) | Successor sets; upgrade flips, rebuilds, keeps history and open episodes; refuses jumps; CLI default |
| `tests/test_placement_report.py` (3) | Report 3 by source (passed/failed/returned, on schedule, Wilson CI, returns, minutes); aggregate-only and read-only (DB hash unchanged); `placement status` |
| `tests/test_placement_sidecar.py` (4) | Self-report RPC by item and inspector block; honest refusal while off; quick-check RPCs withhold results; **G4/G6** map labels assumed points without changing any other field |
| `tests/test_placement_fixture_copies.py` (3) | **G9** on backup-API copies of the three working fixtures, plus "no episode opened" with placement on |
| Vitest `PlacementControls.test.tsx` (4), `CalibrationScreen.test.tsx` (2), `KnowledgeWellView.test.tsx` (+2), `PracticeScreen.test.tsx` (+2) | The "assumed (not tested)" labels and the "I know this", "I don't know this", "Check what I already know" and quick-check controls; the well's G4/G6 for the assumed label |

Changed existing tests: `test_ai_config.py` and `test_mvp09_upgrade.py`
(new vaults and the CLI default now reach `mvp-0.10`; mvp-0.9 is still
reached explicitly), `test_sidecar_contract.py` (item points gain
`assumed`), `test_architecture.py` (the placement store is a registered SQL
owner), the three head-fixture paths, and the CLI help snapshot.

## Owner commands

Run on a backup-API copy first (Phase 2's copy recipe in
`slice-a-phase-2.md` works unchanged), then on the live vault when satisfied.
Never on the tracked fixtures.

```bash
# Upgrade (refuses anything but mvp-0.9). A vault still at mvp-0.8 runs
# `--to mvp-0.9` first. Afterwards, optionally retag the per-LO mastery rows:
uv run learnloop upgrade --to mvp-0.10 --vault "$VAULT"
uv run learnloop rebuild-derived-state --vault "$VAULT"

# What is assumed known right now, and when each first review is due:
uv run learnloop placement status --vault "$VAULT" --json

# Report 3 (read-only, aggregates only), after a few imports and first reviews:
uv run learnloop eval placement --vault "$COPY" --output-dir fixtures-local/reports/placement

# Kill switch: restores the opening probes, serving and ordering of mvp-0.9 and
# ignores recorded assumptions. Add to the vault's learnloop.toml:
#   [placement]
#   enabled = false
# Narrower: keep assumed-known but bring the opening probes back:
#   [placement]
#   initial_probes = true
```

### What to watch in the first weeks

- **Report 3's miss rate by source.** Self-reports and fast-tracks that miss
  their first review return to learning quietly; a high self-report miss rate
  says "I know this" is too generous for you, a high fast-track miss rate says
  q or the answer floor should rise (D6: tune from report 3).
- **How rarely fast-track fires.** Expect it to need four to six clean answers
  in a row with the incumbent (deviation 4). If it never fires, that is the
  incumbent's honest uncertainty, not a bug.
- **Early versus on-schedule checks.** Many early resolutions mean
  goal-frontier or requested serving reached the LO before day 14.
- **New imports.** Placement is invisible on existing LOs (deviation 3); it
  shows when new material arrives: no "probe queue" entries for it, new items
  in prerequisite order, and "taught first" on topics you asked about.
- **Opening episodes left from before.** If the pending opening episodes on
  existing LOs bother you (they can commission instrument generation when an
  authoring route is set), say so (open question 1).

## Open questions

1. **Close untouched opening episodes?** Existing `initial` episodes with no
   observation stay open under `mvp-0.10` (all `pending_items` on the tracked
   fixtures). Option: under placement, treat an unobserved opening episode as
   not open for serving and generation, without rewriting it (the kill switch
   stays exact). Not built: it changes serving beyond the spec text.
2. **D6's q.** 0.8 ships per the handoff prompt. D6 recommends 0.9 if report
   2 lacked data, and on the tracked `linear_algebra` copy it did (no later
   attempts under either revision policy). `placement.fast_track_q = 0.9` is
   a one-line config change (a default change needs a fingerprint decision).
3. **First-review pass criterion.** Full marks, clean. Should partial credit
   (say ≥ 0.75) keep an assumed LO in maintenance?
4. **Quick check on the import result.** Wanted as a button on the ingest
   batch result once an import knows which LOs it created?
5. **Daily-loop DL1** consumes `placement.state` (`open_by_lo`,
   `due_learning_object_ids`) for the maintain lane and the headline's
   "assumed" count; the queue components `new_material`, `assumed_check` and
   `taught_first` mark the lanes.

## Gate

Run on the implementation commit `1f2bed45` (the only later source change is
a comment rewrap in `scheduler.py`); references regenerated afterwards.

| Check | Result |
|---|---|
| `uv sync --extra dev`, then `uv pip install pypdfium2` | OK (`uv sync` removes `pypdfium2`, so it was installed again) |
| `uv run lint-imports --no-cache` | **10 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7,127 passed**, 0 failed, 14 existing warnings (Python 3.12 fork and SQLite datetime-adapter); 203 s |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **67 passed**, 7,060 deselected; 45 s |
| `npm install`, `npm run typecheck` (apps/learnloop-tauri) | OK; typecheck 0 errors (npm install reports the existing audit notices and esbuild's blocked postinstall) |
| `npm test` (vitest) | **73 passed** in 18 files |
| `npm run frontend:build` | Passed; existing >500 kB chunk warning |
| `cargo check` | Not runnable here: `rustc: symbol lookup error … LLVM_23.1` before any project code (environment, as in Phase 2) |
| `db_generate_reference.py` / `db_validate_reference.py` | Schema **169**, 269 table notes, 553 config leaves in 31 sections, **0 errors** |
| Head fixture | `migration_head_169`: delete journal, integrity ok, FK-clean, `max(version)=169`, no WAL companions |
| Tracked working vaults | Untouched (`git status` clean for `fixtures/linear_algebra`, `probability`, `arxiv_v2`) |
