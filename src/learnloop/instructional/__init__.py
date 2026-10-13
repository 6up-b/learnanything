"""Canonical sources as a shared instructional service (spec_source_practice_and_probes_v1).

A composition layer, not a domain package: it holds the contamination policy's
server-side derivation, the tutor's offers, the source-exercise arm, the
valuation adapter, the exposure rule, the need step, the tool registry and
dispatcher, and S5's report. It composes ``practice_index``,
``source_retrieval``, ``diagnosis``, ``scheduling``, ``substrate``, ``content``
and ``ops``; nothing it imports imports it back (G17). Domain packages,
``practice_index`` and ``source_retrieval`` reach it only through injected
callables; the sidecar and the CLI wire it in.

Tools propose; existing serving paths serve (SC1).
"""
