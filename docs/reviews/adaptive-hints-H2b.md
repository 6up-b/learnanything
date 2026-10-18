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

## 1. What was built

### 1.1 The practice screen (`apps/learnloop-tauri`)

- `src/app/algoConfig.ts`: `adaptiveHints` (`authoredOfferAfterSeconds`,
  `helpStyle`) from the app snapshot's `hints` key, which the sidecar sends
  only while `hints.adaptive_enabled` and `hints.telemetry_enabled` are on
  (`learnloop_sidecar/context.py:config_dto`); null otherwise, and every path
  of the screen is then the base's. `setAdaptiveHelpStyle` keeps the saved
  style.
- `src/components/ui.tsx`: a `KeyBar` entry with `onClick` renders as a
  `button.keybar-control` with the same `<b>key</b> label` (styled as the
  label it was, static); entries without one render exactly as before.
- `src/screens/practice/useAdaptiveHints.ts` (the hook): a press flushes the
  draft, sends it with `practice.request_hint`, and paces `practice.hint_job`
  polls (350 ms rising to 1.5 s: latency bounds); exactly the result the
  delivering read returns is rendered; `disabled` hands the press back to
  the screen's own authored path (`revealAuthoredHint`, the base's code);
  `refused` reports the sidecar's message; `withheld` / `unavailable` show
  their one line (a withheld hint offers the worked-help picks). The authored
  offer appears once `authoredOfferAfterSeconds` pass while a job is pending
  and an authored hint is left (the lowest index shown by neither the client
  nor the service); taking it calls `practice.cancel_hint` first and, only on
  `cancelled: true`, reveals through `practice.record_hint_reveal`
  (client-counted, `hintsUsed + 1`); `already_shown` keeps the adaptive hint
  and reveals nothing. A generation counter drops late answers of an earlier
  item's request.
- `src/screens/practice/HintPanel.tsx`: appears only once a hint was asked for
  (D13); every hint in order with its label line (`origin · kind · horizon ·
  worked help ◌`, the origin once when it equals the kind, *not graded ·
  counts as a hint* on a discriminating question); one quiet line under each
  hint from `result.replies` (*a smaller step toward this goal* first under a
  waypoint, then *this doesn't connect to my work… · show me the book's
  way*); the feedback box (the four shortcuts each saying what it does, UX
  §5.7; *that's not where I'm stuck* shows the draft's lines as toggles and
  sends the picked ones as `feedbackSelection`; *say more (optional)*; an
  empty `↵ next hint` is allowed; the next hint is asked at once, the service
  keeps the level); the worked-help picks from `result.picks`, each with its
  consequence stated beside it before it is taken; a discriminating
  question's own one-line answer box (never the draft) with *↵ answer · skip
  to a hint*, then the line `practice.answer_discriminating` returns; the
  "⋯" help-style menu (the three styles with UX §5.11's lines). Nothing
  steals focus, animates or opens a modal.
- `src/screens/practice/HelpStyleSettings.tsx`: the same three settings as a
  Settings row (*Hints · help style*), absent while adaptive hints are off.
- `src/screens/practice/hintCopy.ts`: every fixed string of the panel (G-H12's
  lint reads them).
- `src/screens/PracticeScreen.tsx`: the hook and the panel wired in (below
  the authored hints' banners in the answer-box mode); a press goes to the
  service while adaptive hints are on; the plain card's existing *Hint*
  button calls the same press and shows for every item (adaptive hints serve
  items with no authored hints too); the `^h hint` key-bar entry becomes the
  control in both cards. The legacy banner list shows `hintsUsed - (the
  panel's client reveals)` authored hints, so an offer-taken hint is shown
  once (in the panel).
- `src/api/client.ts`, `src/api/dto.ts`: the five calls and their types;
  `src-tauri/src/{commands,main}.rs`: five passthroughs
  (`practice_request_hint`, `practice_hint_job`, `practice_cancel_hint`,
  `practice_answer_discriminating`, `practice_set_help_style`).

### 1.2 Sidecar

- `practice.set_help_style {helpStyle}` (`handlers/hints.py`, desktop only,
  pinned as `HINT_PANEL_RPCS`): writes `[hints] help_style` through
  `ops.settings_store.apply_config_updates` (comment-preserving, atomic) and
  reloads, as `reader.set_cue_preferences` does; no generic config write
  exists (every Settings section has its own RPC), so this is the narrowest
  one. The same style again writes nothing.
- The authored-reveal ruling in `_deliver` (`hint_service.reveal_exempt`).
- A "doesn't connect" reply with text and a discriminating answer queue a
  `hint_feedback` learner text when their row is written, and wake the
  post-attempt worker's `gaps` slot (never failing the hint).
- `submit_attempt_on` schedules outcome placement after the response is
  built (`_schedule_hint_outcome`; never on the request path).

### 1.3 The authored-reveal ruling

`learnloop.hints.service.REVEAL_EXEMPT_KINDS = {"authored"}`: a delivered
`authored` row writes no `reveal_events` row; it is still marked shown and
counted at level 3 by the server fold, which matches the client count it
replaces. Every other kind keeps §5's `tutor_answer` reveal (basis
`hint:<kind>:L<level>`). Checked on a backup-API copy of `probability`: the
codex-refused authored fallback is shown, `hints_used` 1, `primed` 0, **0
reveal rows** (H2a's landing measured one at 0.143 for the same hint).

### 1.4 Outcome placement (`learnloop/hints/outcome.py`)

`schedule_outcome_placement` (after submit; switched off, guarded or unhinted
returns before any thread) → H1's `BackgroundBuilds.launch` (the sidecar's
`ctx.map_builds`, bound to the loaded vault) → `place_outcome`: due when the
attempt is graded, not fully correct, non-empty, has shown hint rows, its item
has a current map and no verdict was written; a durable claim
`hint_outcome:<attempt id>` (task `hint_outcome_placement`) through H1's
`_claimed` (lease, heartbeat, fence); one structured call
(`OutcomePlacementV1`: route, last node reached, the answer's quote) through
`PaidCalls` with H1's fenced repository; validated in code (the map's route
and node, the node on the route, the quote in the answer), re-asked once;
then one `judgment_ledger` row per shown hint (task `hint_outcome`, judge
`llm`, left `help_assist`, right `practice_attempt`, verdict `reached` /
`not_reached` / `unknown` with the reason and the placement), written in a
fenced transaction. Metered calls need `hints.price_per_million` and join
`hints.maps.max_daily_cost_usd` (the maps' envelope now counts owner kinds
`approach_map` and `hint_outcome`). Measurement only: no attempt, reveal,
mastery, diagnosis, evidence or `help_assists` change (asserted over every
table). Switches: `hints.outcome_placement_enabled`, `hints.adaptive_enabled`
(+ telemetry), `hints.maps.enabled`; without an injected client
`LEARNLOOP_APPROACH_MAP_BUILDS=off` or `LEARNLOOP_HINT_MODELS=off` (both in
`tests/conftest.py`) start nothing. Route `ai.routing.hint_outcome` (an
`AITask`, `ROUTE_FOR_OPERATION`, `AIRoutingConfig`, a judge-route disclosure).

### 1.5 The report (`learnloop/hints/report.py`, `report_adaptive.py`; `hints-report-v2`)

Per kind and level, beside H0's columns: `doesnt_connect` (`replied`, and
`by_shortcut` from the `hint_fit` verdicts), `more_help_level` (the level of
the next hint), `outcome_placement` (reached / not_reached / unknown /
not_placed of the attached rows), `chooser`, and for waypoints
`goals_reached_without_more_help` and `smaller_steps_taken`. Unaided next
progress gains `reached_by` (`grade`, `next_placement`, `outcome_placement`)
and `not_reached` / `not_reached_by`: a hint followed by more help is settled
by the next hint's placement (the node the work had reached, on the same map
and route) when the attempt recorded no other assistance; a final answer not
fully correct by its outcome placement. Top level: `expertise_reversal` (the
same columns by placement intent and by P(success) at request time, split at
the median of the logged values, per kind and level), `help_seeking` (abuse:
two requests of one attempt in a row, the second a plain request on unchanged
work, with the gap's p50/p95; avoidance: graded unassisted submissions not
fully correct, with their latency), `routes` (the chooser's `hint_choice`
requests by status and latency, who served; the writer's requests, latency,
re-asks, withholds, downgrades, cancels, failures and writer-down fallbacks by
reason; each route's receipts: calls by status, tokens, metered cost,
seconds). `not_yet_measured` is now only `off_policy_estimates` (H5). The
service rows log `state_at_request` (placement intent, P(success)) in
`contract_failures_json` from H2b on. Read-only; it never reads
`feedback_text`, `body_md` or a receipt's text.

### 1.6 Migration 212 and the `hint_feedback` adapter

`migrations/212_hint_feedback_source_kind.sql`: 208's rebuild of
`learner_text_gaps` and `learner_text_gap_jobs`, byte for byte, with
`'hint_feedback'` added to both CHECKs (asserted against 208's text). The
adapter (`diagnosis/text_gaps/sources.py`: `hint_feedback_row`,
`hint_feedback_text`; `jobs.enqueue_hint_feedback`; `contract.py` readable and
non-serving; `judges.kind_state`'s surface line; `provenance.hint_feedback_record`
and the pipeline's write record): roles `hint_feedback` (a reply's text, with
the hint replied to and its shortcut) and `discriminate_answer` (the answer,
with the question), the item's question and LO as context, never the answer
key or worked help (a reply to a level 4-5 hint shows "worked help (not
shown)"); the gap row carries the item, so a misconception named mid-attempt
is one of the next hint's rivals (`hints.discriminating.open_rivals`,
asserted). No table added, so no `table_roles` change; `fixtures/
migration_head_211` → `migration_head_212` (git rename; a backup-API copy with
only 212 applied, `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`,
header bytes 1/1, `integrity_check` ok, `foreign_key_check` empty, no
companion files; README paragraph and chain) and every path naming it (29 test
files, both reference scripts with `SCHEMA_HEAD = 212`,
`docs/decider-tier1-migration.md`, the Database Catalog).

### 1.7 Config

`[hints] authored_offer_after_seconds = 4.0` (display cap, classified
`structural`/`display` in `params/parameter_registry.py`) and
`outcome_placement_enabled = true`; route `ai.routing.hint_outcome`. All 19
`DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries recomputed (0 mismatches) with the
"no scoring, scheduling, projection or serving change" note; the reference
notes' leaf count is 897.

## 2. Deviations (each recorded)

1. **The help-style write is a new RPC**, `practice.set_help_style` (no generic
   config-write path exists; each Settings section has its own `update_*`).
2. **Outcome placement is stored as `judgment_ledger` rows**, one per shown
   hint (left `help_assist`, right `practice_attempt`); `help_assists` is not
   updated (its identity trigger and append-only intent stay).
3. **H1's claim helpers gained `key` / `task` / `producer` keywords**
   (`map_builder._try_claim`, `_claim`, `_claimed`; defaults unchanged) so
   outcome placement takes its own durable claim through the same lease,
   heartbeat and fence; the maps' envelope counts `hint_outcome` receipts
   (`ENVELOPE_OWNER_KINDS`). H1's validator and lifecycle are otherwise
   untouched.
4. **The same answer on the same map is placed once per prompt**: a second
   attempt with an identical answer reuses the checkpointed placement
   (PaidCalls' checkpoint), so it costs no second call.
5. **"Not where I'm stuck" selects lines of the draft**, not a character
   range: the MathLive answer box exposes no selection the panel can read.
6. **A discriminating answer shows only its settled line**; no next hint
   follows unasked (G-H15). *skip to a hint* asks for "More".
7. **The panel is not restored after a restart**: its hints live in the
   screen; the server rows still count at submit, and a restored draft shows
   the client's own authored prefix as before.
8. **Steps mode (Work in steps) shows no adaptive panel**: the workbench's
   help is RW2b/H3's.
9. **The report's P(success) split is at the median** of the logged values (a
   data-relative cut reported with its value); intent is the placement
   intent as logged. Rows before H2b say `not_logged`.
10. **H0's report reads H2's rows correctly**: the hint rows' own
    `hint:`-basis reveals are not "other assistance", the server's levels 1-3
    count as recorded, and a discriminating answer is not "more help".
11. **The `hint_feedback` write record lists the item's solution as an
    input** (a hint is written from it), so nothing a reply names is released
    to the chat frontend before the solution is.
12. **The workbench's rows are no `hint_feedback` source** (`surface =
    'workbench'` is `workbench_text`'s, RW2b's adapter).
13. **No inline map build on a hint** (§4.3.1 row 2): it needs a fast route
    (the map route resolves to Codex on the owner's vaults). Not built.

## 3. Gates covered

G-H1 (vitest `PracticeScreen.adaptiveOff.test.tsx`: the plain and classic
cards, with and without authored hints, before and after two Ctrl+H, equal
byte for byte to file snapshots written on `5b2efaf24` before any H2b change,
and no H2a/H2b RPC called; pytest `test_hint_kill_switch.py`: the app
snapshot has no `hints` key with adaptive hints or their telemetry off and is
otherwise identical, through the sidecar's `load_vault` too; outcome
placement starts nothing with adaptive hints off; H2a's RPC and table parity
tests), G-H3 (vitest: the authored offer cancels first and records one
client reveal, `already_shown` reveals nothing, a service hint records no
client reveal; pytest `test_hint_authored_reveal_ruling.py`: one count either
path), G-H12 (vitest `hintCopy.test.ts`: every fixed string and literal of the
panel's files, and the sidecar's kind labels, pass the forbidden-wording list,
read from `learnloop/hints/kinds.py` so the two lists cannot drift; worked
help is marked), G-H15 (vitest: replies go to the next request at once with
the answered hint, shortcuts, text and selection; the picks; no hint
unasked), G-H16 (vitest: the answer box is its own, never the draft; the
settled line), G-H17 (migration 212's tests, the deviation recorded in §15),
the authored-reveal ruling (a test that fails on `5b2efaf24`), outcome
placement (`test_hint_outcome.py`), the report (`test_hint_report.py`), the
adapter (`test_hint_feedback_texts.py`).

## 4. Tests

New pytest (40, fakes only): `tests/test_hint_authored_reveal_ruling.py` (3;
the first two fail on `5b2efaf24`), `tests/test_hint_outcome.py` (14),
`tests/test_hint_report.py` (7), `tests/test_hint_feedback_texts.py` (8),
`tests/test_hint_feedback_widening.py` (4, one durability-lane),
`tests/test_hint_kill_switch.py` (+4, 9 in all). New vitest (27):
`src/screens/PracticeScreen.adaptiveOff.test.tsx` (4) with its four file
snapshots under `src/screens/__snapshots__/`,
`src/screens/PracticeScreen.adaptiveHints.test.tsx` (17),
`src/screens/practice/hintCopy.test.ts` (4),
`src/screens/practice/HelpStyleSettings.test.tsx` (2). Changed:
`tests/test_hint_telemetry.py` (report v2, the config keys),
`tests/test_judge_routes.py` (the `hint_outcome` disclosure),
`tests/test_mobile_allowlist.py` (the H2b pin),
`tests/test_learner_text_source_widening.py` (212 is the recorded second
widening), `tests/test_help_assists_schema.py`,
`tests/test_library_asks_migration.py`, `tests/test_approach_maps_schema.py`
(212 on the way to head), `tests/test_route_rules_in_grader.py` (head 212),
the head-fixture paths in 29 test files, `tests/cli_help_snapshot.json` (the
report's help text).

## 5. Files

- Frontend: `apps/learnloop-tauri/src/screens/practice/{useAdaptiveHints.ts,HintPanel.tsx,HelpStyleSettings.tsx,hintCopy.ts}`
  (new), `src/screens/{PracticeScreen,SettingsScreen}.tsx`,
  `src/components/ui.tsx`, `src/app/algoConfig.ts`, `src/api/{client,dto}.ts`,
  `src/styles/app.css`, `src-tauri/src/{commands,main}.rs`.
- Python: `src/learnloop/hints/{outcome,report_adaptive}.py` (new),
  `src/learnloop/hints/{service,report,map_builder}.py`,
  `src/learnloop/diagnosis/text_gaps/{contract,jobs,judges,pipeline,provenance,sources}.py`,
  `src/learnloop_sidecar/{context.py,handlers/hints.py,handlers/practice.py}`,
  `src/learnloop/ai/{routing,disclosures}.py`,
  `src/learnloop/config/{schema,template}.py`,
  `src/learnloop/params/parameter_registry.py`, `src/learnloop/cli/hints.py`.
- Schema: `migrations/212_hint_feedback_source_kind.sql`,
  `fixtures/migration_head_212/` (renamed from `_211`, rebuilt, README).
- Docs: this file; `docs/specs/spec_adaptive_hints_v1.md` §15 (the H2b note and
  the G-H17 deviation carried); `docs/decider-tier1-migration.md` (the head
  path); the regenerated references (head 212, 897 leaves).

## 6. Gate (this step; the full suite, the whole durability lane and vitest run once in the landing gate)

`TMPDIR` = the worktree's `fixtures-local/tmp`; the full-suite lock was free.
- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok
  (pypdfium2 5.14.0).
- `uv run lint-imports --no-cache`: **26 kept, 0 broken**.
- Targeted pytest, `uv run pytest -n auto` over 140 files (template `.pyc`
  cleared first): **2847 passed, 2 xfailed**. The files: every `tests/test_hint_*.py`
  (the new ones and H0-H2a's), `test_help_assists_schema`,
  `test_approach_maps*`, `test_approach_map_*`, the learner-text gap tests
  (`test_learner_text_gaps*`, `test_learner_text_source_widening`,
  `test_reader_formative_texts`, and every file naming `text_gaps`), every
  file driving `submit_attempt` / `submit_dont_know` or `config_dto`, every
  file naming the head fixture, the `test_mvp0*_upgrade` snapshot files, and
  the contract pins (`test_mobile_allowlist`, `test_desktop_rpc_contract`,
  `test_sidecar_serializer_snapshot`, `test_architecture`,
  `test_coordinated_migrations`, `test_tracked_fixture_databases`,
  `test_table_roles`, `test_registry_audit`, `test_grading_cli`,
  `test_p0_cutover_mvp08`, `test_vault_template`, `test_config_refactor`,
  `test_provider_resolution_parity`, `test_field_config`,
  `test_cli_help_snapshot`, `test_sqlite_file_copies`, `test_judge_routes`).
  The list is `fixtures-local/tmp/pyfiles.txt` in the worktree.
- Durability: `-m durability` on `test_hint_feedback_widening`,
  `test_learner_text_source_widening`, `test_help_assists_schema`,
  `test_approach_maps_schema`, `test_library_asks_migration`,
  `test_hint_telemetry`: **5 passed**; the new outcome, adapter, report,
  ruling and kill-switch tests under `--durable-sqlite` (WAL, the background
  threads' own connections): **41 passed**.
- References: `db_generate_reference.py` then `db_validate_reference.py`:
  **0 errors** (head 212, 330 table notes, 897 effective leaves).
- Frontend: `npm install`, `npm run typecheck` clean; `npx vitest run` over
  the 37 files that touch what changed (the panel's four, every
  PracticeScreen, SettingsScreen, KeyBar and algoConfig test, the copy
  deny-lists): **356 passed**; `npm run frontend:build`: built (the usual
  chunk-size warning).
- `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml`: ok.
- A no-model smoke on a backup-API copy of the worktree's tracked
  `fixtures/probability` under `fixtures-local/h2b-smoke/` (`env -i`, empty
  `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, no key variable,
  `LEARNLOOP_HINT_MODELS`, `LEARNLOOP_APPROACH_MAP_BUILDS` and
  `LEARNLOOP_ROUTER_MODELS` off, `outcome_placement_enabled`,
  `build_on_serve`, embeddings and query rewrites off in the copy's toml):
  165 → 212 migrated, `foreign_key_check` clean, both CHECKs admit
  `hint_feedback`; the snapshot's `hints` key present; `practice.set_help_style`
  wrote `guide_me`; `practice.request_hint` on Codex served the authored
  fallback (`codex_refused`, "from the item"), shown, **0 reveal rows**;
  `submit_attempt`: `hints_used` 1, `primed` 0; **0 receipts, 0 outcome
  verdicts, $0**; the report (`hints-report-v2`) shows the authored row and
  the writer's `codex_refused` fallback. No paid or live call was made in
  this stage.

## 7. Owner-run commands

```bash
# Adaptive hints on the practice screen are on by default (the kill switch):
#   [hints]
#   adaptive_enabled = false   # the practice screen is exactly as before H2b (byte for byte)
# Outcome placement (one background call per hinted answer not fully right, on a question with a map):
#   outcome_placement_enabled = false
# How long a hint is written before "use the item's hint instead" appears (seconds, a display cap):
#   authored_offer_after_seconds = 4
# The help style (also from the hint panel's "⋯" menu and Settings → Hints):
#   help_style = "balanced"    # or "let_me_struggle", "guide_me"

# The writer still needs a fast route (H2a): sign in to the ChatGPT plan once and route the writer to it.
uv run learnloop ai signin chatgpt
uv run learnloop ai status chatgpt --vault <path>
#   [ai.providers.chatgpt]
#   type = "chatgpt_plan"
#   model = "<a model `learnloop ai models chatgpt --vault <path> --profile chatgpt` lists>"
#   [ai.routing]
#   hint_writer = "chatgpt"
#   hint_outcome = "chatgpt"   # optional; unset it is the active provider (Codex, estimated_only)

# The report (read-only, no model call, no learner text):
uv run learnloop hints report --vault <path> --json
uv run learnloop hints report --vault <path> --since 14d --surface practice --json
# Learner-text gaps read "doesn't connect" text and discriminating answers with the rest:
uv run learnloop gaps run --vault <path> --dry-run
```

## 8. Open questions (with the default taken)

1. **Outcome placement defaults on** (D11). On the owner's vaults
   `ai.routing.hint_outcome` is unset, so it follows the active provider
   (Codex): one background Codex call (estimated_only) after each hinted
   answer graded not fully correct on an item with a map, like H1's
   `build_on_serve`. Default: on, as the spec says; `outcome_placement_enabled
   = false` stops it. A metered route needs `hints.price_per_million` and is
   held to the maps' $0.50 a day.
2. **"Doesn't connect" text and discriminating answers are read by
   learner-text gaps** with the pipeline's own switch and daily call cap: each
   reply with text is one gap-reader call in the background. Default: on with
   the pipeline (`learner_text_gaps.enabled`); empty replies queue nothing.
3. **The panel is not restored after a restart** (deviation 7). Default: not
   restored; a later phase could add a read of the submission's shown rows.
4. **Line selection for "not where I'm stuck"** (deviation 5). Default: lines.
5. **P(success) split at the median** (deviation 9). Default: median of the
   logged values; fixed bands would be a hand-set cut.
6. Carried from H2a §8 (defaults unchanged): uniform rival weights; hint
   reveals other than authored ones join auto-prime's 0.35 sum (the ruling
   took only authored ones out); `submit_dont_know`'s tutor-question
   asymmetry; `hint_fit` for replies only.
7. **New, from the tests**: H2a's keyless fence closes a hint's count when an
   attempt of its session and item has `created_at >= requested_at`; attempts
   are stamped to the second, so a hint requested in the same second as the
   item's previous attempt in the session answers `submission_complete`
   (seen only in tests that re-serve the same item at once). Default: left as
   H2a built it; a learner re-serving the same item within a second is
   unlikely, but the fence could compare at sub-second resolution.

## 9. Friction notes for H3 (RW2b), H4 and H5

**H3 (RW2b, the workbench).** `learnloop.hints.service.request_hint` still
validates `surface = 'practice'` (H2a); widen it and pass the step state. The
panel's pieces are reusable in the step editor: `HintPanel`'s card, feedback
box (swap the draft-line picker for the step picker and `about_step`),
discriminating box and picks, and `hintCopy.ts`'s strings (the Reader's
words); `useAdaptiveHints` assumes one answer draft and the practice submit's
key. The help-style menu writes the stored preference; the workbench header's
per-problem override (`workbench_sessions.help_style`, D31) is RW2b's. Outcome
placement places a practice attempt's final answer; in the workbench the
step verdicts already place work, so it should not run there (its due check
reads `practice_attempts.learner_answer_md` and every shown hint row of the
attempt: filter by surface when workbench rows exist). The report's
`--surface workbench` already filters every new section except the receipts
(not per surface). The workbench's learner text stays `workbench_text`
(RW2b's adapter); 212 did not touch it.

**H4 (guided redo and the tutor).** The same service with their surfaces; the
redo's attempt is primed, so the report's unaided progress will read
`primed` there unless H4 settles it by placements (the next-placement rule
needs no other assistance in the attempt). A reply during a redo is
`hint_feedback` with the redo's item; the adapter ignores the surface except
`workbench`.

**H5 (the off-policy report).** The rows carry what it needs: `chooser`,
`propensity`, `probabilities_json`, `drawn_option_json`, `seed`,
`policy_version` and, from H2b on, `contract_failures_json.state_at_request`
(placement intent, P(success)); outcomes are the report's per-row unaided
progress (with its `reached_by` basis) and later independent success (pending
counted, never imputed). Rows served under `argmax` log propensity 1 and give
no support; fallback and `learner_pick` rows are outside the sampling.
