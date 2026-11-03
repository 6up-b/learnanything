# Reader RW5c P1: "matches the book's equation (checked)", option B

- **Stage:** `reader-rw5c-p1`, branch `reader/rw5c-p1`, worktree `learnanything-merge2`, base `aae65635b6` (mvp-0.43, migration 237).
- **Spec:** `docs/specs/spec_reader_rw5c_checked_labels_v1.md`, §13 row P1 with every section it cites, §18's resolved contracts F1-F9.
- **Owner decision 2026-11-02 (Q1):** option B: every label and every number in a label slot on a checked figure is code-owned.
- **Migration:** `238_figure_source_checks.sql`. **Head fixture:** `fixtures/migration_head_238`. **Successor:** none (§10.3; playbook step 1: no scoring, scheduling, projection or admissibility meaning changes).
- **Model routes, caps, prices, new constants:** none (§6.7, §15). The check makes no model call. Its only spend is the second author attempt after a proved `differs`, inside the existing two-attempt cap, `figures.max_daily_cost_usd` and the existing `FiguresGate`.

## Plan as built

| Part | Where |
|---|---|
| The closed book-math reader (§5.3) | `src/learnloop/figures/book_math.py` (new, pure) |
| The Python twins of `formatValue` and `String(v)` (§6.4, §7.2, G22) | `src/learnloop/figures/display_format.py` (new; standard library only, sent into the sandbox) |
| The one fixed harness (§6.2-§6.5) | `src/learnloop/figures/source_check_harness.py` (new; a program sent to `pf_sandbox`, never imported) |
| Candidates, binding, outcomes, recording, recheck, the n=1 instruments (§5, §6, §10, §12) | `src/learnloop/figures/source_check.py` (new) |
| The generic walk, the roles, code's TeX and plain renderings, the label rewrite (§7, §8.2) | `src/learnloop/figures/elements.py` (new) |
| The evaluator's bounds for a derived label (§7.2, F2) | `figures/spec.py` `derived_bounds`, twin `figureSpec.ts` `derivedBounds` |
| The ledger (§10.2) | `migrations/238_figure_source_checks.sql`, `db/stores/figures.py` |
| The switch (§10.1) | `config/schema.py`, `figure_admission.checked_labels_enabled`, `params/parameter_registry.py`, every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry |
| Inside the build, the view, `build_key`, `request_hash`, *rebuild* (§6.6, §6.7, §7.4) | `figures/service.py` |
| RPCs | `reader.figure_recheck` (new), `reader.figure_revise` gains `rebuild` |
| CLI and report (§10.4, §12) | `learnloop reader figure-checks`, `figures.source_checks` in `learnloop reader report` |
| The renderer (§7.2-§7.4) | `screens/reader/figures/figureLabels.tsx` (new), `FigureInline.tsx`, `FigurePanels.tsx`, `AdvancedPanels.tsx`, `useFigures.ts`, `api/dto.ts`, `api/client.ts`, `ReaderScreen.tsx`, Tauri passthrough |

## §2 and the design's citations, re-checked at `aae65635b6`

The design's code truth was `dbc1559e7`. Every §2 row was re-read at the base. **No row is contradicted**: what moved is line numbers and the surrounding code that later stages added. Nothing below needed the conservative fallback of §18.

**Unchanged lines:** `figures/verify.py` (`:48`, `:96`, `:365`, `:391`), `figures/spec.py` (`:114`, `:119`, `:313`, `:652-654`, `:803`, `:825`, `:848`), `FigureInline.tsx` (`:28`, `:49`), `FigurePanels.tsx` (`:22`, `:91`), `workbench/symbolic.py` (`:1013`, `:1033`, `:1039`), `pf_sandbox.py` (`:80`, `:120`), `block_health.py` (`:66`), `math_text.py` (`:34-36`, `GREEK` at `:36`), `224_figure_requests.sql:149-150`, `template.py:842`.

| Design citation | At the base | What else changed there |
|---|---|---|
| `figures/grammar.py:105-117` `Node` | `:111` | `Meter` was added (RW5d P2, `:657`); `evaluate` takes `meter` |
| `grammar.py:120` names | `_NAME` `:102`, `is_name` `:126` | |
| `grammar.py:48-55` caps | `:54-61` | |
| `grammar.py:74-84` reserved | `:75-90` | |
| `grammar.py:618-639` `exact_sum` | `:624-645` | |
| `grammar.py:479-495` `_pow` | `:485-501` | |
| `grammar.py:710-717` `piecewise` | `:768-775` | |
| `db/stores/figures.py:32-43` | `VERIFIED_RW5C` `:43`, `shown_verification` `:46` | |
| `service.py:233-244` `build_key` | `:383-397` | now also holds `sketch_switch`, `rich_tiers_switch`, `manim_tier_ready`, `author_learner_state_enabled` |
| `service.py:649-658` `shown_row` | `:1014-1023` | |
| `service.py:664-704` `PROPERTY_CHECKS` | `:1029` | |
| `service.py:731` `figure_view` | `:1301` | goes through `_presented_row` (sketch recheck, `worded_row`) |
| `service.py:821-846` `request_hash` | `:1574-1639` | the show-me, sketch, rich, `different_kind` and learner-state fields sit beside it, all added only when set |
| `service.py:850` `_reusable` | `:1642` | |
| `service.py:925` held-out predicate | `:530` `withheld_message`; `source_context` uses `material.covers` | |
| `service.py:967-995` `_author_context` | `:1870-1920` | |
| `service.py:1186-1226` the loop | `:2333-2464` | V3's rich branch sits inside it |
| `service.py:1267-1278` store | `:2516-2533` | |
| `service.py:1319` `revision_request` | `:2909` | |
| `handlers/reader.py:666-681` | `:707-722` | |
| `pyproject.toml:672` | `:794` | |
| `protected_tables.py:105`, `:320-331`, `:509-511`, `:543` | `:116`, `:350-360`, `:560-575`, `:615` | |
| `column_classes.py:294-300` | `:315-326` | |
| `config/schema.py:2583-2591` | `FiguresConfig` `:2736` | |
| 28 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries | 34 | |
| Migration 227, `migration_head_227` | 238, `migration_head_238` | Q6's number, per the stage brief |

**Claims that no longer held, each resolved without weakening anything:**

- *§6.2 "Limits: 20 CPU seconds"*: `SandboxLimits(cpu_seconds=20, wall_seconds=30)` holds at `symbolic.py:1033`. `pf_sandbox.SandboxLimits` also caps memory (2048 MB, its default). RW5c passes the same object, so no number is new. A run past the CPU limit loses its output, so the harness stops *starting* work when one more unit no longer fits (`cpu_seconds - per_check_seconds`) and reports what finished: "a timeout means `undecided` for the pairs that did not finish" now holds per pair, with no new constant.
- *§5.2 uses `exam_material(...).withheld`*: `service.source_context` and `passages_context` use `material.covers(extraction, span)`, the same predicate object. RW5c uses `covers`.
- *§11.4 "The desktop Reader is the only host in P1"*: since RW5d P3 and P4b, figures also show on attempt hosts and in lessons, all through `figure_view`. See the decisions below.

## What the later stages needed: decisions recorded

**(1) Prebuilt figures (RW5d P5).** The check runs where every build stores: inside `_author_and_store`, so a prebuilt figure is checked when it is built and arrives checked (§11.1). Its second attempt after `differs` passes the prefetch hold like any request.

- *`build_key` does not orphan prebuilds.* `figures.checked_labels_enabled` joins `build_key` only. `git grep` shows no persisted `build_key`: it is compared in memory by `FiguresGate` within one build. `request_hash` is untouched, so existing prebuilds keep their reuse keys and a press of the same input reuses the row with no request. `tests/test_rw5c_source_check.py::test_build_key_holds_the_switch_and_the_reuse_key_does_not` and the switch-off golden pin this.
- *Prebuilds stored before this landing* have no check row. They are rechecked by code on first open, at no cost.
- *An unpressed prebuilt figure whose check says `differs`* is not listed: `_prebuilt_listed` keeps "speculation is invisible until useful" (RW5d Codex review F10), since its only state would be a failed line.

**(2) Teacher visuals (RW5d P4b).** **In scope.** A lesson's grammar figure builds through the same `_author_and_store` (grounding `retrieved`, its fixed keys), so it goes through the same check, inside the same two attempts; a lesson turn already waits on its figure, and the check adds at most the sandbox's wall clock. `teacher.visuals.lesson_view` is `figure_view` plus suppressions, so it carries the elements and the rewritten spec. A rejected figure's view is `failed`, so `lesson_view` returns None and the lesson says what it says of any failed figure. A lesson figure has no *not right?* and no recheck control (`useLessonFigureCtl` has neither `recheck` nor `rebuild`): one built before this landing stays an illustration until its row exists. `teacher.visuals.summary` still reads the stored labels for the teacher's own prompt; that is a prompt input, not a label slot.

**(3) Followed figures, correspondence and side-by-side Compare (RW5d P4a, CA).** All three draw `FigureInline` from `reader.figures` views, so they show the code-owned labels with no code of their own. `follow` reads the figure's own book's listing, and Compare's `side.figures` is a `useFigures` of its side. The "also in your books" offer names the home only ("◇▸ interactive version from Lay §5.1") and shows no label, so nothing changes there. `section_figures` leaves out a rejected figure. *Residual:* a followed figure's copy is not refreshed by a recheck started from it until it is followed again; it shows as an illustration meanwhile, which errs on the honest side.

**(4) The prefetch report and other readers of figure rows** read `interactive_figures` and `figure_requests` by SQL (`prefetch_ledger.py:207`, `prefetch.py:909`, `:1186`, `:1365`, `help.py:404`, `reader_report.py`, `router_reader.py`, `diagnosis/split/figure_trace.py`, `diagnosis/text_gaps/*`). None reads the new ledger, and `interactive_figures` is unchanged, so each is unaffected. Two places filter a rejected figure through `FS.source_rejected`: the hint chooser's `explore_figure` scan (`help.py`) and `shown_figure` (predictions, `figure.open`). With the switch off neither reads the ledger.

**Sketch, `js_animation` and `manim`** keep *not checked against the book* (§9, N-a): `SC.grammar_row` is false for them, no check runs, and their views have no `elements` or `source_check` key.

## Open questions used (Q1 is the owner's; every other is a default, not owner-confirmed)

| Q | Answer used | Status |
|---|---|---|
| Q1 | **Option B** | **owner decided 2026-11-02** |
| Q2 | `figures.checked_labels_enabled` default on | default, not owner-confirmed |
| Q3 | (ii): code reads every readable equation in the input spans; the quote is a pointer and a stated claim | default, not owner-confirmed |
| Q4 | Not shown; a stored figure gets the same state with *rebuild* while `figures.revisions_enabled` is on | default, not owner-confirmed |
| Q5 | Health `ok` only | default, not owner-confirmed |
| Q6 | Migration `figure_source_checks`, numbered **238** per the brief | default, not owner-confirmed |
| Q7 | Recheck on first open and through the CLI | default, not owner-confirmed |
| Q8 | Keep display agreement | default, not owner-confirmed |
| Q9 | Free model text keeps its numbers and symbols, in the model's voice outside the panels | default, not owner-confirmed |
| Q10 | Exact binary64 literals | default, not owner-confirmed |
| Q11 | Name-against-name passes the prerequisite; P1 decides it `undecided` (`parametric_breakpoint`) | default, not owner-confirmed |
| Q12 | `\log` unreadable in P1 | default, not owner-confirmed |
| Q13 | An `illustrative` figure's element can be `book` | default, not owner-confirmed |
| Q14 | RW5d tier claims: later, P3, designed first | default, not owner-confirmed |
| Q15 | Not a hint-chooser feature now | default, not owner-confirmed |
| Q16 | No bubblewrap: never "checked" | default, not owner-confirmed |
| Q17 | P1b's prompt addition is the owner's, from the report | default, not owner-confirmed |
| Q18 | The short line, with the ⓘ | default, not owner-confirmed |

## Deviations from the letter of the spec

Each is additive or stricter; none lets anything more carry the claim.

1. **A fourth role, `symbol`.** §8.2 draws a slider of a checked definition's symbol as the book's token (`§ λ`). It is no `book` element (G23a: only a `book` element carries the claim words), so it has its own closed role rather than overloading `book`.
2. **`plain` on every element, and `reasons_json` and `duration_ms` on the row.** `aria-label`s and SVG `<text>` cannot hold KaTeX, so each element also carries a code-written plain string (the left-hand side's markup dropped for `book`). The two columns serve the report (§12 asks for reason counts and latency).
3. **Three more refusals in the reader**, each a guess the table does not settle: `a / b c` and `a / b / c` (`ambiguous_slash`), `x^10` (LaTeX superscripts only the 1; `syntax`) and `\frac{d}{dx}` (`derivative`: as a product the `d` would cancel). A row with no condition column is `cases_cover`.
4. **The parser is recursive, not iterative**: one frame per nesting level, capped by `grammar.MAX_DEPTH`, the same bound the grammar's own parser uses. §5.3 says "an iterative parser"; the property it wants (never a recursion error) holds, and the seeded fuzz covers it.
5. **`\dfrac` and `\tfrac` stay unreadable** (`unsupported_command`): the table is closed, additions are P2 rows from the report.
6. **Structural equality spares sympy the proof, not the domain rule.** §6.3 step 4 says identical trees have identical domains; §14 requires `x^{1/3}` against itself to be `undecided` (`domain`). `decide` runs the definedness conditions first, so a power whose domain cannot be stated exactly stays `undecided` even when the trees match. The stricter reading wins.
7. **A control's bare `s + 1` on a piecewise definition** makes its comparisons computed, so the harness answers `undecided` for it, which refuses it (§6.5: "different or undecided, never equal"). `d + 1` and `2·d` still decide such pairs.
8. **Recheck is triggered by the Reader's open** (`reader.figure_recheck` from `FigureInline`'s toggle), not by listing, as §10.4 says. Lessons and attempt hosts have no recheck control.

## The adversarial question, walked through the code

"Find a displayed element or number that these rules let carry the claim."

- **Label slots.** With a `book` element, `rewrite_spec` replaces every `Label` the walk finds, so a model string cannot reach a slot; an id with no element draws `◇` alone. Prediction choices and stored answers go out as element ids, in code's words.
- **The annotation line.** Its text is free model text. It stays behind `◇`, and its target is drawn with no glyph and no claim words (`bare`), so a model note never reads as the source's voice.
- **Derived numbers.** A shade, highlight or bound readout is `derived` only when its parent is a `book` element (or, for a readout, its body is the bare reference of a definition with one, and its variable is the book's). Otherwise the same template runs in the model's voice. Bounds are the evaluator's, written losslessly.
- **The figure-level line.** `CheckedBadge` lists `book` elements only; `labelElements` requires both `status === "checked"` and a `book` element.
- **Kept views.** `redelivered_view` rebuilds the labels and claim from the ledger as the switch is now, so a job result finished before a switch-off shows none.

**Known and left:** `view.label` (the server's string) stays RW5a's illustration text on a checked figure. The Reader draws its own badge, and the Ask rail's line uses `frameBadge`, so a checked figure can read "not checked against the book" there: it errs on the honest side, and is an open question below.

## Coverage on the owner's material (§12 item 1)

Code only, under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, on fresh `learnloop.db.copies.copy_tree_with_databases` backups of `learnanything-ad1/fixtures-local/owner-copies-mvp035` under the gitignored `fixtures-local/rw5c-coverage/` (schema upgraded on the copies under `UPGRADE_SCRATCH_COPY`). No model client, no write beyond the copies, no socket, $0.

**`learnloop reader figure-checks --recheck --dry-run --json`:** `figures: 0` on all three copies (`interactive_figures` is empty in `owner-copies-mvp035`: figures postdate it). So the instrument the spec names has nothing to report on these copies, and the question "is RW5c vacuous on the owner's material" cannot be answered from stored figures.

**So the same reader and health gate were run over every block of the copies' readings** (counts only; no text was printed or kept). This answers how much of the books the table can read at all, which is what P2's order needs:

| Vault | Readings | Blocks | Blocks with LaTeX | Health ok / suspect | Segments | Readable (and healthy) |
|---|---|---|---|---|---|---|
| `linear_algebra` | 4 | 1074 | 194 | 194 / 0 | 402 | 51 |
| `probability` | 4 | 579 | 164 | 163 / 1 | 259 | 25 |
| `arxiv_v2` | 12 | 4717 | 57 | 57 / 0 | 235 | 16 |
| **Total** | 20 | 6370 | 415 | 414 / 1 | 896 | **92** |

Refusals by reason key (all three vaults):

| Reason | Count | What it mostly is |
|---|---|---|
| `not_equation` | 577 | inline math with no `=`, such as `$x$`: not a miss |
| `syntax` | 69 | LaTeX outside the grammar's shapes |
| `multiple_relations` | 43 | chained `a = b = c` |
| `relation` | 32 | an inequality, `\approx` or `\propto` as the relation |
| `unsupported_command` | 26 | a command outside the table (which ones was not recorded: counts only) |
| `application` | 16 | a name applied like a function |
| `binom` | 11 | |
| `set` | 10 | |
| `sum` | 7 | |
| `subscript` | 5 | |
| `factorial` | 3 | |
| `derivative`, `limit` | 2 each | |
| `too_long` | 1 | |

Of the 319 segments that state a relation (896 minus `not_equation`), the table reads **92 (29%)**. **The honest reading: not vacuous on the books, but narrow, and unmeasured on real figures.** A figure also has to pass the binding (the author's names, exact literals, a bare reference), and `names` and `not_bare` cannot be measured until figures exist. The first real numbers come from the owner's report after landing (`learnloop reader report`, `figures.source_checks`, or the dry run above). That report is P1b's input: the author prompt was not changed, so a stored figure's names are whatever the author chose.

## Gate

Owner rule 2026-10-17: the full suite, the whole durability lane and the whole vitest run are the landing's. Targeted only here. Every command ran in `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, pytest at `-n 6` or fewer, vitest at `--maxWorkers=4`, one test command at a time, `TMPDIR` outside the worktree. Scripts outside pytest ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `lint-imports --no-cache` | **42 kept, 0 broken** |
| pytest, every test file naming figures or the check (131 files, list below) | 3272 passed, 6 skipped, 36 xfailed; 7 failed, each fixed and rerun in the next row |
| pytest, every contract file for what moved (config defaults, CLI help, table roles, AD classes, migration chain, head paths, mobile allowlist) plus the files changed (133 files, list below) | 8060 passed, 12 skipped, 3 xfailed; 2 failed, each fixed and rerun in the next row |
| pytest, the RW5c files plus the two fixed (`test_rw5c_*`, `test_cli_help_snapshot.py`, `test_teacher_te1b_migration.py`) | **297 passed** |
| `pytest -m durability` on `test_rw5c_migration.py`, `test_figure_prefetch_migration.py`, `test_tracked_fixture_databases.py`, `test_public_tip_guards.py` | **2 passed**, 24 deselected |
| `pytest --durable-sqlite` on `test_rw5c_migration.py`, `test_rw5c_judgments.py`, `test_rw5c_recheck.py` | **24 passed** |
| `pytest` on `test_tracked_fixture_databases.py`, `test_public_tip_guards.py`, `test_sqlite_file_copies.py` | **18 passed** |
| `npm run typecheck` | ok |
| `vitest run --maxWorkers=4 src/screens/reader/figures src/screens/LessonScreen.test.tsx src/components/askFigures.test.tsx src/screens/reader/alsoInBooksReader.test.tsx` | **472 passed**, 22 files |
| `npm run frontend:build` | built |
| `cargo check --manifest-path src-tauri/Cargo.toml` | ok |
| `db_generate_reference.py`, `db_validate_reference.py` | errors `[]`; head 238, 373 table notes, 1128 config leaves |
| `module_generate.py`, `module_validate.py` | PASS, 1153 module notes |
| `desktop_generate.py`, `desktop_validate.py` | PASS (`--check` clean) |

**What failed in the first two rows, all expected from the change:** the mobile allowlist's pinned RPC list (the new `reader.figure_recheck`); `test_no_code_path_can_store_or_render_verified_or_checked` (it pinned the claim's words as absent: now allowed only in `labels.py` and `FIGURE_FRAME`); the defaults snapshots and the four tests freezing older values (`test_reader_ca2_one_ask`, `test_batch3_landing`, `test_teacher_te1_successor`, `test_teacher_te1b_suggestions`: all 34 entries recomputed, and the frozen comparisons also drop the new key); `test_teacher_te1b_migration.py`'s composed chain; the CLI help snapshot (`reader` and `reader figure-checks` only); and one test of mine ordering verdicts by a tied timestamp.

**G23a-G23i, and where each is pinned:**

| Gate | Tests |
|---|---|
| G23a | `test_rw5c_labels.py`, `test_rw5c_switch_off.py::test_a_row_written_just_before_a_switch_off...`, vitest `the claim appears only on a book element...` |
| G23b | `test_rw5c_book_math.py`, `test_rw5c_source_check.py` (blocks, quotes, `test_a_fake_author...`, `test_a_model_quote...`) |
| G23c | `test_rw5c_source_check.py` (the planted-wrong corpus: domains, F8, mixed candidates, controls, literals, conditions, display) |
| G23d | `test_rw5c_labels.py::test_g23d_*` |
| G23e | `test_rw5c_labels.py` (no model label in the delivered spec, the view or the choices), vitest `every label slot reads from the elements`, `an id with no element...` |
| G23f | `test_rw5c_source_check.py` (no bubblewrap, a timeout, failed runs, inconclusive controls, unreadable and unhealthy blocks, a check that raises) |
| G23g | `test_rw5c_switch_off.py` against `tests/fixtures/rw5c_switch_off_golden.json`, recorded by `tests/rw5c_golden_source.py` on `git archive aae65635b6`; the admission tests in `test_rw5c_source_check.py`, `test_rw5c_recheck.py` |
| G23h | `test_rw5c_never_evidence.py`, the `evidence-never-reads-figures` contract |
| G23i | `test_rw5c_judgments.py` |
| G22's extension | `test_rw5c_display_twins.py`, vitest `figureDisplayCorpus.test.ts`, both over `figureDisplayCorpus.json`, whose `formatValue` and `String(v)` answers were written by node |

The sandboxed tests ran against real bubblewrap on this machine (`/usr/bin/bwrap`); the fake-sandbox twins cover the rest.

**Files of the first pytest row:** every `tests/test_*.py` matching `git grep -lE "figures|figure_|FiguresConfig|interactive_figures|source_check"` at the WIP commit. **Second row:** every `tests/test_*.py` matching `DEFAULTS_SNAPSHOT_BY_ALGORITHM|defaults_fingerprint|FiguresConfig|parameter_registry|cli_help_snapshot|table_roles|protected_tables|column_classes|migration_head_238`, plus the RW5c files and the fixed ones. Both lists are the grep at this commit; neither was hand-picked.

**Live calls and spend:** none. No model call, no paid command, no owner vault opened, no git in the main checkout, no stash, no GUI, no tailscale. Every author in the tests is a fake.

## Owner-run commands

Dry-run first; both make no model call.

```bash
uv run learnloop reader figure-checks --recheck --dry-run --json --vault <vault>   # by reason key; writes nothing
uv run learnloop reader figure-checks --recheck --json --vault <vault>             # stored figures due a check
uv run learnloop reader figure-checks --json --vault <vault>                       # the audit: each checked element
```

If a wrong "checked" ever shows: `figures.checked_labels_enabled = false`, write a reproducing test, and run a Codex review (§12).

## Open questions

For the owner:

1. **Every default Q2-Q18 above** is recorded as a default, not owner-confirmed.
2. **Coverage cannot be measured on the mvp-0.35 copies**, which hold no figures. After landing, `learnloop reader figure-checks --recheck --dry-run --json` on a vault with figures gives the first `names` and `not_bare` numbers. They decide P1b (a prompt addition asking for the book's symbol names and a bare reference) and P2's order.
3. **`view.label` and the Ask rail's line** still read as an illustration on a checked figure (`frameBadge`). It errs on the honest side and no slot is wrong; a follow-up could pass the checked badge to the rail.
4. **A followed figure** shows as an illustration until it is followed again after its recheck. A lesson or attempt-host figure built before this landing has no recheck control (Deviation 8).
5. **`\dfrac` and `\tfrac`** are refused as outside the table. `unsupported_command`'s 26 refusals were not broken down (counts only); a later instrument could name the commands.

For the landing: merge main first if follow-ups batch 7 has landed (its files do not overlap this stage's except `figures/prefetch.py` by name, which this stage did not edit). The reference notes and the snapshots will need regenerating after that merge.
