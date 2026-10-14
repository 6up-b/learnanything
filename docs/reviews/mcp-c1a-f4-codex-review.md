# Chat frontend C1a, F4 round 3: the Codex review and its fixes (F4 round 4)

**Stage:** `mcp-c1a-f4`, branch `mcp/c1-read-context` (worktree `learnanything-mcp`).
**Reviewed:** the F4 round 3 fix only, `4493140a2..f6c6c73b8` (implemented in `3e1725836`, recorded in
`f6c6c73b8`): one guarded renderer (`AnswerTextGuard.render`) for every answer-derived text in
`learning_context`, provenance followed back to the originating answers, the output schema typed and closed.
**Codex job:** `20261014-160833-QIinAQ`. **Fixed in:** `c06f73aae`. Main is `4108e1ccd` (mvp-0.24); it was not
merged here (convergence happens at landing).

## Findings

| ID | Severity | Title | Verdict | Commit | Test (fails before the fix, passes after) |
|---|---|---|---|---|---|
| F1 | High | Derived beliefs lose the originating diagnosis's context | **fixed** | `c06f73aae` | `test_a_diagnosis_s_context_follows_its_text_into_every_belief_drawn_from_it`, `test_a_joint_grader_s_history_follows_the_causes_it_wrote`, `test_provenance_cycles_are_followed_to_the_end` |
| F2 | High | Generated prerequisite titles (and their slug ids) bypass the renderer | **fixed** | `c06f73aae` | `test_a_prerequisite_drafted_from_an_unpinned_answer_shows_neither_its_title_nor_its_id`, `test_text_a_model_wrote_while_shown_a_withheld_topic_name_follows_it`, `test_every_text_field_of_the_output_is_guarded_or_not_answer_derived` (extended) |
| F3 | Medium | Malformed provenance lists silently discard unknown links | **fixed** | `c06f73aae` | `test_a_provenance_list_with_an_unreadable_member_withholds` (6 cases), `test_a_diagnosis_receipt_with_an_unreadable_member_withholds` (18 cases) |

All tests are in `tests/test_mcp_c1a_review.py`. None was rejected.

### Reproduction (fail first)

The new tests were written first and run against `f6c6c73b8`. **28 of 28 failed**, each for the reason the
finding names. Re-checked before the gate: with `f6c6c73b8`'s `learner_context.py` in place (plus a four-line
shim defining the names the new tests import: `LO_ALIAS_PREFIX`, `TOPIC_WITHHELD`, `TOPIC_FIELDS`,
`TOPIC_ID_FIELDS`), **30 of 30** selected cases failed: the 28 fail-first cases, the topic-name link test and the
extended schema test (`8841` found in a candidate's `topic` and `learning_object_id`). With the fix restored
they pass.

- **F1.** A pinned answer's live diagnosis was shown the unpinned historical `att_legacy` (its receipt names it)
  and its causal view laid `Believes LEGACY KEY 8841 a row swap negates the volume for every matrix` on the
  pinned answer's own error event. `Repository.error_events_for_attempt` returns the overlaid cause (asserted).
  The hypothesis materialized from that event, its recurrence group, the misconception and candidate
  normalized from it, and the candidate a gap on the diagnosis (`source_kind='diagnosis'`) created were
  released with the key. Only the diagnosis summary was withheld. The joint grader variant failed the same
  way: a cause written by a grader whose C4 history named `att_legacy`. In the cycle variant, two diagnoses
  were each shown the other answer's hypothesis, and one of them was also shown `att_legacy`. Both hypotheses
  were released.
- **F2.** A prerequisite created from `att_legacy`'s stuck answer, titled `Legacy key 8841: a row swap negates
  the volume` with id `lo_ltg_legacy_key_8841_a_row_swap_negates_the_v_<hash>` (the pipeline's own `slug`).
  Its title appeared as `topic` and `target_topic` and its id in every section an LO appears in. A topic
  search for `8841 negates` matched it.
- **F3.** `["e1", x]` with `x` one of `null`, `""`, `false`, `0`, `[]`, `"  "` released the misconception (the
  invalid member was dropped and `e1` resolved to the pinned answer). For a diagnosis receipt, a null, empty or
  false member in any of its six lists released the summary, and so did a citation with no answer.

## What changed

**One closure for provenance (F1).** `AnswerTextGuard.closure` follows a graph of provenance nodes to the end.
The nodes are an answer's grading, a diagnosis, a hypothesis, an episode, an error event, a registry belief, a
misconception, a candidate, a gap's reading and a generated topic. Cycles are handled with Tarjan's strongly
connected components, done iteratively. Every node of a component gets the whole component's closure, so a
closure is complete whichever node is read first; the test checks two orders. The links are:

- **An answer's grading** (`graded`) links to every completed live diagnosis of that answer, superseded ones
  included. The overlay lays a diagnosis's causes on the answer's events, and the factor projection, the
  normalizer and the gap pipeline read them. What an earlier diagnosis supplied stays in the beliefs drawn from
  it. The grading node also includes the joint grader's C4 history (`diagnostic_augmentation_receipts`, the
  only other-attempt material a joint grader is given) and the answer's topic name when that topic was
  generated (the grader was shown it).
- **A diagnosis** links to everything its context receipt says it was shown: the failure, success and history
  answers, its citations, the answers its text names, its hypotheses and recorded beliefs (each followed
  onward) and the generated topics in its neighbourhood. If there is no receipt, or a list cannot be read, the
  link is missing.
- **Beliefs** follow their error events into the answer's grading. Hypotheses follow their own answer's grading
  and their episode. Misconceptions follow their promotions. Candidates follow their error hunts and the gaps
  that created them.
- **A gap's reading** links to its words and to the diagnosis it read (`source_id`, the omission F1 names). It
  also links to a generated topic it is anchored on.

Every section renders from these closures. A diagnosis summary is the closure of its diagnosis.

F1 asked for the originating diagnosis to be carried through materialization, promotion and gap creation. No
record names which diagnosis supplied a belief's text, and existing records would need it too. So the read side
follows **every** completed live diagnosis of the answer, which is a superset of the originating one. It needs
no migration, no write-path change and no replay change. The conservative consequence: once any diagnosis of
an answer was shown unsafe material, every belief drawn from that answer's grading is withheld (entries, counts
and status kept, reason noted). The round 3 test's positive control `mc_swap` is now withheld for exactly this
reason. A belief drawn from the learner's question during that answer (`mcand_row`) still shows.

**Topic names and ids have one renderer too (F2).** Every topic name and id in `learning_context` goes through
`AnswerTextGuard.topic` and `AnswerTextGuard.lo_ref`.

- **Which topics count as generated:** those marked by `created_from_learner_text`, an id of the form
  `lo_ltg_`, or a gap recording the creation.
- **How a generated name is rendered:** like any answer-derived text, with the provenance of its drafting: the
  gaps that created it, and every generated topic created no later in a shared subject, since the drafter is
  shown the subject's concept titles. The id's words get the same check.
- **While a generated name is withheld:** the entry keeps its place and shows `a topic named from the learner's
  own words, its name withheld: <why>`. Its id is the opaque `lo_withheld_<sha256[:16]>`, which
  `learning_context` accepts back as a named id. A topic search does not match its words, since a match would
  confirm them.
- **Any other name** (one the vault authored) is released as the vault has it. The private `_AUTHORED` origin
  allows this, only from `topic`/`lo_ref`, and an AST test pins it.
- **Schema partition:** `TOPIC_FIELDS` (9) and `TOPIC_ID_FIELDS` (9) join `ANSWER_DERIVED_FIELDS` (10) and
  `NON_ANSWER_FIELDS` (now 70) in partitioning the 98 text fields. The schema test now plants a prerequisite
  drafted from the unrevisioned answer in every section. It checks that every name or id value is a
  `GuardedText` or a withheld stand-in, that each of the 18 fields stood in at least once, and that the drafted
  title, its id, its slug and `8841` appear nowhere.
- **ID audit:** the other id fields are ULIDs, except `recurrence_groups[].group_key`, a SHA-256 digest of the
  root statement (see Q13). Concept and practice-item ids are not in the output.

**Strict provenance lists (F3).** `_id_list` returns None (unreadable, a missing link) unless every member is a
nonempty string. `_cited_answers` does the same for citations, each of which must name an answer.

### Claims, revisited

| Claim the review rejected | Now |
|---|---|
| "Every answer behind it" receives protection and revision checks | Followed transitively through grading, every live diagnosis, C4 history, receipts and gaps; cycles closed |
| The 88 other fields are non-answer-derived "by construction" | 18 of them were topic names and ids; they are now released only by the guard's name renderers, the other 70 are ids, timestamps, codes and fixed notes |
| Unreadable provenance fails closed | A list with any invalid member, or a citation with no answer, is unreadable as a whole |

### Q9 and Q10 (the round 3 open questions), assessed

- **Q9 (a regrade re-mints error-event ids, so a belief listing the old ids is withheld):** confirmed and kept.
  This agrees with the review: the conservative withholding is right, and the remedy is durable provenance
  (desktop scope: keep event ids across a regrade, or have re-normalization rewrite the source lists), not a
  weaker guard. Under round 4 it is unchanged: the missing event is still a missing link.
- **Q10 (a tutor question about an item asked outside any attempt is withheld for lack of a revision):**
  confirmed and kept, consistent with the revised spec. Round 4 extends its reach. A prerequisite *drafted*
  from such a question is now also withheld: its name shows the label and its id the alias. Recording the
  item's contract (or snapshot hash) on `question_events` when the question is asked would let both show
  safely (desktop scope).

### New open questions for the owner

- **Q11 (the subject cascade for generated names):** the drafter is shown the subject's concept titles
  (`concepts_in_subject`, up to 40). Following provenance completely therefore makes every generated topic
  created later in a subject follow every earlier one. Once one generated name is withheld (Q10, a cold
  check, an unpinned answer), later generated names in that subject are withheld too, until it clears.
  Recording on the gap row which concepts the drafter was shown would narrow this to what was actually shown.
  This is desktop scope. No generated topic exists on either copy today.
- **Q12 (other tools show topic names unguarded):** `today` (plan topics) and `progress` (goal topics, the
  assumed list, retention risks) read vault titles and ids directly. This review covered `learning_context`
  only (the stage's range), so a generated name withheld there can still reach a chat host through those two
  tools. Recommended follow-up: route their names through `AnswerTextGuard.topic` / `lo_ref`
  (`retention_risks` already takes `topic=`/`ref=`).
- **Q13 (the group key is a digest of the root statement):** `group_key = grp:` + SHA-256 of the normalized root
  statement. No text escapes. But a client that guesses a withheld root statement exactly (after
  normalization) can confirm the guess. Assessed as low risk, so not changed. A keyed digest would close it if
  wanted.
- Q1-Q10 are otherwise unchanged.

## Manual run (backup-API copies, no model, no network)

`learning_context` (30 traces) ran through the SDK client on the `fixtures-local/c1a-manual` backup-API copies.
Every model client was refused and no paid route was asked for. It ran on the fixed code and on `f6c6c73b8`:

| Vault | fixed | round 3 | output |
|---|---|---|---|
| linear_algebra | 367 ms | 396 ms | **identical**: 30 traces (12 answers shown), 2 open hypotheses (1 shown, 1 withheld as a probe), 7 retention risks, scope 21 topics, 0 aliases |
| probability | 163 ms | 148 ms | **identical**: 2 traces (2 answers shown), 1 retention risk, scope 18 topics, 0 aliases |

On the owner's data the fix withholds nothing that was shown before. Neither copy has a completed diagnosis, a
generated topic, an active misconception, an open candidate or an open gap. The shown hypothesis's answer has
no C4 history. 6 of the 11 C4 receipts on the linear_algebra copy name history. Only one of those answers has
an open belief: the hypothesis already withheld as a diagnostic check, because protection is checked first.
Re-checked before the gate by a direct read-only call (`Repository.attach(..., read_only=True)`, no model
client, API key variables blanked) of both versions' `learning_context` on the same copies: the JSON output
(minus `as_of`) is byte-identical between `c06f73aae` and `f6c6c73b8` on both, with the counts above.
**Paid calls: 0; cost: $0.**

## Gate (F4 round 4)

Run on `c06f73aae` (the fix step resumed after an interruption: the gate, the fail-first check and the manual
comparison were rerun on that commit), with TMPDIR set to the worktree's `fixtures-local/tmp`:

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **21 kept, 0 broken** |
| `git diff --check 4493140a2..HEAD` | clean |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10725 passed**, 0 failed, 16 warnings (9:37); round 3 had 10696, plus the 29 new cases |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10625 deselected (1:47) |
| The C1a tests alone (`test_mcp_c1a_review`, `test_mcp_tools`, `test_mcp_runtime`, `test_mcp_http`, `test_mcp_cli`) | **86 passed** (57 before, plus 29: the 28 fail-first cases and the topic-name link test) |
| DB reference generate/validate, CLI help snapshot, config references | not applicable: no schema, CLI or config change (the MCP output schema's field types are unchanged) |
| npm / cargo | not applicable: nothing under `apps/learnloop-tauri` changed |
| Paid calls | none ($0) |
