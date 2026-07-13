---
schema_version: 1
id: note_tutor_qa_01kxc1vhhwek0gycsbqs9s69wv
subjects:
  - attn
related_los:
  - lo_scaled_dot_product_attention
related_concepts: []
source_type: learner_note
created_at: '2026-07-12T20:56:14Z'
updated_at: '2026-07-12T20:56:14Z'
---

# Why do we divide by \sqrt{d_k} before softmax?

**Q (practice):** Why do we divide by \sqrt{d_k} before softmax?

**A:** Think about what happens to the query-key dot products as the key/query dimension \(d_k\) gets larger: if each vector has more components, what tends to happen to the size/variance of the raw dot-product scores?

Then ask: if the scores going into softmax are very large in magnitude, does softmax produce smooth weights or weights that are almost all on one position?

The \(\sqrt{d_k}\) factor is there to keep the score scale more stable before softmax, so the attention weights do not become overly sharp just because the vectors have higher dimension.
