/**
 * Claude DOM Adapter
 * Extracts assistant response bubbles from Anthropic Claude web interface.
 */
window.ClaudeAdapter = {
  name: "claude",

  isMatch() {
    return window.location.hostname.includes("claude.ai");
  },

  getLatestResponseElement() {
    const assistantMessages = document.querySelectorAll(
      '[data-is-streaming="false"] .font-claude-message, .font-claude-message, [data-testid="chat-message-content"]'
    );
    if (!assistantMessages || assistantMessages.length === 0) {
      return null;
    }
    const latest = assistantMessages[assistantMessages.length - 1];
    return latest;
  },

  getLatestResponseText() {
    const el = this.getLatestResponseElement();
    return el ? el.innerText.trim() : "";
  }
};
