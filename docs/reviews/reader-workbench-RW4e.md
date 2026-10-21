# Reader workbench RW4e: instructional roles (stage `reader-rw4e`)

Branch `reader/rw4e` (worktree `learnanything-rw4b`), base `main` at
`a12ba5ba9` (the RW4d landing; migration head 215; AD1, RW2b+H3, RW1c, RW4b,
DL2 (successor mvp-0.29), RW3b and RW4d on main). Spec:
`docs/specs/spec_reader_workbench_v1.md` §1's RW4e line, §7.9 in full, §7.1
(roles: ingest decides exclusions, proposals add detail), §3.4 item 14 (the
object-type mapping), §6.2 item 2 (RW3b's contrast lists), §11 (`[roles]`),
§12's row, §14 G44 and G19, §15's test list; UX
`docs/specs/ux_reader_workbench_v1.md` §4.5 (role labels on hits, "model's
label" for a proposal). Read: `reader-workbench-RW4d.md` §9 note 1 (write
through `reader/source_objects.py`; never a version of a kept claim),
`reader-workbench-RW3b.md` (the judge already returns per-passage roles with a
confidence and keeps them on its links).

## 0. Plan (written before the code)

**Scope.** RW4e only: the optional per-passage `roles` field of the Reader's
two judges (the library organizer, route `library_organizer`; the cue judge,
route `passage_cue_judge`) written as source-object proposals; the owner-run
batch labeller `learnloop reader label-roles --source <id> [--dry-run]` (route
`role_labeller`); the positive uses: the sources spec's `find_sources(roles=…)`
and its intent lists read the proposals as well as `role_hint`, RW3b's
contrast list prefers `contrast` / `counterexample` passages, and library
answers group by role with "model's label" for a proposal. Not here: P3's
review path (unchanged; nothing promotes a proposal), `source_rerank` /
`source_compare` returning roles (the sources spec's §18 request; recorded as
an open item), RW7a's path judge.

**No migration, no new table.** Proposals go into `source_objects`,
`source_object_versions`, `source_object_citations` (094, RAW_LEDGER) through
`reader/source_objects.py`'s proposal path (`author_source_object`, plus a new
`append_proposal_version` for a second judge's agreement). No table role,
replayer, head fixture or reference schema change.

**The proposal** (`src/learnloop/reader/source_roles.py`, new): one
`source_objects` row per span and role; `object_type` by §3.4 item 14
(`worked_example` → `worked_example`, `exercise` → `problem`, `definition` →
`definition`, `theorem` → `claim`, everything else → `motif_or_passage`);
`authorial_role` the role; `content_json` = `{kind: "instructional_role",
role, confidence, judge, ledger_id, prompt_version, model}`; `authorship =
'ai'`, `status = 'proposed'`, the reading's `revision_id`; one citation (span,
block content hash, revision); `exact_text` empty (the citation points at the
passage; nothing is copied). A **second judge** proposing the same role on the
same passage (same revision, span and block hash) appends a version carrying
its own confidence, judge and ledger id, so agreement is visible; the same
judge again writes nothing (idempotent). Before any write, the one exam
predicate (`exam_material(...).withheld`) is asked about every passage: exam
or held-out passages are never proposed (fail closed: an unreadable predicate
proposes nothing). A kept comparison's claim (RW4d) is never versioned: role
proposals are their own objects.

**Readers** (`visible_role_proposals`, `best_roles`): head versions only
(`proposed` / `reviewed`), resolved to the current reading through the one
alias authority (`CitationResolver`), with every object RW4d's
`hidden_source_objects` hides left out (exam or held out now, fail closed),
and nothing at all while `roles.positive_filter_enabled` is off. A passage's
confidence is its best judge's; `low` counts only when nothing better exists.

**Judges** (no extra call):
- *Cue judge* (`passage_cues.judge_target`): its schema and prompt are
  unchanged (it already returns `roles` with confidences); with
  `roles.on_demand_enabled` every judged passage's roles become proposals
  (judge `passage_cue_judge`, its ledger row's id). Its parsing tolerates a
  missing or malformed `roles` field (a before-validator that changes no JSON
  schema, so the request hash, ledger ids and prompt stay `a12ba5ba9`'s).
- *Library organizer* (`library_ask.organize`): off, RW4a's `library_organizer.v1`
  request exactly (its `roles` are names, kept on the row only). On, the
  `library_organizer.v2` request: the same instructions with roles as optional
  output, each with a confidence, parsed tolerantly; the notes keep `roles` as
  names (the UI is unchanged) and every judged passage's roles become
  proposals (judge `library_organizer`).

**Batch labeller** (`src/learnloop/source_retrieval/role_labeller.py`, new;
CLI `learnloop reader label-roles`): the source's blocks in reading order,
without page furniture and headers, and without anything a model may not read
(RW3b's `protection`: T6's teaching exclusions and the held-out partition;
`model_reader_withheld`: solutions and assessment lanes); passages a
`role_labeller` proposal or ledger row already covers are skipped (resumable);
listwise batches through `judge_listwise` (route `role_labeller`, ledger task
`instructional_roles`), one call each; `roles.batch_max_cost_usd` (5.00, per
run) checked **before each batch call** against what the run has spent plus
that batch's estimate (metered; a subscription route is `estimated_only`, as
every Codex role), and held by the run's `SpendBudget` too. `--dry-run`: zero
calls and zero writes; the batch plan, the route, estimated tokens and
dollars, the cap and the batches that would be capped. Never on the reading
hot path (no RPC). `LEARNLOOP_ROLE_LABELLER_MODELS=off` in the test suite.

**Positive uses** (gated by `roles.positive_filter_enabled`):
- `search_spans(roles=…)` (`corpus.role_proposal_keys`) and
  `find_sources.source_object_lists` read `visible_role_proposals`; off, RW4e
  proposals are ignored entirely (both by role and by their mapped type).
- RW3b's `contrast_list` gets RW4e's `contrast` / `counterexample` proposals
  through `source_object_lists(..., "remediate")` (off: only the judge's own
  link roles, as at `a12ba5ba9`).
- Library answers: a main hit whose ingest role is ordinary prose and that
  has a proposal is grouped by its proposed role (Foundation, Explanation,
  Contrast, Worked example, Prerequisite, Application, Exercise) and carries
  `proposed_role {role, confidence, label: "model's label"}`; the Reader shows
  "counterexample · model's label" in the hit's locator.
- **Never to exclude** (G44): `teaching_exclusions`, `item_exclusions`,
  `model_reader_withheld` and the item-bound scopes read no proposal; a
  proposal never admits a block into an item-bound scope and never removes one
  from an exclusion.

**Config.** `[roles] on_demand_enabled = true`, `positive_filter_enabled =
true`, `batch_max_cost_usd = 5.0`, and the route `ai.routing.role_labeller`
(empty = the active provider); modelled defaults, classified in the parameter
registry; every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry recomputed with a "no
scoring, scheduling, projection or serving change" note. **Successor:** none
(labels on sources).

**Report.** `learnloop reader report` gains `roles`: proposals by role and by
judge, and agreement (passages two judges proposed the same role for).

**Tests** (fakes only): `test_source_roles.py` (G44: the proposal shape, the
type mapping, the version-on-agreement rule, idempotence, held-out spans never
proposed and never returned, exclusions and item-bound scopes unchanged by a
proposal, a table diff), `test_label_roles_cli.py` (dry-run: zero calls, zero
writes, the plan and the cap; the cap checked before each batch; resume),
`test_roles_judges.py` (the roles field in both judges, present / absent /
malformed, with fakes; find_sources' roles matching proposals and role_hint
with the low-confidence rule; RW3b's contrast preference; library grouping),
`test_roles_switch_off.py` (a golden recorded on `a12ba5ba9`: library answer,
notes, cue discovery, find_sources; with both switches off and proposals
present the tip answers the same bytes), the registry classification of every
`roles.*` key, and the RW4b statement-reader and RW4d source-object pins in
every gate (`test_library_exercises.py`, `test_source_objects.py`, the RW4d
files).

## 1. What was built

### 1.1 The proposal (`src/learnloop/reader/source_roles.py`, new)

- **One vocabulary**: `ROLES` (the twelve roles of §7.9), `CONFIDENCES`, the three judges (`library_organizer`, `passage_cue_judge`, `role_labeller`); `RoleProposal` (the wire model, moved here from `passage_cues.py` with the same name and fields, so RW3b's JSON schema is unchanged: its hash is pinned to `a12ba5ba9`'s); `RS.ROLES` is `library_ask.ROLES`.
- **`propose_roles(vault, repository, claims, judge=…, prompt_version=…, model=…)`**: each `{extraction_id, span_id, role, confidence, ledger_id}` becomes one `source_objects` row with one version through `reader/source_objects.py` (`author_source_object`): `object_type` by §3.4 item 14 (`object_type_for`: worked_example → worked_example, exercise → problem, definition → definition, theorem → claim, all else → motif_or_passage), `authorial_role` the role, `content_json = {kind: "instructional_role", role, confidence, judge, ledger_id, prompt_version, model, extraction_id}`, `model_provenance_json` the judge, ledger id, prompt version and model, `authorship = 'ai'`, `status = 'proposed'`, the reading's `revision_id`, `exact_text` empty, one citation (span, block content hash, revision). Malformed claims and passages that do not exist are skipped with a reason; nothing raises.
- **Agreement is a version.** A second judge proposing the same role on the same passage (same revision, span and block hash) appends a version to the existing object (`source_objects.append_proposal_version`, new, the proposal path's second writer: AI authorship, `proposed`, append-only), carrying its own confidence, judge and ledger id. The same judge again writes nothing (`already proposed by this judge`); a reviewed, rejected or superseded object takes no further proposal (its review stands).
- **Exam protection at write.** Before anything is written the one predicate is asked about every passage (`exam_material(vault, repository).withheld(keys)`); exam and held-out passages are skipped (`exam_material`); an unreadable predicate skips everything (fail closed).
- **Readers.** `role_proposals(vault, repository, extraction_ids=…, roles=…)`: RW4e's objects (any version marked `kind = instructional_role`), their **head** version `proposed` or `reviewed`, each citation on the reading it resolves to now (`CitationResolver`, the one alias authority), the confidence the best any judge gave (an unstated one ranks between medium and low), the judges in order, and **without every object RW4d's `hidden_source_objects` hides** (exam or held out now; an unreadable predicate hides all). Empty while `roles.positive_filter_enabled` is off. `role_keys` gives `(confident, low)` keys (a passage with any confident proposal is never in `low`); `best_roles` each passage's best label.
- **Tolerant parsing.** `clean_roles` / `tolerate_roles` (a `mode="before"` model validator: no JSON schema change) read a `roles` field that is missing, a string, or holds entries without a confidence or outside the vocabulary as the well-formed entries only (possibly none).

### 1.2 The judges (no extra call)

- **Cue judge** (`passage_cues.judge_target`): request unchanged (prompt, schema, ledger ids). `CueJudgment` reads `roles` tolerantly. With `roles.on_demand_enabled`, after its links are written, every judged passage's roles (all of the shortlist the judge answered for, not only the picks) are proposed with judge `passage_cue_judge`, the passage's `judgment_ledger` id and `passage_cue_judge.v2`; the result carries `role_proposals` counts only while the switch is on.
- **Library organizer** (`library_ask.organize`): `organizer_task(vault)` picks RW4a's `ORGANIZER_TASK` (`library_organizer.v1`, roles as names, kept on the row only) while `on_demand_enabled` is off, else `ORGANIZER_ROLES_TASK` (`library_organizer.v2`: the same instructions with the roles sentence replaced by "if you can tell, propose … each with a confidence (high, medium or low); leave roles empty when unsure"; `OrganizerRolesResult` with tolerant roles). The notes keep `roles` as names (the UI is unchanged); every judged passage's roles are proposed with judge `library_organizer`; the stored organizer carries `prompt_version` and, on, `role_proposals` counts. The cached and recovered paths are task-aware (`_recovered_answer(…, task)`).

### 1.3 The batch labeller (`src/learnloop/source_retrieval/role_labeller.py`, new; `learnloop reader label-roles`)

- `eligible_passages`: the reading's blocks in reading order (`extraction_blocks`), without page furniture and section headers, without what RW3b's `protection` withholds (teaching exclusions and the held-out partition) and what `model_reader_withheld` withholds (solutions, assessment lanes); passages this labeller already judged (its `judgment_ledger` rows for the reading at this prompt version) are counted as `already_labelled` and skipped: a rerun resumes. A reading held back whole is `withheld` (no call).
- `label_roles(vault, repository, extraction_id, dry_run=…, client=…)`: batches of `BATCH_SIZE` (12) passages, `PASSAGE_CHARS` (1,500) each, one `judge_listwise` call per batch (route `role_labeller`, ledger task `instructional_roles`, left kind `source_extraction`, ids `rlb_…`, verdict `roles` | `none`); the run's `SpendBudget` (one call and one retry per batch, `roles.batch_max_cost_usd` on metered dollars). **Before each batch call** the run's spend plus that batch's worst-case estimate is checked against the cap; a batch that would pass it is not sent and neither is any after it (`capped`, with the reason). Protection is read again before each batch. Every judged passage's roles are proposed with judge `role_labeller`. A subscription route (Codex) is `estimated_only` and exempt from the dollar cap, as every Codex role (the call and retry caps hold).
- `--dry-run`: zero calls, zero writes (the repository is attached read-only by `planning_repository`): passages (blocks, eligible, already labelled, withheld by reason), every batch (span range, estimated tokens and dollars, `planned` / `would_cap`), the route and its cost basis, the spend plan, and the cap (`checked: before each batch call`).
- `LEARNLOOP_ROLE_LABELLER_MODELS=off` (set by `tests/conftest.py`): no real client is resolved; an injected one still answers. No RPC reaches the labeller (never on the reading hot path).

### 1.4 Positive use (only while `roles.positive_filter_enabled` is on)

- **`find_sources(roles=…)`**: `search_spans` → `corpus.role_proposal_keys(vault, …)` = ingest's hints (unchanged) ∪ every other source object with an `authorial_role` (read as before) ∪ RW4e's visible proposals (`RS.role_keys`); a `low` proposal counts only when nothing better exists (unchanged rule). `role_basis` reports hints, proposals and low-confidence counts as before.
- **Intent lists**: `find_sources.source_object_lists(vault, repository, intent, extraction_ids)` (gains `vault`) reads every non-RW4e object as before and RW4e's visible proposals by role or by their mapped type (`remediate` → contrast, counterexample; `alternative` → alternative_treatment, intuition; `explain` → explanation, definition, theorem and the definition/claim/procedure types; `worked_example` by type), low ones last.
- **RW3b's contrast preference**: `passage_cues.contrast_list` reads `source_object_lists(vault, …, "remediate", …)`, so RW4e's `contrast` / `counterexample` proposals on the target's LOs (or their confusables) join the shortlist's fusion as the `contrast` extra list (with RW3b's own link roles, as before).
- **Library answers**: `library_ask.label_proposed_roles`: a main hit whose ingest role is ordinary prose (or none) and that has a visible proposal is grouped by it (`ROLE_GROUPS`: Foundation, Explanation, Contrast, Worked example, Prerequisite, Application, Exercise) and carries `proposed_role {role, confidence, judges, label: "model's label"}`; groups follow `ROLE_GROUP_ORDER` (RW4a's order with the new groups between). Ingest roles keep their groups; expansion hits keep their subheads.
- **Never to exclude (G44)**: `teaching_exclusions`, `item_exclusions`, `model_reader_withheld`, `scope_for` and every item-bound scope read no proposal (pinned by a before/after diff of all of them).

### 1.5 Config, route, report

- `[roles] on_demand_enabled = true`, `positive_filter_enabled = true`, `batch_max_cost_usd = 5.0` (`RolesConfig`, modelled defaults, out of the decision-only template); `ai.routing.role_labeller` (empty = the active provider; `AITask`, `ROUTE_FOR_OPERATION`). Registry: both switches and the cap `structural` / `operational` (the route by the `ai.` rule). All 20 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries recomputed with a "no scoring, scheduling, projection or serving change" note.
- `learnloop reader report` gains `roles`: proposals (live heads), by role, by confidence, versions by judge, agreed (two or more judges on one object), heads by status. Counts and labels only.
- **No disclosure entry** for `role_labeller`: it sends book passages only, no learner text (the disclosure list is of routes that receive learner text).

### 1.6 Frontend

`LibraryHitDto.proposedRole?` (`ProposedRoleDto`); `screens/reader/roleLabel.ts` (new): `hitRoleLabel(hit)` = "counterexample (model's label)" for a proposal, else RW4a's group label; `LibraryAnswer.tsx`: the locator calls it (one line and an import). No other UI; `ReaderScreen.tsx` untouched.

### 1.7 A shared read made faster

`span_aliases.cited_reading` takes optional memoized lookups; `CitationResolver` reads each revision's completed readings and each reading's block hashes once per resolver (resolvers are created per read path). Same answers; 324 role proposals read in 0.19 s instead of 4.4 s (the resolver opened two connections per citation).

## 2. Gates and where they are tested

| Gate | Backend | Frontend |
|---|---|---|
| **G44** roles add, never exclude; proposals carry confidence, judge, ledger id, revision and citation | `test_source_roles.py`: the proposal's every field and the table diff (only the three proposal tables change; no YAML, mapping proposal or relation); the type mapping (×12); `…never_admits_a_block_nor_removes_an_exclusion` (teaching/item exclusions, model-reader filter, item-bound scope identical with proposals on solutions, exercises and the item's worked example; practice-bound `roles=` never returns a solution); `…roles_filters_match_ingest_hints_and_proposals_with_the_low_confidence_rule`; `…intent_lists_read_proposals_by_role_and_by_their_mapped_type` | `libraryRoles.test.tsx` |
| Version on agreement | `test_source_roles.py::…a_second_judge_adds_a_version…`, `…reviewed_or_rejected…`; `test_roles_judges.py::…two_judges_agreeing…` (cue judge then organizer on one passage) | — |
| Held-out / exam | `test_source_roles.py`: never proposed (exam reading and a held-out chapter: nothing written at all), unreadable predicate proposes nothing, **held out later never returned** (role reads, role keys, best roles, intent lists, `find_sources(roles=…)`, P3's review read; rows kept), failing protection read hides all; `test_label_roles_cli.py::…held_out_and_exam_material_never_reach_the_labeller` | — |
| Judges' roles field: present / absent / malformed | `test_roles_judges.py` (cue judge and organizer, ×3 shapes each: lines, verdicts, order, links unchanged; only well-formed entries proposed); the two result schemas' hashes equal `a12ba5ba9`'s | — |
| Batch labeller: dry-run, cap, resume | `test_label_roles_cli.py` (11): the CLI dry run (database file byte-identical), `would_cap`, no model reachable, unknown source, reading order and no solutions sent, the cap before each batch (one call, then `capped`), a zero cap (no call), subscription `estimated_only`, resume (no call), missing roles field | — |
| RW3b's contrast preference | `test_roles_judges.py::…prefers_contrast_and_counterexample…` (the `contrast` list joins the fusion, ranks no lower; outside the target's LOs not added; off: absent) | — |
| Library grouping, "model's label" | `test_roles_judges.py::…library_answers_group_a_proposed_role…` | `libraryRoles.test.tsx` (the label on the proposed passage only; RW4a's elsewhere) |
| **Switch-off = `a12ba5ba9`** | `test_roles_switch_off.py` (golden `tests/fixtures/roles_switch_off_a12ba5ba9.json` recorded on the base tree: library answer, notes, a second ask, the ask rows, the organizer's request hashes, cue discovery, its links, the judge's request hashes, the whole ledger, nine `find_sources` calls with manifests; the tip runs with eight proposals already stored and both switches off; zero proposals written by the run) | `libraryRoles.test.tsx` (no `proposedRole`: RW4a's label); RW4a's `libraryAskSwitchOff` snapshots unchanged |
| Registry | `test_source_roles.py::…classified_as_operational…`; `test_registry_audit.py` | — |
| Report | `test_source_roles.py::…reader_report_counts…` | — |

**Fail-first evidence.** The golden was recorded on `a12ba5ba9`'s own `src` (a `git archive` under `fixtures-local/base-a12`, with `-o pythonpath=…`; the test asserts the base module path while recording, because pytest's `pythonpath = ["src"]` otherwise puts the tip first — an earlier recording attempt with `PYTHONPATH` alone ran the tip and was discarded) twice, byte-identical, and passes on the tip. With the switches left on (proposals stored), the same test fails on `ask`, `discovered`, `notes`, `find_sources` and more (checked once with a throwaway copy). `test_source_roles.py`, `test_roles_judges.py` and `test_label_roles_cli.py` cannot import on the base (no `source_roles` / `role_labeller`). First-run failures fixed before the backend commit: the RW4b statement-reader pin (`propose_roles` read block text through `blocks_by_key`; it now asks `existing_spans`), the re-read pin (a legacy object with `authorial_role` was hidden; RW4e's readers now take only objects marked `instructional_role`), and two pins that counted every source object (below).

## 3. Decisions and deviations

1. **RW4e proposals are the objects marked `kind = instructional_role`.** Other source objects with an `authorial_role` (none is written in production; the sources spec's tests write some) are read exactly as at `a12ba5ba9`, under every switch. RW4e's are read by head version only (the earlier readers read any version), and not at all while the positive filter is off — by role *or* by their mapped type, so an RW4e `worked_example` never reaches the worked-example list while off.
2. **The cue judge's tolerance holds under both switches.** Its request must stay `a12ba5ba9`'s (one schema for both states), so the before-validator is always there: a well-formed answer parses exactly as before; an answer with a missing or malformed `roles` field, which RW3b retried and then reported unjudged, now keeps its links with no roles. A strict improvement; recorded because "byte-identical off" holds for well-formed answers only.
3. **The organizer's on-request is a new prompt version** (`library_organizer.v2`): switching `on_demand_enabled` changes its ledger ids, so a question asked once in each state is judged twice (no cross-state cache).
4. **Every judged passage's roles are proposed**, not only the picks (the judge read each; §7.9 says "per passage").
5. **The same judge proposing again writes nothing** (its first confidence stands); a second *judge* adds a version; a reviewed or rejected proposal takes none.
6. **The cap is metered-only**, checked before each batch with the worst-case estimate (`METERED_REQUESTS_PER_CALL`); Codex is `estimated_only` and never refused for money (Slice A §5 rule 6, as every Codex role), with its estimate reported in the dry run.
7. **P3's review read (`reader.source_objects`) shows RW4e's proposals under either switch** (it is the review path, not a positive use); `hidden_source_objects` applies there as everywhere.
8. **Grouping touches ordinary prose only**: ingest's own roles keep their groups (ingest is the authority for its four roles); the hit gains `proposed_role`, the frontend shows it in the locator.
9. **No disclosure entry for `role_labeller`** (it sends book passages, never learner text).
10. **Three existing pins updated** (each with a comment): `test_reader_rw3b_protection.py` allows the three proposal tables to change during discovery (proposals, never evidence); `test_rw4d_rw3b_composition.py` counts kept-comparison objects apart from the cue judge's role proposals; `test_reread_safety.py` passes the vault to `source_object_lists` (its new first argument).
11. **`CitationResolver` memoizes per resolver** (shared module): same answers, resolvers are local to one read path, so nothing stale survives a write.
12. **`exact_text` is empty**: the citation points at the passage; nothing of the book's text is copied into a proposal.

## 4. Successor

**None.** Labels on sources (P3 §7 proposals). Nothing here writes an attempt, evidence, mastery, certification, FSRS, a plan, a concept edge, a facet merge, a prerequisite or a learning-object change; replay and rebuild never read the proposals for scoring; no table, migration or replayer.

## 5. Friction notes for RW7a and RW6b

1. **RW7a (reading paths)**: read roles through `source_roles.best_roles(vault, repository, keys)` / `role_proposals(...)` (visible, current-reading keys; already filtered by exam protection; empty while the positive filter is off). `RoleLabel.judges` and `confidence` say how settled a label is; `low` alone should never be the reason a passage is "skippable". A path judge that proposes roles can call `propose_roles(..., judge=…)` once its name is added to `JUDGES` (one line) — and its own `prompt_version`.
2. **RW7a**: `prerequisite` proposals are the model's reading of the book, not the concept graph's prerequisites; never turn one into an edge (G18 / P3 §7.3).
3. **RW6b (follow-ups, the card)**: `reader report --json`'s `roles` gives proposal counts by role and agreement; for a card, prefer counting agreed proposals (`versions_by_judge`, `agreed`) and never quote passages (proposals hold none).
4. **Both**: a cold-path cost to know — `role_proposals` resolves every RW4e citation once per call (about 0.6 ms each on the test vault after the memoization); a fully labelled 2,000-passage book adds about a second to `find_sources` calls that read the lists. If that shows in the latency report, cache visible labels per reading (keyed by the proposal tables' row counts and the exam-material fingerprint).
5. **The sources spec's §18 request** (`source_rerank` and `source_compare` returning an optional per-passage `roles`) is not built here; adding it is one `propose_roles(..., judge="source_rerank")` call after their judgments, with the judge added to `JUDGES`.

## 6. Owner-run commands (dry run first; on a backup copy)

```bash
uv run python -c "from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases as c; c(Path('fixtures/probability'), Path('fixtures-local/rw4e-prob'))"
uv run learnloop doctor --fix-state --vault fixtures-local/rw4e-prob
uv run learnloop reader label-roles --vault fixtures-local/rw4e-prob --source <source id> --dry-run --json
# read the plan: passages, batches, estimated tokens/dollars, route and cost basis, the cap and any would_cap batch
uv run learnloop reader label-roles --vault fixtures-local/rw4e-prob --source <source id> --json
uv run learnloop reader report --json --vault fixtures-local/rw4e-prob   # the "roles" row
```

The labeller's route is `ai.routing.role_labeller` (unset: the active provider; Codex is `estimated_only`). A metered route needs `source_retrieval.llm_price_per_million` and is held to `roles.batch_max_cost_usd` (5.00 per run). In the Reader (`LEARNLOOP_VAULT=$PWD/fixtures-local/rw4e-prob npm run dev`), *where else is this explained?* then shows "… (model's label)" on proposed passages. Switches: `[roles] on_demand_enabled = false` (the judges write nothing; their requests are RW4a's/RW3b's), `positive_filter_enabled = false` (proposals ignored everywhere but P3's review list).

## 7. Model calls made in this stage

Tests: fakes only. **No live or paid call**: no vault copy was opened and no command ran against a vault outside pytest. Python outside pytest ran only under `env -i` with empty `HOME` / `CODEX_HOME` / `LEARNLOOP_CONFIG_DIR` (`fixtures-local/tmp/iso.sh`): the schema hashes, the snapshot recomputation, the CLI help snapshot, `reader --help`, the reference generator and validators. One exception, harmless: a single `python -c "import learnloop, learnloop_sidecar"` (printing module paths, no call possible) ran under `uv run` without that isolation early on.

## 8. Tests and counts

- New backend: `tests/test_source_roles.py` **26** (the type mapping parametrized ×12), `tests/test_roles_judges.py` **14** (malformed shapes ×3 for each judge), `tests/test_label_roles_cli.py` **11**, `tests/test_roles_switch_off.py` **1** (golden `tests/fixtures/roles_switch_off_a12ba5ba9.json`, recorded on `a12ba5ba9`).
- Changed backend tests: `tests/library_ask_fixtures.py` (`OrganizerFake` answers RW4e's request too, knobs `roles` / `malformed_roles`), `tests/conftest.py` (`LEARNLOOP_ROLE_LABELLER_MODELS=off`), `test_reader_rw3b_protection.py`, `test_rw4d_rw3b_composition.py`, `test_reread_safety.py` (§3 item 10), `tests/cli_help_snapshot.json`.
- New vitest: `src/screens/reader/libraryRoles.test.tsx` **2**.

## 9. Files

- Backend: `src/learnloop/reader/source_roles.py` (new), `src/learnloop/source_retrieval/role_labeller.py` (new), `src/learnloop/reader/source_objects.py` (`append_proposal_version`), `src/learnloop/source_retrieval/{library_ask.py, passage_cues.py, find_sources.py, corpus.py, search.py}`, `src/learnloop/content/sources/span_aliases.py`, `src/learnloop/reader/reader_report.py`, `src/learnloop/cli/reader.py`, `src/learnloop/ai/routing.py`, `src/learnloop/config/{schema.py, template.py}`, `src/learnloop/params/parameter_registry.py`.
- Frontend: `apps/learnloop-tauri/src/screens/reader/roleLabel.ts` (new), `libraryRoles.test.tsx` (new), `screens/reader/LibraryAnswer.tsx` (one line), `api/dto.ts`. Nothing under `src-tauri`.
- References: Configuration and Database references regenerated (942 leaves in 67 sections; 335 table notes; schema head 215 unchanged; 0 errors), `_scripts/db_generate_reference.py` (`roles` description), the two prose counts, `Maps/LearnLoop Pipeline Map.md` (RW4e bullet).

## 10. Open questions (with the default taken)

1. *Defaults on?* **Yes, both** (frictionless defaults): the judges propose on every judgment and the filters read proposals. `on_demand_enabled` on means the organizer's request is `library_organizer.v2` for every vault (a new request, so a first ask after landing is judged again rather than served from an RW4a ledger row).
2. *Should the batch cap bind Codex?* **No** (`estimated_only`, as every Codex role; Slice A §5 rule 6). A large book on Codex is roughly one call per 12 passages; the dry run says how many.
3. *A second proposal by the same judge with a different confidence?* **Ignored** (first stands). Alternative: append a version so a judge's revised view is kept.
4. *Grouping by a proposal over a specific ingest role* (an ingest `definition` the model calls a `contrast`)? **Ingest wins**; the note line still shows the organizer's role labelled the model's.
5. *P3's review list shows RW4e proposals even with the positive filter off.* **Yes** (review is not a positive use). The owner may prefer a filter in that list (by `kind`).
6. *Crash between a batch's ledger rows and its proposals* leaves those passages "already labelled" without proposals. **Default: accept** (the window is one write); a repair would read the batch's checkpoint as RW4a's `_recovered_answer` does. **Superseded by the Codex review (F2, `reader-rw4e-codex-review.md`)**: the window was several independently committed writes; a judged passage no proposal carries the ledger id of is now pending and applied on the next run from its receipt (no call), and a run with one it cannot recover ends `incomplete`.
7. *`source_rerank` / `source_compare` roles* (the sources spec's §18 request): **not built here**; one call each once that spec adds the field (§5 note 5).

## 11. Gate (implement step; targeted, per the owner's 2026-10-17 rule)

Run in the worktree with `TMPDIR` = `fixtures-local/tmp`, `uv run --no-sync` after the install; `/tmp/learnloop-fullsuite.lock` was free (checked with `flock -n`).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **28 kept**, 0 broken |
| targeted `pytest -n auto -q -p no:cacheprovider` over the **138 files** below, on the stage's code (`0c8e038e2`) | **2,911 passed**, 0 failed (8 min 23 s) |
| `pytest -n auto --durable-sqlite` on `test_source_roles`, `test_label_roles_cli`, `test_roles_judges`, `test_source_objects` (no migration; the proposal writes on production pragmas and WAL) | **54 passed** |
| `npm install`, `npm run typecheck` | ok, clean |
| vitest `src/screens/reader`, `src/screens/ReaderScreen*`, `attentionBudget.test.tsx`, `LibraryPlace.reread.test.tsx` | **68 files, 524 tests passed** (incl. `libraryRoles.test.tsx` 2; RW4a's and RW4d's switch-off snapshots unchanged) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `db_generate_reference.py`, `db_validate_reference.py`, `validate_vault.py` | regenerated (942 leaves, 335 table notes, head 215); errors []; passed (1,136 notes, all reachable) |
| defaults snapshots | all 20 recomputed with the template `.pyc` cleared; 0 mismatches (`test_config_refactor.py` in the run) |
| contract tests in the run: `test_config_refactor`, `test_cli_help_snapshot` (rewritten for `reader` and `reader label-roles`), `test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`, `test_mobile_allowlist` (no new RPC), `test_architecture`, `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_registry_audit`, `test_sqlite_file_copies`, `test_judge_routes`, `test_instructional_layering` | pass |

Pins that must be in every gate (orchestrator note): `test_library_exercises.py` (the RW4b statement-reader pin), `test_source_objects.py`, `test_compare_sources_keep.py`, `test_compare_keep_switch_off.py`, `test_rw4d_rw3b_composition.py`, `test_reader_compare_table.py`, `test_roles_switch_off.py` — all in the list.

**Not done:** no adversarial (Codex) review in this step; no real-UI look (exercised through the real `ReaderScreen` in jsdom); the labeller has run only on fakes.

**The 138 pytest files run** (the new and changed test files; every test file naming `library_ask`, `passage_cues`, `find_sources`, `source_object_lists`, `role_proposal_keys`, `search_spans`, the corpus, `source_objects`, `reader_report`, `span_aliases` / `CitationResolver` / `cited_reading`, `parameter_registry`, `DEFAULTS_SNAPSHOT` / `defaults_fingerprint` / `effective_defaults`, the reader CLI, `AITask` / `ROUTE_FOR_OPERATION`, the organizer and cue judge, `reader.library_ask*` / `reader.cue*`; and the contract tests above):

```text
test_ad1_codex_review_fixes test_ad1_fix_round4 test_ad1_migration test_ad1_reading_opportunities 
test_approach_maps test_architecture test_cli_help_snapshot test_compare_keep_switch_off 
test_compare_sources_keep test_config_refactor test_constraint_engine test_coordinated_migrations 
test_decider_landing test_desktop_rpc_contract test_diagnosis_input_provenance test_discriminating_search 
test_exam_protection_identity test_exam_protection_landing test_exam_protection test_exercise_arm 
test_facet_authority test_facet_authority_review test_facet_identity test_facet_locks_landing 
test_facet_reword_confirm test_facet_span_support test_field_config test_find_sources_intents 
test_grading_cli test_help_assists_schema test_import_split_parity test_ingest_jobs 
test_instructional_layering test_intent_codex_rereview test_interaction_signals 
test_intervention_outcomes_replayer test_judge_routes test_kinship_feature test_label_roles_cli 
test_library_ask_expand test_library_ask test_library_ask_review test_library_asks_migration 
test_library_exercises test_mcp_c1a_narrow test_mcp_c1a_review test_mcp_cli test_mcp_tools 
test_method_explicit_upgrade test_mobile_allowlist test_mvp010_upgrade test_mvp011_upgrade 
test_mvp013_upgrade test_mvp014_upgrade test_mvp015_upgrade test_mvp016_upgrade test_mvp017_upgrade 
test_mvp018_upgrade test_mvp020_upgrade test_mvp021_upgrade test_mvp022_upgrade test_mvp023_upgrade 
test_mvp024_upgrade test_open_world_gate test_output_budget test_p0_cutover_mvp08 test_passage_links 
test_plan_determinism test_prescription_passages test_project_cli test_provider_resolution_parity 
test_reader_compare_table test_reader_cue_holdout test_reader_cues_cli_report test_reader_cues 
test_reader_cue_value test_reader_find_sources_callers test_reader_intentions test_reader_intent 
test_reader_pdf_selection test_reader_report test_reader_requests test_reader_rw1b_fix_round4 
test_reader_rw1b_review test_reader_rw1c_review test_reader_rw2b_review test_reader_rw3a_landing 
test_reader_rw3b_fix_round4 test_reader_rw3b_fix_round5 test_reader_rw3b_fix_round6 
test_reader_rw3b_protection test_reader_rw3b_review_fixes test_reader_rw3b_switch_off test_reader_try_first 
test_reader_tutor_offers test_reader_tutor_retrieval test_reader_tutor_switch_off test_reader_workbench_rw2a 
test_reading_step_switch test_recurrence_commands test_registry_audit test_regrade_contract_successor 
test_regrade_contract_upgrade test_required_method_round3_review test_reread_safety_landing 
test_reread_safety test_retrieval_interventions_write_points test_roles_judges test_roles_switch_off 
test_router_coldness_covariates test_rw4d_rw3b_composition test_rw4_kill_switches test_salience_firewall 
test_sensitivity_certificates test_serve_eligibility_review test_sidecar_reader_p3_slice2 
test_sidecar_serializer_snapshot test_source_exercise_rpcs test_source_first_needs test_source_objects 
test_source_retrieval_followup test_source_retrieval_guards test_source_retrieval_rereview 
test_source_retrieval_search test_source_roles test_sources_merge_composition test_sqlite_file_copies 
test_t6_followup_review test_table_roles test_tool_dispatch_policy test_tool_registry 
test_tool_results_withhold_answers test_tools_cli test_tracked_fixture_databases test_tutor_tool_requests 
test_ux_phase1_landing test_valuation_calibration_fields test_workbench_check 
```
