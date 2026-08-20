---
title: Glossary
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - documentation.md
  - ARCHITECTURE.md
  - src/learnloop
tags:
  - learnloop/reference
  - learnloop/glossary
---

# Glossary

**Activity administration**

A recorded presentation context: what surface was shown, for what purpose, with what source/assistance conditions. See [[Attempt Processing]].

**Assessment contract**

Content-addressed snapshot of item, rubric, targets, recipes, dependencies, correlation groups, and assistance budget at presentation time. See [[Canonical Knowledge Model#Contracts and historical replay]].

**Capability**

A closed, domain-general performance operation combined with a facet in canonical evidence.

**Canonical evidence**

Direct licensed facet × capability observations used by learner views and certification; distinct from prediction-only LO calibration.

**Cold observation / cold probe**

An administration protected from immediate source/reveal/familiarity contamination, often delayed and held out. See [[Goals and Certification#Cold probes]].

**Compatibility substrate**

Frozen old-vault behavior under `learnloop.substrate.compat`. See [[ADR-012 Freeze the compatibility substrate]].

**Criterion**

Smallest scored observation boundary in a rubric; targets specific facet/capability roles.

**DERIVED**

Table role for state that one owner can clear and exactly reconstruct. See [[State and Persistence#Table roles]].

**Document IR**

Structured extracted representation of a source revision, including blocks, anchors, metadata, and health. See [[Content Pipeline]].

**Evidence coverage**

How much of the frozen contract frontier an answer actually exposed, not merely points earned. See [[Evidence and Measurement#Coverage]].

**Expected information gain (EIG)**

Expected reduction in posterior/predictive uncertainty from an eligible diagnostic instrument. See [[Diagnosis and Remediation#Expected information gain]].

**Facet**

Canonical content claim/unit that may participate in multiple learning objects.

**Familiarity**

Recorded exposure used to discount independence and protect cold measurement; not ability evidence.

**FSRS**

Item/card memory model producing difficulty, stability, retrievability, due time, and review intervals. See [[Scheduling and Selection#FSRS]].

**Goal frontier**

Scoped cells that are unexamined, at risk, or insufficient for a goal's terminal contract.

**Hypothesis set**

Versioned, locked plausible causal explanations used during a diagnostic episode.

**Ingest batch/job**

Durable SQLite workflow units with dependencies, leases, retry identities, and checkpoint progress. See [[Content Pipeline#Durable checkpoint ladder]].

**Learning object (LO)**

A performance blueprint describing valid compositions of facet × capability components.

**Manual resolution**

Typed provider-selection outcome with no AI client, preserving manual/self-grade workflow semantics. See [[AI Architecture#Failure and manual behavior]].

**Mastery EKF**

Per-LO prediction calibration residual under canonical versions; never direct certification credit. See [[Learner State and Projections#LO mastery calibration]].

**Measurement label**

One of measured/inferred/claimed/unknown attached to displayed state. See [[Evidence and Measurement#Display labels]].

**Observation ledger**

Immutable attempt/activity evidence from which projections can be replayed.

**Practice item**

Concrete authored/generated assessment or learning surface attached to an LO, rubric, mode, lineage, and lifecycle.

**Primed attempt**

Attempt after relevant content/answer exposure; useful but not equivalent to cold independent evidence.

**Projection**

Versioned computed state/read model derived from authoritative ledgers.

**RAW_LEDGER**

Table role for authoritative authored, captured, calibrated, or observed input that rebuild must preserve.

**RECEIPT**

Append-only table role for decisions and audit history.

**Replay**

Reapplication of historical events/contracts under defined semantics to reconstruct projection state.

**Rung**

Curriculum task-depth level, distinct from a capability and from the golden-path pattern ladder.

**Shadow rebuild**

Candidate replay on a copied DB with semantic diff and live-file hash isolation. See [[State and Persistence#Shadow rebuild]].

**Source set**

Collection membership that pins immutable source revisions and records role, authority, scope, and selection.

**Surface**

Presentation identity/family used to track freshness, exposure, reservations, and single-use diagnostic constraints.

**Teach-back**

Conversation where learner explains and a naïve-student model asks planned questions; completed transcript becomes one asked-criteria-only attempt.

**WORKFLOW**

Table role for mutable queues, sessions, leases, and other in-flight lifecycle state preserved during rebuild.

## Related lookup

Use [[Module Catalog]] for symbols/files, [[Database Catalog]] for table semantics, and [[Configuration]] for settings/defaults.
