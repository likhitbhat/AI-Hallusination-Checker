# API Specifications

## Base URL
Default local development endpoint: `http://127.0.0.1:8000`

---

## Endpoints

### 1. Health & Readiness
`GET /api/health`
- **Response**: `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2026-09-05T09:15:00Z"
}
```

---

### 2. Verify AI Response
`POST /api/verify`
- **Request Body**:
```json
{
  "text": "India has 28 states and 8 Union Territories. The capital of Australia is Sydney.",
  "platform": "chatgpt"
}
```
- **Response**: `200 OK`
```json
{
  "request_id": "req_123456",
  "overall_score": 0.49,
  "overall_status": "PARTIALLY_SUPPORTED",
  "claims_analyzed": 2,
  "verified": 1,
  "partially_supported": 0,
  "hallucinated": 1,
  "insufficient_evidence": 0,
  "claims": [
    {
      "claim_id": "claim_1",
      "claim": "India has 28 states and 8 Union Territories.",
      "type": "numerical",
      "status": "VERIFIED",
      "confidence": 0.96,
      "semantic_score": 0.94,
      "nli": "ENTAILMENT",
      "nli_score": 0.95,
      "source_reliability": 0.98,
      "rule_score": 1.0,
      "evidence": [
        {
          "title": "Government of India Official Portal",
          "url": "https://india.gov.in",
          "snippet": "India comprises 28 States and 8 Union Territories."
        }
      ],
      "explanation": "High-reliability official evidence directly supports this claim."
    },
    {
      "claim_id": "claim_2",
      "claim": "The capital of Australia is Sydney.",
      "type": "geographical",
      "status": "LIKELY_HALLUCINATED",
      "confidence": 0.98,
      "semantic_score": 0.92,
      "nli": "CONTRADICTION",
      "nli_score": 0.99,
      "source_reliability": 0.95,
      "rule_score": 0.0,
      "evidence": [
        {
          "title": "Australian Government - Facts and figures",
          "url": "https://australia.gov.au",
          "snippet": "Canberra was selected as the nation's capital in 1908 as a compromise between Sydney and Melbourne."
        }
      ],
      "explanation": "Authoritative sources confirm Canberra, not Sydney, is the capital of Australia."
    }
  ]
}
```

---

### 3. Claim Extraction
`POST /api/claims/extract`
- **Request Body**:
```json
{
  "text": "..."
}
```
- **Response**:
```json
{
  "claims": [
    {
      "id": "c1",
      "text": "Atomic claim statement",
      "type": "factual"
    }
  ]
}
```

---

### 4. Verification History
`GET /api/history?limit=20&offset=0`
- **Response**: Paginated list of past verification runs.
