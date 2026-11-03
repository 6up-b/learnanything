"""Reader workbench RW5a: explorable figures (spec_reader_workbench_v1 §8; UX §4.7, W11).

A figure is a declarative spec, never code (§8.2): the figure author writes an
:class:`~.spec.InteractiveFigureSpecV1` (JSON), validated against the grammar
of :mod:`.grammar`, verified by :mod:`.verify` before it is shown (§8.3), and
drawn by the Reader's trusted renderer from the TypeScript twin of the same
grammar (``apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.ts``),
the two kept identical by one golden corpus.

* :mod:`.grammar`: the hand-written parser and evaluator (no ``eval``), the
  fixed adaptive Simpson rule and exact sums;
* :mod:`.spec`: the spec, its caps, and :func:`~.spec.evaluate_figure` (the
  panels' data, the corpus's parity unit);
* :mod:`.verify`: structure, invariants, shaded areas (§8.3 steps 1-2);
* RW5c's step 3, the source match: :mod:`.katex_tree` (the page's KaTeX parses the
  book's equation in a sealed engine), :mod:`.book_math` (a closed translator reads
  that tree), :mod:`.source_check` with its sandboxed harness (the exact check,
  no model), :mod:`.elements` (code-owned labels) and :mod:`.display_format`
  (the display twins);
* :mod:`.routes`: ``figure_author`` under the spend cap;
* :mod:`learnloop.figure_admission`: the one switch predicate and the gate
  every figure-derived model request passes;
* :mod:`.service`: build, reuse, revise, list, predict, explain.

Content and formative only (W1): nothing here writes an attempt, evidence,
mastery, certification, scheduling, FSRS or adaptive-difficulty state, and
nothing that writes those imports this package (``evidence-never-reads-figures``).
"""
