# Reader RW5d P1: "show me" in the Reader (stage record)

- **Spec:** `docs/specs/spec_reader_show_me_figures_v1.md` rev 2 (owner-approved, Q1-Q27 decided), phase P1 only.
- **Branch:** `reader/rw5d-p1-show-me` in `learnanything-ad1`, base `eaf9859ad`.
- **Migration:** `224_figure_requests.sql` (223 is reserved for Reader CA2; the runner is set-based; renumber at landing if needed).
- **Successor:** none (spec §14: content and display only; nothing in scoring, scheduling, projection or serving reads anything P1 adds).
- **Live calls:** none. Every model call in the tests is a fake. No paid or CLI command was run against any vault; the
  only database work outside pytest was the head-fixture rebuild on a backup-API copy under `fixtures-local/rw5d-p1/`.

## What P1 ships

### The request (§7.1)
- `figure.request(FigureRequestV1)`, the one RPC for every host (`learnloop_sidecar/handlers/figures.py`). Its fields:
  - `goalText` (≤ 600 characters after normalizing);
  - `anchor` (today's request: `extractionId`, `spanIds`, `region`);
  - `origin`;
  - `hostRef`;
  - `readingAt` (the home when there is no anchor);
  - `offerRef`;
  - `coldActive`.
- `reader.figure_request` is now a thin wrapper over the same path, for anchor-only requests. RW5a/b's callers and
  tests are unchanged, apart from the contract's new `showMe` key.
- **Derived on the server, never sent:** `goal_author` (`extra="forbid"` refuses a client-sent one), the caller and its
  policy, the tiers (`["grammar"]`).
  - `learner` for the box and the rail.
  - `tutor` only when `offerRef` names a stored tutor answer whose `figure_goal.text` equals the goal (G-SM5).
- **Refused before any job or call:**
  - `ask`, `teacher` and `prefetch` origins (reserved by the migration);
  - P3/P4 host references (`itemId`, `submissionId`, `workbenchSessionId`, `attemptId`, `lessonId`, `nodeId`);
  - `coldActive`, and a derived `cold_attempt` or any policy other than `reading`: P1 builds nothing during attempts
    (SM4);
  - a goal while `figures.show_me_enabled` is off;
  - neither goal nor anchor, or `show_me` with no words;
  - a goal with no anchor and no reading position;
  - a home that is held out.
- **T1.** The build job captures `unit_origin()`/`unit_token()` in the request (LibraryJobs), so its origin is
  `figure.request`. Redesign D's offer and grant are keyed by it (a test asserts the job's origin). Pressed only:
  nothing builds in the background. `figure_author` was already in `METERED_PRICE_SETTINGS`.

### Grounding (§8.3)
- `figures.service.ground` handles three cases:
  - **With an anchor:** `anchor`.
  - **With fixed keys** (the tutor answer's displayed cited spans, or a revision's own kept passages): those still
    allowed now.
  - **Otherwise:** `find_sources_for_caller(query=goal, caller=<derived>, intent="explain", verify=True, limit=3)`,
    with the reading position's learning objects as context. Only the verification's picks count (status `ok`), at
    most `GROUNDING_PASSAGES` = 3 (`keep`: prompt size, in `figure_admission`). Each pick is rechecked with
    `spans_withheld` here.
- **Nothing found** (an empty result, unverified, or retrieval failing) gives `grounding = none`:
  - the figure is built anyway;
  - code forces `kind: illustrative`, empties `source_claims`, drops every assumption quote and any `equals_source`
    invariant (`_ungrounded`);
  - the server label is "AI-built illustration · not from your books";
  - the Reader's code-owned badge reads "not from your books — LearnLoop's model's illustration · not checked against
    the book".
- **Retrieved passages** go to the author keyed `extraction_id:span_id`, so a quote verifies against the right block
  of the right book. Each comes with its neighbours (neighbours never displace a kept passage). Every sent key is
  stored in `input_span_keys_json`.
- **Joint requests** use the anchor's context exactly as before and add the goal. No retrieval runs.

### The author (§8.2)
- A show-me request (a goal, or no anchor) carries `learner_request {text, written_by}` and `grounding`. It uses its own
  prompt version (`figure_author.v1+show-me-v1` / `figure_author.v2-panels+show-me-v1`) and `SHOW_ME_TEXT` in its
  instructions.
- An RW5a/b request is prompted and hashed byte for byte as before (G-SM4; a test recomputes the pre-224 key).
- **The reuse key** gains the goal (whitespace-normalized, case kept), its author, the grounding mode and the kept keys.
  Origin stays out of the key, so a box request with origin `selection` or `show_me` reuses the same figure.
- **Design choice: no cross-book reuse for goal-only figures.** A goal-only request's key names its home
  (`extraction_id`, where the learner was reading), so the figure lists and lands there. The same words asked while
  reading another book build again. The alternative was a cross-extraction listing join; the spec's columns do not
  carry a home span. Recorded for review.

### The ledger and the view
- **`figure_requests`.** Every request, built or reused, appends one row in the same transaction as the figure. The row
  holds what was asked, the reading position, the verified host refs, the policy, caller kind and `policy_derived_from`,
  the grounding, and its manifest (`find_sources`'s manifest, the kept keys, the passages' titles). `figure_id` is set
  once. Anchor-only RW5a/b requests get rows too (`grounding anchor`).
- **The figure view gains** `goalText`, `goalAuthor`, `grounding` and `passages`, only while show me is on (off: RW5a/b's
  view key for key). A goal-only figure's `anchorSpanId` is its reading position.
- **Show me switched off:**
  - figures built from a goal, or with no anchor, are not listed;
  - their predictions, explanations and revisions refuse (`show_me_disabled`);
  - their deliveries are withheld.
- **Held-out rechecks** (`row_withheld`): the home's spans plus every retrieved key, across sources, on listing,
  delivery, predictions, explanations and revisions. The learner-text gap path (`text_gaps/sources.py`,
  `provenance.py`) reads `input_span_keys_json` too: a missed prediction on a show-me figure rechecks the other books'
  passages, and its provenance names each source.
- **"Not right?"** (`revision_request`) keeps the goal, its author, the home and the grounding. Nothing is retrieved
  again, and `none` stays `none`.

### The tutor (§6.3)
- With `figures.show_me_enabled`, RW5b's tutor offers and RW1c's lookup on, the Reader tutor's answer may carry
  `figure_goal` (≤ 160 characters). Its prompt versions are the four Reader-tutor versions plus `-show-me`, and new
  context/answer classes keep the RW5b and RW1c ones intact.
- This is never asked for a question bound to an item or under a non-`reading` policy (cold, or a bound workbench).
- The stored view keeps `figure_goal {text, span_keys}`; the span keys are the displayed citations and excerpt (none on
  abstention). `offers()` adds a `show_me` button whose `label` is the goal.
- Off (or offers off), the tutor's prompt, output model and view are RW5b's (G-SM7, tested).

### The intent box (§6.1, Q15)
- One action, `make_explorable`. While show me is on, its palette label is "show me…", and its Decider option text
  gains the clause "The learner's words, if any, say what the figure should show or vary." under question-set
  `reader-intent-qs-v2-show-me` (routings hash as before while off).
- With words, the Reader sends a joint request (`origin show_me`). With an empty box it is RW5a's request.
- The routed line reads "Understand · show me · from your selection and your words" or "· from your selection".

### The Ask rail (§6.2)
- "show me ▸" (button, and `Alt+↵`) sends the box's words as a goal. The home is the inquiry's passage, else the
  selection's last block, else the reading position.
- The thread keeps one line per request:
  - pending, then "▸ interactive version · from your books: § … · open", or "not from your books — …";
  - "open" expands the figure under its passage and jumps there.
- "ⓘ where this goes" carries the spec's sentence. The button and the key are absent while show me is off.

### The figure line
- The collapsed line quotes the goal in its author's voice: the learner's words in learner quotes, or the tutor's as
  "◇ … (AI-written)". It is outside the code-owned badge slot.
- Retrieved passages are listed as `§ title section`.

### The report
- `learnloop reader report --json` gains `figures.show_me`, while show me is on. Counts only, never the words:
  - requests, by origin;
  - joint requests;
  - who wrote the goal;
  - the grounding mix, and abstentions;
  - figures built, by verification;
  - unsupported kinds;
  - "not right?" count and rate.

### Other changes
- **Events:** `show_me_requested` (salience only: origin, anchored, goal author; registered as
  `RW5D_SERVER_EVENTS`).
- **Disclosure:** the `figures` row names the goal text and the retrieved passages.
- **Switch:** `figures.show_me_enabled` (default on). It is classified in `params/parameter_registry.py` (structural,
  operational, a kill switch), and `show_me_enabled` lives in `figure_admission` (a leaf, so the tutor never imports the
  figure service: the import contracts hold).
- **AD guard:** the new `interactive_figures` columns are classified in `adaptive_difficulty/protected_tables.py` and
  `column_classes.py`. `goal_text` and `input_span_keys_json` are derived and unread.

## The migration (§13.1, G-SM8)

- **`figure_requests`** (RAW_LEDGER in `db/table_roles.py`):
  - the spec's columns, including `build_mode`, `tiers_allowed_json` and `prefetch_decision_id` (P2b/P5, reserved);
  - CHECKs on origin (seven values including `prefetch`), goal author and grounding;
  - goal text needs an author, and goal or anchor is required;
  - append-only triggers (`figure_id` set once).
- **`interactive_figures`** is rebuilt temp-then-rename under `PRAGMA foreign_keys = OFF`, every row copied unchanged:
  - the origin CHECK is widened;
  - `extraction_id` is nullable, with `CHECK (extraction_id IS NOT NULL OR request_id IS NOT NULL)`;
  - new columns `request_id`, `goal_text`, `grounding`, `input_span_keys_json` and `tier`
    (`grammar|sketch|js_animation|manim`);
  - columns reserved and unused: `program_version`, `engine_sha256`, `runtime_digest`, `instrumented_sha256`,
    `media_file_name`, `fuller_of_id` and `checks_json`;
  - the same four indexes, plus `(request_id)`.
- **Head fixture:** `fixtures/migration_head_224` is `migration_head_222` (sanitized, tracked) on a backup-API copy with
  only 224 applied (`UPGRADE_SCRATCH_COPY`):
  - checkpoint (0, 0, 0), `journal_mode=DELETE`, header bytes 1/1;
  - `integrity_check` ok, `foreign_key_check` empty, no companion files;
  - the schema diff is exactly 224's objects plus the rebuilt `interactive_figures`, and only `schema_migrations` moved
    (209 to 210 rows);
  - copied into place with the backup API, and the README records it.
  - The hard-coded paths moved to 224: 40 tests, the sanitizer, `db_generate_reference.py` and
    `db_validate_reference.py` (with `SCHEMA_HEAD = 224` in both).
  - The earlier migrations' "nothing else changed" diffs read the new `RW5D_ADDED_OBJECTS` and `RW5D_ALTERED_TABLES`
    (from `tests/test_figure_requests_migration.py`). Their applied lists end in 224.
- **Defaults snapshots:** all 24 were recomputed (the effective config gains `figures.show_me_enabled`). I checked that
  dropping that key from each version's effective config reproduces the previous hash at every version (24/24).
- **DB reference:** `db_generate_reference.py` was rerun. The prose counts are now 353 table notes and 1,055 config
  leaves. `db_validate_reference.py` reports 0 errors, and `validate_vault.py` passes (1,158 notes, 1,156/1,156
  reachable).

## Gate (this step; the full suite runs once at landing)

Every pytest, vitest, npm and cargo command ran in `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G`, pytest at `-n 6` at most, and vitest at `--maxWorkers=4`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| New: `tests/test_figures_show_me.py`, `tests/test_figure_requests_migration.py` | 23 + 6 passed (one of the 6 on the durability lane) |
| The 12 RW5a/b figure files (offers, region, revisions, verification, codex review, final round, fix round 2, migration, rpc, rw5b review, scope redesign, switch off) | 143 passed (after the `showMe` contract key and the show-me tutor model name were added to 4 pins) |
| Tutor and intent: rw5b fix round 2, judge routes, practice-proposal caller columns, find-sources callers, inquiry kill switch, reader intent, intentions, reconstruct, rw1b ×4, rw1c review, tutor offers, tutor retrieval, tutor switch off, rw4 kill switches, tutor practice request, tutor tool requests | 395 passed (fake updated for the show-me answer model; 1 model-name pin updated; show-me gated off for bound or cold questions) |
| Every test that names `migration_head_224` (40 files) + figures migration + figure requests migration + tracked fixture databases + coordinated migrations + migration coordinator | first run: 613 passed and 35 failed (the expected later-migration diffs). Fixed, then the 14 affected files: 105 passed |
| Contract set: architecture, CLI help snapshot, desktop RPC contract, mobile allowlist, registry audit, sidecar registry, serializer snapshot, table roles, tracked fixture databases, eval harness, config refactor, judge routes, plan-first transport (+ paid roles, offer grants, offer grants r5), AD protected tables and readings, AD guard, coordinated migrations, migrations, public tip guards | 776 passed and 1 failed. The failure was `test_plan_first_transport_offer_grants::test_p1_after_a_yes…` under `-n 6` load (a batch key missing after the drain); it passes alone and in a rerun of its two files (23 passed) |
| Modules changed (text gaps, provenance, reader report, reader modes, figure admission, column classes, disclosures, reading paths, salience firewall, learner-text gaps, tutor tests…: 53 files + `tests/test_tutor*` and `test_reader_tutor*`) | 7192 passed and 2 failed (`test_reading_paths` contract pins). After pinning `showMe`: show-me + reading paths + figures rpc + salience firewall gave 5628 passed |
| `-m durability` on the 16 migration-path files | 13 passed |
| `npm install`, `npm run typecheck` | ok, 0 errors |
| `npx vitest run --maxWorkers=4 src/screens/reader src/api` | 88 files, 802 passed (new: `figures/showMe.test.tsx`, 6 tests; `readerFigures.test.tsx` + 1 joint-request test; 2 files' palette label is now "show me…") |
| `npm run frontend:build` | built |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | ok |
| DB reference generate / validate | 0 errors |

## Open points for the landing and the owner

1. **Renumbering.** CA2 is expected to take 223. If the numbers change at landing, rename `224_figure_requests.sql`,
   `migration_head_224` and the paths together.
2. **Owner checkpoint.** The spec asks for one real "show me" on a `fixtures-local` copy with the plan route. It was not
   run here (the stage ran with no live calls).
3. **Every Reader tutor answer** uses the `-show-me` prompt versions while show me is on: one extra optional output
   field, with no new call. The receipts' prompt versions move with it.
4. **A re-asked goal** runs its grounding retrieval (`source_rerank`'s verification, cached by that service's own
   verdict cache) before the reuse key can be computed, because the key includes the kept passages. The author is not
   called again.
5. **Goal-only reuse is per home book** (see "Design choice" above). Within that book a reused figure lands where the
   current request was made, and is listed under every paragraph it was asked at (Codex review F3).
6. **The Ask rail's passage chips peek** as RW1c's citations do (this book: a peek with its crumb; another book: opened
   as a detour), and "open" goes to the figure through the return stack, with "back to where I was" (Codex review F8).
7. **The Ask rail sends a goal-only request even with a selection** (the spec's Ask-rail framing). Joint requests come
   from the intent box.

## Codex review

The findings, their fixes and the gate are in `docs/reviews/reader-rw5d-p1-show-me-codex-review.md`.

## Landing onto main (batch 3: Reader CA2 + Reader RW5d P1 + local retrieval P2, 2026-10-26)

The three stages land together (owner-approved batch landing) on `merge/batch3-onto-main` in `learnanything-merge2`,
cut from `main` at `1335df0c0` (latest `mvp-0.34`, migrations through 222, head fixture `migration_head_222`, Reader
CA1 just landed). Main was neither fast-forwarded nor pushed. The same section is appended to all three stages'
records; the stage-specific owner notes and open items are at the end.

### Commits and conflicts

| Commit | What |
|---|---|
| `043463103` | `--no-ff` merge of `reader/ca2-one-ask` (`ebfbfe7e5`, base `eae00d58a`). Conflicts composed keeping both sides: `algorithm_versions.py` (the chain gains `ONE_ASK_ALGORITHM_VERSION` after `REPLAY_LEDGER_ALGORITHM_VERSION`), `cli/app.py` (help text, `--to` dispatch, refusal text name 0.33, 0.34 and 0.35), `config/schema.py` (`ReplayConfig` and `AskConfig`), `template.py` (23 snapshot hunks: main's notes kept, CA2's note added, renumbered "inert below mvp-0.35"), `parameter_registry.py` (C0a's and CA2's rules), `sidecar/context.py`, `handlers/practice.py`, `handlers/sessions.py` (CA1's `pageSeen` and CA2's `earlierOpened` draft flags side by side: `_with_keyed_flag` and `_with_earlier_opened`, `draft_page_seen` and the earlier-marker helpers), `api/client.ts`, `PracticeScreen.tsx` (CA1's as-printed imports and `OpenInSource` modal beside CA2's `DockedAsk`; the book component stays `bookCarried \|\| pageSeen`, CA2's `earlierCounted` beside it; both draft flags in the checkpoint and its deps), 45 test files (main's absolute chain indices and head paths kept; the version pins moved below), the reference notes (main's side, then regenerated). CA2's `migrations/221_workbench_earlier_opened.sql` renamed **223**; its `fixtures/migration_head_221` dropped (main's 222 kept for the rebuild). CA2's `one_ask_upgrade.py` rewritten to the journalled activation (below). The stale practice-cap wording fixed (below). |
| `bdd511fa6` | `--no-ff` merge of `reader/rw5d-p1-show-me` (`33b9aa5d8`, base `eaf9859ad`). Conflicts: `template.py` (24 hunks, RW5d's `[figures] show_me_enabled` note on every tag), `AskRail.tsx` (CA2's Enter-sends branch and RW5d's `alt+Enter` *show me ▸* branch both kept, CA2's `enterSends` label kept on the ask button, RW5d's show-me row and thread lines after it), `tests/test_mobile_allowlist.py` (the desktop-only list names both `READER_CA1_RPCS` and `READER_RW5D_RPCS`; CA2 adds no RPC). Migration 224 keeps its number. |
| `54aef20c7` | `fixtures/migration_head_224` **rebuilt** from main's tracked, sanitized `migration_head_222/state.sqlite`: a backup-API copy, 223 then 224 applied under `UPGRADE_SCRATCH_COPY`, `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE` (header bytes 1/1), integrity ok, `foreign_key_check` empty, copied into place with the backup API, no companion files. Every table's rows equal main's 222 except `schema_migrations` (+223, +224); against RW5d's own head only `workbench_sessions` differs. Git records it as the rename `migration_head_222 -> migration_head_224`; README updated. |
| `de25dd4fa` | Earlier migrations' schema-diff tests through 223 + 224 (`[..., 222, 223, 224]`, `CA2_ALTERED_TABLES = {"workbench_sessions"}` beside RW5d's sets); CA2's migration test renumbered `test_223_adds_only_the_earlier_opening_column` (from 222, applies [223, 224], head 224); chain pins at mvp-0.35; all 26 defaults fingerprints recomputed (template `.pyc` cleared). |
| `88ac84275` | `--no-ff` merge of `retrieval/lr-p2-query-student` (`3d3755578`, base `eaf9859ad`). Conflicts: `parameter_registry.py` (RW5d's `figure_admission` and LR P2's four module owners), `template.py` (24 hunks, LR P2's `[embedding.local]` student keys and route note on every tag). Fingerprints recomputed again (26, from the composed defaults). |
| `930abc06e` | References and CLI help (below). |
| `867f7934a` | `tests/test_batch3_landing.py`: the chain and journal tests and interactions (i)-(iv); the activation journal's docstring names `one_ask_upgrade`. |
| `9a3dbdeba` | The last tests pinning mvp-0.34 as the latest (LP claim fixes' version set, rebuild equivalence's bare upgrade, mvp-0.18's default target); version comments. |

`main` and all three stage tips (`ebfbfe7e5`, `33b9aa5d8`, `3d3755578`) are ancestors of the tip. Against main the diff
adds **no tracked database or binary apart from the head fixture rename** (`git diff --numstat -M main` lists only
`fixtures/{migration_head_222 => migration_head_224}/state.sqlite` as binary); the root `.gitignore` is unchanged.

### Renumbering and the chain

- `ONE_ASK_ALGORITHM_VERSION = "mvp-0.35"`, after `REPLAY_LEDGER_ALGORITHM_VERSION` (`mvp-0.34`, rebuild equivalence;
  `mvp-0.33` is the LP claim fixes). `LATEST_ALGORITHM_VERSION` is `mvp-0.35`; `ONE_ASK_VERSIONS == {"mvp-0.35"}`; the
  snapshot `mvp-0.35` is recorded; the earlier `*_VERSIONS` sets each gain `mvp-0.35`.
- `one_ask_upgrade.py` now follows `replay_ledger_upgrade.py`: `PREDECESSOR = mvp-0.34`, the chained predecessors
  `mvp-0.9 .. mvp-0.33` go through `upgrade_to_replay_ledger` first; the activation is ONE `BEGIN IMMEDIATE`
  transaction under the vault mutation lock (the predecessor's manifest, `activate_p0_projection`, the registry
  refresh, the journal (`predecessor`, `target`) at the shared `<db>.claim-fixes-activation` path, the durable
  publication last); the completion marker is the `p0_projection_activation` receipt under the tag. Its
  `complete_interrupted_activation` completes a journal naming mvp-0.35 and hands any other to rebuild equivalence's
  (which hands an mvp-0.33 journal on). The CLI (`cli/runtime.py`) and the desktop sidecar (`sidecar/context.py`) now
  install `one_ask_upgrade.complete_interrupted_activation`, the chain's latest.
- `learnloop upgrade --to mvp-0.35` works from mvp-0.9, 0.27, 0.29, 0.30, 0.31, 0.32, 0.33 and 0.34
  (`test_upgrade_to_mvp035_works_from_every_supported_version`, 8 cases); the bare `upgrade` targets mvp-0.35. The
  upgrade's help and refusal text name every tag; `tests/cli_help_snapshot.json` changed only for `upgrade`.
- New keys move no unrelated version hash: `test_eval_harness.py`, `test_success_head*.py` and the field arm tests pass
  as merged (the arm hashes read `[mastery]` only).

### The practice Ask cap (fixed at landing; owner decisions 2026-10-26)

`config/template.py`'s `[tutor_qa]` comment and `TutorQAConfig`'s description said practice was "per item+session".
They now say: **per attempt; enforced on metered routes; unlimited on the subscription (ChatGPT plan) route while
`[ask] panel_enabled`** (off, the cap applies on every route). The cap stays `max_questions_practice = 3` in
`<vault>/learnloop.toml` `[tutor_qa]`, beside `max_questions_feedback` (per attempt), `max_questions_library` (per note
per UTC day) and `max_questions_reader` (per span per UTC day). The code (`tutor_qa.question_usage(metered=...)`) was
already CA2's final rule; no behaviour changed.

### Interactions (`tests/test_batch3_landing.py`; no break found, so no fix)

- **(i) CA2's cap vs RW5d's *show me*.** RW5d's spec §6.2 sends the Ask rail's text "as a figure goal instead of a
  question"; CA2's K5 cap counts question events. A tutor `figure_goal` press and an Ask-rail *show me* each build a
  figure, write no `question_events` row and leave the practice and library budgets as they were, at mvp-0.35 with the
  panel on (`test_i_...`). P3's Ask-panel *show me* (a figure as a hint-equivalent) is not built yet.
- **(ii) CA2's `earlier_opened_at` vs CA1 and rebuild equivalence.** The column is LIFECYCLE state on a WORKFLOW table;
  replay never reads it. A workbench submit with an earlier opening carried into steps rebuilds exactly as the same
  submit without it: mastery 0, facets 0 (`test_ii_...`). **Finding (pre-existing on main, not the batch):** on that
  real-clock sidecar path the shadow rebuild moves the submitted item's `due_at` by 1 s (live 1 s later): reproduced
  3/3 on `git archive main` at mvp-0.34 with a plain workbench submit. The owner parity below (frozen clocks) is 0/0/0.
  CA1's as-printed page reads and writes no learner state (its parity stands).
- **(iii) T1's offer keying vs CA2's routes.** A grant given on `figure.request` (even naming `tutor_qa`) never routes
  CA2's Ask (`ask_tutor_question`) to OpenRouter; a grant given on the Ask itself routes it to OpenRouter, which is
  metered (`is_subscription_transport` false), so the per-attempt cap applies there; the plan route stays unlimited
  with the panel on (`test_iii_...`; fake OpenAI client, nothing sent).
- **(iv) LR P2's resolver vs RW5d's grounding.** RW5d grounds a goal through `find_sources_for_caller`. With an adopted
  (fake) student behind `spaces.LOCAL_QUERY_ENCODER` and `default = "local:grouped"`, the hook is live (it tries to start
  the query process); with `embedding.local.student = false` it starts nothing and the grounding retrieval's status and
  hits equal P1's empty hook exactly (`test_iv_...`).

### Regeneration

- `db_generate_reference.py` then `db_validate_reference.py`: **errors []** after the prose counts were updated by hand
  (Configuration.md and Database.md: **1,064 leaves in 74 sections, 353 table notes**). No new `CONFIG_SECTION_FUNCTIONS`
  entry was needed (CA2 brought `ask`; `figures` and `embedding.local` existed). ~425 other note changes are
  `source_commit` stamps.
- `validate_vault.py`: passed (1,161 notes).
- `tests/cli_help_snapshot.json`: `upgrade` only. RPC contract, serializer snapshot and mobile allowlist pass as merged.

### Gate (at `9a3dbdeba`; `env -i`, empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`; logs in `fixtures-local/landing-batch3/logs/`)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` (+ `uv pip install pypdfium2`), 5G scopes; `lint-imports --no-cache` | **36 kept**, 0 broken |
| targeted run (104 files: every stage's tests, the chain/migration/pin files, contracts), `-n 6`, 5G | 2,188 passed, 3 failed (stale latest-version pins, fixed in `9a3dbdeba`, 42 passed on rerun), 25 skipped, 3 xfailed, 26 min |
| `tests/test_batch3_landing.py` | 24 passed |
| full suite (`flock`, 10G/2G scope, `pytest -n 8 --dist worksteal --durations=50`) | **NOT COMPLETED.** Started 20:18:49 after waiting for the thread-leak stage's lock; reached 99% by 21:06:40, then no line was written. One worker held ~737 threads at ~1,100% CPU (the known leaked-thread class); it was SIGKILLed at 21:36 as a worker of this run, but xdist never replaced it and the other 7 workers sat idle in `futex_wait` (load ~0.6): a hang, not slow tests. The progress lines show 16 `F` marks before the hang; with `-q` the names print only at the end, so they are unknown. Killing the rest of the run's process tree was **refused by the permission layer**, so per the brief the gate stopped there: the lock is still held by that hung run, and the requested rerun (`-o faulthandler_timeout=600 --junitxml=full.xml`) and the durability lane were not run. Wall time and the 50 slowest tests are therefore not available. |
| Codex lockdown on main's tree (`git archive main`, alone) | the same 10 fail on codex-cli 0.164.0: `test_codex_isolation_mcp_check` ×3, `test_codex_lockdown_round2` ×3, `test_codex_lockdown_round3` ×3, `test_diagnosis_isolation::test_configured_mcp_servers_are_listed_and_disabled` |
| torch lane (`uv sync ... --extra pdf`; `tests/test_query_student.py` + `_gpu.py`; then the standard extras re-synced, torch gone) | 50 passed, 1 skipped (the GPU smoke) |
| owner lane (`-m owner_vaults`, backup-API copies of the three mvp030 backups in `fixtures-local/owner-lane-batch3/`) | 83 passed, **6 failed: exactly the 6 known** (`test_doctor` pre-044, `test_migrate_fresh` 153, `test_goal_decay_projection`, `test_sidecar_contract` recent ingests, `test_activity_backfill`, `test_placement_fixture_copies[arxiv_v2]`); 0 `model_call_receipts` |
| `npm install` (esbuild's postinstall blocked as before), `npm run typecheck` | clean |
| `npm test -- --maxWorkers=4` (whole vitest) | **221 files, 1,917 tests passed** (61 s) |
| `npm run frontend:build`; `cargo check` | built (the usual chunk-size warning); finished |
| empty dirs | `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` stayed empty; `HOME` gained `.nv/ComputeCache` and `.local/share` (the torch lane's CUDA cache and a tool cache) |

### Parity (backup-API copies of the mvp030 backups; `fixtures-local/landing-batch3/`, scripts in `scripts/`)

Setup: `orig/` = backup-API copies of `learnanything/fixtures-local/vault-backups-20261025-mvp030/{linear_algebra,probability}`;
`u34/` = `orig` brought to **mvp-0.34 with main's code** (routes to the `127.0.0.1:9` blackhole, 64 tasks on main and 65
on the merge (LR P2's `retrieval_query_generator`), none outside it; `upgrade --to mvp-0.34`, `rebuild-derived-state` ×2).
`code_main` = `git archive 1335df0c0`, `code_merge` = `git archive 867f7934a` (src and migrations unchanged since). Every
run through `env -i` with empty dirs; `run.py`'s audit hook refuses Codex process starts and non-loopback sockets.

- **(a) main vs merge at mvp-0.34** (after the primary sidecar load; a second main copy as the noise control): every
  row of all 357 common tables identical (18,806 rows LA, 8,195 probability); the merge adds only 224's objects
  (`figure_requests` empty, its indexes and triggers) and the new columns (`interactive_figures` ×12,
  `workbench_sessions.earlier_opened_at`), all NULL; `schema_migrations` +223, +224, common rows identical; integrity
  ok, foreign keys 0, `model_call_receipts` 0. Certification, Today and the plan **byte-identical** main vs merge (and
  main vs main). `rebuild --shadow` **0/0/0** both sides; `doctor` identical (57/1 LA, 101/48 probability, pre-existing).
- **(b) `upgrade --to mvp-0.35`** (the merge's code, on copies of u34): "mvp-0.34 -> mvp-0.35", no journal left. **Rows:
  every row kept; mastery and every schedule unchanged (0 LOs, 0 items moved).** What changes, exactly: the
  `algorithm_version` stamp (0.34 -> 0.35) and `updated_at`/`created_at` of `facet_recall_state` (76 / 2 rows) and
  `facet_capability_evidence` (36 / 1) (DERIVED, the projection activation), `parameter_registry.updated_at` (352, the
  refresh), plus one `derived_state_rebuilds` (`p0_projection_activation`), one `parameter_registry_manifests` row.
  Shadow right after the upgrade: facet 0, **mastery 21 / 18 = the `mastery_state` version stamp only** (no value moves),
  schedule 0, as at RW7b's projection-only activation; after `rebuild-derived-state` ×2: **0/0/0**; doctor unchanged.
  After a primary load + 12 live attempts (frozen clock): **0/0/0**. Bare `upgrade` -> mvp-0.35. From the mvp-0.30
  backup straight `--to mvp-0.35` (chains through 0.31-0.34) and the owner's two steps (`--to mvp-0.34`, then
  `--to mvp-0.35`), rebuilt: **0/0/0**, doctor unchanged. **Nothing changes until CA2 is used.**
- **(c) the kill switches** (`[ask] panel_enabled`, `cold_help_converts`, `[figures] show_me_enabled`,
  `[embedding.local] student` all false): set before the upgrade (k35), or after an on upgrade then rebuilt (kr35),
  versus the merge's mvp-0.34 copy: certification, Today, mastery and every schedule identical after the version
  stamp; the plan identical except 7 hashes over the versioned card (`card_hash`, `snapshot_hash`), exactly as the
  rbeq landing recorded for its tag; the switches-on copy (on35) the same. (a) shows the merge at mvp-0.34 equals main.
- **(d) an interrupted mvp-0.35 activation** (the upgrade dies with `os._exit(17)` after the config publication):
  label mvp-0.35, journal present, the predecessor's mastery untouched. `upgrade --to mvp-0.35` completes it ("completed
  the interrupted activation of mvp-0.35"; again: "vault is already mvp-0.35"); the desktop start completes it; both
  equal the clean upgrade (0 LOs moved). Every attach that may not complete it refuses with "The upgrade to mvp-0.35
  did not finish ... run `learnloop upgrade --to mvp-0.35`" (`Repository`, `open_vault_repository` without a
  completer, the secondary attach, and the remote schema check as `SchemaMismatch`), leaving the vault as it was. Plain
  `doctor --json` is a read-only attach and refuses too (the journal stays), as recorded at the LP and rbeq landings.
- **Receipts and calls.** The 42 parity databases with a receipts table and the 3 owner-lane copies hold **0
  `model_call_receipts`** (the other 21 files are the probability backup's empty `.learnloop/state.sqlite` stubs); no
  audit-log line (no process start, no socket). **Spend: $0.** Nothing under `~/learnloop-vaults`, `~/learnloop-retired`
  or `~/learnloop-books` was opened or listed.

### Owner notes

- **Before upgrading:** back up the vaults; close the desktop app, the MCP server and the phone page. Then
  `learnloop upgrade --to mvp-0.35 --vault <vault>` (or the bare `learnloop upgrade`); from mvp-0.30 it chains through
  0.31-0.34 (mvp-0.34's step is the whole-vault rebuild). Migrations 223 and 224 apply on the first open.
- **Kill switches (`<vault>/learnloop.toml`):** `[ask] panel_enabled = false` (the overlay and per-source answer mode
  as before), `[ask] cold_help_converts = false` (the predecessor's cold rules, no downgrade), `[figures]
  show_me_enabled = false` (RW5b's figures exactly), `[embedding.local] student = false` (the query student never
  serves; P1's retrieval).
- **The practice Ask cap:** `[tutor_qa] max_questions_practice` (default 3) per attempt on metered routes; unlimited on
  the ChatGPT plan route while the panel is on.
- **Local retrieval P2 stays off until you run its setup** (`docs/reviews/retrieval-local-p2-query-student.md`,
  "Commands for the owner"): `embeddings local setup` (adopting the cached 9B), `embeddings local index`,
  `embeddings local student setup` (adopting the two 0.6B bases), then `student plan`, `generate`, `targets`, `train`,
  `evaluate`, `adopt` / `reject`, `status`, each with `--dry-run` first.

### Open items

- **The full suite and the durability lane are not done.** The run hung at 99% (leaked-thread workers deadlocked); the
  kill of its process tree was refused by the permission layer, so the lock is still held by it. Owner/coordinator:
  end that run (`fixtures-local/landing-batch3/scripts/fullsuite.sh`'s tree), then rerun once with
  `-o faulthandler_timeout=600 --junitxml=fixtures-local/landing-batch3/logs/full.xml`, then `-m durability`, and
  record the hung tests' stacks, wall time and the 50 slowest here. Do not land before that.
- **Low (pre-existing, main):** a real-clock workbench submit leaves `practice_item_state.due_at` 1 s later than a
  rebuild computes (interaction (ii)); frozen-clock parity is 0/0/0.
- **Low (recorded since LP):** `doctor --json` refuses an interrupted activation rather than completing it.

### Open items for RW5d P1

- The numbers held: migration **224**, with CA2's 223 before it; the head fixture is `migration_head_224` rebuilt from
  main's 222 with 223 and 224 (the branch's own 224-on-222 database was dropped).
- Interaction (i): *show me* is not a question and spends no Ask budget; P3's Ask-panel *show me* (one hint-equivalent
  on an open attempt) waits for P3.
- Still open from the stage: the owner checkpoint (one real *show me* on a `fixtures-local` copy with the plan route)
  was not run (no live calls here); every Reader tutor answer uses the `-show-me` prompt versions while the switch is on.
