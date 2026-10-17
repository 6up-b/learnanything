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
