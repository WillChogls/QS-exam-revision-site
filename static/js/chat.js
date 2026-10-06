// Chat tutor panel: UI only. Replace getReply() with a backend call later.
(function () {
  "use strict";

  const PLACEHOLDER_REPLY = "AI tutor coming soon.";

  /**
   * Get the tutor's reply to a message.
   * context: { level, subject, year, paper, paperId, question } (question is a number or null)
   * Currently unused: swap this body for e.g. a fetch() to a Flask endpoint.
   */
  async function getReply(message, context) {
    return PLACEHOLDER_REPLY;
  }

  const panel = document.getElementById("chat-panel");
  if (!panel) return;

  const toggle = document.getElementById("chat-toggle");
  const messages = document.getElementById("chat-messages");
  const empty = document.getElementById("chat-empty");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const question = document.getElementById("chat-question");
  const sendButton = document.getElementById("chat-send");
  const clearButton = document.getElementById("chat-clear");

  function getContext() {
    const d = panel.dataset;
    return {
      level: d.level,
      subject: d.subject,
      year: Number(d.year),
      paper: Number(d.paper),
      paperId: Number(d.paperId),
      question: question.value ? Number(question.value) : null,
    };
  }

  function addMessage(role, text) {
    const item = document.createElement("li");
    item.className = "chat-message chat-message-" + role;
    item.dataset.role = role;

    const author = document.createElement("p");
    author.className = "chat-message-author";
    author.textContent = role === "user" ? "You" : "Tutor";
    if (role === "user" && question.value) author.textContent += " · Q" + question.value;

    const body = document.createElement("p");
    body.className = "chat-message-text";
    body.textContent = text;

    item.append(author, body);
    messages.append(item);
    empty.hidden = true;
    item.scrollIntoView({ block: "nearest" });
  }

  toggle.addEventListener("click", function () {
    panel.hidden = !panel.hidden;
    toggle.setAttribute("aria-expanded", String(!panel.hidden));
    toggle.textContent = panel.hidden ? "Show chat" : "Hide chat";
    if (!panel.hidden) input.focus();
  });

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    addMessage("user", text);
    input.value = "";
    sendButton.disabled = true;
    try {
      addMessage("tutor", await getReply(text, getContext()));
    } catch (err) {
      addMessage("tutor", "Sorry, something went wrong.");
    } finally {
      sendButton.disabled = false;
      input.focus();
    }
  });

  clearButton.addEventListener("click", function () {
    messages.replaceChildren();
    empty.hidden = false;
    input.focus();
  });
})();
