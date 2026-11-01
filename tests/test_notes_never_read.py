"""Curriculum C2: a note is never a source, a generation input or evidence
(spec_deliverable_curriculum_v1 §9.3, §10.2, §12.3).

* Statically: the only code that names the notes' tables or modules is the notes'
  own (the adapter, the store, the linking service, the sidecar handler, the report's
  CLI) and the two registries that classify the tables (rebuild roles, AD's guard,
  which refuses them). So ``find_sources``, ``teaching_scope``, PF generation, the
  blind grader (S1), the tutor and teach-back (the teacher's item minting is not
  built; TE1 will live beside them) and adaptive difficulty never read
  ``learner_notes`` or ``learner_note_links``.
* By the import graph: none of those modules reaches the notes' modules, directly or
  through any chain (the sidecar handler and the CLI are the only importers).
* Dynamically: with a sentinel note linked, the coverage judge, the scope resolver and
  the path judge (C0a/C0b's model calls) never see its text.
"""
from __future__ import annotations

import re
from pathlib import Path

import grimp

from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake
from tests.notes_fixtures import SENTINEL
from tests.reading_path_fixtures import call
from tests.section_coverage_fixtures import CoverageJudgeFake

ROOT = Path(__file__).resolve().parents[1]
NAMES = re.compile(r"\b(learner_notes|learner_note_links|note_links|notes_tend)\b")
#: Every source file that may name the notes' tables or modules, and why.
ALLOWED = {
    "src/learnloop/curriculum/notes_tend.py": "the one tend adapter",
    "src/learnloop/db/stores/learner_notes.py": "the tables' store",
    "src/learnloop/source_retrieval/note_links.py": "the linking service (display and learner-voice records)",
    "src/learnloop_sidecar/handlers/notes.py": "the notes RPCs",
    "src/learnloop/cli/curriculum.py": "the report's notes row (aggregates only)",
    "src/learnloop/db/table_roles.py": "rebuild roles (RAW_LEDGER)",
    "src/learnloop/adaptive_difficulty/protected_tables.py": "AD's guard: classified so an AD read is refused",
    "src/learnloop/adaptive_difficulty/column_classes.py": "AD's guard: every column classified",
}
#: The modules that must never read a note (spec §10.2's list).
NEVER = (
    "learnloop.source_retrieval.find_sources",
    "learnloop.source_retrieval.corpus",       # teaching_scope
    "learnloop.ops.pf_generation",             # PF generation
    "learnloop.ops.pf_calls",
    "learnloop.attempts",                      # the blind grader (S1), evidence
    "learnloop.tutor",                         # the tutor and teach-back (teacher item minting: TE1, not built)
    "learnloop.adaptive_difficulty",
    "learnloop.diagnosis",
    "learnloop.scheduling",
    "learnloop.substrate",                     # replay and projections
    "learnloop.learner",
    "learnloop.goals",
    "learnloop.hints",
    "learnloop.daily_plan",
)
NOTES_MODULES = ("learnloop.source_retrieval.note_links", "learnloop.curriculum.notes_tend",
                 "learnloop.db.stores.learner_notes")


def test_only_the_notes_own_code_names_their_tables_or_modules():
    found = set()
    for path in sorted((ROOT / "src").rglob("*.py")):
        if NAMES.search(path.read_text(encoding="utf-8")):
            found.add(path.relative_to(ROOT).as_posix())
    assert found <= set(ALLOWED), sorted(found - set(ALLOWED))
    assert {"src/learnloop/source_retrieval/note_links.py", "src/learnloop/db/stores/learner_notes.py",
            "src/learnloop_sidecar/handlers/notes.py"} <= found


def test_no_generation_grading_evidence_or_ad_module_reaches_the_notes_modules():
    graph = grimp.build_graph("learnloop", "learnloop_sidecar")
    importers = set()
    for module in NOTES_MODULES:
        importers |= {name for name in graph.find_downstream_modules(module) if not name.startswith(NOTES_MODULES)}
    # The only modules that reach the notes' code: the sidecar (its notes handler) and the CLI.
    assert all(name.startswith(("learnloop_sidecar", "learnloop.cli", "learnloop.__main__")) for name in importers), (
        sorted(name for name in importers if not name.startswith(("learnloop_sidecar", "learnloop.cli"))))
    for package in NEVER:
        members = {package} | (graph.find_descendants(package) if graph.find_children(package) else set())
        for member in members:
            for target in NOTES_MODULES:
                assert graph.find_shortest_chain(importer=member, imported=target) is None, (member, target)


def test_a_linked_sentinel_note_never_reaches_coverage_scope_or_path_judges(tmp_path, monkeypatch):
    from tests.test_notes_linked import _deliverable, _lines

    coverage = CoverageJudgeFake()
    deliverable = DeliverableFake(primaries={"Eigenvalues": "Chapter 5 Eigenvalues"})
    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(tmp_path, monkeypatch)
    ctx.coverage_judge_client = coverage
    ctx.deliverable_scope_client = deliverable
    ctx.deliverable_path_client = deliverable
    linked = _lines(call(ctx, "notes.path", {"goal_id": goal_id}))
    assert any(SENTINEL in line["note"]["text"] for line in linked)  # the sentinel note is linked
    # Every later C0a/C0b call: a new scope input (resolver), its coverage, a re-judged path.
    call(ctx, "curriculum.set_scope", {"goal_id": goal_id, "kind": "text", "text": "and determinants"})
    call(ctx, "curriculum.path", {"goal_id": goal_id})
    call(ctx, "curriculum.set_depth", {"goal_id": goal_id, "depth": "fluency"})
    prompts = [*coverage.prompts, *deliverable.prompts]
    assert prompts, "the later judges ran"
    assert all(SENTINEL not in prompt for prompt in prompts)
    # The vault's sources never include a note (no source artifact is written for one).
    vault = load_vault(paths.root)
    with repository.connection() as connection:
        sources = " ".join(" ".join(str(value) for value in row)
                           for row in connection.execute("SELECT * FROM source_artifacts"))
    assert SENTINEL not in sources and str(fake_tend.notes) not in sources
    assert vault.config.notes.enabled
