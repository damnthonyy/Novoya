import asyncio
import math
from datetime import datetime, timedelta

from novoya_api.accounts.domain.errors import TooManyAttempts
from novoya_api.shared.application.clock import Clock


class InMemoryRateLimiter:
    """RateLimiter with a fixed window per key, in memory.

    Enough for one API instance: counters are lost on restart and not shared between
    instances. With several instances, write a database-backed one behind the same port.
    """

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._windows: dict[str, tuple[datetime, int]] = {}
        self._lock = asyncio.Lock()

    async def hit(self, key: str, limit: int, window: timedelta) -> None:
        async with self._lock:
            now = self._clock.now()
            started, count = self._windows.get(key, (now, 0))
            if now - started >= window:
                started, count = now, 0
            count += 1
            self._windows[key] = (started, count)
            if count > limit:
                retry_after = math.ceil((started + window - now).total_seconds())
                raise TooManyAttempts(max(retry_after, 1))

    async def reset(self, key: str) -> None:
        async with self._lock:
            self._windows.pop(key, None)
