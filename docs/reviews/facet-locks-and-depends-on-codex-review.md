# Codex review: facet locks removed, criterion `depends_on`

Stage `facet-locks-and-depends-on`, branch `facets/locks-and-depends-on`.
Codex reviewed `d60b0b0a` (job `20261013-034101-0lVA4S`, source review and
read-only in-memory checks). It found one High and four Medium defects. All
five reproduced as failing tests before the fix, and all five are fixed in
`1096319f`. No migration, no new RPC, no frontend or `src-tauri` change, and
no paid call.

## Review

### Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Library edits bypass the facet-history guarantee | fixed | `1096319f` | `tests/test_facet_reword_paths.py`: `test_a_library_edit_that_rewords_an_evidenced_facet_records_a_version_with_undo`, `..._only_grows_a_facet_is_written_as_typed_and_is_not_a_version`, `..._cannot_set_a_facets_version_by_hand`, `..._registry_edit_that_does_not_parse_is_refused_and_writes_nothing`, `test_a_library_reword_interrupted_before_the_write_is_withdrawn`, `..._interrupted_after_the_write_is_finished_by_recovery`, `..._whose_write_never_landed_is_withdrawn_by_recovery` |
| F2 | Medium | Append cannot produce the facet rewords its prompt promises | fixed | `1096319f` | `tests/test_facet_reword_paths.py`: `test_the_append_schema_lets_a_provider_reword_a_facet`, `test_an_append_facet_restructure_applies_as_a_facet_version_with_undo`, `..._refuses_when_the_facet_changed_since`, `..._that_cannot_apply_is_dropped_with_a_diagnostic` (deactivate; unregistered target) |
| F3 | Medium | "Grading-neutral" repair also changes failure attribution | fixed | `1096319f` | `tests/test_synthesis_criterion_dependencies.py`: `test_fix_content_keeps_a_self_dependency_because_removing_it_changes_failure_attribution`, `test_fix_content_never_changes_localization_for_the_entries_it_removes`, `test_doctor_fix_content_cli_reports_self_dependencies_it_leaves` |
| F4 | Medium | Reword undo records no owner verdict | fixed | `1096319f` | `tests/test_facet_reword_paths.py`: `test_undoing_a_reword_appends_the_owners_verdict_to_the_judgment_ledger`, `test_an_interrupted_reword_undo_records_the_verdict_once` |
| F5 | Medium | An unchanged-meaning payload can lower the version and break undo | fixed | `1096319f` | `tests/test_facet_reword_paths.py`: `test_a_stale_version_on_an_unchanged_meaning_keeps_the_current_version_and_the_undo`, `test_an_oversized_incoming_version_is_ignored_and_every_undo_still_applies`, `test_a_reword_after_a_reword_undoes_in_order_with_server_versions` |

### How each one reproduced (tests written first, run against `d60b0b0a`)

- **F1.** A `write_vault_file` save of `facets.yaml` that changes an evidenced
  facet's claim wrote no action, and the facet kept `version` 1. A typed
  stale version was written as typed. An unparseable registry was written
  too. A reword row left `applying` while the file still showed the old entry
  was "recovered" by writing the new entry (`applied`): wrong for an owner
  save that never landed.
- **F2.** `AppendReconciliation.model_validate` of a facet restructure failed
  with `literal_error` on `target_entity_type='facet'`. Widening the literal
  alone would not have been enough. Under strict structured output the
  restructure's bare `payload: dict` becomes an object the provider may not
  fill; `test_codex_output_schema.py` already lists it among the
  `_KNOWN_UNFILLABLE_MAP_FIELDS`. A real model's facet restructure would
  therefore always arrive with an empty payload and reword nothing.
- **F3.** With `depends_on: [<itself>, facet_…]` the repair removed 2
  entries, not 1. Localization of that failed criterion went from
  `assessable=False, first_error=False` to `True, True`, as Codex said.
- **F4.** After a reword undo, `judgment_ledger` had no row.
- **F5.** A same-meaning payload with `version: 1` wrote 1 over 2. A reword
  with `version: 99` wrote 99, and the chain 7 then 2 ended at 8 instead of 3.

### What changed

**F1. The Library save goes through the reword record.**
- `content/facet_identity/actions.save_registry_text` handles a Library save
  of `facets.yaml` (`write_vault_file` detects the registry path).
- Every existing facet whose `MEANING_FIELDS` changed gets a `reword` action,
  as a proposal apply would: `origin = 'registry'`, `judge = 'owner'`,
  `run_id = 'library'`, `detail.via = 'library'`, the replaced entry kept,
  evidence recorded. It is undoable from the facet inspector and with
  `learnloop facets undo`.
- The save is write-ahead under the vault mutation lock: the `applying` rows
  commit, `facets.yaml` is replaced atomically, then the rows become
  `applied`.
- Recovery now withdraws (`abandoned`) a reword intent whose file still
  shows the old entry, instead of writing one entry of a save the owner saw
  fail. It never re-folds learning objects for a reword (no evidence moved).
- The text is written as typed unless a version, or a reworded facet's stale
  `semantic_fingerprint`, had to be corrected. The RPC returns the text
  actually written; the Library screen already shows the returned body.
- Text that does not parse, or is not a valid facet registry, is refused
  with `invalid_registry` and nothing is written. Before, it was written as
  typed.
- The sidecar reloads its vault after a registry save.
- `vault/yaml_io.yaml_from_string` was added, the round-trip parser that is
  the inverse of `yaml_to_string`.

**F2. Append can name a facet, and the wording reaches the apply.**
- `AppendRestructure.target_entity_type` admits `facet`.
- A new declared `facet_wording` (`AppendFacetWording`: kind, claim,
  description, the condition lists, non-goals) carries the new meaning. A
  strict-schema provider can fill it. A blank field keeps the facet's
  current value.
- Normalization (`source_append._facet_restructure_payload`):
  - only the meaning fields travel, from `facet_wording`, with the bare
    payload as a fallback for a provider that fills it;
  - `expected_target_hash` is stamped from the vault at synthesis, because
    the neighborhood never shows the model a target hash;
  - a facet `deactivate`, an unregistered target, or a restructure that
    changes nothing is dropped with a `facet_restructure` review diagnostic.
- The accept-time hash check refuses the reword if the facet changed since
  (tested).
- `_compile_facet` refuses an `update` of a facet that is not registered
  (before, it would have minted the facet again, possibly under a
  merged-away id). It also strips `expected_target_hash` from what it
  writes, so proposal bookkeeping stays out of `facets.yaml`.
- Prompt rule 6 now says how to reword a facet.
- The append prompt versions keep their `mvp-0.10-*` names. Both were
  introduced on this unmerged branch, so no completed run or cached shard
  carries them.

**F3. `--fix-content` removes only what grading already ignored.**
- An entry is removed only when it names no criterion of the item.
- A self-dependency is kept and listed under `self_dependencies`, with a
  note: a failed attempt at that criterion contributes no failure evidence,
  and removing the entry would change that. It needs a semantic correction
  by hand, and doctor reports it as `criterion:dependency_cycle`.
- The CLI prints "left as is (depends on itself): …". The help text and the
  report's note no longer claim that every removal is neutral.
- A new negative test checks that localization is identical before and after
  the repair for every pass/fail combination.
- Fresh backup-API copies of the tracked `probability`, `arxiv_v2` and
  `linear_algebra` give the same dry-run counts as the stage review (46/13,
  46/15, 0) and **0 self-dependencies**, so the owner commands in the stage
  review stand.

**F4. A reword undo is the owner's verdict.**
- `append_owner_verdicts` writes one row for a reword:
  - task `facet_reword` (`REWORD_TASK`);
  - `facet:<id>` against `facet_wording:<content hash of the meaning
    fields written>`;
  - judge `owner`, verdict `rejected`;
  - a rationale with the action, versions and fields.
- It commits in the same transaction as the `undoing` intent. An interrupted
  undo that is retried, or finished by recovery, never appends it again
  (tested with a crash before the file restore).
- Keying on the wording makes a later, different wording a different
  question.

**F5. `version` is server-managed for an existing facet.**
- `_facet_version` ignores a payload's `version`. A facet keeps its version
  when its meaning is unchanged and gets exactly one more when it changes.
- The Library path applies the same rule.

**Docs.**
- `spec_knowledge_model.md` §3.4 now lists both writers, the server-managed
  version and the undo verdict.
- `spec_source_ingestion_v2.md` §10.3 describes the facet restructure shape.
- The stage review's two claims that did not hold ("the one in-app path", and
  "Grading does not change" without the self-dependency case) are corrected
  in place.
- The CLI help snapshot is regenerated, and so are the architecture
  references: the config reference cites `cli/app.py` line numbers, which
  this change shifted.

### Codex's "claims that don't hold"

All four are accepted and corrected (F1, F2, F3, F5 above). None was
rejected.

### Spec-conformance rows Codex left open

- **Shadow-rebuild equivalence.** These fixes change content writes and
  history, never projection, scoring or serving. `tests/test_shadow_rebuild.py`
  and `tests/test_rebuild_orchestrator.py` run in the full suite below.
- **Full suite, WAL, concurrency.** Rerun below (full suite and the
  durability lane).

### Residual limits (not defects of this stage)

- An edit of `facets.yaml` made outside the app (another text editor) is
  still not versioned. The app has no hook on it.
- Deleting a facet entry in the Library is not a reword, so it is not
  versioned. Doctor reports criteria that then target an unregistered
  facet.

## Gate

Run on `1096319f` (the fix commit; only this file changed after it),
2026-10-13, with `TMPDIR` set to the worktree's `fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (163 packages resolved) |
| `uv run lint-imports --no-cache` | 15 contracts kept, 0 broken |
| Reproduction: the new tests against `d60b0b0a`'s `src/` | 18 failed, 8 passed (every F1, F2, F4, F5 test and both F3 behaviour tests fail; the localization guard and the pre-existing tests pass) |
| Targeted: `test_facet_reword_paths.py`, `test_synthesis_criterion_dependencies.py`, `test_facet_rewords.py` | 32 passed |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8973 passed**, 0 failed, 0 skipped (271 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **95 passed**, 8878 deselected (93 s) |
| `db_validate_reference.py` | ok, `errors: []`, schema head 188 |
| `db_generate_reference.py` | changes only the `source_commit` stamps (no content drift), so nothing to commit |
| Frontend, `src-tauri`, schema | unchanged by the fix (no npm, cargo or migration step needed) |

The F3 dry run was rerun with the fixed code on fresh backup-API copies
(`fixtures-local/fl-*-review`). Results: probability 46 entries in 13
items, arxiv_v2 46 in 15, linear_algebra 0. None of them has a
self-dependency.

## Paid calls

None. Cost $0.

## Open questions for the owner

1. **Learning-object restructures and their target hash.** This is
   pre-existing, found while fixing F2, and not changed here. The append
   neighborhood never shows the model a target hash, and a restructure's
   `expected_target_hash` defaults to `""`. From reading
   `_accept_time_rechecks`: an LO or practice-item restructure written by a
   real model is therefore refused at accept as "target changed after
   synthesis". Their bare `payload` is also unfillable under strict output
   (already pinned in `_KNOWN_UNFILLABLE_MAP_FIELDS`). Facet restructures now
   stamp the hash server-side and carry a declared `facet_wording`. Should
   LO and practice-item restructures get the same treatment? That changes
   which append proposals can apply, so it was left for a successor.

## Re-review

Codex re-reviewed `d60b0b0a..facets/locks-and-depends-on` (through
`f84366f1`) and the record above (job `20261013-051444-33a9sK`, source review
and isolated in-memory checks). It confirmed F1 to F5 fixed and found one new
High defect, F6, so the stage was reopened. F6 reproduced (first on the
unfixed tree, then as failing tests). It is fixed in `5a6eeb54`, and the
references are regenerated in `4f02c092`. No migration, no new RPC, no
frontend or `src-tauri` change, and no paid call.

### Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Library edits bypass the facet-history guarantee | fixed (confirmed by the re-review) | `1096319f` | the tests listed above |
| F2 | Medium | Append cannot produce the facet rewords its prompt promises | fixed (confirmed by the re-review) | `1096319f` | the tests listed above; their builder now cites a span (F6) |
| F3 | Medium | "Grading-neutral" repair also changes failure attribution | fixed (confirmed by the re-review) | `1096319f` | the tests listed above |
| F4 | Medium | Reword undo records no owner verdict | fixed (confirmed by the re-review) | `1096319f` | the tests listed above |
| F5 | Medium | An unchanged-meaning payload can lower the version and break undo | fixed (confirmed by the re-review) | `1096319f` | the tests listed above |
| F6 | High | New facet restructures bypass exam-authority enforcement | fixed | `5a6eeb54` | `tests/test_facet_reword_paths.py`: `test_the_append_schema_lets_a_facet_reword_cite_its_spans`, `test_an_exam_only_facet_reword_hard_fails_the_exam_authority_gate` (schema to gate), `test_an_uncited_facet_reword_is_dropped_because_its_authority_cannot_be_judged[exam, alternate_explanation]`, `test_a_facet_reword_an_explanatory_span_corroborates_passes_the_gate`, `test_a_cited_facet_reword_records_its_spans_in_the_facets_provenance`, `test_a_facet_reword_citation_that_does_not_resolve_is_dropped_not_fatal[False, True]` |

### How F6 reproduced

- **The bypass, on `f84366f1`.** The setup: the bootstrap map, then an
  appended member with role `exam`. The provider returned a facet restructure
  of `facet_symmetry_definition` with new wording. It had no citation,
  because the schema had no field for one. The gates produced only an
  `adequate_provenance` review diagnostic (`blocked=False`). Accepting the
  item rewrote the facet's claim. This is Codex's scenario. Exam units never
  reach the model as text (`_collect_inputs` keeps them in the exam profile),
  so an exam-driven reword arrives uncited, and `_gate_exam_authority` skips
  an item with no provenance.
- **The tests, on `f84366f1`'s `src/`.** All 8 new tests fail. In 7 of them,
  `AppendReconciliation.model_validate` rejects `facet_wording.provenance`
  with `extra_forbidden`: the wire shape could not carry a citation. The
  schema test's assertion fails too.

### What changed (`5a6eeb54`)

**Wire and prompt.**
- `AppendFacetWording.provenance: list[SynthSpanRef]` holds the provided
  spans that support the new wording, in the shape a new facet's
  `provenance` uses. A strict-schema provider can fill it.
- Prompt rule 6 asks for these citations and says that an uncited reword is
  dropped. Rule 7 (exam material must not modify a canonical claim) is
  unchanged.

**Normalization.** `source_append._facet_reword` replaces
`_facet_restructure_payload`.
- **A citation that does not resolve is dropped.** It uses the same checks
  as the `provenance_link` lane (`_span_problem`: extraction run in the
  source set, span resolves, unit valid). It produces a `facet_restructure`
  review diagnostic and never hard-fails the paid run.
- **A reword left with no citation is dropped,** with a `facet_restructure`
  review diagnostic. The diagnostic points the owner to the Library
  reword. Keeping an uncited reword as an `adequate_provenance` review was
  the bypass: its authority cannot be judged.
- **Roles come from the extraction run** (`_span_refs`, `span_origin`). The
  model's `role` is never used.
- **The resolved citations ride on the `GateItem`.** Exam-only support is an
  `exam_authority` hard-fail, exactly as for a new facet (§8.7: "hard-fail
  unless explicit manual authority"). Exam plus an explanatory span is
  corroborated and passes. Support with no semantic-authority role at all
  (`problem_set`, `notes`, an `exercise` relation) is an
  `adequate_provenance` review, as for a new facet.

**Persistence.**
- The citations are added to the facet's `provenance` snapshot in the
  proposal payload. The existing refs and the origin are kept, and
  duplicates are skipped. The apply writes the snapshot to `facets.yaml` and
  links the new spans in `entity_source_links` (the standard
  `_entity_source_link_rows` path).
- An exam citation is recorded as `assessment_alignment`, never as semantic
  support (§9.3 keeps the two apart).
- The reword's undo restores the old snapshot along with the old wording
  (tested).

**Manual authority.** For a facet, the explicit and audited override is the
owner's own reword in the Library (F1). That writes a `reword` action with
judge `owner` and `detail.via = "library"`, and it is versioned and
undoable. Nothing in the append lane sets `manual_authority`.

**Docs.**
- Spec §8.7: "adequate provenance" now covers a reworded facet.
- Spec §10.3 describes the cited reword.
- The append prompt versions keep their `mvp-0.10-*` names. As before, both
  were introduced on this unmerged branch.
- `4f02c092` regenerates the references. The config reference cites
  `source_append.py:376` for `ingest.bootstrap_practice_items`, and the new
  imports shifted it to `:382`. Everything else in that commit is the
  `source_commit` stamp.

### Residual limits (pre-existing, not changed here)

- **Unit role overrides.** A citation's role is its member's `default_role`
  (`span_origin` is per extraction run). A unit-level `role_override` is not
  seen by `_span_refs`. This applies to every new facet and LO citation too.
  It is pre-existing and shared, so it is left for a successor.
- **Links after an undo.** After a reword undo, the `entity_source_links` row
  the reword added stays. That table is a raw ledger, and no proposal revert
  removes links.
- **LO and practice-item restructures** still carry no citations. They cannot
  apply anyway; see open question 1 (their target hash is never stamped).

### Re-review gate

Run on `4f02c092` (the fix and reference commits; only this file changed
after them), 2026-10-13, with `TMPDIR` set to the worktree's
`fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (163 packages resolved) |
| `uv run lint-imports --no-cache` | 15 contracts kept, 0 broken |
| Bypass reproduction on `f84366f1` (scratch test, exam-role member, uncited reword) | diagnostics `[adequate_provenance: review]`, not blocked; accepting it rewrote the claim. On `5a6eeb54` the same scenario gives `[facet_restructure: review]` and persists no facet update |
| `tests/test_facet_reword_paths.py` against `f84366f1`'s `source_append.py` and `ai_contracts.py` | 12 failed, 13 passed: the 8 new F6 tests, plus the 4 F2 append tests whose shared builder now carries a citation the old wire shape rejects (`extra_forbidden`) |
| Targeted: `test_facet_reword_paths.py` | 25 passed |
| Append-adjacent: `test_codex_output_schema.py`, `test_facet_identity_ingest.py`, `test_ingest_instrument_gates.py`, `test_openai_chat_client.py`, `test_structured_transport_parity.py`, `test_source_append.py`, `test_facet_rewords.py`, `test_synthesis_gates.py` | 411 passed |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8981 passed**, 0 failed, 0 skipped (359 s); 8973 before plus the 8 new tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **95 passed**, 8886 deselected (123 s) |
| `db_generate_reference.py` | one content change (the `source_append.py:382` citation) plus the `source_commit` stamps, committed in `4f02c092` |
| `db_validate_reference.py` | ok, `errors: []`, schema head 188 |
| `module_validate.py` | ok (wikilinks 14712/14712, source/test links 11795/11795) |
| Frontend, `src-tauri`, schema | unchanged by the fix (no npm, cargo or migration step needed) |

### Paid calls (re-review)

None. Cost $0.
