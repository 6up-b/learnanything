"""The Reader workbench's visual reference check (docs/reviews/reader-visual-reference.md).

The mockup is the design (docs/specs/spec_reader_workbench_v2.md §4): its deep links were captured, outside
every checkout, into a private reference directory, one PNG and one JSON of measured facts per state and
viewport. This script puts the desks' harness page (the same page scripts/desk_harness/run.py drives) in the
equivalent state for each landed stage, measures the same facts, and diffs them:

- design tokens exactly (§4.2): the mockup's :root custom properties against the desks' `--desk-*` ones;
- colours exactly (text, background, borders, shadow), as hex;
- type exactly (the designed family, size, weight, style, line height, letter spacing, case);
- geometry within GEOMETRY_TOLERANCE_PX (bounding box, padding, radius, border widths);
- a region the mockup shows and the harness does not is a missing element.

It also writes, for the owner's eyes only and only into the private directory, a side-by-side image per
state (mockup | harness | changed pixels) and the share of changed pixels. Nothing it writes goes in the
repository: the reference holds the owner's book text.

Build the harness page first (apps/learnloop-tauri: `npx vite build --config vite.desks.config.mjs`), then:

    uv run --no-project --with playwright==1.65.2 --with pillow==11.3.0 \\
        python scripts/desk_harness/visual_reference.py --ref <the private reference directory> --stage rd4

`--stage` is rd1, rd2, rd3, rd4, rd5, rd6, rd8, rd9, notebook or all; `--state NAME` runs one state; `--viewport design|laptop|both`.
Exit status 0 when the run completed (differences are findings, not failures), 2 when the reference is
missing. `--dump NAME` prints the harness's element tree in that state (for mapping new regions).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.async_api import Page, async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import DIST, route_outside, serve  # noqa: E402  (a sibling script, not a package)

# The mockup's design viewport and the laptop it folds for (the shelf becomes a rail below 1400 px).
VIEWPORTS = {"design": {"width": 1440, "height": 900}, "laptop": {"width": 1280, "height": 800}}

# Geometry is compared within 2 px. The smallest design quantities in §4.3 are the 9 px order grade, the
# 10 px slot gap and 14 px insets, so 2 px still catches every departure from a stated value, while it
# absorbs what is not a design difference: sub-pixel rounding of percentages (52 % of the stage) and the
# variable fonts' line boxes, which the app ships where the mockup fetched static cuts (±1 px per line).
GEOMETRY_TOLERANCE_PX = 2.0

# The share of pixels counted as changed uses the harness's own threshold (run.py PIXEL_THRESHOLD): a
# channel differing by more than 24 is a different pixel, anything less is antialiasing.
PIXEL_THRESHOLD = 24

# What each region's box means for the comparison: "box" its position and size, "pos" its position and
# height (its width follows its text, which differs between the owner's book and the fixture), "size" its
# width and height (where it sits follows content above it), "none" no geometry (only colour and type).
GEOM_KEYS = {"box": ("x", "y", "w", "h"), "pos": ("x", "y", "h"), "yh": ("y", "h"), "size": ("w", "h"), "width": ("w",), "height": ("h",), "none": ()}


@dataclass(frozen=True)
class Region:
    harness: str  # a CSS selector in the harness page; the first visible match is measured
    geom: str = "none"
    skip: tuple[str, ...] = ()  # properties not compared: the two pages build this region differently


# The named regions. A name is shared with the private capture, which holds the mockup's own selectors.
REGIONS: dict[str, Region] = {}


def region(name: str, harness: str, geom: str = "none", skip: tuple[str, ...] = ()) -> None:
    REGIONS[name] = Region(harness, geom, skip)


# ── Teacher lesson windows (RD9a; the harness's ?lesson=1 page): the lesson pad's head, modes and frame ──
region("lesson_body", ".desk-pads .paper.k-lesson", "width")
region("lesson_head", ".desk-pads .lessonnb .lhead", "none")
region("lesson_head_glyph", ".desk-pads .lessonnb .lhead .lg", "size")
region("lesson_head_faint", ".desk-pads .lessonnb .lhead .faint", "none")
region("lesson_mode_on", ".desk-pads .lessonnb .lmodes button.on", "height")
region("lesson_mode", ".desk-pads .lessonnb .lmodes button:not(.on)", "height")
region("lesson_mode_line", ".desk-pads .lessonnb .lmodes .lmd", "height")
region("lesson_frame", ".desk-pads .lessonnb .lframe", "width")

# ── the goal lens (RD6; the goal variant, the harness's ?goal=1 page) ──
region("goal_band", ".goalband", "box")
region("goal_band_lab", ".goalband .gb-goal .gb-lab", "height")
region("goal_band_sentence", ".goalband .gb-t", "height")
region("goal_band_counts", ".goalband .gb-path .gb-lab", "height")
region("goal_band_dot", ".gb-stops .gs:not(.chk):not(.unm):not(.rd-likely):not(.pre)", "size")
region("goal_band_dot_likely", ".gb-stops .gs.rd-likely", "size")
region("goal_band_dot_pre", ".gb-stops .gs.pre:not(.later)", "size")
region("goal_band_dot_later", ".gb-stops .gs.later", "size")
region("goal_band_dot_unmatched", ".gb-stops .gs.unm", "size")
region("goal_band_depth_on", ".gb-depth button.on", "height")
region("goal_band_depth", ".gb-depth button:not(.on)", "height")
region("goal_band_here_lab", ".gb-here .gb-lab", "height")
region("goal_band_here", ".gb-here .gb-ht", "height")
region("goal_band_next_lab", ".gb-next .gb-lab", "height")
region("goal_band_next", ".gb-nb", "height")
region("goal_band_dim", ".gb-dim", "height")
region("goal_band_path", ".gb-pth", "height")
# The marks: their width (their height follows the passage, their place the book's layout). The mark-to-text gap
# is the harness run's own check (scripts/desk_harness/run.py, the goal run).
# A mark holds no text: the type and text colour it inherits from its passage are not its own.
MARK_SKIP = ("color", "font")
region("goal_mark_core", "[data-window-kind='source'] .gm.gl-core:not(.gl-paper)", "width", skip=MARK_SKIP)
region("goal_mark_sup", "[data-window-kind='source'] .gm.gl-sup:not(.gl-paper)", "width", skip=MARK_SKIP)
region("goal_mark_skip", "[data-window-kind='source'] .gm.gl-skip:not(.gl-paper)", "width", skip=MARK_SKIP)
region("goal_mark_later", "[data-window-kind='source'] .gm.gl-later:not(.gl-paper)", "width", skip=MARK_SKIP)
region("goal_mark_on", "[data-window-kind='source'] .gm.on", "width", skip=MARK_SKIP)
# Dimmed text: its colour (the prose's own type and box are the book window's, VR-3, VR-4).
region("goal_text_dimmed", "[data-window-kind='source'] [data-span-id].gl-dim", "none",
       skip=("font", "padding", "radius", "background", "background_eff", "box_shadow", "border_left_width", "border_left_color"))
region("goal_why", ".gwhy.on", "width")
region("goal_why_head", ".gwhy.on .gwh", "none")
region("goal_why_body", ".gwhy.on .gwr", "none")
region("goal_why_for", ".gwhy.on .gwr b", "none")
region("goal_why_coverage", ".gwhy.on .gwc", "none")
region("goal_callout", "[data-window-kind='source'] .callout.gcall", "none")
region("goal_callout_lab", "[data-window-kind='source'] .callout.gcall .lab", "none")
region("goal_path", ".ovl.gpath", "box")
region("goal_path_left", ".gpath .gp-l", "size")
region("goal_path_h3", ".gpath h3", "none")
region("goal_path_scope", ".gp-scope", "none")
region("goal_path_unmatched", ".gp-unm", "none")
region("goal_path_depth_on", ".gp-d.on", "width")
region("goal_path_depth", ".gp-d:not(.on)", "width")
region("goal_path_ready", ".gp-ready", "none")
region("goal_path_key", ".gp-key", "none")
region("goal_path_head", ".gp-r-wrap > .gp-gh", "height")
region("goal_path_lo", ".gp-lo", "width")
region("goal_path_lo_title", ".gp-h .gp-ti", "none")
region("goal_path_tag_core", ".gp-tag.core", "height")
region("goal_path_tag_pre", ".gp-tag.prerequisite", "height")
region("goal_path_dot", ".gp-h .gp-n.rd-likely", "size")
region("goal_path_primary", ".gp-prim", "width")
region("goal_path_primary_src", ".gp-prim .gp-src", "width")
region("goal_path_primary_at", ".gp-prim .gp-at", "width")
region("goal_path_primary_why", ".gp-prim .gp-why", "none")
region("goal_path_alt", ".gp-alt", "width")
region("goal_path_skip", ".gp-s", "width")
region("goal_path_skip_head", ".skipg .gp-gh", "none")
# The row's own box, colours and type are the shelf's (RD1; its interface face is VR-1): only the goal's additions here.
region("goal_shelf_row", ".desk-shelf .desk-src.g-core", "none", skip=("padding", "radius", "box_shadow", "background", "background_eff", "font"))
region("goal_shelf_mark_core", ".desk-shelf .desk-src.g-core > .gm.sh", "width", skip=MARK_SKIP)
region("goal_shelf_mark_sup", ".desk-shelf .desk-src.g-sup > .gm.sh", "width", skip=MARK_SKIP)
region("goal_shelf_mark_skip", ".desk-shelf .desk-src.g-skip > .gm.sh", "width", skip=MARK_SKIP)
region("goal_shelf_line", ".desk-shelf .desk-src.g-core > .gwl", "height")
region("goal_shelf_line_skip", ".desk-shelf .desk-src.g-skip > .gwl", "height")
region("goal_shelf_range", ".desk-shelf .desk-src .bar .gr", "height", skip=MARK_SKIP)
region("goal_transcript_mark", "[data-window-kind='video'] .tp.g-sup .tx > .gm.gl-tx", "width", skip=MARK_SKIP)
# Dimmed cue text: its colour (the cues' own type and box are the video window's, VR-5).
region("goal_transcript_dimmed", "[data-window-kind='video'] .tp.gl-dim .tx [data-transcript-span]", "none",
       skip=("font", "padding", "radius", "background", "background_eff", "box_shadow", "border_bottom_width", "border_bottom_color"))
region("goal_transcript_head", "[data-window-kind='video'] .gtcall:not(.off)", "none")
region("goal_transcript_head_off", "[data-window-kind='video'] .gtcall.off", "none")
region("goal_track", "[data-window-kind='video'] .vtrack", "height", skip=MARK_SKIP)
region("goal_track_line", "[data-window-kind='video'] .vtrack .ln", "height", skip=MARK_SKIP)
region("goal_track_seg", "[data-window-kind='video'] .vtrack .gseg", "height", skip=MARK_SKIP)
region("goal_comp_ctx", ".desk-companion .ctx .gctx", "none")
region("goal_pad_line", ".gfor", "none")
region("goal_paper_mark", "[data-window-kind='source'] .gm.gl-paper", "width", skip=MARK_SKIP)
region("goal_paper_callout", ".gpcall", "none")

# ── the shell (RD1) ──
region("topbar", ".desk-top", "box")
region("brand", ".desk-brand", "box")
region("desk_tab_on", ".desk-tabs button[aria-current='true']", "pos")
region("desk_tab", ".desk-tabs button:not([aria-current='true'])", "pos")
region("top_chip", ".desk-top .tb", "height")
region("shelf", ".desk-shelf", "box")
region("shelf_head", ".desk-shelf > h4", "box")
region("shelf_switch", ".desk-shelf > h4 .switch", "size")
region("shelf_row_focus", ".desk-shelf .desk-src.prim", "none")
region("shelf_row_kind", ".desk-shelf .desk-src.prim .k", "height")
region("shelf_row_name", ".desk-shelf .desk-src.prim .n", "none")
region("shelf_row_where", ".desk-shelf .desk-src .w", "none")
region("shelf_row_bar_line", ".desk-shelf .desk-src .bar .ln", "size")
region("shelf_row_bar_read", ".desk-shelf .desk-src .bar .rd", "height")
region("shelf_row_inview", ".desk-shelf .desk-src.open:not(.prim)", "none")
region("shelf_row_other", ".desk-shelf .desk-src:not(.open):not(.prim)", "none")
region("shelf_lower_head", ".desk-shelf .lower h4", "none")
region("shelf_carried_head", ".desk-shelf .desk-carried h4", "none")
region("shelf_carried_item", ".desk-shelf .desk-carried .q", "none")
region("stage", ".desk-stage", "box")
region("sliver_right", ".desk-sliver.r", "box")
region("sliver_left", ".desk-sliver.l", "box")
region("sliver_glyph", ".desk-sliver .sg", "none")
region("sliver_title", ".desk-sliver .st", "none")
region("footer", ".desk-keys", "box")
region("footer_hint", ".desk-keys > span:not(.desk-dots):not(.note)", "pos")
region("footer_kbd", ".desk-keys > span:not(.desk-dots):not(.note) kbd", "height")
region("footer_dot_focus", ".desk-dots button.f", "size")
region("footer_dot_inview", ".desk-dots button.in", "size")
region("footer_dot", ".desk-dots button:not(.f):not(.in)", "size")
region("footer_note", ".desk-keys .note", "height")
region("window_focus", ".desk-window.focus", "box")
region("window_focus_head", ".desk-window.focus .desk-pane-head", "box")
region("window_focus_glyph", ".desk-window.focus .desk-pane-head .g", "none")
region("window_focus_title", ".desk-window.focus .desk-pane-head .t", "none")
region("window_focus_loc", ".desk-window.focus .desk-pane-head .loc", "none")
region("window_focus_close", ".desk-window.focus .desk-pane-head .x", "none")
region("window_other", ".desk-window:not(.focus):not(.paused)", "size")
region("window_other_head", ".desk-window:not(.focus):not(.paused) .desk-pane-head", "size")
# The page sheet: the Reader's scroller that holds the passages (the mockup's .sheet).
region("book_paper", ".desk-window [data-window-kind='source'] .ll-scroll:has(> [data-span-id])", "none")
# The first passage is the one being read (amber); the plain style is the next one's.
region("book_prose", ".desk-window [data-window-kind='source'] [data-span-id] @1", "none")
region("book_heading", ".desk-window [data-window-kind='source'] h2", "none")
# The transcript's paper sheet; the mockup pads the sheet, the desks the scroller inside it (under its header row).
region("video_paper", ".desk-window [data-window-kind='video'] .watch-transcript", "none", ("padding",))
region("video_cue", ".desk-window [data-window-kind='video'] [data-transcript-span]", "none")
region("focus_badge", "~.desk-zoom-badge", "yh")
# ── the overview (RD2) ──
region("ov_label", ".desk-ov-label", "none")
# The mockup draws the ring on the card itself, the desks on a ring element over it: only the ring compares.
region("ov_ring_sel", ".desk-ov-ring.sel", "none", ("background", "background_eff", "radius", "padding", "font"))
region("ov_ring_rel", ".desk-ov-ring.rel", "none", ("background", "background_eff", "radius", "padding", "font"))
# The mockup pads its card; the desks pad the face inside the card (compared by eye, not here).
region("ov_card", ".desk-card", "none", ("padding",))
region("ov_card_sel", ".desk-window.ov-selected .desk-card", "none", ("padding",))
region("ov_card_glyph", ".desk-card-g", "none")
region("ov_card_name", ".desk-card-n", "none")
region("ov_card_bar", ".desk-card-bar .ln", "height")
region("ov_link", ".desk-ov-links path", "none")
region("ov_link_label", ".desk-ov-links text", "none")
region("ov_ghost", ".desk-ov-ghost", "none")
region("hud", ".desk-hud", "pos")
region("shelf_rail", ".desk-shelf-rail", "box")
region("shelf_overlay", ".desk-shelf-overlay", "box")
# ── the companion and search (RD3) ──
region("comp_panel", ".desk-companion", "box")
region("comp_grab", ".desk-companion .grab", "size")
region("comp_tabs", ".desk-companion .ctabs", "size")
region("comp_tab_on", ".desk-companion .ctabs button.on", "height")
region("comp_tab", ".desk-companion .ctabs button:not(.on)", "height")
region("comp_ctx", ".desk-companion .ctx", "height")
region("comp_earlier", ".desk-companion .ctx .earlier", "none")
region("comp_body", ".desk-companion .body", "none")
region("comp_bub_you", ".desk-companion .bub.you", "none")
region("comp_bub_you_who", ".desk-companion .bub.you .who", "none")
region("comp_bub_ai", ".desk-companion .bub.ai", "none")
region("comp_bub_ai_who", ".desk-companion .bub.ai .who", "none")
region("comp_bub_ai_text", ".desk-companion .bub.ai p", "none")
region("comp_claim", ".desk-companion .claim", "none")
region("comp_chip", ".desk-companion .chip", "none")
region("comp_chip_quote", ".desk-companion .chip .q", "none")
region("comp_input", ".desk-companion .input", "height")
region("comp_pill", ".desk-companion-pill.on", "box")
region("comp_closed_tab", ".desk-companion-tab", "box")
region("hist_note", ".desk-companion .history .hnote", "none")
region("hist_day", ".desk-companion .history .hday", "none")
region("hist_desk", ".desk-companion .history .hdesk", "none")
region("hist_q", ".desk-companion .history .hq", "none")
region("hist_a", ".desk-companion .history .ha", "none")
region("search_backdrop", ".desk-search-backdrop", "box")
region("search_panel", ".desk-search", "width")
region("search_input", ".desk-search-in", "height")
region("search_input_field", ".desk-search-in input", "none")
region("search_group_head", ".desk-search-group .grp", "height")
region("search_row", ".desk-search .r:not(.sel)", "height")
region("search_row_where", ".desk-search .r:not(.sel) .w", "none")
region("search_sel", ".desk-search-sel", "height")
region("search_row_sel_text", ".desk-search .r.sel .t", "none")
region("search_foot", ".desk-search-foot", "height")
# ── the pads (RD4) ──
region("pad_window_head", ".desk-window:has(.desk-pads) .desk-pane-head", "height")
region("pad_tab_open", ".desk-pads .ptab.open .sheet", "height")
region("pad_tab", ".desk-pads .ptab:not(.open) .sheet", "height")
region("pad_tab_title", ".desk-pads .ptab.open .tt", "none")
region("pad_tab_label", ".desk-pads .ptab.open .tl", "none")
region("pad_tab_meta", ".desk-pads .ptab.open .tm", "none")
region("pad_paper", ".desk-pads .paper.k-running", "none")
region("pad_day", ".desk-pads .paper .day", "height")
region("pad_prose", ".desk-pads .pb:not(.srcrow):not(.jot) .bx", "none")
region("pad_quote", ".desk-pads .quote", "none")
region("pad_backlink", ".desk-pads .back", "height")
region("pad_tutor", ".desk-pads .tutorq", "none")
region("pad_tutor_who", ".desk-pads .tutorq .who", "none")
region("pad_submitted", ".desk-pads .submitted", "height")
region("pad_carry", ".desk-pads .carry", "none")
region("pad_jot", ".desk-pads .pb.jot .wline", "none")
# The mockup measures the gutter cell holding the glyph, the desks the glyph: colour and type compare.
region("pad_mark_src", ".desk-pads .mark.src", "none", ("padding", "radius"))
region("pad_mark_ll", ".desk-pads .mark.ll", "none", ("padding", "radius"))
region("pad_mark_fig", ".desk-pads .mark.fig", "none", ("padding", "radius"))
region("pad_lift", ".desk-pads .lift", "none")
# The mockup pads the stub's block box, the desks the box around the stub.
region("pad_lifted", ".desk-pads .lifted", "none", ("padding",))
region("pad_info_pop", ".desk-pads .pinfo-pop", "none")
# The ⓘ ring: in a pad stack's title bar the button is the ring; a stack mounted alone has its ring inside its bar.
region("pad_info_button", ".desk-pane-head .pinfo, .desk-pads .pinfo .ic", "none")
region("pad_card", ".desk-pads .pcard", "size")
# ── the context menu (RD5): one menu for passages, cues, highlights, notes, window headers and pad lines ──
# Its height follows its rows (the spec's verbs per object kind): the width is compared.
region("pad_menu", ".desk-menu:not(.submenu)", "width")
region("pad_menu_row", ".desk-menu > .mi:not(.sel)", "height")
region("pad_menu_head", ".desk-menu .mh", "none")
region("auto:div.pro", ".desk-menu .pro", "width")
region("auto:span.why", ".desk-menu .why", "none")
region("arrange_panel", ".desk-arrange", "none")
region("arrange_card", ".desk-pads .desk-arrange .row:not(.sel)", "none")
region("split_pane", ".desk-pads .split .pane", "none")
region("sketch_bar", ".desk-pads .desk-sketch .bar", "height")
region("sketch_tool", ".desk-pads .desk-sketch .bar button:not(.on)", "height")
region("sketch_canvas", ".desk-pads .desk-sketch canvas, .desk-pads .desk-sketch svg", "none")
region("pass_mark_pad", ".desk-pmark.pad", "none")
region("pad_flash", ".desk-pads .pb.flash", "none")
# ── pen and ink on sources (RD8a) ──
region("pen_chip_top", ".desk-top .penchip", "height")
region("pen_sim_top", ".desk-top .simpen", "height")
region("pen_hint", ".desk-keys .penk", "height")
region("pen_hint_kbd", ".desk-keys .penk kbd", "height")
# Only the pointer's cursor over the text (the prose itself is book_prose's, RD1's).
region("pen_text_cursor", ".desk-window [data-window-kind='source'] [data-span-id] @1", "none",
       ("color", "background", "background_eff", "box_shadow", "outline", "font", "radius", "padding", "border", "opacity"))
# A path's text colour and type are inherited and never drawn: a stroke compares its stroke, width and opacity.
STROKE_ONLY = ("color", "font", "background", "background_eff")
# Every stroke of a kind: its colour, width and opacity (the harness draws the learner's own stroke, the mockup a synthetic one).
region("pen_stroke_under", "svg.desk-pen-ink path.stroke.under", "none", STROKE_ONLY)
region("pen_stroke_bracket", "svg.desk-pen-ink path.stroke.bracket", "none", STROKE_ONLY)
region("pen_stroke_lasso", "svg.desk-pen-ink path.stroke.lasso", "none", STROKE_ONLY)
region("pen_stroke_strike", "svg.desk-pen-ink path.stroke.strike", "none", STROKE_ONLY)
region("pen_stroke_note", "svg.desk-pen-ink path.stroke.note", "none", STROKE_ONLY)
# The mockup wraps the words in a <mark> (or colours the paragraph); the desks lay a box under them: colours only.
region("pen_mark_hl", ".desk-pen-mark.underline", "height", ("radius", "padding", "font", "color"))
region("pen_mark_para", ".desk-pen-mark.bracket", "none", ("radius", "padding", "font", "color"))
region("pen_mark_sel", ".desk-pen-mark.lasso", "height", ("radius", "padding", "font", "color"))
region("pen_chip", ".desk-pen-chip", "height")
region("pen_chip_text", ".desk-pen-chip > span", "height")
region("pen_chip_undo", ".desk-pen-chip [data-undo]", "height")
region("pen_chip_x", ".desk-pen-chip [data-x]", "height")
region("pen_chip_ask", ".desk-pen-chip .askc", "height")
region("pen_note", ".desk-pen-note", "width")
region("pen_note_who", ".desk-pen-note .who", "height")
region("pen_note_text", ".desk-pen-note .ocr", "none")
region("pen_note_label", ".desk-pen-note .ocrl", "height")

# ── ink pads (RD8a, `#pen=pad`): the mockup draws its ink as handwriting-font text (mock ink); the desks draw the
# learner's strokes, so strokes are not compared here, only the paper, the bar and the transcription lines.
region("ink_pad_paper", ".desk-pads .paper.handpad", "none", ("radius", "padding", "font", "color"))
region("ink_bar", ".desk-pads .handbar", "height")
region("ink_bar_button", ".desk-pads .handbar button", "height")
region("ink_prov", ".desk-pads .pb .mark.prov", "none", ("padding",))
region("ink_read", ".desk-pads .ocrl2", "none")
region("ink_read_label", ".desk-pads .ocrl2 .ocrt", "height")
region("ink_read_tex", ".desk-pads .ocrl2 .ocrtex", "none")
region("ink_hint", ".desk-pads .hint2", "none")

# The pointer's cursor is compared on these regions only (pen mode's crosshair on the text).
CURSOR_REGIONS = frozenset({"pen_text_cursor"})


# The measured facts of one region: every computed colour, the type, the box model and the bounding box.
MEASURE_JS = r"""
(regions) => {
  const hex = (v) => v.replace(/rgba?\(([^)]+)\)/g, (_, body) => {
    const p = body.split(/[\s,\/]+/).filter(Boolean).map(Number);
    const h = (n) => Math.round(n).toString(16).padStart(2, '0');
    const a = p.length > 3 ? p[3] : 1;
    return '#' + h(p[0]) + h(p[1]) + h(p[2]) + (a < 1 ? h(a * 255) : '');
  });
  const effOpacity = (e) => { let o = 1; for (let n = e; n && n.nodeType === 1; n = n.parentElement) o *= Number(getComputedStyle(n).opacity); return Math.round(o * 1000) / 1000; };
  const effBackground = (e) => { for (let n = e; n && n.nodeType === 1; n = n.parentElement) { const b = getComputedStyle(n).backgroundColor; if (b && b !== 'rgba(0, 0, 0, 0)' && b !== 'transparent') return hex(b); } return null; };
  // Shown means on screen and not faded out: both pages keep some hidden controls at opacity 0.
  const visible = (e, anyOpacity = false) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth && (anyOpacity || effOpacity(e) > 0.01); };
  const out = {};
  for (const [name, sel] of regions) {
    // "selector @n" measures the n-th shown match (from 0), for a region whose first match is a special case.
    // "~selector" also takes a match faded to opacity 0 (a badge that has faded out by the time it is measured).
    const faded = sel.startsWith('~'); const bare = faded ? sel.slice(1) : sel;
    const at = bare.match(/^(.*)\s@(\d+)$/); const query = at ? at[1] : bare; const nth = at ? Number(at[2]) : 0;
    let els;
    try { els = [...document.querySelectorAll(query)]; } catch (err) { out[name] = { error: String(err) }; continue; }
    const vis = els.filter((e) => visible(e) || (faded && visible(e, true)));
    if (vis.length <= nth) { out[name] = null; continue; }
    const e = vis[nth]; const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
    const side = (p) => ['top', 'right', 'bottom', 'left'].map((s) => cs.getPropertyValue(p.replace('*', s)));
    out[name] = {
      count: vis.length,
      box: { x: Math.round(r.x * 10) / 10, y: Math.round(r.y * 10) / 10, w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10 },
      color: hex(cs.color),
      background: hex(cs.backgroundColor),
      background_eff: effBackground(e),
      background_image: cs.backgroundImage === 'none' ? 'none' : hex(cs.backgroundImage).slice(0, 300),
      border_color: side('border-*-color').map(hex),
      border_width: side('border-*-width'),
      border_style: side('border-*-style'),
      box_shadow: hex(cs.boxShadow),
      outline: cs.outlineStyle === 'none' ? 'none' : hex(cs.outlineColor) + ' ' + cs.outlineWidth + ' ' + cs.outlineStyle,
      font_family: cs.fontFamily,
      font_size: cs.fontSize,
      font_weight: cs.fontWeight,
      font_style: cs.fontStyle,
      line_height: cs.lineHeight,
      letter_spacing: cs.letterSpacing,
      text_transform: cs.textTransform,
      radius: ['top-left', 'top-right', 'bottom-right', 'bottom-left'].map((c) => cs.getPropertyValue('border-' + c + '-radius')),
      padding: side('padding-*'),
      opacity: Number(cs.opacity),
      opacity_eff: effOpacity(e),
      filter: cs.filter,
      cursor: cs.cursor,
    };
    if (e instanceof SVGElement) { out[name].stroke = hex(cs.stroke); out[name].fill = hex(cs.fill); out[name].stroke_width = cs.strokeWidth; }
  }
  return out;
}
"""

# Every custom property the page's style sheets declare on :root (the mockup) or on .desk-shell (the desks
# scope their tokens there so no other screen changes), with its computed value.
ROOT_VARS_JS = r"""
(scope) => {
  const target = document.querySelector(scope) || document.documentElement;
  const cs = getComputedStyle(target); const out = {};
  const pattern = scope === ':root' ? /(^|,)\s*:root\b/ : new RegExp('(^|,)\\s*' + scope.replace('.', '\\.') + '\\s*($|,)');
  const walk = (rules) => { for (const r of rules) {
    if (r.cssRules && !r.selectorText) walk(r.cssRules);
    if (r.selectorText && pattern.test(r.selectorText)) for (const n of r.style) if (n.startsWith('--')) out[n] = cs.getPropertyValue(n).trim(); } };
  for (const sh of document.styleSheets) { try { walk(sh.cssRules); } catch (err) { /* a cross-origin sheet has no rules to read */ } }
  return out;
}
"""


async def measure(page: Page, selectors: dict[str, str]) -> dict[str, Any]:
    return await page.evaluate(MEASURE_JS, [[name, sel] for name, sel in selectors.items()])


async def root_vars(page: Page, scope: str) -> dict[str, str]:
    return await page.evaluate(ROOT_VARS_JS, scope)


# ── putting the harness in each state ──

Drive = Callable[[Page], Awaitable[None]]


async def wait(page: Page, ms: int) -> None:
    await page.wait_for_timeout(ms)


async def keys(page: Page, *pressed: str, gap: int = 250) -> None:
    for key in pressed:
        await page.keyboard.press(key)
        await wait(page, gap)


async def select_passage(page: Page, text: str) -> None:
    await page.evaluate("""(text) => { const p = [...document.querySelectorAll('[data-desk-window="fx_w_book"] [data-span-id]')].find((e) => e.textContent.includes(text));
      const range = document.createRange(); range.selectNodeContents(p); const sel = getSelection(); sel.removeAllRanges(); sel.addRange(range); }""", text)


async def scroll_book(page: Page, by: int) -> None:
    await page.evaluate("""(by) => { const sc = [...document.querySelectorAll('[data-desk-window="fx_w_book"] *')].find((e) => e.scrollHeight > e.clientHeight + 20); if (sc) sc.scrollTop += by; }""", by)


async def pads_in_view(page: Page) -> None:
    """The pad stack is the first desk's last window: walk the focus to it."""
    await keys(page, *["Alt+l"] * 6)
    await page.wait_for_selector(".desk-pads [data-block]")
    await wait(page, 900)


async def pads_beside_book(page: Page) -> None:
    """The mockup's pads sit beside the book: move the stack left until it is the book's neighbour."""
    await pads_in_view(page)
    # Move the stack left until it is second on the strip, just right of the book.
    for _ in range(8):
        # The strip's order from the windows' places (the shelf's rows are gone below 1400 px, where it is a rail).
        place = await page.evaluate("""() => { const ws = [...document.querySelectorAll('[data-desk-window]')].filter((p) => p.dataset.windowState !== 'hidden')
            .sort((a, b) => a.closest('.desk-window').getBoundingClientRect().x - b.closest('.desk-window').getBoundingClientRect().x);
          return ws.findIndex((p) => p.querySelector('.desk-pads')); }""")
        if place <= 1:
            break
        await keys(page, "Alt+BracketLeft")
    # The book takes the focus again, as in the mockup: the camera then shows the book left, the pads right.
    await keys(page, "Alt+h")
    await wait(page, 1500)


async def d_plain(page: Page) -> None:
    return None


async def d_desk1(page: Page) -> None:
    await page.get_by_role("button", name="attention", exact=True).click()
    await wait(page, 1500)


async def d_focus3(page: Page) -> None:
    await keys(page, "Alt+l", "Alt+l", "Alt+l")
    await wait(page, 700)


async def d_move(page: Page) -> None:
    await keys(page, "Alt+BracketRight")
    await wait(page, 700)


async def d_zoom_after(page: Page) -> None:
    await keys(page, "Alt+Enter")
    await wait(page, 700)


async def d_fs150(page: Page) -> None:
    await keys(page, "Alt+Enter")
    await wait(page, 500)
    await keys(page, *["Equal"] * 5, gap=120)
    await wait(page, 400)


async def d_ov(page: Page) -> None:
    await keys(page, "Alt+o")
    await wait(page, 900)


async def d_ovn_far(page: Page) -> None:
    await d_ov(page)
    await keys(page, *["l"] * 8, gap=120)
    await wait(page, 600)


async def d_ovn_down(page: Page) -> None:
    await d_ov(page)
    await keys(page, "j", "j", gap=200)
    await wait(page, 600)


async def d_scrub(page: Page) -> None:
    await page.evaluate("() => { window.__deskDebug.beginZoom(); window.__deskDebug.setZoomProgress(0.5); }")
    await wait(page, 300)


async def d_ovg(page: Page) -> None:
    await d_ov(page)
    await page.keyboard.down("g")
    await wait(page, 500)


async def d_roundtrip(page: Page) -> None:
    await d_ov(page)
    await keys(page, "Escape")
    await wait(page, 900)


async def d_lap_open(page: Page) -> None:
    await page.get_by_role("button", name="show the strip").click()
    await wait(page, 400)


async def d_lap_comp(page: Page) -> None:
    await d_shiftc(page)


async def ask(page: Page) -> None:
    """The mockup's companion shows a thread; the fixture's starts empty, so one question is asked and answered."""
    box = page.locator(".desk-companion .input")
    if await box.count() and await box.is_enabled():
        await box.fill("why does the largest score win?")
        await box.press("Enter")
        await page.wait_for_selector('.desk-companion [data-exchange-status="answered"]', timeout=8000)
        # A focused input draws its focus border and keeps the desk's keys from the router.
        await page.evaluate("() => document.activeElement?.blur()")
        await wait(page, 300)


async def d_cur_sel(page: Page) -> None:
    # Not asked: asking takes the selection chip into the question, and the chip is what this state shows.
    await select_passage(page, "largest score")
    await keys(page, "c")
    await wait(page, 500)


async def d_cur_handoff(page: Page) -> None:
    await select_passage(page, "Adding the same constant")
    await keys(page, "c")
    await wait(page, 400)
    await ask(page)
    await scroll_book(page, 240)
    await wait(page, 700)


async def d_shiftc(page: Page) -> None:
    await keys(page, "Shift+C")
    await wait(page, 500)
    await ask(page)


async def d_dock_right(page: Page) -> None:
    await d_shiftc(page)
    stage = await page.evaluate("() => { const r = document.querySelector('[data-desk-stage]').getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width }; }")
    grab = await page.locator(".desk-companion .grab").bounding_box()
    if grab:
        await page.mouse.move(grab["x"] + grab["width"] / 2, grab["y"] + 4)
        await page.mouse.down()
        await page.mouse.move(stage["x"] + stage["w"] - 120, stage["y"] + 120, steps=8)
        await page.mouse.up()
    await wait(page, 600)


async def d_cov(page: Page) -> None:
    await d_shiftc(page)
    await d_ov(page)


async def d_hist(page: Page) -> None:
    await d_shiftc(page)
    await page.locator(".desk-companion .ctabs button", has_text="history").click()
    await wait(page, 600)


async def d_selctx(page: Page) -> None:
    await select_passage(page, "largest score")
    await keys(page, "Shift+C")
    await wait(page, 500)


async def d_spot(page: Page) -> None:
    await keys(page, "/")
    await page.keyboard.type("softmax")
    await wait(page, 4200)


async def d_switch(page: Page) -> None:
    # Below 1400 px the shelf is a rail: its ☰ shows the strip, whose heading has the switch.
    if not await page.get_by_role("button", name="/ switch").is_visible():
        await d_lap_open(page)
    await page.get_by_role("button", name="/ switch").click()
    await wait(page, 500)


async def d_run(page: Page) -> None:
    await pads_beside_book(page)


async def d_tabs_distance(page: Page) -> None:
    await pads_beside_book(page)
    geo = await page.evaluate("""() => { const s = document.querySelector('.desk-pads .pscroller'); const p = document.querySelectorAll('.desk-pads .paper')[1]; return { top: p.offsetTop, h: s.clientHeight }; }""")
    await page.locator(".desk-pads .pscroller").evaluate("(s, y) => { s.scrollTop = y; }", max(0, geo["top"] - geo["h"] * 0.6))
    await wait(page, 500)


async def d_lesson_tab(page: Page) -> None:
    """The mockup's lesson tab open in the stack beside the book: scroll the stack until the lesson's paper is the
    open one (the fixture's stack has two pads above it where the mockup has three)."""
    await pads_beside_book(page)
    await page.wait_for_selector('.desk-pads .paper[data-pad="lesson:fx_lesson_softmax"] [data-testid="lesson-view"]')
    await page.locator(".desk-pads .pscroller").evaluate(
        "(s) => { const p = s.querySelector('.paper[data-pad=\"lesson:fx_lesson_softmax\"]'); s.scrollTop = Math.max(0, p.offsetTop - 2 * 30 - 30); }")
    await wait(page, 700)


async def d_lift(page: Page) -> None:
    await pads_beside_book(page)
    await page.locator('.desk-pads [data-block="fx_b_r7"]').hover()
    await page.locator('.desk-pads [data-block="fx_b_r7"] .lift').click()
    await wait(page, 600)
    await page.mouse.move(5, 5)


async def d_sketch(page: Page) -> None:
    await pads_beside_book(page)
    await keys(page, "Alt+l", "Alt+d")
    await wait(page, 500)


async def d_info(page: Page) -> None:
    await pads_beside_book(page)
    # Its ⓘ sits in the pad stack's title bar ("Scratchpads ⓘ yours").
    await page.locator(".desk-window:has(.desk-pads) .desk-pane-head .pinfo").click()
    # The mockup's link opens it without a pointer over the ⓘ: leave its hover state out of the measure.
    await page.mouse.move(5, 5)
    await wait(page, 300)


async def d_submitted(page: Page) -> None:
    await pads_beside_book(page)
    await page.locator('.desk-pads [data-block="fx_b_r4"]').scroll_into_view_if_needed()
    await wait(page, 300)


async def d_append(page: Page) -> None:
    await pads_beside_book(page)
    await page.locator(".desk-pads .pscroller").evaluate("(s) => { s.scrollTop = s.scrollHeight; }")
    await wait(page, 400)


async def d_markback(page: Page) -> None:
    await pads_beside_book(page)
    marks = page.locator(".desk-pmark.pad")
    if await marks.count():
        await marks.first.click()
        await wait(page, 250)


async def d_backlink(page: Page) -> None:
    await pads_beside_book(page)
    back = page.locator(".desk-pads .back")
    if await back.count():
        await back.first.click()
        await wait(page, 600)
    # The pointer leaves the § row, or its hover (dark row, white text) is what gets measured.
    await page.mouse.move(5, 5)
    await wait(page, 300)


async def menu_settled(page: Page) -> None:
    # The cheap rows come at once; the judged rows through the job on the poller (two reads, about 3 s).
    await page.wait_for_selector(".desk-menu")
    await wait(page, 3600)


async def d_menu_cue(page: Page) -> None:
    # The first desk's video window shows its transcript beside the book.
    cue = page.locator("[data-transcript-span]:visible").first
    await cue.click(button="right")
    await menu_settled(page)


async def d_menu_hl(page: Page) -> None:
    # The fixture's book has no saved highlight: a passage's menu stands for it (the same menu, headed "a passage").
    await page.locator('[data-desk-window="fx_w_book"] [data-span-id]').nth(2).click(button="right", position={"x": 60, "y": 8})
    await menu_settled(page)


async def d_menu_selection(page: Page) -> None:
    await select_passage(page, "largest score")
    target = page.locator('[data-desk-window="fx_w_book"] [data-span-id]').filter(has_text="largest score").first
    await target.click(button="right", position={"x": 60, "y": 8})
    await menu_settled(page)


async def d_arrange(page: Page) -> None:
    await pads_beside_book(page)
    await keys(page, "Alt+l", "Alt+a")
    await wait(page, 300)


async def d_split(page: Page) -> None:
    await d_arrange(page)
    await keys(page, "Enter")
    await wait(page, 500)


# The goal lens (RD6) on the synthetic goal: the book focused, its first section in view.
GOAL_BOOK = "[data-desk-window='fx_w_book']"


async def goal_ready(page: Page) -> None:
    await page.wait_for_selector(".goalband")
    await page.locator(f"{GOAL_BOOK} [data-span-id='fx_ext_softmax_s1_2']").scroll_into_view_if_needed()
    await wait(page, 900)


async def goal_hover(page: Page, selector: str) -> None:
    """Hover a mark that is not the first of its kind: the first stays at rest for its own comparison (the reference
    opens its why from code, with no pointer over the mark)."""
    mark = page.locator(selector).nth(1)
    await mark.scroll_into_view_if_needed()
    await wait(page, 300)
    await mark.hover()
    await wait(page, 500)


async def d_goal_frame(page: Page) -> None:
    await goal_ready(page)


async def d_goal_why(page: Page) -> None:
    await goal_ready(page)
    await goal_hover(page, f"{GOAL_BOOK} .gm.gl-core")


async def d_goal_whysup(page: Page) -> None:
    await goal_ready(page)
    await goal_hover(page, f"{GOAL_BOOK} .gm.gl-sup")


async def d_goal_whyskip(page: Page) -> None:
    await goal_ready(page)
    await goal_hover(page, f"{GOAL_BOOK} .gm.gl-skip")


async def d_goal_basics(page: Page) -> None:
    await goal_ready(page)
    await page.click("[data-gdepth='get_the_idea']")
    await wait(page, 1200)
    await goal_hover(page, f"{GOAL_BOOK} .gm.gl-later")


async def d_goal_path(page: Page) -> None:
    await goal_ready(page)
    await page.mouse.click(700, 500)
    await keys(page, "p")
    await wait(page, 600)


async def d_goal_paper(page: Page) -> None:
    await goal_ready(page)
    # The note is the desk's third window (the shelf is a rail on the laptop): walk the focus to it.
    await keys(page, "Alt+l", "Alt+l")
    await wait(page, 1800)


async def d_goal_pads(page: Page) -> None:
    await goal_ready(page)
    await pads_in_view(page)


async def d_goal_video(page: Page) -> None:
    """The video window focused, its transcript's head in view (the reference's #goal=video)."""
    await goal_ready(page)
    await keys(page, "Alt+l")
    await wait(page, 1200)


async def d_goal_companion(page: Page) -> None:
    await goal_ready(page)
    await keys(page, "Shift+C")
    await wait(page, 900)


async def d_goal_nodim(page: Page) -> None:
    await goal_ready(page)
    await page.click("[data-gdim]")
    await page.mouse.move(700, 600)
    await wait(page, 500)
# ── pen and ink (RD8a): pen mode on, then one synthetic pen stroke (pointer events with pointerType "pen", pressure
# and tilt) drawn on the book's text with the mockup's own stroke shapes (st_16.js: strokeUnder, strokeStrike,
# strokeBracket, strokeLasso, strokeScribble), through the same input and recognizer a real pen goes through.
PEN_STROKE_JS = r"""
(kind) => {
  const win = document.querySelector('[data-desk-window="fx_w_book"]');
  const body = win.querySelector('[data-pen-host]');
  const ps = [...win.querySelectorAll('[data-span-id]')].filter((p) => p.getBoundingClientRect().width > 100 && (p.textContent || '').trim().split(/\s+/).length > 12);
  const jit = (i, a = 1.2) => Math.sin(i * 2.3) * a;
  const words = (p, from, n) => {
    const w = document.createTreeWalker(p, NodeFilter.SHOW_TEXT);
    for (let node = w.nextNode(); node; node = w.nextNode()) {
      const parts = [...node.data.matchAll(/\S+/g)];
      for (let k = from; k + n <= parts.length; k++) {
        const r = document.createRange(); r.setStart(node, parts[k].index); r.setEnd(node, parts[k + n - 1].index + parts[k + n - 1][0].length);
        const rs = [...r.getClientRects()]; if (rs.length === 1) return rs;
      }
    }
    return [];
  };
  let pts = []; let target = ps[1];
  if (kind === 'underline') { const rect = words(ps[1], 2, 6)[0]; for (let x = rect.left; x <= rect.right; x += 6) pts.push([x, rect.bottom + 2 + jit(x)]); }
  if (kind === 'strike') { target = ps[2]; const rect = words(ps[2], 2, 5)[0]; const y = rect.top + rect.height * .55; for (let x = rect.left; x <= rect.right; x += 6) pts.push([x, y + jit(x, .8)]); }
  if (kind === 'bracket') { target = ps[3]; const r = ps[3].getBoundingClientRect(); const x = r.left - 22; pts.push([x + 10, r.top + 4]); for (let y = r.top + 4; y <= r.bottom - 4; y += 8) pts.push([x + jit(y, 1), y]); pts.push([x + 10, r.bottom - 4]); }
  if (kind === 'note') { const r = ps[1].getBoundingClientRect(); const side = ps[2].getBoundingClientRect(); const x = r.right + 28, y = Math.min(side.bottom + 30, r.bottom + 40), w = 170;
    for (let t = 0; t < 1; t += .006) pts.push([x + t * w, y + Math.sin(t * 60) * 7 + Math.sin(t * 13) * 3]); }
  if (kind === 'lasso') { const rs = words(ps[1], 3, 4); const f = rs[0], l = rs[rs.length - 1], P = 5;
    const seg = (a, b) => { for (let t = 0; t < 1; t += .08) pts.push([a[0] + (b[0] - a[0]) * t + jit(pts.length * 3, 1.5), a[1] + (b[1] - a[1]) * t + jit(pts.length * 5, 1.5)]); };
    const L = Math.min(...rs.map((r) => r.left)) - P, R = Math.max(...rs.map((r) => r.right)) + P;
    const c = [[f.left - P, f.top - P], [R, f.top - P], [R, l.top - P], [l.right + P, l.top - P], [l.right + P, l.bottom + P], [L, l.bottom + P], [L, f.bottom + 1], [f.left - P, f.bottom + 1], [f.left - P + 4, f.top - P]];
    for (let i = 0; i < c.length - 1; i++) seg(c[i], c[i + 1]); pts.push([f.left - P + 6, f.top - P - 2]); }
  const fire = (type, [x, y], i) => target.dispatchEvent(new PointerEvent(type, { bubbles: true, cancelable: true, composed: true, pointerId: 7, pointerType: 'pen', isPrimary: true,
    clientX: x, clientY: y, pressure: type === 'pointerup' ? 0 : .45 + .1 * Math.sin(i), tiltX: 18, tiltY: -9, button: type === 'pointermove' ? -1 : 0, buttons: type === 'pointerup' ? 0 : 1 }));
  fire('pointerdown', pts[0], 0); pts.slice(1).forEach((p, i) => fire('pointermove', p, i + 1)); fire('pointerup', pts[pts.length - 1], pts.length);
  return { body: !!body, points: pts.length };
}
"""


async def d_pen_pad(page: Page) -> None:
    """The handwritten pad beside the book, open, in pen mode."""
    await pads_beside_book(page)
    await keys(page, "Alt+p")
    tab = page.locator('[data-pad-tab="fx_pad_hand"]')
    await tab.click()
    await wait(page, 900)


def d_pen(kind: str) -> Drive:
    async def drive(page: Page) -> None:
        await keys(page, "Alt+p")
        await page.locator('[data-desk-window="fx_w_book"] [data-pen-host]').wait_for(timeout=8000)
        await page.evaluate(PEN_STROKE_JS, kind)
        await wait(page, 900)
    return drive


@dataclass(frozen=True)
class State:
    name: str  # the mockup's deep link, without '#'
    stage: str
    drive: Drive
    regions: tuple[str, ...]
    viewports: tuple[str, ...] = ("design", "laptop")
    variant: str = "arxiv_v2"
    init_storage: tuple[tuple[str, str], ...] = ()
    note: str = ""
    # The harness page's query, with its "?" (the goal lens is `?goal=1`; the ink pad's fixture `?inkpad=1`).
    query: str = ""
    geometry: bool = True  # False where the mockup's state is not a resting layout (its self-tests run on)


SHELL = ("topbar", "brand", "desk_tab_on", "desk_tab", "top_chip", "shelf", "shelf_head", "shelf_switch", "shelf_row_focus",
         "shelf_row_kind", "shelf_row_name", "shelf_row_where", "shelf_row_bar_line", "shelf_row_bar_read", "shelf_row_inview",
         "shelf_row_other", "shelf_lower_head", "shelf_carried_head", "shelf_carried_item", "stage", "sliver_right", "sliver_left",
         "sliver_glyph", "sliver_title", "footer", "footer_hint", "footer_kbd", "footer_dot_focus", "footer_dot_inview", "footer_dot",
         "footer_note")
WINDOWS = ("window_focus", "window_focus_head", "window_focus_glyph", "window_focus_title", "window_focus_loc", "window_focus_close",
           "window_other", "window_other_head", "book_paper", "book_prose", "book_heading", "video_paper", "video_cue")
OVERVIEW = ("ov_label", "ov_ring_sel", "ov_ring_rel", "ov_card", "ov_card_sel", "ov_card_glyph", "ov_card_name", "ov_card_bar", "ov_link", "ov_link_label",
            "ov_ghost", "hud", "comp_pill")
COMPANION = ("comp_panel", "comp_grab", "comp_tabs", "comp_tab_on", "comp_tab", "comp_ctx", "comp_earlier", "comp_body", "comp_bub_you",
             "comp_bub_you_who", "comp_bub_ai", "comp_bub_ai_who", "comp_bub_ai_text", "comp_claim", "comp_chip", "comp_chip_quote", "comp_input",
             "comp_closed_tab", "comp_pill")
# The selection chip is measured before a question is asked, the thread's bubbles after (asking takes the chip).
COMPANION_CHIP = tuple(n for n in COMPANION if not n.startswith(("comp_bub", "comp_claim")))
COMPANION_THREAD = tuple(n for n in COMPANION if not n.startswith("comp_chip"))
HISTORY = ("hist_note", "hist_day", "hist_desk", "hist_q", "hist_a")
SEARCH = ("search_backdrop", "search_panel", "search_input", "search_input_field", "search_group_head", "search_row", "search_row_where",
          "search_sel", "search_row_sel_text", "search_foot")
PEN = ("pen_chip_top", "pen_sim_top", "pen_hint", "pen_hint_kbd", "pen_text_cursor", "pen_chip", "pen_chip_text", "pen_chip_undo", "pen_chip_x")
PADS = ("pad_window_head", "pad_tab_open", "pad_tab", "pad_tab_title", "pad_tab_label", "pad_tab_meta", "pad_paper", "pad_day",
        "pad_prose", "pad_quote", "pad_backlink", "pad_tutor", "pad_tutor_who", "pad_submitted", "pad_carry", "pad_jot", "pad_mark_src",
        "pad_mark_ll", "pad_mark_fig")

MENU = ("pad_menu", "pad_menu_row", "pad_menu_head", "auto:div.pro", "auto:span.why")
LESSON = ("lesson_body", "lesson_head", "lesson_head_glyph", "lesson_head_faint", "lesson_mode_on", "lesson_mode", "lesson_mode_line",
          "lesson_frame", "pad_window_head", "pad_tab_open", "pad_tab_title", "pad_tab_meta")

GOAL_BAND = ("goal_band", "goal_band_lab", "goal_band_sentence", "goal_band_counts", "goal_band_dot", "goal_band_dot_likely",
             "goal_band_dot_pre", "goal_band_dot_unmatched", "goal_band_depth_on", "goal_band_depth", "goal_band_here_lab", "goal_band_here",
             "goal_band_next_lab", "goal_band_next", "goal_band_dim", "goal_band_path")
GOAL_MARKS = ("goal_mark_core", "goal_mark_sup", "goal_mark_skip", "goal_text_dimmed")
GOAL_SHELF = ("goal_shelf_row", "goal_shelf_mark_core", "goal_shelf_mark_sup", "goal_shelf_mark_skip", "goal_shelf_line", "goal_shelf_line_skip",
              "goal_shelf_range")
GOAL_VIDEO = ("goal_transcript_mark", "goal_transcript_dimmed", "goal_transcript_head", "goal_transcript_head_off", "goal_track",
              "goal_track_line", "goal_track_seg")
GOAL_WHY = ("goal_why", "goal_why_head", "goal_why_body", "goal_why_for", "goal_why_coverage", "goal_mark_on", "goal_mark_later")
GOAL_PATH = ("goal_path", "goal_path_left", "goal_path_h3", "goal_path_scope", "goal_path_unmatched", "goal_path_depth_on", "goal_path_depth",
             "goal_path_ready", "goal_path_key", "goal_path_head", "goal_path_lo", "goal_path_lo_title", "goal_path_tag_core", "goal_path_tag_pre",
             "goal_path_dot", "goal_path_primary", "goal_path_primary_src", "goal_path_primary_at", "goal_path_primary_why", "goal_path_alt",
             "goal_path_skip", "goal_path_skip_head")

STATES: list[State] = [
    State("plain", "rd1", d_plain, SHELL + WINDOWS + ("comp_panel", "comp_closed_tab")),
    State("desk=1", "rd1", d_desk1, SHELL + WINDOWS),
    State("focus=3", "rd1", d_focus3, SHELL + WINDOWS),
    State("move", "rd1", d_move, SHELL + WINDOWS),
    State("zoom=after", "rd1", d_zoom_after, ("window_focus", "window_focus_head", "focus_badge", "book_paper", "book_prose", "topbar")),
    State("s11=fs150", "rd1", d_fs150, ("window_focus", "window_focus_head", "focus_badge", "book_paper", "book_prose", "topbar")),
    State("ov", "rd2", d_ov, SHELL + OVERVIEW),
    State("ovn=far", "rd2", d_ovn_far, OVERVIEW),
    State("ovn=down", "rd2", d_ovn_down, OVERVIEW),
    State("scrub=0.5", "rd2", d_scrub, ("stage", "window_focus", "ov_card", "ov_label", "comp_panel")),
    State("ovg", "rd2", d_ovg, OVERVIEW),
    State("selftest", "rd2", d_roundtrip, SHELL + WINDOWS, note="the mockup's self-test is still running when captured", geometry=False),
    State("selftest2", "rd2", d_roundtrip, SHELL + WINDOWS, note="the mockup's self-test is still running when captured", geometry=False),
    State("lap=1", "rd2", d_plain, SHELL + WINDOWS + ("shelf_rail",), viewports=("laptop",)),
    State("lap=open", "rd2", d_lap_open, SHELL + ("shelf_rail", "shelf_overlay"), viewports=("laptop",)),
    State("cur=sel", "rd3", d_cur_sel, COMPANION_CHIP),
    State("cur=handoff", "rd3", d_cur_handoff, COMPANION_THREAD),
    State("cur=shiftc", "rd3", d_shiftc, COMPANION_THREAD),
    State("dock=right", "rd3", d_dock_right, COMPANION_THREAD, note="the mockup's link leaves the panel at its default dock", geometry=False),
    State("cov", "rd3", d_cov, OVERVIEW),
    State("hist", "rd3", d_hist, COMPANION_THREAD + HISTORY),
    State("selctx", "rd3", d_selctx, COMPANION_CHIP),
    State("spot=softmax", "rd3", d_spot, SEARCH),
    State("switch", "rd3", d_switch, SEARCH),
    State("lap=comp", "rd3", d_lap_comp, COMPANION_THREAD + ("shelf_rail",), viewports=("laptop",)),
    State("s11=run", "rd4", d_run, PADS),
    State("tabs=distance,pad=2,padf=0.4", "rd4", d_tabs_distance, PADS),
    State("tabs=order", "rd4", d_run, PADS, init_storage=(("learnloop.desks.tabGrade", "order"),)),
    State("s11=lift", "rd4", d_lift, PADS + ("pad_lifted",)),
    State("s11=sketchqk", "rd4", d_sketch, PADS + ("sketch_bar", "sketch_tool", "sketch_canvas")),
    State("s12=info", "rd4", d_info, PADS + ("pad_info_pop", "pad_info_button")),
    State("s12=submitted", "rd4", d_submitted, PADS),
    State("append", "rd4", d_append, PADS),
    State("markback", "rd4", d_markback, PADS + ("pass_mark_pad", "pad_flash")),
    State("backlink", "rd4", d_backlink, PADS + ("book_prose",)),
    # The mockup's #s11=menu is a selection's menu over the book: RD5's menu (the pad line's menu is the same one).
    State("s11=menu", "rd5", d_menu_selection, MENU),
    State("menu=cue", "rd5", d_menu_cue, MENU),
    State("menuhl", "rd5", d_menu_hl, MENU),
    State("s11=arrange", "rd4", d_arrange, ("arrange_panel", "arrange_card", "pad_window_head")),
    State("s11=split", "rd4", d_split, PADS + ("split_pane",)),
    State("goal=frame", "rd6", d_goal_frame, GOAL_BAND + GOAL_MARKS + GOAL_SHELF + ("goal_callout", "goal_callout_lab"), variant="arxiv_v2_goal", query="?goal=1"),
    State("goal=why", "rd6", d_goal_why, GOAL_BAND + GOAL_MARKS + GOAL_WHY, variant="arxiv_v2_goal", query="?goal=1"),
    State("goal=whysup", "rd6", d_goal_whysup, GOAL_BAND + GOAL_MARKS + GOAL_WHY, variant="arxiv_v2_goal", query="?goal=1"),
    State("goal=whyskip", "rd6", d_goal_whyskip, GOAL_BAND + GOAL_MARKS + GOAL_WHY, variant="arxiv_v2_goal", query="?goal=1"),
    State("goal=basics", "rd6", d_goal_basics, GOAL_BAND + GOAL_MARKS + GOAL_WHY + ("goal_band_dot_later",), variant="arxiv_v2_goal", query="?goal=1"),
    State("goal=path", "rd6", d_goal_path, GOAL_BAND + GOAL_PATH, variant="arxiv_v2_goal", query="?goal=1"),
    State("goal=paper", "rd6", d_goal_paper, GOAL_BAND + ("goal_paper_mark", "goal_paper_callout"), variant="arxiv_v2_goal", query="?goal=1"),
    State("goal=pads", "rd6", d_goal_pads, GOAL_BAND + ("goal_pad_line",), variant="arxiv_v2_goal", query="?goal=1"),
    State("goal=frame,nodim", "rd6", d_goal_nodim, GOAL_BAND + GOAL_MARKS + GOAL_SHELF, variant="arxiv_v2_goal", query="?goal=1"),
    State("goal=video", "rd6", d_goal_video, GOAL_BAND + GOAL_SHELF + GOAL_VIDEO, variant="arxiv_v2_goal", query="?goal=1"),
    # The companion's context line keeping the goal in view: the reference shows it with the companion open at its
    # check (RD7's); only the companion's line is compared here.
    State("goal=check", "rd6", d_goal_companion, ("goal_comp_ctx", "comp_ctx"), variant="arxiv_v2_goal", query="?goal=1",
          note="only the companion's context line; the check itself is RD7's"),
    State("pen=underline", "rd8", d_pen("underline"), PEN + ("pen_stroke_under", "pen_mark_hl")),
    State("pen=bracket", "rd8", d_pen("bracket"), PEN + ("pen_stroke_bracket", "pen_mark_para")),
    State("pen=note", "rd8", d_pen("note"), PEN + ("pen_stroke_note", "pen_note", "pen_note_who", "pen_note_text", "pen_note_label")),
    State("pen=lasso", "rd8", d_pen("lasso"), PEN + ("pen_stroke_lasso", "pen_mark_sel", "pen_chip_ask")),
    State("pen=strike", "rd8", d_pen("strike"), PEN + ("pen_stroke_strike",)),
    State("pen=pad", "rd8", d_pen_pad, ("pen_chip_top", "pen_hint", "ink_pad_paper", "ink_bar", "ink_bar_button", "ink_prov", "ink_read",
                                         "ink_read_label", "ink_read_tex", "ink_hint", "pad_window_head", "pad_tab_open"), query="?inkpad=1"),
    # The Teacher lesson's tab open in the stack (RD9a). The reference was captured with the notebook served: its
    # frame holds the notebook, ours the lesson itself (RD9b brings the notebook), so the frame is compared as a box.
    State("tabs=distance,pad=3", "rd9", d_lesson_tab, LESSON, query="?lesson=1",
          note="the frame's content is the notebook in the reference and the lesson itself here (RD9b)"),
]

STATE_BY_NAME = {state.name: state for state in STATES}


def file_stem(variant: str, state: str, viewport: str) -> str:
    """The reference's file name for one capture: safe on every file system, readable in a listing."""
    return f"{variant}__{re.sub(r'[^A-Za-z0-9_.-]+', '_', state) or 'plain'}__{viewport}"


# ── diffing ──

COLOUR_KEYS = ("color", "background", "box_shadow", "outline", "stroke", "fill")
TYPE_KEYS = ("font_size", "font_weight", "font_style", "line_height", "letter_spacing", "text_transform")


def primary_family(stack: str) -> str:
    """The designed family a stack asks for first; the app's fonts are the variable cuts of the same faces."""
    first = stack.split(",")[0].strip().strip('"').strip("'")
    return re.sub(r"\s+Variable$", "", first)


def same_numbers(a: Any, b: Any) -> bool:
    """Two computed values that differ only past 0.05 px are the same value: the mockup works its world sizes
    out from 1/0.34 to more digits than the desks write (38.233 px and 38.2353 px, 4.4115 px and 4.41 px)."""
    if a == b:
        return True
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    pattern = r"-?\d+(?:\.\d+)?"
    na, nb = re.findall(pattern, a), re.findall(pattern, b)
    return len(na) == len(nb) and re.sub(pattern, "#", a) == re.sub(pattern, "#", b) and all(abs(float(x) - float(y)) < 0.05 for x, y in zip(na, nb, strict=True))


def px(value: str) -> float | None:
    match = re.fullmatch(r"(-?[\d.]+)px", value.strip())
    return float(match.group(1)) if match else None


def near(a: str, b: str) -> bool:
    pa, pb = px(a), px(b)
    if pa is not None and pb is not None:
        return abs(pa - pb) <= GEOMETRY_TOLERANCE_PX
    return a == b


def border_shown(facts: dict[str, Any], i: int, width: str) -> bool:
    """A border drawn in a transparent colour is no border on screen (it only reserves a highlight's room)."""
    colour = facts["border_color"][i]
    return facts["border_style"][i] != "none" and px(width) != 0 and not (len(colour) == 9 and colour.endswith("00"))


def diff_region(name: str, mock: dict[str, Any], app: dict[str, Any], geometry: bool = True) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    skip = REGIONS[name].skip

    def add(kind: str, prop: str, m: Any, a: Any) -> None:
        if prop in skip or (kind == "type" and "font" in skip) or (kind == "geometry" and not geometry):
            return
        if "border" in skip and prop.startswith("border_"):
            return
        rows.append({"region": name, "kind": kind, "prop": prop, "mockup": m, "app": a})

    for key in COLOUR_KEYS:
        if key in mock and not same_numbers(mock.get(key), app.get(key)):
            add("colour", key, mock.get(key), app.get(key))
    # A transparent background is compared by what shows through it.
    if mock.get("background") != app.get("background") and mock.get("background_eff") != app.get("background_eff"):
        add("colour", "background_eff", mock.get("background_eff"), app.get("background_eff"))
    for i, edge in enumerate(("top", "right", "bottom", "left")):
        mw, aw = mock["border_width"][i], app["border_width"][i]
        m_on, a_on = border_shown(mock, i, mw), border_shown(app, i, aw)
        if m_on != a_on or (m_on and not near(mw, aw)):
            add("geometry", f"border_{edge}_width", f"{mw if m_on else '0px'} {mock['border_style'][i]}", f"{aw if a_on else '0px'} {app['border_style'][i]}")
        if m_on and a_on and mock["border_color"][i] != app["border_color"][i]:
            add("colour", f"border_{edge}_color", mock["border_color"][i], app["border_color"][i])
    if primary_family(mock["font_family"]) != primary_family(app["font_family"]):
        add("type", "font_family", mock["font_family"], app["font_family"])
    for key in TYPE_KEYS:
        if not same_numbers(mock.get(key), app.get(key)) and not (key == "line_height" and near(str(mock.get(key)), str(app.get(key)))):
            add("type", key, mock.get(key), app.get(key))
    for key in ("radius", "padding"):
        if any(not near(m, a) for m, a in zip(mock[key], app[key], strict=True)):
            add("geometry", key, " ".join(mock[key]), " ".join(app[key]))
    geom = REGIONS[name].geom
    for k in GEOM_KEYS[geom]:
        if abs(mock["box"][k] - app["box"][k]) > GEOMETRY_TOLERANCE_PX:
            add("geometry", f"box.{k}", mock["box"][k], app["box"][k])
    if abs(mock["opacity_eff"] - app["opacity_eff"]) > 0.05:
        add("colour", "opacity", mock["opacity_eff"], app["opacity_eff"])
    if name in CURSOR_REGIONS and "cursor" in mock and mock.get("cursor") != app.get("cursor"):
        add("cursor", "cursor", mock.get("cursor"), app.get("cursor"))
    if "stroke_width" in mock and "stroke_width" in app and mock["stroke_width"] != app["stroke_width"]:
        add("colour", "stroke_width", mock["stroke_width"], app["stroke_width"])
    return rows


def diff_tokens(mock_vars: dict[str, str], app_vars: dict[str, str]) -> list[dict[str, Any]]:
    """The mockup's `--x` against the desks' `--desk-x`: a differing value is a finding; a token the desks lack
    is listed (the app may write the value literally where it is used)."""
    rows = []
    for name, value in sorted(mock_vars.items()):
        app_name = "--desk-" + name[2:]
        got = app_vars.get(app_name)
        norm = lambda v: re.sub(r"\s+", "", v or "").lower()  # noqa: E731
        if got is None:
            rows.append({"token": name, "kind": "absent", "mockup": value, "app": None})
        elif norm(got) != norm(value):
            rows.append({"token": name, "kind": "differs", "mockup": value, "app": got})
    return rows


def pixel_share(mock_png: Path, app_png: Path, side_by_side: Path) -> float:
    from PIL import Image, ImageChops, ImageDraw

    a = Image.open(mock_png).convert("RGB")
    b = Image.open(app_png).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size)
    diff = ImageChops.difference(a, b)
    # A pixel is changed when any channel is past the threshold.
    r, g, bl = diff.point(lambda v: 255 if v > PIXEL_THRESHOLD else 0).split()
    changed_img = ImageChops.lighter(ImageChops.lighter(r, g), bl)
    changed = sum(1 for v in changed_img.getdata() if v)
    share = changed / (a.size[0] * a.size[1])
    w, h = a.size
    sheet = Image.new("RGB", (w * 3 + 40, h + 28), (20, 20, 22))
    sheet.paste(a, (0, 28))
    sheet.paste(b, (w + 20, 28))
    heat = Image.new("RGB", a.size, (12, 12, 13))
    heat.paste((227, 160, 99), mask=changed_img)
    sheet.paste(heat, (2 * w + 40, 28))
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), "mockup", fill=(216, 216, 224))
    draw.text((w + 28, 8), "harness", fill=(216, 216, 224))
    draw.text((2 * w + 48, 8), f"changed pixels {share:.1%}", fill=(216, 216, 224))
    sheet.save(side_by_side)
    return share


# ── the run ──


async def open_harness(browser: Any, base: str, viewport: dict[str, int], state: State) -> Page:
    page = await browser.new_page(viewport=viewport)
    await page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(base) else route_outside(route))
    if state.init_storage:
        script = ";".join(f"localStorage.setItem({json.dumps(k)}, {json.dumps(v)})" for k, v in state.init_storage)
        await page.add_init_script(script)
    await page.goto(f"{base}/desk-harness.html{state.query}")
    await page.wait_for_selector("[data-desk-window]")
    await page.evaluate("document.fonts.ready")
    await page.wait_for_timeout(1500)
    await state.drive(page)
    return page


async def compare_state(browser: Any, base: str, ref: Path, out: Path, state: State, viewport: str) -> dict[str, Any]:
    stem = file_stem(state.variant, state.name, viewport)
    ref_json = ref / f"{stem}.json"
    if not ref_json.exists():
        return {"state": state.name, "viewport": viewport, "status": "no reference capture", "file": ref_json.name}
    reference = json.loads(ref_json.read_text())
    page = await open_harness(browser, base, VIEWPORTS[viewport], state)
    try:
        app_png = out / f"{stem}__harness.png"
        await page.screenshot(path=str(app_png))
        names = [n for n in state.regions if n in REGIONS]
        measured = await measure(page, {n: REGIONS[n].harness for n in names})
        app_vars = await root_vars(page, ".desk-shell")
        errors = await page.evaluate("() => window.__deskHarnessErrors || []")
    finally:
        await page.close()
    # Below 1400 px the mockup's shelf element itself narrows to the rail, where the desks swap in a rail element.
    shelf = reference["regions"].get("shelf")
    if shelf and shelf["box"]["w"] <= 60 and not reference["regions"].get("shelf_rail"):
        reference["regions"]["shelf_rail"], reference["regions"]["shelf"] = shelf, None
    rows: list[dict[str, Any]] = []
    missing, extra, unmapped = [], [], []
    for name in names:
        mock = reference["regions"].get(name, "unmapped")
        app = measured.get(name)
        if mock == "unmapped":
            unmapped.append(name)
        elif mock is None and app is None:
            continue
        elif mock is not None and app is None:
            missing.append(name)
        elif mock is None and app is not None:
            extra.append(name)
        elif "error" in mock or "error" in app:
            rows.append({"region": name, "kind": "error", "prop": "selector", "mockup": mock.get("error"), "app": app.get("error")})
        else:
            rows += diff_region(name, mock, app, state.geometry)
    share = pixel_share(ref / reference["screenshot"], app_png, out / f"{stem}__side_by_side.png")
    return {
        "state": state.name, "stage": state.stage, "viewport": viewport, "status": "compared",
        "link_applied": reference.get("link_applied"), "pixel_changed_share": round(share, 4),
        "missing_in_app": missing, "only_in_app": extra, "not_mapped_in_reference": unmapped,
        "differences": rows, "tokens": diff_tokens(reference.get("root_vars", {}), app_vars), "harness_errors": errors,
        "app": measured,
    }


async def dump(base: str, state: State, viewport: str) -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await open_harness(browser, base, VIEWPORTS[viewport], state)
        tree = await page.evaluate(r"""() => { const rows = []; const walk = (el, d) => { const cs = getComputedStyle(el); if (cs.display === 'none') return;
          const r = el.getBoundingClientRect(); const cls = typeof el.className === 'string' ? el.className.trim().split(/\s+/).filter(Boolean).join('.') : '';
          if (r.width >= 1 || r.height >= 1) rows.push('  '.repeat(d) + el.tagName.toLowerCase() + (cls ? '.' + cls : '') + ` [${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}]`);
          if (d < 22) for (const c of el.children) walk(c, d + 1); }; walk(document.body, 0); return rows.join('\n'); }""")
        print(tree)
        await browser.close()


def aggregate(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per distinct difference (region, property, mockup value, harness value), with the states and
    viewports it shows in: the same wrong colour on ten states is one finding."""
    rows: dict[tuple[str, ...], dict[str, Any]] = {}
    for r in results:
        if r["status"] != "compared":
            continue
        where = f"{r['state']} [{r['viewport']}]"
        for d in r["differences"]:
            key = (r["stage"], d["region"], d["kind"], d["prop"], json.dumps(d["mockup"]), json.dumps(d["app"]))
            rows.setdefault(key, {"stage": r["stage"], **d, "where": []})["where"].append(where)
        for name in r["missing_in_app"]:
            key = (r["stage"], name, "missing", "", "", "")
            rows.setdefault(key, {"stage": r["stage"], "region": name, "kind": "missing", "prop": "", "mockup": "shown", "app": "absent", "where": []})["where"].append(where)
    return sorted(rows.values(), key=lambda row: (row["stage"], row["region"], row["kind"], row["prop"]))


def summarise(results: list[dict[str, Any]]) -> str:
    lines = []
    for r in results:
        if r["status"] != "compared":
            lines.append(f"{r['state']} [{r['viewport']}]: {r['status']}")
            continue
        kinds: dict[str, int] = {}
        for row in r["differences"]:
            kinds[row["kind"]] = kinds.get(row["kind"], 0) + 1
        lines.append(f"{r['state']} [{r['viewport']}]: pixels changed {r['pixel_changed_share']:.1%}; missing {len(r['missing_in_app'])}; "
                     + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) + f"; token rows {len(r['tokens'])}")
    return "\n".join(lines)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ref", type=Path, required=True, help="the private reference directory")
    parser.add_argument("--stage", default="all", choices=["rd1", "rd2", "rd3", "rd4", "rd5", "rd6", "rd8", "rd9", "notebook", "all"])
    parser.add_argument("--state", default=None)
    parser.add_argument("--viewport", default="both", choices=["design", "laptop", "both"])
    parser.add_argument("--out", type=Path, default=None, help="where the comparison goes (default: <ref>/compare)")
    parser.add_argument("--dump", default=None, metavar="STATE")
    args = parser.parse_args()
    if args.stage == "notebook":
        # The notebook frame runs a real sandboxed session; its own harness compares the lesson state's frame.
        import subprocess

        return subprocess.call([sys.executable, str(Path(__file__).with_name("notebook.py")), "--ref", str(args.ref)])
    if not DIST.exists():
        print("build the harness page first: npx vite build --config vite.desks.config.mjs", file=sys.stderr)
        return 2
    server, port = serve(DIST)
    base = f"http://127.0.0.1:{port}"
    try:
        if args.dump:
            await dump(base, STATE_BY_NAME[args.dump], "design" if args.viewport == "both" else args.viewport)
            return 0
        if not args.ref.is_dir():
            print("no reference directory: run the private capture first", file=sys.stderr)
            return 2
        out = args.out or (args.ref / "compare")
        out.mkdir(parents=True, exist_ok=True, mode=0o700)
        chosen = [s for s in STATES if (args.state is None or s.name == args.state) and (args.stage == "all" or s.stage == args.stage)]
        results = []
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            for state in chosen:
                for viewport in state.viewports:
                    if args.viewport != "both" and viewport != args.viewport:
                        continue
                    try:
                        results.append(await compare_state(browser, base, args.ref, out, state, viewport))
                    except Exception as exc:  # a state the harness cannot reach is a finding, not the end of the run
                        results.append({"state": state.name, "stage": state.stage, "viewport": viewport, "status": f"not reachable: {str(exc).splitlines()[0][:160]}"})
            await browser.close()
        tag = args.state and re.sub(r"[^A-Za-z0-9_.-]+", "_", args.state) or args.stage
        (out / f"result__{tag}.json").write_text(json.dumps(results, indent=1, default=str))
        (out / f"findings__{tag}.json").write_text(json.dumps(aggregate(results), indent=1, default=str))
        print(summarise(results))
        print(f"wrote {len(results)} comparisons to {out}")
        return 0
    finally:
        server.shutdown()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
