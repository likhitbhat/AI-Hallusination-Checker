# Hybrid AI-Based System for Detecting and Verifying Hallucinated Information in Generative AI Responses

A production-quality web browser extension and backend verification system that detects potentially hallucinated factual information in generative AI outputs (ChatGPT, Google Gemini, Claude) using a multi-signal **hybrid verification architecture**.

---

## Architecture Overview

Instead of naively prompting another LLM to judge truthfulness, this system decomposes AI responses into verifiable atomic claims and evaluates each claim through an objective pipeline:

```text
                 USER
                   |
                   v
        +----------------------+
        | Generative AI Website|
        | ChatGPT/Gemini/Claude|
        +----------+-----------+
                   |
                   v
        +----------------------+
        | Browser Extension    |
        | Chrome Manifest V3   |
        +----------+-----------+
                   |
                   | HTTPS REST API
                   v
        +----------------------+
        | FastAPI Backend      |
        | Python 3.11+         |
        +----------+-----------+
                   |
                   v
        +----------------------+
        | Claim Extraction     |
        | (Atomic separation)  |
        +----------+-----------+
                   |
                   v
        +----------------------+
        | Claim Classification  |
        +----------+-----------+
                   |
          +--------+--------+
          |                 |
          v                 v
+-------------------+ +-------------------+
| Evidence Retrieval| | Rule-Based Engine |
| Search Providers  | | Numbers/Dates/etc |
+---------+---------+ +---------+---------+
          |                    |
          +---------+----------+
                    |
                    v
          +--------------------+
          | Semantic Similarity|
          | Embeddings         |
          +---------+----------+
                    |
                    v
          +--------------------+
          | NLI Verification   |
          | Entail/Neutral/Cont|
          +---------+----------+
                    |
                    v
          +--------------------+
          | Source Reliability |
          | Domain Scoring     |
          +---------+----------+
                    |
                    v
          +--------------------+
          | Hybrid Score Engine|
          +---------+----------+
                    |
                    v
          +--------------------+
          | Result Generator   |
          | Explainable output |
          +---------+----------+
                    |
                    v
          +--------------------+
          | Browser Extension  |
          | Highlight & Evidence|
          +--------------------+
```

---

## Directory Structure

```text
├── backend/               # FastAPI backend service, services, models, tests
│   ├── app/
│   │   ├── api/           # API routes, dependencies, schemas
│   │   ├── services/      # Extraction, classification, retrieval, NLI, rules, scoring
│   │   ├── models/        # Database models & ORM entities
│   │   ├── database/      # Session management & migrations
│   │   └── utils/         # Helpers, security, logging
│   ├── tests/             # Pytest test suites
│   ├── requirements.txt
│   └── README.md
│
├── extension/             # Chrome Manifest V3 browser extension
│   ├── background/        # Service worker for background events & API comms
│   ├── content/           # Content script & CSS for in-page claim highlighting
│   ├── popup/             # Extension UI for quick verification & manual input
│   ├── options/           # Settings & backend configuration
│   ├── assets/            # Extension icons and graphics
│   ├── manifest.json
│   └── README.md
│
├── dashboard/             # Web dashboard for analytics, history, and audits
│   ├── public/
│   ├── src/
│   └── README.md
│
├── evaluation/            # Research evaluation framework & benchmark datasets
│   ├── dataset/           # Annotated test datasets with ground-truth facts
│   ├── results/           # Benchmark metrics & comparison results
│   ├── evaluate.py        # Evaluation pipeline
│   ├── metrics.py         # Precision, Recall, F1, Latency calculations
│   └── README.md
│
├── docs/                  # Comprehensive project documentation
│   ├── architecture.md    # System design & component interactions
│   ├── api.md             # REST API specifications
│   ├── installation.md    # Local setup and deployment guide
│   ├── methodology.md     # Hybrid scoring & mathematical formulation
│   ├── testing.md         # Test strategy and test execution instructions
│   ├── evaluation.md      # Research findings & baseline comparisons
│   └── README.md
│
├── .env.example           # Configuration template
├── .gitignore             # Git ignore patterns
└── README.md              # Project root documentation
```

---

## Hybrid Verification Formula

The composite score for each claim is calculated via a configurable multi-signal formula:

$$\text{Final Score} = w_e \cdot S_{\text{evidence}} + w_n \cdot S_{\text{nli}} + w_s \cdot S_{\text{source}} + w_r \cdot S_{\text{rule}}$$

Where the default initial parameters are:
- $w_e = 0.35$ (Evidence Support)
- $w_n = 0.30$ (Natural Language Inference Score)
- $w_s = 0.20$ (Source Reliability Score)
- $w_r = 0.15$ (Deterministic Rule Consistency)

### Status Categorization

- **VERIFIED** ($Score \ge 0.80$): High confidence supporting evidence with high source reliability.
- **PARTIALLY_SUPPORTED** ($0.60 \le Score < 0.80$): Moderate support or mixed signals.
- **LIKELY_HALLUCINATED** ($Score < 0.60$ with contradictory evidence): Evidence explicitly contradicts claim.
- **INSUFFICIENT_EVIDENCE**: No credible external sources found (never falsely marked as hallucinated).

---

## 17-Phase Development Roadmap

- [x] **Phase 1 — Project Setup**: Repository setup, directory scaffold, `.env.example`, `.gitignore`, foundational documentation.
- [ ] **Phase 2 — Backend Skeleton**: FastAPI app, health endpoints, config loader, structured logging, error handling.
- [ ] **Phase 3 — Browser Extension**: Manifest V3, popup UI, content scripts, background worker, manual input.
- [ ] **Phase 4 — Extension ↔ Backend**: End-to-end communication with mock verification data.
- [ ] **Phase 5 — Claim Extraction**: Atomic factual claim extraction engine.
- [ ] **Phase 6 — Claim Classification**: Claim categorization (numerical, historical, geographical, etc.).
- [ ] **Phase 7 — Evidence Retrieval**: Multi-provider search abstraction, deduplication, snippet extraction.
- [ ] **Phase 8 — Evidence Ranking**: Relevance, semantic similarity, and source reliability ranking.
- [ ] **Phase 9 — NLI Verification**: Natural Language Inference (Entailment, Contradiction, Neutral).
- [ ] **Phase 10 — Rule-Based Engine**: Deterministic arithmetic, percentages, dates, and unit checks.
- [ ] **Phase 11 — Hybrid Scoring**: Multi-signal scoring engine with configurable weights and thresholds.
- [ ] **Phase 12 — Results UI**: Extension in-page claim highlighting, badges, and detailed evidence popovers.
- [ ] **Phase 13 — Dashboard**: Verification history, analytics, accuracy metrics, and claim inspection.
- [ ] **Phase 14 — Database**: PostgreSQL persistence for requests, claims, evidence, and audit logs.
- [ ] **Phase 15 — Research Evaluation**: Benchmark datasets, baseline comparisons, precision/recall/F1 metrics.
- [ ] **Phase 16 — Performance & Optimization**: Caching, concurrency, prompt hardening, latency tuning.
- [ ] **Phase 17 — Documentation**: Complete system architecture, API guide, and academic research report.

---

## Quick Start (Phase 1)

1. Clone the repository and configure your environment:
   ```bash
   cp .env.example .env
   ```
2. Inspect the documentation in [`docs/`](docs/) and specific component READMEs.
