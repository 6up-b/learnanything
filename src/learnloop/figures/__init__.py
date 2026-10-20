"""Reader workbench RW5a: explorable figures (spec_reader_workbench_v1 §8; UX §4.7, W11).

A figure is a declarative spec, never code (§8.2): the figure author writes an
:class:`~.spec.InteractiveFigureSpecV1` (JSON), validated against the grammar
of :mod:`.grammar`, verified by :mod:`.verify` before it is shown (§8.3), and
drawn by the Reader's trusted renderer from the TypeScript twin of the same
grammar (``apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.ts``),
the two kept identical by one golden corpus.

* :mod:`.grammar`: the hand-written parser and evaluator (no ``eval``), the
  fixed adaptive Simpson rule, exact sums, and the sympy translation the
  verifier's sandboxed check reads;
* :mod:`.spec`: the spec, its caps, and :func:`~.spec.evaluate_figure` (the
  panels' data, the corpus's parity unit);
* :mod:`.verify`: structure, invariants, shaded areas, source match;
* :mod:`.routes`: ``figure_author`` and ``figure_verifier`` under the spend cap;
* :mod:`.service`: build, reuse, revise, list, predict, explain.

Content and formative only (W1): nothing here writes an attempt, evidence,
mastery, certification, scheduling, FSRS or adaptive-difficulty state, and
nothing that writes those imports this package (``evidence-never-reads-figures``).
"""
