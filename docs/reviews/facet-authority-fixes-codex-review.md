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
