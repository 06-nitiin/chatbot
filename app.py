import json
import os

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, session, stream_with_context
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

import bot_engine
import llm_fallback
import long_responses as long

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")


limiter = Limiter(get_remote_address, app=app, default_limits=["60 per hour"])

MAX_HISTORY = 20


def get_history():
    if "history" not in session:
        session["history"] = []
    return session["history"]


def save_history(history):
    session["history"] = history[-MAX_HISTORY:]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
@limiter.limit("15 per minute")
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    history = get_history()
    response, confidence, matched, source, intent_id = bot_engine.get_response_with_confidence(
        user_message, history=history, allow_llm_fallback=True
    )

    history.append({"role": "user", "message": user_message})
    history.append({"role": "bot", "message": response})
    save_history(history)

    return jsonify(
        {
            "response": response,
            "confidence": confidence,
            "matched": matched,
            "source": source,
            "intent": intent_id,
        }
    )


@app.route("/api/chat/stream", methods=["POST"])
@limiter.limit("15 per minute")
def chat_stream():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    history = get_history()
    response_text, confidence, matched, intent_id = bot_engine.best_rule_match(user_message)

    def sse(payload):
        return f"data: {json.dumps(payload)}\n\n"

    if matched:
        history.append({"role": "user", "message": user_message})
        history.append({"role": "bot", "message": response_text})
        save_history(history)

        def generate():
            yield sse({"type": "chunk", "text": response_text})
            yield sse({"type": "done", "source": "rules", "confidence": confidence, "intent": intent_id})

        return Response(generate(), mimetype="text/event-stream")

    # Save the user's turn now (safe - happens before the response starts).
    history.append({"role": "user", "message": user_message})
    save_history(history)

    if llm_fallback.is_configured():
        history_snapshot = list(history)  # capture before the generator runs

        def generate():
            try:
                for piece in llm_fallback.ask_llm_stream(user_message, history=history_snapshot):
                    yield sse({"type": "chunk", "text": piece})
                yield sse({"type": "done", "source": "llm"})
            except llm_fallback.LLMUnavailable:
                fallback_text = long.unknown()
                yield sse({"type": "chunk", "text": fallback_text})
                yield sse({"type": "done", "source": "fallback"})

        return Response(stream_with_context(generate()), mimetype="text/event-stream")

    def generate():
        fallback_text = long.unknown()
        yield sse({"type": "chunk", "text": fallback_text})
        yield sse({"type": "done", "source": "fallback"})

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/chat/append-bot-reply", methods=["POST"])
def append_bot_reply():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    history = get_history()
    history.append({"role": "bot", "message": message})
    save_history(history)
    return jsonify({"status": "ok"})


@app.route("/api/clear", methods=["POST"])
def clear_history():
    session.pop("history", None)
    return jsonify({"status": "cleared"})


@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({"error": "Too many messages - please slow down a bit."}), 429


if __name__ == "__main__":
    app.run(debug=True)