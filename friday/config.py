"""App-wide settings. Everything reads from here, nothing reads os.environ directly."""
import os
from dotenv import load_dotenv

load_dotenv()


def _f(key: str, default: float) -> float:
    try:
        return float(os.getenv(key) or default)
    except ValueError:
        return default


# Brain
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
FAST_MODEL = os.getenv("FAST_MODEL", "claude-haiku-4-5-20251001")
DEEP_MODEL = os.getenv("DEEP_MODEL", "claude-opus-5")

# Voice
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "")
CARTESIA_VOICE_ID = os.getenv("CARTESIA_VOICE_ID", "")
CARTESIA_SPEED = _f("CARTESIA_SPEED", 1.08)

# Tools
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")
HOME_LAT = _f("HOME_LAT", 53.3811)
HOME_LON = _f("HOME_LON", -1.4701)
HOME_LABEL = os.getenv("HOME_LABEL", "home")

# Server
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_URL = f"http://{MCP_HOST}:{MCP_PORT}/sse"
LATENCY_LOG = os.getenv("LATENCY_LOG", "./latency.jsonl")

# Cache TTLs (seconds). Pre-fetching turns a network hop into a memory read.
TTL_WEATHER = 600
TTL_NEWS = 300
TTL_SEARCH = 120
