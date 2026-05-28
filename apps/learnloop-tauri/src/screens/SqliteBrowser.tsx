import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { SqliteExecResult, SqliteTableInfo, SqliteTableSnapshot } from "../api/dto";
import { COLOR, Faint, FONT_MONO, Pill } from "../components/term";

const PAGE = 200;

type Cell = string | number | boolean | null;

function CellText({ value }: { value: Cell }) {
  if (value === null) return <span style={{ color: COLOR.textFaint, fontStyle: "italic" }}>NULL</span>;
  if (typeof value === "number") return <span style={{ color: COLOR.amber }}>{String(value)}</span>;
  if (typeof value === "boolean") return <span style={{ color: COLOR.pink }}>{String(value)}</span>;
  return <span style={{ color: COLOR.text }}>{value}</span>;
}

// One inline-editable grid cell. Click to edit (when editable); Enter / blur commits.
function GridCell({
  value,
  editable,
  onCommit
}: {
  value: Cell;
  editable: boolean;
  onCommit: (next: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");

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
    cursor: editable ? "text" : "default"
  };

  if (editing) {
    return (
      <td style={{ ...tdStyle, padding: 0 }}>
        <input
          autoFocus
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onBlur={() => {
            setEditing(false);
            onCommit(draft);
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              (event.target as HTMLInputElement).blur();
            } else if (event.key === "Escape") {
              event.preventDefault();
              setEditing(false);
            }
          }}
          style={{
            width: "100%",
            boxSizing: "border-box",
            background: COLOR.bgInput,
            border: `1px solid ${COLOR.amber}`,
            color: COLOR.text,
            fontFamily: FONT_MONO,
            fontSize: 12,
            padding: "3px 7px",
            outline: "none"
          }}
        />
      </td>
    );
  }
  return (
    <td
      style={tdStyle}
      title={value === null ? "NULL" : String(value)}
      onClick={() => {
        if (!editable) return;
        setDraft(value === null ? "" : String(value));
        setEditing(true);
      }}
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

  const updateCell = async (rowid: number, column: string, value: string) => {
    if (!selected || busy) return;
    setBusy(true);
    try {
      await api.sqliteUpdateCell(path, selected, rowid, column, value === "" ? null : value);
      await loadTable(selected, offset);
    } catch (error) {
      onError((error as Error).message);
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

  return (
    <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
      {/* Table list */}
      <div style={{ width: 200, flexShrink: 0, borderRight: `1px solid ${COLOR.border}`, overflowY: "auto" }}>
        <div style={{ padding: "8px 12px", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", color: COLOR.textFaint, borderBottom: `1px solid ${COLOR.border}` }}>
          tables · {tables.length}
        </div>
        {tables.map((table) => (
          <div
            key={table.name}
            onClick={() => { setSelected(table.name); setOffset(0); }}
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

        <div style={{ flex: 1, overflow: "auto", minHeight: 0 }}>
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
                        editable={editable && row.rowid !== null}
                        onCommit={(next) => { if (row.rowid !== null) void updateCell(row.rowid, data.columns[cellIndex].name, next); }}
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
    </div>
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
