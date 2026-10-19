"""Reader workbench RW2b: checks and the help ladder's Reader side (spec_reader_workbench_v1 §5.2-5.6).

* :mod:`.check`: "Check my work" (route ``workbench_check``) and its validation;
* :mod:`.symbolic`: the declared symbolic checks, fixed sympy code in the PF-b sandbox;
* :mod:`.ladder`: what the one hint service is given for a workbench request,
  the Reader's fallback progression, and the problem's restored help;
* :mod:`.bridge`: "compare with the book" under a hint.

A package of its own beside :mod:`learnloop.reader` (whose RW2a module
:mod:`learnloop.reader.workbench` is the scratchpad), because it calls the
hint service (:mod:`learnloop.hints`) and the source-retrieval spend envelope,
and both of those already read the Reader: kept here, no import cycle forms
(``frozen-cross-package-cycles``). It defines no hint writer, chooser or map
builder (G64, ``workbench-calls-the-one-hint-service``), and nothing that
writes evidence imports it (``evidence-never-reads-the-workbench``).
"""
