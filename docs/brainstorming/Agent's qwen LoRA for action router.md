I think Qwen3-Embedding-0.6B could be a very good fit for LearnLoop's action router, particularly the action-conditioned Q/K architecture we previously discussed.

But I would make one important distinction: I wouldn't train Qwen to directly classify which tutoring action to take. I'd use its embeddings inside a learned action-value model that understands the learner's state.

That's a much more interesting approach than a conventional BERT classifier, because LearnLoop isn't merely trying to recognize what kind of mistake a student made. It's trying to decide which intervention is most valuable, given what it already knows and what it costs to intervene.

## 1. Proposed architecture

Learner evidence

Response, error trace, misconception hypotheses, concept context

Qwen3-Embedding-0.6B

Semantic evidence representation

Action-conditioned feature fusion

Semantic features + numeric learner state + candidate action features + cost/uncertainty

Small learned Q/K scorer + value head

Estimate expected outcome and utility for each action

Deterministic feasibility and decision layer

Evidence authority, robust EVSI, admissibility, OOD and abstention

Probe

Repair

Practice

Retrieval

Audit

No-op

This preserves LearnLoop's existing distinction between semantic evidence, probabilistic learner state, and routing authority. Initially, the learned model would run in shadow mode and wouldn't be allowed to override the deterministic router.

Qwen's official embedding models support task-conditioned representations and reduced-dimensional embeddings. The 0.6B model produces up to 1,024-dimensional vectors and can be fine-tuned using LoRA.

![](https://www.google.com/s2/favicons?domain=https://huggingface.co&sz=32)

Hugging Face

+1

## 2. Why I prefer action-conditioned scoring over classification

A standard classifier would predict:

\[ P(a\mid x) \]

where \(x\) is the text describing the learner's latest answer, and \(a\) is a tutoring action.

The problem is that the same error can demand different actions depending on learner history.

For example, imagine a learner incorrectly asserts that independence implies mutual exclusivity.

|Learner state|Appropriate action|
|---|---|
|First occurrence, uncertain misconception|Diagnostic probe|
|Misconception confirmed repeatedly|Minimal repair|
|Corrected previously, but execution remains weak|Guided practice|
|Previously mastered, now due for retention testing|Retrieval check|
|Well-established mastery; no useful new information expected|No intervention|

The semantic content might be nearly identical in every case. The optimal action changes because the underlying learner state changes.

Instead, I would learn an action-conditioned value:

\[ Q_\theta(s_t,a) = \mathbb E[\text{benefit}-\text{cost}\mid s_t,a] \]

with a small learned scorer that takes both Qwen representations and LearnLoop's explicit probabilistic state.

## 3. The specific model I'd implement

Your earlier Q/K retrieval idea fits this particularly well.

For each evidence event, compute a Qwen embedding \(e_i\). For each candidate action \(a\), construct a query that depends on the action and learner state:

\[ q_a=W_q[\phi(s_t);u_a] \]

Here, \(\phi(s_t)\) contains the structured learner-state features, and \(u_a\) is a learned representation of the candidate action.

Then retrieve the most relevant learner evidence:

\[ \alpha_{a,i} = \operatorname{softmax}_i \left( \frac{q_a^\top W_k e_i}{\sqrt d} \right) \]

\[ z_a=\sum_i\alpha_{a,i}W_v e_i \]

Finally, use a small MLP:

\[ \hat{\mathbf y}_a= f_\theta(z_a,\phi(s_t),u_a) \]

Rather than predict one class, let \(\hat{\mathbf y}_a\) estimate several quantities, such as expected mastery gain, diagnostic information, learner effort, and false-remediation risk.

These can feed the existing robust action comparator. The learned estimates should carry uncertainty, not just point values.

The interesting part is that different tutoring actions learn to attend to different portions of the same evidence history.

A diagnostic probe might attend to conflicting answers, while a retrieval check might attend to old successful demonstrations and elapsed time.

## 4. How I would train it

I would not immediately LoRA-fine-tune Qwen. For LearnLoop, the training signal and evaluation setup matter more than the backbone's size.

## 1

Frozen embeddings + learned Q/K scorer

Embed responses, diagnoses, and evidence descriptions with Qwen3-Embedding-0.6B. Train only the projection layers, attention module, and small prediction head. Keep explicit numeric signals separate.

This should be the first experiment.

## 2

Pairwise preference learning from your EVSI teacher

If the exact robust comparator establishes that action \(a^+\) is better than \(a^-\) for a particular state, train the scorer to recover that ordering:

\[ \mathcal L_{\text{rank}} = -\log\sigma(Q_\theta(s,a^+)-Q_\theta(s,a^-)) \]

Omit unresolved ties, stop decisions, and unsupported rankings. The learned model initially assists with near-tie discrimination rather than replacing the teacher.

## 3

Fine-tune Qwen with LoRA if needed

Once you have enough diverse labeled examples, adapt the embedding space to distinguish educational mechanisms and learner-state evidence.

You could combine ranking or classification supervision with a supervised contrastive objective, but only for genuinely meaningful distinctions. Two examples of the same misconception do not necessarily imply the same optimal tutoring action.

Qwen's official training stack supports LoRA and InfoNCE-based embedding fine-tuning.

![](https://www.google.com/s2/favicons?domain=https://github.com&sz=32)

GitHub

I would use the 5090 to train and evaluate the model, then cache embeddings for evidence that doesn't change. The compact scorer should handle the actual routing computation.

## 5. The experiment I would run first

Compare these architectures on exactly the same held-out learner-state snapshots.

|Model|Purpose|
|---|---|
|Numeric-only router|Establish how much structured state already explains|
|Qwen + softmax classifier|Simple BERT-style baseline|
|Qwen + numeric features + MLP|Test whether semantic information adds value|
|Qwen + action-conditioned Q/K|Test the value of action-specific evidence retrieval|
|Q/K + LoRA-adapted Qwen|Test whether fine-tuning the embeddings is worthwhile|

Evaluate pairwise action-order accuracy, decision regret against the robust EVSI teacher, calibration, false-remediation frequency, abstention behavior, and latency. Split by learner or source context to avoid leaking nearly identical evidence between training and testing.

One particularly important ablation: Qwen versus no Qwen. It is quite possible that your structured features already capture most of the action-selection signal. If so, Qwen's most valuable contribution may be interpreting error traces and retrieving relevant evidence, rather than predicting the action directly.

## 6. An alternative worth testing: Qwen3-Reranker

Qwen also offers a [Qwen3-Reranker-0.6B](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B) model, designed to assess query-document relevance rather than generate standalone embeddings.

![](https://www.google.com/s2/favicons?domain=https://qwenlm.github.io&sz=32)

Qwen

You could represent a learner-state summary as the query and candidate interventions as documents, then train a reranker on pairwise preferred actions.

However, that would be a useful baseline, not my preferred production architecture. A reranker must be explicitly trained to evaluate intervention value; relevance alone doesn't capture causal effects, time costs, or uncertainty. It also makes preserving typed numeric signals less natural.

My recommendation for LearnLoop: Start with frozen Qwen3-Embedding-0.6B, an action-conditioned Q/K scorer, and your existing `RouterStateV1` signals. Use `evsi.py` for teacher rankings, `action_loss.py` for costs, and keep the deterministic controller authoritative while the learned model runs in shadow mode.

The goal isn't to produce a better semantic classifier. It's to find out whether semantic evidence representations improve the quality of action-value estimates beyond what your existing probabilistic state and deterministic router already provide.

That's the experiment I'd prioritize before spending time fine-tuning the whole embedding model.