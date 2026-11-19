class DeviceManagerError(Exception):
    """Base exception for all domain errors in device_manager."""


class DeviceNotFoundError(DeviceManagerError, ValueError):
    """Raised when a requested device serial number is not registered."""


class DeviceDisconnectedError(DeviceManagerError, ConnectionError, RuntimeError):
    """Raised when an operation requires an active device connection."""


class UnexpectedAdbOutputError(DeviceManagerError, ValueError):
    """Raised when an ADB command returns output that cannot be parsed."""
