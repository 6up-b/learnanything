// ⋯ → Keyboard & help (UX Phase 2; docs/specs/ux_learnloop_v1.md §5.1, §5.4).
// Generated from the shared key map (app/keymap.ts), so it never drifts from
// what the keys do. Each screen's own keys stay on its key bar.
import { useEffect, useRef } from "react";
import { CLASSIC_REPLACEMENTS, SCOPED_OVERRIDES, shellBindings } from "../app/keymap";
import type { ShellMode } from "../app/shell";

export function KeyboardHelp({ shell, onClose }: { shell: ShellMode; onClose: () => void }) {
  const ref = useRef<HTMLElement | null>(null);
  useEffect(() => {
    ref.current?.focus();
  }, []);
  const rows = shellBindings(shell);
  const classic = shellBindings("classic");
  return (
    <div className="keys-help-backdrop" onClick={onClose}>
      <section
        ref={ref}
        className="keys-help"
        role="dialog"
        aria-modal="true"
        aria-label="Keyboard & help"
        tabIndex={-1}
        onClick={(event) => event.stopPropagation()}
        onKeyDown={(event) => {
          // Modal: the screen beneath keeps its keys to itself meanwhile.
          event.stopPropagation();
          if (event.key === "Escape") onClose();
        }}
      >
        <header className="keys-help-header">
          <h2>Keyboard & help</h2>
          <button type="button" className="keys-help-close" aria-label="Close" onClick={onClose}>
            ×
          </button>
        </header>
        <p className="keys-help-note">These work everywhere. Each screen's own keys are on the bar at its bottom.</p>
        <table className="keys-help-table">
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td>
                  <kbd>{row.keys}</kbd>
                </td>
                <td>{row.label}</td>
              </tr>
            ))}
            <tr>
              <td>
                <kbd>Esc</kbd>
              </td>
              <td>Back one step, or close what is open</td>
            </tr>
          </tbody>
        </table>
        {shell === "simple" ? (
          <>
            <h3>Keys that moved</h3>
            <table className="keys-help-table">
              <tbody>
                {classic
                  .filter((row) => CLASSIC_REPLACEMENTS[row.id])
                  .map((row) => (
                    <tr key={row.id}>
                      <td>
                        <kbd>{row.keys}</kbd> <span className="keys-help-was">was {row.label}</span>
                      </td>
                      <td>{CLASSIC_REPLACEMENTS[row.id]}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
            {SCOPED_OVERRIDES.map((override) => (
              <p key={override.file} className="keys-help-note">
                <kbd>{override.keys}</kbd> in {override.where}: {override.note}
              </p>
            ))}
            <p className="keys-help-note">
              Type <kbd>&gt;</kbd> in the palette for learnloop commands (<kbd>&gt; doctor</kbd>). The old tabs are under ⋯ → Under the
              hood. To go back to them for now, set <code>shell = "classic"</code> under <code>[ui]</code> in the library's
              learnloop.toml.
            </p>
          </>
        ) : null}
      </section>
    </div>
  );
}
