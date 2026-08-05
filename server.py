"""FRIDAY MCP server. `uv run friday`

Exposes the tool surface over SSE at http://127.0.0.1:8000/sse. Both the voice
agent and Claude Desktop connect to this same server - one brain, two faces.
"""
import asyncio

from fastmcp import FastMCP

from friday import config
from friday.tools import register_all
from friday.tools.cache import refresh_loop
from friday.tools import weather, web

mcp = FastMCP("friday")
register_all(mcp)


@mcp.resource("friday://info")
def info() -> str:
    return "FRIDAY tool server. Fast model on every turn, deep model behind deep_analysis."


async def _warmers() -> None:
    """Keep the hot tools permanently pre-fetched."""
    await asyncio.gather(
        refresh_loop("weather", config.TTL_WEATHER, weather.warm),
        refresh_loop("news", config.TTL_NEWS, web.warm),
    )


def main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(_warmers())
    mcp.run(transport="sse", host=config.MCP_HOST, port=config.MCP_PORT)


if __name__ == "__main__":
    main()
