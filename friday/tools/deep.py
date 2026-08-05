"""The two-brain split.

Every conversational turn runs on the fast model. Anything that needs real
reasoning gets handed to Opus as a background job: FRIDAY says "working on it"
and carries on talking. This is both the fast architecture AND the accurate one
- Stark asks for a simulation and gets it after a pause.

Never put a high-effort model on the default path. It kills the illusion.
"""
import asyncio
import uuid
from typing import Any

from anthropic import AsyncAnthropic

from friday import config

_jobs: dict[str, dict[str, Any]] = {}
_client: AsyncAnthropic | None = None


def _c() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


async def _run(job_id: str, question: str) -> None:
    try:
        msg = await _c().messages.create(
            model=config.DEEP_MODEL,
            max_tokens=2000,
            system=("Answer thoroughly, then compress the answer to at most three "
                    "sentences suitable for being read aloud. Output only those "
                    "sentences."),
            messages=[{"role": "user", "content": question}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        _jobs[job_id] = {"status": "done", "result": text.strip(), "q": question}
    except Exception as e:
        _jobs[job_id] = {"status": "error", "result": str(e)[:200], "q": question}


def register(mcp):
    @mcp.tool()
    async def deep_analysis(question: str) -> str:
        """Hand a hard question to the deep model. Returns IMMEDIATELY with a job
        id - do not wait. Say 'Working on it' once, continue the conversation
        normally, then call check_analysis when he asks or after a minute."""
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
