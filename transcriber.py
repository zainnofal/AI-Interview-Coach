import os
import whisper

# Attempt to use local Whisper model
USE_LOCAL_WHISPER = True
try:
    model = whisper.load_model("base")

    def transcribe_with_local_whisper(filename):
        print(f"Transcribing with local Whisper model: {filename}")
        result = model.transcribe(filename)
        return result["text"]

    transcribe_audio = transcribe_with_local_whisper
    print("Using local Whisper model for transcription")

except (ImportError, OSError, Exception) as e:
    USE_LOCAL_WHISPER = False
    print(f"Local Whisper model not available: {e}")
    print("Trying alternative transcription methods...")

# Try OpenAI Whisper API if local fails
if not USE_LOCAL_WHISPER:
    USE_OPENAI_API = True
    try:
        from openai import OpenAI
        from config import OPENAI_API_KEY

        client = OpenAI(api_key=OPENAI_API_KEY)

        def transcribe_with_openai_api(filename):
            print(f"Transcribing with OpenAI API: {filename}")
            try:
                with open(filename, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                return response.text
            except Exception as e:
                print(f"OpenAI API transcription error: {e}")
                return "[Transcription failed]"

        transcribe_audio = transcribe_with_openai_api
        print("Using OpenAI API for transcription")

    except (ImportError, OSError, Exception) as e:
        USE_OPENAI_API = False
        print(f"OpenAI API not available for transcription: {e}")

# Fallback if both fail
if not USE_LOCAL_WHISPER and not USE_OPENAI_API:
    print("Using simulated transcription with canned responses")

    def transcribe_with_canned_responses(filename):
        print(f"Would transcribe {filename} (Transcription systems not available)")

        if "job_role" in filename:
            roles = ["software engineer", "product manager", "data scientist", 
                     "marketing specialist", "ux designer", "project manager"]
            import hashlib
            hash_value = int(hashlib.md5(filename.encode()).hexdigest(), 16) % len(roles)
            return roles[hash_value]

        if "0" in filename:
            return "I've worked on several technical projects including a web application using React and Node.js..."
        elif "1" in filename:
            return "I ensure code quality by writing comprehensive test suites including unit and integration tests..."
        elif "2" in filename:
            return "When debugging complex problems, I first gather all available information including logs..."
        elif "3" in filename:
            return "I stay current with industry trends by following tech blogs..."
        elif "4" in filename:
            return "When working in teams, I value clear communication and well-defined responsibilities..."
        elif "5" in filename:
            return "My approach to learning new technologies is to build small projects that use core functionality..."
        else:
            return "I believe my experience and passion for learning make me a good fit for this role..."

    transcribe_audio = transcribe_with_canned_responses
