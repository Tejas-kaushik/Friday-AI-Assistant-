"""Time, date, and machine state. Spoken-form output only - no ISO strings."""
import platform
import shutil
from datetime import datetime


def _spoken_time(dt: datetime) -> str:
    h24, m = dt.hour, dt.minute
    h12 = h24 % 12 or 12
    words = {0: "twelve", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
             6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
             11: "eleven", 12: "twelve"}
    hw = words[h12]
    nxt = words[(h12 % 12) + 1]
    if m == 0:
        base = f"{hw} o'clock"
    elif m == 15:
        base = f"quarter past {hw}"
    elif m == 30:
        base = f"half {hw}"
    elif m == 45:
        base = f"quarter to {nxt}"
    elif m < 30:
        base = f"{m} past {hw}"
    else:
        base = f"{60 - m} to {nxt}"
    if h24 < 5 or h24 >= 22:
        return f"{base} at night"
    part = "morning" if h24 < 12 else "afternoon" if h24 < 18 else "evening"
    return f"{base} in the {part}"


def register(mcp):
    @mcp.tool()
    def get_time() -> str:
        """Current local time and date, phrased for speech."""
        now = datetime.now()
        return f"{_spoken_time(now)}, {now.strftime('%A the %d of %B')}"

    @mcp.tool()
    def get_system_info() -> str:
        """Host machine state: OS, disk headroom. For 'how are the systems' style asks."""
        du = shutil.disk_usage("/")
        free_gb = du.free / 1e9
        return (f"{platform.system()} {platform.release()}, "
                f"{free_gb:.0f} gigabytes free of {du.total / 1e9:.0f}")
