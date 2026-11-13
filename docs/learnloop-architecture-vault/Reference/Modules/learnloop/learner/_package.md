---
title: "learnloop.learner — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/learner/__init__.py"
  - "src/learnloop/learner/assessment_contracts.py"
  - "src/learnloop/learner/blueprint_projection.py"
  - "src/learnloop/learner/calibration.py"
  - "src/learnloop/learner/capability_grid.py"
  - "src/learnloop/learner/capability_mapping.py"
  - "src/learnloop/learner/contract_reachability.py"
  - "src/learnloop/learner/facet_diagnostics.py"
  - "src/learnloop/learner/facet_evidence_timeline.py"
  - "src/learnloop/learner/facet_state_reader.py"
  - "src/learnloop/learner/familiarity.py"
  - "src/learnloop/learner/hypothesis_claims.py"
  - "src/learnloop/learner/identifiability.py"
  - "src/learnloop/learner/independence_audit.py"
  - "src/learnloop/learner/inference_precheck.py"
  - "src/learnloop/learner/learner_profile.py"
  - "src/learnloop/learner/learner_review_feed.py"
  - "src/learnloop/learner/lesson_weight.py"
  - "src/learnloop/learner/mastery.py"
  - "src/learnloop/learner/mastery_step_attribution.py"
  - "src/learnloop/learner/measurement_state.py"
  - "src/learnloop/learner/overconfidence.py"
  - "src/learnloop/learner/recall_calibration.py"
  - "src/learnloop/learner/recall_coverage.py"
  - "src/learnloop/learner/residual_diagnostics.py"
  - "src/learnloop/learner/session_learning_diff.py"
  - "src/learnloop/learner/surfaced_beliefs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Inspect Persistent State"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Mastery, recall, evidence, claims, ability transitions, and learner-state views.

For system intent, use [[Learning System]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/learner/__init__|learnloop.learner]] | [[Reference/Modules/learnloop/learner/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] | [[Reference/Modules/learnloop/learner/assessment_contracts#^module-purpose|purpose]] | `ACTIVE` | 24 | 17 |
| [[Reference/Modules/learnloop/learner/blueprint_projection|learnloop.learner.blueprint_projection]] | [[Reference/Modules/learnloop/learner/blueprint_projection#^module-purpose|purpose]] | `ACTIVE` | 6 | 4 |
| [[Reference/Modules/learnloop/learner/calibration|learnloop.learner.calibration]] | [[Reference/Modules/learnloop/learner/calibration#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |
| [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] | [[Reference/Modules/learnloop/learner/capability_grid#^module-purpose|purpose]] | `ACTIVE` | 3 | 2 |
| [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] | [[Reference/Modules/learnloop/learner/capability_mapping#^module-purpose|purpose]] | `ACTIVE` | 24 | 4 |
| [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] | [[Reference/Modules/learnloop/learner/contract_reachability#^module-purpose|purpose]] | `ACTIVE` | 11 | 4 |
| [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] | [[Reference/Modules/learnloop/learner/facet_diagnostics#^module-purpose|purpose]] | `ACTIVE` | 26 | 7 |
| [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] | [[Reference/Modules/learnloop/learner/facet_evidence_timeline#^module-purpose|purpose]] | `ACTIVE` | 6 | 18 |
| [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] | [[Reference/Modules/learnloop/learner/facet_state_reader#^module-purpose|purpose]] | `ACTIVE` | 26 | 8 |
| [[Reference/Modules/learnloop/learner/familiarity|learnloop.learner.familiarity]] | [[Reference/Modules/learnloop/learner/familiarity#^module-purpose|purpose]] | `ACTIVE` | 4 | 5 |
| [[Reference/Modules/learnloop/learner/hypothesis_claims|learnloop.learner.hypothesis_claims]] | [[Reference/Modules/learnloop/learner/hypothesis_claims#^module-purpose|purpose]] | `ACTIVE` | 3 | 3 |
| [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] | [[Reference/Modules/learnloop/learner/identifiability#^module-purpose|purpose]] | `ACTIVE` | 9 | 5 |
| [[Reference/Modules/learnloop/learner/independence_audit|learnloop.learner.independence_audit]] | [[Reference/Modules/learnloop/learner/independence_audit#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/learner/inference_precheck|learnloop.learner.inference_precheck]] | [[Reference/Modules/learnloop/learner/inference_precheck#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/learner/learner_profile|learnloop.learner.learner_profile]] | [[Reference/Modules/learnloop/learner/learner_profile#^module-purpose|purpose]] | `ACTIVE` | 4 | 2 |
| [[Reference/Modules/learnloop/learner/learner_review_feed|learnloop.learner.learner_review_feed]] | [[Reference/Modules/learnloop/learner/learner_review_feed#^module-purpose|purpose]] | `ACTIVE` | 1 | 7 |
| [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] | [[Reference/Modules/learnloop/learner/lesson_weight#^module-purpose|purpose]] | `ACTIVE` | 12 | 8 |
| [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] | [[Reference/Modules/learnloop/learner/mastery#^module-purpose|purpose]] | `ACTIVE` | 41 | 17 |
| [[Reference/Modules/learnloop/learner/mastery_step_attribution|learnloop.learner.mastery_step_attribution]] | [[Reference/Modules/learnloop/learner/mastery_step_attribution#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/learner/measurement_state|learnloop.learner.measurement_state]] | [[Reference/Modules/learnloop/learner/measurement_state#^module-purpose|purpose]] | `ACTIVE` | 3 | 1 |
| [[Reference/Modules/learnloop/learner/overconfidence|learnloop.learner.overconfidence]] | [[Reference/Modules/learnloop/learner/overconfidence#^module-purpose|purpose]] | `ACTIVE` | 3 | 1 |
| [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] | [[Reference/Modules/learnloop/learner/recall_calibration#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] | [[Reference/Modules/learnloop/learner/recall_coverage#^module-purpose|purpose]] | `ACTIVE` | 11 | 10 |
| [[Reference/Modules/learnloop/learner/residual_diagnostics|learnloop.learner.residual_diagnostics]] | [[Reference/Modules/learnloop/learner/residual_diagnostics#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/learner/session_learning_diff|learnloop.learner.session_learning_diff]] | [[Reference/Modules/learnloop/learner/session_learning_diff#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/learner/surfaced_beliefs|learnloop.learner.surfaced_beliefs]] | [[Reference/Modules/learnloop/learner/surfaced_beliefs#^module-purpose|purpose]] | `ACTIVE` | 8 | 3 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/_package|learnloop]] — 30 static module edges
- [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] — 25 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 21 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 6 static module edges
- [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] — 6 static module edges
- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 5 static module edges
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 5 static module edges
- [[Reference/Modules/learnloop/config/_package|learnloop.config]] — 4 static module edges
- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — 1 static module edge
- [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] — 1 static module edge
- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 1 static module edge
- [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] — 1 static module edge
- [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 31 static module edges
- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 20 static module edges
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 18 static module edges
- [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] — 15 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 14 static module edges
- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — 9 static module edges
- [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] — 9 static module edges
- [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] — 9 static module edges
- [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] — 8 static module edges
- [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] — 7 static module edges
- [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] — 6 static module edges
- [[Reference/Modules/learnloop/field/_package|learnloop.field]] — 6 static module edges
- [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] — 6 static module edges
- [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] — 6 static module edges
- [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] — 5 static module edges
- [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] — 4 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 3 static module edges
- [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] — 3 static module edges
- [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] — 3 static module edges
- [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] — 3 static module edges
- [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] — 3 static module edges
- [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] — 2 static module edges
- [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] — 2 static module edges
- [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] — 2 static module edges
- [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] — 2 static module edges
- [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] — 2 static module edges
- [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] — 2 static module edges
- [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] — 1 static module edge
- [[Reference/Modules/learnloop/recognition/_package|learnloop.recognition]] — 1 static module edge
- [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] — 1 static module edge
- [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] — 1 static module edge
- [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.learner"]
    n_learnloop["learnloop"]
    n_learnloop_sidecar_handlers["learnloop_sidecar.handlers"]
    n_learnloop_diagnosis["learnloop.diagnosis"]
    n_learnloop_vault["learnloop.vault"]
    n_learnloop_substrate["learnloop.substrate"]
    n_learnloop_db["learnloop.db"]
    n_learnloop_goals["learnloop.goals"]
    n_learnloop_attempts["learnloop.attempts"]
    n_learnloop_content_authoring["learnloop.content.authoring"]
    n_learnloop_scheduling["learnloop.scheduling"]
    n_learnloop -->|3| center
    center -->|30| n_learnloop
    n_learnloop_sidecar_handlers -->|31| center
    n_learnloop_diagnosis -->|20| center
    center -->|5| n_learnloop_diagnosis
    center -->|25| n_learnloop_vault
    n_learnloop_substrate -->|18| center
    center -->|5| n_learnloop_substrate
    center -->|21| n_learnloop_db
    n_learnloop_goals -->|15| center
    center -->|6| n_learnloop_goals
    n_learnloop_attempts -->|14| center
    center -->|6| n_learnloop_attempts
    n_learnloop_content_authoring -->|9| center
    center -->|1| n_learnloop_content_authoring
    n_learnloop_scheduling -->|9| center
    center -->|1| n_learnloop_scheduling
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Start a Learning Cycle]]
- [[Inspect Persistent State]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/learner" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
