---
schema_version: 1
id: note_tutor_qa_01kyh7bk0p7e996nyjs80qgrm9
subjects:
  - vector-spaces
related_los:
  - lo_orient_to_the_vector_space_idea
related_concepts: []
source_type: learner_note
created_at: '2026-07-27T07:24:17Z'
updated_at: '2026-07-27T07:24:17Z'
---

# For the transfer part of this question, I said we can use t…

**Q (feedback):** For the transfer part of this question, I said we can use the 0 vector to help differentiate between 2 spaces if we don't have to carry out a full axiom proof. Would a better approach have been seeing if there's a function or linear operationr in R^2->R^2 such that we have v+w = T^{-1}(T(v)+T(w)), a * v = T^{-1}(a*T(v))?

**A:** Yes—your proposed map \(T\) is a useful **stronger, more advanced approach**, provided \(T:\mathbb R^2\to\mathbb R^2\) is bijective. The formulas

\[
v\oplus w=T^{-1}(T(v)+T(w)),\qquad a\odot v=T^{-1}(aT(v))
\]

transport the usual vector-space operations through \(T\). They show that the new structure is **isomorphic** to the usual vector space, so its axioms follow from the usual ones.

However, isomorphic does not mean that the two operation packages are literally the same. They are the same candidate structure only if

\[
v\oplus w=v+w \quad\text{and}\quad a\odot v=av
\]

for every \(v,w,a\). Otherwise, the underlying set and field are shared, but the operations—and therefore the structures—differ.

Checking the zero vector is a good quick test: under the transported operations, the additive identity is \(T^{-1}(0)\). If this differs from the usual \(0\), the structures are certainly different. But if the zeros agree, that alone does not prove the structures are the same; their sums or scalar multiples may still differ.

For the original transfer question, the simplest strategy is therefore:

1. Identify the shared data: \(\mathbb R^2\) and \(\mathbb R\).
2. Compare the two addition and scalar-multiplication rules directly.
3. Find one input where a computed sum or scalar multiple differs; that already proves the candidate structures are distinct.
4. Use a transporting bijection \(T\) only if you also want to establish that the new operations form a vector space isomorphic to the usual one without checking every axiom.
