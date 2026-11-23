"""Reader workbench v2 (spec §7.6): the two DERIVED span projections, ``question_event_spans`` and
``learner_text_gap_spans``, their per-source recipes, their write-through and their replayers.

A leaf below the packages that write through it (the Reader's Ask, the tutor, the gap pipeline) and
the rebuild that replays it: it imports only the stores, so no package cycle can run through it
(``pyproject.toml``'s acyclic contract). The union read that consumes it is ``learnloop.passage_union``.
"""
