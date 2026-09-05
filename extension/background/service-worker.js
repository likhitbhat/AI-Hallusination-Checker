/**
 * AI Hallucination Checker - Service Worker (Manifest V3)
 */

const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

// Set up Context Menu on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "verify_selected_text",
    title: "🔍 Verify Selected Text for Hallucinations",
    contexts: ["selection"]
  });

  chrome.storage.local.get(["backendUrl"], (res) => {
    if (!res.backendUrl) {
      chrome.storage.local.set({ backendUrl: DEFAULT_BACKEND_URL });
    }
  });
});

// Handle Context Menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "verify_selected_text" && info.selectionText) {
    const textToVerify = info.selectionText.trim();
    
    // Save selected text in storage for popup to consume
    chrome.storage.local.set({
      pendingVerification: {
        text: textToVerify,
        platform: "selected_text",
        timestamp: Date.now()
      }
    });

    // Notify user to open popup or trigger verification
    chrome.action.setBadgeText({ text: "...", tabId: tab.id });
    chrome.action.setBadgeBackgroundColor({ color: "#38bdf8", tabId: tab.id });

    // Attempt direct verification
    chrome.storage.local.get(["backendUrl"], async (config) => {
      const apiUrl = (config.backendUrl || DEFAULT_BACKEND_URL) + "/api/verify";
      try {
        const response = await fetch(apiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: textToVerify,
            platform: "selected_text"
          })
        });

        if (response.ok) {
          const data = await response.json();
          // Store result
          chrome.storage.local.set({ lastResult: data });

          // Update badge
          const status = data.overall_status;
          if (status === "VERIFIED") {
            chrome.action.setBadgeText({ text: "OK", tabId: tab.id });
            chrome.action.setBadgeBackgroundColor({ color: "#10b981", tabId: tab.id });
          } else if (status === "PARTIALLY_SUPPORTED") {
            chrome.action.setBadgeText({ text: "PART", tabId: tab.id });
            chrome.action.setBadgeBackgroundColor({ color: "#f59e0b", tabId: tab.id });
          } else {
            chrome.action.setBadgeText({ text: "WARN", tabId: tab.id });
            chrome.action.setBadgeBackgroundColor({ color: "#ef4444", tabId: tab.id });
          }

          // Send message to active tab to highlight
          chrome.tabs.sendMessage(tab.id, {
            action: "HIGHLIGHT_VERIFICATION_RESULTS",
            claims: data.claims
          });
        }
      } catch (err) {
        console.error("Context menu verification error:", err);
        chrome.action.setBadgeText({ text: "ERR", tabId: tab.id });
        chrome.action.setBadgeBackgroundColor({ color: "#64748b", tabId: tab.id });
      }
    });
  }
});
