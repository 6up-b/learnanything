# mvp-0.75: the lesson-weight fit reads mastery's recorded facts

Branch `teacher/l42-fix-round-2`, from `b887fc9b4a`: main `bc70e26255` (mvp-0.72, migration head 274) plus H3's fix round
(mvp-0.73). The tag is reserved after mvp-0.74, which is another worker's. The chain lists it after whichever tag
comes last at the merge. The findings come from L4-2's second adversarial review (2026-11-25), ledger rows L42-R17
to L42-R27. The design and the choice between three options are in
[refactor-l42-fit-redesign.md](refactor-l42-fit-redesign.md). All measurements were taken on synthetic vaults with
fakes.

The tag consists of:
- one constant, `LESSON_WEIGHT_FACTS_ALGORITHM_VERSION`;
- its chain entry, set and predicate (`mastery_facts_recorded`);
- one upgrade row, `Link(mvp-0.75, whole_vault_rebuild)`, and its test row.

It adds no migration (276 is not taken), no config key, no kill switch and no new constant.

## What changes at the tag

- **Mastery records what it did (L42-R21, L42-R22).** Each application, live or replayed, writes a
  `mastery_application` block into the attempt's payload (`mastery.mastery_application_facts`). The block holds:
  - whether the update applied;
  - the prior `(μ, P, last_evidence_at)`;
  - the instant;
  - the score mastery read;
  - the `(a, b)` it applied;
  - the observation weight;
  - the interpretation variance it was given;
  - `primed`;
  - the coverage floor;
  - the posterior.

  A raw table beside the curve would describe grade time. The trajectory needs mastery's current application, and a
  regrade of an earlier answer moves every later prior on replay. For that reason the block lives in the record that
  replay rewrites.
- **Whole-second observation (L42-R17).** A live grade observes at the whole second the ledger keeps, which is the
  instant replay observes at. As a result, a rebuild no longer moves a live grade's drift interval.
- **The fit reads facts and infers nothing (L42-R21, L42-R22).** `lesson_weight.mastery_applications` is the one
  reader. In the trajectory:
  - every update's applied flag, instant, score, weight, noise and floor come from its block, and the check's own
    block supplies the start state with its clock;
  - the blocks must chain exactly: each prior equals the previous posterior, including the clock, and the outcome's
    prior equals the last posterior;
  - the outcome's block is required, so the fit fails closed.

  The labels on `trajectory_inputs` are `missing_application_record`, `outcome_record_missing`,
  `curve_differs_from_applied`, `chain_broken`, `outcome_chain_broken` and `update_not_reproduced`. The last one is a
  guard for a mastery configuration edited since the facts were recorded. Any label sends the fit to the first-order
  form. A floor-bound update is now recomputed rather than labelled, because its noise is recorded. The likelihood
  keeps the frozen pair, per the owner's option 2. When a resolver's frozen pair differs from the pair mastery
  applied, the weight and pool updates record `resolving_pair_differs_from_applied`.
- **The first-order form uses the check as it now stands (L42-R20).** `check_application` supplies:
  - the check's replayed prior and instant, from its block;
  - the current grade of its current epoch;
  - its frozen curve, or the applied one when no frozen curve exists.

  The trace records these as `first_order_inputs`. The check's stored sensitivity is used only when its block is
  missing. Its recorded mass and receipt do not change.
- **One outcome order (L42-R19).** `qualifying_outcomes` takes the order as a required argument, and
  `outcome_order(tag, fit=...)` is the only source of it. From the tag the retained-forecast report
  (`forecast_report.resolve_lesson_step`) and the router's miss-cause learning (`miss_cause._offer_rows`,
  `miss_cause_report.section`) take the fit's order.
- **A check is placed at its attempt (L42-R18).** From the tag, only an outcome after the later of the check row's
  instant and its attempt's instant can resolve the check. This applies to history as well.

Below the tag every one of these behaves exactly as at mvp-0.73. Tests cover both sides, in
`tests/test_lesson_weight_facts.py` and the pinned predecessor cases in `tests/test_lesson_weight_fit_trajectory.py`.

## Fixed without the tag (they change live writes, not what a stored row means)

- **L42-R18.** The live check reads its instant under the writer lock and applies its attempt at that same instant.
- **L42-R24.** A teacher request records the request gate's estimate of the prompt it sends, under
  `input_estimate` on its receipt. The compaction forecast measures growth from that estimate, including for nested
  and withheld calls whose text is not kept. A receipt from before this change that has no text is bounded below by
  the current estimate.
- **L42-R25, L42-R26.** The owner SQL in [algorithm-mvp-0.72.md](algorithm-mvp-0.72.md) now applies two rules:
  - the window query uses the freeze's availability predicate;
  - the label report counts the missing curve's provenance values.

  The same record also carries the record corrections (L42-R27).

**Why a whole-vault rebuild.** The rebuild writes every attempt's block, so all of history gets the facts at once.
No "unknown at upgrade" marker is needed for the mastery facts. Mastery's replay already observes at whole seconds,
so the rebuild moves no mastery value. The frozen curves and their missing markers are unchanged.

## Pins and goldens

- **Identity pins.** The nine pins that hash the vault's tag were regenerated: `A1-A4.manifest_hash.init`,
  `C3.boundary(.init, _offer.init)`, `C3b.chooser(_offer)`, `C3b.start_key(_offer)`, `C5.init` and `C6.init`.
- **Effective defaults and the CLI surface:** the tag line, and `upgrade --to`'s default. Only that one value of the
  CLI snapshot changed.
- **Goldens.** The grade application golden (88 payloads) and the diagnosis journey golden (18) each gain the block
  and the tag. A parsed comparison, with nested JSON strings decoded, found no other value changed.
- **Structure ratchets.** `attempts.py` rose to 5,873 lines (+2: the gate and the call), and golden JSON lines rose to
  307,358 (+2,226). The reasons are recorded in `structure.toml`.

## The owner-copy procedure (for the orchestrator, from an mvp-0.74 or mvp-0.73 copy; counts and digests only)

Make backup-API copies. Run [algorithm-mvp-0.72.md](algorithm-mvp-0.72.md)'s digests for the checks, the lesson and
forecast receipts and `attempt_grade_curves` on the predecessor. Then run `learnloop upgrade --vault "$COPY" --to
mvp-0.75` and the same digests again, followed by the queries below. Expected results:
- the raw receipts, checks and curves digests are unchanged;
- `learning_object_mastery`, `facet_recall_state` and `attempt_surprise` differ only in `algorithm_version`;
- every payload has its block;
- on a copy with lesson checks, the likelihood and label counts account for each changed weight or pool update.

The three owner copies on record hold no lesson check, so on them only the block count moves.

```sh
sqlite3 -readonly -header "$COPY_DB" <<'SQL'
SELECT count(*) AS payloads,
       count(*) FILTER (WHERE json_type(payload_json, '$.mastery_application') = 'object') AS with_facts,
       count(*) FILTER (WHERE json_extract(payload_json, '$.mastery_application.applied') = 1) AS applied
FROM attempt_debug_payloads;
SQL
```

The likelihoods, the labels that sent a window to the first-order form (including a missing curve's provenance), and
the resolving fallbacks and pair disagreements, as counts only:

```sh
sqlite3 -readonly -header "$COPY_DB" <<'SQL'
SELECT json_extract(detail_json, '$.likelihood') AS likelihood, count(*) AS updates
FROM lesson_weight_trace WHERE kind = 'weight_update' GROUP BY 1 ORDER BY 1;
SELECT label, count(DISTINCT seq) AS updates FROM (
  SELECT t.seq, j.key AS label
  FROM lesson_weight_trace t, json_each(t.detail_json, '$.trajectory_inputs') i, json_each(i.value) j
  WHERE t.kind = 'weight_update' AND j.key IN ('missing_application_record', 'outcome_record_missing',
    'curve_differs_from_applied', 'chain_broken', 'outcome_chain_broken', 'update_not_reproduced')
  UNION ALL
  SELECT t.seq, json_extract(i.value, '$.provenance')
  FROM lesson_weight_trace t, json_each(t.detail_json, '$.trajectory_inputs') i
  WHERE t.kind = 'weight_update' AND json_extract(i.value, '$.provenance') IN ('missing_capture', 'missing_at_upgrade')
) GROUP BY 1 ORDER BY 1;
SELECT kind, coalesce(json_extract(detail_json, '$.resolving_fallback'), '-') AS fallback,
       json_type(detail_json, '$.resolving_pair_differs_from_applied') IS NOT NULL AS pair_differs, count(*) AS updates
FROM lesson_weight_trace WHERE kind IN ('weight_update', 'pool_update') GROUP BY 1, 2, 3 ORDER BY 1, 2, 3;
SQL
```

Run `learnloop rebuild-derived-state --vault "$COPY" --json` twice. The payload, mastery and trace digests must
match after each run.

## Open, an owner call (L42-R9, restated)

A calibration import changes the interpretation variance that replay recomputes, because the latest matching
calibration wins. A rebuild after an import therefore moves mastery, and through it the fit, without a new answer.
There are two options:
- **Pin the calibration identity (or the applied variance) per epoch.** Old grades keep their meaning. From this tag
  the block already records the variance mastery applied, so replay could read it back for epochs graded under a
  calibration rather than recompute it.
- **Keep retroactive reinterpretation, which is the channel's design.** An import then rebuilds the affected
  projections in its own transaction and reports the change.

**Recommendation: the second option.** The calibration channel exists to reinterpret past grades, so the defect is
the silent, delayed move, not the move itself. A rebuild at import with a change report makes the move explicit
without changing the channel's design. This is not changed here.
