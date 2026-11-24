"""Owner-side additions to installed API facts. One entry per tool with a gap."""

TOOL_NOTES = {
    'mo.App': {},
    'mo.accordion': {},
    'mo.callout': {},
    'mo.hstack': {},
    'mo.vstack': {},
    'mo.image_compare': {},
    'mo.persistent_cache': {},
    'mo.state': {},
    'mo.stop': {},
    'mo.tabs': {},
    'mo.md': {'gotcha': 'Keep authored prose and LaTeX out of batch format strings.'},
    'mo.center': {'gotcha': 'Centering can shrink a widget below its intended width.'},
    'mo.ui.anywidget': {'gotcha': 'Wrap a widget to make synced value reads reactive.'},
    'mo.ui.table': {'gotcha': 'Small learner-facing tables can use Markdown to avoid extra controls.'},
    'TangleLatex': {'typed_alternative': 'Enter the named parameter values.',
                    'static_fallback': 'Render the formula at the selected parameters.'},
    'TangleChoice': {'affordance': 'Switch between discrete assumptions.'},
    'TangleSelect': {'affordance': 'Select a discrete case.'},
    'FormulaAnimation': {'gotcha': 'Check long math at the actual stage size and inspect subscripts. '
                                  'Off-stage steps are intentionally hidden.'},
    'StateViewer': {'gotcha': 'Use for discrete changes in state. Complex HTML is flattened.'},
    'WidgetFlow': {'gotcha': 'Use distinct widget instances in a marimo session and check edge-label overlap.'},
    'Hint': {'gotcha': 'Requires a running marimo session.'},
    'LiveEdit': {'gotcha': 'Check the table width in the rendered cell.'},
    'TextCompare': {'gotcha': 'Highlights shared text runs. Supply explicit insertions and deletions for a diff.'},
    'shape_display': {'gotcha': 'Requires two or three axes.'},
    'KeystrokeWidget': {'check': 'Use local process data only with learner opt-in.'},
    'ManimWeb': {'check': 'Use trusted animation templates only.'},
    'mo.sql': {'requires': ['duckdb']},
    'mo.ui.altair_chart': {'requires': ['altair']},
    'mo.ui.plotly': {'requires': ['plotly']},
    'mo.ui.matplotlib': {'requires': ['matplotlib']},
}

RECIPES = {
    'commit-gate': 'Bind a distinct public name to each ll.commit(input, prompt=..., response=..., facets=...). '
                   'Declare ll.reveal(after=gate, show="named_cell") and hold its output and readers.',
    'rubric': 'A non-computable activity can use a rubric check(draw, answer) and an empty mutant collection.',
    'scratch': 'Keep scratch work separate from visible output. A future host supplies only permission-filtered inputs.',
    'diff': 'Align the two runs and mark the changed lines and the first divergence.',
    'presentation': 'State what the learner should see. Keep the control and its effect visible together. '
                    'Give wide content its own scrolling area and make the default state show the contrast.',
    'slides': 'Use the slides layout for a sequence of verified frames on a narrow screen.',
}
