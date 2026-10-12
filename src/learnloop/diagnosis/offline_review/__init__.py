"""Slice 1 M1: the offline review of blind grading and history-aware diagnosis.

Nothing here changes a live vault. A run copies the vault database through the
backup API into its own directory, plants unlabelled synthetic learners, blind
grades a stratified sample, diagnoses each attempt under five arms, has a blind
LLM judge compare them in two passes, probes the blind grader, and reports.

* :mod:`.spend` - per-route admission (metered vs subscription) and usage;
* :mod:`.planted` - planted learners with known truth (S1.0);
* :mod:`.probes` - E1 grader probes;
* :mod:`.judge` - the blind pairwise / link / planted-cause judge;
* :mod:`.runner` - plan, estimate, run (resumable), into the scratch copy;
* :mod:`.report` - the M1 report (aggregates only);
* :mod:`.spot_check` - the optional ~10-item owner screens;
* :mod:`.links` - importing pattern-link verdicts into ``judgment_ledger``.
"""
