# Method-explicit items, second Codex review (stage `method-explicit-2`)

Branch `grading/method-explicit-items`, worktree `learnanything-merge`, base
`main` at `1def803a1` (not merged here; it lands after R2a, relabelled then).
Codex job `20261014-013257-ASCzCS`, read-only, reviewed
`c9c5e6e4c..838681f8a` (the redesign: the frozen `required_method` field as
the one authority, the canonical sentence, the ledgered one-time judgments).

The verdict was **REOPENED**: F13 incomplete and four new defects (F14 to
F17). The four "claims that don't hold" in the review all trace to these
findings. Every finding reproduced and is fixed. No finding was rejected.

## Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F14 | High | A quoted canonical sentence suppresses the actual instruction | fixed | `9bd9038fd` | `test_f14_*` (5 cases + 5 PF-variant cases + 3) |
| F15 | High | Source updates retain a judgment for a different statement | fixed | `9bd9038fd` | `test_f15_*` (5) |
| F13 | Medium | Disputed historical keys remain verified after a content edit | fixed | `9bd9038fd` | `test_f13_*` (4) |
| F16 | Medium | Accepted owner overrides never reach the judgment ledger | fixed | `9bd9038fd` | `test_f16_*` (3) |
| F17 | Medium | A transient PF judgment failure strands selected candidates | fixed | `9bd9038fd` | `test_f17_*` (3) |

All tests are in `tests/test_required_method_reopened.py` (28 cases). The
references were regenerated in `7ab736561`.

## F14 (High): the instruction is the writer's own final paragraph

**Reproduction.** `has_method_instruction` accepted the canonical sentence
anywhere in the prompt. Both writers and validation therefore treated these
as instructed:

- `The previous exercise said "Use cofactor expansion in your answer." Compute det(B).`
- the sentence mid-paragraph, after a colon, in an earlier paragraph, or
  inside a closing quote.

`normalize_required_method` and `inherit_required_method` appended nothing,
and `required_method_problems` reported nothing. Grading still enforced the
field. Clearing the field (`strip_method_instruction`) removed the first
occurrence, so it cut the quoted sentence out of the text.

**Fix.** The instruction is now a dedicated block that the writer owns: the
canonical sentence as the prompt's own **final paragraph**.

- `has_method_instruction` accepts only a prompt whose last paragraph
  (after a blank line; `\r\n` counts) is exactly the sentence, whitespace
  aside. An occurrence anywhere else never counts.
- `ensure_method_instruction` appends the block unless the prompt already
  ends with it. The authoring guidance asks the model to write the sentence,
  so a prompt whose own last sentence is exactly the canonical sentence
  (after `.`, `!` or `?`) has that sentence moved into the block, not
  repeated. A sentence that continues a quote, a colon or a clause is never
  touched.
- `strip_method_instruction` removes only the block. Text without the block
  is returned unchanged.
- Doctor's `required_method:not_stated` and the gold-set loader use the same
  check. Their messages now say "does not end with the paragraph".

**Tests.**

- The five placements are each `not_stated` until the block is appended,
  through the writer check (`normalize_required_method`) and the PF variant
  writer (`inherit_required_method`).
- A trailing instruction sentence becomes the block without a duplicate.
- Clearing removes only the block and leaves a quoted sentence intact.
- An owner override on a generated item whose prompt quotes the sentence adds
  and removes the block end to end.
- Some existing assertions pinned the old "anywhere" rule: an inline
  `Compute det(A). Use … in your answer.` counted as stated. They are in
  `test_required_method_items.py` (the explicit-instruction test, two
  validation tests and the doctor test's two items) and
  `test_required_method_authority.py` (one). They now use the block form,
  and the inline form is asserted `not_stated`.

## F15 (High): a decided statement is never rewritten through a proposal

**Reproduction.** A source item carries `required_method` with
`statement: source, decided_by: judgment` and judgment `J`. A generated
update proposes `prompt: "Factor A using row reduction."` and a new method.

`_hold_required_method_to_rule` dropped only the `required_method` key, and
the prompt change survived. The row was `warning`, not `invalid`. Accepting
it would have merged the new statement with the old field and `J`. An owner
edit of a pending update could do the same.

**Fix.** A new predicate, `rewrites_decided_statement(existing, prompt)` in
`vault/required_method.py`, is true when the item has a `source` required
method and the new prompt differs, whitespace aside. It is enforced at three
points:

- **Validation.** `_validation_errors` (generated proposals) and
  `_edited_payload_validation_errors` (owner edits, refreshes) report
  `required_method:source_statement_edited`. The row is `invalid`: it is never
  auto-applied, `accept` refuses it, and the repair pass is told why.
- **Apply chokepoint.** `_compile_practice_item` raises
  `PatchApplicationError` for any accept path, so a stale or forced row is
  refused too. The message points to
  `learnloop grading required-method --clear`.
- **Writer.** A restatement that differs only in whitespace has its `prompt`
  key dropped, so the verbatim statement stays and the rest of the update
  applies.

The reviewer offered two fixes: reject the edit, or require a fresh decision
on the new statement. Rejection was chosen. It keeps the redesign's rule
that a textbook statement is never rewritten, and the owner keeps a path:
clear the requirement, edit, then set it again.

**The same writer, generated items.** These fixes stop generated updates
from breaking "the text agrees with the field":

- An update that rewrites a generated item's prompt and leaves its field now
  gets the block.
- An update that renames the method replaces the old block instead of
  stacking the new one under it.
- If the rename is dropped (not a method target), the item keeps its field
  and its prompt.

**Tests.**

- The verify's reproduction is `invalid`, `accept` raises, and the item and
  `J` are unchanged.
- An owner edit is `invalid`, and the compile chokepoint refuses it even when
  the row is forced valid.
- A whitespace-only restatement applies with the verbatim statement.
- A generated item's new prompt gets the block.
- A renamed method gets one block, and a dropped rename leaves the prompt
  alone.

## F13 (Medium): a frozen regrade binds the revision it graded

**Reproduction.**

1. Grade a verified required-method exercise.
2. Record a `disputed` key check against that revision.
3. Edit the item.
4. Regrade: it reads the frozen contract, whose content is no longer
   current.

The redesign passed `bind_item=None`, which skipped binding altogether, so
the attempt stayed `verified` despite the dispute of the content it was
graded on.

**Fix.** Binding always runs, and resolves the key status of the revision
actually graded:

- **Exact rebuild.** `GradedContract.graded_reference_contents` rebuilds
  that revision's `reference_content_hash` from the frozen statement and
  expected answer, with each rubric the item is known to have had:
  - its current rubric;
  - the rubrics in its `practice_item_snapshots` rows;
  - the default rubric.

  The revision whose compiled contract matches the frozen
  `item_content_hash` and `rubric_content_hash` is the one graded
  (`graded_revision = frozen`).
- **No exact rebuild.** This happens when the rubric changed too and no
  snapshot kept the old one. Every revision a key check recorded may then be
  the graded one. The current revision is excepted when the frozen statement
  or answer differs from it. The binding fails closed: any unverified
  candidate lowers the attempt (`graded_revision = unresolved`).
- **Store.** `bind_replacement_grade` takes `graded_contents` and
  `graded_revision`, and reads each revision's status through the new
  `key_status_for_content`. `effective_key_status` is now a thin wrapper over
  it, so the current-content path is unchanged.
- **Ledger.** The ledger row names the revision that lowered the attempt.
  Its rationale gains `graded_revision` and `candidate_revisions`.

**Tests.**

- **The verify's reproduction.** The attempt is lowered, and the binding
  names the graded revision (`graded_revision=frozen`).
- **A dispute of the edited revision.** The attempt is not lowered, so
  historical verification against an unrelated revision stands.
- **A revision that cannot be rebuilt.** The attempt stands when every other
  checked revision is verified, and is lowered (`graded_revision=unresolved`)
  when the graded one was disputed.
- **Unchanged tests.** The earlier F13 tests still pass: an unverified edit
  never lowers a frozen regrade, a frozen content that IS current still
  binds, and a regrade without a frozen method binds the current content.

## F16 (Medium): the owner's override is their verdict in `judgment_ledger`

**Reproduction.** An override was accepted (set or `--clear`). Its decision
reached the proposal audit and the YAML. It never reached
`judgment_ledger`, contrary to implementation handoffs §0 rule 6 ("every LLM,
verifier or owner verdict appends to `judgment_ledger`").

**Fix.** The verdict is written by the acceptance plan:

- **Write-ahead.** `_compile_practice_item` recognizes the override by its
  audit (`required_method_override`, which only the owner's command writes).
  It adds a `required_method_owner_verdict` side effect to the item's durable
  plan, and `apply_protocol._perform_side_effect` performs it through
  `record_owner_verdict`.
- **Idempotent.** The row id is fixed by the proposal item
  (`rmowner_<proposal item id>`), so a recovery that re-runs the plan appends
  nothing twice.
- **The question.** `task = required_method_statement`,
  `left = (practice_item, id)`, `right = (required_method, method)`. This is
  the same question as the import's judgment.
- **The verdict.** `judge = owner`, `prompt_version =
  required-method-override-v1`, verdict `requires` or `not_required`.
- **Input hash.**
  - A source statement uses the import judgment's own hash (the statement
    verbatim and the method's name), so a lookup of that question finds the
    owner's answer.
  - A generated item hashes the statement, method and criteria.
- **Links.** The row supersedes the latest verdict on the same question: the
  import's judgment, or an earlier owner verdict. The rationale keeps the
  field before the change, `prior_judgment_id` (the field's own judgment,
  which may belong to a different method's question), and the proposal and
  item ids.

**Tests.**

- **A source item.** Its override is ledgered and supersedes the import's
  judgment, with the expected input hash. A later `--clear` is ledgered as
  `not_required` and supersedes the owner's first verdict.
- **A generated item.** Its override is ledgered, and re-running the side
  effect appends nothing.
- **A generated update.** It writes no owner verdict.

## F17 (Medium): a PF judgment failure leaves the job retryable

**Reproduction.** Generation, verification and selection succeeded, then the
variant judgment timed out or was refused by the spend cap.
`judge_variant_stem` swallowed every exception, including a cancellation.
`_FamilyRun.execute` marked the mint request `admitted` and the family
`complete`. A rerun of the round found the request terminal
(`already_admitted`), so the paid, verified candidate stayed selected and
unjudged for good.

**Fix.**

- **Strict judgment.** The run calls `judge_variant_stem(strict=True)`.
- **Refusal or cancellation.** A spend refusal or a cancellation propagates
  as every other PF stage's does. The run releases the request to `pending`
  and stops (`over_budget` or `cancelled`).
- **Any other failure, or no judge ready.** Every selected variant is tried
  first. Then `RequiredMethodJudgmentIncomplete` is raised, after which:
  - the variants already judged `consistent` publish (when the run
    publishes);
  - the request is left `failed`, which a rerun of the round reclaims;
  - the family reports `status: judgment_incomplete` with the failure
    classes and "rerun this round to judge them".
- **Resume.** A rerun of the same round replays every generation, panel and
  selection call from its checkpoints, so nothing is regenerated or paid
  again. It reuses the verdicts already ledgered and asks only the missing
  ones, under the run's own caps.
- **Cancellation outside a run.** `judge_variant_stem` no longer swallows a
  cancellation (`AIInterrupted`) anywhere.

**Tests.**

- A timeout and a spend refusal each leave the request retryable (`failed`
  and `pending`).
- The rerun makes **zero** generation calls and exactly one judgment call,
  then marks the request `admitted`. The backlog then publishes the variant.
- A cancellation during the judgment cancels the run, with the request
  `pending`.
- **Unchanged test.** The redesign's `test_a_variant_with_no_verdict_or_an_edited_stem_is_not_published`
  still passes. With no judge ready, the family now also reports
  `judgment_incomplete` and stays retryable.

## Fail-first

`838681f8a`'s `src` was exported to `fixtures-local/tmp/base_838681f8a`, with
`migrations` linked in. No tracked vault was linked. The new tests ran
against the export (`pytest -o pythonpath=<export>/src`).

**`tests/test_required_method_reopened.py`: 25 failed, 3 passed.** Every
failure is behavioural: the base ran and gave the wrong answer, and none
failed to import.

| Finding | Failed on the base | What the base did |
|---|---|---|
| F14 | 13 | a quoted, mid-paragraph, after-colon, earlier-paragraph or closing-quote sentence counted as instructed (writer, PF writer, validation); the trailing sentence was not moved into the block; clearing cut the quoted sentence; the override left a quoted prompt without the block |
| F15 | 5 | the source rewrite was `warning`, not `invalid`; an owner edit was `valid`; a whitespace restatement kept the rewritten prompt; a generated item's new prompt lacked the block; a renamed method stacked two blocks |
| F13 | 2 | the graded revision's later dispute left the attempt `verified` (exact and unresolved rebuilds) |
| F16 | 2 | no owner row was appended, and the override's compile carried no side effect |
| F17 | 3 | a timeout or a spend refusal completed the family and admitted the request; a cancellation was swallowed |

The 3 that pass on the base are the intended controls:

- F13: a dispute of the edited (current) revision does not lower the
  attempt;
- F13: an unresolved rebuild with every revision verified stands;
- F16: a generated update writes no owner verdict.

## Gate

The gate ran on the tree at `7ab736561`. The only uncommitted changes were
this record and the pointer in `method-explicit-items.md`. `TMPDIR` was the
worktree's `fixtures-local/tmp`.

The owner paused this step (2026-10-14, about 02:20 to 09:00) after the
fixes and references were committed. The full suite had finished and the
durability lane had started, but neither result was recorded. Both were
rerun from the start after the pause. The results below are from that
rerun. Main was not merged in (it has moved to `56579d271`, RW3a landed).

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| Stage tests (`test_required_method_reopened.py`, `test_required_method_items.py`, `test_required_method_authority.py`) | **194 passed** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10551 passed**, 0 failed, 0 skipped (48 warnings, 615.86s) |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10452 deselected, 0 failed (1 warning, 166.48s) |
| `db_generate_reference.py`, then `db_validate_reference.py` | **0 errors**: schema head 199, 318 table notes. Only citations, source-commit stamps and the `practice_item_snapshots` note's new `attempts.py` citation moved. Revalidated after the pause: `errors: []` |
| `validate_vault.py` | passed (1,099 notes, 22,001 links; revalidated after the pause) |
| CLI help snapshot | unchanged (no CLI change; `test_cli_help_snapshot.py` passes) |
| Defaults and template snapshots | unchanged (no configuration key) |
| Frontend and cargo | not applicable: nothing under `apps/learnloop-tauri` changed |

There were no paid calls. No external interface or paid command changed:
F17 only changes what happens after a judgment fails. No key, env file or
vault database was read, and no tracked vault was opened.

## Not changed, and open questions

1. **`edit_item` (the learner's in-place reword) is not guarded.** Two cases
   are open:
   - a reword of a source-decided statement keeps the decision made on the
     old wording;
   - a reword of a generated item may drop the block, which doctor then
     reports as `not_stated`.

   The review named the proposal path only. A guard here would either
   refuse a learner's edit or silently change grading, so it is left for the
   owner. The options are: refuse with a pointer to `--clear`, drop the
   requirement, or re-append the block.
2. **An unresolved F13 rebuild is conservative.** When the graded revision
   cannot be rebuilt, a disputed check of any other earlier revision also
   lowers the regrade. Snapshots of the item make the rebuild exact. Without
   one, failing closed seemed the right default for certification.
3. **With no judge ready, a required-method PF family stays
   `judgment_incomplete` on every run of its round** until a judge is
   configured. This is honest and retryable, but repeated. Say if a missing
   judge should instead be refused before the run starts.
4. **The owner's clear is recorded as `not_required`,** not as one of the
   import question's options (`allows` / `prohibits`): the owner's command
   does not say which. Readers that test `== "requires"` are unaffected.

## Re-review (Codex job `20261014-094127-Volan7`)

The re-review read `838681f8a..444f5ba95`, read-only, and returned
**REOPENED**:

- F15 and F16 were confirmed fixed.
- F14 (High) was reopened.
- F13 and F17 were reopened through two new defects, F19 and F20.
- F18 is a new defect.

Every reopened and new finding reproduced. All are fixed in `82566269e`,
and none was rejected.

| Commit | What |
|---|---|
| `82566269e` | the fixes and their tests |
| `fc1191a21` | regenerated architecture references (citations and source-commit stamps only) |
| `548a6011c` | a docstring correction in `restate_method_instruction`, and the stage record's pointer |
| `fc44c9f21` | the contract module computes the recorded hash through a private alias (the gate's first run, below) |
| (this commit) | this record |

### Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F14 | High (reopened) | An indented quotation of the sentence stood for the writer's block | fixed | `82566269e` | `test_f14_*` (12 cases) |
| F15 | High | Source updates retain a judgment for a different statement | confirmed fixed by the re-review; no change | `9bd9038fd` | `test_f15_*` (5, unchanged) |
| F13 | Medium (reopened) | A frozen regrade can bind the wrong key revision (see F19) | fixed with F19 | `82566269e` | `test_f19_*`; one `test_f13_*` case is now historical |
| F16 | Medium | Accepted owner overrides never reach the judgment ledger | confirmed fixed by the re-review; no change | `9bd9038fd` | `test_f16_*` (3, unchanged) |
| F17 | Medium (reopened) | Partial publication breaks the judgment-only recovery (see F20) | fixed with F20 | `82566269e` | `test_f20_*`; `test_f17_*` (3) now resume at the judgment |
| F18 | Medium | Clearing or renaming a legacy method leaves its instruction behind | fixed | `82566269e` | `test_f18_*` (15 cases) |
| F19 | Medium | Frozen reconstruction mistakes equivalent rubrics for identical reference revisions | fixed | `82566269e` | `test_f19_*` (5 cases) |
| F20 | Medium | Partial PF publication invalidates recovery checkpoints | fixed | `82566269e` | `test_f20_*` (1 case) |

The new tests are in `tests/test_required_method_rereview.py` (33 cases).

### F14 (High, reopened): the writer renders its block; generated text never stands for it

**Reproduction.** The re-review's prompt was:

```
Compute det(B). The previous exercise said:

    Use cofactor expansion in your answer.
```

`has_method_instruction` normalized whitespace, so it took the indented
quotation for the writer's block. As a result:

- `normalize_required_method` and `inherit_required_method` appended
  nothing;
- validation reported nothing;
- grading enforced the field;
- clearing the field cut the quotation out.

Three more prompts reproduced the defect. Each ends with a column-0
paragraph:

- the sentence after "said:";
- the sentence after "The previous exercise ended as follows.";
- a block the model wrote itself.

The previous fix's "move the model's own trailing sentence into the block"
also took generated text for the block.

**Fix.** The block is the writer's alone, and nothing generated stands for
it.

- **`render_method_instruction`.** This replaces `ensure_method_instruction`.
  It always appends the block, "Use {name} in your answer.", as the final
  paragraph after the generated text. It never reads what the text ends
  with. Every creation writer uses it:
  - authoring and practice proposals;
  - synthesis;
  - PF variants (`inherit_required_method`).
- **The guidance.** `CRITERIA_BY_FACT_GUIDANCE`,
  `REQUIRED_METHOD_VARIANT_GUIDANCE` and the two schema descriptions
  (`RequiredMethodPayload.name`, `PracticeItemPatchPayload.required_method`)
  no longer ask the model for the sentence. They now say: "LearnLoop
  appends 'Use {name} in your answer.' … itself: never write, quote or
  contradict it." Every prompt that carries them moved its version:

  | Prompt | New version |
  |---|---|
  | The rule (`CRITERIA_BY_FACT_RULE_VERSION`) | `criteria-by-fact-v2` |
  | Authoring, diagnostic authoring, practice generation, canonical ingest, exercise authoring, and synthesis and append (both variants each) | `…-criteria-by-fact-v2` |
  | PF generator program | `pf-generator-program-v8` |
  | PF proposer, single-shot and source-anchored | `pf-ensemble-propose-v4`, `pf-single-shot-v4`, `pf-source-anchored-v4` |
  | Rubric-phrasing judge | `rubric-phrasing-judge-v2` |

  Teach-back has its own clause and keeps its version. The guidance stays
  the same length to within a sentence, and the spend-envelope tests pass
  unchanged.
- **`has_method_instruction`.** It now reads only STORED prompts, for
  doctor, the gold-set loader, and a writer asking whether an item's prompt
  still carries its block. The block counts only as the writer renders it:
  - its own final paragraph after any blank lines;
  - starting at column 0;
  - word for word (whitespace between words aside).

  An indented paragraph (two spaces, a tab, a Markdown code block) or a
  blockquote is `required_method:not_stated`.
- **`restate_method_instruction`.** This serves a prompt that is a revision
  of an item's stored prompt, which carries the item's own block:
  - updates;
  - owner overrides;
  - method-phrasing repairs.

  It removes the previous method's instruction, then renders the field's
  block. A prompt that already ends with an unchanged method's block is
  kept as it is. A revision therefore carries one block, and a quotation in
  it is followed by the writer's block.
- **`normalize_required_method(render_instruction=False)`.** The proposal
  writer decides the field first, then restates the text.

**Tests.**

- The five generated endings each get the block after them:
  - writer and PF writer: indented, blockquote, after a colon, introduced,
    and a block the model wrote.
- Validation reports the indented, blockquote, two-space and tab endings,
  and accepts the rendered block (with longer breaks, CRLF, or alone).
- The guidance no longer asks for the sentence, and every version moved.
- The re-review's prompt runs end to end through an authoring proposal:
  - payload, accepted item and doctor agree;
  - the text ends with the writer's block after the quotation.
- A generated update keeps one block when its revision carries the item's
  block, and renders the block after an indented quotation.

**Existing tests changed.** These pinned the old adoption:

- `test_f14_a_trailing_instruction_sentence_becomes_the_block_without_a_duplicate`
  is now `test_f14_the_writer_never_takes_a_trailing_sentence_for_its_block`.
- `test_a_generated_prompt_gets_the_canonical_sentence_whatever_it_says`
  asserted idempotence, a second pass appending nothing. The writer's input
  is generated text, so it now asserts the output is stated.
- The authority test's whitespace example now starts at column 0, and the
  indented form is asserted not stated.
- `test_the_explicit_instruction` uses `render_method_instruction` and
  `restate_method_instruction`.
- The version pins moved: `test_authoring_prompts_carry_the_rule_and_moved_their_versions`,
  the method-phrasing judge's two, and the synthesis version.

### F18 (Medium): clearing or renaming removes a legacy instruction, never a quoted one

**Reproduction.** A generated item has a prompt that the earlier rule
accepted: `Define the SVD of A. Use singular value decomposition in your
answer.`

- `override_payload(clear=True)` dropped the field and kept the
  instruction.
- Renaming kept it and appended the new block under it.
- A generated update renaming the method did the same.

**Fix.** `strip_method_instruction` removes the instruction for the item's
own method:

- the writer's block, when the prompt ends with it;
- then every standalone occurrence of the sentence. This is the legacy
  inline instruction, or a copy the text repeats. An occurrence is
  standalone when all of these hold:
  - it is at the start of the text, or after a sentence's end (`.`, `!` or
    `?`) on its own line or an earlier one;
  - its line is not indented and not a blockquote;
  - it is followed by whitespace or the end.

A quoted occurrence is never edited: in quotation marks or brackets, after
a colon, indented, or in a blockquote. A line removed whole keeps the
larger break around it.

The override (clear, rename, re-set) uses it through
`restate_method_instruction`, as do the proposal writer and the
method-phrasing repair. Setting the same method again converts a legacy
instruction into the block. The repair could previously stack a renamed
method's block; it now goes through the same path.

**Tests.**

- Clearing removes each legacy placement: trailing, leading, mid, own line,
  own paragraph, the block, and a standalone copy with a block.
- Six quoted placements survive: double quotes, after a colon, indented,
  blockquote, after a colon on the previous line, in parentheses.
- The re-review's scenario through `override_payload`: clear, rename and
  re-set, then an accepted clear.
- A generated update renaming a legacy method replaces its instruction.

### F19 (Medium; F13 reopened): the regrade binds the revision the contract recorded

**Reproduction.** An item graded under an inherited default rubric
(`grading_rubric = None`) has its prompt edited, and the same rubric is
then written inline.

The reconstruction tried the current inline rubric first. Its resolved
contract matched, so it was declared the exact revision, but its
reference-content hash is not the `None` revision's. Both consequences
reproduced:

- an undisputed verified attempt became `unverified`, because the inline
  twin was never checked;
- a dispute of the revision actually graded was ignored, leaving the
  attempt `verified`, when the inline twin had a verified check.

**Fix.**

- **The contract records the revision.** `compile_assessment_contract`
  records `reference_content_hash` (statement, expected answer and the
  item's own rubric, inline or inherited) when the item has a required
  method. Every other contract, and its hash, is unchanged.
- **The regrade binds that hash.** `graded_reference_contents` binds the
  recorded hash exactly (`graded_revision=frozen`).
- **Historical contracts keep the ambiguity.** For a contract frozen before
  this change, every rubric representation whose contract matches is
  collected: the current one, the snapshots', and none (inherited).
  - One revision matches: it is `frozen`.
  - Several match: the binding is `ambiguous`. It keeps the candidates a
    key check recorded (a verified attempt's revision had one), else all
    of them, and binds fail closed.
  - None matches: `unresolved`, as before.
- **The regrade always binds the graded revision.** It now passes the
  frozen contract whenever it reads it. The `matches_current_content` gate
  is gone (and the method with it), so an equivalent current rubric never
  decides the binding.

**Tests.**

- A method contract records the hash; a contract without a method does not.
- Each consequence is tested with a recorded and with a historical
  contract:
  - the inherited-rubric attempt stays `verified` with no binding;
  - the disputed graded revision lowers the attempt, binding that
    revision's hash (`frozen` / `ambiguous`).
- `test_f13_when_the_graded_revision_cannot_be_rebuilt_*` now strips the
  recorded hash, since the unresolved path is the historical one. Its
  assertions are unchanged.

### F20 (Medium; F17 reopened): a rerun resumes at the judgment and publication step

**Reproduction.** Two variants were selected (with a publish cap of 5). One
judgment succeeded and the other timed out. The first was published and
the request was left `failed`.

The rerun of the round re-ran the whole pipeline. The published variant
changed the freshness comparisons and the MMR history, so 7 paid
(fake-counted) calls missed their checkpoints.

**Fix.** `_FamilyRun._resume_after_selection` checks for a persisted
`selection_json` among the candidates of the claimed mint request. When
there is one, the selection has finished. This covers a request left after:

- a judgment failure;
- a spend refusal or cancellation (released to `pending`);
- a publication error.

The rerun then:

- loads the persisted candidates;
- orders the selected ones by the selection judge's rank, else the MMR
  rank;
- asks only the missing verdicts (`_judge_required_method` reuses the
  ledgered ones);
- publishes and resolves the request.

It skips skeleton, generation, filters, panel, freshness and selection.
The family reports `resumed: required_method_judgment`.

Partial publication on an incomplete judgment is kept: publishing the
judged variants no longer touches the rerun's requests, and
`learnloop pf publish` may publish them in between too.

**Test.** The run has two selected variants: one judged and published, the
other timing out. The rerun makes:

- **zero** generation, panel, freshness and selection calls;
- exactly one judgment call.

It then publishes the second variant and admits the request. The F17 tests
also take the resume path now. They pass unchanged: zero generation calls
and one judgment.

### Fail-first

The base `444f5ba95` `src` was exported to `fixtures-local/tmp/base_444f5ba95`,
with `migrations` linked in. Its `tests/` used the base versions of the five
test modules this fix edits. No tracked vault was linked. The final
`tests/test_required_method_rereview.py` ran against the export
(`pytest -o pythonpath=src`; tracebacks confirm the export's modules).

**25 failed, 8 passed.** Every failure is behavioural:

| Finding | Failed on the base | What the base did |
|---|---|---|
| F14 | 10 | took the indented, after-colon, introduced and model-written endings for the block (writer and PF writer); validated the indented, two-space and tab endings; the guidance asked for the sentence; the end-to-end payload and the update kept the quotation as the block |
| F18 | 9 | kept six legacy placements on clear (only the block-alone case passed); cut an indented quotation out; the override's clear, rename and re-set and the update's rename kept the legacy instruction |
| F19 | 5 | recorded no hash; lowered the inherited-rubric attempt (recorded and historical); kept the attempt verified despite the graded revision's dispute (recorded and historical) |
| F20 | 1 | the rerun made 7 non-judgment calls |

The 8 that pass on the base are the intended controls:

- the blockquote ending (writer and validation);
- clearing the block alone;
- five quoted placements surviving a clear.

### Gate (re-review)

The gate ran on the tree at `fc44c9f21`. The only uncommitted change was
this record. `TMPDIR` was the worktree's `fixtures-local/tmp`. The full
suite and the durability lane ran back to back under one hold of
`/tmp/learnloop-fullsuite.lock`.

**The first run, on `548a6011c`, found one failure.** The durability lane
passed (99 passed, 10485 deselected). The full suite had 10583 passed and
1 failed: `test_characterization_assessment_exam.py::test_contract_hash_is_single_monolithic_content_hash`
pins `contract_hash` as the contract module's only public `*_hash` callable,
and the module-level import of `reference_content_hash` added a second one.
`fc44c9f21` imports it under a private alias. Both the full suite and the
durability lane were then rerun from the start; the results below are that
rerun's.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| Stage tests (`test_required_method_rereview.py`, `test_required_method_reopened.py`, `test_required_method_items.py`, `test_required_method_authority.py`) | **227 passed** (the new file: 33) |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10584 passed**, 0 failed, 0 skipped (48 warnings, 518.49s) |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10485 deselected, 0 failed (1 warning, 116.22s) |
| `db_generate_reference.py`, then `db_validate_reference.py` | **0 errors**: schema head 199, 318 table notes. Only citations and source-commit stamps moved (`fc1191a21`); revalidated on `548a6011c` and `fc44c9f21` (no line moved): `errors: []` |
| `validate_vault.py` | passed (1,099 notes, 22,001 links) |
| CLI help snapshot | unchanged (no CLI change; `test_cli_help_snapshot.py` passes) |
| Defaults and template snapshots | unchanged (no configuration key) |
| Frontend and cargo | not applicable: nothing under `apps/learnloop-tauri` changed |

There were no paid calls. No live check was needed: the external
interfaces are unchanged. The prompt text that changed is the guidance
wording, pinned by tests. No key, env file or vault database was read, and
no tracked vault was opened. Main was not merged in.

### Not changed, and open questions

The earlier open questions 1, 3 and 4 still stand. Question 2 is narrowed
to historical contracts. New:

5. **A model that disobeys the new guidance gets a visible duplicate.**
   A creation prompt that still ends with "Use X in your answer." keeps it,
   and the writer's block follows. This is honest and harmless to grading,
   and the guidance asks the model not to write the sentence. An update
   that carries the item's own block or inline instruction is deduplicated
   (it is restated).
6. **A stored-prompt check cannot tell a column-0 final sentence's
   author.** A non-writer edit (`edit_item`, a hand edit) ending in
   "said:", then a blank line and the sentence, still reads as stated.
   Writers never produce that from generated text. This is the same
   boundary as open question 1.
7. **A resumed PF job's publication order is approximate.** It sorts by the
   selection judge's rank, else the MMR rank: the judge's own `selected`
   order is not persisted. Only the daily cap's cut-off can differ.
