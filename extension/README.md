# Browser Extension - AI Hallucination Checker

Chromium-compatible Chrome Extension (Manifest V3) for inspecting and verifying AI responses generated on ChatGPT, Google Gemini, and Claude, as well as highlighted text and manual input.

## Features

- **In-Page AI Response Detection**: Adapters for ChatGPT, Gemini, and Claude.
- **Claim Highlighting**: Direct visual highlighting on AI response bubbles (Verified, Partial, Hallucinated, Insufficient Evidence).
- **Interactive Claim Detail Popover**: Inspection of confidence, NLI result, source reliability, and supporting evidence links.
- **Manual Response Verification**: Dedicated popup interface for verifying copied AI outputs.
- **Context Menu Integration**: Right-click to verify selected text.

## Directory Layout

```text
extension/
├── manifest.json            # Manifest V3 definition
├── background/
│   └── service-worker.js    # Background network requests & state
├── content/
│   ├── content.js           # DOM extraction & in-page claim highlighting
│   ├── content.css          # In-page highlight styles & modal overlay
│   └── adapters/            # Platform-specific DOM adapters (ChatGPT, Gemini, Claude)
├── popup/
│   ├── popup.html           # Main popup UI
│   ├── popup.css
│   └── popup.js
├── options/
│   ├── options.html         # User settings (backend URL, toggles)
│   ├── options.css
│   └── options.js
├── assets/                  # Icons (16px, 48px, 128px)
└── README.md
```

## Installation in Chrome / Edge / Brave

1. Open `chrome://extensions/` (or `edge://extensions/`).
2. Enable **Developer mode** in the top-right corner.
3. Click **Load unpacked**.
4. Select the `extension/` folder.
