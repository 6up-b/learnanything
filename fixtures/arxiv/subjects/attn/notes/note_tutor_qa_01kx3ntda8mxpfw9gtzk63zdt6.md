---
schema_version: 1
id: note_tutor_qa_01kx3ntda8mxpfw9gtzk63zdt6
subjects:
  - attn
related_los:
  - lo_causal_masking
related_concepts: []
source_type: learner_note
created_at: '2026-07-09T14:51:59Z'
updated_at: '2026-07-09T14:51:59Z'
---

# Why do we need to hide future tokens from past tokens? What…

**Q (practice):** Why do we need to hide future tokens from past tokens? What happens if future tokens are included within attention?

**A:** Think about the training setup for GPT: at each position, the model is supposed to predict the **next** token using only the tokens that came before it.

If a position could attend to tokens that are actually **after** it, what information would it have access to during training that it would not have during real generation?

A useful way to reason about it: for token position `i`, ask which positions should be valid evidence for predicting from position `i`, and which positions would leak information from the answer or the future.
