---
title: User Journey Map
aliases:
  - Workflow MOC
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - README.md
  - documentation.md
tags:
  - learnloop/workflow
  - moc
---

# User Journey Map

Workflows are procedural and observable. They link to concept notes for explanations instead of embedding a second copy of the algorithm.

```mermaid
flowchart LR
    INIT[Initialize a Vault] --> CONFIG[Configure AI or manual mode]
    INIT --> IMPORT[Import Canonical Sources]
    IMPORT --> BUILD[Inventory and synthesize study map]
    BUILD --> LEARN[Start a Learning Cycle]
    LEARN --> OUTPUT[Process Model Output]
    OUTPUT --> STATE[Inspect Persistent State]
    STATE --> LEARN
    STATE --> DOCTOR[Doctor, migrate, recover, rebuild]
```

This loop distinguishes source/build work from repeated learning work. Initialization and canonical synthesis are occasional; attempt → evidence → state → next action repeats continuously.

## First-use path

1. [[Initialize a Vault]]
2. [[Configure AI Providers]] or choose the typed manual path
3. [[Import Canonical Sources]]
4. [[Build a Study Map]]
5. [[Start a Learning Cycle]]
6. [[Process Model Output]]
7. [[Inspect Persistent State]]

The import/build steps preserve the identity chain described by [[Source Authority and Provenance]].

## Continued-use paths

- [[Continue a Learning Cycle]]
- [[Reader to Practice Workflow]]
- [[Tutor and Teach-Back Workflow]]
- [[Goals Exams and Certification Workflow]]
- [[Rebuild and Shadow Compare]]
- [[Doctor Migrations and Recovery]]

## Observable examples

Open [[Example Index]] for copyable configurations, command sessions, expected filesystem artifacts, and representative database queries.
