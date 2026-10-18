# Adaptive hints H2b: adaptive hints on the practice screen (stage `hints-h2b`)

Branch `hints/h2b` (worktree `learnanything-merge4`), base `main` at
`5b2efaf24` (H2a landed; migration head 211). Spec:
`docs/specs/spec_adaptive_hints_v1.md` §2, §4.2, §4.7, §4.8, §5, §6.1, §6.3
(descriptive rows, the expertise-reversal split, abuse and avoidance counts,
latency and cost; not the off-policy estimates, H5), §7.3, §9, §10 (H2 row),
§11 (G-H1, G-H3, G-H12, G-H15, G-H16, G-H17), §12 (D5, D11, D13, D15-D17);
`docs/reviews/adaptive-hints-H2a.md` §8, §9 and "Landing onto main";
`docs/specs/ux_reader_workbench_v1.md` §5.6, §5.7.

## 0. Plan (written before the code)

**Scope.** H2b completes H2: the practice-screen panel over H2a's RPCs, the
authored-reveal evidence ruling, outcome placement, the per-kind report rows,
the `hint_feedback` learner-text adapter with migration 212, and the wording
lint over the new strings. Out of scope: off-policy estimates (H5), the
workbench (RW2b/H3), guided redo and the tutor (H4), the inline map build on a
hint, unsolicited hints. H2a's fold, fence, delivery and contracts, H0's
attach and H1's validator and lifecycle are called, not reworked; the one
change to H2a's delivery is the authored-reveal ruling.

**1. The practice screen** (`apps/learnloop-tauri`; new files under
`src/screens/practice/`):
- `algoConfig` reads a `hints` key the sidecar sends only while adaptive hints
  are on (`hints.adaptive_enabled` and `hints.telemetry_enabled`), with
  `authored_offer_after_seconds` and `help_style`; absent, every path is the
  base's (G-H1, checked byte for byte against file snapshots written on the
  base before any change).
- `KeyBar` entries may carry an `onClick`: the `^h hint` entry becomes a
  button with the same label and key, only while adaptive hints are on
  (D13: nothing else is added; the plain card's existing *Hint* button calls
  the same press).
- `useAdaptiveHints` (hook): a press flushes the draft, calls
  `practice.request_hint` and paces `practice.hint_job` polls; `disabled`
  falls back to today's authored path exactly; the diagnostic-block refusal
  and the cold-check banner are unchanged. After
  `hints.authored_offer_after_seconds` (4, a new display cap) a pending
  request with an authored hint left offers *use the item's hint instead*:
  `practice.cancel_hint` first, then the existing client reveal
  (`practice.record_hint_reveal`, client-counted); a cancel answering
  `already_shown` keeps the adaptive hint. One hint recorded (G-H3).
- `HintPanel` (component): every hint in order with its labels
  (`result.labels`: *AI-written* / *from the item*, the kind in plain words,
  the horizon words, *worked help ◌*); one quiet line under each (*this
  doesn't connect to my work… · show me the book's way*, and first *a smaller
  step toward this goal* under a waypoint, from `result.replies`); the
  feedback box (the four shortcuts each saying what it does; *that's not
  where I'm stuck* lets the learner pick the lines of the draft they mean,
  sent as `feedbackSelection`; *say more (optional)*; an empty submit is
  allowed; the next hint is requested at once at the same level); the
  worked-help picks from `result.picks` with their consequence stated before
  they are taken; the discriminating question's label, its own one-line
  answer box (never the draft), *↵ answer · skip to a hint*, then the line
  `practice.answer_discriminating` returns; the "⋯" help-style menu.
- Help style: no generic config write exists (each Settings section has its
  own `update_*` RPC), so the narrowest one is added:
  `practice.set_help_style {helpStyle}` (desktop only, pinned) writes
  `[hints] help_style` through `ops.settings_store.apply_config_updates` and
  reloads, as `reader.set_cue_preferences` does; the panel's "⋯" menu and a
  Settings row call it.
- Tauri passthroughs for the five RPCs; `cargo check`.

**2. The authored-reveal ruling** (binding, from the H2a landing finding): a
service-served `authored` hint writes NO `reveal_events` row, as the client's
reveal of the same hint writes none (§10.1 successor 3 keeps authored reveals
out of the ledger in v1); it still counts at level 3 as a server row. Every
other kind keeps §5's `tutor_answer` reveal. A test that fails on 5b2efaf24.

**3. Outcome placement** (§6.1, D11): route `hint_outcome` (chat,
structured; any profile, Codex included: background);
`hints.outcome_placement_enabled` (default on); one background call after a
hinted `submit_attempt` graded not fully correct on an item with a current
map, placing the final answer on the map; measurement only (never the grade,
diagnosis or evidence); in the maps' envelope
`hints.maps.max_daily_cost_usd`; H1's `BackgroundBuilds` registry, durable
claim, lease and fence; gated by `LEARNLOOP_APPROACH_MAP_BUILDS=off` and
`LEARNLOOP_HINT_MODELS=off` (both already set in `tests/conftest.py`) without
an injected client. Stored as `judgment_ledger` rows (task `hint_outcome`,
judge `llm`, one per shown hint row of the attempt, verdict `reached` /
`not_reached` / `unknown`, the placement in the rationale): no new table,
nothing on `help_assists` (its identity trigger and append-only intent stay).

**4. The report** (§6.3): `learnloop hints report` gains, per kind and
level, "doesn't connect" by shortcut, the level of the help that followed,
the outcome placements, and for waypoints the goals reached without more
help and the smaller steps taken; and top-level sections: the
expertise-reversal split (placement intent and P(success) at request time,
logged on the row from H2b on), help abuse (re-asks with the work unchanged,
with the gap's distribution) and avoidance (unassisted submissions not fully
correct, with their latency distribution) as counts, and latency and cost per
route (chooser, writer, outcome placement, maps: p50/p95, re-asks, withholds,
fallbacks by reason, receipts' tokens and metered cost). No model call, no
learner text, read-only; every number with its sample size, never a
threshold.

**5. Migration 212 and the `hint_feedback` adapter**: both `source_kind`
CHECKs widened with `hint_feedback` (208's temp-then-rename under `PRAGMA
foreign_keys = OFF`, the runner's `foreign_key_check`, a durability-lane
test); the adapter reads `help_assists.feedback_text` on `request =
'feedback'` rows (role `hint_feedback`) and on `assist_kind =
'discriminate_answer'` rows (role `discriminate_answer`), queued by the
sidecar when the row is written (so a gap named mid-attempt joins the next
hint's rivals), a non-serving kind like `workbench_text`. No new table, so no
`table_roles` change; `fixtures/migration_head_211` → `migration_head_212`
and its hard-coded paths; the references regenerated. The G-H17 deviation
(two widenings, 208 and 212) recorded in the spec's §15.

**6. G-H12's wording lint** over the new UI strings (a pytest over the panel's
files and the kinds' labels).

**Config** `[hints]`: `authored_offer_after_seconds = 4` (display cap),
`outcome_placement_enabled = true`; route `ai.routing.hint_outcome`; both
classified in `params/parameter_registry.py` (the numeric one); every
`DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry recomputed with the "no scoring,
scheduling, projection or serving change" note.
