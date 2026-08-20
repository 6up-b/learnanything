---
title: Search Guide
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-18
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - docs/learnloop-architecture-vault/.obsidian/graph.json
tags:
  - learnloop/docs
  - learnloop/meta
  - learnloop/search
---

# Search Guide

Use Obsidian's search pane (`Ctrl/Cmd+Shift+F`), tags pane, quick switcher, backlinks, and local graph together.

## High-value searches

```query
tag:#learnloop/workflow [status:active]
```

```query
tag:#docs/module "src/learnloop/scheduling"
```

```query
tag:#learnloop/desktop path:"Reference/Desktop"
```

```query
tag:#learnloop/database/table [table_role:derived]
```

```query
[source_paths:src/learnloop/ai]
```

```query
tag:#learnloop/decision "compatibility"
```

```query
path:"Reference/Modules" "Who calls it"
```

```query
tag:#learnloop/status/dormant OR tag:#learnloop/status/compat
```

> [!tip] Exact property syntax
> Obsidian versions differ slightly in property-query UI. If `[property:value]` is unsupported, search the YAML text directly, for example `path:"Reference/Database/Tables" "table_role: derived"`.

## Find a change point

1. Search the behavior term, then open its concept note.
2. Follow “Implementation anchors” to a package/module MOC.
3. Open the module note and inspect **Who calls it**, **Dependencies**, and **Important tests**.
4. Use backlinks on the concept heading to find workflows and decisions affected by the change.

## Graph filters

The vault graph colors concepts, architecture, workflows, modules, tables, and decisions separately. Useful filters:

- `-path:_meta/Templates` — hide templates.
- `tag:#learnloop/architecture OR tag:#learnloop/concept` — conceptual skeleton only.
- `tag:#docs/module path:"Reference/Modules/learnloop/scheduling"` — one package neighborhood.
- `tag:#learnloop/desktop/rust path:"Reference/Desktop"` — native desktop bridge modules only.
- `tag:#learnloop/database/table -[table_role:workflow]` — durable evidence/projection tables.

## Backlinks and unlinked mentions

Backlinks are the preferred “used by” index for concepts. Generated module notes contain explicit importers because module relationships are machine-derived. Enable **Unlinked mentions** when renaming a concept; it catches prose that has not yet become a WikiLink.

## Bookmarks

Recommended bookmarks: [[Home]], [[User Journey Map]], [[Architecture Map]], [[Learning System]], [[Module Catalog]], [[Desktop Module Catalog]], [[Database Catalog]], and [[Refactor Status]].
