"""C1 closure: which src modules can the entry points and replay roots reach?

AST import edges over src/ (module-level and function-local imports, TYPE_CHECKING
blocks included, which over-approximates), plus a string edge for every string
constant naming a module (dotted, with or without the `learnloop.` prefix), which
covers MODULE_INVENTORY, open_world_gate, valuation's named gaps and the scoreboard.
Prints JSON: module count, reached count per root set, and the targets' reach.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path.cwd() / "src"
TARGETS = [
    "learnloop.diagnosis.causal_migration",
    "learnloop.diagnosis.remediation_intake",
    "learnloop.substrate.compat.card_outcome_replay",
    "learnloop.scheduling.prequential",
    "learnloop.sim.interval_width_viability",
]


def module_name(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def main() -> None:
    modules = {module_name(p): p for p in ROOT.rglob("*.py") if "__pycache__" not in p.parts}
    short = {}
    for name in modules:
        if name.startswith("learnloop."):
            short[name[len("learnloop."):]] = name
    edges: dict[str, set[str]] = {m: set() for m in modules}
    for name, path in modules.items():
        is_pkg = path.name == "__init__.py"
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            targets: list[str] = []
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
                v = node.value.strip()
                if v in modules:
                    targets = [v]
                elif v in short:
                    targets = [short[v]]
                elif v.startswith("src/") and v.endswith(".py"):
                    # MODULE_INVENTORY names modules by path (`src/learnloop/x/y.py`)
                    dotted = v[len("src/"):-len(".py")].replace("/", ".").removesuffix(".__init__")
                    if dotted in modules:
                        targets = [dotted]
            for t in targets:
                # importing a.b.c also imports a and a.b
                parts = t.split(".")
                for i in range(1, len(parts) + 1):
                    cand = ".".join(parts[:i])
                    if cand in modules and cand != name:
                        edges[name].add(cand)

    def closure(roots: list[str]) -> set[str]:
        seen = set()
        stack = [r for r in roots if r in modules]
        while stack:
            m = stack.pop()
            if m in seen:
                continue
            seen.add(m)
            stack.extend(edges[m] - seen)
        return seen

    entry = [m for m in modules if m.split(".")[0] in {"learnloop_sidecar", "learnloop_mobile", "learnloop_mcp"}
             or m.startswith(("learnloop.cli", "learnloop.tui"))]
    replay = [f"learnloop.{m}" for m in ("substrate.rebuild_orchestrator", "substrate.shadow_rebuild",
                                         "substrate.canonical_projection", "attempts.attempts",
                                         "daily_plan.engine", "ops.doctor", "db.migrate")]
    sets = {"entry_points": closure(entry), "replay_rebuild_upgrade": closure(replay)}
    importers = {t: sorted(m for m, e in edges.items() if t in e) for t in TARGETS}
    out = {
        "modules": len(modules),
        "edges": sum(len(e) for e in edges.values()),
        "reached": {k: len(v) for k, v in sets.items()},
        "targets": {t: {"exists": t in modules, "importers": importers[t],
                        **{k: (t in v) for k, v in sets.items()}} for t in TARGETS},
    }
    out["unreached_from_entry_points"] = sorted(set(modules) - sets["entry_points"])
    json.dump(out, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
