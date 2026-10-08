# Reader clarification branches

The Reader already saved source-grounded Ask exchanges, but could not distinguish
a follow-up from an unrelated question on the same passage. This slice gives
those exchanges explicit parents and renders the resulting hierarchy in the
existing Ask rail, alongside the source.

## Integration baseline

Checked on October 8, 2026:

- `main`: `472128f527b9b4b02aa6581cc26b4a623870b371`, migration head 158.
- Open draft PR #5, `fix/review-recovery-and-telemetry`:
  `210621a3ad292ed65a7e37dc02cb94912975bdba`, migration head 163.
- This branch is based on PR #5 to retain its Reader lifecycle fixes and React
  test infrastructure. Review it as a stacked change; it does not modify PR #5.
- No SQL migration or new persistence table. The optional parent lives on the
  existing `reader_answer_submitted` interaction-event payload. Existing vaults
  and flat histories need no backfill.

## Behavior and contract

- `reader.ask.parentExchangeId` is the completed **reader-answer event ID**
  returned as `readerAnswerEventId`, not the tutor's `eventId`.
- A null/omitted parent starts a new root with no prior conversation context.
- A follow-up resolves its parent from persisted events in the current vault.
  Its extraction and primary span must match. Missing parents, wrong ID kinds,
  mismatched anchors and cycles fail before logging or model generation.
- The parent's saved selected spans and exact quote override the current UI
  selection. A follow-up refuses to generate if its primary source passage can
  no longer be resolved.
- Only ancestors from the selected branch enter the tutor prompt. Siblings,
  unrelated roots, failed calls, practice answers and learner posteriors do not.
  The latest 12 ancestors are included; the manifest records included IDs and the
  omitted count. All parent links remain in durable history.
- Ask history returns parent IDs and saved selections. Legacy exchanges project
  null parents and remain available as independent roots or follow-up parents.
- The Ask rail supports expanding/collapsing branches, asking from any exchange,
  continuing the latest answer, explicitly starting a new thread, searching
  descendants with their ancestors visible, and returning to source passages or
  validated citations. Starting a follow-up does not move the reading position.
- Failed submissions retain the draft and parent for retry. Replies that finish
  after leaving a source cannot populate a later source view. Completed replies
  remain recoverable through the existing history endpoint.

## Grounding and evidence

The existing tutor source-span allowlist still validates citations. Answers and
selections continue to carry extraction/span identities; ancestry is conversation
context, not an additional source of citation authority. The normal Reader Ask
exposure, reserve invalidation and cold-hint paths remain in use. Reader events
remain `salience_only`, and reader questions still attach no mastery facets or
independent assessment observations.

The graph is independent of retrieval: future cross-source or vault-note
retrieval can extend the validated source manifest while retaining exchange IDs,
parent links and citation identities. This slice does not introduce that
retrieval, cross-extraction parenting, or automatic reanchoring after extraction
replacement.

## Validation

- 123 tests passed across `test_reader_branches.py`, `test_reader_dialogue.py`,
  `test_sidecar_reader.py`, `test_tutor_qa.py`, `test_tutor_citations.py`, and
  `test_salience_firewall.py` before adding the final unavailable-anchor case.
- The final 12 branching tests passed with production SQLite durability enabled
  (`--durable-sqlite`), including the unavailable-anchor case and sidecar
  reinitialization/persistence.
- All 22 React tests passed. The final 9 branching component/screen tests passed
  again after the last UI edits. Coverage includes hierarchy, sibling/deep
  branches, search, legacy/corrupt history readability, anchor navigation,
  inherited submission payloads, remount restoration, retry and stale replies
  after leaving/reopening a source.
- TypeScript check, production frontend build and all six import contracts passed.
  Vite retains its existing large-chunk warning.
- No paid model calls, production vaults, native Tauri launch or full Python suite
  were used. Backend tests ran in an isolated UV environment with the Reader's
  dependencies; the full project sync was blocked by unavailable native
  Manim/Pango build prerequisites. No dependency or lockfile changes are included.

Commands for a normal configured checkout:

```sh
uv run pytest tests/test_reader_branches.py tests/test_reader_dialogue.py tests/test_sidecar_reader.py tests/test_tutor_qa.py tests/test_tutor_citations.py tests/test_salience_firewall.py -q
uv run pytest tests/test_reader_branches.py --durable-sqlite -q
uv run lint-imports --no-cache
npm test --prefix apps/learnloop-tauri
npm run typecheck --prefix apps/learnloop-tauri
npm run frontend:build --prefix apps/learnloop-tauri
```
