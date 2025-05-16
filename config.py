# OpenAI API key for GPT models
OPENAI_API_KEY = ""

# ElevenLabs credentials for realistic TTS
ELEVENLABS_API_KEY = ""
ELEVENLABS_VOICE_ID = ""

# Voice and transcription settings
MAX_RECORDING_DURATION = 30  # Maximum recording duration in seconds 
DEFAULT_RECORDING_DURATION = 15  # Default recording duration

# Debug mode - set to True to print more information
DEBUG = True

# Print API key information if in debug mode
if DEBUG:
    print(f"OpenAI API Key: {OPENAI_API_KEY[:8]}...{OPENAI_API_KEY[-4:]}")
    print(f"ElevenLabs API Key: {ELEVENLABS_API_KEY[:8]}...{ELEVENLABS_API_KEY[-4:]}")
    print(f"ElevenLabs Voice ID: {ELEVENLABS_VOICE_ID}")

# API validation helper functions
def is_valid_openai_key(key):
    """Basic validation for OpenAI key format"""
    return key and (key.startswith("sk-") or key.startswith("sk-proj-")) and len(key) > 20

def is_valid_elevenlabs_key(key):
    """Basic validation for ElevenLabs key format"""
    return key and key.startswith("sk_") and len(key) > 20

# Check API keys
if not is_valid_openai_key(OPENAI_API_KEY):
    print("WARNING: OpenAI API key appears to be invalid!")

if not is_valid_elevenlabs_key(ELEVENLABS_API_KEY):
    print("WARNING: ElevenLabs API key appears to be invalid!")
