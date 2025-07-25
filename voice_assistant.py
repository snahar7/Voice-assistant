import speech_recognition as sr
import pyttsx3
import openai
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Initialize OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

class VoiceAssistant:
    def __init__(self):
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        
        # Set voice properties
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[0].id)  # Index 0 for male, 1 for female
        self.engine.setProperty('rate', 150)    # Speaking rate
        
        # Wake word
        self.wake_word = "hey assistant"
        
        print("Voice Assistant initialized and ready!")

    def speak(self, text):
        """Convert text to speech"""
        print(f"Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        """Listen for audio input"""
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                return self.recognizer.recognize_google(audio).lower()
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                return ""
            except Exception as e:
                print(f"Error: {str(e)}")
                return ""

    def process_command(self, command):
        """Process voice command using OpenAI"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful voice assistant. Keep responses concise and natural."},
                    {"role": "user", "content": command}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"

    def run(self):
        """Main loop for the voice assistant"""
        self.speak("Hello! I'm your AI voice assistant. Say 'hey assistant' to wake me up.")
        
        while True:
            text = self.listen()
            
            if text:
                print(f"You said: {text}")
                
                if self.wake_word in text:
                    self.speak("Yes, I'm here! How can I help you?")
                    
                    # Listen for the actual command
                    command = self.listen()
                    if command:
                        print(f"Command: {command}")
                        response = self.process_command(command)
                        self.speak(response)
                
            time.sleep(0.1)  # Small delay to prevent high CPU usage

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run() 