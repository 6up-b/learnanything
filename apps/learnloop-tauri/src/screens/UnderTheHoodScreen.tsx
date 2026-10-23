// Under the hood (UX Phase 2; docs/specs/ux_learnloop_v1.md §5.2, §7.7, §8.5,
// §10 2.2): the owner's instrument panel. A left list of tools, each under a
// plain title with its own count; on the right, the tool's screen exactly as
// it was, in its terminal voice, under that title with its old name in small
// type. Reached from ⋯ and the palette, never the top bar (Q12).
//
// This screen is only the frame. The App mounts each tool's screen as its
// child, with the same props it always had: nothing inside them changes.
import type { ReactNode } from "react";
import { uthTool, visibleUthTools, type UthToolId } from "../app/shell";
import { releaseFocusAfterPointer } from "../components/frameFocus";

export function UnderTheHoodScreen({
  tool,
  onSelectTool,
  counts,
  children
}: {
  tool: UthToolId;
  onSelectTool: (tool: UthToolId) => void;
  /** Each tool's own count, beside its name (unbadged in the nav). */
  counts: Partial<Record<UthToolId, number>>;
  children: ReactNode;
}) {
  const current = uthTool(tool);
  return (
    <div className="uth">
      <nav className="uth-list" aria-label="Under the hood" data-shell-chrome="">
        <div className="uth-list-title">Under the hood</div>
        {visibleUthTools().map((entry) => {
          const count = counts[entry.id] ?? 0;
          return (
            <button
              key={entry.id}
              type="button"
              className={entry.id === tool ? "uth-tool active" : "uth-tool"}
              aria-current={entry.id === tool ? "page" : undefined}
              aria-label={count > 0 ? `${entry.title}, ${count} waiting` : entry.title}
              title={`was ${entry.was}`}
              onClick={(event) => {
                onSelectTool(entry.id);
                releaseFocusAfterPointer(event);
              }}
            >
              <span className="uth-tool-title">{entry.title}</span>
              {count > 0 ? (
                <span className="uth-tool-count" aria-hidden="true">
                  {count}
                </span>
              ) : null}
            </button>
          );
        })}
      </nav>
      <section className="uth-pane" aria-labelledby="uth-pane-title">
        <header className="uth-pane-header">
          <h2 id="uth-pane-title">{current.title}</h2>
          <span className="uth-was">was {current.was}</span>
        </header>
        <div className="uth-pane-body">{children}</div>
      </section>
    </div>
  );
}
