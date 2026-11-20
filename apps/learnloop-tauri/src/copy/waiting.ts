// "Waiting you can see" (docs/reviews/ux-waiting.md): every line the shared
// waiting indicator (components/Waiting.tsx) says, in one place so the
// deny-list test reads them all. The phone imports these same words through
// `@desktop/copy/waiting` (apps/learnloop-mobile/src/components/Waiting.tsx), so
// a wait both apps share is said the same way on both.
//
// A second line ("…Later") is said only where the wait is usually long, and
// only what the walks and the code show: grading took 13 to 33 s in the walks,
// a tutor reply 5 to 46 s, a lesson turn 11 to 83 s, a hint about 30 s.
export const WAITING_COPY = {
  /** Today's Begin, Continue and Next, and Next after feedback: the plan's next step is chosen and served
   *  (it can be a reading as well as a question, so the line does not say "question"). */
  choosingNext: "Choosing what's next…",
  /** A question the learner picked (a row of today's list, Practise for this goal), and a question loading. */
  openingQuestion: "Opening the question…",
  /** Practise for this goal: today's list is read for the goal's next question, then it is served. */
  findingGoalQuestion: "Finding a question for this goal…",
  /** Submit, until the grade is back. */
  checkingAnswer: "Checking your answer…",
  checkingAnswerLater: "This can take a minute.",
  /** Submit with no AI grading (the learner grades against the full answer): only a save. */
  savingAnswer: "Saving your answer…",
  /** The feedback screen reading the graded attempt. */
  openingFeedback: "Opening your feedback…",
  /** The tutor (Ask) writing a reply. */
  writingReply: "Writing a reply…",
  writingReplyLater: "This can take a minute.",
  /** A Teacher lesson's turn. */
  teacherWriting: "The teacher is writing…",
  teacherWritingLater: "This can take a minute or two.",
  /** A lesson's typed goal being found in the books (Find it in my books). */
  lookingInBooks: "Looking in your books…",
  /** A hint being written for the learner's work. */
  hintLater: "This can take up to half a minute.",
  /** A miss being looked into (the diagnosis), on the phone's feedback: the phone's own words, kept. */
  lookingIntoAnswer: "Looking into what happened here…",
  /** "This doesn't sound right" sent on the phone's feedback: the answer is graded again. */
  lookingAgain: "Looking again…",
  /** Today's plan being read: app start and every return to Today (the phone's words). */
  readingPlan: "Reading today's plan…",
  /** The phone's Today with the plan off: today's list being read. */
  readingList: "Reading today's list…",
  /** The phone's Read tab: the books being listed. */
  readingBooks: "Reading your books…",
  /** The phone's Reader: a book's section being opened. */
  openingSection: "Opening the section…",
  /** "Something else would help": the plan's other options being read. */
  lookingAtOptions: "Looking at what the plan could do…",
  /** A goal's details: the projection of where the goal is heading (10 to 14 s in the walks, uncached). */
  workingOutGoal: "Working out where this goal is heading…",
  /** Keep going on a finished day: the plan is extended. */
  addingMore: "Adding more to today…",
} as const;
