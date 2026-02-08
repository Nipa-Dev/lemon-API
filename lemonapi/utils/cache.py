from datetime import datetime
from aiocache import SimpleMemoryCache, BaseCache
from aiocache.serializers import JsonSerializer

import functools
import inspect


cache = SimpleMemoryCache(serializer=JsonSerializer(), namespace="wiki")


def _serialize(obj):
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: _serialize(val) for key, val in obj.items()}
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def cache_result(cache_key: str, ttl=600, cache: BaseCache = cache):
    """
    Decorator to cache the result of function using a formatted cache key.

    The `cache_key` can include placeholders for the function's parameters, which will be
    filled in at runtime using Python's `str.format(**kwargs)`.

    Example:
        ```
        @cache_result(cache_key="search:{q}", ttl=120)
        async def search_notes(q: str): ...
        ```
        If called with `q="hello"`, the cache key will be "search:hello".

    Args:
        cache_key (str): A format string for the cache key. Can reference function parameters by name.
                         If no placeholders are used, the key is treated as a static string.
        ttl (int, optional): Time-to-live for the cache entry in seconds. Defaults to 60.
        cache (BaseCache, optional): Cache backend instance implementing `get` and `set`. Defaults to global `cache`.

    Returns:
        Callable: The decorated async function with caching behavior.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            bound_args = inspect.signature(func).bind(*args, **kwargs)
            bound_args.apply_defaults()
            key = cache_key.format(**bound_args.arguments)
            cached = await cache.get(key)
            if cached is not None:
                return cached

            result = await func(*args, **kwargs)
            await cache.set(key, _serialize(result), ttl=ttl)
            return result

        return wrapper

    return decorator
