# Evaluation - Research Benchmark & Metrics

Research evaluation framework designed to benchmark the accuracy, precision, recall, F1-score, latency, and reliability of the Hybrid Verification Architecture against baseline systems.

## Baselines

1. **Baseline 1 (LLM-Only)**: Zero-shot/few-shot prompt to an LLM asking whether a claim is true or hallucinated without external retrieval.
2. **Baseline 2 (Search/Evidence-Only)**: Keyword/semantic search matching without Natural Language Inference (NLI) or rule consistency.
3. **Proposed System (Hybrid Multi-Signal)**: Hybrid pipeline combining atomic claim extraction, multi-source retrieval, domain reliability weighting, NLI, and deterministic rule verification.

## Directory Layout

```text
evaluation/
├── dataset/                 # Curated benchmark datasets (synthetic & real AI responses)
│   ├── ground_truth.json    # Annotated ground-truth claims with labels
│   └── test_responses.json  # Raw responses from ChatGPT, Gemini, and Claude
├── results/                 # Output benchmark reports, confusion matrices, and latency logs
├── evaluate.py              # Main benchmark execution script
├── metrics.py               # Calculation of Accuracy, Precision, Recall, F1, FPR, FNR
└── README.md
```
