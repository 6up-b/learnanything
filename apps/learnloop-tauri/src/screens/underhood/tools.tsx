// The Under-the-hood tools that had no tab of their own (UX Phase 2;
// docs/specs/ux_learnloop_v1.md §5.2). Each is a thin entry point to a screen
// or overlay that already exists, unchanged: the SQLite browser, the
// inspector, a calibration session, the mistake history, Settings' AI routes.
// They speak the owner's terminal voice, like the rest of Under the hood.
import { lazy, useState, type ReactNode } from "react";
import { api } from "../../api/client";
import { TAG } from "../../api/queryTags";
import { useCachedQuery } from "../../api/useCachedQuery";
import type { SessionSnapshot, VaultTreeNode } from "../../api/dto";
import { errorMessage } from "../../errors";

const SqliteBrowser = lazy(() => import("../SqliteBrowser").then((module) => ({ default: module.SqliteBrowser })));

function ToolNote({ children }: { children: ReactNode }) {
  return <div className="uth-note">{children}</div>;
}

/** The library's own database file, as the vault tree lists it. */
export function stateDatabasePath(nodes: VaultTreeNode[]): string | null {
  let fallback: string | null = null;
  const walk = (list: VaultTreeNode[]): string | null => {
    for (const node of list) {
      if (node.type === "file" && node.name === "state.sqlite") return node.path;
      if (node.type === "file" && node.kind === "sqlite" && fallback === null) fallback = node.path;
      if (node.children) {
        const nested = walk(node.children);
        if (nested) return nested;
      }
    }
    return null;
  };
  return walk(nodes) ?? fallback;
}

/** Data: the SQLite browser on this library's database (was: Library → state.sqlite). */
export function DataTool({ onError }: { onError: (message: string) => void }) {
  const tree = useCachedQuery(["get_vault_tree"], () => api.getVaultTree(), { tags: [TAG.library] });
  if (!tree.data) {
    return <ToolNote>{tree.error ? `could not read the vault tree: ${tree.error.message}` : "reading the vault tree…"}</ToolNote>;
  }
  const path = stateDatabasePath(tree.data.tree);
  if (!path) return <ToolNote>no database file in this library's tree.</ToolNote>;
  return <SqliteBrowser path={path} onError={onError} />;
}

/** Inspector: `learnloop show <id>` (the inspector overlay, as from the palette). */
export function InspectorTool({ recentIds, onInspect }: { recentIds: string[]; onInspect: (id: string) => void }) {
  const [id, setId] = useState("");
  const open = (value: string) => {
    const trimmed = value.trim();
    if (trimmed) onInspect(trimmed);
  };
  return (
    <div className="uth-form">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          open(id);
        }}
      >
        <label>
          <span className="uth-faint">learnloop show</span>{" "}
          <input value={id} onChange={(event) => setId(event.target.value)} placeholder="any id: lo_…, pi_…, an attempt, an error" spellCheck={false} />
        </label>{" "}
        <button type="submit" className="uth-button">
          open
        </button>
      </form>
      {recentIds.length > 0 ? (
        <div className="uth-recent">
          <span className="uth-faint">on screen recently:</span>
          {recentIds.slice(0, 12).map((recent) => (
            <button key={recent} type="button" className="uth-link" onClick={() => onInspect(recent)}>
              {recent}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

/** Calibration: a full calibration session (`calibrate`), batched diagnostic
 *  blocks over all open episodes. The palette's `> calibrate <goal_id>` still
 *  takes a goal. */
export function CalibrationTool({
  session,
  onOpenCalibration,
  onError
}: {
  session: SessionSnapshot | null;
  onOpenCalibration: (calibrationSessionId: string) => void;
  onError: (message: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  if (!session) {
    return <ToolNote>start a session first — calibration attaches to the active practice session (Today → Begin).</ToolNote>;
  }
  return (
    <div className="uth-form">
      <ToolNote>batched diagnostic blocks over every open probe episode. for one goal: <code>&gt; calibrate &lt;goal_id&gt;</code> in the palette.</ToolNote>
      <button
        type="button"
        className="uth-button"
        disabled={busy}
        onClick={() => {
          setBusy(true);
          api
            .startCalibrationSession({ sessionId: session.sessionId, goalId: null, timeBudgetMinutes: null })
            .then((progress) => onOpenCalibration(progress.calibrationSessionId))
            .catch((error) => onError(errorMessage(error, "Could not start a calibration session.")))
            .finally(() => setBusy(false));
        }}
      >
        {busy ? "starting…" : "start calibration"}
      </button>
    </div>
  );
}

/** Mistake history: the `learnloop diff` overlay (was the Review screen). */
export function MistakesTool({ onOpen }: { onOpen: () => void }) {
  return (
    <div className="uth-form">
      <ToolNote>the learner-model change ledger opens over this screen.</ToolNote>
      <button type="button" className="uth-button" onClick={onOpen}>
        open mistake history
      </button>
    </div>
  );
}

/** Spend & AI routes: Settings holds them until Phase 6 gives this a page. */
export function SpendTool({ onOpenSettings }: { onOpenSettings: () => void }) {
  return (
    <div className="uth-form">
      <ToolNote>
        spend caps, per-route models and provider limits live in Settings for now. from a terminal: <code>learnloop ai status</code>.
      </ToolNote>
      <button type="button" className="uth-button" onClick={onOpenSettings}>
        open settings
      </button>
    </div>
  );
}
