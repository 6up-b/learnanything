"""What other test files use from ``tests/test_figures_prefetch.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from learnloop.figures import power as P
from learnloop.figures import prefetch as PF
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.vault.loader import load_vault

from tests.figure_fixtures import (
    EXTRACTION,
    AuthorFake,
    _Recording,
    build_figure_vault,
    rows,
    set_config,
    upsert_source_set,
)
from tests.source_inventory_helpers import _persist


TWO = "ext_two"


class JudgeFake(_Recording):
    """``figure_prefetch_judge``: answers from a queue (a dict, a callable of the context, or an exception);
    empty, the section's first equation block (p_open 0.8) or a gap goal (p_open 0.6)."""

    def __init__(self, answers: list[Any] | None = None, *, provider_type: str = "chatgpt_plan") -> None:
        super().__init__(provider_type=provider_type)
        self.answers = list(answers or [])

    def complete(self, request: Any) -> Any:
        assert request.purpose == "figure_prefetch_judge"
        context = self._record(request)
        answer = self.answers.pop(0) if self.answers else None
        if callable(answer):
            answer = answer(context)
        if isinstance(answer, BaseException):
            raise answer
        if answer is None:
            if context["mode"] == "section":
                ids = [block["id"] for block in context["blocks"] if block["type"] == "Equation"]
                answer = {"blocks": [{"block": ids[0], "goal": "", "p_open": 0.8}]}
            else:
                answer = {"goal": "slide p and watch the mass left of zero move", "p_open": 0.6}
        return request.result_model.model_validate(answer)


@pytest.fixture(autouse=True)
def mains():
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    yield
    P.set_power_reader(None)


def seed_two_sections(paths: Any, repository: Any) -> None:
    """A second book with two sections (s1, s2), each a header, a paragraph and an equation."""

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, current_revision_id, "
            "reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            ("src_two", "pdf", "file:///src_two.pdf", "Two Sections", "rev_two", 1,
             "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_two", "src_two", "sha256:src_two", None, "2026-01-01T00:00:00Z"))
        connection.commit()
    spec = (("q1", "SectionHeader", "1 Waves"), ("q2", "Text", "A wave moves with speed v = f lambda."),
            ("q3", "Equation", "v = f \\lambda"), ("q4", "SectionHeader", "2 Damping"),
            ("q5", "Text", "Damping shrinks the amplitude by e^{-gamma t}."), ("q6", "Equation", "A(t) = A_0 e^{-\\gamma t}"))
    blocks = [DocumentBlock.build(span_id=span, block_type=kind, text=text, ordinal=ordinal, page=1,
                                  bbox=[72.0, 40.0 * ordinal, 540.0, 40.0 * ordinal + 30],
                                  section_path=["/page/1/SectionHeader/1"],
                                  extractor_block_id=f"/page/1/{kind}/{ordinal}")
              for ordinal, (span, kind, text) in enumerate(spec, start=1)]
    units = [DocumentUnit(unit_id="s1", label="1 Waves", ordinal=0, semantic_hash="sha256:s1", page_start=1,
                          page_end=1, span_ids=["q1", "q2", "q3"]),
             DocumentUnit(unit_id="s2", label="2 Damping", ordinal=1, semantic_hash="sha256:s2", page_start=1,
                          page_end=1, span_ids=["q4", "q5", "q6"])]
    ir = DocumentIR(extractor="marker", extractor_version="1", units=units, blocks=blocks, assets=[],
                    health=ExtractionHealth())
    _persist(repository, ir, revision_id="rev_two", extraction_id=TWO)
    upsert_source_set(paths.root, {
        "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
        "members": [
            {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
            {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
            {"source_id": "src_text", "revision_id": "rev_text", "default_role": "primary_textbook"},
            {"source_id": "src_prob", "revision_id": "rev_prob", "default_role": "primary_textbook"},
            {"source_id": "src_two", "revision_id": "rev_two", "default_role": "primary_textbook"},
        ],
    })


def seed_wait(repository: Any, *, seconds: float = 40.0) -> None:
    """A measured pressed author call (the quick tiers' wait), so a prebuild has a W."""

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO model_call_receipts (id, owner_kind, owner_id, purpose, provider, status, started_at, "
            "finished_at) VALUES (?, 'sidecar_rpc', 'figure.request:x', 'figure_author', 'fake_figures', 'completed', "
            "?, ?)", ("mcr_wait", "2026-10-01T10:00:00+00:00",
                      f"2026-10-01T10:00:{int(seconds):02d}+00:00" if seconds < 60 else "2026-10-01T10:01:00+00:00"))
        connection.commit()


def make_vault(tmp_path: Path, *, on: bool = True, wait: bool = True, two: bool = False, **prefetch: Any):
    paths, repository = build_figure_vault(tmp_path / "vault")
    set_config(paths, "figures", prefetch_enabled=on)
    if prefetch:
        set_config(paths, "figures.prefetch", **prefetch)
    if two:
        seed_two_sections(paths, repository)
    if wait:
        seed_wait(repository)
    return paths, repository, load_vault(paths.root)


def switch(paths: Any, on: bool) -> None:
    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    config.write_text(text.replace(f"prefetch_enabled = {'false' if on else 'true'}",
                                   f"prefetch_enabled = {'true' if on else 'false'}"), encoding="utf-8")


def env_for(vault: Any, repository: Any, *, judge: Any = None, author: Any = None, seed: int = 0,
            **kwargs: Any) -> PF.PrefetchEnv:
    defaults: dict[str, Any] = {"pause_reader": lambda: None, "foreground_wait_seconds": 0.0}
    defaults.update(kwargs)
    return PF.PrefetchEnv(vault=vault, repository=repository, judge_client=judge if judge is not None else JudgeFake(),
                          author_client=author if author is not None else AuthorFake(),
                          rng=np.random.default_rng(seed), **defaults)


def plan_record(monkeypatch: Any, extraction_id: str = EXTRACTION, section_id: str = "u54",
                plan_id: str = "dp_1") -> None:
    block = SimpleNamespace(is_reading=True, withdrawn_path_reading=False,
                            reading_target=SimpleNamespace(extraction_id=extraction_id, section_id=section_id))
    record = SimpleNamespace(id=plan_id, blocks=[block], items=lambda: [])
    monkeypatch.setattr(PF, "_plan_record", lambda env, ref: record if ref in (None, plan_id) else None)


def count(repository: Any, table: str) -> int:
    with repository.connection() as connection:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def decisions(repository: Any) -> list[dict[str, Any]]:
    return rows(repository, "figure_prefetch_decisions")
