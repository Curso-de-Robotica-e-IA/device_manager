from unittest.mock import MagicMock

from device_manager.manager_singleton import (
    get_device_manager,
    reset_device_manager,
)


def test_shared_device_manager_provider_initializes_only_once() -> None:
    """Ensure get_device_manager returns a single shared instance without inheritance."""
    reset_device_manager()
    conn = MagicMock()
    conn.usb_scanner.list_connected_devices.return_value = []

    instance1 = get_device_manager(check_dependencies=False, connector=conn)
    instance2 = get_device_manager(check_dependencies=False, connector=conn)

    assert instance1 is instance2
    reset_device_manager()
