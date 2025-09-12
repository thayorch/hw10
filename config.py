import os
from dotenv import load_dotenv
load_dotenv()
MODEL = os.getenv("MODEL")
assert MODEL, "Set MODEL in .env (e.g., groq/llama-3.3-70b-versatile)"