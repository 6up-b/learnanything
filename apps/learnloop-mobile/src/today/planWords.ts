// Mobile v2 §2.2, J1: the plan in the learner's words, on the phone. The desktop's
// `app/todayPlan.ts` says the same things, but it imports the desktop's Tauri client, so the phone
// keeps this small formatter (§5.3: shared modules only when they reach no `@tauri-apps/*`). Like
// the desktop's, it formats and decides nothing: every number is one the plan DTO carries (G3), the
// lanes are never named, and the only count is what waits for the desktop (ux §4.1).
import type { DailyPlanBodyDto, PlanBlockDto, PlanLane } from "@desktop/api/dto";
import type { PhonePlanDto, PhoneStepDto } from "../api/phone";

function titles(list: readonly string[]): string {
  const unique = [...new Set(list.filter(Boolean))];
  if (unique.length <= 2) return unique.join(" and ");
  return `${unique.slice(0, 2).join(", ")} and more`;
}

function questions(count: number): string {
  return count === 1 ? "1 short question" : `${count} short questions`;
}

function minutesWord(minutes: number): string {
  return minutes === 1 ? "1 minute" : `${minutes} minutes`;
}

/** What a block does, in words (never its lane's name). */
export function blockPhrase(block: Pick<PlanBlockDto, "lane" | "items" | "learningObjectTitles" | "reading" | "chosenBy">): string {
  if (block.reading) return `read ${block.reading.sectionTitle?.trim() || "the next section"}`;
  const about = titles(block.learningObjectTitles);
  if (block.chosenBy === "learner_pick") return `your pick, ${about || "a question"}`;
  const open = block.items.filter((item) => item.state === "planned" || item.state === "served").length || block.items.length;
  switch (block.lane as PlanLane | null) {
    case "maintain":
      return `${questions(open)} from earlier days`;
    case "repair":
      return "a fix for a mix-up";
    case "new":
      return about ? `new: ${about}` : "something new";
    case "push":
      return about ? `a step further on ${about}` : "a step further";
    default:
      return about || questions(open);
  }
}

/** "About 18 minutes left today: 3 short questions from earlier days." Null with nothing open. */
export function planSentence(plan: DailyPlanBodyDto): string | null {
  const open = plan.blocks.filter((block) => block.status !== "done");
  const current = open.find((block) => block.id === plan.currentBlockId) ?? open[0];
  const ahead = current ? blockPhrase(current) : plan.projected[0] ? "more to choose as you go" : null;
  if (!ahead) return null;
  const begun = plan.blocks.some((block) => block.status === "done" || Boolean(block.startedAt));
  if (plan.minutesAreASuggestion) {
    const past = Math.round(plan.minutesPastPlan ?? 0);
    const head = begun
      ? past > 0
        ? `About ${minutesWord(past)} past today's suggested time`
        : `About ${minutesWord(Math.max(1, Math.round(plan.minutesLeft)))} left of today's suggested time`
      : `About ${minutesWord(Math.max(1, Math.round(plan.minutesBudget)))} suggested today`;
    return `${head}: ${ahead}.`;
  }
  const head = begun
    ? `About ${minutesWord(Math.max(1, Math.round(plan.minutesLeft)))} left today`
    : `${minutesWord(Math.max(1, Math.round(plan.minutesBudget)))} today`;
  return `${head}: ${ahead}.`;
}

/** "Done for today · 26 minutes." The time spent, never a count of items. */
export function doneLine(data: PhonePlanDto): string {
  const minutes = Math.max(0, Math.round(data.day?.actualMinutes ?? 0));
  return minutes > 0 ? `Done for today · ${minutesWord(minutes)}.` : "Done for today.";
}

/** The one count the phone shows (ux §4.1): what explains an absence. Null when nothing waits. */
export function waitingForDesktop(data: PhonePlanDto | null | undefined): string | null {
  const questionsWaiting = data?.device?.deferredCount ?? 0;
  const readings = data?.device?.readingsWaiting ?? 0;
  const parts: string[] = [];
  if (questionsWaiting > 0) parts.push(questionsWaiting === 1 ? "1 question is" : `${questionsWaiting} questions are`);
  if (readings > 0) parts.push(readings === 1 ? "a reading is" : `${readings} readings are`);
  if (parts.length === 0) return null;
  if (parts.length === 1) return `${capitalized(parts[0])} waiting for the desktop.`;
  return `${capitalized(parts[0].replace(/ (is|are)$/, ""))} and ${parts[1].replace(/ (is|are)$/, "")} are waiting for the desktop.`;
}

function capitalized(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** The step a reply names: the step itself, or (a read) the plan's next step. */
export function stepOf(data: PhonePlanDto | null | undefined): PhoneStepDto | null {
  if (!data) return null;
  if (data.step !== undefined) return data.step ?? null;
  return (data.plan?.nextStep ?? null) as PhoneStepDto | null;
}

/** The current block's own "why" and its receipts (why? and details ▸, collapsed: ux §4.1). */
export function currentWhy(plan: DailyPlanBodyDto): { why: string | null; details: string | null; decisionId: string | null } {
  const current = plan.blocks.find((block) => block.id === plan.currentBlockId) ?? null;
  return {
    why: current?.why?.trim() || null,
    details: current?.whyDetails ?? null,
    decisionId: current?.objectiveDecisionId ?? null
  };
}
