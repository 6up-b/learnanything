# Reader workbench RW4a: library questions and source comparison (stage `reader-rw4a`)

Branch `reader/rw4a` (worktree `learnanything-merge4`), base `main` at
`8eb1ba5d2` (RW1b landed; migration head 208). Spec:
`docs/specs/spec_reader_workbench_v1.md` §13 row RW4a and what it cites (§7.2
the caller-side concept-graph expansion, §7.3 ask your library in full and the
compare paragraphs, §7.5 `library_asks`, §7.6, §7.7; §11 config, routes and
ledger tasks; §12's RW4a row; §3.4 items 11 and 17; §14 G17, G18, G19, G20,
G53; §20.9). Consumed, never rebuilt: `spec_source_practice_and_probes_v1.md`
§9.1 `find_sources` (`source_retrieval/find_sources.py`) and §9.4
`compare_sources` (`source_retrieval/compare.py`, migration 189), the sources
service's `propose_sources` / `propose_comparison` (server-derived caller,
shared daily cap), `PinnedSpanProvider` (`source_retrieval/tutor.py`) and the
`find_practice` RPC with a `reader` caller. Presentation:
`docs/specs/ux_reader_workbench_v1.md` §1 (Transfer: "where else is this
explained?", "where is this used?"; Orient: "what do I need first?"), §3.1
comparing posture, §3.5 keys, §4.0 seven states, §4.5, W9, W10, §10.
RW1b's friction note 1 (the palette rows RW4a adds).

## 0. Plan (written before the code)

**Scope.** RW4a only: "Ask" (Shift+Enter) in the library search box and
`Ctrl+Shift+F` / the palette in the Reader, answered sources first in the
comparing posture beside the open source; the organizer's one-line
contributions (one `judge_listwise` call); the personalized chip; the
caller-side concept-graph expansion; pin, peek, open; compare pinned passages
through `compare_sources` (display only); "ask the tutor about these" over the
pinned passages; "practice this question" through `find_practice`; RW1b's
palette rows for Orient and Transfer; migration 209. Not here: RW4b's
exercise view and fallback search, RW4d's keep / my take / perspectives,
RW4e's role proposals in `source_objects`, RW1c's tutor modes, RW5 figures;
no grading, regrade, replay, eligibility or scheduling change; RW1b's
reader_requests / reader_capture revert paths and RW6a's recap reads untouched.

**Migration 209** (`209_library_asks.sql`): `library_asks` (WORKFLOW: paid
outputs, never re-run on rebuild): `id`, `caller` (`learner` | `tutor`),
`query_md`, `query_hash`, `personalized`, `requested_perspectives_json`,
`manifest_json` (every `find_sources` manifest, the expansion calls
included, with the policy and how it was derived), `organizer_json` (lines
with their hit keys and ledger ids), `comparison_id` (a `source_comparisons`
id), RW4d's `kept_json` and `kept_at` (created now so RW4d adds no
migration), `question_event_id`, `model`, `prompt_version`, `created_at`,
plus the Reader context it was asked from (`extraction_id`, `anchor_json`,
`entry`). Classified WORKFLOW in `db/table_roles.py` (no DERIVED table, so no
replayer). `fixtures/migration_head_208` → `migration_head_209` (backup-API
copy of the base's 208 database, only 209 applied, rollback journal) and every
hard-coded path; the reference scripts' `SCHEMA_HEAD`.

**Backend** (`src/learnloop/reader/library_ask.py`, pure composition over
injected sources-service callables: `learnloop.reader` may not import
`learnloop.instructional`, so the sidecar injects `propose_sources`,
`propose_comparison` and the caller; *moved during the build to
`src/learnloop/source_retrieval/library_ask.py`, see §3*):
- `ask_library`: the main `find_sources(intent="explain", scope="library",
  personalized=…, limit=8)` under the server-derived Reader caller (policy
  `reading`; a workbench session's item gives `assisted_practice`; an open
  cold administration `cold_attempt` and nothing), "where else is this
  explained?" excluding the selected spans; then, with
  `library_ask.expand_graph`, one more `find_sources(intent="explain",
  learning_object_ids=<expanded LOs>, verify=False)` per requested expansion
  (prerequisites; applications = LOs listing an anchor LO as a prerequisite;
  confusables on request), keeping only hits linked to the expanded LOs by
  provenance (similarity never creates an edge), each labelled. The anchor's
  LOs are the selection's (or the reading passage's) provenance-linked LOs.
  The graph read is the sources spec's (`expansion_lists`' read factored out
  as `expanded_learning_objects`, behaviour unchanged), not a second copy.
  Hits grouped by source and then role (Foundation, Worked example,
  Exercise, Explanation; Prerequisites and Applications under their own
  subheads); a `library_asks` row; one exposure row per shown span
  (`record_shown_spans`, context `library`); the salience-only reader event
  `library_ask`.
- `organize`: one `judge_listwise` call over the union (route
  `library_organizer`, ledger task `library_contribution`): a verdict per hit
  (`contributes` | `related` | `unrelated`), the picks in order, a one-line
  contribution that must cite exactly its own hit (validated in code; a line
  citing anything else is dropped, never repaired), proposed roles kept on
  the row for RW4e (no `source_objects` write), and, personalized only, at
  most one "speaks to your open question about …" naming one of the open
  gaps or active misconceptions it was shown (validated). Personalized off:
  no learner state in the prompt, retrieval order kept. Capped by
  `library_ask.max_daily_cost_usd` ($1.00 metered, today's
  `library_organizer` receipts; Codex `estimated_only`).
- `compare`: `compare_sources` with the Reader caller over the pinned keys
  (gated by `reader_compare.enabled` and the sources spec's
  `source_service.compare`); the row's `comparison_id`; a table built for
  display only (one row per source, the open source's first; *contributes* from
  the contributions, *assumes* from `different_assumptions` relations,
  *differs from the others* from the other relations, each cell with its own
  source's verified quote; no consensus row); the event `compare_opened`.
- `ask_tutor`: `tutor_qa.ask_question` in the `reader` context (§3.4 item 11)
  anchored on the first pinned passage, a new root thread, with
  `source_span_provider = PinnedSpanProvider(pinned)`: `tutor_qa` gains the
  smallest change — in the reader context an injected provider's spans
  replace the selection delivery (None keeps today's bytes) — so the
  citation allowlist is the pinned passages; the row's `question_event_id`.
- RPCs (desktop-only, pinned in `test_mobile_allowlist.py`, Tauri
  passthroughs): `reader.library_ask`, `reader.library_ask_notes`,
  `reader.library_compare`, `reader.library_ask_tutor`; "practice this
  question" is the existing `find_practice` RPC with a `reader` caller (one
  RPC, DL3's and RW1c's too). `reader.prompt_contract` carries `libraryAsk`
  only while its switches are on.
- Palette (`reader_intent.ACTIONS`): Orient *what do I need first?*
  (prerequisites), Transfer *where else is this explained?* and *where is this
  used?* (applications), effect `library_ask`, `needs=("library",)`; the
  Decider's options follow; `readerIntentContract.ts` regenerated.

**Config** (modelled defaults, out of the decision-only template;
every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry recomputed with a "no scoring,
scheduling, projection or serving change" note): `[library_ask]` `enabled =
true`, `expand_graph = true`, `personalized_default = true`,
`max_daily_cost_usd = 1.00`; `[reader_compare]` `enabled = true`
(`keep_enabled` is RW4d's and is not added here). Route
`ai.routing.library_organizer` (a listwise chat task; unset = the active
provider; low reasoning effort, the fast route) with its disclosure.

**Successor.** None: retrieval is context (T6's ruling) and the organizer's
lines and the comparison are display. If anything changes what is served or
graded, stop and record it. Kill switches: `library_ask.enabled`,
`library_ask.expand_graph`, `reader_compare.enabled`; off, the RPCs refuse,
the contract has no `libraryAsk` key, and the Reader and the library search
are the base's byte for byte.

**Frontend** (`apps/learnloop-tauri`, new files under `screens/reader/`):
`useLibraryAsk.ts` (the ask, notes, pins, compare, tutor and practice states
with the seven-state contract), `LibraryAnswer.tsx` (W9: the header with how
the passages were found, the personalized chip, groups by source and role,
each `§` excerpt with its `◇` line arriving later, peek / pin / open),
`CompareTable.tsx` (W10, display only: "differences kept · each line quotes
its own source"). The comparing posture replaces the rail at half the window,
resizable; Esc leaves it; "open" goes through the existing source detour
(a crumb); peek opens the passage's neighbours in the pane. The library page's
Shift+Enter asks in place. Nothing steals focus, animates or opens a modal.

**Tests** (fakes only; fail-first for G17-G20 and G53):
`test_reader_find_sources_callers.py` (G19: Reader caller contexts and their
policies, sources spec faked and present; the scope equals
`TutorSpanProvider`'s for the same item; no Reader surface gets `authoring`;
manifests record policy and expansions; G53 absent/faked and no second
definition), `test_library_ask.py` (G17, personalization chip, practice this
question, pinned-span tutor, the expansion calls), `test_library_ask_expand.py`
(the caller-side expansion, labels, one organizer verification),
`test_reader_compare_table.py` (G18 over a faked `compare_sources`, no
`source_objects` or relation writes), `test_rw4_kill_switches.py` (G20: off,
RPCs refuse and the contract, palette and library search are the base's),
`test_library_asks_migration.py` (the table, its role, a durability-lane
case); vitest `libraryAsk.test.tsx` and `libraryAskSwitchOff.test.tsx`
(snapshots written on the base frontend before any RW4a frontend code).

## 1. What was built

### 1.1 Migration 209 (`migrations/209_library_asks.sql`)

- `library_asks` (WORKFLOW): every §7.5 column (`id`, `caller` `learner` | `tutor`, `query_md`, `query_hash`, `personalized`, `requested_perspectives_json`, `manifest_json`, `organizer_json`, `comparison_id` → `source_comparisons(id)`, RW4d's `kept_json` and `kept_at`, `question_event_id`, `model`, `prompt_version`, `created_at`) plus where it was asked from (`entry`, CHECK'd with all five entries; `extraction_id`; `anchor_json`). Two indexes. No other table changes (the upgrade test diffs every other table's SQL).
- `db/table_roles.py`: WORKFLOW. No DERIVED table, so no replayer. Replay and rebuild never read it.
- SQL lives in a registered store, `src/learnloop/db/stores/library_asks.py` (added to `test_architecture.py`'s `REGISTERED_SQL_OWNERS`).
- Head fixture `fixtures/migration_head_208` → `fixtures/migration_head_209`: a backup-API copy of the base's 208 database with only 209 applied under `upgrade_allowance(UPGRADE_TEST_HELPER)`, `wal_checkpoint(TRUNCATE)` → `(0, 0, 0)`, `journal_mode=DELETE` (header bytes 18-19 are 1/1), `integrity_check` ok, `foreign_key_check` empty, copied in with the backup API, no companion files; README gains the 209 paragraph. Every file that named the old path now names `migration_head_209` (the tests, both reference scripts with `SCHEMA_HEAD = 209`, `docs/decider-tier1-migration.md`, the Database Catalog); `test_route_rules_in_grader.py`'s head assertion is 209; RW1b's widening test now asserts 208 is applied *first* (209 follows on the way to head).

### 1.2 Config (modelled defaults; out of the decision-only template)

`[library_ask]` `enabled = true`, `expand_graph = true`, `personalized_default = true`, `max_daily_cost_usd = 1.00` (classified in the parameter registry as a money bound); `[reader_compare]` `enabled = true`. Route `ai.routing.library_organizer` (`AITask`, `ROUTE_FOR_OPERATION`, `AIRoutingConfig`; low reasoning effort by default, the fast route; unset = the active provider; a metered route needs `source_retrieval.llm_price_per_million` or the notes are skipped and labelled). All 19 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries recomputed (`defaults_fingerprint_for_version`) with a "no scoring, scheduling, projection or serving change" note. The judge-route disclosure gains `library_organizer` (the question, the passages, and with the personalized chip on the open questions named on those passages' topics).

### 1.3 The library answer (`src/learnloop/source_retrieval/library_ask.py`)

- **Where it lives.** Beside T6's library search (`source_retrieval/library.py`), which it extends. It could not live in `learnloop.reader`: `source_retrieval` already imports the Reader's span helpers, so a Reader module importing `find_sources` or `judge_listwise` closes a package cycle (`Existing deferred cross-package cycles are frozen` broke). It reaches the sources service (`learnloop.instructional`) only by injection: the sidecar binds `propose_sources` / `propose_comparison` to the server-derived caller.
- **`ask_library`**: the main `find_sources(intent="explain", scope="library", learning_object_ids=<anchor LOs>, personalized=…, verify=False, limit=8)` (the anchor LOs are the selection's or the reading passage's provenance-linked LOs, or given ones); *where else is this explained?* excludes the anchor spans. With `expand_graph`, one more `find_sources(intent="explain", learning_object_ids=<expanded LOs>, verify=False, limit=8)` per expansion the entry asks for (Ctrl+Shift+F, the library search and *where else*: prerequisites + applications; *what do I need first?*: prerequisites; *where is this used?*: applications), keeping at most 3 passages that are **linked to those LOs by provenance** (`build_cross_source_spans`) and carry a `provenance` rank, each labelled Prerequisite / Application; a similar passage is never labelled. Hits grouped by source (first appearance) and then role (Foundation = definition/theorem/proof, Explanation, Worked example, Exercise), expansions under their own subheads. *What do I need first?* also lists the prerequisite LOs with whether each is shown on the learner's own (`lo_certification(...).demonstrated`, a pure read) and their passages. One `library_asks` row (manifests: the caller, the derived policy and how, the main call's manifest, each expansion call's LOs, manifest and kept keys, or why expansion was skipped); one `source_exposure_events` row per passage shown (`record_shown_spans`, context `library`, entity `library_ask`), as "each span shown is recorded as exposure" says; the salience-only event `library_ask`.
- **The graph read** (`find_sources.expanded_learning_objects`, the sources spec's `expansion_lists` read factored out so it is one function): `LearningObject.prerequisites` / `.confusables` name **concepts** in real vaults (placement and the tutor's prerequisite questions read them so), plus `prerequisite` and `confusable_with` edges; the LOs reached are those concepts' LOs (an entry naming an LO id is read as that LO). See §3 item 3.
- **`organize`**: one `judge_listwise` call over the union (route `library_organizer`, ledger task `library_contribution`, left = the ask id, right = the span key, prompt `library_organizer.v1`). Per passage a verdict (`contributes` | `related` | `unrelated`), a one-line contribution (the ledger rationale), `cites` (must be exactly its own ref, checked in code: otherwise the line is dropped, never repaired, and counted in `dropped_lines`), proposed roles from RW4e's vocabulary (others dropped; kept on the row only), and, personalized only, `speaks_to` naming one of the open questions it was shown (active misconceptions' statements and named, not-undone learner-text gaps on the passages' LOs; validated against that list; at most one passage). Personalized: the organizer's pick order; off: no learner state in the prompt and retrieval order. A request the ledger answers (same prompt, same passages) reuses the notes validated the first time (`notes_for_ledger_ids`) and shows no unchecked line. Capped by `library_ask.max_daily_cost_usd` (today's `library_organizer` receipts at the price; subscription calls count nothing), the remainder passed as the call's `max_estimated_usd`; capped → status `capped`, no call.
- **`compare`**: the service's `compare_sources` (bound to the caller) over ≥ 2 pinned keys; the row's `comparison_id`; `compare_table` builds the display: one row per source, the open source's first, *contributes* from its contributions, *assumes* from `different_assumptions` relations it is in, *differs from the others* from its other relations, each cell carrying its own source's quote (the relation's left or right quote); `also discussed in`, unverified sources and dropped pins listed; no consensus row. Nothing written to `source_objects` or their relations.
- **`ask_tutor`**: `tutor_qa.ask_question(context="reader")` anchored on the first pinned passage, a new root (`reader_thread=[]`), with `source_span_provider = OnlyPinned(PinnedSpanProvider(pins))` (the numbered blocks a pinned passage cites are left out, so the allowlist is exactly the pins); the row's `question_event_id`. `tutor_qa`'s reader branch gains the smallest change: an injected provider's spans replace the selection delivery and the provider's manifest is stored as `source_retrieval`; with no provider (every other reader ask) its bytes are unchanged (tested).

### 1.4 The sidecar (`src/learnloop_sidecar/handlers/library_ask.py`)

Four desktop-only RPCs (pinned off the phone; Tauri passthroughs): `reader.library_ask`, `reader.library_ask_notes`, `reader.library_compare`, `reader.library_ask_tutor`. `reader_caller` builds the caller on the server: `caller_for(repository, "reader", extraction_id)` → `reading`; with `workbench_session_id` naming a session bound to an item → that item's `practice` context → `assisted_practice`; a cold administration of that item → `cold_attempt`. No RPC input has a `policy` field. "Practice this question" is the existing `find_practice` RPC with a `reader` caller (one RPC: DL3's and RW1c's too). `reader.prompt_contract` carries `libraryAsk` (`expandGraph`, `personalizedDefault`, `compare`) only while `library_ask.enabled`, `source_service.enabled`, `reader_inquiry.enabled` and the reader are on. Events, salience-only and server-owned (`reader_inquiry.RW4A_SERVER_EVENTS`): `library_ask`, `library_notes`, `compare_opened`, `library_tutor_asked`.

### 1.5 The palette (`src/learnloop/reader/reader_intent.py`)

Orient *what do I need first?* and Transfer *where else is this explained?* / *where is this used?*, effect `{"kind": "library_ask", "entry": …}`, `needs=("library",)` with `Availability.library` from the three switches; the Decider's options follow; never on the learner's own notes (not anchor-free). `fixtures/readerIntentContract.ts` regenerated (the fixture test pins it).

### 1.6 The report (`reader_report.py`)

`library`: asks, by entry, personalized share, notes by status, lines dropped for citing another passage, compared and tutor-asked shares. Counts only (tested: no question text).

### 1.7 The Reader (frontend)

- `screens/reader/useLibraryAsk.ts`: the comparing posture's state (ask → notes fetched at once → pins → compare / tutor / practice / peek), each part on the seven-state contract at its own landing place (`notesPhase`, `comparePhase`); a late result never reopens a closed answer.
- `screens/reader/LibraryAnswer.tsx` (W9 + the display-only W10 `CompareTable`): `ASK YOUR LIBRARY`, the question, `N sources · M passages · found by keyword [+ meaning] · notes by LearnLoop's model`, the `personalized ●/○` chip (re-asks), groups by source and role, Prerequisites / Applications *· from your concept map*, each `§` excerpt with its locator, then its `◇` line (`◐ noting what each contributes…` until then; `(model's label)` for a proposed finer role; `◌ speaks to your open question about … (model's reading)`), peek · pin · open; *compare pinned (n)* (or "pin passages from two places to compare them"), *practice this question ▸*, the tutor box ("answers only from these N passages · ↵ ask"); the comparing keys inside the answer (↑↓ move, space peek, p pin, o open, c compare, ctrl+↵ the tutor).
- `screens/reader/LibraryPane.tsx`: the posture at half the window, resizable (arrows on the separator), remembered (`ll.library.splitWidth`, try/catch), never under 480 px; Ctrl+Shift+F's ask box (the learner's key, so it takes the cursor); Esc peels the peek, then the posture.
- `ReaderScreen.tsx` (+~115 lines): the hook, Ctrl+Shift+F, the palette's `library_ask` effect (and *change* closes it), the rail stepped aside while comparing, "open" as a detour (this book: a peek crumb; another book: `rememberLeftSource` + `openSource(…, via "search")`, so Alt+← comes back), "practice this ▸" through the shell's `onCheckMe` (a learner pick, book out of view), and on the library page Shift+Enter asks (the answer in place, with a `↵ search by meaning · ⇧↵ ask your library` hint). Off, none of it renders.

## 2. Gates and where they are tested

| Gate | Backend | Frontend |
|---|---|---|
| **G17** sources first; each line cites exactly its own hit; the tutor's citations stay inside the pins | `test_library_ask.py` (passages, no essay, no model call, no question or learning-state row until asked; a line citing another passage dropped; one organizer call, ledger rows; cached requests keep only validated lines; the tutor's context holds exactly the pins and its citation outside them is dropped; a `question_events` row in the reader context) | `libraryAsk.test.tsx` (passages before notes, notes in model voice, no tutor call until asked; "answers only from…") |
| **G18** compare through `compare_sources`; only verified lines; no consensus; no proposal writes | `test_reader_compare_table.py` (faked and present service; open source first; own-source quotes per cell; dropped lines never reach the table; `source_objects*` counts and vault YAML unchanged; `comparison_id` only; both switches) | `libraryAsk.test.tsx` (one row per source, "your passage", no consensus/summary) |
| **G19** policy from the caller, never an argument; `assisted_practice` = `TutorSpanProvider`'s scope; no `authoring`; manifests record policy and expansions | `test_reader_find_sources_callers.py` (reading; a workbench session → assisted_practice, no exercise/solution, scope equal to `tutor_scope`; cold → nothing; no `policy` input; every manifest policy in the three learner-facing ones) | — |
| **G20** switches restore T6's search, tutor spans, the base contract | `test_rw4_kill_switches.py` (contract = RW1b's minus `libraryAsk` and the library rows; every RPC refuses and writes nothing under each of three switches; `reader.search_sources` identical on/off; `reader.ask`'s tutor prompt identical on/off; `expand_graph` off; `reader_compare` off) | `libraryAskSwitchOff.test.tsx` (6 snapshots written on the base, unchanged: palette, Ctrl+Shift+F, Shift+Enter, with intent on and with inquiry off; no library call) |
| **G53** absent / faked; no second definition | `test_reader_find_sources_callers.py` (the service faked: the documented calls; absent: the ask is absent and refuses; an AST scan of `learnloop/reader/**`, the Reader handlers and `source_retrieval/library*.py`: no `find_sources`, `compare_sources`, `find_practice`, `value_candidates`, `propose_*`) | — |
| the expansion (§7.2) | `test_library_ask_expand.py` (the graph read with concept ids, edges and LO ids; one extra call per expansion with the expanded LOs, `verify=False`; only provenance-linked passages labelled; manifests; the organizer judges the union once; entries; `expand_graph` off; no anchor) | the Prerequisites subhead |
| W1 / firewall | `test_library_ask.py::test_every_rw4a_event_is_salience_only…` | — |
| G54 / G56 (attention, states) | — | `libraryAsk.test.tsx` (no focus move when results land; capped names the $; failed keeps the question; Esc layers); `attentionBudget.test.tsx`, `voices.test.tsx` lints pass over the new components |

**Fail-first evidence.** Backend: run against the base's source (`git archive 8eb1ba5d2 src migrations`, `PYTHONPATH` to it, `-o pythonpath=.`): the five RW4a test files fail at collection (no `learnloop.source_retrieval.library_ask`) and the migration test fails 4 of 4. Frontend: `libraryAsk.test.tsx` against the base frontend (`git archive 8eb1ba5d2 apps/learnloop-tauri`, this repo's `node_modules`): 9 of 9 fail (the keys test was added after). The switched-off snapshots were written on the base (`3e27ab1f3`) and pass unchanged.

## 3. Decisions and deviations

1. **The module lives in `source_retrieval/`, not `learnloop/reader/`** (§1.3): the frozen-cycle contract forbids `reader → source_retrieval` / `reader → practice_index`. It sits beside T6's library search, which already houses the Reader's library search; the Reader package defines no retrieval (G53's scan covers both).
2. **The main call is unverified too.** §7.6's caps line reads as if the main retrieval verifies and only expansions skip it; §7.2 says the organizer "judges the union, so the expansions are verified once, together". The organizer *is* the judgment of every passage, so the main call runs at retrieval rank: one paid judgment per ask (not two), and the excerpts land before any model call (UX §4.5 "excerpts first, notes when ready").
3. **The graph is read as vaults store it.** On a backup-API copy of a real vault, every LO's `prerequisites` named concept ids, so the first reading (the sources spec's, taking them as LO ids) expanded to nothing — the sources spec's `expand` lists were empty on real data for the same reason. `expanded_learning_objects` now resolves concepts to their LOs and reads `prerequisite` / `confusable_with` edges (the rule placement and the tutor already use); an LO id still reads as that LO. This changes the sources spec's `expansion_lists` (retrieval context only; no caller in the code passes `expand` today) — recorded for that spec.
4. **The sources spec's `expand` argument exists** (the §18 request landed), but RW4a keeps the caller-side calls the task and §7.2 describe: `expand` fuses the expansion as one more RRF list into the main question's ranking, where a prerequisite passage competes on similarity to the question and is usually cut from the page; one call per expansion gives each its own page. Both read the same graph function.
5. **"Assumes" is derived.** `compare_sources`' output has contributions and pairwise relations, no per-source assumptions: *assumes* shows the `different_assumptions` relations a source is in (with its own quote), *differs from the others* its other relations. A per-source `assumes` field would be the sources spec's to add.
6. **Requested perspectives are not offered** in RW4a's table (UX §4.5 puts the field with RW4d); `requested_perspectives_json` stays `[]`.
7. **The tutor's pinned answer drops cited numbered blocks** (`OnlyPinned`) so "answers only from these N passages" is literally the allowlist; the passages themselves are complete blocks.
8. **Peek is a layer in the pane** (Esc closes it), not a return-stack crumb: the stack's entries restore source positions and rail tabs, not postures. *Open* is a crumb (this book: a peek detour; another book: a source detour).
9. **Personalized off re-asks** (a new row, `personalized = false` through to `find_sources`), so each row's prompt is what was sent.
10. **The library page's answer** shows in place (no open source to sit beside); "practice this ▸" is offered only in the Reader (where the shell's learner-pick path exists).
11. **Exposures**: one `source_exposure_events` row per passage shown, at the ask (the passages render at once). That is the sources spec's rule ("each span shown is recorded as exposure"); its consequence (the exposure rule keeps an exercise whose span was shown out of independent checks) is that spec's, unchanged.
12. **Requires RW1a's inquiry** (`reader_inquiry.enabled`), like RW1b and RW6a: its states, voices and return stack.
13. **`[reader_compare] keep_enabled`** is RW4d's and was not added (a switch with nothing to switch).
14. **Ask/compare/tutor run synchronously** on the serial sidecar, like `reader.ask` and the `find_sources` RPC; the organizer is a second RPC so the passages land first.

## 4. Successor

**None.** Retrieval is context (T6's ruling); the organizer's lines, the roles and the compare table are display; the tutor question is an ordinary reader-context `question_events` row (salience and learner-text gaps as any reader question); "practice this question" proposes and the plan's learner pick serves. Nothing here writes an attempt, evidence, mastery, certification, FSRS or a plan; replay never reads `library_asks`. The exposure rows are the sources spec's existing record (§3 item 11). Off, every RPC refuses and the Reader is byte-identical to the base (G20 tests).

## 5. Friction audit (G52) for the workflows RW4a touched

| Workflow | Before | After |
|---|---|---|
| "Where else is this explained?" | Library page → type → Enter → a flat hit list → open each | select → Tab → *where else is this explained?* → passages by book and role beside the source, each with a one-line note; the source keeps its place |
| "What do I need first?" | Guide / map, by hand | select → Tab → *what do I need first?* → the prerequisite topics with ● or "not yet shown on your own" and a passage each |
| Compare two books | Two windows, by hand | pin (p) two passages → c → one row per book, each line quoting its book |
| Ask the tutor across books | Not possible (library questions needed a note) | pin → type → ↵ ("answers only from these N passages") |
| Practise the question | Practice screen, search by hand | *practice this question ▸* → proposals → *practice this ▸* (a learner pick) |

Keyboard: every action is reachable (Ctrl+Shift+F; Tab + arrows + ↵ from a selection; inside the answer ↑↓ / space / p / o / c / ctrl+↵; Esc peels). Waits on a model: the notes (`◐ noting…`, the passages already shown), compare, the tutor. Focus moves only on the learner's key (the Ctrl+Shift+F box).

## 6. Tests and counts

New backend files (all pass): `test_library_ask.py` 10, `test_library_ask_expand.py` 13, `test_reader_find_sources_callers.py` 7, `test_reader_compare_table.py` 4, `test_rw4_kill_switches.py` 8, `test_library_asks_migration.py` 4 (one on the durability lane); `tests/library_ask_fixtures.py` (builder, `OrganizerFake`, a citing tutor fake). Changed: `test_mobile_allowlist.py` (+6 pins, a registry check), `test_reader_intentions.py` (+1; NOT_LANDED, kinds), `test_reader_intent.py` (the off contract also switches `library_ask` off; Orient), `test_judge_routes.py`, `test_architecture.py` (the store), `test_learner_text_source_widening.py` (208 first), 25 files' head-fixture paths. New vitest: `libraryAsk.test.tsx` 10, `libraryAskSwitchOff.test.tsx` 4 (6 snapshots); changed `IntentBox.test.tsx` (Orient).

## 7. Files

- Migration and fixture: `migrations/209_library_asks.sql`; `fixtures/migration_head_209/` (renamed from `_208`, rebuilt, README).
- Backend: `src/learnloop/source_retrieval/library_ask.py` (new), `src/learnloop/db/stores/library_asks.py` (new), `src/learnloop/source_retrieval/find_sources.py` (`expanded_learning_objects`), `src/learnloop/tutor/tutor_qa.py` (reader context with an injected provider), `src/learnloop/reader/reader_intent.py`, `src/learnloop/reader/reader_inquiry.py`, `src/learnloop/reader/reader_report.py`, `src/learnloop/db/table_roles.py`, `src/learnloop/ai/routing.py`, `src/learnloop/ai/disclosures.py`, `src/learnloop/config/schema.py`, `src/learnloop/config/template.py`, `src/learnloop/params/parameter_registry.py`; sidecar `src/learnloop_sidecar/handlers/library_ask.py` (new), `handlers/reader.py` (contract), `handlers/__init__.py`.
- Frontend: `screens/reader/{useLibraryAsk.ts, LibraryAnswer.tsx, LibraryPane.tsx}` (new), `screens/ReaderScreen.tsx`, `api/{client.ts, dto.ts}`, `fixtures/readerIntentContract.ts`, `src-tauri/src/{commands.rs, main.rs}` (four passthroughs).
- References: Configuration and Database references regenerated (head 209, 328 table notes, 880 leaves in 60 sections), `_scripts/db_generate_reference.py` (two section descriptions, `SCHEMA_HEAD`), `_scripts/db_validate_reference.py` (`SCHEMA_HEAD`), `Configuration.md` / `Database.md` counts, `Maps/LearnLoop Pipeline Map.md` (the RW4a bullet).

## 8. Open questions (with the default taken)

1. Should the comparing posture push a return-stack entry of its own (a "comparing" crumb restoring the answer)? **Default: no** — the source never moves, Esc leaves, *open* pushes a crumb; a posture crumb needs RW1a's stack to restore postures.
2. Should a library ask from inside a workbench session be offered in the UI (the RPC supports it, `assisted_practice`)? **Default: no UI** in RW4a (the working posture replaces the right side); RW2b's bridging is the in-session path.
3. The organizer's verdict `unrelated` dims a passage rather than hiding it. **Default: dim** (nothing disappears after it was shown).
4. Should exposures wait until a passage is scrolled into view? **Default: at the ask** (the pane shows them at once; the sources spec counts "shown").
5. Should `compare_sources` return a per-source `assumes`? **Default: derived from relations** here; a request for the sources spec (§9 below).
6. `lo_certification` per prerequisite LO costs ~0.5 s on a 21-LO vault copy for *what do I need first?*. **Default: keep** (only that entry reads it); cache if it grows.

## 9. Friction notes for RW1c, RW4b, RW4d and RW4e

1. **RW1c**: the tutor-over-pins path is `library_ask.ask_tutor` (reader context + `OnlyPinned(PinnedSpanProvider)`), and `tutor_qa`'s reader branch now takes an injected `source_span_provider`: RW1c's Reader-context span provider with its own query can be passed the same way (it replaces the selection delivery; None keeps today's). "Another way to see this" could hand off to the comparing posture (`useLibraryAsk.ask` with entry `where_else_explained`) instead of its card; RW1b's card is unchanged here.
2. **RW4b**: "Nothing in practice fits yet" is where RW4b's *find an exercise in my sources ▸* goes (`LibraryAnswer`'s practice block); the textbook-exercise candidates come back from the same `find_practice` call (`sourceExercises`), not yet rendered.
3. **RW4d**: `library_asks.kept_json` / `kept_at` exist; `comparison_id` is set on compare; `compare_table` rows carry each source's key, so *Keep this comparison* reads the stored `source_comparisons` row by `comparison_id`. Add `[reader_compare] keep_enabled` and the perspectives field above the table (`requested_perspectives_json`); `CompareTable` is display-only now.
4. **RW4e**: the organizer already proposes roles per passage (`organizer_json.notes[].roles`, RW4e's vocabulary, validated) without writing `source_objects`; RW4e persists them as proposals (`authorial_role`) and shows them as "model's label" (the note's label already does for a finer role).
5. **All**: the sources spec's `expand` (and `expansion_lists`) now read concepts (§3 item 3); its tests use LO ids and still pass. `ReaderScreen.tsx` is ~3,150 lines; RW4a's behaviour lives in `screens/reader/`.

## 10. Owner-run commands

No paid run is needed. To look at it on a copy: `uv run python -c "from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases as c; c(Path('fixtures/linear_algebra'), Path('fixtures-local/rw4a-la'))"`, then `uv run learnloop doctor --fix-state --vault fixtures-local/rw4a-la` (applies 209), then `LEARNLOOP_VAULT=$PWD/fixtures-local/rw4a-la npm run dev` from `apps/learnloop-tauri`. In the Reader: select a line → Tab → *where else is this explained?* / *what do I need first?*; or Ctrl+Shift+F; on the library page Shift+Enter. The notes need the `library_organizer` route (unset: the active provider; on Codex `estimated_only`); a deep question may also use T6's `source_query_rewrite` route. Switches in the copy's `learnloop.toml`: `[library_ask] enabled = false` (today's Reader and library search), `expand_graph = false`, `personalized_default = false`, `max_daily_cost_usd`; `[reader_compare] enabled = false`. `uv run learnloop reader report --json --vault <copy>` shows the `library` row.

**Model calls made in this stage.** Tests: fakes only. One manual smoke on a backup-API copy (`fixtures-local/rw4a-la`, embeddings switched off in the copy): its first run made **2 unintended live calls** — T6's `source_query_rewrite` on Codex (`gpt-5.6-sol`, ChatGPT subscription, ~17.8k input and ~100 output tokens each, `estimated_only`, $0 metered) for the conceptual questions the smoke asked; no dry run preceded them. The copy's `[source_retrieval] query_rewrite` was then switched off and every later smoke run made **0** model calls (receipts unchanged). The smoke (no organizer call): the library search ask 8 passages / 2 sources in 0.6 s; *where else* on an LO-linked passage 14 passages with 2 prerequisite LOs (3 passages) and 3 applications (4 passages) in 2.3 s; *what do I need first?* 11 passages in 1.3 s; 9 `library_asks` rows and 81 exposure rows, in the copy only.

## 11. Gate

Run in the worktree with `TMPDIR` set to `fixtures-local/tmp`, `uv run --no-sync` after the install. Owner rule 2026-10-17: targeted tests only (the full suite, the whole durability lane and the whole vitest run are the landing gate's). `/tmp/learnloop-fullsuite.lock` was free each time.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **24 kept**, 0 broken |
| targeted `pytest -n auto -q -p no:cacheprovider` over 213 files (listed below), on the stage tip | **3,835 passed, 2 xfailed**, 0 failed (9 min 34 s). The first run (before the graph fix) had 1 failure: `test_rw4_kill_switches.py::test_t6s_library_search_is_unchanged` compared wall times (`timingsMs`); it now ignores them (3 of 3 alone after the fix) |
| `pytest -m durability` on the migration and fixture files (`test_library_asks_migration`, `test_learner_text_source_widening`, `test_migrations`, `test_coordinated_migrations`, `test_tracked_fixture_databases`) | **4 passed** (71 deselected) |
| `pytest --durable-sqlite` on the five RW4a behaviour files | **42 passed** |
| `npm install`, `npm run typecheck` | ok, clean |
| vitest `src/screens/reader`, `src/screens/ReaderScreen.*.test.tsx`, `attentionBudget.test.tsx`, `LibraryPlace.reread.test.tsx` | **48 files, 368 tests passed** (incl. `libraryAsk.test.tsx` 10, `libraryAskSwitchOff.test.tsx` 4 with its 6 base snapshots unchanged, `IntentBox.test.tsx`, `voices.test.tsx`, `attentionBudget.test.tsx`) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | finished, exit 0 (four passthroughs) |
| `db_generate_reference.py`, `db_validate_reference.py`, `validate_vault.py` | regenerated (schema head 209, 328 table notes, 880 configuration leaves in 60 sections); errors []; passed (1,122 notes, all reachable) |
| `module_validate.py` / `desktop_validate.py` | pre-existing failures, not RW4a's: 799 missing module notes (none for an RW4a module) / the unclassified `pdfSelection/testing/syntheticBook.ts` RW6a and RW1b recorded |
| contract tests in the targeted run: `test_config_refactor.py` (19 snapshots recomputed, the template `.pyc` cleared), `test_cli_help_snapshot.py` (unchanged), `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`, `test_architecture.py`, `test_table_roles.py`, `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`, `test_instructional_layering.py`, `test_sqlite_file_copies.py`, `test_judge_routes.py` | pass |

**Not done:** no adversarial (Codex) review in this step; no real-UI look (exercised through the real `ReaderScreen` in jsdom); the organizer has run only against fakes.

**The 213 pytest files run** (the changed and new test files; every test file naming `tutor_qa`, `ask_question`, `find_sources`, `expansion_lists`/`expanded_learning_objects`, `reader_intent`, `reader_inquiry`, `reader_report`, `prompt_contract`, `disclosures`, `parameter_registry`, `table_roles`, `ROUTE_FOR_OPERATION`, `DEFAULTS_SNAPSHOT`, `source_service`, `instructional.sources`, `search_library`, `reader.search_sources`, `judge_listwise`, `effective_defaults` or `library_ask`; every `test_reader_*`; the contract tests above):

```text
test_ai_config test_architecture test_attach_to_family test_auto_build_spend_report 
test_build_study_map_routing test_canonical_exercise_serialization test_capture_desktop 
test_capture_route_recovery test_chatgpt_plan_provider test_chatgpt_plan_workspace test_cli_help_snapshot 
test_codex_output_schema test_compare_sources test_config_refactor test_constraint_engine 
test_coordinated_migrations test_daily_loop_reader_authored_practice test_daily_loop_reader_retire 
test_daily_loop_reference_adoption test_daily_plan_replay test_decider_landing test_desktop_rpc_contract 
test_diagnosis_context test_diagnosis_history_modes test_diagnosis_input_provenance_landing 
test_diagnosis_input_provenance test_diagnosis_replay test_dialogue_causal_join test_discriminating_search 
test_embedding_route_isolation test_exam_protection_identity test_exam_protection test_exam_protection_review 
test_exercise_arm test_facet_identity_actions test_facet_locks_landing test_field_config 
test_field_signal_production_paths test_find_sources_intents test_forecast_receipts_landing 
test_forecast_receipts test_grading_cli test_hypothesis_reference_contract test_import_split_parity 
test_instructional_layering test_integration_daily_loop_field test_intervention_outcomes_replayer 
test_judge_routes test_key_ladder_labels test_kinship_feature test_learner_pick_proposal 
test_learner_text_gaps_composition test_learner_text_gaps_flow test_learner_text_gaps 
test_learner_text_gaps_review test_learner_text_source_widening test_library_ask_expand test_library_ask 
test_library_asks_migration test_mcp_c1a_narrow test_mcp_c1a_review test_mcp_cli test_mcp_tools 
test_method_explicit_landing test_method_explicit_upgrade test_migrations test_misconception_routing 
test_mobile_allowlist test_model_usage_report test_mvp010_upgrade test_mvp011_upgrade test_mvp013_upgrade 
test_mvp014_upgrade test_mvp015_upgrade test_mvp016_upgrade test_mvp017_route_check_replay 
test_mvp017_upgrade test_mvp018_upgrade test_mvp020_upgrade test_mvp021_upgrade test_mvp022_upgrade 
test_mvp023_upgrade test_mvp024_upgrade test_open_world_gate test_output_budget test_p0_cutover_mvp08 
test_pfc_unverified_unassessed test_pf_generation test_pinned_span_bridge test_placement_opening_probes 
test_placement_signals test_plan_determinism test_practice_availability test_practice_proposal_caller_columns 
test_prescription_passages test_probability_cli test_project_cli test_proposal_impressions 
test_provider_resolution_parity test_question_context test_question_promotions test_question_signal 
test_quick_check test_reader_active_reading test_reader_activity test_reader_adoption_ownership 
test_reader_authoring test_reader_branches test_reader_capture test_reader_compare_table test_reader_cues 
test_reader_dialogue test_reader_find_sources_callers test_reader_formative_texts test_reader_guidance 
test_reader_inquiry_kill_switch test_reader_inquiry_status test_reader_intentions test_reader_intent 
test_reader_observation_records test_reader_passage_check test_reader_pdf_selection test_reader_progression 
test_reader_quick_check test_reader_recap test_reader_recap_review test_reader_recap_review_r2 
test_reader_recap_review_r3 test_reader_reconnect test_reader_reconstruct test_reader_render_views 
test_reader_report test_reader_requests test_reader_restoration test_reader_rw1b_final_verify 
test_reader_rw1b_fix_round4 test_reader_rw1b_rereview test_reader_rw1b_review test_reader_rw3a_landing 
test_reader_workbench_rw2a test_reader_wrap_up test_reading_hardening_landing test_reading_step_switch 
test_rebuild_orchestrator test_recurrence_commands test_recurrence_live test_reference_check_binding 
test_reference_gate_imports test_registry_audit test_regrade_contract_successor test_regrade_contract_upgrade 
test_required_method_authority test_required_method_reopened test_required_method_rereview 
test_required_method_round3_final_verify test_required_method_round3 test_required_method_round3_rereview 
test_required_method_round3_review test_reread_safety_landing test_reread_safety 
test_retrieval_interventions_write_points test_reveal_ledger test_router_r2a_landing test_router_r2a_serving 
test_router_r2bc_landing test_route_rules_in_grader test_rw4_kill_switches test_sensitivity_certificates 
test_serve_eligibility_review test_shadow_rebuild test_sidecar_queue_serialization test_sidecar_reader_p3 
test_sidecar_reader test_sidecar_serializer_snapshot test_sidecar_source_retrieval test_sidecar_teach_back 
test_source_block_fts test_source_exercise_import test_source_exercise_rpcs test_source_first_needs 
test_source_retrieval_codex_unavailable test_source_retrieval_followup test_source_retrieval_guards 
test_source_retrieval_rereview_cost test_source_retrieval_rereview test_source_retrieval_search 
test_source_retrieval_tutor test_source_service_spend_accounting test_source_service_spend_envelopes 
test_sources_merge_composition test_sources_outcomes_report test_sqlite_file_copies 
test_structured_transport_parity test_stuck_prompt test_stuck_prompt_replay test_table_roles 
test_tier1_decider test_tool_dispatch_policy test_tool_registry test_tool_results_withhold_answers 
test_tools_cli test_tracked_fixture_databases test_tutor_citations test_tutor_delivery_fixes 
test_tutor_practice_request test_tutor_promotion_w2 test_tutor_qa test_tutor_tool_requests 
test_ux_phase1_connect_ai test_ux_phase1_landing test_ux_phase1_usability_round1 test_ux_phase4_feedback 
test_valuation_calibration_fields 
```

## Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/rw4a-onto-main`. Main's tip was `8eb1ba5d2` (the RW1b landing), which is the stage's base. The stage tip is `07f77d497`, unchanged. Codex's final verify (job `20261017-215940-M3pFfC`) is clean. Main was neither fast-forwarded nor pushed here.

**Commits:**
- `15789eb84`: a real `--no-ff` merge of `reader/rw4a` onto `8eb1ba5d2`. Main had not moved, so the merged tree is exactly the stage tip (`git diff 07f77d497 15789eb84` is empty).
- `27bad0c2f`: the references regenerated on the merged tree.
- This record.

### Merge

- **No conflicts.** Migration 209 was still free (main's head was 208). `fixtures/migration_head_209` is in rollback mode: header bytes 18-19 are 1/1, `journal_mode` is `delete`, its last `schema_migrations` row is 209 and there is no `-wal` or `-shm`. `fixtures/migration_head_208` is gone. No tracked code or test names the old path; only earlier review records and the 209 fixture's README mention it, as history.
- **No algorithm successor.** The vaults' labels and the Pipeline Map's `implementation_version` are unchanged.

### Regenerated

- **References.** Ran `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, `schema_head` 209, 328 table notes. 390 notes changed, all of them `source_commit` / `source_commit_timestamp` labels, with no content changes. Committed as `27bad0c2f`.
- **Defaults snapshots.** Deleted the template `.pyc` and touched `template.py`. All 19 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries equal `defaults_fingerprint_for_version`: **0 mismatches**.
- **CLI help snapshot.** Rewritten with `python tests/test_cli_help_snapshot.py --write`: no change.
- **Pipeline Map.** The stage's RW4a bullet (the library ask, the organizer route, `library_asks`, the kill switches) is already there, so nothing was added. `validate_vault.py` passes (1,122 notes, 1,120/1,120 reachable).

### Gate

Run on `27bad0c2f`, the final code tree; the only later commit adds this section. Python 3.12.14, `TMPDIR` set to merge2's `fixtures-local/tmp`, `uv run --no-sync` after the install. Both suite lanes ran under `flock /tmp/learnloop-fullsuite.lock`. No paid call was made: every test uses fakes. **This is the first full run over the stage's code**; every stage step had run targeted tests only (owner rule 2026-10-17).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `lint-imports --no-cache` | **24 kept**, 0 broken |
| `pytest -n auto -q -p no:cacheprovider` (full suite) | **13,135 passed, 2 xfailed**, 0 failed (18 min 7 s; `fixtures-local/rw4a-landing-fullsuite.log`). RW1b's landing ran 13,063; the +72 are RW4a's new tests |
| `pytest -m durability` | **108 passed**, 13,029 deselected (2 min 58 s); RW1b's was 107, plus the `library_asks` migration's durability case |
| `npm install`, `npm run typecheck` | ok, clean |
| `npm test` (vitest) | **123 files, 994 tests passed** (RW1b's: 120 files, 971) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished, exit 0 (`src-tauri` gains the six passthroughs) |
| tracked fixtures | `git status` clean after both lanes and the frontend run |

Nothing failed, so nothing was rerun or fixed. None of the known flakes fired (`"8841"` in `test_mcp_c1a_review.py`, the vitest load-timing cases). The vitest run went after both pytest lanes, with nothing else running.

### Parity (backup-API copies; no model call)

**Setup:**
- **Copies.** The owner's `fixtures/linear_algebra` and `fixtures/probability` (with probability's `.learnloop/state.sqlite`) were copied with `copy_tree_with_databases` from the main checkout into `fixtures-local/landing-rw4a/orig/`. Each original was read once. Every other copy came from `orig/` or from another copy through the same helper. `arxiv_v2` was not opened.
- **Code.** Main's code is `git archive 8eb1ba5d2` and the merge's is `git archive 27bad0c2f`, each containing only `src`, `migrations` and `pyproject.toml`. Each was put first on `sys.path`, and every run printed the `learnloop` package it imported.
- **Environment.** `LEARNLOOP_CONFIG_DIR` was an empty directory and `LEARNLOOP_AI_PROVIDER` was unset. Every process started in a directory holding no `.env`. For the upgrade runs and the sidecar runs, `HOME` and `CODEX_HOME` were also empty directories, so no Codex login, ChatGPT-plan token or OpenRouter key was reachable. The sidecar ran with a minimal environment (`PATH`, `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR`, `LANG`).
- **Model routes, before any retrieval.** Every switch copy's `learnloop.toml` was rewritten first:
  - `ai.active_provider` and every chat route the vault sets, plus `library_organizer`, `source_query_rewrite`, `source_rerank`, `source_compare`, `source_relevance_judge`, `source_query_writer` and the learner-gap routes, went to an `openai_chat` profile at `http://127.0.0.1:9/v1` with an unset key variable;
  - `[source_retrieval]` `query_rewrite`, `tutor_query_rewrite`, `tutor_rerank` and `dense` were all false;
  - `[embedding]` `enabled`, `backfill_enabled` and `backfill_sources_on_extract` were all false.

  `config effective` confirmed the result. No call was attempted: no organizer, compare or tutor request was sent.
- **Starting state.** Both vaults were at schema 165, label `mvp-0.8`, with **0** `model_call_receipts`.
- **Cleanup.** Once these copies existed, `fixtures-local/landing-rw1b/` (1.4 GB) was deleted. The deletion was behind fail-closed guards: the name had to match exactly; the resolved path had to sit directly inside merge2's `fixtures-local`; the path had to be a real directory, ignored by git and holding no tracked file; nothing in it could have been modified in the last 30 minutes (`find -mmin -30`, where an error refuses); and no process could have a file open in it (`lsof +D`).

| Check | linear_algebra | probability |
|---|---|---|
| **(a)** open (migrate), main's code / the merge's | 165 → 208 (43) / 165 → 209 (44) | 165 → 208 (43) / 165 → 209 (44) |
| schema objects, main vs merge | the only difference is the merge's new `library_asks` table and its two indexes (`idx_library_asks_created`, `idx_library_asks_extraction`); every other table, index and trigger has identical SQL | same |
| rows of every table (332), on main's columns | **identical** (16,534 rows); `schema_migrations` differs only by the 209 row; `library_asks` is empty | **identical** (7,632 rows); `library_asks` is empty |
| `rebuild --shadow --json`, main vs merge | **0 differences** (facet 0, mastery 2, schedule 8; live database unchanged on both) | **0 differences** (facet 0, mastery 1, schedule 1) |
| `doctor --json`, main vs merge | **0 differences** (57 issues, 1 error) | **0 differences** (101 issues, 48 errors) |
| **(b)** upgrade shadow: main's code migrates to 208, then the merge's code applies **209 only** | applied 1, head 209; `foreign_key_check` empty, `integrity_check` ok; all 332 tables' rows identical to the 208 copy; schema differs only by `library_asks` and its indexes | same |
| `rebuild --shadow` and `doctor`: main's code on the 208 copy vs the merge's code on the upgraded copy | **0 differences** each | **0 differences** each |
| **(c)** at `mvp-0.8`: every facet's `facet_evidence_timelines` (`as_dict` plus the eleven `TimelinePoint` fields), 40 single-facet curves, every LO's `recipe_gaps` and `lo_certification` | **byte-identical JSON** (39 facets, 84 points, 2 corrections; 21 LOs, 1 certified) | **byte-identical** (29 facets, 2 points; 18 LOs, 0 certified) |
| the Today queue: `build_due_queue` at a frozen clock (2026-10-18 09:00 UTC), `persist_explanations=False`, with no session, a session and a greedy session; every `ScheduledItem` and the head | **byte-identical** (41 items each; head `pi_what_makes_function_axiom_strategy`) | **byte-identical** (67 items; head `pi_exercise_01kyn2kdf7h2kba1fp7wv7t3w5`) |
| the same, on a copy upgraded by main's code to `mvp-0.27` (`upgrade --to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice), then opened by each code (the merge's applies 209) | **byte-identical** certification and curves (82 points, 7 corrections, 1 attempt held `grade_contract_unrecorded`; 1 LO certified) and Today queue (43 items) | **byte-identical** (29 facets, 2 points; 0 certified; Today queue 67 items) |

**(d) The switches, through the merge's real sidecar** (stdio: `initialize`, then the RPCs; a pending library job was read with `reader.library_job` until done). Each case used its own copy of probability at 209, with the routes neutralized as above and one section appended to `learnloop.toml`.

| Case | Result |
|---|---|
| everything on | the contract carries `libraryAsk {compare: true, expandGraph: true, personalizedDefault: true}` and the palette's `orient` group with `where_else_explained`, `where_is_this_used` and `what_do_i_need_first`. A library-search ask returns 8 passages; *where else is this explained?* on `s14` of `ext_01KYMSJJNJQ0W9QHZ9ZMFD88NY` returns 12 passages with prerequisite and application expansions (policy `reading`). Each ask writes one `library_asks` row, one exposure row per passage and one `library_ask` event. `model_call_receipts` stays at 0 and `judgment_ledger` is unchanged (no organizer call: the notes were not requested) |
| `[library_ask] enabled = false` | all six RPCs (`reader.library_ask` ×2, `_ask_notes`, `_compare`, `_ask_tutor`, `reader.library_job`, `_job_cancel`) refuse `library_ask_disabled`. The contract has no `libraryAsk` key and no library palette rows; it equals the on-contract with those removed, byte for byte |
| `[reader_compare] enabled = false` | the contract's `libraryAsk.compare` is `false` (the rest of the contract is unchanged). The ask works; `reader.library_compare` refuses `reader_compare_disabled` |
| `[library_ask] expand_graph = false` | the contract's `libraryAsk.expandGraph` is `false`. An anchored ask with an LO gives 8 passages, no expansion hits, and a manifest of `expansions: []` and `expansions_skipped: "library_ask.expand_graph is off"` |
| a held-out selection (unit `u3`, spans `s1`–`s11`, marked `held_out_evaluation` on the copy through `save_unit_selection`; `held_out_material` covers it) | three asks (`reader`, `where_else_explained` with `s2` + `s14`, `what_do_i_need_first`) are each refused `exam_material`. The refusal surfaces on the job read; the start answers with a job. Nothing is written: no `library_asks` row, exposure, event or receipt |
| what the refusals write | nothing. In the `library_ask` off case and the held-out case, the dump before and after differs only by `initialize` re-stamping three derived rows (`facet_recall_state` ×2, `facet_capability_evidence`), as at RW6a and RW1b |

**`model_call_receipts` added during the parity runs: 0.** Every one of the 23 copies has 0, as the originals did.

### For the owner

- **No upgrade command.** RW4a has no successor; the vaults keep their label.
- **Migration 209 applies on the next open** (the desktop app, the CLI, the MCP runtime or the mobile host, whichever opens the vault first). It only adds the empty `library_asks` table and its two indexes. **Close the app, the MCP runtime and the mobile host, and back up first**, as for any migration.
- **Turning it off.** All in the vault's `learnloop.toml`:
  - `[library_ask]` / `enabled = false`: today's Reader and library search; every library RPC refuses.
  - `expand_graph = false`: no prerequisite or application expansion calls.
  - `personalized_default = false`: the chip starts off, and no learner state goes in the organizer prompt.
  - `[reader_compare]` / `enabled = false`: no compare.

  The library ask also needs `source_service.enabled` and `reader_inquiry.enabled` (both on by default).
- **The organizer route.** `ai.routing.library_organizer` is one listwise call per ask, through the shared `judge_listwise` (ledger task `library_contribution`). It runs only when the notes are fetched. Unset, it is the active provider (Codex here, a ChatGPT subscription call, `estimated_only`). Its metered spend is capped by `[library_ask] max_daily_cost_usd = 1.00` a UTC day. The cap is reserved atomically per attempt and priced at `source_retrieval.llm_price_per_million`. Subscription routes are never refused by it. A metered route without a price skips the notes and labels them. A deep question may also use T6's `source_query_rewrite` route (turn it off with `[source_retrieval] query_rewrite = false`).
- **Recorded at implement:**
  - **The concept-id expansion fix.** Real vaults' `LearningObject.prerequisites` / `.confusables` name concepts, so the sources spec's `expansion_lists` read expanded to nothing. `expanded_learning_objects` now resolves concepts to their LOs and reads `prerequisite` / `confusable_with` edges, and this also changes the sources spec's `expand` (retrieval context only). The parity copy confirmed it on probability: prerequisite and application hits appeared.
  - **Two accidental subscription calls.** The implementer's first smoke run on a copy made two `source_query_rewrite` calls on Codex (`gpt-5.6-sol`, ChatGPT subscription, about 17.8k input tokens each, $0 metered), with no dry run first. The landing made none.
- **To look at it:** see §10.
- **Open questions (defaults taken):**
  - stage record §8: 1, no comparing crumb; 2, no in-session library-ask UI; 3, `unrelated` dims; 4, exposure at the ask; 5, `assumes` derived from relations; 6, `lo_certification` per prerequisite uncached;
  - `reader-rw4a-codex-review.md`'s three: `reader.ask` stays synchronous; a cancelled tutor job's answer is still written; a library-page pick opens the first passage's book;
  - noted for a successor: RW1b's `reader.intent_routing` still takes a bounded `wait_ms`.
- **New at landing (small):**
  - **The held-out refusal comes on the job read.** `reader.library_ask` answers with a job, and the job read raises `exam_material`. The refusal still comes before any retrieval or write. The frontend reads jobs, so it shows the refusal. A direct RPC client that ignores job errors would just see a job.
  - **Each ask writes exposure rows at once.** One `source_exposure_events` row per passage shown (12 for one *where else* ask), as the sources spec's rule says. Over time this will grow the exposure table faster than other surfaces.
- **Also pre-existing:** the sidecar's `initialize` re-stamps three derived rows on open. The `mvp-0.27` upgrade holds one linear_algebra attempt `grade_contract_unrecorded`.
- **Not done:** no real-UI look (as in the stage). The organizer, compare and tutor were never run against a live model.
