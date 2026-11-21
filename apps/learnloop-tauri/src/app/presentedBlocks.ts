// What a practice question shows, in order (the sidecar's presentation blocks), on the desktop and the phone alike.
//
// Every block is shown, whatever its kind, with one exception: an error hunt's work to check whose text the prompt
// already holds. The writer sometimes copies the work into the prompt ("Submitted work: …") as well as into the
// item's own worked solution, and the learner then read the same work twice (the live walk partread-3: "the worked
// solution was printed twice"). Shown once, in the prompt, nothing is lost: the block's text is all there. A laddered
// stem's shared setup is never left out (a part can be served days after the others; see `ItemPresentation`).
//
// Pure: the phone imports it (`@desktop/app/presentedBlocks`), so it reaches no Tauri binding.

import type { PresentationBlockDto } from "../api/dto";

/** Text as a reader sees it: runs of white space (line breaks included) are one space, none at either end. */
function plain(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

/** The blocks to show: all of them, less an error hunt's work whose text (white space aside) is already in a prompt. */
export function presentedBlocks<T extends Pick<PresentationBlockDto, "kind" | "markdown">>(blocks: readonly T[]): T[] {
  const prompts = blocks.filter((block) => block.kind === "prompt").map((block) => plain(block.markdown));
  return blocks.filter((block) => {
    if (block.kind !== "error_hunt_worked_solution") return true;
    const work = plain(block.markdown);
    return work === "" || !prompts.some((prompt) => prompt.includes(work));
  });
}
