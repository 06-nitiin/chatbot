# chatbot

A hybrid chatbot that combines deterministic rule-based responses with a Gemini AI fallback. Common messages are handled locally and quickly, while unmatched messages can use Gemini with recent conversation context.

**Live demo:** [health-chatbot-7afg.onrender.com](https://health-chatbot-7afg.onrender.com)

## Features

- Rule-based intent matching with fuzzy typo tolerance.
- Precision-weighted matching to reduce false positives.
- Gemini AI fallback with recent conversation memory.
- Canned fallback responses when Gemini is unavailable or unconfigured.
- Streaming responses through Server-Sent Events.
- Browser voice input through the Web Speech API.
- Clear conversation control.
- Response source labels for rules, AI, and unmatched fallback responses.
- Request validation for empty, malformed, and non-string messages.
- Session cookie security settings for local and HTTPS production use.
- Health-check endpoint for service monitoring.
- Offline automated tests for the rule engine, Gemini fallback, and Flask routes.

## How it works

1. `bot_engine.py` checks the message against the configured intents.
2. A sufficiently confident match returns an immediate local response.
3. An unmatched message is sent to Gemini when `GEMINI_API_KEY` is configured.
4. If Gemini is unavailable, the application returns a canned fallback response.
5. Recent conversation turns are stored in the Flask session, with a maximum of 20 entries.

## Project structure

```text
chatbot/
├── app.py                 # Flask server, routes, sessions, and validation
├── bot_engine.py          # Intent matching and response routing
├── llm_fallback.py        # Gemini requests and streaming fallback
├── long_responses.py      # Canned responses and fallback messages
├── mains.py               # Terminal/CLI version of the bot
├── requirements.txt
├── test_app.py            # Flask route and API tests
├── test_bot_engine.py     # Rule-engine tests
├── test_llm_fallback.py   # Offline Gemini fallback tests
├── .env.example           # Safe environment-variable template
├── templates/
│   └── index.html         # Chat interface
└── static/
    ├── style.css          # Visual design and busy states
    └── script.js           # Chat, streaming, voice input, and controls
```

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy the environment template:

```bash
cp .env.example .env
```

Configure the local `.env` file with your own values:

```env
GEMINI_API_KEY=your-gemini-api-key
FLASK_SECRET_KEY=your-existing-secret-key
SESSION_COOKIE_SECURE=false
```

`GEMINI_MODEL` is optional. `.env` is ignored by Git and must never be committed.

For Render or another HTTPS deployment, set:

```text
SESSION_COOKIE_SECURE=true
```

Use the same `FLASK_SECRET_KEY` across local or production restarts when you want existing signed sessions to remain valid. Rotate it only if the old value may have been exposed.

## Running locally

Start the web application:

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

Check the service health in another terminal:

```bash
curl http://127.0.0.1:5000/health
```

Expected response:

```json
{"status":"ok"}
```

Run the terminal version:

```bash
python mains.py
```

Type `quit` or `exit` to leave.

## Testing

Run the complete offline test suite:

```bash
python -m unittest discover -v
```

The tests do not call Gemini or require a real API key. They cover the intent engine, Gemini error handling, streaming behavior, session history, request validation, health checks, and Flask routes.

Check Python syntax:

```bash
python -m py_compile app.py bot_engine.py llm_fallback.py test_app.py test_bot_engine.py test_llm_fallback.py
```

## Useful test messages

- `hi` or `hello` — rule-based greeting.
- `thanks` — rule-based response.
- `give me advice` — rule-based advice response.
- `another one` — tests conversation context through the AI fallback.
- `what's a good name for a pet rock?` — typically uses the AI fallback.

## Health endpoint

The `GET /health` endpoint returns a small JSON response without using the chatbot engine or Gemini:

```json
{"status":"ok"}
```

It can be used by a monitoring service or to confirm that a local or deployed Flask process is responding.

## Deployment

The application is configured for Render with:

```text
Build command: pip install -r requirements.txt
Start command: gunicorn app:app
```

Configure these environment variables in Render’s dashboard rather than committing them to Git:

- `GEMINI_API_KEY`
- `FLASK_SECRET_KEY`
- `SESSION_COOKIE_SECURE=true`
- Optional: `GEMINI_MODEL`

Keep development work on a feature branch, run the tests locally, and merge into `main` only when the changes are ready for the connected Render service:

```bash
git switch feature/new
python -m unittest discover -v
git add .
git commit -m "Describe the update"
git push origin feature/new

# When ready for deployment
git switch main
git pull origin main
git merge feature/new
git push origin main
```

## Adding a rule-based intent

Add a dictionary to `INTENTS` in `bot_engine.py` with an `id`, `response`, `words`, and either `single_response` or `required_words`. Add longer reusable text to `long_responses.py` when appropriate, then add a regression test to `test_bot_engine.py`.

Never commit `.env`, API keys, or production secrets. If a secret is exposed, revoke it and generate a replacement immediately.
