# Teacher TE1b: the router suggests lessons, the learner opts in

**Stage:** `teacher-te1b-router-suggestions`, branch `teacher/te1b-router-suggestions` (worktree
`learnanything-astrafix`), base `1a33bb5db3` (main: teacher TE1 + C4, `mvp-0.41`, migration head 234). **Spec:**
`docs/specs/spec_teacher_v1.md` §15.1 (with §7 step 1, §8.3 `origin`, §18.1, §18.3, §18.4, §19, §20's TE1b row,
§21). **No paid or live call was made**: nothing in TE1b calls a model (the draw, the acceptance model and the
card are code; the lesson Start reuses TE1's `lesson.turn`, tested with TE1's `TeacherFake`). Every ad-hoc script
ran under `env -i` with an empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` and
`LEARNLOOP_ROUTER_MODELS=off`. No owner vault was opened, `~/.config/learnloop` was not read, nothing ran against
`fixtures/linear_algebra`, `fixtures/probability` or `fixtures/arxiv_v2`, and no GUI was launched.

**A successor:** `mvp-0.43` after `mvp-0.41` (ONE constant, `LESSON_SUGGESTIONS_ALGORITHM_VERSION`). follow-ups
Nov 2 lands first as `mvp-0.42`, so this claims the next tag; at the landing the chain becomes
`… mvp-0.41, mvp-0.42, mvp-0.43` and `PREDECESSOR` (`lesson_suggestions_upgrade.py`) moves to follow-ups' constant
(renumber if another successor lands first). **One migration:** 236 (follow-ups Nov 2's 235 lands first; the head
fixture is `migration_head_236`, rebuilt from main's `migration_head_234` with only 236 applied: at the landing
rebuild it from main's then-current head, which will hold 235).

## What was built

| Piece | Where |
|---|---|
| The tag `LESSON_SUGGESTIONS_ALGORITHM_VERSION = "mvp-0.43"`, appended to `SUCCESSOR_CHAIN`; `LESSON_SUGGESTIONS_VERSIONS` | `src/learnloop/algorithm_versions.py` |
| The upgrade (the TE1 pattern): accepts mvp-0.41 or mvp-0.9 onwards through the chain; one journalled activation; `complete_interrupted_activation` hands an earlier journal to TE1's; the CLI's and the sidecar's installed completion is this link's; `learnloop upgrade --to mvp-0.43` and the bare upgrade's target | `src/learnloop/lesson_suggestions_upgrade.py`, `cli/app.py`, `cli/runtime.py`, `learnloop_sidecar/context.py`, `activation_journal.py`, `pyproject.toml` |
| Config `[router.lesson_suggestions]`: `enabled` (the successor's kill switch, default on) and `ceiling_per_day` = 3 (`keep`); both classified in the parameter registry; every defaults snapshot recomputed (the keys are present and inert below the tag; dropping them reproduces main's values, tested) and mvp-0.43 recorded | `config/schema.py`, `config/template.py`, `params/parameter_registry.py` |
| Migration 236: `router_decisions` rebuilt so `decision_kind` admits `lesson_suggestion` (202's temp-then-rename precedent, every row and id kept, the same indexes, triggers and foreign keys); `router_suggestion_responses` (RAW_LEDGER, append-only, one response per decision, a decline carries no lesson) | `migrations/236_router_lesson_suggestions.sql`, `db/table_roles.py`, `fixtures/migration_head_236/` |
| The design `lesson_suggestion_draw`, registered where every decision row is written | `db/stores/router.py` |
| The functional core: the acceptance model (logistic with latent effects, AD's ADF step per recovery-grid bank, grid weights by `log Z`), the replay of the response ledger, the decline bookkeeping, the candidates' values and the draw with exact propensities | `src/learnloop/router/lesson_suggestions.py` |
| The shell: candidates, the day's draw and decision row, the `ignored` sweep, the card view, the response | `src/learnloop/daily_plan/lesson_suggestion.py`, `db/stores/router_suggestions.py` |
| Start opens a TE1 lesson with `origin = 'router'`, `origin_ref` = the decision id, under the lesson id its response recorded (refused unless that response exists; a second Start resumes the lesson); the receipt's `origin` is the decision id (§8.3) | `teacher/service.py` |
| The intention-to-treat outcome of every suggestion decision (shown or not) on the drawn LO's `R_cold`, in the one `router_outcomes` replayer | `router/outcomes.py` |
| `lesson.suggestion` (the day's card, no model call) and `lesson.suggestion_respond`; `lesson.turn` `open` takes `origin = "router_suggestion"`, `suggestion_decision_id` and `lesson_id`; desktop only; `teacher.suggestions` in the UI config (absent while off) | `learnloop_sidecar/handlers/lesson.py`, `learnloop_sidecar/context.py` |
| The Today card (Start, up to two alternatives, Not now; a section in the page, never a dialog), shown in the default shell's Today (`TodayPlace`, Codex review F1) and the classic `TodayScreen`, only while `teacher.suggestions` is on; Start opens the lesson screen with the suggestion's ids | `apps/learnloop-tauri/src/screens/today/LessonSuggestionCard.tsx`, `screens/TodayScreen.tsx`, `screens/LessonScreen.tsx`, `app/App.tsx`, `app/algoConfig.ts`, `api/client.ts`, `api/dto.ts`, `src-tauri/src/{commands,main}.rs` |
| Generated references (DB, config, desktop) regenerated; validators' pins moved (schema head 236; 370 table notes; 1121 config leaves; 308 TS sources) | `docs/learnloop-architecture-vault/` |

## How it works (the decisions taken here)

1. **Candidates** (`instruct(lesson)`, one LO each, §15.1's three reasons): an LO on an active goal with no
   attempt (`new_goal`); an LO whose two latest cold attempts (AD's cold types, unprimed, unhinted, graded) were
   both not right (`cold_failing`); an attempted LO that adaptive difficulty's posterior predicts below its practice
   band (`below_band`, `adaptive_difficulty.readiness.band_positions`: the LO's main cell tested, AD's own
   out-of-band rule `max P_band < calibrate_below` over its commission points, and even the easiest point's expected
   success under the band's lower edge; Codex review F6). An LO with an
   open lesson, or taught by a lesson since its last attempt, is left out (listed on the row's exclusions).
2. **The acceptance model** `P(accept) = σ(h·θ)`: intercept; time of day as sin/cos; the share of a lesson that fits
   in the plan's minutes left (`min(left, 15)/15 − 1`); re-entry; the reason (two indicators); the days since the
   last suggestion (`1/(1 + 1) − 1/(1 + d)`: 0 at the seeded one-a-day cadence, every gap its own value; Codex review
   F7); and for a declined goal `−D · g_R(d)`, `g_R(d) = max(0, 1 −
   log(1+d)/log(1+R))`, with the recovery `R` on a grid. Every context feature is 0 at the reference context, so
   the seeds are the reference context's.
   **Seeded priors (`suggestion_priors_v1`, basis `legacy`, every effect N(·, 1²)):** the intercept is centred
   where the prior predictive is 0.9 (revision 3's "about one a day": with the one-card-a-day rule a card on about
   nine days in ten), `D` where a goal just declined is at 0.01, and `R ∈ {3.5, 4.95, 7, 9.9, 14}` days (centred on
   the 7-day mute, a factor of two either side), uniform weights. The seeded curve for a declined goal:
   0.01 at the "Not now", 0.12 a day later, 0.52 at three days, 0.83 at seven, back at 0.9 by fourteen (tested).
   Every shown suggestion's response is an observation (accepted 1; declined or ignored 0; a chosen alternative 0
   on the card's suggestion and 1 on the alternative), entered in response order with the inputs stored at its
   draw, so a replay never reads today's state. Every reader replays the ledger (no derived table).
3. **The draw** (once per local day, at Today's open): each candidate's value is `log P(accept) + log(1 − p)` (`p`
   the predicted success: room to learn); the target over the top `router.k` is drawn by the router's design for
   its mode (codex re-review F5): `router.mode = "mixture"` is the router's `model_mixture` (the configured
   `router.weights`, the staged rule's pick the top value, the `epsilon_min` floor each; the Decider and the
   router LLM are not asked about lesson candidates, so their weight is the staged rule's, G7), `staged` is the
   randomization layer's `epsilon_tiebreak` on `P(accept)·room`; then the card shows with the drawn candidate's
   `P(accept)`. Shown or not, ONE
   `lesson_suggestion` decision is written (receipt key `lesson_suggestion:<date>`: at most one a day), with the
   candidates' `pi`, `p_accept`, `room`, `value` and inputs, the seed, the snapshot hash, the model summary, the
   card hash, and the exact joint probability of the drawn target and the arm (`π(c)·P(c)` shown, `π(c)·(1 − P(c))`
   no card: the outcome is the drawn target's, so the propensity is too; `pi_drawn` and `arm_propensity` are on the
   detail, the aggregate `p_no_card` only for the report; Codex review F3), and the predeclared outcome scope
   (`target_scope`: the target and the up-to-two candidates the card offers, or would offer, beside it). So
   suggestions come as often as they are predicted to be taken, and a "Not now" mutes that goal as long as the
   recovery posterior says, with no quota and no fixed mute length.
4. **The ceiling** (`keep`, 3): a draw it binds shows no card and is logged with `ceiling.bound` (deterministic
   propensity of the arm; the row's propensity is the drawn target's `π`). Since the card is drawn at most once a day
   (§19), it binds only if the owner sets it to 0 or the
   one-a-day rule is relaxed: see ruling 2.
5. **Responses.** `accepted` / `chose_alternative` (with the candidate) / `declined`, once per decision (the same
   response again is idempotent; another is refused). A Start records the lesson id first, so the lesson row and
   the response name each other. If the opening then fails before the lesson is saved (the teacher's client
   unavailable) or the app stops in between, the day's card offers that one lesson again (`pending_lesson`, "Open
   the lesson") under the recorded id, and the lesson screen repeats the idempotent open: it resumes only on the
   sidecar's own saved-lesson id (Codex review F2). A card left unanswered is recorded `ignored` by the next day's
   first suggestion step. The day's responses in the router card's 7-day window are preference lines on the
   learner-state card ("not now on X", section `lesson_suggestions`, card version `+te1b` while present; Codex
   review F5).
6. **The outcome** (§15.1's "lesson value on R_cold", logged for the router's 200-decision DR estimate, no switch
   claimed): per suggestion decision, shown or not, the first eligible cold retrieval on the drawn LO at least a
   day after both the decision and the last exposure (a lesson's reveal rows are exposures), `S = R_cold`,
   `action_status` the learner's response (`taken` / `not_taken` / `open`; `not_applicable` with no card). The
   detail also records `R_cold` on every LO of the predeclared scope, marking the one the learner took, so an
   accepted alternative's delayed check reaches its decision without replacing the ITT target (Codex review F4).
   A suggestion decision never supersedes a plan block's outcome.
7. **The kill switch.** Off (`router.lesson_suggestions.enabled`, or `router.enabled`, `router.log_decisions` or
   `teacher.enabled` off), or below the tag: `lesson.suggestion` returns `null` and writes nothing (every table
   byte-identical, tested), `lesson.suggestion_respond` refuses, the UI config has no `teacher.suggestions` and
   Today never asks for the card. With it on, the plan's own payload is still byte-identical (the card is its
   own RPC; tested by reading the plan at TE1's tag and at TE1b's after a draw).

## Rulings wanted (deviations from the spec text)

1. **The models are not asked about lesson candidates.** §15.1 says the candidate "joins the `mixture`
   draw … or `epsilon_tiebreak` in `staged` mode". Since the codex re-review (F5) the target IS drawn that way:
   the router's `model_mixture` with the configured weights and floor, or `epsilon_tiebreak` when staged
   (`detail.target`, recomputable with `router.mixture.recompute`). The Decider and the router LLM are not asked
   (their question set `router_qs_v2` is unchanged; no new model call), so their weight goes to the staged rule
   as for any model not set up (G7), recorded `not_asked`. The row's design `lesson_suggestion_draw` names the
   two stages (the router's target draw, then the show coin). Asking the models is a later step behind the
   router's own evaluation.
2. **"At most one a day" (§19) against "no per-day quota, ceiling 3" (§15.1).** Built: one decision a day (the
   §19 rule and the stage brief), and the ceiling enforced and logged, which therefore binds only at 0. If the
   owner wants the model to set the frequency within the day, the receipt key moves to a per-boundary key and
   the ceiling becomes live.
3. **`ignored` is recorded at the next day's first suggestion step**, not at the end of the session (no session
   end is reliably recorded on the desktop: closing the app ends none).
4. **The lesson row keeps TE1's `origin = 'router'`** (migration 234's CHECK; no rebuild of a protected ledger)
   with `origin_ref` = the decision id; the API names the origin `router_suggestion`.
5. ~~The router card's preference line is not built~~: built in the Codex fix round (F5), as an evidence section
   present only with answers in the card's 7-day window, the card version suffixed `+te1b` while present.

## Gate (this step; the full suite runs once, in the landing gate)

Every pytest/vitest/npm/cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G`, pytest at `-n 6`, vitest at `--maxWorkers=4`, one test run at a time.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **41 kept, 0 broken** (a first draft had the shell import the teacher; the
  teacher reads are now inlined, pinned equal to `teacher.service.lessons_active` and `teacher.brief.lo_prediction`).
- Targeted pytest, migration and head-fixture set (97 files: every test naming `migration_head_236`,
  `discover_migrations` or `apply_migrations`, plus `tests/test_teacher_te1_successor.py`): **1400 passed, 7
  skipped, 5 failed**; the five were stale version pins (method-explicit, plan-follows-path, mvp018's bare upgrade,
  TE1's chain position and its installed-completion check), fixed and rerun in the wide set below.
- Targeted pytest, wide set (149 files: the TE1b and TE1 files, every file naming the router outcomes, the router
  store or its designs, `config_dto`, `RouterConfig`, `activation_journal`, the parameter registry, the defaults
  snapshots, `SUCCESSOR_CHAIN`/`LATEST_ALGORITHM_VERSION`, `table_roles`, the lesson handler or the teacher service,
  and the contract files: desktop RPC contract, mobile allowlist, architecture, coordinated migrations, tracked
  fixture databases, registry audit, CLI help snapshot, serializer snapshot, public-tip guards, sqlite file copies):
  **2711 passed, 12 skipped, 6 xfailed, 4 failed**; the four (three chain-position pins and the architecture
  test's SQL-owner registry, which now names `db/stores/router_suggestions.py`) fixed; rerun of those files with
  the TE1b files and the mobile allowlist: **434 passed**.
- Durability: `-m durability` over the 97-file migration set: **71 passed**; the TE1b files with
  `--durable-sqlite`: **31 passed**.
- Frontend: `npm install` ok; `npm run typecheck` ok; vitest on the touched files
  (`src/screens/today/LessonSuggestionCard.test.tsx`, `src/screens/TodayScreen.suggestion.test.tsx`,
  `src/app/lessonsConfig.test.ts`, `src/screens/LessonScreen.test.tsx`, `src/screens/TodayScreen.plan.test.tsx`,
  `src/app/App.today.test.tsx`): **6 files, 51 passed**; `src/copy` and `src/app` (the jargon deny-list and the
  shell): **29 files, 270 passed**; `npm run frontend:build` ok.
- `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml`: ok.
- References: `db_generate_reference.py` then `db_validate_reference.py`: **errors []** (prose counts moved to 370
  tables / 1121 leaves); `desktop_generate.py` then `desktop_validate.py`: **passed** (308 TS, ACTIVE 314); the
  CLI help snapshot rewritten (`upgrade --to`'s help).
- Head fixture: a backup-API copy of main's `migration_head_234` under `fixtures-local/te1b-head/`, only 236
  applied under `UPGRADE_SCRATCH_COPY`; `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header 1/1,
  `integrity_check` ok, `foreign_key_check` empty; copied into place with the backup API, no companion files.

**TE1b test files (for the landing gate):** `tests/test_teacher_te1b_suggestions.py` (the card once a day, the
logged draw and its exact propensities, a no-card day logged, no candidate writes nothing, the candidate reasons,
responses logged once and idempotent, `ignored` the next day, responses moving the model, "Not now" muting per the
recovery prior, the seeded priors, re-acceptance teaching the grid, Start opening a lesson with the decision as
origin and resuming on a second Start, the receipt's origin, the ITT outcome, off/below-tag/router-off/lessons-off
writing nothing, the desktop config, the plan byte-identical with a draw, the chain, the upgrade and its refusals,
the installed completion, the defaults parity, the ceiling bind, the parity with the teacher's reads; a socket guard
on the flows: no network) and `tests/test_teacher_te1b_migration.py`; frontend
`src/screens/today/LessonSuggestionCard.test.tsx`, `src/screens/TodayScreen.suggestion.test.tsx`,
`src/app/lessonsConfig.test.ts`. Changed existing tests: the 56 head-path/chain-pin files, the 15 migration tests
composing `TE1_AND_TE1B_*`, `tests/test_teacher_te1_successor.py`, `tests/test_recurrence_commands.py`,
`tests/test_mobile_allowlist.py`, `tests/test_architecture.py`, `tests/cli_help_snapshot.json`.

## Owner items

- Look at the card's copy and the seeded behaviour on a `fixtures-local` copy (no paid call is needed: the card
  and the draw make none; Start then runs a real lesson, which is TE1's owner checkpoint).
- Rulings 1-5 above. The seeds (0.9 / 0.01 / the 7-day grid) are revision 3's defaults; the owner may override.

## Open items

- The router report (`learnloop router report`) does not yet print the suggestion decisions' ITT split; the rows
  and outcomes are logged for it.
- At the landing: renumber the tag after follow-ups Nov 2's mvp-0.42 (`PREDECESSOR` and the chain), migration 236
  if taken, and rebuild `migration_head_236` from main's head; the composed migration-test sets read
  `TE1_AND_TE1B_*` from `tests/test_teacher_te1b_migration.py`.

## Landing onto main

**Base and tip.** Landed onto main `f9bc4254b3` (follow-ups Nov 2) in `learnanything-astrafix`, branch
`teacher/te1b-router-suggestions`. Three commits on top of `8bd1b78ec3`: the R2 fix (`6e6bd6afe6`), a merge of main
`de9a03763d` (`7d4e37644a`), and a merge of main `f9bc4254b3` with the R4 renumber (`cb0811c9ca`). Main is an
ancestor of the tip. No paid or live model call was made. Every Python or CLI run went under `env -i` with an
empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No owner vault was opened, and no GUI was launched.

### Merges and conflicts

- **Main `de9a03763d` (RW5d P4b, the teacher's visuals; no migration, no successor).**
  - `config/template.py`: every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry conflicted. Both sides' comments were kept.
  - The lesson handler's docstring: both paragraphs were kept.
  - Every other file merged without conflict.
  - TE1b's frozen main snapshot values moved to that main's values.
- **Main `f9bc4254b3` (follow-ups Nov 2: help-fold successor `mvp-0.42`, migration 235).**
  - **Head fixture.** Both sides had renamed `migration_head_234`: main to `migration_head_235`, this branch to
    `migration_head_236`. Resolved to a single `migration_head_236`: main's 235 companion files, byte-identical,
    plus `state.sqlite` rebuilt as below.
  - **Successor.** The successor wiring conflicted in `algorithm_versions.py`, `activation_journal.py`,
    `cli/app.py`, `cli/runtime.py`, `learnloop_sidecar/context.py` and `pyproject.toml`. Both links were kept.
  - **Tests.** About 60 test files conflicted on chain, version-set and head pins. Resolved to the merged chain and
    the 236 head, with both sides' comments kept.
  - **Generated references.** Main's side, then regenerated.
  - **CLI help snapshot.** Regenerated.

### Successor and migration (ruling R4)

- **Tag.** TE1b is `mvp-0.43`. `lesson_suggestions_upgrade.PREDECESSOR` is now
  `HELP_FOLD_ATTACH_ALGORITHM_VERSION` (`mvp-0.42`). Its chained upgrade and its completion are
  `help_fold_attach_upgrade`'s, and that link hands earlier journals on to TE1's.
- **Chain.** The chain ends `… mvp-0.41, mvp-0.42, mvp-0.43`.
- **Where both links are named.**
  - the activation journal;
  - `learnloop upgrade --to`'s help;
  - the CLI's and the sidecar's installed completion (TE1b's, the chain's latest).
- **Tests moved.**
  - Every version set and chain pin.
  - Follow-ups Nov 2's own pins: its versions now include `mvp-0.43`, and its bare-upgrade test now uses `--to`,
    because the bare upgrade targets `mvp-0.43`.
  - TE1b's tests: "below the tag" is now `mvp-0.42`, and the upgrade is tested from `mvp-0.42` directly and from
    TE1's `mvp-0.41` through the chain.
- **Migration** stays 236 (235 is follow-ups Nov 2's). P5 takes 237.
- **Head fixture rebuild.** `migration_head_236` was rebuilt from main's tracked `migration_head_235/state.sqlite`:
  - a backup-API copy under `fixtures-local/landing-te1b-head/`;
  - only 236 applied, under `UPGRADE_SCRATCH_COPY`;
  - `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE` (header 1/1), `integrity_check` ok,
    `foreign_key_check` empty;
  - copied into place with the backup API, with no companion files.

  Its README has a TE1b section. The 5 hard-coded paths, `SCHEMA_HEAD` and the composed migration lists moved to
  236.
- **Config.** Every fingerprint was recomputed with `defaults_fingerprint_for_version` after clearing `.pyc`:
  34 changed, and a second pass changed 0.
- **References.** `db_generate_reference.py` (370 table notes; prose counts moved to 370 tables and 1123 config
  leaves). `db_validate_reference.py`: errors `[]`. `validate_vault.py`: passed (1390 notes). `desktop_generate.py`
  and `desktop_validate.py`: passed. `module_validate.py`: passed.

### The R2 fix (codex verify F8)

- **Validate before offering.** A Start whose lesson never opened (a reservation) is now checked against the
  current vault before it is offered again, whether it is from an earlier day or today
  (`daily_plan.lesson_suggestion.reservation_problem`):
  - every reserved LO must still be in the vault;
  - the exam material must be readable (`teacher.brief.protection_state` is not None; read without importing the
    teacher, and a test pins the two equal).

  Those are exactly what the lesson's opening refuses on before any teacher call. An LO has no protection status
  of its own, so "not protected" means the exam material can be checked.
- **Set aside.** A reservation that can no longer open gets an `expired` row on its decision, with the reason and
  the reservation's lesson id. Nothing is deleted, and the Start stays recorded. For an earlier day's
  reservation, the day then draws normally. For today's own, the day shows no card, because there is one decision
  a day.
- **"Not now" on the pending card.** It calls `lesson.suggestion_respond` with `response = "released"`. That
  releases the reservation; its LOs count as declined for the decline recovery; it is not an acceptance
  observation. The outcome ledger still reads the Start.
- **Lesson refusal.** A released or expired reservation's lesson refuses to open (`not_found`).
- **Ledger.** Migration 236 (not yet on main) allows `released` and `expired`. Its UNIQUE on `decision_id` became
  two partial UNIQUE indexes: one learner response per decision, and at most one release per decision.
  `responses()`, `response_for()` and the router outcomes' query read the learner's response only.
- **Tests.**
  - Reproduce-first: `tests/test_teacher_te1b_landing_r2.py` failed 8 of its 9 tests on the pre-fix tree and passes
    on the fix. The ninth checks that a valid reservation is still offered, so it passes either way.
  - The migration test covers the release indexes.
  - Vitest: the pending card shows "Open the lesson" and "Not now"; "Not now" releases; a failed release keeps
    the card.

### Gate

Each command ran in its own memory-capped scope. The full suite ran under `flock` in a 10G scope; everything else
ran in 5G scopes.

| Check | Result |
|---|---|
| `lint-imports --no-cache` | 42 kept, 0 broken |
| Full pytest (`-n 8 --dist worksteal`) | 23944 passed, 90 skipped, 47 xfailed, **0 failed** (42:48) |
| Durability lane (`-m durability`) | 187 passed, 1 skipped |
| Owner lane on fresh backup-API copies of `owner-copies-mvp035` (`fixtures-local/landing-te1b/owner-lane`) | 83 passed, 4 skipped, 2 failed: the two known failures (`test_activity_backfill…duration`, `placement_fixture_copies[arxiv_v2]`) |
| `npm install`, `npm run typecheck` | ok |
| Whole vitest (`--maxWorkers=4`) | 2468 passed, 1 failed (see below) |
| `npm run frontend:build` | ok |
| `cargo check` | ok |

**The one vitest failure.** It was not the known sketch-sandbox flake. It was
`src/screens/reader/sideBySideCorrespondence.test.tsx` "(iv) peek, side by side and go there each record once"
(1019 ms, one assertion). It ran while the smoke was loading the machine. Alone it passed 3 times out of 3. It is
Reader code that TE1b does not touch: a timing flake under load.

**Targeted runs before the gate.**

- After the first merge: 138 files, 2272 passed.
- After the second merge: 162 files, 2647 passed and 16 failed. The 16 were stale chain and version pins (negative
  chain indexes, version sets missing `mvp-0.42`, follow-ups Nov 2's own pins, its head test). All were fixed and
  rerun green.
- Targeted vitest (LessonSuggestionCard, TodayScreen.suggestion, TodayScreen.plan, App.today, App.lessonSuggestion,
  LessonScreen, lessonsConfig): 63 passed.

### Smoke on fresh owner copies

Setup (`fixtures-local/landing-te1b-smoke/`, driver `scripts/smoke.sh`, rerun part `scripts/rerun_la.sh`):

- **Copies and routes.** Fresh backup-API copies of the three mvp035 owner copies. Each was neutralized under its
  own side's code: every AI route at the `127.0.0.1:9` blackhole with the key variable unset.
- **Environment.** `env -i` with an empty `HOME`, `CODEX_HOME` and config.
- **Audit hook.** It logs every process start and every socket connect, and refuses non-loopback sockets and any
  Codex start. A self-test confirmed it logs a loopback connect, refuses `192.0.2.1` and refuses a `codex` start.
- **Code.** `git archive` of main `f9bc4254b3` and of the branch `cb0811c9ca`, each with `src/` and `migrations/`.
- **Copies prepared.**
  - `m`: main code, bare upgrade, mvp-0.35 → mvp-0.42 (head 235).
  - `b42`: branch code, `--to mvp-0.42`, head 236.
  - `b`: `b42` then a bare upgrade, mvp-0.42 → mvp-0.43.
  - `boff`: `b` with `router.lesson_suggestions.enabled = false`.
  - `bs`: `b`, with the day's suggestion drawn before the plan.

  Each copy had its primary desktop load, `migrate_vault` and `rebuild-derived-state`.

**Plan and Today parity.**

| Check | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Today: b42, boff, b and bs vs main | byte-identical (525266 B) | byte-identical (740827 B) | byte-identical (344204 B) |
| Plan dump at mvp-0.42, b42 vs main | byte-identical (84736 B) | byte-identical (124061 B) | byte-identical (32473 B) |
| Plan dump at mvp-0.43, suggestions on (b) vs off (boff) | byte-identical | byte-identical | byte-identical |
| Plan dump, boff vs main | 14 differing leaves, all the version label (see below) | 20, same | 14, same |
| Plan dump with the day's suggestion drawn first (bs) vs b | payload byte-identical; only id-bearing hashes differ (see below) | byte-identical | byte-identical |

- **boff vs main.** Every differing leaf is one of these:
  - the version string (`algorithmVersion` in the four plan payloads, `algorithm_version` on the decision rows,
    and in probability the three `ad_selections` rows' `algorithm_version` and `versions_json`);
  - JSON that embeds that string (the router card's `content_json`, the decision's `detail_json`);
  - the hashes computed over it (`card_hash`, `snapshot_hash`, `content_hash`).

  With main's `mvp-0.42` read as `mvp-0.43` and those hashes dropped, the dumps are identical (`plan_norm.py`) on all
  three copies. At the same tag, suggestions on and off are byte-identical. So with suggestions off, the plan
  differs from main's only by being at the new tag.
- **bs vs b on linear_algebra.** The plan payloads (`read`, `serve1`, `serve2`, `read2`) are byte-identical. The
  differences are confined to the plan-block decision's `card_hash`, `snapshot_hash` and payload `content_hash`,
  and the `lesson_suggestion` decision count (0 vs 1). The cause is the deterministic id generator: drawing the
  suggestion first consumed ids. So the plan's block ids differ in the raw text that is hashed, though they map to
  the same placeholders (`hash_norm.py`: identical without those hashes).

**`lesson.suggestion` on each copy at mvp-0.43** (sidecar handlers in process, frozen clock):

- **linear_algebra** (4 candidates):
  - **The draw.** Day 0: one `lesson_suggestion` decision with an exact propensity (0.809) and a card. Day 1: one
    decision (0.555), and day 0's shown, unanswered card recorded as `ignored`.
  - **A second call the same day** wrote nothing and returned the same card.
  - **"Not now"** recorded one `declined` row, and no card that day afterwards.
  - **Start.** It recorded an `accepted` row with its lesson id, before the teacher was called. `lesson.turn` open
    was refused with `plan_unavailable` (routes blackholed). No lesson row and no turn were written, and the
    response was kept. The pending card then showed; its "Not now" recorded `released`, and no card afterwards.
  - **Model calls:** 0 receipts in every mode.
- **probability and arxiv_v2:** no candidate (no active goal, no failing cold pair, no below-band LO). Nothing was
  written on any day, and both calls agreed.
- **`rebuild --shadow`** on b, boff and every suggestion copy, in all three vaults: facet 0, mastery 0, schedule 0,
  live database unchanged.
- **Receipts:** 26 databases compared with `base/`: **0 new `model_call_receipts`**.
- **Audit:** no process start and no socket connect at all (the audit log was never created), so no non-loopback
  socket and no Codex process.

The smoke driver first crashed in the decline and Start modes on linear_algebra. The handler returns camelCase
keys and the driver read snake_case. That was a driver bug, not a TE1b one. Those two modes were rerun on fresh
copies with the fixed driver (`rerun_la.sh`), with the results above.

### Rulings (verbatim)

- **R1 (F5):** "Accepted for v1: lesson candidates are drawn by the router's model_mixture with the Decider and router LLM recorded as not_asked and their weight moved to the staged rule, with the epsilon floor and exact logged propensities. Asking those models about lesson candidates needs a new question set and new model calls each day; that is a follow-up once lesson suggestions have data, not a landing blocker. Document in the spec's as-built note that model weights do not yet influence lesson selection."
- **R2 (F8):** "Fix at landing: validate a recovered reservation against current vault content (LO present, openable, not protected) before returning it; an invalid one is set aside (recorded in the response ledger as expired/invalid, nothing deleted) and the day draws normally; give the pending card a 'Not now' that releases the reservation. Regression tests for both. No further review round."
- **R3:** "One card a day (spec §19) is kept; ceiling_per_day stays as a logged guard. 'ignored' is recorded at the next day's first suggestion step. The lessons row keeps migration 234's origin='router' with origin_ref = the decision id. All accepted as built."
- **R4:** "Successor renumber: followups-nov2 lands first with mvp-0.42 <- mvp-0.41 and migration 235; TE1b becomes mvp-0.43 <- mvp-0.42 and migration 236 (or the next free numbers if main has moved further)."

The spec's as-built note (`docs/specs/spec_teacher_v1.md` §20, TE1b) records R1 ("the models' weights do not yet
influence lesson selection"), R2 and R3.

### Owner items

- **The card on a copy.** Check the card's copy and the seeded behaviour on a `fixtures-local` copy. Neither the
  card nor the draw makes a model call. On the owner copies only linear_algebra has candidates today.
- **Start.** Start runs a real lesson, which is TE1's owner checkpoint: it needs one ChatGPT-plan call and the
  owner's go-ahead.
- **Working vaults.** Upgrade them to `mvp-0.43` through the chain: back up, run `learnloop upgrade`, then
  `rebuild-derived-state`.

### Open items

- **The models and lesson candidates.** The models are not yet asked about lesson candidates (R1). That needs a
  new question set and daily model calls; it comes once suggestions have data.
- **The "not now on X" preference line** on the router card needs review. A pending card's "Not now" (`released`)
  is not yet shown in it, because the card reads learner responses only.
- **The router report** (`learnloop router report`) does not yet print the suggestion decisions' intention-to-treat
  split.
- **Expiry on unreadable exam material.** R2 sets a reservation aside when the exam material cannot be read, which
  may be a passing failure. Fail-closed was chosen so suggestions are never blocked indefinitely; "Teach me" still
  opens the lesson.
- **Copy carried over from TE1.** `lesson.turn` open refused with `plan_unavailable` says "your lesson is saved"
  though no lesson row exists (seen again in the smoke).
