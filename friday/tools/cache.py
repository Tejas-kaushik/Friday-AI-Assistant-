"""Tiny TTL cache + background pre-fetch.

Cached weather/news means the tool call is a dict lookup, not a network trip.
This is worth more milliseconds than any model choice you will make.
"""
import asyncio
import time
from typing import Any, Awaitable, Callable

_store: dict[str, tuple[float, Any]] = {}


async def cached(key: str, ttl: int, fn: Callable[[], Awaitable[Any]]) -> Any:
    now = time.time()
    hit = _store.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    val = await fn()
    _store[key] = (now, val)
    return val


def prime(key: str, val: Any) -> None:
    _store[key] = (time.time(), val)


async def refresh_loop(key: str, ttl: int, fn: Callable[[], Awaitable[Any]]) -> None:
    """Keep a key permanently warm. Spawn one of these per hot tool at boot."""
    while True:
        try:
            prime(key, await fn())
        except Exception:
            pass
        await asyncio.sleep(max(30, ttl - 15))
