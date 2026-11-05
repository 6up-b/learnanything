"""RO2 landing, second pass (ruling R7): the structural guard on AD's reads of a reading's structure.

* No code reached from AD's operation (the history card's reads, the reading sweep and its listed
  sources, dose) calls a raw document loader: the IR comes from ``MaterialView.document_ir`` only, after
  the sweep's withheld rule. The raw-loading versions stay as thin wrappers for callers outside AD.
* A guard denial on any AD read inside the serve leaves the learner's serve unchanged: the same step and
  presentation, and no AD row of that serve (as before the fix).

The reproduction itself (a span-anchored Reader question on the textbook fake) is
``tests/test_ro2_ad_document_ir.py``. Fakes only; no model call.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from tests.ad_fakes import rows

SRC = Path(__file__).resolve().parents[1] / "src"
#: The modules AD's operation reaches for a reading's structure; the walk follows their calls into every
#: learnloop function it can resolve (module functions, imported names, ``self`` methods, classes' __init__).
ROOTS = frozenset({
    "learnloop/adaptive_difficulty/history_card.py",
    "learnloop/adaptive_difficulty/reading.py",
    "learnloop/reading_sources.py",
    "learnloop/adaptive_difficulty/dose.py",
})
#: Raw loaders of a reading's stored structure (each reads ``source_document_*`` outside the chokepoint).
RAW_LOADERS = frozenset({"load_document_ir", "document_blocks", "document_blocks_on_pages"})
#: The one place AD may load it: the reading chokepoint (inside Scope.DERIVE, after the withheld rule).
CHOKEPOINT = ("learnloop/adaptive_difficulty/material_view.py", "MaterialView.document_ir")
#: Calls whose receiver, when reached from AD, is the operation's ProjectedRepository (its
#: ``load_document_ir`` is the chokepoint): each with why. The runtime test below checks it.
PROJECTED_ONLY: dict[tuple[str, str], str] = {
    ("learnloop/content/sources/span_aliases.py", "_computed"):
        "the span translator's re-read aliases: VaultReadingMap hands the section mapping "
        "project_repository(...), so its SpanTranslator loads both readings through the view",
}


class _Index:
    """Every function and method of ``src/learnloop`` by module, with each module's import names."""

    def __init__(self) -> None:
        self.functions: dict[tuple[str, str], ast.AST] = {}
        self.imports: dict[str, dict[str, tuple[str, str]]] = {}
        self.modules: dict[str, str] = {}
        for path in sorted(SRC.rglob("*.py")):
            rel = str(path.relative_to(SRC))
            self.modules[rel[:-3].replace("/", ".").removesuffix(".__init__")] = rel
        for rel in self.modules.values():
            tree = ast.parse((SRC / rel).read_text(encoding="utf-8"))
            names: dict[str, tuple[str, str]] = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    for alias in node.names:
                        names[alias.asname or alias.name] = (node.module, alias.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        names[alias.asname or alias.name.split(".")[0]] = (alias.name, "")
            self.imports[rel] = names
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.functions[(rel, node.name)] = node
                elif isinstance(node, ast.ClassDef):
                    for member in node.body:
                        if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            self.functions[(rel, f"{node.name}.{member.name}")] = member

    def resolve(self, rel: str, owner: str | None, call: ast.Call) -> list[tuple[str, str]]:
        func = call.func
        found: list[tuple[str, str]] = []
        if isinstance(func, ast.Name):
            if (rel, func.id) in self.functions:
                found.append((rel, func.id))
            elif func.id in self.imports[rel]:
                module, name = self.imports[rel][func.id]
                target = self.modules.get(module)
                if target and (target, name) in self.functions:
                    found.append((target, name))
                elif target:  # a class: its methods are reached through its instances, so take them all
                    found += [key for key in self.functions if key[0] == target and key[1].startswith(f"{name}.")]
        elif isinstance(func, ast.Attribute):
            base = func.value
            if isinstance(base, ast.Name) and base.id == "self" and owner:
                if (rel, f"{owner}.{func.attr}") in self.functions:
                    found.append((rel, f"{owner}.{func.attr}"))
            elif isinstance(base, ast.Name) and base.id in self.imports[rel]:
                module, name = self.imports[rel][base.id]
                target = self.modules.get(f"{module}.{name}" if name else module)
                if target and (target, func.attr) in self.functions:
                    found.append((target, func.attr))
        return found


def _reachable_raw_loads() -> tuple[set[tuple[str, str]], list[str]]:
    index = _Index()
    pending = [key for key in index.functions if key[0] in ROOTS]
    seen: set[tuple[str, str]] = set()
    raw: list[str] = []
    while pending:
        key = pending.pop()
        if key in seen or key == CHOKEPOINT:
            continue
        seen.add(key)
        rel, qualified = key
        owner = qualified.split(".")[0] if "." in qualified else None
        for node in ast.walk(index.functions[key]):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute) and node.func.attr in RAW_LOADERS and key not in PROJECTED_ONLY:
                raw.append(f"{rel}:{node.lineno} {qualified} calls .{node.func.attr}()")
            pending += [target for target in index.resolve(rel, owner, node) if target not in seen]
    return seen, raw


def test_no_code_reached_from_ads_operation_calls_a_raw_document_loader():
    """Fails before the fix: VaultReadingMap.los_for_span and los_for_section reached
    section_map.section_id_for_span and learning_objects_for_section, each calling
    repository.load_document_ir."""

    seen, raw = _reachable_raw_loads()
    # The walk does reach the mapping helpers, so a raw call there would be seen.
    assert ("learnloop/adaptive_difficulty/reading.py", "VaultReadingMap.los_for_span") in seen
    assert ("learnloop/adaptive_difficulty/reading.py", "VaultReadingMap.los_for_section") in seen
    assert ("learnloop/section_map.py", "learning_objects_for_section_in_ir") in seen
    assert raw == [], raw
    assert set(PROJECTED_ONLY) <= seen, sorted(set(PROJECTED_ONLY) - seen)  # no stale entry


def test_at_run_time_ad_loads_a_reading_only_through_its_chokepoint(tmp_path, monkeypatch):
    """The same rule observed: on the span-anchored textbook fake, the history card, the reading map's
    span and section mapping and a whole serve record (its sweep included) load every document IR
    inside ``MaterialView.document_ir``; none raw. A ProjectedRepository's loader counts as the view's."""

    from contextlib import closing

    from learnloop.adaptive_difficulty import history_card as HC
    from learnloop.adaptive_difficulty.material_view import MaterialView
    from learnloop.adaptive_difficulty.operation import ad_operation
    from learnloop.adaptive_difficulty.reading import VaultReadingMap
    from learnloop.adaptive_difficulty.serve import record_plan_serve
    from learnloop.db.connection import connect
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from tests.test_ro2_ad_document_ir import SERVED, _textbook_with_span_question

    inside = {"depth": 0}
    loads: list[bool] = []
    raw_load = Repository.load_document_ir
    chokepoint = MaterialView.document_ir

    def counted_load(self, extraction_id):
        loads.append(inside["depth"] > 0)
        return raw_load(self, extraction_id)

    def counted_chokepoint(self, repository, extraction_id):
        inside["depth"] += 1
        try:
            return chokepoint(self, repository, extraction_id)
        finally:
            inside["depth"] -= 1

    paths, repository, extraction, span, unit = _textbook_with_span_question(tmp_path, "mvp-0.46")
    import sqlite3

    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
                           "VALUES ('blk', 'practice', 10, 'hash', ?)", (SERVED,))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
                           "VALUES ('pp_1', 'blk', 'pi_eigen_2', 'chooser', ?)", (SERVED,))
    monkeypatch.setattr(Repository, "load_document_ir", counted_load)
    monkeypatch.setattr(MaterialView, "document_ir", counted_chokepoint)
    vault = load_vault(paths.root)
    with ad_operation(vault, repository, read_only=True) as op:
        mapping = VaultReadingMap(op.vault, repository, op.view)
        assert mapping.los_for_span(extraction, span) == ["lo_matrices"]
        assert mapping.los_for_section(extraction, unit) == ["lo_matrices"]
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            HC.build_sections(op.vault, connection, op.view.item("pi_eigen_1"), served_at=SERVED, view=op.view)
    with repository.atomic():
        record = record_plan_serve(vault, repository, presentation_id="pp_1", practice_item_id="pi_eigen_2",
                                   served_at=SERVED)
    assert record.skipped is None
    assert loads and all(loads), loads


def test_the_raw_loading_wrappers_stay_for_callers_outside_ad():
    """The incumbent's callers keep their signatures: the raw-loading versions are thin wrappers over the
    IR-taking ones."""

    from learnloop import section_map

    tree = ast.parse(Path(section_map.__file__).read_text(encoding="utf-8"))
    functions = {node.name: ast.unparse(node) for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "section_id_in_ir(" in functions["section_id_for_span"]
    assert "learning_objects_for_section_in_ir(" in functions["learning_objects_for_section"]
    assert "load_document_ir" not in functions["section_id_in_ir"]
    assert "load_document_ir" not in functions["learning_objects_for_section_in_ir"]


def test_a_guard_denial_in_ads_serve_leaves_the_learners_serve_unchanged(tmp_path, monkeypatch):
    """Any AD read the guard refuses poisons AD's operation and rolls back AD's writes of the serve, never the
    serve itself: the same step, the same presentation row, and no AD row of that serve."""

    import learnloop.adaptive_difficulty.serve as ad_serve
    from learnloop.daily_plan.engine import advance, build_plan
    from tests.ad_fakes import ad_plan_vault, plan_env

    original = ad_serve.freeze_history_inputs

    def refused(vault, connection, item, **kwargs):
        connection.execute("SELECT * FROM grading_evidence LIMIT 1").fetchall()  # DENIED to AD
        return original(vault, connection, item, **kwargs)

    def serve(root, *, deny: bool):
        paths = ad_plan_vault(root)
        if deny:
            monkeypatch.setattr(ad_serve, "freeze_history_inputs", refused)
        env, _clock = plan_env(paths)
        build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
        _record, step = advance(env, serve=True)
        monkeypatch.undo()
        presented = rows(paths.sqlite_path, "SELECT practice_item_id, origin, served_at FROM plan_presentations")
        ad_rows = {table: len(rows(paths.sqlite_path, f"SELECT * FROM {table}"))
                   for table in ("forecast_receipts", "item_serve_inputs", "ad_history_forecast_draws")}
        return step, presented, ad_rows

    step, presented, ad_rows = serve(tmp_path / "ok", deny=False)
    denied_step, denied_presented, denied_rows = serve(tmp_path / "denied", deny=True)

    def strip(value):
        return json.dumps({k: v for k, v in value.items() if k not in ("presentation_id", "block_id", "plan_id")},
                          sort_keys=True, default=str)

    assert strip(denied_step) == strip(step) and denied_presented == presented
    assert ad_rows["forecast_receipts"] > 0 and ad_rows["ad_history_forecast_draws"] == 1
    assert denied_rows == {"forecast_receipts": 0, "item_serve_inputs": 0, "ad_history_forecast_draws": 0}
