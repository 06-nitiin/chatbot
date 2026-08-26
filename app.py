from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request


load_dotenv()

from bot_engine import get_response_with_confidence
 
app = Flask(__name__)
 
 
@app.route("/")
def index():
    return render_template("index.html")
 
 
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    response, confidence, matched, source = get_response_with_confidence(user_message)

    return jsonify(
        {
            "response": response,
            "confidence": confidence,
            "matched": matched,
            "source": source,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)