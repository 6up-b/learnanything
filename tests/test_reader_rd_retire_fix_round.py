"""The Reader's retirement, review fix round (docs/reviews/reader-rd-retire.md "Review fix round").

Major 15 (ledger RDX-8): one damaged ``desk_windows`` row (its ``spec_json`` or ``view_json`` not a JSON object:
``'[]'``, ``'null'``, malformed) failed ``desk.state`` for every desk. Each row is read on its own now: the damaged
window comes back with no content (the desks keep it inert and name it) beside the healthy ones.
"""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.desks.workspace import desk_state
from tests.desk_helpers import Batches
from tests.helpers import create_basic_vault


def _desk_with_three_windows(tmp_path) -> Repository:
    repository = Repository(create_basic_vault(tmp_path / "vault").sqlite_path)
    batches = Batches(repository)
    batches.desk({"op": "create_desk", "desk_id": "d1", "title": "a book", "position": "a0"})
    for version, window_id in enumerate(("w_ok", "w_spec", "w_view"), start=1):
        reply = batches.desk({"op": "open_window", "desk_id": "d1", "window_id": window_id, "expected_version": version,
                              "content": {"kind": "source", "source_id": f"src_{window_id}", "extraction_id": f"ext_{window_id}"},
                              "view": {"spanId": "s1"}})
        assert reply["results"] == [{"status": "ok"}]
    return repository


def _windows(repository: Repository) -> dict[str, dict]:
    desk = desk_state(repository)["desks"][0]
    return {window["window_id"]: window for slot in desk["slots"] for window in slot["windows"]}


def test_one_damaged_window_row_leaves_every_other_window_readable(tmp_path):
    repository = _desk_with_three_windows(tmp_path)
    for spec, view in (("[]", "null"), ("null", "{not json"), ("{not json", "[1]"), ('{"content": [1]}', '"text"')):
        with repository.connection() as connection:
            connection.execute("UPDATE desk_windows SET spec_json = ? WHERE window_id = 'w_spec'", (spec,))
            connection.execute("UPDATE desk_windows SET view_json = ? WHERE window_id = 'w_view'", (view,))
        windows = _windows(repository)
        assert windows["w_ok"]["content"]["source_id"] == "src_w_ok"
        assert windows["w_ok"]["view"] == {"spanId": "s1"}
        assert windows["w_spec"]["content"] is None, spec
        assert windows["w_view"]["view"] == {}, view
        assert windows["w_view"]["content"]["source_id"] == "src_w_view"
