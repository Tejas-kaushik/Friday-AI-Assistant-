# F.R.I.D.A.Y.

A voice assistant built to feel like the films, which means built for one
number: **800ms from you finishing your sentence to the first syllable out of
the speaker.** Everything in here is in service of that.

Two faces, one brain:

```
                    ┌──────────────────────────┐
  Claude Desktop ───┤                          │
                    │   MCP server (SSE :8000) │──► weather (cached)
  Voice agent ──────┤   `uv run friday`        │──► news (cached)
   mic → STT →      │                          │──► web search
   Haiku → TTS      │                          │──► system state
                    └──────────────┬───────────┘
                                   └──────────► deep_analysis → Opus, async
```

**Why the split:** the fast model handles every turn. Anything needing real
reasoning goes to `deep_analysis`, which returns a job id immediately — FRIDAY
says "working on it", keeps talking, and reads the answer when it lands. That
is both the low-latency architecture *and* the movie-accurate one.

## Run it

```bash
uv sync
cp .env.example .env      # fill in keys
uv run friday             # terminal 1 — MCP server, must start first
uv run friday_voice       # terminal 2 — voice agent
```

Then open the LiveKit Agents Playground and join the room.

**Text-first is the right order.** Before touching voice, point Claude Desktop
at `http://127.0.0.1:8000/sse` and run FRIDAY as a text assistant for a few
days. You will find out what the character gets wrong and what tools you
actually want long before you have spent a weekend on audio plumbing.

## The four things that make it feel real

1. **Irish voice, ~1.08x speed.** Not optional. A warm American voice is the
   single biggest immersion break, and it is a config line to fix.
2. **Instant acknowledgement.** `session.say(ACKS[0])` fires before the LLM has
   produced a token. Pre-render those to WAV (see `assets/`) and it costs ~0ms.
   One word hides most of the pipeline.
3. **Barge-in.** You must be able to cut it off mid-sentence. Without this,
   every demo has a moment where someone talks over it and it keeps droning.
4. **The prompt.** `friday/prompt.py`. One-sentence answers, no follow-up
   offers, banned phrases. Verbosity is the failure mode that survives every
   other fix.

## Measure it

```bash
uv run friday_eval          # tool routing + character drift, ~18 cases
python -m friday.latency    # p50/p95 per pipeline hop
```

Run the evals before every prompt change. Chase whichever latency hop is
fattest — it is usually TTS, not the model, and almost never the one you
assumed.

## The wall display

Spare monitor in kiosk mode: [World Monitor's free dashboard]
(https://www.worldmonitor.app/dashboard) on one half, `tail -f latency.jsonl`
on the other, amber on black. You write none of it and it is the thing people
photograph.

Its 59-tool MCP server is Pro-only ($39.99/mo), so it is deliberately not wired
in. If you ever subscribe, add its URL to `mcp_servers` in `agent_friday.py` —
no other change needed.

## Build order

1. MCP server + Claude Desktop. Use it daily. Note what you wish it could do.
2. Build those tools. Add them to `evals/cases.yaml` first, then implement.
3. Voice loop. Instrument every hop.
4. Wake word (openWakeWord, local, "Friday"). Last on purpose — worthless until
   the thing behind it is fast.
