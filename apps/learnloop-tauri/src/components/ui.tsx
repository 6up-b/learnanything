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
  { id: "errors", key: "8", label: "Errors" },
  { id: "doctor", key: "9", label: "Doctor" },
  { id: "maintain", key: "0", label: "Maintain" }
] as const;

export type TopTab = (typeof navTabs)[number]["id"];

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

// Fallback when the sidecar health snapshot doesn't advertise its provider
// list (older sidecar). "manual" is always appended by the menu itself.
const DEFAULT_PROVIDERS = ["codex", "deepseek_flash", "deepseek_pro"];

// The nav-bar "ai:<provider>" health chip, now a dropdown: click to switch the
// grading backend between the configured AI providers and manual (self) grading.
function AiProviderMenu({
  ready,
  label,
  manual,
  providers,
  onSelect
}: {
  ready: boolean;
  label: string;
  manual: boolean;
  providers: string[];
  onSelect?: (provider: string) => void;
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const close = () => setOpen(false);
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("click", close);
    window.addEventListener("keydown", onEscape);
    return () => {
      window.removeEventListener("click", close);
      window.removeEventListener("keydown", onEscape);
    };
  }, [open]);

  const options = [...(providers.length ? providers : DEFAULT_PROVIDERS).filter((p) => p !== "manual"), "manual"];
  const optionLabel = (p: string) => (p === "manual" ? "manual grading" : p);

  return (
    <span className="ai-menu-wrap" onClick={(event) => event.stopPropagation()}>
      <span
        className={ready || manual ? "health ok" : "health bad"}
        role="button"
        tabIndex={0}
        title={`AI provider: ${label} · click to switch`}
        style={{ cursor: onSelect ? "pointer" : undefined }}
        onClick={() => onSelect && setOpen((o) => !o)}
        onKeyDown={(event) => {
          if (onSelect && (event.key === "Enter" || event.key === " ")) {
            event.preventDefault();
            setOpen((o) => !o);
          }
        }}
      >
        ai:{label}{onSelect ? (open ? " ▴" : " ▾") : ""}
      </span>
      {open ? (
        <div className="ai-menu" role="menu">
          {options.map((provider) => (
            <button
              key={provider}
              type="button"
              role="menuitem"
              className={provider === label ? "active" : ""}
              onClick={() => {
                setOpen(false);
                onSelect?.(provider);
              }}
            >
              {provider === label ? "● " : "  "}
              {optionLabel(provider)}
            </button>
          ))}
        </div>
      ) : null}
    </span>
  );
}

export function TerminalFrame({
  active,
  onTab,
  children,
  aiReady,
  aiLabel,
  aiManual = false,
  aiProviders = [],
  onSelectAiProvider,
  vaultRoot,
  onSelectVault
}: {
  active: TopTab;
  onTab: (tab: TopTab) => void;
  children: ReactNode;
  aiReady: boolean;
  aiLabel: string;
  aiManual?: boolean;
  aiProviders?: string[];
  onSelectAiProvider?: (provider: string) => void;
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
            <AiProviderMenu
              ready={aiReady}
              label={aiLabel}
              manual={aiManual}
              providers={aiProviders}
              onSelect={onSelectAiProvider}
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
