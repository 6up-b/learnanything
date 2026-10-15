"""LearnLoop's MCP adapter: the vault in ChatGPT and Claude chat (spec_mcp_frontend_c1).

An entry point like ``learnloop_sidecar`` and ``learnloop_mobile``: it owns the
protocol (tools, schemas, transports, the endpoint gate) and calls only the
application services in ``learnloop.remote`` and the shared read model
``learnloop.learner_context`` (import-linter: ``mcp-adapter-calls-application-
services``). It needs the optional ``mcp`` extra (the official MCP Python SDK,
pinned at 2.3.0, the version the M0 probe verified with both hosts).
"""

ADAPTER_VERSION = "0.1.0"
DEFAULT_PORT = 8769
