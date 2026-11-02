# followups-batch5: Codex review fix round

Codex review job 20261102-102846-iWwlFV, of branch `fix/followups-batch5` at 51f52be349. It found two High
findings, both in item A (recap protection). The fix is in a9107bae28. No schema, migration, parameter,
grading, evidence or network change. No live calls were made, and every model in the tests is a fake.

## Findings

| id | severity | title | verdict | commit | test / reason |
|---|---|---|---|---|---|
| F1 | High | A recap loses the protection dependencies of the earlier recaps its lesson was given | fixed | a9107bae28 | `tests/test_followups_batch5_recap_dependencies.py::test_f1_*` (4) |
| F2 | High | A recap bypasses the protection on the Reader notes its lesson was given | fixed | a9107bae28 | `tests/test_followups_batch5_recap_dependencies.py::test_f2_*` (5) |

Reproduction: the 9 new tests were written first. 7 of them failed before the fix. Five failed on the
leak itself: lesson 2's inherited recap was admitted after P was held out (`last_lessons` path and
`read_history` path), the inherited-lesson-missing case was admitted, and a `your_notes`-only lesson's
recap was admitted after only the note's source became protected. Two failed because the notes check did
not exist yet. The other 2 passed before and after the fix: they are the controls where protection moved
elsewhere and the recaps stay.

### F1: recaps inherited from earlier lessons

* `teacher/brief.py` `_lesson_exposure` now returns an `_Exposure` that also lists the earlier lessons
  whose recaps the lesson was given. These come from two places: its brief's `last_lessons` entries that
  carried a recap, and `l:` entries with a recap in its `read_history` results.
* `recap_admissible` checks those lessons transitively through `_admissible`. The check is memoized: the
  `memo` is shared across all the recaps in one brief or one `read_history` result, and the library and
  withheld reads are shared within one check. It fails closed in two cases: a lesson whose opening turn
  cannot be found (missing provenance), and a cycle (a lesson that is still being judged counts as not
  admissible). The existing fast path still applies to each lesson: if that lesson's recorded protection
  equals today's, its recap and everything it inherited were admitted under the same protection.
* Tests:
  * 3-lesson regression through `last_lessons`;
  * the same chain through `read_history` alone (lesson 3's brief copy scrubbed so only the read delivered
    lesson 1's recap);
  * a control where protection moved elsewhere and both recaps stay;
  * an inherited `l:` id with no lesson behind it, which fails closed once protection changes.

### F2: notes the lesson was given

* `_lesson_exposure` also lists the notes the lesson was given: the `nodes[].your_notes[].id` headers
  (whose `line` carries the note's first line) and the `read_note` results that were not refused.
* `teacher/notes.py` `notes_still_deliverable` is injected into `build_brief` (from `service.open_lesson`)
  and into `actions.read_history`. Injection is needed because the import contract
  `notes-are-never-a-source-or-evidence` keeps `teacher.brief` away from the notes' code. The function
  works as follows:
  * It resolves each `n:<link id>` through its link row. `learner_note_links` is append-only by trigger,
    so a later hide or re-link appends rows and cannot change what the delivered row names. This answers
    the reviewer's "independent of later link changes".
  * It judges the note keys with C2b's own predicate, `vault_notes.snapshot_protected_keys`. That
    predicate checks every anchor version the annotation ever had, plus those sections' headers, and it
    is the same check that withholds the original note.
  * It fails closed in three cases: a ref with no link row, a Reader note with no anchor history (its
    source cannot be told), and any read error.
  * Captures hold no book text and stay.
* New store function `db.stores.learner_notes.links_by_id` (read-only).
* `recap_admissible` without a notes check, for a lesson that was given notes, leaves the recap out
  (fail closed).
* Tests:
  * after `read_note`, only the Lay note's section (`lay_eigen`) is held out; the lesson's own book is
    `ext_book`. The recap is left out and the sentinel is in no prompt;
  * the same through the `your_notes` header alone;
  * the dependency survives a later hide row on the link;
  * a control where protection moved elsewhere and the recap stays;
  * the missing notes check fails closed.

## Gate

Run in `/home/saturn/Documents/thinking/learnanything-merge2`. Every pytest ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, with `-n 6` and TMPDIR outside
the worktree.

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
* `uv run lint-imports --no-cache`: 42 kept, 0 broken.
* Targeted pytest: **354 passed, 0 failed**, across 22 files:
  * `test_followups_batch5_recap_dependencies` (new) and `test_followups_batch5_recap_protection`;
  * `test_followups_batch5_lesson` and `test_followups_nov2_figure_provenance`;
  * `test_notes_as_learner_text`, `test_notes_linked`, `test_notes_never_read`, `test_notes_c2b_review5`
    and `test_notes_vault_search`;
  * `test_followups_nov2_note_gap_unlinked`, `test_learner_notes_migration` and
    `test_learner_notes_vault_origin_migration`;
  * `test_reader_rw5d_p4b_teacher_visuals`;
  * `test_teacher_te1_curriculum_c4`, `test_teacher_te1_lesson`, `test_teacher_te1_review_fixes`,
    `test_teacher_te1_successor` and `test_teacher_te1_weight`;
  * `test_teacher_te0_review_fixes` and `test_teacher_te0_fix_round2`;
  * `test_architecture` and `test_ai_tool_isolation`.
* The module catalog was regenerated for the touched modules (`module_generate.py`, 17 notes);
  `module_validate.py` PASS. Both ran under `env -i` with an empty HOME, CODEX_HOME and
  LEARNLOOP_CONFIG_DIR.
* Not run, and not needed:
  * durability tests: no migration or DB/connection code changed;
  * frontend, cargo and the DB reference scripts: nothing under apps/ changed and the schema did not
    change.
  * Full suite: deferred to the landing gate (owner rule, 2026-10-17).

## Re-review (Codex job 20261102-104644-F99Se9)

Verdict REOPENED. F1 and F2 were confirmed fixed. One new finding, F3, is now fixed.

| id | severity | title | verdict | commit | test or reason |
|----|----------|-------|---------|--------|----------------|
| F1 | High | Inherited recaps are not part of a recap's dependencies | confirmed fixed (re-review) | a9107bae28 | `test_f1_*` (4) |
| F2 | High | Notes the lesson was given are not part of a recap's dependencies | confirmed fixed (re-review) | a9107bae28 | `test_f2_*` (5) |
| F3 | Medium | Long recap dependency chains crash lesson opening | fixed | 074d1972a0 | `test_f3_a_chain_longer_than_the_recursion_limit_is_judged_without_crashing`, `test_f3_a_missing_ancestor_at_the_bottom_of_a_long_chain_fails_every_recap_above_it`, `test_f3_a_cycle_in_a_long_chain_fails_closed` |

### F3

* Reproduced first. The three new tests build a synthetic chain of `sys.getrecursionlimit() + 200`
  lessons. Each lesson inherits only its predecessor's recap and recorded a protection that no longer
  matches, so every link is re-checked. Before the fix, all three raised `RecursionError`.
* Fix (`src/learnloop/teacher/brief.py`):
  * `_admissible` now walks the chain depth-first over an explicit stack instead of recursing.
  * Memoization is kept. A lesson is held in `memo` as False while it is being judged, so a dependency
    that reaches back to it (a cycle) fails closed.
  * Any lesson above a failing lesson also fails. Earlier lessons are still checked in sorted order.
  * The per-lesson check moved unchanged into `_own_verdict`. It returns False, True when nothing more
    needs checking (including unchanged protection), or the earlier lessons that still need checking.
* The tests also check that the memo ends complete: every lesson in the chain is admitted, or none is
  when the bottom ancestor is missing.

### Gate (re-review)

Run in `/home/saturn/Documents/thinking/learnanything-merge2`. Every pytest ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`.

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
* `uv run lint-imports --no-cache`: 42 kept, 0 broken.
* Before the fix, `pytest tests/test_followups_batch5_recap_dependencies.py -k f3` gave 3 failed
  (RecursionError). After the fix, the whole file gave 12 passed.
* Targeted pytest `-n 6`, 7 files: **98 passed, 0 failed**. The files were:
  * `test_followups_batch5_recap_dependencies` and `test_followups_batch5_recap_protection`;
  * `test_notes_never_read`;
  * `test_teacher_te1_curriculum_c4`, `test_teacher_te1_lesson` and `test_teacher_te1_review_fixes`;
  * `test_reader_rw5d_p4b_teacher_visuals`.
* `test_architecture`: 18 passed.
* `module_generate.py` regenerated the catalog for `teacher/brief.py` and the new tests.
  `module_validate.py` gave PASS. Both ran under `env -i` with an empty HOME, CODEX_HOME and
  LEARNLOOP_CONFIG_DIR.
* Not run, and not needed:
  * durability tests: no migration or DB code changed;
  * frontend, cargo and the DB reference scripts: nothing under apps/ changed and the schema did not
    change;
  * the full suite: deferred to the landing gate (owner rule, 2026-10-17).
