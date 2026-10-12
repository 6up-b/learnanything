"""Project understanding M1: delayed comprehension probes on agent-written code.

``spec_project_understanding_v1.md``. Agent-written diffs in enrolled repos are
captured automatically (a git-only sweep at app start and plan build, plus an
optional append-only ``post-commit`` pending list), redacted, and stored as
content-addressed snapshots. About seven days later two sealed questions per
diff, answered from memory, check whether the owner still understands the
code. Grading is learner-blind.

M1 is standalone: everything lives in ``<vault>/projects/project_store.sqlite``
(plus the pending list and the originals store). It never opens, migrates or
writes ``state.sqlite``, and probe answers are practice only, never cold
certification (decision D6). M2 imports the store into the vault.
"""
