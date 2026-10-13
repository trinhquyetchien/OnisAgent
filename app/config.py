import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "onis_db.json"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

KEV_BASE_URL = os.getenv("KEV_BASE_URL", "http://localhost:8008")
KEV_MODEL_NAME = os.getenv("KEV_MODEL_NAME", "jaredpalmer/kev-0.8b")
KEV_TEMPERATURE = float(os.getenv("KEV_TEMPERATURE", "2.35"))

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.65"))
