import os
from flask import Flask, render_template, request, jsonify
import logging
import os

app = Flask(__name__)

# Try to import transformers pipeline. If not available, the app still runs
# but uses a small fallback responder so you can develop the UI locally.
transformers_available = True
chatbot = None
try:
    from transformers import pipeline
except Exception:
    transformers_available = False

# OpenAI SDK will be imported dynamically inside `openai_reply` so the
# editor won't flag a missing module at import time. At runtime we attempt
# to import the package only if `OPENAI_API_KEY` is present.


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


def openai_reply(user_text: str) -> str:
    """Call OpenAI ChatCompletion (gpt-3.5-turbo) if API key and package are available.

    Returns the assistant reply text on success, or None on error/unavailable.
    """
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None

        # Import openai dynamically so missing package doesn't trigger
        # a static analyzer error in editors. If it's not installed, just
        # return None and the caller will fall back.
        try:
            import importlib

            openai = importlib.import_module("openai")
        except Exception:
            return None

        openai.api_key = api_key
        # Use a simple system prompt to keep replies chatty and helpful
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Buddy, a helpful assistant."},
                {"role": "user", "content": user_text},
            ],
            max_tokens=150,
            temperature=0.7,
        )
        if resp and getattr(resp, "choices", None) and len(resp.choices) > 0:
            # Newer SDKs return dict-like objects; guard access safely
            choice = resp.choices[0]
            # choice.message may be present (newer) or choice.get('message') for dicts
            msg = None
            if hasattr(choice, "message"):
                msg = choice.message.get("content", "")
            elif isinstance(choice, dict):
                msg = choice.get("message", {}).get("content", "")
            else:
                msg = getattr(choice, "text", "")
            return (msg or "").strip()
    except Exception as e:
        logging.exception("OpenAI request failed: %s", e)
    return None


def gemini_reply(user_text: str) -> str:
    """Attempt to call Google Gemini / Generative AI.

    This function tries a few common client libraries (`google.generativeai`,
    `google.cloud.aiplatform`/Vertex AI) using dynamic imports so missing
    packages won't break static analysis. If a call succeeds it should return
    the assistant text, otherwise returns None to allow fallback.
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return None

        import importlib
        # Try google.generativeai (the lightweight GenAI client)
        try:
            genai = importlib.import_module("google.generativeai")
            # configure API key if available
            if hasattr(genai, "configure"):
                try:
                    genai.configure(api_key=api_key)
                except Exception:
                    # some versions use different names; try setting attribute
                    try:
                        setattr(genai, "api_key", api_key)
                    except Exception:
                        pass

            # Preferred method: genai.chat.create or genai.generate_text
            if hasattr(genai, "chat") and hasattr(genai.chat, "create"):
                try:
                    resp = genai.chat.create(model="gemini", messages=[{"author": "user", "content": user_text}])
                    # Try common response shapes
                    if isinstance(resp, dict):
                        # dict-like: look for candidates / messages
                        cand = resp.get("candidates") or resp.get("outputs")
                        if cand and len(cand) > 0:
                            first = cand[0]
                            return first.get("content") or first.get("text")
                    else:
                        # object-like
                        candidates = getattr(resp, "candidates", None)
                        if candidates and len(candidates) > 0:
                            c = candidates[0]
                            return getattr(c, "content", None) or getattr(c, "text", None)
                except Exception:
                    pass

            if hasattr(genai, "generate_text"):
                try:
                    # Some clients accept model name like "text-bison-001" or "gemini" family
                    resp = genai.generate_text(model="text-bison-001", prompt=user_text)
                    if isinstance(resp, dict):
                        return resp.get("result") or resp.get("text") or resp.get("output")
                    else:
                        return getattr(resp, "text", None) or getattr(resp, "result", None)
                except Exception:
                    pass
        except Exception:
            # google.generativeai not available or call failed — try Vertex AI
            pass

        # Try Vertex AI via google.cloud.aiplatform (if installed/configured)
        try:
            aiplatform = importlib.import_module("google.cloud.aiplatform")
            try:
                # initialize client using project/region env vars or default credentials
                client = aiplatform.gapic.PredictionServiceClient()
                # The REST/gRPC call shape depends on deployment; we won't try to guess here.
                # Return None so fallback occurs if we can't safely call it.
                return None
            except Exception:
                return None
        except Exception:
            pass

    except Exception as e:
        logging.exception("Gemini request failed: %s", e)
    return None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    sticker = request.json.get("sticker") if request.is_json else None

    # If a sticker is sent, acknowledge it quickly (frontend already displays it)
    if sticker:
        # You could implement richer logic here (e.g., tag-based replies)
        return jsonify({"reply": "Nice sticker!"})

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

    # Next prefer Gemini (Google Generative AI) if configured
    gemini_ans = gemini_reply(user_input)
    if gemini_ans is not None:
        return jsonify({"reply": gemini_ans})

    # Then prefer OpenAI if configured
    openai_ans = openai_reply(user_input)
    if openai_ans is not None:
        return jsonify({"reply": openai_ans})

    # fallback path (transformers & OpenAI not available or failed)
    bot_reply = fallback_reply(user_input)
    return jsonify({"reply": bot_reply})


if __name__ == "__main__":
    # When developing on Windows, set host/port as needed. Debug = True for auto-reload.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
