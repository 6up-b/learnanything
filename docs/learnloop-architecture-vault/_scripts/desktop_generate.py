#!/usr/bin/env python3
"""Generate the Obsidian desktop-source reference from static repository evidence.

The generator never imports or executes the desktop application.  It inventories
the authored TypeScript/TSX tree and the five Rust crate modules, resolves local
imports, records inbound consumers, extracts source anchors, associates tests by
explicit evidence, and writes deterministic Markdown.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
VAULT_ROOT = REPO_ROOT / "docs" / "learnloop-architecture-vault"
CATALOG_ROOT = VAULT_ROOT / "Reference" / "Desktop"
TS_ROOT = REPO_ROOT / "apps" / "learnloop-tauri" / "src"
RUST_ROOT = REPO_ROOT / "apps" / "learnloop-tauri" / "src-tauri" / "src"
DOC_VERSION = "1.0.0"
GENERATED_AT = "2026-08-18"


AREA_RESPONSIBILITIES = {
    "TypeScript": "The React renderer entry point and cross-cutting frontend modules.",
    "TypeScript/api": "Typed DTOs and the renderer-to-Tauri invocation facade.",
    "TypeScript/app": "Desktop shell orchestration, keyboard policy, configuration helpers, and recent-vault state.",
    "TypeScript/components": "Reusable learner-facing controls and composite interaction surfaces.",
    "TypeScript/components/goldenpath": "Golden-path setup and triage components used by the staged learning journey.",
    "TypeScript/components/graphedit": "Study-map editing widgets, pending edits, and geometry previews.",
    "TypeScript/components/recipeedit": "Recipe-tree editing for structured learning plans.",
    "TypeScript/fixtures": "Deterministic renderer fixtures used to demonstrate or restore known states.",
    "TypeScript/fixtures/goldenpath": "A barrel over checked-in golden-path JSON scenario fixtures.",
    "TypeScript/render": "Markdown, mathematics, and live-editor rendering adapters.",
    "TypeScript/screens": "Top-level routed workflow screens in the desktop shell.",
    "TypeScript/screens/reader": "Reader request-state coordination extracted from the main reader screen.",
    "TypeScript/screens/startBackdrops": "Canvas/SVG simulations and workers used as the start-screen visual backdrop.",
    "Rust": "The native Tauri shell, command bridge, sidecar process manager, error contract, and vault watcher.",
}


BEHAVIOR_TEST_RULES: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (("goldenpath", "goldenpathscreen"), ("tests/test_sidecar_golden_path.py", "tests/test_sidecar_golden_path_assessment.py", "tests/test_golden_path_fixture.py")),
    (("reader", "pdfreader", "openinsource", "pagerange", "sourcetail", "highlight"), ("tests/test_sidecar_reader.py", "tests/test_sidecar_reader_pdf_view.py", "tests/test_reader_render_views.py", "tests/test_reader_requests.py")),
    (("practice", "itempresentation", "probe", "dialogue", "questionqueue"), ("tests/test_large_practice_flow.py", "tests/test_sidecar_contract.py", "tests/test_practice_information.py", "tests/test_sidecar_diagnostic.py")),
    (("repair", "causal", "adjudication", "diagnostic", "whydiagnosis"), ("tests/test_causal_repair_sidecar_rpcs.py", "tests/test_causal_attribution_p0.py", "tests/test_diagnosis_adjudication.py", "tests/test_diagnostic_review_policy.py")),
    (("goal", "exam"), ("tests/test_sidecar_goals.py", "tests/test_sidecar_exams.py", "tests/test_goal_projection.py", "tests/test_exam_session.py")),
    (("calibration",), ("tests/test_calibration_sessions.py", "tests/test_exam_calibration.py", "tests/test_answer_calibration_duel.py")),
    (("ingest", "source", "quickadd", "outlineandplan", "newvault"), ("tests/test_sidecar_ingest_m3.py", "tests/test_source_ingestion.py", "tests/test_ingest_runner.py", "tests/test_init.py")),
    (("knowledge", "graph", "facet", "syllabus", "recipe", "studymap"), ("tests/test_sidecar_knowledge_model.py", "tests/test_graph_editor_reads.py", "tests/test_graph_edit_proposals.py", "tests/test_build_study_map_routing.py")),
    (("maintenance", "sqlite", "settings"), ("tests/test_maintenance_feed.py", "tests/test_doctor.py", "tests/test_desktop_rpc_contract.py")),
    (("feedback", "review", "trackrecord", "provenance", "claim"), ("tests/test_review_log.py", "tests/test_learner_review_system_entries.py", "tests/test_forecast_ledger.py")),
    (("api/client", "api/dto", "commands.rs", "sidecar.rs", "errors.rs", "main.rs"), ("tests/test_desktop_rpc_contract.py", "tests/test_sidecar_contract.py")),
    (("vault_watcher", "queueevents"), ("tests/test_desktop_rpc_contract.py", "tests/test_sidecar_contract.py")),
]


SPECIAL_PURPOSES = {
    "src/main.tsx": "Bootstraps React, applies the persisted palette before first paint, and mounts the desktop application shell.",
    "src/vite-env.d.ts": "Adds Vite's ambient client declarations to the TypeScript compilation unit.",
    "src/api/client.ts": "Defines the typed renderer-side RPC facade that converts UI actions into named Tauri commands.",
    "src/api/dto.ts": "Owns the renderer's TypeScript representation of sidecar request, response, and view contracts.",
    "src/app/App.tsx": "Owns desktop navigation and cross-screen state, connecting startup, sessions, overlays, vault refresh, and route handoffs.",
    "src/app/algoConfig.ts": "Normalizes and exposes algorithm configuration values needed by presentation code.",
    "src/app/keyboard.ts": "Centralizes keyboard-target and shortcut guards shared by desktop interactions.",
    "src/app/recentVaults.ts": "Persists and normalizes the renderer's recent-vault list.",
    "src/errors.ts": "Turns unknown renderer failures into the user-facing desktop error contract.",
    "src/queueEvents.ts": "Provides the in-window event boundary that tells independent surfaces the practice queue changed.",
    "src-tauri/src/main.rs": "Bootstraps the native Tauri runtime, registers protocols and commands, and composes the sidecar and vault watcher.",
    "src-tauri/src/commands.rs": "Implements the native command boundary, adapting Tauri invocations to typed JSON-RPC calls on the Python sidecar.",
    "src-tauri/src/sidecar.rs": "Owns the Python sidecar child process, vault selection, JSON-RPC request lifecycle, timeout, restart, and isolated long-running calls.",
    "src-tauri/src/errors.rs": "Defines the serializable native command error contract and distinguishes retryable application failures from invalidated transports.",
    "src-tauri/src/vault_watcher.rs": "Coalesces native filesystem mutations and asks the Python authority to refresh the selected vault before notifying the renderer.",
}


@dataclass(frozen=True, slots=True)
class Symbol:
    name: str
    kind: str
    line: int
    signature: str
    exported: bool
    generated_by_macro: bool = False


@dataclass(slots=True)
class ImportEdge:
    target: Path
    specifier: str
    names: set[str] = field(default_factory=set)
    referenced_names: set[str] = field(default_factory=set)
    kind: str = "import"


@dataclass(slots=True)
class SourceInfo:
    source: Path
    language: str
    area: str
    text: str
    symbols: list[Symbol]
    commit: str
    commit_timestamp: str
    worktree_state: str
    refactor_status: str = "UNREVIEWED"
    activation_kind: str = "unreviewed"
    activation_evidence: str = ""
    activation_chain: list[Path] = field(default_factory=list)
    internal_dependencies: dict[Path, ImportEdge] = field(default_factory=dict)
    asset_dependencies: set[Path] = field(default_factory=set)
    external_dependencies: set[str] = field(default_factory=set)
    std_dependencies: set[str] = field(default_factory=set)

    @property
    def relative(self) -> str:
        return self.source.relative_to(REPO_ROOT / "apps" / "learnloop-tauri").as_posix()

    @property
    def source_path(self) -> str:
        return self.source.relative_to(REPO_ROOT).as_posix()

    @property
    def module_id(self) -> str:
        stem = self.relative.rsplit(".", 1)[0].replace("/", ".")
        return f"desktop.{stem}"


def run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, text=True, capture_output=True
    ).stdout.strip()


def source_files() -> list[tuple[Path, str]]:
    typescript = sorted(
        path for path in TS_ROOT.rglob("*") if path.is_file() and path.suffix in {".ts", ".tsx"}
    )
    rust = sorted(RUST_ROOT.glob("*.rs"))
    return [(path, "TypeScript") for path in typescript] + [(path, "Rust") for path in rust]


def area_for(source: Path, language: str) -> str:
    if language == "Rust":
        return "Rust"
    parent = source.parent.relative_to(TS_ROOT).as_posix()
    return "TypeScript" if parent == "." else f"TypeScript/{parent}"


def note_path(source: Path, language: str) -> Path:
    root = TS_ROOT if language == "TypeScript" else RUST_ROOT
    return (CATALOG_ROOT / language / source.relative_to(root)).with_suffix(".md")


def area_note_path(area: str) -> Path:
    return CATALOG_ROOT / area / "_area.md"


def wikilink(path: Path, alias: str | None = None) -> str:
    target = path.relative_to(VAULT_ROOT).with_suffix("").as_posix()
    return f"[[{target}|{alias or path.stem}]]"


def markdown_link(from_note: Path, target: Path, label: str) -> str:
    relative = os.path.relpath(target, from_note.parent).replace(os.sep, "/")
    return f"[{label}]({relative})"


def yaml_string(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def yaml_list(values: Iterable[object]) -> list[str]:
    values = list(values)
    return [f"  - {yaml_string(value)}" for value in values] if values else ["  []"]


def compact(text: str, limit: int = 260) -> str:
    value = re.sub(r"\s+", " ", text).strip()
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def declaration_signature(text: str, start: int) -> str:
    tail = text[start : start + 700]
    end_positions = [position for marker in ("{", "=>", ";") if (position := tail.find(marker)) >= 0]
    end = min(end_positions) if end_positions else tail.find("\n")
    if end < 0:
        end = min(len(tail), 240)
    return compact(tail[:end], 260)


def typescript_symbols(text: str) -> list[Symbol]:
    pattern = re.compile(
        r"(?m)^[ \t]*(?P<export>export\s+)?(?P<default>default\s+)?(?P<async>async\s+)?"
        r"(?P<kind>function|class|interface|type|enum|const|let)\s+(?P<name>[A-Za-z_$][\w$]*)"
    )
    found: dict[tuple[str, int], Symbol] = {}
    for match in pattern.finditer(text):
        symbol = Symbol(
            name=match.group("name"),
            kind=match.group("kind"),
            line=line_number(text, match.start()),
            signature=declaration_signature(text, match.start()),
            exported=bool(match.group("export")),
        )
        found[(symbol.name, symbol.line)] = symbol
    return sorted(found.values(), key=lambda item: (item.line, item.name))


def rust_symbols(text: str) -> list[Symbol]:
    pattern = re.compile(
        r"(?m)^[ \t]*(?P<pub>pub(?:\([^)]*\))?\s+)?(?P<async>async\s+)?"
        r"(?P<kind>fn|struct|enum|trait|type|const|static)\s+(?P<name>[A-Za-z_][\w]*)"
    )
    found: dict[tuple[str, int], Symbol] = {}
    for match in pattern.finditer(text):
        symbol = Symbol(
            name=match.group("name"),
            kind=match.group("kind"),
            line=line_number(text, match.start()),
            signature=declaration_signature(text, match.start()),
            exported=bool(match.group("pub")),
        )
        found[(symbol.name, symbol.line)] = symbol
    # commands.rs defines many public functions through this local macro.
    for match in re.finditer(r"sidecar_passthrough!\(\s*([A-Za-z_][\w]*)", text):
        name = match.group(1)
        symbol = Symbol(
            name=name,
            kind="fn",
            line=line_number(text, match.start()),
            signature=f"pub async fn {name}(input, sidecar) [expanded by sidecar_passthrough!]",
            exported=True,
            generated_by_macro=True,
        )
        found[(symbol.name, symbol.line)] = symbol
    return sorted(found.values(), key=lambda item: (item.line, item.name))


def provenance(source: Path) -> tuple[str, str, str]:
    relative = source.relative_to(REPO_ROOT).as_posix()
    status = run_git("status", "--porcelain=v1", "--untracked-files=all", "--", relative)
    if not status:
        worktree = "clean"
    elif status.startswith("??"):
        worktree = "untracked"
    elif status[0] != " ":
        worktree = "staged-or-mixed"
    else:
        worktree = "modified"
    log = run_git("log", "-1", "--format=%H%n%cI", "--", relative).splitlines()
    if len(log) >= 2:
        commit, timestamp = log[0], log[1]
    else:
        head = run_git("show", "-s", "--format=%H%n%cI", "HEAD").splitlines()
        commit, timestamp = f"workspace/uncommitted @ {head[0]}", head[1]
    return commit, timestamp, worktree


def resolve_typescript(source: Path, specifier: str, source_set: set[Path]) -> Path | None:
    if not specifier.startswith("."):
        return None
    # Vite loader queries (for example ``./julia.worker?worker``) identify the
    # same authored module while changing how the bundler instantiates it.
    clean_specifier = specifier.split("?", 1)[0]
    base = source.parent / clean_specifier
    candidates = [
        base,
        Path(str(base) + ".ts"),
        Path(str(base) + ".tsx"),
        base.with_suffix(".ts"),
        base.with_suffix(".tsx"),
        base / "index.ts",
        base / "index.tsx",
    ]
    return next((candidate.resolve() for candidate in candidates if candidate.resolve() in source_set), None)


def import_names(clause: str) -> set[str]:
    value = re.sub(r"\btype\s+", "", clause).strip()
    names: set[str] = set()
    namespace = re.search(r"\*\s+as\s+([A-Za-z_$][\w$]*)", value)
    if namespace:
        names.add(namespace.group(1))
    block = re.search(r"\{(.*?)\}", value, re.DOTALL)
    if block:
        for raw in block.group(1).split(","):
            token = raw.strip()
            if not token:
                continue
            alias = re.split(r"\s+as\s+", token)
            names.add(alias[-1].strip())
    prefix = value.split("{", 1)[0].split(",", 1)[0].strip()
    if prefix and prefix not in {"type"} and not prefix.startswith("*"):
        match = re.match(r"([A-Za-z_$][\w$]*)", prefix)
        if match:
            names.add(match.group(1))
    return names


def add_ts_imports(info: SourceInfo, source_set: set[Path]) -> None:
    text = info.text
    statements: list[tuple[str, str, str]] = []
    from_pattern = re.compile(
        r"(?ms)^[ \t]*(?:import|export)\s+(?P<clause>.*?)[ \t]+from[ \t]+[\"'](?P<spec>[^\"']+)[\"'][ \t]*;"
    )
    occupied: list[tuple[int, int]] = []
    for match in from_pattern.finditer(text):
        statements.append((match.group("spec"), match.group("clause"), "import-or-re-export"))
        occupied.append(match.span())
    side_effect = re.compile(r"(?m)^[ \t]*import[ \t]+[\"'](?P<spec>[^\"']+)[\"'][ \t]*;?")
    for match in side_effect.finditer(text):
        statements.append((match.group("spec"), "", "side-effect import"))
    dynamic = re.compile(r"\bimport\(\s*[\"'](?P<spec>[^\"']+)[\"']\s*\)")
    for match in dynamic.finditer(text):
        statements.append((match.group("spec"), "", "dynamic import"))

    for specifier, clause, kind in statements:
        names = import_names(clause)
        referenced = {name for name in names if len(re.findall(rf"\b{re.escape(name)}\b", text)) > 1}
        resolved = resolve_typescript(info.source, specifier, source_set)
        if resolved is not None:
            edge = info.internal_dependencies.setdefault(
                resolved, ImportEdge(resolved, specifier, kind=kind)
            )
            edge.names.update(names)
            edge.referenced_names.update(referenced)
            if kind != "import-or-re-export":
                edge.kind = kind
        elif specifier.startswith("."):
            asset = (info.source.parent / specifier.split("?", 1)[0]).resolve()
            if asset.exists():
                info.asset_dependencies.add(asset)
            else:
                info.external_dependencies.add(f"unresolved local specifier: {specifier}")
        else:
            info.external_dependencies.add(specifier)


def add_rust_imports(info: SourceInfo, rust_by_stem: dict[str, Path]) -> None:
    text = info.text
    for match in re.finditer(r"(?m)^\s*mod\s+([a-z_][\w]*)\s*;", text):
        name = match.group(1)
        if name in rust_by_stem:
            target = rust_by_stem[name]
            info.internal_dependencies[target] = ImportEdge(target, name, kind="module declaration")
    for name in sorted(set(re.findall(r"\bcrate::([a-z_][\w]*)", text))):
        if name in rust_by_stem and rust_by_stem[name] != info.source:
            target = rust_by_stem[name]
            edge = info.internal_dependencies.setdefault(target, ImportEdge(target, f"crate::{name}", kind="crate import"))
            edge.names.add(name)
            edge.referenced_names.add(name)
    for match in re.finditer(r"(?m)^\s*use\s+([a-z_][\w]*)::", text):
        root = match.group(1)
        if root == "std":
            info.std_dependencies.add("std")
        elif root not in {"crate", "self", "super"} and root not in rust_by_stem:
            info.external_dependencies.add(root)


def collect_infos() -> dict[Path, SourceInfo]:
    pairs = source_files()
    source_set = {path.resolve() for path, _ in pairs}
    infos: dict[Path, SourceInfo] = {}
    for source, language in pairs:
        source = source.resolve()
        text = source.read_text(encoding="utf-8")
        commit, timestamp, worktree = provenance(source)
        symbols = typescript_symbols(text) if language == "TypeScript" else rust_symbols(text)
        infos[source] = SourceInfo(
            source=source,
            language=language,
            area=area_for(source, language),
            text=text,
            symbols=symbols,
            commit=commit,
            commit_timestamp=timestamp,
            worktree_state=worktree,
        )
    rust_by_stem = {path.stem: path for path, info in infos.items() if info.language == "Rust"}
    for info in infos.values():
        if info.language == "TypeScript":
            add_ts_imports(info, source_set)
        else:
            add_rust_imports(info, rust_by_stem)
    audit_activation(infos)
    return infos


def entry_reachability(entry: Path, infos: dict[Path, SourceInfo]) -> dict[Path, Path | None]:
    parents: dict[Path, Path | None] = {entry: None}
    queue = [entry]
    while queue:
        current = queue.pop(0)
        for target in sorted(infos[current].internal_dependencies):
            if target not in parents:
                parents[target] = current
                queue.append(target)
    return parents


def reconstruct_chain(target: Path, parents: dict[Path, Path | None]) -> list[Path]:
    chain: list[Path] = []
    current: Path | None = target
    while current is not None:
        chain.append(current)
        current = parents[current]
    return list(reversed(chain))


def audit_activation(infos: dict[Path, SourceInfo]) -> None:
    """Assign lifecycle status only from explicit build/runtime evidence."""
    ts_entry = (TS_ROOT / "main.tsx").resolve()
    rust_entry = (RUST_ROOT / "main.rs").resolve()
    ts_parents = entry_reachability(ts_entry, infos)
    rust_parents = entry_reachability(rust_entry, infos)
    ambient = (TS_ROOT / "vite-env.d.ts").resolve()
    for source, info in infos.items():
        if source in ts_parents:
            info.refactor_status = "ACTIVE"
            info.activation_kind = "entry-reachable build graph"
            info.activation_chain = reconstruct_chain(source, ts_parents)
            if "/fixtures/" in info.relative:
                info.activation_evidence = "Imported through a current Reader/GoldenPath screen reachable from src/main.tsx."
            elif "/startBackdrops/" in info.relative:
                info.activation_evidence = "Imported through StartScreen's supported optional backdrop paths reachable from src/main.tsx."
            else:
                info.activation_evidence = "A static TypeScript import path reaches this file from the Vite entry src/main.tsx."
        elif source == ambient:
            info.refactor_status = "ACTIVE"
            info.activation_kind = "compiler-implicit"
            info.activation_evidence = "tsconfig.json includes src, and this declaration references vite/client for the current frontend build."
        elif source in rust_parents:
            info.refactor_status = "ACTIVE"
            info.activation_kind = "native-entry-reachable"
            info.activation_chain = reconstruct_chain(source, rust_parents)
            info.activation_evidence = "A Rust mod/use edge reaches this crate module from src-tauri/src/main.rs."
        else:
            # A missing edge is not positive evidence for DORMANT, EVALUATION,
            # or COMPAT. New implicit entries require an explicit audit rule.
            raise RuntimeError(
                f"unclassified desktop source {info.source_path}: add explicit activation or lifecycle evidence"
            )


def purpose(info: SourceInfo) -> str:
    if info.relative in SPECIAL_PURPOSES:
        return SPECIAL_PURPOSES[info.relative]
    stem = info.source.stem
    lower = info.relative.lower()
    if "/startbackdrops/" in lower:
        return f"Implements the `{stem}` start-screen visualization or its rendering support."
    if "/screens/" in lower and info.source.suffix == ".tsx":
        return f"Implements the `{stem}` routed desktop screen and coordinates its learner-facing workflow state."
    if "/components/" in lower and info.source.suffix == ".tsx":
        return f"Provides the reusable `{stem}` interaction surface used by one or more desktop workflows."
    if "/components/" in lower:
        return f"Provides shared `{stem}` state or utility behavior for desktop components."
    if "/render/" in lower:
        return f"Adapts `{stem}` content editing or rendering into React presentation behavior."
    if "/fixtures/" in lower:
        return f"Exposes deterministic `{stem}` fixture data for a reproducible desktop scenario."
    exports = [symbol.name for symbol in info.symbols if symbol.exported]
    if exports:
        shown = ", ".join(f"`{name}`" for name in exports[:4])
        suffix = " and related exports" if len(exports) > 4 else ""
        return f"Provides {shown}{suffix} within the desktop's {info.area} ownership area."
    return f"Provides the desktop `{stem}` module within the {info.area} ownership area."


def workflow_links(info: SourceInfo) -> list[tuple[str, str]]:
    lower = info.relative.lower()
    links: list[tuple[str, str]] = [
        ("[[Architecture/Adapter Architecture#Request flow|adapter request flow]]", "places this module on the UI/sidecar boundary"),
    ]
    if any(word in lower for word in ("reader", "pdf", "markdown", "openinsource", "highlight", "pagerange")):
        links += [
            ("[[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]]", "owns the end-to-end reader sequence"),
            ("[[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]]", "owns reader semantics"),
        ]
    if any(word in lower for word in ("practice", "today", "feedback", "review", "queue", "probe", "repair", "causal", "diagnostic", "calibration")):
        links += [
            ("[[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]]", "shows the user-facing session path"),
            ("[[Concepts/Learning System#One attempt|one-attempt model]]", "owns learning semantics"),
        ]
    if "goldenpath" in lower or "golden_path" in lower:
        links += [
            ("[[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]]", "places the staged journey in the user-facing session path"),
            ("[[Concepts/Learning System#The feedback loop|learning feedback loop]]", "owns the learning intent behind the fixture or surface"),
        ]
    if any(word in lower for word in ("repair", "causal", "diagnostic", "adjudication", "probe")):
        links.append(("[[Concepts/Diagnosis and Remediation#Episode lifecycle|diagnosis episode lifecycle]]", "owns diagnostic and repair policy"))
    if any(word in lower for word in ("goal", "exam")):
        links += [
            ("[[Workflows/Goals Exams and Certification Workflow|Goals, Exams, and Certification Workflow]]", "owns the end-to-end goal path"),
            ("[[Concepts/Goals and Certification|Goals and Certification]]", "owns goal and certification semantics"),
        ]
    if any(word in lower for word in ("ingest", "source", "library", "outline", "quickadd", "newvault")):
        links += [
            ("[[Workflows/Import Canonical Sources|Import Canonical Sources]]", "owns import sequencing"),
            ("[[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]]", "owns pipeline persistence semantics"),
        ]
    if any(word in lower for word in ("knowledge", "graph", "facet", "syllabus", "recipe", "studymap")):
        links += [
            ("[[Workflows/Build a Study Map|Build a Study Map]]", "owns the map-building journey"),
            ("[[Concepts/Canonical Knowledge Model#Core entities|canonical knowledge entities]]", "owns graph meaning"),
        ]
    if any(word in lower for word in ("settings", "algo", "animation")):
        links.append(("[[Workflows/Configure AI Providers|Configure AI Providers]]", "owns provider setup"))
    if any(word in lower for word in ("maintenance", "sqlite", "vault_watcher")):
        links += [
            ("[[Workflows/Inspect Persistent State|Inspect Persistent State]]", "owns safe inspection"),
            ("[[Architecture/State and Persistence#Open modes and migrations|state open modes]]", "owns persistence safety"),
        ]
    if info.relative in {"src/main.tsx", "src/app/App.tsx", "src-tauri/src/main.rs"}:
        links += [
            ("[[Architecture/Architecture Overview#Runtime composition|runtime composition]]", "shows this entry point in the whole process graph"),
            ("[[Workflows/Initialize a Vault|Initialize a Vault]]", "owns first-run behavior"),
        ]
    if info.area in {"TypeScript/api", "Rust"}:
        links.append(("[[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]]", "owns the four-layer RPC contract"))
    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    for link, reason in links:
        if link not in seen:
            seen.add(link)
            result.append((link, reason))
    return result


def test_inventory(infos: dict[Path, SourceInfo]) -> tuple[dict[Path, list[tuple[Path, str, str]]], list[Path]]:
    tests = sorted((REPO_ROOT / "tests").rglob("test_*.py"))
    token_sets = {
        test: set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{7,}\b", test.read_text(encoding="utf-8")))
        for test in tests
    }
    symbol_owners: Counter[str] = Counter(
        symbol.name for info in infos.values() for symbol in info.symbols if symbol.exported and len(symbol.name) >= 8
    )
    direct: dict[Path, list[tuple[Path, str, str]]] = defaultdict(list)
    for source, info in infos.items():
        # PascalCase names are useful cross-language contract evidence (DTOs and
        # React surfaces). Lowercase words such as ``initialize`` are too
        # generic to associate with a Rust module merely by token equality.
        unique_symbols = {
            symbol.name
            for symbol in info.symbols
            if symbol.exported
            and symbol_owners[symbol.name] == 1
            and len(symbol.name) >= 8
            and symbol.name[0].isupper()
        }
        for test in tests:
            test_text = test.read_text(encoding="utf-8")
            if info.source_path in test_text or info.relative in test_text:
                direct[source].append((test, "direct source contract", "references the exact source path"))
                continue
            matches = sorted(unique_symbols & token_sets[test])
            if matches:
                shown = ", ".join(f"`{name}`" for name in matches[:4])
                reason = f"references uniquely owned exported name{'s' if len(matches) > 1 else ''} {shown}"
                direct[source].append((test, "cross-boundary name contract", reason))
    return direct, tests


def behavior_tests(info: SourceInfo) -> list[Path]:
    key = info.relative.lower()
    selected: list[Path] = []
    for needles, paths in BEHAVIOR_TEST_RULES:
        if any(needle in key for needle in needles):
            for relative in paths:
                path = REPO_ROOT / relative
                if path.is_file() and path not in selected:
                    selected.append(path)
    return selected[:6]


def frontmatter(info: SourceInfo) -> list[str]:
    tags = [
        "learnloop/docs",
        "learnloop/reference/module",
        "learnloop/desktop",
        f"learnloop/desktop/{info.language.lower()}",
        f"refactor/{info.refactor_status.lower()}",
    ]
    return [
        "---",
        f"title: {yaml_string('Desktop module · ' + info.relative)}",
        'type: "desktop-module-reference"',
        'status: "current"',
        f"refactor_status: {yaml_string(info.refactor_status)}",
        f'version: "{DOC_VERSION}"',
        f"module: {yaml_string(info.module_id)}",
        f"language: {yaml_string(info.language)}",
        f"area: {yaml_string(info.area)}",
        f"source_path: {yaml_string(info.source_path)}",
        "source_paths:",
        *yaml_list([info.source_path]),
        f"source_commit: {yaml_string(info.commit)}",
        f"source_commit_timestamp: {yaml_string(info.commit_timestamp)}",
        f"source_worktree_state: {yaml_string(info.worktree_state)}",
        f"activation_kind: {yaml_string(info.activation_kind)}",
        f"activation_evidence: {yaml_string(info.activation_evidence)}",
        "generated: true",
        f"generated_at: {yaml_string(GENERATED_AT)}",
        "tags:",
        *yaml_list(tags),
        "---",
    ]


def render_module(
    info: SourceInfo,
    infos: dict[Path, SourceInfo],
    inbound: dict[Path, list[tuple[SourceInfo, ImportEdge]]],
    direct_tests: dict[Path, list[tuple[Path, str, str]]],
) -> str:
    path = note_path(info.source, info.language)
    source_link = markdown_link(path, info.source, info.source_path)
    lines = frontmatter(info)
    lines += [
        "",
        f"# `{info.relative}`",
        "",
        f"Area: {wikilink(area_note_path(info.area), info.area)} · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].",
        "",
        "## Why this module exists",
        "",
        purpose(info),
        "",
        "The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.",
        "",
        "^desktop-module-purpose",
        "",
        "## Source facts",
        "",
        "| Fact | Value |",
        "|---|---|",
        f"| Source | {source_link} |",
        f"| Source lines | {len(info.text.splitlines())} |",
        f"| Language | `{info.language}` |",
        f"| Area | {wikilink(area_note_path(info.area), info.area)} |",
        f"| Refactor status | `{info.refactor_status}` |",
        f"| Activation kind | `{info.activation_kind}` |",
        f"| Worktree state | `{info.worktree_state}` |",
        f"| Source commit | `{info.commit}` |",
        f"| Commit timestamp | `{info.commit_timestamp}` |",
        "",
        "## Activation and status evidence",
        "",
        f"> [!success] {info.refactor_status}",
        f"> {info.activation_evidence}",
        ">",
    ]
    if info.activation_chain:
        chain = " → ".join(
            wikilink(note_path(source, infos[source].language), infos[source].relative)
            for source in info.activation_chain
        )
        lines.append(f"> Build/entry chain: {chain}")
    else:
        tsconfig = REPO_ROOT / "apps" / "learnloop-tauri" / "tsconfig.json"
        lines.append(
            f"> Compiler evidence: {markdown_link(path, tsconfig, 'apps/learnloop-tauri/tsconfig.json')}."
        )
    lines += [
        "",
        "## Public API",
        "",
    ]
    exports = [symbol for symbol in info.symbols if symbol.exported]
    if exports:
        for symbol in exports:
            qualifier = "; macro-expanded" if symbol.generated_by_macro else ""
            lines.append(f"- `{symbol.signature}` — {symbol.kind}, line {symbol.line}{qualifier}")
    elif info.relative == "src/main.tsx":
        lines.append("No exported declaration; this file executes as the Vite renderer entry point.")
    elif info.relative == "src/vite-env.d.ts":
        lines.append("No exported declaration; its `vite/client` reference augments the ambient TypeScript environment.")
    elif info.relative == "src-tauri/src/main.rs":
        lines.append("No library export; `fn main` is the Cargo binary entry point.")
    else:
        lines.append("No exported declaration was detected; this is an entry, side-effect, fixture, or file-local module.")
    lines += ["", "## Internal implementation anchors", ""]
    internal = [symbol for symbol in info.symbols if not symbol.exported]
    if internal:
        for symbol in internal:
            lines.append(f"- `{symbol.signature}` — {symbol.kind}, line {symbol.line}")
    else:
        lines.append("No non-exported declaration anchor was detected by the static extractor.")
    lines += [
        "",
        "## Who imports or calls it",
        "",
        "> [!note] Static-evidence boundary",
        "> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.",
        "",
    ]
    consumers = inbound.get(info.source, [])
    if consumers:
        for consumer, edge in consumers:
            imported = ", ".join(f"`{name}`" for name in sorted(edge.names)) or edge.kind
            used = ", ".join(f"`{name}`" for name in sorted(edge.referenced_names))
            suffix = f"; references {used}" if used else "; no named call claim"
            lines.append(f"- {wikilink(note_path(consumer.source, consumer.language), consumer.relative)} — {edge.kind}: {imported}{suffix}")
    elif info.relative == "src/main.tsx":
        html = REPO_ROOT / "apps" / "learnloop-tauri" / "index.html"
        lines.append(f"- {markdown_link(path, html, 'apps/learnloop-tauri/index.html')} — Vite HTML entry loads `/src/main.tsx`.")
    elif info.relative == "src/vite-env.d.ts":
        tsconfig = REPO_ROOT / "apps" / "learnloop-tauri" / "tsconfig.json"
        lines.append(f"- {markdown_link(path, tsconfig, 'apps/learnloop-tauri/tsconfig.json')} — compiler inclusion under `src`; no explicit import is required.")
    elif info.relative == "src-tauri/src/main.rs":
        cargo = REPO_ROOT / "apps" / "learnloop-tauri" / "src-tauri" / "Cargo.toml"
        lines.append(f"- {markdown_link(path, cargo, 'apps/learnloop-tauri/src-tauri/Cargo.toml')} — Cargo binary entry point.")
    else:
        lines.append("No live desktop source file directly imports this module. Do not infer dormancy: it can still be an implicit entry, worker, ambient declaration, fixture, or runtime-dispatched surface.")
    lines += ["", "## Dependencies", "", "### Desktop source modules", ""]
    if info.internal_dependencies:
        for target, edge in sorted(info.internal_dependencies.items(), key=lambda item: item[0].as_posix()):
            target_info = infos[target]
            names = ", ".join(f"`{name}`" for name in sorted(edge.names))
            detail = f"; imports {names}" if names else ""
            lines.append(f"- {wikilink(note_path(target, target_info.language), target_info.relative)} — {edge.kind}{detail}")
    else:
        lines.append("No local TypeScript/TSX or Rust module dependency was detected.")
    lines += ["", "### Assets, platform, and third-party dependencies", ""]
    dep_lines: list[str] = []
    for asset in sorted(info.asset_dependencies):
        dep_lines.append(f"- Local asset: {markdown_link(path, asset, asset.relative_to(REPO_ROOT).as_posix())}")
    if info.std_dependencies:
        dep_lines.append("- Rust standard library: " + ", ".join(f"`{item}`" for item in sorted(info.std_dependencies)))
    if info.external_dependencies:
        dep_lines.append("- Imported packages/crates: " + ", ".join(f"`{item}`" for item in sorted(info.external_dependencies)))
    lines += dep_lines or ["No explicit asset, standard-library, package, or crate dependency was detected."]
    lines += ["", "## Larger desktop and workflow participation", ""]
    for link, reason in workflow_links(info):
        lines.append(f"- {link} — {reason}.")
    lines += [
        "",
        "The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.",
        "",
        "## Tests that define behavior",
        "",
    ]
    listed: set[Path] = set()
    for test, evidence, reason in direct_tests.get(info.source, [])[:8]:
        disclaimer = "" if evidence == "direct source contract" else "; it does **not** directly execute this source module"
        lines.append(f"- {markdown_link(path, test, test.relative_to(REPO_ROOT).as_posix())} — {evidence}: {reason}{disclaimer}.")
        listed.add(test)
    if "#[cfg(test)]" in info.text:
        lines.append(f"- {source_link} — inline Rust unit-test module; run with `cargo test` from `apps/learnloop-tauri/src-tauri`.")
    for test in behavior_tests(info):
        if test not in listed:
            lines.append(f"- {markdown_link(path, test, test.relative_to(REPO_ROOT).as_posix())} — related cross-boundary behavior contract; it does **not** directly execute this source module.")
            listed.add(test)
    if not listed and "#[cfg(test)]" not in info.text:
        lines.append("- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.")
    lines += ["", "## Modification guidance", ""]
    lower = info.relative.lower()
    if info.language == "TypeScript" and ("/screens/" in lower or "/components/" in lower):
        lines += [
            "- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.",
            "- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.",
        ]
    elif info.area == "TypeScript/api":
        lines += [
            "- Add or change an RPC in all four layers: DTO, client facade, Rust command/registration, and Python sidecar handler/registry.",
            "- Preserve camelCase wire names and typed error behavior; exercise `tests/test_desktop_rpc_contract.py` plus the feature's sidecar tests.",
        ]
    elif info.language == "Rust":
        lines += [
            "- Keep native code an adapter: process/protocol/window/filesystem concerns belong here, while learning rules and durable state interpretation stay in Python domains.",
            "- Command changes must remain synchronized with `src/api/client.ts`, `src/api/dto.ts`, `main.rs` registration, and the Python sidecar registry.",
        ]
    else:
        lines.append("- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.")
    lines += [
        "- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.",
        "- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.",
        "",
        "### Regeneration checklist",
        "",
        f"1. Modify {source_link} and focused tests.",
        "2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.",
        "3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_area(area: str, members: list[SourceInfo], child_areas: list[str], head_commit: str, head_timestamp: str) -> str:
    path = area_note_path(area)
    source_dir = TS_ROOT if area == "TypeScript" else RUST_ROOT if area == "Rust" else TS_ROOT / area.removeprefix("TypeScript/")
    source_path = source_dir.relative_to(REPO_ROOT).as_posix()
    lines = [
        "---",
        f"title: {yaml_string('Desktop area · ' + area)}",
        'type: "desktop-area-map"',
        'status: "current"',
        'refactor_status: "ACTIVE"',
        f'version: "{DOC_VERSION}"',
        "source_paths:",
        *yaml_list([source_path]),
        f"source_commit: {yaml_string(head_commit)}",
        f"source_commit_timestamp: {yaml_string(head_timestamp)}",
        "generated: true",
        f"generated_at: {yaml_string(GENERATED_AT)}",
        "tags:",
        *yaml_list(["learnloop/docs", "learnloop/moc", "learnloop/desktop", "learnloop/desktop/area"]),
        "---",
        "",
        f"# {area}",
        "",
        f"Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: {markdown_link(path, source_dir, source_path)}",
        "",
        "## Responsibility",
        "",
        AREA_RESPONSIBILITIES[area],
        "",
        "> [!note] Ownership boundary",
        "> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.",
        "",
        "## Child areas",
        "",
    ]
    if child_areas:
        for child in child_areas:
            lines.append(f"- {wikilink(area_note_path(child), child)} — {AREA_RESPONSIBILITIES[child]}")
    else:
        lines.append("No nested ownership area.")
    lines += ["", "## Direct modules", "", "| Module | Status | Purpose | Imports | Imported by |", "|---|---|---|---:|---:|"]
    # Inbound counts are supplied later by a temporary attribute-free scan.
    for info in sorted(members, key=lambda item: item.relative):
        lines.append(
            f"| {wikilink(note_path(info.source, info.language), info.source.name)} | `{info.refactor_status}` | {purpose(info).replace('|', r'\|')} | {len(info.internal_dependencies)} | {{INBOUND:{info.source_path}}} |"
        )
    if not members:
        lines.append("| — | — | This area contains only child areas. | 0 | 0 |")
    lines += [
        "",
        "## Modification guidance",
        "",
        "Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.",
        "",
        "## Related notes",
        "",
        "- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]",
        "- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]",
        "- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_catalog(infos: dict[Path, SourceInfo], areas: list[str], head_commit: str, head_timestamp: str) -> str:
    path = CATALOG_ROOT / "Desktop Module Catalog.md"
    ts_count = sum(info.language == "TypeScript" for info in infos.values())
    rust_count = sum(info.language == "Rust" for info in infos.values())
    status_counts = Counter(info.refactor_status for info in infos.values())
    ts_entry_reachable = sum(info.activation_kind == "entry-reachable build graph" for info in infos.values())
    rust_entry_reachable = sum(info.activation_kind == "native-entry-reachable" for info in infos.values())
    compiler_implicit = sum(info.activation_kind == "compiler-implicit" for info in infos.values())
    fixture_count = sum("/fixtures/" in info.relative for info in infos.values())
    backdrop_count = sum("/startBackdrops/" in info.relative for info in infos.values())
    lines = [
        "---",
        'title: "Desktop Module Catalog"',
        'type: "map-of-content"',
        'status: "current"',
        'refactor_status: "ACTIVE"',
        f'version: "{DOC_VERSION}"',
        "source_paths:",
        *yaml_list(["apps/learnloop-tauri/src", "apps/learnloop-tauri/src-tauri/src"]),
        f"source_commit: {yaml_string(head_commit)}",
        f"source_commit_timestamp: {yaml_string(head_timestamp)}",
        "generated: true",
        f"generated_at: {yaml_string(GENERATED_AT)}",
        "tags:",
        *yaml_list(["learnloop/docs", "learnloop/moc", "learnloop/desktop", "learnloop/desktop/module-catalog"]),
        "---",
        "",
        "# Desktop Module Catalog",
        "",
        "> [!abstract] Exact coverage",
        f"> One generated note exists for each of the **{ts_count} live TypeScript/TSX modules** under `apps/learnloop-tauri/src` and **{rust_count} authored Rust crate modules** under `src-tauri/src`. Cargo `target/` output and `build.rs` are not runtime crate modules and are intentionally excluded.",
        "",
        "^desktop-catalog-coverage",
        "",
        "## Runtime bridge",
        "",
        "```mermaid",
        "flowchart LR",
        '  UI[React screens and components] --> DTO[api/dto.ts contracts]',
        '  DTO --> CLIENT[api/client.ts invoke facade]',
        '  CLIENT --> COMMANDS[Rust commands.rs]',
        '  COMMANDS --> MANAGER[Rust SidecarManager]',
        '  MANAGER --> PY[Python learnloop_sidecar registry]',
        '  WATCH[Rust VaultWatcher] --> MANAGER',
        '  PY --> DOMAIN[Python domain owners and SQLite]',
        "```",
        "",
        "The diagram makes the cross-language request boundary explicit: TypeScript presents and adapts, Rust owns native transport/process concerns, and Python remains the learning and persistent-state authority. See [[Architecture/Adapter Architecture#Request flow|request flow]].",
        "",
        "## Area maps",
        "",
        "| Area | Direct modules | Responsibility |",
        "|---|---:|---|",
    ]
    for area in areas:
        count = sum(info.area == area for info in infos.values())
        lines.append(f"| {wikilink(area_note_path(area), area)} | {count} | {AREA_RESPONSIBILITIES[area]} |")
    lines += [
        "",
        "## Status and evidence",
        "",
        "| Refactor status | Modules | Positive evidence required |",
        "|---|---:|---|",
        f"| `ACTIVE` | {status_counts.get('ACTIVE', 0)} | Current entry/build reachability or an explicit compiler inclusion. |",
        f"| `DORMANT` | {status_counts.get('DORMANT', 0)} | An owned retained seam plus evidence that no primary workflow uses it. |",
        f"| `COMPAT` | {status_counts.get('COMPAT', 0)} | An explicitly frozen compatibility contract. |",
        f"| `EVALUATION` | {status_counts.get('EVALUATION', 0)} | A simulation/audit surface that measures rather than serves the learner. |",
        "",
        f"The audit proves **{ts_entry_reachable} TypeScript/TSX files** are reachable through static imports from `src/main.tsx`, **{compiler_implicit} ambient declaration** is included by `tsconfig.json`, and **{rust_entry_reachable} Rust modules** are reachable by `mod`/`crate` edges from native `main.rs`.",
        "",
        f"The reachability set includes all **{fixture_count} authored fixture modules** through current Reader/GoldenPath screens and all **{backdrop_count} backdrop/worker modules** through StartScreen's supported optional presentation paths. Entry files are active roots. Therefore all {len(infos)} files are `ACTIVE`; none has positive evidence for `DORMANT`, `COMPAT`, or `EVALUATION`.",
        "",
        "> [!warning] Static graph limits",
        "> Import and symbol-reference edges are reproducible build evidence, not runtime tracing. The generator refuses an unclassified file instead of treating a missing caller as proof of dormancy; a new implicit entry requires an explicit audit rule.",
        "",
        "## Find a desktop module",
        "",
        "```query",
        'path:"Reference/Desktop" tag:#learnloop/desktop/typescript',
        "```",
        "",
        "```query",
        'path:"Reference/Desktop" section:("Modification guidance") "RPC"',
        "```",
        "",
        "> [!tip] Optional Dataview index",
        "> The vault works without Dataview; when enabled, this produces a sortable source table.",
        "",
        "```dataview",
        'TABLE language AS Language, area AS Area, source_path AS Source, source_commit_timestamp AS Commit',
        'FROM "Reference/Desktop"',
        'WHERE type = "desktop-module-reference"',
        "SORT source_path ASC",
        "```",
        "",
        "## How to change the desktop safely",
        "",
        "1. Locate a module through its area map and inspect inbound consumers and outbound dependencies.",
        "2. Follow the canonical workflow/concept links for semantics; do not derive learning policy from UI wording.",
        "3. For an RPC shape change, keep TypeScript DTO/client, Rust command registration/bridge, and Python handler/registry synchronized.",
        "4. Run the focused cross-boundary tests, frontend typecheck/build, and Rust tests named in the module note.",
        "5. Regenerate and validate this reference.",
        "",
        "## Maintenance",
        "",
        "```bash",
        ".venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py",
        ".venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py",
        "```",
        "",
        "Use `desktop_generate.py --check` in CI to verify byte-for-byte reproducibility without writing files.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def rendered_files() -> dict[Path, str]:
    infos = collect_infos()
    inbound: dict[Path, list[tuple[SourceInfo, ImportEdge]]] = defaultdict(list)
    for consumer in infos.values():
        for target, edge in consumer.internal_dependencies.items():
            inbound[target].append((consumer, edge))
    for consumers in inbound.values():
        consumers.sort(key=lambda item: item[0].relative)
    direct_tests, _ = test_inventory(infos)
    rendered: dict[Path, str] = {}
    for info in infos.values():
        rendered[note_path(info.source, info.language)] = render_module(info, infos, inbound, direct_tests)

    areas = sorted({info.area for info in infos.values()})
    head = run_git("show", "-s", "--format=%H%n%cI", "HEAD").splitlines()
    head_commit, head_timestamp = head[0], head[1]
    inbound_counts = {path: len(consumers) for path, consumers in inbound.items()}
    for area in areas:
        members = [info for info in infos.values() if info.area == area]
        prefix = area + "/"
        children = sorted(
            candidate for candidate in areas
            if candidate.startswith(prefix) and "/" not in candidate[len(prefix):]
        )
        body = render_area(area, members, children, head_commit, head_timestamp)
        for info in members:
            body = body.replace(f"{{INBOUND:{info.source_path}}}", str(inbound_counts.get(info.source, 0)))
        rendered[area_note_path(area)] = body
    rendered[CATALOG_ROOT / "Desktop Module Catalog.md"] = render_catalog(infos, areas, head_commit, head_timestamp)
    return rendered


def main() -> int:
    check = sys.argv[1:] == ["--check"]
    if sys.argv[1:] and not check:
        print("usage: desktop_generate.py [--check]", file=sys.stderr)
        return 2
    rendered = rendered_files()
    actual = set(CATALOG_ROOT.rglob("*.md")) if CATALOG_ROOT.exists() else set()
    expected = set(rendered)
    if check:
        errors: list[str] = []
        for path, content in sorted(rendered.items()):
            if not path.is_file():
                errors.append(f"missing: {path.relative_to(REPO_ROOT)}")
            elif path.read_text(encoding="utf-8") != content:
                errors.append(f"stale: {path.relative_to(REPO_ROOT)}")
        for path in sorted(actual - expected):
            errors.append(f"unexpected: {path.relative_to(REPO_ROOT)}")
        if errors:
            print("Desktop catalog is not reproducible:", file=sys.stderr)
            print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
            return 1
        print(f"Desktop catalog reproducibility passed: {len(rendered)} generated notes")
        return 0

    CATALOG_ROOT.mkdir(parents=True, exist_ok=True)
    for stale in sorted(actual - expected):
        stale.unlink()
    for path, content in sorted(rendered.items()):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    ts_count = sum(path.is_relative_to(CATALOG_ROOT / "TypeScript") and path.name != "_area.md" for path in rendered)
    rust_count = sum(path.is_relative_to(CATALOG_ROOT / "Rust") and path.name != "_area.md" for path in rendered)
    area_count = sum(path.name == "_area.md" for path in rendered)
    print(f"Generated {ts_count} TypeScript/TSX notes, {rust_count} Rust notes, {area_count} area maps, and 1 catalog")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
