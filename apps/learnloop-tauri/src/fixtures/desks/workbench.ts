// A minimal fake workbench service for the desks' harness (`?problem=1`): one RW2 session opened from a selection,
// its steps saved, the help ladder answered with one rung's suggestion, the check pending, and a submit that records
// an attempt. Enough for the problem pad's harness run (spec §15.2); none of it grades anything.
import type { WorkbenchSessionDto } from "../../api/dto";

const RECORD = { bookCounted: false, bookVisible: true, hints: 0, questionHints: 0, ownAttempt: true, line: "your own attempt", footer: "book open · help used: none", stuckNote: null };

export class FixtureWorkbench {
  readonly calls: Array<{ command: string; input: Record<string, unknown> }> = [];
  private session: WorkbenchSessionDto | null = null;
  private saved = 0;
  /** Each write's answer by its idempotency key (a repeat answers the same, as the service does), and each step's
   *  chain (its first row) by row id. */
  private byKey = new Map<string, Record<string, unknown>>();
  private chainOf = new Map<string, string>();
  private bodies = new Map<string, string>();

  private make(input: Record<string, unknown>): WorkbenchSessionDto {
    return {
      sessionId: "fx_wb_1", practiceItemId: "fx_item_wb", stemMd: String(input.stemMd ?? "Exercise 1.1 Show the weights add up to one."),
      importStatus: "none", importError: null, origin: "reader", entry: "work_through", parentSessionId: null,
      extractionId: String(input.extractionId ?? ""), spanIds: (input.spanIds as string[] | undefined) ?? [], sourceVisible: true, sourceHiddenAt: null,
      sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open", attemptId: null, createdAt: "2026-11-23T09:00:00Z",
      updatedAt: "2026-11-23T09:00:00Z", closedAt: null, steps: [], lastEditedStepId: null, record: RECORD, parts: null, sourceId: "fx_src_softmax",
    } as unknown as WorkbenchSessionDto;
  }

  /** Steps' texts as last saved, by chain (a test reads what help would read). */
  stepBodies(): Record<string, string> {
    return Object.fromEntries(this.bodies);
  }

  private checkOnLast(): unknown {
    if (typeof window === "undefined" || new URLSearchParams(window.location.search).get("inkhelp") !== "1") return null;
    const chains = [...new Set(this.chainOf.values())];
    const last = chains[chains.length - 1];
    if (!last) return null;
    return { assistId: "fx_check_1", checkedAt: "2026-11-23T09:01:00Z", firstQuestionableStepId: last, errorKind: null, assumptions: [],
      symbolicEnabled: false, symbolicAvailable: false, stale: false, changedSteps: [],
      verdicts: chains.map((chainId, index) => ({ chainId, number: index + 1, verdict: chainId === last ? "questionable" : "valid", method: "model",
        mark: chainId === last ? "?" : "≈", label: "model's reading, not checked", reason: chainId === last ? "the sign of the second term" : "",
        dependsOn: [], assumption: "", first: chainId === last, editedSinceCheck: false, deletedSinceCheck: false })) };
  }

  /** The answer to a workbench command, or undefined when the command is not the workbench's. */
  answer(command: string, input: Record<string, unknown>): unknown {
    if (!command.startsWith("workbench_")) return undefined;
    this.calls.push({ command, input });
    switch (command) {
      case "workbench_for_source":
        return { sessions: [], openSessionDays: 30 };
      case "workbench_open":
        this.session = this.session ?? this.make(input);
        return { session: this.session, resumed: input.entry === "resume" };
      case "workbench_refresh_import":
      case "workbench_admit":
      case "workbench_leave":
      case "workbench_set_book":
        return { session: this.session };
      case "workbench_save_step": {
        const key = String(input.clientIdempotencyKey ?? "");
        const repeat = this.byKey.get(key);
        if (repeat) return repeat;
        this.saved += 1;
        const row = `fx_step_${this.saved}`;
        const chain = input.op === "add" ? row : this.chainOf.get(String(input.stepId)) ?? String(input.stepId);
        this.chainOf.set(row, chain);
        const body = input.bodyMd !== undefined && input.bodyMd !== null ? String(input.bodyMd) : this.bodies.get(chain) ?? "";
        this.bodies.set(chain, body);
        const answer = { version: 1, savedAt: "2026-11-23T09:00:05Z", record: RECORD,
          step: { stepId: row, chainId: chain, ordinal: this.saved, kind: input.kind ?? "step",
            bodyMd: body, deleted: input.op === "delete", createdAt: "x", editedAt: "x", versions: [] } };
        this.byKey.set(key, answer);
        return answer;
      }
      case "workbench_help_state":
        // `?problem=1&inkhelp=1`: the last check found the newest step the first that doesn't hold (its ◇).
        return { version: 1, check: this.checkOnLast(), hints: [], helpStyle: null, storedHelpStyle: "balanced", hintsEnabled: true };
      case "workbench_check": {
        // `?inkhelp=1`: the check answers at once, the newest step the first that doesn't hold (its ◇).
        const check = this.checkOnLast();
        if (check) return { version: 1, jobId: null, kind: "check", state: "done", result: { status: "ready", shown: true, check, record: RECORD } };
        return { version: 1, jobId: "fx_help_job", kind: "check", state: "pending", result: null };
      }
      case "workbench_suggest_help":
      case "workbench_help_job":
        return { version: 1, jobId: "fx_help_job", kind: "suggest", state: "pending", result: null };
      case "workbench_cancel_help":
        return { cancelled: true };
      case "workbench_submit": {
        const submitted = { ...(this.session as WorkbenchSessionDto), status: "submitted", attemptId: "fx_attempt_wb" } as WorkbenchSessionDto;
        this.session = submitted;
        return { version: 1, practiceSession: null, session: submitted, attempt: { attemptId: "fx_attempt_wb" } };
      }
      default:
        return { session: this.session };
    }
  }
}
