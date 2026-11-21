# Notebook activities: live displays, notebooks, masked cells and the authoring harness (NA)

**Status:** queued (owner, 2026-11-20). After the refactor and UX stages: evidence packets → AD memory → reveal adjudication → WQ teach-back → projects-as-goal → notebook activities → teacher v2 (TE5 to TE10). Track H and NA0 run beside the queue. H1 has landed: `learnloop notebook check`, package `src/learnloop/notebook_authoring/`, and the optional `notebook` extra. H1 checks structure only; the remaining harness and runtime work is queued (§15). §16 records the decisions and the values owed by the owner.

**Source:** `docs/brainstorming/Active Formats Brainstorm 2026-11-18.md` §1 (owner decisions of Nov 18 and Nov 20), §13–§17 (the brainstorm), §18 (code verification) and §19 (three adversarial reviews). The evidence, rejected ideas and links are there; this spec holds what to build.

**Owner decisions this spec implements (Nov 18 and Nov 20):**
- A real coding-agent harness authors marimo notebooks and displays; **both** app-vendored widgets and marimo notebooks live in LearnLoop.
- **Infrastructure, not a catalogue:** models compose freely from the widget and marimo toolbox, extensible across subjects.
- wigglystuff displays as **Show me figures** that bring a book's figure crop and nearby passages to life.
- The teacher **may edit the learner's notebook,** with every diff clearly visualized and interpretable; the **hidden scratch cell** is wanted; teacher and repair model **choose** between extending a notebook and creating a new one.
- In any coding dialog the AI **asks before writing code**.
- **Masked-cell probes and PIs join the existing probe/PI substrate** and are served when the pipeline chooses them.
- **Relax strict guardrails** that matter little downstream; keep what data collection, offline policy learning and learner-visible behaviour need (§14).
- One spec covers measurement, harness and runtime.

## 1. The problem

1. **LearnLoop's displays can't be manipulated beyond the figure grammar and sketch tiers,** and its models can't build interactive material. RW5d figures stop at grammar panels, QuickJS sketches and Manim video (`figures/rich.py:92`, `figures/request.py:64`).
2. **Learner emissions are thin.** Most attempts yield a graded answer; predictions, uncertainty, intermediate steps and process are rarely captured. `n_planted_trials` is never filled from real trials (brainstorm §18); repair effects are "not causally yet" for lack of randomized, logged episodes.
3. **The teacher and repair model can describe but not build instruments,** and there is no LearnLoop-owned loop for authoring and checking code.

## 2. Rules every stage follows

- **No rule maps a score, miss count or stuck flag to an action.** Mask choice, mask dose, reveal depth, repair stage, extend-vs-create and edit-vs-ask are candidates drawn with logged propensities (`propensity_kind` exact / estimated / deterministic / none). A propensity is called exact only when the probability vector is computed (a softmax, a categorical draw). A Thompson draw's selection probability is estimated by resampling and labelled `estimated`.
- **No made-up constants.** New weights, noise scales, tolerances and masses start at an existing seeded prior or zero and are learned. Machine-safety caps (time, memory, fuel, file size) are registered as `keep`, as `figures/sketch_engine.py` does.
- **Help is never certification.** Displays, teacher edits, reveals and in-notebook commits are assisted or in-context; only `standalone_cold` commits (§7.4) count toward cold evidence.
- **The commit is frozen and logged before any reveal or downstream output.** Enforced by the host, not the notebook.
- **The blind grader stays blind.** It sees `BlindGradingContext` (`attempts/blind_grading.py:104`): the frozen answer and the key, never interaction history.
- **Synthetic and execution answers never become evidence, human sensitivity/specificity, or router value.** They are unit tests of an activity.
- **Persisted meaning follows `docs/algorithm-change-playbook.md`.** Emissions are first recorded as uninterpreted receipts; a model reads them only after its own successor tag, `UPGRADES` row, `table_roles.py` classification and replay tests.
- **At n = 1, no stage claims a benefit.** Each adds a section to `learnloop data-capture report`, labelled observational unless randomized, with effective sample size.
- **Exam and held-out material is never served, quoted or used as supply,** in any cell, caption, label or note.

### 2.1 Design values and learned values (a registry)
Each number or count below is either an owner-set **design value** (registered as `keep`, changeable, and logged with every decision it affects) or **learned** (with its prior mean, prior variance and data source). The prior variance matters as much as the mean, because it sets the first offer and ask rates.

| Value | Kind |
|---|---|
| Prior centre of "one mask per notebook" (§7.5) | learned; prior from the plain-item arm |
| "One optional prediction" on a figure (§4.4) | design value (the most a figure may carry); whether it is offered is a draw |
| "One primary randomized reveal per (notebook, concept)" (§12.3) | design value (identification) |
| Visual-QA questions per cell (§11.5) | design value (cost against coverage) |
| Communicative-score pass threshold | Decided (owner, 2026-11-20): owner-set seed cutoff, then learned from owner-labelled verdicts; decided in principle; the value is owed by the owner |
| Design rates for arms (notebook vs plain item, repair stage 3, persona, work questions) | design value (like RO5's `check_rate`) |
| Probe count and tolerance in code classification (§8.5) | probe count is a design value; agreement enters §8.2's likelihood with the learned ε |
| Mask, reveal and medium choices | learned, drawn with logged propensities |

## 3. Architecture

```
            authoring harness (§11, durable jobs, tool-free model calls)
                 │ writes                         │ writes
                 ▼                                ▼
   display spec (data only)              activity.py  +  key.py
        │                                    │            │
        ▼                                    ▼            ▼
  app-vendored widgets (§4)          marimo runtime (§5)  sidecar sandbox (§6)
  sketch-style sealed frame          sealed frame/webview  generate / check / mutants
        │                                    │            │
        └──── host commit bridge (§6.3): freeze → log → grade → reveal ────┘
                                     │
           items / attempts / reveal_events / help_assists / receipts (§7, §12)
                                     │
                router, diagnoser, teacher, repair (§8–§10), offline analysis
```

Two runtimes, one contract:
- **Display tier** (app-vendored widgets): data-only display specs, no model code at serve time. For Show me figures, inline displays and fast reveal units. Desktop first.
- **Notebook tier** (marimo): activities, quests, projects, the coding module, anything that needs Python. A native, sandboxed marimo server per session (§5.1).
- **The contract** (§6) is the same for both: commit points, reveal units, a key the client never holds.

## 4. Display tier: app-vendored widgets

### 4.1 Display spec
- A `DisplaySpecV1`: `widget` (from a supported subset), `props` (schema-validated per widget), `bindings` (live readouts in the figure grammar, `figures/grammar.py`, whose TS twin is `figureGrammar.ts`), `recorded` payloads (StateViewer steps or TraceView spans recorded at authoring time), `notes`, `fidelity` (`reconstructed` | `illustrative`), `parameterisation` (§4.4), `reveal_units`, optional `commit` (§6).
- No model-written JavaScript in this tier. A display that needs code is a notebook.

### 4.2 Supported widget subset
- First subset: TangleDistribution, TangleLatex, FormulaAnimation, FormulaDAG (with `fn` replaced by grammar bindings), Matrix, Slider2D, ChartPuck, StateViewer (replay of recorded steps), SortableList. Others join after their adapter passes the tests in §15.
- The **notebook tier** runs native marimo, so every wigglystuff widget is available there unchanged, including the marimo-only helpers (WidgetFlow, WidgetDAG, Hint, shape_display, CellTour) and TextCompare.
- Each widget's full ES module dependency graph is bundled and pinned. The adapter implements the anywidget front-end model (AFM: `get`, `set`, `on`/`off`, `save_changes`, custom messages, lifecycle cleanup), not just four methods, and is tested per widget.
- Every widget has a **typed alternative** (enter the numbers) and a **static fallback** (a rendered frame), for accessibility and for the phone.
- ManimWeb is excluded from this tier (it executes scene JS verbatim and loads from a CDN). It enters later only as data-filled trusted templates with a vendored engine.
- **Gaps found building the Nov 20 prototype** (first candidates for model-written widgets, §11.4): a discrete toggle (TangleLatex has none; a sign flip had to be a number stepping −1 to 1 by 2; check wigglystuff 0.6.0's TangleChoice and TangleSelect first, which the gallery doesn't show); FormulaAnimation fork markers and parallel tracks (it takes one flat step list); a 1-D shape glyph (shape_display needs 2–3 axes); a diff mode for TextCompare (§9.3).

### 4.3 Where it renders
- A new sealed frame modelled on `apps/learnloop-tauri/sketch-frame.html` (`sandbox="allow-scripts"`, opaque origin, its own CSP with `connect-src 'none'`), as a second Vite entry with a new exact `frame-src` entry in `tauri.conf.json`. KaTeX comes from the already-pinned copy (`KATEX_VERSION = "0.16.47"`).
- Messages cross by a typed protocol like `sketchFrameProtocol.ts`. The frame never receives key material.

### 4.4 Live Show me figures (first use)
- A new figure tier `live` beside grammar, sketch and manim, with its own switch. Its data-only displays join `LESSON_TIERS` after NA1, because they render in-turn. Notebooks never do: they attach to lessons asynchronously (§9.9).
- Grounding reuses RW5d unchanged: `source_context` (passage plus `CONTEXT_BLOCKS` neighbours), `crop_image`, protection, admission, reuse keys, prefetch.
- **Parameterisation:** every distribution display declares the book's parameterisation (symbols, rate vs scale, Gamma(α, β) vs (k, θ)) and an explicit map to the widget's (scipy's). Check: mean and variance computed from the cited formulas equal the widget's `mean`/`sd` at sampled parameter values.
- **Fidelity:** with image input available, the start-state render is compared with the crop by a vision model; without it, or when the comparison fails, the display is labelled `illustrative`, never `reconstructed`.
- **One optional prediction:** a figure may carry one commit ("where will the mean move?"), using RW5d's existing figure-prediction path (`figures/predictions.py`). Optional; offered as a candidate, not forced.
- Exposure: shown displays write help and reveal rows as figures do today (`figures/help.py`).
- Decided (owner, 2026-11-20): the separate Manim figure tier retires when notebooks and cells cover its uses (§9.11), including animations as anywidgets; it remains until that coverage exists.

## 5. Notebook tier: marimo

### 5.1 Runtime: native first, Pyodide later if needed (owner, Nov 20)
- **Native marimo server.** One sandboxed `marimo` server process per notebook session, started and supervised by the sidecar, shown in a webview. Model-written notebooks run under bubblewrap (the PF sandbox's hardened profile, a new `pf-activity-v1`-style protocol for a long-lived server, no network namespace (the server listens on a Unix domain socket bound into the sandbox, and the sidecar proxies the webview's HTTP/WebSocket traffic to it, so "no network" and "reachable from the app" both hold; NA0.2 tests this), the session's scratch as the only writable path, a capped scope). The learner's own code runs on a native kernel under their control.
- Why native: the learner's own code needs it anyway, so it is one runtime, not two; marimo's server has documented endpoints for observing and running cells (marimo pair uses `/api/sessions` and `/api/kernel/execute`), which the teacher's verbs need; no masked or cold-eligible value is computed in the notebook kernel at all (§6.3), so none can leak from it; packaging is the existing `uv` environment; all installed packages and the host GPU are available.
- Costs to handle: process lifecycle (start, idle shutdown, crash recovery as a durable session), authentication between the webview and the server (a per-session token; the server bound to localhost), memory per session.
- **What the learner sees:** the app view with every cell run on load (the prototype's WebAssembly edit mode came up with all cells stale until "run all"); code shown per cell where it's the subject (coding and DSA activities), hidden elsewhere; the learner can switch a notebook to edit view.
- **Phone:** notebooks on the phone use the server on the desktop over the tailnet, as the phone page already does; with no connection, the phone shows the display tier's static fallbacks.
- **Pyodide later, only if needed:** for offline phone use or macOS/Windows learners without bubblewrap. Its costs (WebKitGTK behaviour, cold start, memory, package set, a large runtime shipped as release assets because of G8, a home-made bridge for teacher control) are recorded in the brainstorm doc §19.3.

### 5.2 Packaging
- H1 pins `marimo==0.25.2` and `wigglystuff==0.6.0` in the optional `notebook` extra in `pyproject.toml`; the runtime sandbox will mount the locked environment read-only.
- The **display tier's** front-end bundles (widget ES modules) are small and pinned in the app like the sketch engine (`engine.lock.json` pattern), within G8's limits (`tests/test_public_tip_guards.py:42,156`). Anything over 5 MiB ships as a release asset with a manifest (name, version, size, SHA-256, licence, source URL) and a reproducible recipe in git; no chunking or encoding to evade G8.
- Licences: wigglystuff is MIT at 576c56e; every transitive wheel, engine, font and copied doc is inventoried into `LICENSES.txt`.

### 5.2a The toolbox on the native runtime
- The notebook environment is not limited to marimo, wigglystuff and numpy. The prototype limited it that way for an easy WebAssembly export, and the birthday notebook had no curves because nothing could draw them. The native environment includes:
  - charting: Altair (marimo's reactive `mo.ui.altair_chart`, whose selections feed back into Python), Plotly and matplotlib;
  - data: pandas or polars;
  - LearnLoop's own figure grammar and sketch tier, wrapped as widgets;
  - trusted Manim templates;
  - real computation where it reveals the idea: train the tiny classifier, simulate the process, run the algorithm.
- The pinned environment's package list is itself a card (§11.3), so the author knows what it can import.

### 5.2b Look and feel: a LearnLoop theme for marimo (owner, Nov 20)
- **One stylesheet, LearnLoop's tokens.** Notebooks render with a LearnLoop stylesheet (marimo's `App(css_file=…)`, or injected by the host) that maps LearnLoop's design tokens onto marimo's own CSS variables:
  - the source is the default tokens on `:root` in `apps/learnloop-tauri/src/styles/app.css` and the palettes in `palettes.css`;
  - it sets LearnLoop's fonts, type scale and radii, and styles cells, callouts, accordions, tables, buttons, sliders and forms;
  - it carries §11.5's presentation defaults: a centered column, centered outputs, wide content scrolling inside its own container.

  A notebook should look like part of LearnLoop, not an embedded third-party app.
- **It follows Settings live.** LearnLoop switches palettes by setting `data-palette` on `<html>` (from `localStorage["learnloop.palette"]`, instantly from Settings). The notebook document uses the same attribute and the same palette blocks. When the palette changes, the host sets it on the notebook's document (postMessage to the frame or webview, or a URL parameter on load), with no rebuild. Charts follow too:
  - an `ll.chart_theme()` helper registers an Altair theme and matplotlib rcParams from the current tokens;
  - the host's palette value is a hidden reactive input, so chart cells re-render on a change;
  - widgets keep `theme="auto"`.
- **One source of truth.** The marimo theme is generated from `app.css` and `palettes.css` at build time, not hand-copied. A test fails if a palette's base token is missing from the generated theme, and the sketch-frame palette rule (base tokens stay literal hex) holds here too.
- **What the prototype theme taught (Nov 20).** A Codex agent drafted `learnloop_theme.css` from `app.css` and `palettes.css` and marimo 0.25.2's installed assets. It maps LearnLoop's tokens onto marimo's own variables (`--background`, `--foreground`, `--primary`, `--muted`, `--card`, the `--slate-*` and `--gray-*` ramps, `--cm-*`, the font variables) and onto wigglystuff's widget hooks (`--fd-*`, `--fa-*`, `--lt-*`, `--sv-*`, `--tc-*`, `--dt-*`). Four lessons:
  - marimo copies custom CSS into widget shadow roots, so `:host` rules are needed;
  - all LearnLoop palettes are dark, so the sheet forces marimo's dark variables even in marimo's light mode;
  - canvases (matplotlib images, Vega charts) can't be recoloured by CSS, which is why `ll.chart_theme()` exists;
  - JetBrains Mono has to be loaded explicitly.

- **Variables-only theme.** At 15:10 on Nov 20 the prototype's Codex-drafted theme (per-component rules, about 1,050 lines) was replaced, by the owner or another session, with a variables-only theme of about 310 lines. It is forked from "mininini" in Haleshot/marimo-themes (Apache-2.0; the attribution is kept in the file). It sets only marimo's variables on one tonal ladder (inset < page < surface < raised), lets marimo's components style themselves, and sets dark mode in the prototype's own `pyproject.toml` (`[tool.marimo.display] theme = "dark"`), not the repository's configuration. It is shorter and less likely to break when marimo updates (per-component selectors are tied to marimo's internal class names). **Decided (owner, 2026-11-20): variables only** (decision 13). Per-component rules, like the Codex draft's, are not used. The prototype's replacement theme is not yet purely variables (it still has component rules near its end), imports Google Fonts and doesn't follow Settings. The generated theme sets variables only, vendors its font for offline use, and follows `data-palette`.
  The generated theme replaces the hand-drafted one when this is built.
- **Reviewed per palette.** The §11.5 presentation review runs on the default palette and on each palette whose contrast differs most, so a chart readable on the default palette but not on another is caught.

### 5.3 Notebooks in the vault
- Quest and project notebooks live in the vault (owner, Nov 18) as `.py` files. LearnLoop also keeps, per notebook, **stable cell ids, revision hashes and actor-tagged patch events** (§9.3). Edits made outside LearnLoop are reconciled as `unknown` provenance.
- Decided (owner, 2026-11-20): the surface is called **notebooks**. Owner's note (verbatim): "they should be called notebooks". The Reader workbench remains a separate surface.

## 6. The activity contract and SDK

### 6.1 Files
- `activity.py` (client): the notebook. Public calculations stay local and reactive.
- `key.py` (sidecar only; never sent to the client, the planner or the teacher; the grader sees only the expected answer it already receives in `BlindGradingContext`): `generate(seed)`, `check(draw, answer)`, `mutants`, and per-mask correct values. It runs under a new PF-sandbox protocol `pf-activity-v1` (`run_sandboxed_python` today supports `pf-generator-v1` and `pf-equivalence-v1`).
- `contract` (declared in `activity.py` through the SDK, validated at authoring):
  - commit points: widget or input, prompt, response type (scalar with unit and declared precision, distribution, set/mask, ordering, expression, text, code, **curve**: a drawn prediction with CurveEditor, SplineDraw or Paint, scored on features such as sign changes, extrema and position against the true curve), facets;
  - **target:** the facet and the cold item family the activity should move (pre-declared, reviewer C1);
  - reveal units and their kinds;
  - **assumptions:** each premise the notebook's conclusions rest on, as a statement plus a code handle that switches it off or changes it, for example "the activation is ReLU", "the bias joins before the ReLU", "the birthdays are independent", "T is a bijection". Because the notebook is code, the consequence of changing an assumption is computed, not asserted (§7.7);
  - mask declarations (§7);
  - fidelity and source anchors.

### 6.2 SDK surface (Python, in the notebook; the display tier declares the same contract in `DisplaySpecV1`)
`ll.draw()` (public part of an immutable draw id), `ll.commit(widget_or_input, prompt=, response=, facets=)`, `ll.reveal(after=, show=)`, `ll.hint_unit(kind, ...)`, `ll.mask(cell, kind)`, `ll.explain(after=)` (a one-line "why" input). Every call is declarative; the host enforces it. `ll.explain` delegates to the shared work-question service (§9.8).
- The SDK never passes model-written text through a `str.format`-style template. In the prototype, marimo's `mo.md(...).batch()` formatted a commit prompt and the braces in `\frac{1}{\sqrt2}` crashed the cell at runtime, while `marimo check` passed.
- Response kinds include **`approach`**: a plan or method stated without solving (the brainstorm's plan-only and "understand" reps), graded by rubric against the item's solution recipe family.
- **The SDK owns each commit point's state.** A notebook may have several commit points (07 has five), and marimo allows one definition per global name, so per-commit state (the form, the frozen answer, the classifier, the mutant list) is namespaced by the SDK, not written by the author. The prototype needed a prefixed multi-gate helper for this. marimo also makes names starting with an underscore private to their cell; the prototype failed once on a shared `_PROBES`.
- **Cell names are part of the contract.** Tours (CellTour `cell_name`), "Ask about this" records, verdict records, lint findings, plan conformance and screenshots all key on cell names. Names are stable, semantic and unique, and a regenerated cell keeps its name unless it supersedes it.

### 6.3 Host-owned commit (integrity)
- Submission belongs to the host (the app or the native server's LearnLoop adapter), not to notebook code. A commit message is authenticated, idempotent and bound to: draw id, contract hash, code revision, widget snapshot, completed execution revision, and the client's visible-state hash.
- State machine: `editing → pending → frozen → graded → revealed`, with `error` and `offline_queued`. The host freezes and logs before acknowledging; reveals are never optimistic; a stale or forged commit is refused. Tests: races, retries, reconnects, stale outputs, forged messages.
- **The teacher cannot submit learner evidence.** `nb_commit_point` (§9) only *creates a commit point*; the learner commits.
- Downstream cells that depend on a masked cell are held until its commit is frozen (marimo's automatic reruns must not show the output first).

### 6.3a Trusted services, and what marimo 0.25.2 actually offers (second review, Nov 20)
- **No masked or cold-eligible value is computed in the notebook kernel.** A model-written notebook runs model-controlled Python, and marimo's dataflow graph is dependency metadata, not an information-flow proof. So:
  - keys, masked values and cold surfaces live only in sidecar services;
  - submission, freezing, reveal release and grading are sidecar services with atomic database transitions;
  - the kernel holds no submission credential and cannot release a held output;
  - edits after a freeze are new revisions, and switching a notebook to edit view is recorded as exposure.
- **marimo facts that shape the runtime** (checked against the installed 0.25.2):
  - The endpoints that run cells, change cell configuration and run scratch code require **edit mode**. Run mode gives each connection its own kernel, and `create_asgi_app` is run-mode only.
  - The CLI launches Uvicorn on a host and port. There is no Unix-socket option, so the §5.1 socket needs a launcher of our own.
  - UI element values are not persisted, so durable sessions, phone resume and commit snapshots need host-side replay of recorded values.
- **So NA0.2 is a gate, not a spike.** It must show:
  - an edit-mode server under the sandbox, behind an app-view front end;
  - the socket bridge with authentication, WebSocket proxying and reconnect;
  - held cells implemented through the host (cell `disabled` config driven by the sidecar);
  - UI-state replay;
  - the list of private marimo interfaces relied on.

  Model-written JavaScript runs in the webview, so the proxy injects a strict CSP, and the notebook's origin has no Tauri IPC.

### 6.4 The degenerate contract
Where answers aren't computable (law, languages, close reading), the contract keeps commit points, targets, reveal units and a rubric checker; `mutants` may be empty and the likelihood falls back to the grader's rubric outcome. NA0.5 hand-authors two activities each for a law and an arXiv-style vault against the draft SDK and records which parts were empty; §7–§8 must work with the degenerate contract.

## 7. Masked cells in the probe/PI substrate

### 7.1 Mask kinds
Forward (output from inputs), inverse (input from output), delta (change when one input changes, using committed vs live values), structural (which cells change), error (raises or not, why), step (next derivation line or algorithm state), **assumption** (what changes when a premise is removed or altered, §7.7). **Qualitative responses come first** where the mask allows (direction, ordering, which cells), because numeric forward masks measure arithmetic more than concepts (brainstorm §19.1).

### 7.2 As items
- A masked cell served outside its notebook is a `PracticeItem` with a new `practice_mode`: `masked_cell` (practice, reusable) or `masked_cell_probe` (diagnostic; the purpose derivation in `controller_snapshot.py:51-58` reads it as diagnostic; single-use per draw like `diagnostic_probe`).
- Hooks to extend: `scheduling/serving_exclusions.py`, `scheduling/device_eligibility.py` (`DESKTOP_ONLY_MODES` until the phone renders it), `learner_protection.PROBE_MODES`, `capability_mapping.default_capability_for`, a default rubric in `rubrics/*.yaml` with `applies_to.practice_mode`, `instrument_serving.unservable_reason` (refuse when the surface can't render), `PracticeScreen.tsx` / `FeedbackScreen.tsx` / `api/dto.ts`.
- The stimulus is a minimal display or notebook slice rendered from the key's public draw; grading is deterministic through `answer_check.py` or the key's `check`, inside `BlindGradingContext`.
- The pipeline serves them like any candidate (`Candidate` in `controller_snapshot.py:63`), with `expected_minutes` learned like other modes.

### 7.3 Surface identity: the activity-lineage substrate
- Notebook activities use the generic activity-lineage substrate that already exists (migration 065, `spec_p0_measurement_correctness.md` §3): `activity_families` (purpose `diagnostic` / `instructional` / `practice` / `assessment`, fixed for life) ← one per activity generator; `activity_card_versions` (`card_contract_hash`, `contract_json`, `lineage_kind` minor_successor | fork) ← the contract (activity hash + key hash); `activity_surfaces` (`surface_hash`, `fingerprint`, `surface_json`) ← **one surface per seeded draw**; `activity_administrations` (snapshot hash, `assistance_json`, `feedback_condition`, selection policy) ← one per serving or notebook instance; `activity_exposure_events` (`rendered` at most once per surface, `submitted`, `feedback_revealed`) ← the shared familiarity ledger.
- **Identity is content-derived.** A surface's identity is `surface_hash` over the rendered stimulus, with `fingerprint` for near-clones (migration 065), not the seed. Two seeds that produce the same stimulus are one surface, and a cosmetic edit to a generator does not mint new surfaces. Every serving looks up the exposure ledger. **Moving an item out of a notebook never restores coldness:** an item previewed or answered in a notebook keeps that exposure wherever it is served later (the prototype's 07 mislabelled previewed items as `standalone_cold`). Because a family's purpose is fixed for life, a generator used for instruction, practice and diagnosis gets one family per purpose.
- A fresh seed is a fresh surface only when its stimulus is new. The served `PracticeItem` also carries its own `shared_stimulus_id` (generator hash + seed + cell id), because PF variants otherwise inherit the parent's `surface_group_id` (`pf_publish.py:152`).
- Reproducibility fingerprints (generator, checker, runtime, seed) are pinned in `tests/test_identity_pins.py`; they are distinct from novelty eligibility, which the isomorph judge still decides. A **surface distance** for R_cold is defined: a different generator or representation, not only a new seed.

### 7.4 Coldness classes (enforced at read time)
- `in_context`: committed inside the notebook session where it was authored or explored.
- `fresh_seed_same_notebook`: a new draw of the same notebook.
- `standalone_cold`: served as an item outside the notebook, on a fresh surface, with cold-eligible values computed sidecar-only and no in-force exposures. **Only this class counts toward R_cold.**
- A **derivability check** at authoring marks a mask `in_context` when a visible descendant cell, plot axis or earlier reveal lets the learner invert it.

### 7.5 Choosing masks and dose
- Candidate masks are scored by the live EVSI machinery (`scheduling/evsi.py` `robust_evsi`, `lcb / (expected_minutes + burden_minutes)`) when likelihoods are promoted, else by separability (§8.1).
- The draw is a softmax/Thompson draw over candidates with logged propensity and the full candidate set; never a pure argmax. `selection_purpose` (`measurement` | `practice`) is logged and kept apart in mastery projections and calibration reports.
- **Dose is a draw too.** The prior is centred on one mask per notebook (the most separating one), the alternatives include more masks and a worked cell instead of a mask (procedural nodes for novices, Teacher sweep §1.5), and a plain text item on the same facet is a standing arm (§12.3).

### 7.6 One commit = one attempt
- A commit with several masked values is one attempt whose answer vector is scored by one joint likelihood (§8.2). No discount constant; duplicating a mask on one dependency path must leave the posterior unchanged (test).
- `"not sure, because…"` text is accepted as a response on **every** commit point, whatever its response kind, and routed to the diagnoser (learner text over skip buttons). The prototype offered it on only one notebook.
- Options in a selected-response commit present outcomes, not the explanation being diagnosed. "16" is an outcome; "16: recompute all 4 query rows" names the mutant and teaches before the commit. The pre-commit reveal audit (§11.2) asks this.

### 7.7 Assumption surgery, served by adaptive difficulty (owner, Nov 20)
"What if this assumption were removed or changed?" is the owner's favourite format (assumption surgery), made executable.
- **The probe.** Assumption toggles (TangleChoice or TangleSelect) switch a declared assumption (§6.1). Before the cell reruns, the learner predicts what changes: which conclusions survive and which break. The key is the rerun itself. The misconceptions this diagnoses are "nothing changes" and "everything breaks", plus assumption-specific ones from the registry.
- **The witness.** Where the format calls for it, the learner then builds the counterexample that breaks the conclusion without the assumption (a Matrix, a Slider2D or ChartPuck point, a dataset), and code checks it.
- **Examples from the prototype's notebooks:**
  - 07: replace ReLU with leaky ReLU, and the folds stop being flat;
  - 02: make T non-bijective, T(x, y) = (x, x³), and the transported structure fails;
  - 05: drop the causal mask, and the cached row is no longer enough;
  - 03: let two birthdays be dependent, and equalizing can stop helping.
- **No mastery threshold: AD serves it.** An assumption probe is a task at a feature point on the rung ladder (`curriculum/depth_rungs.py`): a transfer level plus a new feature **`perturbation = assumption`** (decided, see below). AD's band draw (`adaptive_difficulty/selection.py`, `ad_select_v1`) offers it only when its predicted success at that point falls in the practice band, and AD's calibrate mode picks the most informative candidate when it is unsure. AD's commissions (`adaptive_difficulty/generation.py`) can commission assumption items like any other feature point, and re-forecast them when they land. "Sufficiently high mastery" is the band itself, so no number is invented.
- **Why `perturbation` is its own feature, not a `transfer` value** (owner, Nov 20: "a new value of transfer, unless the implementation implies otherwise"; it does). AD codes `transfer` cumulatively: `feature_coding` in `adaptive_difficulty/priors.py` turns on a β step for the value and every level below it (`TRANSFER_ORDER = same_context, near, far, novel_combination`), and `depth_rungs.py`'s bounds, `selection.py`'s ladder levels and the transfer-distance bands all treat it as one ordered scale. A new value would have to sit somewhere on that scale. Appended last, an assumption probe would inherit every transfer step and be predicted harder than any novel combination, although "same setting, one premise toggled" can be easy. And it could not combine with a transfer level: "near transfer with an assumption changed" would be inexpressible. So `perturbation` (`none` | `assumption`) is a separate dimension coded as one additive β coordinate, the way `tools: open` is, learned from a seeded prior and combinable with any transfer level. Adding it changes persisted meaning (new β coordinates, the feature-audit literals in `adaptive_difficulty/feature_audit.py`, the enumerations in `curriculum/ai_contracts.py` and `depth_edge_authoring.py`, ladder order), so it follows `docs/algorithm-change-playbook.md`.
- **Live probing.** Inside a notebook, after a commit that is fast, confident and correct, the router may draw an assumption probe at once. Its value is its expected information: far-transfer success is most uncertain exactly then. It is a candidate with a logged propensity, never a rule.
- **The depth envelope.** The rung ladder refuses anything deeper than `select_method` without a learner-reviewed depth envelope (the comment on `DEFAULT_TRAJECTORY`). Assumption surgery sits at that depth, so this is where the envelope gets built: Decided (owner, 2026-11-20): generate a default list of fair-game assumptions per topic that the learner can edit (decision 14). The learner reviews that editable envelope before deeper probes are served.
- **What it feeds.** Cold answers at far-transfer points update AD's ability estimate along the transfer dimension, so LearnLoop learns whether the learner can carry an idea to a changed premise, not only apply it. Witnesses and predictions feed the misconception registry: which assumptions this learner over-weights ("everything breaks") or under-weights ("nothing changes").
- **In the Reader too** (§18): beside a theorem or definition, a cell lets the learner switch off each hypothesis and see the counterexample appear. That is assumption surgery where the learner reads, grounded in the passage.

## 8. Diagnosis with mutants

### 8.1 Separability is a property of the instrument
- Running mutants records **instrument validity**, not Beta counts: `mask_separability(item, cell, seed, mutant, output_hash, distinct_from_correct, distinct_from_mutants[], near_slip_of_correct)`.
- A **slip operator** generates neighbours of the correct value; a draw where any mutant falls in that neighbourhood, or equals the correct value (ITS P3), is marked low-information. Probes reject such draws; practice items keep them and log the rejection rate per generator.
- `item_misconception_discrimination` stays human-only for new sources: a separate source key (or ledger) keeps `source='sim'` rows (written today by `diagnosis/diagnostic_gate.py`) from merging with human counts. Test: running the gate with 10 or 1,000 seeds leaves every reader's posterior unchanged.

### 8.2 Likelihood
- P(o | h) = (1 − ε)·1[o = m_h(draw)] + ε·K(o | m_h), with explicit `H_slip` and `H_other` hypotheses. ε and the kernel K are learned per checker kind and pooled across families from a seeded prior. Continuous answers use a density with a learned noise scale; tolerance comes from the declared precision.
- These are tier-0 likelihoods; they never drive live EVSI until pooled human evidence promotes them (Pipeline Augmentation Plan §C).
- A match is admitted as `matched_single` (migration 130's vocabulary). Mutant provenance is logged (`learner_error_event_ids` / generated / owner). Mutants seeded from the learner's data are held out of evaluation; the `H_other` rate is a health metric.

### 8.3 Seeding mutants
From `error_events.misconception_consistent_answer` and clustered learner errors first, the LLM second (data-derived chaffs explained 23.9% vs 2.4%; LLM errors differ in distribution). Each mutant needs a non-applicability control (a draw where it should not fire).

### 8.4 What the learner and teacher see
- Diagnoses are hypotheses. The teacher **asks** ("did you carry the sign through?") rather than asserts, consistent with the accepted learner-input-after-a-miss spec.
- The "mix of interpreters" readout is shown to no one until it passes a held-out test: it must predict the learner's next wrong answer on a new surface better than slip plus base rate. Until then it is logged only.

### 8.5 Classifying the learner's code by behaviour
A code commit is classified by **running it**, not by reading it. The learner's function is called on probe inputs, and its outputs are compared with the reference and with each mutant's outputs. Each rule's agreement with the learner's outputs is recorded probe by probe, as a vector, and enters §8.2's likelihood with its learned ε. So a slip on one probe doesn't erase an otherwise clean match. Exact agreement on every probe is the special case.
- The probe inputs are chosen for separability (§8.1): no two rules may agree on all of them, and at least one probe must sit near each rule's edge case (07 used six, including h = (0, 0), where "bias after the ReLU" returns −1).
- Code that raises is logged with its error as the answer, and goes to the diagnoser.
- Code that matches no rule goes to `H_other`.
- The learner's own code runs in their own kernel (§5.1). Only the outputs and the matched rule are logged.
- The work question that follows quotes the learner's actual line (§9.8).

## 9. Teacher and repair model on notebooks

### 9.1 Verbs
| Verb | Operations |
|---|---|
| Observe | cell map, a cell's code, outputs, errors, variables, dependency graph, widget values, commit snapshots, interaction log |
| Author | create or extend a notebook or display (a durable job, §11) |
| Act | edit or add cells, set a widget value, step an animation, show a reveal unit, create a commit point, run scratch |

### 9.2 Teacher integration
- New teacher actions: `nb_observe` (a read action under the existing one-follow-up bound in `_teach_loop`, `teacher/service.py:1226`), `nb_request` (starts or extends a durable authoring job; the turn doesn't wait; results arrive like rich figures), `nb_edit`, `nb_set`, `nb_reveal`, `nb_commit_point`, `nb_scratch`.
- Each is added to `ACTIONS` and the strict `ActionRequestV1` **in all eight turn classes** (four of them TE2 variants) (`contracts.py`, including the overridden literals at `:230`), with an executor in `teacher/actions.py`, policy from `caller_for`, receipts, and tests for every schema combination, deferred results, crash recovery and protection changes. `PROMPT_VERSION` moves.
- A short notebook-state view (what the learner dragged, committed, reverted since the last turn) is part of each turn's context.

### 9.3 Edits the learner can read (owner decision)
- The diff view builds on wigglystuff's **TextCompare** (owner, Nov 20): two panels with shared word runs highlighted (`min_match_words`, `matches`, `selected_match` synced), so what is *not* highlighted is what changed. TextCompare is a shared-passage tool, not a diff tool, so LearnLoop adds insert/delete markup and the per-change reason on top.
- Teacher and repair edits **apply** to the learner's notebook and are shown as highlighted diffs: added lines green, removed lines struck, prop changes (`max: 10 → 50`), a "teacher added" band on new cells, and a **required one-line reason** per change. One-click revert per change or per turn; full edit history.
- Records: actor-tagged patch events against an expected base revision, stable cell ids, revision hashes, execution receipts. A revert after later learner edits is a merge, shown as such. Reverting doesn't undo exposure.
- Assistance follows **executed dependencies and exposure history**: a commit whose executed inputs include non-learner lines is assisted, whether or not those lines are still visible.
- **Coding dialog exception (Nov 18 rule):** edits to the learner's own solution code arrive as a proposed diff the learner accepts.
- An edit that would rerun a cell downstream of an open mask is held until that mask's commit is frozen.
- Measured, because "kept" is the default: uptake (kept / edited / reverted / ignored) joined to the next cold outcome; unassisted-commit rate against edit frequency (a helplessness signal); a "why this change?" work question from the shared service (§9.8), offered as a candidate after kept edits.

### 9.4 The scratch cell
- Runs in a separate disposable worker with a **bounded, permission-filtered snapshot**: scalars, arrays and selected tables only, filtered by the Reader's retrieval-permission table (no key material, no held-out text); unsupported values are refused.
- Cancellable, with receipts (source revision, inputs, output). Numbers the teacher states from it carry a "computed" mark that expands to the code; "computed" means executed, not verified.
- Never shown to the learner unless the teacher quotes it; quoting is exposure.

### 9.5 Extend or create
One action with a target (an existing notebook or a new one), logged with its propensity. Extensions are dated, labelled sections; new notebooks are linked from the lesson and the topic.

### 9.6 Repair, staged
- **Stage 1:** mark the fork (the first "≠" from `workbench/symbolic.py`, `CHECKED`/`CHECKED_NUMERICALLY`/`MODEL`) and offer a retry from it.
- **Stage 2** (a candidate after a failed retry or a recurrence): a static side-by-side at the fork line, the witness (drag a TangleLatex until the buggy identity breaks) and the one-line "why".
- **Stage 3 arms** (randomized, logged): the step-by-step animation; the "rule carried forward" contrast. Neither is the default. Each runs at an owner-set design rate and is compared with stage 2 on `standalone_cold` retries per minute. None is promoted or dropped before the comparison has the power §12.3 asks for.
- Retries: from the fork (assisted), then a fresh draw on a different surface (cold). Diagnosis-specific repair is randomized against generic reteaching, so the comparison Sleeman et al. made can be made here.

### 9.7 Simulated novice
Ships first as **"debug the interpreter"**: a mutant interpreter in `key.py`; the learner supplies a discriminating input plus a reason (code checks the input; the grader judges the reason). A voiced persona is an arm at an owner-set design rate, compared with kill-the-mutant on cold retries. It is not gated on winning a comparison that can't run before the arm exists.

### 9.8 Implementation teach-back
Questions about the learner's own cells while they implement ("why `+=` here?"), with a key committed first, a blind grade and a learned in-context weight, are specified across surfaces (notebook, Reader workbench, coding dialog, lessons) in `docs/specs/spec_implementation_teachback_v1.md`. Decided (owner, 2026-11-20): use that one service on every surface, folding §6.2's `ll.explain` and §9.3's "why this change?" one-liner into WQ5.

### 9.9 Topic notebooks: repairs appended to lessons
- One notebook per concept or learning objective accumulates over time: the lesson's visuals, repairs, the learner's own explorations and prediction cells, each in a dated section, with CellTour and a folded table of contents to navigate. This is the extend-or-create action's default target (§9.5).
- A repair is appended to the topic notebook of the facet it repairs. It starts from the visuals the learner has already seen there, and the author reads that notebook as context (§11.7).
- Lessons attach their rich visuals through the same notebooks. The notebook is built by a durable job and appended when ready, so a lesson turn never waits on it; `LESSON_TIERS` stays as it is for in-turn figures.
- **Sections are isolated and versioned.** marimo allows one definition per global name and reruns the whole notebook on load, so appended sections would collide and old ones would rerun. Each dated section is **its own small notebook**, with its own namespace and its own cell names. The topic notebook is a host-rendered index over its sections that loads older ones lazily. (`app.embed()` was considered and rejected: it returns one output plus definitions, so embedded cells lose the names that tours, "Ask about this", lint and verdicts key on.) Teacher edits (§9.3) and the learner's edit view create **new revisions** of a section; a published revision is never changed in place. Each section keeps its provenance: request, context snapshot, plan, harness version, cards and model. A shipped section is immutable. A negative verdict on a cell regenerates that cell as a new section that **supersedes** it; nothing is deleted. Appends are atomic against an expected base revision.
- **Coldness:** a topic notebook is in-context material. Masked items drawn from it are `in_context` or `fresh_seed_same_notebook`, never `standalone_cold`; cold items come from fresh surfaces served elsewhere (§7.4).

### 9.10 Ask about any cell (owner, Nov 20)
- Every cell carries an **"Ask about this"** affordance, provided by the host's notebook frame, not authored per notebook. So it exists on every cell of every notebook, including ones written outside LearnLoop. No wigglystuff widget does this. It is a LearnLoop component in the toolbox, and inside a notebook it is also available as `ll.ask(cell)` for an author who wants it inline.
- **Events, not reconstructions.** Each question is an append-only event written at submission, with the execution revision, the exposure state and a link to the answer. A later question or commit never rewrites an earlier one. (The prototype rebuilt its question log from current form values: a second question replaced the first, and committing changed an earlier question's `open_commit`. It also offered the box on selected cells only.)
- **The question is a learner emission.** It is logged as an observation of kind `learner_question` (§12.4) with:
  - the learner's words;
  - the cell id, its code revision, its rendered output and widget values at that moment;
  - which reveal units and commits were in force;
  - the notebook's target facet.

  The diagnoser reads it. A cheap Decider labels what the question is about (notation, purpose of the cell, a step, a prerequisite, the visual itself, the answer) as an annotation, never removing the text. Questions are some of the most direct evidence of where understanding stops, and they cost the learner nothing extra.
- **The answer** comes from the tutor (its existing `find_sources`, `find_practice` and `compare_sources` tools) with the cell as context. It is help: logged as exposure, judged for reveals by the Decider's shared judgment once built. While a commit is open in the notebook, the answer may not give away that commit's answer (the same guard as teacher answers).
- **What it feeds:**
  - a question that shows a gap may become a work question (`spec_implementation_teachback_v1.md`) or a candidate follow-up;
  - a question about a visual counts against that cell in the teaching review's data (§11.5 layer 3: "what would a learner take away?" now has real answers);
  - the question and its answer may be appended to the topic notebook (§9.9) as a dated note.

### 9.11 Entry points: ask for a notebook about any concept (owner, Nov 20)
- **From the concept graph or the facet well:** the learner browses concepts, or asks in natural language ("explain why the KV cache is linear per step"), and gets a **teacher notebook** that explains it. The query is resolved to concepts and facets by the existing retrieval (`find_sources`, the concept graph). The notebook is authored by the durable job (§11.1) using the read API (§11.7), so it is **learner-model informed**: what the learner has seen, missed and asked shapes the visual plan. It is appended to that concept's topic notebook (§9.9). The request itself is an observation (`learner_question` at the concept level, §12.4).
- **From textbook spans:** a passage or figure in the Reader becomes a notebook the same way (the Show me path, §4.4, extended to the notebook tier). Grounding stays RW5d's: the passage, its neighbours, the figure crop and the held-out rules.
- **Notebooks supersede explanation videos and the Manim figure tier.** Decided (owner, 2026-11-20): retire the separate tier when notebooks cover its uses. Owner's note (verbatim): "Manim animations can be anywidgets, so they are superseded by marimo/wigglystuff notebooks and cells". Notebooks can carry animation where it helps: wigglystuff's ManimWeb (trusted templates; it runs scene JS verbatim from a CDN, so it needs a vendored engine and templates the author fills with data), FormulaAnimation, or a rendered Manim clip embedded in a cell. Unlike a video, they also carry interaction, prediction and the learner's own work. The rich `manim` tier (`figures/rich.py`) and `content/authoring/concept_animation.py` are retired once the notebook tier covers their uses; until then they stay as they are (decision 12). Before retiring, extract the sandbox helpers: `pf_sandbox.py` imports `_sandbox_bwrap_path` and `_sandboxed_command` from `concept_animation.py`.

### 9.12 How a notebook reaches the learner: worked through with notebook 07
Notebook 07 is the prototype used to explain the flow here; private learner history is omitted. A notebook is **offered, never forced, and also requestable**.

**Entry points:**
1. **Suggested on Today.** `router/lesson_suggestions.py` already proposes `instruct(lesson)` on one learning object for one of its reasons: `new_goal`, `below_band` (AD predicts the learner below the practice band) and `cold_missed` (any cold check missed since the topic's last lesson; since the owner's IH decision 4, `mvp-0.55`, there is no separate `cold_failing` gate). `REASONS` in `src/learnloop/router/lesson_suggestions.py` remains exactly (`new_goal`, `cold_failing`, `below_band`, `cold_missed`), including the legacy constant for compatibility. Serving is **two-stage** (§9.13): the suggestion picks the learning object, then a second logged draw picks the medium. The learner accepts or declines. Acceptance is the existing learned model (time of day, minutes left, reason, spacing, decline depth), so "Not now" costs nothing and is learned from.
2. **After a miss, as a candidate.** A repair section is a candidate after a miss, priced with its authoring spend and latency like any other (§9.13). It is never appended automatically: the learner may recover before authoring finishes, so an automatic repair could arrive after the need has passed.
3. **Asked for.** From the concept graph or the facet well, or by a natural-language query (§9.11), or "Show me" on a Reader passage. The request resolves to a concept, the job runs, and the learner is notified when it's ready.
4. **Inside a lesson.** The teacher's `write_plan` attaches a planned notebook section.

**Latency is handled by prebuilding.** RW5d's learned prefetch (quiet, desktop and plugged in, plan transport only) builds notebooks for likely suggestions ahead of time, so an accepted suggestion opens at once.

**How the author knows what to retrieve.** Every entry point carries a **target** (facet or concept, plus the reason or the learner's words). The author pulls the rest through the read API (§11.7):

| What the author needs | Read |
|---|---|
| Attempts on the concept and their error types | `read_evidence(facet)`: the evidence-packet claim card |
| Prerequisites and successors | `read_concept` over the concept graph |
| Earlier worked examples, subject to retrieval permissions | `read_history` (an existing teacher action) |
| Misconceptions to turn into mutants | `read_misconceptions(facet)` |
| What the learner has already seen; reserved cold surfaces | `read_exposure` |
| Earlier sections of the topic notebook; source passages | `read_topic_notebook`, `find_sources` |

**Where it fits in the action router:**
- **A notebook is one more candidate action:** "instruct with a notebook" on a learning object, beside the text lesson, a follow-up item and plain practice. It carries contract features (commit points, explanation asked, mutant contrasts), learned `expected_minutes`, and a pre-registered cold target (the learner's next `standalone_cold` answer on the facet). Its value is learned from that outcome and pooled over contract features (§12.3), against the standing plain-item arm. Every draw logs its propensity.
- **Inside the notebook,** each commit point is an in-context observation that never certifies. A code commit is classified by its behaviour against the mutants.
- **The transfer items join the item pool** as `masked_cell` / `masked_cell_probe` items on fresh surfaces. The scheduler later serves them as ordinary cold items outside the notebook, which is where the evidence of learning comes from.

### 9.13 Serving: pull first, priced, and spaced (second review, Nov 20)
- **Two-stage serving.** The router first picks the learning target, then a second logged draw picks the medium: text lesson, a new notebook section, reopening a section, or a plain item. Requested sessions and offered ones are logged apart.
- **Price is part of value.** Authoring spend and latency are a price inside the candidate's value, so a 0.5M-token notebook competes honestly with a two-minute item. A notebook carries a **target minutes** field in its contract, and the offer states it.
- **Pull first: a "Ready for you" shelf on Today.** No toasts. An entry is revalidated against current evidence when it is shown (a notebook built for a gap since closed is retired), expires, and resumes at the last commit. One entry per published revision.
- **Design-rate randomization.** Notebook against plain item is randomized at an owner-set design rate, as RO5's `check_rate` is. Without it, honest priors and early declines starve the notebook arm before it can show anything.
- **Peek before open.** The notebook's key figure as a static frame with one control, in Feedback or on the shelf; "open" continues from there.
- **One-cell return.** A cell already seen comes back days later as a fresh-seed prediction at plain-item minutes, typed on the phone if needed. This gives notebooks a spaced tail. The unseen transfer item is reserved separately, and reopening a notebook records exposure that invalidates reservations it contaminates.
- **Exam digest.** Before an exam goal's date, a review notebook is assembled only from already-verified sections, with no new authoring, followed by protected cold checks.
- **Phone: "build this for tonight".** The phone sends a concept or question to the desktop shelf, and receives slides of verified static frames.
- **Reader margin marks.** Prebuild from reading position, and mark passages that have a ready section.
- **Steer at accept.** "What do you want to see?" is passed verbatim as the entry intent (§11.7).
- **Coding and project traces.** On a failing test in the learner's own repo: a trace notebook (`LiveEdit.from_pytest`), independent behavioural and property checks, and a work question. Exam adapters ground notebooks in allowed concepts and practice sources (`goals/exam_readiness.py`, `goals/exam_pool.py`).

## 10. Notebook items from the learner's own work
- Cells the learner wrote come back later as masked items (generation plus retrieval of their own work), served through §7.
- `projects/probes.py` (standalone `project_store.sqlite`, sealed until `probe_delay_days`, practice only) is the first source. Decided (owner, 2026-11-20): join project-probe answers to learner state in NA5 (§16); today they remain in the standalone store.

## 11. The authoring harness

### 11.1 Loop
- A **durable job** (the rich-figure job pattern: leases, heartbeats, recovery, `report()` cancellation), not extra teacher turns.
- **Lifecycle, persisted phase by phase:** context snapshot → alternative plans → selected plan → implementation → verification → revision → publication. Each transition records its inputs, outputs, spend, findings and a resume checkpoint.
  - Budget for verification is reserved before another authoring round starts.
  - Cost is logged per stage and round (model tokens, screenshots, execution, wall time) and reported per accepted cell.
  - Verified sections are reused before anything new is authored.
  - Cancellation, a missing image route, a runtime crash and an exhausted budget each have a defined outcome. The last verified revision is kept. A failed teaching review never downgrades a notebook to help-only: it stays unpublished.
  - How many alternative plans to draft is itself a logged draw.
- **Two caches:** generation (request, learner-context snapshot, source hashes, prompt and cards) and verification (artifact, dependencies, runtime, viewport, palette, interaction state). Protection is rechecked before a cached notebook is served.
- Each model call is one strict structured output on the configured route (tool-free plan transport by default); tool requests follow `ai/tool_requests.py`; LearnLoop executes them and returns observations. The loop stops when all checks pass or the job's spend envelope (the figure route's daily envelope pattern) is used.
- Tools: `read_card`, `search_examples` / `read_example` (§11.3), `write_cells` / `edit_cell` (job scratch only; traversal and symlinks refused), `run_activity` (native, `pf-activity-v1`), `run_tests`, `check_derivation` (RW2b), `check_tex` (`figures/katex_tree.py`), `check_props`, `check_leakage` (`practice_leakage.check_leakage`, `reserved_findings` over every cell, output, caption, label and note), `render_preview`, `find_sources`.
- **The model writes cells, not files.** It submits (cell name, code) pairs; a small LearnLoop writer emits marimo's file format, parses it back with marimo's loader and runs `marimo check`. marimo derives each cell's references and definitions itself; hand-written cell signatures are error-prone. The prototype used marimo's private `marimo._ast.codegen.generate_filecontents`; the writer hides that behind one module pinned with the runtime, so an upstream change breaks one place. Tools that inspect notebooks use marimo's parser and dataflow graph, never text matching: marimo turned a pure function cell into a top-level `@app.function`, which broke a regex-based check in the prototype.
- **Context assembly** joins attempt → item → error events → source spans. When `practice_item_snapshots` has no row for an attempt, the item comes from the vault YAML at its recorded hash.
- **Numbers shown to the learner come from executed code** (a cell, the key, or the scratch worker), never from text the model typed into a note.

### 11.2 Verification (before anything ships)
1. Schema and props; KaTeX; maths (a "≠" step blocks the display).
2. Notebook structure: single definitions, no cycles, pinned dependencies.
3. Execution and tests in the sandbox; same-seed reproducibility.
4. **Contract drive** in the target runtime: the correct answer passes; each mutant's answer fails with its misconception flagged; junk fails; nothing from `key.py` reaches the client before commit; masks pass the derivability check; draws are checked for coincidence and near-slip collisions.
   - **Every reveal state runs.** A normal headless run never executes held cells, so their errors stay hidden (the prototype's brace crash sat behind the gate). The host exposes a **synthetic-commit interface** for verification only: in a headless session it injects a commit (correct, each mutant, junk) through the same path a learner's commit takes, and each resulting state runs to completion. It is unreachable from a learner session.
   - **Verification runs inside marimo's runtime** (a headless sandboxed server or `marimo export html`), never as a plain script or `app.run()`: Hint and WidgetFlow raise `RuntimeError` outside a running marimo session.
   - **Pre-commit reveal audit.** Text checks miss structural leaks. In the prototype, a graph shown before the commit gave away the answer through its shape (bias before ReLU), and a teacher edit stating the answer was ungated. The audit has two parts: a rule (no cell that runs before the commit may read a value derived from the key, the answer, or a reveal unit; checked on marimo's dataflow graph), and a judgment (the locked-state render, as text and a screenshot where image input exists, is asked "does anything visible give away the committed answer?").
   - **The mutant state is real.** The synthetic commit for a mutant seeds that mutant's actual answer, including mutant code for a code commit. So the cells after the commit render what a learner holding that misconception would see, and those states are reviewed too.
   - **After any fix, re-run the review on the changed cells and their neighbours,** not only the question that failed. In 07, the fix that made regions countable (brighter fills) hid the zero line in the next round.
5. **Independent reference** on a sample: a second model or route writes `check` from the stated problem; disagreement fails the activity (generator–checker collusion).
5b. **Teaching correctness (second review, Nov 20).** No layer above checks that what a notebook teaches is right: a figure can be legible and wrong. A solver blind to the notebook derives each cell's stated claim, each commit key and each mutant's "why" from the source passages and the item. Any disagreement blocks publication. The plan pins every definition the notebook relies on to the source's wording. 07 showed why: "linear region" can mean a piece of the function or an activation pattern, and the two count differently. 07's Part 3 counts activation patterns (7) where the function has 4 pieces, and its Part 1 treats a surviving kink as a misconception. Which one the learner's source means was never checked.
6. **Presentation and teaching review** (§11.5): layout lint on every cell, a Decider screenshot pass per cell, and a teaching-intent review. Findings go back to the authoring loop with cell ids.
- Results are cached by artifact, toolchain and runtime hashes. The landing gate runs a small deterministic suite; full certification runs on changed activities and on runtime changes, outside the landing gate (like `ux_walk_browser`). The prototype's costs: tens of seconds per headless export; a real-time browser check of six notebooks ran past ten minutes (a virtual-time screenshot only showed "Loading marimo…").

### 11.3 Capability cards and the example index
Decided (owner, 2026-11-20): build the example index in NA0, alongside track H, so owner-side authoring can use it immediately.

The authoring model's real dependency is narrow: marimo and widget API facts plus working examples. Building the prototype took about 18 web lookups, and **the website was not enough**: WidgetFlow's synced values, CellTour's step format and FormulaDAG's `fn` rules were only in the installed package's docstrings and source; TextCompare turned out not to be a diff tool. So every source is read from the **installed, pinned package**, not the web:

| Source (at the pinned wigglystuff commit and marimo version) | Becomes | In the prompt? |
|---|---|---|
| `AGENTS.md` roster (one row per widget: class, core synced traits, one line) | the **index**, compressed to ~1 line per widget | always (a few KB) |
| `inspect.signature`, docstrings, the synced traits read off the class | the API part of each **card** | `read_card(name)` |
| `docs/reference/*.md` (71 pages, about 200 KB) | the prose part of each card | `read_card(name)` |
| `demos/*.py` (95 notebooks, about 650 KB) | **example slices** (below) | `search_examples` / `read_example` |
| marimo's own `get_marimo_rules` and API docs for the pinned version | marimo cards (`mo.ui.*`, layouts, `mo.stop`, `mo.state`, forms) | `read_card` |
| LearnLoop's SDK and contract patterns (commit gate, reveal unit, mutant `classify`, scratch, diff) | **recipe** cards | index always; body on demand |
| Gotchas found in verification (the `.batch()` braces; marimo-only helpers; distinct objects in WidgetFlow; `np.dot` drops shape names) | a "gotchas" line on the card they belong to | with the card |

**Example slices, not whole demos.** Each demo is parsed with marimo's loader, and its dataflow graph gives every cell's definitions and references. For each cell that constructs or reads a widget, the indexer takes that cell plus its **ancestor closure**, drops markdown-only cells, and records the result as a slice. A slice is a short runnable example of that use (not necessarily the smallest): in `demos/state_viewer.py`, the maze viewer is 5 of 18 cells. Markdown cells that carry the teaching context the code relies on are kept, and the extracted slice itself is executed and rendered, not only its source demo.
- Each slice is executed headlessly once at index time (an execution receipt), and dropped if it fails.
- It is stored with: the widgets and `mo.*` APIs it uses (from the AST), its line count, a one-line purpose written once by a model at index time, the demo path and the pinned commit.
- Slices are embedded with LearnLoop's existing embedding route and searched by `search_examples(query, widget=None, k)`. That returns up to k slices under a line budget; `read_example(id, expand="ancestors" | "demo")` returns more only when asked.

**Exemplars from LearnLoop itself.** Activities that pass §11.2 (and, once data exists, those whose pooled value is highest) are indexed the same way, so the library grows from what worked. The index is rebuilt when the pinned versions change; a card's example re-runs then.

**For the owner-side path,** the same index is exported as a static folder (index, cards, slices) that Claude Code or Codex can read with ordinary file tools.

**Gotchas found building the prototype.** Each goes on the card it belongs to, so the author reads it when it reads the card:
- **marimo:**
  - `mo.md(...).batch()` formats its template with `str.format`, so braces in LaTeX break it; never pass model text through it.
  - Names starting with an underscore are private to their cell.
  - One definition per global name.
  - A pure-function cell becomes a top-level `@app.function`.
  - Hint and WidgetFlow raise outside a running notebook.
  - `mo.center` shrinks an anywidget to its content width, so FormulaAnimation scrolled sideways.
  - An anywidget must be wrapped in `mo.ui.anywidget(...)` for its `.value` to be reactive. Synced values then sit under keys such as `.value["values"]`.
  - A UI element can be rendered inside the output of the cell that reads it (the co-visibility fix in 07) without losing its state.
  - `mo.ui.table` adds Search, Columns, Explore and Export controls that a reviewer read as jargon; small learner-facing tables are plain Markdown.
  - The WebAssembly export needs dependencies declared in a PEP 723 header, and its edit mode loads with every cell stale.
- **wigglystuff:**
  - FormulaAnimation's default 360 px stage clipped long TeX. Its stage hides off-stage steps on purpose (a lint false positive). KaTeX subscripts render flattened inside it in this setup (open).
  - StateViewer's `view_func` HTML is flattened: a table came out as "rowK[:,0]K[:,1]", so plain lines are used. Two StateViewers side by side overflow a medium-width column, so they are stacked. `show_code=False` and `only_changes=True` keep a pair compact.
  - LiveEdit tables can be wider than the cell.
  - WidgetFlow's edge labels can collide with arrows and nodes in its overlay. A plain row of glyphs with arrow text is safer when labels are long.
  - TextCompare highlights shared runs; it is not a diff.
  - shape_display needs two or three axes.
  - The gallery doesn't show TangleChoice and TangleSelect.
- **Charts:**
  - Altair's `mark_*(color=…)` can be overridden by a registered theme; `color=alt.value(…)` holds.
  - Altair 6 registers themes with `alt.theme.register(name, enable=True)`.
  - matplotlib images are opaque to the DOM lint, and so is Vega's canvas: only screenshots review them.
  - A shared scale can hide a small series (05's cached line); add a detail panel.
  - Curves that coincide hide each other (07's three orders); use small multiples.
  - Light region fills swallow a white overlay line; check overlay contrast against every fill.

### 11.3a The roster the author should reach for (beyond the prototype's widgets)
The index (§11.3) covers everything installed. These are the ones the prototype didn't use and that most often fit a teaching need, with their affordance in one line:
- **Answers:**
  - TangleChoice and TangleSelect: discrete choices and assumption toggles;
  - Matrix: counterexamples and edited matrices;
  - CurveEditor, SplineDraw, Paint: drawn predictions (the `curve` response kind);
  - HeatmapSelect, ChartSelect, ChartMultiSelect: "select the region where…";
  - SortableList: order derivation steps or proof lines;
  - GridDraw: DP tables;
  - EdgeDraw and GraphWidget: draw a prerequisite graph or a dataflow.
- **Showing:**
  - ThreeWidget: surfaces in 3-D (07 in two inputs: the output surface being folded, likely the strongest picture of "fold");
  - RidgelineChart: a distribution across a parameter sweep;
  - PlaySlider and FramePlayer: time-stepping;
  - ManimWeb: trusted templates only (§9.11);
  - FitProgress: training dynamics;
  - ParallelCoordinates and PairPlot: data concepts.
- **Layout and help:** Pip and FloatingPanel keep a control in view while scrolling (the co-visibility fix, §11.5); Hint; DriverTour and CellTour.
- **Voice and process:** SpeechToText for voice teach-back; KeystrokeWidget only with the learner's opt-in, local process data.
- **Codebases:** ModuleTreeWidget and ApiDoc to explore a repo's structure; TraceView for request flows; `LiveEdit.from_pytest` on failing tests.
- **marimo:**
  - `mo.ui.chat` for "Ask about this" threads, the simulated novice and work questions;
  - `mo.ui.code_editor` and in-notebook pytest cells to grade implementations;
  - `mo.ui.dataframe` and `mo.ui.data_explorer` for data-literacy topics;
  - SQL cells with DuckDB;
  - `mo.ui.altair_chart` selections as answers;
  - `mo.ui.run_button` and `mo.ui.refresh`;
  - `mo.ui.file` and `mo.ui.microphone`;
  - the slides layout for phone lessons;
  - `mo.persistent_cache` for expensive cells (training, simulation), which also cuts re-run time in review.
- **To grow:** gaps found so far (FormulaAnimation fork markers and tracks, a 1-D shape glyph, a TextCompare diff mode, an assumption-toggle panel) are the first candidates for model-written widgets, each starting as an affordance card plus a test (decision 2: they join automatically after checks).

### 11.3b Extending the toolbox (H3)
Decided (owner, 2026-11-20): the toolbox must be easy to extend. Owner's words (verbatim):

> "For notebooks also--we should make it easy to add additional tools available for the model. For example, tangleLatex from wigglystuff was recently released and would be extremely helpful as a tool for making marimo notebooks."

**Orchestrator's reading (design rule):** H3 generates tool cards from the installed, pinned packages' own sources. Anything extraction cannot supply, such as a typed alternative, a static fallback or a check, belongs in one declarative entry per tool. A test must establish that every exported widget has a card or is listed as deliberately left out. Adding a tool by bumping its pinned version in the `notebook` extra and regenerating the cards and example index is a normal landing, including `uv.lock`, the licence notice in `LICENSES.txt`, and the parser's version check in `src/learnloop/notebook_authoring/marimo_adapter.py`.

### 11.4 Owner-side authoring
H1 has landed: `learnloop notebook check PATH --scope structure --out REPORT_DIR` checks a notebook written outside LearnLoop (Claude Code, Codex, by hand) without executing it. It reports structural findings and incomplete review, never acceptance. Track H extends it to the full §11.2 review. Widgets written this way, like model-written ones, join the library automatically once they pass checks (owner, Nov 20).

### 11.5 Presentation and teaching review (owner feedback, Nov 20)
The owner's review of the six prototype notebooks found overlapping text (04), text cut off in the last cell (05), cells too small and not centered, and cells whose purpose was unclear (05's later cells, 02, 06). None of these are caught by execution or contract checks. Three layers run on every reveal state from §11.2 item 4, cheapest first:

1. **Layout lint (deterministic, every cell).** In the headless runtime, each cell is located by its `[data-cell-name]` container and its rendered DOM is measured:
   - text-bearing boxes whose rectangles intersect (overlap);
   - content wider or taller than its container (`scrollWidth > clientWidth`, clipped overflow), including SVG text past its viewBox;
   - outputs much narrower than the cell, or not centered in it.

   Each finding carries the cell name, the element and the rectangles. Thresholds for "too small" and "off-center" are layout facts measured in pixels against the cell, registered as `keep` presentation settings, not model parameters. Content inside canvases and iframes is opaque to the DOM, so it goes to layer 2.
2. **Decider visual pass (cheap model, every cell).** Each cell is screenshotted alone, and a Decider-tier model with image input answers fixed questions, each yes/no with the region:
   - Is any text overlapping other text or graphics?
   - Is any text or graphic cut off?
   - Is the content legible at this size?
   - Is it awkwardly placed (crowded, off-center, mostly empty)?

   It returns one record per cell. The questions are fixed so answers are comparable across models and versions. The Decider's accuracy is measured against owner-labelled and seeded defects (§11.5, "Gaming and accuracy"), not by agreement with layer 1. This needs a route with image input (`FigureRoute.reads_images()`; decision 4). Decided (owner, 2026-11-20): use an image-capable OpenRouter profile behind the per-action offer, with an independent checking route allowed when author and checker would otherwise be the same model. This is decided in principle; the value is owed by the owner: the named profile, its verified price and the per-run cap. Paid runs still need the owner's OK. Without the route, layer 1 still runs and the gap is logged.
3. **Teaching-intent review (stronger model, every cell, then the notebook).** Each cell declares one sentence of intent in the contract ("shows that only the both-x-and-y group changes as x moves"). The reviewer sees the cell's screenshot, its intent and the notebook's target facet, and answers:
   - Does the render make that visible to a learner who doesn't already know it?
   - What would a learner take away?
   - Is there a widget used without revealing anything?

   At notebook level it asks whether every cell earns its place, whether the key contrast is explicit, and whether a domain-native representation is missing (§11.6).

Layers 1 and 2 are pass/fail inputs to the loop. Layer 3 gives findings and a revision request, and a notebook that keeps failing it is not shipped. All three are logged per cell and per harness version, so presentation quality can be compared across models and prompts.

**What the first real run of the review found (Nov 20, notebooks 02–05 v2 and v1's 04 and 05):**
- **Layer 1 caught:** v1 05's clipped last cell (756 px of content in a 358 px box), its LiveEdit tables 594 px past the cell, v2 05's diff table 46 px past both edges, and off-center cells (content at 60% width, shifted left).
- **Layer 1 missed:** v1 04's overlap, an edge label colliding with an arrowhead and a node in WidgetFlow's overlay (text against graphics), and a truncated Vega legend label drawn on a canvas. Both were visible in the per-cell screenshots. So layer 2 is not optional.
- **The lint needs care:** cells must be scrolled into view before they are measured (marimo renders lazily and scrolls inside its own container), and text boxes must be compared per line fragment (`getClientRects`), or a wrapped inline label reads as an overlap.
- **Layer 3 caught teaching failures no layout check can see:**
  - a default that made the key picture degenerate (02's parallelogram collapsed to a line at v = w);
  - a log scale that hid the very difference the caption claimed (05's linear against quadratic work).

**Layer 2b: the Decider battery (owner, Nov 20).** A cheap Decider-tier model sees only a cell's screenshot (and, where noted, its caption or intent), never the code. Questions are fixed, so answers are comparable across models, harness versions and palettes. Each answer is logged with its cell, state and palette.

*UX questions (yes/no, with the region):*
- Is any text overlapping text or graphics?
- Is any text or graphic cut off?
- Is every axis labelled, with units where the quantity has them?
- Can every legend entry and colour be told apart?
- Is anything too small to read at this size?
- Is the content crowded, off-center or mostly empty?
- Does any visible label use internal jargon?
- Does the figure match the page's palette (no white boxes on a dark page)?
- Is there a control whose effect isn't visible in this view (co-visibility)?
- In the locked state: does anything visible give away the answer to the open question?

*Semantic questions, which separate good visualizations from poor ones:*
1. **Visual question answering with ground truth.** Each cell's plan carries one to three questions whose answers the author's own code computes, for example "at which x is the collision chance lowest?", "how many places does the solid curve bend?", "which run does more work at step 4?". The Decider answers from the screenshot alone. Its accuracy is the cell's **communicative score**: a figure that doesn't let a reader read off its point fails, however correct its code. This is the strongest single filter, because it is checked against computed truth, not taste.
2. **The naive-viewer takeaway.** "In one sentence, what does this figure show?" A second call judges whether that sentence matches the cell's declared intent (§11.5 layer 3). A mismatch means the figure says something other than what the author meant.
3. **Contrast detection.** Where a cell contrasts the correct rule with a mutant, the Decider sees the two renders unlabelled and is asked which shows the stated property, for example "outputs are never negative". If it can't tell, the contrast isn't visible.
4. **Counterfactual sensitivity.** The same cell rendered at two settings of its main control (two values of x). Can the Decider say what changed, and which way? If not, the control does nothing visible.
5. **Caption against render.** Each claim in the caption ("the minimum sits at x = y", "the cached line grows by one per step") is checked against the screenshot. Where the claim is numeric, it is also checked against the data behind the chart. This catches 05 v2's log scale, where the caption claimed what the render hid.
6. **Earns its place.** Given the notebook's target and every cell's screenshot, which cells could be removed without losing anything the learner needs? A cell named repeatedly is a candidate to cut.

The Decider's accuracy is itself measured: against layer 1 where they overlap, against owner-labelled defects, and on deliberately broken controls (an overlap injected, an axis label removed, a caption made false). The battery is trusted only as far as it catches those.

**Gaming and accuracy (second review, Nov 20).** As built in the prototype, the author wrote the figure, the caption, the visual questions and their ground truth, and the reviewer saw captions. Partly a text-reading test. So:
- **Figure-only inputs.** Visual QA runs on a crop of the figure with caption, title and annotation text masked. Numbers printed inside the figure (07's region labels) count as text unless the question is about them.
- **Independent questions.** A second model writes the visual questions from the cell's intent and the facet, blind to the code.
- **Independent oracle.** Ground truth comes from a registered function executed by the harness and independent of the author's helpers. 07's caption reported "no bends" at weights (1, 1) and bias +1, where the output |x| + 1 still bends at 0, because caption and ground truth shared one buggy helper.
- **Harness-chosen states.** The harness, not the author, picks at least two control settings with different answers.
- **Baselines.** The communicative score is figure-only accuracy minus the accuracy of a no-image baseline and a caption-only baseline. Questions answerable from priors don't count.
- **Seeded defects in every run.** An injected overlap, a false caption and a swapped legend measure the reviewer's recall, which is logged with its verdicts.
- **Caption ablation.** Removing the caption must not change the figure-only answers.
- **The naive viewer is not naive:** the model already knows the concept. Treat its takeaway as a consistency check, not as evidence of what a learner would see.

**The review covers the state matrix, not one state.** The prototype reviewed only one state: correct answer auto-committed through a test hook, default values, closed accordions, the first tab, one palette, one width. TextCompare and the second StateViewer tab were never seen. Each plan carries an **interaction script**, and the review runs it:
- the locked state;
- correct, mutant, junk and free-text submissions through the real submission path (the synthetic-commit interface, not an environment flag);
- every disclosure opened and every tab visited;
- each control at its extremes and at every **pivotal value** the plan names (03's x = y = 0.275 was unreachable with a 0.01 step);
- a resize to phone width;
- each reviewed palette.

**More checks:**
- **Lint fails, durably.** Layer-1 findings, including width and centering, fail the round, except findings matched by a registered widget-specific rule (the known false positives: text inside collapsed `<details>`, FormulaAnimation's off-stage steps). Screenshot failures fail the run. Every screenshot and finding is recorded in a manifest keyed by code, runtime and state hashes, never in a shared folder where old files survive.
- **Plan conformance.** Each plan row maps to cell ids. Layer 3 compares the render with the plan, and drift needs a logged reason. The prototype's 04 plan promised linked point selection and a batch table, and the build shipped a slider.
- **Co-visibility.** From marimo's dataflow graph, a control and the outputs it drives must fit one viewport, or the control floats beside them (wigglystuff's FloatingPanel) or sits on the picture (ChartPuck drags points on a matplotlib chart in data coordinates).
- **Contrast acceptance.** Where a notebook contrasts two runs, both are visible at once, aligned, with the first divergence marked. Tabs fail this (the prototype's 05).
- **Mutant fidelity.** A mutant built from a learner's answer implements the answer as quoted. If it implements one interpretation, it says so. Projection and operation counts are asserted. (The prototype implemented only part of a quoted rule; the check must cover every operation in the source answer.)
- **Copy and theme lint.** A term list from the roster and contract vocabulary keeps internal words out of learner-facing text: "mutant", widget names like "CellTour", bare node symbols like "E" and "Q". No literal colours outside `ll.chart_theme()` (§5.2b).
- **One acceptance matrix** (a ruling; it replaces the earlier variants in §11.1, §11.6 and §14). Decided (owner, 2026-11-20): use an owner-set seed score cutoff; notebooks above it and through all mandatory checks are accepted without an individual owner verdict, and later owner verdicts move the cutoff. This is decided in principle; the value is owed by the owner. No automatic acceptance uses an invented cutoff. Every published notebook, help-only or not, passes layer 1, the dataflow rules and layer 2b. Layer 3 runs on sampled states for each help-only notebook; no layer is skipped. Until a route with image input exists (decision 4), notebooks of every kind publish only to the owner-side path. A failing notebook is never republished as help-only. Only the number of states and rounds reviewed may differ by kind, and the coverage manifest (§11.10) records which.
- **Reviewer accuracy** is measured against owner-labelled defects and clean controls, not against agreement with the lint.

**Presentation defaults** are recipe cards (§11.3) the author starts from:
- app width `full` for wide content, `medium` otherwise;
- outputs centered with `mo.center` or `mo.hstack(justify="center")`;
- widgets given explicit width and height that fit the cell (the prototype's FormulaAnimation clipped long TeX at its default 360 px height);
- one idea per cell, with a one-line caption above any widget saying what to look at.
- **Learner text is quoted verbatim in a code or text block, never as Markdown math.** Learner answers and workbench steps often hold half-written LaTeX (unbalanced `$`), which breaks rendering.
- **No hover-only information.** A tooltip doesn't exist on a phone, so anything a learner needs is visible without hovering.
- **Defaults make the point.** The starting state is non-degenerate (02's parallelogram collapsed at its first default) and every pivotal value is reachable (03's x = y).

### 11.6 Steering toward helpful visualizations
The owner's verdicts:
- **01 worked:** an anchored derivation, then a witness the learner makes.
- **05's side-by-side rule contrast worked,** but the difference between the two wasn't made explicit.
- **03's StateViewer writing replay was shoehorned;** the probability content had no distribution or curve.
- **02 and 06 were not illuminating:** 06 evaluated one point instead of showing the concept.

So the harness steers what to show, not only how to render it:

1. **A visual plan before code.** The author first writes, per notebook, a short plan:
   - the one idea the learner should see;
   - the contrast or change that reveals it (what varies, what stays fixed);
   - the representation that makes that contrast visible;
   - for each widget, the sentence saying what it reveals.

   A widget without such a sentence is not used. The plan is reviewed (layer 3's notebook questions, asked of the plan) before any cells are written, because fixing a plan is cheaper than fixing a notebook.
2. **Domain-native representations** as recipe guidance, not rules:
   - probability shows distributions and how a quantity varies as a parameter moves (a curve of P(collision) against x with its minimum at x = y; TangleDistribution; simulation beside formula);
   - linear algebra shows geometry (the plane warped by T, the parallelogram rule in the T-picture mapped back as a curved one);
   - neural-network concepts show functions over input space (each earlier ReLU's graph, their weighted sum, and where the later ReLU folds it), not a single evaluated point;
   - algorithms show the work that differs, aligned step by step (05's contrast as an aligned code diff plus a per-step work chart and the attention triangle each version computes).
3. **Make the contrast explicit.** When a notebook compares the learner's rule with the correct one:
   - the two run side by side on the same inputs, with the changed lines highlighted in the code;
   - the first point where they diverge is marked;
   - a caption says the difference in one sentence.
4. **Exemplars carry ratings.** The owner's verdicts are the first labels: 01 and 05's contrast cell positive; 03's replay, 02's flow and 06's single-point DAG negative, each with the reason. Retrieval (§11.3) prefers positively rated exemplars and shows the reason beside a negative one. A learner-facing "was this clear?" line under each notebook (learner text, not a rating button) keeps adding labels.
5. **A harness evaluation set.** The six prototype evaluation cases, with the owner's verdicts and reasons, are the first fixed eval set. A change to the authoring prompt, model, cards or reviewers is compared on it: layout findings, teaching-review findings, and the owner's pairwise preference between old and new versions where the owner gives one. Layer 3's judgments are checked against the owner's verdicts before they are trusted to reject notebooks.


**Root causes in the prototype** (the author's own postmortem, Nov 20). Most of the weak notebooks came from constraints the author imposed, not limits of the tools:
- **scope:** each notebook was built around one wrong answer, not the concept;
- **widgets first:** the roster was treated as a quota;
- **one skeleton:** header → tour → commit → reveals in every notebook;
- **no charting library;**
- **blind authoring:** no render was seen until the end;
- **one pass:** no alternatives compared;
- **diagnostic only:** every notebook was a repair;
- **thin context:** one attempt and an error label.

The review favoured richer context over a single-answer view. The rules below answer these causes.

6. **Specify goals and checks, never structure.** No prompt mandates a section order, a tour, a recap or a widget. The Nov 12 animation bake-off showed the same thing: a mandated title/beats/recap read as a slideshow, while the free-form prompt produced the strongest piece, one continuously transformed object. The commit gate stands only in front of the reveal it guards; a notebook may open with exploration, and may have no commit point at all (decision 3).
7. **The ladder of abstraction** (Bret Victor) is a recipe the author may choose, not a required structure: one concrete instance, then the same instance with a parameter swept, then a summary curve or picture across the sweep, then the general claim. It fits most explanations, and the plan says why when it isn't used. Structural diversity across notebooks is itself an eval-set measure, because the prototype's v2 still shared one skeleton built from shared helpers.
8. **Plan alternatives.** The author drafts several visual plans; how many is a logged draw (§11.1). A reviewer picks one by the §11.5 layer-3 questions asked of the plan, before any cell is written. The others are kept and may become randomized arms.
9. **Affordance cards.** Beside each widget's API card (§11.3) sits what it reveals, what it is for, and how it is misused. For example: "StateViewer reveals how state changes across discrete steps of an algorithm; not for replaying prose or sequences of text". Owner and learner verdicts add to the misuse lines.
10. **Components over raw widgets.** LearnLoop recipe components the author composes:
    - a contrast pair (two runs aligned, the diff highlighted, the first divergence marked, a one-line caption);
    - a ladder of abstraction;
    - simulation beside formula;
    - a fork animation;
    - the commit gate;
    - a linked view (select here, highlight there).

    Model-written components that pass verification join the library like widgets.
11. **Iterate with eyes.** The authoring job's budget covers several render-and-revise rounds: §11.5's layers 1–2 after every round, layer 3 when the lint is clean. Image input for the author and the reviewers is a prerequisite for this loop, not an extra (decision 4).

### 11.7 The author's read API: LearnLoop as a source the author can query
The author pulls context instead of receiving one large prompt. The teacher already has most of this API: `read_source`, `find_sources`, `find_practice`, `read_history`, `read_note` (`teacher/contracts.py` `ACTIONS`). The authoring job gets the same read actions, with policy from the caller as in `caller_for`, plus:
- `read_evidence(facet)`: the evidence packet for the facet (`spec_evidence_packets_v1.md`): attempt facts, claims and the observations behind them, across every attempt, not only the one being repaired;
- `read_concept(concept)`: prerequisites and neighbours from the concept graph;
- `read_figure(span)`: a source figure's crop (`figures/grounding.py` `crop_image`);
- `read_misconceptions(facet)`: registry entries, consistent answers and mutant provenance;
- `read_exposure(facet)`: what the learner has already been shown, so the notebook doesn't repeat it;
- `read_topic_notebook(concept)`: the topic notebook so far (§9.9), and earlier lesson visuals;
- `read_workbench(session)`: the learner's own steps and verdicts.

More reads that the reviews found high-value:
- `read_verdicts(concept | idiom)`: earlier verdicts on cells, with reasons (§11.8);
- `read_interaction(notebook)`: widgets touched or ignored, dwell, disclosures opened, where the learner stopped;
- `read_questions(facet)`: earlier `learner_question`s with their labels;
- **serving context:** device, viewport, touch or pointer, palette, runtime budget, minutes available, goal date. A "hover to see p" fails on a phone;
- **reserved surfaces:** which surfaces upcoming cold items use, so a notebook doesn't spend them;
- **the learner's own notation and wording,** from their answers and the source;
- **the entry intent verbatim,** and where it came from (§9.11 resolves a query to concepts; the words are kept too);
- **reading position:** what has been read and what comes next;
- **successful contrasting attempts** on the facet, and alternative explanations of the errors;
- **pending edits and ownership** of cells in the target notebook;
- **the job's own history:** rejected plans and earlier rounds' findings.

The plan cites which evidence supports its scope and states what remains uncertain. 06's "myopic" verdict came from a plan scoped to one answer without saying why.

Every read is logged as part of what the model was shown (EP2). Reads are filtered by the Reader's retrieval-permission table: no held-out material, and no key or expected answer of an open cold item.

### 11.8 Verdicts as data: closing the feedback loop
- **A verdict record** covers one cell or one notebook:
  - the exact artifact, cell and state hash;
  - the reviewer's original words, reason and reviewer identity (owner, learner, a model reviewer);
  - the plan row and harness version, and the idioms and widgets used;
  - a supersession link.

  It is versioned and append-only.
- **Where verdicts go:**
  - accepted lessons are compiled, with provenance, into affordance-card misuse lines (§11.6 item 9) and retrieval annotations (§11.3);
  - they rank exemplars;
  - they calibrate the teaching reviewer.
- **The owner's review console** is itself a marimo app over the per-cell screenshots and states. Verdicts are typed or spoken; wigglystuff's AnnotationWidget takes keyboard and speech actions.
- **The eval set grows beyond the six prototype cases,** which become development regressions: untouched cases spanning exploration, textbook explanation, non-computable subjects and topic-notebook extension, so prompts and reviewers don't overfit six demonstrations. The prototype's 01 is a labelled negative on one point: it shows the future cold question and calls a same-generator seed "standalone cold".

### 11.9 Cost estimates (from notebook 07's measured sizes, Nov 20)
These are estimates from the prototype's artifacts, not from a production run. The prototype session's own token use is not a measure: it was a conversation.

**Measured sizes:**
- the generated notebook: 34 KB, about 9–10k tokens;
- the cells a model must emit: about 25 KB, about 7–8k tokens;
- evidence-packet context is budgeted below; private attempt and item sizes are omitted;
- 19 cell screenshots: about 500 image tokens each by Claude's size rule (other providers count images differently, up to about 750–1,100).

**Authoring one notebook:**

| Part | Tokens |
|---|---|
| Fixed prompt: rules, SDK, contract, card index | about 5–8k input |
| Context: evidence packet, concept graph, sources | about 8–12k input |
| Cards and example slices read on demand | about 8–12k input |
| Plans (2–3 alternatives plus the choice) | about 2k output |
| The cells | about 8k output |
| Each fix round (findings in, cell edits out) | about 2–3k input plus the context; about 2–3k output |

- 07 took about 12 model calls: plan, author, about four execution and structure fixes, and three review rounds. Each re-sends about 35–45k tokens of context.
- **Total input: about 0.4–0.6M tokens per notebook,** mostly the same prefix every call, so prompt caching cuts the real cost several-fold. **Total output: about 25–35k tokens,** or about 50–80k with a reasoning model's thinking tokens.
- A simpler notebook that passes in one round: about 150–250k input and 15–30k output.
- On the plan transport this counts against the ChatGPT subscription's usage limits, not a per-token bill. Per-token prices were not looked up for this estimate.
- Also local compute: about a minute of CPU per state per notebook for headless execution and lint, and a few minutes of wall time in total, which is why prebuilding matters (§9.12).

**Decider review (§11.5 layer 2b):**
- **Per cell:** one screenshot plus the question battery (about 400 tokens) in, an answer of about 150–300 tokens out. About **1–1.5k input and 0.2–0.3k output per cell.**
- **Per state of 07:** about 19 cells, of which about 8 visual cells get the full semantic battery: about 20–25k input and 4–5k output.
- **A full review:** three states (locked, correct, mutant) times two to three rounds, re-reviewing only changed cells after round 1. That is **about 50–80k input and 10–15k output per notebook,** plus a few small second calls for the takeaway judge. Each palette reviewed (§5.2b) adds about one state's worth.
- **Agent overhead:** the prototype's review agents used 57–79k tokens per round, mostly agent-framework overhead. A direct call with only the screenshot and questions is about a tenth of that.
- **On a cheap Decider-tier model, review costs a fraction of authoring.** The binding constraint is a route with image input (decision 4), not money.

**What to measure in production** (§11.1's cost accounting): tokens and seconds per stage and round, cache hit rate, rounds to convergence, and cost per accepted cell.

### 11.10 More harness machinery (second review, Nov 20)
- **An executable acceptance manifest.** Each notebook revision has a manifest covering:
  - every state × layer × round of §11.5's matrix;
  - the independent oracle results;
  - screenshot completeness;
  - the publication decision.

  Missing cells fail the run. It includes regressions for retries, crashes, stale revisions and synthetic-evidence contamination. Synthetic commits go through the form, freeze and classify path; the prototype seeded state directly, which the spec forbids.
- **Incremental verification by render hash.** After a change, re-review only cells whose render changed, plus their dataflow dependents, in every state. The cache identity includes reviewer prompt and model, theme, oracle version and the pinned packages.
- **Versioned widget promotion with quarantine.** Auto-join (decision 2) stands. Each promoted widget version has an immutable dependency manifest and reverse-dependency links. A version that later fails is quarantined, and the notebooks using it fall back to their last verified revisions, so one bad widget can't poison many notebooks.
- **A storyboard round.** Each alternative plan renders only its key figure, and the reviewer and owner choose among pictures, not plan text.
- **Misconception-reader ablation (layer 3b).** A model holding each mutant belief walks the notebook through the synthetic-commit path. A cell earns its place only if removing it stops that reader's transfer answer from changing.
- **Pin-bump regression.** Any marimo or wigglystuff upgrade reruns the eval set.
- **Verification never imports builders.** The prototype's builders rewrote notebooks on import. Verification reads artifacts only.
- **Routes.** The Decider provider (`ai/providers/decider.py`) serves only `DECISIONS`, and `FigureRoute.reads_images()` only reports its client's capability, so the visual reviewer needs its own route, schema, admission and "unavailable" outcome. Readability questions see screenshots only. Semantic and leakage reviewers may also see the question, the key and the context: only grading is blind.
- **Where the eval set lives.** The eval set and the exemplar library hold learner answers, so they live outside the public tip, like the vaults.
- **Cost per opened notebook** is the reported unit (§11.9), since a notebook never opened costs as much as one used.

## 12. Measurement and logging

### 12.1 Minimum logging contract (from the first slice that has a commit)
1. **Instance:** `notebook_instance_id`, `activity_hash`, `key_hash`, `generator_hash`, `seed`, `sdk_contract_version`, `runtime_lock_hash`, authoring model and prompt version, `mutant_set_json` (name, provenance, code hash), `dep_graph_hash`, device, surface.
2. **Mask candidates:** `candidate_masks_json` with scores, `design`, `policy_version`, `rng_seed`, `propensity`, `propensity_kind`, `selection_purpose`.
3. **Commit (one per attempt):** `commit_id → attempt_id`, `cell_id`, `mask_type`, raw answer with unit and precision, raw confidence, `correct_value`, `mutant_outputs_json` (value and distance per mutant), `match_set`, `first_error_step`, `correct_prefix_len`, `checker_kind`/`checker_version`, `path_id`.
4. **Commit context:** `visible_state_hash`, derivability verdict, `prior_exposures_json` (ordered reveal units, teacher diffs in force, authorship of executed lines), `cue_condition`, `coldness_class` with reason, frozen-at (server-ordered before any reveal).
5. **Timing:** `render_ready_at`, `first_interaction_at`, `commit_at`, focus/visibility intervals, `runtime_warm`; `active_seconds` (RE0) excludes render and runtime lag.
6. **Reveal decision:** eligible set, probabilities, drawn unit, `propensity`, `propensity_kind`, `requested_by` (router / teacher / learner), `after_commit_id`, `shown_at`, dwell, `reveal_events` amount per affected item, and a **pre-registered `outcome_target_json`** (concept, surface, delay window).
7. **Stop coin** per commit with its propensity.
8. **Non-events:** masks offered but skipped, notebook abandonment, rejected draws.
9. **Teacher diffs:** kept / edited / reverted / ignored, linked to the next cold attempt.
- Drag trajectories are logged as raw events (device-normalised) and not modelled until an ablation shows value; process features generalise poorly (Lane C).

### 12.2 Where it lives
- Reveal units reuse `help_assists` (`options_json`, `probabilities_json`, `drawn_option_json`, `propensity`, `seed`, `rivals_json`, `predicted_answers_json`, `eig_nats`) with new `assist_kind` / `hint_kind` values.
- `reveal_events.source_kind` gains `notebook_reveal` and `teacher_edit` (rebuild pattern of migration 179); `router_decisions.decision_kind` gains `mask_draw`, `mask_dose` and `reveal_unit` (rebuild pattern of migration 236).
- **Instances and commits use the activity substrate** (§7.3), not new tables: an instance is an `activity_administrations` row; each commit is an `activity_observations` row with its `measurement_events` (`response_appended`, `raw_grade_appended`, `grade_classified`, `grade_interpreted`: the kinds attempts already write). The commit's extra fields (§12.1 items 3–5) go in the measurement payload under a versioned schema.
- New receipt tables only where nothing fits: `notebook_patch_events` (actor-tagged edits, §9.3) and `mask_separability` (§8.1), RAW_LEDGER or RECEIPT in `table_roles.py`.
- **The substrate write contract.** `activity_observations` (migration 065) has no observation-kind or payload column. `substrate/activities.py` appends observations without a payload and derives eligibility from purpose and feedback condition. So:
  - notebook observations carry a versioned envelope in `measurement_events.payload_json`, registered by kind;
  - the transaction boundary, the link to `practice_attempts` and what readers that don't know the kind do with it are specified before the first write.
- **Concept-level exposure needs its own record.** `reveal_events.practice_item_id` is NOT NULL (migration 154), so exposure to a notebook section that belongs to no item needs a nullable item or a sibling table.
- **Verdict storage** (§11.8) is an append-only verdicts table plus supersession events, with indexes by artifact, cell and idiom. Card compilation is rebuildable from it.
- **Propensities.** `router_decisions.propensity_kind` (migration 236) allows only `exact`, `deterministic`, `none` and `not_served`. `estimated` needs the CHECK widened, with the estimation method and its uncertainty recorded, and every reader updated. Learner requests carry `none`, never a policy propensity.
- Migrations take the next free number when each stage lands. The receipts change no decision, so they need no successor tag; the first stage that reads them for a decision does.

### 12.3 Evaluation at n = 1
- **Power first:** before claiming any activity effect, compute from existing attempt variance how many `standalone_cold` retries per arm are needed to detect the effect sizes in the literature (dynamic visualisations g ≈ 0.23; prequestions on questioned content g ≈ 0.54). If that exceeds a year of volume, the report says the router will not learn the difference and every claim is observational.
- **Pool value on contract features,** with shrinkage: commit present, response generated vs selected, explanation required, mutant-separating, declared target facet. No per-notebook values.
- **Standing arm:** a plain text item on the same facet; the comparison is cold gain per minute.
- **What is identifiable:** a within-learner average effect of reveal class on the next `standalone_cold` outcome, pooled across concepts. One primary randomized reveal per (notebook, concept); later reveals are sequential treatments with full exposure history. Per-misconception repair effects are not claimed.
- **Emission ablation** (Pipeline Augmentation Plan §D) is the acceptance test for each new channel: it earns credit only for unique predictive or decision gain in replay.
- Calibration claims are gated on posterior interval width, not a fixed count.

<a id="124-one-observation-stream-across-surfaces-proposal-depends-on-spec_evidence_packets_v1md"></a>
### 12.4 One observation stream across surfaces (depends on `spec_evidence_packets_v1.md`)
Decided (owner, 2026-11-20): adopt one observation registry across surfaces, learned per-kind weights and evidence packets as the read side.

Today each surface keeps its own record, read by its own consumers:
- **Attempts** write the activity substrate and feed the grader, diagnoser, learner state, scheduling and AD.
- **Reader workbench steps** (`workbench_steps`, append-only) feed hints. No learner model reads that process today.
- **Figure predictions** (`figure_predictions`) go to a formative queue.
- **Lesson checks** feed `lesson_weight`.
- **Placement quick checks** have their own tables.
- **Confidence taps** reach the router card, diagnoser, hint writer and tutor.
- **Help and reveals** (`help_assists`, `reveal_events`) feed assistance accounting.

Notebook commits would otherwise be one more silo. The adopted design has three parts:

1. **Write side: one stream.** Every learner emission that says something about knowledge becomes an `activity_observations` row under an administration, with an observation kind from one registry: attempt, masked commit, prediction (figure or notebook), `approach` (plan-only), `learner_question` (asked about a cell, §9.10), teach-back turn, lesson check, quick check, confidence, stuck press, self-explanation line, diff uptake. Each observation carries:
   - the **facts** around it (EP Part A's replacement for "assisted": which help, which reveals, first exposure, time);
   - its **coldness class** (§7.4) and cue condition;
   - its **raw response** under a versioned payload.

   Process events (drags, writing steps) stay as raw events linked to the observation, not as observations themselves.
2. **Read side: evidence packets.** EP's packet is the one view the diagnoser, the Decider, the action model and the teacher read. A hypothesis's claim card cites observations across surfaces: a figure prediction, a masked commit and a teach-back line can all support or weaken the same claim.
3. **Update side: a learned weight per observation kind.** `learner/lesson_weight.py` already learns a lesson check's evidential mass `m = σ(η)` from the next qualifying cold outcome on an unseen item. That generalizes to every kind:
   - `m_kind = σ(η_kind + offsets)`, starting from a seeded prior and learned the same way;
   - an `approach` statement, an in-notebook commit or a figure prediction earns the mass its record of predicting later cold answers supports, and no more;
   - certification stays with `standalone_cold` observations.

   This replaces per-surface special cases with one rule, and it is what lets plan-only and "describe your approach" reps feed `method_selection` without pretending to be solved problems.

This is larger than the notebook work and touches persisted meaning across surfaces, so activation follows the playbook. Notebook commits and work-question answers use the shared substrate (§12.2). Decided (owner, 2026-11-20): work-question answers use path A, one observation of kind `work_question` per answer; their logit-mass prior is N(0, 1), like `learner/lesson_weight.py`. They remain in-context evidence and never certify.

### 12.5 How the data feeds back into learning about the learner
| Signal from notebooks | Where it goes | What it changes |
|---|---|---|
| Commits (choices, numbers, distributions, drawn curves, code by behaviour) | activity substrate → blind grader → diagnoser | claims in the evidence packet; misconception prevalence; AD's ability at that feature point, at the learned in-context weight (§12.4) |
| A later `standalone_cold` answer | the same, at full weight | certification, AD, and the learned value of the notebook and contract features that preceded it |
| "Ask about this" questions, "not sure, because…" text, work-question replies | the diagnoser and evidence-packet claims | new hypotheses about what the learner doesn't follow; the teaching review's evidence about confusing cells |
| Teacher-diff uptake, dwell, untouched cells, tours started, where the learner stopped | raw events, readable through `read_interaction` (§11.7) | the author's next plan (which representations work for this learner); cells that don't earn their place |
| Assumption probes and witnesses (§7.7) | AD at far-transfer points; the misconception registry | transfer readiness; which assumptions the learner over- or under-weights |
| Verdicts on cells (owner or learner) | verdict records (§11.8) | exemplar ranking, affordance-card misuse lines, reviewer calibration |
| Accepting or declining offers; opens from the shelf | the existing acceptance model (`router/lesson_suggestions.py`) | when and how notebooks are offered (§9.13) |

**Limits at n = 1:** most per-kind weights and effects stay wide for months, and the design rates and the power calculation (§12.3) keep that visible in reports. Drag paths and timing are logged raw and modelled only after an emission ablation shows they add something.

## 13. What feeds which model, and when
| Consumer | Feed | When |
|---|---|---|
| Misconception registry | human commits only, by source; separability as instrument validity | after NA3's successor tag |
| Diagnoser | answer vectors, first error step, "not sure, because…" text, confidence | NA3 |
| Router | contract features (not embeddings at first), learned value pooled | after enough `standalone_cold` volume |
| EVSI | tier-0 likelihoods only after promotion | later |
| Repair-effect model | reveal episodes with pre-registered targets | logged from NA2; estimated when ESS allows |
| Encoders and fine-tunes | mutant runs as pretraining only, evaluated on human commits | later |
| Stopping logic | commit-level stop coins | NA2 onward |

## 14. Guardrails: relaxed and kept (owner, Nov 20)

**Relaxed:**
- Decided (owner, 2026-11-20): help-only notebooks and displays (no commit points) are activities logged as help and exposure, never evidence. They skip the commit-specific leakage-free proof; schema, KaTeX, maths and held-out text checks remain, and the acceptance matrix (§11.5) keeps visual review and publication checks.
- Help-only notebooks review fewer states and rounds; no layer is skipped (the acceptance matrix, §11.5).
- Practice items keep coincident or near-slip draws (logged and down-weighted by the likelihood); only probes reject them.
- The greedy "no two masks on one path" rule is dropped once the joint likelihood exists.
- Widgets, model-written or owner-written, join the library automatically on passing §11.2's checks; no owner review (owner, Nov 20).
- No fixed "~50 ratings" calibration floor.
- Displays may be shown without a prediction; a prediction is a candidate, not a gate.
- **Authoring is not boxed in:** no mandated notebook structure or widget quota; the commit gate guards only its reveal; the native toolbox is broad (§5.2a); lesson visuals arrive as notebooks, not only the narrow in-turn tiers; the authoring budget allows several render-and-revise rounds.

**Kept:**
- Commit frozen and logged before any reveal or downstream output; host-owned submission.
- The key and cold-eligible masked values never in the client, planner, teacher context or grader history.
- The blind grader.
- One commit = one attempt with a joint likelihood.
- Propensities on every draw, including deterministic and non-randomized ones.
- The append-only reveal ledger and authorship records; non-learner executed lines make a commit assisted.
- Synthetic and execution answers never become evidence, human sensitivity/specificity or router value; tier-0 likelihoods never drive live EVSI unpromoted.
- Execution receipts; coldness classes enforced at read time.
- Held-out material checks on every authored string.

## 15. Stages and placement

| Stage | What | Persisted meaning? |
|---|---|---|
| **NA0** | Spikes: packaging and CSP; browser control; runtime comparison; authoring yield; non-computable activities | No |
| **NA1** | Display tier and live Show me figures (help-only, optional prediction) | No |
| **NA2** | Contract, SDK, host commit, receipts (§12.1), in-notebook commits | No (receipts only) |
| **NA3** | Masked-cell items in the substrate; mutants with the noise model; diagnosis | Yes |
| **NA4** | Teacher and repair verbs; diffs and authorship; scratch; staged repair | Yes (assistance accounting) |
| **NA5** | Quests, projects and the coding module on notebooks | Yes |
| **NA6** | Phone | No |

**Tracks and persisted meaning (second review, Nov 20; replaces the stages table where they disagree):**
- **Track H: an owner-side harness, with no app code and no persisted meaning.** Cards and the example index, the cell writer, `learnloop notebook check`, the review layers and acceptance manifest, the eval set, and the review console. Useful at once, and it de-risks everything else. H1 has landed as the structure-only checker in `src/learnloop/notebook_authoring/`, with the optional `notebook` extra.
  - **H3: capability cards.** Generate cards from installed packages and maintain the example index (§11.3, §11.3b). **Acceptance:** every exported widget has a generated card or an explicit exclusion; extraction gaps have one declarative entry per tool; a normal pin bump updates the lock, licence notice and parser version check and regenerates cards and examples.
- **Track S0: asked-for, help-only notebooks** opened from Today's shelf or the facet well, logging only opens, dwell and questions. Its purpose is to learn whether notebooks get opened at all. Decision 4 selects OpenRouter image input; its owner-supplied profile, verified price and per-run cap still gate review.
- **The runtime track** (NA0.2 as a gate, then NA2 onward) starts only after S0 shows notebooks are used.
- **Correction to the table above:** NA1 and NA2 are not "receipts only". They write assistance and reveals, grade commits and activate stopping logic, so each splits into passive collection (no decision reads it) and activation (a successor tag, an `UPGRADES` row, table roles and rebuild ownership, defaults and identity decisions, predecessor replay and upgrade tests, per `docs/algorithm-change-playbook.md`). An experiment's "none" arm is not a predecessor implementation. NA6 changes device eligibility, which is persisted meaning too.
- **Dependencies on unbuilt specs:** evidence packets, the Decider reveal judgment, learner-input-after-miss and the workbench adapter. RE0's capture is built (`docs/reviews/re0-capture.md`). File and line references here will move under the refactor.

### NA0: spikes (in this order)
Decided (owner, 2026-11-20): the owner supplies exports or backup-API copies outside the checkout, excluding held-out exam material; workers read those exports, never live vaults, and tracked result records contain aggregate counts and rates only. This is decided in principle; the value is owed by the owner: the exports for the six evaluation cases, twenty authoring requests across three vaults and four non-computable cases. The owner runs the power exporter on backup copies and supplies its aggregate output. These are planned sample sizes, not reported vault counts.

Decided (owner, 2026-11-20): measure the packaged desktop app in a supervised session now; phone measurements and budgets wait for NA6.

1. **Packaging and CSP:** an audited asset manifest; the pinned display bundle boots with networking disabled under the production Tauri CSP (opaque-origin frame, module workers, MIME types, fonts) without granting same-origin access; the notebook webview reaches only its own localhost server.
2. **Server control under the sandbox:** a marimo server in bubblewrap with no network; observe → edit → run → inspect → save/reload from the sidecar through the server's endpoints; list the upstream interfaces relied on and whether any are private.
3. **Runtime budgets:** in the packaged desktop app on WebKitGTK, with the owner present: time to interactive, memory per session, sustained manipulation, idle shutdown and resume. Set desktop budgets from these measurements. Phone measurements over the tailnet, phone budgets and the static fallback for no connection are completed in NA6.
4. **Authoring yield:** build the example index here, alongside H3, then run 20 activities from owner-supplied exports spanning three vaults through the harness; record pass rate per check, spend and minutes.
5. **Non-computable activities:** two hand-authored activities each for a law and an arXiv-style vault against the draft SDK; record which contract parts are empty; finalise §6.4.
6. **Power calculation** (§12.3) from aggregate output the owner supplies by running the exporter on backup copies.

### NA1: display tier and live figures
- `DisplaySpecV1`, the widget subset adapters with typed alternatives and static fallbacks, the sealed display frame, the `live` figure tier with parameterisation and fidelity checks, one optional prediction through `figures/predictions.py`, exposure rows.
- Acceptance: a probability-vault figure block becomes a live TangleDistribution whose start state matches the printed parameters (or is labelled illustrative); works offline; parameter-map check passes; no network in the frame.

### NA2: contract and commit
- SDK, `pf-activity-v1`, host commit state machine, receipts tables, logging contract, in-notebook commits graded blind; coldness classes; derivability check; contract drive on the native server.
- Acceptance: integrity tests (races, retries, forged messages, stale outputs, downstream hold) pass; a commit never precedes its log row; the grader's input has no history.

### NA3: masked items and diagnosis
- New `practice_mode`s and hooks; per-draw `shared_stimulus_id`; mask selection with propensities; joint likelihood with learned ε and kernel; `mask_separability`; human-only discrimination ledger; mutant seeding from error events; the held-out readout test (readout hidden until it passes).
- Acceptance: the 10-vs-1,000-seed invariance test; duplicating a mask on one path leaves the posterior unchanged; `standalone_cold` is the only class feeding R_cold; replay and upgrade tests under the playbook.

### NA4: teacher and repair
- Teacher actions in all eight turn-schema variants (§9.2); durable authoring jobs; diffs, patch events, merges and revert; scratch worker; staged repair with randomized stage-3 arms and the reteaching comparison; "debug the interpreter".
- Acceptance: every schema combination tested; crash recovery of jobs; assistance follows executed dependencies; a held downstream rerun never reveals an open mask.

### NA5: quests, projects, coding
- Quest notebooks in the vault, project notebooks, the coding module (ask-before-code enforced by a validator on proposed diffs), own-work masked items, `projects/probes.py` joined to learner state (decided, owner, 2026-11-20).

### NA6: phone
- Display tier first (typed alternatives and static fallbacks), then notebooks served from the desktop's marimo server over the tailnet. Measure the phone with the owner present in NA6 and set its budgets here; NA0.3 measures the desktop only.

**Placement:** Decided (owner, 2026-11-20): track H and NA0 start beside the queue. After the refactor and UX stages, the order is evidence packets, AD memory, reveal adjudication, WQ teach-back, projects-as-goal, notebook activities, then teacher v2 (TE5 to TE10). NA2's passive receipts stay in that order; they were not authorized to land early.

<a id="16-owner-decisions-open"></a>
## 16. Owner decisions
1. **Runtime:** Decided (owner, 2026-11-20): native first, a sandboxed marimo server per session; Pyodide later only if needed (§5.1).
2. **Model-written widgets:** Decided (owner, 2026-11-20): join the library automatically once they pass §11.2's checks.
3. **Help-only activities:** Decided (owner, 2026-11-20): notebooks and displays without commits are logged as help and exposure, never evidence; fewer states and rounds, no review layer skipped (§14).
4. **Image input:** Decided (owner, 2026-11-20): route visual review and figure fidelity to an OpenRouter profile behind the per-action offer; allow an independent checking route when author and checker would otherwise be the same model. Owner's words (verbatim): "add it to the route visual review/plan transport to an OpenRouter profile". **Orchestrator's reading:** image input is not added to the plan transport. The route is decided in principle; the value is owed by the owner: the named image-capable profile, verified price and per-run cap. Paid runs require the owner's OK.
5. **Name:** Decided (owner, 2026-11-20): notebooks. Owner's note (verbatim): "they should be called notebooks".
6. **Project probes:** Decided (owner, 2026-11-20): join `projects/probes.py` answers to learner state in NA5.
7. **Placement:** Decided (owner, 2026-11-20): "start H and NA0 beside the queue". The remaining notebook stages follow projects-as-goal and precede teacher v2 (TE5 to TE10, §15); NA2's passive receipts stay in queue order.
8. **Teacher edits:** Decided (owner, 2026-11-20): teacher and repair edits apply with highlighted diffs and §9.3's measurements. Edits to the learner's solution code in a coding dialog remain proposed diffs under ask-before-code.
9. **One observation stream:** Decided (owner, 2026-11-20): adopt the cross-surface registry and learned per-kind weights, with evidence packets as the read side (§12.4), so new surfaces do not add evidence silos. Work questions use path A and a logit-mass prior of N(0, 1).
10. **Example index:** Decided (owner, 2026-11-20): build it in NA0 alongside track H, so owner-side authoring can use it immediately (§11.3).
11. **Implementation teach-back:** Decided (owner, 2026-11-20): use the one service in `spec_implementation_teachback_v1.md`; fold `ll.explain` and the "why this change?" line into it (§9.8).
12. **Manim:** Decided (owner, 2026-11-20): retire the rich `manim` tier and `content/authoring/concept_animation.py` when notebooks cover their Reader and lesson uses; extract the sandbox helpers first (§9.11). Owner's note (verbatim): "Manim animations can be anywidgets, so they are superseded by marimo/wigglystuff notebooks and cells". One animation path remains.
13. **Theme:** Decided (owner, 2026-11-20): variables only, generated from LearnLoop's tokens, with no per-component selectors; keep third-party licence notices (§5.2b). This reduces dependence on marimo's internal class names.
14. **Assumption-surgery depth envelope:** Decided (owner, 2026-11-20): a generated default list per topic that the learner can edit and review (§7.7). The separate `perturbation` feature remains decided because AD's cumulative transfer coding cannot express it independently.
15. **Acceptance seed:** Decided (owner, 2026-11-20): set a seed cutoff, accept above it after mandatory checks, then learn from owner verdicts (§11.5); decided in principle; the value is owed by the owner.
16. **Private-data spikes:** Decided (owner, 2026-11-20): owner-supplied exports outside the checkout, aggregate counts and rates only in tracked records, and the owner runs the power exporter on backup copies (§15, NA0); decided in principle; the value is owed by the owner: the exports and aggregate output.
17. **App and phone measurements:** Decided (owner, 2026-11-20): supervised packaged-desktop measurements now; phone measurements and budgets in NA6 (§15).

## 17. Lessons from the Nov 20 prototype
Prototype marimo notebooks were built from private exports (kept outside the repo because they hold learner answers), checked headlessly with the held cells run, exported to WebAssembly and loaded in Chromium. What changed in this spec because of it: §4.2 widget gaps; §5.1 what the learner sees; §6.2 no format-style templates and the `approach` response kind; §7.3 and §12.2 the activity substrate; §11.1 cells not files, marimo's parser, context-assembly fallback, executed numbers; §11.2 every reveal state, runtime-only verification, the reveal audit, measured costs; §11.3 sources from the installed package and example slices; §12.4 one observation stream. After the owner's review of the six notebooks (Nov 20): §11.5 presentation and teaching review, §11.6 steering toward helpful visualizations and its root-cause list, §11.7 the author's read API, §9.9 topic notebooks, §5.2a the broad toolbox. Also: WebAssembly exports need the dependencies declared in a PEP 723 header, or Pyodide fails with `ModuleNotFoundError: wigglystuff`.

**The full harness run on a new notebook (07, Nov 20; record kept with the private prototype outside the repository).** A notebook with multiple commit points, behavioural code classification, an anchored work question, and transfer items previewed as practice items. Private history and answer text are omitted. It went through:
- planning with alternatives;
- execution in the locked, correct and mutant states;
- the layout lint;
- three rounds of a blind Decider (Haiku, screenshots only).

Results:
- **A partial run, not the full matrix.** All verdict records are in the correct state. The mutant and locked screenshots predate the fixes. Synthetic commits seeded state directly instead of going through the submission path. Junk and free-text commits, opened tours and disclosures, control extremes, phone width, a second palette, the independent reference, the dataflow reveal rule and seeded defects were not run. Screenshots included captions, and in round 1 a count was read from the caption. The second review also found real bugs on paths never exercised: free text overrode a selected choice; a tour title and a header quote gave the answer away before a commit; g1 and g2 options named the mutant's reason; previewed items were labelled `standalone_cold`; and the bends caption was wrong at bias +1.
- **Visual QA against computed ground truth separated good figures from poor ones,** as far as it went. Round 1 missed 2 of 7 questions, and both misses were real defects: an occluded curve, and region colours too alike to count. Round 2 caught a regression introduced by a fix (brighter fills hid the zero line). After round 3 every ground-truth question was answered correctly from the picture alone.
- **The UX battery found real defects** the lint did not: unlabelled axes, a clipped curve, a legend over the plot, internal jargon including a spec id, and a co-visibility failure ("drag a₁…" with the controls in another cell).
- **Found by screenshot but not by the Decider:** `mo.center` shrinks anywidgets (a FormulaAnimation then scrolled sideways), and KaTeX subscripts render flattened inside FormulaAnimation (open).
- **Needs widget-aware rules:** two lint false positives, from collapsed `<details>` text and FormulaAnimation's hidden off-stage steps.

## 18. marimo and wigglystuff elsewhere in LearnLoop (after the shared host works)
Ranked by the Fable and Astra reviews (Nov 20), value against effort:

| Surface | Insert | Value / effort; where |
|---|---|---|
| Reader | A manipulable source figure linked to its passage, with "Ask about this" | High / M; `screens/reader/figures/FigureInline.tsx` |
| Feedback | The learner's rule against the reference, run side by side at the first divergence; `mo.image_compare` or TextCompare of answer against rubric quote | High / M; `screens/feedback/CompareMethods.tsx` |
| Predictions everywhere | **Drawn predictions** (CurveEditor, SplineDraw, Paint) before a reveal: the `curve` response kind (§6.1) | High / M |
| Questions and dialogs | `mo.ui.chat` (custom Python model function, streaming, history as its value) for "Ask about this" threads, the simulated novice (§9.7) and work questions, with the sidecar tutor behind it | High / S |
| Lessons | Reopen and extend the same concept visualization (topic notebooks, §9.9) | High / M; `screens/LessonScreen.tsx` |
| Facet well and concept graph | A natural-language notebook request with the resolved target shown (§9.11); learner-drawn prerequisite maps (GraphWidget, EdgeDraw) as an emission compared with the graph | High / M; `components/FacetInspector.tsx` |
| Coding and DSA | Failing-test trace (`LiveEdit.from_pytest`), state comparison, anchored work questions, proposed solution edits | High / H; `screens/PracticeScreen.tsx` plus a notebook adapter |
| Phone | The slides layout (slide order follows cell order) for lessons; resume saved state; static trace frames. NA6 also compares one server per session with `create_asgi_app` serving many run-mode notebooks from one process | Medium / M; `apps/learnloop-mobile/src/read/ReaderScreen.tsx` |
| Owner analysis | `mo.ui.data_explorer` over `learnloop data-capture report` and the harness eval set | Medium / S |
| Voice teach-back | `mo.ui.microphone` or speech-to-text into text (WebKitGTK support unverified) | Medium / M |

**More placements (Nov 20):**
- **Reader: assumption toggles on theorems** (§7.7). Probably the highest-value new use.
- **Quick checks and placement: distribution-valued answers.** A TangleDistribution answer scored by log score carries more information per item than a single number, so placement converges faster (`K_useful`).
- **Review cards: one-cell returns** (§9.13).
- **Photos of handwritten work** (`mo.ui.file` or WebcamCapture), through OCR into the symbolic step check (RW2b), for a repair animation from work done on paper.
- **Projects and big codebases:** ModuleTreeWidget, ApiDoc, TraceView, `LiveEdit.from_pytest` and in-notebook pytest cells.
- **Exam prep:** the exam digest (§9.13).
- **Phone:** slides over verified frames, with typed predictions.

Not adopted: marimo islands. They run reactive code on Pyodide and are an early feature, which conflicts with native-first.

## 19. Not in this spec
- ManimWeb with model-written scenes (only trusted templates, later).
- Per-misconception repair-effect claims at n = 1.
- Router values learned from contract embeddings before `standalone_cold` volume exists.
- Fine-tuning on mutant runs as anything but pretraining.
- A general notebook editor; notebook completion or dialog length as a success metric.
