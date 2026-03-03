"""Server-Sent Events broadcast hub for real-time updates."""

import asyncio
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# Map of challenge_id -> set of asyncio.Queue
_subscribers: dict[int, set[asyncio.Queue]] = defaultdict(set)


def broadcast(challenge_id: int, event_type: str, data: dict | None = None):
    """Push an event to all subscribers of a challenge.

    Safe to call from sync code — fires and forgets into each subscriber's queue.
    """
    queues = _subscribers.get(challenge_id)
    if not queues:
        return
    payload = json.dumps({"type": event_type, **(data or {})})
    dead = []
    for q in queues:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        queues.discard(q)


async def subscribe(challenge_id: int):
    """Async generator that yields SSE-formatted strings."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=64)
    _subscribers[challenge_id].add(queue)
    try:
        while True:
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=30)
                yield f"data: {payload}\n\n"
            except asyncio.TimeoutError:
                # Send keepalive
                yield ": keepalive\n\n"
    finally:
        _subscribers[challenge_id].discard(queue)
        if not _subscribers[challenge_id]:
            del _subscribers[challenge_id]
