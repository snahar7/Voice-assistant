# AI Voice Assistant

An always-on AI voice assistant that uses speech recognition and OpenAI's GPT-3.5 for natural language processing.

## Features

- Voice activation with wake word ("hey assistant")
- Continuous listening mode
- Natural language processing using OpenAI's GPT-3.5
- Text-to-speech responses
- Ambient noise adjustment

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

3. Run the voice assistant:
```bash
python voice_assistant.py
```

## Usage

1. Start the assistant by running the script
2. Say "hey assistant" to activate
3. Wait for the "How can I help you?" prompt
4. Speak your command or question
5. Listen for the AI's response

## Requirements

- Python 3.7+
- OpenAI API key
- Microphone
- Speakers

## Note

Make sure your system's microphone and speakers are properly configured before running the assistant. 