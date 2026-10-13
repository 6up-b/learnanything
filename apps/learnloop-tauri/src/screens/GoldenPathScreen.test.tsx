import { afterEach, expect, it, vi } from "vitest";

vi.mock("../api/client", () => ({ api: {} }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: () => null }));

import { setAlgoConfig } from "../app/algoConfig";
import { triageCoarseOptions } from "./GoldenPathScreen";

afterEach(() => setAlgoConfig(undefined));

// mvp-0.13: the golden path's "I didn't know" report is worded "I was stuck";
// its value stays failure triage's coarse class, so routing is unchanged.
it("words the triage outcome as the vault's answer surfaces do", () => {
  setAlgoConfig({ practice: { stuckPrompt: true } });
  const stuck = triageCoarseOptions();
  expect(stuck.find((option) => option.value === "dont_know")?.label).toBe("I was stuck / left it blank");
  expect(stuck.map((option) => option.value)).toEqual(["wrong", "dont_know", "correct"]);

  setAlgoConfig({ practice: { stuckPrompt: false } });
  const before = triageCoarseOptions();
  expect(before.find((option) => option.value === "dont_know")?.label).toBe("I didn't know / left it blank");
  expect(before.map((option) => option.value)).toEqual(stuck.map((option) => option.value));
});
