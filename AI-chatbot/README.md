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
