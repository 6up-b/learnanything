// A minimal fake workbench service for the desks' harness (`?problem=1`): one RW2 session opened from a selection,
// its steps saved, the help ladder answered with one rung's suggestion, the check pending, and a submit that records
// an attempt. Enough for the problem pad's harness run (spec §15.2); none of it grades anything.
import type { WorkbenchSessionDto } from "../../api/dto";

const RECORD = { bookCounted: false, bookVisible: true, hints: 0, questionHints: 0, ownAttempt: true, line: "your own attempt", footer: "book open · help used: none", stuckNote: null };

export class FixtureWorkbench {
  readonly calls: Array<{ command: string; input: Record<string, unknown> }> = [];
  private session: WorkbenchSessionDto | null = null;
  private saved = 0;

  private make(input: Record<string, unknown>): WorkbenchSessionDto {
    return {
      sessionId: "fx_wb_1", practiceItemId: "fx_item_wb", stemMd: String(input.stemMd ?? "Exercise 1.1 Show the weights add up to one."),
      importStatus: "none", importError: null, origin: "reader", entry: "work_through", parentSessionId: null,
      extractionId: String(input.extractionId ?? ""), spanIds: (input.spanIds as string[] | undefined) ?? [], sourceVisible: true, sourceHiddenAt: null,
      sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open", attemptId: null, createdAt: "2026-11-23T09:00:00Z",
      updatedAt: "2026-11-23T09:00:00Z", closedAt: null, steps: [], lastEditedStepId: null, record: RECORD, parts: null, sourceId: "fx_src_softmax",
    } as unknown as WorkbenchSessionDto;
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
      case "workbench_save_step":
        this.saved += 1;
        return { version: 1, savedAt: "2026-11-23T09:00:05Z", record: RECORD,
          step: { stepId: `fx_step_${this.saved}`, chainId: input.stepId ?? `fx_step_${this.saved}`, ordinal: this.saved, kind: input.kind ?? "step",
            bodyMd: input.bodyMd ?? "", deleted: input.op === "delete", createdAt: "x", editedAt: "x", versions: [] } };
      case "workbench_help_state":
        return { version: 1, check: null, hints: [], helpStyle: null, storedHelpStyle: "balanced", hintsEnabled: true };
      case "workbench_suggest_help":
      case "workbench_check":
      case "workbench_help_job":
        return { version: 1, jobId: "fx_help_job", kind: command === "workbench_check" ? "check" : "suggest", state: "pending", result: null };
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
