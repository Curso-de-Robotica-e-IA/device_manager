from functools import lru_cache
from typing import Any

from device_manager.manager import DeviceManager


@lru_cache(maxsize=1)
def get_device_manager(*args: Any, **kwargs: Any) -> DeviceManager:
    """Return a cached shared DeviceManager instance."""
    return DeviceManager(*args, **kwargs)


def reset_device_manager() -> None:
    """Clear the cached shared DeviceManager instance."""
    get_device_manager.cache_clear()
