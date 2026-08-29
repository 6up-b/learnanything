---
title: Documentation Dashboard
aliases:
  - Vault Status Dashboard
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-18
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - docs/learnloop-architecture-vault
tags:
  - learnloop/docs
  - learnloop/meta
  - learnloop/status
---

# Documentation Dashboard

This note works as a plain navigation page and becomes a live status tracker when the optional Dataview plugin is enabled.

## Native searches

```query
[status:needs-owner-input]
```

```query
[status:compat] OR [refactor_status:COMPAT] OR [table_role:compat]
```

```query
[implementation_version:mvp-0.9]
```

```query
[generated]
```

## Dataview — status tracker

```dataview
TABLE status AS Status, choice(doc_version, doc_version, version) AS "Doc version", implementation_version AS Implementation, architecture_version AS Architecture, choice(last_reviewed, last_reviewed, last_verified) AS Reviewed
FROM ""
WHERE file.extension = "md" AND !contains(file.path, "_meta/Templates")
SORT status ASC, file.name ASC
```

## Dataview — notes needing attention

```dataview
TABLE status, functionality_status AS "Runtime status", refactor_status AS "Refactor status", source_commit_timestamp, source_paths
FROM ""
WHERE status = "needs-owner-input" OR status = "proposed" OR status = "dormant" OR startswith(default(functionality_status, ""), "dormant") OR refactor_status = "DORMANT"
SORT choice(functionality_status, functionality_status, status) ASC, file.name ASC
```

## Dataview — generated references

```dataview
TABLE type, refactor_status, choice(table_role, table_role, role) AS Role, choice(source_path, source_path, source_paths) AS Source
FROM "Reference"
WHERE generated OR status = "generated" OR type = "module-reference"
SORT file.folder ASC, file.name ASC
```

> [!info] Plugin independence
> Dataview is optional. All content and WikiLinks work in core Obsidian; generated scripts perform the CI-style coverage checks.

## Review checklist

- Run the module and database generators/validators in `_scripts/`.
- Resolve broken WikiLinks and heading/block fragments.
- Compare authored notes' `source_paths` after architectural changes.
- Update `doc_version` when a note's public structure or meaning changes.
- Update `implementation_version` only when the note describes a different algorithm/config era.

## Reproducible validation

Each generated catalog owns its generator and strict coverage validator; the final command validates metadata, all WikiLinks (including heading/block fragments), every declared source path, and reachability of every non-template note from [[Home]].

```bash
.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py
.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py
.venv/bin/python docs/learnloop-architecture-vault/_scripts/db_generate_reference.py
.venv/bin/python docs/learnloop-architecture-vault/_scripts/db_validate_reference.py
.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py --check
.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py
.venv/bin/python docs/learnloop-architecture-vault/_scripts/validate_vault.py
```

See [[Module Catalog#Maintenance]], [[Desktop Module Catalog#Maintenance]], and [[Database#Documentation regeneration]] for catalog-specific ownership and regeneration rules.
