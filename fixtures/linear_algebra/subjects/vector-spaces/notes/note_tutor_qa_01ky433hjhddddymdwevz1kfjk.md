---
schema_version: 1
id: note_tutor_qa_01ky433hjhddddymdwevz1kfjk
subjects:
  - vector-spaces
related_los: []
related_concepts: []
source_type: learner_note
created_at: '2026-07-22T04:59:52Z'
updated_at: '2026-07-22T04:59:52Z'
---

# So to my understanding, when 2 basis vectors line up that m…

**Q (reader):** So to my understanding, when 2 basis vectors line up that means they're linearly dependent (scalar multiples of each other)? What would be their cross product (since orthogonal cross product is 0) and what would be a matrix with these vectors as column's eigenvalues and eigenvectors?

**A:** Yes—if two nonzero vectors “line up,” then one is a scalar multiple of the other, say \(v=c\,u\), so they are linearly dependent. (The zero vector also makes a set dependent.)

A small correction: **parallel** vectors have zero cross product, not orthogonal vectors. In \(\mathbb R^3\),
\[
u\times v=u\times(cu)=c(u\times u)=0.
\]
For orthogonal nonzero vectors, \(\|u\times v\|=\|u\|\|v\|\), so the cross product is generally nonzero.

For eigenvalues, the vectors must form a square matrix. If \(u=(a,b)^T\) and \(v=cu\), then
\[
A=[u\;v]=\begin{pmatrix}a&ca\\b&cb\end{pmatrix}.
\]
Its determinant is \(0\), so one eigenvalue is \(\lambda_1=0\). Since the sum of the eigenvalues is the trace,
\[
\lambda_2=\operatorname{tr}(A)=a+cb.
\]
A corresponding zero-eigenvalue eigenvector is
\[
\begin{pmatrix}-c\\1\end{pmatrix},
\]
because the column combination \(-cu+v\) vanishes. Also, \(u\) is an eigenvector for \(\lambda_2=a+cb\). If \(a+cb=0\), both eigenvalues are zero and the eigenvector structure needs separate consideration.

So the key chain is: **columns line up \(\Rightarrow\) dependent columns \(\Rightarrow\) determinant zero \(\Rightarrow\) zero is an eigenvalue**.
