# Daily loop DL2: intent

**Branch:** `daily-loop/dl2`, worktree `learnanything-dl2`, from `main` at `fab576ac1`
(migration head 213; DL1's plan, AD1, H2b, RW2b + H3 on main).

**Spec:** `docs/specs/spec_daily_loop_v1.md` §12 row "DL2" and the sections it cites:
§5.1 (commitments carry intent), §5.2 (the single control, the projected cost, "Check
once"), §5.3 (per-intent recall targets, the anchor rule, the most-recent-choice
resolution), §5.4 (deadlines as goals), §5.6 (assumed known as Keep), §6.1 (lanes:
push from Learn and Master, scheduled checks), §6.3 (admission by intent), §7 (re-entry
triage by intent), §11 (`intent_v1`, `intent.enabled`, `intent.recall_targets_enabled`),
§13 G4 and G8, §16. Cross-spec requests: `spec_reader_workbench_v1.md` §18 (DL2 rows),
§9.3 items 6, 9 and 10, D42, D46, G27, G61.

## Plan (written before coding)

### Ruling to verify first: live change, not a successor

The orchestrator's note and the standing owner ruling (UX Phase 1 landing; facet-locks
F6): a serving change that replay never reads ships live behind a kill switch. DL2 is
that case if (a) nothing persisted changes meaning and (b) replay never reads intent.
Evidence to collect before relying on it:

- `due_at` keeps being written at 0.90 by the attempt path (unchanged); recall targets
  scale an *effective* due at serving time only;
- no projection, mastery, facet, FSRS or evidence writer reads commitments
  (`git grep` over `substrate/`, `learner/`, `attempts/`, `field/`, `placement/`,
  `goals/`, the rebuild orchestrator);
- the only new persisted rows are commitment versions/events (through the existing
  API: RAW_LEDGER / RECEIPT, never replayed into a projection) and learner goals in
  `goals.yaml` (the existing goal machinery, as `create_goal` writes them);
- a shadow rebuild on backup-API copies shows zero mastery/facet/projection deltas (G8).

If all hold: no `intent_v1` tag; `intent.enabled` (default on) and
`intent.recall_targets_enabled` (default on) are the kill switches; with no
commitments the behaviour is today's exactly. Otherwise `mvp-0.29` with a successor
record (AD2+AD3 holds `mvp-0.28`).

### No new tables or fields (§10)

Commitments through `learnloop.curriculum.commitments` only (`create_commitment`,
`append_commitment_version`, `change_disposition`), with
`provenance = {"via": "intent_control", "scope": {...}, "choice": ...}`; request
commitments other paths created are never versioned or re-disposed. Deadlines use the
existing `commitment_versions.goal_id`. No migration expected (217 reserved if one
proves unavoidable).

### Files

- New package `learnloop/intent/` (a leaf below the plan; nothing in it imports
  `learnloop.daily_plan` except the control's cost preview):
  - `model.py`: choices, presets, dispositions, targets, the snapshot dataclasses;
  - `resolution.py`: §5.3's most-recent-choice resolution over commitment snapshots
    (choice time skips satisfaction and deadline links; ties item-level, then higher
    target, then id), per item and per LO; "Check once" states (waiting, due,
    answered) with the date `due_hint` else `created_at + capture.test_me_later_days`;
  - `recall_targets.py`: `ratio(target, w20)`, `effective_due`, the anchor rule
    (latest FSRS-eligible attempt by `classify_attempt_activity`), fallbacks counted;
  - `serving.py`: what the scheduler and the plan read (`IntentServing`: exclusion,
    effective due, push, requests, the dated "Check once" branch and its candidates);
  - `control.py`: apply a choice to an LO / subject / source / item scope, the
    consequence line ("replaces your earlier setting on …") by the same resolution, the
    projected cost "about N min/day of reviews" (§6.4 estimates, §5.3 targets);
  - `deadline.py`: "Add a deadline" (a learner `Goal` linked by a commitment version's
    `goal_id`);
  - `checks.py`: settle answered checks (`satisfy_single_check`), the plan's
    `check_once` provider, the served-check view (cold banner, restoration link).
- `db/stores/intent_reads.py`: read-only bulk queries (commitments, heads, targets,
  events, FSRS anchors).
- `scheduling/scheduler.py`: four small hooks (resolution once per build; the intent
  gate after the lifecycle gate; `_forgetting_risk` reads the effective due; the dated
  checks' candidates trimmed to the top-ranked one after the sort). Nothing else.
- `db/repositories.py`: `requested_practice_item_ids(skip_commitment_ids=())`, the
  query unchanged when empty.
- `daily_plan/`: `lanes.classify_item` takes an effective due and a push set;
  `engine._classified_pool` adds the `check_once` checks, intent-aware requests and
  push; admission orders Learn/Master first and admits none from Keep/Light touch;
  review load over effective dues of non-excluded items; re-entry drops Light touch
  and orders by intent tier; `IntentView` filled; `report` counts recall-target
  fallbacks.
- Sidecar `handlers/intent.py`: `get_intent`, `set_intent`, `set_intent_deadline`;
  the practice item DTO gains `intentCheck` (only when the item is a served check);
  the feedback DTO gains the restoration link when provenance carries it;
  `prepare_queue_build` settles answered checks. Pinned desktop-only.
- Config `[intent]` (`enabled`, `recall_targets_enabled`, `recall_targets`) and
  `[capture] test_me_later_days` (7; DL3 adds the rest of `[capture]`), classified in
  the parameter registry; defaults snapshots recomputed.
- Desktop: `IntentControl` (segmented control, consequence line, cost preview) on the
  LO and item inspector views, the subject (from the LO view), and the source (book);
  the check's cold banner, the locator-free header and the help ladder's header on
  the practice screen; the restoration link on feedback.

### Tests

`test_intent_resolution.py`, `test_intent_recall_targets.py`, `test_intent_exclusion.py`,
`test_intent_goal_deadline.py`, `test_intent_checks.py` (due_hint present/absent,
minutes-bounded multiple checks, held-out never selected), `test_intent_plan.py` (push,
admission, re-entry, byte-identity pins), `test_intent_rpc.py`, the mobile allowlist pins,
vitest for the control, the cost preview, the cold header and the restoration link.
