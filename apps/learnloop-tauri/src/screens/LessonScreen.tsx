// Teacher TE1: the lesson screen (spec_teacher_v1 §19), the lesson as its own full-screen place.
//
// Reader workbench RD9a (spec_reader_workbench_v2 §11.1): its content is LessonView (./LessonView), which a desk's
// lesson window shows too; this is that content in the screen frame, unchanged. LessonView's header describes the
// lesson both show (documents not chat, checks, outages, figures, activity intervals, TE2's question and typed goal).

import { LessonView, type LessonViewProps } from "./LessonView";

export { LESSON_FIGURE_CONTRACT, LESSON_FIGURE_COPY, PROBE_POLL_MS } from "./LessonView";
export type { LessonEntry } from "./LessonView";

export function LessonScreen(props: Omit<LessonViewProps, "frame" | "onClose" | "onView" | "onStartFresh"> & {
  /** `kept`: the lesson is still open (Close never stops one), so the host can say where it is now. */
  onClose: (kept: boolean) => void;
}) {
  return <LessonView {...props} frame="screen" />;
}
