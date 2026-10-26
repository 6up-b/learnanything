"""Executable architecture guardrails for deferred imports and dynamic links."""

from __future__ import annotations

import ast
import importlib
import pkgutil
import re
from pathlib import Path
from tests.ast_cache import source_ast, source_text, python_files


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
        "projects",
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
        "src/learnloop/db/stores/completion.py",
        "src/learnloop/db/stores/model_calls.py",
        "src/learnloop/db/stores/collection.py",
        "src/learnloop/db/stores/embedding_vectors.py",
        # Local contextual retrieval P1a (migration 220): the embedding space
        # registry, the append-only retrieval feedback and the DERIVED fusion
        # posterior (replaced whole by its replayer and the refit).
        "src/learnloop/db/stores/retrieval_spaces.py",
        # The local space's per-vault vector cache (a derived file outside
        # state.sqlite, written only by the index job).
        "src/learnloop/local_embeddings/cache.py",
        # Local retrieval P2: the query student's teacher-replay queue, a derived per-vault file
        # outside state.sqlite (<vault>/.learnloop/student-replay.sqlite: learner text stays local).
        "src/learnloop/source_retrieval/student_encoder.py",
        "src/learnloop/db/stores/judgments.py",
        # Exam protection by extraction identity (Codex review F3): exam-qualified
        # copies appended to the held-out signal ledger, never an update.
        "src/learnloop/db/stores/held_out_signals.py",
        # Research experiment E0 (Codex review F1): the redaction of a SERVICE
        # copy's protected block text before any production path reads it; the
        # function refuses any database outside fixtures-local, and the frozen
        # corpus copies are only ever opened read-only.
        "src/learnloop/experiments/contextual_embeddings/system_arms.py",
        # Facet identity: applied merge/absorb actions and their facet_merges rows.
        "src/learnloop/db/stores/facet_identity.py",
        "src/learnloop/projects/experiment_store.py",
        # Slice 1 M1: review_* tables that exist only inside a scratch copy.
        "src/learnloop/db/stores/diagnosis_review.py",
        "src/learnloop/db/stores/field.py",
        "src/learnloop/db/stores/families.py",
        "src/learnloop/db/stores/practice_index.py",
        # Canonical sources (spec_source_practice_and_probes_v1): impressions,
        # imports, key checks, comparisons, tool calls and interventions.
        "src/learnloop/db/stores/source_service.py",
        # Slice 1 M2: blind grades, diagnoses, card taps and the job queue.
        "src/learnloop/db/stores/diagnoses.py",
        # Shared capture domain owns only the M1 mobile/inbox workflow tables.
        "src/learnloop/capture/devices.py",
        "src/learnloop/capture/inbox.py",
        "src/learnloop/capture/maintenance.py",
        "src/learnloop/capture/routing.py",
        # Learner field F2 placement receipts and quick-check queue state.
        "src/learnloop/db/stores/placement.py",
        # Reader workbench RW2d: what the predecessor's derivation and rule
        # would have decided where the workbench signals changed a placement.
        "src/learnloop/db/stores/field_signal_receipts.py",
        # Slice A Phase 5a (PF-b): candidates, skeletons and DERIVED fingerprints.
        "src/learnloop/db/stores/pf.py",
        # Slice 2 T1: the recurrence-group projection and escalation receipts.
        "src/learnloop/db/stores/recurrence.py",
        # Slice 2 T1: leases of the shared judge's in-flight questions.
        "src/learnloop/db/stores/judgment_claims.py",
        # Slice 2 T6: the DERIVED source_block_fts rebuild (its replayer body).
        "src/learnloop/db/stores/source_block_fts.py",
        # Daily-loop DL1: the finite plan's workflow rows and block receipts.
        "src/learnloop/db/stores/daily_plans.py",
        # Diagnosis input provenance (migration 205): append-only write-time
        # records of model-written text and the regrade error-event lineage.
        "src/learnloop/db/stores/write_provenance.py",
        # Router R1: append-only decision rows and the DERIVED outcome cache;
        # R2a: the decision payloads (the stored learner-state card).
        "src/learnloop/db/stores/router.py",
        # Router R2a: the append-only plan presentations (the exact
        # decision -> presentation -> attempt receipt).
        "src/learnloop/db/stores/plan_presentations.py",
        # Learner-text gaps: the gap ledger, reversals, queue and receipts.
        "src/learnloop/db/stores/learner_gaps.py",
        # EVSI calibration Part B: the append-only voi_forecasts receipts.
        "src/learnloop/db/stores/voi_forecasts.py",
        # Saved diagnosis forecasts: the append-only forecast_receipts family.
        "src/learnloop/db/stores/forecast_receipts.py",
        # Adaptive difficulty AD1 (migration 213): the append-only
        # item_serve_inputs and ad_reading_opportunities receipts, the
        # item_forecast_payloads workflow rows, and the served revision's
        # practice_item_snapshots row.
        "src/learnloop/db/stores/ad_receipts.py",
        # Adaptive difficulty AD2+AD3 (migration 214): the append-only
        # ad_selections, ad_commission_results, ad_dose_offers,
        # ad_relatedness_runs and ad_coupling_versions, and the DERIVED
        # ad_state, ad_attempt_trace and item_forecast_scores.
        "src/learnloop/db/stores/ad_serving.py",
        # Reader workbench RW2a: workbench_sessions (lifecycle) and the
        # append-only workbench_steps (migration 207).
        "src/learnloop/db/stores/workbench.py",
        # Adaptive hints H0: help_assists (migration 210), the authored-hint
        # reveal rows and their attach to the attempt at submit.
        "src/learnloop/db/stores/help_assists.py",
        # Adaptive hints H1: approach_maps (migration 211), one immutable row
        # per map version (the builder in learnloop.hints.map_builder).
        "src/learnloop/db/stores/approach_maps.py",
        # Reader workbench RW3b: passage_links and reader_cue_impressions
        # (migration 215), the cue judge's links and the cue receipts.
        "src/learnloop/db/stores/reader_cue_links.py",
        # Reader workbench RW7a: reader_path_sections and reader_path_depths
        # (migration 217), the path judge's labels and the learner's choices.
        "src/learnloop/db/stores/reading_paths.py",
        # Deliverable curriculum C0a: section_coverage (migration 222), the
        # coverage judge's rows and the learner's corrections (append-only).
        "src/learnloop/db/stores/section_coverage.py",
        # Reader workbench RW4a: library_asks (migration 209), one row per
        # library question with its manifests and organizer lines.
        "src/learnloop/db/stores/library_asks.py",
        # Reader workbench RW5a: interactive_figures (migration 216, built
        # figure versions) and the append-only figure_predictions (its one
        # update sets explanation_text once, enforced by trigger).
        "src/learnloop/db/stores/figures.py",
        # mvp-0.21 value-of-information stopping: the follow-up value
        # decisions' append-only receipts (one row per decision).
        "src/learnloop/db/stores/followup_value.py",
        "src/learnloop/substrate/replay.py",
        # Sole derived shadow-family FSRS writer; never a serving cache.
        "src/learnloop/substrate/family_memory.py",
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
    return frozenset(_module_name(path) for path in python_files(LEARNLOOP_ROOT))


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

    Visitor().visit(source_ast(source))
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
        for path in python_files(root):
            importer = _module_name(path)
            for line, edge in _function_local_domain_edges(
                source_text(path),
                importer,
                available_modules=available_modules,
                importer_is_package=path.name == "__init__.py",
            ):
                locations.setdefault(edge, []).append(
                    f"{path.relative_to(REPOSITORY_ROOT)}:{line}"
                )
    return frozenset(locations), locations


def _private_cross_boundary_imports(source: str, importer: str) -> list[str]:
    tree = source_ast(source)
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
    tree = source_ast(source)
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
            # Dynamic identifiers still leave the SQL verb in the literal
            # f-string fragments, so scanning them catches UPDATE/INSERT/DELETE
            # calls that interpolate a table name.
            sql_text = "".join(
                value.value
                for value in statement.values
                if isinstance(value, ast.Constant) and isinstance(value.value, str)
            )
        if sql_text is not None and SQL_WRITE_RE.search(sql_text):
            writes.append(node.lineno)
    return writes


def test_legacy_codex_namespace_is_not_referenced() -> None:
    """No source or test may reference a codex or services package under learnloop; neither exists."""

    forbidden = ".".join(("learnloop", "codex"))
    retired_services = ".".join(("learnloop", "services"))
    violations: list[str] = []
    for relative_root in ("src", "tests"):
        for path in python_files(REPOSITORY_ROOT / relative_root):
            for line_number, line in enumerate(
                source_text(path).splitlines(), start=1
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
        for path in python_files(infrastructure):
            tree = source_ast(source_text(path))
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
        for path in python_files(root):
            relative = path.relative_to(root).with_suffix("")
            importer = ".".join((prefix, *relative.parts))
            for detail in _private_cross_boundary_imports(
                source_text(path), importer
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
        for path in python_files(root):
            relative = str(path.relative_to(REPOSITORY_ROOT))
            lines = _sql_write_lines(source_text(path))
            if lines and relative not in REGISTERED_SQL_OWNERS:
                violations.append(f"{relative}: {lines}")
    assert not violations, "\n".join(violations)


def test_every_registered_sql_owner_still_writes() -> None:
    """A registered module without writes would let a future write pass unreviewed."""

    idle_owners = sorted(
        relative
        for relative in REGISTERED_SQL_OWNERS
        if not _sql_write_lines(source_text(REPOSITORY_ROOT / relative))
    )
    assert not idle_owners, idle_owners


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


# -- RW2b fix rounds 11-12: one accessor for stored symbolic results ------------------------------

#: The raw stored symbolic fields: a check's verdict records, the placement's
#: ``symbolic`` outcomes, a hint's ``claims``, a decided method, the record
#: decoder. A READ is a load (a dict key or an assignment target writes).
_SYMBOLIC_CONSTANTS = {"step_verdicts_json": "step_verdicts_json", "checked_numerically": "checked_numerically"}
_SYMBOLIC_KEYS = {"symbolic": "symbolic_key", "claims": "claims_key"}
#: Exemptions by FUNCTION (fix round 12): (module, qualified function) ->
#: tokens; "<module>" is module level, "*" a whole module. The accessor, the
#: writer operations (they decide and store the methods), and modules whose
#: "claims" belong to another domain.
_SYMBOLIC_FIELD_ALLOWED: dict[tuple[str, str], set[str]] = {
    ("src/learnloop/symbolic_view.py", "*"): set(_SYMBOLIC_CONSTANTS.values()) | set(_SYMBOLIC_KEYS.values())
    | {"verdict_from_record"},
    ("src/learnloop/workbench/symbolic.py", "<module>"): {"checked_numerically"},  # CHECKED_NUMERICALLY
    ("src/learnloop/workbench/check.py", "<module>"): {"checked_numerically"},  # MARKS, METHOD_LABELS
    ("src/learnloop/workbench/check.py", "check_view"): {"verdict_from_record"},  # decodes verdict_records()
    ("src/learnloop/workbench/ladder.py", "_verdicts"): {"verdict_from_record"},  # decodes verdict_records()
    ("src/learnloop/hints/workbench.py", "verify_claims"): {"checked_numerically"},  # decides a claim's status
    ("src/learnloop/db/stores/help_assists.py", "<module>"): {"step_verdicts_json"},  # the store's COLUMNS
    # Another domain's "claims" (source inventories, EVSI comparisons, the offline judge):
    ("src/learnloop/cli/evsi.py", "*"): {"claims_key"},
    ("src/learnloop/evsi_calibration/compare.py", "*"): {"claims_key"},
    ("src/learnloop/diagnosis/offline_review/judge.py", "*"): {"claims_key"},
    ("src/learnloop/content/synthesis/source_set_synthesis.py", "*"): {"claims_key"},
    ("src/learnloop/content/synthesis/vault_epigraphs.py", "*"): {"claims_key"},
    ("src/learnloop/content/synthesis/append_neighborhood.py", "*"): {"claims_key"},
    ("src/learnloop/content/synthesis/graph_nomination.py", "*"): {"claims_key"},
    ("src/learnloop/content/synthesis/source_coverage.py", "*"): {"claims_key"},
    ("src/learnloop/content/synthesis/source_unit_inventory.py", "*"): {"claims_key"},
    ("src/learnloop/db/repositories.py", "*"): {"claims_key"},
}
#: The readers, each CALLING the accessor (checked by AST).
_SYMBOLIC_READERS = (
    "src/learnloop/workbench/check.py",
    "src/learnloop/workbench/ladder.py",
    "src/learnloop/hints/report_workbench.py",
    "src/learnloop/diagnosis/split/workbench_trace.py",
    "src/learnloop/diagnosis/split/live.py",
    "src/learnloop_sidecar/handlers/workbench_help.py",
    "src/learnloop/hints/workbench.py",
    # Reader RW2c's help outcomes read which steps a check found valid only
    # through the hint service's per-help outcome (review F4:
    # hints.report_workbench.workbench_unaided_progress, listed above).
)


def _symbolic_field_uses(source: str) -> list[tuple[str, str]]:
    """``(qualified function, token)`` for every raw read in ``source``."""

    tree = ast.parse(source)
    dict_keys = {id(key) for node in ast.walk(tree) if isinstance(node, ast.Dict) for key in node.keys if key}
    out: list[tuple[str, str]] = []

    def visit(node: ast.AST, scope: str) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            scope = node.name if scope == "<module>" else f"{scope}.{node.name}"
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in dict_keys \
                and node.value in _SYMBOLIC_CONSTANTS:
            out.append((scope, _SYMBOLIC_CONSTANTS[node.value]))
        elif isinstance(node, ast.Name) and node.id == "verdict_from_record":
            out.append((scope, "verdict_from_record"))
        elif isinstance(node, ast.Attribute) and node.attr == "verdict_from_record":
            out.append((scope, "verdict_from_record"))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" \
                and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value in _SYMBOLIC_KEYS:
            out.append((scope, _SYMBOLIC_KEYS[node.args[0].value]))
        elif isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load) \
                and isinstance(node.slice, ast.Constant) and node.slice.value in _SYMBOLIC_KEYS:
            out.append((scope, _SYMBOLIC_KEYS[node.slice.value]))
        for child in ast.iter_child_nodes(node):
            visit(child, scope)

    visit(tree, "<module>")
    return out


def _symbolic_field_violations(files: dict[str, str]) -> list[str]:
    out = []
    for relative, text in files.items():
        for scope, token in _symbolic_field_uses(text):
            top = scope.split(".", 1)[0] if scope != "<module>" else scope
            allowed = (_SYMBOLIC_FIELD_ALLOWED.get((relative, "*"), set())
                       | _SYMBOLIC_FIELD_ALLOWED.get((relative, scope), set())
                       | _SYMBOLIC_FIELD_ALLOWED.get((relative, top), set()))
            if token not in allowed:
                out.append(f"{relative}:{scope}: {token}")
    return sorted(set(out))


def _calls_the_accessor(source: str) -> bool:
    """Whether ``source`` imports from ``learnloop.symbolic_view`` and CALLS
    one of the names it imports (by AST, not a substring)."""

    tree = ast.parse(source)
    names = {alias.asname or alias.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
             and node.module == "learnloop.symbolic_view" for alias in node.names}
    return any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in names
               for node in ast.walk(tree))


def test_symbolic_field_detector_rejects_a_synthetic_reader() -> None:
    assert _symbolic_field_violations({"src/learnloop/new_reader.py": 'def f(row):\n    return row.get("step_verdicts_json")\n'}) == [
        "src/learnloop/new_reader.py:f: step_verdicts_json"]
    # The verify's case (round 12): a raw read added to a writer module, outside its writer operations.
    workbench = (REPOSITORY_ROOT / "src/learnloop/hints/workbench.py").read_text(encoding="utf-8")
    injected = workbench + '\n\ndef sneaky(row):\n    return row.get("step_verdicts_json")\n'
    assert _symbolic_field_violations({"src/learnloop/hints/workbench.py": injected}) == [
        "src/learnloop/hints/workbench.py:sneaky: step_verdicts_json"]
    # Writing a stored field (a dict key, an assignment target) is not a read.
    assert _symbolic_field_violations({"src/learnloop/w.py": 'def w(p):\n    p["claims"] = []\n'
                                                             '    return {"step_verdicts_json": "[]"}\n'}) == []
    # A reader must CALL the accessor; naming it is not enough.
    assert not _calls_the_accessor('# learnloop.symbolic_view\nimport json\n')
    assert _calls_the_accessor('from learnloop.symbolic_view import switch\nswitch(None)\n')


def test_stored_symbolic_results_are_read_only_through_the_one_accessor() -> None:
    files = {}
    for path in sorted((REPOSITORY_ROOT / "src").rglob("*.py")):
        files[path.relative_to(REPOSITORY_ROOT).as_posix()] = path.read_text(encoding="utf-8")
    assert _symbolic_field_violations(files) == []
    for relative in _SYMBOLIC_READERS:
        assert _calls_the_accessor(files[relative]), relative


#: The TypeScript side (fix round 12): only helpModel's verdictMark and
#: claimLine render a symbolic mark; nobody else reads a verdict's mark or
#: writes "✓"/"≠" on the workbench, and the unused CheckMarker stays unused.
_TS_ROOT = REPOSITORY_ROOT / "apps" / "learnloop-tauri" / "src"


def _ts_function_body(source: str, name: str) -> str:
    start = source.index(f"export function {name}(")
    end = source.index("\n}\n", start)
    return source[start:end]


def _ts_symbolic_mark_violations(files: dict[str, str]) -> list[str]:
    out = []
    for relative, text in files.items():
        allowed = ""
        if relative.endswith("screens/workbench/helpModel.ts"):
            allowed = _ts_function_body(text, "verdictMark") + _ts_function_body(text, "claimLine")
        for number, line in enumerate(text.splitlines(), 1):
            code = line.strip()
            if code.startswith(("//", "*", "/*")):
                continue
            if "workbench" in relative and ("✓" in code or "≠" in code) and code not in allowed:
                out.append(f"{relative}:{number}: a symbolic mark outside verdictMark/claimLine")
            if re.search(r"\bverdict\.mark\b", code) and code not in allowed:
                out.append(f"{relative}:{number}: verdict.mark read outside verdictMark")
            if re.search(r"import\s*\{[^}]*\bCheckMarker\b", code):
                out.append(f"{relative}:{number}: CheckMarker imported")
    return out


def test_only_verdict_mark_and_claim_line_render_symbolic_marks() -> None:
    files = {path.relative_to(_TS_ROOT).as_posix(): path.read_text(encoding="utf-8")
             for path in sorted(_TS_ROOT.rglob("*.ts*")) if ".test." not in path.name}
    assert _ts_symbolic_mark_violations(files) == []
    assert _ts_symbolic_mark_violations({"screens/workbench/Rogue.tsx": "const x = `${verdict.mark} ok`;"}) == [
        "screens/workbench/Rogue.tsx:1: verdict.mark read outside verdictMark"]


def _raw_verdict_reads(source: str) -> list[str]:
    """Scopes that read ``._raw_verdicts`` outside ``WorkbenchHintContext``
    (RW2b fix round 15: only the context's own ``current()`` reads them)."""

    out: list[str] = []

    def visit(node: ast.AST, scope: str) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            scope = node.name if scope == "<module>" else f"{scope}.{node.name}"
        if isinstance(node, ast.Attribute) and node.attr == "_raw_verdicts" \
                and not scope.startswith("WorkbenchHintContext"):
            out.append(scope)
        for child in ast.iter_child_nodes(node):
            visit(child, scope)

    visit(ast.parse(source), "<module>")
    return out


def test_only_the_hint_context_reads_its_raw_verdicts() -> None:
    assert _raw_verdict_reads("def f(context):\n    return context._raw_verdicts\n") == ["f"]
    found = {}
    for path in sorted((REPOSITORY_ROOT / "src").rglob("*.py")):
        reads = _raw_verdict_reads(path.read_text(encoding="utf-8"))
        if reads:
            found[path.relative_to(REPOSITORY_ROOT).as_posix()] = reads
    assert found == {}
