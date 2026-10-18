# Adaptive hints H0: hint telemetry and the shared `help_assists` table (stage `hints-h0`)

Branch `hints/h0` (worktree `learnanything-merge4`), base `main` at
`610e61dc0` (RW4a landed; migration head 209). Spec:
`docs/specs/spec_adaptive_hints_v1.md` §2, §3.2, §5, §6.1-6.2, §6.3, §9, §10
(H0 row, order, §10.1), §11 (G-H1 telemetry clause, G-H10, G-H13, G-H17, the H0
tests), §15, §16.4; `docs/specs/spec_reader_workbench_v1.md` §5.5 (logging),
§5.7 (`help_assists`), §5.10 (RW2c's draws), §11, §13 (RW2b row), G64.

## 0. Plan (written before the code)

**Scope.** H0 only: no model call, no visible change. Not here: approach maps
(H1), the hint service, writer, chooser or `request_hint` (H2), workbench help
(RW2b/H3), any evidence, grading, scheduling or replay change.

**Migration 210** (`210_help_assists.sql`): `help_assists`, RAW_LEDGER, created
once with every column and CHECK value both specs write (G-H17, Reader G64):
the hints spec's §9 row, the Reader's §5.7 workbench columns, RW2c's assist
kinds (`bridge`, `example`, `compare_methods`, whose passage draws reuse
`propensity` / `seed`). CHECKs: `surface` (4), `assist_kind` (7), `hint_kind`
(12), `chooser` (4), `request` (4), `feedback_shortcut` (4, no
`different_approach`), `level_source` (2), `counted_by` (2), `level` and
`offered_level` 1-5, `shown` 0/1, `propensity` in [0, 1]. Deletes refused by
trigger; an attached `attempt_id` never changes. Classified in
`db/table_roles.py`; `fixtures/migration_head_209` -> `migration_head_210`
(backup-API copy, only 210 applied, rollback journal) and every hard-coded
path; the reference scripts' head. The two specs' column lists are
cross-checked in §3 below, each mismatch with its resolution.

**Store** `db/stores/help_assists.py` (the one SQL owner, registered in
`tests/test_architecture.py`): insert an authored-reveal row; attach a
session's unattached rows for an item to an attempt.

**Package `learnloop.hints`, minimal:** `telemetry.py` (the authored-reveal row
and the attach, both no-ops under the kill switch) and `report.py` (the
descriptive rows). An import-linter contract (G-H13): `learnloop.hints`
imports no evidence writer (attempts, learner, scheduling, diagnosis,
substrate, placement, field, goals, curriculum, router).

**Sidecar** `practice.record_hint_reveal` (in `handlers/practice.py`): writes
one row (`surface='practice'`, `assist_kind='hint'`, `hint_kind='authored'`,
`level=3` (§4.2's table), `chooser='none'`, `counted_by='client'`,
`shown=1`, `authored_index`, `work_hash` / `work_chars` of the draft sent with
the call (the text is hashed and dropped), `requested_at` / `shown_at`,
item id and hash, session id). Validation of the item and index; a no-op
(`recorded: false` with a reason) when the switch is off or the item is in an
active diagnostic block (the same block the screen refuses the reveal in). A
failed write is logged and answered `recorded: false`, never an error.
`submit_attempt`, `submit_dont_know` and the empty-stuck path attach the
session's unattached rows for the item to the attempt after it commits
(telemetry only, swallowed on failure; never changes the payload). Pinned
desktop-only in `tests/test_mobile_allowlist.py`; Tauri passthrough
`practice_record_hint_reveal`.

**Frontend.** `api.recordHintReveal`; `revealHint` fires it (unawaited, errors
swallowed) only when it actually reveals a new authored hint (not when
refused, not past the last hint). Nothing rendered changes.

**Config.** `[hints] telemetry_enabled = true` (modelled default, left out of
the decision-only template); every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry
recomputed with a "no scoring, scheduling, projection or serving change" note.

**Report.** `learnloop hints report [--since] [--surface] [--json]` (§6.3's
named surface; read-only, no model, no learner text): per kind, level and
surface, with authored hints as the baseline kind: reveals, items, sessions,
per-item and per-session counts, which hint in the list, timing (reveal to
submit), what followed (the attempt's recorded outcome, more help in the same
attempt, later independent success on the item with pending counts),
unattached reveals.

**Tests.** `test_hint_telemetry.py`, `test_help_assists_schema.py` (G-H17, the
durability-lane migration case), G-H10 (rebuild and shadow replay with
`help_assists` populated: zero model and embedding calls, and replay never
reads the table), the report; vitest for the screen's call.

**Known deviation (recorded, not fixed).** Migration 208 (RW1b) widened
`learner_text_gaps.source_kind` with `workbench_text` and `reader_formative`
but not `hint_feedback`, so G-H17's "one widening migration" cannot hold; H2
carries a second widening for `hint_feedback`.

## 1. What was built

### 1.1 Migration 210 (`migrations/210_help_assists.sql`)

`help_assists`, RAW_LEDGER (`db/table_roles.py`), 58 columns: every column of
the hints spec's §9 row (38), the Reader's §5.7 workbench columns (17,
`assist_kind` included) and three logged-but-unlisted columns (§3 below).
CHECKs, each holding every value either spec writes: `surface` (`practice`,
`workbench`, `guided_redo`, `tutor`), `assist_kind` (`hint`, `check`,
`discriminate_answer`, `bridge`, `example`, `compare_methods`, `feedback`),
`hint_kind` (the twelve kinds of hints §4.2, `continuation` included),
`chooser` (`decider`, `fallback`, `learner_pick`, `none`), `request` (`more`,
`feedback`, `book_way`, `smaller_step`), `feedback_shortcut`
(`not_where_stuck`, `too_big`, `learner_route`, `notation`; no
`different_approach`), `level_source` (`offered`, `learner_pick`),
`counted_by` (`client`, `server`), `level` and `offered_level` 1-5, `shown`
0/1, plus sanity bounds (`horizon` >= 1, `authored_index` >= 0, `work_chars`
>= 0, `latency_ms` >= 0, `propensity` in [0, 1]). Foreign keys: `attempt_id`
-> `practice_attempts`, `workbench_session_id` -> `workbench_sessions`. Four
indexes (session+item, attempt, workbench session, surface+time). Two
triggers: no delete; the identity columns (`id`, `surface`, `assist_kind`,
`practice_session_id`, `requested_at`) and an attached `attempt_id` are fixed
(later phases may still fill `shown_at`, a workbench problem's item binding,
and the rest). No DERIVED table, so no replayer; replay and rebuild never read
it.

Head fixture: `fixtures/migration_head_209` -> `fixtures/migration_head_210`,
a backup-API copy of the base's 209 database with only 210 applied under
`upgrade_allowance(UPGRADE_TEST_HELPER)`, `wal_checkpoint(TRUNCATE)` -> `(0,
0, 0)`, `journal_mode=DELETE` (header bytes 18-19 are 1/1), `integrity_check`
ok, `foreign_key_check` empty, copied in with the backup API, no companion
files; README gains the 210 paragraph and the chain. Every file naming the old
path now names `_210` (26 test files, both reference scripts with `SCHEMA_HEAD =
210`, `docs/decider-tier1-migration.md`, the Database Catalog);
`test_route_rules_in_grader.py`'s head assertion is 210; RW4a's
`test_library_asks_migration.py` now tolerates 210 following 209 on the way to
head (its "nothing else" set excludes `help_assists`' objects) and its head
test reads the code's head.

### 1.2 Store and package

- `src/learnloop/db/stores/help_assists.py` (registered SQL owner in
  `tests/test_architecture.py`): `COLUMNS` (table order, pinned by the schema
  test), `insert_assist` (refuses unknown columns), `attach_attempt` (fills
  `attempt_id` on the session's unattached `surface = 'practice'` rows for the
  item).
- `src/learnloop/hints/` (minimal): `telemetry.py` (`record_authored_reveal`,
  `attach_reveals_to_attempt`, `reveal_instant`, `work_digest`,
  `telemetry_enabled`, `AUTHORED_LEVEL = 3`) and `report.py`
  (`build_hints_report`). Import-linter contract `hints-never-write-evidence`
  (G-H13): `learnloop.hints` imports none of `learnloop.attempts`, `.learner`,
  `.scheduling`, `.goals`, `.diagnosis`, `.curriculum`, `.substrate`,
  `.placement`, `.field`, `.router`, `.daily_plan`, `.cli`, `learnloop_sidecar`.

### 1.3 The sidecar (`src/learnloop_sidecar/handlers/practice.py`)

- `practice.record_hint_reveal` (`HintRevealInput`: `sessionId`,
  `practiceItemId`, `authoredIndex` >= 0, `answerMd`, `revealedAt`): with the
  switch off it answers `{recorded: false, reason: "telemetry_disabled"}`
  before reading anything; an unknown item is `not_found`, an index past the
  item's hints `validation_error`; during a diagnostic block on the item (an
  in-progress episode with a *served* presentation of this item, the state in
  which the screen refuses the reveal) it answers `reason:
  "diagnostic_block"` and writes nothing; otherwise one row: `surface =
  'practice'`, `assist_kind = 'hint'`, `hint_kind = 'authored'`, `level = 3`,
  `chooser = 'none'`, `counted_by = 'client'`, `shown = 1`, `authored_index`,
  `practice_item_id` and `practice_item_hash` (the current revision),
  `practice_session_id`, `work_hash` (sha256) and `work_chars` of the draft
  sent (the text is never stored), `requested_at = shown_at` = the client's
  press time (ms precision, UTC), or the sidecar's clock when the client's is
  missing, malformed or more than 60 s ahead. A failed write is logged and
  answered `reason: "write_failed"`, never raised.
- `submit_attempt`, `submit_dont_know` and the empty-stuck path call
  `_attach_hint_reveals` after the attempt and its receipt commit: telemetry
  only, skipped with the switch off, failures logged and swallowed, the
  response unchanged. A retried submit answering from its receipt attaches
  nothing new.
- `HINT_TELEMETRY_RPCS`, pinned desktop-only in `tests/test_mobile_allowlist.py`
  (with `submit_attempt` and `submit_dont_know` as the extended RPCs).
- Tauri: `sidecar_passthrough!(practice_record_hint_reveal,
  "practice.record_hint_reveal")` and its `generate_handler!` entry.

### 1.4 Config (modelled default; out of the decision-only template)

`[hints] telemetry_enabled = true` (`HintsConfig`, `LearnLoopConfig.hints`).
All 19 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries (`mvp-0.9`..`mvp-0.27`) were
recomputed with `defaults_fingerprint_for_version` after deleting the
template `.pyc`; every one moves only because the effective config gains the
section, recorded in the template comments with the "no scoring, scheduling,
projection or serving change" note. No `[hints]` key besides
`telemetry_enabled`: the spec's other keys belong to H1-H5.

### 1.5 The frontend

- `api.recordHintReveal` (`apps/learnloop-tauri/src/api/client.ts`).
- `PracticeScreen.tsx` (15 lines): `revealHint`, after its existing refusals
  (not ready; the plain card's check on your own; a diagnostic block), calls a
  module-level `recordHintReveal` with the index it is about to show only when
  `hintsUsed < item.hints.length` (so never past the last hint or on an item
  without hints), unawaited, its rejection and a synchronous throw (a sidecar
  or mock without the RPC) both swallowed. Nothing rendered depends on it.

### 1.6 The report (`learnloop hints report [--since] [--surface] [--json]`)

§6.3's named surface, created here (`src/learnloop/cli/hints.py`,
`learnloop/hints/report.py`; CLI help snapshot updated). Read-only, no model,
no learner text. Per surface, assist kind, hint kind and level (authored hints
flagged `baseline`): shown, items, sessions, attempts, unattached, reveals per
item and per session (p50/p95 with n), which hint in the list
(`by_authored_index`), empty work at request, seconds from reveal to submit
and seconds into the attempt (from the attempt's latency), more help in the
same attempt, the attempt's recorded outcome (correct / partial / incorrect /
ungraded from `practice_attempts.correctness`), attempt types, later
independent success on the item and on its learning object (pass / fail /
pending, never imputed); totals; the top 20 items by reveals (a display cap);
and `not_yet_measured` naming what needs H1-H5 (unaided next progress, "doesn't
connect", off-policy estimates, the expertise-reversal split). The CLI adds
the vault's `[hints]` section.

## 2. Gates and where they are tested

| Gate | Test |
|---|---|
| G-H1 (telemetry clause): off, no `help_assists` row; the RPC a no-op; practice RPCs and screen as on the base | `test_hint_telemetry.py::test_kill_switch_writes_nothing_and_the_rpc_is_a_no_op`, `::test_hints_used_primed_reveals_and_evidence_are_identical_with_telemetry_on_or_off` (every existing practice RPC's response and every table but `help_assists` identical on vs off, ids made deterministic); `PracticeScreen.hintTelemetry.test.tsx` (screen identical whether the call records, no-ops, fails or is missing) |
| No evidence change (H1, §5): `hints_used`, `primed`, reveal events, evidence byte-identical on vs off | the same comparison, plus explicit `attempt_type, hints_used, primed` rows and `reveal_events` count 0; `::test_submit_attaches...` (the client's count kept with more rows than it counts) |
| G-H10: rebuild and replay make zero model and embedding calls with `help_assists` populated, and never read it | `::test_rebuild_with_help_assists_populated_calls_no_model_and_never_reads_it` (model/embedding client constructors forbidden; the derived state equals a rebuild of a copy with the table dropped; rows untouched; shadow rebuild too) |
| G-H13: import-linter contract; RPC desktop-only; table classified | `lint-imports` (`hints-never-write-evidence`), `test_mobile_allowlist.py`, `test_help_assists_schema.py::test_help_assists_is_a_raw_ledger`, `test_table_roles.py` |
| G-H17: one schema with every column and CHECK value of both specs | `test_help_assists_schema.py` (columns = §9 + §5.7 + the three logged columns, in `COLUMNS` order; every CHECK value admitted, NULL where optional, outside values and `different_approach` refused; the 209 -> 210 upgrade adds only the table, indexes and triggers; the durability lane) |
| G-H14 (cold and probe parity) | the screen's existing refusals are untouched (vitest: no call on a refused reveal in a diagnostic check or a plain-card check on your own); the sidecar's served-probe check (`::test_no_row_during_a_diagnostic_block`, `::test_the_diagnostic_block_is_a_served_probe_of_this_item`) |

## 3. The two specs' column lists, cross-checked

Both lists were read in full (hints §9; Reader §5.7, §5.5 "Logging", §5.10
RW2c, §11, §13 RW2b row). They agree on every column name and on every CHECK
value; the mismatches are in what they leave unsaid, resolved so neither
spec's later phase rebuilds the table:

1. **Nullability.** Hints §9 marks `practice_item_id`, `practice_item_hash`,
   `practice_session_id`, `work_hash`, `work_chars` and `counted_by` as
   required, but a workbench problem has no item until its import binds (RW2a,
   `workbench_sessions.practice_item_id`), and the workbench's practice
   session is filled at submit. Resolved: nullable (H0 always fills them).
2. **`counted_by` on uncounted rows.** Only `client | server` is listed, yet a
   `discriminate_answer` or `feedback` row is counted by neither (hints §5).
   Resolved: nullable, NULL meaning "counted by neither"; no third value was
   invented.
3. **Logged on the row but in neither list.** Hints §4.2/§6.2 keep "the drawn
   option ... and record the served kind" (a contract downgrade or a zero-EIG
   fallback serves a kind other than the one drawn), and §6.2 and Reader §5.5
   ("on the `help_assists` row: ... the policy and question-set versions and
   the state hash") log the question-set version and the state hash.
   Resolved: three nullable columns, `drawn_option_json`,
   `question_set_version`, `state_hash` (the receipts keep theirs too). The
   map version is `map_id` (each `approach_maps` row is one version).
4. **`hint_kind`'s count.** Reader §5.7 says "the adaptive-hints spec's eleven
   plus `continuation`", hints §9 lists twelve with `continuation`: the same
   twelve.
5. **`assist_kind` outside the workbench.** Reader §5.7 says every other
   surface writes `hint`; hints §16.4 item 1 adds `discriminate_answer` there.
   The CHECK holds all seven either way (wording only, as §16.4 says).
6. **`request`'s values.** Listed by the hints spec only (§16.3 item 6); the
   CHECK takes its four.
7. **Levels.** Reader G5 speaks of help levels 0-5; level 0 is the learner's
   own work and never an assist row, so `level` and `offered_level` are 1-5
   (the task's ruling; Reader §5.5's suggested rung is 1-5).
8. **Types neither spec states.** `seed` TEXT (the router's and migration
   098's convention), `propensity` and `eig_nats` REAL, `horizon`, `level`,
   `latency_ms`, `work_chars`, `authored_index` INTEGER, `shown` 0/1.
9. **RW2c.** Its kinds (`bridge`, `example`, `compare_methods`) are in
   `assist_kind`; its passage draws use `propensity` and `seed` "on the assist
   row" (Reader §5.10); its passages and roles live in
   `retrieval_manifest_json`, `cited_span_ids_json`, `alternatives_json`. No
   further column.

## 4. Decisions and deviations

- **The kill switch and the screen.** The screen always sends the reveal; the
  sidecar answers off before reading anything. No flag was added to the
  client's config payload (that would change `get_config` / `load_vault`), so
  the screen's rendering and every pre-existing RPC response are identical to
  the base with the switch off; the only new traffic is the no-op call.
- **The attach is after the commit, outside the attempt's transaction**, so
  the submit path's transaction and response are untouched. If it fails (or
  the process dies between the two), the rows stay unattached, and a later
  attempt on the same item in the same session would take them. Recorded for
  H2 (friction 2). Off, nothing is attached, so rows written while on stay
  unattached if the switch is turned off before submit.
- **Level 3 for authored hints**, as §4.2's table says (the item's last,
  "near-give-away" hint included); `authored_index` is 0-based.
- **Timing** is the client's press time (the sidecar answers one request at a
  time, so a reveal sent while another call runs would be stamped late), with
  a 60 s clock-skew allowance (a timing sanity cap, not a rule).
- **A server-side diagnostic-block check** mirrors the screen's refusal (a
  served probe presentation of the item); the plain card's "check on your
  own" refusal is the screen's only (the sidecar does not know the card).
  On the classic card a cold check still reveals with its banner, unchanged,
  and the reveal is recorded.
- **`learnloop hints report` is new**: the spec names it (§6.3); there was no
  earlier hints report to extend.
- **§3.2's citations, re-verified on `610e61dc0`:** the substance holds, the
  lines moved: the serializer's hints at `serializers.py:432-438` (spec
  `:368-377`); `revealHint` at `PracticeScreen.tsx:788-800` (spec `:576-584`),
  Ctrl+H at `:723-725` (spec `:516-518`), the banners at `:1497` and `:1657`
  (spec `:1189-1192`); the fold at `handlers/practice.py:858-865` (spec
  `:556-561`) and `submit_dont_know_on` at `:995` (spec `:676-717`);
  `REVEAL_SOURCE_KINDS` at `reveal_ledger.py:49` (spec `:37`); auto-prime's
  0.35 at `attempts.py:152` (spec `:147`); `hint_equivalents_for_submission`
  at `tutor_qa.py:900` (spec `:741`); "the timing of ordinary hints" still at
  `field/probability_states.py:100`. Two facts changed since the audit: hints
  are **not** keyboard-only any more (UX Phase 4's plain card has a "Hint"
  button, `PracticeScreen.tsx:1741`, which calls the same `revealHint`), and
  submit now also folds the item's open workbench problems' held hints
  (`_held_assistance`, RW2a).
- **Known deviation (recorded, not fixed).** Migration 208 (RW1b) widened
  `learner_text_gaps.source_kind` and `learner_text_gap_jobs.source_kind` with
  `workbench_text` and `reader_formative` but not `hint_feedback`, so G-H17's
  "one widening migration" cannot hold; H2 carries a second widening (both
  tables, temp-then-rename, FK check, durability test) for `hint_feedback`
  alone. Also recorded in the spec's §15 (with an H0 landing note).

## 5. Successor

None (§10.1). Telemetry only: no scoring, scheduling, projection, serving,
grading or replay path reads the rows or the key; `hints_used` is still the
client's count; authored reveals still write no reveal row (§10.1 successor
3 stays a named later successor).

## 6. Tests and counts

New: `tests/test_hint_telemetry.py` (25), `tests/test_help_assists_schema.py`
(9, one durability-marked),
`apps/learnloop-tauri/src/screens/PracticeScreen.hintTelemetry.test.tsx` (6).
Changed: `tests/test_mobile_allowlist.py` (the pinned H0 RPCs),
`tests/test_architecture.py` (the store), `tests/cli_help_snapshot.json`,
`tests/test_library_asks_migration.py` and `tests/test_route_rules_in_grader.py`
(head 210), and the other test files whose head-fixture path moved (26 in all).

## 7. Files

- Migration and fixture: `migrations/210_help_assists.sql`;
  `fixtures/migration_head_210/` (renamed from `_209`, rebuilt, README).
- Python: `src/learnloop/hints/{__init__,telemetry,report}.py`,
  `src/learnloop/db/stores/help_assists.py`, `src/learnloop/cli/hints.py`,
  `src/learnloop/cli/__init__.py`, `src/learnloop/config/schema.py`,
  `src/learnloop/config/template.py`, `src/learnloop/db/table_roles.py`,
  `src/learnloop_sidecar/handlers/practice.py`, `pyproject.toml`.
- Frontend / Tauri: `apps/learnloop-tauri/src/api/client.ts`,
  `apps/learnloop-tauri/src/screens/PracticeScreen.tsx`,
  `apps/learnloop-tauri/src-tauri/src/{commands,main}.rs`.
- Docs: this file; `docs/specs/spec_adaptive_hints_v1.md` §15;
  `docs/learnloop-architecture-vault/_scripts/db_{generate,validate}_reference.py`
  (head 210, the `hints` config section's concern); the regenerated
  references (new `Tables/help_assists.md`, `Fields/Config - hints.md`,
  commit labels and line citations elsewhere; the prose counts in
  `Configuration.md` and `Database.md`: 881 leaves, 61 sections, 329 tables);
  `docs/decider-tier1-migration.md` (the head path).

## 8. Open questions (with the default taken)

1. **The classic card's cold-check reveal** (allowed there with its banner)
   is recorded like any reveal. Default: record it (the reveal happened; the
   attempt is already assisted by the client's count).
2. **The last authored hint's level.** §4.2 puts `authored` at 3; the item's
   last hint is often a near-give-away. Default: 3 for every authored hint;
   the report's `by_authored_index` shows the last-hint share.
3. **Rows left unattached** (switch turned off mid-attempt, an attach that
   failed, an item never submitted) stay unattached and count as
   `unattached` in the report. Default: no back-fill.
4. **Settings exposure** of `hints.telemetry_enabled`. Default: none (a
   modelled default in `learnloop.toml`, like the other kill switches).
5. **`submit_dont_know`'s fold asymmetry** (spec §14 Q5) is untouched by H0.

## 9. Friction notes for H1, H2 and RW2b

1. **H1.** `help_assists.map_id` has no foreign key (approach_maps does not
   exist yet), and adding one later would need a rebuild: keep it a soft
   reference and validate in code. H1's migration is 211 with the usual head
   rename (`migration_head_210` -> `_211`; 26 test files and both reference
   scripts name it).
2. **H2's server fold.** Count shown level-1-3 rows with `counted_by =
   'server'` since the item's last attempt in the session, bounded by time
   (not only `attempt_id IS NULL`): a row H0 failed to attach would otherwise
   be counted into a later attempt. `store.attach_attempt` attaches
   `surface = 'practice'` only; guided redo and tutor rows need it widened.
   When the service serves an `authored` hint itself, that row is
   server-counted while `record_hint_reveal`'s are client-counted: keep the
   two paths from counting one reveal twice (G-H3).
3. **H2 and the import-linter contract.** `hints-never-write-evidence`
   forbids `learnloop.attempts` (where the reveal ledger lives) and
   `learnloop.diagnosis` (`instrument_expected_information_gain`) and
   `learnloop.placement` (the state reads). Either write the `tutor_answer`
   reveal from the sidecar handler and pass the EIG and state readers in by
   injection, or add `ignore_imports` lines with their reasons for pure reads.
4. **H2's learner-text widening** is a second migration (§4), adding
   `hint_feedback` to both `source_kind` CHECKs.
5. **RW2b.** Workbench rows carry `workbench_session_id`; the practice
   session is known only at submit, so the workbench attach must key on the
   workbench session (the H0 attach does not touch them). The workbench's
   held hints (`workbench.held_hints`, RW2a's `carried_hints`) and server-folded
   `help_assists` rows are two sources of one count: fold one rule (Reader
   §5.4). `counted_by` NULL for `feedback` and `discriminate_answer` rows.

## 10. Owner-run commands

```bash
uv run learnloop hints report --vault <path> [--since 7d] [--surface practice] [--json]
# kill switch, in the vault's learnloop.toml:
#   [hints]
#   telemetry_enabled = false
```

Migration 210 is applied by the coordinator when the vault is next opened (no
command; it only creates the empty table).

**Model calls made in this stage: 0** (tests use fakes; the one manual smoke
ran no sidecar and no model route: a backup-API copy of the
`fixtures/linear_algebra` git version in `fixtures-local/h0-la`, upgraded
155 -> 210 by `open_vault_repository`, `foreign_key_check` empty,
`integrity_check` ok, only new empty tables plus their seed rows created; one
authored reveal recorded and reported; the copy then deleted).

## 11. Gate (this step; the full suite, the whole durability lane and the whole vitest run are the landing gate's)

Run in the worktree with `TMPDIR=fixtures-local/tmp`; `/tmp/learnloop-fullsuite.lock` was free throughout.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **25 kept, 0 broken** (24 on the base plus `hints-never-write-evidence`).
- Targeted pytest, `uv run pytest -n auto <72 files>`: **1567 passed** (277.7 s). The files: every new or changed test file, every file that drives `submit_attempt` / `submit_dont_know` / the practice handler through the sidecar, every file naming the head fixture, the config-defaults-snapshot files, and the contract tests (CLI help snapshot, serializer snapshot, desktop RPC contract, mobile allowlist, architecture, table roles, coordinated migrations, tracked fixture databases, SQLite file copies, config, instructional layering):
    `tests/test_architecture.py`   `tests/test_causal_p2_acceptance.py`   `tests/test_causal_repair_sidecar_rpcs.py`   `tests/test_cli_help_snapshot.py`   `tests/test_config_refactor.py`   `tests/test_coordinated_migrations.py`   `tests/test_daily_plan_composition.py`   `tests/test_daily_plan_replay.py`   `tests/test_daily_plan_review_regressions.py`   `tests/test_daily_plan_rpc.py`   `tests/test_desktop_rpc_contract.py`   `tests/test_diagnosis_async_router.py`   `tests/test_diagnosis_card.py`   `tests/test_diagnosis_input_provenance.py`   `tests/test_diagnosis_replay.py`   `tests/test_exam_protection_review.py`   `tests/test_facet_identity_actions.py`   `tests/test_field_signal_production_paths.py`   `tests/test_forecast_receipts_landing.py`   `tests/test_forecast_receipts.py`   `tests/test_help_assists_schema.py`   `tests/test_hint_telemetry.py`   `tests/test_import_split_parity.py`   `tests/test_instructional_layering.py`   `tests/test_learner_text_source_widening.py`   `tests/test_library_asks_migration.py`   `tests/test_method_explicit_upgrade.py`   `tests/test_migrations.py`   `tests/test_mobile_allowlist.py`   `tests/test_mvp010_upgrade.py`   `tests/test_mvp011_upgrade.py`   `tests/test_mvp013_upgrade.py`   `tests/test_mvp014_upgrade.py`   `tests/test_mvp015_upgrade.py`   `tests/test_mvp016_upgrade.py`   `tests/test_mvp017_route_check_replay.py`   `tests/test_mvp017_upgrade.py`   `tests/test_mvp018_upgrade.py`   `tests/test_mvp020_upgrade.py`   `tests/test_mvp021_upgrade.py`   `tests/test_mvp022_upgrade.py`   `tests/test_mvp023_upgrade.py`   `tests/test_mvp024_upgrade.py`   `tests/test_pfc_unverified_unassessed.py`   `tests/test_placement_opening_probes.py`   `tests/test_plan_determinism.py`   `tests/test_reader_rw3a_landing.py`   `tests/test_reader_workbench_rw2a.py`   `tests/test_reading_step_switch.py`   `tests/test_rebuild_orchestrator.py`   `tests/test_recurrence_commands.py`   `tests/test_recurrence_live.py`   `tests/test_regrade_contract_successor.py`   `tests/test_regrade_contract_upgrade.py`   `tests/test_router_r1_composition.py`   `tests/test_router_r2a_serving.py`   `tests/test_router_r2bc_landing.py`   `tests/test_route_rules_in_grader.py`   `tests/test_serve_eligibility_review.py`   `tests/test_shadow_rebuild.py`   `tests/test_sidecar_contract.py`   `tests/test_sidecar_item_authoring.py`   `tests/test_sidecar_serializer_snapshot.py`   `tests/test_sidecar_trace_and_clarification.py`   `tests/test_sidecar_tutor_qa.py`   `tests/test_source_block_fts.py`   `tests/test_sqlite_file_copies.py`   `tests/test_stuck_prompt.py`   `tests/test_stuck_prompt_replay.py`   `tests/test_table_roles.py`   `tests/test_tracked_fixture_databases.py`   `tests/test_ux_phase4_feedback.py`
- Durability: `uv run pytest -m durability tests/test_help_assists_schema.py tests/test_library_asks_migration.py tests/test_learner_text_source_widening.py tests/test_migrations.py tests/test_tracked_fixture_databases.py tests/test_daily_plan_replay.py`: **5 passed** (60 deselected); and `uv run pytest -n auto --durable-sqlite tests/test_help_assists_schema.py tests/test_hint_telemetry.py`: **33 passed** (production pragmas and WAL for every H0 test).
- Frontend (`apps/learnloop-tauri`): `npm install` ok; `npm run typecheck` ok; `npx vitest run src/screens/PracticeScreen.hintTelemetry.test.tsx src/screens/PracticeScreen.test.tsx src/screens/PracticeScreen.phase4.test.tsx src/screens/PracticeScreen.workbench.test.tsx`: **62 passed** (4 files); `npx vitest run src/api`: **6 passed** (2 files); `npm run frontend:build`: ok.
- `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml`: ok.
- References: `db_generate_reference.py` (head 210; new `help_assists` and `Config - hints` notes; commit labels and line citations elsewhere) and `db_validate_reference.py`: **0 errors** (329 table notes, 881 leaves); `validate_vault.py`: passed (1124 notes). `desktop_validate.py` and `module_validate.py` fail on this base for files H0 does not touch (`pdfSelection/testing/syntheticBook.ts`; missing module notes such as `ai/agreement.md`); not part of this gate.
- Snapshots: `tests/cli_help_snapshot.json` rewritten (`hints`, `hints report`, the root help); the template `.pyc` cleared before the defaults snapshots were recomputed and before the targeted run.

## 12. Commits

- `308b13bd8` the stage (migration 210, head fixture, store, `learnloop.hints`, the RPC and attach, config and snapshots, the report, frontend and Tauri, tests, spec §15, this record).
- `be34c4a73` the references regenerated on `308b13bd8` (commit labels only; `db_validate_reference` 0 errors; `validate_vault` passed).
