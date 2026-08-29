---
schema_version: 1
id: note_tutor_qa_01kz5450h56x0ftvmb1e1q95t2
subjects:
  - counting
related_los:
  - lo_analyze_and_optimize_nonuniform_collision_probab
related_concepts: []
source_type: learner_note
created_at: '2026-08-04T00:53:04Z'
updated_at: '2026-08-04T00:53:04Z'
---

# I still don't understand why replacing (x+y)e_2 with (\frac…

**Q (feedback):** I still don't understand why replacing (x+y)e_2 with (\frac{x+y}{2})e_2 doesn't change the sum

**A:** The key is that **both** $x$ and $y$ are replaced by the average $a=\frac{x+y}{2}$. Therefore

$$xe_2+ye_2=(x+y)e_2$$

becomes

$$ae_2+ae_2=2ae_2=2\left(\frac{x+y}{2}\right)e_2=(x+y)e_2.$$

So it does **not** become only $\frac{x+y}{2}e_2$; that would count just one of the two averaged variables. Equivalently, the exactly-one-variable contribution depends only on the sum $x+y$, and averaging preserves that sum.
