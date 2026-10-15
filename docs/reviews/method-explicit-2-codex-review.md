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

## Round 3 (stage `method-explicit-3`): finished by design

The final verify of the re-review (Codex job `20261014-113512-OQ2Gd7`,
read-only, `444f5ba95..e96075e94`) returned **REOPENED**:

- F15 and F16 were confirmed fixed.
- F14, F18, F13/F19 and F17/F20 were reopened.
- F21 and F22 are new.

The text findings had one cause. The canonical sentence lived inside the
item's stored statement, so code had to find, keep or remove it by matching
text, and each matcher was defeated by the statement's own words:

- a quotation of the sentence was adopted as the instruction (F14);
- removal deleted a sentence inside a quotation (F18, F21).

Round 3 applies the design Codex proposed instead of a fourth matcher. Every
reproduction in the verify reproduced and is fixed. No finding was rejected.

| Commit | What |
|---|---|
| `7efb7664b` | the redesign and its tests |
| `7beb18d2c` | regenerated architecture references (citations and source-commit stamps only) |
| (this commit) | this record |

### Findings

| ID | Severity | Title | Verdict | Test |
|---|---|---|---|---|
| F14 | High (reopened) | A generated update's quotation of the sentence was adopted as the instruction | fixed by design: the instruction is rendered from the field | `test_f14_*` (2), the surface tests (3) |
| F21 | Medium (new; F18 reopened) | Clearing or renaming deleted sentences inside quotations | fixed by design: the statement is never edited | `test_f21_*` (2) |
| F18 | Medium (reopened) | Clearing or renaming a legacy method left its instruction behind | superseded: nothing is removed by text; a legacy sentence stays as written (open question 8) | `test_f21_*[legacy_block]` |
| F13 / F19 | Medium (reopened) | A changed inherited default defeats historical ambiguity handling | fixed: the binding fails closed | `test_f19_a_changed_inherited_default_*` (4) |
| F17 / F20 | Medium (reopened) | Recovery still requires a full-pipeline budget | fixed: resumable jobs are planned as their unfinished work | `test_f20_*` (2) |
| F22 | Medium (new) | Partial selection persistence is mistaken for completed selection | fixed: the selection is persisted whole, with a completion marker | `test_f22_*` (2) |
| F15, F16 | High, Medium | (unchanged) | confirmed fixed by the verify; kept as they are | unchanged |

F1 and F11 are kept as they are too. The successor placeholder
(`mvp-0.22-placeholder`) and the kill switch (`[required_method] enabled`)
stay. The new tests are in `tests/test_required_method_round3.py` (15
cases).

### 1. The instruction is rendered from the field, never stored (F14, F18, F21)

**Reproductions.**

- F14: an update of a generated cofactor-expansion item whose new prompt is
  `Compute det(B). The previous exercise said:`, a blank line, then
  `Use cofactor expansion in your answer.` The update writer kept it
  unchanged (the unchanged-method shortcut took the quotation for the
  writer's block), validation reported nothing, and grading enforced the
  method.
- F21: a stored body `Read the old rule: "Compute det(A). Use cofactor
  expansion in your answer. Then check your work." Compute det(B).`, with or
  without the writer's block after it. `override_payload(clear=True)` and a
  rename both cut the sentence out of the quotation.

**Design.** The stored statement never contains the instruction, and nothing
reads or edits the statement for it.

- **`learnloop.vault.required_method`.** `render_method_instruction`,
  `has_method_instruction`, `strip_method_instruction`,
  `restate_method_instruction` and the legacy-span matcher are deleted. Two
  functions replace them:
  - `method_instruction(method)`: "Use {name} in your answer.", from the
    item's field or the mapping a contract froze;
  - `presented_prompt(statement, method)`: the statement verbatim, then the
    sentence as its own paragraph. Without a method it is the statement
    exactly, so every other item's prompt and hash is unchanged.
- **Writers store the text as generated and change only the field.**
  - `normalize_required_method` notes `required_method:kept` (no
    `instruction_added`; the `render_instruction` parameter is gone);
  - `inherit_required_method` (PF variants) copies the field only;
  - the proposal writer (`_hold_required_method_to_rule`) keeps a revised
    prompt exactly as generated, whatever it quotes;
  - the owner's override (`override_payload`) never carries a `prompt` key
    (`prompt_changed` is gone from its audit and the CLI result);
  - the method-phrasing repair sets the field only;
  - synthesis, likewise.

  F15's rule is unchanged: a source statement is never rewritten.
- **Validation.** `required_method:not_stated` is gone, from doctor and the
  gold-set loader. What remains: `undecided`, `unknown_criterion`,
  `not_a_method_target`, and the advisory flags.
- **Every surface renders it.**

  | Surface | How |
  |---|---|
  | Desktop practice, exams, golden path (`item_presentation`) | a `required_method_instruction` block after the `prompt` block (`PRESENTATION_BLOCK_KINDS`, `dto.ts`) |
  | Desktop Today's queue detail | now renders the shared `ItemPresentation` (it showed `detail.prompt`) |
  | Terminal practice and Today screens | `presented_prompt` |
  | Reader's placed quick check (`reader_guidance`) | `presented_prompt` |
  | Exam review fields, adjudication case, guided redo | `presented_prompt` |
  | Tutor (`tutor_qa`, the source tutor's span provider, `find_sources`), the tutor's typed practice tool (`instructional/tools`) | `presented_prompt` |
  | Diagnoser (split context and history), learner-text gap sources | `presented_prompt` |
  | The grader (`build_grading_context`; the blind context and the hard-case harness build on it) | `presented_prompt(contract statement, contract required_method)`: the instruction the learner saw, from the frozen contract; without a contract, the item as presented now |

  There is no MCP read path on this branch.
- **Legacy statements are left as written.** A statement written under the
  earlier rules may still end with the sentence. It is not edited, so the
  learner and the grader see the sentence twice. Grading is unaffected: it
  reads the field. There is no display de-duplication and no doctor cleanup
  (open question 8).
- **The generation guidance and prompt versions are unchanged.** "LearnLoop
  appends 'Use {name} in your answer.' … itself: never write, quote or
  contradict it" is still what the learner sees. The schema docstrings a
  model may read are untouched too.

**Tests.**

- F14 (2): the verify's update is stored verbatim, presented as the
  quotation then the writer's block, and sent to the grader that way;
  validation reports nothing. A regrade's grader question renders the
  method the frozen contract presented after the item's field is cleared.
- Surfaces (3): the presentation block, the exam review, the Reader quick
  check and the tutor's practice tool render the sentence for a method item
  only; a published PF variant's stem carries no sentence and is presented
  with the parent's.
- F21 (2, the verify's body with and without a legacy block): clear and
  rename carry no `prompt`, and an accepted clear leaves the statement
  byte-identical, quotation included.

**Existing tests changed.** These exercised the deleted matchers, so they
are retired:

- the re-review's F14 and F18 tests in `test_required_method_rereview.py`
  (26 cases; 33 to 7);
- the second review's F14 tests in `test_required_method_reopened.py`
  (13 cases; 28 to 15). The guidance-version test stays. Assertions that a written
prompt ends with the block now assert the prompt is stored verbatim and
`presented_prompt` ends with the sentence:

- `test_required_method_items.py`, `test_required_method_authority.py` and
  `test_required_method_reopened.py` (F15's generated-item cases);
- `test_method_phrasing_report.py`, `test_required_method_grading.py` and
  `test_grading_hardcases.py`. The loader's `not_stated` refusal case is
  removed, and the cell-5 pair asserts the grader's rendered question.

The CLI help snapshot moved for `grading required-method`, whose help text
changed.

### 2. Historical reconstruction fails closed (F13/F19)

**Reproduction.** A historical contract (no `reference_content_hash`) was
graded under the inherited rubric R, and its exact item snapshot was
preserved. Then:

- the default rubric was changed to R2;
- the item was edited, and R written inline;
- the inline-R twin of the graded statement was checked verified;
- the revision actually graded was disputed.

The reconstruction resolved the inherited revision with today's R2, so that
revision no longer matched. The inline twin was returned as `frozen`, and
the attempt stayed **verified**.

**Fix.** `GradedContract.graded_reference_contents` reads only an inline
rubric exactly. An inherited one resolved to the default at the time, which
nothing records. When both hold:

- the item is known to have inherited a default (its current rubric or a
  recorded snapshot's is `None`);
- today's default does not reproduce the frozen rubric hash;

then the default the answer was graded under cannot be recovered. The
binding returns the inherited revision first, then whatever else matched,
as `ambiguous_default` (`AMBIGUOUS_DEFAULT_REVISION`). `bind_replacement_grade`
lowers the attempt to `unverified` whatever the candidates' statuses: it is
never `frozen`, and never verified from today's default.

A method contract that recorded its hash binds exactly as before. A
historical contract whose inherited default is still today's keeps the
`frozen` and `ambiguous` handling.

**Tests (4).**

- Historical: lowered whether the graded revision is disputed or not
  (`graded_revision=ambiguous_default`).
- Recorded: lowered only when the graded revision is disputed
  (`graded_revision=frozen`), else verified with no binding.

The earlier F13 and F19 tests pass unchanged.

### 3. PF resume (F17/F20/F22)

**Reproductions.**

- F20: a partially published two-candidate request with one missing
  judgment, retried with `max_calls = 1` and generous caps. Preflight
  estimated the whole pipeline (67 calls) and refused `over_budget` before
  the resume check ran.
- F22: selection persisted candidate by candidate. An interruption after the
  first commit left one `selected` row with `selection_json` and the other
  chosen candidate a survivor without it. The rerun took that for a finished
  selection, judged one candidate and admitted the request, stranding the
  other.

**Fix.**

- **Atomic selection.** `_select` writes every survivor's status and
  `selection_json` in ONE transaction (`_persist_all`). Each
  `selection_json` carries the complete selected order (`selected_order`)
  and a completion marker (`selection_complete`).
- **Resume by stage.** `selection_state` reads the persisted rows:
  - the marker exists: the selection finished, and the rerun resumes at the
    judgment and publication step with exactly that order;
  - a selection without the marker: the selection never finished. The rerun
    loads the survivors back as survivors and finishes the selection first
    (its judge's request is the checkpointed one), then judges and
    publishes;
  - no selection: the pipeline runs from its checkpoints.
- **Detected before routes and budget.** `generate_practice` calls
  `_resumable_job` for each target. It finds the claimable request of the
  same angle and versions whose candidates are not stale and whose
  selection started, and counts the selected candidates with no ledgered
  verdict. This runs before any route is resolved or budget planned.
- **Only the unfinished work is planned.** `_plan_resume` plans:
  - at the judgment stage, only the missing judgments (publication makes no
    call);
  - at the selection stage, the selection judge's one call (ensemble) and up
    to one judgment per slot.

  Only the jobs that run the pipeline need its routes. A resumable job
  resolves none (the selection route, for an ensemble selection-stage
  resume).
- **No unplanned spend.** A job planned as a resume that finds nothing to
  resume when it runs releases its request and reports
  `resume_unavailable`.
- **Order.** The re-review's approximate publication order
  (`_selection_rank`, open question 7) is gone: the order is the one
  persisted.

**Tests.**

- F20 (2): the verify's reproduction plans exactly 1 call under
  `max_calls = 1`. The retry makes one judgment call and no other call,
  publishes the waiting variant, and admits the request. A resumable job's
  dry run plans no pipeline role, candidate or freshness pair, and resolves
  no route.
- F22 (2):
  - the verify's interruption (the second selection write raises) leaves no
    partial selection; the rerun judges and publishes both chosen
    candidates and admits the request;
  - the partial state written directly is resumed as `selection` with no
    upstream call: two judgments, two publications, no stranded survivor.

### Fail-first

The base `e96075e94` was exported (`src`, `tests`, `pyproject.toml`) to
`fixtures-local/tmp/base_e96075e94`, with `migrations` linked in. No tracked
vault was linked. The final `tests/test_required_method_round3.py` ran
against it (`pytest -o pythonpath=src`; tracebacks confirm the export's
modules).

**13 failed, 2 passed.** Every failure is behavioural, none an import error:

| Finding | Failed on the base | What the base did |
|---|---|---|
| F14 | 2 | adopted the quoted sentence as the block (no instruction block after it); the grader's question for a frozen method after the field was cleared had no sentence |
| Surfaces | 3 | no `required_method_instruction` block kind; the Reader quick check and the tutor's tool showed the bare statement; the PF variant's stem stored the sentence |
| F21 | 2 | clear and rename cut the sentence out of the quotation |
| F19 | 2 | the historical regrade stayed `verified` (disputed and undisputed) |
| F20 | 2 | the dry run was `over_budget` (calls exceeds max_calls); the resumable job's plan resolved and planned the pipeline's roles |
| F22 | 2 | the interruption left one candidate's selection persisted; the partial state resumed as `required_method_judgment`, not `selection` |

The 2 that pass on the base are the intended controls: the recorded
contract, disputed and undisputed.

### Gate

The gate ran on the tree at `7beb18d2c`. The only uncommitted changes were
this record and the pointer in `method-explicit-items.md`. `TMPDIR` was the
worktree's `fixtures-local/tmp`. The full suite and the durability lane each
ran under `/tmp/learnloop-fullsuite.lock`, one after the other. This step
was interrupted by a restart: it resumed from 41 uncommitted files and no
commits since `e96075e94`, and every gate step below was run after the
restart, on the final tree.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| Targeted run before the commit (the 132 test files touching the changed modules, plus the CLI-help and assessment characterization tests) | **2517 passed** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10559 passed**, 0 failed, 0 skipped (48 warnings, 581.31s). That is 10584 − 40 retired + 15 new |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10460 deselected, 0 failed (1 warning, 104.71s) |
| Frontend (`apps/learnloop-tauri`): `npm install`, `npm run typecheck`, `npm test`, `npm run frontend:build` | typecheck clean; vitest **74 files, 479 tests passed** (the new `ItemPresentation.test.tsx` included); build succeeded |
| Cargo | not applicable: nothing under `src-tauri` changed |
| `db_generate_reference.py`, then `db_validate_reference.py` | **0 errors**: schema head 199, 318 table notes. Only citations and source-commit stamps moved (`7beb18d2c`) |
| `validate_vault.py` | passed (1,099 notes, 22,001 links) |
| CLI help snapshot | `grading required-method` moved, because its help text changed (`test_cli_help_snapshot.py` passes) |
| Defaults and template snapshots | unchanged (no configuration key) |

There were no paid calls and no live check: no external interface changed,
and the generation prompts and their versions are unchanged. No key, env
file or vault database was read, and no tracked vault was opened. Main was
not merged in.

### Not changed, and open questions

Open questions 1, 3 and 4 still stand. Question 2 is now settled as
fail-closed for an unrecoverable inherited default. Questions 5 and 6 (a
model-written duplicate, a stored-prompt check's author) no longer apply,
since nothing reads the statement for the instruction, and question 7 is
closed by the persisted order. New:

8. **Legacy statements show the sentence twice.** A statement written under
   the earlier rules (the branch's own writers, before round 3) may end with
   "Use X in your answer.", and the rendered block repeats it. Nothing
   removes it: text surgery is what this round retires. If the owner wants
   it gone, the options are a display-only de-duplication that never
   reaches grading, or a one-time doctor-proposed cleanup the owner
   confirms. Neither is built. These statements exist only in vaults that
   ran this unmerged branch.
9. **An inherited default nobody can recover lowers every historical
   regrade of that item.** This is the fail-closed rule the task asks for.
   A changed default, together with an item known to have inherited it,
   makes every historical regrade unverified, even one whose graded
   revision was verified. Contracts frozen from now on record the revision
   and are unaffected.
10. **A pre-round-3 complete selection resumes as `selection`.** Rows that
    this branch wrote before round 3 carry no completion marker, so their
    selection is redone, possibly with a fresh selection call when the
    survivors changed. That is honest, and planned under the caps.

## Final verify fixes (stage `method-explicit-3`, final verify)

The final verify of the round-3 re-review (Codex job
`20261015-010744-fq1jgd`, read-only, `c391dd8b8..grading/method-explicit-items`
at `bcff06523`, with the record in `method-explicit-3-codex-review.md`)
returned **REOPENED**:

- F9 (Medium) was confirmed closed.
- F1 (High) was still open in two historical cases. Both reproduced in
  memory, as the verify did, and both are fixed by one rule. No finding was
  rejected.

| Commit | What |
|---|---|
| `021f65890` | the fix and its tests |
| `46be22d71` | regenerated architecture references (citations, capped source-path lists and source-commit stamps only) |
| (this commit) | this section, a correction note under the re-review's remaining limits in `method-explicit-3-codex-review.md`, and the pointer in `method-explicit-items.md` |

Counts (`git diff --numstat bcff06523..021f65890`): `src/` +116 / −50,
`tests/` +230 / −12. No migration, no new table, no configuration key, no
prompt version, no CLI help and nothing under `apps/` changed.

### The two cases

1. **An unrecoverable rubric.** A contract frozen under the induction
   method before review F1 recorded the legacy hash (statement, expected
   answer and rubric R1, no method). The method is cleared, and that
   cleared revision is disputed by a check written after the fix. Then the
   live rubric becomes R2, and no snapshot kept R1. No rebuild reproduced
   the recorded hash, so `graded_reference_contents` fell back to it. The
   cleared question has exactly that hash, so its dispute lowered the
   induction answer (`key_status=disputed; graded_revision=frozen`).
2. **A contract without a recorded hash.** A method contract frozen before
   contracts recorded a hash (round 2, F19) was invisible to the collision
   rule, which read only recorded hashes. With a legacy check of the
   induction question, clearing the method still read `book_solution` (the
   cleared question verified) with no fresh check.

### One rule

**A method contract binds its answer key only where that binding is
established exactly. It is established by a hash recorded with its key
identity, or by rebuilding the revision graded from a rubric the item is
known to have had. Otherwise the binding is AMBIGUOUS.**

An ambiguous binding is isolated, and it fails closed:

- **No check of any revision decides it.** A check of another revision
  never verifies it, and a dispute of another revision never lowers it.
  Nothing tells its own checks from those of the question with its method
  cleared, which may carry the same hash, so no check is read at all.
- **It needs a fresh check.** Its key status is `changed_since_check`. A
  regrade under it is lowered whatever any check says
  (`key_status=changed_since_check; graded_revision=ambiguous_method`), and
  the binding names only its own revision. The grade certifies nothing.
- **It lends no credit.** A question without a method takes no credit from
  a legacy check that an ambiguous method contract may own.

Where verification is displayed, `changed_since_check` now reads "Needs a
fresh check: the answer key changed since it was checked". That is the key
label the desktop and the sidecar show for an item.

**Scope.** Only vaults that ran this unmerged branch have such contracts:
main has no `required_method`. An ambiguous contract is a method contract
this branch froze before `021f65890`, since every method contract frozen
from now on records its key identity. The collision rule reads only method
contracts, so an item without one (every item on main) is unchanged.

### Fix

1. **A method contract records its key identity.** Next to
   `reference_content_hash` it now records `key_identity: "method-aware"`.
   This is the field and value every check has recorded since the
   re-review (`KEY_IDENTITY_FIELD`, `KEY_IDENTITY`), not a new mechanism.
   - Without the field, a contract frozen after the merge whose rubric
     changed with no snapshot could not be told from a legacy one. The rule
     would then fail it closed on main.
   - With it, ambiguity is confined to this branch's earlier contracts.
   - Only method contracts carry it, so only their contract hash changes.
     Contracts are content-addressed, so a method item presented again gets
     a new contract version. Every other contract is unchanged.
2. **`GradedContract.graded_reference_contents`** (method contracts):
   - With the identity, the recorded hash binds exactly (`frozen`), with
     or without the rubric.
   - Without it (this branch, before `021f65890`), the revision is rebuilt
     with each known rubric: the current one, each snapshot's, and an
     inherited one.
     - A rebuild with the method reproduces the hash: it binds as recorded.
     - A rebuild without the method reproduces it (the legacy identity): it
       binds the method-aware revision with the legacy mapping, as the
       re-review did.
     - No rebuild reproduces it: `([recorded], "ambiguous_method")`.
       This was verify case 1.
   - A historical method contract (no hash) that no rebuild reproduces was
     `unresolved` and bound to every checked revision. It is now
     `(["unrebuilt:<item_content_hash>"], "ambiguous_method")`.
   - Unchanged:
     - `frozen`, an exact rebuild or the attempt-time revision;
     - `ambiguous`, the round-2 F19 rubric provenance among method-aware
       rebuilds of the same question;
     - `ambiguous_default`;
     - every outcome for a contract without a method.
3. **`bind_replacement_grade`.** `ambiguous_method` and
   `ambiguous_default` (`UNESTABLISHED_REVISIONS`) read no check. The
   status of an exercise import is `changed_since_check`, and the grade is
   lowered. `not_applicable` content is never gated, as before.
   - For `ambiguous_default` the outcome is unchanged: it was already
     lowered whatever the statuses.
   - Only its rationale changes. It now shows `changed_since_check`
     instead of whichever check came first.
4. **The collision rule.** `legacy_method_identity(connection, item_id,
   hash)` replaces `legacy_method_contents`. A legacy check of a question
   without a method does not apply when either holds:
   - a method contract recorded that hash (as before);
   - a method contract recorded no hash at all. Its legacy identity cannot
     be named, so this fails closed for every question without a method on
     that item. This was verify case 2.

   A check written now (with its identity) applies as before.

| Case | Base (`bcff06523`) | Now |
|---|---|---|
| Legacy-hash contract, rubric lost, the cleared question disputed | lowered by that dispute (`key_status=disputed`, `frozen`) | needs a fresh check (`changed_since_check`, `ambiguous_method`); the dispute is not read |
| The same, the cleared question freshly verified | verified | needs a fresh check |
| The same, the cleared question left alone | verified (legacy checks) | needs a fresh check |
| Historical contract, rubric lost (the same three) | `unresolved`: lowered by the cleared question's dispute, else verified | needs a fresh check |
| Historical contract, the method cleared | the cleared question `book_solution` | `changed_since_check` until a check written now verifies it |
| Historical contract rebuilt exactly, the cleared question disputed | verified, no binding | verified, no binding (unchanged) |
| A contract frozen now, rubric lost | bound as recorded | bound as recorded, by its identity |
| This branch's contract with a method-aware hash and no identity, rubric rebuilt | bound as recorded | bound as recorded |
| The same, rubric lost | bound as recorded | needs a fresh check (fail closed) |
| An item that never had a method (main) | unchanged | unchanged |

**The cost of failing closed** (vaults that ran this branch only):

- A regrade under an ambiguous method contract is lowered and stays
  lowered, since statuses are never raised. That holds even where the
  revision graded was in fact verified.
- A contract this branch froze between review F1 (`2d7c49483`) and
  `021f65890` recorded a hash that names the method, but not its
  identity. When its rubric is lost it is ambiguous too: only a rebuild
  can tell its hash from a legacy one.
- With any method contract that recorded no hash, every question without a
  method on that item needs a fresh check before a legacy check counts for
  it, not only the cleared one.

**Superseded.**

- **Round-2 F13, `unresolved`.** Under F13 above, a historical method
  contract that cannot be rebuilt stood when every checked revision was
  verified, and was lowered (`unresolved`) when one was not. Those checked
  revisions include the question before its method was set. Such a contract
  is now ambiguous and needs a fresh check either way.
  - Its test is renamed
    `test_f13_when_the_graded_revision_cannot_be_rebuilt_it_needs_a_fresh_check`,
    and both of its cases expect that.
  - `unresolved` stays for a contract without a method, which a regrade
    reads only when the item has a method now.
- **The re-review's remaining limits** (`method-explicit-3-codex-review.md`).
  - The third (a legacy contract whose rubric cannot be rebuilt is read as
    recorded) is fixed. A note there points here.
  - The first, second and fourth still stand.
- **The `pre_fix` fixture.** It now also strips the identity from its
  contract, since the code it emulates recorded none.

### Tests (10)

In `tests/test_required_method_round3_final_verify.py`:

- The verify's first case (`recorded`, the legacy hash) and its historical
  twin (no hash), each with the cleared question disputed, verified or left
  alone by a check written now (6). Every case needs a fresh check and
  names only its own revision.
- The verify's second case (1). The cleared question reads
  `changed_since_check` and `unverified`, and only a check written now
  verifies it. The historical contract, rebuilt exactly, keeps its own
  binding, so the cleared question's dispute does not reach it.
- A contract frozen now (1). It records its identity, and with its rubric
  lost it still binds exactly: verified by its revision's check, lowered by
  that revision's dispute (`frozen`).
- This branch's contract with a method-aware hash and no identity (2). It
  binds exactly when rebuilt (the control), and needs a fresh check when
  its rubric is lost.

### Fail-first

The base `bcff06523` was exported (`src`, `tests`, `pyproject.toml`) to
`fixtures-local/tmp/base_bcff06523`, with `migrations` linked in. No tracked
vault was linked. The final `tests/test_required_method_round3_final_verify.py`
ran there with the worktree's interpreter, `pytest -o pythonpath=src`.
Tracebacks and `source_service.__file__` confirm the export's modules.

**9 failed, 1 passed.** Every failure is a behavioural `AssertionError`;
none is an import, type or attribute error.

| Test | What the base did |
|---|---|
| Case 1, legacy hash, cleared question disputed | lowered by that dispute: `key_status=disputed; graded_revision=frozen` |
| Case 1, legacy hash, cleared question verified or left alone (2) | `verified` |
| Case 1, historical, cleared question disputed | lowered by that dispute, bound `unresolved` to the cleared question's hash |
| Case 1, historical, cleared question verified or left alone (2) | `verified` |
| Case 2 | the cleared question `book_solution`, where `changed_since_check` was expected |
| A contract frozen now | no `key_identity` in the contract |
| This branch's contract, rubric lost | `verified` (bound as recorded) |

The one that passes on the base is the intended control: a rebuilt
contract of this branch binds exactly.

### Gate (final verify)

The gate ran on the tree at `46be22d71`. The only uncommitted changes were
the three review records. `TMPDIR` was the worktree's `fixtures-local/tmp`.
The full suite and the durability lane each ran under
`/tmp/learnloop-fullsuite.lock`, one after the other. This completes the
gate the re-review left unfinished.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| Targeted run while fixing (110 test files touching the changed modules, plus `test_architecture.py` and `test_instructional_layering.py`) | **1970 passed** |
| The review test files after the last edits (`test_required_method_round3_final_verify.py`, `_round3_rereview`, `_round3_review`, `_rereview`, `_reopened`, `_round3`, `test_reference_gate_imports.py`, `test_source_exercise_import.py`) | **123 passed** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10601 passed, 1 failed**, 0 skipped (48 warnings, 482.79s). That is 10592 + 10 new tests |
| The one failure, rerun alone | `test_learner_pick_proposal.py::test_the_delivery_carries_r1s_decision_of_the_block_that_served_it`: **passed 3 of 3** alone, and its file **14 passed**. Under `-n auto` load, router R1's `plan_block` row was not yet visible. It touches none of the changed modules, and its items have no method |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10503 deselected, 0 failed (1 warning, 135.82s) |
| Frontend and cargo | not applicable: nothing under `apps/` changed |
| `db_generate_reference.py`, then `db_validate_reference.py` | **0 errors**: schema head 199, 318 table notes, schema unchanged. Only citations, capped source-path lists and source-commit stamps moved (`46be22d71`) |
| `validate_vault.py` | passed (1,099 notes, 22,001 links) |
| CLI help snapshot, defaults and template snapshots | unchanged: no command, option or configuration key changed. The template `.pyc` was cleared before the suite, and their tests pass in it |
| Undefined names and unused imports in the changed files (`ruff --select F821,F401,F811,F841`) | none new: 16 in the three `src/` files before and after, all pre-existing. The test files are clean |

There were no paid calls and no live check. No key, env file or vault
database was read, and no tracked vault was opened. Main was not merged in.
