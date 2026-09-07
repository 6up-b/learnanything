---
title: "Configuration Field Catalog"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "Effective config index"
  - "learnloop.toml field MOC"
config_schema_version: 2
algorithm_version: "mvp-0.9"
section_count: 27
field_count: 495
field_status_counts: {"ACTIVE": 472, "COMPAT": 4, "DORMANT": 15, "LEGACY": 4}
generated: true
source_paths:
  - "src/learnloop/config/schema.py"
  - "src/learnloop/config/template.py"
  - "tests/test_config_refactor.py"
tags:
  - "learnloop/configuration/moc"
  - "learnloop/configuration/schema-v2"
  - "learnloop/navigation"
---

# Configuration Field Catalog

The section notes below enumerate every leaf in the effective configuration of a newly initialized mvp-0.9 vault. Start with [[Configuration]] for precedence and policy, then use this catalog for exact paths/defaults. ^config-catalog-scope

> [!note] Explicit versus effective
> The generated `learnloop.toml` is intentionally small. Each field row says whether the value is an explicit template decision or a modeled default/validator seed.

## Runtime and refactor status

Every one of the 487 effective leaves has a semantic Function, a runtime/refactor Status, and concrete schema or consumer anchors. Status is about authority, not truthiness:

| Status | Effective leaves | Meaning |
|---|---:|---|
| `ACTIVE` | 472 | Canonical typed input to current behavior. |
| `DORMANT` | 15 | Implemented but shadow-only, default-inert, or behind a shipped-off activation gate. |
| `COMPAT` | 4 | Effective compatibility seam retained while canonical behavior uses another field or route. |
| `LEGACY` | 4 | Read only by a frozen historical replay path. |

> [!warning] Compatibility aliases are not effective leaves
> One-way aliases and discarded retired keys are listed under **Compatibility-only inputs** in the affected section notes. They are accepted inputs, but do not survive as additional leaves in the 487-path effective model. See [[Legacy Configuration Compatibility]].

## Sections

| Section | Effective leaf values | Primary concern |
|---|---:|---|
| [[Config - schema_version|`schema_version`]] | 1 | Runtime configuration |
| [[Config - storage|`storage`]] | 1 | Runtime configuration |
| [[Config - algorithms|`algorithms`]] | 1 | Runtime configuration |
| [[Config - evidence|`evidence`]] | 38 | Learning policy; see [[Learning System]] |
| [[Config - scheduler|`scheduler`]] | 39 | Learning policy; see [[Learning System]] |
| [[Config - goals|`goals`]] | 1 | Learning policy; see [[Learning System]] |
| [[Config - hypothesis|`hypothesis`]] | 6 | Runtime configuration |
| [[Config - mastery|`mastery`]] | 24 | Learning policy; see [[Learning System]] |
| [[Config - probe|`probe`]] | 62 | Learning policy; see [[Learning System]] |
| [[Config - recall_coverage|`recall_coverage`]] | 81 | Learning policy; see [[Learning System]] |
| [[Config - facet_diagnostic|`facet_diagnostic`]] | 4 | Runtime configuration |
| [[Config - misconceptions|`misconceptions`]] | 7 | Runtime configuration |
| [[Config - practice_generation|`practice_generation`]] | 4 | Runtime configuration |
| [[Config - exam_seeding|`exam_seeding`]] | 2 | Runtime configuration |
| [[Config - tutor_qa|`tutor_qa`]] | 11 | Runtime configuration |
| [[Config - tutor_promotion|`tutor_promotion`]] | 6 | Runtime configuration |
| [[Config - teach_back|`teach_back`]] | 3 | Runtime configuration |
| [[Config - rung_variants|`rung_variants`]] | 8 | Runtime configuration |
| [[Config - animation|`animation`]] | 16 | Runtime configuration |
| [[Config - ingest|`ingest`]] | 38 | Runtime configuration |
| [[Config - ai|`ai`]] | 114 | AI provider profile and task routing; see [[AI Architecture]] |
| [[Config - capabilities|`capabilities`]] | 6 | Runtime configuration |
| [[Config - locks|`locks`]] | 2 | Runtime configuration |
| [[Config - error_impacts|`error_impacts`]] | 9 | Runtime configuration |
| [[Config - fitting|`fitting`]] | 6 | Runtime configuration |
| [[Config - trace_evidence|`trace_evidence`]] | 2 | Runtime configuration |
| [[Config - diagnostic_augmentation|`diagnostic_augmentation`]] | 3 | Runtime configuration |

## Search recipes

- `path:"Reference/Configuration/Fields" "gate_score_threshold"` — locate an exact field.
- `path:"Reference/Configuration/Fields" "explicit template decision"` — see fields written by init.
- `path:"Reference/Configuration/Fields" "modeled default or validator seed"` — see hidden effective policy.
- `path:"Reference/Configuration/Fields" "**LEGACY**"` — frozen replay-only fields.
- `path:"Reference/Configuration/Fields" "Compatibility-only inputs"` — sections accepting old spellings.
- `tag:#learnloop/configuration/section/ingest` — filter to one top-level section.

## Related notes

- [[learnloop.toml]]
- [[Legacy Configuration Compatibility]]
- [[Environment and Machine Settings]]
- [[Runtime and Vault Data Files]]
