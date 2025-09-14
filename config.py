import os
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

@dataclass
class Settings:
    OPENAI_API_KEY: str
    DEFAULT_MODEL: str = "gpt-4o-mini"
    MAX_INPUT_CHARS: int = 60000  # generous for long resumes/JDs

def get_settings() -> Settings:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return Settings(OPENAI_API_KEY=key)

def init_openai_client(api_key: str | None = None) -> OpenAI:
    key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is missing. Set it in your environment or sidebar.")
    return OpenAI(api_key=key)
