# mvp-0.69: inline cold checks in the Reader (Reader workbench v2, RD7a)

Branch `reader/rd7a-inline-checks-backend`, from RD10's tip, with origin/main and `reader/rd8fix` merged in (latest
tag `mvp-0.68`, migration head 269). The spec is `docs/specs/spec_reader_workbench_v2.md` §12.6 (corrected to the
owner's three rulings of 2026-11-23), §3.4's `check.*` rows and §15; the stage's own record is
`docs/reviews/reader-rd7a.md`. Everything here was measured on synthetic vaults and fakes. The owner's vaults are the
orchestrator's (the last sections).

| Commit | What |
|---|---|
| `ff07150c56`, `1debb36a94` | Migration 270: `check_administrations` (WORKFLOW), `check_veil_sets` (RECEIPT), and the video chapters' replacement guard (RD10-10); roles; the earlier migrations' diffs subtract 270's objects |
| `c3f092a442` | The head fixture upgraded from 269 to 270, on its own |
| `a0873aa32f` | The tag: one constant, the chain entry, its set and predicate, one upgrade row, one test row; the mechanical moves by the tag string |
| `b945497d8c` | The behaviour: the administration protocol, the lock Today honours, its RPCs and tests |
| `b2c7dccfdb` | Rust passthroughs and typed client calls |
| (this record) | This record, `reader-rd7a.md`, the spec's §12.6 corrections, the G2 design renumbered to `mvp-0.70` in its proposal lines, ledger RD10-10 fixed |

One migration (270), no config key, no kill switch (owner rule 2026-11-16), no prompt and no model call of its own
(the attempt service grades as it always does).

## What changes

Before the tag a due "Check once" is answered only where Today serves it. At the tag:

- **A new serving surface** (`reader_inline`). `check.begin_inline` serves the item Today's check view would serve.
  It goes through Today's own session serve (`get_practice_item` with the desks' practice session), so the
  assessment contract is frozen and the check's view is shown exactly as in Today. The answer goes through the one
  attempt service (`submit_attempt_on`, recorded with `entry_surface = 'reader_inline'`). Settlement then runs as for
  any qualifying attempt (`settle_answered_checks`): the first on-your-own, cold attempt answers the check, whatever
  surface it came from.
- **A lock Today honours.** While an inline administration is open on a commitment:
  - Today's build does not serve its items as the check (`IntentServing.pick_checks` drops them).
  - Today's serve of the item says "being answered in the Reader" and is practice (`served_check`).
  - The due-check rows carry `being_answered`.
  - One administration is open at a time (a partial unique index).
  - The Reader refuses to open a check whose item has an answer being written in an open Today session.
- **Exposure written at once by a new writer** (owner ruling Q1, the existing overlap rule). Opening a veil writes a
  `source_review` reveal on each of the check's candidates, sized by the opened text's overlap with that candidate's
  answer key (`tutor_qa.span_answer_overlap`; basis `check_inline:opened_veil`). The Check once decision reads the
  reveal ledger as it always does: the answer is practice only if the reveal primes the item. Navigating writes no
  reveal; help is the hint path's, which the attempt service already folds in.
- **Veils by default** (owner ruling Q2). Every note-bearing surface on every desk is veiled when a check opens: pads,
  lessons, threads, the companion's history, margin notes, and every window but a source's text, whole. The check's
  LO's covered passages are veiled by structure. There is no "counts as practice" rule for what was on screen before
  the veils dropped, so evidence is decided by the reveal ledger alone. The Decider's judgment, later, may only
  un-veil (`inline_administration.narrow`).
- **Opened notes are unmeasured, and the answer counts as practice** (confirmed by the owner, 2026-11-23). A note's words are never read (curriculum C2's fence: a note is never evidence). The veil set names the notes the
  client showed by id only, and opening a note's veil (a margin note or any `learner_notes`-backed surface) writes no
  reveal: the exposure event lists it under `unmeasured_notes`. Because whether an unread note gave the answer away
  cannot be told, the answer errs toward practice: `check.submit_inline` submits it with the attempt's declared `primed`
  flag (`inline_administration.notes_opened`), and the reply says `reason: primed` with `primed_by: unmeasured_note`. The
  flag a rebuild reads is the attempt row's own `practice_attempts.primed` (raw), written at submit; replay equality is
  tested (`test_an_answer_after_a_notes_veil_was_opened_is_practice_and_says_why`). Measured surfaces (pads, companion
  exchanges, source passages) keep the overlap rule exactly as built.
  
  **Confirmed by the owner (2026-11-23):** opening one of your own notes during a cold check counts as practice. The
  alternative it was weighed against, kept as history: an unmeasured opening costs nothing (the answer stays cold unless
  something measured primes it).
- **A later answer on the other surface** (owner ruling Q3, the existing rule) answers nothing and stays ordinary
  evidence; the reply labels it practice (`reason: already_answered`).

Below the tag every `check.*` administration RPC refuses (`below_tag`) and Today ignores the lock, exactly as at
mvp-0.68 (`inline_checks_on`, tested).

## The tables (migration 270)

- **`check_administrations` (WORKFLOW).** The token, the request id (unique: a retried begin is the same
  administration), the commitment, the surface, the session, the item, the contract, whether it was cold when served,
  the state (`open`, `submitted`, `abandoned`, `superseded`), the protection method, the exposure record, the
  submission id (unique; named before the attempt so a crash after it is recoverable), the attempt id, and the
  timestamps. A trigger makes a closed row final, and rows are never deleted.
- **`check_veil_sets` (RECEIPT, append-only by triggers).** One row at the opening, one per `protect_more` with new
  veils, one per opened veil, and one at the close: what was veiled and what had been opened by then.
- **`video_chapters_no_replace_decided`.** RD10's review, finding 10: an insert reusing a decided chapter's id is
  skipped.

Nothing that scores, schedules, certifies or replays reads these tables.

## Playbook ruling and activation

The playbook's test (step 1): the change alters persisted meaning. From the tag on, attempts from a new surface answer
checks, a lock changes what Today serves while it is held, and a new writer adds reveals that the `CHECK_ONCE` and
`SUBMIT` decisions read. So a tag: `mvp-0.69`, the immediate successor of `mvp-0.68` (step 3), with no kill switch.

- `INLINE_CHECK_ALGORITHM_VERSION = "mvp-0.69"`, appended to `SUCCESSOR_CHAIN`; `INLINE_CHECK_VERSIONS`; the one
  predicate `inline_checks_on(config)`.
- **`Link(mvp-0.69, idempotent_projection)`.** Only administrations from the upgrade on behave differently, and none
  exists before migration 270. Every effect on evidence is an ordinary attempt or reveal row, which the projection
  already reads, so no rebuild and no activation of its own.
- `tests/test_upgrades.py`'s `EXPECTED_ACTIVATIONS` gains the row. The table's tests run over it: activation,
  recovery, re-run and refused jump.

## Pins and goldens that moved

- **The tag commit, by the tag string alone** (as at mvp-0.62 to mvp-0.68):
  - `tests/goldens/identities.toml`: the same nine pins (`A1-A4.manifest_hash.init`, `C3.boundary.init`,
    `C3.boundary_offer.init`, `C3b.chooser`, `C3b.chooser_offer`, `C3b.start_key`, `C3b.start_key_offer`, `C5.init`,
    `C6.init`), regenerated with `--write`.
  - `tests/goldens/effective_defaults.toml`: the algorithm line, `--write`.
  - `tests/cli_surface.json`: `upgrade --to`'s default, by hand.
  - `tests/goldens/placement_stored_misses.json`: its manifest's tag.
  - The diagnosis journey golden: its tag strings and its two decision states' `config` and `snapshot_hash`, nothing
    else; 324 lines, `DIAGNOSIS_JOURNEY_WRITE_GOLDEN=1`.
  - Latest-tag and chain-position pins in 46 earlier successors' test files, moved mechanically:
    - every negative `SUCCESSOR_CHAIN[-n]` index (n > 1) and every negative slice bound one further;
    - `mvp-0.69` appended to tails and to the version sets that include every later tag;
    - the latest and fresh-vault tags;
    - the pad text tag test names its places from the end.
- **The behaviour commit**: no identity pin moved and none was added. Assertions changed:
  - `tests/test_reader_rd0_reads.py`: a due check row now carries `being_answered: False`.
  - `tests/test_mobile_allowlist.py`: RD0's pin now covers `checks.due_for` alone among the inline check RPCs; RD7's
    six are pinned on their own.
- **The migration commits**: `RD7A_ADDED_OBJECTS` subtracted in the earlier migrations' "nothing else changed" diffs
  (`tests/reader_rd7a_migration_helpers.py`). RD10's migration test compares with the head as 268 left it, without
  270's guard on its table. No assertion was loosened: each change admits exactly 270's objects.

## Tests

`tests/test_reader_rd7a_inline_checks.py` (19) and `tests/test_reader_rd7a_migration.py` (7). The protocol's rules each
fail with their line removed (shown, `reader-rd7a.md` §5):

- the lock;
- the reveal an opened veil writes;
- the settlement after submit;
- the crash recovery after the attempt;
- supersession;
- the refusal while Today has an answer being written.

They also cover:

- the parity with Check once in Today;
- a crash at each transition;
- the live projection equal to a whole-vault rebuild.

## What the orchestrator must run on owner copies

On backup-API copies (never a live vault), each at `mvp-0.68`, from the landed tip, with the scratch wrapper's
isolation. One read-only script (counts only; it attaches the database read-only, writes nothing and calls no model):

```python
# inline_check_counts.py <copy root>: due checks, inline administrations and their reveals, counts only (reads the
# database read-only, writes nothing, calls no model)
import json, sqlite3, sys
from collections import Counter
from contextlib import closing
from pathlib import Path

from learnloop.algorithm_versions import INLINE_CHECK_VERSIONS
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

vault = load_vault(Path(sys.argv[1]))
database = VaultPaths(vault.root, vault.config).sqlite_path
version = vault.config.algorithms.algorithm_version
out = {"algorithm_version": version, "inline_checks_on": version in INLINE_CHECK_VERSIONS}
with closing(sqlite3.connect(f"file:{database}?mode=ro", uri=True)) as connection:
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    one = lambda sql: connection.execute(sql).fetchone()[0]
    out["test_me_later_commitments"] = one("SELECT COUNT(*) FROM commitments WHERE created_action = 'test_me_later'") \
        if "commitments" in tables else None
    out["reveals_by_basis_check_inline"] = one(
        "SELECT COUNT(*) FROM reveal_events WHERE basis LIKE 'check_inline:%'") if "reveal_events" in tables else None
    out["attempts_on_reader_inline"] = one(
        "SELECT COUNT(*) FROM practice_attempts WHERE entry_surface = 'reader_inline'")
    if "check_administrations" in tables:
        out["administrations_by_state"] = dict(sorted(Counter(row[0] for row in connection.execute(
            "SELECT state FROM check_administrations")).items()))
        out["veil_sets"] = one("SELECT COUNT(*) FROM check_veil_sets")
    if "video_chapters" in tables:
        out["video_chapters_by_state"] = dict(sorted(Counter(row[0] for row in connection.execute(
            "SELECT state FROM video_chapters")).items()))
print(json.dumps(out, sort_keys=True))
```

Per copy (publish counts only):

1. `inline_check_counts.py` at `mvp-0.68`: `test_me_later` commitments (the checks that could be administered
   inline), and **0 reveals of basis `check_inline:`, 0 attempts on `reader_inline`**.
2. `learnloop rebuild --shadow --json --vault "$COPY"` at `mvp-0.68` (mastery, facet, schedule changed: the baseline).
3. Apply migration 270 with the landed code (opening the copy does it). Then run:
   - `learnloop upgrade --vault "$COPY" --to mvp-0.69`;
   - `learnloop doctor --vault "$COPY"`;
   - `PRAGMA integrity_check`;
   - `PRAGMA foreign_key_check`.

   The schema diff is 270's objects (two tables, their indexes and triggers, the video chapters' guard); rows change
   only in `schema_migrations`.
4. `inline_check_counts.py` at `mvp-0.69`: `inline_checks_on` true, `administrations_by_state` `{}`, `veil_sets` 0,
   the video chapters' counts unchanged.
5. `learnloop rebuild --shadow --json` at `mvp-0.69`: **0, 0, 0 and no due date moved**, except the rows'
   algorithm-tag stamp, as at mvp-0.68: this upgrade row is an idempotent projection, so live rows keep their stamp
   while the shadow stamps `mvp-0.69`.
6. Verify the live databases' SHA-256 unchanged.

## Limitations

- An exposure retried after a lost reply writes its reveal again (`check.expose` has no idempotency key in §3.4). The
  ledger then over-counts that opening, which errs towards practice, never towards a cold credit that was not earned.
- The item an inline check serves is its first servable candidate in id order. Today ranks candidates by the build's
  queue, so with several eligible candidates the two surfaces can pick different items, each frozen and graded by
  the same rules.
- The Reader-side lock reads Today's open session checkpoints: an item shown in Today with an answer being typed. A
  Today serve with nothing typed yet does not hold the check; the first settling attempt wins, as always.
- A lesson's quick question (RD9a-3's interim) stays on the lesson screen; see `reader-rd7a.md` §6.

## Owner copies (run by the orchestrator)

Not run yet.
