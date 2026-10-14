"""Application services for frontends that run outside the desktop (spec_mcp_frontend_c1).

The MCP chat adapter (``learnloop_mcp``) calls only this package and the shared
read model (``learnloop.learner_context``); it holds no learning policy of its
own. Mobile M2 can attach the same way later (``runtime``).

* ``runtime``: secondary attach to a vault the desktop owns (no migration, no
  startup work), with content freshness;
* ``endpoint_token``: the persistent secret endpoint path, machine-local;
* ``views``: status, today, progress and the library, read-only;
* ``sources``: grounded passages with citations, exposure recorded first;
* ``telemetry``: every chat tool call in ``interaction_events``, and the
  ``learnloop mcp activity`` report;
* ``errors``: the refusals a host may see verbatim (anything else is a
  generic failure: no internal text leaves).
"""
