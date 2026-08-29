---
title: Example Index
aliases:
  - Examples MOC
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-18
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - README.md
  - src/learnloop/cli/app.py
tags:
  - learnloop/example
  - moc
---

# Example Index

These examples are operator walkthroughs, not additional authorities for the architecture. Follow their workflow links when a command's safety boundary or concept needs explanation.

## New vault to first work

1. [[First Vault Walkthrough]] — install, initialize, verify, and make the first import.
2. [[AI Provider Configuration Recipes]] — ready provider, OpenAI-compatible route, or manual mode.
3. [[Deliberate Canonical Import Session]] — inspect, pin, and plan one actual Markdown source.
4. [[First Learning Session]] — preview the queue, start a UI session, submit, and finish.

## Focused operations

- [[Manual Attempt and State Inspection]] — self-grade an ordinary item and trace all persisted layers.
- [[Provider-Backed Attempt and Agent Run]] — run structured grading, verify success versus fallback, and inspect the durable model-call receipt.
- [[Goal and Exam Session]] — create a goal, prepare fresh material, and administer held-out items.
- [[Recovery and Rebuild Drill]] — rehearse doctor and isolated replay without mutating live state.

## Search recipes

Paste these into Obsidian search:

```text
tag:#learnloop/example "Prerequisites"
path:Examples/ "Observable"
path:Workflows/ "[!warning]"
tag:#learnloop/operations [status:active]
```

> [!info] Shell convention
> Examples assume execution from the repository root and use `uv run`. Set `VAULT` once per shell. Placeholder values use angle brackets and must be replaced.

## Related maps

- [[User Journey Map]]
- [[Architecture Map]]
- [[Data and State Map]]
