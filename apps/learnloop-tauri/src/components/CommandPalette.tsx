// Command palette / inline `learnloop` shell.
//
// Open with Ctrl/Cmd+P or `:` from anywhere. Mirrors the MVP CLI surface:
//   today · review · why · show · attempt · propose · proposals · accept ·
//   reject · ingest · add-subject · add-note · merge-concepts · doctor ·
//   init · goto · help · clear
//
// Autocomplete is grammar-aware: each command declares which argument slot
// expects which entity kind, and the palette filters the ids the app knows
// about (current practice item, queue items, inspected entities, subjects).
//
// Output renders inline in a scroll-back buffer above the prompt. Navigation
// commands (today, attempt, goto, …) close the palette and route the app via
// the callbacks passed in from <App />. Data commands (review, why, show,
// doctor) call the real Tauri backend.

import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type { CliCommandResult, SessionSnapshot } from "../api/dto";
import { Pill, navTabs, type TopTab } from "./ui";

const HISTORY_KEY = "learnloop.commandHistory";

// ── Output rows ─────────────────────────────────────────────────────────
type OutputRow =
  | { type: "cmd"; text: string }
  | { type: "log"; text: string }
  | { type: "err"; text: string }
  | { type: "blank" }
  | { type: "p"; text: string }
  | { type: "label"; text: string; value: string }
  | { type: "kv"; k: string; v: string }
  | { type: "section"; text: string }
  | { type: "why-row"; k: string; contrib: number }
  | { type: "review"; n: number; id: string; title: string; mode: string; meta: string; why: string }
  | { type: "doctor"; name: string; status: "ok" | "warn" | "err"; note?: string }
  | { type: "summary"; errs: number; warns: number }
  | { type: "help"; commands: Array<{ name: string; help: string }> };

// ── Command grammar ─────────────────────────────────────────────────────
// Static description of every command — used by both autocomplete and the
// parser. Execution lives in runCommand().
type ArgKind = "practice_item" | "concept" | "goal" | "any" | "subject" | "tab" | "url" | "path";
interface ArgSpec {
  name: string;
  kind?: ArgKind;
}
interface GrammarSpec {
  help: string;
  args: ArgSpec[];
  flags: string[];
}

const GRAMMAR: Record<string, GrammarSpec> = {
  today: { help: "Launch the today loop", args: [], flags: [] },
  ask: { help: "Ask the tutor a question about the current context", args: [], flags: [] },
  review: { help: "Print the current due queue", args: [], flags: ["--energy", "--minutes", "--json"] },
  why: { help: "Explain a queued item's scheduler priority", args: [{ name: "practice_item_id", kind: "practice_item" }], flags: [] },
  show: { help: "Universal inspector — open any LO / PI / attempt / error", args: [{ name: "id", kind: "any" }], flags: [] },
  attempt: { help: "Open the practice screen for an item", args: [{ name: "practice_item_id", kind: "practice_item" }], flags: [] },
  propose: { help: "Run the Codex authoring proposal flow", args: [], flags: ["--file", "--subjects", "--notes", "--instructions", "--json"] },
  proposals: { help: "List proposal batches and item decisions", args: [], flags: [] },
  accept: { help: "Accept a proposal batch (or items via --items)", args: [{ name: "patch_id" }], flags: ["--items"] },
  reject: { help: "Reject a proposal batch (or items via --items)", args: [{ name: "patch_id" }], flags: ["--items"] },
  "edit-proposal-item": { help: "Edit a proposal item payload from a JSON/YAML file", args: [{ name: "patch_id" }, { name: "item_id" }], flags: ["--file", "--json"] },
  ingest: { help: "Stage a source note from URL / arXiv / PDF / .md", args: [{ name: "source", kind: "url" }], flags: ["--kind", "--subject", "--learning-object", "--goal", "--allow-auto-captions", "--instructions", "--json"] },
  "add-subject": { help: "Create a subject view + metadata", args: [{ name: "id", kind: "subject" }, { name: "title" }], flags: [] },
  "add-note": { help: "Register a note for later proposal generation", args: [{ name: "subject_id", kind: "subject" }, { name: "note_id" }, { name: "title" }], flags: ["--body", "--file", "--source-type"] },
  "generate-practice": { help: "Generate post-probe practice proposals", args: [], flags: ["--subjects", "--target-items-per-lo", "--max-new-per-lo", "--max-los", "--from-goal", "--instructions", "--dry-run", "--json"] },
  "populate-goal": { help: "Generate + accept practice items covering an active goal's scope", args: [{ name: "goal_id", kind: "goal" }], flags: ["--target-items-per-lo", "--max-new-per-lo", "--instructions", "--review", "--dry-run", "--json"] },
  calibrate: { help: "Start a calibration session — batched diagnostic blocks over a goal (or all open episodes)", args: [{ name: "goal_id", kind: "goal" }], flags: ["--minutes"] },
  "generate-diagnostics": { help: "Generate diagnostic follow-up practice proposals", args: [], flags: ["--learning-object-id", "--max-needs", "--instructions", "--ai-provider", "--dry-run", "--json"] },
  "observation-templates": { help: "List observation templates", args: [], flags: ["--all", "--json"] },
  "register-observation-template": { help: "Register an observation template", args: [], flags: ["--file", "--domain", "--version", "--title", "--active", "--inactive", "--json"] },
  "record-observation": { help: "Record an observation response", args: [{ name: "template_id" }], flags: ["--response-json", "--response-file", "--subject", "--learning-object-id", "--practice-item-id", "--session-id", "--json"] },
  "misconception-candidates": { help: "Rank misconception/error candidates", args: [{ name: "practice_item_id", kind: "practice_item" }], flags: ["--query", "--limit", "--json"] },
  "merge-concepts": {
    help: "Merge a duplicate concept into the canonical concept",
    args: [{ name: "canonical_id", kind: "concept" }, { name: "duplicate_id", kind: "concept" }],
    flags: ["--alias", "--no-alias", "--dry-run", "--force", "--json"]
  },
  doctor: { help: "Validate vault, schemas, and runtime health", args: [], flags: ["--json", "--fix-state"] },
  init: { help: "Create a new vault", args: [], flags: [] },
  goto: { help: "Jump to a tab", args: [{ name: "tab", kind: "tab" }], flags: [] },
  help: { help: "List available commands", args: [], flags: [] },
  clear: { help: "Clear the scroll-back", args: [], flags: [] }
};

const CLI_DELEGATED_COMMANDS = new Set([
  "propose",
  "proposals",
  "accept",
  "reject",
  "edit-proposal-item",
  "ingest",
  "add-subject",
  "add-note",
  "generate-practice",
  "populate-goal",
  "generate-diagnostics",
  "observation-templates",
  "register-observation-template",
  "record-observation",
  "misconception-candidates",
  "merge-concepts",
  "init"
]);

// ── Execution context ───────────────────────────────────────────────────
interface CmdCtx {
  session: SessionSnapshot | null;
  onGoto: (tab: TopTab) => void;
  onOpenPractice: (id: string) => void;
  onOpenCalibration: (calibrationSessionId: string) => void;
  onInspect: (id: string) => void;
  onAsk: () => boolean;
  clearBuffer: () => void;
  close: () => void;
}

type Flags = Record<string, string | true>;

async function runCommand(name: string, args: string[], flags: Flags, ctx: CmdCtx, argv: string[]): Promise<OutputRow[]> {
  if (name === "__cli__" || CLI_DELEGATED_COMMANDS.has(name) || !GRAMMAR[name]) {
    return runCli(argv);
  }
  switch (name) {
    case "today": {
      ctx.onGoto("today");
      ctx.close();
      return [{ type: "log", text: "→ today" }];
    }
    case "ask": {
      if (!ctx.onAsk()) {
        return [{ type: "err", text: "no askable context — open a note, a practice item, or feedback first" }];
      }
      ctx.close();
      return [{ type: "log", text: "→ ask" }];
    }
    case "goto": {
      const tab = findTab(args[0]);
      if (!tab) return [{ type: "err", text: `unknown tab: ${args[0] ?? "(none)"}` }];
      ctx.onGoto(tab);
      ctx.close();
      return [{ type: "log", text: `→ ${tab}` }];
    }
    case "review":
      return runReview(args, flags, ctx);
    case "why":
      return runWhy(args);
    case "show":
      return runShow(args, ctx, argv);
    case "attempt": {
      if (!args[0]) return [{ type: "err", text: "usage: attempt <practice_item_id>" }];
      ctx.onOpenPractice(args[0]);
      ctx.close();
      return [{ type: "log", text: `→ practice · ${args[0]}` }];
    }
    case "calibrate":
      return runCalibrate(args, flags, ctx);
    case "doctor":
      return runDoctor();
    case "proposals": {
      ctx.onGoto("proposals");
      ctx.close();
      return [{ type: "log", text: "→ proposals" }];
    }
    case "propose": {
      ctx.onGoto("proposals");
      ctx.close();
      return [{ type: "log", text: "→ proposals · authoring flow is not wired into the desktop build yet" }];
    }
    case "ingest": {
      ctx.onGoto("ingest");
      ctx.close();
      return [{ type: "log", text: `→ ingest${args[0] ? ` · ${args[0]}` : ""}` }];
    }
    case "accept":
    case "reject":
    case "add-subject":
    case "add-note":
    case "init":
      return [{ type: "log", text: `‘${name}’ is not available in the desktop build yet.` }];
    case "clear":
      ctx.clearBuffer();
      return [];
    case "help":
      return [{ type: "help", commands: [] }];
    default:
      return [{ type: "err", text: `unknown command: ${name}` }];
  }
}

async function runCli(argv: string[]): Promise<OutputRow[]> {
  const result = await api.runCliCommand(argv);
  return cliResultRows(result);
}

function cliResultRows(result: CliCommandResult): OutputRow[] {
  const rows: OutputRow[] = [];
  for (const line of splitOutput(result.stdout)) {
    rows.push({ type: "log", text: line });
  }
  for (const line of splitOutput(result.stderr)) {
    rows.push({ type: "err", text: line });
  }
  if (result.exitCode !== 0) {
    rows.push({ type: "err", text: `exit code ${result.exitCode}` });
  }
  if (rows.length === 0) {
    rows.push({ type: "log", text: "ok" });
  }
  return rows;
}

function splitOutput(value: string): string[] {
  return value.replace(/\r\n/g, "\n").split("\n").filter((line) => line.length > 0);
}

async function runReview(_args: string[], flags: Flags, ctx: CmdCtx): Promise<OutputRow[]> {
  const energy = typeof flags["--energy"] === "string" ? (flags["--energy"] as string) : null;
  if (energy && !["low", "medium", "high"].includes(energy)) {
    return [{ type: "err", text: "invalid --energy (expected low | medium | high)" }];
  }
  let minutes: number | null = null;
  if (typeof flags["--minutes"] === "string") {
    const parsed = Number(flags["--minutes"]);
    if (!Number.isInteger(parsed) || parsed <= 0) return [{ type: "err", text: "invalid --minutes" }];
    minutes = parsed;
  }
  const queue = await api.getTodayQueue({
    sessionId: ctx.session?.sessionId ?? null,
    availableMinutes: minutes ?? ctx.session?.availableMinutes ?? null,
    energy: energy ?? ctx.session?.energy ?? null
  });
  if (queue.totalItems === 0) {
    return [{ type: "log", text: "queue is empty for this readiness." }];
  }
  const rows: OutputRow[] = [{ type: "label", text: "due items", value: String(queue.totalItems) }, { type: "blank" }];
  for (const section of queue.sections) {
    rows.push({ type: "section", text: section.title.toUpperCase() });
    section.items.forEach((item, index) => {
      rows.push({
        type: "review",
        n: index + 1,
        id: item.practiceItemId,
        title: item.learningObjectTitle,
        mode: item.selectedMode || item.practiceMode,
        meta: `${item.mastery == null ? "mastery —" : `mastery ${item.mastery.toFixed(2)}`} · ${item.dueStatus}`,
        why: item.plainEnglish[0] ?? ""
      });
    });
  }
  return rows;
}

// Start a §5.9 calibration session and enter the calibration screen. With a
// goal id it batches episode blocks across that goal's facet scope; without
// one it runs over the already-open probe episodes.
async function runCalibrate(args: string[], flags: Flags, ctx: CmdCtx): Promise<OutputRow[]> {
  if (!ctx.session) {
    return [{ type: "err", text: "start a session first — calibration attaches to the active practice session" }];
  }
  let minutes: number | null = null;
  if (typeof flags["--minutes"] === "string") {
    const parsed = Number(flags["--minutes"]);
    if (!Number.isInteger(parsed) || parsed <= 0) return [{ type: "err", text: "invalid --minutes" }];
    minutes = parsed;
  }
  const progress = await api.startCalibrationSession({
    sessionId: ctx.session.sessionId,
    goalId: args[0] ?? null,
    timeBudgetMinutes: minutes
  });
  ctx.onOpenCalibration(progress.calibrationSessionId);
  ctx.close();
  return [
    {
      type: "log",
      text: `→ calibration · ${progress.calibrationSessionId} · ${progress.blocksPlanned} blocks planned · ${progress.timeBudgetMinutes}m budget`
    }
  ];
}

async function runWhy(args: string[]): Promise<OutputRow[]> {
  if (!args[0]) return [{ type: "err", text: "usage: why <practice_item_id>" }];
  const explanation = await api.explainPracticeItem(args[0]);
  const c = explanation.components;
  const rows: OutputRow[] = [
    { type: "label", text: "priority", value: explanation.priority.toFixed(3) },
    { type: "blank" },
    { type: "why-row", k: "forgetting_risk", contrib: c.forgettingRisk },
    { type: "why-row", k: "goal_frontier", contrib: c.goalFrontier ?? 0 },
    { type: "why-row", k: "recent_error", contrib: c.recentError },
    { type: "why-row", k: "probe_eig", contrib: c.probeEig }
  ];
  const followupContribution = (c.interventionFollowup ?? 0) + (c.negativeSurpriseFollowup ?? 0);
  if (followupContribution > 0) {
    rows.push({ type: "why-row", k: "intervention_followup", contrib: followupContribution });
  }
  rows.push({ type: "blank" });
  if (explanation.readinessFactor != null) {
    rows.push({ type: "kv", k: "readiness_factor", v: explanation.readinessFactor.toFixed(2) });
  }
  rows.push({ type: "kv", k: "expected_info_gain", v: explanation.expectedInformationGain.toFixed(3) });
  rows.push({ type: "kv", k: "selected_mode", v: explanation.selectedMode });
  rows.push({ type: "blank" });
  explanation.plainEnglish.forEach((line) => rows.push({ type: "p", text: line }));
  return rows;
}

async function runShow(args: string[], ctx: CmdCtx, argv: string[]): Promise<OutputRow[]> {
  if (!args[0]) return [{ type: "err", text: "usage: show <id>" }];
  const entity = await api.inspectEntity(args[0]);
  if (entity.kind === "not_found") {
    return runCli(argv);
  }
  ctx.onInspect(args[0]);
  ctx.close();
  return [{ type: "log", text: `opened inspector → ${entity.kind} ${entity.id}` }];
}

async function runDoctor(): Promise<OutputRow[]> {
  const health = await api.getRuntimeHealth();
  const checks: Array<{ name: string; status: "ok" | "warn" | "err"; note?: string }> = [
    { name: "vault loaded", status: health.vaultLoaded ? "ok" : "err", note: health.vaultLoaded ? undefined : "no vault selected" },
    {
      name: "sqlite migrations",
      status: health.database.ok && health.database.migrationsApplied >= health.database.latestMigration ? "ok" : "warn",
      note: `${health.database.migrationsApplied}/${health.database.latestMigration} applied`
    },
    {
      name: "codex healthcheck",
      status: health.codex.ready ? "ok" : "warn",
      note: health.codex.ready ? (health.codex.actualRevision ?? health.codex.model ?? undefined) : health.codex.status
    }
  ];
  const rows: OutputRow[] = [{ type: "log", text: `running ${checks.length} checks...` }];
  checks.forEach((check) => rows.push({ type: "doctor", ...check }));
  rows.push({ type: "blank" });
  rows.push({
    type: "summary",
    errs: checks.filter((c) => c.status === "err").length,
    warns: checks.filter((c) => c.status === "warn").length
  });
  return rows;
}

// ── Tokenizer / autocomplete / parser ───────────────────────────────────
interface Completion {
  completion: string;
  replaceToken: string;
  hint: string;
  kind: string;
}

function tokenize(line: string, cursor: number) {
  const left = line.slice(0, cursor);
  const leftTokens = left.split(/\s+/);
  const all = line.trim() === "" ? [] : line.trim().split(/\s+/);
  return {
    all,
    activeIndex: Math.max(0, leftTokens.length - 1),
    activePrefix: leftTokens[leftTokens.length - 1],
    endsWithSpace: /\s$/.test(left)
  };
}

interface Candidates {
  entityIds: string[];
  practiceItemIds: string[];
  conceptIds: string[];
  goalIds: string[];
  subjects: string[];
}

function candidatesFor(kind: ArgKind | undefined, c: Candidates): string[] {
  switch (kind) {
    case "practice_item":
      return c.practiceItemIds;
    case "concept":
      return c.conceptIds;
    case "goal":
      return c.goalIds;
    case "any":
      return Array.from(new Set([...c.practiceItemIds, ...c.entityIds]));
    case "subject":
      return c.subjects;
    case "tab":
      return navTabs.map((tab) => tab.id);
    default:
      return [];
  }
}

function computeCompletions(line: string, cursor: number, cands: Candidates): Completion[] {
  const tok = tokenize(line, cursor);
  const prefix = tok.endsWithSpace ? "" : tok.activePrefix;

  // First token → command names.
  if (tok.activeIndex === 0 && !tok.endsWithSpace) {
    return Object.entries(GRAMMAR)
      .filter(([name]) => name.startsWith(prefix))
      .map(([name, spec]) => ({ completion: name, replaceToken: tok.activePrefix, hint: spec.help, kind: "command" }));
  }

  const spec = GRAMMAR[tok.all[0]];
  if (!spec) return [];

  // Flag name completion.
  if (prefix.startsWith("--")) {
    return spec.flags
      .filter((flag) => flag.startsWith(prefix))
      .map((flag) => ({ completion: flag, replaceToken: prefix, hint: "flag", kind: "flag" }));
  }

  // Compute positional index, skipping flags + their values.
  const positional: string[] = [];
  let pendingFlag: string | null = null;
  for (let i = 1; i < tok.all.length; i += 1) {
    const token = tok.all[i];
    if (token.startsWith("--")) {
      pendingFlag = token;
      continue;
    }
    if (pendingFlag && spec.flags.includes(pendingFlag)) {
      pendingFlag = null;
      continue;
    }
    positional.push(token);
  }

  // Active token is a flag value? (no structured suggestions except --subject)
  const before = tok.all.slice(0, tok.activeIndex);
  const lastBefore = before[before.length - 1];
  if (lastBefore && lastBefore.startsWith("--")) {
    if (lastBefore === "--subject") {
      return cands.subjects.filter((s) => s.startsWith(prefix)).map((s) => ({ completion: s, replaceToken: prefix, hint: "subject", kind: "subject" }));
    }
    return [];
  }

  const posIndex = tok.endsWithSpace ? positional.length : positional.length - 1;
  const argSpec = spec.args[posIndex] ?? spec.args[spec.args.length - 1];
  if (!argSpec) return [];

  const pool = candidatesFor(argSpec.kind, cands);
  const exact = pool.filter((id) => id.startsWith(prefix));
  const sub = pool.filter((id) => !id.startsWith(prefix) && id.includes(prefix));
  return [...exact, ...sub].slice(0, 20).map((id) => ({
    completion: id,
    replaceToken: prefix,
    hint: argSpec.kind ?? "",
    kind: argSpec.kind ?? "arg"
  }));
}

function parse(line: string): { error?: string; name?: string; positional: string[]; flags: Flags; argv: string[] } {
  const tokenized = shellTokenize(line);
  if (tokenized.error) return { error: tokenized.error, positional: [], flags: {}, argv: [] };
  let tokens = tokenized.tokens;
  if (tokens.length === 0) return { error: "empty", positional: [], flags: {}, argv: [] };
  if (tokens[0] === "learnloop") {
    tokens = tokens.slice(1);
    if (tokens.length === 0) tokens = ["--help"];
  }
  const name = tokens[0].startsWith("-") ? "__cli__" : tokens[0];
  const positional: string[] = [];
  const flags: Flags = {};
  for (let i = name === "__cli__" ? 0 : 1; i < tokens.length; i += 1) {
    const token = tokens[i];
    if (token.startsWith("--")) {
      const next = tokens[i + 1];
      if (next && !next.startsWith("--")) {
        flags[token] = next;
        i += 1;
      } else {
        flags[token] = true;
      }
    } else {
      positional.push(token);
    }
  }
  return { name, positional, flags, argv: tokens };
}

function shellTokenize(line: string): { tokens: string[]; error?: string } {
  const tokens: string[] = [];
  let current = "";
  let quote: "'" | '"' | null = null;
  let escaping = false;
  let tokenStarted = false;

  for (const char of line.trim()) {
    if (escaping) {
      current += char;
      escaping = false;
      tokenStarted = true;
      continue;
    }
    if (char === "\\" && quote !== "'") {
      escaping = true;
      tokenStarted = true;
      continue;
    }
    if (quote) {
      if (char === quote) {
        quote = null;
      } else {
        current += char;
        tokenStarted = true;
      }
      continue;
    }
    if (char === "'" || char === '"') {
      quote = char;
      tokenStarted = true;
      continue;
    }
    if (/\s/.test(char)) {
      if (tokenStarted) {
        tokens.push(current);
        current = "";
        tokenStarted = false;
      }
      continue;
    }
    current += char;
    tokenStarted = true;
  }

  if (escaping) current += "\\";
  if (quote) return { tokens: [], error: "unterminated quote" };
  if (tokenStarted) tokens.push(current);
  return { tokens };
}

function findTab(value: string | undefined): TopTab | null {
  if (!value) return null;
  const lowered = value.toLowerCase();
  return navTabs.find((tab) => tab.id === lowered || tab.label.toLowerCase() === lowered)?.id ?? null;
}

// ── Kind badge ──────────────────────────────────────────────────────────
function KindBadge({ kind }: { kind: string }) {
  const map: Record<string, { tone: string; label: string }> = {
    command: { tone: "amber", label: "cmd" },
    flag: { tone: "slate", label: "flag" },
    subject: { tone: "green", label: "subject" },
    concept: { tone: "amber", label: "concept" },
    tab: { tone: "cyan", label: "tab" },
    practice_item: { tone: "cyan", label: "pi" },
    goal: { tone: "green", label: "goal" },
    any: { tone: "slate", label: "id" }
  };
  const m = map[kind] ?? { tone: "slate", label: kind || "?" };
  return <Pill tone={m.tone}>{m.label}</Pill>;
}

// ── Output row renderer ─────────────────────────────────────────────────
function modeTone(mode: string): string {
  if (mode.includes("probe")) return "pink";
  if (mode.includes("recall") || mode.includes("define")) return "cyan";
  if (mode.includes("proof") || mode.includes("derive")) return "amber";
  return "slate";
}

function OutputRowView({ row, commands }: { row: OutputRow; commands: Array<{ name: string; help: string }> }) {
  switch (row.type) {
    case "cmd":
      return (
        <div className="cli-row cli-row-cmd">
          <span className="cli-caret">❯</span>
          <span>{row.text}</span>
        </div>
      );
    case "log":
      return <div className="cli-row cli-row-log">{row.text}</div>;
    case "err":
      return <div className="cli-row cli-row-err">{row.text}</div>;
    case "blank":
      return <div className="cli-blank" />;
    case "p":
      return <div className="cli-row cli-row-p">{row.text}</div>;
    case "label":
      return (
        <div className="cli-row cli-row-label">
          <span className="cli-faint">{row.text} </span>
          <span className="cli-accent">{row.value}</span>
        </div>
      );
    case "kv":
      return (
        <div className="cli-row cli-row-kv">
          <span className="cli-faint">{row.k}</span>
          <span>{row.v}</span>
        </div>
      );
    case "section":
      return <div className="cli-section">{row.text}</div>;
    case "why-row":
      return (
        <div className="cli-why-row">
          <span className={`cli-why-key ${row.k}`}>{row.k}</span>
          <span className="cli-why-contrib">{row.contrib >= 0 ? "+" : ""}{row.contrib.toFixed(3)}</span>
        </div>
      );
    case "review":
      return (
        <div className="cli-review">
          <span className="cli-faint cli-review-n">{row.n}.</span>
          <span className="cli-accent">{row.id}</span>
          <Pill tone={modeTone(row.mode)}>{row.mode}</Pill>
          <span className="cli-review-meta">{row.meta}</span>
          <span className="cli-accent cli-review-why">{row.why}</span>
        </div>
      );
    case "doctor": {
      const mark = row.status === "ok" ? "✓" : row.status === "warn" ? "⚠" : "✗";
      return (
        <div className={`cli-doctor cli-status-${row.status}`}>
          <span className="cli-doctor-mark">{mark}</span>
          <span>{row.name}</span>
          <span className="cli-faint">{row.note ?? ""}</span>
        </div>
      );
    }
    case "summary":
      return (
        <div className={`cli-row cli-summary cli-status-${row.errs ? "err" : row.warns ? "warn" : "ok"}`}>
          {row.errs} errors · {row.warns} warnings
        </div>
      );
    case "help":
      return (
        <div className="cli-help">
          {commands.map((cmd) => (
            <div className="cli-help-row" key={cmd.name}>
              <span className="cli-accent">{cmd.name}</span>
              <span className="cli-faint">{cmd.help}</span>
            </div>
          ))}
        </div>
      );
    default:
      return null;
  }
}

// ── Main palette ────────────────────────────────────────────────────────
export function CommandPalette({
  open,
  session,
  entityIds,
  practiceItemIds,
  subjects,
  onClose,
  onGoto,
  onOpenPractice,
  onOpenCalibration,
  onInspect,
  onAsk,
  onError
}: {
  open: boolean;
  session: SessionSnapshot | null;
  entityIds: string[];
  practiceItemIds: string[];
  subjects: string[];
  onClose: () => void;
  onGoto: (tab: TopTab) => void;
  onOpenPractice: (id: string) => void;
  onOpenCalibration: (calibrationSessionId: string) => void;
  onInspect: (id: string) => void;
  onAsk: () => boolean;
  onError: (message: string) => void;
}) {
  const [line, setLine] = useState("");
  const [cursor, setCursor] = useState(0);
  const [buffer, setBuffer] = useState<OutputRow[]>([]);
  const [history, setHistory] = useState<string[]>(() => readHistory());
  const [histIdx, setHistIdx] = useState(-1);
  const [acIdx, setAcIdx] = useState(0);
  const [busy, setBusy] = useState(false);
  const [conceptIds, setConceptIds] = useState<string[]>([]);
  const [goalIds, setGoalIds] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const subjectsKey = useMemo(() => subjects.join("\0"), [subjects]);
  const cands = useMemo<Candidates>(
    () => ({ entityIds, practiceItemIds, conceptIds, goalIds, subjects }),
    [entityIds, practiceItemIds, conceptIds, goalIds, subjects]
  );
  const completions = useMemo(() => computeCompletions(line, cursor, cands), [line, cursor, cands]);

  const helpCommands = useMemo(() => Object.entries(GRAMMAR).map(([name, spec]) => ({ name, help: spec.help })), []);

  useEffect(() => {
    setAcIdx(0);
  }, [line]);

  useEffect(() => {
    if (open) window.setTimeout(() => inputRef.current?.focus(), 30);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    api
      .getConceptGraph()
      .then((graph) => {
        if (!cancelled) setConceptIds(graph.concepts.map((concept) => concept.id));
      })
      .catch(() => {
        if (!cancelled) setConceptIds([]);
      });
    api
      .goalsList()
      .then((snapshot) => {
        // populate-goal only operates on active goals, so only offer those.
        if (!cancelled) setGoalIds(snapshot.goals.filter((goal) => goal.status === "active").map((goal) => goal.id));
      })
      .catch(() => {
        if (!cancelled) setGoalIds([]);
      });
    return () => {
      cancelled = true;
    };
  }, [open, subjectsKey]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [buffer, open]);

  if (!open) return null;

  function applyCompletion(index: number) {
    const sel = completions[index];
    if (!sel) return;
    const tok = tokenize(line, cursor);
    const tokStart = cursor - tok.activePrefix.length;
    const before = line.slice(0, tokStart);
    const after = line.slice(cursor);
    const trail = after.startsWith(" ") ? "" : " ";
    const newLine = `${before}${sel.completion}${trail}${after}`;
    const newCursor = (before + sel.completion + trail).length;
    setLine(newLine);
    setCursor(newCursor);
    window.setTimeout(() => {
      inputRef.current?.focus();
      inputRef.current?.setSelectionRange(newCursor, newCursor);
    }, 0);
  }

  async function execute() {
    const raw = line.trim();
    if (!raw || busy) return;
    const parsed = parse(raw);
    const nextHistory = [raw, ...history.filter((entry) => entry !== raw)].slice(0, 50);
    setHistory(nextHistory);
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistory));
    } catch {
      /* ignore */
    }
    setLine("");
    setCursor(0);
    setHistIdx(-1);

    if (parsed.error) {
      setBuffer((b) => [...b, { type: "cmd", text: raw }, { type: "err", text: parsed.error as string }]);
      return;
    }
    setBuffer((b) => [...b, { type: "cmd", text: raw }]);
    setBusy(true);
    try {
      const ctx: CmdCtx = {
        session,
        onGoto,
        onOpenPractice,
        onOpenCalibration,
        onInspect,
        onAsk,
        clearBuffer: () => setBuffer([]),
        close: onClose
      };
      const out = await runCommand(parsed.name as string, parsed.positional, parsed.flags, ctx, parsed.argv);
      if (out.length) setBuffer((b) => [...b, ...out]);
    } catch (error) {
      const message = (error as Error).message ?? String(error);
      onError(message);
      setBuffer((b) => [...b, { type: "err", text: message }]);
    } finally {
      setBusy(false);
    }
  }

  function onInputKey(event: React.KeyboardEvent<HTMLInputElement>) {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "p") {
      onClose();
      event.preventDefault();
      return;
    }
    if (event.key === "Escape") {
      onClose();
      event.preventDefault();
    } else if (event.key === "Enter") {
      void execute();
      event.preventDefault();
    } else if (event.key === "Tab") {
      applyCompletion(acIdx);
      event.preventDefault();
    } else if (event.key === "ArrowDown") {
      if (completions.length > 0) {
        setAcIdx((i) => Math.min(completions.length - 1, i + 1));
      } else if (history.length > 0) {
        const next = Math.max(-1, histIdx - 1);
        setHistIdx(next);
        const value = next === -1 ? "" : history[next] ?? "";
        setLine(value);
        setCursor(value.length);
      }
      event.preventDefault();
    } else if (event.key === "ArrowUp") {
      if (completions.length > 0 && line.trim().length > 0) {
        setAcIdx((i) => Math.max(0, i - 1));
      } else if (history.length > 0) {
        const next = Math.min(history.length - 1, histIdx + 1);
        setHistIdx(next);
        const value = history[next] ?? "";
        setLine(value);
        setCursor(value.length);
      }
      event.preventDefault();
    } else if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "l") {
      setBuffer([]);
      event.preventDefault();
    } else if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "c" && line) {
      setLine("");
      setCursor(0);
      event.preventDefault();
    }
  }

  return (
    <div className="cli-backdrop" onMouseDown={onClose}>
      <div className="cli-shell" onMouseDown={(event) => event.stopPropagation()}>
        <div className="cli-titlebar">
          <span className="cli-title">
            learnloop <span className="cli-accent">shell</span>
          </span>
          <span className="cli-hint">
            <b>^p</b> toggle <b>tab</b> complete <b>↑↓</b> nav <b>esc</b> close
          </span>
        </div>

        <div className="cli-scrollback" ref={scrollRef}>
          {buffer.length === 0 ? (
            <div className="cli-row cli-row-p">
              <span className="cli-accent">learnloop</span> — type <b>help</b> for commands, or start with{" "}
              <b>review</b>, <b>doctor</b>, or <b>show &lt;id&gt;</b>.
            </div>
          ) : (
            buffer.map((row, index) => <OutputRowView key={index} row={row} commands={helpCommands} />)
          )}
          {busy ? <div className="cli-row cli-row-log">…running</div> : null}
        </div>

        {completions.length > 0 ? (
          <div className="cli-completions">
            {completions.map((entry, index) => (
              <div
                key={`${entry.kind}:${entry.completion}`}
                className={`cli-completion ${index === acIdx ? "selected" : ""}`}
                onMouseEnter={() => setAcIdx(index)}
                onMouseDown={(event) => {
                  event.preventDefault();
                  applyCompletion(index);
                }}
              >
                <KindBadge kind={entry.kind} />
                <span className="cli-completion-text">{entry.completion}</span>
                <span className="cli-faint cli-completion-hint">{entry.hint}</span>
              </div>
            ))}
          </div>
        ) : null}

        <div className="cli-prompt-row">
          <span className="cli-caret">❯</span>
          <span className="cli-faint">learnloop</span>
          <input
            ref={inputRef}
            value={line}
            onChange={(event) => {
              setLine(event.target.value);
              setCursor(event.target.selectionStart ?? event.target.value.length);
            }}
            onKeyDown={onInputKey}
            onKeyUp={(event) => setCursor(event.currentTarget.selectionStart ?? 0)}
            onClick={(event) => setCursor(event.currentTarget.selectionStart ?? 0)}
            placeholder="type a command — tab to complete"
            spellCheck={false}
            disabled={busy}
          />
          {completions.length > 0 ? (
            <span className="cli-faint cli-match-count">
              {completions.length} match{completions.length === 1 ? "" : "es"}
            </span>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function readHistory(): string[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(HISTORY_KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed.filter((entry) => typeof entry === "string").slice(0, 50) : [];
  } catch {
    return [];
  }
}
