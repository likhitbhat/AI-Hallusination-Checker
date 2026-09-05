# Testing Strategy & Test Execution

## Overview
The testing pipeline spans unit tests, service-level integration tests, mock provider harnesses, and browser extension simulation.

---

## 1. Test Suite Categories

### Unit Tests
- **Claim Extraction**: Splitting compound sentences into isolated factual propositions.
- **Claim Classification**: Accurately distinguishing factual/numerical statements from opinions and speculative predictions.
- **Rule Engine**: Validating mathematical arithmetic, percentage ratios, chronological dates, and unit conversions without LLM non-determinism.
- **Source Reliability**: Ensuring domain parsing and reliability score lookup match configured tiers.
- **Scoring Engine**: Validating mathematical bounds, edge cases (zero evidence, conflicting signals), and threshold transitions.

### Integration Tests
- **API Routes**: Testing `/api/health`, `/api/verify`, `/api/claims/extract`, and error handling for malformed requests.
- **Mock External Retrieval**: Providing deterministic offline search and embedding responses to ensure repeatable CI/CD test runs.

---

## 2. Running Tests

```bash
# Run all backend unit and integration tests
pytest backend/tests -v

# Run with test coverage report
pytest backend/tests --cov=backend/app --cov-report=term-missing
```
