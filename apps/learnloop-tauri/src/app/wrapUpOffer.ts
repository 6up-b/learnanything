// Reader workbench RW6a (spec §9.1, UX S11): the wrap-up offer appears where
// the learner lands after leaving the Reader -- Today or the library -- for
// one view, never in the Reader being closed. The App arms it on that one
// transition and disarms it on the next tab change.
export type WrapUpLanding = "today" | "library";

export function wrapUpOfferArmed(previousTab: string, nextTab: string): boolean {
  return previousTab === "reader" && (nextTab === "today" || nextTab === "library");
}
