# F.R.I.D.A.Y.

A voice assistant built to feel like the films, which means built for one
number: **800ms from you finishing your sentence to the first syllable out of
the speaker.** Everything here is in service of that.

**Status:** text assistant working. Voice not built yet.

```
   chat.py  ──────►  MCP server (stdio)  ──► weather (Open-Meteo)
   Groq brain                            ──► news (BBC / Sky RSS)
                                         ──► web search (Brave, optional)
                                         ──► time / system state
                                         ──► deep_analysis (async job)
```

**Why the split:** the fast model handles every turn. Anything needing real
reasoning goes to `deep_analysis`, which returns a job id immediately — FRIDAY
says "working on it", keeps talking, and reads the answer when it lands. That
is both the low-latency architecture *and* the movie-accurate one.

Both brains currently run on Groq's free tier, so "deep" buys higher token
limits and a reasoning-oriented system prompt rather than more capability. Swap
`DEEP_MODEL_GROQ` (or point `friday/tools/deep.py` at a paid Anthropic key) and
the gap becomes real.

## Run it

```bash
conda create -n friday python=3.11 -y
conda activate friday
pip install fastmcp groq httpx python-dotenv pyyaml

cp .env.example .env        # add GROQ_API_KEY from console.groq.com
python chat.py
```

Free key, no card required. `quit` to exit.

## The four things that make it feel real

1. **The prompt.** `friday/prompt.py`. One-sentence answers, no follow-up
   offers, banned phrases, Irish register. Verbosity is the failure mode that
   survives every other fix — and the tool rules are ordered deliberately,
   because these models weight the top of a section far more heavily.
2. **Irish voice, ~1.08x speed** (once voice exists). Not optional. A warm
   American voice is the single biggest immersion break.
3. **Instant acknowledgement.** `ACKS[0]` fires before the LLM produces a
   token. Pre-render to WAV (see `assets/`) and it costs ~0ms.
4. **Barge-in.** You must be able to cut it off mid-sentence.

## Measure it

```bash
python -m evals.run_evals   # tool routing + character drift, 17 cases
python -m friday.latency    # p50/p95 per pipeline hop (voice only)
```

Currently 16/17, zero character violations. Run before every prompt change.
Two real bugs were caught this way and would never have surfaced by hand:
fabricated news headlines when the model answered from memory instead of
calling the tool, and a phantom `get_time` call on the word "thanks".

## Build order

1. ~~MCP server + text client~~ — done
2. Use it daily. Note what you wish it could do, then build those tools.
   Add the eval case to `evals/cases.yaml` first, then implement.
3. Voice loop (`agent_friday.py` — written but untested, and still wired for
   Anthropic; needs porting to Groq). LiveKit + Deepgram + Cartesia, all free
   tier. Instrument every hop.
4. Wake word (openWakeWord, local, "Friday"). Last on purpose — worthless
   until the thing behind it is fast.

## The wall display

Spare monitor in kiosk mode: [World Monitor's free
dashboard](https://www.worldmonitor.app/dashboard) on one half, `tail -f
latency.jsonl` on the other, amber on black. You write none of it and it is the
thing people photograph.

Its 59-tool MCP server is Pro-only, so it is deliberately not wired in.

## Files

| | |
|---|---|
| `chat.py` | terminal client — the thing you actually run |
| `server_stdio.py` | MCP server over stdio (used by `chat.py` and evals) |
| `server.py` | same tools over SSE, for network clients |
| `agent_friday.py` | voice agent — written, not yet working |
| `friday/prompt.py` | the character. Matters more than the rest combined |
| `friday/tools/` | weather, news, search, system, deep_analysis |
| `evals/` | tool-routing and character-drift harness |