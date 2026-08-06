"""The two-brain split.
Explicit cues: "think hard", "work out", "figure out", "should I", "help me
decide", "what's the best way". If the user says any of these, call this tool
even if you believe you know the answer.

Every conversational turn runs on the fast model. Anything needing real
reasoning gets handed off as a background job: FRIDAY says "working on it" and
carries on talking, then reads the answer when it lands. This is both the
low-latency architecture AND the movie-accurate one - Stark asks for a
simulation and gets it after a pause.

Never put a slow model on the default path. It kills the illusion.

Note: on Groq's free tier both brains are the same model, so "deep" currently
buys higher token limits and a reasoning-oriented system prompt rather than
more capability. The architecture is right; swap DEEP_MODEL_GROQ (or point
this back at a paid Anthropic key) and the gap becomes real.
"""
import asyncio
import os
import uuid
from typing import Any

from groq import AsyncGroq

_jobs: dict[str, dict[str, Any]] = {}
_client: AsyncGroq | None = None


def _c() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


async def _run(job_id: str, question: str) -> None:
    try:
        r = await _c().chat.completions.create(
            model=os.getenv("DEEP_MODEL_GROQ", "openai/gpt-oss-120b"),
            max_tokens=2000,
            messages=[
                {"role": "system", "content":
                 "Answer thoroughly, then compress the answer to at most three "
                 "sentences suitable for being read aloud. Output only those "
                 "sentences."},
                {"role": "user", "content": question},
            ],
        )
        text = (r.choices[0].message.content or "").strip()
        _jobs[job_id] = {"status": "done", "result": text, "q": question}
    except Exception as e:
        _jobs[job_id] = {"status": "error", "result": str(e)[:200], "q": question}


def register(mcp):
    @mcp.tool()
    async def deep_analysis(question: str) -> str:
        """Use for ANY question requiring reasoning, judgement, comparison,
        planning, or weighing tradeoffs - decisions, "should I", "work out",
        "think about", "what's the best way", "help me decide". Not for lookups.
        Returns IMMEDIATELY with a job id - do not wait. Say 'Working on it'
        once, continue talking normally, then call check_analysis after a
        minute or when he asks."""
        job_id = uuid.uuid4().hex[:8]
        _jobs[job_id] = {"status": "running", "result": None, "q": question}
        asyncio.create_task(_run(job_id, question))
        return f"job {job_id} running"

    @mcp.tool()
    def check_analysis(job_id: str) -> str:
        """Collect a deep_analysis result. If still running, say nothing to Boss."""
        j = _jobs.get(job_id)
        if not j:
            return "no such job"
        if j["status"] == "running":
            return "still running"
        return j["result"]

    @mcp.tool()
    def pending_analyses() -> str:
        """List deep_analysis jobs that have finished but not been read out."""
        done = [k for k, v in _jobs.items() if v["status"] == "done"]
        return ", ".join(done) or "none"