// UX Phase 2 fix round 4: what the shell chrome's key isolation cannot reach.
//
// app/ShellChromeRoot.tsx stops a key pressed on a chrome control before any
// window or document listener in the bubble phase sees it. A listener
// registered for the CAPTURE phase on window or document runs before the
// event reaches any element, so no element can stop it. These are pinned
// here, each with why a key from the chrome does no harm there. A new one
// fails this test until it is reviewed and listed.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { expect, it } from "vitest";

const CAPTURE_LISTENERS: Record<string, string> = {
  "components/SessionFinishHud.tsx": "the session finish card: an overlay over the screen, its keys while it shows",
  "components/AskOverlay.tsx": "the ask overlay: modal, its box has the focus",
  "components/pdfSelection/usePdfSelection.ts": "Esc clears a PDF marquee selection; harmless from anywhere",
  "components/QuickAddDialog.tsx": "a modal dialog with the focus",
  "components/InspectorOverlay.tsx": "the inspector overlay: modal",
  "screens/reader/bareAlt.ts": "watches a bare Alt press (no action on Enter, Space or Esc)",
  "components/OpenInSource.tsx": "a modal",
  "components/StudyMapBriefWizard.tsx": "a modal wizard",
  "components/NewVaultWizard.tsx": "a modal wizard",
  "components/WriteCardDialog.tsx": "a modal dialog",
  "screens/RepairScreen.tsx": "the repair overlay: modal",
  "screens/reader/useIntentBox.ts": "the Reader's intent box, open only over a selection",
  "screens/LibraryScreen.tsx": "Ctrl/Cmd+F find in the open note (a modified key, the shell lets those through anyway)",
  "screens/reader/useReaderInquiry.ts": "the Reader's inquiry box (open over a selection) and its Ctrl/Cmd+F find",
  "screens/ReaderScreen.tsx": "the Reader's modal capture surfaces"
};

const SRC = join(__dirname, "..");

function sourceFiles(dir: string, rel = ""): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    const relPath = rel ? `${rel}/${name}` : name;
    if (statSync(path).isDirectory()) out.push(...sourceFiles(path, relPath));
    else if (/\.tsx?$/.test(name) && !/\.test\.tsx?$/.test(name) && !name.endsWith(".d.ts")) out.push(relPath);
  }
  return out;
}

it("pins every capture-phase key listener on window or document, with why the chrome's keys are harmless there", () => {
  const found = new Set<string>();
  for (const file of sourceFiles(SRC)) {
    const text = readFileSync(join(SRC, file), "utf8");
    if (/(?:window|document)\.addEventListener\(\s*"key(?:down|up|press)"\s*,\s*[^)]*,\s*(?:true|\{\s*capture:\s*true\s*\})\s*\)/.test(text)) found.add(file);
  }
  expect([...found].sort()).toEqual(Object.keys(CAPTURE_LISTENERS).sort());
});
