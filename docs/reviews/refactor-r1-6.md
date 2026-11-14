# Refactor fix R1-6: the Demonstrated timeline credits an observation the projection banks nothing for

Bug ledger row R1-6 (with D-34, and two sibling shapes found on the way, R1-6b and R1-6c). Branch
`fix/r1-6-timeline-credit-gap`, based on main `ab77f15b4e`. Behaviour track, read side only: nothing the
projection persists moves, so no algorithm tag (`docs/algorithm-change-playbook.md` step 1); the corrections are
ungated (§3).

## 1. The shape, on a private copy

A fresh backup-API copy of `learnanything-ad1/fixtures-local/owner-copies-mvp058/linear_algebra` (at `mvp-0.58`)
under the gitignored `fixtures-local/r16/`, since deleted. Structure and numbers only; no learner, item or answer
text was read out of it.

The projection banks per facet, the timeline folds per facet; on the copy two facets disagree, through one attempt
whose criteria target both (each criterion has two primary targets at `schema_interpretation`):

| Facet | Timeline final | Banked | Cells banked |
|---|---|---|---|
| A (the receipt tests' first failure) | 0.200036 | 0.113064 | `schema_interpretation` 0.113064 |
| B | 0.634898 | 0.547926 | `procedure_execution` 0.434862, `schema_interpretation` 0.113064 |

Per observation of facet A's cell (B's `schema_interpretation` cell is the same four attempts): an assisted attempt
on the item (no credit, but it marks the item's surface group), then three unassisted attempts on the same item:
an independent attempt (timeline 0.086972, banked the same), a self report (0.026092, the same), and the
disagreeing observation (timeline 0.086972, banked 0). Its structure:

- **Attempt**: `independent_attempt`, no hints, not primed, no reference status, no recorded activity
  classification (the policy's defaults: unassisted, certification-eligible). Active interpretation present
  (`certainty_discount` = `shared_certainty_lcb` = 0.6958, the evidence mass both folds use); no adjudication.
- **Grading epochs**: the first grade, four rows by grader tier 1, grading revision 0, each citing the same
  contract, observation ids present, no attribution, full marks (4 criteria of 1 point), all four superseded. A
  regrade 6.5 hours later on the same day: four rows by tier 3, **no grading revision, no contract, no observation
  id**, no attribution, the same full marks, live. That is a regrade written before regrade contracts (`mvp-0.26`).
  Replay recorded the hold on the attempt (`manual_review_reason = grade_contract_unrecorded`).
- **Mapping**: the contract's four criteria each name two primary targets (facets A and B) at
  `schema_interpretation`, rubric total 4. The live item's rubric has the same four criteria with **no authored
  targets** (the contract compiled them from the item's facets). Surface group from the item id (no fingerprint).
- **Caps**: none bound (`bound_by` empty); direct channel, nothing embedded. The 0.086972 is the repeat-surface
  credit (discount 0.25: the group was marked by the earlier assisted attempt).
- **Time order**: third unassisted observation in the cell; its first grade and the held regrade are the cell's
  last two events.

Why the folds part: the projection reads only the current epoch and skips a held attempt
(`substrate/canonical_projection.py:719-722`). The timeline replays every epoch and turns the held one into a
zeroing correction (`learner/facet_evidence_timeline.py:926`), but emitted an epoch's event only for the facets
that epoch's rubric *names* or *credits*. The held epoch is read against the live rubric (it cites no contract),
whose criteria carry no targets, and it credits nothing, so no correction event reached facets A or B and the first
epoch's 0.087 stayed on both curves. This is exactly D-34's mechanism (D-34's construction: a cited grade flipped by
an adjudication, then rewritten as a regrade before regrade contracts); the ledger's note that the copies hold no
such regrade was wrong for this copy.

**The same shape elsewhere** (counts): `arxiv_v2` holds 1 held attempt of this shape (a cited first epoch under an
uncited live regrade), but its live rubric names targets, so the correction was already emitted and the folds agreed;
`probability` 0; the tracked `migration_head` 0; `mvp017_route_check_replay` 1 cited epoch under an uncited live one,
not held there (the receipt tests never replay it), and both folds read the uncited epoch alike.

## 2. Which fold is right

The projection. Its own rule (`project_canonical_facet_state` docstring, `canonical_projection.py:641-644`): "Each
attempt contributes its current grading epoch under the contract that epoch cites; an attempt whose current contract
is unrecorded contributes nothing, as replay holds it." The timeline states the same rule for itself and failed to
apply it: the module docstring ("Each graded attempt contributes exactly its *latest grading epoch*'s credit. A
regrade replaces the attempt's previous contribution"), the snapshot field (`contract_unrecorded`: "The projection
banks nothing from them; neither does this fold.") and the held branch's comment ("the current epoch banks nothing,
so it corrects the attempt's earlier contribution to none"). The vault's `Canonical Knowledge Model` note: "changing
a live item/rubric after presentation cannot change what a historical answer demonstrated" — the timeline's facet
filter made the live rubric decide it. So the timeline is wrong, and the fix is read side.

## 3. The fix and the gating call

**R1-6 / D-34** (`f448c90f60`): within one attempt, a later epoch also gets an event in every facet an earlier
epoch of that attempt put an event on (`reached_facets`, `facet_evidence_timeline.py:907`, `:966-967`), so a
correction replaces the attempt's contribution in every facet it reached. This is more general than D-34's proposed
fix (name the held epoch's facets from the live item's compiled targets): it does not depend on the live item at all,
so it also covers the retarget sibling below. D-34's strict xfail is now a pass.

**Ungated, with the reason.** The brief's precedent (S6) gates a display correction by
`facet_belief_corrections_on` so the kill switch restores the predecessor's display. Here the predecessor's display
was never coherent: the projection holds the attempt, reads the current epoch alone, reads the corrected contract and
resolves aliases at every tag and with the switch either way, so the predecessor's curve disagreed with the
predecessor's own banked credit. Each new test runs with the switch on and off (`b034701fac`); all eight variants
fail at the base (`switch_off` included) and pass now.

## 4. Fail-first evidence (at `ab77f15b4e`, the tests on synthetic vaults)

| Test (`tests/test_projection_timeline_agreement.py`) | At the base |
|---|---|
| `test_the_timeline_drops_what_a_held_uncited_regrade_holds` (D-34, was a strict xfail) | `recall` timeline 2.3916 vs banked 1.3916 |
| `test_a_held_regrade_that_kept_its_marks_takes_its_credit_off_the_curve[switch_on/off]` (R1-6's owner shape: the item's criteria name no targets, a cited first grade, a regrade before regrade contracts with every mark kept, superseding every row) | `recall` 0.8697 vs 0.6958 |
| `test_a_regrade_under_a_retargeted_item_takes_the_old_facets_credit_off_the_curve[switch_on/off]` (sibling: a criterion retargeted to another facet between grade and regrade) | `recall` 0.6088 vs 0.5218 |
| `test_a_measurement_correction_that_reinterprets_history_reaches_the_curve[switch_on/off]` (R1-6b) | shared facet 1.3916 vs 0.6958 |
| `test_a_trace_observation_recorded_under_a_facet_alias_licenses_the_supporting_credit_in_both[switch_on/off]` (R1-6c) | `f_algebra` 0.0 vs 0.0803 |

The owner lane at the base with the xfails removed: `test_receipt_exactness[owner:linear_algebra-mvp-0.58]`,
`[owner:linear_algebra-mvp-0.59]` and `test_receipt_derivation[owner:linear_algebra]` fail (0.200 vs 0.113); now
the owner lane passes on all three copies at both tags (18 passed for the two files, fixtures included).

## 5. Siblings: every place the timeline decides whether an observation counts, caps, or is replaced

Timeline lines are `learner/facet_evidence_timeline.py` at the tip, projection lines `substrate/canonical_projection.py`.

| Timeline | Projection | Verdict |
|---|---|---|
| attempt set and order: `snapshot.attempts` (`:866`, `list_attempt_history`, `ORDER BY created_at, id`) | `ledger_rows` (`:713`, the same table and order) | agree |
| current epoch: last of `ordered_epochs(all rows)` (`:898`) | `current_epoch(live rows)` (`:719`) | agree (shared `grading_epochs`; the D-34 construction with partial supersession passes) |
| held attempt: last epoch with no rows (`:926`) | `continue` (`:721`) | agreed on credit and marks; the correction event was lost — **R1-6, fixed** |
| a later epoch's facets: `historical | credited` (`:966`) | current epoch only | **R1-6 (held) and the retarget shape, fixed** |
| contract read: stored contract (`fetch_assessment_contract_versions`) | `effective_assessment_contract_versions(…, projection_version)` (`:328`) | **R1-6b, fixed**: a measurement correction with historical reinterpretation for the vault's version redirected the projection only |
| no contract: live item rubric (`:820`), `item is None` skips | the same (`:734`) | agree |
| trace observations: merge map only | aliases, then merges (`:841`) | **R1-6c, fixed**: an observation stored under a facet id that is now an alias licensed the supporting target only in the projection |
| unassessed rows (`:639`), localization, the supporting split (`:702`), transfer scale (`:709`) | `:795`, `:878`, `:881` | agree |
| evidence mass: `p0_evidence_mass_by_attempt`, fail-closed 0.0 (`:874`) | `p0_effective_evidence_mass` (`:766`) | agree (one helper; the ledger covers every attempt) |
| activity policy (`:877`) | `:780` | agree (same columns, same function) |
| unresolved-failure gate on the raw fraction (`:718`) | on the adjudicated fraction when an adjudication heads the chain (`:916`) | agree on what they decide here (marks): with several targets and no attribution neither marks anything either way |
| unverified (PF-c) failure and the single-target synthesis (`:751`, `:755`) | ungated (`:1000`, `:1005`) | agree with the switch on; **with the switch off, or at the floor `mvp-0.58`, they disagree by S6's design** (logged R1-6d, not changed: §7) |
| caps: `itemize_observation_contributions` (`:770`), embedded share via `group_scale` (`:784`) | `:1054`, `min(embedded, credit)` (`:1067`) | agree (embedded ≤ credit by construction, so the `min` never binds) |
| novelty: marks of the latest epoch only (`:958`, `:1015`) | marks of the current epoch | agree |
| fold: replace per attempt, embedded cap per cell (`:504`, `:525`) | per-cell `cap_embedded_credit` (`:1106`) | agree |
| `snapshot_as_of` hold (`_epoch_held_as_of`) | replay's predicate | unchanged; the carried facets apply as of a cutoff too |

Callers of the changed functions: `load_facet_timeline_snapshot` (now takes `projection_version`):
`session_learning_diff.session_learning_diffs` and the module's own `vault_timeline_snapshot`, `_observation_events`,
`facet_evidence_timelines`. `_observation_events_by_facet`: `_observation_events`, `facet_evidence_timelines`, whose
readers are listed in §6. No other module recomputes per-observation credit (`allocate_success_mass` /
`itemize_observation_contributions` are called only by the two folds; `recall_coverage` mentions it in a docstring).

## 6. What the owner sees (on the copies, numbers only)

Measured by running every reader below over a fresh copy of each owner vault with the base code and with this
branch, and diffing the outputs.

- **`linear_algebra`**, facets A and B only:
  - Final Demonstrated: A 0.200 → 0.113, B 0.635 → 0.548 (each now equals banked credit). Each curve gains one
    correction point at the held regrade's time (delta −0.087); points 4 → 5 and 5 → 6.
  - Sidecar `get_facet_evidence_timeline` (knowledge model): the same series.
  - Knowledge map: correction badges on 3 facets → 5 (A and B gain one); the map's Demonstrated state reads banked
    credit and does not change.
  - Session learning diff: one session (the one holding both the attempt and its regrade): facets demonstrated
    2 → 0, demonstrated attempts 1 → 0; corrections stays 1. The other 15 sessions are unchanged.
  - Reader recap and `router_reader` (`_effective_success_since`, "answered since"): for A and B, the session start
    times at which the curve shows an effective unassisted success since then go from 11 to 8 of 16 (the held
    attempt no longer counts).
  - Reader recap "since last time" (`demonstrated_since`): unchanged on all 3 extractions at 4 cut-offs.
  - Receipts: the per-observation itemization sums to banked credit (the correction point carries no itemization);
    `facet_ready_derivation` reads persisted slices and is unchanged.
- **`probability`**, **`arxiv_v2`**: every reader output above byte-identical before and after.

## 7. Proof

- **Agreement tests**: `tests/test_projection_timeline_agreement.py` 11 passed (was 2 passed, 1 xfailed, before the
  new tests). Owner lane (`LEARNLOOP_OWNER_VAULTS` = fresh backup-API copies of the three copies):
  `test_receipt_exactness` and `test_receipt_derivation` 18 passed, both tags, no xfail.
- **P-shadow**: `learnloop rebuild --shadow --json` on fresh copies of the three vaults with the base code and with
  this branch: identical output apart from the run's wall-clock stamp and marker id (semantic summary facet 0 /
  mastery 21, 18, 34 / schedule 0 under both codes; live database unchanged). Nothing stored moves.
- **Identity pins** unmoved (`test_identity_pins`, `test_retired_config_identities` pass). Structure ratchet: no
  number rose (the event walk's epoch-rubric step became `_epoch_rubric_and_group`, `95a6d0063a`, to keep it under
  200 lines).
- **Kill-switch twin**: every new test runs switch on and off (§3).

## 8. Assertions changed

- `tests/test_receipt_exactness.py`, `tests/test_receipt_derivation.py`: the `_known_credit_gap` strict xfails on
  `owner:linear_algebra` removed (the equality they marked now holds); the assertions are unchanged.
- `tests/test_projection_timeline_agreement.py`: D-34's strict xfail removed.
- `tests/test_facet_evidence_timeline.py::test_bulk_timelines_read_grading_history_once`: the contract-read spy
  wraps `effective_assessment_contract_versions` (the read the snapshot now makes) instead of
  `fetch_assessment_contract_versions`; it still asserts exactly one bulk contract read.

## 9. Ledger

R1-6 and D-34 fixed (`f448c90f60`; owner lane `d6594cd572`). New rows: R1-6b (fixed, `5e7ae62c60`, `13dc45a6b9`),
R1-6c (fixed, `19e2d04079`), R1-6d (open: S6's gated rule leaves the timeline and banked credit apart at the floor
tag and with the switch off; a design call, see below).

**R1-6d, the choice.** S6 made the timeline skip a PF-c unverified failure and synthesize a failure only when no
attribution is on record, gated so that the switch off (and `mvp-0.58`) shows the predecessor's curve. The projection
does both at every tag, so for those two shapes the predecessor's curve does not equal the predecessor's banked
credit (S6's own failing test: Demonstrated 0.25 of banked). Choices: (a) keep S6's gate (the switch restores the
predecessor's display, incoherent for those shapes); (b) ungate as here (the curve always ends at banked credit; the
switch then no longer restores that display). Recommendation: (b), for the reason in §3; it changes
`test_s6_with_the_switch_off_the_timeline_is_the_predecessors`, so it is not done here. The owner copies hold
neither shape (the S6 record), so no owner display moves either way.

## 10. Not verified

- The durability lane, `--fresh-connections`, vitest, the arc-close lane and the full suite (the orchestrator's).
- The readers in §6 were run as library calls over the copies (the sidecar handlers and the router's reader-activity
  claims were not driven end to end; the router's claim list depends on reader sessions the copies may not hold, so
  only the predicate it applies was measured).
- The shadow ran at the copies' own tag (`mvp-0.58`); the owner lane's receipt tests covered `mvp-0.59`.
- The retarget, measurement-correction and alias shapes are shown on synthetic vaults only: no owner copy holds a
  measurement correction (0, 0, 0), a trace observation under an alias (0 of 1 row on `probability`), or a facet
  merge.
