"""The paper theme every notebook frame is served with (spec_reader_workbench_v2 §11.2).

Delivered by the frame proxy (a stylesheet link it adds to the page), never by editing a notebook, so a notebook
written outside LearnLoop looks like the workbench too. It sets marimo's own CSS variables (owner decision 13:
variables only, so a marimo update that renames a component class breaks nothing): the workbench's page paper and
surface, its ink and rules, Literata for prose and headings, JetBrains Mono for code; marimo's own text face for
its controls.
marimo's app view already keeps equal side margins (17 and 19 px in a 514 px frame against the mockup's 18 and
18). marimo's "Reconnected" banner is not styled away: the proxy drops the message that shows it.

The commit-point classes (``ll-commit``, ``ll-held``, ``ll-verdict``) are LearnLoop's own, for the commit gate a
notebook's SDK renders: a paper card with the purple voice edge, a held state, a verdict line.

The faces are the app's own (the ``@fontsource-variable`` packages the desktop app installs), served from the
frame's origin because its CSP allows fonts from nowhere else; where they are not installed, the stacks fall back
to the system's serif and monospace.
"""
from __future__ import annotations

import os
from pathlib import Path

#: The workbench's paper colours (desk.css tokens and the mockup's measured notebook): page, surface, ink, rule,
#: the purple voice.
PAGE = "#f7f5f0"
SURFACE = "#fdfdfc"
INK = "#1f1e1c"
INK_SOFT = "#55524c"
RULE = "#e3e0d8"
FRAME_RULE = "#dcd7cc"
PURPLE = "#5b4a9a"

#: The font files the theme serves (published name -> fontsource package and file).
FONT_FILES: dict[str, tuple[str, str]] = {
    "literata.woff2": ("literata", "literata-latin-wght-normal.woff2"),
    "literata-italic.woff2": ("literata", "literata-latin-wght-italic.woff2"),
    "jetbrains-mono.woff2": ("jetbrains-mono", "jetbrains-mono-latin-wght-normal.woff2"),
}
#: Where the faces are looked for when no directory is configured: the desktop app's installed packages.
FONT_PACKAGES_ENV = "LEARNLOOP_NOTEBOOK_FONTS_DIR"


def font_packages_dir() -> Path:
    configured = os.environ.get(FONT_PACKAGES_ENV)
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[3] / "apps" / "learnloop-tauri" / "node_modules" / "@fontsource-variable"


def font_file(name: str) -> Path | None:
    """The served font ``name``'s file, or None when it is not a theme font or not installed."""

    entry = FONT_FILES.get(name)
    if entry is None:
        return None
    path = font_packages_dir() / entry[0] / "files" / entry[1]
    return path if path.is_file() else None


def theme_css(base_url: str) -> str:
    fonts = f"{base_url}/__ll/fonts"
    prose = '"Literata Variable", "Literata", Georgia, serif'
    mono = '"JetBrains Mono Variable", "JetBrains Mono", ui-monospace, monospace'
    return f"""/* LearnLoop paper theme (served by the notebook proxy) */
@font-face {{ font-family: "Literata Variable"; font-style: normal; font-weight: 200 900; font-display: swap;
  src: url("{fonts}/literata.woff2") format("woff2-variations"), local("Literata"); }}
@font-face {{ font-family: "Literata Variable"; font-style: italic; font-weight: 200 900; font-display: swap;
  src: url("{fonts}/literata-italic.woff2") format("woff2-variations"), local("Literata Italic"); }}
@font-face {{ font-family: "JetBrains Mono Variable"; font-style: normal; font-weight: 100 800; font-display: swap;
  src: url("{fonts}/jetbrains-mono.woff2") format("woff2-variations"), local("JetBrains Mono"); }}
:root, :root.light, .light, .light-theme, .marimo, .marimo.light {{
  --background: {PAGE} !important;
  --foreground: {INK} !important;
  --card: {SURFACE} !important;
  --card-foreground: {INK} !important;
  --popover: {SURFACE} !important;
  --popover-foreground: {INK} !important;
  --muted: #efece5 !important;
  --muted-foreground: {INK_SOFT} !important;
  --border: {RULE} !important;
  --input: {FRAME_RULE} !important;
  --accent: #efece5 !important;
  --accent-foreground: {INK} !important;
  --primary: {PURPLE} !important;
  --primary-foreground: {SURFACE} !important;
  --ring: {PURPLE} !important;
  --marimo-heading-font: {prose} !important;
  --marimo-monospace-font: {mono} !important;
  --ll-page: {PAGE};
  --ll-surface: {SURFACE};
  --ll-ink: {INK};
  --ll-rule: {RULE};
  --ll-purple: {PURPLE};
}}
html, body {{ background: {PAGE} !important; color: {INK}; }}
/* marimo's prose (Markdown cells) takes its colours from the typography plugin's variables, set per element. */
.prose, .markdown {{
  /* Prose is Literata, like the books and pads; marimo's controls keep its own text face. */
  --text-font: {prose} !important;
  --marimo-text-font: {prose} !important;
  --tw-prose-body: {INK} !important;
  --tw-prose-headings: {INK} !important;
  --tw-prose-lead: {INK_SOFT} !important;
  --tw-prose-bold: {INK} !important;
  --tw-prose-links: {PURPLE} !important;
  --tw-prose-counters: {INK_SOFT} !important;
  --tw-prose-bullets: {FRAME_RULE} !important;
  --tw-prose-hr: {RULE} !important;
  --tw-prose-quotes: {INK_SOFT} !important;
  --tw-prose-quote-borders: {RULE} !important;
  --tw-prose-captions: {INK_SOFT} !important;
  --tw-prose-code: {INK} !important;
}}
/* LearnLoop's commit points (the SDK's commit gate renders these classes). */
.ll-commit {{ background: {SURFACE}; border: 1px solid {RULE}; border-left: 3px solid {PURPLE}; border-radius: 4px;
  padding: 10px 12px; font-family: {prose}; color: {INK}; }}
.ll-commit.ll-held {{ border-left-style: dashed; color: {INK_SOFT}; }}
.ll-verdict {{ margin-top: 6px; font: 12px {mono}; color: {PURPLE}; }}
"""
