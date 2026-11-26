from device_manager.exceptions.errors import DeviceManagerError


class DependencyVersionError(DeviceManagerError):
    """Raised when the found dependency version is lower than the minimum
    required by the library to work correctly."""

    pass
