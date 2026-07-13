---
schema_version: 1
id: note_tutor_qa_01kxcfb9bst8e83ew4rzj99jk9
subjects:
  - attn
related_los:
  - lo_decoder_causal_masking
related_concepts: []
source_type: learner_note
created_at: '2026-07-13T00:52:01Z'
updated_at: '2026-07-13T00:52:01Z'
---

# Can you clarify what it means for the decoder also using ou…

**Q (feedback):** Can you clarify what it means for the decoder also using output embeddings offset by 1 position so predictions are made from the preceding target context?

**A:** It means the decoder’s input sequence is shifted relative to what it is asked to predict.

During training, if the target sentence is:

`I like cats <eos>`

then the decoder is fed something like:

`<bos> I like cats`

and it is trained to predict:

`I like cats <eos>`

So at the position where the model predicts `like`, its input context contains only `<bos> I`, not the actual future word `like` as an input at that same prediction step. This is the “offset by one position” detail.

Causal masking and offset embeddings work together:

- The offset makes each prediction correspond to the next target token.
- The causal mask ensures each decoder position can only attend to earlier positions and itself in that shifted input.

So your original answer was right about future-token masking. The missing detail was just that the decoder is also trained with shifted target inputs, so predictions are made from the preceding target context rather than from the token being predicted or later tokens.
