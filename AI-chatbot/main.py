import os
from flask import Flask, render_template, request, jsonify
import logging

app = Flask(__name__)

# Try to import transformers pipeline. If not available, the app still runs
# but uses a small fallback responder so you can develop the UI locally.
transformers_available = True
chatbot = None
try:
    from transformers import pipeline
except Exception:
    transformers_available = False


def init_chatbot():
    """Lazy initialize the transformers pipeline. Returns True if initialized."""
    global chatbot
    if not transformers_available:
        return False
    if chatbot is None:
        try:
            # DialoGPT is used here as an example. You can replace the model string.
            chatbot = pipeline("text-generation", model="microsoft/DialoGPT-medium")
        except Exception as e:
            logging.exception("Failed to initialize transformers pipeline: %s", e)
            return False
    return True


def fallback_reply(user_text: str) -> str:
    """A tiny rule-based responder used when transformers isn't available.

    This ensures the web UI remains responsive during development.
    """
    txt = user_text.strip().lower()
    if not txt:
        return "Say something and I'll try to reply."
    if any(greet in txt for greet in ("hi", "hello", "hey", "yo")):
        return "Hi — I'm Buddy. I'm running in fallback mode (local AI not installed)."
    if "help" in txt:
        return (
            "I can chat! To enable a stronger AI locally, install `transformers` and a backend (e.g. torch):\n"
            "pip install transformers torch\nThen restart the app and reload this page."
        )
    # default echo-ish reply
    return "I don't have the local AI model available. Install requirements or ask something else."


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")

    # Prefer transformers when available
    if init_chatbot():
        try:
            # Limit tokens so responses are reasonably short
            response = chatbot(user_input, max_new_tokens=50)
            # generated_text may include the prompt; keep it simple
            bot_reply = response[0].get("generated_text", "")
            return jsonify({"reply": bot_reply})
        except Exception as e:
            logging.exception("Error while generating with transformers: %s", e)
            # fall through to fallback reply

    # fallback path (transformers not installed or failed)
    bot_reply = fallback_reply(user_input)
    return jsonify({"reply": bot_reply})


if __name__ == "__main__":
    # When developing on Windows, set host/port as needed. Debug = True for auto-reload.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
