# Codex review: the facet reword confirm

Stage `facet-reword-confirm`, branch `merge/facet-locks` (base `da3d5585`;
the stage `b59f5a1a`, references `8351490f`, recorded at `9a0d38e5` in
`docs/reviews/facet-reword-confirm.md`). Owner-directed, 2026-10-13: a reword
without explanatory support waits for the owner's one-tap confirm, and exam
material stays a hard block.

Codex reviewed `da3d5585..merge/facet-locks` (job `20261013-115043-e7WRO0`:
source review and in-memory reproductions; it ran no gate). It found one High
and five Medium defects. All six reproduced as failing tests before the fix.
Five are fixed outright; F6 is fixed by a kill switch, and its request for an
algorithm successor is rejected with the reason below.

- Fix: `d79a24af`. References regenerated: `112094e8`.
- No migration (the branch's 185 and 186 stay as they are; no 189 needed).
- One config key: `facet_identity.reword_confirm = true` (modelled default,
  left out of the decision-only template). All eight defaults snapshots
  (mvp-0.9 to mvp-0.16) were recomputed; each moves only because the
  effective config gains the key.
- The append wire contract (`AppendFacetWording`) gains `title`,
  `positive_examples` and `negative_examples`, and prompt rule 6 says so. The
  `mvp-0.10-append-*` prompt versions were introduced on this unmerged branch,
  so no completed run or cached shard carries them, and they keep their names
  (as at the facet-locks review).
- No RPC, frontend or `src-tauri` change: the confirm card already renders
  every entry of `changes` and hides an `assessmentOnly` source's text.
- No paid call.

## Review

### Findings

| ID | Severity | Title | Verdict | Commit | Test (fail-first on `9a0d38e5`) or reason |
|---|---|---|---|---|---|
| F1 | High | Absorbing a mis-cited exam candidate bypasses the authority block | fixed | `d79a24af` | `test_an_attach_absorbing_an_exam_span_cited_under_the_wrong_unit_never_grows_the_facet` (end to end: append producer, identity judge, gates, compiler); `test_an_in_run_consolidation_never_takes_exam_meaning_cited_under_the_wrong_unit[merge / absorb-precondition / absorb-example]` |
| F2 | Medium | Confirmation silently overwrites intervening alias edits | fixed | `d79a24af` | `test_a_confirm_keeps_an_alias_added_since_when_the_reword_adds_one_too`, `test_a_confirm_keeps_error_signatures_and_repairs_changed_since`, `test_a_confirm_refuses_a_conflicting_change_it_cannot_merge` |
| F3 | Medium | Reclassified exam sources retain visible cached excerpts | fixed | `d79a24af` | `test_a_pending_confirm_hides_a_sources_text_once_its_member_is_an_exam` (pending list, registry review, the sidecar inbox, `describe`, the facet history), `test_a_pending_confirm_hides_a_sources_text_once_its_unit_is_held_out` |
| F4 | Medium | Confirmed rewords never install their authoritative provenance links | fixed | `d79a24af` | `test_a_confirmed_reword_installs_its_source_links`, `test_an_interrupted_confirm_installs_its_source_links_on_recovery` (both read `get_entity_provenance`) |
| F5 | Medium | The append producer cannot deliver title or example-only updates | fixed | `d79a24af` | `test_an_append_title_update_applies_without_a_new_version[facet_wording / loose_payload]`, `test_an_append_worked_example_update_applies_without_a_new_version`, `test_the_append_schema_lets_a_provider_send_a_title_and_worked_examples` |
| F6 | Medium | Admission behaviour changes without a successor or kill switch | fixed in part (kill switch); rejected in part (algorithm successor) | `d79a24af` | `test_with_the_kill_switch_an_unsupported_change_is_refused_at_accept_not_held[claim / title]`, `test_with_the_kill_switch_the_append_lane_drops_an_uncited_reword`, `test_with_the_kill_switch_an_uncited_absorbed_example_joins_as_an_alias_only`, `test_with_the_kill_switch_a_reword_held_earlier_can_still_be_decided`, `test_the_policy_follows_the_switch`. Successor rejected: content admission, nothing persisted changes meaning (below) |

All tests are in `tests/test_facet_reword_confirm_review.py` (21).

**Fail-first.** The 21 tests were written and run before the fix, then again
against `9a0d38e5`'s `src/` and `migrations/` (a `git archive` copy under
`fixtures-local/tmp`, with `-o pythonpath=` pointing at it; a probe test
confirmed `learnloop` and `learnloop_sidecar` were imported from the copy):
**21 failed**. Each failure is the defect, not a setup error:

- **F1**: the attach row carried the exam claim as a worked example
  (`'positive_examples' in {... 'positive_examples': ['On the final exam,
  ...']}`), with no `exam_authority` diagnostic and no hard fail. In-run, the
  exam claim and the exam-only precondition joined the textbook survivor
  under all three consolidations.
- **F2**: aliases `['original', 'later']` became `['original', 'proposed']`;
  error signatures `['forgets the transpose']` became `['swaps U and V']`; a
  status changed both ways was overwritten (`DID NOT RAISE`).
- **F3**: after the notes member was re-marked `exam`, and after its unit was
  held out for evaluation, the pending confirm still returned the notes
  excerpt.
- **F4**: after the confirm, `entity_source_links` had no row for the cited
  span, though facets.yaml recorded it.
- **F5**: `facet_wording.title` was refused by the strict wire model
  (`extra_forbidden`); a loose-payload title was dropped as "carries no new
  wording".
- **F6**: `facet_identity.reword_confirm` did not exist (`AttributeError`),
  nor did `authority.meaning_policy`.

### F1: a retired candidate's unresolved citations travel with its contribution

`_normalize` kept a candidate's unresolved citations in
`candidate["unresolved"]` but built the contribution an attach or in-run
consolidation joins from `candidate["support"]` alone. An exam span named
under the wrong unit therefore arrived "uncited": the presentation exemption
let it grow a registered facet's examples, and a new survivor took its claim
and conditions.

`_joined_contribution` now gives both joins the candidate's validated and
unresolved citations. The chokepoint's `exam_material()` sees the unresolved
exam citation, the join is refused (`exam_authority`), and the candidate joins
as an alias only, with a review diagnostic naming the facet. An unresolved
citation that is not exam material still supports nothing, so nothing else
changes: an uncited new survivor is `new_unsupported` as before, and an
uncited absorbed example of a registered facet is still a presentation change.
A new facet's own unresolved citations are unchanged (still the
`adequate_provenance` review); the finding and the fix are about joins.

### F2: a confirm merges three ways

`_confirmed_entry` took every field the held reword changed. Now, for each
such field:

- the facet still holds what the reword found: the reword's value;
- the facet already holds the reword's value: unchanged;
- a list both changed (aliases, error signatures, repairs, tags): today's
  items, less what the reword removed, plus what it added;
- anything else both changed differently: a conflict. The confirm is refused
  (`changed_since`, naming the field), and nothing is recorded. Keeping the
  current wording still works.

The wording fields cannot conflict, since a confirm whose wording changed
since is already refused. The confirm card now lists every field the confirm
writes (`changes`: the wording fields first, then anything else the reword
changes), so the owner sees an alias change before confirming it.

### F3: excerpts are read when shown

A held reword no longer stores span text (`authority.source_views` keeps ids,
role and locator). `authority.visible_sources` resolves each recorded source
again when a view is built, with the vault's roles and held-out selections of
that moment:

- it resolves to material that is not assessment-only: today's role and an
  excerpt;
- it is exam material now (member re-marked as an exam, unit held out, or
  named under the wrong unit): role `exam`, `assessment_only`, no text;
- it no longer resolves for another reason (unit deselected): no text;
- no resolver (a view built without the repository): no text (fail closed).

`pending_reword_confirms` (registry review, the proposals inbox) and
`facet_history` (the facet inspector) build one resolver per listing;
`describe` and `confirm_view` take one. The confirm itself was already
re-judged with today's roles and refuses such a reword (`exam_authority`).

### F4: a confirm installs its source links write-ahead

The confirm validates the citations it records again with today's resolver
(`authority.written_provenance`), and the ones that resolve become
`entity_source_links` rows (`authority.added_provenance`, the proposal
apply's rule; `apply_protocol.entity_source_link_rows`, fixed ids, the
proposal's id as `patch_id`, relations as resolved: `support`, or
`assessment_alignment` for exam material). The rows are recorded in the
action's intent (`detail.source_links`) in the same transaction as the
owner's verdict and the save intent, then installed in the transaction that
marks the action and the save `applied`. Recovery of a confirm whose file
write landed installs them in the transaction that marks it `applied`.
Inserts are `INSERT OR IGNORE` on fixed ids and the table's unique key, so a
second pass changes nothing (tested). A confirm that never lands installs
none. As with any reword, an undo leaves the links (the table is a raw
ledger; recorded at the facet-locks review).

### F5: the append lane carries the title and worked examples

`AppendFacetWording` gains `title`, `positive_examples` and
`negative_examples`. `_facet_reword` copies every `authority.AUTHORITY_FIELDS`
field from `facet_wording` or the loose payload and detects a change with
`authority_changes`, so a title-only or examples-only update is no longer
dropped as "carries no new wording". The compiler still decides the version
(`meaning_changes`): such an update applies uncited (verdict `presentation`),
is not a version, and is on the facet's history with its undo. Tested through
the append producer and its strict wire model, not by inserting proposals.

### F6: a kill switch, no algorithm successor

**Fixed: the kill switch.** `facet_identity.reword_confirm` (default `true`)
selects the chokepoint's admission policy (`authority.meaning_policy`):

- `true` (`REWORD_CONFIRM`): the stage's rule.
- `false` (`EXPLANATORY_ONLY`): the predecessor rule. A registered facet's
  meaning, title and worked examples change only with an explanatory citation
  in every contribution, and a change without it is refused, never held
  (`check_meaning_write` returns `unsupported_reword` with the predecessor's
  message and `confirmable` false). The compiler raises at accept as before.
  The producers drop what it would refuse: the append reword lane
  (`facet_restructure` review diagnostic), bootstrap and append registered-id
  candidates (as before the stage), and an attach's uncited absorbed example
  (alias only).
- Exam-only support is refused under both.
- Rewords already held stay decidable: the owner's confirm is manual
  authority, so it judges with `REWORD_CONFIRM` whatever the switch
  (exam-only still refuses it), and keep works as before.

`MeaningVerdict.confirmable` is now a field the policy sets, not a property of
the code. Predecessor and successor are each tested through the compiler, the
append producer and the attach path, and directly at the chokepoint.

**Rejected: an algorithm successor and its rebuild validation.**

- The playbook's trigger is a change that "alters persisted meaning"
  (scoring, scheduling, projection, or the admissibility of evidence), and it
  versions how persisted history is interpreted on replay. This change decides
  which proposal writes reach `facets.yaml` at accept time (or wait for the
  owner). Replay never runs a proposal apply, a producer or a confirm, and no
  module this stage or this fix touches is read by replay or projections, so
  every recorded attempt, evidence row and projection means what it meant.
  Two binaries agree on every derived table for the same vault content.
- Facet content then reaches serving only as vault content, like any accepted
  proposal: the same path as a Library edit, which needs no version.
- The repository's precedents are consistent. Facet identity (merges at
  ingest), PF-b ("publishing verified items is a content change, gated by its
  own kill switch, not an algorithm successor"), the T6 follow-up (Codex F7
  rejected for the same reason), the facet-locks removal and the facet
  authority chokepoint were each Codex-reviewed with a kill switch or none,
  and no successor.
- The owner's standing decision (2026-10-12) is live changes behind kill
  switches, with no shadow stages by default.
- Playbook step 7's shadow rebuild validates a new version's replay against
  a copy. With no version and no replay change there is nothing for it to
  compare, so none was run.

The defaults snapshots record the new key, as every content kill switch
before it did (`config/template.py`).

### Claims in the stage record, corrected

`docs/reviews/facet-reword-confirm.md` now points here for each:

- "Exam-only support is refused on every write path": true only after F1.
- "An alias added to the facet since stays": now true even when the reword
  changes the aliases too (F2), and a conflict refuses the confirm.
- "A confirm never shows exam text": now true after a source is reclassified
  (F3).
- "Title and example changes from source updates apply": now true for the
  append producer (F5).
- "No algorithm successor: a content path": stands, now with a kill switch
  (F6). "No config change" no longer holds.

### Behaviour the owner will notice

- A source update whose duplicate facet rests on an exam span the model cited
  under the wrong unit no longer adds that wording as a worked example: the
  duplicate becomes an alias, and the review says why.
- **Confirm reword** keeps what you changed on the facet since (aliases, error
  signatures, repairs) and adds the reword's own. If you changed a field the
  reword also changes in a way that cannot be merged, the confirm says so and
  changes nothing.
- The confirm card lists everything it will write, an alias included.
- A source you re-mark as an exam, or a unit you hold out, stops showing its
  text on a waiting confirm at once.
- After a confirm, the facet's sources panel lists the passages the reword
  cited.
- A source update can now change a facet's title or worked examples on its
  own.
- `[facet_identity] reword_confirm = false` in `learnloop.toml` turns the
  confirm path off: such rewords are refused or dropped again.

## Gate

Run on `112094e8` (the fix and the references; only the two review files
changed after), 2026-10-13, with `TMPDIR` set to the worktree's
`fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (163 packages resolved; pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 15 contracts kept, 0 broken |
| Fail-first: `tests/test_facet_reword_confirm_review.py` against `9a0d38e5`'s `src/` | 21 failed (probe confirmed the copy was imported) |
| Targeted: facet, proposal, synthesis, append, source, registry, config, template, contract, doctor, provenance, sidecar, CLI and reference suites (122 files) | 1,496 passed |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **9,218 passed**, 0 failed, 0 skipped, 46 warnings (the existing fork and deprecation warnings), 312 s (queued 12:33, lock 12:36, done 12:42); 9,197 at `9a0d38e5` plus the 21 new tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **95 passed**, 9,123 deselected, 1 warning, 97 s (queued 12:42, lock 12:47, done 12:49) |
| Frontend (`npm install`, `typecheck`, `test`, `frontend:build`) | not run: nothing under `apps/` changed |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated (`112094e8`: the `facet_identity.reword_confirm` row, 759 effective leaves, the two hand-written prose counts in `Configuration.md` and `Database.md`, and `source_commit` stamps); `errors: []`; schema head 186 (no schema change) |
| `validate_vault.py` | passed (1,086 notes, 21,874 wikilinks/fragments, 4,483 source paths) |
| `module_validate.py` | wikilinks 14,712/14,712, source/test links 11,795/11,795, catalog YAML 508/508; the 539 "missing expected note" issues are unchanged (pre-existing) |
| Tracked fixture vaults | untouched and never opened; `git status` clean after the full suite and the durability lane |

## Paid calls

None. Cost $0. Every test uses fakes; no command ran against a vault, and the
tracked fixture vaults (`fixtures/linear_algebra`, `probability`, `arxiv_v2`)
were not opened.

## Open questions for the owner

1. **F6: version the admission rule?** Rejected here as content admission
   (above). If you want admission rules versioned, it is a new tag at landing
   (the next free after main's mvp-0.17) with the switch as its kill switch.
   Recommended default: keep it a content kill switch, like the earlier facet
   stages.
2. **F2: a conflict refuses the confirm.** A field other than a list (status,
   concept) that both the reword and a later edit changed refuses the confirm,
   rather than picking a side. Recommended default: keep refusing (keep the
   current wording, or re-run the source update).
3. **F3: a waiting confirm whose source became exam material** still shows
   its card (text hidden, role "exam") and a confirm button, which the
   re-judgment refuses (`exam_authority`) with a plain message. Recommended
   default: keep the card, so the owner can close it with keep current
   wording.
4. **F4: links after an undo.** Undoing a confirmed reword leaves the source
   links it installed, as undoing any reword does (`entity_source_links` is a
   raw ledger). Recommended default: keep.

## Re-review

Codex re-reviewed `9a0d38e5..merge/facet-locks` (through `b5a6af01`; job
`20261013-125019-aiThKm`: static review and guarded in-memory checks, no
filesystem-backed or durability suites). It confirmed F1 to F5 fixed, found no
new defects in the fix commits, and reopened F6: the kill switch works, but
"the required successor and isolated rebuild validation remain absent", and
the rejection "does not establish an exception to handoff §0's serving-change
requirement" (`docs/specs/implementation_handoffs.md` §0 rule 5: "A change to
what is served is an algorithm successor with a kill switch, checked by a
shadow rebuild on a backup-API copy").

This step runs the isolated rebuild validation, which was missing, and rejects
the successor again. This time the reason rests on what rule 5 covers, as the
specs that state it define it. No code changed: no migration, no config key, no
RPC, frontend or `src-tauri` change, and no paid call.

### Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Absorbing a mis-cited exam candidate bypasses the authority block | confirmed fixed by Codex | `d79a24af` | no action |
| F2 | Medium | Confirmation silently overwrites intervening alias edits | confirmed fixed by Codex | `d79a24af` | no action |
| F3 | Medium | Reclassified exam sources retain visible cached excerpts | confirmed fixed by Codex | `d79a24af` | no action |
| F4 | Medium | Confirmed rewords never install their authoritative provenance links | confirmed fixed by Codex | `d79a24af` | no action |
| F5 | Medium | The append producer cannot deliver title or example-only updates | confirmed fixed by Codex | `d79a24af` | no action |
| F6 | Medium (reopened) | Admission behaviour changes without a successor (and its rebuild validation) | **rejected** (the successor); the isolated rebuild validation is now run and shows zero delta | this commit (record only) | Shadow rebuilds on backup-API copies of all three tracked fixtures: predecessor, switch on and switch off agree exactly (below). Successor: rule 5 covers changes to the rule that serves, not content writes the rule reads, in the specs that state it (below) |

### F6: reproduction

The finding reproduces as stated. At `b5a6af01`, `SUCCESSOR_CHAIN` still ends at
`mvp-0.16` (the stage left it unchanged), and the review recorded that no
shadow rebuild had been run. This is a process requirement, not a behaviour
defect, so no test can fail on it. What can be checked is rule 5's rebuild,
and that is run below.

### F6: the isolated rebuild validation (now run)

**Method.**

- **Copies.** Backup-API copies (`learnloop.db.copies.copy_tree_with_databases`)
  of the worktree's three tracked fixtures (`linear_algebra`, `probability`,
  `arxiv_v2`), under `fixtures-local/f6rebuild/`.
- **Migration.** Each copy was migrated to schema head 186 with
  `db.migrate.apply_migrations`: 155 → 186 for `linear_algebra` and
  `probability`, 152 → 186 for `arxiv_v2`. The stage added no migration, so
  the predecessor and HEAD share that head.
- **Runs.** `learnloop rebuild --shadow --json` ran four times on each copy:
  1. HEAD (`b5a6af01`) with the copy's own config (the switch at its default,
     `true`);
  2. HEAD with `--set facet_identity.reword_confirm=false` (the kill switch);
  3. HEAD with `--set facet_identity.reword_confirm=true`;
  4. the predecessor `da3d5585` (the commit before the stage).
- **The predecessor's code.** A `git archive` of `da3d5585`'s `src/` and
  `migrations/` under `fixtures-local/tmp/f6pre`, put first on `PYTHONPATH`. A
  probe confirmed what was imported: `learnloop.__file__` resolved to the
  archive, and its `authority` module has no `meaning_policy`.

**Results.**

| Copy | Version | Replayed attempts | Rebuilt LOs | Unaccounted | Live vs replay rows (facet / mastery / schedule) | Four runs identical | Live DB sha256 (before = after) |
|---|---|---|---|---|---|---|---|
| `linear_algebra` | `mvp-0.8` | 70 | 8 | 0 | 22 / 6 / 47 | yes | `6d1927bb41eaa035…` |
| `probability` | `mvp-0.8` | 2 | 1 | 0 | 2 / 1 / 1 | yes | `f849f97f09919223…` |
| `arxiv_v2` | `mvp-0.8` | 3 | 3 | 0 | 2 / 34 / 3 | yes | `ae51cfff9e293730…` |

- **The diff rows are the baseline gap, not the stage.** They compare the
  projections stored in each fixture's committed `state.sqlite` with a replay
  today. The predecessor reports the same rows with the same values, so the
  stage and its switch add zero mastery, facet and schedule delta.
- **What differs between runs.** Only the surrogate ULIDs the replay mints:
  the shadow marker id and the replayed family ids. Playbook step 6 ignores
  these.
- **Live databases.** Each copy's database hash is the same before and after
  its four runs, and every run reported `live_database.unchanged: true`.
- **Tracked fixtures.** The worktree's fixtures were opened only by the copy,
  and `git status` stayed clean.

**The served set, statically.**

- **Where the switch is read.** Only through `authority.meaning_policy`,
  which is called in four places, all content writers:
  - the proposal compiler (`content/proposals/patches.py:557`);
  - bootstrap, consolidation and attach (`content/synthesis/source_set_synthesis.py:940`
    and `:1100`);
  - the append producer (`content/synthesis/source_append.py:884`).
- **Serving code doesn't call it.** No module under `scheduling`,
  `daily_plan`, `substrate`, `placement`, `router`, `learner`, `attempts`,
  `goals`, `diagnosis` or `field` calls these functions.
- **Changed modules the serving code loads.** In a fresh interpreter, importing
  the scheduler, the daily plan, the rebuild orchestrator, placement, the
  router and both graders loads only three of the stage's changed modules:
  - `config.schema` and `config.template`: the new key;
  - `db.stores.facet_identity`: a docstring and `update_action`, a writer only
    the confirm calls. These consumers use `settled_merge_rows`, which is
    unchanged.
- **The one static import chain** from those packages to the authority module
  is `attempts.attempts` → `content.proposals.proposals`
  (`maybe_promote_self_tagged_fatal_error`). That function queues a
  `review_required` rubric proposal and never compiles a facet item.
- **What does change.** Grading and tutor prompts read a facet's wording from
  `facets.yaml`. A confirmed reword, or an uncited title or example change,
  therefore changes the text they read, as a Library edit or an
  explanatory-cited reword already does. That is a content change, the
  category the specs below keep out of rule 5.

### F6: why the successor is still rejected

The first rejection argued from the playbook's trigger, persisted meaning.
The re-review is right that this did not answer rule 5. But the specs that
state rule 5 also say what it covers, and each one keeps content writes
outside it:

1. **Slice A §0.3.** This is the spec whose owner decision 2 is "each serving
   change is its own algorithm successor". It says: "Publishing verified PF
   items is a content change, like writing a card, not an algorithm change."
   That holds even though publication puts new items in the queue. PF-b
   shipped that way: kill switch `pf.generation_enabled`, no successor
   (`docs/reviews/slice-a-phase-5a.md`).
2. **The handoff itself, in the same document as rule 5.**
   - **The facet identity prompt.** Merge and absorb ("a special case or
     worked instance becomes an example or precondition of the general
     facet") "apply live", behind kill switch `facet_identity.enabled`. It
     adds: "If merging facets changes evidence projections, follow the
     algorithm-change playbook, but a vault-content merge the owner can undo
     is the expected shape." The one automatic difference this stage makes is
     of that class: a registered facet's title or worked examples grow
     without an explanatory citation, on the facet's history with an undo.
     A meaning change without explanatory support is still never written
     without the owner's tap.
   - **Learner-text gaps (§4).** A missing prerequisite's concept, LO, edge
     and seeded practice item are "created live … behind a kill switch". Only
     bringing a check forward "changes scheduling, so it ships as an algorithm
     successor". As merged, `algorithm_versions.py` (`mvp-0.16`) says the
     same: "The rest of the pipeline (names, matches, edges, created
     prerequisites, holding-pen sightings) is a live change behind its own
     switches, not version-gated."
3. **Daily loop §11, the successor table.** "Capture adoption | None:
   content, like writing a card" and "Reader presets through adoption | None:
   content path". Each has a kill switch only.
4. **Reader workbench §3.** "Tier-2 inputs to content … take no successor. A
   tier-2 signal that changes serving, such as … feeding Phase 6's fast-track
   rule or reading paths steering the plan, is an algorithm successor."

Across these, a serving change alters the rule that chooses, schedules or
projects: the plan, the queue, fast-track, probe ties, placement, check
dates. A content write that the rule then reads is gated by a kill switch,
not a version. This stage changes which facet writes reach `facets.yaml`, and
makes a meaning change without explanatory support wait for the owner's tap
instead of being refused. The validation above shows the rule side unchanged.

A successor here would put a version gate in front of a content writer:

- **It would delay what the owner asked for.** Every vault below the tag
  (all of the owner's vaults, at `mvp-0.9` to `mvp-0.16`) would keep refusing
  such rewords until `learnloop upgrade`. That is the shadow-stage shape the
  owner's standing decision rules out ("live changes behind kill switches, no
  shadow stages by default"; handoff §0 rule 7: "Prefer decisive live changes
  behind kill switches over shadow stages"). And it would apply to the change
  the owner asked for in this stage.
- **It would version nothing that replay reads.** Replay and rebuild never
  consult the policy (above), so two versions would replay the same vault
  identically.
- **It wouldn't add an audit trail.** Each write the new policy admits is
  already identifiable on the facet's history:
  - an uncited title or example change is a `reword` action with
    `detail.presentation = true` and its `sources` (each with its role);
  - a held reword is a `proposed` reword;
  - a confirm appends the owner's `granted` verdict to `judgment_ledger`.

The kill switch restores the predecessor exactly, and is tested through the
compiler, the producers and the attach path (`d79a24af`). Open question 1
stands: the owner may still ask for a tag at the checkpoint, and it would be
the next free tag after `main`'s `mvp-0.17` at landing.

### Noticed, not changed: `lint-imports` never sees `learnloop.content`

While trying to pin F6's boundary as an import contract, I found that
`src/learnloop/content/` has no `__init__.py`, on this branch and on `main`.
It is a namespace package, so grimp leaves its 72 modules out of the graph
(`grimp.build_graph("learnloop")` has no `learnloop.content.*` module).

- **The effect.** The four contracts that forbid `learnloop.content`
  (`pyproject.toml` lines 91, 115, 141 and 221: "Persistence and AI stay below
  domain policy", "Router R1 logging…", "Project understanding M1…",
  "Primitive modules stay dependency free") cannot detect an import of it.
- **The test.** A contract that forbade
  `learnloop.content.facet_identity.authority` stayed KEPT with a direct
  import planted in `scheduling/scheduler.py`. The probe was reverted.
- **Why it is not fixed here.** The gap predates this branch, and adding the
  `__init__.py` could break contracts across the codebase, so it is outside
  this stage (open question 5).

### Open questions for the owner (added)

5. **`learnloop.content` is invisible to the import contracts** (above).
   Recommended default: add `src/learnloop/content/__init__.py` in a separate
   change and fix or explicitly ignore whatever the four contracts then
   report.

### Re-review gate

Run on `b5a6af01`'s code, 2026-10-13, with `TMPDIR` set to the worktree's
`fixtures-local/tmp`. This step changed only these two review files.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (163 packages resolved; pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 15 contracts kept, 0 broken (the probe contract was reverted before this run) |
| Shadow rebuilds (F6): 3 copies × 4 runs | 12 runs, all exit 0; per copy, the four runs are identical apart from replay-minted ULIDs, and the live DB hash is unchanged |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **9,218 passed**, 0 failed, 0 skipped, 46 warnings (the existing fork and deprecation warnings), 327 s (queued 13:03:54, lock 13:03:54, done 13:09:25) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **95 passed**, 9,123 deselected, 1 warning, 95 s (queued 13:09:25, lock 13:14:39, done 13:16:16) |
| Frontend (`npm install`, `typecheck`, `test`, `frontend:build`) | not run: nothing under `apps/` changed |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `db_generate_reference.py` / `db_validate_reference.py` | not run: no schema or config change since `112094e8` |
| Tracked fixture vaults | the worktree's copies were opened only by `copy_tree_with_databases`; `git status` was clean after the copies, the rebuilds, the full suite and the durability lane. The owner's checkout was never touched |

### Paid calls (re-review)

None. Cost $0. Shadow rebuilds make no model or embedding call.
