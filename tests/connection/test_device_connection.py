from device_manager.connection.device_connection import DeviceConnection


def test_device_connection_validate_connection_connected(mock_mixed_devices):
    """Test the validate_connection method of DeviceConnection for
    a connected device."""
    is_connected = DeviceConnection().validate_connection(
        serial_number='RXT8595',
    )
    assert is_connected is True, (
        'Device RXT8595 should be reported as connected.'
    )


def test_device_connection_list_all_devices(mock_two_devices_authorized):
    """Test the list_all_devices method of DeviceConnection."""
    device_connection = DeviceConnection(subprocess_check_flag=False)
    devices = device_connection.list_all_devices()
    assert devices == {'RXT8595': 'device', 'RXT8596': 'device'}, (
        'The list of devices should match the expected serial numbers.'
    )


def test_device_connection_check_authorized_devices(mock_mixed_devices):
    """Test the check_authorization method of DeviceConnection."""
    device_connection = DeviceConnection(subprocess_check_flag=False)
    authorized_devices = device_connection.check_authorized_devices()
    assert authorized_devices == ['RXT8595'], (
        'The list of authorized devices should only include connected devices.'
    )


def test_device_connection_check_authorization(mock_mixed_devices):
    """Test the check_authorization method of DeviceConnection."""
    device_connection = DeviceConnection(subprocess_check_flag=False)
    is_authorized = device_connection.check_authorization('RXT8595')
    assert is_authorized is True, (
        'Device RXT8595 should be reported as authorized.'
    )

    is_not_authorized = device_connection.check_authorization('RXT8596')
    assert is_not_authorized is False, (
        'Device RXT8596 should be reported as not authorized.'
    )

    is_offline = device_connection.check_authorization('RXT8597')
    assert is_offline is False, 'Device RXT8597 should be reported as offline.'
