# Jarvis AI

A voice-controlled personal assistant built with Python. Jarvis can perform system tasks, tell the time, search the web using Google (via SerpAPI), and chat using OpenAI GPT.  

---

## Features

- Voice recognition and command execution
- System commands:
  - Open apps: Chrome, Notepad, VS Code
  - Take screenshots
  - Shutdown computer
  - Tell current time
- Web search using Google via SerpAPI
- Chat responses via OpenAI GPT
- Multi-language support
- Fully customizable and extensible

---

## Requirements

- Python 3.10+
- Packages (install via `pip install -r requirements.txt`):
  - `speechrecognition`
  - `edge_tts`
  - `pygame`
  - `pyautogui`
  - `requests`
  - `openai`
  - `serpapi`

---

## Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/<your-username>/jarvis-ai.git
    cd jarvis-ai
    ```

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate      # Linux / macOS
    venv\Scripts\activate         # Windows
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set API keys in `jarvis.py`:
    ```python
    openai.api_key = "YOUR_OPENAI_API_KEY"
    SERPAPI_API_KEY = "YOUR_SERPAPI_KEY"
    ```

---

## Usage

Run Jarvis:

```bash
python jarvis.py
