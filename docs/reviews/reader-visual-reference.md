# Reader workbench v2: the visual reference and what it found (2026-11-23)

The owner, Nov 23: "take screenshots of the mockup including colors then use it to verify". The workbench's goal is
the mockup, rebuilt on real LearnLoop functionality (spec `docs/specs/spec_reader_workbench_v2.md` §4). This record
says how the reference was made, how a frontend worker re-checks a stage against it, and what differs today in the
landed stages (RD1 desks, RD2 overview, RD3 companion and search, RD4 pads). Nothing product-side changed in this
step.

## 1. The reference (private)

- **Where.** The private reference directory, outside every checkout, mode 700. It holds one PNG and one JSON per
  state, viewport and mockup variant, `index.json` (every capture, whether its deep link applied, the hosts refused),
  the capture script, and the comparison output (`compare/`). Nothing from it is in the repository: the mockup is
  built from the owner's vaults and shows book text. Ask the orchestrator for its location.
- **What.** Every deep link of spec §4.1's table, in both mockup variants (`arxiv_v2`, and `arxiv_v2_goal`, which
  adds the goal fork), at the mockup's design viewport (1440 × 900) and the laptop (1280 × 800). The goal links only
  in the goal variant. The Teacher lesson link with the vault notebooks' static site served on 127.0.0.1:8777.
  248 captures in all: 56 links × 2 viewports in `arxiv_v2`, 68 × 2 in `arxiv_v2_goal` (the plain view included).
- **The facts in a JSON.** Every custom property on `:root` with its computed value, and for each named region of
  the state (window chrome, shelf rows, footer dots, companion parts, search parts, pad tabs, pad blocks and gutter
  marks, overview cards and rings and links, menus…): its colours as exact hex (text, background, what shows through
  a transparent background, each border, box shadow, outline, SVG stroke and fill), type (family stack, size, weight,
  style, line height, letter spacing, case), border radius, padding, border widths, opacity (own and effective), and
  bounding box. A region counts as shown when it is on screen and its effective opacity is above 0.01. Up to 40
  elements whose class appears in a state but not in the plain view are measured too, as `auto:<tag.class>`: the
  facts for the stages not built yet.
- **How it was driven.** The mockup served on 127.0.0.1 and driven in headless Playwright Chromium. Google Fonts and
  KaTeX from jsDelivr were allowed (the mockup fetches its fonts; the app ships the same faces locally); YouTube
  posters were refused (their ids are the owner's videos), so video windows show their poster frame empty; the
  notebooks' WebAssembly runtime was allowed for the Teacher lesson link only.
- **Deep links that do not apply in headless Chromium.** `#focus=3` and `#move` render the plain view (`#move` has no
  value, so the mockup's parser reads it as false; `#focus=3`'s focus is undone by a later layer). They were captured
  after the mockup's own keys (`alt+l` ×3, `alt+]`), which run the code those links call, as the RD1 review did.
  `#selftest` and `#selftest2` start the mockup's self-tests, which are still running when captured: their geometry
  is not compared.

## 2. Re-checking a stage (one command per stage)

Build the harness page once (from `apps/learnloop-tauri`, through the scratch wrapper):

    npx vite build --config vite.desks.config.mjs

then, from the worktree root:

    uv run --no-project --with playwright==1.65.2 --with pillow==11.3.0 \
        python scripts/desk_harness/visual_reference.py --ref <the private reference directory> --stage rd1

`--stage` is `rd1`, `rd2`, `rd3`, `rd4`, `rd6` (the goal lens, on the harness's `?goal=1` page) `rd9` (the Teacher
lesson's tab, on the harness's `?lesson=1` page) or `rd10` (follow-along and the suggested chapters, on `?video=1`); `--state '<deep link>'` re-checks one state (for example
`--state 'cur=sel'`); `--viewport design|laptop|both`. Each state starts from a fresh page, so states are independent.
It prints one line per state and viewport, and writes into `<ref>/compare/`: `result__<stage>.json` (every difference
per state, the harness's own measurements, the tokens), `findings__<stage>.json` (one row per distinct difference,
with the states it shows in), and for each state `<variant>__<state>__<viewport>__side_by_side.png` (mockup |
harness | changed pixels). Each state and viewport takes about 8 s (a few minutes a stage). Differences are findings, not failures: the exit
status is 0 when the run completed and 2 when the build or the reference is missing.

A later stage adds its states to `STATES` in the script (a deep link name, the stage, a function that puts the
harness in that state, the regions it shows) and the harness selectors of any new region to `REGIONS`. The mockup's
selectors for every region name are in the private capture script; a region the private capture has not mapped is
reported as `not_mapped_in_reference`, and the capture is rerun for it (`capture.py --only '<link>|<link>'`). A
selector ending in ` @n` measures the n-th shown match (from 0); one starting with `~` also takes a match faded to
opacity 0.

## 3. What is compared, and the tolerances

- **Tokens, exactly** (§4.2): each mockup `:root` property `--x` against the desks' `--desk-x` on `.desk-shell`.
- **Colours, exactly**: hex strings, alpha included. A transparent background is compared by what shows through it.
- **Type, exactly**: the designed family (the first family of the stack, with the app's ` Variable` suffix removed:
  the app ships the variable cuts of the same faces), size, weight, style, line height, letter spacing and case.
- **Geometry, within 2 px.** The smallest design quantities in §4.3 are the 9 px tab order grade, the 10 px slot gap
  and the 14 px insets; 2 px still catches every departure from a stated value while it absorbs what is not a design
  difference: sub-pixel rounding of percentages (52 % of the stage) and the variable fonts' line boxes against the
  static cuts the mockup fetched (±1 px a line). Positions and sizes are compared only where they do not follow
  content: a region whose width follows its text, or whose place follows the blocks above it, compares its height or
  its size only (per region in the script), because the fixture's text is not the owner's.
- **The pixel figure** is the share of pixels where any channel differs by more than 24 (the harness's own
  threshold). It is for the owner's eye, beside the side-by-side images: the fixture's arrangement and text differ
  from the owner's desk (a video beside the book where the mockup has the pads; a Guide panel fourth), so 20–60 %
  changes in every state, and the number tracks layout changes, not correctness.

## 4. Tokens (§4.2)

Every §4.2 colour is the same value in both: shell, paper, ink 1–3, rules, amber and amber ink, LearnLoop purple,
purple ink and wash, cyan (and the mockup's own `--shell2`, `--line`, `--line2`, `--t`, `--t2`, `--t3`). Pad paper
`#fdfdfc`, search `#2563eb` and pen `#2b4fa8` are literals in the mockup and tokens in the desks; the values agree.

| Token | Mockup | Desks | Reading |
|---|---|---|---|
| `--book`, `--paperfont`, `--mono` | `"Literata"`, `"Source Serif 4"`, `"JetBrains Mono"` first | the same faces, their ` Variable` cuts first | the same design (the app ships the variable cuts locally, §4.2) |
| `--ui` | `"JetBrains Mono", …` | `"Inter Variable", "Inter", …` | **a conflict between the spec and the mockup**: §4.2 says UI is Inter, the mockup sets its whole interface in JetBrains Mono. VR-1 |
| `--amber-wash` `#fbeedc`, `--amber-mid` `#9a6f3a`, `--amber-hi` `#f0c890`, `--cyan-ink` `#1f7f8f`, `--cyan-wash` `#e2f3f5`, `--elev` `#181818`, `--elev2` `#1d1d20`, `--bd` `#2a2a2a`, `--bd2` `#3a3a3a`, `--wash-amber` `#241d12`, `--wash-purple` `#1a162a`, `--purple-line` `#7d6fb8` | declared | absent as tokens | not in §4.2; the desks write several of these values as literals where they use them. Information, not a finding |
| `--mock` | `#c58bd8` | absent | mockup only, never built (§4.2) |

The goal variant declares the same tokens plus five for the goal lens (`--gl` `#5b4a9a`, `--gl-sup`
`rgba(91,74,154,.34)`, `--gl-skip` `#b9b2cc`, `--gdim` `#8e897f`, `--gband` `#0f0e12`): RD6's.

## 5. Findings by stage

Severity: **colour** (a wrong colour or token), **size** (a wrong size or position), **element** (a missing
element), **state** (a missing state). "Excused" names the §4.4 row, or says why the difference is not a defect
(a fixture difference, a recorded deviation, a spec rule the mockup does not follow). Each real difference has a
ledger row (`docs/reviews/refactor-bug-ledger.md`, VR-n), with no fix and its stage's fix round as the deadline.

Counts (rows of `findings__all.json`, one row per region, property and pair of values, as the comparison's last
lines print them; corrected 2026-11-23, §10): RD1 95, RD2 107, RD3 75, RD4 93; after reading them, **41 real differences**
(RD1 12, RD2 7, RD3 9, RD4 13; three of them owner calls) and the rest excused or explained below. The overview's type is measured in world
pixels (the cards are drawn at 1/0.34 and scaled), so a world size is given with its on-screen size.

### RD1: desks, windows, focus mode (`#desk=1`, `#focus=3`, `#move`, `#zoom=after`, `#s11=fs150`, plain view)

| Id | State | What differs | Severity | Excused? |
|---|---|---|---|---|
| VR-1 | every state | The interface type: the desks set chrome text (shelf rows and names, top bar, slivers, window frames, stage) in Inter; the mockup sets every interface region in JetBrains Mono (its `--ui`). The desks' tabs, keys and pad tabs are already mono, so the shell mixes the two | colour or token (type) | No. §4.2 says Inter: the spec and the mockup disagree. **Owner call** |
| VR-2 | every state with windows | Window head: background `#151517`, mockup `#161618f0`; bottom rule `#26262a`, mockup `#000000`; head text `#d8d8e0`, mockup `#a8a8b8` (the title stays `#d8d8e0` in both); the kind glyph `#8b8b9d`, mockup `#d8d8e0` | colour | No |
| VR-3 | plain, `#desk=1`, `#move`, focus mode | The book and the transcript are not set on a sheet: in the mockup the page is a sheet inside the window, 22 px of the window's dark showing at each side, padded 40/44/54/60 px (transcript 18/22/30/12) with a `0 10px 40px #00000073` shadow; the desks fill the window with paper, no padding, no shadow | missing element | No |
| VR-4 | plain, `#desk=1`, `#move`, focus mode | Book prose: 15 px on a 22.1 px line, mockup 16.5 px on 27.4 px (design viewport); 13 px, mockup 15 px on 24.9 px (laptop) | wrong size | No |
| VR-5 | `#desk=1`, `#focus=3` | Transcript cues: 11 px on 17.6 px in `#55524c` with a 1 px rule under each cue; mockup 15 px Literata on 24.3 px in `#1f1e1c`, no rule | wrong size, colour | No |
| VR-6 | plain, `#desk=1`, `#focus=3`, `#move` | Shelf rows: focused and in-view background `#1a1a1e`, mockup `#1b1a17` (warm); the focus bar 2 px, mockup 3 px; the in-view bar `#a8a8b8`, mockup `#9a6f3a` (amber mid) | colour | No |
| VR-7 | plain, `#desk=1`, `#focus=3`, `#move` | Footer desk dots 18 px wide, mockup 15 px (on a 25 px pitch) | wrong size | No |
| VR-8 | `#s11=fs150` | Focus mode's zoom badge: top right, 24 px high, radius 4 px, `#141416e6`, text `#a8a8b8` 11 px, padding 4/8; mockup bottom centre (x 691, y 850 at 1440 × 900), 28 px high, a pill (radius 12 px), `#181818f0`, text `#d8d8e0` 12 px, padding 5/14 | wrong position, colour | No (§4.3's toast is bottom centre too) |
| VR-9 | plain, every state | Top-bar chips 12 px, mockup 11.5 px | wrong size (type) | No |
| VR-10 | plain, every state | The shelf's "/ switch" weight 400, mockup 500 | type | No |
| VR-11 | plain, `#desk=1`, `#focus=3`, `#move` (laptop) | Below 1400 px the top bar is 38 px high; the mockup's is 34 px | wrong size | No |
| VR-12 | plain | The companion starts closed (its tab at the bottom right); the mockup starts with it docked open at `br` | missing state | Not a §4.4 row; the spec does not say which. **Owner call** |

Also excused: focus mode fills the viewport (1440 × 900, radius 0, no ring) where the mockup's focused window is 676 px
at x 34 with a `#6b5534` ring (§4.4 row 1: focus is truly full screen); slots 563 px wide where the mockup's are 558 (RD1's recorded deviation: equal 34 px margins both sides,
so every window x after the first is 5 px further right); `#desk=1` has no sliver and `#focus=3`'s window has no
location line (the fixture's attention desk has two windows and its fourth window is the Guide panel: a fixture
difference); the harness's first passage is amber with a 3 px bar (it is the passage being read), so the plain
passage after it is measured.

### RD2: the overview and the laptop rail (`#ov`, `#ovn=far`, `#ovn=down`, `#scrub=0.5`, `#ovg`, `#lap=1`, `#lap=open`)

| Id | State | What differs | Severity | Excused? |
|---|---|---|---|---|
| VR-13 | `#ov`, `#ovn=*`, `#ovg`, `#scrub=0.5` | Desk row labels: `#8b8b9d`, 32 world px (10.9 on screen), weight 500, spacing 3.2; mockup `#a8a8b8`, 38.2 world px (13.0), weight 400, spacing 3.8 | colour, type | No |
| VR-14 | `#ov`, `#ovn=*`, `#ovg` | Card names: weight 400 at 38 world px (12.9 on screen); mockup weight 500 at 35.3 (12.0) | type | No |
| VR-15 | `#ov`, `#ovn=*`, `#ovg` | The card's kind glyph `#8b8b9d`; mockup cyan `#6ad0e0` | colour | No |
| VR-16 | `#ov`, `#ovn=*`, `#ovg` | The card's minimap bar `#2e2e34` with 3 px radius; mockup `#3a3a40`, square | colour | No |
| VR-17 | `#ov`, `#ovn=far`, `#ovg` | The focused card's face `#202024`; mockup `#2a261e` (warm) | colour | No |
| VR-18 | `#ov`, `#ovn=down`, `#ovg` | Link labels in `#6ad0e0` with no halo; mockup `#bfeef5` with a `#0a0a0b` stroke halo; links drawn at opacity 0.9, mockup 1 | colour | No |
| VR-19 | `#ov`, `#ovn=*`, `#ovg` | Rings: a related card's cyan ring 5.88 world px (2.0 on screen), mockup 4.41 (1.5); the selection's halo `#e3a0632e` (18 %), mockup `#e3a06340` (25 %) | colour, size | No |

Also excused: the laptop rail matches exactly (44 px, `#0e0e10`, the same border); a far selection has no relations
in the fixture, so `#ovn=far` has no links or cyan rings (fixture); the mockup's cards pad their picture 29.4 world
px where the desks inset a live miniature (two constructions of the same card: no visual difference measured); type
differences under 0.5 world px (0.2 on screen) are rounding of the mockup's 1/0.34 scaling; `#selftest` and
`#selftest2` compare colour and type only (the mockup's self-tests still run when captured) and show RD1's rows.

### RD3: the companion and search (`#cur=sel`, `#cur=handoff`, `#cur=shiftc`, `#dock=right`, `#cov`, `#hist`, `#selctx`, `#spot=softmax`, `#switch`, `#lap=comp`)

| Id | State | What differs | Severity | Excused? |
|---|---|---|---|---|
| VR-20 | every companion state | Line height: the companion's text sits on the browser's normal line (about 1.2); the mockup's on 1.6 (19.2 px at 12 px) in the body, tabs and handle, 16–17.3 px in the history. The tab row is 27 px high (mockup 30.6), a tab 20 px (23.6) | type, size | No |
| VR-21 | every companion state | The active tab's amber underline 2 px; mockup 1 px | wrong size | No |
| VR-22 | `#cur=sel` (design) | The companion opened at the cursor is 360 px wide at 1440 × 900; the mockup's 400. §4.3 asks for 360 only below 1240 px: the desks appear to test the stage (1204 px) instead of the window | wrong size | No |
| VR-23 | `#cur=shiftc`, `#cur=handoff`, `#hist`, `#lap=comp` (laptop) | The docked companion at 1280 × 800: 400 × 383 px; the mockup's 330 × 368 | wrong size | §4.3 says 400 wide; the mockup draws 330 at this width. **Owner call** |
| VR-24 | `#cur=sel` | The selection chip: left rule `#9a6f3a`, mockup `#3a3a3a`; its label `#8b8b9d`, mockup `#d8d8e0`; the quote `#f0c890` 12 px, mockup `#d8d8e0` 12.5 px; padding 6/8/6/8, mockup 3/0/3/8 | colour, type | No |
| VR-25 | `#selctx` | In the harness, shift+C with a passage selected opens the docked companion without the selection chip; the mockup's docked companion shows "§ asking about …" with the selection | missing state | No |
| VR-26 | `#hist` | History day headers have no top rule; the mockup's have 1 px | missing element | No |
| VR-27 | `#spot=softmax`, `#switch` | The search footer has no band of its own; the mockup's sits on `#111113` between 1 px rules | missing element, colour | No |
| VR-28 | `#spot=softmax`, `#switch` | Search input text `#eeeeee`, mockup `#ffffff`; the selected row's text `#ffffff`, mockup `#d8d8e0` | colour | No |

Also excused: the input's text colour (`#d8d8e0` against the mockup's `#8b8b9d`: the mockup's input is a static line
of placeholder text, §4.4 row 12); `#dock=right` compares colour and type only (in headless Chromium the mockup's
link leaves the panel at its default dock); an anchored panel's place follows the fixture's passage; the search
panel's height follows its results (its 640 px width matches); the search backdrop is a pseudo-element in the
mockup and was not measured (RD3's review: no visible blur there, 2 px in the desks per §4.3). Chip and thread are
measured in different states, because asking takes the chip into the question.

### RD4: the pads (`#s11=run`, `#tabs=distance,pad=2,padf=0.4`, `#tabs=order`, `#s11=lift`, `#s11=sketchqk`, `#s12=info`, `#s12=submitted`, `#append`, `#markback`, `#backlink`, `#s11=menu`, `#s11=arrange`, `#s11=split`)

| Id | State | What differs | Severity | Excused? |
|---|---|---|---|---|
| VR-29 | `#s11=run` and every RD1 state | The shelf has no TODAY · RUNNING PAD section (its heading, "open", and the running pad's last lines); the mockup's sits above CARRIED | missing element | No |
| VR-30 | plain, `#desk=1`, `#focus=3`, `#move`, `#ov` | Carried questions in the shelf: `#a8a8b8`, upright, normal line; mockup `#d8d8e0`, italic, 15.4 px line | colour, type | No |
| VR-31 | every pad state | Pad paper and tab borders `#4a4740`; mockup `#2a2825` | colour | No |
| VR-32 | every pad state | Gutter marks (§, ◇, ◇ fig) are bare glyphs; the mockup's are chips with a 3 px radius and 3/2/1/2 padding (their colours agree) | wrong size | No |
| VR-33 | every pad state | A quote's back-link chip is transparent; the mockup's sits on `#fff8ec` | colour | No |
| VR-34 | every pad state | Quote text `#2a2825`, mockup `#3b3832`; the tutor's block text `#3b3832`, mockup `#2a2825`; its rule `#7d6fb8`, mockup `#6a5aa8`; its "◇ the tutor …" line `#5b4a9a`, mockup `#6a5aa8` | colour | No |
| VR-35 | every pad state | The submitted tag: text `#2f7a46`, border `#8cc39c`, 10 px, no letter spacing; mockup `#2f6b3b`, `#9fc9a8`, 9.5 px, 0.38 px spacing | colour, type | No |
| VR-36 | every pad state | The open tab's title weight 400, mockup 500; a block's prose has no left padding, the mockup's 6 px | type, size | No |
| VR-37 | `#s12=info` | ⓘ is bare text in `#a8a8b8`; the mockup's is circled (1 px border, 50 % radius) in `#8b8b9d`. The popover's text `#a8a8b8` 11 px, mockup `#d8d8e0` 12 px; its shadow `0 14px 40px`, mockup `0 12px 30px` | colour, type | Its place (a row above the stack, not the title bar) is RD4's recorded deviation; the styling is not |
| VR-38 | `#s11=lift` | The lifted stub "→ lifted to …" in `#7a766e` with no padding; mockup `#1f1e1c`, 3 px above and below | colour | No |
| VR-39 | `#s11=arrange` | Arrange is a floating panel (`#181818`, 1 px border, radius 4, a `0 24px 70px` shadow, padding 6); the mockup's covers the pad window (`#0c0c0df5`, no border or radius, padding 14) | wrong colour, size | No |
| VR-40 | `#s11=menu` | The menu's frame: 340 px wide, mockup 360; text `#d8d8e0`, mockup `#eeeeee`; its heading `#8b8b9d` 10.5 px over a 1 px rule, mockup `#a8a8b8` 10 px, no rule; rows on the normal line, mockup 16.8 px; shadow `0 24px 70px`, mockup `0 18px 50px` | colour, type, size | The mockup's menu here is the source menu (RD5's rows); only the frame and row type are compared |
| VR-41 | `#markback` | The passage's ✎ mark: 3 px side padding on the normal line; mockup no padding on an 18 px line | wrong size | No |

Also excused: day headings measure `text-transform: none` against the mockup's `uppercase`, but the desks' day text is
already capitals (no visible difference); in `#s11=split` the desks title each pane with a heading row instead of
tabs (RD4's recorded construction), so the split's tab regions are absent; `#append` is compared as the running pad
scrolled to its end, while the mockup's frame is RD5's passage-menu append (only the pad's colours are compared);
in `#s11=lift` the carry chip has scrolled out of view; at 1280 × 800 the jot line is below the fold; the arrange
cards are not mapped (the two constructions differ); `#s11=sketchqk` is on the attention desk in the mockup and on the
first desk in the harness (its tool row is compared; it matches).

## 6. Not reachable, not compared

Every landed state was reached by the harness at both viewports (73 comparisons, none refused). What is compared
only in part, and why:

- `#selftest`, `#selftest2`, `#dock=right`: colour and type only (the mockup is not at rest, or its link does not
  apply in headless Chromium).
- `#append`, `#s11=menu`: the mockup's frame belongs to RD5 (the passage menu); the pad side and the menu's frame are
  compared.
- The search backdrop (a pseudo-element in the mockup) and video posters (YouTube refused) are not measured.
- The focus-mode badge has faded out by the time the mockup is captured (4.5 s): it is measured at opacity 0 on
  both sides (a `~` before a region's selector takes a faded match), so its place, size, colours and type compare,
  and its opacity row is not a finding.
- The companion's claim chip and the history's anchors depend on the fixture's thread; they are measured where the
  harness's thread shows them.

## 7. The states each later stage must pass

Captured, both viewports and (for non-goal links) both variants; nothing compared yet. Each later stage adds these
states to the script's `STATES` with a driver and its regions' harness selectors. The private capture measured,
besides the shell's named regions, the elements new in each state (`auto:<tag.class>`), so a later worker has the
mockup's facts for the new parts without re-running it.

| Stage | States it must pass |
|---|---|
| RD5 Menus | `#menu=cue`, `#menuhl`, `#s11=menu` (the source menu: promoted rows, the verbs, Append to …), `#append` (the passage side) |
| RD6 Goal lens | `#goal=frame`, `#goal=why`, `#goal=whysup`, `#goal=whyskip`, `#goal=basics`, `#goal=path`, `#goal=paper`, `#goal=pads`, `#goal=frame,nodim`; the five goal tokens |
| RD7 Inline checks and veils | `#goal=check`, `#goal=answered`, `#goal=checkb`, `#s12=check`, `#s12=answered` |
| RD8a Pen and ink | `#pen=underline`, `#pen=bracket`, `#pen=note`, `#pen=lasso`, `#pen=strike`, `#pen=pad`, `#pen=ladder`, `#pen=rung2`, `#pen=veil` |
| Figures (§13.1) | `#figmark`, `#figmove`; `#figopen` and `#figsrc` render the plain view in headless Chromium (inert links: drive them by the mockup's clicks when the stage comes) |
| RD9a / RD9b Lesson windows and notebooks | `#tabs=distance,pad=3` (captured with the notebooks' static site served on 127.0.0.1:8777; the lesson rendered). RD9a compares it in the `rd9` stage: the lesson pad's head, mode buttons and frame (regions `lesson_*`, measured into the existing capture with the private tool's `--add-regions`, which keeps its screenshot and earlier regions) and the open tab; the frame's content (the notebook) is RD9b's |
| RD10 Video and carried polish | The `rd10` stage: `follow` (the book's chip) against the plain view, `chapters` (the suggested chapters under the focused video, an accepted chapter's tick) against `#goal=video`; regions `follow_*` and `chap_*`, measured into those captures with the private tool's `--add-regions`. A state may name its reference link (`reference`) when it is not its own name |
| RD1 follow-ups | `#s11=fs150` and `#zoom=after` again once VR-8 is fixed |

## 8. Not verified

- The packaged app on WebKitGTK: everything here is Chromium, both sides (as the stage reviews).
- The goal variant's non-goal states were captured but compared only through `arxiv_v2`'s: the shell is the same
  page, and its `:root` tokens are `arxiv_v2`'s plus the five goal tokens.
- Animations and timings (§4.3's durations and easings): the reference is resting frames.
- The mockup's own defects (§4.4) are captured as they are; they are not findings.
- Hover states (the § row's fade, mark hover cards) and the claim chip: the stage harness checks them; this
  reference has resting frames only.
- The 41 differences were read from measured facts and the side-by-side images; each was not separately confirmed
  against the source of the rule that draws it.

## 9. Fix round (2026-11-23, branch `reader/visual-parity-fixes`)

The owner's rule for this round: the workbench recreates the mockup, so where the spec's text and the mockup disagree
on looks the mockup wins and the spec is corrected in the same commit (VR-1: §4.2's interface face; VR-23: §4.3's
laptop docks; §4.3 also gains the 34 px top bar on a short window). Behaviour stays as it was, except VR-25, which
was a product bug. Styles live in `styles/desk.css`; markup changed in three places only (the selection chip's label
in its own span, ⓘ in its own ring, the overview's link labels' paint).

**Counts:** see §10 (one reproducible number per stage, and the command that prints it).

| Row | Outcome |
|---|---|
| VR-1 | Fixed: `--desk-ui` is JetBrains Mono; §4.2 corrected. Reading text stays Literata. The Inter package is still imported by the shell (the harness's font check loads it); dropping it is a later cleanup |
| VR-2, VR-4..VR-11, VR-30 | Fixed (window heads, prose 16.5 px on 1.66, cues 15 px Literata in ink, shelf rows, dots, the zoom badge's bottom-centre pill, chips, "/ switch", the 34 px top bar under 820 px, carried questions) |
| VR-3 | The book: fixed (the Reader's scroller is the page sheet, 22 px of the window's dark round it, the mockup's padding and shadow). The transcript's sheet: open, it needs §7.4's player and transcript layout (the watch panel's inline-styled card), not a style change |
| VR-12 | Owner (the first-load state is behaviour) |
| VR-13..VR-19 | Fixed (overview labels, card names and glyph, the minimap bar, the selection's warm face, link labels with their halo, rings; the card face's padding and gap too) |
| VR-20, VR-21, VR-24, VR-26..VR-28 | Fixed (the companion's 1.6 line, the 1 px tab underline, the chip, history day rules, the search footer band, search text colours; the context line kept to one line) |
| VR-22, VR-23 | Fixed: the companion's narrow summon and laptop docks go by the window's width (`Stage.viewport`, optional, read only by the companion's rules); §4.3 corrected |
| VR-25 | A product bug, fixed: shift+c dropped a selection, so a question asked at the dock carried no passage (§8.6). Fail-first test in `DeskShell.test.tsx` |
| VR-29 | Moved to the menus frontend worker, with the pad window's title |
| VR-31, VR-33..VR-41 | Fixed (pad borders, tab titles, quotes and back-link chips, the tutor's block, the submitted tag, ⓘ, the lifted stub, the ✎ mark, the pad menu's frame and selection, arrange covering the pad window, the sketch's tool row) |
| VR-32 | Withdrawn: the mockup's measured "chip" was its gutter cell, transparent and borderless; nothing differs on screen |
| VR-42 (new) | Fixed: the DeskShell tests' `passage.union_range` double answered the wrong shape (six unhandled rejections per run) |
| VR-43 (new) | Owner: the mockup sets a source window's prose to 15 px when it is beside the focus; doing so reflows the book on every focus change |
| VR-44 (new) | Owner: the mockup's 558 px slots (34 px left, 44 right) were built and backed out in this round: the third window's edge then counts as visible (a lifecycle change). RD1's 563 px stays |
| VR-45 (new) | Open: the mockup's opened strip covers the rail with its ☰ inside; that needs markup and a way to close, not a style |

**Still excused** (unchanged from §5): focus mode is truly full screen (§4.4 row 1); the companion's input is a real
input (§4.4 row 12); fixture differences (which card is first on screen, the attention desk's two windows, the Guide
panel's missing location, the anchored panel's place); the mockup's own timing (its badge has faded when captured);
day headings measure `text-transform: none` but their text is already capitals; the passages' 12 px reading-bar
padding (the sheet's padding is 12 px less, so the text sits where the mockup's does).

**What the comparison learned this round** (in the script, tracked): a border in a transparent colour is no border;
values within 0.05 px are equal (the mockup works out 1/0.34 to more digits); the book's paper is the page sheet;
the selected overview card's face is measured; the pad menu's rows exclude the selected one; the gutter marks
compare colour and type; the pointer leaves a control the driver clicked before measuring.

**Assertions and expectations changed:** the desk harness's anchored-summon check now scrolls the book so its
passage is near the top before selecting (at the new reading size the panel no longer fit below it); the expectation
itself (10 px below the selection) is unchanged. The geometry test's slot sum was changed for the 558 px slots and
changed back with them (net unchanged). No snapshot or style assertion encoded the old values.

**Tests:** vitest (4 workers) 362 files, 4057 tests passed; `npm run typecheck` clean; the desk harness 97 passed, 0
failed (every display-math check included: pads at three widths, the hover card, the companion's answer, after a
resize); no new TypeScript file, so `desktop_validate.py`'s three counts are unchanged (its reproducibility check
lists the generated notes the landing regenerates).

### Round 2 (the two rows that needed markup; on top of the goal lens's watch panel)

| Row | Outcome |
|---|---|
| VR-3, the transcript | Fixed (`040b025bb8`): the video window as the mockup's §7.4 layout. The player sits on the window's dark (12 px down, 16 px in) with the goal lens's track under it in the same cell; the panel's controls line follows on dark; the transcript is a paper sheet with the mockup's margins and shadow that fills the rest of the window and scrolls inside itself (following the video moves that scroller). `YouTubeWatchPanel.tsx` gains class names only, on the goal lens's markup; the desks lay it out with `order` and `display: contents`, so no element moves and the player never remounts (the harness's two-player, hidden-desk and remount checks pass) |
| VR-45 | Fixed (`3dc89dc187`): below 1400 px the opened strip covers the rail from the window's edge with its own ☰ and "strip" on top; the closed rail shows ☰ over a vertical "strip". The shell owns the open state; the key router gains a `strip` scope (below arrange, above pen) whose esc closes it and which passes every other key on. Fail-first tests in `DeskShell.test.tsx` (esc and pointer); `router.test.ts` gains the strip case, and its scope-order expectation now lists `strip` |
| Inter | Removed (`8024da8119`): no other screen named it. The package, the shell's import, its `LICENSES.txt` entry and the harness's font check (now four fonts) went; §4.2 says so |

After round 2 every row the comparison still reports (RD1 to RD4, both viewports; counted in §10) is excused or
listed above (VR-12, VR-29, VR-43, VR-44, the fixture's differences). The `video_paper` rows and the open
strip's place are gone. Tests: vitest 367 files, 4099 passed; typecheck clean; the desk harness 120 passed, 0 failed
(the goal lens's checks included).

## 10. Counts: one number per stage, and how to reproduce it (corrected 2026-11-23)

The comparison's last lines print, per stage, the rows of `findings__<run>.json`: one row per region, property and
pair of values, so the same difference at other values (the laptop's sizes, another state's position) is a row of
its own. Run from the worktree root, after building the harness page:

    uv run --no-project --with playwright==1.65.2 --with pillow==11.3.0 \
        python scripts/desk_harness/visual_reference.py --ref <the private reference directory> --stage all

| Stage | Before the fix round (base of the branch) | Now (this record's tip) |
|---|---|---|
| RD1 | 103 | 37 (colour 2, type 2, geometry 30, missing 3) |
| RD2 | 107 | 22 (colour 8, type 2, geometry 6, missing 6) |
| RD3 | 75 | 7 (colour 1, geometry 4, missing 2) |
| RD4 | 93 | 20 (type 3, geometry 1, missing 16) |

(The reference record's first run, §5, counted 95, 107, 75 and 93; the fix round's base had RD3 and RD4's fix rounds
merged in. The "before" column used the comparison as it was then; later rounds taught it to ignore transparent
borders and sub-0.05 px rounding, which only removes rows.)

**Why the record said 19, 21, 5 and 20 (and 79, 102, 68, 90 before):** those figures came from a private helper that
grouped a region's property across all its values, so a difference measured at two viewports or in three states with
different numbers counted once; the comparison's file counts each pair of values. The integration worker's 37, 22,
7 and 20 are the file's count and are the right figure to quote. Nothing was hidden by the grouping: RD1's 18 extra
rows are the same differences at other values, all already accounted for:

- the 5 px slot width and the positions that follow from it: `window_focus`, `window_focus_head`, `window_other`,
  `window_other_head` widths at 1440 and 1280, and their x in `#focus=3` and `#move` at both sizes (VR-44, owner);
- focus mode at both sizes (`window_focus` and its head: width, height, x, y, radius, ring; the mockup's half-width
  focus, §4.4 row 1), with the prose and sheet padding the mockup's narrower focus column gets at 1280;
- the sheet's 12 px less left padding (the passages carry those 12 px, so the text sits where the mockup's does),
  at two padding values.

RD2's 22 (against 21) is the first card's opacity at two values (it recedes in `#ovn=down` and is mid-fade in the
`#scrub=0.5` frame: which card is first on screen differs with the fixture); RD3's 7 (against 5) is the anchored
panel's place at two viewports (it follows the fixture's passage). No real difference was missing from §9.

