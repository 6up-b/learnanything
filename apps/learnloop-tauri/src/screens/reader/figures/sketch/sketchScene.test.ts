// Reader RW5d P2: both validators agree (spec_reader_show_me_figures_v1 §9.1).
//
// sketchSceneCorpus.json holds the problems the sidecar's validator found for
// each scene and probes result; this validator must find exactly the same.
import { describe, expect, it } from "vitest";
import corpus from "./sketchSceneCorpus.json";
import { clockSteps, impersonates, parseProgram, probeProblems, sceneProblems, SKETCH_MAX_ELEMENTS, type SketchProbe } from "./sketchScene";

describe("the shared corpus", () => {
  for (const testCase of corpus.scenes) {
    it(`scene: ${testCase.name}`, () => {
      expect(sceneProblems(testCase.scene, corpus.parameters)).toEqual(testCase.problems);
    });
  }
  for (const testCase of corpus.probe_cases) {
    it(`probes: ${testCase.name}`, () => {
      expect(probeProblems(testCase.values, corpus.probes as SketchProbe[])).toEqual(testCase.problems);
    });
  }
});

describe("the caps", () => {
  it("refuses more than the element cap", () => {
    const elements = Array.from({ length: SKETCH_MAX_ELEMENTS + 1 }, () => ({ type: "circle", cx: 0, cy: 0, r: 1 }));
    expect(sceneProblems({ viewport: { x: [0, 1], y: [0, 1] }, elements })[0]).toContain("more than 4000");
  });

  it("refuses more than the point cap", () => {
    const elements = Array.from({ length: 11 }, () => ({ type: "polyline", x: new Array(4000).fill(0), y: new Array(4000).fill(0) }));
    expect(sceneProblems({ viewport: { x: [0, 1], y: [0, 1] }, elements }).some((problem) => problem.includes("more than 40000 points"))).toBe(true);
  });
});

describe("the program", () => {
  it("reads a stored program and counts its clock steps", () => {
    const program = parseProgram(JSON.stringify({ program_version: "sketch-v1", demonstrates: "d", parameters: [], code: "x", probes: [], clock: { dt: 0.5, t_max: 10 } }));
    expect(program && clockSteps(program)).toBe(20);
    expect(parseProgram("{not json")).toBeNull();
    expect(parseProgram(JSON.stringify({ spec_version: "ifs-v1" }))).toBeNull();
  });

  it("knows the check words an identifier may not carry", () => {
    expect(impersonates("checkedByLearnLoop")).toBe(true);
    expect(impersonates("envelope")).toBe(false);
  });
});
