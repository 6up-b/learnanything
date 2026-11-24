# Reader workbench v2, RD7a: inline checks and veils (backend)

Stage RD7's backend half (`docs/specs/spec_reader_workbench_v2.md` §12.6, §3.4's `check.*` rows, §14, §15, §15.3, §16's
RD7 row, review F1/F2, decisions D2/D15). Branch `reader/rd7a-inline-checks-backend`, from RD10's tip `c1160f308c`.
This stage changes persisted meaning, so it follows `docs/algorithm-change-playbook.md`; the latest tag is `mvp-0.68`
(`docs/reviews/algorithm-mvp-0.68.md`).

## 1. Design note (before code)

### 1.1 What the existing machinery already decides

Read before designing, so the inline surface adds a place and not a rule (D2, §12.6.6 "Evidence"):

- **A "Check once"** is a pending `test_me_later` commitment (`curriculum.commitments`). Today has no administration
  record for it: Today serves the check's item through the ordinary practice serve, and the serve carries the check's
  view (`intent.checks.served_check`, `practice.py`'s `_with_intent_check`).
- **What answers a check** is computed, never stored: `scheduling.intent.serving.build_checks` takes the **first**
  attempt on one of the check's decided items, at or after the check's date, that is on your own
  (`serving.on_your_own`: not primed, no hints, not a hinted or guided attempt, per
  `causal_activity_policy.attempt_counts_as_assisted`) and cold at the attempt (`serve_eligibility.check_once_at_attempt`,
  the `CHECK_ONCE` decision as it stood when the attempt was submitted). Any earlier attempt that fails either test
  answers nothing and dates the check again (`when = attempt + default delay`, `DATE_FROM_PRACTICE`). So "the first
  settling submission wins" already holds, whichever surface the attempts came from.
- **Settlement** (`intent.checks.settle_answered_checks`) only writes the commitment's `satisfied` disposition event for
  a check `build_checks` already reads as answered; it runs where a Today build prepares, never in replay, and never
  grades.
- **"Cold at the attempt"** is the reveal ledger (`reveal_events`, migration 154, `attempts.reveal_ledger`): the
  `CHECK_ONCE` decision makes the item practice when the item is primed by the ledger with standing exposure (the
  summed non-routine reveals since the item's last attempt at or above `AUTO_PRIME_REVEAL_THRESHOLD`, which never lapse;
  `_decide_check_once`), defers it under the cold holds, and submit auto-primes the same draft (`_decide_submit`).
  Reading a source passage enters this ledger only where a surface debits it: the Reader tutor writes `source_review`
  reveals with the amount `tutor_qa.span_answer_overlap` measures between the shown passage and the item's answer key.
  Ordinary reading (`source_exposure_events`) is telemetry and coldness-receipt evidence for the cold follow-up lanes; it
  never makes a Check once practice.
- **Held candidates** are `CheckState.held` (time-bounded holds, `cold_task_holds`); **exposed** ones `CheckState.exposed`
  (standing exposure, practice only); **refused** ones carry their refusal.
- **The attempt service**: the sidecar's `submit_attempt` (`practice.py`, `submit_attempt_on`), over
  `attempts._resolve_attempt_target` (which asks `serve_eligibility.decide(SUBMIT)`), the grader and the existing
  projection. The assessment contract is frozen by the serve that presents the item.

### 1.2 The administration protocol as a state machine

One new WORKFLOW table holds the open administration and its lock (§1.6). States and transitions:

```
             begin_inline (one transaction)
  (none) ──────────────────────────────────────▶ OPEN ──submit_inline──▶ SUBMITTED   (attempt recorded; settled or practice)
                                                  │  ╲
                         protect_more / expose    │   ╲──abandon_inline──▶ ABANDONED (no attempt)
                         (stay OPEN, append)      │
                                                  └──superseded──▶ SUPERSEDED (its commitment settled elsewhere first,
                                                                   or its item stopped being eligible: closed on read)
```

| Step | What is persisted, in one transaction | A crash right after it leaves | Recovery reads |
|---|---|---|---|
| `begin_inline` | refuse unless the commitment is `one_check_pending`, due, has an eligible candidate (`CheckState.eligible`, held ones skipped) and no administration is OPEN (the lock, §1.5); pick the item exactly as Today's check view does; freeze the contract (the serve's own freezing, its hash stored); insert the administration row (`OPEN`, surface `reader_inline`, token, commitment, item, contract hash, protection status); compute the structural protection set (§1.4) and append the first `check_veil_sets` row. Only then is the prompt in the reply | an OPEN administration with its veil set and no prompt shown | the client's `check.begin_inline` retry with the same `request_id` returns the same administration (idempotent); a fresh start finds the OPEN row (`check.open_inline`, a read) and reopens the card with its veils, or abandons it |
| `protect_more` | the newly visible refs classified; a `check_veil_sets` row appended for the additions | the same OPEN administration, one more veil set | the latest veil sets (their union) are the veils |
| `expose` | the exposure through the canonical machinery **at once** (§1.3 Q1), the administration's exposure state updated, the opened ref appended to the veil sets' `opened` | an OPEN, now assisted administration | the exposure is already in the ledger: whatever happens next, the answer cannot be cold |
| `submit_inline` | the attempt through `submit_attempt_on` for the frozen item and contract (its own transaction, as Today's), then the administration `SUBMITTED` with the attempt id and `submission_id` (unique), then `settle_answered_checks` | an attempt with the administration still OPEN (crash between the two) | `submit_inline` retried with the same `submission_id` finds the attempt by its client submission key and closes the administration with it (idempotent, the first result returned); a fresh start's read finds an OPEN administration whose item has an attempt with that key and closes it the same way |
| `abandon_inline` | the administration `ABANDONED`; a final `check_veil_sets` row with what was opened | a closed administration | nothing to recover; the duty stays pending, the exposure stays in the ledger |
| (read) | an OPEN administration whose commitment is no longer `one_check_pending` (settled by Today first, stopped, replaced) or whose item is no longer a decided candidate is closed `SUPERSEDED` on the next read | — | — |

Today's side of the lock is a read (§1.5): it writes nothing in Today's serve path.

### 1.3 What changes persisted meaning, and the open questions that decide it

The playbook's test: the change alters persisted meaning because it adds a serving surface whose attempts answer
checks, a lock that changes what Today serves while it is held, and exposure written at once by a new writer that the
`CHECK_ONCE` and `SUBMIT` decisions then read. What a replay must reproduce is unchanged in kind: attempts (raw),
reveal events (raw), commitment events (raw ledger, written by settlement outside replay) and the projection derived
from attempts and reveals. The new tables are WORKFLOW (the administration) and RECEIPT (`check_veil_sets`); neither is
read by the projection, the scheduler, readiness or certification, so a whole-vault rebuild equals the live projection
as long as every inline effect on evidence goes through those raw rows. What an inline administration writes that
Today's does not: the administration row, the veil sets, and (Q1, Q2) the reveal rows its exposure creates.

**Three questions the spec leaves open decide what evidence an answer becomes. I stop here for the owner's answers.**

**Q1. What does opening a veil ("show it anyway") write, and so what does the answer become?** The spec says at once
"persisted through the canonical exposure machinery" and "from then on the answer is assisted ... counts as practice".
The canonical machinery that the Check once decision reads is the reveal ledger, and its rule is amount-based.

- (a) **The existing rule, exactly as Check once.** The opened ref's text is debited as a `source_review` reveal on the
  check's item and LO with the amount `span_answer_overlap` measures against the item's answer key (as the Reader tutor
  debits a passage it opens). The answer is practice only when the ledger primes the item; opening a veil whose text
  does not overlap the key leaves the answer cold. No new rule, no new amount; but "counts as practice" is then not
  always true after an opened veil, and the card's line must say "may count as practice" or be computed at submit.
- (b) **The spec's sentence literally.** Any opened veil makes the attempt primed: the administration's exposure is
  sent as the draft's `declared_primed` (an existing input of the `SUBMIT` decision), so submit records the attempt
  primed and the check reads it as practice and dates itself again. The attempt is then assisted everywhere the
  activity policy reads `primed` (projection, facet timeline, certification), not only for the check. No new reveal
  kind, but a new reason to declare priming.
- (c) **Both**: the `source_review` reveal of (a) for the ledger's record, plus (b)'s declared priming for the
  attempt.

**Q2. "Uncertain protection": what does a visible unanchored pad or thread do to the answer?** §12.6.3: with the
Decider unavailable (always, in RD7) and something unanchored visible before the veil applied, the answer is "accepted,
graded and labelled 'answered with your pads open · counts as practice'; the cold duty stays pending". Nothing in the
existing records says anything was revealed, so the existing fold cannot reach this. And "visible before the veil
applied" is every inline check opened with a pad window on screen, i.e. most of them while the Decider waits.

- (a) **As the spec says**, by declaring the draft primed as in Q1 (b): the attempt is assisted everywhere and the
  check dates itself again. A new rule: a cold-eligible item becomes practice because of what was on screen.
- (b) **Check-only**: the attempt stays an ordinary on-your-own attempt for the projection, but it does not answer the
  check. That needs a new input to `build_checks` (the administration's status), i.e. a check-answering rule that reads
  a WORKFLOW table, which replay and the delivery reader (`daily_plan.check_delivery`) would both have to read.
- (c) **Defer the rule until the Decider** (reveal adjudication): whole-window veils are applied, nothing is labelled,
  the answer settles as Check once would. The honesty gap (an unanchored note stating the answer, seen just before
  "check now") stays until the Decider narrows it.
- (d) **Refuse to open** an inline check while an unanchored pad or thread is on screen ("close or move your notes to
  check here", or answer in Today). No evidence rule changes; the cost is friction.

**Q3. "A later [submission] on the other surface is recorded as practice."** Under the existing rule the later
attempt simply answers nothing (the check is already satisfied) and is ordinary evidence like any later attempt.

- (a) **Label only** (existing rule): the card says "already answered in Today · this one is practice"; the attempt's
  evidence is unchanged. My recommendation.
- (b) **Assisted**: declare it primed. A new rule (an on-your-own attempt discounted because another surface settled
  first).

### 1.4 The protection set (non-Decider; the Decider's seam left)

From the request's `visible` (the client sends what is on screen: per window its kind and spans or block ids, pad blocks,
ink owners, thread and history items, the companion, overview previews, search rows), the server classifies:

- **structural**: the LO's covered spans in every source (judged `section_coverage` about the LO and provenance-cited
  spans; the same reads the goal lens uses), pad blocks and ink anchored to those spans or tagged with the LO (the
  pads' anchors, RD4), exchanges citing them (the union read, RD0), the open companion thread, figures for those spans;
- **whole-window**: every pad window and thread window on screen with any block or exchange that has no anchor (the
  spec's unanchored rule);
- the method is recorded as `structural` (nothing unanchored was on screen) or `structural+whole_window`;
- the seam: `protection.narrow(set, judgment)` is the identity until the reveal adjudication judgment exists.

`check_veil_sets` (RECEIPT, append-only): one row per protection computation (begin, each `protect_more`) and one at
close, each with `administration_ref`, `commitment_id`, `method`, `veiled_json` (refs and groups) and `opened_json` (the
veils opened by then).

### 1.5 The lock shared with Today

- **One administration is open at a time** (§12.6.4): a partial unique index over OPEN rows.
- **The Reader side**: `begin_inline` refuses a commitment whose check item is open in Today now: a live practice
  session's presentation of one of its decided candidates served and not yet attempted (the existing presentation and
  session records). Reply `being_answered_in_today`.
- **Today's side**: while an administration is OPEN on a commitment, Today's build shows the check as "being answered
  in the Reader" and does not serve its item as the check (it can still serve the item as practice later; nothing in
  Today's serve path writes). Option, not chosen: Today writes its own administration rows when it serves a check view
  (then the lock is one table, but every Today serve gains a write and a close that a learner who walks away never
  sends, so an expiry would be needed).
- **First settling submission wins** is the existing rule (§1.1); the later one is Q3.

### 1.6 Tag, migration, activation

- **Tag** `mvp-0.69`, `INLINE_CHECK_ALGORITHM_VERSION`, the immediate successor of `mvp-0.68`, appended to
  `SUCCESSOR_CHAIN`, one predicate; no kill switch (owner rule 2026-11-16). Below the tag every `check.*` RPC refuses
  (`below_tag`) and Today's build ignores the lock. The G2 design's proposed tag (`docs/reviews/refactor-g2-design.md`,
  `mvp-0.69`) moves to `mvp-0.70` in its proposal lines only, in the tag's commit.
- **Upgrade row** `Link(mvp-0.69, idempotent_projection)`: only administrations from the upgrade on behave
  differently, and no existing row needs anything (no administration exists before the migration). Test row in
  `EXPECTED_ACTIVATIONS`.
- **Migration 269**: `check_administrations` (WORKFLOW: `administration_token` PK, `request_id` unique,
  `commitment_id`, `surface` (`reader_inline`), `practice_item_id`, `contract_hash`, `state`
  (`open`/`submitted`/`abandoned`/`superseded`), `protection_method`, `exposure_json`, `submission_id` unique,
  `attempt_id`, `opened_at`, `closed_at`; a partial unique index on OPEN; a trigger that a closed row never reopens) and
  `check_veil_sets` (RECEIPT, append-only by trigger). The head fixture upgraded from the tracked 268 copy, on its own.
- **Identity pins**: none expected (no prompt, no keyed hash); the tag string moves the usual tag-string pins in the
  tag's commit only.

### 1.7 Other open questions (none changes evidence; my defaults)

1. **"Abandoned for the day"** (D15): after "not now", the LO's purpose text returns for the rest of the local day
   (D15's wording), and the closed marker stays with "check now" still offered (no rule stops a second try). Display
   only.
2. **Expiry of an OPEN administration** (the app closed for days): none (the spec: "an open administration persists");
   the card reopens or the learner abandons it. A superseded commitment closes it on read.
3. **Item choice when several candidates are eligible**: Today's check view's choice (the first eligible in id order,
   as `served_check` does), so the parity test holds.
4. **`kind: navigated`** in `check.expose`: recorded in the administration's exposure state and the veil set, with no
   reveal (navigating to new content veils it; only opening a veil or taking help is exposure).
5. **`kind: help`** goes through the existing hint path (`hints_used`), which the activity policy already counts.
6. **`check.open_inline`** (a read, for crash recovery): one RPC beyond §3.4's five.

## 2. The owner's answers (2026-11-23), and what changed in the design

- **Q1 = (a), the existing overlap rule.** Opening a veil writes a `source_review` reveal sized by the opened text's
  overlap with the answer key. The answer is practice only if that primes the item. Built on each of the check's
  candidates (each its own key), so an abandoned administration followed by another candidate in Today is decided by
  the same record. Spec §12.6.4's "from then on the answer is assisted" is corrected to say this.
- **Q2, the owner's words: "I would err on veiling notes by default".** Every note-bearing surface on every desk is
  veiled when an inline check opens, not only what structure ties to the answer:
  - all pads (running, named, handwritten, lesson additions) and lessons;
  - threads and the companion's history;
  - margin notes on open sources;
  - every window but a source's text, whole.

  Any veil can be opened, and opening follows Q1. There is no separate "counts as practice" rule for notes that were
  on screen before the veils dropped: §12.6.3's uncertain-protection rule is replaced, and the spec text corrected.
  The seam for the Decider is `inline_administration.narrow`: its judgment may only un-veil what it judges
  irrelevant; it never widens an evidence rule.
- **Q3 = (a), the existing rule.** A later answer on the other surface is labelled practice, answers nothing and stays
  ordinary evidence (`reason: already_answered`). §12.6.5 corrected.
- **The other defaults (§1.7) stand.**
- **The migration is 270** (269 is the pen fix round's guard). It also carries RD10-10's `video_chapters` guard
  trigger (ledger row fixed).
- **The tag is `mvp-0.69`.**

## 3. What was built

- **Migration 270 and its fixture**, each in its own commit. `check_administrations` (WORKFLOW) has a partial unique
  index (one administration open at a time) and triggers (a closed administration is final and kept).
  `check_veil_sets` (RECEIPT) is append-only by triggers, a replacing insert included. `video_chapters_no_replace_decided`
  is added. Roles are set, the architecture test registers the one SQL owner (`db/stores/check_administrations.py`),
  and the earlier migrations' diffs subtract 270's objects.
- **The tag** (`docs/reviews/algorithm-mvp-0.69.md`): one constant, the chain, `INLINE_CHECK_VERSIONS`,
  `inline_checks_on`, `Link(mvp-0.69, idempotent_projection)`, its test row, and the mechanical moves.
- **The protocol** (`learnloop.intent.inline_administration`), with its RPCs in `learnloop_sidecar.handlers.inline_checks`
  (versioned, `extra="forbid"`, desktop-only, pinned):
  - `check.begin_inline {request_id, commitment_id, session_id, visible}`. It picks the check's first servable
    candidate (held candidates are never servable; an exposed-only check is served as practice, as in Today). It serves
    it through Today's own session serve (`get_practice_item`), which freezes the contract and shows the check's view.
    It then computes the protection, writes the administration and the first veil set in one transaction, and only
    then returns the card with the prompt. Retried with the same `request_id`, it returns the same administration.
  - `check.protect_more`: a veil set of the additions only.
  - `check.expose {ref, kind}`: `opened_veil` writes its reveals at once (Q1) and a veil set naming what was opened;
    `navigated` and `help` are recorded only (help is the hint path's). The reply says whether the item is still cold.
  - `check.submit_inline`:
    - it names the submission on the administration first (a crash after the attempt is found by it);
    - it records the attempt through `submit_attempt_on` with surface `reader_inline`, the frozen contract and the
      server's help fold;
    - it closes the administration and settles (`settle_answered_checks`);
    - it returns the attempt's reply with `{cold, reason}`;
    - a duplicate returns the first result, and another submission is refused.
  - `check.abandon_inline`: closed with no attempt, plus a closing veil set; the duty stays pending.
  - `check.open_inline` (the restart read):
    - it returns the open card with its veils and prompt;
    - an administration whose submission reached the attempt service is closed with that attempt and settled;
    - one whose check was settled or stopped elsewhere is closed `superseded`.
- **The lock shared with Today**:
  - `IntentServing.locked` holds the open administrations' commitments (at the tag).
  - `pick_checks` serves none of a locked check's items as the check.
  - `served_check` says "being answered in the Reader" and serves the item as practice.
  - `checks.due_for` rows carry `being_answered`.
  - The Reader side refuses a check whose item has an answer being written in an open Today session.
- **Rust passthroughs and typed client calls** for the six RPCs (`CheckCardDto`, `CheckVisibleDto`, `CheckSubmitDto`).
  No component calls them yet; the card and veils are RD7's frontend half.
- **The spec corrections** (§12.6.3, §12.6.4, §12.6.5) and the G2 design renumbered to `mvp-0.70` in its proposal
  lines.

## 4. Judgment calls

1. **`check.begin_inline` takes the desks' practice `session_id`** (not in §3.4's row). The attempt service records
   every answer on a session, as the pad and workbench submissions do.
2. **The served view is Today's own serve**, called by the handler (`get_practice_item` with the session). The item,
   contract and check view are Today's by construction, which is what the parity test checks. The serve's own writes
   (the content-addressed contract snapshot, the diagnosis serve count) come before the administration's transaction.
   A crash between them leaves a snapshot and no administration, so no prompt was shown.
3. **Which windows are veiled whole.** Every window kind but `source` and `video` is veiled whole, failing closed for
   kinds the client may add later. Within a source window, the check's covered passages and figures on them, plus
   every margin note, are veiled. When coverage cannot be read, every visible source passage is veiled
   (`structural`'s fallback method `whole_sources+notes_by_default`).
4. **An opened veil debits every candidate of the check**, each by its own key's overlap, rather than only the served
   item. An abandoned administration is then honest for whichever candidate Today serves next.
5. **The reply's `reason`** is one of `on_your_own`, `primed`, `with_help`, `seen_before`, `already_answered` or
   `practice`, read from the attempt and the settlement after the fact. It never decides anything.
6. **`check.expose` has no idempotency key** (§3.4's row has none). A retried exposure writes its reveal again, which
   errs towards practice. Recorded as a limitation.
7. **Today-side lock detection** reads open sessions' checkpoints with an answer being typed (§1.5's read, narrowed).
   A Today serve with nothing typed does not hold the check, so a stale checkpoint never blocks the Reader for long.
8. **Coverage reads are injected** by the sidecar (`covered`), because `intent` must not import `source_retrieval`
   (the import contract's acyclic rule).

## 5. Tests

- `tests/test_reader_rd7a_inline_checks.py` (19):
  - the RPCs desktop-only and strict;
  - below the tag;
  - the prompt only after the veils;
  - the protection set;
  - `protect_more`;
  - the lock with Today;
  - the Today-side refusal;
  - Q1 both ways;
  - an idempotent submit;
  - Q3;
  - parity with Check once;
  - abandon;
  - the restart read;
  - a crash after the attempt;
  - a crash before it;
  - supersession;
  - the live projection equal to a whole-vault rebuild.
- `tests/test_reader_rd7a_migration.py` (7).
- **Fail-first.** Before the behaviour commit the protocol file did not collect (the module was absent). With the
  behaviour in place, each rule's line removed made its test fail, then restored:
  - the lock in `intent_serving`;
  - the reveal in `expose`;
  - the settlement in `finish_submit`;
  - the submission branch of `reopen`;
  - supersession in `reopen`;
  - the Today-side refusal.
- **Assertions changed:**
  - `test_reader_rd0_reads.py`: a due row's `being_answered: False`.
  - `test_reader_rd0_rpcs.py`: RD0's inline check RPC is `checks.due_for`, the first of `INLINE_CHECK_RPCS`.
  - `test_mobile_allowlist.py`: RD0's pin minus RD7's six, which are pinned on their own.
  - The tag's mechanical moves (`algorithm-mvp-0.69.md`).

## 6. RD9a-3: what would let a lesson's quick question back into a desk window

RD9a-3's interim stays until RD7's frontend half exists: a lesson's quick question is asked on the full lesson screen
and never in a desk window. Under this guard, a probe could return to a window when all of these hold:

- **The frontend half renders the veils.** Every note-bearing surface on every desk is veiled with nothing moved,
  `check.protect_more` runs before new content renders, and "show it anyway" calls `check.expose`.
- **The probe holds the same lock and veils.** A lesson probe is not a commitment. It needs its own administration on
  the same lock, opened when the probe is served:
  - a surface value beside `reader_inline` (a schema change, since 270's CHECK names one surface);
  - or a probe-keyed administration in a later migration.
- **The lesson's own teaching above the probe is veiled too**, as a note-bearing surface, with its exposure written by
  the same overlap rule. The probe's cold/assisted decision then reads the reveal ledger, as the Check once decision
  does.
- **The probe's existing first-serve claim** (`PR.serve`) is made only when the veils are recorded, not when a window
  reads the lesson. RD9a-3's `frame: "window"` hold already keeps a window's read from serving it.

## 7. Not verified

- No owner copy was opened. The procedure and the read-only script are in `algorithm-mvp-0.69.md`, for the
  orchestrator.
- There is no frontend card or veils yet (RD7's frontend half), so nothing rendered was checked: no visual comparison
  or harness run beyond the existing suite.
- The module catalog notes for the two new modules (`intent/inline_administration.py`,
  `db/stores/check_administrations.py`) are not generated here (references are regenerated at integration).
