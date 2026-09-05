/**
 * AI Hallucination Checker - Content Script
 * Interacts with in-page DOM, extracts AI responses, and renders interactive highlights.
 */

(function () {
  let popoverEl = null;

  function initPopover() {
    if (document.getElementById("ai-fact-checker-popover")) {
      popoverEl = document.getElementById("ai-fact-checker-popover");
      return;
    }
    popoverEl = document.createElement("div");
    popoverEl.id = "ai-fact-checker-popover";
    popoverEl.innerHTML = `
      <div class="popover-header">
        <span class="popover-title">Fact Check Details</span>
        <button class="popover-close" id="ai-popover-close-btn">&times;</button>
      </div>
      <div class="claim-text" id="ai-popover-claim-text"></div>
      <div class="metrics-grid">
        <div class="metric-box">
          <div class="label">Status</div>
          <div class="value" id="ai-popover-status"></div>
        </div>
        <div class="metric-box">
          <div class="label">Confidence</div>
          <div class="value" id="ai-popover-confidence"></div>
        </div>
        <div class="metric-box">
          <div class="label">NLI Classification</div>
          <div class="value" id="ai-popover-nli"></div>
        </div>
        <div class="metric-box">
          <div class="label">Source Reliability</div>
          <div class="value" id="ai-popover-source"></div>
        </div>
      </div>
      <div class="explanation" id="ai-popover-explanation"></div>
      <div style="font-weight: 700; font-size: 11px; text-transform: uppercase; color: #94a3b8; margin-bottom: 6px;">Supporting Evidence</div>
      <div class="evidence-section" id="ai-popover-evidence"></div>
    `;
    document.body.appendChild(popoverEl);

    document.getElementById("ai-popover-close-btn").addEventListener("click", () => {
      popoverEl.style.display = "none";
    });

    document.addEventListener("click", (e) => {
      if (popoverEl && !popoverEl.contains(e.target) && !e.target.closest(".ai-fact-highlight")) {
        popoverEl.style.display = "none";
      }
    });
  }

  function getActiveAdapter() {
    if (window.ChatGPTAdapter && window.ChatGPTAdapter.isMatch()) return window.ChatGPTAdapter;
    if (window.GeminiAdapter && window.GeminiAdapter.isMatch()) return window.GeminiAdapter;
    if (window.ClaudeAdapter && window.ClaudeAdapter.isMatch()) return window.ClaudeAdapter;
    return null;
  }

  function getStatusBadgeHtml(status) {
    switch (status) {
      case "VERIFIED":
        return '<span class="ai-fact-badge status-VERIFIED">🟢 Verified</span>';
      case "PARTIALLY_SUPPORTED":
        return '<span class="ai-fact-badge status-PARTIALLY_SUPPORTED">🟡 Partial</span>';
      case "LIKELY_HALLUCINATED":
        return '<span class="ai-fact-badge status-LIKELY_HALLUCINATED">🔴 Hallucinated</span>';
      default:
        return '<span class="ai-fact-badge status-INSUFFICIENT_EVIDENCE">⚪ Insufficient</span>';
    }
  }

  function showPopoverForClaim(claimData, rect) {
    initPopover();

    document.getElementById("ai-popover-claim-text").innerText = claimData.claim;
    document.getElementById("ai-popover-status").innerHTML = getStatusBadgeHtml(claimData.status);
    document.getElementById("ai-popover-confidence").innerText = Math.round(claimData.confidence * 100) + "%";
    document.getElementById("ai-popover-nli").innerText = claimData.nli || "NEUTRAL";
    document.getElementById("ai-popover-source").innerText = Math.round((claimData.source_reliability || 0) * 100) + "%";
    document.getElementById("ai-popover-explanation").innerText = claimData.explanation || "No explanation available.";

    const evContainer = document.getElementById("ai-popover-evidence");
    evContainer.innerHTML = "";

    if (!claimData.evidence || claimData.evidence.length === 0) {
      evContainer.innerHTML = '<div style="color: #94a3b8; font-size: 11px;">No external sources retrieved.</div>';
    } else {
      claimData.evidence.forEach(item => {
        const itemDiv = document.createElement("div");
        itemDiv.className = "evidence-item";
        itemDiv.innerHTML = `
          <a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.title || item.domain || "Source"}</a>
          <p>${item.snippet}</p>
        `;
        evContainer.appendChild(itemDiv);
      });
    }

    // Position popover relative to clicked element
    const scrollY = window.scrollY || document.documentElement.scrollTop;
    const scrollX = window.scrollX || document.documentElement.scrollLeft;

    let top = rect.bottom + scrollY + 8;
    let left = rect.left + scrollX;

    if (left + 390 > window.innerWidth) {
      left = window.innerWidth - 410;
    }
    if (left < 10) left = 10;

    popoverEl.style.top = `${top}px`;
    popoverEl.style.left = `${left}px`;
    popoverEl.style.display = "block";
  }

  function highlightClaimsInElement(element, claims) {
    if (!element || !claims || claims.length === 0) return;

    let html = element.innerHTML;

    claims.forEach(c => {
      const cleanSnippet = c.claim.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\.$/, '');
      if (cleanSnippet.length < 5) return;

      const regex = new RegExp(`(${cleanSnippet}\\.?)`, 'gi');
      if (regex.test(html)) {
        const badge = getStatusBadgeHtml(c.status);
        html = html.replace(regex, (match) => {
          return `<span class="ai-fact-highlight status-${c.status}" data-claim-id="${c.claim_id}">${match}${badge}</span>`;
        });
      }
    });

    element.innerHTML = html;

    // Attach click handlers to newly inserted highlights
    element.querySelectorAll(".ai-fact-highlight").forEach(el => {
      const cid = el.getAttribute("data-claim-id");
      const cData = claims.find(item => item.claim_id === cid);
      if (cData) {
        el.addEventListener("click", (e) => {
          e.stopPropagation();
          showPopoverForClaim(cData, el.getBoundingClientRect());
        });
      }
    });
  }

  // Listen for messages from popup or background service worker
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "GET_LATEST_RESPONSE") {
      const adapter = getActiveAdapter();
      if (adapter) {
        const text = adapter.getLatestResponseText();
        sendResponse({ success: true, text: text, platform: adapter.name });
      } else {
        // Fallback: check window selection or common page text
        const sel = window.getSelection().toString().trim();
        sendResponse({
          success: !!sel,
          text: sel || "",
          platform: "generic"
        });
      }
      return true;
    }

    if (request.action === "HIGHLIGHT_VERIFICATION_RESULTS") {
      const adapter = getActiveAdapter();
      const targetElement = adapter ? adapter.getLatestResponseElement() : document.body;
      if (targetElement && request.claims) {
        highlightClaimsInElement(targetElement, request.claims);
        sendResponse({ success: true });
      } else {
        sendResponse({ success: false, error: "Target response element not found" });
      }
      return true;
    }
  });

  initPopover();
})();
