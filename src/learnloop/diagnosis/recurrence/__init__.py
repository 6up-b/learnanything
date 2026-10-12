"""Slice 2 T1 (M3): recurrence with authority.

* :mod:`.kind` - the ``same_cause`` match kind over causal hypotheses;
* :mod:`.judging` - the shared shortlist and judge executor;
* :mod:`.live` - the step inside a diagnose job, and the escalation receipt;
* :mod:`.backlog` - ``learnloop embeddings adjudicate --task same_cause --backlog``;
* :mod:`.guard` - the same-answer/different-cause suite that gates the switch;
* :mod:`.upgrade` - ``learnloop upgrade --to mvp-0.11``;
* :mod:`.report` - the M3 signals report;
* :mod:`.benchmarks` - B1 (Eedi 2024) and B3 (vault replay).

The groups themselves are built in ``learnloop.substrate.recurrence_groups``
(the rebuild replayer reaches them there) from raw ledgers only.
"""
