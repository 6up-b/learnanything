"""Slice 2 T6: source retrieval (spec_embedding_consumers_v1 §9).

Keyword search (FTS5 BM25 over ``source_block_fts``) and dense search over the
stored ``source_block/text`` vectors, fused by reciprocal rank, with an LLM
rewrite for conceptual questions and an LLM listwise verification on the one
consequential path (the tutor's grounding spans).

Consumers: the library search, the tutor's source spans, the Quick Add scope
preview and a labelled nearest-LO suggestion for reader spans without
provenance. Retrieval is context only: embeddings rank, nothing here writes
evidence, scheduling or projection state, and every LLM verdict goes to
``judgment_ledger``.

This package sits above the reader, tutor and practice index. Adapters (the
sidecar, the CLI) import it and hand its providers to the tutor and reader by
injection, so those domain packages never import it.
"""
