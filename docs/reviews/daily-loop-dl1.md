# Daily loop DL1: the finite plan

**Branch:** `daily-loop/dl1`, worktree `learnanything-dl1`, from `main` at `0583648d`
(DL0, `fix/daily-loop-followups` F1 and Slice A Phase 6 are merged there).

**Spec:** `docs/specs/spec_daily_loop_v1.md`, §12 row "DL1" and the sections it cites:
§6 (the plan; §6.3 admission; §6.4 the estimator and `PracticeItem.expected_minutes`;
§6.8 the source/chooser interface with `legacy_lanes_v1` and `lane_quota_v1`;
§6.10 reading blocks without pre-questions; §6.7 the headline), §7 goal-optional
re-entry, §10 persistence, §11 the successor and kill switches, §13 gates G1-G3,
G10, G12, G13, §17 (agent prompt).

**Migration:** `174_daily_plans.sql` (the next free number on this branch; Phase 5a takes
174 at merge, so expect renumbering). Head fixture `fixtures/migration_head_174`.

**Algorithm successor:** `daily_plan_v1` = `mvp-0.12` (the next free label on this base; T1
and the stuck prompt also ship successors, so expect relabelling). Kill switch
`plan.enabled`; sub-switches `plan.new_admission_enabled`, `plan.reading_blocks`;
`plan.headline` (display). New vaults stay at `mvp-0.9`; the upgrade is owner-run.

**Paid calls:** none ($0.00). No model or embedding route, no `judgment_ledger` write.
Rebuild and replay make zero model calls with plan rows populated (tested).

| Commit | What |
|---|---|
| `0afa38c2` | The successor, `[plan]` config, fingerprints, registry rules, `upgrade_to_mvp012`, migration 174, the store, the head fixture, `PracticeItem.expected_minutes` |
| `a74c1b55` | `learnloop.daily_plan` (split, admission, estimates, lanes, chooser, container, re-entry, reading, headline, report), the eight RPCs, the reader hook, `learnloop plan show \| report` |
| `57021fab` | The DL1 test files and the mobile pins |
| `381987d2` | Desktop: bridge, Start, Today's plan view, feedback's Next, the reader banner, vitest |
| `85956828` | DB and config references regenerated |
| `52e4f8af` | Review fixes (re-entry item cap counts forced items; every block listed), replay and G3 tests |
| *(this file)* | Review, manual runs, gate |

## Plan (written before coding)

### Files to add or change

- `algorithm_versions.py`: `DAILY_PLAN_ALGORITHM_VERSION` (`daily_plan_v1`, the next free
  label on this base: `mvp-0.12`), `DAILY_PLAN_VERSIONS`; the linear chain keeps the split
  and placement (`DIAGNOSIS_SPLIT_VERSIONS`, `PLACEMENT_VERSIONS`, `P0_SUCCESSOR_VERSIONS`
  gain it); `LATEST_ALGORITHM_VERSION` moves to it.
- `config/schema.py`: a `[plan]` section with the §10 keys (modelled defaults only, left
  out of the decision-only template); `config/template.py`: fingerprints recomputed for
  every version and keyed for `mvp-0.12`; `params/parameter_registry.py`: the new leaves
  classified.
- `ops/vault_upgrade.py`, `cli/app.py`: `upgrade_to_mvp012` (accepts `mvp-0.11`, chains
  from `mvp-0.10`/`mvp-0.9` through `upgrade_to_mvp011`); `learnloop upgrade` defaults to it.
- `vault/models.py`: `PracticeItem.expected_minutes` (optional, omitted when null, outside
  `practice_item_hash` and outside the snapshot JSON when null); the practice-generation
  wire model and its metadata guidance ask for it.
- New package `learnloop/daily_plan/` (a leaf consumer: nothing below it imports it):
  - `types.py`: §6.8's `Lane`, `PlanState`, `ReadingTarget`, `BlockCandidate`,
    `BlockChoice`, `BlockSource`, `BlockChooser`, `CONTINUE_CURRENT`, `STOP_FOR_TODAY`;
  - `estimates.py`: §6.4 (shrinkage from own latencies -> practice-mode median ->
    `expected_minutes` -> 3.0; winsorized at 15 min; feedback dwell; reading words left);
  - `split.py`: `split_v1` and the flow-on/redistribution step;
  - `admission.py`: §6.3 load-based admission (ceiling, cap, floor, exemptions, "more new");
  - `lanes.py`: §6.1 lane classification and `legacy_lanes_v1` (the source);
  - `chooser.py`: `lane_quota_v1` (the chooser);
  - `reading.py`: reading targets for `as_you_read` sources;
  - `reentry.py`: goal-optional re-entry (trigger, caps, panel numbers);
  - `headline.py`: the optional Today headline;
  - `engine.py`: the container (build, block boundaries, feasibility, fallback, learner
    picks, displacement, follow-ups, keep going, more new, minutes, reading ends);
  - `report.py`: `learnloop plan show | report`.
- `db/stores/daily_plans.py`: the only SQL writer for `daily_plans` and the plan's
  `attention_blocks` rows and events.
- Sidecar `handlers/daily_plan.py`: `get_daily_plan`, `set_plan_minutes`, `next_plan_item`,
  `plan_reading_ended`, `plan_keep_going`, `plan_more_new`, `plan_learner_pick`,
  `get_today_headline`; `reader.mark_section_progress` appends `reading_progress` and ends
  a current reading block on completion; `get_today_queue` drops the DL0 re-entry cap only
  while the plan serves (the plan carries re-entry).
- Desktop: the four bridge layers for the eight RPCs; Today's plan view (split line with
  why, current block, next blocks, block line at boundaries, done screen with keep going /
  more new material / done, the re-entry panel and the headline), the full list one key
  away (opening an item from it is a learner pick), Start's plan line and chips, feedback's
  Next through the plan, a reading step opening the reader and "Back to today's plan".
- CLI `cli/plan.py`: `learnloop plan show` and `learnloop plan report` (read-only).
- Mobile pins: the eight RPCs never phone-allowed (`test_mobile_allowlist.py`, used by
  `test_mobile_host_auth.py`).

### Migrations

One migration at the next free number (174 on this branch; Phase 5a takes 174 at merge,
so expect renumbering): `daily_plans` (WORKFLOW) and `attention_blocks` gains
`daily_plan_id`, `plan_ordinal`, `lane`, `chosen_by`, `decision_ref`, `reading_json`.
No DERIVED table, so no replayer. Head fixture renamed and upgraded, references regenerated.

### Algorithm successor and kill switches

`daily_plan_v1` = `mvp-0.12`, kill switch `plan.enabled`, sub-switches
`plan.new_admission_enabled` and `plan.reading_blocks`; `plan.headline` hides the
headline. The plan serves only at a version in `DAILY_PLAN_VERSIONS` with `plan.enabled`;
otherwise every RPC reports the plan as off and Today/Start/`get_today_queue` are DL0's
(G1). Serving only: no projection change, so the upgrade is a tag change plus the
idempotent rebuild of the same projection namespace, prepared before the atomic config
rename. New vaults stay at `mvp-0.9`.

### Spend caps and model routes

None. DL1 makes no model or embedding calls; `expected_minutes` is only read (generation
prompts may now write it, through their existing routes and spend controls).

### `judgment_ledger` writes

None: no LLM, verifier or owner verdict is produced. Plan decisions are
`attention_block_events` receipts.

### Tests

`test_daily_plan_split.py`, `test_daily_plan_build.py`, `test_daily_plan_admission.py`,
`test_duration_estimates.py`, `test_daily_plan_reentry.py`, `test_daily_plan_kill_switch.py`,
`test_block_chooser_interface.py`, `test_daily_plan_rpc.py`, `test_daily_plan_reading.py`,
`test_today_headline.py`, a fixture-copy parity test, the upgrade test, vitest for the plan
view, block lines, done screen, keep going and the reading step.

---

## What was built

### The successor and its switches

- **`mvp-0.12`** (`algorithm_versions.DAILY_PLAN_ALGORITHM_VERSION`) is the next link of the
  linear chain: `mvp-0.11`'s split and placement plus the plan. It joins
  `P0_SUCCESSOR_VERSIONS`, `DIAGNOSIS_SPLIT_VERSIONS` and `PLACEMENT_VERSIONS` (every gate
  is set membership), and `DAILY_PLAN_VERSIONS`. `LATEST_ALGORITHM_VERSION = mvp-0.12`.
- **The plan serves** only at a version in `DAILY_PLAN_VERSIONS` with `plan.enabled`
  (`daily_plan.engine.plan_active`). Otherwise every plan RPC answers
  `{enabled: false, reason}` without building a queue or writing a row, and Start, Today and
  `get_today_queue` are DL0's (G1).
- **Upgrade.** `upgrade_to_mvp012` accepts `mvp-0.11`, and chains from `mvp-0.10` / `mvp-0.9`
  through `upgrade_to_mvp011`. It freezes the `mvp-0.11` manifest, rebuilds the unchanged
  projection namespace and renames the config atomically. `learnloop upgrade` defaults to it.
- **Config `[plan]`** has the §10 keys (modelled defaults, not in the decision-only
  template; validated: repair + maintain shares ≤ 1, floor ≤ cap). Defaults fingerprints are
  recomputed for `mvp-0.9`/`0.10`/`0.11` (they move only because the effective config gains
  the section) and keyed for `mvp-0.12`. The new leaves are classified in the parameter
  registry (split caps and admission as decision constraints; sizes and paces operational).

### Persistence (§10)

- `daily_plans` (WORKFLOW): the §10 columns plus `stop_reason` and `updated_at`.
  `split_json` carries the `split_v1` result, the plan's item universe at build, the
  follow-ups present at build, the reading target, the re-entry gap, the item cap and every
  minutes re-plan; `admission_json` the §6.3 inputs and result.
- `attention_blocks` gains `daily_plan_id`, `plan_ordinal` (unique per plan), `lane`,
  `chosen_by`, `decision_ref`, `reading_json`. Block events: `block_chosen` (candidate set,
  source, chooser, `chosen_by`, propensity, why, `fallback` / `fallback_from`, the state the
  chooser saw, the redistribution, forced items, learner-pick deductions), `item_planned`,
  `item_served`, `item_done` (attempt id, `done_at`, `wall_ms`), `item_skipped`,
  `item_displaced`, `block_started`, `block_ended` (`outcome`), `reading_progress`.
- `db/stores/daily_plans.py` is the only SQL writer (registered in `test_architecture.py`).
  No DERIVED table; replay never reads the plan. Two import contracts: replay, evidence and
  serving internals (`substrate`, `learner`, `attempts`, `scheduling`, `goals`,
  `diagnosis`, `placement`, `field`) never import `learnloop.daily_plan`, and the plan uses
  only the field's predictor interface.
- `PracticeItem.expected_minutes` (optional, `exclude_if` null so item JSON, snapshots and
  their hashes are unchanged; outside `practice_item_hash`). The practice-generation prompt
  asks for it (`PRACTICE_GENERATION_PROMPT_VERSION = mvp-1.3-expected-minutes`) and the wire
  payload carries it.

### The plan container (`learnloop/daily_plan/`)

- **Day and kinds.** One local calendar date (D9). The day's first read builds a `normal`
  plan, or a `reentry` plan after the gap (§7). Keep going builds a `keep_going` extension
  (or, after re-entry, a `normal` plan for the day's remaining minutes). An open plan from an
  earlier day is `abandoned` on the next day's first read.
- **Pool.** The scheduler's ranked eligible list (Today's own build in the sidecar: same
  scheduler call, teach-back filter and offer finalization), classified into lanes in §6.1's
  order (`lanes.classify_pool`): scheduled checks → maintain (Phase 6's `assumed_check`, and
  project probes from a registered provider, at most `project_probes_max_per_day` a day);
  repair (follow-ups and recent errors); new (never attempted); maintain (due, or previously
  attempted requests); push (goal frontier, not due); else "later".
- **Requests first (L3).** Up to `tutor_promotion.requested_items_per_session` requests that
  fit go in the first block; their estimates are deducted before the split.
- **Estimates (§6.4, `estimates.py`).** k = 3 shrinkage from own latencies (winsorized at
  15 min) toward the practice-mode median toward `expected_minutes` (else 3.0), plus the
  median feedback dwell (`item_done` → next `item_served`, capped at 5 min; 0.5 until ten
  observations). Reading: words left / 120 wpm. Each planned item's estimate is on its event.
- **Admission (§6.3, `admission.py`).** L = projected mean daily review minutes over 14
  days; new items admitted in the scheduler's (Phase 6's) order while L + cost ≤ 0.8 × M,
  at most 10 a day across the day's plans, at least 1 when new material exists (not in
  re-entry). Requests are exempt and first. "More new material" bypasses ceiling and cap
  once (a labelled `keep_going` extension, trade-off shown first). `new_admission_enabled =
  false` admits none.
- **Split (§6.2, `split.py`).** `split_v1` with the flow-on; re-entry uses repair and
  maintain only.
- **Blocks (§6.8).** `legacy_lanes_v1` groups each lane's items by LO in rank order and packs
  them into blocks ≤ 15 min, never above the lane's or the plan's minutes (small maintain and
  repair groups merge up to 5+ min; new and push stay on one LO; no minimum).
  `lane_quota_v1` picks the lane with the largest unspent share (ties repair, maintain, new,
  push; then planner value). The container (`engine.decide`) redistributes released lane
  minutes in §6.2's order (new only up to its admitted minutes), offers only feasible
  candidates, falls back to `lane_quota_v1` on an unknown, infeasible or `continue_current`
  choice (flagged), allows `stop_for_today` only when offered, and logs every block decision.
  Router R2 plugs in through `PlanPolicy(source, chooser)`.
- **Serving.** `next_plan_item` reconciles (an attempt after an item was planned marks it
  done, whatever surface served it; unservable items are displaced), plans mid-plan
  follow-ups next (displacing the tail), crosses a boundary when needed, and names the next
  typed step (`item` with the candidate id of the slate that ranked it, `reading`, `done`).
  `serve` records `block_started` / `item_served`; without it it is the prefetch made while
  feedback shows. `skip_practice_item_id` skips.
- **Learner picks (G12).** `plan_learner_pick`: a planned item is just served; any other item
  is a one-item `learner_pick` block (no propensity), its estimate deducted from push, new,
  repair, maintain, the plan's tail displaced so the plan stays finite.
- **Minutes (§6.6).** Every plan stores `remembered_minutes` (chip / carried / generated).
  A chip re-plans the rest (a new split from the next block on, tail displaced if smaller,
  a completed plan reopened if larger); on a re-entry plan it sets the remembered value and
  the budget stays capped; keep-going and the post-re-entry plan never change it.
- **Re-entry (§7, `reentry.py`).** Last real activity (F1) > `reentry_gap_days`, no goal
  needed: min(remembered, 15) minutes, ≤ 8 items, repair and maintain, ordered assumed checks,
  then goal deadlines, then rank. The panel: gap, still solid, slipped below 0.90 (named by
  largest drop, or by blueprint weight under an active goal), and today's re-entry figures.
  No overdue count, no streak, no due date rewritten.
- **Reading blocks (§6.10, `reading.py`).** At most one a day, from the most recently read
  `as_you_read` source (completed synthesis manifests whose brief says so), next unfinished
  section, partial when it exceeds the minutes it can have. `reader.mark_section_progress`
  appends `reading_progress` and ends the block on completion; `plan_reading_ended` records
  `left_reader` / `skipped`; an interrupted block stays current and the next day continues
  the section. No pre-questions (DL4).
- **Headline (§6.7, `headline.py`).** Each active LO in one class: assumed (open Phase 6
  assumption), demonstrated (`lo_certification` for blueprint LOs; every required capability
  of every facet otherwise), learning (direct evidence), untested; expected recall today =
  mean retrievability over items with memory state, labelled "a model estimate, not a test".
  "assumed" is omitted while placement is off.
- **Report (`report.py`, `cli/plan.py`).** `learnloop plan show` (today's stored plans) and
  `learnloop plan report` (days active, plan starts and completions, estimated vs actual
  minutes, keep-going rate, open-to-first-item time, stop reasons, chooser fallbacks).
  Read-only database; no queue build; no model call.

### Sidecar

- RPCs `get_daily_plan`, `set_plan_minutes`, `next_plan_item`, `plan_reading_ended`,
  `plan_keep_going` (`stop: true` is "Done"), `plan_more_new` (`confirm`),
  `plan_learner_pick`, `get_today_headline`. The plan DTO (`view.py`) carries every figure
  the screens show: the split line and per-lane display minutes (largest remainder, summing to
  the budget), block estimates, items and states, the projected blocks (the deterministic
  pair run forward without logging) and "Block N of about M", totals for the plan and the day,
  the re-entry panel, the streak.
- `get_today_queue` drops the DL0 re-entry cap only while the plan serves (the plan carries
  re-entry; L3 picks come from the full list). Its preparation (capture sweep, follow-up
  backfill, diagnosis wait) is shared with the plan.
- Pinned as never phone-allowed (`tests/test_mobile_allowlist.py`, used by
  `tests/test_mobile_host_auth.py`; a test also checks the pinned list equals the handler's).

### Desktop

- Bridge: eight `sidecar_passthrough!` commands, handler registrations, client methods and DTOs
  (`test_desktop_rpc_contract.py` passes).
- **Start** shows today's plan (split line with why, "First: X · N items · about M min",
  welcome-back line on re-entry); chips set the remembered minutes; Begin starts the session
  with the plan's budget and opens its first step. The streak label reads "begin today's plan
  to keep your streak".
- **Today** shows the plan view (`screens/today/DailyPlanView.tsx`): split line and why,
  chips, headline, the re-entry panel, the current block with its items (current one
  highlighted, skip), its block line ("Block 2 of about 3 · maintain · about 8 min · why"),
  "next: new · about 6 min", Enter to continue, `l` for the full list (`p` back). Opening an
  item from the full list is a learner pick. The done screen: "Today complete · 26 min · 9
  items", the streak marked, keep going, done, more new material (trade-off first);
  "Nothing due today" and "Re-entry done. Keep going?" variants. The full list is read only
  when shown.
- **Feedback's Next** follows the plan (`app/dailyPlan.ts`): the next step is read while
  feedback shows; an item in the same block opens directly with its offer; a new block, a
  reading step or the done screen go through the plan view (continue on Enter). Esc / b
  return to the plan view.
- **Reading step**: opens the reader at the section's first span with a "Reading for today's
  plan" banner and "Back to today's plan" (`left_reader`).

## Deviations and decisions

1. **`router.enabled` does not exist on this base** (router R0/R2 are unmerged). The plan
   reads its source and chooser from `PlanEnv.policy` (default: the DL1 pair); the router-on
   rows of §6.8's table are tested with a fake router chooser in that seam. R2 adds the
   switch and selects its policy in the sidecar's `_env`.
2. **A stop has no block,** so its decision (candidate set, chooser, reason) is logged on the
   plan row (`split_json.stop`) rather than as a `block_chosen` event.
3. **The plan's universe is fixed at build** (§6.1 "nothing new is added mid-plan"): items
   that become eligible during the day (a capture adopted, an item falling due at 3 pm) wait
   for keep going or tomorrow. Only follow-ups produced by this session's answers join, by
   displacement.
4. **Requests that do not fit the budget wait** (strict G2); the full list still serves them
   as learner picks.
5. **A pick larger than everything still displaceable** is served anyway (L3) and the
   overrun is recorded on its `block_chosen` event; a pick on a plan that is no longer open is
   served as an open-list pick and does not grow it ("keep going is the only extension").
6. **Re-entry ordering applies within lanes.** Lane interleaving follows `lane_quota_v1`
   (repair first on ties), so an assumed-known check can follow a first repair block.
7. **No intent in DL1.** Every LO is uncommitted (target 0.90, `IntentView` defaults);
   Light-touch exclusion, Keep / Light-touch admission tiers and per-intent recall targets
   are DL2. Re-entry's intent tier is goals with deadlines first.
8. **Project probes** have no producer on this base: the classifier takes them from a
   registered `ScheduledCheckProvider` (project M2's seam), tested with a fake provider.
9. **As-you-read detection** reads completed synthesis manifests whose brief names
   `as_you_read`; a manifest without the field is skipped (conservative). Leaving the reader
   by a tab switch keeps the block current (interrupted); only "Back to today's plan" or a
   skip records `left_reader` / `skipped`. Esc in the reader is not wired to it.
10. **Feedback's Esc / b return to the plan view,** whose full list is one more key (`l`).
11. **The TUI is unchanged:** it keeps DL0's open queue while the desktop serves the plan
    (DL1's row names the desktop Today views). See open question 1.
12. **§9's grading-latency p50/p95** is not in `learnloop plan report` (not in DL1's row).
13. **`get_today_queue` changes under the successor:** no re-entry cap while the plan serves.
14. **The headline is hideable by config** (`plan.headline`), not by an in-app toggle.
15. **The streak badge shows "today ✓" once a session began today** (DL0's rule, which is what
    is counted), not only when the plan completes.
16. **Whole minutes on screen, exact minutes enforced.** The split line shows each lane's
    largest-remainder whole minutes (summing to the budget); the container enforces the exact
    allotments. Both come from the DTO (G3 test compares DTO and persisted plan).
17. **`expected_minutes`** is asked for by the practice-generation prompt only; authoring and
    canonical-ingest prompts are unchanged, capture drafting is DL3.
18. **Estimator inputs:** the mode median uses every attempt with a latency in that mode.
    Headline "direct evidence" = facet capability cells with direct mass (canonical vaults),
    `last_evidence_at` otherwise. The re-entry panel's LO retrievability is the mean over the
    LO's items with memory state.
19. **RPC parameters beyond the spec's names:** `next_plan_item` takes `serve` and
    `skip_practice_item_id`; `plan_keep_going` takes `stop` ("Done"); `plan_more_new` takes
    `confirm`. No extra RPC.
20. **Rust not compiled here** (`rustc` broken on this machine); the passthroughs use the
    existing macro and the static bridge contract test passes.
21. **Doc generators outside the gate:** `module_validate.py` (203 missing module notes) and
    `desktop_validate.py` (`KeyError: 'TypeScript/screens/today'`; the directory predates
    DL1) fail on the base too; `validate_vault.py` passes.

## Manual runs (backup-API copies under `fixtures-local/`, no paid calls)

Copies of `linear_algebra`, `probability` and `arxiv_v2` (`dl1-*`, from this worktree's
tracked fixtures at `0583648d`): `doctor --fix-state`, `upgrade --to mvp-0.9`,
`upgrade --to mvp-0.11`, two `rebuild-derived-state`, then:

| Check | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Same-version shadow at `mvp-0.11` (facet / mastery / schedule rows) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| Candidate shadow `--set algorithms.algorithm_version=mvp-0.12` | 79 / 21 / 0 rows, **0 semantic** (version tag only) | 2 / 18 / 0, **0 semantic** | 6 / 34 / 0, **0 semantic** |
| Source database SHA-256 across the shadows | unchanged | unchanged | unchanged |
| `learnloop upgrade` (default target) | mvp-0.11 → mvp-0.12 | same | same |
| Same-version shadow at `mvp-0.12` after a rebuild | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

**Served-set diff** (each `mvp-0.12` copy on 2026-10-12, real clock, no session): the open
queue against today's plan.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Open queue (`get_today_queue`) | 40 items (cap `null` while the plan serves) | 67 items | 32 items |
| Plan kind, budget (remembered) | re-entry (gap 76 days), 10 min (10) | normal, 30 min (30) | re-entry (gap 83 days), 15 min (25) |
| Split line | `10 min · maintain 7 · repair 3` | `30 min · repair 9 · new 21` | `15 min · maintain 7 · repair 3` |
| Admission | none (re-entry), L = 23.7 min/day | 10 admitted, stopped by the daily cap; L = 4.2 min/day, ceiling 24 | none (re-entry), L = 9.0 |
| Chosen + projected blocks (items) | repair 1, maintain 2 (7.8 min) | repair 2, new 3, new 2 (28.4 min) | repair 1, maintain 2 (10.5 min) |
| Re-entry panel | solid 0, slipped 7 (named) | — | solid 0, slipped 3 (named) |
| Headline | 1 demonstrated · 0 assumed · 11 learning · 9 untested — 66% | 0 · 0 · 1 · 17 — 59% | 0 · 0 · 5 · 29 — 48% |
| Build time (`get_daily_plan`) | 0.34 s | 0.22 s | 0.32 s |

The re-entry plans fill less than their cap because only those items are due or in repair
(the plan admits no new or push material in re-entry, §7); see open question 7.

**A simulated day** on a fresh `mvp-0.12` copy of `probability` (frozen clock 2026-10-14,
"I don't know" answers, one learner pick from the full list): a 30-minute plan of 7 items
(27.9 estimated minutes) in 3 chosen blocks plus the pick, completed with "today's minutes are
used"; keep going built a 10-minute extension (`10 min · repair 10`); "more new material"
offered 1 item, "adds about 2.6 min/day of reviews". `learnloop plan report`: 1 day active,
1 plan start, 1 completion, keep-going rate 1.0, 7 items done, 27.9 estimated vs 13.0 actual
minutes, 0 chooser fallbacks.

**Kill switch on the copies** is pinned by `test_plan_off_is_dl0_on_fixture_copies`
(below): with `plan.enabled = false` at `mvp-0.12`, `get_today_queue` (with and without
minutes) and `get_start_summary` equal `mvp-0.11`'s on all three, the plan RPCs answer
`enabled: false`, and no plan row is written.

## Tests

| File | Covers |
|---|---|
| `test_daily_plan_split.py` (10) | Shares, caps, requests deducted before the split, new ≤ admitted, flow-on order, re-entry lanes, "more new" first, whole-minute line, redistribution and the new room |
| `test_daily_plan_build.py` (19) | §6.1 lane order; due project probes in maintain under the cap, the fifth "later", outside the new-item cap; packing (a single 3.5-min due item is a block; small maintain groups merge; new stays on one LO; ≤ 15 min, lane and plan bounds); a 3.5-min item served with 4 min left; **G2** finite at 10/15/25/40 min (budget and every lane's allotment at every step); requests first and deducted; mid-plan follow-ups displace the tail; items appearing mid-plan never join; **G12** picks logged without propensity and displacing; boundary-only decisions; `decide` is pure |
| `test_daily_plan_admission.py` (7) | Review load, ceiling, daily cap across plans, floor (not past the cap, not in re-entry, not when off, once a day), exempt requests first, "more new" bypass and trade-off, order kept |
| `test_duration_estimates.py` (9) | Shrinkage, winsorizing, feedback dwell, reading estimate, loaded latencies, `expected_minutes` optional / omitted / outside the hash, the wire payload |
| `test_daily_plan_reentry.py` (5) | **G10**: no goal needed, 15 min / 8 items, repair and maintain only, no new, no due date rewritten; no re-entry within the gap; order; the panel (no overdue, no streak); the full list uncapped while the plan serves |
| `test_daily_plan_kill_switch.py` (10) | **G1** on copies of the three fixtures; version gate; every row of the plan × router table (fake router chooser); the new-admission and headline switches |
| `test_block_chooser_interface.py` (9) | **G13**: 7 min with 5 left and 10 min with 1 lane minute never offered; unknown / infeasible / `continue_current` / unoffered stop fall back, flagged; a valid router choice keeps its propensity and decision ref; flow-on order; lane-quota ties; every decision logged with its candidate set |
| `test_daily_plan_rpc.py` (10) | Remembered minutes (40 → keep going 10 → 40 tomorrow; re-entry 15 and its remainder leave 40; a chip on re-entry changes the remembered value, not the cap); serving with the offer that ranked it; skip; more new; headline; validation; **G3** DTO figures equal the persisted plan |
| `test_daily_plan_reading.py` (7) | Only as-you-read imports; words left shrink with progress; typed reading step; `reading_progress` and completion from the reader; `left_reader` / `skipped` consume the estimate; partial block; interrupted block resumes; the next day continues the section; switch off |
| `test_today_headline.py` (5) | One of two capabilities → learning; one of two facets → learning; all → demonstrated; a blueprint LO with an integration gap → learning; assumed first and omitted before placement; expected recall labelled |
| `test_daily_plan_replay.py` (2, durability) | Rebuild with plan rows makes no model call, leaves them untouched and reproduces the same derived state; a plan runs on a fresh WAL vault |
| `test_mvp012_upgrade.py` (9) | Successor sets, activation, upgrade from `mvp-0.11` (nothing rewritten), chains from `mvp-0.9`, refusals, CLI default, fingerprint, head-fixture path (FK, doctor, idempotent rebuild) |
| Vitest `DailyPlanView.test.tsx` (9), `dailyPlan.test.tsx` (4), `FeedbackScreen.plan.test.tsx` (2), `StartScreen.test.tsx` (+3) | Split line and why, headline, block line, items, next block, keys, reading line, re-entry panel, done screen (figures, streak, keep going, done, more new and its trade-off), empty and re-entry variants; step routing, reader target, key-bar labels, the reader banner; feedback's Next serving within the block and handing a new block to the plan; Start's plan, Begin, chips, streak label |

Changed existing tests: `test_mvp011_upgrade.py` (latest version and sets; the CLI default
moved, so `--to mvp-0.11` is explicit), `test_mvp09_upgrade.py` (comment), the six head-fixture
paths, `test_architecture.py` (the store is a registered SQL owner), the CLI help snapshot,
`StartScreen.test.tsx` (the plan read is mocked off for the DL0 cases).

## Files touched

- New: `migrations/174_daily_plans.sql`, `src/learnloop/db/stores/daily_plans.py`,
  `src/learnloop/daily_plan/` (`types`, `estimates`, `split`, `admission`, `lanes`,
  `chooser`, `records`, `engine`, `view`, `reading`, `reentry`, `headline`, `report`),
  `src/learnloop/cli/plan.py`, `src/learnloop_sidecar/handlers/daily_plan.py`,
  `apps/learnloop-tauri/src/app/dailyPlan.ts`,
  `apps/learnloop-tauri/src/screens/today/DailyPlanView.tsx`,
  `apps/learnloop-tauri/src/components/PlanReadingBanner.tsx`, the tests above,
  `tests/daily_plan_fakes.py`.
- Changed: `algorithm_versions.py`, `config/schema.py`, `config/template.py`,
  `params/parameter_registry.py`, `ops/vault_upgrade.py`, `cli/app.py`, `cli/__init__.py`,
  `vault/models.py`, `content/proposals/ai_contracts.py`,
  `content/authoring/practice_generation.py`, `db/table_roles.py`, `pyproject.toml` (two
  import contracts), sidecar `handlers/__init__.py`, `queue.py`, `reader.py`; desktop
  `commands.rs`, `main.rs`, `client.ts`, `dto.ts`, `App.tsx`, `StartScreen.tsx`,
  `TodayScreen.tsx`, `FeedbackScreen.tsx`; `tests/helpers.py` (`create_daily_plan_vault`);
  the head fixture (`migration_head_173` → `migration_head_174`) and its README; the DB
  reference scripts and generated notes; `Version Registry.md`.
- Tracked working vaults: untouched (`git status` clean for `fixtures/linear_algebra`,
  `fixtures/probability`, `fixtures/arxiv_v2`).

## Owner commands

Run on a backup-API copy first, then on the live vault when satisfied. Never on the tracked
fixtures.

```bash
# Upgrade (accepts mvp-0.11; chains from mvp-0.10 / mvp-0.9). Optional retag after:
uv run learnloop upgrade --vault "$VAULT"
uv run learnloop rebuild-derived-state --vault "$VAULT"

# Today's stored plan, and the two-week checkpoint report (both read-only):
uv run learnloop plan show --vault "$VAULT" --json
uv run learnloop plan report --vault "$VAULT" --json

# Kill switch: DL0's Today exactly. Add to the vault's learnloop.toml:
#   [plan]
#   enabled = false
# Narrower: new_admission_enabled = false (no system-chosen new material),
# reading_blocks = false, headline = false.
```

### What to watch in the first two weeks (the DL1 checkpoint, Q0)

- `learnloop plan report`: days active, plan starts vs completions, keep-going rate, and
  open-to-first-item time answer Q0.
- `actual_over_estimate_median`: the estimator starts at 3 minutes plus 0.5 of feedback and
  shrinks toward your own latencies; a ratio far from 1 for long says the prior is off.
- `chooser_fallbacks` should stay 0 with the deterministic pair.
- Re-entry after a long break serves only what is due or in repair (no new material).

## Open questions

1. **The TUI** keeps DL0's open queue while the desktop serves the plan. Build a TUI plan
   view, or is the TUI out of the daily loop?
2. **Re-entry order across lanes.** Should due assumed-known checks lead a re-entry plan even
   when a repair block ties first under `lane_quota_v1`?
3. **The fixed universe.** Items falling due later the same day wait for keep going or
   tomorrow. Acceptable, or should the next boundary admit them within the lanes?
4. **Pick overrun.** A pick larger than everything displaceable is served past the budget
   (recorded). Keep, or refuse with "start keep going"?
5. **§9's grading-latency report** in `learnloop plan report`: DL1 follow-up or later?
6. **Requests larger than the budget** wait in their lane. OK?
7. **Under-filled re-entry plans** (fixture copies: 3 items in 15 minutes): honest per §7, or
   allow push once repair and maintain run dry?
8. **Esc from feedback** returns to the plan view (list one more key). Or straight to the
   full list, as DL0's wording?
