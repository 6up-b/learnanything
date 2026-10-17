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
