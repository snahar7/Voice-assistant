from dotenv import load_dotenv
import os

# Load the environment variables from .env
load_dotenv()

# Get the API key
api_key = os.getenv('OPENAI_API_KEY')

if api_key:
    # Only show first few and last few characters for security
    visible_part = f"{api_key[:4]}...{api_key[-4:]}"
    print(f"✅ API key loaded successfully! Key starts with '{visible_part}'")
else:
    print("❌ Error: OPENAI_API_KEY not found in .env file") 