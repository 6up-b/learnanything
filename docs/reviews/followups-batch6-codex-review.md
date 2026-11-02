# Follow-ups batch 6: Codex review fixes

Stage `followups-batch6`, branch `fix/followups-batch6`, worktree `learnanything-dl2`. Review: Codex
(gpt-6.1-sol), job `20261102-144908-iG3wYr`, on `07e3e85f54`. Four findings, all Medium. The stage record
is `docs/reviews/followups-batch6.md`.

**No live or paid call was made.** Every model is a fake. The one ad-hoc run outside pytest (the CLI help
snapshot `--write`) ran under `env -i` with an empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`,
and `LEARNLOOP_FIGURE_PREFETCH=off`. No vault was opened outside pytest's synthetic ones. **No migration, no
schema change, no config key, no successor.**

## Review

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Automatic retries bypass protection for active cold checks | **fixed** | `f76f6fb45d` | `tests/test_followups_batch6_review_fixes.py::test_f1_*` (7 tests; 6 failed before the fix, and the unrelated-check test passed before and after) |
| F2 | Medium | Paced jobs consume retry slots and starve eligible jobs | **fixed** | `f76f6fb45d` | `test_f2_*` (3 tests; all 3 failed before the fix) |
| F3 | Medium | The reported ITT difference conditions on outcome availability | **fixed** (relabelled) | `4fca4f97f3` | `test_f3_*` (2 tests, both failed before the fix); `tests/test_followups_batch6_router_report.py` updated |
| F4 | Medium | G1 changes serving inputs under the existing algorithm tag | **rejected** (successor), ruling wanted; card-version mitigation | `b6799c0b96` | Reason below. `test_f4_*` (1 test, failed before the change) |

### F1: a cold check that starts after the plan wait (fixed)

**Reproduced.** A prebuild's rich job meets the plan's limit. After that, one of the vault's items comes under an
open cold check, and its worked answer is a paragraph of the job's saved context (`input_span_ids`). Before the
fix, three paths ignored the check:
- `retry_plan_waits` requeued the job;
- the Reader's `reader.figures` read requeued it;
- the worker, once requeued, sent the request and stored the figure.

`run_builds` refuses that state for a new build, but none of the retry paths asked the same question.

**Fix.** There is now one core, `service.item_passages(vault, repository, extra_item_ids=())`. It returns the
passages (`corpus.item_exclusions`) of items under a live administration (`WITHHELD_COLD`, `WITHHELD_RESERVED`,
`WITHHELD_PROBE`) plus any extra items. It returns None when protection can't be read, and callers fail closed.
- `prefetch.item_protection` now reads that core, adding the stored plan's open items (`held_plan_item_ids`).
  What it covers is unchanged.
- `service.prefetch_plan_waits`, which serves both the Reader's reads and the pass, drops a job whose saved
  context (`rich_base_keys`: its passage, the paragraphs it was sent, its region, retrieved keys and home)
  touches a protected passage. If protection can't be read, it returns nothing.
- `retry_plan_waits` also passes the stored plan's open items, so it applies the same rule as `run_builds`.
- **The worker** (`rich.run_rich_job`, prebuilds only) checks `_item_protected` at the start and in its
  hold. The hold runs before every request and before the store. A stop is `exam_material`.

**What the worker does not check.** It checks live administrations, not the stored plan's open items.
`figures/prefetch.py` is a composition layer that nothing imports back (`test_figures_prefetch_boundary.py`).
Reading the day plan from `figures.rich` would need a new ignore in the frozen-cycles contract. The plan's
items are still checked at both points where a prebuild can start: `run_builds` and `retry_plan_waits`.

**Tests (fakes).** The cold reservation starts **after** the initial plan failure. Each line below is one test:
- the pass's function asks nothing, and a real pass sends nothing;
- the Reader's read asks nothing;
- a direct requeue is stopped by the worker before any request, and nothing is listed;
- a check that starts while the author writes: the request was already sent, but nothing is stored;
- unreadable protection: no requeue, and the worker sends nothing;
- the stored plan's open items are protected in the pass;
- a cold check on an unrelated passage still lets the retry through.

### F2: paced jobs never take a due job's slot (fixed)

**Reproduced.** With `max_daily_builds = 1`, the newer of two waiting jobs was inside its retry interval. The
old code sliced `waiting[:bound]`, so it tried only the paced newer job and never reached the due older one.

**Fix.** The bound now counts successful requeues. The scan orders jobs by `rich.plan_retry_order`: the last
retry in this process, with never-asked jobs first, and the ledger's newest-first order for ties. It goes on
until `max_daily_builds` requeues succeed. A paced job declines without a request and is passed over. No new
constant.

**Tests.**
- A paced job first in line leaves the slot to the due one, and nothing more is asked once the bound is reached.
- The scan goes past three paced jobs to requeue two due ones.
- A job that keeps meeting the limit yields its slot to a never-asked job on the next pass.

### F3: the R_cold comparison is labelled observed-only (fixed by relabelling)

**Agreed.** Accepted lessons can delay the drawn LO's eligible cold retrieval, so which decisions have an outcome
can depend on the arm. Propensity weighting does not correct that.

**Fix.**
- `itt_difference_r_cold` is now `observed_difference_r_cold`.
- Each arm reports `observed_share`, and the text reads "observed k of n".
- The last line reads: "Difference in mean R_cold among observed outcomes only (card - no card): … Descriptive,
  not an intention-to-treat estimate: an accepted lesson can delay its topic's cold check, so which outcomes are
  in yet can differ by arm."
- The funnel rates stay labelled intention to treat: they are taken over every decision of the arm.
- No causal estimate under censoring is attempted. That would be new analysis, not a follow-up.
- The `router report` help text changed, and `tests/cli_help_snapshot.json` was regenerated (`router`,
  `router report`).

**Tests.**
- Differential availability: the card arm has 1 of 3 observed and the no-card arm 2 of 2. The test checks the
  shares, the observed-only difference of +0.50, and that the text never says "ITT difference".
- The CLI runs on logged decisions with observed cold outcomes for both arms. `derive_router_outcomes` is faked to
  final values, which the earlier CLI test never had. The test checks the JSON key, `+1.00`, and the label.

### F4: G1's card line under the existing tag (rejected; ruling wanted)

**The facts are right.** At mvp-0.43, a pending card's "Not now" adds a line to the router card the plan's models
read, and switching suggestions off removes the whole section rather than restoring the pre-batch6 card.

**Why no successor in this step.** Minting one (mvp-0.44) would mean:
- a new tag and its chain entry;
- a defaults snapshot;
- an upgrade step;
- switch-off parity.

That is a successor stage, not a follow-up fix, and it is out of this step's scope. It also goes against what was
decided before:
- **Earlier rulings.** Router-card inputs have been ruled serving-time, not persisted meaning: TE0's confidence
  section, and RW6b part 2's ruling R1, "router input changes without a successor, and router decisions are
  serving-time and not persisted meaning", flagged to the owner. Follow-ups Nov 1c (E) also changed the card
  without a tag.
- **The playbook's in-place exception path.** An amendment before any vault has reached the tag has precedent
  (mvp-0.11), but it needs an owner decision. No vault reached mvp-0.43 before this branch: the owner's vaults
  are at mvp-0.35, and TE1b landed today.

**Mitigation (`b6799c0b96`).** While the section carries a `released` line, the card's version now takes a
further suffix, `+te1b+released` (`SUGGESTION_RELEASE_CARD_SUFFIX`). A stored card and its decision therefore
name the new input. A card without such a line is still TE1b's: same bytes, same version.
`test_f4_a_card_with_a_released_line_moves_its_version_and_te1bs_card_keeps_its_own` checks both.

**Ruling wanted (orchestrator or owner), one of:**
- (a) accept G1 in place under mvp-0.43, as with TE0 and RW6b P2 R1, recorded as an in-place amendment before
  any vault reached the tag;
- (b) revert G1's card line at the landing, so that the router card at mvp-0.43 is TE1b's byte for byte, and
  carry it to the next successor;
- (c) gate it behind the next successor's tag when one is minted.

### Not findings

- **Spec conformance "F: shared cue density, still missing".** This was recorded open in the stage record (item F:
  two designs, neither small). It is not a finding of this review, and it is unchanged.
- **"No schema, table-role, replayer, grading, evidence-writing or embedding changes"** still holds after these
  fixes.

## Gate

Every pytest command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at
`-n 6` at most, one run at a time. The targeted run was serialized behind
`flock /tmp/learnloop-fullsuite.lock`. Per the owner's rule, the full suite, the whole durability lane and the
whole vitest run were not run.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 42 kept, 0 broken |
| reproduce-first: `pytest tests/test_followups_batch6_review_fixes.py` with `figures/service.py`, `prefetch.py`, `rich.py` and `router/suggestion_report.py` at `07e3e85f54` | 11 failed, 1 passed (the unrelated-check test, which pins behaviour that is kept) |
| reproduce-first F4: `-k f4` with `router/card.py` at the prior commit | 1 failed (import of the new suffix) |
| targeted `uv run pytest -n 6` over the 125 files in `docs/reviews/followups-batch6.targeted-tests.txt` | **2494 passed, 29 skipped, 1 xfailed**, 0 failed (26 min 44 s), at `b6799c0b96` |
| Durability lane, npm/vitest, cargo check, DB reference scripts, desktop catalog | not needed: no migration, DB or connection code, schema, frontend or `src-tauri` change |

**What the 125 files cover:**
- the stage's earlier 116 files;
- this step's `tests/test_followups_batch6_review_fixes.py`;
- every other test file that imports a changed module (git grep for `figures.service`, `figures.prefetch`,
  `figures.rich`, `router.card`, `router_card`, `suggestion_report`, `cli.router`, `prefetch_plan_waits`,
  `retry_plan_wait`): `test_ad23_contract.py`, `test_judge_routes.py`, `test_router_card_reading_gaps.py`,
  `test_teacher_te1_successor.py`, `test_teacher_te1b_migration.py`, `test_teacher_te1b_rereview_fixes.py`,
  `test_teacher_te1b_suggestions.py`;
- the contract tests: architecture, mobile allowlist, desktop RPC contract, serializer snapshot, CLI help
  snapshot, table roles, tracked fixture databases, coordinated migrations, the registry audit, the prefetch
  boundary and the Codex tool lockdown.

## For the landing

- **Unchanged from the stage record:** merge main first (batch 5), then regenerate the module references.
- **`figures/service.py` gains exported names:** `item_passages`, `rich_base_keys`, `rich_base_item_protected`,
  `ITEM_PASSAGE_PROTECTED` and `LIVE_ADMINISTRATION_REASONS`.
- **`figures/rich.py` gains `plan_retry_order`;** `router/card.py` gains `SUGGESTION_RELEASE_CARD_SUFFIX`.
- **F4 needs its ruling** before the landing: (a), (b) or (c) above.
