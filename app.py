from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
import os

load_dotenv()

from bot_engine import get_response_with_confidence

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    if "history" not in session:
        session["history"] = []

    history = session["history"]

    response, confidence, matched, source, intent_id = get_response_with_confidence(
        user_message, history=history, allow_llm_fallback=True
    )

    history.append({
        "role": "user",
        "message": user_message,
        "intent": None,
        "source": None,
    })
    history.append({
        "role": "bot",
        "message": response,
        "intent": intent_id,
        "source": source,
    })

    if len(history) > 20:
        session["history"] = history[-20:]
    else:
        session["history"] = history

    return jsonify({
        "response": response,
        "confidence": confidence,
        "matched": matched,
        "source": source,
        "intent": intent_id,
    })


@app.route("/api/clear", methods=["POST"])
def clear_history():
    session.pop("history", None)
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True)