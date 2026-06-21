"""
config.py
---------
Centralized configuration for the data/model layer. Reads from
environment variables, optionally loaded from a .env file. The
Application Layer never needs to pass API keys or model names by
hand — just set them once in .env and every service in this package
picks them up automatically.

Falls back to sane defaults so the package still imports cleanly even
if python-dotenv isn't installed yet.
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env loading is a convenience, not a hard requirement

# --- External data sources ---
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

# --- Pretrained models (all local, no hosted LLM APIs) ---
EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
LOCAL_LLM_MODEL_NAME = os.environ.get("LOCAL_LLM_MODEL_NAME", "google/flan-t5-base")

# --- Search behavior ---
SEARCH_MIN_CONFIDENCE = float(os.environ.get("SEARCH_MIN_CONFIDENCE", "0.35"))
DEFAULT_VIDEO_COUNT = int(os.environ.get("DEFAULT_VIDEO_COUNT", "4"))
