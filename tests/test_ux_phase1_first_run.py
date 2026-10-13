"""UX Phase 1: a library exists before the first click (docs/specs/ux_learnloop_v1.md §6.1, Q1/Q2).

The desktop shell asks the sidecar to create its default library (``~/LearnLoop``)
when nothing is remembered; ``initialize`` creates it silently with no subject
and the default level. Without the flag a missing path still fails, and it never
scaffolds into a folder that already holds someone's files.
"""

from __future__ import annotations

import io
import json

from learnloop_sidecar.server import serve


def _rpc(messages):
    stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _initialize(path, **extra):
    return _rpc([{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(path), **extra}}])[0]


def test_initialize_creates_the_default_library_when_asked(tmp_path):
    home_library = tmp_path / "home" / "LearnLoop"
    response = _initialize(home_library, createIfMissing=True)
    assert "error" not in response, response
    vault = response["result"]["vault"]
    assert (home_library / "learnloop.toml").is_file()
    assert vault["subjects"] == []
    assert not (home_library / "profile" / "learner.yaml").exists()


def test_initialize_keeps_an_existing_library(tmp_path):
    library = tmp_path / "LearnLoop"
    _initialize(library, createIfMissing=True)
    marker = library / "notes.md"
    marker.write_text("mine", encoding="utf-8")
    config_before = (library / "learnloop.toml").read_text(encoding="utf-8")
    response = _initialize(library, createIfMissing=True)
    assert "error" not in response, response
    assert marker.read_text(encoding="utf-8") == "mine"
    assert (library / "learnloop.toml").read_text(encoding="utf-8") == config_before


def test_initialize_without_the_flag_still_refuses_a_missing_path(tmp_path):
    response = _initialize(tmp_path / "nowhere")
    assert "error" in response
    assert not (tmp_path / "nowhere" / "learnloop.toml").exists()


def test_initialize_never_scaffolds_into_someone_elses_folder(tmp_path):
    folder = tmp_path / "LearnLoop"
    folder.mkdir()
    (folder / "taxes-2025.xlsx").write_bytes(b"not a vault")
    response = _initialize(folder, createIfMissing=True)
    assert response["error"]["data"]["code"] == "library_folder_in_use"
    assert "LearnLoop couldn't open your library" in response["error"]["message"]
    assert not (folder / "learnloop.toml").exists()
