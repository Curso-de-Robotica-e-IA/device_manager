from device_manager.manager_singleton import DeviceManagerSingleton


def test_singleton(monkeypatch):
    """Test the singleton behavior of DeviceManagerSingleton."""
    monkeypatch.setattr(
        'device_manager.manager_singleton.DeviceManagerSingleton.__init__',
        lambda self: None,
    )
    instance1 = DeviceManagerSingleton()
    instance2 = DeviceManagerSingleton()

    assert id(instance1) == id(instance2), (
        'DeviceManagerSingleton instances should have the same ID.'
    )
