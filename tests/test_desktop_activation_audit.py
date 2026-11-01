"""Every desktop source carries positive activation evidence (follow-ups Oct 31).

The architecture vault's desktop catalog generator refuses a frontend file it
cannot classify (no path from the Vite entry, no compiler inclusion, no vitest
import): a missing caller is never taken as proof of dormancy. That refusal
went unnoticed for weeks because nothing ran the generator, so the whole
``desktop_validate.py`` failed on its first line. This runs the same audit
cheaply (no git, no rendering): a new test helper, Worker, or ambient
declaration must get an explicit rule in ``desktop_generate.audit_activation``.

The full catalog check (``desktop_validate.py``) is not run here: its notes pin
each source's last commit, so it goes stale at every frontend commit until the
catalog is regenerated (a docs step, not a test gate).
"""

from __future__ import annotations

import functools
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "docs" / "learnloop-architecture-vault" / "_scripts" / "desktop_generate.py"
KINDS = {"entry-reachable build graph", "compiler-implicit", "vitest-support", "native-entry-reachable"}


@functools.cache
def _generator():
    spec = importlib.util.spec_from_file_location("desktop_generate_for_audit", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their module through sys.modules
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def _audited_infos(generator):
    pairs = generator.source_files()
    source_set = {path.resolve() for path, _ in pairs}
    infos = {}
    for path, language in pairs:
        path = path.resolve()
        infos[path] = generator.SourceInfo(
            source=path, language=language, area=generator.area_for(path, language),
            text=path.read_text(encoding="utf-8"), symbols=[], commit="", commit_timestamp="", worktree_state="",
        )
    rust_by_stem = {path.stem: path for path, info in infos.items() if info.language == "Rust"}
    for info in infos.values():
        if info.language == "TypeScript":
            generator.add_ts_imports(info, source_set)
        else:
            generator.add_rust_imports(info, rust_by_stem)
    generator.audit_activation(infos)  # raises on an unclassified source
    return infos


def test_every_desktop_source_has_activation_evidence():
    generator = _generator()
    infos = _audited_infos(generator)
    assert infos
    unknown = {info.relative: info.activation_kind for info in infos.values() if info.activation_kind not in KINDS}
    assert unknown == {}
    assert {info.refactor_status for info in infos.values()} == {"ACTIVE"}
    assert all(info.activation_evidence for info in infos.values())


def test_every_desktop_area_has_a_stated_responsibility():
    """The catalog's area maps need one line each; a new frontend directory needs one too."""

    generator = _generator()
    areas = {generator.area_for(path.resolve(), language) for path, language in generator.source_files()}
    assert sorted(areas - set(generator.AREA_RESPONSIBILITIES)) == []


def test_test_support_is_never_reached_from_the_app_entry():
    """The vitest-support rule only applies off the build graph: a test helper the app imports is build code."""

    generator = _generator()
    infos = _audited_infos(generator)
    support = [info for info in infos.values() if info.activation_kind == "vitest-support"]
    for info in support:
        assert info.activation_chain, info.relative
        assert all(infos[step].activation_kind == "vitest-support" for step in info.activation_chain), info.relative
