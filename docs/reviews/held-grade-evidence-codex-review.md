# Codex review of held-grade-evidence: assessed to held transitions

Stage: `held-grade-evidence`, on `merge/proof-alternatives` (worktree
`learnanything-merge`). Reviewed at `aa60d773` (the stage record, docs only
after `dd704cf6`).

Input: an independent Codex review (job `20261013-094441-F9GgvY`, read-only).
It found three defects: one High, two Medium. They share one cause. The stage
tested grades held on their first submission. These three are about an
ASSESSED grade that a later regrade holds:

- **F1.** The regrade left the old assessed rows live.
- **F2.** Certification probe readers kept their verdicts.
- **F3.** Diagnostic observation readers kept their verdicts.

All three reproduced (fail-first, below) and were fixed. None was rejected.
No paid call was made, and no schema, config or frontend file changed.

## Findings

| ID | Severity | Title | Verdict | Commit | Tests (`tests/test_held_grade_evidence.py`) |
|---|---|---|---|---|---|
| F1 | High | Regrading an assessed attempt into a hold leaves evidence that defeats the hold | fixed | `23128d0f` | `test_review_f1_a_regrade_into_a_hold_supersedes_the_assessed_grade_it_replaces`, `test_review_f1_the_ledger_reads_the_evidence_as_the_attempt_step_does` |
| F2 | Medium | Previously scored certification probes remain training labels after being held | fixed | `c3b40700` (export: `145d2bf9`) | `test_review_f2_a_scored_cold_probe_regraded_into_a_hold_abstains` |
| F3 | Medium | Diagnostic boundary labels still interpret held regrades as measured performance | fixed | `611adf5c` | `test_review_f3_diagnostic_observations_held_by_a_regrade_qualify_nothing` |

### F1: a regrade into a hold supersedes the grade it replaces

**Reproduction.** An attempt was validated live (4/4, assessed tier-3 rows).
A blind regrade then held it: the checker returned `cannot_tell` /
`not_established`, the grader gave 0/4, and nothing was located.

- Before the fix, the regrade left four live rows
  (`['result', 'result', 'setup', 'setup']`).
- The predicate's two evaluations disagreed: the ledger said not held, replay
  said held (`(False, True)`).
- The failure streak, the FSRS fitter and the dataset's `R_next` read the
  ledger. They would take the provisional 0/4.

**Fix.**

- **Supersession.** `regrade_attempt` now supersedes tiers 1 and 3 when the
  incoming grade is held, as well as when the prior grade was held (F4 of
  the stage).
- **The ledger's evidence half.** `held_for_review_attempts` now reads it
  per criterion, as the attempt step reads its criterion vector. A criterion
  is assessed when a live row grades it and no live row marks it unassessed.
- **Why the second change.** The regrade supersedes machine tiers only, so
  an owner adjudication's tier-4 rows stay live beside a later held regrade.
  Replay leaves out every criterion an unassessed row names, so it holds.
  The old ledger rule ("some live row is assessed") did not, and the
  attempt's score is the regrade's provisional one. The second test pins
  this case. With the old ledger rule it failed: `(False, True)`.

**Regression.** The test runs assessed, then held, then validated. At each
step it compares:

- the ledger status and the replay status;
- the live rows;
- the schedule (live and after a full rebuild);
- the fitter's `applies_review`;
- the same-item failure streak;
- the dataset `R_next` of the earlier attempt.

Held: both evaluations say held, the schedule is the pre-attempt one, the
fitter applies no review, the streak is 0 and `R_next` is
`grade_held_for_review` with no value. Validated: both say not held, the
schedule is the assessed one again, and the review applies.

### F2: a scored cold probe held by a regrade abstains

**Reproduction.** A certification cold probe was scored on submission
(`held`, success). A regrade then held its grade. The test simulates this
with the ledger a regrade into a hold writes: unassessed tier-3 rows over
tiers 1 and 3, and a held blind record. The certification vault runs no
route check of its own.

- Before the fix, `false_certification_rate` kept denominator **1**
  (`held = 1`).
- `cold_outcome_labels` still exported the success.

**Fix.** A new function, `certification_cold_probe.effective_cold_probe_outcomes`,
is the outcome store as readers take it now.

- A row whose probe attempt is held now (THE predicate over the ledger) reads
  as `indeterminate`, reason `grade_held_for_review`, with no success and no
  correctness.
- This applies to a scored row and to a row held on submission (recorded
  `grade_unavailable`).
- The stored receipt is untouched: its verdict is kept under
  `recorded_verdict`.
- A release restores the recorded verdict: a validating regrade, or an owner
  adjudication (tested).
- Any other abstention (surface, assistance, a withdrawn certificate)
  outranks the hold, as on the ladder.
- `false_certification_rate` (and so the B5 scoreboard), `cold_outcome_labels`
  and `certification_cold_probe_report` all read it.
- The reason is read-time only. Migration 139's CHECK vocabulary is for
  stored rows and is unchanged.

### F3: diagnostic observations held by a regrade qualify nothing

**Reproduction.** The test used the golden-path fixture: a baseline episode
with two qualifying, belief-updating probe answers on the method-selection
cell. The boundary read `weak`. Both answers were then held by the
regrade-into-hold ledger, and five readers were checked:

| Reader | Before the fix |
|---|---|
| Qualifying rows in the episode | 2 |
| Belief-updating rows in the episode | 2 |
| Vault qualifying count | 2 |
| `episode_posterior` qualifying count | **0** |
| EIG calibration observations | 2 |

Only the posterior excluded them, and the boundary still labelled the cell
`weak`.

**Fix.** One shared effective view:

- **Where it is.** `held_grades.effective_probe_observation_rows`, applied by
  the repository's `probe_observations_for_episode`. Every reader of an
  episode's observations reads through that accessor:
  - the diagnostic boundary;
  - block completion and the episode completion policy, robust override
    included;
  - calibration-session progress;
  - the probe-audit EIG, cross-surface and replay checks;
  - the posterior.
- **What it does.** While an observation's grade is held, it updates no
  belief and qualifies nothing. Its joined `rubric_score` is `None`, and the
  row carries `grade_held_for_review`.
- **The boundary.** It reads a held observation as `contested` (linked to its
  receipt), exactly as a probe held on submission already read. It is never
  `weak` or `demonstrated` from a provisional score.
- **The counts.** The §5.9 session cap and the onboarding ceiling counts
  (`qualifying_probe_observation_count*`) exclude held observations too.
- **The receipt.** `as_recorded=True` returns the stored flags.
  `probe_observation_for_attempt` stays the receipt, used only for existence
  checks and the grader-agreement regrade check.

## The review's other claims

- **"Every reader reads one of [the two evaluations]."** The certification
  exports and the diagnostic boundary now read the ledger predicate (F2, F3).
- **The flags claim.** The stage doc said the diagnostic pack, calibration
  sessions and probe blocks' qualifying counts "read the held observation's
  flags". They now read the effective view (F3). The stage doc's table rows,
  and decisions 3 and 4, are corrected.
- **"The two predicate evaluations agree."** They now agree by construction:
  the same per-criterion rule over the same live rows (F1, both tests).

## Parity

Nothing changes below `mvp-0.17`, or with the kill switch on:

- No record holds anything there.
- The new supersession fires only when the incoming grade is held.
- The ledger's per-criterion rule runs only for record-held attempts.
- Both effective views return their rows unchanged when the held set is
  empty.

The stage's parity runs (`mvp-0.16` and `mvp-0.17` with the switch off, 0
differing tables on the owner's three vault copies) are therefore unaffected,
and were not repeated.

## Gate

Run at `145d2bf9` (the last code commit; the record commit after it is docs
only), with `TMPDIR` set to the worktree's `fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **15 kept, 0 broken** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **9252 passed**, 0 failed, 46 warnings, 5 min 40 s. The stage gate passed 9248, and this fix adds 4 tests (`test_review_f1_*` x2, `test_review_f2_*`, `test_review_f3_*`) and changes no existing test |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **95 passed**, 9157 deselected, 1 warning |
| DB and config reference: `db_generate_reference.py`, then `db_validate_reference.py` | **errors: []**. Schema head 185, 308 table notes, 367 owned notes, 4072 wikilinks checked. The schema and config did not change. Generation rewrote 355 notes, all restamp-only (`source_commit` and its timestamp), so it was dropped; the committed reference validates as is |

- **Not applicable.** No file under `apps/learnloop-tauri` changed, so the
  npm and cargo steps do not apply.
- **Test flags.** Both pytest runs also passed `-q -p no:cacheprovider`.

## Paid calls

None. Every test uses fakes.

## Open questions

1. **Causal cold verifications.** This one was not raised by the review. A
   repair's cold verification records its success from the cold attempt when
   it is answered (`causal_cold_verifications`). A held cold attempt is
   already refused (`cold_attempt_unassessed`). But a verification recorded
   from an assessed cold attempt that a later regrade holds keeps its
   success. The factor resolution applied from it is not undone either.
   Undoing it means reopening a resolved factor, a state transition beyond
   this fix. Should a regrade into a hold reopen it?
2. **A regrade of an adjudicated attempt.** A machine regrade supersedes the
   machine tiers only, so an owner adjudication's tier-4 rows stay live
   beside it. The attempt's score becomes the regrade's: a held regrade
   holds the attempt (pinned above), and a non-held one replaces the ruling
   in replay. Should a regrade of an adjudicated attempt be refused, or rank
   below the adjudication?
