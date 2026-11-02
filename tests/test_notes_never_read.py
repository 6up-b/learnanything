"""Curriculum C2: a note is never a source, a generation input or evidence
(spec_deliverable_curriculum_v1 §9.3, §10.2, §12.3).

* Statically: the only code that names the notes' tables or modules is the notes'
  own (the vault notes search, the store, the linking service, the sidecar handler, the
  report's CLI) and the two registries that classify the tables (rebuild roles, AD's guard,
  which refuses them). So ``find_sources``, ``teaching_scope``, PF generation, the
  blind grader (S1), the tutor and teach-back (the teacher's item minting is not
  built; TE1 will live beside them) and adaptive difficulty never read
  ``learner_notes`` or ``learner_note_links``.
* By the import graph: none of those modules reaches the notes' modules, directly or
  through any chain (the sidecar handler and the CLI are the only importers).
* Dynamically: with a sentinel note linked, the coverage judge, the scope resolver and
  the path judge (C0a/C0b's model calls) never see its text.

Curriculum C5 (spec §10.2, §12 C5) adds the one declared exception: with the learner's
opt-in (``notes.gaps_enabled``, default off) a LINKED note is a tier-2 learner-text-gaps
input, read through ``source_retrieval.note_gaps`` (notes code, read-only) by the gap
pipeline's adapter ``diagnosis.text_gaps.sources`` alone. That exception is pinned
statically here (no other module of the packages below imports ``note_gaps``) and, since
``text_gaps`` became a regular package (followups batch 5, I; before, grimp did not graph
it), in the import graph: that one edge exists, and with it set aside nothing below reaches
the notes' code (tests/test_notes_as_learner_text.py covers what the reading may write: gap
rows only, never evidence).
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
NAMES = re.compile(r"\b(learner_notes|learner_note_links|note_links|vault_notes)\b")
#: Every source file that may name the notes' tables or modules, and why.
ALLOWED = {
    "src/learnloop/source_retrieval/vault_notes.py": "C2b: the vault's own notes (search, read, embedding)",
    "src/learnloop/db/stores/learner_notes.py": "the tables' store",
    "src/learnloop/source_retrieval/note_links.py": "the linking service (display and learner-voice records)",
    "src/learnloop/source_retrieval/note_gaps.py": "curriculum C5: the gap pipeline's read-only way to linked notes",
    "src/learnloop_sidecar/handlers/notes.py": "the notes RPCs",
    "src/learnloop/cli/curriculum.py": "the report's notes row (aggregates only)",
    "src/learnloop/db/table_roles.py": "rebuild roles (RAW_LEDGER)",
    "src/learnloop/adaptive_difficulty/protected_tables.py": "AD's guard: classified so an AD read is refused",
    "src/learnloop/adaptive_difficulty/column_classes.py": "AD's guard: every column classified",
    "src/learnloop/teacher/notes.py": "curriculum C4: the lesson's notes headers and read_note (the teacher's one door)",
}
#: Teacher TE1 + curriculum C4 (spec §8.2, §10.4): the teacher reads note text through read_note, and the
#: brief lists the headers, through teacher.notes only; the service injects it, the read action calls it.
TEACHER_NOTE_READERS = ("learnloop.teacher.notes", "learnloop.teacher.actions", "learnloop.teacher.service",
                        # Reader RW5d P5: the prefetch service reads a lesson's stored plan through
                        # teacher.service.load_state (the plan nodes and their delivered passages; never a
                        # note); it reaches the notes modules only through that module.
                        "learnloop.figures.prefetch")
#: The modules that must never read a note (spec §10.2's list).
NEVER = (
    "learnloop.source_retrieval.find_sources",
    "learnloop.source_retrieval.corpus",       # teaching_scope
    "learnloop.ops.pf_generation",             # PF generation
    "learnloop.ops.pf_calls",
    "learnloop.attempts",                      # the blind grader (S1), evidence
    "learnloop.tutor",                         # the tutor and teach-back
    "learnloop.teacher.checks",                # teacher item minting (TE1): never a generation input
    "learnloop.teacher.brief",                 # the brief takes the notes by injection only
    "learnloop.teacher.guards",
    "learnloop.teacher.delayed",
    "learnloop.teacher.contracts",
    "learnloop.adaptive_difficulty",
    "learnloop.diagnosis",
    "learnloop.scheduling",
    "learnloop.substrate",                     # replay and projections
    "learnloop.learner",
    "learnloop.goals",
    "learnloop.hints",
    "learnloop.daily_plan",
)
NOTES_MODULES = ("learnloop.source_retrieval.note_links", "learnloop.source_retrieval.vault_notes",
                 "learnloop.db.stores.learner_notes", "learnloop.source_retrieval.note_gaps")
#: Curriculum C5's one declared exception: the only source files outside the sidecar and the
#: CLI that import ``note_gaps`` (the gap pipeline's adapter, lazily, behind the opt-in).
NOTE_GAPS_IMPORTERS = {"src/learnloop/diagnosis/text_gaps/sources.py"}
_IMPORTS_NOTE_GAPS = re.compile(r"(from\s+learnloop\.source_retrieval\s+import\s+[^\n]*\bnote_gaps\b"
                                r"|learnloop\.source_retrieval\.note_gaps\b)")


def test_only_the_notes_own_code_names_their_tables_or_modules():
    found = set()
    for path in sorted((ROOT / "src").rglob("*.py")):
        if NAMES.search(path.read_text(encoding="utf-8")):
            found.add(path.relative_to(ROOT).as_posix())
    assert found <= set(ALLOWED), sorted(found - set(ALLOWED))
    assert {"src/learnloop/source_retrieval/note_links.py", "src/learnloop/db/stores/learner_notes.py",
            "src/learnloop_sidecar/handlers/notes.py"} <= found


def test_c5s_one_exception_only_the_gap_pipelines_adapter_imports_note_gaps():
    found = set()
    for path in sorted((ROOT / "src").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith(("src/learnloop_sidecar/", "src/learnloop/cli/")) or relative in ALLOWED:
            continue
        if _IMPORTS_NOTE_GAPS.search(path.read_text(encoding="utf-8")):
            found.add(relative)
    assert found == NOTE_GAPS_IMPORTERS, sorted(found)
    # The adapter reaches it only behind the opt-in (the config is read first).
    sources = (ROOT / "src/learnloop/diagnosis/text_gaps/sources.py").read_text(encoding="utf-8")
    enabled = sources[sources.index("def learner_notes_enabled"):sources.index("def learner_note_ids")]
    assert enabled.index("gaps_enabled") < enabled.index("import note_gaps")
    # No text_gaps module other than the adapter names the notes' modules or tables.
    for path in sorted((ROOT / "src/learnloop/diagnosis/text_gaps").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert not NAMES.search(text), path.name
        if path.name != "sources.py":
            assert "note_gaps" not in text, path.name


#: Curriculum C5's declared edge (also the import-linter contracts' one ignore for it).
C5_EDGE = {"importer": "learnloop.diagnosis.text_gaps.sources", "imported": "learnloop.source_retrieval.note_gaps"}


def test_no_generation_grading_evidence_or_ad_module_reaches_the_notes_modules():
    graph = grimp.build_graph("learnloop", "learnloop_sidecar")
    # C5's one exception, graphed now that text_gaps is a regular package: it exists, and it is the only
    # way any module below reaches the notes' code (set aside, the checks are C2's as before).
    assert graph.direct_import_exists(**C5_EDGE)
    graph.remove_import(**C5_EDGE)
    importers = set()
    for module in NOTES_MODULES:
        importers |= {name for name in graph.find_downstream_modules(module) if not name.startswith(NOTES_MODULES)}
    # The only modules that reach the notes' code: the sidecar (its notes handler) and the CLI.
    allowed = ("learnloop_sidecar", "learnloop.cli", "learnloop.__main__", *TEACHER_NOTE_READERS)
    assert all(name.startswith(allowed) for name in importers), (
        sorted(name for name in importers if not name.startswith(allowed)))
    for package in NEVER:
        members = {package} | (graph.find_descendants(package) if graph.find_children(package) else set())
        for member in members:
            for target in NOTES_MODULES:
                assert graph.find_shortest_chain(importer=member, imported=target) is None, (member, target)


def test_a_linked_sentinel_note_never_reaches_coverage_scope_or_path_judges(tmp_path):
    from tests.test_notes_linked import _deliverable, _lines

    coverage = CoverageJudgeFake()
    deliverable = DeliverableFake(primaries={"Eigenvalues": "Chapter 5 Eigenvalues"})
    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path)
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
    assert SENTINEL not in sources
    assert vault.config.notes.enabled


def test_the_tend_adapter_is_gone():
    """C2b: the tend adapter, its config and its test scaffolding are removed; nothing in the
    source, the tests' fixtures or the desktop app runs or names it (the word ``tend`` is
    allowed only in history notes about C2's era)."""

    pattern = re.compile(r"notes_tend|NOTES_TEND|notes\.tend|NotesTendConfig|install_fake_tend|FakeTend|TendSettings"
                         r"|TendUnavailable|tend_settings|tend_unavailable")
    roots = [ROOT / "src", ROOT / "apps/learnloop-tauri/src", ROOT / "apps/learnloop-tauri/src-tauri/src"]
    found = []
    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.suffix not in {".py", ".ts", ".tsx", ".rs"} or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                found.append(f"{path.relative_to(ROOT)}:{line}:{match.group(0)}")
    # The config's legacy-key tolerance names the table it ignores.
    allowed = {"src/learnloop/config/schema.py"}
    assert [entry for entry in found if entry.split(":", 1)[0] not in allowed] == []
    assert not (ROOT / "src/learnloop/curriculum/notes_tend.py").exists()
    for test in sorted((ROOT / "tests").glob("*.py")):
        if test.name == "test_notes_never_read.py":
            continue
        text = test.read_text(encoding="utf-8")
        assert "install_fake_tend" not in text and "LEARNLOOP_NOTES_TEND" not in text, test.name
