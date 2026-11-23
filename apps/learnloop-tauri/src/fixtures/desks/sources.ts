// The desks' synthetic workspace (spec §18.3): project-authored text only. A short self-written book on
// softmax, a short self-written note in the shape of a paper on attention, and a synthetic transcript
// for a video on the same idea. Nothing here comes from an owner's vault, a book or the mockups.
import type {
  ReaderGuidePlanDto,
  ReaderGuideSectionDto,
  ReaderRenderBlockDto,
  ReaderRenderViewDto,
  ReaderWatchPlanDto,
  SourceLibraryCard,
} from "../../api/dto";

function block(spanId: string, blockType: string, markdown: string, extractorBlockId?: string): ReaderRenderBlockDto {
  return {
    displayNodeId: `node-${spanId}`,
    spanId,
    blockType,
    ...(extractorBlockId ? { extractorBlockId } : {}),
    markdown,
    sanitized: false,
    katexNodes: [],
    assets: [],
    health: { status: "ok", recommendedView: "derived", reasonFlags: [] },
  };
}

interface Section {
  id: string;
  title: string;
  paragraphs: string[];
}

const SOFTMAX_SECTIONS: Section[] = [
  {
    id: "s1",
    title: "1 Scores into weights",
    paragraphs: [
      "A classifier ends with one number per class, a score. Scores can be any real numbers, and on their own they say only which class is ahead, not by how much it should be trusted.",
      "Softmax turns a list of scores $z_1, \\dots, z_K$ into a list of weights that are positive and add up to one: $$p_k = \\frac{e^{z_k}}{\\sum_{j=1}^{K} e^{z_j}}.$$",
      "The largest score gets the largest weight, but every class keeps some. That is why softmax is called a soft maximum: it keeps the winner and the runners-up in proportion.",
      "Adding the same constant $c$ to every score changes nothing, since $e^{z_k + c} = e^{c} e^{z_k}$ and the factor $e^{c}$ cancels between the top and the bottom of the fraction.",
    ],
  },
  {
    id: "s2",
    title: "2 Why the exponential",
    paragraphs: [
      "Any positive, increasing function would make scores into positive weights. The exponential is chosen because differences in scores become ratios of weights: $p_a / p_b = e^{z_a - z_b}$.",
      "A score one unit higher is always worth the same factor $e \\approx 2.72$, wherever on the line the two scores sit. Nothing about the scale of the scores matters, only their gaps.",
      "With a base other than $e$, say $b$, the same holds with the factor $b$; writing $b^{z} = e^{z \\ln b}$ shows this is the exponential with every score multiplied by $\\ln b$.",
    ],
  },
  {
    id: "s3",
    title: "3 Temperature",
    paragraphs: [
      "Dividing every score by a temperature $T > 0$ before the exponential gives $$p_k(T) = \\frac{e^{z_k / T}}{\\sum_j e^{z_j / T}}.$$",
      "A low temperature sharpens the weights toward the largest score; a high temperature flattens them toward equal shares. At $T = 1$ it is plain softmax.",
      "Take the scores $(1, 2, 1)$. At $T = 1$ the middle class gets about $0.58$ and each other about $0.21$; at $T = 0.5$ the middle class gets about $0.79$.",
      "Scaling the scores in a model, for example dividing a dot product by the square root of its length, is a temperature chosen so the weights do not saturate.",
    ],
  },
  {
    id: "s4",
    title: "4 Cross-entropy",
    paragraphs: [
      "To train the scores, compare the weights with the true class $y$. Cross-entropy charges $-\\ln p_y$: nothing when the model is sure and right, a lot when it is sure and wrong.",
      "Written in the scores, the loss is $$L = -z_y + \\ln \\sum_j e^{z_j}.$$ The first term pushes the true score up; the second, a smooth maximum of all the scores, pushes the largest ones down.",
      "If the model gives the true class a weight of $0.1$, the loss is $\\ln 10 \\approx 2.30$; at $0.9$ it is about $0.105$.",
    ],
  },
  {
    id: "s5",
    title: "5 The gradient",
    paragraphs: [
      "The derivative of the loss with respect to each score is strikingly simple: $$\\frac{\\partial L}{\\partial z_k} = p_k - [k = y].$$",
      "Every wrong class is pushed down by its own weight, and the true class is pushed up by what it is missing from one. When the weights match the one-hot target, the gradient is zero.",
      "A quick check by finite differences: nudge one score by a small $h$, recompute the loss, and divide the change by $h$; the result should agree with $p_k - [k = y]$ to a few digits.",
    ],
  },
  {
    id: "s6",
    title: "6 Computing it safely",
    paragraphs: [
      "Exponentials overflow quickly: $e^{1000}$ is not a number a computer can hold. Because adding a constant changes nothing, subtract the largest score first: $z_k - \\max_j z_j$.",
      "After the shift the largest exponent is $e^0 = 1$, every other one is at most one, and the sum lies between $1$ and $K$.",
      "The same shift keeps the loss safe: $\\ln \\sum_j e^{z_j} = m + \\ln \\sum_j e^{z_j - m}$ with $m = \\max_j z_j$, the log-sum-exp trick.",
    ],
  },
];

const PAPER_SECTIONS: Section[] = [
  {
    id: "p1",
    title: "1 Attention as a weighted average",
    paragraphs: [
      "A query looks at a set of keys and asks how well each matches. The matches are scores; softmax turns them into weights; the weights average the values attached to the keys.",
      "With queries $Q$, keys $K$ and values $V$ stacked as matrices, the whole step is $$\\operatorname{attend}(Q, K, V) = \\operatorname{softmax}\\!\\left(\\frac{Q K^{\\top}}{\\sqrt{d}}\\right) V.$$",
    ],
  },
  {
    id: "p2",
    title: "2 Why divide by the square root",
    paragraphs: [
      "If the entries of a query and a key are independent with mean zero and variance one, their dot product over $d$ entries has variance $d$. Large scores push softmax to a single winner, where its gradient vanishes.",
      "Dividing by $\\sqrt{d}$ brings the variance back to one: a temperature set by the dimension.",
    ],
  },
  {
    id: "p3",
    title: "3 Masks",
    paragraphs: [
      "To stop a position from attending to later ones, its scores for those positions are set to $-\\infty$ before softmax, so their weights are exactly zero.",
    ],
  },
];

function bookView(sourceId: string, extractionId: string, sections: Section[]): ReaderRenderViewDto {
  const blocks: ReaderRenderBlockDto[] = [];
  for (const section of sections) {
    blocks.push(block(`${extractionId}_${section.id}_h`, "Section", `## ${section.title}`));
    section.paragraphs.forEach((text, index) => blocks.push(block(`${extractionId}_${section.id}_${index + 1}`, "Text", text)));
  }
  return {
    renderViewId: `rv_${extractionId}`,
    extractionId,
    revisionId: `rev_${extractionId}`,
    sourceId,
    renderer: "marker_markdown",
    rendererVersion: "1",
    contentHash: `sha256:${extractionId}`,
    status: "ready",
    layers: {},
    blocks,
    otherReadings: [],
  };
}

function guideOf(view: ReaderRenderViewDto, sections: Section[]): ReaderGuidePlanDto {
  const out: ReaderGuideSectionDto[] = sections.map((section) => {
    const spanIds = view.blocks.filter((each) => each.spanId?.startsWith(`${view.extractionId}_${section.id}_`)).map((each) => each.spanId as string);
    return { id: `${view.extractionId}_${section.id}`, label: section.title, startSpanId: spanIds[0], endSpanId: spanIds[spanIds.length - 1], spanIds, question: null, suggestedPassages: [] };
  });
  return { sourceId: view.sourceId, extractionId: view.extractionId, personalized: false, selectionBasis: "fixture", goalContext: null, sections: out };
}

const CUE_TEXT = [
  "So we have three scores, one for each class.",
  "They can be any numbers at all, negative too.",
  "What we want is weights that add up to one.",
  "First make each score positive with the exponential.",
  "Then divide each by the sum of all of them.",
  "Notice the biggest score still gets the biggest share.",
  "But the others do not drop to zero.",
  "Now watch what happens if I add ten to every score.",
  "Every exponential grows by the same factor.",
  "And that factor cancels in the division.",
  "So only the gaps between scores matter.",
  "Let us put a temperature in front.",
  "Divide by a half and the winner pulls ahead.",
  "Divide by two and everything flattens out.",
  "This is the knob people turn when sampling text.",
  "Next, how do we train the scores?",
  "We look at the weight on the right answer.",
  "And take minus its logarithm as the loss.",
  "If the weight is one, the loss is zero.",
  "If the weight is tiny, the loss is large.",
  "The gradient turns out to be very tidy.",
  "It is the weight minus one for the right class.",
  "And just the weight for every other class.",
  "Let me check that numerically with a small nudge.",
  "The numbers agree to four places.",
  "One last thing: big scores overflow.",
  "So subtract the largest score first.",
  "Nothing changes, and nothing overflows.",
  "That is softmax, end to end.",
  "Thanks for watching.",
];

function transcriptView(sourceId: string, extractionId: string): ReaderRenderViewDto {
  const blocks = CUE_TEXT.map((text, index) => {
    const start = index * 6;
    return block(`${extractionId}_c${index + 1}`, "Text", text, `t=${start}-${start + 6}`);
  });
  return {
    renderViewId: `rv_${extractionId}`,
    extractionId,
    revisionId: `rev_${extractionId}`,
    sourceId,
    renderer: "captions",
    rendererVersion: "2",
    contentHash: `sha256:${extractionId}`,
    status: "ready",
    layers: {},
    blocks,
    otherReadings: [],
  };
}

function card(sourceId: string, title: string, kindNoun: string, canonicalUri: string): SourceLibraryCard {
  return {
    sourceId, title, acquisitionKind: "fixture", canonicalUri, workId: null, currentRevisionId: `rev_${sourceId}`, revisionCount: 1,
    readiness: "ready", unitCount: 1, blockCount: 1, extractionStatus: "completed", suggestedRole: null, readerEnabled: true,
    updateAvailable: false, kindNoun,
  };
}

/** The videos' ids are synthetic: the harness never loads YouTube (its frames are served locally). */
export const FIXTURE_VIDEO_IDS = { byHand: "fxSoftmax01", masks: "fxMasks0002" } as const;

export const FIXTURE_SOURCES = {
  book: { sourceId: "fx_src_softmax", extractionId: "fx_ext_softmax" },
  paper: { sourceId: "fx_src_attention", extractionId: "fx_ext_attention" },
  video: { sourceId: "fx_src_video", extractionId: "fx_ext_video" },
  video2: { sourceId: "fx_src_video2", extractionId: "fx_ext_video2" },
} as const;

export const FIXTURE_VIEWS: Record<string, ReaderRenderViewDto> = {
  [FIXTURE_SOURCES.book.sourceId]: bookView(FIXTURE_SOURCES.book.sourceId, FIXTURE_SOURCES.book.extractionId, SOFTMAX_SECTIONS),
  [FIXTURE_SOURCES.paper.sourceId]: bookView(FIXTURE_SOURCES.paper.sourceId, FIXTURE_SOURCES.paper.extractionId, PAPER_SECTIONS),
  [FIXTURE_SOURCES.video.sourceId]: transcriptView(FIXTURE_SOURCES.video.sourceId, FIXTURE_SOURCES.video.extractionId),
  [FIXTURE_SOURCES.video2.sourceId]: transcriptView(FIXTURE_SOURCES.video2.sourceId, FIXTURE_SOURCES.video2.extractionId),
};

export const FIXTURE_GUIDES: Record<string, ReaderGuidePlanDto> = {
  [FIXTURE_SOURCES.book.extractionId]: guideOf(FIXTURE_VIEWS[FIXTURE_SOURCES.book.sourceId], SOFTMAX_SECTIONS),
  [FIXTURE_SOURCES.paper.extractionId]: guideOf(FIXTURE_VIEWS[FIXTURE_SOURCES.paper.sourceId], PAPER_SECTIONS),
};

export const FIXTURE_WATCH: Record<string, ReaderWatchPlanDto> = {
  [FIXTURE_SOURCES.video.sourceId]: {
    sourceId: FIXTURE_SOURCES.video.sourceId, videoId: FIXTURE_VIDEO_IDS.byHand, pausePoints: [],
    embedUrl: `https://www.youtube-nocookie.com/embed/${FIXTURE_VIDEO_IDS.byHand}?enablejsapi=1`,
  },
  [FIXTURE_SOURCES.video2.sourceId]: {
    sourceId: FIXTURE_SOURCES.video2.sourceId, videoId: FIXTURE_VIDEO_IDS.masks, pausePoints: [],
    embedUrl: `https://www.youtube-nocookie.com/embed/${FIXTURE_VIDEO_IDS.masks}?enablejsapi=1`,
  },
};

export const FIXTURE_LIBRARY: SourceLibraryCard[] = [
  card(FIXTURE_SOURCES.book.sourceId, "Softmax, a short book", "book", "fixture://softmax-book"),
  card(FIXTURE_SOURCES.paper.sourceId, "Attention as averaging (a note)", "paper", "fixture://attention-note"),
  card(FIXTURE_SOURCES.video.sourceId, "Softmax by hand (synthetic captions)", "video", `https://www.youtube.com/watch?v=${FIXTURE_VIDEO_IDS.byHand}`),
  card(FIXTURE_SOURCES.video2.sourceId, "Masks in attention (synthetic captions)", "video", `https://www.youtube.com/watch?v=${FIXTURE_VIDEO_IDS.masks}`),
];
