# chatbot

A hybrid chatbot that started life as a two-file terminal keyword-matcher and has since grown into a deployed, context-aware, voice-enabled web app. Fast, free, deterministic rule-based matching handles common stuff (greetings, small talk); an AI fallback (Google Gemini's free API tier) with real conversation memory handles everything else.

**🔴 Live demo:** [health-chatbot-7afg.onrender.com](https://health-chatbot-7afg.onrender.com)
*(hosted on Render's free tier — the first load after inactivity can take ~30 seconds to wake up)*


## Features

- **Rule-based matching first.** Scores your message against predefined intents using word overlap (with typo tolerance via fuzzy matching), so common phrases get instant, free, deterministic replies with no API call at all.
- **AI fallback with memory.** Anything the rules can't confidently handle goes to Gemini's free API tier — and the bot actually remembers the conversation, so follow-ups like "another one" or "what about that city's population?" work correctly instead of being treated as a cold start each time.
- **Precision-weighted scoring.** Long, unrelated messages that happen to contain one common word (like "how" or "you") don't get hijacked by a short rule-based intent — the matcher checks how much of *your message* the intent actually explains, not just whether a keyword showed up anywhere in it.
- **Voice input.** Click the mic and talk instead of typing, using the browser's built-in Web Speech API (Chrome/Edge/Safari). Continuous listening means pausing mid-sentence to think doesn't cut you off — click the mic again when you're done to send.
- **Per-user session memory**, with a `clear` button to reset the conversation on demand.
- **Every reply is tagged with its source** (`rules`, `ai`, or `unmatched`) so you can see which path handled it.
- **Deployed for free** on Render, from a GitHub repo, with zero paid services anywhere in the stack.

## How it works

1. **Rules first.** `bot_engine.py` scores your message against a list of intents. If one scores above the confidence threshold, that's the reply — no network call, instant, free.
2. **AI fallback, with context.** If nothing matches confidently and a `GEMINI_API_KEY` is configured, the message — plus recent conversation history from the Flask session — is sent to Gemini for a real generated reply.
3. **Canned fallback.** If neither applies (no key configured, or the API call fails), the bot returns a generic "I don't understand" response instead of erroring out.

## Project structure

```
chatbot/
├── app.py               # Flask server — routes, session handling
├── bot_engine.py          # Core matching logic + fallback routing
├── llm_fallback.py         # Calls Gemini's free API, with conversation history
├── mains.py                # Terminal/CLI version of the bot
├── long_responses.py      # Canned longer replies + fallback responses
├── requirements.txt
├── .env.example             # Template for your local secrets — copy to .env
├── templates/
│   └── index.html         # Chat UI page
└── static/
    ├── style.css           # Terminal-style visual design
    └── script.js           # Chat logic, voice input, talks to /api/chat
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
python3 -m pip install -r requirements.txt
```

### Environment variables

Copy the template and fill in your own values:
```bash
cp .env.example .env
```

You'll need two:

- **`GEMINI_API_KEY`** — free, no credit card required. Get one at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
- **`FLASK_SECRET_KEY`** — used to cryptographically sign session cookies (this is what makes conversation memory work). Generate one yourself:
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```

`.env` is gitignored, so neither of these ever gets committed. If you skip `GEMINI_API_KEY`, unmatched messages just get the generic fallback reply instead of an AI-generated one. `FLASK_SECRET_KEY` has a hardcoded development fallback in `app.py`, but you should always set a real one before deploying anywhere public.

## Running it

**Web app:**
```bash
python3 app.py
```
Then open `http://127.0.0.1:5000`.

**Terminal version:**
```bash
python3 mains.py
```
Type `quit` or `exit` to leave.

## Try asking it

- `hi` / `hello` — rule-based
- `give me advice` — rule-based, then say `another one` — tests memory, since the AI needs the prior turn to know what you mean
- Anything off-script, e.g. `what's a good name for a pet rock?` — goes to the AI fallback
- Click the mic and just talk — try pausing mid-sentence to confirm it doesn't cut you off

## Deployment

This runs on Render's free tier via `gunicorn app:app`. To deploy your own copy:

1. Push your repo to GitHub.
2. Create a new Web Service on [render.com](https://render.com), connect the repo.
3. Build command: `pip install -r requirements.txt`. Start command: `gunicorn app:app`.
4. Add `GEMINI_API_KEY` and `FLASK_SECRET_KEY` as environment variables in Render's dashboard (Environment tab) — these are never read from your local `.env` file, so this step is required separately.
5. Deploy. Render auto-redeploys on every push to your connected branch by default.

## Notes

- Flask's dev server (`python3 app.py`) is fine for local use; production traffic goes through `gunicorn` instead, which is what Render actually runs.
- The matching logic lives in `bot_engine.py` — add a new dict to `INTENTS` with a `response`, `words`, and either `single_response` or `required_words` to extend it.
- Free API tiers change their limits and model names over time. If `llm_fallback.py` stops working, check whether Google has deprecated the current model (this has already happened once during development) and update `GEMINI_MODEL` in `.env` accordingly.
- Never commit your real `.env` file. If you ever do by accident, revoke both keys immediately and generate new ones.