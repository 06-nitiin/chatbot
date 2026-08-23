const log = document.getElementById("log");
const form = document.getElementById("prompt-form");
const input = document.getElementById("prompt-input");
const clock = document.getElementById("clock");

function tick() {
  const now = new Date();
  clock.textContent = now.toLocaleTimeString("en-GB", { hour12: false });
}
tick();
setInterval(tick, 1000);

function addLine(who, text, confidence) {
  const line = document.createElement("div");
  line.className = `line ${who}`;

  const whoSpan = document.createElement("span");
  whoSpan.className = "who";
  whoSpan.textContent = who === "bot" ? "BOT>" : "YOU>";

  const textSpan = document.createElement("span");
  textSpan.className = "text";
  textSpan.textContent = text;

  line.appendChild(whoSpan);
  line.appendChild(textSpan);

  if (who === "bot" && typeof confidence === "number") {
    const tag = document.createElement("span");
    tag.className = `confidence ${confidence >= 50 ? "high" : "low"}`;
    tag.textContent = `match ${confidence}%`;
    line.appendChild(tag);
  }

  log.appendChild(line);
  log.scrollTop = log.scrollHeight;
}

async function sendMessage(message) {
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    if (!res.ok) {
      addLine("bot", "Something went wrong talking to the server.");
      return;
    }

    const data = await res.json();
    addLine("bot", data.response, data.confidence);
  } catch (err) {
    addLine("bot", "Connection lost. Is the Flask server still running?");
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  addLine("user", message);
  input.value = "";
  sendMessage(message);
});