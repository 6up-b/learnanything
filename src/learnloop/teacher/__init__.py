"""Teacher TE1: lessons on LearnLoop's latent learner state (``docs/specs/spec_teacher_v1.md``).

A composition layer like ``learnloop.instructional``: nothing below it imports it
back (the sidecar and the CLI do). The model owns how to teach; code owns what
may be shown, who grades, what counts as evidence and at what weight, when the
delayed checks happen and on which items, and the receipts (§3).

* :mod:`.contracts`: ``LessonBriefV1``, ``TeacherTurnV1``, ``LessonReceiptV1``, the actions;
* :mod:`.doctrines`: the versioned doctrine (``doctrine/v1/*.md``);
* :mod:`.brief`: the brief from the ledger (with curriculum C4's deliverable and notes);
* :mod:`.guards`: the output guards (keys, the open check's solution, citations);
* :mod:`.checks`: minted held check items, blind grading and the learned mass;
* :mod:`.delayed`: the delayed retention and transfer checks (Check once);
* :mod:`.service`: the lesson lifecycle behind ``lesson.turn``;
* :mod:`.report`: the learned weight's report lines.

The teacher writes attempts only through the attempts path and never writes
mastery, FSRS or evidence directly; it reads adaptive difficulty only through
AD's read-only ``@entry`` functions and never runs inside an AD operation.
"""
