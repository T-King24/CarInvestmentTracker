from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: int = 1800):
        self.ttl_seconds = ttl_seconds
        self._store: dict[tuple[Any, ...], tuple[float, Any]] = {}

    def cached(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = (fn.__name__, args, tuple(sorted(kwargs.items())))
            now = time.time()
            cached = self._store.get(key)
            if cached and now - cached[0] <= self.ttl_seconds:
                return cached[1]
            result = fn(*args, **kwargs)
            self._store[key] = (now, result)
            return result

        return wrapper


cache = TTLCache()
