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
