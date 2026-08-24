The backbone LLM is stateless between calls. 

1. Recognziing recurring misconceptions across different phrasing and surfaces
	- when a new candidate cause is minted, query its embedding against prior hypotheses for this learner, restricted by facet
	- This helps sharpen the posterior even without serving any probes
	- We can target repairs of the underlying family as opposed to targeting the surface instance
2. Give stateless backbone a longitudinal memory at prompt time
	- Retrieval selects the k most relevant prior trace records (observed error, hypothesis, repair tried, cold outcome) and injects them as text into the diagnostician backbone LLM's prompt. The backbone re reasons over the learner's compressed history on every call while avoiding fine tuning and raw transcripts
3. 