#!/usr/bin/env python3
"""Generate the Obsidian module reference catalog from the live Python tree.

This script intentionally uses only the Python standard library.  It extracts
facts (imports, definitions, docstrings, source locations, test references,
and git provenance) instead of importing LearnLoop, so running it cannot open
or mutate a vault.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
VAULT_ROOT = REPO_ROOT / "docs" / "learnloop-architecture-vault"
CATALOG_ROOT = VAULT_ROOT / "Reference" / "Modules"
SOURCE_ROOTS = (REPO_ROOT / "src" / "learnloop", REPO_ROOT / "src" / "learnloop_sidecar")
DESKTOP_ROOT = REPO_ROOT / "apps" / "learnloop-tauri"
DOC_VERSION = "1.0.0"
GENERATED_DATE = "2026-08-18"

CANONICAL_CONCEPTS = {
    "Architecture Overview",
    "Learning System",
    "AI Architecture",
    "State and Persistence",
    "Configuration",
}
CANONICAL_WORKFLOWS = {
    "Initialize a Vault",
    "Start a Learning Cycle",
    "Import Canonical Sources",
    "Process Model Output",
    "Inspect Persistent State",
}

PACKAGE_DESCRIPTIONS = {
    "learnloop": "Application-level coordinators and dependency-neutral authorities shared across LearnLoop.",
    "learnloop.ai": "Provider-neutral structured transport, routing, provider composition, capability checks, and usage accounting.",
    "learnloop.ai.providers": "Concrete AI transport adapters behind the provider-neutral contract.",
    "learnloop.attempts": "Attempt acceptance, grading, interaction evidence, feedback, and post-attempt processing.",
    "learnloop.cli": "Typer command adapters, rendering, argument contracts, and command registration.",
    "learnloop.config": "Typed configuration schema, compatibility normalization, loading, and template emission.",
    "learnloop.content": "Source-derived content, authoring, synthesis, proposal, and canonical pipeline ownership.",
    "learnloop.content.authoring": "Practice-content authoring gates, generation contracts, and authored artifacts.",
    "learnloop.content.pipeline": "Canonical content extraction and transformation stages.",
    "learnloop.content.proposals": "Reviewable content and graph change proposals and their lifecycle.",
    "learnloop.content.sources": "Canonical source-library identity, manifests, and source-set behavior.",
    "learnloop.content.synthesis": "Synthesis of source material into learning structures and AI-owned contracts.",
    "learnloop.curriculum": "Commitments, blueprints, depth structures, concept relationships, and golden paths.",
    "learnloop.db": "SQLite connections, migrations, repository compatibility, table roles, rebuilds, and persistence infrastructure.",
    "learnloop.db.stores": "Table-family persistence owners extracted from the repository facade.",
    "learnloop.diagnosis": "Diagnostic probes, causal attribution, error classification, and remediation decisions.",
    "learnloop.goals": "Learning goals, forecasts, certification, readiness, and exam workflows.",
    "learnloop.ingest": "Acquisition intermediate representation, locators, fetchers, originals, and ingestion orchestration.",
    "learnloop.ingest.extractors": "Format-specific extraction adapters for canonical sources.",
    "learnloop.learner": "Mastery, recall, evidence, claims, ability transitions, and learner-state views.",
    "learnloop.ops": "Vault diagnostics, locks, settings, startup, upgrades, and operator-facing maintenance.",
    "learnloop.params": "Algorithm parameter registry, fitted values, and sensitivity certificates.",
    "learnloop.reader": "Reader-mode source exploration, annotations, quick checks, and authoring handoffs.",
    "learnloop.scheduling": "Selection, review timing, progression, controller decisions, and scheduling projections.",
    "learnloop.sim": "Offline simulation, benchmark, sweep, synthetic-student, and algorithm evaluation tools.",
    "learnloop.substrate": "Activity, card, surface, and identity substrate plus canonical projections.",
    "learnloop.substrate.compat": "Frozen compatibility machinery retained for old vaults.",
    "learnloop.tui": "Textual UI adapter, screens, widgets, state, and presentation behavior.",
    "learnloop.tui.screens": "Individual Textual user-interface screens.",
    "learnloop.tutor": "Tutoring, hints, teach-back, and tutor question-and-answer workflows.",
    "learnloop.vault": "Filesystem layout, Markdown/YAML I/O, hashes, models, loading, and writing.",
    "learnloop_sidecar": "Desktop sidecar process, RPC registry, transport context, DTOs, and server lifecycle.",
    "learnloop_sidecar.handlers": "RPC adapters that validate requests and delegate to domain and infrastructure APIs.",
}

PRIMITIVE_MODULES = {
    "learnloop.attempt_types",
    "learnloop.clock",
    "learnloop.ids",
    "learnloop.numeric",
}

ROLE_LINKS = {
    "ai": (["AI Architecture", "Architecture Overview"], ["Process Model Output"]),
    "attempts": (["Learning System"], ["Start a Learning Cycle", "Inspect Persistent State"]),
    "learner": (["Learning System"], ["Start a Learning Cycle", "Inspect Persistent State"]),
    "scheduling": (["Learning System"], ["Start a Learning Cycle"]),
    "goals": (["Learning System"], ["Start a Learning Cycle", "Inspect Persistent State"]),
    "diagnosis": (["Learning System"], ["Start a Learning Cycle", "Process Model Output"]),
    "curriculum": (["Learning System"], ["Start a Learning Cycle", "Import Canonical Sources"]),
    "substrate": (["Learning System", "State and Persistence"], ["Start a Learning Cycle", "Inspect Persistent State"]),
    "content": (["Learning System", "AI Architecture"], ["Import Canonical Sources", "Process Model Output"]),
    "reader": (["Learning System"], ["Import Canonical Sources", "Start a Learning Cycle"]),
    "tutor": (["Learning System", "AI Architecture"], ["Start a Learning Cycle", "Process Model Output"]),
    "db": (["State and Persistence", "Architecture Overview"], ["Initialize a Vault", "Inspect Persistent State"]),
    "config": (["Configuration", "Architecture Overview"], ["Initialize a Vault"]),
    "vault": (["State and Persistence"], ["Initialize a Vault", "Inspect Persistent State"]),
    "ingest": (["Architecture Overview"], ["Import Canonical Sources"]),
    "ops": (["State and Persistence", "Configuration"], ["Initialize a Vault", "Inspect Persistent State"]),
    "params": (["Learning System", "Configuration"], ["Start a Learning Cycle"]),
    "sim": (["Learning System"], []),
    "cli": (["Architecture Overview"], ["Initialize a Vault", "Start a Learning Cycle", "Import Canonical Sources", "Inspect Persistent State"]),
    "tui": (["Architecture Overview"], ["Start a Learning Cycle", "Inspect Persistent State"]),
    "sidecar": (["Architecture Overview"], ["Initialize a Vault", "Start a Learning Cycle", "Import Canonical Sources", "Process Model Output", "Inspect Persistent State"]),
    "root": (["Architecture Overview"], ["Initialize a Vault", "Start a Learning Cycle"]),
}

# Runtime/refactor status is evidence-based, not inferred from a missing static
# caller.  These exceptions are intentionally small and point at explicit source
# contracts (DESCOPED, SHADOW ONLY, zero-authority, or disabled admission).
DORMANT_MODULES = {
    "learnloop.scheduling.kinship_feature",
    "learnloop.scheduling.prequential",
}

EVALUATION_MODULES = {
    "learnloop.diagnosis.causal_diagnostic_selector",
    "learnloop.diagnosis.causal_selection_audit",
    "learnloop.scheduling.intent_planner",
    "learnloop.scheduling.shadow_components",
}

MODULE_WORKFLOW_OVERRIDES: dict[str, list[str]] = {
    "learnloop.scheduling.kinship_feature": [],
    "learnloop.scheduling.prequential": [],
    "learnloop.scheduling.shadow_components": [],
    "learnloop.scheduling.intent_planner": ["Start a Learning Cycle"],
    "learnloop.scheduling.open_world_gate": ["Doctor Migrations and Recovery"],
    "learnloop.diagnosis.causal_diagnostic_selector": ["Process Model Output"],
    "learnloop.diagnosis.causal_selection_audit": ["Process Model Output"],
}

OPERATIONAL_SCOPE_NOTES = {
    "learnloop.scheduling.open_world_gate": (
        "ACTIVE dependency-gate reporter; open-world expansion workers, schema, "
        "and successor UI are NOT_IMPLEMENTED"
    ),
}


@dataclass(slots=True)
class Symbol:
    name: str
    kind: str
    line: int
    signature: str
    summary: str
    methods: list["Symbol"] = field(default_factory=list)


@dataclass(slots=True)
class ImportEdge:
    importer: str
    target: str
    imported_names: set[str] = field(default_factory=set)
    called_names: set[str] = field(default_factory=set)


@dataclass(slots=True)
class ModuleInfo:
    name: str
    source: Path
    package: str
    tree: ast.Module
    docstring: str
    symbols: list[Symbol]
    constants: list[tuple[str, int]]
    all_exports: list[str]
    loc: int
    status: str
    layer: str
    source_state: str
    commit: str
    commit_timestamp: str
    internal_dependencies: dict[str, ImportEdge] = field(default_factory=dict)
    stdlib_dependencies: set[str] = field(default_factory=set)
    external_dependencies: set[str] = field(default_factory=set)


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, text=True, capture_output=True
    )
    return result.stdout.strip()


def module_name(source: Path) -> str:
    rel = source.relative_to(REPO_ROOT / "src").with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def package_name(source: Path, name: str) -> str:
    if source.name == "__init__.py":
        return name
    return name.rpartition(".")[0]


def note_path_for_source(source: Path) -> Path:
    return CATALOG_ROOT / source.relative_to(REPO_ROOT / "src").with_suffix(".md")


def moc_path(package: str) -> Path:
    return CATALOG_ROOT.joinpath(*package.split("."), "_package.md")


def module_link(name: str, modules: dict[str, ModuleInfo], *, alias: str | None = None) -> str:
    info = modules[name]
    target = note_path_for_source(info.source).relative_to(VAULT_ROOT).with_suffix("").as_posix()
    label = alias or name
    return f"[[{target}|{label}]]"


def package_link(package: str, *, alias: str | None = None) -> str:
    target = moc_path(package).relative_to(VAULT_ROOT).with_suffix("").as_posix()
    return f"[[{target}|{alias or package}]]"


def yaml_string(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def yaml_list(values: Iterable[object], indent: int = 0) -> list[str]:
    prefix = " " * indent
    values = list(values)
    if not values:
        return [f"{prefix}[]"]
    return [f"{prefix}- {yaml_string(value)}" for value in values]


def one_line(text: str, *, max_length: int = 280) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return ""
    match = re.match(r"(.+?[.!?])(?:\s|$)", compact)
    sentence = match.group(1) if match else compact
    if len(sentence) <= max_length:
        return sentence
    return sentence[: max_length - 1].rstrip() + "…"


def humanize(name: str) -> str:
    return name.strip("_").replace("_", " ") or name


def safe_unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return "…"


def function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    args = safe_unparse(node.args)
    returns = f" -> {safe_unparse(node.returns)}" if node.returns else ""
    return f"{prefix}{node.name}({args}){returns}"


def symbol_from_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Symbol:
    return Symbol(
        name=node.name,
        kind="async function" if isinstance(node, ast.AsyncFunctionDef) else "function",
        line=node.lineno,
        signature=function_signature(node),
        summary=one_line(ast.get_docstring(node) or ""),
    )


def symbols_from_tree(tree: ast.Module) -> tuple[list[Symbol], list[tuple[str, int]], list[str]]:
    symbols: list[Symbol] = []
    constants: list[tuple[str, int]] = []
    exports: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(symbol_from_function(node))
        elif isinstance(node, ast.ClassDef):
            bases = ", ".join(safe_unparse(base) for base in node.bases)
            methods = [
                symbol_from_function(child)
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            symbols.append(
                Symbol(
                    name=node.name,
                    kind="class",
                    line=node.lineno,
                    signature=f"class {node.name}({bases})" if bases else f"class {node.name}",
                    summary=one_line(ast.get_docstring(node) or ""),
                    methods=methods,
                )
            )
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets: list[ast.expr]
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
                value = node.value
            else:
                targets = [node.target]
                value = node.value
            for target in targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    constants.append((target.id, node.lineno))
                if isinstance(target, ast.Name) and target.id == "__all__" and value is not None:
                    try:
                        literal = ast.literal_eval(value)
                    except (ValueError, TypeError, SyntaxError):
                        literal = ()
                    if isinstance(literal, (list, tuple)):
                        exports.extend(str(item) for item in literal if isinstance(item, str))
    return symbols, constants, exports


def source_files() -> list[Path]:
    return sorted(path for root in SOURCE_ROOTS for path in root.rglob("*.py"))


def desktop_source_count() -> int:
    frontend = DESKTOP_ROOT / "src"
    rust = DESKTOP_ROOT / "src-tauri" / "src"
    return sum(1 for path in frontend.rglob("*") if path.suffix in {".ts", ".tsx"}) + sum(
        1 for path in rust.rglob("*.rs")
    )


def package_names(sources: list[Path]) -> set[str]:
    result: set[str] = set()
    for source in sources:
        parent = source.parent
        while parent != REPO_ROOT / "src":
            if parent == REPO_ROOT / "src":
                break
            result.add(".".join(parent.relative_to(REPO_ROOT / "src").parts))
            if parent in SOURCE_ROOTS:
                break
            parent = parent.parent
    return result


def git_state_sets() -> tuple[set[str], set[str], set[str]]:
    modified = set(filter(None, run_git("diff", "--name-only").splitlines()))
    staged = set(filter(None, run_git("diff", "--cached", "--name-only").splitlines()))
    untracked = set(
        filter(None, run_git("ls-files", "--others", "--exclude-standard").splitlines())
    )
    return modified, staged, untracked


def classify_layer(name: str) -> str:
    if name in PRIMITIVE_MODULES:
        return "primitive"
    if name.startswith("learnloop_sidecar"):
        return "adapter"
    second = name.split(".")[1] if "." in name else "root"
    if second in {"config", "vault", "db", "ingest", "ai"}:
        return "infrastructure"
    if second in {"cli", "tui"}:
        return "adapter"
    if second == "sim":
        return "simulation"
    if second == "root" or name in {
        "learnloop.bootstrap",
        "learnloop.app_launch",
        "learnloop.migration_coordinator",
    }:
        return "coordination"
    return "domain"


def classify_status(name: str) -> str:
    if name == "learnloop.substrate.compat" or name.startswith("learnloop.substrate.compat."):
        return "COMPAT"
    if name in DORMANT_MODULES:
        return "DORMANT"
    if name.startswith("learnloop.sim") or name in EVALUATION_MODULES:
        return "EVALUATION"
    return "ACTIVE"


def load_modules(sources: list[Path]) -> dict[str, ModuleInfo]:
    modified, staged, untracked = git_state_sets()
    head_hash, head_time = run_git("show", "-s", "--format=%H%x09%cI", "HEAD").split("\t", 1)
    modules: dict[str, ModuleInfo] = {}
    for source in sources:
        rel = source.relative_to(REPO_ROOT).as_posix()
        text = source.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=rel)
        name = module_name(source)
        symbols, constants, exports = symbols_from_tree(tree)
        if rel in untracked:
            source_state = "untracked"
        elif rel in modified or rel in staged:
            source_state = "modified"
        else:
            source_state = "clean"
        if source_state != "clean":
            commit = f"workspace/uncommitted @ HEAD {head_hash}"
            commit_timestamp = head_time
        else:
            history = run_git("log", "-1", "--format=%H%x09%cI", "--", rel)
            if history:
                commit, commit_timestamp = history.split("\t", 1)
            else:
                commit = f"workspace/uncommitted @ HEAD {head_hash}"
                commit_timestamp = head_time
                source_state = "untracked"
        modules[name] = ModuleInfo(
            name=name,
            source=source,
            package=package_name(source, name),
            tree=tree,
            docstring=ast.get_docstring(tree) or "",
            symbols=symbols,
            constants=constants,
            all_exports=exports,
            loc=len(text.splitlines()),
            status=classify_status(name),
            layer=classify_layer(name),
            source_state=source_state,
            commit=commit,
            commit_timestamp=commit_timestamp,
        )
    return modules


def resolve_from_base(node: ast.ImportFrom, current: ModuleInfo) -> str:
    if node.level == 0:
        return node.module or ""
    package = current.name if current.source.name == "__init__.py" else current.name.rpartition(".")[0]
    relative = "." * node.level + (node.module or "")
    try:
        import importlib.util

        return importlib.util.resolve_name(relative, package)
    except (ImportError, ValueError):
        return ""


def best_internal_target(name: str, module_names: set[str], packages: set[str]) -> str | None:
    if name in module_names or name in packages:
        return name
    parts = name.split(".")
    while len(parts) > 1:
        parts.pop()
        candidate = ".".join(parts)
        if candidate in module_names or candidate in packages:
            return candidate
    return None


def collect_imports(modules: dict[str, ModuleInfo], packages: set[str]) -> dict[str, dict[str, ImportEdge]]:
    module_names = set(modules)
    inbound: dict[str, dict[str, ImportEdge]] = defaultdict(dict)
    stdlib = set(sys.stdlib_module_names)
    for current in modules.values():
        local_bindings: dict[str, tuple[str, str | None, bool]] = {}
        raw_edges: dict[str, ImportEdge] = {}
        for node in ast.walk(current.tree):
            if isinstance(node, ast.ImportFrom):
                base = resolve_from_base(node, current)
                for alias in node.names:
                    if alias.name == "*":
                        candidate_name = base
                    else:
                        candidate_name = f"{base}.{alias.name}" if base else alias.name
                    exact_child = candidate_name if candidate_name in module_names else None
                    target = exact_child or best_internal_target(base, module_names, packages)
                    if target and target.startswith(("learnloop", "learnloop_sidecar")):
                        imported_name = "module" if exact_child else alias.name
                        edge = raw_edges.setdefault(
                            target, ImportEdge(importer=current.name, target=target)
                        )
                        edge.imported_names.add(imported_name)
                        local = alias.asname or alias.name
                        local_bindings[local] = (target, None if exact_child else alias.name, bool(exact_child))
                    else:
                        root = (base or alias.name).split(".")[0]
                        if root in stdlib:
                            current.stdlib_dependencies.add(root)
                        elif root:
                            current.external_dependencies.add(root)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    target = best_internal_target(alias.name, module_names, packages)
                    if target and target.startswith(("learnloop", "learnloop_sidecar")):
                        edge = raw_edges.setdefault(
                            target, ImportEdge(importer=current.name, target=target)
                        )
                        edge.imported_names.add("module")
                        local = alias.asname or alias.name.split(".")[0]
                        local_bindings[local] = (target, None, True)
                    else:
                        root = alias.name.split(".")[0]
                        if root in stdlib:
                            current.stdlib_dependencies.add(root)
                        else:
                            current.external_dependencies.add(root)
        for node in ast.walk(current.tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name) and func.id in local_bindings:
                target, imported_name, is_module = local_bindings[func.id]
                if not is_module and imported_name:
                    raw_edges[target].called_names.add(imported_name)
            elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                binding = local_bindings.get(func.value.id)
                if binding:
                    target, _, is_module = binding
                    if is_module:
                        raw_edges[target].called_names.add(func.attr)
        current.internal_dependencies = raw_edges
        for target, edge in raw_edges.items():
            if target in module_names:
                inbound[target][current.name] = edge
    return inbound


@dataclass(slots=True)
class PythonConsumer:
    path: Path
    tree: ast.Module
    dependencies: dict[str, ImportEdge]
    referenced_tests: dict[str, list[str]] = field(default_factory=dict)


def analyze_consumer(path: Path, modules: dict[str, ModuleInfo], packages: set[str]) -> PythonConsumer:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=path.relative_to(REPO_ROOT).as_posix())
    pseudo_name = path.relative_to(REPO_ROOT).as_posix()
    module_names = set(modules)
    edges: dict[str, ImportEdge] = {}
    bindings: dict[str, tuple[str, str | None, bool]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0:
            base = node.module or ""
            for alias in node.names:
                child = f"{base}.{alias.name}" if base else alias.name
                exact = child if child in module_names else None
                target = exact or best_internal_target(base, module_names, packages)
                if target in module_names:
                    imported_name = "module" if exact else alias.name
                    edge = edges.setdefault(target, ImportEdge(pseudo_name, target))
                    edge.imported_names.add(imported_name)
                    bindings[alias.asname or alias.name] = (
                        target,
                        None if exact else alias.name,
                        bool(exact),
                    )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                target = best_internal_target(alias.name, module_names, packages)
                if target in module_names:
                    edge = edges.setdefault(target, ImportEdge(pseudo_name, target))
                    edge.imported_names.add("module")
                    bindings[alias.asname or alias.name.split(".")[0]] = (target, None, True)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in bindings:
            target, imported_name, is_module = bindings[node.func.id]
            if not is_module and imported_name:
                edges[target].called_names.add(imported_name)
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            binding = bindings.get(node.func.value.id)
            if binding and binding[2]:
                edges[binding[0]].called_names.add(node.func.attr)
    referenced_tests: dict[str, set[str]] = defaultdict(set)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test_"):
            continue
        used_names = {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}
        used_attrs = {
            child.value.id
            for child in ast.walk(node)
            if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name)
        }
        for local, (target, _, _) in bindings.items():
            if local in used_names or local in used_attrs:
                referenced_tests[target].add(node.name)
    return PythonConsumer(
        path,
        tree,
        edges,
        {target: sorted(cases) for target, cases in referenced_tests.items()},
    )


def load_consumers(modules: dict[str, ModuleInfo], packages: set[str]) -> tuple[list[PythonConsumer], list[PythonConsumer]]:
    tests = [analyze_consumer(path, modules, packages) for path in sorted((REPO_ROOT / "tests").rglob("*.py"))]
    scripts = [analyze_consumer(path, modules, packages) for path in sorted((REPO_ROOT / "scripts").rglob("*.py"))]
    return tests, scripts


def role_key(name: str) -> str:
    if name.startswith("learnloop_sidecar"):
        return "sidecar"
    parts = name.split(".")
    return parts[1] if len(parts) > 1 else "root"


def conceptual_links(info: ModuleInfo) -> tuple[list[str], list[str]]:
    concepts, defaults = ROLE_LINKS.get(role_key(info.name), ROLE_LINKS["root"])
    return list(concepts), workflow_links_for(info, list(defaults))


def workflow_links_for(info: ModuleInfo, defaults: list[str]) -> list[str]:
    """Choose workflow links from module evidence instead of package alone.

    The exact overrides capture explicit shadow/dormant contracts.  The token
    rules then identify the user lifecycle named by a module.  Package defaults
    are a final fallback for genuinely broad coordinators/adapters.
    """

    if info.name in MODULE_WORKFLOW_OVERRIDES:
        return list(MODULE_WORKFLOW_OVERRIDES[info.name])
    if info.status == "DORMANT" or info.name.startswith("learnloop.sim"):
        return []

    stem = info.source.stem.casefold()
    role = role_key(info.name)

    if role == "reader":
        return ["Reader to Practice Workflow"]
    if role == "tutor":
        return ["Tutor and Teach-Back Workflow"]
    if role == "goals":
        return ["Goals Exams and Certification Workflow"]
    if role == "ai":
        return ["Configure AI Providers", "Process Model Output"]
    if role == "params":
        return ["Rebuild and Shadow Compare"]

    token_rules: tuple[tuple[tuple[str, ...], list[str]], ...] = (
        (("shadow_rebuild", "rebuild", "replay"), ["Rebuild and Shadow Compare"]),
        (("doctor", "migrat", "recovery", "upgrade", "debug_time", "vault_lock"), ["Doctor Migrations and Recovery"]),
        (("teach_back", "tutor", "hint"), ["Tutor and Teach-Back Workflow"]),
        (("reader", "annotation", "quick_check"), ["Reader to Practice Workflow"]),
        (("exam", "goal", "certif", "forecast"), ["Goals Exams and Certification Workflow"]),
        (("source", "ingest", "extract", "inventory", "synthes", "authoring", "proposal", "build_plan"), ["Import Canonical Sources", "Build a Study Map"]),
        (("attempt", "grad", "evidence", "observation", "feedback", "clarification", "reveal", "surprise"), ["Process Model Output", "Inspect Persistent State"]),
        (("schedul", "review", "session", "fsrs", "queue", "selector", "controller", "progression", "interleav"), ["Start a Learning Cycle", "Continue a Learning Cycle"]),
        (("config", "settings", "provider", "routing", "runtime"), ["Configure AI Providers"]),
        (("vault", "bootstrap", "init", "loader", "writer"), ["Initialize a Vault"]),
    )
    for tokens, workflows in token_rules:
        if any(token in stem for token in tokens):
            return workflows

    role_defaults: dict[str, list[str]] = {
        "attempts": ["Process Model Output", "Inspect Persistent State"],
        "learner": ["Inspect Persistent State", "Start a Learning Cycle"],
        "scheduling": ["Start a Learning Cycle", "Continue a Learning Cycle"],
        "diagnosis": ["Process Model Output", "Start a Learning Cycle"],
        "curriculum": ["Build a Study Map"],
        "substrate": ["Inspect Persistent State", "Rebuild and Shadow Compare"],
        "content": ["Import Canonical Sources", "Build a Study Map"],
        "ingest": ["Import Canonical Sources"],
        "db": ["Inspect Persistent State", "Doctor Migrations and Recovery"],
        "config": ["Initialize a Vault"],
        "vault": ["Initialize a Vault"],
        "ops": ["Doctor Migrations and Recovery"],
        "tui": ["Start a Learning Cycle", "Continue a Learning Cycle"],
    }
    return role_defaults.get(role, defaults)


def purpose_for(info: ModuleInfo) -> str:
    package = package_link(info.package)
    if info.docstring:
        contract = one_line(info.docstring)
        return (
            f"`{info.name}` exists within {package} to own the behavior summarized by its "
            f"module contract: {contract}"
        )
    public = [symbol.name for symbol in info.symbols if not symbol.name.startswith("_")]
    if info.source.name == "__init__.py":
        if info.all_exports:
            exposed = ", ".join(f"`{name}`" for name in info.all_exports[:12])
            suffix = "" if len(info.all_exports) <= 12 else f" and {len(info.all_exports) - 12} more"
            return (
                f"This module is the import boundary for {package}. It makes the package's supported "
                f"surface explicit, including {exposed}{suffix}."
            )
        return f"This module establishes the Python package boundary for {package}."
    if public:
        centers = ", ".join(f"`{name}`" for name in public[:8])
        suffix = "" if len(public) <= 8 else f" and {len(public) - 8} more public symbols"
        return (
            f"This module keeps {humanize(info.source.stem)} behavior inside its owning package, {package}. "
            f"Its public surface centers on {centers}{suffix}."
        )
    private = [symbol.name for symbol in info.symbols]
    if private:
        centers = ", ".join(f"`{name}`" for name in private[:8])
        return (
            f"This implementation module supports {package} through internal helpers such as {centers}; "
            "it does not advertise a standalone public API."
        )
    return f"This module is a source-level boundary within {package}; it currently exposes no top-level definitions."


def modification_guidance(info: ModuleInfo) -> list[str]:
    stem = info.source.stem
    role = role_key(info.name)
    guidance: list[str] = []
    if stem == "__init__":
        guidance.append("Change this file when intentionally adding or removing a package-level re-export; keep implementation logic in the owning module.")
    elif stem == "ai_contracts":
        guidance.append("Change feature context, prompt assembly, result models, and operation purposes here; keep provider mechanics in `learnloop.ai`.")
    elif role == "ai":
        guidance.append("Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.")
    elif info.name.startswith("learnloop.ai.providers"):
        guidance.append("Change provider protocol adaptation and capability reporting here; preserve the shared structured-completion contract.")
    elif role == "db" or ".db.stores" in info.name:
        guidance.append("Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.")
    elif role == "config":
        guidance.append("Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.")
    elif role in {"cli", "tui", "sidecar"}:
        guidance.append("Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.")
    elif role == "ingest":
        guidance.append("Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.")
    elif role in {"attempts", "learner", "scheduling", "goals", "diagnosis", "curriculum", "substrate", "content", "reader", "tutor"}:
        guidance.append(f"Change {humanize(stem)} policy here when {role} owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.")
    else:
        guidance.append(f"Make changes here when the responsibility remains {humanize(stem)} within {info.package}; otherwise move the behavior to its owning boundary.")
    if info.status == "COMPAT":
        guidance.append("This is frozen old-vault compatibility code: do not extend it without an explicit compatibility decision and fixture-backed tests.")
    elif info.status == "DORMANT":
        guidance.append("This module is explicitly dormant/disabled. Do not grant it live workflow authority without a product decision, activation evidence, and tests for the newly reachable path.")
    elif info.status == "EVALUATION":
        guidance.append("Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.")
    guidance.append("Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.")
    if info.all_exports:
        guidance.append("Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.")
    return guidance


def render_frontmatter(info: ModuleInfo) -> list[str]:
    rel = info.source.relative_to(REPO_ROOT).as_posix()
    package_tag = re.sub(r"[^a-z0-9/-]+", "-", info.package.lower().replace(".", "-"))
    tags = [
        "docs/module",
        "architecture/reference",
        f"refactor/{info.status.lower()}",
        f"layer/{info.layer}",
        f"package/{package_tag}",
    ]
    concepts, workflows = conceptual_links(info)
    lines = [
        "---",
        f"title: {yaml_string(info.name)}",
        'type: "module-reference"',
        'status: "current"',
        f"refactor_status: {yaml_string(info.status)}",
        f"version: {yaml_string(DOC_VERSION)}",
        f"source_path: {yaml_string(rel)}",
        "source_paths:",
        *yaml_list([rel], 2),
        f"source_commit: {yaml_string(info.commit)}",
        f"source_commit_timestamp: {yaml_string(info.commit_timestamp)}",
        f"source_worktree_state: {yaml_string(info.source_state)}",
        "generated: true",
        f"generated_at: {yaml_string(GENERATED_DATE)}",
        f"package: {yaml_string(info.package)}",
        f"layer: {yaml_string(info.layer)}",
        *(
            [f"operational_scope: {yaml_string(OPERATIONAL_SCOPE_NOTES[info.name])}"]
            if info.name in OPERATIONAL_SCOPE_NOTES
            else []
        ),
        "concepts:",
        *yaml_list(concepts, 2),
        "workflows:",
        *yaml_list(workflows, 2),
        "aliases:",
        *yaml_list([f"{info.name} module", rel], 2),
        "tags:",
        *yaml_list(tags, 2),
        "---",
    ]
    return lines


def relative_repo_link(note: Path, target: Path, label: str) -> str:
    relative = os.path.relpath(target, note.parent).replace(os.sep, "/")
    return f"[{label}]({relative})"


def render_symbol(symbol: Symbol, note: Path, source: Path, *, include_methods: bool = True) -> list[str]:
    source_link = relative_repo_link(note, source, "source")
    summary = f" — {symbol.summary}" if symbol.summary else ""
    lines = [f"- `{symbol.signature}` ({source_link}, line {symbol.line}){summary}"]
    if include_methods and symbol.methods:
        for method in symbol.methods:
            visibility = "public" if not method.name.startswith("_") else "internal"
            method_summary = f" — {method.summary}" if method.summary else ""
            lines.append(
                f"  - `{method.signature}` (line {method.line}; {visibility}){method_summary}"
            )
    return lines


def consumer_tests_for(
    info: ModuleInfo,
    inbound: dict[str, dict[str, ImportEdge]],
    tests: list[PythonConsumer],
) -> tuple[list[PythonConsumer], list[tuple[str, PythonConsumer]]]:
    direct = [consumer for consumer in tests if info.name in consumer.dependencies]
    indirect: list[tuple[str, PythonConsumer]] = []
    if not direct:
        seen: set[Path] = set()
        for importer in sorted(inbound.get(info.name, {})):
            for consumer in tests:
                if importer in consumer.dependencies and consumer.path not in seen:
                    indirect.append((importer, consumer))
                    seen.add(consumer.path)
                    if len(indirect) >= 12:
                        return direct, indirect
    return direct, indirect


def render_module_note(
    info: ModuleInfo,
    modules: dict[str, ModuleInfo],
    packages: set[str],
    inbound: dict[str, dict[str, ImportEdge]],
    tests: list[PythonConsumer],
    scripts: list[PythonConsumer],
) -> str:
    note = note_path_for_source(info.source)
    note.parent.mkdir(parents=True, exist_ok=True)
    concepts, workflows = conceptual_links(info)
    source_rel = info.source.relative_to(REPO_ROOT).as_posix()
    source_link = relative_repo_link(note, info.source, source_rel)
    lines = render_frontmatter(info)
    lines.extend(
        [
            "",
            f"# `{info.name}`",
            "",
            "> [!info] Generated source reference",
            "> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.",
            "",
            f"Up: {package_link(info.package)} · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].",
            "",
            "## Why this module exists",
            "",
            purpose_for(info),
            "",
            "The authoritative system-level explanation remains in "
            + ", ".join(f"[[{concept}]]" for concept in concepts)
            + "; this note records where this source module participates rather than restating those concepts.",
            "",
            "^module-purpose",
            "",
            "## Source facts",
            "",
            "| Fact | Value |",
            "|---|---|",
            f"| Source | {source_link} |",
            f"| Source lines | {info.loc} |",
            f"| Owning package | {package_link(info.package)} |",
            f"| Architecture layer | `{info.layer}` |",
            f"| Refactor status | `{info.status}` |",
            f"| Worktree state | `{info.source_state}` |",
            f"| Source commit | `{info.commit}` |",
            f"| Commit timestamp | `{info.commit_timestamp}` |",
        ]
    )
    if info.name in OPERATIONAL_SCOPE_NOTES:
        lines.extend(
            [
                f"| Operational scope | `{OPERATIONAL_SCOPE_NOTES[info.name]}` |",
                "",
                "> [!important] Active gate, inactive feature",
                "> This module is live because it reports/enforces the dependency gate. The open-world feature behind that gate is not implemented or serving learners.",
            ]
        )
    if info.status == "COMPAT":
        lines.extend(
            [
                "",
                "> [!warning] Frozen compatibility boundary",
                "> This live module is retained for old vaults. It is green but not a target for new feature growth.",
            ]
        )
    elif info.status == "DORMANT":
        lines.extend(
            [
                "",
                "> [!warning] Dormant or disabled boundary",
                "> The source explicitly withholds live workflow authority. Its code/tests remain inspectable, but activation is a separate product and evidence decision.",
            ]
        )
    elif info.status == "EVALUATION":
        lines.extend(
            [
                "",
                "> [!note] Evaluation-only authority",
                "> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.",
            ]
        )
    lines.extend(["", "## Public API", ""])
    public_symbols = [symbol for symbol in info.symbols if not symbol.name.startswith("_")]
    private_symbols = [symbol for symbol in info.symbols if symbol.name.startswith("_")]
    if public_symbols:
        for symbol in public_symbols:
            lines.extend(render_symbol(symbol, note, info.source))
    else:
        lines.append("No public top-level function or class definition is declared in this file.")
    if info.constants:
        lines.extend(["", "### Module constants", ""])
        for name, line in info.constants:
            lines.append(f"- `{name}` ({source_link}, line {line})")
    if info.all_exports:
        lines.extend(["", "### Explicit exports", "", "`__all__` declares:"])
        lines.append("")
        lines.extend(f"- `{name}`" for name in info.all_exports)
    lines.extend(["", "## Internal implementation anchors", ""])
    if private_symbols:
        for symbol in private_symbols:
            lines.extend(render_symbol(symbol, note, info.source, include_methods=False))
    else:
        lines.append("No private top-level function or class definition is declared in this file.")

    lines.extend(["", "## Who imports or calls it", ""])
    lines.extend(
        [
            "> [!note] Static evidence boundary",
            "> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.",
            "",
        ]
    )
    importers = inbound.get(info.name, {})
    if importers:
        for importer_name in sorted(importers):
            edge = importers[importer_name]
            details: list[str] = []
            if edge.imported_names:
                details.append("imports " + ", ".join(f"`{name}`" for name in sorted(edge.imported_names)))
            if edge.called_names:
                details.append("statically calls " + ", ".join(f"`{name}`" for name in sorted(edge.called_names)))
            lines.append(f"- {module_link(importer_name, modules)} — {'; '.join(details)}")
    else:
        lines.append("No live LearnLoop module directly imports this module in the static graph.")
    tool_consumers = [consumer for consumer in scripts if info.name in consumer.dependencies]
    if tool_consumers:
        lines.extend(["", "### Repository tooling consumers", ""])
        for consumer in tool_consumers:
            edge = consumer.dependencies[info.name]
            calls = f"; calls {', '.join(f'`{name}`' for name in sorted(edge.called_names))}" if edge.called_names else ""
            lines.append(f"- {relative_repo_link(note, consumer.path, consumer.path.relative_to(REPO_ROOT).as_posix())}{calls}")
    if info.name == "learnloop.cli":
        lines.extend(
            [
                "",
                "> [!tip] Runtime entry point",
                "> `pyproject.toml` registers `learnloop = learnloop.cli:app`; console invocation is therefore a non-AST consumer of this module.",
            ]
        )

    lines.extend(["", "## Dependencies", "", "### LearnLoop dependencies", ""])
    if info.internal_dependencies:
        for target in sorted(info.internal_dependencies):
            edge = info.internal_dependencies[target]
            if target in modules:
                link = module_link(target, modules)
            elif target in packages:
                link = package_link(target)
            else:
                link = f"`{target}`"
            calls = f"; calls {', '.join(f'`{name}`' for name in sorted(edge.called_names))}" if edge.called_names else ""
            imports = ", ".join(f"`{name}`" for name in sorted(edge.imported_names))
            lines.append(f"- {link} — imports {imports}{calls}")
    else:
        lines.append("No internal Python dependency was found by static analysis.")
    lines.extend(["", "### Platform and third-party dependencies", ""])
    if info.stdlib_dependencies:
        lines.append("- Standard library: " + ", ".join(f"`{name}`" for name in sorted(info.stdlib_dependencies)))
    else:
        lines.append("- Standard library: none imported directly")
    if info.external_dependencies:
        lines.append("- Third party: " + ", ".join(f"`{name}`" for name in sorted(info.external_dependencies)))
    else:
        lines.append("- Third party: none imported directly")

    lines.extend(["", "## Larger workflow participation", ""])
    if workflows:
        lines.append("Use this module in context through:")
        lines.append("")
        for workflow in workflows:
            lines.append(f"- [[{workflow}]]")
    else:
        lines.append(
            "No direct learner/operator workflow is assigned. This module is offline, "
            "shadow-only, dormant, or a dependency reached only through the static consumers below."
        )
    lines.append("")
    if importers:
        importer_links = [module_link(name, modules) for name in sorted(importers)[:5]]
        suffix = "" if len(importers) <= 5 else f" and {len(importers) - 5} more"
        lines.append(
            "Static participation evidence comes from "
            + ", ".join(importer_links)
            + suffix
            + "."
        )
    else:
        lines.append(
            "No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above."
        )
    lines.append("")
    lines.append(
        "The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface."
    )

    direct_tests, indirect_tests = consumer_tests_for(info, inbound, tests)
    lines.extend(["", "## Tests that define behavior", ""])
    if direct_tests:
        for consumer in direct_tests:
            test_link = relative_repo_link(note, consumer.path, consumer.path.relative_to(REPO_ROOT).as_posix())
            cases = consumer.referenced_tests.get(info.name, [])
            lines.append(f"- {test_link} — direct import")
            for case in cases:
                lines.append(f"  - `{case}`")
    elif indirect_tests:
        lines.append("No test imports this module directly. These tests exercise a direct production consumer:")
        lines.append("")
        for importer_name, consumer in indirect_tests:
            test_link = relative_repo_link(note, consumer.path, consumer.path.relative_to(REPO_ROOT).as_posix())
            lines.append(f"- {test_link} — imports consumer {module_link(importer_name, modules)}")
    else:
        lines.append("No direct or one-hop consumer test was found by static import analysis.")
        lines.append("")
        lines.append("> [!caution] Test gap signal\n> Treat this as a navigation signal, not proof that behavior is untested: dynamic and higher-level coverage is outside this static map. Add focused coverage when changing isolated behavior here.")

    lines.extend(["", "## Modification guidance", ""])
    for item in modification_guidance(info):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "### Regeneration and review checklist",
            "",
            f"1. Modify {source_link} and its owning tests.",
            "2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.",
            "3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.",
            "4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.",
            "",
        ]
    )
    return "\n".join(lines)


def package_for_module(info: ModuleInfo) -> str:
    return info.package


def package_neighbors(
    package: str,
    modules: dict[str, ModuleInfo],
) -> tuple[dict[str, int], dict[str, int]]:
    outgoing: dict[str, int] = defaultdict(int)
    incoming: dict[str, int] = defaultdict(int)
    for info in modules.values():
        source_package = package_for_module(info)
        for target in info.internal_dependencies:
            if target in modules:
                target_package = package_for_module(modules[target])
            else:
                target_package = target
            if source_package != target_package:
                if source_package == package:
                    outgoing[target_package] += 1
                if target_package == package:
                    incoming[source_package] += 1
    return dict(outgoing), dict(incoming)


def package_status(package: str) -> str:
    if package == "learnloop.substrate.compat":
        return "COMPAT"
    if package == "learnloop.sim":
        return "EVALUATION"
    return "ACTIVE"


def package_layer(package: str) -> str:
    if package == "learnloop":
        return "coordination"
    synthetic_name = package if package.count(".") > 1 else package + ".__package__"
    return classify_layer(synthetic_name)


def package_concepts(package: str) -> tuple[list[str], list[str]]:
    if package.startswith("learnloop_sidecar"):
        return ROLE_LINKS["sidecar"]
    parts = package.split(".")
    key = parts[1] if len(parts) > 1 else "root"
    return ROLE_LINKS.get(key, ROLE_LINKS["root"])


def render_mermaid(package: str, outgoing: dict[str, int], incoming: dict[str, int]) -> list[str]:
    neighbors = set(outgoing) | set(incoming)
    if len(neighbors) < 3:
        return []
    ranked = sorted(neighbors, key=lambda name: (-(outgoing.get(name, 0) + incoming.get(name, 0)), name))[:10]
    def node_id(name: str) -> str:
        return "n_" + re.sub(r"[^A-Za-z0-9]", "_", name)
    lines = [
        "",
        "### Dependency neighborhood",
        "",
        "This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.",
        "",
        "```mermaid",
        "flowchart LR",
        f'    center["{package}"]',
    ]
    for neighbor in ranked:
        lines.append(f'    {node_id(neighbor)}["{neighbor}"]')
    for neighbor in ranked:
        if incoming.get(neighbor):
            lines.append(f"    {node_id(neighbor)} -->|{incoming[neighbor]}| center")
        if outgoing.get(neighbor):
            lines.append(f"    center -->|{outgoing[neighbor]}| {node_id(neighbor)}")
    lines.append("```")
    lines.extend(
        [
            "",
            "Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.",
        ]
    )
    return lines


def render_package_moc(
    package: str,
    modules: dict[str, ModuleInfo],
    inbound: dict[str, dict[str, ImportEdge]],
    tests: list[PythonConsumer],
) -> str:
    note = moc_path(package)
    note.parent.mkdir(parents=True, exist_ok=True)
    members = sorted(
        [info for info in modules.values() if info.package == package], key=lambda info: info.name
    )
    descendants = sorted(
        (info for info in modules.values() if info.name.startswith(package + ".")),
        key=lambda info: info.name,
    )
    aggregate = members or descendants
    latest_timestamp = max((info.commit_timestamp for info in aggregate), default="unknown")
    source_paths = [info.source.relative_to(REPO_ROOT).as_posix() for info in members]
    if not source_paths:
        source_paths = ["src/" + package.replace(".", "/") + "/"]
    status = package_status(package)
    layer = package_layer(package)
    concepts, workflows = package_concepts(package)
    tags = [
        "docs/package-map",
        "architecture/reference",
        f"refactor/{status.lower()}",
        f"layer/{layer}",
        "package/" + package.replace(".", "-"),
    ]
    lines = [
        "---",
        f"title: {yaml_string(package + ' — Package Map')}",
        'type: "package-map"',
        'status: "current"',
        f"refactor_status: {yaml_string(status)}",
        f"version: {yaml_string(DOC_VERSION)}",
        "source_paths:",
        *yaml_list(source_paths, 2),
        'source_commit: "aggregate; see module notes"',
        f"source_commit_timestamp: {yaml_string(latest_timestamp)}",
        "generated: true",
        f"generated_at: {yaml_string(GENERATED_DATE)}",
        f"package: {yaml_string(package)}",
        f"layer: {yaml_string(layer)}",
        "concepts:",
        *yaml_list(concepts, 2),
        "workflows:",
        *yaml_list(workflows, 2),
        "tags:",
        *yaml_list(tags, 2),
        "---",
        "",
        f"# `{package}` package map",
        "",
        "> [!info] Generated package map",
        "> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.",
        "",
        "Up: [[Module Catalog]]",
        "",
        "## Responsibility",
        "",
        PACKAGE_DESCRIPTIONS.get(package, f"Source modules owned by the `{package}` package boundary."),
        "",
        "For system intent, use " + ", ".join(f"[[{name}]]" for name in concepts) + ".",
        "",
        "^package-purpose",
        "",
        "## Module index",
        "",
        "| Module | Purpose | Status | Direct importers | Direct test files |",
        "|---|---|---:|---:|---:|",
    ]
    if members:
        for info in members:
            target = note_path_for_source(info.source).relative_to(VAULT_ROOT).with_suffix("").as_posix()
            purpose_link = f"[[{target}#^module-purpose|purpose]]"
            direct_test_count = sum(1 for consumer in tests if info.name in consumer.dependencies)
            lines.append(
                f"| {module_link(info.name, modules)} | {purpose_link} | `{info.status}` | {len(inbound.get(info.name, {}))} | {direct_test_count} |"
            )
    else:
        lines.append(f"| _Namespace package; use child package maps below._ | — | `{status}` | — | — |")
    children = sorted(
        child
        for child in PACKAGE_DESCRIPTIONS
        if child.startswith(package + ".") and child.count(".") == package.count(".") + 1
    )
    if children:
        lines.extend(["", "## Child package maps", ""])
        lines.extend(f"- {package_link(child)} — {PACKAGE_DESCRIPTIONS.get(child, '')}" for child in children)
    outgoing, incoming = package_neighbors(package, modules)
    lines.extend(["", "## Cross-package dependencies", ""])
    if outgoing:
        lines.append("### This package imports")
        lines.append("")
        for target, count in sorted(outgoing.items(), key=lambda item: (-item[1], item[0])):
            target_link = package_link(target) if target in PACKAGE_DESCRIPTIONS else f"`{target}`"
            lines.append(f"- {target_link} — {count} static module edge{'s' if count != 1 else ''}")
    else:
        lines.append("- No cross-package imports were found.")
    if incoming:
        lines.extend(["", "### Packages that import this package", ""])
        for source, count in sorted(incoming.items(), key=lambda item: (-item[1], item[0])):
            source_link = package_link(source) if source in PACKAGE_DESCRIPTIONS else f"`{source}`"
            lines.append(f"- {source_link} — {count} static module edge{'s' if count != 1 else ''}")
    lines.extend(render_mermaid(package, outgoing, incoming))
    lines.extend(["", "## Workflow entry points", ""])
    if workflows:
        lines.extend(f"- [[{workflow}]]" for workflow in workflows)
    else:
        lines.append("- No direct user-facing workflow; this package is offline/evaluation support.")
    lines.extend(
        [
            "",
            "## Find and filter",
            "",
            "Use Obsidian's native search:",
            "",
            "```query",
            f'path:"Reference/Modules/{package.replace(".", "/")}" tag:#docs/module',
            "```",
            "",
            "To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.",
            "",
        ]
    )
    return "\n".join(lines)


def render_catalog(
    modules: dict[str, ModuleInfo], packages: set[str], tests: list[PythonConsumer]
) -> str:
    note = CATALOG_ROOT / "Module Catalog.md"
    latest_timestamp = max(info.commit_timestamp for info in modules.values())
    desktop_modules = desktop_source_count()
    status_counts: dict[str, int] = defaultdict(int)
    for info in modules.values():
        status_counts[info.status] += 1
    lines = [
        "---",
        'title: "Module Catalog"',
        'type: "map-of-content"',
        'status: "current"',
        'refactor_status: "ACTIVE"',
        f"version: {yaml_string(DOC_VERSION)}",
        "source_paths:",
        '  - "src/learnloop"',
        '  - "src/learnloop_sidecar"',
        '  - "apps/learnloop-tauri"',
        'source_commit: "aggregate; see module notes"',
        f"source_commit_timestamp: {yaml_string(latest_timestamp)}",
        "generated: true",
        f"generated_at: {yaml_string(GENERATED_DATE)}",
        "tags:",
        '  - "docs/moc"',
        '  - "docs/module-catalog"',
        '  - "architecture/reference"',
        "---",
        "",
        "# Module Catalog",
        "",
        "> [!abstract] Lookup contract",
        f"> This catalog maps all **{len(modules)} Python source modules** under `src/learnloop` and `src/learnloop_sidecar` to one generated reference note apiece—including explicit active, compatibility, dormant, and evaluation statuses—and links the **{desktop_modules} TypeScript/TSX/Rust modules** in [[Desktop Module Catalog]]. It also provides **{len(packages)} Python package maps**. Concepts belong in [[Architecture Overview]], [[Learning System]], [[AI Architecture]], [[State and Persistence]], and [[Configuration]]; workflows belong in their dedicated notes.",
        "",
        "## Coverage and status",
        "",
        "| Refactor status | Modules | Meaning |",
        "|---|---:|---|",
        f"| `ACTIVE` | {status_counts.get('ACTIVE', 0)} | Live ownership after the refactor. |",
        f"| `COMPAT` | {status_counts.get('COMPAT', 0)} | Live but frozen old-vault compatibility machinery. |",
        f"| `DORMANT` | {status_counts.get('DORMANT', 0)} | Explicitly disabled/descoped modules with no live workflow authority. |",
        f"| `EVALUATION` | {status_counts.get('EVALUATION', 0)} | Shadow, audit, or offline evaluation code whose outputs are decision-inert. |",
        "",
        "> [!note] Generated evidence",
        "> Importers and direct calls are static AST evidence. Dynamic RPC registration, entry points, reflection, and string-based dispatch are called out where known but cannot be proven exhaustively without runtime tracing.",
        "",
        "^catalog-coverage",
        "",
        "## Package maps",
        "",
        "| Package | Layer | Status | Direct modules | Responsibility |",
        "|---|---|---|---:|---|",
    ]
    for package in sorted(packages):
        member_count = sum(1 for info in modules.values() if info.package == package)
        lines.append(
            f"| {package_link(package)} | `{package_layer(package)}` | `{package_status(package)}` | {member_count} | {PACKAGE_DESCRIPTIONS.get(package, 'Source package boundary.')} |"
        )
    lines.extend(
        [
            "",
            "## Desktop client modules",
            "",
            f"The Tauri desktop application has **{desktop_modules} source modules** with one-to-one reference notes in [[Desktop Module Catalog]]. Read [[Desktop Architecture]] first for the React-to-Rust-to-sidecar boundary, then use that catalog for per-file callers, dependencies, tests, and modification guidance.",
            "",
            "> [!tip] Choose the catalog by source tree",
            "> Use this catalog for Python under `src/`; use [[Desktop Module Catalog]] for TypeScript, TSX, and Rust under `apps/learnloop-tauri/`. Both link back to the same concepts and end-to-end workflows.",
            "",
            "## Find a module",
            "",
            "Obsidian's native search operators work without plugins:",
            "",
            "- `path:` restricts search to this catalog.",
            "- `tag:` filters by refactor status, layer, or package.",
            "- `section:` searches a generated heading such as `Modification guidance`.",
            "- `file:` finds a module by source/module filename.",
            "- `line:` finds facts on one generated line.",
            "",
            "```query",
            'path:"Reference/Modules" tag:#docs/module',
            "```",
            "",
            "```query",
            'path:"Reference/Modules" tag:#refactor/compat',
            "```",
            "",
            "```query",
            'path:"Reference/Modules" section:("Modification guidance") "Schema changes"',
            "```",
            "",
            "> [!tip] Optional Dataview index",
            "> If the Dataview community plugin is enabled, the query below creates a sortable live table. The vault does not require the plugin.",
            "",
            "```dataview",
            "TABLE refactor_status AS Status, layer AS Layer, source_path AS Source, source_commit_timestamp AS Commit",
            'FROM "Reference/Modules"',
            'WHERE type = "module-reference"',
            "SORT file.name ASC",
            "```",
            "",
            "## How to read a module note",
            "",
            "1. Use [[#Package maps|the package map]] to locate the ownership boundary.",
            "2. Open the module's purpose block, then inspect its public API and internal anchors.",
            "3. Follow inbound importers to learn who depends on it and outbound dependencies to learn what it assumes.",
            "4. Use test anchors as behavior evidence and the change guide for safe extension points.",
            "5. Follow canonical concept/workflow links for system semantics rather than expecting them to be duplicated in reference notes.",
            "",
            "## Maintenance",
            "",
            "```bash",
            ".venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py",
            ".venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py",
            "```",
            "",
            f"The current generation discovered {len(tests)} Python test files. Each module note lists direct importing tests or, when absent, one-hop consumer tests.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    sources = source_files()
    packages = package_names(sources)
    missing_descriptions = packages - set(PACKAGE_DESCRIPTIONS)
    if missing_descriptions:
        raise SystemExit(f"Add package descriptions for: {sorted(missing_descriptions)}")
    modules = load_modules(sources)
    inbound = collect_imports(modules, packages)
    tests, scripts = load_consumers(modules, packages)
    for info in modules.values():
        note = note_path_for_source(info.source)
        note.write_text(
            render_module_note(info, modules, packages, inbound, tests, scripts),
            encoding="utf-8",
        )
    for package in sorted(packages):
        moc_path(package).write_text(
            render_package_moc(package, modules, inbound, tests), encoding="utf-8"
        )
    (CATALOG_ROOT / "Module Catalog.md").write_text(
        render_catalog(modules, packages, tests), encoding="utf-8"
    )
    print(
        f"Generated {len(modules)} module notes, {len(packages)} package maps, "
        f"and 1 catalog from {len(tests)} test files."
    )


if __name__ == "__main__":
    main()
