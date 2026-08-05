"""Tool-routing evals on Groq. `python -m evals.run_evals`

Checks two things per case: right tool, and character held (length + banned
phrases). Both regress silently as you edit the prompt.
"""
import asyncio, json, os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from groq import AsyncGroq
from fastmcp import Client

from friday.prompt import FRIDAY_PROMPT

load_dotenv()

BANNED = ["great question", "i'd be happy", "let me know if",
          "is there anything else", "as an ai", "certainly,", "absolutely"]


async def one(llm, model, tools, case):
    try:
        r = await llm.chat.completions.create(
            model=model, max_tokens=300, tools=tools,
            messages=[{"role": "system", "content": FRIDAY_PROMPT},
                      {"role": "user", "content": case["say"]}])
        m = r.choices[0].message
        got = m.tool_calls[0].function.name if m.tool_calls else "none"
        text = m.content or ""
    except Exception as e:
        got, text = f"ERROR", str(e)[:80]
    lower = text.lower()
    return {"say": case["say"], "expect": case["expect"], "got": got,
            "tool_ok": got == case["expect"], "text": text.strip(),
            "sentences": len([s for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]),
            "banned": [p for p in BANNED if p in lower]}


async def run():
    cases = yaml.safe_load(Path(__file__).with_name("cases.yaml").read_text())
    llm = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    async with Client("server_stdio.py") as mcp:
        tools = []
        for t in await mcp.list_tools():
            s = dict(t.inputSchema or {})
            s.setdefault("type", "object"); s.setdefault("properties", {})
            s.setdefault("required", [])
            tools.append({"type": "function",
                          "function": {"name": t.name,
                                       "description": t.description or "",
                                       "parameters": s}})

        results = []
        for c in cases:                      # serial: free tier rate limits
            results.append(await one(llm, model, tools, c))
            await asyncio.sleep(0.5)

    for r in results:
        print(f"{'ok  ' if r['tool_ok'] else 'FAIL'} {r['say'][:38]:40s} -> "
              f"{r['got']:16s} (want {r['expect']})")
        if not r["tool_ok"] or r["banned"] or r["sentences"] > 2:
            print(f"       {r['text'][:100]}")

    print(f"\ntool routing : {sum(r['tool_ok'] for r in results)}/{len(results)}")
    print(f"too long     : {sum(r['sentences'] > 2 for r in results)}")
    print(f"banned phrase: {sum(bool(r['banned']) for r in results)}")
    Path("evals/last_run.json").write_text(json.dumps(results, indent=2))


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()