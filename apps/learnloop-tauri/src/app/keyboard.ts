// Shared "is the learner typing right now?" test for window-level shortcut
// handlers.
//
// tagName alone is not enough: the MathLive answer editor is a contenteditable
// <div>, so a plain-character shortcut (`:` opening the command palette) would
// swallow the keystroke mid-answer. Any handler that binds an *unmodified*
// character must go through this.
export function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName.toLowerCase();
  if (tag === "input" || tag === "textarea" || tag === "select" || tag === "math-field") return true;
  if (target.isContentEditable) return true;
  if (target.getAttribute("role") === "textbox") return true;
  // Rendered equations inside the answer editor are contenteditable="false"
  // widgets; a keystroke aimed at one is still typing into the editor around it.
  return target.closest('[contenteditable]:not([contenteditable="false"])') != null;
}
