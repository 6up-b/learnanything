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

---

## Ruling: a live change behind `intent.enabled`, no `intent_v1` successor

The spec names an `intent_v1` successor (§11). The owner's standing ruling (UX Phase 1
landing; facet-locks F6) applies instead, because both of its conditions hold:

1. **Nothing persisted changes meaning.** `due_at` is still written at 0.90 by the attempt
   path (untouched); the recall targets scale an *effective* due at serving time only
   (`scheduling/intent/recall_targets.py`). FSRS state, evidence, mastery, facets,
   certification and every projection are unchanged. `test_stored_due_at_never_changes`
   pins that choices and queue builds leave every `practice_item_state` row as it was. The
   only new rows are commitment versions and events written through the existing
   commitments API (RAW_LEDGER / RECEIPT, never folded into a projection) and learner
   goals in `goals.yaml` written as `create_goal` writes them.
2. **Replay never reads intent.** `git grep` over `substrate/`, `learner/`, `attempts/`,
   `field/`, `goals/`, `diagnosis/` and `placement/` finds no read of `commitments`,
   `commitment_versions`, `commitment_events` or `commitment_target_versions` (the hits
   are prose, and placement's `learner_gap_commitments`, a separate table); nothing in
   replay imports `learnloop.scheduling.intent` or `learnloop.intent`. Shadow rebuilds on
   copies that carry intent commitments show zero deltas (below, G8).

So: no successor tag; **`intent.enabled`** (default on) is the kill switch and
**`intent.recall_targets_enabled`** (default on) the narrower one. With no commitment
covering an item (and the uncommitted target at 0.90), `intent_serving` returns `None`
and every scheduler and plan branch is the predecessor's by construction; byte-identity
with `fab576ac1` is pinned on fixture copies below and by tests. It acts at every
algorithm version (owner vaults at `mvp-0.8` included). AD2+AD3 keeps `mvp-0.28`; DL2
takes no tag (`mvp-0.29` unused).

## What was built

### Serving (`learnloop/scheduling/intent/`, read-only)

- **`resolution.py`** (§5.3): commitments whose head targets include the item or its LO
  cover it (retired ones drop out, satisfied ones stay, source-locator-only ones cover
  nothing). The newest *choice* decides the disposition; a choice is a creation, a
  version, or a disposition change, and neither a check's satisfaction nor a deadline
  link moves it. Ties (the same stored second) go to the item level, then the higher
  recall target, then insertion order (the row's ULID). Depth and target come from the
  newest active intent-control `help_me_remember` covering the item, else the decider, so
  a request never lowers a chosen depth. `Resolution.with_snapshot` is the preview's
  virtual newest choice: the control's consequence line uses the very rule the queue uses.
- **`recall_targets.py`**: `ratio(target) = (target^(1/-w20) - 1) / (0.9^(1/-w20) - 1)`
  (exactly 1.0 at 0.90: the function returns `due_at` itself); `effective_due = anchor +
  (due_at - anchor) x ratio`; the anchor is the latest attempt that
  `classify_attempt_activity` marks `eligible_for_fsrs` (attempt type, `primed`,
  `hints_used`), never `last_attempt_at`. Fallbacks: no state / null `due_at` (not due,
  as today), no qualifying attempt / anchor not before `due_at` (`due_at` unscaled).
- **`serving.py`**: `intent_serving(vault, repository, now)` returns `None` when intent
  changes nothing; otherwise `IntentServing` answers exclusion (`withhold_reason`), the
  effective due, push (attempted Learn/Master items not yet due), requests
  (`filter_requests`: the existing branches minus intent-control commitments and minus
  excluded or pending items, plus the dated "Check once" branch) and the due checks.
  **"Check once"**: a `test_me_later` commitment pending its check holds back the items
  it decides until its date (`due_hint` when present, a date-only value meaning that
  local day; else `created_at + capture.test_me_later_days`), then one item is served:
  the item target, or the scheduler's top-ranked item of the LO (`pick_checks`, after the
  sort). An attempt on an item it decides at or after the date answers it; resolution
  reads it as `satisfied` straight away.
- **Scheduler** (`scheduling/scheduler.py`, four hooks, nothing else): one
  `intent_serving` per build; requests through it; the intent gate right after the
  lifecycle gate (so reserved, held-out and staged-owned items are excluded first and a
  check never selects one); `_forgetting_risk(..., effective_due=)`; a push floor for
  Learn/Master items; `pick_checks` after the sort.
- **`requested_practice_item_ids(skip_commitment_ids=())`**: empty, the query text is
  exactly the predecessor's.

### The plan (`learnloop/daily_plan/`)

- `_classified_pool`: the same request rule; DL2's **`check_once` provider** turns each
  due check's item into DL1's `ScheduledCheck("check_once")` (maintain lane, before
  repair and new; not a requests-first slot, so several due checks are bounded by the
  plan's minutes, not a count); the due test reads the effective due; Learn/Master items
  not yet due go to **push** ("you chose Learn or Master here, not due yet").
- **Admission** (§6.3): requests first; then Learn and Master, then uncommitted, each in
  Phase 6's order; Keep and Light touch admit none. Review load reads effective dues and
  leaves excluded and pending items out.
- **Re-entry** (§7): Light touch is left out; order is assumed checks, then Master / Learn
  / deadlines, then Keep, then uncommitted, then rank. The welcome-back panel counts LOs
  in active intents against each one's own target (Light touch, checks and excluded LOs
  left out).
- **Chooser state**: committed LOs' `IntentView` (choice, disposition, target, deadline)
  reach `PlanState.intents` (the router card reads it); an LO assumed known (not tested)
  with no commitment reads as Keep, 0.85 (§5.6). With no commitment nothing changes
  (DL1's defaults).
- Lane lines: "check · on your own · N checks you asked for (topic)" and the push line
  for chosen material.
- **`learnloop plan report`** gains `intent`: commitments covering items, committed items
  by choice, items scaled, and the fallbacks (`no_state`, `no_due_at`,
  `no_qualifying_attempt`, `anchor_not_before_due`).

### The control (`learnloop/intent/`) and deadlines

- **`control.py`**: scopes `learning_object`, `practice_item`, `subject` (its active LOs),
  `source` (the LOs its current readings teach; by source or extraction id). A depth
  choice creates the scope's own `help_me_remember` commitment (`provenance = {"via":
  "intent_control", "scope", "choice"}`) or versions it (preset, current targets) and
  re-disposes it `active` (choosing again is a new choice); "Check once" creates a fresh
  `test_me_later` commitment; Reference / Pause / Let go re-dispose the scope's newest own
  commitment (`reference_only` / `paused` / `stopped`; Let go is a disposition, not
  `retire`). Other paths' commitments are never touched. The consequence line names what
  it replaces ("Pause 12 topics · replaces your earlier setting on 2 topics and 1 item";
  the scope's own earlier setting is what changes, so it is not counted).
- **Projected cost** (`daily_plan/intent_cost.py`, injected into the control so intent
  never imports the plan): §6.4 estimates of covered items with memory state, at their
  target after the choice, through §6.3's review-load projection: "about N min/day of
  reviews", "under 1 min/day", "no reviews" (Pause, Reference, Let go), "one check, about
  N min".
- **`deadline.py`** (§5.4): "Add a deadline" on the scope's active depth commitment
  creates or moves a learner goal (`creation_source: "learner"`, the LOs' concepts as its
  scope, the commitment's target as `target_recall`) and links it through a version with
  `change_reason = "intent_deadline"` (not a choice). The goal machinery then treats
  those LOs as deadline LOs (push frontier, re-entry tier, the goal report).
- **`checks.py`**: `settle_answered_checks` (called by `prepare_queue_build`) writes
  `satisfy_single_check` for answered checks; `served_check` is the practice view of a
  due check; `answered_check` the feedback view; `restoration_link` the way back.

### Sidecar and desktop

- RPCs `get_intent`, `set_intent`, `set_intent_deadline` (desktop only, pinned).
  `get_practice_item` (session serves only) carries `intentCheck` when the item is a due
  check, `get_feedback` when the attempt answered one; both absent otherwise.
- **`IntentControl`**: eight choices in two groups, the current setting and where it comes
  from, the consequence and cost previewed on hover or focus before anything is taken,
  deadlines; never takes focus. Mounted on the topic and item inspector views, the
  subject (from the topic: "set for all of …", read only when opened) and the book card's
  details.
- **The check on your own** (practice screen): the cold banner; help is never blocked:
  the first hint press opens the ladder with "Taking any help makes this attempt practice
  with help, not a check on your own." and nothing is revealed; "Take a hint" (or the
  hint key again) takes it; no dialog. The header names the book only: no exercise
  number, page, section, source refs or why until feedback.
- **Feedback**: "Your check on your own." and, only when the provenance carries anchor
  spans or inquiry roots, "Back to where you studied this[: label]", which opens the
  Reader at the first anchor span (a link, never a jump).

## Reader cross-spec requests (`spec_reader_workbench_v1.md` §18)

| Request | Built | Deferred to RW6b (reason) |
|---|---|---|
| (a) dated branch reads `commitment_versions.due_hint`, else `capture.test_me_later_days` | Yes; datetime and date-only hints; tested both ways (`test_intent_checks.py`) | — |
| (b) DL2's provider fills `check_once`; several checks bounded by minutes, not a count | Yes; a 10-minute plan serves 2 of 8 due checks, a 40-minute plan 5 to 8 (more than the probe count cap) | — |
| (c) the served check: cold banner, help never blocked with the ladder's consequence (D42), a header that locates nothing until feedback (D46, G61) | Yes, on the practice screen (simple and classic cards; vitest asserts no exercise number, page, section, link or "why") | The plan line's "from your reading of §5.4 (why)": RW6b's provenance supplies the reading; DL2's line is "check · on your own · …". Probe-type checks on the phone keep "continue it on the desktop" (unchanged) |
| (d) "back to where you studied this" from provenance | Yes, rendered only when `inquiry_root_event_ids` / `anchor_span_ids` are present; opens the Reader at the first anchor span of `provenance.source_id` | Opening at an inquiry *branch* (RW6b knows how to restore one), and the "answered wrong or with help" condition (RW6b's follow-up rule; DL2 shows the link after any answered check whose provenance has one) |

Depth intents map onto RW7a's depth choice as one setting: not built (RW7a is unmerged).

## Deviations

1. **Module placement.** The serving modules live in `learnloop.scheduling.intent` (not
   `learnloop.intent` as planned): `scheduling -> intent -> (params, curriculum,
   scheduling.fsrs)` made a package cycle that `frozen-cross-package-cycles` refuses. The
   control, checks, deadline and report stay in `learnloop.intent`, above scheduling. One
   new ignore entry: `scheduling.intent.recall_targets -> diagnosis.causal_activity_policy`
   (a leaf; the same exemption `attempts.attempts` has).
2. **"Check once" creates a fresh commitment per choice** (its date counts from its own
   creation) instead of re-disposing an older check; an older check stays as history and,
   being an older choice, decides nothing.
3. **Linking a deadline is not a choice**: the version it appends carries
   `change_reason = "intent_deadline"`, skipped by the choice time (else adding a
   deadline to an LO would undo a later item Pause). A deadline can be added or moved,
   not removed, in DL2.
4. **Assumed known as Keep (§5.6)** is a label for the chooser and the re-entry tier; the
   check's date is placement's, so the 0.85 target has nothing to scale. It applies when
   intent is active (some commitment exists), keeping the no-commitment byte identity.
5. **The capture view has no control**: on this base a capture is a reference until DL3's
   "Practice this" makes an item (intent is never asked at capture, Q6/C2). DL3 mounts the
   same `IntentControl` on the adopted item.
6. **The help ladder** on the practice screen is one rung (the item's hint, or the
   adaptive hint when on); "Enter on a rung" is the focused "Take a hint" button or the
   hint key pressed again. No focus is moved.
7. **`[capture]` gains only `test_me_later_days`**; DL3 adds the rest of the section.
8. **Fallback counts** in `plan report` include items under a non-0.90 target that have
   no review state yet (`no_state`, `no_due_at`): honest labels, not errors.

## Manual runs (backup-API copies under `fixtures-local/`, no model calls)

Copies of `linear_algebra`, `probability` and `arxiv_v2` (`copy_tree_with_databases`),
`doctor --fix-state` (migration 213), every command through
`fixtures-local/tmp/dl2-iso.sh` (`env -i`, no API keys, empty `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`). `fab576ac1`'s code ran from `git archive` on `PYTHONPATH`.

- **Owner vaults hold no commitment that covers an item** (two `source_locator`-only
  commitments: Reader presets). Intent therefore changes nothing on them today.
- **Byte identity with `fab576ac1`** at a frozen clock: the ranked list (item, priority,
  every component), `get_today_queue` (with and without 25 minutes) and
  `get_start_summary`: identical on all three at `mvp-0.8`, for intent on and
  `intent.enabled = false` (41 / 67 / 32 ranked). With the version set to `mvp-0.27`
  (plan live): the same plus `get_daily_plan` and `next_plan_item`, identical once ids
  are normalized (re-entry plans: 1 / 1 / 2 items; 43 / 67 / 32 ranked).
- **Choices on the shadow copies** (Pause, Light touch, Check once on an item, Master):
  the ranked list loses 8 / 3 / 3 items; each check item is served 8 days later.
- **G8 shadow rebuild** after two `rebuild-derived-state` on those copies (commitments
  present): facet / mastery / schedule deltas **0 / 0 / 0** on all three (unchanged 79 /
  21 / 99, 2 / 18 / 77, 6 / 34 / 32); live database SHA-256 unchanged by each shadow.
- **Anchor reproduction** on read-only copies: every item with a `due_at` and an anchor
  reproduces `anchor + stability x fsrs_interval_factor` within one second (53 / 1 / 3
  items, worst 0.95 s, no item without an anchor).
- `learnloop plan report --json` on the linear-algebra copy: `intent` = 4 commitments
  covering items; 10 paused, 10 light touch, 3 master, 1 check; 5 scaled, 9 `no_due_at`.

Paid calls: none ($0.00). No `judgment_ledger` write.

## Tests

| File | Count | Covers |
|---|---|---|
| `test_intent_resolution.py` | 24 | §5.3 cases: item Pause under LO Master; subject Pause after adoption (requests included); LO choice after item Pause; a request never lowers a chosen depth; Master on an item is not a request; ties; consequence-line parity (5 scenarios) and wording; projected cost by target; "Check once": uncommitted item, item under an older LO Master, LO check (exactly one item), a later LO choice re-includes, a check replaced before its date is never served, satisfaction leaves the choice time, satisfied decides over an older Master; retired drop out; source-locator-only covers nothing; check dates |
| `test_intent_recall_targets.py` | 11 | The ratio (= FSRS interval ratio, exactly 1 at 0.90); effective due; fallbacks; anchor skips primed and diagnostic, an ordinary review moves it; identity at 0.90 (uncommitted items' priority and components equal intent off); both kill switches; stored `due_at` never changes; fixture-copy reproduction (3) |
| `test_intent_exclusion.py` | 15 | Pause / Reference / Let go at item, LO and subject scope (9); resuming; an excluded request; review load; intent off; held-out never selected by an LO check or an item check |
| `test_intent_checks.py` | 10 | `due_hint` (datetime, date-only) and the default delay; `capture.test_me_later_days`; settling once, only answered checks, not before the date; the served check's view (banner, help header, locators hidden); the way back present / absent; ordinary attempts; a Reader check is a request only when dated |
| `test_intent_goal_deadline.py` | 4 | Learner goal created and linked by `goal_id`; moving keeps the goal; the link does not move the choice time; needs an active depth |
| `test_intent_plan.py` | 12 | Check in maintain, not requests-first; waiting check and pause out of the plan; minutes bound several checks (10 and 40 minutes); push from Learn; admission Learn first, Keep none; re-entry drops Light touch and orders by tier; chooser views; no-commitment plan equals intent off; plan report fallbacks; re-entry panel; assumed as Keep |
| `test_intent_rpc.py` | 6 | `get_intent` / `set_intent` / `set_intent_deadline`; `intentCheck` on a session serve (not on others or read-only opens) and on feedback; intent off; refusals |
| `test_mobile_allowlist.py` | +6 | The pinned list equals the handler's; the three intent RPCs and the two extended reads pinned desktop-only |
| Vitest `IntentControl.test.tsx` | 8 | Optional / none selected; consequence and cost before a choice; apply; inherited source; deadline; off; no focus; one line |
| Vitest `PracticeScreen.intentCheck.test.tsx` | 6 | Cold banner and no locators (simple, classic); help ladder before the hint, then taken (simple, classic); the hint key again takes it; ordinary items unchanged |
| Vitest `IntentCheckFeedback.test.tsx`, `app/intentCheck.test.ts` | 2 + 3 | The feedback line and the way back; the Reader target |

Changed existing tests: `test_mobile_allowlist.py` only. `PracticeScreen.adaptiveOff`'s
byte snapshots (the practice card with no check) pass unchanged.

## Files

- New: `src/learnloop/scheduling/intent/` (`model`, `resolution`, `recall_targets`,
  `serving`), `src/learnloop/intent/` (`control`, `checks`, `deadline`, `report`),
  `src/learnloop/daily_plan/intent_cost.py`, `src/learnloop/db/stores/intent_reads.py`,
  `src/learnloop_sidecar/handlers/intent.py`; desktop `components/IntentControl.tsx`,
  `components/IntentCheckFeedback.tsx`, `app/intentCheck.ts`; the tests above,
  `tests/intent_fakes.py`.
- Changed: `scheduling/scheduler.py` (four hooks), `db/repositories.py`
  (`skip_commitment_ids`), `daily_plan/engine.py`, `lanes.py`, `reentry.py`,
  `cli/plan.py`, `config/schema.py` (`[intent]`, `[capture]`), `config/template.py`
  (snapshots), `params/parameter_registry.py`, `pyproject.toml` (one ignore), sidecar
  `handlers/__init__.py`, `daily_plan.py`, `feedback.py`, `practice.py`, `queue.py`;
  desktop `commands.rs`, `main.rs`, `client.ts`, `dto.ts`, `App.tsx`, `BookCard.tsx`,
  `InspectorOverlay.tsx`, `FeedbackScreen.tsx`, `PracticeScreen.tsx`; the reference
  generator's section map and the regenerated references (925 leaves, 64 sections).
- No migration (217 unused). Tracked working vaults untouched.

## Owner commands

Run on a backup-API copy first, then the live vault when satisfied (never the tracked
fixtures).

```bash
# Nothing to upgrade: intent acts at every version, and with no commitment nothing changes.
uv run learnloop plan report --vault "$VAULT" --json   # see "intent": what is committed, fallbacks
# Kill switches (add to learnloop.toml):
#   [intent]
#   enabled = false                 # serving reads commitments only for requests, as before DL2
#   recall_targets_enabled = false  # keep exclusion, checks, push; serve every item at its due_at
# The target table (Q8):
#   [intent.recall_targets]
#   keep_in_touch = 0.80
#   remember_key_ideas = 0.85
#   work_fluently = 0.90
#   master_tasks_like_these = 0.92
#   uncommitted = 0.90
# The "Check once" delay without a due_hint:
#   [capture]
#   test_me_later_days = 7
```

## Open questions (each with the default in force)

1. **Q8, the target table** (owner checkpoint): Light touch 0.80, Keep 0.85, Learn 0.90,
   Master 0.92, uncommitted 0.90 (accepted 2026-10-12).
2. **`intent.enabled` default on** (frictionless: with no commitment it is today's
   behaviour). Keep?
3. **Reader "test me later" on an item** is a "Check once": one check after the delay,
   then nothing until a later choice. The owner vaults have none on items today (only
   source locators); RW1b's "reconstruct" items will follow this rule. Keep?
4. **"Let go"** is the `stopped` disposition (history kept, reversible by a later choice),
   not `retire`. Keep?
5. **Removing a deadline**: not offered (move only). Add "remove" (pause the goal)?
6. **The control's placement**: inspector (topic, item), subject from the topic, book card
   details. A control on Today's plan items or the knowledge map as well?

## Friction notes

- **RW6b**: create follow-ups as `test_me_later` commitments with `due_hint` (ISO date or
  datetime) and `provenance` carrying `inquiry_root_event_ids`, `anchor_span_ids`,
  `source_id`, `extraction_id` and `restoration_label` ("Mixture CDF → integration
  bounds"); DL2 serves, dates, settles and links them. Use a unique client idempotency key
  per follow-up. `answered_check` currently shows the way back after any answered check;
  RW6b's "only when wrong or with help" rule belongs in its own view. The plan line can
  take RW6b's purpose and *why* through the lane reason (DL2's says "check · on your own").
  Note `append_commitment_version` clears `due_hint`/`provenance` on later versions;
  resolution reads `via` and the restoration from version 1 and the latest non-null
  `due_hint`.
- **RW7a**: the depth choice ("get the idea / learn to use it / fluency") should call
  `set_intent` on the source scope (Master = fluency, Learn = learn to use it, Keep and
  Light touch = get the idea) so the Guide's choice and DL2's stay one setting; the
  source scope resolves the source's current readings' LOs.

## Gate (implement step; targeted, per the owner rule of 2026-10-17)

The full pytest suite, the whole durability lane and the whole vitest run are the landing
gate's. Run here, with `TMPDIR` in the worktree's `fixtures-local/tmp`:

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | OK |
| `uv run lint-imports --no-cache` | **28 kept, 0 broken** |
| `pytest -n auto` on the 7 new `test_intent_*` files, `test_mobile_allowlist.py` and the contract pins (`test_architecture`, `test_config_refactor`, `test_registry_audit`, `test_sidecar_registry`, `test_sidecar_serializer_snapshot`, `test_cli_help_snapshot`, `test_desktop_rpc_contract`, `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_vault_template`, `test_ai_config`, `test_plan_determinism`, `test_reading_step_switch`, `test_mvp015/016/017/018/022_upgrade`, `test_method_explicit_upgrade`, `test_diagnosis_input_provenance`, `test_sqlite_file_copies`) | **594 passed** |
| `pytest -n auto` on the 133 existing files that exercise a changed module (`git grep` for `build_due_queue`, `_forgetting_risk`, `requested_practice_item_ids`, the plan engine, lanes, re-entry and report, `get_practice_item`, `get_feedback`, `get_today_queue`, `prepare_queue_build`, the plan RPCs, `cli.plan`; list in `fixtures-local/tmp/dl2-affected.txt`) | **2,978 passed** (on `462f02eaf`; later commits add tests and docs only) |
| `pytest -m durability` on those files and `test_daily_plan_replay.py` | **12 passed** |
| the intent tests with `--durable-sqlite` | **84 passed** |
| `npm run typecheck` | clean |
| vitest: the 4 new files and the 18 touched screens' files | **236 passed in 22 files** |
| `npm run frontend:build` | OK (existing chunk-size warning) |
| `cargo check` | OK |
| `db_generate_reference.py`, `db_validate_reference.py` | **0 errors** (925 leaves in 64 sections; prose counts updated; the rest is commit labels) |
| Tracked working vaults | untouched (copies only) |
