// Teacher TE1: "Teach me this" shows only while the sidecar says lessons may open (its `teacher` key).
import { afterEach, expect, it } from "vitest";
import { algoConfig, setAlgoConfig } from "./algoConfig";

afterEach(() => setAlgoConfig({}));

it("lessons are off until the sidecar sends its teacher key", () => {
  setAlgoConfig({});
  expect(algoConfig().lessons).toBe(false);
  setAlgoConfig({ teacher: { lessons: true } });
  expect(algoConfig().lessons).toBe(true);
  setAlgoConfig({ teacher: { lessons: "yes" } });
  expect(algoConfig().lessons).toBe(false);
});

it("Today's lesson suggestion card is off until the sidecar sends teacher.suggestions with lessons on (TE1b)", () => {
  setAlgoConfig({ teacher: { lessons: true } });
  expect(algoConfig().lessonSuggestions).toBe(false);
  setAlgoConfig({ teacher: { lessons: true, suggestions: true } });
  expect(algoConfig().lessonSuggestions).toBe(true);
  setAlgoConfig({ teacher: { suggestions: true } });
  expect(algoConfig().lessonSuggestions).toBe(false);
});
