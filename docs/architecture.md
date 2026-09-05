# Architecture & System Design

## 1. High-Level Architecture

The system coordinates three principal layers:
- **Client Tier**: Chrome Manifest V3 extension with platform-specific content adapters (ChatGPT, Google Gemini, Claude), popup manager, and DOM highlight injector.
- **Service Tier**: Asynchronous FastAPI service orchestrating claim extraction, search retrieval, NLI, rule checking, and hybrid score computation.
- **Persistence Tier**: Relational database (PostgreSQL / SQLite) storing audit trails, raw verification requests, individual claim scores, and retrieved evidence links.

```text
+-------------------------------------------------------------+
|                      Client Layer                           |
|  [ ChatGPT / Gemini / Claude ] <-> [ Content Script Adapter]|
|                                             |               |
|                                    [ Popup & Options UI ]   |
|                                             |               |
|                                 [ Background Service Worker]|
+---------------------------------------------+---------------+
                                              | HTTPS REST API
                                              v
+-------------------------------------------------------------+
|                      Backend Service                        |
|                                                             |
|  [ FastAPI Routes: /api/verify, /api/claims, /api/health ]  |
|                                                             |
|  +-------------------------------------------------------+  |
|  |                Hybrid Pipeline Engine                 |  |
|  |                                                       |  |
|  |  1. Claim Extractor (Atomic factual statement splits) |  |
|  |  2. Claim Classifier (Numerical, Historical, etc.)   |  |
|  |  3. Evidence Retriever (Tavily/DuckDuckGo/Serper)    |  |
|  |  4. Source Reliability Scorer (Domain-based rating)   |  |
|  |  5. Semantic Verifier (Cosine similarity)             |  |
|  |  6. Natural Language Inference (NLI Entail/Contr/Neut)|  |
|  |  7. Rule-Based Engine (Arithmetic, Dates, Logic)     |  |
|  |  8. Hybrid Scoring Engine (Multi-signal synthesis)   |  |
|  |  9. Explainable Result Generator                     |  |
|  +-------------------------------------------------------+  |
|                                                             |
|  [ Database / ORM Layer: Request, Claim, Evidence Models ]   |
+-------------------------------------------------------------+
```

## 2. Security Boundaries & Protection
- **No Client Secrets**: API keys (LLM, search, embeddings, DB) reside solely within backend environment variables.
- **Prompt Injection Defense**: Retrieved evidence is treated as strictly untrusted payload data and fenced away from prompt instruction directives.
- **Rate Limiting & Input Bounds**: Payloads exceeding size or claim count constraints are throttled to prevent abuse.
