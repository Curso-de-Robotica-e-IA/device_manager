from device_manager.exceptions.errors import DeviceManagerError


class DependencyNotFoundError(DeviceManagerError, FileNotFoundError):
    """Raised when the necessary system dependencies are not found."""

    pass
