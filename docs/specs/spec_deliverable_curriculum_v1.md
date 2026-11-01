# Deliverable curriculum: one deliverable, across all your books (v1)

**Status:** draft, 2026-10-25. **Every owner question (Q1–Q15, §14) is DECIDED 2026-10-25**: the recommended answers were adopted, with one change, to Q5: the notes allowlist also covers `~/org`. Specification only: no code changed, no model or paid call made, nothing run.
- **Base:** `main` at `fa2eb72f8` (migration head 220). RW7b is read on its branch (`reader/rw7b` in `learnanything-dl2`, head `9cd119e41` plus uncommitted review fixes), because this spec builds directly on it.
- **Companion:** `docs/specs/ux_reader_compare_ask_v1.md` (branch `docs/reader-compare-ask-ux`) designs how skim-and-jump and Compare-from-anywhere look and feel. **This spec owns the shared backbone** those surfaces read, the curated path, and the notes link. Where the two touch, this spec names the data and the read API, and the UX spec names the presentation.
- Code paths are under `src/learnloop/` unless they say otherwise. "Owner principles" are the binding ones in §2.

---

## 0. Owner direction (verbatim, 2026-10-25)

> "for syntopic reading we want to be able to connect it to handwritten notes, goal/quest ( i want to learn this linear algebra for machine learning) or exam ( i want to learn only for my exam ) then have canonical source sections that are curated and only go over what you need for that deliverable"

> "for syntopic reading should we have the ability to skim through multiple sources and jump to sections that correlate with the other source?"

Read as five requirements:
1. **A deliverable is something the learner names**: a quest ("linear algebra for machine learning"), an exam ("only my midterm") or a project. It scopes what to learn.
2. **A curated path across all sources**: for each thing the deliverable needs, the one section worth reading, and nothing the deliverable doesn't need.
3. **Correspondence across sources**: from any section, the sections in other books that treat the same idea, so the learner can skim and jump.
4. **The learner's handwritten and typed notes take part**, in the learner's own voice.
5. All of it in service of being ready for the deliverable, which LearnLoop measures only by delayed cold checks.

---

## 1. Thesis

**A deliverable is a goal. A curriculum is a judged choice of sections over the goal's learning objects. The backbone is section-to-LO coverage, not a section-to-section graph.**

- **The deliverable is an existing `Goal`.** Goals already carry the learner's sentence (`intent_sentence`), a scope (`facet_scope`), a deadline (`due_at`) and an exam (`exam`) (`vault/models.py:60-91`). DL2 already turns a deadline into a goal linked from a commitment (`spec_daily_loop_v1.md` §5.4). The teacher spec already resolves a typed goal to LOs and creates a missing LO (`spec_teacher_v1.md` §8.1 `goal`, §11.5). This spec adds no goal object and no goal kind field. What it adds is a durable record of *how* the learner scoped the goal (their text, a topic list, a syllabus page) and how that text was resolved to LOs.
- **The correspondence index is coverage, judged per LO.** Two sections across two books correspond when both treat the same learning object. Coverage is therefore one row per (section, LO), and correspondence is a join on the LO. That is O(sections), not O(sections²). The relation *between* two treatments (equivalent, different assumptions, different notation, disagreement) is judged only when someone looks: `compare_sources` already does it on demand, and RW4d's kept comparisons make the learner's judgments permanent. The vault's LO graph is the shared vocabulary. A smarter model doesn't remove it, because it is also what evidence, scheduling and certification are about.
- **The curated path generalises RW7a from one book to all of them.** RW7a asks one model call per source and depth to label its sections. Here one call per deliverable and depth reads the coverage of every needed LO across every source and picks, per LO, **one primary section** (the best treatment for this learner and this deliverable), keeps the others as **alternates**, adds **prerequisites** only where the learner hasn't demonstrated them, and leaves everything else off the path. Code enforces the honest-label rules RW7a already enforces, plus "exactly one primary per LO".
- **"Best for this learner" is the frontier model's judgment over the learner's own context**, never a weighted score. The context is the deliverable's text, the depth, what the learner has read and in which book, what they kept or rejected in comparisons, which passages they said didn't help, and their notes. The learner's swaps ("read it in Strang instead") are recorded as verdicts. A learned per-learner source preference is deferred, with a trigger (§13).
- **Notes are the learner's voice, linked, not ingested.** Grove/Org, Obsidian and Pocket Notes are already indexed on carson by the owner's `tend`. LearnLoop asks `tend` for candidates and a model proposes links from notes to the passages and LOs they discuss. A linked note is shown beside the book as the learner's own words. It is never a source LearnLoop teaches from, never a generation input, never evidence and never a claim.
- **Readiness is only delayed cold checks** (Check once, RW6b once it lands). Reading the path raises AD's *predicted* level through AD's existing reading opportunities. It never certifies anything (`spec_knowledge_model.md` §9.3, §9.5).

**What the bitter lesson cuts from the orchestrator's proposal:**

| Proposed | Verdict | Why |
|---|---|---|
| A stored section × section relation graph with typed edges | **Cut** | A model judges a pair better when it reads both, at the moment of use, with the learner's question. `compare_sources` does that already and stores it. Precomputing every pair is O(n²) paid judgments, most of which nobody reads. What has to persist is the learner's verdict (RW4d keeps) and the cheap per-LO coverage |
| A "best treatment" score (clarity × notation fit × depth match …) | **Cut** | That is a hand-weighted rule. The path judge reads the same signals as text and decides. Its choices and the learner's swaps are logged, so a learned preference can replace it later, with data |
| A syllabus parser or topic-list grammar | **Cut** | One resolution call reads whatever the learner pasted or photographed and maps it to LOs, listing what it couldn't match |
| An Org/Markdown parser and a note index inside LearnLoop | **Cut** | `tend` already chunks by heading, keys chunks by path, heading and content hash, and searches by words and meaning. LearnLoop calls it |
| Coverage of the whole library up front | **Cut to demand** | Coverage is judged for the LOs a deliverable needs, when it is created or changes. An owner-run batch covers more when wanted (as `learnloop reader label-roles` does for roles) |
| `complementary` as a relation | **Corrected** | `compare_sources` cannot emit it: its labels are `equivalent`, `different_assumptions`, `different_notation`, `disagreement`, `unclear` (`source_retrieval/compare.py:71`). How two sources complement each other is each one's distinct contribution. `complementary` exists only in RW4d's fine-to-coarse map (`kept_comparisons.py:101`) |

---

## 2. Standing constraints (binding)

- **Bitter lesson.** Frontier-model judgment over hand rules. Code keeps only what a smarter model doesn't remove: what may be shown, honest labels, evidence semantics, receipts, protection.
- **No made-up constants.** Every weight, margin or threshold is learned with a seeded, labelled prior (`prior_basis`), a structural bound, or a labelled `keep` guardrail. This spec introduces **no weights or thresholds**. Its numbers are the `keep` caps in §10.3, each with its reason.
- **Frictionless UX over transparency.** The path is a list of sections with a one-line why each. The glass box (coverage rows, who judged what, the resolution) is on demand. There is no jargon and no count of waiting things.
- **Learner text over skip buttons.** The deliverable is typed in the learner's words. A "this isn't what I need" reply is text the resolver reads.
- **Evidence, not mastery.** Reading the path, a linked note or a swap never marks anything known. "Already shown" needs `lo_certification(...).demonstrated`. "Am I ready?" means delayed cold checks.
- **Exam protection (A8, `exam_material`).** Exam questions and their solutions are never taught and never shown to a model as teaching (§9).
- **T1 transport.** Every model route is plan-first (`chatgpt_plan`). Background work is quiet: if the plan is down it waits, and nothing asks. A pressed action may offer OpenRouter (redesign D): the offer is the grant, keyed by the origin RPC method (§10.3).
- **Public repository.** No book text and no note text in the repo, fixtures or docs. Tests use synthetic notes.

---

## 3. Code truth (`main` at `fa2eb72f8` unless marked)

### 3.1 Goals, intent, deadlines, checks

| Fact | Where |
|---|---|
| `Goal`: `title`, `intent_sentence` (the learner's larger purpose), `creation_source` (`learner`, `source_ingestion`, `study_map`, `legacy`), `status`, `priority` (a tiebreak, not a weight), `target_recall`, `facet_scope` (concepts and facets), `due_at`, `exam` (`enabled`, `item_count`), confirmed-contract head. Goals live in `goals.yaml`, not SQL (`vault/paths.py:33`); SQL holds only their terminal contracts (`migrations/068_goal_terminal_contracts.sql`) | `vault/models.py:62-93`; `GoalFacetScope` `:47-54`; `GoalExamConfig` `:57-59` |
| Goals do **not** reference source sets yet. `source_set_ids` is named only in a docstring as a future field | `vault/models.py:164` |
| Quest resolution: an explicit `intent_sentence` wins, else the exam or practice scope, never a source-ingestion title | `goals/goal_intent.py:24` `resolve_goal_quest` |
| Creating a goal refuses concepts with no active LO unless `allow_empty_scope`. **No RPC edits a goal's scope, deadline or title**: there are only `create_goal`, `update_goal_status` (`:644`) and `update_goal_intent` (`:668`, the sentence only) | `learnloop_sidecar/handlers/goals.py:487` `create_goal`; input `:70-82` |
| DL2's deadline writer creates or updates a learner goal `goal_intent_<commitment>` with facets only and links it from a commitment version | `intent/deadline.py:78` `set_deadline`; RPCs `set_intent`, `set_intent_deadline` (`learnloop_sidecar/handlers/intent.py:77`, `:89`); `intent/control.py:432` `apply_choice` |
| The nearest active goal (used by re-entry) | `learnloop_sidecar/handlers/goals.py:112` |
| A goal's practice exam serves reserved, never-practised items and freezes predictions | `goals/exam_session.py:210` `start_exam` |
| DL2: commitments carry intent; `create_commitment` `:300`, `append_commitment_version` `:414`, `satisfy_single_check` `:717`; a deadline is a goal linked from a commitment version's `goal_id` | `curriculum/commitments.py`; `spec_daily_loop_v1.md` §5.1–5.4 |
| Check once: a `test_me_later` commitment, disposition `one_check_pending`, served once as a dated learner request (`due_hint` wins over `capture.test_me_later_days`); only an on-your-own attempt answers it, any other attempt is practice and re-dates it; settled by `settle_answered_checks` | `db/repositories.py:5077`; `scheduling/intent/serving.py:20-45`, `:130`; `intent/checks.py`; `spec_daily_loop_v1.md` §5.2 |
| `lo_certification(...).demonstrated`: direct, capability-matched, unassisted evidence on a blueprint's components (certification credit ≥ 1 per facet capability). **It does not require a delayed cold attempt**; the delayed cold probe is a later validity check | `goals/goal_certification.py:284-327`; `goals/certification.py:3-7`; `goals/certification_cold_probe.py` |
| AD's practice band is one vault-wide setting, applied per slot over its candidates | `config/schema.py:3719`; `adaptive_difficulty/selection.py:61-71` |

### 3.2 RW7a reading paths (per source)

| Fact | Where |
|---|---|
| Display only; kill switch `reading_paths.enabled` (default off) | `source_retrieval/reading_paths.py:1-36`, `:155-157` |
| **One path per extraction and depth.** Depth is chosen per source (`reader_path_depths.source_id`). Nothing spans two sources | `reading_paths.py:296` `path_inputs`, `:587` `depth_choice`; `migrations/217_reader_reading_paths.sql` |
| The judge's input: depth, the goal's title, and per sendable section its id, title, `book_roles` (`role_hint`), `proposed_roles` (RW4e) and topics (linked LOs with status) | `reading_paths.py:421-438` `build_prompt` |
| Withheld sections are never sent; a reading withheld whole, or whose exam check can't be read, is `withheld` | `reading_paths.py:309-317` |
| LO status: demonstrated, assumed (open `assumption_decisions`), learning, new | `reading_paths.py:245-270` |
| Honest-label rule, run after the model and again at display | `reading_paths.py:347-364` `honest_label` |
| `state_key` hashes prompt version, depth, section list, LO statuses, the goal id and the prompt itself | `reading_paths.py:206-224` |
| The goal a path serves: highest `(priority, id)` over `goal_for_item` per linked LO | `reading_paths.py:273-285`; `reader/reader_guidance.py:169` |
| Section → LO: no link table; LOs' (and their facets') provenance `source_refs` matched to the section's spans through the span-alias authority | `reader/reader_progression.py:31`, `:44`, `:66`; sections from `reader_guidance.py:313` |
| Table `reader_path_sections` (WORKFLOW, append-only); classified PROTECTED/READING for AD | `migrations/217_reader_reading_paths.sql`; `adaptive_difficulty/protected_tables.py:141`, `:372` |
| RPCs `reader.reading_path`, `reader.reading_path_set_depth`, `reader.reading_path_override` | `learnloop_sidecar/handlers/reading_paths.py:36-40` |
| Route `reading_path_judge` | `ai/routing.py:132`, `:253` |

### 3.3 RW7b (branch `reader/rw7b`, not on main)

- DL1's reading block keeps its order (U4's furthest-read, the front-matter rule, the exam filter), and the path **narrows** it to unfinished core and prerequisite sections: `daily_plan.reading.next_reading_target(..., section_filter=)` (branch `reading.py:81-83`), called from `_reading_on_path` (branch `engine.py:207`, `:1367`).
- `plan_path(vault, repo, extraction_id)` (branch `reading_paths.py:1250`) reads the current-key rows only. A stale path is not followed; a withheld path plans nothing. No model call in the plan.
- Gate `reading_path_plan_active` requires the plan, the tag, `reading_paths.enabled` **and** `reading_paths.plan_uses_path` (branch `engine.py:181-200`). Switching off reverts an unstarted reading (`:2845`).
- Receipt `split_json["reading_path"]`, version `reading_path_plan_v1`: `predecessor`, `chosen_by` (`path` | `order`), `label`, `same_as_predecessor`, `paths` (branch `engine.py:203-204`, `:266-273`, `:1431`).
- Successor `mvp-0.32` (branch `algorithm_versions.py:451`), no migration. Review: `docs/reviews/reader-workbench-RW7b.md` (open questions §7).

### 3.4 Sources, comparison, kept comparisons, roles

| Fact | Where |
|---|---|
| `compare_sources(vault, repository, query, *, caller, facet_ids, requested_perspectives, pinned_span_ids, …)`: policy derived from the caller; one `search_spans(consumer="compare")` per source in scope with a shared query vector; best 3 keys per source verified; `exam_withheld` on pins and hits; stored in `source_comparisons` (WORKFLOW) | `source_retrieval/compare.py:156`, `:189`, `:206-210`, `:245-361`; `migrations/189_source_comparisons.sql`; `db/table_roles.py:506` |
| Relation labels `equivalent`, `different_assumptions`, `different_notation`, `disagreement`, `unclear`; no consensus field | `compare.py:71`, `:83-104` |
| RW4d keep: RPCs `reader.library_compare_keep`, `…_remove`, `…_reopen`, `reader.kept_comparisons` | `learnloop_sidecar/handlers/kept_comparisons.py:38-41` |
| Kept claims are `source_object_versions` rows (`object_type` claim or definition, `authorship='ai'`, `status='proposed'`); relations in `source_object_relations` by `RELATION_MAP` (equivalent→supports, different_assumptions/different_notation/complementary→refines, disagreement→contradicts, unclear→unresolved; equivalent definitions→`alternate_definition`); "your take" is `learner_connects` with `learner_text`, `authorship='learner'` | `source_retrieval/kept_comparisons.py:97-104`, `:138-143`, `:284`, `:368-376`, `:407`, `:419`; `reader/source_objects.py:38`, `:45`, `:144` |
| CHECKs: `relation_type` ∈ supports, contradicts, refines, alternate_definition, unresolved, learner_connects; `review_status` ∈ proposed, reviewed, rejected, superseded. All four source-object tables are RAW_LEDGER | `migrations/094_source_objects.sql:62-69`; `table_roles.py:522-525` |
| RW4e roles: `source_object_versions.authorial_role` proposals; vocabulary definition, theorem, explanation, intuition, worked_example, exercise, figure, counterexample, contrast, prerequisite, alternative_treatment, application; batch `learnloop reader label-roles` | `reader/source_roles.py:64-68`, `:245`; `cli/reader.py:106-140`; `source_retrieval/role_labeller.py:388` |
| Multi-source provenance for authored entities: `entity_source_links` (relation ∈ primary, support, alternate, exercise, assessment_alignment) | `migrations/044_provenance_manifests_apply_intents.sql` |
| Learner-authored, span-anchored annotations with `privacy_locality='local_private'` | `migrations/090_source_annotations.sql` |
| Source roles: `notes` is a known role with no semantic authority (fail closed); `exam` has assessment alignment only | `content/sources/role_authority.py:25-67`, `:214` |

### 3.5 Retrieval

- Every source consumer goes through `search_spans` (`source_retrieval/search.py:274`). It takes a `consumer`, not a space. The resolver `resolve_source_spaces` (`source_retrieval/spaces.py:279`) picks spaces and fusion weights per query when local or fallback is enabled; otherwise today's single index runs (`spaces.py:76-80`, `search.py:414`).
- Default space `qwen` (`config/schema.py:2891`), `qwen/qwen3-embedding-8b` (`:2900`). `embedding.enabled` defaults false, so **dense retrieval may be absent**: keyword (FTS) must be enough for candidates (`spec_local_contextual_retrieval_v1.md` §1).
- Vectors are per block (`search.py:7-9`). There is no section-level vector.

### 3.6 Exam protection

- The predicate is `content/sources/exam_material.py`: exam members whole (rule 1), exam units (rule 2), `held_out_evaluation` units (rule 3), protected books' unmarked readings withheld whole (rule 4) (`:19-71`). Calls: `exam_withheld` `:986`, `reading_held_back` `:1028`, `spans_withheld` `:1105`, `exam_reserved` `:1488`.
- AD's A8 holds by construction inside a guarded operation with a protection epoch (`adaptive_difficulty/operation.py`, `protection.py`, `sending.py`, `material_view.py`; `spec_adaptive_difficulty_v1.md` A8, D25). Every table AD may touch is classified in `protected_tables.py`, checked by `tests/test_ad_protected_tables.py:38`.
- Exam and problem-set units whose use mode is `blueprint_only` or `available_for_practice` may steer targets; `held_out_evaluation` units never do (`content/synthesis/source_unit_selection.py:333`; AD §9.5).

### 3.7 Notes on this machine (read from docs only; no note was opened)

- **`tend`** (`~/.local/src/tend/SPEC.md`, v0.1, 2026-10-21) indexes grove (`~/Documents/thinking/notes`, Org), Markdown under `~/Documents/thinking`, Obsidian vaults, `~/Documents/Quicknote` (Pocket Notes) and `~/org/*.org` (§3).
  - Chunks are heading sections, keyed by `path#heading-path` plus a content hash. Storage is `~/.local/share/tend/tend.db` (FTS5 plus voyage-4 vectors).
  - Interface: `tend search [-k N] [--json] [--words] QUERY`, `tend related PATH:LINE`, `tend nearest`, `tend serve` (stdio JSON, with a `read` op). Results carry path, line, title, heading and snippet. Offline, it falls back to lexical search with a warning.
  - Its invariants: plain text is the source of truth; agents never write into notes; every external send is a documented choice. Note text already goes to Voyage (its embeddings decision).
- **Pocket Notes.** The repository (`~/Documents/thinking/3ds`) is **not on carson**. From `tend`'s SPEC §3b and §8a: 3DS pages are transcribed (Gemini 3.1 Flash Lite) into Quicknote Markdown and `pocket-inbox.org`, and `tend` indexes them. This spec relies on that and on nothing inside the 3DS project.
- There is **no notes import in LearnLoop today**. A Markdown note added through Add would be ingested as a `textfile` source and labelled a book (`ingest/resolution.py:11`, `:63-64`; `content/pipeline/add_source.py:100-111`), which is exactly what this spec avoids. The nearest pieces are the `notes` source role (fail-closed authority), `source_annotations` (learner-authored, span-anchored) and RW4d's `learner_connects`.

### 3.8 Not built yet

- TE1 (lessons, `LessonBriefV1`) is approved, not built: no `LessonBrief` in `src/`.
- RW6b (cold follow-ups valued by EIG/EVSI) is not landed. Check once is DL2's.
- Phone photos of handwritten work (mobile M2b) need `image_transcription`, which is not built (`spec_mobile_tailnet_v1.md:56`; `spec_image_dropin_ingest.md`).

---

## 4. What exists, and what is new

| Piece | Exists | New here |
|---|---|---|
| The deliverable | `Goal` with `intent_sentence`, `facet_scope`, `due_at`, `exam`; DL2 deadlines; TE §11.5 typed goals | **Scope inputs** (the learner's text, topic list, syllabus page) and their **resolution** to LOs, recorded (`deliverable_scope_inputs`, `deliverable_scope_resolutions`) |
| Which sections treat which LO | Provenance `source_refs` per LO (`reader_progression.py:66`), `entity_source_links` | **`section_coverage`**: a judged, cross-source (section, LO) table with treatment, roles and what the section assumes, plus the learner's corrections |
| Relations between two treatments | `compare_sources` on demand; RW4d kept relations | Nothing. Read as they are, and shown in skim-and-jump |
| A path through one book | RW7a, `reader_path_sections` | — |
| A path for a deliverable through all books | — | **`deliverable_path_sections`**: per needed LO one primary, alternates, prerequisites; the Guide shows the deliverable's slice per book |
| The plan follows a path | RW7b (one book at a time, branch) | **C1**: the plan follows the deliverable's order across books (a successor) |
| Notes | `tend` outside LearnLoop | **`learner_notes`** (snapshots of linked notes only) and **`learner_note_links`** (proposed and accepted links to passages and LOs); a `tend` adapter |
| Readiness | Check once (DL2); AD's "ready for exam level (predicted)"; demonstrated labels | **"Am I ready?"** on a deliverable: Check once commitments over its LOs; RW6b values them once it lands |
| Lessons | TE1's `LessonBriefV1` (not built) | Amendment: the brief's `goal` and `sources` come from the deliverable and its path; `your_notes` headers (C4) |

---

## 5. The deliverable

### 5.1 What it is

A deliverable is a learner goal (`creation_source = "learner"`). It is created from the learner's words. Its kind is shown, not stored, because every kind is already expressible:

| The learner says | What the goal carries | Shown as |
|---|---|---|
| "Linear algebra for machine learning" | `intent_sentence`; LOs resolved from it; no deadline | a quest |
| "Only what's on my midterm, Nov 12: chapters 1–4, eigenvalues, no proofs" | `intent_sentence`, `due_at`, `exam.enabled`; LOs resolved from the text, topic list or syllabus | an exam |
| "Understand enough to build the GRU gesture model" | `intent_sentence`; LOs resolved from it | a project (repo-linked projects are `spec_project_understanding_v1.md`'s, §13) |

**No new goal object, no kind field.** `resolve_goal_quest` already distinguishes explicit intent from exam and practice goals (`goal_intent.py:24`). The Guide's wording follows that.

### 5.2 Scope inputs (the learner's own words)

The learner describes the deliverable by any of:
- **text** ("only the midterm: ch 1–4, eigenvalues, no proofs");
- **a topic list** pasted from the course page;
- **a syllabus page**, as a passage of a source in the library (a selection in the Reader, or a whole short document);
- later, **a photo** of a handwritten list (§13).

Each is one append-only row in `deliverable_scope_inputs`. A correction ("not Jordan form; we skipped it") is another row: learner text over a delete button.

**What may never be a scope input** is exam material: a span `exam_withheld` refuses (§9.1). The learner is told in plain words: "This page is protected exam material, so LearnLoop won't read it. Type the topics instead."

### 5.3 Resolution

One model call (route `deliverable_scope_resolver`, a pressed action) reads:
- the inputs, in order;
- the vault's active LOs as compact records (id, title, statement, concept, prerequisites), never their items;
- the LO ids that practice-available exam and problem-set units of this subject map to (only ids, never their text; §9.2).

It returns:
- the LOs the deliverable needs, each with the phrase of the learner's input it answers;
- **phrases it could not match**, each with a proposed new LO statement.

Then code:
- validates every id;
- writes the goal's `facet_scope` through a new RPC, `curriculum.set_scope`, under the vault mutation lock, the way DL2's `set_deadline` writes a goal (`intent/deadline.py:78`; no goal RPC edits scope today): the concepts of the resolved LOs, plus facets where the learner's scope is narrower than a whole concept ("eigenvalues, not diagonalisation");
- creates a proposed LO for each unmatched phrase only when the learner confirms it, through TE §11.5's `create_goal_lo` path (the learner's request is the decision; `origin = codex_proposal`, `mechanism = deliverable_scope_v1`). Before TE2 builds that action, C0 builds it once, to TE §11.5's design, and TE2 takes it over (built once).

**What the learner sees:** "For your midterm: 14 topics from your books · 2 not in your library yet (Jordan form? no — you said skipped) · change". Each topic is one line; *not this* and *add* are text boxes. The resolution's receipt (`deliverable_scope_resolutions`) is on demand.

**Re-resolution** happens only when an input is added. Nothing re-resolves on its own.

### 5.4 Depth

A deliverable has one depth (RW7a's `get_the_idea` / `learn_to_use_it` / `fluency`), asked once ("How deep for this?"). When the learner sets DL2's intent on the deliverable, RW7a's `INTENT_DEPTH` maps it, so it stays one setting. It is stored as a scope input (`kind = 'depth'`), the newest standing.

---

## 6. The correspondence backbone: section coverage

### 6.1 Data

`section_coverage` (WORKFLOW: paid outputs, never re-run on rebuild; append-only by triggers, as `reader_path_sections`):

| Column | Meaning |
|---|---|
| `id` | |
| `extraction_id`, `section_id` | The section, on one reading (section ids from `extraction_sections`) |
| `learning_object_id` | The LO it treats |
| `treatment` | `introduces` · `develops` · `applies` · `mentions` · `not_about` (a structural vocabulary describing the section, not a weight) |
| `roles_json` | The roles the judge saw or proposed for the section's passages (RW4e vocabulary) |
| `assumes_json` | LO ids the section takes as known (the judge's reading; feeds prerequisite choice) |
| `notation_md` | One line, when the section's notation differs from the LO statement's ("uses row vectors") |
| `origin` | How the candidate arrived: `provenance` · `retrieval` · `learner` |
| `learner_override` | NULL for a judge row; `is_about` · `not_about` · `none` (cleared) for the learner's correction |
| `state_key` | Hash of the LO statement, the section's block hashes, the candidate set and the prompt version |
| `ledger_id` | `judgment_ledger` (task `section_coverage`; judge `llm`, or `learner_card` for corrections) |
| `model`, `prompt_version`, `created_at` | |

The newest learner row per (section, LO) stands over judge rows. A changed `state_key` writes new rows, and old ones are no longer read (RW7a's pattern).

### 6.2 How it is built

**Per LO, listwise, on demand.** For each LO a deliverable needs (and its prerequisite closure to the depth the path needs, §7.2):

1. **Candidates, without a model:**
   - **provenance:** the sections whose spans the LO's (and its facets') `source_refs` hit (`learning_objects_for_section`);
   - **retrieval:** `search_spans(consumer="coverage")` with the LO's title and statement as the query, **once per source** in the library scope, as `compare_sources` does, so no book is crowded out (keyword always; meaning through whatever space the resolver makes available; §3.5). Hits are grouped to their sections;
   - **learner:** sections the learner linked by hand (§6.5), and the passages of kept comparisons on this LO.
2. **Filter before any model sees anything:** `exam_withheld` on every span, `reading_held_back` per extraction, solution and exercise blocks dropped (`role_hint`), as `path_inputs` does.
3. **One listwise judgment** (route `section_coverage_judge`, through `judge_listwise`): the LO, and per candidate section its title, its role labels and its lead passages (verbatim, bounded per section by the prompt bound in §10.3). It returns per section its `treatment`, roles, `assumes` and notation line. Every section it names must be a candidate (validated). Each passage it judges also yields RW4e role proposals, at no extra call, through RW4e's existing writer (a fourth judge, `section_coverage_judge`, added to `source_roles.py:70-73`).

**Why per LO, not per section.** The deliverable asks "where is X treated?", and one call per LO reads all its candidates together, so the judge can compare treatments while deciding. A per-section pass would read every section of every book to find the few that matter.

**Whole library, when wanted.** `learnloop curriculum cover --source <id> [--dry-run]` (owner-run) walks a source's sections and judges them against the LOs their candidates suggest, with its own spend cap. It never runs on a hot path. This is how a library gets correspondence for LOs no deliverable has asked about yet.

### 6.3 When it is re-judged

- When a deliverable is created or its scope changes: only the LOs that are new, or whose `state_key` changed.
- When a source is added or re-read (a new extraction): its candidate sections for already-covered LOs join the next judgment of those LOs. This runs as a background job on the extraction's completion and is coalesced per LO.
- When an LO's statement changes.
- **Never** because of learner state. Coverage describes books, not the learner. That is why it is shared across deliverables and outlives any one of them.

### 6.4 What it powers

- **Skim and jump** (the companion UX spec): from a section, its correspondents are the other books' sections whose coverage names the same LO with `treatment` other than `not_about`, ordered by `treatment` (`introduces` and `develops` first) and then by retrieval rank. Each carries the relation the learner kept, if any ("you compared these on 3 Oct: different notation"), else none. **Read API:** `reader.correspondents(extraction_id, section_id)` → per LO, per other source, the sections with treatment, roles, notation line, kept relation and a `jump` locator. No model call. A section with no coverage yet returns the live `search_spans` hits per source, labelled "found by search, not checked" (no model, no write).
- **Compare from anywhere** (the companion UX spec): pressing Compare on a correspondent pins both sections' passages into `compare_sources` as today. Nothing new on the backend.
- **The curated path** (§7).
- **Teacher grounding** (§8.2) and **find_sources** as one more ranked list for `explain` (`spec_source_practice_and_probes_v1.md` §9.2's "source objects add a list" pattern): a (section, LO) row with `introduces` or `develops` is a candidate for that LO. Retrieval stays context (T6's ruling), so this is no successor.

### 6.5 The learner's corrections

On any correspondent or path line: *not about this* and *also about…* (a text box: "this is really about orthogonal projection"). The text is resolved to an LO by the same resolver as scope inputs, without a new route, and written as a `learner` row. Corrections are ground truth for coverage and are counted in the coverage report (§11) as the judge's error rate.

*As built (Reader CA5a's fix round, `docs/reviews/reader-ca5a-find-section-codex-review.md`):* on an unchecked search hit (no LO of its own), *not about this* is one operation in one transaction: a section-pair `learner_card` verdict in `judgment_ledger` (task `section_correspondence`, `reader_section` → `reader_section`, the operation's record, idempotent by the client's operation id) plus a `learner` row per LO of the open section. A section with no LO gets the pair verdict only; no LO is inferred from search similarity. The pair verdict only hides the hit in that section's unchecked list; it is never coverage, evidence or a judge-error count.

### 6.6 What it never does

- It is never evidence, never a prerequisite edge, never a provenance link. It does not write `source_refs`, `entity_source_links`, `relations.yaml` or LO status (P3 §7.3; RW4d's rule). Promoting a coverage row to provenance would be a canonical change through the existing proposal review, and is not in this spec.
- It never reads learner data. That keeps it shareable across vaults' futures (n > 1) and keeps A8 simple (§9).

---

## 7. The curated path across all sources

### 7.1 Labels

| Label | Meaning | Honest-label rule (code) |
|---|---|---|
| **core** | The primary section for a needed LO: read this one | Exactly one per (deliverable, depth, LO); the LO is in the deliverable's resolved scope; the section's coverage for that LO is `introduces` or `develops` |
| **prerequisite** | The primary section for an LO the core sections assume, which the learner hasn't demonstrated | The LO is in the needed LOs' prerequisite closure (`LearningObject.prerequisites`) or in a core section's `assumes`; not demonstrated; not assumed |
| **alternate** | Another book's treatment of a needed LO, kept one tap away ("another way: Strang §2.3, more geometric") | Its coverage names the LO; it is not the primary. Never planned |
| **already shown** | Every LO the section is primary for is demonstrated | `lo_certification(...).demonstrated` for each (RW7a's rule) |
| **assumed** | Only open `assumption_decisions` LOs | RW7a's rule |

Anything that fails its rule falls back to `core` for a needed LO, as RW7a does. **Sections of no needed LO are not on the path.** In a book's own view they show as "not needed for your midterm · read it anyway" (a display state, not a stored label).

### 7.2 How it is chosen

One call per deliverable and depth (route `deliverable_path_judge`, background):
- **Input:**
  - the deliverable: its sentence, its resolved LOs with the phrases they answer, its deadline and depth;
  - per needed LO and per prerequisite LO (closure to the depth's reach, structural: `fluency` and `learn_to_use_it` read the closure to depth 2, `get_the_idea` to depth 1, labelled `keep` with RW7a's depth semantics as the reason), its status (RW7a's four), and its coverage rows across sources;
  - **the learner's own context**, as text: which sources they have been reading (`reader_section_progress`), passages they said didn't help (RW1c's "that didn't help" rows), kept comparisons and their takes on these LOs, swaps they made on earlier paths, and linked notes' headings (C2 on);
  - the minutes available before the deadline, from DL1's estimates (`spec_daily_loop_v1.md` §6.4), so the judge can prefer a shorter treatment when time is short.
- **Output:** an ordered list (prerequisites before what assumes them), one primary per LO with a one-line why ("Axler §5.B: proves it the way your exam asks, and you've been reading Axler"), alternates per LO with a one-line difference, and one exercise worth trying per core section (RW7a's `pick_exercises` rule, read across the chosen section's book).
- **Code:** validates ids and the one-primary rule, applies the honest-label rules, writes `deliverable_path_sections` and a `judgment_ledger` verdict (task `deliverable_path_role`).
- **Cache key** (`state_key`): the depth, the resolved scope, the coverage rows' ids, the LO statuses, the learner-context digest and the prompt version. A changed key is judged on the next Guide open, or by a background job when C1 needs it for tomorrow's plan.

**"Best treatment for this learner", without weights.** The judge is told what "best" means for this deliverable in plain words ("the treatment that gets this learner to do what the deliverable asks, in the time left, building on what they have read") and given the context above. It is not given a scoring formula, and code never re-ranks its choice. The learner's swaps and skips are verdicts on it. Whether a different choice would have produced better cold checks is a question for the learned preference (§13), which needs the logged choices this design writes from day one.

### 7.3 Learner overrides

- **Use this one instead** (on an alternate): the alternate becomes core for that LO, and the old primary an alternate. A `learner_card` verdict; it stands across re-judgments (the newest learner row per (deliverable, LO) wins), as RW7a's overrides do.
- **Read it anyway** / **skip it**: RW7a's semantics. Skip marks nothing as known.
- **I know this — check me later**: creates a Check once on that LO (DL2's `test_me_later`, `provenance = {via: "deliverable_path", goal_id}`) and takes the section off the plan until the check is answered. A failed check puts it back. This is the honest form of "already know it": a cold check, not a claim.
- **Text**: *not what I need…* on any line goes to the scope resolver as a new input (§5.2).

### 7.4 Data

`deliverable_path_sections` (WORKFLOW, append-only):
`id`, `goal_id`, `depth`, `learning_object_id`, `extraction_id`, `section_id`, `label` (`core`, `prerequisite`, `alternate`, `already_shown`, `assumed`), `ordinal`, `reason`, `exercise_span_id`, `learner_override` (`use_instead`, `read_anyway`, `skip`, `check_later`, `none`), `state_key`, `ledger_id`, `model`, `prompt_version`, `created_at`. A unique index on judge rows per (goal, depth, state_key, LO, section).

### 7.5 What changes in RW7a

- **Data: nothing.** `reader_path_sections` and `reader_path_depths` are unchanged.
- **Display.** When `curriculum.enabled` is on and an active deliverable's path names sections of the open source, the Guide's path card shows **the deliverable's slice for this book**: its core, prerequisite and alternate sections here, labelled; sections of no needed LO shown as "not needed for <deliverable>"; and, where a needed LO's primary is in another book, one line ("eigenvectors: on your path in Strang §6.1 ▸"). A toggle *this book alone* shows RW7a's own path, judged on demand as today.
- **One producer per view.** While the deliverable slice is shown, RW7a's judge is not called for that source. Its rows stay valid for *this book alone*.
- **Which deliverable.** The one `goal_for_source` already picks (`reading_paths.py:273-285`, highest `(priority, id)` over the linked LOs' goals), so RW7a's goal line and this slice never disagree.

### 7.6 What changes in RW7b (C1, a successor)

- **The order changes.** RW7b narrows *one book's* predecessor order to its path. C1 makes the deliverable's ordinal the order: the plan's reading block opens the next unfinished core or prerequisite section **in the deliverable path's order, in whichever book it is**. The predecessor's front-matter rule and exam filter still run first on each candidate, and DL2's intent filter (`reading_allowed`) still applies.
- **Which deliverable.** The nearest active goal, by the existing rule (`handlers/goals.py:112`), among goals with a fresh deliverable path. Only one reading block a day is planned today, so no interleaving rule is needed.
- **Where it plugs in.** `_reading_on_path` (branch `engine.py:207`) gains a first branch: when `deliverable_plan_active(vault)` and a fresh deliverable path exists, choose from `deliverable_plan_path(goal)`, a sibling of RW7b's `plan_path` that reads `deliverable_path_sections` by the same stale/withheld/unreadable rules. Otherwise RW7b's per-book path runs unchanged, then the predecessor's order.
- **Receipts.** `split_json["reading_path"]` moves to `reading_path_plan_v2`. It keeps v1's keys and adds `deliverable` (goal id, path state key, the row ids read) and `chosen_by = "deliverable"`. `predecessor` is now **RW7b's** choice (what the per-book path would have opened), so the receipt states exactly what the successor changed.
- **Successor.** The next free `mvp-0.N` after RW7b's `mvp-0.32` (renumbered at merge). No migration beyond C0's. Upgrade function per the playbook; shadow rebuild with zero projection deltas (it changes serving, not projections).
- **Kill switch** `curriculum.plan_uses_path` (and `curriculum.enabled`, as RW7b's open question 1 gates the plan on the Guide's switch). Off: RW7b's plans, byte-identical (gate G-C4).
- **Stale path:** not followed, as RW7b (no model call from the plan). Because the deliverable path's key includes learner state, C1's background job re-judges a stale deliverable path once a day before the plan is built, quietly (plan route only; if the plan is down, the plan falls back to RW7b and the receipt says `stale`).

---

## 8. What it drives

### 8.1 The daily plan (RW7b → C1)

§7.6. Beyond reading: the deliverable's LOs are the goal's frontier, so DL2's push lane already serves them (`spec_daily_loop_v1.md` §5.4). Nothing else in the plan changes.

### 8.2 Teacher lessons (TE1)

An amendment to `spec_teacher_v1.md`, recorded there when C4 lands:
- **`LessonBriefV1.goal`**: the deliverable's sentence, its LO ids and "how they were resolved" = the resolution receipt's phrase per LO (§5.3).
- **`sources`**: for each brief node, its **primary section** from the deliverable path, whole, then alternates as outline only, still through `teaching_scope` with exam and withheld roles removed. Today TE1 would send "the goal's sections"; with a deliverable, those are the path's sections, so a lesson teaches from the book the path chose and can say "your other book does this with matrices; want that view?".
- **`your_notes`** (C2 on): per node, headers of the linked notes (title, heading, date, one line), with the note text through a `read_note` action. It is the learner's voice, labelled so; the doctrine says to use it as what the learner already thinks, not as a source of truth.
- **Router-suggested lessons** (TE1b) may name a deliverable LO whose primary section was read but whose cold checks failed. That is the router's choice, and the deliverable adds no rule.

### 8.3 Adaptive difficulty

- **No change to AD.** AD's band is one vault-wide setting (`config/schema.py:3719`) applied per slot, and its draws are per LO and cell; the deliverable decides which LOs are on the frontier, so AD's band applies to the deliverable's LOs through the existing serve path.
- **Reading on the path is already an AD learning opportunity** (`spec_adaptive_difficulty_v1.md` §5.11): a primary section read is a section completion of that reading, with its learned dose curve. It raises the predicted level, never evidence (A12). A reading with withheld blocks is absent for AD's reading signals (Option B), whatever the path says.
- **"Ready for exam level (predicted)"** (AD §9.5) is the deliverable's readiness *prediction*, shown labelled as a prediction; untested stays untested.
- New tables are classified for AD (§9.4).

### 8.4 DL2

- The deliverable's deadline is the goal's `due_at`. A deadline set from a commitment (DL2 §5.4) and a deadline typed in the deliverable are the same field.
- **The intent control on a deliverable** fans out to one commitment over its LOs, linked by `goal_id`, as a subject or source control does today. Setting it also sets the deliverable's depth (§5.4).
- Recall targets follow the commitment's intent (DL2 §5.3); the goal's `target_recall` stays the goal report's.

### 8.5 "Am I ready?" (Check once, then RW6b)

- **A button on the deliverable**, never a prompt. It creates one Check once per needed LO that isn't demonstrated and has no pending check, through `create_commitment(action = "test_me_later", …, provenance = {via: "deliverable_ready", goal_id})`.
  - Items come from `find_practice` with TE §13's candidate rule (unattempted; no reveal; never served to a chat host; not from a family shown on the path's exercises), and never an exam-reserved item (`exam_reserved`).
  - Dates are written as the commitment's `due_hint`, which DL2's serving already prefers (`scheduling/intent/serving.py:130`), from retrievability as TE §13 dates them (`R*` a seeded prior, basis `published`; the 14-day `keep`), and are bounded by the deadline: a check is never dated after `due_at`.
- **When RW6b lands**, its valuation chooses and dates these checks, and this picker retires (one producer).
- **The answer to "am I ready?"** is the deliverable's line: per LO, *demonstrated* (unassisted, capability-matched evidence; `lo_certification`), *likely* (AD's labelled prediction) or *untested*, and the dated checks still to come. It never counts what was read, and it never says "ready" from in-session success.
- **For an exam deliverable with `exam.enabled`**, the goal's existing practice exam (`start_exam`) remains the whole-exam rehearsal, unchanged.

---

## 9. Exam scoping and protection

### 9.1 Scoping never reads protected material

- A scope input that is a span runs `exam_withheld` first; a withheld span is refused (§5.2). A syllabus added as a source **must not carry the `exam` role**, or rule 1 withholds it whole. C3 adds a `syllabus` source role with assessment-alignment authority only (`role_authority.py`'s matrix: `(False, True)`), never practice and never protected (Q2, DECIDED 2026-10-25).
- The resolver never sees a held-out unit, an exam-reserved item, or any exam question text.

### 9.2 What exam material may contribute

- **Practice-available exam and problem-set units** (`blueprint_only`, `available_for_practice`) contribute their **LO mapping only**: "your past papers test these LOs". Their text is not sent; the ids are enough to scope, and sending less is safer.
- **Held-out units** (`held_out_evaluation`) contribute nothing, ever. They stay evaluation only (AD §9.5's report may compare the deliverable's ladder with them, unchanged).

### 9.3 Teaching never shows exam questions

- Coverage, the path, correspondents, the companion UX surfaces and teacher grounding read only through `exam_withheld`, `reading_held_back` and `spans_withheld`, before any candidate reaches a model or a screen.
- **`exam`-role sources are never a primary or an alternate.** They have no semantic authority (`role_authority.py:51`), so they never teach.
- **Notes are never a generation input** (§10.2). A note that copies an exam question is therefore never turned into an item, never sent to a generator and never used as teaching context. It is shown only beside the passages it was linked to, in the learner's own voice.
- **"Only for my exam"** narrows what is taught. It never means teaching the exam: readiness checks exclude exam-reserved items, and the practice exam's pool is the existing reserved pool.

### 9.4 AD classification

`section_coverage`, `deliverable_path_sections`, `deliverable_scope_inputs`, `deliverable_scope_resolutions`, `learner_notes` and `learner_note_links` are classified in `adaptive_difficulty/protected_tables.py` (`ROLES`, `COLUMNS`, and `READING` for the tables that reference a reading's sections or spans), as `reader_path_sections` is. AD reads none of them. The contract test (`test_ad_protected_tables.py:38`) keeps that true.

### 9.5 Gates

- **G-C1 (sentinel):** a held-out unit and an exam-role source carry sentinel strings. No `section_coverage_judge`, `deliverable_path_judge`, `deliverable_scope_resolver` or `note_link_judge` request captured by `StructuredClientFake` contains them, and no correspondent, path row or brief names their spans.
- **G-C2:** a syllabus span with the exam role is refused as a scope input.
- **G-C3:** readiness checks never pick an `exam_reserved` or held-out item.

---

## 10. Notes in the learner's voice

### 10.1 Adapters

- **One adapter: `tend`** (`curriculum/notes_tend.py`). It calls `tend search -k K --json [--words] QUERY` and `tend serve`'s `read` op as subprocesses, with a timeout. (`tend`'s SPEC names the `read` op for opening remote hits; C2 confirms its output shape first, and falls back to reading the heading's line range from the file, inside the allowlist.) LearnLoop never parses Org or Obsidian Markdown itself and never builds a note index. Through `tend` this covers grove (Org), Obsidian vaults, Markdown notes under `~/Documents/thinking`, and **Pocket Notes** (3DS handwriting transcribed into Quicknote by Pocket Notes' worker).
- **An allowlist** (`notes.tend.paths`) limits which of `tend`'s folders LearnLoop may use. Its default is grove notes, Quicknote, the Obsidian vaults and **`~/org`**, the owner's planning notes (Q5, DECIDED 2026-10-25). `~/org` is reached as `tend` indexes it (`tend`'s corpus names `~/org/*.org`). Whether a file there, such as the profile `me.md`, is reachable is `tend`'s corpus setting, not LearnLoop's. **Project repositories stay excluded.** A hit outside the allowlist is dropped before anything is stored or sent.
- **`~/org` is private planning text, and the privacy rules apply to it unchanged** (§10.2, §10.4). Only the ChatGPT plan model reads its text. Only linked sections are stored. A planning note is never a source and never evidence, exactly like any other note.
- **Later: phone photos** of handwritten notes, through `image_transcription` (mobile M2b / `spec_image_dropin_ingest.md`). The transcript is shown for the learner to correct before it is kept, as that spec requires (§13).
- When `tend` is absent (a contributor's machine), the notes features are hidden. Nothing else depends on them.

### 10.2 Voice and status

A linked note is the learner's own text:
- Shown in the learner's voice (`›`, UX §3.4's third voice), with its title, heading and date, and "handwritten · transcribed by Pocket Notes" for a Quicknote page.
- **Never a source** (no `source_artifacts` row, so never in `find_sources`, `teaching_scope` or a comparison's counterparts), **never a generation input** (PF, S1, need fulfilment and the teacher's item minting never read `learner_notes`), **never evidence** (no attempt, no claim, no self-report, no AD reading opportunity: a note is not one of AD's four discrete reading kinds).
- **Read for gaps only by opt-in** (C5): a linked note may then be a learner-text-gaps input (`source_kind = 'learner_note'`), tier 2 only (steers hypotheses and routing, never mastery), with *ⓘ where this goes* saying so (UX §4.10).

### 10.3 Links

- **Candidates (no model).** For each core and alternate section on a deliverable path and for each needed LO: `tend search` with the LO's title and the section's title. Candidates are heading sections within the allowlist.
- **One listwise judgment per LO** (route `note_link_judge`, background): the LO, its primary passage's lead, and the candidate notes' text (read through `tend`). It returns per note `discusses` (with the passage or LO it discusses and one line on how: restates, questions, disagrees, applies, worked it), or `unrelated`.
- **Stored as proposals** in `learner_note_links` (`authorship = 'ai'`, `status = 'proposed'`). A proposal is shown as "from your notes" (labelled "linked by LearnLoop's model"), and one tap hides it (`rejected`, a `learner_card` verdict). Keeping it (`accepted`) needs no tap: frictionless defaults. The learner can also link a note by hand from the Reader (`authorship = 'learner'`).
- **Where links show:** a `›` mark in the margin beside the passage (the learner's own mark, outside the cue budget, like `⇄`); on the deliverable path line ("your note from 3 Oct"); in Compare's *your take* band, with *use as my take*, which writes RW4d's `learner_connects` relation quoting the note (RW4d's existing write, no new relation); in the teacher's brief (§8.2).
- **Snapshots.** `learner_notes` stores a snapshot of a note section **only when it is linked** (proposed or accepted): its `tend` reference (path, heading path, line), content hash, title, heading, captured date, origin (`tend` | `pocket_notes` | later `phone_photo`) and the text, bounded per note. When `tend` reports a new content hash, the snapshot is refreshed and the link re-judged. Notes are never written back to: `tend`'s invariant 2 forbids agents writing into notes, and LearnLoop proposes nothing into `~/org/proposals.org` in v1 (§13).

### 10.4 Privacy

- Notes stay on carson. Candidates are read from `tend` on carson; snapshots live in the vault, which lives in the private data root on the hub and is backed up encrypted (`spec_storage_sync_v1.md` §6). No note text is ever in the public repository: tests use synthetic notes, and G8 (`test_public_tip_guards.py`) already rejects tracked databases.
- **A model reads note text only on `chatgpt_plan`**, and only in `note_link_judge` and (C4) the teacher's `read_note`. Note linking is background-only, so it is never offered OpenRouter: if the plan is down, it waits. The teacher's `read_note`, inside a pressed lesson that has an OpenRouter grant, follows the lesson's grant (Q6, DECIDED 2026-10-25).
- **`tend`'s meaning search embeds its query through Voyage**, `tend`'s documented choice. LearnLoop's queries are LO titles and section titles, never passages or note text. With `notes.tend.lexical_only = true`, LearnLoop uses `--words` and nothing leaves the machine (Q7, DECIDED 2026-10-25).

---

## 11. Measurement (honest time-to-signal at n = 1)

`learnloop curriculum report` (aggregates only, read-only):

| Question | Signal | When it can say something |
|---|---|---|
| Does coverage find the right sections? | Learner corrections per judged (section, LO) row; correspondents opened, compared or kept | Days. Every correction is a labelled error |
| Is the primary choice right? | *Use this one instead* swaps and skips per path line; alternates opened | A week of reading |
| Does the path save time? | Minutes read on the deliverable's LOs against the predecessor's estimate for book order (DL1's estimates for the sections the path left out) | A week; it is an estimate and is labelled so |
| Did the learner learn what the deliverable needs? | Delayed cold checks on the deliverable's LOs: share right, by LO, with intervals | Weeks. At n = 1 it has no counterfactual. It says whether the learner is ready, not whether the path caused it |
| Did reading the primary help more than reading an alternate? | Per LO, cold outcomes after primary vs alternate reads | Not answerable soon: few LOs, the learner's choices confounded with difficulty. Logged for the learned preference (§13) |
| Notes | Links hidden vs kept; *use as my take* | Days |

**What it never reports as success:** sections read, path completion, time on the page, or in-session answers. An exam deliverable's real exam is one outcome; the report records it, if the learner enters it, as one data point.

An n = 1 alternating design (half the deliverable's LOs on the curated path, half in book order, both followed by cold checks) would estimate the path's effect for this learner. It withholds curation on purpose, so it runs only if the owner opts in (§13).

---

## 12. Phases, kill switches, successors

| Phase | Contents | Persisted meaning | Kill switch (off restores) |
|---|---|---|---|
| **C0: the backbone and the path, display only** (first slice) | One migration: `deliverable_scope_inputs` (RAW_LEDGER), `deliverable_scope_resolutions` (WORKFLOW), `section_coverage` (WORKFLOW), `deliverable_path_sections` (WORKFLOW). Scope from text or a topic list (§5.2–5.4), with `create_goal_lo` built once to TE §11.5. Coverage per LO on demand (§6.2), `learnloop curriculum cover`. `reader.correspondents` (§6.4). The deliverable path (§7.1–7.4) and the Guide's slice (§7.5). Overrides including *check me later* (§7.3). "Am I ready?" (§8.5). The report's coverage, choice and time rows. Routes `deliverable_scope_resolver`, `section_coverage_judge`, `deliverable_path_judge` | **None.** Display, retrieval context, proposals, and learner-pressed Check once commitments served by DL2's unchanged rule (the RW1b reconstruct precedent) | `curriculum.enabled` (today's Guide and RW7a), `curriculum.coverage_on_extract` |
| **C1: the plan follows the deliverable** | §7.6 | **Successor** after RW7b's `mvp-0.32`; receipts v2 | `curriculum.plan_uses_path` (RW7b's plans, byte-identical) |
| **C2: notes linked** | `learner_notes` and `learner_note_links` (RAW_LEDGER; one migration); the `tend` adapter and allowlist; route `note_link_judge`; margin `›` marks, path lines, *use as my take* | None (display; learner-voice records) | `notes.enabled`, `notes.tend.lexical_only` |
| **C3: exam scoping from a syllabus** | The `syllabus` source role (Q2); practice-available exam units' LO mappings in resolution (§9.2); G-C1..C3 hardened on a fixture with every kind of exam material | None | `curriculum.exam_units_in_scope` |
| **C4: the teacher reads the deliverable** | §8.2's `LessonBriefV1` amendment; `read_note` | TE1's successor carries it if TE1 is unlanded; else none (context only) | `teacher.brief.use_deliverable` |
| **C5: notes as learner text** | `learner_text_gaps.source_kind` widened with `learner_note` (a FK-safe rebuild, as migrations 208 and 212 did); only linked notes; *ⓘ where this goes* | None (tier 2, the learner-text-gaps precedent) | `notes.gaps_enabled` (default off: opt-in, Q9, DECIDED 2026-10-25) |

**The smallest valuable first slice is C0 for one deliverable.** It answers both owner questions on day one: what to read across all books for this goal (the path), and where else each section is treated (the correspondents for skim-and-jump). It changes no plan and no evidence. If C0 is too large for one stage, split it at the seam: **C0a** coverage plus `reader.correspondents` (unblocks the companion UX spec), then **C0b** scope resolution plus the path.

**Order and dependencies.** C0 after RW7b lands (it reuses RW7b's `effective_label` extraction and is the base C1 changes), in parallel with TE1. C1 after C0 has run on real deliverables for a week (overrides read). C2 any time after C0. C3 with or after C0. C4 with TE1 or after it. C5 after C2, on the owner's opt-in.

### 12.1 Routes, caps and transport (T1)

| Route | Kind | When it runs | T1 |
|---|---|---|---|
| `deliverable_scope_resolver` | chat | Pressed (create or change a deliverable) | Plan first; on plan failure the pressed action may offer OpenRouter (redesign D), the grant keyed by the origin RPC `curriculum.set_scope` |
| `section_coverage_judge` | listwise | Background jobs spawned by a deliverable change or an extraction | Quiet. Spawned jobs capture `unit_origin()` at creation, so a grant on `curriculum.set_scope` covers the coverage of that change in that session; otherwise they wait for the plan |
| `deliverable_path_judge` | chat | Guide open (on the Guide's existing background thread), C1's daily job | As above, origin `reader.reading_path` for the Guide; C1's job is quiet only |
| `note_link_judge` | listwise | Background | Quiet only; never offered OpenRouter (note text, §10.4) |

- **Caps** (`keep`; each a money or prompt bound, not a model parameter): `curriculum.max_daily_cost_usd` for metered fallback spend (reason: unapproved spend is the realistic harm); `curriculum.cover_max_cost_usd` per owner-run batch (as `roles.batch_max_cost_usd`); per-call prompt bound `curriculum.max_prompt_tokens` (as `source_service.compare_max_prompt_tokens`, reason: the context window). Each route gets a `METERED_PRICE_SETTINGS` entry so the offer has a price gate.
- **Cost shape on the plan.** A 30-LO deliverable is about 30 coverage calls (each the LO plus ≤ 3 sections per source with their lead passages) and one path call. That is rate-limit headroom, not money.
- **Ledger tasks:** `section_coverage`, `deliverable_path_role`, `deliverable_scope`, `note_link`, each with `learner_card` rows for the learner's corrections.

### 12.2 Persistence

- Migrations numbered at merge (`ls migrations/`; head 220 on `main`). Each new table classified in `db/table_roles.py` and in AD's `protected_tables.py` (§9.4). **No DERIVED table, so no replayer.** Replay never reads these tables. The evidence they lead to (attempts on checks) lives where replay already reads it.
- Head-fixture procedure per `CLAUDE.md` for each migration.
- Config sections `[curriculum]` and `[notes]`; each phase records "no scoring, scheduling, projection or serving change" in the defaults snapshot, except C1, which records its successor.

### 12.3 Tests (targeted while iterating; the full suite once at landing)

- C0: honest labels (one primary per LO; `already_shown` only when demonstrated; an unknown section id refused); coverage candidates per source (a big book never crowds out a small one); correspondents with no coverage return search hits labelled unchecked and write nothing; the scope resolver's unmatched phrases never create an LO without the learner's yes; `curriculum.enabled = false` leaves every RW7a RPC byte-identical (parity on fixture copies); G-C1, G-C2, G-C3.
- C1: G47-style: `curriculum.plan_uses_path = false` gives RW7b's plans byte-identical; a stale deliverable path is not followed; a withheld section is never the step; the receipt's `predecessor` equals RW7b's choice; shadow rebuild with zero projection deltas.
- C2: an allowlist miss is never stored or sent; no `learner_notes` text in any generation, grading, diagnosis or AD request (a sentinel note); hidden links stay hidden across re-judgments; `tend` absent hides the features.
- Every test uses `StructuredClientFake`; no model calls; any ad-hoc script runs under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

---

## 13. Deferred, with triggers

| DEFERRED | What it would take | Revisit when |
|---|---|---|
| **A learned per-learner source preference** (which book's treatments lead to better cold checks for this learner) | Logged primary choices and swaps with cold outcomes per LO (written from C0); a model of preference by source and treatment with shrinkage; logged propensities, which means sampling among treatments the judge marks acceptable | Enough deliverable LOs have matured cold outcomes after both a primary and an alternate read that an interval excludes no difference, *or* the owner asks to explore books on purpose |
| **A precomputed section × section relation index** | Pairwise judgments over all corresponding sections | The companion UX's correspondents are opened often and Compare is pressed on most of them, so on-demand comparison latency is the measured bottleneck |
| **Full-library claim index** (RW §17) | Unchanged from the Reader spec | Unchanged: kept comparisons exceed 10 a month and the owner asks to browse claims |
| **Deliverables across vaults** ("LA for ML" spans `linear_algebra` and `probability`) | One learner state across vaults, which the storage spec keeps separate (§1, "each vault stays a separate learner state") | The owner merges vaults or asks for a cross-vault deliverable |
| **Repo-linked project deliverables** | `spec_project_understanding_v1.md`'s capture; a project's LOs from its code | That spec's M2 lands |
| **Phone photos of notes** | `image_transcription` (DL4 / mobile M2b), the transcript review step, `origin = 'phone_photo'` | That route is merged |
| **Proposing back into `tend`** (e.g. "your note answers the question you asked in the Reader") | A proposal into `~/org/proposals.org` in `tend`'s format, never a note edit | The owner asks |
| **Promoting coverage to provenance** | The existing proposal review, writing `source_refs` / `entity_source_links` from learner-confirmed coverage | Coverage corrections stay rare for a month *and* a provenance-reading feature (practice generation, certification scope) is measured to miss sections coverage finds |
| **Alternating-treatments experiment** (curated path vs book order) | §11's design; withholds curation from half the LOs | The owner opts in |
| **Practice from your own notes** (Matuschak's "the mnemonic medium can be extended to one's personal notes", `docs/specs/spec_andymatusnotes.md:448`) | A note-sourced item path with its own provenance and leakage rule (a note may copy an exam question, §9.3), learner review before an item exists, and the learner-text label | The owner asks, *and* C2's links are kept more often than hidden |
| **Notes outside `tend`'s allowlisted folders** (e.g. Markdown docs inside project repositories, which Q5 keeps excluded) | An owner decision per folder | The owner asks |

---

## 14. Owner questions (all DECIDED 2026-10-25)

The owner adopted every recommended answer on 2026-10-25, with one change, to Q5 (`~/org` added to the allowlist).

| # | Question | Decision |
|---|---|---|
| Q1 | Should a deliverable just be a goal (with your words and an optional deadline), rather than a new kind of object? | DECIDED 2026-10-25: **Yes.** Goals already hold your sentence, scope, deadline and exam. Quest, exam and project are shown from what the goal has |
| Q2 | How should a syllabus come in? | DECIDED 2026-10-25: **Typed or pasted text in C0; a `syllabus` source role in C3** that is used to scope but never taught from and never protected. A syllabus must not be given the `exam` role, or it is hidden whole |
| Q3 | Build correspondences only for what a deliverable needs, or for the whole library in the background? | DECIDED 2026-10-25: **Only on demand**, plus an owner-run command for a whole book. Whole-library coverage spends plan headroom on sections nobody reads |
| Q4 | When two books treat a topic equally well, should LearnLoop sometimes pick the other one on purpose, to learn which suits you? | DECIDED 2026-10-25: **Not in v1.** The model's pick, with *use this one instead*. Exploration comes with the learned preference (§13) |
| Q5 | Which of your notes may LearnLoop read? | **DECIDED 2026-10-25 (changed from the recommendation): grove notes, Quicknote (Pocket Notes), the Obsidian vaults and `~/org`** (your planning notes, including `me.md` as far as `tend` indexes it). Project repos stay excluded. The privacy rules are unchanged for `~/org`: only the plan model reads note text, only linked notes are stored, and a note is never a source or evidence (§10.1) |
| Q6 | May the plan's model read your note text to link it? And may a lesson running on an OpenRouter grant read a note? | DECIDED 2026-10-25: **Yes to the plan** for linking. **Yes for a lesson** you started and granted, since you pressed it; background linking never uses OpenRouter |
| Q7 | `tend`'s meaning search sends the query (a topic title, never a passage or a note) to Voyage, as `tend` already does for your notes. OK? | **DECIDED 2026-10-25 (confirmed as recommended): yes**, with words-only search when offline, and a setting to make it words-only always |
| Q8 | Store copies of the notes that get linked, inside the vault? | DECIDED 2026-10-25: **Yes, linked notes only**, refreshed when the note changes. The vault is private and backed up encrypted |
| Q9 | Should LearnLoop read linked notes for gaps in your understanding (like your Reader questions)? | DECIDED 2026-10-25: **Later and opt-in (C5).** Off by default; it only ever steers what to suggest, never grades you |
| Q10 | When you say "I already know this" on a path section, should it ask for a cold check later? | DECIDED 2026-10-25: **Yes**: *I know this — check me later* schedules one check and takes the section off the plan until then. Plain *skip it* stays too |
| Q11 | With several deliverables at once, which does the plan follow? | DECIDED 2026-10-25: **The nearest-due one** (the existing nearest-goal rule). The others still show their paths in the Guide |
| Q12 | "Am I ready?" before RW6b lands: how many checks? | DECIDED 2026-10-25: **One per topic you haven't shown yet, dated by forgetting, never after the deadline.** RW6b takes over the choosing when it lands |
| Q13 | In a book that's part of a deliverable, should the Guide show the deliverable's slice by default? | DECIDED 2026-10-25: **Yes, with *this book alone*** one tap away |
| Q14 | Should the Guide's switch also turn off the plan following the deliverable (as RW7b does)? | DECIDED 2026-10-25: **Yes**, so the plan never follows a path you can't see |
| Q15 | First slice: C0 whole, or C0a (correspondents) first so the skim-and-jump UX can be built sooner? | DECIDED 2026-10-25: **C0a first if the UX spec is ready to build; otherwise C0 whole** |
