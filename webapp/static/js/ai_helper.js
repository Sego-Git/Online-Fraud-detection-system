const helperBtn = document.getElementById("ai-helper-btn");
const chatBox = document.getElementById("ai-chatbox");
const sendBtn = document.getElementById("send-ai");
const userInput = document.getElementById("ai-input");
const messages = document.getElementById("ai-chat-messages");

helperBtn.onclick = () => {
  chatBox.style.display =
    chatBox.style.display === "flex" ? "none" : "flex";
};

sendBtn.onclick = sendMessage;
userInput.addEventListener("keypress", e => {
  if (e.key === "Enter") sendMessage();
});

function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  addMessage("You", text);
  userInput.value = "";

  // Temporary simple explanation (will later connect to backend AI)
  setTimeout(() => {
    addMessage(
      "AI Helper",
      "This result shows how risky your transactions are. High risk means the transaction is more likely to be fraudulent. Medium risk should be reviewed, and low risk is usually safe."
    );
  }, 800);
}

function addMessage(sender, text) {
  const msg = document.createElement("div");
  msg.innerHTML = `<strong>${sender}:</strong> ${text}`;
  msg.style.marginBottom = "8px";
  messages.appendChild(msg);
  messages.scrollTop = messages.scrollHeight;
}
