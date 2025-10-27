# Buddy — Simple local AI Chatbot

This small Flask app serves a tiny chat UI and (optionally) uses a local transformer model to generate replies.

Quick setup (Windows PowerShell)

```powershell
# create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# run the app
python main.py
```

Notes
- If you don't (yet) want to install `transformers` and `torch`, the app will still run in a lightweight "fallback" mode that replies with simple messages.
- To enable the full AI responses install `transformers` and a backend (for most users: `torch`).
- Models like `microsoft/DialoGPT-medium` can be large — expect download time and memory usage. Use smaller models for development.

Troubleshooting
- If VS Code reports "Import 'transformers' could not be resolved": make sure the workspace interpreter is set to the venv created above (Command Palette → Python: Select Interpreter).
- Verify installation from the terminal used by VS Code:

```powershell
python -c "import transformers; print(transformers.__version__)"
```

OpenAI integration

To enable OpenAI as a fallback provider (useful if you don't want to run local models), do the following:

1. Install the Python package (already added to `requirements.txt`):

```powershell
pip install -r requirements.txt
```

2. Set your OpenAI API key in the environment before running the app (PowerShell):

```powershell
$env:OPENAI_API_KEY = "sk-..."
python main.py
```

When `OPENAI_API_KEY` is present and the `openai` package is available, the server will call OpenAI (gpt-3.5-turbo) to generate replies. If neither local transformers nor OpenAI are available, the app uses a small local fallback responder so the UI remains usable.

Gemini (Google) integration

You can also use Google Gemini (Generative AI) as a provider. The server will attempt to call Gemini when `GEMINI_API_KEY` or `GOOGLE_API_KEY` is set and a supported client library is installed. The app tries `google.generativeai` first and falls back to Vertex AI libraries if present.

Install a client (choose one):

```powershell
# lightweight GenAI client (recommended):
pip install google-generativeai

# or install Vertex AI SDK (if you prefer):
pip install google-cloud-aiplatform
```

Set the API key (PowerShell):

```powershell
$env:GEMINI_API_KEY = "YOUR_KEY_HERE"
python main.py
```

Notes:
- The Gemini integration in this project uses dynamic imports and multiple call patterns to remain flexible across client library versions. If you hit errors, check which client you installed and consult its docs. If you'd like, I can adapt the code to a single client and sample call shape matching your preferred library/version.
