# Voice Assistant

An always-on, wake-word voice assistant: say "hey assistant", ask anything, and hear the answer read back.

**Why:** capture tasks and questions hands-free, on the go.

![Screenshot](docs/screenshot.png) <!-- TODO: add screenshot/GIF -->

## Features
- Wake word ("hey assistant") with continuous listening
- Google speech recognition with ambient-noise adjustment
- OpenAI chat responses, spoken back via pyttsx3
- Flask/WSGI entry (`app.py`, `wsgi.py`), Dockerfile, macOS launchd plist for running at login

## Tech stack
Python, SpeechRecognition, PyAudio, pyttsx3, OpenAI, python-dotenv, Docker

## Setup
```bash
pip install -r requirements.txt
echo "OPENAI_API_KEY=sk-..." > .env
python test_env.py        # verifies the key loads
python voice_assistant.py
```

## Environment variables
`OPENAI_API_KEY`

## License
MIT
