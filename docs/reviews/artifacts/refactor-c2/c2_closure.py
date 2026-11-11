"""C2 closure: are the registry-tied candidates reached by anything but the registry?

Same graph as refactor-c1's c1_closure.py: AST import edges over src/ (module-level and
function-local imports, TYPE_CHECKING blocks included), plus a string edge for every
string constant naming a module (dotted, short, or as the `src/learnloop/...py` path
MODULE_INVENTORY uses). C2's question is narrower than C1's: MODULE_INVENTORY and
open_world_gate name the candidates by string, so the full graph reaches them by
construction. The pruned graph drops (a) every string edge from
`params.parameter_registry` and `scheduling.open_world_gate` into a candidate and
(b) every edge from one candidate into another, so a candidate counts as reached only
if something outside the set imports it. Prints JSON.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path.cwd() / "src"
TARGETS = [
    "learnloop.substrate.compat.substrate_cutover",
    "learnloop.scheduling.progression_policy",
    "learnloop.scheduling.progression",
    "learnloop.scheduling.reentry_adapter",
    "learnloop.scheduling.predictive_targets",
    "learnloop.scheduling.short_session",
]
STRING_DISPATCHERS = {"learnloop.params.parameter_registry", "learnloop.scheduling.open_world_gate"}


def module_name(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def main() -> None:
    modules = {module_name(p): p for p in ROOT.rglob("*.py") if "__pycache__" not in p.parts}
    short = {name[len("learnloop."):]: name for name in modules if name.startswith("learnloop.")}
    edges: dict[str, set[str]] = {m: set() for m in modules}
    string_edges: dict[str, set[str]] = {m: set() for m in modules}
    for name, path in modules.items():
        is_pkg = path.name == "__init__.py"
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            targets: list[str] = []
            is_string = False
            if isinstance(node, ast.Import):
                targets = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = name.split(".") if is_pkg else name.split(".")[:-1]
                    base = base[: len(base) - (node.level - 1)] if node.level > 1 else base
                    mod = ".".join(base + ([node.module] if node.module else []))
                else:
                    mod = node.module or ""
                targets = [mod] + [f"{mod}.{a.name}" for a in node.names]
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                is_string = True
                v = node.value.strip()
                if v in modules:
                    targets = [v]
                elif v in short:
                    targets = [short[v]]
                elif v.startswith("src/") and v.endswith(".py"):
                    dotted = v[len("src/"):-len(".py")].replace("/", ".").removesuffix(".__init__")
                    if dotted in modules:
                        targets = [dotted]
            for t in targets:
                parts = t.split(".")
                for i in range(1, len(parts) + 1):
                    cand = ".".join(parts[:i])
                    if cand in modules and cand != name:
                        edges[name].add(cand)
                        if is_string:
                            string_edges[name].add(cand)

    present = [t for t in TARGETS if t in modules]
    pruned = {m: set(e) for m, e in edges.items()}
    for m in STRING_DISPATCHERS & set(modules):
        pruned[m] -= (string_edges[m] & set(present))
    for t in present:
        pruned[t] -= set(present)

    def closure(graph: dict[str, set[str]], roots: list[str]) -> set[str]:
        seen: set[str] = set()
        stack = [r for r in roots if r in graph]
        while stack:
            m = stack.pop()
            if m in seen:
                continue
            seen.add(m)
            stack.extend(graph[m] - seen)
        return seen

    entry = [m for m in modules if m.split(".")[0] in {"learnloop_sidecar", "learnloop_mobile", "learnloop_mcp"}
             or m.startswith(("learnloop.cli", "learnloop.tui"))]
    replay = [f"learnloop.{m}" for m in ("substrate.rebuild_orchestrator", "substrate.shadow_rebuild",
                                         "substrate.canonical_projection", "attempts.attempts",
                                         "daily_plan.engine", "ops.doctor", "db.migrate")]
    plan = [m for m in modules if m.startswith(("learnloop.daily_plan", "learnloop.router",
                                                "learnloop.router_objective"))]
    full = {"entry_points": closure(edges, entry), "replay_rebuild_upgrade": closure(edges, replay),
            "plan_path": closure(edges, plan)}
    cut = {"entry_points": closure(pruned, entry), "replay_rebuild_upgrade": closure(pruned, replay),
           "plan_path": closure(pruned, plan)}
    out = {
        "modules": len(modules),
        "edges": sum(len(e) for e in edges.values()),
        "reached_full": {k: len(v) for k, v in full.items()},
        "reached_pruned": {k: len(v) for k, v in cut.items()},
        "targets": {
            t: {
                "exists": t in modules,
                "importers_all": sorted(m for m, e in edges.items() if t in e),
                "importers_outside_set_and_dispatchers": sorted(m for m, e in pruned.items() if t in e),
                "full": {k: (t in v) for k, v in full.items()},
                "pruned": {k: (t in v) for k, v in cut.items()},
            }
            for t in TARGETS
        },
        "unreached_from_entry_points_pruned": sorted(set(modules) - cut["entry_points"]),
    }
    json.dump(out, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
