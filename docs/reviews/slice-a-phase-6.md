# Slice A Phase 6: starting new material without ceremony (learner field F2)

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
