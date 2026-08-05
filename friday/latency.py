"""Latency instrumentation. The whole project is judged on one number.

Target: 800ms from Boss finishing his sentence to the first syllable out of
the speaker. You cannot optimise what you do not measure, and the hop that
dominates is almost never the one you expect.
"""
import json
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from friday import config

_turn: Optional[dict] = None


def start_turn(utterance: str = "") -> None:
    global _turn
    _turn = {"t0": time.perf_counter(), "utterance": utterance, "hops": {}}


@contextmanager
def hop(name: str):
    """Time one leg of the pipeline: stt / llm_ttft / tool / tts_first_chunk."""
    t = time.perf_counter()
    try:
        yield
    finally:
        if _turn is not None:
            _turn["hops"][name] = round((time.perf_counter() - t) * 1000, 1)


def mark(name: str) -> None:
    """Record ms since turn start - use for first-token / first-audio marks."""
    if _turn is not None:
        _turn["hops"][name] = round((time.perf_counter() - _turn["t0"]) * 1000, 1)


def end_turn() -> Optional[dict]:
    global _turn
    if _turn is None:
        return None
    rec = {
        "ts": time.time(),
        "utterance": _turn["utterance"][:120],
        "total_ms": round((time.perf_counter() - _turn["t0"]) * 1000, 1),
        **_turn["hops"],
    }
    _turn = None
    try:
        with Path(config.LATENCY_LOG).open("a") as f:
            f.write(json.dumps(rec) + "\n")
    except OSError:
        pass
    return rec


def report() -> str:
    """p50/p95 over the log. Run this weekly; chase whichever hop is fattest."""
    p = Path(config.LATENCY_LOG)
    if not p.exists():
        return "no latency data yet"
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    if not rows:
        return "no latency data yet"
    keys = sorted({k for r in rows for k in r if k.endswith("_ms") or k in
                   ("stt", "llm_ttft", "tool", "tts_first_chunk")})
    out = [f"turns: {len(rows)}"]
    for k in keys:
        vals = sorted(r[k] for r in rows if isinstance(r.get(k), (int, float)))
        if not vals:
            continue
        p50 = vals[len(vals) // 2]
        p95 = vals[min(len(vals) - 1, int(len(vals) * 0.95))]
        out.append(f"{k:20s} p50 {p50:7.1f}ms   p95 {p95:7.1f}ms")
    return "\n".join(out)


if __name__ == "__main__":
    print(report())
