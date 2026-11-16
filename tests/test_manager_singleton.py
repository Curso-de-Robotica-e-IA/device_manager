from typing import Any

from device_manager.manager_singleton import DeviceManagerSingleton
from _pytest.monkeypatch import MonkeyPatch

def test_singleton(monkeypatch: MonkeyPatch):
    """Test the singleton behavior of DeviceManagerSingleton."""

    def _noop_init(self: Any) -> None:
        """Bypass __init__ to keep the singleton behavior isolated."""
        return None

    monkeypatch.setattr(
        'device_manager.manager_singleton.DeviceManagerSingleton.__init__',
        _noop_init,
    )
    instance1 = DeviceManagerSingleton()
    instance2 = DeviceManagerSingleton()

    assert id(instance1) == id(instance2), (
        'DeviceManagerSingleton instances should have the same ID.'
    )
