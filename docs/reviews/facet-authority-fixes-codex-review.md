# Codex review: the facet authority chokepoint

Stage `facet-authority-fixes`, branch `merge/facet-locks` (main `3192d0c9`
plus `facets/locks-and-depends-on`, merged at `783263ef`; the chokepoint
`10415fdf`, recorded at `dd4e41af`). Owner-directed: facet locks stay removed,
and the exam-authority guarantee must hold without them.

Codex reviewed `783263ef..dd4e41af` (job `20261013-084836-j0SaqX`: source
review and in-memory checks with the real authority and compiler code). It
found four High and two Medium defects: ways exam material, or a citation the
chokepoint never validated, still reached a facet's meaning or its displayed
authority. All six reproduced as failing tests before the fix, and all six are
fixed in `97137de4`. References regenerated in `70effb29`.

- No migration, no config change, no RPC, no frontend or `src-tauri` change.
- No algorithm successor: this is content admission (which facet writes the
  chokepoint accepts, what an undo may restore, what a Library save records).
  Scoring, scheduling, projections and replay are unchanged.
- No paid call.

## Review

### Findings

| ID | Severity | Title | Verdict | Commit | Test (fail-first on `dd4e41af`) |
|---|---|---|---|---|---|
| F1 | High | A refused undo permanently blocks later facet operations | fixed | `97137de4` | `tests/test_facet_authority.py::test_an_ingest_consolidation_keeps_exam_only_meaning_out_and_its_undo_cannot_mint_it` (extended: persisted status, no owner verdict, recovery empty, a Library save runs); `tests/test_facet_authority_review.py::test_recovery_settles_an_undo_intent_the_authority_rule_refuses` |
| F2 | High | An empty `meaning_support` bypasses explicit exam provenance | fixed | `97137de4` | `test_an_empty_meaning_support_never_hides_a_writes_exam_citation[[] / [empty contribution]]`, `test_a_citation_the_write_records_but_its_meaning_support_leaves_out_is_judged_on_its_own`, `test_a_malformed_meaning_support_is_refused[6 shapes]`; guard `test_a_write_whose_meaning_support_declares_its_exam_citation_with_textbook_support_applies` |
| F3 | High | Split units lose their span boundaries and role overrides | fixed | `97137de4` | `test_selecting_one_child_of_a_split_unit_never_selects_its_sibling`, `test_split_children_keep_their_own_role_overrides_in_any_order[4: both orders × implicit/explicit theory role]`, `test_the_writer_refuses_a_reword_citing_the_unselected_half_of_a_split_unit` |
| F4 | High | Re-extraction makes a forbidden exam-facet restoration admissible | fixed | `97137de4` | `test_a_citation_of_an_earlier_extraction_of_a_member_revision_keeps_its_role`, `test_a_re_extraction_never_makes_an_exam_only_restoration_admissible`, `test_an_undo_never_mints_a_candidate_whose_recorded_citations_no_longer_resolve` |
| F5 | Medium | Unresolved citations become current semantic-authority links | fixed | `97137de4` | `test_a_citation_that_does_not_resolve_never_becomes_a_semantic_authority_link` |
| F6 | Medium | The manual-authority exception lacks complete audit records | fixed | `97137de4` | `test_every_library_change_to_a_facets_meaning_records_the_owners_authority_verdict`, `test_a_library_save_that_never_lands_withdraws_its_authority_verdicts`, `test_recovery_withdraws_the_verdicts_of_a_library_save_killed_before_its_write`, `test_the_registry_writer_refuses_an_owner_edit_with_no_audit_record` |

Tests in the `test_…` cells without a file are in
`tests/test_facet_authority_review.py`.

**Fail-first.** The tests were written and run before the fix, then again
against `dd4e41af`'s `src/` and `migrations/` (a `git archive` copy under
`fixtures-local/tmp`, with `-o pythonpath=` pointing at it, since
`pyproject.toml` puts `src` first): **25 failed, 1 passed**. The one that
passes is the guard (a write that declares its exam citation beside a
textbook one applies, before and after). Each failure is the defect, not a
setup error:

- **F1**: the refused undo left the row `undoing` (`assert 'undoing' ==
  'proposed'`); recovery of an `undoing` intent raised the same
  `exam_authority` refusal it would raise on every later operation.
- **F2**: `meaning_support: []` and `[{"from", "citations": []}]` beside an
  exam-only provenance ref applied (`DID NOT RAISE`); so did a declared
  textbook contribution beside an undeclared exam ref, and all six malformed
  shapes.
- **F3**: with only `chapter#Theory` selected, the exam half (`s2`) resolved
  as `primary_textbook` under `chapter#Theory`; with both children selected
  and overridden, the role of `s2` depended on scope order (`exam` or
  `primary_textbook`) and the theory half could resolve as `exam`; the reword
  citing `s2` under `chapter#Theory` applied.
- **F4**: after a second extraction of `rev_exam`, `ext_exam:s1` gave
  `CitationProblem('extraction run ext_exam is not in the source set')`, and
  the undo minted the exam-only candidate (`DID NOT RAISE`); with the exam
  member removed from the set, the undo minted it too.
- **F5**: the facet citing an unselected span got a `current` link row with
  relation `primary`.
- **F6**: no `MANUAL_AUTHORITY_TASK`, no verdict rows; `OwnerEdit("")` was
  accepted.

On the fix all 26 pass.

### What changed

**F1. Undo checks before it records; recovery settles a refusal.**
- `authority.check_registry_text` is the decision `write_registry_text`
  makes, without writing. `undo_action` builds the restoration
  (`_restoration`: text, basis, resolver) and checks it **before**
  `_record_undo_intent`. A refused undo raises (`FacetAuthorityRefusal`, a
  `FacetIdentityActionError` carrying the chokepoint's code) and records
  nothing: no `undoing` row, no owner verdict.
- `recover_interrupted_actions` no longer retries a write the chokepoint
  refuses. An `undoing` row returns to `applied`, with
  `undo_detail.refused = {code, message, at}` beside the intent's
  `requested_at` and `owner_judgment_ids` (the ledger is append-only, so those
  verdicts stay and are named). An `applying` merge is withdrawn
  (`abandoned`). The outcome row carries `refused` and `refusal`, not
  `problem`, so `doctor --fix-state` reports it as finished ("refused by the
  meaning-authority check: …") and the sidecar logs it. Every later merge,
  undo and Library save runs.

**F2. `meaning_support` is parsed strictly and reconciled with the write.**
- `contributions_from_support` refuses bookkeeping that is not a list of
  contributions (`{"from", "citations": [...]}`) or citations, each naming a
  span (`invalid_meaning_support`, surfaced as a `PatchApplicationError`
  naming `meaning_support`). Nothing malformed is read as "no support".
- `write_contributions`: each declared contribution is judged on its own, and
  a block-span ref the write records that no declared contribution cites is
  one more contribution (`provenance`), judged on its own. So `[]` beside an
  exam ref is an exam-only contribution (refused), and a declared textbook
  span never corroborates an exam ref it does not name. A genuinely uncited
  new facet (no refs, no declared citations) is still admitted for review,
  the accepted default.

**F3. A split child is its own spans and its own role.**
- `source_unit_selection.effective_unit_spans` (from the same walk as
  `compute_effective_units`, which now delegates to it) gives each effective
  unit the spans it holds: a split child only the blocks under its heading, a
  merge its members' spans. The RPC shape of `compute_effective_units` is
  unchanged.
- The resolver judges a cited unit, and the selected scope, by the spans each
  holds. A span's role comes from each scope entry that holds it (its
  `role_override`, else the member's role); when several entries or members
  hold it, the least authoritative role wins, whatever their order.

**F4. An extraction resolves through its revision; recorded citations must
resolve.**
- The resolver keeps every member (also one with no extraction yet) and
  resolves a citation's extraction through `get_extraction_run(...).revision_id`
  when it is not the member revision's latest extraction. A re-extraction of a
  pinned revision no longer orphans its earlier citations: they keep the
  member's role and scope, against the earlier extraction's own units.
- `check_meaning_write(require_resolved=True)` refuses
  (`unresolved_citation`) when a recorded citation does not resolve, instead
  of treating the contribution as uncited. The registry writer's `Cited` basis
  (an undo restoring a never-registered candidate on its own citations)
  requires it.

**F5. An unvalidated ref never links.**
- `written_provenance` marks every new ref with a locator that it cannot
  validate (a block span that does not resolve, a non-block-span locator, or
  no source set) `role: unresolved`; the YAML snapshot keeps it as a record
  of what was cited.
- `added_provenance` (the `link_payload` that becomes `entity_source_links`
  rows) leaves those out. A `current` `primary` link, and so
  `get_entity_provenance(...)["semantic_authority"]`, only ever comes from a
  validated citation.

**F6. Every manual-authority change is an owner verdict.**
- `save_registry_text` appends, for every facet whose `AUTHORITY_FIELDS` the
  save changes (a new facet, a worked example and a title included), the
  owner's `granted` verdict in `judgment_ledger`: task
  `facet_manual_authority`, `left = facet:<id>`, `right =
  facet_wording:<hash of its meaning>`, `judge = owner`, `created_at`, and a
  rationale with `actor`, `granted_at`, `save_id`, `scope = {facet_id, fields,
  new_facet}` and the reason (ingestion §4.2).
- The verdicts commit with the write-ahead intent (before the file write). If
  the write fails they are superseded by `withdrawn` verdicts; if the process
  stops first, recovery withdraws them when it abandons the save's reword
  (each reword's `detail.authority_judgment_ids` lists the save's verdicts;
  `detail.authority_judgment_id` names its own).
- `OwnerEdit(judgment_id)` must name its verdict; the registry writer refuses
  an owner edit without one (`unaudited`).
- Which edits are versions is unchanged (`MEANING_FIELDS`): an example-only
  edit or a new facet gets a verdict but no reword action.

## Behaviour the owner will notice

- **A refused undo no longer wedges the vault.** Undoing an exam-only alias
  join (or a candidate whose citations no longer resolve) is refused up front
  and leaves nothing in flight. A vault that already has such an `undoing`
  row is settled the next time any facet operation, the sidecar or
  `doctor --fix-state` runs recovery; doctor lists it as finished with the
  refusal.
- **A pending proposal whose facet payload has malformed `meaning_support`**,
  or records an exam span its `meaning_support` does not name, is refused at
  accept with a message naming the facet. Producers in this branch always
  declare every span they record, so a fresh run is not affected.
- **A split chapter's halves are separate.** Selecting `chapter#Theory` no
  longer lets a citation of the other half count, and `chapter#Exam` with
  `role_override: exam` stays exam material whatever the scope order.
- **Undoing a consolidation after a re-extraction** judges the candidate's
  exam citation as exam; after its source left the set, the undo is refused
  (`unresolved_citation`) rather than minting the candidate as uncited.
- **The provenance view** no longer shows a citation outside the selected
  units as a facet's semantic authority.
- **Library saves** add one owner verdict per facet whose meaning changed;
  nothing else about saving changes.

## Gate

Run on `70effb29` (the fix and the references; only this file changed after),
2026-10-13, with `TMPDIR` set to the worktree's `fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (163 packages resolved) |
| `uv run lint-imports --no-cache` | 15 contracts kept, 0 broken |
| Fail-first: the 26 tests against `dd4e41af`'s `src/` | 25 failed, 1 passed (the guard) |
| Targeted (before the doctor/sidecar reporting change) | facet, synthesis, append, apply, provenance, registry, leakage and architecture suites: 431 passed; source, unit, ingest and inventory suites (44 files): 555 passed |
| Targeted (on `97137de4`) | `tests/test_facet_*.py`, doctor, effective units, apply write-ahead, provenance, sidecar registry, judgment ledger: 310 passed |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **9,140 passed**, 0 failed, 0 skipped, 46 warnings (the existing fork and deprecation warnings), 324 s (lock wait 09:39 to 09:43); 9,115 at `dd4e41af` plus the 25 new tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **95 passed**, 9,045 deselected, 1 warning, 96 s |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated (`70effb29`: two-line shifts of the config citations into `learnloop_sidecar/context.py` and `ops/doctor.py`, `source_commit` stamps); `errors: []` |
| `validate_vault.py` | passed (1,085 notes, 21,864 wikilinks/fragments, 4,478 source paths) |
| `module_validate.py` | wikilinks 14,712/14,712, source/test links 11,795/11,795, catalog YAML 508/508; its 539 "missing expected note" issues (module coverage 474/735) are the same before the change (checked on `dd4e41af`'s tree) |
| Frontend, `src-tauri`, schema, config | unchanged (no npm, cargo or migration step needed) |

## Paid calls

None. Cost $0. Every test uses fakes; no command ran against a vault, and the
tracked fixture vaults were not opened.

## Open questions for the owner

1. **Synthesis inputs for a split child.** The resolver now treats
   `chapter#Theory` and `chapter#Exam` as separate units, so authority holds
   at every citation. Synthesis's input side (`effective_scope_groups`) still
   expands a selected split child to its raw parent with the parent's role,
   so the model can be shown the other half's inventory. Its citations of that
   half are refused or judged as exam now; making the input side split-aware
   is a separate synthesis change. Build it?
2. **A Library save stopped between its intent and its write, with no
   reword.** Its `granted` verdicts (new facets or example-only edits) stay,
   naming a wording the registry never showed: recovery withdraws a save's
   verdicts only through its reword rows. A save with any reword, and every
   in-process failure, withdraws them. Recommended default: leave it (the
   window is one DB commit to one atomic rename, and the verdict is audit
   only, never read as authority).
3. **Unresolved citations in a proposal.** An undo's recorded citations must
   resolve; a proposal's new facet whose only citations do not resolve is
   still admitted for review as uncited (the accepted default), and its
   citations never link or support. Should a proposal be strict too?
4. **Owner verdicts of a settled undo.** An `undoing` row recorded before this
   fix carries the owner's `different` verdicts; settling it keeps them (the
   ledger is append-only) and names them beside the refusal. A later dedupe
   will therefore not re-merge that pair. Recommended default: keep them (the
   owner did judge them different).

## Files

- **Changed, Python:** `content/facet_identity/authority.py` (resolver,
  strict `meaning_support`, reconciliation, `require_resolved`, unvalidated
  refs, `check_registry_text`, audited `OwnerEdit`);
  `content/facet_identity/actions.py` (undo pre-check, refusal settling,
  owner verdicts); `content/proposals/patches.py` (malformed bookkeeping
  refused); `content/synthesis/source_unit_selection.py`
  (`effective_unit_spans`); `ops/doctor.py`, `learnloop_sidecar/context.py`
  (report a settled refusal).
- **Tests:** new `tests/test_facet_authority_review.py` (25); extended
  `tests/test_facet_authority.py` (the consolidation-undo test, and its setup
  as `_exam_alias_consolidation`).
- **Docs:** `spec_source_ingestion_v2.md` §4.3 and §8.7,
  `spec_knowledge_model.md` §3.4; the regenerated architecture references;
  this file.
- **Fixtures:** none touched. `fixtures/linear_algebra`, `probability` and
  `arxiv_v2` were not opened.

## Re-review 2

Codex re-reviewed the fixes after `dd4e41af` (`97137de4`, references
`70effb29`, record `ddf941d5`; job `20261013-095625-XzqNgm`). Verdict
REOPENED: F1, F3, F4, F5 and F6 confirmed fixed, F2 not clean (a reopened
variant), and one new finding, F7, in F6's audit mechanism. Both reproduced
fail-first and both are fixed in `cc30ebb8`; references regenerated in
`de4b02d9`. Facet locks stay removed.

- One migration (186, `facet_registry_saves`, WORKFLOW) and a new head
  fixture; no config change, no RPC shape change (a Library save's result
  gains `save_id`; the sidecar reads only `text`), no frontend or
  `src-tauri` change.
- No algorithm successor: content admission and a Library save's write-ahead
  bookkeeping. Scoring, scheduling, projections and replay are unchanged.
- No paid call.

### Findings

| ID | Severity | Title | Verdict | Commit | Test (fail-first on `ddf941d5`) or reason |
|---|---|---|---|---|---|
| F1 | High | A refused undo permanently blocks later facet operations | confirmed fixed by Codex | `97137de4` | no action |
| F2 | High | `meaning_support` coverage counted a declared citation before validating its unit (reopened) | fixed | `cc30ebb8` | `tests/test_facet_authority_rereview.py::test_a_declared_citation_that_does_not_resolve_never_hides_the_writes_exam_ref[chapter#Theory / chapter#Nowhere]`, `::test_a_declared_citation_covers_a_recorded_span_only_when_it_resolves`; guard `::test_a_write_declaring_both_halves_of_a_split_unit_under_their_own_units_applies` |
| F3 | High | Split units lose their span boundaries and role overrides | confirmed fixed by Codex | `97137de4` | no action |
| F4 | High | Re-extraction makes a forbidden exam-facet restoration admissible | confirmed fixed by Codex | `97137de4` | no action |
| F5 | Medium | Unresolved citations become current semantic-authority links | confirmed fixed by Codex | `97137de4` | no action |
| F6 | Medium | The manual-authority exception lacks complete audit records | confirmed fixed by Codex for successful saves; its durability gap is F7 | `97137de4` | no action beyond F7 |
| F7 | Medium | Interrupted saves without rewords leave permanent authority grants | fixed | `cc30ebb8` | `tests/test_facet_authority_rereview.py::test_recovery_withdraws_the_verdict_of_a_save_killed_before_its_write[new_facet_only / example_only / claim_edit]`, `::test_recovery_keeps_the_verdict_of_a_save_killed_after_its_write[3 edits]`, `::test_a_save_that_fails_in_process_settles_its_intent`, `::test_a_save_that_lands_records_a_settled_intent`, `::test_doctor_reports_and_settles_an_interrupted_save_with_no_reword`, `::test_a_save_intent_has_a_closed_lifecycle` |

Nothing was rejected.

**Reproduction.** Both scenarios were reproduced on `ddf941d5` before any
change:

- **F2**: a split chapter with `chapter#Theory` (textbook) and `chapter#Exam`
  (`role_override: exam`) both selected; a new facet whose provenance records
  the exam half `ext_split/s2` and whose `meaning_support` declares
  `ext_split/s2` under `chapter#Theory` (or under a unit that does not exist)
  applied (`DID NOT RAISE`). The declaration fails resolution ("span s2 is not
  in unit chapter#Theory"), yet its `(extraction_id, span_id)` marked the
  recorded ref as covered, so the exam ref was never judged and the facet
  compiled as `new_unsupported`.
- **F7**: a Library save killed (a `BaseException` from `_write_registry`)
  after its verdicts committed: for a new-facet-only and an example-only save,
  `recover_interrupted_actions` returned `[]` and the ledger kept
  `['granted']`; the claim-edit control returned
  `[('applying', 'abandoned')]` with `['granted', 'withdrawn']`, as Codex
  described.

**Fail-first.** The 14 tests in `tests/test_facet_authority_rereview.py`, run
against `ddf941d5`'s `src/` and `migrations/` (a `git archive` copy under
`fixtures-local/tmp`, `-o pythonpath=` pointing at it): **13 failed, 1
passed** (the guard: both halves declared under their own units apply,
before and after). The failures: F2's two scenarios `DID NOT RAISE`; F2's
unit test has no `resolver` argument to give; F7's six kill tests find no
`library_save` recovery row (`StopIteration`; for the before-write
new-facet and example cases this is the defect: nothing recovers and the
verdict stays `granted`); doctor reports nothing in flight; the intent and
lifecycle tests find no save intent API. On the fix all 14 pass.

### What changed

**F2. A declared citation covers a recorded span only when it resolves.**
- `authority.write_contributions(payload, before, after, resolver)`: a
  recorded block-span ref is left out of the extra `provenance` contribution
  only when a declared citation that **resolves** in the proposal's resolver
  names the same span. A declared citation that does not resolve (its unit
  does not hold the span, the unit does not exist, the span is outside the
  selected units, the extraction is not in the source set) supports nothing
  and covers nothing, so the write's own exam ref is judged on its own:
  exam-only, refused (`exam_authority`). Without a resolver nothing covers.
- A resolved declared citation of a span has the span's role (the resolver
  decides a role from the scope entries that hold the span, never from the
  unit the citation names), so coverage never changes what a span is.
- `patches._compile_facet` passes `facet_authority.resolver`. The undo path
  (`_restore_basis`) is unchanged: a registry entry carries no
  `meaning_support`, so all its refs are one contribution and must resolve.

**F7. Every Library save with verdicts is a recoverable intent.**
- Migration 186 adds `facet_registry_saves` (WORKFLOW): `id` (the save id the
  verdicts' rationale carries), `status` (`applying`, `applied`,
  `abandoned`), `facets_json` (per facet: the wording key before, or null
  for a new facet, the wording key after, which is the verdict's
  `right_id`, and the fields), `judgment_ids_json`, `action_ids_json`,
  `applied_at`, `abandoned_at`, `settle_detail_json`.
- `save_registry_text` records the intent in the same write-ahead
  transaction as the owner's verdicts and the `applying` rewords, whenever
  there are verdicts (a new facet or an example-only edit included). The
  intent owns the verdicts: a reword row now carries `detail.save_id` (and
  its own `authority_judgment_id`) instead of the list of the save's
  verdicts. On success the rewords and the intent become `applied` together;
  an in-process write failure abandons both and withdraws the verdicts once.
- `recover_interrupted_actions` settles each `applying` intent first
  (`registry_save_state`): the file is replaced atomically, so one facet
  showing the wording its verdict names proves the save landed (derived
  state refreshed, `applied`, verdicts stand); every facet as before (a new
  facet absent) or edited since is not proof, so the verdicts are
  `withdrawn` and the intent `abandoned` with the reason, the file state and
  the withdrawn ids. Its outcome rows carry `kind: "library_save"`. Rewords
  settle as before, from their own facet. A reword recorded by `97137de4`'s
  code (no intent, a `detail.authority_judgment_ids` list) still withdraws
  its save's verdicts when abandoned.
- `doctor` counts interrupted saves with the in-flight actions
  (`facet_identity:interrupted`), and `--fix-state` reports a settled save
  ("Library save … (applying -> abandoned; 1 owner verdict(s) withdrawn)").
- Head fixture `migration_head_185` → `migration_head_186`: a backup-API copy
  with only 186 applied (checkpointed, `journal_mode=DELETE`,
  `integrity_check` ok, `foreign_key_check` clean, no `-wal`/`-shm`). README,
  `SCHEMA_HEAD` and every hard-coded head path (12 tests, both reference
  scripts) point at 186; `test_facet_rewords_migration` pins its 184 → 185
  upgrade to migrations through 185.

**Merge note.** main's head is now `185_reader_authored_question_scopes`
(RW1a, merged after this branch was cut), so this branch's
`185_facet_identity_rewords` and `186_facet_registry_saves` renumber to 186
and 187 when `merge/facet-locks` lands on main, with the head fixture rebuilt
from main's head the same way.

### Behaviour the owner will notice

- **A misdeclared citation no longer hides exam material.** A proposal whose
  facet cites the exam half of a split chapter under the theory half (or
  under a unit that does not exist) is refused at accept with the
  exam-authority message, instead of applying as uncited.
- **A Library save stopped mid-write leaves no standing verdict.** The next
  facet operation, sidecar open or `doctor --fix-state` withdraws the
  verdicts of a save the registry never showed, a new facet or an
  example-only edit included, and keeps them when the edit did land. Doctor
  lists such a save as in flight until then.
- Open question 2 of the first re-review (leave the reword-less window) is
  closed by F7: there is no such window now.

### Gate

Run on `de4b02d9` (the fix and the references; only this file changed
after), 2026-10-13, with `TMPDIR` set to the worktree's `fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (163 packages resolved; pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 15 contracts kept, 0 broken |
| Fail-first: `tests/test_facet_authority_rereview.py` against `ddf941d5`'s `src/` and `migrations/` | 13 failed, 1 passed (the guard) |
| Targeted (before the commit) | 62 facet, proposal, synthesis, append, library, doctor, migration, upgrade, apply, provenance, registry, unit-selection, judgment and fixture suites: 802 passed, 1 failed (`test_facet_reword_paths.py::test_a_library_reword_interrupted_after_the_write_is_finished_by_recovery`, which expected one recovery row; updated to the save and its reword), then 25/25 in that file |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **9,154 passed**, 0 failed, 0 skipped, 46 warnings (the existing fork and deprecation warnings), 345 s (lock taken at once, 10:25:07); 9,140 at `ddf941d5` plus the 14 new tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **95 passed**, 9,059 deselected, 1 warning, 96 s |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated (`de4b02d9`: schema head 186, the new `facet_registry_saves` table note, `source_commit` stamps); `errors: []`, 309 table notes, role counts workflow 77 |
| `validate_vault.py` | passed (1,086 notes, 21,874 wikilinks/fragments, 4,482 source paths) |
| `module_validate.py` | wikilinks 14,712/14,712, source/test links 11,795/11,795, catalog YAML 508/508; the 539 "missing expected note" issues are the same as at `ddf941d5` |
| Frontend, `src-tauri`, config | unchanged (no npm or cargo step needed) |
| Tracked fixture vaults | untouched; `git status` clean after the full suite and the durability lane |

### Paid calls

None. Cost $0. Every test uses fakes; no command ran against a vault, and the
tracked fixture vaults (`fixtures/linear_algebra`, `probability`,
`arxiv_v2`) were not opened.

### Files

- **Changed, Python:** `content/facet_identity/authority.py`
  (`write_contributions` validates coverage); `content/proposals/patches.py`
  (passes the resolver); `content/facet_identity/actions.py` (save intents,
  `registry_save_state`, recovery, `wording_key`);
  `db/stores/facet_identity.py` (save intent rows); `db/table_roles.py`;
  `ops/doctor.py`.
- **Schema:** `migrations/186_facet_registry_saves.sql`;
  `fixtures/migration_head_186/` (renamed from 185, README).
- **Tests:** new `tests/test_facet_authority_rereview.py` (14); updated
  `tests/test_facet_authority_review.py` and `tests/test_facet_reword_paths.py`
  (a killed save now recovers as two rows, the save and its reword),
  `tests/test_facet_rewords_migration.py`, and the 12 head-fixture paths.
- **Docs:** `spec_source_ingestion_v2.md` §8.7; the regenerated architecture
  references; this file.
- **Fixtures:** only the migration-head fixture. `fixtures/linear_algebra`,
  `probability` and `arxiv_v2` were not opened.
