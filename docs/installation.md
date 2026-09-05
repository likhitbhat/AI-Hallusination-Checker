# Installation and Setup Guide

## Prerequisites
- **Python**: Version 3.11 or newer (Python 3.13 supported)
- **Node.js**: Version 18+ (for dashboard or extension packaging)
- **Browser**: Chromium-based browser (Google Chrome, Microsoft Edge, Brave)

---

## 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp ../.env.example .env

# Run FastAPI server with auto-reload
uvicorn app.main:app --reload --port 8000
```

---

## 2. Browser Extension Setup

1. Open your browser and navigate to `chrome://extensions/` (or `edge://extensions/`).
2. Toggle on **Developer Mode** (usually top-right).
3. Click **Load unpacked**.
4. Select the `extension/` directory from this repository.
5. The **AI Hallucination Checker** icon should now appear in your browser extension toolbar.

---

## 3. Web Dashboard Setup

```bash
cd dashboard
# Follow instructions in dashboard/README.md once dashboard phase begins
```
