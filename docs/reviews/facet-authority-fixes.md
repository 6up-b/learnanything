# Facet authority fixes: exam authority enforced once, where a facet's meaning is written

Stage `facet-authority-fixes`, branch `merge/facet-locks` (main `3192d0c9` plus
`facets/locks-and-depends-on`, merge recorded at `783263ef`). Owner-directed:
facet locks stay removed, and the exam-authority guarantee must hold without
them.

The facet-locks branch fixed F6 (an append facet reword bypassed
`exam_authority`) for the reword lane only. An independent read-only Codex
verification (job `20261013-055453-vZTyoZ`, against `8711beb9`) reopened F6
with four High and three Medium findings: exam-only material could still
change a facet's meaning by other routes. This stage closes them with one
chokepoint and records every facet write path against it.

- Fix: `10415fdf`. References regenerated: `b2c14e49`.
- No migration, no config change, no RPC, no frontend or `src-tauri` change.
- No algorithm successor: this is a content path (which facet writes are
  admitted). Scoring, scheduling, projection and replay are unchanged.
- No paid call.

## 1. Findings

| # | Severity | Finding (Codex) | Verdict | Fail-first tests (`tests/test_facet_authority.py`) |
|---|---|---|---|---|
| 1 | High | An uncited `create` carrying a registered facet's id overwrites it (append, bootstrap, the proposal writer) | fixed | `test_an_uncited_append_facet_carrying_a_registered_id_never_rewrites_it`, `test_a_bootstrap_candidate_carrying_a_registered_id_cannot_reword_it_uncited`, `test_a_cited_bootstrap_candidate_carrying_a_registered_id_rewords_it_as_a_checked_update`, `test_a_proposal_create_over_a_registered_facet_needs_explanatory_support` |
| 2 | High | A non-explanatory second citation (`notes`) defeats the `exam_authority` hard fail | fixed | `test_a_notes_citation_never_corroborates_exam_material_at_the_gate`, `test_an_exam_and_notes_reword_hard_fails_exam_authority`, `test_the_writer_refuses_a_reword_supported_by_exam_and_notes_only` |
| 3 | High | A unit with `role_override: exam` inside a `primary_textbook` extraction counts as textbook support | fixed | `test_an_exam_override_inside_a_textbook_extraction_is_exam_material`, `test_citations_take_the_units_role_override`, `test_the_writer_refuses_a_reword_citing_an_exam_override_only` |
| 4 | High | Identity consolidation merges an exam-only candidate into a textbook one and keeps its meaning; an in-run `absorb_as=precondition` moves the exam claim into the survivor; the merged YAML records the exam span as support | fixed | `test_consolidation_never_carries_exam_only_meaning_into_a_survivor[merge-None, absorb-precondition, absorb-example]`, `test_the_writer_refuses_a_new_facet_one_of_whose_contributions_is_exam_only`, `test_an_ingest_consolidation_keeps_exam_only_meaning_out_and_its_undo_cannot_mint_it`; guard `test_a_survivor_that_only_exam_material_supports_still_fails_after_consolidation` |
| 5 | Medium | The persisted locator can name a different span from the validated ids | fixed | `test_a_citations_locator_is_derived_from_its_validated_ids`, `test_the_writer_judges_a_persisted_citation_by_the_span_its_locator_names` |
| 6 | Medium | Citation resolution enforces neither the selected scope nor span-to-unit membership; an unselected span counts as corroboration | fixed | `test_a_reword_citing_a_span_outside_its_unit_is_dropped`, `test_an_unselected_span_never_corroborates_exam_material`, `test_a_provenance_link_to_an_unselected_unit_is_dropped`, `test_the_writer_refuses_a_reword_whose_only_support_is_unselected` |
| 7 | Medium | Duplicate facet ids in a Library save get separate rewords against one snapshot; loader and undo disagree | fixed | `test_a_library_save_listing_a_facet_twice_is_refused_and_writes_nothing` |
| — | — | A new write path must not bypass the chokepoint | added | `test_the_registry_writer_refuses_exam_only_meaning_whatever_the_caller_declares`, `test_a_facet_write_compiled_without_the_authority_context_is_refused`, `test_every_writer_of_facet_meaning_goes_through_the_authority_chokepoint` |

**Fail-first.** 25 of the tests were written and run before the fix (24
failed in place; the guard passed). The end-to-end consolidation and undo test
was added while implementing it. All 26 were then run against `783263ef`'s
`src/` and `migrations/` (a `git archive` copy under `fixtures-local/tmp`,
`-o pythonpath=` pointing at it; the structural test parses the imported
package's tree): **25 failed, 1 passed**. The one that passes is the guard (a
survivor whose own support is only exam material hard-fails before and after
consolidation). Each failure is the behaviour the finding describes, not a
setup error:

- 1: the exam append's row for `facet_symmetry_definition` carries the exam
  claim, and accepting it overwrites the facet; the direct `create` proposal
  applies (`DID NOT RAISE`).
- 2: `{exam, notes}` gives no `exam_authority` diagnostic; the append run is
  not blocked; the writer applies.
- 3: `_span_refs` reports `primary_textbook` for the overridden unit; the run
  is not blocked.
- 4: the survivor's preconditions or examples carry the exam text, the gates
  pass, and the exam ref is recorded with relation `primary`.
- 5: the recorded locator is `span:ext_exam/s1` for ids `ext_text/s1`; the
  spoofed create applies.
- 6: the reword citing `s2` under unit `two_selected` persists; the
  unselected span corroborates; `_span_problem` returns `None`.
- 7: the save is written with two entries and two reword actions.
- Chokepoint: `facet_identity.authority` does not exist; a facet item compiles
  without any check; `actions.py` writes `facets.yaml` itself.

On the fix all 26 pass.

## 2. Design: one chokepoint

`src/learnloop/content/facet_identity/authority.py` is the one place exam
authority is decided for a facet. Everything else either calls it or is
refused by it.

**A facet's meaning** is `AUTHORITY_FIELDS`: `kind`, `title`, `claim`,
`description`, `preconditions`, `postconditions`, `applicability`, `non_goals`,
`positive_examples`, `negative_examples`. `MEANING_FIELDS` (what writes a
version) is a subset. Growing examples is meaning for authority but still not a
new version. Aliases, error signatures, repairs, provenance, status and
version are not meaning.

**Citations are resolved from their ids, never from the producer's claims**
(`CitationResolver`):

1. The extraction run must belong to a source-set member.
2. The span must resolve in that run's document.
3. A cited unit must contain the span (raw or effective unit ids).
4. The span's unit must be in the member's selected scope. An empty scope means
   the whole artifact.
5. The role is that unit's `role_override` when the scope gives one, else the
   member's `default_role`. When several members select the unit, the least
   authoritative role wins (exam, then non-semantic roles, then explanatory).
6. An exam citation's relation is `assessment_alignment`.
7. The locator is `format_block_span(extraction_id, span_id)`.

The run's own resolver lives on `_SynthesisInputs.resolver`. At apply, the
resolver uses the proposal's source set (patch → agent run → synthesis run →
manifest), or every source set of the vault when the proposal has none.

**One rule** (`role_authority.support_verdict`, also used by the §8.7 gates):

- `explanatory`: at least one explanatory citation (primary textbook, lecture,
  paper, reference or alternate explanation) with relation primary, support or
  alternate.
- `exam_uncorroborated`: exam material and no explanatory citation. Notes,
  problem-set, unknown or unresolved citations never corroborate.
- `unsupported`: everything else.

**`check_meaning_write`** judges each *contribution* to a change separately:
the candidate itself, each candidate a consolidation joined to it, a reword,
an absorbed example.

- A **registered** facet's meaning changes only when every contribution is
  `explanatory`. An uncited or exam-only change is refused (`unsupported_reword`
  or `exam_authority`).
- A **new** facet may carry no `exam_uncorroborated` contribution. An uncited
  new facet stays what it was: a proposal the `adequate_provenance` gate sends
  to review.

**Writers.**

- `patches._compile_facet` calls `check_meaning_write` for every facet item
  through a `ProposalAuthority` context. Without that context it refuses. The
  context comes from the proposal's `meaning_support` (the citations by id,
  one entry per contribution); without one, from the block-span refs the write
  adds, resolved by their locator.
- `written_provenance` re-derives every ref a write adds from the span its
  locator names, and the entity's source links are written from those refs
  (`CompiledPatch.link_payload`).
- `_apply_accepted_locked` then calls `verify_registry_transition`: the staged
  `facets.yaml` may change no facet's meaning that a checked item did not
  write. This also covers any other compiled writer that might touch the file.
- `write_registry_text` is the one writer for everything else. It diffs the
  new text against the file and requires, for each facet whose meaning
  changes, a basis it verifies itself:
  - `Cited`: judged as above, with a resolver required;
  - `RegisteredMerge`: the union of registered facets, recomputed with
    `merged_survivor`;
  - `Restore`: equal to an entry the action recorded;
  - `OwnerEdit`: the owner's Library save, the explicit, audited manual
    authority, recorded as a `reword` action with an undo.

  It also refuses a facet id listed twice.
- `join_candidate` is how a merge or absorb of a candidate changes its
  survivor. The candidate's meaning joins only when `check_meaning_write`
  allows it on the candidate's own citations; otherwise it joins as an alias
  only, and its references resolve to the survivor.

**Producers pre-filter, but nothing depends on them.** Bootstrap and append
normalization, consolidation, attach and the reword lane call the same
functions. They drop or flag a write that would be refused, so a paid run is
not lost at accept, and they declare the support the apply judges again. A
producer that skips them is refused at the writer.

## 3. Every write path of a facet's meaning

| # | Path | Entry points | How it goes through the chokepoint |
|---|---|---|---|
| 1 | Proposal apply: bootstrap creates | `create_study_map(apply=True)`, `revalidate_synthesis_candidate(apply=True)`, accept from CLI or desktop | `_apply_accepted_locked` → `stage_target_contents` → `compile_proposal_item` → `_compile_facet` → `check_meaning_write` (`meaning_support` per contribution) → `upsert_facet` on the staging copy → `verify_registry_transition` → `materialize_targets` |
| 2 | Proposal apply: a create carrying a registered id (bootstrap or append coverage, finding 1) | the same | Pre-filtered in `_normalize` with `check_meaning_write(registered=True)`. A refused one is dropped with a review diagnostic, and references resolve to the registered facet as it is. An allowed one is an `update` with `expected_target_hash` and `meaning_support`. Either way the apply judges it again as path 1. |
| 3 | Proposal apply: append facet reword (F6 lane) | append review accept | `_facet_reword` resolves citations with the resolver and sets `meaning_support`; the apply judges it as path 1 |
| 4 | Proposal apply: attach (a candidate absorbed into a registered facet as an example) | bootstrap and append accept | `_normalize` grows the example only when `check_meaning_write(registered=True)` allows the candidate's contribution, else alias only (contract note and review diagnostic). The alias row's `meaning_support` names the contributions; the apply judges them as path 1. |
| 5 | Proposal apply: edited payloads | review UI `edited_payload` | compiled like any payload: path 1 (support from its `meaning_support`, else the refs it adds) |
| 6 | In-run consolidation (merge, absorb as example or precondition) | `_normalize` with the facet-identity plan | `join_candidate` (`union_payload` is called only there); the survivor's `meaning_support` lists every joined contribution, judged again at apply (path 1) |
| 7 | Vault merge of registered facets | `learnloop facets dedupe` (`run_dedupe`), registry review, facet inspector, coarsening (`subject_registry.propose_facet_merge`) | `merge_registered_facets` → `merged_survivor` → `_write_registry` → `write_registry_text` with `RegisteredMerge` (the writer recomputes the union from the file) |
| 8 | Undo of any action | `learnloop facets undo`, desktop undo RPC | `_finish_undo` → `write_registry_text` with `Restore` (recorded entries). A candidate an ingest consolidation never registered is `Cited` on its own citations with a vault resolver, so undoing an exam-only alias join is refused (`exam_authority`). |
| 9 | Recovery of interrupted actions | `recover_interrupted_actions` (every merge, undo and dedupe; sidecar open; `doctor --fix-state`) | an `applying` merge: `RegisteredMerge`; `undoing`: path 8; an `applying` Library reword whose save never landed is withdrawn (no write) |
| 10 | Recovery of an interrupted proposal apply | `recover_apply_intents` (startup, doctor) | re-materializes an intent whose contents path 1 already checked before the intent was committed |
| 11 | The owner's Library save of `facets.yaml` | sidecar `write_vault_file` → `save_registry_text` | duplicate ids refused (finding 7); `write_registry_text` with `OwnerEdit` (each reword an audited action with an undo) |
| 12 | A new vault's empty registry | `vault.loader` init and load | writes `{"facets": []}`: no meaning |

**Not facet writers (checked).**

- `provenance_link`, `notation_mapping` and `source_conflict` apply as DB rows
  only. An exam span is now always `assessment_alignment`, and one targeting a
  facet is dropped with a review diagnostic.
- `_apply_reject_side_effect` never reverts a facet, and `_compile_deactivate`
  refuses facets.
- Graph-edit and authoring proposals cannot carry facet items (their item
  types exclude `facet`); if one did, it would compile through path 1.
- `doctor --fix-content` edits practice items only.
- `src-tauri` and the frontend write the registry only through
  `write_vault_file`.
- An edit made in another text editor is outside the app (a residual limit
  since F1).

**The bypass test** (`test_every_writer_of_facet_meaning_goes_through_the_authority_chokepoint`)
parses every module of the imported `learnloop`, `learnloop_sidecar` and
`learnloop_mobile` and fails when:

- a module outside a short, justified allowlist names `facets_path` or
  `"facets.yaml"`;
- any module other than `authority.py`, the loader's empty-registry init or
  `vault.writer` (staging) passes the registry to a file write;
- `upsert_facet`, `union_payload`, `write_registry_text`, `OwnerEdit`,
  `compile_proposal_item` or `stage_target_contents` is called outside its
  allowed modules;
- `_compile_facet` stops calling `check_meaning_write`;
- the apply stops verifying the staged registry.

Two behavioural tests pin the writers themselves:

- `write_registry_text` refuses an exam-only change whatever basis the caller
  declares. A spoofed textbook role or locator on the citation is ignored, and
  an empty `Cited`, a missing basis, a merge naming an unregistered retiree
  and a restore of an unrecorded entry are all refused.
- A facet item compiled without the authority context is refused.

## 4. What changed for each finding

1. **Registered-id creates.** `_normalize` checks every candidate whose id is a
   registered facet as a reword, with all its contributions. A refused one is
   dropped (gate `facet_restructure` or `exam_authority`, severity review) and
   its references resolve to the registered facet. An allowed one becomes a
   reviewed `update` with a stamped target hash (append mode: intent
   `restructure_unlocked`). `_compile_facet` refuses a meaning change to a
   registered facet with no explanatory contribution, whatever the operation.
2. **Corroboration.** `_gate_exam_authority` and `_has_semantic_authority` use
   `support_verdict`: exam material without an explanatory citation fails
   whatever else is cited. `check_meaning_write` applies the same rule per
   contribution.
3. **Unit overrides.** The resolver takes the unit's `role_override` (merged
   effective units expanded) over the member's role. `_span_refs`, the reword
   lane, the provenance-link lane and the apply all use it.
4. **Consolidation.** `join_candidate` joins a candidate's meaning only on its
   own citations; an exam-only candidate joins as an alias, with a
   `contract_note` on the identity action and an `exam_authority` review
   diagnostic. Joined candidates' exam refs carry `assessment_alignment` (the
   resolver), never support. The survivor's gate provenance stays its own, so a
   survivor that only exam material supports still hard-fails. Each joined
   contribution rides in `meaning_support` and is judged again at apply.
   Undoing an exam-only alias join would mint the candidate; it is judged as a
   new facet on its own citations and refused.
5. **Locators.** `_span_refs` records the locator derived from the validated
   ids (the model's `locator` is ignored). At apply, every ref a write adds is
   re-derived from the span its locator names, so displayed evidence is the
   validated evidence, and source links come from those refs. A spoofed ref is
   judged by the span it names.
6. **Scope.** A citation outside the selected units, or in a unit that does not
   contain its span, does not resolve: it is not recorded and supports
   nothing. A new `citation_scope` gate reviews it when the span, scope and
   unit gates do not already hard-fail it. The reword and link lanes drop it
   per item (`_span_problem` is the resolver).
7. **Duplicate ids.** `_parse_registry_text` refuses a registry that lists a
   facet id twice (`invalid_registry`, naming the id) before any action is
   recorded or anything written. `write_registry_text` refuses it too.

## 5. Behaviour the owner will notice

- **A reword through a proposal needs an explanatory citation.** This covers
  an append restructure, a re-bootstrap whose id collides with a registered
  facet, an edited payload, and an absorbed example on a registered facet. The
  owner's own Library edit needs none: it is the manual authority.
- **Pending proposals made before this change** are judged at accept like any
  other. Such a proposal is refused with a message naming the facet:
  - an attach row that grows a registered facet's examples with no
    `meaning_support`;
  - a create over a registered id with no explanatory citation.

  Re-run the append or bootstrap to get a proposal that carries its support,
  or make the change in the Library.
- **An exam-only candidate the judge merges into a textbook facet** now joins
  as an alias. Its id resolves to the facet, but its conditions and examples
  are not added. The ingest result says so (`contract_note`, review
  diagnostic). Undoing that consolidation is refused, because it would mint an
  exam-only facet; the owner can create the facet in the Library.
- **An exam span attached to a facet through a `provenance_link`** is dropped
  with a review diagnostic. Before, it was auto-applied as `support`.
- Proposal facet payloads carry `meaning_support`, proposal bookkeeping that is
  never written to `facets.yaml`, like `expected_target_hash`.

## 6. Tests

- **New `tests/test_facet_authority.py` (26)**: the table in §1.
- **Changed:**
  - `tests/test_facet_rewords.py`: `_facet_update_proposal` cites an
    explanatory span (new `tests/helpers.seed_explanatory_source`) when the
    update changes the facet's meaning; `cited=False` leaves it uncited.
  - `tests/test_facet_reword_paths.py`: crash injection patches
    `actions._write_registry` (the registry writer) instead of the removed
    `_write_facets` / `_write_registry_text`.
  - `tests/test_facet_identity_actions.py`: the same, for 7 crash tests.
  - `tests/test_facet_identity_ingest.py`, `tests/test_facet_identity_composition.py`:
    the attach row's payload keys include `meaning_support`, which cites the
    absorbed candidate's span.

## 7. Gate

Run on `b2c14e49` (the fix and the references; only this file changed after),
2026-10-13, with `TMPDIR` set to the worktree's `fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (163 packages resolved) |
| `uv run lint-imports --no-cache` | 15 contracts kept, 0 broken |
| Fail-first: `tests/test_facet_authority.py` against `783263ef`'s `src/` | 25 failed, 1 passed (the guard) |
| Targeted: the facet, synthesis, append, apply and architecture suites (14 files) | 221 passed |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **9,115 passed**, 0 failed, 0 skipped, 46 warnings (the existing fork and deprecation warnings), 387 s (13 min 28 s including the wait for the lock); 9,089 at the merge plus the 26 new tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **95 passed**, 9,020 deselected, 1 warning, 102 s |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated (`b2c14e49`: the three shifted config citations, table-note source lists, `source_commit` stamps); `errors: []`; schema head 185 |
| `validate_vault.py`, `module_validate.py` | passed (1,085 notes; wikilinks 14,712/14,712, source/test links 11,795/11,795) |
| Frontend, `src-tauri`, schema, config | unchanged (no npm, cargo or migration step needed) |

## 8. Paid calls

None. Cost $0. Every test uses fakes; no command ran against a vault.

## 9. Open questions for the owner

1. **Uncited new facets.** A new facet with no explanatory citation is still
   admitted after review (`adequate_provenance`), as before. A model could
   draw a new facet from the exam profile and cite nothing. Should a new
   facet in a run that had exam material need an explanatory citation at
   apply too? The recommended default is to keep it reviewable (generous
   default) and leave the review diagnostic as it is.
2. **Facets already in the registry.** A facet that reached the registry
   through one of the seven routes before this fix keeps its meaning, and a
   vault merge treats registered meaning as admitted. A doctor audit could
   list registered facets whose provenance is exam-only or uncited. Not built:
   build one?
3. **Declared support is trusted to be about the wording.** The chokepoint
   validates which spans a write cites and their roles. It cannot check that a
   cited textbook span says what the new wording says; that is a semantic
   check (a judge call), not done here.
4. **Learning objects** get the corrected gate rule (finding 2's
   corroboration, the unit override, scope) at synthesis, but no apply-time
   chokepoint. That chokepoint is facet-only, per the stage. Extend it to LO
   meaning?
5. **A span selected in two source sets with different roles** resolves to
   the less authoritative role when the vault-wide resolver is used (a
   proposal with no source set, an undo). Is that the right tie-break?

## 10. Files

- **New:** `src/learnloop/content/facet_identity/authority.py`,
  `tests/test_facet_authority.py`, this file.
- **Changed, Python:**
  - `content/sources/role_authority.py`: `support_verdict`,
    `is_semantic_support`, the role and relation sets;
  - `content/synthesis/synthesis_gates.py`: the rule, `ProvenanceRef.problem`,
    `citation_scope`, proposal-only keys in the alias check;
  - `content/synthesis/source_set_synthesis.py`: the resolver,
    `_span_refs`, consolidation, attach, id collisions, `meaning_support`;
  - `content/synthesis/source_append.py`: `_span_problem`, the reword's
    `meaning_support`, exam links;
  - `content/proposals/patches.py`: `_compile_facet`, the staged-registry
    check, `link_payload`;
  - `content/proposals/apply_protocol.py`: passes the context and uses
    `link_payload`;
  - `content/facet_identity/actions.py`: `_write_registry` with a basis,
    duplicate ids, `merged_survivor`.
- **Changed, tests:** `tests/helpers.py` and the five test files in §6.
- **Changed, docs:** `spec_source_ingestion_v2.md` §4.3, §8.7, §10.3;
  `spec_knowledge_model.md` §3.4; the regenerated architecture references.
- **Fixtures:** none touched. `fixtures/linear_algebra`, `probability` and
  `arxiv_v2` were not opened.
