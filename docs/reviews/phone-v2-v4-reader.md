# Phone v2, stage V4: the phone Reader

**Spec:** `docs/specs/spec_mobile_frontend_v2.md` §8's V4 row (detail in §3 "The phone Reader" with CA7 folded in, §2.3, §4, §5.1-§5.4, §7; owner decision **D4**, accepted 2026-11-06: text first, the original page as a host-rendered image on demand, no PDF.js on the phone). **Branch:** `phone/v4-reader`, from main `ccb6573987`. **No migration, no successor** (the playbook ruling is §3). **No model call of its own:** the Ask from a selection is the desktop's `reader.ask` under its routes and budgets (D2); pages are rendered locally with pypdfium2. **No new dependency** (pypdfium2 is the one the sidecar's `span_view` already uses; see §2 item 10).

## Commits

| Commit | What |
|---|---|
| `031c10cc83` | (1) The backend: `render_view`'s range; the phone's protection; the media lane and its cache; allowlist V4 rows and the `phone_reader` switch and capability; the plan's reading blocks on the phone; D6's deferred generation; §2.3's lift; tests (`test_mobile_v4_reader.py`, `test_mobile_v4_plan.py`, `test_mobile_v4_eligibility.py`) and the pins that moved |
| `5a75873fa5` | (2) The PWA: the Read place and the Reader, the selection sheet, *as printed*, the outbox's reader intents, the page cache in the service worker, the generated contract files; vitest |
| `85fc6e32a8` | (3) This review, the spec's "As built" note, regenerated references |
| (this commit) | The review's commit and gate tables |

Main had not moved from `ccb6573987` when the stage ended (checked before (3)), so there was nothing to merge.

## 1. What was built

### 1.1 `reader.render_view`'s range (§3.2)

- `ReaderRenderViewInput` gains `sectionId`, or `fromSpanId`/`toSpanId` (either end may stay open; both forms together are refused). A section is the guide plan's (`section_map.extraction_sections`: its first to its last readable span, in reading order). The reply carries only that range's blocks, in the same block shape, plus `range: {sectionId, fromSpanId, toSpanId, blockCount}`. An unknown section or span is `validation_error`.
- **Absent, the reply is today's byte for byte.** The range is applied after the payload is built, and only when a range parameter is not null; explicit nulls are absence. `test_render_view_without_a_range_is_todays_reply_byte_for_byte` rebuilds the pre-V4 reply from the same primitives in the same order and compares the JSON bytes. The shared handler holds the range, so the host and the desktop can't drift.

### 1.2 Protection on the phone: text, page images, caches

One predicate, `learnloop_sidecar.phone_reader.phone_withheld` (the vault's `exam_material`: an exam-pool source, a held-out unit, a reading held back until it is marked, rules 1-4; it includes the desktop Reader's held-out partition). It is read at every request, never cached, and fails closed (an unreadable predicate withholds the whole reading). It runs only at a phone origin; the desktop never reaches it.

- **Text.** At a phone origin, `reader.render_view` refuses a reading exam material covers whole (`409 held_out_material`, before a render view is made) and sends every covered passage with no text, math or assets (`withheld: true`; the block stays, so section counts, progress and the place line up). `protection` is widened to every passage withheld here and, for a ranged reply, covers the whole reading, so it is one value per reading. `reader.guide_plan` refuses a reading withheld whole and drops any suggested passage, cue or section question that names a withheld passage. `reader.ask_history` drops exchanges grounded on one. `get_source_library` lists only books the phone's Reader opens (reader on, ready, not withheld whole) and never a file location.
- **Model actions.** At a phone origin, `reader.ask` and `reader.capture` (Save) refuse a selection naming a withheld passage before any model call or write. The PWA offers no Ask on a protected selection, by the desktop's own rule (`groundingProtected`, mirrored in `readerModel.selectionProtected`).
- **Page images and stored images.** The media lane refuses (`403 held_out_material`) any page that holds a withheld passage on any reading of its file, any page of a reading withheld whole, and any image that is the original of a protected book. It serves only pages some reading of the book covers: a page nobody has read (an answer key at the back of a book read in part) is not known to be safe, so it is `404`.
- **As printed.** `practice.as_printed` at a phone origin answers `kind: none` when the item's print names a withheld passage (the desktop's server already crops only the problem's own blocks and nothing during a check on your own).
- **Caches.** The display cache never holds what the host never sent. Each reading's protection is kept beside what was cached of it (`readerCache`); when a load sees it changed (a mark made on the desktop), every cached section of that reading and every page image go. A 401 clears the display cache and the page images together (`clearDisplayCache`). The service worker keeps only a `200` the host marked `immutable`, never a refusal.
- **The reader's protection key** (`protection` on `render_view`) is what the phone's Ask gating and its cache purge read; both are above.

Tests: `test_the_phone_is_never_sent_held_out_text`, `test_a_reading_exam_material_covers_whole_reaches_the_phone_not_at_all`, `test_the_phones_ask_and_save_refuse_protected_passages_before_any_model`, `test_a_page_showing_a_held_out_passage_is_never_served`, `test_a_mark_made_after_a_page_was_cached_withholds_it_at_once`, `test_an_image_that_is_a_protected_books_original_is_withheld` (`tests/test_mobile_v4_reader.py`); `readerCache.test.ts`; the service worker's page tests in `sw.test.ts`.

### 1.3 The media lane (§3.3, §5.1)

- `learnloop_mobile/media.py`: `GET /api/v1/reader/page/{ref}/{page}?w={px}` and `GET /api/v1/assets/{sha256-<hex>}`, both `Token(app)` (a capture token is `403`, no token `401`, another identity `403`), both on their own executor (`mobile-media`, 2 threads) and lane (`pages`, 8 in flight, then `503 host_busy`), so a render never queues behind an RPC.
- `ref` is a reading (an extraction id) or the file itself (`sha256-<hex>`, the originals store's name, which an `llpdf://` link names). `page` is zero-based, as the blocks carry it. `w` snaps to 720 or 1080 (any other query key is `400`).
- **Per vault.** The host is pinned to one vault; an id resolves only in its database, a token only on the host that paired it, and the cache is keyed by the vault (`<cache>/<vault key>/<file hash>/<page>-<width>.png`): two hosts never share an entry, even for the same file.
- **Immutable and content-addressed.** `Cache-Control: private, max-age=31536000, immutable`, an `ETag` from the file's hash, page and width. A reading names one revision and so one file, so the URL names its content.
- **The cache** is outside the vault (`MobileConfig.page_cache_dir`; default `$XDG_CACHE_HOME/learnloop/mobile-pages`, or beside an isolated `LEARNLOOP_CONFIG_DIR`; a path inside the vault is refused), written atomically, bounded at 512 MB (oldest first). The protection check runs on every request, cached render or not.
- Protection reads a settled snapshot of the vault's files (`settled_load_vault`, reloaded when the fingerprint moves; one caught mid-rewrite is `503 vault_unsettled`, never a read of a half-written source-sets file).
- Rendering uses `span_view`'s pdfium lock, which every pdfium call in the process shares.

### 1.4 Progress, activity, doses and the end of a reading (§3.4, §5.4)

- **Monotonic progress was already there.** `Repository.upsert_reader_section_progress` takes `MAX` of `spans_seen` and `span_count` and stamps `revealed_at`/`completed_at` once. No change, so replay equivalence is unaffected. `test_progress_is_monotonic_across_the_phone_and_the_desktop` pins it across a phone and a desktop write.
- **The outbox's reader intents** (`store/outbox.ts`, `READER_INTENT`, IndexedDB store `intents`, DB version 3): `reader.mark_section_progress`, `reader.log_activity`, `reader.dose_offer_event`. On the host each is a `long` method: its acceptance is a `mobile_jobs` row keyed by the intent's ULID, so a replay after a lost reply is coalesced (the same key with other params is `409 submission_conflict`), and the row each writes is the desktop's exactly. The latest progress per section replaces an unsent older one. A flush asked for during a running one runs right after it (found by the journey test: an intent queued mid-flush otherwise waited a minute).
- **Activity** carries the client's `occurredAt` per event, so RO0's `occurred_at`/`received_at` gap survives the outbox. At a phone origin each event records `device_surface: phone_reader`, set by the server from the origin. The payload's own `surface` stays the Reader's view (`text`, `pdf`, `watch`), and a client's `device_surface` is dropped. `test_activity_is_the_desktops_row_with_the_phones_surface`.
- **Doses.** `reader.dose_offer` is the desktop's handler: its seed is the visit and section, so the same boundary gives the same draw. `test_doses_from_the_phone_are_the_desktops_draw_and_rows` runs the same boundaries on two identical vaults, one through the desktop's handler and one through the phone, and compares every `ad_dose_offers` row and every reply (ids and times aside). A replayed `taken` is one row.
- **The end of a reading.** `plan_reading_ended` and a completion's `reading_progress`/`block_ended` events are the desktop's (the same detail, `{outcome, minutes_counted}`). For a device, the reading block they end is the one its Reader was served (`engine._current_reading`), which can follow work it left for the desktop; for the desktop it is the plan's current block, as before.
- **D6: a section finished on the phone builds its questions on the desktop.** On the phone host's secondary attach, the first completion stamps the section `deferred_to_primary` (the same once-only claim) and enqueues nothing. The previous code would have stamped `enqueuing`, then failed on the unbound runner, and stranded the section for good. The desktop takes the stamp at its start and when its Reader opens the book (`reader.get_progress`), and enqueues exactly what its own completion would have: the same candidates, refs and reason. A failed enqueue hands the stamp back. Keep-ahead on the host is the durable reading request the desktop's sweep already acts on; the host no longer tries to act on it itself. `test_a_section_finished_on_the_phone_builds_its_questions_on_the_desktop_once`.

### 1.5 The plan's reading blocks on the phone (§2.2; V2's hold lifted)

- **Kill switch `phone_reader`** in `mobile.toml` (`MobileConfig.phone_reader`, default true). It has the same shape as `phone_plan` and `phone_probes`. Off: every V4 method is `409 phone_reader_off`, the media endpoints are `404`, `meta` says so, and the phone is V3's.
- **The capability.** The host carries `phone_reader` on the origin only for an app that says it has the Reader (`LearnLoop-Capabilities: phone_probes,phone_reader`). A cached V3 app keeps V3's plan, where every reading waits for the desktop, and is never handed a reading step it can't end. A job keeps what its app said; a restarted host's job runs as V3's.
- **The step filter** (`PlanStepFilter.reading`): a reading block is the phone's when its book opens in the phone's Reader (reader on, the source not opted out, the reading completed, nothing of its section withheld from the phone). Otherwise it is held and counted as before. The phone's boundary decisions name it in their `device` entry (`readings: phone_reader`) beside the rules in force.
- Tests: `tests/test_mobile_v4_plan.py`. The phone takes the reading block and ends it, and its `block_started`, `reading_progress` and `block_ended` events equal the desktop's on an identical vault. `plan_reading_ended` from the phone matches. A cached V3 app holds the reading. A reading the phone may not show stays held. The decisions name the reader and the rules.

### 1.6 §2.3: item assets and `llpdf://` as page images

- `device_eligibility.ineligibility_reason(media=True)` (under `phone_reader`) lifts `embeds_image`, `links_llpdf` and `references_item_asset` exactly when every such target is one the host serves by content address: an `llpdf://…/sha256-<hex>[#page=N]` link to a stored PDF, or an image or asset whose target ends in a stored image's `sha256-<hex>` name. A path, a remote image, raw HTML or an unaddressed `llpdf:` link keeps PR-6's reason; nothing reads text cues. The rules are named `device_eligibility_v2` on every phone decision under it (a new rule set is a new name). `tests/test_mobile_v4_eligibility.py`.
- The PWA renders a prompt's stored images from `/api/v1/assets/…` and its page links as the page image, on demand (`PhoneMedia`, `withPageLinks`); a remote image stays a link (CSP).

### 1.7 Ask and Save from a selection; *as printed* after feedback (§3.5, CA7)

- `reader.ask` is a job on the phone (`runLong`, the 15 s wait, then a poll; *Thinking…*). The phone sends the desktop's fields: `extractionId`, `spanId`, `selectionSpanIds`, `selectionQuote`, the question, `retrievalIntent`, and `parentExchangeId` for a follow-up (*Another way*, *That didn't help*). The answer opens in the sheet in the three voices.
- **A cold check is the server's to know.** The allowlist refuses `coldActive`, `coldAttemptId` and `workbenchSessionId` from the phone. At a phone origin the handler refuses the Ask (`cold_check_open`) while a session this device owns has an active probe presentation, or its checkpoint's question is administered on your own now (`as_printed.cold_now`) or is today's open randomized check. Unreadable state refuses it.
- **Save** is `reader.capture` with `action: highlight` and no session (the allowlist's constraint). It is local first, and the desktop drains its outbox.
- ***As printed* after feedback** is `practice.as_printed` with `render`: the crops the desktop's Feedback shows, and *View the page* as the page image (§2 item 1).

### 1.8 The PWA

- `read/ReadScreen.tsx`: the books, with *Continue reading* for the one last read here, and the copy on this phone when the desktop is away.
- `read/ReaderScreen.tsx`: the section list as a sheet, with words rather than glyphs (§2 item 3). It shows the section's text in the book's face with KaTeX. A held-out passage says so in one line. A block whose health recommends the page shows the page image, labelled *as printed*; others offer *View the page*.
- Loading and progress: the copy on this phone is shown at once and then refreshed (§4.5), and the next section is prefetched. Progress is reported as spans scroll into view (debounced). *Next section* reports the completion, asks the dose arm, and shows its offer with the desktop's words and why.
- Plan readings show the desktop's banner, with *Back to today's plan* (`left_reader`) and *Skip this reading* (`skipped`).
- `read/SelectionSheet.tsx`, `read/PageImage.tsx` (blob URLs under the bearer token), `read/AsPrinted.tsx`, `read/readerCache.ts`, `read/readerModel.ts`.
- Shell changes:
  - Today's plan step `reading` opens the Reader.
  - The Reader covers the tab bar, and Back returns to the books.
  - `#/read/<extraction>/<section>` reopens it.
  - The offline line now says *Reading and capture still work*.
- `public/sw.js`: the page and stored images, cache first, kept across builds, bounded at 300 entries; only an immutable `200` is kept.
- The generated `phoneMethods.ts`/`retryPolicy.json` (the digest moves, so a cached V3 app offers the reload) and 13 new request contracts. Both name scanners now read `rpcOnce`, the outbox intents' one send.

## 2. Where the spec was not built as written, and the smallest way to finish

1. ***As printed* is `practice.as_printed`, not `reader.block_original_region`.** The desktop's Feedback reads the item's print through `practice.as_printed`, whose server keeps the crop to the problem's own blocks, never its solution, and nothing during a check on your own. `reader.block_original_region` crops any block it is named, with none of those guards, so it is not allowlisted. The phone's *View the page* is the media lane's. Smallest alternative if the owner wants the RPC itself: allowlist it with a phone-origin guard (the `phone_withheld` check plus `practice.as_printed`'s solution rule).
2. **There is no server-side "saved place".** The desktop keeps its place in its own `localStorage`, and `reader.saved_place` only translates a place across re-reads. The shared place is the host's reading history (`reader.get_progress`, the desktop's own fallback through `resumeSpanFromHistory`), so *Continue reading* lands at the furthest section read on either device, and progress never moves backwards. Each device keeps its own scroll, as §5.6 says. `reader.saved_place` is allowlisted (read only) but not called. Smallest finish for "the device that read last wins the place": a `reader_last_place` row (a migration) written by both Readers.
3. **The section list uses words ("read", "started", "you're here"), not `○ ◌ ●`.** Those glyphs are evidence states; reading is never evidence of mastery, and the desktop's guide carries no glyphs either.
4. **The phone is stricter than the desktop on display.** The desktop shows a book's held-out text and refuses model actions on it. The phone is never sent it (the stage's protection rule) and says *A passage held out for your exam. It isn't shown here.*
5. **Not on the phone in V4:** the guide's section-break quick checks and their cold administration, margin cues and the intent box, annotations as objects, translation and the watch plan (desktop tools, as §3.5 and §2.1 J7 say). With no reader check on the phone, the Reader's own cold flag is never the phone's to send.
6. **A dose's extra question** shows its prompt and, on *Show the answer*, its expected answer as a self-check (recorded `taken`). The desktop's inquiry answer path (`reader.inquiry_question_action`) is not on the phone. Smallest finish: allowlist it with the outbox.
7. **The cold check for Ask** is read from this device's open sessions: an active probe presentation, the checkpoint's item cold now, or today's open randomized check. A check open on the desktop's session is the desktop's own Ask's to refuse, as before.
8. **Pages a reading does not cover are not served** (§1.2), so an `llpdf://` link to an unread page is `404` on the phone.
9. **Surfaces.** Activity rows record `device_surface: phone_reader`. The dose rows and the plan's reading events carry none: there is no column (no migration), and the plan's events are the desktop's exactly. A dose row's visit id ties it to the phone's activity for that visit.
10. **pypdfium2 must be in the host's environment.** It comes with the `pdf` and `glm-ocr` extras, not `mobile`. Without it the page endpoint answers a typed `503 pages_unavailable` rather than a misleading `404`. Smallest finish, if the owner's host ever runs without it: add `pypdfium2>=4` to the `mobile` extra (one `uv lock`).
11. **The §2.3 lift covers content-addressed targets only.** A prompt's relative image path (`figures/graph.png`) or remote image stays the desktop's, because the host serves no path. Smallest finish: an item-asset store keyed by hash at authoring, so prompts name `sha256-…` targets.
12. **The library list is `get_source_library` at a phone origin** (read only, filtered). V7 adds the rest of J15. The handler skips its background reload of applied batches on the phone host (its ingest is the desktop's), which the secondary attach could not do anyway.
13. **The D6 pickup runs at the desktop's start and when its Reader opens the book**, not on a timer. With the desktop app already open, a section finished on the phone builds its questions when the desktop's Reader next reads that book's progress, or at the next start. Smallest finish: call `drain_deferred_section_generations` from the reading sweep's pass.
14. **A mark made while the phone is offline** reaches its caches at the next contact with that reading (the protection comparison). Until then the copy already on the phone, sent before the mark, stays readable offline. The host refuses everything protected from the mark on.
15. **iOS selection is not driven in jsdom.** The selection sheet is tested as a component (the spans and quote it sends, refusals, Save); the long press and the handles are P7's.

## 3. Persisted meaning and the playbook ruling

- No table, column or migration. New values only: `reader_section_progress.generation_batch_id = 'deferred_to_primary'` (written only by the phone host), the activity payload key `device_surface` (only at a phone origin), and decision `device` entries with `readings` and `device_eligibility_v2` (only under a phone origin).
- **Ruling (`docs/algorithm-change-playbook.md`): no successor.** Reading recorded from the phone is the same evidence as on the desktop: the same handlers write the same rows (progress, activity, dose draws and uptake, plan reading events; pinned by the equality tests). Reading is salience only and never evidence of mastery, so nothing scored, scheduled or replayed reads it differently. The desktop's serving and recording are unchanged at a None origin. The rebuild and replay read nothing new: progress was already monotonic, the deferred stamp is a claim, not a projection, and the activity key is salience.
- The 2026-10-17 rule (a change to which items are served as measurements mints a successor) does not apply.
  - Reading blocks are not measurements.
  - §2.3's lift changes which items a phone origin may be served, under a host switch, and names the new rules on every phone decision (`device_eligibility_v2`), as V2's device rules did without a successor. The desktop's is unchanged.
  - An item lifted is the same item with the same stimulus, rendered from the same bytes.
  - If the owner reads the lift as a measurement change, the smallest alternative is V3's: a `PHONE_MEDIA_VERSIONS` successor gating `media=True`.

## 4. Security notes for review

- **Allowlist:** 14 V4 rows, each named with its constraints. The G3 enumeration keeps every other method at 403. `reader.block_original_region`, `reader.pdf_view`, the library's Ask and Compare, figures, lessons, presets and annotations stay off (`test_v4_holds_back_what_later_stages_open`).
- **Origin and capability:** `phone_reader` comes from the host's config and the app's header, never a parameter, and the desktop's origin is None.
- **Media:** `Token(app)` under the same Host and identity checks; GET only; path segments matched exactly (`..` and extra segments are 404); only `w` as a query key. Protection is read on every request. Errors carry no exception text.
- **No spend:** the Ask is the desktop's, with its refusals checked before the provider is asked (the tests' provider fails the test if it is reached on a refused path).

## 5. Gate

Owner rule 2026-10-17: the full suite, the whole durability lane and the whole vitest run are the landing gate's, on the merged tree; none was run here. Every pytest, vitest and npm command ran under `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, pytest at `-n 6` at most, vitest at `--maxWorkers=4`, the large passes behind `flock /tmp/learnloop-fullsuite.lock`.

| Step | Command / files | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`; `uv pip install --offline pypdfium2==5.14.0` | done |
| Architecture | `uv run lint-imports --no-cache` (under `env -i`, empty `HOME`/`CODEX_HOME`/`LEARNLOOP_CONFIG_DIR`) | **43 kept, 0 broken** |
| New tests while building | `test_mobile_v4_reader.py`, `test_mobile_v4_plan.py`, `test_mobile_v4_eligibility.py`, `test_mobile_allowlist.py`, `test_mobile_meta_timing.py`, `test_mobile_phone_contract.py` | 393 passed |
| Targeted pass 1 | 146 files: every test file `git grep` finds naming a changed module or function (`render_view`, `mark_section_progress`, `get_progress`, `log_activity`/`record_activity`, `reading_ended`/`note_reading_progress`, `device_eligibility`/`PlanStepFilter`/`DeviceFilter`/`device_policy`/`ineligibility_reason`, `get_source_library`, `as_printed`, `reader.ask`, `reader.capture`, `guide_plan`, `ask_history`, `section_generation`, `RequestOrigin`/`request_origin`, `learnloop_mobile`, `reader_section_progress`, `_step_filter`): the AD, reader, plan, mobile, data-capture, curriculum, figure, library-ask, re-read, UX Phase 1 and session-ownership files | **11842 passed, 11 skipped, 3 failed**: three pins of V3's shape (the allowlist's milestone set, the host's lane counters, the app's capability header), updated |
| Targeted pass 2 | 77 files: every `test_mobile_*`, every `test_sidecar_reader*`, every `test_ux_phase1_*`, `test_reader_pdf_selection`, `test_daily_plan_reading`, `test_reading_request_sweep`, `test_reading_hardening_landing`, `test_reader_activity`, `test_ro0_row5_event_times`, `test_reread_safety`, `test_device_eligibility`, `test_request_origin`, `test_session_ownership`, `test_reader_ca1_as_printed`, `test_ad3_dose_arm`; the contract set (`test_cli_help_snapshot`, `test_config_refactor` (defaults snapshot), `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_architecture`, `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_registry_audit`, `test_module_catalog_inventory`, `test_public_tip_guards`, `test_sqlite_file_copies`); the display-label audit (`test_sidecar_measurement`, `test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`); the frozen cycles (`test_codex_lockdown_frozen`) and the process-launch allowlist (`test_codex_lockdown_round3`) | **1708 passed, 1 failed**: the phone contract's reply journey, where a long reader method passed the host's 15 s wait under load and answered 202. The journey now follows a 202 as the phone does; rerun 8 passed |
| After the docs commit | `test_module_catalog_inventory.py`, `test_public_tip_guards.py` | 23 passed |
| PWA | `npm install --prefer-offline`; `npm run typecheck`; `npx vitest run --maxWorkers=4 src/api src/store src/sw.test.ts src/shell src/practice src/today src/capture src/read src/desktopImports.test.ts`; `npm run build` | typecheck clean; **26 files, 313 tests passed**; build passes |
| Desktop | no file under `apps/learnloop-tauri` changed (`git diff --stat` empty), so no desktop typecheck, vitest, build or `cargo check` | n/a |
| References | `module_generate.py` then `module_validate.py`; `desktop_validate.py`; `validate_vault.py` | PASS (1252 notes, links 41797/41797); 323/323 + 6/6, reproducible; 2245 notes. Provenance-only churn left out (46 notes). No schema change, so no DB reference run |
| Durability lane | no migration and no DB/connection code changed (the two repository methods are plain statements on an existing table) | not run |
| Spend | no paid call, no live call: every ad-hoc command ran under `env -i` with empty dirs and routes off; tests use fakes (the Ask's provider is a refusal in the tests) | $0 |

## 6. Phone acceptance (the owner runs these on the iPhone; spec §7.5)

| Id | Check |
|---|---|
| **P7** | Open a book from **Read**: the books are listed; open one. Tap the section title: the section list opens as a sheet; pick a section. The text is in the book's face and math renders (try a section with an equation; wide equations scroll inside their own box). Tap *View the page* under a block: the original page appears as printed. Select a passage (long press, then drag the handles): the sheet offers **Ask**, **Save**, **Copy**; type a question and Ask: *Thinking…*, then an answer that quotes the passage (§ the book, › you, ◇ LearnLoop). Then turn on airplane mode: the section you have open and the next one stay readable (*the copy on this phone*), and *Next section* still works into the prefetched one. Read to the end of a section, turn airplane mode off, and open the desktop's Reader on the same book: the progress made offline is there. |
| **P8** | Finish a section on the phone (*Next section*, or *Done with this section* on a plan reading). On the desktop, open the Reader on that book: the section shows as completed, and its questions arrive in the plan or the list as they would after finishing it on the desktop (they are built by the desktop app, D6: if the desktop app was closed, they arrive after it starts). |

Also worth a look while there: a held-out section of a book you marked shows *A passage held out for your exam* with no text and no page; *Back to today's plan* on a plan reading returns to Today with the plan moved on.

## 7. Open questions for the owner

1. §2 item 2: is the shared place "furthest read" (built) enough, or should the device that read last win (a small migration)?
2. §2 item 10: add pypdfium2 to the `mobile` extra?
3. §3: confirm the no-successor reading of §2.3's lift (or take the V3-style successor).

## Landing onto main

Landed by the landing agent (continuation after a usage-limit stop), tip merged with main `a525dbcef4` (router speed 2 and the figure author fix; `5fe3a22558` and `214c206ff1` before it). No successor, no migration. Kill switch `phone_reader` in `mobile.toml` (and the app's capability header: a V3 app gets V3).

### Rulings (verbatim)

- R1: "F4: protection filtering on the phone runs on the COMPLETE stored provenance of every Ask exchange, tutor answer and excerpt (selection span ids, cited spans, excerpt locations, anchors), read before any presentation switch strips fields; only after an item passes is it projected under the presentation switches. Codex's two reproductions (reader_inquiry off hiding selection_span_ids; both tutor presentation switches off hiding excerpt locations) are tests, failing on the pre-fix source, and every other phone read that filters by provenance is checked for the same ordering. No further Codex round; I read the diff before landing."
- R2: "Open questions, decided: (a) Continue reading lands at the furthest section read on either device, as built (a last-place row is not needed now); (b) pypdfium2 is added to the mobile extra at the version the project pins (5.14.0), so page images work on a host without the pdf extras; (c) the §2.3 lift (image, page and asset prompts phone-eligible when the host serves every target by content address, device_eligibility_v2) takes no successor: it changes which device shows an item, not what an answer means, and the label records it; (d) 'as printed' after feedback stays practice.as_printed (guarded) rather than reader.block_original_region; (e) the D6 pickup also running from the desktop's reading sweep goes to the follow-up batch."
- R3: "Owner, Nov 5: the old item difficulty scalar is to be retired in the refactor. V4 adds no new reader or writer of it; the landing checks this with a grep of the diff against main and records the result."

R3 grep: `git diff main...HEAD -U0 -- src apps/learnloop-mobile/src migrations`, added lines matching `difficulty` (case-insensitive): only `import learnloop.adaptive_difficulty.reading as reading` (a module path, not the scalar). No new reader or writer of the scalar.

### Commits of the landing

R1 `b1b08138a6`; R2 (b) `6b428a6c66` (pypdfium2 in the mobile extra, lock updated offline); the smoke's finding, its own commit `10b97d1062` (a held-out section's heading was sent as the section's label in `reader.guide_plan` at a phone origin; the label is now `Section N`; test fails before, passes after); merges of main (`5fe3a22558`, then `a525dbcef4`, the latter resolving only generated references and `desktop_validate.py`'s counts, now 325 / 314 / 331).

### Gate (on the tree merged with `a525dbcef4`)

| Step | Result |
|---|---|
| `uv sync --offline --extra dev --extra mobile`, then `uv pip install --offline pypdfium2==5.14.0` | done (sync alone installs 4.30.0 on this machine; see open items) |
| `lint-imports --no-cache` | 43 kept, 0 broken |
| Full pytest (`-n 8`, worksteal, 10G scope) | **30272 passed, 90 skipped, 47 xfailed**, 58m46s |
| Durability lane (`-m durability`) | 409 passed, 1 skipped |
| Owner lane on fresh backup-API copies of `owner-copies-mvp035` | 83 passed, 4 skipped, the 2 known failures (`test_backfill_logs_attempt_duration_interaction_events`, `test_placement_ignores_unanswered_opening_episodes_on_fixture_copies[arxiv_v2]`) |
| Desktop: typecheck, vitest (`--maxWorkers=4`), frontend build | clean; 276 files, 2787 tests passed |
| Phone: typecheck, vitest, build | clean; 29 files, 337 tests passed |
| References | module and desktop generate and validate, `validate_vault.py`: pass (no schema move, no DB reference) |

### Smoke (in-process, fresh copies of the mvp-0.43 backup upgraded on main code to mvp-0.54, on linear_algebra, arxiv_v2 and probability; every AI route refused except in-process fakes)

* Desktop at a `None` origin, main (`a525dbcef4` archive) against the branch: replies byte-identical after id and time renaming on all three copies (41, 117 and 36 steps, 0 diffs).
* Phone Reader: 16 checks, 0 problems on each copy (books, section text, prefetch, page image and its cache, token and cross-vault refusals, shared progress, outbox replay once, Ask and Save, as printed, a plan reading block served on the phone with `plan_reading_ended`).
* Protection: 0 problems on each copy (held-out span, exam-pool source and withheld reading never reach the phone as text, page image, Ask history or display cache; purge on change). The `arxiv_v2` run failed once before the heading fix (`guide_plan`) and passes after.
* `phone_reader` off and a V3 app: the phone behaves as V3 (3 checks, 0 problems, each copy).
* Twin (same reading through the desktop handler and through the phone): dose offers, dose events and the 8 dose rows equal; reading progress equal. The plan composition is not identical between the twins (the phone applies device eligibility, and its reply carries a `device` block), so block ordinals and review-load figures differ; the desktop is deterministic across runs, so this is the phone's filtering. The cause was not isolated further.
* 0 receipts from a real model, no socket connect, no Codex process, every off-allowlist method refused.

### The owner's steps

`uv sync --inexact --extra dev --extra mobile` (new pypdfium2 dependency; `--inexact` because a plain sync in the main checkout uninstalls torch and marker; pypdfium2 stays at 4.30.0), rebuild the PWA, restart the phone host, `learnloop doctor`, Reload the phone app, then P7 and P8 on the iPhone (§6). To turn the feature off: `phone_reader = false` in `mobile.toml`; the phone returns to V3.

### Open items

* The D6 pickup from the desktop's reading sweep goes to the follow-up batch (R2 e).
* R2 (b) narrowed by the orchestrator: the mobile extra says `pypdfium2>=4`, not 5.14.0, because an exact 5.14.0 is unsatisfiable beside the pdf extra (marker-pdf -> pdftext 0.6.3 pins 4.30.0). The lock and the owner's host hold 4.30.0, and the phone's page tests pass under it (49 passed) as under 5.14.0. The gate itself ran under 5.14.0.
* Twin plan composition difference above: the orchestrator compared the twins' plans on linear_algebra, and the 26 plans' blocks (ordinal, lane, action, subtype, status, items) are equal, with no block deferred (`deferredCount` 0). The other plan fields and the other two copies weren't compared, so what differs there is still not isolated. Not a stop condition: doses, rows and progress are equal.
