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
