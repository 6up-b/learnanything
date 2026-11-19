# K6 fix round A

Nine rows of the K6 review (`docs/reviews/refactor-k6.md`, ledger rows in `refactor-bug-ledger.md`), on
`fix/k6-round-a` from main `f297905e49`, one commit per row. Each row's sequence was first written as a test and
run on the unfixed code; all nine failed for the reason the review gives, K6-14 (filed as suspected) included.
No row needed a migration, a config switch, an identity-pin change, a prompt change at fixed inputs or a
different rebuild result: `tests/test_identity_pins.py` passed after every source commit. Every change affects
new events, or what may reach a model or a screen from now on. Stored attempts, reveals and exposures keep the
meaning they had; the stored rows that are read differently are named per row.

## Per row

### K6-2: the pinned tutor of a bound library ask (`21cd7ada40`)

- **Reproduced.** Fail-first: `count_hint_equivalent_question_events('pi_eigen_1', None, item_window_only=True)`
  was `0`, not `1` (the question row had no item).
- **Before:** "Ask the tutor" from a library ask made inside a bound workbench session filtered the pins by the
  item, but `RD.ask` got no binding, and `tutor_qa.ask_question` also dropped any binding whenever a source
  provider was given. The answer's help never counted on the item.
- **Now:** the handler builds the very `BoundAsk` the workbench's Reader Ask builds (`reader_tutor.restriction`
  and `bound_ask`, from the workbench session the ask recorded in its manifest), with that path's switches, and
  passes it with the stored restriction; `tutor_qa` keeps the binding with the pins-only provider. A bound
  answer's cited pins are one source review: the T6 cited-span debit no longer also runs for a bound answer.
  If the session now names a different item, the request is refused (`caller_mismatch`).
- **Who:** a learner using "Ask the tutor" from a bound library ask: the substantive answer counts as a hint on
  the item (once), and its overlap is a `tutor_answer` reveal. No stored row is read differently.
- **Deviation:** none. The binding comes from the session the ask recorded, since the tutor RPC takes no
  session; an ask with no recorded session (older rows) stays unbound, as before.

### K6-3: the linked fallback (`2f6c051931`)

- **Reproduced.** Fail-first: the item's own solution text was among the tutor's `source_spans` with the provider
  failing (`assert OWN_SOLUTION not in {...}`), and the cited fallback passage wrote no source review
  (`assert [] == [event_id]`).
- **Before:** the linked spans (the fallback when retrieval declines or fails) had only the cross-source span
  builder's exam and semantic-link checks; the item rules (`linked_reference_filter`) were applied to their
  references only. The cited-span debit ran only when the provider's spans were used.
- **Now:** the linked spans pass the injected `linked_reference_filter` before hydration (a span whose block
  cannot be read is withheld; what was withheld is on the delivery receipt as `linked_withheld`), and a cited
  passage is debited whichever branch delivered it, whenever a provider was in play.
- **Who:** a learner practising an item whose LO links a passage that is the item's own solution, or lies in the
  body region after an item-linked example or a solution lead: that passage no longer reaches the tutor or a
  chip. Cited fallback passages now debit the item like retrieved ones. No stored row is read differently.
- **Deviations.** (1) With no provider at all (`source_retrieval.enabled` off) the debit is not added:
  `test_source_retrieval_guards::test_linked_spans_without_retrieval_are_not_debited` pins that switch's
  "unchanged" promise. The filter itself applies on that path too (protection). (2) Three delivery-fix tests
  (`test_tutor_delivery_fixes`, F1 group) linked a teaching passage that sits inside the item's example or a
  solution region by the production region rule; their fixtures gain a section break so they still test
  reference refusal.

### K6-4: the whole Reader request on the phone, and ancestors (`bba27da874`)

- **Reproduced.** Fail-first, phone: with a rule-2 exam unit (exam material, not held out) beside the selection
  and a theorem the selection cites by number in another exam unit, both sentinels were in the provider's
  context at the phone origin (`assert NEIGHBOUR_SENTINEL not in given` failed). Desktop, ancestors: after the
  passage a root answer quoted was held out, the follow-up's thread still carried that answer
  (`all("Prelude sentinel" not in answer_md ...)` failed).
- **Before:** the phone refused a protected selection, then built the context under the held-out partition
  only; `ask_provenance` did not name the manifest's spans; ancestors' answers were sent as stored.
- **Now:** at a phone origin the handler passes the phone's own predicate (`phone_reader.destination_material`:
  `exam_material(...).material`, refused when unreadable) as `context_withheld`; `reader_dialogue.ask` and
  `tutor_qa.ask_question` join it to the held-out material for neighbours, references, retrieved passages and
  the excerpt. An ancestor's answer is sent only when none of the passages its stored exchange names is
  withheld now (held-out on the desktop, exam material on the phone; fail closed for an exchange the events
  don't account for); otherwise `ANCESTOR_ANSWER_WITHHELD` stands in, and the learner's question stays.
  `ask_provenance` now also names every span of the stored manifest.
- **Who:** phone learners: neighbours and cited blocks in exam material no longer reach the model or the phone.
  Desktop and phone: a branch continued after a mark no longer resends the earlier answer. **Stored rows read
  differently:** the phone's Ask history and its final check now judge each stored exchange's manifest spans
  too, so an older exchange whose context held phone-withheld material drops from the phone's history (the
  desktop keeps it).
- **Deviation:** the placeholder line is new wording ("[An earlier answer is left out: it drew on material that
  is now held out.]"), modelled on `EARLIER_ANSWER_LEFT_OUT`; it reaches a model, never the screen.

### K6-5: reopened results (`088d9058c7`)

- **Reproduced.** Fail-first: after a held-out mark, the cached organizer notes came back and the organizer
  judged the marked passage when uncached (`DID NOT RAISE`); the phone's job poll returned the stored answer
  (`'Spans sentinel' not in json.dumps(polled)` failed).
- **Before:** `organize` reused stored notes or judged the ask's stored keys without a protection read; the ask
  and notes jobs re-delivered their kept result unchecked; the phone host returned a completed `reader.ask`
  job's stored result on a poll or a same-key retry.
- **Now:** `library_ask.refuse_withheld` (exam material, fail closed) runs before the organizer reuses or judges;
  the ask and notes jobs carry `deliver_passages`, run at every read; the host's `_current_view` judges a
  completed `reader.ask` by `phone_reader.sendable_exchanges` (now the one judgment the fresh answer and the
  history use as well) and answers `held_out_material` with the phone history's wording. Library refusals use
  the kept comparison's wording.
- **Who:** a learner reopening notes or a kept library answer after marking a passage: refused whole, "Ask again"
  searches fresh. A phone polling or retrying a finished Ask after a mark: refused; the stored job row and the
  desktop's history are unchanged. No stored row is read differently apart from that delivery check.
- **Deviation:** refuse whole rather than drop the passage, following the kept-comparison rule (a derived
  answer whose dependencies are now withheld is withheld). The pinned-tutor job is not given the delivery
  check (not in this row's sequence).

### K6-6: the Reader reserve detector (`d8db9aa3d4`)

- **Reproduced.** Fail-first: a reserved stem reproduced only in the verified excerpt, or only in the bridge,
  was not burned (`assert surface_id in answer["burnedSurfaceIds"]`, `in []`).
- **Before:** detection read the explanation and the citation labels only.
- **Now:** the verified excerpt's quote, the bridge and any citation excerpt are held to the same lexical floor
  (`lexical_reserve_reveal`, unchanged, so the contamination detectors' shadow comparison is unchanged); the
  exposure detail records `matched_field` for a detected reserve. Caller declarations and hash/fingerprint
  checks are as they were.
- **Who:** a reserve the learner read in an excerpt or bridge is no longer eligible as unseen (one
  `externally_reported` exposure). No stored row is read differently.
- **Not done:** "a single collision across repeat presentation of the same display id" needs DJ1's display id;
  today detection runs once per generated answer, and the test asserts one exposure for that answer.

### K6-7: the Teacher's help withdrawal (`863c12ca99`)

- **Reproduced.** Fail-first: a help reply with the solution only in a choice left the check open
  (`assert view["open_check"] is None` failed).
- **Before:** the withdrawal compared `turn.message` alone with the committed solution.
- **Now:** it compares the turn's displayed fields joined (`_displayed`: message, choices, prediction, check,
  plan, recap, visual goal). Withdrawal, its receipt, the forecast's censoring and the no-attempt rule are as
  before; ordinary turns' guard is unchanged.
- **Who:** a learner given a choice that states the open check's answer: the check is withdrawn, not gradable.
  No stored row is read differently.

### K6-8: Compare's own-passage debit (`0654795ece`)

- **Reproduced.** Fail-first: a reused comparison added no debit (`assert 1 == 2`), and a one-book result none
  (`assert [] == ['compare_sources:post_attempt']`).
- **Before:** the full `source_review` debit ran only on a fresh, model-compared result.
- **Now:** `compare_sources` debits at its single exit from the final passage list (`result.sources`, an
  anchor's blocks included): fresh, reused, `too_few_sources`, skipped or unavailable routes that list the
  passages. Each returning call is one presentation, as Find Sources counts its own.
- **Who:** post-attempt comparisons showing the item's own passage now debit it on every return. No stored row
  is read differently.
- **Not done:** idempotence for a retry of one presentation needs a display id (DJ1); a retry today is a second
  call and debits again (the amount is a full 1.0, so the priming threshold is already crossed).

### K6-9: the cited passage's measured text (`06efb33bbc`)

- **Reproduced.** Fail-first: a citation whose overlap lay past the chip's 600 characters was debited 0.6 (the
  whole passage), not 0 (`assert [0.6] == [0.0]`; written after K6-3, on the fallback branch, which uses the
  same measure as the provider branch).
- **Before:** `_cited_span_overlap` measured each cited passage's whole text as the tutor read it.
- **Now:** `_shown_citation_overlap` measures what the chip shows: its label and, in the Ask panel, its excerpt;
  a bound Reader answer adds its excerpt's verified quote. A zero writes no reveal row, as before.
- **Who:** learners whose citations overlap the key only in an unshown tail: no debit. With the Ask panel off
  (a chip is a label) the cited-passage debit is now usually zero.
- **Opening the source:** the source viewer records a `source_exposure_events` row (`context=tutor_citation`)
  when a chip is opened; no item `reveal_events` debit exists for that action, and none was added.
- **Note:** the panel shows the first citation's excerpt above the answer; every citation's excerpt is
  measured (the server cannot know which the client shows first), which errs towards exposure.

### K6-14: a stored margin link after a role change (`ea21c26aa7`)

- **Reproduced** (filed as suspected). Fail-first: after the block before a placed cue became a "Solution." lead
  (the cue's passage, span, text and target unchanged, its effective role now `solution`, asserted through
  `model_reader_withheld`), both the RPC plan and an uncached `merged_cues` still placed the cue
  (`assert 't3' not in {'t3', 't9'}`).
- **Now:** `discovered_candidates` drops a link whose passage `model_reader_withheld` names a solution, so the
  plan and a tap no longer resolve it.
- **Who:** margin cues on passages reclassified as solutions disappear. No stored link is changed.
- **Deviation:** only the `solution` reason is applied at display, not `assessment_lane`, so no text the owner's
  Reader default allows is newly withheld.

## Shared helpers (rule 2)

`tutor_qa._admitted_linked`, `tutor_qa._shown_citation_overlap`, `reader_dialogue._shown_reserve_fields` and
`_sendable_exchanges`, `phone_reader.destination_material` and `sendable_exchanges` (the latter moved from
`handlers.reader._phone_ask_history`), `library_ask.withheld_now` / `refuse_withheld`,
`handlers.library_ask.deliver_passages`, `compare._debit_shown_own_passages`, `runtime._deliverable`. No final
passage-admission or display-accounting function was built (G6 and DJ1).

## What was run

Every run in a 5G scope at `-n 2` at most, one at a time.

- Each new test, red on the unfixed code and green after its fix (the failing lines above).
- After each fix: the module's own test files (tutor, reader, library ask, teacher, compare, cue, mobile groups).
- `tests/test_identity_pins.py` after each of the nine source commits: 342 passed each time.
- `scripts/affected_tests.py --files <10 changed src files>`: 694 files, so the brief's name filter (reader,
  tutor, library_ask, compare, find_sources, teacher, cue, mobile, reserve, k1, protection, exam_protection):
  184 files, `-m "not arc_close"`: 3252 passed in 9 min 35 s.
- `tests/test_identity_pins.py tests/test_structure_ratchets.py tests/test_k1_source_sets_gate.py`: 372 passed
  (the ratchet first caught a stage-artifact comment of this round in `phone_reader.py`, reworded).
- `tests/test_test_layout.py` alone at `-n 1`: 3 passed; `tests/test_architecture.py` alone at `-n 1`: 18 passed.
- `ruff check`: all checks passed; `lint-imports --no-cache`: 43 kept, 0 broken.

## Not verified

- No frontend run: the wording of the new refusals on the desktop library panel and on the phone was not seen in
  a client. No `apps/` file changed.
- The phone fixes were checked through the host's TestClient, not a device.
- K6-4's reference case is covered by the phone test (a theorem cited by number from another exam unit); the
  retrieved-passage and excerpt cases share the same `withheld` argument but have no test of their own.
- K6-6 and K6-8's "once per presentation of one display id" parts, which need DJ1's display id.
- The full landing and arc-close gates were not run.

## Added at review (orchestrator)

**K6-7, the other side.** Measuring every displayed field would also withdraw a multiple-choice check when a help
reply simply lists that check's own options again, which tells the learner nothing new. The withdrawal now leaves
out the open check's options when the turn lists all of them; a turn that lists only some of them (the solution
among them) narrows the answer and is still measured. Test:
`tests/test_teacher_te1_lesson.py::test_help_that_lists_a_multiple_choice_checks_own_options_again_keeps_the_check`.

**Still open after this round** (recorded in the ledger rows): "once per presentation" for K6-6 and K6-8 needs the
display ids of the Decider's first stage, so a retried comparison debits again; the pinned-tutor job has no
delivery re-check under K6-5; the retrieved-passage and excerpt cases of K6-4 share the tested argument and have
no test of their own.
