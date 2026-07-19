from __future__ import annotations

import time
from collections import OrderedDict
from functools import wraps
from typing import Any, Callable


def cached(ttl: int = 300, maxsize: int = 128):
    cache: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = f"{func.__module__}.{func.__name__}:{args}:{frozenset(kwargs.items())}"
            now = time.time()
            if key in cache:
                entry = cache[key]
                if now - entry["time"] < ttl:
                    cache.move_to_end(key)
                    return entry["value"]
                del cache[key]
            result = await func(*args, **kwargs)
            cache[key] = {"value": result, "time": now}
            if len(cache) > maxsize:
                cache.popitem(last=False)
            return result
        return wrapper
    return decorator
