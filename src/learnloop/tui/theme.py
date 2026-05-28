from __future__ import annotations

from textual.theme import Theme

# Custom theme variables that have no semantic-token equivalent. These must also
# be exposed via LearnLoopApp.get_theme_variable_defaults so they resolve at
# CSS-parse time (before on_mount registers the theme).
LEARNLOOP_VARIABLES = {
    "probe": "#dc7fb8",            # pink — probe phase / transfer mode
    "border-blurred": "#2d2e42",   # default card border
    "footer-key-foreground": "#e3a063",
}

LEARNLOOP_THEME = Theme(
    name="learnloop",
    primary="#e3a063",      # amber — brand, focus borders, "good"
    secondary="#5a4d8a",    # muted purple — short_answer, generic chips
    accent="#6ad0e0",       # cyan — evidence facets, "explanation"
    foreground="#d8d8e0",   # body text
    background="#15161f",   # app background
    surface="#1c1d2a",      # elevated strips/cards
    panel="#11121b",        # inset inputs / answer editor
    success="#7fd28f",      # high mastery, "easy", worked_problem
    warning="#dccd5a",      # difficulty, "hard"
    error="#e07e7e",        # low mastery, "again", fatal errors
    dark=True,
    variables=dict(LEARNLOOP_VARIABLES),
)
