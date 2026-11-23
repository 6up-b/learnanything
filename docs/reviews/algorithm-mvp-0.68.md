# mvp-0.68: a scratchpad's words are learner text (Reader workbench v2, RD4a)

Branch `reader/rd4a-pads-backend`, from origin/main `b495b1e67f` (latest tag `mvp-0.67`, migration head 265). The
spec is `docs/specs/spec_reader_workbench_v2.md` §10.11 (the contract per its review's F4), §15.2 and §15.3's RD4 row
("yes: `pad_text` gaps start steering hypotheses and routing"); the stage's own record is `docs/reviews/reader-rd4a.md`.
Everything here was measured on synthetic vaults and fakes; the owner's vaults are the orchestrator's (the last
sections).

| Commit | What |
|---|---|
| `93dad1ea31` | Migration 266: the five RD4 tables, `pad_text` in both gap tables, the two pad reversals; roles; the earlier migrations' diffs |
| `e7f4ec2af7` | The head fixture upgraded from 265 to 266, on its own |
| `26b818ddd4` | The tag: one constant, the chain entry, its set and predicate, one upgrade row, one test row; the mechanical moves by the tag string |
| `2aa49765a4` | The behaviour (emission, the pipeline's `pad_text` adapter and span recipe, the reconcile hooks) with the rest of RD4's backend (submission, carried questions, proposals, the drain, their RPCs, the fences) and their tests |
| `fab1b3efa4` | Rust passthroughs and typed client calls |
| (this record) | This record, `reader-rd4a.md`, the G2 design renumbered to `mvp-0.69` in its proposal lines, ledger row RD4a-1 |

One migration (266), no config key, no kill switch (owner rule 2026-11-16), no prompt text changed (the reader's task
for the new kind is the note reader's; the Decider's state gains one sentence naming the kind).

## What changes

Before the tag the workbench's pads (migration 262) held the learner's own writing as workflow data that nothing
read. At the tag:

- **What is emitted**: a committed block version of the learner's own words, a `text` or `note` block of provenance
  `learner`, an `ink` block's transcription (`ink_transcription`) or its correction (`learner_correction`), not
  removed and not blank. Quoted source, tutor and figure blocks, sketches, cells, check cells and lift-out stubs emit
  nothing, so a pad of quotes emits nothing.
- **How**: through `learnloop.pads.emission` alone (import fence 1's exit). After a pad batch commits, each touched
  block's current wording is queued once as a `learner_text_gap_jobs` row of source kind `pad_text` whose
  `source_id` is the version where those words were written (a move, or a lift into a pad of its own, keeps the
  words and so keeps their reading), with a frozen snapshot in the job's payload: the words, whether they were
  transcribed from handwriting, whether they include a quote, the passages the block (or the quote it is a note
  under) is linked to, and the problem pad's workbench session. The gap pipeline reads that snapshot
  (`diagnosis.text_gaps.sources.pad_text`), never a pad table, as the note reader reads a note, and writes its
  `learner_text_gaps` row (source kind `pad_text`, the version as source) with its passages in `detail_json`.
- **Effects** (`diagnosis/text_gaps/contract.py`): `pad_text` is in `READABLE_SOURCE_KINDS` and
  `NON_SERVING_SOURCE_KINDS`. Its gaps name a prerequisite or a belief, become hypotheses, inform the companion, the
  Teacher and the router's learner state (every reader of named gaps reads them), and may create a topic or a
  misconception candidate through the pipeline's holding pen and caps. They never bring a check forward and are never
  a weak prerequisite observation for placement (`field.signals`, the sooner check), and never feed mastery,
  readiness or certification.
- **Quoted by the learner**: a block containing a whole sentence of one of the pad's quote blocks or of a linked
  passage is queued as the learner's text but never read for a gap: its row has kind `none`, action `none`, reason
  `quoted_by_learner`, and no model call is made.
- **Corrections supersede**: when a block's words change, every gap read from its earlier words gets one
  `superseded` reversal (the row stays), and a reading of earlier words still queued is set aside unread
  (`skipped`). **Tombstones retract**: a removed block's gaps get one `retracted` reversal. A reading already under
  way when its words were replaced finishes and writes its gap; the reconcile that runs after every gap drain (and
  when a vault opens) sets it aside.
- **Idempotent**: everything is keyed by the wording's version; the reconcile re-run changes nothing.

Below the tag a pad emits nothing, exactly as at mvp-0.67 (`pad_text_on`, tested). Reversals never wait for the tag
or the pipeline's switch (a gap read from words that no longer stand must not keep steering), but none can exist below
it. Emission waits for `learner_text_gaps.enabled`, like every other learner text; switched on again, the reconcile
queues the standing words.

## The tables (migration 266)

`learner_text_gaps.source_kind` and `learner_text_gap_jobs.source_kind` gain `pad_text`, and
`learner_text_gap_reversals.reversal` gains `superseded` and `retracted`: each table rebuilt temp-then-rename as 235
and 248 were, every row, index and trigger kept, the definitions changed in their CHECK alone. The five RD4 tables
(`pad_block_submissions`, `carried_questions`, `carried_question_events`, `pad_proposals`, `proposal_labels`) are
the stage's, described in `docs/reviews/reader-rd4a.md`; nothing that scores, schedules or certifies reads them.

## Playbook ruling and activation

The playbook's test (step 1): the change alters persisted meaning (from the tag on, the router's learner state, the
companion and the Teacher read gaps named from pad text, and the gap pipeline creates topics and candidates from it).
So a tag: `mvp-0.68`, the immediate successor of `mvp-0.67` (step 3), no kill switch.

- `PAD_TEXT_ALGORITHM_VERSION = "mvp-0.68"`, appended to `SUCCESSOR_CHAIN`; `PAD_TEXT_VERSIONS`; the one predicate
  `pad_text_on(config)`.
- **`Link(mvp-0.68, idempotent_projection)`**: only blocks committed from the upgrade on behave differently, and
  nothing already derived reads a pad (fence 1), so no rebuild and no activation of its own. Existing pad rows need
  nothing at the upgrade: the pads' own reconcile, run when the sidecar opens the vault, queues the words standing
  then (superseded versions are never queued). No UI wrote pads before RD4's frontend, so the owner's vaults are
  expected to have none (the counts script below says).
- `tests/test_upgrades.py`'s `EXPECTED_ACTIVATIONS` gains the row; the table's tests run over it (activation,
  recovery, re-run, refused jump).

## Pins and goldens that moved

- **The tag commit, by the tag string alone** (as at mvp-0.62 to mvp-0.67): `tests/goldens/identities.toml` the same
  nine pins (`A1-A4.manifest_hash.init`, `C3.boundary.init`, `C3.boundary_offer.init`, `C3b.chooser`,
  `C3b.chooser_offer`, `C3b.start_key`, `C3b.start_key_offer`, `C5.init`, `C6.init`), `--write`;
  `tests/goldens/effective_defaults.toml` (the algorithm line, `--write`); `tests/cli_surface.json` (`upgrade --to`'s
  default, by hand); `tests/goldens/placement_stored_misses.json` (its manifest's tag); the journey golden (320 tag
  strings and its two decision states' `config` and `snapshot_hash`, nothing else); latest-tag and chain-position pins
  in 42 earlier successors' test files: every negative `SUCCESSOR_CHAIN[-n]` index (n > 1) and every negative slice
  bound one further (two-sided slices included), `mvp-0.68` appended to tails and to the version sets that include
  every later tag, the fresh-vault tag in `test_ad23_successor`, `test_serve_eligibility_review` and
  `test_intent_codex_rereview`; `tests/test_teacher_te1_successor.py`'s mixed tail (`"mvp-0.67"` inserted before
  `LATEST_ALGORITHM_VERSION`, by hand); the mastery seed's own tag test names its places from the end and its version
  set gains `mvp-0.68`.
- **The behaviour commit**: no identity pin moved and none was added.No row-recording golden moved: the journey, grade-application,
  synthesis-tail and due-queue goldens pass unchanged (none of their journeys writes a pad, so no new table gains a
  row in them and no gap of kind `pad_text` exists there). The structure golden needed no change.
- **The migration commit**: `RD4_ADDED_OBJECTS` subtracted in the earlier migrations' "nothing else changed" diffs
  (`tests/reader_rd4_migration_helpers.py`); AD2+AD3's 218 diff admits the three rebuilt tables
  (`RD4_ALTERED_TABLES`); the TE2 migration test undoes 266's schema before its own downgrade and compares with the
  head as 248 left it (`undo_266`). No assertion was loosened: each change admits exactly 266's objects.

## Tests

See `docs/reviews/reader-rd4a.md` §6 for the files and the fail-first evidence; the emission contract is
`tests/test_reader_rd4_emission.py` (the RD4 row's three: quote-only pads emit nothing, corrections supersede,
tombstones retract; plus idempotence, the tag, the switch, moves and lifts, ink, readings finished during an edit,
quoted text, and the live span projection equal to a rebuild).

## What the orchestrator must run on owner copies

On backup-API copies (never a live vault), each at `mvp-0.67`, from the landed tip, with the scratch wrapper's
isolation. One read-only script (counts only; it attaches the database read-only, writes nothing and calls no model):

```python
# pad_text_counts.py <copy root>: scratchpads and their learner text, counts only (reads the database read-only,
# writes nothing, calls no model)
import json, sqlite3, sys
from collections import Counter
from contextlib import closing
from pathlib import Path

from learnloop.algorithm_versions import PAD_TEXT_VERSIONS
from learnloop.db.stores import pad_reads
from learnloop.pads import emission
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

vault = load_vault(Path(sys.argv[1]))
database = VaultPaths(vault.root, vault.config).sqlite_path
version = vault.config.algorithms.algorithm_version
out = {"algorithm_version": version, "pad_text_on": version in PAD_TEXT_VERSIONS,
       "pipeline_enabled": bool(vault.config.learner_text_gaps.enabled)}
with closing(sqlite3.connect(f"file:{database}?mode=ro", uri=True)) as connection:
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    one = lambda sql: connection.execute(sql).fetchone()[0]
    if "pads" in tables:
        out["pads"] = one("SELECT COUNT(*) FROM pads")
        out["block_versions"] = one("SELECT COUNT(*) FROM pad_block_versions")
        blocks = pad_reads.block_ids(connection)
        heads = [pad_reads.head(connection, block) for block in blocks]
        out["blocks_by_head_kind"] = dict(sorted(Counter(
            "removed" if head["tombstone"] else f"{head['kind']}|{head['provenance']}" for head in heads if head).items()))
        standing = {str(words["version_id"]) for words in
                    (emission.words_version(emission.lineage(connection, block)) for block in blocks) if words}
        out["standing_learner_words"] = len(standing)
    if "pad_block_submissions" in tables:
        jobs = dict(connection.execute(
            "SELECT source_id, state FROM learner_text_gap_jobs WHERE source_kind = 'pad_text'").fetchall())
        gaps = dict(connection.execute(
            "SELECT source_id, id FROM learner_text_gaps WHERE source_kind = 'pad_text'").fetchall())
        reversed_gaps = {row[0] for row in connection.execute(
            "SELECT gap_id FROM learner_text_gap_reversals WHERE reversal IN ('superseded', 'retracted')")}
        out["pad_text_jobs_by_state"] = dict(sorted(Counter(jobs.values()).items()))
        out["pad_text_gaps_by_kind"] = dict(sorted(Counter(row[0] for row in connection.execute(
            "SELECT kind FROM learner_text_gaps WHERE source_kind = 'pad_text'")).items()))
        out["pad_text_reversals_by_kind"] = dict(sorted(Counter(row[0] for row in connection.execute(
            "SELECT r.reversal FROM learner_text_gap_reversals AS r JOIN learner_text_gaps AS g ON g.id = r.gap_id "
            "WHERE g.source_kind = 'pad_text'")).items()))
        emits = out["pad_text_on"] and out["pipeline_enabled"]
        out["would_queue_on_open"] = len(standing - set(jobs) - set(gaps)) if emits else 0
        out["gaps_on_words_no_longer_standing_and_not_set_aside"] = sum(
            1 for source_id, gap_id in gaps.items() if source_id not in standing and gap_id not in reversed_gaps)
        out["submissions_by_kind"] = dict(sorted(Counter(row[0] for row in connection.execute(
            "SELECT submitted_as FROM pad_block_submissions")).items()))
        out["carried_by_state"] = dict(sorted(Counter(row[0] for row in connection.execute(
            "SELECT state FROM carried_questions")).items()))
        out["proposals"] = one("SELECT COUNT(*) FROM pad_proposals")
        out["proposal_labels_by_label"] = dict(sorted(Counter(row[0] for row in connection.execute(
            "SELECT label FROM proposal_labels")).items()))
print(json.dumps(out, sort_keys=True))
```

Per copy (publish counts only):

1. `pad_text_counts.py` at `mvp-0.67`: **pads, block versions, blocks by head kind, standing learner words** (expected
   0 everywhere: no UI wrote pads).
2. `learnloop rebuild --shadow --json --vault "$COPY"` at `mvp-0.67` (mastery, facet, schedule changed: the baseline).
3. Apply migration 266 with the landed code (opening the copy does it), then `learnloop upgrade --vault "$COPY" --to
   mvp-0.68`, `learnloop doctor --vault "$COPY"`, `PRAGMA integrity_check`, `PRAGMA foreign_key_check`; the schema diff
   is 266's 28 objects and the three rebuilt tables, rows changed only in `schema_migrations`.
4. `pad_text_counts.py` at `mvp-0.68`: `pad_text_on` true, **`would_queue_on_open`** (the words the first sidecar open
   queues; expected = `standing_learner_words`, 0 on a copy with no pads), no `pad_text` job or gap yet, every RD4
   table empty.
5. `learnloop rebuild --shadow --json` at `mvp-0.68`: **0, 0, 0 and no due date moved** (nothing derived reads a pad).
6. Verify the live databases' SHA-256 unchanged.

On a scratch-built demonstration vault (`learnloop init`, its tag set to `mvp-0.67`, one pad written through
`pad.apply`'s core: a quote, a text block edited once, a removed text block), through the CLI and the script: step 1
gave 1 pad, 5 block versions, heads `removed` 1, `source_quote|source` 1, `text|learner` 1, 1 standing learner wording,
no job and `would_queue_on_open` 0 (`pad_text_on` false); step 2's shadow 0, 0, 0, no due date moved, the database
unchanged; step 3's upgrade `mvp-0.67 -> mvp-0.68`, `learnloop doctor` exit 0, `integrity_check` ok, no foreign-key
violation; step 4 `would_queue_on_open` 1 and no job yet; the pads' reconcile (what the sidecar's open runs) queued the
edited block's last wording only (`v1b`: not the superseded `v1`, not the removed block, not the quote), after which
`would_queue_on_open` 0 and one queued `pad_text` job; step 5's shadow 0, 0, 0, no due date moved, the database
unchanged.

## Limitations

- Words committed before the tag are emitted at the first open after the upgrade, with the passages linked then (not
  those at their writing); their versions' timestamps are kept as `written_at`.
- A block written during an open check administration is emitted at once: administrations arrive with RD7, which owns
  that rule (§10.11 "During an open check").
- The quote check is lexical (a whole sentence, word for word): a paraphrased source sentence is the learner's.
- Carried questions do not reach the router or the Teacher yet (an open design question, `reader-rd4a.md` §5).
