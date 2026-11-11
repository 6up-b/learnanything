"""T1 before/after measure: selector reach for a fixed module sample, every src module's depth-1 cost,
and the test-file -> test-file import count. Usage: t1_measure.py <ids file> <junit xml> <out json>"""

from __future__ import annotations

import ast
import importlib.util
import json
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path.cwd()
spec = importlib.util.spec_from_file_location("affected_tests_t1", ROOT / "scripts/affected_tests.py")
AT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AT)

SAMPLE = [
    "src/learnloop/router/mixture.py",
    "src/learnloop/daily_plan/engine.py",
    "src/learnloop/figures/prefetch.py",
    "src/learnloop/attempts/grading.py",
    "src/learnloop/diagnosis/followups.py",
    "src/learnloop/db/stores/daily_plans.py",
    "src/learnloop_sidecar/handlers/daily_plan.py",
    "src/learnloop_mobile/host.py",
    "src/learnloop/reader/reader_dialogue.py",
    "src/learnloop/teacher/service.py",
    "src/learnloop/provenance.py",
    "src/learnloop/ingest/resolution.py",
]

ids_path, junit_path, out_path = map(Path, sys.argv[1:4])
ids_per_file = Counter(line.split("::", 1)[0] for line in ids_path.read_text().splitlines() if "::" in line)
seconds = defaultdict(float)
for case in ET.parse(junit_path).iter("testcase"):
    cls = case.get("classname") or ""
    parts = cls.split(".")
    # classname is tests.test_x or tests.test_x.TestClass
    if len(parts) >= 2:
        seconds[f"{parts[0]}/{parts[1]}.py"] += float(case.get("time") or 0)

graph = AT.Graph()


def cost(tests):
    return (len(tests), sum(ids_per_file.get(t, 0) for t in tests), round(sum(seconds.get(t, 0) for t in tests), 1))


rows = []
for path in SAMPLE:
    res = AT.select([path], graph, depth=1)
    assert res["mode"] == "selected", (path, res["reasons"])
    rows.append([path, *cost(res["tests"])])

# Every src module's depth-1 selection (as refactor-a6's sweep), skipping full-suite fallbacks.
all_costs = []
for p in graph.files:
    if not p.startswith("src/"):
        continue
    res = AT.select([p], graph, depth=1)
    if res["mode"] != "selected":
        continue
    all_costs.append(cost(res["tests"]))


def pct(values, q):
    values = sorted(values)
    return values[min(len(values) - 1, int(q * len(values)))]


summary = {}
for k, label in enumerate(("files", "test_ids", "seconds")):
    vals = [c[k] for c in all_costs]
    summary[label] = {"median": statistics.median(vals), "p75": pct(vals, 0.75), "p90": pct(vals, 0.9)}
summary["modules"] = len(all_costs)

# Test-to-test imports (any tests/*.py importing from a tests/test_*.py).
pairs, names = set(), 0
fanin = defaultdict(set)
for path in sorted((ROOT / "tests").glob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        mods = []
        if isinstance(node, ast.ImportFrom) and node.level == 0 and (node.module or "").startswith("tests.test_"):
            mods = [(node.module, len(node.names))]
        elif isinstance(node, ast.Import):
            mods = [(a.name, 1) for a in node.names if a.name.startswith("tests.test_")]
        for mod, n in mods:
            pairs.add((path.stem, mod))
            names += n
            fanin[mod].add(path.stem)
top = sorted(((len(v), k) for k, v in fanin.items()), reverse=True)[:10]
out = {"sample": rows, "all_src_depth1": summary, "test_to_test": {"module_pairs": len(pairs), "names": names,
                                                                    "top_fanin": top}}
out_path.write_text(json.dumps(out, indent=1))
print("| module | test files | test ids | test s |")
for r in rows:
    print(f"| `{r[0].removeprefix('src/')}` | {r[1]} | {r[2]} | {r[3]} |")
print(json.dumps(summary))
print("test->test module pairs", len(pairs), "names", names, "top", top[:5])
