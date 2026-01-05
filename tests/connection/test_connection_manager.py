from device_manager.connection.connection_manager import (
    ConnectionManager,
    ConnectionManagerSingleton,
)


def test_connection_manager_init():
    """Test the initialization of ConnectionManager."""
    manager = ConnectionManager(subprocess_check_flag=True)
    assert isinstance(manager, ConnectionManager), (
        'manager should be an instance of ConnectionManager.'
    )


def test_connection_manager_singleton():
    """Test the singleton behavior of ConnectionManagerSingleton."""
    instance1 = ConnectionManagerSingleton(subprocess_check_flag=True)
    instance2 = ConnectionManagerSingleton(subprocess_check_flag=False)

    assert id(instance1) == id(instance2), (
        'ConnectionManagerSingleton instances should have the same ID.'
    )


def test_check_devices_adb_connection(mock_mixed_devices):
    """Test the check_devices_adb_connection method of ConnectionManager."""

    is_connected = ConnectionManager.check_devices_adb_connection(
        serial_number='RXT8595',
        subprocess_check_flag=False,
    )
    assert is_connected is True, (
        'Device RXT8595 should be reported as connected.'
    )

    is_unauthorized = ConnectionManager.check_devices_adb_connection(
        serial_number='RXT8596',
        subprocess_check_flag=False,
    )
    assert is_unauthorized is True, (
        'Device RXT8596 should be reported as not authorized.'
    )

    is_offline = ConnectionManager.check_devices_adb_connection(
        serial_number='RXT8597',
        subprocess_check_flag=False,
    )
    assert is_offline is False, 'Device RXT8597 should be reported as offline.'

    is_not_connected = ConnectionManager.check_devices_adb_connection(
        serial_number='RXT8598',
        subprocess_check_flag=False,
    )
    assert is_not_connected is False, (
        'Device RXT8598 should be reported as not connected.'
    )
