"""Executable architecture guardrails for deferred imports and dynamic links."""

from __future__ import annotations

import ast
import importlib
import pkgutil
import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LEARNLOOP_ROOT = REPOSITORY_ROOT / "src" / "learnloop"
SIDECAR_ROOT = REPOSITORY_ROOT / "src" / "learnloop_sidecar"
FUNCTION_LOCAL_DOMAIN_IMPORTS = (
    REPOSITORY_ROOT / "tests" / "architecture_function_local_domain_imports.txt"
)
DOMAIN_PACKAGES = frozenset(
    {
        "attempts",
        "learner",
        "scheduling",
        "goals",
        "diagnosis",
        "curriculum",
        "substrate",
        "content",
        "reader",
        "tutor",
        "ops",
        "params",
        "sim",
    }
)
SQL_WRITE_RE = re.compile(
    r"\b(?:INSERT\s+(?:OR\s+\w+\s+)?INTO|UPDATE|DELETE\s+FROM|REPLACE\s+INTO)\b",
    re.IGNORECASE,
)
REGISTERED_SQL_OWNERS = frozenset(
    {
        "src/learnloop/db/migrate.py",
        "src/learnloop/db/repositories.py",
        "src/learnloop/db/stores/ingest_queue.py",
        "src/learnloop/substrate/replay.py",
        "src/learnloop/scheduling/controller_ownership.py",
        "src/learnloop/scheduling/controller_store.py",
        "src/learnloop/scheduling/kinship_feature.py",
        "src/learnloop/scheduling/prequential.py",
        "src/learnloop/scheduling/shadow_components.py",
        "src/learnloop/diagnosis/probe_episodes.py",
        "src/learnloop/curriculum/concepts.py",
        "src/learnloop/curriculum/depth_edge_authoring.py",
        "src/learnloop/goals/goal_series_store.py",
        "src/learnloop/ops/debug_time_store.py",
        # Explicit owner-gated administrative escape hatch.  Its arbitrary SQL
        # console is not an application-domain write path.
        "src/learnloop_sidecar/handlers/sqlite_admin.py",
    }
)


def _import_targets(tree: ast.AST) -> list[tuple[int, str]]:
    targets: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            targets.append((node.lineno, node.module))
    return targets


def _boundary(module_name: str) -> str:
    parts = module_name.split(".")
    if parts[0] == "learnloop_sidecar":
        return "learnloop_sidecar"
    if parts[0] == "learnloop" and len(parts) > 1:
        return ".".join(parts[:2])
    return parts[0]


def _module_name(path: Path) -> str:
    """Return the import name for a Python file below ``learnloop``."""

    relative = path.relative_to(LEARNLOOP_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(("learnloop", *parts))


def _runtime_module_names() -> frozenset[str]:
    return frozenset(_module_name(path) for path in LEARNLOOP_ROOT.rglob("*.py"))


def _resolved_import_from_module(
    importer: str,
    imported: str | None,
    level: int,
    *,
    importer_is_package: bool,
) -> str:
    """Resolve an ``ImportFrom`` module without importing application code."""

    if level == 0:
        return imported or ""
    package = importer.split(".") if importer_is_package else importer.split(".")[:-1]
    keep = len(package) - (level - 1)
    base = package[: max(keep, 0)]
    if imported:
        base.extend(imported.split("."))
    return ".".join(base)


def _function_local_import_targets(
    source: str,
    importer: str,
    *,
    available_modules: frozenset[str],
    importer_is_package: bool = False,
) -> list[tuple[int, str]]:
    """Find imports nested in functions, resolving ``from package import module``.

    Imports made lazily by CLI/TUI/sidecar adapters are intentionally outside
    this helper's policy.  Its caller supplies domain modules only.
    """

    found: list[tuple[int, str]] = []

    class Visitor(ast.NodeVisitor):
        function_depth = 0

        def _visit_function(self, node: ast.AST) -> None:
            self.function_depth += 1
            self.generic_visit(node)
            self.function_depth -= 1

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
            self._visit_function(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
            self._visit_function(node)

        def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
            if self.function_depth:
                found.extend((node.lineno, alias.name) for alias in node.names)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
            if not self.function_depth:
                return
            module = _resolved_import_from_module(
                importer,
                node.module,
                node.level,
                importer_is_package=importer_is_package,
            )
            resolved_submodules = [
                f"{module}.{alias.name}"
                for alias in node.names
                if module and f"{module}.{alias.name}" in available_modules
            ]
            if resolved_submodules:
                found.extend((node.lineno, target) for target in resolved_submodules)
            elif module:
                found.append((node.lineno, module))

    Visitor().visit(ast.parse(source))
    return found


def _function_local_domain_edges(
    source: str,
    importer: str,
    *,
    available_modules: frozenset[str],
    importer_is_package: bool = False,
) -> list[tuple[int, str]]:
    source_boundary = _boundary(importer)
    edges: list[tuple[int, str]] = []
    for line, target in _function_local_import_targets(
        source,
        importer,
        available_modules=available_modules,
        importer_is_package=importer_is_package,
    ):
        target_parts = target.split(".")
        if (
            len(target_parts) < 2
            or target_parts[0] != "learnloop"
            or target_parts[1] not in DOMAIN_PACKAGES
            or _boundary(target) == source_boundary
        ):
            continue
        edges.append((line, f"{importer} -> {target}"))
    return edges


def _frozen_function_local_domain_edges() -> frozenset[str]:
    lines = FUNCTION_LOCAL_DOMAIN_IMPORTS.read_text(encoding="utf-8").splitlines()
    return frozenset(
        line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")
    )


def _current_function_local_domain_edges() -> tuple[frozenset[str], dict[str, list[str]]]:
    available_modules = _runtime_module_names()
    locations: dict[str, list[str]] = {}
    for package in sorted(DOMAIN_PACKAGES):
        root = LEARNLOOP_ROOT / package
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            importer = _module_name(path)
            for line, edge in _function_local_domain_edges(
                path.read_text(encoding="utf-8"),
                importer,
                available_modules=available_modules,
                importer_is_package=path.name == "__init__.py",
            ):
                locations.setdefault(edge, []).append(
                    f"{path.relative_to(REPOSITORY_ROOT)}:{line}"
                )
    return frozenset(locations), locations


def _private_cross_boundary_imports(source: str, importer: str) -> list[str]:
    tree = ast.parse(source)
    importer_boundary = _boundary(importer)
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module is None:
            continue
        if not node.module.startswith(("learnloop.", "learnloop_sidecar.")):
            continue
        if _boundary(node.module) == importer_boundary:
            continue
        for alias in node.names:
            if alias.name.startswith("_") and not alias.name.startswith("__"):
                violations.append(f"{node.lineno}: {node.module}.{alias.name}")
    return violations


def _sql_write_lines(source: str) -> list[int]:
    tree = ast.parse(source)
    writes: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"execute", "executemany", "executescript"} or not node.args:
            continue
        statement = node.args[0]
        sql_text: str | None = None
        if isinstance(statement, ast.Constant) and isinstance(statement.value, str):
            sql_text = statement.value
        elif isinstance(statement, ast.JoinedStr):
            # Dynamic identifiers still leave the SQL verb in literal f-string
            # fragments; ignoring JoinedStr made the ownership guard falsely
            # green for UPDATE/INSERT/DELETE calls.
            sql_text = "".join(
                value.value
                for value in statement.values
                if isinstance(value, ast.Constant) and isinstance(value.value, str)
            )
        if sql_text is not None and SQL_WRITE_RE.search(sql_text):
            writes.append(node.lineno)
    return writes


def test_legacy_codex_namespace_is_not_referenced() -> None:
    """Provider-neutral AI contracts must not regress to the deleted namespace."""

    forbidden = ".".join(("learnloop", "codex"))
    retired_services = ".".join(("learnloop", "services"))
    violations: list[str] = []
    for relative_root in ("src", "tests"):
        for path in sorted((REPOSITORY_ROOT / relative_root).rglob("*.py")):
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if forbidden in line or retired_services in line:
                    violations.append(
                        f"{path.relative_to(REPOSITORY_ROOT)}:{line_number}: {line.strip()}"
                    )
    assert not violations, "\n".join(violations)


def test_infrastructure_never_imports_domain_packages() -> None:
    """Persistence and AI may share infrastructure, but never import policy."""

    violations: list[str] = []
    for infrastructure in (
        LEARNLOOP_ROOT / "config",
        LEARNLOOP_ROOT / "vault",
        LEARNLOOP_ROOT / "db",
        LEARNLOOP_ROOT / "ingest",
        LEARNLOOP_ROOT / "ai",
    ):
        for path in sorted(infrastructure.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for line, target in _import_targets(tree):
                parts = target.split(".")
                if len(parts) > 1 and parts[0] == "learnloop" and parts[1] in DOMAIN_PACKAGES:
                    violations.append(
                        f"{path.relative_to(REPOSITORY_ROOT)}:{line}: {target}"
                    )
    assert not violations, "\n".join(violations)


def test_infrastructure_boundary_detector_rejects_a_synthetic_domain_edge() -> None:
    tree = ast.parse("from learnloop.learner import mastery\n")
    domain_targets = [
        target
        for _line, target in _import_targets(tree)
        if len(target.split(".")) > 1
        and target.split(".")[0] == "learnloop"
        and target.split(".")[1] in DOMAIN_PACKAGES
    ]
    assert domain_targets == ["learnloop.learner"]


def test_function_local_domain_import_detector_rejects_a_synthetic_new_edge() -> None:
    edge = "learnloop.scheduling.synthetic -> learnloop.learner.mastery"
    detected = _function_local_domain_edges(
        "def choose():\n    from learnloop.learner import mastery\n",
        "learnloop.scheduling.synthetic",
        available_modules=_runtime_module_names(),
    )

    assert detected == [(2, edge)]
    assert edge not in _frozen_function_local_domain_edges()


def test_function_local_domain_imports_match_the_frozen_edge_inventory() -> None:
    """Deferred domain-local imports may disappear, but no new edge may appear.

    The inventory is the surviving intersection of current edges and function-
    local ``services`` edges in pre-refactor HEAD, mechanically mapped to the
    modules' new domain homes. Adapter lazy imports were not part of that
    baseline. Stale entries fail too, making a removed edge shrink the ratchet.
    """

    frozen = _frozen_function_local_domain_edges()
    current, locations = _current_function_local_domain_edges()
    unregistered = sorted(current - frozen)
    stale = sorted(frozen - current)
    details: list[str] = []
    if unregistered:
        details.append("new function-local cross-domain edges:")
        details.extend(
            f"  {edge} ({', '.join(locations[edge])})" for edge in unregistered
        )
    if stale:
        details.append("stale frozen edges (remove them; the ratchet shrank):")
        details.extend(f"  {edge}" for edge in stale)

    assert not details, "\n".join(details)


def test_private_cross_package_import_detector_rejects_synthetic_edge() -> None:
    violations = _private_cross_boundary_imports(
        "from learnloop.learner.mastery import _internal\n",
        "learnloop.scheduling.scheduler",
    )
    assert violations == ["1: learnloop.learner.mastery._internal"]


def test_runtime_packages_import_only_public_cross_boundary_names() -> None:
    violations: list[str] = []
    for root, prefix in ((LEARNLOOP_ROOT, "learnloop"), (SIDECAR_ROOT, "learnloop_sidecar")):
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(root).with_suffix("")
            importer = ".".join((prefix, *relative.parts))
            for detail in _private_cross_boundary_imports(
                path.read_text(encoding="utf-8"), importer
            ):
                violations.append(f"{path.relative_to(REPOSITORY_ROOT)}:{detail}")
    assert not violations, "\n".join(violations)


def test_sql_write_location_detector_rejects_synthetic_owner() -> None:
    source = 'connection.execute("INSERT INTO new_table(id) VALUES (?)", (1,))\n'
    assert _sql_write_lines(source) == [1]


def test_sql_write_location_detector_rejects_f_string_owner() -> None:
    source = 'connection.execute(f"DELETE FROM {table} WHERE id = ?", (1,))\n'
    assert _sql_write_lines(source) == [1]


def test_sql_writes_stay_in_registered_owner_modules() -> None:
    violations: list[str] = []
    for root in (LEARNLOOP_ROOT, SIDECAR_ROOT):
        for path in sorted(root.rglob("*.py")):
            relative = str(path.relative_to(REPOSITORY_ROOT))
            lines = _sql_write_lines(path.read_text(encoding="utf-8"))
            if lines and relative not in REGISTERED_SQL_OWNERS:
                violations.append(f"{relative}: {lines}")
    assert not violations, "\n".join(violations)


def test_assessment_service_reexports_neutral_algorithm_versions() -> None:
    from learnloop import algorithm_versions
    from learnloop.learner import assessment_contracts

    for name in (
        "KM_ALGORITHM_VERSION",
        "P0_ALGORITHM_VERSION",
        "REVEAL_LEDGER_ALGORITHM_VERSION",
        "P0_SUCCESSOR_VERSIONS",
        "P0_PROJECTION_VERSIONS",
        "CANONICAL_STATE_VERSIONS",
    ):
        assert getattr(assessment_contracts, name) is getattr(
            algorithm_versions,
            name,
        )


def test_every_runtime_module_imports() -> None:
    modules: set[str] = set()
    for package_name in ("learnloop", "learnloop_sidecar"):
        package = importlib.import_module(package_name)
        modules.update(
            entry.name
            for entry in pkgutil.walk_packages(
                package.__path__, package.__name__ + "."
            )
            if not entry.name.endswith(".__main__")
        )

    failures: list[str] = []
    for module_name in sorted(modules):
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - failure detail only
            failures.append(f"{module_name}: {type(exc).__name__}: {exc}")
    assert not failures, "\n".join(failures)


def test_runtime_constructed_module_references_resolve() -> None:
    """Pin links whose import paths are data, so ordinary import tools miss them."""

    from learnloop.params import parameter_registry
    from learnloop.diagnosis import scoreboard

    dynamic_attributes = {
        "learnloop.diagnosis.robust_composition": (
            "build_ensemble",
            "robust_quantile",
            "evaluate_selection",
        ),
        "learnloop.attempts.effective_observation": (
            "build_effective_observation",
            "shared_certainty_lcb",
        ),
        "learnloop.learner.familiarity": (
            "familiarity_projection_v1",
            "HARD_NAMESPACES",
            "record_memberships",
        ),
        "learnloop.substrate.administration_adapters": ("__name__",),
        "learnloop.curriculum.golden_path_assessment": ("__name__",),
        "learnloop.curriculum.pattern_ladder": ("__name__",),
        "learnloop.reader.annotations": ("__name__",),
        "learnloop.attempts.salience_firewall": ("__name__",),
        "learnloop.scheduling.constraint_engine": ("evaluate", "manifest"),
        "learnloop.scheduling.staged_policy": ("decide",),
        "learnloop.scheduling.predictive_targets": ("__name__",),
        "learnloop.scheduling.dispersion": ("__name__",),
        "learnloop.scheduling.interleaving": ("__name__",),
    }
    for module_name, attributes in dynamic_attributes.items():
        resolved = importlib.import_module(module_name)
        assert all(hasattr(resolved, name) for name in attributes), module_name

    producer_module, producer_name = scoreboard._FALSE_CERTIFICATION_PRODUCER
    assert callable(getattr(importlib.import_module(producer_module), producer_name))

    # The parameter registry constructs module paths from its inventory. Resolve
    # every registered constant, not merely the modules sampled above.
    parameter_registry._MODULE_ATTR_CACHE.clear()
    for spec in parameter_registry.REGISTRY.values():
        if spec.source_of_value != "module_constant":
            continue
        parameter_registry._resolve_module_constant(spec.path)
