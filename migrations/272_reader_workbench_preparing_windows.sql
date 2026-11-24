-- Reader workbench v2, RD-retire (docs/reviews/reader-rd-retire.md, phase 2 step 2): a window for a book still being
-- prepared. desk_windows.kind gains 'preparing': its spec_json names the source alone ({"kind": "preparing",
-- "source_id": ...}), because a book being prepared has no reading yet, and a source window names its reading
-- (desks/content_ref.py). The window shows the original while the text is made, its progress, a failure and the retry;
-- once the book is ready the desk replaces it with the book's source window.
--
-- The rebuild follows 266: SQLite cannot widen a CHECK in place, so desk_windows is rebuilt temp-then-rename with every
-- row and id preserved, under PRAGMA foreign_keys = OFF (no table's foreign key names desk_windows; its own names
-- desks); DROP TABLE removes its index, recreated on the renamed table with the same name and definition. The same
-- columns, defaults and CHECKs otherwise. No row changes.
PRAGMA foreign_keys = OFF;

CREATE TABLE desk_windows__272 (
  window_id TEXT PRIMARY KEY,
  desk_id TEXT NOT NULL REFERENCES desks(desk_id),
  slot INTEGER NOT NULL CHECK (slot >= 0),
  pane INTEGER NOT NULL DEFAULT 0 CHECK (pane IN (0, 1)),
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
  kind TEXT NOT NULL CHECK (kind IN (
    'source', 'video', 'pad', 'pad_stack', 'lesson', 'thread', 'compare', 'panel', 'figure_notebook', 'preparing'
  )),
  spec_json TEXT NOT NULL,
  view_json TEXT NOT NULL DEFAULT '{}',
  opened_at TEXT NOT NULL,
  closed_at TEXT
);
INSERT INTO desk_windows__272 (window_id, desk_id, slot, pane, active, kind, spec_json, view_json, opened_at, closed_at)
SELECT window_id, desk_id, slot, pane, active, kind, spec_json, view_json, opened_at, closed_at
FROM desk_windows;

DROP TABLE desk_windows;
ALTER TABLE desk_windows__272 RENAME TO desk_windows;
CREATE INDEX idx_desk_windows_desk ON desk_windows(desk_id, closed_at, slot, pane);

PRAGMA foreign_keys = ON;
