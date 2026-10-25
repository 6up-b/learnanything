"""Experiment E0: hosted contextual source embeddings, no GPU
(``docs/specs/spec_contextual_source_embeddings_experiments_v1.md`` §5).

Does contextual encoding find canonical explanations and supporting evidence
LearnLoop otherwise misses? E0 answers, in order: do fixed delivery or direct
reading suffice (D0-D3); does hosted contextualization beat cheap context
with Qwen (R0-R5); only then, is local work warranted (S4, E1).

Modules:

* ``pins``: models, routes, provider contracts and prices (each flagged
  verified or not), caps, seeds and versions; the frozen constants.
* ``credentials``: process-environment keys and ``--env-file`` (never echoed).
* ``budget``: the one E0 spend ledger ($25 across every paid call).
* ``corpus``: copies, the read-only inventory, policy verdicts and
  invalidation, candidate units, windows, dependency maps, families.
* ``adapters``: the isolated embedding adapters (Qwen, Perplexity, Voyage).
* ``retrieval``: exact search and the R0-R5 arm definitions.
* ``delivery``: D0-D3.
* ``bank``: the smoke bank, question writing, labels, adjudication.
* ``metrics``, ``stop_rules``: §5.2 metrics and §7's S1-S4.
* ``plan``: the frozen run plan and its estimate; ``report``: the §11 report.
* ``runner``: the dry run (no network, no writes) and the paid run's steps.

Nothing here is evidence, nothing changes production retrieval, serving,
config defaults or the one-embedding-model decision
(``qwen/qwen3-embedding-8b``). Private text, vectors and labels stay in
``fixtures-local/contextual-embeddings/``; only aggregates are published.
"""
