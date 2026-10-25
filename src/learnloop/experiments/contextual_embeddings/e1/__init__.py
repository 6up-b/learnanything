"""Experiment E1: local pplx v2-context-9b (preview) batch pilot (spec §8).

E1 reuses E0's bank, labels and frozen finalists (by path, after E0's run
finishes) and adds two local arms, ``V2_grouped`` and ``V2_singleton``, from
``perplexity-ai/pplx-embed-v2-context-9b-preview`` in BF16.

Modules:

* ``pins``: the model (repo, revision, every file's size and SHA-256, the
  reviewed remote code), the separate environment, the GPU-hours, memory,
  precision and money bounds, the smoke and profiling, the decision rule.
* ``worker``: the standalone batch process (stdlib + numpy at import; torch
  only inside its loader) run in its own ``systemd-run`` scope.
* ``gpu_meter``: the <= 4 GPU-hours meter and the supervised launch.
* ``local``: the job, the scoped launch, validation, the v2 vector store, ranking.
* ``replay``: E0's outputs imported and replayed without any call, and the
  replay verified against E0's published slices.
* ``supplement``: labels for the v2 arms' new candidates (E0's rubric and roles).
* ``ledger``: E1's own <= $5 hard-cap ledger (never an E0 ledger).
* ``plan``, ``run``, ``decide``, ``report``: the plan and its estimates, the
  stages, the prespecified decision, the aggregate report.

Nothing here changes production retrieval, serving, defaults or the
one-embedding-model decision. Private text, vectors and labels stay under
``fixtures-local/contextual-embeddings/e1/``.
"""
