# The first evening, step 1: one OK before every model route

Step 1 of the stage "The first evening, finished" (the design's §4 part "one OK before every model route", §5's row
"AI OK", §6's row 1, §7's row 1). The owner decided on 2026-11-20 that the OK comes first for every model route and
that "the one time OK covers all usages (so the learner says OK once)". Branch `ux/first-evening-one-ok` from main
`5508b1a9bb`.

| Commit | What |
|---|---|
| `59df4c918f` | `learnloop.ai.model_use` (the record, the live lookup), `model_call` refuses before anything is sent, the factory binds every client; the test world (`tests/ai_ok_world.py`, marker `no_ai_ok`) |
| `958b641a0a` | The waiting state (jobs, RPCs, judge routes, uploads), the resume, the sheet's payload, the build gate and Quick Add read the one OK; backend tests |
| `a1faee36fb` | The Decider landing's two tests read the Decider's recipient under "What's sent"; docstrings |
| `19a339b245` | The one sheet on every entry, desktop and phone; `desktop_validate.py` counts `app/aiOk.ts` |

This record and ledger row UX-10 are the last commit. No algorithm tag, no kill switch, no prompt change, no new
config field, no migration, no new spend. The blind grader is untouched. Once the OK exists every request is
byte-identical to today's (`tests/test_identity_pins.py`: 345 passed, no pin moved).

## The record, where it lives, and why

**One record**: the table `[ai.consent.model_use]` of the library's `learnloop.toml`:

```toml
[ai.consent.model_use]
granted_at = "2026-11-21T09:00:00+00:00"
data_flow = "all_model_use"
disclosure_version = 1
```

It reuses the existing consent table (`AIConfig.consent: dict[str, AIConsentRecord]`, `extra = "allow"`) under a new
key, so **no config field is added, changed or retired and no migration is needed**: `config/retired.py`, the
effective defaults golden (`ai.consent = {}`) and the whole-config hashes of a library without the record are
unchanged. Writing the record changes that library's config dump, as the earlier per-provider OK always did.

Saying OK writes it into the library (`connect_ai` with `provider = "current"`, `first_run.py:294`) and the existing
mirror copies it into this computer's `ai_defaults.toml` (`save_ai_settings_to`, unchanged), from where libraries made
later inherit it (`bootstrap`, unchanged). **Why the library plus the machine mirror**: the library is where the OK has
always been recorded and travels with the library; the machine mirror makes "once" hold on this computer: the
lookup reads the library's record, else the mirror's (`model_use.recorded_acceptance`), so an existing library opened
on a computer where the OK was given elsewhere is covered without asking again.

**What counts** (`model_use.acceptance_in`, pure):
- the `model_use` record with `data_flow = "all_model_use"` and a date;
- **an earlier genuine OK**: any other `[ai.consent.<key>]` with a date and `data_flow = "passages_and_answers"` (or
  no `data_flow`, the old default), i.e. the connection sheet's OK for `codex`, `chatgpt`, `openrouter` or a profile.
  Such a library is never asked again, whichever provider serves now.
- **Not**: the upload-only OKs (`whole_files`, `whole_files_zai`), a record without its date, the `model_use` key with
  another flow. A ChatGPT sign-in (OAuth) writes nothing; **connecting no longer writes a record** (`connect_ai`
  `chatgpt`/`openrouter` used to write `consent.chatgpt`/`consent.openrouter`; now the sheet asks for the OK after
  connecting); a "Use OpenRouter instead" grant no longer counts as consent (`AuthoringRoute.consented` used
  `or self.granted`; now `model_use.accepted(vault_root)`, `add_source.py:521`).

The lookup is **live**: it reads the two files as they are, again only when their stat changes (`_consent_in_file`,
mtime/size/inode cache), so a client built before the OK is covered the moment it is given.

## The enforcement point and every route it covers

**One function at physical request admission**: `learnloop.ai.execution.model_call` calls `model_use.admit(client)`
first (`execution.py:518`), before the request gate, the receipt and any byte, for wrapper and physical calls alike.
`admit` refuses (`ModelUseNotAccepted`, not an `AIProviderUnavailable`, so no retry, fallback or failure line acts on
it) when the client carries a lookup (`model_use.AcceptanceLookup`) that finds no OK. **The lookup is bound to the
client** by the single factory, `make_ai_provider_client_from_profile` (`client.py:65`-`86`), from the `vault_root` it
was already given, so background threads and resumed jobs keep it whatever context they lost. A client built outside
the factory (a test's double) carries no lookup and is not held here.

| Route | How it is held | Where |
|---|---|---|
| ChatGPT plan transport (each Responses request, retries, refresh) | factory-bound; `model_call` per request | `client.py:86`, `chatgpt_plan.py:488` |
| OpenRouter / OpenAI-compatible chat, its transport retries and truncation retry | same | `client.py:73`/`:77`, `openai_chat.py:574` |
| The Decider | same | `client.py:81`, `decider.py:252` |
| Embeddings (OpenAI-compatible, Voyage contextual) | same | `client.py:65`/`:69`, `openai_embedding.py:102`, `voyage_contextual.py:134` |
| Fallback (a granted OpenRouter for a plan route; `ai.fallback_provider`) | built by `ready_client_for_task` through the same factory | `routing.py` (unchanged) |
| Video generation | bound in `make_video_generation_client`; its HTTP helper admits itself (no `model_call`) | `client.py:114`, `openrouter_video.py:187` |
| Owner tools building clients from a library (judge readiness, recurrence benchmarks, embedding compare) | bound | `probability_arms.py:404`, `benchmarks.py:258`, `embedding_compare.py:209` |
| Whole-file uploads (transcription, hosted PDF reading, GLM-OCR to z.ai) | `_guard_file_upload` requires the OK first (then the upload's own OK, unchanged) | `jobs.py:370` |
| Background ingest jobs whose purpose is model work | the runner waits before the handler | `runner.py:138`, `:1081` |
| Any other job that reaches a model | the refusal (or an error raised from it) becomes the waiting state | `runner.py:1157`, `:1419` |
| Reader Ask, desktop and phone (`reader.ask`; the phone host runs the same handler) | refused with `waiting_for_ok` before anything is stored | `handlers/reader.py:157` |
| Section quick check (`reader.author_section_question`) | refused before the job is queued | `handlers/reader.py:2029` |
| Reading-path judgment (background thread) | `JudgeRoute.problem` gives `waiting_for_ok`, an admission reason re-asked on every read | `reading_paths.py:677`, `:881` |
| Goal resolver (`curriculum.create_deliverable`, `curriculum.set_scope`) and every curriculum chat route | refused before the goal is made; `ChatRoute.problem` gives `waiting_for_ok` | `handlers/deliverables.py:567`, `:596`; `source_retrieval/deliverables.py:261`, `:317` |
| Quick Add (`confirm_quick_add`) | refused before anything is created or queued | `handlers/ingest.py:1498` |
| Automatic question build (Add, keep-ahead, retry) | the planner's gate reads the one OK (`needs_consent`, as before) | `add_source.py:521`, `run_auto_study_map` |
| Any RPC whose model call no early check stopped | the sidecar's dispatcher answers `waiting_for_ok` (desktop and phone host share `_handle`) | `server.py:152` |

Not covered (not reached through the factory): the experiment harnesses `experiments/contextual_embeddings/live.py`
(`qwen_factory`, built from a config with no library root) and `experiments/contextual_embeddings/anthropic_api.py`;
both are owner-run research commands on copies. Grading, diagnosis, hints, lessons and every other serving route go
through the factory and `model_call`, so they are held, but their own handling of the refusal (what the learner sees)
is only the backstop's `waiting_for_ok`; see "What I did not verify".

## The waiting state and what resumes

Missing OK is never a provider failure:
- a job waits as `waiting_for_input` with `result.waiting_for_input = {"code": "waiting_for_ok"}`, its lease released,
  no `error`, never tried again on its own (`a_retry_may_cure` is false for it);
- a book's automatic build waits as before (`outcome: waiting, reason: needs_consent`), its card saying "Questions
  wait for your OK" with the action that opens the sheet;
- an RPC answers the error code `waiting_for_ok` with "LearnLoop is waiting for your OK before it uses AI." and stores
  nothing (the Ask's question, the goal's sentence, Quick Add's choices stay on screen);
- a reading path shows that line and "Give your OK ▸".

**Saying OK resumes once**: `connect_ai` `current` records the OK and then `ingest_jobs.resume_waiting_for_ok()`
requeues every job waiting for it, a single time (a second OK finds none: `resumed == []`), and
`release_waiting_builds` re-plans every book waiting (`released`); the desktop sends each request the sheet was opened
for again, once; a reading path is read again when the sheet closes and judges then. Connecting where the OK was
already given resumes the same way. **Closing the sheet** ("Not now") sends nothing: the work stays waiting, the
refused request is answered with its `waiting_for_ok` line, and reading (local) is unaffected.

## The sheet, as shipped, and where it appears

Title **Before LearnLoop uses AI**. Text:

> LearnLoop uses AI for questions, replies, feedback and other learning help. It can send your books, files you
> choose, your questions and your answers to the services you connect.
>
> **OK** · What's sent ▸
>
> Reading works without it. Anything that needs AI waits for your OK.

"What's sent" (folded; built by the sidecar, `first_run.whats_sent`), one line each:
- "To {AI}: passages of your books and of files you add, your questions to the tutor, and your answers, to write
  questions, reply and give feedback."
- the Decider's sentence, when one of its routes is on (unchanged words, `decider_judgments.connection_note`);
- "To {provider}: short passages of your books, to find related passages." when embeddings are on;
- "If {AI} is unavailable, LearnLoop asks before it uses OpenRouter instead." when that offer can be made;
- "Sending a whole file (a recording to transcribe, a scan to read) asks once more, for that file."
- "You say OK once, and it covers every use. Your library stays on this computer."

OK is the one primary action. With no AI connected, after OK the same sheet says "Now connect the AI LearnLoop uses."
with Continue with ChatGPT (primary), Use an OpenRouter key and Other (advanced) ▸; connected, "Connected to {AI}.
Questions are on." and Close. The close control reads "Not now" until then.

It appears (one sheet, `ConnectAISheet`, rendered by `App` while asked):
- **Add** (empty install's first library, a fresh library, an existing library without an OK; drop, Ctrl+O, the Add
  box, the Library): `add_source` returns `waitingForOk`, and the sheet opens as the book opens;
- **Quick Add**: confirming is refused with `waiting_for_ok`; the sheet opens and OK sends the confirmation again;
- **direct Reader entry**: the reading path waiting asks once per app run on its own, "Give your OK ▸" any time;
  the Reader's Ask and quick check open the sheet from their refusal and are sent again on OK;
- **goals**: creating or rescoping a goal, likewise;
- **any other desktop request** refused with `waiting_for_ok` (the API client, `app/aiOk.ts`); requests refused
  together share one sheet and one answer, and a request refused again after OK is not asked about again;
- the existing "Questions wait for your OK · Give your OK" card and Today lines open it as before;
- **the phone**: it cannot record the OK in this step (no allowlisted method). Its Ask shows: "LearnLoop asks for your
  OK before it uses AI: it can send your books, files you choose, your questions and your answers to the services
  you connect. Say OK on your desktop. Nothing was sent." and keeps the typed question; the host sent nothing.

Distinct controls stay: the uploads' own OKs, the animation's "runs AI-written code" consent, the extraction repair's
consent, money confirmations and "Use OpenRouter instead".

## Tests

New: `tests/test_one_ai_ok.py` (23 tests, all `no_ai_ok`), `apps/learnloop-tauri/src/app/aiOk.test.ts` (5). Extended:
`tests/test_ux_phase1_connect_ai.py` (+3 tests, module `no_ai_ok`), `ConnectAI.test.tsx` (rewritten to the one
sheet, 13), the phone's `SelectionSheet.test.tsx` (+1). The parameterized trap covers ChatGPT plan, OpenRouter,
OpenRouter with a throttled-then-retried request, embeddings and the Decider, each in the request's thread and in a
thread of its own: zero dispatches before the OK, the call proceeds after one OK (two requests for the retry case),
and the next call is never asked again. Separately: video, a granted fallback, jobs (a model job and one that reaches a
model: both wait, resume once, run once), Add's build, Reader Ask desktop and phone, quick check, goal resolver,
reading-path judge, Quick Add, the dispatcher backstop, the record's rules, the live read and the machine mirror, an
earlier OK honoured across a provider change, a sign-in / upload OK / fallback grant not being the OK, and "Not now"
leaving the book readable with its questions waiting.

**The test world.** Every test not about the OK runs as a computer where the OK was given (`tests/ai_ok_world.py`,
from `conftest.py`'s run setup: `model_use.machine_acceptance` reports one); a test about it is marked `no_ai_ok`
(new marker in `pyproject.toml`), reads the real files and gets an empty config directory of its own. Without this,
every test that builds a real client through the factory against a library with no OK (about 60 files) would be
refused. A process a test spawns reads the real files.

**Fail-first.** With only `model_use.py` and the tests in place and every other source change reverted:
`tests/test_one_ai_ok.py` + `tests/test_ux_phase1_connect_ai.py` → `28 failed, 6 passed` (every adapter dispatched
before the OK; the video client sent its request; the Ask, quick check, goal and Quick Add went ahead). With the
sheet's sources reverted: `ConnectAI.test.tsx` → `6 failed | 7 passed`; the phone's `SelectionSheet.test.tsx` →
`1 failed | 4 passed`; `aiOk.test.ts` cannot import without `app/aiOk.ts`.

**Assertions changed, and why** (each follows the owner's ruling; none loosened):
- `test_ux_phase1_connect_ai.py`: the OK writes `model_use` (flow, version, mirror), not `codex`; `whatLeaves` is the
  new sentence and the Decider moved into `whatsSent`; `current` with nothing connected now records the OK (was
  `ai_not_connected`); connecting ChatGPT or OpenRouter writes no consent (was `chatgpt`/`openrouter`), and a later
  library inherits `model_use`.
- `test_plan_first_transport.py::test_rr_f1…`: `connect_ai current` with nothing connected answers (needs `connect`,
  no fallback offer) instead of `ai_not_connected`; the property it pins (a status read offers nothing) is kept.
- `test_decider_landing.py` (two tests): the Decider's sentence is checked in `whatsSent`, not appended to `whatLeaves`.
- `test_ux_phase1_auto_build.py::test_missing_consent_waits_for_one_ok`: marked `no_ai_ok` (unchanged assertions).
- `ConnectAI.test.tsx`, `denyList.test.tsx`: the one sheet's words and order (OK first, connecting after).

## Commands and results

Every pytest run through a script with explicit targets, `-n 1`, `-p no:cacheprovider`, in a 3G scope, under the
scratch wrapper; the npm installs used `npm ci --offline` against the shared npm cache.

| Command | Result |
|---|---|
| `tests/test_one_ai_ok.py` | 23 passed |
| `tests/test_ux_phase1_connect_ai.py` | 11 passed |
| `scripts/affected_tests.py --files <the 19 changed src files>` | 1,366 files (`execution.py` reaches nearly everything); ran the files whose names contain the brief's filters plus `plan_first_transport, chatgpt_plan, openrouter, decider, embedding, ingest_runner, quick_add, video, glm_ocr, audio, transcri, mobile, phone, upload, sidecar_contract, one_ai_ok, section_done, empty_first_build, keep_local, reread, first_run, probability_cli, recurrence, ai_compare, judge_routes, spend, curriculum` and `test_ai_config`, `test_effective_defaults_golden`, `test_evidence_config`: 133 files in four chunks of at most 40, `-m "not arc_close"` |
| chunk 1 (40 files) | 2 failed, 600 passed (the Decider landing's two `whatLeaves` tests, fixed in `a1faee36fb`; then `tests/test_decider_landing.py`: 14 passed) |
| chunk 2 (40 files) | 1080 passed |
| chunk 3 (40 files) | 794 passed, 5 skipped |
| chunk 4 (13 files) | 241 passed |
| identity pins, structure ratchets, effective defaults golden, CLI help snapshot, kill switches, SQLite file copies, public tip guards, retired config identities, diagnosis journey golden, desktop activation audit, mobile allowlist | 777 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 44 kept, 0 broken. |
| `scripts/check_gate_partition.py` | collected 32165: landing 32100 + arc_close 65 |
| desktop `tsc --noEmit`; phone `tsc --noEmit` | 0; 0 |
| desktop vitest, 4 workers | 321 files, 3361 tests passed |
| phone vitest, 4 workers | 43 files, 437 tests passed |
| desktop `frontend:build`; phone `vite build` | 0; 0 |

No Rust was touched (no new Tauri command: the OK rides on `connect_ai`), so `cargo check` was not run. Structure
ratchets: no number rose (no private patch site, no source-text assertion, `handlers/reader.py` 2934 lines under its
2980 ceiling). No pin or golden moved. `desktop_validate.py`'s counts moved by one for the new `app/aiOk.ts`
(334 sources, 323 entry-reachable, 340 active); the vault references are not regenerated here (the landing does).

## What a walk must check

With a config directory where no OK was ever given (the walk's machine config must not already hold one, or every
library is covered):
- **empty install** and **fresh library**: the first Add opens the sheet as the book opens; nothing is written before
  OK; "Not now" leaves the book readable and its card on "Questions wait for your OK"; OK later writes questions once;
- **existing library without an OK**, on a computer without one: the same; with an OK given in another library on this
  computer: never asked;
- **an earlier OK** (a library from before this step): never asked, whatever the provider;
- **direct Reader entry** (a book opened from the Library, no Add this run): the reading path asks once; Ask and the
  quick check ask and, after OK, go ahead without a second press; with "Not now" the Ask's question stays;
- **Quick Add** and **a goal sentence**: asked, then done once on OK;
- **sign-in alone does not bypass it**: Continue with ChatGPT after OK connects; signing in without OK still asks;
- **the phone**: its Ask before the OK shows the desktop-OK line and sends nothing; after the OK on the desktop the
  same question goes through;
- the sheet at phone width, keyboard-only (Tab to OK, What's sent, Not now; Escape closes as Not now), reduced motion,
  and the real WebKitGTK window.

## What I did not verify

- No app, browser or server was launched: every entry above is proven by tests with fakes, not seen.
- Grading, diagnosis, hints, lessons, the teacher, approach maps, AD forecasts, cue judges, the router's models and the
  rest are held by the enforcement point (they build clients through the factory), but their own handling of the
  refusal was not exercised: a background one may record a failure where it catches errors broadly (nothing is sent
  either way), and an interactive one shows the sheet through the dispatcher's `waiting_for_ok`. In practice these
  run only where questions exist, which needs the OK, or in libraries whose earlier OK is honoured.
- The two experiment harnesses named above are not bound.
- The phone cannot record the OK (no allowlisted method in this step).
- `desktop_validate.py` itself was not run (its catalog needs the regenerated notes); its counts were updated by hand.
