import os

# Load API key from environment variable; this should be set in advance
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
LLAMA_API_KEY = os.environ.get('LLAMA_API_KEY')

# Define the base URL
BASE_URL = "https://api.llama.com/v1"
GROQ_AUDIO_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
