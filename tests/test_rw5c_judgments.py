"""Reader RW5c (Codex review F6, G23i): every check is a verdict, committed with its row."""

from __future__ import annotations

from typing import Any

import pytest

from learnloop.db.stores import figures as store
from learnloop.figures import source_check as SC
from learnloop.figures import spec as S
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import AuthorFake, build, context, rows
from tests.rw5c_fixtures import EXTRACTION, build_check_vault, plot

BOOK = [("s5", "Text", "$f(x)=x$")]


@pytest.fixture
def stored(tmp_path) -> tuple[Any, Any, dict[str, Any]]:
    paths, repository = build_check_vault(tmp_path / "vault", BOOK)
    ctx = context(paths.root, author=AuthorFake([plot("x")]))
    build(ctx, {"extractionId": EXTRACTION, "spanIds": ["s5"]})
    return paths, repository, rows(repository, "interactive_figures")[0]


def _verdicts(repository: Any) -> list[dict[str, Any]]:
    return [row for row in rows(repository, "judgment_ledger") if row["task"] == SC.LEDGER_TASK]


def test_a_build_commits_one_row_with_one_verifier_verdict(stored):
    _paths, repository, figure = stored
    checks, verdicts = rows(repository, "figure_source_checks"), _verdicts(repository)
    assert len(checks) == len(verdicts) == 1
    check, verdict = checks[0], verdicts[0]
    assert check["judgment_id"] == verdict["id"] and check["trigger"] == "build" and check["figure_id"] == figure["id"]
    assert verdict["judge"] == "verifier" and verdict["left_kind"] == "interactive_figure"
    assert verdict["left_id"] == figure["id"] and verdict["right_kind"] is None and verdict["judge_model"] is None
    assert verdict["prompt_version"] is None and verdict["supersedes_id"] is None
    assert verdict["verdict"] == check["outcome"] and len(verdict["input_hash"]) == 64
    assert len(verdict["rationale"]) <= 400
    assert "f:" in verdict["rationale"]
    # The build's figure_verified verdict is unchanged, and keeps recording steps 1-2.
    built = [row for row in rows(repository, "judgment_ledger") if row["task"] == "figure_verified"]
    assert [row["verdict"] for row in built] == ["illustrative"]


def test_a_recheck_supersedes_the_previous_verdict_of_the_same_figure(stored):
    paths, repository, figure = stored
    vault = load_vault(paths.root)
    full = store.figure(repository.connection(), figure["id"])
    SC.recheck(vault, repository, full)
    SC.recheck(vault, repository, full)
    with repository.connection() as connection:
        ordered = [dict(row) for row in connection.execute(
            "SELECT id, supersedes_id FROM judgment_ledger WHERE task = ? ORDER BY rowid", (SC.LEDGER_TASK,))]
    assert len(ordered) == 3 and ordered[0]["supersedes_id"] is None
    assert [row["supersedes_id"] for row in ordered[1:]] == [ordered[0]["id"], ordered[1]["id"]]
    assert [row["trigger"] for row in rows(repository, "figure_source_checks")].count("recheck") == 2


def test_a_failure_between_the_two_inserts_leaves_neither(stored, monkeypatch):
    paths, repository, figure = stored
    vault = load_vault(paths.root)
    full = store.figure(repository.connection(), figure["id"])

    def boom(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("the disk is gone")

    monkeypatch.setattr(store, "insert_source_check", boom)
    with pytest.raises(RuntimeError):
        SC.recheck(vault, repository, full)
    assert len(rows(repository, "figure_source_checks")) == 1 and len(_verdicts(repository)) == 1


def test_at_build_a_failure_leaves_no_figure_row_and_no_verdict(tmp_path, monkeypatch):
    paths, repository = build_check_vault(tmp_path / "vault", BOOK)
    from learnloop.figures import service as FS

    def boom(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("the disk is gone")

    monkeypatch.setattr(store, "insert_source_check", boom)
    with pytest.raises(RuntimeError):
        FS.build_figure(load_vault(paths.root), repository, FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["s5"]),
                        author_client=AuthorFake([plot("x")]))
    assert rows(repository, "interactive_figures") == [] and _verdicts(repository) == []


def test_the_rationale_is_code_text_only():
    compiled = S.parse_spec(plot("x", label="the model's own words", demonstrates="more model words"))
    check = SC._finished(compiled, [{"name": "f", "outcome": "differs", "reason": "differs",
                                     "witness": {"kind": "value", "at": {"x": "1/2"}}}], [], {"differs": 1}, SC.DIFFERS, "")
    assert check.rationale == "f: differs (differs) at x=1/2"
    assert "model" not in check.rationale
