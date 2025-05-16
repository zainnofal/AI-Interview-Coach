import os
import time
import sys
import random
import re

# Global variables to track TTS status
USE_OPENAI_TTS = False
openai_client = None
CURRENT_VOICE = "shimmer"  # Default voice

# Function to add natural speech elements
def add_natural_speech_elements(text):
    """
    Add filler words, slight pauses, and natural speech patterns to make 
    the text sound more conversational and human-like.
    """
    # Don't modify text that's already short
    if len(text) < 30:
        return text
        
    # List of filler sounds/words and transitions
    fillers = ["Um, ", "Hmm, ", "So, ", "Well, ", "Right, ", "", "", "", ""]
    pauses = [", ", "... ", ". ", " — ", ""]
    transitions = ["you know, ", "I mean, ", "like, ", "", "", "", ""]
    
    # Add a random filler at the beginning (30% chance)
    if random.random() < 0.3:
        text = random.choice(fillers) + text
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    processed_sentences = []
    
    for sentence in sentences:
        # Skip if sentence is too short
        if len(sentence) < 40:
            processed_sentences.append(sentence)
            continue
            
        # Add natural elements to longer sentences
        words = sentence.split()
        if len(words) > 8:
            # Choose a random position approximately in the first half
            pos = random.randint(2, min(5, len(words) // 2))
            
            # 20% chance to insert a filler or pause
            if random.random() < 0.2:
                if random.random() < 0.5:
                    words.insert(pos, random.choice(transitions))
                else:
                    words[pos] = words[pos] + random.choice(pauses)
        
        processed_sentences.append(' '.join(words))
    
    return ' '.join(processed_sentences)

# Import config for debugging
from config import DEBUG

# Try to import OpenAI for TTS
try:
    from openai import OpenAI
    from config import OPENAI_API_KEY

    if DEBUG:
        print(f"OpenAI import successful")
        print(f"Using OpenAI API Key: {OPENAI_API_KEY[:8]}...{OPENAI_API_KEY[-4:]}")
    
    # Initialize client
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Test if the client is working
        def check_openai_tts():
            """Check if OpenAI TTS is working properly and return status message"""
            global USE_OPENAI_TTS
            
            try:
                # Create a small test speech to verify credentials
                print("Testing OpenAI TTS connection...")
                response = openai_client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input="Hello, I'm testing the OpenAI text to speech API."
                )
                
                # If we get here without an exception, it's working
                USE_OPENAI_TTS = True
                return "OpenAI TTS connection successful. Available voices: alloy, echo, fable, onyx, nova, shimmer"
            except Exception as e:
                USE_OPENAI_TTS = False
                return f"OpenAI TTS connection failed: {str(e)}"
        
        # Check connection on startup
        connection_status = check_openai_tts()
        print(f"OpenAI TTS status: {connection_status}")
        
        def speak_openai(text):
            """Use OpenAI for text-to-speech"""
            global USE_OPENAI_TTS
            
            if not USE_OPENAI_TTS:
                print("OpenAI TTS not available, using fallback...")
                speak_fallback(text)
                return
                
            try:
                print(f"🗣️ OpenAI TTS: {text}")
                
                # Add natural speech elements and modify for faster pace
                processed_text = add_natural_speech_elements(text)
                
                # Create speech with HD model
                response = openai_client.audio.speech.create(
                    model="tts-1-hd",
                    voice=CURRENT_VOICE,  # Use the globally set voice
                    input=processed_text
                )
                
                # Save to a temporary file and play
                temp_file = "temp_speech.mp3"
                response.stream_to_file(temp_file)
                
                # Play the audio (platform dependent)
                import platform
                if platform.system() == "Darwin":  # macOS
                    import subprocess
                    subprocess.run(["afplay", temp_file])
                elif platform.system() == "Windows":
                    import os
                    os.system(f'start {temp_file}')
                else:  # Linux and others
                    import os
                    os.system(f"mpg123 {temp_file}")
                    
                return True
            except Exception as e:
                print(f"OpenAI TTS error: {e}")
                print("Falling back to system TTS...")
                USE_OPENAI_TTS = False
                speak_fallback(text)
                
    except Exception as e:
        if DEBUG:
            print(f"Error initializing OpenAI client: {e}")
        openai_client = None
        
except (ImportError, OSError) as e:
    USE_OPENAI_TTS = False
    print(f"OpenAI TTS import failed: {e}")
    print("OpenAI TTS not available, will check other options...")

# MacOS say command TTS
def speak_macos(text):
    """Use macOS say command for TTS"""
    try:
        print(f"🗣️ System Voice: {text}")
        os.system(f'say "{text}"')
        return True
    except Exception as e:
        print(f"macOS TTS error: {e}")
        return False

# pyttsx3 TTS
try:
    import pyttsx3
    engine = pyttsx3.init()
    
    def speak_pyttsx3(text):
        """Use pyttsx3 for TTS"""
        try:
            print(f"🗣️ pyttsx3: {text}")
            engine.say(text)
            engine.runAndWait()
            return True
        except Exception as e:
            print(f"pyttsx3 error: {e}")
            return False
except:
    def speak_pyttsx3(text):
        return False

# Fallback text-only TTS
def speak_print(text):
    """Last resort, just print the text"""
    print(f"🗣️ SPEAKING: {text}")
    print("(Text-only mode, no audio output available)")
    # Simulate speech time
    words = text.split()
    time.sleep(len(words) * 0.2)  # Approximately 0.2 seconds per word
    return True

# Composite fallback function
def speak_fallback(text):
    """Try multiple fallback methods in order"""
    # First try macOS say
    if speak_macos(text):
        return
    
    # Then try pyttsx3
    if speak_pyttsx3(text):
        return
    
    # Last resort is just print
    speak_print(text)

# Set the default speak function based on what's available
if USE_OPENAI_TTS:
    speak = speak_openai
    print("Using OpenAI Text-to-Speech")
else:
    speak = speak_fallback
    print("Using system TTS")

# Function to check all available voice services and report status
def check_voice_services():
    """Check all voice services and return status of each"""
    status = {}
    
    if 'check_openai_tts' in globals():
        status["openai"] = check_openai_tts()
    else:
        status["openai"] = "OpenAI TTS not imported"
    
    # Report which service is currently active
    if USE_OPENAI_TTS:
        status["active"] = "openai"
    else:
        status["active"] = "system"
    
    return status

# Function to change the voice
def set_voice(voice):
    """Set the voice to use for TTS"""
    global CURRENT_VOICE
    valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    if voice in valid_voices:
        CURRENT_VOICE = voice
        print(f"Voice set to: {CURRENT_VOICE}")
    else:
        print(f"Invalid voice '{voice}', using default: {CURRENT_VOICE}")
        
    return CURRENT_VOICE
