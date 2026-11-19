import logging

from device_manager.connection.adb_connection_discovery import (
    AdbConnectionDiscovery,
)
from device_manager.connection.adb_pairing import AdbPairing
from device_manager.device_actions import DeviceActions
from device_manager.device_info import DeviceInfo
from device_manager.manager import DeviceManager
from device_manager.manager_singleton import (
    get_device_manager,
    reset_device_manager,
)

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    'DeviceManager',
    'DeviceActions',
    'DeviceInfo',
    'AdbPairing',
    'AdbConnectionDiscovery',
    'get_device_manager',
    'reset_device_manager',
]
