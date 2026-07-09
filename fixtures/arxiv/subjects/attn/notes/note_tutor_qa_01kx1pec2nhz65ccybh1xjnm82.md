---
schema_version: 1
id: note_tutor_qa_01kx1pec2nhz65ccybh1xjnm82
subjects:
  - attn
related_los:
  - lo_softmax_logits_temperature
related_concepts: []
source_type: learner_note
created_at: '2026-07-08T20:24:24Z'
updated_at: '2026-07-08T20:24:24Z'
---

# I know that temperature controls the distribution output fr…

**Q (practice):** I know that temperature controls the distribution output from softmax where lower temperature makes the model collapse into a more narrow distribution while higher temperature makes the model have higher variance, but I don't know the actual equation with logits/temperature that we apply softmax to. Was it softmax(\sqrt{logit/temperature})?

**A:** Use a logit vector idea: for each vocabulary token \(i\), start with its raw score \(z_i\). Temperature is applied by scaling those scores before the softmax step:

\[
\text{softmax}(z/T)_i = \frac{e^{z_i/T}}{\sum_j e^{z_j/T}}
\]

So the operation is based on exponentiating scaled logits and then normalizing across all tokens. As a check: if \(T\) gets smaller, what happens to the gap between a high logit and a low logit after dividing by \(T\)? How would that affect the normalized probabilities?
