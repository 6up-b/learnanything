# The follow-up gate's records survive replay (refactor bug ledger H-1)

Found while designing H3 to H6 (`docs/reviews/refactor-h3-h6-design.md` §3.9, on the arc H design branch). Fixed here
as its own small landing, option (A) of that section. Base: origin/main `86f29b0d39`.

## The defect

The live follow-up gate (`diagnosis/followups.py`) runs after the grade and writes its decision onto the attempt's
surprise row with an UPDATE (`db/stores/attempts.py`, `update_attempt_surprise_actions`):

- the actions it queued (`triggered_actions_json`);
- the ones it held back (`suppressed_actions_json`);
- what it read and scored (`gate_diagnostics_json`).

The grade itself inserts the row with those empty. Replay never runs the gate. Yet every replay of `learning_state`
deleted the row and inserted the grade's fresh one:

- the whole-vault rebuild cleared the table (`substrate/rebuild_orchestrator.py`, `_run_learning_state`);
- a per-LO replay reset the LO's attempts' rows (`substrate/replay.py`, `_replay_learning_object`). A regrade runs one,
  and so do the grading command, the integration backfill, goal series and exam seeding.

So the records were cleared, not recomputed. Nothing served or answered was undone: follow-up tasks, attempts,
remediation episodes and ratings are their own rows. But history lost the record:

- the attempt's feedback and detail lost their queued and held-back actions, the gate's diagnostics, and the "this
  answered the follow-up from …" link (`followup_source_attempt`), which the rating path uses too;
- past sessions' count of follow-ups queued read 0;
- an unanswered legacy queued follow-up (`negative_surprise_followup:`, `intervention_followup:queued:`) left the
  scheduler's pending list;
- the gate fitter (`learnloop fit gate`), the scheduling evaluation and the signal quantiles lost their rows.

## The fix

Replay now carries the three columns across, by attempt id, the way it already carries diagnosis receipts and the
firewall's audit events:

- **Per-LO replay** (`substrate/replay.py`). `_replay_learning_object` reads the LO's attempts' gate records before
  the reset deletes their rows (`Repository.attempt_surprise_gate_records`). After each attempt replays, it writes the
  record back onto the replayed row, byte for byte (`Repository.restore_attempt_surprise_gate_record`). The record goes
  back before the next attempt replays, as live, where the gate ran between the two answers. This covers the regrade,
  the grading command, the integration backfill, goal series and exam seeding.
- **Whole-vault rebuild** (`substrate/rebuild_orchestrator.py`). `_run_learning_state` reads every row's record before
  it clears the table and hands them to the per-LO replay (`rebuild_derived_state(..., gate_records=...)`), because the
  per-LO read would then find the table empty.
- **The shadow rebuild** (`substrate/shadow_rebuild.py`) now compares these columns. `ShadowRebuildResult` gains
  `followup_gate_records`, counts only:
  - rows before and after;
  - rows the gate wrote something on, before and after;
  - rows changed, and recorded rows the replay cleared;
  - rows added and removed.

  `as_dict()` (so `learnloop rebuild --shadow --json`) carries it as `followup_gate_records`. The text summary adds one
  line: "Follow-up gate records: N recorded, M changed by the replay." Before this, the shadow rebuild never compared
  `attempt_surprise`, so it could not have reported the clearing.

No replayer reads these columns. The scheduler's pending list, the feedback, the session summary, the gate fitter and
the reports are all live reads. So carrying them changes no other derived number.

## The tag question

The playbook's step 1: "Decide whether the change alters persisted meaning. If it does, add a new immediate-successor
`algorithm_version`." Step 6: "The same-version rebuild on the golden fixture must reproduce the same semantic
projection."

**No tag.** Reasons:

- The fix changes no live write. A grade and the gate write what they wrote before.
- What it changes is a rebuild's output, from "the grade's empty record" to "the record stored now". So after any
  rebuild every row holds exactly what it held before the rebuild.
- A rebuild therefore never moves a stored value it did not move before. It stops moving one it should never have
  moved: step 6's same-version reproduction, restored.
- No replayer derives anything from these columns, so no derived number moves either.
- The D8 gaps that did take tags (mvp-0.65 to mvp-0.67) were different. Each changed numbers replay derives (mastery,
  coverage, the seed) relative to what vaults had stored. Here no derived number changes.

**What `learnloop rebuild --shadow` reports on an existing vault:**
- **Records already cleared by an earlier rebuild** (the owner copies the orchestrator ran: 0 rows with records):
  `recorded_before` 0, `changed` 0, `cleared` 0. Nothing to restore, so no difference.
- **Records the live gate wrote since the last rebuild:** `recorded_before` N, `changed` 0. The replay keeps them.
  The predecessor code would have reported `cleared` N, had the shadow rebuild compared them.

## Records already cleared cannot be recomputed

The gate read live state when it decided: the session's time and caps, the learner's minutes, its thresholds as fitted
then, the item pool. Replay has none of that and never runs the gate. Records an earlier rebuild cleared (every
whole-vault upgrade so far, mvp-0.46 among them, every regrade's LO, every `learnloop rebuild`) are gone from the live
vaults.

**The owner's option: restore from a backup taken before the clearing rebuild.** What it would involve:

1. **Pick the backup.** The newest backup of each vault taken before the rebuild that cleared it. Several upgrades may
   each have cleared a different part of history: an attempt graded between two rebuilds is only in a backup taken
   between them.
2. **A one-off script, run on a backup-API copy of the live vault first, never on the live vault.** For every attempt
   present in both, it copies the three columns from the backup's `attempt_surprise` into the copy's row, and only
   where the copy's row holds the grade's empty values. That way a record the gate wrote since is never overwritten.
3. **Decide the queue part separately.** A restored queued action that nobody has answered since puts a legacy
   follow-up back on the scheduler's pending list, possibly weeks old. Two choices:
   - restore everything;
   - restore the diagnostics and the held-back actions, and the queued actions only where a later attempt answered
     them. That gives history and the rating link back without reviving stale follow-ups.
4. **Check it.** On the copy: `learnloop doctor`, the shadow rebuild (with this fix it carries the restored records:
   `changed` 0), and a count of restored rows. Then apply it to the live vault with LearnLoop closed.

After this landing, any later rebuild keeps what is restored. Without this landing, the next rebuild would clear it
again, so the restore only makes sense after this lands.

## Tests

`tests/test_gate_records_survive_replay.py`, 26 tests:

| Test | What | Before the fix (the shadow comparison in place, the replay as on the base) |
|---|---|---|
| `test_a_whole_vault_rebuild_keeps_the_gates_records[<case>]` | The 21 synthetic diagnosis journeys (`tests/diagnosis_journey_helpers.py`): every row's three columns are identical before and after a whole-vault rebuild | 9 failed (the journeys with gate records), 12 passed (no records to lose) |
| `test_the_journeys_hold_gate_records_to_keep` | The recurrence journey has three rows with actions and diagnostics, so the tests below are not empty | passed (it checks the fixture) |
| `test_a_per_lo_replay_keeps_them` | `replay_learning_object` on every LO keeps them | failed |
| `test_a_regrade_keeps_them` | A regrade of an attempt with a gate record keeps every record, the regraded attempt's included | failed |
| `test_what_history_shows_reads_the_same_after_a_rebuild` | With a queued action on an attempt whose item was answered later and one nobody answered since: every attempt's feedback bundle (the surprise card's actions and diagnostics, the follow-up link, the rating, the queued flag), `followup_source_attempt` (the rating path), the session's follow-up count (2) and the scheduler's pending list are the same after a whole-vault rebuild | failed (count 2 → 0, the pending item gone, the links gone) |
| `test_the_shadow_rebuild_compares_the_gates_records` | `followup_gate_records`: 3 recorded, 0 changed, added or removed | failed (`changed` 3, `cleared` 3) |

The feedback comparison leaves out the bundle's causal overlay (`causalFeedback`). That part is the diagnosis
receipt's, not the gate's, and it does differ after a rebuild of the recurrence journey: ledger row H-2 below.

## What else moved, deliberately

- **`tests/goldens/grade_application/history.json`**: three lines. The golden history's regrade replays its learning
  object, and that replay used to clear the first attempt's gate record. The golden had pinned the cleared values
  (`[]`, `[]`, `null`) in the live rows, and in the rebuild's added and removed rows. Now the record the gate wrote
  stays. Only those three columns of that one row differ (checked field by field against the regenerated file).
  Regenerated with `GRADE_APPLICATION_GOLDEN_WRITE=1`.
- **`tests/test_voi_stopping.py::test_each_follow_up_decision_keeps_its_own_receipt_through_rebuilds`**: one
  assertion changed. It pinned the defect: "The derived copy is gone (attempt_surprise is rebuilt without it)". That
  review (F1) had moved the value-of-information decision to its own immutable receipt (`followup_value_decisions`)
  because the copy on the surprise row did not survive a rebuild. The test now asserts that the copy survives the
  rebuild and the LO replay and equals the receipt's decision. Its other assertions, that the receipt stands
  unchanged and that a later decision is a new receipt, are unchanged.

## Found on the way: H-2

On the recurrence journey, a whole-vault rebuild changes the causal overlay of the first attempt's feedback. The
diagnosis receipt it renders has another `receiptId`, and one of its two hypotheses (the misconception's, "Believes
V and V transpose are the same matrix.") has a new `hypothesisId`. The other hypothesis and every statement are
unchanged. So a surrogate id the learner's history shows is reminted by replay, and anything keyed by that hypothesis
id across a rebuild would lose its target. Not investigated further here: it is not the gate's. Recorded as H-2
(open), for the orchestrator to place.

## Contract changes

- `ShadowRebuildResult.followup_gate_records` (new field), and `learnloop rebuild --shadow --json`'s new
  `shadow_rebuild.followup_gate_records` (counts only).
- The text output of `learnloop rebuild --shadow` gains one line.
- `Repository.attempt_surprise_gate_records(attempt_ids=None)` and
  `Repository.restore_attempt_surprise_gate_record(attempt_id, record)`, in the attempts store (the owner of
  `attempt_surprise`).
- `replay_learning_object(..., gate_records=None)` and `rebuild_derived_state(..., gate_records=None)`: optional
  keyword arguments.

No migration, no tag, no config field, no identity pin.

## Commands and results

Each pytest run: `-n 1 -p no:cacheprovider`, through the scratch wrapper, in a 3G scope.

| Command | Result |
|---|---|
| The new file on the base code, before the fix | 13 failed, 13 passed |
| The new file after the fix | 26 passed |
| 176 files: every test file that calls a rebuild, a replay, a regrade or the shadow rebuild, or reads `attempt_surprise`, the follow-up link or the pending list, plus identity pins, structure ratchets, architecture, test layout, the CLI help snapshot, the upgrades and the diagnosis journey golden; four chunks, `-m "not arc_close"` | 722 passed, 1 xfailed; 1173 passed, 1 failed (the grade-application golden); 946 passed; 1508 passed, 1 failed (the value-of-information test) |
| After the golden and the assertion above | `tests/test_grade_application_golden.py` 2 passed; `tests/test_voi_stopping.py` 65 passed |
| `uv run ruff check` / `uv run lint-imports --no-cache` | All checks passed! / Contracts: 54 kept, 0 broken. |

No identity pin moved. One slip in procedure: one single-file run (the grade-application golden, to read its
difference) started while the third chunk was still running, so two test commands ran at once for about five seconds.
Both finished normally.

## Not verified

- The landing gate and the full suite.
- A shadow rebuild of an owner copy with this code. On the copies the orchestrator ran, no row holds a gate record,
  so it would show `recorded_before` 0.
- Where H-2's reminted hypothesis id comes from.

## H-2: replay reverted a hypothesis and reminted its receipt (fixed, branch `refactor/h2-stable-receipt-ids`)

### What happened

A diagnosed attempt's causal record is versioned per episode (`causal_hypotheses`, a raw ledger). Live
materialization (`diagnosis/causal_attribution.py::materialize_causal_episode`) appends a version only when its
content differs from the episode's head (`db/stores/causal.py::append_causal_hypothesis`). It then writes a
content-addressed diagnosis receipt (`dr_<hash>`, which cites each hypothesis's id and version) into the attempt's
debug payload and sets the cause factor's refs.

Later live events append newer versions of the same episode:
- a recurrence promotion (status `validated`);
- a withdrawal (retired);
- a learner's confirmation.

Replay of the attempt (every whole-vault rebuild, every per-LO replay, a regrade's replay) called the same
materialization. It recomputed the attempt's own content, the first version's, and compared it with the head, now
the later live version. They differed, so it appended a third version: a copy of the first, with a fresh ULID
(`new_ulid()`), stamped at the attempt's time.

Every consequence followed from that one append:
- the episode's head went back to the first version's status, so a promotion, a withdrawal or a confirmation was
  silently undone for everything that reads the head;
- the receipt, rebuilt from the heads, cited the new id, so its content and its content-addressed id changed, and it
  was appended as the attempt's current receipt;
- an open cause factor's refs (`unresolved_cause_factors.candidate_causes_json`) would be rewritten to the new version.
  That is from the code: the journeys hold no open factor on these episodes.

**Not a timestamp or a counter:** the hypothesis id was a fresh ULID, and the receipt id changed because its content
cited that id.

On the recurrence journey, both misconception episodes (the first two attempts) were reverted on the first rebuild,
and the mid-check journey's one was too. A second rebuild appended nothing more: the reverted head then matched.

### Who reads these ids

**Hypothesis ids:**
- the receipt's citations, the overlay's `causalHypotheses`, `unverified` and `traceConsistency`;
- the cause factors' refs;
- mechanism taxonomy assignments;
- blind prediction bundles, probe candidates and decisions, cold outcomes;
- the would-merge log and `diagnosis_context_receipts.hypothesis_ids_json`;
- the learner's narrowing and confirmation actions, which the frontend sends by `hypothesisId`.

**Receipt ids:** `diagnosis_adjudications.diagnosis_receipt_id` and the overlay's `receiptId`.

**Was real data already orphaned?** Not as dangling ids: the earlier versions and receipts are never deleted, so every
stored reference still resolves. What was lost is attachment:
- after such a rebuild, the head and the attempt's current receipt are the replay's copies;
- an adjudication of the first receipt, a probe decision or a confirmation on the later version, and the frontend's
  remembered ids now point at rows history no longer shows as current;
- the hypothesis's status reads as before the promotion, withdrawal or confirmation.

Any owner vault rebuilt after such a live event carries this. A read-only signature for the orchestrator:

```sh
sqlite3 -readonly "$COPY_DB" "SELECT count(*) FROM causal_hypotheses h JOIN causal_hypotheses p ON p.id = h.supersedes_id WHERE h.created_at <= p.created_at;"
```

Replay stamps a version with the replayed attempt's time, so it is no later than its predecessor; a live append is
later. So this counts versions replay appended. The tracked `mvp017_route_check_replay` fixture holds one: its second
version carries the first's own time.

### The fix: carry the live version, never revert

- **`append_causal_hypothesis(..., replayed_from=[ids])`.** When the head differs, a version of the episode with
  identical semantic content is returned instead of appending a new one:
  - the version the attempt's recorded receipt cites is preferred;
  - otherwise the newest identical version;
  - with none identical (a regrade's new grade), a version is appended as live.

  The store reads the episode's versions through the new `causal_hypothesis_versions`.
- **`materialize_causal_episode(..., replay=True)`,** passed by the attempt step when it replays
  (`replace_existing`). It hands the recorded receipt's citations to the append. It builds the receipt and the factor
  refs from the versions live materialization used: the ones just reused, else the recorded receipt's, else the
  head. Ordered as live ordered them.
- **Result:** the receipt's content, and so its content-addressed id, is reproduced, and
  `append_attempt_diagnosis_receipt` (which dedupes by id) adds nothing. Live materialization is unchanged
  (`replay=False`).
- **The sibling in this path:** text provenance (`text_write_provenance`) rode on each reverting append, and goes with
  it. The other diagnosis-path ids (cause factor ids, repair class definitions, abstention notes) were not reminted:
  no rebuild of the 21 journeys added rows to them.

**Derive or carry?** Carry. A deterministic derivation of hypothesis ids would change every stored id, which is the
opposite of what is wanted. The receipt id is already content-derived and is reproduced once its content is.

**Vaults an earlier rebuild already reverted** keep exactly what they hold. The reverted copy is identical to the
first version and the current receipt cites it, so replay prefers it, and nothing moves. The fix stops further
reversions; it does not undo earlier ones.

**The owner's option:** a one-off script on a backup-API copy that appends, for each episode the signature above
finds, a version copying the live head it reverted (its predecessor's content: status, evidence). Then check it with
`doctor` and a shadow rebuild (which now reports appended ledger rows, below) before applying it with LearnLoop
closed. Receipts already appended stay; history's current receipt then still cites the reverted copy, whose
statement is the first version's.

**A replay-made version from older code** (the fixture's second version) is handled the same way. Its first version
is identical to what replay computes today, so replay reuses it and appends nothing. The head stays the stored
second version. Before the fix the first rebuild appended a third (a copy of the first), and
`tests/test_mvp017_route_check_replay.py::test_the_bounded_replay_corrects_the_copy_in_one_rebuild_and_then_changes_nothing`
pinned that append and the recurrence restamp it caused. Its expected list of tables changed by the first rebuild
loses `causal_hypotheses` and `hypothesis_recurrence_state`. Its other assertions are unchanged: the second rebuild
changes nothing, and the ledgers are as before.

### The tag question

**No tag**, for the same reasons as H-1:
- no live write changes;
- a rebuild now reproduces the stored hypotheses, receipts and refs, and appends nothing to a raw ledger;
- a vault already reverted is replayed to exactly what it holds.

### The shadow rebuild now shows ledger growth

`ShadowRebuildResult.ledger_rows_added` (and `as_dict()["ledger_rows_added"]`): rows the replay added, by ledger or
receipt table (`db.table_roles`), counts only. Before this change the shadow rebuild compared only derived
projections, so it could not have shown H-2. It shows:
- the rebuild's own receipt (`derived_state_rebuilds`, +1, always);
- one-time backfills on vaults that never ran them;
- anything a replay appends that it should not.

### Tests

- **`tests/test_replay_keeps_diagnosis_ids.py`, 24 tests:**
  - for all 21 journeys, every hypothesis (id, version, head, status), every receipt (current id, citations, the
    list) and every factor's refs are equal before and after a whole-vault rebuild;
  - the recurrence journey's two promoted episodes stay promoted and their receipts keep their ids, with every
    reference still resolving;
  - a per-LO replay appends no version;
  - the shadow rebuild reports no diagnosis-ledger rows added, no gate record changed and no difference in facets or
    schedules. The recurrence journey's vault never ran the bootstrap, so the rebuild adds a cold mastery row for each
    LO with no attempt, as the rebuild says it must.
- **`tests/test_gate_records_survive_replay.py::test_what_history_shows_reads_the_same_after_a_rebuild`** no longer
  leaves out the causal overlay.
- **Fail-first:**
  - with `src` at the H-1 tip, 6 failed: the mid-check and recurrence journeys, the promoted-episode test, the
    per-LO replay, the shadow test and the history test;
  - with the shadow change alone, the shadow test failed on `causal_hypotheses` and `text_write_provenance`;
  - after the fix, all 50 tests in the two files passed.
- **Affected set:** 190 files (every test naming causal hypotheses, materialization, diagnosis receipts, the
  rebuilds, replay or regrades, plus pins, ratchets, architecture, layout, the CLI snapshot, upgrades and both
  goldens), four chunks, `-m "not arc_close"`: 719, 1350 (1 xfailed), 1047 and 1470 passed, with 2 failures:
  - the fixture test above, which pinned the old append;
  - the structure ratchet, one line over in `attempts/attempts.py`, fixed by keeping the call's line count.

  Then those two files and the two new ones: 56 passed. `ruff`: all checks passed. `lint-imports`: 54 kept,
  0 broken.

### Found on the way: H-3

Every whole-vault rebuild of the cold-check and deterministic-classification journeys appends rows to
`raw_grade_events`, `measurement_events`, `grade_interpretations` and `activity_observations`: 3, 12, 3 and 3 rows
on each cold-check journey, every rebuild, not once. A second rebuild adds them again. This is the grading and
measurement substrate, not the diagnosis path, so it is not fixed here. Recorded as H-3 (open). The shadow rebuild's
`ledger_rows_added` now shows it on any vault.

## H-3: rows a rebuild appends to raw ledgers (branch `refactor/h3-replay-appends-raw-ledgers`)

(The ledger row H-3, not arc H's step H3.)

### What writes them, and when

The writer is the grade channel's dual write in the attempt step, reached from replay:
`attempts/attempts.py::_dual_write_grade_channel` → `grade_resolution.record_grade_dual_write` →
`ensure_administration_identity` → `substrate/activities.py::open_administration` and `append_observation`, then the
raw grade event, the interpretation and the measurement events.

From the grade channel fixes on (mvp-0.60, `GRADE_CHANNEL_FIX_VERSIONS`, refactor bug ledger D-36 and D-52), a
replay instead reuses the attempt's newest observation (`record_replayed_grade`) and appends only what changed. Below
that tag, a rebuild re-mints each answer's whole chain every time, as the predecessor did. That is kept on purpose so
the predecessor replays as it did, and `tests/test_rebuild_history_appends.py` pins it.

The journeys that showed the growth (cold pass, cold fail, deterministic classification) run at mvp-0.7, below the
version floor (mvp-0.58), under the tests' allowance. **So H-3 is D-36 seen at an old tag, not a new defect at the
head.** Nothing at mvp-0.60 or later re-mints a chain on a second rebuild.

### The sweep

A new guard, `tests/test_replay_writes_no_ledger.py`, covers all 21 journeys plus the grade-application golden's
broad history at the head (self-graded, model-graded, hinted, primed, "I don't know", stuck, unassessed, held, a
repeat and a sibling, the blind door, a regrade, an adjudication). On each it runs one whole-vault rebuild, then two
more, then two rounds of per-LO replay of every LO, counting rows in every `RAW_LEDGER` and `RECEIPT` table
(`db.table_roles`).

- **The second and third rebuilds** add exactly their one rebuild receipt (`derived_state_rebuilds`) and nothing
  else.
- **Per-LO replays** add nothing.
- **Exception:** a vault below the grade channel fixes may add the grade chain's tables (`activity_observations`,
  `raw_grade_events`, `grade_interpretations`, `measurement_events`, `activity_administrations`), the predecessor's
  rule. No other table.
- **The first rebuild** may add only one-time rows, listed in the test as `FIRST_REBUILD_BACKFILL`:
  - the activity substrate's backfill of cards, surfaces and families for unanswered items;
  - administrations, exposures and observations for answers recorded without them;
  - outcome schemas and mastery seeds a vault never recorded;
  - the grade channel's one reconciliation of a grade the ledger lags. The broad history's first rebuild adds one raw
    grade event, one interpretation and three measurement events for that, D-36's "only what changed".

  A second rebuild adds none of these.

The guard is fail-first for H-2's class: with `src` at the H-1 tip (before H-2), it fails on the mid-check and
recurrence journeys, where the first rebuild appends `causal_hypotheses` and `text_write_provenance`. At this tip,
22 passed.

### Does anything drift with the number of rebuilds?

No scored or learner-visible number. On a vault rebuilt below mvp-0.60, every reader of the duplicated chains reads
each attempt's newest observation:
- the authoritative observation ledger and the projection (`db/stores/observation_ledger.py`);
- the review queue (fixed by D-36);
- the field's grader-model read (`field/outcomes.py::_grader_models`);
- the router check's quarantine read (`router_objective/checks.py`);
- the first cold administration per contract (`db/stores/activity.py`, first by time).

D-36 found the derived tables equal after each rebuild. The one real harm below the tag, an owner adjudication lost
to the next rebuild (D-52), is fixed from mvp-0.60 on. What remains is storage: one extra chain per graded answer per
rebuild run while the vault was below mvp-0.60.

### Existing vaults: leave the rows, an owner option

Nothing here deletes a raw row. Signature, read-only:

```sh
sqlite3 -readonly "$COPY_DB" "SELECT count(*) AS attempts_with_copies, coalesce(sum(n - 1), 0) AS extra_observations FROM (SELECT attempt_id, count(*) AS n FROM activity_observations WHERE attempt_id IS NOT NULL GROUP BY attempt_id HAVING n > 1);"
```

From mvp-0.60 an attempt keeps one observation, so more than one means rebuilds below the tag re-minted it.

**Owner options:**
- **(a) Leave them (recommended).** Every reader takes the newest. The cost is storage.
- **(b) A one-off compaction on a copy.** Remove every observation but the newest per attempt, with its raw event,
  interpretations and measurement events, then check with doctor and a shadow rebuild. That is a write to raw
  ledgers and needs the owner's explicit decision, outside this landing.
- **(c) Move the version floor to mvp-0.60 or later (ADR-019).** The owner copies are at mvp-0.68. Then no supported
  vault can re-mint chains, and the predecessor path and its test can go, retiring the class rather than guarding it.

### Tag and migration

None: this landing changes no source file. It adds the guard test and the record.
