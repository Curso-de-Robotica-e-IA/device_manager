from device_manager.manager import DeviceManager


class DeviceManagerSingleton(DeviceManager):
    """Singleton class to manage the DeviceManager instance."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DeviceManagerSingleton, cls).__new__(cls)
        return cls._instance
