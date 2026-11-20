# UX-11: a web page keeps its display equations, its section titles and none of its furniture

Ledger defect UX-11 (with UX-24's proper fix). Branch `fix/ux11-html-extraction-keeps-math`, from main `4566d93ae9`. No schema change, no migration, no algorithm tag, no config field, no prompt change; no identity pin moved.

| Commit | What |
|---|---|
| `9aafff7b6e` | What each source kind extracts to today, captured from the unchanged code (`tests/fixtures/ux11_extraction_before.json`) |
| `a4c03947a3` | A new read of a web page keeps its display equations and its headings' words (extraction `html` version 3) |
| `2af911b2e5` | A page read before is offered a re-read for its missing equations (the card's line, `read_again`) |
| `3f89f41789` | The line and the confirmation in plain words (the deny-list caught "study map"); `read_again` in the desktop's action kinds |
| `6061628dbb` | Desktop and phone renderer tests over the new blocks |
| `103d84246f` | PreTeXt's permalink buttons are page furniture too (they cost the chapter 14 more paragraphs) |
| `30fe374214` | The renderer tests say which blocks they shorten |
| `4da0beb667` | MathML, MediaWiki formulas and MathJax script math reach the text as TeX (a test of that step) |

This record and the ledger cells are the last commit.

## Step 0: where a web page's math, headings and text went

Both tracked samples through the production path (`add_source` → the `import` job → `default_extract`: `_html_to_markdown` = `trafilatura.extract(output_format="markdown", include_tables=True, include_comments=False)` → `markdown_to_ir(extractor_name="html")`, version 2), with fake models. Each stage was read on its own: trafilatura's XML output (its body before any Markdown is written), its text output, its Markdown, and the normalizer's blocks.

### The chapter's 34 display equations

`samples/understanding-linear-algebra-symmetric-matrices-and-variance.html` (PreTeXt): 34 `div.displaymath`, each a bare `\begin{equation*}` or `\begin{align*}` environment in raw TeX (MathJax renders them in the browser).

| # | Where in the page | Version 2 | Version 3 |
|---|---|---|---|
| 1 | Preview Activity 7.1.1, task (b) | dropped | kept |
| 2, 3 | the section's introduction: P and D in general, then for the preview's matrix | dropped | kept |
| 4 | Subsection 7.1.1: `A = QDQ^{-1} = QDQ^T.` | **kept** | kept |
| 5 | Subsection 7.1.1: `A^T = (QDQ^T)^T = … = A.` | dropped | kept |
| 6-9 | Examples 7.1.6 and 7.1.7 (Q, u₁, u₂, `A\xvec = Q(D(Q^T\xvec))`) | dropped | kept |
| 10 | Subsection 7.1.1 (`\vvec\cdot(A\wvec) = …`) | dropped | kept |
| 11, 12 | Proposition 7.1.10 | dropped | kept |
| 13, 14 | Example 7.1.11 (an `align*`) | dropped | kept |
| 15 | Activity 7.1.4: the three data points | dropped | kept |
| 16 | Activity 7.1.4, a task's sentence (a list item): the demeaned points | dropped | kept (in the list item's sentence) |
| 17 | Activity 7.1.4, a task's sentence: `V = \frac 1N\sum_j~|\dtil_j|^2.` | **kept** | kept (in the list item's sentence) |
| 18-22 | Subsection 7.1.2 (an `align*` among them) | dropped | kept |
| 23 | Proposition 7.1.16 (additivity of variance) | dropped | kept |
| 24, 25 | Activity 7.1.5: the data and the matrix A | dropped | kept |
| 26 | Activity 7.1.5, a task's sentence | dropped | kept (in the list item's sentence) |
| 27 | Subsection 7.1.2 (`C^T = …`) | dropped | kept |
| 28 | Proposition 7.1.17 | dropped | kept |
| 29 | Subsection 7.1.2: `V = V_{\uvec_1} + V_{\uvec_2}.` | **kept** | kept |
| 30 | the Summary's list | dropped | kept (in the list item's sentence) |
| 31 | Exercise 5: the five data points | dropped | kept |
| 32 | Exercise 6: the data matrix | dropped | kept |
| 33 | Exercise 7, a part's sentence: Q and D | dropped | kept (in the list item's sentence) |
| 34 | Exercise 9: v₁ and v₂ | dropped | kept |

**Where each was lost: in the readable-body extractor, every one of the 31.** None is mangled anywhere: the 3 that reach trafilatura's body reach its Markdown, the normalizer's blocks and the Reader unchanged, and the 31 others are absent from trafilatura's body already (its XML output). The Markdown step and the normalizer lose no display.

**Why the body extractor lost them.** trafilatura looks for the page's body with a list of XPaths whose second is `(.//article)[1]`. A PreTeXt section is a `<main>` of `<section>`s whose activities, examples, definitions, propositions and exercises are each an `<article>` (31 of them, some nested). trafilatura took the first one, Preview Activity 7.1.1, for the whole page: 822 characters, with display 1 and five headings. That is short, so it compared it with its fallback extractors and kept the fallback's 13,435 characters. The fallback keeps a paragraph by its share of ordinary words: a formula-only paragraph has none, so the displays went, and with them every heading and most list items. The same loss took 116 of the chapter's body paragraphs and list items, among them:

- **the exercises' matrices**: Activity 7.1.2's "For each of the following matrices…" is followed in the page by four list items, each `\(\begin{bmatrix} 3 \amp -4 \\ 4 \amp 3 \end{bmatrix} \text{.}\)` and so on; all four were dropped, so the sentence was followed by the next paragraph. Activity 7.1.3's three, Exercise 4's four (`\(\displaystyle \begin{bmatrix}…\)`) and Exercise 2's likewise. These are inline TeX matrices, not display math: the 34 is a lower bound on what a learner lost;
- "enables us to write \(A = PDP^{-1}\)…" after display 2, and most activity tasks.

### Figures, tables and other math

| What | In the page | Version 2 | Version 3 |
|---|---|---|---|
| Figures | the chapter's 9 `<figure>`: SVG plots, each with a caption ("Figure 7.1.2 The matrix transformation defined by D.") and a long description in a `<details>` | dropped whole (trafilatura drops figures; the text still says "as shown in Figure 7.1.2") | the same (filed: UX-35) |
| Tables | the article's one arrival-schedule table | a Markdown table | the same |
| Matrices written as TeX | inline `\(\begin{bmatrix}…\)` in paragraphs and list items | kept where its paragraph survived (most did not, above) | kept |
| MathML | neither sample has any (`<math>`: 0) | trafilatura drops a `<math>` element's TeX annotation and keeps its token text, or drops it hidden (Wikipedia's MathML copy is `display:none`, its visible formula an image, also dropped) | its TeX (annotation, else `alttext`) as `\( \)` or `\[ \]`; a MediaWiki formula's TeX from its MathML or its image's alt text |
| Sage cells | 8 `<script type="text/x-sage">` | dropped (scripts) | the same |

### Section headings

| | The page's heading text | Version 2: unit label, section path | Version 3 |
|---|---|---|---|
| Chapter | 35 `h1`-`h6`: the site banner "Understanding Linear Algebra", a hidden "Search Results:", "Section 7.1 Symmetric matrices and variance", 6 `h3` ("Subsection 7.1.1 Symmetric matrices and orthogonal diagonalization", …, "Exercises 7.1.4 Exercises") and 26 `h4` ("Activity 7.1.2.", "Theorem 7.1.9. The Spectral Theorem.", "1." …) | no heading reached the Markdown (the fallback writes none): one unit, labelled the import's title or "Document" (the fixture: "Document"), path `root` | 33 heading lines (not the banner, not the hidden search box); one unit, labelled **"Section 7.1 Symmetric matrices and variance"**, locator `root/root/section-7-1-symmetric-matrices-and-variance`. The normalizer's units go two heading levels deep, so the subsections and activities stay headings inside the one section |
| Article | "Elevator paradox" (`h1`), five `h2`: "Modeling the elevator problem", "More than one elevator", "The real-world case", "References", "External links" (and "Contents" in the hidden table of contents) | the Markdown has the six headings; `markdown_to_ir` keeps only `_slug(heading)` as each block's `section_path` and each unit's `label` and drops the heading line: "(intro)", "modeling-the-elevator-problem", … (UX-24 shows these as words) | labels "(intro)", "Modeling the elevator problem", "More than one elevator", "The real-world case", "References", "External links"; `section_path` and locators keep the slugs |

### Furniture kept at a section's start

| Page | What version 2 kept | From |
|---|---|---|
| Article | "[edit]" glued to the first block of 5 of its 6 sections (blocks `s3`, `s10`, `s12`, `s13`, `s15`: "[edit]Several attempts…", "[edit]- ↑ Nahin…") | MediaWiki's `span.mw-editsection` beside each `h2`: trafilatura writes the heading, then the span's text as the start of the next paragraph |
| Article | the introduction's first block, `s1`: "This article has multiple issues. Please help improve it or discuss these issues on the talk page. (Learn how and when to remove these messages)" and a line "\|" | MediaWiki's maintenance box, `table.ambox` |
| Chapter | none (no section had a start: no headings). Its "🔗" permalink buttons (`div.autopermalink`, one after every paragraph and heading) never show, but in version 3's path they cost 14 short paragraphs (below) | |

### The extraction identity, and what moves when the text changes

`default_extraction_identity` for a web page (category `web` or `arxiv`, or HTML content) was `{"extractor": "html", "extractor_version": "2", "model_versions": {}, "config": {}}`. The import hashes it with the revision's id, the page selection (none) and the IR schema version into the run's `extraction_request_hash` (`ingest/hashing.py`). A completed run with that hash for the revision is reused without extracting (`handle_import`). The result hash is over the request hash and the IR.

So if the extraction's output changed for the same bytes **with the same identity**, nothing would change: every import of a revision already read reuses the stored run, and the improvement would never reach a page read before. With a **new version**, the request hash differs, so an import of the same bytes extracts again and stores a new run under a new extraction id. Everything keyed on the reading then belongs to one reading or the other:

| Keyed on | What it is | For the new reading |
|---|---|---|
| extraction id | the run, its blocks, units, render view, health | new rows; the old ones stay |
| span ids (`s1`, `s2`, … by order) and block content hashes (sha256 of the text) | every block | renumbered and rehashed wherever text changed: in the chapter, 59 blocks become 135 |
| unit ids (`u1`, … by order) and semantic hashes (over the unit's text) | sections | the article keeps `u1`-`u6`; their semantic hashes change (each lost its "[edit]"); the chapter keeps `u1`, rehashed |
| inventory rows (extraction, unit, semantic hash; window checkpoints on the rendered prompt) | the model's reading of a unit | none: reused only for the same unit id **and** semantic hash with every cited span exact (`_reusable_inventory_for_extraction`), so a changed unit is inventoried, and paid, again |
| synthesis manifests (`extractor_versions`, inventory row ids) | a build's record | a later build records the new reading |
| unit selection, marks (`exam_paper_metadata`, `MARKS_MADE_ON_KEY`), section progress, annotations, items' source refs (`entity_source_links`, `source_object_citations`), the saved place | the learner's | only by a re-read's carry-over (below) |

## The fix, per loss

| Loss | Where | Fix (version 3, `learnloop/ingest/extractors/web_page.py`) |
|---|---|---|
| 31 displays, 116 paragraphs and list items, every heading of a page made of articles | the body extractor's first-`<article>` rule | When the first `<article>` holds under half the letters of the page's `<main>` (else `<body>`), the articles are parts of the page, not the page: they are read as `<div>`s (`_articles_as_parts`). A blog post whose `<article>` is its body is untouched |
| 14 short paragraphs version 3 still lost (Definition 7.1.5; Theorem 7.1.9's statement "The matrix A is orthogonally diagonalizable if and only if A is symmetric.") | trafilatura drops a short paragraph whose only link is the permalink button inside it | the button is page furniture (`autopermalink`, below). 4 list items remain lost: "Sketch the vectors … on the left/right side of Figure 7.1.1." (repeated sentences) |
| "[edit]", the maintenance box | trafilatura keeps their text | `PAGE_FURNITURE`, removed by class before reading, each element whole with nothing else (its tail text is kept): `mw-editsection` (MediaWiki's [edit] link beside a section heading), `ambox` (MediaWiki's maintenance notices), `autopermalink` (PreTeXt's "copy heading and permalink" button). A class names the element, so the rule cannot reach body text the page did not mark that way |
| MathML, MathJax's `math/tex` scripts | trafilatura drops them or keeps token text | their TeX as `\( \)` (inline) or `\[ \]` (display), in place (`_math_as_tex`, `_mediawiki_formulas_as_tex`) |
| a heading written at the end of the line before it ("…*orthogonally diagonalizable*.#### Definition 7.1.4.") | trafilatura's Markdown writer, after emphasis closing a paragraph | `_tidy`: split onto its own line only when the words after the marks are a heading of the page |
| a list item written "-" alone on a line, its text on the next | the Markdown writer, for an item whose text starts in a child element | `_tidy` joins them, unless the next line starts a heading, item, table or display |
| a display environment on the line after a paragraph's last words | the Markdown writer | `_displays_apart`: a blank line before and after a display environment that starts a line, so it is a block of its own as in the page (one inside a list item's sentence stays there) |
| a section labelled by its slug | `markdown_to_ir` | `section_titles=True` (version 3 only): a unit's label is its heading's own words; the slug stays every block's `section_path` and the unit's locator |

**Display math is kept as the page writes it, not wrapped in `$$`.** A PreTeXt display stays a bare `\begin{equation*}…\end{equation*}` (or `align*`), which the renderers already draw (UX-25's `bareEnvironmentsAsDisplayMath`: equation, align, gather, alignat, starred or not; in a block of its own or in a sentence). Wrapping would change what the book-math check reads (it finds no equation in a bare environment, so such a block never gets a "checked" label) and would turn an environment KaTeX cannot draw (`multline`) into a red error instead of readable TeX. A page's own `\[ \]` and `$$` pass through; MathML becomes `\[ \]`, which the renderers turn into display math on lines of their own.

**trafilatura is not replaced.** Every web page is still read by the same `trafilatura.extract` call with the same options; version 3 changes the parsed page it is given (the tree trafilatura's own `load_html` parses) and tidies its Markdown. On a page with no article structure, no furniture class, no MathML and no glued heading or bare "-", version 3's text equals version 2's (the article: the same text, less the furniture).

What version 3 still does as version 2 did, and is filed: a paragraph whose `<div>` holds inline emphasis is split at the emphasis ("we say that \(A\) is" / "*orthogonally diagonalizable*."; "A" / "*symmetric*matrix…"), and two sibling paragraph `<div>`s are sometimes glued ("…its transpose.To begin…"): UX-34. Figures and their captions: UX-35.

## Version 3, and how old and new readings are told apart

`WEB_PAGE_EXTRACTOR_VERSION = "3"` (`web_page.py`) is what `default_extraction_identity` returns for a web page and what `markdown_to_ir` stamps on its IR; `OLD_WEB_PAGE_EXTRACTOR_VERSION = "2"`. A stored reading says which it is in `source_extraction_runs.extractor_version` (with `extractor = "html"`). Nothing else distinguishes them and nothing new is stored. The card's offer and the `read_again` action read that column.

**A page read before is not changed silently and not read again on its own.** Its stored run, blocks, hashes, span ids, units and everything keyed on them stay as they are (`test_ux11_a_page_read_before_keeps_its_stored_reading_under_the_new_code`, on a library built with the old extraction from the fixture and then opened by the new code: the Library, the Reader, an Add of the same page, the card). No job reads a page again by itself: Add of a page already in the library returns `existing` and imports nothing, and nothing queues an `import` for a book except the learner's Add, the card's actions, the Ingest screen and `learnloop import` (`enqueue_add_source`, `start`, the import batch, `cli/app.py`). One consequence, by design of the identity: **an import of an already-read page from the Ingest screen or `learnloop import` now reads it again** (version 3 is a new request hash), with the carry-over below. Before, such an import of unchanged bytes reused the stored reading. It is something the learner does, not automatic, and it was already a re-read whenever the page's bytes had changed.

## Reading a page again: what it costs and what it keeps

The re-read is the existing one: an `import` naming the book (`enqueue_add_source(source, source_id=…, auto_build=False)`), which reads the revision's own saved copy (`reread.original_bytes`, verified by its hash; refused if it changed or went missing), registers nothing new (same bytes, same revision), extracts with version 3, makes the new reading current, and carries over (`reread.carry_over`).

**Cost.** The reading itself runs on this computer and sends nothing to a model (the test counts inventory and synthesis calls across the re-read: none). It builds nothing (`auto_build=False`): no inventory, no synthesis, no questions. Afterwards, as after any import:

- **model work for its sections is paid again when it is next needed.** An inventory is reused only for the same unit id and semantic hash. Every unit of both samples changed text (the chapter's one unit gained its equations; each article section lost its "[edit]"), so the next build or question-writing for a section inventories it again at its full price (test: the new reading's unit takes a fresh inventory call; a second one is a cache hit). Sections already built count as built (coverage is by unit id), so no build starts by itself; a later "Build questions for the whole page" or as-you-read questions for a changed section pay their inventory and synthesis as the first time did. **That a re-read re-pays model work for every changed part is why it is offered and never automatic.**
- what an import always queues: the meaning-search index of the new text if embeddings are on (`embedding.enabled`, off by default), local or fallback contextual indexes if switched on (off by default), and the curriculum coverage pass (`curriculum.coverage_on_extract`, on by default) which judges again, on the ChatGPT plan only and quietly, each topic already covered, if any.

**What it keeps** (the existing carry-over, unchanged): section progress (mapped section to section: the same id and label, or the semantic hash, or a unique label, or where most of the old section's passages landed through the span aliases); the study map's chosen chapters; highlights and notes, re-anchored by their words (`reanchor_annotation` → `_locate_quote`; a quote that cannot be found is marked to be placed again); the citations of questions, facets and notes, through the span aliases. **Protection marks never move to another reading** (the protection redesign): the old reading keeps its marks; the new reading of a protected page is withheld whole until the owner marks it, and the marking proposes the same sections (the article's held-out "the-real-world-case" is proposed as "The real-world case"). The old reading stays stored.

## The Library's offer

On the book card of a web page whose current reading is version 2 **and** whose saved original has display equations that reading left out (counted by reading the original with version 3, on this computer, no model; cached per reading and original, which never change), in the place of the card's quiet health line:

> This page's text is missing 31 equations · **Read it again**
>
> details: This page was read before LearnLoop kept a web page's equations and section titles. Reading it again from the copy saved when you added it keeps them; your progress and notes move to the new reading.

A page with nothing to gain (the article) or read with version 3 gets no line. The action is `read_again` (`source_action`). With study state (or exam marks) it first asks:

> **Read “…” again with its equations?**
> Read on this computer from the copy saved when you added it: free.
> The new text keeps the 31 equations the old one left out, and each section's own title.
> Your progress (1 section), 1 note, the passages your questions and notes cite and your study-map chapters move to the new reading. Anything that can't be matched is marked so you can place it again.
> Reading it sends nothing to an AI. Questions already written stay. Afterwards, as for any page you add, the new text may be indexed or checked against your topics, and a section whose text changed is read by the AI again before new questions are written from it.
> (on a page with exam marks) Your exam material isn't moved: …
> [Read it again] [Not now]

The action refuses a book whose reading is not a version-2 web page ("This book's reading already keeps what reading it again would.") and one whose saved copy changed. The line holds while the planner is at rest or skipped (the card shows one line: a build waiting for the OK or a review shows instead).

## Protection: hidden and collapsed content

What version 2 does, measured on two page shapes (one `<article>` that is the body, as a blog; many `<article>`s in a `<main>`, as a book) with marked text in each kind of hidden part (`tests/fixtures/ux11_extraction_before.json`, `probe`):

| Hidden part | Version 2 | Version 3 |
|---|---|---|
| a closed `<details>`'s body (a solution behind "Solution") | **reaches the text** in both shapes | the same |
| an open `<details>` | reaches the text | the same |
| `hidden` attribute | reaches the text | the same |
| `style="display:none"`, `aria-hidden="true"`, a `hidden` class | left out | left out |
| the chapter's macro definitions (`display:none`), its figures' long descriptions (`<details>` inside `<figure>`), its search box | left out | left out |

Version 3 reads more of some pages than version 2 did, so it could have let a hidden part in that version 2's fallback had dropped. It cannot: before reading, each hidden or collapsed part of the page (a closed `<details>`, judged by its body since its summary shows; `hidden`; `aria-hidden`; `display:none` or `visibility:hidden`; `<template>`) whose letters and digits are not in version 2's reading of the same page is removed, and one shorter than 12 letters is always removed (`_hidden_parts_as_before`). So version 3's text holds a hidden part only where version 2's did. The source-macro work still reads the hidden definitions at render time only (UX-2), from the stored original.

That version 2 (and so version 3) puts a closed `<details>` body into the text is the existing behaviour, kept as the brief asks; it is not protection a page's author can rely on.

## Tests, each written first and seen failing

Python, `tests/test_ux11_html_extraction.py` (10 tests), against the fixture taken from the unchanged code (`9aafff7b6e`; its chapter blocks hash to the digest `test_ux2_source_macros.py` pinned before UX-2, `f03ceb9f…69202`). First run, before any source change: 7 failed, 2 passed (the two invariants that must hold before and after):

| Test | Before the fix | After |
|---|---|---|
| `the_chapter_keeps_all_34_display_equations_in_page_order` (the count, in order; display 2's matrices, display 4, exercise 6's matrix each a block of its own; the exercise's four matrices after its sentence; the renderer is given the stored text) | "3 of 34 display equations kept in page order: [4, 17, 29]"; then, with the permalink rule switched off, "assert 'Asymmetricmatrix\\(A\\)…' in …" (Definition 7.1.5 missing) | passed |
| `section_titles_are_the_headings_own_words_and_the_slug_stays_the_id` | "At index 1 diff: 'modeling-the-elevator-problem' != 'Modeling the elevator problem'" | passed |
| `the_articles_sections_carry_no_edit_link_or_maintenance_notice_and_keep_their_text` (and every old block's text, less "[edit]", is still there) | `assert not any("[edit]" …)` | passed |
| `hidden_and_collapsed_parts_are_treated_as_the_old_extraction_treated_them` (both shapes, each kind; the chapter's hidden parts) | `('html', '2') == ('html', '3')` (the version) | passed |
| `other_source_kinds_extract_byte_for_byte_as_before` (both PDF samples, a Markdown and a text file: run identity, blocks, units against the fixture) | passed (the control) | passed |
| `a_page_read_before_keeps_its_stored_reading_under_the_new_code` | passed (the control) | passed |
| `the_card_offers_a_page_read_before_its_missing_equations_and_only_that_page` | "Questions for Document come up as you read" | passed |
| `reading_it_again_gives_the_new_text_and_carries_progress_the_study_map_and_a_highlight` (the confirmation's lines; no model call during the re-read; all 34 displays; the old reading untouched; progress, chapters and the highlight beside display 4 carried, its quote found again; the next inventory paid again) | `ValidationError … action … input_value='read_again'` | passed |
| `reading_the_article_again_maps_its_sections_and_its_held_out_mark_waits_for_the_owner` | as above | passed |
| `mathml_and_script_math_reach_the_text_as_tex` (written after the step; a page with a block MathML formula, an `alttext` one, a MediaWiki formula and a `math/tex; mode=display` script) | with `_mediawiki_formulas_as_tex` and `_math_as_tex` switched off: "assert '\\[\\bar x = \\frac1n\\sum_i x_i\\]' in 'The sample mean … is for the measurements taken in order…'" | passed |

`tests/test_ux2_source_macros.py::test_ux2_a_new_read_of_the_sample_carries_the_pages_macros_and_stores_none_of_them` (new): written after the fix; it is the version-3 counterpart of the existing pins.

Frontends (renderer unchanged): `apps/learnloop-tauri/src/render/webPageMath.test.tsx` (6 tests) and `apps/learnloop-mobile/src/read/webPageMath.test.tsx` (1, the phone Reader through the fake host) draw version 3's blocks: a display of matrices, the exercise's four matrices as list items, displays inside a task's sentence, the data matrix, `\[ \]` from MathML, each with the page's macros and no error node. They passed at once against the unchanged renderer (two arithmetic slips in the first draft's expected counts were corrected), which is the point of keeping the page's own form: their evidence of the before-state is the Python tests (version 2 has no such blocks). `copy/denyList.test.tsx` gains the card line and the confirmation's sentences; it failed first on "study map" in the details ("expected [ 'study map' ] to deeply equal []"), now reworded.

## Assertions changed, and why

- `tests/test_ux2_source_macros.py`: no assertion changed. Its fixture `added_sample` now builds the library the way a library that read the sample before UX-11 holds it (the Add path with the old extraction from the fixture, `tests/web_page_reading_helpers.py`), because its pins (`EXTRACTOR = ("html", "2")`, 59 blocks, the blocks' digest, block `s5`, the render view's hash) describe that stored reading; a new read is now version 3. Before the change of fixture, two of its tests failed on the new code (`('html', '3') == ('html', '2')`; the render view hash). It also imports the handlers itself: run alone it failed with `KeyError: 'add_source'` on main (UX-36).
- In my own new test, the definition is checked in its words without emphasis marks, because the emphasis split (UX-34) is still there.

## Pins and goldens

None moved: `tests/test_identity_pins.py` 342 passed after every source commit; `test_effective_defaults_golden.py`, `test_cli_help_snapshot.py`, `test_kill_switches.py`, `test_sqlite_file_copies.py`, `test_structure_ratchets.py` pass unchanged (below). No config field. No snapshot moved. The sidecar's `source_action` gains one literal (`read_again`); no CLI contract changes. No new non-test TypeScript file (`desktop_validate.py`'s counts unchanged).

## What was run

Every Python run through the scratch wrapper (`env -i`, isolated HOME, CODEX_HOME and config dir) in a 3G scope at `-n 1`; node in a 5G scope with `--maxWorkers=4`; one command at a time.

| Command | Result |
|---|---|
| the capture script over the unchanged code (`9aafff7b6e`'s fixture) | written; its chapter digest equals UX-2's pinned `f03ceb9f…` |
| `pytest tests/test_ux11_html_extraction.py`, before any source change | 7 failed, 2 passed |
| `pytest tests/test_ux11_html_extraction.py tests/test_ux2_source_macros.py tests/web_page_reading_helpers.py` (final) | 29 passed |
| `pytest tests/test_ux2_source_macros.py` alone, on main's version of the file | 16 passed, 2 errors (`KeyError: 'add_source'`) |
| `pytest tests/test_identity_pins.py` after each source commit | 342 passed, each time |
| `scripts/affected_tests.py --files` the six changed source files | 782 files: over 150, so the 190 whose names contain extract, ingest, html, web, source, reread, reader, annotation, librar, normaliz, card, add_source, import, first_run, ux_phase1, ux2, ux11, exam, glm, marker, pdf, transcript, youtube or caption, in five chunks of at most 40, `-m "not arc_close"` |
| chunk 1 (first run, before `103d84246f`) | 812 passed |
| chunks 1-5 (after `103d84246f`) | 812 passed; 630 passed; 772 passed; 620 passed, 5 warnings; 427 passed. Chunk 1 run again after `4da0beb667` (web_page.py was switched for a few seconds during its first run, for the math test's fail-first): 812 passed |
| `pytest tests/test_structure_ratchets.py tests/test_effective_defaults_golden.py tests/test_cli_help_snapshot.py tests/test_kill_switches.py tests/test_sqlite_file_copies.py` | 383 passed (342 of them the identity pins) |
| `pytest tests/test_test_layout.py` (alone) | 3 passed |
| `pytest tests/test_architecture.py` (alone) | 18 passed |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 43 kept, 0 broken. |
| `scripts/check_gate_partition.py` | collected 31868: landing 31803 + arc_close 65 |
| desktop `npm ci`; phone `npm ci` | exit 0, exit 0 (esbuild's install script blocked by allowScripts, as before) |
| desktop `npx vitest run src/render/webPageMath.test.tsx` | 6 passed (first draft: 2 failed on the test's own counts) |
| desktop `npx vitest run src/copy/denyList.test.tsx` | 1 failed ("study map"), 192 passed; after the rewording 193 passed |
| desktop `npm run typecheck` | exit 0 |
| desktop `npx vitest run --maxWorkers=4` (whole suite) | Test Files 315 passed (315), Tests 3214 passed (3214) |
| desktop `npm run frontend:build` | exit 0, "✓ built in 2.73s" |
| phone `npm run typecheck` | exit 0 |
| phone `npx vitest run --maxWorkers=4` (whole suite) | Test Files 42 passed (42), Tests 417 passed (417) |
| phone `npm run build` | exit 0, "✓ built in 813ms" |

## What a walk must check

- **firstq (a new learner adds the chapter as a web page).** In the Reader: Activity 7.1.2's "For each of the following matrices, determine whether…" is followed by its four matrices, drawn; Exercise 4's four matrices and Exercise 6's data matrix likewise; the preview's P and D, "A = QDQ^{-1} = QDQ^T", the variance equations and Proposition 7.1.16 are drawn as display math with bold vectors and ℝ, no red commands, no raw `\begin`; displays inside an activity's tasks (Activity 7.1.4: "find the demeaned data points" then the equation, then "and plot them") are drawn on their own lines with the task's words kept around them (a list item there may close and reopen around the display: look at how it reads). The phone's Reader on the same section, through a desktop with this branch.
- **firstq, the first build.** The chapter's text is about twice version 2's (27,873 characters of Markdown against 13,441; one section of 135 passages against 59). Check that its first build (as-you-read) completes: the inventory window and the synthesis pass are bigger than in the UX-13 walks (largest window then 3,169 output tokens against the 6,000 ceiling). If a step is refused, record its sizes.
- **retainer (the elevator article added now).** Contents, the reading path, "Next: read …", side by side and the phone's section list name the sections "Modeling the elevator problem", "More than one elevator", "The real-world case", "References", "External links", and "Introduction" for the first; no section starts with "[edit]"; the introduction starts with "The elevator paradox is…", not "This article has multiple issues".
- **A page read before this branch (a walk vault from before).** Its card says "This page's text is missing N equations · Read it again" (the chapter: 31); its Reader shows exactly what it showed before until the learner presses it; pressing it with progress or notes asks first with the lines above; after it, the Reader shows the new text, Contents the new titles, the progress and highlights where they were, and the card's line is gone. On a page with exam marks: the new reading is held back until the owner marks it, and the marking proposes the same sections.
- **Ask, quick checks and questions written from the new text** read the displays (the model now sees them): a question about the exercise's matrices names them.

## Judgment calls to read first

1. **The fix changes what trafilatura is given, not trafilatura.** The STOP condition was "replacing the readable-body extractor wholesale". Version 3 keeps the same call and options; it marks a page's articles as parts of the page when the first holds under half of it. What changes for every other page read now: a page whose first `<article>` is small next to its `<main>` (a book section, a listing page whose first card is an article) is read from `<main>`/`<body>` by trafilatura's later rules instead of from its first article, so more of it is read (on a listing page, possibly its other cards); a page whose first article is its body (a blog post, a news story) reads as before; a page with no article reads as before. Plus the named furniture, MathML and tidy steps above.
2. **PreTeXt's permalink buttons are furniture**, added after the display fix showed they cost 14 paragraphs (a definition and a theorem's statement among them). Removed by class, as the brief's furniture rule asks; it is not at a section's start, and it is not in version 2's text either.
3. **Display math stays as the page writes it** (bare environments), not `$$` (reasons above). A display inside a list item's sentence stays in its sentence.
4. **The chapter stays one section.** The normalizer's units go two heading levels deep, and this page has one level-2 heading; its subsections are headings inside the section. Splitting it by subsection would change unit structure (and inventory granularity) for every version-3 page: not done; worth a decision.
5. **Hidden parts: never more than version 2.** The guard is exact by text, so a hidden part version 2 kept stays (a closed `<details>` solution included: the existing behaviour, which the brief says to keep), and one it left out stays out; a part under 12 letters is always out, which may drop a short hidden note version 2 kept.
6. **An Ingest-screen or CLI import of a page already read now reads it again** (with the carry-over), where it reused the reading before. The alternative, keeping version 2 sticky for any import but the card's, would make the extraction depend on how it was asked for; not taken.
7. **Marks.** "Carries marks over" is, by the existing rule, not moving them: they stay on the reading they were made on and the new reading waits for the owner, with the same sections proposed. If the owner wants marks moved by a web re-read, that is a change to the protection redesign's rule.
8. **Size.** 458 lines added and 42 removed under `src/` (374 non-blank, docstrings and 22 comment lines included; `web_page.py` is 255 of them), about the brief's 400-line bound; not clearly over it, so not a stop.

## Not verified

- No app, browser, server or walk was run; the screens through vitest (jsdom and node rendering), the sidecar through its handlers. How a display inside a list item reads in the real window (the list may close and reopen around it) was not seen.
- No live model: whether the bigger first build of a version-3 chapter completes on the live route (above), and how the models write from text that now has its equations.
- Web pages other than the two samples: other PreTeXt books, other MediaWiki pages, MathJax-rendered pages saved after rendering (`mjx-container`, whose MathML carries no TeX annotation: left as trafilatura reads it), arXiv's HTML (LaTeXML `alttext`: handled by the MathML step, not tried on a real page). MathML, MediaWiki formulas and script math were checked on one hand-written page (`test_ux11_mathml_and_script_math_reach_the_text_as_tex`), not on a real page.
- A real owner vault: the offer's cost and count on a library of many web pages (each count reads its original once per process: two trafilatura runs, about 0.1 s for the chapter).
