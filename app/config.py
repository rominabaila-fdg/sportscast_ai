
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    ELEVEN_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVEN_BASE_URL: str = os.getenv("ELEVEN_BASE_URL", "https://api.elevenlabs.io")
    # TTS defaults
    ELEVEN_MODEL_ID: str = os.getenv("ELEVEN_MODEL_ID", "eleven_flash_v2_5")
    ELEVEN_OUTPUT_FORMAT: str = os.getenv("ELEVEN_OUTPUT_FORMAT", "pcm_16000")
    ELEVEN_OPTIMIZE_LATENCY: str = os.getenv("ELEVEN_OPTIMIZE_LATENCY", "0")  # 0..4
    # Ring buffer and cooldowns
    RING_BUFFER_SIZE: int = int(os.getenv("RING_BUFFER_SIZE", "20"))
    GOAL_COOLDOWN_S: int = int(os.getenv("GOAL_COOLDOWN_S", "0"))
    CARD_COOLDOWN_S: int = int(os.getenv("CARD_COOLDOWN_S", "0"))
    PROMO_COOLDOWN_S: int = int(os.getenv("PROMO_COOLDOWN_S", "0"))  # ~1x/ repriză
    BET_COOLDOWN_S: int = int(os.getenv("BET_COOLDOWN_S", "0"))
    # Coalescing window for near-simultaneous events (sec)
    COALESCE_WINDOW_S: int = int(os.getenv("COALESCE_WINDOW_S", "10"))

settings = Settings()
