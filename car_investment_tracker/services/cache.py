from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from threading import Lock
from typing import Any


def _make_hashable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, dict):
        return tuple(sorted((k, _make_hashable(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple, set)):
        return tuple(_make_hashable(v) for v in value)
    return repr(value)


class TTLCache:
    def __init__(self, ttl_seconds: int = 1800):
        self.ttl_seconds = ttl_seconds
        self._store: dict[tuple[Any, ...], tuple[float, Any]] = {}
        self._lock = Lock()

    def cached(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = (
                fn.__name__,
                tuple(_make_hashable(arg) for arg in args),
                tuple(sorted((k, _make_hashable(v)) for k, v in kwargs.items())),
            )
            now = time.time()
            with self._lock:
                cached = self._store.get(key)
                if cached and now - cached[0] <= self.ttl_seconds:
                    return cached[1]

            result = fn(*args, **kwargs)

            with self._lock:
                refreshed_now = time.time()
                cached = self._store.get(key)
                if cached and refreshed_now - cached[0] <= self.ttl_seconds:
                    return cached[1]
                self._store[key] = (refreshed_now, result)
            return result

        return wrapper


cache = TTLCache()
