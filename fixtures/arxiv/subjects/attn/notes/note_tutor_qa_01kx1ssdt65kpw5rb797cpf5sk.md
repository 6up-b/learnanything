---
schema_version: 1
id: note_tutor_qa_01kx1ssdt65kpw5rb797cpf5sk
subjects:
  - attn
related_los:
  - lo_softmax_logits_temperature
related_concepts: []
source_type: learner_note
created_at: '2026-07-08T21:22:52Z'
updated_at: '2026-07-08T21:22:52Z'
---

# If (T) is small, then the gap between a high logit and low…

**Q (practice):** If (T) is small, then the gap between a high logit and low logit should be high. This means P(high logit) is very high and P(low logit) is very low. I'm not sure why mathematically this works though even after being given the direct equation. Is this just because a low (T) value makes the exponential function steeper?

**A:** A useful way to see it is to compare two tokens instead of the whole vocabulary.

For logits \(z_h\) and \(z_l\), temperature changes the scaled gap:

\[
\frac{z_h}{T} - \frac{z_l}{T} = \frac{z_h - z_l}{T}
\]

So when \(T\) is small, the same original logit difference becomes a larger difference before exponentiation. Then softmax exponentiates those scaled scores and normalizes them across tokens.

Rather than thinking only “the exponential gets steeper,” ask: if the scaled gap doubles or triples, what happens to the ratio \(e^{z_h/T} / e^{z_l/T}\)? How would that ratio affect the probability mass after normalization?
