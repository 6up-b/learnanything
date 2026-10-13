# Facet reword confirm: a reword without explanatory support waits for the owner

Stage `facet-reword-confirm`, branch `merge/facet-locks` (base `da3d5585`, the
facet authority chokepoint after its second Codex re-review). Owner-directed,
2026-10-13:

> Ok youre right about exams and problem sets creating poor facets, although
> failure on a pset while having success on a generated practice surface that
> tests the same underlying concept could imply that the pset is testing some
> nuanced application/version of the idea that isnt being quite captured by
> the generated practice. But that could be for the LLM action router to
> decide when such a situation presents itself. We can have explicitly
> held-out exams/practice sets, but could also use practice sets and exams to
> seed what kind of questions and to what difficulty/rigor the learner is
> preparing for. I feel like a confirm this reword is better.

- Fix: `b59f5a1a`. References regenerated: `8351490f`.
- No migration (a held reword is a `facet_identity_actions` row with status
  `proposed`, which the 185 table already allows), no config change.
- One new RPC (`decide_facet_reword`, desktop only), two CLI commands
  (`learnloop facets confirm|keep`), frontend and `src-tauri` changes.
- No algorithm successor: a content path (which facet writes are admitted,
  and when). Scoring, scheduling, projections and replay are unchanged.
  Checked at the Codex re-review: on backup-API copies of the three tracked
  fixtures, shadow rebuilds under the predecessor, and under this stage with
  the switch on and off, agree exactly. Why rule 5 of handoff §0 takes no
  successor here: `facet-reword-confirm-codex-review.md`, "Re-review".
- No paid call.

**Corrected by the Codex review** (`d79a24af`;
`docs/reviews/facet-reword-confirm-codex-review.md`). These statements below did
not hold as built:
- "Exam-only support is refused on every write path" (§1.2, §3): an attach or
  in-run absorb whose candidate cited exam material under the wrong unit
  joined as an uncited example (F1). Fixed: joins are judged with the
  candidate's unresolved citations.
- "Only what the reword changed is taken from it, so an alias added to the
  facet since stays" (§1.1): not when the reword changed the aliases too
  (F2). Fixed: a three-way merge, and a conflict refuses the confirm.
- "An exam citation shows no text" (§1.1): a source re-marked as an exam, or
  a unit held out, after the hold kept its cached excerpt (F3). Fixed:
  excerpts are read when shown, with that moment's roles.
- The confirm wrote its citations to facets.yaml but not to
  `entity_source_links` (F4). Fixed: installed write-ahead, finished by
  recovery.
- "Title and worked-example changes from a source update apply" (§1.3, §4):
  the append producer could not send them (F5). Fixed.
- "No config change": the review adds the kill switch
  `facet_identity.reword_confirm` (F6; no algorithm successor, as above).

## 1. What changed

### 1.1 One-tap confirm instead of refusal

`authority.check_meaning_write` used to refuse (`unsupported_reword`) a change
to a registered facet's meaning unless every contribution cited an
explanatory span. Now:

| Support of the change (per contribution) | Before | Now |
|---|---|---|
| every contribution explanatory | applies | applies (unchanged) |
| any contribution exam-only (exam with no explanatory citation beside it, held-out units included) | refused (`exam_authority`) | refused (`exam_authority`), on every path |
| otherwise: uncited, or only notes, problem-set or unknown-role citations, or citations that do not resolve | refused (`unsupported_reword`) | **held for the owner's confirm** (`unsupported_reword`, `verdict.confirmable`) |

- **At accept** (`patches._compile_facet` → `_held_for_confirm`): a
  confirmable write is not written. The item is accepted, nothing touches
  `facets.yaml` and no source link is added. The apply's side effect
  (`facet_reword_confirm`) records a `reword` action with status `proposed`
  and `detail.confirm`, which holds:
  - the entry it would replace and the entry it would write;
  - the fields it changes;
  - its validated sources (`authority.source_views`: source, unit, role,
    locator, a short excerpt; an exam citation shows no text);
  - the citations that did not count, and why;
  - its contributions (`meaning_support`), which the confirm judges again;
  - a plain message naming the facet.

  The rest of the proposal applies as usual.
- **Confirm** (`actions.confirm_reword`, under the vault lock, write-ahead
  like a Library save):
  1. the facet's meaning must still be the wording the reword replaces
     (`changed_since` otherwise);
  2. the recorded contributions are re-judged with the vault's source sets,
     so a source re-marked as an exam since refuses the confirm
     (`exam_authority`);
  3. the owner's `granted` verdict (`judgment_ledger`, task
     `facet_manual_authority`, `judge = 'owner'`, origin `confirm`), the save
     intent (`facet_registry_saves`) and the row (now `applying`, judge
     `owner`, with the entries it replaces and writes) commit together;
  4. `facets.yaml` is written through the chokepoint with an `OwnerEdit`
     basis (a facet version when its meaning fields change);
  5. the row and the intent become `applied`.

  The row is then the facet's `reword` history entry with the existing
  one-tap undo. Only what the reword changed is taken from it, so an alias
  added to the facet since stays.
- **Keep current wording** (`actions.keep_current_wording`): the row becomes
  `abandoned` with `undo_detail.kept_current_wording`, and the owner's
  `rejected` verdict is recorded (task `facet_reword`), as an undo records
  one.
- **Interrupted confirm.** An in-process write failure, or a process stopped
  before the write, returns the reword to `proposed`. Recovery or the failure
  handler withdraws its verdict through the save intent, and the owner can
  confirm again. `doctor --fix-state` reports "the reword waits for your
  confirm again".
- **Pending proposals made before this change.** Their facet items compile
  through the same path at accept, so one the old rule refused (an uncited
  create over a registered id, a notes-only reword) becomes a confirm. Its
  message names the facet, for example: "The proposed new wording of facet
  facet_svd_factorization (claim) has no textbook, lecture, paper, reference
  or alternate-explanation source behind it (it cites no source), so it waits
  for your confirm before it changes the facet".
- **Producers keep what they used to drop.** Each one emits a
  `facet_reword_confirm` review diagnostic for what it keeps:
  - the append reword lane keeps an uncited reword (it used to drop it);
  - bootstrap and append creates that carry a registered facet's id keep a
    confirmable one as a checked `update` with a stamped target hash.
- **Surfaces (no new screen).**
  - Registry review lists the subject's pending confirms at the top.
  - The proposals inbox lists every pending confirm above the batches.
  - A proposal item that holds a confirm shows "waits for your confirm".
  - The facet inspector's history labels a held, kept, confirmed, or title
    and examples change, with its sources.
  - Each confirm card (`components/RewordConfirms.tsx`) shows:
    - the facet;
    - each changed field, now and new;
    - one plain sentence on its support ("It cites no source.", "It cites
      only notes material: no textbook, lecture, paper or reference
      passage.");
    - its sources with their excerpts;
    - the citations that did not count;
    - the buttons **confirm reword** and **keep current wording**.

  RPC `decide_facet_reword {actionId, decision: "confirm" | "keep"}`;
  `get_subject_registry` and `get_proposals` carry `rewordConfirms`; CLI
  `learnloop facets confirm|keep <id>`.

### 1.2 Exam stays a hard block

- Exam-only support is refused on every write path, a confirm included. The
  table in §3 covers each path.
- **Held-out units.** A unit marked `held_out_evaluation` in its unit
  selection is exam material whatever role its member has: the resolver gives
  its spans the role `exam`.
- **Misdeclared exam citations.** A citation that does not resolve but names
  exam material by its span is still exam material, never "uncited"
  (`CitationResolver.exam_material`). The span might be named under the wrong
  unit, or sit in an exam member's unselected unit. This closes a hole the
  confirm path would otherwise open: a producer drops a citation that does not
  resolve, so a reword resting on a misattributed exam span would have arrived
  "uncited" and become a confirm. The check runs in three places:
  - the chokepoint;
  - the append reword lane (dropped with an `exam_authority` review
    diagnostic, since the gates cannot see an unresolved citation);
  - the bootstrap/append registered-id check (dropped with `exam_authority`).
- The only override remains the owner's own Library edit.
- Exams and problem sets keep their assessment-alignment role (exam profile,
  task families, formats, emphasis). Nothing in that lane changed.

### 1.3 Titles and worked examples need no explanatory citation

- `authority.PRESENTATION_FIELDS = (title, positive_examples,
  negative_examples)`. A change to a registered facet that touches only these
  is allowed without an explanatory citation (verdict `presentation`).
  Exam-only support is still refused, since an exam's wording or worked item
  never reaches a facet through a model.
- Claim, description (definition), kind, preconditions, postconditions,
  applicability and non-goals stay meaning.
- The change is recorded on the facet's history with its sources: a `reword`
  row with `detail.presentation`, the same undo, and no version.
- Every proposal reword now keeps its validated sources (`detail.sources`).
- When the change is a proposal's own attach or in-run consolidation, that
  identity action is already the history entry with its undo, so no second
  row is written.
- An attach that absorbs an uncited candidate's claim as a worked example of
  a registered facet now grows the examples, where it used to join as an
  alias only.

### 1.4 Every other guarantee kept

These are unchanged, and their tests pass unchanged:
- citation resolution from ids;
- scope and unit membership, split children;
- locators derived from validated ids;
- unresolved refs never linking;
- strict `meaning_support`;
- duplicate-id refusal;
- undo pre-check and recovery settling;
- Library save intents;
- the structural bypass test (`OwnerEdit` is still only constructed in
  `actions.py`, `_compile_facet` still calls `check_meaning_write` before
  `upsert_facet`, and the staged registry is still verified).

## 2. Tests

**New: `tests/test_facet_reword_confirm.py` (42).**

| Area | Tests |
|---|---|
| 1. confirm | uncited reword held; notes / problem_set / unknown-role support held (3); confirm applies as owner authority with verdict, save intent, history and undo; confirm keeps a later alias; keep closes it with the owner's rejected verdict; a pre-change pending proposal becomes a confirm naming the facet; confirm refuses after the facet changed; interrupted confirm returns to pending (verdict withdrawn) and confirms later; in-process failure stays pending; uncited and notes-cited append rewords reach the owner; bootstrap registered-id create kept for confirm; a confirm never shows exam text |
| surfaces | registry review lists a confirm with wording and sources; the sidecar lists (inbox and per item) and confirms; the sidecar keeps the wording and refuses a second decision; the CLI confirms |
| 2. exam | exam-only claim, precondition, title and worked-example changes refused and never held (4); exam-only create over a registered id refused; exam-only bootstrap candidate dropped; exam-only append reword hard-fails; registry writer refuses exam-only and an unconfirmed reword; exam span cited under the wrong unit refused at the writer (2); same via the append lane and via bootstrap (dropped, `exam_authority`); a confirm whose support became exam material refused; a held-out unit is exam material whatever its member's role; the Library stays the override |
| 3. titles and examples | title change applies uncited, on the history; worked example applies with its notes source on the history, undoable; claim, definition, preconditions and non-goals stay meaning (4); a cited reword records its sources; the chokepoint verdicts for titles and examples |

**Fail-first.** The 42 tests were run against `da3d5585`'s `src/` and
`migrations/` (a `git archive` copy under `fixtures-local/tmp`, with
`-o pythonpath=` pointing at it; a probe test confirmed both `learnloop` and
`learnloop_sidecar` were imported from the copy).

- **As written: 39 failed, 3 passed.** The 3 call no new API: the exam-only
  bootstrap candidate, the registry writer, and the Library override.
- **With only the new listing helper shimmed to "no confirms": 33 failed, 9
  passed.** The 9 are exam guards whose refusal already held. The 33 fail on
  the behaviour itself:
  - the old writer raised `PatchApplicationError ... cites no span from an
    explanatory source` for every uncited, notes, problem-set or
    unknown-role reword and for the title and example changes;
  - the held-out unit resolved as `primary_textbook`;
  - `MeaningVerdict` had no `confirmable`;
  - the history had no `presentation` key;
  - no confirm or keep API, no RPC, no CLI command existed.

  Four of the 33 were added while implementing, as guards against this
  stage's own relaxation: the two wrong-unit writer tests and the append and
  bootstrap wrong-unit tests. On the base they fail because the refusal was
  reported as `unsupported_reword` or `facet_restructure`, not as exam
  material; nothing was written either way.

**Existing tests updated to the owner's decision.** Each pinned the refusal
the owner replaced:

- `tests/test_facet_authority.py`:
  - the exam append's uncited create over a registered id is kept as an
    update and held, never written;
  - the bootstrap candidate is kept for confirm;
  - the proposal create over a registered facet is held;
  - a reword citing a span outside its unit drops the citation and is held;
  - a reword supported only by an unselected span is held, naming the
    citation that did not count.
- `tests/test_facet_authority_review.py`: the reword citing the unselected
  half of a split unit is held, naming the citation. The variant where that
  half is selected as exam material is refused (new test).
- `tests/test_facet_reword_paths.py`: an uncited append reword waits for the
  confirm (exam and alternate-explanation members); a reword whose only
  citation does not resolve is kept uncited.
- `tests/test_facet_rewords.py`: a growth-only examples update is still not a
  version, and is now on the history with its source.
- `tests/test_mobile_allowlist.py`: `decide_facet_reword` is desktop only.
- `tests/cli_help_snapshot.json`: `facets confirm`, `facets keep`, and the
  `facets actions` help.

**Frontend.**
- New `RewordConfirms.test.tsx` (7): wording before and after and the
  plain-words support line; confirm and keep with one tap; a refused confirm
  keeps the card and reports the error; sources with excerpts and exam text
  hidden; only pending rewords listed.
- `FacetInspector.test.tsx` gains the history labels (1).

## 3. Exam-only support on every write path

| Path | Exam-only outcome | Test |
|---|---|---|
| Proposal apply: update (claim, precondition, title, worked example) | refused at the writer, nothing held | `test_an_exam_only_change_through_a_proposal_is_refused_never_held[4]` |
| Proposal apply: create carrying a registered id (exam provenance ref) | refused | `test_an_exam_only_create_carrying_a_registered_id_is_refused` |
| Proposal apply: exam span declared under the wrong unit | refused (exam material by its span) | `test_an_exam_span_cited_under_the_wrong_unit_is_refused_not_held[2]` |
| Proposal apply: a held-out unit of an explanatory member | refused | `test_a_held_out_evaluation_unit_is_exam_material_whatever_its_members_role` |
| Bootstrap normalize: registered-id candidate | dropped (`exam_authority`) | `test_an_exam_only_bootstrap_candidate_carrying_a_registered_id_is_dropped_not_held`, `test_a_bootstrap_reword_citing_exam_material_under_the_wrong_unit_is_dropped_not_held` |
| Append reword lane | gates hard-fail, or dropped (`exam_authority`) when the exam citation did not resolve | `test_an_exam_only_append_reword_still_hard_fails`, `test_an_append_reword_citing_exam_material_under_the_wrong_unit_is_dropped_not_held` |
| Registry writer (`Cited` basis: undo, recovery) | `exam_authority`; an unconfirmed reword is `unsupported_reword` | `test_the_registry_writer_refuses_exam_only_meaning_and_an_unconfirmed_reword` |
| The confirm | re-judged: `exam_authority` | `test_a_confirm_whose_support_became_exam_material_is_refused` |
| Consolidation, attach, undo of an exam-only alias join | unchanged (alias only; undo refused) | `tests/test_facet_authority.py` (unchanged, passing) |
| The owner's Library edit | allowed: the explicit override | `test_the_library_stays_the_owners_override_for_exam_wording` |

## 4. Behaviour the owner will notice

- **Accepting a source update no longer fails on a facet reword.** When the
  new wording has no textbook, lecture, paper or reference passage behind it:
  - the rest applies;
  - the reword appears under "Rewords waiting for your confirm" in registry
    review and at the top of the proposals inbox, with the wording now and
    new, and what it cited;
  - the proposal item shows "waits for your confirm".
- **Confirm reword** applies it as your own edit. It is undoable from the
  facet's history, and the history names its sources. **Keep current wording**
  closes it.
- **An uncited reword drawn from an exam-only append** used to be dropped.
  It now reaches you as a confirm that says "It cites no source". The model
  may have drawn it from the exam profile, so keep the current wording unless
  you agree with it.
- **Exam material can never be confirmed into a facet.** A reword resting on
  exam material alone is refused or dropped as before, including:
  - one citing an exam span under the wrong unit;
  - one citing a unit you marked as held out for evaluation.

  Only your own Library edit can put exam wording into a facet.
- **Title and worked-example changes** from a source update apply without an
  explanatory source and show up in the facet's history with what they cited
  (not a new version). An absorbed duplicate's claim now becomes a worked
  example of the registered facet even when it cites nothing; it used to stay
  an alias only.

## 5. Docs

- `spec_source_ingestion_v2.md`:
  - §4.2: the manual-authority paragraph (Library edit or one-tap confirm;
    exam-only never confirmable; held-out units are exam material);
  - §8.7: the chokepoint bullets (exam block with misdeclared citations,
    the confirm path, titles and examples), and "adequate provenance";
  - §10.3: the append restructure policy and registered-id creates.
- `spec_knowledge_model.md` §3.4: the exam-authority bullet (the confirm path,
  presentation fields, the two forms of manual authority).
- `spec_action_router_v1.md` §15:
  - D14 and D15 in the decisions table;
  - §15.5 the "surface gap" signal: a failed canonical or problem-set
    exercise with passed generated surfaces on the same facets; the router
    chooses among more source exercises, a refined facet or condition
    through the confirm path, or hardening the generated family; it needs
    canonical exercises attached as surfaces of the same practice family
    (sources track S1); held-out items never take part;
  - §15.6: exam and problem-set profiles seed difficulty and rigor of PF
    generation and S1 exercise selection, not only families, formats and
    emphasis; held-out units stay excluded.
- `docs/reviews/facet-authority-fixes.md` §11 records the second re-review's
  F7 as rejected (§6 below).

## 6. Second re-review F7: rejected

Codex's verification of the second re-review's fixes (job
`20261013-103557-c11o4C`) reopened F7: "Pre-upgrade interrupted saves retain
permanent authority grants". A Library save by `ddf941d5`'s code, killed
before its write, would keep its `granted` verdicts after migration 197
(built as 186 on this branch; renumbered at the landing, §10.1).

Rejected, with no change. The grant-recording save code exists only on this
unmerged branch, together with migration 197 (its 186), so no vault ever ran
the pre-197 version. Recorded in `docs/reviews/facet-authority-fixes.md` §11.

## 7. Gate

Run on `8351490f` (the fix and the references; only this file changed after),
2026-10-13, with `TMPDIR` set to the worktree's `fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (163 packages resolved; pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 15 contracts kept, 0 broken |
| Fail-first: `tests/test_facet_reword_confirm.py` against `da3d5585`'s `src/` | 39 failed, 3 passed; with the listing helper shimmed, 33 failed, 9 passed (the exam guards) |
| Targeted: facet, proposal, synthesis, append, source, registry, sidecar, doctor, contract and CLI suites (70 files) | 874 passed |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **9,197 passed**, 0 failed, 0 skipped, 46 warnings (the existing fork and deprecation warnings), 467 s (lock taken at once, 11:34); 9,154 at `da3d5585` plus the 42 new tests and the new `decide_facet_reword` allowlist case |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **95 passed**, 9,102 deselected, 1 warning, 114 s (after waiting for the lock, 11:42 to 11:48) |
| `apps/learnloop-tauri`: `npm install`, `npm run typecheck`, `npm test`, `npm run frontend:build` | ok; typecheck clean; vitest 37 files, 192 tests passed; build ok (the existing chunk-size warning) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | ok (`decide_facet_reword` passthrough) |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated (`8351490f`: three shifted config citations in `ops/doctor.py` and `source_set_synthesis.py`, `source_commit` stamps); `errors: []`; schema head 186 (no schema change) |
| `validate_vault.py` | passed (1,086 notes, 21,874 wikilinks/fragments, 4,482 source paths) |
| `module_validate.py` | wikilinks 14,712/14,712, source/test links 11,795/11,795, catalog YAML 508/508; the 539 "missing expected note" issues are unchanged |
| `desktop_validate.py` | not part of the gate; it crashes before validating with `KeyError: 'TypeScript/screens/today'` in `desktop_generate.py` (the `screens/today` folder has no area description). The folder is in `da3d5585`, so this predates the stage. |
| Tracked fixture vaults | untouched and never opened; `git status` clean after the full suite and the durability lane |

## 8. Paid calls

None. Cost $0. Every test uses fakes; no command ran against a vault, and the
tracked fixture vaults (`fixtures/linear_algebra`, `probability`,
`arxiv_v2`) were not opened.

## 9. Open questions for the owner

1. **Exam-only titles and worked examples.** The stage keeps refusing a title
   or worked-example change whose only support is exam material. It reads "it
   applies (if it otherwise passes)" as passing the exam rule too, because an
   exam's worked item copied into a facet's examples would reach teaching and
   generation contexts. Recommended default: keep refusing.
2. **Should a confirm say when its run saw exam material?** An uncited reword
   from an append that added an exam may have been drawn from the exam
   profile. The confirm says "It cites no source" but not that an exam was in
   the run. Recommended default: add a line ("this source update included
   exam material, which never supports wording") when the run's manifest had
   an exam profile.
3. **Doctor and pending confirms.** `learnloop doctor` does not list rewords
   waiting for a confirm, while registry review, the inbox and
   `learnloop facets actions` do. Add an info line?
4. **Attach of an uncited duplicate.** Under rule 3, an absorbed duplicate's
   claim becomes a worked example of a registered facet without a citation.
   It is on the facet's history as the attach action, with its undo. Keep
   that, or hold it for a confirm too?
5. **Re-judging at confirm uses every source set of the vault.** When a span
   is selected in two sets with different roles, the less authoritative role
   wins, so a span that is exam material in any set refuses the confirm.
   Recommended default: keep that (fail closed for exams).

## 10. Landing onto main

Branch `merge/facet-locks-onto-main`, from main `e3aed505` (RW1a, the route
check mvp-0.17 and the sources track mvp-0.18/0.19; migrations 185-195). A
real `--no-ff` merge of `merge/facet-locks` (`5a5e1e8e`, unchanged) as
`7a2e4135`, the composition fix `68408145` (§10.3), references `bbb4363b`,
and this record. No algorithm successor (a content path; owner-consistent).
No paid call.

### 10.1 Migrations

| On `merge/facet-locks` | On main | What |
|---|---|---|
| `185_facet_identity_rewords` (built as 188 on facets/locks-and-depends-on) | **196** | rebuilds `facet_identity_actions` (rows, ids and indexes kept) so its CHECKs accept `action = 'reword'` and `origin IN ('proposal', 'registry')`; the temporary table is now `facet_identity_actions__196` |
| `186_facet_registry_saves` | **197** | adds `facet_registry_saves` (WORKFLOW, no replayer) |

Main's 185 (RW1a), 186 (route check) and 187-195 (sources) keep their
numbers; `migrations/` runs 1..197 with only main's historical gaps (38-39,
42-43, 46, 60, 67, 127-129, 135-137). The numbers 185 and 186 in §0-§9 and in
the branch's other records mean 196 and 197 on main. Head fixture
`fixtures/migration_head_197` (renamed from main's `migration_head_195`; a
backup-API copy with only 196-197 applied through `apply_migrations`,
`wal_checkpoint(TRUNCATE)`, `journal_mode=DELETE`, `integrity_check` ok,
`foreign_key_check` clean); every hard-coded head path (15 tests and the two
reference scripts) and `SCHEMA_HEAD` point at it. A database that ran this
branch's code before the landing would record 185/186 as the facet
migrations and skip main's 185/186; none exists (the owner's vaults run
main's code, and this branch's stages never opened them; §6).

Config: the effective defaults gain only `facet_identity.reword_confirm =
true`, so all eleven `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries (mvp-0.9 to
mvp-0.19) were recomputed. `decide_facet_reword` stays desktop-only in
`tests/test_mobile_allowlist.py`; the CLI help snapshot is unchanged by
`--write`.

### 10.2 The sources track's write paths, checked against the chokepoint

No module of the sources track writes a facet's meaning. Each was read, and
`tests/test_facet_locks_landing.py` pins it structurally: the bypass test
(`test_every_writer_of_facet_meaning_goes_through_the_authority_chokepoint`)
parses all 33 modules, and none names `facets_path` or `"facets.yaml"`,
calls `upsert_facet`, `union_payload`, `write_registry_text`, `OwnerEdit`,
`compile_proposal_item`, `stage_target_contents`, `check_meaning_write` or
`persist_proposal_batch` (the only way a facet item reaches the proposal
compiler), or writes `entity_source_links`.

| Path | Entry points | What it writes | Facets |
|---|---|---|---|
| Exercise imports | `source_exercise_import.import_source_exercise` (CLI `learnloop sources`, sidecar `source_service`, the `source_exercise_import` ingest job, harvest, needs, `record_reader_import`) | `exercise_authoring.write_draft` → `vault.writer.upsert_practice_item` (with `canonical_exercise`); `source_exercise_imports`, `reference_key_checks` rows | references registered canonical facets only (`vault.evidence_facets`; an unknown id is dropped, `lo_fallback` takes the LO's facet union) |
| Key checks and recovery | `verify_item_key`, `resume_import`, `recover_import_checks`, the edit re-check in `handlers/item_authoring.py` | database rows | none |
| Family attachment | `attach_to_matching_family` | activity-family membership proposals (families store) | none |
| Authoring and draft validation | `exercise_authoring.author_exercises`, `draft_validation.py` | nothing (validation) or the import's write | none |
| Practice proposals | `practice_index/retrieval.py` (`insert_proposal`: caller, intent, valuation), `instructional/practice.py` (impressions, selection, delivery, pick) | `practice_index_proposals`, `instructional_impressions`, `retrieval_interventions` rows | none |
| Source-first needs | `instructional/needs.fulfil_need_from_sources` (the primed-retry handler, `learnloop generate-diagnostics`) | an exercise import; otherwise the existing generation lane (`generate_diagnostic_proposal`, authoring proposals whose item types exclude `facet`) | none |
| Harvest and verify | `instructional/harvest.harvest`, `verify` | exercise imports, key checks | none |
| Source comparisons, find_sources, tools | `compare.compare_sources`, `find_sources.find_sources_for_caller`, `instructional/tools.py` | `source_comparisons`, `source_tool_calls` rows; reads `entity_source_links` | none |
| Valuation, exposure, interventions, outcomes | `instructional/valuation.py`, `exposure.py`, `interventions.py`, `substrate/intervention_outcomes.py` | receipts and the DERIVED outcome join | none |
| PF publish and verify | `ops/pf_publish.py`, `ops/pf_verify.py` | practice items (`variant_of` canonical exercises) | none |
| Spend | `source_retrieval/service_spend.py`, `db/stores/source_service.py` | `source_service_spend` | none |
| Upgrade | `sources_upgrade.py` | `algorithm_version` | none |

### 10.3 The two exam predicates

Not unified here (the exam-protection stage makes one). Where each is used:

**A. main's source predicates (`source_retrieval/corpus.py`)**, which decide
what text a model or the tutor receives:

- `exam_exclusions` → `exam_withheld(vault, repository, keys)`: exam-role
  members whole and exam unit overrides (by id in the pinned extraction, by
  label elsewhere; unresolvable means the whole extraction), in every
  extraction of the source (all revisions). Used by
  `tutor.PinnedSpanProvider` (pinned spans, "it is exam material"),
  `find_sources.find_sources_for_caller` (the pool, `manifest.exam_withheld`)
  and `compare.compare_sources` (pins and hits).
- `teaching_exclusions` (a superset: exam, problem-set, notes and
  unknown-role material, every `exercise` / `assessment_alignment` link):
  `teaching_scope` (the tutor's grounding; `find_sources`, `needs`,
  `exposure`, `exercises`), `model_reader_withheld` (`instructional/tools.py`,
  results returned to a model) and `assessment_spans`.

**B. the facet-meaning predicate (`role_authority` + `facet_identity/authority.py`)**,
which decides whether a citation can support a facet's meaning:

- `role_authority.ASSESSMENT_ONLY_ROLES = {exam}`, `support_verdict`,
  `is_semantic_support`;
- `authority.CitationResolver.resolve` (the scope entry's role, else the
  member's; the least authoritative across members and sets; a span in a
  `held_out_evaluation` unit is `exam`) and `exam_material` (an unresolved
  citation that names exam material by its span stays exam);
- used by `check_meaning_write` (every facet writer: `patches._compile_facet`,
  `write_registry_text` with a `Cited` basis, `join_candidate`),
  `actions.confirm_reword` (re-judged), `visible_sources` / `excerpt` (no
  exam text in a confirm card), `synthesis_gates._gate_exam_authority`,
  `_has_semantic_authority` and `_gate_practice_exam_only`,
  `source_set_synthesis._span_refs` and its registered-id check, and
  `source_append._facet_reword` / `_checked_reword`.

**Held-out units.** B counted a `held_out_evaluation` unit as exam whatever
its member's role; A counted it only inside an exam member or an exam unit
override, so a textbook unit held out for evaluation still reached the tutor
and models. Fixed in `68408145` (fail closed, nothing released): both corpus
predicates add every `held_out_evaluation` unit of a member's source (by id
where its selection marks it, by label in the source's other extractions; an
unresolvable id or label withholds the whole extraction; a split child
withholds its raw parent). Tests: `tests/test_facet_locks_landing.py` (4 of
its 6 failed on the merge commit's `corpus.py`).

**Neither weakens the other.** The landing changed no line of B; A only
gained exclusions. `role_authority`'s existing `semantic_contract` table,
which A's teaching rule reads, is unchanged (the branch only added the
support rule beside it).

**Differences left for the exam-protection stage:**

1. *Revisions.* A treats every extraction of an exam source (any revision)
   as exam; B resolves only the member's pinned revision's extractions, so a
   citation into another revision does not resolve, is not `exam_material`,
   and an otherwise-uncited reword resting on it becomes a confirm (shown to
   the owner without excerpt) rather than refused.
2. *Corroboration.* A withholds exam spans regardless of what else is in the
   result; B lets an exam citation stand beside an explanatory one
   (corroborated, `assessment_alignment`).
3. *A third exam test.* `content/authoring/practice_leakage.held_out_spans`
   (the leakage inventory exercise imports and PF generation screen against)
   counts held-out units only inside exam-role units, as before; unchanged
   here.

### 10.4 Gate

Run on `bbb4363b` (the merge, the fix and the references; only this record
and `facet-authority-fixes.md` §11 changed after), 2026-10-13, `TMPDIR` the
worktree's `fixtures-local/tmp`, under heavy machine load (load average
about 20). Nothing failed, so nothing needed a solo rerun.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 17 contracts kept, 0 broken |
| Targeted (120 facet, source, migration, config, upgrade, synthesis, proposal and registry files; the resolved tree with the fix, before committing) | 1,476 passed |
| `tests/test_facet_locks_landing.py` against the merge commit's `corpus.py` | 4 failed (the held-out cases), 2 passed (the guards); 6 passed on the fix |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **9,952 passed**, 0 failed, 0 skipped, 46 warnings (the existing fork and deprecation warnings), 394 s (lock taken at once) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 9,853 deselected, 1 warning, 105 s (after a 6-minute wait for the lock) |
| `apps/learnloop-tauri`: `npm install`, `npm run typecheck`, `npm test`, `npm run frontend:build` | ok; typecheck clean; vitest 54 files, 295 tests passed; build ok (the existing chunk-size warning) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | ok, 0 warnings |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated at schema head 197 (317 table notes, 788 effective leaves; prose counts in `Configuration.md` and `Database.md` fixed by hand); `errors: []` |
| `validate_vault.py` | passed (1,097 notes, 21,981 wikilinks/fragments, 4,603 source paths) |
| `module_validate.py` | wikilinks 14,712/14,712, source/test links 11,795/11,795, catalog YAML 508/508; its 612 issues are all "missing expected note" (the existing kind; the branch recorded 539 before main's new modules) |
| CLI help snapshot, `--write` | unchanged |
| Tracked fixture vaults | `git status` clean after every step |

### 10.5 Parity

Backup-API copies (`copy_tree_with_databases`) of this worktree's tracked
`fixtures/linear_algebra` and `fixtures/probability` (both at migration 155)
into `fixtures-local/facet-locks-parity/{main,merge}/`; the `main` copies run
`e3aed505`'s `src/` and `migrations/` (a `git archive` copy, on
`PYTHONPATH`, the import path checked), the `merge` copies this branch.
Each copy was migrated by opening a `Repository`, then `learnloop rebuild
--shadow --json` and `learnloop doctor` (text and `--json`).

| | linear_algebra main | linear_algebra merge | probability main | probability merge |
|---|---|---|---|---|
| Migrated to | 195 | 197 | 195 | 197 |
| Shadow rebuild | exit 0, live DB unchanged | same | exit 0, live DB unchanged | same |
| Replay | 70 attempts, 11 replayers, 0 unaccounted | identical (after normalizing run-time ULIDs: minted family ids, the marker) | 2 attempts, 11 replayers, 0 unaccounted | identical (same normalization) |
| `learner_state_diff` (facet / mastery / schedule) | 22 / 6 / 47 | identical | 2 / 1 / 1 | identical |
| doctor errors | 1 | 1 (same) | 49 | 49 (same) |
| doctor issues | 105 | 106 | 133 | 134 |
| `criterion:unknown_dependency` | 0 | 0 | **46** | **46** |

- The only doctor difference is the branch's expected warning
  `config:retired_setting` ("learnloop.toml sets retired 'locks'"), once per
  vault.
- **The depends_on work does not change the 46.** Doctor's check is the same;
  the branch stops new synthesis from writing such entries and adds the
  owner-run repair. `learnloop doctor --fix-content --dry-run` on the merge
  copy would remove all 46 entries (28 criteria, 13 items, 1 unreadable
  item, 0 self-dependencies), as recorded in
  `facet-locks-and-depends-on.md` §4. The tracked copy has 46; the owner's
  live vault may differ (48 was reported there).
- probability's other errors (2 `yaml:invalid` for
  `pi_exercise_01kyn22qcffk7sae9ttxvz4j5n.yaml`, 1 `layout:missing_directory`)
  are the same under both.

### 10.6 Open questions for the owner

1. **Held-out units in the leakage inventory.** `practice_leakage.held_out_spans`
   (the leakage screen of exercise imports and PF generation) still counts a
   held-out unit only inside an exam-role unit. Recommended default: leave it
   to the exam-protection stage, which makes one predicate.
2. **Revision scope of exam material for facet citations** (§10.3, difference
   1). Recommended default: the exam-protection stage adopts the corpus rule
   (every revision of an exam source is exam).
3. **The live probability vault's `unknown_dependency` entries.** Run
   `learnloop doctor --vault <vault> --fix-content --dry-run`, then without
   `--dry-run`, when convenient (no grade changes). Recommended default: run
   it.
