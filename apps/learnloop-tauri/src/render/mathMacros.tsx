import { createContext, useContext, type ReactNode } from "react";

/**
 * The TeX macros of the source whose math is on screen (`mathMacros` of `reader.render_view` and of a side-by-side
 * section), for every `MarkdownMath` below the provider. A book defines its notation once (`\vvec`, `\real`) where
 * the extraction does not keep it; without the table KaTeX shows those commands as red raw text, or `\real` as its
 * own ℜ. The sidecar bounds the table and drops any definition that could include, define or re-catcode anything;
 * each body only ever reaches KaTeX as a macro, under KaTeX's own expansion limit.
 *
 * A provider with `null` (or an empty table) is no macros: the second pane shows another book, and the open book's
 * notation must not reach it.
 */
export type MathMacros = Readonly<Record<string, string>>;

const MathMacrosContext = createContext<MathMacros | null>(null);

export function MathMacrosProvider({ macros, children }: { macros: MathMacros | null | undefined; children: ReactNode }) {
  const table = macros && Object.keys(macros).length > 0 ? macros : null;
  return <MathMacrosContext.Provider value={table}>{children}</MathMacrosContext.Provider>;
}

/** The macros in force here, or null when none are. */
export function useMathMacros(): MathMacros | null {
  return useContext(MathMacrosContext);
}
