"""Reader RW5a final round (orchestrator): the verify's findings that are fixed.

See docs/reviews/reader-rw5a-codex-review.md, "Final round (orchestrator)".

High 4 (+5): the figure author runs as an isolated, tool-free turn (no files,
tools, workspace or vault), like every other source-only Reader route, and a
provider that cannot isolate it is refused before any request.
High 2: the Reader report counts a legacy "verified" as an illustration,
through the figure view's one normalization.
High 1 (the fixed part): the frame is code-owned; the server sends only
closed property-check keys (the Reader's badge test is in FigureInline.test.tsx).
"""

from __future__ import annotations

import json

import pytest

from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.figures import service as FS
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import EXTRACTION, AuthorFake, build, build_figure_vault, context, flagship, rows

# ---------------------------------------------------------------------------
# High 4: an isolated, tool-free author turn
# ---------------------------------------------------------------------------


class _OptionsAuthor(AuthorFake):
    """Records the request options the transport receives."""

    def __init__(self, *, provider_type: str, isolates: bool = True, **kwargs) -> None:
        super().__init__([flagship(kind="illustrative")], provider_type=provider_type, **kwargs)
        self.isolates = isolates
        self.options: list[dict] = []

    def supports(self, capability: str) -> bool:
        if capability == ISOLATED_TURN:
            return self.isolates
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, TOOL_FREE}

    def complete(self, request):
        self.options.append({"isolated": request.isolated, "workspace": request.workspace})
        return super().complete(request)


@pytest.mark.parametrize("provider_type", ["codex_sdk", "openai_chat"])
def test_the_author_is_an_isolated_turn_with_no_workspace(tmp_path, provider_type):
    paths, repository = build_figure_vault(tmp_path / "vault")
    if provider_type == "openai_chat":
        from tests.figure_fixtures import set_config

        set_config(paths, "figures", price_per_million=1.0)
    author = _OptionsAuthor(provider_type=provider_type)
    figure = build(context(paths.root, author=author))["figure"]
    assert figure["verification"] == "illustrative"
    assert author.options == [{"isolated": True, "workspace": None}]


def test_a_provider_that_cannot_isolate_is_refused_before_any_request(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    author = _OptionsAuthor(provider_type="codex_sdk", isolates=False)
    with pytest.raises(FS.FigureRefused) as caught:
        FS.build_figure(load_vault(paths.root), repository,
                        FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]), author_client=author)
    assert caught.value.code == "not_isolated"
    assert author.calls == 0 and author.options == []
    assert rows(repository, "interactive_figures") == []


# ---------------------------------------------------------------------------
# High 2: the report normalizes a legacy "verified"
# ---------------------------------------------------------------------------

def _legacy_verified(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    build(context(paths.root, author=AuthorFake([flagship()])))
    with repository.connection() as connection:
        connection.execute("UPDATE interactive_figures SET verification = 'verified'")
        connection.commit()
    return paths, repository


def test_the_report_counts_a_legacy_verified_as_an_illustration(tmp_path):
    from learnloop.reader.reader_report import build_reader_report

    _paths, repository = _legacy_verified(tmp_path)
    assert build_reader_report(repository.sqlite_path, figures_enabled=True)["figures"]["built"] == {"illustrative": 1}


@pytest.mark.parametrize("json_flag", [True, False], ids=["json", "text"])
def test_the_report_cli_never_shows_verified(tmp_path, json_flag):
    from typer.testing import CliRunner

    from learnloop.cli import app

    paths, _repository = _legacy_verified(tmp_path)
    args = ["reader", "report", "--vault", str(paths.root), *(["--json"] if json_flag else [])]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["figures"]["built"] == {"illustrative": 1}
    assert "verified" not in result.output


# ---------------------------------------------------------------------------
# High 1 (the fixed part): closed property-check keys for the code-owned frame
# ---------------------------------------------------------------------------

def test_the_view_sends_closed_property_check_keys_only(tmp_path):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    claim = "matches the book's equation (checked)"
    spec = flagship(kind="illustrative", demonstrates=claim)
    spec["panels"].append({"kind": "readout", "label": claim, "expr": "1"})
    figure = build(context(paths.root, author=AuthorFake([spec])))["figure"]
    assert figure["propertyChecks"] == ["values_finite", "integrates_to_one", "nonnegative", "shaded_areas"]
    assert set(figure["propertyChecks"]) <= set(FS.PROPERTY_CHECKS)
    # The model's words reach the Reader as model text (spec and demonstrates),
    # inside the code-owned frame; the badge is the Reader's own.
    assert figure["demonstrates"] == claim and figure["verification"] == "illustrative"
