import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { open as openDialog } from "@tauri-apps/plugin-dialog";

export const navTabs = [
  { id: "start", key: "1", label: "Start" },
  { id: "today", key: "2", label: "Today" },
  { id: "graph", key: "3", label: "Graph" },
  { id: "ingest", key: "4", label: "Ingest" },
  { id: "proposals", key: "5", label: "Proposals" },
  { id: "registry", key: "6", label: "Registry" },
  { id: "library", key: "7", label: "Library" },
  { id: "golden", key: "8", label: "Golden Path" },
  { id: "reader", key: "9", label: "Reader" },
  { id: "maintain", key: "0", label: "Maintain" }
] as const;

// `errors` is an overlay-only route used by `learnloop diff`, not a visible
// tab; `settings` is reached via the nav-status chip (or Alt+S), not navTabs.
export type TopTab = (typeof navTabs)[number]["id"] | "errors" | "settings";

function getAppWindow(): ReturnType<typeof getCurrentWindow> | null {
  try {
    return getCurrentWindow();
  } catch {
    return null;
  }
}

export function Titlebar() {
  const appWindow = useMemo(getAppWindow, []);
  const [maximized, setMaximized] = useState(false);

  useEffect(() => {
    if (!appWindow) return;
    let unlisten: (() => void) | undefined;
    const sync = () => appWindow.isMaximized().then(setMaximized).catch(() => {});
    sync();
    appWindow.onResized(sync).then((fn) => { unlisten = fn; }).catch(() => {});
    return () => unlisten?.();
  }, [appWindow]);

  return (
    <div className="titlebar" data-tauri-drag-region>
      <span className="titlebar-brand" data-tauri-drag-region>LearnLoop</span>
      <div className="window-controls">
        <button className="win-btn" type="button" aria-label="Minimize" onClick={() => appWindow?.minimize()}>
          <svg width="11" height="11" viewBox="0 0 11 11"><rect x="1" y="5" width="9" height="1" /></svg>
        </button>
        <button className="win-btn" type="button" aria-label={maximized ? "Restore" : "Maximize"} onClick={() => appWindow?.toggleMaximize()}>
          {maximized ? (
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none" stroke="currentColor">
              <rect x="1.5" y="3" width="6" height="6" /><path d="M3 3V1.5h6V7.5H7.5" />
            </svg>
          ) : (
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none" stroke="currentColor"><rect x="1.5" y="1.5" width="8" height="8" /></svg>
          )}
        </button>
        <button className="win-btn close" type="button" aria-label="Close" onClick={() => appWindow?.close()}>
          <svg width="11" height="11" viewBox="0 0 11 11" stroke="currentColor"><path d="M1 1l9 9M10 1l-9 9" /></svg>
        </button>
      </div>
    </div>
  );
}

// Show only the trailing folders of a vault path so the long
// "C:\Users\…\OneDrive\…" prefix doesn't dominate the nav bar. A leading "…"
// marks that the path was shortened; the full path stays in the title tooltip.
export function truncateVaultPath(path: string, segments = 3): string {
  const sep = path.includes("\\") ? "\\" : "/";
  const parts = path.split(/[\\/]+/).filter(Boolean);
  if (parts.length <= segments) return path;
  return `…${sep}${parts.slice(-segments).join(sep)}`;
}

// The green vault path in the nav bar. Clicking it opens the OS folder picker.
function VaultPath({ root, onSelect }: { root: string; onSelect: (path: string) => void }) {
  const pick = async () => {
    const selected = await openDialog({ directory: true, multiple: false, defaultPath: root });
    if (typeof selected === "string" && selected !== root) {
      onSelect(selected);
    }
  };

  return (
    <span
      className="vault-path"
      role="button"
      tabIndex={0}
      title={`${root} · click to change vault`}
      onClick={() => void pick()}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          void pick();
        }
      }}
    >
      {truncateVaultPath(root)}
    </span>
  );
}

// The nav-bar settings chip: a gear plus the Alt+S shortcut. It keeps the
// at-a-glance AI ready/unready color and opens the Settings screen, which
// replaced the old inline provider dropdown.
function SettingsChip({
  ready,
  manual,
  active,
  onOpen
}: {
  ready: boolean;
  manual: boolean;
  active: boolean;
  onOpen: () => void;
}) {
  return (
    <button
      type="button"
      className={`nav-settings ${ready || manual ? "health ok" : "health bad"}${active ? " open" : ""}`}
      title="open settings (Alt+S)"
      onClick={onOpen}
    >
      <span className="nav-settings-gear">⚙</span>
      <span className="nav-settings-key">[Alt+S]</span>
    </button>
  );
}

export function TerminalFrame({
  active,
  onTab,
  children,
  aiReady,
  aiManual = false,
  vaultRoot,
  onSelectVault
}: {
  active: TopTab;
  onTab: (tab: TopTab) => void;
  children: ReactNode;
  aiReady: boolean;
  aiManual?: boolean;
  vaultRoot?: string | null;
  onSelectVault: (path: string) => void;
}) {
  return (
    <div className="desktop-shell">
      <div className="terminal-frame">
        <Titlebar />
        <nav className="top-nav">
          {navTabs.map((tab) => (
            <button
              key={tab.id}
              className={tab.id === active ? "active" : ""}
              onClick={() => onTab(tab.id)}
              type="button"
            >
              <span>[{tab.key}]</span>{tab.label}
            </button>
          ))}
          <div className="nav-status">
            {vaultRoot ? <VaultPath root={vaultRoot} onSelect={onSelectVault} /> : null}
            <SettingsChip
              ready={aiReady}
              manual={aiManual}
              active={active === "settings"}
              onOpen={() => onTab("settings")}
            />
          </div>
        </nav>
        <main className="frame-body">{children}</main>
      </div>
    </div>
  );
}

export function SectionHeader({ children }: { children: ReactNode }) {
  return <div className="section-header">{children}</div>;
}

export function Pill({ children, tone = "slate" }: { children: ReactNode; tone?: string }) {
  return <span className={`pill ${tone}`}>{children}</span>;
}

export function Card({
  children,
  focused = false,
  onClick
}: {
  children: ReactNode;
  focused?: boolean;
  onClick?: () => void;
}) {
  return (
    <div className={`card ${focused ? "focused" : ""}`} onClick={onClick}>
      {children}
    </div>
  );
}

export function EntityLink({
  id,
  onInspect,
  children,
  style
}: {
  id: string;
  onInspect: (id: string) => void;
  children?: ReactNode;
  style?: CSSProperties;
}) {
  return (
    <span
      className="entity-link"
      style={style}
      role="button"
      tabIndex={0}
      onClick={(event) => {
        event.stopPropagation();
        onInspect(id);
      }}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          event.stopPropagation();
          onInspect(id);
        }
      }}
    >
      {children ?? id}
    </span>
  );
}

const SPINNER_FRAMES = "⣾⣽⣻⢿⡿⣟⣯⣷";

function Spinner() {
  const [frame, setFrame] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setFrame((f) => (f + 1) % SPINNER_FRAMES.length), 80);
    return () => clearInterval(id);
  }, []);
  return <span className="spinner">{SPINNER_FRAMES[frame]}</span>;
}

export function EmptyPlaceholder({ title }: { title: string }) {
  return (
    <div className="placeholder-screen">
      <div className="placeholder-title"><Spinner /> {title}</div>
    </div>
  );
}

export function KeyBar({ keys, right }: { keys: Array<{ key: string; label: string }>; right?: ReactNode }) {
  return (
    <div className="keybar">
      {keys.map((item) => (
        <span key={item.key}><b>{item.key}</b> {item.label}</span>
      ))}
      {right ? <span style={{ marginLeft: "auto" }}>{right}</span> : null}
    </div>
  );
}
