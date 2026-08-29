---
title: "Repository Tooling Configuration"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
source_paths:
  - "pyproject.toml"
  - "uv.lock"
  - ".python-version"
  - "apps/learnloop-tauri/package.json"
  - "apps/learnloop-tauri/package-lock.json"
  - "apps/learnloop-tauri/tsconfig.json"
  - "apps/learnloop-tauri/vite.config.mjs"
  - "apps/learnloop-tauri/src-tauri/Cargo.toml"
  - "apps/learnloop-tauri/src-tauri/Cargo.lock"
  - "apps/learnloop-tauri/src-tauri/.cargo/config.toml"
  - "apps/learnloop-tauri/src-tauri/tauri.conf.json"
  - "apps/learnloop-tauri/src-tauri/capabilities/default.json"
  - "src/learnloop/sim/default_sweep.yaml"
  - "src/learnloop/sim/planted_misgrade_sweep.yaml"
  - "calibration_bundles/template.yaml"
tags:
  - "learnloop/configuration/development"
  - "learnloop/repository"
  - "learnloop/status/active"
---

# Repository Tooling Configuration

These files configure development, packaging, tests, architecture enforcement, desktop builds, and simulation—not an individual learner vault. ^tooling-config-scope

| File | Function | Runtime/refactor status |
|---|---|---|
| `pyproject.toml` | Python package metadata, dependencies/extras, `learnloop` entry point, pytest path, and six import-linter architecture contracts | **ACTIVE** — authoritative package/test/architecture config |
| `uv.lock` | Reproducible Python dependency resolution | **ACTIVE** — generated lock; update through `uv` |
| `.python-version` | Local Python version selection | **ACTIVE** — developer runtime selector |
| `apps/learnloop-tauri/package.json` / `package-lock.json` | Desktop frontend scripts and reproducible JavaScript dependency graph | **ACTIVE** — package manifest plus generated lock |
| `apps/learnloop-tauri/tsconfig.json` | TypeScript compiler configuration and implicit `src` inclusion | **ACTIVE** — frontend compile contract |
| `apps/learnloop-tauri/vite.config.mjs` | React/Vite plugin, fixed development port, watch exclusions, and allowed environment prefixes | **ACTIVE** — desktop frontend build/dev-server config |
| `apps/learnloop-tauri/src-tauri/Cargo.toml` / `Cargo.lock` | Rust desktop-shell crate, dependencies, and reproducible resolution | **ACTIVE** — crate manifest plus generated lock |
| `apps/learnloop-tauri/src-tauri/.cargo/config.toml` | Exports `WEBKIT_DISABLE_DMABUF_RENDERER=1` to avoid the documented WebKitGTK/Mesa Wayland crash; ignored where WebKitGTK is absent | **ACTIVE** — platform runtime workaround |
| `apps/learnloop-tauri/src-tauri/tauri.conf.json` | Tauri application identity, build, window, bundle, and plugin configuration | **ACTIVE** — native application config |
| `apps/learnloop-tauri/src-tauri/capabilities/default.json` | Grants the main window its exact dialog, opener, titlebar/window-control, and webview-zoom permissions | **ACTIVE** — security-sensitive capability allowlist |
| `src/learnloop/sim/default_sweep.yaml` | Default algorithm parameter sweep inputs | **EVALUATION** — offline, decision-inert experiment input |
| `src/learnloop/sim/planted_misgrade_sweep.yaml` | Planted grading-error experiment inputs | **EVALUATION** — offline, decision-inert experiment input |
| `calibration_bundles/template.yaml` | Template for reviewed calibration-bundle data | **ACTIVE** — operator-facing template, not a learner-vault default |

> [!important] Architecture contracts live in project config
> `pyproject.toml` forbids infrastructure from importing domain policy, keeps primitive modules dependency-free, isolates CLI/TUI/sidecar adapters, and freezes existing cross-package cycles. A module move that passes unit tests can still violate these contracts.

> [!warning] Desktop permissions are executable policy
> Treat `capabilities/default.json` as a security boundary, not packaging decoration. New Tauri commands do not automatically need new native permissions; expand the allowlist only for a concrete renderer capability and review [[Privacy and Trust Boundaries]].

Use [[Configuration]] for runtime vault settings and [[Module Catalog]] for production module ownership.
