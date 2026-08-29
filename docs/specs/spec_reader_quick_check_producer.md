# Reader quick-check producer (minimal slice)

Status: implemented alongside this spec.
Scope: the missing *producer* for section-boundary quick checks in the Reader.
The consumer chain (guide plan → boundary card → present/submit/dispositions)
shipped with P2/P3; until now the only writer of question placements was the
golden-path fixture, so real vaults never saw a quick check.

## Contract

1. **Trigger.** When the learner is in `anchor` mode ("read closely") with
   section prompts on — the same `boundaryChecksAvailable` gate that already
   controls quick-check display — and their reading position crosses the tail
   of a section that has no question (owner-reviewed or authored), the Reader
   fires `reader.author_section_question`. The reading hot path never blocks on
   a model: the RPC only enqueues a durable job and returns.
2. **Producer.** A new `reader_quick_check` job on the existing durable ingest
   queue (drained by the sidecar's background thread at quick-add priority).
   The handler loads the section's readable IR blocks, calls a new
   span-grounded codex task (`run_reading_quick_check`, getattr-discovered),
   validates every cited span id against the provided set in code, and inserts
   one row into `reader_authored_questions` (migration 105), status `proposed`.
3. **Consumer.** `build_guide_plan` fills sections that lack an owner-reviewed
   placement with the section's latest `proposed` authored question, marked
   `placement: "auto_authored"`. Owner-reviewed placements always win; the two
   sources never blend within a section. The Reader polls the guide plan while
   an authoring request is in flight and shows the boundary card exactly as it
   does for owner-placed questions.
4. **Answering (evidence honesty).** An auto-authored question has no practice
   item, no surface, and no administration. Answering it is a formative
   self-check: the learner writes an answer, the expected answer is revealed
   for comparison, and the row records `response_md`/`answered_at`. Nothing
   touches attempts, mastery, or certification — statuses live on the row
   (`proposed → answered | dismissed | escalated`), not on new
   interaction-event kinds.
5. **Escalation to a PI (Matuschak reader-control).** "Add to practice" calls
   `reader.escalate_authored_question`, which mints a real PracticeItem via the
   learner-authority authoring path (no review gate): provenance
   `origin="codex_proposal"` with `span:<extraction_id>/<span_id>` source
   refs, a plain correctness rubric, and the learning object the learner
   confirms (the guide plan suggests the section's top-passage LO). The row
   flips to `escalated` and carries the `practice_item_id`; the sidecar
   reloads the vault so the new card schedules immediately.
6. **Suppression.** "Don't bring this back" flips the row to `dismissed`;
   authoring is idempotent per (extraction, section, prompt version), so a
   dismissed section is never re-authored and a `proposed` row is reused
   instead of re-generating.

## Non-goals (deferred)

- No ask-now density policy: at most one authored question per section, only
  in anchor mode, only on learner approach.
- No grading of the self-check answer (no LLM call on submit).
- No depth-envelope integration yet; escalation is the learner's explicit act.
- Owner review UI for authored questions (they are visible, dismissable
  artifacts, which is the P2-era review affordance for learner-owned items).

## Touched pieces

- `migrations/105_reader_authored_questions.sql` — new table.
- `codex/{schemas,prompts,client}.py` — `ReadingQuickCheck` task (SDK-only,
  getattr tier, span-grounded, untrusted-text framing).
- `db/repositories.py` — insert/get/list/status methods.
- `services/reader_quick_check.py` — section blocks, generation + span
  validation, actions, escalation.
- `services/ingest_runner.py` — `handle_reader_quick_check` + client seam.
- `learnloop_sidecar/ingest_jobs.py` — `enqueue_reader_quick_check`.
- `learnloop_sidecar/handlers/reader.py` — `reader.author_section_question`,
  `reader.authored_question_action`, `reader.escalate_authored_question`.
- Tauri passthroughs + `client.ts`/`dto.ts` + `ReaderScreen.tsx` trigger,
  card branch, and escalate action.
