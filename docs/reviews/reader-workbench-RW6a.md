# Reader workbench RW6a: "Last time here" (stage `reader-rw6a`)

Branch `reader/rw6a` (worktree `learnanything-merge4`), base `main` at
`e182f3ec8` (RW2a landed: migration 207, `workbench.enabled`). Spec:
`docs/specs/spec_reader_workbench_v1.md` §13 row RW6a and what it cites
(§9.1 in full: the card, the reader session, the typed per-session summary,
`ReaderObservationV1`, Wrap up; §9.4: no table; §9.6: `recap.enabled`,
`recap.wrap_up_enabled`), §3.4, §12, §14 (G25 summary part, G31, G50), §16
(D16, D34, D36), §20 (§20.9: S10, S11 adopted). Presentation:
`docs/specs/ux_reader_workbench_v1.md` §1, §2 moments 0, 10 and 11, §3.4,
§4.0, §4.8, §4.12, W1, W12, §10 S10/S11. RW2a's friction notes (§5 item 1:
`workbench.for_source` is the read for "Unfinished").

## 0. Plan (written before the code)

**Scope.** RW6a only. Deterministic, no model call, no route, no spend, no
migration, no new table, no new interaction-event kind, no new reveal kind,
no successor. Grading, regrade, replay, eligibility and the workbench's
recording rules are untouched.

**The reader session** (`learnloop/reader/reader_sessions.py`, pure core plus
one read). A visit is the reader envelope's `reader_view_opened` /
`reader_view_closed` pair for one `visit_id` (RW1a's funnel; its end is the
close, else the visit's last event, else its open). A **session** is one visit
on a source, or several visits on the same source less than 30 minutes apart
(gap = next open − previous end; `SESSION_GAP`, a definition, not a config
key). The card's session is the one before the current one: a visit opened
less than 30 minutes after the last one joins that session, so its card is
about the session before.

**The typed per-session summary** (`learnloop/reader/recap.py`,
`ReaderSessionSummaryV1`, §9.1's list): sections read (`reader_section_progress`
stamps in the window); inquiries opened, resolved and still open with their
roots (`reader_answer_submitted` + `question_events.resolution` +
`inquiry_status_set`); workbench sessions (item, highest help level — none
before RW2b's ladder, so `null` with the book and hints RW2a records —,
submitted or abandoned, grade from the attempt); cues opened or marked not
relevant (RW3a's tap events); predictions missed (RW5a absent: `[]`); gaps
named by learner-text gaps from the session's questions (`learner_text_gaps`,
`source_kind = 'tutor_question'`); facets touched; **claims needing an
independent check** (facets of the session's assisted workbench attempts — a
counted book or hints — with no certification-eligible full success on the
facet since the session began); and the session's **`ReaderObservationV1`**
records (`learnloop/reader/reader_observations.py`), `authority:
"routing_only"`. Today's only tier-2 source is RW1a's reconnect *still
unclear*; the builders for RW1b's next-step / why-step / assumption misses and
RW5a's missed predictions exist and read nothing until those phases add rows.
Deterministic from the ledgers: built twice with the same `now`, the JSON is
identical (G25).

**The card** (`reader.recap`, a pure read): continue at (the last section of
that session; the Reader's restored place does the scrolling); **Still open**
(open roots on the source, *open* and the RW1a status chips); **Unfinished**
(`workbench.sessions_for_source`'s open problems: steps, help so far,
*Resume this problem*); **Worth a second look** (the still-unclear records
whose root is still open; RW1b/RW5a rows render when they exist); **Since last
time** (LOs this source teaches, `lo_certification(...).demonstrated` now,
dated by the certifying attempt — the point at which the last of the LO's
facets crossed the demonstrated threshold on the Demonstrated curve — after
the previous session ended; checks retired since as no longer needed: the
read is ready, RW6b writes them). Headings carry no counts, nothing is
"overdue", the well's markers only.

**Recap events** (G31): `reader.recap_event` writes one salience-only
`reader_action_invoked` with payload `event` `recap_shown` (once per visit when
the card renders), `recap_dismissed` (hides the card for this source until the
next session) or `wrap_up_opened`. Opening a source writes nothing else: the
recap read writes nothing, with the recap on or off.

**Wrap up** (`reader.wrap_up`, a pure read): the session's three lists —
resolved (undo), still open (resolve · keep open, and revisit once in the
Reader), worth reinforcing (`◌` work with help, claims needing an independent
check, misses when their phases land). Activity (D34): an inquiry exchange, a
workbench session, a formative answer or a kept comparison in the session;
scrolling, highlights and cue taps don't count. **The offer at the
destination** (`reader.wrap_up_offer`, a pure read): the most recent reader
session had activity and no `wrap_up_opened` followed its start. The desktop
shows the dim line on the first Today or library view after leaving the
Reader, never in the Reader being closed, never blocking. Actions call the
same RPCs the chips call (`reader.set_inquiry_status`, the `test_me_later`
preset); Wrap up writes nothing of its own.

**Config** `[recap] enabled = true, wrap_up_enabled = true` (modelled defaults,
left out of the decision-only template); every
`DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry recomputed with the "no scoring,
scheduling, projection or serving change" note. The config DTO carries
`recap` only while one of them is on. Off: the four RPCs refuse
(`recap_disabled`, `wrap_up_disabled`) before reading or writing, and the
Reader and Today render byte-identically.

**G50.** An import-linter contract `evidence-never-reads-reader-observations`
keeps substrate, learner, attempts, scheduling, goals, diagnosis, placement,
field and router from importing `reader_observations`, `reader_sessions` or
`recap`.

**Frontend** (new files under `screens/reader/`): `useReaderRecap.ts` (load,
`recap_shown`, collapse on first scroll or *continue*, *last time ▸*,
*dismiss*, the footer's *Wrap up (under a minute)* after activity, `w`),
`RecapCard.tsx`, `WrapUpPanel.tsx`, `WrapUpOffer.tsx` (the destination
line, rendered by the App above Today's queue and the library on the first
view after leaving the Reader). Four Tauri passthroughs. Desktop only (D20),
pinned off the phone.

**Today's re-entry panel** (DL1): not built in RW6a — the panel is goal-scoped
and shown only with the plan off; carrying the card there needs a new "most
recent source" read on Today. Recorded as an open question.

**Tests (fail-first):** `tests/test_reader_recap.py` (G25 summary part, G31,
the session boundary, the card's sections and their sources, Since last time
dating, dismiss, the kill switch), `tests/test_reader_observation_records.py`
(G50), `tests/test_reader_wrap_up.py` (activity rule, the destination offer,
pure reads, the switch); vitest `RecapCard.test.tsx`, `WrapUp.test.tsx`,
`recapSwitchOff.test.tsx` (snapshots written on the base frontend).

## 1. What was built

| Part | What | Commits |
|---|---|---|
| Fail-first backend | `tests/test_reader_recap.py` (16), `tests/test_reader_observation_records.py` (6), `tests/test_reader_wrap_up.py` (12), `tests/recap_fixtures.py`, the four RPCs pinned off the phone; the switched-off Reader snapshots written on the base frontend | `90560a639` |
| Backend | `reader_sessions.py`, `reader_observations.py`, `recap.py`, `reader_progression.learning_objects_by_section`, `handlers/recap.py`, `[recap]`, the config DTO, every defaults snapshot, the import-linter contract | `90c261ba8` |
| Fail-first frontend | `RecapCard.test.tsx` (8), `WrapUp.test.tsx` (7, then 8), `ReaderScreen.recap.test.tsx` (4) | `f5f10cce2` |
| Frontend | `useReaderRecap.ts`, `RecapCard.tsx`, `WrapUpPanel.tsx`, `WrapUpOffer.tsx`, `recapCopy.ts`, `app/wrapUpOffer.ts`, the GuideRail header slot, the App's destination line, four Tauri passthroughs | `3182337e2`, `4d3837942` |
| References | the `[recap]` section (865 leaves in 55 sections), regenerated at head 207, the Pipeline Map bullet | `8c9ce7ce2` |
| Record | this file | (last commit) |

**Paid calls:** none ($0.00). RW6a has no route, no model call and no spend; every test uses the stub reader client and fakes.

### 1.1 The reader session (`learnloop/reader/reader_sessions.py`)

- A **visit** is RW1a's envelope: `reader_view_opened` (which names the source) and `reader_view_closed` for one `visit_id`; a visit with no close ends at the last event carrying its `visit_id` (a selection, an action, a recap event), else at its open.
- A **session** groups one source's visits whose gap (next open − previous end) is under 30 minutes (`SESSION_GAP`, a definition rather than a setting, so no config key and no parameter-registry entry). Sessions are per source. `split_sessions` gives the card's *previous* session and the *current* one: the current visit's session, or — when its open has not reached the envelope yet — the last session if it ended under 30 minutes ago, else a new one starting now. A source reopened 20 minutes after closing is the same session, so its card is about the session before.
- Pure over event rows; one read (`envelope_events`). Visits are recorded only while `reader_inquiry.enabled` is on (RW1a's funnel switch, `activity.ts`); with it off there are no sessions, so no card and no offer (recorded as a deviation, §3 item 1).

### 1.2 The typed session summary (`recap.session_summary`, `ReaderSessionSummaryV1`)

§9.1's list, ids and verdicts only (no learner text; G25's test checks the learner's words are absent):
- `sections_read`: `reader_section_progress` rows with a reveal, completion or update stamp in the window;
- `inquiries`: `opened` (roots created in the window), `resolved` (an `inquiry_status_set` to resolved in the window, still resolved), `still_open` (inquiries the session touched — a root or a branch — that are open now), each with its root, question id, anchor spans; `inquiry_exchanges` lists every exchange (activity);
- `workbench`: problems the session worked on (a step written, a lifecycle event or opened in the window): item, status (open, submitted, abandoned), `highest_help_level: null` (the ladder's levels arrive with RW2b), `book_counted` and `hints` as RW2a records them, the attempt and its grade (`rubric_score`, `correctness`);
- `cues`: RW3a's opened / check-me taps and not-relevant marks (undo honoured);
- `predictions_missed`: RW5a's records (none on `main`);
- `gaps_named`: learner-text gaps named from the session's questions (`source_kind = 'tutor_question'`, kinds other than none / unread);
- `learning_objects_touched`, `facets_touched`: the problems' item facets and the LOs (and their facets) of the inquiries' anchors;
- **`claims_needing_independent_check`**: facets of the session's submitted attempts that were assisted (the book counted, or hints), with no unassisted success on the facet from the session's start — an unassisted success read as the evidence system defines it, a point on the facet's Demonstrated curve that earned credit without help or priming (`facet_evidence_timelines`), so this read never re-implements the activity policy;
- `observations`: the session's `ReaderObservationV1` records;
- `activity` / `activity_sources` (D34).

Computed twice (the second time from a freshly loaded vault and repository), the JSON is identical (G25's summary part).

### 1.3 `ReaderObservationV1` (`learnloop/reader/reader_observations.py`)

A frozen dataclass with §9.1's fields (`kind`, `source_event_ids`, `span_ids`, `item_id`, `step_id`, `facet_candidates`, `observed`, `hypotheses`, `assistance`, `authority`), plus `root_exchange_id` (the card's *open*), `observed_at` and `record_version`; it refuses an unknown kind or any authority but `routing_only`. Builders:
- **still unclear** (RW1a, the only tier-2 source on `main`): one record per `reconnect_answered` with `answer = still_unclear` in the session; spans from the root's anchor; facet candidates are the LOs of those spans; `observed = {answer, via}`; hypotheses are the gaps learner-text gaps named from the follow-up the learner asked from that root afterwards;
- **next step / why step / assumptions** (RW1b, ready): selection-scoped `reader_authored_questions` in those styles with a `partly` / `no` self-check (migration 185 already has the columns); reads nothing until RW1b writes rows;
- **predictions** (RW5a, ready): `figure_predictions` with `matched = 0` when that table and column exist; nothing until RW5a.

### 1.4 The card (`reader.recap`)

`{recap, dismissed}`; `recap` is null on a first visit, within the first session and after a dismiss in the current session. Its parts: `session` (header *LAST TIME HERE · Thu 9 Oct · about 40 min*), `continue_at` (the session's last section; the Reader's restored place does the scroll), `still_open` (every open root on the source, its words cut to 140 characters), `unfinished` (`workbench.sessions_for_source`'s open problems with `step_count`, `help` and *help so far: the book* / *none* / *2 hints on the answer box*), `worth_a_second_look` (last session's formative records, plus every earlier *still unclear* whose inquiry is still open, one per inquiry; those roots leave Still open so a thread shows once), `since_last_time` (`demonstrated`: this source's LOs — provenance-linked to any section — with `lo_certification(...).demonstrated` now and a facet that crossed the demonstrated threshold, from below it at the session's end, after the session ended; dated by that point's attempt, the last such crossing; `checks_retired`: `retired` commitment events with `reason = no_longer_needed` naming this source, which RW6b's re-valuation will write).

### 1.5 Wrap up (`reader.wrap_up`, `reader.wrap_up_offer`)

- Three lists from the summary: **resolved** (*undo*: `reader.set_inquiry_status` → open, trigger undo), **still open** (*resolve*: the same RPC → resolved; *revisit once*: `reader.invoke_preset` with `test_me_later`, marked `where = reader` because the preset needs the open reading; *keep open*: no RPC, nothing written), **worth reinforcing** (`◌` problems worked with help, claims needing an independent check, RW1b/RW5a misses when they exist).
- In the Reader the session is the current one (it runs to now); at the destination, the source's latest.
- **The offer at the destination** is a pure read: the most recent reader session (across sources) had activity and no `wrap_up_opened` for that source at or after its start.

### 1.6 The events (G31) and the switches

- `reader.recap_event` writes one `reader_action_invoked` (subject `reader_extraction`, payload `event`, `extraction_id`, `visit_id`, `authority_class = salience_only`): `recap_shown`, `recap_dismissed` (gated by `recap.enabled`) or `wrap_up_opened` (gated by `recap.wrap_up_enabled`). No new interaction kind (§3.4 item 4).
- `reader.recap` refuses `recap_disabled`; `reader.wrap_up` and `reader.wrap_up_offer` refuse `wrap_up_disabled`; each before any read or write. The switches are independent: the card off leaves Wrap up on its own switch and vice versa. The config DTO carries `recap: {enabled, wrapUpEnabled}` only while one is on.

### 1.7 Frontend

- **`useReaderRecap`** (kept out of `ReaderScreen.tsx`, which gains about 90 lines of wiring): reads the card per opened source; records `recap_shown` once per visit, only while the card is unfolded on the Guide tab with the rail showing; the learner's first scroll (`readingMoved`, which jumps and the restoration don't set) or *continue* folds it to *last time ▸* · *continue at …*, and later scrolling leaves it as the learner set it; *dismiss* records `recap_dismissed` and removes card and link. Wrap up's availability is re-read when an Ask lands or a problem changes (`activityKey`); `w` outside text fields, without modifiers, outside the working posture, opens it.
- **`RecapCard`** (W12 without RW6b's *Coming up* and narrative): headings *Still open*, *Unfinished*, *Worth a second look*, *Since last time* with no counts; an empty section is left out; Still open lines carry *open* (the Ask tab and a peek at the passage, with its crumb back) · *resolved* · *revisit once* · *keep open* (writes nothing); Unfinished lines *✎ Exercise 5.14 · 4 steps · help so far: the book · Resume this problem ▸*; *◌ your question "…" — still unclear when you came back to it · open ▸*; *● conditional probability — demonstrated on your own (Mon)*.
- **`WrapUpPanel`**: the three lists, each line its actions (at the destination only the ones that run there), *kept open* after keep open, *close · esc*, `Esc` closes; a claim already shown as a problem worked with help is not repeated.
- **`WrapUpOffer`** + **`app/wrapUpOffer.ts`**: the App arms the line on the transition from the Reader to Today or the library and disarms it on the next tab change; it renders above Today's queue and the library (always the same element shape, so its arrival never remounts Today), asks `reader.wrap_up_offer`, shows *Reading wrap-up ready — under a minute ▸* (dim, no focus, no modal); pressed, Wrap up opens in place, `wrap_up_opened` is written, and *resolve* / *undo* call `reader.set_inquiry_status`.
- **Switched off** (`recap` absent or both false): no call, no element; the Reader matches the base snapshots byte for byte (`recapSwitchOff.test.tsx`, and RW2a's `switchOff.test.tsx` still passes); Today and the library render `<>{null}{…}</>`.

## 2. Gates and where they are tested

| Gate | Backend | Frontend |
|---|---|---|
| **G25** (the summary part) | `test_the_typed_summary_is_deterministic_from_the_ledgers` (twice, fresh objects, identical JSON; §9.1's keys; no learner text); `test_the_summary_keeps_to_its_session`; `test_claims_needing_an_independent_check_are_assisted_only_facets` | — |
| **G31** | `test_opening_a_source_writes_nothing_but_the_recap_shown_event` (every table compared; one salience-only row); `test_switched_off_opening_writes_nothing_and_the_recap_rpcs_refuse`; `test_unknown_recap_events_are_refused_before_any_write` | `ReaderScreen.recap.test.tsx`: recap_shown once on opening, nothing focused; first visit: no event |
| **G50** | `test_reader_observation_records.py`: one routing-only record per still unclear, deterministic, kinds, RW1b/RW5a reads empty, building writes nothing, the import-linter contract and a scan of every evidence package; `test_wrap_up_is_a_pure_read_and_its_actions_are_the_chips_rpcs`; `test_opening_wrap_up_writes_only_the_wrap_up_opened_event` | `WrapUp.test.tsx`: keep open writes nothing; the destination writes only wrap_up_opened and the status RPC |
| Session boundary (30 min) | `test_visits_less_than_30_minutes_apart_are_one_session` (29.9 vs 30.0 min), `test_sessions_are_per_source_and_a_visit_without_a_close_ends_at_its_last_event`, `test_the_card_is_about_the_session_before_the_current_one`, `test_sessions_are_read_from_the_reader_envelope`, `test_no_card_on_a_first_visit_or_within_the_same_session` | — |
| Card sections and sources | `test_the_card_reads_still_open_unfinished_and_worth_a_second_look` | `RecapCard.test.tsx` (sections, no counts, empty sections left out, the chips) |
| Since last time dating | `test_since_last_time_dates_the_certifying_attempt_after_the_previous_session` (crossing after, already demonstrated, the last facet's crossing, undemonstrated, assisted); `test_since_last_time_reads_the_real_ledger_without_inventing_a_gain` | `RecapCard.test.tsx` (*● … (Mon)*) |
| Wrap up's activity rule | `test_scrolling_highlights_and_cue_taps_alone_are_not_activity`; `test_an_inquiry_or_a_workbench_session_is_activity` (root, branch, problem); `test_the_footer_offer_follows_the_current_session_only` | `WrapUp.test.tsx`: the rail offer only after activity, `w`, `w` in a text field, `w` while working; `ReaderScreen.recap.test.tsx`: the footer and the panel in the rail |
| Landing-place offer | `test_the_offer_appears_where_the_learner_lands_until_wrap_up_is_opened`; `test_the_offer_reads_the_most_recent_session_only` | `WrapUp.test.tsx`: armed only Reader → Today / library; one dim line, no focus, no dialog, opened in place, Esc |
| Collapse / reopen / dismiss | `test_dismiss_hides_the_card_until_the_next_session` | `RecapCard.test.tsx` (hook: first scroll and continue fold, only the first scroll, reopen, dismiss); `ReaderScreen.recap.test.tsx` |
| Switch-off byte identity | `test_switched_off_…`, `test_wrap_up_switched_off_refuses_and_writes_nothing`, `test_the_card_off_leaves_wrap_up_on_its_own_switch`, `test_the_kill_switches_default_on_and_the_config_dto_names_them`; `test_config_refactor.py` (nineteen snapshots) | `recapSwitchOff.test.tsx` (2 configs × 3 snapshots, written on the base; no recap call); `WrapUp.test.tsx` (off: no line, no call) |
| Attention budget (G54's part) | — | `attentionBudget.test.tsx`'s lint already covers `screens/reader/*.tsx` (no animation or transition in the new components) |

**Fail-first evidence.** Backend (`90560a639`): the three files failed at collection on the base (no `learnloop.reader.reader_sessions`) and 4 mobile pins failed (unregistered RPCs). Frontend (`f5f10cce2`): `RecapCard.test.tsx` and `WrapUp.test.tsx` failed at import, all 4 of `ReaderScreen.recap.test.tsx` failed; the switched-off snapshots were written on the base and pass unchanged after. Tightened after the implementation, each recorded: the problem fixture opens on the basic vault's item (a selection with no import is refused by RW2a's rules, which this stage keeps); the claims test fakes the Demonstrated curve (the implementation reads the evidence system's own unassisted success rather than re-deriving the activity policy, which the frozen-cycle contract forbids the reader package to import); the inquiry exchanges moved out of `inquiries` to their own key; *keep open* carries no RPC, so the action set filters it; the panel's *revisit once* is checked before *keep open* folds the line's chips.

## 3. Decisions taken within the spec, and deviations

1. **Sessions need RW1a's envelope.** Visits are written only while `reader_inquiry.enabled` is on (RW1a's funnel switch in `activity.ts`), so with it off there are no reader sessions: no card, no Wrap up, no offer. The spec defines the session on that envelope; RW6a adds no second visit writer. Visits recorded before RW1a landed don't exist, so the first card appears after the first recorded session.
2. **Sessions are per source.** §9.1 says "one visit, or several visits less than 30 minutes apart"; the card is about *this* source's last time and the destination offer about the source just left, so visits on two books 10 minutes apart are two sessions, one per book.
3. **The card's session is the one before the current one**, and a reopen within 30 minutes joins the current session, so its card is about the session before that (or none). Dismiss lasts for the current session, so a reopen within 30 minutes stays dismissed.
4. **Still open lists every open inquiry on the source**, not only last session's (a thread doesn't stop being open); an inquiry whose last "still unclear" is listed under Worth a second look is shown there only, once.
5. **"Became demonstrated since" is read from the Demonstrated curve.** `lo_certification(...).demonstrated` now, and one of the LO's facets crossed the certification threshold (`DEMONSTRATED_CREDIT`) after the previous session ended, having been below it at that end; the date and attempt are the last such crossing's. The certificate itself is per (facet, capability) and per recipe; the curve sums a facet's capabilities, so an LO already demonstrated whose other facet crosses later can read as "since" (honest about the attempt, generous about "became"). No certification code changed.
6. **Claims needing an independent check**: RW2a's assistance only (the book counted, carried hints); RW2b adds help level 3+ through `help_assists`. "Since" starts at the session's start, so an own success in the session answers it.
7. **"Checks retired since"** reads a `retired` commitment event with `detail.reason = "no_longer_needed"` and `detail.extraction_id`; nothing on `main` writes that shape yet. RW6b should write it (friction note 3) or change this read.
8. **Wrap up's "revisit once"** runs in the Reader only (the `test_me_later` preset needs the open reading's render view and spans); at the destination still-open lines offer *resolve* and *keep open*, resolved lines *undo*, and worth-reinforcing lines are information without an action there.
9. **Worth reinforcing** has no per-line action in RW6a: its lines are problems worked with help (resume lives in the card) and claims (RW6b schedules their checks and gives them *undo*).
10. **No "on the map ▸"** link on Since last time lines yet (the Reader has no handle to open the map at an LO); the marker and wording are the well's.
11. **Today's re-entry panel (DL1)** does not show the card: the panel is goal-scoped and shown only with the plan off, and the card is per source, so it needs a "most recent source" read on Today — new wiring, outside "if it fits". The destination line is on Today (and the library) as specified.
12. **The `observed` field of a still-unclear record** is `{answer, via}`, and records carry `root_exchange_id`, `observed_at` and `record_version` beside §9.1's fields (routing data for the card; typed, no prose).
13. **The `figure_predictions` read** assumes RW5a's table has `extraction_id`, `matched` and `created_at`; it checks the columns and reads nothing otherwise. RW5a should match or adjust it (friction note 4).

## 4. Friction audit (G52) for the workflows RW6a touched

| Workflow | Before RW6a | After |
|---|---|---|
| Come back to a book | The restored place; open questions only in the Ask rail or Today's queue; problems as rail lines | One card at the head of the Guide: continue, the open questions in your words with their chips, the problems with *Resume*, what is worth a second look, what you have since shown on your own; folds on the first scroll |
| End a reading session | Nothing | `w` or the rail footer; or, after leaving, one dim line where you land; under a minute, Esc closes |
| Check whether reading led anywhere | The map | *Since last time · ● … demonstrated on your own (Mon)* on the book itself |

Keyboard: `w` (outside text fields), Esc closes Wrap up; every line's action is a button in reading order; nothing takes focus.

## 5. Friction notes for RW1b, RW2b and RW6b

1. **RW1b**: next-step, why-step and assumption answers are read from `reader_authored_questions` with `scope_kind = 'selection'`, `question_style IN ('next_step', 'why_step', 'assumptions')` and `answered_at`; a `partly` / `no` `self_check` becomes a `ReaderObservationV1` (`next_step_missed`, `why_step_missed`, `assumption_missed`) and any answered one counts as activity for Wrap up. Write those columns and the card and Wrap up pick them up with no RW6a change. The `reader_formative` texts' gap ids would fill `hypotheses` via `reader_observations.named_gaps` once their `source_kind` exists (today it reads `tutor_question` only).
2. **RW2b**: `session_summary`'s `workbench[].highest_help_level` is `null` and claims read only the book and carried hints. Fill `highest_help_level` from `help_assists` (max level with `surface = 'workbench'`), add level ≥ 3 to `_claims`, and add builders for `check_questionable`, `hint_taken`, `doesnt_connect` and `discriminate_answer` in `reader_observations.py` (the kinds are declared). The Unfinished line's `help_line` should name the ladder's rungs (*help: check, L1 question, L3 hint*, W12).
3. **RW6b**: the typed summary (`recap.session_summary`) and `ReaderObservationV1` are the inputs §9.2-9.3 name; `reader_session_digests.summary_json` can store `session_summary(...)` as is (it is deterministic and carries no learner text). "Coming up" and the narrative go in `RecapCard` after Since last time (the card has no slot yet); Wrap up's worth-reinforcing gains the checks with *why* and *undo*. Re-valuation retirements should write `commitment_events(kind = 'retired', detail = {reason: 'no_longer_needed', extraction_id, solved_attempt_id})`, which `recap.retired_checks` already reads for *No longer needed: you solved one like it on …*.
4. **RW5a**: `reader_observations.prediction_observations` reads `figure_predictions(extraction_id, matched, created_at)`; name the columns so or change the read.
5. **Performance** (backup-API copy of the tracked `fixtures/probability`, upgraded with `doctor --fix-state`, two synthetic sessions written on the copy): `reader.recap` 0.04-0.05 s, `reader.wrap_up` 0.04 s, `reader.wrap_up_offer` 0.03 s; Since last time over a 17-LO source 0.09 s. The card's cost grows with the source's LOs (one `lo_certification` each) and the attempt ledger (one Demonstrated-curve read for the demonstrated LOs' facets).
6. `ReaderScreen.tsx` grew by 94 lines (now 2,858); the card, panel and offer live in `screens/reader/`.

## 6. Open questions (with the default taken)

1. Show the card in Today's re-entry panel (DL1) for the most recent source? **Default: not in RW6a** (needs a Today read of the most recent source; the destination line is there).
2. Count visits on two books less than 30 minutes apart as one reader session? **Default: no, sessions are per source** (§3 item 2).
3. Record visits (and so sessions) when `reader_inquiry.enabled` is off? **Default: no** — the envelope is RW1a's; off means no card.
4. "On the map ▸" on Since last time lines? **Default: later**, when the Reader can open the map at an LO.
5. Should *keep open* write anything (for example a status event with `trigger = "keep"`)? **Default: no**; it is the status the inquiry already has.
6. Should the inquiry quick check's own `partly` / `no` self-check (RW1a's reconnect *quick check*) count as worth a second look? It has no `ReaderObservationV1` kind in §9.1. **Default: no**, until the spec names one.

## 7. Owner-run commands

None needed (no model call, no migration). To look at it on a copy: make a backup-API copy into `fixtures-local/` (`learnloop.db.copies.copy_tree_with_databases`), `uv run learnloop doctor --fix-state --vault <copy>`, then `LEARNLOOP_VAULT=<abs path to the copy> npm run dev` from `apps/learnloop-tauri`; read a book, close it, wait 30 minutes or more, open it again for the card; ask a question and go back to Today for the wrap-up line. `[recap] enabled = false` / `wrap_up_enabled = false` in the copy's `learnloop.toml` switch each off.

## 8. Gate

Run in the worktree with `TMPDIR` set to `fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **24 kept**, 0 broken (23 on the base plus `evidence-never-reads-reader-observations`) |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | **12,917 passed**, 2 xfailed, 0 failed (1,096 s), on `8c9ce7ce2` (the backend tip; later commits touch only `apps/` and this file). Base was 12,879: +34 RW6a tests, +4 mobile pins |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | **106 passed**, 12,813 deselected (115 s) |
| `npm install`, `npm run typecheck` | ok, clean |
| `npm test` (vitest) | **112 files, 923 tests passed** (base 901; +22: recapSwitchOff 2, RecapCard 8, WrapUp 8, ReaderScreen.recap 4) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | finished, exit 0 (four passthroughs) |
| `db_generate_reference.py`, `db_validate_reference.py`, `validate_vault.py`, `module_validate.py` | regenerated (head 207, 327 table notes, 865 configuration leaves in 55 sections); errors []; passed, 1,116 notes; passed |
| `tests/test_config_refactor.py` (nineteen snapshots recomputed, config `.pyc` cleared), `test_cli_help_snapshot.py`, `test_sidecar_serializer_snapshot.py`, `test_desktop_rpc_contract.py`, `test_architecture.py`, `test_coordinated_migrations.py` | pass (in the full suite); CLI help unchanged, no migration |

**Pre-existing, not RW6a:** `desktop_validate.py` stops on `apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts` ("unclassified desktop source"), a file on the base from the Reader PDF selection stage; RW6a's files were not reached. **Not done:** no adversarial (Codex) review in this stage, no real-UI look (the screens are exercised through the real `ReaderScreen` in jsdom). Manual run: two backup-API copies in `fixtures-local/` (`rw6a-probability`, upgraded with `doctor --fix-state`, synthetic visits written on the copy only; `rw6a-linear_algebra`, copied, unused); no tracked vault was opened or changed.

## Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/rw6a-onto-main`. The stage's base and main's tip are both `e182f3ec8` (RW2a, mvp-0.27, schema head 207). The stage's tip is `2444257c5` (16 commits, after the Codex review's three rounds; the round 3 verify, job `20261017-130629-eROC0Q`, is clean), unchanged. Main was neither fast-forwarded nor pushed here.

**Commits:**
- `a44fe3b88`: a real `--no-ff` merge of `reader/rw6a` onto `e182f3ec8`. The merged tree is byte-identical to the stage tip's (`git diff 2444257c5 a44fe3b88` is empty).
- `e4155b989`: the references regenerated on the merged tree.
- This record.

### Merge

- **No conflicts.** Main had not moved since the stage's base. No migration, no table, so `fixtures/migration_head_207` is untouched (rollback-mode: header bytes 18-19 are 1/1, no `-wal` or `-shm`).
- **No algorithm successor:** the vaults' labels and the Pipeline Map's `implementation_version` stay as they were. One config section (`[recap] enabled`, `wrap_up_enabled`), four `reader.*` RPCs (desktop only, pinned off the phone), four Tauri passthroughs, one import-linter contract.

### Regenerated

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, `schema_head` 207, 327 table notes. 384 notes changed: the `source_commit` labels, and the configuration leaves' line citations that moved in `src/learnloop_sidecar/context.py` (the review's F10 config DTO) and `src/learnloop/learner/facet_evidence_timeline.py` (the review's timeline fields). Committed as `e4155b989`.
- **Defaults snapshots.** The template `.pyc` was deleted and `template.py` touched. All 19 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries equal `defaults_fingerprint_for_version`: **0 mismatches**.
- **CLI help snapshot.** Rewritten with `python tests/test_cli_help_snapshot.py --write`: no change.
- **The Pipeline Map.** The stage's RW6a bullet is already there; nothing to add. `validate_vault.py` passes (1,116 notes, 1,114/1,114 reachable); `module_validate.py` passes.

### Gate

Run on `e4155b989`, the final code tree; the only later commit adds this section. Python 3.12.14, `TMPDIR` set to merge2's `fixtures-local/tmp`, `uv run --no-sync` after the install; both suite lanes under `flock /tmp/learnloop-fullsuite.lock`. No paid call: every test uses fakes.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `lint-imports --no-cache` | **24 kept**, 0 broken |
| `pytest -n auto -q -p no:cacheprovider` (full suite) | **12,941 passed, 2 xfailed**, 0 failed (18 min 12 s; `fixtures-local/rw6a-landing-fullsuite.log`) |
| `pytest -m durability` | **106 passed**, 12,837 deselected (3 min 38 s) |
| `npm install`, `npm run typecheck` | ok, clean |
| `npm test` (vitest) | **115 files, 936 tests passed** |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished, exit 0 (`src-tauri` differs from main: the four passthroughs) |
| tracked fixtures | `git status` clean after both lanes |

The counts equal the stage's last gates (backend on `ebcfe6ff4`, frontend on `12aed8c89`). Nothing failed, so nothing was rerun; none of the known flakes (`"8841"` in `test_mcp_c1a_review.py`, `test_reading_usable_with_synthesis_worker_down`, the vitest timing cases in `Workbench.test.tsx` and `FeedbackScreen.test.tsx`) fired.

### Parity (backup-API copies; no model call)

**Setup:**
- **Copies.** The owner's `fixtures/linear_algebra` and `fixtures/probability` (with probability's `.learnloop/state.sqlite`) were copied with `copy_tree_with_databases` from the main checkout into `fixtures-local/landing-rw6a/orig/`. Each original was read once; every other copy came from `orig/` or another copy through the same helper. `arxiv_v2` was not opened.
- **Code.** Main's code is `git archive e182f3ec8` and the merge's is `git archive e4155b989` (each without the top-level `fixtures/`), each first on `PYTHONPATH`; every run printed the `learnloop` package it imported. Both archives were removed afterwards.
- **Environment.** `LEARNLOOP_CONFIG_DIR` was an empty directory, `LEARNLOOP_AI_PROVIDER` unset, every process started in a directory holding no `.env`. `model_call_receipts` is 0 on the recap copies.
- **Starting state.** Both vaults at schema 165, label `mvp-0.8`.
- **Cleanup.** The previous landing's `fixtures-local/landing-rw2a/` (1.5 GB) was deleted once these copies existed, behind guards on the exact path, that git ignores it, that it holds no tracked file, nothing in it modified in the last 30 minutes (`-mmin`), and no process with a file open in it.

| Check | linear_algebra | probability |
|---|---|---|
| **(a)** open (migrate), main's code / the merge's | 165 → 207 (42) / 165 → 207 (42) | 165 → 207 (42) / 165 → 207 (42) |
| `.dump`, main's vs the merge's, outside the `schema_migrations` stamps | **identical** (22,746 lines; the 194 `schema_migrations` rows differ only in their applied-at stamps) | **identical** (14,315 lines; same) |
| `rebuild --shadow --json`, main vs merge | **0 differences** (facet 0, mastery 2, schedule 8; live unchanged on both sides) | **0 differences** (facet 0, mastery 1, schedule 1) |
| `doctor --json`, main vs merge | **0 differences** (57 issues, 1 error) | **0 differences** (101 issues, 48 errors) |
| **(b)** at `mvp-0.8`: every facet's `facet_evidence_timelines(...)` (`as_dict`, plus each of main's eleven `TimelinePoint` fields), 40 single-facet `facet_evidence_timeline` curves, every LO's `recipe_gaps` and `lo_certification` (default arguments) | **byte-identical JSON** (39 facets, 84 points, 2 corrections; 21 LOs, 23 recipes, 1 certified) | **byte-identical** (29 facets, 2 points; 18 LOs, 0 certified) |
| the same, on a copy upgraded by main's code to `mvp-0.27` (`upgrade --to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice), so the regrade-contract reading and its hold are live | **byte-identical** (82 points, 7 corrections, 1 attempt held `grade_contract_unrecorded`; 1 LO certified) | **byte-identical** |

Every shadow, doctor and certification run left its database byte-identical (sha256 before and after).

**(c) The recap, through the real sidecar** (merge code over stdio: `initialize`, `get_config`, then the RPCs). On a 207 copy of probability, two synthetic sessions were written through the Reader's own code (`reader_inquiry.record_activity` with a frozen clock, and one question through `reader_dialogue.ask` with the stub client): a previous session 4 h to 3 h ago on `ext_01KYMSJJNJQ0W9QHZ9ZMFD88NY` with one question, and the current visit opened a minute ago (a second copy leaves the current visit out, as at the destination). Each read was sent three times; the times are the third call's, measured at the client while the full suite held the machine.

| Case | Result |
|---|---|
| recap on, in the Reader (`visitId` = the current visit) | `reader.recap` 136 ms (card present: the session, Still open 4, Since last time read); `reader.wrap_up` 47 ms (the current session: empty lists); `reader.wrap_up_offer` 36 ms (`offer: false`: the most recent session has no activity yet); `get_config` carries `recap: {enabled, wrapUpEnabled}` |
| recap on, at the destination (no current visit) | `reader.recap` 138 ms; `reader.wrap_up` 110 ms (the source's latest session: Still open 1); `reader.wrap_up_offer` 74 ms (`offer: true`) |
| what the reads write | nothing: the `.dump` is identical before and after the twelve reads |
| `reader.recap_event` `recap_shown` | exactly **one** new row: `interaction_events`, `reader_action_invoked` on `reader_extraction`, payload `{authority_class: salience_only, event: recap_shown, extraction_id, visit_id}`, origin `learner`; nothing else changed or removed |
| `[recap] enabled = false`, `wrap_up_enabled = false` | `reader.recap` and the `recap_shown` / `recap_dismissed` events refuse `recap_disabled`; `reader.wrap_up`, `reader.wrap_up_offer` and `wrap_up_opened` refuse `wrap_up_disabled`; `get_config` has no `recap` key; the `.dump` is unchanged across all seven calls |
| `[reader_inquiry] enabled = false` (recap on) | all seven calls refuse `inquiry_disabled`; no `recap` key; `.dump` unchanged |

The sidecar's `initialize` itself re-stamps three derived rows' timestamps on open (`facet_recall_state`, `facet_capability_evidence`); main's code does exactly the same on the same copy, so it is pre-existing and not RW6a's. The stage's own measurement (§5 item 5: 0.03-0.05 s) is in-process; these are client round trips over stdio with fsync-on-commit.

### For the owner

- **No upgrade command, no migration.** RW6a has no successor and no schema change; the vaults keep their label and schema head 207. Nothing runs on first open beyond what main already does.
- **Turning it off:** in the vault's `learnloop.toml`, `[recap]` / `enabled = false` hides the card and refuses its RPCs; `wrap_up_enabled = false` does the same for Wrap up and the destination line. They are independent. Both need `reader_inquiry.enabled` on (RW1a's switch, the default): with it off there are no sessions and every recap RPC refuses `inquiry_disabled`.
- **To look at it:** the stage record's §7 (a backup-API copy, `doctor --fix-state`, `LEARNLOOP_VAULT=<copy> npm run dev`; read, close, come back after 30 minutes). Visits before RW1a landed were never recorded, so the first card appears after the first recorded session.
- **Open questions (defaults taken):** the stage record's §6: 1 no card in Today's re-entry panel (DL1); 2 sessions per source; 3 no visits while `reader_inquiry` is off; 4 no *on the map ▸* yet; 5 *keep open* writes nothing; 6 the quick check's own self-check is not a second-look record.
- **Residuals of the review's F1 round 3** (what the cutoff replay cannot rebuild from timestamped rows, recap-only): the only-grade exception's score at the cutoff is re-summed from `points_awarded` when a later grade overwrote the attempt row; the hold is read under today's tag, so a cutoff before the vault's mvp-0.26 upgrade sees an uncited regrade as held; today's item maximum counts at the cutoff. The as-of read replays the grading ledger only: trace observations, activity classifications and the P0 masses are read as they are now.
- **Pre-existing, default path, left open (not RW6a's):**
  - **[Medium] A regrade to zero on an item whose criteria have no authored targets never reaches the Demonstrated curve.** `_observation_events_by_facet` emits an epoch's event only for `requested & (historical_facets | credited_facets)`, `historical_facets` reads authored `criterion.targets` only, and a zero-credit epoch credits nothing, so the correction is dropped: the ledger banks 0 but the curve keeps the earlier credit. That breaks receipt exactness for such items, and for them "a success regraded to nothing does not clear an independent-check claim" does not hold, because the recap reads the curve. The fix changes the default extraction, so it goes through the algorithm-change playbook (queued separately).
  - **[Low]** The current curve has no point where a replay hold is placed (holds are recorded by replay, without a grading row), so the plotted history of a held-then-released attempt overstates the hold interval. "Since last time" no longer reads those points (it replays as of each moment).
  - `desktop_validate.py` stops on `apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts` ("unclassified desktop source"), a file on the base from the Reader PDF selection stage.
- **Friction notes for the next stages** (stage record §5): RW1b's `reader_authored_questions` columns, RW2b's `highest_help_level` and level 3+ claims, RW6b's `retired` / `no_longer_needed` commitment events and the `reader_session_digests` input, RW5a's `figure_predictions(extraction_id, matched, created_at)` read.
- **Not done in the stage:** no real-UI look (the screens are exercised through the real `ReaderScreen` in jsdom).
