import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

OPENCODE_API_KEY = os.getenv("OPENCODE_API_KEY", "")
OPENCODE_API_KEY_BACKUP = os.getenv("OPENCODE_API_KEY_BACKUP", "")
OPENCODE_AUX_KEY = os.getenv("OPENCODE_AUX_KEY", "")
OPENCODE_BASE_URL = "https://opencode.ai/zen/v1"

COGNEE_API_KEY = os.getenv("COGNEE_API_KEY", "")
COGNEE_API_BASE_URL = os.getenv("COGNEE_API_BASE_URL", "")

FREE_MODELS = [
    "mimo-v2.5-free",
    "big-pickle",
    "minimax-m2.5-free",
    "nemotron-3-super-free",
    "glm-4.7-free",
    "kimi-k2.5-free",
]

TASKS_FILE = DATA_DIR / "tasks.json"
ACTIVITY_LOG = DATA_DIR / "activity_log.jsonl"
DAILY_SUMMARIES = DATA_DIR / "daily_summaries.json"
APP_STATE = DATA_DIR / "app_state.json"
