# Guide overlay fix: Codex review fixes

**Branch:** `fix/guide-overlay` (worktree `learnanything-guide-fix`, base `main` at
`19798a0c`, not rebased). The review covered the guide-overlay fix (`a18639b2`..`25768bac`,
described in `guide-overlay.md`).

**Codex job:** `~/.cache/codex-agent/jobs/20261012-231031-e7ZzBo`.

**Findings:** one Medium (F1), no High, plus two claims in `guide-overlay.md` that did
not hold. F1 reproduced with a failing Reader test first and is fixed. Both claims are
corrected.

**Paid calls:** none ($0.00); everything ran on fakes, and no copy of an owner vault was
made or needed. **Migration:** none; the schema is unchanged. **Serving, replay,
evidence:** unchanged. The Guide is display: the plan build still writes nothing
(`test_guide_plan_writes_nothing` passes), and the new read touches only
`post_attempt_jobs` and `error_events`. No algorithm successor, config key or defaults
snapshot is involved.

## Review

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Cached Guide plans hide completed diagnoses | fixed | `807cf054` (fail-first `71149d5d`) | `src/screens/ReaderScreen.guide.test.tsx` "a mounted Guide names the diagnoser's statement once the pending diagnosis lands" (fail-first); `src/screens/reader/guidePlan.test.tsx` (6 tests); `tests/test_reader_guidance.py::test_split_guide_plan_names_the_pending_diagnosis_until_it_lands`, `::test_split_guide_plan_waits_on_nothing_once_the_diagnosis_failed`, `::test_split_guide_plan_waits_only_on_diagnoses_behind_its_passages`, `::test_joint_guide_plan_never_waits_on_a_shadow_diagnosis`; `tests/test_sidecar_reader.py::test_reader_guide_plan_rpc_returns_real_section_boundaries` |
| C1 | (claim) | "Fetches the live views … in one query" | fixed (wording) | `807cf054` (docstring); this review commit (`guide-overlay.md`) | It is batched, not one query: the error-event read, a table check, one diagnoses read and one blind-grade read (four statements, as Codex counted). `guide-overlay.md` and the `live_causal_views` docstring now say so |
| C2 | (claim) | "The Guide names the diagnoser's statement after completion" | fixed (by F1) | `807cf054` | True for a fresh plan before the fix, but a mounted Guide kept the error-type fallback. It now holds for the Reader on screen too |

The desktop tests use the real `api` client wrapper and the real query cache, with only
the Tauri transport faked, so invalidations come from the wrappers, not from the tests.
`ReaderScreen.guide.test.tsx` renders the real `ReaderScreen` (only the PDF pane and the
Markdown renderer are stubbed).

### F1: the Guide did not catch up with a pending diagnosis

**Two halves, one reproduced.**

1. **The mounted Guide never refreshed. Reproduced.** The Reader opened a source while the
   diagnosis was pending and showed "Revisit this to resolve: conceptual schema error."
   The fake sidecar then completed the diagnosis. Thirty seconds later the rail still
   showed the error type: the Reader loads the plan once per open and had no reason to
   load it again (fail-first test above).
2. **The cached reopen. Did not reproduce in the Reader, but fixed anyway.** Codex
   reproduced it against the query cache alone, and there the fetch count does stay at 1.
   In the integrated Reader, every open of a real source calls `api.readerDrainOutbox()`.
   That is a Reader mutation (`mutatingReader`), and it marks every `reader:<source>`
   read stale once it settles, success or failure. So the next open re-read the plan even
   before the fix. The two end-to-end tests that pin this ("reopening a cached source
   re-reads a Guide plan that was waiting on a diagnosis", "an attempt submitted
   elsewhere invalidates the cached Guide plan") passed at `71149d5d`. That freshness was
   incidental to the outbox drain, so the plan's own rules now provide it (below), and
   `guidePlan.test.tsx` tests them without the drain.

**Fix (`807cf054`).**

- **The plan says what it is waiting on.** `build_guide_plan` returns
  `pending_diagnosis_attempt_ids`:
  - the attempts behind the LOs of its shown `recent_misunderstanding` passages whose
    live diagnosis is still pending;
  - "pending" is `diagnosis_status`'s rule: an open (queued or leased) `diagnose` job;
  - live jobs only. A shadow diagnosis never lays an overlay, and a failed one never
    will, so a joint vault and a failed diagnosis wait on nothing.

  The repository read is
  `DiagnosisStoreMixin.pending_live_diagnoses_for_active_errors(lo_ids)`: one
  `post_attempt_jobs` ⋈ `error_events` read, with the mode filtered the way
  `diagnosis_status` filters it. The joint parity test still holds: both plans carry the
  same empty list.
- **The Reader re-reads a waiting plan.** `useGuideDiagnosisRefresh`
  (`screens/reader/guidePlan.ts`) re-reads the plan while the list is non-empty.
  - It polls at 4 s, then backs off ×1.5 to a 60 s cap. A diagnosis held up for long
    (provider not ready, budget, kill switch) costs one local plan read a minute while
    the Reader is open.
  - Polls never overlap, and they stop when the list empties, on a source change and on
    unmount.
  - The authoring poll already re-reads the same plan every 4 s, and its comment calls it
    "a cheap local read".
  - It does not call `diagnosis_status`, because that RPC debits the displayed repairs
    once a diagnosis is done.
  - A refresh keeps the authoring poll's rule: it never blanks a complete Guide.
- **A waiting plan is never served from the cache.** `readGuidePlan` re-reads a cached
  plan that lists pending diagnoses instead of serving it, because the diagnosis may have
  landed while no Reader was open.
- **The plan's cache entry carries its learner-state dependencies.** It was tagged only
  `reader:<source>`. It is now also tagged `graph` (mastery, items), `goals` (the active
  goal) and a new `errors` tag ("active error events and the diagnoses laid over them").
  - Attempt mutations (`ATTEMPT_TAGS`) and `add_error_event` invalidate `errors`.
  - The feedback screen's `DiagnosisCard` invalidates `errors` once, when it sees a
    diagnosis land. This also helps a sidecar that predates the pending list.
- **Reusable for RW3a.** The read and the refresh live in `screens/reader/guidePlan.ts`.
  The Reader's per-source cache helper moved verbatim to `screens/reader/readerCache.ts`
  (plus optional tags and `force`). `ReaderScreen.tsx` changes by about 30 lines, which
  keeps the overlap with RW1a's rail split small. RW3a's margin cues read the same plan,
  so they refresh with it.

**No Rust change.** The refresh reuses the existing `reader_guide_plan` command, so no
new Tauri command was needed. While the Rust toolchain on carson is broken (B3; `rustc`
fails with a symbol lookup error), a new command could not have been compiled.

### Observation (not changed)

Because every open drains the outbox through a Reader mutation, the Reader's ten-minute
per-source cache window (`READER_CACHE_MS`) never serves a reopen. In the Reader test
the second open re-fetched the render view, the plan, the progress and the PDF
manifest. The comment above `cachedSourceRead` says a reopen "is served from memory". That is
a performance matter, not a correctness one, and it is outside this stage. It could be
fixed by having the drain invalidate only when it drained or failed something. The
owner's call.

## Gate

Run at `807cf054`; the review commit is documentation only.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 14 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | 8548 passed, 0 failed, 0 skipped (249 s; 8544 before, plus the 4 new Guide tests) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | 93 passed, 8455 deselected, 0 failed (93 s) |
| Frontend: `npm install`, `npm run typecheck`, `npm test` | ok; typecheck clean; 33 files, 160 tests passed |
| `cargo check` | not run: the Rust toolchain on carson is broken (B3), and no Rust file changed |
| DB reference scripts | schema not changed: not run |

## Open questions for the owner

1. **The outbox drain defeats the Reader's per-source cache** (observation above). Leave
   it, or invalidate only when the drain did something?
2. The three questions in `guide-overlay.md` still stand. They are the probe hypothesis
   lane under the split (a serving change that needs a successor), the
   `learnloop misconceptions` CLI, and the `decision_features` receipt.
