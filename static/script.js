const log = document.getElementById("log");
const form = document.getElementById("prompt-form");
const input = document.getElementById("prompt-input");
const clock = document.getElementById("clock");
const micButton = document.getElementById("mic-button");
const micStatus = document.getElementById("mic-status");
const clearButton = document.getElementById("clear-btn");

const WELCOME_MESSAGE = 'Hi. I now remember our conversation context — try "hi", "give me advice", then "another one". You can also click the mic to talk.';

function tick() {
  const now = new Date();
  clock.textContent = now.toLocaleTimeString("en-GB", { hour12: false });
}
tick();
setInterval(tick, 1000);

const SOURCE_LABELS = {
  rules: "rules",
  llm: "ai",
  fallback: "unmatched",
};

function addLine(who, text, confidence, source) {
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

  if (who === "bot" && source) {
    const tag = document.createElement("span");
    tag.className = `confidence source-${source}`;
    tag.textContent = source === "rules" ? `match ${confidence}%` : SOURCE_LABELS[source] || source;
    line.appendChild(tag);
  }

  log.appendChild(line);
  log.scrollTop = log.scrollHeight;
}

async function clearConversation() {
  clearButton.disabled = true;

  try {
    const response = await fetch("/api/clear", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error("Could not clear the conversation");
    }

    log.replaceChildren();
    addLine("bot", WELCOME_MESSAGE);
    input.value = "";
    input.focus();
  } catch (error) {
    addLine("bot", "I couldn't clear the conversation. Please try again.");
  } finally {
    clearButton.disabled = false;
  }
}

clearButton.addEventListener("click", clearConversation);

async function streamMessage(message) {
  const botLine = document.createElement("div");
  botLine.className = "line bot";
  const whoSpan = document.createElement("span");
  whoSpan.className = "who";
  whoSpan.textContent = "BOT>";
  const textSpan = document.createElement("span");
  textSpan.className = "text";
  botLine.appendChild(whoSpan);
  botLine.appendChild(textSpan);
  log.appendChild(botLine);
  log.scrollTop = log.scrollHeight;

  let fullText = "";
  let source = null;
  let confidence = null;

  try {
    const res = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    if (res.status === 429) {
      const data = await res.json().catch(() => ({}));
      textSpan.textContent = data.error || "Too many messages - please slow down.";
      return;
    }

    if (!res.ok || !res.body) {
      textSpan.textContent = "Something went wrong talking to the server.";
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop();

      for (const evt of events) {
        if (!evt.startsWith("data: ")) continue;
        const payload = JSON.parse(evt.slice(6));

        if (payload.type === "chunk") {
          fullText += payload.text;
          textSpan.textContent = fullText;
          log.scrollTop = log.scrollHeight;
        } else if (payload.type === "done") {
          source = payload.source;
          confidence = payload.confidence;
        }
      }
    }
  } catch (err) {
    textSpan.textContent = fullText || "Connection lost. Is the Flask server still running?";
    return;
  }

  if (source) {
    const tag = document.createElement("span");
    tag.className = `confidence source-${source}`;
    tag.textContent = source === "rules" ? `match ${confidence}%` : (SOURCE_LABELS[source] || source);
    botLine.appendChild(tag);
  }

  if (source === "llm" && fullText) {
    fetch("/api/chat/append-bot-reply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: fullText }),
    }).catch(() => {});
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  addLine("user", message);
  input.value = "";
  streamMessage(message);
});

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
  micButton.style.display = "none";
} else {
  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = "en-US";

  let isListening = false;

  function setListeningState(listening) {
    isListening = listening;
    micButton.classList.toggle("listening", listening);
    micStatus.textContent = listening ? "listening... (click mic again when done)" : "";
  }

  micButton.addEventListener("click", () => {
    if (isListening) {
      recognition.stop();
      return;
    }
    try {
      recognition.start();
      setListeningState(true);
    } catch (err) {
      // The browser may reject repeated start calls while recognition is active.
    }
  });

  recognition.addEventListener("result", (event) => {
    let transcript = "";
    for (let i = 0; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    input.value = transcript;
    input.scrollLeft = input.scrollWidth;
  });

  recognition.addEventListener("end", () => {
    setListeningState(false);
    const message = input.value.trim();
    if (message) {
      addLine("user", message);
      input.value = "";
      streamMessage(message);
    }
  });

  recognition.addEventListener("error", (event) => {
    setListeningState(false);
    if (event.error === "not-allowed" || event.error === "service-not-allowed") {
      micStatus.textContent = "Microphone access denied.";
    } else if (event.error === "no-speech") {
      micStatus.textContent = "Didn't catch that, please try again.";
    } else {
      micStatus.textContent = "Voice input error.";
    }
    setTimeout(() => { micStatus.textContent = ""; }, 3000);
  });
}
