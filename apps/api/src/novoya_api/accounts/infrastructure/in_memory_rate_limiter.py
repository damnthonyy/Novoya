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

    MAX_KEYS = 50_000  # past this, finished windows are dropped: keys come from user input

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._windows: dict[str, tuple[datetime, timedelta, int]] = {}
        self._lock = asyncio.Lock()

    async def hit(self, key: str, limit: int, window: timedelta) -> None:
        async with self._lock:
            now = self._clock.now()
            if len(self._windows) >= self.MAX_KEYS:
                self._prune(now)
            started, _, count = self._windows.get(key, (now, window, 0))
            if now - started >= window:
                started, count = now, 0
            count += 1
            self._windows[key] = (started, window, count)
            if count > limit:
                retry_after = math.ceil((started + window - now).total_seconds())
                raise TooManyAttempts(max(retry_after, 1))

    def _prune(self, now: datetime) -> None:
        self._windows = {
            key: entry for key, entry in self._windows.items() if now - entry[0] < entry[1]
        }

    async def reset(self, key: str) -> None:
        async with self._lock:
            self._windows.pop(key, None)
