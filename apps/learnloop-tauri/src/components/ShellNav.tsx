// The simple shell's nav (UX Phase 2; docs/specs/ux_learnloop_v1.md §5.1,
// §7.8, §10 2.1):
//
//   Today   Library   Reader   Progress              [+ Add]  ^K  ⋯
//
// Four places with plain labels (their Alt keys in the tooltip, Q10), the one
// verb to start, the palette, and ⋯ for the corner of the machine: Settings,
// Under the hood, Switch library and Keyboard & help. No badges in the bar
// (§5.2); the vault chip and the settings chip move into ⋯ (§7.8). One plain
// line appears only when grading, which the learner uses, isn't working.
import { useEffect, useMemo, useRef, useState } from "react";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import { listRecentVaults, samePath, vaultName, vaultNameWithParent } from "../app/recentVaults";
import { PLACES, type Place } from "../app/shell";
import { focusFrameBodyAfterPointer } from "./frameFocus";

export interface SimpleNavProps {
  /** The place on screen; "underhood" lights ⋯. */
  active: Place | "underhood" | null;
  onPlace: (place: Place) => void;
  onPalette: () => void;
  onSettings: () => void;
  onUnderTheHood: () => void;
  onKeyboardHelp: () => void;
  onNewLibrary?: () => void;
  /** Grading is down (not a manual choice, and an AI is connected). */
  gradingTrouble?: boolean;
  onFixGrading?: () => void;
}

export function SimpleNav({
  active,
  onPlace,
  onPalette,
  onSettings,
  onUnderTheHood,
  onKeyboardHelp,
  onNewLibrary,
  gradingTrouble = false,
  onFixGrading,
  vaultRoot,
  onSelectVault,
  onAdd
}: SimpleNavProps & {
  vaultRoot?: string | null;
  onSelectVault: (path: string) => void;
  onAdd?: () => void;
}) {
  return (
    <nav className="top-nav simple-nav" aria-label="Places" data-shell-chrome="">
      {PLACES.map((place) => {
        const current = place.id === active;
        return (
          <button
            key={place.id}
            type="button"
            className={current ? "active" : ""}
            aria-current={current ? "page" : undefined}
            title={`${place.label} (Alt+${place.key})`}
            onClick={(event) => {
              onPlace(place.id);
              focusFrameBodyAfterPointer(event);
            }}
          >
            {place.label}
          </button>
        );
      })}
      <div className="nav-status">
        {gradingTrouble ? (
          <button type="button" className="nav-trouble" onClick={onFixGrading}>
            Grading isn't working · Fix
          </button>
        ) : null}
        {onAdd ? (
          <button type="button" className="nav-add" onClick={onAdd} title="Add a book, paper or video (Ctrl+O)">
            + Add
          </button>
        ) : null}
        <button type="button" className="nav-palette" onClick={onPalette} title="Commands (Ctrl+K)">
          ^K
        </button>
        <MoreMenu
          underTheHood={active === "underhood"}
          vaultRoot={vaultRoot ?? null}
          onSelectVault={onSelectVault}
          onSettings={onSettings}
          onUnderTheHood={onUnderTheHood}
          onKeyboardHelp={onKeyboardHelp}
          onNewLibrary={onNewLibrary}
        />
      </div>
    </nav>
  );
}

function MoreMenu({
  underTheHood,
  vaultRoot,
  onSelectVault,
  onSettings,
  onUnderTheHood,
  onKeyboardHelp,
  onNewLibrary
}: {
  underTheHood: boolean;
  vaultRoot: string | null;
  onSelectVault: (path: string) => void;
  onSettings: () => void;
  onUnderTheHood: () => void;
  onKeyboardHelp: () => void;
  onNewLibrary?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const buttonRef = useRef<HTMLButtonElement | null>(null);

  // Read fresh each time it opens; the current library is always listed.
  const recents = useMemo(() => {
    if (!open) return [];
    const list = listRecentVaults();
    if (!vaultRoot) return list;
    return list.some((path) => samePath(path, vaultRoot)) ? list : [vaultRoot, ...list];
  }, [open, vaultRoot]);
  const labelFor = useMemo(() => {
    const counts = new Map<string, number>();
    for (const path of recents) counts.set(vaultName(path), (counts.get(vaultName(path)) ?? 0) + 1);
    return (path: string) => ((counts.get(vaultName(path)) ?? 0) > 1 ? vaultNameWithParent(path) : vaultName(path));
  }, [recents]);

  useEffect(() => {
    if (!open) return;
    const onDocMouseDown = (event: MouseEvent) => {
      if (!wrapRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDocMouseDown, true);
    return () => document.removeEventListener("mousedown", onDocMouseDown, true);
  }, [open]);

  const choose = (action: () => void, event: { detail: number }) => {
    setOpen(false);
    action();
    focusFrameBodyAfterPointer(event);
  };

  const openAnother = async () => {
    setOpen(false);
    const selected = await openDialog({ directory: true, multiple: false, defaultPath: vaultRoot ?? undefined });
    if (typeof selected === "string" && !(vaultRoot && samePath(selected, vaultRoot))) onSelectVault(selected);
  };

  return (
    <div
      className="more-menu-wrap"
      ref={wrapRef}
      onKeyDown={(event) => {
        // Every key pressed here stays in the shell's chrome: the nav is a
        // `data-shell-chrome` part (app/ShellChromeRoot.tsx), so Enter and
        // Space activate the row and Esc closes the menu, and no screen sees
        // them. Fix round 4 generalized this menu's own Enter/Space stop to
        // all of the chrome.
        if (event.key === "Escape" && open) {
          setOpen(false);
          buttonRef.current?.focus();
        }
      }}
    >
      <button
        ref={buttonRef}
        type="button"
        className={underTheHood ? "nav-more active" : "nav-more"}
        aria-haspopup="menu"
        aria-expanded={open}
        title="Settings, Under the hood, libraries, keys"
        onClick={() => setOpen((value) => !value)}
      >
        ⋯
      </button>
      {open ? (
        <div className="vault-menu more-menu" role="menu">
          <button type="button" role="menuitem" onClick={(event) => choose(onSettings, event)}>
            {/* No <span>: the nav's ".top-nav button span" rule (the classic key
                hints) would shrink and dim it. */}
            Settings <kbd>Ctrl+,</kbd>
          </button>
          <button type="button" role="menuitem" className={underTheHood ? "active" : ""} onClick={(event) => choose(onUnderTheHood, event)}>
            Under the hood
          </button>
          <div className="more-menu-label" role="presentation">
            Switch library
          </div>
          {recents.map((path) => {
            const current = vaultRoot ? samePath(path, vaultRoot) : false;
            return (
              <button
                key={path}
                type="button"
                role="menuitem"
                title={path}
                className={current ? "active more-menu-library" : "more-menu-library"}
                aria-current={current ? "true" : undefined}
                onClick={(event) => choose(() => {
                  if (!current) onSelectVault(path);
                }, event)}
              >
                {labelFor(path)}
              </button>
            );
          })}
          <button type="button" role="menuitem" className="more-menu-library" onClick={() => void openAnother()}>
            Open another library…
          </button>
          {onNewLibrary ? (
            <button type="button" role="menuitem" className="more-menu-library" onClick={(event) => choose(onNewLibrary, event)}>
              New library…
            </button>
          ) : null}
          <button type="button" role="menuitem" className="more-menu-sep" onClick={(event) => choose(onKeyboardHelp, event)}>
            Keyboard & help
          </button>
        </div>
      ) : null}
    </div>
  );
}
