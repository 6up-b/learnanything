"""The refactor's success measures (docs/specs/refactor_strategy_v3.md §6), one way.

S0 and Z2 both run this script, so the "before" and "after" are counted the
same way. Three kinds of measure:

- computed from the checkout (the default, a few seconds): sizes, module and
  file counts, the plumbing counts, version-literal and tag-gate counts;
- timed (``--timed``): the serial, ``-n 8`` and durability suite times, and step A6's two gates (``landing``, ``arc_close``). These
  take machine time, so they run only when asked, and the exact commands are
  printed either way;
- manual: measures that need judgment or the owner. Listed with their procedure.

Only tracked files are read (``git ls-files``), so a gitignored
``fixtures-local/`` or a stray vault never enters a count. Nothing here opens a
database or makes a model call. Run it under an empty ``HOME`` and config dir:

    uv run python scripts/refactor_measures.py --json out.json --markdown out.md
"""

from __future__ import annotations

import argparse
import ast
import importlib
import io
import json
import re
import shlex
import subprocess
import sys
import time
import tokenize
import tomllib
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("src/learnloop", "src/learnloop_sidecar", "src/learnloop_mobile", "src/learnloop_mcp")
TAG = re.compile(r"mvp-0\.(\d+)")
DEFAULT_FLOOR = "mvp-0.43"
UPGRADE_FAMILY = re.compile(r"(upgrade|successor)")


# -- files ---------------------------------------------------------------------


def tracked(*prefixes: str, suffix: str | None = None) -> list[Path]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--", *prefixes],
        check=True, capture_output=True,
    ).stdout.decode()
    paths = [ROOT / p for p in out.split("\0") if p]
    # A tracked file deleted in the working tree is not part of this checkout.
    return [p for p in paths if p.is_file() and (suffix is None or p.suffix == suffix)]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


# -- per-file Python facts -----------------------------------------------------

_SKIP_TOKENS = {
    tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
    tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER,
}


def _string_statement_lines(tree: ast.AST) -> set[int]:
    """Lines of string-only expression statements: docstrings and the bare
    triple-quoted blocks used as comments. Not code by the map's definition."""

    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            lines.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    return lines


def python_facts(path: Path) -> dict:
    """Raw and code lines, statements, functions, long functions, and the
    ``mvp-0.N`` literals by where they sit (comment / docstring or multi-line
    string / code string). Same definitions as the map's §1 sweep."""

    text = read(path)
    facts = {"raw": text.count("\n") + (0 if text.endswith("\n") or not text else 1),
             "code": 0, "statements": 0, "functions": 0, "long_functions": [],
             "tags": {"comment": 0, "docstring": 0, "code": 0}}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return facts
    doc_lines = _string_statement_lines(tree)
    code_lines: set[int] = set()
    fstring_triple: list[bool] = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError):
        tokens = []
    for tok in tokens:
        kind = tok.type
        if kind == tokenize.COMMENT:
            facts["tags"]["comment"] += len(TAG.findall(tok.string))
            continue
        if kind == getattr(tokenize, "FSTRING_START", -1):
            fstring_triple.append(tok.string.rstrip().endswith(('"""', "'''")))
        elif kind == getattr(tokenize, "FSTRING_END", -1) and fstring_triple:
            fstring_triple.pop()
        if kind == tokenize.STRING or kind == getattr(tokenize, "FSTRING_MIDDLE", -1):
            hits = len(TAG.findall(tok.string))
            if hits:
                if kind == tokenize.STRING:
                    body = tok.string.lstrip("rRbBuUfF")
                    multi = body.startswith(('"""', "'''"))
                else:
                    multi = bool(fstring_triple and fstring_triple[-1])
                where = "docstring" if multi or tok.start[0] in doc_lines else "code"
                facts["tags"][where] += hits
        if kind in _SKIP_TOKENS:
            continue
        for line in range(tok.start[0], tok.end[0] + 1):
            if line not in doc_lines:
                code_lines.add(line)
    facts["code"] = len(code_lines)
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt):
            facts["statements"] += 1
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            facts["functions"] += 1
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            if length > 100:
                facts["long_functions"].append((node.name, node.lineno, length))
    return facts


# -- version sets and tag gates ------------------------------------------------


def _version_set_values(src_files: list[Path]) -> tuple[dict[str, frozenset], set[str], list[str]]:
    """Every module-level ``*_VERSIONS`` set of algorithm tags in ``src`` and
    its value, read by importing the module that defines it; and the names of
    ``*_VERSIONS`` sets that hold something else (prompt or schema versions),
    which aren't tag gates. Names defined twice with different values are left
    out and reported."""

    values: dict[str, frozenset] = {}
    other: set[str] = set()
    clash: set[str] = set()
    problems: list[str] = []
    for path in src_files:
        tree = ast.parse(read(path))
        names = []
        for node in tree.body:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
            names += [t.id for t in targets if isinstance(t, ast.Name) and t.id.endswith("_VERSIONS")]
        if not names:
            continue
        module = rel(path)[len("src/"):-len(".py")].replace("/", ".").removesuffix(".__init__")
        try:
            mod = importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001 - a count, not a gate: report and go on
            problems.append(f"import {module}: {type(exc).__name__}")
            continue
        for name in names:
            value = getattr(mod, name, None)
            if not isinstance(value, (set, frozenset, tuple, list)):
                continue
            value = frozenset(str(v) for v in value)
            if not value or not all(TAG.fullmatch(v) for v in value):
                other.add(name)
                continue
            if name in values and values[name] != value:
                clash.add(name)
            values.setdefault(name, value)
    for name in clash:
        values.pop(name, None)
        problems.append(f"{name} has two different definitions; its gates are not classified")
    return values, other - set(values), problems


def _gate_target(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name) and node.id.endswith("_VERSIONS"):
        return node.id
    if isinstance(node, ast.Attribute) and node.attr.endswith("_VERSIONS"):
        return node.attr
    return None


def tag_gates(src_files: list[Path], floor: str) -> dict:
    """``x in X_VERSIONS`` / ``not in`` sites in ``src``. A gate is constant at
    the floor when every tag from the floor to the latest is in the set (or none
    is): on a vault at or above the floor, its other branch can't run. The
    paired-with-a-kill-switch split is not counted; it needs reading (§6)."""

    from learnloop.algorithm_versions import SUCCESSOR_CHAIN

    chain = list(SUCCESSOR_CHAIN)
    if floor not in chain:
        return {"error": f"floor {floor} is not in SUCCESSOR_CHAIN"}
    live = set(chain[chain.index(floor):])
    values, other, problems = _version_set_values(src_files)
    total = constant = unknown = 0
    varying_sites: list[str] = []
    constant_sites: list[str] = []
    for path in src_files:
        text = read(path)
        if "_VERSIONS" not in text:
            continue
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, ast.Compare):
                continue
            for op, right in zip(node.ops, node.comparators, strict=True):
                if not isinstance(op, (ast.In, ast.NotIn)):
                    continue
                name = _gate_target(right)
                if name is None or name in other:
                    continue
                total += 1
                value = values.get(name)
                if value is None:
                    unknown += 1
                elif live <= value or not (live & value):
                    constant += 1
                    constant_sites.append(f"{rel(path)}:{node.lineno} {name}")
                else:
                    varying_sites.append(f"{rel(path)}:{node.lineno} {name}")
    return {
        "floor": floor, "latest": chain[-1], "chain_length": len(chain),
        "version_sets": len(values), "gates": total, "constant_at_floor": constant,
        "varying": len(varying_sites), "unclassified": unknown,
        "varying_sites": varying_sites, "constant_sites": constant_sites, "problems": problems,
    }


# -- test plumbing -------------------------------------------------------------


def _frozen_set_assertions(tree: ast.AST) -> int:
    """``X_VERSIONS == frozenset({...})`` (or a set literal): a pin every new
    tag edits (test-suite audit §7)."""

    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or not any(isinstance(op, ast.Eq) for op in node.ops):
            continue
        sides = [node.left, *node.comparators]
        if not any(_gate_target(s) for s in sides):
            continue
        for side in sides:
            literal = side.args[0] if (
                isinstance(side, ast.Call) and isinstance(side.func, ast.Name)
                and side.func.id in {"frozenset", "set"} and side.args
            ) else side
            if isinstance(literal, (ast.Set, ast.List, ast.Tuple)) and any(
                isinstance(e, ast.Constant) and isinstance(e.value, str) and TAG.fullmatch(e.value)
                for e in literal.elts
            ):
                count += 1
                break
    return count


def _latest_pin(tree: ast.AST) -> bool:
    """``LATEST == "mvp-0.N"`` or ``SUCCESSOR_CHAIN[-1] == "mvp-0.N"``."""

    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        sides = [node.left, *node.comparators]
        names_latest = any(
            (isinstance(s, ast.Name) and s.id == "LATEST")
            or (isinstance(s, ast.Attribute) and s.attr == "LATEST")
            or (isinstance(s, ast.Subscript) and isinstance(s.value, (ast.Name, ast.Attribute))
                and getattr(s.value, "id", getattr(s.value, "attr", "")) == "SUCCESSOR_CHAIN")
            for s in sides
        )
        literal = any(isinstance(s, ast.Constant) and isinstance(s.value, str) and TAG.fullmatch(s.value) for s in sides)
        if names_latest and literal:
            return True
    return False


def test_plumbing(test_files: list[Path], floor: str, latest: str) -> dict:
    floor_n, latest_n = int(TAG.fullmatch(floor).group(1)), int(TAG.fullmatch(latest).group(1))
    out = Counter()
    frozen_files: list[str] = []
    for path in test_files:
        text = read(path)
        tags = {int(m) for m in TAG.findall(text)}
        if tags:
            out["files_naming_any_tag"] += 1
        if any(n >= floor_n for n in tags):
            out["files_naming_a_tag_at_or_above_floor"] += 1
        if latest_n in tags:
            out["files_naming_the_latest_tag"] += 1
        if "DEFAULTS_SNAPSHOT_BY_ALGORITHM" in text or "defaults_fingerprint_for_version" in text:
            out["files_reading_defaults_digests"] += 1
        if "LEGACY_DEFAULT_CONFIG_TEXT" in text:
            out["files_reading_legacy_default_config_text"] += 1
        uses_vault = "create_basic_vault" in text
        if uses_vault:
            out["files_using_create_basic_vault"] += 1
            if not tags and not re.search(r"algorithm_version|\bLATEST\b|SUCCESSOR_CHAIN", text):
                out["of_those_naming_no_version"] += 1
        if not path.name.startswith("test_"):
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        n = _frozen_set_assertions(tree)
        if n:
            out["frozen_version_set_assertions"] += n
            frozen_files.append(rel(path))
        if _latest_pin(tree):
            out["files_with_a_latest_pin"] += 1
    out["files_with_frozen_version_sets"] = len(frozen_files)
    return dict(out)


def head_fixture_refs() -> dict:
    """Files naming the current head fixture's directory: each one is edited
    at every migration (A2). An old head named in a comment isn't counted."""

    heads = sorted(p.name for p in (ROOT / "fixtures").glob("migration_head*") if p.is_dir())
    names = re.compile("|".join(re.escape(h) + r"\b" for h in heads) or r"(?!)")
    files = tracked("tests", "scripts", "docs/learnloop-architecture-vault/_scripts")
    by_root = Counter()
    lines = 0
    for path in files:
        if path.suffix not in {".py", ".toml", ".json", ".md", ".txt", ".sql"}:
            continue
        hits = sum(1 for line in read(path).splitlines() if names.search(line))
        if hits:
            by_root["tests" if rel(path).startswith("tests/") else "scripts"] += 1
            lines += hits
    fixture_files = tracked(*(f"fixtures/{h}" for h in heads)) if heads else []
    return {"head_fixtures": heads, "head_fixture_files": len(fixture_files),
            "files_naming_head_path": sum(by_root.values()), "test_files": by_root["tests"],
            "script_files": by_root["scripts"], "lines": lines}


def generated_notes() -> dict:
    notes = tracked("docs/learnloop-architecture-vault", suffix=".md")
    generated = stamped = 0
    for path in notes:
        head = read(path)[:4000]
        if not head.startswith("---"):
            continue
        front = head.split("\n---", 1)[0]
        if re.search(r"^generated:\s*true\s*$", front, re.M):
            generated += 1
            if re.search(r"^source_commit:", front, re.M):
                stamped += 1
    return {"vault_notes": len(notes), "generated_notes": generated,
            "generated_notes_with_commit_stamps": stamped}


def defaults_digests() -> dict:
    out: dict = {}
    try:
        from learnloop.config import template
        out["defaults_digests"] = len(getattr(template, "DEFAULTS_SNAPSHOT_BY_ALGORITHM", {}) or {})
    except Exception as exc:  # noqa: BLE001
        out["defaults_digests_error"] = type(exc).__name__
    try:
        from learnloop.config.schema import AlgorithmsConfig
        out["algorithms_config_default_tag"] = AlgorithmsConfig.model_fields["algorithm_version"].default
    except Exception as exc:  # noqa: BLE001
        out["algorithms_config_default_error"] = type(exc).__name__
    return out


def repository_methods() -> int:
    tree = ast.parse(read(ROOT / "src/learnloop/db/repositories.py"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Repository":
            return sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in node.body)
    return -1


def import_contracts() -> int:
    data = tomllib.loads(read(ROOT / "pyproject.toml"))
    return len(data.get("tool", {}).get("importlinter", {}).get("contracts", []))


# -- the computed sweep --------------------------------------------------------


def computed(floor: str) -> dict:
    sys.path.insert(0, str(ROOT / "src"))
    src_files = tracked(*PACKAGES, suffix=".py")
    totals = Counter()
    tag_where = Counter()
    long_fns: list[tuple[str, str, int, int]] = []
    per_file_raw: dict[str, int] = {}
    for path in src_files:
        f = python_facts(path)
        per_file_raw[rel(path)] = f["raw"]
        for key in ("raw", "code", "statements", "functions"):
            totals[key] += f[key]
        tag_where.update(f["tags"])
        long_fns += [(rel(path), name, line, n) for name, line, n in f["long_functions"]]
    over200 = sorted((n, f"{p}:{line} {name}") for p, name, line, n in long_fns if n > 200)
    root_upgrades = [p for p in src_files if re.fullmatch(r"src/learnloop/[a-z0-9_]+_upgrade\.py", rel(p))]
    all_upgrades = [p for p in src_files if "upgrade" in p.name]
    test_files = tracked("tests", suffix=".py")
    family = [p for p in test_files if p.name.startswith("test_") and UPGRADE_FAMILY.search(p.name)]
    gates = tag_gates(src_files, floor)
    latest = gates.get("latest") or floor
    return {
        "size": {
            "python_files": len(src_files),
            "src_learnloop_files": sum(1 for p in src_files if rel(p).startswith("src/learnloop/")),
            "raw_lines": totals["raw"], "code_lines": totals["code"],
            "statements": totals["statements"], "functions": totals["functions"],
            "functions_over_100_lines": len(long_fns),
            "functions_over_200_lines": len(over200),
            "longest_functions": [s for _, s in sorted(over200, reverse=True)[:10]],
            "config_template_lines": per_file_raw.get("src/learnloop/config/template.py"),
            "config_schema_lines": per_file_raw.get("src/learnloop/config/schema.py"),
            "test_python_files": len(test_files),
            "test_files_named_test_": sum(1 for p in test_files if p.name.startswith("test_")),
            "test_lines": sum(read(p).count("\n") for p in test_files),
            "migrations": len(tracked("migrations", suffix=".sql")),
        },
        "rules": {
            "root_upgrade_modules": len(root_upgrades),
            "all_upgrade_modules": len(all_upgrades),
            "upgrade_module_lines": sum(per_file_raw[rel(p)] for p in all_upgrades),
            "repository_methods": repository_methods(),
            "tag_literals": dict(tag_where),
            "tag_gates": gates,
            "import_linter_contracts": import_contracts(),
        },
        "plumbing": {
            "head_fixture": head_fixture_refs(),
            **defaults_digests(),
            **generated_notes(),
            "tests": test_plumbing(test_files, floor, latest),
            "upgrade_and_successor_test_files": len(family),
            "upgrade_and_successor_test_lines": sum(read(p).count("\n") for p in family),
        },
    }


# -- timed ---------------------------------------------------------------------

TIMED = {
    # The audit's -n 8 figures were taken in a 10 GB scope; serial and
    # durability fit in 5 GB. Keep these identical at S0 and Z2.
    "serial": ("5G", ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider"]),
    "n8": ("10G", ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider", "-n", "8", "--dist", "worksteal"]),
    "durability": ("5G", ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider", "-m", "durability"]),
    # Step A6's two gates, which split n8's tests between them: every landing runs "landing", each arc's close runs
    # "arc_close". n8 stays the whole suite, so S0 and Z2 compare like with like.
    "landing": ("10G", ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider", "-n", "8", "--dist", "worksteal",
                        "-m", "not arc_close"]),
    "arc_close": ("10G", ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider", "-n", "8", "--dist", "worksteal",
                          "-m", "arc_close"]),
}


def timed_command(name: str, junit: Path) -> list[str]:
    memory, cmd = TIMED[name]
    return ["systemd-run", "--user", "--scope", "--quiet", "-p", f"MemoryMax={memory}",
            "-p", "MemorySwapMax=1G", *cmd, f"--junitxml={junit}"]


def junit_seconds(junit: Path) -> dict:
    """Test seconds in all, and the upgrade-and-successor family's share."""

    total = family = 0.0
    tests = 0
    for case in ET.parse(junit).iter("testcase"):
        seconds = float(case.get("time") or 0)
        total += seconds
        tests += 1
        if UPGRADE_FAMILY.search((case.get("classname") or "").rsplit(".", 1)[-1]):
            family += seconds
    return {"tests": tests, "test_seconds": round(total, 1), "upgrade_family_seconds": round(family, 1),
            "upgrade_family_share": round(family / total, 4) if total else None}


def run_timed(names: list[str], out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for name in names:
        junit = out_dir / f"{name}.xml"
        cmd = timed_command(name, junit)
        print(f"running {name}: {shlex.join(cmd)}", file=sys.stderr)
        start = time.monotonic()
        code = subprocess.run(cmd, cwd=ROOT).returncode
        results[name] = {"command": shlex.join(cmd), "exit_code": code,
                         "wall_seconds": round(time.monotonic() - start, 1)}
        if junit.is_file():
            results[name].update(junit_seconds(junit))
    return results


# -- manual --------------------------------------------------------------------

MANUAL = [
    ("Time to locate (§6)", "A fresh agent gets only a symptom, the vault and `why`; record minutes and files opened. "
     "Symptoms: (1) dormant or resolved learning objects still served (docs/reviews/daily-loop-bugs.md §2); "
     "(2) choosing a help style changed nothing (docs/reviews/owner-capture-2026-10-25-fixes.md B2); "
     "(3) the scheduler offer does not belong to this item/session (same, B4); (4) a router decision that fell back "
     "to a rule: which model failed and how; (5) where to change the mixing rule, an objective term, a route, a threshold."),
    ("The four real cases", "tests/test_why_cases.py passes; tests/test_why_real_cases.py passes on the owner's fresh "
     "backup copy (backup-API copy under fixtures-local/why-cases/); a no-code reader answers from `why`'s output."),
    ("`why` coverage", "`learnloop why` answers the latest decision, an attempt, a block and a figure with chosen, "
     "alternatives, losers' reasons, inputs, decider, versions, seed, next."),
    ("Silent sites S1-S15", "Each has a fail-first test, or a line in ADR-017 saying why not."),
    ("Decisions with no record", "B8's inventory lists none unexplained."),
    ("What a change costs", "On a scratch branch at Z2, make each §6 sample change and count files edited "
     "(git diff --stat); 'today' figures are in the strategy's §6 and the map's §9."),
    ("Next right after feedback; connection opens per job", "The router speed harness on large backup-API copies "
     "(docs/reviews/router-speed2.md, method and pinned week), against mvp-0.49 by the same method."),
    ("Decision values at a fixed draw count", "P-draw: byte-identical across each speed step."),
    ("Kill switches at or below the floor", "Read D7's list; count the switches whose tag is at or below the floor."),
    ("Tag gates paired with a kill switch", "Read each site in the JSON's `constant_sites`; the split isn't syntactic."),
    ("Database size", "The owner reports each live vault's state.sqlite size before and after each drop (private; "
     "kept in fixtures-local/, never committed)."),
    ("Removed list", "Z2's report names every removed feature."),
]


# -- output --------------------------------------------------------------------


def markdown(report: dict) -> str:
    c = report.get("computed", {})
    size, rules, plumb = c.get("size", {}), c.get("rules", {}), c.get("plumbing", {})
    gates = rules.get("tag_gates", {})
    tags = rules.get("tag_literals", {})
    head = plumb.get("head_fixture", {})
    tests = plumb.get("tests", {})
    rows = [
        ("Python files, all four packages", size.get("python_files")),
        ("Raw lines; code lines", f"{size.get('raw_lines')}; {size.get('code_lines')}"),
        ("Statements; functions", f"{size.get('statements')}; {size.get('functions')}"),
        ("Functions over 100 lines; over 200", f"{size.get('functions_over_100_lines')}; {size.get('functions_over_200_lines')}"),
        ("`config/template.py`; `config/schema.py` lines", f"{size.get('config_template_lines')}; {size.get('config_schema_lines')}"),
        ("Root `*_upgrade.py`; all upgrade modules (lines)",
         f"{rules.get('root_upgrade_modules')}; {rules.get('all_upgrade_modules')} ({rules.get('upgrade_module_lines')})"),
        ("`Repository` methods", rules.get("repository_methods")),
        ("`mvp-0.N` literals: code / docstring / comment", f"{tags.get('code')} / {tags.get('docstring')} / {tags.get('comment')}"),
        (f"Tag gates: constant at {gates.get('floor')} / all (varying, unclassified)",
         f"{gates.get('constant_at_floor')} / {gates.get('gates')} ({gates.get('varying')}, {gates.get('unclassified')})"),
        ("Latest tag; chain length", f"{gates.get('latest')}; {gates.get('chain_length')}"),
        ("Import-linter contracts", rules.get("import_linter_contracts")),
        ("Head fixture; its tracked files", f"{', '.join(head.get('head_fixtures', []))}; {head.get('head_fixture_files')}"),
        ("Files naming the head path: tests + scripts (lines)",
         f"{head.get('test_files')} + {head.get('script_files')} ({head.get('lines')})"),
        ("Frozen defaults digests; test files reading them",
         f"{plumb.get('defaults_digests')}; {tests.get('files_reading_defaults_digests')}"),
        ("Frozen `*_VERSIONS` set assertions (files)",
         f"{tests.get('frozen_version_set_assertions')} ({tests.get('files_with_frozen_version_sets')})"),
        ("Test files with a latest pin", tests.get("files_with_a_latest_pin")),
        ("Test files naming the latest tag; a tag at or above the floor; any tag",
         f"{tests.get('files_naming_the_latest_tag')}; {tests.get('files_naming_a_tag_at_or_above_floor')}; {tests.get('files_naming_any_tag')}"),
        ("Default test vault's tag; files using it; of those naming no version",
         f"{plumb.get('algorithms_config_default_tag')}; {tests.get('files_using_create_basic_vault')}; {tests.get('of_those_naming_no_version')}"),
        ("Upgrade and successor test files (lines)",
         f"{plumb.get('upgrade_and_successor_test_files')} ({plumb.get('upgrade_and_successor_test_lines')})"),
        ("Vault notes; generated; generated with commit stamps",
         f"{plumb.get('vault_notes')}; {plumb.get('generated_notes')}; {plumb.get('generated_notes_with_commit_stamps')}"),
        ("Test Python files (named `test_*`); lines",
         f"{size.get('test_python_files')} ({size.get('test_files_named_test_')}); {size.get('test_lines')}"),
        ("Migrations", size.get("migrations")),
    ]
    lines = [f"# Refactor measures at `{report['commit']}`", "",
             f"Computed {report['generated_at']}. Floor {gates.get('floor')}.", "",
             "| Measure | Value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in rows]
    lines += ["", "## Timed", ""]
    timed = report.get("timed")
    if timed:
        lines += ["| Run | Wall s | Exit | Tests | Test s | Upgrade family share |", "|---|---:|---:|---:|---:|---:|"]
        for name, r in timed.items():
            lines.append(f"| {name} | {r.get('wall_seconds')} | {r.get('exit_code')} | {r.get('tests')} | "
                         f"{r.get('test_seconds')} | {r.get('upgrade_family_share')} |")
    else:
        lines.append("Not run (pass `--timed`). The commands:")
    lines += ["", "```"] + report["timed_commands"] + ["```", "", "## Manual", ""]
    lines += [f"- **{name}.** {how}" for name, how in MANUAL]
    if gates.get("problems"):
        lines += ["", "## Problems", ""] + [f"- {p}" for p in gates["problems"]]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--floor", default=DEFAULT_FLOOR, help="oldest tag a live vault holds (default %(default)s)")
    parser.add_argument("--json", type=Path, help="write the JSON report here (default: stdout)")
    parser.add_argument("--markdown", type=Path, help="write the Markdown table here")
    parser.add_argument("--timed", default="", help="comma list of serial,n8,durability,landing,arc_close: run those suites (machine time)")
    parser.add_argument("--timed-dir", type=Path, default=ROOT / "fixtures-local" / "refactor-measures",
                        help="where timed runs write their JUnit XML (gitignored by default)")
    args = parser.parse_args(argv)
    names = [n for n in args.timed.split(",") if n]
    unknown = [n for n in names if n not in TIMED]
    if unknown:
        parser.error(f"unknown timed run(s): {', '.join(unknown)}")
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short=10", "HEAD"],
                            check=True, capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"],
                                check=True, capture_output=True, text=True).stdout.strip())
    report = {
        "commit": commit + ("+dirty" if dirty else ""),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "computed": computed(args.floor),
        "timed_commands": [f"{n}: {shlex.join(timed_command(n, args.timed_dir / f'{n}.xml'))}" for n in TIMED],
        "timed": run_timed(names, args.timed_dir) if names else None,
        "manual": [{"measure": name, "procedure": how} for name, how in MANUAL],
    }
    text = json.dumps(report, indent=2, sort_keys=False)
    if args.json:
        args.json.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    if args.markdown:
        args.markdown.write_text(markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
