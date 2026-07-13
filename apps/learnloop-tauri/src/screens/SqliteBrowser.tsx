import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type RefObject
} from "react";
import { api } from "../api/client";
import type { SqliteExecResult, SqliteTableInfo, SqliteTableSnapshot } from "../api/dto";
import { COLOR, Faint, FONT_MONO, Pill } from "../components/term";

const PAGE = 200;

type Cell = string | number | boolean | null;
type BrowserMode = "nav" | "edit";
type CellPosition = { row: number; column: number };

function CellText({ value }: { value: Cell }) {
  if (value === null) return <span style={{ color: COLOR.textFaint, fontStyle: "italic" }}>NULL</span>;
  if (typeof value === "number") return <span style={{ color: COLOR.amber }}>{String(value)}</span>;
  if (typeof value === "boolean") return <span style={{ color: COLOR.pink }}>{String(value)}</span>;
  return <span style={{ color: COLOR.text }}>{value}</span>;
}

// A selectable grid cell. Editing is deliberately handled by the inspector so
// long and multiline values never have to fit inside the table column.
function GridCell({
  value,
  selected,
  editing,
  onSelect,
  onEdit,
  cellRef
}: {
  value: Cell;
  selected: boolean;
  editing: boolean;
  onSelect: () => void;
  onEdit: () => void;
  cellRef: (element: HTMLTableCellElement | null) => void;
}) {
  const tdStyle = {
    borderRight: `1px solid ${COLOR.border}`,
    borderBottom: `1px solid ${COLOR.border}`,
    padding: "4px 8px",
    fontFamily: FONT_MONO,
    fontSize: 12,
    whiteSpace: "nowrap" as const,
    maxWidth: 360,
    overflow: "hidden",
    textOverflow: "ellipsis",
    cursor: "pointer",
    background: editing ? "#302314" : selected ? "#241d12" : "transparent",
    boxShadow: selected ? `inset 0 0 0 1px ${editing ? COLOR.green : COLOR.amber}` : "none"
  };

  return (
    <td
      ref={cellRef}
      role="gridcell"
      aria-selected={selected}
      style={tdStyle}
      title={value === null ? "NULL" : String(value)}
      onClick={onSelect}
      onDoubleClick={onEdit}
    >
      <CellText value={value} />
    </td>
  );
}

function ConsoleResult({ result }: { result: SqliteExecResult }) {
  if (result.kind === "write") {
    return (
      <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.green, padding: "8px 0" }}>
        ✓ {result.rowsAffected} row{result.rowsAffected === 1 ? "" : "s"} affected
        {result.lastInsertRowId ? <Faint> · last rowid {result.lastInsertRowId}</Faint> : null}
      </div>
    );
  }
  return (
    <div style={{ overflow: "auto", maxHeight: 240, border: `1px solid ${COLOR.border}`, marginTop: 8 }}>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            {result.columns.map((col) => (
              <th key={col} style={headStyle}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {result.rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} style={{ ...cellStyle }}>
                  <CellText value={cell} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {result.truncated ? (
        <div style={{ padding: "6px 8px", fontSize: 11, color: COLOR.amber }}>
          results truncated to first 500 rows
        </div>
      ) : null}
    </div>
  );
}

export function SqliteBrowser({ path, onError }: { path: string; onError: (message: string) => void }) {
  const [tables, setTables] = useState<SqliteTableInfo[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [data, setData] = useState<SqliteTableSnapshot | null>(null);
  const [offset, setOffset] = useState(0);
  const [sql, setSql] = useState("");
  const [execResult, setExecResult] = useState<SqliteExecResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [activeCell, setActiveCell] = useState<CellPosition | null>(null);
  const [mode, setMode] = useState<BrowserMode>("nav");
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [editDraft, setEditDraft] = useState("");
  const [editAsNull, setEditAsNull] = useState(false);
  const gridRef = useRef<HTMLDivElement>(null);
  const editRef = useRef<HTMLTextAreaElement>(null);
  const cellRefs = useRef(new Map<string, HTMLTableCellElement>());
  const initialFocusPath = useRef<string | null>(null);

  const refreshTables = useCallback(async () => {
    try {
      const snapshot = await api.sqliteTables(path);
      setTables(snapshot.tables);
      setSelected((current) => current ?? snapshot.tables[0]?.name ?? null);
    } catch (error) {
      onError((error as Error).message);
    }
  }, [path, onError]);

  // (Re)load the table list whenever the database file changes.
  useEffect(() => {
    setSelected(null);
    setData(null);
    setOffset(0);
    setExecResult(null);
    setActiveCell(null);
    setMode("nav");
    setInspectorOpen(false);
    initialFocusPath.current = null;
    void refreshTables();
  }, [refreshTables]);

  const loadTable = useCallback(
    async (table: string, nextOffset: number) => {
      try {
        setData(await api.sqliteTable(path, table, PAGE, nextOffset));
      } catch (error) {
        onError((error as Error).message);
      }
    },
    [path, onError]
  );

  useEffect(() => {
    if (selected) void loadTable(selected, offset);
  }, [selected, offset, loadTable]);

  // Start each table/page at its first cell and place keyboard focus in the
  // database grid the first time this file opens.
  useEffect(() => {
    cellRefs.current.clear();
    setMode("nav");
    setActiveCell(data && data.rows.length > 0 && data.columns.length > 0 ? { row: 0, column: 0 } : null);
    if (data && initialFocusPath.current !== path) {
      initialFocusPath.current = path;
      requestAnimationFrame(() => gridRef.current?.focus());
    }
  }, [data?.table, data?.columns.length, data?.rows.length, offset, path]);

  useEffect(() => {
    if (!activeCell) return;
    cellRefs.current.get(`${activeCell.row}:${activeCell.column}`)?.scrollIntoView({ block: "nearest", inline: "nearest" });
  }, [activeCell]);

  useEffect(() => {
    if (mode === "edit") requestAnimationFrame(() => editRef.current?.focus());
  }, [mode]);

  const updateCell = async (rowid: number, column: string, value: string | null): Promise<boolean> => {
    if (!selected || busy) return false;
    setBusy(true);
    try {
      await api.sqliteUpdateCell(path, selected, rowid, column, value);
      await loadTable(selected, offset);
      return true;
    } catch (error) {
      onError((error as Error).message);
      return false;
    } finally {
      setBusy(false);
    }
  };

  const insertRow = async () => {
    if (!selected || busy) return;
    setBusy(true);
    try {
      await api.sqliteInsertRow(path, selected);
      await refreshTables();
      await loadTable(selected, offset);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const deleteRow = async (rowid: number) => {
    if (!selected || busy) return;
    setBusy(true);
    try {
      await api.sqliteDeleteRow(path, selected, rowid);
      await refreshTables();
      await loadTable(selected, offset);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const runSql = async () => {
    if (!sql.trim() || busy) return;
    setBusy(true);
    try {
      const result = await api.sqliteExec(path, sql);
      setExecResult(result);
      // A write may have changed the current table / row counts.
      if (result.kind === "write") {
        await refreshTables();
        if (selected) await loadTable(selected, offset);
      }
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const editable = Boolean(data?.editable);
  const rangeEnd = data ? Math.min(offset + (data.rows.length || 0), data.rowCount) : 0;
  const pkSet = useMemo(() => new Set(data?.primaryKey ?? []), [data]);
  const selectedValue = activeCell && data ? data.rows[activeCell.row]?.cells[activeCell.column] : undefined;
  const selectedColumn = activeCell && data ? data.columns[activeCell.column] : undefined;
  const selectedRow = activeCell && data ? data.rows[activeCell.row] : undefined;
  const selectedCellEditable = Boolean(editable && selectedRow?.rowid !== null && selectedRow?.rowid !== undefined);

  const focusGrid = () => requestAnimationFrame(() => gridRef.current?.focus());

  const selectCell = (position: CellPosition, openInspector = false) => {
    setActiveCell(position);
    setMode("nav");
    if (openInspector) setInspectorOpen(true);
    focusGrid();
  };

  const beginCellEdit = (position: CellPosition | null = activeCell) => {
    if (!position || !data || busy) return;
    const row = data.rows[position.row];
    const value = row?.cells[position.column];
    if (value === undefined || !editable || row.rowid === null) return;
    setActiveCell(position);
    setEditDraft(value === null ? "" : String(value));
    setEditAsNull(value === null);
    setInspectorOpen(true);
    setMode("edit");
  };

  const cancelCellEdit = () => {
    setMode("nav");
    focusGrid();
  };

  const commitCellEdit = async () => {
    if (!selectedColumn || !selectedRow || selectedRow.rowid === null) return;
    const saved = await updateCell(selectedRow.rowid, selectedColumn.name, editAsNull ? null : editDraft);
    if (saved) {
      setMode("nav");
      focusGrid();
    }
  };

  const moveCell = (rowDelta: number, columnDelta: number) => {
    if (!data || data.rows.length === 0 || data.columns.length === 0) return;
    const current = activeCell ?? { row: 0, column: 0 };
    setActiveCell({
      row: Math.max(0, Math.min(data.rows.length - 1, current.row + rowDelta)),
      column: Math.max(0, Math.min(data.columns.length - 1, current.column + columnDelta))
    });
  };

  const onGridKeyDown = (event: ReactKeyboardEvent<HTMLDivElement>) => {
    if (mode !== "nav") return;
    let handled = true;
    if (event.key === "h" || event.key === "ArrowLeft") moveCell(0, -1);
    else if (event.key === "l" || event.key === "ArrowRight") moveCell(0, 1);
    else if (event.key === "j" || event.key === "ArrowDown") moveCell(1, 0);
    else if (event.key === "k" || event.key === "ArrowUp") moveCell(-1, 0);
    else if (event.key === "Enter" || event.key === "i" || event.key === "e") beginCellEdit();
    else if (event.key === " ") setInspectorOpen((open) => !open);
    else if (event.key === "Escape" && inspectorOpen) setInspectorOpen(false);
    else handled = false;
    if (handled) {
      event.preventDefault();
      event.stopPropagation();
    }
  };

  return (
    <div data-sqlite-browser style={{ flex: 1, display: "flex", minHeight: 0 }}>
      {/* Table list */}
      <div style={{ width: 200, flexShrink: 0, borderRight: `1px solid ${COLOR.border}`, overflowY: "auto" }}>
        <div style={{ padding: "8px 12px", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", color: COLOR.textFaint, borderBottom: `1px solid ${COLOR.border}` }}>
          tables · {tables.length}
        </div>
        {tables.map((table) => (
          <div
            key={table.name}
            onClick={() => {
              setSelected(table.name);
              setOffset(0);
              setInspectorOpen(false);
              focusGrid();
            }}
            style={{
              padding: "6px 12px",
              cursor: "pointer",
              fontFamily: FONT_MONO,
              fontSize: 12,
              display: "flex",
              justifyContent: "space-between",
              gap: 8,
              background: selected === table.name ? "#241d12" : "transparent",
              borderLeft: `2px solid ${selected === table.name ? COLOR.amber : "transparent"}`,
              color: selected === table.name ? COLOR.text : COLOR.textDim
            }}
          >
            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{table.name}</span>
            <Faint style={{ fontSize: 11 }}>{table.rowCount}</Faint>
          </div>
        ))}
      </div>

      {/* Grid + console */}
      <div className="ll-scroll" style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "8px 14px", borderBottom: `1px solid ${COLOR.border}`, display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
          <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.amberLink }}>{selected ?? "—"}</span>
          {data ? <Faint style={{ fontSize: 11 }}>{data.rowCount} rows</Faint> : null}
          <Pill color={mode === "edit" ? "green" : "amber"} style={{ fontSize: 10 }}>{mode === "edit" ? "EDIT" : "NAV"}</Pill>
          {!editable && data ? <Pill color="slate">read-only · no rowid</Pill> : null}
          <span style={{ flex: 1 }} />
          {editable ? (
            <ActionButton label="+ row" onClick={insertRow} />
          ) : null}
          <ActionButton label="‹ prev" disabled={offset <= 0} onClick={() => setOffset(Math.max(0, offset - PAGE))} />
          <Faint style={{ fontSize: 11, fontFamily: FONT_MONO }}>
            {data ? `${data.rowCount === 0 ? 0 : offset + 1}–${rangeEnd}` : "—"}
          </Faint>
          <ActionButton label="next ›" disabled={!data || rangeEnd >= data.rowCount} onClick={() => setOffset(offset + PAGE)} />
        </div>

        <div
          ref={gridRef}
          role="grid"
          aria-label={selected ? `${selected} database table` : "database table"}
          tabIndex={0}
          onKeyDown={onGridKeyDown}
          style={{ flex: 1, overflow: "auto", minHeight: 0, outline: "none" }}
        >
          {data ? (
            <table style={{ borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {editable ? <th style={{ ...headStyle, width: 28 }} /> : null}
                  {data.columns.map((col) => (
                    <th key={col.name} style={headStyle}>
                      <span style={{ color: COLOR.cyan }}>{col.name}</span>
                      {pkSet.has(col.name) ? <span style={{ color: COLOR.amber }}> ★</span> : null}
                      <Faint style={{ fontSize: 10 }}> {col.type || "·"}</Faint>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row, rowIndex) => (
                  <tr key={row.rowid ?? `r${rowIndex}`}>
                    {editable ? (
                      <td style={{ ...cellStyle, textAlign: "center", color: COLOR.red, cursor: row.rowid !== null ? "pointer" : "default" }}
                        onClick={() => { if (row.rowid !== null) void deleteRow(row.rowid); }}
                        title="delete row"
                      >
                        {row.rowid !== null ? "✕" : ""}
                      </td>
                    ) : null}
                    {row.cells.map((cell, cellIndex) => (
                      <GridCell
                        key={cellIndex}
                        value={cell}
                        selected={activeCell?.row === rowIndex && activeCell.column === cellIndex}
                        editing={mode === "edit" && activeCell?.row === rowIndex && activeCell.column === cellIndex}
                        onSelect={() => selectCell({ row: rowIndex, column: cellIndex }, true)}
                        onEdit={() => {
                          beginCellEdit({ row: rowIndex, column: cellIndex });
                        }}
                        cellRef={(element) => {
                          const key = `${rowIndex}:${cellIndex}`;
                          if (element) cellRefs.current.set(key, element);
                          else cellRefs.current.delete(key);
                        }}
                      />
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: 20, color: COLOR.textFaint, fontSize: 13 }}>loading database…</div>
          )}
        </div>

        {/* SQL console */}
        <div style={{ borderTop: `1px solid ${COLOR.borderStrong}`, padding: "10px 14px", flexShrink: 0, background: COLOR.bg }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <span style={{ fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", color: COLOR.textFaint }}>sql console</span>
            <span style={{ flex: 1 }} />
            <ActionButton label={busy ? "running…" : "run"} active onClick={runSql} />
          </div>
          <textarea
            value={sql}
            onChange={(event) => setSql(event.target.value)}
            onKeyDown={(event) => {
              if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                event.preventDefault();
                void runSql();
              }
            }}
            spellCheck={false}
            placeholder="SELECT * FROM …   (⌃↵ to run)"
            style={{
              width: "100%",
              boxSizing: "border-box",
              minHeight: 52,
              resize: "vertical",
              background: COLOR.bgInput,
              border: `1px solid ${COLOR.border}`,
              color: COLOR.green,
              fontFamily: FONT_MONO,
              fontSize: 12.5,
              padding: "8px 10px",
              outline: "none"
            }}
          />
          {execResult ? <ConsoleResult result={execResult} /> : null}
        </div>
      </div>

      {inspectorOpen && activeCell && selectedColumn && selectedRow && selectedValue !== undefined ? (
        <CellInspector
          table={selected ?? "—"}
          column={selectedColumn.name}
          columnType={selectedColumn.type}
          primaryKey={selectedColumn.pk}
          notNull={selectedColumn.notnull}
          rowNumber={offset + activeCell.row + 1}
          rowid={selectedRow.rowid}
          value={selectedValue}
          mode={mode}
          editable={selectedCellEditable}
          busy={busy}
          draft={editDraft}
          editAsNull={editAsNull}
          editRef={editRef}
          onChangeDraft={setEditDraft}
          onChangeNull={setEditAsNull}
          onBeginEdit={() => beginCellEdit()}
          onCommit={() => void commitCellEdit()}
          onCancel={cancelCellEdit}
          onClose={() => {
            if (mode === "edit") cancelCellEdit();
            setInspectorOpen(false);
            focusGrid();
          }}
        />
      ) : null}
    </div>
  );
}

function CellInspector({
  table,
  column,
  columnType,
  primaryKey,
  notNull,
  rowNumber,
  rowid,
  value,
  mode,
  editable,
  busy,
  draft,
  editAsNull,
  editRef,
  onChangeDraft,
  onChangeNull,
  onBeginEdit,
  onCommit,
  onCancel,
  onClose
}: {
  table: string;
  column: string;
  columnType: string;
  primaryKey: boolean;
  notNull: boolean;
  rowNumber: number;
  rowid: number | null;
  value: Cell;
  mode: BrowserMode;
  editable: boolean;
  busy: boolean;
  draft: string;
  editAsNull: boolean;
  editRef: RefObject<HTMLTextAreaElement>;
  onChangeDraft: (value: string) => void;
  onChangeNull: (value: boolean) => void;
  onBeginEdit: () => void;
  onCommit: () => void;
  onCancel: () => void;
  onClose: () => void;
}) {
  return (
    <aside
      aria-label="Cell inspector"
      style={{
        width: 360,
        maxWidth: "40%",
        flexShrink: 0,
        borderLeft: `1px solid ${COLOR.borderStrong}`,
        background: COLOR.bgElev,
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
        fontFamily: FONT_MONO
      }}
    >
      <div style={{ padding: "9px 12px", borderBottom: `1px solid ${COLOR.border}`, display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ color: COLOR.textFaint, fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase" }}>
          cell inspector
        </span>
        <span style={{ flex: 1 }} />
        <Pill color={mode === "edit" ? "green" : "slate"} style={{ fontSize: 9 }}>{mode === "edit" ? "EDIT" : "VIEW"}</Pill>
        <button
          type="button"
          onClick={onClose}
          title="close inspector (space)"
          style={{ border: 0, background: "transparent", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 15, cursor: "pointer", padding: "0 2px" }}
        >
          ×
        </button>
      </div>

      <div style={{ padding: "12px", borderBottom: `1px solid ${COLOR.border}`, display: "grid", gap: 7, fontSize: 11 }}>
        <div style={{ color: COLOR.text, fontSize: 12, overflowWrap: "anywhere" }}>
          <span style={{ color: COLOR.amberLink }}>{table}</span>
          <Faint>.</Faint>
          <span style={{ color: COLOR.cyan }}>{column}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 6 }}>
          <Pill color="slate" style={{ fontSize: 9 }}>{columnType || "untyped"}</Pill>
          {primaryKey ? <Pill color="amber" style={{ fontSize: 9 }}>primary key</Pill> : null}
          {notNull ? <Pill color="purple" style={{ fontSize: 9 }}>not null</Pill> : null}
        </div>
        <div style={{ display: "flex", gap: 14 }}>
          <Faint>row <span style={{ color: COLOR.textDim }}>{rowNumber}</span></Faint>
          <Faint>rowid <span style={{ color: COLOR.textDim }}>{rowid ?? "—"}</span></Faint>
        </div>
      </div>

      <div style={{ padding: "10px 12px 6px", display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ color: COLOR.textFaint, fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase" }}>value</span>
        <span style={{ flex: 1 }} />
        {value === null && mode === "nav" ? <Pill color="pink" style={{ fontSize: 9 }}>NULL</Pill> : null}
      </div>

      {mode === "edit" ? (
        <div style={{ padding: "4px 12px 12px", display: "flex", flexDirection: "column", gap: 10, minHeight: 0, flex: 1 }}>
          <textarea
            ref={editRef}
            value={draft}
            disabled={editAsNull || busy}
            onChange={(event) => onChangeDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Escape") {
                event.preventDefault();
                event.stopPropagation();
                onCancel();
              } else if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                event.preventDefault();
                event.stopPropagation();
                onCommit();
              }
            }}
            spellCheck={false}
            style={{
              flex: 1,
              minHeight: 160,
              resize: "none",
              boxSizing: "border-box",
              background: editAsNull ? COLOR.bg : COLOR.bgInput,
              border: `1px solid ${editAsNull ? COLOR.border : COLOR.green}`,
              color: editAsNull ? COLOR.textFaint : COLOR.text,
              fontFamily: FONT_MONO,
              fontSize: 12,
              lineHeight: 1.55,
              padding: "9px 10px",
              outline: "none",
              whiteSpace: "pre-wrap",
              overflowWrap: "anywhere"
            }}
          />
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <ActionButton label={editAsNull ? "✓ NULL" : "set NULL"} active={editAsNull} onClick={() => onChangeNull(!editAsNull)} />
            <span style={{ flex: 1 }} />
            <ActionButton label="cancel" onClick={onCancel} />
            <ActionButton label={busy ? "saving…" : "save  ^↵"} active disabled={busy} onClick={onCommit} />
          </div>
        </div>
      ) : (
        <div style={{ padding: "4px 12px 12px", display: "flex", flexDirection: "column", minHeight: 0, flex: 1 }}>
          <pre
            style={{
              margin: 0,
              padding: "10px",
              flex: 1,
              minHeight: 80,
              overflow: "auto",
              background: COLOR.bgInput,
              border: `1px solid ${COLOR.border}`,
              color: value === null ? COLOR.textFaint : COLOR.text,
              fontFamily: FONT_MONO,
              fontSize: 12,
              lineHeight: 1.55,
              whiteSpace: "pre-wrap",
              overflowWrap: "anywhere",
              userSelect: "text"
            }}
          >
            {value === null ? "NULL" : String(value)}
          </pre>
          <div style={{ paddingTop: 10, display: "flex", justifyContent: "flex-end" }}>
            {editable ? <ActionButton label="edit  i" active onClick={onBeginEdit} /> : <Faint style={{ fontSize: 11 }}>read-only cell</Faint>}
          </div>
        </div>
      )}
    </aside>
  );
}

function ActionButton({ label, onClick, active = false, disabled = false }: { label: string; onClick: () => void; active?: boolean; disabled?: boolean }) {
  return (
    <span
      onClick={disabled ? undefined : onClick}
      style={{
        padding: "3px 10px",
        border: `1px solid ${active ? COLOR.amber : COLOR.borderStrong}`,
        background: active ? "#241d12" : "transparent",
        color: disabled ? COLOR.textFaint : active ? COLOR.amber : COLOR.textDim,
        fontFamily: FONT_MONO,
        fontSize: 11,
        fontWeight: 600,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        whiteSpace: "nowrap"
      }}
    >
      {label}
    </span>
  );
}

const headStyle = {
  position: "sticky" as const,
  top: 0,
  background: COLOR.bgElev,
  borderRight: `1px solid ${COLOR.border}`,
  borderBottom: `1px solid ${COLOR.borderStrong}`,
  padding: "6px 8px",
  textAlign: "left" as const,
  fontFamily: FONT_MONO,
  fontSize: 11,
  fontWeight: 600,
  whiteSpace: "nowrap" as const
};

const cellStyle = {
  borderRight: `1px solid ${COLOR.border}`,
  borderBottom: `1px solid ${COLOR.border}`,
  padding: "4px 8px",
  fontFamily: FONT_MONO,
  fontSize: 12,
  whiteSpace: "nowrap" as const
};
