from flask import Flask, render_template, request, jsonify
from transformers import pipeline

app = Flask(__name__)

# Load AI model
chatbot = pipeline("text-generation", model="microsoft/DialoGPT-medium")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json["message"]
    response = chatbot(user_input, max_new_tokens=50)
    bot_reply = response[0]["generated_text"]
    return jsonify({"reply": bot_reply})

if __name__ == "__main__":
    app.run(debug=True)
