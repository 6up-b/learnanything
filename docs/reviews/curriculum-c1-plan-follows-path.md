# Curriculum C1: the plan follows the deliverable

**Stage:** `curriculum-c1-plan-follows-path`, branch `curriculum/c1-plan-follows-path` (worktree `learnanything-ad1`),
base `94494b4cc` (main: mvp-0.38, migration head 228). **Spec:** `docs/specs/spec_deliverable_curriculum_v1.md` §7.6,
§8.1 and the §12 C1 row. **No paid or live call was made**: every model is a fake (`DeliverableFake`,
`PathJudgeFake`, C0a's `CoverageJudgeFake`); every ad-hoc script ran under `env -i` with an empty, existing `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` (`scratchpad/c1/iso.sh`). No owner vault was opened, `~/.config/learnloop`
was not read, and nothing ran against `fixtures/linear_algebra`, `fixtures/probability` or `fixtures/arxiv_v2`.
**A successor**: `mvp-0.39` after `mvp-0.38`. **No migration** (C0's 228 holds every table C1 reads).

## Successor number

RW6b part 1 (`mvp-0.39`, migration 227) had not landed when this stage started (main `94494b4cc` is `mvp-0.38`,
`ls migrations/` ends at 226, 228), so C1 is built as **`mvp-0.39` after `mvp-0.38`**. Whichever of the two lands
second renumbers: the tag is ONE constant (`DELIVERABLE_PLAN_ALGORITHM_VERSION`), the chain is linear, and the
pins below move with it (see "Renumbering at landing").

## What was built

| Piece | Where |
|---|---|
| The tag `DELIVERABLE_PLAN_ALGORITHM_VERSION = "mvp-0.39"`, appended to `SUCCESSOR_CHAIN`; `DELIVERABLE_PLAN_VERSIONS` | `src/learnloop/algorithm_versions.py` |
| The upgrade, per the playbook and the mvp-0.36/0.37/0.38 pattern: accepts mvp-0.38 or mvp-0.9 onwards through the chain, one journalled `BEGIN IMMEDIATE` activation (predecessor's manifest, projection activation as the completion marker, registry refresh, journal, publication last), `complete_interrupted_activation` handing an earlier link's journal down the chain | `src/learnloop/deliverable_plan_upgrade.py` |
| `learnloop upgrade --to mvp-0.39`, the bare upgrade's target (the latest), the help text; the CLI's and the sidecar's installed completion is now this link's; the activation journal's docstring; the frozen-source-modules list | `cli/app.py`, `cli/runtime.py`, `learnloop_sidecar/context.py`, `activation_journal.py`, `pyproject.toml` |
| Kill switch `[curriculum] plan_uses_path` (default true), classified (`structural`, `operational`) in the parameter registry; every defaults snapshot mvp-0.9 … mvp-0.38 recomputed (the key is present and inert below the tag) and mvp-0.39 recorded | `config/schema.py`, `params/parameter_registry.py`, `config/template.py` |
| The gate `engine.deliverable_plan_active(vault)`: the tag, `curriculum.enabled`, `curriculum.plan_uses_path` **and RW7b's gate** (`reading_paths.enabled`, `reading_paths.plan_uses_path`) | `daily_plan/engine.py` |
| `_reading_on_path` gains its first branch: RW7b's own body is now `_reading_on_book_path` (unchanged), and with C1 active `_reading_on_deliverable` reads the deliverable the plan follows and walks its path in order | `daily_plan/engine.py` |
| Which deliverable: `plan_deliverable` walks `nearest_deliverables` (the active deliverables in the existing nearest-goal rule's order: nearest due date, then higher priority, then id) and follows the first whose path is fresh (or withheld) | `source_retrieval/deliverable_path.py` |
| `deliverable_plan_path(vault, repository, goal)`: RW7b's `plan_path`'s sibling. The lines are the Guide's own (`effective_lines`) from the judge's rows **for the learner's current state key**; `stale` (judged only for an older state), `withheld` (protection unreadable: followed, plans nothing), `unreadable` (recorded, RW7b decides), `no_scope` / `no_depth` / `not_judged` (not in play). Never judged here | `source_retrieval/deliverable_path.py` |
| The walk: `next_listed_reading_target(steps, from_furthest, exam, allowed)` takes the planned lines (`core`, `prerequisite`, a *read it anyway*) in the path's order across books, and runs the predecessor's rules first on each candidate: the exam predicate (an exam extraction, a section with an exam span), U4's front-matter rule (with `plan.reading_from_furthest`), DL2's `reading_allowed` per book; a finished section (DL1's rule, now `_unfinished_target`, shared) is passed | `daily_plan/reading.py` |
| Receipt `reading_path_plan_v2` (only where a deliverable path was in play): v1's keys with `predecessor` = **RW7b's choice**, `chosen_by` ∈ `deliverable` / RW7b's `path` / `order`, `deliverable` (goal id, status, depth, `input_state_key`, `judgment.state_key`, every row read with its judge and override row ids, the line chosen, every deliverable consulted) and `rw7b` (RW7b's own v1 receipt, or None) | `daily_plan/engine.py` |
| The switch reaching a built plan: `_reading_path_switched_off` now asks `_path_switch_target` where to go. A v1 receipt behaves exactly as before. A v2 receipt with C1 off and RW7b on goes back to RW7b's choice (transition reason `deliverable_path_off`); with RW7b off too, to the order's (RW7b's own receipt's `predecessor`; `reading_path_off`). The block move (end the unstarted reading block unread, recompute the reading's minutes, re-split) is `_move_plan_reading`, factored out unchanged | `daily_plan/engine.py`, `daily_plan/records.py` |
| The daily quiet re-judgment: `deliverable_path.refresh_for_plan` judges the nearest in-play deliverable whose path is stale, under `plan_fallback.quiet()` (no OpenRouter offer, no grant); the sidecar starts it in the background from every plan RPC (`daily_plan._require` → `handlers/deliverables.refresh_for_plan`), at most once a local day per vault per sidecar process | `source_retrieval/deliverable_path.py`, `learnloop_sidecar/handlers/deliverables.py`, `learnloop_sidecar/handlers/daily_plan.py` |
| Refresh adoption: a plan built on a stale path takes C1's step once a judgment of a stale deliverable is recorded after the build and the path is fresh, while no reading of the plan has started or ended (recorded once, as the receipt's `refreshed`) | `daily_plan/engine.py` (`_deliverable_path_refreshed`) |
| Config reference: the kill switch's description; DB/config reference regenerated | `docs/learnloop-architecture-vault/_scripts/db_generate_reference.py`, the generated notes |
| Spec §7.6 "as built" note | `docs/specs/spec_deliverable_curriculum_v1.md` |

## Decisions taken here (open to the owner or the landing)

1. **C1 sits inside RW7b's gate.** `_reading_on_path` is only called with RW7b active, and the spec places C1 as its
   first branch, so C1 needs `reading_paths.enabled` and `reading_paths.plan_uses_path` too, besides
   `curriculum.enabled` (Q14: the plan never follows a path the learner cannot see; the Guide's slice lives in the
   path card, which shows only with `reading_paths.enabled`) and `curriculum.plan_uses_path`.
2. **"In whichever book" is any book the path names**, not only as-you-read imports (DL1's conservative rule for
   the per-book order). The deliverable is the learner's explicit act naming what to read across books. DL2's
   `reading_allowed` is applied per book, as it is to RW7b's candidate list; exam and held-out material is
   excluded twice (C0a's library never lists it, and the plan's exam predicate runs on each candidate).
3. **A fresh path with nothing left to plan** (every line finished, skipped, already shown, assumed, pending a
   check, or filtered) **leaves RW7b's choice**; the receipt says `status: path` with `step: null`. The deliverable
   leads while it has something to read; the learner's other reading is not blocked once it is done.
4. **A withheld path plans nothing** (fail closed, RW7b's rule): protection could not be read, so no reading.
5. **No deliverable in play leaves RW7b's plan byte for byte** (no v2 receipt), mirroring RW7b's "None when no path
   was in play". A deliverable without a resolution, a depth or any judgment is not in play.
6. **The v2 receipt keeps `rw7b`** (RW7b's own receipt) so that turning C1 off restores RW7b's reading exactly
   and turning both paths off restores the order's. When C1 and RW7b choose the same section, C1 off still moves
   the stored reading to RW7b's own copy (RW7b's `core` label, not C1's `prerequisite`): RW7b's plan exactly.
7. **The daily re-judgment runs in the background and the build never waits.** The sidecar answers one request
   at a time and the plan calls no model, so a synchronous judgment before the build would freeze the app for
   a model call. It starts with the first plan RPC of the day (`get_daily_plan` and every other plan RPC go
   through `_require`), once a local day per vault in a sidecar process (an in-memory marker: a restart may run it
   once more, and a fresh path pays nothing). "Plan route only" is `plan_fallback.quiet()` (no offer, no grant),
   as C0b's on-extract job; an explicitly metered route would still be held to `curriculum.max_daily_cost_usd`.
   The CLI builds plans without it (a CLI build on a stale path follows RW7b and says `stale`).
8. **Refresh adoption (beyond the letter of §7.6).** The path's key holds the days left before the deadline and
   the books read (C0b's learner context), so a deadline deliverable's path is stale at **every** day's build,
   and starting a new book makes it stale too. Without adoption C1 would almost never act for an exam. A plan
   built stale takes the deliverable's step on a later read, once a judgment was recorded after the build (the
   cheap gate `judged_since`) and the path is fresh, while its reading is unstarted; recorded once as
   `refreshed` (not `transition`, so the kill switch still reaches the plan afterwards).
9. **One block reason.** Any path withdrawal ends the block with `reading_path_off` (so
   `PlannedBlock.withdrawn_path_reading` keeps its meaning); the transition's own reason distinguishes
   `deliverable_path_off` and `deliverable_path_refreshed`.
10. **The block's "why" reuses RW7b's words** ("prerequisite on your reading path"): no DTO or frontend change.
11. **The learner context C0b deferred to C1** (RW1c's "that didn't help" rows, kept comparisons, DL1's minute
    estimates) is **already fed to the path judge**: C0b's Codex review fix F11 added all three
    (`deliverable_path.learner_context`: `didnt_help`, `kept`, `minutes_available` from DL1's daily budget times
    the days left, section minutes at `plan.read_words_per_minute`). Nothing to add; C0b's open item is closed.

## Constants

None new. `PLANNED_LABELS` reuses RW7b's; the once-a-day bound is the plan's own day (`engine.local_date`), a
structural cadence from the spec, not a parameter. The only new config key is the boolean kill switch, classified.

## Persisted meaning

A serving change only: which section the reading block opens. Never evidence, FSRS, the projection or replay
(replay never reads a plan's reading). The activation is the idempotent projection rebuild of the same namespace.
`test_a_shadow_rebuild_is_zero_and_never_reads_a_deliverable_path`: live database unchanged, summary
`{mastery: 0, facet: 0, schedule: 0}`, and no deliverable path read.

## Tests (`tests/test_curriculum_c1_plan_follows_path.py`, 37 tests; every model a fake)

Fail-first: with `deliverable_plan_active` forced to False, 21 of the 37 fail (every behaviour test; the G-C4
parity tests through their "on differs" check); the 16 that pass are the upgrade chain, the pure refresh function,
the no-deliverable and head-fixture parities and the shadow rebuild.

- The successor: one constant after mvp-0.38, the latest, defaults snapshots; the switch on by default,
  classified, and off with either curriculum switch, either RW7b switch, the plan off, or below the tag.
- What changes: the reading block opens the path's first unfinished line (a prerequisite in the notes) where RW7b
  opens "Chapter 5"; the receipt v2 (predecessor = RW7b's choice, the rows read, the line chosen); **across books
  in path order** (Lay's 5.2 next, a book the predecessor never reads); nothing left → RW7b's choice; the nearest
  deliverable with a fresh path is followed (a nearer one with no depth passed over and recorded).
- Filters first: the exam predicate (spans and whole extractions), DL2's `reading_allowed` (unit level and a real
  `set_intent` pause through the build), U4's front-matter rule (and not with DL1's order), a section held out
  since the judgment, a withheld path (plans nothing), an unreadable path (RW7b's choice, recorded).
- Stale: not followed, the receipt says `stale` with both keys; the daily refresh is quiet (offers suppressed
  inside the fake), runs before the build when inline, once a day (again the next day); the plan down → RW7b,
  `stale`, nothing relayed; the refresh function judges only a stale path and stops when switched off; refresh
  adoption (recorded once, then the switch still reaches the plan).
- G-C4: off (`plan_uses_path`, `curriculum.enabled`) every plan build is RW7b's byte for byte, the served plan,
  Today and the next item included (with RW7b's own path judged so its v1 receipt is present); no deliverable in
  play → RW7b's; the head fixture copy (`migration_head_228`) on, off and curriculum-off equal the predecessor's;
  turning C1 off after the build → RW7b's reading (`deliverable_path_off`); both paths off → the order's
  (`reading_path_off`, recorded once); the same section → RW7b's own label.
- The upgrade: from mvp-0.9, 0.32, 0.37, 0.38; the bare upgrade; refusal before the chain; an interrupted
  activation completed by the next CLI command, by the sidecar's open and by the upgrade; a failure after the
  rename leaves the predecessor and no journal; an interrupted mvp-0.38 activation then `--to mvp-0.39`; without
  a completion an attach refuses and the upgrade still completes the earlier journal.

## Gate (this step; the full suite runs once at landing)

GATE_PLACEHOLDER

## Renumbering at landing

If RW6b part 1 (`mvp-0.39`) lands first, C1 becomes `mvp-0.40` after it: change the one constant, the upgrade's
`PREDECESSOR` / `_upgrade_to_predecessor` / completion import (RW6b's upgrade module), the CLI branch and help, the
runtime/sidecar completion import, the defaults snapshot key and the recomputed fingerprints (both successors'
keys present in every snapshot), the chain pins in the successor tests (the files edited here, plus RW6b's own),
the CLI help snapshot, the spec's as-built note and this record.

## Open questions

1. Should C1 stand on its own switches, independent of RW7b's `reading_paths.plan_uses_path` (decision 1)?
2. Should the deliverable branch read only as-you-read books, as DL1's order does (decision 2)?
3. Refresh adoption (decision 8) is beyond the spec's letter; the alternative is a synchronous re-judgment before
   the day's first build (blocking the app for one model call). Keep adoption?
4. A path goes stale whenever the learner starts a new book (C0b's key names books read); the daily refresh or a
   Guide open re-judges it. Should "books read" leave the key (a C0b change) so C1 follows longer between days?
5. A CLI-built plan never starts the refresh (decision 7). Acceptable?
