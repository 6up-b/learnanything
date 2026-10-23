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

> **Superseded (Codex re-review F2, 2026-10-20):** DL2 is the successor `mvp-0.29`
> behind `intent.enabled`. The follow-up gate (review F1) withholds a paused item's
> pending cold retry, which changes which items are served as measurements, so the
> 2026-10-17 rule (`docs/algorithm-change-playbook.md`) applies. See
> `docs/reviews/daily-loop-dl2-codex-review.md` ("Re-review").

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

> **Superseded (Codex re-review F2, 2026-10-20):** intent is the successor `mvp-0.29`
> (`intent_v1`), gated on the version and `intent.enabled`; below the tag every serve
> path and plan run the predecessor's code. Conditions 1 and 2 below still hold (no
> projection change, replay never reads intent), which is why the tag needs no
> migration and its upgrade is a tag change plus the idempotent projection rebuild.

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
# Intent is the successor mvp-0.29 (Codex re-review F2): back up, then upgrade (from
# mvp-0.27 here, mvp-0.28 after AD2+AD3 lands; from mvp-0.9 onwards through the chain).
uv run learnloop upgrade --vault "$VAULT" --to mvp-0.29
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

## Codex review (fix step)

The Codex review of `bbb0b05d3` (job `20261020-000102-fgOsoH`) and its fixes are in
`docs/reviews/daily-loop-dl2-codex-review.md`: F1 and F3-F10 fixed (intent at follow-up
insertion and in plans already built; "Check once" through the one eligibility decision
with an honest practice label; held grades never anchor; the review interval from the
anchor; re-entry's order through the chooser; reading by the source's intent; deadline
goals scoped by facets, recoverable and serialized; the headline's population by
intent). F2 (an `intent_v1` successor) rejected under the standing live-change ruling,
an open question there. Where this file's claims above differ, that file is current.

## Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/dl2-onto-main`, cut from main at `3988cf778` (the
RW4b landing, migration head 213; RW1c and RW4b landed after DL2 branched from `fab576ac1`). The stage tip is
`0dfe9f5bc`, unchanged. The orchestrator's last verify (Codex job `20261020-154253-UY2KgG` on `0dfe9f5bc`) left one
Medium, F23, ruled non-blocking (open items below). Main was neither fast-forwarded nor pushed here.

### Commits and conflicts

- `8bb003dae`: a `--no-ff` merge of `daily-loop/dl2` onto `3988cf778`. One source conflict:
  - `config/template.py`: RW1c's, RW4b's and DL2's notes kept on every defaults snapshot (DL2's `[intent]` /
    `[capture]` note under mvp-0.9's, a one-line pointer on the others), DL2's `mvp-0.29` entry added, and all
    **20** snapshots (mvp-0.9 … mvp-0.27, mvp-0.29) recomputed from the composed defaults.
  - 399 generated reference notes took main's side and were regenerated afterwards.
  - Auto-merged without conflict, then read: `daily_plan/engine.py` (RW4b's keyed `learner_pick` with `within=`,
    the strict presentation write, `pick_keyed`, `picked_under` and `_pick_new_block` sit beside DL2's
    `_select_checks`, the `CheckGate` call path and `checks_unplanned`; DL2 never touched `learner_pick`, and RW4b
    never touched the pool, admission or reconcile), `scheduling/scheduler.py`, `PracticeScreen.tsx`, `dto.ts`,
    `client.ts`, `config/schema.py`, `params/parameter_registry.py`, the sidecar handler registry, the RPC pins
    (`test_mobile_allowlist.py`, the desktop contract), `commands.rs` / `main.rs` and the CLI help snapshot.
  - Comments only, in the merge commit: `algorithm_versions.py`, `intent_upgrade.py` and the template's mvp-0.29
    note now say DL2 landed first with predecessor mvp-0.27, so mvp-0.28 is never used on main and AD2+AD3 lands as
    mvp-0.30 (they said the landing would chain mvp-0.29 after mvp-0.28).
- `406510934`: the references regenerated on the merged tree.
- `51802ebbb`: the interaction test (below).
- This record.

**A keyed learner pick of an item with a "Check once".** No test covered it, so
`tests/test_dl2_rw4b_keyed_pick_check.py` (3 tests) pins it on the merged tree:
- a keyed pick (`idempotency_key`, `within`) of a **planned due check** serves the check's own planned block (no
  second learner-pick block), writes one `pick_keyed` receipt, runs `within` once, keeps the served view the check
  on your own (`cold`), returns the same presentation on retry and writes nothing, and its answer on your own
  satisfies the check;
- a keyed pick of a **due check the plan does not hold** (a dated Reader check created after the plan was built)
  is the learner's one-item block, and its answer satisfies the check too;
- a keyed pick of an item a **waiting check holds** is still the learner's own pick (L3), and its attempt before the
  date answers nothing (`one_check_pending`).

All three pass on the merge commit: the two stages compose with no code change.

### The successor chain

Kept exactly as built: `INTENT_ALGORITHM_VERSION = "mvp-0.29"`, appended to `SUCCESSOR_CHAIN` after
`ELIGIBILITY_DECISION_ALGORITHM_VERSION` (mvp-0.27); `LATEST_ALGORITHM_VERSION` = mvp-0.29; `INTENT_VERSIONS`
= `successors_from("mvp-0.29")`; `intent_upgrade.PREDECESSOR` = mvp-0.27 with `upgrade_to_mvp027` chained and
`_CHAINED_PREDECESSORS` = mvp-0.9 … mvp-0.26; the CLI's `upgrade --to mvp-0.29` branch and its "expected" list;
the projection namespace stays mvp-0.8's (every chain tag inherits it). On the merged tree the 59 files that pin
the chain, the snapshots, an upgrade or the RPC/CLI contracts (`fixtures-local/tmp/dl2-landing-pins.txt`: every test
naming `SUCCESSOR_CHAIN`, `LATEST_ALGORITHM_VERSION`, `DEFAULTS_SNAPSHOT_BY_ALGORITHM`, `upgrade_to_mvp0*`,
`INTENT_ALGORITHM_VERSION` or `mvp-0.29`, plus the contract pins) ran **1,205 passed** before the full suite.
Upgrades run on copies: `--to mvp-0.29` from mvp-0.27, the owner's chain from mvp-0.8 (`--to mvp-0.9`, `--to
mvp-0.27`, `--to mvp-0.29`) and the chained form from mvp-0.9 (`--to mvp-0.29` directly) all succeed (parity (b)).

### Regeneration

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, `schema_head` 213,
  333 table notes, **929** configuration leaves in **66** sections (DL2's `[intent]` and `[capture]` on RW4b's
  921 / 64). The two prose counts in `Configuration.md` and `Database.md` were moved by hand; the rest is commit
  labels, DL2's tests in the table notes and the two new field notes (403 files).
- **Defaults snapshots.** With the template's `.pyc` cleared, all **20** `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries
  (mvp-0.9 … mvp-0.27 and mvp-0.29) match `defaults_fingerprint_for_version`. Recomputed in the merge commit.
- **CLI help snapshot, RPC pins** (serializer snapshot, desktop RPC contract, mobile allowlist, sidecar registry):
  passed in the pin run above; no file needed rewriting. DL2's RPCs (`get_intent`, `set_intent`,
  `set_intent_deadline`) and the two extended reads stay desktop-only, as its review pinned them.
- **`validate_vault.py`**: passes (1,133 notes, 1,131/1,131 reachable).
- **Known failures from before this stage, not fixed:** `desktop_validate.py` still stops on
  `components/pdfSelection/testing/syntheticBook.ts`; `module_validate.py` reports **948** issues (914 at the RW4b
  landing: DL2 adds modules without module notes, such as `learnloop/intent/` and `scheduling/intent/`).

### Gate

Python 3.12.14. `TMPDIR` was merge2's `fixtures-local/tmp`; every command after the install ran as `uv run
--no-sync`. Both suite lanes ran under `flock /tmp/learnloop-fullsuite.lock` on `51802ebbb` (the gate head; this
record changes docs only). The AD2+AD3, RW3b and RW4d worktrees and their processes were not touched. Every test
uses fakes. **This is the first full run over DL2's code**: the stage and its 7 fix rounds ran targeted tests only.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `lint-imports --no-cache` | **28 kept**, 0 broken |
| full suite `pytest -n auto` | **14,783 passed, 2 xfailed, 0 failed** (24 min 9 s; `fixtures-local/dl2-landing-fullsuite.log`). RW4b's landing ran 14,486 |
| `pytest -m durability` | **113 passed**, 14,672 deselected (3 min 49 s; `fixtures-local/dl2-landing-durability.log`) |
| `npm install`, `npm run typecheck` | up to date; clean |
| `npm test` (the whole vitest run) | **154 files, 1,206 tests passed** on the first run. The `FeedbackScreen` flake did not fire |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | ok. DL2 added three passthroughs to `commands.rs` / `main.rs` (10 lines) |
| thread, lock and timing tests | all passed on the first run, so none was rerun. The `"8841"` MCP flake and `test_voi_v2` did not fire |
| tracked fixtures, worktree | `git status` clean after both lanes and the frontend run; no non-empty `-wal` beside a fixture |

No failure, so no landing fix.

### Parity (backup-API copies; no model call completed)

**Setup** (as at the RW4b landing; scripts in `fixtures-local/landing-dl2/scripts/`):
- **Copies.** `fixtures/linear_algebra` and `fixtures/probability` were copied once, with `copy_tree_with_databases`,
  from the main checkout into `fixtures-local/landing-dl2/orig/`. Every other copy came from `orig/` or its upgraded
  copies through the same helper. `arxiv_v2` was not opened. Both vaults start at schema 165, label `mvp-0.8`.
- **Code.** Main's code is `git archive 3988cf778`; the merge's is `git archive 51802ebbb`.
- **Environment.** Every run went through `env -i` with only `PATH`, `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`,
  `TMPDIR` and `LANG` (empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`).
- **Routes.** `neutralize3.py`, under each code, sent all 55 routes to `127.0.0.1:9` (the reader, tutor, sources,
  hint, workbench, AD and Decider routes included); `query_rewrite`, `tutor_query_rewrite`, `tutor_rerank`, `dense`,
  `[embedding]` and `[learner_text_gaps]` off; `build_on_serve` and outcome placement off. `routes.py` resolved all
  58 `AITask`s on both codes: nothing outside the two loopback profiles except `embedding`, disabled and keyless.

**(a) Below the successor**

| Check | linear_algebra | probability |
|---|---|---|
| open (migrate), main's code / the merge's | 165 → 213 (48) / the same | the same |
| schema, main@213 vs merge@213 | **identical**: 1,414 objects, none on one side only, no SQL differs | **identical** (1,413) |
| rows of every table (338), all columns | **identical** (16,539 rows); `schema_migrations` differs only in `applied_at` | **identical** (7,637 rows; the same) |
| `foreign_key_check` / `integrity_check` | 0 / ok, both sides | the same |
| `rebuild --shadow --json` | **0 differences** after normalisation (facet 0, mastery 2, schedule 8); live database unchanged on both | **0 differences** (0 / 1 / 1) |
| `doctor --json` | **0 differences** after normalisation (57 issues, 1 error) | **0 differences** (101 issues, 48 errors) |
| at `mvp-0.8`: certification, recipe gaps, curves; the Today queue at a frozen clock (no session, a session, greedy); the daily plan | **byte-identical** (cert 132,860 bytes; queue 41; the plan is off below mvp-0.14) | **byte-identical** (cert 17,494; queue 67) |
| upgraded by main's code to `mvp-0.27` (`--to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice; all rc 0), opened by each code: certification and curves, Today queue | **byte-identical** (129,651 bytes; queue 43) | **byte-identical** (17,495; queue 67) |
| the daily plan at `mvp-0.27` (frozen clock: read, serve, serve again, read) | identical except `router_decisions.card_hash`, `snapshot_hash` and the card hash inside `detail_json`; a second run of main's code differs from the first in exactly these three | the same |

**(b) The upgrade to mvp-0.29** (the merge's code)

| Check | linear_algebra | probability |
|---|---|---|
| `upgrade --to mvp-0.29` on main's mvp-0.27 copy | rc 0, "mvp-0.27 -> mvp-0.29", label `mvp-0.29` | the same |
| rows vs the mvp-0.27 source | every table present on both, no SQL differs; **no row removed** from any table. Changed: `facet_capability_evidence` (36) and `facet_recall_state` (76), DERIVED, identical except the `algorithm_version` stamp; `parameter_registry` + 6 rows (`capture.test_me_later_days` and the five `intent.recall_targets.*`), `parameter_registry_manifests` + 1, `derived_state_rebuilds` + 1 | the same (1 and 2 derived rows; the same 6 + 1 + 1) |
| `rebuild --shadow` right after the upgrade | facet 0, **mastery 21**, schedule 0: all 21 are the `algorithm_version` stamp of `mastery_state` rows (mvp-0.27 → mvp-0.29), no value differs; live database unchanged | facet 0, mastery 18 (stamp only), schedule 0 |
| the owner's chain from mvp-0.8 (`--to mvp-0.9`, `--to mvp-0.27`, `--to mvp-0.29`, `rebuild-derived-state` twice) | all rc 0; `rebuild --shadow` **0 / 0 / 0** | the same |
| the chained form (`--to mvp-0.9`, then `--to mvp-0.29` straight from mvp-0.9; `rebuild-derived-state` twice) | rc 0 ("mvp-0.9 -> mvp-0.29"); shadow **0 / 0 / 0** | the same |
| at the frozen clock, no commitments, mvp-0.29 vs mvp-0.27 (same code): Today queue | **byte-identical** (528,665 bytes) | **byte-identical** (741,269) |
| certification and curves | identical except the `label` (the version) | the same |
| the daily plan | identical except `plan.algorithmVersion` (4 responses) and `router_decisions.algorithm_version`, plus the three card-hash fields that differ between any two runs | the same |

**(c) Intent at mvp-0.29 through the real sidecar** (stdio; `SystemClock` read from a file the driver moves;
`intent_run.py`) on a copy of probability at mvp-0.29. The same RPC sequence ran on the mvp-0.27 copy (`cbase`) and on
mvp-0.29 with `[intent] enabled = false` (`dioff`).

| Step | Result at mvp-0.29 |
|---|---|
| `get_intent` on `pi_prob_derive_complement` (X) | enabled, "No setting", eight choices with consequences and costs ("Check once": "one check on your own in 7 days … about 4 min") |
| `set_intent` X **Check once**; Y (the queue's head, `pi_three_independent_birthd`) **Let go** | both applied. Tables written: `commitments`, `commitment_versions`, `commitment_target_versions`, `commitment_events`, `depth_policy_versions`, `depth_envelope_versions` (the commitments API) and `queue_state` (WORKFLOW, the queue revision). **No** `practice_item_state`, mastery, facet, evidence or projection table moved |
| the queue and plan right after | queue 67 → 65: X (waiting) and Y gone; today's plan, built before the choices, displaced Y (`item_displaced`, `intent_stopped`) |
| `set_intent` Learn on `lo_construct_a_combinatorial_proof_of_an_identity`, `set_intent_deadline` 2026-12-01 | a learner goal `goal_intent_…` in `profile/goals.yaml`, `target_recall` **0.90**, due 2026-12-01T23:59:59Z |
| `set_intent` Master, then `set_intent_deadline` 2026-12-15 (the move) | the same goal, due **2026-12-15**, `target_recall` **0.92**. The move wrote no table (the link stands; `queue_state` only). Its title still reads "(Learn) by 2026-12-01" (accepted Low) |
| clock + 8 days: `start_session`, `get_today_queue`, `get_daily_plan` | X is back in the queue; the plan holds it as a **planned check**: `check_once` in the maintain lane ("your one delayed check"), `checks` = [X], `checks_unplanned` = []; Y absent |
| `get_practice_item` X (session serve) | `intentCheck`: the cold banner, `cold: true`, the help-ladder header, `locatorsHidden: true`, date source `test_me_later_days` |
| `submit_attempt` X on your own (manual grade 4/4, `hintsUsed` 0), acknowledge, `get_feedback` | feedback carries `intentCheck` (no restoration: no provenance); 5 minutes later the next queue build settles it: `disposition_changed` → **satisfied**, `administration_id` = the attempt |
| clock + 30 days | Y never in the queue or any plan (Let go is stopped); X, answered, no longer served by intent; `next_plan_item` serves nothing |
| the check's attempt vs `cbase` and `dioff` (the same submission at the same instant) | **identical** evidence fields: `open_text`, `hints_used` 0, `primed` 0, correctness 1.0, rubric 4, `evidence_origin` human, `desktop_practice`, the same facets and weights, FSRS-eligible activity, 0 reveal rows; the resulting `practice_item_state` (stability 8.2956, difficulty 1.0, due 2026-11-06T01:50:39Z) identical |
| `cbase` and `dioff` | `get_intent` answers `enabled: false`; every `set_intent` / `set_intent_deadline` refuses ("Intent settings are off … need algorithm version mvp-0.29 or later and intent.enabled = true") and writes nothing; the queue stays 67 at every step; Y is served at +30 days |

**(d) The kill switch.** `[intent] enabled = false` at mvp-0.29, against (b)'s no-commitment mvp-0.29 reads: the
Today queue and certification **byte-identical** on both vaults; the daily plan identical except the three
card-hash fields that differ between any two runs. Through the sidecar (`dioff` above) it behaves as `cbase`.

**`model_call_receipts`**: 0 rows in all 33 learner databases under `landing-dl2/` that carry the table (every
copy, run and base); none `completed`. The other 18 `state.sqlite` files are probability's empty
`.learnloop/state.sqlite`, which have no such table.

### New findings

1. **No composition failure.** RW4b's keyed pick and DL2's checks compose as built; the new test pins it.
2. **`upgrade --to mvp-0.29` leaves `mastery_state` stamped with the old version until a derived-state rebuild.**
   A shadow rebuild right after the upgrade reports one mastery "change" per LO, and every one is the
   `algorithm_version` stamp; no value differs, and `rebuild-derived-state` clears it (shadow 0 / 0 / 0). The
   upgrade's body is `upgrade_to_mvp027`'s (`activate_p0_projection`), so this is the predecessor's behaviour;
   the owner commands below include the rebuild, as the earlier landings' upgrade method did. Low.
3. **The control's "current" keeps the choice after a check is answered** (`get_intent` still says "Check once";
   the disposition is `satisfied`). That is the spec's label for the setting; the check view itself is gone.
   Display only.
4. **Moving a deadline writes no table** when the depth's link already stands: the goal file is rewritten
   (due and `target_recall`), and the queue revision bumps.

### For the owner

- **The successor mvp-0.29.** Back up the vault, close the app, the MCP server and the mobile host, then upgrade.
  Your vaults are at mvp-0.8, so run the chain:

  ```bash
  uv run learnloop upgrade --vault "$VAULT" --to mvp-0.9
  uv run learnloop upgrade --vault "$VAULT" --to mvp-0.27
  uv run learnloop upgrade --vault "$VAULT" --to mvp-0.29
  uv run learnloop rebuild-derived-state --vault "$VAULT"   # restamps mastery rows (finding 2)
  uv run learnloop rebuild --shadow --json --vault "$VAULT" # expect 0 / 0 / 0
  ```

  (`--to mvp-0.29` straight from mvp-0.9 also works: it runs the mvp-0.27 step first.)
- **mvp-0.28 is skipped on main.** DL2 landed before adaptive difficulty AD2+AD3, which will land as **mvp-0.30**
  with mvp-0.29 as its predecessor. The tag mvp-0.28 is never used on main.
- **What you see.**
  - An intent control (Master, Learn, Keep, Light touch, Check once; Reference, Pause, Let go) in the inspector for a
    topic and for an item, for the whole subject (from a topic: "set for all of …") and on a book card's details.
    Hovering or focusing a choice shows what it replaces and its cost ("about N min/day of reviews") before you
    take it. With Learn or Master chosen you can add or move a deadline (a goal; not remove one yet).
  - **Check once**: the item leaves your reviews and comes back once, after 7 days (`[capture]
    test_me_later_days`, or a Reader check's own date), as a check on your own: a cold banner, the book named but no
    exercise number, page or section until feedback, and help that is never blocked but turns the attempt into
    practice with help. The plan puts due checks first in its minutes; one it cannot fit is recorded with its
    reason. When a check came from the Reader with a place to return to, feedback offers "Back to where you
    studied this" (RW6b's follow-ups will carry it).
  - Pause, Reference and Let go keep an item out of everything served; Light touch and Keep add no new material;
    Learn and Master pull material forward before it is due; reviews follow each choice's recall target.
  - With no setting anywhere, nothing changes (parity (b)).
- **The kill switches.** `[intent] enabled = false`: serving and the plan as at mvp-0.27, the control answers
  "off" (parity (d)). `[intent] recall_targets_enabled = false`: exclusion, checks and push stay, every item is
  reviewed at its stored due. Rolling the version back is restore-only.
- **The Q8 target table** (`[intent.recall_targets]`, accepted 2026-10-12):

  | Choice | Key | Target |
  |---|---|---|
  | Light touch | `keep_in_touch` | 0.80 |
  | Keep | `remember_key_ideas` | 0.85 |
  | Learn | `work_fluently` | 0.90 |
  | Master | `master_tasks_like_these` | 0.92 |
  | no setting | `uncommitted` | 0.90 |

### Open questions (defaults in force)

1. **Q8, the target table** above: kept as accepted.
2. **`intent.enabled` on by default** (with no setting it is the predecessor's behaviour): **on**.
3. **A Reader "test me later" on an item is a "Check once"** (one check after the delay, then nothing until a later
   choice): **yes**.
4. **"Let go" is the `stopped` disposition** (history kept, reversible by a later choice), not `retire`: **yes**.
5. **Removing a deadline**: **not offered** (move only).
6. **Where the control lives**: the inspector (topic, item), the subject from a topic, the book card's details;
   **not** on Today's plan items or the knowledge map yet.

The Codex rounds' own open questions (a hold that lapses between serve and submit: read at submission; the probe
contract carrying the diagnostic variant) keep their defaults, as recorded in `daily-loop-dl2-codex-review.md`.

### Open items

- **F23 (Medium, ruled non-blocking by the orchestrator).** A storage error in the shared serving-exclusion reads
  aborts the whole plan build before the check gate runs. That is the predecessor's existing fail-closed, visible
  behaviour, and nothing unchecked is admitted.
- **Accepted Lows:**
  - requests (L3) are placed without the frame's verdict (R2a's design);
  - a deadline goal's title keeps its creation depth label (seen in parity (c): "(Learn) by 2026-12-01" after
    Master and a move);
  - a reserved candidate served in its own assessment flow shows as the check;
  - the check gate's snapshot covers only the check candidates;
  - the practice-item serve can't see an active diagnostic before the probe contract arrives;
  - a limited session queue may postpone a check.
- **Finding 2** (the mastery stamp until a derived-state rebuild after the upgrade; Low).
- **Friction notes for RW6b and RW7a** stand as written above (follow-ups as dated `test_me_later` commitments with
  provenance; RW7a's depth choice through `set_intent` on the source scope).
- **From before this stage:** `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (948 issues).
