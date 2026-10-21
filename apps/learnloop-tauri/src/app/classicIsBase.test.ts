// UX Phase 2 fix round 4 (whole-stage verify 20261021-134216-8mdDfN item 2):
// classic is base by construction.
//
// Every file this stage changed under screens/ and components/ is listed
// here, each changed behaviour with how classic stays base's:
//   - "simple-only": the behaviour runs only in the simple shell. `evidence`
//     names the gate in the file (a `simpleShell()` branch, the
//     `screenLeavesKey` guard, which answers false in classic, a prop only the
//     simple shell passes, or a component only the simple shell mounts) and
//     `classicVerbatim` the base code the classic branch still runs, which
//     must appear unchanged in both this tree and base (c80c54cbb).
//   - "shared": it runs in both shells, with the reason that is safe.
// The list must match the stage's diff against base exactly (git, when the
// base commit is reachable), so a new change cannot land unlisted.
import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const BASE = "c80c54cbb";
const SRC = join(__dirname, "..");
const APP_ROOT = join(SRC, "..");
const REPO_PREFIX = "apps/learnloop-tauri/src/";
// Paths as git prints them relative to the app root (`--relative`, ls-files).
const LOCAL_PREFIX = "src/";

interface Behaviour {
  behaviour: string;
  kind: "simple-only" | "shared";
  /** Each must match the file (or `in`, when the gate lives elsewhere). */
  evidence: RegExp[];
  in?: string;
  /** Base code the classic branch runs, present unchanged in both trees. */
  classicVerbatim?: string[];
  reason?: string;
}

const APP = "app/App.tsx";

export const STAGE_CHANGES: Record<string, Behaviour[]> = {
  "components/CommandPalette.tsx": [
    {
      behaviour: "the palette: plain commands first, the learnloop shell behind >, reset on opening, chrome part",
      kind: "simple-only",
      evidence: [/if \(props\.shell === "simple"\) return <SimpleCommandPalette \{\.\.\.props\} \/>;/, /return <ClassicCommandPalette \{\.\.\.base\} \/>;/],
      reason: "ClassicCommandPalette is base's component verbatim (checked below)"
    }
  ],
  "components/KeyboardHelp.tsx": [
    {
      behaviour: "Keyboard & help (new)",
      kind: "simple-only",
      in: APP,
      evidence: [/onKeyboardHelp: \(\) => setKeysHelpOpen\(true\)/, /\{ id: "keys", label: "Keyboard & help"/],
      reason: "opened only from the simple nav's ⋯ and the simple palette's plain commands"
    }
  ],
  "components/NoticeHost.tsx": [
    { behaviour: "the notice host (new)", kind: "simple-only", in: APP, evidence: [/\{simple && !settingsOpen \? <NoticeHost /] }
  ],
  "components/OutlineAndPlan.tsx": [
    {
      behaviour: "Esc closes the build-plan modal",
      kind: "simple-only",
      evidence: [/const escCloses = simpleShell\(\);/, /if \(escCloses\) onClose\(\);/, /escCloses \? "esc close" : "esc back"/],
      classicVerbatim: ['if (step === "plan") setStep("outline");', "else onClose();"]
    }
  ],
  "components/ShellNav.tsx": [
    {
      behaviour: "the simple nav (new)",
      kind: "simple-only",
      in: "components/ui.tsx",
      evidence: [/if \(shell === "simple" && simpleNav\) \{/]
    }
  ],
  "components/ui.tsx": [
    {
      behaviour: "TerminalFrame draws the simple nav",
      kind: "simple-only",
      evidence: [/shell = "classic",/, /if \(shell === "simple" && simpleNav\) \{/],
      reason: "classic is the default and falls through to base's frame"
    },
    {
      behaviour: 'TopTab gains "underhood"',
      kind: "shared",
      evidence: [/\| "errors" \| "settings" \| "underhood";/],
      reason: "a type: no tab, key or screen of classic sets it"
    }
  ],
  "screens/FeedbackScreen.tsx": [
    { behaviour: "modified keys are the shell's", kind: "simple-only", evidence: [/if \(screenLeavesKey\(event\)\) return;/], reason: "screenLeavesKey is false in classic (keymap.test.ts)" }
  ],
  "screens/KnowledgeMapScreen.tsx": [
    {
      behaviour: "one error per failed feed, with its source and retry",
      kind: "simple-only",
      evidence: [/const simple = simpleShell\(\);/, /useReportQueryError\(snapshotQuery, onError, simple\);/, /if \(simple\) return;/],
      classicVerbatim: [
        "const loadError = snapshotQuery.error ?? historyQuery.error ?? decayQuery.error;",
        "if (loadError) onError(loadError.message);"
      ]
    }
  ],
  "screens/LibraryScreen.tsx": [
    {
      behaviour: "one error per failed read, with its source and retry",
      kind: "simple-only",
      evidence: [/const simple = simpleShell\(\);/, /useReportQueryError\(treeQuery, onError, simple\);/, /if \(simple\) return;/],
      classicVerbatim: [
        "const loadError = treeQuery.error ?? proposalsQuery.error ?? sourceSetsQuery.error;",
        "if (loadError) onError(loadError.message);"
      ]
    },
    {
      behaviour: "databases leave the file tree; the first file is a note",
      kind: "simple-only",
      evidence: [/if \(!data \|\| shellMode\(\) === "classic"\) return data;/, /if \(shell === "classic"\) return firstFilePath\(nodes\);/]
    },
    { behaviour: "modified keys are the shell's", kind: "simple-only", evidence: [/if \(screenLeavesKey\(event\)\) return;/] },
    { behaviour: "onError takes an ErrorReport", kind: "shared", evidence: [/onError: ReportError;/], reason: "a type: classic's onError ignores the report and shows base's toast" }
  ],
  "screens/ProposalsScreen.tsx": [
    { behaviour: "repeat marks", kind: "simple-only", evidence: [/snapshot && simpleShell\(\) \? repeatedPendingProposals/] },
    { behaviour: "modified keys are the shell's", kind: "simple-only", evidence: [/if \(screenLeavesKey\(event\)\) return;/] }
  ],
  "screens/reader/ReaderWorkingPosture.tsx": [
    {
      behaviour: "the palette's ask waits in the workbench",
      kind: "simple-only",
      in: "screens/ReaderScreen.tsx",
      evidence: [/askWaiting=\{askWaitsForWork \?/],
      reason: "set only by askRequest, which the App passes only in the simple shell"
    }
  ],
  "screens/ReaderScreen.tsx": [
    {
      behaviour: "the palette's ask opens Ask from every posture",
      kind: "simple-only",
      in: APP,
      evidence: [/\{\.\.\.\(simple \? \{ askRequest: readerAskRequest \} : \{\}\)\}/],
      reason: "without askRequest (classic) the effects return at once"
    }
  ],
  "screens/SqliteBrowser.tsx": [
    {
      behaviour: "Data's read-only gate",
      kind: "simple-only",
      evidence: [/editGate = false/, /useState\(!editGate\)/],
      reason: "only Under the hood → Data passes editGate; without it every edit path is base's"
    },
    { behaviour: "modified keys are not grid keys", kind: "simple-only", evidence: [/if \(simpleShell\(\) && \(event\.ctrlKey \|\| event\.metaKey \|\| event\.altKey\)\) return;/] }
  ],
  "screens/TodayScreen.tsx": [
    { behaviour: "modified keys are the shell's", kind: "simple-only", evidence: [/if \(screenLeavesKey\(event\)\) return;/] }
  ],
  "screens/UnderTheHoodScreen.tsx": [
    { behaviour: "Under the hood (new)", kind: "simple-only", in: APP, evidence: [/if \(simple && placeOfTab\(tab\) === "underhood"\) \{/] }
  ],
  "screens/underhood/tools.tsx": [
    { behaviour: "Under the hood's tools (new)", kind: "simple-only", in: APP, evidence: [/if \(simple && placeOfTab\(tab\) === "underhood"\) \{/] }
  ]
};

function read(path: string): string {
  return readFileSync(join(SRC, path), "utf8");
}

function git(command: string): string | null {
  try {
    return execSync(`git ${command}`, { cwd: APP_ROOT, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
  } catch {
    return null;
  }
}

const baseReachable = git(`cat-file -e ${BASE}^{commit}`) !== null;

function baseFile(path: string): string {
  const text = git(`show ${BASE}:${REPO_PREFIX}${path}`);
  if (text === null) throw new Error(`${path} is not in ${BASE}`);
  return text;
}

describe("classic is base by construction", () => {
  it("names a gate for every simple-only behaviour, and a reason for every shared one", () => {
    for (const [file, behaviours] of Object.entries(STAGE_CHANGES)) {
      expect(behaviours.length, file).toBeGreaterThan(0);
      for (const entry of behaviours) {
        const text = read(entry.in ?? file);
        for (const pattern of entry.evidence) expect(pattern.test(text), `${file}: ${entry.behaviour}: ${pattern}`).toBe(true);
        if (entry.kind === "shared") expect(entry.reason, `${file}: ${entry.behaviour}`).toBeTruthy();
      }
    }
  });

  it("lists exactly the files this stage changed under screens/ and components/", () => {
    if (!baseReachable) return; // a checkout without the base commit has nothing to compare against
    const changed = (git(`diff --relative --name-only ${BASE} -- src/screens src/components`) ?? "")
      .concat(git(`ls-files --others --exclude-standard -- src/screens src/components`) ?? "")
      .split("\n")
      .filter((line) => line && !/\.test\.tsx?$/.test(line) && !line.includes("__snapshots__"))
      .map((line) => line.slice(LOCAL_PREFIX.length));
    expect([...new Set(changed)].sort()).toEqual(Object.keys(STAGE_CHANGES).sort());
  });

  it("runs base's code in each classic branch, unchanged", () => {
    if (!baseReachable) return;
    for (const [file, behaviours] of Object.entries(STAGE_CHANGES)) {
      for (const entry of behaviours) {
        for (const snippet of entry.classicVerbatim ?? []) {
          expect(read(file).includes(snippet), `${file} still has: ${snippet}`).toBe(true);
          expect(baseFile(file).includes(snippet), `base ${file} has: ${snippet}`).toBe(true);
        }
      }
    }
  });

  it("keeps base's palette component verbatim as the classic palette", () => {
    if (!baseReachable) return;
    const component = (text: string, name: string) => {
      const start = text.indexOf(name);
      const end = text.indexOf("\nfunction readHistory()", start);
      expect(start, name).toBeGreaterThanOrEqual(0);
      return text.slice(start + name.length, end);
    };
    const base = component(baseFile("components/CommandPalette.tsx"), "export function CommandPalette({");
    const classic = component(read("components/CommandPalette.tsx"), "function ClassicCommandPalette({");
    expect(classic).toBe(base);
  });
});
