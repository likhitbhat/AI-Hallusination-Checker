# Research Methodology & Scoring Formulation

## 1. Problem Formulation
Generative Large Language Models frequently generate factually inaccurate statements with high linguistic confidence ("hallucinations"). Simple verification approaches—such as querying another LLM—are susceptible to circular reasoning and lack verifiable citations.

The **Hybrid Verification Architecture** models fact checking as a multi-stage evidence-based inference task.

---

## 2. Multi-Signal Mathematical Scoring Model

For an extracted atomic claim $c$, candidate evidence snippets $\{e_1, e_2, \dots, e_k\}$ retrieved from external knowledge sources are evaluated.

Each claim is assigned a hybrid confidence score $S(c) \in [0.0, 1.0]$:

$$S(c) = w_e \cdot S_{\text{evidence}}(c) + w_n \cdot S_{\text{nli}}(c) + w_s \cdot S_{\text{source}}(c) + w_r \cdot S_{\text{rule}}(c)$$

Subject to:
$$\sum w_i = 1.0, \quad w_i \ge 0$$

### Default Configuration Weights
| Parameter | Description | Default Weight |
|---|---|---|
| $w_e$ | Semantic relevance and evidence density | `0.35` |
| $w_n$ | NLI classification score (Entailment vs Contradiction) | `0.30` |
| $w_s$ | Source credibility rating | `0.20` |
| $w_r$ | Deterministic rule consistency | `0.15` |

---

## 3. Natural Language Inference (NLI) Mapping
Given claim $c$ and top evidence $e$:
- **Entailment**: Evidence supports claim $\implies S_{\text{nli}} = P(\text{Entailment})$
- **Contradiction**: Evidence refutes claim $\implies S_{\text{nli}} = 1.0 - P(\text{Contradiction})$
- **Neutral**: Evidence is tangential $\implies S_{\text{nli}} = 0.50$

---

## 4. Source Reliability Taxonomy
Domains are mapped to credibility tiers:
- Government (`.gov`, `.mil`, official portals): `1.00`
- Academic / Peer-Reviewed (`.edu`, research repositories): `0.95`
- International Bodies (WHO, UN, World Bank): `0.90`
- Curated Encyclopedias (Wikipedia, Britannica): `0.80`
- Established Major News Organizations: `0.80`
- General Web Domains: `0.55`
- Unknown / Unclassified Domains: `0.30`
