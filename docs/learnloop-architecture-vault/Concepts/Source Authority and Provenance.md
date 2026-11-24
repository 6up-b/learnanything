---
title: Source Authority and Provenance
aliases:
  - Source Model
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
last_reviewed: 2026-11-23
source_commit: 86f29b0d390ed2ecdbb0347d98ccb1175ac52728
source_commit_timestamp: "2026-11-23T23:12:28-05:00"
source_paths:
  - src/learnloop/content/sources
  - src/learnloop/content/synthesis
  - src/learnloop/ingest/ir.py
  - src/learnloop/reader
tags:
  - learnloop/concept
  - learnloop/sources
  - learnloop/provenance
---

# Source Authority and Provenance

A canonical source is not simply text pasted into a prompt. LearnLoop separates captured material, immutable revision identity, extraction quality, collection membership, synthesis proposals, and applied canonical content.

## Authority chain

```mermaid
flowchart LR
    O[Original URI/file] --> A[Content-addressed asset]
    A --> R[Immutable revision]
    R --> X[Extraction + Document IR]
    X --> U[Units/spans + health]
    U --> SS[Source-set membership<br/>role, authority, scope, pinned revision]
    SS --> M[Synthesis manifest/proposal]
    M --> C[Reviewed canonical content]
    C --> E[Assessment contracts and evidence]
```

Each arrow adds interpretation while retaining the identity behind it. A source-set membership owns role/scope; the raw artifact does not retroactively acquire a subject role.

^source-authority-chain

## Immutability

New bytes create/reuse an asset and revision; they do not mutate an old revision. New extraction settings create a new extraction identity. Synthesis/appends produce manifests, runs, proposals, and change receipts. This supports reproducible citations and lets a reviewer ask exactly which revision shaped a learning object.

## Roles and authority

Sources can be primary, reference, adjunct, exam-like, or otherwise constrained by source-set policy. Role influences synthesis and allowed evidence use, not the truth of the captured bytes. Exam sources have additional leakage/held-out rules.

## Extraction health

Document IR retains blocks/anchors and health flags. Outline/unit selection and budgets let a user inspect what will be synthesized. Poor pages can be repaired or re-extracted without losing the original. A fallback extractor records its degradation rather than presenting identical quality.

## Model output

Inventory stores validated source-unit data. Synthesis stages typed proposals for canonical content. Stable IDs, source refs, manifests, merge/reconciliation rules, validation gates, and reviewed application control canonical mutation. See [[Process Model Output]] and [[AI Architecture#Output trust boundary]].

## Reader citations

Reader/tutor manifests expose bounded source spans and citation IDs. Answers are citation-validated; uncited claims are removed or refused. Source exposure is logged because it affects later measurement coldness.

## Modification guidance

- Preserve asset/revision/extraction identity boundaries.
- Register source kinds in [[Reference/Modules/learnloop/ingest/source_kinds|the source-kind table]]. Extend the extractor, typed IR, health and provenance tests.
- Add synthesis fields to feature-owned contracts and manifests before applying them.
- Keep source role/scope on collection membership, not the global asset.
- Verify citations, append reconciliation, and deletion semantics.

## Workflows and tests

- [[Import Canonical Sources]] and [[Build a Study Map]]
- source layer/objects/refs/sets/inventory/synthesis tests
- ingestion adapters, extraction health, span reanchor, reader citation tests

