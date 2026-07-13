---
schema_version: 1
id: note_tutor_qa_01kxc23vhpqzhft1exv824kqjc
subjects:
  - attn
related_los:
  - lo_scaled_dot_product_attention
related_concepts: []
source_type: learner_note
created_at: '2026-07-12T21:00:46Z'
updated_at: '2026-07-12T21:00:46Z'
---

# if each vector has more components, then the size/variance…

**Q (practice):** if each vector has more components, then the size/variance of the raw dot-product scores should get larger. if the scores going into softmax are very large in magnitude, the softmax would produce weights that are all in one position since softmax is an exponential function (largest value is pushed to 1 then everything else is pushed to 0 since the exponential amplifies gaps)

**A:** Good line of reasoning to test. Try making it precise with two checks:

1. For a query-key dot product with \(d_k\) components, what happens to the variance of the sum if the components are roughly independent with similar variance?
2. What does dividing by \(\sqrt{d_k}\) do to that variance before the scores reach softmax?

Then connect that to softmax: when score gaps get large, the distribution becomes very peaked, so the model gets less useful gradient signal across the non-largest positions.
