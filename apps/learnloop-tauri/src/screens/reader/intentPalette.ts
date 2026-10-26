// The intent box's palette and copy (reader workbench RW1b; spec §4.2; UX §4.1, W2).
//
// The palette comes from the sidecar (reader.prompt_contract's `intent`), so the
// actions that exist, their intentions and their effects are one table
// (learnloop.reader.reader_intent). This file only filters what this selection
// may offer (a held-out passage shows nothing to a model; "work through this"
// needs the workbench here) and words the routed line.
import type { ReaderIntentActionDto, ReaderIntentContractDto, ReaderIntentGroupDto } from "../../api/dto";

export const INTENT_COPY = {
  placeholder: "what do you want to do with this?",
  label: "What do you want to do with this?",
  keys: "↵ ask · tab actions · esc",
  paletteLabel: "what do you want to do?",
  paletteKeys: "↑↓ move · ↵ · esc",
  routing: "choosing",
  change: "change",
  // UX §4.10: where the box's words go.
  whereThisGoes: "Used to pick the action you meant. If it becomes a question, it's kept like one.",
  protected: "This passage is held out of LearnLoop's models. You can still highlight it, mark it and keep notes.",
} as const;

/** The groups this selection may offer: none emptied, none disabled (U13). */
export function visiblePalette(
  contract: ReaderIntentContractDto,
  options: { notes: boolean; protectedSelection: boolean; canWorkThrough: boolean; canAnotherWay?: boolean },
): ReaderIntentGroupDto[] {
  const groups = options.notes ? contract.notesPalette : contract.palette;
  return groups
    .map((group) => ({
      ...group,
      actions: group.actions.filter((action) => {
        if (options.protectedSelection && action.model) return false;
        if (action.effect.kind === "work_through" && !options.canWorkThrough) return false;
        if (action.effect.kind === "another_way" && options.canAnotherWay === false) return false;
        return true;
      }),
    }))
    .filter((group) => group.actions.length > 0);
}

export function paletteActions(groups: ReaderIntentGroupDto[]): ReaderIntentActionDto[] {
  return groups.flatMap((group) => group.actions);
}

const GROUP_WORDS: Record<string, string> = {
  understand: "Understand", apply: "Apply", consolidate: "Consolidate", transfer: "Transfer", orient: "Orient",
};

/** RW5d P1: the figure action's label while figures.show_me_enabled is on (the sidecar's palette). */
export const SHOW_ME_LABEL = "show me…";

/** The routed line, in the palette's own words (UX §4.1 microcopy): "Understand · ask · help me reason".
 *  RW5d P1: "show me" says what it will use ("from your selection and your words"). */
export function routedLine(action: Pick<ReaderIntentActionDto, "label" | "intention"> & { effect?: ReaderIntentActionDto["effect"] },
                           words?: string): string {
  const intention = action.intention ? GROUP_WORDS[action.intention] : null;
  const showMe = action.label === SHOW_ME_LABEL && action.effect?.kind === "figure";
  const label = showMe ? "show me" : action.label;
  const uses = showMe ? (words?.trim() ? "from your selection and your words" : "from your selection") : null;
  return [intention, label, uses].filter(Boolean).join(" · ");
}
