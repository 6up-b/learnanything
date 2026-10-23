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

## 12. Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/rw4e-onto-main`, cut from main at `a12ba5ba9` (the
RW4d landing record; migration head 215 with `migration_head_215`, 20 defaults snapshots, 938 configuration leaves).
The stage tip is `111617408` (base `a12ba5ba9`, so main had not moved), unchanged. Main was neither fast-forwarded
nor pushed here.

**The orchestrator's verifies.** Codex job `20261020-224735-XWC66K` on `57d02d3f0` found everything clean except
F10; `20261020-225727-W36G4L` on `111617408` checked the F10 fix and reopened one Medium, which the orchestrator
**ruled non-blocking (Low)**:

> Recovery of an OLDER-format labeller ledger row (verdict "none" beside roles, written before round 5's
> normalisation) whose receipt never finished (a suppressed receipt-finish persistence error) reports done instead of
> incomplete.

**Why it isn't blocking.** The labeller has never shipped, so no such row exists in any real vault: only this
branch's own pre-round-5 code wrote them. New runs normalise the verdict at capture. It is recorded under the open
items below.

### Commits and conflicts

- `b35681815`: a `--no-ff` merge of `reader/rw4e` onto `a12ba5ba9`. **No conflict**: the stage branched from main's
  tip, so `config/template.py` (all 20 snapshots), the parameter registry, `test_mobile_allowlist`, the CLI help,
  the RPC pins, `find_sources` / `search` / `passage_cues`, `reader/source_objects.py` and `LibraryAnswer.tsx` all
  came in as the stage left them. The generated references were the stage's (made on `a12ba5ba9`) and were
  regenerated in the next commit.
- `f5af84d7f`: the regeneration (below); the gate head.
- This record (docs only).

### Regeneration

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, `schema_head` **215**,
  **335** table notes, **942** configuration leaves in **67** sections (RW4e's `[roles]` three and
  `ai.routing.role_labeller` on RW4d's 938). 404 files changed: the commit labels on every note, plus RW4e's
  fix-round tests (`test_roles_concurrency.py`, `test_roles_switch_off_legacy_parity.py`), which the stage's
  references (made before those rounds) did not cite, in the `roles` field notes and in the `parameter_registry`,
  `source_objects`, `source_object_versions` and `source_object_citations` table notes. The two prose counts
  (`Configuration.md`, `Database.md`) already said 942 / 67 / 335.
- **Defaults snapshots.** With the template's `.pyc` cleared (and run with `-B`), all **20**
  `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries equal `defaults_fingerprint_for_version` on the merged tree: **0
  mismatches**, nothing to rewrite.
- **CLI help snapshot and RPC pins.** `tests/cli_help_snapshot.json` already carries `reader label-roles`. A pin run of
  16 files (`test_cli_help_snapshot`, `test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`,
  `test_mobile_allowlist`, `test_sidecar_contract`, `test_config_refactor`, `test_registry_audit`,
  `test_library_exercises`, `test_architecture`, `test_table_roles`, `test_tracked_fixture_databases`,
  `test_sqlite_file_copies`, `test_roles_switch_off`, `test_roles_switch_off_legacy_parity`, `test_source_roles`,
  `test_rw4d_rw3b_composition`): **491 passed, 1 skipped** (the legacy golden's base-only recorder,
  `RW4E_WRITE_LEGACY_GOLDEN=1`). No snapshot needed rewriting; RW4e adds no RPC.
- **Head fixture.** No migration: `migration_head_215` stays main's.
- **`validate_vault.py`**: passes (1,136 notes, 1,134/1,134 reachable).
- **Known failures from before this stage, not fixed:** `desktop_validate.py` still stops on
  `components/pdfSelection/testing/syntheticBook.ts`; `module_validate.py` reports **962** issues (958 at the RW4d
  landing; RW4e adds modules without module notes, such as `reader/source_roles.py` and
  `source_retrieval/role_labeller.py`).

Every script outside pytest (the generators, validators, the snapshot check) ran under `env -i` with only `PATH`,
`TMPDIR`, `LANG`, an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, and `LEARNLOOP_CUE_JUDGE_MODELS=off`,
`LEARNLOOP_ROLE_LABELLER_MODELS=off` (`fixtures-local/landing-rw4e/scripts/iso.sh`).

### Gate

Python 3.12.14. `TMPDIR` was merge2's `fixtures-local/tmp`; every command after the install ran as `uv run
--no-sync`. Both suite lanes ran under `flock /tmp/learnloop-fullsuite.lock` on `f5af84d7f`. The AD2+AD3
(`learnanything-ad1`), RW5a (`learnanything-dl2`) and RW4e stage (`learnanything-rw4b`) worktrees and their processes
were not touched (the machine's load average was about 24 when the suite started). Every test uses fakes. **This is
the first full run over RW4e's code**: the stage and its five fix rounds ran targeted tests only.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `lint-imports --no-cache` | **28 kept**, 0 broken |
| full suite `pytest -n auto` | **15,054 passed, 1 skipped, 2 xfailed, 0 failed** (23 min 51 s; `fixtures-local/rw4e-landing/fullsuite.log`). RW4d's landing ran 14,973; the skip is the base-only golden recorder |
| `pytest -m durability` | **117 passed**, 14,940 deselected (4 min 24 s; `fixtures-local/rw4e-landing/durability.log`); RW4d's landing 114, RW4e's `test_roles_concurrency.py` adds 3 |
| `npm install`, `npm run typecheck` | ok; clean |
| `npm test` (the whole vitest run, default workers) | **161 files, 1,274 tests passed** (RW4d's landing: 160 / 1,272; `libraryRoles.test.tsx` adds 1 / 2) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | ok (nothing under `src-tauri` changed) |
| thread, lock and timing tests | all passed on the first run (`test_roles_concurrency.py` included), so none was rerun |
| tracked fixtures, worktree | `git status` clean after both lanes and the frontend run; no `-wal` / `-shm` beside a fixture |

No failure, so no landing fix.

### Parity (backup-API copies; no model call completed)

**Setup** (scripts in `fixtures-local/landing-rw4e/scripts/`, adapted from the RW4d landing's):
- **Copies.** `fixtures/linear_algebra` and `fixtures/probability` were copied once, with `copy_tree_with_databases`,
  from the main checkout into `fixtures-local/landing-rw4e/orig/`; every other copy came from `orig/` or its upgraded
  copies through the same helper. `arxiv_v2` was not opened. Both vaults start at schema 165, label `mvp-0.8`;
  linear_algebra holds 4 source objects, probability 5, **none of them RW4e's** (no `instructional_role` object).
- **Code.** Main's code is `git archive a12ba5ba9`; the merge's is `git archive f5af84d7f`.
- **Environment.** Every run went through `env -i` with only `PATH`, `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`,
  `TMPDIR` and `LANG` (empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`).
- **Routes.** `neutralize3.py`, under each code, sent every route field to `127.0.0.1:9` (56 on main, 57 on the
  merge: `role_labeller` is the new one; `library_organizer`, `passage_cue_judge`, the reader, tutor, sources,
  `source_compare`, cue, hint, workbench, AD, figure and Decider routes included), the active provider to that
  loopback profile with no fallback; `query_rewrite`, `tutor_query_rewrite`, `tutor_rerank`, `dense`, `[embedding]`
  and `[learner_text_gaps]` off; `build_on_serve` and outcome placement off. `routes.py` resolved all 59 `AITask`s on
  main's code and all 60 on the merge's: nothing outside the loopback profiles except `embedding`, disabled and
  keyless; `role_labeller` and `library_organizer` resolve to the loopback.

**(a) No schema change**

| Check | linear_algebra | probability |
|---|---|---|
| open (migrate), main's code / the merge's | 165 → 215 (49 applied) / the same | the same |
| schema, main vs merge | **identical** (1,428 objects; none on one side only; no SQL differs) | **identical** (1,427) |
| rows of every table (340), all columns | **identical** (16,540 rows); `schema_migrations` differs only in `applied_at` | **identical** (7,638 rows; the same) |
| `foreign_key_check` / `integrity_check` | 0 / ok, both sides | the same |
| `rebuild --shadow --json`, main vs merge | **0 differences** after normalisation (facet 0, mastery 2, schedule 8 on both); live database unchanged on both | **0 differences** (0 / 1 / 1) |
| `doctor --json`, main vs merge | **0 differences** after normalisation (57 issues, 1 error) | **0 differences** (101 issues, 48 errors) |

**(b) Nothing served changes** (frozen clock 2026-10-19 09:00 UTC; certification with recipe gaps and curves, the
Today queue with no session / a session / greedy, the daily plan read, served twice and read again)

| Check | linear_algebra | probability |
|---|---|---|
| at `mvp-0.8` (the copies' label) | cert **byte-identical** (132,860 bytes), Today **byte-identical** (504,488), plan byte-identical (off below mvp-0.14) | cert (17,494), Today (709,910), plan: all **byte-identical** |
| upgraded by main's code to `mvp-0.27` (`--to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice; all rc 0), opened by each code | cert **byte-identical** (129,651), Today **byte-identical** (528,665) | cert (17,495), Today (741,269): **byte-identical** |
| then by main's code to `mvp-0.29` (`--to mvp-0.29`, `rebuild-derived-state` twice; all rc 0), opened by each code | cert and Today **byte-identical** (the same sizes) | the same |
| the daily plan at mvp-0.27 and at mvp-0.29 | identical except `router_decisions.card_hash`, `snapshot_hash` and the card hash inside `detail_json`; a second run of main's code on a fresh copy differs from the first in exactly these three (`plan_repeat.sh`), as at the RW3b, DL2 and RW4d landings | the same |

**(c) The real sidecar** (stdio, `SystemClock` frozen at 2026-10-19 09:00 UTC through `sidecar_clock.py`;
`roles_run.py`, compared by `ccmp.py` with run-generated ids normalised) on copies of main's mvp-0.29 vaults: (i)
`cm`, main's code; (ii) `coff`, the merge with `[roles] on_demand_enabled = false` and `positive_filter_enabled =
false`; (iii) `cdef`, the merge at its defaults. Each, 31 calls: `initialize`; `reader.prompt_contract`;
`reader.source_objects` for the book that has objects (probability `src_01KYMSH13FAGNWVPPHCQ2FY3B4`, 5 objects;
linear_algebra `src_01KY2YG27G1SDWA4FN939ZBB34`, 4) and `reader.proposal_inbox`; `reader.guide_plan` on that book's
reading (its cues); `find_sources` (the desktop `find_sources` RPC, caller `reader`) for the intents `explain`,
`remediate`, `alternative` and `worked_example` without `roles=`, and `explain` with `roles=` `[definition]`,
`[contrast, counterexample]`, `[worked_example]`, `[explanation, intuition]` and `[theorem]`; `reader.library_ask`
on one of the objects' passages (a job, polled) and its `reader.library_ask_notes` (the organizer; a job, polled);
the reads, the guide plan and the nine `find_sources` again; `shutdown`.

| Step | (i) main vs (ii) both switches off | (iii) defaults, every difference from (i) |
|---|---|---|
| `initialize` | identical apart from the vault path; the method list is the same (RW4e adds no RPC) | the same |
| `reader.prompt_contract` | **identical** | identical |
| `reader.source_objects` (both reads) | **identical** (5 / 4 objects) | identical |
| `reader.proposal_inbox` (both reads) | **identical** (1 / 4 proposals) | identical |
| `reader.guide_plan` (both reads) | **identical** (8 cues on each book) | identical |
| `find_sources` (18 calls per vault) | **identical** apart from `manifest.search.timingsMs.total` (wall-clock milliseconds; main against main again on a fresh copy differs in it too, `cm2.sh`). Probability returns 8 / 0 / 0 / 0 hits for the four intents and 3 / 0 / 8 / 0 / 3 for the five role filters; linear_algebra 7 / 0 / 0 / 0 and 0 for each filter | identical to (i) the same way: **no RW4e proposal exists on these copies**, and no existing source object is `low` confidence where a stronger one is eligible, so the positive filter and the shared eligibility change no hit |
| `reader.library_ask` (the job's result) | **identical** (`status: ok`) | identical |
| `reader.library_ask_notes` (the organizer job) | **identical**: `skipped: metered organizer route without source_retrieval.llm_price_per_million` (refused before any call), `promptVersion: library_organizer.v1` | the same refusal, with **`promptVersion: library_organizer.v2`** (the only response difference in (iii)) |
| rows written (over the same copy opened by the merge's code, ids and timestamps aside) | the same tables and rows on all three: one `library_asks` row, two `interaction_events`, 14 `source_exposure_events`, and the open-time derived refresh (probability: 1 `facet_capability_evidence`, 2 `facet_recall_state`; linear_algebra: 36, 76 and 30 `practice_item_state`) | the ask row's `organizer_json.prompt_version` is `library_organizer.v2` (v1 in (i) and (ii)); no source object, version, citation or `judgment_ledger` row on any run |

So (i) and (ii) are identical call by call apart from the vault path and wall-clock timings, and (iii) differs only in
the organizer's prompt version.

**(d) The dry-run CLI** (`learnloop reader label-roles --source <id> --dry-run`, with `--json` and without, the
merge's code, on fresh copies of the mvp-0.29 vaults; every file of each vault hashed before and after)

| Check | linear_algebra (`src_01KY2YG27G1SDWA4FN939ZBB34`) | probability (`src_01KYMSH13FAGNWVPPHCQ2FY3B4`) |
|---|---|---|
| rc, calls | 0, `calls: 0`, `status: dry_run` (both formats) | the same |
| files before vs after | **byte-identical** (145 files, the database included) | **byte-identical** (120 files) |
| receipts, `instructional_roles` ledger rows after | 0, 0 | 0, 0 |
| passages | 489 blocks, **353 eligible**, 0 already labelled, 0 pending apply; withheld: 133 furniture or empty, 3 assessment lane (reading `ext_01KY2ZX9193YPC73DT6HXFFNDC`) | 518 blocks, **341 eligible**, 0 / 0; withheld: 115 furniture or empty, 44 solutions, 18 assessment lane |
| the plan on the loopback route (metered, no price) | 30 batches of up to 12, 645,699 estimated tokens, `estimated_usd: null`, every batch `would_cap`, `route_status: skipped: metered role labeller route without source_retrieval.llm_price_per_million`; caps `{batch_size 12, checked: before each batch call, roles.batch_max_cost_usd 5.0}` | 29 batches, 660,124 tokens, the same |
| the plan with `source_retrieval.llm_price_per_million = 10.0` on a further copy (probability only; still the loopback) | — | files byte-identical (120), 0 calls; estimated $6.60 for the book; **batches 1–21 `planned` ($4.83), 22–29 `would_cap`** (batch 22 would pass $5.00), which shows the cap is checked before each batch |

**`model_call_receipts`**: 38 learner databases under `landing-rw4e/` carry the table; **no row** in any of them
(none completed, none attempted: the organizer and the labeller refused before calling).

### New findings

1. **No composition work.** The stage branched from main's tip, so the merge was clean; the gate and parity found
   nothing to fix.
2. **`library_asks.prompt_version` stays `library_organizer.v1`** on an ask whose notes ran under v2: the column is
   RW4a's constant, written when the ask is made, while `organizer_json.prompt_version` and the notes response say
   v2. Nothing found reads the column for caching (the cache is the ledger, keyed by prompt version). Low; not
   changed.
3. **On an unpriced metered route the dry run marks every batch `would_cap`**, with the reason in `route_status`.
   Correct (the real run would send nothing), but a reader of the batch list alone could take it for the dollar cap.
   The owner's vaults use Codex (`estimated_only`), so the real dry run will show `planned`. Low.

### For the owner

- **No migration.** Your database changes only when a judge proposes roles or you run the labeller, and only the
  three source-object tables; your algorithm version is unchanged and nothing served moves (parity (a), (b)).
- **What you see in the Reader.** On a library answer (*where else is this explained?*), a passage the model reads
  as, say, a counterexample is grouped under *Contrast* and labelled **"counterexample (model's label)"**. Ingest's
  own roles (definition, theorem, worked example, exercise) keep their groups. Nothing else in the UI changes. The
  labels are proposals: they never hide a passage, never admit exam or held-out material, and never grade you;
  P3's review list (`reader.source_objects`) shows them for review.
- **Behind the scenes.** The cue judge and the library organizer now also return roles per passage (no extra
  call); the tutor's and the Reader's source lookups (`find_sources`, intent lists, RW3b's contrast list) can use
  them.
- **The batch labeller** (owner-run, on a backup copy, **dry run first**; §6):
  `uv run learnloop reader label-roles --vault fixtures-local/rw4e-prob --source <source id> --dry-run --json` shows
  the passages, the batches with estimated tokens and dollars, the route and its cost basis and any `would_cap`
  batch, with 0 calls and 0 writes (parity (d)); then run it without `--dry-run`. On Codex it is `estimated_only`;
  a metered route needs `source_retrieval.llm_price_per_million` and stops before the batch that would pass
  `roles.batch_max_cost_usd` (5.00).
- **The switches** (`[roles]`, both default on): `on_demand_enabled = false` makes the judges propose nothing and
  their requests RW4a's / RW3b's; `positive_filter_enabled = false` makes every retrieval path ignore the proposals
  (P3's review list still shows them). With both off, the Reader and `find_sources` answered exactly as
  `a12ba5ba9` on your copies (parity (c)).
- **Notes recorded at landing:**
  - Both role switches default **on**.
  - The first library ask after landing is **judged again** under `library_organizer.v2`, not served from an RW4a
    ledger row (parity (c): the notes' prompt version is v2 at defaults).
  - Codex labeller runs are **`estimated_only`** and exempt from the dollar cap (the call and retry caps hold).
  - The **same judge's later confidence is ignored** (its first proposal stands; a second judge adds a version).
  - **Ingest's specific role wins** the grouping.
  - **P3's review list shows RW4e proposals** under either switch.
  - With `positive_filter_enabled` on, the low-confidence rule (a `low` row counts only when no stronger eligible one
    remains) also applies to **older (non-RW4e) source objects**. With it off, retrieval is exactly `a12ba5ba9`'s
    code path, pinned by `tests/fixtures/roles_switch_off_legacy_a12ba5ba9.json`.
  - **`CitationResolver` memoizes per resolver** (resolvers live for one read path, so nothing stale outlives a
    write).

### Open questions (defaults in force)

1. *Both role switches on by default?* **Yes** (frictionless defaults).
2. *First ask after landing re-judged under v2 rather than served from an RW4a row?* **Yes** (a new prompt version;
   no cross-version cache).
3. *Should the dollar cap bind Codex labeller runs?* **No** (`estimated_only`, as every Codex role).
4. *A later proposal by the same judge with another confidence?* **Ignored** (first stands).
5. *A proposal against a specific ingest role?* **Ingest wins** the grouping; the organizer's line still shows the
   model's label.
6. *P3's review list shows RW4e proposals with the positive filter off?* **Yes** (review is not a positive use).
7. *The low-confidence rule for older source objects while the positive filter is on?* **Applies** (one rule for
   every source object); off, `a12ba5ba9`'s path.
8. *`CitationResolver` memoized per resolver?* **Yes.**

### Open items

- **Older-format labeller ledger rows (ruled Low, from verify `20261020-225727-W36G4L`).** Recovery of a labeller
  ledger row written before fix round 5's normalisation (verdict `none` beside roles) whose receipt never finished
  (a suppressed receipt-finish persistence error) reports `done` instead of `incomplete`. No such row exists in any
  real vault (the labeller never shipped; only this branch's pre-round-5 code wrote them), and new runs normalise the
  verdict at capture. **Follow-up:** when an unapplied legacy `none` row cannot be resolved, report `incomplete`.
- **Findings 2 and 3** above (Low).
- **From the stage, not built:** `source_rerank` / `source_compare` roles (the sources spec's §18 request; §5 note 5);
  the per-reading cache of visible labels if `role_proposals` shows in the latency report (§5 note 4).
- **From before this stage:** `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (962 issues).
