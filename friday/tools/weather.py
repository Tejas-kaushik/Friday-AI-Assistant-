"""Weather via Open-Meteo. No API key, and kept warm in cache so the tool
call costs a dict lookup rather than a round trip."""
import httpx

from friday import config
from friday.tools.cache import cached

_CODES = {
    0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "freezing fog", 51: "light drizzle", 53: "drizzle",
    55: "heavy drizzle", 61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow", 80: "showers",
    81: "showers", 82: "violent showers", 95: "thunderstorms",
}


async def _fetch() -> str:
    url = ("https://api.open-meteo.com/v1/forecast"
           f"?latitude={config.HOME_LAT}&longitude={config.HOME_LON}"
           "&current=temperature_2m,weather_code,wind_speed_10m"
           "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
           "&forecast_days=1&timezone=auto")
    async with httpx.AsyncClient(timeout=6) as c:
        d = (await c.get(url)).json()
    cur, day = d["current"], d["daily"]
    desc = _CODES.get(cur["weather_code"], "unsettled")
    return (f"{desc}, {round(cur['temperature_2m'])} degrees in {config.HOME_LABEL}, "
            f"high of {round(day['temperature_2m_max'][0])}, "
            f"{day['precipitation_probability_max'][0]} percent chance of rain")


async def warm() -> str:
    return await _fetch()


def register(mcp):
    @mcp.tool()
    async def get_weather() -> str:
        """Current conditions and today's outlook for home."""
        return await cached("weather", config.TTL_WEATHER, _fetch)
