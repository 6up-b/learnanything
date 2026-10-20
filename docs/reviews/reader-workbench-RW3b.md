# Reader workbench RW3b: discovered cues (stage `reader-rw3b`)

Branch `reader/rw3b` (worktree `learnanything-merge4`), base `main` at
`c9ad9cce1` (RW1c landed; migration head 213). Spec:
`docs/specs/spec_reader_workbench_v1.md` §1's RW3b line, §6 in full (§6.1
kinds and restraint, §6.2 "RW3b: discovered links" items 1-6, §6.3 data,
§6.4 routes, §6.5 switches), §5.2's in-session updates, §7.9 (roles: positive
use only, G44), §11, §13, G13-G16, G42, G44, the §14 RW3b test lists and the
§15 cue metrics. Presentation: `docs/specs/ux_reader_workbench_v1.md` §3.4
(the legend: `◌┆`, `●┆`, `▹┆`), §4.3 (the next-step fold `▹┆` opens), §4.4.
Friction notes read: RW3a (notes 3, 5, 7), RW1b §9 item 4, RW1c §8 item 2,
RW2a note 6, RW4a §9 item 4.

## 0. Plan (written before the code)

**What exists.** RW3a draws the Guide's own `recent_misunderstanding`
passages as `◌┆` marks (`reader/reader_cues.py`, `screens/reader/cues.ts`,
`useReaderCues.ts`, `MarginMark.tsx`), within the learner's density budget,
one per screenful, never on the restored passage or while skimming. Taps are
salience-only events and `learner_card` verdicts on ledger task
`passage_cue`. T6's `search_spans` takes `extra_lists`; the shared
`judge_listwise` gives request identity, the ledger-served cache, one capped
call plus a retry; `corpus.role_proposal_keys` already reads RW4e role
proposals; `corpus.model_reader_withheld` and `exam_material.held_out_material`
are the protection helpers every model context uses.

**Scope (RW3b only).**

1. **Migration 215** (AD2+AD3 holds 214; the runner has no contiguity check,
   so the 213 -> 215 gap is tried first and recorded): `passage_links`
   (WORKFLOW: paid outputs, never re-run on rebuild) and
   `reader_cue_impressions` (RECEIPT, with `suppressed_reason`; append-only
   but for one write-once response, enforced by trigger). Head fixture
   rebuilt to `migration_head_215` with the backup API (rollback mode), its
   README and every hard-coded path updated; references regenerated.
2. **Targets** (`source_retrieval/passage_cues.py`, a pure read of existing
   state, each rendered as its LLM-written statement): durable misconceptions
   on the open source's learning objects (lifecycle active), open probe-episode
   hypotheses (their posterior), named learner-text gaps not undone, and
   demonstrated facets (for "a new application"). Each target has a
   `state_key` (its statement and status); a new or resolved target
   recomputes only its own links.
3. **Shortlist.** `search_spans` over the open source's extraction with the
   target's statement as the query, plus two `extra_lists`: passages with a
   `contrast` or `counterexample` role (RW4e proposals through
   `role_proposal_keys`, and roles RW3b's own judge proposed) on the target's
   learning objects or their `confusables`, and the misconception's
   `correction_source_span_ids`. **Every shortlisted passage passes T6's
   exclusions and held-out filtering before the judge sees it:** the scope
   excludes `teaching_exclusions` and the held-out partition, and the pool is
   filtered again by `model_reader_withheld` (solutions, assessment lanes)
   and `held_out_material` (one shared helper each, no second leak check).
4. **Judge.** One listwise call per target through `judge_listwise` (route
   `passage_cue_judge`, ledger task `passage_cue`, left kind `cue_target`):
   every passage judged `clarifies_distinction` | `new_application` |
   `prerequisite_for` | `try_first` | `none`, at most two picks, each with a
   quote verified in code against the block (`text_canon.canonical`), and
   per passage the instructional `roles` RW4e reads (kept on the link,
   used only positively, G44). `try_first` is kept only on a worked example
   or derivation (`reader_tutor.NEXT_STEP_ROLES`) for an open target; a pick
   whose quote does not verify is dropped, never repaired. Background work:
   Codex by default (`ai.active_provider`, `estimated_only`), caps
   `cues.max_calls_per_source_open` (12) and `cues.max_daily_cost_usd`
   ($0.50 metered, the shared daily envelope as RW4a's organizer).
5. **Value order** (`cues.value_order_enabled`): within a section, Guide and
   discovered cues by `p_open` (read from existing state: the episode
   posterior, the misconception's lifecycle, the gap's status, the active
   predictor's P(failure) on the passage's LO for "new application" and
   "try first"), then the judge's pick rank, Guide first on ties; a target
   already shown this visit ranks after every target not yet shown; then the
   density budget. Off: RW3a's order with discovered cues after the Guide's.
6. **Holdout** (`cues.holdout_rate`, 0.1): an eligible discovered cue is
   withheld by a seeded draw (seed derived from the link id, reproducible),
   its propensity logged; Guide cues are never held out; density, spacing
   and restored-line suppressions are recorded with their reason and are not
   holdouts.
7. **Impressions** (`reader_cue_impressions`): one row per (visit, cue): shown
   (when in view), held out, or suppressed with its reason; `p_open` and its
   source, the density, the seed and propensity come from the server's own
   computation, never the client's; the learner's response (`opened`,
   `check_me`, `try_first`, `not_relevant`, `fewer`) is written once.
8. **Kinds and copy** (fixed templates, G16): discovered distinctions `◌┆`
   ("Connects to something you worked on: …"), a new application `●┆` ("A new
   use of something you've shown: …"), try this step first `▹┆` ("Try the
   next step before reading it?"); the "because" line says "found by
   LearnLoop's model, not by a test". "Try this step first" opens RW1b's
   *let me try the next step* at that line (a learner pick, never a gate).
9. **RPCs** (desktop only): `reader.cue_discovery` (starts the background
   job for the open source, answers at once), `reader.cue_discovery_job`,
   `reader.cue_impressions`, `reader.discovered_cue_action`. The guide plan
   merges discovered cues only when `cues.discovery_enabled`; a tap is
   resolved by link id without rebuilding the plan (RW3a friction note 5).
   In-session updates: the Reader asks for discovery again when the plan's
   target fingerprint changes (a new hypothesis or gap), so only the new
   target's links are computed, in the background.
10. **Owner-run** `learnloop reader cues discover --vault --source [--dry-run]`
    (dry run: targets and shortlists, no model call) and the cue funnel in
    `learnloop reader report` (impressions shown vs held out with
    propensities, response rates).

**Switches.** `cues.enabled` (RW3a's), `cues.discovery_enabled`,
`cues.try_first_enabled`, `cues.value_order_enabled`, `cues.one_per_viewport`
(RW3a's), `cues.holdout_rate`. With every RW3b switch off the RW3a cues are
byte-identical to `c9ad9cce1` (pinned in pytest and vitest before any change).

**Never.** Nothing RW3b writes enters evidence, mastery, serving or grading;
"Check me" and "Try this step first" are learner picks. No edit to
`adaptive_difficulty/`, scheduling intent, `daily_plan` or RW4b's exercise
files; `ReaderScreen.tsx` changes are a few wiring lines, the behaviour lives
in `screens/reader/`. No live model call anywhere in this stage.
