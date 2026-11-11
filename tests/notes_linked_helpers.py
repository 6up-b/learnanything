"""What other test files use from ``tests/test_notes_linked.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from pathlib import Path

from learnloop.source_retrieval import note_links as NL
from learnloop.vault.loader import load_vault

from tests.deliverable_fixtures import DeliverableFake, build_deliverable_vault
from tests.notes_fixtures import NoteLinkFake, eigen_notes
from tests.reading_path_fixtures import call, context
from tests.section_coverage_fixtures import CoverageJudgeFake


def _ctx(paths, **attrs):
    fake = attrs.pop("fake", None) or DeliverableFake(primaries={"Eigenvalues": "Chapter 5 Eigenvalues"})
    return context(paths.root, deliverable_inline=True, notes_inline=True, coverage_judge_client=CoverageJudgeFake(),
                   deliverable_scope_client=fake, deliverable_path_client=fake, **attrs)


def _deliverable(tmp_path: Path, *, config: str = "", notes: NoteLinkFake | None = None):
    """A deliverable vault with a judged path for lo_eigen (primary ch_eigen in ext_book),
    the synthetic vault notes, and the sidecar context."""

    paths, repository = build_deliverable_vault(tmp_path / "vault", config=config)
    corpus = eigen_notes(repository)
    notes = notes or NoteLinkFake()
    ctx = _ctx(paths, note_link_client=notes)
    created = call(ctx, "curriculum.create_deliverable", {"sentence": "eigenvalues for my midterm"})
    goal_id = created["goalId"]
    view = call(ctx, "curriculum.set_depth", {"goal_id": goal_id, "depth": "learn_to_use_it"})
    assert view["status"] == "ready"
    return paths, repository, ctx, goal_id, corpus, notes


def _lines(out, lo: str = "lo_eigen") -> list:
    return next((entry["notes"] for entry in out["lines"] if entry["learningObjectId"] == lo), [])


def _target(paths, repository, goal_id):
    vault = load_vault(paths.root)
    return vault, NL.path_targets(vault, repository, goal_id)[0]


def _link_typed_by_hand(ctx, corpus):
    return call(ctx, "notes.link", {"note": {"note_key": corpus["typed"]}, "extraction_id": "ext_book",
                                    "span_id": "s2"})


class _Published:
    """A loaded-vault provider shaped as the sidecar's (``snapshot()`` and a
    generation-bound ``admit``): ``publish`` is a settings reload."""

    def __init__(self, vault):
        self.vault, self.generation = vault, 1

    def publish(self, vault):
        self.vault, self.generation = vault, self.generation + 1

    def __call__(self):
        return self.vault

    def snapshot(self):
        return self.vault, self.generation

    def admit(self, generation):
        return generation == self.generation
