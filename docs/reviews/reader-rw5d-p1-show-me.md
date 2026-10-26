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
5. **Goal-only reuse is per home book** (see "Design choice" above).
6. **The Ask rail's passage chips are text,** not RW1c's peeking chips. "open" jumps with the Reader's `jumpToSpan`
   (no "back to where I was" crumb). Both are small follow-ups if the owner wants them.
7. **The Ask rail sends a goal-only request even with a selection** (the spec's Ask-rail framing). Joint requests come
   from the intent box.
