"""History-aware diagnosis, split from the learner-blind grader (Slice 1 §5).

The grader measures one answer blind; the diagnoser explains it across time
from blind grades, typed prior hypotheses, the prerequisite neighbourhood and
the misconception registry. Modules:

* :mod:`.settings` - history modes and the §12 defaults;
* :mod:`.history` - typed, blind-grade-equivalent history records and stores;
* :mod:`.context` - the deterministic ``DiagnosisContext`` assembler;
* :mod:`.contract` - ``DiagnosisProposal`` and its prompt;
* :mod:`.validation` - the §5.4 validators and anti-anchoring check;
* :mod:`.snapshot` - the §5.6 as-of export for the read-only workspace mode;
* :mod:`.retrieval` - §9.4 hybrid exact + kNN retrieval;
* :mod:`.legacy_view` - the stored joint diagnosis in the new shape;
* :mod:`.diagnoser` - assemble, call, validate, receipt.

Nothing here writes evidence (S2): every output is a level-4 hypothesis.
"""
