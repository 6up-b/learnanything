"""Reader RW5c (G23g): what the switch-off golden pins, as one function both trees can run.

``tests/fixtures/rw5c_switch_off_golden.json`` was written by running this file on an export of main
(``aae65635b6``, before RW5c): ``python tests/rw5c_golden_source.py <out> `` under ``env -i`` with
``PYTHONPATH=<export>/src:<export>``. :mod:`tests.test_rw5c_switch_off` runs the same function on this
tree with ``figures.checked_labels_enabled`` off and compares: the views, the reader report, the CLI's
report, the reuse keys and the author's prompt must be main's, byte for byte, once ids and times are
replaced. It imports nothing RW5c added.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ID = re.compile(r"\b(fig|frq|fpr|ljob|jdg)_[0-9A-Za-z]+\b")
UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
WHEN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)?")
TEMPORARY = re.compile(r"(?:/[^\s\"']+)+/vault\b")
NOW = datetime(2026, 11, 2, 12, 0, 0, tzinfo=timezone.utc)


def _clean(value: Any) -> Any:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    for pattern, replacement in ((ID, r"\1_ID"), (UUID, "UUID"), (WHEN, "WHEN"), (TEMPORARY, "VAULT")):
        text = pattern.sub(replacement, text)
    return json.loads(text)


def golden(root: Path, *, switch: bool) -> dict[str, Any]:
    from typer.testing import CliRunner

    from learnloop.cli.app import app
    from learnloop.figures import service as FS
    from learnloop.reader.reader_report import build_reader_report
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths
    from tests.figure_fixtures import EXTRACTION, AuthorFake, build, build_figure_vault, call, context, flagship, set_config

    paths, repository = build_figure_vault(root)
    if switch:
        set_config(paths, "figures", checked_labels_enabled=False)
    author = AuthorFake([flagship()])
    ctx = context(paths.root, author=author)
    first = build(ctx)
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    prediction = next(iter(listed["figures"][0]["predictions"]), None)
    predicted = None
    if prediction is not None:
        predicted = call(ctx, "reader.figure_predict", {"figureId": first["figure"]["figureId"], "predictionIndex": 0,
                                                        "answer": prediction["choices"][0]["value"]})
    again = call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    vault = load_vault(paths.root)
    context_ = FS.SourceContext(passage=[{"span_id": "p3", "type": "Equation", "text": "x"}], span_texts={"p3": "x"})
    hashes = {
        "plain": FS.request_hash(FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]), context_, None),
        "advanced": FS.request_hash(FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]), context_, None, advanced=True),
        "revision": FS.request_hash(FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"], supersedes_id="fig_1",
                                                     revision_note="a note"), context_, None),
    }
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    report = build_reader_report(sqlite_path, now=NOW, figures_enabled=True, figure_offers_enabled=True,
                                 figure_show_me_enabled=True)
    cli = CliRunner().invoke(app, ["reader", "report", "--json", "--vault", str(paths.root)])
    return _clean({
        "built": first, "listed": listed, "predicted": predicted, "after": again, "request_hash": hashes,
        "report": report, "cli_report": json.loads(cli.output), "cli_exit": cli.exit_code,
        "author_prompt_sha256": hashlib.sha256(author.prompts[0].encode("utf-8")).hexdigest(),
        "author_calls": author.calls,
        "tables": sorted(row[0] for row in repository.connection().execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'figure%'") if row[0] != "figure_source_checks"),
    })


if __name__ == "__main__":
    import tempfile

    out = Path(sys.argv[1])
    with tempfile.TemporaryDirectory() as scratch:
        payload = golden(Path(scratch) / "vault", switch=False)
    out.write_text(json.dumps(payload, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
