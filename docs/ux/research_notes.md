# Research notes behind `ux_learnloop_v1.md`

These notes back §2 and §3 of `docs/specs/ux_learnloop_v1.md` and give fuller quotes than the spec does. Collected 2026-10-12/13.

How to read them:
- Text in "double quotes" is verbatim from the page as read.
- Where a passage is paraphrased, it says so.
- Anything about LearnLoop is inference. These notes do not quote it as a source.

## 1. Scott Jenson, "Are we stuck with the same Desktop UX forever? | Ubuntu Summit 25.10"

**The talk**
- Video: <https://www.youtube.com/watch?v=1fZTOjd_bOQ>. Uploaded 2025-12-11, 43:30 long.
- The session took place on 2025-10-24 in London. Schedule and abstract: <https://discourse.ubuntu.com/t/are-we-stuck-with-the-same-desktop-ux-forever/67253>.
- Abstract: "This talk focuses on that evil little term "UX/UI," which is responsible for so much confusion and tension in open-source projects. Not only does it unnecessarily pit programmers against designers, but it also limits our vision of what we could be doing."

**About the transcript**
- The quotes come from YouTube's auto-generated English captions, read in full. They may contain transcription errors.
- Time codes mark the start of each caption chunk.
- The slides are not online.

### Quotes from the talk

- On settings (5:44): "the fact that they actually make you pick your window manager when you boot is just the ultimate UX sin, right? Um, UX designers in general don't like to like settings that much. I realize that's not a popular opinion here."
- On change (9:36): "Users always don't like change. So, that's not controversial. The issue is what do you do about it? How do you roll it out in a way that is sensitive and doesn't like freak them out and can be done slowly."
- On the term UX/UI (15:14): "It is the most destructive term we have inflicted upon ourselves because it confuses everybody."
- On how designers and programmers think (18:36): "programmers think mathematically and designers think stat statistically… Programmers tend to be in the might category… They find every possible problem, right? Designers, of course, think statistically."
- On learning loops, borrowed from Raph Koster (21:56): "The user has a mental model and they have an intent. So then they look on the screen and they find an affordance to do their action and they get a result which gives them feedback. And then what happens is you go back the loop and you learn."
- On fun (22:30): "Fun is just another word for learning… you have to teach people how to use your product. And the more they learn, the more fun they have."
- On rushing (24:13): "the most common product mistake is rushing. People just go, go, go. They just cram things in, put in put in more menu items, put in more icons. They don't step back."
- On consistency (25:54): "this boring base is powerfully consistent. It's always a click. And we always underestimate how important consistency is."
- On loops (27:34): "So the moral of the story is don't rush, get perspective, and try to think more in loops."
- On AI (32:04): "We don't need these things to take the bar exam. We need these things to do text analysis and basic stuff."
- On programmers and consumers (38:11): "we tend to always overindex on programmers. What would happen if we actually thought about consumers a little bit?"

### Jenson's posts that the talk points to

**[How Video Games Inspire Great UX](https://jenson.org/games/)**
- "They show you EVERYTHING at the very beginning hoping you'll get it all in this one shot. Of course, we all know what happens: skip, skip, skip…."
- "APPS Tend to offer users a large toolbox and let them figure out how to get started. GAMES Have a clear understanding of the journey and say "Start here first"."
- "for App UX, hints are exactly the opposite, usually dialog box prompts in your face that stop you dead in your tracks!"
- "APPS Assume users are at a constant skill level. GAMES Use hints constantly and patiently to move users to the next level."

**[Boring is good](https://jenson.org/boring/)**
- "The user has no idea an LLM is even involved; they just get better results."
- "a mature technology doesn't look like magic; it looks like infrastructure."

**[The Paradox of Empathy](https://jenson.org/paradox/)**
- "Without clear empathic understanding of what your users need, products tend to throw the book at them, offering every possible option. This is indeed powerful, but the flow is overly complex and you'll confuse and loose many."

### Hacker News thread: <https://news.ycombinator.com/item?id=46256834>

There are 205 comments, read in full through the Algolia API. Each quote below links to its comment as `https://news.ycombinator.com/item?id=<id>`.

**Configuration vs. defaults**
- jhhh (46258932): "when some changes do create even more problems there's never any configuration to disable them".
- stephenlf (46260684): "Convention over configuration is a powerful idea. Most people don't want to twiddle with configs. The power user approach is the way to go."
- seba_dos1 (46261836): "rarely is not never, and when I do really need an option, it better be there. There's a gradient between unmaintainable multidimensional matrices of options and "one size ought to fit everyone" and both ends of it make the user miserable."
- rcxdude (46262843): "you should think about how these options interact and compose at the start, as opposed to only adding options in an ad-hoc manner".
- array_key_first (46264121): "Config on top of config on top of setting on top of options."

**Discoverability**
- bgbntty2 (46259497): "Tools and options are hidden behind menus. Even the menus are hidden behind a hamburger icon… target the technological toddlers, but then you might lose, or at least annoy, your power users."
- mrob (46258721): "Whenever there is a list of choices, all choices should be displayed, and this list should be filterable in real time by typing."

**Consistency and muscle memory**
- ChuckMcM (46259383): "consistency is a bigger win for the end user than form".
- chrsw (46263827): "I want to use the computer. I don't need to become an expert in computer interfaces."
- rustcleaner (46269308): "AVOID BREAKING MUSCLE MEMORY AT ALMOST ANY COST!"

**A pro-transparency voice**
- cben (46386474): "I want universal visibility into app behavior — what it accessed, what it changed… everything it logged." The spec keeps that visibility under the hood.

**Phrases that do not appear.** Neither the talk nor the thread says "design for the 80%" or "progressive disclosure". Those framings are the spec's.

## 2. Andy Matuschak, *How might we learn?* (May 2024): <https://andymatuschak.org/hmwl/>

- **Ideal learning environment.** "people will tell me about a time when they learned a lot, but learning wasn't the point. Instead, they were immersed in a situation with real personal meaning". Also: "You really do want to make doing-the-thing the primary activity. But the realities of cognitive psychology mean that in many cases, you really do need explicit guidance, scaffolding, practice, and attention to memory support."
- **Guidance in action.** "This AI system isn't trapped in its own chatbox, or in the sidebar of one application."
- **Synthesized dynamic media.** "At any time, Sam can just "view source" to tinker with this figure".
- **Contextualized study.**
  - "the AI reassures Sam that they don't necessarily need to read this entire thousand-page book right now… It's made a personal map in the book's table of contents."
  - "there's a huge amount of value in shared canonical artifacts… we can preserve those by layering personalized context as a lens on top of texts like this."
  - "those annotations won't end up trapped in this PDF: they'll feed into future discussion and practice".
- **Practice and memory.**
  - "What if this kind of reinforcement were woven into the grain of the learning medium?"
  - "one week later, you'll get an email that says: "Hey, you've probably started to forget some of what you read. Do you want to take five minutes to quickly review that material again?""
  - "Central to this is the idea of a daily ritual, a vessel for practice."
  - "memory systems are often too disconnected from my authentic practice."
- **Dynamic practice.**
  - "They install a home screen widget, which ambiently exposes them to practice prompts drawn from highlights, questions asked, and other activity the AI can access."
  - "These synthesized prompts can vary each time they're asked… The prompts get deeper and more complex over time".
  - "it's important that Sam can steer them with feedback."
- **Design principles.** "we bring guided learning to authentic contexts, rather than thinking of it as a separate activity".
- **Chatbot tutors.**
  - "Chatbot tutors aren't interested in what I'm trying to do; there's a set of things they think I should know or should be able to do, and they view me as defective until I say the right things."
  - They "can't join me where the real action is."
- **Ethics.** "The famous "bicycle for the mind" metaphor is better because it has no agenda other than the one you bring."

## 3. Matuschak's notes

| Note | Quote |
|---|---|
| [OS-level spaced repetition system](https://notes.andymatuschak.org/zNLoqjEVe5dheMKmTTyB9E3) | "What if, rather than living "inside an app's shoebox", as in Anki and other existing tools, prompts were framed more like files in folders—readable and writable throughout the system?" · "You'd import these prompts as you read, just as your browser forms a history as you read." · "Your PDF and e-book reader's annotations could naturally be surfaced in this centralized SRS, rather than remaining siloed in some inaccessible sidebar." · "the system may create tentative SRS prompts based on links you've bookmarked or phrases you've searched for repeatedly." |
| [SRS can be used to program attention](https://notes.andymatuschak.org/zB92WZZ5baBHKZPPbWMbYEv) | "you can make a coarser decision—to devote your attention to SRS practice for 10 minutes—and then let your attention be directed by the machine within that block." |
| [SRS make memory a choice](https://notes.andymatuschak.org/zSTqsQ4ATXB61k3Z43TforN) | "Deciding to remember something with a spaced repetition system is (aspirationally) a lightweight gesture." |
| [Prompts are interleaved into the reading experience](https://notes.andymatuschak.org/zTzb8spnoqzxs3mkvPKprmn) | Contrasts a "Quizlet-style" approach with "interleaving the prompts into the reading experience at a finer granularity." |
| [Light-weight prompts](https://notes.andymatuschak.org/zCfJ4TfWWa24aKoRS7dpNc5) | "Quantum Country's median prompt review time is 6 seconds" · "If prompts were weighty like a textbook exercise, many readers would pick and choose… That extra decision makes each prompt even heavier!" |
| [Review sets create natural breaks](https://notes.andymatuschak.org/zK3NFrSoD22JaVYdBe5CbmE) | "the review sets feel like a welcome exhalation" |
| [Writing good prompts is hard](https://notes.andymatuschak.org/zKy4FsHTcf8LdkgXkMueeGL) | "it's not obvious when the prompts you've written are bad" |
| [The limiting factor is writing enough good prompts](https://notes.andymatuschak.org/z2ySBuuMjHwuewNBi65YmXD) | "writing 40 prompts will add 30-60 minutes of effortful work to otherwise casual reading sessions" |
| [Regular SRS practice is an onerous habit](https://notes.andymatuschak.org/z3DiwZKDuLxMV17mt2nWH7y) | "a successful Spaced repetition memory system must deliver significant personal value immediately… Most systems don't: they're an empty box meant for the user to fill." |
| [Onboarding depends on a critical mass of content](https://notes.andymatuschak.org/zPUXHmQEkd33qkuTCnvKVL6) | "the prompts presented in the first few weeks of practice play an outsized role in a user's experience." |
| [Optimize emotional connection](https://notes.andymatuschak.org/zPiRwRHQxGfF9Zej765PB8M) | "the critical thing to optimize is emotional connection… and conversely, to ruthlessly minimize elements which provoke a sigh." |
| [Sessions are too disconnected](https://notes.andymatuschak.org/zEmEnm29YT9Lp4mnWzPVQZJ) | "it often feels like a chore in part because it's not doing the thing" |
| [SRS make memory feel worse](https://notes.andymatuschak.org/z7eDbmw9aUV7FCYYVstUQz4) | "Your expected accuracy rate across your entire collection may be 95+%, but your accuracy rate in a given session is likely to be much lower." |
| [SRS don't rapidly demonstrate benefits](https://notes.andymatuschak.org/z8a6SPMmmTjzDGkbCmJP75Y) | "It may also be useful to surface overall progress in review sessions (as Quantum Country does)" |
| [A "skip" mechanism](https://notes.andymatuschak.org/zCajfeVzLxpqtCzvF7jXVVy) | Proposes "a "skip" button which defers a prompt with exponential backoff". It also cites Kornell & Bjork 2008: dropping flashcards "had small but consistently negative effects on learning". |
| [Destructive operations as final decisions](https://notes.andymatuschak.org/z4xE8FBHhDo5pTvJuCBPRYC) | "systems which explicitly reify "priority" and "context" are typically over-fiddly and unusable. A better "core verb" is needed." |
| [SRS lowers the stakes of destructive operations](https://notes.andymatuschak.org/zJ5Yzvba2729XKXivBBZ91J) | "If you recast the destructive operations as "not right now," they feel completely different." |
| [Inboxes only work if you trust how they're drained](https://notes.andymatuschak.org/zGKqPvetpYbvbXmPmuuvfx8) | "You'll trust an inbox system which ends up dropping 90% of items if the other 10% were the only ones you really cared about." |
| [Beware automatic import](https://notes.andymatuschak.org/zL2SPWGitsD4TruNYBzSZ7s) | "the reading inbox may intermittently become intimidatingly long. That discourages you from opening it" |
| [Give readers control over prompts](https://notes.andymatuschak.org/z8kPkXQZ3wVR5DfJ79uhnuz) | "readers should be able to disable or skip prompts that don't resonate; readers should be able to make simple edits to authors' wording" · "you can click on the highlighted text—and boom, now you'll remember it forever." |
| [Implicitly authoritarian](https://notes.andymatuschak.org/zR5H2t4iYJECveXmu1DnYvS) | "I want my collection of prompts to feel under my control." |
| [Peripheral vision](https://notes.andymatuschak.org/z4geAr5cERWdJPrdhU5gy3N) | "Software systems, by contrast, often lack this kind of peripheral vision." · "Unchanging peripheral vision desensitizes." |
| [Self-graded vs. machine-graded](https://notes.andymatuschak.org/zScaVuH9r2pwo24iD3f39bU) | "Self-graded systems outperform machine-graded systems in most respects." Also: machine-graded systems "can perform more advanced knowledge modeling". |
| [Avoid orphan prompts](https://notes.andymatuschak.org/z3uFvLFRt8ognrjd6ADZMJc) | "isolated prompts often start to feel like a burden in the review session" |

The owner's copies of several of these notes are in `docs/specs/spec_andymatusnotes.md`.

## 4. Pain points of studying, video and SRS: sources

### Textbooks and reading

- **Rereading and highlighting.** Dunlosky et al. 2013, *PSPI*, <https://doi.org/10.1177/1529100612453266>.
  - "Five techniques received a low utility assessment: summarization, highlighting, the keyword mnemonic, imagery use for text learning, and rereading."
  - Practice testing and distributed practice "received high utility assessments."
- **Illusions of competence.** Karpicke, Butler & Roediger 2009, *Memory*, <https://doi.org/10.1080/09658210802647009>.
  - "relatively few engage in self-testing or retrieval practise while studying. We propose that many students experience illusions of competence while studying".
  - Counter-evidence: Kuhbandner & Emmerdinger 2019, <https://doi.org/10.1080/09658211.2019.1610177>. Rereading is mainly "rereading not understood parts".
- **Fluency mistaken for understanding.** Bjork & Bjork 2011, <https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2016/04/EBjork_RBjork_2011.pdf>.
  - Rereading gives "a sense of familiarity or perceptual fluency that we interpret as understanding or comprehension".
  - Difficulties "become undesirable difficulties" without the background knowledge.
- **Judgments of learning.** Koriat & Bjork 2005, <https://doi.org/10.1037/0278-7393.31.2.187>.
- **Illusion of explanatory depth.** Rozenblit & Keil 2002, <https://doi.org/10.1207/s15516709cog2605_1>.
- **What self-learners say.**
  - <https://www.reddit.com/r/math/comments/ar42jo/>: "I feel like I understand things, but I can't solve problems."
  - <https://www.reddit.com/r/learnmath/comments/2c8dhm/>: "I have no way to know whether this answer I feel good about is completely wrong or not".
- **Books as a medium.** Matuschak, "Why books don't work", <https://andymatuschak.org/books/>: "Readers must run their own feedback loops."
- **Reading mathematics textbooks.** Shepherd, Selden & Selden 2012, <https://doi.org/10.1080/10986065.2012.682959>: high-ACT readers "were not effective readers of their mathematics textbooks."
- **Prior knowledge.** Hailikari et al. 2008, <https://doi.org/10.5688/aj7205113>.

### Video

- **Fluent instructors.** Carpenter et al. 2013, <https://doi.org/10.3758/s13423-013-0442-z>: "lecture fluency did not significantly affect the amount of information learned."
- **Active vs. passive learning.** Deslauriers et al. 2019, *PNAS*, <https://doi.org/10.1073/pnas.1821936116>.
- **Illusion of skill from watching.** Kardas & O'Brien 2018, <https://doi.org/10.1177/0956797617740646>: "repeatedly watching others can foster an illusion of skill acquisition".
- **Interpolated tests and mind-wandering.** Szpunar, Khan & Schacter 2013, *PNAS*, <https://doi.org/10.1073/pnas.1221764110>.
- **Video length and engagement.** Guo, Kim & Rubin 2014, <https://pg.ucsd.edu/publications/edX-MOOC-video-production-and-engagement_LAS-2014.pdf>: "median engagement time is at most 6 minutes, regardless of total video length."
- **Dropout and navigation in video.**
  - Kim et al. 2014, <https://doi.org/10.1145/2556325.2566237>.
  - NoteVideo, <https://doi.org/10.1145/2470654.2466147>.
  - Visual Transcripts, <https://doi.org/10.1145/2816795.2818123>.
- **MOOC attrition.** Reich & Ruipérez-Valiente 2019, <https://webs.um.es/jruiperez/papers/journals/2019_Science_MOOCPivot_postprint.pdf>: "52% never enter the courseware".

### Flashcards and SRS

- **Writing prompts.** Matuschak, "How to write good prompts", <https://andymatuschak.org/prompts/>.
  - "you're likely to give them mostly bad prompts"
  - "Discourage pattern matching…"
- **The skill barrier.** Matuschak & Nielsen, <https://numinous.productions/ttft/>: "making good cards is a difficult skill to master."
- **Orphans and backlog.** Nielsen, "Augmenting Long-term Memory", <http://augmentingcognition.com/ltm.html>.
  - "lonely orphans"
  - "It's intimidating to come back to find you have 500 cards to review in a day."
- **Anki's own warnings.** Anki manual, deck options, <https://docs.ankiweb.net/deck-options.html>.
  - "has become overwhelmed by the reviews required"
  - "Make sure you understand the options before changing them".
- **Interval hell and FSRS.** Anki FAQ on SM-2 and FSRS, <https://docs.ankiweb.net/faqs/what-spaced-repetition-algorithm>: "low interval hell"; FSRS "solved by mean reversion of difficulty" (FSRS FAQ via <https://forums.ankiweb.net/t/does-fsrs-solve-ease-hell/38275>).
- **Load balancing and easy days.** Anki 24.11, <https://github.com/ankitects/anki/releases/tag/24.11>.
- **Probability-based review.** Readwise, <https://docs.readwise.io/readwise/docs/faqs/reviewing-highlights>: "a decaying algorithm based on a recall probability half-life rather than a date-based algorithm".
- **Cards keep their context.** RemNote, <https://help.remnote.com/en/articles/6025481-creating-flashcards>: the review shows "all of the ancestors of the bullet".
- **What users say, on HN.**
  - 39165811: "the huge backlog is too much that I give up"
  - 39006302: "I just want to practice when I feel like it"
  - 39293926: "Anki feels like Microsoft Word"
  - 10729202: "manually making cards was too tedious"
- **What users say, on r/Anki.** "20 reasons why Anki isn't popular", <https://www.reddit.com/r/Anki/comments/1i17ckd/>.

### Learning apps in general

- **Feature fatigue.** Thompson, Hamilton & Rust 2005, <https://doi.org/10.1509/jmkr.2005.42.4.431>.
- **Choice overload.** Iyengar & Lepper 2000, <https://doi.org/10.1037/0022-3514.79.6.995>. Counter-evidence: Scheibehenne et al. 2010 meta-analysis, <https://ideas.repec.org/a/oup/jconrs/v37y2010i3p409-425.html>, "mean effect size of virtually zero".
- **Gamification.** Sailer & Homner 2020, <https://doi.org/10.1007/s10648-019-09498-w>. Rodrigues et al. 2022, <https://doi.org/10.1186/s41239-021-00314-6>.
- **Streaks.**
  - Duolingo, <https://blog.duolingo.com/how-duolingo-streak-builds-habit/>.
  - Silverman & Barasch 2023, <https://doi.org/10.1093/jcr/ucac029>.
  - Lally et al. 2010, <https://doi.org/10.1002/ejsp.674>.
- **Algorithm aversion.** Dietvorst et al. 2015, <https://doi.org/10.1037/xge0000033>. Dietvorst et al. 2018, <https://doi.org/10.1287/mnsc.2016.2643>.
- **Learning dashboards.** Matcha et al. 2019, <https://doi.org/10.1109/tlt.2019.2916802>.
- **Self-regulated learning.** Bjork, Dunlosky & Kornell 2013, <https://doi.org/10.1146/annurev-psych-113011-143823>. Kizilcec et al. 2020, <https://doi.org/10.1073/pnas.1921417117>.

### Caveats

- Forum quotes are anecdotes, not prevalence data.
- Duolingo's figures are company-reported.
- One education-app retention figure (about 2% at day 30) was seen only in a search snippet and is not relied on.
- Ariely & Wertenbroch 2002 on deadlines carries a 2026 retraction notice. It is not cited.
