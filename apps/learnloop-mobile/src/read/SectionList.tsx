// The section list (mobile v2 §3.1), from the guide plan's sections: each title, what of it was read (on either
// device: the history is the host's), and where the learner is. Words only: reading is never evidence of
// mastery, so it carries none of the evidence glyphs.
import type { ReaderGuideSectionDto, ReaderProgressListDto } from "@desktop/api/dto";
import { Sheet } from "../shell/Sheet";
import { sectionState } from "./readerModel";

const STATE_WORD = { read: "read", started: "started", unread: "" } as const;

export function SectionList({
  sections,
  progress,
  current,
  onPick,
  onClose
}: {
  sections: readonly ReaderGuideSectionDto[];
  progress: ReaderProgressListDto | null;
  current: string | null;
  onPick: (sectionId: string) => void;
  onClose: () => void;
}) {
  return (
    <Sheet title="Sections" onClose={onClose}>
      <ul className="list" aria-label="Sections">
        {sections.map((section) => {
          const state = STATE_WORD[sectionState(section.id, progress)];
          return (
            <li key={section.id}>
              <button type="button" aria-current={section.id === current ? "true" : undefined} onClick={() => onPick(section.id)}>
                <span>{section.label}</span>
                {section.id === current ? <span className="dim"> · you're here</span> : state ? <span className="dim"> · {state}</span> : null}
              </button>
            </li>
          );
        })}
      </ul>
    </Sheet>
  );
}
