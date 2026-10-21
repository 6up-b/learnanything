"""Reader RW5a: the owner's scope decision and the redesign (2026-10-21).

See docs/reviews/reader-rw5a-codex-review.md, "Owner scope decision and redesign".

Class A: RW5a makes no "matches the book's equation (checked)" claim. Every
figure is an illustration, the source check (spec §8.3 step 3) is RW5c's,
and no code path stores or renders "verified" or "checked".

Class B: one :class:`~learnloop.figure_admission.FiguresGate` admits every
physical request of a build and of a figure prediction's learner-text
reading. Before each one it compares the configuration as it is now with
the start; any change stops the work with no further call. Switched off, a
figure text already queued takes main's path (it has nothing to read).

The admission sweeps enumerate every request (fakes that enter
``model_call``, as a real provider does), so a call added later is covered.
"""

from __future__ import annotations

import json
import re
from contextlib import contextmanager
from pathlib import Path

import pytest

from learnloop.ai.execution import model_call
from learnloop.figures import routes as R
from learnloop.figures import service as FS
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import (
    EQUATION_TEXT,
    EXTRACTION,
    AuthorFake,
    VerifierFake,
    build,
    build_figure_vault,
    call,
    context,
    flagship,
    rows,
)
from tests.test_figures_switch_off import _switch
from tests.text_gap_fakes import ChoiceDecider, GapLLMFake

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Class A: nothing is "checked"
# ---------------------------------------------------------------------------

def _highlight_case() -> dict:
    """Round 5's verify, High 1: f = 0.5 over a PMF support {0, 1}, a highlight
    covering both bars labelled f(k) (it shows 1)."""

    return {"spec_version": "ifs-v1", "kind": "reconstructed",
            "source_claims": [{"span_id": "p3", "quote": EQUATION_TEXT}], "demonstrates": "the book's f",
            "definitions": [{"name": "f", "expr": "0.5"}],
            "panels": [{"kind": "pmf_bars", "k": {"var": "k", "min": 0, "max": 1},
                        "series": [{"expr": "f", "label": "f(k)"}],
                        "highlight": {"from": "0", "to": "1", "label": "f(k)"}}],
            "invariants": [{"kind": "sums_to_one", "expr": "f", "var": "k", "from": 0, "to": 1},
                           {"kind": "equals_source", "name": "f"}]}


def _long_literal_case() -> dict:
    """Round 5's verify, High 2: a 31-digit literal the old literal rule rounded away."""

    spec = _highlight_case()
    spec["definitions"] = [{"name": "f", "expr": "1.00000000000000000000000000001*x"}]
    spec["panels"] = [{"kind": "function_plot", "x": {"var": "x", "min": 0, "max": 1},
                       "series": [{"expr": "f", "label": "f(x)"}]}]
    spec["invariants"] = [{"kind": "equals_source", "name": "f"}]
    return spec


@pytest.mark.parametrize("spec", [flagship(), _highlight_case(), _long_literal_case()],
                         ids=["flagship", "highlight", "long_literal"])
def test_no_figure_is_labelled_checked(tmp_path, spec):
    paths, repository = build_figure_vault(tmp_path / "vault")
    verifier = VerifierFake()  # a passing check, if anything asked it
    ctx = context(paths.root, author=AuthorFake([spec]), verifier=verifier)
    figure = build(ctx)["figure"]
    assert figure["verification"] == "illustrative"
    assert "checked" not in figure["label"].replace("not checked", "")
    assert figure["reason"] == FS.RECONSTRUCTION_REASON and verifier.calls == 0
    (row,) = rows(repository, "interactive_figures")
    assert row["verification"] == "illustrative"
    (listed,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert listed["verification"] == "illustrative"


def test_a_stored_verified_row_is_rendered_as_an_illustration(tmp_path):
    """A row stored "verified" before the scope decision is shown as RW5a's rules make it."""

    paths, repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake([flagship()]))
    build(ctx)
    with repository.connection() as connection:
        connection.execute("UPDATE interactive_figures SET verification = 'verified'")
        connection.commit()
    (listed,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert listed["verification"] == "illustrative" and listed["reason"] == FS.RECONSTRUCTION_REASON
    assert listed["label"] == "AI-built illustration of an interpretation · not checked against the book"


def _python_strings(path: Path) -> list[str]:
    """Every string constant of a module that is not a docstring (code, not prose)."""

    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                  if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                  and node.body and isinstance(node.body[0], ast.Expr)
                  and isinstance(node.body[0].value, ast.Constant)}
    # A key ("verified": whether a quote is verbatim in its span) is a field
    # name, not a verification value.
    keys = {id(key) for node in ast.walk(tree) if isinstance(node, ast.Dict) for key in node.keys if key is not None}
    keys |= {id(node.slice) for node in ast.walk(tree) if isinstance(node, ast.Subscript)}
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and id(node) not in docstrings and id(node) not in keys]


def _code_strings(path: Path) -> str:
    """A module's string literals (Python) or its text without comments (TypeScript)."""

    if path.suffix == ".py":
        return "\n".join(_python_strings(path))
    text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
    return re.sub(r"(?m)^\s*//.*$|\s// .*$", "", text)


def test_no_code_path_can_store_or_render_verified_or_checked():
    """Static: the claim's words appear nowhere in the figure code (Python or
    the Reader's renderer), and "verified" only as the store's RW5c constant;
    no verifier route exists."""

    from learnloop.ai import routing
    from learnloop.config.schema import AIRoutingConfig

    python = [*sorted((ROOT / "src" / "learnloop" / "figures").glob("*.py")),
              ROOT / "src" / "learnloop" / "figure_admission.py",
              ROOT / "src" / "learnloop_sidecar" / "handlers" / "figures.py",
              ROOT / "src" / "learnloop" / "db" / "stores" / "figures.py"]
    frontend = [path for path in sorted((ROOT / "apps" / "learnloop-tauri" / "src" / "screens" / "reader" / "figures")
                                        .glob("*.ts*")) if ".test." not in path.name]
    for path in [*python, *frontend]:
        text = _code_strings(path)
        assert "matches the book" not in text and "matches the source" not in text, path
        assert "equation (checked)" not in text and "· checked" not in text, path
    for path in python:
        literals = [value for value in _python_strings(path) if value == "verified"]
        if path.name == "figures.py" and path.parent.name == "stores":
            continue  # SHOWN and VERIFIED_RW5C: the stored value migration 216 keeps for RW5c
        assert literals == [], path
    assert not hasattr(R, "VERIFIER_TASK") and R.OWNER_KINDS == (R.AUTHOR_TASK,)
    assert "figure_verifier" not in AIRoutingConfig.model_fields
    assert "figure_verifier" not in Path(routing.__file__).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Class B: the admission sweep (every physical request)
# ---------------------------------------------------------------------------

class _Counter:
    def __init__(self, flip=None, after: int | None = None) -> None:
        self.flip, self.after, self.admitted = flip, after, 0

    def entered(self) -> None:
        self.admitted += 1
        if self.after is not None and self.admitted == self.after and self.flip is not None:
            self.flip()


class _GatedAuthor(AuthorFake):
    """An author that answers inside ``model_call``, so the installed gate admits it."""

    def __init__(self, answers, counter: _Counter, **kwargs) -> None:
        super().__init__(answers, **kwargs)
        self.counter = counter

    def complete(self, request):
        with model_call(self, purpose=request.purpose, prompt=request.prompt):
            self.counter.entered()
            return super().complete(request)


def _figures_setting(root: Path, key: str, value: str) -> None:
    config = root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    found = re.search(r"(?ms)^\[figures\]\n(.*?)(?=^\[|\Z)", text)
    if found is None:
        text = text.rstrip("\n") + f"\n\n[figures]\n{key} = {value}\n"
    elif re.search(rf"(?m)^{key} = ", found.group(1)):
        body = re.sub(rf"(?m)^{key} = .*$", f"{key} = {value}", found.group(1), count=1)
        text = text[:found.start(1)] + body + text[found.end(1):]
    else:
        text = text[:found.start(1)] + f"{key} = {value}\n" + text[found.start(1):]
    config.write_text(text, encoding="utf-8")


FLIPS = {
    "switch": lambda root: _switch(root, "figures", False),
    "cap": lambda root: _figures_setting(root, "max_daily_cost_usd", "0.5"),
    "price": lambda root: _figures_setting(root, "price_per_million", "3.0"),
}
#: A reconstruction whose first answer is unusable, so the build retries.
BUILD_ANSWERS = ["not a spec", flagship()]
BUILD_REQUESTS = 2


def test_the_build_control_makes_every_request(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    counter = _Counter()
    author = _GatedAuthor(list(BUILD_ANSWERS), counter)
    outcome = FS.build_figure(load_vault(paths.root), repository,
                              FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]), author_client=author)
    assert counter.admitted == BUILD_REQUESTS == author.calls
    assert outcome.view["verification"] == "illustrative" and len(rows(repository, "interactive_figures")) == 1


@pytest.mark.parametrize("flip", sorted(FLIPS))
@pytest.mark.parametrize("after", range(1, BUILD_REQUESTS + 1))
def test_a_build_makes_no_request_after_its_configuration_changes(tmp_path, flip, after):
    """Flip the switch, the cap or the price after the N-th admitted request:
    request N+1 is never admitted, and nothing is stored."""

    paths, repository = build_figure_vault(tmp_path / "vault")
    counter = _Counter(lambda: FLIPS[flip](paths.root), after)
    author = _GatedAuthor(list(BUILD_ANSWERS), counter)
    with pytest.raises(FS.FigureRefused) as caught:
        FS.build_figure(load_vault(paths.root), repository,
                        FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]), author_client=author)
    assert caught.value.code == "figures_changed"
    assert counter.admitted == after and author.calls == after
    assert rows(repository, "interactive_figures") == []


def test_a_sidecar_reload_stops_a_running_build(tmp_path):
    """The sidecar's build reads the vault loaded NOW (ctx.loaded_vault)."""

    import threading

    paths, repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root)
    ctx.library_ask_inline = False  # the build runs as a job, as in the app
    entered, release = threading.Event(), threading.Event()

    class _Waiting(_GatedAuthor):
        def complete(self, request):
            entered.set()
            assert release.wait(30)
            return super().complete(request)

    counter = _Counter()
    ctx.figure_author_client = _Waiting(list(BUILD_ANSWERS), counter)
    job = call(ctx, "reader.figure_request", {"extractionId": EXTRACTION, "spanIds": ["p3"]})
    assert entered.wait(30)
    _switch(paths.root, "figures", False)
    ctx.reload(maintenance=False)
    release.set()
    kept = ctx.figure_jobs.get(job["jobId"])
    assert kept is not None and kept.done.wait(60)
    assert counter.admitted == 0  # the first request was refused at its admission
    assert rows(repository, "interactive_figures") == []


class _GatedReader(GapLLMFake):
    def __init__(self, counter: _Counter, **kwargs) -> None:
        super().__init__(**kwargs)
        self.counter = counter

    def complete(self, request):
        with model_call(self, purpose=request.purpose, prompt=request.prompt):
            self.counter.entered()
            return super().complete(request)


class _GatedDecider(ChoiceDecider):
    """The in-process Decider double, its ``model_call`` counted."""

    def __init__(self, counter: _Counter, **kwargs) -> None:
        super().__init__(**kwargs)
        original = self._model_call

        @contextmanager
        def counted(client, **call):
            with original(client, **call) as metadata:
                counter.entered()
                yield metadata

        self._model_call = counted


def _gap_clients(counter: _Counter):
    from learnloop.diagnosis.text_gaps.pipeline import PipelineClients

    reading = LearnerGap(kind="prerequisite", prerequisite_name="Eigenvectors",
                         prerequisite_line="Vectors a matrix only scales.")
    llm = _GatedReader(counter, reading=reading)
    decider = _GatedDecider(counter, kind="prerequisite")
    return PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=lambda: decider, drafter=lambda: llm,
                           tutor=None, embedder=None)


def _gap_job(tmp_path):
    from tests.test_figures_codex_review import _missed_prediction

    return _missed_prediction(tmp_path)


def _gap_requests(tmp_path) -> int:
    from learnloop.diagnosis.text_gaps.jobs import process_next_gap_job

    paths, repository, _ctx, _found = _gap_job(tmp_path / "control")
    counter = _Counter()
    outcome = process_next_gap_job(paths.root, repository, owner="t", clients=_gap_clients(counter))
    assert outcome.state == "done"
    return counter.admitted


def test_the_gap_control_reads_with_the_reader_and_the_decider(tmp_path):
    # The reader, the Decider and the actions after them: the sweep below
    # covers every one of these requests.
    assert _gap_requests(tmp_path) >= 2


def test_a_figure_reading_makes_no_request_after_figures_are_switched_off(tmp_path):
    from learnloop.diagnosis.text_gaps.jobs import process_next_gap_job

    total = _gap_requests(tmp_path)
    for after in range(1, total + 1):
        paths, repository, _ctx, found = _gap_job(tmp_path / f"n{after}")
        counter = _Counter(lambda paths=paths: _switch(paths.root, "figures", False), after)
        outcome = process_next_gap_job(paths.root, repository, owner="t", clients=_gap_clients(counter))
        assert counter.admitted == after, (after, total)
        if after == total:
            # Switched off during the reading's last request: there is no
            # further request to refuse, and that reading stands.
            assert outcome.state == "done"
            continue
        assert (outcome.state, outcome.error) == ("retry_later", "figures_changed")
        with repository.connection() as connection:
            assert connection.execute("SELECT COUNT(*) FROM learner_text_gaps").fetchone()[0] == 0
        # The next run takes main's path: switched off, it has nothing to read.
        again = process_next_gap_job(paths.root, repository, owner="t", clients=_gap_clients(counter))
        assert (again.state, again.error) == ("skipped", None) and counter.admitted == after
        assert found["predictionId"] == again.source_id

