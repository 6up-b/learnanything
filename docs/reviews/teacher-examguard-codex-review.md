# Teacher exam-question guard: Codex review and fixes (`teacher/exam-question-guard`, base `23182034c6`)

The Codex review (gpt-6.1-sol, codex-job `20261106-085612-5svOl3`) of `830923138d` and `5d3be261c8` raised two
findings. Both reproduced as failing tests and are fixed. No migration, successor, config key or model request
(0 paid calls). No reader or writer of the old item difficulty scalar. The diff stays in `teacher/guards.py` and
`teacher/service.py`'s guard loop in `_call_teacher`; it does not touch TE3a's reveal/show write or receipt exposure.

## Review

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Distinctive whole exam questions under six words bypass protection | fixed | (this commit) | `test_a_whole_short_reserved_question_with_a_distinctive_number_counts`, `test_a_teacher_check_posing_a_short_reserved_question_is_withheld`, `test_the_graders_feedback_quoting_a_short_reserved_question_is_not_shown` |
| F2 | Medium | Splitting a reserved question between message and check evades every guard | fixed | (this commit) | `test_a_reserved_question_split_between_message_and_check_is_withheld`; negative `test_half_a_reserved_question_beside_an_ordinary_check_is_accepted` |

### F1: a whole short stem with a distinctive number

**Reproduced.** The vault gains an exam-pool item "Factor 9871 into primes." whose key shares no words with it.
Before the fix, `quotes_reserved` dropped the matcher's `stem` finding because it is shorter than the shingle
order (6). As a result:

- `reserved_guard` passed it;
- a teacher check posing it was accepted and shown;
- grader feedback quoting it was kept.

All three tests failed.

**Fix** (`guards.quotes_reserved`). A finding shorter than the matcher's span still counts when the same text also
carries a distinctive number that the matcher reports (`numeric` kind) and that number lies inside the span. The
match uses normalized words, so "16.0" is compared as "16 0". This adds no new parameter. Both rules belong to the
matcher:

- its span length (`shingle_n`);
- its distinctive-number rule (`_numeric_literals`: three or more digits, or a decimal, fraction or percentage),
  less what ordinary items already show.

**Which short phrases still do not count.** The negative test pins four, plus the earlier `ORDINARY` sentence:

- "Later we define a basis carefully." (the short stem "Define a basis." with no number);
- "We factor whole numbers into primes.";
- a lone "9871";
- "Factor 9872 into primes.".

**Judgment, recorded for the owner.** A short reserved stem with no distinctive number still does not count, for
example "State the rank-nullity theorem." The finding's claim was about distinctive questions. A short stem made
only of words is the concept's own phrase, and a lesson on that concept says it. Withholding it would block ordinary
lesson turns. That would be a false refusal, which is a defect under this stage's bar.

To protect such stems too, have `counts` in `quotes_reserved` return True for every `stem` finding, so that every
whole stem counts. This is a one-line change. The cost is a refusal whenever a lesson uses that phrase.

### F2: a question split across fields

**Reproduced.** An exam-pool item reads "For polynomial x³−7x+2, identify every real root." The turn puts
"For polynomial x³−7x+2," in the message and "identify every real root." in `check.question`. Each half has fewer
than 6 normalized words and passes alone, so the turn was accepted.

**Fix** (`service._call_teacher`). After the per-field loop, the displayed fields are joined in their display order
(the same join `_record_reveals` uses) and screened once more with `reserved_guard`. A hit withholds the turn with
location `turn`, under the same refusal and re-prompt as any other hit. The per-field checks still run first, so a
field that carries the question alone is still named.

**Negative test.** Half of the question beside an ordinary check is accepted.

**Byte-identical guarantee.** A lesson with no reserved text is unchanged: the added check writes nothing when it
passes. `test_a_lesson_with_no_reserved_text_is_byte_identical_with_the_guard_off` still passes.

### The "claims that don't hold"

Both are answered by F1 and F2:

- The matcher's whole-stem behaviour is now kept for distinctive short stems.
- A turn is screened whole as well as by field.

### Not fixed (smallest way to finish, if wanted)

- **Across turns.** A question split across two turns (its setup in turn k, its ask in turn k+1) is not screened
  whole. To finish: screen `S.displayed_texts(state)`'s last accepted turn joined with the new turn's displayed text,
  in `_call_teacher`. This is about four lines, at the cost of a second matcher pass per turn.
- **The figure beside the turn.** A built figure is screened alone, not joined with its turn's message. To finish,
  pass the message into the `_visual` reserved check.

Neither is the finding's scenario. Both need a model that deliberately spreads a question across turns or across
the figure.

## Gate (this step; targeted, per the owner's rule of 2026-10-17)

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| `pytest -n 6 tests/test_teacher_exam_question_guard.py`, new tests in place, before the fix | **4 failed, 20 passed** (reproduction: F1 x3, F2 x1; the F2 negative and the 19 earlier tests pass) |
| the same file after the fix | **24 passed** |
| `uv run lint-imports --no-cache` (isolated env) | 43 kept, 0 broken |
| `pytest -n 6` behaviour set (list below) | **667 passed** |
| `pytest -n 6` contract set (list below) | **959 passed, 6 skipped** |
| `module_generate.py`, `module_validate.py` (isolated env) | 1244 module notes; PASS |

Every pytest ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at `-n 6`, with
TMPDIR outside the worktree. Every other Python command (lint-imports, the module scripts) ran under `env -i` with an
empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR.

**Behaviour set (667).** These are the files that exercise `teacher.guards` and `teacher.service`, the same list as
the stage's first gate:

- `tests/test_teacher_*.py` (all 28 files, `test_teacher_exam_question_guard.py` included);
- `test_reader_rw5d_p4b_teacher_visuals`;
- `test_data_capture_a6_delayed_pick`, `test_data_capture_successor`;
- `test_figures_prefetch`, `test_figures_prefetch_review_fixes`;
- `test_followup_single_use`, `test_followup_successor`, `test_followup_reserved_only`;
- `test_followups_batch5_lesson`, `test_followups_batch5_recap_dependencies`, `test_followups_batch5_recap_protection`;
- `test_followups_batch6_review_fixes`, `test_followups_batch6_router_report`;
- `test_followups_batch7_prefetch_capped_resume`, `test_followups_nov2_figure_provenance`;
- `test_ro1_successor`, `test_ro4_successor`, `test_ro5_successor`, `test_ro6_successor`, `test_rofu_successor`;
- `test_practice_leakage`.

**Contract set (959 + 6 skipped):**

- architecture and registries: `test_architecture` (frozen cycles), `test_table_roles`, `test_registry_audit`,
  `test_module_catalog_inventory`, `test_ad_protected_tables`;
- `test_cli_help_snapshot`;
- the display-label audit: `test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`,
  `test_rw5c_labels`;
- the process-launch allowlist: `test_ai_tool_isolation`, `test_e0_isolation`, `test_codex_tool_lockdown`,
  `test_codex_lockdown_round3`;
- storage and the public tip: `test_sqlite_file_copies`, `test_public_tip_guards`, `test_config_refactor`;
- the desktop and sidecar contracts: `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`,
  `test_sidecar_contract`, `test_sidecar_registry`, `test_desktop_activation_audit`;
- `test_mobile_allowlist`;
- `test_coordinated_migrations`, `test_tracked_fixture_databases`;
- `test_notes_never_read`.

Not run, because nothing they cover changed:

- no migration, DB or connection code: the durability lane and the DB reference scripts;
- no frontend or Rust: npm, vitest, cargo;
- no config key: the defaults snapshot.

The full suite runs once, in the landing gate.

## Re-review (codex-job `20261106-091057-Yehmn5`, of `356f531bdc`)

The re-review confirmed F2 fixed and reopened F1. It established no new defect introduced by the fix commit. The fix
below supersedes the F1 "Judgment, recorded for the owner" above: a short word-only stem is now withheld when it is
posed. No migration, successor, config key, new parameter or model request (0 paid calls). No reader or writer of the
old item difficulty scalar. The diff stays in `teacher/guards.py` (`quotes_reserved` and a new `_posed`); no call
site changed.

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 (reopened) | High | Distinctive short stems still pass unless the text carries a numeric finding: a word-only stem ("Decrypt QEBNRFZH using Caesar cipher.") and a numbered stem whose number an ordinary item also shows | fixed | (this commit) | `test_a_whole_short_reserved_question_posed_on_its_own_counts_without_a_number`, `test_a_short_reserved_question_counts_when_an_ordinary_item_shows_its_number`, `test_a_teacher_check_posing_a_short_reserved_question_is_withheld[Decrypt QEBNRFZH using Caesar cipher.]`, `test_the_graders_feedback_quoting_a_short_reserved_question_is_not_shown[Decrypt QEBNRFZH using Caesar cipher.]` |
| F2 | Medium | Splitting a reserved question between message and check | confirmed fixed by the re-review | `356f531bdc` | no change |

### F1 reopened: reproduced

The vault gains an exam-pool item "Decrypt QEBNRFZH using Caesar cipher." (key "stoat lark: a plain word"). One
test adds an ordinary item "Is 9871 divisible by seven?". Before the fix, four tests failed (**4 failed, 24 passed**):

- `quotes_reserved` passed the cipher stem, alone and after "Here is one to try:";
- a teacher check posing it was accepted;
- grader feedback "Right. Compare: Decrypt QEBNRFZH using Caesar cipher." was kept;
- with the ordinary 9871 item, the matcher's subtraction dropped its numeric finding, so "Factor 9871 into primes."
  passed again. The test asserts that the numeric finding is gone, so it pins the reviewer's mechanism.

### Fix (`guards.quotes_reserved`, `guards._posed`)

A span shorter than the matcher's shingle order still counts only when it is the question, and not a phrase inside a
teaching sentence. That now holds in two ways.

1. **It carries a distinctive number**, by the matcher's own numeric rule (`inventory_for_texts([text]).numerics`,
   that is `_numeric_literals`), read from the shown text itself rather than from the subtracted findings. An
   ordinary item showing 9871 makes a lone "9871" harmless. It does not make the whole question "Factor 9871 into
   primes." ordinary. This rule counts the stem anywhere, including inside a sentence ("Then factor 9871 into
   primes by trial division.").
2. **A whole stem the text poses** (new, independent of numbers). This holds when the stem stands as its own
   sentence or clause: before and after it there is a clause mark or the text's edge. A clause mark
   (`CLAUSE_MARKS`) is one of `. , ; : ! ?`, a line break, a quotation mark or a bracket. The stem also counts when
   a question mark follows it ("Can you decrypt QEBNRFZH using Caesar cipher?"). The words are the matcher's own
   (`[a-z0-9]+` on the lowered text, which is `_normalize_tokens` with positions). The F2 join puts a line break
   between fields, so each displayed field's edges are clause edges there too.

No new threshold. The rules use the matcher's span length, its numeric rule and punctuation. `CLAUSE_MARKS` is a
structural character set, not a numeric parameter, so it needs no entry in `parameter_registry`.

**The common-phrase negatives stay accepted.** These are pinned:

- `ORDINARY` (with "Later we define a basis carefully.") as a whole lesson turn;
- "Now we define a basis.";
- "To define a basis, list vectors.";
- "We decrypt messages using a Caesar cipher.";
- "Here 9871 is only a number.";
- "Factor 9872 into primes.";
- "We factor whole numbers into primes.".

**Now withheld:**

- "Define a basis." on its own;
- "Next: define a basis.";
- a plan statement or check question that is exactly a reserved short stem.

That is the exam question posed. A teacher check posing it would also give the learner the reserved question
before its exam. The cost is a re-prompt when the teacher writes a plan step word for word as a reserved short stem.

### Left (smallest way to finish, if wanted)

**A word-only short stem inside a longer sentence** that neither opens a clause nor ends in a question mark is
still a phrase. An example is "You could decrypt QEBNRFZH using Caesar cipher now." Telling it apart from "Later
we define a basis carefully." needs a notion of a distinctive word ("qebnrfzh" against "define"). The vault offers
no structural notion of that. On this test vault "define" appears in no ordinary item or source text either, so a
"word no ordinary text shows" rule would refuse the common-phrase negative.

To finish, in `_posed`, count a stem whose words include one that `reserved.questions.source_shows` and no ordinary
item shows. That needs the ordinary items' vocabulary, which is the `shown` list in
`practice_leakage.reserved_questions`, kept on `ReservedQuestions`. The cost is false refusals on young vaults whose
ordinary vocabulary is thin.

### Gate (this step; targeted, per the owner's rule of 2026-10-17)

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| `pytest -n 6 tests/test_teacher_exam_question_guard.py`, new tests in place, before the fix | **4 failed, 24 passed** (the reproduction above) |
| the same file after the fix | **28 passed** |
| `lint-imports --no-cache` (isolated env) | 43 kept, 0 broken |
| `pytest -n 6` behaviour set (the list above, unchanged) | **671 passed** (667 before, plus the 4 new cases) |
| `pytest -n 6` contract set (the list above, unchanged: frozen cycles in `test_architecture`, the CLI help snapshot, the display-label audit, the process-launch allowlist) | **959 passed, 6 skipped** |
| `module_generate.py`, `module_validate.py` (isolated env) | 1244 module notes; PASS |

The isolation and memory rules were the same as the first round:

- every pytest ran in the 5G memory-capped scope at `-n 6`, with TMPDIR outside the worktree;
- every other Python command ran under `env -i` with an empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR.

The following were not run, for the same reasons as the first round: the durability lane, the DB reference
scripts, npm, vitest, cargo and the defaults snapshot.

The spec's §9.3 As built ("What counts as a hit") and `teacher-exam-question-guard.md`'s owner-judgment note are
updated to match.
