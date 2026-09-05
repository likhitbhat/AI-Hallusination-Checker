/**
 * AI Hallucination Checker - Web Dashboard Logic
 */

const BACKEND_URL = window.location.origin;

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const serverStatusText = document.getElementById("serverStatusText");
  const serverBadge = document.getElementById("serverBadge");
  const refreshDataBtn = document.getElementById("refreshDataBtn");
  const navItems = document.querySelectorAll(".nav-item");
  const tabPanes = document.querySelectorAll(".tab-pane");
  const pageTitle = document.getElementById("pageTitle");

  // Stats Elements
  const statTotalRequests = document.getElementById("statTotalRequests");
  const statTotalClaims = document.getElementById("statTotalClaims");
  const statVerifiedClaims = document.getElementById("statVerifiedClaims");
  const statHallucinations = document.getElementById("statHallucinations");
  const statPartialClaims = document.getElementById("statPartialClaims");
  const statAvgConfidence = document.getElementById("statAvgConfidence");
  const statusDistributionBars = document.getElementById("statusDistributionBars");
  const platformListContainer = document.getElementById("platformListContainer");
  const historyTableBody = document.getElementById("historyTableBody");
  const inspectorSearchInput = document.getElementById("inspectorSearchInput");
  const inspectBtn = document.getElementById("inspectBtn");
  const inspectorDetailsArea = document.getElementById("inspectorDetailsArea");

  // Tab Navigation
  navItems.forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const tabName = item.getAttribute("data-tab");
      navItems.forEach(i => i.classList.remove("active"));
      item.classList.add("active");

      tabPanes.forEach(pane => pane.classList.remove("active"));
      const activePane = document.getElementById(`tab-${tabName}`);
      if (activePane) activePane.classList.add("active");

      // Update Header Title
      if (tabName === "overview") pageTitle.innerText = "Verification Overview";
      if (tabName === "history") pageTitle.innerText = "Verification History";
      if (tabName === "inspector") pageTitle.innerText = "Claim Inspector";
      if (tabName === "evaluation") pageTitle.innerText = "Research Benchmark & Evaluation";
    });
  });

  // Fetch Dashboard Analytics
  async function loadAnalytics() {
    try {
      const res = await fetch(`${BACKEND_URL}/api/analytics`);
      if (res.ok) {
        const data = await res.json();
        statTotalRequests.innerText = data.total_requests;
        statTotalClaims.innerText = data.total_claims;
        statVerifiedClaims.innerText = data.status_breakdown.verified || 0;
        statHallucinations.innerText = data.status_breakdown.hallucinated || 0;
        statPartialClaims.innerText = data.status_breakdown.partially_supported || 0;
        statAvgConfidence.innerText = Math.round(data.average_confidence * 100) + "%";

        renderStatusBars(data.status_breakdown, data.total_claims);
        renderPlatforms(data.platforms);

        serverStatusText.innerText = "Connected (Online)";
        serverBadge.querySelector(".dot").style.backgroundColor = "#10b981";
      } else {
        throw new Error("Server response error");
      }
    } catch (e) {
      serverStatusText.innerText = "Disconnected";
      serverBadge.querySelector(".dot").style.backgroundColor = "#ef4444";
    }
  }

  function renderStatusBars(breakdown, total) {
    statusDistributionBars.innerHTML = "";
    const items = [
      { label: "Verified Claims", count: breakdown.verified || 0, color: "green" },
      { label: "Partially Supported", count: breakdown.partially_supported || 0, color: "yellow" },
      { label: "Likely Hallucinated", count: breakdown.hallucinated || 0, color: "red" },
      { label: "Insufficient Evidence", count: breakdown.insufficient_evidence || 0, color: "slate" }
    ];

    items.forEach(item => {
      const pct = total > 0 ? Math.round((item.count / total) * 100) : 0;
      const row = document.createElement("div");
      row.className = "bar-row";
      row.innerHTML = `
        <span class="bar-label">${item.label}</span>
        <div class="bar-track">
          <div class="bar-fill ${item.color}" style="width: ${pct}%"></div>
        </div>
        <span class="bar-val">${item.count}</span>
      `;
      statusDistributionBars.appendChild(row);
    });
  }

  function renderPlatforms(platforms) {
    platformListContainer.innerHTML = "";
    const entries = Object.entries(platforms || {});
    if (entries.length === 0) {
      platformListContainer.innerHTML = `<div class="empty-prompt">No platform activity recorded yet.</div>`;
      return;
    }
    entries.forEach(([name, cnt]) => {
      const row = document.createElement("div");
      row.className = "platform-item";
      row.innerHTML = `
        <span>🤖 ${name.toUpperCase()}</span>
        <span style="color: #38bdf8;">${cnt} runs</span>
      `;
      platformListContainer.appendChild(row);
    });
  }

  // Fetch Verification History
  async function loadHistory() {
    try {
      const res = await fetch(`${BACKEND_URL}/api/history?limit=25`);
      if (res.ok) {
        const data = await res.json();
        historyTableBody.innerHTML = "";
        if (data.items.length === 0) {
          historyTableBody.innerHTML = `<tr><td colspan="7" class="empty-state">No verification records found. Run a verification from extension to populate history.</td></tr>`;
          return;
        }

        data.items.forEach(r => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td><code>${r.request_id}</code></td>
            <td><strong>${r.platform.toUpperCase()}</strong></td>
            <td><span class="status-badge ${r.overall_status}">${r.overall_status.replace("_", " ")}</span></td>
            <td>${Math.round(r.overall_score * 100)}%</td>
            <td>${r.claims_count}</td>
            <td style="max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${r.preview}</td>
            <td>
              <button class="action-btn inspect-req-btn" data-req-id="${r.request_id}" style="padding: 4px 10px; font-size: 11px;">Inspect</button>
            </td>
          `;
          historyTableBody.appendChild(tr);
        });

        // Attach inspector button handlers
        document.querySelectorAll(".inspect-req-btn").forEach(btn => {
          btn.addEventListener("click", () => {
            const reqId = btn.getAttribute("data-req-id");
            inspectRequest(reqId);
          });
        });
      }
    } catch (e) {
      console.error("Error loading history:", e);
    }
  }

  // Inspect Request
  async function inspectRequest(requestId) {
    // Switch to inspector tab
    document.querySelector('[data-tab="inspector"]').click();
    inspectorSearchInput.value = requestId;
    inspectorDetailsArea.innerHTML = `<div class="empty-prompt">Loading claim data for ${requestId}...</div>`;

    try {
      const res = await fetch(`${BACKEND_URL}/api/verification/${requestId}`);
      if (res.ok) {
        const data = await res.json();
        inspectorDetailsArea.innerHTML = `
          <div style="margin-bottom: 16px; padding: 12px; background: #111827; border-radius: 8px;">
            <h3>Request: <code>${data.request_id}</code></h3>
            <p style="color: #94a3b8; font-size: 12px; margin-top: 4px;">Overall Score: <strong>${Math.round(data.overall_score * 100)}%</strong> | Status: <span class="status-badge ${data.overall_status}">${data.overall_status}</span></p>
          </div>
        `;

        data.claims.forEach((c, idx) => {
          const item = document.createElement("div");
          item.className = "inspector-card-item";
          item.innerHTML = `
            <div class="inspector-claim-title">Claim ${idx + 1}: "${c.claim}"</div>
            <div class="inspector-signals-grid">
              <div class="signal-pill">
                <div class="label">Status</div>
                <div class="val">${c.status}</div>
              </div>
              <div class="signal-pill">
                <div class="label">Confidence</div>
                <div class="val">${Math.round(c.confidence * 100)}%</div>
              </div>
              <div class="signal-pill">
                <div class="label">NLI Label</div>
                <div class="val">${c.nli} (${Math.round(c.nli_score * 100)}%)</div>
              </div>
              <div class="signal-pill">
                <div class="label">Source Credibility</div>
                <div class="val">${Math.round(c.source_reliability * 100)}%</div>
              </div>
            </div>
            <p style="color: #cbd5e1; font-size: 13px; margin-bottom: 8px;"><strong>Rationale:</strong> ${c.explanation}</p>
            <details style="margin-top: 8px; font-size: 12px; color: #94a3b8;">
              <summary style="cursor: pointer; font-weight: 600; color: #38bdf8;">View Evidence Snippets (${c.evidence.length})</summary>
              <div style="margin-top: 8px; display: flex; flex-direction: column; gap: 6px;">
                ${c.evidence.map(e => `
                  <div style="background: #111827; padding: 8px; border-radius: 4px;">
                    <a href="${e.url}" target="_blank" style="color: #38bdf8; font-weight: 600; text-decoration: none;">${e.title}</a>
                    <p style="margin-top: 4px; color: #cbd5e1;">${e.snippet}</p>
                  </div>
                `).join('')}
              </div>
            </details>
          `;
          inspectorDetailsArea.appendChild(item);
        });
      } else {
        inspectorDetailsArea.innerHTML = `<div class="empty-prompt">No record found with ID: ${requestId}</div>`;
      }
    } catch (e) {
      inspectorDetailsArea.innerHTML = `<div class="empty-prompt">Error retrieving details: ${e.message}</div>`;
    }
  }

  inspectBtn.addEventListener("click", () => {
    const q = inspectorSearchInput.value.trim();
    if (q) inspectRequest(q);
  });

  refreshDataBtn.addEventListener("click", () => {
    loadAnalytics();
    loadHistory();
  });

  // Initial Load
  loadAnalytics();
  loadHistory();
});
