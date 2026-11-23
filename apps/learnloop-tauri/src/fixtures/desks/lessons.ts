// The synthetic workspace's Teacher lessons (spec §11.1, §18.3): one finished lesson on softmax (a check answered
// and graded, a close card), its additions pad, and a fake lesson service for the harness: lesson.view replays what
// a lesson recorded, lesson.turn's opening makes a new lesson after a short wait, lesson.list names them. Every
// call is recorded, so the harness can show a review made no turn. Project-authored text only.
import type { LessonSummaryDto, LessonTurnInput, LessonViewDto, PadBlockDto, PadViewDto } from "../../api/dto";

export const FIXTURE_LESSON_ID = "fx_lesson_softmax";
export const FIXTURE_ADDITIONS_PAD_ID = "fx_pad_lesson_adds";
const T = "2026-11-21T10:00:00Z";

export const FIXTURE_LESSON_VIEW: LessonViewDto = {
  version: 1,
  lessonId: FIXTURE_LESSON_ID,
  goal: "softmax and cross-entropy: the log undoes the exp",
  learningObjectIds: ["fx_lo_softmax"],
  closed: true,
  closeReason: "goal_reached",
  feed: [
    { kind: "message", text: "Each score becomes a weight: $p_k = e^{h_k} / \\sum_j e^{h_j}$. Taking the log turns the division into a subtraction:\n\n$$\\ln p_k = h_k - \\ln \\sum_{j=1}^{n} e^{h_j} = h_k - \\operatorname{LSE}(h_1, h_2, \\ldots, h_n)$$\n\nSo the loss for the right class $y$ is the gap between the log-sum-exp and its score.", choices: [] },
    { kind: "check", checkRef: "fx_chk1", node: "n1", question: "If every score goes up by 3, what happens to the loss?", form: "free", choices: [], unanchored: false },
    { kind: "learner", text: "nothing: the log-sum-exp goes up by 3 as well, so the gap stays the same", checkRef: "fx_chk1" },
    { kind: "check_result", checkRef: "fx_chk1", result: "correct", graderFeedback: "Right: a shared shift cancels in $h_y - \\operatorname{LSE}(h)$.", unanchored: false, answerLabel: null },
    { kind: "close", reason: "goal_reached", recap: "Retrieve later: the loss is $\\operatorname{LSE}(h) - h_y$, and a shared shift of the scores leaves it alone.",
      delayedChecks: [{ learningObjectId: "fx_lo_softmax", title: "softmax", purpose: "retention", due: "2026-11-25" }] },
  ],
  plan: [
    { id: "n1", statement: "the log undoes the exp", position: "visited" },
    { id: "n2", statement: "a shared shift leaves the loss alone", position: "visited" },
  ],
  openCheck: null,
  openPrediction: null,
  quickCheck: { learningObjectIds: ["fx_lo_softmax"] },
  inspector: { doctrine: "fx-doctrine", route: "fixture", model: "fixture-teacher", forecasts: [] },
};

export const FIXTURE_LESSON_SUMMARY: LessonSummaryDto = {
  lessonId: FIXTURE_LESSON_ID,
  title: "softmax + cross-entropy",
  goal: FIXTURE_LESSON_VIEW.goal,
  openedAt: T,
  closed: true,
  closeReason: "goal_reached",
  learningObjectIds: ["fx_lo_softmax"],
  madeFrom: "question",
  additionsPadId: FIXTURE_ADDITIONS_PAD_ID,
};

export function fixtureAdditionsPad(): PadViewDto {
  const block: PadBlockDto = {
    blockId: "fx_b_add1", headVersionId: "fx_b_add1_v1", kind: "text", provenance: "learner", positionKey: "a",
    bodyMd: "why does the gradient not depend on which wrong class got the mass?", payload: {}, day: null,
    createdAt: "2026-11-22T09:00:00Z", updatedAt: "2026-11-22T09:00:00Z", submissions: [],
  };
  return {
    version: 1,
    pad: { padId: FIXTURE_ADDITIONS_PAD_ID, kind: "lesson_additions", title: "your additions · softmax + cross-entropy", kept: false,
      homeDeskId: null, workbenchSessionId: null, lessonId: FIXTURE_LESSON_ID, version: 1, createdAt: T, updatedAt: T },
    blocks: [block],
    anchors: [],
  };
}

/** An opened lesson's first view: the teacher's opening, waiting for the learner. */
function openingView(lessonId: string, goal: string): LessonViewDto {
  return {
    version: 1, lessonId, goal, learningObjectIds: ["fx_lo_softmax"], closed: false, closeReason: null,
    feed: [{ kind: "message", text: "Let's start from the passage you picked: what does dividing every score by $T$ do to the weights?", choices: [] }],
    plan: [{ id: "n1", statement: "temperature reshapes the weights", position: "current" }],
    openCheck: null, openPrediction: null, quickCheck: { learningObjectIds: ["fx_lo_softmax"] },
    inspector: { doctrine: "fx-doctrine", route: "fixture", model: "fixture-teacher", forecasts: [] },
  };
}

export class FixtureLessons {
  readonly calls: Array<{ command: string; input: unknown }> = [];
  private views = new Map<string, LessonViewDto>([[FIXTURE_LESSON_ID, FIXTURE_LESSON_VIEW]]);
  private summaries = new Map<string, LessonSummaryDto>([[FIXTURE_LESSON_ID, FIXTURE_LESSON_SUMMARY]]);
  private count = 0;

  constructor(private readonly delay: (ms: number) => Promise<void> = (ms) => new Promise((resolve) => setTimeout(resolve, ms))) {}

  async turn(input: LessonTurnInput): Promise<LessonViewDto> {
    this.calls.push({ command: "lesson_turn", input });
    if (input.action === "open") {
      // A turn takes a while: the opening tab shows the teacher writing meanwhile.
      await this.delay(900);
      this.count += 1;
      const lessonId = `fx_lesson_opened_${this.count}`;
      const view = openingView(lessonId, "temperature in softmax");
      this.views.set(lessonId, view);
      this.summaries.set(lessonId, { lessonId, title: "temperature in softmax", goal: view.goal, openedAt: "2026-11-23T10:00:00Z", closed: false,
        closeReason: null, learningObjectIds: ["fx_lo_softmax"], madeFrom: input.entry === "reader_selection" ? "selection" : "topic", additionsPadId: null });
      return view;
    }
    const view = this.views.get(String(input.lessonId)) ?? FIXTURE_LESSON_VIEW;
    return view;
  }

  view(input: { lessonId: string }): LessonViewDto {
    this.calls.push({ command: "lesson_view", input });
    const view = this.views.get(input.lessonId);
    if (!view) throw { code: "not_found", message: `No lesson ${input.lessonId}.` };
    return view;
  }

  list(input: { lessonIds?: string[]; learningObjectIds?: string[] }): { lessons: LessonSummaryDto[] } {
    this.calls.push({ command: "lesson_list", input });
    const all = [...this.summaries.values()].reverse();
    return { lessons: all.filter((lesson) => (!input.lessonIds || input.lessonIds.includes(lesson.lessonId))
      && (!input.learningObjectIds || lesson.learningObjectIds.some((lo) => input.learningObjectIds!.includes(lo)))) };
  }
}
