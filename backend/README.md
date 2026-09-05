# Backend - Hybrid Hallucination Verification Service

FastAPI-powered asynchronous backend implementing the multi-stage hybrid claim verification pipeline.

## Structure

```text
backend/
├── app/
│   ├── main.py              # Application entrypoint & lifespan events
│   ├── config.py            # Pydantic Settings configuration loader
│   ├── api/
│   │   ├── routes/          # API endpoints (/health, /verify, /claims, etc.)
│   │   ├── dependencies.py  # Dependency injection (db sessions, services)
│   │   └── schemas.py       # Pydantic request & response models
│   ├── services/            # Pipeline services
│   │   ├── claim_extractor.py
│   │   ├── claim_classifier.py
│   │   ├── evidence_retriever.py
│   │   ├── evidence_ranker.py
│   │   ├── semantic_verifier.py
│   │   ├── nli_verifier.py
│   │   ├── rule_engine.py
│   │   ├── source_reliability.py
│   │   ├── scoring_engine.py
│   │   └── result_generator.py
│   ├── models/              # SQLAlchemy database models
│   ├── database/            # Database engine and session factory
│   └── utils/               # Logging, security, sanitization helpers
├── tests/                   # Pytest test suites
├── requirements.txt         # Dependencies
└── README.md
```

## Setup & Running

```bash
# From backend directory
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
