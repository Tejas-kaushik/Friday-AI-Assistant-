"""Terminal FRIDAY on Groq. Same MCP server, same tools, free brain."""
import asyncio, json, os
from dotenv import load_dotenv
from groq import AsyncGroq
from fastmcp import Client
from friday.prompt import FRIDAY_PROMPT

load_dotenv()

async def main():
    llm = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    async with Client("server_stdio.py") as mcp:
        tools = []
        for t in await mcp.list_tools():
            schema = dict(t.inputSchema or {})
            schema.setdefault("type", "object")
            schema.setdefault("properties", {})
            schema.setdefault("required", [])
            tools.append({"type": "function",
                          "function": {"name": t.name,
                                       "description": t.description or "",
                                       "parameters": schema}})
        print(f"FRIDAY online. {len(tools)} tools.\n")
        history = [{"role": "system", "content": FRIDAY_PROMPT}]
        while True:
            said = input("> ").strip()
            if said in ("quit", "exit"):
                break
            history.append({"role": "user", "content": said})
            while True:
                try:
                    r = await llm.chat.completions.create(
                        model=model, messages=history, tools=tools, max_tokens=500)
                except Exception as e:
                    print(f"  [error: {str(e)[:120]}]")
                    history.pop()
                    break
                m = r.choices[0].message
                history.append(m.model_dump(exclude_none=True))
                if m.content:
                    print(m.content.strip())
                if not m.tool_calls:
                    break
                for c in m.tool_calls:
                    print(f"  [{c.function.name}]")
                    try:
                        args = json.loads(c.function.arguments or "{}")
                    except Exception:
                        args = {}
                    out = await mcp.call_tool(c.function.name, args or {})
                    history.append({"role": "tool", "tool_call_id": c.id,
                                    "content": str(out.content[0].text if out.content else "")})

asyncio.run(main())