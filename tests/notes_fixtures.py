"""Builders and fakes for curriculum C2's tests (notes linked; no network, no real tend).

Privacy: no test ever reaches the owner's real ``tend`` or notes. ``conftest`` sets
``LEARNLOOP_NOTES_TEND=off``; :func:`install_fake_tend` points it at a FAKE ``tend``
executable written into the test's tmp directory, which answers from a synthetic
corpus of notes also written there:

* ``search -k K --json --local --notes-only [--words] -- QUERY``: every corpus entry one
  of whose ``words`` appears in the query (tend's JSON shape: ``results`` and
  ``warning``); entries outside the allowlist and another machine's entries are returned
  too, so the adapter's dropping is exercised;
* ``serve``: one JSON request per stdin line; ``read`` answers the file's whole text, or
  ``{"error": "PermissionError: private note"}`` for a path the corpus marks private.

Every invocation's argv is appended to the log (one JSON line each).
``FAKE_TEND_MODE``: ``slow`` (sleeps past any timeout), ``no_read`` (``unknown op``),
``fail`` (exit 1); ``serve_fail`` (``serve`` exits 1 and says nothing), ``serve_garbage``
(``serve`` prints unreadable lines), ``serve_slow`` (``serve`` sleeps past any timeout):
search still answers in those three (Codex review F1: tend's read is down, its search up).

``NoteLinkFake`` answers the note link judge from the prompt's context: a note whose
text contains one of ``discusses`` words discusses it (``how`` and ``about`` as
configured); every other note is unrelated. It is a ChatGPT-plan client
(``provider_type = "chatgpt_plan"``), the only route the judge may ask.
"""

from __future__ import annotations

import json
import stat
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

from learnloop.ai.execution import report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION
from tests.structured_ai import StructuredClientFake

SENTINEL = "SENTINEL-NOTE-TEXT-7f3a"

_FAKE = r'''#!{python}
import json, os, sys, time
corpus = json.load(open(os.environ["FAKE_TEND_CORPUS"]))
log = os.environ.get("FAKE_TEND_LOG")
if log:
    with open(log, "a") as handle:
        handle.write(json.dumps(sys.argv[1:]) + "\n")
mode = os.environ.get("FAKE_TEND_MODE", "")
if mode == "slow":
    time.sleep(30)
if mode == "fail":
    sys.exit(1)
args = sys.argv[1:]
if args and args[0] == "search":
    query = args[args.index("--") + 1:] if "--" in args else [a for a in args[1:] if not a.startswith("-")]
    text = " ".join(query).casefold()
    k = int(args[args.index("-k") + 1]) if "-k" in args else 10
    hits = [dict(entry["hit"], via="words" if "--words" in args else "both")
            for entry in corpus["entries"] if any(word.casefold() in text for word in entry["words"])]
    print(json.dumps({{"results": hits[:k], "warning": None}}))
elif args and args[0] == "serve":
    if mode == "serve_fail":
        sys.exit(1)
    if mode == "serve_slow":
        time.sleep(30)
    if mode == "serve_garbage":
        for line in sys.stdin:
            print("not json at all", flush=True)
        sys.exit(0)
    private = set(corpus.get("private", []))
    for line in sys.stdin:
        if not line.strip():
            continue
        req = json.loads(line)
        if mode == "no_read":
            res = {{"error": "unknown op 'read'"}}
        elif req.get("op") != "read":
            res = {{"error": "unknown op " + repr(req.get("op"))}}
        elif req["path"] in private:
            res = {{"error": "PermissionError: private note"}}
        else:
            try:
                res = {{"text": open(req["path"]).read(), "title": os.path.basename(req["path"])}}
            except OSError as exc:
                res = {{"error": "RemoteError: not an indexed file: " + req["path"]}}
        res["id"] = req.get("id")
        print(json.dumps(res), flush=True)
else:
    sys.exit(2)
'''


class FakeTend:
    """The fake executable, its synthetic corpus and its invocation log."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.notes = root / "notes"
        self.quicknote = root / "Quicknote"
        self.pocket = self.quicknote / "Pocket Notes"
        self.outside = root / "projects" / "repo"
        for folder in (self.notes, self.pocket, self.outside):
            folder.mkdir(parents=True, exist_ok=True)
        self.binary = root / "bin" / "tend"
        self.corpus_path = root / "corpus.json"
        self.log = root / "tend.log"
        self.entries: list[dict[str, Any]] = []
        self.private: list[str] = []

    def write_binary(self) -> None:
        self.binary.parent.mkdir(parents=True, exist_ok=True)
        self.binary.write_text(_FAKE.format(python=sys.executable), encoding="utf-8")
        self.binary.chmod(self.binary.stat().st_mode | stat.S_IXUSR)

    def add(self, path: Path, text: str, *, words: Sequence[str], heading: str = "", line: int = 1,
            content_hash: str | None = None, mtime: float = 1_759_500_000.0, source: str = "local",
            private: bool = False, title: str | None = None) -> dict[str, Any]:
        """A synthetic note file and its tend hit (``line`` is the heading's line)."""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        hit = {"id": len(self.entries) + 1, "path": str(path), "title": title or path.stem, "heading": heading,
               "line": line, "snippet": text[:80], "score": 1.0, "via": "both",
               "hash": content_hash or f"h-{len(self.entries)}-{abs(hash(text)) % 10_000}", "source": source,
               "mtime": mtime}
        self.entries.append({"hit": hit, "words": list(words)})
        if private:
            self.private.append(str(path))
        self.save()
        return hit

    def save(self) -> None:
        self.corpus_path.write_text(json.dumps({"entries": self.entries, "private": self.private}), encoding="utf-8")

    def calls(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines() if line.strip()]

    def config(self, *, lexical_only: bool = False, extra: str = "") -> str:
        """The vault's ``[notes.tend]`` section for this corpus (the allowlist: notes and Quicknote)."""

        return (f'[notes.tend]\npaths = ["{self.notes}", "{self.quicknote}"]\n'
                f'pocket_notes_paths = ["{self.pocket}"]\nlexical_only = {"true" if lexical_only else "false"}\n'
                f"timeout_seconds = 5.0\n{extra}")


def install_fake_tend(root: Path, monkeypatch: Any, *, mode: str = "") -> FakeTend:
    fake = FakeTend(root)
    fake.write_binary()
    fake.save()
    monkeypatch.setenv("LEARNLOOP_NOTES_TEND", str(fake.binary))
    monkeypatch.setenv("FAKE_TEND_CORPUS", str(fake.corpus_path))
    monkeypatch.setenv("FAKE_TEND_LOG", str(fake.log))
    if mode:
        monkeypatch.setenv("FAKE_TEND_MODE", mode)
    else:
        monkeypatch.delenv("FAKE_TEND_MODE", raising=False)
    return fake


def eigen_corpus(fake: FakeTend) -> dict[str, dict[str, Any]]:
    """Synthetic notes: two that discuss eigenvalues (one a Pocket Notes page), one that
    does not, one outside the allowlist, one another machine's, one private."""

    return {
        "typed": fake.add(fake.notes / "linear.org",
                          "#+title: Linear algebra\n* Eigen stuff\nEigenvalues: Av = lv, so det(A - lI) = 0. "
                          f"{SENTINEL}\n* Other\nUnrelated text.\n", words=["eigenvalues"], heading="Eigen stuff",
                          line=2, title="Linear algebra"),
        "pocket": fake.add(fake.pocket / "2026-10-03.md",
                           "# Eigen page\nWorked the 2x2 eigen example by hand.\n", words=["eigenvalues"],
                           heading="Eigen page", line=1, title="2026-10-03"),
        "unrelated": fake.add(fake.notes / "groceries.org", "* Shopping\nEggs, milk, eigen-free bread.\n",
                              words=["eigenvalues"], heading="Shopping", line=1, title="groceries"),
        "outside": fake.add(fake.outside / "README.md", "# Eigen solver\nProject docs about eigenvalues.\n",
                            words=["eigenvalues"], heading="Eigen solver", line=1),
        "remote": fake.add(fake.notes / "remote.org", "* Eigen remote\nEigenvalues on the laptop.\n",
                           words=["eigenvalues"], heading="Eigen remote", line=1, source="laptop"),
        "private": fake.add(fake.notes / "private.org", "* Eigen private\nEigenvalues, private.\n",
                            words=["eigenvalues"], heading="Eigen private", line=1, private=True),
    }


def prompt_context(prompt: str) -> dict[str, Any]:
    start = prompt.index("{", prompt.index("prompt_version"))
    return json.loads(prompt[start:])["context"]


class NoteLinkFake(StructuredClientFake):
    provider_name = "fake_plan_notes"
    provider_type = "chatgpt_plan"
    model = "fake-note-link-model"

    def __init__(self, *, discusses: Sequence[str] = ("Av = lv", "eigen example"), how: str = "restates",
                 about: str = "passage", fail: Exception | None = None,
                 shape: Callable[[list[dict[str, Any]]], list[dict[str, Any]]] | None = None,
                 on_call: Callable[[], None] | None = None) -> None:
        self.discusses = tuple(discusses)
        self.how = how
        self.about = about
        self.fail = fail
        #: Rewrites the verdicts before they are returned (an incomplete answer, F12).
        self.shape = shape
        #: Runs when a request arrives (the learner acting meanwhile, F2).
        self.on_call = on_call
        self.prompts: list[str] = []
        self.contexts: list[dict[str, Any]] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        context = prompt_context(request.prompt)
        self.prompts.append(request.prompt)
        self.contexts.append(context)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 60,
                           "resolved_model": self.model})
        if self.on_call is not None:
            self.on_call()
        if self.fail is not None:
            raise self.fail
        verdicts = []
        for note in context["notes"]:
            if any(word in note["text"] for word in self.discusses):
                verdicts.append({"note": note["id"], "verdict": "discusses", "about": self.about, "how": self.how,
                                 "line": f"your note {self.how} it"})
            else:
                verdicts.append({"note": note["id"], "verdict": "unrelated"})
        if self.shape is not None:
            verdicts = self.shape(verdicts)
        return request.result_model.model_validate({"notes": verdicts})

    @property
    def calls(self) -> int:
        return len(self.contexts)


class MeteredNoteLinkFake(NoteLinkFake):
    """The same answers on a metered (OpenRouter-like) route: the judge must refuse it."""

    provider_name = "fake_metered_notes"
    provider_type = "openrouter"


__all__ = ["FakeTend", "MeteredNoteLinkFake", "NoteLinkFake", "SENTINEL", "eigen_corpus", "install_fake_tend",
           "prompt_context"]
