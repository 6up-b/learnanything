# The first evening, step 7: what comes next, dated

Step 7 of the stage "The first evening, finished" (the design's §4 part "Tomorrow: add one shared, read-only dated
summary", §1's rows "Session end/tomorrow" and "Today/phone after practice", §5's row "Dated next-practice summary",
§6's row 7 and §7's row 7). Three live walks ended with the same complaint: "I could not find when my answered
questions would return", "can you tell what will happen tomorrow? No" (the third audit's F40 and UX-44c). Before this
step the session's end returned no next-due date and the finish card said only what moved; Today said nothing of
tomorrow; the full list said "comes back in 9 days". Now one read-only summary, `next_practice`, is carried by the
session's end and by Today's plan read, and the finish card, the phone's finish banner, Today (desktop and phone) and
the full list say what is due on which day, when a check on your own becomes available, and what is still being
written. Branch `ux/first-evening-next-practice` from main `f44283f88e`.

No algorithm tag, config key, kill switch, migration or prompt change. Nothing is scheduled, served, built or written:
the summary reads through a read-only attach and the database is byte-identical after it (below). No identity pin,
golden or snapshot moved.

## Judgment calls to read first

1. **Today says it only once the day's plan is done or holds nothing.** While the plan holds questions, the plan is
   what comes next; a "tomorrow" line under Begin would compete with it. Done or empty (desktop: `done || emptyDay`;
   phone: the stop/done screen and an open plan with nothing in it) it says the lines. The plan-off Today (the
   desktop's minutes-and-Begin screen, the phone's queue) says none: `get_daily_plan` returns its off reply there and
   carries no summary. The phone's finish banner in queue mode does say them (they come from `end_session`).
2. **The finish card and Today never say it twice.** The desktop's Today hides its lines while the finish card is up
   (`finishCardShown`, from the shell's `finishSummary`). On the phone the banner's snapshot is shown while it is still
   the same plan day as Today's current read, and Today's lines are hidden meanwhile; after the day turns, the banner
   keeps "Session finished: N answers." and Today says the new day's lines.
3. **"Still due today" and "available now" are the finish's alone.** At the finish the summary may hold questions due
   today that the session did not reach; the card says "Still due today: 1 question." and tomorrow's count becomes
   "Tomorrow: 2 more questions due" ("Nothing more is due tomorrow." when none), because an unanswered question due
   today is still due tomorrow and "Nothing is due tomorrow" would be false. Today's own plan and full list say what is
   due today, so Today's lines start at tomorrow (with the same "more" when something is still due today).
4. **Minutes only where an estimate supports them.** The plan's estimator always returns a number: with no authored
   `expected_minutes`, no answer of the learner's on the item and none on its kind of question, that number is the
   fallback constant (3 minutes plus the default half minute of feedback). A day containing such an item gets
   `minutes: null` and the words name no minutes ("Tomorrow: 1 question due."). Every other day's minutes are the sum
   of the plan's own per-item estimates (`item_minutes`, as the plan stores them).
5. **A check's question is counted once, as the check.** An open cold check (`cold_retry` or
   `certification_cold_probe`, pending or served, not expired) whose chosen question is also in the review population
   is counted under the check's `not_before` day, not under its review due: the routine queue holds that question back
   for the check (`add_source._not_askable_now` reads the same rows). A check whose question is retired or not
   servable is not named (no promise that cannot be kept). A check whose day has come is today's ("available now" at
   the finish; the plan serves it).
6. **"Being written" is the writing jobs' own topics.** `writing` is every topic named by a queued or running
   `practice_expansion` job's payload, less the parts that job already wrote or stopped on (`question_parts` with a
   patch or an error); adaptive difficulty's variant jobs (`ad_commission_id`) write no new topic's questions and are
   not counted. It does not call `add_source.reading_questions`: that read claims owed topics on the desktop (a write).
   `waiting` (finished sections whose writing waits for the book's topics or the desktop) and `held` (topics whose
   written questions wait for a look) are in the object, but no words say them in this step: Today's cause lines
   (step 4) already say the waiting states with the book's name, and the held line ("2 more questions need your OK")
   with its review target is step 8's.
7. **Today leaves "being written" to the book's line when one shows.** On an empty day Today's cause line (step 4:
   "Writing questions from what you’ve read of “Part”… Keep reading meanwhile.") names the book and the part; the
   summary's "Questions on 3 more topics are still being written." is then left out (`writing: cause === null`). No
   step-4 line was changed: none states something this summary states better.
8. **The full list's day.** A row in the list's "later" part says the day of its effective due from the summary
   ("comes back tomorrow", "comes back Wednesday", "comes back on 9 November"), or, kept for a check, "a check on your
   own from 14 November". A row the summary does not name keeps its own due time, now in the same words on this
   device's calendar ("comes back in 9 days" is gone). "coming back later today" remains only for a row truly due later
   today.
9. **A step's reply keeps the last summary.** Only `get_daily_plan` carries it (every answer, application, review
   acceptance and queue-revision change already re-reads Today's plan through the `queue` tag; the phone's revision
   poll does the same). The phone stores a step's reply (`plan_keep_going`, `set_plan_minutes`, `next_plan_item`) as
   the plan; those carry no summary, so the screens keep the last one read (`useLatestNextPractice`) until the next
   read rather than going blank. Adding it to every plan reply would put a population read on each answer's step.
10. **The day's turn.** The summary says when the plan's next day starts (`calendar.next_day_starts_at`, that local
    midnight as UTC, with its own offset); Today (desktop and phone) reads the plan again then (`useNextDayRefresh`),
    once per value, so a reply carrying the same instant does not loop.
11. **The classic HUD is unchanged.** `[ui] practice_feedback = "classic"` keeps its full-screen HUD exactly; the lines
    are on the simple finish card.

## Commits

| Commit | What |
|---|---|
| `b74c4909d0` | Tests first: the summary's backend tests and fixture (`tests/test_next_practice.py`, `tests/next_practice_helpers.py`, three tests in `tests/test_ux_phase4_feedback.py`) |
| `7ee89bd4e2` | `daily_plan.next_practice`; `end_session` and `get_daily_plan` carry it |
| `14f899cbf7` | Tests first: the words (`app/nextPractice.test.ts`), the finish card, Today and the full list (desktop), the phone's Today and finish banner, the deny-lists |
| `8a0b72e8a0` | `app/nextPractice.ts`; the finish card, Today, the full list (desktop); the phone's Today and finish banner; `desktop_validate.py`'s counts |
| `49d95001e4` | Comments name what the code does, not the stage |
| `fcde215f06` | `app/todayPlan.test.ts`: the full list's day words |
| (this record) | `docs/reviews/first-evening-step-7.md` |

## The object, and where each field comes from

`learnloop.daily_plan.next_practice.next_practice(vault, repository, clock=None)`
(`src/learnloop/daily_plan/next_practice.py:61`), camel-cased on the wire as `nextPractice`:

| Field | Meaning | Source |
|---|---|---|
| `as_of` | the instant read (UTC) | the clock (`SystemClock`, or the plan env's) |
| `calendar.today`, `.tomorrow` | the plan's local calendar day and the next | the machine's local zone at that instant, as `engine.local_date` (`src/learnloop/daily_plan/engine.py:593`) |
| `calendar.zone` | the zone's name at that instant ("EDT") | `astimezone().tzname()` |
| `calendar.next_day_starts_at` | the next local midnight, as UTC, with that midnight's own offset | as `engine.local_day_start_iso` (`engine.py:599`) |
| `reviews[]` | `{date, count, item_ids, learning_object_ids, minutes}` per day, sorted; a due now or earlier is today's | `engine.review_population` (`engine.py:1550`: active, servable, not withheld by intent, each at its effective due) with the build's intent view `scheduling.intent.serving.intent_serving` (`src/learnloop/scheduling/intent/serving.py:623`), less the open checks' questions (`next_practice.py:100`) |
| `reviews[].minutes` | the sum of the plan's estimates, or null | `daily_plan.estimates.Estimator.item_minutes` (`src/learnloop/daily_plan/estimates.py:138`) over `load_duration_evidence` (`:161`), the plan's `latency_cap_minutes` and `read_words_per_minute`; null when an item's `estimate` (`:118`) rests on the fallback alone |
| `checks[]` | `{date, count, item_ids, learning_object_ids, kinds}` per day of `not_before` | `followup_tasks` (`migrations/139_certification_cold_probes.sql:50`) of the cold kinds (`serve_eligibility.COLD_FOLLOWUP_TASK_KINDS`, `src/learnloop/serve_eligibility.py:84`), status pending or served, `expires_at` null or not passed (`next_practice.py:179`) |
| `next_review_date` | the first review day after today, or null | `reviews` |
| `writing` | `{topic_count, learning_object_ids}` | queued/running `practice_expansion` jobs' `learning_object_ids` (`content/pipeline/jobs.py:3474`) less their `question_parts` with a patch or error (`jobs.py:3611`); no `ad_commission_id` (`next_practice.py:195`) |
| `waiting` | `{section_count}` | `reader_section_progress` finished rows stamped `waiting_for_build`, `deferred_to_primary` or `enqueuing` (`src/learnloop/db/stores/reader.py:43`-`:47`) |
| `held` | `{topic_count, learning_object_ids}` | `reader_topic_question_work.state = 'held'` (`migrations/257_reader_topic_question_work.sql:20`; set at `jobs.py:3703`) |

Carried by `end_session` (`src/learnloop_sidecar/handlers/sessions.py:236`, the finish's snapshot) and
`get_daily_plan` (`src/learnloop_sidecar/handlers/daily_plan.py:433`, at the plan env's clock), through
`next_practice_or_none`: a read that fails is logged and the reply carries `null`, never an error. Nothing else of
either reply changed. The phone host's allowlist names RPCs, not reply fields: an optional field on two existing
replies, no pin edited.

A held grade is no review (`learnloop.held_grades`): the item keeps the due it had. A question never answered has no
due date and is in no group. A question still being written has no item and no date.

## The read-only proof

- The summary never reads through the caller's repository: it attaches the same file with
  `Repository.attach(path, read_only=True)` (`src/learnloop/db/repositories.py:330`), a `mode=ro` SQLite connection
  on which any write raises. The reads it shares with serving skip their lazy marks on such an attach
  (`Repository.due_followup_tasks`, `src/learnloop/db/stores/remediation.py:530`, guards both marks with
  `not self._read_only`). It builds no plan and calls neither `build_due_queue` nor `read_due_queue`.
- `test_the_read_leaves_the_database_byte_identical`: on the full fixture plus an expired cold retry (a writable read
  marks it `expired`) and a due one (marked `served`), the SHA-256 of the database file and its WAL (if any) and a
  full `iterdump()` are equal before and after the read.
- `test_a_writable_read_of_the_due_queue_would_have_changed_it` is the control: the same fixture, `read_due_queue` on
  the writable repository, and the fingerprint differs, the two tasks now `expired` and `served`.
- `test_it_reads_nothing_through_the_callers_repository`: an object carrying only `sqlite_path` gives the same summary.
- The same byte-identity test was run in the durability lane (`--durable-sqlite`: WAL, `synchronous=FULL`, fresh
  vaults) as well as the fast lane (below).

## The calendar and daylight-saving rules

- A day is the machine's local calendar day, as the plan's (`engine.local_date`). Each instant (a due, a check's
  `not_before`) is converted with the offset in force at that instant (`datetime.astimezone()` on the instant), never
  with now's offset; a due or `not_before` already passed is today's.
- The next day starts at its own local midnight (a naive midnight resolved in the local zone), so a 25-hour or 23-hour
  day has the right length.
- The words compare plain dates of that calendar (`daysFrom`, UTC day numbers of the `YYYY-MM-DD` strings): no zone or
  clock of the device decides which day is "tomorrow". Today and tomorrow by name; the next six days by weekday; after
  that the date ("9 November"), with the year when it differs from today's ("8 January 2027"). "due Monday", "due on
  9 November", "available from Saturday", "available from 14 November", "available from tomorrow".
- Tested: `test_a_due_after_the_clocks_go_back_stays_on_its_own_day` (New York, Saturday 31 October 2026 19:00 EDT: a
  due at 23:30 EST on Sunday 1 November, 04:30 UTC on Monday, is Sunday's, where now's UTC-4 would put it on Monday;
  the next day starts at 04:00 UTC; read during that Sunday, the next day starts at 05:00 UTC, 25 hours later); the
  words across the spring change's 23-hour Sunday, a month's end and a year's end (`nextPractice.test.ts`).
- The full list's fallback for a row the summary does not name uses this device's calendar (the desktop's is the
  plan's machine).

## The words, before and after

Desktop, the session finish card (simple presentation):

| State | Before | After |
|---|---|---|
| Any | "26 minutes this session · 9 questions" / "Since last time: ● …" / "3 days in a row" · **Done ↵** | the same, then the lines below |
| Due tomorrow, with estimates | — | "Tomorrow: 2 questions due · about 3 minutes." |
| Due tomorrow, an item with no supported estimate | — | "Tomorrow: 1 question due." |
| Nothing tomorrow, next within the week | — | "Nothing is due tomorrow. Your next questions are due Monday." (one: "Your next question is due Wednesday.") |
| Nothing tomorrow, next after the week | — | "Nothing is due tomorrow. Your next question is due on 9 November." |
| Some still due today | — | "Still due today: 1 question." then "Tomorrow: 2 more questions due · about 3 minutes." or "Nothing more is due tomorrow. …" |
| A check open now | — | "A check on your own is available now." (several: "2 checks on your own are available now.") |
| A later check | — | "A check on your own is available from Saturday." / "… from tomorrow." / "… from 14 November." (several: "2 checks on your own are available from 7 November.") |
| Writing | — | "Questions on 3 more topics are still being written." (one: "Questions on 1 more topic are still being written.") |
| Only checks or writing, nothing dated | — | "Nothing is due tomorrow." before them |
| Nothing dated, nothing under way, or no summary | — | nothing |

Phone, the finish banner (plan on: `PlanToday`; plan off: `TodayScreen`): before "Session finished: 2 answers."; after,
the same banner and under it the finish's lines above (`session-next`).

Today (desktop `TodayPlace`, phone `PlanToday`), once the day's plan is done or empty:

| State | Before | After |
|---|---|---|
| Done, nothing more for today | "Done for today. …" / "Nothing else is needed today." | the same, then e.g. "Tomorrow: 2 questions due · about 3 minutes." "A check on your own is available from 14 November." "Questions on 3 more topics are still being written." (`today-next`) |
| Done, nothing due tomorrow | — | "Nothing is due tomorrow. Your next question is due Wednesday." |
| Empty day with a book's cause line | "Nothing planned for today." and the cause | the same, then the dated lines without the writing line |
| Open plan with questions | the plan | unchanged: no lines |
| Under the finish card (desktop) or the same day's finish banner (phone) | — | no lines (the finish says them) |

The full list (desktop), a row in its later part:

| Row | Before | After |
|---|---|---|
| Never answered | "not answered yet" | unchanged |
| Due later today | "coming back later today" | unchanged |
| Due tomorrow | "comes back tomorrow" | unchanged |
| Due in 2-6 days | "comes back in 4 days" | "comes back Wednesday" |
| Due in 7 or more days | "comes back in 9 days" | "comes back on 9 November" |
| Kept for a check on your own | its review due ("comes back in 2 days") | "a check on your own from 14 November" |

## Tests, with fail-first evidence

Backend (`tests/test_next_practice.py`, the fixture in `tests/next_practice_helpers.py`: New York, the night daylight
saving ends; a review due tomorrow, one due 23:30 on the long Sunday, one nine days on, a check fourteen days on whose
question is also due Tuesday, one never answered, one retired, one with a held grade, one with no estimate, a writing
job with one of four topics written, a variant job and a finished job, a held topic):

| Test | Asserts |
|---|---|
| `test_the_evening_summary_dates_every_review_check_and_work_under_way` | the whole object |
| `test_a_due_after_the_clocks_go_back_stays_on_its_own_day` | DST, both instants |
| `test_a_checks_question_is_counted_once_as_the_check` | no double count |
| `test_what_has_no_day_is_given_none` | never answered, retired, held grade, writing has no date |
| `test_minutes_only_where_an_estimate_supports_them` | 3.0 and null |
| `test_nothing_due_tomorrow_names_the_nearest_later_day`, `test_whats_due_now_or_later_today_is_todays`, `test_a_check_open_now_is_todays_and_an_expired_one_is_gone`, `test_sections_waiting_for_their_book_are_counted_apart`, `test_as_of_is_the_instant_read` | the other states |
| `test_the_read_leaves_the_database_byte_identical`, `test_a_writable_read_of_the_due_queue_would_have_changed_it`, `test_it_reads_nothing_through_the_callers_repository` | the proof |

`tests/test_ux_phase4_feedback.py`: `test_the_session_finish_says_what_comes_next_dated` (the reply's `nextPractice`
equals the camel-cased expected object), `test_the_session_finish_and_today_agree_at_the_same_instant` (`end_session`'s
and `get_daily_plan`'s are equal), `test_the_session_finish_stands_when_what_comes_next_cannot_be_read` (null, the
reply intact).

Fail-first (each run at the tests' commit, before the implementation):

```
tests/test_next_practice.py: 12 failed, 1 passed (ModuleNotFoundError: No module named 'learnloop.daily_plan.next_practice';
  the one that passed is the control, read_due_queue changing the database)
tests/test_ux_phase4_feedback.py (the three): 3 failed — KeyError: 'nextPractice'
src/app/nextPractice.test.ts: Failed to resolve import "./nextPractice"
src/components/SessionFinishHud.phase4.test.tsx: 2 failed — Unable to find an element by: [data-testid="session-next"]
src/screens/today/TodayPlace.test.tsx (with nextPractice.ts present, TodayPlace.tsx and todayPlan.ts as before): 6 failed —
  4× Unable to find [data-testid="today-next"] (done day, nothing tomorrow, empty day with a cause, the day's turn);
  "expected 'Topic 1comes back in 9 days' to contain 'comes back on 5 November'";
  "expected 'Topic 1comes back in 6 days' to contain 'comes back Wednesday'"
apps/learnloop-mobile Today.plan.test.tsx and Today.queue.test.tsx (PlanToday.tsx and TodayScreen.tsx as before): 5 failed
```

Desktop: `src/app/nextPractice.test.ts` (11: days, every line's state, the full list's row words, the deny-list);
`SessionFinishHud.phase4.test.tsx` (+3); `TodayPlace.test.tsx` (+8: done day, nothing tomorrow, open plan silent, an
empty day's cause keeps the writing, under the finish card, no summary, the full list from the summary, the day's
turn); `copy/denyList.test.tsx` (every new line, `STEP7_SENTENCES`); `copy/denyList.phase4.test.tsx` (the finish card
rendered with a summary). Phone: `Today.plan.test.tsx` (+5) and `Today.queue.test.tsx` (+1).

Assertions changed:

- `TodayPlace.test.tsx`, UX-44c's "the full list says when an answered question comes back": `/comes back in 9 days/`
  became the day's name (`comes back on <date>`, computed from the same due): the words this step replaces.
- `app/todayPlan.test.ts`, UX-44c's "an answered one says when it comes back, by the day": `"comes back in 9 days"`
  became `"comes back on 29 November"`, and a weekday case (`"comes back Tuesday"`) was added.
- `copy/denyList.test.tsx`, `ROUND_3B_SENTENCES`: "comes back in 9 days" became "comes back on 9 November" (the
  sentence no longer exists; the new one meets the list).

## What was run

Every Python run through the scratch wrapper (empty home, config and Codex dirs); every pytest run from a script that
refuses an empty target list, `-n 1`, in a 3 GB scope, one at a time; vitest with 4 workers; npm through the shared npm
cache.

| Command | Result |
|---|---|
| `tests/test_next_practice.py` (fast lane) | 13 passed |
| `tests/test_next_practice.py --durable-sqlite` (WAL, the production pragmas, fresh vaults) | 13 passed |
| `test_next_practice.py` and `test_ux_phase4_feedback.py` `-k "next or agree or stands"`, three runs | 23 passed, three times |
| `tests/test_identity_pins.py` after the first source commit | 351 passed |
| `scripts/affected_tests.py --files` the three changed sources | 608 files (over 150: the filter below was run instead) |
| The brief's name filter (ux_phase4, session_finish, sessions, today, first_questions, due_queue, review_population, daily_plan_engine, mobile_allowlist, mobile_v2_plan, mobile_v4, plus next_practice: 20 files) united with every test file calling `end_session` or `get_daily_plan` (61): 76 files, chunks of 40 and 36, `-m "not arc_close"` | 1034 passed, 9 skipped, 1 xfailed; 1131 passed, 17 skipped |
| `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards`, `test_desktop_activation_audit` | 410 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 45 kept, 0 broken. |
| `scripts/check_gate_partition.py` | collected 32523: landing 32457 + arc_close 66 |
| Desktop `npm run typecheck`; `vitest run --maxWorkers=4` (whole suite); `npm run frontend:build` | clean; 322 files, 3,438 tests passed; built |
| Phone `npm run typecheck`; `vitest run --maxWorkers=4` (whole suite); `npm run build` | clean; 43 files, 446 tests passed; built |

No identity pin, golden, structure ratchet or snapshot moved. `desktop_validate.py`'s three counts take the one new
non-test TypeScript file (`app/nextPractice.ts`): 334 → 335 TypeScript files, 323 → 324 entry-reachable, ACTIVE
340 → 341 (checked against the generator's own audit). No ledger row: no defect was found.

## What a live-route walk must check

The patient first-day persona (once right, once wrong or partly right) and the learner who stops at 60 % (the design's
§7 row 7), on the real desktop window and the phone:

1. **The finish names the real next date.** End a session (Done for today): the card says "Tomorrow: N questions due
   · about M minutes." or "Nothing is due tomorrow. Your next questions are due <day>."; a read of
   `practice_item_state.due_at` for the answered questions (converted to the machine's local day) confirms each named
   day. A wrong answer's question should come back sooner than a right one's.
2. **Returning on that day agrees with the scheduler** (the design's §8 bounded test): on the named day, Today's plan
   offers those questions; on the day before, it does not. The day named is the machine's local day, including across
   a daylight-saving change if one falls in the window.
3. **A check on your own** (the wrong-answer walk's redo: "A check on your own comes back on another day." in feedback):
   the finish says "A check on your own is available from <day>." with the same day as the task's `not_before`; the
   full list says "a check on your own from <day>" for its question, and the question is not also counted under
   tomorrow.
4. **The 60 % learner**: with part-read questions still being written, the finish says "Questions on N more topics
   are still being written." with no date, and Today's empty day keeps step 4's "Writing questions from what you’ve
   read of …" without a second writing line.
5. **Today after "Done"**: under the finish card Today shows no dated lines; after Enter dismisses the card, Today's
   done screen shows the same lines (same instant, same words).
6. **The full list** (`l`): an answered question shows "comes back <weekday>" or "comes back on <date>", never "later
   today" unless it truly comes back today.
7. **The day's turn**: leave Today open across local midnight (or move the clock): the lines move ("Tomorrow" becomes
   the new day's) without a press.
8. **The phone**: the finish banner's lines under "Session finished: N answers."; the plan-done Today's lines once the
   banner's day has passed; the queue (plan off) shows the banner's lines.
9. **Cost**: `get_daily_plan`'s time with and without the summary on a large vault (the sidecar debug log); the read
   is one review population, one intent view and one duration-evidence load per Today read.
10. The database's mtime and `PRAGMA data_version` unchanged across a Today read that changes nothing else.

## What was not verified

- No app, browser, server, phone or real model ran (the rules): the screens are tested in vitest/jsdom only; their
  layout at phone width and in the real WebKitGTK window is not seen.
- Real vaults: the summary's cost on a large vault (it adds one population read per `get_daily_plan`), and whether the
  owner's real estimates are "supported" (minutes shown) or not, are not measured.
- The design's §8 "Tomorrow wording matches actual serving dates" test (advance a frozen clock to each named day and
  compare eligible items through the scheduler) was not built: the summary uses the plan's own population and intent
  view, but serving on the day also passes the scheduler's other gates (exam reservations, rung holds, the cold
  lane's deferrals), so a question named for a day could still be held back on it. The words say "due", not "will be
  served".
- The phone's clock against the host's: the words use the host's calendar; the refresh at the next day uses the
  device's clock to wait for the host's instant.
- The classic HUD shows no lines (unchanged by choice).
