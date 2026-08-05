"""Search and news.

Note on World Monitor: its 59-tool MCP server sits behind Pro, so it is NOT
wired in here. Use the free dashboard as the wall display instead (see README).
If you do subscribe, drop its MCP URL into agent_friday.py alongside ours -
no code change needed here.
"""
import re
import xml.etree.ElementTree as ET

import httpx

from friday import config
from friday.tools.cache import cached

_RSS = [
    ("https://feeds.bbci.co.uk/news/world/rss.xml", "BBC"),
    ("https://feeds.skynews.com/feeds/rss/world.xml", "Sky"),
]


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


async def _news() -> str:
    heads: list[str] = []
    async with httpx.AsyncClient(timeout=6, follow_redirects=True) as c:
        for url, src in _RSS:
            try:
                root = ET.fromstring((await c.get(url)).text)
                for item in root.iter("item"):
                    t = _clean(item.findtext("title", ""))
                    if t:
                        heads.append(f"{t} ({src})")
                    if len(heads) >= 8:
                        break
            except Exception:
                continue
    return " | ".join(heads[:8]) or "no headlines available"


async def warm() -> str:
    return await _news()


async def _search(q: str) -> str:
    if not config.BRAVE_API_KEY:
        return "search unavailable - no key configured"
    async with httpx.AsyncClient(timeout=8) as c:
        r = await c.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": q, "count": 4},
            headers={"X-Subscription-Token": config.BRAVE_API_KEY,
                     "Accept": "application/json"},
        )
        d = r.json()
    out = []
    for res in (d.get("web", {}).get("results") or [])[:4]:
        out.append(f"{_clean(res.get('title'))}: {_clean(res.get('description'))}")
    return " | ".join(out) or "nothing useful found"


def register(mcp):
    @mcp.tool()
    async def get_world_news() -> str:
        """Top world headlines right now. Returns raw headlines - summarise them,
        do not read the list aloud verbatim.Name the two or three most significant stories specifically. Never say
"and other news" - that is filler."""
        return await cached("news", config.TTL_NEWS, _news)

    @mcp.tool()
    async def search_web(query: str) -> str:
        """Search the live web for facts you do not know. Keep queries short."""
        return await cached(f"search:{query}", config.TTL_SEARCH,
                            lambda: _search(query))

    @mcp.tool()
    async def fetch_url(url: str) -> str:
        """Fetch and strip a web page. Returns the first ~2000 characters."""
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as c:
            txt = (await c.get(url)).text
        return _clean(txt)[:2000]
