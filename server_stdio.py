"""Stdio transport for Claude Desktop. Same tools, no network hop."""
from fastmcp import FastMCP
from friday.tools import register_all

mcp = FastMCP("friday")
register_all(mcp)

if __name__ == "__main__":
    mcp.run()