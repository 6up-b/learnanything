"""Local contextual source retrieval (spec_local_contextual_retrieval_v1, P1a).

The production package for the local pplx v2 9B document space: its pins
and identity, the batch worker (load, encode, unload, exit) in its own capped
``systemd-run --user --scope``, the GPU meter, the locks, the owner-run
setup and the index job writing the per-vault vector cache. Moved from E1;
``learnloop.experiments`` is never imported. Off until the owner runs
``learnloop embeddings local setup`` and sets ``embedding.local.enabled``.
"""
