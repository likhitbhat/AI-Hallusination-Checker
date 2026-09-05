document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("settingsForm");
  const backendUrlInput = document.getElementById("backendUrlInput");
  const autoHighlightCheckbox = document.getElementById("autoHighlightCheckbox");
  const statusMsg = document.getElementById("statusMsg");

  // Load saved preferences
  chrome.storage.local.get(["backendUrl", "autoHighlight"], (result) => {
    backendUrlInput.value = result.backendUrl || "http://127.0.0.1:8000";
    autoHighlightCheckbox.checked = result.autoHighlight !== false;
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const url = backendUrlInput.value.trim().replace(/\/+$/, "");
    const autoHighlight = autoHighlightCheckbox.checked;

    chrome.storage.local.set({
      backendUrl: url,
      autoHighlight: autoHighlight
    }, () => {
      statusMsg.innerText = "Settings saved successfully!";
      statusMsg.className = "status-msg success";
      setTimeout(() => {
        statusMsg.style.display = "none";
      }, 2500);
    });
  });
});
