# Reader workbench RW7a: reading paths in the Guide, display only (stage `reader-rw7a`)

Branch `reader/rw7a` (worktree `learnanything-rw4b`), base `main` at
`a76c8358a` (the RW4e landing; migration head 215; AD1, RW2b+H3, RW1c, RW4b,
DL2 (successor mvp-0.29), RW3b, RW4d and RW4e on main). Spec:
`docs/specs/spec_reader_workbench_v1.md` §1's RW7a line and §10.1 in full,
§11 (`reader_path_sections`, `[reading_paths]`, route `reading_path_judge`,
ledger task `reading_path_role`), §12's row (display, no successor), §14 G47
(RW7a's part), §15's reading-path measures, §18's DL2 note ("DL2's depth
intents map onto RW7a's depth choice as one setting"). UX
`docs/specs/ux_reader_workbench_v1.md` §4.11 (the path card, role chips,
"why", overrides), §2 Moment 0, wireframe W1, §4.0 (the seven states of a
model-backed action).

## 0. Plan (written before the code)

**Scope.** RW7a only: per source and depth, the Guide's *your path* card
shows each section as core, prerequisite, enrichment, already shown or
assumed, each with a one-line why and *read it anyway* / *skip it*; one
exercise worth trying per core section; the suggested next activity line;
the goal it serves (named, never created). Not here: RW7b (the plan following
the path; `reading_paths.plan_uses_path` is RW7b's key and is not added), the
sources spec's searched exercise candidates (below).

**Display only (G47, orchestrator note 1).** Nothing in the plan, evidence,
mastery, scheduling, projection or serving reads RW7a's tables. With RW7a on
and paths, depths and overrides stored, `get_daily_plan` and
`get_today_queue` answer the bytes a golden recorded on `a76c8358a` holds
(test). An override or *skip it* writes one `judgment_ledger` `learner_card`
row and one `reader_path_sections` row, nothing else (table diff test).
*Skip it* marks nothing as known.

**Data: migration 217** (AD2+AD3 holds 214, RW5a 216; the runner is
set-based). Two WORKFLOW tables, append-only by trigger, never replayed:
- `reader_path_sections` (the spec's columns): `id`, `extraction_id`,
  `depth`, `section_id`, `label`, `reason`, `exercise_span_id`,
  `learner_override` (`read_anyway` | `skip` | `none` = cleared; NULL on a
  judge row), `ledger_id`, `state_key`, `model`, `prompt_version`,
  `created_at`. A judge row per (extraction, depth, state_key, section),
  unique among judge rows (a partial unique index: a second process judging
  the same state writes nothing); an override row per learner press, the
  newest per (extraction, depth, section) standing across re-judgments
  ("is kept").
- `reader_path_depths`: the Guide's depth choice per source (`id`,
  `source_id`, `depth`, `created_at`), the newest standing. Orchestrator note
  7 allows "its own per-source row"; a depth is a source's, not a
  section's, so it is not folded into `reader_path_sections`.

**Depth and DL2: one setting, display-level mapping only (note 7).** The
Guide never writes DL2's tables. The depth shown is the newer of (a) the
Guide's own choice for the source and (b) DL2's intent-control choice on the
source scope (its own commitment for `{"kind": "source", "id": source}` or
for one of the source's readings), mapped Master -> fluency, Learn -> learn
to use it, Keep and Light touch -> get the idea; Check once, Reference,
Pause, Let go and no setting map to nothing. Neither exists: the Guide asks
once ("How deep do you want to go?") and makes no call until answered. So the
two read as one setting (whichever the learner set last governs the path),
while DL2's stored intent and everything it serves stay exactly
`a76c8358a`'s (test: a depth change leaves `commitments` and
`commitment_versions` untouched). Chosen because writing DL2 from the Guide
would change what DL2 serves (a serving change, F3) and DL2's control
already owns the source scope's commitments.

**Labels: one call per source and depth** (route `reading_path_judge`, a
chat task registered like the other Reader routes: `AITask`,
`ROUTE_FOR_OPERATION`, `ai.routing.reading_path_judge`, a disclosure). The
prompt carries only what the spec lists: the section list (labels, in book
order), each section's roles (ingest `role_hint` plus RW4e's visible
proposals through `source_roles.best_roles`), the linked LOs' titles and the
learner's status on each (demonstrated / assumed / learning / new), the depth
and the goal's title. No passage text, no learner free text. Withheld
sections (`exam_material(...).withheld`, held-out included) are never sent;
a reading that is exam material whole has no path. Spend: metered routes are
held to `reading_paths.max_daily_cost_usd` (0.50, a new key: the spec names
none but the orchestrator requires a cap) at
`source_retrieval.llm_price_per_million`, checked before the call (refused
when unpriced or used up); Codex is `estimated_only`.
`LEARNLOOP_READING_PATH_MODELS=off` in the suite.

**Honest labels in code after the model (G47, note 2).** `already_shown`
stands only when the section teaches at least one LO and every LO it
teaches is demonstrated (`lo_certification(...).demonstrated`); `assumed`
only when every LO is demonstrated or has an open `assumption_decisions` row
(`placement.state.load_placement_state(...).open_by_lo`) and at least one is
assumed; otherwise the label becomes `core` with a code-written reason. The
same rule runs again at display against the statuses of that moment.

**Cache and re-judging.** `state_key` = hash(prompt version, depth, the
sendable section list's hash, every linked LO's status, the goal id). Guide
open with a fresh path: no call. A changed depth, section list or LO status
gives a new key and one new call; an older path is shown meanwhile (labels
re-checked for honesty) and marked as being updated.

**Ledger.** One `llm` verdict per section (task `reading_path_role`, left
`reading_path` = `<extraction>:<depth>`, right `reader_section` = section id,
input hash = state key; the rationale keeps the model's label, the shown
label and whether code changed it). An override is a `learner_card` verdict
on the same question.

**Exercise worth trying.** For each core section, the first exercise region
(`content.sources.exercise_statements.exercise_regions`) whose lead block is
in the section and whose statement the one statement reader
(`read_exercise_statement`, fail closed on exam and held-out material) still
reads. Stored as `exercise_span_id`; re-read at display (a region held out
since is not named). *Try it* opens it in the workbench through RW4b's
fallback path (`workbench.open` with the Reader's `import_request`,
`work_through`, the book shown). **Deviation:** the sources spec's searched
candidate (`instructional.exercises.exercise_candidates`) is not used: it is
a search with paid steps (query embedding, rewrite) and has no
section-to-exercise mapping; `learnloop.reader` cannot import
`learnloop.instructional` either (the import contract). Recorded as an open
question.

**Suggested next activity, no model.** The first core or prerequisite
section in book order (a *read it anyway* counts as core; a *skip it*
leaves it out) not completed (`reader_section_progress`), with, at *learn to
use it* and *fluency*, its exercise: "Next: read §5.4 Mixtures, then try
Exercise 5.14 · about 6 min of reading" (reading minutes from the section's
words at 200 a minute).

**Sidecar** (`learnloop_sidecar/handlers/reading_paths.py`, desktop only):
`reader.reading_path` (the view; starts the judge in the background when the
depth is known and the cached path is not fresh; the Reader polls),
`reader.reading_path_set_depth`, `reader.reading_path_override`. Every one
refuses `reading_paths_disabled` while off. `reader.prompt_contract` gains
`reading_paths` only while on. RW1b's palette gains Orient's *what matters
here?* (effect `reading_path`, opens the Guide's path; needs
`reading_paths`), absent while off.

**Frontend.** New `screens/reader/ReadingPathCard.tsx` and `readingPath.ts`;
`GuideRail` gains an optional `path` node shown in place of the goal card
(absent: today's Guide); `ReaderScreen` passes it while the contract has
`readingPaths`, and handles the `reading_path` effect.

**Config.** `[reading_paths] enabled = true`, `max_daily_cost_usd = 0.5`;
`ai.routing.reading_path_judge` (empty = the active provider). Modelled
defaults, classified in the parameter registry, every defaults snapshot
recomputed with a "no scoring, scheduling, projection or serving change"
note. **Successor:** none.

**Tests planned** (fakes only): `tests/test_reading_paths.py` (honest labels
for each label, the display-only plan/Today golden from `a76c8358a`, the
override and skip table diffs, the cache key and each re-judge trigger, no
call on a fresh path or while off, the spend cap before the call, the
exercise pick and exam exercises never named, the suggested next line
without a model, depth memory and the DL2 mapping with DL2's rows
unchanged, withheld sections never sent and stored rows withheld later not
shown, the ledger rows); `tests/test_reading_paths_switch_off.py` (guide
plan, prompt contract and palette pinned to `a76c8358a` with the switch
off); table roles, migration and head fixture tests; the mobile allowlist pin;
the parameter registry; vitest `ReadingPathCard.test.tsx` and a GuideRail pin.
Plus the RW4e role-reader, RW4d source-object and RW4b exercise pins in
every gate.
