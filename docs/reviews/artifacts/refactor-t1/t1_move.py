"""Refactor step T1: move what other files import out of tests/test_*.py into helper modules.

Usage (from the repository root; docs/reviews/refactor-t1.md): t1_move.py plan   -> fixtures-local/t1/plan.json + flags printed, no writes
       t1_move.py apply  -> writes helpers, rewrites donors and every importing file

Per donor tests/test_X.py: the names other tests/*.py files import from it are the seeds; their
top-level definitions plus everything those definitions reference at module level (transitively)
move, verbatim, to tests/X_helpers.py; the imports they need are copied there. The donor imports
back every moved name it still references and every moved fixture. Every ``from tests.test_X
import`` (and ``import tests.test_X as A``) then names ``tests.X_helpers`` instead.
"""

from __future__ import annotations

import ast
import json
import re
import symtable
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path.cwd()
T = ROOT / "tests"
OUT = ROOT / "fixtures-local/t1"

# (importer stem, donor stem): imports left in place (test cases reused by name; see the record).
ALLOW = {("test_p2_leakage_suite", "test_reader_dialogue"), ("test_p2_leakage_suite", "test_surface_pool")}
# Donors that patch their own globals: the patch targets are moved to the helper by hand after apply.
SELF_PATCH_HANDLED = {"test_plan_first_transport_offer_grants", "test_rospeed_ad_link"}
SUSPECT = re.compile(r"__file__|__name__|\binspect\b|getsource|sys\.modules|globals\(\)")


def helper_name(donor: str) -> str:
    return f"{donor[len('test_'):]}_helpers"


def donor_of_from(node: ast.ImportFrom) -> str | None:
    if node.level == 0 and node.module and node.module.startswith("tests.test_"):
        name = node.module[len("tests."):]
        if "." not in name and (T / f"{name}.py").exists():
            return name
    return None


def donor_of_import(alias: ast.alias) -> str | None:
    if alias.name.startswith("tests.test_"):
        name = alias.name[len("tests."):]
        if "." not in name and (T / f"{name}.py").exists():
            return name
    return None


def collect_seeds():
    seeds: dict[str, set[str]] = defaultdict(set)
    for path in sorted(T.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        aliases: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                d = donor_of_from(node)
                if d and (path.stem, d) not in ALLOW:
                    seeds[d].update(a.name for a in node.names)
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == "tests":
                for a in node.names:
                    if a.name.startswith("test_") and (T / f"{a.name}.py").exists():
                        if not a.asname:
                            raise SystemExit(f"{path}: from tests import {a.name} without alias")
                        aliases[a.asname] = a.name
            elif isinstance(node, ast.Import):
                for a in node.names:
                    d = donor_of_import(a)
                    if d:
                        if not a.asname:
                            raise SystemExit(f"{path}: bare import {a.name} without alias")
                        aliases[a.asname] = d
        if aliases:
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases:
                    seeds[aliases[node.value.id]].add(node.attr)
    return seeds


def stmt_start(node: ast.stmt) -> int:
    decos = getattr(node, "decorator_list", None) or []
    return min([node.lineno, *(d.lineno for d in decos)])


class Donor:
    def __init__(self, stem: str):
        self.stem = stem
        self.path = T / f"{stem}.py"
        self.src = self.path.read_text(encoding="utf-8")
        self.lines = self.src.splitlines(keepends=True)
        self.tree = ast.parse(self.src)
        self.flags: list[str] = []
        self.table = symtable.symtable(self.src, str(self.path), "exec")
        self.future = any(isinstance(n, ast.ImportFrom) and n.module == "__future__" for n in self.tree.body)
        # name -> list of statement indexes binding it at top level
        self.binders: dict[str, list[int]] = defaultdict(list)
        for i, node in enumerate(self.tree.body):
            for name in self._binds(node):
                self.binders[name].append(i)
        self.declared_global = set()
        for tbl in self._all_tables(self.table):
            for sym in tbl.get_symbols():
                if sym.is_declared_global():
                    self.declared_global.add(sym.get_name())
        self.has_self_module_patch = bool(re.search(r"sys\.modules\[__name__\]|globals\(\)", self.src))

    @staticmethod
    def _all_tables(tbl):
        yield tbl
        for child in tbl.get_children():
            yield from Donor._all_tables(child)

    def _binds(self, node) -> set[str]:
        out: set[str] = set()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.asname or a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                out.add(a.asname or a.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            tgts = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in tgts:
                for sub in ast.walk(t):
                    if isinstance(sub, ast.Name):
                        out.add(sub.id)
        else:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                    out.add(sub.id)
                elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    out.add(sub.name)
                elif isinstance(sub, (ast.Import, ast.ImportFrom)):
                    for a in sub.names:
                        out.add(a.asname or a.name.split(".")[0])
        return out

    def _module_level_names(self, node) -> set[str]:
        """Names a statement reads at module level (not inside function or class bodies)."""

        out: set[str] = set()

        def visit(n):
            if isinstance(n, ast.Name):
                out.add(n.id)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for d in n.decorator_list:
                    visit(d)
                visit(n.args)
                if n.returns:
                    visit(n.returns)
                return
            if isinstance(n, ast.ClassDef):
                for d in n.decorator_list:
                    visit(d)
                for b in n.bases:
                    visit(b)
                for k in n.keywords:
                    visit(k)
                return
            for c in ast.iter_child_nodes(n):
                visit(c)

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            visit(node)
        else:
            visit(node)
        return out

    def uses(self, i: int) -> set[str]:
        node = self.tree.body[i]
        names = self._module_level_names(node)
        lo, hi = stmt_start(node), node.end_lineno
        for child in self.table.get_children():
            if lo <= child.get_lineno() <= hi:
                for tbl in self._all_tables(child):
                    for sym in tbl.get_symbols():
                        if sym.is_global() and sym.is_referenced():
                            names.add(sym.get_name())
                        elif tbl.get_type() == "class" and sym.is_referenced() and not sym.is_assigned() \
                                and not sym.is_free() and not sym.is_parameter():
                            names.add(sym.get_name())
        # Annotations under `from __future__ import annotations` are strings at runtime but still
        # resolve against module globals (get_type_hints, dataclasses, pydantic): keep them as uses.
        for sub in ast.walk(node):
            if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for a in [*sub.args.args, *sub.args.kwonlyargs, *sub.args.posonlyargs,
                          *(x for x in (sub.args.vararg, sub.args.kwarg) if x)]:
                    if a.annotation is not None:
                        names |= {n.id for n in ast.walk(a.annotation) if isinstance(n, ast.Name)}
                if sub.returns is not None:
                    names |= {n.id for n in ast.walk(sub.returns) if isinstance(n, ast.Name)}
            if isinstance(sub, ast.AnnAssign):
                names |= {n.id for n in ast.walk(sub.annotation) if isinstance(n, ast.Name)}
        return names

    def plan(self, seeds: set[str]):
        body = self.tree.body
        moved: set[int] = set()
        needed_imports: dict[int, set[str]] = defaultdict(set)
        work = list(seeds)
        seen: set[str] = set()
        while work:
            name = work.pop()
            if name in seen:
                continue
            seen.add(name)
            idxs = self.binders.get(name)
            if not idxs:
                if name in seeds:
                    self.flags.append(f"seed {name} not bound at top level")
                continue
            if len(idxs) > 1:
                kinds = {type(body[i]).__name__ for i in idxs}
                if kinds <= {"Assign", "AnnAssign"}:
                    between = range(idxs[0] + 1, idxs[-1])
                    if any(j not in idxs and name in self._module_level_names(body[j]) for j in between):
                        self.flags.append(f"{name} rebound with readers in between")
                elif not kinds <= {"Import", "ImportFrom"}:
                    self.flags.append(f"{name} bound {len(idxs)} times at top level ({sorted(kinds)})")
            for i in idxs:
                node = body[i]
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    needed_imports[i].add(name)
                    continue
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign,
                                         ast.AnnAssign)):
                    self.flags.append(f"{name} bound by a {type(node).__name__} at line {node.lineno}")
                    continue
                if i in moved:
                    continue
                moved.add(i)
                for b in self._binds(node):
                    if b.startswith("test_") or (b.startswith("Test") and isinstance(node, ast.ClassDef)) \
                            or b in ("pytestmark", "pytest_generate_tests"):
                        self.flags.append(f"would move test/collection name {b}")
                    if b in self.declared_global:
                        self.flags.append(f"{b} is declared global somewhere in the donor")
                    seen.add(b)
                work.extend(self.uses(i) - seen)
        if moved and self.has_self_module_patch and self.stem not in SELF_PATCH_HANDLED:
            self.flags.append("donor patches its own module globals (sys.modules[__name__]/globals())")
        suspects = []
        for i in sorted(moved):
            seg = "".join(self.lines[stmt_start(body[i]) - 1: body[i].end_lineno])
            if SUSPECT.search(seg):
                suspects.append(f"line {body[i].lineno}: {SUSPECT.search(seg).group(0)}")
        self.moved, self.needed_imports, self.suspects = moved, needed_imports, suspects
        self.moved_names = set().union(*(self._binds(body[i]) for i in moved)) if moved else set()
        self.fixtures = {body[i].name for i in moved if isinstance(body[i], (ast.FunctionDef, ast.AsyncFunctionDef))
                         and any("fixture" in ast.unparse(d) for d in body[i].decorator_list)}

    # ---- writing -------------------------------------------------------------------------------
    def attached_start(self, i: int) -> int:
        """1-based first line of statement i including the comment block directly above it."""

        start = stmt_start(self.tree.body[i])
        prev_end = self.tree.body[i - 1].end_lineno if i > 0 else 0
        line = start - 1
        while line - 1 >= prev_end and line >= 1 and self.lines[line - 1].lstrip().startswith("#"):
            line -= 1
        return line + 1 if line + 1 <= start else start

    def import_text(self, i: int) -> str:
        node = self.tree.body[i]
        names = self.needed_imports[i]
        if isinstance(node, ast.Import):
            return "".join(self.lines[node.lineno - 1: node.end_lineno]).rstrip("\n") if \
                len(node.names) == 1 else "\n".join(
                    f"import {a.name}" + (f" as {a.asname}" if a.asname else "")
                    for a in node.names if (a.asname or a.name.split(".")[0]) in names)
        keep = [a for a in node.names if (a.asname or a.name) in names]
        parts = [a.name + (f" as {a.asname}" if a.asname else "") for a in keep]
        mod = "." * node.level + (node.module or "")
        one = f"from {mod} import {', '.join(parts)}"
        if len(one) <= 110:
            return one
        return f"from {mod} import (\n" + "".join(f"    {p},\n" for p in parts) + ")"

    def sections(self):
        """[(header lines 0-based [lo, hi) incl. the blank lines after it, [statement indexes])]: a comment block at
        column 0 with a blank line after it heads the top-level statements up to the next such block."""

        body = self.tree.body
        heads = []
        for i in range(1, len(body)):
            lo, hi = body[i - 1].end_lineno, self.attached_start(i) - 1  # gap, 0-based [lo, hi)
            k = lo
            last = None
            while k < hi:
                if self.lines[k].startswith("#"):
                    j = k
                    while j < hi and self.lines[j].startswith("#"):
                        j += 1
                    e = j
                    while e < hi and not self.lines[e].strip():
                        e += 1
                    if j < hi:  # a blank line follows, so it is a header, not an attached comment
                        last = (k, e)
                    k = e
                else:
                    k += 1
            if last:
                heads.append((last, i))
        out = []
        for n, ((lo, hi), first) in enumerate(heads):
            end = heads[n + 1][1] if n + 1 < len(heads) else len(body)
            out.append(((lo, hi), list(range(first, end))))
        return out

    def moved_headers(self):
        """{first statement index: (lo, hi)} for headers whose whole section moves."""

        return {stmts[0]: span for span, stmts in self.sections() if stmts and all(i in self.moved for i in stmts)}

    def helper_source(self) -> str:
        body = self.tree.body
        out = [f'"""What other test files use from ``tests/{self.stem}.py``, kept here because a test file never\n'
               f'imports another (``tests/test_test_layout.py``; refactor step T1)."""\n']
        if self.future:
            out.append("\nfrom __future__ import annotations\n")
        groups = {0: [], 1: [], 2: [], 3: []}
        for i in sorted(self.needed_imports):
            text = self.import_text(i)
            if not text or "__future__" in text:
                continue
            node = body[i]
            top = (node.module if isinstance(node, ast.ImportFrom) else node.names[0].name).split(".")[0]
            g = 3 if top == "tests" else 2 if top.startswith("learnloop") else 0 if top in sys.stdlib_module_names \
                else 1
            groups[g].append(text)
        blocks = ["\n".join(v) for _, v in sorted(groups.items()) if v]
        if blocks:
            out.append("\n" + "\n\n".join(blocks) + "\n")
        headers = self.moved_headers()
        prev_kind = None
        for i in sorted(self.moved):
            node = body[i]
            seg = "".join(self.lines[self.attached_start(i) - 1: node.end_lineno]).rstrip("\n") + "\n"
            kind = "def" if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else "assign"
            sep = "\n\n" if (kind == "def" or prev_kind in (None, "def")) else ""
            if i in headers:
                lo, hi = headers[i]
                head = "".join(self.lines[lo:hi]).rstrip("\n") + "\n"
                out.append("\n\n" + head + ("\n\n" if kind == "def" else "\n") + seg)
            else:
                out.append(sep + seg)
            prev_kind = kind
        return "".join(out)

    def donor_source(self) -> str:
        body = self.tree.body
        drop: set[int] = set()  # 0-based line indexes
        for i in self.moved:
            start = self.attached_start(i) - 1
            end = body[i].end_lineno  # exclusive 0-based
            while end < len(self.lines) and not self.lines[end].strip():
                end += 1
            drop.update(range(start, end))
        for lo, hi in self.moved_headers().values():
            drop.update(range(lo, hi))
        # A dropped run between two kept non-blank lines keeps its trailing blank lines, so the statements
        # around it stay apart (a moved constant written right under a kept one, then a def).
        k = 0
        while k < len(self.lines):
            if k in drop:
                a = k
                while k < len(self.lines) and k in drop:
                    k += 1
                b = k
                if a > 0 and self.lines[a - 1].strip() and b < len(self.lines) and self.lines[b].strip():
                    t = b
                    while t - 1 >= a and not self.lines[t - 1].strip():
                        t -= 1
                    drop.difference_update(range(t, b))
            else:
                k += 1
        remaining_src = "".join(line for k, line in enumerate(self.lines) if k not in drop)
        # Which moved names does the rest still use?
        try:
            rtree = ast.parse(remaining_src)
        except SyntaxError as exc:  # pragma: no cover - reported
            raise SystemExit(f"{self.stem}: remaining source does not parse: {exc}")
        used = set()
        for n in ast.walk(rtree):
            if isinstance(n, ast.Name):
                used.add(n.id)
            elif isinstance(n, ast.arg):
                used.add(n.arg)
            elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.isidentifier():
                used.add(n.value)
        by_name = sorted(n for n in self.moved_names if n in used and n not in self.fixtures)
        fixture_only = sorted(self.fixtures)
        new_lines = []
        mod = f"tests.{helper_name(self.stem)}"
        if by_name:
            new_lines.append(_from_line(mod, by_name, ""))
        if fixture_only:
            new_lines.append(_from_line(mod, fixture_only, "  # noqa: F401 - fixtures, used by parameter name"))
        insert_after = None  # 0-based line index after which to insert
        for node in body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and node is body[0]:
                insert_after = node.end_lineno - 1
                continue
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                insert_after = node.end_lineno - 1
                continue
            break
        out = []
        block = "".join(s + "\n" for s in new_lines)
        if insert_after is None:
            out.append(block + "\n")
        for k, line in enumerate(self.lines):
            if k not in drop:
                out.append(line)
            if k == insert_after:
                out.append(block)
        return "".join(out).rstrip("\n") + "\n"


def _from_line(mod: str, names: list[str], comment: str) -> str:
    one = f"from {mod} import {', '.join(names)}{comment}"
    if len(one) <= 110:
        return one
    return f"from {mod} import ({comment}\n" + "".join(f"    {n},\n" for n in names) + ")"


def rewrite_imports(path: Path, donors: set[str]) -> bool:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)
    changed = False
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.ImportFrom):
            d = donor_of_from(node)
            if d and d in donors and (path.stem, d) not in ALLOW:
                targets.append(d)
        elif isinstance(node, ast.Import):
            for a in node.names:
                d = donor_of_import(a)
                if d and d in donors:
                    targets.append(d)
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == "tests":
            for a in node.names:
                if a.name in donors:
                    if node.lineno != node.end_lineno:
                        raise SystemExit(f"{path}:{node.lineno}: multi-line from tests import")
                    k = node.lineno - 1
                    new, n = re.subn(rf"\b{a.name}\b(?= as )", helper_name(a.name), lines[k], count=1)
                    if n != 1:
                        raise SystemExit(f"{path}:{node.lineno}: could not rewrite {a.name}")
                    lines[k] = new
                    changed = True
        for d in targets:
            k = node.lineno - 1
            pat = re.compile(rf"\btests\.{d}\b")
            new, n = pat.subn(f"tests.{helper_name(d)}", lines[k], count=1)
            if n != 1:
                raise SystemExit(f"{path}:{node.lineno}: could not rewrite {d}")
            lines[k] = new
            changed = True
    if changed:
        path.write_text("".join(lines), encoding="utf-8")
    return changed


def main(mode: str) -> int:
    seeds = collect_seeds()
    plans = {}
    all_flags = {}
    for stem in sorted(seeds):
        d = Donor(stem)
        d.plan(seeds[stem])
        hp = T / f"{helper_name(stem)}.py"
        if hp.exists():
            d.flags.append(f"helper path {hp.name} exists")
        plans[stem] = d
        if d.flags:
            all_flags[stem] = d.flags
    report = {stem: {"seeds": sorted(seeds[stem]), "moved": sorted(d.moved_names), "fixtures": sorted(d.fixtures),
                     "suspects": d.suspects, "flags": d.flags,
                     "imports": sorted({n for s in d.needed_imports.values() for n in s})}
              for stem, d in plans.items()}
    (OUT / "plan.json").write_text(json.dumps(report, indent=1))
    print(f"donors {len(plans)}; flagged {len(all_flags)}; moved names {sum(len(d.moved_names) for d in plans.values())}")
    for stem, flags in all_flags.items():
        print(stem, flags)
    sus = {s: d.suspects for s, d in plans.items() if d.suspects}
    print("suspects:", json.dumps(sus, indent=0))
    if mode != "apply":
        return 0
    if all_flags:
        print("refusing to apply with flags")
        return 1
    donors = set(plans)
    for stem, d in plans.items():
        (T / f"{helper_name(stem)}.py").write_text(d.helper_source(), encoding="utf-8")
        d.path.write_text(d.donor_source(), encoding="utf-8")
    touched = []
    for path in sorted(T.glob("*.py")):
        if rewrite_imports(path, donors):
            touched.append(path.name)
    (OUT / "touched.json").write_text(json.dumps({"donors": sorted(donors), "rewritten": touched,
                                                  "helpers": sorted(helper_name(s) + ".py" for s in donors)}, indent=1))
    print(f"wrote {len(donors)} helpers; rewrote imports in {len(touched)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "plan"))
