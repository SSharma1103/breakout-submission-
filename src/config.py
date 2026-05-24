from pathlib import Path
from typing import Any
import json
import os

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DB_DIR = ROOT_DIR / "src" / "db"

load_dotenv(ROOT_DIR / ".env")


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def load_sop() -> dict[str, Any]:
    with open(DATA_DIR / "sop.json", "r", encoding="utf-8") as file:
        return json.load(file)


def use_openai() -> bool:
    return bool(OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here")
