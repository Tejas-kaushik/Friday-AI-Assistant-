"""FRIDAY voice agent. `uv run friday_voice`

Pipeline, and why each piece is what it is:

  mic
   |-- Deepgram STT      streaming partials, endpointing at 300ms
   |-- Silero VAD        + turn detector, so barge-in works
   |-- Haiku (fast)      streaming tokens; deep model lives behind a tool
   |-- Cartesia TTS      streaming, speaks on the first sentence not the last
   `-- speaker

Target: 800ms from Boss stopping to first syllable out. Everything here is in
service of that number. Check it with `python -m friday.latency`.

API-surface note: livekit-agents moves fast. If a symbol below has been
renamed, check the current docs before rewriting the architecture - the shape
of the pipeline is right even when the import path drifts.
"""
import logging

from livekit.agents import (Agent, AgentSession, JobContext, WorkerOptions,
                            cli, mcp)
from livekit.plugins import anthropic, cartesia, deepgram, silero

from friday import config, latency
from friday.prompt import ACKS, FRIDAY_PROMPT

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("friday")


class Friday(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=FRIDAY_PROMPT,
            # One brain, shared with Claude Desktop. Add the World Monitor MCP
            # URL here too if you ever subscribe to Pro.
            mcp_servers=[mcp.MCPServerHTTP(url=config.MCP_URL)],
        )

    async def on_user_turn_completed(self, turn_ctx, new_message) -> None:
        # Clock starts the instant he stops talking, not when we start thinking.
        latency.start_turn(getattr(new_message, "text_content", "") or "")
        latency.mark("user_turn_end")


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            language="en-GB",
            api_key=config.DEEPGRAM_API_KEY,
            interim_results=True,      # partials, so the LLM can be pre-warmed
            endpointing_ms=300,        # short: he speaks in clipped sentences
        ),
        llm=anthropic.LLM(
            model=config.FAST_MODEL,
            api_key=config.ANTHROPIC_API_KEY,
            temperature=0.4,           # low: character consistency over variety
        ),
        tts=cartesia.TTS(
            api_key=config.CARTESIA_API_KEY,
            voice=config.CARTESIA_VOICE_ID,   # Irish. This is not optional.
            speed=config.CARTESIA_SPEED,      # ~1.08: rushed reads as competent
        ),
        vad=silero.VAD.load(),
        allow_interruptions=True,      # barge-in. Without it he sounds like a robot.
        min_interruption_duration=0.3,
    )

    @session.on("agent_state_changed")
    def _on_state(ev) -> None:
        state = getattr(ev, "new_state", None)
        if state == "thinking":
            latency.mark("llm_ttft")
        elif state == "speaking":
            latency.mark("first_audio")
            rec = latency.end_turn()
            if rec:
                log.info("turn %.0fms  ttft %.0fms",
                         rec.get("total_ms", 0), rec.get("llm_ttft", 0))

    await session.start(room=ctx.room, agent=Friday())

    # Hardcoded, sub-100ms, no model involved. This single line hides most of
    # the pipeline behind one word and reads as eager rather than slow.
    # Pre-render ACKS to WAV and play from disk to shave the TTS hop entirely.
    await session.say(ACKS[0], allow_interruptions=True)


def dev() -> None:
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


if __name__ == "__main__":
    dev()
