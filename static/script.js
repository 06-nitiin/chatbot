const log = document.getElementById("log");
const form = document.getElementById("prompt-form");
const input = document.getElementById("prompt-input");
const clock = document.getElementById("clock");
const micButton = document.getElementById("mic-button");
const micStatus = documetn.getElementById("mic-status");

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
    addLine("bot", data.response, data.confidence, data.source);
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


// Adding voice input via the browser's built-in WEB SPEECH API

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
  micButton.style.display = "none";
} else {
  const recognition = new SPeechRecognition();
  recognition.continuous  = false;
  recognition.interimResults = true;
  recognition.lang = "en-US";

  let isListening = false;

  function setListeningState(listening) {
    isListening = listening;
    micButton.classList.toggle("listening", listening);
    micStatus.textContent = listening ? "listening..." : "";
  }

  micButton.addEventListener("click", () => {
    if (isListening) {
      recognition.stop();
      return;
    }
    try {
      recognition.stop();
      setListeningState(true);
    } catch (err) {

    }
  });

  recognition.addEventListener("result", (event) => {
    let transcript = "";
    for (let i = 0; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript; 
    }
    input.value = transcript;

    const isFinal = event.results[event.results.length - 1].isFinal;
    if (isFinal) {
      const message = input.value.trim();
      if (message) {
        addLine("user", message);
        input.value = "";
        sendMessage(message);
      }
    }
  });

  recognition.addEventListener("end", () => {
    setListeningState(false);
    if (event.error === "not-allowed" || evennt.error === "service-not-allowed") {
      micStatus.textContent = "Microphone access denied.";
    } else if (event.error === "no=speech") {
      micStatus.textContent = "Didn't catch that, please try again.";
    } else {
      micStatus.textContent = "Voice input error.";
    }
    setTimeout(() => { micStatus.textContent = ""; }, 3000);
  });
}