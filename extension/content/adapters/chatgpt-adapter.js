/**
 * ChatGPT DOM Adapter
 * Extracts assistant response bubbles from ChatGPT web interface.
 */
window.ChatGPTAdapter = {
  name: "chatgpt",
  
  isMatch() {
    return window.location.hostname.includes("chatgpt.com") || window.location.hostname.includes("openai.com");
  },

  getLatestResponseElement() {
    // Select assistant messages by standard role or test attributes
    const assistantMessages = document.querySelectorAll(
      '[data-message-author-role="assistant"], div[data-testid^="conversation-turn-"]:has([data-message-author-role="assistant"]), .agent-turn'
    );
    if (!assistantMessages || assistantMessages.length === 0) {
      // Fallback selector
      const markdownBlocks = document.querySelectorAll('.markdown');
      if (markdownBlocks.length > 0) {
        return markdownBlocks[markdownBlocks.length - 1];
      }
      return null;
    }
    const latest = assistantMessages[assistantMessages.length - 1];
    const markdownContent = latest.querySelector('.markdown') || latest;
    return markdownContent;
  },

  getLatestResponseText() {
    const el = this.getLatestResponseElement();
    return el ? el.innerText.trim() : "";
  }
};
