/**
 * AI Hallucination Checker - Popup Script
 */

const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

document.addEventListener("DOMContentLoaded", async () => {
  // UI Elements
  const backendIndicator = document.getElementById("backendStatusIndicator");
  const errorBanner = document.getElementById("errorBanner");
  const errorMessage = document.getElementById("errorMessage");
  const loadingView = document.getElementById("loadingView");
  const loadingTitle = document.getElementById("loadingStepTitle");
  const loadingDetail = document.getElementById("loadingStepDetail");
  const progressBarFill = document.getElementById("progressBarFill");
  const resultsCard = document.getElementById("resultsCard");
  const overallScoreText = document.getElementById("overallScoreText");
  const overallStatusBadge = document.getElementById("overallStatusBadge");
  const verifiedCount = document.getElementById("verifiedCount");
  const partialCount = document.getElementById("partialCount");
  const hallucinatedCount = document.getElementById("hallucinatedCount");
  const insufficientCount = document.getElementById("insufficientCount");
  const claimsSection = document.getElementById("claimsSection");
  const claimsList = document.getElementById("claimsList");
  const claimsTotalCount = document.getElementById("claimsTotalCount");
  const verifyResponseBtn = document.getElementById("verifyResponseBtn");
  const toggleManualBtn = document.getElementById("toggleManualBtn");
  const manualSection = document.getElementById("manualSection");
  const manualTextArea = document.getElementById("manualTextArea");
  const verifyManualBtn = document.getElementById("verifyManualBtn");
  const openDashboardLink = document.getElementById("openDashboardLink");
  const openOptionsLink = document.getElementById("openOptionsLink");

  let backendUrl = DEFAULT_BACKEND_URL;

  // Retrieve configured backend URL
  const storedConfig = await chrome.storage.local.get(["backendUrl", "lastResult", "pendingVerification"]);
  if (storedConfig.backendUrl) {
    backendUrl = storedConfig.backendUrl;
  }

  // Check health of backend
  checkBackendHealth();

  // If there is pending verification from context menu
  if (storedConfig.pendingVerification) {
    manualTextArea.value = storedConfig.pendingVerification.text;
    manualSection.classList.remove("hidden");
    chrome.storage.local.remove(["pendingVerification"]);
  }

  // If there is a cached result, render it
  if (storedConfig.lastResult) {
    renderVerificationResults(storedConfig.lastResult);
  }

  // Health check function
  async function checkBackendHealth() {
    try {
      const resp = await fetch(`${backendUrl}/api/health`, { method: "GET" });
      if (resp.ok) {
        backendIndicator.className = "backend-status online";
        backendIndicator.title = "Backend Status: Online";
      } else {
        throw new Error("Bad status");
      }
    } catch (e) {
      backendIndicator.className = "backend-status offline";
      backendIndicator.title = "Backend Status: Offline (Run local backend)";
    }
  }

  // Set step progress animation
  function setProgress(step, percent, title, detail) {
    progressBarFill.style.width = `${percent}%`;
    loadingTitle.innerText = title;
    loadingDetail.innerText = detail;
  }

  // Call verification API
  async function runVerification(text, platform = "generic") {
    if (!text || text.trim().length < 5) {
      showError("Please select or paste text with at least 5 characters to verify.");
      return;
    }

    hideError();
    resultsCard.classList.add("hidden");
    claimsSection.classList.add("hidden");
    loadingView.classList.remove("hidden");

    try {
      setProgress(1, 20, "Extracting Claims...", "Decomposing AI response into atomic factual statements");
      await new Promise(r => setTimeout(r, 200));

      setProgress(2, 50, "Searching Evidence...", "Retrieving multi-source web evidence and knowledge bases");
      await new Promise(r => setTimeout(r, 200));

      setProgress(3, 75, "Analyzing Consistency...", "Running Natural Language Inference & deterministic rule engine");

      const response = await fetch(`${backendUrl}/api/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text, platform: platform })
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server error (${response.status})`);
      }

      setProgress(4, 100, "Finalizing...", "Calculating calibrated hybrid confidence scores");
      await new Promise(r => setTimeout(r, 150));

      const data = await response.json();
      chrome.storage.local.set({ lastResult: data });
      renderVerificationResults(data);

      // Send to active tab content script to highlight
      const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (activeTab && activeTab.id) {
        chrome.tabs.sendMessage(activeTab.id, {
          action: "HIGHLIGHT_VERIFICATION_RESULTS",
          claims: data.claims
        }).catch(() => {
          // Tab might not be an AI page, ignore silently
        });
      }
    } catch (err) {
      showError(`Verification failed: ${err.message}. Ensure backend is running on ${backendUrl}`);
    } finally {
      loadingView.classList.add("hidden");
    }
  }

  function renderVerificationResults(data) {
    if (!data) return;

    overallScoreText.innerText = Math.round(data.overall_score * 100) + "%";
    overallStatusBadge.innerText = data.overall_status.replace("_", " ");
    overallStatusBadge.className = `status-pill status-${data.overall_status}`;

    verifiedCount.innerText = data.verified || 0;
    partialCount.innerText = data.partially_supported || 0;
    hallucinatedCount.innerText = data.hallucinated || 0;
    insufficientCount.innerText = data.insufficient_evidence || 0;

    resultsCard.classList.remove("hidden");

    // Render claims
    claimsList.innerHTML = "";
    claimsTotalCount.innerText = data.claims ? data.claims.length : 0;

    if (data.claims && data.claims.length > 0) {
      claimsSection.classList.remove("hidden");
      data.claims.forEach(c => {
        const card = document.createElement("div");
        card.className = `claim-card status-${c.status}`;
        card.innerHTML = `
          <div class="claim-card-header">
            <span class="claim-type-tag">${c.type}</span>
            <span style="font-weight: 700; font-size: 11px;">${Math.round(c.confidence * 100)}%</span>
          </div>
          <div class="claim-card-text">${c.claim}</div>
          <div class="claim-card-meta">
            <span>NLI: ${c.nli}</span>
            <span>Sources: ${c.evidence ? c.evidence.length : 0}</span>
          </div>
        `;
        claimsList.appendChild(card);
      });
    }
  }

  function showError(msg) {
    errorMessage.innerText = msg;
    errorBanner.classList.remove("hidden");
  }

  function hideError() {
    errorBanner.classList.add("hidden");
  }

  // Event Listeners
  verifyResponseBtn.addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.id) {
      showError("No active browser tab found.");
      return;
    }

    try {
      chrome.tabs.sendMessage(tab.id, { action: "GET_LATEST_RESPONSE" }, (response) => {
        if (chrome.runtime.lastError || !response || !response.success || !response.text) {
          showError("Could not automatically locate an AI response on this page. Use Manual / Paste Input.");
          manualSection.classList.remove("hidden");
        } else {
          runVerification(response.text, response.platform);
        }
      });
    } catch (e) {
      showError("Error accessing page: " + e.message);
    }
  });

  toggleManualBtn.addEventListener("click", () => {
    manualSection.classList.toggle("hidden");
  });

  verifyManualBtn.addEventListener("click", () => {
    const text = manualTextArea.value;
    runVerification(text, "manual_input");
  });

  openDashboardLink.addEventListener("click", (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: `${backendUrl}/docs` });
  });

  openOptionsLink.addEventListener("click", (e) => {
    e.preventDefault();
    if (chrome.runtime.openOptionsPage) {
      chrome.runtime.openOptionsPage();
    }
  });
});
