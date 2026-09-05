# Research Evaluation & Benchmark Protocol

## Objective
Quantitatively validate the hypothesis that a **hybrid multi-signal verification architecture** outperforms single-agent LLM verification and simple retrieval-based verifiers in detecting factual hallucinations.

---

## Evaluation Metrics

1. **Accuracy**: Overall fraction of correctly identified claims (true positives + true negatives / total).
2. **Precision**: Ratio of accurately flagged hallucinations to total flagged claims.
3. **Recall**: Proportion of actual hallucinations successfully identified by the system.
4. **F1-Score**: Harmonic mean of Precision and Recall.
5. **False Positive Rate (FPR)**: Verified facts erroneously categorized as hallucinations.
6. **False Negative Rate (FNR)**: Hallucinations mistakenly passed as verified.
7. **Average Verification Latency**: End-to-end execution time per claim and per full response.

---

## Baseline Comparison Matrix

| Metric | Baseline 1 (LLM-Only) | Baseline 2 (Search-Only) | Proposed Hybrid System |
|---|---|---|---|
| Precision | To be evaluated | To be evaluated | Target: $\ge 88\%$ |
| Recall | To be evaluated | To be evaluated | Target: $\ge 85\%$ |
| F1-Score | To be evaluated | To be evaluated | Target: $\ge 86\%$ |
| Grounding / Citations | None (Circular) | Snippets only | Verifiable URLs + NLI justification |
| Latency | Fast | Medium | Sub-second cached, $\approx 2-4$s fresh |
