// The intent box's contract as the sidecar sends it with every RW1b switch on,
// RW4a's library ask on and RW7a's reading paths on (reader.prompt_contract's `intent`, generated from
// learnloop.reader.reader_intent's catalogue: tests/test_reader_intentions.py
// pins the same table). Used by the Reader's RW1b and RW4a tests.
import type { ReaderIntentContractDto } from "../api/dto";

export const readerIntentContractFixture: ReaderIntentContractDto = {
  "palette": [
    {
      "group": "understand",
      "label": "Understand",
      "intention": "understand",
      "actions": [
        {
          "id": "ask_answer_directly",
          "group": "understand",
          "intention": "understand",
          "label": "ask",
          "effect": {
            "kind": "ask",
            "answerMode": "answer_directly"
          },
          "model": true
        },
        {
          "id": "ask_help_me_reason",
          "group": "understand",
          "intention": "understand",
          "label": "ask · help me reason",
          "effect": {
            "kind": "ask",
            "answerMode": "help_me_reason"
          },
          "model": true
        },
        {
          "id": "ask_ask_me_first",
          "group": "understand",
          "intention": "understand",
          "label": "ask · ask me first",
          "effect": {
            "kind": "ask",
            "answerMode": "ask_me_first"
          },
          "model": true
        },
        {
          "id": "alt_explanation",
          "group": "understand",
          "intention": "understand",
          "label": "explain differently",
          "effect": {
            "kind": "preset",
            "preset": "alt_explanation"
          },
          "model": true
        },
        {
          "id": "worked_example",
          "group": "understand",
          "intention": "understand",
          "label": "worked example",
          "effect": {
            "kind": "preset",
            "preset": "worked_example"
          },
          "model": true
        },
        {
          "id": "ask",
          "group": "understand",
          "intention": "understand",
          "label": "research this",
          "effect": {
            "kind": "preset",
            "preset": "ask"
          },
          "model": true
        },
        {
          "id": "why_step",
          "group": "understand",
          "intention": "understand",
          "label": "why does this step work?",
          "effect": {
            "kind": "active_reading",
            "style": "why_step"
          },
          "model": true
        },
        {
          "id": "assumptions",
          "group": "understand",
          "intention": "understand",
          "label": "what does this assume?",
          "effect": {
            "kind": "active_reading",
            "style": "assumptions"
          },
          "model": true
        },
        {
          "id": "another_way",
          "group": "understand",
          "intention": "understand",
          "label": "another way to see this",
          "effect": {
            "kind": "another_way"
          },
          "model": true
        }
      ]
    },
    {
      "group": "apply",
      "label": "Apply",
      "intention": "apply",
      "actions": [
        {
          "id": "work_through",
          "group": "apply",
          "intention": "apply",
          "label": "work through this",
          "effect": {
            "kind": "work_through"
          },
          "model": true
        },
        {
          "id": "next_step",
          "group": "apply",
          "intention": "apply",
          "label": "let me try the next step",
          "effect": {
            "kind": "active_reading",
            "style": "next_step"
          },
          "model": true
        },
        {
          "id": "import_exercise",
          "group": "apply",
          "intention": "apply",
          "label": "add this exercise to practice",
          "effect": {
            "kind": "import_exercise"
          },
          "model": true
        }
      ]
    },
    {
      "group": "consolidate",
      "label": "Consolidate",
      "intention": "consolidate",
      "actions": [
        {
          "id": "test_me_later",
          "group": "consolidate",
          "intention": "consolidate",
          "label": "revisit once (test me later)",
          "effect": {
            "kind": "preset",
            "preset": "test_me_later"
          },
          "model": true
        },
        {
          "id": "help_me_remember",
          "group": "consolidate",
          "intention": "consolidate",
          "label": "help me remember",
          "effect": {
            "kind": "preset",
            "preset": "help_me_remember"
          },
          "model": true
        },
        {
          "id": "reconstruct",
          "group": "consolidate",
          "intention": "consolidate",
          "label": "reconstruct this later",
          "effect": {
            "kind": "active_reading",
            "style": "reconstruct"
          },
          "model": true
        }
      ]
    },
    {
      "group": "transfer",
      "label": "Transfer",
      "intention": "transfer",
      "actions": [
        {
          "id": "connect_it",
          "group": "transfer",
          "intention": "transfer",
          "label": "connect it",
          "effect": {
            "kind": "preset",
            "preset": "connect_it"
          },
          "model": true
        },
        {
          "id": "why_matters",
          "group": "transfer",
          "intention": "transfer",
          "label": "why this matters",
          "effect": {
            "kind": "preset",
            "preset": "why_matters"
          },
          "model": true
        },
        {
          "id": "where_else_explained",
          "group": "transfer",
          "intention": "transfer",
          "label": "where else is this explained?",
          "effect": {
            "kind": "library_ask",
            "entry": "where_else_explained"
          },
          "model": true
        },
        {
          "id": "where_is_this_used",
          "group": "transfer",
          "intention": "transfer",
          "label": "where is this used?",
          "effect": {
            "kind": "library_ask",
            "entry": "where_is_this_used"
          },
          "model": true
        }
      ]
    },
    {
      "group": "orient",
      "label": "Orient",
      "intention": "orient",
      "actions": [
        {
          "id": "what_matters_here",
          "group": "orient",
          "intention": "orient",
          "label": "what matters here?",
          "effect": {
            "kind": "reading_path"
          },
          "model": false
        },
        {
          "id": "what_do_i_need_first",
          "group": "orient",
          "intention": "orient",
          "label": "what do I need first?",
          "effect": {
            "kind": "library_ask",
            "entry": "what_do_i_need_first"
          },
          "model": true
        }
      ]
    },
    {
      "group": "mark",
      "label": "Mark",
      "intention": null,
      "actions": [
        {
          "id": "highlight",
          "group": "mark",
          "intention": null,
          "label": "highlight",
          "effect": {
            "kind": "highlight"
          },
          "model": false
        },
        {
          "id": "note",
          "group": "mark",
          "intention": null,
          "label": "note",
          "effect": {
            "kind": "highlight",
            "note": true
          },
          "model": false
        },
        {
          "id": "mark_confusing",
          "group": "mark",
          "intention": null,
          "label": "confusing",
          "effect": {
            "kind": "preset",
            "preset": "mark_confusing"
          },
          "model": false
        },
        {
          "id": "not_worth_remembering",
          "group": "mark",
          "intention": null,
          "label": "not worth remembering",
          "effect": {
            "kind": "preset",
            "preset": "not_worth_remembering"
          },
          "model": false
        }
      ]
    }
  ],
  "notesPalette": [
    {
      "group": "understand",
      "label": "Understand",
      "intention": "understand",
      "actions": [
        {
          "id": "ask_answer_directly",
          "group": "understand",
          "intention": "understand",
          "label": "ask",
          "effect": {
            "kind": "ask",
            "answerMode": "answer_directly"
          },
          "model": true
        },
        {
          "id": "ask_help_me_reason",
          "group": "understand",
          "intention": "understand",
          "label": "ask · help me reason",
          "effect": {
            "kind": "ask",
            "answerMode": "help_me_reason"
          },
          "model": true
        },
        {
          "id": "ask_ask_me_first",
          "group": "understand",
          "intention": "understand",
          "label": "ask · ask me first",
          "effect": {
            "kind": "ask",
            "answerMode": "ask_me_first"
          },
          "model": true
        }
      ]
    },
    {
      "group": "consolidate",
      "label": "Consolidate",
      "intention": "consolidate",
      "actions": [
        {
          "id": "test_me_later",
          "group": "consolidate",
          "intention": "consolidate",
          "label": "revisit once (test me later)",
          "effect": {
            "kind": "preset",
            "preset": "test_me_later"
          },
          "model": true
        },
        {
          "id": "help_me_remember",
          "group": "consolidate",
          "intention": "consolidate",
          "label": "help me remember",
          "effect": {
            "kind": "preset",
            "preset": "help_me_remember"
          },
          "model": true
        }
      ]
    },
    {
      "group": "transfer",
      "label": "Transfer",
      "intention": "transfer",
      "actions": [
        {
          "id": "connect_it",
          "group": "transfer",
          "intention": "transfer",
          "label": "connect it",
          "effect": {
            "kind": "preset",
            "preset": "connect_it"
          },
          "model": true
        }
      ]
    }
  ],
  "speculative": true,
  "speculateAfterMs": 600,
  "timeoutSeconds": 4.0
};
