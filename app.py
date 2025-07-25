from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import speech_recognition as sr
import threading
import json
import os
from datetime import datetime
import time
import requests
import pyaudio
import wave
import numpy as np
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Handle reverse proxies
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize SocketIO with SSL support and optimized settings
socketio = SocketIO(app, 
                   cors_allowed_origins="*", 
                   ssl_context=('ssl/cert.pem', 'ssl/key.pem'),
                   async_mode='threading',
                   ping_timeout=10,
                   ping_interval=5,
                   max_http_buffer_size=5e6)

# Store tasks in memory (you can later persist this to a database)
tasks = []
# Global flag to control background listening
is_listening = False
background_thread = None
# Cache the microphone instance
_microphone = None

def get_microphone():
    """Get or create a cached microphone instance"""
    global _microphone
    if _microphone is None:
        _microphone = sr.Microphone(
            device_index=None,
            sample_rate=44100,  # Standard sample rate
            chunk_size=4096
        )
    return _microphone

def play_activation_sound():
    """Play a subtle activation sound"""
    SAMPLE_RATE = 44100
    DURATION = 0.05  # Reduced to 50ms
    
    # Generate a short ascending tone with even softer frequencies
    t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION))
    # Even lower frequency range
    frequency = np.linspace(400, 800, len(t))
    # Softer sine wave with gentler envelope
    samples = np.sin(2 * np.pi * frequency * t) * np.exp(-8 * t)
    
    # Reduce amplitude to 30% of maximum
    samples = (samples * 32767 * 0.3).astype(np.int16)
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # Open stream
    stream = p.open(format=pyaudio.paInt16,
                   channels=1,
                   rate=SAMPLE_RATE,
                   output=True)
    
    # Play the sound
    stream.write(samples.tobytes())
    
    # Clean up
    stream.stop_stream()
    stream.close()
    p.terminate()

def check_internet_connection():
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except:
        return False

def background_listening():
    """Continuous background listening for wake word"""
    global is_listening
    
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 250
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.5
    recognizer.phrase_threshold = 0.3
    recognizer.non_speaking_duration = 0.3
    
    microphone = get_microphone()  # Use cached microphone
    
    print("Starting background listening...")
    print("Available microphones:", sr.Microphone.list_microphone_names())
    socketio.emit('status', {'message': 'Assistant is ready! Say "Jarvis" to give a task.'})
    
    # Initial calibration
    with microphone as source:
        print("Performing initial calibration...")
        socketio.emit('status', {'message': 'Calibrating microphone...'})
        recognizer.adjust_for_ambient_noise(source, duration=1)  # Reduced calibration time
        print(f"Energy threshold set to {recognizer.energy_threshold}")
    
    while is_listening:
        try:
            if listen_for_wake_word(recognizer, microphone):
                task_text = listen_for_task(recognizer, microphone)
                if task_text:
                    task = {
                        'id': len(tasks) + 1,
                        'text': task_text,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'completed': False
                    }
                    tasks.append(task)
                    print(f"Task added: {task}")
                    socketio.emit('new_task', task)
                    socketio.emit('status', {'message': 'Task added! Say "Jarvis" for another task.'})
                else:
                    socketio.emit('status', {'message': 'Ready for new task. Say "Jarvis" to try again.'})
        except Exception as e:
            print(f"Error in background listening: {str(e)}")
            socketio.emit('status', {'message': 'Temporarily lost connection. Reconnecting...'})
        time.sleep(0.1)

def listen_for_wake_word(recognizer, microphone):
    """Listen specifically for the wake word 'Jarvis'"""
    try:
        with microphone as source:
            print("Listening for wake word 'Jarvis'...")
            socketio.emit('status', {'message': 'Waiting for wake word "Jarvis"...'})
            
            # Quick calibration before each wake word attempt
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            # More lenient listening parameters
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=2)
            
            try:
                # Try Google Speech Recognition first
                text = recognizer.recognize_google(
                    audio,
                    language='en-US',
                    show_all=True  # Get confidence scores
                )
                
                print(f"Raw recognition result: {text}")  # Debug output
                
                # List of wake word variants (ordered by priority)
                wake_words = [
                    'jarvis',
                    'travis',
                    'javis',
                    'jarves',
                    'service',
                    'järvis',
                    'jervis',
                    'jarvus',
                    'java',
                    'drivers'
                ]
                
                if isinstance(text, dict) and 'alternative' in text:
                    # Process all alternatives
                    for alt in text['alternative']:
                        transcript = alt.get('transcript', '').lower()
                        confidence = alt.get('confidence', 0)
                        
                        print(f"Alternative: {transcript} (confidence: {confidence})")
                        
                        # Check each wake word with word boundary
                        for wake_word in wake_words:
                            if f" {wake_word} " in f" {transcript} ":
                                print(f"Wake word '{wake_word}' detected with confidence {confidence}!")
                                play_activation_sound()
                                return True
                            
                elif isinstance(text, str):
                    # Fallback for when show_all=True doesn't work
                    text = text.lower()
                    print(f"Heard (string): {text}")
                    for wake_word in wake_words:
                        if f" {wake_word} " in f" {text} ":
                            print(f"Wake word '{wake_word}' detected!")
                            play_activation_sound()
                            return True
                return False
                
            except sr.UnknownValueError:
                return False
                
            except sr.RequestError:
                # If online recognition fails, try Sphinx
                try:
                    text = recognizer.recognize_sphinx(
                        audio,
                        keyword_entries=[('jarvis', 0.4), ('travis', 0.4)]
                    ).lower()
                    print(f"Sphinx heard: {text}")
                    if any(f" {wake_word} " in f" {text} " for wake_word in ['jarvis', 'travis']):
                        print("Wake word detected (using Sphinx)!")
                        play_activation_sound()
                        return True
                except Exception as e:
                    print(f"Sphinx recognition failed: {str(e)}")
                return False
                
    except Exception as e:
        print(f"Error in wake word detection: {str(e)}")
        return False

def listen_for_task(recognizer, microphone, max_retries=2):
    """Listen for a task and return the recognized text"""
    retries = 0
    while retries <= max_retries:
        try:
            with microphone as source:
                # Play activation sound and start listening immediately
                if retries == 0:  # Only play sound on first attempt
                    play_activation_sound()
                    # Quick calibration on first attempt
                    recognizer.adjust_for_ambient_noise(source, duration=0.2)
                
                print(f"Listening for task (attempt {retries + 1})...")
                socketio.emit('status', {'message': f'Listening... (attempt {retries + 1})'})
                
                try:
                    # Increased timeout for more natural speech pace
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    print("Audio captured, processing...")
                    
                    try:
                        # Try with Google Speech Recognition
                        text = recognizer.recognize_google(
                            audio,
                            language='en-US'
                        )
                        print(f"Task recognized: {text}")
                        return text
                        
                    except sr.UnknownValueError:
                        print(f"Could not understand audio (attempt {retries + 1})")
                        if retries < max_retries:
                            socketio.emit('status', {'message': 'Could not understand. Please try again.'})
                            time.sleep(0.3)  # Shorter pause between attempts
                        else:
                            socketio.emit('status', {'message': 'Could not understand. Say "Jarvis" to start over.'})
                        retries += 1
                            
                    except sr.RequestError as e:
                        print(f"Could not request results; {e}")
                        error_msg = str(e).lower()
                        if "connection failed" in error_msg:
                            socketio.emit('status', {'message': 'Connection failed. Please check your internet.'})
                        else:
                            socketio.emit('status', {'message': f'Service error: {str(e)}'})
                        return None
                    
                except sr.WaitTimeoutError:
                    print(f"No speech detected (attempt {retries + 1})")
                    if retries < max_retries:
                        socketio.emit('status', {'message': 'No speech detected. Please try again.'})
                        time.sleep(0.3)  # Shorter pause between attempts
                    else:
                        socketio.emit('status', {'message': 'No speech detected. Say "Jarvis" to start over.'})
                    retries += 1
                    
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            socketio.emit('status', {'message': 'An unexpected error occurred. Please try again.'})
            return None
    
    return None

@app.route('/')
def index():
    return render_template('index.html', tasks=tasks)

@socketio.on('connect')
def handle_connect():
    global background_thread, is_listening
    emit('tasks', tasks)
    
    # Start background listening if not already running
    if not is_listening:
        is_listening = True
        background_thread = threading.Thread(target=background_listening)
        background_thread.daemon = True
        background_thread.start()

@socketio.on('disconnect')
def handle_disconnect():
    global is_listening
    is_listening = False

@socketio.on('start_listening')
def handle_start_listening():
    """Handle manual button press to start listening"""
    print("Manual listening triggered...")
    
    # Initialize recognizer with specific settings
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.6
    recognizer.phrase_threshold = 0.3
    recognizer.non_speaking_duration = 0.3
    
    # Use cached microphone instance
    microphone = get_microphone()
    
    # Listen for task directly (skip wake word when button is pressed)
    task_text = listen_for_task(recognizer, microphone)
    
    if task_text:
        task = {
            'id': len(tasks) + 1,
            'text': task_text,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'completed': False
        }
        tasks.append(task)
        print(f"Task added: {task}")
        socketio.emit('new_task', task)
        socketio.emit('status', {'message': 'Task added! Click button or say "Jarvis" for another task.'})

@socketio.on('toggle_task')
def handle_toggle_task(data):
    task_id = data['id']
    for task in tasks:
        if task['id'] == task_id:
            task['completed'] = not task['completed']
            emit('task_updated', task, broadcast=True)
            break

if __name__ == '__main__':
    print("Starting voice assistant...")
    socketio.run(app, 
                debug=False,  # Disable debug mode for production
                host='0.0.0.0',
                port=8443,
                ssl_context=(
                    'ssl/cert.pem',
                    'ssl/key.pem'
                )) 