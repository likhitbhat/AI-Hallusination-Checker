/**
 * Google Gemini DOM Adapter
 * Extracts assistant response bubbles from Google Gemini web interface.
 */
window.GeminiAdapter = {
  name: "gemini",

  isMatch() {
    return window.location.hostname.includes("gemini.google.com");
  },

  getLatestResponseElement() {
    const responseContainers = document.querySelectorAll(
      'model-response, .model-response-text, message-content, .response-container'
    );
    if (!responseContainers || responseContainers.length === 0) {
      return null;
    }
    const latest = responseContainers[responseContainers.length - 1];
    return latest;
  },

  getLatestResponseText() {
    const el = this.getLatestResponseElement();
    return el ? el.innerText.trim() : "";
  }
};
