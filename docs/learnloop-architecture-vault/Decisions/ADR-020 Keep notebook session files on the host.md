---
title: ADR-020 Keep notebook session files on the host
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
decision_date: 2026-11-23
decision_status: accepted
last_reviewed: 2026-11-23
source_commit: 9038b096e7446d5f433f95d881de7e7c1bd0da15
source_commit_timestamp: "2026-11-23T19:57:34-05:00"
source_paths:
  - src/learnloop/notebook_runtime/hostfiles.py
  - src/learnloop/notebook_runtime/sandbox.py
  - src/learnloop/notebook_runtime/supervisor.py
  - src/learnloop/notebook_runtime/proxy.py
  - tests/test_notebook_host_boundary.py
tags:
  - learnloop/decision
  - learnloop/security
  - learnloop/reader
---

# ADR-020 Keep notebook session files on the host

## Context

The marimo server and its kernel share a sandbox. Letting that sandbox write into the directory the supervisor uses for a token or socket lets notebook code substitute the path the host later opens.

## Decision

The sandbox receives no writable host path. It writes to its own temporary filesystems. The supervisor creates the token and mounts it read-only. The host creates and listens on the Unix socket and passes the descriptor to the child. The child needs no host socket pathname.

Host session files go through [[Reference/Modules/learnloop/notebook_runtime/hostfiles|hostfiles]]. It checks private directories, creates files exclusively without following links and checks the socket before host connections. It also owns the checked write of a pad's derived notebook beneath the vault. The frame reaches the server through the session's loopback HTTP and WebSocket proxy. See [[Reference/Modules/learnloop/notebook_runtime/proxy|Notebook proxy]].

## Consequences

- Restart and connection use the same host-owned boundary. Notebook code can still change its own state.
- The kernel shares the server's credential. Held cells control frame display and must never contain material that needs to be secret from the running notebook. See [[Workbench protection]].
- The runtime requires its sandbox and user scope. The frame can report an unavailable runtime. See [[Reader workbench#Ink, lessons and notebooks]].

## Enforcement

`tests/test_notebook_host_boundary.py` checks the launch boundary, audits host filesystem calls and exercises hostile path substitutions in a real sandbox. The runtime tests cover close during startup and forced cleanup at close or vault switch.

## What would reverse it

A replacement runtime would need a host interface that eliminates sandbox-controlled host paths and proves equivalent isolation on restart and reconnect. Protecting a reveal from notebook code would also require the protected content to stay outside the kernel until a host-owned commit permits release.
