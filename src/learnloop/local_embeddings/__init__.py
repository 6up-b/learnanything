"""Local contextual source retrieval (spec_local_contextual_retrieval_v1, P0/P1a).

The production package for the local pplx v2 9B document space: its pins
and identity, the batch worker (load, encode, unload, exit) in its own capped
``systemd-run --user --scope``, the GPU meter, the locks, the owner-run setup,
the per-vault vector cache, and the learned rank-fusion core shared by every
source space. Moved from E1; ``learnloop.experiments`` is never imported, and
nothing here imports ``learnloop.source_retrieval`` (which drives it: the
index job, the windows and the resolver live there). Off until the owner runs
``learnloop embeddings local setup`` and sets ``embedding.local.enabled``.
"""
